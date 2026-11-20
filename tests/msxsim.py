"""MSX1 test bench on the Z80 simulator of SkoolKit.

An MSX object is an MSX1 with C-BIOS in slot 0, a 32 KB cartridge in
slot 1 (#4000-#BFFF) and 64 KB of RAM in slot 3, as openMSX builds the
machines C-BIOS_MSX1_EU (TMS9929A, 50 Hz) and C-BIOS_MSX1 (TMS9918A,
60 Hz). The Z80 is SkoolKit's (pure Python: the one that lets the
bench add what the MSX adds to it); around it:

  time    T-states of SkoolKit plus the MSX wait: one T-state more
          for every M1 cycle (+1 for an instruction, +2 with a CB, ED,
          DD or FD prefix, +1 for every 5-T-state cycle of HALT). An
          interrupt costs 19 (IM 2) or 13 (IM 1) T-states.
  VDP     16 KB of VRAM behind ports #98 and #99, 8 registers, the
          status register, the frame interrupt (flag F at the start of
          line 192, a request while F and R1 bit 5 are set), the
          sprites of a frame (5th sprite, collision) and the rule of
          the TMS9918A: two VRAM accesses (port #98) during the picture
          less than VRAM_GAP T-states apart are an error of the test.
  PSG     16 registers behind #A0-#A2; register 14 reads joystick
          port 1 or 2 (register 15, bit 6). As in the C-BIOS machines
          of openMSX, bits 6-7 of register 7 are forced to 10 (port A
          in, port B out); the log keeps what the program wrote.
  PPI     slots (#A8), keyboard matrix (#A9, row in #AA bits 0-3).

The machine starts at the cartridge's INIT with the BIOS state openMSX
had there (tests/openmsx_run.py writes it: RAM of page 3, slots, PPI,
PSG, the time to the next frame interrupt). The program after INIT is
the bench's alone; only RSLREG and ENASLT run code of C-BIOS (BSD
licence), read from the openMSX installation.

Use:  m = MSX(rom, state, cbios); m.run_to(addr)
"""
import random

from skoolkit.simulator import Simulator

A_, F_, B_, C_ = 0, 1, 2, 3
SP_, I_, PC_, T_, IFF_, IM_, HALT_ = 12, 14, 24, 25, 26, 27, 28

LINE_T = 228                    # T-states in a line
LINES = {50: 313, 60: 262}      # lines in a frame
VRAM_GAP = 29                   # T-states between VRAM accesses
PSG_MASK = (0xFF, 0x0F, 0xFF, 0x0F, 0xFF, 0x0F, 0x1F, 0xFF,
            0x1F, 0x1F, 0x1F, 0xFF, 0xFF, 0x0F, 0xFF, 0xFF)
# keyboard row 8 and the joystick, by name
ROW8 = {'SPACE': 0, 'HOME': 1, 'INS': 2, 'DEL': 3, 'LEFT': 4,
        'UP': 5, 'DOWN': 6, 'RIGHT': 7}
JOY = {'UP': 0, 'DOWN': 1, 'LEFT': 2, 'RIGHT': 3, 'A': 4, 'B': 5}


def io_offset(memory, pc):
    """T-states from the start of the instruction at pc to its I/O
    cycle, M1 waits included (the Z80 timing of openMSX)."""
    op = memory[pc]
    if op in (0xD3, 0xDB):              # OUT (n),A  IN A,(n)
        return 9
    if op == 0xED:
        op2 = memory[(pc + 1) & 0xFFFF]
        if op2 & 0xC6 == 0x40:          # IN r,(C)  OUT (C),r
            return 11
        if op2 in (0xA3, 0xAB, 0xB3, 0xBB):     # OUTI ... OTDR
            return 15
        if op2 in (0xA2, 0xAA, 0xB2, 0xBA):     # INI ... INDR
            return 12
    return 0


class VDP:
    """The TMS9918A / TMS9929A as the program sees it."""

    def __init__(self, hz):
        self.hz = hz
        self.vram = bytearray(0x4000)
        self.regs = [0] * 8
        self.status = 0
        self.latch_full = False
        self.latch = 0
        self.pointer = 0
        self.data = 0                   # read-ahead / last written
        self.picture_start = None       # T of line 0 of the picture
        self.frame_t = LINES[hz] * LINE_T
        self.last_vram = None           # T of the last #98 access
        self.too_fast = []              # (T, PC, gap) in the picture
        self.writes = 0
        self.on_since = None            # T the screen went on
        self.off_at = None              # T the screen went off

    # -- ports -------------------------------------------------------

    def in_picture(self, t):
        if not self.regs[1] & 0x40 or self.picture_start is None:
            return False
        return 0 <= (t - self.picture_start) % self.frame_t \
            < 192 * LINE_T

    def vram_access(self, t, pc):
        if self.last_vram is not None and self.in_picture(t):
            gap = t - self.last_vram
            if gap < VRAM_GAP:
                self.too_fast.append((t, pc, gap))
        self.last_vram = t

    def write(self, port, value, t, pc):
        if port & 1 == 0:               # #98: VRAM data
            self.vram_access(t, pc)
            self.data = value
            self.vram[self.pointer] = value
            self.pointer = (self.pointer + 1) & 0x3FFF
            self.latch_full = False
            self.writes += 1
        elif self.latch_full:           # #99, second byte
            if value & 0x80:            # register
                if value & 7 == 1:
                    on = self.latch & 0x40
                    if on and not self.regs[1] & 0x40:
                        self.on_since = t
                    elif self.regs[1] & 0x40 and not on:
                        self.off_at = t
                self.regs[value & 7] = self.latch
                self.pointer = (value << 8 | (self.pointer & 0xFF)) \
                    & 0x3FFF
            else:                       # address
                self.pointer = (value << 8 | self.latch) & 0x3FFF
                if not value & 0x40:    # read: read ahead
                    self.vram_access(t, pc)
                    self.data = self.vram[self.pointer]
                    self.pointer = (self.pointer + 1) & 0x3FFF
            self.latch_full = False
        else:                           # #99, first byte
            self.pointer = (self.pointer & 0x3F00) | value
            self.latch = value
            self.latch_full = True

    def read(self, port, t, pc):
        self.latch_full = False
        if port & 1 == 0:               # #98: VRAM data
            self.vram_access(t, pc)
            value = self.data
            self.data = self.vram[self.pointer]
            self.pointer = (self.pointer + 1) & 0x3FFF
            return value
        value = self.status             # #99: status
        self.status &= 0x1F
        return value

    @property
    def irq(self):
        return bool(self.status & 0x80 and self.regs[1] & 0x20)

    # -- the frame ---------------------------------------------------

    def vblank(self, t):
        """Line 192 at T-state t: the sprites of the lines of the
        picture just shown that had the screen on, then F."""
        start = t - 192 * LINE_T
        lo, hi = 0, 192
        if self.regs[1] & 0x40:
            if self.on_since is not None and self.on_since > start:
                lo = -(-(self.on_since - start) // LINE_T)
        elif self.off_at is not None and self.off_at > start:
            hi = (self.off_at - start) // LINE_T
        else:
            hi = 0
        if lo < hi:
            self.check_sprites(lo, hi)
        self.status |= 0x80

    def check_sprites(self, lo=0, hi=192):
        """5th sprite and collision on lines lo to hi - 1, as
        openMSX's SpriteChecker."""
        size = 16 if self.regs[1] & 2 else 8
        mag = 2 if self.regs[1] & 1 else 1
        sat = (self.regs[5] & 0x7F) << 7
        fifth, fifth_line = -1, 999
        count = [0] * 192
        shown = [[] for _ in range(192)]
        sprite = 0
        while sprite < 32:
            y = self.vram[sat + 4 * sprite]
            if y == 208:
                break
            for line in range(lo, hi):
                sl = (line - 1 - y) & 0xFF      # shown one line lower
                if sl >= size * mag:
                    continue
                if count[line] == 4:
                    if line < fifth_line:
                        fifth_line, fifth = line, sprite
                    continue
                count[line] += 1
                shown[line].append((sprite, sl // mag))
            sprite += 1
        status = self.status
        if fifth != -1 and status & 0xC0 == 0:
            status = 0x40 | (status & 0x20) | fifth
        if not status & 0x40:
            status = (status & 0xA0) | min(sprite, 31)
        if not status & 0x20 and self.collision(shown, size, mag):
            status |= 0x20
        self.status = (self.status & 0x80) | (status & 0x7F)

    def sprite_row(self, sprite, row, size, mag):
        """The pixels of one row of a sprite: (x, 256-bit mask)."""
        sat = (self.regs[5] & 0x7F) << 7
        spg = (self.regs[6] & 7) << 11
        x = self.vram[sat + 4 * sprite + 1]
        if self.vram[sat + 4 * sprite + 3] & 0x80:
            x -= 32
        pat = self.vram[sat + 4 * sprite + 2]
        if size == 16:
            pat &= 0xFC
            bits = self.vram[spg + pat * 8 + row] << 8 | \
                self.vram[spg + pat * 8 + 16 + row]
            width = 16
        else:
            bits = self.vram[spg + pat * 8 + row]
            width = 8
        mask = 0
        for b in range(width):
            if bits & (1 << (width - 1 - b)):
                for m in range(mag):
                    px = x + b * mag + m
                    if 0 <= px < 256:
                        mask |= 1 << px
        return mask

    def collision(self, shown, size, mag):
        for line in shown:
            seen = 0
            for sprite, row in line:
                mask = self.sprite_row(sprite, row, size, mag)
                if seen & mask:
                    return True
                seen |= mask
        return False


class PSG:
    def __init__(self, regs):
        self.regs = list(regs)
        self.select = 0
        self.log = []                   # (T, register, value)
        self.joy = [0x3F, 0x3F]         # ports 1 and 2, 1 = released
        # the C-BIOS machines of openMSX: port A always an input,
        # port B an output, whatever register 7 says
        self.ignore_directions = True

    def write(self, port, value, t):
        if port & 3 == 0:               # #A0
            self.select = value & 0x0F
        elif port & 3 == 1:             # #A1
            r = self.select
            self.log.append((t, r, value))
            if r == 7 and self.ignore_directions:
                value = (value & 0x3F) | 0x80
            self.regs[r] = value & PSG_MASK[r]

    def read(self):
        r = self.select
        if r == 14 and not self.regs[7] & 0x40:     # port A: input
            r15 = self.regs[15]
            port = (r15 >> 6) & 1
            pin8 = r15 & (0x10 << port)
            joy = 0x3F if pin8 else self.joy[port]
            self.regs[14] = joy | 0x80      # bit 7: cassette in
        return self.regs[r]


class MSX:
    """An MSX1 started at the cartridge's INIT.

    cart     the 32 KB ROM (#4000-#BFFF, slot 1)
    state    the BIOS state at INIT (openmsx_run.cbios_state)
    cbios    (main ROM, logo ROM) of C-BIOS, 32 KB and 16 KB
    seed     RAM #C000-#F37F and VRAM filled at random with this seed
             (None: as openMSX had them at INIT)
    """

    def __init__(self, cart, state, cbios, seed=None):
        self.hz = state['hz']
        empty = bytes([0xFF]) * 0x4000
        main, logo = cbios
        self.slot_rom = {
            0: bytes(main) + bytes(logo) + empty,
            1: empty + bytes(cart) + empty,
            2: empty * 4,
        }
        self.ram = bytearray(0x10000)
        self.ram[0xC000:] = bytes.fromhex(state['ram_c000'])
        self.vdp = VDP(self.hz)
        self.psg = PSG(state['psg'])
        self.ppi_c = state['ppi_c']
        self.keys = set()               # pressed, names of ROW8
        self.mem = bytearray(0x10000)
        self.a8 = state['a8']
        for page in range(4):
            slot = (self.a8 >> (2 * page)) & 3
            lo, hi = page * 0x4000, (page + 1) * 0x4000
            src = self.ram if slot == 3 else self.slot_rom[slot]
            self.mem[lo:hi] = src[lo:hi]
        if seed is not None:
            fill = random_fill(seed)
            self.mem[0xC000:0xF380] = fill['ram']
            self.vdp.vram[:] = fill['vram']
        else:
            self.vdp.vram[:] = bytes.fromhex(state['vram'])
        self.vdp.regs = list(state['vdp_regs'])
        self.vdp.status = state['vdp_status']
        regs = {'PC': state['init'], 'SP': state['sp']}
        for name, value in state.get('regs', {}).items():
            key = name if not name.endswith('2') else '^' + name[:-1]
            regs[key] = value
        cpu_state = {'im': state['im'], 'iff': state['iff'],
                     'tstates': 0}
        self.cpu = Simulator(self.mem, regs, cpu_state)
        self.cpu.set_tracer(self)
        self.cpu.opcodes[0x76] = self.halt
        self.regs = self.cpu.registers
        self.next_vbl = state['vbl_after_init']
        self.vdp.picture_start = self.next_vbl - 192 * LINE_T
        self.ei_last = False
        self.t_insn = 0
        self.pc_insn = 0
        self.irq_log = []               # T of every interrupt taken
        self.instructions = 0
        self.exec_map = None            # a set, to record PCs
        self.watch = {}                 # address: name, to time
        self.marks = []                 # (name, T) when reached

    # -- slots ---------------------------------------------------------

    def set_slots(self, value):
        for page in range(4):
            new = (value >> (2 * page)) & 3
            old = (self.a8 >> (2 * page)) & 3
            if new == old:
                continue
            lo, hi = page * 0x4000, (page + 1) * 0x4000
            if old == 3:
                self.ram[lo:hi] = self.mem[lo:hi]
            src = self.ram if new == 3 else self.slot_rom[new]
            self.mem[lo:hi] = src[lo:hi]
        self.a8 = value

    def rom_written(self):
        """Pages mapped to a ROM whose bytes changed (a write to ROM
        that the real machine would have ignored)."""
        out = []
        for page in range(4):
            slot = (self.a8 >> (2 * page)) & 3
            lo, hi = page * 0x4000, (page + 1) * 0x4000
            if slot != 3 and self.mem[lo:hi] != self.slot_rom[slot][lo:hi]:
                out.append(page)
        return out

    def ram_page3(self):
        return bytes(self.mem[0xC000:0x10000])

    # -- ports (called by the simulator) -------------------------------

    def io_time(self):
        return self.t_insn + io_offset(self.mem, self.pc_insn)

    def read_port(self, registers, port):
        p = port & 0xFF
        if p in (0x98, 0x99):
            return self.vdp.read(p, self.io_time(), self.pc_insn)
        if p == 0xA2:
            return self.psg.read()
        if p == 0xA8:
            return self.a8
        if p == 0xA9:
            value = 0xFF
            if self.ppi_c & 0x0F == 8:
                for k in self.keys:
                    value &= ~(1 << ROW8[k]) & 0xFF
            return value
        if p == 0xAA:
            return self.ppi_c
        return 0xFF

    def write_port(self, registers, port, value, *rest):
        p = port & 0xFF
        if p in (0x98, 0x99):
            self.vdp.write(p, value, self.io_time(), self.pc_insn)
        elif p in (0xA0, 0xA1):
            self.psg.write(p, value, self.io_time())
        elif p == 0xA8:
            self.set_slots(value)
        elif p == 0xAA:
            self.ppi_c = value
        elif p == 0xAB and not value & 0x80:    # bit set/reset
            bit = (value >> 1) & 7
            if value & 1:
                self.ppi_c |= 1 << bit
            else:
                self.ppi_c &= ~(1 << bit) & 0xFF

    # -- input -----------------------------------------------------------

    joy_port = 0        # the joystick plugged into port 1 (1: port 2)

    def set_input(self, keys=(), joy=()):
        """Keys of row 8 and the joystick (in port 1, or in the port
        joy_port says) held from now on."""
        self.keys = set(keys)
        bits = 0x3F
        for j in joy:
            bits &= ~(1 << JOY[j])
        self.psg.joy[self.joy_port] = bits

    # -- running ---------------------------------------------------------

    def halt(self):
        """HALT: 5-T-state cycles until a request can be taken."""
        regs = self.regs
        t = regs[T_]
        if self.vdp.irq:
            n = 1
        elif not regs[IFF_] or not self.vdp.regs[1] & 0x20:
            raise RuntimeError(f'HALT at ${regs[PC_]:04X} that no '
                               'interrupt can end')
        else:
            n = max(1, -(-(self.next_vbl - t) // 5))
        regs[T_] = t + 5 * n - 1        # the loop adds the M1 wait
        regs[PC_] = (regs[PC_] + 1) & 0xFFFF
        regs[HALT_] = 1

    def interrupt(self):
        regs, mem = self.regs, self.mem
        regs[HALT_] = 0
        self.irq_log.append(regs[T_])
        pc = regs[PC_]
        sp = (regs[SP_] - 2) & 0xFFFF
        regs[SP_] = sp
        mem[sp] = pc & 0xFF             # page 3 is RAM
        mem[(sp + 1) & 0xFFFF] = pc >> 8
        if regs[IM_] == 2:
            vec = regs[I_] * 256 + 0xFF     # the bus reads #FF
            regs[PC_] = mem[vec] | mem[(vec + 1) & 0xFFFF] << 8
            regs[T_] += 19
        else:
            regs[PC_] = 0x38
            regs[T_] += 13
        regs[IFF_] = 0

    def run_to(self, stop, max_t=None):
        """Run until PC = stop, at least one instruction first.
        Returns the T-states used."""
        regs, mem = self.regs, self.mem
        ops = self.cpu.opcodes
        vdp = self.vdp
        t0 = regs[T_]
        limit = t0 + (max_t or 200 * vdp.frame_t)
        first = True
        exec_map = self.exec_map
        while True:
            pc = regs[PC_]
            if pc == stop and not first:
                return regs[T_] - t0
            first = False
            if regs[IFF_] and not self.ei_last and vdp.irq:
                self.interrupt()
                self.ei_last = False
                continue
            op = mem[pc]
            self.t_insn = regs[T_]
            self.pc_insn = pc
            if exec_map is not None:
                exec_map.add(pc)
            if pc in self.watch:
                self.marks.append((self.watch[pc], regs[T_]))
            ops[op]()
            regs[T_] += 2 if op in (0xCB, 0xED, 0xDD, 0xFD) else 1
            self.instructions += 1
            self.ei_last = op == 0xFB
            while regs[T_] >= self.next_vbl:
                vdp.vblank(self.next_vbl)
                self.next_vbl += vdp.frame_t
            if regs[T_] >= limit:
                raise RuntimeError(f'${stop:04X} not reached in '
                                   f'{limit - t0} T-states')

    @property
    def tstates(self):
        return self.regs[T_]


def random_fill(seed):
    """RAM #C000-#F37F and the 16 KB of VRAM, at random: the same bytes
    for the bench and for openMSX."""
    rng = random.Random(seed)
    return {'ram': bytes(rng.randrange(256) for _ in range(0x3380)),
            'vram': bytes(rng.randrange(256) for _ in range(0x4000))}


def read_symbols(path):
    """Symbols written by sjasmplus (--sym) or pasmo."""
    import re
    out = {}
    for line in open(path, encoding='ascii'):
        m = re.match(r'\s*([\w.]+):?\s+EQU\s+(\S+)', line, re.I)
        if not m:
            continue
        name, val = m.groups()
        if val.lower().startswith('0x'):
            out[name] = int(val, 16)
        elif val.upper().endswith('H'):
            out[name] = int(val[:-1], 16)
        else:
            out[name] = int(val)
    return out

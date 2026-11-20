"""The model of the sound: what the AY player and the beeper must do.

Independent of the Z80 code: it reads only the data made by the
asset builder (assets.json, key 'music') and follows the rules of
the C64 player, brought to the AY (game/assets/ay_music.py):

AYPlayer(music, song)
    .frame() computes one frame and returns the 11 registers (0-10)
    that the interrupt will send at the start of the next frame.
    Before the first frame the registers are those of silence
    (all 0, mixer $3F).
Beeper(music)
    .start(n) asks for effect n (1-8); .frame() returns the slice
    of this frame: None, or (mode, delay, count, levels), where
    levels are the speaker bits (0 or 1) of the passes.
AYFx(music)
    (milestone 0.7) SOUND FX on the AY: .start(n) asks for effect n
    with the same priorities; .frame(), called by the interrupt
    after it has sent .regs, computes the registers of the next
    frame: channel A plays an entry of 'ayfx' a frame (volume, tone
    or noise; after the first frame of the release the effect no
    longer holds its priority), the end silences it.

Standard library only.
"""
REST, LENGTH, INSTRUMENT, END = 0x60, 0x80, 0xC0, 0xFF
TRANSPOSE_ZERO, ORDER_LOOP = 0xA0, 0xFF
WAVE_TONE, WAVE_NOISE, WAVE_HOLD, WAVE_LOOP = 1, 2, 0xFE, 0xFF
WAVE_FIXED, ENV_HOLD, NO_VIBRATO = 0x80, 0xFF, 0xFF
MIXER_OFF = 0x3F
FX_TONE, FX_NOISE = 1, 2
LFSR_SEED, LFSR_TAPS = 0xACE1, 0xB400


def silence():
    regs = [0] * 11
    regs[7] = MIXER_OFF
    return regs


class Voice:
    def __init__(self, order):
        self.order_list = order
        self.order = 0          # entry of the order list
        self.pattern = None     # (pattern number, position)
        self.steps = 0
        self.length = 1
        self.note = 0
        self.trans = 0
        self.instr = 0
        self.wave = 0
        self.ctrl = 0
        self.arg = 0
        self.gate = 0
        self.env = 0
        self.vol = 0
        self.age = 0
        self.vibph = 0


class AYPlayer:
    def __init__(self, music, song='theme'):
        self.m = music
        self.regs = silence()
        self.tick = 0
        self.frames = 0
        orders = music['songs'][song]['orders']
        self.voices = [Voice(o) for o in orders]
        for v in self.voices:
            self.next_pattern(v)

    # -- reading the score ----------------------------------------

    def next_pattern(self, v):
        while True:
            b = v.order_list[v.order]
            if b == ORDER_LOOP:
                v.order = v.order_list[v.order + 1]
                continue
            v.order += 1
            if b >= LENGTH:
                v.trans = b - TRANSPOSE_ZERO
                continue
            v.pattern = [b, 0]
            return

    def next_event(self, v):
        while True:
            pat = self.m['patterns'][v.pattern[0]]
            b = pat[v.pattern[1]]
            v.pattern[1] += 1
            if b == END:
                self.next_pattern(v)
                continue
            if b >= INSTRUMENT:
                v.instr = b & 0x1F
            elif b >= LENGTH:
                v.length = b - (LENGTH - 1)
            elif b == REST:
                self.gate_off(v)
                break
            else:
                self.start_note(v, (b + v.trans) & 0xFF)
                break
        v.steps = v.length

    def start_note(self, v, note):
        ins = self.m['instruments'][v.instr]
        v.note = note
        v.wave = ins['wave']
        v.env = ins['env']
        v.age = 0
        v.vibph = 0
        v.gate = 1

    def gate_off(self, v):
        if not v.gate:
            return
        v.gate = 0
        ins = self.m['instruments'][v.instr]
        v.env = ins['rel'] + ins['rel_start'][v.vol]

    # -- one frame ---------------------------------------------------

    def frame(self):
        """Returns the registers to send next frame (a copy)."""
        regs = self.regs
        regs[7] = MIXER_OFF
        for n, v in enumerate(self.voices):
            self.voice_frame(n, v, regs)
        self.tick = (self.tick + 1) % self.m['speed']
        self.frames += 1
        return list(regs)

    def voice_frame(self, n, v, regs):
        m = self.m
        if self.tick == 0:
            if v.steps == 0:
                self.next_event(v)
            v.steps -= 1
        elif self.tick == m['gate_tick'] and v.steps == 0:
            self.gate_off(v)
        waves = m['waves']
        e = v.wave
        while True:
            ctrl, arg = waves[e]
            if ctrl == WAVE_HOLD:
                break
            if ctrl == WAVE_LOOP:
                e = arg
                continue
            v.ctrl = ctrl
            if ctrl == WAVE_NOISE:
                v.arg = arg
            elif arg & 0x80:
                v.arg = arg & 0x7F
            else:
                v.arg = (arg + v.note) & 0xFF
            e += 1
            break
        v.wave = e
        env = m['env_data']
        v.vol = env[v.env]
        if env[v.env + 1] != ENV_HOLD:
            v.env += 1
        if v.ctrl == WAVE_NOISE:
            regs[6] = v.arg
            regs[7] &= ~(8 << n) & 0xFF
        else:
            period = m['periods'][v.arg]
            vib = m['instruments'][v.instr]['vib']
            if vib != NO_VIBRATO and v.age >= vib:
                period += m['vibrato'][v.vibph & 7]
                v.vibph = (v.vibph + 1) & 0xFF
            period &= 0xFFFF
            regs[2 * n] = period & 0xFF
            regs[2 * n + 1] = period >> 8
            regs[7] &= ~(1 << n) & 0xFF
        regs[8 + n] = v.vol
        if v.age < 255:
            v.age += 1


class Beeper:
    def __init__(self, music):
        self.m = music
        self.next = 0
        self.pos = 0
        self.prio = 0
        self.lfsr = LFSR_SEED

    def start(self, n):
        """From milestone 0.6 with the C64's priorities: an effect
        less important than the one playing or asked is not heard."""
        prio = self.m.get('sfx_priority', [0] * 8)[n - 1]
        if prio < self.prio:
            return
        self.prio = prio
        self.next = n

    def frame(self):
        if self.next:
            self.pos = self.m['sfx_first'][self.next - 1]
            self.next = 0
        if not self.pos:
            return None
        mode, delay, count = self.m['sfx'][self.pos]
        if mode == 0:
            self.pos = 0
            self.prio = 0
            return None
        self.pos += 1
        levels = []
        if mode == FX_TONE:
            s = 0
            for _ in range(count):
                s ^= 1
                levels.append(s)
        else:
            x = self.lfsr
            for _ in range(count):
                bit = x & 1
                x >>= 1
                if bit:
                    x ^= LFSR_TAPS
                levels.append(bit)
            self.lfsr = x
        return mode, delay, count, levels

    def pass_tstates(self, mode, delay):
        loop = self.m['beeper_loop']
        base = loop['noise_base'] if mode == FX_NOISE else \
            loop['tone_base']
        return base + 13 * delay + 2


AYFX_NOISE, AYFX_TAIL, AYFX_STOP = 0x10, 0x20, 0xFF
MIXER_TONE_A, MIXER_NOISE_A = 0x3E, 0x37


class AYFx:
    def __init__(self, music):
        self.m = music
        self.next = 0
        self.pos = 0
        self.prio = 0
        self.regs = silence()

    def start(self, n):
        prio = self.m['sfx_priority'][n - 1]
        if prio < self.prio:
            return
        self.prio = prio
        self.next = n

    def frame(self):
        if self.next:
            self.pos = self.m['ayfx_first'][self.next - 1]
            self.next = 0
        if not self.pos:
            return
        ctrl, arg = self.m['ayfx'][self.pos]
        if ctrl == AYFX_STOP:
            self.pos = 0
            self.prio = 0
            self.regs[8] = 0
            self.regs[7] = MIXER_OFF
            return
        self.pos += 1
        if ctrl & AYFX_TAIL:
            self.prio = 0
        self.regs[8] = ctrl & 15
        if ctrl & AYFX_NOISE:
            self.regs[6] = arg
            self.regs[7] = MIXER_NOISE_A
        else:
            period = self.m['periods'][arg]
            self.regs[0] = period & 255
            self.regs[1] = period >> 8
            self.regs[7] = MIXER_TONE_A

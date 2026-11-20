"""Phase 0 checks: the probe in the bench and in openMSX, on the two
C-BIOS MSX1 machines (EU: TMS9929A, 50 Hz; INT: TMS9918A, 60 Hz).

  state     the BIOS state at INIT, read from openMSX (the bench starts
            from it); compared with the one kept in fase0/build
  model     an independent Python model of the probe's rules (input,
            sprite, fire, torch, note) against the bench, every frame
  openMSX   RAM #C000-#F37F, VRAM, VDP registers, PSG registers (but
            14, see openmsx_run.py) and the T-states of every
            frame_ready, bench = openMSX, every frame; three starts:
            the RAM and VRAM C-BIOS left, and two random fillings
  timing    three pieces of code (DJNZ, OUTI + JP NZ, LDIR): hand
            count with the M1 wait = bench = openMSX
  interrupt the frame period in T-states (lines x 228), frames counted
            50 or 60 a second; IM 2 against IM 1 + H.TIMI (C-BIOS)
  slots     page 2 on the cartridge after ENASLT
  50/60 Hz  byte #002B of every C-BIOS MSX1 ROM, and what the probe read
  shots     screenshots of openMSX (-raw): two runs identical; the
            renderer (tools/vram2png.py) gives the same pixels from
            the VRAM; the palette of openMSX measured
  sound     the note recorded by openMSX (soundlog) and its pitch;
            register 7 always 10xxxxxx; the joystick read while the
            note plays
  broken    the six broken versions, each stopped by its check

Writes OUT/fase0.json, OUT/png/*.png, OUT/wav/*.wav. --reference FILE
compares the bench's facts with another run of this script (the
workspace's, on the PC or on a second machine): they must be identical.
--no-openmsx runs only the bench (a second machine without openMSX).

The openMSX runs go to a temporary folder (OUT/runs with --keep-runs:
about 40 MB).

Usage: python tests/fase0_check.py --out DIR [--openmsx EXE |
           --no-openmsx] [--reference FILE] [--update-state]
           [--keep-runs]
"""
import argparse
import hashlib
import json
import math
import os
import struct
import sys
import tempfile
import time
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BUILD = ROOT / 'fase0' / 'build'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'tools'))
import msxsim  # noqa: E402
import openmsx_run  # noqa: E402
import vram2png  # noqa: E402
from msxtools import CBIOS, cbios_dir, find_tool, sha  # noqa: E402

MACHINES = {    # name: openMSX machine, Hz, main ROM
    'eu': ('C-BIOS_MSX1_EU', 50, CBIOS['eu']),
    'int': ('C-BIOS_MSX1', 60, CBIOS['int']),
}
FRAMES = 120
SEEDS = (None, 1, 2)
# the input, from frame_ready K on: (keys of row 8, joystick 1)
SCRIPT = {
    10: (('RIGHT',), ()),
    22: ((), ('UP',)),
    34: (('SPACE',), ()),
    36: ((), ()),
    40: ((), ('LEFT', 'DOWN', 'A')),
    52: ((), ()),
    60: (('UP', 'LEFT'), ('RIGHT',)),
    72: ((), ()),
    90: (('DOWN',), ('DOWN',)),
    96: ((), ()),
}
SHOTS = (40, 99)
CLOCK = 3579545
RUNS = None     # the openMSX runs: a temporary folder, or OUT/runs


class Checks:
    def __init__(self):
        self.items = []

    def add(self, name, ok, detail=''):
        self.items.append({'check': name, 'pass': bool(ok),
                           'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}"
              + (f'  ({detail})' if detail else ''))
        return ok

    @property
    def failed(self):
        return [c for c in self.items if not c['pass']]


def h(data):
    return hashlib.sha256(bytes(data)).hexdigest()[:16]


def rom(name):
    return (BUILD / f'{name}.rom').read_bytes(), \
        msxsim.read_symbols(BUILD / f'{name}.sym')


def cbios_roms(cdir, machine):
    main = (cdir / MACHINES[machine][2]).read_bytes()
    logo = (cdir / CBIOS['logo']).read_bytes()
    return main, logo


def input_at(k):
    """The input held at frame_ready k (set at frame_ready k - 1)."""
    keys, joy = (), ()
    for f in sorted(SCRIPT):
        if f <= k:
            keys, joy = SCRIPT[f]
    return keys, joy


# -- the model of the probe's rules --------------------------------------

class ProbeModel:
    """The rules of fase0/src/probe.asm, written from its comments:
    keys of row 8 or joystick 1 move sprite 0 one pixel a frame (up,
    down, left, right, all that are held); a new press of space or
    button A swaps white (15) and light yellow (11); every 4th frame
    the torch drawing takes the next of 8 phases; the note sounds from
    frame 25 to frame 74."""

    def __init__(self):
        self.frames = 0
        self.x, self.y, self.colour = 120, 60, 15
        self.prev = 0
        self.inp = 0
        self.phase = 0

    def frame(self, keys, joy):
        self.frames += 1
        bits = 0
        names = ('UP', 'DOWN', 'LEFT', 'RIGHT')
        for i, n in enumerate(names):
            if n in keys or n in joy:
                bits |= 1 << i
        if 'SPACE' in keys or 'A' in joy:
            bits |= 16
        self.prev, self.inp = self.inp, bits
        if bits & 1:
            self.y = (self.y - 1) & 255
        if bits & 2:
            self.y = (self.y + 1) & 255
        if bits & 4:
            self.x = (self.x - 1) & 255
        if bits & 8:
            self.x = (self.x + 1) & 255
        if bits & ~self.prev & 16:
            self.colour ^= 5
        if self.frames % 4 == 0:
            self.phase = (self.phase + 1) & 7
        self.note = 15 if 25 <= self.frames < 75 else 0

    def check(self, ram, vram, psg):
        """Differences between the model and a frame of the program."""
        out = []
        frames = ram[0] | ram[1] << 8
        want = {'frames': (frames, self.frames),
                'input': (ram[3], self.inp),
                'hero_x': (ram[7], self.x), 'hero_y': (ram[8], self.y),
                'hero_colour': (ram[9], self.colour),
                'torch_phase': (ram[10], self.phase),
                'SAT 0': (bytes(vram[0x1B00:0x1B04]),
                          bytes([self.y, self.x, 0, self.colour])),
                'PSG 8': (psg[8], self.note)}
        for k, (got, exp) in want.items():
            if got != exp:
                out.append(f'{k} {got!r} != {exp!r}')
        return out


# -- the bench -------------------------------------------------------------

def bench_run(name, state, cb, seed, frames, script=True, watch=()):
    data, sym = rom(name)
    m = msxsim.MSX(data, state, cb, seed=seed)
    m.watch = {sym[w]: w for w in watch}
    out = []
    for k in range(1, frames + 1):
        if script:
            m.set_input(*input_at(k))
        try:
            m.run_to(sym["frame_ready"], max_t=20 * m.vdp.frame_t)
        except RuntimeError as e:
            out.append({'error': str(e)})
            break
        out.append({'ram': bytes(m.mem[0xC000:0xF380]),
                    'vram': bytes(m.vdp.vram), 'vdp': list(m.vdp.regs),
                    'psg': list(m.psg.regs), 'a8': m.a8,
                    't': m.tstates, 'status': m.vdp.status})
    return m, out


def frame_facts(frames):
    return [{'t': f['t'], 'ram': h(f['ram']), 'vram': h(f['vram'])}
            if 'error' not in f else f for f in frames]


def compare(bench, emu, checks, tag):
    """Every frame: RAM, VRAM, VDP and PSG registers, T-states."""
    n = min(len(bench), len(emu))
    first_bad = None
    for k in range(n):
        b, e = bench[k], emu[k]
        if 'error' in b:
            first_bad = (k + 1, b['error'])
            break
        diffs = []
        if b['ram'] != e['ram']:
            i = next(i for i in range(len(b['ram']))
                     if b['ram'][i] != e['ram'][i])
            diffs.append(f'RAM ${0xC000 + i:04X}')
        if b['vram'] != e['vram']:
            i = next(i for i in range(0x4000)
                     if b['vram'][i] != e['vram'][i])
            diffs.append(f'VRAM ${i:04X}')
        if b['vdp'] != e['vdp']:
            diffs.append('VDP registers')
        if b['psg'][:14] + b['psg'][15:] != e['psg'][:14] + e['psg'][15:]:
            diffs.append('PSG registers')
        if b['t'] != e['t']:
            diffs.append(f"T {b['t']} != {e['t']}")
        if b['a8'] != e['a8']:
            diffs.append('slots')
        if diffs:
            first_bad = (k + 1, ', '.join(diffs))
            break
    ok = first_bad is None and len(bench) == len(emu)
    checks.add(f'{tag}: bench = openMSX, every frame', ok,
               f'{n} frames' if ok else
               f'frame {first_bad[0]}: {first_bad[1]}' if first_bad
               else f'{len(bench)} frames against {len(emu)}')
    return ok


# -- timing ----------------------------------------------------------------

def hand_counts():
    """The three pieces of code counted by hand, M1 waits included
    (the T-states of the Z80 manual + 1 for every M1 cycle)."""
    # t1: LD B,0 (7+1); DJNZ taken 255 times (13+1), not taken (8+1)
    t1 = 8 + 255 * 14 + 9
    # t2: 256 x (OUTI 16+2, JP NZ 10+1)
    t2 = 256 * (18 + 11)
    # t3: LDIR of 256 bytes: 255 x (21+2) and the last (16+2)
    t3 = 255 * 23 + 18
    return {'t1': t1, 't2': t2, 't3': t3}


def timings(marks):
    d = dict()
    for name, t in marks:
        d.setdefault(name, t)
    return {'t1': d['t1_end'] - d['timing_t1'],
            't2': d['t2_end'] - d['t2_loop'],
            't3': d['t3_end'] - d['t3_ldir']}


# -- sound ----------------------------------------------------------------

def wav_pitch(path):
    w = wave.open(str(path))
    n, ch, rate = w.getnframes(), w.getnchannels(), w.getframerate()
    s = struct.unpack('<%dh' % (n * ch), w.readframes(n))[::ch]
    peak = max(abs(x) for x in s) if s else 0
    loud = [i for i, x in enumerate(s) if abs(x) > 0.3 * peak]
    if peak < 200 or not loud:
        return None, 0.0
    # the pitch in the middle 60 % (away from the edges and the
    # output filter of openMSX), the length above 30 % of the peak
    cut = (loud[-1] - loud[0]) // 5
    seg = s[loud[0] + cut:loud[-1] - cut]
    mean = sum(seg) / len(seg)
    up = [i for i in range(1, len(seg))
          if seg[i - 1] - mean < 0 <= seg[i] - mean]
    freq = (len(up) - 1) / ((up[-1] - up[0]) / rate)
    return freq, (loud[-1] - loud[0]) / rate


def psg_wav(log, path, hz_clock=1789772.5, t_end=None, rate=44100):
    """Channel A of the PSG (tone and volume) from the register writes
    of the bench, as a square wave: for the author to listen to."""
    regs = [0] * 16
    events = sorted(log)
    t_end = t_end or (events[-1][0] + CLOCK)
    samples = bytearray()
    i, phase = 0, 0.0
    for n in range(int(t_end / CLOCK * rate)):
        t = n * CLOCK / rate
        while i < len(events) and events[i][0] <= t:
            regs[events[i][1]] = events[i][2]
            i += 1
        period = (regs[0] | (regs[1] & 15) << 8) or 1
        freq = hz_clock / 16 / period
        on = not regs[7] & 1
        vol = regs[8] & 15
        phase = (phase + freq / rate) % 1.0
        v = 8000 * vol // 15 if on and vol else 0
        samples += struct.pack('<h', v if phase < 0.5 else -v)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(samples))


# -- the checks ------------------------------------------------------------

def run_machine(mname, openmsx, cdir, out, checks, facts, args):
    machine, hz, mainrom = MACHINES[mname]
    frame_t = msxsim.LINES[hz] * msxsim.LINE_T
    data, sym = rom('probe')
    joy_read = openmsx_run.find_in(data, 0x4000, sym['in_joy'],
                                   (0xDB, 0xA2)) + 2
    f = facts[mname] = {}
    tag = f'{mname} ({hz} Hz)'
    state_file = BUILD / f'cbios_state_{mname}.json'
    # 1. the state at INIT
    if openmsx:
        r = openmsx_run.run(openmsx, BUILD / 'probe.rom', machine, sym,
                            8, RUNS / f'{mname}_state')
        state = openmsx_run.cbios_state(RUNS / f'{mname}_state',
                                        sym['init'], hz, frame_t)
        if state_file.exists() and not args.update_state:
            kept = json.loads(state_file.read_text())
            checks.add(f'{tag}: state at INIT = the one kept',
                       kept == state,
                       'fase0/build/' + state_file.name)
        else:
            state_file.write_text(json.dumps(state) + '\n')
    state = json.loads(state_file.read_text())
    f['vbl_after_init'] = state['vbl_after_init']
    f['init_slots'] = f"#{state['a8']:02X}"
    cb = cbios_roms(cdir, mname)
    # 2. bench and model, three starts
    runs = {}
    marks = None
    for seed in SEEDS:
        m, frames = bench_run('probe', state, cb, seed, FRAMES,
                              watch=('timing_t1', 't1_end', 't2_loop',
                                     't2_end', 't3_ldir', 't3_end',
                                     'isr'))
        runs[seed] = (m, frames)
        model = ProbeModel()
        bad = None
        for k, fr in enumerate(frames, 1):
            model.frame(*input_at(k))
            diff = model.check(fr['ram'], fr['vram'], fr['psg'])
            if diff:
                bad = (k, diff)
                break
        checks.add(f'{tag} seed {seed}: model = bench, every frame',
                   bad is None and len(frames) == FRAMES,
                   f'{len(frames)} frames' if bad is None else
                   f'frame {bad[0]}: {bad[1][:3]}')
        f[f'seed_{seed}'] = frame_facts(frames)
        if seed is None:
            marks = m.marks
            f['too_fast_rule'] = len(m.vdp.too_fast)
            checks.add(f'{tag}: no VRAM access closer than '
                       f'{msxsim.VRAM_GAP} T-states in the picture',
                       not m.vdp.too_fast, str(m.vdp.too_fast[:2]))
            checks.add(f'{tag}: no write to ROM', not m.rom_written())
            r7 = [v for t, r, v in m.psg.log if r == 7]
            checks.add(f'{tag}: PSG register 7 always 10xxxxxx',
                       r7 and all(v & 0xC0 == 0x80 for v in r7),
                       f'{len(r7)} writes')
            ram = frames[-1]['ram']
            checks.add(f'{tag}: page 2 on the cartridge (ENASLT)',
                       ram[0x0C] == 0xA5 and m.a8 & 0x3C == 0x14,
                       f'read #{ram[0x0C]:02X}, slots #{m.a8:02X}, '
                       f'cart_slot {ram[0x0B]}')
            b2b = cb[0][0x2B]
            checks.add(f'{tag}: #002B read = the ROM\'s, bit 7 = '
                       f'{int(hz == 50)}',
                       ram[0x0D] == b2b and (b2b >> 7) == (hz == 50),
                       f'#{ram[0x0D]:02X}')
            f['msx_id1'] = ram[0x0D]
            first = frames[0]['ram']
            checks.add(f'{tag}: nothing pressed: row 8 reads #FF, '
                       'empty joystick port 1 reads #BF (bits 0-5 at 1)',
                       first[5] == 0xFF and first[6] == 0xBF,
                       f'#{first[5]:02X} #{first[6]:02X}')
            # the frame
            irq = m.irq_log
            periods = [b - a for a, b in zip(irq, irq[1:])]
            mean = (irq[-1] - irq[1]) / (len(irq) - 2)
            f['frame_t'] = mean
            checks.add(f'{tag}: frame = {frame_t} T-states = '
                       f'{msxsim.LINES[hz]} lines x 228',
                       abs(mean - frame_t) < 0.2
                       and all(abs(p - frame_t) < 5 for p in periods[1:]),
                       f'mean {mean:.2f}, {min(periods[1:])}-'
                       f'{max(periods[1:])} (HALT cycles of 5)')
            frames_n = ram[0] | ram[1] << 8
            checks.add(f'{tag}: {FRAMES} frames, {FRAMES} interrupts',
                       frames_n == FRAMES, str(frames_n))
            busy = [fr['t'] - i for fr, i in
                    zip(frames[1:], irq[1:len(frames)])]
            f['irq_to_frame_ready'] = [min(busy), max(busy)]
            wav = out / 'wav'
            wav.mkdir(parents=True, exist_ok=True)
            psg_wav(m.psg.log, wav / f'bench_note_{mname}.wav',
                    t_end=frames[-1]['t'])
    # timing
    hand = hand_counts()
    bench_t = timings(marks)
    f['timing'] = {'hand': hand, 'bench': bench_t}
    checks.add(f'{tag}: T-states of t1 t2 t3, bench = hand count',
               bench_t == hand, f'{bench_t} / {hand}')
    if not openmsx:
        return
    # 3. openMSX: three starts, the same input
    for seed in SEEDS:
        rd = RUNS / f'{mname}_seed_{seed}'
        r = openmsx_run.run(openmsx, BUILD / 'probe.rom', machine, sym,
                            FRAMES, rd, seed=seed, inputs=SCRIPT,
                            joy_read=joy_read,
                            marks=('timing_t1', 't1_end', 't2_loop',
                                   't2_end', 't3_ldir', 't3_end'))
        compare(runs[seed][1], r['frames'], checks,
                f'{tag} seed {seed}')
        if seed is None:
            emu_t = timings(r['marks'])
            facts.setdefault('openmsx', {})[mname] = {'timing': emu_t}
            checks.add(f'{tag}: T-states of t1 t2 t3, openMSX = bench',
                       emu_t == bench_t, str(emu_t))
            m = runs[seed][0]
            n = len(r['irq'])
            checks.add(f'{tag}: interrupts at the same T-states',
                       r['irq'][:n] == m.irq_log[:n],
                       f'{n} interrupts')
            checks.add(f'{tag}: openMSX dropped no VRAM access',
                       not r['too_fast'], str(r['too_fast'][:2]))
            if seed is None and mname == 'eu':
                rd2 = RUNS / f'{mname}_seed_{seed}_again'
                openmsx_run.run(openmsx, BUILD / 'probe.rom', machine,
                                sym, FRAMES, rd2, seed=seed,
                                inputs=SCRIPT, joy_read=joy_read)
                same = (rd / 'frames.bin').read_bytes() == \
                    (rd2 / 'frames.bin').read_bytes()
                checks.add(f'{tag}: two openMSX runs, the same bytes',
                           same)


def screenshots(openmsx, out, checks, facts):
    """Two runs with screenshots: identical; = the renderer."""
    data, sym = rom('probe')
    joy_read = openmsx_run.find_in(data, 0x4000, sym['in_joy'],
                                   (0xDB, 0xA2)) + 2
    png = out / 'png'
    png.mkdir(parents=True, exist_ok=True)
    runs = []
    for i in (1, 2):
        rd = RUNS / f'shots_{i}'
        r = openmsx_run.run(openmsx, BUILD / 'probe.rom',
                            'C-BIOS_MSX1_EU', sym, max(SHOTS) + 3, rd,
                            inputs=SCRIPT, shots=SHOTS,
                            joy_read=joy_read)
        runs.append((rd, r))
    palette = {}
    unmatched = []
    same_pixels = True
    shot_facts = {}
    delays = {1: {}, 2: {}}

    def clashes(rows, a, pal):
        n = 0
        for y in range(len(a)):
            for x in range(len(a[0])):
                if pal.setdefault(rows[y][x], a[y][x]) != a[y][x]:
                    n += 1
        return n

    # openMSX's screenshot at a stop shows the picture of an earlier
    # frame, 1 to 3 back, and how far back changes from run to run
    # (found on the author's PC, 8 November): the figures are drawn
    # from the VRAM, so what must be the same in two runs is the VRAM;
    # every screenshot must be the drawing of one of those VRAMs.
    for i, (rd, r) in enumerate(runs, 1):
        for k in SHOTS:
            for kk in (k, k + 2):
                a = vram2png.read_png_rgb(rd / f'shot_{kk}.png')
                found = None
                for back in (1, 2, 3):
                    fr = r['frames'][kk - 1 - back]
                    rows = vram2png.frame(fr['vram'], fr['vdp'])
                    trial = dict(palette)
                    if clashes(rows, a, trial) == 0:
                        found = back
                        palette = trial
                        break
                delays[i][kk] = found
                if found is None:
                    unmatched.append((i, kk))
                if i == 1:
                    b = vram2png.read_png_rgb(runs[1][0] / f'shot_{kk}.png')
                    same_pixels &= a == b
                    shot_facts[kk] = h(bytes(v for row in a for p in row
                                             for v in p))
                    (png / f'openmsx_frame{kk}.png').write_bytes(
                        (rd / f'shot_{kk}.png').read_bytes())
    facts['shot_delay'] = delays
    facts['shots_same_pixels'] = same_pixels
    n = max(SHOTS) + 3
    same_vram = all(runs[0][1]['frames'][j]['vram'] ==
                    runs[1][1]['frames'][j]['vram'] for j in range(n))
    checks.add('shots: two runs, the same VRAM in every frame (the '
               'source of the figures)', same_vram,
               f'{n} frames; screenshots identical: {same_pixels}')
    checks.add('shots: renderer from VRAM = openMSX, every pixel of '
               'every screenshot (geometry left 32, top 24)',
               not unmatched,
               f'frames back: run 1 {delays[1]}, run 2 {delays[2]}'
               + (f'; unmatched {unmatched}' if unmatched else ''))
    pal = {str(c): list(rgb) for c, rgb in sorted(palette.items())}
    facts['palette_openmsx'] = pal
    facts['shots'] = shot_facts
    checks.add('shots: all 15 colours seen',
               sorted(palette) == list(range(1, 16)),
               f'indices {sorted(palette)}')
    if vram2png.PALETTE_OPENMSX:
        checks.add('shots: palette = the one in tools/vram2png.py',
                   all(tuple(vram2png.PALETTE_OPENMSX[c]) == tuple(v)
                       for c, v in palette.items()))
    # renderer PNGs (x4, no smoothing) for the author to look at
    full = [None] + [tuple(pal[str(i)]) if str(i) in pal else (0, 0, 0)
                     for i in range(1, 16)]
    full[0] = full[1]
    for k in SHOTS:
        fr = runs[0][1]['frames'][k - 2]
        rows = vram2png.frame(fr['vram'], fr['vdp'])
        (png / f'renderer_frame{k}_x4.png').write_bytes(
            vram2png.png_bytes(rows, full, 4))


def sound(openmsx, out, checks, facts):
    """The note, recorded by openMSX's soundlog."""
    data, sym = rom('probe')
    rd = RUNS / 'sound'
    rd.mkdir(parents=True, exist_ok=True)
    wav = out / 'wav' / 'openmsx_note_eu.wav'
    wav.parent.mkdir(parents=True, exist_ok=True)
    script = (
        'set renderer none\nset throttle off\n'
        f'debug set_bp {sym["init"]} {{}} {{ '
        f'soundlog start {{{wav.as_posix()}}}; after time 2.5 '
        '{ soundlog stop; exit } }\n')
    (rd / 'sound.tcl').write_text(script)
    import subprocess
    subprocess.run([openmsx, '-machine', 'C-BIOS_MSX1_EU', '-cart',
                    str(BUILD / 'probe.rom'), '-script',
                    str(rd / 'sound.tcl')], capture_output=True,
                   timeout=120)
    freq, dur = wav_pitch(wav) if wav.exists() else (None, 0)
    expect = 1789772.5 / 16 / 254
    facts['note'] = {'expected_hz': round(expect, 3),
                     'openmsx_hz': round(freq, 2) if freq else None,
                     'seconds': round(dur, 3)}
    checks.add('sound: openMSX note at 1 789 772.5 / 16 / 254 Hz',
               freq is not None and abs(freq - expect) < 0.05,
               f'{freq:.2f} Hz, {dur:.2f} s' if freq else 'no sound')
    checks.add('sound: the note lasts 50 frames (0.997 s at 50 Hz)',
               abs(dur - 50 * 71364 / CLOCK) < 0.01, f'{dur:.3f} s')


def irq_cost(openmsx, cdir, out, checks, facts):
    """IM 2 (ours) against IM 1 and H.TIMI (the BIOS's handler)."""
    res = {}
    state = json.loads((BUILD / 'cbios_state_eu.json').read_text())
    for name in ('probe', 'probe_im1'):
        data, sym = rom(name)
        r = openmsx_run.run(openmsx, BUILD / f'{name}.rom',
                            'C-BIOS_MSX1_EU', sym, 30,
                            RUNS / f'cost_{name}')
        busy = [fr['t'] - i for fr, i in zip(r['frames'][2:],
                                             r['irq'][2:])]
        res[name] = {'openmsx': [min(busy), max(busy)]}
        if name == 'probe_im1':
            m, frames = bench_run(name, state, cbios_roms(cdir, 'eu'),
                                  None, 30, script=False)
            ok = len(frames) == 30 and 'error' not in frames[-1]
            if ok:
                compare(frames, r['frames'], checks,
                        'IM 1 + H.TIMI (C-BIOS handler in the bench)')
            bb = [fr['t'] - i for fr, i in zip(frames[2:],
                                              m.irq_log[2:])]
            res[name]['bench'] = [min(bb), max(bb)] if bb else None
    extra = res['probe_im1']['openmsx'][0] - res['probe']['openmsx'][0]
    facts['irq_cost'] = dict(res, extra_bios=extra)
    checks.add('interrupt: the BIOS way costs more T-states a frame',
               extra > 0, f'IM 2 {res["probe"]["openmsx"]}, IM 1 + '
               f'H.TIMI {res["probe_im1"]["openmsx"]}: +{extra} T')


def broken(openmsx, cdir, out, checks, facts):
    """Each broken version, stopped by its check, in the bench and in
    openMSX."""
    state = json.loads((BUILD / 'cbios_state_eu.json').read_text())
    cb = cbios_roms(cdir, 'eu')
    res = {}

    def both(name, frames=60, script=True):
        data, sym = rom(name)
        m, fb = bench_run(name, state, cb, 1, frames, script=script)
        r = None
        if openmsx:
            jr = openmsx_run.find_in(data, 0x4000, sym['in_joy'],
                                     (0xDB, 0xA2)) + 2
            r = openmsx_run.run(openmsx, BUILD / f'{name}.rom',
                                'C-BIOS_MSX1_EU', sym, frames,
                                RUNS / name, seed=1,
                                inputs=SCRIPT if script else None,
                                joy_read=jr, max_seconds=6)
        return m, fb, r

    # x1: status not read: the interrupt comes back at once
    m, fb, r = both('probe_x1', 5)
    stopped = 'error' in fb[0]
    emu = None if r is None else len(r['frames'])
    checks.add('broken x1 (status not read): frame_ready never '
               'reached', stopped and (emu in (None, 0)),
               f"bench: {fb[0].get('error', 'reached')[:40]}; "
               f'openMSX frames: {emu}')
    res['x1'] = {'bench_irqs': len(m.irq_log), 'openmsx_frames': emu}
    # x2: register 7 bit 6 at 1: port A as an output. The C-BIOS
    # machines of openMSX ignore it (and say so through a callback);
    # on an MSX that obeys it, the joystick would read nothing.
    m, fb, r = both('probe_x2', 34)
    bad7 = [v for t, rg, v in m.psg.log if rg == 7 and v & 0xC0 != 0x80]
    y = fb[-1]['ram'][8]
    calls = None if r is None else len(r['psg_directions'])
    checks.add('broken x2 (register 7 = 11xxxxxx): stopped by the rule '
               'of register 7 (bench) and by openMSX\'s callback',
               bad7 and (r is None or calls),
               f'bench: {len(bad7)} writes; openMSX: {calls} callbacks;'
               f' joystick still read (hero_y {y}): ignored by the '
               'C-BIOS machines')
    res['x2'] = {'bad_r7': len(bad7), 'hero_y': y,
                 'openmsx_callbacks': calls}
    # x3: ENASLT forgotten: page 2 is RAM
    m, fb, r = both('probe_x3', 10, script=False)
    ram = fb[-1]['ram']
    vr = fb[-1]['vram']
    checks.add('broken x3 (ENASLT forgotten): page 2 not the '
               'cartridge, thirds and sprite lost',
               ram[0x0C] != 0xA5 and vr[0:8] != bytes(
                   [0xFF, 0x81, 0x81, 0x81, 0xFF, 0x18, 0x18, 0x18])
               and (r is None or r['frames'][-1]['ram'][0x0C] != 0xA5),
               f'read #{ram[0x0C]:02X}, slots #{m.a8:02X}')
    res['x3'] = {'page2_read': ram[0x0C], 'slots': m.a8}
    # x4: Y = 208 on sprite 1: the list ends there
    m, fb, r = both('probe_x4', 10, script=False)
    st = fb[-1]['ram'][2]
    checks.add('broken x4 (Y = 208 on sprite 1): one sprite only',
               st & 0x1F == 1 and (r is None or
                                   r['frames'][-1]['ram'][2] == st),
               f'status #{st:02X} (sprite number 1)')
    res['x4'] = {'status': st}
    # x5: five sprites on a line: 5S and the fifth's number
    m, fb, r = both('probe_x5', 10, script=False)
    st = fb[-1]['ram'][2]
    rows = vram2png.indices(fb[-1]['vram'], fb[-1]['vdp'])
    line = rows[msxsim_row_y() + 5]
    shown = sorted(set(c for c in line if c in (8, 10, 12, 13, 6)))
    checks.add('broken x5 (five sprites on a line): 5S, sprite 5, '
               'the fifth not drawn',
               st & 0x40 and st & 0x1F == 5 and 6 not in shown
               and (r is None or r['frames'][-1]['ram'][2] == st),
               f'status #{st:02X}, colours on the line {shown}')
    res['x5'] = {'status': st}
    # x6: VRAM too fast in the picture
    m, fb, r = both('probe_x6', 10, script=False)
    rule = len(m.vdp.too_fast)
    dropped = None if r is None else len(r['too_fast'])
    lost = None
    if r is not None:
        lost = r['frames'][-1]['vram'][0x808:0x810] != \
            fb[-1]['vram'][0x808:0x810]
    checks.add('broken x6 (OUTI 18 T apart in the picture): the bench '
               'rule and openMSX\'s dropped writes',
               rule > 0 and (r is None or (dropped and lost)),
               f'bench: {rule} accesses < {msxsim.VRAM_GAP} T; openMSX:'
               f' {dropped} dropped, torch bytes lost: {lost}')
    res['x6'] = {'rule': rule, 'openmsx_dropped': dropped}
    facts['broken'] = res


def msxsim_row_y():
    return 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--openmsx')
    ap.add_argument('--no-openmsx', action='store_true')
    ap.add_argument('--reference')
    ap.add_argument('--update-state', action='store_true')
    ap.add_argument('--keep-runs', action='store_true')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    global RUNS
    if args.keep_runs:
        RUNS = out / 'runs'
    else:
        tmp = tempfile.TemporaryDirectory()
        RUNS = Path(tmp.name)
    start = time.time()
    openmsx = None if args.no_openmsx else find_tool('openmsx',
                                                     args.openmsx)
    cdir = cbios_dir(openmsx)
    if cdir is None:
        print('C-BIOS not found')
        return 1
    checks = Checks()
    facts = {'openmsx_exe': openmsx, 'cbios_dir': str(cdir),
             'cbios_002B': {k: f'#{(cdir / v).read_bytes()[0x2B]:02X}'
                            for k, v in CBIOS.items() if k != 'logo'}}
    for k, v in facts['cbios_002B'].items():
        print(f'C-BIOS {k}: #002B = {v}')
    for mname in MACHINES:
        run_machine(mname, openmsx, cdir, out, checks, facts, args)
    if openmsx:
        screenshots(openmsx, out, checks, facts)
        sound(openmsx, out, checks, facts)
        irq_cost(openmsx, cdir, out, checks, facts)
    broken(openmsx, cdir, out, checks, facts)
    bench_facts = {k: facts[k] for k in MACHINES}
    bench_facts['broken'] = facts['broken']
    if args.reference:
        ref = json.loads(Path(args.reference).read_text())
        rf = {k: ref['facts'][k] for k in MACHINES}
        rf['broken'] = ref['facts']['broken']
        diff = [k for k in bench_facts
                if json.dumps(_only_bench(bench_facts[k]),
                              sort_keys=True,
                              default=str) !=
                json.dumps(_only_bench(rf[k]), sort_keys=True,
                           default=str)]
        checks.add('bench facts = the reference run', not diff,
                   f'{args.reference}' + (f': differ in {diff}'
                                          if diff else ''))
    report = {'python': sys.version.split()[0],
              'skoolkit': __import__('skoolkit').VERSION,
              'seconds': round(time.time() - start, 1),
              'checks': checks.items, 'facts': facts,
              'failed': len(checks.failed)}
    (out / 'fase0.json').write_text(
        json.dumps(report, indent=1, default=str) + '\n',
        encoding='utf-8')
    print(f"\n{len(checks.items) - len(checks.failed)} of "
          f"{len(checks.items)} checks passed "
          f"({report['seconds']} s); report: {out / 'fase0.json'}")
    return 1 if checks.failed else 0


def _only_bench(d):
    """The facts without what openMSX gave (a machine without
    openMSX has only the bench's)."""
    if isinstance(d, dict):
        return {k: _only_bench(v) for k, v in d.items()
                if not k.startswith('openmsx')}
    return d


if __name__ == '__main__':
    sys.exit(main())

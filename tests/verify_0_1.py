"""Milestone 0.1 checks: the Moss Gate in Screen 2, the two versions
of the graphics (A, B), on the two C-BIOS MSX1 machines (EU:
TMS9929A, 50 Hz; INT: TMS9918A, 60 Hz).

  state     the BIOS state at INIT of every game ROM, read from
            openMSX; compared with the one kept in game/build
  model     the game (the Moss Gate) in the bench, 120 frames, three
            starts (the RAM and VRAM C-BIOS left, two random
            fillings): the screen of every frame = the model
            (tests/msx_model.py) with the flame of phase
            (frames / 8) mod 4; the frame counter, the room, the
            zone, the HUD's variables, the stack
  rooms     a ROM for every room (START_ROOM 0-15): in openMSX (50
            Hz, with screenshots) and in the bench with the state of
            that run, every frame bench = openMSX and screen = model;
            in the bench at 60 Hz too
  openMSX   the game in openMSX, the same three starts: RAM, VRAM,
            VDP and PSG registers (but 14) and T-states of every
            frame_ready = bench; interrupts at the same T-states
  palettes  the Phase 0 probe on both machines: its screenshots show
            the 15 colours of tools/vram2png.py, the TMS9929A's at 50
            Hz and the TMS9918A's at 60 Hz (openMSX gives them
            different colours)
  shots     the screenshots of openMSX, taken in the middle of a
            phase of the flame (so the 1-3 frames they lag do not
            matter) = the model drawn with the machine's palette,
            every pixel and the border
  rules     no VRAM access closer than 29 T-states in the picture,
            nothing dropped by openMSX, no write to ROM, PSG register
            7 always 10xxxxxx, no sprite (Y = 208 at #1B00), the
            VDP registers of Screen 2; RAM written only in the areas
            of game/src/vars.asm and the stack
  measures  T-states of the start-up and of its parts, of every frame
            (interrupt to frame_ready, with and without the torches),
            the lines where the frames write VRAM, the stack's depth,
            the cartridge's bytes (game/build/manifest.json)
  mutations copies of the source with one mistake each: every one
            must be stopped by the check named

Writes OUT/verify_0_1.json, the captures in OUT/png (the screenshots
of openMSX as they are, and sheets made from them: A and B side by
side, the 16 rooms, the torch in its four phases). --reference
FILE compares the facts with another run (the workspace's, on the
PC); --no-openmsx runs only the bench.

Usage: python tests/verify_0_1.py --out DIR [--openmsx EXE |
           --no-openmsx] [--reference FILE] [--update-state]
           [--keep-runs]
Needs the build: python tools/build_game.py
"""
import argparse
import hashlib
import json
import shutil
import struct
import sys
import tempfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BUILD = ROOT / 'game' / 'build'
SRC = ROOT / 'game' / 'src'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'tools'))
import msx_model  # noqa: E402
import msxsim  # noqa: E402
import openmsx_run  # noqa: E402
import vram2png  # noqa: E402
from msxtools import CBIOS, cbios_dir, find_tool, run  # noqa: E402

MACHINES = {    # name: openMSX machine, Hz
    'eu': ('C-BIOS_MSX1_EU', 50),
    'int': ('C-BIOS_MSX1', 60),
}
VERSIONS = ('A', 'B')
GAME_ROOM = 1
FRAMES = 120
ROOM_FRAMES = 47
SEEDS = (None, 1, 2)
GAME_SHOTS = (4, 12, 20, 28)     # and +2: phases 0, 1, 2, 3
ROOM_SHOTS = (44,)               # and 46: phase 1
# the RAM of game/src/vars.asm: [first, last + 1)
RAM_AREAS = ((0xC000, 0xC044), (0xC100, 0xC3A0), (0xF000, 0xF101),
             (0xF1F1, 0xF1F4))
STACK, STACK_ROOM = 0xF380, 64
VDP_REGS = [0x02, 0xE2, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x01]
WATCH = ('init', 'vdp_init', 'psg_init', 'load_glyphs', 'enter_room',
         'load_zone', 'build_names', 'put_names', 'hud_draw',
         'irq_init', 'main_loop', 'isr', 'frame_ready')
RUNS = None


class Checks:
    def __init__(self):
        self.items = []

    def add(self, name, ok, detail=''):
        self.items.append({'check': name, 'pass': bool(ok),
                           'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}"
              + (f'  ({detail})' if detail else ''), flush=True)
        return ok

    @property
    def failed(self):
        return [c for c in self.items if not c['pass']]


def h(data):
    return hashlib.sha256(bytes(data)).hexdigest()[:16]


def rom_files(name):
    return (BUILD / f'{name}.rom').read_bytes(), \
        msxsim.read_symbols(BUILD / f'{name}.sym')


def cbios_roms(cdir, mname):
    key = 'eu' if mname == 'eu' else 'int'
    return ((cdir / CBIOS[key]).read_bytes(),
            (cdir / CBIOS['logo']).read_bytes())


# -- the model, cached ------------------------------------------------

_MODEL = {}


def model(name, phase, v):
    key = (name, phase, v)
    if key not in _MODEL:
        _MODEL[key] = msx_model.screen(name, phase, v)
    return _MODEL[key]


def model_frame(name, phase, v):
    """The model as openMSX shows it: 320 x 240, the border."""
    g = vram2png.GEOMETRY
    back = VDP_REGS[7] & 15
    out = [[back] * g['width'] for _ in range(g['height'])]
    for y, row in enumerate(model(name, phase, v)):
        out[g['top'] + y][g['left']:g['left'] + 256] = row
    return out


_SCREEN = {}


def screen_of(vram, regs):
    key = hashlib.sha1(bytes(vram) + bytes(regs)).digest()
    if key not in _SCREEN:
        _SCREEN[key] = vram2png.indices(vram, regs)
    return _SCREEN[key]


def first_diff(a, b):
    for y in range(len(a)):
        if a[y] != b[y]:
            x = next(i for i in range(len(a[y])) if a[y][i] != b[y][i])
            return y, x, a[y][x], b[y][x]
    return None


# -- the bench ----------------------------------------------------------

def bench_run(rom, sym, state, cb, seed, frames, watch=False,
              log_vram=False):
    m = msxsim.MSX(rom, state, cb, seed=seed)
    if watch:
        m.watch = {sym[w]: w for w in WATCH}
    if log_vram:
        m.vram_log = []
        vdp = m.vdp
        plain = vdp.vram_access

        def logged(t, pc):
            m.vram_log.append(t)
            plain(t, pc)
        vdp.vram_access = logged
    out = []
    for k in range(1, frames + 1):
        try:
            m.run_to(sym['frame_ready'], max_t=40 * m.vdp.frame_t)
        except RuntimeError as e:
            out.append({'error': str(e)})
            break
        out.append({'ram': bytes(m.mem[0xC000:0xF380]),
                    'vram': bytes(m.vdp.vram), 'vdp': list(m.vdp.regs),
                    'psg': list(m.psg.regs), 'a8': m.a8,
                    't': m.tstates, 'sp': m.regs[msxsim.SP_]})
    return m, out


def frame_checks(frames, name, v, zone, start, want=None):
    """Every frame against the model and the variables. Returns
    {check: None or the first problem}."""
    want = want or len(frames)
    bad = {'reached': None, 'screen': None, 'variables': None,
           'registers': None}
    if len(frames) < want or 'error' in frames[-1]:
        err = frames[-1].get('error', '') if frames else ''
        bad['reached'] = f'{len(frames) - bool(err)} of {want} ' \
                         f'frames {err}'
    for k, fr in enumerate(frames, 1):
        if 'error' in fr:
            break
        ram = fr['ram']
        if bad['screen'] is None:
            got = screen_of(fr['vram'], fr['vdp'])
            d = first_diff(got, model(name, (k >> 3) & 3, v))
            if d:
                bad['screen'] = (f'frame {k}: pixel ({d[1]}, {d[0]}) '
                                 f'colour {d[2]}, model {d[3]}')
        if bad['variables'] is None:
            count = ram[0] | ram[1] << 8
            vals = {'frames': (count, k), 'room': (ram[5], start),
                    'zone': (ram[6], zone), 'energy': (ram[0x1C], 8),
                    'keys': (ram[0x1D], 0), 'seals': (ram[0x1E], 0),
                    'score': (bytes(ram[0x1F:0x22]), bytes(3)),
                    'SP': (fr['sp'], STACK)}
            wrong = [f'{n} {a} not {b}' for n, (a, b) in vals.items()
                     if a != b]
            if wrong:
                bad['variables'] = f'frame {k}: ' + ', '.join(wrong)
        if bad['registers'] is None:
            if fr['vdp'] != VDP_REGS or fr['vram'][0x1B00] != 208:
                bad['registers'] = (f"frame {k}: VDP "
                                    f"{[hex(x) for x in fr['vdp']]}, "
                                    f"Y0 {fr['vram'][0x1B00]}")
    return bad


def rule_checks(m):
    r7 = [val for t, r, val in m.psg.log if r == 7]
    return {'29T': m.vdp.too_fast[:2] or None,
            'rom': m.rom_written() or None,
            'r7': None if r7 and all(x & 0xC0 == 0x80 for x in r7)
            else [hex(x) for x in r7[:3]]}


def ram_written(runs):
    """Addresses of #C000-#F37F that differ from the random filling
    at the end, in any of the runs with a filling."""
    out = set()
    for seed, frames in runs.items():
        if seed is None or 'error' in frames[-1]:
            continue
        fill = msxsim.random_fill(seed)['ram']
        last = frames[-1]['ram']
        out |= {0xC000 + i for i in range(len(fill))
                if fill[i] != last[i]}
    return out


def ram_check(written):
    inside = set()
    for lo, hi in RAM_AREAS:
        inside |= set(range(lo, hi))
    stack = [a for a in written if STACK - STACK_ROOM <= a < STACK]
    outside = sorted(a for a in written
                     if a not in inside and
                     not STACK - STACK_ROOM <= a < STACK)
    depth = STACK - min(stack) if stack else 0
    return outside, depth


def measures(m, sym, frames):
    marks = {}
    for name, t in m.marks:
        marks.setdefault(name, t)
    order = ['vdp_init', 'psg_init', 'load_glyphs', 'enter_room',
             'load_zone', 'build_names', 'put_names', 'hud_draw',
             'irq_init', 'main_loop']
    parts = {a: marks[b] - marks[a] for a, b in zip(order, order[1:])
             if a in marks and b in marks}
    parts['start-up'] = marks['main_loop'] - marks['init']
    irq = m.irq_log
    ready = [f['t'] for f in frames]
    busy = [r - i for r, i in zip(ready, irq)]
    torch = [b for k, b in enumerate(busy, 1) if k % 8 == 0]
    quiet = [b for k, b in enumerate(busy, 1) if k % 8]
    # lines of the frame where VRAM is written once running
    start = marks['main_loop']
    fr_t = m.vdp.frame_t
    lines = sorted({((t - m.vdp.picture_start) % fr_t) // 228
                    for t in m.vram_log if t > start})
    return {'parts': parts, 'frame_t': fr_t,
            'busy_torches': [min(torch), max(torch)],
            'busy_quiet': [min(quiet), max(quiet)],
            'busy_max_percent': round(100 * max(busy) / fr_t, 2),
            'vram_lines': [lines[0], lines[-1]] if lines else None}


# -- openMSX --------------------------------------------------------------

def emu_compare(bench, emu):
    n = min(len(bench), len(emu))
    for k in range(n):
        b, e = bench[k], emu[k]
        if 'error' in b:
            return f'frame {k + 1}: {b["error"]}'
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
            return f'frame {k + 1}: ' + ', '.join(diffs)
    if len(bench) != len(emu):
        return f'{len(bench)} frames against {len(emu)}'
    return None


def emu_run(openmsx, rom_name, mname, frames, rd, seed=None, shots=()):
    machine, hz = MACHINES[mname]
    sym = msxsim.read_symbols(BUILD / f'{rom_name}.sym')
    return openmsx_run.run(openmsx, BUILD / f'{rom_name}.rom', machine,
                           sym, frames, rd, seed=seed, shots=shots,
                           max_seconds=round(6 + frames / 50, 2))


def state_of(rd, sym, mname):
    hz = MACHINES[mname][1]
    return openmsx_run.cbios_state(rd, sym['init'], hz,
                                   msxsim.LINES[hz] * msxsim.LINE_T)


def shot_ok(path, name, phase, v, hz):
    """A screenshot = the model with the machine's palette, every
    pixel."""
    got = vram2png.read_png_rgb(path)
    want = model_frame(name, phase, v)
    pal = vram2png.palette(hz)
    for y in range(len(want)):
        row = [tuple(pal[c]) for c in want[y]]
        if got[y] != row:
            x = next(i for i in range(len(row)) if got[y][i] != row[i])
            return f'{path.name}: pixel ({x}, {y}) {got[y][x]}, ' \
                   f'model {row[x]}'
    return None


def shot_hash(path):
    rows = vram2png.read_png_rgb(path)
    return h(bytes(v for row in rows for p in row for v in p))


# -- pictures -------------------------------------------------------------

def png_rgb(rows, scale=1):
    w, hh = len(rows[0]), len(rows)
    raw = bytearray()
    for row in rows:
        line = bytearray()
        for p in row:
            line += bytes(p) * scale
        for _ in range(scale):
            raw += b'\0' + line
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    head = struct.pack('>IIBBBBB', w * scale, hh * scale, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', head)
            + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
            + chunk(b'IEND', b''))


def sheet(images, cols, gap=8, colour=(40, 40, 40)):
    """Images (rows of RGB) of one size in a grid."""
    hh, w = len(images[0]), len(images[0][0])
    n_rows = -(-len(images) // cols)
    W = cols * w + (cols + 1) * gap
    H = n_rows * hh + (n_rows + 1) * gap
    out = [[colour] * W for _ in range(H)]
    for i, img in enumerate(images):
        r, c = divmod(i, cols)
        y0, x0 = gap + r * (hh + gap), gap + c * (w + gap)
        for y in range(hh):
            out[y0 + y][x0:x0 + w] = img[y]
    return out


def crop(img, x, y, w, hh):
    return [row[x:x + w] for row in img[y:y + hh]]


# -- the parts ------------------------------------------------------------

def game(openmsx, cdir, checks, facts, args, png):
    for v in VERSIONS:
        name = msx_model.rooms()[GAME_ROOM]
        zone = msx_model.zone_of(name)
        rom, sym = rom_files(f'cryptmorrow_{v}')
        for mname, (machine, hz) in MACHINES.items():
            tag = f'{v} {mname} ({hz} Hz)'
            f = facts.setdefault(f'{v}_{mname}', {})
            state_file = BUILD / f'state_{v}_{mname}.json'
            if openmsx:
                rd = RUNS / f'{v}_{mname}_state'
                emu_run(openmsx, f'cryptmorrow_{v}', mname, 8, rd)
                state = state_of(rd, sym, mname)
                if state_file.exists() and not args.update_state:
                    kept = json.loads(state_file.read_text())
                    checks.add(f'{tag}: state at INIT = the one kept',
                               kept == state,
                               'game/build/' + state_file.name)
                else:
                    state_file.write_text(json.dumps(state) + '\n')
            state = json.loads(state_file.read_text())
            cb = cbios_roms(cdir, mname)
            runs = {}
            for seed in SEEDS:
                m, frames = bench_run(rom, sym, state, cb, seed, FRAMES,
                                      watch=seed is None,
                                      log_vram=seed is None)
                runs[seed] = (m, frames)
                bad = frame_checks(frames, name, v, zone, GAME_ROOM,
                                   FRAMES)
                for what, label in (
                        ('reached', 'frame_ready every frame'),
                        ('screen', 'screen = model, every frame'),
                        ('variables', 'counter, room, zone, HUD, '
                                      'stack, every frame'),
                        ('registers', 'VDP registers of Screen 2, no '
                                      'sprite')):
                    checks.add(f'{tag} seed {seed}: {label}',
                               bad[what] is None,
                               bad[what] or f'{len(frames)} frames')
                f[f'seed_{seed}'] = [
                    {'t': fr['t'], 'ram': h(fr['ram']),
                     'vram': h(fr['vram'])} if 'error' not in fr
                    else fr for fr in frames]
                rules = rule_checks(m)
                checks.add(f'{tag} seed {seed}: no VRAM access closer '
                           f'than {msxsim.VRAM_GAP} T in the picture, '
                           'no write to ROM, PSG R7 10xxxxxx',
                           not any(rules.values()), str(rules))
            written = ram_written({s: fr for s, (m, fr) in runs.items()})
            outside, depth = ram_check(written)
            f['stack_depth'] = depth
            checks.add(f'{tag}: RAM written only in the areas of '
                       'vars.asm and the stack (seeds 1, 2)',
                       not outside and 0 < depth <= STACK_ROOM,
                       f'stack {depth} bytes' + (
                           f'; outside {[hex(a) for a in outside[:4]]}'
                           if outside else ''))
            m0, fr0 = runs[None]
            mea = measures(m0, sym, fr0)
            f['measures'] = mea
            checks.add(f'{tag}: a frame within its time, VRAM written '
                       'only out of the picture (lines 192 and after)',
                       mea['busy_max_percent'] < 100 and
                       mea['vram_lines'] and mea['vram_lines'][0] >= 192,
                       f"busy {mea['busy_quiet']} / {mea['busy_torches']}"
                       f" T of {mea['frame_t']}; lines "
                       f"{mea['vram_lines']}")
            checks.add(f'{tag}: {FRAMES} frames, {FRAMES} interrupts',
                       len(m0.irq_log) == FRAMES,
                       str(len(m0.irq_log)))
            if not openmsx:
                continue
            for seed in SEEDS:
                rd = RUNS / f'{v}_{mname}_seed_{seed}'
                r = emu_run(openmsx, f'cryptmorrow_{v}', mname, FRAMES,
                            rd, seed=seed)
                bad = emu_compare(runs[seed][1], r['frames'])
                checks.add(f'{tag} seed {seed}: bench = openMSX, every '
                           'frame', bad is None,
                           bad or f"{len(r['frames'])} frames")
                if seed is None:
                    n = len(r['irq'])
                    checks.add(f'{tag}: interrupts at the same '
                               'T-states', n == FRAMES and
                               r['irq'] == m0.irq_log[:n],
                               f'{n} interrupts')
                checks.add(f'{tag} seed {seed}: openMSX dropped no VRAM '
                           'access, no PSG port A as output',
                           not r['too_fast'] and
                           not r['psg_directions'],
                           f"{r['too_fast'][:2]} {r['psg_directions'][:2]}")
            # the real captures: the four phases of the flame
            rd = RUNS / f'{v}_{mname}_shots'
            r = emu_run(openmsx, f'cryptmorrow_{v}', mname,
                        max(GAME_SHOTS) + 3, rd, shots=GAME_SHOTS)
            bad, hashes = [], {}
            for k in GAME_SHOTS:
                for kk in (k, k + 2):
                    p = rd / f'shot_{kk}.png'
                    if not p.exists():
                        bad.append(f'shot_{kk}.png missing')
                        continue
                    e = shot_ok(p, name, (k >> 3) & 3, v, hz)
                    if e:
                        bad.append(e)
                    hashes[kk] = shot_hash(p)
                ph = (k >> 3) & 3
                if (rd / f'shot_{k}.png').exists():
                    shutil.copy(rd / f'shot_{k}.png',
                                png / f'moss_gate_{v}_{hz}hz_phase{ph}'
                                '.png')
            facts.setdefault('openmsx', {})[f'{v}_{mname}_shots'] = hashes
            checks.add(f'{tag}: screenshots of the four phases = '
                       'the model, every pixel', not bad,
                       bad[0] if bad else f'{len(hashes)} screenshots')


def rooms(openmsx, cdir, checks, facts, png):
    names = msx_model.rooms()
    for v in VERSIONS:
        for mname in MACHINES:
            hz = MACHINES[mname][1]
            tag = f'{v} {mname} ({hz} Hz)'
            cb = cbios_roms(cdir, mname)
            kept = json.loads((BUILD / f'state_{v}_{mname}.json')
                              .read_text())
            probs, emu_probs, shot_probs = [], [], []
            for n, name in sorted(names.items()):
                rname = f'rooms/{v}_{n:02}'
                rom, sym = rom_files(rname)
                state = kept
                emu = None
                if openmsx and mname == 'eu':
                    rd = RUNS / f'{v}_room_{n:02}'
                    emu = emu_run(openmsx, rname, mname, ROOM_FRAMES, rd,
                                  shots=ROOM_SHOTS)
                    state = state_of(rd, sym, mname)
                m, frames = bench_run(rom, sym, state, cb, None,
                                      ROOM_FRAMES)
                bad = frame_checks(frames, name, v,
                                   msx_model.zone_of(name), n,
                                   ROOM_FRAMES)
                rules = rule_checks(m)
                problems = [f'{k}: {e}' for k, e in bad.items() if e] + \
                    [f'{k}: {e}' for k, e in rules.items() if e]
                if problems:
                    probs.append(f'room {n}: {problems[0]}')
                facts.setdefault('rooms', {})[f'{v}_{mname}_{n:02}'] = \
                    h(frames[-1].get('vram', b''))
                if emu is None:
                    continue
                e = emu_compare(frames, emu['frames'])
                if e or emu['too_fast'] or emu['psg_directions']:
                    emu_probs.append(f'room {n}: {e} {emu["too_fast"][:1]}')
                for kk in (ROOM_SHOTS[0], ROOM_SHOTS[0] + 2):
                    p = rd / f'shot_{kk}.png'
                    s = shot_ok(p, name, 1, v, hz) if p.exists() else \
                        f'shot_{kk}.png missing'
                    if s:
                        shot_probs.append(f'room {n}: {s}')
                    elif kk == ROOM_SHOTS[0]:
                        shutil.copy(p, png / f'room_{n:02}_{name}_{v}.png')
                        facts.setdefault('openmsx', {})[
                            f'room_{v}_{n:02}'] = shot_hash(p)
            checks.add(f'{tag}: 16 rooms, {ROOM_FRAMES} frames each: '
                       'screen = model, variables, rules', not probs,
                       probs[0] if probs else '')
            if openmsx and mname == 'eu':
                checks.add(f'{tag}: 16 rooms, bench = openMSX every '
                           'frame, nothing dropped', not emu_probs,
                           emu_probs[0] if emu_probs else '')
                checks.add(f'{tag}: 16 rooms, screenshots = model',
                           not shot_probs,
                           shot_probs[0] if shot_probs else '')


def sheets(png):
    """Sheets for the author, from the screenshots of openMSX."""
    names = msx_model.rooms()
    made = []
    for hz in (50, 60):
        a = png / f'moss_gate_A_{hz}hz_phase1.png'
        b = png / f'moss_gate_B_{hz}hz_phase1.png'
        if a.exists() and b.exists():
            img = sheet([vram2png.read_png_rgb(a),
                         vram2png.read_png_rgb(b)], 2)
            out = png / f'sheet_moss_gate_A_B_{hz}hz_x2.png'
            out.write_bytes(png_rgb(img, 2))
            made.append(out.name)
    for v in VERSIONS:
        shots = [png / f'room_{n:02}_{name}_{v}.png'
                 for n, name in sorted(names.items())]
        if all(p.exists() for p in shots):
            img = sheet([vram2png.read_png_rgb(p) for p in shots], 4)
            out = png / f'sheet_rooms_{v}.png'
            out.write_bytes(png_rgb(img, 1))
            made.append(out.name)
    for n, name in sorted(names.items()):
        a = png / f'room_{n:02}_{name}_A.png'
        b = png / f'room_{n:02}_{name}_B.png'
        if a.exists() and b.exists():
            img = sheet([vram2png.read_png_rgb(a),
                         vram2png.read_png_rgb(b)], 2)
            (png / f'sheet_room_{n:02}_{name}_A_B_x2.png').write_bytes(
                png_rgb(img, 2))
    # the torch at row 4, column 8 and the moss left of it, x 4
    tiles = []
    for v in VERSIONS:
        for ph in range(4):
            p = png / f'moss_gate_{v}_50hz_phase{ph}.png'
            if not p.exists():
                return made
            tiles.append(crop(vram2png.read_png_rgb(p), 32, 24 + 16,
                              96, 40))
    out = png / 'sheet_torch_phases_A_B_x4.png'
    out.write_bytes(png_rgb(sheet(tiles, 4, gap=2), 4))
    made.append(out.name)
    return made


# -- mutations ------------------------------------------------------------

MUTATIONS = [
    # name, version, edits (file, old, new), the check that must stop
    # it (None: an equivalent mutation, that no check may stop)
    ('torches_every_16', 'A',
     [('torches.asm', '        and 7\n', '        and 15\n')],
     'screen'),
    ('torches_every_4', 'A',
     [('torches.asm', '        and 7\n', '        and 3\n')],
     None),
    ('third_without_inc', 'A',
     [('room.asm', '        ld a,c\n        inc a\n        rrca\n',
       '        ld a,c\n        rrca\n')],
     'screen'),
    ('name_not_centred', 'A',
     [('hud.asm', '        inc a\n        srl a', '        srl a')],
     'screen'),
    ('status_not_read', 'A',
     [('interrupt.asm', '        in a,(VDP_STAT)         ; clears',
       '        xor a                   ; clears')],
     'reached'),
    ('colours_wrong_third', 'A',
     [('zone.asm', '        add a,COLOURS / 256     ; the colour',
       '        add a,COLOURS / 256 + 8 ; the colour')],
     'screen'),
    ('gradient_7_rows', 'B',
     [('vdp.asm', '        ld bc,8*256+VDP_DATA\npc_gradient_row:',
       '        ld bc,7*256+VDP_DATA\npc_gradient_row:')],
     'screen'),
    ('im2_table_256', 'A',
     [('start.asm', '        ld bc,256\n', '        ld bc,255\n')],
     'reached'),
    ('names_in_rom', 'A',
     [('vars.asm', 'room_names      equ #C100',
       'room_names      equ #8100')],
     'rom'),
    ('psg_port_a_out', 'A',
     [('start.asm', '        ld a,%10111111          ; bits 7-6',
       '        ld a,%11111111          ; bits 7-6')],
     'r7'),
    ('fast_vram_screen_on', 'A',
     [('vdp.asm', '        db R1_OFF               ; R1: screen off',
       '        db R1_ON                ; R1: screen off'),
      ('zone.asm', 'lt_pattern_row:\n        outi                    '
       '; 18 T\n        jp nz,lt_pattern_row    ; 11 T\n',
       'lt_pattern_row:\n        otir\n')],
     '29T'),
]


def mutations(sjasm, openmsx, cdir, checks, facts):
    state = json.loads((BUILD / 'state_A_eu.json').read_text())
    cb = cbios_roms(cdir, 'eu')
    name = msx_model.rooms()[GAME_ROOM]
    zone = msx_model.zone_of(name)
    out = {}
    for mname, v, edits, must in MUTATIONS:
        tmp = Path(tempfile.mkdtemp(prefix='mut_'))
        try:
            src = tmp / 'src'
            shutil.copytree(SRC, src)
            ok_edit = True
            for fname, old, new in edits:
                p = src / fname
                text = p.read_text(encoding='ascii')
                if text.count(old) != 1:
                    ok_edit = False
                p.write_text(text.replace(old, new), encoding='ascii')
            gen = (ROOT / 'game' / 'assets' / 'generated' / v).as_posix()
            code, msg = run([sjasm, '--nologo', '--msg=war',
                             f'-DSTART_ROOM={GAME_ROOM}', f'-i{gen}',
                             f'--raw={(tmp / "m.rom").as_posix()}',
                             f'--sym={(tmp / "m.sym").as_posix()}',
                             (src / 'cryptmorrow.asm').as_posix()], tmp)
            if code or not ok_edit:
                checks.add(f'mutation {mname}: applied and assembled',
                           False, msg or 'the text to change is not there '
                           'once')
                continue
            rom = (tmp / 'm.rom').read_bytes()
            sym = msxsim.read_symbols(tmp / 'm.sym')
            st = state if v == 'A' else json.loads(
                (BUILD / f'state_{v}_eu.json').read_text())
            stopped = set()
            for seed in SEEDS:
                m, frames = bench_run(rom, sym, st, cb, seed, 40)
                bad = frame_checks(frames, name, v, zone, GAME_ROOM, 40)
                bad.update(rule_checks(m))
                stopped |= {k for k, e in bad.items() if e}
            emu = ''
            if must is None:
                out[mname] = sorted(stopped)
                checks.add(f'mutation {mname} ({v}): equivalent, no '
                           'check stops it', not stopped,
                           'checks failed: ' + ', '.join(sorted(stopped))
                           if stopped else 'the same screen every '
                           'frame: the phase written again, unchanged')
                continue
            if openmsx and must in ('29T', 'r7'):
                rd = RUNS / f'mut_{mname}'
                r = openmsx_run.run(openmsx, tmp / 'm.rom',
                                    'C-BIOS_MSX1_EU', sym, 40, rd,
                                    max_seconds=7)
                seen = r['too_fast'] if must == '29T' \
                    else r['psg_directions']
                emu = f'; openMSX: {len(seen)} ' + \
                    ('dropped VRAM accesses' if must == '29T'
                     else 'writes of R7 with port A as output')
                if not seen:
                    stopped.discard(must)
            out[mname] = sorted(stopped)
            checks.add(f'mutation {mname} ({v}): stopped by "{must}"',
                       must in stopped,
                       'checks failed: ' + ', '.join(sorted(stopped))
                       + emu)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    facts['mutations'] = out


def palettes(openmsx, checks, facts):
    """The Phase 0 probe on both machines: every one of the 15
    colours of its screenshots = the palette of tools/vram2png.py."""
    sys.path.insert(0, str(HERE))
    import fase0_check as F0
    probe = ROOT / 'fase0' / 'build'
    data = (probe / 'probe.rom').read_bytes()
    sym = msxsim.read_symbols(probe / 'probe.sym')
    joy = openmsx_run.find_in(data, 0x4000, sym['in_joy'],
                              (0xDB, 0xA2)) + 2
    for mname, (machine, hz) in MACHINES.items():
        rd = RUNS / f'palette_{mname}'
        r = openmsx_run.run(openmsx, probe / 'probe.rom', machine, sym,
                            max(F0.SHOTS) + 3, rd, inputs=F0.SCRIPT,
                            shots=F0.SHOTS, joy_read=joy)
        seen, bad = {}, []
        for k in F0.SHOTS:
            for kk in (k, k + 2):
                shot = vram2png.read_png_rgb(rd / f'shot_{kk}.png')
                found = None
                for back in (1, 2, 3):
                    fr = r['frames'][kk - 1 - back]
                    rows = vram2png.frame(fr['vram'], fr['vdp'])
                    trial, clash = dict(seen), False
                    for y in range(len(rows)):
                        for x in range(len(rows[0])):
                            c = rows[y][x]
                            if trial.setdefault(c, shot[y][x]) != \
                                    shot[y][x]:
                                clash = True
                                break
                        if clash:
                            break
                    if not clash:
                        found, seen = back, trial
                        break
                if found is None:
                    bad.append(kk)
        pal = vram2png.palette(hz)
        same = sorted(seen) == list(range(1, 16)) and \
            all(tuple(pal[c]) == tuple(rgb) for c, rgb in seen.items())
        facts.setdefault('openmsx', {})[f'palette_{mname}'] = {
            str(c): list(rgb) for c, rgb in sorted(seen.items())}
        checks.add(f'{mname} ({hz} Hz): the 15 colours of the probe\'s '
                   'screenshots = vram2png.palette(' + str(hz) + ')',
                   same and not bad,
                   f'colours seen {sorted(seen)}' +
                   (f'; screenshots not matched {bad}' if bad else ''))


def main():
    global RUNS
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--openmsx')
    ap.add_argument('--no-openmsx', action='store_true')
    ap.add_argument('--reference')
    ap.add_argument('--update-state', action='store_true')
    ap.add_argument('--keep-runs', action='store_true')
    ap.add_argument('--sjasmplus')
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    png = out / 'png'
    png.mkdir(exist_ok=True)
    openmsx = None if a.no_openmsx else find_tool('openmsx', a.openmsx)
    if not a.no_openmsx and not openmsx:
        print('openMSX not found (--no-openmsx for the bench only)')
        return 1
    sjasm = find_tool('sjasmplus', a.sjasmplus)
    cdir = cbios_dir(openmsx)
    if cdir is None:
        print('C-BIOS not found')
        return 1
    if a.keep_runs:
        RUNS = out / 'runs'
        RUNS.mkdir(exist_ok=True)
    else:
        RUNS = Path(tempfile.mkdtemp(prefix='verify_0_1_'))
    checks, facts = Checks(), {}
    try:
        manifest = json.loads((BUILD / 'manifest.json').read_text())
        checks.add('build: game/build/manifest.json without problems',
                   not manifest['problems'],
                   '; '.join(manifest['problems'][:2]))
        facts['build'] = {k: e['sha256'][:16]
                          for k, e in manifest['roms'].items()}
        facts['cartridge'] = manifest['measures']
        if openmsx:
            palettes(openmsx, checks, facts)
        game(openmsx, cdir, checks, facts, a, png)
        rooms(openmsx, cdir, checks, facts, png)
        made = sheets(png)
        if made:
            print('sheets:', ', '.join(made))
        if sjasm:
            mutations(sjasm, openmsx, cdir, checks, facts)
        else:
            checks.add('mutations: sjasmplus found', False)
    finally:
        if not a.keep_runs:
            shutil.rmtree(RUNS, ignore_errors=True)
    if a.reference:
        ref = json.loads(Path(a.reference).read_text())['facts']
        # the facts as the report writes them: JSON turns the
        # numbers used as keys (frames of the screenshots) into
        # strings (found on the PC, 8 November: the reference never
        # matched)
        mine = json.loads(json.dumps(facts))
        keys = [k for k in ref if k != 'openmsx']
        diff = [k for k in keys if ref.get(k) != mine.get(k)]
        checks.add('bench facts = the reference (' + a.reference + ')',
                   not diff, ', '.join(diff[:4]))
        if openmsx and 'openmsx' in ref:
            ro, mo = ref['openmsx'], mine.get('openmsx', {})
            diff = sorted(k for k in set(ro) | set(mo)
                          if ro.get(k) != mo.get(k))
            checks.add('openMSX facts (palettes, screenshots) = the '
                       'reference', not diff, ', '.join(diff[:4]))
    report = {'checks': checks.items, 'facts': facts,
              'failed': len(checks.failed), 'openmsx': openmsx,
              'cbios': str(cdir)}
    (out / 'verify_0_1.json').write_text(json.dumps(report, indent=1)
                                         + '\n', encoding='utf-8')
    print(f'\n{len(checks.items)} checks, {len(checks.failed)} failed')
    for c in checks.failed:
        print('FAILED:', c['check'], c['detail'])
    return 1 if checks.failed else 0


if __name__ == '__main__':
    sys.exit(main())

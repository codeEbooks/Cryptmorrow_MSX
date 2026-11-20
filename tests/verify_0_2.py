"""Milestone 0.2 checks: the explorer in the Moss Gate, on the two
C-BIOS MSX1 machines (EU: TMS9929A, 50 Hz; INT: TMS9918A, 60 Hz).

  state     the BIOS state at INIT of the game, read from openMSX;
            compared with the one kept in game/build
  walk      the game in the bench: a tour of the Moss Gate (to every
            wall, round the pillars, under the gate, down the steps
            to the edge of the room) and 1200 frames of changing
            input, given by the keyboard (arrows, SPACE), by joystick
            1 (stick, button A) or by both at once; three starts (the
            RAM and VRAM C-BIOS left, two random fillings). After
            every frame: the input byte, the explorer (x, y,
            direction, walk image and timer, moving, blocked) = the
            model (tests/hero_model.py, the ZX rules); the screen =
            the room of tests/msx_model.py with the explorer drawn
            where the model put it; the frame counter, the room, the
            HUD's variables, the stack; the map of solid cells in RAM
            = the one the model reads from the room's text
  rooms     a ROM for every room (START_ROOM 0-15), 300 frames of
            input each: the same checks, in openMSX too (50 Hz) and
            in the bench at 60 Hz
  openMSX   the game in openMSX with the same input, the three starts:
            RAM, VRAM, VDP and PSG registers (but 14) and T-states of
            every frame_ready = bench; interrupts at the same T-states.
            The joystick is given right after IN A,(#A2) (an aid of
            the test: openMSX 21.0 has no command for it)
  shots     screenshots of openMSX at frames where the explorer has
            stood still for four frames and the flame keeps its phase
            (the 1-3 frames a screenshot lags do not matter) = the
            model with the machine's palette, every pixel
  palettes  the Phase 0 probe on both machines: the 15 colours of
            tools/vram2png.py
  rules     no VRAM access closer than 29 T-states in the picture,
            nothing dropped by openMSX, no write to ROM, PSG register
            7 always 10xxxxxx, the VDP registers of Screen 2, the
            sprite list ending after the explorer; RAM written only
            in the areas of game/src/vars.asm and the stack
  measures  T-states of the start-up and its parts, of every frame
            and of its parts (input, explorer, sprite, torches), the
            lines where the frames write VRAM, the stack's depth
  mutations copies of the source with one mistake each: every one
            must be stopped by the check named (or by none, for an
            equivalent one, which is said)

Writes OUT/verify_0_2.json and, in OUT/png, the screenshots of
openMSX as they are and sheets made from them (the explorer in the
room, its eight images). --reference FILE compares the facts with
another run (the workspace's, on the PC); --no-openmsx runs only the
bench.

Usage: python tests/verify_0_2.py --out DIR [--openmsx EXE |
           --no-openmsx] [--reference FILE] [--update-state]
           [--keep-runs] [--sjasmplus EXE]
Needs the build: python tools/build_game.py
"""
import argparse
import hashlib
import json
import random
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
GENERATED = ROOT / 'game' / 'assets' / 'generated' / 'B'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'tools'))
import hero_model as H  # noqa: E402
import msx_model  # noqa: E402
import msxsim  # noqa: E402
import openmsx_run  # noqa: E402
import vram2png  # noqa: E402
from msxtools import CBIOS, cbios_dir, find_tool, run  # noqa: E402

MACHINES = {    # name: openMSX machine, Hz
    'eu': ('C-BIOS_MSX1_EU', 50),
    'int': ('C-BIOS_MSX1', 60),
}
VERSION = 'B'                   # the graphics of the game
GAME = 'cryptmorrow'
GAME_ROOM = 1
SEEDS = (None, 1, 2)
RANDOM_FRAMES = 1200
ROOM_FRAMES = 300
U, D, L, R, F = H.JOY_UP, H.JOY_DOWN, H.JOY_LEFT, H.JOY_RIGHT, \
    H.JOY_FIRE
KEY_NAMES = {U: 'UP', D: 'DOWN', L: 'LEFT', R: 'RIGHT', F: 'SPACE'}
JOY_NAMES = {U: 'UP', D: 'DOWN', L: 'LEFT', R: 'RIGHT', F: 'A'}
# A tour of the Moss Gate (the ZX's, and then down the steps to the
# edge of the room, which the ZX's did not reach): to every wall,
# round the pillars, under the gate; (input, frames).
TOUR = [(0, 10), (U, 40), (R, 120), (D, 90), (L, 230), (U, 80),
        (R | U, 30), (L | R, 20), (U | D, 20), (F, 10), (D, 40),
        (R, 60), (D, 90), (L, 40), (U, 30), (L, 30), (D, 60), (0, 10),
        (R, 75), (D, 50), (L, 8), (R, 16), (U, 20), (0, 10)]
CHOICES = [0, R, L, D, U, F, R | U, R | D, L | U, L | D, L | R, U | D,
           R | F, U | F]
SOURCES = ('keys', 'joy', 'both')
TOUR_FRAMES = sum(n for _, n in TOUR)
# stops for the screenshots: (input, frames)
SHOT_ROUTE = [(0, 14), (R, 44), (0, 12), (D, 37), (0, 12), (L, 69),
              (0, 12), (U, 30), (0, 12)]
# the RAM of game/src/vars.asm: [first, last + 1)
RAM_AREAS = ((0xC000, 0xC052), (0xC100, 0xC3A0), (0xC400, 0xC680),
             (0xF000, 0xF101), (0xF1F1, 0xF1F4))
STACK, STACK_ROOM = 0xF380, 64
VDP_REGS = [0x02, 0xE2, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x01]
WATCH = ('init', 'vdp_init', 'psg_init', 'load_glyphs', 'load_shapes',
         'enter_room', 'load_zone', 'build_names', 'build_solid',
         'put_names', 'hud_draw', 'hero_init', 'irq_init', 'main_loop',
         'isr', 'read_input', 'update_hero', 'draw_hero',
         'animate_torches', 'frame_ready')
HERO_VARS = ('hero_x', 'hero_y', 'hero_dir', 'hero_frame',
             'hero_timer', 'hero_moving', 'hero_block')
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


def rom_files(name, build=BUILD):
    return (build / f'{name}.rom').read_bytes(), \
        msxsim.read_symbols(build / f'{name}.sym')


def cbios_roms(cdir, mname):
    key = 'eu' if mname == 'eu' else 'int'
    return ((cdir / CBIOS[key]).read_bytes(),
            (cdir / CBIOS['logo']).read_bytes())


# -- the input ------------------------------------------------------------

def split(bits, source):
    """The input bits as keys of row 8 and joystick 1."""
    keys = [KEY_NAMES[b] for b in (U, D, L, R, F) if bits & b]
    joy = [JOY_NAMES[b] for b in (U, D, L, R, F) if bits & b]
    if source == 'keys':
        return tuple(keys), ()
    if source == 'joy':
        return (), tuple(joy)
    # both: left, right and fire from the keys, up and down from the
    # stick
    return (tuple(KEY_NAMES[b] for b in (L, R, F) if bits & b),
            tuple(JOY_NAMES[b] for b in (U, D) if bits & b))


def script_of(route, sources):
    """[(bits, keys, joy)] a frame, from [(bits, frames)]."""
    out = []
    for i, (bits, n) in enumerate(route):
        keys, joy = split(bits, sources[i % len(sources)])
        out += [(bits, keys, joy)] * n
    return out


def random_route(seed, frames):
    rnd = random.Random(seed)
    route, total, srcs = [], 0, []
    while total < frames:
        n = min(rnd.randint(4, 60), frames - total)
        route.append((rnd.choice(CHOICES), n))
        srcs.append(rnd.choice(SOURCES))
        total += n
    out = []
    for (bits, n), s in zip(route, srcs):
        out += [(bits,) + split(bits, s)] * n
    return out


def game_script():
    return script_of(TOUR, SOURCES) + random_route(7, RANDOM_FRAMES)


def room_script(n):
    # two frames without input first: openmsx_run gives the input of
    # a frame at the frame_ready before it, and frame 1 has none
    return [(0, (), ())] * 2 + random_route(100 + n, ROOM_FRAMES - 2)


def inputs_of(script):
    """openmsx_run's input: {frame: (keys, joy)} where it changes."""
    assert script[0][0] == 0, 'no input can be given for frame 1'
    out, prev = {}, None
    for k, (bits, keys, joy) in enumerate(script, 1):
        if (keys, joy) != prev:
            out[k] = (keys, joy)
            prev = (keys, joy)
    return out


def shot_frames(script):
    """Frames k with no input from k - 4 to k + 2 and k mod 8 = 4 or
    5: the explorer stands, the flame keeps its phase."""
    out = []
    for k in range(5, len(script) - 2):
        if k % 8 in (4, 5) and all(script[j - 1][0] == 0
                                   for j in range(k - 4, k + 3)):
            if not out or k - out[-1] > 8:
                out.append(k)
    return out


# -- the model, cached ------------------------------------------------

_MODEL = {}


def model_room(name, phase):
    key = (name, phase)
    if key not in _MODEL:
        _MODEL[key] = msx_model.screen(name, phase, VERSION)
    return _MODEL[key]


def model_screen(name, phase, hero):
    return msx_model.with_hero(model_room(name, phase), hero.image,
                               hero.x, hero.y)


def model_frame(rows):
    """The model as openMSX shows it: 320 x 240, the border."""
    g = vram2png.GEOMETRY
    back = VDP_REGS[7] & 15
    out = [[back] * g['width'] for _ in range(g['height'])]
    for y, row in enumerate(rows):
        out[g['top'] + y][g['left']:g['left'] + 256] = row
    return out


_BACK = {}


def screen_of(vram, regs):
    """The screen the VDP shows: the room from the tables (cached),
    the sprites drawn over a copy."""
    key = hashlib.sha1(bytes(vram[:0x1B00]) + bytes(vram[0x2000:0x3800])
                       + bytes(regs)).digest()
    if key not in _BACK:
        plain = bytearray(vram)
        plain[0x1B00] = 208             # no sprites
        _BACK[key] = vram2png.indices(bytes(plain), regs)
    rows = [list(r) for r in _BACK[key]]
    vram2png.draw_sprites(vram, regs, rows)
    return rows


def first_diff(a, b):
    for y in range(len(a)):
        if a[y] != b[y]:
            x = next(i for i in range(len(a[y])) if a[y][i] != b[y][i])
            return y, x, a[y][x], b[y][x]
    return None


# -- the bench ----------------------------------------------------------

def bench_walk(rom, sym, state, cb, seed, script, name, start,
               watch=False, log_vram=False):
    """The program with this input, checked after every frame.
    Returns (machine, records for openMSX, problems, facts)."""
    m = msxsim.MSX(rom, state, cb, seed=seed)
    if watch:
        m.watch = {sym[w]: w for w in WATCH}
    if log_vram:
        m.vram_log = []
        plain = m.vdp.vram_access

        def logged(t, pc):
            m.vram_log.append(t)
            plain(t, pc)
        m.vdp.vram_access = logged
    solid = msx_model.solid_cells(name)
    zone = msx_model.zone_of(name)
    hero = H.HeroModel(solid)
    hv = [sym[v] - 0xC000 for v in HERO_VARS]
    inp = sym['input'] - 0xC000
    so = sym['solid_map'] - 0xC000
    bad = dict.fromkeys(('reached', 'input', 'hero', 'screen',
                         'variables', 'registers', 'solid'))
    recs, facts = [], []
    ram = None
    for k, (bits, keys, joy) in enumerate(script, 1):
        m.set_input(keys, joy)
        try:
            m.run_to(sym['frame_ready'], max_t=40 * m.vdp.frame_t)
        except RuntimeError as e:
            bad['reached'] = f'frame {k} of {len(script)}: {e}'
            break
        hero.update(bits)
        ram = bytes(m.mem[0xC000:0xF380])
        vram = bytes(m.vdp.vram)
        regs = list(m.vdp.regs)
        if bad['input'] is None and ram[inp] != bits:
            bad['input'] = f'frame {k}: #{ram[inp]:02X}, model ' \
                           f'#{bits:02X}'
        prog = tuple(ram[a] for a in hv)
        if bad['hero'] is None and prog != hero.state():
            bad['hero'] = f'frame {k}: {prog}, model {hero.state()}'
        if bad['screen'] is None:
            d = first_diff(screen_of(vram, regs),
                           model_screen(name, (k >> 3) & 3, hero))
            if d:
                bad['screen'] = (f'frame {k}: pixel ({d[1]}, {d[0]}) '
                                 f'colour {d[2]}, model {d[3]}')
        if bad['variables'] is None:
            count = ram[0] | ram[1] << 8
            vals = {'frames': (count, k & 0xFFFF), 'room': (ram[5], start),
                    'zone': (ram[6], zone), 'energy': (ram[0x1C], 8),
                    'keys': (ram[0x1D], 0), 'seals': (ram[0x1E], 0),
                    'score': (ram[0x1F:0x22], bytes(3)),
                    'SP': (m.regs[msxsim.SP_], STACK)}
            wrong = [f'{n} {a} not {b}' for n, (a, b) in vals.items()
                     if a != b]
            if wrong:
                bad['variables'] = f'frame {k}: ' + ', '.join(wrong)
        if bad['registers'] is None and (regs != VDP_REGS or
                                         vram[0x1B04] != 208):
            bad['registers'] = f'frame {k}: VDP {regs}, Y of sprite 1 ' \
                               f'{vram[0x1B04]}'
        if bad['solid'] is None and k in (1, len(script)) and \
                list(ram[so:so + 640]) != solid:
            bad['solid'] = f'frame {k}: the solid map in RAM'
        recs.append((h(ram), h(vram), tuple(regs),
                     tuple(m.psg.regs[:14] + m.psg.regs[15:]), m.a8,
                     m.tstates))
        facts.append([m.tstates, h(ram), h(vram)])
    return m, recs, bad, facts, ram


def rule_checks(m):
    r7 = [val for t, r, val in m.psg.log if r == 7]
    return {'29T': m.vdp.too_fast[:2] or None,
            'rom': m.rom_written() or None,
            'r7': None if r7 and all(x & 0xC0 == 0x80 for x in r7)
            else [hex(x) for x in r7[:3]]}


def ram_check(lasts):
    """Addresses of #C000-#F37F that differ from the random filling
    at the end, in the runs with a filling: all in RAM_AREAS or in
    the stack. Returns (outside, stack depth)."""
    written = set()
    for seed, ram in lasts.items():
        if seed is None or ram is None:
            continue
        fill = msxsim.random_fill(seed)['ram']
        written |= {0xC000 + i for i in range(len(fill))
                    if fill[i] != ram[i]}
    inside = set()
    for lo, hi in RAM_AREAS:
        inside |= set(range(lo, hi))
    stack = [a for a in written if STACK - STACK_ROOM <= a < STACK]
    outside = sorted(a for a in written if a not in inside and
                     not STACK - STACK_ROOM <= a < STACK)
    return outside, (STACK - min(stack) if stack else 0)


def measures(m, recs):
    marks = {}
    for name, t in m.marks:
        marks.setdefault(name, []).append(t)
    first = {k: v[0] for k, v in marks.items()}
    order = ['vdp_init', 'psg_init', 'load_glyphs', 'load_shapes',
             'enter_room', 'load_zone', 'build_names', 'build_solid',
             'put_names', 'hud_draw', 'hero_init', 'irq_init',
             'main_loop']
    parts = {a: first[b] - first[a] for a, b in zip(order, order[1:])
             if a in first and b in first}
    parts['start-up'] = first['main_loop'] - first['init']
    # the parts of a frame, from one call to the next (draw_hero
    # runs once at the start too: only the marks of the loop count)
    loop = first['main_loop']
    frame = {}
    chain = ['read_input', 'update_hero', 'draw_hero',
             'animate_torches', 'frame_ready']
    seen = {c: [t for t in marks.get(c, []) if t > loop] for c in chain}
    for a, b in zip(chain, chain[1:]):
        ts = [y - x for x, y in zip(seen[a], seen[b])]
        frame[a] = [min(ts), max(ts)] if ts else None
    ready = [r[5] for r in recs]
    irq = m.irq_log
    busy = [r - i for r, i in zip(ready, irq)]
    start = first['main_loop']
    fr_t = m.vdp.frame_t
    lines = sorted({((t - m.vdp.picture_start) % fr_t) // 228
                    for t in m.vram_log if t > start})
    return {'parts': parts, 'frame_parts': frame, 'frame_t': fr_t,
            'busy': [min(busy), max(busy)],
            'busy_max_percent': round(100 * max(busy) / fr_t, 2),
            'vram_lines': [lines[0], lines[-1]] if lines else None}


# -- openMSX --------------------------------------------------------------

def emu_compare(recs, emu):
    n = min(len(recs), len(emu))
    for k in range(n):
        b, e = recs[k], emu[k]
        diffs = []
        if b[0] != h(e['ram']):
            diffs.append('RAM')
        if b[1] != h(e['vram']):
            diffs.append('VRAM')
        if list(b[2]) != e['vdp']:
            diffs.append('VDP registers')
        if list(b[3]) != e['psg'][:14] + e['psg'][15:]:
            diffs.append('PSG registers')
        if b[4] != e['a8']:
            diffs.append('slots')
        if b[5] != e['t']:
            diffs.append(f"T {b[5]} != {e['t']}")
        if diffs:
            return f'frame {k + 1}: ' + ', '.join(diffs)
    if len(recs) != len(emu):
        return f'{len(recs)} frames against {len(emu)}'
    return None


def emu_run(openmsx, rom_path, sym, mname, frames, rd, seed=None,
            shots=(), script=None):
    machine, hz = MACHINES[mname]
    rom = Path(rom_path).read_bytes()
    joy_read = openmsx_run.find_in(rom, 0x4000, sym['in_joy'],
                                   (0xDB, 0xA2)) + 2
    return openmsx_run.run(openmsx, rom_path, machine, sym, frames, rd,
                           seed=seed, shots=shots,
                           inputs=inputs_of(script) if script else None,
                           joy_read=joy_read,
                           max_seconds=round(6 + frames / 45, 2))


def state_of(rd, sym, mname):
    hz = MACHINES[mname][1]
    return openmsx_run.cbios_state(rd, sym['init'], hz,
                                   msxsim.LINES[hz] * msxsim.LINE_T)


def shot_ok(path, rows, hz):
    """A screenshot = the model's rows with the machine's palette."""
    got = vram2png.read_png_rgb(path)
    want = model_frame(rows)
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
    Hh = n_rows * hh + (n_rows + 1) * gap
    out = [[colour] * W for _ in range(Hh)]
    for i, img in enumerate(images):
        r, c = divmod(i, cols)
        y0, x0 = gap + r * (hh + gap), gap + c * (w + gap)
        for y in range(hh):
            out[y0 + y][x0:x0 + w] = img[y]
    return out


def shapes_sheet(vram, png):
    """The 8 images as the VDP has them (#3800), white on black."""
    pal = vram2png.palette(50)
    images = []
    for n in range(8):
        img = []
        for row in range(16):
            bits = vram[0x3800 + n * 32 + row] << 8 | \
                vram[0x3800 + n * 32 + 16 + row]
            img.append([tuple(pal[15]) if bits & (0x8000 >> x)
                        else tuple(pal[1]) for x in range(16)])
        images.append(img)
    (png / 'sheet_explorer_images_x8.png').write_bytes(
        png_rgb(sheet(images, 8, gap=2), 8))


# -- the parts ------------------------------------------------------------

def game(openmsx, cdir, checks, facts, args, png):
    name = msx_model.rooms()[GAME_ROOM]
    rom, sym = rom_files(GAME)
    script = game_script()
    for mname, (machine, hz) in MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        f = facts.setdefault(f'game_{mname}', {})
        state_file = BUILD / f'state_{mname}.json'
        if openmsx:
            rd = RUNS / f'{mname}_state'
            emu_run(openmsx, BUILD / f'{GAME}.rom', sym, mname, 8, rd)
            state = state_of(rd, sym, mname)
            if state_file.exists() and not args.update_state:
                kept = json.loads(state_file.read_text())
                checks.add(f'{tag}: state at INIT = the one kept',
                           kept == state, 'game/build/' + state_file.name)
            else:
                state_file.write_text(json.dumps(state) + '\n')
        state = json.loads(state_file.read_text())
        cb = cbios_roms(cdir, mname)
        runs, lasts = {}, {}
        for seed in SEEDS:
            n = len(script) if seed is None else TOUR_FRAMES
            m, recs, bad, fr, last = bench_walk(
                rom, sym, state, cb, seed, script[:n], name, GAME_ROOM,
                watch=seed is None, log_vram=seed is None)
            runs[seed] = (m, recs)
            lasts[seed] = last
            f[f'seed_{seed}'] = fr
            for what, label in (
                    ('reached', 'frame_ready every frame'),
                    ('input', 'the input byte = keys + joystick'),
                    ('hero', 'the explorer = the model'),
                    ('screen', 'screen = model, every frame'),
                    ('variables', 'counter, room, zone, HUD, stack'),
                    ('registers', 'VDP registers, sprite list ends'),
                    ('solid', 'solid map in RAM = the room\'s text')):
                checks.add(f'{tag} seed {seed}: {label}',
                           bad[what] is None, bad[what] or f'{n} frames')
            rules = rule_checks(m)
            checks.add(f'{tag} seed {seed}: no VRAM access closer than '
                       f'{msxsim.VRAM_GAP} T in the picture, no write to '
                       'ROM, PSG R7 10xxxxxx', not any(rules.values()),
                       str(rules))
        outside, depth = ram_check(lasts)
        f['stack_depth'] = depth
        checks.add(f'{tag}: RAM written only in the areas of vars.asm '
                   'and the stack (seeds 1, 2)',
                   not outside and 0 < depth <= STACK_ROOM,
                   f'stack {depth} bytes' + (
                       f'; outside {[hex(a) for a in outside[:4]]}'
                       if outside else ''))
        m0, recs0 = runs[None]
        mea = measures(m0, recs0)
        f['measures'] = mea
        checks.add(f'{tag}: a frame within its time, VRAM written only '
                   'out of the picture (lines 192 and after)',
                   mea['busy_max_percent'] < 100 and mea['vram_lines']
                   and mea['vram_lines'][0] >= 192,
                   f"busy {mea['busy']} T of {mea['frame_t']}; lines "
                   f"{mea['vram_lines']}")
        if mname == 'eu':
            shapes_sheet(bytes(m0.vdp.vram), png)
        if not openmsx:
            continue
        for seed in SEEDS:
            n = len(runs[seed][1])
            rd = RUNS / f'{mname}_seed_{seed}'
            r = emu_run(openmsx, BUILD / f'{GAME}.rom', sym, mname, n,
                        rd, seed=seed, script=script[:n])
            bad = emu_compare(runs[seed][1], r['frames'])
            checks.add(f'{tag} seed {seed}: bench = openMSX, every frame',
                       bad is None, bad or f"{len(r['frames'])} frames")
            if seed is None:
                k = len(r['irq'])
                checks.add(f'{tag}: interrupts at the same T-states',
                           k == n and r['irq'] == m0.irq_log[:k],
                           f'{k} interrupts')
            checks.add(f'{tag} seed {seed}: openMSX dropped no VRAM '
                       'access, no PSG port A as output',
                       not r['too_fast'] and not r['psg_directions'],
                       f"{r['too_fast'][:2]} {r['psg_directions'][:2]}")
            del r
        shots(openmsx, mname, sym, checks, facts, png)


def shots(openmsx, mname, sym, checks, facts, png):
    """The explorer standing at four places: openMSX's screenshots
    = the model."""
    machine, hz = MACHINES[mname]
    name = msx_model.rooms()[GAME_ROOM]
    script = script_of(SHOT_ROUTE, SOURCES)
    ks = shot_frames(script)
    rd = RUNS / f'{mname}_shots'
    emu_run(openmsx, BUILD / f'{GAME}.rom', sym, mname, len(script), rd,
            shots=ks, script=script)
    hero = H.HeroModel(msx_model.solid_cells(name))
    want = {}
    for k, (bits, keys, joy) in enumerate(script, 1):
        hero.update(bits)
        if k in ks:
            want[k] = model_screen(name, (k >> 3) & 3, hero)
    bad, hashes = [], {}
    for k in ks:
        for kk in (k, k + 2):
            p = rd / f'shot_{kk}.png'
            if not p.exists():
                bad.append(f'shot_{kk}.png missing')
                continue
            e = shot_ok(p, want[k], hz)
            if e:
                bad.append(e)
            hashes[str(kk)] = shot_hash(p)
        if (rd / f'shot_{k}.png').exists():
            shutil.copy(rd / f'shot_{k}.png',
                        png / f'explorer_{hz}hz_frame{k}.png')
    facts.setdefault('openmsx', {})[f'shots_{mname}'] = hashes
    checks.add(f'{mname} ({hz} Hz): screenshots of the explorer at '
               f'frames {ks} = the model, every pixel', not bad and ks,
               bad[0] if bad else f'{len(hashes)} screenshots')
    imgs = [vram2png.read_png_rgb(png / f'explorer_{hz}hz_frame{k}.png')
            for k in ks if (png / f'explorer_{hz}hz_frame{k}.png').exists()]
    if imgs:
        (png / f'sheet_explorer_{hz}hz.png').write_bytes(
            png_rgb(sheet(imgs, 3), 1))


def rooms(openmsx, cdir, checks, facts):
    names = msx_model.rooms()
    for mname, (machine, hz) in MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        cb = cbios_roms(cdir, mname)
        kept = json.loads((BUILD / f'state_{mname}.json').read_text())
        probs, emu_probs = [], []
        for n, name in sorted(names.items()):
            rname = f'rooms/{n:02}'
            rom, sym = rom_files(rname)
            script = room_script(n)
            state, emu = kept, None
            if openmsx and mname == 'eu':
                rd = RUNS / f'room_{n:02}'
                emu = emu_run(openmsx, BUILD / f'{rname}.rom', sym, mname,
                              len(script), rd, script=script)
                state = state_of(rd, sym, mname)
            m, recs, bad, fr, last = bench_walk(rom, sym, state, cb, None,
                                                script, name, n)
            bad.update(rule_checks(m))
            problems = [f'{k}: {e}' for k, e in bad.items() if e]
            if problems:
                probs.append(f'room {n}: {problems[0]}')
            facts.setdefault('rooms', {})[f'{mname}_{n:02}'] = \
                fr[-1] if fr else None
            if emu is not None:
                e = emu_compare(recs, emu['frames'])
                if e or emu['too_fast'] or emu['psg_directions']:
                    emu_probs.append(f'room {n}: {e} '
                                     f'{emu["too_fast"][:1]}')
        checks.add(f'{tag}: 16 rooms, {ROOM_FRAMES} frames of input each:'
                   ' input, explorer, screen, solid map, rules',
                   not probs, probs[0] if probs else '')
        if openmsx and mname == 'eu':
            checks.add(f'{tag}: 16 rooms, bench = openMSX every frame, '
                       'nothing dropped', not emu_probs,
                       emu_probs[0] if emu_probs else '')


def palettes(openmsx, checks, facts):
    """The Phase 0 probe on both machines: every one of the 15
    colours of its screenshots = the palette of tools/vram2png.py."""
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
                            if trial.setdefault(rows[y][x], shot[y][x]) \
                                    != shot[y][x]:
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
                   f'screenshots = vram2png.palette({hz})',
                   same and not bad, f'colours seen {sorted(seen)}' +
                   (f'; screenshots not matched {bad}' if bad else ''))


# -- mutations ------------------------------------------------------------

MUTATIONS = [
    # name, edits (file, old, new), the check that must stop it
    # (None: an equivalent mutation, that no check may stop)
    ('right_wins', [('hero.asm', '        bit 2,c                 ; left',
                     '        bit 3,c                 ; left')], 'hero'),
    ('down_wins', [('hero.asm', '        bit 0,c                 ; up',
                    '        bit 1,c                 ; up')], 'hero'),
    ('hitbox_right_short',
     [('hero.asm', '        add a,BOX_RIGHT+1\n',
       '        add a,BOX_RIGHT\n')], 'hero'),
    ('walk_every_4', [('hero.asm', 'WALK_RATE       equ 8 ',
                       'WALK_RATE       equ 4 ')], 'hero'),
    ('stand_keeps_step',
     [('hero.asm', 'ah_stand:\n        xor a\n        ld (hero_frame),a\n',
       'ah_stand:\n        xor a\n')], 'hero'),
    ('room_lines_168', [('hero.asm', 'ROOM_LINES      equ 160',
                         'ROOM_LINES      equ 168')], 'hero'),
    ('sprite_a_line_low',
     [('hero.asm', '        ld a,(hero_y)\n        dec a\n',
       '        ld a,(hero_y)\n')], 'screen'),
    # sprites 2-31 are then all at Y = 0 but colour 0 (the VRAM is
    # cleared): nothing to see, so the list's end is checked itself
    ('list_not_ended',
     [('hero.asm', '        ld a,208                ; the list ends',
       '        ld a,207                ; the list ends')], 'registers'),
    ('keys_row_7', [('input.asm', 'KEY_ROW         equ 8 ',
                     'KEY_ROW         equ 7 ')], 'input'),
    ('psg_port_a_out',
     [('start.asm', '        ld a,%10111111          ; bits 7-6',
       '        ld a,%11111111          ; bits 7-6')], 'r7'),
    ('solid_bits_swapped',
     [('room.asm', '        call solid_bit          ; top left\n'
       '        inc hl\n        call solid_bit          ; top right\n',
       '        inc hl\n        call solid_bit          ; top left\n'
       '        dec hl\n        call solid_bit          ; top right\n'
       '        inc hl\n')], None),
]


def mutations(sjasm, openmsx, cdir, checks, facts):
    state = json.loads((BUILD / 'state_eu.json').read_text())
    cb = cbios_roms(cdir, 'eu')
    name = msx_model.rooms()[GAME_ROOM]
    script = game_script()[:TOUR_FRAMES]
    out = {}
    for mname, edits, must in MUTATIONS:
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
            code, msg = run([sjasm, '--nologo', '--msg=war',
                             f'-DSTART_ROOM={GAME_ROOM}',
                             f'-i{GENERATED.as_posix()}',
                             f'--raw={(tmp / "m.rom").as_posix()}',
                             f'--sym={(tmp / "m.sym").as_posix()}',
                             (src / 'cryptmorrow.asm').as_posix()], tmp)
            if code or not ok_edit:
                checks.add(f'mutation {mname}: applied and assembled',
                           False, msg or 'the text to change is not there '
                           'once')
                continue
            rom, sym = rom_files('m', tmp)
            m, recs, bad, fr, last = bench_walk(rom, sym, state, cb, None,
                                                script, name, GAME_ROOM)
            bad.update(rule_checks(m))
            stopped = {k for k, e in bad.items() if e}
            out[mname] = sorted(stopped)
            if must is None:
                checks.add(f'mutation {mname}: equivalent, no check stops '
                           'it', not stopped, 'checks failed: ' +
                           ', '.join(sorted(stopped)) if stopped else
                           'the same frames: every solid byte of the '
                           'data is 0 or 15')
                continue
            emu = ''
            if openmsx and must == 'r7':
                rd = RUNS / f'mut_{mname}'
                r = emu_run(openmsx, tmp / 'm.rom', sym, 'eu', 60, rd,
                            script=script[:60])
                emu = f"; openMSX: {len(r['psg_directions'])} writes of " \
                      'R7 with port A as output'
                if not r['psg_directions']:
                    stopped.discard(must)
            checks.add(f'mutation {mname}: stopped by "{must}"',
                       must in stopped, 'checks failed: ' +
                       ', '.join(sorted(stopped)) + emu)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    facts['mutations'] = out


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
        RUNS = Path(tempfile.mkdtemp(prefix='verify_0_2_'))
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
        rooms(openmsx, cdir, checks, facts)
        if sjasm:
            mutations(sjasm, openmsx, cdir, checks, facts)
        else:
            checks.add('mutations: sjasmplus found', False)
    finally:
        if not a.keep_runs:
            shutil.rmtree(RUNS, ignore_errors=True)
    if a.reference:
        ref = json.loads(Path(a.reference).read_text())['facts']
        # the facts as the report writes them (JSON: tuples become
        # lists, numbers used as keys become strings)
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
    (out / 'verify_0_2.json').write_text(json.dumps(report, indent=1)
                                         + '\n', encoding='utf-8')
    print(f'\n{len(checks.items)} checks, {len(checks.failed)} failed')
    for c in checks.failed:
        print('FAILED:', c['check'], c['detail'])
    return 1 if checks.failed else 0


if __name__ == '__main__':
    sys.exit(main())

"""Milestone 0.3 checks: the dungeon. The explorer walks through the
openings of the 16 rooms (the locked doors shut; in the visit,
cryptmorrow_visit.rom, all open), on the two C-BIOS MSX1 machines
(EU: TMS9929A, 50 Hz; INT: TMS9918A, 60 Hz).

  state     the BIOS state at INIT of the game, read from openMSX, the
            first interrupt fitted to openMSX's T-states over 300
            frames (calibrate); compared with the one kept in
            game/build
  game      the game in the bench: a tour of the seven rooms of the
            atrium that need no key (every opening, both ways: 12
            passages, the routes found by tests/route.py), pushing
            against the three locked doors, then 1200 frames of
            changing input; keyboard (arrows, SPACE), joystick 1
            (stick, button A) or both; three starts (the RAM and VRAM
            C-BIOS left, two random fillings). After every pass of
            the main loop (frame_ready): the input byte; the room and
            the explorer = the model (tests/world_model.py, with
            tests/hero_model.py: the ZX rules); the screen = the room
            of tests/msx_model.py with the explorer where the model
            put it and the flames of the frame counter's phase; the
            frame counter = the interrupts taken, the room, the zone,
            the HUD's variables, the stack; the map of solid cells in
            RAM = the room's text (at the start and after every
            change)
  hidden    every change of room, from the program's VRAM writes and
            the times the picture shows each row: no picture shows
            the room half built (every picture shows the old room,
            the room black or the new room, in this order); while it
            is black no sprite is shown; the cells of the zone (slots
            0-#DF) are written only while the room is black
  visit     the visit (every locked door open): the 15 openings of
            the dungeon both ways, 30 passages through the four
            zones, with the same checks, in the bench and openMSX at
            50 and 60 Hz
  rooms     a ROM for every room (START_ROOM 0-15), 300 frames of
            input each: the same checks (the explorer may leave the
            room), in openMSX too (50 Hz) and in the bench at 60 Hz
  openMSX   the game and the visit in openMSX with the same input:
            RAM, VRAM, VDP and PSG registers (but 14) and T-states of
            every frame_ready = bench; interrupts at the same
            T-states. The joystick is given right after IN A,(#A2)
            (an aid of the test: openMSX 21.0 has no command for it)
  shots     screenshots of openMSX in seven rooms of the four zones,
            reached through a change of room, the explorer standing
            and the flame keeping its phase = the model with the
            machine's palette, every pixel
  palettes  the Phase 0 probe on both machines: the 15 colours of
            tools/vram2png.py
  rules     no VRAM access closer than 29 T-states in the picture,
            nothing dropped by openMSX, every byte to VDP_CTRL with
            interrupts off (an address or a register is two bytes),
            no write to ROM, PSG register 7 always 10xxxxxx, the VDP
            registers of Screen 2, the sprite list ending after the
            explorer's two sprites; RAM written only in the areas of
            game/src/vars.asm and the stack
  measures  T-states of the start-up and its parts, of every frame
            and of its parts, of every change of room and of its
            parts, the black pictures of a change, the lines where the
            frames without a change write VRAM, the stack's depth
  mutations copies of the source with one mistake each: every one
            must be stopped by the check named

Writes OUT/verify_0_3.json and, in OUT/png, the screenshots of
openMSX and sheets made from them. --reference FILE compares the
facts with another run (the workspace's, on the PC); --no-openmsx
runs only the bench.

Usage: python tests/verify_0_3.py --out DIR [--openmsx EXE |
           --no-openmsx] [--reference FILE] [--update-state]
           [--keep-runs] [--sjasmplus EXE]
Needs the build: python tools/build_game.py
"""
import argparse
import bisect
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
import route as RT  # noqa: E402
import vram2png  # noqa: E402
import world_model as W  # noqa: E402
from msxtools import CBIOS, cbios_dir, find_tool, run  # noqa: E402

MACHINES = {    # name: openMSX machine, Hz
    'eu': ('C-BIOS_MSX1_EU', 50),
    'int': ('C-BIOS_MSX1', 60),
}
VERSION = 'B'                   # the graphics of the game
GAME, VISIT = 'cryptmorrow', 'cryptmorrow_visit'
GAME_ROOM = 1
SEEDS = (None, 1, 2)
RANDOM_FRAMES = 1200
ROOM_FRAMES = 300
U, D, L, R, F = H.JOY_UP, H.JOY_DOWN, H.JOY_LEFT, H.JOY_RIGHT, \
    H.JOY_FIRE
KEY_NAMES = {U: 'UP', D: 'DOWN', L: 'LEFT', R: 'RIGHT', F: 'SPACE'}
JOY_NAMES = {U: 'UP', D: 'DOWN', L: 'LEFT', R: 'RIGHT', F: 'A'}
PUSH = {'north': U, 'south': D, 'west': L, 'east': R}
# The game: the atrium's seven rooms, every opening both ways, and
# a push against each locked door (A south of the Root Cellar, B
# east of the Long Gallery, C east of the Sunken Hall).
GAME_TOUR = [('stand', 2), ('exit', 'south'), ('exit', 'west'),
             ('push', 'south', 30), ('exit', 'north'), ('exit', 'south'),
             ('exit', 'east'), ('exit', 'east'), ('push', 'east', 30),
             ('exit', 'north'), ('exit', 'south'), ('exit', 'west'),
             ('exit', 'south'), ('push', 'east', 30), ('exit', 'north'),
             ('exit', 'north'), ('stand', 10)]
# The visit: the dungeon is a tree of 16 rooms and 15 openings; a
# walk round it goes through every opening once each way.
VISIT_SIDES = ['south', 'west', 'north', 'south', 'south', 'south',
               'east', 'west', 'north', 'north', 'east', 'east',
               'north', 'south', 'east', 'north', 'south', 'south',
               'north', 'west', 'west', 'south', 'east', 'south',
               'east', 'west', 'north', 'west', 'north', 'north']
VISIT_TOUR = [('stand', 2)] + [('exit', s) for s in VISIT_SIDES] + \
    [('stand', 10)]
# The mutations' visit: into each zone and back (6 changes of zone).
SHORT_VISIT = [('stand', 2)] + [('exit', s) for s in (
    'south', 'west', 'south', 'north', 'east', 'east', 'east', 'west',
    'west', 'south', 'east', 'west')] + [('stand', 4)]
# The screenshots: (ROM, start room, doors open, exits); the
# explorer stands 24 frames after each change.
SHOT_PLANS = [(VISIT, 1, True, ['south', 'east', 'east', 'north']),
              ('rooms/08', 8, False, ['north']),
              ('rooms/10', 10, False, ['south']),
              ('rooms/12', 12, False, ['east'])]
CHOICES = [0, R, L, D, U, F, R | U, R | D, L | U, L | D, L | R, U | D,
           R | F, U | F]
SOURCES = ('keys', 'joy', 'both')
# the RAM of game/src/vars.asm: [first, last + 1)
RAM_AREAS = ((0xC000, 0xC058), (0xC100, 0xC3A0), (0xC400, 0xC680),
             (0xF000, 0xF101), (0xF1F1, 0xF1F4))
STACK, STACK_ROOM = 0xF380, 64
VDP_REGS = [0x02, 0xE2, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x01]
ROOM_BLANK = 0xE0
ROOM_NAMES = (0x1800 + 2 * 32, 0x1800 + 22 * 32)   # rows 2-21
WATCH = ('init', 'vdp_init', 'psg_init', 'load_glyphs', 'load_shapes',
         'enter_room', 'load_zone', 'build_room', 'hud_draw',
         'put_names', 'hero_init', 'irq_init', 'main_loop', 'isr',
         'read_input', 'update_hero', 'check_exits', 'change_room',
         'hide_room', 'room_built', 'draw_hero', 'animate_torches',
         'reveal_room', 'frame_ready')
HERO_VARS = ('hero_x', 'hero_y', 'hero_dir', 'hero_frame',
             'hero_timer', 'hero_moving', 'hero_block')
WHAT = ('reached', 'input', 'hero', 'screen', 'variables', 'registers',
        'solid', 'hidden')
LABELS = {'reached': 'frame_ready every pass',
          'input': 'the input byte = keys + joystick',
          'hero': 'room and explorer = the model',
          'screen': 'screen = model, every pass',
          'variables': 'frames = interrupts, room, zone, HUD, stack',
          'registers': 'VDP registers, sprite list ends',
          'solid': 'solid map in RAM = the room\'s text',
          'hidden': 'every change hidden'}
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


def runs_of(path):
    """[(bits, frames)] from a list of bits a frame."""
    out = []
    for b in path:
        if out and out[-1][0] == b:
            out[-1][1] += 1
        else:
            out.append([b, 1])
    return [tuple(r) for r in out]


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


def door_ahead(probe, side, name):
    """The cell one pixel ahead of the hitbox, toward `side`, is in a
    locked door's metatile (room `name`)."""
    x, y = probe.x, probe.y
    if side in ('north', 'south'):
        px = x + H.BOX_MID
        py = y + (H.BOX_TOP - 1 if side == 'north' else H.BOX_BOTTOM + 1)
    else:
        px = x + (H.BOX_LEFT - 1 if side == 'west' else H.BOX_RIGHT + 1)
        py = y + H.BOX_BOTTOM
    row, col = (py - H.ROOM_TOP_LINE) // 16, px // 16
    grid = msx_model.dungeon.load_room(name).grid
    return 0 <= row < 10 and 0 <= col < 16 and grid[row][col] == 'D'


def plan_push(world, side):
    """Inputs that walk the explorer into the locked door on `side`,
    until it stops there."""
    joy = PUSH[side]

    def goal(p, j):
        return j == joy and p.block and door_ahead(p, side, world.name)
    return RT.plan(world, goal, f'push the door {side}')


def plan_bits(world, actions):
    """Inputs (bits a frame) for the actions, moving `world` along:
    ('exit', side), ('push', side, frames), ('stand', frames)."""
    out = []
    for act in actions:
        if act[0] == 'exit':
            path = RT.plan_exit(world, act[1])
        elif act[0] == 'push':
            path = plan_push(world, act[1])
            path += [PUSH[act[1]]] * (act[2] - 1)
        else:
            path = [0] * act[1]
        for b in path:
            world.update(b)
        out += path
    return out


_TOURS = {}


def tour_script(actions, room, doors_open=False):
    key = (tuple(tuple(a) for a in actions), room, doors_open)
    if key not in _TOURS:
        world = W.World(room, doors_open=doors_open)
        _TOURS[key] = script_of(runs_of(plan_bits(world, actions)),
                                SOURCES)
    return list(_TOURS[key])


def game_script():
    return tour_script(GAME_TOUR, GAME_ROOM) + \
        random_route(7, RANDOM_FRAMES)


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
        if len(_BACK) > 400:
            _BACK.clear()
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


# -- a change of room, as the picture shows it ---------------------------

ORDER = ('old', 'black', 'new')


def hidden(before, writes, t0, t1, vdp, after):
    """A change of room from the VRAM writes [(T, address, value)]
    between two frame_ready (T t0 and t1), the VRAM before and after.
    Every picture that starts in between must show, in every row of
    the room from its first line to its last, the old room, the room
    black or the new room, the same in all rows, in this order; no
    sprite while black (sprite 0's Y = 208 at the start and the end of
    the picture); slots 0-#DF of the patterns and colours written only
    while all the room is black. Returns (problem or None, black
    pictures)."""
    lo, hi = ROOM_NAMES
    old, new = before[lo:hi], after[lo:hi]
    vram = bytearray(before)
    ft, line = vdp.frame_t, msxsim.LINE_T
    first = t0 + (vdp.picture_start - t0) % ft
    samples = []
    p = first
    while p < t1:
        samples.append((p, 'sat', p))
        samples.append((p + 192 * line - 1, 'sat', p))
        for r in range(2, 22):
            samples.append((p + 8 * r * line, r, p))
            samples.append((p + (8 * r + 8) * line - 1, r, p))
        p += ft
    samples.sort(key=lambda s: s[0])
    seen = {}               # picture: [set of states, sprite Ys]
    shown = sum(1 for b in vram[lo:hi] if b != ROOM_BLANK)
    problem = None
    i = 0
    for t, what, pic in samples + [(None, None, None)]:
        while i < len(writes) and (t is None or writes[i][0] <= t):
            wt, a, v = writes[i]
            i += 1
            if lo <= a < hi:
                shown += (vram[a] == ROOM_BLANK) - (v == ROOM_BLANK)
            elif (a < 0x1800 or 0x2000 <= a < 0x3800) and \
                    (a & 0x7FF) < 0xE0 * 8 and shown and \
                    problem is None:
                problem = f'slot {(a & 0x7FF) >> 3:02X} written at ' \
                          f'T {wt} with the room shown'
            vram[a] = v
        if t is None:
            break
        s = seen.setdefault(pic, [set(ORDER), []])
        if what == 'sat':
            s[1].append(vram[0x1B00])
            continue
        row = bytes(vram[0x1800 + 32 * what:0x1820 + 32 * what])
        k = (what - 2) * 32
        states = set()
        if row == old[k:k + 32]:
            states.add('old')
        if row == bytes([ROOM_BLANK]) * 32:
            states.add('black')
        if row == new[k:k + 32]:
            states.add('new')
        s[0] &= states
    level, black = 0, 0
    for pic in sorted(seen):
        states, ys = seen[pic]
        ok = [ORDER.index(x) for x in states if ORDER.index(x) >= level]
        if not ok:
            problem = problem or (f'picture at T {pic}: rows of '
                                  f'different states or out of order')
            break
        level = min(ok)
        if ORDER[level] == 'black':
            black += 1
            if any(y != 208 for y in ys):
                problem = problem or (f'picture at T {pic}: a sprite '
                                      'over the black room')
    return problem, black


# -- the bench ----------------------------------------------------------

def bench_walk(rom, sym, state, cb, seed, script, start, doors_open=False,
               watch=False):
    """The program with this input, checked after every pass of the
    main loop. Returns (machine, records for openMSX, problems, facts,
    last RAM, measures of the changes)."""
    m = msxsim.MSX(rom, state, cb, seed=seed)
    if watch:
        m.watch = {sym[w]: w for w in WATCH}
    writes, ctrl_on = [], []
    vdp = m.vdp
    plain = vdp.write

    def logged(port, value, t, pc):
        if port & 1 == 0:
            writes.append((t, vdp.pointer, value))
        elif m.regs[msxsim.IFF_] and not ctrl_on:
            ctrl_on.append(f'${pc:04X} at T {t}')
        plain(port, value, t, pc)
    vdp.write = logged
    world = W.World(start, doors_open=doors_open)
    names = msx_model.rooms()
    hv = [sym[v] - 0xC000 for v in HERO_VARS]
    inp = sym['input'] - 0xC000
    so = sym['solid_map'] - 0xC000
    bad = dict.fromkeys(WHAT)
    recs, digest, changes, quiet = [], hashlib.sha256(), [], []
    counts = []
    ram = None
    before, t_prev = bytes(vdp.vram), m.tstates
    for k, (bits, keys, joy) in enumerate(script, 1):
        m.set_input(keys, joy)
        n_irq = len(m.irq_log)
        try:
            m.run_to(sym['frame_ready'], max_t=40 * vdp.frame_t)
        except RuntimeError as e:
            bad['reached'] = f'pass {k} of {len(script)}: {e}'
            break
        changed = world.update(bits)
        ram = bytes(m.mem[0xC000:0xF380])
        vram = bytes(vdp.vram)
        regs = list(vdp.regs)
        name = world.name
        count = ram[0] | ram[1] << 8
        counts.append(count)
        if bad['input'] is None and ram[inp] != bits:
            bad['input'] = f'pass {k}: #{ram[inp]:02X}, model ' \
                           f'#{bits:02X}'
        prog = (ram[sym['room'] - 0xC000],) + tuple(ram[a] for a in hv)
        if bad['hero'] is None and prog != world.state():
            bad['hero'] = f'pass {k}: {prog}, model {world.state()}'
        if bad['screen'] is None:
            d = first_diff(screen_of(vram, regs),
                           model_screen(name, (count >> 3) & 3,
                                        world.hero))
            if d:
                bad['screen'] = (f'pass {k} (room {world.room}): pixel '
                                 f'({d[1]}, {d[0]}) colour {d[2]}, '
                                 f'model {d[3]}')
        if bad['variables'] is None:
            vals = {'frames': (count, len(m.irq_log) & 0xFFFF),
                    'room': (ram[5], world.room),
                    'zone': (ram[6], msx_model.zone_of(name)),
                    'energy': (ram[0x1C], 8), 'keys': (ram[0x1D], 0),
                    'seals': (ram[0x1E], 0),
                    'score': (ram[0x1F:0x22], bytes(3)),
                    'reveal_due': (ram[sym['reveal_due'] - 0xC000], 0),
                    'SP': (m.regs[msxsim.SP_], STACK)}
            wrong = [f'{n} {a} not {b}' for n, (a, b) in vals.items()
                     if a != b]
            if wrong:
                bad['variables'] = f'pass {k}: ' + ', '.join(wrong)
        if bad['registers'] is None and (regs != VDP_REGS or
                                         vram[0x1B08] != 208):
            bad['registers'] = f'pass {k}: VDP {regs}, Y of sprite 2 ' \
                               f'{vram[0x1B08]}'
        if bad['solid'] is None and (k == 1 or changed) and \
                list(ram[so:so + 640]) != world.solid(world.room):
            bad['solid'] = f'pass {k}: the solid map in RAM (room ' \
                           f'{world.room})'
        if changed:
            e, black = hidden(before, writes, t_prev, m.tstates, vdp,
                              vram)
            if e and bad['hidden'] is None:
                bad['hidden'] = f'pass {k} (to room {world.room}): {e}'
            changes.append({'pass': k, 'room': world.room,
                            'irq': len(m.irq_log) - n_irq,
                            'black': black, 't': m.tstates - t_prev})
        else:
            quiet.extend(t for t, a, v in writes)
            if len(m.irq_log) - n_irq != 1 and bad['hidden'] is None:
                bad['hidden'] = f'pass {k}: {len(m.irq_log) - n_irq} ' \
                                'interrupts without a change'
        writes.clear()
        before, t_prev = vram, m.tstates
        recs.append((h(ram), h(vram), tuple(regs),
                     tuple(m.psg.regs[:14] + m.psg.regs[15:]), m.a8,
                     m.tstates))
        digest.update(f'{m.tstates} {h(ram)} {h(vram)};'.encode())
    m.quiet_writes = quiet
    m.ctrl_on = ctrl_on
    m.counts = counts
    facts = {'passes': len(recs), 'end_t': m.tstates,
             'digest': digest.hexdigest()[:16],
             'changes': [[c['pass'], c['room'], c['irq'], c['black']]
                         for c in changes]}
    return m, recs, bad, facts, ram, changes


def rule_checks(m):
    r7 = [val for t, r, val in m.psg.log if r == 7]
    return {'29T': m.vdp.too_fast[:2] or None,
            'ctrl': m.ctrl_on[:2] or None,
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


def span(values):
    return [min(values), max(values)] if values else None


def measures(m, recs, changes):
    marks = {}
    for name, t in m.marks:
        marks.setdefault(name, []).append(t)
    first = {k: v[0] for k, v in marks.items()}
    order = ['vdp_init', 'psg_init', 'load_glyphs', 'load_shapes',
             'enter_room', 'load_zone', 'build_room', 'hud_draw',
             'put_names', 'hero_init', 'irq_init', 'main_loop']
    parts = {a: first[b] - first[a] for a, b in zip(order, order[1:])
             if a in first and b in first}
    parts['start-up'] = first['main_loop'] - first['init']
    ready = [r[5] for r in recs]
    change_at = {c['pass'] for c in changes}

    def after(name, t0, t1):
        ts = marks.get(name, [])
        i = bisect.bisect_right(ts, t0)
        return ts[i] if i < len(ts) and ts[i] < t1 else None
    # the parts of a pass without a change
    chain = ['read_input', 'update_hero', 'check_exits', 'draw_hero',
             'animate_torches', 'reveal_room', 'frame_ready']
    frame = {c: [] for c in chain[:-1]}
    busy = []
    room_parts = {k: [] for k in ('hide', 'zone', 'build', 'hud',
                                  'built', 'wait', 'reveal')}
    zone_change = []
    fr_t = m.vdp.frame_t
    irq = m.irq_log
    prev = first['main_loop']
    for k, t in enumerate(ready, 1):
        ts = [after(c, prev, t + 1) for c in chain]
        if k not in change_at:
            for a, b, c in zip(ts, ts[1:], chain):
                if a is not None and b is not None:
                    frame[c].append(b - a)
            i = bisect.bisect_right(irq, prev)
            if i < len(irq):
                busy.append(t - irq[i])
        else:
            c0 = after('change_room', prev, t)
            hz = after('hide_room', prev, t)
            en = after('enter_room', prev, t)
            lz = after('load_zone', prev, t)
            br = after('build_room', prev, t)
            hd = after('hud_draw', br or prev, t)
            rb = after('room_built', prev, t)
            rv = after('reveal_room', rb or prev, t)
            nxt = irq[bisect.bisect_right(irq, rb)] if rb else None
            room_parts['hide'].append(en - hz)
            room_parts['build'].append(hd - br)
            room_parts['hud'].append(rb - hd)
            room_parts['built'].append(rb - c0)
            room_parts['wait'].append(nxt - rb)
            room_parts['reveal'].append(t - rv)
            if lz is not None:
                room_parts['zone'].append(br - lz)
                zone_change.append(k)
        prev = t
    lines = sorted({((t - m.vdp.picture_start) % fr_t) // 228
                    for t in m.quiet_writes if t > first['main_loop']})
    same = [c for c in changes if c['pass'] not in zone_change]
    other = [c for c in changes if c['pass'] in zone_change]
    return {'parts': parts,
            'frame_parts': {c: span(v) for c, v in frame.items()},
            'frame_t': fr_t, 'busy': span(busy),
            'busy_max_percent': round(100 * max(busy) / fr_t, 2)
            if busy else None,
            'vram_lines': [lines[0], lines[-1]] if lines else None,
            'change_parts': {k: span(v) for k, v in room_parts.items()},
            'changes_same_zone': {
                'n': len(same), 'irq': span([c['irq'] for c in same]),
                'black': span([c['black'] for c in same])},
            'changes_new_zone': {
                'n': len(other), 'irq': span([c['irq'] for c in other]),
                'black': span([c['black'] for c in other])}}


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
            return f'pass {k + 1}: ' + ', '.join(diffs)
    if len(recs) != len(emu):
        return f'{len(recs)} passes against {len(emu)}'
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
                           max_seconds=round(10 + frames / 30, 2))


def emu_irq_same(m, emu):
    k = min(len(emu['irq']), len(m.irq_log))
    return k > 0 and emu['irq'][:k] == m.irq_log[:k], k


def state_of(rd, sym, mname):
    hz = MACHINES[mname][1]
    return openmsx_run.cbios_state(rd, sym['init'], hz,
                                   msxsim.LINES[hz] * msxsim.LINE_T)


CALIBRATION_FRAMES = 300


def calibrate(state, rom, sym, cb, script, start, emu):
    """The first rise of the VDP's interrupt line after INIT, which
    openMSX's probe sees at an instruction boundary, up to one HALT
    cycle (5 T-states) late: openmsx_run.cbios_state gives an upper
    bound. The value is the latest of that bound and the 4 T-states
    before it with which the bench takes every interrupt and reaches
    every frame_ready at openMSX's T-states (milestone 0.2.1).
    Returns (state, how many T-states earlier) or (state, None)."""
    n = min(len(script), len(emu['frames']))
    for d in range(5):
        st = dict(state, vbl_after_init=state['vbl_after_init'] - d)
        m, recs, bad, fr, last, ch = bench_walk(rom, sym, st, cb, None,
                                                script[:n], start)
        if emu_compare(recs, emu['frames'][:n]) is None and \
                emu_irq_same(m, emu)[0]:
            return dict(st, vbl_calibration=d), d
    return state, None


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
    Wd = cols * w + (cols + 1) * gap
    Hh = n_rows * hh + (n_rows + 1) * gap
    out = [[colour] * Wd for _ in range(Hh)]
    for i, img in enumerate(images):
        r, c = divmod(i, cols)
        y0, x0 = gap + r * (hh + gap), gap + c * (w + gap)
        for y in range(hh):
            out[y0 + y][x0:x0 + w] = img[y]
    return out


# -- the parts ------------------------------------------------------------

def walk_checks(checks, tag, bad, n):
    for what in WHAT:
        checks.add(f'{tag}: {LABELS[what]}', bad[what] is None,
                   bad[what] or f'{n} passes')


def game(openmsx, cdir, checks, facts, args):
    rom, sym = rom_files(GAME)
    script = game_script()
    tour_n = len(tour_script(GAME_TOUR, GAME_ROOM))
    for mname, (machine, hz) in MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        f = facts.setdefault(f'game_{mname}', {})
        state_file = BUILD / f'state_{mname}.json'
        if openmsx:
            rd = RUNS / f'{mname}_state'
            cal = script[:CALIBRATION_FRAMES]
            emu = emu_run(openmsx, BUILD / f'{GAME}.rom', sym, mname,
                          len(cal), rd, script=cal)
            state, d = calibrate(state_of(rd, sym, mname), rom, sym,
                                 cbios_roms(cdir, mname), cal, GAME_ROOM,
                                 emu)
            checks.add(f'{tag}: the first interrupt after INIT fitted '
                       f'to openMSX ({len(cal)} passes)', d is not None,
                       f'{d} T-states before the probe\'s bound')
            del emu
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
            n = len(script) if seed is None else tour_n
            m, recs, bad, fr, last, ch = bench_walk(
                rom, sym, state, cb, seed, script[:n], GAME_ROOM,
                watch=seed is None)
            runs[seed] = (m, recs, ch)
            lasts[seed] = last
            f[f'seed_{seed}'] = fr
            walk_checks(checks, f'{tag} game seed {seed}', bad, n)
            rules = rule_checks(m)
            checks.add(f'{tag} game seed {seed}: no VRAM access closer '
                       f'than {msxsim.VRAM_GAP} T in the picture, '
                       'VDP_CTRL with interrupts off, no write to ROM, '
                       'PSG R7 10xxxxxx', not any(rules.values()),
                       str(rules))
        outside, depth = ram_check(lasts)
        f['stack_depth'] = depth
        checks.add(f'{tag}: RAM written only in the areas of vars.asm '
                   'and the stack (seeds 1, 2)',
                   not outside and 0 < depth <= STACK_ROOM,
                   f'stack {depth} bytes' + (
                       f'; outside {[hex(a) for a in outside[:4]]}'
                       if outside else ''))
        m0, recs0, ch0 = runs[None]
        mea = measures(m0, recs0, ch0)
        f['measures'] = mea
        checks.add(f'{tag}: a pass without a change within its frame, '
                   'its VRAM written out of the picture (lines 192 and '
                   'after)',
                   mea['busy_max_percent'] < 100 and mea['vram_lines']
                   and mea['vram_lines'][0] >= 192,
                   f"busy {mea['busy']} T of {mea['frame_t']}; lines "
                   f"{mea['vram_lines']}")
        doors = [c for c in fr_pushes(script[:tour_n])]
        checks.add(f'{tag}: the three locked doors stop the explorer',
                   len(doors) == 3, f'pushes {doors}')
        if not openmsx:
            continue
        for seed in SEEDS:
            n = len(runs[seed][1])
            rd = RUNS / f'{mname}_seed_{seed}'
            r = emu_run(openmsx, BUILD / f'{GAME}.rom', sym, mname, n,
                        rd, seed=seed, script=script[:n])
            bad = emu_compare(runs[seed][1], r['frames'])
            checks.add(f'{tag} game seed {seed}: bench = openMSX, every '
                       'pass', bad is None,
                       bad or f"{len(r['frames'])} passes")
            if seed is None:
                same, k = emu_irq_same(runs[seed][0], r)
                checks.add(f'{tag}: interrupts at the same T-states',
                           same and k == len(runs[seed][0].irq_log),
                           f'{k} interrupts')
            checks.add(f'{tag} game seed {seed}: openMSX dropped no VRAM '
                       'access, no PSG port A as output',
                       not r['too_fast'] and not r['psg_directions'],
                       f"{r['too_fast'][:2]} {r['psg_directions'][:2]}")
            del r


def fr_pushes(script):
    """The pushes of GAME_TOUR found in the script: the model's
    explorer blocked by a door cell for 20 passes or more, the room
    the same."""
    world = W.World(GAME_ROOM)
    out, run_n = [], 0
    for bits, keys, joy in script:
        room = world.room
        world.update(bits)
        p = world.hero
        side = {U: 'north', D: 'south', L: 'west', R: 'east'}.get(bits)
        if side and p.block and world.room == room and \
                door_ahead(p, side, world.name):
            run_n += 1
            if run_n == 20:
                out.append(f'{world.room} {side}')
        else:
            run_n = 0
    return out


def visit(openmsx, cdir, checks, facts):
    rom, sym = rom_files(VISIT)
    script = tour_script(VISIT_TOUR, GAME_ROOM, doors_open=True)
    rooms_seen = set()
    world = W.World(GAME_ROOM, doors_open=True)
    for bits, k, j in script:
        world.update(bits)
        rooms_seen.add(world.room)
    for mname, (machine, hz) in MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        state = json.loads((BUILD / f'state_{mname}.json').read_text())
        cb = cbios_roms(cdir, mname)
        m, recs, bad, fr, last, ch = bench_walk(rom, sym, state, cb, None,
                                                script, GAME_ROOM,
                                                doors_open=True,
                                                watch=True)
        f = facts.setdefault(f'visit_{mname}', {})
        f['run'] = fr
        walk_checks(checks, f'{tag} visit', bad, len(script))
        rules = rule_checks(m)
        checks.add(f'{tag} visit: the rules (29 T, VDP_CTRL, ROM, R7)',
                   not any(rules.values()), str(rules))
        checks.add(f'{tag} visit: 30 changes of room, the 16 rooms',
                   len(ch) == 30 and len(rooms_seen) == 16,
                   f'{len(ch)} changes, {len(rooms_seen)} rooms')
        mea = measures(m, recs, ch)
        f['measures'] = {k: mea[k] for k in (
            'change_parts', 'changes_same_zone', 'changes_new_zone')}
        if not openmsx:
            continue
        rd = RUNS / f'{mname}_visit'
        r = emu_run(openmsx, BUILD / f'{VISIT}.rom', sym, mname,
                    len(recs), rd, script=script[:len(recs)])
        e = emu_compare(recs, r['frames'])
        same, k = emu_irq_same(m, r)
        checks.add(f'{tag} visit: bench = openMSX, every pass, '
                   'interrupts at the same T-states, nothing dropped',
                   e is None and same and k == len(m.irq_log) and
                   not r['too_fast'] and not r['psg_directions'],
                   e or f"{len(r['frames'])} passes, {k} interrupts")
        del r


def shots(openmsx, cdir, checks, facts, png):
    """Seven rooms reached through a change, the explorer standing:
    openMSX's screenshots = the model."""
    names = msx_model.rooms()
    for mname, (machine, hz) in MACHINES.items():
        state = json.loads((BUILD / f'state_{mname}.json').read_text())
        cb = cbios_roms(cdir, mname)
        bad, hashes, imgs = [], {}, []
        for rname, start, opened, sides in SHOT_PLANS:
            acts = [('stand', 6)]
            for s in sides:
                acts += [('exit', s), ('stand', 24)]
            script = tour_script(acts, start, opened)
            rom, sym = rom_files(rname)
            m, recs, b, fr, last, ch = bench_walk(rom, sym, state, cb,
                                                  None, script, start,
                                                  doors_open=opened)
            # the frame counter of every pass; the shots where the
            # explorer has stood 4 passes, stands 2 more, the counter
            # mod 8 is 4 or 5, 10 passes after a change
            counts = m.counts
            world = W.World(start, doors_open=opened)
            want, ks, last_change = {}, [], -99
            for k, (bits, keys, joy) in enumerate(script, 1):
                if world.update(bits):
                    last_change = k
                if last_change > 0 and k + 2 <= len(script) and \
                        k - last_change >= 10 and \
                        counts[k - 1] % 8 in (4, 5) and \
                        all(script[j - 1][0] == 0
                            for j in range(k - 4, k + 3)) and \
                        (not ks or k - ks[-1] > 8) and \
                        not any(w[0] == world.room for w in want.values()):
                    ks.append(k)
                    want[k] = (world.room, model_screen(
                        world.name, (counts[k - 1] >> 3) & 3,
                        world.hero))
            rd = RUNS / f'{mname}_shots_{rname.replace("/", "_")}'
            emu_run(openmsx, BUILD / f'{rname}.rom', sym, mname,
                    len(script), rd, shots=ks, script=script)
            for k in ks:
                room, rows = want[k]
                for kk in (k, k + 2):
                    p = rd / f'shot_{kk}.png'
                    if not p.exists():
                        bad.append(f'{rname} shot_{kk}.png missing')
                        continue
                    e = shot_ok(p, rows, hz)
                    if e:
                        bad.append(f'{rname} {e}')
                    hashes[f'{rname}_{kk}'] = shot_hash(p)
                p = rd / f'shot_{k}.png'
                if p.exists():
                    dst = png / f'room{room:02}_{hz}hz.png'
                    shutil.copy(p, dst)
                    imgs.append(vram2png.read_png_rgb(dst))
        facts.setdefault('openmsx', {})[f'shots_{mname}'] = hashes
        checks.add(f'{mname} ({hz} Hz): screenshots of {len(imgs)} rooms '
                   'reached through a change = the model, every pixel',
                   not bad and len(imgs) == 7, bad[0] if bad else
                   f'{len(hashes)} screenshots')
        if imgs:
            (png / f'sheet_rooms_{hz}hz.png').write_bytes(
                png_rgb(sheet(imgs, 4), 1))


def rooms(openmsx, cdir, checks, facts):
    names = msx_model.rooms()
    for mname, (machine, hz) in MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        cb = cbios_roms(cdir, mname)
        kept = json.loads((BUILD / f'state_{mname}.json').read_text())
        probs, emu_probs, n_changes = [], [], 0
        for n, name in sorted(names.items()):
            rname = f'rooms/{n:02}'
            rom, sym = rom_files(rname)
            script = room_script(n)
            state, emu = kept, None
            if openmsx and mname == 'eu':
                rd = RUNS / f'room_{n:02}'
                emu = emu_run(openmsx, BUILD / f'{rname}.rom', sym, mname,
                              len(script), rd, script=script)
                state, d = calibrate(state_of(rd, sym, mname), rom, sym,
                                     cb, script, n, emu)
            m, recs, bad, fr, last, ch = bench_walk(rom, sym, state, cb,
                                                    None, script, n)
            n_changes += len(ch)
            bad.update(rule_checks(m))
            problems = [f'{k}: {e}' for k, e in bad.items() if e]
            if problems:
                probs.append(f'room {n}: {problems[0]}')
            facts.setdefault('rooms', {})[f'{mname}_{n:02}'] = fr
            if emu is not None:
                e = emu_compare(recs, emu['frames'])
                if e or emu['too_fast'] or emu['psg_directions']:
                    emu_probs.append(f'room {n}: {e} '
                                     f'{emu["too_fast"][:1]}')
        checks.add(f'{tag}: 16 rooms, {ROOM_FRAMES} passes of input each '
                   f'({n_changes} changes of room): input, explorer, '
                   'screen, solid map, hidden changes, rules',
                   not probs, probs[0] if probs else '')
        if openmsx and mname == 'eu':
            checks.add(f'{tag}: 16 rooms, bench = openMSX every pass, '
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
    ('north_edge_low',
     [('world.asm', 'NORTH_EDGE      equ ROOM_TOP+7-BOX_TOP',
       'NORTH_EDGE      equ ROOM_TOP+6-BOX_TOP')], 'hero'),
    ('entry_margin_4', [('world.asm', 'ENTRY_MARGIN    equ 8 ',
                         'ENTRY_MARGIN    equ 4 ')], 'hero'),
    ('west_goes_east',
     [('world.asm', '        ld a,255                ; a room left',
       '        ld a,1                  ; a room left')], 'hero'),
    ('south_two_rows',
     [('world.asm', '        ld a,GRID_W             ; a row down',
       '        ld a,2*GRID_W           ; a row down')], 'hero'),
    ('doors_open_in_game',
     [('world.asm', 'SOLID_DOOR      equ 1-DOORS_OPEN',
       'SOLID_DOOR      equ 0')], 'hero'),
    ('solid_map_not_built',
     [('room.asm', '        ld (hl),a               ; top left\n',
       '        nop\n')], 'solid'),
    ('room_not_hidden',
     [('world.asm', '        ld a,ROOM_BLANK\n',
       '        ld a,ROOM_BLANK\n        ret\n')], 'hidden'),
    ('explorer_not_hidden',
     [('world.asm', '        ld de,SPRITES\n        ld a,208\n'
       '        ld b,1\n        call vram_fill\n', '')], 'hidden'),
    ('reveal_without_wait',
     [('world.asm', '        halt                    ; the top of a',
       '        nop                     ; the top of a')], 'hidden'),
    ('zone_before_black',
     [('world.asm', '        push af\n        call hide_room\n'
       '        pop af\n        call enter_room\n',
       '        call enter_room\n        call hide_room\n')], 'hidden'),
    ('flames_of_the_old_phase',
     [('zone.asm', '        xor a\n        ld (flame_phase),a',
       '        ld a,(flame_phase)\n        ld (flame_phase),a')],
     'screen'),
    ('name_not_changed',
     [('room.asm', '        call build_room         ; HL: then the '
       'name\n        jp hud_draw', '        call build_room         ; '
       'HL: then the name\n        ld a,(zone)\n        cp #FF\n'
       '        ret nz\n        jp hud_draw')], 'screen'),
    ('vdp_address_unguarded',
     [('vdp.asm', 'vram_write_at:\n        di\n',
       'vram_write_at:\n        nop\n')], 'ctrl'),
    ('right_wins', [('hero.asm', '        bit 2,c                 ; left',
                     '        bit 3,c                 ; left')], 'hero'),
    ('list_not_ended',
     [('hero.asm', '        ld a,208                ; the list ends',
       '        ld a,207                ; the list ends')], 'registers'),
    ('keys_row_7', [('input.asm', 'KEY_ROW         equ 8 ',
                     'KEY_ROW         equ 7 ')], 'input'),
    ('skin_in_khaki', [('hero.asm', 'HERO_SKIN       equ 9 ',
                        'HERO_SKIN       equ 10')], 'screen'),
    ('psg_port_a_out',
     [('start.asm', '        ld a,%10111111          ; bits 7-6',
       '        ld a,%11111111          ; bits 7-6')], 'r7'),
]


def mutations(sjasm, openmsx, cdir, checks, facts):
    state = json.loads((BUILD / 'state_eu.json').read_text())
    cb = cbios_roms(cdir, 'eu')
    game_s = tour_script(GAME_TOUR, GAME_ROOM)
    visit_s = tour_script(SHORT_VISIT, GAME_ROOM, doors_open=True)
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
            built = []
            for tag, doors in (('m', 0), ('v', 1)):
                code, msg = run([sjasm, '--nologo', '--msg=war',
                                 f'-DSTART_ROOM={GAME_ROOM}',
                                 f'-DDOORS_OPEN={doors}',
                                 f'-i{GENERATED.as_posix()}',
                                 f'--raw={(tmp / (tag + ".rom")).as_posix()}',
                                 f'--sym={(tmp / (tag + ".sym")).as_posix()}',
                                 (src / 'cryptmorrow.asm').as_posix()], tmp)
                built.append((code, msg))
            if any(c for c, msg in built) or not ok_edit:
                checks.add(f'mutation {mname}: applied and assembled',
                           False, built[0][1] or 'the text to change is '
                           'not there once')
                continue
            stopped = set()
            for tag, script, opened in (('m', game_s, False),
                                        ('v', visit_s, True)):
                rom, sym = rom_files(tag, tmp)
                m, recs, bad, fr, last, ch = bench_walk(
                    rom, sym, state, cb, None, script, GAME_ROOM,
                    doors_open=opened)
                bad.update(rule_checks(m))
                stopped |= {k for k, e in bad.items() if e}
            out[mname] = sorted(stopped)
            emu = ''
            if openmsx and must == 'r7':
                rd = RUNS / f'mut_{mname}'
                rom, sym = rom_files('m', tmp)
                r = emu_run(openmsx, tmp / 'm.rom', sym, 'eu', 60, rd,
                            script=game_s[:60])
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
        RUNS = Path(tempfile.mkdtemp(prefix='verify_0_3_'))
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
        game(openmsx, cdir, checks, facts, a)
        visit(openmsx, cdir, checks, facts)
        if openmsx:
            shots(openmsx, cdir, checks, facts, png)
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
    (out / 'verify_0_3.json').write_text(json.dumps(report, indent=1)
                                         + '\n', encoding='utf-8')
    print(f'\n{len(checks.items)} checks, {len(checks.failed)} failed')
    for c in checks.failed:
        print('FAILED:', c['check'], c['detail'])
    return 1 if checks.failed else 0


if __name__ == '__main__':
    sys.exit(main())

"""Milestone 0.8 checks: the complete cartridge. At power on the
opening screen (the ZX game's loading screen) for three seconds or
until FIRE; then, as in milestone 0.7, the title with the menu of the
sound, the end screens, a new game from the title
(game/src/screens.asm), on the two C-BIOS MSX1 machines (EU: TMS9929A,
50 Hz; INT: TMS9918A, 60 Hz).

  sessions  (tests/sessions_0_8.py) the cartridge from its start, as a
            player uses it: the opening for its three seconds (or
            ended by FIRE), the title, the menu up and down, FIRE, the
            whole game (VICTORY), the room still, the end screen, FIRE,
            the title, a game in SOUND FX and one in SILENT that end in
            GAME OVER; and a short one in MUSIC to GAME OVER. Every
            pass = the model of the states and of the screens
            (tests/msx_states.py: art.py's loading, title and end
            screens, recoloured as the rooms), each game = the same
            game in the tests' cartridge pass by pass, the sound = the
            model, the rules; the short one again with the RAM filled
            at random (seeds 1, 2): the same, and the RAM written only
            in the areas of vars.asm and the stack; in openMSX the
            same, byte for byte, its screenshots (the opening too) and
            its recorded piece of the end.

The other checks are those of milestone 0.6.1, on the tests'
cartridges (cryptmorrow_play*.rom: START_PLAY, the game at once in
each mode of the sound, as the cartridge was before the title); the
games stop ENDING_FRAMES - 1 passes after their end (then the end
screen comes); the pieces of the end to their end are in the sessions.
From milestone 0.6.1 (the author, after the hand test of 0.6: «i suoni
sembrano avere un leggero ritardo»):

  latency   every effect asked in SOUND FX (and taken, by its
            priority) sounds in the group of registers sent at the
            next interrupt, the one whose picture shows what asked
            for it; in MUSIC the piece of the end has its first frame
            in that group

  calls     the sounds the program asks in every pass (sound_effect,
            end_sound; set_audio at the start, in the ROM's mode) =
            the sounds of the model's pass (tests/world_model.py), in
            order
  psg       every group of the 11 registers 0-10 sent to the PSG (by
            the interrupt every frame, and by psg_silence at once) =
            tests/psg_model.py fed with the interrupts and the sounds
            asked, at the times the bench took them (the model says
            what, the bench when); every other write: registers 11-13
            at 0 after a silence, register 15 to read the joystick;
            in MUSIC the registers sent at the same T-state after
            every interrupt (the next frame always worked out
            before: by the main loop, or by the interrupt while a
            room is built)
  sound     the music data in the cartridge, read back = c64/score.py
            (patterns, order lists) and c64/sfx.py (the effects, from
            their first note: without the C64's frame of the gate
            off; the C64's priorities), every note played with the period
            round(1 789 772.5 / (16 f)); the theme in the bench, a
            whole loop and more (3 072 frames at 50 Hz, 6 a step;
            3 584 at 60 Hz, 7 a step): = the model, the second loop
            as the first, the cost of the interrupt frame by frame;
            the eight effects, each alone, and the priorities; in
            openMSX the sound itself, as WAV files (wav/): the theme
            (a loop at 50 Hz, 20 seconds at 60), the eight effects,
            the pieces of the end (in the runs of the game and of the
            defeat); the pitch of the fanfare's E6 measured in
            openMSX's sound = the PSG's 1 789 772.5 Hz (within 3
            cents; the 128K's AY clock would be 16 cents off); the
            loudness of every frame following the registers sent,
            every steady note of the lead and 8 in 10 of the bass
            found in the sound (the ZX's rules for its AY)
  data      the objects, doors and enemies in the cartridge (the
            rooms' records, door_table) = the room files
            (dungeon.py); the nine images of the combat in the sprite
            shapes (VRAM, after INIT) = art_pieces.COMBAT_FRAMES
  state     the BIOS state at INIT of the game, read from openMSX, the
            first interrupt fitted to openMSX's T-states over 300
            passes (calibrate); compared with the one kept in
            game/build
  game      the whole game in the bench, fighting: the inputs planned
            by tests/game_plan.py with the models (the ZX's steps and
            fighter, tests/game_0_5.json), two passes without input
            first, AFTER_END passes after VICTORY (the piece of the
            end); keyboard, joystick 1 or both (the joystick read
            with the music on); in MUSIC three starts (the RAM and
            VRAM C-BIOS left, two random fillings, these on the first
            passes), in SOUND FX and SILENT one. After every pass of
            the main loop: the input byte (0 while the blade is out);
            the room and the explorer = the model (tests/world_model.py, with
            tests/hero_model.py: the ZX rules); the game (keys, seals,
            score, energy, doors open, the end, the objects taken) =
            the model; the combat (the pass counter, the blow, the
            damage timer, the three enemies, the sprite list
            prepared, its rotation) = the model; the sprite list in
            the VDP = the model's; the screen = tests/msx_model.py
            (the room as it is, the HUD as it was at the top of the
            pass, VICTORY or GAME OVER, the sprites four on a line;
            the room black after a change); the frame counter = the
            interrupts taken, the room, the zone, the stack; the map
            of solid cells in RAM = the room's text with its door
  defeat    GAME OVER: energy 2 put in RAM, out of the Moss Gate and
            down to the skeleton of the Crossroads, still until it
            touches the explorer; then 260 passes of input that change
            nothing (the piece of the defeat); the same checks every
            pass, in the three modes
  hidden    every change of room, from the program's VRAM writes and
            the times the picture shows each row, until the room is
            shown at the top of the next pass: no picture shows the
            room half built; no sprite while it is black; the cells of
            the zone written only while it is black
  sprites   the passes with a fifth sprite on a line (the VDP's 5S
            flag, which turns the order) and the longest run of
            pictures in which a figure is cut
  rooms     a ROM for every room (START_ROOM 0-15), 300 passes of
            input each (a game that ends in them stops 49 passes
            later: the end screen is the sessions'): the same checks,
            in openMSX too (50 Hz) and in the bench at 60 Hz
  openMSX   the game and the defeat in openMSX with the same input and
            pokes: RAM, VRAM, VDP and PSG registers (but 14) and
            T-states of every frame_ready = bench (the whole game read
            back from openMSX's file a pass at a time); interrupts at
            the same T-states; every write to the PSG = the bench's,
            at the same T-state (MUSIC and SOUND FX). The joystick
            is given right after IN A,(#A2) (an aid of the test:
            openMSX 21.0 has no command for it)
  shots     screenshots of openMSX: the portal open, VICTORY, two
            fights of the game (frozen by game_ended put in RAM), GAME
            OVER = the model with the machine's palette, every pixel
  palettes  the Phase 0 probe on both machines: the 15 colours of
            tools/vram2png.py
  rules     no VRAM access closer than 29 T-states in the picture,
            nothing dropped by openMSX, every byte to VDP_CTRL with
            interrupts off, no write to ROM, PSG register 7 always
            10xxxxxx, every access to the PSG's ports with interrupts
            off (the interrupt selects registers too), the VDP
            registers of Screen 2; RAM written only in the areas of
            game/src/vars.asm and the stack
  measures  T-states of the start-up and its parts, of every frame
            and of its parts (music_due too), of the interrupt (with
            and without the music worked out in it), of the frames
            that open a door, take an object, hit or defeat an enemy,
            take a touch or end the game, of every change of room;
            the lines where the frames without a change write VRAM,
            the stack's depth
  mutations copies of the source with one mistake each: every one
            must be stopped by the check named

Writes OUT/verify_0_8.json and, in OUT/png, the screenshots of
openMSX, a sheet made from them and the combat's images as the
cartridge has them; in OUT/wav the sound of openMSX. --reference FILE
compares the facts with another run (the workspace's, on the PC);
--no-openmsx runs only the bench.

Usage: python tests/verify_0_8.py --out DIR [--openmsx EXE |
           --no-openmsx] [--reference FILE] [--update-state]
           [--keep-runs] [--sjasmplus EXE] [--only PART,...]
Needs the build: python tools/build_game.py
"""
import argparse
import array
import bisect
import hashlib
import json
import math
import random
import shutil
import struct
import sys
import tempfile
import wave
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
import game_plan  # noqa: E402
import psg_model as P  # noqa: E402
import route as RT  # noqa: E402
import vram2png  # noqa: E402
import world_model as W  # noqa: E402
from msxtools import CBIOS, cbios_dir, find_tool, run  # noqa: E402
from make_chain import final_text  # noqa: E402

dungeon = msx_model.dungeon
MACHINES = {    # name: openMSX machine, Hz
    'eu': ('C-BIOS_MSX1_EU', 50),
    'int': ('C-BIOS_MSX1', 60),
}
VERSION = 'B'                   # the graphics of the game
CARTRIDGE = 'cryptmorrow'      # the opening, the title (0.7, 0.8)
GAME = 'cryptmorrow_play'       # the tests' cartridges: the game
GAMES = {P.MODE_MUSIC: 'cryptmorrow_play',      # at once
         P.MODE_FX: 'cryptmorrow_play_fx',
         P.MODE_SILENT: 'cryptmorrow_play_silent'}
ENDING_FRAMES, END_DELAY = 50, 100     # screens.asm
MODE_NAMES = {P.MODE_MUSIC: 'MUSIC', P.MODE_FX: 'SOUND FX',
              P.MODE_SILENT: 'SILENT'}
MUSIC = json.loads((GENERATED / 'music.json').read_text())
CLOCK = 3579545
GAME_ROOM = 1
SEEDS = (None, 1, 2)
SEED_PASSES = 2000              # the random fillings: the start
ROOM_FRAMES = 300
U, D, L, R, F = H.JOY_UP, H.JOY_DOWN, H.JOY_LEFT, H.JOY_RIGHT, \
    H.JOY_FIRE
KEY_NAMES = {U: 'UP', D: 'DOWN', L: 'LEFT', R: 'RIGHT', F: 'SPACE'}
JOY_NAMES = {U: 'UP', D: 'DOWN', L: 'LEFT', R: 'RIGHT', F: 'A'}
# The whole game: the plan of tests/game_plan.py (the ZX's steps and
# fighter, played on the models), after two passes without input
# (openmsx_run gives the input of a pass at the frame_ready before
# it: pass 1 has none).
PLAN_FILE = HERE / game_plan.PLAN_FILE
PREFIX = 2
AFTER_END = ENDING_FRAMES - 1   # passes after VICTORY: the room still
# Steps of the other scripts: ('exit', side), ('get', column, row),
# ('push', side, frames) (walk into a door, then keep pushing, FIRE
# pressed every other 8 frames), ('stand', frames) (a screenshot in
# every stand of 24 passes or more), ('wait', frames) (no
# screenshot), ('plan', n) (the first n passes of the game's plan),
# ('down_to', y) (walk down to that line), ('until_end',) (stand
# until the game ends), ('poke', name, value) (a byte of RAM put
# there before the next pass, with hud_dirty for the HUD; game_ended
# freezes the game where it is, for a screenshot).
DEFEAT_STEPS = [('wait', 2), ('poke', 'energy', 2), ('exit', 'south'),
                ('down_to', 106), ('until_end',)]
AFTER_DEFEAT = ENDING_FRAMES - 1
SHOT_PLANS = [
    # the portal opened with three seals and the keys put in RAM;
    # out through it: VICTORY
    (GAME, 1, [('wait', 2), ('poke', 'key_set', 7),
               ('poke', 'seals', 3), ('wait', 4), ('push', 'north', 0),
               ('stand', 24), ('exit', 'north'), ('stand', 30)]),
    # two moments of the game's fights, frozen: the Crossroads, the
    # blade down on the skeleton just hit, red; the Bone Pit, the
    # blade up, the skeleton and the dust of the bat
    (GAME, 1, [('wait', 2), ('plan', 288), ('poke', 'game_ended', 1),
               ('stand', 30)]),
    (GAME, 1, [('wait', 2), ('plan', 956), ('poke', 'game_ended', 1),
               ('stand', 30)]),
    # GAME OVER
    (GAME, 1, DEFEAT_STEPS + [('stand', 30)]),
]
SHOTS_WANTED = 5
CHOICES = [0, R, L, D, U, F, R | U, R | D, L | U, L | D, L | R, U | D,
           R | F, U | F]
SOURCES = ('keys', 'joy', 'both')
# the RAM of game/src/vars.asm: [first, last + 1)
RAM_AREAS = ((0xC000, 0xC0BC), (0xC100, 0xC3A0), (0xC400, 0xC680),
             (0xC680, 0xC68C), (0xC690, 0xC69B), (0xC6A0, 0xC6D9),
             (0xC6E0, 0xC718), (0xC720, 0xC720 + 26 * 34 + 32 * 32),
             (0xF000, 0xF101), (0xF1F1, 0xF1F4))
STACK, STACK_ROOM = 0xF380, 64
VDP_REGS = [0x02, 0xE2, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x01]
ROOM_BLANK = 0xE0
ROOM_NAMES = (0x1800 + 2 * 32, 0x1800 + 22 * 32)   # rows 2-21
WATCH = ('init', 'vdp_init', 'psg_init', 'vars_init', 'load_glyphs',
         'load_shapes',
         'enter_room', 'load_zone', 'build_room', 'show_door',
         'spawn_enemies', 'hud_draw', 'put_names', 'hero_init',
         'show_combat', 'put_sprites', 'irq_init', 'main_loop', 'isr',
         'animate_torches', 'hud_update', 'reveal_room', 'read_input',
         'check_fire', 'update_hero', 'check_exits', 'change_room',
         'hide_room', 'room_built', 'check_door', 'check_objects',
         'update_enemies', 'check_blade', 'check_contact', 'game_over',
         'victory', 'frame_ready', 'music_due', 'music_step',
         'isr_done', 'audio_frame', 'psg_flush', 'fx_frame')
SOUND_MARKS = ('set_audio', 'end_sound', 'sound_effect')
HERO_VARS = ('hero_x', 'hero_y', 'hero_dir', 'hero_frame',
             'hero_timer', 'hero_moving', 'hero_block')
WHAT = ('reached', 'input', 'hero', 'game', 'combat', 'sprites',
        'screen', 'variables', 'registers', 'solid', 'hidden', 'calls',
        'psg', 'psg_time', 'latency')
LABELS = {'reached': 'frame_ready every pass',
          'input': 'the input byte = keys + joystick (0 while the '
                   'blade is out)',
          'hero': 'room and explorer = the model',
          'game': 'keys, seals, score, energy, doors, end, objects',
          'combat': 'blow, damage, enemies, sprite list = the model',
          'sprites': 'the sprite list in the VDP = the model',
          'screen': 'screen = model, every pass',
          'variables': 'frames = interrupts, room, zone, stack',
          'registers': 'VDP registers of Screen 2',
          'solid': 'solid map in RAM = the room with its door',
          'hidden': 'every change hidden',
          'calls': 'the sounds asked = the model\'s, in order',
          'psg': 'every group of registers sent to the PSG = the model '
                 '(psg_model), the other writes as they must be',
          'psg_time': 'the PSG\'s registers sent at the same T-state '
                      'after every interrupt (the music\'s next frame '
                      'always ready)',
          'latency': 'every effect taken, and the piece of an end, '
                     'heard at the next interrupt'}
RULES = ('29T', 'ctrl', 'rom', 'r7', 'psgdi')
RUNS = None
WAVS = None
GAME_RUNS = ('music', 'fx', 'silent')   # the parts of game()


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


def plan_inputs():
    """The game's plan: the inputs of every pass."""
    data = json.loads(PLAN_FILE.read_text())
    return game_plan.decode(data['inputs'])


def plan_steps(world, steps):
    """The steps planned on `world`, which moves along: (bits a pass,
    {pass: [(name, value)]} the pokes)."""
    bits, pokes = [], {}
    for st in steps:
        if st[0] == 'poke':
            pokes.setdefault(len(bits) + 1, []).extend(
                [(st[1], st[2]), ('hud_dirty', 1)])
            poke_model(world, st[1], st[2])
            continue
        if st[0] == 'exit':
            path = RT.plan_exit(world, st[1])
        elif st[0] == 'get':
            path = RT.plan_get(world, st[1], st[2])
        elif st[0] == 'push':
            side = RT.PUSH[st[1]]
            path = RT.plan_push(world, st[1])
            path += [side | (F if (i >> 3) & 1 else 0)
                     for i in range(st[2])]
        elif st[0] == 'plan':
            path = plan_inputs()[:st[1]]
        elif st[0] == 'down_to':
            path = []
            probe = world.clone()
            while probe.hero.y < st[1] and not probe.ended:
                probe.update(D)
                path.append(D)
        elif st[0] == 'until_end':
            path = []
            probe = world.clone()
            while not probe.ended:
                probe.update(0)
                path.append(0)
                if len(path) > 3000:
                    raise ValueError('the game does not end')
        else:                           # stand, wait
            path = [0] * st[1]
        for b in path:
            world.update(b)
        bits += path
    return bits, pokes


def poke_model(world, name, value):
    if name in ('energy', 'key_set', 'seals'):
        setattr(world, name, value)
    elif name == 'game_ended':
        world.ended = value             # frozen: no name changes


_PLANS = {}


def plan_script(steps, room):
    """(script, pokes): the steps' inputs as keys and joystick, and
    the pokes."""
    key = (tuple(tuple(s) for s in steps), room)
    if key not in _PLANS:
        world = W.World(room)
        bits, pokes = plan_steps(world, steps)
        _PLANS[key] = (script_of(runs_of(bits), SOURCES), pokes)
    script, pokes = _PLANS[key]
    return list(script), dict(pokes)


_GAME = []


def game_script():
    """The whole game: the plan after PREFIX passes without input, up
    to VICTORY, then AFTER_END passes without input (the room still;
    from milestone 0.7 the end screen comes after them)."""
    if not _GAME:
        bits = [0] * PREFIX + plan_inputs()
        script = script_of(runs_of(bits), SOURCES)
        end = end_pass(script, {})
        script = script[:end] + script_of(runs_of([0] * AFTER_END),
                                          SOURCES)
        _GAME.append(script)
    return list(_GAME[0]), {}


def defeat_script():
    """GAME OVER, then AFTER_DEFEAT passes of input."""
    script, pokes = plan_script(DEFEAT_STEPS, GAME_ROOM)
    return script + random_route(9, AFTER_DEFEAT), pokes


def room_script(n):
    """ROOM_FRAMES passes of random input in room n; a game that ends
    in them (room 3: GAME OVER) is cut AFTER_END passes later, as the
    whole game: from milestone 0.7 the end screen would come (the
    sessions try it)."""
    # two frames without input first: openmsx_run gives the input of
    # a frame at the frame_ready before it, and frame 1 has none
    script = [(0, (), ())] * 2 + random_route(100 + n, ROOM_FRAMES - 2)
    end = end_pass(script, {}, n)
    return script[:end + AFTER_END] if end else script


def inputs_of(script):
    """openmsx_run's input: {frame: (keys, joy)} where it changes."""
    assert script[0][0] == 0, 'no input can be given for frame 1'
    out, prev = {}, None
    for k, (bits, keys, joy) in enumerate(script, 1):
        if (keys, joy) != prev:
            out[k] = (keys, joy)
            prev = (keys, joy)
    return out


def pokes_of(pokes, sym):
    """openmsx_run's pokes: {pass: [(address, value)]}."""
    return {k: [(sym[n], v) for n, v in lst] for k, lst in pokes.items()}


# -- the model, cached ------------------------------------------------

_MODEL = {}


def model_room(name, phase, drawn):
    key = (name, phase, tuple(sorted(drawn.items())))
    if key not in _MODEL:
        if len(_MODEL) > 2000:
            _MODEL.clear()
        _MODEL[key] = msx_model.screen(name, phase, VERSION, **drawn)
    return _MODEL[key]


def model_screen(world, count):
    """The screen of the world at a frame counter: the room black
    after a change, else with the sprites in the VDP."""
    rows = model_room(world.name, (count >> 3) & 3, world.drawn())
    if world.black:
        return msx_model.black_room(rows)
    return msx_model.with_sprites(rows, world.sat())


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
    back = regs[7] & 15                 # transparent: the backdrop
    return [[c or back for c in r] for r in rows]


def first_diff(a, b):
    for y in range(len(a)):
        if a[y] != b[y]:
            x = next(i for i in range(len(a[y])) if a[y][i] != b[y][i])
            return y, x, a[y][x], b[y][x]
    return None


# -- a change of room, as the picture shows it ---------------------------

ORDER = ('old', 'black', 'new')


def hidden(before, writes, t0, t1, vdp, after, t_hide):
    """A change of room from the VRAM writes [(T, address, value)]
    between two frame_ready (T t0 and t1: the pass before the change
    and the pass after it, which shows the new room), the VRAM before
    and after. Every picture that starts in between must show, in
    every row of the room from its first line to its last, the old
    room, the room black or the new room, the same in all rows, in
    this order; no sprite while black (sprite 0's Y = 208 at the start
    and the end of the picture); from hide_room on (T t_hide), slots
    0-#DF of the patterns and colours written only while all the room
    is black. Returns (problem or None, black pictures)."""
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
                    wt >= t_hide and problem is None:
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

def bcd(ram, at):
    """Three bytes of two BCD digits, the highest first (a digit
    above 9, as a mistake would leave it, counts as it is)."""
    v = 0
    for b in ram[at:at + 3]:
        v = v * 100 + (b >> 4) * 10 + (b & 15)
    return v


def sat_of(vram):
    """The sprite list in the VDP: (Y, X, shape, colour) up to Y =
    208."""
    out = []
    for k in range(32):
        e = tuple(vram[0x1B00 + 4 * k:0x1B04 + 4 * k])
        if e[0] == 208:
            break
        out.append(e)
    return out


def event_of(g0, g1, c0, c1):
    """What a pass did to the game: from the model's game_state and
    combat_state before and after it."""
    if g1[5] != g0[5]:
        return 'end'
    if g1[4] != g0[4]:
        return 'door'
    if g1[6:] != g0[6:]:
        return 'object'
    if g1[3] < g0[3]:
        return 'touch'
    if g1[2] != g0[2]:
        return 'defeat'
    hp0 = [c0[8 + 9 * i + W.HP] for i in range(3)]
    hp1 = [c1[8 + 9 * i + W.HP] for i in range(3)]
    if hp1 != hp0:
        return 'hit'
    if c1[1] == W.SLASH_FRAMES:
        return 'blow'
    if g1 != g0:
        return 'state'
    return None


class MarksA(list):
    """The bench's marks, with the A register at each: (name, T,
    A)."""
    def __init__(self, m):
        super().__init__()
        self.m = m

    def append(self, x):
        super().append(x + (self.m.regs[msxsim.A_],))


def expected_calls(sounds, mode):
    """What the program must call for the sounds of a pass:
    sound_effect (A = SFX number) for an effect; for the end,
    end_sound (A = ENDED_*), which outside MUSIC goes on into
    sound_effect with its effect. With the model's sound of each."""
    out = []
    for s in sounds:
        if s in ('won', 'lost'):
            ended = W.ENDED_WON if s == 'won' else W.ENDED_LOST
            out.append(('end_sound', ended, ('end', s == 'won')))
            if mode != P.MODE_MUSIC:
                out.append(('sound_effect', P.SFX[s], None))
        else:
            out.append(('sound_effect', P.SFX[s], ('sfx', P.SFX[s])))
    return out


class PSGLog:
    """The bench's PSG log, read as it grows: the groups of the 11
    registers 0-10 written in order (T of the first write, values)
    and the other writes."""
    def __init__(self, psg):
        self.log = psg.log
        self.at = 0
        self.groups = []
        self.others = []

    def update(self):
        log, i = self.log, self.at
        while i < len(log):
            if log[i][1] == 0:
                if i + 11 > len(log):
                    break
                if [x[1] for x in log[i:i + 11]] == list(range(11)):
                    self.groups.append((log[i][0],
                                        [x[2] for x in log[i:i + 11]]))
                    i += 11
                    continue
            self.others.append(log[i])
            i += 1
        self.at = i


JOY_PORT1 = 0x8F                # input.asm: R15, port 1


def bench_walk(rom, sym, state, cb, seed, script, start, pokes=None,
               watch=False, until=None, screen=True, mode=P.MODE_MUSIC):
    """The program with this input (and these pokes), checked after
    every pass of the main loop (the screen only if `screen`: the
    mutations leave it out but where it is the check that must stop
    them); with `until`, it stops as soon as that check fails. `mode`:
    the ROM's SOUND_MODE. Returns (machine, records for openMSX,
    problems, facts, last RAM, the changes of room, the passes)."""
    m = msxsim.MSX(rom, state, cb, seed=seed)
    m.watch = {sym[w]: w for w in (WATCH if watch else ('hide_room',))
               + SOUND_MARKS + ('room_built', 'isr', 'isr_done',
                                'music_init')}
    # the instruction after sound_effect's DI: from there the
    # interrupt waits (the time an effect is asked)
    se = sym['sound_effect']
    m.watch[rom.index(0xF3, se - 0x4000) + 0x4001] = 'se_held'
    m.marks = MarksA(m)
    hz = state['hz']
    pm = P.PSGMachine(MUSIC, hz)
    plog = PSGLog(m.psg)
    psg_on = []
    psg_write, psg_read = m.psg.write, m.psg.read

    def psg_w(port, value, t):
        if m.regs[msxsim.IFF_] and not psg_on:
            psg_on.append(f'write #{0xA0 + (port & 3):02X} at T {t}')
        psg_write(port, value, t)

    def psg_r():
        if m.regs[msxsim.IFF_] and not psg_on:
            psg_on.append(f'read #A2 at T {m.tstates}')
        return psg_read()
    m.psg.write, m.psg.read = psg_w, psg_r
    m.psg_on = psg_on
    irq_done, marks_done, checked, times_done = 0, 0, 0, 0
    heard = []                  # requests whose sound is awaited
    times_g = []                # the T-state of every group sent
    flush_base = None           # T from the interrupt to a flush
    late, late_bad = [], None
    sound_facts = {'calls': {}, 'late_flushes': 0}
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
    m.ctrl_on = ctrl_on
    pokes = pokes or {}
    world = W.World(start)
    hv = [sym[v] - 0xC000 for v in HERO_VARS]
    inp = sym['input'] - 0xC000
    so = sym['solid_map'] - 0xC000
    gs = [sym[v] - 0xC000 for v in ('key_set', 'seals')]
    score, energy = sym['score'] - 0xC000, sym['energy'] - 0xC000
    doors, ended = sym['doors_open'] - 0xC000, sym['game_ended'] - 0xC000
    taken = sym['taken'] - 0xC000
    cv = [sym[v] - 0xC000 for v in ('turn', 'slash_timer', 'blade_dir',
                                     'fire_held', 'invulnerable',
                                     'hero_shown', 'spr_rot',
                                     'spr_count')]
    en, sl = sym['enemies'] - 0xC000, sym['spr_list'] - 0xC000
    bad = dict.fromkeys(WHAT)
    recs, digest, changes, quiet, passes = [], hashlib.sha256(), [], [], []
    counts, fifths = [], []
    ram = None
    pend = None             # a change waiting for its room to show
    before, t_prev = bytes(vdp.vram), m.tstates
    for k, (bits, keys, joy) in enumerate(script, 1):
        for name, v in pokes.get(k, ()):
            m.mem[sym[name]] = v
            poke_model(world, name, v)
        m.set_input(keys, joy)
        n_irq = len(m.irq_log)
        n_marks = len(m.marks)
        try:
            m.run_to(sym['frame_ready'], max_t=40 * vdp.frame_t)
        except RuntimeError as e:
            bad['reached'] = f'pass {k} of {len(script)}: {e}'
            break
        g0, c0 = world.game_state(), world.combat_state()
        changed = world.update(bits)
        ram = bytes(m.mem[0xC000:0xF380])
        vram = bytes(vdp.vram)
        regs = list(vdp.regs)
        count = ram[0] | ram[1] << 8
        counts.append(count)
        if W.fifth(world.picture):
            fifths.append(k)
        if bad['input'] is None and ram[inp] != world.input:
            bad['input'] = f'pass {k}: #{ram[inp]:02X}, model ' \
                           f'#{world.input:02X}'
        prog = (ram[sym['room'] - 0xC000],) + tuple(ram[a] for a in hv)
        if bad['hero'] is None and prog != world.state():
            bad['hero'] = f'pass {k}: {prog}, model {world.state()}'
        game = (ram[gs[0]], ram[gs[1]], bcd(ram, score), ram[energy],
                ram[doors], ram[ended]) + tuple(ram[taken:taken + 32])
        if bad['game'] is None and game != world.game_state():
            bad['game'] = f'pass {k}: {game[:6]}, model ' \
                          f'{world.game_state()[:6]}' + (
                              ' (objects taken)' if game[:6] ==
                              world.game_state()[:6] else '')
        combat = tuple(ram[a] for a in cv) + tuple(ram[en:en + 27]) + \
            tuple(ram[sl:sl + 4 * ram[cv[7]]])
        if bad['combat'] is None and combat != world.combat_state():
            bad['combat'] = f'pass {k}: {combat}, model ' \
                            f'{world.combat_state()}'
        if bad['sprites'] is None and sat_of(vram) != world.sat():
            bad['sprites'] = f'pass {k}: {sat_of(vram)}, model ' \
                             f'{world.sat()}'
        if screen and bad['screen'] is None:
            d = first_diff(screen_of(vram, regs),
                           model_screen(world, count))
            if d:
                bad['screen'] = (f'pass {k} (room {world.room}): pixel '
                                 f'({d[1]}, {d[0]}) colour {d[2]}, '
                                 f'model {d[3]}')
        if bad['variables'] is None:
            vals = {'frames': (count, len(m.irq_log) & 0xFFFF),
                    'room': (ram[5], world.room),
                    'zone': (ram[6], msx_model.zone_of(world.name)),
                    'reveal_due': (ram[sym['reveal_due'] - 0xC000],
                                   int(changed)),
                    'SP': (m.regs[msxsim.SP_], STACK)}
            wrong = [f'{n} {a} not {b}' for n, (a, b) in vals.items()
                     if a != b]
            if wrong:
                bad['variables'] = f'pass {k}: ' + ', '.join(wrong)
        if bad['registers'] is None and regs != VDP_REGS:
            bad['registers'] = f'pass {k}: VDP {regs}'
        if bad['solid'] is None and \
                list(ram[so:so + 640]) != world.hero.solid:
            bad['solid'] = f'pass {k}: the solid map in RAM (room ' \
                           f'{world.room})'
        if pend is not None:
            # the pass after a change: the room is shown
            p_before, p_t0, p_hide, p_writes, p_k, p_irq, p_t = pend
            e, black = hidden(p_before, p_writes + writes, p_t0,
                              m.tstates, vdp, vram, p_hide)
            if e and bad['hidden'] is None:
                bad['hidden'] = f'pass {p_k} (to room {world.room}): {e}'
            changes.append({'pass': p_k, 'room': world.room,
                            'irq': p_irq, 'black': black, 't': p_t})
            pend = None
        if changed:
            hides = [t for n, t, a in m.marks[n_marks:]
                     if n == 'hide_room']
            pend = (before, t_prev, hides[0] if hides else t_prev,
                    list(writes), k, len(m.irq_log) - n_irq,
                    m.tstates - t_prev)
        else:
            if not (changes and changes[-1]['pass'] == k - 1):
                quiet.extend(t for t, a, v in writes)
            if len(m.irq_log) - n_irq != 1 and bad['hidden'] is None:
                bad['hidden'] = f'pass {k}: {len(m.irq_log) - n_irq} ' \
                                'interrupts without a change'
        # -- the sound: the calls, then the PSG
        pm_marks = [x for x in m.marks[marks_done:]
                    if x[0] in SOUND_MARKS + ('se_held', 'music_init')]
        got, times = [], []
        for i, (n, t, a) in enumerate(pm_marks):
            if n not in SOUND_MARKS:
                continue
            got.append((n, a))
            # when it takes effect: an effect after the DI, a piece
            # in music_init (with the interrupt held off)
            then = {('sound_effect', P.MODE_FX): 'se_held',
                    ('end_sound', P.MODE_MUSIC): 'music_init'}.get(
                        (n, mode))
            if then:
                t = next((tt for nn, tt, aa in pm_marks[i + 1:]
                          if nn == then), t)
            times.append(t)
        want = expected_calls(world.sounds, mode)
        if k == 1:
            want = [('set_audio', mode, ('mode', mode))] + want
        if bad['calls'] is None and got != [(n, a) for n, a, s in want]:
            bad['calls'] = f'pass {k}: {got}, model ' \
                           f'{[(n, a) for n, a, s in want]}'
        for s in world.sounds:
            sound_facts['calls'][s] = sound_facts['calls'].get(s, 0) + 1
        events = [(t, w[2]) for t, w in zip(times, want) if w[2]]
        events += [(t, ('irq',)) for t in m.irq_log[irq_done:]]
        for t, e in sorted(events):
            if e[0] == 'irq':
                pm.interrupt()
            elif e[0] == 'mode':
                pm.set_audio(e[1])
                if e[1] == P.MODE_MUSIC:
                    heard.append((t, k, 'music', None))
            elif e[0] == 'end' and mode == P.MODE_MUSIC:
                pm.end_sound(e[1])
                heard.append((t, k, 'music', None))
            else:
                # an effect, or the effect of an end (SOUND FX)
                n = P.SFX['won' if e[1] else 'lost'] if e[0] == 'end' \
                    else e[1]
                took = pm.fx.asked - pm.fx.refused
                if e[0] == 'end':
                    pm.end_sound(e[1])
                else:
                    pm.sfx(n)
                if pm.fx.asked - pm.fx.refused > took:
                    # it replaces an effect asked before the same
                    # interrupt
                    i = bisect.bisect_right(m.irq_log, t)
                    heard[:] = [h for h in heard if h[2] != 'effects' or
                                bisect.bisect_right(m.irq_log, h[0]) != i]
                    heard.append((t, k, 'effects', n))
        plog.update()
        # an effect taken, a song begun: heard in the group that the
        # next interrupt sends (the first of its kind after the
        # request): the effect's first note, the song's first frame
        times_g += [g[0] for g in plog.groups[len(times_g):]]
        for item in list(heard):
            t, kk, kind, what = item
            i = bisect.bisect_right(m.irq_log, t)
            if i >= len(m.irq_log):
                continue
            j = bisect.bisect_right(times_g, m.irq_log[i])
            if j >= len(plog.groups) or j >= len(pm.kinds):
                continue
            heard.remove(item)
            sound_facts['heard'] = sound_facts.get('heard', 0) + 1
            sent = plog.groups[j][1]
            if kind == 'effects':
                ctrl, arg = MUSIC['fx'][MUSIC['fx_first'][what - 1]]
                ok = sent[8] == ctrl & 15 and (
                    sent[7] == 0xB7 and sent[6] == arg if ctrl & 0x10
                    else sent[7] == 0xBE and
                    sent[0] | sent[1] << 8 == MUSIC['periods'][arg])
            else:
                ok = sum(sent[8:11]) > 0
            ok = ok and pm.kinds[j] == kind and \
                (i + 1 >= len(m.irq_log) or
                 plog.groups[j][0] < m.irq_log[i + 1])
            if not ok and bad['latency'] is None:
                bad['latency'] = (f'pass {kk}: ' + (
                    f'effect {what}' if kind == 'effects' else 'a song') +
                    ' not heard at the next interrupt')
        if bad['psg'] is None:
            n0 = len(plog.groups)
            j = next((i for i in range(checked, min(n0,
                                                    len(pm.flushes)))
                      if plog.groups[i][1] != pm.flushes[i]), None)
            if j is None and n0 != len(pm.flushes):
                j = min(n0, len(pm.flushes))
            if j is not None:
                bad['psg'] = (f'pass {k}: group {j} of {n0} '
                              f'(model {len(pm.flushes)}): ' + (
                                  f'{plog.groups[j][1]}, model '
                                  f'{pm.flushes[j]} ({pm.kinds[j]})'
                                  if j < n0 and j < len(pm.flushes)
                                  else ''))
            checked = n0
            wrong = [(r, v) for t, r, v in plog.others
                     if not (r in (11, 12, 13) and v == 0) and
                     not (r == 15 and v == JOY_PORT1)]
            if wrong and bad['psg'] is None:
                bad['psg'] = f'pass {k}: other writes {wrong[:3]}'
        # the time of the music's flushes from their interrupts
        if mode == P.MODE_MUSIC and bad['psg'] is None:
            for j in range(times_done, len(plog.groups)):
                if pm.kinds[j] != 'music':
                    continue
                tg = plog.groups[j][0]
                d = tg - m.irq_log[bisect.bisect_right(m.irq_log, tg)
                                   - 1]
                if flush_base is None:
                    flush_base = d
                if d != flush_base:
                    late.append((k, d))
            times_done = len(plog.groups)
        irq_done = len(m.irq_log)
        marks_done = len(m.marks)
        what = event_of(g0, world.game_state(), c0, world.combat_state())
        if what:
            passes.append((k, what))
        writes.clear()
        before, t_prev = vram, m.tstates
        recs.append((h(ram), h(vram), tuple(regs),
                     tuple(m.psg.regs[:14] + m.psg.regs[15:]), m.a8,
                     m.tstates))
        digest.update(f'{m.tstates} {h(ram)} {h(vram)};'.encode())
        if until and (bad.get(until) or
                      (until in RULES and rule_checks(m)[until])):
            break
    m.quiet_writes = quiet
    m.counts = counts
    m.fifths = fifths
    # no flush late: the music's next frame is always ready when the
    # interrupt comes
    if late:
        late_bad = f'pass {late[0][0]}: a flush {late[0][1]} T after ' \
                   f'the interrupt (not {flush_base}); {len(late)} late'
    if bad['psg_time'] is None:
        bad['psg_time'] = late_bad
    sound_facts['late_flushes'] = len(late)
    sound_facts['flush_after_interrupt'] = flush_base
    sound_facts['groups'] = len(plog.groups)
    sound_facts['kinds'] = {k: pm.kinds.count(k)
                            for k in ('now', 'music', 'effects')}
    if mode == P.MODE_FX:
        sound_facts['effects_asked'] = pm.fx.asked
        sound_facts['effects_refused'] = pm.fx.refused
    m.sound_facts = sound_facts
    m.plog = plog
    m.pm = pm
    facts = {'passes': len(recs), 'end_t': m.tstates,
             'digest': digest.hexdigest()[:16],
             'changes': [[c['pass'], c['room'], c['irq'], c['black']]
                         for c in changes],
             'events': {w: sum(1 for k, x in passes if x == w)
                        for w in sorted({x for k, x in passes})},
             'fifth_sprite_passes': len(fifths),
             'game': list(world.game_state()[:6]),
             'sound': sound_facts,
             'psg_digest': h(json.dumps([g[1] for g in plog.groups])
                             .encode())}
    return m, recs, bad, facts, ram, changes, passes


def rule_checks(m):
    r7 = [val for t, r, val in m.psg.log if r == 7]
    bad7 = [hex(x) for x in r7 if x & 0xC0 != 0x80]
    return {'29T': m.vdp.too_fast[:2] or None,
            'ctrl': m.ctrl_on[:2] or None,
            'rom': m.rom_written() or None,
            'r7': None if r7 and not bad7 else (bad7[:3] or 'none'),
            'psgdi': getattr(m, 'psg_on', [])[:1] or None}


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


def measures(m, recs, changes, events):
    marks = {}
    for name, t, *_ in m.marks:
        marks.setdefault(name, []).append(t)
    first = {k: v[0] for k, v in marks.items()}
    # the start-up of the tests' cartridges (milestone 0.7: the
    # variables, the sprites' images and the interrupt first, then
    # game_init, as for every game)
    order = ['psg_init', 'vdp_init', 'vars_init', 'load_shapes',
             'irq_init', 'load_glyphs', 'enter_room', 'load_zone',
             'build_room', 'show_door', 'spawn_enemies', 'hud_draw',
             'put_names', 'hero_init', 'show_combat', 'put_sprites',
             'main_loop']
    parts = {a: first[b] - first[a] for a, b in zip(order, order[1:])
             if a in first and b in first}
    parts['start-up'] = first['main_loop'] - first['init']
    ready = [r[5] for r in recs]
    change_at = {c['pass'] for c in changes}
    event_at = dict(events)

    def after(name, t0, t1):
        ts = marks.get(name, [])
        i = bisect.bisect_right(ts, t0)
        return ts[i] if i < len(ts) and ts[i] < t1 else None
    chain = ['put_sprites', 'animate_torches', 'hud_update',
             'reveal_room', 'read_input', 'check_fire', 'update_hero',
             'check_exits', 'check_door', 'check_objects',
             'update_enemies', 'check_blade', 'check_contact',
             'show_combat', 'music_due', 'frame_ready']
    frame = {c: [] for c in chain[:-1]}
    busy, busy_of = [], {w: [] for w in ('door', 'object', 'end',
                                         'touch', 'defeat', 'hit',
                                         'blow', 'state')}
    busy_reveal = []
    room_parts = {k: [] for k in ('hide', 'zone', 'build',
                                  'door_objects_enemies', 'hud',
                                  'built', 'reveal')}
    zone_change = []
    fr_t = m.vdp.frame_t
    irq = m.irq_log
    prev = first['main_loop']
    for k, t in enumerate(ready, 1):
        if k not in change_at:
            ts = [after(c, prev, t + 1) for c in chain]
            if k not in event_at and k - 1 not in change_at:
                for a, b, c in zip(ts, ts[1:], chain):
                    if a is not None and b is not None:
                        frame[c].append(b - a)
            if k - 1 in change_at and ts[3] and ts[4]:
                room_parts['reveal'].append(ts[4] - ts[3])
            i = bisect.bisect_right(irq, prev)
            if i < len(irq):
                b = t - irq[i]
                if k - 1 in change_at:
                    busy_reveal.append(b)
                else:
                    busy.append(b)
                if k in event_at:
                    busy_of[event_at[k]].append(b)
        else:
            c0 = after('change_room', prev, t)
            hz = after('hide_room', prev, t)
            en = after('enter_room', prev, t)
            lz = after('load_zone', prev, t)
            br = after('build_room', prev, t)
            sd = after('show_door', br or prev, t)
            hd = after('hud_draw', br or prev, t)
            rb = after('room_built', prev, t)
            room_parts['hide'].append(en - hz)
            room_parts['build'].append(sd - br)
            room_parts['door_objects_enemies'].append(hd - sd)
            room_parts['hud'].append(rb - hd)
            room_parts['built'].append(rb - c0)
            if lz is not None:
                room_parts['zone'].append(br - lz)
                zone_change.append(k)
        prev = t
    lines = sorted({((t - m.vdp.picture_start) % fr_t) // 228
                    for t in m.quiet_writes if t > first['main_loop']})
    # the interrupt: from isr to isr_done, with or without the
    # music worked out in it
    done, steps = marks.get('isr_done', []), marks.get('music_step', [])
    plain, inside = [], []
    for a in marks.get('isr', []):
        i = bisect.bisect_right(done, a)
        if i == len(done):
            continue
        j = bisect.bisect_right(steps, a)
        (inside if j < len(steps) and steps[j] < done[i]
         else plain).append(done[i] - a)
    # music_due at the end of a pass (not the one before a room is
    # built): to frame_ready
    ready = marks.get('frame_ready', [])
    hides = marks.get('hide_room', [])
    mains = []
    for a in marks.get('music_due', []):
        i = bisect.bisect_right(ready, a)
        j = bisect.bisect_right(hides, a)
        if i < len(ready) and not (j < len(hides) and
                                   hides[j] < ready[i]):
            mains.append(ready[i] - a)
    same = [c for c in changes if c['pass'] not in zone_change]
    other = [c for c in changes if c['pass'] in zone_change]
    return {'parts': parts,
            'interrupt': {'without_music_step': span(plain),
                          'with_music_step': span(inside),
                          'with_music_step_n': len(inside)},
            'music_due_to_frame_ready': span(mains),
            'frame_parts': {c: span(v) for c, v in frame.items()},
            'frame_t': fr_t, 'busy': span(busy),
            'busy_max_percent': round(100 * max(busy) / fr_t, 2)
            if busy else None,
            'busy_events': {k: span(v) for k, v in busy_of.items()},
            'busy_reveal': span(busy_reveal),
            'busy_reveal_max_percent': round(
                100 * max(busy_reveal) / fr_t, 2) if busy_reveal
            else None,
            'vram_lines': [lines[0], lines[-1]] if lines else None,
            'change_parts': {k: span(v) for k, v in room_parts.items()},
            'changes_same_zone': {
                'n': len(same), 'irq': span([c['irq'] for c in same]),
                'black': span([c['black'] for c in same])},
            'changes_new_zone': {
                'n': len(other), 'irq': span([c['irq'] for c in other]),
                'black': span([c['black'] for c in other])}}


# -- the data -------------------------------------------------------------

def data_check(rom, sym):
    """The rooms' records and door_table read back from the cartridge
    = the room files: door, objects (kind, column, row), enemies
    (kind, column, row, flags), the open tiles of every door (column,
    row, the posts of the portal)."""
    def byte(a):
        return rom[a - 0x4000]

    def word(a):
        return byte(a) | byte(a + 1) << 8
    problems, n_obj, n_door, n_en = [], 0, 0, 0
    for n, name in msx_model.rooms().items():
        room = dungeon.load_room(name)
        rec = word(sym['room_table'] + 2 * n)
        door = dungeon.DOOR_NUMBERS[room.door] if room.door else 0
        if byte(rec + 1) != door:
            problems.append(f'room {n}: door {byte(rec + 1)}')
        for s in range(2):
            got = tuple(byte(rec + 2 + 4 * s + i) for i in range(3))
            if s < len(room.objects):
                kind, letter, c, r = room.objects[s]
                want = (room.code(kind, letter), c, r)
                n_obj += 1
            else:
                want = (0, 0, 0)
            if got != want:
                problems.append(f'room {n} slot {s}: {got}, not {want}')
        for s in range(W.MAX_ENEMIES):
            got = tuple(byte(rec + 10 + 4 * s + i) for i in range(4))
            if s < len(room.enemies):
                kind, c, r, axis, fast = room.enemies[s]
                want = (dungeon.ENEMIES[kind], c, r,
                        (dungeon.AXES[axis] if axis else 0) |
                        (dungeon.FAST if fast else 0))
                n_en += 1
            else:
                want = (0, 0, 0, 0)
            if got != want:
                problems.append(f'room {n} enemy {s}: {got}, not '
                                f'{want}')
        if door:
            n_door += 1
            tiles = dungeon.door_tiles(room)[0]
            left = min(c for c, r in tiles)
            want = [(c, r, (0b0101 if c == left else 0b1010)
                     if door == W.PORTAL and r < 2 else 0)
                    for c, r in tiles]
            a = word(sym['door_table'] + 2 * (door - 1))
            got = []
            while byte(a) != 0xFF:
                got.append((byte(a), byte(a + 1), byte(a + 3)))
                a += 4
            if got != want:
                problems.append(f'door {door}: {got}, not {want}')
    return problems, n_obj, n_door, n_en


def sprite_bytes(drawing):
    """A 16 x 16 drawing as the TMS9918A keeps a sprite: the left
    eight columns of the 16 rows, then the right eight."""
    def byte(r, c0):
        return int(''.join('1' if ch == '#' else '0'
                           for ch in drawing[r][c0:c0 + 8]), 2)
    return [byte(r, 0) for r in range(16)] + \
        [byte(r, 8) for r in range(16)]


def combat_images_check(vram, rom, sym):
    """The nine images of the combat in the sprite shapes of the VRAM
    (from shape 64) = art_pieces.COMBAT_FRAMES; their colours in
    image_ink = msx_model.COMBAT_INKS. Returns (problems, a picture
    of them as the cartridge has them, 8 times bigger)."""
    problems = []
    base = 0x3800 + W.COMBAT_SHAPE * 8
    inks = [rom[sym['image_ink'] - 0x4000 + i] for i in range(9)]
    if tuple(inks) != msx_model.COMBAT_INKS:
        problems.append(f'colours {inks}')
    pal = vram2png.palette(50)
    scale, gap = 8, 8
    pic = [[(40, 40, 40)] * (9 * (16 * scale + gap) + gap)
           for _ in range(16 * scale + 2 * gap)]
    for n, drawing in enumerate(msx_model.art_pieces.COMBAT_FRAMES):
        got = list(vram[base + 32 * n:base + 32 * n + 32])
        if got != sprite_bytes(drawing):
            problems.append(f'image {n}')
        x0 = gap + n * (16 * scale + gap)
        for y in range(16):
            for x in range(16):
                b = got[y + (16 if x >= 8 else 0)] >> (7 - (x & 7)) & 1
                c = tuple(pal[inks[n]] if b else pal[1])
                for yy in range(scale):
                    row = pic[gap + y * scale + yy]
                    row[x0 + x * scale:x0 + x * scale + scale] = \
                        [c] * scale
    return problems, pic


# -- openMSX --------------------------------------------------------------

def emu_compare(recs, emu):
    """recs = openMSX's frames (a list, or a generator reading them
    from the file one at a time)."""
    n = 0
    for k, e in enumerate(emu):
        n += 1
        if k >= len(recs):
            continue
        b = recs[k]
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
    if len(recs) != n:
        return f'{len(recs)} passes against {n}'
    return None


def emu_run(openmsx, rom_path, sym, mname, frames, rd, seed=None,
            shots=(), script=None, pokes=None, lazy=False,
            psg_log=False, wav=None):
    machine, hz = MACHINES[mname]
    rom = Path(rom_path).read_bytes()
    joy_read = openmsx_run.find_in(rom, 0x4000, sym['in_joy'],
                                   (0xDB, 0xA2)) + 2
    return openmsx_run.run(openmsx, rom_path, machine, sym, frames, rd,
                           seed=seed, shots=shots,
                           inputs=inputs_of(script) if script else None,
                           pokes=pokes_of(pokes or {}, sym),
                           joy_read=joy_read, lazy=lazy,
                           psg_log=psg_log, wav=wav,
                           max_seconds=round(10 + frames / 30, 2))


def emu_irq_same(m, emu):
    k = min(len(emu['irq']), len(m.irq_log))
    return k > 0 and emu['irq'][:k] == m.irq_log[:k], k


def state_of(rd, sym, mname):
    hz = MACHINES[mname][1]
    return openmsx_run.cbios_state(rd, sym['init'], hz,
                                   msxsim.LINES[hz] * msxsim.LINE_T)


CALIBRATION_FRAMES = 300


def calibrate(state, rom, sym, cb, script, start, emu, pokes=None):
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
        m, recs, bad, fr, last, ch, ev = bench_walk(
            rom, sym, st, cb, None, script[:n], start, pokes)
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


def data(checks, facts, cdir, png):
    rom, sym = rom_files(GAME)
    problems, n_obj, n_door, n_en = data_check(rom, sym)
    facts['data'] = {'objects': n_obj, 'doors': n_door, 'enemies': n_en}
    checks.add('data: the objects, doors and enemies in the cartridge '
               '= the room files', not problems and n_obj == 20 and
               n_door == 4 and n_en == 34, problems[0] if problems else
               f'{n_obj} objects, {n_door} doors, {n_en} enemies')
    state = json.loads((BUILD / 'state_eu.json').read_text())
    m = msxsim.MSX(rom, state, cbios_roms(cdir, 'eu'))
    m.run_to(sym['frame_ready'], max_t=40 * m.vdp.frame_t)
    problems, pic = combat_images_check(bytes(m.vdp.vram), rom, sym)
    (png / 'combat_images.png').write_bytes(png_rgb(pic))
    facts['data']['combat_images'] = h(m.vdp.vram[0x3A00:0x3B20])
    checks.add('data: the nine images of the combat in the VRAM after '
               'INIT = art_pieces.COMBAT_FRAMES, their colours = '
               'msx_model.COMBAT_INKS', not problems,
               problems[0] if problems else 'png/combat_images.png')


def flicker(script, pokes, room):
    """The model's game: the pictures in which the VDP leaves out a
    figure on a line, and the longest run of pictures in which the
    same figure is cut."""
    world = W.World(room)
    total, runs, cur = 0, {}, {}
    for k, (bits, keys, joy) in enumerate(script, 1):
        for name, v in pokes.get(k, ()):
            poke_model(world, name, v)
        world.update(bits)
        c = {world.picture_tags[i] for i in W.cut(world.picture)}
        total += bool(c)
        for t in list(cur):
            if t not in c:
                runs[t] = max(runs.get(t, 0), cur.pop(t))
        for t in c:
            cur[t] = cur.get(t, 0) + 1
    for t, n in cur.items():
        runs[t] = max(runs.get(t, 0), n)
    return {'pictures_cut': total, 'longest_run': max(runs.values())
            if runs else 0, 'runs': dict(sorted(runs.items()))}


def end_pass(script, pokes, room=GAME_ROOM):
    """The pass in which the model's game ends."""
    model = W.World(room)
    for k, (bits, keys, joy) in enumerate(script, 1):
        for name, v in pokes.get(k, ()):
            poke_model(model, name, v)
        model.update(bits)
        if model.ended:
            return k
    return None


def model_end(script, pokes, room):
    model = W.World(room)
    for k, (bits, keys, joy) in enumerate(script, 1):
        for name, v in pokes.get(k, ()):
            poke_model(model, name, v)
        model.update(bits)
    return model


def psg_writes_same(m, r):
    """openMSX's writes to the PSG = the bench's: the same registers
    and values, in the same order, at the same T-states (openMSX
    gives the start of the instruction, the bench its I/O cycle: 9
    T-states later for OUT (n),A, 15 for OUTI)."""
    b, o = m.psg.log, r['psg_writes']
    if len(b) != len(o):
        return False, f'{len(b)} writes in the bench, {len(o)} in openMSX'
    for i, (x, y) in enumerate(zip(b, o)):
        if x[1:] != y[1:] or x[0] - y[0] not in (9, 15):
            return False, f'write {i}: bench {x}, openMSX {y}'
    return True, f'{len(b)} writes'


def walk_machine(openmsx, cdir, checks, f, mname, tag, script, pokes,
                 seeds, label, mode=P.MODE_MUSIC, wav=None):
    """The script in the bench (each seed) and, with openMSX, there
    too: the checks of every pass; the runs of the bench. wav: (file,
    pass): openMSX's sound recorded from that pass (seed None)."""
    game_rom = GAMES[mode]
    rom, sym = rom_files(game_rom)
    state = json.loads((BUILD / f'state_{mname}.json').read_text())
    cb = cbios_roms(cdir, mname)
    runs, lasts = {}, {}
    label = f'{label} {MODE_NAMES[mode]}'
    for seed in seeds:
        n = len(script) if seed is None else SEED_PASSES
        m, recs, bad, fr, last, ch, ev = bench_walk(
            rom, sym, state, cb, seed, script[:n], GAME_ROOM, pokes,
            watch=seed is None, mode=mode)
        runs[seed] = (m, recs, ch, ev)
        lasts[seed] = last
        f[f'seed_{seed}'] = fr
        walk_checks(checks, f'{tag} {label} seed {seed}', bad, n)
        rules = rule_checks(m)
        checks.add(f'{tag} {label} seed {seed}: no VRAM access closer '
                   f'than {msxsim.VRAM_GAP} T in the picture, '
                   'VDP_CTRL with interrupts off, no write to ROM, '
                   'PSG R7 10xxxxxx, the PSG with interrupts off',
                   not any(rules.values()), str(rules))
    if openmsx:
        for seed in seeds:
            m, recs = runs[seed][0], runs[seed][1]
            n = len(recs)
            rd = RUNS / f'{mname}_{label.replace(" ", "_")}_seed_{seed}'
            rec = wav if seed is None else None
            r = emu_run(openmsx, BUILD / f'{game_rom}.rom', sym, mname,
                        n, rd, seed=seed, script=script[:n],
                        pokes=pokes, lazy=True, psg_log=True, wav=rec)
            bad = emu_compare(recs, r['frames'])
            same, k = emu_irq_same(m, r)
            psame, pdet = psg_writes_same(m, r)
            checks.add(f'{tag} {label} seed {seed}: bench = openMSX, '
                       'every pass, interrupts at the same T-states, '
                       'every write to the PSG the same, at the same '
                       'T-state, nothing dropped, no PSG port A as '
                       'output',
                       bad is None and same and k == len(m.irq_log) and
                       psame and not r['too_fast'] and
                       not r['psg_directions'],
                       bad or (f'{len(recs)} passes, {k} interrupts, '
                               if psame else '') + pdet)
            if rec:
                t0 = r['wav_from'] or 0
                fg = [x for x in frame_groups(r) if x[0] >= t0]
                samples, rate = read_wav(rec[0])
                hd = heard(samples, rate, [x[0] for x in fg], t0,
                           [x[1] for x in fg])
                f['openmsx_sound'] = dict(hd, file=Path(rec[0]).name)
                checks.add(f'{tag} {label}: openMSX\'s sound from pass '
                           f'{rec[1]} ({Path(rec[0]).name}): the '
                           'loudness of every frame follows the '
                           'registers', hd['loudness_correlation'] >=
                           0.75, str(hd))
            del r
    return runs, lasts


def game(openmsx, cdir, checks, facts, args):
    rom, sym = rom_files(GAME)
    script, pokes = game_script()
    model = model_end(script, pokes, GAME_ROOM)
    end = model.game_state()
    checks.add('the model: the whole game planned, VICTORY, 10400 '
               'points, three seals, no key left, the four doors open, '
               'energy 6', end[:6] == (0, 3, 10400, 6, 15, W.ENDED_WON),
               f'{len(script)} passes; {end[:6]}')
    fl = flicker(script, pokes, GAME_ROOM)
    facts['sprites'] = fl
    for mname, (machine, hz) in MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        f = facts.setdefault(f'game_{mname}', {})
        if 'music' in GAME_RUNS:
            state_file = BUILD / f'state_{mname}.json'
            if openmsx:
                rd = RUNS / f'{mname}_state'
                cal = script[:CALIBRATION_FRAMES]
                emu = emu_run(openmsx, BUILD / f'{GAME}.rom', sym, mname,
                              len(cal), rd, script=cal, pokes=pokes)
                state, d = calibrate(state_of(rd, sym, mname), rom, sym,
                                     cbios_roms(cdir, mname), cal, GAME_ROOM,
                                     emu, pokes)
                checks.add(f'{tag}: the first interrupt after INIT fitted '
                           f'to openMSX ({len(cal)} passes)', d is not None,
                           f'{d} T-states before the probe\'s bound')
                del emu
                if state_file.exists() and not args.update_state:
                    # vbl_seen, the probe's times from the power on,
                    # aside: C-BIOS's start takes longer or shorter
                    # with the cartridge's bytes (milestone 0.7)
                    kept = json.loads(state_file.read_text())
                    same = [k for k in kept if k != 'vbl_seen' and
                            kept[k] != state.get(k)]
                    checks.add(f'{tag}: state at INIT = the one kept '
                               '(but the times of the probe from the '
                               'power on)', not same,
                               'game/build/' + state_file.name +
                               (f': {same}' if same else ''))
                else:
                    state_file.write_text(json.dumps(state) + '\n')
            runs, lasts = walk_machine(
                openmsx, cdir, checks, f, mname, tag, script, pokes, SEEDS,
                'game')
            outside, depth = ram_check(lasts)
            f['stack_depth'] = depth
            checks.add(f'{tag}: RAM written only in the areas of vars.asm '
                       'and the stack (seeds 1, 2)',
                       not outside and 0 < depth <= STACK_ROOM,
                       f'stack {depth} bytes' + (
                           f'; outside {[hex(a) for a in outside[:4]]}'
                           if outside else ''))
            m0, recs0, ch0, ev0 = runs[None]
            mea = measures(m0, recs0, ch0, ev0)
            f['measures'] = mea
            ends = [k for k, w in ev0 if w == 'end']
            count = {w: sum(1 for k, x in ev0 if x == w)
                     for w in ('door', 'object', 'blow', 'hit', 'defeat',
                               'touch')}
            checks.add(f'{tag}: VICTORY at pass {ends[0] if ends else None}'
                       f', {len(ch0)} changes of room = the model\'s',
                       ends and len(ch0) == model.changes,
                       ', '.join(f'{w} {n}' for w, n in count.items()))
            sf = m0.sound_facts
            checks.add(f'{tag}: the sounds of the game (MUSIC): every one '
                       'asked as the model asks it; the theme, then the '
                       'piece of the victory (to its end: the sessions)',
                       sf['calls'].get('won') == 1 and
                       m0.pm.player is not None and
                       m0.pm.player.voices[0].order_list ==
                       MUSIC['songs']['won']['orders'][0],
                       f"{sf['calls']}; groups {sf['groups']}")
            checks.add(f'{tag}: a pass without a change within its frame, '
                       'its VRAM written out of the picture (lines 192 and '
                       'after)',
                       mea['busy_max_percent'] < 100 and
                       mea['busy_reveal_max_percent'] < 100 and
                       mea['vram_lines']
                       and mea['vram_lines'][0] >= 192 and
                       mea['vram_lines'][1] < msxsim.LINES[hz],
                       f"busy {mea['busy']} T (showing a room "
                       f"{mea['busy_reveal']}) of {mea['frame_t']}; lines "
                       f"{mea['vram_lines']}")
            checks.add(f'{tag}: pictures with a fifth sprite on a line '
                       '(the order turns): the same figure cut at most 2 '
                       'pictures in a row',
                       len(m0.fifths) == fl['pictures_cut'] > 0 and
                       fl['longest_run'] <= 2,
                       f"{len(m0.fifths)} passes with 5S, {fl}")
        for mode, run in ((P.MODE_FX, 'fx'), (P.MODE_SILENT, 'silent')):
            if run not in GAME_RUNS:
                continue
            fm = facts.setdefault(f'game_{mname}_{GAMES[mode]}', {})
            walk_machine(openmsx if mode == P.MODE_FX else None, cdir,
                         checks, fm, mname, tag, script, pokes, (None,),
                         'game', mode)


def defeat(openmsx, cdir, checks, facts):
    """GAME OVER: energy 2 put in RAM, down to the skeleton of the
    Crossroads; then input that changes nothing."""
    script, pokes = defeat_script()
    model = model_end(script, pokes, GAME_ROOM)
    checks.add('the model: GAME OVER in the Crossroads, energy 0',
               model.ended == W.ENDED_LOST and model.energy == 0 and
               model.room == 5, f'{len(script)} passes')
    for mname, (machine, hz) in MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        f = facts.setdefault(f'defeat_{mname}', {})
        for mode in (P.MODE_FX, P.MODE_SILENT):
            fm = facts.setdefault(f'defeat_{mname}_{GAMES[mode]}', {})
            walk_machine(None, cdir, checks, fm, mname, tag, script,
                         pokes, (None,), 'defeat', mode)
        runs, lasts = walk_machine(
            openmsx, cdir, checks, f, mname, tag, script, pokes, (None,),
            'defeat')
        m0, recs0, ch0, ev0 = runs[None]
        ends = [k for k, w in ev0 if w == 'end']
        after = len(recs0) - ends[0] if ends else 0
        f['end_pass'] = ends[0] if ends else None
        checks.add(f'{tag}: GAME OVER at pass '
                   f'{ends[0] if ends else None}, then {after} passes '
                   'of input with the room still, every one = the model '
                   '(nothing moves)',
                   ends and after >= AFTER_DEFEAT and
                   ev0[-1][0] == ends[0],
                   f'{len(ev0)} passes that change the game')
        pm = m0.pm
        checks.add(f'{tag}: the sounds of the defeat (MUSIC): the theme, '
                   'then the piece of the defeat (to its end: the '
                   'sessions)',
                   m0.sound_facts['calls'].get('lost') == 1 and
                   pm.player is not None and
                   pm.player.voices[0].order_list ==
                   MUSIC['songs']['lost']['orders'][0],
                   f"{m0.sound_facts['calls']}")


def shots(openmsx, cdir, checks, facts, png):
    """Five moments of the game, still (the explorer standing in the
    Moss Gate, a fight frozen by game_ended put in RAM, GAME OVER):
    openMSX's screenshots = the model."""
    for mname, (machine, hz) in MACHINES.items():
        state = json.loads((BUILD / f'state_{mname}.json').read_text())
        cb = cbios_roms(cdir, mname)
        bad, hashes, imgs = [], {}, []
        for pn, (rname, start, steps) in enumerate(SHOT_PLANS, 1):
            # the passes of every stand of 24 or more
            world = W.World(start)
            stands, script, pokes = [], [], {}
            for st in steps:
                s, p = plan_steps(world, [st])
                for k, lst in p.items():
                    pokes.setdefault(len(script) + k, []).extend(lst)
                if st[0] == 'stand' and st[1] >= 24:
                    stands.append(range(len(script) + 1,
                                        len(script) + st[1] + 1))
                script += s
            script = script_of(runs_of(script), SOURCES)
            rom, sym = rom_files(rname)
            m, recs, b, fr, last, ch, ev = bench_walk(
                rom, sym, state, cb, None, script, start, pokes)
            b.update(rule_checks(m))
            bad += [f'{rname} bench: {w}: {e}' for w, e in b.items() if e]
            counts = m.counts
            world = W.World(start)
            want, ks = {}, []
            for k, (bits, keys, joy) in enumerate(script, 1):
                for name, v in pokes.get(k, ()):
                    poke_model(world, name, v)
                world.update(bits)
                st = next((r for r in stands if k in r), None)
                if st and k - st[0] >= 10 and k + 2 <= st[-1] and \
                        counts[k - 1] % 8 in (4, 5) and \
                        not any(x in st for x in ks):
                    ks.append(k)
                    want[k] = (world.room, model_screen(world,
                                                        counts[k - 1]))
            rd = RUNS / f'{mname}_shots_{pn}'
            emu_run(openmsx, BUILD / f'{rname}.rom', sym, mname,
                    len(script), rd, shots=ks, script=script,
                    pokes=pokes)
            for i, k in enumerate(ks):
                room, rows = want[k]
                for kk in (k, k + 2):
                    p = rd / f'shot_{kk}.png'
                    if not p.exists():
                        bad.append(f'{rname} shot_{kk}.png missing')
                        continue
                    e = shot_ok(p, rows, hz)
                    if e:
                        bad.append(f'{rname} {e}')
                    hashes[f'{pn}_{rname}_{kk}'] = shot_hash(p)
                p = rd / f'shot_{k}.png'
                if p.exists():
                    dst = png / (f'shot{pn}_{i + 1}_room{room:02}_'
                                 f'{hz}hz.png')
                    shutil.copy(p, dst)
                    imgs.append(vram2png.read_png_rgb(dst))
        facts.setdefault('openmsx', {})[f'shots_{mname}'] = hashes
        checks.add(f'{mname} ({hz} Hz): {len(imgs)} screenshots (the '
                   'portal open, VICTORY, two fights, the skeleton hit in '
                   'red, GAME OVER) = the model, every pixel',
                   not bad and len(imgs) == SHOTS_WANTED, bad[0] if bad
                   else f'{len(hashes)} screenshots')
        if imgs:
            (png / f'sheet_game_{hz}hz.png').write_bytes(
                png_rgb(sheet(imgs, 3), 1))


def rooms(openmsx, cdir, checks, facts):
    names = msx_model.rooms()
    for mname, (machine, hz) in MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        cb = cbios_roms(cdir, mname)
        kept = json.loads((BUILD / f'state_{mname}.json').read_text())
        probs, emu_probs, n_changes, n_events = [], [], 0, 0
        cut = []
        for n, name in sorted(names.items()):
            rname = f'rooms/{n:02}'
            rom, sym = rom_files(rname)
            script = room_script(n)
            if len(script) < ROOM_FRAMES:
                cut.append(f'room {n}: {len(script)}')
            state, emu = kept, None
            if openmsx and mname == 'eu':
                rd = RUNS / f'room_{n:02}'
                emu = emu_run(openmsx, BUILD / f'{rname}.rom', sym, mname,
                              len(script), rd, script=script)
                state, d = calibrate(state_of(rd, sym, mname), rom, sym,
                                     cb, script, n, emu)
            m, recs, bad, fr, last, ch, ev = bench_walk(
                rom, sym, state, cb, None, script, n)
            n_changes += len(ch)
            n_events += len(ev)
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
                   f'({AFTER_END} after an end; {n_changes} changes of '
                   f'room, {n_events} passes that change the game or '
                   'fight): input, explorer, game, combat, sprites, '
                   'screen, solid map, hidden changes, rules',
                   not probs, probs[0] if probs else
                   'cut: ' + ', '.join(cut) if cut else '')
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


# -- the sound -------------------------------------------------------------

LOOPS = {50: 3072, 60: 3584}    # frames of the theme: 32 bars
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A',
              'A#', 'B']
FX_GAP = 25                     # passes of silence between effects
E6 = 76                         # the fanfare's long note
AY_LEVELS = [0.0, 0.00999, 0.01445, 0.02106, 0.03070, 0.04555,
             0.06450, 0.10736, 0.12659, 0.20499, 0.29221, 0.37284,
             0.49253, 0.63532, 0.80558, 1.0]


def note_name(n):
    return f'{NOTE_NAMES[n % 12]}{n // 12}'


def decode_pattern(data, instruments):
    tokens, length = [], None
    for b in data:
        if b == 0xFF:
            break
        if b >= 0xC0:
            tokens.append('@' + instruments[b - 0xC0])
        elif b >= 0x80:
            length = b - 0x7F
        elif b == 0x60:
            tokens.append(f'r/{length}')
        else:
            tokens.append(f'{note_name(b)}/{length}')
    return tokens


def decode_order(data, names):
    items, i = [], 0
    while True:
        b = data[i]
        if b == 0xFF:
            target = data[i + 1]
            if target == i - 1 and names[data[i - 1]] == 'silence':
                items[-1] = 'stop'
            elif target != 0:
                items.append(f'loop {target}')
            return items
        items.append(f't{b - 0xA0:+d}' if b >= 0x80 else names[b])
        i += 1


def music_read_back(rom, sym):
    """The music's tables read from the cartridge, in the form of
    music.json."""
    def byte(a):
        return rom[a - 0x4000]

    def word(a):
        return byte(a) | byte(a + 1) << 8
    n_ins = len(MUSIC['instruments'])
    out = {'periods': [word(sym['note_period'] + 2 * i)
                       for i in range(96)]}
    ins = []
    for i in range(n_ins):
        ins.append({'wave': byte(sym['ins_wave'] + i),
                    'env': byte(sym['ins_env'] + i),
                    'rel': byte(sym['ins_rel'] + i),
                    'vib': byte(sym['ins_vib'] + i),
                    'rel_start': [byte(sym['rel_start'] + 16 * i + v)
                                  for v in range(16)]})
    out['instruments'] = ins
    out['env_data'] = [byte(sym['env_data'] + i)
                       for i in range(len(MUSIC['env_data']))]
    out['vibrato'] = [(byte(sym['vib_offset'] + i) ^ 0x80) - 0x80
                      for i in range(8)]
    out['waves'] = [[byte(sym['wave_ctrl'] + i), byte(sym['wave_arg'] + i)]
                    for i in range(len(MUSIC['waves']))]
    pats = []
    for i in range(len(MUSIC['pattern_names'])):
        a, data = word(sym['pat_addr'] + 2 * i), []
        while True:
            data.append(byte(a))
            a += 1
            if data[-1] == 0xFF:
                break
        pats.append(data)
    out['patterns'] = pats
    songs = {}
    for s, name in enumerate(MUSIC['song_numbers']):
        lists = []
        for v in range(3):
            a, data = word(sym['song_orders'] + 6 * s + 2 * v), []
            while True:
                data.append(byte(a))
                a += 1
                if data[-1] == 0xFF:
                    data.append(byte(a))
                    break
            lists.append(data)
        songs[name] = lists
    out['orders'] = songs
    out['sfx_priority'] = [byte(sym['sfx_priority'] + i) for i in range(8)]
    out['fx_first'] = [byte(sym['fx_first'] + i) for i in range(8)]
    out['fx'] = [[byte(sym['fx_data'] + 2 * i), byte(sym['fx_data']
                                                     + 2 * i + 1)]
                 for i in range(len(MUSIC['fx']))]
    return out


def music_check(rom, sym):
    """The music in the cartridge = music.json; read back = the C64's
    score (patterns, order lists), every note played with the PSG's
    period; the effects = c64/sfx.py."""
    sys.path.insert(0, str(ROOT / 'game' / 'assets'))
    sys.path.insert(0, str(ROOT / 'game' / 'assets' / 'c64'))
    import ay_music
    import score
    import sfx
    got = music_read_back(rom, sym)
    want = {'periods': MUSIC['periods'],
            'instruments': [{k: i[k] for k in ('wave', 'env', 'rel',
                                                'vib', 'rel_start')}
                            for i in MUSIC['instruments']],
            'env_data': MUSIC['env_data'], 'vibrato': MUSIC['vibrato'],
            'waves': [list(w) for w in MUSIC['waves']],
            'patterns': MUSIC['patterns'],
            'orders': {s: v['orders'] for s, v in MUSIC['songs'].items()},
            'sfx_priority': MUSIC['sfx_priority'],
            'fx_first': MUSIC['fx_first'], 'fx': MUSIC['fx']}
    differ = [k for k in want if got[k] != want[k]]
    instruments = [i['name'] for i in MUSIC['instruments']]
    names = MUSIC['pattern_names']
    bad = []
    for n, data in zip(names, got['patterns']):
        if decode_pattern(data, instruments) != score.PATTERNS[n].split():
            bad.append(f'pattern {n}')
    for song, lists in got['orders'].items():
        for v, data in enumerate(lists):
            if decode_order(data, names) != score.SONGS[song]['orders'][v]:
                bad.append(f'order {song} {v + 1}')
    played = set()
    for song in MUSIC['songs']:
        pl = P.PSGPlayer(MUSIC, song, 50)
        for _ in range(MUSIC['songs'][song]['steps'] * MUSIC['speed_50']):
            pl.frame()
            for v in pl.voices:
                if v.ctrl == 1:
                    played.add(v.arg)
    clock = CLOCK / 2
    wrong = [n for n in sorted(played) if got['periods'][n] !=
             round(clock / (16 * 440 * 2 ** ((n - 57) / 12)))
             or not 0 < got['periods'][n] < 4096]
    # the effects, read back = the C64's (c64/sfx.py): the notes from
    # the first frame (the C64's frame of the gate off left out), the
    # release down to 0 giving up the priority from its second frame;
    # the priorities
    data, first = got['fx'], got['fx_first']
    ay_music.AY_CLOCK = clock
    fx_ok, frames = True, {}
    for e, (name, effect) in enumerate(sfx.EFFECTS.items()):
        notes = []
        for item in effect['frames'].split(','):
            w, note = item.split()
            noise = int(w, 16) & 0x80 != 0
            num = ay_music.note_number(note)
            notes.append((noise, ay_music.noise_period(num) if noise
                          else num))
        pos, entries = first[e], []
        while data[pos][0] != 0xFF:
            entries.append(tuple(data[pos]))
            pos += 1
        body = entries[:len(notes)]     # from the first note
        ok = [(c & 0x10 != 0, a) for c, a in body] == notes
        ok = ok and all(c & 15 for c, _ in body)
        rel = entries[len(notes):]
        vols = [c & 15 for c, _ in rel]
        ok = ok and vols and vols[-1] == 0 and \
            all(a >= b for a, b in zip(vols, vols[1:]))
        ok = ok and not rel[0][0] & 0x20 and \
            all(c & 0x20 for c, _ in rel[1:])
        ok = ok and all(a == notes[-1][1] for _, a in rel)
        fx_ok = fx_ok and ok and \
            got['sfx_priority'][e] == effect['priority']
        frames[name] = len(entries)
    return {'differ': differ, 'score': bad, 'periods_wrong': wrong,
            'notes_played': [note_name(min(played)),
                             note_name(max(played))],
            'effects_read_back': fx_ok, 'effect_frames': frames,
            'bytes': sym['music_end'] - sym['note_period']}


def audible(regs):
    """What can be heard: the mixer, the period of every channel
    whose tone is on, the volumes, the noise period if any noise is
    on."""
    out = [regs[7]]
    for c in range(3):
        if not (regs[7] >> c) & 1:
            out.append(regs[2 * c] | regs[2 * c + 1] << 8)
        out.append(regs[8 + c])
    if regs[7] & 0x38 != 0x38:
        out.append(regs[6])
    return out


def isr_costs(m):
    """T-states from isr to isr_done: without and with music_step
    inside (the bench's marks)."""
    marks = {}
    for name, t, *_ in m.marks:
        marks.setdefault(name, []).append(t)
    done, steps = marks.get('isr_done', []), marks.get('music_step', [])
    plain, inside = [], []
    for a in marks.get('isr', []):
        i = bisect.bisect_right(done, a)
        if i == len(done):
            continue
        j = bisect.bisect_right(steps, a)
        (inside if j < len(steps) and steps[j] < done[i]
         else plain).append(done[i] - a)
    mains = []
    ready = marks.get('frame_ready', [])
    for a in marks.get('music_due', []):
        i = bisect.bisect_right(ready, a)
        if i < len(ready):
            mains.append(ready[i] - a)
    return {'interrupt': span(plain), 'interrupt_with_music_step':
            span(inside), 'music_due': span(mains)}


def theme_bench(cdir, mname, hz):
    """The theme on the bench, standing in the Moss Gate: a loop and
    120 frames more, every pass checked as in the game."""
    rom, sym = rom_files(GAME)
    state = json.loads((BUILD / f'state_{mname}.json').read_text())
    n = LOOPS[hz] + 120
    script = [(0, (), ())] * n
    m, recs, bad, fr, last, ch, ev = bench_walk(
        rom, sym, state, cbios_roms(cdir, mname), None, script,
        GAME_ROOM, watch=True)
    music = [g for g, k in zip(m.plog.groups, m.pm.kinds)
             if k == 'music']
    loop = LOOPS[hz]
    repeats = len(music) > loop + 100 and all(
        audible(music[k][1]) == audible(music[k + loop][1])
        for k in range(1, len(music) - loop))
    return m, bad, repeats, n


def effects_bench(cdir, mname, hz):
    """SOUND FX: the eight effects one after another, each asked as
    sound_effect asks it (sfx_next, and a priority above all), FX_GAP
    passes apart: the groups sent = the model. Returns (problems,
    frames of each effect, the pokes {pass: [(name, value)]}, the
    passes)."""
    rom, sym = rom_files(GAMES[P.MODE_FX])
    state = json.loads((BUILD / f'state_{mname}.json').read_text())
    m = msxsim.MSX(rom, state, cbios_roms(cdir, mname))
    pm = P.PSGMachine(MUSIC, hz)
    pm.set_audio(P.MODE_FX)
    pokes, k = {}, FX_GAP
    for n in range(1, 9):
        pokes[k] = [('sfx_next', n), ('sfx_prio', 9)]
        k += sum(1 for _ in fx_entries(n)) + 1 + FX_GAP
    passes = k
    plog = PSGLog(m.psg)
    irq_done, frames, bad, playing = 0, {}, None, None
    for k in range(1, passes + 1):
        for name, v in pokes.get(k, ()):
            m.mem[sym[name]] = v
        if pokes.get(k):
            pm.fx.next, pm.fx.prio = pokes[k][0][1], 9
            playing = (pokes[k][0][1], k)
        m.run_to(sym['frame_ready'], max_t=40 * m.vdp.frame_t)
        for _ in m.irq_log[irq_done:]:
            pm.interrupt()
        irq_done = len(m.irq_log)
        if playing and m.mem[sym['sfx_pos']] == 0 and \
                m.mem[sym['sfx_next']] == 0:
            # the interrupts from the request to the end
            frames[playing[0]] = k - playing[1] + 1
            playing = None
    plog.update()
    if [g[1] for g in plog.groups] != pm.flushes:
        bad = next((f'group {i}: {g[1]}, model {f}' for i, (g, f) in
                    enumerate(zip(plog.groups, pm.flushes)) if g[1] != f),
                   f'{len(plog.groups)} groups, model {len(pm.flushes)}')
    return bad, frames, pokes, passes, m, pm


def fx_entries(n):
    pos = MUSIC['fx_first'][n - 1]
    while MUSIC['fx'][pos][0] != 0xFF:
        yield MUSIC['fx'][pos]
        pos += 1


def read_wav(path):
    w = wave.open(str(path))
    rate = w.getframerate()
    a = array.array('h')
    a.frombytes(w.readframes(w.getnframes()))
    if sys.byteorder == 'big':
        a.byteswap()
    return a, rate


def goertzel(x, f, rate):
    w = 2 * math.pi * f / rate
    c = 2 * math.cos(w)
    s1 = s2 = 0.0
    for v in x:
        s0 = v + c * s1 - s2
        s2, s1 = s1, s0
    return s1 * s1 + s2 * s2 - c * s1 * s2


def frames_audio(samples, rate, starts, t0):
    """The samples of each frame: from one flush to the next (times
    in T-states from INIT; t0: when the recording started)."""
    out = []
    for a, b in zip(starts, starts[1:]):
        i = int((a - t0) * rate / CLOCK)
        j = int((b - t0) * rate / CLOCK)
        out.append(samples[max(0, i):max(0, j)])
    return out


def rms(x):
    if not x:
        return 0.0
    mean = sum(x) / len(x)
    return math.sqrt(sum((v - mean) ** 2 for v in x) / len(x))


def corr(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((x - mb) ** 2 for x in b))
    if not sa or not sb:
        return 0.0
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def loudness(regs):
    total = 0.0
    for c in range(3):
        if not (regs[7] >> c) & 1 or not (regs[7] >> (c + 3)) & 1:
            total += AY_LEVELS[regs[8 + c]] ** 2
    return math.sqrt(total)


def note_runs(groups, chan, minlen, tol):
    """Steady notes of a channel: (first, end, period) where the tone
    is on, loud (12-15) and the period moves at most tol."""
    out, start, cur = [], None, None
    for k in range(len(groups) + 1):
        on = False
        if k < len(groups):
            r = groups[k]
            on = not (r[7] >> chan) & 1 and r[8 + chan] >= 12
            per = r[2 * chan] | r[2 * chan + 1] << 8
        if not (on and cur is not None and abs(per - cur) <= tol):
            if cur is not None and k - start >= minlen:
                out.append((start, k, cur))
            start, cur = (k, per) if on else (None, None)
    return out


def note_found(x, rate, period, harmonics):
    """The note's energy (at its harmonics) at least twice that of
    every other semitone within five."""
    f = CLOCK / 2 / (16 * period)

    def energy(g):
        return sum(goertzel(x, g * h, rate) for h in harmonics)
    e0 = energy(f)
    return all(e0 > 2 * energy(f * 2 ** (s / 12))
               for s in range(-5, 6) if s)


NOTE_CHECKS = (('lead', 1, 12, 2, (1,), 2), ('bass', 0, 8, 0, (1, 3), 1))


def heard(samples, rate, starts, t0, groups):
    """openMSX's sound against the registers sent (groups[k] sounds
    from starts[k] to starts[k + 1]): the loudness of every frame
    against the model's (correlation), the steady notes of the bass
    and of the lead found."""
    audio = frames_audio(samples, rate, starts, t0)
    level = [rms(x) for x in audio]
    exp = [loudness(g) for g in groups[:len(audio)]]
    r = corr(level, exp)
    notes = {}
    for name, chan, minlen, tol, harms, skip in NOTE_CHECKS:
        res = []
        for a, b, per in note_runs(groups[:len(audio)], chan, minlen,
                                   tol):
            x = [v for k in range(a + skip, b - 1) for v in audio[k]]
            res.append(note_found(x, rate, per, harms))
        notes[name] = {'found': sum(res), 'of': len(res)}
    return {'loudness_correlation': round(r, 3), 'notes': notes}


def pitch_cents(samples, rate, starts, t0, groups, chan, period):
    """The frequency of the longest run of frames where the channel
    plays this period loud, measured in openMSX's sound (the peak of
    the spectrum within a semitone, a tenth of a cent apart), in
    cents from the PSG's clock / (16 period)."""
    runs = [(a, b) for a, b, p in note_runs(groups, chan, 4, 0)
            if p == period]
    if not runs:
        return None, 0
    a, b = max(runs, key=lambda r: r[1] - r[0])
    audio = frames_audio(samples, rate, starts, t0)
    x = [v for k in range(a + 1, min(b, len(audio))) for v in audio[k]]
    f = CLOCK / 2 / (16 * period)
    best = max(range(-1000, 1001, 10),
               key=lambda c: goertzel(x, f * 2 ** (c / 12000), rate))
    fine = max(range(best - 10, best + 11),
               key=lambda c: goertzel(x, f * 2 ** (c / 12000), rate))
    return fine / 10, b - a


def sound(openmsx, cdir, checks, facts, out):
    rom, sym = rom_files(GAME)
    mc = music_check(rom, sym)
    facts['music'] = mc
    checks.add('sound: the music in the cartridge = music.json (made '
               'by psg_music.py); read back = c64/score.py, every note '
               'played with the period round(1 789 772.5 / (16 f))',
               not mc['differ'] and not mc['score'] and
               not mc['periods_wrong'],
               f"{mc['bytes']} bytes, notes {mc['notes_played']}" +
               (f"; differ {mc['differ']}" if mc['differ'] else '') +
               (f"; {mc['score'][:2]}" if mc['score'] else ''))
    checks.add('sound: the eight effects read back = c64/sfx.py (the '
               'notes from the first frame, the release giving up the '
               'priority), the C64\'s priorities', mc['effects_read_back'],
               str(mc['effect_frames']))
    wavs = WAVS
    for mname, (machine, hz) in MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        f = facts.setdefault(f'sound_{mname}', {})
        m, bad, repeats, n = theme_bench(cdir, mname, hz)
        costs = isr_costs(m)
        f['theme'] = {'groups': len(m.plog.groups),
                      'flush_after_interrupt':
                          m.sound_facts['flush_after_interrupt'],
                      'late': m.sound_facts['late_flushes'],
                      'speed': m.mem[sym['music_speed']], **costs}
        wrong = {w: e for w, e in bad.items() if e}
        rules = {w: e for w, e in rule_checks(m).items() if e}
        checks.add(f'{tag}: the theme in the bench, {n} passes '
                   'standing in the Moss Gate: every pass = the model '
                   '(explorer, screen, sounds asked, PSG), the rules',
                   not wrong and not rules,
                   str(wrong or rules) if wrong or rules else
                   f'{len(m.plog.groups)} groups sent')
        speed = MUSIC['speed_50' if hz == 50 else 'speed_60']
        checks.add(f'{tag}: the theme, {speed} frames a step: a loop '
                   f'of {LOOPS[hz]} frames and more = the model, the '
                   'second loop as the first, every group sent at the '
                   'same T-state after its interrupt',
                   repeats and not m.sound_facts['late_flushes'] and
                   m.mem[sym['music_speed']] == (6 if hz == 50 else 7),
                   f"{f['theme']}")
        bad_fx, frames, pokes, passes, mf, pmf = effects_bench(
            cdir, mname, hz)
        want = {n + 1: len(list(fx_entries(n + 1))) + 1
                for n in range(8)}
        # the effect's frame worked out first: its registers go to the
        # PSG a little later after the interrupt than the music's
        fl = PSGLog(mf.psg)
        fl.update()
        after = [t - mf.irq_log[bisect.bisect_right(mf.irq_log, t) - 1]
                 for t, g in fl.groups if t > mf.irq_log[0]]
        f['effects'] = {'frames': frames, 'groups': len(mf.psg.log),
                        'flush_after_interrupt': [min(after), max(after)]}
        checks.add(f'{tag}: SOUND FX, the eight effects one after '
                   'another = the model, each to its end',
                   bad_fx is None and frames == want,
                   bad_fx or str(frames))
        if not openmsx:
            continue
        # openMSX: the sound itself
        rd = RUNS / f'{mname}_theme'
        nt = LOOPS[hz] + 60 if hz == 50 else 1200
        name = f'theme_{hz}hz.wav'
        r = emu_run(openmsx, BUILD / f'{GAME}.rom', sym, mname, nt, rd,
                    script=[(0, (), ())] * nt, psg_log=True,
                    wav=(wavs / name, 0))
        groups = frame_groups(r)
        samples, rate = read_wav(wavs / name)
        starts = [t for t, g in groups]
        hd = heard(samples, rate, starts, r['wav_from'] or 0,
                   [g for t, g in groups])
        f['openmsx_theme'] = hd
        lead, bass = hd['notes']['lead'], hd['notes']['bass']
        checks.add(f'{tag}: openMSX plays the theme ({name}): the '
                   'loudness of every frame follows the registers, every '
                   'steady note of the lead and 8 in 10 of the bass '
                   'found in the sound',
                   hd['loudness_correlation'] >= 0.75 and
                   lead['found'] == lead['of'] and
                   bass['of'] > 0 and bass['found'] >= 0.8 * bass['of'],
                   str(hd))
        rd = RUNS / f'{mname}_effects'
        name = f'effects_{hz}hz.wav'
        rom_fx, sym_fx = rom_files(GAMES[P.MODE_FX])
        r = emu_run(openmsx, BUILD / f'{GAMES[P.MODE_FX]}.rom', sym_fx,
                    mname, passes, rd, script=[(0, (), ())] * passes,
                    pokes=pokes, psg_log=True, wav=(wavs / name, 0))
        same, det = psg_writes_same(mf, r)
        samples, rate = read_wav(wavs / name)
        fg = frame_groups(r)
        groups, starts = [g for t, g in fg], [t for t, g in fg]
        cents, nfr = pitch_cents(samples, rate, starts,
                                 r['wav_from'] or 0, groups, 0,
                                 MUSIC['periods'][E6])
        f['openmsx_effects'] = {'e6_cents': cents, 'e6_frames': nfr}
        checks.add(f'{tag}: openMSX plays the eight effects ({name}): '
                   'its writes to the PSG = the bench\'s; the E6 of the '
                   'fanfare measured in the sound within 3 cents of '
                   '1 789 772.5 / (16 x period)',
                   same and cents is not None and abs(cents) <= 3,
                   f'{det}; E6: {cents} cents over {nfr} frames '
                   f'(the 128K\'s AY clock would give '
                   f'{1200 * math.log2(1773400 / 1789772.5):.1f})')
        f['wav'] = {p.name: p.stat().st_size for p in sorted(
            wavs.glob(f'*_{hz}hz.wav'))}


def frame_groups(r):
    """The groups of registers 0-10 that openMSX's interrupts sent
    (within 2 000 T-states of one): (T, values)."""
    writes, irq = r['psg_writes'], r['irq']
    out, i = [], 0
    while i < len(writes):
        if i + 11 <= len(writes) and \
                [x[1] for x in writes[i:i + 11]] == list(range(11)):
            t = writes[i][0]
            j = bisect.bisect_right(irq, t) - 1
            if j >= 0 and t - irq[j] < 2000:
                out.append((t, [x[2] for x in writes[i:i + 11]]))
            i += 11
        else:
            i += 1
    return out


# -- mutations ------------------------------------------------------------

MUTATIONS = [
    # name, edits (file, old, new), the check that must stop it, the
    # script ('game' or 'defeat')
    ('key_not_used_up',
     [('objects.asm', '        xor b                   ; the key is',
       '        or b                    ; the key is')], 'game'),
    ('potion_with_full_energy',
     [('objects.asm', '        ret nc                  ; full: it stays',
       '        nop                     ; full: it stays')], 'game'),
    ('door_drawn_shut',
     [('objects.asm', 'show_door:\n',
       'show_door:\n        ret\n')], 'solid'),
    ('object_taken_again',
     [('objects.asm', '        ld (de),a               ; taken for',
       '        nop                     ; taken for')], 'game'),
    ('object_not_erased',
     [('objects.asm', '        call erase_object\n',
       '        nop\n')], 'screen'),
    ('seal_100', [('objects.asm', '        ld de,#1000 ',
                   '        ld de,#0100 ')], 'game'),
    ('score_without_daa',
     [('objects.asm', '        add a,e\n        daa\n',
       '        add a,e\n')], 'game'),
    ('portal_two_seals', [('objects.asm', 'MAX_SEALS       equ 3',
                           'MAX_SEALS       equ 2')], 'hero'),
    # a door's cells 1, as a wall's: check_door still answers, but to
    # every wall too (block 1); the explorer's block shows it
    ('door_as_wall', [('room.asm', 'SOLID_DOOR      equ 2',
                       'SOLID_DOOR      equ 1')], 'hero'),
    ('hit_middle_low',
     [('objects.asm', 'HIT_Y           equ (BOX_TOP+BOX_BOTTOM)/2',
       'HIT_Y           equ (BOX_TOP+BOX_BOTTOM)/2+4')], 'game'),
    ('hud_not_updated',
     [('hud.asm', 'hud_update:\n        ld a,(hud_dirty)\n        or a\n'
       '        ret z\n', 'hud_update:\n        ret\n')], 'screen'),
    ('portal_posts_free',
     [('objects.asm', '        call mask_cells\n', '        nop\n')],
     'solid'),
    ('game_goes_on',                    # the pass after VICTORY
     [('main.asm', '        ret nz                  ; out through the'
       ' portal', '        nop')], 'sprites'),
    ('explorer_after_victory',
     [('world.asm', '        ld de,SPRITES\n        ld a,208\n'
       '        ld b,1\n        call vram_fill\n        ld hl,'
       'txt_victory\n', '        ld hl,txt_victory\n')], 'sprites'),
    ('victory_in_name_colour',
     [('world.asm', '        ld c,WON_COLOUR\n',
       '        ld c,#F1\n')], 'screen'),
    ('room_not_hidden',
     [('world.asm', '        ld a,ROOM_BLANK\n',
       '        ld a,ROOM_BLANK\n        ret\n')], 'hidden'),
    ('vdp_address_unguarded',
     [('vdp.asm', 'vram_write_at:\n        di\n',
       'vram_write_at:\n        nop\n')], 'ctrl'),
    ('north_edge_low',
     [('world.asm', 'NORTH_EDGE      equ ROOM_TOP+7-BOX_TOP',
       'NORTH_EDGE      equ ROOM_TOP+6-BOX_TOP')], 'hero'),
    ('list_not_ended',
     [('combat.asm', '        ld a,208                ; the end of',
       '        ld a,207                ; the end of')], 'sprites'),
    ('keys_row_7', [('input.asm', 'KEY_ROW         equ 8 ',
                     'KEY_ROW         equ 7 ')], 'input'),
    ('psg_port_a_out',
     [('player.asm', 'MIXER_OFF       equ %10111111',
       'MIXER_OFF       equ %11111111')], 'r7'),
    # the combat (the ZX's mutations of its milestone 0.6)
    ('fire_held_repeats',
     [('combat.asm', '        jr z,cf_blade           ; no change\n',
       '')], 'combat'),
    ('walking_with_the_blade_out',
     [('combat.asm', '        xor a                   ; the blade is'
       ' out\n        ld (input),a\n', '        xor a\n')], 'input'),
    ('hits_of_a_blow_not_cleared',
     [('combat.asm', '        ld (ix+EN_HIT),0\n', '')], 'combat'),
    ('skeletons_not_turning',
     [('combat.asm', '        xor 1                   ; left-right\n'
       '        ld (ix+EN_DIR),a\n', '        xor 1\n')], 'combat'),
    ('touch_at_12_across',
     [('combat.asm', 'REACH_X         equ 8 ',
       'REACH_X         equ 12 ')], 'combat'),
    ('damage_timer_stuck',
     [('combat.asm', '        dec a\n        ld (invulnerable),a\n',
       '        dec a\n')], 'combat'),
    ('enemies_not_back',
     [('room.asm', '        call spawn_enemies      ; back at their'
       ' places\n', '')], 'combat'),
    ('no_game_over',
     [('combat.asm', '        ret nz\n        jr game_over\n',
       '        ret\n')], 'game', 'defeat'),
    ('skeleton_in_two_hits',
     [('combat.asm', '        db 0,3,1', '        db 0,2,1')], 'combat'),
    ('bats_awake_anywhere',
     [('combat.asm', 'CHASE_X         equ 96 ',
       'CHASE_X         equ 255 ')], 'combat'),
    ('blade_never_listed',
     [('combat.asm', '        pop hl\n        call list_sprite\n',
       '        pop hl\n')], 'combat'),
    ('energy_not_drawn_after_a_touch',
     [('combat.asm', '        ld a,1\n        ld (hud_dirty),a\n'
       '        ld a,SFX_HURT\n', '        ld a,SFX_HURT\n')],
     'screen'),
    ('explorer_not_blinking',
     [('combat.asm', '        ld a,(invulnerable)\n        and 4\n',
       '        ld a,(invulnerable)\n        and 0\n')], 'combat'),
    ('dust_that_stays',
     [('combat.asm', '        ld (ix+EN_KIND),0       ; then gone\n',
       '')], 'combat'),
    ('half_way_point_not_tried',
     [('combat.asm', '        ld a,(blade_dir)        ; the point half'
       ' way\n        add a,4                 ; (entries 4-7)\n',
       '        ret\n')], 'combat'),
    ('game_over_in_name_colour',
     [('combat.asm', '        ld c,LOST_COLOUR\n',
       '        ld c,#F1\n')], 'screen', 'defeat'),
    # the sprites of the MSX
    ('no_rotation',
     [('combat.asm', '        inc (hl)                ; a place further'
       ' on\n', '')], 'sprites'),
    ('rotation_every_frame',
     [('combat.asm', '        jr z,ps_first\n', '')], 'sprites'),
    ('sprites_shown_a_frame_early',
     [('main.asm', '        call put_sprites        ; prepared by the'
       ' last pass\n', ''),
      ('main.asm', '        jp show_combat          ; the next frame\'s'
       ' sprites\n', '        call show_combat\n        jp put_sprites'
       '\n')], 'sprites'),
    ('combat_y_not_a_line_up',
     [('combat.asm', '        dec (hl)                ; Y\n', '')],
     'combat'),
    ('skeleton_in_grey',
     [('combat.asm', 'SKELETON_INK    equ 15 ',
       'SKELETON_INK    equ 14 ')], 'combat'),
    # milestone 0.5.1: the enemy just hit is red
    ('hit_enemy_not_red',
     [('combat.asm', '        ld (hl),HIT_INK         ; red\n', '')],
     'combat'),
    ('hit_enemy_light_red',
     [('combat.asm', 'HIT_INK         equ 8 ',
       'HIT_INK         equ 9 ')], 'screen'),
    ('passes_not_counted',
     [('main.asm', '        ld hl,turn\n        inc (hl)\n', '')],
     'combat'),
    # milestone 0.6: the sound
    ('joystick_read_unguarded',
     [('input.asm', '        di                      ; the interrupt'
       ' selects\n', '        nop\n')], 'psgdi'),
    ('speed_60_at_50',
     [('start.asm', '        ld a,SPEED_50\n', '        ld a,SPEED_60\n')],
     'psg'),
    ('release_a_frame_late',
     [('player.asm', '        add a,GATE_BEFORE\n',
       '        add a,GATE_BEFORE-1\n')], 'psg'),
    ('no_vibrato',
     [('player.asm', '        cp NO_VIBRATO\n        ret z            '
       '       ; an instrument without\n', '        ret\n')], 'psg'),
    ('drums_open_channel_b',
     [('player.asm', 'mix_noise:  db $F7,$EF,$DF',
       'mix_noise:  db $F7,$EF,$EF')], 'psg'),
    ('register_10_not_sent',
     [('player.asm', 'PSG_REGS        equ 11 ',
       'PSG_REGS        equ 10 ')], 'psg'),
    ('interrupt_without_sound',
     [('interrupt.asm', '        call audio_frame        ; the PSG of'
       ' this frame\n', '')], 'psg'),
    ('slash_not_asked',
     [('combat.asm', '        ld a,SFX_SLASH\n        call sound_effect'
       '\n', '')], 'calls'),
    ('victory_without_its_piece',       # end_game without end_sound
     [('world.asm', '        jp end_game             ; end (screens.asm)'
       '\n', '        ld a,STATE_ENDING\n        ld (game_state),a\n'
       '        ld a,ENDING_FRAMES\n        ld (end_timer),a\n'
       '        ret\n')], 'calls'),
    ('song_of_the_end_wrong',
     [('player.asm', '        add a,a\n        add a,l\n        add a,a'
       '\n', '        add a,a\n        add a,a\n')], 'psg'),
    ('music_not_by_the_interrupt',
     [('world.asm', '        ld a,1                  ; the interrupt\'s'
       ' work\n        ld (music_by_isr),a\n', '')], 'psg_time'),
    ('music_not_ready_before_a_room',
     [('world.asm', '        call music_due          ; the next frame '
       'now, then\n', '')], 'psg_time'),
    ('effects_without_priority',
     [('player.asm', '        jr c,se_refused         ; less important'
       ': not heard\n', '')], 'psg', 'game', P.MODE_FX),
    ('release_keeps_the_priority',
     [('player.asm', '        xor a                   ; the release '
       'goes on: any\n        ld (sfx_prio),a         ; effect may '
       'come now\n', '')], 'psg', 'game', P.MODE_FX),
    # milestone 0.6.1: no frame of delay
    ('effect_a_frame_late',
     [('player.asm', 'fx_frame:\n        ld a,(audio_mode)\n'
       '        cp MODE_FX\n        call z,fx_step          ; SOUND FX:'
       ' this frame\n        jp psg_flush\n',
       'fx_frame:\n        call psg_flush\n        ld a,(audio_mode)\n'
       '        cp MODE_FX\n        ret nz\n        jp fx_step\n')],
     'latency', 'game', P.MODE_FX),
    ('end_piece_a_frame_late',
     [('player.asm', '        jp music_step           ; its first '
       'frame, ready for\n', '        ret\n')], 'latency'),
    # milestone 0.7: the states, the title, the end screens (the
    # session 'mutation': the menu, two short games)
    ('title_theme_not_again',
     [('screens.asm', '        ld a,(audio_mode)       ; first the sound\n'
       '        call set_audio\n', '')], 'calls', 'session'),
    ('room_still_49',
     [('screens.asm', 'ENDING_FRAMES   equ 50', 'ENDING_FRAMES   equ 49')],
     'states', 'session'),
    ('fire_counts_too_soon',
     [('screens.asm', '        ld (fire_armed),a       ; presses do not '
       'count yet\n', '')], 'states', 'session'),
    ('rooms_not_counted',
     [('room.asm', '        jp mark_seen            ; seen: for the '
       'end screen\n', '        ret\n')], 'screen', 'session'),
    ('new_game_keeps_rooms',
     [('start.asm', '        ld (rooms_seen),a       ; none (put_names '
       'marks)\n', '')], 'screen', 'session'),
    ('prompt_still',
     [('screens.asm', 'pulse_prompt:\n        ld a,(turn)\n',
       'pulse_prompt:\n        ret\n        ld a,(turn)\n')], 'screen',
     'session'),
    ('letters_without_joints',
     [('screens.asm', '        ld b,0                  ; rows 7 and 15: '
       'dark', '        ld b,#FF                ; rows 7 and 15: dark')],
     'screen', 'session'),
    ('logo_without_moss',
     [('screens.asm', '        call nz,big_drips', '        nop')],
     'screen', 'session'),
    ('band_flames_still',
     [('screens.asm', '        call band_flame\n', '')], 'screen',
     'session'),
    ('cursor_runs_held',
     [('screens.asm', '        ld hl,stick_held\n        cp (hl)\n'
       '        ld (hl),a\n        ret z                   ; no change\n',
       '        ld hl,stick_held\n        cp (hl)\n        ld (hl),a\n')],
     'states', 'session'),
    ('sound_fx_without_sample',
     [('screens.asm', '        ld a,SFX_PICKUP         ; a sample of the '
       'effects\n        jp sound_effect', '        ret\n'
       '        jp sound_effect')], 'calls', 'session'),
    ('music_owed_kept',
     [('player.asm', '        ld (sfx_prio),a\n        ld (music_owed),a\n'
       '        ld a,(audio_mode)\n', '        ld (sfx_prio),a\n'
       '        ld a,(audio_mode)\n')], 'psg', 'session'),
    ('drawing_without_the_interrupt',
     [('screens.asm', 'screen_blank:\n        call music_due\n'
       '        ld a,1\n        ld (music_by_isr),a\n',
       'screen_blank:\n        call music_due\n')], 'psg_time',
     'session'),
    ('fire_at_the_press',
     [('screens.asm', '        jr nz,fr_pressed\n', '        jr nz,fr_now\n'),
      ('screens.asm', 'fr_pressed:\n', 'fr_now:\n        scf\n'
       '        ret\nfr_pressed:\n')], 'states', 'session'),
    ('skeleton_of_the_title_still',
     [('screens.asm', '        ld a,(turn)             ; the skeleton: '
       'pass / 8\n', '        xor a                   ; the skeleton: '
       'pass / 8\n')], 'sprites', 'session'),
    # milestone 0.8: the opening screen (the session 'mutation': its
    # three seconds; 'mutation_skip': FIRE ends it)
    ('opening_too_short',
     [('screens.asm', 'OPENING_50      equ 150',
       'OPENING_50      equ 149')], 'states', 'session'),
    ('opening_theme_again',
     [('screens.asm', '        jp title_screen         ; the theme goes on',
       '        jp show_title')], 'calls', 'session'),
    ('opening_names_a_row_low',
     [('screens.asm', '        ld de,NAMES+OPEN_ROW*32 ; their names',
       '        ld de,NAMES+OPEN_ROW*32+32')], 'screen', 'session'),
    ('opening_cells_on_the_logo',
     [('screens.asm', '        ld d,(PATTERNS+OPEN_BASE0*8)/256',
       '        ld d,PATTERNS/256')], 'screen', 'session'),
    ('opening_without_credit',
     [('screens.asm', '        ld bc,OPEN_CREDIT_ROW*256+OPEN_CREDIT_COL\n'
       '        ld hl,txt_credit\n        ld a,TEXT_NUM\n'
       '        call print_text\n', '')], 'screen', 'session'),
    ('opening_deaf_to_fire',
     [('screens.asm', '        call fire_released\n        jr c,of_title\n',
       '        call fire_released\n')], 'states', 'session_skip'),
]


def mutations(sjasm, openmsx, cdir, checks, facts, which=None):
    state = json.loads((BUILD / 'state_eu.json').read_text())
    cb = cbios_roms(cdir, 'eu')
    script, pokes = game_script()
    out = {}
    scripts = {'game': (script, pokes), 'defeat': defeat_script()}
    chosen = MUTATIONS if which is None else MUTATIONS[which[0]:which[1]]
    for mname, edits, must, *run_of in chosen:
        session = run_of and run_of[0] in ('session', 'session_skip')
        if not session:
            mscript, mpokes = scripts[run_of[0] if run_of else 'game']
        mode = run_of[1] if len(run_of) > 1 else P.MODE_MUSIC
        tmp = Path(tempfile.mkdtemp(prefix='mut_'))
        try:
            src = tmp / 'src'
            shutil.copytree(SRC, src)
            # the game as the chain's last step shows it: the tags of
            # the steps (tools/make_chain.py) out of the comments
            for f in src.glob('*.asm'):
                text = final_text(f.read_text(encoding='ascii'), f.name)
                f.write_text(text, encoding='ascii')
            ok_edit = True
            for fname, old, new in edits:
                p = src / fname
                text = p.read_text(encoding='ascii')
                if text.count(old) != 1:
                    ok_edit = False
                p.write_text(text.replace(old, new), encoding='ascii')
            code, msg = run([sjasm, '--nologo', '--msg=war',
                             f'-DSTART_ROOM={GAME_ROOM}',
                             f'-DSOUND_MODE={mode}',
                             f'-DSTART_PLAY={0 if session else 1}',
                             f'-i{GENERATED.as_posix()}',
                             f'--raw={(tmp / "m.rom").as_posix()}',
                             f'--sym={(tmp / "m.sym").as_posix()}',
                             (src / 'cryptmorrow.asm').as_posix()], tmp)
            if code or not ok_edit:
                checks.add(f'mutation {mname}: applied and assembled',
                           False, msg or 'the text to change is not '
                           'there once')
                continue
            rom, sym = rom_files('m', tmp)
            if session:
                import sessions_0_8
                bad, rules = sessions_0_8.mutation_run(
                    sys.modules[__name__], rom, sym, cdir,
                    'mutation_skip' if run_of[0] == 'session_skip'
                    else 'mutation')
                bad.update(rules)
                stopped = {k for k, e in bad.items() if e}
                out[mname] = sorted(stopped)
                checks.add(f'mutation {mname}: stopped by "{must}"',
                           must in stopped, 'checks failed: ' +
                           ', '.join(sorted(stopped)))
                continue
            m, recs, bad, fr, last, ch, ev = bench_walk(
                rom, sym, state, cb, None, mscript, GAME_ROOM, mpokes,
                until=must, screen=must == 'screen', mode=mode)
            bad.update(rule_checks(m))
            stopped = {k for k, e in bad.items() if e}
            out[mname] = sorted(stopped)
            emu = ''
            if openmsx and must == 'r7':
                rd = RUNS / f'mut_{mname}'
                r = emu_run(openmsx, tmp / 'm.rom', sym, 'eu', 60, rd,
                            script=mscript[:60], pokes=mpokes)
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


def split_facts(facts):
    """(the bench's facts, openMSX's): the key openmsx (palettes,
    screenshots) is openMSX's; in the facts of a part, the keys
    openmsx_... and wav are the measures of openMSX's sound, left out
    of both: the recording goes through the audio mixer of the
    platform (on Windows the files at 60 Hz end 512 samples earlier
    than on Linux, and the measures move in the third decimal), so
    they are checked against their thresholds on every machine, not
    compared between machines. The writes to the PSG that make the
    sound are compared, every one. The screenshots of the sessions
    (session_...: taken in real time, with the sound recorded) are
    left out too: openMSX's picture at a frame_ready is one of a few
    frames before, how many depends on how busy the machine is (on the
    PC, with other programs at work, the screenshot two frames after
    the title showed the title's picture again); each one is checked
    on every machine against the bench's last pictures, every pixel.
    The palettes and the screenshots of the games are compared."""
    bench, emu = {}, {}
    for k, v in facts.items():
        if k == 'openmsx':
            emu[k] = {x: y for x, y in v.items()
                      if not x.startswith('session_')}
        elif isinstance(v, dict):
            bench[k] = {x: y for x, y in v.items()
                        if not x.startswith('openmsx') and x != 'wav'}
        else:
            bench[k] = v
    return bench, emu


def main():
    global RUNS, WAVS
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--openmsx')
    ap.add_argument('--no-openmsx', action='store_true')
    ap.add_argument('--reference')
    ap.add_argument('--update-state', action='store_true')
    ap.add_argument('--keep-runs', action='store_true')
    ap.add_argument('--sjasmplus')
    ap.add_argument('--only', help='parts, comma separated: data, '
                    'sound, palettes, game, defeat, shots, rooms, '
                    'mutations')
    ap.add_argument('--mutations', help='FROM-TO: only these (0-based, '
                    'TO excluded)')
    a = ap.parse_args()
    parts = set(a.only.split(',')) if a.only else {
        'data', 'sound', 'palettes', 'game', 'defeat', 'shots', 'rooms',
        'sessions', 'mutations'}
    which = tuple(int(x) for x in a.mutations.split('-')) \
        if a.mutations else None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    png = out / 'png'
    png.mkdir(exist_ok=True)
    WAVS = out / 'wav'
    WAVS.mkdir(exist_ok=True)
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
        RUNS = Path(tempfile.mkdtemp(prefix='verify_0_8_'))
    checks, facts = Checks(), {}
    try:
        manifest = json.loads((BUILD / 'manifest.json').read_text())
        checks.add('build: game/build/manifest.json without problems',
                   not manifest['problems'],
                   '; '.join(manifest['problems'][:2]))
        facts['build'] = {k: e['sha256'][:16]
                          for k, e in manifest['roms'].items()}
        facts['cartridge'] = manifest['measures']
        if 'data' in parts:
            data(checks, facts, cdir, png)
        if 'sound' in parts:
            sound(openmsx, cdir, checks, facts, out)
        if openmsx and 'palettes' in parts:
            palettes(openmsx, checks, facts)
        if 'game' in parts:
            game(openmsx, cdir, checks, facts, a)
        if 'defeat' in parts:
            defeat(openmsx, cdir, checks, facts)
        if openmsx and 'shots' in parts:
            shots(openmsx, cdir, checks, facts, png)
        if 'rooms' in parts:
            rooms(openmsx, cdir, checks, facts)
        if 'sessions' in parts:
            import sessions_0_8
            sessions_0_8.sessions(sys.modules[__name__], openmsx, cdir,
                                  checks, facts, png)
        if 'mutations' in parts:
            if sjasm:
                mutations(sjasm, openmsx, cdir, checks, facts, which)
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
        rb, ro = split_facts(ref)
        mb, mo = split_facts(mine)
        diff = [k for k in rb if rb.get(k) != mb.get(k)]
        checks.add('bench facts = the reference (' + a.reference + ')',
                   not diff, ', '.join(diff[:4]))
        if openmsx and ro:
            diff = sorted(k for k in set(ro) | set(mo)
                          if ro.get(k) != mo.get(k))
            checks.add('openMSX facts (palettes, screenshots) = the '
                       'reference', not diff, ', '.join(diff[:4]))
    report = {'checks': checks.items, 'facts': facts,
              'failed': len(checks.failed), 'openmsx': openmsx,
              'cbios': str(cdir)}
    (out / 'verify_0_8.json').write_text(json.dumps(report, indent=1)
                                         + '\n', encoding='utf-8')
    print(f'\n{len(checks.items)} checks, {len(checks.failed)} failed')
    for c in checks.failed:
        print('FAILED:', c['check'], c['detail'])
    return 1 if checks.failed else 0


if __name__ == '__main__':
    sys.exit(main())

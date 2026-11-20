"""The test of a step of the book's chain (Phase D, D.2): steps 01-06
(steps 07 and 08: tests/verify_1_0.py --step 7|8, the test of the
complete game).

The step is the folder chain/NN (made and built by tools/make_chain.py
--assemble); its cartridge is started from the C-BIOS state at INIT
(game/build/state_eu.json, state_int.json), at 50 Hz (C-BIOS MSX1 EU)
and at 60 Hz (C-BIOS MSX1), in the bench (tests/msxsim.py) and in
openMSX:

  build      the cartridge = chain/chain.json's (SHA-256), its
             manifest without problems
  data       the rooms' records in the cartridge (door, objects,
             enemies: in the data from step 01, used from 04 and 05)
             = the room files, from 04 with the open tiles of the
             doors; from 02 the explorer's 16 sprite shapes in the
             VRAM after INIT = art_pieces.HERO_FRAMES in its two
             colours; from 05 the nine images of the combat; in 06
             the music read back = c64/score.py
  route      the step's route, every pass = the step's model
             (tests/step_world.py), from the first pass: the input
             byte, the explorer, the game, the combat, the sprite
             list, the screen, the variables (frames = interrupts,
             room, zone, the stack), the VDP's registers, the solid
             map, every change of room hidden (else one interrupt a
             pass); in step 03 every opening of the 16 rooms crossed
             (the model's route); the rules (no VRAM
             access closer than 29 T in the picture, the VDP's
             address with interrupts off, no write to the ROM; before
             step 06 nothing written to the PSG's sound registers,
             from 06 register 7 always 10xxxxxx and the PSG with
             interrupts off); in step 06 the walk of the test of 1.0
             as it is (tests/verify_0_8.py bench_walk): also the
             sounds asked and every group of registers sent to the
             PSG = the model (psg_model)
  seeds      the start with the RAM and the VRAM filled at random (two
             fillings, SEED_PASSES passes): every pass = the model;
             the RAM written only in the areas of vars.asm
  openMSX    the same input: every pass = the bench (RAM, VRAM, VDP
             and PSG registers, slots, T-states, the interrupts; in
             step 06 every write to the PSG at the same T-state)
  captures   the step's moments as PNG (from the bench); openMSX's
             screenshot of the first of them after pass 8 (a short run
             of its own, in real time) = one of the bench's last
             pictures
  mutations  three one-line defects in what the step adds, each
             built from the step's sources and stopped by the check
             named

The routes (the input of the keyboard and of the joystick in turn,
tests/verify_0_8.py script_of):

  01  ROUTE_01 passes of random input: none is read
  02  the Moss Gate: as far as the explorer goes to the north, south,
      west and east (into the openings, up to the edge of the room),
      back to the start each time; then ROUTE_02 passes of random input
  03  every room, from its own cartridge (START_ROOM = 0-15, built
      from the step's sources; room 1 is the step's cartridge): out
      through every opening and back (an opening whose way back is a
      shut door: last, one way); then ROUTE_03 passes of random input
  04  the walking game: the steps of the whole game of the test of
      1.0 (tests/game_plan.py GAME_STEPS, the doors that resist
      included) without the fights, to VICTORY; then AFTER passes of
      random input, the room still
  05  the whole game of the test of 1.0 (tests/game_0_5.json), the
  06  fights and VICTORY; GAME OVER without help (tests/sessions_1_0.py:
      four touches of the skeleton of the Crossroads); each then AFTER
      passes of random input, the room still

Report: chain/evidence-workspace/steps/NN/verify_step.json (--out
another folder), with the PNGs. With --reference REPORT the facts of
the bench are compared with another report's (the workspace's, in the
virtual machine and on the PC).

Usage: python tests/verify_step.py --step N [--out DIR] [--chain DIR]
       [--openmsx EXE] [--no-openmsx] [--sjasmplus EXE]
       [--no-mutations] [--reference REPORT]
The parts of the virtual machine (a call there has a time limit):
       [--machine eu|int] [--segment N|FROM-TO] [--no-screen]
       [--no-seeds] [--seeds-only] [--mutations-only] [--mutation NAME]
"""
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE), str(ROOT / 'tools')]
import folder_first as FF  # noqa: E402
FOLDER = FF.use(sys.argv)       # a variant's folder: its data first
import hero_model as H  # noqa: E402
import msx_model  # noqa: E402
import msxsim  # noqa: E402
import openmsx_run  # noqa: E402
import route as RT  # noqa: E402
import sessions_1_0 as S1  # noqa: E402
import step_world as SW  # noqa: E402
import verify_0_8 as V  # noqa: E402
import vram2png  # noqa: E402
import world_model as W  # noqa: E402
from collections import deque  # noqa: E402
from game_plan import GAME_STEPS  # noqa: E402
from msxtools import (cbios_dir, find_tool, read_symbols,  # noqa: E402
                      run)

CHAIN = ROOT / 'chain'
STEPS = {1: '01-first-room', 2: '02-explorer', 3: '03-dungeon',
         4: '04-objects-doors', 5: '05-combat', 6: '06-sound'}
U, D, L, R, F = V.U, V.D, V.L, V.R, V.F
START = V.GAME_ROOM                     # the Moss Gate
# what a variant may change in the test (--set, Phase D, D.3)
FLAME_SHIFT = 3                         # the flame: frames >> 3
JOY_PORT = 1                            # the joystick plugged in port 1
SOUND_MODE = 0                          # step 06: MUSIC at INIT
GAME_CHASE = (W.CHASE_X, W.CHASE_Y)     # a bat wakes within (1.0)
ROUTE_01, ROUTE_02, ROUTE_03 = 400, 2000, 150
AFTER = 300                             # passes after an end
SEED_PASSES = 500
SIDES = ('north', 'south', 'west', 'east')
OPPOSITE = {'north': 'south', 'south': 'north', 'west': 'east',
            'east': 'west'}
WHAT = ('reached', 'input', 'hero', 'game', 'combat', 'sprites',
        'screen', 'variables', 'registers', 'solid', 'hidden', 'quiet')
LABELS = dict(V.LABELS, quiet='nothing written to the PSG\'s sound '
              'registers (0-13)')
# the first step with each check (the others: every step)
FROM = {'input': 2, 'hero': 2, 'game': 3, 'combat': 5}


def name_of(step, what):
    """The name of a check of every pass, as the step has it."""
    if what == 'input' and step < 5:
        return 'the input byte = keys + joystick'
    if what == 'game' and step < 4:
        return 'keys, seals, score, energy (the HUD\'s values)'
    if what == 'hidden' and step < 3:
        return 'one interrupt a pass'
    if what == 'hidden' and step < 6:
        return 'every change hidden, else one interrupt a pass'
    return LABELS[what]
BLANK = 1                               # row 0 before step 03: black

# Three one-line defects a step: (name, step, [(file, old, new)], the
# check that must stop it, the route). From the tests of milestones
# 0.1-0.8 (tests/verify_0_1.py ... verify_0_8.py), in what the step
# adds.
MUTATIONS = [
    ('third_without_inc', 1, [('room.asm', '        ld a,c\n'
                               '        inc a\n        rrca\n',
                               '        ld a,c\n        rrca\n')],
     'screen'),
    ('status_not_read', 1, [('interrupt.asm', '        in a,(VDP_STAT)'
                             '         ; clears',
                             '        xor a                   ; clears')],
     'reached'),
    ('names_in_rom', 1, [('vars.asm', 'room_names      equ #C100',
                          'room_names      equ #8100')], 'rom'),
    ('right_wins', 2, [('hero.asm', '        bit 2,c                 ; '
                        'left', '        bit 3,c                 ; '
                        'left')], 'hero'),
    ('sprite_a_line_low', 2, [('hero.asm', '        ld a,(hero_y)\n'
                               '        dec a\n',
                               '        ld a,(hero_y)\n')], 'sprites'),
    ('keys_row_7', 2, [('input.asm', 'KEY_ROW         equ 8 ',
                        'KEY_ROW         equ 7 ')], 'input'),
    ('west_goes_east', 3, [('world.asm', '        ld a,255            '
                            '    ; a room left',
                            '        ld a,1                  ; a room '
                            'left')], 'hero'),
    ('room_not_hidden', 3, [('world.asm', '        ld a,ROOM_BLANK\n',
                             '        ld a,ROOM_BLANK\n        ret\n')],
     'hidden'),
    ('name_not_changed', 3, [('room.asm', '        call build_room   '
                              '      ; HL: then the name\n'
                              '        jp hud_draw',
                              '        call build_room         ; HL: '
                              'then the name\n        ld a,(zone)\n'
                              '        cp #FF\n        ret nz\n'
                              '        jp hud_draw')], 'screen'),
    ('key_not_used_up', 4, None, 'game'),
    ('door_drawn_shut', 4, None, 'solid'),
    ('hud_not_updated', 4, None, 'screen'),
    ('skeletons_not_turning', 5, None, 'combat'),
    ('no_rotation', 5, None, 'sprites'),
    ('no_game_over', 5, None, 'game', 'defeat'),
    ('joystick_read_unguarded', 6, None, 'psgdi'),
    ('slash_not_asked', 6, None, 'calls'),
    ('register_10_not_sent', 6, None, 'psg'),
]


def mutation_edits(mu):
    """The edits of a mutation: its own, or those of the test of 1.0
    of the same name."""
    if mu[2] is not None:
        return mu[2]
    return next(m[1] for m in V.MUTATIONS if m[0] == mu[0])


# -- the step's model on the screen --------------------------------------

def model_screen(world, count):
    """The screen of the step at a frame counter (as
    verify_0_8.model_screen): row 0 blank before step 03."""
    rows = V.model_room(world.name, (count >> FLAME_SHIFT) & 3,
                        world.drawn())
    if world.hud_blank():
        rows = [[BLANK] * 256 for _ in range(8)] + rows[8:]
    if world.black:
        return msx_model.black_room(rows)
    return msx_model.with_sprites(rows, world.sat())


# -- the walk of steps 01-05 -----------------------------------------------

def step_walk(rom, sym, state, cb, step, script, start, pokes=None,
              seed=None, until=None, screen=True, shows=None):
    """The step with this input, checked after every pass of the main
    loop against the step's model, as verify_0_8.bench_walk does for
    the complete game (without the sound: before step 06 the PSG's
    sound registers are never written). Returns (machine, records for
    openMSX, problems, facts, last RAM, the changes of room, the
    passes that changed the game)."""
    m = msxsim.MSX(rom, state, cb, seed=seed)
    m.joy_port = JOY_PORT - 1
    m.watch = {sym['hide_room']: 'hide_room'} if 'hide_room' in sym \
        else {}
    m.marks = V.MarksA(m)
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
    world = SW.StepWorld(step, start)
    has = {w: step >= FROM.get(w, 1) for w in WHAT}
    has['quiet'] = step < 6

    def at(name):
        return sym[name] - 0xC000
    hv = [at(v) for v in V.HERO_VARS if v in sym]
    gnames = [v for v in ('key_set', 'seals', 'score', 'energy',
                          'doors_open', 'game_ended') if v in sym]
    cv = [at(v) for v in ('turn', 'slash_timer', 'blade_dir', 'fire_held',
                          'invulnerable', 'hero_shown', 'spr_rot',
                          'spr_count') if v in sym]
    bad = dict.fromkeys(WHAT)
    recs, digest, changes, events = [], hashlib.sha256(), [], []
    ram = None
    pend = None
    psg_seen = 0
    before, t_prev = bytes(vdp.vram), m.tstates
    for k, (bits, keys, joy) in enumerate(script, 1):
        for name, v in pokes.get(k, ()):
            m.mem[sym[name]] = v
            V.poke_model(world, name, v)
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
        count = ram[at('frames')] | ram[at('frames') + 1] << 8
        if has['input'] and bad['input'] is None and \
                ram[at('input')] != world.input:
            bad['input'] = f'pass {k}: #{ram[at("input")]:02X}, model ' \
                           f'#{world.input:02X}'
        if has['hero'] and bad['hero'] is None:
            prog = (ram[at('room')],) + tuple(ram[a] for a in hv)
            want = world.state()[:len(prog)]
            if prog != want:
                bad['hero'] = f'pass {k}: {prog}, model {want}'
        if has['game'] and bad['game'] is None:
            game = tuple(V.bcd(ram, at(v)) if v == 'score' else
                         ram[at(v)] for v in gnames)
            if 'taken' in sym:
                game += tuple(ram[at('taken'):at('taken') + 32])
            want = world.game_state()[:len(gnames)] + (
                world.game_state()[6:] if 'taken' in sym else ())
            if game != want:
                bad['game'] = f'pass {k}: {game[:6]}, model {want[:6]}'
        if has['combat'] and bad['combat'] is None:
            n = ram[at('spr_count')]
            combat = tuple(ram[a] for a in cv) + tuple(
                ram[at('enemies'):at('enemies') + 27]) + tuple(
                ram[at('spr_list'):at('spr_list') + 4 * n])
            if combat != world.combat_state():
                bad['combat'] = f'pass {k}: {combat}, model ' \
                                f'{world.combat_state()}'
        if bad['sprites'] is None and V.sat_of(vram) != world.sat():
            bad['sprites'] = f'pass {k}: {V.sat_of(vram)}, model ' \
                             f'{world.sat()}'
        if screen and bad['screen'] is None:
            d = V.first_diff(V.screen_of(vram, regs),
                             model_screen(world, count))
            if d:
                bad['screen'] = (f'pass {k} (room {world.room}): pixel '
                                 f'({d[1]}, {d[0]}) colour {d[2]}, '
                                 f'model {d[3]}')
        if bad['variables'] is None:
            vals = {'frames': (count, len(m.irq_log) & 0xFFFF),
                    'room': (ram[at('room')], world.room),
                    'zone': (ram[at('zone')],
                             msx_model.zone_of(world.name)),
                    'SP': (m.regs[msxsim.SP_], V.STACK)}
            if 'reveal_due' in sym:
                vals['reveal_due'] = (ram[at('reveal_due')], int(changed))
            wrong = [f'{n} {a} not {b}' for n, (a, b) in vals.items()
                     if a != b]
            if wrong:
                bad['variables'] = f'pass {k}: ' + ', '.join(wrong)
        if bad['registers'] is None and regs != V.VDP_REGS:
            bad['registers'] = f'pass {k}: VDP {regs}'
        if bad['solid'] is None and \
                list(ram[at('solid_map'):at('solid_map') + 640]) != \
                world.hero.solid:
            bad['solid'] = f'pass {k}: the solid map in RAM (room ' \
                           f'{world.room})'
        if pend is not None:
            p_before, p_t0, p_hide, p_writes, p_k, p_irq, p_t = pend
            e, black = V.hidden(p_before, p_writes + writes, p_t0,
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
        elif len(m.irq_log) - n_irq != 1 and bad['hidden'] is None:
            bad['hidden'] = f'pass {k}: {len(m.irq_log) - n_irq} ' \
                            'interrupts without a change'
        if shows is not None:
            shows.update(k, ram, vram, script[k - 1], sym)
        if has['quiet']:
            log = m.psg.log
            loud = [x for x in log[psg_seen:] if x[1] < 14]
            psg_seen = len(log)
            if loud and bad['quiet'] is None:
                bad['quiet'] = f'pass {k}: register {loud[0][1]} = ' \
                               f'#{loud[0][2]:02X}'
        what = V.event_of(g0, world.game_state(), c0,
                          world.combat_state())
        if what:
            events.append((k, what))
        writes.clear()
        before, t_prev = vram, m.tstates
        recs.append((V.h(ram), V.h(vram), tuple(regs),
                     tuple(m.psg.regs[:14] + m.psg.regs[15:]), m.a8,
                     m.tstates))
        digest.update(f'{m.tstates} {V.h(ram)} {V.h(vram)};'.encode())
        if until and (bad.get(until) or
                      (until in V.RULES and rules_of(step, m)[until])):
            break
    for w in WHAT:
        if not has[w]:
            bad[w] = None
    facts = {'passes': len(recs), 'end_t': m.tstates,
             'digest': digest.hexdigest()[:16],
             'changes': [[c['pass'], c['room'], c['irq'], c['black']]
                         for c in changes],
             'events': {w: sum(1 for k, x in events if x == w)
                        for w in sorted({x for k, x in events})},
             'game': list(world.game_state()[:6]),
             'room': world.room}
    return m, recs, bad, facts, ram, changes, events


def applicable(step):
    """The checks of every pass that the step has."""
    if step == 6:
        return V.WHAT
    return [w for w in WHAT if step >= FROM.get(w, 1) and
            (w != 'quiet' or step < 6)]


def rules_of(step, m):
    """The rules of verify_0_8.rule_checks; before step 06 the PSG's
    register 7 is never written and the interrupt does not use the
    PSG: no DI around the joystick (tests/chain_smoke.py)."""
    rules = V.rule_checks(m)
    if step < 6:
        rules['r7'] = rules['psgdi'] = None
    return rules


def walk(rom, sym, state, cb, step, script, start, pokes=None, seed=None,
         until=None, screen=True, shows=None):
    """Steps 01-05: step_walk; step 06: the walk of the test of 1.0
    (bench_walk, MUSIC), as it is. screen: the screen compared every
    pass (left out only in the long parts of the virtual machine)."""
    if step < 6:
        return step_walk(rom, sym, state, cb, step, script, start, pokes,
                         seed, until, screen, shows)
    msxsim.MSX.joy_port = JOY_PORT - 1
    m, recs, bad, facts, ram, ch, ev = V.bench_walk(
        rom, sym, state, cb, seed, script, start, pokes, until=until,
        screen=screen, mode=SOUND_MODE)
    msxsim.MSX.joy_port = 0
    if shows is not None and facts.get('sound'):
        shows.data['sound_kinds'] = facts['sound']['kinds']
        shows.data['sound_calls'] = facts['sound']['calls']
    facts['room'] = ram[sym['room'] - 0xC000] if ram else None
    return m, recs, bad, facts, ram, ch, ev


# -- what a route shows (the facts of the variants, D.3) -----------------

class Shows:
    """What a walk shows, pass by pass, from the program's RAM and
    VRAM (report['shows'], not compared with a reference): the flame
    phases drawn, the zone at the start, the explorer's colours, the
    energy, the moves made with the joystick alone, the first bat."""

    def __init__(self, step):
        self.step = step
        self.data = {}
        self.prev = None
        self.flames = 0
        self.energies = []
        self.joy_moves = 0
        self.bat = None

    def update(self, k, ram, vram, item, sym):
        def var(name):
            return ram[sym[name] - 0xC000] if name in sym else None
        d = self.data
        phase = var('flame_phase')
        if self.prev is not None and phase != self.prev['phase']:
            self.flames += 1
        if k == 1:
            d['zone_start'] = var('zone')
        if k == V.PREFIX:
            # the room drawn: its green pixels (inks 2, 3, 12), the
            # ink of the energy bar (row 0, column 7: its slot's row 3)
            rows = V.screen_of(vram, V.VDP_REGS)
            d['green_room'] = sum(1 for r in rows[16:176] for c in r
                                  if c in (2, 3, 12))
            if 'energy' in sym:
                slot = vram[0x1800 + 7]
                d['bar_ink'] = vram[0x2000 + 8 * slot + 3] >> 4
        sat = V.sat_of(vram)
        if 'clothes' not in d and len(sat) >= 2:
            d['skin'], d['clothes'] = sat[0][3], sat[1][3]
        energy = var('energy')
        if energy is not None and (not self.energies or
                                   self.energies[-1] != energy):
            self.energies.append(energy)
        pos = (var('hero_x'), var('hero_y'))
        bits, keys, joy = item
        if self.prev is not None and joy and not keys and \
                pos != self.prev['pos']:
            self.joy_moves += 1
        if 'enemies' in sym:
            self.track_bat(k, ram, sym, pos)
        self.prev = {'phase': phase, 'pos': pos}

    def track_bat(self, k, ram, sym, pos):
        """The first bat of the room: where it is, when it first moves
        and how far the explorer was then; how long it stayed still
        with the explorer within the game's box of 96 x 90."""
        e0 = sym['enemies'] - 0xC000
        bats = [ram[e0 + 9 * i:e0 + 9 * i + 9] for i in range(3)
                if ram[e0 + 9 * i] == W.BAT]
        if not bats:
            self.bat = None
            return
        b = bats[0]
        at = (b[1], b[2])
        far = (abs(pos[0] - at[0]), abs(pos[1] - at[1]))
        if self.bat is None or self.bat.get('room') != ram[
                sym['room'] - 0xC000]:
            self.bat = {'room': ram[sym['room'] - 0xC000], 'at': at,
                        'still_in_96x90': 0, 'woke_at': None}
            self.data.setdefault('bats', []).append(self.bat)
            return
        if at == self.bat['at'] and self.bat['woke_at'] is None:
            if far[0] < GAME_CHASE[0] and far[1] < GAME_CHASE[1]:
                self.bat['still_in_96x90'] += 1
        elif self.bat['woke_at'] is None:
            self.bat['woke_at'] = {'pass': k, 'far': list(far)}
        self.bat['at'] = at

    def result(self, facts):
        d = dict(self.data)
        d['flame_changes'] = self.flames
        d['energies'] = self.energies
        d['joy_moves'] = self.joy_moves
        d['events'] = facts.get('events', {})
        d['game'] = facts.get('game')
        return d


# -- the routes --------------------------------------------------------------

def script_of(bits):
    """[(bits, keys, joy)] a pass: the keyboard, the joystick and both
    in turn, a run of the same input each (verify_0_8.script_of)."""
    return V.script_of(V.runs_of(bits), V.SOURCES)


def random_bits(seed, n):
    return [b for b, k, j in V.random_route(seed, n)]


def reach(world):
    """Every position the explorer can reach in its room from where it
    is (the step's rules: before step 03 no exits), breadth first:
    {(x, y): (previous, input)}."""
    probe = H.HeroModel(world.hero.solid)
    start = (world.hero.x, world.hero.y)
    back = {start: None}
    todo = deque([start])
    while todo:
        x, y = todo.popleft()
        for joy in RT.MOVES:
            probe.x, probe.y = x, y
            probe.update(joy)
            nxt = (probe.x, probe.y)
            if nxt not in back:
                back[nxt] = ((x, y), joy)
                todo.append(nxt)
    return back


def path_to(back, goal):
    path, at = [], goal
    while back[at] is not None:
        at, joy = back[at]
        path.append(joy)
    return path[::-1]


def route_02():
    """The Moss Gate: as far as the explorer goes in each direction,
    back to the start each time; then random input."""
    world = SW.StepWorld(2, START)
    bits = [0] * V.PREFIX
    home = (world.hero.x, world.hero.y)
    far, at = {}, {}
    back = reach(world)
    for side, key in (('north', lambda p: (p[1], p[0])),
                      ('south', lambda p: (-p[1], p[0])),
                      ('west', lambda p: (p[0], p[1])),
                      ('east', lambda p: (-p[0], p[1]))):
        goal = min(back, key=key)
        far[side] = goal
        there = path_to(back, goal)
        home_back = reach_path(goal, home, world.hero.solid)
        bits += there
        at[len(bits) + 5] = f'far_{side}'
        bits += [0] * 10 + home_back + [0] * 10
    bits += random_bits(2, ROUTE_02)
    for b in bits:
        world.update(b)
    return [{'name': 'Moss Gate', 'room': START, 'bits': bits,
             'pokes': {}, 'far': far, 'at': at}], world


def reach_path(frm, to, solid):
    w = SW.StepWorld(2, START, *frm)
    w.hero.solid = solid
    return path_to(reach(w), to)


def openings(name):
    """The sides of a room with an opening (a free cell in that side
    of the outer ring of cells: msx_model.solid_cells) and those with
    a door (its cells, shut)."""
    cells = msx_model.solid_cells(name, False)
    ring = {'north': cells[:32], 'south': cells[19 * 32:],
            'west': cells[::32], 'east': cells[31::32]}
    return ({s for s in SIDES if 0 in ring[s]},
            {s for s in SIDES if W.DOOR_CELL in ring[s]})


def cross(world, side):
    """The inputs that take the explorer out through `side`, or None."""
    try:
        return RT.plan_exit(world, side)
    except ValueError:
        return None


def go(world, bits, path, crossed, side):
    room = world.room
    for b in path:
        world.update(b)
    bits += path
    crossed.append((room, side, world.room))


def explore(world, bits, crossed, done):
    """Depth first: out through every opening of the room not crossed
    yet whose way back is open, the rooms beyond, and back."""
    here = world.room
    for side in SIDES:
        if (here, side) in done:
            continue
        out = cross(world, side)
        if out is None:
            continue
        probe = world.clone()
        for b in out:
            probe.update(b)
        if cross(probe, OPPOSITE[side]) is None:
            continue                    # one way: at the end
        there = probe.room
        done.update({(here, side), (there, OPPOSITE[side])})
        go(world, bits, out, crossed, side)
        explore(world, bits, crossed, done)
        back = cross(world, OPPOSITE[side])
        go(world, bits, back, crossed, OPPOSITE[side])
        assert world.room == here


def one_way(world, done):
    """The inputs to the nearest opening not crossed yet (breadth first
    over the rooms), through it: or None."""
    todo = deque([(world, [])])
    seen = {world.room}
    while todo:
        w, path = todo.popleft()
        for side in SIDES:
            out = cross(w, side)
            if out is None:
                continue
            if (w.room, side) not in done:
                return path + [(side, out)]
            probe = w.clone()
            for b in out:
                probe.update(b)
            if probe.room not in seen:
                seen.add(probe.room)
                todo.append((probe, path + [(side, out)]))
    return None


def route_03():
    """Every room from its own cartridge (the Moss Gate first): every
    opening not crossed yet, out and back, depth first; then the
    nearest opening still not crossed (its way back a shut door), one
    way; then random input."""
    segs, done = [], set()
    rooms = sorted(msx_model.rooms())
    for n in [START] + [r for r in rooms if r != START]:
        world = SW.StepWorld(3, n)
        bits, crossed = [0] * V.PREFIX, []
        for b in bits:
            world.update(b)
        explore(world, bits, crossed, done)
        way = one_way(world, done)
        if way:
            for side, out in way:
                done.add((world.room, side))
                go(world, bits, out, crossed, side)
        extra = random_bits(300 + n, ROUTE_03)
        for b in extra:
            world.update(b)
        segs.append({'name': f'room {n:02}', 'room': n, 'bits':
                     bits + extra, 'pokes': {}, 'crossed': crossed,
                     'rooms': world.changes})
    return segs, None


def route_04():
    """The walking game: the steps of the whole game without the
    fights, to VICTORY; then random input."""
    world = SW.StepWorld(4, START)
    bits = [0] * V.PREFIX
    for b in bits:
        world.update(b)
    for st in GAME_STEPS:
        if st[0] == 'exit':
            path = RT.plan_exit(world, st[1])
        elif st[0] == 'get':
            path = RT.plan_get(world, st[1], st[2])
        else:
            joy = RT.PUSH[st[1]]
            path = RT.plan_push(world, st[1])
            path += [joy | (F if (k // 8) % 2 else 0)
                     for k in range(st[2])] + [0]
        for b in path:
            world.update(b)
        bits += path
    assert world.ended == W.ENDED_WON, 'the walking game does not end'
    after = random_bits(4, AFTER)
    return [{'name': 'the walking game', 'room': START,
             'bits': bits + after, 'pokes': {}}], world


def route_05():
    """The whole game of the test of 1.0, to VICTORY; GAME OVER without
    help; each then random input."""
    game = S1.planned_game(V)
    defeat = S1.alone_defeat(V)
    return [{'name': 'the whole game', 'room': START,
             'bits': game + random_bits(5, AFTER), 'pokes': {}},
            {'name': 'defeat', 'room': START,
             'bits': defeat + random_bits(6, AFTER), 'pokes': {}}], None


def route_potion():
    """04a: the energy put at 3 in memory (with hud_dirty: the HUD drawn
    again), then the nearest potion, in the Root Cellar: out to the
    south and to the west, onto the potion; then still."""
    world = SW.StepWorld(4, START)
    bits = [0] * V.PREFIX
    for b in bits:
        world.update(b)
    pokes = {V.PREFIX + 1: [('energy', 3), ('hud_dirty', 1)]}
    V.poke_model(world, 'energy', 3)
    for kind, *arg in (('exit', 'south'), ('exit', 'west'),
                       ('get', 12, 2)):
        path = RT.plan_exit(world, *arg) if kind == 'exit' else \
            RT.plan_get(world, *arg)
        for b in path:
            world.update(b)
        bits += path
    bits += [0] * 60
    return [{'name': 'the potion', 'room': START, 'bits': bits,
             'pokes': pokes}], world


def route_bats():
    """05b: the planned game (tests/game_0_5.json) up to the Root
    Cellar; there, by the shortest way, to a place inside the game's
    96 x 90 from its bat but outside the variant's 48 x 45 (60-80
    pixels across), still for 150 passes; then to a place 24-40 pixels
    from it, inside 48 x 45: on the way the bat wakes; then still."""
    world = SW.StepWorld(5, START)
    plan = S1.planned_game(V)
    bits = []
    for b in plan:
        world.update(b)
        bits.append(b)
        if world.room == 4:
            break
    for b in [0] * 30:
        world.update(b)
        bits.append(b)
    bat = next(e for e in world.enemies if e[W.KIND] == W.BAT)

    def far(x, y):
        return abs(x - bat[W.X]), abs(y - bat[W.Y])

    def go(lo, hi):
        back = reach(world)
        spots = [p for p in back if not RT.exit_side(*p) and
                 lo <= far(*p)[0] < hi and far(*p)[1] < 30]
        goal = min(spots, key=lambda p: len(path_to(back, p)))
        for b in path_to(back, goal):
            world.update(b)
            bits.append(b)
    go(60, 80)
    for b in [0] * 150:
        world.update(b)
        bits.append(b)
    go(24, 40)
    for b in [0] * 60:
        world.update(b)
        bits.append(b)
    return [{'name': 'the bat', 'room': START, 'bits': bits,
             'pokes': {}}], world


ROUTES = {'potion': route_potion, 'bats': route_bats}


def routes(step):
    if step == 1:
        return [{'name': 'the first room', 'room': START,
                 'bits': [0] * V.PREFIX + random_bits(1, ROUTE_01),
                 'pokes': {}}], None
    return {2: route_02, 3: route_03, 4: route_04, 5: route_05,
            6: route_05}[step]()


def coverage(checks, facts, segs):
    """Step 03: every opening of every room crossed (the model's
    route), both ways but where the way back is a shut door; no door
    crossed."""
    crossed = [c for s in segs for c in s['crossed']]
    out = {(r, side) for r, side, to in crossed}
    links = {(r, to) for r, side, to in crossed}
    missing, doors, n_open = [], [], 0
    for n, name in sorted(msx_model.rooms().items()):
        sides, shut = openings(name)
        n_open += len(sides)
        missing += [f'{n} {s}' for s in sorted(sides) if (n, s) not in out]
        doors += [f'{n} {s}' for s in sorted(shut) if (n, s) in out]
    one = sorted(f'{r}-{to}' for r, to in links if (to, r) not in links)
    facts['openings'] = {'openings': n_open, 'crossings': len(crossed),
                         'one_way': one}
    checks.add(f'the route: every opening of the 16 rooms crossed '
               f'({n_open}), both ways but {len(one)} whose way back is '
               'a shut door; no door crossed', not missing and not doors
               and n_open == 27 and len(one) == 3,
               f'missing {missing}, doors {doors}' if missing or doors
               else f'{len(crossed)} crossings, one way {one}')


# -- the data -----------------------------------------------------------------

def rooms_check(rom, sym):
    """Steps 01-03: verify_0_8.data_check without the doors' tiles (not
    in the cartridge before step 04)."""
    fake = dict(sym)
    problems, n_obj, n_door, n_en = [], 0, 0, 0

    def byte(a):
        return rom[a - 0x4000]
    for n, name in msx_model.rooms().items():
        room = V.dungeon.load_room(name)
        rec = byte(fake['room_table'] + 2 * n) | \
            byte(fake['room_table'] + 2 * n + 1) << 8
        door = V.dungeon.DOOR_NUMBERS[room.door] if room.door else 0
        n_door += bool(door)
        if byte(rec + 1) != door:
            problems.append(f'room {n}: door {byte(rec + 1)}')
        for s in range(2):
            got = tuple(byte(rec + 2 + 4 * s + i) for i in range(3))
            want = (0, 0, 0)
            if s < len(room.objects):
                kind, letter, c, r = room.objects[s]
                want = (room.code(kind, letter), c, r)
                n_obj += 1
            if got != want:
                problems.append(f'room {n} slot {s}: {got}')
        for s in range(W.MAX_ENEMIES):
            got = tuple(byte(rec + 10 + 4 * s + i) for i in range(4))
            want = (0, 0, 0, 0)
            if s < len(room.enemies):
                kind, c, r, axis, fast = room.enemies[s]
                want = (V.dungeon.ENEMIES[kind], c, r,
                        (V.dungeon.AXES[axis] if axis else 0) |
                        (V.dungeon.FAST if fast else 0))
                n_en += 1
            if got != want:
                problems.append(f'room {n} enemy {s}: {got}')
    return problems, n_obj, n_door, n_en


def hero_shapes_check(vram):
    """The explorer's 8 images in two layers in the sprite shapes
    (0-63) = art_pieces.HERO_FRAMES split by msx_model.hero_colour."""
    problems = []
    for shape in list(range(0, 32, 4)) + list(range(32, 64, 4)):
        px = msx_model.sprite_pixels(shape)
        rows = [''.join('#' if (x, y) in px else '.' for x in range(16))
                for y in range(16)]
        want = V.sprite_bytes(rows)
        got = list(vram[0x3800 + 8 * shape:0x3800 + 8 * shape + 32])
        if got != want:
            problems.append(f'shape {shape}')
    return problems


def data(step, checks, facts, rom, sym, state, cb):
    if step >= 4:
        problems, n_obj, n_door, n_en = V.data_check(rom, sym)
        what = 'with the open tiles of the doors'
    else:
        problems, n_obj, n_door, n_en = rooms_check(rom, sym)
        what = 'the doors\' tiles not yet in the cartridge'
    facts['data'] = {'objects': n_obj, 'doors': n_door, 'enemies': n_en}
    checks.add(f'data: the rooms\' records in the cartridge (door, '
               f'objects, enemies) = the room files ({what})',
               not problems and (n_obj, n_door, n_en) == (20, 4, 34),
               problems[0] if problems else
               f'{n_obj} objects, {n_door} doors, {n_en} enemies')
    m = msxsim.MSX(rom, state, cb)
    try:
        m.run_to(sym['frame_ready'], max_t=40 * m.vdp.frame_t)
    except RuntimeError as e:
        # a program that gets lost is a check failed, not an error of
        # the test
        checks.add('frame_ready every pass: the first one after INIT, '
                   'for the data in the VRAM', False, str(e)[:120])
        return
    vram = bytes(m.vdp.vram)
    if step >= 2:
        problems = hero_shapes_check(vram)
        checks.add('data: the explorer\'s 16 sprite shapes in the VRAM '
                   'after INIT = art_pieces.HERO_FRAMES, skin and '
                   'clothes (msx_model.hero_colour)', not problems,
                   ', '.join(problems[:4]))
    if step >= 5:
        problems, pic = V.combat_images_check(vram, rom, sym)
        checks.add('data: the nine images of the combat in the VRAM '
                   'after INIT = art_pieces.COMBAT_FRAMES, their colours '
                   '= msx_model.COMBAT_INKS', not problems,
                   problems[0] if problems else '')
    if step >= 6:
        mc = V.music_check(rom, sym)
        facts['music'] = mc
        checks.add('data: the music in the cartridge = music.json; read '
                   'back = c64/score.py, every note with the PSG\'s '
                   'period; the eight effects = c64/sfx.py',
                   not mc['differ'] and not mc['score'] and
                   not mc['periods_wrong'] and mc['effects_read_back'],
                   f"{mc['bytes']} bytes, notes {mc['notes_played']}")


# -- the pictures -------------------------------------------------------------

def pictures(rom, sym, state, cb, script, pokes, wanted):
    """The VRAM and the VDP's registers at the frame_ready of the
    passes wanted (a plain run of the bench)."""
    m = msxsim.MSX(rom, state, cb)
    m.joy_port = JOY_PORT - 1
    out = {}
    for k, (bits, keys, joy) in enumerate(script, 1):
        if k > max(wanted):
            break
        for name, v in pokes.get(k, ()):
            m.mem[sym[name]] = v
        m.set_input(keys, joy)
        try:
            m.run_to(sym['frame_ready'], max_t=40 * m.vdp.frame_t)
        except RuntimeError:
            break                       # lost: no more pictures
        if k in wanted:
            out[k] = (bytes(m.vdp.vram), list(m.vdp.regs))
    return out


def png(path, vram, regs, hz):
    path.write_bytes(vram2png.png_bytes(vram2png.frame(vram, regs),
                                        vram2png.palette(hz), 2))


def moments(step, seg, events, changes):
    """{pass: name} of the PNGs of a segment."""
    first = {}
    for k, w in events:
        first.setdefault(w, k)
    out = {}
    if step == 1:
        out = {8 * p + 3: f'phase{p}' for p in range(4)}
    elif step == 2:
        out = dict(seg['at'])
    elif step == 3:
        out = {V.PREFIX: 'start', V.PREFIX + 30: 'walk'}
        if changes:
            out[changes[0]['pass']] = 'black'
            out[changes[0]['pass'] + 1] = 'next'
    else:
        for w in ('door', 'object', 'hit', 'blow', 'touch', 'end'):
            if w in first:
                out[first[w] + (0 if w == 'end' else 2)] = w
        if 'end' in first:
            out[min(len(seg['bits']), first['end'] + 100)] = 'after'
    return out


# -- openMSX ------------------------------------------------------------------

def emu(openmsx, step, rom_path, sym, mname, script, pokes, rd, shot=None):
    machine, hz = V.MACHINES[mname]
    rom = Path(rom_path).read_bytes()
    joy = None
    if 'in_joy' in sym:
        joy = openmsx_run.find_in(rom, 0x4000, sym['in_joy'],
                                  (0xDB, 0xA2)) + 2
    return openmsx_run.run(openmsx, rom_path, machine, sym, len(script),
                           rd, inputs=V.inputs_of(script), joy_read=joy,
                           shots=(shot,) if shot else (),
                           pokes=V.pokes_of(pokes, sym), lazy=True,
                           psg_log=step >= 6, joy_port=JOY_PORT,
                           max_seconds=round(10 + len(script) / 30, 2))


def emu_checks(step, m, recs, r):
    """(problem or None, detail): openMSX = the bench every pass."""
    bad = V.emu_compare(recs, r['frames'])
    same, k = V.emu_irq_same(m, r)
    problem = bad or (None if same and k == len(m.irq_log) and
                      not r['too_fast'] and not r['psg_directions']
                      else f'interrupts {k} of {len(m.irq_log)}, too '
                           f'fast {r["too_fast"][:2]}, PSG port A '
                           f'{r["psg_directions"][:1]}')
    detail = f'{len(recs)} passes, {k} interrupts'
    if step >= 6 and problem is None:
        psame, pdet = V.psg_writes_same(m, r)
        problem = None if psame else pdet
        detail += f', {pdet}'
    return problem, detail


def shot_same(path, pics, k, hz):
    """openMSX's screenshot = one of the bench's last 4 pictures
    (lesson 34)."""
    if not path.exists():
        return 'no screenshot'
    got = vram2png.read_png_rgb(path)
    pal = vram2png.palette(hz)
    for j in range(k, k - 4, -1):
        if j not in pics:
            continue
        want = vram2png.frame(*pics[j])
        if all(got[y] == [tuple(pal[x]) for x in want[y]]
               for y in range(len(want))):
            return None
    return 'none of the last 4'


# -- the cartridges -----------------------------------------------------------

def assemble(sjasm, work, room, mode, out):
    """The step's sources in `work` (game/src, game/assets/generated/B)
    assembled as its build does: START_ROOM = room (and SOUND_MODE).
    Returns (rom bytes, symbols) or (None, message)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    src = work / 'game' / 'src'
    gen = work / 'game' / 'assets' / 'generated' / 'B'
    sym = out.with_suffix('.sym')
    args = [sjasm, '--nologo', '--msg=war', f'-DSTART_ROOM={room}',
            f'-i{gen.as_posix()}', f'--raw={out.as_posix()}',
            f'--sym={sym.as_posix()}']
    if (src / 'player.asm').exists():
        args.append(f'-DSOUND_MODE={mode}')
    code, msg = run(args + [(src / 'cryptmorrow.asm').as_posix()], src)
    if code or msg:
        return None, msg
    return out.read_bytes(), read_symbols(sym)


def copy_step(folder, dest):
    if dest.exists():
        shutil.rmtree(dest)
    (dest / 'game' / 'assets').mkdir(parents=True)
    shutil.copytree(folder / 'game' / 'src', dest / 'game' / 'src')
    shutil.copytree(folder / 'game' / 'assets' / 'generated',
                    dest / 'game' / 'assets' / 'generated')


def apply(work, edits):
    """The edits on the step's sources: each line must be there once
    (in the file named, or else in the one file that has it)."""
    src = work / 'game' / 'src'
    for fname, old, new in edits:
        p = src / fname
        if not p.exists() or p.read_text(encoding='ascii').count(old) != 1:
            have = [f for f in sorted(src.glob('*.asm'))
                    if f.read_text(encoding='ascii').count(old) == 1]
            if len(have) != 1:
                return f'{fname}: the line is not there once'
            p = have[0]
        text = p.read_text(encoding='ascii')
        p.write_text(text.replace(old, new), encoding='ascii')
    return None


# -- the test -----------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--step', type=int, required=True, choices=STEPS)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--chain', type=Path, default=CHAIN)
    ap.add_argument('--openmsx')
    ap.add_argument('--no-openmsx', action='store_true')
    ap.add_argument('--sjasmplus')
    ap.add_argument('--no-mutations', action='store_true')
    ap.add_argument('--reference', type=Path)
    ap.add_argument('--machine', choices=sorted(V.MACHINES),
                    help='only this machine (the parts of the virtual '
                    'machine)')
    ap.add_argument('--mutations-only', action='store_true')
    ap.add_argument('--mutation', help='only this mutation')
    ap.add_argument('--no-seeds', action='store_true')
    ap.add_argument('--seeds-only', action='store_true')
    ap.add_argument('--segment', help='only these parts of the route: N '
                    'or FROM-TO (TO excluded; steps 05-06: 0 the whole '
                    'game, 1 GAME OVER; step 03: the rooms in order, the '
                    'Moss Gate first)')
    ap.add_argument('--no-screen', action='store_true',
                    help='the screen not compared every pass (the long '
                    'parts of the virtual machine: declared)')
    ap.add_argument('--folder', type=Path, help='a variant of the step '
                    '(variants/NN-name/ID, D.3): its cartridge and data')
    ap.add_argument('--set', action='append', default=[],
                    help='a change of the models (a variant: the same '
                    'change as in the program)')
    ap.add_argument('--route', choices=sorted(ROUTES),
                    help='a route of a variant instead of the step\'s')
    a = ap.parse_args(argv)
    step, name = a.step, STEPS[a.step]
    FF.apply(a.set)
    if FOLDER:
        FF.music(V, FOLDER)
    out = a.out or CHAIN / 'evidence-workspace' / 'steps' / f'{step:02}'
    out.mkdir(parents=True, exist_ok=True)
    pngs = out / 'png'
    pngs.mkdir(exist_ok=True)
    openmsx = None if a.no_openmsx else find_tool('openmsx', a.openmsx)
    if not a.no_openmsx and not openmsx:
        print('openMSX not found (--no-openmsx for the bench only)')
        return 1
    sjasm = find_tool('sjasmplus', a.sjasmplus)
    cdir = cbios_dir(openmsx)
    if cdir is None:
        print('C-BIOS not found')
        return 1
    folder = FOLDER or a.chain / name
    build = folder / 'game' / 'build'
    rom_path = build / 'cryptmorrow.rom'
    rom = rom_path.read_bytes()
    sym = read_symbols(build / 'cryptmorrow.sym')
    checks, facts = V.Checks(), {'step': name}
    shows = {}
    if step == 6:
        shows['music_speed'] = [V.MUSIC['speed_50'], V.MUSIC['speed_60']]
    tmp = Path(tempfile.mkdtemp(prefix=f'verify_step{step:02}_'))
    try:
        # -- build
        manifest = json.loads((build / 'manifest.json').read_text())
        chain = json.loads((a.chain / 'chain.json').read_text())
        sha = hashlib.sha256(rom).hexdigest()
        want = chain['steps'][name]['rom_sha256']
        facts['cartridge'] = sha[:16]
        if FOLDER:
            checks.add(f'build: {FOLDER.name}/game/build/manifest.json '
                       'without problems; the cartridge = its manifest\'s'
                       ' (built by the folder\'s tools)',
                       not manifest.get('problems') and
                       sha == manifest['roms']['cryptmorrow']['sha256'],
                       f'{sha[:16]}' + (', = the step\'s' if sha == want
                                        else ''))
        else:
            checks.add(f'build: {name}/game/build/manifest.json without '
                       'problems; the cartridge = chain/chain.json\'s',
                       not manifest.get('problems') and sha == want,
                       f'{sha[:16]}')
        states = {mn: json.loads((ROOT / 'game' / 'build' /
                                  f'state_{mn}.json').read_text())
                  for mn in V.MACHINES}
        cbs = {mn: V.cbios_roms(cdir, mn) for mn in V.MACHINES}
        data(step, checks, facts, rom, sym, states['eu'], cbs['eu'])
        # -- the routes
        segs, end_world = ROUTES[a.route]() if a.route else \
            routes(step)
        work = tmp / 'step'
        copy_step(folder, work)
        roms = {START: (rom, sym, rom_path)}
        if step == 3:
            for n in sorted(msx_model.rooms()):
                if n == START:
                    continue
                p = tmp / 'rooms' / f'{n:02}.rom'
                r, s = assemble(sjasm, work, n, 0, p)
                checks.add(f'build: the cartridge of room {n:02} '
                           '(START_ROOM) from the step\'s sources', r,
                           '' if r else str(s))
                if r:
                    roms[n] = (r, s, p)
            # room 1: the step's cartridge, assembled again the same
            p = tmp / 'rooms' / '01.rom'
            r, s = assemble(sjasm, work, START, 0, p)
            checks.add('build: the step\'s sources assembled again with '
                       'START_ROOM = 1 = the step\'s cartridge', r == rom)
        if step == 3:
            coverage(checks, facts, segs)
        facts['routes'] = {}
        for seg in segs:
            seg['script'] = script_of(seg['bits'])
            facts['routes'][seg['name']] = {
                k: v for k, v in seg.items()
                if k in ('room', 'crossed', 'rooms', 'far')}
            facts['routes'][seg['name']]['passes'] = len(seg['bits'])
        if a.segment is None:
            run_segs = segs
        else:
            lo, _, hi = a.segment.partition('-')
            run_segs = segs[int(lo):int(hi) if hi else int(lo) + 1]
        first = run_segs[0] is segs[0]
        checked = [w for w in applicable(step)
                   if not (a.no_screen and w == 'screen')]
        for mname, (machine, hz) in V.MACHINES.items():
            if a.mutations_only or a.machine not in (None, mname):
                continue
            tag = f'{mname} ({hz} Hz)'
            state, cb = states[mname], cbs[mname]
            for seg in run_segs if not a.seeds_only else ():
                r_, s_, p_ = roms.get(seg['room'], roms[START])
                label = f'{tag} {seg["name"]}'
                f = facts.setdefault(f'{mname} {seg["name"]}', {})
                sh = Shows(step)
                m, recs, bad, fr, last, ch, ev = walk(
                    r_, s_, state, cb, step, seg['script'], seg['room'],
                    seg['pokes'], screen=not a.no_screen, shows=sh)
                f.update(fr)
                shows[f'{mname} {seg["name"]}'] = sh.result(fr)
                rules = rules_of(step, m)
                probs = [f'{k}: {e}' for k, e in bad.items() if e]
                many = len(segs) > 4
                if not many:
                    for w in checked:
                        e = bad[w]
                        checks.add(f'{label}: {name_of(step, w)}',
                                   e is None, e or f'{len(recs)} passes')
                else:
                    seg['problems'] = probs
                checks.add(f'{label}: no VRAM access closer than '
                           f'{msxsim.VRAM_GAP} T in the picture, the '
                           'VDP\'s address with interrupts off, no write '
                           'to ROM' + (', PSG R7 10xxxxxx, the PSG with '
                                       'interrupts off' if step >= 6
                                       else ''),
                           not any(rules.values()), str(rules))
                seg[f'run_{mname}'] = (m, recs, ch, ev)
                if step >= 4 and seg['name'] in ('the walking game',
                                                 'the whole game'):
                    ends = [k for k, w in ev if w == 'end']
                    still = ends and ev[-1][0] == ends[0] and \
                        len(recs) - ends[0] >= AFTER
                    checks.add(f'{label}: VICTORY at pass '
                               f'{ends[0] if ends else None}, then '
                               f'{len(recs) - ends[0] if ends else 0} '
                               'passes of input with the room still',
                               still, ', '.join(f'{w} {n}' for w, n in
                                                fr['events'].items()))
                if seg['name'] == 'defeat':
                    ends = [k for k, w in ev if w == 'end']
                    model_end = V.end_pass(seg['script'], {})
                    checks.add(f'{label}: GAME OVER without help at pass '
                               f'{ends[0] if ends else None} (the model: '
                               f'{model_end}), then the room still',
                               ends and ends[0] == model_end and
                               ev[-1][0] == ends[0] and
                               fr['game'][5] == W.ENDED_LOST,
                               f'touches {fr["events"].get("touch")}')
            if len(segs) > 4:
                probs = [f'{s["name"]}: {s["problems"][0]}'
                         for s in run_segs if s['problems']]
                n_ch = sum(len(s[f'run_{mname}'][2]) for s in run_segs)
                rooms = f'the {len(segs)} rooms' if run_segs == segs else \
                    'rooms ' + ', '.join(s['name'][5:] for s in run_segs)
                checks.add(f'{tag} {rooms}, each from its '
                           'cartridge, out through every opening and '
                           f'back, {ROUTE_03} passes of random input '
                           f'({n_ch} changes of room): '
                           + ', '.join(name_of(step, w) for w in checked),
                           not probs, probs[0] if probs else
                           f'{sum(len(s["bits"]) for s in run_segs)} '
                           'passes')
            # -- seeds
            seg = segs[0]
            r_, s_, p_ = roms[seg['room']]
            lasts = {}
            probs = []
            for seed in (1, 2) if first and not a.no_seeds else ():
                m, recs, bad, fr, last, ch, ev = walk(
                    r_, s_, state, cb, step, seg['script'][:SEED_PASSES],
                    seg['room'], seg['pokes'], seed=seed)
                lasts[seed] = last
                probs += [f'seed {seed} {k}: {e}' for k, e in bad.items()
                          if e]
                probs += [f'seed {seed} {k}: {e}' for k, e in
                          rules_of(step, m).items() if e]
            if lasts:
                outside, depth = V.ram_check(lasts)
                facts.setdefault(f'{mname} seeds', {})['stack_depth'] = \
                    depth
                checks.add(
                    f'{tag} {seg["name"]}: the RAM and the VRAM filled at '
                    f'random (two fillings, '
                    f'{len(seg["script"][:SEED_PASSES])} passes): every '
                    'pass = the model; the RAM written only in the areas '
                    'of vars.asm and the stack',
                    not probs and not outside and
                    0 < depth <= V.STACK_ROOM,
                    probs[0] if probs else f'stack {depth} bytes' + (
                        f'; outside {[hex(x) for x in outside[:4]]}'
                        if outside else ''))
            # -- captures and openMSX
            for seg in run_segs if not a.seeds_only else ():
                i = segs.index(seg)
                r_, s_, p_ = roms.get(seg['room'], roms[START])
                m, recs, ch, ev = seg.pop(f'run_{mname}')
                wanted = moments(step, seg, ev, ch)
                if step == 3 and i:
                    wanted = {V.PREFIX: 'start'}
                # openMSX's screenshot: the first moment after pass 8
                # (a run of its own, in real time: the screenshot
                # needs the picture drawn)
                late = [k for k in wanted if k >= 8]
                shot = min(late) if late and i == 0 else None
                if shot:
                    for k in range(shot - 3, shot):
                        wanted.setdefault(k, None)
                pics = pictures(r_, s_, state, cb, seg['script'],
                                seg['pokes'], set(wanted)) \
                    if wanted else {}
                for k, what in sorted(wanted.items()):
                    if what and k in pics:
                        tagp = seg['name'].replace(' ', '_')
                        png(pngs / f'step{step:02}_{mname}_{tagp}_'
                            f'{k:05}_{what}.png', *pics[k], hz)
                if openmsx:
                    rd = tmp / 'runs' / f'{mname}_{i}'
                    r = emu(openmsx, step, p_, s_, mname, seg['script'],
                            seg['pokes'], rd)
                    problem, detail = emu_checks(step, m, recs, r)
                    if len(segs) > 4:
                        seg['emu'] = problem
                    else:
                        checks.add(f'{tag} {seg["name"]}: openMSX = the '
                                   'bench, every pass (RAM, VRAM, VDP and '
                                   'PSG registers, slots, T-states, the '
                                   'interrupts' + (', every write to the '
                                                   'PSG' if step >= 6
                                                   else '') + ')',
                                   problem is None, problem or detail)
                    del r
                    if shot:
                        rd = tmp / 'runs' / f'{mname}_{i}_shot'
                        r = emu(openmsx, step, p_, s_, mname,
                                seg['script'][:shot + 2], seg['pokes'], rd,
                                shot)
                        e = shot_same(rd / f'shot_{shot}.png', pics, shot,
                                      hz)
                        checks.add(f'{tag} {seg["name"]}: openMSX\'s '
                                   f'screenshot of pass {shot} = one of '
                                   'the bench\'s last pictures', e is None,
                                   e or f'pass {shot}')
            if openmsx and len(segs) > 4:
                probs = [f'{s["name"]}: {s["emu"]}' for s in segs
                         if s.get('emu')]
                checks.add(f'{tag} the {len(segs)} rooms: openMSX = the '
                           'bench, every pass', not probs,
                           probs[0] if probs else '')
        # -- mutations
        if not a.no_mutations and a.machine is None:
            mutations(step, sjasm, checks, facts, folder, segs, states,
                      cbs, tmp, a.mutation, a.no_screen)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if a.reference:
        ref = json.loads(a.reference.read_text())['facts']
        mine = json.loads(json.dumps(facts))
        if a.mutation and 'mutations' in ref:     # one of the three
            ref['mutations'] = {k: v for k, v in ref['mutations'].items()
                                if k == a.mutation}
        partial = a.machine or a.mutations_only or a.no_mutations or \
            a.segment is not None or a.no_screen or a.no_seeds or \
            a.seeds_only or a.mutation
        diff = sorted(k for k in set(mine) | (set() if partial else
                                              set(ref))
                      if ref.get(k) != mine.get(k))
        checks.add(f'the facts of the bench = the reference '
                   f'({a.reference})', not diff, ', '.join(diff[:4]))
    report = {'checks': checks.items, 'facts': facts,
              'result': 'FAIL' if checks.failed else 'PASS',
              'shows': shows, 'folder': str(FOLDER) if FOLDER else None,
              'set': a.set, 'route': a.route,
              'failed': len(checks.failed),
              'openmsx': str(openmsx) if openmsx else None,
              'cbios': str(cdir)}
    if a.no_screen:
        report['left_out'] = [name_of(step, 'screen')]
    (out / 'verify_step.json').write_text(json.dumps(report, indent=1)
                                          + '\n', encoding='utf-8')
    print(f'\n{name}: {len(checks.items)} checks, {len(checks.failed)} '
          'failed' + ('' if openmsx else ' (no openMSX)'))
    for c in checks.failed:
        print('FAILED:', c['check'], c['detail'])
    return 1 if checks.failed else 0


def mutations(step, sjasm, checks, facts, folder, segs, states, cbs,
              tmp, only=None, no_screen=False):
    """The step's three mutations, at 50 Hz, on the route named (the
    first segment, or 'defeat'; in step 03 every room's cartridge
    until one stops it)."""
    rom0 = (folder / 'game' / 'build' / 'cryptmorrow.rom').read_bytes()
    facts['mutations'] = {}
    for mu in MUTATIONS:
        if mu[1] != step or only not in (None, mu[0]):
            continue
        mname, must = mu[0], mu[3]
        work = tmp / 'mut'
        copy_step(folder, work)
        err = apply(work, mutation_edits(mu))
        stopped, where = False, err
        if err is None:
            if len(mu) > 4:
                todo = [s for s in segs if s['name'] == mu[4]]
            else:
                todo = segs if step == 3 else segs[:1]
            for seg in todo:
                r, s = assemble(sjasm, work, seg['room'], 0,
                                tmp / 'mut_rom' / 'm.rom')
                if r is None:
                    where = f'not built: {s}'
                    break
                if seg['room'] == START and r == rom0:
                    where = 'the same cartridge'
                    break
                m, recs, bad, fr, last, ch, ev = walk(
                    r, s, states['eu'], cbs['eu'], step, seg['script'],
                    seg['room'], seg['pokes'], until=must,
                    screen=must == 'screen' or not no_screen)
                failed = [k for k, e in bad.items() if e] + \
                    [k for k, e in rules_of(step, m).items() if e]
                if must in failed:
                    stopped = True
                    k = len(recs) + ('reached' in failed)
                    where = f'{seg["name"]}, pass {k}; failed: ' \
                            f'{", ".join(failed)}'
                    break
                where = f'not stopped; failed: {failed}'
        facts['mutations'][mname] = stopped
        checks.add(f'mutation {mname}: stopped by "{must}"', stopped, where)


if __name__ == '__main__':
    sys.exit(main())

"""The cases of the final program that the test of 1.0 does not
meet (Phase D, D.5), played on the final program (chain/08-complete,
the tests' cartridge cryptmorrow_play.rom: the game at once in the Moss
Gate, MUSIC) at 50 and 60 Hz, every pass compared with the models as
the test of 1.0 compares a game (verify_0_8.walk_machine: the room,
the explorer, the game, the combat, the sprite list, the screen, the
variables, the sounds asked, the PSG) and, with openMSX, the bench =
openMSX at every pass.

One game, from the Moss Gate, with the harness of the tests (values
put in the program's memory and, the same pass, in the model):

1. two passes still (openMSX takes no input in the first), then
   down through the Moss Gate's opening into the Crossroads;
2. its skeleton made slow (its byte EN_FAST cleared, as a room
   without the flag would have it: every skeleton of the dungeon is
   fast): it rests on the odd passes (skeleton_step);
3. the explorer put at the west opening, x = 6, facing left: a blow;
   the blade would start at x = 6 - 11: it is drawn at 0
   (show_combat);
4. put at the east opening, x = 232, facing right: a blow; the blade
   would start at 243, past BLADE_MAX_X: it is drawn at 239;
5. out through the west opening into the Root Cellar;
6. under its potion with 7 segments of energy (the HUD shows half a
   segment, hud_bar): the potion gives 2, the bar stops at 8
   (use_object);
7. 1 segment of energy, the explorer put on the bat: a touch takes 2,
   the energy stops at 0 (check_contact), GAME OVER.

The plan is made on the model alone (the inputs and the values put in
memory, pass by pass), then played on the program. Writes
OUT/coverage_cases.json (OUT: editorial/coverage, beside the
register).
Usage: python tests/coverage_cases.py [--out DIR] [--no-openmsx]
           [--openmsx EXE]
Run by tools/exec_coverage.py to measure the instructions executed.

From Cryptmorrow ZX (tests/coverage_cases.py). Standard library and
SkoolKit.
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import verify_1_0 as T1  # noqa: E402  (the test of 1.0, on step 08)
import hero_model as H  # noqa: E402
import msxsim  # noqa: E402
import psg_model as P  # noqa: E402
import world_model as W  # noqa: E402
from msxtools import cbios_dir, find_tool  # noqa: E402

V = T1.V
CROSSROADS, ROOT_CELLAR = 5, 4
AFTER = 10                      # passes after GAME OVER
EN_SIZE, EN_FAST = 9, 8         # combat.asm
HERO = ('hero_x', 'hero_y', 'hero_dir')


def poke_model(world, name, value):
    """The values the plan puts in memory, in the model too."""
    if name in ('hero_x', 'hero_y', 'hero_dir'):
        setattr(world.hero, {'hero_x': 'x', 'hero_y': 'y',
                             'hero_dir': 'dir'}[name], value)
    elif name.startswith('en_fast_'):
        world.enemies[int(name[8:])][W.FAST] = value
    else:
        PLAIN(world, name, value)


PLAIN = V.poke_model


class Plan:
    """The game on the model: inputs, values by pass, marks."""

    def __init__(self):
        self.world = W.World(V.GAME_ROOM)
        self.bits, self.pokes, self.marks = [], {}, {}

    def frame(self, joy=0, **poke):
        n = len(self.bits) + 1
        if poke:
            lst = self.pokes.setdefault(n, [])
            for name, value in poke.items():
                if name == 'hero':
                    for k, v in zip(HERO, value):
                        lst.append((k, v))
                        poke_model(self.world, k, v)
                else:
                    lst.append((name, value))
                    poke_model(self.world, name, value)
                    if name == 'energy':
                        lst.append(('hud_dirty', 1))
        self.bits.append(joy)
        self.world.update(joy)
        return n

    def until(self, joy, done, limit, what):
        for _ in range(limit):
            if done(self.world):
                return len(self.bits)
            self.frame(joy)
        raise SystemExit(f'the plan: {what} not reached')

    def mark(self, name):
        self.marks[name] = len(self.bits) + 1     # the next pass


def plan():
    p = Plan()
    w = p.world
    # two passes without input first: openMSX gets the input of a
    # pass at the frame_ready before it, and pass 1 has none
    p.frame(0)
    p.frame(0)
    p.until(H.JOY_DOWN, lambda w: w.room == CROSSROADS, 300,
            'the Crossroads')
    slot = next(k for k, e in enumerate(w.enemies)
                if e[W.KIND] == W.SKELETON)
    p.slot = slot
    p.mark('slow')
    p.frame(0, **{f'en_fast_{slot}': 0})
    for _ in range(15):
        p.frame(0)
    p.mark('slow_end')
    p.until(0, lambda w: not w.safe, 200, 'no touch')
    p.mark('left')
    p.frame(H.JOY_FIRE, hero=(6, 84, H.DIR_LEFT))
    p.until(0, lambda w: not w.slash, 40, 'the end of the blow')
    p.mark('right')
    p.frame(H.JOY_FIRE, hero=(232, 84, H.DIR_RIGHT))
    p.until(0, lambda w: not w.slash, 40, 'the end of the blow')
    p.frame(H.JOY_LEFT, hero=(6, 84, H.DIR_LEFT))
    p.until(H.JOY_LEFT, lambda w: w.room == ROOT_CELLAR, 20,
            'the Root Cellar')
    p.until(0, lambda w: not w.safe, 200, 'no touch')
    room = w.rooms[ROOT_CELLAR]
    potion = next(s for s, (kind, letter, c, r) in enumerate(room.objects)
                  if room.code(kind, letter) == W.KIND_POTION)
    kind, letter, c, r = room.objects[potion]
    # below the potion's metatile, facing up: two passes up take it
    x = 16 * c + 8 - W.HIT_X
    y = 16 * r + W.ROOM_TOP + 16 + 2 - W.HIT_Y
    p.mark('potion')
    p.frame(H.JOY_UP, hero=(x, y, H.DIR_UP), energy=7)
    p.marks['potion_taken'] = p.until(
        H.JOY_UP, lambda w: (ROOT_CELLAR, potion) in w.taken, 10,
        'the potion')
    if w.energy != W.ENERGY_MAX:
        raise SystemExit('the plan: the potion did not fill the bar')
    p.until(0, lambda w: not w.safe, 200, 'no touch')
    bat = next(e for e in w.enemies if e[W.KIND] == W.BAT)
    p.mark('touch')
    p.frame(0, hero=(bat[W.X], bat[W.Y], w.hero.dir), energy=1)
    p.marks['over'] = p.until(0, lambda w: w.ended, 30, 'GAME OVER')
    for _ in range(AFTER):
        p.frame(0)
    return p


def play(openmsx, cdir, p, sym):
    """The plan on the program at 50 and 60 Hz: every pass = the model
    (and = openMSX); the facts read in the program's memory after every
    pass."""
    traces = []
    run_to = msxsim.MSX.run_to
    en, sl = sym['enemies'], sym['spr_list']

    def traced(self, stop, max_t=None):
        mem = self.mem
        energy_in = mem[sym['energy']]      # with the pokes of the pass
        used = run_to(self, stop, max_t)
        trace = getattr(self, 'trace', None)
        if trace is None:
            trace = self.trace = []
            traces.append(trace)
        trace.append({
            'energy_in': energy_in,
            'turn': mem[sym['turn']],
            'energy': mem[sym['energy']],
            'ended': mem[sym['game_ended']],
            'slash': mem[sym['slash_timer']],
            'hero_x': mem[sym['hero_x']],
            'hud_bar': list(mem[sym['hud_row'] + 7:sym['hud_row'] + 11]),
            'list': list(mem[sl:sl + 4]),
            'skeleton': list(mem[en + EN_SIZE * p.slot:
                                 en + EN_SIZE * (p.slot + 1)])})
        return used
    checks, report = V.Checks(), {}
    script = V.script_of(V.runs_of(p.bits), V.SOURCES)
    msxsim.MSX.run_to = traced
    try:
        for mname in V.MACHINES:
            hz = V.MACHINES[mname][1]
            f = report.setdefault(f'{mname}_{hz}hz', {})
            n0 = len(traces)
            V.walk_machine(openmsx, cdir, checks, f, mname,
                           f'{mname} ({hz} Hz)', script, p.pokes, (None,),
                           'the cases of D.5', P.MODE_MUSIC)
            f['seen'] = seen(traces[n0], p, sym)
    finally:
        msxsim.MSX.run_to = run_to
    return checks, report


def seen(trace, p, sym):
    """The facts of the cases, read in the program's memory (trace[k -
    1]: after pass k)."""
    k = p.marks
    sk = [trace[n - 1]['skeleton'] for n in range(k['slow'],
                                                 k['slow_end'] + 1)]
    turns = [trace[n - 1]['turn'] for n in range(k['slow'],
                                                k['slow_end'] + 1)]
    moved = [i for i in range(1, len(sk)) if sk[i][1:4] != sk[i - 1][1:4]]
    left, right = trace[k['left'] - 1], trace[k['right'] - 1]
    taken = k['potion_taken']
    before = trace[k['potion'] - 1]
    over = trace[k['over'] - 1]
    return {
        'skeleton_fast': sk[0][EN_FAST],
        'skeleton_passes': len(sk) - 1,
        'skeleton_moves': len(moved),
        'skeleton_moved_on_odd_turns': [turns[i] for i in moved
                                        if turns[i] & 1],
        'left_hero_x': left['hero_x'], 'left_blade_x': left['list'][1],
        'left_blade_out': left['slash'] > W.BLADE_UNTIL,
        'right_hero_x': right['hero_x'],
        'right_blade_x': right['list'][1],
        'right_blade_out': right['slash'] > W.BLADE_UNTIL,
        'potion_energy_before': trace[taken - 1]['energy_in'],
        'potion_bar_before': before['hud_bar'],
        'potion_energy_after': trace[taken - 1]['energy'],
        'touch_energy_before': trace[k['over'] - 1]['energy_in'],
        'over_energy': over['energy'], 'over_ended': over['ended']}


def good(s, sym):
    bar = [sym['BAR_FULL']] * 3 + [sym['BAR_HALF']]
    return (s['skeleton_fast'] == 0 and s['skeleton_moves'] > 0 and
            not s['skeleton_moved_on_odd_turns'] and
            s['left_hero_x'] == 6 and s['left_blade_out'] and
            s['left_blade_x'] == 0 and
            s['right_hero_x'] == 232 and s['right_blade_out'] and
            s['right_blade_x'] == sym['BLADE_MAX_X'] and
            s['potion_energy_before'] == 7 and
            s['potion_bar_before'] == bar and
            s['potion_energy_after'] == W.ENERGY_MAX and
            s['touch_energy_before'] == 1 and s['over_energy'] == 0 and
            s['over_ended'] == W.ENDED_LOST)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', type=Path,
                    default=ROOT / 'editorial' / 'coverage')
    ap.add_argument('--openmsx')
    ap.add_argument('--no-openmsx', action='store_true')
    args = ap.parse_args(argv)
    openmsx = None if args.no_openmsx else find_tool('openmsx',
                                                     args.openmsx)
    if not args.no_openmsx and not openmsx:
        print('openMSX not found (--no-openmsx for the bench only)')
        return 1
    tmp = Path(tempfile.mkdtemp(prefix='coverage_cases_'))
    try:
        T1.on_step(8, tmp)
        V.RUNS = tmp / 'runs'
        V.RUNS.mkdir()
        rom_files = V.rom_files
        rom, sym = rom_files(V.GAMES[P.MODE_MUSIC])
        extra = {f'en_fast_{s}': sym['enemies'] + EN_SIZE * s + EN_FAST
                 for s in range(W.MAX_ENEMIES)}
        V.rom_files = lambda name, *a: (
            rom_files(name, *a)[0], {**rom_files(name, *a)[1], **extra})
        V.poke_model = poke_model
        p = plan()
        checks, report = play(openmsx, cbios_dir(openmsx), p, sym)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok = not checks.failed
    for name, f in report.items():
        s = f['seen']
        g = good(s, sym)
        checks.add(f'{name}: the slow skeleton rested on the odd passes '
                   f'({s["skeleton_moves"]} moves in '
                   f'{s["skeleton_passes"]} passes); the blade at x '
                   f'{s["left_blade_x"]} and {s["right_blade_x"]}; the bar '
                   f'with half a segment at 7; the potion '
                   f'{s["potion_energy_before"]} -> '
                   f'{s["potion_energy_after"]}; the touch '
                   f'{s["touch_energy_before"]} -> {s["over_energy"]}, '
                   'GAME OVER', g)
        ok &= g
    report = {'frames': len(p.bits), 'marks': p.marks,
              'pokes': {str(n): v for n, v in sorted(p.pokes.items())},
              'openmsx': bool(openmsx), 'machines': report,
              'checks': checks.items,
              'result': 'PASS' if ok else 'FAIL'}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'coverage_cases.json').write_text(
        json.dumps(report, indent=1) + '\n', encoding='ascii')
    print(f"{len(checks.items)} checks, {len(checks.failed)} failed")
    print(f"COVERAGE CASES {report['result']}")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

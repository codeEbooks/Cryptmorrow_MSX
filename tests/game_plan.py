"""The whole game planned with the models (milestone 0.5): the inputs
that win it, fighting the enemies on the way.

The planner plays the game in tests/world_model.py, frame by frame,
and writes down the joystick of every frame; the test replays those
inputs in the program and compares it with the model. The program is
never searched or aimed at: it only gets the inputs.

A plan is a list of steps:
  ('exit', side)          walk out of the room through that side
  ('get', column, row)    walk onto the object of that metatile
  ('push', side, frames)  walk into the door on that side, then keep
                          pushing (FIRE every other 8 frames)
  ('energy', n)           the test puts n in energy (and marks the HUD)
  ('clear',)              defeat every enemy of the room (fight)
Before every step but 'energy' and 'clear' the enemies still alive in
the room are fought, so the explorer walks only in empty rooms.

fight(world, n): before every frame the fighter tries short moves -
stand, or walk up, down, left or right for 1, 4, 10 or 20 frames -
each followed by a simple policy (strike when the enemy is near the
point of the blow, walk to a place where the enemy will come within a
sword's length, turn towards it) for HORIZON frames, and takes the
first frame of the best: least energy lost, then fewest frames with
an enemy touching the explorer (counted also while it cannot be
hurt), then the enemy defeated soonest, then more hits, then closer
to the waiting place. It strikes
when a trial copy of the world shows that the blow will hit. (As the
planner of the C64 game.)

Copied from Cryptmorrow ZX (tests/game_plan.py, as in its milestone
0.6) and adapted to the MSX in milestone 0.5: the world is the MSX's
tests/world_model.py (World(room)); the plan goes to
tests/game_0_5.json. The steps and the fighter are the ZX's.
Standard library only.
"""
import random

import hero_model as H
import route as RT
import world_model as W

U, D, L, R, F = H.JOY_UP, H.JOY_DOWN, H.JOY_LEFT, H.JOY_RIGHT, H.JOY_FIRE
HORIZON = 40
CANDIDATES = [[0]] + [[j] * k for j in (U, D, L, R) for k in (1, 4, 10, 20)]
FACE = {H.DIR_DOWN: D, H.DIR_UP: U, H.DIR_LEFT: L, H.DIR_RIGHT: R}


def alive(e):
    return e[W.KIND] and not e[W.DUST]


def blow_hits(world, n):
    """A trial copy: FIRE now, then the blade's frames standing still;
    True if enemy n is hit."""
    c = world.clone()
    hp = c.enemies[n][W.HP]
    c.update(F)
    for _ in range(W.BLADE_FRAMES):
        e = c.enemies[n]
        if not e[W.KIND] or e[W.DUST] or e[W.HP] < hp or c.ended:
            break
        c.update(0)
    e = c.enemies[n]
    return (e[W.HP] < hp or e[W.DUST] or not e[W.KIND]) and not c.ended


def cell_of(x, y):
    """The cell of the middle of a hitbox at sprite corner (x, y)."""
    return ((y + W.HIT_Y - 16) // 8) * 32 + (x + W.HIT_X) // 8


def patrol(world, e):
    """The ends of a skeleton's patrol: (lowest, highest) x for one
    walking across, y for one walking up and down."""
    probe = list(e)
    across = e[W.DIR] in (H.DIR_LEFT, H.DIR_RIGHT)
    ends = []
    for d in ((H.DIR_LEFT, H.DIR_RIGHT) if across else
              (H.DIR_UP, H.DIR_DOWN)):
        probe[W.X], probe[W.Y], probe[W.DIR] = e[W.X], e[W.Y], d
        for _ in range(256):
            if world.enemy_blocked(probe):
                break
            world.move(probe, d)
        ends.append(probe[W.X] if across else probe[W.Y])
    return ends


def spot(world, n):
    """Where the explorer waits for enemy n, and the way it faces: a
    skeleton walking across is struck from above (or below) its row,
    one walking up and down from beside its column, at the place of
    its patrol nearest to the explorer, where it will come by; a bat,
    which comes to the explorer, a sword's length from it along the
    longer axis."""
    h, e = world.hero, world.enemies[n]
    if e[W.KIND] == W.SKELETON:
        lo, hi = patrol(world, e)
        if e[W.DIR] in (H.DIR_LEFT, H.DIR_RIGHT):
            x = min(max(h.x, lo), hi)
            options = [(x, e[W.Y] - 11, H.DIR_DOWN),
                       (x, e[W.Y] + 14, H.DIR_UP)]
        else:
            y = min(max(h.y, lo), hi)
            options = [(e[W.X] - 13, y + 1, H.DIR_RIGHT),
                       (e[W.X] + 13, y + 1, H.DIR_LEFT)]
        free = [o for o in options if free_at(world, o[0], o[1])]
        if free:
            return min(free, key=lambda o: abs(o[0] - h.x) +
                       abs(o[1] - h.y))
    dx, dy = e[W.X] - h.x, e[W.Y] - h.y
    if abs(dx) >= abs(dy):
        return (e[W.X] - (13 if dx > 0 else -13), e[W.Y] + 1,
                H.DIR_RIGHT if dx > 0 else H.DIR_LEFT)
    return (e[W.X] - 2, e[W.Y] - (12 if dy > 0 else -15),
            H.DIR_DOWN if dy > 0 else H.DIR_UP)


def free_at(world, x, y):
    if not (8 <= x <= 232 and 18 <= y <= 150):
        return False
    probe = H.HeroModel(world.hero.solid, x, y)
    return not any(probe.is_solid(x + dx, y + dy)
                   for dx in (H.BOX_LEFT, H.BOX_RIGHT)
                   for dy in (H.BOX_TOP, H.BOX_BOTTOM))


def field(world, target):
    """Steps from every free cell of the room to the target cell."""
    solid = world.hero.solid
    dist = {target: 0}
    todo = [target]
    for c in todo:
        r, k = divmod(c, 32)
        for nr, nk in ((r + 1, k), (r - 1, k), (r, k + 1), (r, k - 1)):
            if 0 <= nr < 20 and 0 <= nk < 32:
                nc = nr * 32 + nk
                if nc not in dist and not solid[nc]:
                    dist[nc] = dist[c] + 1
                    todo.append(nc)
    return dist


def toward(world, n, plan=None):
    """The policy's move: along the field to the waiting spot, then
    to it pixel by pixel, then turned the right way (then nothing)."""
    h = world.hero
    if plan is None:
        tx, ty, face = spot(world, n)
        dist = field(world, cell_of(tx, ty))
    else:
        tx, ty, face, dist = plan
    here = cell_of(h.x, h.y)
    if here in dist and dist[here] > 1:
        r, k = divmod(here, 32)
        best = None
        for joy, c in ((D, here + 32), (U, here - 32), (R, here + 1),
                       (L, here - 1)):
            v = dist.get(c)
            if v is not None and (best is None or v < best[0]):
                best = (v, joy)
        if best and best[0] < dist[here]:
            return best[1]
    if abs(ty - h.y) > 1:
        return D if ty > h.y else U
    if abs(tx - h.x) > 1:
        return R if tx > h.x else L
    return FACE[face] if h.dir != face else 0


def strike_now(world, n):
    """The policy's guess (no trial copy): the enemy near the point of
    a blow in the direction the explorer faces."""
    h, e = world.hero, world.enemies[n]
    d = h.dir
    px, py = h.x + W.STRIKE_X[d], h.y + W.STRIKE_Y[d]
    return abs(e[W.X] - px) < W.REACH_X + 3 and \
        abs(e[W.Y] - py) < W.REACH_Y + 3


def policy(world, n, plan=None):
    if world.blade_out() or world.fire_held:
        return 0
    if strike_now(world, n):
        return F
    return toward(world, n, plan)


def rollout(world, n, moves, horizon=HORIZON, plan=None):
    c = world.clone()
    energy, room = c.energy, c.room
    hits, done = 0, None
    hp = c.enemies[n][W.HP]
    danger = 0
    for k in range(horizon):
        joy = moves[k] if k < len(moves) else policy(c, n, plan)
        c.update(joy)
        if c.room != room or c.ended:
            break
        hx, hy = c.hero.x, c.hero.y
        danger += any(alive(e) and c.near(hx, hy, e)
                      for e in c.enemies)   # a touch, even when safe
        e = c.enemies[n]
        if e[W.HP] < hp:
            hits += hp - e[W.HP]
            hp = e[W.HP]
        if not alive(e):
            done = k
            break
    h = c.hero
    if plan:
        tx, ty, _, dist = plan
        far = dist.get(cell_of(h.x, h.y), 99) * 8 + abs(tx - h.x) + \
            abs(ty - h.y)
    else:
        e = c.enemies[n]
        far = abs(e[W.X] - h.x) + abs(e[W.Y] - h.y)
    left = c.room != room or c.ended == W.ENDED_LOST
    return (-(energy - c.energy) - (100 if left else 0), -danger,
            -(done if done is not None else 1000), hits, -far)


def fight(world, n, inputs, max_frames=1500):
    """Defeat enemy n of the room; the inputs are appended."""
    start = len(inputs)
    while alive(world.enemies[n]) and len(inputs) - start < max_frames:
        if world.ended:
            raise ValueError(f'room {world.room}: the game ended in a '
                             'fight')
        if world.blade_out() or world.fire_held:
            joy = 0
        elif blow_hits(world, n):
            joy = F
        else:
            tx, ty, face = spot(world, n)
            plan = (tx, ty, face, field(world, cell_of(tx, ty)))
            first = [[toward(world, n, plan)]]  # wins the ties
            joy = max(first + CANDIDATES, key=lambda m: rollout(
                world, n, m, plan=plan))[0]
        room = world.room
        world.update(joy)
        inputs.append(joy)
        if world.room != room:
            raise ValueError(f'room {room}: the fight left the room')
    if alive(world.enemies[n]):
        raise ValueError(f'room {world.room}: enemy {n} still alive')
    while world.blade_out() or world.fire_held:
        world.update(0)
        inputs.append(0)


def clear(world, inputs):
    """Fight the enemies of the room: first the bats already awake
    (they come for the explorer), then the nearest."""
    while True:
        h = world.hero
        left = []
        for k, e in enumerate(world.enemies):
            if not alive(e):
                continue
            fx, fy, _, _ = world.measure(h.x, h.y, e)
            awake = e[W.KIND] == W.BAT and fx < W.CHASE_X and \
                fy < W.CHASE_Y
            left.append((not awake, fx + fy, k))
        if not left:
            return
        fight(world, min(left)[2], inputs)


def plan_game(steps, after=150, seed=5):
    """The inputs of the whole game; the energy put in memory (frame
    -> value); what each step did."""
    world = W.World()
    inputs, pokes, done = [], {}, []
    for step in steps:
        kind = step[0]
        n0, e0 = len(inputs), world.energy
        if kind == 'energy':
            pokes[len(inputs)] = step[1]
            world.energy = step[1]
        else:
            clear(world, inputs)
            path = []
            if kind == 'exit':
                path = RT.plan_exit(world, step[1])
            elif kind == 'get':
                path = RT.plan_get(world, step[1], step[2])
            elif kind == 'push':
                path = RT.plan_push(world, step[1])
                joy = path[-1]
                path += [joy | (F if (k // 8) % 2 else 0)
                         for k in range(step[2])]
                path.append(0)          # (as the ZX's plan)
            for joy in path:
                world.update(joy)
                inputs.append(joy)
        done.append({'step': ' '.join(map(str, step)),
                     'frames': len(inputs) - n0, 'room': world.room,
                     'doors': world.doors, 'keys': world.key_set,
                     'seals': world.seals, 'score': world.score,
                     'energy': world.energy, 'energy_before': e0,
                     'taken': len(world.taken), 'ended': world.ended})
        if world.ended == W.ENDED_LOST:
            raise ValueError(f'GAME OVER at step {step}')
    rnd = random.Random(seed)
    extra = []
    choices = [0, U, D, L, R, F, U | F, D | F, L | F, R | F]
    while len(extra) < after:
        extra += [rnd.choice(choices)] * rnd.randint(4, 30)
    for joy in extra[:after]:
        world.update(joy)
    return inputs + extra[:after], pokes, done, world


# The whole game of milestone 0.5: the steps of 0.4 (the doors that
# resist, the objects, the doors, the portal), with the fights now
# before every step. No energy is put in memory: the enemies take it.
# The ZX's steps of its milestone 0.6.
GAME_STEPS = [
    ('push', 'north', 40),      # 1 MOSS GATE: the portal, no seals
    ('exit', 'south'),          # 1 -> 5 CROSSROADS
    ('exit', 'west'),           # 5 -> 4 ROOT CELLAR
    ('push', 'south', 40),      # door A, no key
    ('get', 12, 2),             # potion
    ('exit', 'north'),          # 4 -> 0 BONE PIT
    ('get', 12, 3),             # treasure
    ('get', 3, 7),              # potion
    ('exit', 'south'),          # 0 -> 4
    ('exit', 'east'),           # 4 -> 5
    ('exit', 'east'),           # 5 -> 6 LONG GALLERY
    ('get', 13, 8),             # treasure
    ('exit', 'north'),          # 6 -> 2 THE OLD WELL
    ('get', 3, 2),              # key A
    ('get', 12, 2),             # treasure
    ('exit', 'south'),          # 2 -> 6
    ('exit', 'west'),           # 6 -> 5
    ('exit', 'west'),           # 5 -> 4
    ('push', 'south', 0),       # door A opens: key A used up
    ('exit', 'south'),          # 4 -> 8 OSSUARY
    ('get', 12, 7),             # potion
    ('exit', 'south'),          # 8 -> 12 CATACOMBS
    ('get', 12, 2),             # key B
    ('get', 3, 7),              # treasure
    ('exit', 'east'),           # 12 -> 13 BONE SHRINE
    ('get', 8, 3),              # seal 1
    ('exit', 'west'),           # 13 -> 12
    ('exit', 'north'),          # 12 -> 8
    ('exit', 'north'),          # 8 -> 4: door A drawn open
    ('exit', 'east'),           # 4 -> 5
    ('exit', 'south'),          # 5 -> 9 SUNKEN HALL
    ('push', 'east', 40),       # door C: key B is not its key
    ('exit', 'north'),          # 9 -> 5
    ('exit', 'east'),           # 5 -> 6
    ('push', 'east', 0),        # door B opens
    ('exit', 'east'),           # 6 -> 7 FLOODED STAIR
    ('get', 12, 2),             # potion
    ('exit', 'north'),          # 7 -> 3 BLACK CISTERN
    ('get', 7, 5),              # key C
    ('get', 12, 7),             # potion
    ('exit', 'south'),          # 3 -> 7
    ('exit', 'south'),          # 7 -> 11 DROWNED SHRINE
    ('get', 8, 4),              # seal 2
    ('get', 3, 5),              # treasure
    ('exit', 'north'),          # 11 -> 7
    ('exit', 'west'),           # 7 -> 6
    ('exit', 'west'),           # 6 -> 5
    ('exit', 'south'),          # 5 -> 9
    ('get', 7, 7),              # treasure
    ('push', 'east', 0),        # door C opens
    ('exit', 'east'),           # 9 -> 10 AMBER HALL
    ('get', 12, 2),             # potion
    ('exit', 'south'),          # 10 -> 14 TREASURY
    ('get', 3, 2),              # treasure
    ('get', 12, 2),             # treasure
    ('exit', 'east'),           # 14 -> 15 SUN VAULT
    ('get', 7, 4),              # seal 3
    ('exit', 'west'),           # 15 -> 14
    ('exit', 'north'),          # 14 -> 10
    ('exit', 'west'),           # 10 -> 9
    ('exit', 'north'),          # 9 -> 5
    ('exit', 'north'),          # 5 -> 1 MOSS GATE
    ('push', 'north', 0),       # the portal opens
    ('exit', 'north'),          # out through it: VICTORY
]
PLAN_FILE = 'game_0_5.json'


def encode(inputs):
    """Run-length: [[joy, count], ...]."""
    out = []
    for joy in inputs:
        if out and out[-1][0] == joy:
            out[-1][1] += 1
        else:
            out.append([joy, 1])
    return out


def decode(runs):
    return [joy for joy, n in runs for _ in range(n)]


def main():
    """Plan the whole game again and write tests/game_0_5.json (the
    test replays it)."""
    import json
    import time
    from pathlib import Path
    t = time.time()
    inputs, pokes, steps, world = plan_game(GAME_STEPS)
    out = Path(__file__).resolve().parent / PLAN_FILE
    data = {'about': 'the whole game of milestone 0.5, planned by '
                     'tests/game_plan.py with the models',
            'frames': len(inputs), 'inputs': encode(inputs),
            'pokes': {str(k): v for k, v in pokes.items()},
            'steps': steps,
            'final': dict(world.hud(), doors=world.doors,
                          taken=len(world.taken), ended=world.ended)}
    out.write_bytes((json.dumps(data, separators=(',', ':')) + '\n')
                    .encode('ascii'))
    print(f'{len(inputs)} frames, {data["final"]}, '
          f'{time.time() - t:.0f} s -> {out}')


if __name__ == '__main__':
    main()

"""A player that is not a plan (milestone 1.0): it plays the world
model (tests/world_model.py) and writes down what it pressed, so that
the cartridge can be given the same passes and compared with the
models, pass by pass.

In a game it chases the nearest enemy of the room and strikes when it
is near, or, with no enemy left, walks out of the room by a side the
planner (route.plan_exit) can reach; now and then it does something
at random. After GAME_CAP passes without an end it stops striking and
walks into the enemies, so that every game ends. Around the games
(tests/sessions_1_0.py) it waits on the opening screen or skips it
with FIRE, moves the cursor of the sound on the title a few times and
starts with FIRE, waits on the end screen and presses FIRE.

Copied from Cryptmorrow ZX (tests/bot.py, milestone 1.0) and adapted
to the MSX: the world model of the MSX tests, the passes of the
cartridge's states. A seed makes it repeat itself. Standard library
only.
"""
import random

import hero_model as H
import route as RT
import world_model as W

U, D, L, R, F = H.JOY_UP, H.JOY_DOWN, H.JOY_LEFT, H.JOY_RIGHT, H.JOY_FIRE
CHOICES = [0, R, L, D, U, F, R | U, R | D, L | U, L | D, R | F, U | F]
SIDES = ['north', 'south', 'east', 'west']
GAME_CAP = 6000             # passes; then it walks into the enemies
GAME_MAX = 12000            # a game longer than this: a fault


def toward(dx, dy):
    if abs(dx) >= abs(dy):
        return R if dx > 0 else L
    return D if dy > 0 else U


def next_inputs(world, rnd, reckless):
    """The next few inputs of a game."""
    if not reckless and rnd.random() < 0.15:
        return [rnd.choice(CHOICES)] * rnd.randint(4, 20)
    hx, hy = world.hero.x, world.hero.y
    alive = [e for e in world.enemies
             if e[W.KIND] and not e[W.DUST]]
    if alive:
        e = min(alive, key=lambda e: abs(e[W.X] - hx) + abs(e[W.Y] - hy))
        dx, dy = e[W.X] - hx, e[W.Y] - hy
        joy = toward(dx, dy)
        if reckless:
            return [joy] * rnd.randint(2, 6)
        if abs(dx) <= 20 and abs(dy) <= 20:
            return [joy, joy, F, 0, 0, 0]
        return [joy] * rnd.randint(4, 12)
    sides = SIDES[:]
    rnd.shuffle(sides)
    for side in sides:
        try:
            path = RT.plan_exit(world, side)
        except ValueError:
            continue
        return path + [path[-1]] * 4
    return [rnd.choice(CHOICES)] * 8


def play(seed, room, prefix=0):
    """The bits of a whole game from its first pass to its end (the
    pass that ends it included), `prefix` passes without input first,
    and the world model at the end."""
    rnd = random.Random(seed)
    world = W.World(room)
    bits, queue = [0] * prefix, []
    for _ in range(prefix):
        world.update(0)
    while not world.ended:
        if len(bits) >= GAME_MAX:
            raise ValueError(f'seed {seed}: no end in {GAME_MAX} passes')
        if not queue:
            queue = next_inputs(world, rnd, len(bits) >= GAME_CAP)
        joy = queue.pop(0)
        room_before = world.room
        world.update(joy)
        bits.append(joy)
        if world.room != room_before:
            queue = []
    return bits, world


def title_moves(rnd, mode, modes):
    """The title: a wait, the cursor moved up and down a few times
    (each press held 4 passes, let go 4), FIRE pressed and let go.
    Returns (bits, the mode chosen); modes: (first, last)."""
    first, last = modes
    bits = [0] * rnd.randint(5, 60)
    for _ in range(rnd.randint(0, 4)):
        b = rnd.choice([U, D])
        bits += [b] * 4 + [0] * rnd.randint(4, 20)
        mode = max(first, mode - 1) if b == U else min(last, mode + 1)
    bits += [F] * 3 + [0]
    return bits, mode


def end_wait(rnd, delay):
    """The end screen: FIRE now and then while it does not count yet,
    the piece of the end to its end, then FIRE pressed and let go."""
    bits = [0] * rnd.randint(10, 60)
    if rnd.random() < 0.5:
        bits += [F] * 4 + [0] * 4
    bits += [0] * (delay + rnd.randint(0, 200))
    return bits + [F] * 3 + [0]

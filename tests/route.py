"""Routes through the dungeon for the tests: the joystick input that
takes the explorer out of a room through a given side.

plan_exit(world, side) searches, breadth first, the positions the
explorer can reach in its room (one pixel a frame, with the rules of
hero_model) and returns the shortest list of inputs, one per frame,
whose last one makes it leave through `side` ('north', 'south',
'west', 'east'). It does not move the world. tour(world, sides)
chains several exits and moves the world along. From milestone 0.4
also plan_get (walk onto an object's metatile) and plan_push (walk
into a door).

Copied from Cryptmorrow ZX (tests/route.py) and adapted to the MSX in
milestones 0.3 and 0.4: the room starts at line 16; free_spot searches
the MSX room. Standard library only.
"""
from collections import deque

import hero_model as H
import world_model as W

MOVES = (H.JOY_RIGHT, H.JOY_LEFT, H.JOY_DOWN, H.JOY_UP)


def exit_side(x, y):
    if y <= W.NORTH_EDGE:
        return 'north'
    if y >= W.SOUTH_EDGE:
        return 'south'
    if x <= W.WEST_EDGE:
        return 'west'
    if x >= W.EAST_EDGE:
        return 'east'
    return None


def plan(world, goal, what):
    """Breadth first over the positions the explorer can reach in its
    room: the shortest list of inputs whose last move satisfies
    goal(probe, joy) (probe: the HeroModel after that move)."""
    solid = world.hero.solid
    start = (world.hero.x, world.hero.y)
    back = {start: None}
    todo = deque([start])
    probe = H.HeroModel(solid)
    while todo:
        x, y = todo.popleft()
        for joy in MOVES:
            probe.x, probe.y = x, y
            probe.update(joy)
            nxt = (probe.x, probe.y)
            if goal(probe, joy):
                path = [joy]
                at = (x, y)
                while back[at] is not None:
                    at, j = back[at]
                    path.append(j)
                return path[::-1]
            if exit_side(*nxt) or nxt in back:
                continue
            back[nxt] = ((x, y), joy)
            todo.append(nxt)
    raise ValueError(f'room {world.room}: cannot {what}')


def plan_exit(world, side):
    return plan(world, lambda p, j: exit_side(p.x, p.y) == side,
                f'go out to the {side}')


def plan_get(world, col, row):
    """Inputs that bring the middle of the hitbox into metatile (col,
    row): the object there is picked up (or tried)."""
    def goal(p, joy):
        return (((p.x + W.HIT_X) & 0xFF) >> 4 == col and
                ((p.y + W.HIT_Y - H.ROOM_TOP_LINE) & 0xFF) >> 4 == row)
    return plan(world, goal, f'reach {col},{row}')


PUSH = {'north': H.JOY_UP, 'south': H.JOY_DOWN, 'west': H.JOY_LEFT,
        'east': H.JOY_RIGHT}


def plan_push(world, side):
    """Inputs that make the explorer walk into the door on `side`
    until a door cell stops it."""
    joy_side = PUSH[side]
    return plan(world, lambda p, j: j == joy_side and
                p.block == W.DOOR_CELL, f'push the door {side}')


def tour(world, sides):
    """Inputs for the exits in `sides`, one after the other; the world
    follows. Returns (inputs, rooms visited)."""
    inputs, rooms = [], [world.room]
    for side in sides:
        path = plan_exit(world, side)
        for joy in path:
            world.update(joy)
        inputs += path
        rooms.append(world.room)
    return inputs, rooms


def free_spot(world_solid, near=(H.START_X, H.START_Y)):
    """A position near `near` where the explorer's hitbox and the
    points around it are on free cells."""
    probe = H.HeroModel(world_solid)
    best = None
    for y in range(24, 150):
        for x in range(8, 232):
            if any(probe.is_solid(x + dx, y + dy)
                   for dx in (H.BOX_LEFT - 1, H.BOX_MID, H.BOX_RIGHT + 1)
                   for dy in (H.BOX_TOP - 1, H.BOX_BOTTOM + 1)):
                continue
            d = abs(x - near[0]) + abs(y - near[1])
            if best is None or d < best[0]:
                best = (d, x, y)
    return best[1], best[2]

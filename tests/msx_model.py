"""The model of the MSX screen: what a room must look like, from
art.py alone.

Independent of the Z80 code and of the asset builder
(game/assets/build_msx.py): it does not read their data and does not
import them. It asks art.py (the ZX game's drawings, unchanged) for
the room as the Spectrum shows it, without objects and enemies (not
in milestone 0.1), and recolours it by the rules of the MSX book:

- every ZX colour has its TMS9918A colour, normal and BRIGHT
  (TMS_NORMAL, TMS_BRIGHT below);
- a ZX cell, ink on paper, becomes an MSX cell with the same 8 x 8
  pixels and the same ink and paper on its 8 rows (version A);
- version B: the cells of some roles take a colour per row
  (ROWS_B), when their colour in A is the one named: the flame red
  at the tip and yellow at the base, the moss in three greens, the
  water in bands, the well's water in two blues;
- the flame shows the phase that is due: (frames / 8) mod 4;
- the HUD (rows 0, 1, 22, 23) is art.py's, with the values given
  (energy, keys, seals, score: 8, 0, 0, 0 until milestone 0.4) and
  the room's name; after the victory (milestone 0.4) VICTORY in place
  of the name, at column 12, in its own colour;
- the objects (milestone 0.4) that are still there, drawn by art.py
  with the room; the door, if open: its tiles as art.py draws the
  room with the door open (a locked door D as an opening E, the gate
  G of the portal as the open gate O), the rest of the room as it is
  with the door shut;
- the solid cells (from milestone 0.2): a metatile of the room's text
  whose symbol is masonry (# T t r n), a pillar (P), the well (W),
  the altar (A), water (w) or an urn (u) is solid (1) in its four
  cells; a locked door (D) or the gate of the portal (G) is solid
  with the value 2 (from milestone 0.4: the door's cells, which the
  program looks for); a door open is free, but for the two posts of
  the open portal (in the top two rows of the gate, the left cells
  of its left tiles and the right cells of its right ones: 1);
- the explorer (from milestone 0.2.1: two sprites, the author's
  choice) is an image of art_pieces.HERO_FRAMES drawn over the room at
  its x and y in two colours: light red (9) for the skin, that is the
  face from under the hat's brim (row 3, in profile row 4) to row 7,
  but not seen from behind, and the hands, the outer pixels of row 11
  (columns 0-3 and 12-15, in profile 4, 5, 10, 11); dark yellow (10)
  for the clothes, the rest;
- from milestone 0.5 the sprites are a list, as the VDP gets it: (Y,
  X, shape, colour), Y a line above the top; shapes 0-28 the
  explorer's skin (image x 4), 32-60 its clothes, 64-96 the images of
  the combat (art_pieces.COMBAT_FRAMES, x 4), each in its colour
  (COMBAT_INKS, approved by the author on 9 November: the skeleton
  white, the bat magenta, the dust grey, the blade cyan), an enemy
  just hit red (HIT_INK, milestone 0.5.1, as in the C64 game); on
  every line of the picture only the first four sprites of the list
  that cross it are drawn, the first in front; after GAME OVER
  (milestone 0.5) GAME OVER in place of the name, at column 11, in
  its own colour.

Use: screen(name, phase=0, version='A', door_open=False,
            objects=None, won=False, energy=8, keys=0, seals=0,
            score=0, lost=False) -> 192 rows of 256 colour indices
            (1-15; 0, transparent, never appears); objects: the
            slots of the room whose object is still there (None:
            all)
     solid_cells(name, door_open=False) -> 640 values, 0 free, 1
     solid, 2 a door (32 x 20)
     with_hero(rows, image, x, y) -> the rows with the explorer
     with_sprites(rows, sat) -> the rows with a sprite list
     black_room(rows) -> the rows with the room black (a change)
     rooms() -> {number: name} of the dungeon's 16 slots
     zone_of(name) -> 0-3, the zone as the program numbers it
Standard library only.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'game' / 'assets'))
sys.path.insert(0, str(ROOT / 'tools'))
import art  # noqa: E402
import art_pieces  # noqa: E402
import dungeon  # noqa: E402

SOLID_SYMBOLS = '#TtrnPWAwu'
DOOR_SYMBOLS, DOOR_CELL = 'DG', 2
HERO_SKIN, HERO_CLOTHES = 9, 10
# the colours of the combat's sprites, by image: skeleton (2), bat
# (2), dust, blade down, up, left, right [approved 9/11]; an enemy
# just hit is red (milestone 0.5.1)
COMBAT_INKS = (15, 15, 13, 13, 14, 7, 7, 7, 7)
HIT_INK = 8

# ZX colours 0-7: black, blue, red, magenta, green, cyan, yellow,
# white. The TMS9918A has no BRIGHT: the nearest of its 15 colours.
TMS_NORMAL = [1, 4, 6, 13, 12, 7, 10, 14]
TMS_BRIGHT = [1, 5, 8, 13, 2, 7, 11, 15]
# version B: role -> (ink or paper, its colour in A, rows 0-7)
ROWS_B = {
    'flame': ('ink', 11, (8, 9, 9, 10, 10, 11, 11, 11)),
    'moss': ('ink', 12, (3, 3, 2, 2, 2, 12, 12, 12)),
    'mossface': ('ink', 12, (3, 3, 2, 2, 2, 12, 12, 12)),
    'fmoss': ('ink', 12, (3, 3, 2, 2, 2, 12, 12, 12)),
    'water': ('paper', 7, (7, 7, 5, 5, 7, 7, 5, 5)),
    'wellwater': ('ink', 5, (5, 5, 4, 4, 5, 5, 4, 4)),
}


class _Roles(dict):
    """A palette that answers with the role's name."""

    def __missing__(self, key):
        return key


def opened(room):
    """The room's map with its door open."""
    return [r.replace('D', 'E').replace('G', 'O') for r in room.grid]


def _zx(name, phase, palettes, door_open=False, objects=None, won=False,
        hud=None, lost=False):
    room = dungeon.load_room(name)
    things = [o for k, o in enumerate(room.objects)
              if objects is None or k in objects]
    s = art.Screen()
    saved = art.ZONES, art.BASE
    if palettes is not None:
        art.ZONES = {z: palettes for z in saved[0]}
        art.BASE = palettes
    try:
        art.render_grid(s, room.grid, room.zone, things, phase, 'closed')
        if door_open and room.door:
            o = art.Screen()
            art.render_grid(o, opened(room), room.zone, things, phase,
                            'closed')
            for c, r in dungeon.door_tiles(room)[0]:
                for y in range(16):
                    line = (art.TOP + 2 * r) * 8 + y
                    s.px[line][16 * c:16 * c + 16] = \
                        o.px[line][16 * c:16 * c + 16]
                for cy in range(2):
                    row = art.TOP + 2 * r + cy
                    s.at[row][2 * c:2 * c + 2] = o.at[row][2 * c:2 * c + 2]
        pal = art.ZONES[room.zone]
        art.hud(s, pal, name='' if won or lost else room.title,
                **(hud or {}))
        if won:
            art.text(s, 12, 23, 'VICTORY', pal['won'])
        if lost:
            art.text(s, 11, 23, 'GAME OVER', pal['lost'])
    finally:
        art.ZONES, art.BASE = saved
    return s


def _colours(attr, role, version):
    """Ink and paper of the 8 rows of a cell."""
    table = TMS_BRIGHT if attr & 0x40 else TMS_NORMAL
    ink, paper = table[attr & 7], table[(attr >> 3) & 7]
    inks, papers = (ink,) * 8, (paper,) * 8
    if version == 'B' and role in ROWS_B:
        side, was, rows = ROWS_B[role]
        if side == 'ink' and ink == was:
            inks = rows
        if side == 'paper' and paper == was:
            papers = rows
    return inks, papers


def screen(name, phase=0, version='A', door_open=False, objects=None,
           won=False, energy=8, keys=0, seals=0, score=0, lost=False):
    hud = {'energy': energy, 'keys': keys, 'seals': seals,
           'score': score}
    zx = _zx(name, phase, None, door_open, objects, won, hud, lost)
    roles = _zx(name, phase, _Roles(), door_open, objects, won, hud,
                lost)
    out = []
    for y in range(192):
        row = []
        cy = y >> 3
        for cx in range(32):
            inks, papers = _colours(zx.at[cy][cx], roles.at[cy][cx],
                                    version)
            ink, paper = inks[y & 7], papers[y & 7]
            px = zx.px[y][cx * 8:cx * 8 + 8]
            row.extend(ink if p else paper for p in px)
        out.append(row)
    return out


def rooms():
    slots, start = dungeon.load_dungeon()
    return {n: name for n, name in enumerate(slots) if name}


def start_room():
    return dungeon.load_dungeon()[1]


def zone_of(name):
    """The zone of a room: 0 the atrium, 1-3 the wings A, B, C."""
    return dungeon.ZONES.index(dungeon.load_room(name).zone)


def solid_cells(name, door_open=False):
    """The 32 x 20 cells of the room under the HUD: 0 free, 1 solid,
    2 a door; door_open: the room's door open."""
    room = dungeon.load_room(name)
    cells = [0] * (32 * 20)
    for r, line in enumerate(room.grid):
        for c, ch in enumerate(line):
            v = 1 if ch in SOLID_SYMBOLS else \
                DOOR_CELL if ch in DOOR_SYMBOLS else 0
            for dy in range(2):
                for dx in range(2):
                    cells[(2 * r + dy) * 32 + 2 * c + dx] = v
    if door_open and room.door:
        tiles = dungeon.door_tiles(room)[0]
        left = min(c for c, r in tiles)
        for c, r in tiles:
            for dy in range(2):
                for dx in range(2):
                    post = room.door == dungeon.PORTAL and r < 2 and \
                        dx == (0 if c == left else 1)
                    cells[(2 * r + dy) * 32 + 2 * c + dx] = int(post)
    return cells


def hero_colour(image, dx, dy):
    """The colour of the pixel at column dx, row dy of an image of
    the explorer (0-7: down, down step, up, up step, left, left step,
    right, right step)."""
    profile, back = image >= 4, image in (2, 3)
    brim = 4 if profile else 3
    if brim < dy <= 7 and not back:
        return HERO_SKIN                # the face
    if dy == 11 and (dx in (4, 5, 10, 11) if profile
                     else dx <= 3 or dx >= 12):
        return HERO_SKIN                # the hands
    return HERO_CLOTHES


def with_hero(rows, image, x, y):
    """A copy of the screen rows with the explorer's image (0-7, the
    order of HERO_FRAMES) at x, y, in its two colours."""
    out = [list(r) for r in rows]
    drawing = art_pieces.HERO_FRAMES[image]
    for dy in range(16):
        for dx in range(16):
            if drawing[dy][dx] == '#' and 0 <= y + dy < 192 \
                    and 0 <= x + dx < 256:
                out[y + dy][x + dx] = hero_colour(image, dx, dy)
    return out


def sprite_pixels(shape):
    """The 16 x 16 pixels of a shape of the list: (dx, dy) set."""
    if shape < 64:
        image = (shape & 31) >> 2
        colour = HERO_SKIN if shape < 32 else HERO_CLOTHES
        drawing = art_pieces.HERO_FRAMES[image]
        return {(dx, dy) for dy in range(16) for dx in range(16)
                if drawing[dy][dx] == '#' and
                hero_colour(image, dx, dy) == colour}
    drawing = art_pieces.COMBAT_FRAMES[(shape - 64) >> 2]
    return {(dx, dy) for dy in range(16) for dx in range(16)
            if drawing[dy][dx] == '#'}


_PIXELS = {}


def with_sprites(rows, sat):
    """A copy of the screen rows with the sprite list sat [(Y, X,
    shape, colour)]: on each line the first four that cross it, the
    first in front."""
    out = [list(r) for r in rows]
    for line in range(192):
        on = []
        for k, (y, x, shape, colour) in enumerate(sat):
            dy = (line - 1 - y) & 0xFF
            if dy < 16:
                on.append((dy, x, shape, colour))
                if len(on) == 4:
                    break
        for dy, x, shape, colour in reversed(on):
            if shape not in _PIXELS:
                _PIXELS[shape] = sprite_pixels(shape)
            for dx in range(16):
                if (dx, dy) in _PIXELS[shape] and x + dx < 256:
                    out[line][x + dx] = colour
    return out


def black_room(rows):
    """A copy of the rows with lines 16-175 black: the room hidden
    during a change."""
    return rows[:16] + [[1] * 256 for _ in range(160)] + rows[176:]

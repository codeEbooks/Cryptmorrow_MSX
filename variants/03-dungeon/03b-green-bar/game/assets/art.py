"""Cryptmorrow ZX: the graphics, drawn as Spectrum screens.

A room is 16 x 10 metatiles of 16 x 16 pixels; a metatile is 2 x 2
character cells, and every cell has its own attribute (ink, paper,
BRIGHT). This module draws every metatile from its symbol in the room
map, from the symbols around it (autotiling: a wall with floor below
shows its lit face, a wall beside the floor a rim, and so on) and
from its place in the room; it gives every cell a role ('mass',
'face', 'floor', 'flame'...) that the zone's palette turns into an
attribute. Sprites are masked and take the ink of the cells they
cross, as the game will draw them.

The drawings are in art_pieces.py; the rooms in rooms/ (read by
dungeon.py). The result is a 6912-byte screen, exactly what the
Spectrum keeps at $4000, so it can be shown in Fuse and compared.

These screens are the art of the game: the asset builder turns them into
the game's tile set. Standard library only.
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / 'tools'))
import art_pieces as P  # noqa: E402
import dungeon  # noqa: E402
import scr2png  # noqa: E402

K, B, R, M, G, C, Y, W = range(8)       # Spectrum colours


def attr(ink, paper=K, bright=0):
    return (bright << 6) | (paper << 3) | ink


# ------------------------------------------------------------------
# Palettes: role -> attribute. The atrio is grey stone, zone A grey
# with a cyan face, zone B blue, zone C red brick with a gold face.
# ------------------------------------------------------------------
BASE = {
    'mass': attr(W), 'face': attr(K, W), 'moss': attr(G),
    'mossface': attr(G, W), 'iron': attr(K, W), 'roots': attr(Y),
    'floor': attr(W), 'fmoss': attr(G), 'flame': attr(Y, K, 1),
    'pillar': attr(W, K, 1), 'arch': attr(W), 'door': attr(K, R),
    'step': attr(W), 'bones': attr(W, K, 1), 'gold': attr(Y, K, 1),
    'water': attr(W, C, 1), 'urn': attr(Y), 'niche': attr(W),
    'grate': attr(C), 'altar': attr(W, K, 1), 'candle': attr(Y, K, 1),
    'well': attr(W, K, 1), 'wellwater': attr(B, K, 1),
    'potion': attr(R, K, 1), 'key': attr(Y, K, 1),
    'seal': attr(M, K, 1), 'treasure': attr(Y, K, 1),
    'hud': attr(W, K, 1), 'num': attr(W), 'bar': attr(G, K, 1),
    'rule': attr(G), 'name': attr(W, K, 1), 'logo': attr(W, K, 1),
    'logo2': attr(W), 'menu': attr(W), 'menu_on': attr(Y, K, 1),
    'note': attr(C),
    'won': attr(Y, K, 1),               # VICTORY
    'lost': attr(R, K, 1),              # GAME OVER
    'won2': attr(Y), 'lost2': attr(R),  # big words, row 3
}
ZONES = {
    'atrio': dict(BASE),
    'A': dict(BASE, face=attr(K, C), mossface=attr(B, C),
              iron=attr(K, C)),
    'B': dict(BASE, mass=attr(B, K, 1), face=attr(B, C),
              iron=attr(B, C), floor=attr(C), arch=attr(C),
              step=attr(C), pillar=attr(C, K, 1),
              altar=attr(C, K, 1)),
    'C': dict(BASE, mass=attr(R), face=attr(R, Y), iron=attr(R, Y),
              floor=attr(Y), arch=attr(Y), step=attr(Y),
              pillar=attr(Y, K, 1), altar=attr(Y, K, 1),
              urn=attr(R, K, 1)),
}
MOSS = {'atrio': 6, 'A': 0, 'B': 0, 'C': 0}   # seeds, in 97ths


def h(c, r, k=0):
    """A fixed pseudo-random number 0-96 for a place: the same room
    always gets the same variants."""
    return (c * 73 + r * 151 + k * 37 + c * r * 11) % 97


# ------------------------------------------------------------------
# The screen: 256 x 192 pixels and 32 x 24 attributes.
# ------------------------------------------------------------------
class Screen:
    def __init__(self):
        self.px = [[0] * 256 for _ in range(192)]
        self.at = [[attr(W)] * 32 for _ in range(24)]

    def bytes(self):
        """The 6912 bytes of the screen in the Spectrum's order."""
        scr = bytearray(6912)
        for y in range(192):
            base = ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)
            for c in range(32):
                b = 0
                for bit in self.px[y][c * 8:c * 8 + 8]:
                    b = (b << 1) | bit
                scr[base + c] = b
        for r in range(24):
            for c in range(32):
                scr[6144 + r * 32 + c] = self.at[r][c]
        return bytes(scr)

    def png(self, border=0, scale=3):
        return scr2png.png_bytes(self.bytes(), border, scale)


# ------------------------------------------------------------------
# A metatile (or a bigger piece): pixels and one role per cell.
# ------------------------------------------------------------------
class Tile:
    def __init__(self, role='floor', w=16, hh=16):
        self.w, self.h = w, hh
        self.px = [[0] * w for _ in range(hh)]
        self.fill_roles(role)

    def fill_roles(self, role):
        self.roles = [[role] * (self.w // 8) for _ in range(self.h // 8)]

    def draw(self, rows, x0=0, y0=0, mirror=False):
        """'#' ink, '.' paper, 'o' half tone, ',' keep."""
        for y, row in enumerate(rows):
            if mirror:
                row = row[::-1]
            for x, ch in enumerate(row):
                xx, yy = x0 + x, y0 + y
                if not (0 <= xx < self.w and 0 <= yy < self.h):
                    continue
                if ch == '#':
                    self.px[yy][xx] = 1
                elif ch == '.':
                    self.px[yy][xx] = 0
                elif ch == 'o':
                    self.px[yy][xx] = 1 if (xx + yy) % 2 == 0 else 0


# ------------------------------------------------------------------
# Masonry
# ------------------------------------------------------------------
def brick_mass(x, y):
    """Masonry in shadow: bricks 16 x 8 laid with a stagger of 8; lit
    top and left edge, dark bottom and right edge, half-tone face.
    Ink is the stone."""
    xx = (x + (8 if (y // 8) % 2 else 0)) % 16
    yy = y % 8
    if yy == 7 or xx == 15:
        return 0
    if yy == 0 or xx == 0:
        return 1
    if yy == 6 or xx == 14:
        return 0
    return 1 if (x + y) % 2 == 0 else 0


def brick_face(x, y):
    """The lit face of a wall: solid stone, dark joints and a few pits.
    Ink is the joint."""
    xx = (x + (8 if (y // 8) % 2 else 0)) % 16
    yy = y % 8
    if yy == 7 or xx == 15:
        return 1
    if (yy == 6 or xx == 14) and (x + y) % 2 == 0:
        return 1
    return 1 if (xx, yy) in ((4, 2), (9, 4), (11, 1)) else 0


MOSS_CELLS = set()


def grow_moss(grid, zone):
    """The wall cells with moss: a few seeds, each dripping one or two
    cells down and sometimes one to the side."""
    MOSS_CELLS.clear()
    rows, cols = len(grid), len(grid[0])

    def wall(cx, cy):
        c, r = cx // 2, cy // 2
        return 0 <= c < cols and 0 <= r < rows and grid[r][c] == '#'
    for cy in range(rows * 2):
        for cx in range(cols * 2):
            if not wall(cx, cy) or h(cx, cy, 5) >= MOSS[zone]:
                continue
            MOSS_CELLS.add((cx, cy))
            for k, (dx, dy) in enumerate(((0, 1), (0, 2), (1, 0),
                                          (-1, 1))):
                if h(cx, cy, 11 + k) < (60, 25, 30, 20)[k] and \
                        wall(cx + dx, cy + dy):
                    MOSS_CELLS.add((cx + dx, cy + dy))


def wall_tile(o, c, r):
    """o: which of the eight neighbours are open (not wall)."""
    t = Tile('mass')
    face = o['s']
    for y in range(16):
        for x in range(16):
            t.px[y][x] = brick_face(x, y) if face else brick_mass(x, y)
    if face:
        t.fill_roles('face')
        t.px[15] = [1] * 16                          # foot of the wall
        t.px[14] = [1 if x % 2 == 0 else t.px[14][x] for x in range(16)]
    rim = 0 if face else 1
    for side, x_out, x_in in (('e', 15, 14), ('w', 0, 1)):
        if o[side]:
            for y in range(16):
                t.px[y][x_out], t.px[y][x_in] = rim, 1 - rim
    if o['n'] and not face:
        t.px[0] = [1] * 16
        t.px[1] = [0] * 16
        if o['e']:
            t.px[0][15] = 0
        if o['w']:
            t.px[0][0] = 0
    # inner corners: the rim of a side wall reaches up to the face
    for side, diag, x_out, x_in in (('e', 'se', 15, 14),
                                    ('w', 'sw', 0, 1)):
        if not face and not o[side] and o[diag] and not o['s']:
            for y in range(10, 16):
                t.px[y][x_out], t.px[y][x_in] = 1, 0
    for cy in range(2):
        for cx in range(2):
            if (c * 2 + cx, r * 2 + cy) not in MOSS_CELLS:
                continue
            v = h(c, r, cx + cy) % 2
            moss = P.MOSS_FACE[v] if face else P.MOSS_MASS[v]
            t.roles[cy][cx] = 'mossface' if face else 'moss'
            for y in range(8):
                for x in range(8):
                    if moss[y][x] == '#' or (moss[y][x] == 'o' and
                                             (x + y) % 2 == 0):
                        t.px[cy * 8 + y][cx * 8 + x] = 1
    return t


def face_tile(o, c, r):
    """A wall face without moss (the base of torches, niches and
    roots)."""
    keep = set(MOSS_CELLS)
    MOSS_CELLS.clear()
    t = wall_tile(dict(o, s=True), c, r)
    MOSS_CELLS.update(keep)
    return t


def torch_tile(o, c, r, right, phase=0):
    """A torch on the face: the flame in a dark recess (its own cell,
    ink yellow), the iron bracket below it."""
    t = face_tile(o, c, r)
    cx = 8 if right else 0
    for y in range(8):
        for x in range(cx, cx + 8):
            # the joints round the recess catch the light
            t.px[y][x] = 1 if brick_face(x, y) and (x + y) % 2 else 0
    t.draw(P.FLAME[phase % len(P.FLAME)], cx, 0)
    t.roles[0][cx // 8] = 'flame'
    t.draw(P.BRACKET[:7], cx, 8)
    for x in range(cx, cx + 8):
        if P.BRACKET[7][x - cx] == '#':
            t.px[15][x] = 1
    t.roles[1][cx // 8] = 'iron'
    return t


def niche_tile(o, c, r):
    t = face_tile(o, c, r)
    t.draw(P.NICHE, 0, 8)
    t.roles[1] = ['niche', 'niche']
    for x in range(4, 12):                    # the arch cuts the bricks
        t.px[7][x] = 1
    for x in range(5, 11):
        t.px[6][x] = 1
    return t


def roots_tile(o, c, r):
    t = face_tile(o, c, r)
    t.draw(P.ROOTS)
    t.roles[1] = ['roots', 'roots']
    return t


# ------------------------------------------------------------------
# Floors: flagstones in two courses, a pattern of 64 x 32 pixels cut
# into eight metatiles by the place of the tile. The joints are a
# dotted line, the top-left corner of every stone catches the light.
# ------------------------------------------------------------------
STONES = [(0, 0, 20, 15), (22, 0, 12, 15), (36, 0, 14, 7),
          (36, 9, 14, 6), (52, 0, 10, 15), (9, 17, 14, 13),
          (25, 17, 8, 13), (35, 17, 8, 13), (45, 17, 10, 13),
          (57, 17, 14, 13)]
CRACKS = {0: [(13, 4), (12, 5), (12, 6), (11, 7), (10, 8)],
          5: [(5, 3), (6, 4), (7, 4), (8, 5)],
          8: [(3, 8), (4, 7), (5, 7)]}


def floor_pattern():
    px = [[0] * 64 for _ in range(32)]
    for i, (x0, y0, w, hh) in enumerate(STONES):
        for y in range(hh):
            for x in range(w):
                if x in (0, w - 1) and y in (0, hh - 1):
                    continue                        # rounded corner
                gx, gy = (x0 + x) % 64, (y0 + y) % 32
                edge = x in (0, w - 1) or y in (0, hh - 1)
                on = edge and (gx + gy) % 2 == 0
                if (y == 0 and 1 <= x <= 4) or (x == 0 and 1 <= y <= 2):
                    on = True                       # the lit corner
                px[gy][gx] = 1 if on else 0
        for (cx, cy) in CRACKS.get(i, ()):
            px[(y0 + cy) % 32][(x0 + cx) % 64] = 1
    return px


FLOOR = floor_pattern()


def floor_tile(c, r, shadow=False):
    """The floor at column c, row r; in the shadow of a wall above it
    loses its top rows."""
    t = Tile('floor')
    x0 = (c % 4) * 16
    t.px = [FLOOR[(r % 2) * 16 + y][x0:x0 + 16] for y in range(16)]
    if shadow:
        for y in range(3):
            t.px[y] = [0] * 16
        t.px[3] = [p if x % 4 == 1 else 0 for x, p in enumerate(t.px[3])]
    return t


def stairs_tile():
    """An opening on the south edge: steps going down, closer and
    darker."""
    t = Tile('floor')
    for y, style in ((0, 'solid'), (5, 'solid'), (9, 'dots'),
                     (12, 'dots'), (14, 'sparse')):
        for x in range(16):
            v = {'solid': True, 'dots': (x + y) % 2 == 0,
                 'sparse': x % 4 == 0}[style]
            t.px[y][x] = 1 if v else 0
    for y in (1, 6):
        t.px[y] = [1 if (x + y) % 2 == 0 else 0 for x in range(16)]
    return t


def water_tile(same, c, r, phase=0):
    """Standing water; same: which neighbours are water too. A stone
    lip where the pool meets the floor, ripples that drift."""
    t = Tile('water')
    for (x0, y0, n) in ((3, 4, 4), (10, 9, 4), (5, 12, 3), (12, 3, 2)):
        x0 = (x0 + (c % 2) * 5 + (r % 2) * 3 + phase) % 12
        for x in range(n):
            t.px[y0][x0 + x] = 1
        t.px[y0 + 1][max(x0 - 1, 0)] = 1
        t.px[y0 + 1][min(x0 + n, 15)] = 1
    if not same['n']:
        t.px[0] = [1] * 16
        t.px[1] = [0] * 16
        t.px[2] = [1 if x % 2 == 0 else 0 for x in range(16)]
    if not same['s']:
        t.px[15] = [1] * 16
    for side, x_out, x_in in (('w', 0, 1), ('e', 15, 14)):
        if not same[side]:
            for y in range(16):
                t.px[y][x_out], t.px[y][x_in] = 1, 0
    return t


# ------------------------------------------------------------------
# Big pieces
# ------------------------------------------------------------------
GATE_CENTRE = (15.5, 16.0)
GATE_R_OUT, GATE_R_IN = 15.6, 8.6


def gate_tile(state='closed'):
    """The gate of the Moss Gate, 2 x 3 metatiles (32 x 48): an arch
    of voussoirs, a wooden door (red paper, black ink) and two steps.
    'open': the doorway is dark."""
    t = Tile('arch', 32, 48)
    cx, cy = GATE_CENTRE
    for y in range(32):
        for x in range(32):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if y <= cy:
                opening = d < GATE_R_IN
                ring = GATE_R_IN <= d < GATE_R_OUT
            else:
                opening = 8 <= x <= 23
                ring = 1 <= x <= 30 and not opening
            if 8 <= x <= 23 and 8 <= y <= 31:          # door cells
                v = 1
                if opening and state != 'open':
                    v = 0                               # red wood
                    if x in (8, 23, 12, 16, 19) or y == 31:
                        v = 1                           # plank joints
                    elif y in (13, 14, 25, 26):
                        v = 0 if (x in (10, 14, 18, 21) and
                                  y in (13, 25)) else 1  # iron bands
                    elif (x, y) in ((20, 19), (19, 20), (21, 20),
                                    (20, 21)):
                        v = 1                           # ring pull
                    elif (x * 7 + y * 3) % 29 == 0:
                        v = 1                           # grain
            elif ring and y <= cy:
                a = math.degrees(math.atan2(-dy, dx)) % 180
                gap = min(abs(a - j) for j in range(20, 180, 20))
                joint = math.radians(gap) * d < 0.55
                edge = d >= GATE_R_OUT - 1 or d < GATE_R_IN + 1
                v = 0 if joint or edge else 1
            elif ring:
                xx = x - 1 if x < 16 else 30 - x        # 0 = outer edge
                v = 0 if xx >= 6 or (y - 17) % 5 == 4 else 1
            elif y < 16:
                v = brick_mass(x, y)
            else:
                v = 1 - brick_face(x, y)
                if y == 31 or (y == 30 and x % 2 == 0):
                    v = 0
            t.px[y][x] = v
    for y in range(32, 48):
        for x in range(32):
            v = 0
            for (ya, yb, xa, xb) in ((33, 38, 5, 26), (40, 46, 1, 30)):
                if ya <= y <= yb and xa <= x <= xb:
                    if x in (xa, xb) and y == ya:
                        v = 0
                    elif y == ya or x == xa:
                        v = 1
                    elif y == yb or x == xb:
                        v = 0
                    else:
                        v = 1 if (x + y) % 2 == 0 and y < yb - 1 else 0
            t.px[y][x] = v
    names = {'a': 'arch', 'd': 'door', 's': 'step'}
    t.roles = [[names[ch] for ch in row] for row in
               ("aaaa", "adda", "adda", "adda", "ssss", "ssss")]
    return t


def pillar_tile(c, r):
    t = Tile('pillar', 16, 32)
    t.px = floor_tile(c, r).px + floor_tile(c, r + 1).px
    t.draw(P.PILLAR)
    return t


def well_tile(c, r):
    """A round well, 2 x 2 metatiles: a ring of twelve stones round
    dark water."""
    t = Tile('well', 32, 32)
    for y in range(32):
        for x in range(32):
            dx, dy = x - 15.5, y - 15.5
            d = math.hypot(dx, dy)
            step = math.pi / 6
            off = (math.atan2(dy, dx) + step / 2) % step - step / 2
            if d < 11.0:
                v = (abs(d - 5.5) < 0.6 and dy < 0) or \
                    (abs(d - 8.5) < 0.6 and dy > 2)       # ripples
            elif d < 12.0 or d >= 15.4:
                v = False
            else:
                v = abs(d * math.sin(off)) >= 0.6       # joints
                if d > 14.4 and (dx > 0 or dy > 0) and (x + y) % 2:
                    v = False                           # shaded side
            if d >= 16.4:
                t.px[y][x] = FLOOR[((r % 2) * 16 + y) % 32][
                    ((c % 4) * 16 + x) % 64]
            else:
                t.px[y][x] = 1 if v else 0
    t.roles = [['well'] * 4, ['well', 'wellwater', 'wellwater', 'well'],
               ['well', 'wellwater', 'wellwater', 'well'], ['well'] * 4]
    return t


def altar_tile():
    """The altar, 3 x 1 metatiles: two candles in their own cells (so
    the flames are yellow), a chalice, a carved slab."""
    t = Tile('altar', 48, 16)
    for y in range(8, 16):
        for x in range(48):
            v = 0
            if 1 <= x <= 46:
                if y == 8 or x == 1:
                    v = 1                          # lit top and left
                elif y == 9:
                    v = x % 2
                elif y == 15 or x == 46:
                    v = 0
                elif 3 <= x <= 44 and ((x - 3) % 14 == 0 or
                                       y in (10, 14)):
                    v = 1                          # three panels
                elif 11 <= y <= 13 and (x + y) % 4 == 0 and 3 <= x <= 44:
                    v = 1
            t.px[y][x] = v
    t.draw(P.ALTAR_TOP)
    t.draw(P.CHALICE, 20, 0)
    t.roles = [['candle', 'altar', 'altar', 'altar', 'altar', 'candle'],
               ['altar'] * 6]
    return t


def grate_tile(across=True):
    """A locked door: an iron grate across the opening."""
    t = Tile('grate')
    for y in range(16):
        for x in range(16):
            bar = x % 4 == 1 if across else y % 4 == 1
            band = y in (3, 12) if across else x in (3, 12)
            t.px[y][x] = 1 if bar or band else 0
    return t


def over_floor(c, r, rows, role=None, cells=None, shadow=False):
    """The floor with a drawing over it; role for the cells listed
    (all four if cells is None)."""
    t = floor_tile(c, r, shadow)
    t.draw(rows)
    if role:
        for (cx, cy) in cells or ((0, 0), (1, 0), (0, 1), (1, 1)):
            t.roles[cy][cx] = role
    return t


# ------------------------------------------------------------------
# A room on the screen (rows 2-21 of the 24)
# ------------------------------------------------------------------
WALLS = dungeon.WALLS
OBJECTS = {'key': P.KEY, 'potion': P.POTION, 'seal': P.SEAL,
           'treasure': P.TREASURE}
TOP = 2


def render_grid(s, grid, zone, objects=(), phase=0, gate='closed',
                top=TOP):
    pal = ZONES[zone]
    rows, cols = len(grid), len(grid[0])
    things = {(c, r): kind for (kind, letter, c, r) in objects}

    def sym(c, r):
        if not (0 <= c < cols and 0 <= r < rows):
            return '#'
        return grid[r][c]

    def is_open(c, r):
        if sym(c, r) == 'G':                # the gate's step row
            return sym(c, r - 1) == 'G' and sym(c, r - 2) == 'G'
        return sym(c, r) not in WALLS

    grow_moss(grid, zone)
    done = set()
    for r in range(rows):
        for c in range(cols):
            if (c, r) in done:
                continue
            ch = grid[r][c]
            o = {k: is_open(c + dc, r + dr) for k, (dc, dr) in (
                ('n', (0, -1)), ('s', (0, 1)), ('w', (-1, 0)),
                ('e', (1, 0)), ('nw', (-1, -1)), ('ne', (1, -1)),
                ('sw', (-1, 1)), ('se', (1, 1)))}
            shadow = not o['n']
            if ch == '#':
                t = wall_tile(o, c, r)
            elif ch in 'Tt':
                t = torch_tile(o, c, r, ch == 't', phase)
            elif ch == 'n':
                t = niche_tile(o, c, r)
            elif ch == 'r':
                t = roots_tile(o, c, r)
            elif ch in 'GO':
                t = gate_tile('open' if ch == 'O' else gate)
                done.update((c + x, r + y) for x in range(2)
                            for y in range(3))
            elif ch == 'P':
                t = pillar_tile(c, r)
                done.add((c, r + 1))
            elif ch == 'W':
                t = well_tile(c, r)
                done.update(((c + 1, r), (c, r + 1), (c + 1, r + 1)))
            elif ch == 'A':
                t = altar_tile()
                done.update(((c + 1, r), (c + 2, r)))
            elif ch == 'w':
                same = {k: sym(c + dc, r + dr) == 'w' for k, (dc, dr) in
                        (('n', (0, -1)), ('s', (0, 1)), ('w', (-1, 0)),
                         ('e', (1, 0)))}
                t = water_tile(same, c, r)      # still water
            elif ch == 'u':
                t = over_floor(c, r, P.URN, 'urn')
            elif ch == 'D':
                t = grate_tile(across=r in (0, rows - 1))
            elif ch == 'm':
                v = h(c, r) % 2
                t = over_floor(c, r, P.MOSS_FLOOR[v], 'fmoss',
                               ((0, 0), (1, 0)) if v == 0 else
                               ((0, 1), (1, 1)), shadow)
            elif ch == 'b':
                t = over_floor(c, r, P.BONES[h(c, r) % 3], shadow=shadow)
            elif ch == 'g':
                t = over_floor(c, r, P.GOLD, 'gold')
            elif ch == 'E' and r == rows - 1:
                t = stairs_tile()
            elif ch == '_':
                t = Tile('floor')
            else:
                t = floor_tile(c, r, shadow and ch != 'E')
            if (c, r) in things:
                kind = things[(c, r)]
                t = over_floor(c, r, OBJECTS[kind], kind, shadow=shadow)
            blit(s, t, c, r, pal, top)
    return s


def blit(s, t, c, r, pal, top=TOP):
    for y in range(t.h):
        s.px[top * 8 + r * 16 + y][c * 16:c * 16 + t.w] = t.px[y]
    for cy, row in enumerate(t.roles):
        for cx, role in enumerate(row):
            s.at[top + r * 2 + cy][c * 2 + cx] = pal[role]


# ------------------------------------------------------------------
# Sprites: masked (the mask is the drawing grown by one pixel), they
# take the ink of the cells they cross.
# ------------------------------------------------------------------
def sprite(s, rows, x0, y0, mirror=False):
    rows = [r[::-1] if mirror else r for r in rows]
    for y in range(16):
        for x in range(16):
            near = any(0 <= y + dy < 16 and 0 <= x + dx < 16 and
                       rows[y + dy][x + dx] == '#'
                       for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            if near and 0 <= y0 + y < 192 and 0 <= x0 + x < 256:
                s.px[y0 + y][x0 + x] = 1 if rows[y][x] == '#' else 0


SPRITES = {'skeleton': P.SKELETON, 'bat': P.BAT}


def enemies(s, room, top=TOP):
    for kind, c, r, axis, fast in room.enemies:
        sprite(s, SPRITES[kind], c * 16, (top + r * 2) * 8)


# ------------------------------------------------------------------
# Text, HUD, the name of the room
# ------------------------------------------------------------------
def text(s, col, row, msg, a):
    for i, ch in enumerate(msg):
        glyph = P.FONT[ch]
        for y in range(8):
            s.px[row * 8 + y][(col + i) * 8:(col + i) * 8 + 8] = \
                [1 if p == '#' else 0 for p in glyph[y]]
        s.at[row][col + i] = a


def icon(s, col, row, rows, a):
    for y in range(8):
        s.px[row * 8 + y][col * 8:col * 8 + 8] = \
            [1 if p == '#' else 0 for p in rows[y]]
    s.at[row][col] = a


def hud(s, pal, energy=8, keys=0, seals=0, score=0, name=''):
    """Row 0: ENERGY and its bar (eight segments in four cells), the
    key, the seals, SCORE. A rule under it and above the name."""
    for row in (0, 1, 22, 23):
        s.px[row * 8:row * 8 + 8] = [[0] * 256 for _ in range(8)]
        s.at[row] = [pal['hud']] * 32
    text(s, 0, 0, 'ENERGY', pal['hud'])
    for i in range(4):
        cell = []
        for y in range(8):
            row = ''
            for seg in range(2):
                full = i * 2 + seg < energy
                if 1 <= y <= 5:
                    row += '###.' if full else (
                        '#.#.' if y in (1, 5) else '....')
                else:
                    row += '....'
            cell.append(row)
        icon(s, 7 + i, 0, cell, pal['bar'])
    icon(s, 12, 0, P.KEY_ICON, pal['key'])
    text(s, 13, 0, str(keys), pal['num'])
    icon(s, 15, 0, P.SEAL_ICON, pal['seal'])
    text(s, 16, 0, f'{seals}/3', pal['num'])
    text(s, 20, 0, 'SCORE', pal['hud'])
    text(s, 26, 0, f'{score:06d}', pal['num'])
    for c in range(32):
        s.px[12][c * 8:c * 8 + 8] = [1] * 8
        s.px[22 * 8 + 3][c * 8:c * 8 + 8] = [1] * 8
        s.at[1][c] = s.at[22][c] = BASE['rule']
    text(s, 16 - (len(name) + 1) // 2, 23, name, pal['name'])


def room_screen(name, hero=None, phase=0, state=None, gate='closed'):
    """A room as the game will show it. hero: (drawing, x, y, mirror)
    in screen pixels; state: energy, keys, seals, score."""
    room = dungeon.load_room(name)
    s = Screen()
    render_grid(s, room.grid, room.zone, room.objects, phase, gate)
    hud(s, ZONES[room.zone], name=room.title, **(state or {}))
    enemies(s, room)
    if hero:
        drawing, x, y, mirror = hero
        sprite(s, drawing, x, y, mirror)
    return s


# ------------------------------------------------------------------
# The title screen
# ------------------------------------------------------------------
TITLE_BAND = ["#######GG#######",
              "#T#####GG#####t#",
              "##.....GG.....##",
              "################"]


def logo_squares(word, row):
    """The pixels inside the letters of a word of the logo font:
    squares of 2 x 2 pixels, letters 20 x 24 pixels, 2 apart, the word
    centred. Returns (set of (x, y), x0, width)."""
    width = len(word) * 22 - 2
    x0 = (256 - width) // 2
    y0 = row * 8
    inside = set()
    for i, ch in enumerate(word):
        if ch == ' ':
            continue
        for gy, line in enumerate(P.LOGO[ch]):
            for gx, v in enumerate(line):
                if v == '#':
                    for y in range(2):
                        for x in range(2):
                            inside.add((x0 + i * 22 + gx * 2 + x,
                                        y0 + gy * 2 + y))
    return inside, x0, width


def logo_drips(word, row):
    """The drips of moss under the letters: (x, length) each, as the
    logo draws them from y0 + 24 down."""
    inside, x0, width = logo_squares(word, row)
    y = row * 8 + 23
    drips, last = [], -9
    for x in range(x0, x0 + width):
        if (x, y) not in inside or (x - 1, y) not in inside or \
                (x + 1, y) not in inside:
            continue
        if x - last < 4 or h(x, 3) >= 30:
            continue
        last = x
        drips.append((x, 3 + h(x, 7) % 5))     # a drip of moss
    return drips


def logo(s, word, row, pal, bright='logo', normal='logo2', moss=True):
    """Letters of stone, 20 x 24 pixels, 2 apart, centred, on rows
    row to row + 2 (the first two in the bright colour); with moss,
    green moss drips from them into the row below."""
    inside, x0, width = logo_squares(word, row)
    y0 = row * 8
    for (x, y) in inside:
        up = (x, y - 1) in inside
        left = (x - 1, y) in inside
        down = (x, y + 1) in inside
        right = (x + 1, y) in inside
        ly = y - y0
        if not up or not left:
            v = 1                               # lit edge
        elif not down or not right:
            v = 0                               # shadow edge
        elif ly in (7, 15):
            v = 0                               # joints of the courses
        elif ly in (6, 14):
            v = (x + y) % 2                     # their shaded edge
        else:
            v = 1
        s.px[y][x] = v
    for c in range(32):
        s.at[row][c] = pal[bright]
        s.at[row + 1][c] = pal[bright]
        s.at[row + 2][c] = pal[normal]
        if moss:
            s.at[row + 3][c] = pal['moss']
    if not moss:
        return
    y = y0 + 23
    for x, length in logo_drips(word, row):
        for k in range(1, length + 1):
            s.px[y + k][x] = 1
        if length > 4:
            s.px[y + length][x + 1] = 1
            s.px[y + length + 1][x] = s.px[y + length + 1][x + 1] = 1


def title_screen(machine='128', controls='KEMPSTON', choice=0, phase=0,
                 sprites=True):
    pal = ZONES['atrio']
    s = Screen()
    for row in range(24):
        for c in range(32):
            s.at[row][c] = pal['menu']
    logo(s, 'CRYPTMORROW', 1, pal)
    render_grid(s, TITLE_BAND, 'atrio', phase=phase, top=6)
    if sprites:
        sprite(s, P.HERO_DOWN, 120, 6 * 8 + 32)
        sprite(s, P.SKELETON, 52, 6 * 8 + 32)
        sprite(s, P.BAT, 184, 6 * 8 + 30)
    items = ['MUSIC', 'SOUND FX', 'SILENT'] if machine == '128' else \
        ['SOUND FX', 'SILENT']
    for i, item in enumerate(items):
        on = i == choice
        a = pal['menu_on'] if on else pal['menu']
        text(s, 11, 15 + i, ('> ' if on else '  ') + item, a)
    text(s, 7, 19, 'CONTROLS ' + controls, pal['note'])
    text(s, 11, 21, 'PRESS FIRE', pal['hud'])
    text(s, 6, 23, '(C) 2026 ERIC A. NORTON', pal['num'])
    return s


# ------------------------------------------------------------------
# The end screens: the big word in
# the letters of the logo, a band of the crypt (after a lost game the
# bones of zone A before the shut gate; after a won game the open
# gate), the score, the seals and the rooms explored, PRESS FIRE.
# ------------------------------------------------------------------
END_LOST_BAND = ["#######GG#######",
                 "#n#T###GG###t#n#",
                 "#b..b..GG..b..b#",
                 "################"]
END_WON_BAND = ["#######GG#######",
                "#T#####GG#####t#",
                "##.m...GG...m.##",
                "################"]


def end_screen(won, score=0, seals=0, rooms=0, prompt=True, phase=0):
    pal = ZONES['atrio']
    s = Screen()
    if won:
        logo(s, 'VICTORY', 1, pal, 'won', 'won2', moss=False)
        render_grid(s, END_WON_BAND, 'atrio', phase=phase, gate='open',
                    top=6)
    else:
        logo(s, 'GAME OVER', 1, pal, 'lost', 'lost2', moss=False)
        render_grid(s, END_LOST_BAND, 'A', phase=phase, top=6)
    text(s, 10, 15, 'SCORE', pal['num'])
    text(s, 16, 15, f'{score:06d}', pal['hud'])
    text(s, 10, 16, 'SEALS', pal['num'])
    text(s, 16, 16, f'{seals}/3', pal['hud'])
    text(s, 10, 17, 'ROOMS', pal['num'])
    text(s, 16, 17, f'{rooms:02d}/16', pal['hud'])
    if prompt:
        text(s, 11, 21, 'PRESS FIRE', pal['hud'])
    return s


# ------------------------------------------------------------------
# The loading screen. Under the
# logo, a view down the crypt in one-point perspective: the near wall
# and its doorway (stones twice the size, two torches, moss), a second
# doorway, and at the end the shut gate of the Moss Gate between two
# torches, the three seals before its steps, a skeleton on guard and a
# bat; near, twice the size, the explorer seen from behind. A wall at
# depth z is drawn 1/z the size; the eye is at y = EYE. The light of
# the torches is a denser half-tone; the far walls have less of it.
# ------------------------------------------------------------------
EYE = 96                    # the vanishing point is (128, EYE)
DROP = 80                   # the floor under the eye at depth 1
DOOR_W, DOOR_TOP = 80, 50   # a doorway at depth 1: half width, arch
RING = 12                   # its ring of voussoirs
NEAR, SECOND, END = 1.0, 1.43, 2.0          # the depths of the walls
VIEW_TOP, VIEW_BOTTOM = 40, 176             # pixel rows of the view


def masonry(x, y, bw, bh, fill=2):
    """Bricks bw x bh laid with a stagger of half a brick, lit top and
    left edge, dark bottom and right edge (brick_mass at any size);
    the face in half-tone: fill 2 every other pixel, 4 one in four,
    0 none."""
    row = math.floor(y / bh)
    xx = (x + (bw / 2 if row % 2 else 0)) % bw
    yy = y - row * bh
    if yy >= bh - 1 or xx >= bw - 1:
        return 0
    if yy < 1 or xx < 1:
        return 1
    if yy >= bh - 2 or xx >= bw - 2:
        return 0
    if fill == 2:
        return 1 if (x + y) % 2 == 0 else 0
    if fill == 4:
        return 1 if x % 2 == 0 and y % 2 == 0 else 0
    return 0


def in_doorway(x, y, z):
    """Is the pixel inside the doorway of the wall at depth z (jambs
    up to the eye, then a half ellipse)?"""
    hw = DOOR_W / z
    if y >= EYE + DROP / z:
        return False
    if y >= EYE:
        return abs(x - 128) < hw
    return ((x - 128) / hw) ** 2 + ((y - EYE) / (DOOR_TOP / z)) ** 2 < 1


def voussoirs(x, y, z):
    """The pixel of the ring of stones round the doorway at depth z,
    or None outside it: jambs of stones 10/z high, an arch of
    voussoirs every 15 degrees."""
    hw, w, ry = DOOR_W / z, RING / z, DOOR_TOP / z
    if y >= EYE + DROP / z:
        return None
    dx = x - 128
    if y >= EYE:
        d = abs(dx) - hw
        if not 0 <= d < w:
            return None
        k = (y - EYE) / (10 / z)
        if d >= w - 1 or (k - math.floor(k)) * (10 / z) < 1:
            return 0
        return 1 if d < 1 or (x + y) % 2 == 0 else 0
    inner = (dx / hw) ** 2 + ((y - EYE) / ry) ** 2
    outer = (dx / (hw + w)) ** 2 + ((y - EYE) / (ry + w)) ** 2
    if inner < 1 or outer >= 1:
        return None
    angle = math.degrees(math.atan2(EYE - y, dx)) % 180
    gap = min(abs(angle - j) for j in range(15, 180, 15))
    if math.radians(gap) * math.hypot(dx, (y - EYE) * hw / ry) < 0.8:
        return 0                                # a joint
    if outer > 0.93:
        return 0                                # the outer edge
    if inner < 1.06:
        return 1                                # the lit inner edge
    return 1 if (x + y) % 2 == 0 else 0


def flagstone(x, y):
    """The floor in perspective (y below the eye): rows of stones 0.16
    deep, joints every 24 across, staggered; dotted joints."""
    z = DROP / (y - EYE)
    across = (x - 128) * z
    row = math.floor(z / 0.16)
    if (z - row * 0.16) * DROP / (z * z) < 1:
        return 1 if x % 2 == 0 else 0           # a joint across
    if (across + (12 if row % 2 else 0)) % 24 < z:
        return 1 if y % 2 == 0 else 0           # a joint along
    return 0


def scaled(rows, k):
    """A drawing k times the size."""
    out = []
    for r in rows:
        out += [''.join(ch * k for ch in r)] * k
    return out


def figure(s, rows, x0, y0):
    """A masked drawing of any size, as sprite() draws 16 x 16."""
    hh, ww = len(rows), len(rows[0])
    for y in range(hh):
        for x in range(ww):
            near = any(0 <= y + dy < hh and 0 <= x + dx < ww and
                       rows[y + dy][x + dx] == '#'
                       for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            if near:
                s.px[y0 + y][x0 + x] = 1 if rows[y][x] == '#' else 0


def paint(s, rows, x0, y0):
    """A drawing over the screen: '#' ink, '.' paper, ',' keep."""
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in '#.':
                s.px[y0 + y][x0 + x] = 1 if ch == '#' else 0


LOADING_TORCHES = (96, 152)                 # x of the far torches
LOADING_MOSS = ((0, 5), (1, 5), (2, 5), (0, 6), (11, 5), (12, 5),
                (12, 6), (19, 5), (20, 5), (29, 5), (30, 5), (31, 5),
                (31, 6), (0, 18), (0, 19), (1, 19), (31, 18),
                (30, 19), (31, 19))
LOADING_SEALS = (100, 124, 148)             # x of the seals, row 17


def loading_screen():
    pal = ZONES['atrio']
    s = Screen()
    for row in range(24):
        for c in range(32):
            s.at[row][c] = pal['mass']
    logo(s, 'CRYPTMORROW', 1, pal)
    for y in range(VIEW_TOP, VIEW_BOTTOM):
        for x in range(256):
            if not in_doorway(x, y, NEAR):
                v = voussoirs(x, y, NEAR)
                if v is None:
                    v = masonry(x, y, 32, 16)
            elif not in_doorway(x, y, SECOND):
                if y >= EYE + DROP / SECOND:
                    v = flagstone(x, y)
                else:
                    v = voussoirs(x, y, SECOND)
                    if v is None:
                        v = masonry(x, y, 22, 11, 4)
            elif y >= EYE + DROP / END:
                v = flagstone(x, y)
            else:                               # the end wall
                d = min(math.hypot(x - tx - 4, (y - 100) * 1.3)
                        for tx in LOADING_TORCHES)
                v = masonry(x, y, 16, 8, 2 if d < 16 else
                            4 if d < 30 else 0)
            s.px[y][x] = v
    for tx in LOADING_TORCHES:                  # the far torches
        paint(s, P.FLAME[0], tx, 96)
        paint(s, P.BRACKET, tx, 104)
        s.at[12][tx // 8] = pal['flame']
    gate = gate_tile('closed')
    for y in range(48):
        s.px[88 + y][112:144] = gate.px[y]
    for cy, row in enumerate(gate.roles):
        for cx, role in enumerate(row):
            s.at[11 + cy][14 + cx] = pal[role]
    for tx in (8, 232):                         # the near torches
        flame = scaled(P.FLAME[1], 2)
        paint(s, [r.replace(',', '.') for r in flame], tx, 80)
        paint(s, scaled(P.BRACKET, 2), tx, 96)
        for cy in (10, 11):
            s.at[cy][tx // 8] = s.at[cy][tx // 8 + 1] = pal['flame']
    for (cx, cy) in LOADING_MOSS:
        pattern = P.MOSS_MASS[(cx + cy) % 2]
        for y in range(8):
            for x in range(8):
                ch = pattern[y][x]
                if ch == '#' or (ch == 'o' and (x + y) % 2 == 0):
                    s.px[cy * 8 + y][cx * 8 + x] = 1
        s.at[cy][cx] = pal['moss']
    for x in LOADING_SEALS:                     # on a dark floor
        for c in (x // 8, (x + 7) // 8):
            for y in range(136, 144):
                s.px[y][c * 8:c * 8 + 8] = [0] * 8
            s.at[17][c] = pal['seal']
        paint(s, P.SEAL_ICON, x, 136)
    figure(s, P.SKELETON, 80, 128)
    figure(s, P.BAT, 168, 72)
    figure(s, scaled(P.HERO_UP, 2), 112, 144)
    text(s, 4, 23, '(C) 2026 ERIC A. NORTON', pal['num'])
    return s


if __name__ == '__main__':
    out = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
    s = room_screen('moss_gate', (P.HERO_DOWN, 120, 128, False))
    (out / 'moss_gate.png').write_bytes(s.png())
    (out / 'title.png').write_bytes(title_screen().png())

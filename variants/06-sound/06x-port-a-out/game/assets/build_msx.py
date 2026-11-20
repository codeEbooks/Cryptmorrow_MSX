"""Cryptmorrow MSX: turn the graphics into the data of Screen 2.

art.py (from the ZX game, unchanged) draws every room as the
Spectrum shows it: pixels, and one role per character cell ('mass',
'face', 'flame'...). This builder renders those pictures with a
palette that answers with the role, recolours every cell for the
TMS9918A and cuts them into what the MSX program keeps in the
cartridge:

  cells      for every zone and every third of the screen, the
             different cells (8 pattern bytes and a colour) that its
             rooms use there, numbered from 0: the slots of that
             third's pattern and colour tables
  metatiles  for every zone, its 16 x 16 pieces: the slots of their
             four cells in each third where they appear (12 bytes)
  solid      for every zone, the solid kind of each metatile, the
             same for its four cells: 0 free, 1
             solid (walls, pillars, the well, the altar, water,
             urns), 2 a locked door or the gate of the portal
             (SOLID_DOOR in the data, defined in
             game/src/room.asm)
  maps       16 x 10 metatile numbers per room, the room's zone and
             name
  objects    the two object slots of every room: kind
             (keys 1-3, seal 4, treasure 5, potion 6), column, row and
             its metatile, the floor with the object drawn over it
  doors      the door of every room (1-3 the locked
             doors A-C, 4 the portal) and its open tiles, drawn by
             art.py with the door open (a locked door as an opening,
             the portal as the open gate): column, row, metatile and
             the solid cells (the posts of the open portal)
  shapes     the 8 images of the explorer (art_pieces.HERO_FRAMES) in
             two layers, two 16 x 16 sprites one over the other:
             the skin (the face below the
             hat brim, the hands) and the clothes (the hat, the coat,
             the legs; from behind the head too). 32 bytes a sprite,
             the left 8 columns then the right 8: the 8 skins, then
             the 8 clothes
  flames     the four phases of the flame cell, for a torch with the
             flame on the left and on the right; for every zone the
             slots that hold a flame (the program rewrites them)
  glyphs     the fixed slots of the HUD (third 0) and of the room's
             name (third 2): letters, digits, icons, bar, rules
  gradients  the colours of a cell row by row (version B)
  bands      the bands of the title and of the two end
             screens (art.py: TITLE_BAND, END_WON_BAND, END_LOST_BAND,
             16 x 4 metatiles drawn from row 6), cut like the rooms:
             their metatiles join their zone's (atrium, atrium, A), in
             its rows 2-5, so that their cells have slots in thirds 0
             and 1; their own cells come after the rooms' (the game
             loads only those: the screens are drawn from the
             cartridge)
  big        the letters of the logo (art_pieces.LOGO:
             12 rows of 10 squares), each row already doubled to 20
             pixels (3 bytes, the leftmost pixel in bit 7); the three
             big words (the logo, VICTORY, GAME OVER): first pixel
             column, character row, colours; the drips of moss under
             the logo (art.logo_drips)
  text       the font of the texts of the title and of
             the end screens (art_pieces.FONT) and their colours
  opening    the opening screen: art.py's loading
             screen of the ZX game (the crypt in perspective, the shut
             gate, the seals, the explorer from behind), recoloured;
             rows 5-22 as names of the different cells of each third
             (third 0 from slot OPEN_BASE, after the slots of the
             logo's rows), the cells; the logo and the credit are drawn
             as on the title (big letters, text)

Colours. A ZX attribute (ink, paper, BRIGHT) becomes a TMS colour
by ZX_TO_TMS. A cell's colour is one byte (ink << 4 | paper) for
all its rows; a byte below #10 (ink 0, transparent, never used) is
instead the number of a gradient: 8 bytes, one per row.

Two versions of the graphics (question 3 of Phase A; the author
chose B on 8 November, "B, much the better graphics"):
  A  the ZX pixels and colours, recoloured: one colour per cell
  B  the same, with colours row by row where the MSX can do more:
     the flame red at the tip and yellow at the base, the moss in
     three greens (light above), the water in bands, the well's
     water in two blues
The game uses B; A is written only on request (--version A).

Writes game/assets/generated/<B|A>/gfx_*.asm, seven files in the
order of the cartridge (lines of at most 60 characters, for sjasmplus
and pasmo), and gfx.json (the same data, for the tests):

  gfx_zones.asm     the slots of the HUD and of the name, the
                    gradients, the flames, the glyphs, the four zones
  gfx_explorer.asm  the explorer's images
  gfx_combat.asm    the images of the combat
  gfx_rooms.asm     the sixteen rooms
  gfx_screens.asm   the title and the end screens
  gfx_opening.asm   the opening screen
  gfx_doors.asm     the doors

A step of the book's chain includes only the files it uses
(game/src/cryptmorrow.asm); the complete game includes all seven, in
this order. The tests' model does not read these: it recolours
art.py's pictures and finds the solid cells by itself
(tests/msx_model.py).

Usage: python game/assets/build_msx.py [--version A]
Standard library only.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / 'tools'))
import art  # noqa: E402
import art_pieces as P  # noqa: E402
import dungeon  # noqa: E402

OUT = HERE / 'generated'
ZONES = dungeon.ZONES                       # atrio, A, B, C = 0-3
K, B, R, M, G, C, Y, W = range(8)           # Spectrum colours
# ZX colour (normal, bright) -> TMS9918A colour
ZX_TO_TMS = {K: (1, 1), B: (4, 5), R: (6, 8), M: (13, 13),
             G: (12, 2), C: (7, 7), Y: (10, 11), W: (14, 15)}
# Version B: roles coloured row by row, when their colour in A is the
# one named: role: (ink or paper, its A colour, the 8 new colours)
GRADIENTS = {
    'flame': ('ink', 11, [8, 9, 9, 10, 10, 11, 11, 11]),
    'moss': ('ink', 12, [3, 3, 2, 2, 2, 12, 12, 12]),
    'mossface': ('ink', 12, [3, 3, 2, 2, 2, 12, 12, 12]),
    'fmoss': ('ink', 12, [3, 3, 2, 2, 2, 12, 12, 12]),
    'water': ('paper', 7, [7, 7, 5, 5, 7, 7, 5, 5]),
    'wellwater': ('ink', 5, [5, 5, 4, 4, 5, 5, 4, 4]),
}
FLAME_MAX = 6                   # flame_list in game/src/vars.asm
# the symbols of a room that the explorer cannot enter (the ZX rule)
SOLID = set(dungeon.WALLS) | set('GPWAwuD')
SOLID_DOOR = 2                  # a locked door: SOLID_DOOR in the data
FIRST_GLYPH = 0xE0              # slots E0-FF of thirds 0 and 2
ROOM_SLOTS = FIRST_GLYPH        # room cells: slots 0 to DF
# third 0 (the HUD)
HUD_BLANK, RULE_TOP = 0xE0, 0xE1
HUD_LETTERS = 'ENRGYSCO'        # slots E2-E9
BAR_FULL, BAR_HALF, BAR_EMPTY = 0xEA, 0xEB, 0xEC
KEY_ICON, SEAL_ICON, SLASH = 0xED, 0xEE, 0xEF
DIGIT_0 = 0xF0                  # F0-F9
# third 2 (the name)
NAME_BLANK, RULE_BOTTOM, LETTER_A = 0xE0, 0xE1, 0xE2   # A-Z: E2-FB


def tms(attr, bright_override=None):
    """(ink, paper) of a ZX attribute, as TMS colours."""
    ink, paper, bright = attr & 7, (attr >> 3) & 7, (attr >> 6) & 1
    return ZX_TO_TMS[ink][bright], ZX_TO_TMS[paper][bright]


def colour_rows(zone, role, version):
    """The 8 colour bytes of a cell of this role."""
    ink, paper = tms(art.ZONES[zone][role])
    inks, papers = [ink] * 8, [paper] * 8
    if version == 'B' and role in GRADIENTS:
        which, was, rows = GRADIENTS[role]
        if which == 'ink' and ink == was:
            inks = rows
        elif which == 'paper' and paper == was:
            papers = rows
    return tuple((i << 4) | p for i, p in zip(inks, papers))


def cell_bytes(s, row, col):
    out = []
    for y in range(8):
        b = 0
        for bit in s.px[row * 8 + y][col * 8:col * 8 + 8]:
            b = (b << 1) | bit
        out.append(b)
    return tuple(out)


class RolePalette(dict):
    """Answers with the role itself: rendering with it leaves in the
    attributes which role every cell has."""

    def __missing__(self, role):
        return role


def opened_grid(room):
    """The room's map with its door open (milestone 0.4): a locked
    door drawn as an opening (D as E), the portal as the open gate (G
    as O)."""
    return [row.replace('D', 'E').replace('G', 'O') for row in room.grid]


def role_screen(name, phase=0, gate='closed', hud=True, objects=False,
                opened=False):
    """art.py's room screen, with roles in place of attributes;
    objects: with the room's objects; opened: with its door open."""
    room = dungeon.load_room(name)
    s = art.Screen()
    pal = RolePalette()
    zones, base = art.ZONES, art.BASE
    art.ZONES = {z: pal for z in zones}
    art.BASE = pal
    grid = opened_grid(room) if opened else room.grid
    try:
        art.render_grid(s, grid, room.zone,
                        room.objects if objects else (), phase, gate)
        if hud:
            art.hud(s, pal, name=room.title)
    finally:
        art.ZONES, art.BASE = zones, base
    return room, s


def room_names():
    slots, start = dungeon.load_dungeon()
    return slots, start


def flame_type(room, mc, mr):
    return 1 if room.grid[mr][mc] == 't' else 0     # 0 left, 1 right


# -- milestone 0.7: the title and the end screens -------------------------

# the bands: art.py's grid, its zone, the state of the gate
BANDS = {'title': (art.TITLE_BAND, 'atrio', 'closed'),
         'won': (art.END_WON_BAND, 'atrio', 'open'),
         'lost': (art.END_LOST_BAND, 'A', 'closed')}
BAND_ROW = 6                    # character row of the band's top
BAND_H = 4                      # metatiles down
BAND_MR = (BAND_ROW - art.TOP) // 2     # as rows 2-5 of a room
# the big words: art.py's title_screen and end_screen
WORDS = {'logo': ('CRYPTMORROW', 1, 'logo', 'logo2', True),
         'won': ('VICTORY', 1, 'won', 'won2', False),
         'lost': ('GAME OVER', 1, 'lost', 'lost2', False)}
TEXT_CHARS = ' ()./0123456789>' + ''.join(chr(65 + i) for i in range(26))
TEXT_ROLES = ('menu', 'menu_on', 'hud', 'num')
NO_MOSS = 0xFF                  # a big word without moss


class BandRoom:
    """What metatile() and flame_type() read of a room: its grid, the
    band in rows 2-5."""

    def __init__(self, grid):
        self.grid = ['.' * dungeon.MAP_W] * BAND_MR + list(grid)


def band_screen(grid, zone, gate):
    """art.py's band on a screen of roles, from row BAND_ROW."""
    s = art.Screen()
    pal = RolePalette()
    zones, base = art.ZONES, art.BASE
    art.ZONES = {z: pal for z in zones}
    art.BASE = pal
    try:
        art.render_grid(s, grid, zone, (), 0, gate, top=BAND_ROW)
    finally:
        art.ZONES, art.BASE = zones, base
    return s


def big_data(colour_code, version):
    """The letters of the logo font doubled to 20 pixels a row, the
    three words, the drips under the logo."""
    letters = sorted({ch for w in WORDS.values() for ch in w[0]} - {' '})
    font = {}
    for ch in letters:
        rows = []
        for line in P.LOGO[ch]:
            bits = 0
            for v in line:
                bits = (bits << 2) | (3 if v == '#' else 0)
            rows.append([(bits << 4) >> 16 & 255, (bits << 4) >> 8 & 255,
                         (bits << 4) & 255])
        font[ch] = rows
    words = {}
    for name, (word, row, bright, normal, moss) in WORDS.items():
        inside, x0, width = art.logo_squares(word, row)
        words[name] = {
            'word': word, 'x0': x0, 'row': row,
            'colours': [colour_code(colour_rows('atrio', r, version))
                        for r in (bright, normal)] +
                       [colour_code(colour_rows('atrio', 'moss', version))
                        if moss else NO_MOSS],
            'inside': sorted(inside)}
    return {'letters': ''.join(letters), 'font': font, 'words': words,
            'drips': art.logo_drips('CRYPTMORROW', 1)}


def text_data(version):
    def font(ch):
        return [int(''.join('1' if q == '#' else '0' for q in r), 2)
                for r in P.FONT[ch]]
    colours = {}
    for role in TEXT_ROLES:
        rows = colour_rows('atrio', role, version)
        assert len(set(rows)) == 1, role
        colours[role] = rows[0]
    return {'chars': TEXT_CHARS,
            'font': [font(ch) for ch in TEXT_CHARS], 'colours': colours}


OPEN_ROWS = range(5, 23)        # the view; 0-4 the logo, 23 the credit
OPEN_BASE = (160, 0, 0)         # the first slot of each third's cells
OPEN_CREDIT = (23, 4)           # row, column of the credit


def opening_data(colour_code, version):
    """The opening screen: names of rows OPEN_ROWS, the cells of each
    third (pattern, colour code)."""
    s = art.Screen()
    pal = RolePalette()
    zones, base = art.ZONES, art.BASE
    art.ZONES = {z: pal for z in zones}
    art.BASE = pal
    try:
        s = art.loading_screen()
    finally:
        art.ZONES, art.BASE = zones, base
    thirds, names = [[], [], []], []
    for r in OPEN_ROWS:
        t = r // 8
        for c in range(32):
            key = (cell_bytes(s, r, c),
                   colour_code(colour_rows('atrio', s.at[r][c], version)))
            if key not in thirds[t]:
                thirds[t].append(key)
            names.append(OPEN_BASE[t] + thirds[t].index(key))
    top = (OPEN_ROWS[0] % 8) * 32      # third 0: the logo's slots
    if OPEN_BASE[0] < top or OPEN_BASE[0] % 32 or \
            OPEN_BASE[0] + len(thirds[0]) > 256:
        raise ValueError('opening: third 0 does not fit')
    if len(thirds[1]) > 256 or len(thirds[2]) > 7 * 32:
        raise ValueError('opening: thirds 1-2 do not fit (row 23: the '
                         'credit\'s slots)')
    return {'names': names, 'base': list(OPEN_BASE),
            'cells': [[{'pattern': list(p), 'colour': col}
                       for p, col in th] for th in thirds]}


def build(version):
    slots, start = room_names()
    rooms = []                       # (number, name, room, screen)
    for number, name in enumerate(slots):
        if name:
            room, s = role_screen(name)
            rooms.append((number, name, room, s))
    gradients = []                   # the different 8-row colours

    def colour_code(rows):
        if len(set(rows)) == 1:
            return rows[0]
        if rows not in gradients:
            gradients.append(rows)
        return gradients.index(rows)
    # flames: 2 types x 4 phases, from the drawings of a room
    flames = {}
    for number, name, room, s in rooms:
        for mr in range(dungeon.MAP_H):
            for mc in range(dungeon.MAP_W):
                if room.grid[mr][mc] not in 'Tt':
                    continue
                ft = flame_type(room, mc, mr)
                col = mc * 2 + ft
                row = art.TOP + mr * 2
                for ph in range(4):
                    _, sp = role_screen(name, ph)
                    pat = cell_bytes(sp, row, col)
                    assert sp.at[row][col] == 'flame'
                    old = flames.setdefault((ft, ph), pat)
                    assert old == pat, 'flame differs between torches'
    zone_data = {}
    for zi, zone in enumerate(ZONES):
        mts = []                     # metatiles: 4 cell keys
        third_cells = [[], [], []]   # per third: cell keys in order
        mt_thirds = []               # per metatile: thirds it is in
        maps, objects, doors = {}, {}, {}

        def metatile(s, room, mc, mr, solid):
            """The number of the metatile at column mc, row mr of the
            screen s, with this solid kind."""
            third = (art.TOP + mr * 2) // 8
            keys = []
            for dy in range(2):
                for dx in range(2):
                    row = art.TOP + mr * 2 + dy
                    col = mc * 2 + dx
                    role = s.at[row][col]
                    rows = colour_rows(zone, role, version)
                    if role == 'flame':
                        key = ('flame', flame_type(room, mc, mr),
                               colour_code(rows))
                    else:
                        key = (cell_bytes(s, row, col),
                               colour_code(rows))
                    keys.append(key)
            keys = (tuple(keys), solid)
            if keys not in mts:
                mts.append(keys)
                mt_thirds.append(set())
            k = mts.index(keys)
            mt_thirds[k].add(third)
            for key in keys[0]:
                if key not in third_cells[third]:
                    third_cells[third].append(key)
            return k
        for number, name, room, s in rooms:
            if room.zone != zone:
                continue
            m = []
            for mr in range(dungeon.MAP_H):
                for mc in range(dungeon.MAP_W):
                    sym = room.grid[mr][mc]
                    solid = SOLID_DOOR if sym in 'DG' else \
                        1 if sym in SOLID else 0
                    m.append(metatile(s, room, mc, mr, solid))
            maps[number] = m
            # the objects (milestone 0.4): the floor of their place
            # with the object over it, as art.py draws the room with
            # its objects
            _, so = role_screen(name, objects=True)
            objects[number] = [
                {'kind': room.code(kind, letter), 'col': c, 'row': r,
                 'metatile': metatile(so, room, c, r, 0)}
                for kind, letter, c, r in room.objects]
            # the door, opened: its tiles as art.py draws the open
            # door; free, but for the two posts of the portal's arch
            # (the left cells of its left tiles, the right cells of
            # its right ones, in the top two rows): a mask of solid
            # cells, bits 0-3 top left, top right, bottom left,
            # bottom right
            if room.door:
                tiles, _ = dungeon.door_tiles(room)
                _, sd = role_screen(name, opened=True)
                left = min(c for c, r in tiles)
                lst = []
                for c, r in tiles:
                    mask = 0
                    if room.door == dungeon.PORTAL and r < 2:
                        mask = 0b0101 if c == left else 0b1010
                    lst.append([c, r, metatile(sd, room, c, r, 0), mask])
                doors[dungeon.DOOR_NUMBERS[room.door]] = (number, lst)
        # the cells the game uses: load_zone loads only these; the
        # bands' own cells come after them, for the title and the
        # end screens (drawn from the cartridge)
        game_cells = [len(third_cells[t]) for t in range(3)]
        # the bands of the title and of the end screens
        # (milestone 0.7), as rows 2-5 of a room of their zone
        bands = {}
        for bname, (grid, bzone, gate) in BANDS.items():
            if bzone != zone:
                continue
            bs = band_screen(grid, zone, gate)
            broom = BandRoom(grid)
            m = []
            for br in range(BAND_H):
                for mc in range(dungeon.MAP_W):
                    m.append(metatile(bs, broom, mc, br + BAND_MR, 0))
            bands[bname] = m
        for t in range(3):
            if game_cells[t] == 0 and third_cells[t]:
                raise ValueError(f'zone {zone} third {t}: cells of '
                                 'the bands only')
            if len(third_cells[t]) > ROOM_SLOTS:
                raise ValueError(f'zone {zone} third {t}: '
                                 f'{len(third_cells[t])} cells, more '
                                 f'than {ROOM_SLOTS} slots')
        if len(mts) > 256:
            raise ValueError(f'zone {zone}: {len(mts)} metatiles')
        table = []
        for k, (keys, solid) in enumerate(mts):
            rec = []
            for t in range(3):
                for key in keys:
                    rec.append(third_cells[t].index(key)
                               if t in mt_thirds[k] else 0)
            table.append(rec)
        flame_slots = []
        for t in range(3):
            for i, key in enumerate(third_cells[t]):
                if key[0] == 'flame':
                    flame_slots.append((t, i, key[1]))
        if len(flame_slots) > FLAME_MAX:
            raise ValueError(f'zone {zone}: {len(flame_slots)} flame '
                             f'slots, more than {FLAME_MAX}')
        zone_data[zone] = {
            'cells': [[{'pattern': list(flames[(key[1], 0)])
                        if key[0] == 'flame' else list(key[0]),
                        'colour': key[-1]} for key in third_cells[t]]
                      for t in range(3)],
            'game_cells': game_cells,
            'metatiles': table, 'maps': maps,
            'solid': [solid for keys, solid in mts],
            'flames': flame_slots, 'objects': objects, 'doors': doors,
            'bands': bands}
    glyphs = glyph_cells(version, colour_code)
    room_list = []
    for number, name, room, s in rooms:
        if not (len(room.title) <= 31 and
                set(room.title) <= set(' ABCDEFGHIJKLMNOPQRSTUVWXYZ')):
            raise ValueError(f'{name}: the name {room.title!r} is not '
                             'letters and spaces, 31 at most')
        zd = zone_data[room.zone]
        door = dungeon.DOOR_NUMBERS[room.door] if room.door else 0
        room_list.append({'number': number, 'name': name,
                          'zone': ZONES.index(room.zone),
                          'title': room.title,
                          'map': zd['maps'][number], 'door': door,
                          'objects': zd['objects'][number],
                          'enemies': [
                              {'kind': dungeon.ENEMIES[kind],
                               'col': c, 'row': r,
                               'flags': (dungeon.AXES[axis] if axis
                                         else 0) |
                               (dungeon.FAST if fast else 0)}
                              for kind, c, r, axis, fast
                              in room.enemies],
                          'door_list': zd['doors'][door][1]
                          if door else []})
    bands = {name: {'zone': ZONES.index(bz),
                    'map': zone_data[bz]['bands'][name]}
             for name, (g, bz, gate) in BANDS.items()}
    for zd in zone_data.values():
        del zd['objects'], zd['doors'], zd['bands']
    won = tms(art.BASE['won'])
    lost = tms(art.BASE['lost'])
    return {'version': version, 'start': start, 'zones': ZONES,
            'won_colour': won[0] << 4 | won[1],
            'lost_colour': lost[0] << 4 | lost[1],
            'zone_data': zone_data, 'rooms': room_list,
            'flames': {f'{ft}{ph}': list(p)
                       for (ft, ph), p in sorted(flames.items())},
            'glyphs': glyphs, 'gradients': [list(g) for g in gradients],
            'shapes': [sprite_bytes(layer(f, n, 'skin'))
                       for n, f in enumerate(P.HERO_FRAMES)] +
                      [sprite_bytes(layer(f, n, 'clothes'))
                       for n, f in enumerate(P.HERO_FRAMES)],
            'combat': [sprite_bytes(f) for f in P.COMBAT_FRAMES],
            'bands': bands,
            'big': big_data(colour_code, version),
            'text': text_data(version),
            'opening': opening_data(colour_code, version)}


def layer(rows, n, which):
    """The pixels of image n (0-7, the order of HERO_FRAMES: down,
    down step, up, up step, left, left step, right, right step) that
    belong to one layer. The skin: the rows under the hat brim to row
    7 (not from behind, where it is the hair), and the hands on row
    11 (the outer pixels: columns 0-3 and 12-15 seen from the front
    or behind; columns 4, 5, 10, 11 in profile). The clothes: the
    rest."""
    profile, back = n >= 4, n in (2, 3)
    brim = 4 if profile else 3
    hands = (4, 5, 10, 11) if profile else \
        (0, 1, 2, 3, 12, 13, 14, 15)
    out = []
    for y, row in enumerate(rows):
        line = ''
        for x, ch in enumerate(row):
            skin = (brim < y <= 7 and not back) or \
                (y == 11 and x in hands)
            line += ch if (ch == '#' and skin == (which == 'skin')) \
                else '.'
        out.append(line)
    return out


def sprite_bytes(rows):
    """A 16 x 16 drawing as the 32 bytes of a TMS9918A sprite: the
    left column of 16 rows, then the right one."""
    def byte(r, c0):
        return int(''.join('1' if ch == '#' else '0'
                           for ch in rows[r][c0:c0 + 8]), 2)
    return [byte(r, 0) for r in range(16)] + \
        [byte(r, 8) for r in range(16)]


def glyph_cells(version, colour_code):
    """The fixed slots of thirds 0 and 2, from art.py's HUD."""
    _, s = role_screen('moss_gate')         # any room: the HUD
    out = {0: {}, 2: {}}

    def put(third, slot, rows, role):
        cr = colour_rows('atrio', role, version)
        out[third][slot] = {'pattern': list(rows),
                            'colour': colour_code(cr)}

    def font(ch):
        return [int(''.join('1' if p == '#' else '0' for p in r), 2)
                for r in P.FONT[ch]]
    put(0, HUD_BLANK, [0] * 8, 'hud')
    put(0, RULE_TOP, cell_bytes(s, 1, 0), 'rule')
    for i, ch in enumerate(HUD_LETTERS):
        put(0, 0xE2 + i, font(ch), 'hud')
    for slot, energy in ((BAR_FULL, 2), (BAR_HALF, 1), (BAR_EMPTY, 0)):
        hs = art.Screen()
        art.hud(hs, art.ZONES['atrio'], energy=energy)
        put(0, slot, cell_bytes(hs, 0, 7), 'bar')
    put(0, KEY_ICON, cell_bytes(s, 0, 12), 'key')
    put(0, SEAL_ICON, cell_bytes(s, 0, 15), 'seal')
    put(0, SLASH, font('/'), 'num')
    for d in range(10):
        put(0, DIGIT_0 + d, font(str(d)), 'num')
    put(2, NAME_BLANK, [0] * 8, 'name')
    put(2, RULE_BOTTOM, cell_bytes(s, 22, 0), 'rule')
    for i in range(26):
        put(2, LETTER_A + i, font(chr(65 + i)), 'name')
    return {str(t): {f'{k:02X}': v for k, v in sorted(g.items())}
            for t, g in out.items()}


# -- the assembly data ------------------------------------------------

def db_lines(values, per=8):
    out = []
    for i in range(0, len(values), per):
        out.append('        db ' + ','.join(f'#{v:02X}' for v in
                                            values[i:i + per]))
    return out


PARTS = (('zones', 'the slots of the HUD and of the name, the gradients,',
          'the flames, the glyphs, the four zones'),
         ('explorer', 'the explorer\'s images', None),
         ('combat', 'the images of the combat', None),
         ('rooms', 'the sixteen rooms', None),
         ('screens', 'the title and the end screens', None),
         ('opening', 'the opening screen', None),
         ('doors', 'the doors', None))
PART = '\0part '                 # a mark between two parts


def asm_parts(data):
    """The seven files gfx_*.asm: {name: text}, in the cartridge's
    order."""
    v = data['version']
    files = {}
    for chunk in asm(data).split(PART)[1:]:
        name, body = chunk.split('\n', 1)
        _, first, second = next(x for x in PARTS if x[0] == name)
        head = [f'; gfx_{name}.asm - Cryptmorrow MSX graphics, version '
                f'{v}:', f'; {first}']
        if second:
            head.append(f'; {second}')
        head += ['; Generated by game/assets/build_msx.py from art.py:',
                 '; do not edit.', '']
        files[f'gfx_{name}.asm'] = '\n'.join(head) + '\n' + \
            body.strip('\n') + '\n'
    assert list(files) == [f'gfx_{x[0]}.asm' for x in PARTS]
    return files


def asm(data):
    """All the graphics, the parts marked by PART."""
    lines = [PART + 'zones']
    lines += ['; slots of the HUD (third 0) and of the name (third 2)',
              f'HUD_BLANK       equ #{HUD_BLANK:02X}',
              f'BAR_FULL        equ #{BAR_FULL:02X}',
              f'BAR_HALF        equ #{BAR_HALF:02X}',
              f'BAR_EMPTY       equ #{BAR_EMPTY:02X}',
              f'KEY_ICON        equ #{KEY_ICON:02X}',
              f'SEAL_ICON       equ #{SEAL_ICON:02X}',
              f'SLASH           equ #{SLASH:02X}',
              f'DIGIT_0         equ #{DIGIT_0:02X}',
              f'RULE_TOP        equ #{RULE_TOP:02X}',
              f'NAME_BLANK      equ #{NAME_BLANK:02X}',
              f'RULE_BOTTOM     equ #{RULE_BOTTOM:02X}',
              f'LETTER_A        equ #{LETTER_A:02X}',
              f'ROOM_COUNT      equ {len(data["rooms"])}',
              f'START_DEFAULT   equ {data["start"]}',
              f'WON_COLOUR      equ #{data["won_colour"]:02X}'
              '     ; VICTORY',
              f'LOST_COLOUR     equ #{data["lost_colour"]:02X}'
              '     ; GAME OVER',
              f'MAX_ENEMIES     equ {dungeon.MAX_ENEMIES}'
              '       ; enemy slots in a room',
              f'SKELETON        equ {dungeon.ENEMIES["skeleton"]}'
              '       ; enemy kinds',
              f'BAT             equ {dungeon.ENEMIES["bat"]}',
              f'AXIS_FLAG       equ {1 << 0}'
              '       ; flags: up and down',
              f'FAST_FLAG       equ {dungeon.FAST}'
              '       ; every frame', '']
    for i, ch in enumerate(HUD_LETTERS):
        lines.append(f'HUD_{ch}           equ #{0xE2 + i:02X}')
    lines += ['', '; gradients: 8 colour bytes, one a row',
              'gradients:']
    for g in data['gradients']:
        lines += db_lines(g)
    lines += ['', '; the four phases of the flame, left then right',
              'flame_phases:']
    for ft in (0, 1):
        for ph in range(4):
            lines += db_lines(data['flames'][f'{ft}{ph}'])
    lines += ['', '; glyphs: slot, then 8 pattern bytes and a colour',
              'glyphs_top:']
    for slot, g in data['glyphs']['0'].items():
        lines += db_lines([int(slot, 16)] + g['pattern'] +
                          [g['colour']], 10)
    lines += ['        db #00                  ; end (slot 0 = none)',
              'glyphs_bottom:']
    for slot, g in data['glyphs']['2'].items():
        lines += db_lines([int(slot, 16)] + g['pattern'] +
                          [g['colour']], 10)
    lines += ['        db #00                  ; end', '']
    lines += ['; zones: for each third, the number of cells of',
              '; the game and of all (the bands\' come last), then',
              '; their patterns (8 bytes each) and their colours',
              '; (1 byte each); the metatiles (12 bytes: 4 slots',
              '; for each third); their solid kind (1 byte',
              '; each: 0 free, 1 solid, SOLID_DOOR); the flame slots',
              '; (third, slot, type) of the game, then #FE and the',
              '; bands\' own, if any, ending with #FF',
              'zone_table:']
    for z in data['zones']:
        lines.append(f'        dw zone_{z}')
    for z in data['zones']:
        zd = data['zone_data'][z]
        lines += ['', f'zone_{z}:',
                  f'        dw zone_{z}_mt          ; metatiles',
                  f'        dw zone_{z}_so          ; solid kinds',
                  f'        dw zone_{z}_fl          ; flame slots']
        for t in range(3):
            cells = zd['cells'][t]
            lines.append(f'        db {zd["game_cells"][t]},{len(cells)}'
                         .ljust(32) + f'; third {t}: the game\'s, all')
            pats = [b for c in cells for b in c['pattern']]
            lines += db_lines(pats)
            lines += db_lines([c['colour'] for c in cells])
        lines.append(f'zone_{z}_mt:')
        for rec in zd['metatiles']:
            lines += db_lines(rec, 12)
        lines.append(f'zone_{z}_so:')
        lines += [ln.replace(f'#{SOLID_DOOR:02X}', 'SOLID_DOOR')
                  for ln in db_lines(zd['solid'], 4)]
        lines.append(f'zone_{z}_fl:')
        own = [f for f in zd['flames'] if f[1] < zd['game_cells'][f[0]]]
        for t, slot, ft in own:
            lines += db_lines([t, slot, ft])
        if len(own) < len(zd['flames']):
            lines.append('        db #FE                  ; the bands\'')
            for t, slot, ft in zd['flames']:
                if (t, slot, ft) not in own:
                    lines += db_lines([t, slot, ft])
        lines.append('        db #FF')
    lines += [PART + 'explorer',
              '; the explorer: 8 images (down, down step, up, up',
              '; step, left, left step, right, right step) in two',
              '; layers of 16 x 16, 32 bytes a sprite: the 8 skins,',
              '; then the 8 clothes', 'hero_shapes:']
    for shape in data['shapes']:
        lines += db_lines(shape)
    lines += [PART + 'combat',
              '; the combat: skeleton (2), bat (2), dust, the',
              '; blade down, up, left, right; 32 bytes each',
              'combat_shapes:']
    for shape in data['combat']:
        lines += db_lines(shape)
    lines += [PART + 'rooms',
              '; rooms: zone, door (0, 1-3 A-C, 4 the portal), two',
              '; object slots (kind, column, row, metatile; kind 0:',
              '; empty), three enemy slots (kind, column, row,',
              '; flags; kind 0: empty), the map (160 metatile',
              '; numbers), the name (ending with 0); a room of the',
              '; grid that is empty has the word 0', 'room_table:']
    by_number = {r['number']: r for r in data['rooms']}
    for n in range(16):
        lines.append(f'        dw room_{n}' if n in by_number
                     else '        dw 0')
    for r in data['rooms']:
        lines += ['', f'room_{r["number"]}:                 '
                  f'; {r["title"]}'[:60],
                  f'        db {r["zone"]},{r["door"]}']
        for s in range(2):
            o = r['objects'][s] if s < len(r['objects']) else None
            lines.append('        db ' + (
                f"{o['kind']},{o['col']},{o['row']},{o['metatile']}"
                if o else '0,0,0,0'))
        for s in range(dungeon.MAX_ENEMIES):
            e = r['enemies'][s] if s < len(r['enemies']) else None
            lines.append('        db ' + (
                f"{e['kind']},{e['col']},{e['row']},{e['flags']}"
                if e else '0,0,0,0'))
        lines += db_lines(r['map'], 8)   # a map row: 2 lines
        lines.append('        db "' + r['title'] + '",0')
    lines += [PART + 'screens',
              f'BAND_ROW        equ {BAND_ROW}       ; the bands: rows'
              f' {BAND_ROW}-{BAND_ROW + 2 * BAND_H - 1}',
              f'BAND_H          equ {BAND_H}       ; metatiles down',
              f'BAND_MR         equ {BAND_MR}       ; as these rows of'
              ' a room']
    for role in TEXT_ROLES:
        lines.append(f'TEXT_{role.upper():<12}equ #'
                     f'{data["text"]["colours"][role]:02X}')
    lines += ['', '; the bands: their zone, then 4 rows of 16 metatiles']
    for name, band in data['bands'].items():
        lines += [f'band_{name}:', f'        db {band["zone"]}']
        lines += db_lines(band['map'], 8)
    big = data['big']
    lines += ['', '; the letters of the logo font: 12 rows of 20',
              '; pixels (each square doubled), 3 bytes a row',
              f'BIG_COUNT       equ {len(big["letters"])}',
              f'big_letters:    db "{big["letters"]}",0', 'big_font:']
    for ch in big['letters']:
        lines.append(f'        ; {ch}')
        for row in big['font'][ch]:
            lines += db_lines(row)
    lines += ['', '; the big words: first pixel column, character',
              '; row, colours of rows 1-2, of row 3, of the moss',
              '; row under them (NO_MOSS: none), the letters',
              f'NO_MOSS         equ #{NO_MOSS:02X}']
    for name, w in big['words'].items():
        c = w['colours']
        lines += [f'word_{name}:',
                  f'        db {w["x0"]},{w["row"]},#{c[0]:02X},'
                  f'#{c[1]:02X},#{c[2]:02X}',
                  f'        db "{w["word"]}",0']
    lines += ['', '; the drips of moss under the logo: pixel column',
              '; and length; 0 ends', 'logo_drips:']
    for x, n in big['drips']:
        lines.append(f'        db {x},{n}')
    lines.append('        db 0')
    lines += ['', '; the font of the texts: the characters, then 8',
              '; pattern bytes each, in the same order',
              f'TEXT_COUNT      equ {len(data["text"]["chars"])}',
              'text_chars:',
              f'        db "{data["text"]["chars"][:21]}"',
              f'        db "{data["text"]["chars"][21:]}"', 'text_font:']
    for rows in data['text']['font']:
        lines += db_lines(rows)
    op = data['opening']
    lines += [PART + 'opening',
              '; the opening screen: the loading',
              '; screen of the ZX game; for each third the number',
              '; of its cells (twice, as a zone\'s), their patterns',
              '; and colours, from slot OPEN_BASE0 in third 0, 0 in',
              '; thirds 1-2; then the names of rows 5-22. The logo',
              '; and the credit are drawn as on the title',
              f'OPEN_BASE0      equ {op["base"][0]}',
              f'OPEN_ROW        equ {OPEN_ROWS[0]}       ; the names\' first',
              f'OPEN_ROWS       equ {len(OPEN_ROWS)}',
              f'OPEN_CREDIT_ROW equ {OPEN_CREDIT[0]}',
              f'OPEN_CREDIT_COL equ {OPEN_CREDIT[1]}',
              'open_cells:']
    for t, cells in enumerate(op['cells']):
        lines.append(f'        db {len(cells)},{len(cells)}'.ljust(32) +
                     f'; third {t}')
        lines += db_lines([b for c in cells for b in c['pattern']])
        lines += db_lines([c['colour'] for c in cells])
    lines.append('open_names:')
    lines += db_lines(op['names'])
    lines += [PART + 'doors',
              '; doors 1-4: their open tiles (column, row,',
              '; metatile, solid cells: bits 0-3 TL TR BL BR), #FF',
              'door_table:']
    doors = sorted((r['door'], r) for r in data['rooms'] if r['door'])
    lines += [f'        dw door_{d}' for d, r in doors]
    for d, r in doors:
        lines.append(f'door_{d}:                 ; {r["title"]}'[:60])
        for c, row, mt, mask in r['door_list']:
            lines.append(f'        db {c},{row},{mt},%{mask:04b}')
        lines.append('        db #FF')
    return '\n'.join(lines) + '\n'


def main():
    versions = ('A',) if sys.argv[1:] == ['--version', 'A'] else ('B',)
    for version in versions:
        data = build(version)
        out = OUT / version
        out.mkdir(parents=True, exist_ok=True)
        for name, text in asm_parts(data).items():
            (out / name).write_text(text, encoding='ascii')
        (out / 'gfx.json').write_text(json.dumps(data) + '\n',
                                      encoding='ascii')
        counts = {z: [len(data['zone_data'][z]['cells'][t])
                      for t in range(3)] for z in data['zones']}
        mts = {z: len(data['zone_data'][z]['metatiles'])
               for z in data['zones']}
        print(f'version {version}: cells per third {counts}, '
              f'metatiles {mts}, gradients {len(data["gradients"])}')


if __name__ == '__main__':
    main()

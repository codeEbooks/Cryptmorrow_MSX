"""The title and the end screens of Cryptmorrow MSX (milestone 0.7),
as the model sees them: art.py's screens (the approved graphics of the
ZX game, unchanged), recoloured for the TMS9918A as the rooms are
(game/assets/build_msx.py, version B), cell by cell.

picture(kind, ...) -> 192 rows of 256 colour numbers (0, transparent,
shows the black border: 1):

  title  art.title_screen without its CONTROLS row (the MSX reads the
         keys and the joystick together) and without the sprites (the
         VDP draws them): the logo with its moss, the band of the Moss
         Gate (torches in a phase), the menu with the cursor on the
         mode, PRESS FIRE bright ('hud') or not ('num'), the credit
  end    art.end_screen: VICTORY and the open gate, or GAME OVER and
         the shut gate among the bones of zone A; SCORE, SEALS, ROOMS;
         PRESS FIRE when shown, bright or not
  opening  (milestone 0.8) art.loading_screen, the loading screen of
         the ZX game, as the cartridge shows it at power on

title_sat(turn) -> the 3 x 4 + 1 bytes of the sprite list the program
must have for the next frame: the explorer facing down (two layers),
the skeleton (a new image every 8 passes), the bat (every 4, a pixel
up or down), the end. Standard library only.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / 'game' / 'assets'
sys.path.insert(0, str(ASSETS))
import art  # noqa: E402
import build_msx as B  # noqa: E402

PROMPT_ROW, PROMPT_COLUMN, PROMPT_LEN = 21, 11, 10
CONTROLS_ROW = 19                       # the ZX's, not drawn
TITLE_Y, HERO_TX, SKEL_TX, BAT_TX, BAT_TY = 80, 120, 52, 184, 78
BAT_BOB = [0, 1, 2, 3, 3, 2, 1, 0]
PULSE_BIT = 16
# sprites (game/src/hero.asm, combat.asm)
HERO_SKIN, HERO_CLOTHES, CLOTHES_SHAPES = 9, 10, 32
COMBAT_SHAPE, SKELETON_INK, BAT_INK = 64, 15, 13
IMG_SKELETON, IMG_BAT = 0, 2
_CACHE = {}


def roles(fn, *args, **kw):
    """art.py's screen drawn with roles in place of colours."""
    pal = B.RolePalette()
    zones, base = art.ZONES, art.BASE
    art.ZONES = {z: pal for z in zones}
    art.BASE = pal
    try:
        return fn(*args, **kw)
    finally:
        art.ZONES, art.BASE = zones, base


def recolour(s, zone_of_row, prompt_role=None):
    """The TMS colours of a screen of roles; prompt_role: the role of
    the cells of PRESS FIRE."""
    out = []
    for y in range(192):
        r = y >> 3
        line = []
        for c in range(32):
            role = s.at[r][c]
            if prompt_role and r == PROMPT_ROW and \
                    PROMPT_COLUMN <= c < PROMPT_COLUMN + PROMPT_LEN:
                role = prompt_role
            if not isinstance(role, str):
                role = 'menu'               # never painted: blank
            colour = B.colour_rows(zone_of_row(r), role, 'B')[y & 7]
            ink, paper = colour >> 4 or 1, colour & 15 or 1
            for x in range(c * 8, c * 8 + 8):
                line.append(ink if s.px[y][x] else paper)
        out.append(line)
    return out


def picture(kind, choice=0, phase=0, prompt='hud', won=True, score=0,
            seals=0, rooms=0, shown=True):
    key = (kind, choice, phase, prompt, won, score, seals, rooms, shown)
    if key in _CACHE:
        return _CACHE[key]
    if len(_CACHE) > 64:
        _CACHE.clear()
    if kind == 'opening':
        rows = recolour(roles(art.loading_screen), lambda r: 'atrio')
    elif kind == 'title':
        s = roles(art.title_screen, '128', 'KEMPSTON', choice, phase,
                  sprites=False)
        for y in range(CONTROLS_ROW * 8, CONTROLS_ROW * 8 + 8):
            s.px[y] = [0] * 256
        rows = recolour(s, lambda r: 'atrio', prompt)
    else:
        s = roles(art.end_screen, won, score, seals, rooms, shown, phase)
        band = 'atrio' if won else 'A'
        rows = recolour(s, lambda r: band if 6 <= r < 14 else 'atrio',
                        prompt if shown else None)
    _CACHE[key] = rows
    return rows


def pulse(turn):
    """The role of PRESS FIRE after a pass with this count."""
    return 'num' if turn & PULSE_BIT else 'hud'


def title_sat(turn):
    """The sprite list for the frame after a pass of the title."""
    hero = [TITLE_Y - 1, HERO_TX, 0, HERO_SKIN,
            TITLE_Y - 1, HERO_TX, CLOTHES_SHAPES, HERO_CLOTHES]
    skel = IMG_SKELETON + ((turn >> 3) & 1)
    bat = IMG_BAT + ((turn >> 2) & 1)
    return hero + [TITLE_Y - 1, SKEL_TX, COMBAT_SHAPE + 4 * skel,
                   SKELETON_INK,
                   BAT_TY + BAT_BOB[(turn >> 2) & 7] - 1, BAT_TX,
                   COMBAT_SHAPE + 4 * bat, BAT_INK, 208]

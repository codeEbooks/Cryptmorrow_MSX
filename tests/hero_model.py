"""Python model of the explorer rules in game/src/hero.asm.

The rules of the C64 game, brought to the Spectrum and now to the
MSX: horizontal input wins over vertical, left over right and up
over down; one pixel a frame; a step is refused when a point one
pixel ahead of the hitbox is in a solid cell (three points for up and
down, two for left and right) or outside the room; a new walk image
every 8 frames while moving, the first image when standing. The tests
compare the program with this model after every frame.

Copied from Cryptmorrow ZX (tests/hero_model.py) and adapted to the
MSX in milestone 0.2: the input bits are those of the MSX joystick
(1 up, 2 down, 4 left, 8 right, 16 fire), the keyboard's arrows and
SPACE counting the same; the solid cells come from the room's text
(tests/msx_model.py, solid_cells), not from the builder's data. The
rules are the ZX's, unchanged. Standard library only.
"""

JOY_UP, JOY_DOWN, JOY_LEFT, JOY_RIGHT, JOY_FIRE = 1, 2, 4, 8, 16
DIR_DOWN, DIR_UP, DIR_LEFT, DIR_RIGHT = 0, 1, 2, 3
DIR_NAMES = {0: 'down', 1: 'up', 2: 'left', 3: 'right'}

START_X, START_Y = 120, 104
HERO_SPEED, WALK_RATE = 1, 8
BOX_LEFT, BOX_RIGHT, BOX_MID, BOX_TOP, BOX_BOTTOM = 3, 12, 7, 10, 15
ROOM_TOP_LINE, ROOM_LINES = 16, 160


class HeroModel:
    def __init__(self, solid, x=START_X, y=START_Y):
        self.solid = solid
        self.x, self.y = x, y
        self.dir = DIR_DOWN
        self.moving = 0
        self.frame = 0
        self.timer = 0
        self.block = 0
        self.steps = 0

    def is_solid(self, x, y):
        if x > 255:
            return 1
        line = y - ROOM_TOP_LINE
        if line < 0 or line >= ROOM_LINES:
            return 1
        return self.solid[(line // 8) * 32 + x // 8]

    def blocked(self):
        x, y = self.x, self.y
        if self.dir in (DIR_LEFT, DIR_RIGHT):
            px = x + (BOX_LEFT - 1 if self.dir == DIR_LEFT
                      else BOX_RIGHT + 1)
            return self.is_solid(px, y + BOX_TOP) or \
                self.is_solid(px, y + BOX_BOTTOM)
        py = y + (BOX_TOP - 1 if self.dir == DIR_UP else BOX_BOTTOM + 1)
        return (self.is_solid(x + BOX_LEFT, py) or
                self.is_solid(x + BOX_MID, py) or
                self.is_solid(x + BOX_RIGHT, py))

    def update(self, joy):
        """update_hero, then animate_hero."""
        self.moving = 0
        self.block = 0
        if joy & (JOY_LEFT | JOY_RIGHT):
            self.dir = DIR_LEFT if joy & JOY_LEFT else DIR_RIGHT
        elif joy & (JOY_UP | JOY_DOWN):
            self.dir = DIR_UP if joy & JOY_UP else DIR_DOWN
        else:
            self.animate()
            return
        for _ in range(HERO_SPEED):
            self.block = self.blocked()
            if self.block:
                break
            if self.dir == DIR_LEFT:
                self.x -= 1
            elif self.dir == DIR_RIGHT:
                self.x += 1
            elif self.dir == DIR_UP:
                self.y -= 1
            else:
                self.y += 1
            self.moving = 1
            self.steps += 1
        self.animate()

    def animate(self):
        if self.moving:
            self.timer += 1
            if self.timer == WALK_RATE:
                self.timer = 0
                self.frame ^= 1
        else:
            self.frame = 0
            self.timer = 0

    @property
    def image(self):
        return self.dir * 2 + self.frame

    def state(self):
        return (self.x, self.y, self.dir, self.frame, self.timer,
                self.moving, self.block)

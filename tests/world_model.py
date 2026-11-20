"""Python model of the dungeon and of a game in it: game/src/world.asm,
game/src/objects.asm and, from milestone 0.5, game/src/combat.asm,
with the explorer of hero_model.HeroModel.

Every pass of the main loop:
1. at the top of the frame, what the last pass prepared is shown: the
   sprite list (put_sprites: if the last picture had a fifth sprite on
   a line, the sprites after the explorer start one place further
   on), the HUD's values, the room after a change;
2. until the end of the game: check_fire (a new blow on the edge of
   FIRE when the last one is over; while the blade is out the input is
   ignored: the input byte becomes 0);
3. the explorer moves; if its hitbox has entered the outer ring of
   cells of the room it leaves it (north, south, west, east, in this
   order) and enters the next room of the 4 x 4 grid (room = 4 x row
   + column) from the opposite side, ENTRY_MARGIN pixels inside, at
   the same place along the wall: the room goes black and the
   sprites go at once, the enemies of the new room come back, the
   room is shown at the top of the next pass; out to the north of the
   room of the portal (only through its open door) the game is won:
   the sprites go at once and nothing more happens, then or after;
4. check_door: if a door's cell stopped the explorer (block 2) and
   the door is shut: a locked door opens if the explorer carries its
   key (the key is used up), the portal if it carries the three seals
   (they stay); its open tiles are drawn at once and free its cells
   (but for the two posts of the open portal);
5. check_objects: the object whose metatile holds the middle of the
   hitbox is used: a key is kept, a seal counts and gives 1000
   points, a treasure 250, a potion 2 segments of energy (it stays on
   the floor when the energy is full); a taken object is replaced at
   once by the floor;
6. update_enemies: dust goes after 12 passes, a hit enemy stands
   still 8 passes (and is drawn red: milestone 0.5.1, as in the C64
   game), a skeleton walks its patrol (every other pass,
   every pass if fast) and turns at anything solid or at the ring of
   the openings, a bat within 96 x 90 flies after the explorer
   (across on even passes, up or down on odd ones);
7. check_blade: while the blade is out, the enemies near the point of
   the blow, then near a point half way back, are hit once a blow (a
   skeleton takes 3, 100 points; a bat 1, 50 points; then dust);
8. check_contact: an enemy near the explorer takes 2 segments, then
   30 passes safe (the explorer blinks); at 0, GAME OVER: GAME OVER
   at once in place of the name, the explorer in view, no blade;
9. show_combat: the sprite list of the next frame.

From milestone 0.6 .sounds lists the sounds asked in the pass, in
order (as on the ZX): 'slash' (a new blow), 'door' (a door or the
portal opens), 'pickup' (an object taken), 'dust' (an enemy
defeated), 'hit' (an enemy hurt), 'hurt' (a touch), 'lost' (GAME
OVER), 'won' (VICTORY).

"Near": both distances between the sprites' corners under 8 across
and 9 down. A sprite of the list is (Y, X, shape, colour) as the VDP
gets it: Y a line above the top, shape 0-28 the explorer's skin
(image x 4), 32-60 its clothes, 64-96 the combat (image x 4).

World(room, x, y).update(joy) moves the world one pass and returns
True when the room changed; state() is (room,) + the explorer's
state; game_state() and combat_state() what the program keeps;
drawn() the arguments of msx_model.screen for the frame_ready of the
pass; sat() the sprite list in the VDP then.

Copied from Cryptmorrow ZX (tests/world_model.py of its milestones 0.4
to 0.6) and adapted to the MSX in milestones 0.3-0.6: the rooms, their
objects, doors, enemies and solid cells come from the room's text
(dungeon.py, msx_model.solid_cells), not from the builder's data; the
edges are those of the MSX room (lines 16-175 of the screen); a door
opened and an object taken are drawn in the same pass; the sprites
are the VDP's: a list, four on a line, a colour each. Standard
library only.
"""
import hero_model as H
import msx_model

dungeon = msx_model.dungeon
GRID_W = 4
ENTRY_MARGIN = 8
DOOR_CELL = msx_model.DOOR_CELL
ROOM_TOP = H.ROOM_TOP_LINE                                   # 16
NORTH_EDGE = ROOM_TOP + 7 - H.BOX_TOP                        # 13
SOUTH_EDGE = ROOM_TOP + H.ROOM_LINES - 8 - H.BOX_BOTTOM      # 153
WEST_EDGE = 7 - H.BOX_LEFT                                   # 4
EAST_EDGE = 31 * 8 - H.BOX_RIGHT                             # 236
HIT_X = (H.BOX_LEFT + H.BOX_RIGHT) // 2                      # 7
HIT_Y = (H.BOX_TOP + H.BOX_BOTTOM) // 2                      # 12

ENERGY_MAX, POTION_ENERGY = 8, 2
KIND_SEAL, KIND_TREASURE, KIND_POTION = 4, 5, 6
POINTS = {KIND_SEAL: 1000, KIND_TREASURE: 250}
PORTAL, MAX_SEALS = dungeon.DOOR_NUMBERS[dungeon.PORTAL], 3

# The combat (game/src/combat.asm): the ZX's numbers.
SLASH_FRAMES, BLADE_FRAMES = 20, 8
BLADE_UNTIL = SLASH_FRAMES - BLADE_FRAMES
SAFE_FRAMES, DAMAGE = 30, 2
FLASH_FRAMES, DUST_FRAMES = 8, 12
REACH_X, REACH_Y = 8, 9
CHASE_X, CHASE_Y = 96, 90
RING_LEFT, RING_RIGHT = 8, 248
RING_TOP = ROOM_TOP + 8
RING_BOTTOM = ROOM_TOP + H.ROOM_LINES - 8
BLADE_MAX_X = 239
SKELETON, BAT = dungeon.ENEMIES['skeleton'], dungeon.ENEMIES['bat']
AXIS_FLAG, FAST_FLAG = 1, dungeon.FAST
MAX_ENEMIES = dungeon.MAX_ENEMIES
ENEMY_HP = {SKELETON: 3, BAT: 1}
ENEMY_POINTS = {SKELETON: 100, BAT: 50}
ENDED_LOST, ENDED_WON = 1, 2
IMG_SKELETON, IMG_BAT, IMG_DUST, IMG_BLADE = 0, 2, 4, 5
STRIKE_X = (2, 2, -13, 13, 2, 2, -7, 7)
STRIKE_Y = (12, -15, -1, -1, 6, -8, -1, -1)
BLADE_DX = (5, 5, -11, 11)
BLADE_DY = (8, -6, 0, 0)
# The sprites (hero.asm, combat.asm)
CLOTHES_SHAPES, COMBAT_SHAPE = 32, 64
IMAGE_INK = msx_model.COMBAT_INKS
HIT_INK = msx_model.HIT_INK
# An enemy: a list [kind, x, y, dir, hp, flash, dust, hit, fast].
KIND, X, Y, DIR, HP, FLASH, DUST, HIT, FAST = range(9)


def cut(sat):
    """The places in the list of the sprites the VDP leaves out on at
    least one line (a fifth or later sprite on it)."""
    out = set()
    for line in range(192):
        on = [k for k, e in enumerate(sat)
              if (line - 1 - e[0]) & 0xFF < 16]
        out.update(on[4:])
    return out


def fifth(sat):
    """True if a line of the picture (0-191) has more than four of
    these sprites (the VDP's 5S flag). A sprite covers the 16 lines
    after its Y; the most crowded line is line 0 or the first line of
    a sprite."""
    for line in {0} | {(e[0] + 1) & 0xFF for e in sat}:
        if line < 192 and sum(1 for e in sat
                              if (line - 1 - e[0]) & 0xFF < 16) >= 5:
            return True
    return False


class World:
    def __init__(self, room=None, x=H.START_X, y=H.START_Y):
        self.names = msx_model.rooms()
        self.rooms = {n: dungeon.load_room(name)
                      for n, name in self.names.items()}
        self.energy = ENERGY_MAX
        self.key_set = 0
        self.seals = 0
        self.score = 0
        self.doors = 0                  # bits: doors A-C, portal
        self.taken = set()              # (room, slot)
        self.ended = 0                  # ENDED_LOST, ENDED_WON
        self.end_name = None            # 'won', 'lost': the name row
        self.changes = 0
        self.slash = 0                  # slash_timer
        self.blade_dir = 0
        self.fire_held = 0
        self.safe = 0                   # invulnerable
        self.turn = 0
        self.input = 0                  # the input byte
        self.rot = 0                    # spr_rot
        self.enemies = []
        self.sounds = []                # asked in the pass (0.6)
        if room is None:
            room = dungeon.load_dungeon()[1]
        if isinstance(room, str):
            room = {v: k for k, v in self.names.items()}[room]
        self.hero = H.HeroModel(None, x, y)
        self.enter(room)
        self.show_combat()              # init: show_combat,
        self.shown = self.listed()      # put_sprites
        self.picture = self.shown       # what the VDP shows
        self.picture_tags = self.listed(True)
        self.black = False              # the room black now
        self.hud_shown = self.hud()

    def clone(self):
        """A copy to try moves on (the solid map is shared: it is
        replaced, never changed in place)."""
        w = World.__new__(World)
        w.__dict__.update(self.__dict__)
        w.taken = set(self.taken)
        w.enemies = [list(e) for e in self.enemies]
        w.sounds = list(self.sounds)
        h = H.HeroModel.__new__(H.HeroModel)
        h.__dict__.update(self.hero.__dict__)
        w.hero = h
        return w

    # -- the room on the screen ---------------------------------------------

    @property
    def name(self):
        return self.names[self.room]

    def door(self, room=None):
        """The door of a room: 0, 1-3 the locked doors A-C, 4 the
        portal."""
        d = self.rooms[self.room if room is None else room].door
        return dungeon.DOOR_NUMBERS[d] if d else 0

    def door_bit(self, room=None):
        d = self.door(room)
        return (1 << (d - 1)) if d else 0

    def door_open(self):
        return bool(self.doors & self.door_bit())

    def enter(self, room):
        """enter_room: the solid map of the room with its door as it
        is; the enemies back at their places."""
        self.room = room
        self.hero.solid = msx_model.solid_cells(self.name,
                                                self.door_open())
        self.enemies = []
        slots = list(self.rooms[room].enemies)
        for k in range(MAX_ENEMIES):
            if k < len(slots):
                kind, c, r, axis, fast = slots[k]
                kind = dungeon.ENEMIES[kind]
                flags = (dungeon.AXES[axis] if axis else 0) | \
                    (FAST_FLAG if fast else 0)
            else:
                kind, c, r, flags = 0, 0, 0, 0
            self.enemies.append([
                kind, 16 * c, 16 * r + ROOM_TOP,
                H.DIR_DOWN if flags & AXIS_FLAG else H.DIR_RIGHT,
                ENEMY_HP.get(kind, 0), 0, 0, 0, flags & FAST_FLAG])

    def solid(self, room=None):
        """The solid map the room would have now."""
        room = self.room if room is None else room
        return msx_model.solid_cells(
            self.names[room], bool(self.doors & self.door_bit(room)))

    # -- a pass ---------------------------------------------------------------

    def update(self, joy):
        self.sounds = []
        self.put_sprites()
        self.hud_shown = self.hud()
        self.black = False
        self.turn = (self.turn + 1) & 0xFF
        if self.ended:
            return False
        joy = self.check_fire(joy)
        self.input = joy
        h = self.hero
        h.update(joy)
        step = None
        if h.y <= NORTH_EDGE:
            if self.door() == PORTAL:
                self.victory()          # out through the portal
                return False
            h.y, step = SOUTH_EDGE - ENTRY_MARGIN, -GRID_W
        elif h.y >= SOUTH_EDGE:
            h.y, step = NORTH_EDGE + ENTRY_MARGIN, GRID_W
        elif h.x <= WEST_EDGE:
            h.x, step = EAST_EDGE - ENTRY_MARGIN, -1
        elif h.x >= EAST_EDGE:
            h.x, step = WEST_EDGE + ENTRY_MARGIN, 1
        if step is not None:
            room = (self.room + step) & 0xFF
            if room not in self.names:
                raise ValueError(f'room {room}: off the grid')
            self.picture = []           # hide_room: no sprites
            self.picture_tags = []
            self.black = True
            self.enter(room)
            self.changes += 1
        self.check_door()
        self.check_objects()
        self.update_enemies()
        self.check_blade()
        self.check_contact()
        self.show_combat()
        return step is not None

    def put_sprites(self):
        """The list prepared by the last pass to the VDP: the
        explorer, then the others from spr_rot; spr_rot one further
        on if the last picture had a fifth sprite on a line."""
        if fifth(self.picture):
            self.rot += 1
        if self.rot >= len(self.others):
            self.rot = 0
        self.shown = self.listed()
        self.picture = self.shown
        self.picture_tags = self.listed(True)

    def listed(self, tags=False):
        o = self.others_tags if tags else self.others
        hero = ['skin', 'clothes'] if tags else self.hero_sat
        return (hero if self.hero_shown else []) + \
            o[self.rot:] + o[:self.rot]

    def victory(self):
        self.ended = ENDED_WON
        self.sounds.append('won')
        self.end_name = 'won'
        self.slash = 0
        self.hero_shown = False
        self.others = []
        self.others_tags = []
        self.picture = []               # 208 at sprite 0, now
        self.picture_tags = []

    def check_door(self):
        if self.hero.block != DOOR_CELL or not self.door():
            return
        bit = self.door_bit()
        if self.doors & bit:
            return                      # open already
        if self.door() == PORTAL:
            if self.seals != MAX_SEALS:
                return
        else:
            if not self.key_set & bit:
                return
            self.key_set ^= bit         # the key is used up
        self.doors |= bit
        self.sounds.append('door')
        self.hero.solid = self.solid()  # drawn open at once

    def check_objects(self):
        h = self.hero
        col = ((h.x + HIT_X) & 0xFF) >> 4
        row = ((h.y + HIT_Y - ROOM_TOP) & 0xFF) >> 4
        room = self.rooms[self.room]
        for slot, (kind, letter, c, r) in enumerate(room.objects):
            if (self.room, slot) in self.taken or (c, r) != (col, row):
                continue
            if self.use(room.code(kind, letter)):
                self.taken.add((self.room, slot))
                self.sounds.append('pickup')

    def use(self, kind):
        if kind < KIND_SEAL:
            self.key_set |= 1 << (kind - 1)
            return True
        if kind == KIND_SEAL:
            self.seals += 1
        if kind in POINTS:
            self.score += POINTS[kind]
            return True
        if self.energy >= ENERGY_MAX:
            return False                # the potion stays
        self.energy = min(ENERGY_MAX, self.energy + POTION_ENERGY)
        return True

    # -- the combat ----------------------------------------------------------

    def blade_out(self):
        return self.slash > BLADE_UNTIL

    def check_fire(self, joy):
        if self.slash:
            self.slash -= 1
        fire = joy & H.JOY_FIRE
        if fire != self.fire_held:
            self.fire_held = fire
            if fire and not self.slash:
                self.slash = SLASH_FRAMES
                self.blade_dir = self.hero.dir
                for e in self.enemies:
                    e[HIT] = 0
                self.sounds.append('slash')
        return 0 if self.blade_out() else joy

    def measure(self, px, py, e):
        """far_x, far_y, west, north from enemy e to the point (px is
        a 16-bit value: a blade's point may lie off the screen; py is
        8 bits)."""
        dx = px - e[X]
        west = 0
        if 0 <= dx <= 255:
            far_x = dx
        elif -256 <= dx < 0:
            west = 1
            far_x = -dx if dx != -256 else 255
        else:
            far_x = 255
        py &= 0xFF
        if py >= e[Y]:
            return far_x, py - e[Y], west, 0
        return far_x, e[Y] - py, west, 1

    def near(self, px, py, e):
        fx, fy, _, _ = self.measure(px, py, e)
        return fx < REACH_X and fy < REACH_Y

    def enemy_cell(self, x, y):
        if not (RING_TOP <= y < RING_BOTTOM and
                RING_LEFT <= x < RING_RIGHT):
            return 1
        return self.hero.solid[((y - ROOM_TOP) // 8) * 32 + x // 8]

    def enemy_blocked(self, e):
        x, y, d = e[X], e[Y], e[DIR]
        if d in (H.DIR_DOWN, H.DIR_UP):
            py = y + (H.BOX_BOTTOM + 1 if d == H.DIR_DOWN
                      else H.BOX_TOP - 1)
            return (self.enemy_cell(x + H.BOX_LEFT, py) or
                    self.enemy_cell(x + H.BOX_RIGHT, py))
        px = x + (H.BOX_LEFT - 1 if d == H.DIR_LEFT else H.BOX_RIGHT + 1)
        return (self.enemy_cell(px, y + H.BOX_TOP) or
                self.enemy_cell(px, y + H.BOX_BOTTOM))

    @staticmethod
    def move(e, d):
        if d == H.DIR_DOWN:
            e[Y] += 1
        elif d == H.DIR_UP:
            e[Y] -= 1
        elif d == H.DIR_LEFT:
            e[X] -= 1
        else:
            e[X] += 1

    def update_enemies(self):
        for e in self.enemies:
            if not e[KIND]:
                continue
            if e[DUST]:
                e[DUST] -= 1
                if not e[DUST]:
                    e[KIND] = 0
                continue
            if e[FLASH]:
                e[FLASH] -= 1
                continue
            if e[KIND] == SKELETON:
                if not e[FAST] and self.turn & 1:
                    continue
                if self.enemy_blocked(e):
                    e[DIR] ^= 1
                else:
                    self.move(e, e[DIR])
            else:
                fx, fy, west, north = self.measure(self.hero.x,
                                                   self.hero.y, e)
                if fx >= CHASE_X or fy >= CHASE_Y:
                    continue
                if not self.turn & 1:
                    if fx:
                        self.move(e, H.DIR_LEFT if west else H.DIR_RIGHT)
                elif fy:
                    self.move(e, H.DIR_UP if north else H.DIR_DOWN)

    def check_blade(self):
        if not self.blade_out():
            return
        for k in (self.blade_dir, self.blade_dir + 4):
            px = self.hero.x + STRIKE_X[k]
            py = self.hero.y + STRIKE_Y[k]
            for e in self.enemies:
                if not e[KIND] or e[DUST] or e[HIT]:
                    continue
                if not self.near(px, py, e):
                    continue
                e[HIT] = 1
                e[HP] -= 1
                if not e[HP]:
                    e[DUST] = DUST_FRAMES
                    self.score += ENEMY_POINTS[e[KIND]]
                    self.sounds.append('dust')
                else:
                    e[FLASH] = FLASH_FRAMES
                    self.sounds.append('hit')

    def check_contact(self):
        if self.safe:
            self.safe -= 1
            return
        for e in self.enemies:
            if not e[KIND] or e[DUST]:
                continue
            if self.near(self.hero.x, self.hero.y, e):
                self.energy = max(0, self.energy - DAMAGE)
                self.safe = SAFE_FRAMES
                self.sounds.append('hurt')
                if not self.energy:
                    self.game_over()
                return

    def game_over(self):
        self.ended = ENDED_LOST
        self.sounds.append('lost')
        self.end_name = 'lost'
        self.safe = 0
        self.slash = 0

    def show_combat(self):
        """The sprite list of the next frame: the explorer's two
        sprites (hero_sat; listed unless it blinks), then the blade,
        then the enemies (an enemy just hit in red, from milestone
        0.5.1; in 0.5 it blinked, as on the ZX)."""
        h = self.hero
        self.hero_shown = not self.safe & 4
        y = (h.y - 1) & 0xFF
        self.hero_sat = [(y, h.x, h.image * 4, msx_model.HERO_SKIN),
                         (y, h.x, CLOTHES_SHAPES + h.image * 4,
                          msx_model.HERO_CLOTHES)]
        out, tags = [], []

        def entry(img, x, y, tag, ink=None):
            out.append(((y - 1) & 0xFF, x, COMBAT_SHAPE + 4 * img,
                        IMAGE_INK[img] if ink is None else ink))
            tags.append(tag)
        if self.blade_out():
            d = self.blade_dir
            x = h.x + BLADE_DX[d]
            x = 0 if x < 0 else min(x, BLADE_MAX_X)
            entry(IMG_BLADE + d, x, (h.y + BLADE_DY[d]) & 0xFF, 'blade')
        for n, e in enumerate(self.enemies):
            if not e[KIND]:
                continue
            if e[DUST]:
                img = IMG_DUST
            else:
                shift = 3 if e[KIND] == SKELETON else 2
                img = ((self.turn >> shift) & 1) + (
                    IMG_SKELETON if e[KIND] == SKELETON else IMG_BAT)
            entry(img, e[X], e[Y], f'enemy {n}',
                  HIT_INK if e[FLASH] else None)
        self.others = out
        self.others_tags = tags

    # -- what the program shows and keeps ---------------------------------

    @property
    def keys(self):
        return bin(self.key_set).count('1')

    def hud(self):
        return {'energy': self.energy, 'keys': self.keys,
                'seals': self.seals, 'score': self.score}

    def objects_there(self):
        return tuple(s for s in range(len(self.rooms[self.room].objects))
                     if (self.room, s) not in self.taken)

    def drawn(self):
        """The arguments of msx_model.screen for the frame_ready of
        this pass (but the name and the flame's phase): the HUD as it
        was at the top of the pass, the rest as it is."""
        return dict(self.hud_shown, door_open=self.door_open(),
                    objects=self.objects_there(),
                    won=self.end_name == 'won',
                    lost=self.end_name == 'lost')

    def sat(self):
        """The sprite list in the VDP at the frame_ready of this
        pass."""
        return list(self.picture)

    def game_state(self):
        taken = tuple(int((r, s) in self.taken) for r in range(16)
                      for s in range(2))
        return (self.key_set, self.seals, self.score, self.energy,
                self.doors, self.ended) + taken

    def combat_state(self):
        """turn, slash_timer, blade_dir, fire_held, invulnerable,
        hero_shown, spr_rot, spr_count, the enemies, spr_list."""
        return (self.turn, self.slash, self.blade_dir, self.fire_held,
                self.safe, int(self.hero_shown), self.rot,
                len(self.others)) + tuple(
                    v & 0xFF for e in self.enemies for v in e) + tuple(
                    v for s in self.others for v in s)

    def state(self):
        return (self.room,) + self.hero.state()

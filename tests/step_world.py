"""The model of the steps 01-06 of the book's chain (Phase D, D.2):
the model of the complete game (world_model.World, with
hero_model.HeroModel and msx_model's screen) without what a step does
not have yet.

Before step 07 there is no title and no end screen: the cartridge
starts a game in the Moss Gate at once and, when the game ends, the
room stands still (play_frame returns at once; the torches burn on).
What each step has (chain/NN/README.md):

01  the Moss Gate drawn, its name between the two lines, the torches
    (a new flame phase every 8 frames); row 0 of the HUD blank, no
    explorer, no sprite, no input read;
02  the explorer: the controls, the walk, the collisions; no exits:
    the explorer walks into an opening up to the edge of the room
    (outside it is solid, hero.asm is_solid);
03  the exits to the other rooms, the room black while the next one
    is built; the HUD's row 0, which never changes in this step; the
    doors stay shut, no objects;
04  the objects, the doors, the portal, VICTORY; the HUD drawn again
    when a value changes; FIRE does nothing;
05  the blade, the enemies, the damage, GAME OVER, the order of the
    sprites turning; no sound;
06  the sound: the complete game's model as it is (world_model.World),
    its .sounds asked in the pass.

StepWorld(step, room).update(joy) moves the world one pass of the
step's main loop, as world_model.World does for the complete game;
.drawn(), .sat(), .state(), .game_state(), .combat_state() as there.
Before step 05 the enemies' slots are empty; before step 06 .sounds
stays empty. Standard library only.
"""
import world_model as W

STEPS = range(1, 7)
EMPTY = [0] * 9                         # an enemy slot without enemy


class StepWorld(W.World):
    def __init__(self, step, room=None, x=W.H.START_X, y=W.H.START_Y):
        assert step in STEPS
        self.step = step
        super().__init__(room, x, y)

    def clone(self):
        w = super().clone()
        w.__class__ = StepWorld
        return w

    def enter(self, room):
        super().enter(room)
        if self.step < 5:               # no enemies yet
            self.enemies = [list(EMPTY) for _ in self.enemies]

    def show_combat(self):
        super().show_combat()
        if self.step == 1:              # no explorer
            self.hero_shown = False

    def update(self, joy):
        if self.step >= 5:
            changed = super().update(joy)
            if self.step == 5:
                self.sounds = []        # no sound in step 05
            return changed
        self.sounds = []
        self.put_sprites()
        self.hud_shown = self.hud()
        self.black = False
        if self.step == 1 or self.ended:
            return False                # 01: no input, no explorer
        self.input = joy                # 02-04: no blade, FIRE kept
        h = self.hero
        h.update(joy)
        step = None
        if self.step >= 3:              # check_exits
            if h.y <= W.NORTH_EDGE:
                if self.step >= 4 and self.door() == W.PORTAL:
                    self.victory()      # out through the portal
                    self.sounds = []
                    return False
                h.y, step = W.SOUTH_EDGE - W.ENTRY_MARGIN, -W.GRID_W
            elif h.y >= W.SOUTH_EDGE:
                h.y, step = W.NORTH_EDGE + W.ENTRY_MARGIN, W.GRID_W
            elif h.x <= W.WEST_EDGE:
                h.x, step = W.EAST_EDGE - W.ENTRY_MARGIN, -1
            elif h.x >= W.EAST_EDGE:
                h.x, step = W.WEST_EDGE + W.ENTRY_MARGIN, 1
        if step is not None:
            room = (self.room + step) & 0xFF
            if room not in self.names:
                raise ValueError(f'room {room}: off the grid')
            self.picture = []           # hide_room: no sprites
            self.picture_tags = []
            self.black = True
            self.enter(room)
            self.changes += 1
        if self.step >= 4:
            self.check_door()
            self.check_objects()
        self.show_combat()
        self.sounds = []
        return step is not None

    def drawn(self):
        d = super().drawn()
        if self.step < 4:               # no objects drawn
            d['objects'] = ()
        return d

    def hud_blank(self):
        """Row 0 of the HUD blank (steps 01-02: the cells HUD_BLANK,
        black)."""
        return self.step < 3

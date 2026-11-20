"""The guided variants and the "Where it breaks" versions of the chain
of the book (Phase D, D.3; the list approved by the author on 13
November 2026: "Approvo tutto").

Read by tools/make_variants.py, which builds each one in
variants/NN-name/ID/ from chain/NN-name/, proves it and writes its
README.md.

A variant is one idea changed in one place of a step: the same change
is made in the Python models (`model`: statements run before the test
plans its routes; VS is tests/verify_step.py, W world_model, MM
msx_model, H hero_model, V verify_0_8), so the step's own test
(tests/verify_step.py; for step 07 the test of 1.0 on the folder)
compares the changed program with the changed models pass by pass,
on the step's routes (or the variant's own, `route`), and must PASS;
`expect` are the facts of its report that show the change (`r` is the
report). A variant of the data (a room, a colour, the music, a word)
needs no statement: the test reads the data of the variant's folder.

A break is a classic mistake made on purpose: the step's own test,
with the models unchanged, must FAIL, and the first failed check must
match `fails` (a regular expression); `shot` is the picture of the
test that shows it (a PNG of the report's png/ folder), or None.

Edits: (file in the step folder, old text, new text); the old text
must be there exactly once. Everything the reader reads (the README)
is in English.

From Cryptmorrow ZX (tools/variants.py), with the MSX's list: the
ZX's ideas where they make sense, the beeper's and the Kempston's
replaced by the PSG's and the joystick's, the six breaks of the MSX
of the starting sheet (section 9.2) and two more. Standard library.
"""

VARIANTS = [
    # --- step 01: the first room ----------------------------------------
    dict(id='01a-faster-flames', step=1, kind='variant',
         title='Faster flames',
         summary='The torches flicker twice as fast: a new flame every '
                 '4 frames instead of every 8.',
         edits=[('game/src/torches.asm',
                 '        ld a,(frames)\n'
                 '        and %00011000           ; the phase due, x 8\n',
                 '        ld a,(frames)\n'
                 '        add a,a                 ; frames x 2: every 4\n'
                 '        and %00011000           ; the phase due, x 8\n')],
         model=['VS.FLAME_SHIFT = 2'],
         where='`game/src/torches.asm`, the first lines of '
               '`animate_torches`: the low byte of `frames` and the mask '
               '`%00011000`, which keeps bits 3 and 4 - the phase '
               '(frames / 8) mod 4, already multiplied by 8, the bytes '
               'of a flame.',
         see='Every torch changes its flame every 4 frames, 12.5 times '
             'a second at 50 Hz (15 at 60 Hz); the four flames come in '
             'the same order.',
         limits='One `add a,a` halves the period (4 frames), two give 2, '
                'one `rrca` instead doubles it (16): the mask must stay '
                '`%00011000`, the place of the phase times 8. The four '
                'flames stay four (`flame_phases`).',
         depends='Nothing else: `animate_torches` draws the phase it '
                 'finds, and only when it changes (`flame_phase`). The '
                 'test\'s model has the same period (`FLAME_SHIFT`: the '
                 'phase is frames >> 2).',
         expect=[('the flame changed about twice as often (about 100 '
                  'times in 402 passes; 50 in the step)',
                  "r['shows']['eu the first room']['flame_changes'] >= 95"
                  " and r['shows']['int the first room']"
                  "['flame_changes'] >= 95")]),
    dict(id='01b-another-zone', step=1, kind='variant',
         title='The colours of another zone',
         summary='The Moss Gate in the colours of zone C, the amber '
                 'wing. One line of data.',
         edits=[('game/assets/rooms/moss_gate.txt',
                 'name: THE MOSS GATE\ndoor: portal\n',
                 'name: THE MOSS GATE\nzone: C\ndoor: portal\n')],
         model=[],
         where='`game/assets/rooms/moss_gate.txt`, the header of the '
               'room: a line `zone:` (without it a room is in the '
               'atrium, `atrio` in the data). The asset builder '
               '(`build_msx.py`) writes the zone into the room\'s '
               'record; `enter_room` reads it and `load_zone` copies '
               'that zone\'s patterns and colours into the three '
               'thirds of the VRAM.',
         see='The same room in the amber of zone C: the walls, the '
             'floor and the pillars in its colours, the moss gone from '
             'the walls (zone C grows none).',
         limits='`atrio`, `A`, `B` or `C` (`ZONES` in `dungeon.py`). '
                'A room keeps its map; only the colours of its roles and '
                'the moss of the zone change.',
         depends='The asset builder runs again (`tools/build_game.py '
                 '--assets` does it): the room table, nothing else. In '
                 'the later steps the start room would look like the '
                 'treasury.',
         expect=[('the start room in zone 3 (C), = the model of the new '
                  'data', "r['shows']['eu the first room']['zone_start'] "
                  "== 3 and r['result'] == 'PASS'")]),
    # --- step 02: the explorer -------------------------------------------
    dict(id='02a-red-coat', step=2, kind='variant',
         title='A red coat',
         summary='The explorer\'s hat and coat in dark red instead of '
                 'dark yellow: one sprite, one colour.',
         edits=[('game/src/hero.asm',
                 'HERO_CLOTHES    equ 10          ; dark yellow: hat, coat',
                 'HERO_CLOTHES    equ 6           ; dark red: hat, coat')],
         model=['MM.HERO_CLOTHES = 6'],
         where='`game/src/hero.asm`, the constant `HERO_CLOTHES`: the '
               'colour byte of sprite 1, the clothes, in `hero_sat` '
               '(`hero_sprites`).',
         see='The same explorer with a dark red hat and coat; the face '
             'and the hands (sprite 0, `HERO_SKIN`) stay light red.',
         limits='Any of the 15 colours (1-15; 0 is transparent: the '
                'clothes would vanish). A sprite has one colour: a '
                'third colour would need a third sprite on the same '
                'lines, one of the four a line allows.',
         depends='Nothing: the shapes do not change, only the colour '
                 'byte of the list.',
         expect=[('sprite 1 (the clothes) in colour 6, sprite 0 (the '
                  'skin) in 9', "r['shows']['eu Moss Gate']['clothes'] == "
                  "6 and r['shows']['eu Moss Gate']['skin'] == 9")]),
    dict(id='02b-joystick-port-2', step=2, kind='variant',
         title='The joystick in port 2',
         summary='The explorer follows the joystick in port 2 instead '
                 'of port 1: one bit of PSG register 15.',
         edits=[('game/src/input.asm',
                 'JOY_PORT1       equ %10001111   ; R15: port 1, pin 8 low',
                 'JOY_PORT1       equ %11001111   ; R15: port 2, pin 8 low')],
         model=['VS.JOY_PORT = 2'],
         where='`game/src/input.asm`, the value written to PSG register '
               '15 before register 14 is read: bit 6 picks the port '
               '(0: port 1, 1: port 2); bits 4 and 5 are pin 8 of the '
               'two ports, kept low.',
         see='The arrows and SPACE still work; the stick and button A '
             'now come from port 2 (in openMSX: plug a joystick into '
             '`joyportb`); the stick in port 1 does nothing.',
         limits='Bit 6 picks one port at a time: to read both, read '
                'register 14 twice, with bit 6 at 0 and then at 1. The '
                'name `JOY_PORT1` stays: the README says why.',
         depends='Nothing else reads the joystick. The test plugs its '
                 'joystick into port 2 (`JOY_PORT`, in the bench and in '
                 'openMSX).',
         expect=[('the explorer moved with the joystick of port 2 alone '
                  '(passes with the stick only)',
                  "r['shows']['eu Moss Gate']['joy_moves'] > 100 and "
                  "r['shows']['int Moss Gate']['joy_moves'] > 100")]),
    # --- step 03: the dungeon --------------------------------------------
    dict(id='03a-autumn-moss', step=3, kind='variant',
         title='Autumn moss',
         summary='The moss of the atrium in yellow and red instead of '
                 'three greens.',
         edits=[('game/assets/build_msx.py',
                 "    'moss': ('ink', 12, [3, 3, 2, 2, 2, 12, 12, 12]),\n"
                 "    'mossface': ('ink', 12, [3, 3, 2, 2, 2, 12, 12, 12]),"
                 "\n"
                 "    'fmoss': ('ink', 12, [3, 3, 2, 2, 2, 12, 12, 12]),\n",
                 "    'moss': ('ink', 12, [11, 11, 10, 10, 10, 6, 6, 6]),\n"
                 "    'mossface': ('ink', 12, [11, 11, 10, 10, 10, 6, 6, "
                 "6]),\n"
                 "    'fmoss': ('ink', 12, [11, 11, 10, 10, 10, 6, 6, 6]),"
                 "\n")],
         model=["MM.ROWS_B['moss'] = ('ink', 12, (11, 11, 10, 10, 10, 6,"
                " 6, 6))",
                "MM.ROWS_B['mossface'] = ('ink', 12, (11, 11, 10, 10, 10,"
                " 6, 6, 6))",
                "MM.ROWS_B['fmoss'] = ('ink', 12, (11, 11, 10, 10, 10, 6,"
                " 6, 6))"],
         where='`game/assets/build_msx.py`, the table `ROWS_B`: the '
               'colour of each of the 8 pixel rows of a cell, for the '
               'roles whose colour has a row of its own in the graphics '
               'B (the approved ones). The moss: light green at the '
               'tip, medium, dark at the root.',
         see='The moss on the walls and the tufts on the floor of the '
             'atrium in light yellow, dark yellow and dark red.',
         limits='Eight colours, one a row, 1-15 each; the paper of the '
                'cell stays the stone\'s. Only the atrium grows moss '
                'with these rows.',
         depends='The asset builder runs again (the colours of the zone '
                 'atrio). The title\'s moss under the logo uses the same '
                 'rows: from step 07 it would turn autumn too.',
         expect=[('no green pixel in the room at the start (1 818 in the '
                  'step: the moss)',
                  "r['shows']['eu room 01']['green_room'] == 0")]),
    dict(id='03b-green-bar', step=3, kind='variant',
         title='A green energy bar',
         summary='The energy bar of the HUD in green instead of red.',
         edits=[('game/assets/art.py',
                 "'bar': attr(R, K, 1),",
                 "'bar': attr(G, K, 1),")],
         model=[],
         where='`game/assets/art.py` (the ZX game\'s drawings, which the '
               'MSX asset builder recolours): the role `bar`, bright red '
               'ink on black.',
         see='The segments of the bar in the HUD\'s row 0 in medium '
             'green (2) instead of medium red (8).',
         limits='The 8 colours of the ZX (with BRIGHT): `build_msx.py` '
                'turns each into a TMS9918A colour. The bar keeps its '
                'cells: four, two segments a cell.',
         depends='The asset builder runs again (the HUD\'s slots in the '
                 'three thirds). The test reads `art.py` of the folder.',
         expect=[('the ink of the bar\'s cells: medium green (2; medium '
                  'red, 8, in the step)',
                  "r['shows']['eu room 01']['bar_ink'] == 2")]),
    # --- step 04: objects and doors ---------------------------------------
    dict(id='04a-strong-potion', step=4, kind='variant',
         title='A stronger potion',
         summary='A potion gives back 4 segments of energy instead of 2.',
         edits=[('game/src/objects.asm',
                 'POTION_ENERGY   equ 2',
                 'POTION_ENERGY   equ 4')],
         model=['W.POTION_ENERGY = 4'],
         route='potion',
         where='`game/src/objects.asm`, the constant `POTION_ENERGY`, '
               'added to the energy (up to `ENERGY_MAX`) when a potion '
               'is taken.',
         see='From 3 segments a potion brings the bar to 7, not 5. With '
             'the bar full a potion still stays on the floor.',
         limits='1-8: the energy stops at `ENERGY_MAX` (8) anyway.',
         depends='Nothing else. In step 04 nothing takes energy away: '
                 'the test puts 3 in memory, as the book does.',
         expect=[('the energy 8, put at 3, then 7 after the potion',
                  "r['shows']['eu the potion']['energies'] == [8, 3, 7]")]),
    dict(id='04b-rich-treasure', step=4, kind='variant',
         title='Richer treasures',
         summary='A treasure is worth 500 points instead of 250.',
         edits=[('game/src/objects.asm',
                 '        ld de,#0250             ; 250 points (BCD)',
                 '        ld de,#0500             ; 500 points (BCD)')],
         model=['W.POINTS[W.KIND_TREASURE] = 500'],
         where='`game/src/objects.asm`, the points of a treasure: two '
               'BCD digits a byte, added to `score` with `DAA`.',
         see='VICTORY at 7 000 points instead of 5 000: the same eight '
             'treasures.',
         limits='BCD digits only (`#0999` at most here: the score has 6 '
                'digits and `add_score` adds four of them); `#0A00` is '
                'not a number for `DAA`.',
         depends='Nothing else; the HUD shows what `score` holds.',
         expect=[('VICTORY at 7 000 points (5 000 in the step)',
                  "r['shows']['eu the walking game']['game'][2] == 7000")]),
    # --- step 05: combat ----------------------------------------------------
    dict(id='05a-light-damage', step=5, kind='variant',
         title='Lighter damage',
         summary='A touch takes 1 segment of energy instead of 2.',
         edits=[('game/src/combat.asm',
                 'DAMAGE          equ 2           ; energy lost at a touch',
                 'DAMAGE          equ 1           ; energy lost at a touch')],
         model=['W.DAMAGE = 1'],
         where='`game/src/combat.asm`, the constant `DAMAGE`, taken from '
               '`energy` by `check_contact`.',
         see='Eight touches before GAME OVER instead of four; the bar '
             'goes down one segment at a time.',
         limits='1-8 (8: GAME OVER at the first touch). An odd damage '
                'makes the energy odd: `check_contact` stops at 0, not '
                'below.',
         depends='Nothing else; after each touch the explorer is safe '
                 'for 30 passes (`SAFE_FRAMES`), as before.',
         expect=[('GAME OVER without help after eight touches (seven, '
                  'then the last)',
                  "r['shows']['eu defeat']['events'].get('touch') == 7 "
                  "and r['shows']['eu defeat']['game'][5] == 1")]),
    dict(id='05b-lazy-bats', step=5, kind='variant',
         title='Lazy bats',
         summary='A bat wakes only within 48 x 45 pixels of the explorer '
                 'instead of 96 x 90.',
         edits=[('game/src/combat.asm',
                 'CHASE_X         equ 96          ; a bat chases the '
                 'explorer\n'
                 'CHASE_Y         equ 90          ; inside this distance',
                 'CHASE_X         equ 48          ; a bat chases the '
                 'explorer\n'
                 'CHASE_Y         equ 45          ; inside this distance')],
         model=['W.CHASE_X, W.CHASE_Y = 48, 45'],
         route='bats',
         where='`game/src/combat.asm`, the constants `CHASE_X` and '
               '`CHASE_Y`: the distances across and down within which '
               '`update_enemies` moves a bat towards the explorer.',
         see='In the Root Cellar the bat stays asleep with the explorer '
             '80 pixels away (it used to wake at 96) and wakes at less '
             'than 48.',
         limits='Under 256 across (`far_x` is a byte) and 192 down. At 8 '
                'or less a bat touches before it wakes.',
         depends='The planned whole game waits for the bats to come: '
                 'with lazy bats it no longer works (the Bone Shrine '
                 'stays guarded). The test plays a route of its own: the '
                 'planned game to the Root Cellar, then still, then '
                 'closer.',
         expect=[('the bat still for 150 passes with the explorer inside '
                  '96 x 90, awake at less than 48 across',
                  "r['shows']['eu the bat']['bats'][-1]['still_in_96x90']"
                  " >= 150 and r['shows']['eu the bat']['bats'][-1]"
                  "['woke_at']['far'][0] < 48")]),
    # --- step 06: sound -----------------------------------------------------
    dict(id='06a-effects-first', step=6, kind='variant',
         title='Effects only',
         summary='The game starts in SOUND FX: the effects on the PSG, '
                 'no music.',
         edits=[('game/src/start.asm',
                 '        ld a,SOUND_MODE         ; MUSIC, SOUND FX or '
                 'SILENT',
                 '        ld a,1                  ; SOUND FX (2: SILENT)')],
         model=['VS.SOUND_MODE = 1'],
         where='`game/src/start.asm`, the mode given to `set_audio` at '
               'INIT: 0 MUSIC, 1 SOUND FX, 2 SILENT (in step 06 it comes '
               'from the assembler, `SOUND_MODE`; from step 07 from the '
               'menu of the title).',
         see='No theme: only the effects, the blow, the hits, the doors, '
             'the objects, the touches, and the effect of the end.',
         limits='0, 1 or 2. With 2 (SILENT) the PSG is silent all the '
                'game: the interrupt still sends its registers, all at '
                'volume 0.',
         depends='Nothing else: `set_audio` sets the mode for '
                 '`sound_effect` and `end_sound`.',
         expect=[('no group of the music sent to the PSG, the effects '
                  'yes', "r['shows']['eu the whole game']['sound_kinds']"
                  "['music'] == 0 and r['shows']['eu the whole game']"
                  "['sound_kinds']['effects'] > 0")]),
    dict(id='06b-faster-music', step=6, kind='variant',
         title='Faster music',
         summary='The theme at 150 beats a minute instead of 125: 5 '
                 'frames a step instead of 6.',
         edits=[('game/assets/c64/score.py',
                 'SPEED = 6            # frames per step: 50 / 6 * 60 / 4 '
                 '= 125 BPM (PAL)',
                 'SPEED = 5            # frames per step: 50 / 5 * 60 / 4 '
                 '= 150 BPM (PAL)'),
                ('game/assets/psg_music.py',
                 "    if GATE_BEFORE != 2 or SPEED_60 != 7:\n"
                 "        raise ValueError('the speeds approved: 6 and 7, "
                 "gate 2')",
                 "    if GATE_BEFORE != 1 or SPEED_60 != 6:\n"
                 "        raise ValueError('the speeds of this variant: 5 "
                 "and 6, gate 1')")],
         model=[],
         where='`game/assets/c64/score.py`, `SPEED`: the frames of a '
               'step (a sixteenth note) at 50 Hz; `psg_music.py` makes '
               'the 60 Hz speed from it (`round(SPEED x 60 / 50)`) and '
               'checks the speeds it was approved with: a variant '
               'changes that check too.',
         see='The same theme and the same pieces of the end, faster: 150 '
             'beats a minute at 50 Hz, 6 frames a step at 60 Hz.',
         limits='The release of a note comes `GATE_TICK` (4) frames '
                'into its step: under 5 frames a step the note would '
                'have no time before its release.',
         depends='The music data again (`music.asm`: `SPEED_50`, '
                 '`SPEED_60`, `GATE_BEFORE`); the test reads the '
                 '`music.json` of the folder.',
         expect=[('the PSG = the model at 5 frames a step (6 at 60 Hz)',
                  "r['shows']['music_speed'] == [5, 6] and "
                  "r['result'] == 'PASS'")]),
    # --- step 07: the title and the ends -------------------------------------
    dict(id='07a-ice-crypt', step=7, kind='variant',
         title='Another name in the logo',
         summary='The title says ICE CRYPT in the big letters of the logo '
                 'instead of CRYPTMORROW.',
         edits=[('game/assets/build_msx.py',
                 "WORDS = {'logo': ('CRYPTMORROW', 1, 'logo', 'logo2', "
                 "True),",
                 "WORDS = {'logo': ('ICE CRYPT', 1, 'logo', 'logo2', "
                 "True),"),
                ('game/assets/build_msx.py',
                 "'drips': art.logo_drips('CRYPTMORROW', 1)}",
                 "'drips': art.logo_drips('ICE CRYPT', 1)}"),
                ('game/assets/art.py',
                 "            s.at[row][c] = pal['menu']\n"
                 "    logo(s, 'CRYPTMORROW', 1, pal)",
                 "            s.at[row][c] = pal['menu']\n"
                 "    logo(s, 'ICE CRYPT', 1, pal)")],
         model=[],
         where='`game/assets/build_msx.py` (`WORDS`: the word of the logo '
               'and the drips of moss under it) and `art.py` '
               '(`title_screen`, the drawing the model compares with).',
         see='ICE CRYPT in the big stone letters, centred, with its moss; '
             'the band of the crypt, the menu and the credit as before.',
         limits='The letters of the three words of the game only (the '
                'font has C R Y P T M O W V I A G E). A word is centred '
                'from its number of characters.',
         depends='The asset builder runs again (the font, the words, the '
                 'drips). The test reads `art.py` and `build_msx.py` of '
                 'the folder.',
         expect=[('every title of the sessions = the model of the new '
                  'title', "r['result'] == 'PASS' and all(c['pass'] for c "
                  "in r['checks'] if 'title and the end screens' in "
                  "c['check'])")]),
    dict(id='07b-short-wait', step=7, kind='variant',
         title='A shorter wait on the end screen',
         summary='PRESS FIRE comes 50 passes after the end screen instead '
                 'of 100.',
         edits=[('game/src/screens.asm',
                 'END_DELAY       equ 100         ; passes before FIRE',
                 'END_DELAY       equ 50          ; passes before FIRE')],
         model=['import sessions_0_8; sessions_0_8.V_DELAY = 50',
                'V.END_DELAY = 50'],
         where='`game/src/screens.asm`, the constant `END_DELAY`: the '
               'passes of the end screen before FIRE counts and PRESS '
               'FIRE appears.',
         see='PRESS FIRE one second after the end screen at 50 Hz '
             'instead of two.',
         limits='1-255 (`end_timer` is a byte). A FIRE pressed before '
                'still does not count.',
         depends='Nothing else in the program. The sessions\' end '
                 'screens are played with the same input: the model of '
                 'the states waits 50 passes too.',
         expect=[('every end screen of the sessions = the model of the '
                  'states with 50 passes', "r['result'] == 'PASS'")]),
]

BREAKS = [
    dict(id='01x-status-not-read', step=1, kind='break',
         title='The VDP status not read',
         summary='The interrupt forgets to read the VDP\'s status: the '
                 'request is never cleared.',
         edits=[('game/src/interrupt.asm',
                 '        in a,(VDP_STAT)         ; clears the request',
                 '        xor a                   ; clears the request')],
         symptom='The first frame never ends: the torches stand still, '
                 'nothing changes on the screen.',
         cause='Reading the status register (port `#99`) is what clears '
               'the VDP\'s interrupt request. Without it the line stays '
               'low: as soon as the interrupt ends with `EI` and `RETI`, '
               'the Z80 takes it again, for ever, and the main loop '
               'never runs.',
         fails=r'frame_ready every pass',
         shot=None),
    dict(id='02x-small-sprites', step=2, kind='break',
         title='8 x 8 sprites',
         summary='Register 1 without the size bit: the VDP draws the '
                 'sprites 8 x 8 pixels.',
         edits=[('game/src/vdp.asm',
                 'R1_ON           equ %11100010   ; 16K, on, interrupt, '
                 '16x16',
                 'R1_ON           equ %11100000   ; 16K, on, interrupt, '
                 '16x16')],
         symptom='Only a quarter of the explorer: the top left 8 x 8 '
                 'pixels of its two sprites, a piece of hat and face.',
         cause='Bit 1 of register 1 (SI) picks 16 x 16 sprites; at 0 the '
               'VDP draws 8 x 8 ones, and a shape number picks 8 bytes '
               'instead of 32: shape 0 is the first quarter of the '
               '16 x 16 drawing.',
         fails=r'screen = model',
         shot='step02_eu_Moss_Gate'),
    dict(id='03x-too-fast', step=3, kind='break',
         title='Faster than the VDP',
         summary='The names of the new room sent with OTIR, one every 23 '
                 'T-states during the picture: the rule of 29 broken.',
         edits=[('game/src/room.asm',
                 'pn_byte:\n'
                 '        outi                    ; 18 T\n'
                 '        jp nz,pn_byte           ; 11 T\n',
                 'pn_byte:\n'
                 '        otir                    ; 23 T a byte\n')],
         symptom='At 60 Hz, after a change of room, openMSX ends with a '
                 'VRAM different from the bench\'s: the VDP lost writes '
                 'that came too soon, and cells of the new room can be '
                 'wrong. At 50 Hz the same cartridge is right.',
         cause='During the picture the TMS9918A in Screen 2 needs about '
               '8 microseconds between two accesses to the VRAM - 29 '
               'T-states of the Z80 with the M1 wait, as much as `OUTI` '
               'and `JP NZ`. `OTIR` repeats `OUTI` by itself in 23. '
               'Outside the picture any speed is fine: at 50 Hz there '
               'are 121 lines of it, and `put_names` ends in time; at '
               '60 Hz there are 70, and its last rows go out while the '
               'picture is drawn. A mistake that only one of the two '
               'speeds shows: the test runs both.',
         fails=r'29 T',
         shot=None),
    dict(id='04x-key-stays', step=4, kind='break',
         title='The key that stays',
         summary='A key opens its door and is not used up: `or` instead '
                 'of `xor`.',
         edits=[('game/src/objects.asm',
                 '        xor b                   ; the key is used up',
                 '        or b                    ; the key is used up')],
         symptom='Door A opens and its key is still in the HUD.',
         cause='The key is a bit of `key_set`; `xor` with the door\'s '
               'bit clears it (the bit is set: the key is there), `or` '
               'sets it again.',
         fails=r'keys, seals, score',
         shot=None),
    dict(id='05x-hidden-at-208', step=5, kind='break',
         title='Hidden at Y = 208',
         summary='The blinking explorer is hidden with Y = 208 instead of '
                 'being left out of the list: 208 ends the list.',
         edits=[('game/src/combat.asm',
                 '        ld a,(invulnerable)\n'
                 '        and 4\n'
                 '        ld a,1\n'
                 '        jr z,sc_hero\n'
                 '        xor a                   ; 4 passes off, 4 on\n'
                 'sc_hero:\n'
                 '        ld (hero_shown),a\n'
                 '        call hero_sprites\n',
                 '        ld a,1\n'
                 '        ld (hero_shown),a\n'
                 '        call hero_sprites\n'
                 '        ld a,(invulnerable)\n'
                 '        and 4\n'
                 '        jr z,sc_shown\n'
                 '        ld a,208                ; hidden: off screen?\n'
                 '        ld (hero_sat),a\n'
                 'sc_shown:\n')],
         symptom='While the explorer blinks after a touch, the blade and '
                 'the enemies blink with it: on the frames it is hidden '
                 'nothing is drawn.',
         cause='A sprite whose Y is 208 (`#D0`) ends the list for the '
               'VDP: the sprites after it are not drawn at all. The '
               'explorer is sprite 0.',
         fails=r'the sprite list in the VDP|blow, damage',
         shot=None),
    dict(id='06x-port-a-out', step=6, kind='break',
         title='Port A as an output',
         summary='PSG register 7 written with bit 6 at 1: port A, the '
                 'joysticks, becomes an output.',
         edits=[('game/src/player.asm',
                 'MIXER_OFF       equ %10111111   ; tone and noise off',
                 'MIXER_OFF       equ %11111111   ; tone and noise off')],
         symptom='In openMSX nothing changes (its C-BIOS machines keep '
                 'port A an input, and say so); on an MSX that obeys the '
                 'register the joystick goes dead.',
         cause='Bits 6 and 7 of register 7 set the direction of the '
               'PSG\'s two ports: port A (the joysticks) must stay an '
               'input (0), port B an output (1). `%10xxxxxx` always.',
         fails=r'PSG R7 10xxxxxx|every group of registers sent to the '
               r'PSG',
         shot=None),
    dict(id='07x-address-split', step=7, kind='break',
         title='An address split by the interrupt',
         summary='The two bytes of a VRAM address written with the '
                 'interrupt on.',
         edits=[('game/src/vdp.asm',
                 'vram_write_at:\n        di\n',
                 'vram_write_at:\n')],
         symptom='Now and then a few cells of the title, of an end '
                 'screen or of a room land in the wrong place: when the '
                 'interrupt falls between the two bytes. In the test it '
                 'happens at both speeds, in openMSX as in the bench: the '
                 'title after GAME OVER at 60 Hz, with stray pieces of '
                 'moss and brick (the picture).',
         cause='The address goes to port `#99` in two bytes. The '
               'interrupt reads the status from the same port, and that '
               'read resets the VDP\'s byte counter: the second byte is '
               'taken as a first one, and the next writes go to another '
               'address.',
         fails=r"VDP_CTRL with interrupts off|'ctrl'",
         shot='short_title_again_60hz'),
    dict(id='08x-no-enaslt', step=8, kind='break',
         title='ENASLT forgotten',
         summary='The cartridge never puts its second half in page 2 '
                 '(#8000-#BFFF).',
         edits=[('game/src/start.asm',
                 '        jp ENASLT               ; returns to our caller',
                 '        ret                     ; returns to our caller')],
         symptom='In openMSX, after the C-BIOS logo the screen stays '
                 'black: no opening screen, no title, and FIRE does '
                 'nothing. What the cartridge keeps in page 2 - the '
                 'opening screen, the logo, the zones, the rooms - is read '
                 'from the RAM, and what the program does then depends on '
                 'what the RAM holds: in openMSX it never reaches its '
                 'first frame; in the test bench, with another RAM, the '
                 'title comes without its logo and its menu, and FIRE '
                 'stops it.',
         cause='At INIT only page 1 (#4000-#7FFF) of the cartridge is '
               'selected; the BIOS routine ENASLT puts the cartridge\'s '
               'slot in page 2 as well. Without it, half of the 32 KB is '
               'not there.',
         fails=r'screen|the opening|reached',
         shot=None),
]

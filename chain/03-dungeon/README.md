# Cryptmorrow MSX, step 03 - The dungeon

Sixteen rooms in a grid of 4 x 4, four zones. At an opening the
explorer enters the next room from the opposite side; while the room
changes the screen stays on: the room goes black, is built in several
frames and comes back at once. Row 0 is the HUD: ENERGY and its bar,
the keys, the seals, SCORE.

New or changed: `world.asm`; `hud.asm` (row 0), `room.asm`, `main.asm`, `start.asm`, `vars.asm`.

Not yet: The doors are shut, no objects: the rooms only.

## Build and play

You need Python 3.10 or later, sjasmplus 1.24.0 and openMSX 21.0
with its C-BIOS (pasmo 0.5.3 too, if you want the bytes compared with
a second assembler).

`python tools/run_game.py` builds the cartridge and opens it in
openMSX on a C-BIOS MSX1 at 50 Hz; the arrows move the explorer (or joystick 1, on the keys I J K L). Add `--hz 60` for the 60 Hz
machine. `python tools/build_game.py` only builds: the data
(`game/assets/build_msx.py` and `game/assets/psg_music.py`), the
line length, sjasmplus (pasmo too, if it is found), and checks the
cartridge.

The cartridge is `game/build/cryptmorrow.rom`, 32 768 bytes from
`#4000`, which the BIOS starts by itself. It was tested in openMSX
and in the test bench of the book, not on a real MSX. This step is
generated from the source of the complete game, `game/src`, by
`tools/make_chain.py` at the root of the repository: every file,
routine and data format here is the one of the finished game.

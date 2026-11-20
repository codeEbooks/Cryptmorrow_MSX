# Cryptmorrow MSX, step 01 - The first room

The cartridge starts: the header that the BIOS looks for, INIT,
and page 2 of the memory taken for the cartridge with ENASLT (the
graphics alone are already more than 16 KB). The VDP goes to Screen
2; the Moss Gate's zone puts its cells in the pattern and colour
tables of the three thirds, the room its 16 x 10 metatiles in the name
table and its solid cells in RAM; the name is printed between two
rules. An IM 2 interrupt marks the frames: the main loop waits for it
with `HALT`, and every 8 frames the flames change.

New or changed: every file: `cryptmorrow.asm`, `msx.asm`, `vars.asm`, `start.asm`, `main.asm`, `interrupt.asm`, `vdp.asm`, `zone.asm`, `room.asm`, `hud.asm`, `torches.asm`.

Not yet: No explorer, no keys: the room only.

## Build and play

You need Python 3.10 or later, sjasmplus 1.24.0 and openMSX 21.0
with its C-BIOS (pasmo 0.5.3 too, if you want the bytes compared with
a second assembler).

`python tools/run_game.py` builds the cartridge and opens it in
openMSX on a C-BIOS MSX1 at 50 Hz. Add `--hz 60` for the 60 Hz
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

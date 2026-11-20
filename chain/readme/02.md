# Cryptmorrow MSX, step 02 - The explorer

The explorer, two hardware sprites of 16 x 16, one over the other:
the skin and the clothes. The keyboard (the arrows and SPACE) and
joystick 1 (read through the PSG's port A) make one byte of input;
the explorer walks a pixel a frame, turns, takes a new image every 8
frames, and stops where the pixel ahead of its feet is solid. Each
pass prepares the sprites of the next frame; at the top of the frame
`put_sprites` gives them to the VDP.

New or changed: `input.asm`, `hero.asm`; `combat.asm` (only `show_combat` and `put_sprites`: the rest comes in step 05); `main.asm` (`play_frame`), `start.asm`, `vars.asm`, `msx.asm`.

Not yet: The openings do not lead anywhere yet.

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

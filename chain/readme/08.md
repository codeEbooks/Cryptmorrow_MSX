# Cryptmorrow MSX, step 08 - The complete game

At power on the opening screen, the ZX game's loading screen in the
MSX's colours, for three seconds or until FIRE, the theme already
playing; then the title. This is Cryptmorrow MSX 1.0, byte for byte:
the cartridge, and the tests' cartridges built with `START_PLAY`.

New or changed: `screens.asm` (`show_opening`, `opening_frame`), `start.asm`, `vars.asm`, `cryptmorrow.asm`.

Not yet: Nothing: this is the finished game.

## Build and play

You need Python 3.10 or later, sjasmplus 1.24.0 and openMSX 21.0
with its C-BIOS (pasmo 0.5.3 too, if you want the bytes compared with
a second assembler).

`python tools/run_game.py` builds the cartridge and opens it in
openMSX on a C-BIOS MSX1 at 50 Hz; the arrows move the explorer (or joystick 1, on the keys I J K L), SPACE strikes (the joystick's fire: the right Ctrl); on the title up and down choose the sound, and FIRE, pressed and let go, starts the game. Add `--hz 60` for the 60 Hz
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

# Cryptmorrow MSX, step 06 - Sound

The PSG: the theme of the C64 game in three voices, worked out at the
end of each pass and sent to the PSG by the interrupt; the effects of
the game (the blow, a hit, the dust, an object, a door, a touch, the
ends), each with its priority; the three modes MUSIC, SOUND FX and
SILENT. The mode is the one given to the assembler, `SOUND_MODE`
(0 MUSIC, the default; 1 SOUND FX; 2 SILENT): the menu comes in step
07. From here the interrupt uses the PSG too: the joystick is read
with the interrupt held off.

New or changed: `player.asm`, the music (`game/assets/psg_music.py`); `start.asm` (`psg_init`), `interrupt.asm`, `main.asm`, `world.asm`, `objects.asm`, `combat.asm`, `input.asm`, `vars.asm`, `msx.asm`.

Not yet: No title. After the end the room stands still: reset the machine to play again.

## Build and play

You need Python 3.10 or later, sjasmplus 1.24.0 and openMSX 21.0
with its C-BIOS (pasmo 0.5.3 too, if you want the bytes compared with
a second assembler).

`python tools/run_game.py` builds the cartridge and opens it in
openMSX on a C-BIOS MSX1 at 50 Hz; the arrows move the explorer (or joystick 1, on the keys I J K L), SPACE strikes (the joystick's fire: the right Ctrl). Add `--hz 60` for the 60 Hz
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

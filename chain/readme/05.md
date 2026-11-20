# Cryptmorrow MSX, step 05 - Combat

The sword, the skeletons that patrol and the bats that chase. A blow
lasts 20 passes, with the blade out for 8; a skeleton takes three
hits, a bat one, and leaves a little dust. A touch costs two segments
of energy, then the explorer blinks and cannot be hurt for a while;
with no energy left, GAME OVER. The VDP shows four sprites on a line:
with a fifth, the order of the sprites turns every frame, so that the
one left out flickers instead of vanishing.

New or changed: `combat.asm` (the whole file); `main.asm` (the blow, the enemies, the touches in `play_frame`), `room.asm` (`spawn_enemies`), `hero.asm` (the combat's images), `world.asm`, `interrupt.asm`, `start.asm`, `vars.asm`.

Not yet: No sound. After the end the room stands still: reset the machine to play again.

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

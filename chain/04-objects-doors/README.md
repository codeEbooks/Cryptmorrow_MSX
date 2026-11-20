# Cryptmorrow MSX, step 04 - Objects and doors

Keys, treasures, potions and seals lie in the rooms; a locked door
opens with its key, the portal of the Moss Gate with the three seals;
out through it: VICTORY in the name row. What was taken or opened is
kept in RAM: the rooms' data in the cartridge never change. The score
is BCD, six digits.

New or changed: `objects.asm`; `world.asm` (`victory`), `room.asm` (the door and the objects of a room), `combat.asm` (the explorer hidden at the end), `hero.asm`, `main.asm`, `start.asm`, `vars.asm`.

Not yet: No enemies. After the end the room stands still: to play again, reset the machine (in openMSX F10, `reset`, Enter).

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

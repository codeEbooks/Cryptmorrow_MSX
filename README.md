# Cryptmorrow MSX

The code of **Cryptmorrow**, Volume 1 of the MSX Game Manual Series
(CODE & BOOKS) by Eric A. Norton: a complete game for the MSX1,
written in assembly language for its Z80 processor, and every step of
it as the book builds it.

Cryptmorrow is a dungeon explorer: a cartridge of 32 KB that starts by
itself when the machine is switched on. Seen from above, an explorer
walks through the sixteen rooms of a crypt beneath the hill of Morrow:
an atrium of seven rooms and three zones of three. Keys open doors,
treasures raise the score and potions give back energy; skeletons
patrol and bats give chase, and the explorer fights them with a blade.
Three seals lie in the dungeon: with all three the portal of the Moss
Gate opens, and out through it the game is won. With no energy left,
it is lost. A title screen offers music, sound effects or silence; the
arrow keys and the space bar play, and so does a joystick.

The repository is the companion of the book. Every listing printed in
the book is a part of a file here, line for line, and every cartridge
here can be rebuilt and compared byte for byte (`verify.py`).

## Play without building

`releases/cryptmorrow-msx-1.0.rom` is the complete game, Cryptmorrow
MSX 1.0: a cartridge of 32 768 bytes, seen by the MSX from
`#4000` to `#BFFF`. Open it in openMSX, the emulator the book uses, on
its C-BIOS MSX1 at 50 Hz:

```text
openmsx -machine C-BIOS_MSX1_EU -cart releases/cryptmorrow-msx-1.0.rom
```

`-machine C-BIOS_MSX1` gives the machine at 60 Hz. The arrow keys move
the explorer and SPACE strikes. To play with joystick 1 as well, on
the keys I J K L and the right Ctrl key, as `tools/run_game.py` sets
it up, add:

```text
-command "set msxjoystick1_config {UP {{keyb I}} DOWN {{keyb K}} LEFT {{keyb J}} RIGHT {{keyb L}} A {{keyb RCTRL}} B {{keyb M}}}; plug joyporta msxjoystick1"
```

- At power on, the opening screen shows for three seconds, or until
  FIRE, with the theme already playing; then the title.
- On the title, up and down choose the sound: MUSIC, SOUND FX or
  SILENT. FIRE, pressed and let go, starts the game.
- After the end screen, FIRE goes back to the title.

The game was tested in openMSX 21.0, with its C-BIOS 0.29, and in the
test bench of the book, at 50 and at 60 Hz. It was not tested on a real
MSX, on another emulator or with a real cartridge made from this file.

SHA-256 of the cartridge:
`ee48662a9c40c039c26017d55ad8dc14786c1d8bcf3842d1831025b8d5f6adbd`

## What is here

```text
game/          the complete game, 1.0: the master source (game/src),
               whose comments also say in which steps each line exists,
               and the data of its rooms, graphics and sound
               (game/assets); game/build holds only the two states of
               C-BIOS that the tests start from
chain/         the eight steps of the book, 01 to 08: each folder has
               its own copy of every source and tool it needs and
               builds on its own
variants/      22 experiments of the book, each a step with one change:
               14 guided variants and 8 "Where it breaks" versions,
               each with a README and the report of its test
               (evidence/)
tests/         the tests the book relies on (chapter 16)
tools/         run_game.py, which builds and plays, and the tools
               named in the book
fase0/         the probe of the first measurements, which the test of
               the palettes runs, and a copy of C-BIOS, the free BIOS
               the test bench runs (fase0/README.md)
reference/     the reference cartridges of the steps and of the
               variants, and the reports of the book's runs of the
               tests of the steps
releases/      the complete game, as a cartridge
verify.py      builds everything again and compares it byte for byte
CHAPTERS.md    chapter by chapter: its step, experiments and tools
TESTING.md     what was tested, with which versions, and the limits
SHA256SUMS.txt the SHA-256 of every file
LICENSE        MIT
```

## What you need

None of these programs is included; download them from their sites.

- **sjasmplus** 1.24.0, the assembler (github.com/z00m128/sjasmplus).
  Another version may give other bytes.
- **openMSX** 21.0, the emulator (openmsx.org). It comes with C-BIOS,
  a free BIOS that starts cartridges; the book uses two of its
  machines, `C-BIOS_MSX1_EU` (50 Hz) and `C-BIOS_MSX1` (60 Hz).
- **Python** 3.10 or later (python.org). The build uses its standard
  library only.
- Optional: **pasmo** 0.5.3, a second assembler: when it is found the
  build checks that it gives the same bytes.
- For the tests only: **SkoolKit** 10.1 (`pip install skoolkit`),
  whose Z80 simulator the test bench is built around.

The tools look for `sjasmplus`, `pasmo` and `openmsx` on the PATH, the
folders where the system looks for programs; then for `sjasmplus.exe`,
`pasmo.exe` or `openmsx.exe` anywhere in the folder `tools` (on
Windows, the archives of these programs can be unpacked there as they
come); then where openMSX is usually installed. A program elsewhere is
given by its full path: `tools/build_game.py --sjasmplus PATH` (and
`--pasmo PATH`), `tools/run_game.py --openmsx PATH`, `verify.py
--sjasmplus PATH`. With sjasmplus outside the PATH, build first with
`build_game.py --sjasmplus PATH`, then play with `run_game.py
--no-build`.

## Build and play a step

Open a command prompt in a step folder, for example
`chain/01-first-room` (on Windows, type `cmd` in the address bar of
File Explorer and press Enter), and type:

```text
python tools/run_game.py
```

On Windows, if `python` is not found, try `py`. `run_game.py` builds
first with `tools/build_game.py`: `game/assets/build_msx.py` and
`game/assets/psg_music.py` make the data again, and it must be the data
in `game/assets/generated/B` (`--assets` writes it there first, after a
change to a room, a drawing or the music); `tools/check_lines.py`
checks that no source line is longer than 60 characters; sjasmplus
assembles `game/src/cryptmorrow.asm` into `game/build/cryptmorrow.rom`
(with its symbols, `.sym`, and its listing, `.lst`); the cartridge must
be 32 768 bytes, with the header the BIOS looks for; and pasmo, if it is
found, must give the same bytes. Then openMSX starts a C-BIOS MSX1 at
50 Hz with the cartridge in its slot; `--hz 60` gives the machine at 60
Hz, `python tools/build_game.py` only builds. The build records what it
made in `game/build/manifest.json`: the versions of the tools, and the
size and SHA-256 of every cartridge (`build_game.py --reference FILE`
compares them with another manifest). From step 07 the build also makes
the tests' cartridges and one cartridge for each room, 20 in all
(chapter 16).

The same works in every folder of `chain` and `variants`. At the root
of the repository, `python tools/build_game.py` builds `game/`, the
master source, into the complete game, the same bytes as step 08, and
`python tools/run_game.py` plays it.

Work on a copy of a step, not on the step itself (chapter 1): copy the
folder beside the original and rename it; a step builds wherever it
stands. The book and `verify.py` compare your cartridges with the steps
as they are.

## Check that you build the book's cartridges

```text
python verify.py
```

`verify.py` checks every file against `SHA256SUMS.txt`, builds the
complete game, the eight steps and the 22 variants again in a temporary
folder, each with its own tools, and compares every cartridge, byte for
byte, with the one in `reference/` or `releases/`, and the 20
cartridges of steps 07 and 08 with those `chain/chain.json` records; it
also assembles the probe of `fase0/` again. A file you changed on
purpose is reported as changed. `python verify.py chain/03` builds only
what matches; `python verify.py --files-only` checks the files and the
headers of the cartridges without sjasmplus.

The cartridges of the steps:

| Step | SHA-256 of the cartridge | Code, data, free (bytes) | Cartridges |
|---|---|---|---|
| `chain/01-first-room` | `1f33844596f28e36b84e5a2b0dbb6123686abe6a33cbdee590be353a1487bf8c` | 860, 19 124, 12 784 | 1 |
| `chain/02-explorer` | `bd3456a5b09c5d3271470da545a24c78cf3c51726e244468d4a05c71186c75bd` | 1 311, 19 636, 11 821 | 1 |
| `chain/03-dungeon` | `eed3d3f53feece189c7ba77ca5139f7bec88815b6f9abcb09e58019f1567809b` | 1 615, 19 636, 11 517 | 1 |
| `chain/04-objects-doors` | `4539d0015ed5e134b6772f5a3ac0d7d7b3933c1be178971700662a54d106a8c5` | 2 245, 19 696, 10 827 | 1 |
| `chain/05-combat` | `1a4338e461e4bcbe2405178bee56ce7964de39d965186c5aec81cb211ed16553` | 3 328, 19 984, 9 456 | 1 |
| `chain/06-sound` | `5b61f06f3420d9ce7a9c2430960bb89cb69898118f3c22e899e06aa89e8cce5e` | 4 325, 21 499, 6 944 | 1 |
| `chain/07-title-and-ends` | `fbd460f7202b102e477460f8711ca48c7fa5bf9d205013c3d47387b301dea244` | 6 016, 22 630, 4 122 | 20 |
| `chain/08-complete` | `ee48662a9c40c039c26017d55ad8dc14786c1d8bcf3842d1831025b8d5f6adbd` | 6 120, 26 209, 439 | 20 |

## Run the tests

Build first: `python tools/build_game.py` at the root of the
repository and in the folder of the step (a test reads the cartridges
and the symbols of `game/build`). Then, from the root, with SkoolKit
installed and openMSX found:

```text
python tests/verify_step.py --step 3
python tests/verify_1_0.py --step 8 --out reports/08
```

`verify_step.py` tests steps 01 to 06 and `verify_1_0.py --step 7` or
`--step 8` the complete game in steps 07 and 08 (`--out DIR`, where the
report goes, is required there); `python tests/verify_1_0.py --out DIR`
alone tests the master source. A test starts the step's cartridges from
the state C-BIOS had at INIT (`game/build/state_eu.json`,
`state_int.json`) in the bench, an MSX1 around SkoolKit's Z80
(`tests/msxsim.py`), and in openMSX, at 50 and at 60 Hz, and plays
routes or sessions a pass at a time against models written in Python,
comparing the screen, the sprites, the PSG's registers and the RAM; then
it puts one-line faults into copies of the program (the mutations) and
must stop each one. `--no-openmsx` leaves openMSX out, `--no-mutations`
(`verify_step.py`) the faults. The bench runs C-BIOS too: its ROMs are
found next to openMSX, among its machines, or else in `fase0/cbios`,
the copy of C-BIOS 0.29 that comes with this repository.

`verify_step.py` writes its report to
`chain/evidence-workspace/steps/NN/verify_step.json` (`--out DIR`
elsewhere). `--reference reference/reports/NN-name.json` also compares
every fact of the bench (in steps 07 and 08, of openMSX too) with the
book's run of the same test, in one check more (two in steps 07 and
08): the 696 checks of step 08 that chapter 16 gives count these two.
On the computer of the book's runs steps 07 and 08 took about 45
minutes each, the other steps from half a minute to a quarter of an
hour. [TESTING.md](TESTING.md) tells what was checked, and how.

## Rights

The contents of this repository, source code, data, tools, tests and
cartridges, including the graphics, rooms, font, sprites, music and
sound effects in `game/assets`, are released under the MIT License: see
[LICENSE](LICENSE). Copyright (c) 2026 Eric A. Norton.

The one exception is `fase0/cbios`: C-BIOS 0.29, the free BIOS for MSX
emulators, the same files that come with openMSX 21.0. It is the work
of its own authors and is redistributed under its own licence, a BSD
licence printed with the copyright notices in
`fase0/cbios/README.cbios.txt`; the MIT License of this repository does
not cover it.

The book is not part of this repository and is not covered by this
license: its text, figures, layout and cover are copyright (c) 2026
Eric A. Norton, all rights reserved. Book by Eric A. Norton; music and
history edited by Jorah Sallow.

Everything in the game was made for it: graphics, rooms, font,
sprites, music and sound effects. No ROM of an MSX, no emulator and
no assembler is included; the only BIOS here is C-BIOS, which is free
software. MSX, ZX Spectrum, Commodore 64 and the other
product names are used to identify the machines and the tools; this is
an independent project, not affiliated with or endorsed by their
owners.

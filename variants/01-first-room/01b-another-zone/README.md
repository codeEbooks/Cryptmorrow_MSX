# Cryptmorrow MSX, step 01 - variant 01b: The colours of another zone

The Moss Gate in the colours of zone C, the amber wing. One line of data.

This folder is step 01 (`chain/01-first-room` in this repository) with one change.

## Where

`game/assets/rooms/moss_gate.txt`, the header of the room: a line `zone:` (without it a room is in the atrium, `atrio` in the data). The asset builder (`build_msx.py`) writes the zone into the room's record; `enter_room` reads it and `load_zone` copies that zone's patterns and colours into the three thirds of the VRAM.

## Before (`game/assets/rooms/moss_gate.txt`)

```text
name: THE MOSS GATE
door: portal
```

## After

```text
name: THE MOSS GATE
zone: C
door: portal
```

## What you will see

The same room in the amber of zone C: the walls, the floor and the pillars in its colours, the moss gone from the walls (zone C grows none).

## Allowed values and limits

`atrio`, `A`, `B` or `C` (`ZONES` in `dungeon.py`). A room keeps its map; only the colours of its roles and the moss of the zone change.

## What else depends on it

The asset builder runs again (`tools/build_game.py --assets` does it): the room table, nothing else. In the later steps the start room would look like the treasury.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 1 --folder variants/01-first-room/01b-another-zone --out variants/01-first-room/01b-another-zone/evidence --no-mutations`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: none: the test reads the data of this folder). Result: PASS, 26 checks; shown: the start room in zone 3 (C), = the model of the new data. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/01-first-room`.

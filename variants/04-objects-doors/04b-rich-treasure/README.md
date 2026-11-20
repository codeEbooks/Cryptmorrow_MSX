# Cryptmorrow MSX, step 04 - variant 04b: Richer treasures

A treasure is worth 500 points instead of 250.

This folder is step 04 (`chain/04-objects-doors` in this repository) with one change.

## Where

`game/src/objects.asm`, the points of a treasure: two BCD digits a byte, added to `score` with `DAA`.

## Before (`game/src/objects.asm`)

```asm
        ld de,#0250             ; 250 points (BCD)
```

## After

```asm
        ld de,#0500             ; 500 points (BCD)
```

## What you will see

VICTORY at 7 000 points instead of 5 000: the same eight treasures.

## Allowed values and limits

BCD digits only (`#0999` at most here: the score has 6 digits and `add_score` adds four of them); `#0A00` is not a number for `DAA`.

## What else depends on it

Nothing else; the HUD shows what `score` holds.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 4 --folder variants/04-objects-doors/04b-rich-treasure --out variants/04-objects-doors/04b-rich-treasure/evidence --no-mutations --set "W.POINTS[W.KIND_TREASURE] = 500"`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `W.POINTS[W.KIND_TREASURE] = 500`). Result: PASS, 35 checks; shown: VICTORY at 7 000 points (5 000 in the step). Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/04-objects-doors`.

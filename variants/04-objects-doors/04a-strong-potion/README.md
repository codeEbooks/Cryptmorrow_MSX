# Cryptmorrow MSX, step 04 - variant 04a: A stronger potion

A potion gives back 4 segments of energy instead of 2.

This folder is step 04 (`chain/04-objects-doors` in this repository) with one change.

## Where

`game/src/objects.asm`, the constant `POTION_ENERGY`, added to the energy (up to `ENERGY_MAX`) when a potion is taken.

## Before (`game/src/objects.asm`)

```asm
POTION_ENERGY   equ 2
```

## After

```asm
POTION_ENERGY   equ 4
```

## What you will see

From 3 segments a potion brings the bar to 7, not 5. With the bar full a potion still stays on the floor.

## Allowed values and limits

1-8: the energy stops at `ENERGY_MAX` (8) anyway.

## What else depends on it

Nothing else. In step 04 nothing takes energy away: the test puts 3 in memory, as the book does.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 4 --folder variants/04-objects-doors/04a-strong-potion --out variants/04-objects-doors/04a-strong-potion/evidence --no-mutations --set "W.POTION_ENERGY = 4" --route potion`): every pass of a route of its own (`potion`), at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `W.POTION_ENERGY = 4`). Result: PASS, 33 checks; shown: the energy 8, put at 3, then 7 after the potion. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/04-objects-doors`.

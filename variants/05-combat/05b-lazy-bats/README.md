# Cryptmorrow MSX, step 05 - variant 05b: Lazy bats

A bat wakes only within 48 x 45 pixels of the explorer instead of 96 x 90.

This folder is step 05 (`chain/05-combat` in this repository) with one change.

## Where

`game/src/combat.asm`, the constants `CHASE_X` and `CHASE_Y`: the distances across and down within which `update_enemies` moves a bat towards the explorer.

## Before (`game/src/combat.asm`)

```asm
CHASE_X         equ 96          ; a bat chases the explorer
CHASE_Y         equ 90          ; inside this distance
```

## After

```asm
CHASE_X         equ 48          ; a bat chases the explorer
CHASE_Y         equ 45          ; inside this distance
```

## What you will see

In the Root Cellar the bat stays asleep with the explorer 80 pixels away (it used to wake at 96) and wakes at less than 48.

## Allowed values and limits

Under 256 across (`far_x` is a byte) and 192 down. At 8 or less a bat touches before it wakes.

## What else depends on it

The planned whole game waits for the bats to come: with lazy bats it no longer works (the Bone Shrine stays guarded). The test plays a route of its own: the planned game to the Root Cellar, then still, then closer.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 5 --folder variants/05-combat/05b-lazy-bats --out variants/05-combat/05b-lazy-bats/evidence --no-mutations --set "W.CHASE_X, W.CHASE_Y = 48, 45" --route bats`): every pass of a route of its own (`bats`), at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `W.CHASE_X, W.CHASE_Y = 48, 45`). Result: PASS, 36 checks; shown: the bat still for 150 passes with the explorer inside 96 x 90, awake at less than 48 across. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/05-combat`.

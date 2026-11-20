# Cryptmorrow MSX, step 05 - variant 05a: Lighter damage

A touch takes 1 segment of energy instead of 2.

This folder is step 05 (`chain/05-combat` in this repository) with one change.

## Where

`game/src/combat.asm`, the constant `DAMAGE`, taken from `energy` by `check_contact`.

## Before (`game/src/combat.asm`)

```asm
DAMAGE          equ 2           ; energy lost at a touch
```

## After

```asm
DAMAGE          equ 1           ; energy lost at a touch
```

## What you will see

Eight touches before GAME OVER instead of four; the bar goes down one segment at a time.

## Allowed values and limits

1-8 (8: GAME OVER at the first touch). An odd damage makes the energy odd: `check_contact` stops at 0, not below.

## What else depends on it

Nothing else; after each touch the explorer is safe for 30 passes (`SAFE_FRAMES`), as before.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 5 --folder variants/05-combat/05a-light-damage --out variants/05-combat/05a-light-damage/evidence --no-mutations --set "W.DAMAGE = 1"`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `W.DAMAGE = 1`). Result: PASS, 68 checks; shown: GAME OVER without help after eight touches (seven, then the last). Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/05-combat`.

# Cryptmorrow MSX, step 07 - variant 07b: A shorter wait on the end screen

PRESS FIRE comes 50 passes after the end screen instead of 100.

This folder is step 07 (`chain/07-title-and-ends` in this repository) with one change.

## Where

`game/src/screens.asm`, the constant `END_DELAY`: the passes of the end screen before FIRE counts and PRESS FIRE appears.

## Before (`game/src/screens.asm`)

```asm
END_DELAY       equ 100         ; passes before FIRE
```

## After

```asm
END_DELAY       equ 50          ; passes before FIRE
```

## What you will see

PRESS FIRE one second after the end screen at 50 Hz instead of two.

## Allowed values and limits

1-255 (`end_timer` is a byte). A FIRE pressed before still does not count.

## What else depends on it

Nothing else in the program. The sessions' end screens are played with the same input: the model of the states waits 50 passes too.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_1_0.py --step 7 --folder variants/07-title-and-ends/07b-short-wait --out variants/07-title-and-ends/07b-short-wait/evidence --only data,sound,palettes,game,defeat,shots,rooms,alone,sessions,players,systems --set "import sessions_0_8; sessions_0_8.V_DELAY = 50" --set "V.END_DELAY = 50"`): every pass of the games, of the sessions and of the three players of the test of 1.0, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `import sessions_0_8; sessions_0_8.V_DELAY = 50`, `V.END_DELAY = 50`). Result: PASS, 590 checks; shown: every end screen of the sessions = the model of the states with 50 passes. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/07-title-and-ends`.

# Cryptmorrow MSX, step 01 - variant 01a: Faster flames

The torches flicker twice as fast: a new flame every 4 frames instead of every 8.

This folder is step 01 (`chain/01-first-room` in this repository) with one change.

## Where

`game/src/torches.asm`, the first lines of `animate_torches`: the low byte of `frames` and the mask `%00011000`, which keeps bits 3 and 4 - the phase (frames / 8) mod 4, already multiplied by 8, the bytes of a flame.

## Before (`game/src/torches.asm`)

```asm
        ld a,(frames)
        and %00011000           ; the phase due, x 8
```

## After

```asm
        ld a,(frames)
        add a,a                 ; frames x 2: every 4
        and %00011000           ; the phase due, x 8
```

## What you will see

Every torch changes its flame every 4 frames, 12.5 times a second at 50 Hz (15 at 60 Hz); the four flames come in the same order.

## Allowed values and limits

One `add a,a` halves the period (4 frames), two give 2, one `rrca` instead doubles it (16): the mask must stay `%00011000`, the place of the phase times 8. The four flames stay four (`flame_phases`).

## What else depends on it

Nothing else: `animate_torches` draws the phase it finds, and only when it changes (`flame_phase`). The test's model has the same period (`FLAME_SHIFT`: the phase is frames >> 2).

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 1 --folder variants/01-first-room/01a-faster-flames --out variants/01-first-room/01a-faster-flames/evidence --no-mutations --set "VS.FLAME_SHIFT = 2"`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `VS.FLAME_SHIFT = 2`). Result: PASS, 26 checks; shown: the flame changed about twice as often (about 100 times in 402 passes; 50 in the step). Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/01-first-room`.

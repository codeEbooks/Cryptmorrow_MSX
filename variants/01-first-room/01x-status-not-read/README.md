# Cryptmorrow MSX, step 01 - where it breaks: The VDP status not read

The interrupt forgets to read the VDP's status: the request is never cleared.

This folder is step 01 (`chain/01-first-room` in this repository) with a mistake made on purpose.

## Before (`game/src/interrupt.asm`)

```asm
        in a,(VDP_STAT)         ; clears the request
```

## After

```asm
        xor a                   ; clears the request
```

## Symptom

The first frame never ends: the torches stand still, nothing changes on the screen.

## Cause

Reading the status register (port `#99`) is what clears the VDP's interrupt request. Without it the line stays low: as soon as the interrupt ends with `EI` and `RETI`, the Z80 takes it again, for ever, and the main loop never runs.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How the test catches it

`python tests/verify_step.py --step 1 --folder variants/01-first-room/01x-status-not-read --out variants/01-first-room/01x-status-not-read/evidence --no-mutations` fails: "frame_ready every pass: the first one after INIT, for the data in the VRAM ($4097 not reached in 2854560 T-states)"

## Repair

Put back the lines of *Before*, or start again from `chain/01-first-room`.

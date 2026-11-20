# Cryptmorrow MSX, step 02 - variant 02b: The joystick in port 2

The explorer follows the joystick in port 2 instead of port 1: one bit of PSG register 15.

This folder is step 02 (`chain/02-explorer` in this repository) with one change.

## Where

`game/src/input.asm`, the value written to PSG register 15 before register 14 is read: bit 6 picks the port (0: port 1, 1: port 2); bits 4 and 5 are pin 8 of the two ports, kept low.

## Before (`game/src/input.asm`)

```asm
JOY_PORT1       equ %10001111   ; R15: port 1, pin 8 low
```

## After

```asm
JOY_PORT1       equ %11001111   ; R15: port 2, pin 8 low
```

## What you will see

The arrows and SPACE still work; the stick and button A now come from port 2 (in openMSX: plug a joystick into `joyportb`); the stick in port 1 does nothing.

## Allowed values and limits

Bit 6 picks one port at a time: to read both, read register 14 twice, with bit 6 at 0 and then at 1. The name `JOY_PORT1` stays: the README says why.

## What else depends on it

Nothing else reads the joystick. The test plugs its joystick into port 2 (`JOY_PORT`, in the bench and in openMSX).

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX; then, in openMSX's console (F10), `unplug joyporta` and `plug joyportb msxjoystick1`: the keys I J K L move the stick of port 2.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 2 --folder variants/02-explorer/02b-joystick-port-2 --out variants/02-explorer/02b-joystick-port-2/evidence --no-mutations --set "VS.JOY_PORT = 2"`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `VS.JOY_PORT = 2`). Result: PASS, 31 checks; shown: the explorer moved with the joystick of port 2 alone (passes with the stick only). Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/02-explorer`.

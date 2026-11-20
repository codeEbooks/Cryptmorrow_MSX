# Cryptmorrow MSX, step 06 - where it breaks: Port A as an output

PSG register 7 written with bit 6 at 1: port A, the joysticks, becomes an output.

This folder is step 06 (`chain/06-sound` in this repository) with a mistake made on purpose.

## Before (`game/src/player.asm`)

```asm
MIXER_OFF       equ %10111111   ; tone and noise off
```

## After

```asm
MIXER_OFF       equ %11111111   ; tone and noise off
```

## Symptom

In openMSX nothing changes (its C-BIOS machines keep port A an input, and say so); on an MSX that obeys the register the joystick goes dead.

## Cause

Bits 6 and 7 of register 7 set the direction of the PSG's two ports: port A (the joysticks) must stay an input (0), port B an output (1). `%10xxxxxx` always.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX: the game plays as before (openMSX's C-BIOS machines keep port A an input); the test sees register 7.

## How the test catches it

`python tests/verify_step.py --step 6 --folder variants/06-sound/06x-port-a-out --out variants/06-sound/06x-port-a-out/evidence --no-mutations` fails: "eu (50 Hz) the whole game: every group of registers sent to the PSG = the model (psg_model), the other writes as they must be (pass 1: group 0 of 3 (model 3): [0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0], model [0, 0, 0, 0, 0, 0, 0, 191, 0, 0, 0] (now))"

## Repair

Put back the lines of *Before*, or start again from `chain/06-sound`.

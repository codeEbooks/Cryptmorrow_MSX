# Cryptmorrow MSX, step 02 - where it breaks: 8 x 8 sprites

Register 1 without the size bit: the VDP draws the sprites 8 x 8 pixels.

This folder is step 02 (`chain/02-explorer` in this repository) with a mistake made on purpose.

## Before (`game/src/vdp.asm`)

```asm
R1_ON           equ %11100010   ; 16K, on, interrupt, 16x16
```

## After

```asm
R1_ON           equ %11100000   ; 16K, on, interrupt, 16x16
```

## Symptom

Only a quarter of the explorer: the top left 8 x 8 pixels of its two sprites, a piece of hat and face.

## Cause

Bit 1 of register 1 (SI) picks 16 x 16 sprites; at 0 the VDP draws 8 x 8 ones, and a shape number picks 8 bytes instead of 32: shape 0 is the first quarter of the 16 x 16 drawing.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How the test catches it

`python tests/verify_step.py --step 2 --folder variants/02-explorer/02x-small-sprites --out variants/02-explorer/02x-small-sprites/evidence --no-mutations` fails: "eu (50 Hz) Moss Gate: screen = model, every pass (pass 1 (room 1): pixel (128, 104) colour 1, model 10)"

Picture: `evidence/png/step02_eu_Moss_Gate_00164_far_north.png`.

## Repair

Put back the lines of *Before*, or start again from `chain/02-explorer`.

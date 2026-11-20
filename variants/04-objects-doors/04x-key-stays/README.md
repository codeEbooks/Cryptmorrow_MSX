# Cryptmorrow MSX, step 04 - where it breaks: The key that stays

A key opens its door and is not used up: `or` instead of `xor`.

This folder is step 04 (`chain/04-objects-doors` in this repository) with a mistake made on purpose.

## Before (`game/src/objects.asm`)

```asm
        xor b                   ; the key is used up
```

## After

```asm
        or b                    ; the key is used up
```

## Symptom

Door A opens and its key is still in the HUD.

## Cause

The key is a bit of `key_set`; `xor` with the door's bit clears it (the bit is set: the key is there), `or` sets it again.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How the test catches it

`python tests/verify_step.py --step 4 --folder variants/04-objects-doors/04x-key-stays --out variants/04-objects-doors/04x-key-stays/evidence --no-mutations` fails: "eu (50 Hz) the walking game: keys, seals, score, energy, doors, end, objects (pass 3147: (1, 0, 750, 8, 1, 0), model (0, 0, 750, 8, 1, 0))"

## Repair

Put back the lines of *Before*, or start again from `chain/04-objects-doors`.

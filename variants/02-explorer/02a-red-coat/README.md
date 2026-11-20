# Cryptmorrow MSX, step 02 - variant 02a: A red coat

The explorer's hat and coat in dark red instead of dark yellow: one sprite, one colour.

This folder is step 02 (`chain/02-explorer` in this repository) with one change.

## Where

`game/src/hero.asm`, the constant `HERO_CLOTHES`: the colour byte of sprite 1, the clothes, in `hero_sat` (`hero_sprites`).

## Before (`game/src/hero.asm`)

```asm
HERO_CLOTHES    equ 10          ; dark yellow: hat, coat
```

## After

```asm
HERO_CLOTHES    equ 6           ; dark red: hat, coat
```

## What you will see

The same explorer with a dark red hat and coat; the face and the hands (sprite 0, `HERO_SKIN`) stay light red.

## Allowed values and limits

Any of the 15 colours (1-15; 0 is transparent: the clothes would vanish). A sprite has one colour: a third colour would need a third sprite on the same lines, one of the four a line allows.

## What else depends on it

Nothing: the shapes do not change, only the colour byte of the list.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 2 --folder variants/02-explorer/02a-red-coat --out variants/02-explorer/02a-red-coat/evidence --no-mutations --set "MM.HERO_CLOTHES = 6"`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `MM.HERO_CLOTHES = 6`). Result: PASS, 31 checks; shown: sprite 1 (the clothes) in colour 6, sprite 0 (the skin) in 9. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/02-explorer`.

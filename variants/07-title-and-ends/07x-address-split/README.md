# Cryptmorrow MSX, step 07 - where it breaks: An address split by the interrupt

The two bytes of a VRAM address written with the interrupt on.

This folder is step 07 (`chain/07-title-and-ends` in this repository) with a mistake made on purpose.

## Before (`game/src/vdp.asm`)

```asm
vram_write_at:
        di
```

## After

```asm
vram_write_at:
```

## Symptom

Now and then a few cells of the title, of an end screen or of a room land in the wrong place: when the interrupt falls between the two bytes. In the test it happens at both speeds, in openMSX as in the bench: the title after GAME OVER at 60 Hz, with stray pieces of moss and brick (the picture).

## Cause

The address goes to port `#99` in two bytes. The interrupt reads the status from the same port, and that read resets the VDP's byte counter: the second byte is taken as a first one, and the next writes go to another address.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How the test catches it

`python tests/verify_1_0.py --step 7 --folder variants/07-title-and-ends/07x-address-split --out variants/07-title-and-ends/07x-address-split/evidence --only data,sound,palettes,game,defeat,shots,rooms,alone,sessions,players,systems` fails: "eu (50 Hz): the theme in the bench, 3192 passes standing in the Moss Gate: every pass = the model (explorer, screen, sounds asked, PSG), the rules ({'ctrl': ['$41CC at T 772934']})"

Picture: `evidence/png/short_title_again_60hz.png`.

## Repair

Put back the lines of *Before*, or start again from `chain/07-title-and-ends`.

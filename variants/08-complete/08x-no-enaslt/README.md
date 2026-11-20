# Cryptmorrow MSX, step 08 - where it breaks: ENASLT forgotten

The cartridge never puts its second half in page 2 (#8000-#BFFF).

This folder is step 08 (`chain/08-complete` in this repository) with a mistake made on purpose.

## Before (`game/src/start.asm`)

```asm
        jp ENASLT               ; returns to our caller
```

## After

```asm
        ret                     ; returns to our caller
```

## Symptom

In openMSX, after the C-BIOS logo the screen stays black: no opening screen, no title, and FIRE does nothing. What the cartridge keeps in page 2 - the opening screen, the logo, the zones, the rooms - is read from the RAM, and what the program does then depends on what the RAM holds: in openMSX it never reaches its first frame; in the test bench, with another RAM, the title comes without its logo and its menu, and FIRE stops it.

## Cause

At INIT only page 1 (#4000-#7FFF) of the cartridge is selected; the BIOS routine ENASLT puts the cartridge's slot in page 2 as well. Without it, half of the 32 KB is not there.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How the test catches it

`python tests/verify_1_0.py --step 8 --folder variants/08-complete/08x-no-enaslt --out variants/08-complete/08x-no-enaslt/evidence --only data,sound,palettes,game,defeat,shots,rooms,alone,sessions,players,systems` fails: "data: the program reached every pass ($413D not reached in 2854560 T-states)"

## Repair

Put back the lines of *Before*, or start again from `chain/08-complete`.

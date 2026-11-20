# Cryptmorrow MSX, step 06 - variant 06a: Effects only

The game starts in SOUND FX: the effects on the PSG, no music.

This folder is step 06 (`chain/06-sound` in this repository) with one change.

## Where

`game/src/start.asm`, the mode given to `set_audio` at INIT: 0 MUSIC, 1 SOUND FX, 2 SILENT (in step 06 it comes from the assembler, `SOUND_MODE`; from step 07 from the menu of the title).

## Before (`game/src/start.asm`)

```asm
        ld a,SOUND_MODE         ; MUSIC, SOUND FX or SILENT
```

## After

```asm
        ld a,1                  ; SOUND FX (2: SILENT)
```

## What you will see

No theme: only the effects, the blow, the hits, the doors, the objects, the touches, and the effect of the end.

## Allowed values and limits

0, 1 or 2. With 2 (SILENT) the PSG is silent all the game: the interrupt still sends its registers, all at volume 0.

## What else depends on it

Nothing else: `set_audio` sets the mode for `sound_effect` and `end_sound`.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 6 --folder variants/06-sound/06a-effects-first --out variants/06-sound/06a-effects-first/evidence --no-mutations --set "VS.SOUND_MODE = 1"`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `VS.SOUND_MODE = 1`). Result: PASS, 81 checks; shown: no group of the music sent to the PSG, the effects yes. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/06-sound`.

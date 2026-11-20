# Cryptmorrow MSX, step 06 - variant 06b: Faster music

The theme at 150 beats a minute instead of 125: 5 frames a step instead of 6.

This folder is step 06 (`chain/06-sound` in this repository) with one change.

## Where

`game/assets/c64/score.py`, `SPEED`: the frames of a step (a sixteenth note) at 50 Hz; `psg_music.py` makes the 60 Hz speed from it (`round(SPEED x 60 / 50)`) and checks the speeds it was approved with: a variant changes that check too.

## Before (`game/assets/c64/score.py`)

```python
SPEED = 6            # frames per step: 50 / 6 * 60 / 4 = 125 BPM (PAL)
```

## After

```python
SPEED = 5            # frames per step: 50 / 5 * 60 / 4 = 150 BPM (PAL)
```

### Before (`game/assets/psg_music.py`)

```python
    if GATE_BEFORE != 2 or SPEED_60 != 7:
        raise ValueError('the speeds approved: 6 and 7, gate 2')
```

### After

```python
    if GATE_BEFORE != 1 or SPEED_60 != 6:
        raise ValueError('the speeds of this variant: 5 and 6, gate 1')
```

## What you will see

The same theme and the same pieces of the end, faster: 150 beats a minute at 50 Hz, 6 frames a step at 60 Hz.

## Allowed values and limits

The release of a note comes `GATE_TICK` (4) frames into its step: under 5 frames a step the note would have no time before its release.

## What else depends on it

The music data again (`music.asm`: `SPEED_50`, `SPEED_60`, `GATE_BEFORE`); the test reads the `music.json` of the folder.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 6 --folder variants/06-sound/06b-faster-music --out variants/06-sound/06b-faster-music/evidence --no-mutations`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: none: the test reads the data of this folder). Result: PASS, 81 checks; shown: the PSG = the model at 5 frames a step (6 at 60 Hz). Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/06-sound`.

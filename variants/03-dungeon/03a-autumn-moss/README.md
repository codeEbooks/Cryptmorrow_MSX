# Cryptmorrow MSX, step 03 - variant 03a: Autumn moss

The moss of the atrium in yellow and red instead of three greens.

This folder is step 03 (`chain/03-dungeon` in this repository) with one change.

## Where

`game/assets/build_msx.py`, the table `ROWS_B`: the colour of each of the 8 pixel rows of a cell, for the roles whose colour has a row of its own in the graphics B (the approved ones). The moss: light green at the tip, medium, dark at the root.

## Before (`game/assets/build_msx.py`)

```python
    'moss': ('ink', 12, [3, 3, 2, 2, 2, 12, 12, 12]),
    'mossface': ('ink', 12, [3, 3, 2, 2, 2, 12, 12, 12]),
    'fmoss': ('ink', 12, [3, 3, 2, 2, 2, 12, 12, 12]),
```

## After

```python
    'moss': ('ink', 12, [11, 11, 10, 10, 10, 6, 6, 6]),
    'mossface': ('ink', 12, [11, 11, 10, 10, 10, 6, 6, 6]),
    'fmoss': ('ink', 12, [11, 11, 10, 10, 10, 6, 6, 6]),
```

## What you will see

The moss on the walls and the tufts on the floor of the atrium in light yellow, dark yellow and dark red.

## Allowed values and limits

Eight colours, one a row, 1-15 each; the paper of the cell stays the stone's. Only the atrium grows moss with these rows.

## What else depends on it

The asset builder runs again (the colours of the zone atrio). The title's moss under the logo uses the same rows: from step 07 it would turn autumn too.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 3 --folder variants/03-dungeon/03a-autumn-moss --out variants/03-dungeon/03a-autumn-moss/evidence --no-mutations --set "MM.ROWS_B['moss'] = ('ink', 12, (11, 11, 10, 10, 10, 6, 6, 6))" --set "MM.ROWS_B['mossface'] = ('ink', 12, (11, 11, 10, 10, 10, 6, 6, 6))" --set "MM.ROWS_B['fmoss'] = ('ink', 12, (11, 11, 10, 10, 10, 6, 6, 6))"`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: `MM.ROWS_B['moss'] = ('ink', 12, (11, 11, 10, 10, 10, 6, 6, 6))`, `MM.ROWS_B['mossface'] = ('ink', 12, (11, 11, 10, 10, 10, 6, 6, 6))`, `MM.ROWS_B['fmoss'] = ('ink', 12, (11, 11, 10, 10, 10, 6, 6, 6))`). Result: PASS, 60 checks; shown: no green pixel in the room at the start (1 818 in the step: the moss). Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/03-dungeon`.

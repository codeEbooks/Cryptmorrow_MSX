# Cryptmorrow MSX, step 03 - variant 03b: A green energy bar

The energy bar of the HUD in green instead of red.

This folder is step 03 (`chain/03-dungeon` in this repository) with one change.

## Where

`game/assets/art.py` (the ZX game's drawings, which the MSX asset builder recolours): the role `bar`, bright red ink on black.

## Before (`game/assets/art.py`)

```python
'bar': attr(R, K, 1),
```

## After

```python
'bar': attr(G, K, 1),
```

## What you will see

The segments of the bar in the HUD's row 0 in medium green (2) instead of medium red (8).

## Allowed values and limits

The 8 colours of the ZX (with BRIGHT): `build_msx.py` turns each into a TMS9918A colour. The bar keeps its cells: four, two segments a cell.

## What else depends on it

The asset builder runs again (the HUD's slots in the three thirds). The test reads `art.py` of the folder.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_step.py --step 3 --folder variants/03-dungeon/03b-green-bar --out variants/03-dungeon/03b-green-bar/evidence --no-mutations`): every pass of the step's routes, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: none: the test reads the data of this folder). Result: PASS, 60 checks; shown: the ink of the bar's cells: medium green (2; medium red, 8, in the step). Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/03-dungeon`.

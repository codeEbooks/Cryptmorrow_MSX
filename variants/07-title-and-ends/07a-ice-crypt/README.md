# Cryptmorrow MSX, step 07 - variant 07a: Another name in the logo

The title says ICE CRYPT in the big letters of the logo instead of CRYPTMORROW.

This folder is step 07 (`chain/07-title-and-ends` in this repository) with one change.

## Where

`game/assets/build_msx.py` (`WORDS`: the word of the logo and the drips of moss under it) and `art.py` (`title_screen`, the drawing the model compares with).

## Before (`game/assets/build_msx.py`)

```python
WORDS = {'logo': ('CRYPTMORROW', 1, 'logo', 'logo2', True),
```

## After

```python
WORDS = {'logo': ('ICE CRYPT', 1, 'logo', 'logo2', True),
```

### Before (`game/assets/build_msx.py`)

```python
'drips': art.logo_drips('CRYPTMORROW', 1)}
```

### After

```python
'drips': art.logo_drips('ICE CRYPT', 1)}
```

### Before (`game/assets/art.py`)

```python
            s.at[row][c] = pal['menu']
    logo(s, 'CRYPTMORROW', 1, pal)
```

### After

```python
            s.at[row][c] = pal['menu']
    logo(s, 'ICE CRYPT', 1, pal)
```

## What you will see

ICE CRYPT in the big stone letters, centred, with its moss; the band of the crypt, the menu and the credit as before.

## Allowed values and limits

The letters of the three words of the game only (the font has C R Y P T M O W V I A G E). A word is centred from its number of characters.

## What else depends on it

The asset builder runs again (the font, the words, the drips). The test reads `art.py` and `build_msx.py` of the folder.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How it was verified

Built by its own tools (`tools/build_game.py`: the data, the lines, sjasmplus, the cartridge, pasmo) and run by the test of the step (`python tests/verify_1_0.py --step 7 --folder variants/07-title-and-ends/07a-ice-crypt --out variants/07-title-and-ends/07a-ice-crypt/evidence --only data,sound,palettes,game,defeat,shots,rooms,alone,sessions,players,systems`): every pass of the games, of the sessions and of the three players of the test of 1.0, at 50 and 60 Hz, in the bench and in openMSX, compared with the models changed in the same way (change to the models: none: the test reads the data of this folder). Result: PASS, 590 checks; shown: every title of the sessions = the model of the new title. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/07-title-and-ends`.

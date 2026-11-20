# Cryptmorrow MSX, step 05 - where it breaks: Hidden at Y = 208

The blinking explorer is hidden with Y = 208 instead of being left out of the list: 208 ends the list.

This folder is step 05 (`chain/05-combat` in this repository) with a mistake made on purpose.

## Before (`game/src/combat.asm`)

```asm
        ld a,(invulnerable)
        and 4
        ld a,1
        jr z,sc_hero
        xor a                   ; 4 passes off, 4 on
sc_hero:
        ld (hero_shown),a
        call hero_sprites
```

## After

```asm
        ld a,1
        ld (hero_shown),a
        call hero_sprites
        ld a,(invulnerable)
        and 4
        jr z,sc_shown
        ld a,208                ; hidden: off screen?
        ld (hero_sat),a
sc_shown:
```

## Symptom

While the explorer blinks after a touch, the blade and the enemies blink with it: on the frames it is hidden nothing is drawn.

## Cause

A sprite whose Y is 208 (`#D0`) ends the list for the VDP: the sprites after it are not drawn at all. The explorer is sprite 0.

## Try it

`python tools/run_game.py` in this folder builds it and opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` for 60 Hz): the arrows and SPACE play, and joystick 1 is on the keys I J K L and right Ctrl.

## How the test catches it

`python tests/verify_step.py --step 5 --folder variants/05-combat/05x-hidden-at-208 --out variants/05-combat/05x-hidden-at-208/evidence --no-mutations` fails: "eu (50 Hz) the whole game: blow, damage, enemies, sprite list = the model (pass 11310: (46, 0, 0, 0, 30, 1, 0, 2, 1, 160, 76, 0, 3, 0, 0, 0, 2, 2, 145, 87, 3, 1, 0, 0, 0, 0, 0, 0, 16, 3, 0, 0, 0, 0, 0, 75, 160, 68, 15, 86, 145, 76, 13), model (46, 0, 0, 0, 30, 0, 0, 2, 1, 160, 76, 0, 3, 0, 0, 0, 2, 2, 145, 87, 3, 1, 0, 0, 0, 0, 0, 0, 16, 3, 0, 0, 0, 0, 0, 75, 160, 68, 15, 86, 145, 76, 13))"

## Repair

Put back the lines of *Before*, or start again from `chain/05-combat`.

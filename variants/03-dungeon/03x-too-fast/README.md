# Cryptmorrow MSX, step 03 - where it breaks: Faster than the VDP

The names of the new room sent with OTIR, one every 23 T-states during the picture: the rule of 29 broken.

This folder is step 03 (`chain/03-dungeon` in this repository) with a mistake made on purpose.

## Before (`game/src/room.asm`)

```asm
pn_byte:
        outi                    ; 18 T
        jp nz,pn_byte           ; 11 T
```

## After

```asm
pn_byte:
        otir                    ; 23 T a byte
```

## Symptom

At 60 Hz, after a change of room, openMSX ends with a VRAM different from the bench's: the VDP lost writes that came too soon, and cells of the new room can be wrong. At 50 Hz the same cartridge is right.

## Cause

During the picture the TMS9918A in Screen 2 needs about 8 microseconds between two accesses to the VRAM - 29 T-states of the Z80 with the M1 wait, as much as `OUTI` and `JP NZ`. `OTIR` repeats `OUTI` by itself in 23. Outside the picture any speed is fine: at 50 Hz there are 121 lines of it, and `put_names` ends in time; at 60 Hz there are 70, and its last rows go out while the picture is drawn. A mistake that only one of the two speeds shows: the test runs both.

## Try it

`python tools/run_game.py --hz 60` in this folder builds it and opens it in openMSX at 60 Hz: walk through the rooms and look at each new one as it appears. At 50 Hz (without `--hz 60`) it plays right.

## How the test catches it

`python tests/verify_step.py --step 3 --folder variants/03-dungeon/03x-too-fast --out variants/03-dungeon/03x-too-fast/evidence --no-mutations` fails: "int (60 Hz) room 01: no VRAM access closer than 29 T in the picture, the VDP's address with interrupts off, no write to ROM ({'29T': [(4412021, 17088, 23), (4412044, 17088, 23)], 'ctrl': None, 'rom': None, 'r7': None, 'psgdi': None})"

## Repair

Put back the lines of *Before*, or start again from `chain/03-dungeon`.

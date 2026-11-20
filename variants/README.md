# Cryptmorrow MSX - guided variants and "where it breaks"

Each folder is a step of the chain (`chain/NN-name` in this repository) with one change: a guided variant to try, or a mistake made on purpose. Its README says where, before and after, what you will see, the limits, how it was verified and how to restore. `python tools/run_game.py` in a folder builds it and opens it in openMSX.

| Step | Folder | Kind | What it shows | Verified |
|---|---|---|---|---|
| 01 | `01-first-room/01a-faster-flames` | variant | The torches flicker twice as fast: a new flame every 4 frames instead of every 8. | yes |
| 01 | `01-first-room/01b-another-zone` | variant | The Moss Gate in the colours of zone C, the amber wing. One line of data. | yes |
| 02 | `02-explorer/02a-red-coat` | variant | The explorer's hat and coat in dark red instead of dark yellow: one sprite, one colour. | yes |
| 02 | `02-explorer/02b-joystick-port-2` | variant | The explorer follows the joystick in port 2 instead of port 1: one bit of PSG register 15. | yes |
| 03 | `03-dungeon/03a-autumn-moss` | variant | The moss of the atrium in yellow and red instead of three greens. | yes |
| 03 | `03-dungeon/03b-green-bar` | variant | The energy bar of the HUD in green instead of red. | yes |
| 04 | `04-objects-doors/04a-strong-potion` | variant | A potion gives back 4 segments of energy instead of 2. | yes |
| 04 | `04-objects-doors/04b-rich-treasure` | variant | A treasure is worth 500 points instead of 250. | yes |
| 05 | `05-combat/05a-light-damage` | variant | A touch takes 1 segment of energy instead of 2. | yes |
| 05 | `05-combat/05b-lazy-bats` | variant | A bat wakes only within 48 x 45 pixels of the explorer instead of 96 x 90. | yes |
| 06 | `06-sound/06a-effects-first` | variant | The game starts in SOUND FX: the effects on the PSG, no music. | yes |
| 06 | `06-sound/06b-faster-music` | variant | The theme at 150 beats a minute instead of 125: 5 frames a step instead of 6. | yes |
| 07 | `07-title-and-ends/07a-ice-crypt` | variant | The title says ICE CRYPT in the big letters of the logo instead of CRYPTMORROW. | yes |
| 07 | `07-title-and-ends/07b-short-wait` | variant | PRESS FIRE comes 50 passes after the end screen instead of 100. | yes |
| 01 | `01-first-room/01x-status-not-read` | where it breaks | The interrupt forgets to read the VDP's status: the request is never cleared. | yes |
| 02 | `02-explorer/02x-small-sprites` | where it breaks | Register 1 without the size bit: the VDP draws the sprites 8 x 8 pixels. | yes |
| 03 | `03-dungeon/03x-too-fast` | where it breaks | The names of the new room sent with OTIR, one every 23 T-states during the picture: the rule of 29 broken. | yes |
| 04 | `04-objects-doors/04x-key-stays` | where it breaks | A key opens its door and is not used up: `or` instead of `xor`. | yes |
| 05 | `05-combat/05x-hidden-at-208` | where it breaks | The blinking explorer is hidden with Y = 208 instead of being left out of the list: 208 ends the list. | yes |
| 06 | `06-sound/06x-port-a-out` | where it breaks | PSG register 7 written with bit 6 at 1: port A, the joysticks, becomes an output. | yes |
| 07 | `07-title-and-ends/07x-address-split` | where it breaks | The two bytes of a VRAM address written with the interrupt on. | yes |
| 08 | `08-complete/08x-no-enaslt` | where it breaks | The cartridge never puts its second half in page 2 (#8000-#BFFF). | yes |

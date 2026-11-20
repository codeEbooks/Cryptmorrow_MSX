# The chapters and their folders

The book builds the game in eight steps. Each chapter works on one
step of `chain/` (two or more chapters may share one); its experiments
are in `variants/`, in the folder of the same step. A variant is the
step with one change: a guided variant ("Make it yours") shows what a
value or a table does, a "Where it breaks" version makes on purpose a
mistake the chapter explains, and its test must fail.

| Chapter | Title | Step | Experiments | Tools and tests |
|---|---|---|---|---|
| 1 | Your workshop | `chain/01-first-room` |  | `tools/build_game.py`, `tools/check_lines.py`, `tools/run_game.py` |
| 2 | The Z80, the slots and the VDP | `chain/01-first-room` |  |  |
| 3 | The tile engine | `chain/01-first-room` | `01b-another-zone` | `tools/build_game.py`, `tools/run_game.py` |
| 4 | Text, torches and the frame | `chain/01-first-room` | `01a-faster-flames`, `01x-status-not-read` | `tools/run_game.py` |
| 5 | Hardware sprites | `chain/02-explorer` | `02a-red-coat`, `02x-small-sprites` | `tools/run_game.py` |
| 6 | The explorer | `chain/02-explorer` | `02b-joystick-port-2` | `tools/run_game.py` |
| 7 | The dungeon and the HUD | `chain/03-dungeon` | `03a-autumn-moss`, `03b-green-bar`, `03x-too-fast` | `tools/build_game.py` |
| 8 | Objects, doors and the portal | `chain/04-objects-doors` | `04a-strong-potion`, `04b-rich-treasure`, `04x-key-stays` | `tests/route.py` |
| 9 | The enemies | `chain/05-combat` | `05b-lazy-bats` |  |
| 10 | The blade and the damage | `chain/05-combat` | `05a-light-damage`, `05x-hidden-at-208` | `tests/sessions_1_0.py` |
| 11 | The PSG and the music | `chain/06-sound` | `06b-faster-music`, `06x-port-a-out` | `tests/psg_model.py` |
| 12 | The effects and the sound modes | `chain/06-sound` | `06a-effects-first` | `tests/psg_model.py` |
| 13 | The title and its big letters | `chain/07-title-and-ends` | `07a-ice-crypt`, `07x-address-split` | `tests/msx_states.py` |
| 14 | States, menu and end screens | `chain/07-title-and-ends` | `07b-short-wait` | `tests/sessions_0_8.py` |
| 15 | The cartridge | `chain/08-complete` | `08x-no-enaslt` |  |
| 16 | Reading and checking the game | `chain/08-complete`, `game` |  | `tools/exec_coverage.py`, `tests/openmsx_run.py`, `tests/verify_step.py`, `tests/verify_1_0.py`, `tests/msxsim.py`, `tests/coverage_cases.py`, `tools/vram2png.py` |
| 17 | Glossary and index |  |  |  |

Step 08 is the complete game, Cryptmorrow MSX 1.0, byte for byte;
`game/` holds its master source, from which `tools/make_chain.py`
makes the eight steps (`python tools/make_chain.py --assemble` writes
them again into `chain/` and builds them; `--out DIR` writes them
elsewhere). `tools/make_variants.py` makes the 22 experiments from the
steps and `tools/variants.py`, the list of their changes (`--out DIR`
elsewhere; `--test` runs their tests too).

## The experiments

| Folder | Chapter | Kind | Title | Its test |
|---|---|---|---|---|
| `variants/01-first-room/01b-another-zone` | 3 | variant | The colours of another zone | PASS |
| `variants/01-first-room/01a-faster-flames` | 4 | variant | Faster flames | PASS |
| `variants/01-first-room/01x-status-not-read` | 4 | where it breaks | The VDP status not read | FAIL, as it must |
| `variants/02-explorer/02a-red-coat` | 5 | variant | A red coat | PASS |
| `variants/02-explorer/02x-small-sprites` | 5 | where it breaks | 8 x 8 sprites | FAIL, as it must |
| `variants/02-explorer/02b-joystick-port-2` | 6 | variant | The joystick in port 2 | PASS |
| `variants/03-dungeon/03a-autumn-moss` | 7 | variant | Autumn moss | PASS |
| `variants/03-dungeon/03b-green-bar` | 7 | variant | A green energy bar | PASS |
| `variants/03-dungeon/03x-too-fast` | 7 | where it breaks | Faster than the VDP | FAIL, as it must |
| `variants/04-objects-doors/04a-strong-potion` | 8 | variant | A stronger potion | PASS |
| `variants/04-objects-doors/04b-rich-treasure` | 8 | variant | Richer treasures | PASS |
| `variants/04-objects-doors/04x-key-stays` | 8 | where it breaks | The key that stays | FAIL, as it must |
| `variants/05-combat/05b-lazy-bats` | 9 | variant | Lazy bats | PASS |
| `variants/05-combat/05a-light-damage` | 10 | variant | Lighter damage | PASS |
| `variants/05-combat/05x-hidden-at-208` | 10 | where it breaks | Hidden at Y = 208 | FAIL, as it must |
| `variants/06-sound/06b-faster-music` | 11 | variant | Faster music | PASS |
| `variants/06-sound/06x-port-a-out` | 11 | where it breaks | Port A as an output | FAIL, as it must |
| `variants/06-sound/06a-effects-first` | 12 | variant | Effects only | PASS |
| `variants/07-title-and-ends/07a-ice-crypt` | 13 | variant | Another name in the logo | PASS |
| `variants/07-title-and-ends/07x-address-split` | 13 | where it breaks | An address split by the interrupt | FAIL, as it must |
| `variants/07-title-and-ends/07b-short-wait` | 14 | variant | A shorter wait on the end screen | PASS |
| `variants/08-complete/08x-no-enaslt` | 15 | where it breaks | ENASLT forgotten | FAIL, as it must |

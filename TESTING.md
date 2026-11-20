# What was tested, and the limits

Everything here ran in emulation: in openMSX, the emulator, with its
C-BIOS, and in the test bench of the book, an MSX1 written in Python
around SkoolKit's Z80 simulator and driven by the tests in `tests/`.
Nothing was run on a real MSX. Chapter 16 of the book ("Reading and
checking the game") tells how the tests work; this page gives the
results, the versions and what the repository cannot repeat.

## The versions

| Program | Versions used |
|---|---|
| sjasmplus | 1.24.0 |
| pasmo | 0.5.3, the second assembler: the same bytes as sjasmplus |
| openMSX | 21.0, with C-BIOS 0.29: the machines `C-BIOS_MSX1_EU` (50 Hz) and `C-BIOS_MSX1` (60 Hz) |
| SkoolKit | 10.1 |
| Python | 3.13 on Linux, 3.14 on Windows; 3.10 or later, standard library only, for the build |

The book's runs were made on Linux (Ubuntu 24.04), with the programs
built from their sources: the "workspace" of the tests' reports. They
were made again on Windows, with the Windows programs of the same
versions: the tests of steps 01 to 07 complete, of step 08 its 20
cartridges, its data and its systems, the 22 variants, the figures and
the measure of the instructions run, all with the same results. Not on
macOS.

## How the game was made, and the names of the tests

Before the game, Phase 0 measured the machine with a probe, a small
cartridge of its own (`fase0/`; chapter 4 quotes one of its
measures). The game was then
made as versions 0.1 to 1.0, each tested before the next: the
"milestones" of the tests' names and comments. Version 1.0 is the
complete game. The book's eight steps were then cut from its source
(`tools/make_chain.py`; Phase D in the comments). The tests of the
milestones `tests/verify_0_1.py`, `verify_0_2.py`, `verify_0_2_1.py`,
`verify_0_3.py` and `verify_0_8.py` hold the models, the checks and the
mutations that the tests of the steps and of 1.0 use; the milestones
themselves are not part of this repository, so those files are not
meant to be run on their own.

## The results printed in the book

| Check | Result |
|---|---|
| The tests of the steps | See the table below: all PASS |
| The test of the complete game (`tests/verify_1_0.py --step 8`) | 696 checks: PASS |
| One-line faults put in on purpose (`--mutations`, in the test of step 08) | 103 of 103 stopped |
| Variants and "Where it breaks" versions | 14 PASS; 8 stopped by their test, as they must be |
| Instructions of the cartridge run by the tests | 3 145 of 3 152: the test of step 08 and the targeted cases of `tests/coverage_cases.py` (`tools/exec_coverage.py`); openMSX reached the same 3 145 |
| The figures | each of the 43 figures (80 pictures) taken twice, identical; 37 checked against the models of the tests, 5 taken in openMSX too |
| Pasmo | the same bytes as sjasmplus, in every build |

The tests of the steps:

| Step | The test | Checks | Faults stopped | Result |
|---|---|---|---|---|
| `01-first-room` | `tests/verify_step.py --step 1` | 29 | 3 | PASS |
| `02-explorer` | `tests/verify_step.py --step 2` | 34 | 3 | PASS |
| `03-dungeon` | `tests/verify_step.py --step 3` | 63 | 3 | PASS |
| `04-objects-doors` | `tests/verify_step.py --step 4` | 38 | 3 | PASS |
| `05-combat` | `tests/verify_step.py --step 5` | 71 | 3 | PASS |
| `06-sound` | `tests/verify_step.py --step 6` | 84 | 3 | PASS |
| `07-title-and-ends` | `tests/verify_1_0.py --step 7` | 688 | 97 | PASS |
| `08-complete` | `tests/verify_1_0.py --step 8` | 696 | 103 | PASS |

The master source, `game/`, builds the same 20 cartridges as step 08;
`tests/verify_1_0.py` on it, with the parts that read the sources (its
build, its data and its systems: `--only data,systems`), gave
9 checks: PASS; every other part runs the same
cartridges as the test of step 08.

The 7 instructions that no test runs are defences, for
whoever moves the enemies, the edges of a room or the cells of a zone;
chapter 16 lists them (Table 7).

## Checked again for this repository

On 17 and 18 November 2026 the repository was checked from clean copies of
this folder, on Linux, with sjasmplus 1.24.0, pasmo 0.5.3, openMSX 21.0
with C-BIOS 0.29, SkoolKit 10.1, Python 3.13.18 and Git 2.43.0
(`check_repository.py` in the book's project):

| Check | Result |
|---|---|
| `python verify.py` | the 2 258 files of `SHA256SUMS.txt` unchanged; the complete game, the 8 steps and the 22 variants built again (164 cartridges), each cartridge identical to its reference and the 20 of steps 07 and 08 to those of `chain/chain.json`; the 22 reports of the variants' tests name those cartridges; the probe of `fase0/` assembled again, identical; the release is the cartridge of step 08: PASS |
| The tests of the steps, built as the README says, with their mutations and `--reference` to `reference/reports/` | steps 01 to 06: 30, 35, 64, 39, 72, 85 checks; step 07: 690; step 08: 696: all PASS: every fact of the bench, and in steps 07 and 08 of openMSX, the same as in the book's runs; every fault put in on purpose stopped (3 in each of steps 01 to 06, 97 in step 07, 103 in step 08) |
| `tests/verify_1_0.py --only data,systems` on the master source | 9 checks: PASS |
| The bench with the C-BIOS of `fase0/cbios` (`--no-openmsx`, so that `cbios_dir` takes this copy) | steps 01, 02 and 03 with `--reference`: 26, 31 and 60 checks, every fact of the bench the same as in the book's runs; step 08, `--only data,systems`: 10 checks: all PASS |
| `tools/make_chain.py --out` another folder | the eight steps and `chain/coverage.csv` identical to `chain/` |
| `tools/make_variants.py --out` another folder | the 22 folders identical, their cartridges those of `reference/variants` |
| The listings and file names of the book | the 207 listings, each identical to its lines here; every file and folder name printed in the book (176, counted chapter by chapter) here or written by a build |
| A Git checkout | `git add` of the folder: 2 259 files, the sources with LF line ends, nothing ignored; a clone made with `core.autocrlf=true` and a `git archive` both agree with `SHA256SUMS.txt` |

Not repeated here: the tests of the variants (`tools/make_variants.py
--test`; their reports are those of the book, and `verify.py` checks
that they name the cartridges of this repository), the figures, the
measure of the instructions run, and anything on Windows or macOS.

## What the repository cannot repeat

- **The figures of the book.** Every picture of the game in the book
  is the VRAM of a program, drawn as openMSX shows it by
  `tools/vram2png.py`; the editorial tools that chose and captured
  them are not part of the repository. The tests write their own
  captures into their reports' `png/` folders.
- **The register of the instructions.** `tools/exec_coverage.py` runs
  the test of step 08 again and writes which instructions ran and
  which ports and tables they touched (`--out FILE`); the register the
  book was measured from is not here.
- **The reports of the tests of the steps.** `reference/reports/` holds
  the reports of the book's runs, without their pictures and sounds;
  running a test writes its report again, with them. The reports of the
  variants' tests, with their pictures, are in their folders'
  `evidence/`.
- **Playing by hand.** The author played the game by hand in openMSX;
  that cannot be in a repository.

## Limits

- A test compares the program with a model written in Python for this
  purpose. A model could be wrong in the same way as the program; the
  faults put in on purpose, which the tests had to stop, are there to
  make that unlikely, not impossible.
- A route is one way through the game. The routes and the sessions
  enter every room, take every object, open every door, meet every
  kind of enemy and win and lose the game, and three players that do
  not follow a plan play 20 000 passes each, but no test can try every
  timing.
- The bench is not an MSX: it starts each cartridge from the state
  C-BIOS had at INIT in openMSX, and only RSLREG and ENASLT run code of
  C-BIOS. openMSX runs the same input as the bench and must agree with
  it, pass by pass.
- `verify.py` proves that the cartridges are built byte for byte as in
  the book. After your own changes it will report differences, as it
  should; only playing and testing tell whether a change works.
- The comments of some sources were last edited for this repository,
  after the tests of the variants had run (no byte of a cartridge
  changed); the reports of the variants name the cartridges they
  tested, and `verify.py` checks that they are those of this
  repository.

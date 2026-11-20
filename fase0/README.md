# fase0: the probe and C-BIOS

Before the game was written, Phase 0 ("fase 0" in the project's own
language, hence the name of the folder) measured the machine with a
probe: a cartridge of 32 768 bytes that does the things the game does
and nothing else. Chapter 4 of the book quotes one of its measures.

- `src/probe.asm`, with `src/msx.asm` (the names of the hardware): the
  header `AB` with INIT at `#4010`; RSLREG and ENASLT, for the
  cartridge in `#8000`-`#BFFF` too; the byte `#002B` of the BIOS (50 or
  60 Hz); Screen 2 written register by register, a drawing for each
  third with a colour for each line (all 15 colours), an animated
  torch, four sprites (sprite 0 moves with the arrows or joystick 1,
  FIRE changes its colour); IM 2 with its table of 257 bytes at
  `#F000` and `JP isr` at `#F1F1`; a note of 440 Hz on the PSG; and
  `frame_ready`, where the tests stop, at the end of every frame.
- `build/probe.rom` and `build/probe.sym`: the probe as assembled for
  the tests, from the folder `build`:

  ```text
  sjasmplus --nologo --msg=war -DBROKEN=0 -DIRQMODE=0 --raw=probe.rom --sym=probe.sym ../src/probe.asm
  ```

  `verify.py` assembles it again and compares the bytes. The test of
  the palettes (`tests/verify_1_0.py`, part `palettes`; the functions
  of `tests/verify_0_8.py` and `tests/fase0_check.py`) runs it in
  openMSX on both machines: every one of the 15 colours of openMSX's
  screenshots must be the colour `tools/vram2png.py` gives it.
- `cbios/`: a copy of C-BIOS 0.29, the free BIOS that comes with
  openMSX, under its own licence (`cbios/README.md`).

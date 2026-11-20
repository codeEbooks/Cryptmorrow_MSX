# fase0/cbios: C-BIOS

C-BIOS 0.29, the free BIOS for MSX emulators, as it comes with openMSX
21.0: the same files, byte for byte, as in the `share/machines` folder
of openMSX and in its `doc/cbios.txt`.

```text
README.cbios.txt         the licence, the authors and the history
cbios_main_msx1_eu.rom   the MSX1 at 50 Hz (C-BIOS_MSX1_EU)
cbios_main_msx1.rom      the MSX1 at 60 Hz (C-BIOS_MSX1)
cbios_logo_msx1.rom      the logo they show at power on
cbios_main_msx1_jp.rom   the Japanese and Brazilian MSX1, not used
cbios_main_msx1_br.rom   by the book
```

The test bench (`tests/msxsim.py`) is an MSX1 with C-BIOS in slot 0:
RSLREG and ENASLT run its code. `cbios_dir` in `tools/msxtools.py`
takes the ROMs from beside openMSX, among its machines, when it finds
them there, and otherwise from this folder, so the tests also run where
openMSX keeps its machines elsewhere (as a Linux distribution or macOS
may install it).

C-BIOS is not part of the game and is not covered by the MIT License
of this repository. It is the work of its own authors (BouKiCHi,
Reikan, Maarten ter Huurne, Albert Beevendorp, Patrick van Arkel,
Manuel Bilderbeek, Joost Yervante Damad, Jussi Pitkänen and Eric Boon)
and is redistributed here, unchanged, under its own BSD licence, whose
text and copyright notices are in `README.cbios.txt`. Its home is
cbios.sourceforge.net.

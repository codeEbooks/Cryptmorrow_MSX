"""Build the cartridge and run it in openMSX.

Usage: python tools/run_game.py [--hz 50|60] [--no-build]
                                [--openmsx EXE]

First tools/build_game.py: the data, the assembler, the cartridge
(game/build/cryptmorrow.rom). Then openMSX starts a C-BIOS MSX1 with
the cartridge in its slot.

--hz        the machine: 50 (C-BIOS MSX1 EU, the default) or 60 Hz
            (C-BIOS MSX1).
--no-build  run the cartridge that is there.

The keyboard's arrows and SPACE play; joystick 1 is plugged in too,
on the keys I J K L and right Ctrl. Close openMSX to stop.
Standard library only.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from msxtools import find_tool  # noqa: E402

ROM = ROOT / 'game' / 'build' / 'cryptmorrow.rom'
MACHINES = {'50': 'C-BIOS_MSX1_EU', '60': 'C-BIOS_MSX1'}
JOY = ('set msxjoystick1_config {UP {{keyb I}} DOWN {{keyb K}} '
       'LEFT {{keyb J}} RIGHT {{keyb L}} A {{keyb RCTRL}} '
       'B {{keyb M}}}; plug joyporta msxjoystick1')


def main(argv=None):
    ap = argparse.ArgumentParser(description='Build and run in openMSX.')
    ap.add_argument('--hz', default='50', choices=sorted(MACHINES))
    ap.add_argument('--no-build', action='store_true')
    ap.add_argument('--openmsx')
    args = ap.parse_args(argv)
    if not args.no_build:
        import build_game
        sys.argv = [sys.argv[0]]
        if build_game.main():
            return 1
    openmsx = find_tool('openmsx', args.openmsx)
    if not openmsx:
        print('openMSX not found: put it in the PATH or use --openmsx')
        return 2
    return subprocess.call([openmsx, '-machine', MACHINES[args.hz],
                            '-cart', str(ROM), '-command', JOY])


if __name__ == '__main__':
    sys.exit(main())

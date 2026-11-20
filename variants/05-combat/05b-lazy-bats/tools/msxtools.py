"""Small helpers shared by the scripts: find the external programs
(sjasmplus, pasmo, openMSX) and C-BIOS, run them, hash bytes; read
the symbols of a build and check a cartridge.

find_tool looks in this order: the path given on the command line,
the PATH, then the portable copies unpacked (at any depth) in the
tools folder (tools/, where the Windows archives of sjasmplus,
pasmo and openMSX can be unpacked as they come), then the usual
places of an installed openMSX.
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent      # this volume
TOOLS = ROOT / 'tools'

NAMES = {
    'sjasmplus': ('sjasmplus',),
    'pasmo': ('pasmo',),
    'openmsx': ('openmsx',),
}
INSTALLED = {
    'openmsx': ['/opt/openMSX/bin/openmsx', '/usr/bin/openmsx',
                '/usr/local/bin/openmsx',
                r'C:\Program Files\openMSX\openmsx.exe',
                r'C:\Program Files (x86)\openMSX\openmsx.exe'],
}
CBIOS = {'eu': 'cbios_main_msx1_eu.rom', 'int': 'cbios_main_msx1.rom',
         'jp': 'cbios_main_msx1_jp.rom', 'br': 'cbios_main_msx1_br.rom',
         'logo': 'cbios_logo_msx1.rom'}


def find_tool(kind, explicit=None):
    if explicit:
        return explicit
    for name in NAMES[kind]:
        found = shutil.which(name)
        if found:
            return found
    if TOOLS.is_dir():
        for name in NAMES[kind]:
            hits = sorted(TOOLS.rglob(name + '.exe'))
            if hits:
                return str(hits[0])
    for path in INSTALLED.get(kind, ()):
        if os.path.exists(path):
            return path
    return None


def cbios_dir(openmsx=None):
    """The folder with the C-BIOS ROMs: next to an openMSX (its
    share/machines), else the copy in fase0/cbios (BSD licence)."""
    if openmsx:
        exe = Path(openmsx).resolve()
        for d in (exe.parent / 'share' / 'machines',
                  exe.parent.parent / 'share' / 'machines'):
            if (d / CBIOS['eu']).exists():
                return d
    d = ROOT / 'fase0' / 'cbios'
    return d if (d / CBIOS['eu']).exists() else None


def sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def run(cmd, cwd=None, timeout=None):
    """Exit code and everything the program wrote."""
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       timeout=timeout)
    return p.returncode, (p.stdout + p.stderr).strip()


def version(exe, kind):
    """The first line of what the assembler says about itself."""
    if kind == 'sjasmplus':
        code, out = run([exe, '--nologo', '--version'])
    else:
        code, out = run([exe])          # pasmo: usage, version first
    return out.splitlines()[0].strip() if out else '?'


def case_twins(sym_file):
    """Labels that differ only in case (they clash in some
    assemblers)."""
    seen = {}
    for line in open(sym_file, encoding='ascii'):
        name = line.split(':')[0].split()[0] if line.strip() else ''
        if name:
            seen.setdefault(name.lower(), set()).add(name)
    return sorted(sorted(v) for v in seen.values() if len(v) > 1)


def header_problems(rom):
    """The cartridge header: "AB", INIT in page 1 after the header,
    the other words 0."""
    out = []
    if rom[:2] != b'AB':
        out.append('the ROM does not start with "AB"')
    init = rom[2] | rom[3] << 8
    if not 0x4010 <= init < 0x8000:
        out.append(f'INIT ${init:04X} is not in page 1 after the header')
    if any(rom[4:16]):
        out.append('STATEMENT, DEVICE, TEXT or the reserved bytes '
                   'are not 0')
    return out


def read_symbols(path):
    """{name: value} of the symbols written by sjasmplus (--sym)."""
    import re
    out = {}
    for line in open(path, encoding='ascii'):
        m = re.match(r'\s*([\w.]+):?\s+EQU\s+(\S+)', line, re.I)
        if not m:
            continue
        name, val = m.groups()
        if val.lower().startswith('0x'):
            out[name] = int(val, 16)
        elif val.upper().endswith('H'):
            out[name] = int(val[:-1], 16)
        else:
            out[name] = int(val)
    return out

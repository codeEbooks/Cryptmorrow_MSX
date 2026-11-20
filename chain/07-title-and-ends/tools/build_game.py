"""Build Cryptmorrow MSX, and check what is built.

1. the data: game/assets/build_msx.py makes the graphics again in
   memory (seven files, gfx_*.asm, and gfx.json) and
   game/assets/psg_music.py the music; they must be the files in
   game/assets/generated/B (--assets writes them first);
2. lines of at most 60 characters: game/src/*.asm and the data;
3. sjasmplus: the cartridge, cryptmorrow.rom (START_ROOM = 1, the
   Moss Gate), with symbols and listing, in game/build/; any message
   but success stops the build; a raw cartridge of 32 768 bytes.
   When the game has its title (START_PLAY in start.asm), also the
   tests' cartridges, the game at once without the title
   (START_PLAY = 1) in each mode of the sound:
   cryptmorrow_play.rom (MUSIC, with listing),
   cryptmorrow_play_fx.rom (SOUND FX), cryptmorrow_play_silent.rom
   (SILENT), with symbols; and one ROM for every room (START_PLAY =
   1, START_ROOM = 0-15, MUSIC), rooms/NN.rom; the ROM of room 1 is
   cryptmorrow_play.rom;
4. the cartridge header; labels that differ only in case;
5. pasmo, if found: the same source must give the same bytes;
6. the cartridge's bytes: code, data, free; the data part by part.

The same script builds the complete game and every step of the
book's chain (tools/make_chain.py), with the files the step has.

Writes game/build/manifest.json (tool versions, sizes, SHA-256,
measures). With --reference FILE it compares every SHA-256 with
another manifest (one kept from a build you trust).

Usage: python tools/build_game.py [--assets] [--sjasmplus EXE]
                                  [--pasmo EXE] [--reference FILE]
Standard library only.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'game' / 'src'
ASSETS = ROOT / 'game' / 'assets'
GENERATED = ASSETS / 'generated'
BUILD = ROOT / 'game' / 'build'
sys.path.insert(0, str(ROOT / 'tools'))
import check_lines  # noqa: E402
from msxtools import (case_twins, find_tool,  # noqa: E402
                      header_problems, read_symbols, run, sha,
                      version)

VERSIONS = ('B',)                  # the graphics of the game
GAME_ROOM = 1                   # the Moss Gate
# the tests' cartridges: the game at once, without the title
# (START_PLAY = 1), in each mode of the sound
PLAY_ROMS = {0: 'cryptmorrow_play', 1: 'cryptmorrow_play_fx',
             2: 'cryptmorrow_play_silent'}  # MUSIC, SOUND FX, SILENT
ROOMS = range(16)
ROM_SIZE = 32768
# the data, part by part: each from its first label to the first
# label of the next part that the build has (or to data_end)
PARTS = (('gradients', 'gradients'), ('flames', 'flame_phases'),
         ('glyphs', 'glyphs_top'), ('zones', 'zone_table'),
         ('shapes', 'hero_shapes'), ('combat', 'combat_shapes'),
         ('rooms', 'room_table'), ('screens', 'band_title'),
         ('opening', 'open_cells'), ('doors', 'door_table'),
         ('music', 'note_period'))
GFX_FILES = ('gfx_zones.asm', 'gfx_explorer.asm', 'gfx_combat.asm',
             'gfx_rooms.asm', 'gfx_screens.asm', 'gfx_opening.asm',
             'gfx_doors.asm')      # build_msx.py, in this order
GENERATED_FILES = GFX_FILES + ('gfx.json', 'music.asm', 'music.json')


def assets(write, problems):
    sys.path.insert(0, str(ASSETS))
    import build_msx
    import psg_music
    lines, music = psg_music.build()
    for v in VERSIONS:
        data = build_msx.build(v)
        files = dict(build_msx.asm_parts(data))
        files.update({'gfx.json': json.dumps(data) + '\n',
                 'music.asm': '\n'.join(lines) + '\n',
                 'music.json': json.dumps(music) + '\n'})
        out = GENERATED / v
        if write:
            out.mkdir(parents=True, exist_ok=True)
            for name, text in files.items():
                (out / name).write_text(text, encoding='ascii',
                                        newline='\n')
        for name, want in files.items():
            f = out / name
            have = f.read_bytes().replace(b'\r\n', b'\n') \
                if f.exists() else b''
            if have != want.encode('ascii'):
                problems.append(f'generated/{v}/{name} is not what '
                                'build_msx.py makes now (--assets)')


def sjasm(exe, v, room, name, listing, problems, mode=0, play=1):
    out = BUILD / name
    out.parent.mkdir(parents=True, exist_ok=True)
    # forward slashes: sjasmplus for Windows warns about a
    # backslash in a file name (Phase 0)
    cmd = [exe, '--nologo', '--msg=war', f'-DSTART_ROOM={room}',
           f'-DSOUND_MODE={mode}', f'-DSTART_PLAY={play}',
           f'-i{(GENERATED / v).as_posix()}',
           f'--raw={out.as_posix()}.rom', f'--sym={out.as_posix()}.sym']
    if listing:
        cmd.append(f'--lst={out.as_posix()}.lst')
    cmd.append((SRC / 'cryptmorrow.asm').as_posix())
    code, msg = run(cmd, BUILD)
    if code or msg:
        problems.append(f'sjasmplus {name}: exit {code}: {msg}')
        return None
    rom = Path(f'{out}.rom').read_bytes()
    if len(rom) != ROM_SIZE:
        problems.append(f'{name}.rom: {len(rom)} bytes, not {ROM_SIZE}')
    problems += [f'{name}.rom: {p}' for p in header_problems(rom)]
    twins = case_twins(Path(f'{out}.sym'))
    if twins:
        problems.append(f'{name}: labels differing in case: {twins}')
    return rom


def pasmo_same(exe, v, room, name, rom, problems, mode=0, play=1):
    tmp = BUILD / 'pasmo'
    tmp.mkdir(parents=True, exist_ok=True)
    out = tmp / (Path(name).name + '.rom')
    code, msg = run([exe, '--equ', f'START_ROOM={room}', '--equ',
                     f'SOUND_MODE={mode}', '--equ', f'START_PLAY={play}',
                     '-I',
                     str(GENERATED / v), 'cryptmorrow.asm', str(out)],
                    SRC)
    if code:
        problems.append(f'pasmo {name}: exit {code}: {msg}')
        return False
    same = out.read_bytes() == rom
    if not same:
        problems.append(f'pasmo {name}: different bytes')
    out.unlink()
    return same


def measures(sym):
    code = sym['code_end'] - 0x4000
    data = sym['data_end'] - sym['code_end']
    have = sorted((sym[label], name) for name, label in PARTS
                  if label in sym)
    ends = [a for a, _ in have[1:]] + [sym['data_end']]
    parts = {name: end - a for (a, name), end in zip(have, ends)}
    if 'combat' in parts:               # the sprites' images: one part
        parts['shapes'] += parts.pop('combat')
    parts = {name: parts[name] for name, _ in PARTS if name in parts}
    return {'code': code, 'data': data,
            'free': 0xC000 - sym['data_end'], 'data_parts': parts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--assets', action='store_true')
    ap.add_argument('--sjasmplus')
    ap.add_argument('--pasmo')
    ap.add_argument('--reference')
    a = ap.parse_args()
    problems = []
    assets(a.assets, problems)
    sources = sorted(SRC.glob('*.asm'))
    if check_lines.main(sources + [GENERATED / v / n
                                   for v in VERSIONS
                                   for n in GFX_FILES +
                                   ('music.asm',)]):
        problems.append('lines longer than 60 characters')
    sj = find_tool('sjasmplus', a.sjasmplus)
    if not sj:
        print('sjasmplus not found')
        return 1
    pa = find_tool('pasmo', a.pasmo)
    tools = {'sjasmplus': version(sj, 'sjasmplus'),
             'pasmo': version(pa, 'pasmo') if pa else None}
    BUILD.mkdir(parents=True, exist_ok=True)
    roms, meas = {}, {}
    tests = 'START_PLAY' in (SRC / 'start.asm').read_text()
    for v in VERSIONS:
        name = 'cryptmorrow'
        rom = sjasm(sj, v, GAME_ROOM, name, True, problems, play=0)
        if rom is None:
            continue
        e = {'bytes': len(rom), 'sha256': sha(rom)}
        if pa:
            e['pasmo_same'] = pasmo_same(pa, v, GAME_ROOM, name, rom,
                                         problems, play=0)
        roms[name] = e
        meas[v] = measures(read_symbols(BUILD / f'{name}.sym'))
        print(f"{name}  {e['sha256'][:16]}  code {meas[v]['code']}, "
              f"data {meas[v]['data']}, free {meas[v]['free']}"
              + ('  pasmo: same' if e.get('pasmo_same') else ''))
        if not tests:
            continue
        play_rom = None
        for mode, mname in PLAY_ROMS.items():
            mrom = sjasm(sj, v, GAME_ROOM, mname, not mode, problems,
                         mode)
            if mrom is None:
                continue
            me = {'bytes': len(mrom), 'sha256': sha(mrom)}
            if pa:
                me['pasmo_same'] = pasmo_same(pa, v, GAME_ROOM, mname,
                                              mrom, problems, mode)
            roms[mname] = me
            if not mode:
                play_rom = mrom
            print(f"{mname}  {me['sha256'][:16]}"
                  + ('  pasmo: same' if me.get('pasmo_same') else ''))
        for r in ROOMS:
            rname = f'rooms/{r:02}'
            rrom = sjasm(sj, v, r, rname, False, problems)
            if rrom is None:
                continue
            re = {'bytes': len(rrom), 'sha256': sha(rrom)}
            if pa:
                re['pasmo_same'] = pasmo_same(pa, v, r, rname, rrom,
                                              problems)
            roms[rname] = re
            if r == GAME_ROOM and rrom != play_rom:
                problems.append(f'{rname}.rom is not '
                                f'{PLAY_ROMS[0]}.rom')
        print(f'  16 rooms of version {v}' +
              ('  pasmo: same' if pa and all(
                  roms.get(f'rooms/{r:02}', {}).get('pasmo_same')
                  for r in ROOMS) else ''))
    tmp = BUILD / 'pasmo'
    if tmp.is_dir() and not any(tmp.iterdir()):
        tmp.rmdir()
    manifest = {'tools': tools, 'roms': roms, 'measures': meas,
                'sources': {p.name: sha(p.read_bytes().replace(
                    b'\r\n', b'\n')) for p in sources},
                'data': {f'{v}/{n}': sha((GENERATED / v / n).read_bytes()
                                         .replace(b'\r\n', b'\n'))
                         for v in VERSIONS
                         for n in GENERATED_FILES}}
    if a.reference:
        ref = json.loads(Path(a.reference).read_text())
        for name, e in ref['roms'].items():
            if roms.get(name, {}).get('sha256') != e['sha256']:
                problems.append(f'{name}: SHA-256 differs from the '
                                'reference')
        manifest['reference'] = {'file': str(a.reference),
                                 'same': not any('reference' in p
                                                 for p in problems)}
    manifest['problems'] = problems
    (BUILD / 'manifest.json').write_text(
        json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    for p in problems:
        print('PROBLEM:', p)
    print('build:', 'FAIL' if problems else 'PASS',
          f"({tools['sjasmplus']}; pasmo: {tools['pasmo']})")
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())

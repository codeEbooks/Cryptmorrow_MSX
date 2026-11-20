"""Generate the chain of the book from the master source.

Usage: python tools/make_chain.py [--assemble] [--out DIR]
                                  [--sjasmplus EXE] [--pasmo EXE]
                                  [STEP ...]

The master is game/src: the complete game, whose comments also carry
tags that say in which steps of the chain each line exists (the method
of the series):

  {3}       the line exists from step 3 on (the same as {3-})
  {3-6}     only in steps 3 to 6;  {-6}: up to step 6
  ;|text    a line of earlier steps only, not of the complete game:
            in the steps of its tag (which must end before the last
            step) it becomes `text`
  ;{3-6}    alone on a line: the lines up to the next ";{}" take this
            range too (blocks nest; a line keeps the narrower range)

A tag is the last thing on its line, inside the comment. Since tags
live in comments, game/src assembles as it is into the complete game,
and the last step is game/src without its tags.

The files of a step are those cryptmorrow.asm includes, each as the
step sees it; a file with no line in a step is not there. The data
(game/assets/generated) are the complete game's: a step includes the
files it uses.

For each step the script writes chain/NN-name/: game/src, a copy of
game/assets (the generators and their data), the tools that build and
run it, README.md from chain/readme/NN.md. With --assemble it builds
every step with its own tools/build_game.py (the data, the lines,
sjasmplus, pasmo if found) and checks that the last step is the game
of the release, byte for byte: the cartridge and the tests'
cartridges (milestones/1.0-complete, or reference/chain in the
package). It also writes chain/chain.json (files, lines,
instructions, bytes, SHA-256 of each step) and chain/coverage.csv,
the draft register of the labels of the complete game with the step
where each first appears.

Standard library only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STEPS = {1: '01-first-room', 2: '02-explorer', 3: '03-dungeon',
         4: '04-objects-doors', 5: '05-combat', 6: '06-sound',
         7: '07-title-and-ends', 8: '08-complete'}
LAST = max(STEPS)
ROOTS = ('cryptmorrow.asm',)
TOOLS = ('build_game.py', 'check_lines.py', 'msxtools.py', 'run_game.py',
         'scr2png.py')
ASSETS_LEFT_OUT = ('__pycache__', 'build_assets.py')
APPROVED = ROOT / 'milestones' / '1.0-complete' / 'game' / 'build'
REFERENCE = ROOT / 'reference' / 'chain'          # in the package
TAG = re.compile(r'\s*\{(\d*)(-?)(\d*)\}$')
BLOCK = re.compile(r'^;\{(\d*)(-?)(\d*)\}$')
INCLUDE = re.compile(r'^\s+include "([a-z_0-9]+\.asm)"')
LINE_LIMIT = 60
DIRECTIVE = re.compile(r'^\s*(db|dw|ds|include|org|if|else|endif)\b',
                       re.I)


def parse(first, dash, last):
    low = int(first) if first else 1
    high = int(last) if last else (LAST if dash or not first else low)
    if first and not dash:
        high = LAST                     # {3}: from 3 on
    return low, high


def step_lines(text, step, name='?'):
    """The lines of one file in one step, tags removed."""
    out, blocks = [], [(1, LAST)]
    for number, line in enumerate(text.splitlines(), 1):
        where = f'{name}:{number}'
        if line == ';{}':
            if len(blocks) == 1:
                raise SystemExit(f'{where}: ;{{}} without a block')
            blocks.pop()
            continue
        block = BLOCK.match(line)
        if block:
            low, high = parse(*block.groups())
            outer = blocks[-1]
            blocks.append((max(low, outer[0]), min(high, outer[1])))
            continue
        low, high = blocks[-1]
        earlier = line.startswith(';|')
        if earlier:
            line = line[2:]
        tag = TAG.search(line)
        if tag:
            first, second = parse(*tag.groups())
            low, high = max(low, first), min(high, second)
            line = line[:tag.start()].rstrip()
            if line.endswith(';') and line.strip() != ';':
                line = line[:-1].rstrip()
        elif earlier:
            raise SystemExit(f'{where}: ;| line without a tag')
        if earlier and high >= LAST:
            raise SystemExit(f'{where}: ;| line in the last step')
        if not earlier and high < LAST:
            raise SystemExit(f'{where}: a line of the complete game'
                             ' missing from it (;| ?)')
        if re.search(r';.*\{[\d-]*\}', line):
            raise SystemExit(f'{where}: tag not at the end')
        if low > high:
            raise SystemExit(f'{where}: a range that is empty')
        if low <= step <= high:
            out.append(line)
    if len(blocks) != 1:
        raise SystemExit(f'{name}: block not closed')
    squeezed = []
    for line in out:                    # no double blank lines
        if line == '' and (not squeezed or squeezed[-1] == ''):
            continue
        squeezed.append(line)
    while squeezed and squeezed[-1] == '':
        squeezed.pop()
    return squeezed


def step_text(text, step, name='?'):
    lines = step_lines(text, step, name)
    return '\n'.join(lines) + '\n' if lines else ''


def final_text(text, name='?'):
    """A source as the complete game shows it: the last step."""
    return step_text(text, LAST, name)


def step_sources(step, source=ROOT / 'game' / 'src'):
    """{file name: text} of the files of a step."""
    files, todo = {}, list(ROOTS)
    while todo:
        name = todo.pop(0)
        if name in files or not (source / name).exists():
            continue
        text = step_text((source / name).read_text(encoding='ascii'),
                         step, name)
        if not text:
            continue
        files[name] = text
        todo += [m.group(1) for line in text.splitlines()
                 for m in [INCLUDE.match(line)] if m]
    return files


def instructions(text):
    """The lines of Z80 code: no comment, no db, dw, ds, equ,
    include, org or conditional."""
    n = 0
    for line in text.splitlines():
        code = re.sub(r'^[A-Za-z_]\w*:', '', line.split(';')[0])
        if not code.strip() or DIRECTIVE.match(code):
            continue
        if re.match(r'^\s*[A-Za-z_]\w*\s+equ\b', code, re.I):
            continue
        n += 1
    return n


def write_sources(step, target, source=ROOT / 'game' / 'src'):
    """The sources of a step into target (a game/src folder)."""
    target.mkdir(parents=True, exist_ok=True)
    files = step_sources(step, source)
    for name, text in files.items():
        (target / name).write_bytes(text.encode('ascii'))
    return files


def generate(step, out_root):
    target = out_root / STEPS[step]
    if target.exists():
        shutil.rmtree(target)
    files = write_sources(step, target / 'game' / 'src')
    shutil.copytree(ROOT / 'game' / 'assets', target / 'game' / 'assets',
                    ignore=shutil.ignore_patterns(*ASSETS_LEFT_OUT))
    (target / 'tools').mkdir()
    for name in TOOLS:
        shutil.copy2(ROOT / 'tools' / name, target / 'tools' / name)
    readme = out_root / 'readme' / f'{step:02d}.md'
    if readme.exists():
        shutil.copy2(readme, target / 'README.md')
    return target, files


def sha(data):
    return hashlib.sha256(data).hexdigest()


def assemble(target, tools=()):
    """The step built by its own tools (tools: more options for
    build_game.py, --sjasmplus EXE). Returns its facts."""
    # Python's cache (__pycache__) stays out of the step's folder
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, 'tools/build_game.py',
                             *tools], cwd=target, capture_output=True,
                            text=True, env=env)
    build = target / 'game' / 'build'
    mfile = build / 'manifest.json'
    manifest = json.loads(mfile.read_text()) if mfile.exists() else {}
    if result.returncode or manifest.get('problems', ['no manifest']):
        raise SystemExit(f'{target.name}: build failed\n{result.stdout}'
                         f'{result.stderr}')
    long = [f'{f.name}:{n}' for f in sorted((target / 'game/src').glob(
            '*.asm')) for n, line in enumerate(f.read_text().splitlines(), 1)
            if len(line.expandtabs(8)) > LINE_LIMIT]
    if long:
        raise SystemExit(f'{target.name}: lines over {LINE_LIMIT}: {long}')
    rom = (build / 'cryptmorrow.rom').read_bytes()
    return {'rom': len(rom), 'rom_sha256': sha(rom),
            'roms': {k: e['sha256'] for k, e in manifest['roms'].items()},
            'pasmo_same': all(e.get('pasmo_same', True)
                              for e in manifest['roms'].values()),
            'measures': manifest['measures']['B']}


DEFINITION = re.compile(r'^([A-Za-z_]\w*)(?::|\s+equ\b)')


def coverage(out_root):
    """chain/coverage.csv: every label and constant of the complete
    game, its file and the step where it first appears; checks that no
    label of a step is missing from the next one."""
    first, previous, rows = {}, set(), []
    for step in sorted(STEPS):
        names = {}
        for path in sorted((out_root / STEPS[step] / 'game/src').glob(
                '*.asm')):
            for number, line in enumerate(path.read_text().splitlines(), 1):
                match = DEFINITION.match(line)
                if match:
                    names.setdefault(match.group(1), (path.name, number))
        lost = previous - set(names) - SEAM_LABELS
        if lost:
            raise SystemExit(f'step {step} drops {sorted(lost)}')
        for name, (file, number) in names.items():
            first.setdefault(name, (step, file))
        previous = set(names)
        if step == LAST:
            rows = [(name, file, number) for name, (file, number)
                    in names.items()]
    lines = ['label,file,line,step,chapter']
    for name, file, number in sorted(rows, key=lambda r: (r[1], r[2])):
        lines.append(f'{name},{file},{number},{first[name][0]:02d},')
    (out_root / 'coverage.csv').write_text('\n'.join(lines) + '\n',
                                           encoding='ascii')
    return len(rows)


SEAM_LABELS = set()     # labels of earlier steps only (none so far)


def released():
    """{name: SHA-256} of the cartridges of 1.0: from the frozen copy
    of 1.0 in the project (milestones/), or, in the package, from the
    reference cartridge of step 08."""
    manifest = APPROVED / 'manifest.json'
    if manifest.exists():
        roms = json.loads(manifest.read_text())['roms']
        return {k: e['sha256'] for k, e in roms.items()}
    return {'cryptmorrow': hashlib.sha256(
        (REFERENCE / f'{STEPS[LAST]}.rom').read_bytes()).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('steps', nargs='*', type=int)
    parser.add_argument('--assemble', action='store_true')
    parser.add_argument('--out', type=Path, default=ROOT / 'chain')
    parser.add_argument('--sjasmplus')
    parser.add_argument('--pasmo')
    args = parser.parse_args(argv)
    tools = [f'--{k}={v}' for k, v in (('sjasmplus', args.sjasmplus),
                                       ('pasmo', args.pasmo)) if v]
    facts = {}
    report = args.out / 'chain.json'
    if report.exists():
        facts = json.loads(report.read_text()).get('steps', {})
    for step in args.steps or sorted(STEPS):
        if args.out != ROOT / 'chain':
            shutil.copytree(ROOT / 'chain' / 'readme', args.out / 'readme',
                            dirs_exist_ok=True)
        target, files = generate(step, args.out)
        lines = sum(text.count('\n') for text in files.values())
        info = {'folder': f'chain/{STEPS[step]}', 'files': sorted(files),
                'lines': lines,
                'instructions': sum(instructions(t)
                                    for t in files.values())}
        if args.assemble:
            info.update(assemble(target, tools))
        facts[STEPS[step]] = info
        print(f'{target.name}: {len(files)} files, {lines} lines, '
              f"{info['instructions']} instructions"
              + (f", code {info['measures']['code']}, data "
                 f"{info['measures']['data']}, free "
                 f"{info['measures']['free']} bytes"
                 if args.assemble else ''))
    problems = []
    last = facts.get(STEPS[LAST], {})
    if args.assemble and 'roms' in last:
        approved = released()
        for name, want in sorted(approved.items()):
            if last['roms'].get(name) != want:
                problems.append(f'step {LAST:02d}: {name}.rom is not '
                                'the approved one')
        print(f'step {LAST:02d} = 1.0 ({len(approved)} cartridges): '
              f'{"FAIL" if problems else "PASS"}')
    if not args.steps:
        print(f'coverage.csv: {coverage(args.out)} labels')
    report.write_text(json.dumps({'steps': facts, 'problems': problems},
                                 indent=1) + '\n', encoding='ascii')
    for p in problems:
        print('PROBLEM:', p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())

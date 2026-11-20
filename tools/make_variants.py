"""Build, prove and describe the guided variants and the "Where it
breaks" versions of the chain of the book (tools/variants.py; Phase D,
D.3).

Usage: python tools/make_variants.py [--test] [--readme] [--out DIR]
           [--sjasmplus EXE] [--pasmo EXE] [--openmsx EXE]
           [--no-openmsx] [--no-build] [ID ...]

For each one (all, or the IDs given):
1. OUT/NN-name/ID/ = chain/NN-name/ with the edits of variants.py
   (OUT: variants/); built by the step's own tools/build_game.py
   --assets: the data again (a change of a room, a colour, a word or
   the music reaches the data), the lines, sjasmplus, the cartridge
   (from step 07 the tests' cartridges and the 16 rooms too), pasmo if
   found.
2. --test: the step's own test on the folder (tests/verify_step.py
   --step N --folder ... --no-mutations: the mutations of D.2 prove
   the step, not the variant; for steps 07 and 08 the test of 1.0,
   tests/verify_1_0.py --step N --folder ..., without its mutations:
   they prove the game, not the variant). A variant runs it with the
   same change in the models (--set) and on its own route if it has
   one (--route), and must PASS with the facts of `expect`; a break
   runs it with the models unchanged and must FAIL, the first failed
   check matching `fails`; its picture is the first PNG of the report
   whose name starts with `shot`. Reports and pictures in the
   folder's evidence/.
3. README.md in the folder: where, before and after, what you see,
   limits, what depends on it, how it was verified, how to restore.
Writes OUT/variants.json with every result and the index
OUT/README.md. --readme only writes the READMEs again (from
variants.json). --no-build tests the folders as they are (a copy of
the project where sjasmplus is missing: steps 01-02 and 04-06, since
the tests of 03, 07 and 08 assemble).

From Cryptmorrow ZX (tools/make_variants.py), brought to the MSX: the
cartridge, openMSX, the reports of tests/verify_step.py and
verify_1_0.py. Standard library.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import make_chain                               # noqa: E402
from variants import BREAKS, VARIANTS           # noqa: E402
from msxtools import find_tool                  # noqa: E402

LANGUAGE = {'.asm': 'asm', '.py': 'python', '.txt': 'text'}
OUT = ROOT / 'variants'
# the parts of the test of 1.0 a variant of step 07 or 08 runs: all but
# the mutations
PARTS_1_0 = ('data,sound,palettes,game,defeat,shots,rooms,alone,'
             'sessions,players,systems')
TRY = {
    'default': '`python tools/run_game.py` in this folder builds it and '
               'opens it in openMSX on a C-BIOS MSX1 at 50 Hz (`--hz 60` '
               'for 60 Hz): the arrows and SPACE play, and joystick 1 is '
               'on the keys I J K L and right Ctrl.',
    '02b-joystick-port-2': '`python tools/run_game.py` in this folder '
                           'builds it and opens it in openMSX; then, in '
                           'openMSX\'s console (F10), `unplug joyporta` '
                           'and `plug joyportb msxjoystick1`: the keys I '
                           'J K L move the stick of port 2.',
    '03x-too-fast': '`python tools/run_game.py --hz 60` in this folder '
                    'builds it and opens it in openMSX at 60 Hz: walk '
                    'through the rooms and look at each new one as it '
                    'appears. At 50 Hz (without `--hz 60`) it plays '
                    'right.',
    '06x-port-a-out': '`python tools/run_game.py` in this folder builds '
                      'it and opens it in openMSX: the game plays as '
                      'before (openMSX\'s C-BIOS machines keep port A an '
                      'input); the test sees register 7.',
}


def step_name(step):
    return make_chain.STEPS[step]


def folder(spec, out=OUT):
    return out / step_name(spec['step']) / spec['id']


def rel(path):
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def build(spec, tools, out=OUT):
    source = ROOT / 'chain' / step_name(spec['step'])
    target = folder(spec, out)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(
        '__pycache__', 'build', 'evidence'))
    for file, old, new in spec['edits']:
        path = target / file
        text = path.read_text(encoding='utf-8')
        if text.count(old) != 1:
            raise SystemExit(f"{spec['id']}: {file}: the old text is there "
                             f'{text.count(old)} times')
        path.write_text(text.replace(old, new), encoding='utf-8',
                        newline='\n')
    facts = make_chain.assemble(target, ['--assets'] + list(tools))
    for junk in target.rglob('__pycache__'):
        shutil.rmtree(junk)
    return {k: facts[k] for k in ('rom', 'rom_sha256', 'pasmo_same')}


def model_options(spec, variant):
    options = []
    for statement in spec.get('model', []) if variant else []:
        options += ['--set', statement]
    if variant and spec.get('route'):
        options += ['--route', spec['route']]
    return options


def test_command(spec, variant, out=OUT, tools=None):
    target = folder(spec, out)
    step = spec['step']
    if step <= 6:
        command = [sys.executable, str(ROOT / 'tests' / 'verify_step.py'),
                   '--step', str(step), '--folder', str(target),
                   '--out', str(target / 'evidence'), '--no-mutations']
    else:
        command = [sys.executable, str(ROOT / 'tests' / 'verify_1_0.py'),
                   '--step', str(step), '--folder', str(target),
                   '--out', str(target / 'evidence'),
                   '--only', PARTS_1_0]
    command += model_options(spec, variant)
    for k, v in (tools or {}).items():
        if v:
            command += [f'--{k}', v] if v is not True else [f'--{k}']
    return command


def display(spec, variant):
    """The test's command line as the README shows it."""
    words = []
    for word in test_command(spec, variant)[1:]:
        if Path(word).is_absolute():
            word = rel(word)
        words.append(f'"{word}"' if ' ' in word or ';' in word else word)
    return 'python ' + ' '.join(words)


def report_of(spec, out=OUT):
    evidence = folder(spec, out) / 'evidence'
    name = 'verify_1_0.json' if spec['step'] >= 7 else 'verify_step.json'
    report = json.loads((evidence / name).read_text())
    report.setdefault('result', 'FAIL' if report['failed'] else 'PASS')
    return report


def picture_of(spec, evidence):
    if not spec.get('shot'):
        return None
    found = sorted((evidence / 'png').glob(spec['shot'] + '*.png'))
    return found[0].name if found else None


def test(spec, out=OUT, tools=None):
    variant = spec['kind'] == 'variant'
    target = folder(spec, out)
    evidence = target / 'evidence'
    if evidence.exists():
        shutil.rmtree(evidence)
    result = subprocess.run(test_command(spec, variant, out, tools),
                            cwd=ROOT, capture_output=True, text=True,
                            timeout=14400)
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'test.log').write_text(result.stdout + result.stderr,
                                       encoding='utf-8', newline='\n')
    try:
        report = report_of(spec, out)
    except (OSError, ValueError):
        return {'command': display(spec, variant), 'result': 'NO REPORT',
                'message': (result.stderr or result.stdout)[-300:],
                'proved': False}
    failed = [c for c in report['checks'] if not c['pass']]
    message = ''
    if failed:
        message = failed[0]['check'] + (f" ({failed[0]['detail']})"
                                        if failed[0]['detail'] else '')
    outcome = {'command': display(spec, variant),
               'result': report['result'], 'message': message[:400],
               'checks': len(report['checks']),
               'failed': len(failed)}
    if variant:
        facts = []
        for text, expression in spec['expect']:
            try:
                ok = bool(eval(expression, {'r': report}))
            except (KeyError, IndexError, TypeError, ValueError):
                ok = False
            facts.append({'fact': text, 'ok': ok})
        outcome['facts'] = facts
        outcome['proved'] = result.returncode == 0 and \
            report['result'] == 'PASS' and all(f['ok'] for f in facts)
    else:
        outcome['proved'] = result.returncode == 1 and \
            report['result'] == 'FAIL' and \
            bool(re.search(spec['fails'], message))
        if spec.get('shot'):
            outcome['picture'] = picture_of(spec, evidence)
            outcome['proved'] &= outcome['picture'] is not None
    return outcome


def block(file, text):
    language = LANGUAGE.get(Path(file).suffix, 'text')
    return f"```{language}\n{text.rstrip(chr(10))}\n```"


def readme(spec, outcome, out=OUT):
    step = step_name(spec['step'])
    number = f"{spec['step']:02d}"
    variant = spec['kind'] == 'variant'
    lines = []
    if variant:
        lines += [f'# Cryptmorrow MSX, step {number} - variant '
                  f"{spec['id'][:3]}: {spec['title']}", '',
                  spec['summary'], '',
                  f'This folder is step {number} (`chain/{step}` in this '
                  'repository) with one change.', '', '## Where', '',
                  spec['where'], '']
    else:
        lines += [f'# Cryptmorrow MSX, step {number} - where it breaks: '
                  f"{spec['title']}", '', spec['summary'], '',
                  f'This folder is step {number} (`chain/{step}` in this '
                  'repository) with a mistake made on purpose.', '']
    for n, (file, old, new) in enumerate(spec['edits']):
        head = '##' if not n else '###'
        lines += [f'{head} Before (`{file}`)', '', block(file, old), '',
                  f'{head} After', '',
                  block(file, new) if new else '(the line removed)', '']
    if variant:
        lines += ['## What you will see', '', spec['see'], '',
                  '## Allowed values and limits', '', spec['limits'], '',
                  '## What else depends on it', '', spec['depends'], '']
    else:
        lines += ['## Symptom', '', spec['symptom'], '', '## Cause', '',
                  spec['cause'], '']
    lines += ['## Try it', '', TRY.get(spec['id'], TRY['default']), '']
    if outcome:
        if variant:
            model = ', '.join(f'`{m}`' for m in spec.get('model', [])) \
                or 'none: the test reads the data of this folder'
            shown = outcome.get('facts', [])
            facts = '; '.join(f['fact'] for f in shown)
            routes = ('every pass of the step\'s routes' if
                      not spec.get('route') else
                      f"every pass of a route of its own (`{spec['route']}`)"
                      ) if spec['step'] < 7 else \
                'every pass of the games, of the sessions and of the ' \
                'three players of the test of 1.0'
            lines += ['## How it was verified', '',
                      'Built by its own tools (`tools/build_game.py`: the '
                      'data, the lines, sjasmplus, the cartridge, pasmo) '
                      'and run by the test of the step '
                      f"(`{outcome['command']}`): {routes}, at 50 and 60 "
                      'Hz, in the bench and in openMSX, compared with '
                      'the models changed in the same way (change to the '
                      f"models: {model}). Result: {outcome['result']}, "
                      f"{outcome['checks']} checks; shown: {facts}. "
                      'Report in `evidence/`.', '']
        else:
            lines += ['## How the test catches it', '',
                      f"`{outcome['command']}` fails: "
                      f"\"{outcome['message']}\"", '']
            if outcome.get('picture'):
                lines += ['Picture: '
                          f"`evidence/png/{outcome['picture']}`.", '']
    lines += ['## Restore' if variant else '## Repair', '',
              'Put back the lines of *Before*, or start again from '
              f'`chain/{step}`.', '']
    (folder(spec, out) / 'README.md').write_text(
        '\n'.join(lines), encoding='utf-8', newline='\n')


def index(summary, out=OUT):
    """OUT/README.md: every variant and break, by step."""
    lines = ['# Cryptmorrow MSX - guided variants and "where it breaks"',
             '',
             'Each folder is a step of the chain (`chain/NN-name` in this '
             'repository) with one change: a guided variant to try, or a '
             'mistake made on purpose. Its README says where, before and '
             'after, what you will see, the limits, how it was verified '
             'and how to restore. `python tools/run_game.py` in a folder '
             'builds it and opens it in openMSX.', '',
             '| Step | Folder | Kind | What it shows | Verified |',
             '|---|---|---|---|---|']
    for spec in VARIANTS + BREAKS:
        outcome = summary.get(spec['id'], {}).get('outcome')
        verified = 'not yet' if not outcome else (
            'yes' if outcome['proved'] else 'NO')
        kind = 'variant' if spec['kind'] == 'variant' else \
            'where it breaks'
        name = f"{step_name(spec['step'])}/{spec['id']}"
        lines.append(f"| {spec['step']:02d} | `{name}` | {kind} | "
                     f"{spec['summary']} | {verified} |")
    (out / 'README.md').write_text('\n'.join(lines) + '\n',
                                   encoding='utf-8', newline='\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('ids', nargs='*')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--readme', action='store_true')
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--sjasmplus')
    parser.add_argument('--pasmo')
    parser.add_argument('--openmsx')
    parser.add_argument('--no-openmsx', action='store_true')
    parser.add_argument('--no-build', action='store_true')
    args = parser.parse_args(argv)
    out = args.out.resolve()
    known = {s['id'] for s in VARIANTS + BREAKS}
    for i in args.ids:
        if i not in known:
            raise SystemExit(f'{i}: not in tools/variants.py')
    build_tools = [f'--{k}={v}' for k, v in (('sjasmplus', args.sjasmplus),
                                             ('pasmo', args.pasmo)) if v]
    test_tools = {'sjasmplus': args.sjasmplus or find_tool('sjasmplus')}
    if args.no_openmsx:
        test_tools['no-openmsx'] = True
    elif args.openmsx:
        test_tools['openmsx'] = args.openmsx
    summary_path = out / 'variants.json'
    summary = json.loads(summary_path.read_text()) if \
        summary_path.exists() else {}
    for spec in VARIANTS + BREAKS:
        if args.ids and spec['id'] not in args.ids:
            continue
        entry = summary.get(spec['id'], {})
        if args.readme:
            readme(spec, entry.get('outcome'), out)
            continue
        if not args.no_build:
            entry.update(step=spec['step'], kind=spec['kind'],
                         title=spec['title'],
                         folder=f"variants/{step_name(spec['step'])}/"
                                f"{spec['id']}",
                         **build(spec, build_tools, out))
            print(f"{spec['id']}: built, {entry['rom']} bytes",
                  flush=True)
        outcome = entry.get('outcome')
        if args.test:
            outcome = test(spec, out, test_tools)
            entry['outcome'] = outcome
            print(f"{spec['id']}: "
                  f"{'PROVED' if outcome['proved'] else 'NOT PROVED'} "
                  f"({outcome['result']}) {outcome['message'][:150]}",
                  flush=True)
        readme(spec, outcome, out)
        if summary_path.exists():     # another run may have written
            summary = json.loads(summary_path.read_text())
        summary[spec['id']] = entry
        out.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=1) + '\n',
                                encoding='utf-8', newline='\n')
    index(summary, out)
    done = [e for e in summary.values() if e.get('outcome', {}).get(
        'proved')]
    print(f'{len(done)} of {len(summary)} proved')
    return 0 if not args.test or len(done) == len(summary) else 1


if __name__ == '__main__':
    sys.exit(main())

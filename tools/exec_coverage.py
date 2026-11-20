"""Which instructions of the cartridges ran while a test of the book
runs, measured two ways (Phase D, D.5):

  the bench    tests/msxsim.py: the map of the instructions executed
               (exec_map, every address the program counter took) is
               on in every MSX the test makes; each MSX is filed under
               its cartridge (by its SHA-256: the cartridge, the three
               tests' cartridges, the 16 rooms) and under the part of
               the test that made it;
  openMSX      in every openMSX run of the test a breakpoint "once" on
               every address of the cartridge's code (#4010 to
               code_end): the addresses openMSX reached. Nothing else
               changes in the run (the script of tests/openmsx_run.py
               gets these lines, and writes the addresses at its end).

Usage: python tools/exec_coverage.py [--root DIR] [--out FILE]
           [--openmsx-out FILE] [--what TEXT] [SCRIPT ARGS...]

With no SCRIPT: the test of 1.0 on the final program, the build as
delivered (no sjasmplus needed, nothing written in chain/), every part
but the mutations (they change the sources):

    tests/verify_1_0.py --step 8 --only data,sound,palettes,game,
        defeat,shots,rooms,alone,sessions,players,systems

The script runs in this process, as `python SCRIPT ARGS` would. Each
MSX of the bench is filed under the part of tests/verify_1_0.py that
made it (the name given to part() in main()), or "main".

Writes FILE (default editorial/coverage/execution.json): the folder of
the program (--root, default chain/08-complete) with the SHA-256 of
its 20 cartridges (tools/make_coverage.py uses a measure only for the
same bytes), the script and its exit code, the frames run, for each
cartridge the addresses executed from #4000 to #BFFF, those of each
part, the ports read and written (with the address of the
instruction), and what each instruction did to the VDP: a register
written (R0-R7), the status read, a table of the VRAM reached (the
address set or the data read or written: patterns, names, sprite
attributes, colours, sprite shapes). And, if openMSX ran,
--openmsx-out (default: FILE with -openmsx before .json): every
openMSX run with its cartridge, part and addresses reached; for the runs of the
sessions (tests/sessions_1_0.py) the bench's run of the same session
beside it, which must have executed the same addresses; for every run,
the addresses must be among those the bench executed on that cartridge
in that part. The files are the same every time the test is the same
(no date, no times).

Standard library and SkoolKit.
"""
import argparse
import hashlib
import json
import os
import runpy
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import msxsim  # noqa: E402
import openmsx_run  # noqa: E402

PARTS = 'data,sound,palettes,game,defeat,shots,rooms,alone,sessions,' \
    'players,systems'
DEFAULT = ['tests/verify_1_0.py', '--step', '8', '--only', PARTS]
CODE = 0x4010                    # after the cartridge's header
CART_LO, CART_HI = 0x4000, 0xC000
COVER_TCL = r'''
set ::hit {{}}
for {{set a LO}} {{$a < HI}} {{incr a}} {{
  debug breakpoint create -address $a -once true -command "lappend ::hit $a"
}}
proc cover_dump {{}} {{
  set f [open [file join $::out cover.txt] w]
  puts $f $::hit
  close $f
}}
'''     # braces doubled: tests/openmsx_run.py formats the whole script


# the VRAM as the game sets the VDP up (vdp.asm: Screen 2)
TABLES = ((0x0000, 'VRAM patterns'), (0x1800, 'VRAM names'),
          (0x1B00, 'VRAM sprite attributes'), (0x1B80, 'VRAM free'),
          (0x2000, 'VRAM colours'), (0x3800, 'VRAM sprite shapes'))


def table(address):
    """The table of the VRAM an address is in."""
    name = TABLES[0][1]
    for start, what in TABLES:
        if address >= start:
            name = what
    return name


def sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


class Spy:
    """What the bench and openMSX did."""

    def __init__(self, script, names):
        self.script = os.path.normcase(str(Path(script).resolve()))
        self.names = names          # sha -> name of the cartridge
        self.machines = []          # one record per MSX
        self.ports = {}             # (cart, pc, direction, port) -> n
        self.vdp = {}               # (cart, pc, register or table) -> n
        self.runs = []              # the openMSX runs
        self.walks = {}             # id(script) -> the session's MSX
        self.session = None         # the bench's MSX of this session

    def part(self):
        """The part of main() of the script that is running now."""
        frame = sys._getframe(2)
        while frame is not None:
            code = frame.f_code
            if os.path.normcase(code.co_filename) == self.script:
                if code.co_name == 'part' and 'name' in frame.f_locals:
                    return frame.f_locals['name']
                if code.co_name == 'main':
                    return 'main'
            frame = frame.f_back
        return '(outside main)'

    def add_vdp(self, cov, pc, what):
        key = (cov['cart'], pc, what)
        self.vdp[key] = self.vdp.get(key, 0) + 1

    def name(self, data):
        h = sha(data)
        return self.names.get(h, f'other {h[:16]}')


def install(spy):
    init = msxsim.MSX.__init__
    run_to = msxsim.MSX.run_to
    read_port = msxsim.MSX.read_port
    write_port = msxsim.MSX.write_port

    def spied_init(self, cart, *args, **kw):
        init(self, cart, *args, **kw)
        self.exec_map = set()
        self.cov = {'cart': spy.name(cart), 'part': spy.part(),
                    'map': self.exec_map, 'tstates': 0, 'runs': 0,
                    'frame_t': self.vdp.frame_t}
        spy.machines.append(self.cov)

    def spied_run_to(self, stop, max_t=None):
        t0 = self.regs[msxsim.T_]
        try:
            return run_to(self, stop, max_t)
        finally:
            cov = getattr(self, 'cov', None)
            if cov is not None:
                cov['tstates'] += self.regs[msxsim.T_] - t0
                cov['runs'] += 1

    def spied_read(self, registers, port):
        cov = getattr(self, 'cov', None)
        if cov is not None:
            key = (cov['cart'], self.pc_insn, 'in', port & 0xFF)
            spy.ports[key] = spy.ports.get(key, 0) + 1
            if port & 0xFF == 0x98:
                spy.add_vdp(cov, self.pc_insn, table(self.vdp.pointer))
            elif port & 0xFF == 0x99:
                spy.add_vdp(cov, self.pc_insn, 'status')
        return read_port(self, registers, port)

    def spied_write(self, registers, port, value, *rest):
        cov = getattr(self, 'cov', None)
        if cov is not None:
            p = port & 0xFF
            key = (cov['cart'], self.pc_insn, 'out', p)
            spy.ports[key] = spy.ports.get(key, 0) + 1
            vdp = self.vdp
            if p == 0x98:
                spy.add_vdp(cov, self.pc_insn, table(vdp.pointer))
            elif p == 0x99 and vdp.latch_full:
                spy.add_vdp(cov, self.pc_insn,
                            f'R{value & 7}' if value & 0x80 else
                            table((value << 8 | vdp.latch) & 0x3FFF))
        return write_port(self, registers, port, value, *rest)

    msxsim.MSX.__init__ = spied_init
    msxsim.MSX.run_to = spied_run_to
    msxsim.MSX.read_port = spied_read
    msxsim.MSX.write_port = spied_write

    # openMSX: the breakpoints, in every run
    template = openmsx_run.TCL
    run = openmsx_run.run
    anchor = '{marks}\n'
    ends = '{stop}close $::fr; close $::ev; exit'
    if template.count(anchor) != 1 or template.count(ends) != 2:
        raise SystemExit('tests/openmsx_run.py: its script changed, the '
                         'breakpoints have no place')

    def spied_run(openmsx, rom_path, machine, sym, frames, out, *a, **kw):
        hi = sym.get('code_end', CART_HI)
        openmsx_run.TCL = template.replace(
            anchor, COVER_TCL.replace('LO', str(CODE)).replace(
                'HI', str(hi)) + anchor).replace(
            ends, 'cover_dump; ' + ends)
        part = spy.part()
        try:
            result = run(openmsx, rom_path, machine, sym, frames, out,
                         *a, **kw)
        finally:
            openmsx_run.TCL = template
        cover = Path(out) / 'cover.txt'
        hits = sorted(int(x) for x in cover.read_text().split()) \
            if cover.exists() else None
        bench = spy.session
        spy.session = None
        spy.runs.append({'part': part,
                         'cart': spy.name(Path(rom_path).read_bytes()),
                         'machine': machine, 'run': Path(out).name,
                         'frames': frames, 'hits': hits,
                         'bench': bench})
        return result
    openmsx_run.run = spied_run

    # the sessions: the bench's MSX of the session that openMSX plays
    import sessions_1_0 as S1
    walk, emu = S1.walk, S1.emu

    def spied_walk(V, rom, sym, state, cb, script, *a, **kw):
        result = walk(V, rom, sym, state, cb, script, *a, **kw)
        old = spy.walks.get(id(script))
        if old is None or old[0] is not script:     # the first walk
            spy.walks[id(script)] = (script, result[0].cov)
        return result

    def spied_emu(V, openmsx, sym, mname, script, rd, *a, **kw):
        old = spy.walks.get(id(script))
        spy.session = old[1] if old and old[0] is script else None
        return emu(V, openmsx, sym, mname, script, rd, *a, **kw)
    S1.walk, S1.emu = spied_walk, spied_emu


def cart_names(root):
    """{SHA-256: name} of the cartridges of the program's build."""
    manifest = json.loads((root / 'game' / 'build' / 'manifest.json')
                          .read_text())
    out = {}
    for name, entry in manifest['roms'].items():
        out.setdefault(entry['sha256'], name)   # rooms/01 = the play ROM
    return out


def in_cart(addresses):
    return sorted(a for a in addresses if CART_LO <= a < CART_HI)


def one_line_lists(report, lists):
    """JSON with each long list of numbers on one line."""
    text = json.dumps(report, indent=1)[:-2]
    for key, value in lists.items():
        text += f',\n "{key}": {{\n' + ',\n'.join(
            f'  {json.dumps(k)}: ' + (json.dumps(v) if isinstance(v, list)
                                      else '{' + ', '.join(
                                          f'{json.dumps(kk)}: '
                                          f'{json.dumps(vv)}'
                                          for kk, vv in v.items()) + '}')
            for k, v in value.items()) + '\n }'
    text += '\n}\n'
    json.loads(text)
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default='chain/08-complete',
                    help='the folder of the program measured')
    ap.add_argument('--out', default='editorial/coverage/execution.json')
    ap.add_argument('--openmsx-out')
    ap.add_argument('--what', default='',
                    help='what the run is for (in Italian, for the '
                         'register)')
    ap.add_argument('command', nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    command = args.command or list(DEFAULT)
    script = ROOT / command[0]
    work = Path(tempfile.mkdtemp(prefix='exec_cov_'))
    extra = [] if '--out' in command else ['--out', str(work)]
    root = ROOT / args.root
    build = root / 'game' / 'build'
    names = cart_names(root)
    before = {n: sha((build / f'{n}.rom').read_bytes())
              for n in names.values()}
    spy = Spy(script, names)
    install(spy)
    argv0 = sys.argv
    sys.argv = [str(script), *command[1:], *extra]
    t0 = time.time()
    try:
        runpy.run_path(str(script), run_name='__main__')
        code = 0
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is
                                                       None else 1)
    finally:
        sys.argv = argv0
        shutil.rmtree(work, ignore_errors=True)     # the test's report
    after = {n: sha((build / f'{n}.rom').read_bytes())
             for n in names.values()}
    if after != before:
        raise SystemExit(f'{args.root}: the build changed during the run')
    carts, parts = {}, {}
    for m in spy.machines:
        c = carts.setdefault(m['cart'], {'machines': 0, 'frames': 0.0,
                                         'runs': 0, 'addresses': set()})
        c['machines'] += 1
        c['frames'] += m['tstates'] / m['frame_t']
        c['runs'] += m['runs']
        c['addresses'] |= m['map']
        p = parts.setdefault(m['part'], {})
        pc = p.setdefault(m['cart'], {'machines': 0, 'frames': 0.0,
                                      'addresses': set()})
        pc['machines'] += 1
        pc['frames'] += m['tstates'] / m['frame_t']
        pc['addresses'] |= m['map']
    order = sorted(carts, key=lambda n: (n.startswith('other'), n))
    report = {
        'root': args.root, 'program': before,
        'script': command[0], 'args': command[1:],
        'what': args.what, 'exit': code,
        'machines': len(spy.machines),
        'frames': round(sum(c['frames'] for c in carts.values())),
        'runs': sum(c['runs'] for c in carts.values()),
        'cartridges': [{'cartridge': n, 'machines': carts[n]['machines'],
                        'frames': round(carts[n]['frames']),
                        'runs': carts[n]['runs'],
                        'executed': len(in_cart(carts[n]['addresses']))}
                       for n in order],
        'sections': [{'section': s, 'cartridges': [
            {'cartridge': n, 'machines': v['machines'],
             'frames': round(v['frames']),
             'executed': len(in_cart(v['addresses']))}
            for n, v in sorted(p.items())]}
            for s, p in sorted(parts.items())],
        'ports': [{'cartridge': c, 'pc': pc, 'direction': d, 'port': port,
                   'count': n}
                  for (c, pc, d, port), n in sorted(spy.ports.items())
                  if CART_LO <= pc < CART_HI],
        'vdp': [{'cartridge': c, 'pc': pc, 'what': w, 'count': n}
                for (c, pc, w), n in sorted(spy.vdp.items())
                if CART_LO <= pc < CART_HI],
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(one_line_lists(report, {
        'executed_addresses': {n: in_cart(carts[n]['addresses'])
                               for n in order},
        'section_addresses': {s: {n: in_cart(v['addresses'])
                                  for n, v in sorted(p.items())}
                              for s, p in sorted(parts.items())}}),
        encoding='ascii', newline='\n')
    print(f"{args.root}: {len(spy.machines)} MSX in the bench, "
          f"{report['frames']} frames; " + ', '.join(
              f"{c['cartridge']} {c['executed']}"
              for c in report['cartridges'][:4]) +
          f"...; exit {code}, {round(time.time() - t0)} s -> {args.out}")
    if spy.runs:
        opath = ROOT / (args.openmsx_out or
                        args.out.replace('.json', '-openmsx.json'))
        write_openmsx(spy, parts, report, opath)
    return 0 if code == 0 else 1


def write_openmsx(spy, parts, bench, path):
    """The openMSX runs, each beside the bench."""
    runs, ok, union = [], True, {}
    for r in spy.runs:
        entry = {k: r[k] for k in ('part', 'cart', 'machine', 'run',
                                   'frames')}
        if r['hits'] is None:
            entry.update(reached=None, within_bench=False)
            ok = False
            runs.append(entry)
            continue
        hits = set(r['hits'])
        entry['reached'] = len(hits)
        mine = parts.get(r['part'], {}).get(r['cart'])
        known = not r['cart'].startswith('other')
        outside = sorted(hits - mine['addresses']) if mine else \
            sorted(hits)
        entry['within_bench'] = not outside if known else None
        if known:
            ok &= not outside
            union.setdefault(r['cart'], set()).update(hits)
        if outside:
            entry['outside_bench'] = outside[:20]
        if r['bench'] is not None:
            b = set(in_cart(r['bench']['map']))
            b = {a for a in b if a >= CODE}
            entry['session'] = {
                'bench_executed': len(b),
                'same': hits == b,
                'only_bench': sorted(b - hits)[:20],
                'only_openmsx': sorted(hits - b)[:20]}
            ok &= hits == b
        runs.append(entry)
    sessions = [r for r in runs if 'session' in r]
    report = {'root': bench['root'], 'program': bench['program'],
              'script': bench['script'], 'args': bench['args'],
              'runs': runs,
              'sessions_same': sum(1 for r in sessions
                                   if r['session']['same']),
              'sessions': len(sessions),
              'result': 'PASS' if ok else 'FAIL'}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(one_line_lists(report, {
        'reached_addresses': {n: sorted(v) for n, v in
                              sorted(union.items())}}),
        encoding='ascii', newline='\n')
    print(f"openMSX: {len(runs)} runs, {report['sessions_same']} of "
          f"{len(sessions)} sessions = the bench, every run within the "
          f"bench: {report['result']} -> {path}")


if __name__ == '__main__':
    sys.exit(main())

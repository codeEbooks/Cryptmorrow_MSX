"""Cryptmorrow MSX 1.0 - the complete game: the criteria of Phase C
(METODO section 10, Cryptmorrow ZX 1.0).

The cartridge of 1.0 is the cartridge of milestone 0.8, byte for
byte: only the header of cryptmorrow.asm says 1.0. This test runs
everything of tests/verify_0_8.py on it, but its sessions, and adds:

  build     the 20 ROMs (the cartridge, the three tests' cartridges,
            the 16 rooms) = those of milestone 0.8 (their SHA-256)
  alone     GAME OVER without any help, on the tests' cartridges in
            the three modes, 50 and 60 Hz: from full energy, out of
            the Moss Gate to the south, down into the row of the
            skeleton of the Crossroads, still: four touches; every
            pass = the world model (milestone 0.8 put energy 2 in RAM)
  sessions  tests/sessions_1_0.py: the long session with the keyboard
            alone (VICTORY, two GAME OVER without help), the short one
            with the joystick alone (and the RAM filled at random),
            three players that are not a plan (tests/bot.py, 20 000
            passes each); every pass = the models (states, screens,
            games, sound); in openMSX too (the keyboard: no aid at
            all; the joystick: given at IN A,(#A2), the aid declared
            since milestone 0.2); the silences after every end
  players   the games of the three players on the tests' cartridges
            against the world model, every pass
  systems   every system of the specification (section 6) with its
            code and its checks; the excluded ones absent (the CONTROLS
            menu, the beeper, the tape, packed data, joystick 2, MSX2);
            no placeholder in the sources
  mutations the 82 of milestone 0.8 and the 21 of milestones 0.1-0.3
            that still apply to the sources: 103, each stopped by the
            check named

Not certified (section 6 of the specification, METODO section 10):
real MSX machines, cartridges made from the ROM, other emulators than
openMSX 21.0 with C-BIOS 0.29, MSX2 and later machines.

Writes OUT/verify_1_0.json. Usage: python tests/verify_1_0.py --out
DIR [--no-openmsx] [--reference REPORT] [--only PARTS]
[--mutations FROM-TO] [--sjasmplus EXE] [--openmsx EXE] [--step 7|8]

With --step 7 or 8 (Phase D, D.2) the test runs on a step of the
book's chain (chain/NN, made by tools/make_chain.py --assemble): its
cartridges (the cartridge, the three tests' cartridges, the 16 rooms),
its sources and its data, from the states at INIT of game/build. Step
08 is 1.0: its 20 ROMs must be those of milestone 0.8 and the facts
of the bench those of 1.0 (--reference). Step 07 is 1.0 without the
opening screen: its ROMs = chain/chain.json's; the title at power on
(tests/sessions_0_8.py OPENING_SCREEN), the sessions without their
opening part; the systems but the opening screen; the mutations that
apply to its sources (those of the opening screen are not there:
declared).

With --folder DIR (Phase D, D.3) the step is a guided variant or a
"Where it breaks" version of step 07 or 08 (variants/NN-name/ID): its
cartridges, sources and data (tests/folder_first.py: its asset modules
first, its music), the ROMs = its manifest's; --set changes the models
as the variant changes the program.
"""
import argparse
import hashlib
import importlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'tools'))
import folder_first as FF  # noqa: E402
FOLDER = FF.use(sys.argv)       # a variant's folder: its data first
import msxsim  # noqa: E402
import psg_model as P  # noqa: E402
import sessions_0_8 as S  # noqa: E402
import sessions_1_0 as S1  # noqa: E402
import verify_0_8 as V  # noqa: E402
import world_model as W  # noqa: E402
from msxtools import cbios_dir, find_tool  # noqa: E402

ROOT = V.ROOT
SRC = V.SRC
ASSETS = ROOT / 'game' / 'assets'
CHAIN_STEPS = {7: '07-title-and-ends', 8: '08-complete'}
OPENING_SYSTEM = 'the opening screen'
# the ROMs of milestone 0.8 (milestones/0.8-complete/game/build/
# manifest.json): 1.0 is the same cartridge
ROMS_0_8 = {
    'cryptmorrow': 'ee48662a9c40c039c26017d55ad8dc14786c1d8bcf3842d1831025b8d5f6adbd',
    'cryptmorrow_play': '19f5a1d19cb1b76709dd4fe2e2146fb9c9ad836776339220b4835e1b3b95ca36',
    'cryptmorrow_play_fx': 'ab104695ae6376ce526f2cd8ad6ec07cc3c583283620a0302dba961d5bf6358c',
    'cryptmorrow_play_silent': '2e8a825d034c72b8b2e05715dde005b080b5a48869f5cf4b818f1686b388120b',
    'rooms/00': 'e7c54a40326500a16a0f57d4ba722831aea1ed4b23f52a39f41ed534c67595a0',
    'rooms/01': '19f5a1d19cb1b76709dd4fe2e2146fb9c9ad836776339220b4835e1b3b95ca36',
    'rooms/02': '7a6e42b4c5cd5677ef350c5bd09f9282a0a3e7bc09348ded843c467f85a29294',
    'rooms/03': '85bf1c956260e8e36a8d228aae29ec7462aa11fa7b0fccb04e5fee75eb49e3e3',
    'rooms/04': '217d7b1325c0c9d592f25064202b32f17b6f160c1a2800ef593d259a90e6829d',
    'rooms/05': '4c955cf120eed47b70762f66806dd46558e714d57070baacc6bd286f7cf053da',
    'rooms/06': '57e9f20835428861f1544f423798749d8fbc87408375373211a3ddbca364e0ca',
    'rooms/07': '8a8446974e52df077318ab5015ba1fbe58f3ff499921a550deb0d229a130829f',
    'rooms/08': 'b22a03ad84eb47cb898748b96f4c37f90bbc7106188248e5d88a5f0b44224c49',
    'rooms/09': '601885ec619dae0cf38b82821021e22cb903907475f6b2fd038340a618041ffe',
    'rooms/10': '97f784b06ff4e18d048d6577d25b2587fce75c6be989afd04fc3016de9e1bc80',
    'rooms/11': '144d6da042bf385014cb743bfc908cfdf9653a6d57abab148cc404e63123df9c',
    'rooms/12': '7bf8c9cff4f9ce9f18ba0c31ee41e2f1cf0b0063ce15bec749815c00348341d0',
    'rooms/13': 'e09e6551887102542e837b7e38b4ce8fc428eb94da64e345f2363be6898598b5',
    'rooms/14': '7ddd6d7ce39878384f1f73d415f6bc29fd59004bbcec77d25276eb3a4fbe8c51',
    'rooms/15': 'ca92724f820b4d10b4e13884e17cab0eca454d5b09bb1cfec964819010420564',
}

# -- the mutations of milestones 0.1-0.3 that still apply ---------------
# (milestone 0.4 on carried theirs forward: they are in V.MUTATIONS)
OLD = {'verify_0_1': ('third_without_inc', 'name_not_centred',
                      'status_not_read', 'colours_wrong_third',
                      'gradient_7_rows', 'im2_table_256', 'names_in_rom',
                      'fast_vram_screen_on'),
       'verify_0_2': ('right_wins', 'down_wins', 'hitbox_right_short',
                      'walk_every_4', 'stand_keeps_step', 'room_lines_168',
                      'sprite_a_line_low'),
       'verify_0_2_1': ('skin_in_khaki',),
       'verify_0_3': ('entry_margin_4', 'west_goes_east', 'south_two_rows',
                      'solid_map_not_built', 'flames_of_the_old_phase')}


def old_mutations():
    """The mutations of milestones 0.1-0.3 in the form of 0.8's: (name,
    edits, the check that must stop it); the whole game as script."""
    out = []
    for mod, names in OLD.items():
        m = importlib.import_module(mod)
        for mu in m.MUTATIONS:
            if mu[0] not in names:
                continue
            edits, must = (mu[2], mu[3]) if mod == 'verify_0_1' else \
                (mu[1], mu[2])
            out.append((f'{mu[0]} (0.{mod[9:].replace("_", ".")})',
                        edits, must))
    assert len(out) == sum(len(n) for n in OLD.values())
    return out


MUTATIONS = V.MUTATIONS + old_mutations()

# -- the systems of the specification -----------------------------------
SYSTEMS = [
    # (section 6 of the specification, its labels, the checks that test
    # it: words of their names)
    ('the explorer', ('hero_init', 'update_hero'),
     'room and explorer = the model'),
    ('skeletons and bats', ('spawn_enemies', 'update_enemies'),
     'blow, damage, enemies, sprite list = the model'),
    ('the blade and the damage', ('check_fire', 'check_blade',
                                  'check_contact'),
     'blow, damage, enemies, sprite list = the model'),
    ('keys, doors, potions, treasures, seals, the portal',
     ('check_objects', 'check_door', 'show_door', 'victory'),
     'keys, seals, score, energy, doors, end, objects'),
    ('the HUD and the name of the room', ('hud_draw', 'hud_update',
                                          'hud_name'),
     'screen = model, every pass'),
    ('the title with the menu of the sound', ('show_title',
                                              'title_frame'),
     'the opening, the title and the end screens = the model'),
    ('the end screens', ('end_game', 'ending_frame', 'show_end',
                         'end_frame'),
     'the opening, the title and the end screens = the model'),
    ('the music and the eight effects', ('music_step', 'end_sound',
                                         'sound_effect', 'fx_step'),
     'every group of registers sent to the PSG'),
    ('the opening screen', ('show_opening', 'opening_frame'),
     'the opening, the title and the end screens = the model'),
]
EXCLUDED_WORDS = re.compile(r'\b(kempston|sinclair|controls|redefin\w*|'
                            r'beeper|tape|loader|depack\w*|unpack\w*|'
                            r'decompress\w*)\b', re.I)
PLACEHOLDER = re.compile(r'\b(TODO|FIXME|TBD|XXX)\b|'
                         r'(?i:\b(placeholder|segnaposto)\b)')
MSX1_PORTS = {0x98, 0x99, 0xA0, 0xA1, 0xA2, 0xA8, 0xA9, 0xAA, 0xAB}


class PortMSX(msxsim.MSX):
    """The bench, keeping the ports it is asked for."""

    def __init__(self, *args, **kw):
        self.ports = set()
        super().__init__(*args, **kw)

    def read_port(self, registers, port):
        self.ports.add(('in', port & 0xFF))
        return super().read_port(registers, port)

    def write_port(self, registers, port, value, *rest):
        self.ports.add(('out', port & 0xFF))
        return super().write_port(registers, port, value, *rest)


def systems(cdir, checks, facts):
    rom, sym = V.rom_files(V.CARTRIDGE)
    missing = [lab for s, labs, w in SYSTEMS for lab in labs
               if lab not in sym]
    facts['systems'] = [{'system': s, 'labels': {lab: sym.get(lab)
                                                 for lab in labs},
                         'tested_by': w} for s, labs, w in SYSTEMS]
    checks.add(f'systems: the {len(SYSTEMS)} systems of the specification '
               '(section 6) each with its code in the cartridge, and '
               'eight effects in the data', not missing and
               len(V.MUSIC['sfx_names']) == 8,
               f'missing {missing}' if missing else
               ', '.join(s for s, labs, w in SYSTEMS))
    words, holders = [], []
    for p in sorted(SRC.glob('*.asm')):
        for n, line in enumerate(p.read_text(encoding='ascii')
                                 .splitlines(), 1):
            if EXCLUDED_WORDS.search(line):
                words.append(f'{p.name}:{n}')
            if PLACEHOLDER.search(line):
                holders.append(f'{p.name}:{n}')
    for p in sorted(ASSETS.glob('*.py')):
        for n, line in enumerate(p.read_text(encoding='utf-8')
                                 .splitlines(), 1):
            if PLACEHOLDER.search(line):
                holders.append(f'{p.name}:{n}')
    checks.add('systems: the excluded ones absent from the sources (the '
               'CONTROLS menu, the beeper, the tape and its loader, '
               'packed data)', not words, ', '.join(words[:4]))
    checks.add('systems: no placeholder (TODO, FIXME, TBD, XXX, '
               'placeholder) in the sources and in the makers of the '
               'data', not holders, ', '.join(holders[:4]))
    # the long session in a bench that keeps the ports, the VDP
    # registers and register 15 of the PSG
    parts = S1.plan(V, 'long', 50)
    script, pokes, starts = S1.flatten(parts)
    state = json.loads((V.BUILD / 'state_eu.json').read_text())
    m = PortMSX(rom, state, V.cbios_roms(cdir, 'eu'))
    vregs = set()
    vdp, plain = m.vdp, m.vdp.write

    def vw(port, value, t, pc):
        if port & 1 and vdp.latch_full and value & 0x80:
            vregs.add(value & 0x3F)
        plain(port, value, t, pc)
    vdp.write = vw
    for bits, keys, joy in script:
        m.set_input(keys, joy)
        m.run_to(sym['frame_ready'], max_t=60 * vdp.frame_t)
    r15 = sorted({v for t, r, v in m.psg.log if r == 15})
    used = sorted(p for d, p in m.ports)
    facts['systems_ports'] = {'ports': [f'{d} #{p:02X}' for d, p in
                                        sorted(m.ports)],
                              'vdp_registers': sorted(vregs),
                              'psg_r15': [f'#{v:02X}' for v in r15]}
    checks.add('systems: joystick 2 never read (every write of PSG '
               'register 15 selects port 1), in the long session',
               r15 and not any(v & 0x40 for v in r15),
               ', '.join(f'#{v:02X}' for v in r15))
    checks.add('systems: nothing of MSX2 and later (only the ports of an '
               'MSX1: VDP #98-#99, PSG #A0-#A2, PPI #A8-#AB; VDP '
               'registers 0-7), in the long session',
               set(used) <= MSX1_PORTS and vregs <= set(range(8)),
               f"ports {facts['systems_ports']['ports']}, VDP registers "
               f'{sorted(vregs)}')


def systems_tested(checks):
    """Every system has passing checks that test it, none failing."""
    out = []
    for s, labs, words in SYSTEMS:
        mine = [c for c in checks.items if words in c['check']]
        if not mine or not all(c['pass'] for c in mine):
            out.append(s)
    return out


def alone(cdir, checks, facts):
    """GAME OVER without help on the tests' cartridges, every pass =
    the world model, in the three modes at 50 and 60 Hz."""
    bits = S1.alone_defeat(V)
    script = V.script_of(V.runs_of(bits), V.SOURCES)
    model = V.model_end(script, {}, V.GAME_ROOM)
    end = V.end_pass(script, {})
    checks.add('the model: GAME OVER without help in the Crossroads, '
               'from full energy (four touches)',
               model.ended == W.ENDED_LOST and model.energy == 0 and
               model.room == 5, f'pass {end} of {len(script)}')
    for mname, (machine, hz) in V.MACHINES.items():
        tag = f'{mname} ({hz} Hz)'
        for mode in (P.MODE_MUSIC, P.MODE_FX, P.MODE_SILENT):
            f = facts.setdefault(f'alone_{mname}_{V.GAMES[mode]}', {})
            runs, lasts = V.walk_machine(None, cdir, checks, f, mname, tag,
                                         script, {}, (None,),
                                         'GAME OVER without help', mode)
            m0, recs0, ch0, ev0 = runs[None]
            # three touches, and the fourth ends the game
            touches = sum(1 for k, w in ev0 if w == 'touch')
            ends = [k for k, w in ev0 if w == 'end']
            f['touches'], f['end_pass'] = touches, ends[0] if ends else None
            checks.add(f'{tag} GAME OVER without help '
                       f'{V.MODE_NAMES[mode]}: three touches, the fourth '
                       f'GAME OVER at pass {f["end_pass"]} = the model',
                       touches == 3 and ends and ends[0] == end,
                       f'{touches} touches before the end')


def on_step(step, tmp):
    """The test on a step of the book's chain: its cartridges, sources
    and data; the states at INIT of the workspace's build (game/build).
    Returns the step's folder."""
    global SRC, ASSETS
    folder = FOLDER or ROOT / 'chain' / CHAIN_STEPS[step]
    build = tmp / 'build'
    shutil.copytree(folder / 'game' / 'build', build)
    for mname in V.MACHINES:
        shutil.copy(V.BUILD / f'state_{mname}.json', build)
    V.BUILD = build
    V.rom_files.__defaults__ = (build,)
    V.SRC = SRC = folder / 'game' / 'src'
    ASSETS = folder / 'game' / 'assets'
    V.GENERATED = ASSETS / 'generated' / 'B'
    if step == 7:
        S.OPENING_SCREEN = False
        SYSTEMS[:] = [s for s in SYSTEMS if s[0] != OPENING_SYSTEM]
    return folder


def applies(mutation):
    """Every line the mutation changes is in the sources once (the
    test of 1.0 applies its mutations to the file named)."""
    for fname, old, new in mutation[1]:
        p = SRC / fname
        if not p.exists() or p.read_text(encoding='ascii').count(old) != 1:
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--openmsx')
    ap.add_argument('--no-openmsx', action='store_true')
    ap.add_argument('--reference')
    ap.add_argument('--keep-runs', action='store_true')
    ap.add_argument('--sjasmplus')
    ap.add_argument('--only', help='parts, comma separated: data, '
                    'sound, palettes, game, defeat, shots, rooms, alone, '
                    'sessions, players, systems, mutations')
    ap.add_argument('--mutations', help='FROM-TO: only these (0-based, '
                    'TO excluded)')
    ap.add_argument('--step', type=int, choices=sorted(CHAIN_STEPS),
                    help='a step of the book\'s chain (Phase D)')
    ap.add_argument('--folder', type=Path, help='a variant of the step '
                    '(variants/NN-name/ID, D.3; with --step)')
    ap.add_argument('--set', action='append', default=[],
                    help='a change of the models (a variant)')
    a = ap.parse_args()
    FF.apply(a.set)
    if FOLDER:
        FF.music(V, FOLDER)
    a.update_state = False
    parts = set(a.only.split(',')) if a.only else {
        'data', 'sound', 'palettes', 'game', 'defeat', 'shots', 'rooms',
        'alone', 'sessions', 'players', 'systems', 'mutations'}
    which = tuple(int(x) for x in a.mutations.split('-')) \
        if a.mutations else None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    png = out / 'png'
    png.mkdir(exist_ok=True)
    V.WAVS = out / 'wav'
    V.WAVS.mkdir(exist_ok=True)
    openmsx = None if a.no_openmsx else find_tool('openmsx', a.openmsx)
    if not a.no_openmsx and not openmsx:
        print('openMSX not found (--no-openmsx for the bench only)')
        return 1
    sjasm = find_tool('sjasmplus', a.sjasmplus)
    cdir = cbios_dir(openmsx)
    if cdir is None:
        print('C-BIOS not found')
        return 1
    if a.keep_runs:
        V.RUNS = out / 'runs'
        V.RUNS.mkdir(exist_ok=True)
    else:
        V.RUNS = Path(tempfile.mkdtemp(prefix='verify_1_0_'))
    checks, facts = V.Checks(), {}
    step_tmp = Path(tempfile.mkdtemp(prefix='verify_1_0_step_')) \
        if a.step else None
    try:
        if a.step:
            folder = on_step(a.step, step_tmp)
            print(f'Step {a.step:02} of the chain: {folder}')
        manifest = json.loads((V.BUILD / 'manifest.json').read_text())
        checks.add('build: game/build/manifest.json without problems',
                   not manifest['problems'],
                   '; '.join(manifest['problems'][:2]))
        roms = {k: e['sha256'] for k, e in manifest['roms'].items()}
        facts['build'] = {k: v[:16] for k, v in roms.items()}
        facts['cartridge'] = manifest['measures']
        if a.step:
            # the ROMs as built = the manifest's = chain/chain.json's
            built = {k: hashlib.sha256((V.BUILD / f'{k}.rom')
                                       .read_bytes()).hexdigest()
                     for k in roms}
            chain = json.loads((ROOT / 'chain' / 'chain.json')
                               .read_text())['steps'][CHAIN_STEPS[a.step]]
            if FOLDER:
                checks.add(f'build: the 20 ROMs of {FOLDER.name} = its '
                           'manifest\'s (built by its tools)',
                           len(roms) == 20 and built == roms,
                           f"cartridge {roms.get('cryptmorrow', '')[:16]}")
            else:
                checks.add(f'build: the 20 ROMs of step {a.step:02} = '
                           'chain/chain.json\'s, byte for byte',
                           len(roms) == 20 and built == roms ==
                           dict(chain['roms']),
                           f"cartridge {roms.get('cryptmorrow', '')[:16]}")
        if a.step != 7 and not FOLDER:
            checks.add('build: the 20 ROMs = those of milestone 0.8, byte '
                       'for byte (1.0 is its cartridge)', roms == ROMS_0_8,
                       f"cartridge {roms.get('cryptmorrow', '')[:16]}")
        def part(name, run, *args):
            # a part the program never gets through (a "Where it breaks"
            # version, D.3: the bench stops it, or openMSX never sees
            # what the part waits for) is a failed check, and the other
            # parts still run
            try:
                run(*args)
            except RuntimeError as error:
                checks.add(f'{name}: the program reached every pass',
                           False, str(error)[:300])
            except Exception as error:          # noqa: BLE001
                checks.add(f'{name}: the part ran to its end', False,
                           f'{type(error).__name__}: {error}'[:300])

        if 'data' in parts:
            part('data', V.data, checks, facts, cdir, png)
        if 'sound' in parts:
            part('sound', V.sound, openmsx, cdir, checks, facts, out)
        if openmsx and 'palettes' in parts:
            part('palettes', V.palettes, openmsx, checks, facts)
        if 'game' in parts:
            part('game', V.game, openmsx, cdir, checks, facts, a)
        if 'defeat' in parts:
            part('defeat', V.defeat, openmsx, cdir, checks, facts)
        if openmsx and 'shots' in parts:
            part('shots', V.shots, openmsx, cdir, checks, facts, png)
        if 'rooms' in parts:
            part('rooms', V.rooms, openmsx, cdir, checks, facts)
        if 'alone' in parts:
            part('alone', alone, cdir, checks, facts)
        if 'sessions' in parts:
            part('sessions', S1.sessions, V, openmsx, cdir, checks, facts,
                 png)
        if 'players' in parts:
            for n in S1.PLAYERS:
                part('players', S1.games_checked, V, cdir, checks, facts,
                     n)
        if 'systems' in parts:
            part('systems', systems, cdir, checks, facts)
        if 'mutations' in parts:
            if sjasm:
                V.MUTATIONS = MUTATIONS
                if a.step == 7:
                    left = [mu[0] for mu in MUTATIONS if not applies(mu)]
                    V.MUTATIONS = [mu for mu in MUTATIONS if applies(mu)]
                    facts['mutations_not_in_step'] = left
                    checks.add(f'mutations: {len(V.MUTATIONS)} of '
                               f'{len(MUTATIONS)} apply to step 07; the '
                               f'{len(left)} left out change the opening '
                               'screen, not in the step', left and
                               all('opening' in n for n in left),
                               ', '.join(left))
                V.mutations(sjasm, openmsx, cdir, checks, facts, which)
            else:
                checks.add('mutations: sjasmplus found', False)
        if parts >= {'game', 'defeat', 'rooms', 'alone', 'sessions',
                     'players', 'systems'}:
            untested = systems_tested(checks)
            checks.add('systems: each one tested, every check that tests '
                       'it passed', not untested, ', '.join(untested))
    finally:
        if not a.keep_runs:
            shutil.rmtree(V.RUNS, ignore_errors=True)
        if step_tmp:
            shutil.rmtree(step_tmp, ignore_errors=True)
    if a.reference:
        ref = json.loads(Path(a.reference).read_text())['facts']
        mine = json.loads(json.dumps(facts))
        rb, ro = V.split_facts(ref)
        mb, mo = V.split_facts(mine)
        diff = [k for k in rb if rb.get(k) != mb.get(k)]
        checks.add('bench facts = the reference (' + a.reference + ')',
                   not diff, ', '.join(diff[:4]))
        if openmsx and ro:
            diff = sorted(k for k in set(ro) | set(mo)
                          if ro.get(k) != mo.get(k))
            checks.add('openMSX facts (palettes, screenshots) = the '
                       'reference', not diff, ', '.join(diff[:4]))
    report = {'checks': checks.items, 'facts': facts,
              'failed': len(checks.failed), 'openmsx': openmsx,
              'cbios': str(cdir)}
    if FOLDER or a.set:                 # a variant (D.3)
        report.update(result='FAIL' if checks.failed else 'PASS',
                      folder=str(FOLDER) if FOLDER else None, set=a.set,
                      parts=sorted(parts))
    (out / 'verify_1_0.json').write_text(json.dumps(report, indent=1)
                                         + '\n', encoding='utf-8')
    print(f'\n{len(checks.items)} checks, {len(checks.failed)} failed')
    for c in checks.failed:
        print('FAILED:', c['check'], c['detail'])
    return 1 if checks.failed else 0


if __name__ == '__main__':
    sys.exit(main())

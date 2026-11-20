"""The sessions of Cryptmorrow MSX 1.0, the complete game (Phase C):
the cartridge from its start, as a player uses it, without any help
of the tests. tests/verify_1_0.py runs them and gives itself as V
(the helpers and constants of tests/verify_0_8.py).

The checks of every pass are those of milestone 0.8's sessions
(tests/sessions_0_8.py: walk, the model of the states, the games
against the tests' cartridges, the PSG); what changes is what the
player does:

  long     the keyboard alone, no byte put in RAM: the opening for its
           three seconds, the menu up and down; MUSIC: the whole game
           planned (tests/game_plan.py), VICTORY; SOUND FX: GAME OVER
           from full energy, without help (out of the Moss Gate to the
           south, down into the row of the skeleton of the
           Crossroads, still: four touches); SILENT: the same; the
           title. In openMSX without any aid (the keyboard is a
           command of openMSX); it records the piece of the victory.
  long_joy the same with the joystick alone, in the bench only.
  short    the joystick alone: FIRE ends the opening; MUSIC: GAME OVER
           without help; the title; again with the RAM filled at
           random. In openMSX the joystick is given right after IN
           A,(#A2), the aid declared since milestone 0.2 (openMSX 21.0
           has no command for it); it records the piece of the defeat.
  player_N three players that are not a plan (tests/bot.py), 20 000
           passes each: the opening waited or skipped, the cursor of
           the sound moved at random, games played chasing the
           enemies and walking out of the rooms until they end, the
           end screen, FIRE, the next game. 1: 50 Hz, keyboard; 2:
           60 Hz, keyboard; 3: 50 Hz, joystick. 1 and 2 in openMSX
           too, without any aid. Each of their games is also played on
           the tests' cartridge of its mode against the world model,
           every pass (games_checked).

The silences (silences): after every GAME OVER and VICTORY, in each
mode, the piece or the effect of the end ends within its length and
nothing sounds after it on the end screen; back on the title MUSIC
plays again (the theme from its start: the PSG = the model), SOUND FX
and SILENT are silent; SILENT never sounds, from the start of its game
to the next title.
"""
import json
import random

import bot
import msxsim
import openmsx_run
import psg_model as P
import sessions_0_8 as S
import world_model as W
from sessions_0_8 import (STATE_TITLE, STATE_PLAY, STATE_ENDING,
                          STATE_END, OPENING, U, D, F, WHAT, LABELS,
                          press, flatten, walk, games_of, seeds_check,
                          opening_kept)

# GAME OVER without help: four touches of the skeleton of the
# Crossroads from full energy (399 passes; Cryptmorrow ZX 1.0 did the
# same)
ALONE = [('wait', 2), ('exit', 'south'), ('down_to', 106),
         ('until_end',)]
KEYS, JOY = ('keys',), ('joy',)
PLAYERS = {1: ('eu', KEYS), 2: ('int', KEYS), 3: ('eu', JOY)}
PLAYER_PASSES = 20000
END_WAIT = 220              # the end screen: the piece to its end


def seq(V, bits, sources):
    """[(bits, keys, joy)] a pass, from the bits, through one input
    (sources: ('keys',) or ('joy',))."""
    return V.script_of(V.runs_of(bits), sources)


_ALONE = []


def alone_defeat(V):
    """The bits of GAME OVER without help, then AFTER_DEFEAT passes of
    input that change nothing (as milestone 0.8's defeat)."""
    if not _ALONE:
        world = W.World(V.GAME_ROOM)
        bits, pokes = V.plan_steps(world, ALONE)
        assert not pokes and world.ended == W.ENDED_LOST
        after = [b for b, k, j in V.random_route(9, V.AFTER_DEFEAT)]
        _ALONE.append(bits + after)
    return list(_ALONE[0])


def planned_game(V):
    script, pokes = V.game_script()
    assert not pokes
    return [b for b, k, j in script]


def player_game(V, rnd, seed):
    """A game of the player: PREFIX passes without input, the bot's
    game to its end, AFTER_END passes of random input."""
    bits, world = bot.play(seed, V.GAME_ROOM, V.PREFIX)
    after = [rnd.choice(bot.CHOICES) for _ in range(V.AFTER_END)]
    return bits + after, world


def plan(V, kind, hz=50):
    """The session: [(what, script, pokes)] in order (as
    sessions_0_8.plan); no pokes. Without the opening screen (step 07
    of the chain) the same, the title at once."""
    return opening_kept(plan_all(V, kind, hz))


def plan_all(V, kind, hz=50):
    end = [0] * 30 + press(F, 4, 70) + [0] * 100 + press(F, 3, 1)
    if kind in ('long', 'long_joy'):
        src = KEYS if kind == 'long' else JOY
        title1 = [0] * 40 + press(D) + press(D) + press(D) + press(U) + \
            press(U) + press(U) + press(U | D) + [0] * 10 + press(F, 3, 1)
        defeat = alone_defeat(V)
        return [('opening', seq(V, [0] * 200, src), {}),
                ('title', seq(V, title1, src), {}),
                (('game', P.MODE_MUSIC, 'game'),
                 seq(V, planned_game(V), src), {}),
                ('end', seq(V, end, src), {}),
                ('title', seq(V, [0] * 10 + press(D) + press(F, 3, 1),
                              src), {}),
                (('game', P.MODE_FX, 'defeat'), seq(V, defeat, src), {}),
                ('end', seq(V, end, src), {}),
                ('title', seq(V, [0] * 6 + press(D) + press(F, 3, 1),
                              src), {}),
                (('game', P.MODE_SILENT, 'defeat'), seq(V, defeat, src),
                 {}),
                ('end', seq(V, end, src), {}),
                ('title', seq(V, [0] * 40, src), {})]
    if kind == 'short':
        src = JOY
        return [('opening', seq(V, [0] * 30 + press(F, 3, 1), src), {}),
                ('title', seq(V, [0] * 20 + press(F, 3, 1), src), {}),
                (('game', P.MODE_MUSIC, 'defeat'),
                 seq(V, alone_defeat(V), src), {}),
                ('end', seq(V, end, src), {}),
                ('title', seq(V, [0] * 20, src), {})]
    return player_plan(V, int(kind.split('_')[1]), hz)


_PLAYERS = {}


def player_plan(V, n, hz):
    if (n, hz) in _PLAYERS:
        return _PLAYERS[(n, hz)]
    mname, src = PLAYERS[n]
    rnd = random.Random(1000 + n)
    if rnd.random() < 0.5:                  # the opening waited
        op = [0] * (OPENING[hz] + rnd.randint(1, 30))
    else:                                   # or ended by FIRE
        op = [0] * rnd.randint(5, OPENING[hz] - 20) + [F] * 3 + [0]
    parts = [('opening', seq(V, op, src), {})]
    total, mode, g = len(op), P.MODE_MUSIC, 0
    while total < PLAYER_PASSES:
        tb, mode = bot.title_moves(rnd, mode,
                                   (P.MODE_MUSIC, P.MODE_SILENT))
        gb, world = player_game(V, rnd, 100 * n + g)
        eb = bot.end_wait(rnd, END_WAIT)
        name = f'player {n} game {g + 1} ' + \
            ('won' if world.ended == W.ENDED_WON else 'lost')
        parts += [('title', seq(V, tb, src), {}),
                  (('game', mode, name), seq(V, gb, src), {}),
                  ('end', seq(V, eb, src), {})]
        total += len(tb) + len(gb) + len(eb)
        g += 1
    parts.append(('title', seq(V, [0] * 40, src), {}))
    _PLAYERS[(n, hz)] = parts
    return parts


class Recorder(S.Model):
    """The model of the states, keeping (state, mode, game) of every
    pass for the silences."""

    def __init__(self, games, hz=50):
        super().__init__(games, hz)
        self.history = []

    def frame(self, bits):
        super().frame(bits)
        self.history.append((self.state, self.mode, self.g))


def sounding(regs):
    """Some sound: a volume not 0 (or the envelope) on a channel."""
    return any(regs[r] & 0x1F for r in (8, 9, 10))


def piece_frames(V, hz, what, mode):
    """The frames of the end's piece (MUSIC: its steps, and two more
    for the release of its last notes) or effect (SOUND FX: its
    frames)."""
    if mode == P.MODE_MUSIC:
        speed = V.MUSIC['speed_50' if hz == 50 else 'speed_60']
        return (V.MUSIC['songs'][what]['steps'] + 2) * speed
    first = V.MUSIC['fx_first'] + [len(V.MUSIC['fx'])]
    n = P.SFX[what]
    return first[n] - first[n - 1]


def silences(V, model, recs, games, hz):
    """The sound around the ends of a session: (problems, facts)."""
    hist = model.history
    sound = [sounding(r[3]) for r in recs]
    n = min(len(hist), len(sound))
    bad, out = [], []
    for gi, game in enumerate(games):
        ks = [k for k in range(n) if hist[k][2] == gi]
        play = [k for k in ks if hist[k][0] in (STATE_PLAY, STATE_ENDING)]
        endk = [k for k in ks if hist[k][0] == STATE_ENDING]
        screen = [k for k in ks if hist[k][0] == STATE_END]
        if not endk or not screen:
            continue                    # the session ends before
        mode, k_end = game['mode'], endk[0]
        what = 'won' if game['won'] else 'lost'
        after = endk + screen
        heard = [k for k in after if sound[k]]
        last = heard[-1] - k_end + 1 if heard else 0
        title = []                      # until the menu or a game
        for k in range(screen[-1] + 1, min(n, screen[-1] + 51)):
            if hist[k][0] != STATE_TITLE or hist[k][1] != mode:
                break
            title.append(k)
        tsound = sum(sound[k] for k in title)
        rec = {'game': gi + 1, 'mode': mode, 'end': what,
               'heard_after_end': last,
               'end_screen': len(screen),
               'title_passes_sounding': tsound,
               'title_passes': len(title)}
        tag = f'game {gi + 1} ({V.MODE_NAMES[mode]}, {what})'
        if mode == P.MODE_SILENT:
            loud = [k for k in play + screen if sound[k]]
            rec['sounding'] = len(loud)
            if loud:
                bad.append(f'{tag}: sound at pass {loud[0] + 1}')
            if tsound:
                bad.append(f'{tag}: sound on the title')
        else:
            length = piece_frames(V, hz, what, mode)
            rec['length'] = length
            if not heard:
                bad.append(f'{tag}: the end not heard')
            elif last > length + 2:
                bad.append(f'{tag}: heard {last} passes after the end, '
                           f'the piece {length}')
            elif heard[-1] >= screen[-1]:
                bad.append(f'{tag}: still sounding when the title came')
            if mode == P.MODE_MUSIC and len(title) >= 10 and \
                    not any(sound[k] for k in title[:10]):
                bad.append(f'{tag}: the theme not again on the title')
            if mode == P.MODE_FX and tsound:
                bad.append(f'{tag}: sound on the title')
        out.append(rec)
    return bad, out


def emu(V, openmsx, sym, mname, script, rd, shots=(), wav=None):
    """openMSX with the session's input; the aid of the joystick only
    if the session uses it."""
    machine, hz = V.MACHINES[mname]
    rom_path = V.BUILD / f'{V.CARTRIDGE}.rom'
    joy_read = None
    if any(j for b, k, j in script):
        rom = rom_path.read_bytes()
        joy_read = openmsx_run.find_in(rom, 0x4000, sym['in_joy'],
                                       (0xDB, 0xA2)) + 2
    return openmsx_run.run(openmsx, rom_path, machine, sym, len(script),
                           rd, shots=shots, inputs=V.inputs_of(script),
                           pokes={}, joy_read=joy_read, lazy=True,
                           psg_log=True, wav=wav,
                           max_seconds=round(10 + len(script) / 30, 2))


def firsts(parts, starts):
    """{'opening', 'title', 'game', 'end': the first pass of each
    part of that kind, in order}."""
    out = {}
    for (what, s, pk), k in zip(parts, starts):
        out.setdefault(what if isinstance(what, str) else what[0],
                       []).append(k)
    return out


def windows_of(kind, parts, starts):
    """The passes of the pictures kept, and taken by openMSX: the
    opening, the title, the end screen; the title again."""
    f = firsts(parts, starts)
    if kind == 'long':
        out = {f['title'][0] + 19: 'title', f['end'][0] + 111: 'end_won'}
        if 'opening' in f:
            out[f['opening'][0] + 99] = 'opening'
        return out
    if kind == 'short':
        return {f['end'][0] + 111: 'end_lost',
                f['title'][1] + 10: 'title_again'}
    return {}


def machines_of(kind):
    if kind.startswith('player_'):
        return (PLAYERS[int(kind.split('_')[1])][0],)
    return ('eu', 'int')


def sessions(V, openmsx, cdir, checks, facts, png,
             kinds=('long', 'long_joy', 'short', 'player_1', 'player_2',
                    'player_3'),
             machines=None, games_cache=None):
    rom, sym = V.rom_files(V.CARTRIDGE)
    for kind in kinds:
        for mname in machines_of(kind):
            if machines and mname not in machines:
                continue
            hz = V.MACHINES[mname][1]
            parts = plan(V, kind, hz)
            script, pokes, starts = flatten(parts)
            assert not pokes
            windows = windows_of(kind, parts, starts)
            capture = {k + i for k in windows for i in range(-6, 3)}
            tag = f'{mname} ({hz} Hz) session {kind}'
            state = json.loads((V.BUILD / f'state_{mname}.json')
                               .read_text())
            cb = V.cbios_roms(cdir, mname)
            if games_cache and (kind, mname) in games_cache:
                games = games_cache[(kind, mname)]
            else:
                games = games_of(V, parts, sym, state, cb, mname)
            model = Recorder(games, hz)
            m, recs, bad, f = walk(V, rom, sym, state, cb, script, pokes,
                                   model, capture=capture)
            pal = V.vram2png.palette(hz)
            for k, name in windows.items():
                rows = [[tuple(pal[c]) for c in r]
                        for r in m.captured[k]]
                (png / f'{kind}_{name}_{hz}hz.png').write_bytes(
                    V.png_rgb(rows, 1))
            f['games'] = [{k: g[k] for k in ('name', 'mode', 'end', 'won',
                                             'score', 'seals', 'rooms')}
                          for g in games]
            facts[f'session_{kind}_{mname}'] = f
            for what in WHAT:
                checks.add(f'{tag}: {LABELS[what]}', bad[what] is None,
                           bad[what] or f"{f['passes']} passes")
            rules = V.rule_checks(m)
            checks.add(f'{tag}: no VRAM access closer than '
                       f'{msxsim.VRAM_GAP} T in the picture, VDP_CTRL '
                       'with interrupts off, no write to ROM, PSG R7 '
                       '10xxxxxx, the PSG with interrupts off',
                       not any(rules.values()), str(rules))
            won = sum(g['won'] for g in games)
            lost = sum(1 for g in games if g['end'] and not g['won'])
            modes = sorted({V.MODE_NAMES[g['mode']] for g in games})
            f['ended'] = {'won': won, 'lost': lost, 'modes': modes}
            checks.add(f'{tag}: {len(games)} games without any byte put '
                       f'in RAM ({won} VICTORY, {lost} GAME OVER; '
                       f'{", ".join(modes)}), each one to its end and '
                       'the title again',
                       games and all(g['end'] for g in games) and
                       (kind not in ('long', 'short') or
                        won == kind.startswith('long')),
                       f"{f['passes']} passes")
            speed = V.MUSIC['speed_50' if hz == 50 else 'speed_60']
            whole = [e for e in f['ends'] if e[1] >=
                     V.MUSIC['songs'][e[0]]['steps'] * speed and not e[2]]
            music = sum(1 for g in games if g['mode'] == P.MODE_MUSIC)
            checks.add(f'{tag}: the piece of every end (MUSIC) played to '
                       'its end, then silence, until the title',
                       len(f['ends']) == music and whole == f['ends'],
                       str(f['ends']))
            sbad, srec = silences(V, model, recs, games, hz)
            f['silences'] = srec
            checks.add(f'{tag}: the silences: after every end the piece '
                       'or the effect ends within its length and nothing '
                       'sounds after it; on the title MUSIC plays again, '
                       'SOUND FX and SILENT are silent; SILENT never '
                       'sounds', not sbad, sbad[0] if sbad else
                       f'{len(srec)} ends')
            if kind == 'short':
                seeds_check(V, checks, f, tag, rom, sym, state, cb, script,
                            pokes, games)
            if not openmsx or kind in ('long_joy', 'player_3'):
                continue                # the joystick: the bench only
            rd = V.RUNS / f'session_{kind}_{mname}'
            wav = None
            if kind in ('long', 'short'):
                start = firsts(parts, starts)['game'][0] + \
                    games[0]['end'] - 1
                wav_name = ('victory' if kind == 'long' else 'defeat') + \
                    f'_{hz}hz.wav'
                wav = (V.WAVS / wav_name, start - 50)
            r = emu(V, openmsx, sym, mname, script, rd,
                    shots=sorted(windows), wav=wav)
            sbad, hashes = [], {}
            for k in sorted(set(windows) | {k + 2 for k in windows}):
                sp = rd / f'shot_{k}.png'
                if not sp.exists():
                    sbad.append(f'shot_{k}.png missing')
                    continue
                errs = [V.shot_ok(sp, m.captured[kk], hz)
                        for kk in range(k - 6, k + 1)]
                if all(errs):
                    sbad.append(errs[-1])
                hashes[str(k)] = V.shot_hash(sp)
            if windows:
                facts.setdefault('openmsx', {})[
                    f'session_{kind}_{mname}'] = hashes
                checks.add(f'{tag}: openMSX\'s screenshots '
                           f'({", ".join(windows.values())}, two frames '
                           'each) = one of the bench\'s last pictures, '
                           'every pixel', not sbad,
                           sbad[0] if sbad else
                           f'{len(hashes)} screenshots')
            diff = V.emu_compare(recs, r['frames'])
            same, n_irq = V.emu_irq_same(m, r)
            psame, pdet = V.psg_writes_same(m, r)
            aid = 'the joystick given at IN A,(#A2)' if kind == 'short' \
                else 'no aid'
            checks.add(f'{tag}: bench = openMSX ({aid}), every pass, '
                       'interrupts at the same T-states, every write to '
                       'the PSG the same, at the same T-state',
                       diff is None and same and
                       n_irq == len(m.irq_log) and psame and
                       not r['too_fast'] and not r['psg_directions'],
                       diff or f'{len(recs)} passes, {n_irq} interrupts, '
                       + pdet)
            if wav:
                t0 = r['wav_from'] or 0
                fg = [x for x in V.frame_groups(r) if x[0] >= t0]
                samples, rate = V.read_wav(wav[0])
                hd = V.heard(samples, rate, [t for t, gg in fg], t0,
                             [gg for t, gg in fg])
                f['openmsx_sound'] = dict(hd, file=wav[0].name)
                checks.add(f'{tag}: openMSX\'s sound from pass '
                           f'{wav[1]} ({wav[0].name}): the loudness of '
                           'every frame follows the registers',
                           hd['loudness_correlation'] >= 0.75, str(hd))
            del r


def games_checked(V, cdir, checks, facts, n, which=None):
    """The games of player n, each on the tests' cartridge of its mode
    against the world model, every pass (the checks of milestone
    0.8's game, the screen included); which: (from, to) of its games
    (the parts of the VM)."""
    mname, src = PLAYERS[n]
    hz = V.MACHINES[mname][1]
    state = json.loads((V.BUILD / f'state_{mname}.json').read_text())
    cb = V.cbios_roms(cdir, mname)
    worst = dict.fromkeys(V.WHAT)
    rules_bad, passes, out = [], 0, {}
    games = [p for p in plan(V, f'player_{n}', hz) if p[0][0] == 'game']
    lo, hi = which or (0, len(games))
    tag = f'{mname} ({hz} Hz) player {n}, games {lo + 1}-{min(hi, len(games))}'
    for what, script, pokes in games[lo:hi]:
        mode = what[1]
        rom, sym = V.rom_files(V.GAMES[mode])
        m, recs, bad, fr, last, ch, ev = V.bench_walk(
            rom, sym, state, cb, None, script, V.GAME_ROOM, {}, mode=mode)
        for w, e in bad.items():
            if e and worst.get(w) is None:
                worst[w] = f'{what[2]}: {e}'
        rules = V.rule_checks(m)
        rules_bad += [f'{what[2]}: {k}: {v}' for k, v in rules.items()
                      if v]
        passes += len(script)
        out[what[2]] = {'mode': mode, 'passes': len(script),
                        'changes': len(ch),
                        'events': {w: sum(1 for k, x in ev if x == w)
                                   for w in ('door', 'object', 'blow',
                                             'hit', 'defeat', 'touch',
                                             'end')}}
    facts.setdefault(f'player_{n}_games', {}).update(out)
    for w in V.WHAT:
        checks.add(f'{tag} on the tests\' cartridges: {V.LABELS[w]}',
                   worst[w] is None, worst[w] or f'{passes} passes')
    checks.add(f'{tag}: no VRAM access closer than '
               f'{msxsim.VRAM_GAP} T in the picture, VDP_CTRL with '
               'interrupts off, no write to ROM, PSG R7 10xxxxxx, the '
               'PSG with interrupts off', not rules_bad,
               rules_bad[0] if rules_bad else f'{len(out)} games')

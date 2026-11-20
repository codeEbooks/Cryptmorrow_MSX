"""The sessions of Cryptmorrow MSX (milestone 0.8): the cartridge from
its start, as a player uses it. tests/verify_0_8.py runs them (part
'sessions') and gives itself as V (its helpers, its constants).

A session is the opening screen (milestone 0.8: three seconds, or FIRE
pressed and let go), the title, the menu of the sound, a game started
by FIRE, the room standing still at the end, the end screen, FIRE
again, the title again, and the next game:

  long   the opening for its three seconds (150 passes at 50 Hz, 180
         at 60); the menu up and down; MUSIC: the whole game planned
         (tests/game_plan.py), VICTORY; SOUND FX: GAME OVER (energy 2
         put in RAM at the start of the game, down to the skeleton of
         the Crossroads); SILENT: GAME OVER; the title. openMSX
         records the piece of the victory.
  short  FIRE ends the opening; MUSIC: GAME OVER; the title. openMSX
         records the piece of the defeat.

What is checked, every pass, against the model of the states (as the
ZX game's tests/states_model.py, without the controls) and against the
tests' cartridges (cryptmorrow_play*.rom, the game at once):

  states   game_state, the mode of the sound, end_timer, fire_armed,
           fire_held, the pass counter, the picture on (R1), the
           opening's passes (open_timer)
  screens  the opening, the title and the end screens =
           msx_states.picture, every
           pixel (the torches in the phase drawn, PRESS FIRE bright or
           not); the sprites of the title = msx_states.title_sat
  game     a game started from the title = the same game in the tests'
           cartridge, pass by pass: every byte of its RAM but the
           frame counter, the flame phase, the sound (GAME_RAM); the
           calls of the sound
  sound    the calls of the sound = the model's (the title: the mode at
           every start, at every move of the menu, the pick-up in
           SOUND FX; the game: those of the tests' cartridge); every
           group of registers sent to the PSG = tests/psg_model.py
           following them; the music's registers always at the same
           T-state after the interrupt
  rules    as in the game: VRAM pace, VDP and PSG with the interrupt
           off, no write to ROM, R7
  seeds    the short session again with the RAM filled at random: the
           same, and every byte written in the areas of vars.asm or
           in the stack
  openMSX  the same session, every pass byte for byte, every write to
           the PSG; the recorded piece of the end follows the
           registers.
"""
import hashlib
import json

import msxsim
import msx_states as MS
import psg_model as P
import world_model as W

STATE_TITLE, STATE_PLAY, STATE_ENDING, STATE_END, STATE_OPENING = \
    range(5)
OPENING = {50: 150, 60: 180}        # its passes: three seconds
# The cartridge begins with the opening screen; step 07 of the book's
# chain (tests/verify_1_0.py --step 7) with the title, at once.
OPENING_SCREEN = True
U, D, L, R, F = 1, 2, 4, 8, 16
# the RAM of a game (vars.asm): all but the frame counter, the
# status, the slot, the flame phase drawn, the sound; and but the
# addresses in the cartridge (the two cartridges differ at INIT, so
# their data move), and the sprite list past its entries
GAME_RAM = ((0xC005, 0xC0BC), (0xC100, 0xC680), (0xC6E0, 0xC6E2),
            (0xC6E4, 0xC6E6))
NOT_GAME = (('zone_mt', 2), ('zone_so', 2), ('room_rec', 2),
            ('flame_phase', 1), ('spr_list', 16),
            ('pt_x', 2), ('pt_y', 1), ('far_x', 1), ('far_y', 1),
            ('west', 1), ('north', 1))    # (and the work of measure)
WHAT = ('reached', 'states', 'screen', 'sprites', 'game', 'calls', 'psg',
        'psg_time')
LABELS = {
    'reached': 'frame_ready every pass',
    'states': 'game_state, mode, timers, FIRE, the pass counter, the '
              'picture on = the model',
    'screen': 'the opening, the title and the end screens = the model, '
              'every pixel',
    'sprites': 'the sprites of the title = the model; none on the end '
               'screen',
    'game': 'each game = the same game in the tests\' cartridge, every '
            'pass (its RAM)',
    'calls': 'the calls of the sound = the model\'s',
    'psg': 'every group of registers sent to the PSG = the model '
           '(psg_model)',
    'psg_time': 'the music\'s registers sent at the same T-state after '
                'every interrupt'}


def keys_script(V, bits):
    return V.script_of(V.runs_of(bits), ('keys',))


def press(b, held=4, after=4):
    return [b] * held + [0] * after


def opening_kept(parts):
    """The parts of a session as the cartridge has them: without the
    opening screen (step 07 of the chain) the title at once."""
    if OPENING_SCREEN:
        return parts
    return [p for p in parts if p[0] != 'opening']


def plan(V, kind):
    """The session: [(what, script, pokes)] in order; what is
    'opening', 'title', ('game', mode, name) or 'end'."""
    return opening_kept(plan_all(V, kind))


def plan_all(V, kind):
    game, _ = V.game_script()
    defeat, dpokes = V.defeat_script()
    # the end screen: FIRE while it does not count yet, PRESS FIRE,
    # the piece of the end to its end (260 passes after the end of
    # the game), FIRE
    end = [0] * 30 + press(F, 4, 70) + [0] * 100 + press(F, 3, 1)
    if kind == 'long':
        title1 = [0] * 40 + press(D) + press(D) + press(D) + press(U) + \
            press(U) + press(U) + press(U | D) + [0] * 10 + press(F, 3, 1)
        return [('opening', keys_script(V, [0] * 200), {}),
                ('title', keys_script(V, title1), {}),
                (('game', P.MODE_MUSIC, 'game'), game, {}),
                ('end', keys_script(V, end), {}),
                ('title', keys_script(V, [0] * 10 + press(D) +
                                      press(F, 3, 1)), {}),
                (('game', P.MODE_FX, 'defeat'), defeat, dpokes),
                ('end', keys_script(V, end), {}),
                ('title', keys_script(V, [0] * 6 + press(D) +
                                      press(F, 3, 1)), {}),
                (('game', P.MODE_SILENT, 'defeat'), defeat, dpokes),
                ('end', keys_script(V, end), {}),
                ('title', keys_script(V, [0] * 40), {})]
    if kind == 'mutation_skip':     # FIRE ends the opening (50 Hz)
        return [('opening', keys_script(V, [0] * 20 + press(F, 3, 1)),
                 {}),
                ('title', keys_script(V, [0] * 10 + press(F, 3, 1)), {}),
                (('game', P.MODE_MUSIC, 'defeat'), defeat, dpokes),
                ('end', keys_script(V, end), {}),
                ('title', keys_script(V, [0] * 40), {})]
    if kind == 'mutation':          # the menu, two short games (50 Hz)
        title1 = [0] * 40 + press(D) + press(D) + press(D) + press(U) + \
            press(U) + press(U) + press(U | D) + [0] * 10 + press(F, 3, 1)
        return [('opening', keys_script(V, [0] * 160), {}),
                ('title', keys_script(V, title1), {}),
                (('game', P.MODE_MUSIC, 'defeat'), defeat, dpokes),
                ('end', keys_script(V, end), {}),
                ('title', keys_script(V, [0] * 10 + press(D) +
                                      press(F, 3, 1)), {}),
                (('game', P.MODE_FX, 'defeat'), defeat, dpokes),
                ('end', keys_script(V, end), {}),
                ('title', keys_script(V, [0] * 40), {})]
    return [('opening', keys_script(V, [0] * 30 + press(F, 3, 1)), {}),
            ('title', keys_script(V, [0] * 20 + press(F, 3, 1)), {}),
            (('game', P.MODE_MUSIC, 'defeat'), defeat, dpokes),
            ('end', keys_script(V, end), {}),
            ('title', keys_script(V, [0] * 20), {})]


_MUTATION_GAMES = {}


def mutation_run(V, rom, sym, cdir, kind='mutation'):
    """A mutated cartridge in the session 'mutation' or
    'mutation_skip' (eu): the problems found, the rules."""
    parts = plan(V, kind)
    script, pokes, starts = flatten(parts)
    state = json.loads((V.BUILD / 'state_eu.json').read_text())
    cb = V.cbios_roms(cdir, 'eu')
    if kind not in _MUTATION_GAMES:
        crom, csym = V.rom_files(V.CARTRIDGE)
        _MUTATION_GAMES[kind] = games_of(V, parts, csym, state, cb, 'eu')
    m, recs, bad, f = walk(V, rom, sym, state, cb, script, pokes,
                           Model(_MUTATION_GAMES[kind], 50))
    return bad, V.rule_checks(m)


def flatten(parts):
    """One script and its pokes; the first pass of each part."""
    script, pokes, starts = [], {}, []
    for what, s, pk in parts:
        starts.append(len(script) + 1)
        for k, lst in pk.items():
            pokes[len(script) + k] = lst
        script += s
    return script, pokes, starts


def game_digest(ram, sym):
    """ram: #C000-#F37F."""
    data = bytearray(ram)
    for name, n in NOT_GAME:
        at = sym[name] - 0xC000
        data[at:at + n] = bytes(n)
    sl = sym['spr_list'] - 0xC000
    used = 4 * ram[sym['spr_count'] - 0xC000]
    data[sl:sl + used] = ram[sl:sl + used]
    d = hashlib.sha1()
    for a, b in GAME_RAM:
        d.update(data[a - 0xC000:b - 0xC000])
    return d.digest()


def play_run(V, rom, sym, state, cb, script, pokes):
    """The tests' cartridge with this script: per pass the digest of
    the game's RAM and the calls of the sound; the game's end."""
    m = msxsim.MSX(rom, state, cb)
    m.watch = {sym[w]: w for w in V.SOUND_MARKS}
    m.marks = V.MarksA(m)
    out, done = [], 0
    for k, (bits, keys, joy) in enumerate(script, 1):
        for name, v in pokes.get(k, ()):
            m.mem[sym[name]] = v
        m.set_input(keys, joy)
        m.run_to(sym['frame_ready'], max_t=40 * m.vdp.frame_t)
        ram = bytes(m.mem[0xC000:0xF380])
        calls = [(n, a) for n, t, a in m.marks[done:]]
        done = len(m.marks)
        out.append((game_digest(ram, sym), calls))
    return out, bytes(m.mem[0xC000:0xF380])


class Model:
    """The states of screens.asm, pass by pass (the game: the tests'
    cartridge and the world model)."""

    def __init__(self, games, hz=50):
        self.games = games          # per game: its plays, end, values
        self.g = -1
        self.state = STATE_OPENING
        self.open_timer = OPENING[hz]
        self.mode = P.MODE_MUSIC
        self.end_timer = self.fire_armed = self.fire_held = 0
        self.stick_held = 0
        self.turn = 0
        self.j = 0                  # the pass of the game
        self.shown = False          # PRESS FIRE on the end screen
        self.appeared = False
        self.changed = False
        # before the first pass: INIT's set_audio (the theme goes on
        # into the title)
        self.pending = [('set_audio', 0)]
        self.sat = [208]                # the opening: no sprite
        self.drawn = None
        if not OPENING_SCREEN:
            # the title at once: INIT's set_audio, then show_title's
            self.state, self.open_timer = STATE_TITLE, 0
            self.pending.append(('set_audio', self.mode))
            self.sat = MS.title_sat(0)  # prepared by show_title

    def fire_released(self, bits):
        fire = bits & F
        if fire == self.fire_held:
            return False
        self.fire_held = fire
        if fire:
            self.fire_armed = 1
            return False
        return bool(self.fire_armed)

    def show_title(self, bits):
        self.state = STATE_TITLE
        self.calls.append(('set_audio', self.mode))
        self.changed = True
        self.fire_armed = 0
        self.stick_held = bits & (U | D)

    def frame(self, bits):
        self.calls, self.pending = self.pending, []
        self.changed, self.appeared = False, False
        self.drawn = self.sat               # put_sprites, at the top
        self.turn = (self.turn + 1) & 255
        if self.state == STATE_OPENING:
            if not self.fire_released(bits):
                self.open_timer -= 1
                if self.open_timer:
                    return
            self.state, self.changed = STATE_TITLE, True
            self.fire_armed = 0             # title_screen: no new
            self.stick_held = bits & (U | D)    # set_audio
            self.sat = MS.title_sat(self.turn)
            return
        if self.state == STATE_TITLE:
            ud = bits & (U | D)
            if ud != self.stick_held:
                self.stick_held = ud
                mode = self.mode
                if ud & U:
                    mode = max(P.MODE_MUSIC, mode - 1)
                elif ud:
                    mode = min(P.MODE_SILENT, mode + 1)
                if ud and mode != self.mode:
                    self.mode = mode
                    self.calls.append(('set_audio', mode))
                    if mode == P.MODE_FX:
                        self.calls.append(('sound_effect', P.SFX['pickup']))
            if self.fire_released(bits):
                self.g += 1
                game = self.games[self.g]
                assert game['mode'] == self.mode, f'the plan: game {self.g} mode {game["mode"]}, menu {self.mode}'
                self.calls.append(('set_audio', self.mode))
                self.state, self.j, self.changed = STATE_PLAY, 0, True
                self.fire_held = self.fire_armed = self.stick_held = 0
                self.end_timer = 0
                self.turn = 0               # vars_init
            else:
                self.sat = MS.title_sat(self.turn)
            return
        if self.state in (STATE_PLAY, STATE_ENDING):
            game = self.games[self.g]
            self.j += 1
            if self.j <= len(game['plays']):
                self.calls = list(game['plays'][self.j - 1][1])
                if self.j == 1:
                    self.calls = self.calls[1:]     # INIT's set_audio
            if self.state == STATE_PLAY:
                if self.j == game['end']:
                    self.state = STATE_ENDING
                    self.end_timer = V_ENDING
                    self.fire_held = game['fire_held']
                return
            self.end_timer -= 1
            if not self.end_timer:
                self.state, self.end_timer = STATE_END, V_DELAY
                self.fire_armed, self.shown, self.changed = 0, False, True
            return
        if self.end_timer:
            self.fire_released(bits)
            self.fire_armed = 0
            self.end_timer -= 1
            if not self.end_timer:
                self.shown = self.appeared = True
            return
        if self.fire_released(bits):
            self.show_title(bits)
            self.sat = MS.title_sat(self.turn)


V_ENDING, V_DELAY = 50, 100


def walk(V, rom, sym, state, cb, script, pokes, model, seed=None,
         capture=()):
    """The session in the bench; returns (machine, recs, problems,
    facts); m.captured: the picture after the passes in capture."""
    m = msxsim.MSX(rom, state, cb, seed=seed)
    m.captured, m.frames = {}, []
    m.watch = {sym[w]: w for w in V.SOUND_MARKS + ('music_init',)}
    se = sym['sound_effect']
    m.watch[rom.index(0xF3, se - 0x4000) + 0x4001] = 'se_held'
    m.marks = V.MarksA(m)
    psg_on, ctrl_on = [], []
    psg_write, psg_read = m.psg.write, m.psg.read

    def psg_w(port, value, t):
        if m.regs[msxsim.IFF_] and not psg_on:
            psg_on.append(f'write #{0xA0 + (port & 3):02X} at T {t}')
        psg_write(port, value, t)

    def psg_r():
        if m.regs[msxsim.IFF_] and not psg_on:
            psg_on.append(f'read #A2 at T {m.tstates}')
        return psg_read()
    m.psg.write, m.psg.read = psg_w, psg_r
    m.psg_on = psg_on
    vdp = m.vdp
    plain = vdp.write

    def logged(port, value, t, pc):
        if port & 1 and m.regs[msxsim.IFF_] and not ctrl_on:
            ctrl_on.append(f'${pc:04X} at T {t}')
        plain(port, value, t, pc)
    vdp.write = logged
    m.ctrl_on = ctrl_on
    hz = state['hz']
    pm = P.PSGMachine(MUSIC_OF(V), hz)
    plog = V.PSGLog(m.psg)
    a = {n: sym[n] - 0xC000 for n in (
        'game_state', 'audio_mode', 'end_timer', 'fire_armed',
        'fire_held', 'turn', 'flame_phase', 'open_timer') if n in sym}
    bad = dict.fromkeys(WHAT)
    recs, facts = [], {'passes': 0, 'screens': 0, 'groups': 0,
                       'ends': []}
    song = None
    irq_done = marks_done = checked = 0
    flush_base = None
    for k, (bits, keys, joy) in enumerate(script, 1):
        for name, v in pokes.get(k, ()):
            m.mem[sym[name]] = v
        m.set_input(keys, joy)
        try:
            m.run_to(sym['frame_ready'], max_t=60 * vdp.frame_t)
        except RuntimeError as e:
            bad['reached'] = f'pass {k}: {e}'
            break
        model.frame(bits)
        ram = bytes(m.mem[0xC000:0xF380])
        vram = bytes(vdp.vram)
        regs = list(vdp.regs)
        recs.append((V.h(ram), V.h(vram), tuple(regs),
                     tuple(m.psg.regs[:14] + m.psg.regs[15:]), m.a8,
                     m.tstates))
        got = (ram[a['game_state']], ram[a['audio_mode']],
               ram[a['end_timer']], ram[a['fire_armed']],
               ram[a['fire_held']], ram[a['turn']], regs[1])
        want = (model.state, model.mode, model.end_timer,
                model.fire_armed, model.fire_held, model.turn, 0xE2)
        if 'open_timer' in a:           # (not in step 07)
            got += (ram[a['open_timer']],)
            want += (model.open_timer,)
        if model.state in (STATE_PLAY, STATE_ENDING):
            # the game's own: from the tests' cartridge
            got, want = got[:3] + got[5:], want[:3] + want[5:]
        if bad['states'] is None and got != want:
            bad['states'] = f'pass {k}: {got}, model {want}'
        # -- the screens
        if model.state in (STATE_TITLE, STATE_END, STATE_OPENING):
            plain_vram = bytearray(vram)
            plain_vram[0x1B00] = 208
            back = [[c or 1 for c in r] for r in
                    V.vram2png.indices(bytes(plain_vram), regs)]
            phase = 0 if model.changed else ram[a['flame_phase']] >> 3
            if model.state == STATE_OPENING:
                want_pic = MS.picture('opening')
                want_sat = [208]
            elif model.state == STATE_TITLE:
                want_pic = MS.picture('title', model.mode, phase,
                                      MS.pulse(model.turn))
                want_sat = [208] if model.changed else model.drawn
            else:
                game = model.games[model.g]
                role = 'hud' if model.appeared else MS.pulse(model.turn)
                want_pic = MS.picture('end', 0, phase, role,
                                      game['won'], game['score'],
                                      game['seals'], game['rooms'],
                                      model.shown)
                want_sat = [208]
            facts['screens'] += 1
            d = V.first_diff(back, want_pic)
            if d and bad['screen'] is None:
                bad['screen'] = f'pass {k} (state {model.state}): ' \
                                f'pixel {d}'
            sat = list(vram[0x1B00:0x1B00 + len(want_sat)])
            if sat != want_sat and bad['sprites'] is None:
                bad['sprites'] = f'pass {k}: {sat}, model {want_sat}'
        elif model.state in (STATE_PLAY, STATE_ENDING):
            game = model.games[model.g]
            if 1 <= model.j <= len(game['plays']) and \
                    bad['game'] is None \
                    and game_digest(ram, sym) != \
                    game['plays'][model.j - 1][0]:
                bad['game'] = f'pass {k}: pass {model.j} of game ' \
                              f'{model.g + 1}'
        # -- the sound: the calls, then the PSG
        marks = [x for x in m.marks[marks_done:]
                 if x[0] in V.SOUND_MARKS + ('se_held', 'music_init')]
        marks_done = len(m.marks)
        got_calls = [(n, aa) for n, t, aa in marks
                     if n in V.SOUND_MARKS]
        if bad['calls'] is None and got_calls != model.calls:
            bad['calls'] = f'pass {k}: {got_calls}, model {model.calls}'
        events = []
        for i, (n, t, aa) in enumerate(marks):
            if n not in V.SOUND_MARKS:
                continue
            # when it takes effect: an effect after the DI, a piece
            # in music_init (with the interrupt held off)
            then = {'sound_effect': 'se_held',
                    'end_sound': 'music_init'}.get(n)
            if then:
                t = next((tt for nn, tt, x in marks[i + 1:]
                          if nn == then), t)
            events.append((t, 1, n, aa))
        events += [(t, 0, 'irq', 0) for t in m.irq_log[irq_done:]]
        irq_done = len(m.irq_log)
        for t, _, n, aa in sorted(events):
            if n == 'irq':
                pm.interrupt()
            elif n == 'set_audio':
                if song in ('won', 'lost'):     # how the end went
                    last = [g for g, kd in zip(pm.flushes, pm.kinds)
                            if kd == 'music'][-1]
                    facts['ends'].append([song, pm.player.frames,
                                          sum(last[8:11])])
                song = 'theme' if aa == P.MODE_MUSIC else None
                pm.set_audio(aa)
            elif n == 'end_sound':
                if pm.mode == P.MODE_MUSIC:
                    song = 'won' if aa == V.W.ENDED_WON else 'lost'
                    pm.song(song)
            else:
                pm.sfx(aa)
        plog.update()
        n0 = len(plog.groups)
        if bad['psg'] is None:
            j = next((i for i in range(checked, min(n0, len(pm.flushes)))
                      if plog.groups[i][1] != pm.flushes[i]), None)
            if j is None and n0 != len(pm.flushes):
                j = min(n0, len(pm.flushes))
            if j is not None:
                bad['psg'] = f'pass {k}: group {j}' + (
                    f': {plog.groups[j][1]}, model {pm.flushes[j]} '
                    f'({pm.kinds[j]})' if j < n0 and j < len(pm.flushes)
                    else f'; {n0} groups, model {len(pm.flushes)}')
            checked = n0
        for j in range(facts['groups'], n0):
            if j < len(pm.kinds) and pm.kinds[j] == 'music':
                tg = plog.groups[j][0]
                i = V.bisect.bisect_right(m.irq_log, tg) - 1
                dt = tg - m.irq_log[i] if i >= 0 else None
                if flush_base is None:
                    flush_base = dt
                if dt != flush_base and bad['psg_time'] is None:
                    bad['psg_time'] = f'pass {k}: {dt} T, not ' \
                                      f'{flush_base}'
        facts['groups'] = n0
        facts['passes'] = k
        m.frames.append(ram[0] | ram[1] << 8)
        if k in capture:
            m.captured[k] = V.screen_of(vram, regs)
    facts['flush_after_interrupt'] = flush_base
    m.pm, m.plog = pm, plog
    return m, recs, bad, facts


def MUSIC_OF(V):
    return V.MUSIC


def games_of(V, parts, sym_play, state, cb, mname):
    """The model's games: for each game of the plan, its run in the
    tests' cartridge of its mode, its end (world model), its values."""
    out = []
    for what, script, pokes in parts:
        if what[0] != 'game':
            continue
        mode, name = what[1], what[2]
        rom, sym = V.rom_files(V.GAMES[mode])
        plays, last = play_run(V, rom, sym, state, cb, script, pokes)
        model = V.model_end(script, pokes, V.GAME_ROOM)
        end = V.end_pass(script, pokes)
        rooms = set()
        world = W.World(V.GAME_ROOM)
        for k, (bits, keys, joy) in enumerate(script, 1):
            for n, v in pokes.get(k, ()):
                V.poke_model(world, n, v)
            world.update(bits)
            rooms.add(world.room)
            if k == end:
                break
        out.append({'mode': mode, 'name': name, 'plays': plays,
                    'end': end, 'won': model.ended == W.ENDED_WON,
                    'score': model.score, 'seals': model.seals,
                    'rooms': len(rooms),
                    'fire_held': last[sym['fire_held'] - 0xC000]})
    return out


def seeds_check(V, checks, f, tag, rom, sym, state, cb, script, pokes,
                games):
    """The session again with the RAM filled at random (seeds 1, 2):
    the same states, screens, sprites, sound and rules (each game's
    RAM is compared with the tests' cartridge only without a filling:
    the unused bytes between the variables keep the filling); then
    every byte written is in the areas of vars.asm or the stack."""
    lasts, bad = {}, []
    for seed in (1, 2):
        m, recs, b, fs = walk(V, rom, sym, state, cb, script, pokes,
                              Model(games, state['hz']), seed=seed)
        lasts[seed] = bytes(m.mem[0xC000:0xF380])
        bad += [f'seed {seed}: {w}: {e}' for w, e in b.items()
                if e and w != 'game']
        bad += [f'seed {seed}: {w}: {e}'
                for w, e in V.rule_checks(m).items() if e]
    outside, depth = V.ram_check(lasts)
    f['stack_depth'] = depth
    checks.add(f'{tag}: with the RAM filled at random (seeds 1, 2) the '
               'same states, screens, sprites, sound and rules; RAM '
               'written only in the areas of vars.asm and the stack',
               not bad and not outside and 0 < depth <= V.STACK_ROOM,
               bad[0] if bad else
               f'outside {[hex(a) for a in outside[:4]]}' if outside
               else f'stack {depth} bytes')


def sessions(V, openmsx, cdir, checks, facts, png, kinds=('long', 'short'),
             machines=None):
    rom, sym = V.rom_files(V.CARTRIDGE)
    for kind in kinds:
        parts = plan(V, kind)
        script, pokes, starts = flatten(parts)
        # the pictures kept, and taken by openMSX: the title, the end
        # screen. openMSX's screenshot at a frame_ready shows a picture
        # of a few frames before (measured: 2 to 4; its frame skip):
        # it must be one of the bench's pictures of the last 6 passes
        windows = {'long': {100: 'opening', 220: 'title',
                            starts[3] + 111: 'end_won'},
                   'short': {starts[3] + 111: 'end_lost',
                             starts[4] + 10: 'title_again'}}[kind]
        capture = {k + i for k in windows for i in range(-6, 3)}
        for mname, (machine, hz) in V.MACHINES.items():
            if machines and mname not in machines:
                continue
            tag = f'{mname} ({hz} Hz) session {kind}'
            state = json.loads((V.BUILD / f'state_{mname}.json')
                               .read_text())
            cb = V.cbios_roms(cdir, mname)
            games = games_of(V, parts, sym, state, cb, mname)
            m, recs, bad, f = walk(V, rom, sym, state, cb, script, pokes,
                                   Model(games, hz), capture=capture)
            pal = V.vram2png.palette(hz)
            shots = dict(windows)
            for k, name in shots.items():
                rows = [[tuple(pal[c]) for c in r] for r in m.captured[k]]
                (png / f'{name}_{hz}hz.png').write_bytes(
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
            speed = V.MUSIC['speed_50' if hz == 50 else 'speed_60']
            whole = [e for e in f['ends'] if e[1] >=
                     V.MUSIC['songs'][e[0]]['steps'] * speed and not e[2]]
            checks.add(f'{tag}: the piece of the end (MUSIC) played to '
                       'its end, then silence, until the title',
                       len(f['ends']) == 1 and whole == f['ends'],
                       str(f['ends']))
            if kind == 'short':
                seeds_check(V, checks, f, tag, rom, sym, state, cb, script,
                            pokes, games)
            if not openmsx:
                continue
            rd = V.RUNS / f'session_{kind}_{mname}'
            g = 0 if kind == 'long' else 0
            start = starts[2] + games[g]['end'] - 1
            wav_name = ('victory' if kind == 'long' else 'defeat') + \
                f'_{hz}hz.wav'
            r = V.emu_run(openmsx, V.BUILD / f'{V.CARTRIDGE}.rom', sym,
                          mname, len(script), rd, script=script,
                          pokes=pokes, lazy=True, psg_log=True,
                          wav=(V.WAVS / wav_name, start - 50),
                          shots=sorted(shots))
            sbad, hashes = [], {}
            for k in sorted(set(shots) | {k + 2 for k in shots}):
                sp = rd / f'shot_{k}.png'
                if not sp.exists():
                    sbad.append(f'shot_{k}.png missing')
                    continue
                errs = [V.shot_ok(sp, m.captured[kk], hz)
                        for kk in range(k - 6, k + 1)]
                if all(errs):
                    sbad.append(errs[-1])
                hashes[str(k)] = V.shot_hash(sp)
            facts.setdefault('openmsx', {})[
                f'session_{kind}_{mname}'] = hashes
            checks.add(f'{tag}: openMSX\'s screenshots of the title and '
                       f'the end screen ({", ".join(shots.values())}, two '
                       'frames each) = one of the bench\'s last pictures, '
                       'every pixel',
                       not sbad, sbad[0] if sbad else
                       f'{len(hashes)} screenshots')
            diff = V.emu_compare(recs, r['frames'])
            same, n_irq = V.emu_irq_same(m, r)
            psame, pdet = V.psg_writes_same(m, r)
            checks.add(f'{tag}: bench = openMSX, every pass, interrupts '
                       'at the same T-states, every write to the PSG the '
                       'same, at the same T-state',
                       diff is None and same and
                       n_irq == len(m.irq_log) and psame and
                       not r['too_fast'] and not r['psg_directions'],
                       diff or f'{len(recs)} passes, {n_irq} interrupts, '
                       + pdet)
            t0 = r['wav_from'] or 0
            fg = [x for x in V.frame_groups(r) if x[0] >= t0]
            samples, rate = V.read_wav(V.WAVS / wav_name)
            hd = V.heard(samples, rate, [t for t, gg in fg], t0,
                         [gg for t, gg in fg])
            facts[f'session_{kind}_{mname}']['openmsx_sound'] = \
                dict(hd, file=wav_name)
            checks.add(f'{tag}: openMSX\'s sound from pass {start - 50} '
                       f'({wav_name}): the loudness of every frame '
                       'follows the registers',
                       hd['loudness_correlation'] >= 0.75, str(hd))
            del r

"""The Cryptmorrow music and sound effects, made for the Spectrum.

The notes come unchanged from the C64 game: c64/score.py (the theme,
the two pieces of the end, instruments and wave tables) and c64/sfx.py
(eight effects), as they were written. This file turns them into the
data of two players:

- player.asm, on the AY (128K, or a 48K with an AY interface): three
  square-wave channels and one noise generator. The SID's waveforms
  become a choice per frame between tone and noise; its envelopes
  (attack, decay, sustain, release) become tables of volumes, one per
  frame, worked out here from the AD and SR bytes; the vibrato of the
  lead becomes a period offset of one unit. The pulse-width sweeps of
  the SID have no equivalent and are left out.
- beeper.asm, on the 48K without an AY: the effects, one slice of
  sound per frame (BEEP_SLICE T-states), a square wave for the tones
  and a pseudo-random sequence for the noise. A note too low for a
  whole period to fit in a slice goes up an octave at a time.
- player.asm again, in SOUND FX mode with an AY: the
  effects on channel A, one entry a frame. As on the C64 an effect
  starts with a frame with the gate off (here: silent), then its
  notes at the volumes of its envelope (AD and SR, as for the
  instruments), then the release; after the first frame of the
  release the effect no longer holds its priority (the C64 effect
  ends there, and the SID's release goes on by itself).

Byte formats (as in the C64 player, and documented again in
game/src/player.asm):
  pattern   $00-$5f note (C0 = 0), $60 rest, $80-$bf length
            (value - $7f steps), $c0-$df instrument, $ff end
  order     $00-$7f pattern, $80-$bf transpose (value - $a0),
            $ff n: continue from entry n
  wave      control and argument per frame: control 1 tone, 2 noise,
            $fe hold the last entry, $ff n jump to entry n; argument,
            for a tone, $00-$7f semitones above the note or $80 + n
            the fixed note n; for noise, the noise period (1-31)
  envelope  volumes 0-15 per frame, $ff: hold the previous one
  effects   per frame: mode (1 tone, 2 noise, 0 end), delay, count
  AY effects per frame: control (bits 0-3 volume, bit 4 noise, bit 5
            the release goes on without the priority; $FF end) and
            argument (note 0-95 for a tone, noise period for noise)

Use: build() -> (asm lines, data for the model); BEEP_SLICE can be
given to build() for the listening variants of the laboratory.
Standard library only.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'c64'))
import score  # noqa: E402  (c64/score.py, unchanged)
import sfx  # noqa: E402    (c64/sfx.py, unchanged)

AY_CLOCK = 1773400            # 128K: 3 546 900 / 2 (Fuse, SkoolKit)
CPU_48 = 3500000              # beeper timing, 48K
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A',
              'A#', 'B']
NOTES = 96                    # C0-B7; $60 is the rest
REST, LENGTH, INSTRUMENT, END = 0x60, 0x80, 0xC0, 0xFF
TRANSPOSE_ZERO, ORDER_LOOP = 0xA0, 0xFF
WAVE_TONE, WAVE_NOISE, WAVE_HOLD, WAVE_LOOP = 1, 2, 0xFE, 0xFF
WAVE_FIXED = 0x80
ENV_HOLD = 0xFF
NO_VIBRATO = 0xFF
FX_TONE, FX_NOISE, FX_END = 1, 2, 0
AYFX_NOISE, AYFX_TAIL, AYFX_STOP = 0x10, 0x20, 0xFF
NOISE_DIVIDE = 8              # noise period = tone period / 8

# The SID's envelope times (ms), by the nibble of AD and SR.
ATTACK_MS = [2, 8, 16, 24, 38, 56, 68, 80, 100, 250, 500, 800, 1000,
             3000, 5000, 8000]
DECAY_MS = [6, 24, 48, 72, 114, 168, 204, 240, 300, 750, 1500, 2400,
            3000, 9000, 15000, 24000]
FRAME_MS = 20
# The AY's 16 volume levels as amplitudes (logarithmic DAC, about
# 3 dB a step; the table of the AY-3-8910 used by emulators).
AY_LEVELS = [0.0, 0.00999, 0.01445, 0.02106, 0.03070, 0.04555,
             0.06450, 0.10736, 0.12659, 0.20499, 0.29221, 0.37284,
             0.49253, 0.63532, 0.80558, 1.0]
# Vibrato: a period offset per frame, eight frames a cycle (6.25 Hz,
# the C64's triangle), one unit up and down.
VIBRATO = [-1, -1, -1, 0, 1, 1, 1, 0]

# The beeper loops of beeper.asm, in T-states without contention:
# one pass of the loop is BASE + 13 * delay + 2 (LD B,n and DJNZ).
TONE_BASE = 39
NOISE_BASE = 74
BEEP_SLICE = 7000             # T-states of sound per frame: 2 ms


def note_number(name):
    """'C#4' -> 49. Octaves 0-7, C0 = 0."""
    pitch, octave = name[:-1], int(name[-1])
    if pitch not in NOTE_NAMES:
        raise ValueError(f'unknown note {name}')
    return octave * 12 + NOTE_NAMES.index(pitch)


def hertz(number):
    return 440.0 * 2 ** ((number - 57) / 12)


def tone_period(number):
    """AY tone period of a note, or 0 if out of the 12-bit range."""
    p = round(AY_CLOCK / (16 * hertz(number)))
    return p if 1 <= p <= 4095 else 0


def noise_period(number):
    """AY noise period (1-31) for a SID noise note."""
    p = round(AY_CLOCK / (16 * hertz(number)) / NOISE_DIVIDE)
    return max(1, min(31, p))


def level(amplitude):
    """The AY volume level nearest to an amplitude (0-1)."""
    return min(range(16), key=lambda v: abs(AY_LEVELS[v] - amplitude))


def envelope(ad, sr):
    """The volumes of an instrument, frame by frame.

    on: from the start of a note: the attack (amplitude rising
    linearly, as on the SID), then the decay to the sustain level
    (falling linearly in volume steps, that is exponentially, as the
    SID's decay sounds), then held. rel: the release from 15 to 0.
    start[v]: where the release goes on from volume v (the first
    entry not louder than v)."""
    attack = round(ATTACK_MS[ad >> 4] / FRAME_MS)
    decay = DECAY_MS[ad & 15] / FRAME_MS
    sustain = level((sr >> 4) / 15)
    release = DECAY_MS[sr & 15] / FRAME_MS
    on = [level(k / attack) for k in range(1, attack)] if attack else []
    t = 0
    while True:
        v = max(sustain, round(15 - 15 * t / decay))
        on.append(v)
        if v == sustain:
            break
        t += 1
    rel = []
    t = 1
    while True:
        v = max(0, round(15 - 15 * t / release))
        rel.append(v)
        if v == 0:
            break
        t += 1
    start = [next(i for i, x in enumerate(rel) if x <= v)
             for v in range(16)]
    return on, rel, start


def compile_waves():
    data, starts = [], {}
    for name, entries in score.WAVES.items():
        starts[name] = len(data)
        for entry in entries:
            if entry == 'end':
                data.append((WAVE_HOLD, 0))
            elif entry.startswith('loop'):
                data.append((WAVE_LOOP,
                             starts[name] + int(entry.split()[1])))
            else:
                control, argument = entry.split()
                if int(control, 16) & 0x80:          # SID noise
                    data.append((WAVE_NOISE,
                                 noise_period(note_number(argument))))
                elif argument[0] in '+-':
                    offset = int(argument)
                    if not 0 <= offset < 0x80:
                        raise ValueError(f'{name}: offset {offset}')
                    data.append((WAVE_TONE, offset))
                else:
                    data.append((WAVE_TONE,
                                 WAVE_FIXED + note_number(argument)))
    if len(data) > 250:
        raise ValueError('wave tables too long')
    return data, starts


def compile_pattern(name, text, instruments):
    data, length, steps = [], None, 0
    for token in text.split():
        if token.startswith('@'):
            data.append(INSTRUMENT + instruments.index(token[1:]))
            continue
        pitch, count = token.split('/')
        count = int(count)
        if not 1 <= count <= 64:
            raise ValueError(f'{name}: length {count}')
        if count != length:
            data.append(LENGTH + count - 1)
            length = count
        data.append(REST if pitch == 'r' else note_number(pitch))
        steps += count
    return data + [END], steps


def compile_orders(song, names, steps):
    orders, lengths = [], []
    for items in score.SONGS[song]['orders']:
        data, total = [], 0
        for item in items:
            if item == 'stop':
                data += [names.index('silence'), ORDER_LOOP, len(data)]
                break
            if item.startswith('t'):
                data.append(TRANSPOSE_ZERO + int(item[1:]))
            else:
                data.append(names.index(item))
                total += steps[item]
        else:
            data += [ORDER_LOOP, 0]
        orders.append(data)
        lengths.append(total)
    if len(set(lengths)) != 1:
        raise ValueError(f'{song}: voices of different lengths')
    if lengths[0] != score.SONGS[song]['bars'] * 16:
        raise ValueError(f'{song}: {lengths[0]} steps')
    return orders, lengths[0]


def beeper_effects(slice_t):
    """Per frame of each effect: (mode, delay, count). count passes
    of the loop fill about slice_t T-states; a pass lasts half a
    period of the note (tone) or one random level (noise)."""
    entries, first = [(FX_END, 0, 0)], []
    for name, effect in sfx.EFFECTS.items():
        first.append(len(entries))
        for item in effect['frames'].split(','):
            wave, note = item.split()
            mode = FX_NOISE if int(wave, 16) & 0x80 else FX_TONE
            base = NOISE_BASE if mode == FX_NOISE else TONE_BASE
            n = note_number(note)
            while True:     # a whole period must fit in a slice
                half = CPU_48 / (2 * hertz(n))
                delay = round((half - base - 2) / 13)
                if delay <= 255 and 2 * half <= slice_t:
                    break
                n += 12     # too low for a slice: an octave up
            delay = max(1, delay)
            passes = base + 13 * delay + 2
            count = max(1, min(255, slice_t // passes))
            entries.append((mode, delay, count))
        entries.append((FX_END, 0, 0))
    if len(entries) > 255:
        raise ValueError('effects too long')
    return entries, first


def ay_effects():
    """The effects for the AY, frame by frame: (control, argument).
    Entry 0 is unused (sfx_pos 0 means no effect)."""
    entries, first = [(AYFX_STOP, 0)], []
    for name, effect in sfx.EFFECTS.items():
        first.append(len(entries))
        on, rel, start = envelope(effect['ad'], effect['sr'])
        frames = []
        for item in effect['frames'].split(','):
            wave, note = item.split()
            frames.append((int(wave, 16) & 0x80 != 0, note_number(note)))

        def entry(noise, note, volume, tail=False):
            ctrl = volume | (AYFX_NOISE if noise else 0) | \
                (AYFX_TAIL if tail else 0)
            return ctrl, noise_period(note) if noise else note
        entries.append(entry(*frames[0], 0))        # the gate off
        volume = 0
        for k, (noise, note) in enumerate(frames):
            volume = on[min(k, len(on) - 1)]
            entries.append(entry(noise, note, volume))
        noise, note = frames[-1]
        for k, v in enumerate(rel[start[volume]:]):  # the release
            entries.append(entry(noise, note, v, tail=k > 0))
        entries.append((AYFX_STOP, 0))
    if len(entries) > 256:
        raise ValueError('AY effects longer than 256 frames in all')
    for ctrl, arg in entries:
        if ctrl != AYFX_STOP and not ctrl & AYFX_NOISE and \
                not tone_period(arg):
            raise ValueError(f'AY effect note {arg}: no period')
    return entries, first


def hexbytes(values):
    return ','.join(f'${v & 255:02X}' for v in values)


def table(label, values, per=10, comment=''):
    lines = [f'{label}:' + (f'  ; {comment}' if comment else '')]
    for i in range(0, len(values), per):
        lines.append('        db ' + hexbytes(values[i:i + per]))
    return lines


def words(label, values, per=6, comment=''):
    lines = [f'{label}:' + (f'  ; {comment}' if comment else '')]
    for i in range(0, len(values), per):
        lines.append('        dw ' + ','.join(str(v) for v in
                                              values[i:i + per]))
    return lines


def build(slice_t=BEEP_SLICE):
    instruments = list(score.INSTRUMENTS)
    waves, starts = compile_waves()
    names = list(score.PATTERNS)
    patterns, steps = {}, {}
    for name, text in score.PATTERNS.items():
        patterns[name], steps[name] = compile_pattern(name, text,
                                                      instruments)
    songs = {s: compile_orders(s, names, steps) for s in score.SONGS}
    env_data, ins = [], []
    for name in instruments:
        i = score.INSTRUMENTS[name]
        on, rel, start = envelope(i['ad'], i['sr'])
        on_at = len(env_data)
        env_data += on + [ENV_HOLD]
        rel_at = len(env_data)
        env_data += rel + [ENV_HOLD]
        delay, depth = i['vib']
        ins.append({'name': name, 'wave': starts[i['wave']],
                    'env': on_at, 'rel': rel_at, 'rel_start': start,
                    'vib': delay if depth else NO_VIBRATO,
                    'on': on, 'release': rel})
    if len(env_data) > 255:
        raise ValueError('envelopes too long')
    periods = [tone_period(n) for n in range(NOTES)]
    fx, fx_first = beeper_effects(slice_t)
    ayfx, ayfx_first = ay_effects()

    lines = ['; music.asm - made by game/assets/ay_music.py from',
             '; c64/score.py and c64/sfx.py (the C64 game).',
             '; Do not edit: run the builder again.', '',
             f'MUSIC_SPEED equ {score.SPEED}       ; frames a step',
             f'GATE_TICK   equ {score.GATE_TICK}       ; release here',
             f'NOTE_REST   equ ${REST:02X}',
             f'CMD_LENGTH  equ ${LENGTH:02X}',
             f'CMD_INSTR   equ ${INSTRUMENT:02X}',
             f'PAT_END     equ ${END:02X}',
             f'ORDER_LOOP  equ ${ORDER_LOOP:02X}',
             f'TRANS_ZERO  equ ${TRANSPOSE_ZERO:02X}',
             f'WAVE_TONE   equ {WAVE_TONE}',
             f'WAVE_NOISE  equ {WAVE_NOISE}',
             f'WAVE_HOLD   equ ${WAVE_HOLD:02X}',
             f'WAVE_LOOP   equ ${WAVE_LOOP:02X}',
             f'ENV_HOLD    equ ${ENV_HOLD:02X}',
             f'NO_VIBRATO  equ ${NO_VIBRATO:02X}',
             f'FX_TONE     equ {FX_TONE}',
             f'FX_NOISE    equ {FX_NOISE}',
             f'BEEP_SLICE  equ {slice_t}    ; T-states a frame',
             f'AYFX_NOISE  equ ${AYFX_NOISE:02X}         ; AY effects',
             f'AYFX_TAIL   equ ${AYFX_TAIL:02X}',
             f'AYFX_STOP   equ ${AYFX_STOP:02X}']
    lines += [f'SONG_{s.upper():<7} equ {n}'
              for n, s in enumerate(score.SONGS)]
    lines += [f'SFX_{e.upper():<7} equ {n + 1}'
              for n, e in enumerate(sfx.EFFECTS)]
    lines.append('')
    lines += words('note_period', periods, 8, 'AY tone period of'
                   ' notes 0-95')
    lines += table('ins_wave', [i['wave'] for i in ins], 10,
                   'instrument: wave table')
    lines += table('ins_env', [i['env'] for i in ins], 10,
                   'volumes of a note')
    lines += table('ins_rel', [i['rel'] for i in ins], 10,
                   'volumes of the release')
    lines += table('ins_vib', [i['vib'] for i in ins], 10,
                   'vibrato after n frames')
    lines.append('rel_start:  ; release entry from volume 0-15')
    for i in ins:
        lines.append('        db ' + hexbytes(i['rel_start'][:8]))
        lines.append('        db ' + hexbytes(i['rel_start'][8:]))
    lines += table('env_data', env_data, 12)
    lines += table('vib_offset', VIBRATO, 8, 'period, a cycle')
    lines += table('wave_ctrl', [c for c, _ in waves], 12)
    lines += table('wave_arg', [a for _, a in waves], 12)
    lines += words('pat_addr', [f'pat_{n}' for n in names], 3)
    lines.append('song_orders:  ; three order lists a song')
    for s in songs:
        lines.append('        dw ' + ','.join(f'ord_{s}_{v + 1}'
                                              for v in range(3)))
    for s, (orders, _) in songs.items():
        for v, data in enumerate(orders):
            lines += table(f'ord_{s}_{v + 1}', data, 12)
    for n in names:
        lines += table(f'pat_{n}', patterns[n], 12)
    lines += table('sfx_first', fx_first, 10, 'effects 1-8')
    lines += table('sfx_mode', [e[0] for e in fx], 12)
    lines += table('sfx_delay', [e[1] for e in fx], 12)
    lines += table('sfx_count', [e[2] for e in fx], 12)
    prio = [e['priority'] for e in sfx.EFFECTS.values()]
    lines += table('sfx_priority', prio, 10, 'effects 1-8')
    lines += table('ayfx_first', ayfx_first, 10, 'AY effects 1-8')
    lines.append('ayfx_data:  ; control, argument a frame')
    flat = [v for e in ayfx for v in e]
    for i in range(0, len(flat), 12):
        lines.append('        db ' + hexbytes(flat[i:i + 12]))

    size = (2 * NOTES + 4 * len(ins) + 16 * len(ins) + len(env_data)
            + len(VIBRATO) + 2 * len(waves) + 2 * len(names)
            + 6 * len(songs)
            + sum(len(o) for orders, _ in songs.values() for o in orders)
            + sum(len(p) for p in patterns.values())
            + len(fx_first) + 3 * len(fx) + len(prio)
            + len(ayfx_first) + 2 * len(ayfx))
    model = {'speed': score.SPEED, 'gate_tick': score.GATE_TICK,
             'periods': periods,
             'instruments': [{k: i[k] for k in ('name', 'wave', 'env',
                                                'rel', 'rel_start',
                                                'vib')} for i in ins],
             'env_data': env_data, 'vibrato': VIBRATO,
             'waves': waves, 'pattern_names': names,
             'patterns': [patterns[n] for n in names],
             'songs': {s: {'orders': o, 'steps': n}
                       for s, (o, n) in songs.items()},
             'song_numbers': list(score.SONGS),
             'sfx_names': list(sfx.EFFECTS), 'sfx_first': fx_first,
             'sfx_priority': prio,
             'sfx': [list(e) for e in fx], 'beep_slice': slice_t,
             'ayfx': [list(e) for e in ayfx], 'ayfx_first': ayfx_first,
             'beeper_loop': {'tone_base': TONE_BASE,
                             'noise_base': NOISE_BASE},
             'bytes': size}
    return lines, model


def played_notes(model):
    """Every tone note the songs can play (with transpositions and
    wave offsets): each must have a period."""
    notes = set()
    for song in model['songs'].values():
        for v, order in enumerate(song['orders']):
            trans = 0
            for b in order:
                if b == ORDER_LOOP:
                    break
                if b >= LENGTH:
                    trans = b - TRANSPOSE_ZERO
                    continue
                instr = None
                for x in model['patterns'][b]:
                    if x >= INSTRUMENT and x != END:
                        instr = x - INSTRUMENT
                    elif x < REST:
                        wave = model['instruments'][instr]['wave']
                        for c, a in model['waves'][wave:]:
                            if c in (WAVE_HOLD, WAVE_LOOP):
                                break
                            if c == WAVE_TONE:
                                notes.add(a - WAVE_FIXED if a >=
                                          WAVE_FIXED else x + trans + a)
    return sorted(notes)


if __name__ == '__main__':
    lines, model = build()
    notes = played_notes(model)
    bad = [n for n in notes if not model['periods'][n]]
    print(f"{model['bytes']} bytes; notes {notes[0]}-{notes[-1]};"
          f' out of range: {bad}')

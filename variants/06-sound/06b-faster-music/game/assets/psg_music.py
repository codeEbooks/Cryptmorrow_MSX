"""The Cryptmorrow music and sound effects on the PSG of the MSX.

The notes are those of the C64 game, unchanged (c64/score.py: the
theme, the two pieces of the end, instruments and wave tables;
c64/sfx.py: the eight effects), as Cryptmorrow ZX made them into the
data of its AY player: ay_music.py, copied from the ZX unchanged, does
the work (patterns, order lists, wave tables, the envelopes of the
SID worked out frame by frame, the effects of channel A). The PSG of
the MSX is the same chip as the AY of the 128K (the AY-3-8910, or
Yamaha's YM2149 in the C-BIOS machines of openMSX); what changes:

- the clock: 3 579 545 / 2 = 1 789 772.5 Hz instead of the 128K's
  1 773 400: the tone periods round(1789772.5 / (16 f)) and the noise
  periods of the drums and of the effects are worked out again;
- the speed: SPEED frames a step at 50 Hz, as on the C64 and the ZX
  (125 beats a minute), SPEED_60 = round(SPEED x 60 / 50) at 60 Hz
  (128.6): the program chooses by bit 7 of the BIOS byte #002B
  (approved by the author on 8 November); the release of the last
  step of a note starts GATE_BEFORE frames before the step ends, at
  both speeds (the ZX's GATE_TICK, 4 of 6);
- no beeper: the effects play only on channel A of the PSG;
- from milestone 0.6.1 (the author, after the hand test of 0.6: "the
  sounds seem to come a little late") the effects start with
  their first note: the C64's first frame with the gate off, which
  ay_effects() keeps (the SID restarts its envelope there; on the
  AY of the ZX it is a silent frame), is left out. The PSG's volumes
  are given frame by frame and need no restart; the effect sounds a
  frame sooner.

Writes nothing itself: build() -> (asm lines, data for the model);
tools/build_game.py writes game/assets/generated/B/music.asm and
music.json. Standard library only.
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'c64'))
import ay_music as A  # noqa: E402  (from Cryptmorrow ZX, unchanged)
import score  # noqa: E402            (c64/score.py, unchanged)
import sfx  # noqa: E402              (c64/sfx.py, unchanged)

PSG_CLOCK = 3579545 / 2          # 1 789 772.5 Hz
SPEED_50 = score.SPEED           # frames a step, 50 Hz
SPEED_60 = round(score.SPEED * 60 / 50)
GATE_BEFORE = score.SPEED - score.GATE_TICK


def without_gate(fx, first):
    """The effects without their first entry, the frame with the
    gate off (volume 0, the release not begun): (entries, first
    entry of each)."""
    gates = set(first)
    for f in first:
        ctrl, arg = fx[f]
        if ctrl == A.AYFX_STOP or ctrl & 15 or ctrl & A.AYFX_TAIL:
            raise ValueError(f'entry {f} is not a gate off')
    out, new_first, moved = [], [], {}
    for i, e in enumerate(fx):
        if i in gates:
            continue
        moved[i] = len(out)
        out.append(e)
    new_first = [moved[f + 1] for f in first]
    return out, new_first


def build():
    A.AY_CLOCK = PSG_CLOCK       # ay_music's periods, MSX clock
    if GATE_BEFORE != 1 or SPEED_60 != 6:
        raise ValueError('the speeds of this variant: 5 and 6, gate 1')
    instruments = list(score.INSTRUMENTS)
    waves, starts = A.compile_waves()
    names = list(score.PATTERNS)
    patterns, steps = {}, {}
    for name, text in score.PATTERNS.items():
        patterns[name], steps[name] = A.compile_pattern(
            name, text, instruments)
    songs = {s: A.compile_orders(s, names, steps) for s in score.SONGS}
    env_data, ins = [], []
    for name in instruments:
        i = score.INSTRUMENTS[name]
        on, rel, start = A.envelope(i['ad'], i['sr'])
        on_at = len(env_data)
        env_data += on + [A.ENV_HOLD]
        rel_at = len(env_data)
        env_data += rel + [A.ENV_HOLD]
        delay, depth = i['vib']
        ins.append({'name': name, 'wave': starts[i['wave']],
                    'env': on_at, 'rel': rel_at, 'rel_start': start,
                    'vib': delay if depth else A.NO_VIBRATO})
    if len(env_data) > 255:
        raise ValueError('envelopes too long')
    periods = [A.tone_period(n) for n in range(A.NOTES)]
    fx, fx_first = without_gate(*A.ay_effects())
    prio = [e['priority'] for e in sfx.EFFECTS.values()]

    lines = ['; music.asm - made by game/assets/psg_music.py from',
             '; c64/score.py and c64/sfx.py (the C64 game), for the',
             '; PSG of the MSX (1 789 772.5 Hz). Do not edit: run',
             '; tools/build_game.py --assets again.', '',
             f'SPEED_50    equ {SPEED_50}       ; frames a step, 50 Hz',
             f'SPEED_60    equ {SPEED_60}       ; frames a step, 60 Hz',
             f'GATE_BEFORE equ {GATE_BEFORE}       ; release: frames'
             ' before',
             '                            ; the end of the last step',
             f'NOTE_REST   equ ${A.REST:02X}',
             f'CMD_LENGTH  equ ${A.LENGTH:02X}',
             f'CMD_INSTR   equ ${A.INSTRUMENT:02X}',
             f'PAT_END     equ ${A.END:02X}',
             f'ORDER_LOOP  equ ${A.ORDER_LOOP:02X}',
             f'TRANS_ZERO  equ ${A.TRANSPOSE_ZERO:02X}',
             f'WAVE_TONE   equ {A.WAVE_TONE}',
             f'WAVE_NOISE  equ {A.WAVE_NOISE}',
             f'WAVE_HOLD   equ ${A.WAVE_HOLD:02X}',
             f'WAVE_LOOP   equ ${A.WAVE_LOOP:02X}',
             f'ENV_HOLD    equ ${A.ENV_HOLD:02X}',
             f'NO_VIBRATO  equ ${A.NO_VIBRATO:02X}',
             f'FX_NOISE    equ ${A.AYFX_NOISE:02X}         ; effects',
             f'FX_TAIL     equ ${A.AYFX_TAIL:02X}',
             f'FX_STOP     equ ${A.AYFX_STOP:02X}']
    lines += [f'SONG_{s.upper():<7} equ {n}'
              for n, s in enumerate(score.SONGS)]
    lines += [f'SFX_{e.upper():<7} equ {n + 1}'
              for n, e in enumerate(sfx.EFFECTS)]
    lines.append('')
    lines += A.words('note_period', periods, 8, 'PSG tone period of'
                     ' notes 0-95')
    lines += A.table('ins_wave', [i['wave'] for i in ins], 10,
                     'instrument: wave table')
    lines += A.table('ins_env', [i['env'] for i in ins], 10,
                     'volumes of a note')
    lines += A.table('ins_rel', [i['rel'] for i in ins], 10,
                     'volumes of the release')
    lines += A.table('ins_vib', [i['vib'] for i in ins], 10,
                     'vibrato after n frames')
    lines.append('rel_start:  ; release entry from volume 0-15')
    for i in ins:
        lines.append('        db ' + A.hexbytes(i['rel_start'][:8]))
        lines.append('        db ' + A.hexbytes(i['rel_start'][8:]))
    lines += A.table('env_data', env_data, 12)
    lines += A.table('vib_offset', A.VIBRATO, 8, 'period, a cycle')
    lines += A.table('wave_ctrl', [c for c, _ in waves], 12)
    lines += A.table('wave_arg', [a for _, a in waves], 12)
    lines += A.words('pat_addr', [f'pat_{n}' for n in names], 3)
    lines.append('song_orders:  ; three order lists a song')
    for s in songs:
        lines.append('        dw ' + ','.join(f'ord_{s}_{v + 1}'
                                              for v in range(3)))
    for s, (orders, _) in songs.items():
        for v, data in enumerate(orders):
            lines += A.table(f'ord_{s}_{v + 1}', data, 12)
    for n in names:
        lines += A.table(f'pat_{n}', patterns[n], 12)
    lines += A.table('sfx_priority', prio, 10, 'effects 1-8')
    lines += A.table('fx_first', fx_first, 10, 'effects 1-8')
    lines.append('fx_data:  ; control, argument a frame')
    flat = [v for e in fx for v in e]
    for i in range(0, len(flat), 12):
        lines.append('        db ' + A.hexbytes(flat[i:i + 12]))
    lines.append('music_end:')

    size = (2 * A.NOTES + 4 * len(ins) + 16 * len(ins) + len(env_data)
            + len(A.VIBRATO) + 2 * len(waves) + 2 * len(names)
            + 6 * len(songs)
            + sum(len(o) for orders, _ in songs.values() for o in orders)
            + sum(len(p) for p in patterns.values())
            + len(prio) + len(fx_first) + 2 * len(fx))
    model = {'clock': PSG_CLOCK, 'speed_50': SPEED_50,
             'speed_60': SPEED_60, 'gate_before': GATE_BEFORE,
             'periods': periods,
             'instruments': [{k: i[k] for k in ('name', 'wave', 'env',
                                                'rel', 'rel_start',
                                                'vib')} for i in ins],
             'env_data': env_data, 'vibrato': A.VIBRATO,
             'waves': waves, 'pattern_names': names,
             'patterns': [patterns[n] for n in names],
             'songs': {s: {'orders': o, 'steps': n}
                       for s, (o, n) in songs.items()},
             'song_numbers': list(score.SONGS),
             'sfx_names': list(sfx.EFFECTS), 'sfx_priority': prio,
             'fx': [list(e) for e in fx], 'fx_first': fx_first,
             'bytes': size}
    return lines, model


if __name__ == '__main__':
    lines, model = build()
    notes = A.played_notes(dict(model, periods=model['periods']))
    bad = [n for n in notes if not model['periods'][n]]
    print(f"{model['bytes']} bytes; notes {notes[0]}-{notes[-1]};"
          f' out of range: {bad}')

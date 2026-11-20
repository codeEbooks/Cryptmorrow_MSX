"""The model of the sound on the PSG of the MSX: what player.asm must
send, frame by frame.

Independent of the Z80 code: it reads only the data made by
game/assets/psg_music.py (game/assets/generated/B/music.json) and
follows the rules of Cryptmorrow ZX's player, whose model is
tests/sound_model.py (copied from the ZX unchanged). What the MSX
changes:

- register 7: bit 7 at 1 (port B an output) and bit 6 at 0 (port A
  an input) in every value: silence is %10111111, not %00111111;
  the masks of the voices and of the effects keep those two bits;
- the speed: SPEED_50 frames a step on the 50 Hz machine, SPEED_60
  on the 60 Hz one; the release of a note's last step GATE_BEFORE
  frames before the step ends;
- the tone and noise periods are those of the MSX's clock (in the
  data).

PSGPlayer(music, song, hz).frame() works out one frame and returns
the 11 registers (0-10) that the interrupt will send at the start of
the next frame. PSGFx(music): SOUND FX on channel A, .start(n) asks
for effect n (1-8) with the C64's priorities, .frame() works out the
registers of a frame. PSGMachine(music, hz) follows what the program
sends, in order: .set_audio(mode), .song(name) (the piece of an end),
.sfx(n) (sound_effect), .interrupt(); .flushes lists the groups of 11
registers, .kinds what each was ('now': psg_silence at once; 'music';
'effects').

From milestone 0.6.1 nothing waits a frame more than it must: a song
starts with its first frame at the first interrupt (music_init works
it out), and in SOUND FX the interrupt works out the effect's frame
before sending it, so that an effect asked in a pass sounds at the
next interrupt, the one whose picture shows what asked for it (the
effects begin with their first note: psg_music.py).

Standard library only.
"""
import sound_model as S

MIXER_PORTS = 0x80              # bit 7: port B out; bit 6: A in
MODE_MUSIC, MODE_FX, MODE_SILENT = 0, 1, 2
SFX = {'slash': 1, 'hit': 2, 'dust': 3, 'pickup': 4, 'door': 5,
       'hurt': 6, 'lost': 7, 'won': 8}


def silence():
    regs = S.silence()
    regs[7] |= MIXER_PORTS
    return regs


def speed_of(music, hz):
    return music['speed_50'] if hz == 50 else music['speed_60']


def as_zx(music, hz):
    """The data in the form of the ZX's model."""
    speed = speed_of(music, hz)
    return dict(music, speed=speed,
                gate_tick=speed - music['gate_before'],
                ayfx=music['fx'], ayfx_first=music['fx_first'])


class PSGPlayer(S.AYPlayer):
    def __init__(self, music, song='theme', hz=50):
        super().__init__(as_zx(music, hz), song)
        self.regs = silence()

    def frame(self):
        regs = super().frame()
        regs[7] |= MIXER_PORTS
        self.regs[7] = regs[7]
        return regs


class PSGFx(S.AYFx):
    def __init__(self, music, hz=50):
        super().__init__(as_zx(music, hz))
        self.regs = silence()
        self.asked = self.refused = 0

    def start(self, n):
        self.asked += 1
        if self.m['sfx_priority'][n - 1] < self.prio:
            self.refused += 1
        super().start(n)

    def frame(self):
        super().frame()
        self.regs[7] |= MIXER_PORTS


class PSGMachine:
    def __init__(self, music, hz=50):
        self.music = music
        self.hz = hz
        self.mode = MODE_SILENT         # psg_init
        self.player = None
        self.fx = PSGFx(music, hz)
        self.flushes = []
        self.kinds = []
        self.send(silence(), 'now')     # psg_init: psg_silence

    def send(self, regs, kind):
        self.flushes.append(list(regs))
        self.kinds.append(kind)

    def set_audio(self, mode):
        self.mode = mode
        self.fx = PSGFx(self.music, self.hz)
        if mode == MODE_MUSIC:
            self.song('theme')
        else:
            self.send(silence(), 'now')

    def song(self, name):
        self.send(silence(), 'now')
        self.player = PSGPlayer(self.music, name, self.hz)

    def end_sound(self, won):
        if self.mode == MODE_MUSIC:
            self.song('won' if won else 'lost')
        else:
            self.sfx(SFX['won' if won else 'lost'])

    def sfx(self, n):
        if self.mode == MODE_FX:
            self.fx.start(n)

    def interrupt(self):
        if self.mode == MODE_MUSIC:
            self.send(self.player.frame(), 'music')
        else:
            if self.mode == MODE_FX:
                self.fx.frame()
            self.send(self.fx.regs, 'effects')

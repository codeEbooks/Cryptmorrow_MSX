# The music and the effects, as notes

The theme, the two pieces of the end and the eight sound effects of
Cryptmorrow, as they were written for the game's first version, on
the Commodore 64: notes, instruments and wave tables for its SID chip.
They are kept here unchanged. `game/assets/psg_music.py`, with the
functions of `game/assets/ay_music.py` (Cryptmorrow ZX's, unchanged),
turns them into the data of the MSX's player, for its PSG chip
(`generated/B/music.asm`, and `generated/B/music.json` for the tests).

| File | What | SHA-256 |
|---|---|---|
| `score.py` | the theme (C# minor, 125 BPM), the pieces of the end, instruments and wave tables | `472fed04d37793bc0a26817c7d8759656f309bdf18171959118bec9a89b7bdbb` |
| `sfx.py` | the eight effects (one voice) | `de1c05792d04a3af0c4da9ec7c3997cd67215b8e1a4da129fcf9de9fb60b9d61` |

The music and the effects are original, written for this game (see the
first lines of `score.py`). To change the music, change these files and
build again with `python tools/build_game.py --assets`: `psg_music.py`
writes the new data.

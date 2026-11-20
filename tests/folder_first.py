"""The tests of a step on a folder of its own (a guided variant or a
"Where it breaks" version, variants/NN-name/ID, Phase D, D.3): the
folder's asset modules and data in place of the project's.

use(argv) is called by tests/verify_step.py and tests/verify_1_0.py
before they import the models: with `--folder DIR` in argv, the asset
modules of DIR/game/assets (art_pieces.py, dungeon.py, art.py,
c64/score.py, c64/sfx.py, ay_music.py, build_msx.py, psg_music.py) are
imported first, so that every later import (tests/msx_model.py,
msx_states.py, verify_0_8.py) finds them already loaded: a variant
that changes a room, a colour, a word of the title or the music is
compared with the models of its own data. music(V, folder) gives
tests/verify_0_8.py the music of the folder (generated/B/music.json:
its speed, its notes).

apply(statements) runs the `--set` statements of a variant (the same
change made in the models: `world_model.POTION_ENERGY = 4`), with the
models' modules as names (and H, W, MM for hero_model, world_model,
msx_model; V for tests/verify_0_8.py, VS for tests/verify_step.py
when it runs).

From Cryptmorrow ZX (tests/folder_first.py), brought to the MSX: the
modules of its assets. Standard library only.
"""
import importlib
import json
import sys
from pathlib import Path

MODULES = ('art_pieces', 'dungeon', 'art', 'score', 'sfx', 'ay_music',
           'build_msx', 'psg_music')
MODELS = ('hero_model', 'msx_model', 'world_model', 'msx_states',
          'psg_model', 'step_world', 'route')


def folder_of(argv):
    if '--folder' not in argv:
        return None
    return Path(argv[argv.index('--folder') + 1]).resolve()


USED = []


def use(argv):
    """Returns the folder (or None)."""
    folder = folder_of(argv)
    if folder is None or USED:
        return folder
    USED.append(folder)
    assets = folder / 'game' / 'assets'
    for path in (assets / 'c64', assets):
        sys.path.insert(0, str(path))
    keep = sys.dont_write_bytecode
    sys.dont_write_bytecode = True      # the folder stays as it was made
    for name in MODULES:
        if name in sys.modules:
            raise RuntimeError(f'{name} imported before the folder')
        importlib.import_module(name)
    sys.dont_write_bytecode = keep
    for path in (assets / 'c64', assets):
        sys.path.remove(str(path))
    return folder


def music(V, folder):
    """tests/verify_0_8.py with the folder's generated data."""
    V.GENERATED = folder / 'game' / 'assets' / 'generated' / 'B'
    V.MUSIC = json.loads((V.GENERATED / 'music.json').read_text())


def apply(statements):
    names = {name: importlib.import_module(name) for name in MODELS}
    names['H'] = names['hero_model']
    names['W'] = names['world_model']
    names['MM'] = names['msx_model']
    names['V'] = importlib.import_module('verify_0_8')
    main = sys.modules.get('__main__')
    for extra in ('verify_step', 'verify_1_0'):
        if extra in sys.modules:
            names[extra] = sys.modules[extra]
        elif Path(getattr(main, '__file__', '') or '').stem == extra:
            names[extra] = main
    if 'verify_step' in names:
        names['VS'] = names['verify_step']
    for statement in statements or ():
        exec(statement, names)

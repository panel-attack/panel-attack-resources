"""Library, writes one file: a JSON generator's file into the game theme's scenes/ folder, as the theme holds it.
A file whose bytes differ from the new output is moved to build/.backup/ first."""

import os

from . import BUILD, GAME_SCENES, game, required, store


def write(rel, doc, st=None):
    """doc, as a generator builds it, into scenes/rel; prints what became of the file."""
    st = st or store.Store(required(GAME_SCENES, 'SCENE_GAME_THEME'), state=BUILD)
    print('%-9s scenes/%s' % (st.replace(os.path.join(GAME_SCENES, rel), game.to_json(game.theme_file(doc))), rel))

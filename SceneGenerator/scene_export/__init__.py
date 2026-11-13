"""Paths the scene exporter uses; writes nothing. The commands are in README.md and __main__.py."""

import os
import sys

GENERATOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# everything the generator makes, none of it committed
BUILD = os.path.join(GENERATOR, 'build')
# each drawing generator's sheet SVG, at its generator's path below SceneGenerator/: build/sheets/plants/trees.svg
SHEETS = os.path.join(BUILD, 'sheets')
# part SVGs cut out of the sheets, at the path their PNG has in the game's scenes folder
SVG_SCENES = os.path.join(BUILD, 'parts')
INDEX = os.path.join(BUILD, 'index.json')
# every part's rendered PNG, at its path below the theme's scenes/; layout and stage copy the ones they draw
RENDERED = os.path.join(BUILD, 'scenes')
# the folder holding the one file Pixelmator Pro opens, each part SVG copied over it in turn
STAGING = os.path.join(BUILD, 'pixelmator')


def folder_from(variable):
    """The folder the environment variable names; unset, a folder under build/ named for it, so a read fails
    naming the variable and nothing is written outside build/."""
    return os.environ.get(variable) or os.path.join(BUILD, variable + ' is unset')


def required(folder, variable):
    """folder, or stops naming the environment variable that gives it when it isn't a folder."""
    if not os.path.isdir(folder):
        raise SystemExit('%s is not a folder: set %s to the folder to use' % (folder, variable))
    return folder


# the panel-game theme the scene JSON and PNGs go into; image paths in the JSON are relative to it
GAME_THEME = folder_from('SCENE_GAME_THEME')
GAME_SCENES = os.path.join(GAME_THEME, 'scenes')
REFERENCES = folder_from('SCENE_REFERENCES')
SCENE_NAME = 'EsmeTerrace'

if GENERATOR not in sys.path:
    sys.path.insert(0, GENERATOR)

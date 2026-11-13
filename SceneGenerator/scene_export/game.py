"""Library, writes nothing: a scene file as the panel-game theme's scenes folder holds it, and the screen's file
one canvas container holding the scene, the shape the game loads a root file by.

The generators give image paths below scenes/ and refs as '<file below scenes/>#<template id>'; the theme wants
both from the theme folder."""

import copy
import json

from .cutting import GAME_CANVAS, num

THEME_FOLDER = 'scenes'
CANVAS = GAME_CANVAS
DECIMALS = 4                        # the places the scene editor writes a number with


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


def theme_file(doc, folder=THEME_FOLDER):
    """A copy of doc as the theme's scenes folder holds it; folder None leaves its paths as they are, as a stage
    folder holds it."""
    doc = copy.deepcopy(doc)
    for n in walk(doc['drawables']):
        if folder and 'filePath' in n:
            n['filePath'] = folder + '/' + n['filePath']
        if folder and n.get('ref', '').partition('#')[0].endswith('.json'):
            n['ref'] = folder + '/' + n['ref']
        for track in n.get('animationTracks', []) + n.get('overrides', {}).get('animationTracks', []):
            repeat_as_the_game_reads_it(track)
    return rounded(doc)


def rounded(value):
    """value with every number at most DECIMALS places, as the scene editor writes them."""
    if isinstance(value, dict):
        return {k: rounded(v) for k, v in value.items()}
    if isinstance(value, list):
        return [rounded(v) for v in value]
    if isinstance(value, float):
        return num(value, DECIMALS)
    return value


def repeat_as_the_game_reads_it(track):
    """The game repeats a track by "repeat": "loop" or "yoyo", not by the loopTrack and yoyo flags."""
    if track.pop('loopTrack', False):
        track['repeat'] = 'loop'
    if track.pop('yoyo', False):
        track['repeat'] = 'yoyo'


def to_json(doc):
    return (json.dumps(doc, indent=2, ensure_ascii=False) + '\n').encode()


def canvas(children):
    """A root file: the one container the game loads it by, the canvas's size at its origin, holding the scene."""
    return {'drawables': [{'id': 'canvas', 'size': {'width': CANVAS[0], 'height': CANVAS[1]}, 'children': children}]}


def screen_scene(scene_name):
    return canvas([{'id': scene_name + ' scene', 'ref': '%s/%s.json' % (scene_name, scene_name)}])


def check_root(doc, scene_name):
    """Raises naming the scene unless doc is one canvas container: the canvas's size, at 0,0 or unplaced, unscaled,
    without an image, a ref or a turn. The game refuses to load a root file of any other shape."""
    drawables = doc.get('drawables', [])
    container = drawables[0] if len(drawables) == 1 else {}
    allowed = {'id', 'size', 'position', 'children'}
    ok = (set(container) <= allowed and container.get('size') == {'width': CANVAS[0], 'height': CANVAS[1]}
          and all(container.get('position', {}).get(a, 0) == 0 for a in ('x', 'y'))
          and isinstance(container.get('children'), list))
    if not ok:
        raise ValueError('%s: a root file must hold one drawable, a container sized %d x %d at 0,0 with no scale, '
                         'image or ref, holding the scene; got %s' % (scene_name, CANVAS[0], CANVAS[1],
                                                                      [sorted(d) for d in drawables]))

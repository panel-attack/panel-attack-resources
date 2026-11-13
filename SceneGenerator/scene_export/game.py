"""Library, writes nothing: a scene file as the panel-game theme's scenes folder holds it, and the screen's file
placing the terrace over the whole 1280 x 720 canvas.

The generators give image paths below scenes/ and refs as '<file below scenes/>#<template id>'; the theme wants
both from the theme folder."""

import copy
import json

from .cutting import num

THEME_FOLDER = 'scenes'
CANVAS = (1280, 720)
DECIMALS = 4                        # the places the scene editor writes a number with


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


def theme_file(doc):
    """A copy of doc as the theme's scenes folder holds it."""
    doc = copy.deepcopy(doc)
    for n in walk(doc['drawables']):
        if 'filePath' in n:
            n['filePath'] = THEME_FOLDER + '/' + n['filePath']
        if n.get('ref', '').partition('#')[0].endswith('.json'):
            n['ref'] = THEME_FOLDER + '/' + n['ref']
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


def screen_scene(scene_name, size):
    scale = max(CANVAS[0] / size[0], CANVAS[1] / size[1])
    return {'drawables': [{'id': scene_name + ' on the canvas', 'xScale': scale, 'yScale': scale,
                           'position': {'x': (CANVAS[0] - size[0] * scale) / 2, 'y': (CANVAS[1] - size[1] * scale) / 2},
                           'children': [{'id': scene_name + ' scene', 'ref': '%s/%s.json' % (scene_name, scene_name)}]}]}

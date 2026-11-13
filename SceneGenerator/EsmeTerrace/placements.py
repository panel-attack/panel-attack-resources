"""Library, writes nothing: the scene-editor edits to the terrace, made in the game's editor on the stage that shipped, as
placement data in canvas units in placements.json, and the edits that apply them to what the generators cut.

placements.json holds:
- objects: for each planted object, its images and plants in draw order; an image is named by its node id and
  drawn where it was cut, or at x, y on the canvas where it was moved, a plant is a ref placed at x, y on the canvas with its rotation and its scales at its
  template's sheet size, swaying after its delay, or standing still without one;
- placed: overrides set on nodes, by the ids on the way to them, their tracks left as they were (a cloud moved
  this way still drifts home to where the generator put it);
- moved: nodes moved to x, y with their tracks;
- left out: nodes the terrace doesn't draw, by the ids on the way to them;
- added: nodes drawn under a node, at an index among its children."""

import copy
import functools
import json
import os

from scene_export import cutting, placed_foliage, wind

HERE = os.path.dirname(os.path.abspath(__file__))
PLANT_KEYS = ('rotation', 'xScale', 'yScale')


@functools.cache
def load():
    with open(os.path.join(HERE, 'placements.json')) as f:
        return json.load(f)


def planted(cut, items):
    """The object's nodes: the cut images the items name, and the plants they place, in the items' order."""
    images = {n['id']: n for n in cut if 'filePath' in n}
    out = []
    for item in items:
        if 'image' in item:
            image = copy.deepcopy(images[item['image']])
            if 'x' in item:
                image['position'] = {'x': item['x'], 'y': item['y']}
            out.append(image)
            continue
        node = {'id': item['id'], 'ref': item['ref'], 'overrides': {'position': {'x': item['x'], 'y': item['y']}}}
        node['overrides'].update({k: item[k] for k in PLANT_KEYS if k in item})
        if 'delay' in item:
            node['overrides']['animationTracks'] = wind.sway(node, delay=item['delay'])
        out.append(node)
    return out


def object_children(obj):
    """The planted object's nodes as placed in the scene editor, in canvas units."""
    return planted(placed_foliage.placed().children[obj], load()['objects'][obj])


def terrace(nodes):
    """The terrace's nodes with the scene-editor edits."""
    data = load()
    return added(without(moved(placed(nodes, data['placed']), data['moved']), data['left out']), data['added'])


def edited(nodes, tree, edit):
    """Copies of the nodes with edit(node, value) applied to each node tree names by the ids on the way to it."""
    nodes = copy.deepcopy(nodes)

    def visit(children, tree):
        by_id = {n.get('id'): n for n in children}
        for node_id, value in tree.items():
            if node_id not in by_id:
                raise ValueError('placements.json names %r, which the generators no longer draw' % node_id)
            node = by_id[node_id]
            if 'children' in node:
                visit(node['children'], value)
            else:
                edit(node, value)
    visit(nodes, tree)
    return nodes


def holder(node):
    return node.setdefault('overrides', {}) if 'ref' in node else node


def placed(nodes, tree):
    return edited(nodes, tree, lambda node, overrides: holder(node).update(copy.deepcopy(overrides)))


def moved(nodes, tree):
    def move(node, to):
        h = holder(node)
        at = h.get('position', {})
        dx, dy = to['x'] - at.get('x', 0), to['y'] - at.get('y', 0)
        h['position'] = {'x': to['x'], 'y': to['y']}
        cutting.shift_tracks(h.get('animationTracks', []), -dx, -dy)
    return edited(nodes, tree, move)


def find(nodes, path):
    for node_id in path:
        nodes = next(n for n in nodes if n.get('id') == node_id).setdefault('children', [])
    return nodes


def without(nodes, paths):
    nodes = copy.deepcopy(nodes)
    for path in paths:
        siblings = find(nodes, path[:-1])
        kept = [n for n in siblings if n.get('id') != path[-1]]
        if len(kept) == len(siblings):
            raise ValueError('placements.json leaves out %r, which the generators no longer draw' % (path,))
        siblings[:] = kept
    return nodes


def added(nodes, additions):
    nodes = copy.deepcopy(nodes)
    for a in additions:
        find(nodes, a['under']).insert(a['at'], copy.deepcopy(a['node']))
    return nodes

"""Library, writes nothing: cutting a generator's sheet SVG into parts, the images the game draws, and the nodes
that draw them. A part's path is where its PNG lives below the game's scenes/ folder, and a node's ref is
'<file below scenes/>#<template id>' until game.py makes it relative to the file it is written into."""

import copy
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from . import SHEETS, svgtools

CANVAS = (1536, 1024)
PAD = 4
NS = '{%s}' % svgtools.SVG_NS


@dataclass
class Part:
    path: str           # relative to build/parts/, without extension or @2x
    svg: str
    box: tuple          # (x, y, w, h) px: where it sits on the 1536 x 1024 canvas (a template: around its stem)

    @property
    def size(self):
        return self.box[2], self.box[3]


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def num(v, places=3):
    v = round(v, places)
    return int(v) if v == int(v) else v


def placed_at(x, y):
    """The overrides placing a ref's template at (x, y) scene units, for a template that sits at the origin: an axis
    left at 0 is left out, and so is the position when both are."""
    position = {axis: v for axis, v in (('x', num(x)), ('y', num(y))) if v != 0}
    return {'position': position} if position else {}


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


def sheet_path(rel):
    """Where the sheet SVG rel, at its generator's path below SceneGenerator/ (plants/trees.svg), is drawn: below
    build/sheets/, its folder made."""
    path = os.path.join(SHEETS, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def load(sheet):
    """The sheet SVG (plants/trees.svg) as drawn into build/sheets/, and its gradients by id."""
    root = ET.parse(sheet_path(sheet)).getroot()
    grads = {g.get('id'): g for g in root.iter(NS + 'linearGradient')}
    return root, grads


def find_group(root, gid):
    for g in root.iter(NS + 'g'):
        if g.get('id') == gid:
            return g
    raise KeyError(gid)


def static_part(path, elements, gradients, name, canvas=CANVAS):
    """The elements as one image, cropped to them; canvas None leaves them uncropped."""
    box = svgtools.crop_box(svgtools.union([svgtools.element_bbox(e) for e in elements]), PAD, canvas)
    return Part(path, svgtools.part_svg(name, elements, gradients, box), box)


def foot_part(path, elements, gradients, name):
    """The elements, drawn standing on (0, 0), as an image around their foot."""
    box = svgtools.foot_box(svgtools.union([svgtools.element_bbox(e) for e in elements]), PAD)
    return Part(path, svgtools.part_svg(name, elements, gradients, box), box)


def filtered(el, keep):
    """A copy of el holding only the paths keep(id) accepts, without groups left empty; None if nothing."""
    if svgtools.local(el.tag) == 'path':
        return el if keep(el.get('id', '')) else None
    out = ET.Element(el.tag, dict(el.attrib))
    for ch in el:
        c = filtered(ch, keep)
        if c is not None:
            out.append(c)
    return out if len(out) else None


def at(box):
    return {'x': num(box[0] / 2), 'y': num(box[1] / 2)}


def image_node(node_id, part):
    """Draws the part where it sits on the canvas."""
    return {'id': node_id, 'filePath': part.path, 'position': at(part.box)}


def image_template(template_id, part):
    return {'id': template_id, 'filePath': part.path, 'templateOnly': True}


def image_ref(node_id, file, template_id, part, **overrides):
    """Draws the image template of the part where the part sits on the canvas."""
    return {'id': node_id, 'ref': file + '#' + template_id, 'overrides': dict(position=at(part.box), **overrides)}


def marker_ref(g, file):
    """Draws the template a generator placed as a <g data-template data-at data-scale> marker where it placed it."""
    x, y = (float(v) for v in g.get('data-at').split(','))
    sx, sy = (float(v) for v in g.get('data-scale').split(','))
    return {'id': g.get('id'), 'ref': file + '#' + g.get('data-template'),
            'overrides': {'position': {'x': num(x / 2), 'y': num(y / 2)}, 'xScale': num(sx, 5), 'yScale': num(sy, 5)}}


def origin(children):
    """Where an object's template is drawn from: the rounded place of its first image."""
    first = next(n for n in children if 'filePath' in n)
    return round(first['position']['x']), round(first['position']['y'])


def shift_tracks(tracks, dx, dy):
    for track in tracks:
        for step in track.get('steps', []):
            props = step.get('animateProperties', {})
            if 'x' in props:
                props['x'] = num(props['x'] - dx)
            if 'y' in props:
                props['y'] = num(props['y'] - dy)


def shifted(children, o):
    """Copies of the nodes moved so o is their (0, 0)."""
    children = copy.deepcopy(children)
    dx, dy = o
    for node in children:
        placed = node.get('overrides', {}) if 'ref' in node else node
        if 'position' not in placed:
            raise ValueError('%s has no position to move into its template' % node['id'])
        placed['position'] = {'x': num(placed['position']['x'] - dx), 'y': num(placed['position']['y'] - dy)}
        shift_tracks(placed.get('animationTracks', []), dx, dy)
    return children


def object_template(template_id, children):
    """The object's nodes as a template drawn from its origin."""
    return {'id': template_id, 'templateOnly': True, 'children': shifted(children, origin(children))}


def object_ref(node_id, file, template_id, children):
    """Draws the object's template where its nodes were."""
    x, y = origin(children)
    return {'id': node_id, 'ref': file + '#' + template_id, 'overrides': {'position': {'x': x, 'y': y}}}

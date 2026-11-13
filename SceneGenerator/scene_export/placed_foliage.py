"""Library, writes nothing: the planters and the corner bush cut into their images and the refs placing their
library pieces and foliage, branches.py's library pieces as templates drawn from the foliage templates, and
the leaf, flower, rose and stem templates all of them place; native.py picks the size each PNG is exported at.

Inside a bush, the stems foliage.py draws between leaves are lifted into the bush's own image under every
leaf; side-by-side renders show no visible difference, and it keeps the stems out of the refs."""

import functools
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from . import svgtools, templates as T
from .capture import Foliage, build_bush, build_planters
from .cutting import NS, UNITS, Part, find_group, half, image_node, load, num, offset, placed_at, point, slug, static_part
from plants import branches, foliage
from furniture import planters

BRANCHES = 'plants/branches.json'
FOLIAGE_FILES = [('leaf-', 'leaves'), ('flower-', 'flowers'), ('daisy-', 'flowers'), ('bud', 'flowers'),
                 ('rose-', 'roses'), ('stem-', 'stems')]
# object: (its sheet, its group there, the folder below scenes/ its images go in)
OBJECTS = {'crystal planter': ('furniture/planters.svg', 'Crystal planter', 'furniture'),
           'left urn': ('furniture/planters.svg', 'Left urn', 'furniture'),
           'right urn': ('furniture/planters.svg', 'Right urn', 'furniture'),
           'corner bush': ('plants/bushes.svg', 'Corner bush', 'plants')}
PIECE_ATTRIBUTES = {'id', 'data-piece', 'data-at', 'data-rotation', 'data-scale', 'data-mirror'}
KIND_NAMES = {'leaf': 'leaf', 'rose': 'rose', 'bud': 'bud', 'twig': 'stem', 'stem': 'stem'}
STATIC_NAMES = {'pot': 'body', 'bush body': 'body', 'body': 'body'}


@dataclass
class Placed:
    children: dict      # object: its nodes, where the scene draws them
    parts: dict         # object: its images
    library: list       # branches.py's pieces as templates
    templates: dict     # foliage template id: templates.Template


def foliage_group(template_id):
    """Which of the plants' foliage files the template is in: leaves, flowers, roses or stems."""
    return next(group for prefix, group in FOLIAGE_FILES if template_id.startswith(prefix))


def foliage_file(template_id):
    return 'plants/%s.json' % foliage_group(template_id)


def template_path(template_id):
    return 'plants/parts/%s/%s' % (foliage_group(template_id), template_id)


def kind_name(record):
    if record.kind == 'flower':
        return 'daisy' if record.params['white'] else 'flower'
    return KIND_NAMES[record.kind]


def template_part(t):
    """The template's PNG part, drawn at its template size about the stem."""
    out = planters.Out()
    out.add_all(t.shapes(stem=(0, 0)))
    g = ET.fromstring('<g xmlns="%s">%s</g>' % (svgtools.SVG_NS, '\n'.join(out.body)))
    elements = list(g)
    grads = {}
    for k, (a, b) in out.gradients.items():
        lg = ET.Element('linearGradient', {'id': k, 'x1': '0', 'y1': '0', 'x2': '0', 'y2': '1'})
        ET.SubElement(lg, 'stop', {'offset': '0', 'stop-color': a})
        ET.SubElement(lg, 'stop', {'offset': '1', 'stop-color': b})
        grads[k] = lg
    bbox = svgtools.union([svgtools.element_bbox(e) for e in elements])
    box = svgtools.stem_box(bbox, (0, 0), T.STEM_PAD)
    return Part(template_path(t.id), svgtools.part_svg(t.id, elements, grads, box), box)


def foliage_items(el):
    """el's foliage in paint order: ('path', path) and ('piece', group of a library piece), other groups
    opened up."""
    for ch in el:
        if svgtools.local(ch.tag) == 'path':
            yield 'path', ch
        elif ch.get('data-piece') is not None:
            yield 'piece', ch
        else:
            yield from foliage_items(ch)


def piece_node(g):
    """The ref placing the library piece a piece group draws, as the group carries it."""
    x, y = (float(v) for v in g.get('data-at').split(','))
    scale = float(g.get('data-scale'))
    return {'id': g.get('id'), 'ref': BRANCHES + '#' + g.get('data-piece'),
            'overrides': {**placed_at(point(x, y)),
                          'rotation': num(float(g.get('data-rotation')), 5),
                          'xScale': num(-scale if g.get('data-mirror') else scale, 5), 'yScale': num(scale, 5)}}


def sub_label(obj, sid):
    s = sid.lower()
    for prefix in (obj + ' ', 'crystal planter ', 'crystal '):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    if s.endswith('leaves'):
        s = s[:-len('leaves')].strip()
    return s


class Cutter:
    def __init__(self):
        self.templates = {}

    def instance(self, obj, label, record, counters, at=point):
        """The ref placing a recorded leaf or flower's template where at(x, y) puts its sheet point."""
        pl = T.place(record)
        t = pl.template
        self.templates.setdefault(t.id, t)
        kind = kind_name(record)
        key = (label, kind)
        counters[key] = counters.get(key, 0) + 1
        node = {'id': ' '.join(x for x in (obj, label, kind, str(counters[key])) if x),
                'ref': foliage_file(t.id) + '#' + t.id,
                'overrides': {**placed_at(at(pl.x, pl.y)), 'rotation': num(pl.rotation, 5),
                              'xScale': num(pl.xscale, 5), 'yScale': num(pl.yscale, 5)}}
        return node

    def planter(self, obj, group, gradients, records, owner, folder):
        """The object's images and nodes: each run of its pot and bush masses one image, each library piece
        and recorded leaf or flower a ref, its floor contact left to its shadow."""
        parts, children = [], []
        counters = {}
        pending = None          # [label, elements] of a static run not yet closed

        def close():
            nonlocal pending
            if pending:
                name = STATIC_NAMES.get(pending[0], pending[0])
                node_id = '%s %s' % (obj, name)
                part = static_part('%s/parts/%s/%s' % (folder, slug(obj), slug(name)), pending[1], gradients, node_id)
                parts.append(part)
                children.append(image_node(node_id, part))
            pending = None

        def static(label, elements):
            nonlocal pending
            if pending is None:
                pending = [label, []]
            pending[1].extend(elements)

        for sub in group:
            sid = sub.get('id')
            label = sub_label(obj, sid)
            if 'floor contact' in sid:
                continue
            paths = list(sub.iter(NS + 'path'))
            if not any(p.get('id') in owner for p in paths):
                static(label, [sub])
                continue
            in_pieces = set()
            for g in sub.iter(NS + 'g'):
                if g.get('data-piece') is not None:
                    in_pieces.update(p.get('id') for p in g.iter(NS + 'path'))
                if g is not sub and set(g.attrib) - PIECE_ATTRIBUTES:
                    raise ValueError('%s: a styled group inside a bush is not supported' % g.get('id'))
            stems = [p for p in paths if p.get('id') not in owner and p.get('id') not in in_pieces]
            close()             # a bush's mass and stems are its own image, never part of the pot's
            if stems:
                static(label, stems)
            close()
            seen = set()
            for kind, el in foliage_items(sub):
                if kind == 'piece':
                    node = piece_node(el)
                    children.append(node)
                    continue
                name = owner.get(el.get('id'))
                if name is None or name in seen:
                    continue
                seen.add(name)
                children.append(self.instance(obj, label, records[name], counters))
        close()
        return parts, children

    def library_piece(self, piece):
        """branches.py's piece as a template drawn from the foliage templates, each side shoot a group at the
        first point of its stem."""
        children, groups, counters = [], {}, {}
        for i, d in enumerate(piece.draws):
            if d.kind == 'stem':
                record = Foliage('stem', '%s %d' % (piece.id, i), dict(base=d.base, angle=d.angle, length=d.length,
                                                                     width=d.width))
            else:
                tone = 'leaf-%d' % d.tone
                record = Foliage('leaf', '%s %d' % (piece.id, i), dict(
                    base=d.base, angle=d.angle, length=d.length, tone=tone, bend=d.bend, width=d.width,
                    stroke=branches.LEAF_STROKE, gloss=d.gloss, shade=foliage.LEAF_SHADE_DEEP[tone]))
            if d.group is None:
                children.append(self.instance(piece.id, '', record, counters, offset))
                continue
            if d.group not in groups:
                groups[d.group] = {'id': '%s %s' % (piece.id, d.group), 'position': offset(*d.base), 'children': []}
                children.append(groups[d.group])
            g = groups[d.group]
            o = g['position']['x'], g['position']['y']
            g['children'].append(self.instance(piece.id, d.group, record, counters, lambda x, y, o=o: {
                'x': num(half(x * UNITS - o[0])), 'y': num(half(y * UNITS - o[1]))}))
        return {'id': piece.id, 'templateOnly': True, 'children': children}


def owners(records):
    return {n: r.name for r in records.values() for n in r.names}


@functools.cache
def placed():
    cutter = Cutter()
    records = {'furniture/planters.svg': build_planters(), 'plants/bushes.svg': build_bush()}
    children, parts = {}, {}
    for obj, (sheet, group_id, folder) in OBJECTS.items():
        root, grads = load(sheet)
        drawn = {p.get('id') for p in root.iter(NS + 'path')}
        missing = [r.name for r in records[sheet].values() if r.names[0] not in drawn]
        if missing:
            raise ValueError('%s is out of date with its generator: %s are not in it' % (sheet, missing[:5]))
        parts[obj], children[obj] = cutter.planter(obj, find_group(root, group_id), grads, records[sheet],
                                                   owners(records[sheet]), folder)

    library = [cutter.library_piece(p) for p in branches.library()]
    for length_name in branches.STEM_LENGTHS:
        for width_name in branches.STEM_WIDTHS:
            t = T.StemTemplate(length_name, width_name)
            cutter.templates.setdefault(t.id, t)
    return Placed(children, parts, library, cutter.templates)


def template_parts(group):
    """The PNG parts of the foliage templates in one of the plants' foliage files."""
    p = placed()
    return [template_part(p.templates[tid]) for tid in sorted(p.templates)
            if foliage_group(tid) == group]


def template_file(group):
    """The plants' foliage file holding the group's templates, each centred on its stem."""
    return {'drawables': [{'id': tid, 'filePath': template_path(tid), 'anchor': 'center', 'pivot': 'center',
                           'templateOnly': True}
                          for tid in sorted(placed().templates) if foliage_group(tid) == group]}

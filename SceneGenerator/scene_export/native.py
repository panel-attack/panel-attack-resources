"""Library, writes nothing: the size each part's PNG is drawn at, chosen from how the scenes draw it.

A part's art is cut from its sheet in the sheet's px; at scale 1 the scenes draw it at its sheet size on the canvas,
cutting.UNITS units a px. Its PNG is drawn at 2x the size the scenes typically draw it, so a draw is near 1:1 on the
2560 x 1440 canvas a 2x screen shows:
- a part all of whose draws are at one scale, as a part used once is, is drawn at exactly that scale, so the scenes
  draw its PNG at scale 1, pixel for pixel;
- a part the scenes draw at several scales, a template, is drawn at the largest of them on each axis, so no draw
  scales its PNG up, only down;
- a part that repeats (wrap), that is stretched to a size, or that no scene draws is drawn at its sheet size.
resolved() divides every scale that draws a part by its resolution, so the scenes draw what they drew, and check()
refuses a part drawn anywhere larger than its PNG, and a part used once that the scenes still draw scaled, or upright
and still off a whole canvas unit."""

import copy
import dataclasses
import math
import xml.etree.ElementTree as ET

from . import game
from .cutting import UNITS, num
from .preview import ANCHORS, merge, mul, node_matrix, stretched

MOVING = {'x', 'y', 'rotation', 'xScale', 'yScale'}
EPSILON = 1e-4


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


def steps(holder):
    for track in holder.get('animationTracks', []):
        for step in track.get('steps', []):
            yield step.get('animateProperties', {})


# ---------------------------------------------------------------- native size

def native_px(px, resolution=1.0):
    """A sheet length's pixels at 2x on the canvas, drawn resolution times its sheet size, rounded to even so a @2x
    image halves exactly."""
    return max(2, 2 * round(px * resolution * UNITS))


def native_svg(svg, resolution=(1.0, 1.0), anchor='topLeft', strip=False):
    """A part SVG drawn at its native size and resolution, its anchor point where the drawing has it; a strip is
    drawn one px wide, its whole width squeezed into it. Its viewBox is stretched to fill the PNG, which has other
    proportions than the art when the part is drawn at another scale on each axis."""
    root = ET.fromstring(svg)
    w, h = int(root.get('width')), int(root.get('height'))
    head = '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (w, h, w, h)
    if head not in svg:
        raise ValueError("not a part SVG in the generators' form: %s" % svg[:120])
    (fx, fy), (rx, ry) = ANCHORS[anchor], resolution
    nw, nh = native_px(w, rx), native_px(h, ry)
    vw, vh = nw / (2 * UNITS * rx), nh / (2 * UNITS * ry)
    if strip:
        nw, vw = 1, w
    view = ' '.join('%g' % (round(v, 6) + 0.0) for v in (fx * (w - vw), fy * (h - vh), vw, vh))
    return svg.replace(head, '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%s" '
                             'preserveAspectRatio="none">' % (nw, nh, view), 1)


def native_part(part, resolution=(1.0, 1.0), anchor='topLeft'):
    """The part as its PNG is drawn: its SVG at its native size, its box the PNG's size."""
    w, h = native_px(part.size[0], resolution[0]), native_px(part.size[1], resolution[1])
    if part.strip:
        w = 1
    return dataclasses.replace(part, svg=native_svg(part.svg, resolution, anchor, part.strip), box=(0, 0, w, h))


# ---------------------------------------------------------------- resolving refs

def without_folder(path):
    prefix = game.THEME_FOLDER + '/'
    return path[len(prefix):] if path.startswith(prefix) else path


def file_of(ref):
    return without_folder(ref.partition('#')[0])


class Files:
    def __init__(self, docs):
        self.docs = docs
        self.ids = {rel: {n['id']: n for n in walk(doc['drawables']) if 'id' in n} for rel, doc in docs.items()}

    def template(self, ref):
        return self.ids[file_of(ref)][ref.partition('#')[2]]

    def effective(self, node):
        """The node with its ref's template and overrides applied, without children."""
        if 'ref' not in node:
            return {k: v for k, v in node.items() if k != 'children'}
        out = self.effective(self.template(node['ref']))
        merge(out, {k: v for k, v in node.get('overrides', {}).items() if k != 'children'})
        return out

    def children(self, node):
        if 'ref' in node:
            return self.children(self.template(node['ref']))
        return node.get('children', [])


class Instance:
    """A textured drawable as drawn: the written nodes on its way from the root, its image, its matrix in canvas
    units, its size in units, whether anything on the way moves, and whether it is stretched to a size."""

    def __init__(self, path, nodes, image, matrix, size, moving, stretched=False):
        self.path, self.nodes, self.image, self.matrix, self.size, self.moving = path, nodes, image, matrix, size, moving
        self.stretched = stretched

    @property
    def scale(self):
        a, b, c, d = self.matrix[:4]
        return math.hypot(a, b), math.hypot(c, d)

    @property
    def rotated(self):
        a, b, c, d = self.matrix[:4]
        return abs(b) > EPSILON or abs(c) > EPSILON or (a < 0 and d < 0)

    @property
    def top_left(self):
        """The top left of the box it draws in."""
        a, b, c, d, e, f = self.matrix
        w, h = self.size
        corners = [(a * x + c * y + e, b * x + d * y + f) for x in (0, w) for y in (0, h)]
        return min(x for x, _ in corners), min(y for _, y in corners)


def whole_file(node):
    return 'ref' in node and '#' not in node['ref']


def instances(docs, roots, size_of, files=None):
    """Every textured drawable the roots draw; size_of(image) is the image's size in units."""
    files = files or Files(docs)
    out = []

    def visit(node, m, moving, nodes, path):
        if whole_file(node):
            for n in docs[file_of(node['ref'])]['drawables']:
                visit(n, m, moving, nodes, path)
            return
        eff = files.effective(node)
        image = 'filePath' in eff and without_folder(eff['filePath'])
        size = eff.get('size', {})
        w, h = size_of(image) if image else (size.get('width', 0), size.get('height', 0))
        here = mul(m, node_matrix(eff, w, h, bool(image)))
        moving = moving or any(MOVING & set(props) for props in steps(eff))
        nodes, path = nodes + [node], path + [node.get('id')]
        if image:
            out.append(Instance(path, nodes, image, here, (w, h), moving, stretched(eff)))
        for child in files.children(node):
            visit(child, here, moving, nodes, path)
    for rel in roots:
        for n in docs[rel]['drawables']:
            visit(n, (1, 0, 0, 1, 0, 0), False, [], [])
    return out


# ---------------------------------------------------------------- resolution

def one_scale(scales):
    return all(abs(sx - scales[0][0]) < EPSILON and abs(sy - scales[0][1]) < EPSILON for sx, sy in scales)


def resolution(scales):
    """The (x, y) resolution of a part the scenes draw at these (x, y) scales."""
    if one_scale(scales):
        return scales[0]
    return max(sx for sx, _ in scales), max(sy for _, sy in scales)


def draws(docs, scenes):
    """{image: [(x, y) scale of each draw]} of every image the scenes draw unstretched; an image stretched to a size
    stays at its sheet size."""
    out = {}
    for i in instances(docs, scenes, lambda image: (1, 1)):
        if i.stretched:
            continue
        out.setdefault(i.image, []).append(i.scale)
    return out


def resolutions(docs, scenes):
    """{image: (x, y) resolution} of every image the scenes draw at other than its sheet size; a repeating image
    stays at its sheet size."""
    repeats = {without_folder(n['filePath']) for doc in docs.values() for n in walk(doc['drawables'])
               if n.get('wrap') == 'repeat' and 'filePath' in n}
    out = {}
    for image, scales in draws(docs, scenes).items():
        r = tuple(num(v, 6) for v in resolution(scales))
        if image not in repeats and r != (1, 1):
            out[image] = r
    return out


def divided(holder, r, inherited=(1, 1)):
    """Divides the scales holder draws its image at by the resolution r, its keyframes' too; a scale equal to the
    one it would inherit is dropped."""
    for axis, k in (('xScale', 0), ('yScale', 1)):
        if axis in holder:
            holder[axis] = num(holder[axis] / r[k], 6)
        for props in steps(holder):
            if axis in props:
                props[axis] = num(props[axis] / r[k], 6)
        if holder.get(axis) == inherited[k]:
            del holder[axis]


def moved(holder, dx, dy):
    """Moves the place in holder, and its own keyframes with it."""
    if not (dx or dy):
        return
    pos = holder.setdefault('position', {})
    for axis, d in (('x', dx), ('y', dy)):
        if d:
            pos[axis] = num(pos.get(axis, 0) + d, 6)
            for props in steps(holder):
                if axis in props:
                    props[axis] = num(props[axis] + d, 6)


def anchor_shift(node, r, size):
    """How far a node's place moves to draw its image from the same point when the image is r times larger: the
    loader places an image's anchor at the place, then scales about its pivot, so an image whose anchor isn't its
    pivot moves."""
    ax, ay = ANCHORS[node.get('anchor', 'topLeft')]
    px, py = ANCHORS[node.get('pivot') or 'center']
    return -(r[0] - 1) * (px - ax) * size[0], -(r[1] - 1) * (py - ay) * size[1]


def resolved(docs, scenes, sizes):
    """(docs, resolutions): copies of the docs with every scale that draws an image of another resolution divided
    by it, so the scenes draw what they drew, and the resolutions. A template keeps its own scale; each ref to it
    gets its own. sizes is {image: its size in units at its sheet size}."""
    rs = resolutions(docs, scenes)
    files = Files(docs)
    out = copy.deepcopy(docs)
    for rel in docs:
        for n, new in zip(walk(docs[rel]['drawables']), walk(out[rel]['drawables'])):
            if whole_file(n) or n.get('templateOnly'):
                continue
            if 'ref' in n:
                t = files.template(n['ref'])
                image = 'ref' not in t and 'filePath' in t and without_folder(t['filePath'])
            else:
                t, image = None, 'filePath' in n and without_folder(n['filePath'])
            r = rs.get(image)
            if not r:
                continue
            if t is None:
                new.setdefault('xScale', 1)
                new.setdefault('yScale', 1)
                divided(new, r)
                moved(new, *anchor_shift(n, r, sizes[image]))
                continue
            holder = new.setdefault('overrides', {})
            inherited = (t.get('xScale', 1), t.get('yScale', 1))
            holder.setdefault('xScale', inherited[0])
            holder.setdefault('yScale', inherited[1])
            divided(holder, r, inherited)
            shift = anchor_shift(files.effective(n), r, sizes[image])
            if shift != (0, 0):
                holder.setdefault('position', copy.deepcopy(t.get('position', {})))
                moved(holder, *shift)
    return out, rs


# ---------------------------------------------------------------- whole canvas units

def still_and_upright(draws):
    """The draws of every part all of whose draws are at one scale, that are upright, still and unstretched."""
    by_image = {}
    for i in draws:
        by_image.setdefault(i.image, []).append(i)
    return [i for image, its in sorted(by_image.items()) if one_scale([i.scale for i in its])
            for i in its if not (i.moving or i.rotated or i.stretched)]


def aligned(docs, scenes, size_of):
    """Copies of the docs with each part used once that the scenes draw upright and still moved onto a whole canvas
    unit, at most half a unit, half rounding up; a node that draws it in places that disagree is left where it is."""
    docs = copy.deepcopy(docs)
    files = Files(docs)
    wanted = {}
    for i in still_and_upright(instances(docs, scenes, size_of, files)):
        x, y = i.top_left
        wanted.setdefault(id(i.nodes[-1]), (i.nodes[-1], set()))[1].add(
            (num(math.floor(x + 0.5) - x, 6), num(math.floor(y + 0.5) - y, 6)))
    for node, offsets in wanted.values():
        if len(offsets) != 1 or offsets == {(0, 0)}:
            continue
        if 'ref' in node:
            holder = node.setdefault('overrides', {})
            holder.setdefault('position', copy.deepcopy(files.effective(node).get('position', {})))
        else:
            holder = node
        moved(holder, *offsets.pop())
    return docs


# ---------------------------------------------------------------- the check

def pixel_perfect_failures(docs, scenes, size_of):
    """'<image>: why' for every draw of a part all of whose draws are at one scale, upright and still, that is
    scaled or off a whole canvas unit."""
    out = []
    for i in still_and_upright(instances(docs, scenes, size_of)):
        (sx, sy), (x, y) = i.scale, i.top_left
        where = ' / '.join(map(str, i.path))
        if abs(sx - 1) > EPSILON or abs(sy - 1) > EPSILON:
            out.append('%s: drawn at scale %g x %g by %s' % (i.image, sx, sy, where))
        elif abs(x - round(x)) > 1e-3 or abs(y - round(y)) > 1e-3:
            out.append('%s: its top left %g, %g is off a whole canvas unit, by %s' % (i.image, x, y, where))
    return out


def enlarged_failures(docs, scenes, size_of):
    """'<image>: why' for every draw that scales a part's PNG up; a part stretched to a size is meant to be."""
    return ['%s: drawn at %gx its PNG by %s' % (i.image, round(max(i.scale), 4), ' / '.join(map(str, i.path)))
            for i in instances(docs, scenes, size_of) if not i.stretched and max(i.scale) > 1 + EPSILON]


def check(docs, scenes, size_of):
    """Refuses, naming each, a part drawn anywhere larger than its PNG, and a part used once that the scenes draw
    upright and still but scaled or off a whole canvas unit."""
    failures = enlarged_failures(docs, scenes, size_of) + pixel_perfect_failures(docs, scenes, size_of)
    if failures:
        raise ValueError('a part must never be drawn larger than its PNG, and a part used once must be drawn at its '
                         'PNG size on a whole canvas unit:\n  ' + '\n  '.join(failures))

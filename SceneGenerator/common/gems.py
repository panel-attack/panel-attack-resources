#   Library, writes nothing: the diamond gem shapes the rail, table and planter generators draw.
#
#   Shared diamond gem, in the style of the reference: a pointed rhombus stone
#   cut as a low pyramid (four triangular facets meeting at the centre, lit
#   from the top left, with a white glint down the upper ridge), sitting in a
#   pointed gold setting whose four bevel faces meet in mitred seams at the tips.
#
#   The gem is described in gem-local (u, v): u to the right, v UP, centred on
#   (cx, cy). The caller passes `mapper`, a function from a list of (u, v) to a
#   list of screen (x, y), so the same gem can be drawn flat or wrapped onto
#   any surface. Edges are cut into `steps` pieces before mapping so curved
#   surfaces bend them; the four tips are always kept as exact vertices.
#
#   diamond_gem() returns a list of Shape(id, points, fill, stroke, width).
#   write(body, shapes) appends them as <path>s to a list of SVG lines (every
#   Out class here keeps one as .body), with mitred joins so the tips stay sharp.

import math
from collections import namedtuple

Shape = namedtuple('Shape', 'id points fill stroke width')

STONE = {
    'light': '#a8f5ec',   # top-left facet, facing the light
    'mid': '#2fd6c8',     # top-right
    'low': '#12aab0',     # bottom-left
    'dark': '#0a8796',    # bottom-right, facing away
    'glint': '#f4fffd',   # white wedge down the upper ridge
    'rim': '#0b5f6e',     # outline round the stone
}
SETTING = {
    'light': '#ffec70',   # top-left face
    'mid': '#f8cf45',     # top-right: faces up, still in the high sun
    'low': '#eba72c',     # bottom-left
    'dark': '#cf7a14',    # bottom-right, facing away
    'fill': '#f5c040',    # under the faces
    'line': '#9a5f14',    # outline round the setting
}
STROKE = 3
STONE_STROKE = 2
GLINT = ((0.0, 0.9), (-0.42, 0.28), (-0.06, 0.04))   # in units of (hw, hh) from the centre


def mapper_pointwise(f):
    """Adapt a per-point mapping f(u, v) -> (x, y) to the list mapper diamond_gem wants."""
    return lambda pts: [f(u, v) for u, v in pts]


def rhombus(cx, cy, hw, hh):
    """Tips in the order top, right, bottom, left (v up)."""
    return [(cx, cy + hh), (cx + hw, cy), (cx, cy - hh), (cx - hw, cy)]


def edges(poly, steps, closed=True):
    """The polygon with each edge cut into `steps` pieces; corners stay exact vertices."""
    out = []
    n = len(poly)
    for i in range(n if closed else n - 1):
        (a, b), (c, d) = poly[i], poly[(i + 1) % n]
        out += [(a + (c - a) * k / steps, b + (d - b) * k / steps) for k in range(steps)]
    if not closed:
        out.append(poly[-1])
    return out


def diamond_gem(name, mapper, cx, cy, hw, hh, setting=None, outer=None, steps=4, stone=STONE, gold=SETTING,
                stroke=STROKE, stone_stroke=STONE_STROKE, glint=GLINT):
    """Shapes for a pointed diamond gem of half width hw and half height hh at (cx, cy),
    optionally in a gold setting: either `setting` wide (measured square to its edges) or
    reaching the half sizes `outer` = (half width, half height). All in gem-local units.
    Returns [Shape], back to front."""
    m = lambda poly: mapper(edges(poly, steps))
    shapes = []
    inner = rhombus(cx, cy, hw, hh)
    top, right, bottom, left = inner
    c = (cx, cy)
    if setting or outer:
        if outer is None:
            side = math.hypot(hw, hh)
            outer = (hw + setting * side / hh, hh + setting * side / hw)
        outer = rhombus(cx, cy, *outer)
        shapes.append(Shape(name + ' setting', m(outer), gold['fill'], 'none', 0))
        for i, tone in enumerate(('mid', 'dark', 'low', 'light')):
            j = (i + 1) % 4
            face = [outer[i], outer[j], inner[j], inner[i]]
            shapes.append(Shape('%s setting %s' % (name, tone), m(face), gold[tone], 'none', 0))
        shapes.append(Shape(name + ' setting outline', m(outer), 'none', gold['line'], stroke))
    for tone, (a, b) in (('light', (left, top)), ('mid', (top, right)), ('dark', (right, bottom)), ('low', (bottom, left))):
        shapes.append(Shape('%s facet %s' % (name, tone), m([c, a, b]), stone[tone], 'none', 0))
    if glint:
        glint = [(cx + hw * gu, cy + hh * gv) for gu, gv in glint]
        shapes.append(Shape(name + ' glint', m(glint), stone['glint'], 'none', 0))
    shapes.append(Shape(name + ' rim', m(inner), 'none', stone['rim'], stone_stroke))
    return shapes


def path_d(points):
    return 'M' + ' L'.join('%.2f,%.2f' % (x, y) for x, y in points) + ' Z'


def svg(s):
    stroke = ('stroke="none"' if s.stroke == 'none' or not s.width else
              'stroke="%s" stroke-width="%g" stroke-linejoin="miter" stroke-miterlimit="12"' % (s.stroke, s.width))
    return '<path id="%s" d="%s" fill="%s" %s/>' % (s.id, path_d(s.points), s.fill, stroke)


def write(body, shapes, group=None):
    """Append the shapes as SVG paths to the list of lines `body`, inside <g id=group> if given."""
    if group:
        body.append('<g id="%s">' % group)
    body += [svg(s) for s in shapes]
    if group:
        body.append('</g>')

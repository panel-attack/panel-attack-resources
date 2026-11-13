#   Library, writes nothing: project() lays flat SVG art on a plane through the stage camera, for the
#   floor, rail and table generators.
#
#   Flat SVG art in, projected SVG art out.
#
#   Scene pieces are drawn flat - a floor pattern seen from straight above, a
#   chair back seen straight on - where they are easy to draw and edit in any
#   SVG editor. project() then places that drawing on a plane in the scene and
#   draws it through the stage camera. Groups, ids, fills, gradients and
#   stroke widths carry over untouched, so the projected file imports into
#   Pixelmator with the same layer names and styles as the flat one.
#
#   Supported input: <g> (with transform), <path> (all commands except arcs),
#   <circle>, <ellipse>, <rect>, <polygon>, <polyline>, and a <defs> block that
#   is copied through as is. Transforms: matrix, translate, scale, rotate.

import math
import re
import xml.etree.ElementTree as ET

SVG_NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG_NS)
INKSCAPE_LABEL = '{http://www.inkscape.org/namespaces/inkscape}label'
KAPPA = 0.5522847498

GEOMETRY_ATTRS = {'d', 'transform', 'cx', 'cy', 'r', 'rx', 'ry', 'x', 'y', 'width', 'height', 'points'}


# ---------------------------------------------------------------- affine transforms

def multiply(m, n):
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


IDENTITY = (1, 0, 0, 1, 0, 0)


def parse_transform(text):
    m = IDENTITY
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', text or ''):
        v = [float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?', args)]
        if name == 'matrix':
            t = tuple(v)
        elif name == 'translate':
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale':
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == 'rotate':
            r = math.radians(v[0])
            t = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)
            if len(v) == 3:
                t = multiply(multiply((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        else:
            raise ValueError('unsupported transform %s' % name)
        m = multiply(m, t)
    return m


def apply(m, p):
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


# ---------------------------------------------------------------- geometry as subpaths of cubics
#
#   A shape is a list of subpaths; a subpath is (start, [segment...], closed)
#   where a segment is ('L', p) or ('C', c1, c2, p).

def parse_path(d):
    tokens = re.findall(r'[MmLlHhVvCcSsQqTtZzAa]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?', d)
    subpaths, segs, start, cur, prev_ctrl, cmd = [], None, None, (0.0, 0.0), None, None
    i = 0

    def num():
        nonlocal i
        i += 1
        return float(tokens[i - 1])

    def point(rel):
        x, y = num(), num()
        return (cur[0] + x, cur[1] + y) if rel else (x, y)

    while i < len(tokens):
        if re.match(r'[A-Za-z]', tokens[i]):
            cmd = tokens[i]
            i += 1
        rel, c = cmd.islower(), cmd.upper()
        if c == 'M':
            if segs is not None:
                subpaths.append((start, segs, False))
            cur = start = point(rel)
            segs = []
            cmd = 'l' if rel else 'L'
            prev_ctrl = None
        elif c == 'Z':
            subpaths.append((start, segs, True))
            segs, cur, prev_ctrl = None, start, None
            continue
        elif c in 'LHV':
            if c == 'L':
                p = point(rel)
            elif c == 'H':
                x = num()
                p = (cur[0] + x if rel else x, cur[1])
            else:
                y = num()
                p = (cur[0], cur[1] + y if rel else y)
            segs.append(('L', p))
            cur, prev_ctrl = p, None
        elif c in 'CS':
            if c == 'C':
                c1 = point(rel)
            else:
                c1 = (2 * cur[0] - prev_ctrl[0], 2 * cur[1] - prev_ctrl[1]) if prev_ctrl else cur
            c2, p = point(rel), point(rel)
            segs.append(('C', c1, c2, p))
            cur, prev_ctrl = p, c2
        elif c in 'QT':
            if c == 'Q':
                q = point(rel)
            else:
                q = (2 * cur[0] - prev_ctrl[0], 2 * cur[1] - prev_ctrl[1]) if prev_ctrl else cur
            p = point(rel)
            c1 = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
            c2 = (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1]))
            segs.append(('C', c1, c2, p))
            cur, prev_ctrl = p, q
        else:
            raise ValueError('arc commands are not supported; convert arcs to curves first')
    if segs:
        subpaths.append((start, segs, False))
    return subpaths


def ellipse(cx, cy, rx, ry):
    k, pts = KAPPA, []
    quads = [((cx + rx, cy), (cx + rx, cy + k * ry), (cx + k * rx, cy + ry), (cx, cy + ry)),
             ((cx, cy + ry), (cx - k * rx, cy + ry), (cx - rx, cy + k * ry), (cx - rx, cy)),
             ((cx - rx, cy), (cx - rx, cy - k * ry), (cx - k * rx, cy - ry), (cx, cy - ry)),
             ((cx, cy - ry), (cx + k * rx, cy - ry), (cx + rx, cy - k * ry), (cx + rx, cy))]
    return [((cx + rx, cy), [('C', q[1], q[2], q[3]) for q in quads], True)]


def polygon(points, closed=True):
    return [(points[0], [('L', p) for p in points[1:]], closed)]


def shape_of(el):
    tag = el.tag.split('}')[-1]
    g = lambda k, default=0.0: float(el.get(k, default))
    if tag == 'path':
        return parse_path(el.get('d', ''))
    if tag == 'circle':
        return ellipse(g('cx'), g('cy'), g('r'), g('r'))
    if tag == 'ellipse':
        return ellipse(g('cx'), g('cy'), g('rx'), g('ry'))
    if tag == 'rect':
        x, y, w, h = g('x'), g('y'), g('width'), g('height')
        return polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
    if tag in ('polygon', 'polyline'):
        v = [float(t) for t in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?', el.get('points', ''))]
        return polygon(list(zip(v[::2], v[1::2])), tag == 'polygon')
    return None


def transform_shape(shape, m):
    return [(apply(m, start), [(s[0],) + tuple(apply(m, p) for p in s[1:]) for s in segs], closed)
            for start, segs, closed in shape]


# ---------------------------------------------------------------- projection

def split_cubic(p0, c1, c2, p3, t):
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, c = lerp(p0, c1), lerp(c1, c2), lerp(c2, p3)
    d, e = lerp(a, b), lerp(b, c)
    f = lerp(d, e)
    return (p0, a, d, f), (f, e, c, p3)


def project_shape(shape, to_screen, pieces=6):
    """Map a flat shape to the screen. Straight lines stay straight under a
    perspective view, so only their ends are mapped; curves are cut into short
    pieces whose control points are mapped (good to a fraction of a pixel)."""
    out = []
    for start, segs, closed in shape:
        new, cur = [], start
        for s in segs:
            if s[0] == 'L':
                new.append(('L', to_screen(s[1])))
                cur = s[1]
                continue
            rest = (cur,) + tuple(s[1:])
            for k in range(pieces, 0, -1):
                piece, rest = split_cubic(*rest, 1 / k) if k > 1 else (rest, None)
                new.append(('C',) + tuple(to_screen(p) for p in piece[1:]))
            cur = s[3]
        out.append((to_screen(start), new, closed))
    return out


def path_d(shape):
    parts = []
    for start, segs, closed in shape:
        parts.append('M%.2f,%.2f' % start)
        for s in segs:
            parts.append(('L%.2f,%.2f' % s[1]) if s[0] == 'L' else
                         'C%.2f,%.2f %.2f,%.2f %.2f,%.2f' % (s[1] + s[2] + s[3]))
        if closed:
            parts.append('Z')
    return ' '.join(parts)


def project(flat_path, out_path, to_screen, width, height):
    """Project every shape in the flat SVG at flat_path; write a screen-space SVG."""
    root = ET.parse(flat_path).getroot()
    out = ET.Element('{%s}svg' % SVG_NS, {'width': str(width), 'height': str(height),
                                          'viewBox': '0 0 %d %d' % (width, height)})

    def walk(src, dst, m):
        for el in src:
            tag = el.tag.split('}')[-1]
            if tag == 'defs':
                dst.append(el)
                continue
            em = multiply(m, parse_transform(el.get('transform')))
            attrs = {k: v for k, v in el.attrib.items() if k not in GEOMETRY_ATTRS}
            if INKSCAPE_LABEL in attrs:
                attrs['id'] = attrs.pop(INKSCAPE_LABEL)
            if tag == 'g':
                walk(el, ET.SubElement(dst, '{%s}g' % SVG_NS, attrs), em)
                continue
            shape = shape_of(el)
            if shape:
                attrs['d'] = path_d(project_shape(transform_shape(shape, em), to_screen))
                ET.SubElement(dst, '{%s}path' % SVG_NS, attrs)

    walk(root, out, IDENTITY)
    ET.indent(out)
    ET.ElementTree(out).write(out_path, xml_declaration=False, encoding='unicode')

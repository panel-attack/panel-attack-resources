"""Library, writes nothing: path maths, and the text of each part SVG (__main__ writes the files).

The generators only write absolute M, L, H, V, C, Q and Z commands, so a path's bounding box is the box
of its points (control points included, which only makes it larger) and moving a path is adding to every
coordinate. Part SVGs are written in exactly the form the generators use, which Pixelmator Pro opens:
a root with integer width and height and a viewBox starting at 0 0, then defs, then one group."""

import math
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

SVG_NS = 'http://www.w3.org/2000/svg'
TOKEN = re.compile(r'[MLHVCQZmlhvcqz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
ALLOWED = {     # every element and attribute the generators' SVGs use
    'svg': {'xmlns', 'width', 'height', 'viewBox'},
    'defs': set(),
    'linearGradient': {'id', 'x1', 'y1', 'x2', 'y2', 'gradientUnits'},
    'stop': {'offset', 'stop-color'},
    'g': {'id', 'opacity', 'fill', 'stroke'},
    'path': {'id', 'd', 'fill', 'fill-opacity', 'opacity', 'stroke', 'stroke-width', 'stroke-linejoin',
             'stroke-linecap', 'stroke-miterlimit'},
}


def _tokens(d):
    return TOKEN.findall(d)


def _segments(d):
    """(command, [numbers]) for each command in the path."""
    out = []
    for tok in _tokens(d):
        if tok.isalpha():
            if tok.islower() and tok not in 'z':
                raise ValueError('relative path command %r is not supported' % tok)
            out.append((tok.upper(), []))
        else:
            out[-1][1].append(float(tok))
    return out


def _points(d):
    x = y = 0.0
    for cmd, nums in _segments(d):
        if cmd == 'H':
            for v in nums:
                x = v
                yield x, y
        elif cmd == 'V':
            for v in nums:
                y = v
                yield x, y
        elif cmd != 'Z':
            for i in range(0, len(nums) - 1, 2):
                x, y = nums[i], nums[i + 1]
                yield x, y


def path_bbox(d):
    pts = list(_points(d))
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def fmt(v):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def scale_path(d, k):
    """The path scaled by k about the origin."""
    parts = []
    for cmd, nums in _segments(d):
        if cmd in 'HV':
            args = ' '.join(fmt(v * k) for v in nums)
        else:
            args = ' '.join('%s,%s' % (fmt(nums[i] * k), fmt(nums[i + 1] * k)) for i in range(0, len(nums) - 1, 2))
        parts.append(cmd + args)
    return ' '.join(parts)


def shift_path(d, dx, dy):
    """The path moved by (-dx, -dy)."""
    parts = []
    for cmd, nums in _segments(d):
        if cmd == 'H':
            args = ' '.join(fmt(v - dx) for v in nums)
        elif cmd == 'V':
            args = ' '.join(fmt(v - dy) for v in nums)
        else:
            args = ' '.join('%s,%s' % (fmt(nums[i] - dx), fmt(nums[i + 1] - dy)) for i in range(0, len(nums) - 1, 2))
        parts.append(cmd + args)
    return ' '.join(parts)


def union(boxes):
    boxes = [b for b in boxes if b is not None]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def crop_box(bbox, pad, canvas=None):
    """(x, y, w, h) in whole pixels holding bbox plus pad, with even w and h (the loader asserts a @2x
    image's size halves exactly), clamped to the canvas (w, h) if given."""
    x0, y0 = math.floor(bbox[0] - pad), math.floor(bbox[1] - pad)
    x1, y1 = math.ceil(bbox[2] + pad), math.ceil(bbox[3] + pad)
    if canvas:
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, canvas[0]), min(y1, canvas[1])
    if (x1 - x0) % 2:
        if canvas and x1 + 1 > canvas[0]:
            x0 -= 1
        else:
            x1 += 1
    if (y1 - y0) % 2:
        if canvas and y1 + 1 > canvas[1]:
            y0 -= 1
        else:
            y1 += 1
    return x0, y0, x1 - x0, y1 - y0


def stem_box(bbox, stem, pad):
    """(x, y, w, h) holding bbox plus pad with the stem point exactly at its centre, so a template's
    "center" anchor and pivot are its stem. w and h are even, so the stem must be a whole pixel."""
    sx, sy = stem
    if sx != int(sx) or sy != int(sy):
        raise ValueError('the stem must sit on a whole pixel')
    hx = math.ceil(max(sx - (bbox[0] - pad), bbox[2] + pad - sx))
    hy = math.ceil(max(sy - (bbox[1] - pad), bbox[3] + pad - sy))
    return int(sx - hx), int(sy - hy), 2 * hx, 2 * hy


def foot_box(bbox, pad):
    """(x, y, w, h) holding bbox plus pad above and to the sides, with its bottom centre on the foot at (0, 0),
    so a template's "bottomCenter" anchor and pivot are where it stands. Anything below the foot is cut off."""
    hx = math.ceil(max(-bbox[0], bbox[2]) + pad)
    top = math.floor(bbox[1] - pad)
    top -= top % 2
    return -hx, top, 2 * hx, -top


# ---------------------------------------------------------------- elements

def local(tag):
    return tag.split('}')[-1]


def element_bbox(el):
    """Box of every path under el, widened by half of the widest stroke drawn."""
    boxes = []
    for p in el.iter():
        if local(p.tag) != 'path' or not p.get('d'):
            continue
        b = path_bbox(p.get('d'))
        if b is None:
            continue
        w = 0.0
        if p.get('stroke', 'none') != 'none':
            w = float(p.get('stroke-width', 1)) / 2
        boxes.append((b[0] - w, b[1] - w, b[2] + w, b[3] + w))
    return union(boxes)


def shifted(el, dx, dy):
    """A copy of el (no namespace on tags) with every path moved by (-dx, -dy)."""
    out = ET.Element(local(el.tag), dict(el.attrib))
    if out.tag == 'path':
        out.set('d', shift_path(el.get('d'), dx, dy))
    for ch in el:
        out.append(shifted(ch, dx, dy))
    return out


def gradient_refs(elements):
    refs = set()
    for el in elements:
        for e in el.iter():
            for v in e.attrib.values():
                refs.update(re.findall(r'url\(#([^)]+)\)', v))
    return refs


def shifted_gradient(grad, dx, dy):
    out = ET.Element('linearGradient', dict(grad.attrib))
    if grad.get('gradientUnits') == 'userSpaceOnUse':
        for k, off in (('x1', dx), ('x2', dx), ('y1', dy), ('y2', dy)):
            if out.get(k) is not None:
                out.set(k, fmt(float(out.get(k)) - off))
    for st in grad:
        out.append(ET.Element('stop', dict(st.attrib)))
    return out


def serialise(el):
    attrs = ''.join(' %s=%s' % (k, quoteattr(v)) for k, v in el.attrib.items())
    tag = local(el.tag)
    if len(el) == 0:
        return '<%s%s/>' % (tag, attrs)
    inner = '\n'.join(serialise(ch) for ch in el)
    return '<%s%s>\n%s\n</%s>' % (tag, attrs, inner, tag)


def part_svg(name, elements, gradients, box):
    """The SVG text of a part: the elements moved so box (x, y, w, h) is the canvas, in the generators'
    form. gradients maps id -> linearGradient element; only the referenced ones are written."""
    x, y, w, h = box
    body = [shifted(el, x, y) for el in elements]
    refs = gradient_refs(body)
    missing = refs - set(gradients)
    if missing:
        raise ValueError('%s: undefined gradients %s' % (name, sorted(missing)))
    defs = ''.join(serialise(shifted_gradient(gradients[g], x, y)) for g in sorted(refs))
    group = ET.Element('g', {'id': name})
    group.extend(body)
    head = '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n' % (w, h, w, h)
    if defs:
        head += '<defs>%s</defs>\n' % defs.replace('\n', '')
    return head + serialise(group) + '\n</svg>\n'


def validate(text):
    """Problems that could stop Pixelmator Pro opening the SVG, or [] when it has the generators' form."""
    problems = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return ['not well-formed XML: %s' % e]
    if root.tag != '{%s}svg' % SVG_NS:
        return ['the root is %s, not an svg element in the SVG namespace' % root.tag]
    w, h = root.get('width', ''), root.get('height', '')
    if not (w.isdigit() and h.isdigit()):
        return ['width and height must be whole pixels, got %r x %r' % (w, h)]
    w, h = int(w), int(h)
    if w < 2 or h < 2 or w % 2 or h % 2:
        problems.append('size %d x %d must be even and at least 2' % (w, h))
    if root.get('viewBox') != '0 0 %d %d' % (w, h):
        problems.append('viewBox %r must be "0 0 %d %d"' % (root.get('viewBox'), w, h))
    ids = set()
    for el in root.iter():
        tag = local(el.tag)
        if tag not in ALLOWED:
            problems.append('element <%s> is not one the generators write' % tag)
            continue
        extra = set(el.attrib) - ALLOWED[tag]
        if extra:
            problems.append('<%s> has attributes the generators never write: %s' % (tag, sorted(extra)))
        if tag == 'linearGradient':
            ids.add(el.get('id'))
    refs = gradient_refs([root])
    if refs - ids:
        problems.append('undefined gradients: %s' % sorted(refs - ids))
    paths = [el for el in root.iter() if local(el.tag) == 'path']
    if not paths:
        problems.append('no paths')
    for p in paths:
        try:
            if path_bbox(p.get('d', '')) is None:
                problems.append('path %r is empty' % p.get('id'))
        except ValueError as e:
            problems.append('path %r: %s' % (p.get('id'), e))
    box = element_bbox(root)
    if box is not None and (box[2] <= 0 or box[3] <= 0 or box[0] >= w or box[1] >= h):
        problems.append('nothing is drawn inside the canvas')
    if box is not None and (box[2] - box[0] < 0.5 or box[3] - box[1] < 0.5):
        problems.append('the drawing has a degenerate box %s' % (box,))
    return problems

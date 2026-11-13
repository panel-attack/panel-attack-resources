#   Writes SVG, run by `python3 -m scene_export render`: EsmeTerrace/rail_flat.svg (one post, seen
#   straight on) and EsmeTerrace/rail.svg (the balustrade sheet).
#
#   The gold balustrade around the terrace, in the style of the reference:
#   a thick handrail (bright top, lit front face, deep underside), a gold base rail
#   sitting on the floor, and between them gold posts that each carry a
#   pointed gem (gems.py) and a heart of two chunky C-scrolls.
#
#   Lit by the stage sun (high, behind the camera, slightly left): every gold
#   shape gets a sheen strip along its edges that face up/left and a shade
#   strip along those facing right/down, and the balusters darken softly just
#   under the handrail.
#
#   Step 1 writes rail_flat.svg: one post and its scrolls drawn flat,
#   seen straight on, in units of 1/1000 eye height (x along the rail, y up
#   is negative, the floor at y=0). Edit the numbers below, or edit that SVG
#   by hand and run --project-only.
#
#   Step 2 stands a copy of it on the terrace circle at every post angle,
#   projected through the stage camera onto the rail plane there, adds the
#   rails as bands following the circle, and writes rail.svg.
#
#   python3 -m EsmeTerrace.rail [--project-only]

import math
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np

from common import gems
from common.flat import IDENTITY, multiply, parse_transform, path_d, project_shape, shape_of, transform_shape
from common.terrace import built_terrace, rail_band, visible_theta_range
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))

FLAT = cutting.sheet_path('EsmeTerrace/rail_flat.svg')
OUT = cutting.sheet_path('EsmeTerrace/rail.svg')
CANVAS = (1536, 1024)
UNIT = 1000                       # flat drawing units per eye height

# Heights and widths in eye heights. The terrace's fitted rail height (0.385)
# is unchanged; the handrail now rises above it to the reference's top line
# (about y541 at the centre, y557 at x=200).
BAY = 0.57                        # post to post, along the rail (~170px at the centre)
RAIL_TOP = 0.472                  # top of the handrail
TOP_RAIL = 0.098                  # handrail depth, so its underside is at RAIL_TOP - TOP_RAIL
HANDRAIL = (                      # (name, depth from RAIL_TOP to its bottom edge, colour), top to bottom
    ('top', 0.026, '#fff27a'),            # upward-facing top surface: brightest
    ('face', 0.060, '#f29a0c'),           # front face, lit
    ('under', 0.074, '#7a2e02'),          # underside, in shade
    ('under glow', TOP_RAIL, '#b8600a'),  # reflected light at the underside's lower lip
)
BASE_RAIL = 0.090                 # base rail height above the floor
BASE_LIP = (0.072, 0.086)         # lit upward lip near the base rail's top
BASE_FOOT_SHADE = (0.004, 0.014)  # shaded strip along the base rail's foot
BASE_SHADE = (0.014, 0.034)       # lower face turning under, in shade (the bar sits straight on the floor)

POST_HALF = 0.036
POST_CAP = dict(half=0.050, height=0.030)
POST_FOOT = dict(half=0.052, height=0.030)
GEM = dict(v=0.228, half_w=0.024, half_h=0.046, setting=0.011)  # stone half sizes, gold setting width
GEM_STROKES = (2.5, 1.5)          # setting and stone outlines, px (thinner than STROKE: the gem is small)

# Between two posts, a heart of two C-scrolls: each half rises from a shared
# foot on the base rail, swings out round a lobe that touches the handrail,
# and curls back inside its own lobe. A drop hangs from the handrail between.
HEART_FOOT = (0.0, 0.082)         # bay-centred; tucked just under the base rail
HEART_LOBE = ((0.13, 0.29), 0.086)  # lobe centre (mirrored) and radius
HEART_CURL = (0.052, 0.018, 280)  # curl radius at its start and end, and how far it turns (degrees)
HEART_WIDTH = (0.046, 0.032)      # ribbon width at the foot and at the curl's end
HEART_KNOB = 0.021                # radius of the round end of the curl
DROP = dict(stem=0.013, v=0.30, radius=0.024, point=0.034)  # stem half-width, ball centre, ball radius, tip below it

# Light on the flat drawing (u right, v up): toward the upper left, mostly up.
LIGHT = (-0.42, 0.91)
SHEEN_EDGE = dict(width=0.010, threshold=0.3)   # edges facing the light
SHADE_EDGE = dict(width=0.012, threshold=-0.2)  # edges facing away (right and down)
EDGE_INSET = 0.004                # strips start this far inside the outline, clear of the stroke
OCCLUSION = dict(colour='#5a2200', opacity=0.2, depths=(0.012, 0.026, 0.045))  # stacked bands under the handrail

STROKE = 3
GOLD_LINE = '#6e3204'
SHEEN = '#fff27a'
SHADE = '#b05c08'
FLAT_COLOURS = {
    'base rail': '#f2a21c',
    'base rail lip': SHEEN,
    'base rail foot': '#a9560a',
    'base rail shade': '#d27e0e',
}
GRADIENTS = {
    'goldGrad': ('#ffc634', '#e58a0a'),
}
GEM_GOLD = dict(gems.SETTING, line=GOLD_LINE)


# ---------------------------------------------------------------- the flat baluster

def fmt(points):
    return 'M' + ' L'.join('%.1f,%.1f' % (u * UNIT, -v * UNIT) for u, v in points) + ' Z'


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def densify(poly, step=0.004):
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        n = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / step)))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    return out


def edge_strips(poly, threshold, width, inset=EDGE_INSET):
    """Strips just inside a closed (u, v) outline along each run of edge whose outward
    normal faces the light (threshold > 0: dot > threshold) or away from it (threshold
    < 0: dot < threshold). Each strip tapers to nothing at its ends."""
    p = np.array(densify(poly))
    area = np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    if area < 0:
        p = p[::-1]
    d = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
    n = np.stack([d[:, 1], -d[:, 0]], 1)
    n /= np.hypot(n[:, 0], n[:, 1])[:, None] + 1e-12
    dot = n @ np.array(LIGHT) / math.hypot(*LIGHT)
    on = dot > threshold if threshold > 0 else dot < threshold
    if on.all():
        on[0] = False
    start = int(np.argmin(on))           # begin the scan off a run so none wraps
    idx = [(start + k) % len(p) for k in range(len(p))]
    runs, cur = [], []
    for i in idx:
        if on[i]:
            cur.append(i)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    strips = []
    for run in runs:
        if len(run) < 3:
            continue
        m = len(run)
        w = [width * min(1.0, 0.15 + 3.0 * min(k, m - 1 - k) / m) for k in range(m)]
        outer = [p[i] - n[i] * inset for i in run]
        inner = [p[i] - n[i] * (inset + wk) for i, wk in zip(run, w)]
        strips.append([tuple(q) for q in outer + inner[::-1]])
    return strips


def clip_above(poly, v0):
    """The part of a closed polygon with v >= v0 (Sutherland-Hodgman against one line)."""
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ina, inb = a[1] >= v0, b[1] >= v0
        if ina:
            out.append(a)
        if ina != inb:
            t = (v0 - a[1]) / (b[1] - a[1])
            out.append((a[0] + (b[0] - a[0]) * t, v0))
    return out if len(out) >= 3 else None


class Flat:
    """Collects the gold shapes of the flat baluster with their light, shade and occlusion."""

    def __init__(self, v_top):
        self.body, self.v_top = [], v_top

    def raw(self, line):
        self.body.append(line)

    def gold(self, name, poly, sheen=SHEEN_EDGE, shade=SHADE_EDGE, occlude=True):
        self.body.append('<path id="%s" d="%s" fill="url(#goldGrad)" stroke="%s" stroke-width="%d" '
                         'stroke-linejoin="round"/>' % (name, fmt(poly), GOLD_LINE, STROKE))
        for label, spec, colour in (('sheen', sheen, SHEEN), ('shade', shade, SHADE)):
            for k, st in enumerate(edge_strips(poly, spec['threshold'], spec['width'])):
                self.body.append('<path id="%s %s%s" d="%s" fill="%s" stroke="none"/>'
                                 % (name, label, ' %d' % (k + 1) if k else '', fmt(st), colour))
        if occlude:
            o = OCCLUSION
            for k, depth in enumerate(o['depths']):
                part = clip_above(densify(poly), self.v_top - depth)
                if part:
                    self.body.append('<path id="%s occlusion %d" d="%s" fill="%s" fill-opacity="%g" stroke="none"/>'
                                     % (name, k + 1, fmt(part), o['colour'], o['opacity']))


def heart_centreline(step=0.002):
    """Left half of the heart: straight up from the foot to the lobe, round
    the lobe clockwise until heading down, then a tightening curl."""
    p = np.array(HEART_FOOT, float)
    (cu, cv), r = HEART_LOBE
    c = np.array([-cu, cv])
    d = c - p
    dist = np.hypot(*d)
    heading = math.atan2(d[1], d[0]) + math.asin(r / dist)
    straight = math.sqrt(dist ** 2 - r ** 2)
    lobe_turn = heading + math.pi / 2
    r0, r1, curl = HEART_CURL[0], HEART_CURL[1], math.radians(HEART_CURL[2])
    curl_length = curl * (r0 + r1) / 2
    lengths = (straight, r * lobe_turn, curl_length)
    pts, s = [], 0.0
    while s <= sum(lengths):
        pts.append(p.copy())
        if s < lengths[0]:
            k = 0.0
        elif s < lengths[0] + lengths[1]:
            k = 1 / r
        else:
            f = (s - lengths[0] - lengths[1]) / curl_length
            k = 1 / (r0 + (r1 - r0) * f)
        heading -= k * step
        p = p + step * np.array([math.cos(heading), math.sin(heading)])
        s += step
    return np.array(pts)


def heart_outline(sign):
    """Closed ribbon round one half of the heart, sign=-1 for the left half."""
    pts = heart_centreline()
    t = np.linspace(0, 1, len(pts))
    d = np.gradient(pts, axis=0)
    normal = np.stack([-d[:, 1], d[:, 0]], 1) / np.hypot(d[:, 0], d[:, 1])[:, None]
    w = (HEART_WIDTH[0] + (HEART_WIDTH[1] - HEART_WIDTH[0]) * t)[:, None] / 2
    ring = np.concatenate([pts + normal * w, (pts - normal * w)[::-1]])[::3]
    end = pts[-1]
    return [(-sign * u, v) for u, v in ring], (-sign * end[0], end[1])


def circle(c, r, n=20):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def write_flat(path):
    v_top = RAIL_TOP - TOP_RAIL
    f = Flat(v_top)
    # The bay is drawn half a bay to the right of the post, as it stands on the rail.
    f.raw('<g id="bay" transform="translate(%.1f,0)">' % (BAY / 2 * UNIT))
    d = DROP
    f.gold('drop stem', rect(-d['stem'], d['stem'], d['v'], v_top + 0.005))
    ball = [(d['radius'] * math.cos(a), d['v'] + d['radius'] * math.sin(a)) for a in np.linspace(0, math.pi, 12)]
    tip = (0, d['v'] - d['radius'] - d['point'])
    left = [(-d['radius'] * 0.55, d['v'] - d['radius'] * 0.8)]
    right = [(d['radius'] * 0.55, d['v'] - d['radius'] * 0.8)]
    f.gold('drop', right + ball + left + [tip])
    for side, sign in (('left', -1), ('right', 1)):
        ribbon, end = heart_outline(sign)
        f.raw('  <g id="%s scroll">' % side)
        f.gold('%s scroll arm' % side, ribbon)
        f.gold('%s scroll knob' % side, circle(end, HEART_KNOB), sheen=dict(SHEEN_EDGE, width=0.007),
               shade=dict(SHADE_EDGE, width=0.007))
        f.raw('  </g>')
    f.raw('</g>')
    f.raw('<g id="post">')
    f.gold('post', rect(-POST_HALF, POST_HALF, BASE_RAIL - 0.01, v_top + 0.005), sheen=dict(SHEEN_EDGE, width=0.013),
           shade=dict(SHADE_EDGE, width=0.015))
    f.gold('post foot', rect(-POST_FOOT['half'], POST_FOOT['half'], BASE_RAIL - 0.01, BASE_RAIL + POST_FOOT['height']),
           sheen=dict(SHEEN_EDGE, width=0.007), shade=dict(SHADE_EDGE, width=0.007))
    f.gold('post cap', rect(-POST_CAP['half'], POST_CAP['half'], v_top - POST_CAP['height'], v_top + 0.005),
           sheen=dict(SHEEN_EDGE, width=0.007), shade=dict(SHADE_EDGE, width=0.007))
    g = GEM
    gem_shapes = gems.diamond_gem('gem', lambda pts: [(u * UNIT, -v * UNIT) for u, v in pts],
                                  0.0, g['v'], g['half_w'], g['half_h'], setting=g['setting'], steps=1,
                                  gold=GEM_GOLD, stroke=GEM_STROKES[0], stone_stroke=GEM_STROKES[1])
    gems.write(f.body, gem_shapes, group='gem')
    f.raw('</g>')

    defs = ''.join('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/>'
                   '<stop offset="1" stop-color="%s"/></linearGradient>' % (gid, a, b)
                   for gid, (a, b) in GRADIENTS.items())
    w, h = (BAY + 0.15) * UNIT, (RAIL_TOP + 0.05) * UNIT
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%d %d %d %d">\n'
                 % (w, h, -0.075 * UNIT, -h + 20, w, h))
        fh.write('<defs>%s</defs>\n<g id="baluster">\n%s\n</g>\n</svg>\n' % (defs, '\n'.join(f.body)))


# ---------------------------------------------------------------- placing it on the rail

def flat_elements(path):
    """[(group path, attrs, shape)] for every shape in the flat file, and its defs."""
    root = ET.parse(path).getroot()
    out, defs = [], ''

    def walk(el, m, groups):
        nonlocal defs
        for child in el:
            tag = child.tag.split('}')[-1]
            if tag == 'defs':
                defs = ''.join(ET.tostring(c, encoding='unicode') for c in child)
                continue
            cm = multiply(m, parse_transform(child.get('transform')))
            if tag == 'g':
                walk(child, cm, groups + [child.get('id', 'group')])
                continue
            shape = shape_of(child)
            if shape:
                attrs = {k: v for k, v in child.attrib.items() if k not in ('d', 'transform')}
                out.append((groups, attrs, transform_shape(shape, cm)))
    walk(root, IDENTITY, [])
    return out, defs.replace(' xmlns="http://www.w3.org/2000/svg"', '').replace('ns0:', '')


def attr_text(attrs):
    return ' '.join('%s="%s"' % kv for kv in attrs.items())


def write_rail(path):
    t = built_terrace()
    elements, defs = flat_elements(FLAT)
    lo, hi = visible_theta_range(t, CANVAS[0], margin=80)
    step = BAY / t.radius
    thetas = [k * step for k in range(int(math.floor(lo / step)), int(math.ceil(hi / step)) + 1)]
    same = lambda p: p

    def band(name, low, high, fill, line=None):
        stroke = 'stroke="%s" stroke-width="%d" stroke-linejoin="round"' % (line, STROKE) if line else 'stroke="none"'
        return '  <path id="%s" d="%s" fill="%s" %s/>' % (name, rail_band(t, (lo, hi), low, high, same, 40), fill, stroke)

    body = ['<g id="Rail">', '<g id="balusters">']
    for n, theta in enumerate(sorted(thetas, key=abs), 1):
        post_at = lambda p, th=theta: t.on_rail(th, p[0] / UNIT, -p[1] / UNIT)
        bay_at = lambda p, th=theta + step / 2: t.on_rail(th, p[0] / UNIT - BAY / 2, -p[1] / UNIT)
        body.append('<g id="baluster %02d">' % n)
        open_groups = []
        for groups, attrs, shape in elements:
            groups = groups[1:]
            to_screen = bay_at if groups[:1] == ['bay'] else post_at
            while open_groups and open_groups != groups[:len(open_groups)]:
                body.append('</g>')
                open_groups.pop()
            for g in groups[len(open_groups):]:
                body.append('<g id="%s %02d">' % (g, n))
                open_groups.append(g)
            attrs = dict(attrs, id='%s %02d' % (attrs.get('id', 'shape'), n))
            body.append('  <path d="%s" %s/>' % (path_d(project_shape(shape, to_screen)), attr_text(attrs)))
        body += ['</g>'] * len(open_groups)
        body.append('</g>')
    body.append('</g>')

    c = FLAT_COLOURS
    body += ['<g id="base rail">',
             band('base rail body', 0.0, BASE_RAIL, c['base rail']),
             band('base rail lip', *BASE_LIP, c['base rail lip']),
             band('base rail foot shade', *BASE_FOOT_SHADE, c['base rail foot']),
             band('base rail shade', *BASE_SHADE, c['base rail shade']),
             band('base rail outline', 0.0, BASE_RAIL, 'none', GOLD_LINE),
             '</g>',
             '<g id="handrail">']
    top = RAIL_TOP
    for name, depth, colour in HANDRAIL:
        body.append(band('handrail %s' % name, RAIL_TOP - depth, top, colour))
        top = RAIL_TOP - depth
    body += [band('handrail outline', RAIL_TOP - TOP_RAIL, RAIL_TOP, 'none', GOLD_LINE),
             '</g>',
             '</g>']
    with open(path, 'w') as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n'
                % (*CANVAS, *CANVAS))
        f.write('<defs>%s</defs>\n%s\n</svg>\n' % (defs, '\n'.join(body)))
    return len(thetas)


def main():
    if '--project-only' not in sys.argv:
        write_flat(FLAT)
    n = write_rail(OUT)
    print('wrote', OUT, '(%d balusters)' % n)


def parts():
    root, grads = cutting.load('EsmeTerrace/rail.svg')
    return [cutting.static_part('EsmeTerrace/parts/rail/rail', [cutting.find_group(root, 'Rail')], grads, 'rail rail')]


if __name__ == '__main__':
    main()

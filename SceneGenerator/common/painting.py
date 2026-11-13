#   Library, writes nothing: the flat-shape kit the sky, the scenery and the trees beyond the rail are drawn with:
#   the Svg sheet writer, colour mixing, and crown_field's woods of small rounded tree crowns.
#
#   All flat shapes; tree scatter and ridgelines use seeded randomness so the
#   result is reproducible (change SEED or the constants below to re-roll).
#   Distant layers are hazier (mixed toward HAZE) and carry thin or no outlines.

import math
import random
import re


WIDTH, HEIGHT = 1536, 1024


SEED = 7


HAZE = '#9eeefc'


# depth colour stops sampled off the reference: (depth, crown body, shaded lower-right side,
# sunlit cap, dark gap between crowns, sunlit slope); far away a blue-green haze, greener nearer
LAND_STOPS = [
    (0.0, '#5cd2f6', '#40c2ea', '#78e0fc', '#28aee2', '#6cd8f8'),
    (0.22, '#56cce6', '#3cb8da', '#74dcf6', '#1a9ad2', '#66d4e8'),
    (0.4, '#44c6d0', '#30b0c4', '#70e2d6', '#2cb0c8', '#66d6c8'),
    (0.5, '#44bcc0', '#28a8bc', '#7cd8c4', '#1aa0c4', '#86d49a'),
    (0.75, '#3aa478', '#248c68', '#a8d862', '#14787a', '#a6d65a'),
    (1.0, '#2c9e58', '#1a7c50', '#b6d64c', '#035c62', '#b4dc48'),
    (1.15, '#9ccc3a', '#62a83a', '#e4ee6a', '#2a7a4a', '#d0e850'),
]


# hill colour by distance tier, sampled off the reference: one palette per tier, front mint-green,
# mid teal, back sky-blue. tier -> (crown body, sunlit top, shaded side, ground between crowns)
HILL_TIERS = {
    'back': ('#5cc1ec', '#8ddff9', '#4fb4e4', '#58bee8'),
    'mid': ('#6bccc6', '#8ce0d4', '#56b9d7', '#58bbdf'),
    'front': ('#93e6c7', '#a8efc5', '#6bcdd3', '#56b6d9'),
}


TIER_OF = {'far ridge': 'back', 'far ridge front': 'back', 'right hill back': 'back', 'left hill back': 'back',
           'far shore': 'mid', 'island': 'mid', 'trees before village': 'mid', 'right hill middle': 'mid',
           'left hill middle': 'mid', 'shore trees': 'mid',
           'right hill low': 'front', 'left hill low': 'front', 'left hill near': 'front'}


TIER_ACCENT = {'back': (0.2, '#6dd0db', 0.8)}   # (share, colour, blend): the back woods' occasional teal crown


TIER_LIGHT = (0.25, 0.45)         # slope light moves a crown this far toward its top (lit) / its side (shade)


TIER_SIDE_GROUND = 0.4           # shaded sides lean this far into the ground colour, so crown edges read


TIER_JITTER = 0.1                # per-crown random blend toward top or side: a few L either way, never a new hue


# canopy: every wooded mass is rows of small tree crowns stepping down the slope; the row behind
# shows through between crowns, with a dark underlay giving the gaps
CROWN_WIDTH = (9, 34)            # px, farthest .. nearest; each crown varies around this


CROWN_HEIGHT = (0.62, 0.9)       # crown height as a share of its width


CROWN_SPACING = (0.5, 1.05)      # centre-to-centre step along a row, in crown widths


ROW_STEP = 0.55                  # rows step down the slope by this share of a crown height


CROWN_SWELL = 0.45               # how much crown size swells and shrinks along a row


CROWN_JITTER = 0.3               # crown bases wander up and down by this share of a crown height


SLOPE_LIGHT = 0.75               # sunlit slope patches blend this far toward the slope colour


SLOPE_SHADE = 0.5                # hollows blend this far toward the gap colour


SLOPE_WAVES = (210, 120)         # px wavelengths of the light and shade patches across each hill


SLOPE_LEVELS = 2                 # tone steps each side of the plain body colour


CROWN_POINTY = 0.16              # share of crowns that are tall, pointed conifers


EDGE_CONTRAST = (1.0, 1.0)       # cap and side strength in the farthest .. mid rows, so the back fades into haze


SIDE_MIN_WIDTH = 9               # crowns narrower than this get no separate shaded side (too small to read, keeps the file small)


CROWN_SNAP_BELOW = 18            # crowns narrower than this px use whole-pixel coordinates


LOOSE_UNTIL = 0.5                # woods nearer than this depth keep their neat rows; farther ones loosen


ROW_WANDER = 0.9                 # crest wander of a far row, in crown heights


LOOSE_JITTER = 0.5               # extra up-and-down scatter of far crowns, in crown heights


LOOSE_TALL = 0.1                 # extra share of tall pointed trees far away


LOOSE_GAPS = 0.2                 # share of far crowns left out, opening gaps and clumps


LOOSE_CLIMB = 0.3                # share of far crowns that rise up into the row behind


LOOSE_SHADOW = (0.0, 0.3)       # far crown shadows blend this far (random) from the gap colour toward the body


LOOSE_NO_EDGE = 0.12             # share of far crowns drawn without a lit cap (and, separately, a shaded side)


CROWN_BIG = 0.05                 # share of crowns that are big old trees spanning two rows


CROWN_BIG_MAX = 1.9              # a big old tree is at most this many typical crown widths across


FAR_SLOPE_DARKEN = 0.6           # a distant ridge's plain slope blends this far toward its side colour at its foot


HAZE_WAVES = (70, 29)            # px wavelengths of the ridge haze's swell along its length


CLUMP_THIN = (0.45, 0.1)         # below a far ridge's crest rows, the clump threshold: first row, rise per row


RIDGE_HAZE = ((4, 0.08), (9, 0.04))   # (height px, opacity) haze layers at the foot of a ridge


RIDGE_HAZE_TINT = 0.15           # the haze is the ridge's own body colour mixed this far toward HAZE, so it stays green


FLOWER, FLOWER_DEEP, FLOWER_CENTRE = '#ff9cc2', '#f25c95', '#ffe07a'


BLOSSOM_MARGIN = 1.5             # blossoms keep this many radii inside the foliage edge


# ================================================================ helpers

def hexrgb(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    ra, rb = hexrgb(a), hexrgb(b)
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * t) for x, y in zip(ra, rb))


def haze(pair, t):
    if isinstance(pair, str):
        return mix(pair, HAZE, t)
    return tuple(mix(c, HAZE, t) for c in pair)


def f(v):
    return ('%.1f' % v).rstrip('0').rstrip('.')


def fs(v):
    return ('%.5f' % v).rstrip('0').rstrip('.')


def poly(points, close=True):
    d = 'M' + ' L'.join('%s,%s' % (f(x), f(y)) for x, y in points)
    return d + (' Z' if close else '')


def arc_to_cubics(x0, y0, rx, ry, large, sweep, x1, y1):
    """SVG endpoint arc (no rotation) as cubic Bezier segments."""
    if rx == 0 or ry == 0 or (x0 == x1 and y0 == y1):
        return [(x0, y0, x1, y1, x1, y1)]
    dx, dy = (x0 - x1) / 2, (y0 - y1) / 2
    lam = (dx / rx) ** 2 + (dy / ry) ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * dy * dy - ry * ry * dx * dx
    den = rx * rx * dy * dy + ry * ry * dx * dx
    co = math.sqrt(max(0.0, num / den)) * (-1 if large == sweep else 1)
    cxp, cyp = co * rx * dy / ry, -co * ry * dx / rx
    cx, cy = cxp + (x0 + x1) / 2, cyp + (y0 + y1) / 2
    t0 = math.atan2((dy - cyp) / ry, (dx - cxp) / rx)
    t1 = math.atan2((-dy - cyp) / ry, (-dx - cxp) / rx)
    dt = t1 - t0
    if sweep and dt < 0:
        dt += 2 * math.pi
    elif not sweep and dt > 0:
        dt -= 2 * math.pi
    n = max(1, int(math.ceil(abs(dt) / (math.pi / 2) - 1e-9)))
    step = dt / n
    k = 4 / 3 * math.tan(step / 4)
    out = []
    for i in range(n):
        a, b = t0 + i * step, t0 + (i + 1) * step
        p0 = (cx + rx * math.cos(a), cy + ry * math.sin(a))
        p3 = (cx + rx * math.cos(b), cy + ry * math.sin(b))
        c1 = (p0[0] - k * rx * math.sin(a), p0[1] + k * ry * math.cos(a))
        c2 = (p3[0] + k * rx * math.sin(b), p3[1] - k * ry * math.cos(b))
        out.append((c1[0], c1[1], c2[0], c2[1], p3[0], p3[1]))
    out[-1] = out[-1][:4] + (x1, y1)
    return out


def without_arcs(d):
    """Rewrite absolute A commands as C so every consumer (flat.py, Pixelmator) reads the path."""
    if 'A' not in d:
        return d
    tokens = re.findall(r'[MLHVCQAZ]|-?[0-9.]+(?:e-?[0-9]+)?', d)
    out, i, cur, start, cmd = [], 0, (0.0, 0.0), (0.0, 0.0), None
    counts = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6, 'Q': 4, 'A': 7, 'Z': 0}
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd == 'Z':
                out.append('Z')
                cur = start
                continue
        args = [float(t) for t in tokens[i:i + counts[cmd]]]
        i += counts[cmd]
        if cmd == 'A':
            for seg in arc_to_cubics(cur[0], cur[1], args[0], args[1], int(args[3]), int(args[4]), args[5], args[6]):
                out.append('C' + ' '.join(f(v) for v in seg))
            cur = (args[5], args[6])
            continue
        out.append(cmd + ' '.join(f(v) for v in args))
        if cmd == 'H':
            cur = (args[0], cur[1])
        elif cmd == 'V':
            cur = (cur[0], args[0])
        else:
            cur = (args[-2], args[-1])
        if cmd == 'M':
            start = cur
            cmd = 'L'
    return ' '.join(out)


class Svg:
    def __init__(self):
        self.parts = []
        self.grads = {}
        self.ids = {}

    def open(self, name):
        self.parts.append('<g id="%s">' % self.unique(name))

    def close(self):
        self.parts.append('</g>')

    def unique(self, name):
        n = self.ids.get(name, 0) + 1
        self.ids[name] = n
        return name if n == 1 else '%s %d' % (name, n)

    def paint(self, fill):
        if isinstance(fill, tuple):
            key = fill
            if key not in self.grads:
                self.grads[key] = 'g%d' % (len(self.grads) + 1)
            return 'url(#%s)' % self.grads[key]
        return fill

    def path(self, d, fill, line=None, width=0, name=None, extra=''):
        ident = ' id="%s"' % self.unique(name) if name else ''
        stroke = (' stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"'
                  % (line, f(width))) if line and width else ''
        self.parts.append('<path%s d="%s" fill="%s"%s%s/>' % (ident, without_arcs(d), self.paint(fill), stroke, extra))

    def stroke(self, d, colour, width, name=None):
        ident = ' id="%s"' % self.unique(name) if name else ''
        self.parts.append('<path%s d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round"/>'
                          % (ident, without_arcs(d), colour, f(width)))

    def template(self, template, draw):
        """draw(svg) draws the template standing on (0, 0), in a group the scene reads as the template."""
        self.parts.append('<g id="%s" data-template="%s">' % (template, template))
        draw(self)
        self.close()

    def place(self, name, template, foot, scale, draw):
        """draw(svg) draws the template standing on (0, 0); this stands it on foot scaled by (sx, sy), in a
        group the scene reads as one placement of the template."""
        (x, y), (sx, sy) = foot, scale
        self.parts.append('<g id="%s" data-template="%s" data-at="%s,%s" data-scale="%s,%s" '
                          'transform="translate(%s,%s) scale(%s,%s)">'
                          % (self.unique(name), template, f(x), f(y), fs(sx), fs(sy), f(x), f(y), fs(sx), fs(sy)))
        draw(self)
        self.close()

    def write(self, path):
        defs = []
        for key, gid in self.grads.items():
            if len(key) == 2:
                a, b = key
                attrs = 'x1="0" y1="0" x2="0" y2="1"'
            else:
                a, b, y1, y2 = key
                attrs = 'gradientUnits="userSpaceOnUse" x1="0" y1="%s" x2="0" y2="%s"' % (f(y1), f(y2))
            defs.append('<linearGradient id="%s" %s><stop offset="0" stop-color="%s"/>'
                        '<stop offset="1" stop-color="%s"/></linearGradient>' % (gid, attrs, a, b))
        with open(path, 'w') as fh:
            fh.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n'
                     % (WIDTH, HEIGHT, WIDTH, HEIGHT))
            fh.write('<defs>\n%s\n</defs>\n' % '\n'.join(defs))
            fh.write('\n'.join(self.parts))
            fh.write('\n</svg>\n')


def curve_y(points, x):
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            t = (1 - math.cos(math.pi * t)) / 2
            return y0 + (y1 - y0) * t
    return points[-1][1]


def line_y(line, x):
    return line if isinstance(line, (int, float)) else curve_y(line, x)


def land_colours(depth):
    depth = max(LAND_STOPS[0][0], min(LAND_STOPS[-1][0], depth))
    for a, b in zip(LAND_STOPS, LAND_STOPS[1:]):
        if depth <= b[0]:
            t = (depth - a[0]) / (b[0] - a[0])
            return [mix(p, q, t) for p, q in zip(a[1:], b[1:])]
    return list(LAND_STOPS[-1][1:])


def crown_shapes(x, b, w, h, lean, pointy=False):
    """One tree crown standing on (x, b): a rounded dome, sometimes softly peaked. Returns path
    fragments for the body, its sunlit upper-left cap and its shaded right side."""
    tx, ty = x + lean * w, b - h
    pk = 1.0 if pointy else max(0.0, lean) * 0.6
    snap = 1.0 if w < CROWN_SNAP_BELOW else 0.5      # coarser coordinates for small crowns keep the file small
    g = lambda v: f(round(v / snap) * snap)
    pts = lambda *ps: ' '.join('%s,%s' % (g(px), g(py)) for px, py in ps)
    body = ('M%s C%s %s %s C%s %s %s Z'
            % (pts((x - w / 2, b)), pts((x - w * 0.52, b - h * 0.72)), pts((tx - w * (0.32 - pk * 0.3), ty)), pts((tx, ty)),
               pts((tx + w * (0.32 - pk * 0.3), ty)), pts((x + w * 0.52, b - h * 0.72)), pts((x + w / 2, b))))
    cap = ('M%s C%s %s %s C%s %s %s Z'
           % (pts((x - w * 0.49, b - h * 0.4)), pts((x - w * 0.5, b - h * 0.84)), pts((tx - w * 0.28, ty)),
              pts((tx + w * 0.06, ty + h * 0.02)), pts((tx - w * 0.16, ty + h * 0.24)), pts((x - w * 0.3, b - h * 0.62)),
              pts((x - w * 0.36, b - h * 0.3))))
    side = ('M%s C%s %s %s L%s C%s %s %s Z'
            % (pts((tx + w * 0.12, ty + h * 0.04)), pts((x + w * 0.4, b - h * 0.86)), pts((x + w * 0.5, b - h * 0.6)),
               pts((x + w / 2, b)), pts((x + w * 0.16, b)), pts((x + w * 0.3, b - h * 0.4)),
               pts((x + w * 0.26, b - h * 0.78)), pts((tx + w * 0.12, ty + h * 0.04))))
    return body, cap, side


def slope_light(phase, x, y):
    """Large-scale light across a hill, -1 (shaded hollow) .. 1 (sunlit slope)."""
    return (0.6 * math.sin(x / SLOPE_WAVES[0] + phase + y / 45)
            + 0.4 * math.sin(x / SLOPE_WAVES[1] + phase * 2.3 - y / 30))


def tone(colours, level):
    body, side, cap, gap, slope = colours
    if level > 0:
        return mix(body, slope, SLOPE_LIGHT * level / SLOPE_LEVELS)
    return mix(body, gap, SLOPE_SHADE * -level / SLOPE_LEVELS)


def ridge_haze(svg, top, depth, phase=0.0):
    """Light haze along the foot of the ridge behind, just above this mass's crown line. Its height
    swells and thins along the ridge so it never reads as a ruled stripe."""
    x0, x1 = top[0][0], top[-1][0]
    xs = [x0 + (x1 - x0) * i / 80 for i in range(81)]
    colour = mix(land_colours(max(0.0, depth - 0.25))[0], HAZE, RIDGE_HAZE_TINT)
    svg.open('ridge haze')
    for h, alpha in RIDGE_HAZE:
        swell = [max(0.0, 0.55 + 0.45 * math.sin(x / HAZE_WAVES[0] + phase) + 0.35 * math.sin(x / HAZE_WAVES[1] + 2 * phase))
                 for x in xs]
        d = 'M' + ' L'.join('%s,%s' % (f(x), f(line_y(top, x) - h * sw)) for x, sw in zip(xs, swell))
        d += ' L' + ' L'.join('%s,%s' % (f(x), f(line_y(top, x) + 6 * min(1.0, sw))) for x, sw in zip(xs[::-1], swell[::-1])) + ' Z'
        svg.path(d, colour, name='haze', extra=' fill-opacity="%s"' % alpha)
    svg.close()


def crown_field(svg, rng, top, bottom, depth, r, name, free_standing=False, crown_w=None, haze=False, rows=None,
                style=None):
    """A wooded mass as a canopy of small crowns in rows stepping down from its top line (the
    ridge is made of crown tips) to its bottom line. Colour comes from depth, lit slopes and
    shaded hollows from a slow light field; no outlines. rows limits the crown rows to the ridge line:
    below them a distant ridge is a plain body-coloured slope that darkens toward its foot."""
    x0, x1 = top[0][0], top[-1][0]
    w_mid = r * 2.2 if free_standing else CROWN_WIDTH[0] + (CROWN_WIDTH[1] - CROWN_WIDTH[0]) * min(1, depth)
    w_mid = crown_w or w_mid
    h_mid = w_mid * sum(CROWN_HEIGHT) / 2
    step = h_mid * ROW_STEP
    tier = HILL_TIERS.get(TIER_OF.get(name))
    gap_c = tier[3] if tier else land_colours(depth)[3]
    phase = rng.uniform(0, 2 * math.pi)
    frng = random.Random(int(phase * 1e6))     # colour choices keep their own stream so placement is unchanged
    # distant woods break out of tidy rows: crests wander, clumps and gaps, crowns at varied heights
    loose = max(0.0, 1 - depth / LOOSE_UNTIL)

    def wander(xx, row):
        return loose * h_mid * ROW_WANDER * (math.sin(xx / (w_mid * 3.1) + phase + row * 1.7)
                                             + 0.6 * math.sin(xx / (w_mid * 1.3) + phase * 2 + row * 2.9))
    svg.open(name)
    if haze:
        ridge_haze(svg, top, depth, phase)
    xs = [x0 + (x1 - x0) * i / 60 for i in range(61)]
    def end_taper(x):
        return min(1.0, (x - x0) / (w_mid * 1.5), (x1 - x) / (w_mid * 1.5))
    under_top = [line_y(bottom, x) - (line_y(bottom, x) - min(line_y(bottom, x), line_y(top, x) + h_mid * 0.7))
                 * end_taper(x) for x in xs]
    if rows:
        d = 'M' + ' L'.join('%s,%s' % (f(x), f(line_y(top, x) + h_mid * 0.6)) for x in xs)
        d += ' L' + ' L'.join('%s,%s' % (f(x), f(line_y(bottom, x))) for x in reversed(xs)) + ' Z'
        svg.path(d, (gap_c, mix(gap_c, tier[2] if tier else land_colours(depth)[1], FAR_SLOPE_DARKEN)), name='ridge slope')
    elif not free_standing:
        d = 'M' + ' L'.join('%s,%s' % (f(x), f(y)) for x, y in zip(xs, under_top))
        d += ' L' + ' L'.join('%s,%s' % (f(x), f(line_y(bottom, x) + 1 - 2 * (1 - end_taper(x))
                                                    + 1.5 * math.sin(x * 0.13 + phase)))
                              for x in reversed(xs)) + ' Z'
        svg.path(d, mix(gap_c, tier[0] if tier else land_colours(depth)[0], loose * LOOSE_SHADOW[0]), name='canopy shade')
    else:
        # a solid mound under the crowns so no water shows through between them
        mound = [min(line_y(bottom, x), line_y(top, x) + h_mid * 0.75) for x in xs]
        d = 'M' + ' L'.join('%s,%s' % (f(x), f(y)) for x, y in zip(xs, mound))
        d += ' L%s,%s L%s,%s Z' % (f(x1), f(line_y(bottom, x1)), f(x0), f(line_y(bottom, x0)))
        svg.path(d, land_colours(depth)[1], name='mound')
    k = 0
    while True:
        crowns = []
        room = False
        x = x0 + rng.uniform(-0.3, 0.3) * w_mid
        while x < x1 + w_mid * 0.3:
            # slow swell so stands of bigger and smaller trees alternate along the slope
            swell = 1 + CROWN_SWELL * math.sin(x / (w_mid * 5.3) + k * 0.7) * math.sin(x / (w_mid * 2.1) + 1.3)
            w = w_mid * swell * rng.uniform(0.7, 1.35)
            h = w * rng.uniform(*CROWN_HEIGHT)
            pointy = rng.random() < CROWN_POINTY + loose * LOOSE_TALL
            if pointy:
                w *= 0.75
                h = w * rng.uniform(1.3, 1.7)
            elif depth >= 0.3 and k >= 2 and rng.random() < CROWN_BIG:
                w = min(w * 1.7, w_mid * CROWN_BIG_MAX)
                h = w * rng.uniform(*CROWN_HEIGHT)
            cx = max(x0, min(x1, x))
            jitter = CROWN_JITTER + loose * LOOSE_JITTER
            base = (line_y(top, cx) + h_mid + k * step + wander(cx, k)
                    + rng.uniform(-jitter, jitter) * h_mid)
            if k and loose and rng.random() < loose * LOOSE_CLIMB:
                base -= step * rng.uniform(0.6, 1.3)     # rises into the row behind
            if h > h_mid * 1.3:
                base += min(h - h_mid, step)    # tall and big crowns stand a row lower and overlap it
            if free_standing:
                # a dome: crowns near the ends start lower
                u = (x - x0) / max(1, x1 - x0)
                base += (1 - math.sin(math.pi * max(0.0, min(1.0, u)))) * h_mid * 0.4
                inside = x0 + w * 0.3 <= x <= x1 - w * 0.3
            else:
                inside = True
            if loose and rng.random() < loose * (style or {}).get('gaps', LOOSE_GAPS):
                inside = False
            room = room or base <= line_y(bottom, cx) + 0.5
            if rows and k >= rows:
                # below a distant ridge's crest the woods thin out into scattered clumps
                clump = (0.5 + 0.5 * math.sin(x / (w_mid * 2.3) + phase * 3)
                         * math.sin(base / (h_mid * 1.7) + x / (w_mid * 4.1) + phase))
                inside = inside and clump > min(0.92, CLUMP_THIN[0] + CLUMP_THIN[1] * (k - rows))
            if inside and base <= line_y(bottom, cx) + 0.5:
                light = slope_light(phase, x, base) + rng.uniform(-0.45, 0.45)
                level = max(-SLOPE_LEVELS, min(SLOPE_LEVELS, int(round(light * SLOPE_LEVELS))))
                crowns.append((x, base, w, h, level, pointy))
            spacing = (CROWN_SPACING[0] - loose * 0.15, CROWN_SPACING[1] + loose * 0.3) if loose else CROWN_SPACING
            spacing = (style or {}).get('spacing', spacing)
            x += w * rng.uniform(*spacing)
        if not room or not (crowns or rows):
            break
        if not crowns:
            k += 1
            continue
        svg.open('crown row %d' % (k + 1))
        # dark underlay for this row: everything between its crowns' shoulders and their bases
        lo = min(c[0] - c[2] / 2 for c in crowns)
        hi = max(c[0] + c[2] / 2 for c in crowns)
        rx = [lo + (hi - lo) * i / 30 for i in range(31)]
        def row_base(xx):
            return min(line_y(bottom, max(x0, min(x1, xx))), line_y(top, max(x0, min(x1, xx))) + h_mid + k * step
                       + wander(max(x0, min(x1, xx)), k))
        if loose and not free_standing:
            # far woods: a soft shadow under each crown, of varying depth, instead of one dark band per row
            pools = {}
            for c in crowns:
                t = round(rng.uniform(*LOOSE_SHADOW) * loose * 4) / 4
                pools.setdefault(t, []).append(
                    'M%s,%s H%s V%s H%s Z' % (f(c[0] - c[2] * 0.45), f(c[1] - c[3] * 0.45), f(c[0] + c[2] * 0.45),
                                              f(c[1] + h_mid * 0.1), f(c[0] - c[2] * 0.45)))
            for t in sorted(pools):
                svg.path(' '.join(pools[t]), mix(gap_c, tier[0] if tier else land_colours(depth)[0], t), name='gaps')
        else:
            if free_standing:
                d = ' '.join('M%s,%s H%s V%s H%s Z' % (f(c[0] - c[2] * 0.42), f(c[1] - c[3] * 0.5),
                                                        f(c[0] + c[2] * 0.42), f(c[1]), f(c[0] - c[2] * 0.42))
                             for c in crowns)
            else:
                d = 'M' + ' L'.join('%s,%s' % (f(xx), f(row_base(xx) - h_mid * 0.5)) for xx in rx)
                d += ' L' + ' L'.join('%s,%s' % (f(xx), f(row_base(xx) + h_mid * 0.15)) for xx in reversed(rx)) + ' Z'
            svg.path(d, gap_c, name='gaps')
        bodies = {}
        caps, sides = {}, {}
        colours = land_colours(depth + k * 0.012)
        contrast = EDGE_CONTRAST[0] + (EDGE_CONTRAST[1] - EDGE_CONTRAST[0]) * min(1.0, depth / 0.5)
        accent = TIER_ACCENT.get(TIER_OF.get(name))
        for x, base, w, h, level, pointy in crowns:
            body, cap, side = crown_shapes(x, base, w, h, rng.uniform(-0.1, 0.18), pointy)
            if tier:
                t_body, t_cap, t_side = tier[:3]
                if accent and frng.random() < accent[0]:
                    t_body = mix(t_body, accent[1], accent[2])
                lit = level / SLOPE_LEVELS * (TIER_LIGHT[0] if level > 0 else TIER_LIGHT[1]) + frng.uniform(-TIER_JITTER, TIER_JITTER)
                lit = round(lit * 20) / 20     # a handful of tone steps keeps the file small
                fill = mix(t_body, t_cap, lit) if lit > 0 else mix(t_body, t_side, -lit)
                side_fill = mix(t_side, tier[3], TIER_SIDE_GROUND)
                cap_fill = mix(t_cap, fill, (1 - contrast) * 0.4)
            else:
                fill = tone(colours, level)
                side_fill = mix(colours[0], colours[1], contrast)
                cap_fill = mix(colours[0], colours[2], contrast)
            bodies.setdefault(fill, []).append(body)
            if not (loose and rng.random() < loose * LOOSE_NO_EDGE):
                caps.setdefault(cap_fill, []).append(cap)
            if not (loose and rng.random() < loose * LOOSE_NO_EDGE) and w >= SIDE_MIN_WIDTH:
                sides.setdefault(side_fill, []).append(side)
        for fill in sorted(bodies):
            svg.path(' '.join(bodies[fill]), fill, name='crowns')
        for fill in sorted(sides):
            svg.path(' '.join(sides[fill]), fill, name='shaded sides')
        for fill in sorted(caps):
            svg.path(' '.join(caps[fill]), fill, name='sunlit caps')
        svg.close()
        k += 1
    svg.close()


def blossom(x, y, r):
    """Five round petals around a centre, as circle subpaths: petals, their shaded lower-right, centre."""
    def circ(cx, cy, cr):
        return 'M%s,%s A%s,%s 0 1 0 %s,%s A%s,%s 0 1 0 %s,%s Z' % (f(cx - cr), f(cy), f(cr), f(cr), f(cx + cr), f(cy),
                                                                  f(cr), f(cr), f(cx - cr), f(cy))
    ring = [(x + r * 0.6 * math.cos(a), y + r * 0.6 * math.sin(a)) for a in
            (math.radians(-90 + 72 * k + r * 13) for k in range(5))]
    pr = r * 0.5
    shade = ' '.join(circ(px + pr * 0.22, py + pr * 0.28, pr) for px, py in ring)
    petals = ' '.join(circ(px, py, pr) for px, py in ring)
    return shade, petals, circ(x - r * 0.04, y - r * 0.04, r * 0.27)


def inside_foliage(outline, x, y, r):
    """True when a blossom of radius r at (x, y) sits inside the leaf mass under the outline,
    clear of its edge."""
    x0, x1 = outline[0][0], outline[-1][0]
    if not x0 + r * BLOSSOM_MARGIN <= x <= x1 - r * BLOSSOM_MARGIN:
        return False
    edge = max(curve_y(outline, max(x0, min(x1, x + dx))) for dx in (-r, 0, r))
    return y - r * BLOSSOM_MARGIN >= edge

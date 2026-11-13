#   Writes SVG, run by `python3 -m scene_export render`: scenery/clouds.svg, the clouds.
#
#   python3 -m scenery.clouds  ->  clouds.svg

import math
import os
import random

from common.painting import SEED, Svg, f, mix
from scene_export import cutting, wind
from scenery import sky

HERE = os.path.dirname(os.path.abspath(__file__))


CLOUD_LINE = '#c3a3be'          # the outline round the cloud, and its contour lines and curl


CLOUD_TOP = '#ffffff'           # the lit middle of the cloud


CLOUD_SHADE = '#dcc2e4'         # the underside, and the crevice under a puff where it tucks behind the next


CLOUD_UNDERSIDE = 0.3           # an underside puff is white down to this share of its height, then shades to its bottom


CLOUD_CRESCENT = 0.4            # how far the shade in the crease under a top puff reaches up, share of its height


CLOUD_SQUASH = (1.0, 1.2)       # a top puff is this many times wider than tall, flattened about its middle


CLOUD_BACK_TINT = 0.35          # how much of the shade the puffs furthest back are tinted with, fading to none at the front


CLOUD_LINE_WIDTH = (0.009, 1.0, 3.6)   # outline width: share of the cloud's width, clamped to (min, max) px


CLOUD_BOTTOM_PUFF = (0.35, 0.8) # the flattened puffs along a cloud's underside: height, as a share of the top puff above


CLOUD_BOTTOM_FLAT = 2.0         # how many times wider than tall those puffs are, so the underside waves in long shallow scallops


CLOUD_SAG = (-0.1, 0.45)        # how far the middle of a cloud's underside hangs below its ends, share of the mean radius


CLOUD_NUB = (0.4, 0.45, 0.6)    # chance a top puff has a swell on its upper side, and the swell's radius range (share)


CLOUD_CONTOUR = (0.9, 0.3, 0.55)   # chance a front puff draws its contour line, and how much of the line it draws (range)


CLOUD_SIZE = 0.9                # a cloud is drawn this size of its layout below, shrunk toward the middle of its base


CLOUD_CURL_LOBES = 5            # a cloud with this many top puffs or more has a curl, on its biggest puff that can take one


CLOUD_CURL = (0.4, 30, 270, 0.3)   # a curl's spiral: radius (share of its puff's), degrees it runs along the puff's
                                   # edge first, degrees it winds, and what share of its radius it tightens to


CLOUD_DEPTH = (45, 312)         # canvas y of a cloud's base nearest, high in the sky, and furthest back, by the horizon
CLOUD_FAR = (0.8, 0.7)          # a cloud furthest back is drawn this share of its size, with this share of the sky's
                                # colour behind it mixed into its colours; nearer clouds have less of both
CLOUD_RECEDE = 1.6              # above 1 keeps clouds near size and colour until low in the sky, then shrinks and hazes
                                # them fast toward the horizon


CLOUD_PLACES = 'cloud places'   # the seed the clouds are scattered across the sky with
CLOUD_BANDS = [((45, 95), 4, 0.45), ((168, 194), 6, 0.3), ((266, 316), 8, 0.3)]
                                # nearest first, each depth's (canvas y range of a cloud's base, how many clouds, how
                                # far each may stray off its even place round their lap, as a share of the spacing); the
                                # mid clouds stay clear above the snow peak, and the far ones tuck behind the ridges
CLOUD_GAP = 0.5                 # the least gap between clouds at one depth, all the way round their lap, as a share of
                                # the narrower one's width; clouds at different depths pass in front of each other


# A random cloud's layout, from the clouds voted up: a few puffs, one clearly on top but not a lone ball.
CLOUD_PUFFS = (3, 7)            # how many top puffs, the fewest and most; the bigger the cloud the more it has
CLOUD_PUFF_SIZE = (14, 50)      # the biggest puff's radius
CLOUD_LEAD = (1.1, 1.45)        # how many times the next biggest puff's radius the biggest one's is
CLOUD_LEAD_AT_END = 0.12        # chance the biggest puff is an end one; there it stands like a cliff over the rest
CLOUD_SPREAD = (0.2, 0.7)       # how far the puffs either side of the biggest stay big, share of the puff count:
                                # low makes a tower, high a long bank
CLOUD_TAIL = (0.1, 1.2)         # how far each tail tip reaches past the end puff, share of the biggest radius


# Each cloud: its top puffs (cx, cy, r), above a row of flattened puffs along the line from the left tail tip
# to the right tail tip; a tail of shrinking puffs reaches each tip that lies past them, starting the given
# thickness.
CLOUDS = [
    ('cloud left edge', [(-6, 68, 18), (18, 58, 18), (36, 70, 13), (50, 80, 10)], (-30, 82), (84, 90), 8),
    ('cloud centre right', [(632, 136, 26), (676, 128, 30), (742, 116, 40), (826, 102, 52), (900, 128, 28),
                            (930, 145, 14)], (585, 145), (952, 158), 10),
    ('cloud mid', [(628, 226, 15), (662, 218, 22), (690, 216, 26), (724, 228, 14)], (570, 236), (752, 238), 6),
    ('cloud behind lamp', [(160, 272, 22), (212, 258, 37), (262, 278, 26), (296, 292, 16)], (120, 300),
     (330, 304), 8),
    ('cloud right small', [(812, 254, 12), (838, 249, 14), (862, 255, 9)], (782, 262), (900, 262), 4),
    ('cloud right', [(1112, 288, 18), (1140, 280, 26), (1172, 290, 18)], (1088, 300), (1212, 300), 6),
]


# The clouds voted up in round 4 of the vote page: (name, the seed of its random layout and of its drawing). They and
# the clouds above are scattered across the sky by places().
ROUND_4 = [
    ('cloud r4-26', 4025), ('cloud r4-20', 4019), ('cloud r4-24', 4023), ('cloud r4-23', 4022), ('cloud r4-25', 4024),
    ('cloud r4-08', 4007), ('cloud r4-09', 4008), ('cloud r4-34', 4033), ('cloud r4-06', 4005), ('cloud r4-27', 4026),
    ('cloud r4-33', 4032), ('cloud r4-14', 4013),
]


# Thin flat wisps for the day valley's sky, drawn where it shows them: a few low puffs at one end and a tail tapering
# along a slant to the other, laid out like CLOUDS, then the canvas y whose depth they are hazed as, so the high ones
# are as pale and blue as clouds far off.
WISPS = [
    ('cloud wisp left', [(310, 92, 9), (330, 86, 13), (352, 85, 11), (374, 94, 7)], (288, 96), (472, 124), 6, 270),
    ('cloud wisp right', [(1316, 96, 7), (1338, 88, 11), (1360, 86, 13), (1380, 93, 9)], (1214, 123), (1394, 96), 6,
     270),
    ('cloud wisp low', [(-6, 170, 14), (18, 162, 18), (42, 174, 11)], (-24, 178), (110, 198), 6, 60),
]


def ellipse(cx, cy, rx, ry):
    return 'M%s,%s A%s,%s 0 1 1 %s,%s A%s,%s 0 1 1 %s,%s Z' % (
        f(cx - rx), f(cy), f(rx), f(ry), f(cx + rx), f(cy), f(rx), f(ry), f(cx - rx), f(cy))


def inside(x, y, puff, margin=0.97):
    cx, cy, rx, ry = puff
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < margin


def crescent(puff, depth):
    """The bottom of the puff down to depth of its height above its lowest point, tapering to points at its sides."""
    cx, cy, rx, ry = puff
    a0, a1 = math.radians(12), math.radians(168)
    x0, y0 = cx + rx * math.cos(a0), cy + ry * math.sin(a0)
    x1, y1 = cx + rx * math.cos(a1), cy + ry * math.sin(a1)
    inner = ry * (1 - depth)
    return 'M%s,%s A%s,%s 0 0 1 %s,%s A%s,%s 0 0 0 %s,%s Z' % (
        f(x0), f(y0), f(rx), f(ry), f(x1), f(y1), f(rx), f(inner), f(x0), f(y0))


def tapered(points, width, hold=0):
    """A filled stroke along points, width wide for the first hold points then narrowing to nothing at the
    last, with a round start."""
    left, right = [], []
    n = len(points) - 1
    for i, (x, y) in enumerate(points):
        (x0, y0), (x1, y1) = points[max(0, i - 1)], points[min(n, i + 1)]
        ln = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / ln, (x1 - x0) / ln
        w = width / 2 * (1 - max(0, i - hold) / (n - hold)) ** 0.8
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    ring = left + right[::-1]
    return 'M' + ' L'.join('%s,%s' % (f(x), f(y)) for x, y in ring) + ' A%s,%s 0 0 1 %s,%s Z' % (
        f(width / 2), f(width / 2), f(left[0][0]), f(left[0][1]))


def edge_points(puff, a0, a1, step=1.2):
    cx, cy, rx, ry = puff
    n = max(2, int(math.radians(a1 - a0) * max(rx, ry) / step))
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def contour(puff, behind, after, others, share):
    """The front puff's own edge carried into the cloud where it lies over a puff behind it: from just inside
    the outline, share of the way along, as a list of points; None where it never meets the outline."""
    pts = edge_points(puff, 160, 380)
    over = [any(inside(x, y, b, 1.0) for b in behind) and not any(inside(x, y, a) for a in after) for x, y in pts]
    on_outline = [not any(inside(x, y, o) for o in others) for x, y in pts]
    runs, i = [], 0
    while i < len(pts):
        if over[i]:
            j = i
            while j + 1 < len(pts) and over[j + 1]:
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1
    best = None
    for i, j in runs:
        if i > 0 and on_outline[i - 1]:
            run = pts[i - 1:j + 1]
        elif j + 1 < len(pts) and on_outline[j + 1]:
            run = pts[i:j + 2][::-1]
        else:
            continue
        if best is None or len(run) > len(best):
            best = run
    if best is None or len(best) < 4:
        return None
    spur = best[:max(3, int(len(best) * share))]
    (x0, y0), cx, cy = spur[0], puff[0], puff[1]
    ln = math.hypot(x0 - cx, y0 - cy)
    return [(x0 + (x0 - cx) / ln, y0 + (y0 - cy) / ln)] + spur


def curl(top, behind, row, outset):
    """(index of the top puff, points, how many of them run along its edge) of a curl, or None: the puff's
    outline carried on from the notch where it meets the outline of a puff behind it, along its own edge over
    that puff, then curling in on itself in a tightening spiral. Only on a puff nothing drawn after it covers,
    so the curl is in front and the outline behind ends cleanly against it. outset moves it out from the edge."""
    best = None
    for i, p in enumerate(top):
        cx, cy, rx, ry = p
        back, after = behind + top[:i], top[i + 1:] + row
        grown = [(ax, ay, arx + outset * 2, ary + outset * 2) for ax, ay, arx, ary in after]
        others = back + after
        rc = min(rx, ry) * CLOUD_CURL[0]
        follow = CLOUD_CURL[1]
        for d in (1, -1):
            angles = list(range(150, 391)) if d == 1 else list(range(390, 149, -1))
            pts = [(cx + (rx + outset) * math.cos(math.radians(a)), cy + (ry + outset) * math.sin(math.radians(a)))
                   for a in angles]
            edge = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in angles]
            for k in range(3, len(pts) - follow - 1):
                x, y = edge[k]
                if any(inside(x, y, o, 1.0) for o in others) or not any(inside(*edge[k + 1], b, 1.0) for b in back):
                    continue
                run = pts[k - 3:k + 1 + follow]
                (x0, y0), (x1, y1) = run[-2], run[-1]
                ln = math.hypot(x1 - x0, y1 - y0)
                ox, oy = x1 + d * -(y1 - y0) / ln * rc, y1 + d * (x1 - x0) / ln * rc
                phi = math.atan2(y1 - oy, x1 - ox)
                sweep = math.radians(CLOUD_CURL[2])
                n = max(8, int(sweep * rc / 1.2))
                spiral = []
                for j in range(1, n + 1):
                    t = j / n
                    rho = rc * (1 - (1 - CLOUD_CURL[3]) * t)
                    spiral.append((ox + rho * math.cos(phi + d * sweep * t), oy + rho * math.sin(phi + d * sweep * t)))
                path = run + spiral
                if all(inside(x, y, p, 1.02 + outset * 4 / min(rx, ry)) and not any(inside(x, y, a, 1.0) for a in grown)
                       for x, y in path) and all(any(inside(x, y, b, 1.0) for b in back)
                                                 for x, y in edge[k + 1:k + 1 + follow]):
                    if best is None or rx > top[best[0]][2]:
                        best = (i, path, len(run))
                    break
    return best


def nubs(lobes, rng):
    """Smaller puffs swelling out of the upper side of some top puffs, so the top is lumpy with sharp notches."""
    out = []
    chance, lo, hi = CLOUD_NUB
    for cx, cy, r in lobes:
        if rng.random() < chance:
            a = math.radians(rng.uniform(215, 325))
            rn = r * rng.uniform(lo, hi)
            out.append((cx + r * 0.6 * math.cos(a), cy + r * 0.6 * math.sin(a), rn))
    return out


def bottom_puffs(lobes, base, rng):
    """A row of overlapping flattened puffs under the top puffs, each sized to the top puff above it and
    hanging lower toward the middle by a sag of the cloud's own, so the underside waves and is not always level."""
    r_mean = sum(r for _, _, r in lobes) / len(lobes)
    xa = min(cx - r * 0.6 for cx, _, r in lobes)
    xb = max(cx + r * 0.6 for cx, _, r in lobes)
    sag = rng.uniform(*CLOUD_SAG) * r_mean
    out = []
    x = xa
    while True:
        r_above = min(lobes, key=lambda p: abs(p[0] - x))[2]
        ry = min(r_above, r_mean) * rng.uniform(*CLOUD_BOTTOM_PUFF)
        rx = ry * CLOUD_BOTTOM_FLAT * rng.uniform(0.8, 1.2)
        t = (x - xa) / (xb - xa)
        out.append((x, base(x) - ry * 0.6 + sag * math.sin(math.pi * min(1.0, t)) + rng.uniform(-0.35, 0.35) * ry,
                    rx, ry))
        if x >= xb:
            return out
        x = min(xb, x + rx * rng.uniform(1.0, 1.3))


def fillers(lobes, row):
    """Puffs hidden inside the cloud joining each top puff down to the row under it, so no sky shows through."""
    out = []
    for cx, cy, r in lobes:
        _, uy, _, ury = min(row, key=lambda p: abs(p[0] - cx))
        rf = r * 0.85
        end = uy + ury * 0.6 - rf
        y = cy
        while y < end:
            y = min(end, y + rf * 0.5)
            out.append((cx, y, rf, rf))
    return out


def tail(start, tip, thick):
    """Flattened puffs from start to a blunt rounded tip, thinning a little on the way."""
    (x0, y0), (x1, y1) = start, tip
    length = math.hypot(x1 - x0, y1 - y0)
    out, s = [], 0.0
    while s < length:
        t = s / length
        r = thick * (1 - 0.3 * t)
        out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r * 1.4, r))
        s += r * 0.5
    return out


def build(lobes, left, right, thick, rng):
    """(fillers, top puffs back to front, the underside row, tail puffs) of one cloud, each (cx, cy, rx, ry)."""
    (xl, yl), (xr, yr) = left, right

    def base(x):
        return yl + (yr - yl) * (x - xl) / (xr - xl)

    row = bottom_puffs(lobes, base, rng)
    tails = []
    first, last = row[0], row[-1]
    if xl < first[0] - first[2]:
        tails += tail((first[0], first[1] + first[3] * 0.3), (xl, yl - thick * 0.3), thick)
    if xr > last[0] + last[2]:
        tails += tail((last[0], last[1] + last[3] * 0.3), (xr, yr - thick * 0.3), thick)
    top = sorted(lobes + nubs(lobes, rng), key=lambda p: p[1] - p[2] * 0.3)
    return fillers(lobes, row), [(cx, cy, r, r / rng.uniform(*CLOUD_SQUASH)) for cx, cy, r in top], row, tails


def random_layout(rng):
    lo, hi = CLOUD_PUFFS
    rmax = rng.uniform(*CLOUD_PUFF_SIZE)
    grown = (rmax - CLOUD_PUFF_SIZE[0]) / (CLOUD_PUFF_SIZE[1] - CLOUD_PUFF_SIZE[0])
    n = min(hi, max(lo, round(lo + grown * (hi - lo)) + rng.randint(-1, 1)))
    top = rng.choice((0, n - 1)) if rng.random() < CLOUD_LEAD_AT_END else rng.randrange(1, n - 1)
    spread = rng.uniform(*CLOUD_SPREAD) * n
    radii = [math.exp(-((i - top) / spread) ** 2) * rng.uniform(0.85, 1.15) for i in range(n)]
    others = max(r for i, r in enumerate(radii) if i != top)
    second = rmax / rng.uniform(*CLOUD_LEAD)
    radii = [rmax if i == top else max(0.35, r / others) * second for i, r in enumerate(radii)]
    xs = [0.0]
    for a, b in zip(radii, radii[1:]):
        xs.append(xs[-1] + (a + b) * rng.uniform(0.45, 0.9))
    base, tilt, span = 200.0, rng.uniform(-0.4, 0.4) * rmax, xs[-1] or 1.0
    lobes = [(x, base + tilt * x / span - r * (0.2 + 1.2 * r / rmax) + rng.uniform(-0.25, 0.25) * r, r)
             for x, r in zip(xs, radii)]
    left = (xs[0] - radii[0] - rng.uniform(*CLOUD_TAIL) * rmax, base + rng.uniform(-0.15, 0.15) * rmax)
    right = (xs[-1] + radii[-1] + rng.uniform(*CLOUD_TAIL) * rmax, base + tilt + rng.uniform(-0.15, 0.15) * rmax)
    return lobes, left, right, rmax * rng.uniform(0.15, 0.3)


def depth(y):
    """How far back a cloud whose base is at canvas y stands: 0 nearest, 1 by the horizon."""
    return min(1.0, max(0.0, (y - CLOUD_DEPTH[0]) / (CLOUD_DEPTH[1] - CLOUD_DEPTH[0]))) ** CLOUD_RECEDE


def depth_size(y):
    return 1 + (CLOUD_FAR[0] - 1) * depth(y)


def colours(y):
    """(outline, lit, shade) of a cloud whose base is at canvas y, hazed toward the sky behind it."""
    behind, t = sky.colour_at(y), CLOUD_FAR[1] * depth(y)
    return tuple(mix(c, behind, t) for c in (CLOUD_LINE, CLOUD_TOP, CLOUD_SHADE))


def sized(lobes, left, right, thick):
    mx, my = (left[0] + right[0]) / 2, (left[1] + right[1]) / 2
    k = CLOUD_SIZE * depth_size(my)

    def at(x, y):
        return mx + (x - mx) * k, my + (y - my) * k
    return ([at(cx, cy) + (r * k,) for cx, cy, r in lobes], at(*left), at(*right), thick * k)


def placed(lobes, left, right, thick, at):
    """The layout moved so the middle of its base is at (x, y)."""
    dx, dy = at[0] - (left[0] + right[0]) / 2, at[1] - (left[1] + right[1]) / 2
    return ([(cx + dx, cy + dy, r) for cx, cy, r in lobes], (left[0] + dx, left[1] + dy),
            (right[0] + dx, right[1] + dy), thick)


def outline_width(shapes):
    width = max(cx + rx for cx, _, rx, _ in shapes) - min(cx - rx for cx, _, rx, _ in shapes)
    return max(CLOUD_LINE_WIDTH[1], min(CLOUD_LINE_WIDTH[2], CLOUD_LINE_WIDTH[0] * width))


def reach(lobes, left, right, thick, seed):
    """(x0, y0, x1, y1) the image of a laid out cloud drawn with seed reaches, a few pixels over at most."""
    shapes = [p for part in build(*sized(lobes, left, right, thick), random.Random(seed)) for p in part]
    line = outline_width(shapes)
    pad = line + cutting.PAD + 3
    # a curl or a contour can wind out past its puff's top or bottom by up to an outline's width
    return (min(cx - rx for cx, _, rx, _ in shapes) - pad, min(cy - ry for _, cy, _, ry in shapes) - pad - line,
            max(cx + rx for cx, _, rx, _ in shapes) + pad, max(cy + ry for _, cy, _, ry in shapes) + pad + line)


def laid_out():
    """[(name, lobes, left, right, thick, the seed it is drawn with)] of every cloud, biggest first."""
    laid = [(name, lobes, left, right, thick, name) for name, lobes, left, right, thick in CLOUDS]
    laid += [(name,) + random_layout(random.Random(seed)) + (seed,) for name, seed in ROUND_4]
    return sorted(laid, key=lambda c: c[3][0] - c[2][0], reverse=True)


def bands():
    """The clouds' names at each depth, nearest first: the bigger a cloud the nearer it stands."""
    names, out = [c[0] for c in laid_out()], []
    assert len(names) == sum(n for _, n, _ in CLOUD_BANDS)
    for _, n, _ in CLOUD_BANDS:
        out.append(names[:n])
        names = names[n:]
    return out


def speed(name):
    """Scene units a second the cloud drifts, the same for every cloud at its depth so they stay spread out."""
    for ((lo, hi), _, _), names in zip(CLOUD_BANDS, bands()):
        if name in names:
            return wind.cloud_speed((lo + hi) / 4)


def places():
    """[(name, lobes, left, right, thick, the seed it is drawn with, the middle of its base)] of every cloud, from the
    horizon up. Each depth's clouds are spread evenly round their lap, half in view and half waiting off the left
    edge for the wind to bring them in, clear of every cloud beside them at that depth."""
    rng = random.Random(CLOUD_PLACES)
    by_name = {c[0]: c for c in laid_out()}
    lap, start, edge = 2 * wind.CLOUD_LAP, 2 * (wind.SCENE_SIZE[0] + wind.OUT_OF_SIGHT - wind.CLOUD_LAP), \
        2 * wind.SCENE_SIZE[0]
    out = []
    for ((lo, hi), n, jitter), names in zip(CLOUD_BANDS, bands()):
        for _ in range(1000):
            order, offset, band = rng.sample(names, n), rng.uniform(0, lap), []
            for k, name in enumerate(order):
                _, lobes, left, right, thick, seed = by_name[name]
                y = rng.uniform(lo, hi)
                x0, y0, x1, y1 = reach(*placed(lobes, left, right, thick, (0, y)), seed)
                xl = start + (offset + (k + rng.uniform(-jitter, jitter)) * lap / n) % lap
                band.append((name, (xl, y0, x1 - x0, y1 - y0), (xl - x0, y)))
            in_view = sum(1 for _, b, _ in band if -b[2] < b[0] < edge)
            waiting = sum(1 for _, b, _ in band if b[0] <= -b[2])
            if in_view == waiting == n // 2 and all(
                    not (a[1] < b[1] + b[3] and b[1] < a[1] + a[3]) or
                    b[2] + CLOUD_GAP * min(a[2], b[2]) <= (a[0] - b[0]) % lap <= lap - a[2] - CLOUD_GAP * min(a[2], b[2])
                    for i, (_, a, _) in enumerate(band) for _, b, _ in band[:i]):
                break
        else:
            raise ValueError('no room in the sky for the clouds ' + ', '.join(names))
        for name, box, at in band:
            out.append(by_name[name] + (at,))
    return sorted(out, key=lambda c: c[-1][1], reverse=True)


def layout_of(name):
    return next(placed(lobes, left, right, thick, at) for n, lobes, left, right, thick, _, at in places() if n == name)


def layouts():
    """[(name, lobes, left, right, thick)] of every cloud in the scene, placed in the sky."""
    return [(name,) + placed(lobes, left, right, thick, at) for name, lobes, left, right, thick, _, at in places()]


def draw_cloud(svg, name, lobes, left, right, thick, rng, haze_y=None):
    """haze_y is the canvas y whose depth the cloud is hazed as, by default its base's."""
    hidden, top, row, tails = build(*sized(lobes, left, right, thick), rng)
    shapes = hidden + top + row + tails
    line = outline_width(shapes)
    ink, lit, shade = colours((left[1] + right[1]) / 2 if haze_y is None else haze_y)
    svg.open(name)
    svg.path(' '.join(ellipse(*p) for p in shapes), ink, ink, line * 2, name='outline')
    svg.path(' '.join(ellipse(*p) for p in shapes), shade, name='shade')
    if hidden:
        svg.path(' '.join(ellipse(*p) for p in hidden), lit, name='inside')
    if tails:
        top_y = min(cy - ry for _, cy, _, ry in tails)
        bottom_y = max(cy + ry for _, cy, _, ry in tails)
        svg.path(' '.join(ellipse(*p) for p in tails), (lit, shade, top_y, bottom_y), name='tail')
    for i, p in enumerate(top):
        cy, ry = p[1], p[3]
        tint = mix(lit, shade, CLOUD_BACK_TINT * (1 - i / len(top)))
        svg.path(ellipse(*p), (tint, lit, cy - ry, cy + ry * 0.2), name='puff')
        svg.path(crescent(p, CLOUD_CRESCENT), (lit, shade, cy + ry * (1 - CLOUD_CRESCENT), cy + ry),
                 name='crease')
    for cx, cy, rx, ry in row:
        svg.path(ellipse(cx, cy, rx, ry), (lit, shade, cy - ry + 2 * ry * CLOUD_UNDERSIDE, cy + ry),
                 name='underside')
    found = curl(top, hidden + tails, row, line / 2) if len(lobes) >= CLOUD_CURL_LOBES else None
    chance, lo, hi = CLOUD_CONTOUR
    for i, p in enumerate(top):
        if i == 0 or rng.random() > chance:
            continue
        share = rng.uniform(lo, hi)
        if found and i == found[0]:
            continue
        pts = contour(p, top[:i], top[i + 1:], [o for o in shapes if o is not p], share)
        if pts:
            svg.path(tapered(pts, line), ink, name='contour')
    if found:
        _, pts, hold = found
        svg.path(tapered(pts, line, hold), ink, name='curl')
    svg.close()


def clouds(svg, rng):
    svg.open('Clouds')
    for name, lobes, left, right, thick, seed, at in places():
        draw_cloud(svg, name, *placed(lobes, left, right, thick, at), random.Random(seed))
    svg.close()


def wisps(svg):
    svg.open('Wisps')
    for name, lobes, left, right, thick, haze_y in WISPS:
        draw_cloud(svg, name, lobes, left, right, thick, random.Random(name), haze_y)
    svg.close()


def main():
    svg = Svg()
    clouds(svg, random.Random(SEED + 1))
    wisps(svg)
    svg.write(cutting.sheet_path('scenery/clouds.svg'))


def cut(group='Clouds'):
    """[(cloud id, its image)] of the group's clouds, each image uncropped, as the wind blows the clouds past the
    canvas edge."""
    root, grads = cutting.load('scenery/clouds.svg')
    return [(c.get('id'), cutting.static_part('scenery/parts/clouds/' + cutting.slug(c.get('id')), [c], grads,
                                              c.get('id'), None))
            for c in cutting.find_group(root, group)]


def cut_all():
    """The terrace's clouds then the day valley's wisps."""
    return cut() + cut('Wisps')


def parts():
    return [part for _, part in cut_all()]


if __name__ == '__main__':
    main()

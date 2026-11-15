#   Writes SVG, run by `python3 -m scene_export render`: scenery/spring_valley.svg, the train meadow's land drawn as
#   the day valley's is (scenery/valley.py): the rolling hills back to front, teal-blue far off to sunlit yellow-green
#   near, with the mixed woods along the far hills' feet, the leafy bushes behind the track and in front of it, the
#   straight level railway the train slides along, and the meadow in front the foreground flowers stand on, each its
#   own image so the mesa, the trees and the train can stand between them.
#
#   python3 -m scenery.spring_valley  ->  spring_valley.svg

import itertools
import math
import os
import random

from common.painting import SEED, WIDTH, Svg, curve_y, f, mix, poly
from scene_export import cutting
from scenery import spring_valley_reference as ref
from scenery.landscape import blades, circle_union, polyline
from scenery.valley import (BODY_SHADING, BOTTOM, CREST_FADE, HILL_OVERLAP, LEFT, RIGHT, Line, fine_blades,
                            light_plane, spline)
from structures.houses import TOWN_LINE_WIDTH

HERE = os.path.dirname(os.path.abspath(__file__))


RAIL_TOP = ref.RAIL_TOP


SLEEPER_WIDTH, SLEEPER_PITCH = ref.SLEEPERS[2], ref.SLEEPERS[3]


SPANS_THE_LAND = ('hills far', 'hills middle', 'track', 'meadow')   # the images reaching past both sides


def rail_top(x):
    """y of the rails' top at x: the track is laid level across the sheet and beyond, so the train keeps one shape."""
    return RAIL_TOP


def edge_of(colour):
    """The outline colour of a shape of this colour: the colour itself darkened, as the terrace's lines are."""
    return mix(colour, '#000000', ref.EDGE_SHADE)


# ================================================================ hills
class Hill:
    """A hill as the day valley's (scenery/valley.py), coloured from this scene's reference."""
    def __init__(self, name, depth, edge):
        self.name, self.depth = name, depth
        self.edge = spline(edge)
        self.partial = edge[0][0] > LEFT or edge[-1][0] < RIGHT
        self.top = Line(edge)
        self.colours = ref.HILL_COLOURS[name]


def hills():
    return [Hill(*h) for h in ref.HILLS]


def bottom_of(all_hills, i):
    """Where hill i's image ends: far enough below the next full-width hill's lowest top to stay hidden under it, or
    past the track for the nearest."""
    front = next((o for o in all_hills[i + 1:] if not o.partial), None)
    lowest = max(y for _, y in front.edge) if front else ref.TRACK_GROUND[0][0][1] + ref.SLEEPERS[1]
    return min(BOTTOM, lowest + HILL_OVERLAP)


def outline(hill, bottom):
    (x0, _), (x1, _) = hill.edge[0], hill.edge[-1]
    return hill.edge + [(min(x1, RIGHT), bottom), (max(x0, LEFT), bottom)]


def draw_hill(svg, all_hills, i):
    """A hill: its body shading from mid tone at the crest to shade at its foot, the sunlit crest cap, and the soft
    lit and shaded planes rolling down its slopes; no line along its top, as the terrace's hills have none."""
    hill = all_hills[i]
    crest, mid, shade = hill.colours
    bottom = bottom_of(all_hills, i)
    svg.open(hill.name)
    y_top = min(y for _, y in hill.edge)
    svg.path(poly(outline(hill, bottom)), (mid, shade, y_top, y_top + BODY_SHADING), name='grass')
    for x0, x1, drop0, drop1, depth, tone in ref.PLANES.get(hill.name, []):
        if tone == 'crest':
            ys = (hill.top(x0) + drop0, hill.top(x1) + drop1)
            fill, name = (crest, mix(crest, mid, CREST_FADE), min(ys), max(ys) + depth), 'lit plane'
        elif tone == 'shade':
            fill, name = mix(mid, shade, ref.HOLLOW_SHADE), 'shade plane'
        else:
            fill, name = mid, 'lit plane'
        svg.path(light_plane(hill, x0, x1, drop0, drop1, depth), fill, name=name)
    svg.close()


# ================================================================ leafy clumps
def leafy(cx, cy, r, rng, scallop=None):
    """The circles a leafy clump is the union of: a round core with a ring of small scallops round its rim, so the
    outline bumps like a mass of leaves rather than a smooth ball."""
    scallop = ref.SCALLOP if scallop is None else scallop
    circles = [(cx, cy, r)]
    n = max(5, int(2 * math.pi * r / (r * scallop * 1.4)))
    phase = rng.uniform(0, 2 * math.pi)
    for k in range(n):
        a = phase + 2 * math.pi * k / n
        rs = r * scallop * rng.uniform(0.7, 1.3)
        d = r - rs * 0.55
        circles.append((cx + d * math.cos(a), cy + d * math.sin(a), rs))
    return circles


def shifted(circles, dx, dy, scale):
    """The circles moved by (dx, dy) radii and scaled, for a lit or body layer inset from a silhouette."""
    return [(cx + r * dx, cy + r * dy, r * scale) for cx, cy, r in circles]


def scaled_about(circles, core, dx, dy, scale):
    """A leafy clump's circles scaled as one shape about its core, moved by (dx, dy) core radii: the clump keeps its
    shape smaller, for a facet of it."""
    cx0, cy0, r0 = core
    ox, oy = cx0 + r0 * dx, cy0 + r0 * dy
    return [(ox + (cx - cx0) * scale, oy + (cy - cy0) * scale, r * scale) for cx, cy, r in circles]


# ================================================================ woods
def dealer(rng, deck):
    """Endless items of deck in shuffled rounds, every item once before any comes again, so a short row of crowns or
    bushes still gets every shape."""
    while True:
        hand = list(deck)
        rng.shuffle(hand)
        yield from hand


def bush_profiles(n, rng, profiles=None):
    """The profiles of n bushes in a row, dealt so each profile comes once before any repeats."""
    return list(itertools.islice(dealer(rng, ref.BUSH_PROFILES if profiles is None else profiles), n))


def taper(cx, base, r, h, rng, share, tiered=False):
    """The circles of a crown rising from a base radius r to a point h above base: a close stack whose radius is
    share(t) of r at t of the way up, every other one fuller when tiered so the sides step like a fir's boughs,
    ending in a tiny circle at the tip, the circle near its middle first as its core."""
    tip = max(0.6, r * ref.TIP_RADIUS)
    step = r * ref.TAPER_STEP
    n = max(3, int((h - r - tip) / step) + 1)
    circles = []
    for k in range(n + 1):
        t = k / n
        y = base - r - (h - r - tip) * t
        bough = (1.12 if k % 2 else 0.9) if tiered else rng.uniform(0.92, 1.08)
        radius = tip if k == n else max(tip, r * share(t) * bough)
        circles.append((cx + rng.uniform(-0.08, 0.08) * r * t, y, radius))
    core = circles.pop(n // 2)
    return [core] + circles


def fir(cx, base, w, h, rng):
    """A pointed fir: a cone, wide at its foot, its sides stepping in bough by bough to its tip."""
    return taper(cx, base, w / 2, h, rng, lambda t: 1 - 0.9 * t, tiered=True)


def poplar(cx, base, w, h, rng):
    """A tall narrow poplar: a flame, full most of the way up, drawing in to its tip."""
    return taper(cx, base, w / 2, h, rng, lambda t: (1 - t) ** 0.4 * (0.8 + 0.2 * math.sin(math.pi * t)))


def lit_cap(circles, core):
    """The circles of a crown's lit cap: the crown's own shape moved to its upper right rim by TREE_LIT_INSET, or
    on a crown taller than it is wide, a fir or poplar, a slimmer copy of its upper part moved to its right side."""
    x0, y0, x1, y1 = (min(cx - r for cx, _, r in circles), min(cy - r for _, cy, r in circles),
                      max(cx + r for cx, _, r in circles), max(cy + r for _, cy, r in circles))
    if y1 - y0 <= 1.3 * (x1 - x0):
        return scaled_about(circles, core, *ref.TREE_LIT_INSET)
    return [(cx + r * 0.35, cy, r * 0.55) for cx, cy, r in circles if cy - r < y0 + (y1 - y0) * ref.TAPER_LIT]


def lumpy(cx, base, w, h, rng):
    """A lumpy broadleaf crown wider than tall: a big ball off centre, a middling one lower on the other side and a
    small one on the outer shoulder, each leafy, the big one first as its core."""
    side = rng.choice((-1, 1))
    big, mid, small = h * 0.5, h * 0.38, h * 0.28
    return (leafy(cx + side * w * 0.18, base - h + big, big, rng, ref.TREE_SCALLOP)
            + leafy(cx - side * w * 0.25, base - mid - h * 0.12, mid, rng, ref.TREE_SCALLOP)
            + leafy(cx + side * w * 0.38, base - small - h * 0.04, small, rng, ref.TREE_SCALLOP))


def flat(cx, base, w, h, rng):
    """A wide flat-topped crown: a level row of small circles along its top over a narrower row at its foot."""
    rt, rb = h * 0.3, h * 0.36
    n = max(3, round(w / (h * 0.55)))
    reach = w / 2 - rt
    top = [(cx - reach + 2 * reach * k / (n - 1), base - h + rt + rng.uniform(-0.3, 0.3), rt) for k in range(n)]
    reach = (w / 2 - rb) * 0.75
    foot = [(cx - reach + 2 * reach * k / (n - 1), base - rb, rb) for k in range(n)]
    return [top[n // 2]] + top[:n // 2] + top[n // 2 + 1:] + foot


def shrub(cx, base, w, h, rng):
    """A low wide shrub: three leafy balls of uneven size side by side on the ground."""
    circles = []
    for k, off in enumerate((0.02, -0.3, 0.3)):
        r = h * 0.5 * (1.0 if k == 0 else rng.uniform(0.7, 0.9))
        circles += leafy(cx + off * w, base - r, r, rng, ref.TREE_SCALLOP)
    return circles


def ball(cx, base, w, h, rng):
    """A round crown: a leafy ball, with a second below it when the crown is tall."""
    r = w / 2
    circles = leafy(cx, base - h + r, r, rng, ref.TREE_SCALLOP)
    if h > w * 1.1:
        circles += leafy(cx, base - r * 0.9, r * 0.95, rng, ref.TREE_SCALLOP)
    return circles


SHAPES = {'round': ball, 'lumpy': lumpy, 'flat': flat, 'fir': fir, 'poplar': poplar, 'shrub': shrub}


def crown(cx, base, w, h, rng, shape='round'):
    """The circles one tree crown standing on base is the union of, in one of CROWN_SHAPES' silhouettes, w and h
    scaled to that shape's proportions; its core circle first."""
    sw, sh = ref.CROWN_SHAPES[shape]
    return SHAPES[shape](cx, base, w * sw, h * sh, rng)


def tree_row(x0, x1, base_at, width, height, rng):
    """[(crown circles, its core)] of a row of crowns of uneven size and of every shape from x0 to x1, each standing
    on base_at(x), overlapping its neighbour."""
    row = []
    shapes = dealer(rng, list(ref.CROWN_SHAPES))
    x = x0 + width * rng.uniform(0.2, 0.6)
    while x < x1:
        size = rng.uniform(0.75, 1.3)
        w = width * size * rng.uniform(0.9, 1.1)
        h = height * size * rng.uniform(0.9, 1.1)
        circles = crown(x, base_at(x), w, h, rng, next(shapes))
        row.append((circles, circles[0]))
        span = max(cx + r for cx, _, r in circles) - min(cx - r for cx, _, r in circles)
        x += max(span, width * 0.6) * rng.uniform(0.5, 0.8)
    return row


def clump(svg, rows, colours):
    """A clump of trees: one shaded mass round every crown of every row, with no line as the terrace's distant trees
    have none, then the crowns: the back rows only as a few caps showing between the front crowns, the front row
    each with its body inset toward the upper right and some with a lit cap, so the crowns read on the mass in a
    few flat values."""
    body, lit, shade = colours
    svg.path(circle_union([c for row in rows for circles, _ in row for c in circles]), shade, name='mass')
    for k, row in enumerate(rows):
        front = k == len(rows) - 1
        for circles, core in row:
            capped = rng_of(core).random() < (ref.FRONT_ROW_CAPS if front else ref.BACK_ROW_CAPS)
            if not (front or capped):
                continue
            svg.open('tree')
            if front:
                svg.path(circle_union(shifted(circles, 0.08, -0.1, 0.88)), body, name='body')
            if capped:
                svg.path(circle_union(lit_cap(circles, core)), lit if front else body,
                         name='lit cap')
            svg.close()


def rng_of(core):
    """A random stream of a crown's own, so its lit cap's scallops don't change the row's placement."""
    return random.Random('%s %s' % (f(core[0]), f(core[1])))


def woods(svg, hills_by_name, rng):
    """The tree lines along the far hills' feet and the copses on their slopes: each clump two rows of crowns, the
    back row standing higher so its crowns show between the front ones, paler the farther off the clump stands."""
    far, near = ref.WOODS_COLOURS
    svg.open('woods')
    for x0, x1, on, rise, width, height, depth in ref.WOODS:
        colours = tuple(mix(a, b, depth) for a, b in zip(far, near))
        hill = hills_by_name[on]
        back = tree_row(x0 + width * 0.3, x1 - width * 0.3, lambda x: hill.top(x) - rise - height * 0.5,
                        width * 0.9, height * 0.9, rng)
        front = tree_row(x0, x1, lambda x: hill.top(x) - rise, width, height, rng)
        svg.open('clump')
        clump(svg, [back, front], colours)
        svg.close()
    svg.close()


# ================================================================ bushes
def lobe_row(cx, cy, r, spread, rng):
    """The circles of one lobe: its core, and a row of slightly smaller ones either side out to spread, close enough
    to merge into one mound, so a lobe spread wide is a low wide mound and not a string of beads."""
    m = max(1, round(spread / (r * 0.8)))
    row = [(cx, cy, r)]
    for k in range(1, m + 1):
        d = spread * k / m
        row.append((cx - d, cy + r * 0.12 * k / m, r * rng.uniform(0.86, 0.94)))
        row.append((cx + d, cy + r * 0.1 * k / m, r * rng.uniform(0.88, 0.96)))
    return row


def hump(t, crown, low):
    """How high a top stands at t of the way across when its crown stands at crown and its ends rise low: a tent,
    NEAR_DOME 1 straight-sided, above 1 fuller in the middle."""
    reach = (t - crown) / (crown if t < crown else 1 - crown)
    return 1 - (1 - low) * abs(reach) ** ref.NEAR_DOME


def saddle(t):
    """A top with two crowns at SADDLE_AT, dipping to SADDLE_DIP between them and falling to the shoulders outside."""
    a, b = ref.SADDLE_AT
    if t < a:
        return 1 - (1 - ref.SHOULDER_LEAST) * (a - t) / a
    if t > b:
        return 1 - (1 - ref.SHOULDER_LEAST) * (t - b) / (1 - b)
    m = (a + b) / 2
    return 1 - (1 - ref.SADDLE_DIP) * (1 - abs(t - m) / (m - a))


def snapped(crown, n):
    """The crown's place moved to the middle of the nearest of n lobes across, so one lobe stands at the crown."""
    return (min(n - 1, max(0, round(crown * n - 0.5))) + 0.5) / n


def top_rise(profile, t, n, rng):
    """How high, as a share of its height, a bush's or mound's top stands t of the way across its n lobes in this
    profile."""
    if profile == 'flat':
        return rng.uniform(*ref.FLAT_TOP)
    if profile == 'humped left':
        return hump(t, snapped(ref.HUMP_AT, n), ref.HUMP_LOW)
    if profile == 'humped right':
        return hump(t, snapped(1 - ref.HUMP_AT, n), ref.HUMP_LOW)
    if profile == 'saddle':
        return saddle(t)
    return math.sin(math.pi * (0.1 + 0.8 * t)) ** 0.7


def spire(cx, foot, h, rng):
    """The pointed spire of a young fir, SPIRE bush heights tall and wide, rising out of a bush h tall at cx."""
    sw, sh = ref.CROWN_SHAPES['fir']
    sh_, sw_ = ref.SPIRE
    return crown(cx, foot, h * sw_ / sw, h * sh_ / sh, rng, 'fir')


def bush_lobes(x, foot, w, h, rng, profile='arch'):
    """(top lobes, foot lobes): the few broad mounds a bush is built of, each a short row of circles so it is wider
    than tall: a row of uneven size along the profile's top over the foot, one per LOBE_SPAN heights of width, under
    an arch one of them the tallest near the middle, in a spired bush one near the middle a conifer's spire, and a
    close row of small ones at the foot so it sits flat on the ground."""
    top, base = [], []
    arched = profile in ('arch', 'spired')
    n = max(ref.BUSH_LOBES, round(w / (h * ref.LOBE_SPAN)))
    tallest = rng.randrange(n // 3, max(n // 3 + 1, 2 * n // 3))
    for k in range(n):
        t = (k + 0.5) / n
        arch = top_rise(profile, t, n, rng) * (rng.uniform(0.8, 1.0) if arched else 1)
        if k == tallest and arched:
            arch = 1.0
        top_at = h * (0.2 + 0.8 * arch)
        r = min(h * rng.uniform(0.36, 0.5) * (0.8 + 0.4 * arch), top_at / 1.9)   # a low lobe is a low, wide one
        cx = x - w / 2 + w * t + rng.uniform(-w * 0.04, w * 0.04)
        cy = foot - top_at + r
        cy = max(min(cy, foot - r * 0.9), foot - h + r * 0.9)
        if k == tallest and profile == 'spired':
            top.append(spire(cx, foot, h, rng))
            continue
        spread = max(r * rng.uniform(*(ref.FLAT_LOBE_SPREAD if profile == 'flat' else ref.LOBE_SPREAD)),
                     h * ref.LOBE_REACH - r * 0.9)
        top.append(lobe_row(cx, cy, r, spread, rng))
    r = h * 0.2
    m = int(w / (r * 0.5))
    for k in range(m):
        t = (k + 0.5) / m
        base.append((x - w / 2 + r * 0.7 + (w - r * 1.4) * t, foot - r, r))
    return top, base


def mound_bumps(x, foot, w, h, rng, profile='dome'):
    """[(bump, its column)] of a near bush: one mound w wide rising to its crown h px above its foot where the
    profile puts it, a dome's somewhere near its middle, stepping down unevenly to its low shoulders, a leafy bump
    of uneven size every NEAR_BUMP px along its top, and under each bump a column of leaves reaching down to the
    flat foot."""
    n = max(ref.BUSH_LOBES, round(w / ref.NEAR_BUMP))
    crown_at = rng.uniform(*ref.CROWN_AT)
    biggest = min(w / n * max(ref.BUMP_SIZES), h * 0.6)
    reach = h - biggest * ref.SCALLOP * 0.7      # the bumps rise to here; their leaves reach the bush's height
    sizes = dealer(rng, ref.BUMP_SIZES)
    out = []
    for k in range(n):
        t = (k + 0.5) / n
        top = hump(t, crown_at, ref.SHOULDER_LEAST) if profile == 'dome' else top_rise(profile, t, n, rng)
        rise = 1 - (1 - top) * rng.uniform(*ref.SHOULDER_STEP)
        r = min(w / n * next(sizes) * rng.uniform(0.95, 1.05), h * 0.6)
        cx = x - w / 2 + w * t + rng.uniform(-0.15, 0.15) * w / n
        cy = min(foot - reach * rise + r, foot - r)
        column = (foot - cy) / 2 + r * 0.6
        out.append(((cx, cy, r), (cx, foot - column, column)))
    return out


def skip_tip_draws(bumps, foot, h, rng):
    """Make the random draws that once gave a few bumps a pointed leafy tip, since taken out, so every bush and the
    grass after it keep the shapes they had."""
    for (cx, cy, r), _ in bumps:
        if rng.random() < ref.TIP_CHANCE and cy - r * ref.TIP_REACH >= foot - h:
            rng.uniform(-0.1, 0.1)


def highlit(bumps, leafy_bumps, foot, h):
    """[(bump, its leafy circles)] the yellow-green highlight catches: the bumps from MOUND_HIGHLIGHT_FROM of the way
    across rightward that rise to the upper part of the mound, and the crown's at the least."""
    pairs = list(zip(bumps, leafy_bumps))
    tops = [foot - (bump[1] - bump[2]) for bump, _ in bumps]
    sunny = [(pair, top) for k, (pair, top) in enumerate(zip(pairs, tops))
             if (k + 0.5) / len(pairs) >= ref.MOUND_HIGHLIGHT_FROM]
    out = [pair for pair, top in sunny if top >= h * ref.MOUND_HIGHLIGHT_RISE]
    return out or [max(sunny, key=lambda s: s[1])[0]]


def lightened(colours, size, biggest):
    """A near bush's colours mixed toward NEAR_LIGHT the smaller it is than the biggest bush: the small bushes a step
    lighter and yellower than the big ones, as in the reference."""
    t = ref.NEAR_LIGHTEN * (1 - size / biggest)
    body, lit, shade, rim = colours
    return tuple(mix(c, ref.NEAR_LIGHT, t) for c in (body, lit, shade)) + (mix(rim, ref.NEAR_LIGHT, t / 2),)


def mound(svg, x, foot, w, h, rng, colours, outline, profile='dome', name='bush'):
    """A near bush as one leafy mound, as in the reference: its silhouette in the shade colour with its outline, a
    darker shade of that, round it alone, every bump's leaves and column moved toward the light over it so the lower
    left stays dark, a lit facet on each bump on the sunny side, and a row of leaves along its flat foot filling the
    dips between the bumps so it stands as one mass, standing on a flat dark foot of grass blades over the outline's
    bottom."""
    body, lit, shade, rim = colours
    bumps = mound_bumps(x, foot, w, h, rng, profile)
    leafy_bumps = [leafy(*bump, rng) for bump, _ in bumps]
    skip_tip_draws(bumps, foot, h, rng)
    columns = [column for _, column in bumps]
    base_r = h * ref.MOUND_BASE
    base = [(x - w / 2 + base_r + (w - 2 * base_r) * k / 8, foot - base_r, base_r) for k in range(9)]
    silhouette = [c for circles in leafy_bumps for c in circles] + columns + base
    svg.open(name)
    svg.path(circle_union(silhouette), shade, name='mass')
    for (bump, column), circles in sorted(zip(bumps, leafy_bumps), key=lambda b: b[0][0][1]):
        svg.path(circle_union(shifted(circles + [column], *ref.MOUND_BODY_INSET)), body, name='lobe')
        svg.stroke(circle_union(shifted(circles, *ref.MOUND_BODY_INSET)), shade, outline * ref.CREASE,
                   name='crease')
    for k, ((bump, _), circles) in enumerate(zip(bumps, leafy_bumps)):
        if (k + 0.5) / len(bumps) >= ref.MOUND_LIT_FROM:
            svg.path(circle_union(scaled_about(circles, bump, *ref.MOUND_LIT_INSET)), lit, name='lit')
    for (bump, _), circles in highlit(bumps, leafy_bumps, foot, h):
        svg.path(circle_union(scaled_about(circles, bump, *ref.MOUND_HIGHLIGHT_INSET)), rim, name='highlight')
    svg.stroke(circle_union(silhouette), edge_of(shade), outline, name='outline')
    reach = w / 2 - base_r * 0.5
    fringe = fine_blades([(x - reach, foot - outline), (x + reach, foot - outline)], rng)
    bottom = max(cy + r for _, cy, r in silhouette) + outline
    svg.path(polyline(fringe) + ' L%s,%s L%s,%s Z' % (f(x + reach), f(bottom), f(x - reach), f(bottom)), shade, name='foot')
    svg.close()


def leafy_lobe(cores, rng):
    """The circles of one leafy mound: every core circle scalloped round its rim, the first core first."""
    return [c for core in cores for c in leafy(*core, rng)]


def bush_silhouette(x, foot, w, h, rng):
    """The circles a bush's leafy silhouette is the union of: every lobe scalloped round its rim."""
    top, base = bush_lobes(x, foot, w, h, rng)
    return [c for lobe in top for c in leafy_lobe(lobe, rng)] + base


def lobe(svg, circles, colours, outline, sunny):
    """One lobe of a bush: its shaded leafy shape, the body moved toward the light over it so the lower left stays in
    shade, the lit crescent moved further, on a sunny lobe a bright rim along its upper right, and when the bush is
    outlined the line over them all so the lit shapes end at the lobe's edge."""
    body, lit, shade, rim = colours
    core = circles[0]
    shape = circle_union(circles)
    svg.path(shape, shade, name='lobe')
    svg.path(circle_union(scaled_about(circles, core, *ref.BUSH_BODY_INSET)), body, name='body')
    svg.path(circle_union(scaled_about(circles, core, *ref.BUSH_LIT_INSET)), lit, name='lit')
    if sunny:
        svg.path(circle_union(scaled_about(circles, core, *ref.BUSH_RIM_INSET)), rim, name='rim')
    if outline:
        svg.stroke(shape, edge_of(shade), outline, name='outline')


def bush(svg, x, foot, w, h, rng, colours, outline, profile='arch', name='bush'):
    """One leafy bush standing on its foot: its few broad lobes drawn back to front, each shaded on its lower left so
    the shade shows where one lobe stands over another, the lobes on the sunny side with a bright rim, and a dark
    flat foot over the lobes' bottoms so the bush sits into the grass."""
    top, base = bush_lobes(x, foot, w, h, rng, profile)
    crowns = [(k, leafy_lobe(lobe, rng)) for k, lobe in enumerate(top)]
    svg.open(name)
    svg.path(circle_union(base), colours[2], name='foot')
    for k, circles in sorted(crowns, key=lambda c: c[1][0][1]):
        lobe(svg, circles, colours, outline, (k + 0.5) / len(crowns) >= ref.BUSH_RIM_FROM)
    svg.close()


def bushes(svg, name, placed, rng, colours, outline, near=False):
    svg.open(name)
    biggest = max(w * h for _, _, w, h in placed)
    profiles = bush_profiles(len(placed), rng, ref.MOUND_PROFILES if near else ref.BUSH_PROFILES)
    for (x, foot, w, h), profile in zip(placed, profiles):
        if near:
            mound(svg, x, foot, w, h, rng, lightened(colours, w * h, biggest), outline, profile)
        else:
            bush(svg, x, foot, w, h, rng, colours, outline, profile)
    svg.close()


# ================================================================ track
def band(y0, y1):
    return 'M%d,%s H%d V%s H%d Z' % (LEFT, f(y0), RIGHT, f(y1), LEFT)


def sleepers(svg):
    """The one row of boards under the rail, seen edge on: the dark between them the whole width, and each board's lit
    end over it every SLEEPER_PITCH px, an on-off pattern."""
    top, bottom, _, _, between, lit = ref.SLEEPERS
    y0, y1 = RAIL_TOP + top, RAIL_TOP + bottom
    svg.path(band(y0, y1), between, name='between the boards')
    x = LEFT
    while x < RIGHT:
        svg.path(poly([(x, y0), (x + SLEEPER_WIDTH, y0), (x + SLEEPER_WIDTH, y1), (x, y1)]), lit, name='sleeper')
        x += SLEEPER_PITCH


def track(svg, rng):
    """The straight level railway seen edge on: the ground behind it with a grass fringe down to the rail, the rail's
    thin dark top line and the thicker grey metal under it at RAIL_TOP, the row of boards under the metal, and the
    ground in front down to the bushes."""
    edge, top_colour, foot_colour = ref.TRACK_GROUND
    svg.open('track')
    y_top = min(y for _, y in edge)
    svg.path(polyline(fine_blades(edge, rng)) + ' L%d,%s L%d,%s Z' % (RIGHT, f(RAIL_TOP), LEFT, f(RAIL_TOP)),
             (top_colour, foot_colour, y_top, RAIL_TOP), name='ground behind')
    for name, rail_top, rail_bottom, rail_colour in ref.RAIL:
        svg.path(band(RAIL_TOP + rail_top, RAIL_TOP + rail_bottom), rail_colour, name=name)
    sleepers(svg)
    near, far = ref.TRACK_FOOT_COLOURS
    foot = RAIL_TOP + ref.SLEEPERS[1]
    svg.path(band(foot, ref.TRACK_FOOT), (near, far, foot, ref.TRACK_FOOT), name='ground in front')
    depth, colour = ref.TRACK_SHADOW
    svg.path(band(foot, foot + depth), colour, name='shadow')
    meadow_bands(svg, ref.TRACK_MEADOW, ref.TRACK_MEADOW_PLANES, rng, ref.MEADOW[0][0])
    svg.close()


# ================================================================ meadow
class Band:
    def __init__(self, edge):
        self.top = Line(edge)


def tuft(x, y, h):
    """Three blades of grass standing at x, y, the middle one h px tall, as a polygon."""
    return poly([(x - 3, y), (x - 1.6, y - h * 0.7), (x - 0.6, y - 1), (x, y - h), (x + 0.6, y - 1),
                 (x + 2, y - h * 0.8), (x + 3, y)])


def drift(x, y, rng):
    """A drift of small flowers around x, y: a handful of dots as one shape."""
    lo, hi, r0, r1, spread = ref.DRIFT
    dots = [(x + rng.uniform(-spread, spread), y + rng.uniform(-spread / 3, spread / 3), rng.uniform(r0, r1))
            for _ in range(rng.randint(lo, hi))]
    return circle_union(dots)


def in_calm(x, rng):
    """Whether a scattered thing at x is dropped to keep the ground calm under the menu buttons."""
    x0, x1, kept = ref.MEADOW_CALM
    return x0 <= x <= x1 and rng.random() > kept


def scatter(svg, bands, k, front, rng, colour):
    """The tufts and flower drifts over band k, between its top fringe and the crest of the band in front of
    it, the next of bands or front for the last."""
    tufts, drifts = ref.MEADOW_TUFTS['meadow' if bands is ref.MEADOW else 'track'][k]
    top = Line(bands[k][0])
    floor = Line(bands[k + 1][0] if k + 1 < len(bands) else front)
    below, above = ref.SCATTER_INSET
    lo, hi = ref.TUFT[:2]
    for count, name in ((tufts, 'tuft'), (drifts, 'drift')):
        for _ in range(count):
            x = rng.uniform(LEFT, RIGHT)
            y0, y1 = top(x) + below, floor(x) - above
            y = rng.uniform(y0, y1)
            if y1 <= y0 or in_calm(x, rng):
                continue
            if name == 'tuft':
                svg.path(tuft(x, y, rng.uniform(lo, hi)), colour, name=name)
            else:
                svg.path(drift(x, y, rng), rng.choice(ref.DRIFT_COLOURS), name=name)


def meadow_bands(svg, bands, planes, rng, front):
    """Meadow bands back to front, each band's top a fringe of grass over the one behind, down to the crest of
    front, the edge of whatever stands in front of the last band: the fine blades of the far band behind the track,
    the terrace's tall tufts across the open meadow. Planes slant across each band as its lit slopes and hollows,
    then tufts and flower drifts are scattered over it."""
    open_meadow = bands is ref.MEADOW
    fringe = blades if open_meadow else fine_blades
    for k, (edge, top_colour, foot_colour) in enumerate(bands):
        y_top = min(y for _, y in edge)
        y_foot = max(y for _, y in (bands[k + 1][0] if k + 1 < len(bands) else front))
        svg.path(polyline(fringe(edge, rng)) + ' L%d,%d L%d,%d Z' % (RIGHT, BOTTOM, LEFT, BOTTOM),
                 (top_colour, foot_colour, y_top, y_foot), name='band')
        for i, x0, x1, drop0, drop1, depth, colour in planes:
            if i == k:
                svg.path(light_plane(Band(edge), x0, x1, drop0, drop1, depth), colour,
                         name='plane' if open_meadow else 'swathe')
        scatter(svg, bands, k, front, rng, ref.TUFT[3] if open_meadow else ref.TUFT[2])


def meadow(svg, rng):
    """The open meadow in front, with lighter and darker planes slanting across its bands."""
    svg.open('meadow')
    meadow_bands(svg, ref.MEADOW, ref.MEADOW_PLANES, rng, [(LEFT, BOTTOM), (RIGHT, BOTTOM)])
    svg.close()


def spring_valley(svg):
    svg.open('Spring Valley')
    all_hills = hills()
    by_name = {h.name: h for h in all_hills}
    for i in range(len(all_hills)):
        if all_hills[i].name == 'hills middle':
            woods(svg, by_name, random.Random('%s woods' % SEED))
        draw_hill(svg, all_hills, i)
    bushes(svg, 'bushes far', ref.BUSHES_FAR, random.Random('%s bushes far' % SEED), ref.BUSHES_FAR_COLOURS, 0)
    track(svg, random.Random('%s track' % SEED))
    bushes(svg, 'bushes', ref.BUSHES_NEAR, random.Random('%s bushes' % SEED), ref.BUSH_COLOURS, TOWN_LINE_WIDTH,
           near=True)
    meadow(svg, random.Random('%s meadow' % SEED))
    svg.close()


def main():
    svg = Svg()
    spring_valley(svg)
    svg.write(cutting.sheet_path('scenery/spring_valley.svg'))


def cut():
    """{name: its image}: each hill, the woods, the bushes, the track and the meadow, each where it sits and uncropped
    past the sheet's edges."""
    root, grads = cutting.load('scenery/spring_valley.svg')
    out = {}
    for g in cutting.find_group(root, 'Spring Valley'):
        name = g.get('id')
        out[name] = cutting.static_part('scenery/parts/spring-valley/' + cutting.slug(name), [g], grads, name, None)
    return out


def parts():
    return list(cut().values())


if __name__ == '__main__':
    main()


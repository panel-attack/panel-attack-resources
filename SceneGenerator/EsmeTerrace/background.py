#   Writes SVG, run by `python3 -m scene_export render`: EsmeTerrace/background.svg, the trees the terrace's camera
#   sees: the woods on the lake's far shore and the hills behind it (Far trees), the trees among the houses (Town),
#   the near woods, cypresses and flowering shrubs just beyond the rail (Near trees), and the shrub at the rail's
#   left end. The trees are placements of plants/trees.py's templates.
#
#   python3 -m EsmeTerrace.background  ->  background.svg

import functools
import math
import os
import random

from common.painting import (FLOWER, FLOWER_CENTRE, FLOWER_DEEP, SEED, WIDTH, Svg, blossom, crown_field,
                             curve_y, inside_foliage, land_colours, mix)
from plants import foliage, trees
from scenery import landscape
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))


TREE_BASE = 610                  # trees stand on this line (hidden by the rail)


CYPRESS_GIRTH = 1.3              # feature cypresses are this much wider than their listed half width


# feature cypresses (x, top y, half width); the rest of the band is scattered
CYPRESSES = [(28, 350, 30), (150, 410, 24), (322, 388, 27), (402, 440, 21),
             (1012, 432, 21), (1300, 428, 21), (1382, 434, 22), (1414, 396, 25), (1468, 340, 30),
             (1524, 396, 27)]


# cypresses standing in the town itself, in front of the houses (x, top y, half width)
TOWN_CYPRESSES = [(479, 432, 19)]


# cypresses standing behind the town's buildings (x, top y, half width)
BEHIND_TOWN_CYPRESSES = [(938, 382, 34)]


SCATTER_STEP = 64                # spacing of scattered trees along the band


KEEP_CLEAR = [(790, 870)]        # x ranges kept free of tall trees (central tower)


# leafy clumps by the water among the houses: (x, top y, width, depth, flowers); depth past 1 turns yellow-green
TOWN_TREES_FRONT = [(520, 508, 56, 0.95, 0), (558, 494, 84, 1.12, 0), (718, 492, 70, 0.98, 2),
                    (905, 510, 92, 0.95, 4), (1090, 506, 66, 1.05, 0), (1280, 498, 72, 0.95, 2)]


CLUMP_BASE = 562                 # clumps by the water stand on this line (hidden behind the rail)


# low woods just behind the rail at either side: (name, top line, bottom, crown radius, depth)
NEAR_WOODS = [
    ('near woods left', [(-20, 470), (60, 466), (140, 474), (220, 488), (300, 506), (370, 524), (430, 546)],
     620, 20, 0.88),
    ('near woods right', [(1120, 524), (1190, 504), (1260, 498), (1330, 504), (1400, 508), (1460, 498),
                          (1560, 470)], 620, 20, 0.88),
]


NEAR_TREES_FROM = (380, 1150)    # the scattered back row stays outside this x range so the lake shows


# flowering shrubs right behind the rail, its whole length. The middle is one receding band:
# (top line, depth, leaf crown width). The sides are separate rounded shrubs along a line:
# (name, x0, x1, top line, depth, leaf crown width)
SHRUB_BAND = ([(380, 534), (520, 544), (680, 548), (840, 546), (1000, 544), (1160, 532)], 0.92, 13)


SHRUB_SIDES = [
    ('shrubs left', -40, 480, [(-40, 488), (70, 482), (170, 494), (260, 508), (340, 522), (430, 540), (480, 550)],
     0.98, 20),
    ('shrubs right', 1080, 1580, [(1080, 550), (1150, 532), (1230, 514), (1320, 500), (1420, 490), (1500, 482),
                                  (1580, 486)], 0.98, 20),
]


SHRUB_WIDTH = (64, 118)          # px, each side shrub


SHRUB_GAP = (6, 26)              # px between neighbouring side shrubs


SHRUB_HEIGHT = (0.55, 0.8)       # dome height as a share of width


SHRUB_BOTTOM = 620


BLOSSOM_SIZE = (2.2, 8.0)        # petal-ring radius, farthest (middle, high in the shrub) .. nearest (sides)


BLOSSOM_STEP = (22, 9)           # px along the middle band between blossoms, farthest .. nearest


BLOSSOM_SPACING = (10, 15)       # px of shrub width per blossom, farthest .. nearest: near ones are bigger and fewer


# the near flowering shrub behind the rail's left end: its leafy top and flowers rise over the handrail and
# its leaves show through the openings below. (outline, seed, leaf length, flower size, flowers, whites)
RAIL_END_SHRUB = ([(-20, 712), (-20, 505), (12, 498), (37, 500), (62, 515), (80, 535), (93, 560), (98, 600),
                   (92, 650), (80, 712)], 30, 24.0, 40.0, 6, 1)


BLOSSOM_HAZE = 0.4               # farthest blossoms mixed this far toward the shrub green


BLOSSOM_WHITE = 0.12             # share of white blossoms


BLOSSOM_WHITE_COLOURS = ('#ffffff', '#c9d8e6')   # white petals, their shaded lower-right


# ---------------------------------------------------------------- far trees
# Woods on the far side of the lake, standing on scenery/landscape.py's hills: a dense band of cypresses and leafy
# clumps along the far waterline, woods on the banks at either end with their biggest trees down by the water,
# hazy woods on the hill faces behind the banks and stands of tiny trees along the hill crests, where the reference
# painting has them.
FAR_SHORE = (330, 1240)          # x span of the band along the far waterline


FAR_SHORE_ROWS = 3               # rows of the band, each standing further up the far hills than the one before


FAR_SHORE_ROW_RISE = 12          # px each row stands above the one in front


FAR_SHORE_TREE = (22, 66)        # px tall, a front-row band tree


FAR_SHORE_STEP = (14, 24)        # px between neighbouring band trees


# stands of crest trees: (x from, x to, hill on whose top line they stand)
FAR_CREST_STANDS = [(120, 160, 'left hill'), (160, 280, 'far hills'), (320, 390, 'far hills'), (425, 490, 'far hills'),
                    (684, 764, 'haze hills'), (783, 1010, 'far hills'), (1128, 1320, 'far hills'),
                    (1368, 1546, 'right hill')]


FAR_CREST_TREE = (10, 20)        # px tall


FAR_CREST_STEP = (5, 10)         # px between neighbouring crest trees


FAR_CREST_SINK = (0.05, 0.25)    # how far below the ridge a crest tree's foot stands, in its heights


# hazy woods down the hill faces behind the banks: (x from, x to, rows)
FAR_SLOPES = [(0, 400, 1), (1260, 1546, 2)]


FAR_SLOPE_HILLS = ('left hill', 'far hills', 'haze hills', 'right hill')   # hills whose skyline the woods hang from


FAR_SLOPE_DEPTH = (6, 40)        # px below the skyline a hill face tree's foot stands


FAR_SLOPE_TREE = (16, 36)        # px tall


FAR_SLOPE_STEP = (6, 14)         # px between neighbouring hill face trees


# the wooded banks at either end of the lake: (name, hill whose top line the woods start under, ground line
# they run down to, trees, spread, reach); a spread above 1 gathers the trees up under the crest, below 1 down by
# the water; reach is the share of the bank, from its outer end, where the trees grow to full size: toward the
# lake they stay small
FAR_BANKS = [('left bank trees', 'left hill', 'left bank', 34, 0.4, 0.3),
             ('right bank trees', 'right hill', 'right bank', 44, 0.45, 0.55)]


FAR_BANK_SHRUB = (9, 16)         # px tall, the low shrubs along a bank's waterline


FAR_BANK_SHRUB_STEP = (12, 30)   # px between neighbouring shrubs


FAR_BANK_SHRUB_SINK = (0, 4)     # px above the waterline a shrub stands


FAR_BANK_FROM = 8                # px under the hill's top line where the bank woods start


FAR_BANK_TREE = (30, 98)         # px tall, furthest up the bank .. down by the water


FAR_BANK_DARK_FROM = 65          # px tall from which a bank tree is always a cypress with a round tree at its foot


FAR_SHORE_CYPRESS_SHARE = 0.68   # share of the band's trees that are cypresses; the rest are leafy clumps


FAR_BANK_CYPRESS_SHARE = 0.5     # share of the banks' smaller trees that are cypresses


FAR_BANK_FOOT_CLUMP = (0.2, 0.45)   # how far beside a big bank cypress its lit round tree stands, in its heights


FAR_BANK_FOOT_CLUMP_SIZE = 0.9   # a big bank cypress's round tree, in the cypress's heights before FAR_CLUMP_HEIGHT


FAR_CYPRESS_SHAPE = (3.3, 5.5)   # a far cypress's height in half widths: broader than the flames beyond the rail


FAR_CLUMP_HEIGHT = 0.55          # a far clump's height, in the height a cypress in its place would have


FAR_CLUMP_TALLEST = 38           # px


FAR_CLUMPS = ('far-clump', 'far-clump-round', 'far-clump-wide')


def hill_line(name, which):
    """The named hill's top or bottom line in scenery/landscape.py."""
    hill = next(h for h in landscape.HILLS if h[0] == name)
    return hill[1] if which == 'top' else hill[2]


def far_cypress(svg, rng, name, x, base, h, variant):
    """A cypress h px tall of a random far shape, drawn from the variant's template, standing on (x, base)."""
    hw = h / rng.uniform(*FAR_CYPRESS_SHAPE)
    trees.placed_cypress(svg, name + ' cypress', x, base - h, hw, base, variant=variant)


def far_clump(svg, rng, name, x, base, h):
    """A leafy clump of a random shape standing on (x, base) in place of a cypress h px tall: lower and rounder."""
    trees.placed(svg, name + ' clump', rng.choice(FAR_CLUMPS), x, base, min(h * FAR_CLUMP_HEIGHT, FAR_CLUMP_TALLEST))


def far_crest_trees(svg, rng):
    """Tiny far cypresses in stands along the skyline of the hills behind the lake, their tips poking above it."""
    svg.open('far ridge trees')
    for x0, x1, hill in FAR_CREST_STANDS:
        ridge = hill_line(hill, 'top')
        x = x0 + rng.uniform(0, FAR_CREST_STEP[1])
        while x < x1:
            h = rng.uniform(*FAR_CREST_TREE)
            base = curve_y(ridge, x) + h * rng.uniform(*FAR_CREST_SINK)
            far_cypress(svg, rng, 'far ridge', x, base, h, 'farthest')
            x += rng.uniform(*FAR_CREST_STEP)
    svg.close()


def far_slope_trees(svg, rng):
    """Hazy woods hanging down the faces of the hills behind the banks, under their skyline."""
    skylines = [hill_line(name, 'top') for name in FAR_SLOPE_HILLS]
    placed = []
    for x0, x1, rows in FAR_SLOPES:
        for _ in range(rows):
            x = x0 + rng.uniform(0, FAR_SLOPE_STEP[1])
            while x < x1:
                sky = min(curve_y(line, x) for line in skylines if line[0][0] <= x <= line[-1][0])
                placed.append((sky + rng.uniform(*FAR_SLOPE_DEPTH), x, rng.uniform(*FAR_SLOPE_TREE)))
                x += rng.uniform(*FAR_SLOPE_STEP)
    svg.open('far slope trees')
    for base, x, h in sorted(placed):
        far_cypress(svg, rng, 'far slope', x, base, h, 'farthest')
    svg.close()


def far_shore_trees(svg, rng):
    """The band along the far waterline, its back rows smaller and further up the far hills."""
    waterline = hill_line('far hills', 'bottom')
    placed = []
    for row in reversed(range(FAR_SHORE_ROWS)):
        x = FAR_SHORE[0] + rng.uniform(0, FAR_SHORE_STEP[1])
        while x < FAR_SHORE[1]:
            base = curve_y(waterline, x) - row * FAR_SHORE_ROW_RISE - rng.uniform(0, 5)
            placed.append((base, x, rng.uniform(*FAR_SHORE_TREE) * (1 - 0.2 * row)))
            x += rng.uniform(*FAR_SHORE_STEP)
    svg.open('far shore trees')
    for base, x, h in sorted(placed):
        if rng.random() < FAR_SHORE_CYPRESS_SHARE:
            far_cypress(svg, rng, 'far shore', x, base, h, 'farthest' if base < curve_y(waterline, x) - 8 else 'far')
        else:
            far_clump(svg, rng, 'far shore', x, base, h)
    svg.close()


def far_bank_trees(svg, rng, name, hill, bank, count, spread, reach):
    """Woods on a bank at one end of the lake, from under the hill's crest down to the water, most of them low
    down, the trees bigger further down; only towards the bank's outer end, away from the lake, do they grow to
    full size. Low shrubs line the waterline."""
    top, shore, hill_shore = hill_line(hill, 'top'), hill_line(bank, 'bottom'), hill_line(hill, 'bottom')

    def ground(x):
        return curve_y(shore if shore[0][0] <= x <= shore[-1][0] else hill_shore, x)
    x0, x1 = top[0][0], top[-1][0]
    outer = x0 if WIDTH / 2 - x0 > x1 - WIDTH / 2 else x1
    placed = []
    for _ in range(count):
        x = rng.uniform(x0, x1)
        v = rng.random() ** spread
        grown = min(1, (1 - abs(x - outer) / (x1 - x0)) / (1 - reach)) ** 2
        lower = ground(x)
        upper = min(curve_y(top, x) + FAR_BANK_FROM, lower)
        base = upper + (lower - upper) * v
        h = (FAR_BANK_TREE[0] + (FAR_BANK_TREE[1] - FAR_BANK_TREE[0]) * v * grown) * rng.uniform(0.8, 1.1)
        if h > FAR_BANK_DARK_FROM:
            placed.append((base, x, h, 'cypress'))
            off = h * rng.uniform(*FAR_BANK_FOOT_CLUMP)
            fx = max((x - off, x + off), key=ground)
            if ground(fx) < base:
                fx = x
            placed.append((min(base + 3, ground(fx)), fx, h * FAR_BANK_FOOT_CLUMP_SIZE, 'foot clump'))
        elif rng.random() < FAR_BANK_CYPRESS_SHARE:
            placed.append((base, x, h, 'cypress'))
        else:
            placed.append((base, x, h, 'clump'))
    x = x0 + rng.uniform(0, FAR_BANK_SHRUB_STEP[1])
    while x < x1:
        placed.append((ground(x) - rng.uniform(*FAR_BANK_SHRUB_SINK), x, rng.uniform(*FAR_BANK_SHRUB), 'shrub'))
        x += rng.uniform(*FAR_BANK_SHRUB_STEP)
    svg.open(name)
    for base, x, h, kind in sorted(placed):
        label = name.removesuffix(' trees')
        if kind == 'cypress':
            far_cypress(svg, rng, label, x, base, h, 'far')
        elif kind == 'shrub':
            trees.placed(svg, label + ' shrub', 'far-shrub', x, base, h)
        else:
            far_clump(svg, rng, label + (' foot' if kind == 'foot clump' else ''), x, base, h)
    svg.close()


def far_trees(svg, rng):
    svg.open('Far trees')
    far_crest_trees(svg, rng)
    far_slope_trees(svg, rng)
    far_shore_trees(svg, rng)
    for bank in FAR_BANKS:
        far_bank_trees(svg, rng, *bank)
    svg.close()


def town_trees(svg):
    """The trees standing among the houses, behind and in front of them."""
    svg.open('Town')
    svg.open('cypresses behind houses')
    for x, top, hw in BEHIND_TOWN_CYPRESSES:
        trees.placed_cypress(svg, 'cypress behind houses', x, top, hw, TREE_BASE + 30)
    svg.close()
    svg.open('trees among houses')
    for x, top, w, _, flowers in TOWN_TREES_FRONT:
        trees.placed_clump(svg, 'clump', x, top, w, flowers, CLUMP_BASE)
    svg.close()
    svg.open('town cypresses')
    for x, top, hw in TOWN_CYPRESSES:
        trees.placed_cypress(svg, 'town cypress', x, top, hw, TREE_BASE)
    svg.close()
    svg.close()


def clear(x):
    return not any(a <= x <= b for a, b in KEEP_CLEAR)


def outside_middle(x):
    return not NEAR_TREES_FROM[0] <= x <= NEAR_TREES_FROM[1]


def near_trees(svg, rng):
    svg.open('Near trees')
    # back row: hazier cypresses scattered behind the feature trees, only at the sides
    svg.open('back row')
    x = -20
    while x < WIDTH + 20:
        edge = max(0.0, 1 - min(x, WIDTH - x) / 300)
        if rng.random() < (0.55 if x < WIDTH / 2 else 0.3) and clear(x) and outside_middle(x):
            top, hw = rng.uniform(445, 485) - edge * 50, rng.uniform(16, 21)
            # drawn into nothing so rng moves on as it always has, keeping everything drawn after it in place
            trees.cypress(Svg(), x, top, hw, TREE_BASE, rng=rng, haze_t=trees.FAR_CYPRESS_HAZE)
            trees.placed_cypress(svg, 'back row cypress', x, top, hw, TREE_BASE, variant='hazy')
        x += SCATTER_STEP * rng.uniform(0.7, 1.3)
    svg.close()
    for name, top, bottom, r, depth in NEAR_WOODS:
        crown_field(svg, rng, top, bottom, depth, r, name)
    svg.open('feature cypresses')
    for cx, top, hw in CYPRESSES:
        top += rng.uniform(-6, 6)
        trees.cypress(Svg(), cx, top, hw * CYPRESS_GIRTH, base=TREE_BASE + 30, rng=rng)    # as for the back row
        trees.placed_cypress(svg, 'feature cypress', cx, top, hw * CYPRESS_GIRTH, TREE_BASE + 30)
    svg.close()
    flower_shrubs(svg, rng)
    svg.close()


def nearness(x):
    """0 in the middle of the band (furthest), 1 at the sides."""
    return min(1.0, abs(x - WIDTH / 2) / (WIDTH / 2 - 220)) ** 1.4


def add_blossom(tiers, rng, x, y, r):
    tier = 0 if r < 3.2 else 1 if r < 5 else 2
    shade, petals, centre = blossom(x, y, r)
    white = rng.random() < BLOSSOM_WHITE
    parts = tiers[tier]
    parts[4 if white else 0].append(shade)
    parts[2 if white else 1].append(petals)
    parts[3].append(centre)


def side_shrubs(svg, rng, tiers, name, x0, x1, line, depth, crown_w):
    """Separate rounded shrubs with gaps between, blossoms clustered on each one's sunlit upper-left."""
    svg.open(name)
    x = x0
    while x < x1:
        w = rng.uniform(*SHRUB_WIDTH)
        cx = x + w / 2
        h = w * rng.uniform(*SHRUB_HEIGHT)
        top = curve_y(line, max(line[0][0], min(line[-1][0], cx))) + rng.uniform(-6, 10)
        dome = [(cx - w / 2, top + h * 0.95), (cx - w * 0.36, top + h * 0.28), (cx - w * 0.06, top),
                (cx + w * 0.34, top + h * 0.22), (cx + w / 2, top + h * 0.95)]
        crown_field(svg, rng, dome, SHRUB_BOTTOM, depth, crown_w / 2, 'shrub', free_standing=True, crown_w=crown_w)
        n = nearness(cx)
        r0 = BLOSSOM_SIZE[0] + (BLOSSOM_SIZE[1] - BLOSSOM_SIZE[0]) * n
        count = max(2, int(w / (BLOSSOM_SPACING[0] + (BLOSSOM_SPACING[1] - BLOSSOM_SPACING[0]) * n)))
        placed = tries = 0
        while placed < count and tries < count * 6:
            tries += 1
            u, v = rng.uniform(-0.4, 0.15), rng.uniform(0.15, 0.55)
            r = r0 * rng.uniform(0.7, 1.1) * (0.8 + 0.4 * v)
            bx, by = cx + u * w, top + v * h + 2
            if inside_foliage(dome, bx, by, r):
                add_blossom(tiers, rng, bx, by, r)
                placed += 1
        x += w + rng.uniform(*SHRUB_GAP)
    svg.close()


def flower_shrubs(svg, rng):
    """Flowering shrubs behind the rail: separate rounded shrubs at the sides, one receding band in
    the middle; blossoms shrink and haze as they recede so the band melts into the trees and town."""
    svg.open('Flowering shrubs')
    tiers = {k: ([], [], [], [], []) for k in range(3)}   # pink shade, pink petals, white petals, centres, white shade
    top, depth, crown_w = SHRUB_BAND
    crown_field(svg, rng, top, SHRUB_BOTTOM, depth, crown_w / 2, 'shrubs middle', crown_w=crown_w)
    x = top[0][0] + 4
    while x < top[-1][0] - 4:
        n = nearness(x)
        ty = curve_y(top, x)
        y = ty + rng.uniform(4, 5 + 50 * (0.4 + n))
        lift = max(0.0, min(1.0, (y - ty) / 40))
        r = (BLOSSOM_SIZE[0] + (BLOSSOM_SIZE[1] - BLOSSOM_SIZE[0]) * n) * (0.75 + 0.35 * lift) * rng.uniform(0.8, 1.15)
        bx = x + rng.uniform(-3, 3)
        if inside_foliage(top, bx, y, r):
            add_blossom(tiers, rng, bx, y, r)
        x += (BLOSSOM_STEP[0] + (BLOSSOM_STEP[1] - BLOSSOM_STEP[0]) * n) * rng.uniform(0.5, 1.5)
    for side in SHRUB_SIDES:
        side_shrubs(svg, rng, tiers, *side)
    leaf = land_colours(1.1)[0]
    for tier, label in ((0, 'far blossoms'), (1, 'blossoms'), (2, 'near blossoms')):
        shade, pink, white, centres, white_shade = tiers[tier]
        t = BLOSSOM_HAZE * (1 - tier / 2)
        svg.open(label)
        if shade:
            svg.path(' '.join(shade), mix(FLOWER_DEEP, leaf, t), name='petal shade')
        if white_shade:
            svg.path(' '.join(white_shade), mix(BLOSSOM_WHITE_COLOURS[1], leaf, t), name='white petal shade')
        if pink:
            svg.path(' '.join(pink), mix(FLOWER, leaf, t), name='pink petals')
        if white:
            svg.path(' '.join(white), mix(BLOSSOM_WHITE_COLOURS[0], leaf, t), name='white petals')
        if centres:
            svg.path(' '.join(centres), mix(FLOWER_CENTRE, leaf, t), name='centres')
        svg.close()
    svg.close()


def rail_end_shrub(svg):
    """Drawn with the planters' bush recipe so it matches the near foliage. Flowers that don't sit
    inside the leaf mass are dropped (with their stems), as for every other blossom."""
    outline, seed, leaf, flower, flowers, whites = RAIL_END_SHRUB
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    x0, x1 = max(min(xs), 0), max(xs)
    base = ((x0 + x1) / 2, max(ys) - 0.35 * (max(ys) - min(ys)))
    centres = {}
    make_flower = foliage.flower

    def flower_at(name, c, radius, *a, **k):
        centres[name] = (c, radius)
        return make_flower(name, c, radius, *a, **k)
    foliage.flower = flower_at
    try:
        shapes = foliage.bush('rail end shrub', base, x1 - x0, base[1] - min(ys), 1.1, seed, leaf, flower,
                              flowers=flowers, whites=whites, spill=0.0, silhouette=outline,
                              sweep=(-1.2, math.pi + 1.2), flower_band=(0.55, 0.85),
                              flower_phi=(0.9, 2.0))
    finally:
        foliage.flower = make_flower
    upper = sorted({(x, y) for x, y in outline if y < 640}, key=lambda p: p[0])
    dropped = [n for n, ((cx, cy), r) in centres.items() if not inside_foliage(upper, cx, cy, r)]
    svg.open('Rail end shrub')
    for s in shapes:
        if any(s.name.startswith(n) for n in dropped):
            continue
        fill = foliage.GRADIENTS.get(s.fill, s.fill)
        extra = ' fill-opacity="%g"' % s.opacity if s.opacity < 1 else ''
        svg.path(s.d, fill, None if s.stroke == 'none' else s.stroke, s.width, name=s.name, extra=extra)
    svg.close()
    return centres, dropped


def main():
    svg = Svg()
    town_trees(svg)
    near_trees(svg, random.Random(SEED + 5))
    rail_end_shrub(svg)
    far_trees(svg, random.Random(SEED + 20))
    svg.write(cutting.sheet_path('EsmeTerrace/background.svg'))


OWN_IMAGES = {'near woods left', 'near woods right', 'Flowering shrubs'}


@functools.cache
def cut():
    """(images, nodes): background.svg's groups as nodes, each tree a ref to its template where background.svg
    places it, the OWN_IMAGES and each run of everything else one image named after its first element."""
    root, grads = cutting.load('EsmeTerrace/background.svg')
    parts = []

    def nodes(parent):
        out, run = [], []

        def image(name, elements):
            part = cutting.static_part('EsmeTerrace/parts/background/' + cutting.slug(name), elements, grads, name)
            parts.append(part)
            out.append(cutting.image_node(name.lower(), part))

        def flush():
            if run:
                image(run[0].get('id'), list(run))
                run.clear()

        for ch in parent:
            if cutting.svgtools.local(ch.tag) == 'defs':
                continue
            if ch.get('data-template'):
                flush()
                out.append(cutting.marker_ref(ch, 'plants/trees.json'))
            elif ch.get('id') in OWN_IMAGES:
                flush()
                image(ch.get('id'), [ch])
            elif any(d.get('data-template') or d.get('id') in OWN_IMAGES for d in ch.iter()):
                flush()
                out.append({'id': ch.get('id').lower(), 'children': nodes(ch)})
            else:
                run.append(ch)
        flush()
        return out
    drawn = nodes(root)
    return parts, drawn


def parts():
    return cut()[0]


if __name__ == '__main__':
    main()

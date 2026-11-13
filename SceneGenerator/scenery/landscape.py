#   Writes SVG, run by `python3 -m scene_export render`: scenery/landscape.svg, the mountains, hills, lake and grass
#   (Landscape) and the meadow on the lake's near shore with trees scattered in it (Far village).
#
#   python3 -m scenery.landscape  ->  landscape.svg

import math
import os
import random

from common.painting import HEIGHT, SEED, WIDTH, Svg, curve_y, f, mix, poly
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- mountains
# Flat faceted ranges, the paler one behind. Light comes from the right: a range is filled with its blue,
# its summits' right flanks are lilac lit planes, and narrow blue gullies cut down across the lit planes.
# Every face pales toward MOUNTAIN_HAZE at its foot.
# (name, blue, lilac, ridge, lit planes, gullies as (top, bottom, half width))
RANGES = [
    ('far range', '#6cb6fa', '#84b3f2',
     [(-10, 294), (0, 297), (100, 335), (173, 315), (250, 341), (293, 329), (345, 345), (420, 352), (700, 352),
      (760, 338), (840, 326), (890, 338), (940, 348), (1300, 348), (1440, 332), (1500, 322), (1537, 307),
      (1546, 309)],
     [[(0, 297), (100, 335), (80, 350), (30, 330)],
      [(173, 315), (250, 341), (240, 360), (205, 352), (182, 334)],
      [(293, 329), (345, 345), (330, 356), (300, 345)],
      [(840, 326), (890, 338), (880, 350), (848, 342)]],
     []),
    ('near range', '#5598ee', '#92a7e8',
     [(150, 380), (230, 365), (290, 346), (340, 326), (380, 310), (400, 308), (410, 303), (440, 275), (459, 265),
      (500, 287), (533, 310), (557, 315), (603, 300), (653, 330), (700, 350), (780, 352), (850, 331), (897, 323),
      (940, 315), (960, 300), (995, 271), (1020, 272), (1057, 240), (1070, 236), (1105, 215), (1147, 242),
      (1157, 245), (1207, 288), (1233, 297), (1268, 315), (1302, 289), (1320, 288), (1358, 260), (1400, 283), (1433, 303),
      (1455, 302), (1490, 322), (1546, 300)],
     [[(459, 265), (500, 287), (533, 310), (557, 315), (522, 340), (500, 392), (470, 400), (448, 337), (452, 310)],
      [(603, 300), (653, 330), (700, 350), (665, 392), (625, 392), (607, 330)],
      [(1358, 260), (1400, 283), (1433, 303), (1455, 302), (1490, 322), (1507, 337), (1480, 395), (1410, 395),
       (1383, 330), (1373, 300)]],
     [((470, 285), (522, 372), 7), ((498, 296), (540, 350), 5), ((612, 316), (642, 365), 6),
      ((1395, 300), (1440, 365), 6), ((1440, 318), (1480, 365), 5)]),
]


MOUNTAIN_HAZE = ('#74c4fb', 0.4)    # (colour, share) a face is mixed toward at its foot


MOUNTAIN_FOOT = 470


# The snow-capped summit right of centre, lit from the left unlike the lilac summits: light rock strips
# slanting up its blue left flank, shaded snow high on the left, and sunlit snow over the apex and right
# ridge with a toothed lower edge, a tongue down the central gully and shaded streaks across it.
LIGHT_STRIPS = ('#88bffc', [((1088, 288), (950, 356), 14), ((1062, 238), (975, 310), 11), ((1098, 245), (1035, 278), 9),
                            ((940, 316), (895, 346), 8)])


SNOW_SHADE = ('#b2cafa', [((1100, 222), (1060, 262), 7), ((1096, 250), (1045, 285), 6)])


SNOW = ('#f4f6fb',
        [[(1105, 215), (1147, 242), (1157, 245), (1207, 288), (1220, 312), (1200, 300), (1210, 330), (1182, 310),
          (1167, 300), (1158, 317), (1145, 292), (1130, 282), (1112, 300), (1100, 280), (1098, 255), (1100, 233)],
         [(1068, 308), (1090, 298), (1110, 310), (1123, 348), (1087, 330), (1073, 323)],
         [(1233, 297), (1268, 315), (1258, 323), (1240, 310)],
         [(995, 271), (1020, 272), (1007, 280)]])


SNOW_STREAKS = ('#c9d6f6', [((1120, 247), (1157, 297), 3), ((1143, 283), (1180, 307), 3)])


# ---------------------------------------------------------------- hills and lake
# Smooth rolling hills between the mountains and the water, back to front: blue far off, teal-green and
# yellow-green nearer, each with flat lit planes slanting down its slopes and a thin sandy strip where it
# meets the water. Lines are (x, y) points joined by eased curves.
# (name, top line, bottom line, (colour at top, at foot), [(plane top line, plane bottom line, colour)],
#  (sand colour, px))
HILLS = [
    ('haze hills',
     [(560, 400), (620, 380), (760, 380), (880, 384), (960, 388), (1040, 378),
      (1140, 370), (1200, 374), (1260, 384), (1320, 392), (1380, 380), (1440, 370), (1500, 374), (1546, 368)],
     [(560, 460), (1546, 460)], ('#56abf4', '#5ea7fa'),
     [([(1380, 382), (1440, 372), (1500, 376), (1546, 370)], [(1440, 386), (1546, 384)], '#63b8e9')], ('#5eaaee', 0)),
    ('far hills',
     [(150, 392), (250, 378), (350, 368), (430, 368), (500, 370), (560, 372), (620, 360), (680, 348),
      (730, 350), (800, 362), (860, 375), (920, 382), (980, 372), (1050, 364), (1100, 358), (1140, 357),
      (1200, 372), (1260, 390), (1320, 398), (1400, 400)],
     [(150, 458), (500, 457), (700, 455), (850, 456), (1000, 453), (1150, 455), (1400, 458)], ('#3f99d8', '#3e99c3'),
     [([(352, 371), (430, 386), (500, 418)], [(392, 388), (470, 410)], '#64bbc0'),
      ([(700, 349), (800, 364), (880, 395), (1000, 440)], [(735, 384), (880, 422), (1000, 442)], '#64bbc0'),
      ([(900, 425), (960, 432), (1040, 446)], [(960, 438)], '#51acc9')],
     ('#a6cdc6', 3)),
    ('right hill',
     [(1110, 463), (1150, 450), (1200, 432), (1250, 415), (1300, 402), (1350, 400), (1420, 388), (1480, 372),
      (1546, 358)],
     [(1110, 463), (1180, 470), (1250, 476), (1546, 480)], ('#2f8bc4', '#318ec0'),
     [([(1300, 452), (1380, 432), (1460, 412), (1546, 395)], [(1340, 462), (1450, 440), (1546, 420)], '#48a19f')],
     ('#8fc3cf', 3)),
    ('right bank',
     [(1215, 486), (1270, 472), (1330, 458), (1400, 440), (1460, 425), (1546, 408)],
     [(1215, 486), (1300, 491), (1420, 497), (1546, 504)], ('#4fa595', '#48a090'),
     [([(1290, 468), (1370, 451), (1450, 436), (1546, 424)], [(1340, 462), (1450, 448), (1546, 440)], '#3a95a0'),
      ([(1300, 478), (1420, 472), (1546, 468)], [(1420, 484), (1546, 482)], '#3a95a0'),
      ([(1240, 482), (1300, 476), (1360, 474)], [(1270, 488), (1330, 486)], '#46a08a')],
     ('#a1b381', 7)),
    ('left hill',
     [(-10, 330), (60, 338), (110, 350), (160, 368), (220, 388), (290, 410), (360, 435), (410, 455), (432, 467)],
     [(-10, 505), (260, 474), (432, 467)], ('#409cb7', '#3f9aa8'),
     [([(-10, 405), (100, 403), (200, 410), (300, 420), (380, 445), (432, 467)],
       [(-10, 480), (120, 452), (240, 466), (330, 472), (432, 467)], '#8dcb6e')],
     ('#d8cc82', 5)),
    ('left bank',
     [(-10, 408), (50, 420), (100, 438), (160, 456), (220, 474), (270, 485), (312, 491)],
     [(-10, 505), (150, 500), (312, 491)], ('#a2d462', '#93cc5e'),
     [([(-10, 438), (60, 452), (130, 472), (200, 490)], [(-10, 504), (100, 501), (200, 496)], '#66b576'),
      ([(40, 428), (120, 446), (180, 466)], [(60, 438), (140, 460), (180, 468)], '#6fb978')],
     ('#d8cc82', 6)),
]


LAKE_TOP = 440


LAKE_COLOURS = ('#40aeee', '#2d9be4', 455, 600)


# Each shore hangs a reflection on the water under its waterline: the shore's foot colour mixed toward the woods'
# green and then into the water, hanging depth px with the inverted tips of the trees along its lower edge, broken
# into strips by the water showing through in ripple lines.
REFLECTION = dict(woods='#1f6f60', woods_share=0.5, water_share=0.5, depth=10, tips=(3, 14), tip_step=(6, 14),
                  taper=20,
                  ripple_every=4.5, ripple=(10, 44), ripple_gap=(3, 12), ripple_width=1.3)


# Light glints on the open water in two sets the scene twinkles in turn: rows of short lens-shaped streaks, closer
# together, longer and thicker nearer the viewer, thickest where the sun off to the left glitters on the lake.
GLINT = dict(colour='#effdff', opacity=0.85, rows=(5, 14), length=(4, 26), width=(0.9, 2.3), gap=(16, 150),
             sun_x=520, sun_reach=420)


# ---------------------------------------------------------------- foreground grass
# Rolling swells in front of the lake, back to front, each lit along its crest and stepping darker down
# to its foot, with flat planes of lighter or darker grass slanting across the far ones; the nearest have
# grass blades along their crest poking up into the swell behind.
# (crest line, lit, foot, px from crest to foot, [(plane top line, plane bottom line, colour)], blades)
SWELLS = [
    ([(-10, 700), (500, 660), (650, 640), (762, 621), (900, 606), (1050, 596), (1200, 588), (1350, 578), (1546, 563)],
     '#b8da48', '#4c9f62', 110,
     [([(1100, 650), (1250, 640), (1400, 632), (1546, 628)], [(1250, 680), (1546, 690)], '#64ae56')],
     False),
    ([(-10, 526), (150, 550), (331, 580), (500, 595), (650, 606), (762, 620), (850, 640), (950, 668), (1050, 700),
      (1546, 760)], '#bcdb4c', '#5aa85a', 120,
     [([(-10, 604), (100, 610), (230, 630), (330, 662)], [(-10, 700), (200, 690)], '#5aa95a'),
      ([(330, 585), (450, 598), (560, 615), (700, 650)], [(450, 606), (560, 632), (640, 650)], '#78ba50'),
      ([(420, 640), (560, 650), (700, 668)], [(560, 660)], '#9fcc48')], False),
    ([(-10, 700), (150, 684), (300, 668), (450, 660), (600, 657), (750, 660), (900, 666), (1050, 672), (1200, 679),
      (1350, 686), (1546, 692)], '#a5d142', '#6cb252', 60, [], False),
    ([(-10, 745), (200, 740), (400, 738), (550, 722), (700, 718), (850, 730), (1000, 740), (1100, 738), (1250, 722),
      (1400, 725), (1546, 730)], '#80bd4c', '#6fb44e', 40, [], True),
    ([(-10, 800), (150, 785), (300, 772), (450, 782), (600, 792), (800, 790), (1000, 792), (1200, 786), (1350, 775),
      (1546, 768)], '#5fa957', '#55a259', 40, [], True),
    ([(-10, 850), (300, 840), (500, 848), (800, 842), (1100, 850), (1300, 838), (1546, 845)], '#509f5c', '#46975e',
     30, [], True),
]


SWELL_STEPS = 16


BLADE = (3, 9, 7)                # blade height px min, max, and spacing


# kept for the far village's meadow: the near shore's waterline, and its edge and glint colours
TOWN_BANK = [(400, 532), (470, 522), (560, 534), (680, 542), (800, 538), (960, 540), (1080, 532),
             (1200, 522), (1300, 518), (1360, 530)]


GRASS_EDGE = '#2f9a72'


SHORE_GLINT = '#d4fdfb'


# ---------------------------------------------------------------- meadow
# The near shore is open meadow from the water down to the canvas bottom: it starts under the feet of the
# left woods, follows TOWN_BANK's waterline and runs in under the right hill's grass bank.
MEADOW_TOP = ([(-20, 601), (250, 601), (330, 563), (396, 561)] + TOWN_BANK
              + [(1430, 515), (WIDTH + 20, 513)])


MEADOW_SHORE = (398, 1440)       # x span where the meadow meets open water; elsewhere it meets woods


MEADOW_GRASS = ('#dcf03c', '#b4dc32')   # a swell's sunlit crest, far .. near


MEADOW_SWELL = ('#64b43c', '#3f9238')   # a swell's shaded foot where the next one rises in front, far .. near


MEADOW_LIGHT = '#e6f84c'         # sunlit tufts, and what a swell's crest leans toward


MEADOW_SWELLS = 6


MEADOW_TUFT = '#5ea82e'


MEADOW_FOOT_GRASS = '#7cc232'


MEADOW_ROLL = (6, 22)            # px a swell's crest rises and falls, far .. near


MEADOW_VALLEY = (850, 1800, (30, 110))  # (x, width, px far .. near): the swells dip into a valley here


MEADOW_TILT = (0.02, 0.05)       # how steeply a swell's crest runs across, in px down per px; neighbours lean opposite ways


MEADOW_SHADING = 22              # steps from a swell's lit crest down to its shaded foot


WOODS_FOOT_SHADOW = ('#5fae5a', 0.45, 9)   # (colour, opacity, px) where the meadow runs in under woods


# (kind, x, base y, width) of each tree standing in the meadow, where the reference painting has them
MEADOW_TREES = [
    ('bush', 1222, 650, 50), ('bush', 1266, 652, 56), ('bush', 1340, 636, 50), ('bush', 1415, 616, 46), ('cypress', 1376, 663, 42), ('bush', 50, 663, 100), ('bush', 1498, 670, 76),
    ('cypress', 133, 671, 40), ('bush', 185, 676, 70), ('bush', 1017, 683, 95), ('bush', 1180, 660, 52), ('bush', 237, 688, 55),
    ('bush', 427, 736, 105), ('cypress', 1448, 768, 53), ('bush', 734, 788, 130), ('bush', 1245, 790, 165),
    ('cypress', 539, 823, 78), ('bush', 60, 843, 120), ('bush', 180, 850, 110), ('bush', 1490, 888, 80),
    ('bush', 1380, 903, 100), ('bush', 410, 953, 160), ('cypress', 285, 963, 90),
]


CYPRESS_HEIGHT = 2.5             # a meadow cypress's height, in widths at its foot


BALL_BUSH = ('#03443c', '#178643', '#8fd23e')   # a leaf ball's shade, body and sunlit cap


CONE_CYPRESS = ('#033c38', '#0c7038', '#5fae36')   # the meadow cypress's leaf balls: shade, body, sunlit cap


LEAF_BALL_HAZE = ('#8ecb6a', 0.3)   # (colour, share) leaf balls at the waterline are mixed toward, none at the bottom


SHORE_BUSH_WIDTH = (40, 70)


BUSH_TRUNK, BUSH_TRUNK_FROM = '#6b4a2a', 90   # trunk colour, and the bush width from which trunks show


DAISY = ('#fdfdf0', '#d8dcc0', '#f4c21e')   # petals, petal edge, centre


DAISY_STEM = '#4f9c2c'


DAISIES = 25                     # scattered singly, besides the clusters


DAISY_CLUSTERS = [(170, 726), (600, 833), (755, 863), (1045, 866), (1160, 846), (1370, 798), (1505, 815),
                  (710, 955), (1145, 985), (490, 1003)]


BUTTERCUP_CLUMPS = [(590, 898), (1490, 968)]


BUTTERCUP = '#f6e23a'


BUTTERCUPS = 20


ROCKS = [(92, 155, 924, 952), (1336, 1420, 942, 972)]   # (x0, x1, top, foot) of each rock in the foreground


ROCK = ('#b7aa98', '#e2d6c4', '#f7f0e4')    # shade, body, sunlit top


TALL_GRASS = [(0, 80), (100, 200), (560, 640), (820, 880), (1420, 1520)]   # x spans of tall grass at the bottom


TALL_GRASS_COLOURS = ('#2c7426', '#4f9c2c')


def circle_union(circles):
    """Exact outline of a union of circles as SVG arcs. circles: [(cx, cy, r)]."""
    arcs = []
    for i, (cx, cy, r) in enumerate(circles):
        covered = []
        inside = False
        for j, (dx, dy, dr) in enumerate(circles):
            if i == j:
                continue
            d = math.hypot(dx - cx, dy - cy)
            if d + r <= dr + 1e-6 and (d > 1e-9 or r < dr or j < i):
                inside = True
                break
            if d >= r + dr or d + dr <= r:
                continue
            phi = math.atan2(dy - cy, dx - cx)
            alpha = math.acos(max(-1.0, min(1.0, (d * d + r * r - dr * dr) / (2 * d * r))))
            covered.append((phi - alpha, phi + alpha))
        if inside:
            continue
        # normalise to [0, 2pi) and find free intervals
        ivs = []
        for a, b in covered:
            span = b - a
            a %= 2 * math.pi
            b = a + span
            if b > 2 * math.pi:
                ivs.append((a, 2 * math.pi))
                ivs.append((0, b - 2 * math.pi))
            else:
                ivs.append((a, b))
        ivs.sort()
        merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else:
                merged.append((a, b))
        if not merged:
            arcs.append((cx, cy, r, 0.0, 2 * math.pi))
            continue
        free = []
        for k in range(len(merged)):
            a = merged[k][1]
            b = merged[(k + 1) % len(merged)][0]
            if k == len(merged) - 1:
                b += 2 * math.pi
            if b - a > 1e-6:
                free.append((a, b))
        for a, b in free:
            arcs.append((cx, cy, r, a, b))

    def pt(cx, cy, r, t):
        return (cx + r * math.cos(t), cy + r * math.sin(t))

    pieces = []
    full = [a for a in arcs if a[4] - a[3] >= 2 * math.pi - 1e-9]
    rest = [a for a in arcs if a[4] - a[3] < 2 * math.pi - 1e-9]
    for cx, cy, r, _, _ in full:
        pieces.append('M%s,%s A%s,%s 0 1 1 %s,%s A%s,%s 0 1 1 %s,%s Z'
                      % (f(cx + r), f(cy), f(r), f(r), f(cx - r), f(cy), f(r), f(r), f(cx + r), f(cy)))
    used = [False] * len(rest)
    for s in range(len(rest)):
        if used[s]:
            continue
        loop = []
        k = s
        while not used[k]:
            used[k] = True
            loop.append(rest[k])
            end = pt(*rest[k][:3], rest[k][4])
            best, bd = None, 1e9
            for m, arc in enumerate(rest):
                if used[m] and m != s:
                    continue
                d = math.dist(end, pt(*arc[:3], arc[3]))
                if d < bd:
                    best, bd = m, d
            if best is None or best == s:
                break
            k = best
        start = pt(*loop[0][:3], loop[0][3])
        d = 'M%s,%s' % (f(start[0]), f(start[1]))
        for cx, cy, r, a, b in loop:
            e = pt(cx, cy, r, b)
            large = 1 if b - a > math.pi else 0
            d += ' A%s,%s 0 %d 1 %s,%s' % (f(r), f(r), large, f(e[0]), f(e[1]))
        pieces.append(d + ' Z')
    return ' '.join(pieces)



def smooth(points, step=6):
    """The eased curve through points (x increasing) as a list of points step px apart."""
    x0, x1 = points[0][0], points[-1][0]
    n = max(2, int((x1 - x0) / step))
    return [(x0 + (x1 - x0) * i / n, curve_y(points, x0 + (x1 - x0) * i / n)) for i in range(n + 1)]


def between(top, bottom):
    """The shape between two lines, both running left to right."""
    return polyline(smooth(top) + smooth(bottom)[::-1]) + ' Z'


def plane(top, bottom):
    """A flat plane on a slope, tapering to a point at each end of its top line short of the canvas edge."""
    inside = [p for p in bottom if top[0][0] < p[0] < top[-1][0]]
    left = [top[0]] if top[0][0] > 0 else [p for p in bottom if p[0] <= top[0][0]]
    right = [top[-1]] if top[-1][0] < WIDTH else [p for p in bottom if p[0] >= top[-1][0]]
    return between(top, left + inside + right)


def hazed(colour, top, haze=MOUNTAIN_HAZE, foot=MOUNTAIN_FOOT):
    """colour fading from top toward haze's colour by its share at the foot."""
    tint, share = haze
    return colour, mix(colour, tint, share), top, foot


def wedge(a, b, w):
    """A narrow leaf-shaped sliver from a to b, w px wide at its widest."""
    (ax, ay), (bx, by) = a, b
    ln = math.hypot(bx - ax, by - ay)
    nx, ny = (by - ay) / ln * w, -(bx - ax) / ln * w
    return poly([a, (ax + (bx - ax) * 0.45 + nx, ay + (by - ay) * 0.45 + ny), b,
                 (ax + (bx - ax) * 0.6 - nx * 0.4, ay + (by - ay) * 0.6 - ny * 0.4)])


SNOWCAP = (LIGHT_STRIPS, SNOW_SHADE, SNOW, SNOW_STREAKS)


def mountains(svg, ranges=RANGES, snowy='near range', snow=SNOWCAP, haze=MOUNTAIN_HAZE, foot=MOUNTAIN_FOOT,
              outline=None, group='Mountains'):
    """The ranges back to front, each down to foot, with the snowcap snow on the range named snowy and, when
    outline is a (colour, px) pair, a line along each ridge. A lit plane given as (colour, points) takes its own
    colour instead of its range's lit one. A range carrying a snowcap as its seventh item wears that one."""
    svg.open(group)
    for name, blue, lit, ridge, planes, cuts, *cap in ranges:
        svg.open(name)
        svg.path(poly(ridge + [(ridge[-1][0], foot), (ridge[0][0], foot)]),
                 hazed(blue, min(y for _, y in ridge), haze, foot), name='blue faces')
        for plane in planes:
            colour, plane = plane if isinstance(plane[0], str) else (lit, plane)
            svg.path(poly(plane), hazed(colour, min(y for _, y in plane), haze, foot), name='lit face')
        if cuts:
            svg.path(' '.join(wedge(*c) for c in cuts), hazed(blue, min(a[1] for a, _, _ in cuts), haze, foot),
                     name='gullies')
        if name == snowy:
            snowcap(svg, *snow)
        elif cap:
            snowcap(svg, *cap[0])
        if outline:
            svg.stroke(polyline(ridge), outline[0], outline[1], name='ridge line')
        svg.close()
    svg.close()


def facet(shape):
    """A snow shape's path: a wedge given as (a, b, width), or a flat facet given as its points."""
    return wedge(*shape) if isinstance(shape[-1], (int, float)) else poly(shape)


def snowcap(svg, strips=LIGHT_STRIPS, shade=SNOW_SHADE, snow=SNOW, streaks=SNOW_STREAKS):
    """A summit's snow, back to front: light rock strips, shaded snow, the snow patches and shaded streaks across
    them, each a (colour, shapes) pair; a layer given as None is left out."""
    svg.open('snow peak')
    for layer, name in ((strips, 'light rock'), (shade, 'snow shade'), (snow, 'snow'), (streaks, 'snow streaks')):
        if layer:
            colour, shapes = layer
            svg.path(' '.join(facet(s) for s in shapes), colour, name=name)
    svg.close()


def hills(svg):
    svg.open('Hills')
    for name, top, bottom, (c0, c1), planes, (sand, width) in HILLS:
        svg.open(name)
        ys = [y for _, y in top]
        svg.path(between(top, bottom), (c0, c1, min(ys), max(y for _, y in bottom)), name='hill')
        for ptop, pbottom, colour in planes:
            svg.path(plane(ptop, pbottom), colour, name='lit plane')
        svg.path(between(bottom, [(x, y + width * tip_taper(x, bottom)) for x, y in smooth(bottom)]), sand,
                 name='sand')
        svg.close()
    svg.close()


def tip_taper(x, line, run=60):
    """1 along a line, narrowing to 0 at an end that stops short of the canvas edge."""
    x0, x1 = line[0][0], line[-1][0]
    t = 1.0
    if x0 > 0:
        t = min(t, (x - x0) / run)
    if x1 < WIDTH:
        t = min(t, (x1 - x) / run)
    return max(0.0, t) ** 0.6


def lake(svg):
    svg.open('Lake')
    svg.path('M-10,%d H%d V%d H-10 Z' % (LAKE_TOP, WIDTH + 10, HEIGHT + 10), LAKE_COLOURS, name='water')
    for name, (shape, colour) in reflections().items():
        svg.open(name + ' reflection')
        svg.path(poly(shape), colour, name='reflection')
        svg.stroke(' '.join(polyline(r) for r in reflection_ripples(name)), LAKE_COLOURS[0], REFLECTION['ripple_width'],
                   name='ripples')
        svg.close()
    svg.close()


def on_open_water(x, y):
    """Whether the lake shows at (x, y): on no hill or its sand, above the grass swells and the near meadow."""
    if y <= LAKE_TOP or y >= meadow_top(x):
        return False
    for _, top, bottom, _, _, (_, sand) in HILLS:
        if (top[0][0] <= x <= top[-1][0] and bottom[0][0] <= x <= bottom[-1][0]
                and curve_y(top, x) <= y <= curve_y(bottom, x) + sand * tip_taper(x, bottom) + 1):
            return False
    for crest, _, _, _, _, bladed in SWELLS:
        if crest[0][0] <= x <= crest[-1][0] and y >= curve_y(crest, x) - (BLADE[1] if bladed else 0) - 1:
            return False
    return True


def shores():
    """The hills that meet the water: {name: (waterline, foot colour)}."""
    return {name: (bottom, colours[1]) for name, _, bottom, colours, _, (_, sand) in HILLS if sand}


def reflections():
    """{shore name: (outline, colour)}, each hanging from its waterline with tree tips along its lower edge."""
    r = REFLECTION
    out = {}
    for name, (bottom, foot) in shores().items():
        rng = random.Random(name + ' reflection')
        line = smooth(bottom)
        x, x1 = bottom[0][0], bottom[-1][0]
        lower = [(x, curve_y(bottom, x))]
        while x < x1:
            step = min(rng.uniform(*r['tip_step']), x1 - x)
            mid = tip_taper(x + step / 2, bottom, r['taper'])
            lower.append((x + step / 2, curve_y(bottom, x + step / 2) + (r['depth'] + rng.uniform(*r['tips'])) * mid))
            x += step
            lower.append((x, curve_y(bottom, x) + r['depth'] * tip_taper(x, bottom, r['taper'])))
        colour = mix(mix(foot, r['woods'], r['woods_share']), LAKE_COLOURS[0], r['water_share'])
        out[name] = (line + lower[::-1], colour)
    return out


def reflection_ripples(name):
    """Broken ripple lines of the water across a shore's reflection."""
    r = REFLECTION
    bottom, _ = shores()[name]
    rng = random.Random(name + ' ripples')
    lines = []
    drop = r['ripple_every']
    while drop < r['depth'] + r['tips'][1]:
        x = bottom[0][0] + rng.uniform(0, r['ripple_gap'][1])
        while x < bottom[-1][0]:
            x1 = min(x + rng.uniform(*r['ripple']), bottom[-1][0])
            lines.append([(xx, curve_y(bottom, xx) + drop) for xx in (x, (x + x1) / 2, x1)])
            x = x1 + rng.uniform(*r['ripple_gap'])
        drop += r['ripple_every']
    return lines


def glints():
    """Two sets of glints on the open water, each (x from, y, x to, thickness)."""
    g = GLINT
    rng = random.Random('glints')
    sets = ([], [])
    near_y = max(meadow_top(x) for x in range(0, WIDTH, 10))
    far_y = min(y for _, y in shores()['far hills'][0])
    y = far_y + 3
    while y < near_y:
        t = (y - far_y) / (near_y - far_y)
        x = rng.uniform(0, g['gap'][1])
        while x < WIDTH:
            sun = math.exp(-((x - g['sun_x']) / g['sun_reach']) ** 2)
            length = (g['length'][0] + (g['length'][1] - g['length'][0]) * t) * rng.uniform(0.6, 1.4)
            width = (g['width'][0] + (g['width'][1] - g['width'][0]) * t) * (0.8 + 0.3 * sun)
            if all(on_open_water(xx, yy) for xx in (x, x + length / 2, x + length) for yy in (y - width, y + width)):
                sets[rng.random() < 0.5].append((x, y, x + length, width))
            x += length + rng.uniform(*g['gap']) * (1.8 - 1.4 * sun)
        y += g['rows'][0] + (g['rows'][1] - g['rows'][0]) * t
    return sets


def glint_shapes(glints):
    """Each glint as a lens tapering to a point at either end."""
    return ' '.join('M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z' % (f(x0), f(y), f((x0 + x1) / 2), f(y - w), f(x1), f(y),
                                                          f((x0 + x1) / 2), f(y + w), f(x0), f(y))
                    for x0, y, x1, w in glints)


def blades(crest, rng):
    """The crest line with grass blades poking up out of it, leaning a little to the right."""
    lo, hi, gap = BLADE
    out = []
    x, x1 = crest[0][0], crest[-1][0]
    while x < x1:
        y = curve_y(crest, x)
        h = rng.uniform(lo, hi)
        out += [(x, y), (x + gap * 0.45 + h * 0.3, y - h), (x + gap * 0.6, y)]
        x += gap * rng.uniform(0.8, 1.3)
    return out + [(x1, curve_y(crest, x1))]


def grass(svg, rng):
    svg.open('Grass')
    for crest, lit, foot, depth, planes, bladed in SWELLS:
        line = blades(crest, rng) if bladed else smooth(crest)
        x0, x1 = crest[0][0], crest[-1][0]
        svg.open('swell')
        svg.path(polyline(line) + ' L%s,%s L%s,%s Z' % (f(x1), f(HEIGHT + 10), f(x0), f(HEIGHT + 10)), foot,
                 name='foot')
        for j in range(SWELL_STEPS):
            t = (SWELL_STEPS - j) / SWELL_STEPS
            lower = [(x, curve_y(crest, x) + depth * t) for x, _ in smooth(crest)]
            svg.path(polyline(line) + ' L' + ' L'.join('%s,%s' % (f(x), f(y)) for x, y in lower[::-1]) + ' Z',
                     mix(foot, lit, ((j + 1) / SWELL_STEPS) ** 0.6), name='light')
        for ptop, pbottom, colour in planes:
            svg.path(plane(ptop, pbottom), colour, name='plane')
        svg.close()
    svg.close()


MEADOW_FAR = min(y for _, y in MEADOW_TOP)


def meadow_top(x):
    return curve_y(MEADOW_TOP, x)


def nearness(y):
    """0 at the meadow's far edge by the water .. 1 at the canvas bottom."""
    return max(0.0, min(1.0, (y - MEADOW_FAR) / (HEIGHT - MEADOW_FAR)))


def polyline(points):
    return 'M' + ' L'.join('%s,%s' % (f(x), f(y)) for x, y in points)


def along_top(x0, x1, drop=lambda x: 0.0, step=6):
    n = max(2, int((x1 - x0) / step))
    xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    return [(x, meadow_top(x) + drop(x)) for x in xs]


def tuft(x, y, s):
    return ('M%s,%s L%s,%s L%s,%s L%s,%s L%s,%s L%s,%s Z'
            % (f(x - s), f(y + s * 0.3), f(x - s * 0.7), f(y - s * 1.1), f(x - s * 0.2), f(y),
               f(x + s * 0.2), f(y - s * 1.5), f(x + s * 0.5), f(y), f(x + s), f(y - s * 0.9)))


def swells(svg, rng):
    """The meadow rolling away from the water: overlapping swells dipping toward a valley and rising to the
    edges, each lit along its crest and stepping darker down to its foot where the next one rises in front,
    closer together further away."""
    vx, span, (dip0, dip1) = MEADOW_VALLEY

    def valley(x):
        return 0.5 + 0.5 * math.cos(2 * math.pi * max(-0.5, min(0.5, (x - vx) / span)))
    xs = [-20 + i * 8 for i in range(int((WIDTH + 40) / 8) + 1)]
    crests = []
    for k in range(1, MEADOW_SWELLS + 2):
        v = (k / MEADOW_SWELLS) ** 1.5
        amp = MEADOW_ROLL[0] + (MEADOW_ROLL[1] - MEADOW_ROLL[0]) * min(1, v)
        dip = dip0 + (dip1 - dip0) * min(1, v)
        waves = [(rng.uniform(2 * math.pi / 1400, 2 * math.pi / 700), rng.uniform(0, 2 * math.pi))]
        tilt = (-1) ** k * rng.uniform(*MEADOW_TILT) * min(1, v * 2)

        def crest(x):
            shore = curve_y(TOWN_BANK, x)
            wave = sum(math.sin(x * k_ + p) for k_, p in waves)
            return max(meadow_top(x) + 3, shore + (HEIGHT - shore) * v + amp * wave
                       + dip * valley(x) + tilt * (x - WIDTH / 2))
        crests.append((v, [crest(x) for x in xs]))
    svg.open('swells')
    for (v, line), (_, nxt) in zip(crests, crests[1:]):
        lit = mix(mix(MEADOW_GRASS[0], MEADOW_GRASS[1], v), MEADOW_LIGHT, rng.uniform(0, 0.2))
        shade = mix(MEADOW_SWELL[0], MEADOW_SWELL[1], min(1, v))
        svg.path(polyline(zip(xs, line)) + ' L%s,%s L-20,%s Z' % (f(WIDTH + 20), f(HEIGHT + 10), f(HEIGHT + 10)),
                 shade, name='swell')
        for j in range(MEADOW_SHADING):
            t = (MEADOW_SHADING - j) / MEADOW_SHADING
            foot = [y + max(4.0, (n - y) * 0.95) * t for y, n in zip(line, nxt)]
            svg.path(polyline(list(zip(xs, line)) + list(zip(reversed(xs), reversed(foot)))) + ' Z',
                     mix(shade, lit, ((j + 1) / MEADOW_SHADING) ** 1.3), name='swell light')
    svg.close()


def woods_foot(svg):
    """A soft shade on the meadow where it runs in under the woods either side of the water."""
    colour, opacity, depth = WOODS_FOOT_SHADOW
    pieces = []
    for x0, x1 in ((-20, MEADOW_SHORE[0]), (MEADOW_SHORE[1], WIDTH + 20)):
        top = along_top(x0, x1)
        foot = along_top(x0, x1, lambda x: depth * (0.6 + 0.4 * math.sin(x * 0.07)))
        pieces.append(polyline(top) + ' L' + ' L'.join('%s,%s' % (f(x), f(y)) for x, y in reversed(foot)) + ' Z')
    svg.path(' '.join(pieces), colour, name='woods foot shadow', extra=' fill-opacity="%g"' % opacity)


def meadow_tufts(svg, rng):
    """Grass tufts strewn over the meadow, small far off and larger close up, some dark and some sunlit."""
    dark, light = [], []
    for _ in range(260):
        x = rng.uniform(-10, WIDTH + 10)
        top = meadow_top(x)
        y = top + 4 + (HEIGHT - top) * rng.random() ** 1.6
        s = 1.6 + 8 * nearness(y) * rng.uniform(0.7, 1.2)
        (light if rng.random() < 0.3 else dark).append(tuft(x, y, s))
    svg.path(' '.join(dark), MEADOW_TUFT, name='tufts')
    svg.path(' '.join(light), MEADOW_LIGHT, name='sunlit tufts')


def shore(svg, rng):
    """The meadow's edge on the open water: a dark water edge and a glint on the water just off it."""
    edge = along_top(*MEADOW_SHORE, lambda x: -0.5)
    svg.stroke(polyline(edge), GRASS_EDGE, 1.6, name='water edge')
    glint = []
    x = MEADOW_SHORE[0] + rng.uniform(0, 10)
    while x < MEADOW_SHORE[1] - 10:
        ln = rng.uniform(10, 40)
        if rng.random() < 0.6:
            glint.append(polyline(along_top(x, x + ln, lambda x: -3.5, step=5)))
        x += ln + rng.uniform(8, 30)
    svg.stroke(' '.join(glint), SHORE_GLINT, 1.4, name='shore glint')


def meadow(svg, rng):
    svg.open('meadow')
    svg.path(polyline(along_top(-20, WIDTH + 20)) + ' L%s,%s L-20,%s Z' % (f(WIDTH + 20), f(HEIGHT + 10),
                                                                          f(HEIGHT + 10)),
             (MEADOW_GRASS[0], MEADOW_GRASS[1], MEADOW_FAR, HEIGHT), name='grass')
    swells(svg, rng)
    woods_foot(svg)
    meadow_tufts(svg, rng)
    shore(svg, rng)
    svg.close()


def meadow_trees():
    """(kind, x, base y, width) of each meadow tree, back to front."""
    return sorted(MEADOW_TREES, key=lambda t: t[2])


def scattered_trees(svg):
    """Each meadow tree, a cypress or a round bush, standing in grass and hazier further off."""
    rng = random.Random(SEED + 9)
    svg.open('meadow trees')
    for i, (kind, x, base, w) in enumerate(meadow_trees()):
        near = nearness(base)
        svg.open('meadow tree %d' % (i + 1))
        if kind == 'cypress':
            cone_cypress(svg, rng, x, base, w, w * CYPRESS_HEIGHT, near)
        else:
            ball_bush(svg, rng, x, base, w, near)
        foot_grass(svg, rng, x, base, w * 1.1)
        svg.close()
    svg.close()


def foot_grass(svg, rng, x, base, w):
    """Grass blades growing up over the foot of a tree, so it stands in the meadow instead of on it."""
    s = max(2.0, w / 22)
    blades = [tuft(x + rng.uniform(-0.5, 0.5) * w, base + rng.uniform(0, 0.25) * s, s * rng.uniform(0.8, 1.3))
              for _ in range(max(4, int(w / 10)))]
    svg.path(' '.join(blades), MEADOW_FOOT_GRASS, name='foot grass')


def shore_bushes(svg):
    """A row of small round bushes along the meadow's edge on the open water."""
    rng = random.Random(SEED + 10)
    svg.open('shore bushes')
    spots = []
    x = MEADOW_SHORE[0] + rng.uniform(0, 10)
    while x < MEADOW_SHORE[1]:
        w = rng.uniform(*SHORE_BUSH_WIDTH)
        spots.append((x, w))
        x += w * rng.uniform(0.7, 1.6)
    for i, (x, w) in enumerate(spots):
        if i in (0, len(spots) - 1) or rng.random() < 0.6:
            ball_bush(svg, rng, x, meadow_top(x) + rng.uniform(12, 34), w, 0.0)
    svg.close()


def circle(x, y, r):
    return 'M%s,%s A%s,%s 0 1,0 %s,%s A%s,%s 0 1,0 %s,%s Z' % (f(x - r), f(y), f(r), f(r), f(x + r), f(y), f(r), f(r),
                                                                f(x - r), f(y))


def leaf_balls(svg, rng, balls, palette, near):
    """Round leaf balls [(x, y, r)] in drawing order, each shaded below and lit on its upper left, mixed toward
    the haze by how far off they stand (near 0 at the waterline .. 1 at the canvas bottom)."""
    haze, share = LEAF_BALL_HAZE
    shade, body, lit = (mix(c, haze, share * (1 - near)) for c in palette)
    for bx, by, br in balls:
        svg.path(circle(bx, by, br), shade, name='ball shade')
        svg.path(circle(bx - br * 0.14, by - br * 0.18, br * 0.8), body, name='ball')
        lr = br * rng.uniform(0.3, 0.42)
        svg.path(circle(bx - br * 0.36, by - br * 0.98 + lr, lr), lit, name='ball lit')


def cone_cypress(svg, rng, x, base, w, h, near):
    """A cypress h tall and w wide at its foot: a cone of leaf balls, small at the tip and broad at the foot."""
    r = w * 0.15
    balls = []
    y = base - h + r * 0.5
    while y < base - r * 0.6:
        t = (y - (base - h)) / h
        br = r * (0.5 + 0.5 * t)
        span = max(0.0, (w / 2 - br) * min(1.0, t / 0.85) ** 0.9)
        n = max(1, round(2 * span / (br * 1.3)) + 1)
        for i in range(n):
            bx = x - span + (2 * span * i / (n - 1) if n > 1 else span) + rng.uniform(-0.2, 0.2) * br
            r_ = br * rng.uniform(0.85, 1.15)
            balls.append((bx, min(y + rng.uniform(-0.15, 0.15) * br, base - r_), r_))
        y += br * 0.85
    svg.open('cypress')
    leaf_balls(svg, rng, balls, CONE_CYPRESS, near)
    svg.close()


def ball_bush(svg, rng, x, base, w, near):
    """A bush w wide standing on base: a dome of round leaf balls, the lower rows in front."""
    h, r = w * 0.66, w * 0.13
    rows = 4
    balls = []
    for j in range(rows):
        t = j / (rows - 1)
        span = w * (0.3 + 0.7 * math.sin(math.pi / 2 * (0.35 + 0.65 * t))) - 2 * r
        n = max(1, round(span / (r * 1.35)) + 1)
        for i in range(n):
            u = i / (n - 1) if n > 1 else 0.5
            bx = x - span / 2 + span * u + rng.uniform(-0.3, 0.3) * r
            br = r * rng.uniform(0.8, 1.2) * (1 + 0.15 * t)
            by = base - h + r + (h - 2 * r) * t + rng.uniform(-0.25, 0.25) * r + r * 0.4 * (2 * u - 1) ** 2 * (1 - t)
            balls.append((bx, min(by, base - br * 0.98), br))
    svg.open('ball bush')
    if w > BUSH_TRUNK_FROM:
        for tx in (x - w * 0.15, x + w * 0.12):
            svg.path(poly([(tx - w * 0.02, base), (tx - w * 0.012, base - h * 0.45), (tx + w * 0.012, base - h * 0.45),
                           (tx + w * 0.02, base)]), BUSH_TRUNK, name='trunk')
    leaf_balls(svg, rng, balls, BALL_BUSH, near)
    svg.close()


def far_village(svg):
    """The meadow on the lake's near shore and the trees scattered in it."""
    meadow(svg, random.Random(SEED + 6))
    daisies(svg, random.Random(SEED + 12))
    shore_bushes(svg)
    scattered_trees(svg)
    rocks(svg)
    tall_grass(svg, random.Random(SEED + 13))


def daisies(svg, rng):
    """White daisies on short stems, in clusters and a few alone, and small yellow buttercups, larger toward the
    bottom."""
    petals, centres, cups, stems = [], [], [], []

    def daisy(x, y):
        r = 1.5 + 6 * nearness(y) * rng.uniform(0.8, 1.2)
        petals.append(circle_union([(x + r * 0.6 * math.cos(a), y + r * 0.45 * math.sin(a), r * 0.42)
                                    for a in (2 * math.pi * k / 7 for k in range(7))]))
        centres.append(circle(x, y, r * 0.3))
        stems.append('M%s,%s Q%s,%s %s,%s' % (f(x), f(y + r * 0.3), f(x + rng.uniform(-2, 2) * r * 0.3), f(y + r * 1.6),
                                             f(x + rng.uniform(-1, 1) * r * 0.4), f(y + r * 3)))

    def buttercup(x, y):
        r = 1.2 + 3.5 * nearness(y) * rng.uniform(0.8, 1.2)
        cups.append(circle_union([(x + r * 0.3 * math.cos(a), y + r * 0.3 * math.sin(a), r * 0.3)
                                  for a in (2 * math.pi * k / 5 for k in range(5))]))

    def anywhere():
        x = rng.uniform(10, WIDTH - 10)
        top = meadow_top(x)
        return x, top + 30 + (HEIGHT - top - 40) * rng.random() ** 0.6
    for cx, cy in DAISY_CLUSTERS:
        spread = 10 + 30 * nearness(cy)
        for _ in range(rng.randint(3, 7)):
            daisy(cx + rng.uniform(-1, 1) * spread, cy + rng.uniform(-0.4, 0.4) * spread)
    for cx, cy in BUTTERCUP_CLUMPS:
        for _ in range(rng.randint(5, 9)):
            buttercup(cx + rng.uniform(-25, 25), cy + rng.uniform(-8, 8))
    for _ in range(DAISIES):
        daisy(*anywhere())
    for _ in range(BUTTERCUPS):
        buttercup(*anywhere())
    petal, edge, centre = DAISY
    svg.open('daisies')
    svg.stroke(' '.join(stems), DAISY_STEM, 1.1, name='stems')
    svg.path(' '.join(petals), petal, edge, 0.6, name='petals')
    svg.path(' '.join(centres), centre, name='centres')
    svg.path(' '.join(cups), BUTTERCUP, name='buttercups')
    svg.close()


def rocks(svg):
    """Two pale rounded rocks half sunk in the foreground grass."""
    shade, body, lit = ROCK
    svg.open('rocks')
    for x0, x1, top, foot in ROCKS:
        w, h = x1 - x0, foot - top
        svg.open('rock')
        svg.path('M%s,%s C%s,%s %s,%s %s,%s Z' % (f(x0), f(foot), f(x0 + w * 0.05), f(top - h * 0.3),
                                                 f(x1 - w * 0.05), f(top - h * 0.3), f(x1), f(foot)), shade, name='shade')
        svg.path('M%s,%s C%s,%s %s,%s %s,%s Z' % (f(x0 + w * 0.04), f(foot - h * 0.2), f(x0 + w * 0.08), f(top - h * 0.2),
                                                 f(x1 - w * 0.2), f(top - h * 0.25), f(x1 - w * 0.12), f(foot - h * 0.3)),
                 body, name='body')
        svg.path('M%s,%s C%s,%s %s,%s %s,%s Z' % (f(x0 + w * 0.15), f(top + h * 0.35), f(x0 + w * 0.2), f(top - h * 0.05),
                                                 f(x0 + w * 0.55), f(top - h * 0.05), f(x0 + w * 0.62), f(top + h * 0.25)),
                 lit, name='sunlit top')
        foot_grass(svg, random.Random(int(x0)), (x0 + x1) / 2, foot, w * 1.2)
        svg.close()
    svg.close()


def blade(x, base, length, lean, w):
    return ('M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z'
            % (f(x - w), f(base), f(x - w * 0.3 + lean * 0.4), f(base - length * 0.55), f(x + lean), f(base - length),
               f(x + w * 0.3 + lean * 0.4), f(base - length * 0.55), f(x + w), f(base)))


def tall_grass(svg, rng):
    """Clumps of long grass blades growing up from the canvas bottom."""
    dark, light = [], []
    for x0, x1 in TALL_GRASS:
        for _ in range(int((x1 - x0) / 6)):
            x = rng.uniform(x0, x1)
            (dark if rng.random() < 0.55 else light).append(
                blade(x, HEIGHT + 4, rng.uniform(28, 62), rng.uniform(-14, 14), rng.uniform(2, 3.5)))
    svg.open('tall grass')
    svg.path(' '.join(dark), TALL_GRASS_COLOURS[0], name='blades')
    svg.path(' '.join(light), TALL_GRASS_COLOURS[1], name='lit blades')
    svg.close()



def main():
    svg = Svg()
    svg.open('Landscape')
    mountains(svg)
    lake(svg)
    hills(svg)
    grass(svg, random.Random(SEED + 3))
    svg.close()
    svg.open('Far village')
    far_village(svg)
    svg.close()
    for name, shine in zip(('Lake shimmer a', 'Lake shimmer b'), glints()):
        svg.open(name)
        svg.path(glint_shapes(shine), GLINT['colour'], name='glints', extra=' fill-opacity="%g"' % GLINT['opacity'])
        svg.close()
    svg.write(cutting.sheet_path('scenery/landscape.svg'))


def cut():
    """{'background': the landscape's image, 'far village': the meadow's, under the name the game's JSON
    already places it by, and 'shimmer a' and 'shimmer b': the lake's two sets of glints}"""
    root, grads = cutting.load('scenery/landscape.svg')
    parts = {'background': cutting.static_part('scenery/parts/landscape/background',
                                               list(cutting.find_group(root, 'Landscape')), grads, 'background'),
             'far village': cutting.static_part('scenery/parts/landscape/far-village',
                                                list(cutting.find_group(root, 'Far village')), grads, 'far village')}
    for k in 'ab':
        parts['shimmer ' + k] = cutting.static_part('scenery/parts/landscape/shimmer-' + k,
                                                    list(cutting.find_group(root, 'Lake shimmer ' + k)), grads,
                                                    'shimmer ' + k)
    return parts


def parts():
    return list(cut().values())


if __name__ == '__main__':
    main()

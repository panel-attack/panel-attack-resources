#   Writes SVG, run by `python3 -m scene_export render`: structures/windmill.svg, the Dutch tower mill on the
#   DayValley meadow's knoll: its tower (with cap and hub boss), its sails and the rail fence either side of it.
#
#   python3 -m structures.windmill  ->  windmill.svg
#
#   Everything is drawn where the first DayValley reference's mill stood on the 1536 x 1024 sheet (read off
#   panel-attack-references/DayValley/stage.png), then moved and scaled about its hub onto the meadow's knoll as
#   it is written. The sun is high to the upper right, above the frame, so the tower's left side is in shade.
#
#   A real Dutch mill's sails turn anticlockwise seen from the front. Each sail's lattice is on the trailing side
#   of its stock, the clockwise side, with a narrow leading board along the other side. The sails are one image
#   centred exactly on the hub so the scene can spin it about its centre; their stocks stop at the boss's rim, so
#   the boss drawn on the tower under them reads as in front and its highlight never turns.

import math
import os
import re

from common.painting import Svg, f, mix, poly, without_arcs
from scene_export import cutting, svgtools
from scenery.valley_reference import HILLS

HERE = os.path.dirname(os.path.abspath(__file__))
KNOLL = next(points for name, _, points in HILLS if name == 'windmill knoll')


INK = '#24223c'                  # the outline ink every face's own colour is darkened toward


LINE_DARKEN = 0.82               # outlines are the face's colour this far toward INK


LINE = 2.2                       # px, outer outlines


DETAIL_LINE = 1.2                # px, seams and inner edges


DRAWN_HUB = (1253, 558)          # sheet px the mill is drawn about: the sails' centre in the first reference
HUB = (1239, 286)                # sheet px the hub is placed at on the knoll: a whole pixel, the sails image is
                                 # centred on it
PLACE_SCALE = 1.2                # the mill drawn this much larger on the knoll than in the first reference


# ---------------------------------------------------------------- tower
TOWER_AXIS_TOP, TOWER_AXIS_FOOT = 1253.5, 1250.5     # the tower leans a hair left, as the reference's does
TOWER_TOP, TOWER_FOOT = 581, 709       # the foot runs a little into the ground
TOWER_TOP_HALF, TOWER_FOOT_HALF = 17.5, 33.5
BRICK = {'lit': '#ecdcc6', 'body': '#e2d0bb', 'shade': '#c8b29b', 'deep': '#ae9680'}
MORTAR = '#d6c3ab'
COURSE = 5.2                     # px between brick courses
BRICK_LENGTH = 9.0               # px, a brick's length at the tower's top; bricks widen with the taper
LIT_SHARE, SHADE_SHARE = 0.26, 0.3     # of the tower's width: the sunlit strip on the right, the shade on the left
LIT_STRIP, SHADE_STRIP = (1 - LIT_SHARE, 1), (0, SHADE_SHARE)   # each as shares across from the tower's left edge
PLINTH = 4                       # px, the stone footing course at the foot
PLINTH_STONE = '#b8aa98'

# ---------------------------------------------------------------- gallery (the stage round the tower)
GALLERY_RAIL_Y, GALLERY_DECK_Y, GALLERY_FOOT_Y = 636.5, 643.5, 650.5
GALLERY_HALF = 27.5
GALLERY_POSTS = 8
WOOD = {'lit': '#c47c46', 'body': '#ad6534', 'deck': '#8a4632', 'shade': '#844724', 'deep': '#5e2e16'}

# ---------------------------------------------------------------- window and door
WINDOW = (1251.5, 617.5, 1251.5, 631.5, 4.6)   # centre x, arch top y, centre x, sill y, half width
GLOW = ('#fffbe0', '#f8dc6a')    # pane, centre to edge
GLOW_HALO = '#ffe680'
DOOR = (1240.0, 680.5, 1261.5, TOWER_FOOT)     # x0, arch top y, x1, foot y: its sill on the tower's floor

# ---------------------------------------------------------------- cap and boss
CAP_CENTRE = (1253.0, 562.5)
CAP_RX, CAP_RY = 25.5, 22.5
CAP_FOOT = 579.5                 # the cap's flat bottom, on the gold curb
CAP = {'lit': '#c47436', 'body': '#9a5028', 'shade': '#843f26', 'deep': '#5a2a18'}
CURB = (1231.0, 579.0, 1276.5, 582.5)          # the gold curb ring the cap turns on: x0, y0, x1, y1
GOLD = {'lit': '#fff6a8', 'body': '#ffdc26', 'curb': '#f0aa14', 'shade': '#d08a0e', 'deep': '#a86a08'}
BOSS_R = 9.5

# ---------------------------------------------------------------- sails
SAIL_ANGLES = (-135, -45, 45, 135)   # degrees on screen (y down), each stock's direction from the hub
STOCK_HALF = 2.2                 # px, half the stock's width
STOCK_END = 97.0                 # px from the hub to a stock's tip
LATTICE_FROM, LATTICE_TO = 23.0, 92.0   # px from the hub along the stock
LATTICE_WIDTH = 18.5             # px, from the stock's side to the lattice's outer edge
LATTICE_CELLS = (7, 2)           # cells along the sail, across it
LEADING_FROM, LEADING_WIDTH = 30.0, 2.4
SAIL_CLOTH = ('#fffaf4', '#f3e8de')    # the cells: lit, and the shade under each bar
SAIL_WOOD = {'lit': '#e8b496', 'body': '#9a5040', 'shade': '#5c2414', 'lattice': '#703018'}

# ---------------------------------------------------------------- fence
# the runs either side of the tower, mirrored about its axis: (sheet px from the axis to the nearest post, to the
# farthest, posts). Their posts stand evenly spaced along the knoll, their feet FENCE_SINK below its top edge, so
# the fence follows the ground over the rise, and its rails run post to post.
FENCE = (54.0, 170.0, 6)
FENCE_SINK = 6.0                 # sheet px below the knoll's top edge each post's foot stands
FENCE_POST = 14.0                # sheet px from a post's foot to its top
POST_HALF = 2.6
RAIL_AT = (0.28, 0.78)             # each rail's height up the post, as a share from the top
RAIL_HALF = 1.5
FENCE_WOOD = {'lit': '#ad7656', 'body': '#8c5638', 'shade': '#6a3c26'}


def placed(x, y):
    """Where a point drawn on the first reference's sheet lands on the knoll."""
    return (HUB[0] + (x - DRAWN_HUB[0]) * PLACE_SCALE, HUB[1] + (y - DRAWN_HUB[1]) * PLACE_SCALE)


def placed_path(d):
    """An absolute path of M, L, C, Q and Z commands (no arcs, no H or V) with every point placed."""
    tokens = re.findall(r'[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?', d)
    out, nums = [], []
    for token in tokens:
        if token.isalpha():
            assert token in 'MLCQZ', 'cannot place a %r command' % token
            out.append(token)
            continue
        nums.append(float(token))
        if len(nums) == 2:
            x, y = placed(*nums)
            out.append('%s,%s' % (f(x), f(y)))
            nums = []
    return re.sub(r'([A-Z]) ', r'\1', ' '.join(out))


def unplaced(x, y):
    """Where a point on the knoll is drawn on the first reference's sheet."""
    return (DRAWN_HUB[0] + (x - HUB[0]) / PLACE_SCALE, DRAWN_HUB[1] + (y - HUB[1]) / PLACE_SCALE)


def knoll_top(x):
    for (x0, y0), (x1, y1) in zip(KNOLL, KNOLL[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    raise ValueError('x %s is off the knoll' % x)


def fence_posts(first, last, count):
    """[((x, foot), top)] drawn px: count posts spaced evenly from sheet x first to last, standing on the knoll."""
    out = []
    for k in range(count):
        x = first + (last - first) * k / (count - 1)
        foot = knoll_top(x) + FENCE_SINK
        (dx, dfoot), (_, dtop) = unplaced(x, foot), unplaced(x, foot - FENCE_POST)
        out.append(((dx, dfoot), dtop))
    return out


def fence_runs():
    """{'left fence': posts, 'right fence': posts}, each run's posts left to right."""
    axis = placed(TOWER_AXIS_FOOT, TOWER_FOOT)[0]
    near, far, count = FENCE
    return {'left fence': fence_posts(axis - far, axis - near, count),
            'right fence': fence_posts(axis + near, axis + far, count)}


FENCE_RUNS = fence_runs()


class PlacedSvg(Svg):
    """An Svg that places everything drawn in it onto the knoll, outlines and gradients scaled with it."""

    def paint(self, fill):
        if isinstance(fill, tuple) and len(fill) == 4:
            fill = fill[:2] + tuple(placed(DRAWN_HUB[0], y)[1] for y in fill[2:])
        return super().paint(fill)

    def path(self, d, fill, line=None, width=0, name=None, extra=''):
        super().path(placed_path(without_arcs(d)), fill, line, width * PLACE_SCALE, name, extra)

    def stroke(self, d, colour, width, name=None):
        super().stroke(placed_path(without_arcs(d)), colour, width * PLACE_SCALE, name)


def line_of(fill):
    return mix(fill, INK, LINE_DARKEN)


def tower_half(y):
    t = (y - TOWER_TOP) / (TOWER_FOOT - TOWER_TOP)
    return TOWER_TOP_HALF + (TOWER_FOOT_HALF - TOWER_TOP_HALF) * t


def tower_x(y, share):
    """The x a share of the tower's width across from its left edge, at height y."""
    h = tower_half(y)
    axis = TOWER_AXIS_TOP + (TOWER_AXIS_FOOT - TOWER_AXIS_TOP) * (y - TOWER_TOP) / (TOWER_FOOT - TOWER_TOP)
    return axis - h + 2 * h * share


def strip(y0, y1, s0, s1):
    return [(tower_x(y0, s0), y0), (tower_x(y0, s1), y0), (tower_x(y1, s1), y1), (tower_x(y1, s0), y1)]


def arch(x0, top, x1, foot, steps=8):
    """An arched opening's outline: straight sides, a round head."""
    r = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    head = [(cx - r * math.cos(math.pi * k / steps), top + r - r * math.sin(math.pi * k / steps))
            for k in range(steps + 1)]
    return [(x0, foot)] + head + [(x1, foot)]


def ellipse(cx, cy, rx, ry):
    return 'M%s,%s A%s,%s 0 1,0 %s,%s A%s,%s 0 1,0 %s,%s Z' % (
        f(cx - rx), f(cy), f(rx), f(ry), f(cx + rx), f(cy), f(rx), f(ry), f(cx - rx), f(cy))


def circle(cx, cy, r):
    return ellipse(cx, cy, r, r)


# ================================================================ tower

def tower_body(svg):
    svg.open('wall')
    outline = strip(TOWER_TOP, TOWER_FOOT, 0, 1)
    svg.path(poly(outline), BRICK['body'], name='wall body')
    svg.path(poly(strip(TOWER_TOP, TOWER_FOOT, *LIT_STRIP)), BRICK['lit'], name='wall lit')
    svg.path(poly(strip(TOWER_TOP, TOWER_FOOT, *SHADE_STRIP)), BRICK['shade'], name='wall shade')
    svg.path(poly(strip(TOWER_TOP, TOWER_FOOT, 0, SHADE_SHARE * 0.35)), BRICK['deep'], name='wall deep shade',
             extra=' fill-opacity="0.55"')
    courses(svg)
    plinth(svg)
    for h, alpha in ((4, 0.22), (8, 0.12)):     # the cap's shadow under the curb
        svg.path(poly(strip(TOWER_TOP, TOWER_TOP + h, 0, 1)), INK, name='cap shadow', extra=' fill-opacity="%s"' % alpha)
    svg.path(poly(outline), 'none', line_of(BRICK['shade']), LINE, name='wall outline')
    svg.close()


def courses(svg):
    """Brick courses: mortar lines round the tower, the bricks' joints staggered course to course."""
    svg.open('brick courses')
    y = TOWER_TOP + COURSE
    row = 0
    while y < TOWER_FOOT - PLINTH - 1:
        if not (GALLERY_RAIL_Y - 2 < y < GALLERY_FOOT_Y + 2):
            svg.stroke('M%s,%s L%s,%s' % (f(tower_x(y, 0) + 0.8), f(y), f(tower_x(y, 1) - 0.8), f(y)),
                       MORTAR, 0.7, name='course')
        top = y - COURSE
        n = max(3, round(2 * tower_half(y) / (BRICK_LENGTH * tower_half(y) / TOWER_TOP_HALF * 0.82)))
        for k in range(n + 1):
            share = (k + (0.5 if row % 2 else 0.0)) / n
            if not 0.04 < share < 0.96:
                continue
            if GALLERY_RAIL_Y - 2 < y < GALLERY_FOOT_Y + 8:
                continue
            svg.stroke('M%s,%s L%s,%s' % (f(tower_x(top, share)), f(top + 0.4), f(tower_x(y, share)), f(y - 0.4)),
                       MORTAR, 0.6, name='joint')
        y += COURSE
        row += 1
    svg.close()


def plinth(svg):
    y0 = TOWER_FOOT - PLINTH
    svg.path(poly(strip(y0, TOWER_FOOT, 0, 1)), PLINTH_STONE, line_of(PLINTH_STONE), DETAIL_LINE, name='plinth')
    svg.path(poly(strip(y0, TOWER_FOOT, *SHADE_STRIP)), mix(PLINTH_STONE, INK, 0.2), name='plinth shade')
    for share in (0.12, 0.3, 0.5, 0.7, 0.88):
        svg.stroke('M%s,%s L%s,%s' % (f(tower_x(y0, share)), f(y0 + 0.6), f(tower_x(TOWER_FOOT, share)),
                                      f(TOWER_FOOT - 0.6)), mix(PLINTH_STONE, INK, 0.35), 0.6, name='plinth joint')


def window(svg):
    """A small oval window lit from inside: a white-hot core, a yellow rim, a wooden frame."""
    cx, top, _, sill, half = WINDOW
    cy, ry = (top + sill) / 2, (sill - top) / 2
    svg.open('window')
    svg.path(ellipse(cx, cy, half * 1.9, ry * 1.3), GLOW_HALO, name='window glow', extra=' fill-opacity="0.2"')
    svg.path(ellipse(cx, cy, half + 1.5, ry + 1.5), WOOD['body'], line_of(WOOD['body']), DETAIL_LINE,
             name='window frame')
    svg.path(ellipse(cx, cy, half, ry), GLOW[1], name='window pane')
    svg.path(ellipse(cx, cy + 0.6, half * 0.62, ry * 0.7), GLOW[0], name='window core')
    svg.path(ellipse(cx, cy + 1.2, half * 0.3, ry * 0.4), '#ffffff', name='window flame')
    svg.close()


def door(svg):
    x0, top, x1, foot = DOOR
    svg.open('door')
    svg.path(poly(arch(x0 - 1.6, top - 1.6, x1 + 1.6, foot)), mix(BRICK['deep'], INK, 0.15), name='door reveal')
    leaf = arch(x0, top, x1, foot)
    svg.path(poly(leaf), WOOD['body'], line_of(WOOD['body']), DETAIL_LINE, name='door leaf')
    w = x1 - x0
    split = x1 - w * 0.32
    head = top + w / 2 - math.sqrt((w / 2) ** 2 - (split - (x0 + x1) / 2) ** 2)
    svg.path(poly([(split, foot), (split, head)] + [p for p in leaf if p[0] > split]), WOOD['lit'], name='door lit',
             extra=' fill-opacity="0.6"')
    for k in (1, 2, 3):
        x = x0 + w * k / 4
        r = w / 2
        dx = x - (x0 + r)
        y = top + r - math.sqrt(max(0.0, r * r - dx * dx)) + 0.6
        svg.stroke('M%s,%s L%s,%s' % (f(x), f(y), f(x), f(foot - 0.3)), WOOD['shade'], 0.7, name='door plank')
    for y in (top + w * 0.55, foot - 6.5):
        svg.path(poly([(x0 + 0.6, y), (x1 - 0.6, y), (x1 - 0.6, y + 1.6), (x0 + 0.6, y + 1.6)]), '#3b3550', name='hinge')
    svg.path(circle(x0 + 3.8, foot - 12.5, 1.1), GOLD['body'], GOLD['deep'], 0.5, name='door knob')
    svg.close()


def gallery(svg):
    """The stage: a plank deck round the tower on brackets, with a railing of posts."""
    svg.open('gallery')
    mid = (tower_x(GALLERY_DECK_Y, 0) + tower_x(GALLERY_DECK_Y, 1)) / 2
    x0, x1 = mid - GALLERY_HALF, mid + GALLERY_HALF
    svg.path(poly([(x0, GALLERY_RAIL_Y), (x1, GALLERY_RAIL_Y), (x1, GALLERY_DECK_Y), (x0, GALLERY_DECK_Y)]),
             BRICK['lit'], name='railing back')
    for k in range(GALLERY_POSTS):
        x = x0 + 1.6 + (x1 - x0 - 3.2) * k / (GALLERY_POSTS - 1)
        tone = WOOD['shade'] if k < GALLERY_POSTS * 0.3 else WOOD['body']
        svg.path(poly([(x - 1.1, GALLERY_RAIL_Y), (x + 1.1, GALLERY_RAIL_Y), (x + 1.1, GALLERY_DECK_Y),
                       (x - 1.1, GALLERY_DECK_Y)]), tone, line_of(tone), 0.6, name='baluster')
    svg.path(poly([(x0 - 1, GALLERY_RAIL_Y - 1.2), (x1 + 1, GALLERY_RAIL_Y - 1.2), (x1 + 1, GALLERY_RAIL_Y + 0.9),
                   (x0 - 1, GALLERY_RAIL_Y + 0.9)]), WOOD['body'], WOOD['shade'], 0.7, name='hand rail')
    deck = [(x0 - 2, GALLERY_DECK_Y), (x1 + 2, GALLERY_DECK_Y), (x1 + 2, GALLERY_FOOT_Y), (x0 - 2, GALLERY_FOOT_Y)]
    svg.path(poly(deck), WOOD['deck'], name='deck')
    svg.path(poly([(x0 - 2, GALLERY_DECK_Y), (x1 + 2, GALLERY_DECK_Y), (x1 + 2, GALLERY_DECK_Y + 2),
                   (x0 - 2, GALLERY_DECK_Y + 2)]), WOOD['lit'], name='deck edge lit')
    svg.path(poly([(x0 - 2, GALLERY_DECK_Y), (x0 + 18, GALLERY_DECK_Y), (x0 + 18, GALLERY_FOOT_Y),
                   (x0 - 2, GALLERY_FOOT_Y)]), WOOD['shade'], name='deck shade', extra=' fill-opacity="0.6"')
    for k in range(1, 12):
        x = x0 - 2 + (x1 - x0 + 4) * k / 12
        svg.stroke('M%s,%s L%s,%s' % (f(x), f(GALLERY_DECK_Y + 2.4), f(x), f(GALLERY_FOOT_Y - 0.4)), WOOD['shade'],
                   0.5, name='plank end')
    svg.path(poly(deck), 'none', line_of(WOOD['body']), DETAIL_LINE, name='deck outline')
    svg.close()


def cap(svg):
    """The turning cap: a round wooden hood of boards on its gold curb, the hub boss in front."""
    svg.open('cap')
    cx, cy = CAP_CENTRE
    cut = (CAP_FOOT - cy) / CAP_RY
    a0 = math.asin(min(1.0, cut))
    n = 28
    hood = []
    for k in range(n + 1):
        a = math.pi - a0 + (math.pi + 2 * a0) * k / n
        hood.append((cx + CAP_RX * math.cos(a), cy + CAP_RY * math.sin(a)))
    svg.path(poly(hood), (CAP['body'], CAP['lit'], cy - CAP_RY, CAP_FOOT), name='hood')
    shade = [(cx - CAP_RX * 0.45 * math.cos(a), cy + CAP_RY * math.sin(a)) for a in
             [-math.pi / 2 + (math.pi / 2 + a0) * k / 14 for k in range(15)]]
    rim = [(cx - CAP_RX * math.cos(a), cy + CAP_RY * math.sin(a)) for a in
           [a0 - (math.pi / 2 + a0) * k / 14 for k in range(15)]]
    svg.path(poly(shade + rim), CAP['shade'], name='hood shade')
    for level in (0.2, 0.42, 0.62, 0.8):          # plank seams running round the hood
        y = cy - CAP_RY + (CAP_FOOT - cy + CAP_RY) * level
        half = CAP_RX * math.sqrt(max(0.0, 1 - ((y - cy) / CAP_RY) ** 2)) - 1.2
        dip = 1.2 + 2.0 * level
        svg.stroke('M%s,%s Q%s,%s %s,%s' % (f(cx - half), f(y), f(cx), f(y + dip), f(cx + half), f(y)), CAP['deep'], 0.7,
                   name='plank seam')
    svg.path(poly(hood), 'none', line_of(CAP['body']), LINE, name='hood outline')
    x0, y0, x1, y1 = CURB
    curb = [(x0, y0), (x1, y0), (x1 - 1, y1), (x0 + 1, y1)]
    svg.path(poly(curb), GOLD['curb'], line_of(GOLD['shade']), DETAIL_LINE, name='curb')
    svg.path(poly([(x0 + 1, y0 + 0.8), (x1 - 1, y0 + 0.8), (x1 - 1, y0 + 2), (x0 + 1, y0 + 2)]), GOLD['body'],
             name='curb lit')
    svg.path(poly([(x0 + 12, y0 + 0.6), (x0 + 0.6, y0 + 0.6), (x0 + 1.4, y1 - 0.6), (x0 + 12, y1 - 0.6)]),
             GOLD['shade'], name='curb shade')
    svg.path(circle(x1 + 1.5, y0 - 0.5, 2.6), GOLD['body'], line_of(GOLD['shade']), DETAIL_LINE, name='brake knob')
    svg.close()
    boss(svg)


def boss(svg):
    hx, hy = DRAWN_HUB
    svg.open('boss')
    svg.path(circle(hx - 0.8, hy + 1.2, BOSS_R + 1.2), INK, name='boss shadow', extra=' fill-opacity="0.25"')
    svg.path(circle(hx, hy, BOSS_R), (GOLD['lit'], GOLD['shade'], hy - BOSS_R, hy + BOSS_R), line_of(GOLD['shade']),
             LINE, name='boss')
    svg.path(circle(hx, hy, BOSS_R * 0.55), GOLD['body'], GOLD['shade'], 0.6, name='boss nose')
    svg.path(ellipse(hx + 2.6, hy - 3.0, 2.4, 1.6), '#fffbe0', name='boss highlight')
    svg.close()


def tower(svg):
    svg.open('windmill tower')
    tower_body(svg)
    window(svg)
    door(svg)
    gallery(svg)
    cap(svg)
    svg.close()


# ================================================================ sails

def sail(svg, angle):
    """One sail: the stock from the boss's rim out, the lattice on its clockwise (trailing) side, the leading
    board on the other."""
    hx, hy = DRAWN_HUB
    a = math.radians(angle)
    u = (math.cos(a), math.sin(a))
    n = (-u[1], u[0])            # clockwise of u on screen

    def at(r, s):
        return hx + u[0] * r + n[0] * s, hy + u[1] * r + n[1] * s

    svg.open('sail %d' % angle)
    s0, s1 = STOCK_HALF, STOCK_HALF + LATTICE_WIDTH
    frame = [at(LATTICE_FROM, s0), at(LATTICE_TO, s0), at(LATTICE_TO, s1), at(LATTICE_FROM, s1)]
    svg.path(poly(frame), SAIL_CLOTH[0], name='cloth')
    along, across = LATTICE_CELLS
    bar = 1.5
    for j in range(1, across):
        s = s0 + (s1 - s0) * j / across
        svg.path(poly([at(LATTICE_FROM, s - bar / 2), at(LATTICE_TO, s - bar / 2), at(LATTICE_TO, s + bar / 2),
                       at(LATTICE_FROM, s + bar / 2)]), SAIL_WOOD['lattice'], name='lath')
    for i in range(1, along):
        r = LATTICE_FROM + (LATTICE_TO - LATTICE_FROM) * i / along
        svg.path(poly([at(r - bar / 2, s0), at(r + bar / 2, s0), at(r + bar / 2, s1), at(r - bar / 2, s1)]),
                 SAIL_WOOD['lattice'], name='sail bar')
    svg.path(poly(frame), 'none', SAIL_WOOD['lattice'], 2.4, name='lattice frame')
    svg.path(poly([at(LATTICE_FROM - 1.1, s0 - 0.2), at(LATTICE_TO + 1.1, s0 - 0.2), at(LATTICE_TO + 1.1, s1 + 1.1),
                   at(LATTICE_FROM - 1.1, s1 + 1.1)]), 'none', mix(SAIL_WOOD['lattice'], INK, 0.5), DETAIL_LINE,
             name='lattice outline')
    lead = [at(LEADING_FROM, -STOCK_HALF), at(LATTICE_TO, -STOCK_HALF), at(LATTICE_TO, -STOCK_HALF - LEADING_WIDTH),
            at(LEADING_FROM + 4, -STOCK_HALF - LEADING_WIDTH)]
    svg.path(poly(lead), SAIL_WOOD['body'], mix(SAIL_WOOD['body'], INK, 0.5), 0.6, name='leading board')
    tip = STOCK_END
    stock = [at(BOSS_R - 1, -STOCK_HALF), at(tip - 1.2, -STOCK_HALF), at(tip, -STOCK_HALF * 0.6),
             at(tip, STOCK_HALF * 0.6), at(tip - 1.2, STOCK_HALF), at(BOSS_R - 1, STOCK_HALF)]
    svg.path(poly(stock), SAIL_WOOD['body'], line_of(SAIL_WOOD['body']), DETAIL_LINE, name='stock')
    svg.stroke(poly([at(BOSS_R, -STOCK_HALF * 0.35), at(tip - 1.5, -STOCK_HALF * 0.35)], close=False),
               SAIL_WOOD['lit'], 1.0, name='stock sheen')
    svg.close()


def sails(svg):
    svg.open('windmill sails')
    for angle in SAIL_ANGLES:
        sail(svg, angle)
    svg.close()


# ================================================================ fence

def fence_run(svg, name, posts):
    svg.open(name)
    for share in RAIL_AT:
        for ((xa, fa), ta), ((xb, fb), tb) in zip(posts, posts[1:]):
            ya, yb = ta + (fa - ta) * share, tb + (fb - tb) * share
            rail = [(xa, ya - RAIL_HALF), (xb, yb - RAIL_HALF), (xb, yb + RAIL_HALF), (xa, ya + RAIL_HALF)]
            svg.path(poly(rail), FENCE_WOOD['body'], line_of(FENCE_WOOD['body']), DETAIL_LINE, name='rail')
            svg.stroke('M%s,%s L%s,%s' % (f(xa + 0.6), f(ya - RAIL_HALF + 0.6), f(xb - 0.6), f(yb - RAIL_HALF + 0.6)),
                       FENCE_WOOD['lit'], 0.7, name='rail sheen')
    for (x, foot), top in posts:
        body = [(x - POST_HALF, foot), (x - POST_HALF, top + 1.4), (x - POST_HALF * 0.55, top),
                (x + POST_HALF * 0.55, top), (x + POST_HALF, top + 1.4), (x + POST_HALF, foot)]
        svg.path(poly(body), FENCE_WOOD['body'], name='post')
        svg.path(poly([(x - POST_HALF * 0.2, foot), (x - POST_HALF * 0.2, top + 0.6), (x - POST_HALF * 0.55, top),
                       (x - POST_HALF, top + 1.4), (x - POST_HALF, foot)]), FENCE_WOOD['shade'], name='post shade')
        svg.stroke('M%s,%s L%s,%s' % (f(x + POST_HALF * 0.5), f(top + 1.6), f(x + POST_HALF * 0.5), f(foot - 1)),
                   FENCE_WOOD['lit'], 0.7, name='post sheen')
        svg.path(poly(body), 'none', line_of(FENCE_WOOD['body']), DETAIL_LINE, name='post outline')
    svg.close()


def fence(svg):
    svg.open('windmill fence')
    for name, posts in FENCE_RUNS.items():
        fence_run(svg, name, posts)
    svg.close()


def main():
    svg = PlacedSvg()
    svg.open('windmill')
    fence(svg)
    tower(svg)
    sails(svg)
    svg.close()
    svg.write(cutting.sheet_path('structures/windmill.svg'))


def sails_part(path, group, grads, name):
    """The sails as one image whose centre is exactly the hub, for a "center" anchor and pivot."""
    box = svgtools.stem_box(svgtools.element_bbox(group), HUB, cutting.PAD)
    return cutting.Part(path, svgtools.part_svg(name, [group], grads, box), box)


def cut():
    """[(template id, its image)]: the tower, the sails, the fence."""
    root, grads = cutting.load('structures/windmill.svg')
    out = []
    for gid, tid in (('windmill tower', 'windmill-tower'), ('windmill fence', 'windmill-fence')):
        name = tid.partition('-')[2]
        out.append((tid, cutting.static_part('structures/parts/windmill/' + name, [cutting.find_group(root, gid)],
                                             grads, tid)))
    out.insert(1, ('windmill-sails', sails_part('structures/parts/windmill/sails',
                                                cutting.find_group(root, 'windmill sails'), grads, 'windmill-sails')))
    return out


def parts():
    return [part for _, part in cut()]


if __name__ == '__main__':
    main()

#   Writes SVG, run by `python3 -m scene_export render`: plants/blossom.svg, the train meadow's pink blossom tree
#   framing the left of the scene: a thick brown trunk rising at the left edge, its foot hidden under the meadow,
#   leaning right and forking into limbs that spread up and right across the top of the frame under clumps of big
#   five-petal blossom, and a few loose clusters hanging from the ends of twigs so the scene can sway them. The bark
#   is outlined; the blossoms are not, each edged only in a darker pink.
#
#   python3 -m plants.blossom  ->  blossom.svg
#
#   Everything is drawn where it sits on the sheet, past the left and top edges. Measurements are sheet px off
#   TrainMeadow/stage.png; light comes from the upper right, so the trunk is lit down its right side and the
#   blossoms' lower-left petals are the deep pink.

import math
import os

from common.painting import Svg, f, mix, poly
from plants.broadleaf import limb
from scene_export import cutting, svgtools

HERE = os.path.dirname(os.path.abspath(__file__))


MEADOW = 600                     # sheet y the meadow's grass hides the trunk's foot below


CROWN_REACH = 560                # sheet x the blossom reaches across the top of the frame


# the bark's outline is a dark shade of its own warm brown, as the Esme terrace outlines every shape, not a purple
BARK = {'line': '#6b3a28', 'shade': '#74405c', 'body': '#cc7152', 'lit': '#f09050'}


# the limbs up in the crown are mostly in its shade: their body and lit colours
UPPER_BARK = {'body': '#954f56', 'lit': '#b8665a'}


UPPER = ('top limb', 'top left limb', 'top twig', 'edge twig')


BARK_LINE = 2.5                  # px, the outline round the trunk and every limb, the Esme leaves' width


# the trunk and its limbs, each a polyline of sheet points with a half width at each point, named so a twig can be
# found by the cluster hanging from it, back to front: the twigs furthest back, then the limbs, then the trunk in front
# of them all, so each limb's shade and lit strip stop where the trunk or a nearer limb covers them. The trunk's foot
# stands well under the meadow; its top and the left limb's end and the top limb's tip run off the edges of the sheet.
LIMBS = {
    'top twig': ([(340, 165), (350, 200)], [6, 4]),
    'edge twig': ([(520, 84), (532, 102), (538, 118)], [6, 5, 4]),
    'top limb': ([(165, 212), (245, 185), (330, 160), (410, 135), (485, 95), (560, 62), (610, 40)],
                 [22, 17, 14, 11, 9, 7, 6]),
    'fork limb': ([(240, 216), (265, 194), (292, 174)], [13, 11, 9]),
    'right limb': ([(140, 236), (178, 229), (215, 222), (250, 215), (266, 222), (278, 238), (294, 253), (318, 258)],
                   [24, 21, 18, 15, 12, 9.5, 7, 5]),
    'top left limb': ([(128, 245), (100, 190), (80, 140), (65, 90), (55, 40)], [28, 24, 19, 15, 12]),
    'left limb': ([(95, 300), (40, 265), (0, 245), (-50, 225)], [34, 30, 26, 22]),
    'trunk': ([(50, 670), (52, 580), (47, 500), (60, 400), (76, 340), (95, 290), (128, 250), (152, 200), (181, 140),
               (200, 90), (218, 30), (228, -10)],
              [60, 57, 50, 46, 38, 40, 44, 26, 17, 13, 11, 10]),
}


# the crotches where limbs leave the trunk and the right limb forks, each the limb edges met in turn round it,
# (limb, side): 'lit' is the side the limb's lit strip runs down, 'shade' the other. Each is filled out to a curve so
# the bark flows from one edge round into the next instead of meeting it in a corner; the right limb is flared above
# and below where it grows out of the trunk's lit side, and its fork is flared under the limb that leaves it
CROTCHES = [
    (('left limb', 'shade'), ('trunk', 'shade')),
    (('left limb', 'lit'), ('trunk', 'shade'), ('top left limb', 'shade')),
    (('right limb', 'lit'), ('trunk', 'lit')),
    (('right limb', 'shade'), ('trunk', 'lit')),
    (('fork limb', 'shade'), ('right limb', 'lit')),
]


FLARE = 36                       # px, how far along each edge from the crotch's corner its curve starts, at most


SHADED = ('trunk', 'left limb', 'top limb', 'top left limb', 'right limb', 'fork limb')   # wide enough for a shade strip


LIT = ('trunk', 'left limb', 'top limb', 'right limb', 'fork limb')      # ... and for a lit strip down their lit side


# the bark is shaded in facets: the lit strip starts this far across the half width at each point along a limb in
# turn, so its inner edge breaks at every bend into planes instead of running a parallel stripe...
LIT_FACETS = (0.45, 0.25, 0.55, 0.35)


# ... and the shade covers this share of the half width from the outline in at each point in turn
SHADE_FACETS = (0.35, 0.25, 0.42, 0.3)


LIT_TO = 0.92                    # the lit strip stops this far across the half width, short of the outline


# dark streaks of bark down the trunk's face, each a polyline of sheet points with a half width at each
STREAKS = [([(70, 560), (62, 520), (58, 470)], [2.5, 2.5, 1.5]), ([(92, 330), (104, 300), (118, 270)], [2, 2, 1.5]),
           ([(40, 445), (44, 410)], [1.5, 1.5]), ([(150, 215), (165, 180)], [1.5, 1.5])]


# the blossoms have no dark line: each is edged in a pink a shade darker than its body, so where petals of one
# blossom lie over another's only the colour change parts them, and the clumps' edges are bare petal against the sky
PETAL = {'edge': '#e366a4', 'deep': '#f474b8', 'body': '#fb8ebb', 'pale': '#ffd1d8', 'pale deep': '#fbbccb',
         'centre': '#ffdbbc', 'heart': '#f6b060'}


BACK = '#d85cbc'                # the shaded blossoms behind the front layer, their body


BACK_EDGE = '#b8449f'            # ... each edged in a darker shade of that magenta, so the slivers that show read as petals


BACK_PALE = '#e27bcc'            # ... and a lighter inner part on each petal


BACK_SEAL = 4.5                  # px, the back mass is stroked in its own colour this far so no chink shows between its petals


PETAL_EDGE = 2.0                 # px, the darker pink edge round each blossom


BUD = {'body': '#cd83d2', 'pale': '#e9b0e4'}


PALE = 0.72                      # a petal's pale inner part as a share of the petal, centred on the blossom with it


PETAL_DISC = 0.85                # a blossom covers this share of its reach but for the notches between its petal tips


EXPOSED = 0.12                   # the share of the back mass the front blossoms may leave uncovered, by PETAL_DISC


DEEP_PETALS = 1                  # every blossom's petals facing furthest from the light are the deep pink, this many


LIGHT = (0.707, -0.707)          # unit direction toward the light, the upper right


# the crown's blossoms, back to front, each (x, y, radius, turn in degrees) on the sheet; split at CROWN_SPLIT into
# the left clump over the trunk's top and the right clump along the top limb
CROWN = [
    (-15, 95, 80, 10), (75, 30, 76, 40), (45, 170, 70, -15), (140, 115, 68, 25), (25, 228, 44, 30),
    (215, 35, 74, 30), (215, 150, 52, 10), (100, 222, 38, -20), (150, 195, 42, 55), (255, 198, 36, -30),
    (285, 120, 72, -20), (298, 58, 44, -5), (385, 55, 76, 15), (365, 150, 54, 30), (475, 125, 84, 0),
    (550, 40, 70, -10), (560, 185, 60, 30), (500, 208, 42, -15), (440, 215, 44, 20),
]


# the shaded blossoms behind the front layer, closing its gaps: the same (x, y, radius, turn), by clump
BACK_CROWN = [
    (30, 215, 50, 20), (0, 150, 60, 50), (100, 190, 48, 0), (200, 120, 56, 10), (230, 170, 44, 40),
    (330, 110, 52, 25), (380, 165, 50, -10), (430, 190, 44, 30), (510, 190, 46, 10), (300, 60, 40, 0),
]


CROWN_SPLIT = 270                # blossoms centred left of this are the left clump


CROWN_LEFT = [b for b in CROWN if b[0] < CROWN_SPLIT]


CROWN_RIGHT = [b for b in CROWN if b[0] >= CROWN_SPLIT]


BACK_LEFT = [b for b in BACK_CROWN if b[0] < CROWN_SPLIT]


BACK_RIGHT = [b for b in BACK_CROWN if b[0] >= CROWN_SPLIT]


# the loose clusters hanging from twig ends, each a template whose anchor and pivot are where it hangs (a whole
# pixel): the twig it hangs from, its blossoms as (dx, dy, radius, turn) and buds as (dx, dy, radius) off that
CLUSTERS = {
    'blossom-cluster-branch': dict(twig='right limb', hang=(318, 258),
                                   blossoms=[(14, 4, 40, 20)], buds=[(-10, 24, 9)]),
    'blossom-cluster-top': dict(twig='top twig', hang=(350, 200),
                                blossoms=[(8, 28, 40, -25)], buds=[]),
    'blossom-cluster-edge': dict(twig='edge twig', hang=(538, 118),
                                 blossoms=[], buds=[(0, 10, 11)]),
}


def circle(x, y, r):
    return 'M%s,%s A%s,%s 0 1,0 %s,%s A%s,%s 0 1,0 %s,%s Z' % (f(x - r), f(y), f(r), f(r), f(x + r), f(y), f(r), f(r),
                                                              f(x - r), f(y))


def square(x, y, half, turn):
    """A square of that half side about (x, y), turned by turn degrees."""
    a = math.radians(turn)
    return poly([(x + half * math.cos(a + k * math.pi / 2) * math.sqrt(2), y + half * math.sin(a + k * math.pi / 2)
                  * math.sqrt(2)) for k in range(4)])


def petal(x, y, r, angle, size=1.0, shift=(0, 0)):
    """One petal of reach r from (x, y) pointing along angle (degrees, y down): a rounded blade with a notch at its
    tip, sized about the flower's centre and shifted by shift (shares of r)."""
    length, width = r * size, r * 0.8 * size
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    ox, oy = x + shift[0] * r, y + shift[1] * r

    def at(u, v):
        return f(ox + u * ca - v * sa), f(oy + u * sa + v * ca)
    pts = [at(0.1 * length, 0), at(0.0, -0.72 * width), at(0.85 * length, -0.62 * width), at(length, -0.14 * width),
           at(0.88 * length, 0), at(length, 0.14 * width), at(0.85 * length, 0.62 * width), at(0.0, 0.72 * width)]
    return ('M%s,%s C%s,%s %s,%s %s,%s L%s,%s L%s,%s C%s,%s %s,%s %s,%s Z'
            % (pts[0] + pts[1] + pts[2] + pts[3] + pts[4] + pts[5] + pts[6] + pts[7] + pts[0]))


def petal_angles(turn):
    return [-90 + turn + 72 * k for k in range(5)]


def petals(x, y, r, turn):
    """The five petals of a blossom as one path."""
    return ' '.join(petal(x, y, r, a) for a in petal_angles(turn))


def flower(svg, x, y, r, turn):
    """A five-petal blossom of reach r centred on (x, y), edged in the darker pink, its lower-left petal the deep
    pink, every petal pale over most of its length (the deep one a deeper pale) so the pale ring is centred on the
    small cream centre and its heart."""
    angles, deep = petal_angles(turn), deep_angles(turn)
    all_petals = petals(x, y, r, turn)
    svg.path(all_petals, PETAL['edge'], PETAL['edge'], PETAL_EDGE * 2, name='blossom edge')
    svg.path(all_petals, PETAL['body'], name='blossom')
    svg.path(' '.join(petal(x, y, r, a) for a in deep), PETAL['deep'], name='blossom deep')
    svg.path(' '.join(petal(x, y, r, a, PALE) for a in angles if a not in deep), PETAL['pale'], name='blossom pale')
    svg.path(' '.join(petal(x, y, r, a, PALE) for a in deep), PETAL['pale deep'], name='blossom pale deep')
    svg.path(square(x, y, r * 0.1, turn + 45), PETAL['centre'], name='blossom centre')
    svg.path(square(x, y, r * 0.055, turn + 45), PETAL['heart'], name='blossom heart')


def deep_angles(turn):
    """The DEEP_PETALS petal angles facing furthest from the light, toward the lower left, so every blossom is shaded
    alike whatever its turn."""
    def toward_light(a):
        return math.cos(math.radians(a)) * LIGHT[0] + math.sin(math.radians(a)) * LIGHT[1], a
    return sorted(petal_angles(turn), key=toward_light)[:DEEP_PETALS]


def back_mass(blossoms):
    """The shaded blossoms as one path: each one's petals and a square over its centre, where the petals start a
    little out and would leave a pinhole."""
    return ' '.join('%s %s' % (petals(x, y, r, turn), square(x, y, r * 0.15, turn + 45)) for x, y, r, turn in blossoms)


def back_layer(svg, blossoms):
    """The shaded blossoms behind the front layer: one magenta mass, stroked in its own colour so no chink between
    petals shows the sky, then each blossom over it back to front, its petals edged in the darker magenta and pale
    inside, so wherever the mass shows between the front blossoms it reads as blossoms in shade."""
    if not blossoms:
        return
    svg.path(back_mass(blossoms), BACK, BACK, BACK_SEAL * 2, name='back blossom')
    for x, y, r, turn in blossoms:
        shape = petals(x, y, r, turn)
        svg.path(shape, BACK_EDGE, BACK_EDGE, PETAL_EDGE * 2, name='back blossom edge')
        svg.path(shape, BACK, name='back blossom petals')
        svg.path(' '.join(petal(x, y, r, a, PALE) for a in petal_angles(turn)), BACK_PALE, name='back blossom pale')


def bud(svg, x, y, r):
    """A loose petal, a lavender diamond, a pale cap toward the light."""
    svg.path(bud_shape(x, y, r), BUD['body'], name='bud')
    svg.path(bud_shape(x + r * 0.25 * LIGHT[0], y + r * 0.25 * LIGHT[1], r * 0.5), BUD['pale'], name='bud pale')


def bud_shape(x, y, r):
    return square(x, y, r * 0.72, 20)


def limb_path(name):
    points, widths = LIMBS[name]
    return limb(points, widths)


def lit_normals(points):
    """The unit normal at each point of a limb, turned to the side of the limb the light reaches: a limb rising up
    the sheet is lit down its right, one running right across it along its top."""
    (ax, ay), (bx, by) = points[0], points[-1]
    sign = 1 if -(by - ay) * LIGHT[0] + (bx - ax) * LIGHT[1] >= 0 else -1
    out = []
    for i in range(len(points)):
        (ax, ay), (bx, by) = points[max(0, i - 1)], points[min(len(points) - 1, i + 1)]
        d = math.hypot(bx - ax, by - ay) or 1.0
        out.append((-sign * (by - ay) / d, sign * (bx - ax) / d))
    return out


def lit_strip(points, widths):
    """The lit strip down a limb's lit side, from LIT_FACETS of each half width in turn out to LIT_TO of it."""
    outer, inner = [], []
    for i, ((x, y), w, (nx, ny)) in enumerate(zip(points, widths, lit_normals(points))):
        share = LIT_FACETS[i % len(LIT_FACETS)]
        outer.append((x + nx * w * LIT_TO, y + ny * w * LIT_TO))
        inner.append((x + nx * w * share, y + ny * w * share))
    return poly(inner + outer[::-1])


def shade_strip(points, widths):
    """The shade down a limb's other side, from its outline SHADE_FACETS of the half width in, in turn."""
    outer, inner = [], []
    for i, ((x, y), w, (nx, ny)) in enumerate(zip(points, widths, lit_normals(points))):
        share = 1 - SHADE_FACETS[i % len(SHADE_FACETS)]
        outer.append((x - nx * w, y - ny * w))
        inner.append((x - nx * w * share, y - ny * w * share))
    return poly(outer + inner[::-1])


def edge(name, side):
    """The polyline down one side of a limb, base to tip."""
    points, widths = LIMBS[name]
    sign = 1 if side == 'lit' else -1
    return [(x + sign * nx * w, y + sign * ny * w) for (x, y), w, (nx, ny) in zip(points, widths, lit_normals(points))]


def inside(name, p):
    """Whether p is inside the limb's outline."""
    return within(edge(name, 'lit') + [LIMBS[name][0][-1]] + edge(name, 'shade')[::-1], p)


def within(ring, p):
    """Whether p is inside the closed polygon ring."""
    hit = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        if (ay > p[1]) != (by > p[1]) and p[0] < ax + (p[1] - ay) * (bx - ax) / (by - ay):
            hit = not hit
    return hit


def crossing(a, b):
    """Where polylines a and b cross, as (point, index of a's segment)."""
    for i, (p, q) in enumerate(zip(a, a[1:])):
        for r, t in zip(b, b[1:]):
            den = (q[0] - p[0]) * (t[1] - r[1]) - (q[1] - p[1]) * (t[0] - r[0])
            if not den:
                continue
            u = ((r[0] - p[0]) * (t[1] - r[1]) - (r[1] - p[1]) * (t[0] - r[0])) / den
            v = ((r[0] - p[0]) * (q[1] - p[1]) - (r[1] - p[1]) * (q[0] - p[0])) / den
            if 0 <= u <= 1 and 0 <= v <= 1:
                return (p[0] + u * (q[0] - p[0]), p[1] + u * (q[1] - p[1])), i
    raise ValueError('the edges do not cross')


def along(polyline, i, corner, step, reach):
    """The point on polyline reach straight from corner, which is on its segment i, walking toward its tip (step 1)
    or its base (step -1)."""
    near = corner
    for far in (polyline[i + 1:] if step > 0 else polyline[i::-1]):
        if math.dist(corner, far) >= reach:
            dx, dy, ex, ey = far[0] - near[0], far[1] - near[1], near[0] - corner[0], near[1] - corner[1]
            a, b, c = dx * dx + dy * dy, 2 * (dx * ex + dy * ey), ex * ex + ey * ey - reach * reach
            t = (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
            return near[0] + t * dx, near[1] + t * dy
        near = far
    raise ValueError('the edge ends within reach of its corner')


def reach(crotch):
    """How far along each edge the crotch's curve starts: FLARE, but no further than the width of the narrowest limb
    it joins where that limb begins, so a twig's fillet stays as small as the twig."""
    return min(FLARE, 2 * min(LIMBS[name][1][0] for name, _ in crotch))


def leaving(polyline, i, corner, other, reach):
    """The points reach along polyline from corner, either way, that lie out of the limb other."""
    out = []
    for step in (1, -1):
        try:
            p = along(polyline, i, corner, step, reach)
        except ValueError:
            continue
        if not inside(other, p):
            out.append(p)
    if not out:
        raise ValueError('the edge stays inside ' + other)
    return out


def flare_points(crotch):
    """(start, corners, end): where the crotch's curve leaves its first edge, the corners where each edge meets the
    next, and where the curve meets its last edge. Where an edge leaves the other limb both ways, as the trunk's
    side does above and below a limb, the crotch's start and end are the nearest pair whose chord crosses no limb
    it joins, so the flare spans the sky in its own corner."""
    edges = [edge(*e) for e in crotch]
    corners = [crossing(a, b)[0] for a, b in zip(edges, edges[1:])]
    starts = leaving(edges[0], crossing(edges[0], edges[1])[1], corners[0], crotch[1][0], reach(crotch))
    ends = leaving(edges[-1], crossing(edges[-1], edges[-2])[1], corners[-1], crotch[-2][0], reach(crotch))
    pairs = [(s, e) for s in starts for e in ends
             if not any(inside(name, ((s[0] + e[0]) / 2, (s[1] + e[1]) / 2)) for name, _ in crotch)]
    start, end = min(pairs, key=lambda pair: math.dist(*pair))
    return start, corners, end


def flare_fill(crotch):
    """The crotch's colour: the bark's shade, carrying a limb's underside shadow round into the trunk, unless every
    edge it joins is a lit one."""
    return BARK['body'] if all(side == 'lit' for _, side in crotch) else BARK['shade']


def flare(crotch):
    """The crotch filled out to a curve from its last edge back round to its first, the corners its handles."""
    start, corners, end = flare_points(crotch)
    curve = 'Q' if len(corners) == 1 else 'C'
    return '%s %s%s Z' % (poly([start] + corners + [end], close=False), curve,
                          ' '.join('%s,%s' % (f(x), f(y)) for x, y in corners[::-1] + [start]))


def trunk(svg):
    """The trunk and its limbs as one outlined mass, each limb then painted over the ones behind it, body, shade and
    lit strip together, the trunk last, its crotches flared in shade, streaked with bark."""
    svg.open('blossom trunk')
    for name in LIMBS:
        svg.path(limb_path(name), BARK['line'], BARK['line'], BARK_LINE * 2, name='limb outline')
    svg.path(' '.join(flare(c) for c in CROTCHES), BARK['line'], BARK['line'], BARK_LINE * 2, name='limb outline')
    for name in LIMBS:
        bark = UPPER_BARK if name in UPPER else BARK
        svg.path(limb_path(name), bark['body'], name='limb')
        if name in SHADED:
            svg.path(shade_strip(*LIMBS[name]), BARK['shade'], name='limb shade')
        if name in LIT:
            svg.path(lit_strip(*LIMBS[name]), bark['lit'], name='limb lit')
    for c in CROTCHES:
        svg.path(flare(c), flare_fill(c), flare_fill(c), 1, name='limb flare')
    svg.path(' '.join(limb(points, widths) for points, widths in STREAKS), BARK['shade'], name='bark streaks')
    svg.close()


def crown(svg, name, blossoms, back):
    """The blossoms as one clump: the shaded back layer behind, each blossom edged in the darker pink over it."""
    svg.open(name)
    back_layer(svg, back)
    for x, y, r, turn in blossoms:
        flower(svg, x, y, r, turn)
    svg.close()


def cluster(svg, tid):
    """The loose cluster tid, drawn where it hangs."""
    c = CLUSTERS[tid]
    hx, hy = c['hang']
    svg.open(tid.replace('-', ' '))
    for dx, dy, r in c['buds']:
        bud(svg, hx + dx, hy + dy, r)
    for dx, dy, r, turn in c['blossoms']:
        flower(svg, hx + dx, hy + dy, r, turn)
    svg.close()


def main():
    svg = Svg()
    svg.open('blossom tree')
    trunk(svg)
    crown(svg, 'blossom crown left', CROWN_LEFT, BACK_LEFT)
    crown(svg, 'blossom crown right', CROWN_RIGHT, BACK_RIGHT)
    for tid in CLUSTERS:
        cluster(svg, tid)
    svg.close()
    svg.write(cutting.sheet_path('plants/blossom.svg'))


def cluster_part(path, group, grads, tid):
    """The cluster as an image whose centre is exactly where it hangs, for a "center" anchor and pivot."""
    box = svgtools.stem_box(svgtools.element_bbox(group), CLUSTERS[tid]['hang'], cutting.PAD)
    return cutting.Part(path, svgtools.part_svg(tid, [group], grads, box), box)


def cut():
    """[(template id, its image)]: the trunk, the two crown clumps, then the loose clusters."""
    root, grads = cutting.load('plants/blossom.svg')
    out = []
    for gid, tid in (('blossom trunk', 'blossom-trunk'), ('blossom crown left', 'blossom-crown-left'),
                     ('blossom crown right', 'blossom-crown-right')):
        out.append((tid, cutting.static_part('plants/parts/blossom/' + tid.partition('-')[2],
                                             [cutting.find_group(root, gid)], grads, tid)))
    for tid in CLUSTERS:
        out.append((tid, cluster_part('plants/parts/blossom/' + tid.partition('-')[2],
                                      cutting.find_group(root, tid.replace('-', ' ')), grads, tid)))
    return out


def parts():
    return [part for _, part in cut()]


if __name__ == '__main__':
    main()

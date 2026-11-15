#   Writes SVG, run by `python3 -m scene_export render`: plants/lantern_tree.svg, the leafy tree framing the right of
#   the TrainMeadow scene: a twisting trunk rising off the bottom right, its foot hidden in the meadow, forking into
#   limbs under a crown of round clumps that runs past the top and right edges; a crystal lantern and a red gear
#   banner hang from the limb reaching left under the crown, where they show against the sky and hills.
#
#   python3 -m plants.lantern_tree  ->  lantern_tree.svg
#
#   Everything is drawn where it sits on the 1536 x 1024 sheet (measured off panel-attack-references/TrainMeadow/
#   stage.png, the tree's look after lantern-tree.jpg there). The crown is the day valley oaks' cloud of clusters
#   (plants/broadleaf.py), lit from the upper right as the whole scene is. The trunk and crown cut as images placed
#   where they sit; the lantern and the banner cut as templates whose top centre is the point on the limb each
#   hangs from, so a "topCenter" anchor and pivot let the scene swing it.

import math
import os
import random

from common.painting import Svg, f, poly
from scene_export import cutting, svgtools
from EsmeTerrace import rail
from plants import broadleaf, foliage
from plants.broadleaf import circle

HERE = os.path.dirname(os.path.abspath(__file__))


# the crown's colours sampled off the stage's right tree: lime caps toward the light and a yellow-green body; its
# shade along the undersides and over the trunk and its outline are the Esme terrace's leaf shade and leaf outline,
# darker greens of the leaves themselves, as every outline here is a dark shade of its own colour, never near-black
CLOUD = {'line': foliage.LEAF_OUTLINE, 'under': foliage.LEAF_SHADE_DEEP['leaf-dark'], 'body': '#8ecd3c',
         'cap': '#aee13a'}


SILHOUETTE_LINE = 3.0            # px, the outline round each cluster, the Esme leaves' width


# the crown's clusters on the sheet, top row first so the lower rows' bodies cover the shade of the rows behind and
# the shade gathers along the underside; each (x, y, radius). Its underside rises to the right, from the low left
# end over the limb the lanterns hang from to the limbs climbing into it over the fork; its top row and right column
# run past the visible band.
CLUSTERS = [(1476, 104, 46), (1530, 66, 56), (1596, 44, 48),
            (1416, 168, 48), (1496, 136, 62), (1578, 104, 58),
            (1368, 232, 50), (1600, 170, 46),
            (1318, 300, 56), (1404, 292, 50), (1498, 262, 54), (1580, 246, 50)]


# clusters from the crown's middle rows drawn last, in front of the row below them, so the crown has depth
CLUSTERS_FRONT = [(1440, 218, 60), (1530, 190, 62)]


# the clusters behind the fork, drawn before the trunk so the limbs climb out of foliage: the crown's underside
CLUSTERS_BACK = [(1452, 326, 40), (1536, 312, 46), (1604, 300, 42)]


CLUSTER_LOBES = 0.4              # a cluster's edge lobes' radius as a share of its radius


# a cluster's body is its lobes each shrunk toward its upper right, tangent to the lobe there, by this share of its
# radius, between its value for the crown's shaded lower left and its value toward the light at the upper right,
# so the shade shows as a crescent along each lobe's underside and left, wide in the crown's shade and gone toward
# the light
BODY_IN = (0.2, 0.03)


# the lit face over the body: one disc the cluster's size, drawn in toward its upper right by this share of its radius
# and sized this share of it, growing toward the light until the mid green shows only as facets between the faces
FACE_IN = (0.18, 0.05)


FACE_SIZE = (0.72, 0.95)


LIGHT_AXIS = ((1300, 340), (1570, 60))   # the crown's light runs from its shaded lower left corner to its lit upper
                                         # right one: a cluster's lighting is how far along this it stands


# the trunk's centreline from the fork down to its foot under the meadow, each (x, y, half width): a slow S, leaning
# left as it rises
TRUNK = [(1480, 356, 17), (1486, 400, 19), (1494, 450, 22), (1502, 500, 26), (1510, 560, 30), (1516, 620, 34)]


# the limbs from the fork, each a quadratic bend (from, over, to) with half widths at its base and tip. 'reach' is the
# limb the lanterns and banner hang from, reaching left under the crown; the rest climb into the clusters.
LIMBS = {
    'reach': (((1470, 372), (1410, 320), (1282, 366)), (16, 3.5)),
    'reach twig': (((1412, 348), (1394, 326), (1374, 306)), (6, 2.5)),
    'climb left': (((1472, 358), (1444, 330), (1386, 292)), (16, 5.5)),
    'climb': (((1478, 352), (1490, 300), (1470, 250)), (13, 5)),
    'climb right': (((1484, 360), (1530, 326), (1570, 290)), (15, 5)),
    'climb right twig': (((1522, 330), (1544, 318), (1556, 296)), (5, 2.5)),
}


BARK = {'body': '#8a4e5c', 'lit': '#d8845a', 'shade': '#6a3e58', 'deep': '#52304a', 'line': '#61303a'}


BARK_LINE = 2.8                  # px, the trunk's outline


LIT_SHARE, SHADE_SHARE = (0.3, 0.88), (-0.95, -0.45)   # the lit strip's and the shade's span across the trunk, as
                                                       # shares of the half width from the centreline (right positive)


GROOVES = [(0.02, -0.6), (0.2, 0.3), (0.35, -0.2), (0.55, 0.55), (0.6, -0.65), (0.8, 0.1)]      # bark grooves: (where along the trunk they start, their x
                                                        # share), each twisting down a third of the trunk


HANGER_LIMB = 'reach'


def bend(a, c, b, n=8):
    return broadleaf.bend(a, c, b, n)


def limb_points(name):
    """The centreline points and half widths of that limb."""
    (a, c, b), (w0, w1) = LIMBS[name]
    pts = bend(a, c, b)
    return pts, [w0 + (w1 - w0) * i / (len(pts) - 1) for i in range(len(pts))]


def along_limb(name, t):
    """The whole pixel nearest the point t of the way along that limb's centreline."""
    (a, c, b), _ = LIMBS[name]
    x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0]
    y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]
    return round(x), round(y)


# the hangers: each hangs from a whole pixel of the 'reach' limb's centreline, that far along it, its template's top
# centre; the lantern's rope and the banner's cords run down from there. The lantern hangs out near the limb's tip,
# the banner between it and the trunk, where the limb's inner half stays clear so the trunk shows.
HANGERS = {
    'lantern-left': (along_limb(HANGER_LIMB, 0.94), 'lantern'),
    'banner': (along_limb(HANGER_LIMB, 0.45), 'banner'),
}


LANTERN = dict(chain=70, cap=(4.5, 14, 9), body=(14, 11, 30), foot=9, crystal=(9, 13))
#   rope length; the cap's (half width at the ring, half width at the body, height); the body's (half width at the
#   top, at the foot, height); the foot's height; the crystal's (half width, half height)


BANNER = dict(cord=(45, 25, 3.5), rod=(29, 3.4), finial=(5, 1.2), cloth=(18, 80), sleeve=(7, 1.5), tail=10,
              border=3.5, gear=(11, 8))
#   the cords' (length down to the rod, half the distance between them, half the spread of each loop's two strands
#   where it goes round the limb); the rod's (half length, radius), long enough to show its shaft past the sleeve
#   and the cords tied round it there; the finials' (length, how far they stand proud of the rod), a cap on each end;
#   the cloth's (half width, length from the rod to the tail's notches); the sleeve's (depth below the rod, where the
#   cloth folds back round it, how far it bulges past the cloth's sides); the swallowtail's depth; the border's
#   width; the gear's (outer radius, teeth)


ROPE = {'body': '#8a6238', 'line': '#614020'}


GOLD = {'lit': '#ffe88a', 'body': '#e4aa3c', 'shade': '#a06a22', 'line': rail.GOLD_LINE}


CRYSTAL = {'glow': '#b8fbff', 'body': '#1cdef7', 'deep': '#0ea4d4', 'pale': '#f0ffff', 'pane': '#0a3448'}


CLOTH = {'body': '#c43048', 'shade': '#8c1e32', 'lit': '#dc4a62', 'trim': '#f0c04a', 'line': '#6e1627'}


DETAIL_LINE = 1.5                # px, the hangers' outlines, the Esme gems' width


def distance_to_limb(point, name):
    """How far outside the limb's body the point is: 0 when the limb covers it."""
    pts, widths = limb_points(name)
    best = math.inf
    for (ax, ay), (bx, by), w in zip(pts, pts[1:], widths):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((point[0] - ax) * dx + (point[1] - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(point[0] - ax - t * dx, point[1] - ay - t * dy) - w)
    return max(0.0, best)


def trunk_path(widths_share=(-1.0, 1.0)):
    """The outline of the trunk between those shares of its half width, from the fork to the foot."""
    left = [(x + w * widths_share[0], y) for x, y, w in TRUNK]
    right = [(x + w * widths_share[1], y) for x, y, w in TRUNK]
    return poly(left + right[::-1])


def trunk(svg):
    """The trunk and its limbs outlined as one, lit down its right, shaded on its left, grooves twisting down it."""
    limbs = [limb_points(name) for name in LIMBS]
    svg.open('lantern tree trunk')
    svg.path(trunk_path(), BARK['line'], BARK['line'], BARK_LINE * 2, name='trunk outline')
    for pts, widths in limbs:
        svg.path(broadleaf.limb(pts, widths), BARK['line'], BARK['line'], BARK_LINE * 2, name='limb outline')
    svg.path(trunk_path(), BARK['body'], name='trunk')
    for pts, widths in limbs:
        svg.path(broadleaf.limb(pts, widths), BARK['body'], name='limb')
    svg.path(trunk_path(SHADE_SHARE), BARK['shade'], name='trunk shade')
    svg.path(trunk_path(LIT_SHARE), BARK['lit'], name='trunk lit')
    for pts, widths in limbs:
        svg.path(broadleaf.limb([(x, y - w * 0.3) for (x, y), w in zip(pts, widths)], [w * 0.3 for w in widths]),
                 BARK['lit'], name='limb lit')
    ys = [y for _, y, _ in TRUNK]
    for start, share in GROOVES:
        top, bottom = ys[0] + (ys[-1] - ys[0]) * start, ys[0] + (ys[-1] - ys[0]) * min(1.0, start + 0.35)
        groove = [(trunk_x(y, share + 0.25 * math.sin((y - top) / 30)), y) for y in range(int(top), int(bottom), 6)]
        svg.stroke(poly(groove, close=False), BARK['deep'], 1.6, name='groove')
    svg.close()


def trunk_x(y, share):
    """The x of that share across the trunk's half width at height y, between the centreline's points."""
    for (x0, y0, w0), (x1, y1, w1) in zip(TRUNK, TRUNK[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return x0 + (x1 - x0) * t + (w0 + (w1 - w0) * t) * share
    return TRUNK[-1][0] + TRUNK[-1][2] * share


def lighting(x, y):
    """How far toward the upper right light a point of the crown stands, 0 at its shaded lower left corner to 1."""
    (x0, y0), (x1, y1) = LIGHT_AXIS
    dx, dy = x1 - x0, y1 - y0
    return max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))


def between(pair, t):
    return pair[0] + (pair[1] - pair[0]) * t


def drawn_in(lobes, k, size=1.0):
    """The lobes each shrunk toward its upper right by k of its radius, staying inside it, then sized by size about
    the same point."""
    return ' '.join(circle(x + k * r, y - k * r, r * (1 - k * math.sqrt(2)) * size) for x, y, r in lobes)


def clusters_of(places, seed):
    rng = random.Random(seed)
    return [(x, y, r, broadleaf.cluster(x, y, r, CLUSTER_LOBES, rng)) for x, y, r in places]


def cloud(svg, clusters):
    """The clusters as one cloud, back to front, each inside its own dark green outline as the Esme bushes edge every
    leaf, filled with the teal of its shade; each cluster's mid green body sits in from the shade toward the upper
    right, and one lit face further in, more so toward the light at the upper right, so the shade shows as crescents
    along the undersides and the mid green as facets between the faces."""
    for x, y, r, lobes in clusters:
        shape = broadleaf.lobes_path([(lx, ly, lr, '') for lx, ly, lr in lobes])
        lit = lighting(x, y)
        svg.path(shape, CLOUD['line'], CLOUD['line'], SILHOUETTE_LINE * 2, name='cluster outline')
        svg.path(shape, CLOUD['under'], name='cluster shade')
        svg.path(drawn_in(lobes, between(BODY_IN, lit)), CLOUD['body'], name='cluster body')
        svg.path(drawn_in([(x, y, r)], between(FACE_IN, lit), between(FACE_SIZE, lit)), CLOUD['cap'], name='cluster face')


def crown_back(svg):
    """The crown's underside behind the fork."""
    svg.open('lantern tree crown-back')
    cloud(svg, clusters_of(CLUSTERS_BACK, 'lantern tree back'))
    svg.close()


def crown(svg):
    """The crown over the trunk and limbs."""
    svg.open('lantern tree crown')
    cloud(svg, clusters_of(CLUSTERS + CLUSTERS_FRONT, 'lantern tree'))
    svg.close()


def ring(svg, x, y, r, name):
    svg.path(circle(x, y, r), 'none', GOLD['shade'], 1.6, name=name)


def rope(svg, x, y, length):
    """A twisted rope down from (x, y), its strands' turns marked along it."""
    svg.stroke('M%s,%s L%s,%s' % (f(x), f(y), f(x), f(y + length)), ROPE['line'], 3.4, name='rope outline')
    svg.stroke('M%s,%s L%s,%s' % (f(x), f(y), f(x), f(y + length)), ROPE['body'], 2.2, name='rope')
    for i in range(int(length // 4)):
        yy = y + 2 + i * 4
        svg.stroke('M%s,%s L%s,%s' % (f(x - 1.1), f(yy + 1.2), f(x + 1.1), f(yy - 1.2)), ROPE['line'], 0.8, name='strand')


def trapezoid(x, y0, y1, hw0, hw1):
    return poly([(x - hw0, y0), (x + hw0, y0), (x + hw1, y1), (x - hw1, y1)])


def lantern(svg, hang):
    """A crystal lantern hanging by its chain from hang: a gold cap and foot round a glass body, a cyan crystal
    glowing inside."""
    x, y = hang
    L = LANTERN
    rope(svg, x, y, L['chain'])
    top = y + L['chain']
    cap_ring, cap_hw, cap_h = L['cap']
    body_hw, foot_hw, body_h = L['body']
    body_top, body_bottom = top + cap_h, top + cap_h + body_h
    foot_bottom = body_bottom + L['foot']
    cx, cy = x, (body_top + body_bottom) / 2
    cap = poly([(x - cap_ring, top), (x + cap_ring, top), (x + cap_hw, body_top - cap_h * 0.35),
                (x + cap_hw, body_top), (x - cap_hw, body_top), (x - cap_hw, body_top - cap_h * 0.35)])
    foot = poly([(x - foot_hw, body_bottom), (x + foot_hw, body_bottom), (x + foot_hw * 0.5, foot_bottom - 3),
                 (x, foot_bottom), (x - foot_hw * 0.5, foot_bottom - 3)])
    body = poly([(x - body_hw, body_top), (x + body_hw, body_top), (x + foot_hw, body_bottom), (x - foot_hw, body_bottom)])
    outline = ' '.join([cap, body, foot])
    svg.path(outline, GOLD['line'], GOLD['line'], DETAIL_LINE * 2, name='lantern outline')
    ring(svg, x, top - 1, 2.5, 'cap ring')
    svg.path(cap, GOLD['body'], name='cap')
    svg.path(poly([(x - cap_ring * 0.5, top + 1.5), (x + cap_ring * 0.3, top + 1.5), (x + cap_hw * 0.3, body_top - 1.5),
                   (x - cap_hw * 0.4, body_top - 1.5)]), GOLD['lit'], name='cap lit')
    svg.path(body, CRYSTAL['pane'], name='pane')
    svg.path(poly([(x - body_hw + 2.5, body_top + 2), (x + body_hw - 2.5, body_top + 2),
                   (x + foot_hw - 2.5, body_bottom - 2), (x - foot_hw + 2.5, body_bottom - 2)]), CRYSTAL['deep'],
             name='glass', extra=' fill-opacity="0.55"')
    svg.path(circle(cx, cy, (L['crystal'][0] * 1.3, L['crystal'][1] * 1.1)), CRYSTAL['glow'], name='glow',
             extra=' fill-opacity="0.45"')
    chw, chh = L['crystal']
    svg.path(poly([(cx, cy - chh), (cx + chw, cy - chh * 0.2), (cx + chw * 0.6, cy + chh), (cx - chw * 0.6, cy + chh),
                   (cx - chw, cy - chh * 0.2)]), CRYSTAL['body'], CRYSTAL['deep'], 1.0, name='crystal')
    svg.path(poly([(cx, cy - chh), (cx + chw, cy - chh * 0.2), (cx - chw, cy - chh * 0.2)]), CRYSTAL['pale'],
             name='crystal lit')
    svg.path(poly([(cx - chw * 0.25, cy - chh * 0.4), (cx + chw * 0.1, cy - chh * 0.2), (cx - chw * 0.2, cy + chh * 0.6)]),
             CRYSTAL['glow'], name='crystal sparkle')
    for side in (-1, 1):
        svg.path(poly([(x + side * body_hw, body_top), (x + side * (body_hw - 2.5), body_top),
                       (x + side * (foot_hw - 2.5), body_bottom), (x + side * foot_hw, body_bottom)]),
                 GOLD['shade'] if side < 0 else GOLD['body'], name='post')
    for yy, hw in ((body_top, body_hw), (body_bottom, foot_hw)):
        svg.path(poly([(x - hw, yy - 1.5), (x + hw, yy - 1.5), (x + hw, yy + 1.5), (x - hw, yy + 1.5)]),
                 GOLD['body'], name='rail')
    svg.path(foot, GOLD['shade'], name='foot')
    svg.path(poly([(x - foot_hw * 0.3, body_bottom + 1), (x + foot_hw * 0.5, body_bottom + 1), (x, foot_bottom - 3)]),
             GOLD['body'], name='foot lit')
    svg.path(poly([(x - 2.2, foot_bottom - 1), (x + 2.2, foot_bottom - 1), (x, foot_bottom + 4)]), GOLD['body'],
             GOLD['line'], DETAIL_LINE, name='finial')


def gear(svg, cx, cy, r, teeth):
    """A gold cog of that outer radius with a hole through it."""
    pts = []
    for i in range(teeth * 2):
        a = math.pi * 2 * i / (teeth * 2) - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.74
        for da in (-0.5, 0.5):
            pts.append((cx + rr * math.cos(a + da * math.pi / (teeth * 2) * 0.9),
                        cy + rr * math.sin(a + da * math.pi / (teeth * 2) * 0.9)))
    svg.path(poly(pts), GOLD['body'], GOLD['line'], DETAIL_LINE, name='gear')
    svg.path(circle(cx, cy, r * 0.3), CLOTH['shade'], GOLD['line'], DETAIL_LINE, name='gear hole')
    svg.path(poly([(cx - r * 0.6, cy - r * 0.55), (cx + r * 0.1, cy - r * 0.7), (cx, cy - r * 0.42),
                   (cx - r * 0.45, cy - r * 0.3)]), GOLD['lit'], name='gear lit')


def cord_loop(svg, cx, y, rod_y, spread):
    """One cord tying the rod up to the limb: a loop whose two strands go round the limb and meet at the rod."""
    for colour, width, name in ((ROPE['line'], 3.0, 'cord outline'), (ROPE['body'], 1.6, 'cord')):
        svg.stroke('M%s,%s L%s,%s L%s,%s' % (f(cx - spread), f(y), f(cx), f(rod_y), f(cx + spread), f(y)), colour,
                   width, name=name)


def rod(svg, x, rod_y):
    """The gold rod the banner hangs from, a cylinder lit along its top and shaded under, a ball finial at each end."""
    rod_hl, rod_r = BANNER['rod']
    body = poly([(x - rod_hl, rod_y - rod_r), (x + rod_hl, rod_y - rod_r), (x + rod_hl, rod_y + rod_r),
                 (x - rod_hl, rod_y + rod_r)])
    svg.path(body, GOLD['body'], GOLD['line'], DETAIL_LINE, name='rod')
    svg.path(poly([(x - rod_hl, rod_y + rod_r * 0.15), (x + rod_hl, rod_y + rod_r * 0.15), (x + rod_hl, rod_y + rod_r),
                   (x - rod_hl, rod_y + rod_r)]), GOLD['shade'], name='rod shade')
    svg.path(poly([(x - rod_hl + 1, rod_y - rod_r + 0.7), (x + rod_hl - 1, rod_y - rod_r + 0.7),
                   (x + rod_hl - 1, rod_y - rod_r * 0.35), (x - rod_hl + 1, rod_y - rod_r * 0.35)]), GOLD['lit'],
             name='rod lit')
    length, proud = BANNER['finial']
    for side in (-1, 1):
        inner, outer = x + side * (rod_hl - 0.5), x + side * (rod_hl + length)
        cap = poly([(inner, rod_y - rod_r - proud), (outer, rod_y - rod_r - proud), (outer, rod_y + rod_r + proud),
                    (inner, rod_y + rod_r + proud)])
        svg.path(cap, GOLD['body'], GOLD['line'], DETAIL_LINE, name='finial')
        svg.path(poly([(inner, rod_y - rod_r - proud + 0.7), (outer, rod_y - rod_r - proud + 0.7), (outer, rod_y - rod_r * 0.3),
                       (inner, rod_y - rod_r * 0.3)]), GOLD['lit'], name='finial lit')
        svg.stroke('M%s,%s L%s,%s' % (f(inner + side * 1.6), f(rod_y - rod_r - proud), f(inner + side * 1.6),
                                      f(rod_y + rod_r + proud)), GOLD['line'], 0.9, name='finial groove')


def banner(svg, hang):
    """The red gear banner as a real one hangs: a round gold rod with a ball finial at each end, tied up to the limb
    by a short cord loop at each end, the swallowtailed red cloth's top folded over the rod in a sleeve that bulges
    past the cloth, a gold border and a gold gear on its field."""
    x, y = hang
    B = BANNER
    cord_len, cord_hx, spread = B['cord']
    rod_hl, rod_r = B['rod']
    rod_y = y + cord_len
    for side in (-1, 1):
        cord_loop(svg, x + side * cord_hx, y, rod_y, spread)
    rod(svg, x, rod_y)
    for side in (-1, 1):
        ring(svg, x + side * cord_hx, rod_y, rod_r + 1.2, 'cord ring')
    chw, length = B['cloth']
    sleeve_depth, bulge = B['sleeve']
    shw = chw + bulge
    top = rod_y - rod_r - 1.0
    fold = rod_y + rod_r + sleeve_depth
    bottom = rod_y + length
    tail = B['tail']
    cloth = poly([(x - shw, top), (x + shw, top), (x + shw, fold), (x + chw, fold + 2), (x + chw, bottom),
                  (x, bottom - tail), (x - chw, bottom), (x - chw, fold + 2), (x - shw, fold)])
    svg.path(cloth, CLOTH['line'], CLOTH['line'], DETAIL_LINE * 2, name='cloth outline')
    svg.path(cloth, CLOTH['shade'], name='cloth border')
    b = B['border']
    inner = poly([(x - chw + b, fold), (x + chw - b, fold), (x + chw - b, bottom - b * 1.6),
                  (x, bottom - tail - b * 0.4), (x - chw + b, bottom - b * 1.6)])
    svg.path(inner, CLOTH['body'], name='cloth')
    svg.path(poly([(x - chw + b, fold), (x - chw + b * 2.2, fold), (x - chw + b * 2.2, bottom - b * 2),
                   (x - chw + b, bottom - b * 1.6)]), CLOTH['shade'], name='cloth shade')
    svg.path(inner, 'none', CLOTH['trim'], 1.2, name='trim')
    svg.path(poly([(x - shw, top), (x + shw, top), (x + shw, fold), (x - shw, fold)]), CLOTH['body'], name='sleeve')
    svg.path(poly([(x - shw, top), (x + shw, top), (x + shw, rod_y), (x - shw, rod_y)]), CLOTH['lit'], name='sleeve lit')
    svg.path(poly([(x - shw, rod_y + rod_r * 0.5), (x + shw, rod_y + rod_r * 0.5), (x + shw, fold), (x - shw, fold)]),
             CLOTH['shade'], name='sleeve fold')
    svg.stroke('M%s,%s L%s,%s' % (f(x - shw), f(fold), f(x + shw), f(fold)), CLOTH['line'], DETAIL_LINE,
               name='sleeve hem')
    gr, teeth = B['gear']
    gear(svg, x, fold + (bottom - fold) * 0.36, gr, teeth)


def hangers(svg):
    for tid, (hang, kind) in HANGERS.items():
        svg.open('lantern tree ' + tid)
        (lantern if kind == 'lantern' else banner)(svg, hang)
        svg.close()


def main():
    svg = Svg()
    svg.open('lantern tree')
    crown_back(svg)
    trunk(svg)
    crown(svg)
    hangers(svg)
    svg.close()
    svg.write(cutting.sheet_path('plants/lantern_tree.svg'))


def hang_box(bbox, hang, pad):
    """(x, y, w, h) holding bbox plus pad below and to the sides, with its top centre exactly on hang, so a template's
    "topCenter" anchor and pivot are where it hangs. w and h are even, so hang must be a whole pixel."""
    hx, hy = hang
    if hx != int(hx) or hy != int(hy):
        raise ValueError('the hang point must sit on a whole pixel')
    half = math.ceil(max(hx - (bbox[0] - pad), bbox[2] + pad - hx))
    height = math.ceil(bbox[3] + pad - hy)
    height += height % 2
    return int(hx - half), int(hy), 2 * half, height


def hanger_part(path, group, grads, name, hang):
    box = hang_box(svgtools.element_bbox(group), hang, cutting.PAD)
    return cutting.Part(path, svgtools.part_svg(name, [group], grads, box), box)


def cut():
    """[(template id, its image)] in draw order: the crown's back, the trunk and the crown where they sit, then each
    hanger around the point it hangs from."""
    root, grads = cutting.load('plants/lantern_tree.svg')
    out = []
    for name in ('crown-back', 'trunk', 'crown'):
        tid = 'lantern-tree-' + name
        out.append((tid, cutting.static_part('plants/parts/lantern-tree/' + name,
                                             [cutting.find_group(root, 'lantern tree ' + name)], grads, tid)))
    for name, (hang, _) in HANGERS.items():
        tid = 'lantern-tree-' + name
        out.append((tid, hanger_part('plants/parts/lantern-tree/' + name,
                                     cutting.find_group(root, 'lantern tree ' + name), grads, tid, hang)))
    return out


def parts():
    return [part for _, part in cut()]


if __name__ == '__main__':
    main()

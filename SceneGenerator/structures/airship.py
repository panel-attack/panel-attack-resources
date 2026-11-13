#   Writes SVG, run by `python3 -m scene_export render`: structures/airship.svg, Magellan's airship: the round blue
#   bird-head balloon with its fin ears, beak and wing, the propeller turning behind it and the studded gondola
#   slung under it.
#
#   python3 -m structures.airship  ->  airship.svg
#
#   Drawn at the size of the hand-drawn DayAirship@2x.png it replaces (300 x 280 px, reference airship.png in
#   panel-attack-references/DayValley/), so the part places at the same scale. Every point below is in that
#   image's pixels; ORIGIN is where its top left sits on the sheet. Light comes from the upper left: the balloon's
#   lower rim is in shade, the ears and wing catch a pale rim on their upper edges.

import math
import os

from common.painting import Svg, f, mix
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))


ORIGIN = (200, 200)              # sheet px of the reference image's top left


INK = '#262658'                  # the outline ink every face's own colour is darkened toward


LINE_DARKEN = 0.95               # outlines are the face's colour this far toward INK


LINE = 4.0                       # px, outer outlines


DETAIL_LINE = 1.6                # px, inner edges


FIN_LINE = 2.6                   # px, the outlines of the small fins and flaps


DARK_LINE = '#0c0a2c'            # the near-black navy round the shaded fins, flaps and gondola


SEAM_LINE = 3.8                  # px, the balloon's seam, drawn as heavy as the reference's


BLUE = {'lit': '#82d5f7', 'body': '#73abd8', 'shade': '#5a7fb4', 'deep': '#4c5482', 'rim': '#7cc0e8', 'back': '#6a9fcf'}
BEAK = {'body': '#4f3860', 'shade': '#351c3a'}
EYE = '#1e1720'
EYE_LINE = '#08060c'
PROP = {'disc': '#fcfcfd', 'tint': '#efe6f3', 'blade': '#1a1820', 'streak': '#24202a'}
GONDOLA = {'rim': '#551f19', 'band': '#282233', 'band_lit': '#3a3448', 'stud': '#a8ccf2', 'socket': '#130e1f',
           'line': '#000000', 'beak_line': '#1a031c'}


# ---------------------------------------------------------------- balloon
BODY_CENTRE = (143.0, 121.0)
BODY_RX, BODY_RY = 116.0, 115.5
BODY_SQUARE = (2.4, 2.2)         # superellipse exponents of the balloon's lower left and lower right (2 is round)
TOP_LEAN = -4.0                  # px the crown of the balloon sits left of its centre
SHADE_EDGE = [(48, 192), (80, 207), (143, 215), (200, 204), (244, 186)]   # the lower shade's hard upper edge, rim to rim
SEAM = [(137, 4), (114, 42), (103, 92), (100, 160), (108, 206), (122, 235)]   # the front meridian seam
RIM_LIGHT = 4.6                  # px inside the outline, the middle of the pale rim light round the balloon's upper left

# ---------------------------------------------------------------- face
EYES = [((66.0, 77.5), 6.5, 18.5, 5.0), ((165.0, 81.5), 7.0, 19.0, 8.0)]   # centre, rx, ry, tilt degrees (top right)
BEAK_SHAPE = [(76, 128), (78, 110), (102, 99), (128, 104), (143, 125), (126, 152), (101, 172), (86, 160)]
BEAK_FACET = [(77, 140), (100, 153), (118, 150), (141, 128), (126, 152), (101, 172), (86, 160)]

# ---------------------------------------------------------------- ears and wing
# the left ear's outline, top lobe round to bottom lobe; the last points close it inside the balloon, out of sight
LEFT_EAR = [(42, 62), (34, 57), (26, 57), (20, 63), (17, 74), (18, 84), (12, 92), (4, 100), (2, 112), (6, 124),
            (12, 130), (11, 140), (12, 154), (18, 164), (30, 168), (42, 164), (60, 140), (60, 80)]
# the wing in front of the balloon's right side: an open curl, outlined along its top arc, its scalloped outer
# edge and its lower hook, its inner side merging into the balloon
WING_TOP = [(220, 113), (232, 96), (248, 86), (264, 84)]
WING_EDGE = [(264, 84), (267, 98), (263, 110), (252, 116), (262, 122), (269, 134), (265, 148), (255, 155),
             (263, 162), (262, 174), (256, 184)]
# the wing's far half, seen past the scalloped near edge as a strip with a straight outer edge, and the shaded
# flap under the lower hook
WING_BACK = [(256, 86), (266, 84), (271, 104), (272, 130), (270, 156), (264, 178), (250, 176), (250, 100)]
WING_FLAP = [(222, 170), (234, 182), (248, 187), (258, 184), (262, 192), (250, 197), (236, 192), (226, 182)]
WING_HOOK = [(220, 168), (232, 180), (246, 186), (256, 184)]
TOP_FIN = [(252, 82), (259, 69), (273, 57), (274, 74), (272, 94)]
TAIL_FIN = [(236, 186), (244, 200), (254, 214), (262, 198), (262, 184)]
TAIL_FIN_RIB = [(238, 190), (247, 200), (254, 211)]

# ---------------------------------------------------------------- propeller
PROP_CENTRE = (281.0, 138.0)
PROP_RX, PROP_RY = 19.0, 41.5
PROP_STREAKS = ([(278, 126), (277, 138), (280, 148)],                        # where the blades catch the eye
                [(280, 141), (285, 134), (290, 137), (287, 146), (293, 151)])

# ---------------------------------------------------------------- gondola
GONDOLA_SIDES = [(73, 218), (80, 238), (90, 257), (103, 270), (120, 277), (141, 279), (162, 277), (180, 270),
                 (195, 257), (205, 238), (212, 218), (190, 198), (92, 198)]
STUDS = [(91, 248), (115, 255), (141, 257), (167, 254), (191, 245)]
STUD_RX, STUD_RY = 4.6, 5.6


def at(x, y):
    return ORIGIN[0] + x, ORIGIN[1] + y


def line_of(fill):
    return mix(fill, INK, LINE_DARKEN)


def smooth(points, closed=True, tension=1.0):
    """A path through the points (reference px) as Catmull-Rom curves, moved onto the sheet."""
    pts = [at(*p) for p in points]
    n = len(pts)

    def p(i):
        if closed:
            return pts[i % n]
        return pts[max(0, min(n - 1, i))]

    segs = n if closed else n - 1
    d = 'M%s,%s' % (f(pts[0][0]), f(pts[0][1]))
    for i in range(segs):
        p0, p1, p2, p3 = p(i - 1), p(i), p(i + 1), p(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 6, p1[1] + (p2[1] - p0[1]) * tension / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 6, p2[1] - (p3[1] - p1[1]) * tension / 6)
        d += ' C%s,%s %s,%s %s,%s' % (f(c1[0]), f(c1[1]), f(c2[0]), f(c2[1]), f(p2[0]), f(p2[1]))
    return d + (' Z' if closed else '')


def ellipse_points(cx, cy, rx, ry, tilt=0.0, n=24):
    t = math.radians(tilt)
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * math.cos(t) - y * math.sin(t), cy + x * math.sin(t) + y * math.cos(t)))
    return out


def rim_point(a, inset=0.0):
    """The balloon's rim at angle a (radians, y down): its crown leaning a little left, its lower half a
    superellipse, squarer on the left, so the bottom sits broad over the gondola as the reference's does."""
    cx, cy = BODY_CENTRE
    c, s = math.cos(a), math.sin(a)
    rx, ry = BODY_RX - inset, BODY_RY - inset
    if s <= 0:
        return cx + rx * c + TOP_LEAN * s * s, cy + ry * s
    e = 2 / BODY_SQUARE[0 if c < 0 else 1]
    return cx + rx * math.copysign(abs(c) ** e, c), cy + ry * s ** e


def capsule_points(cx, cy, rx, ry, tilt):
    """A tall capsule, straight-sided with round ends, turned tilt degrees (its top toward the right)."""
    t = math.radians(tilt)
    half = ry - rx
    out = []
    for k in range(9):
        a = math.pi + math.pi * k / 8
        out.append((rx * math.cos(a), -half + rx * math.sin(a)))
    for k in range(9):
        a = math.pi * k / 8
        out.append((rx * math.cos(a), half + rx * math.sin(a)))
    return [(cx + x * math.cos(t) - y * math.sin(t), cy + x * math.sin(t) + y * math.cos(t)) for x, y in out]


def body_points(n=48):
    return [rim_point(2 * math.pi * k / n) for k in range(n)]


def body_arc(a0, a1, inset=0.0, n=24):
    """Points along the balloon's rim from angle a0 to a1 (degrees, y down), inset px inside it."""
    return [rim_point(math.radians(a0 + (a1 - a0) * k / n), inset) for k in range(n + 1)]


# ================================================================ pieces

def propeller(svg):
    """The propeller seen from the side as a blurred disc, the turning blades as grey arcs round its hub and a
    dark hooked streak where a blade catches the eye."""
    svg.open('propeller')
    cx, cy = PROP_CENTRE
    svg.path(smooth(ellipse_points(cx, cy, PROP_RX, PROP_RY)),
             (PROP['disc'], PROP['tint'], ORIGIN[1] + cy - PROP_RY * 0.2, ORIGIN[1] + cy + PROP_RY), '#1a1a1e', 2.4,
             name='propeller disc')
    for k, (rx, ry) in enumerate(((0.75, 0.86), (0.5, 0.62))):
        arc = [(cx - PROP_RX * rx * math.sin(math.radians(a)) + 2, cy - PROP_RY * ry * math.cos(math.radians(a)))
               for a in range(20, 101, 20)]
        svg.stroke(smooth(arc, closed=False), PROP['blade'], 2.4 - 0.6 * k, name='blade arc')
    svg.stroke(smooth(PROP_STREAKS[0], closed=False), PROP['streak'], 2.8, name='blade streak')
    svg.stroke(smooth(PROP_STREAKS[1], closed=False), PROP['streak'], 2.8, name='blade streak')
    svg.close()


def fin(svg, points, fill, name):
    svg.path(smooth(points, tension=0.6), fill, DARK_LINE, FIN_LINE, name=name)


def fins(svg):
    svg.open('fins')
    fin(svg, TOP_FIN, BLUE['lit'], 'top fin')
    fin(svg, TAIL_FIN, BLUE['deep'], 'tail fin')
    svg.stroke(smooth(TAIL_FIN_RIB, closed=False), line_of(BLUE['deep']), DETAIL_LINE, name='tail fin rib')
    svg.close()


def left_ear(svg):
    """The fluffy three-lobed fin on the balloon's left, tucked behind the balloon's rim."""
    svg.open('left ear')
    svg.path(smooth(LEFT_EAR), BLUE['body'], line_of(BLUE['body']), LINE, name='ear')
    svg.stroke(smooth([(26, 56), (20, 62), (19, 76)], closed=False), BLUE['lit'], 2.4, name='ear sheen')
    svg.stroke(smooth([(10, 96), (6, 104), (5, 116)], closed=False), BLUE['lit'], 2.4, name='ear sheen')
    svg.path(smooth([(13, 154), (16, 162), (24, 167), (34, 168), (26, 162), (18, 156)], tension=0.7),
             BLUE['deep'], name='ear shade')
    svg.close()


def gondola(svg):
    """The gondola: a round-bottomed tub, brown rims above and below a near-black band set with a curved row of
    pale glowing studs, its top hidden up inside the balloon."""
    svg.open('gondola')
    tub = smooth(GONDOLA_SIDES, tension=0.8)
    svg.path(tub, GONDOLA['rim'], GONDOLA['line'], LINE, name='tub')
    band = [(77, 231), (83, 245), (91, 257), (110, 266), (141, 269), (170, 266), (189, 257), (199, 242), (206, 228),
            (176, 240), (141, 245), (106, 242)]
    svg.path(smooth(band, tension=0.6), GONDOLA['band'], GONDOLA['line'], 2.4, name='band')
    for i, (x, y) in enumerate(STUDS):
        k = 0.8 if i in (0, len(STUDS) - 1) else 1.0      # the end studs turn away round the tub
        svg.path(smooth(ellipse_points(x, y, STUD_RX * k + 2.4, STUD_RY + 2.4, n=12)), GONDOLA['socket'],
                 name='stud socket')
        svg.path(smooth(ellipse_points(x, y, STUD_RX * k, STUD_RY, n=12)), GONDOLA['stud'], name='stud')
    svg.close()


def balloon(svg):
    """The balloon: its blue skin, the hard-edged shade along its bottom, a pale rim light on the upper left
    and the seam."""
    svg.open('balloon')
    d = smooth(body_points())
    svg.path(d, BLUE['body'], name='skin')
    svg.stroke(smooth(body_arc(190, 290, RIM_LIGHT), closed=False), BLUE['rim'], 5.0, name='rim light')
    svg.path(smooth(SHADE_EDGE + [p for p in body_arc(12, 168) if p[1] > 180], tension=0.6),
             BLUE['deep'], name='skin shade')
    svg.stroke(smooth(SEAM, closed=False), line_of(BLUE['body']), SEAM_LINE, name='seam')
    svg.path(d, 'none', line_of(BLUE['body']), LINE, name='skin outline')
    svg.close()


def face(svg):
    svg.open('face')
    for (cx, cy), rx, ry, tilt in EYES:
        svg.path(smooth(capsule_points(cx, cy, rx, ry, tilt)), EYE, EYE_LINE, 3.0, name='eye')
    svg.path(smooth([(x + 3, y + 6) for x, y in BEAK_SHAPE], tension=0.8), BLUE['deep'], name='beak shadow',
             extra=' fill-opacity="0.55"')
    svg.path(smooth(BEAK_SHAPE, tension=0.8), BEAK['body'], name='beak')
    svg.path(smooth(BEAK_FACET, tension=0.6), BEAK['shade'], name='beak underside')
    svg.path(smooth(BEAK_SHAPE, tension=0.8), 'none', GONDOLA['beak_line'], 3.0, name='beak outline')
    svg.close()


def wing(svg):
    """The wing on the balloon's right, in front of it: an open curl of three ruffled lobes whose inner side merges
    into the balloon, each lobe catching a pale rim of light, its lower lobe closed off by a curled hook."""
    svg.open('wing')
    svg.path(smooth(WING_BACK, tension=0.6), BLUE['back'], line_of(BLUE['body']), LINE, name='wing back')
    svg.path(smooth(WING_FLAP, tension=0.6), BLUE['deep'], DARK_LINE, FIN_LINE, name='wing flap')
    outline = WING_TOP + WING_EDGE[1:] + list(reversed(WING_HOOK))[1:]
    svg.path(smooth(outline, tension=0.7), BLUE['body'], name='wing')
    svg.stroke(smooth([(x, y + 3) for x, y in WING_TOP], closed=False), BLUE['lit'], 2.6, name='wing sheen')
    for lobe in (WING_EDGE[0:4], WING_EDGE[3:8]):
        svg.stroke(smooth([(x - 3.6, y + 1) for x, y in lobe], closed=False), BLUE['lit'], 4.0, name='lobe rim light')
    ink = line_of(BLUE['body'])
    svg.stroke(smooth(WING_TOP + WING_EDGE[1:], closed=False, tension=0.7), ink, LINE, name='wing outline')
    svg.stroke(smooth(WING_HOOK, closed=False), ink, LINE, name='wing hook')
    svg.close()


def airship(svg):
    svg.open('airship')
    propeller(svg)
    fins(svg)
    left_ear(svg)
    gondola(svg)
    balloon(svg)
    face(svg)
    wing(svg)
    svg.close()


def main():
    svg = Svg()
    airship(svg)
    svg.write(cutting.sheet_path('structures/airship.svg'))


def cut():
    """[(template id, its image)]: the whole airship as one image."""
    root, grads = cutting.load('structures/airship.svg')
    return [('airship', cutting.static_part('structures/parts/airship/airship', [cutting.find_group(root, 'airship')],
                                            grads, 'airship'))]


def parts():
    return [part for _, part in cut()]


if __name__ == '__main__':
    main()

#   Writes SVG, run by `python3 -m scene_export render`: structures/train.svg, the TrainMeadow's steampunk train: a
#   teal-and-gold steam locomotive pulling three carriages along the straight, level track that crosses the meadow.
#
#   python3 -m structures.train  ->  train.svg
#
#   The track runs parallel to the picture at one distance, so the train keeps one shape and only slides in x. It is
#   drawn in one oblique view, as the reference paints it: the near side faces the viewer undistorted, and the far
#   side of everything lies RECEDE px to the right and up per px of depth across the track (project()), so the
#   fronts of things show foreshortened ahead of their sides (the smokebox door, the buffer beam, the cowcatcher,
#   the cylinder heads) and the tops of the roofs and the running board show above their near edges. A far camera
#   makes that one view right at every x. Everything is drawn where the reference's train stands on the
#   1536 x 1024 sheet (read off panel-attack-references/TrainMeadow/train-crop.png, a crop of stage.png at
#   [470, 380, 1110, 540]), its rail tops at RAIL_Y. The sun is to the upper right, so every top face is the lightest
#   tone, every side the body tone, and every front face lies between.
#
#   The wheels stand in the near plane, where the view is undistorted, so they stay circles and a spinning wheel
#   image is right. They are drawn behind the bodies and cut out as their own images, one per wheel size, each
#   centred exactly on its axle so the scene can spin it about its centre; the frames and skirts drawn over them
#   hide their tops, as in the reference. The driving wheels' crank pins all point forward (to the right of the axle), where the
#   connecting rod joining them is drawn, so the rod's image circles with the pins when the scene moves it. The
#   gear emblems on the cab and the carriages are drawn over their bodies and cut out as their own images, one per
#   gear size, centred on their hubs, so the scene can spin them too. The pennant on the cab roof is cut out on its
#   own, hung at the pole, so the scene can flutter it.
#
#   The towers standing on the boiler (the steam dome, the funnel, the headlamp's stalk) and on the roofs (the cab
#   dome, the carriages' toppers) each stand on a foot that wraps what it stands on: where a tower's cylinder meets
#   the round boiler its foot dips below the boiler's top line on the near side (foot_curve()), and on a roof's
#   ridge its foot is the ring the oblique view makes of it. Each is shaded as a cylinder lit from the upper right:
#   a dark band on its left, a lit band on its right.

import colorsys
import math
import os

from common.painting import Svg, f, mix, poly
from EsmeTerrace.rail import GOLD_LINE
from scene_export import cutting, svgtools
from structures.houses import TOWN_LINE_WIDTH

HERE = os.path.dirname(os.path.abspath(__file__))


INK = '#241820'                  # the ink of the shadows the bodies cast on themselves and on the track bed


# Outlines are in the Esme Terrace's style, so the two stages' art matches: every shape's line is a dark of its own
# colour, keeping the colour's saturation (the terrace's teal cushions are lined in deep teal, its white stone in warm
# grey), never greyed toward black; gold takes the terrace's own gold line.
LINE_VALUE = 0.7                 # an outline's HSV value is this share of its fill's, as the terrace's lines are of theirs
LINE_SATURATION = 0.5            # ...and at least this saturated, so pale fills get a warm line rather than a grey one


SCREEN_SCALE = 1280 / 1536       # screen px per sheet px: the sheet is shown about 1280 px wide
MIN_DETAIL = 1 / SCREEN_SCALE    # sheet px, the smallest stroke or feature that still reads at the screen size: one
                                 # screen px, the thin outlines the reference paints
LINE = TOWN_LINE_WIDTH           # px, outer outlines: the Esme Terrace thins its lines with distance, and the train
                                 # stands at its castle's distance, so its outlines are as wide as the castle's


DETAIL_LINE = 1.0                # px, seams, frames and inner edges: the castle's window lines, thinner still


EDGE = LINE / 2                  # px a dark edge disc or stroke shows round a brass piece drawn over it, where a stroke
                                 # would lose the fill: the half of a centred outline that shows


RAIL_Y = 517                     # sheet px, the top of the near rail: every wheel's bottom


DEPTH = 56                       # sheet px, how far across the track a body reaches, its near side to its far side


GAUGE = 44                       # sheet px across the track from the near rail to the far one


RECEDE = (0.42, -0.18)           # sheet px right and up a point lies per px of depth across the track
RIDGE_LIFT = 5                   # sheet px a roof's ridge shows above its near edge's crown: the far slope, drawn straight
                                 # up rather than receding so both ends of a roof read alike


SADDLE_SOFTEN = 0.1              # how much of the true dip a tower's foot shows where it wraps a barrel: the
                                 # reference paints its wide domes sitting nearly flat, so most of the dip is left out


TRAIN_SPEED = 76.0               # sheet px per second the train rolls at: 1536 px of sheet plus its own length in
                                 # about 28 s. The wheels' spin is derived from it so they never skid


TEAL = {'lit': '#4fe0b0', 'body': '#179181', 'shade': '#146b68', 'deep': '#0b4a52'}
GOLD = {'lit': '#ffe07a', 'body': '#eaa934', 'shade': '#b8691c', 'deep': '#7a4412'}
MAROON = {'lit': '#ea8a92', 'body': '#b5425a', 'shade': '#7c2843', 'deep': '#4b1630'}
OLIVE = {'lit': '#67a07a', 'body': '#33775f', 'shade': '#1d5146'}
CREAM = {'lit': '#faf1d6', 'body': '#eddfbc', 'shade': '#cdb98f'}
GLASS = {'lit': '#8fe0ea', 'body': '#43bfd6', 'shade': '#2a90a4'}
RED = {'lit': '#ff8fae', 'body': '#ee4f78', 'shade': '#b32f56'}
DARK = {'lit': '#3b535d', 'body': '#1f3038', 'shade': '#0f1c22'}
SMOKE = {'lit': '#ffffff', 'shade': '#e4edf3', 'line': '#cfdde6'}


# ---------------------------------------------------------------- carriages
CARRIAGE_LEFTS = (485, 609, 733)     # sheet x of each carriage's rear end, the last carriage first
CARRIAGE_W = 118
CAR_ROOF_TOP, CAR_EAVE = 453, 470    # the roof's near edge: its crown and the eave the body hangs from; its top
                                     # face shows above the crown, DEPTH across
CAR_BELT = 489                       # the gold belt between the cream upper body and the teal lower body
CAR_SKIRT = 504                      # the body's bottom edge; the bogies and the wheels' lower halves show below it
CAR_UNDER = 507                      # the dark frame under the skirt reaches down to here
WINDOW_AT = (28, 59, 90)             # px from the carriage's rear to each arched window's centre: one in the middle,
                                     # one either side, so the carriage is the same end to end
WINDOW_W, WINDOW_TOP, WINDOW_SILL = 21, 473, 488
DOOR_IN = 3                          # px in from each end the narrow door stands
MEDALLION_DROP = 9                   # px below the belt the gear medallion in the middle of the lower body hangs, below the windows
TOPPER_IN = 21                       # px in from each end the brass lantern toppers stand on the roof's ridge
TOPPER_HALF = 4                      # a topper's half width
BOGIE_AT = (26,)                     # px from a carriage's end to each wheel at that end

# ---------------------------------------------------------------- locomotive
CAB = (858, 925)                     # x of the cab's back and front walls
CAB_ROOF_TOP, CAB_EAVE, CAB_SILL, CAB_FLOOR = 424, 436, 463, 491
CAB_WINDOWS = ((872, 443, 911, 460),)   # x0, top, x1, sill of the cab's one big window, centred on its side
CAB_GEAR = (892, 476)                # the gear medallion on the cab's side: its hub
FRAME = (854, 1034, 487, 493)        # x0, x1, top, bottom of the running board the boiler and cab sit on
BEAM_BACK = 1016                     # x the buffer beam's own gold side begins, over the running board's end
UNDERFRAME_BOTTOM = 498              # the dark frame under the running board reaches down to here, over the wheels' tops
SHADOW = (-1, 6, 0.3)               # px above and below RAIL_Y the train's shadow on the bed reaches, and its opacity
BOILER = (925, 1040, 466, 21)        # x0, x1, centre y, radius: its belly rests on the running board
BOILER_BANDS = (938, 968, 1000)      # x of each gold band round the boiler: one under the steam dome's middle, none under
                                     # its edges, where a band would read as a leg
HOOP_HALF = 3.5                      # half width of every upright gold hoop round the barrel, the boiler's and the
                                     # smokebox's alike, so they read as one set
BELT_HALF = 1.5                      # half depth of the thin gold belt along the boiler's middle, lengthwise
RIVET_R = 1.3                        # radius of the rivets studding the belt, one between each pair of hoops
FRONT_RING = 5.5                     # px wide the gold ring round the smokebox's front is
FRONT_BAR = 3.5                      # px wide the gold bar from that ring down to the pilot's rail is, the rail's own width
BAR_BEND = 5                         # px radius the bar turns through from falling to running forward
SMOKEBOX = (1034, 1054, 22)          # x0, x1, radius: the maroon smokebox ahead of the boiler, a little fatter; its
                                     # round door is its front face, foreshortened ahead of x1
FUNNEL = (1014, 404)                 # centre x, top y; it rises from the smokebox's top
FUNNEL_HALF = (7, 10, 16)          # half widths: at its base, at the top of its tapering stem, its flared cap
STEAM_DOME = (968, 416, 16)          # centre x, top y, half width: the big brass dome on the boiler
CAB_DOME = (892, 400, 15)            # centre x, top y, half width: the small dome on the cab roof's ridge
HEADLAMP = (1040, 426, 10)          # centre x, top y, half width: the lamp standing on the smokebox
FLAG_POLE = (874, 388)               # x, top y of the pole on the cab roof
FLAG_HANG = (874, 404)               # where the pennant hangs on the pole: the pennant image's right centre
FLAG = [(874, 392), (818, 393), (842, 404), (818, 415), (874, 416)]   # the swallowtail pennant, pole end first
FLAG_GEAR = (858, 404, 9.5)          # hub x, y and radius of the pennant's gear emblem: centred in the pennant's field
                                     # between the pole and the swallowtail's notch, most of the pennant's height
CYLINDER = (1006, 1037, 496, 517)     # x0, x1, top, bottom of the cylinder block ahead of the driving wheels: two
                                     # drums stacked outside the frame, in front of the running board's end
PILOT = (1045, 1073, 1090)           # x of the pilot's near bar, of its top front corner and of its foot's front corner:
                                     # the slatted plough hanging under the buffer beam ahead of the cylinder's head,
                                     # leaning forward to the rail

# ---------------------------------------------------------------- wheels
WHEELS = {'train-drive-wheel': 14, 'train-carriage-wheel': 9}      # template id -> radius px
DRIVE_AXLE_XS = (884, 916, 950, 982)     # four driving wheels coupled in two pairs
LEAD_AXLE_XS = (1052,)               # the small lead wheel under the pilot, seen through its slats
ROD_PAIRS = ((884, 916, 950, 982),)     # the axles each coupling rod joins: one rod couples all four drivers
CRANK_R = 5                          # px from a driving wheel's axle to its crank pin
GEARS = {'train-cab-gear': 18, 'train-carriage-gear': 9}         # template id -> radius px: the cab's gear emblem and
                                     # each carriage's medallion, each its own part spinning about its hub
GEAR_TEETH, GEAR_ROOT = 10, 0.78     # teeth round the cab's gear emblem and how far in from its radius their roots lie:
                                     # short teeth, many, as the reference paints them
GEAR_TEETH_MIN = 6                   # the fewest teeth a smaller gear thins to, keeping the cab gear's tooth pitch
GEAR_TOOTH_SPEED = TRAIN_SPEED / 3   # sheet px per second a gear's teeth run at, decoratively slower than the wheels'
                                     # rims, the same for every gear as if one chain drove them all
ROD_HALF = 2.2                       # px, half the connecting rod's depth
SMOKE_AT = (1013, 378)               # sheet px, the centre of the first smoke puff, drawn over the funnel
SMOKE_SHAPES = {'train-smoke-1': SMOKE_AT, 'train-smoke-2': (960, 330), 'train-smoke-3': (1066, 330),
                'train-smoke-4': (860, 330), 'train-smoke-5': (1170, 330)}
                                     # the five puff shapes and where each is drawn, the others above the train


def line_of(fill):
    """The outline colour of a face painted fill: the terrace's gold line for gold, else a saturated dark of fill."""
    if fill in GOLD.values():
        return GOLD_LINE
    h, s, v = colorsys.rgb_to_hsv(*(int(fill[k:k + 2], 16) / 255 for k in (1, 3, 5)))
    r, g, b = colorsys.hsv_to_rgb(h, max(s, LINE_SATURATION), v * LINE_VALUE)
    return '#%02x%02x%02x' % tuple(round(c * 255) for c in (r, g, b))


def project(x, y, z):
    """Sheet (x, y) of the point z px across the track behind the near-plane point (x, y)."""
    return x + RECEDE[0] * z, y + RECEDE[1] * z


def recede(points, z=DEPTH):
    return [project(x, y, z) for x, y in points]


def top_face(near, z=DEPTH):
    """The face between a near edge and the same edge z px across: the top of a slab, or a front wall."""
    return near + list(reversed(recede(near, z)))


def front_face(x, y0, y1, z=DEPTH):
    """A front wall's face: the vertical edge at x, from y0 to y1, swept z px across."""
    return top_face([(x, y0), (x, y1)], z)


def ring(cx, cy, r, steps=32):
    """A horizontal circle of radius r whose centre projects to (cx, cy): the mouth of a funnel or a dome's foot."""
    return [(cx + r * math.cos(a) + RECEDE[0] * r * math.sin(a), cy + RECEDE[1] * r * math.sin(a))
            for a in (2 * math.pi * k / steps for k in range(steps))]


def front_ring(x, cy, r, steps=32):
    """A circle in a front face, of radius r, whose centre projects to (x, cy): the head of a barrel lying along
    the track."""
    return [(x + RECEDE[0] * r * math.sin(a), cy - r * math.cos(a) + RECEDE[1] * r * math.sin(a))
            for a in (2 * math.pi * k / steps for k in range(steps))]


def circle(cx, cy, r):
    return 'M%s,%s A%s,%s 0 1,0 %s,%s A%s,%s 0 1,0 %s,%s Z' % (
        f(cx - r), f(cy), f(r), f(r), f(cx + r), f(cy), f(r), f(r), f(cx - r), f(cy))


def rrect(x0, y0, x1, y1, r, top_only=False):
    """A rectangle with rounded corners; top_only rounds only the upper two."""
    rb = 0 if top_only else r
    return ('M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z' % (
        f(x0 + r), f(y0), f(x1 - r), f(y0), f(x1), f(y0), f(x1), f(y0 + r), f(x1), f(y1 - rb), f(x1), f(y1),
        f(x1 - rb), f(y1), f(x0 + rb), f(y1), f(x0), f(y1), f(x0), f(y1 - rb), f(x0), f(y0 + r), f(x0), f(y0),
        f(x0 + r), f(y0)))


def arch(x0, top, x1, foot, steps=8):
    """An arched opening's outline: straight sides, a round head."""
    r = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    head = [(cx - r * math.cos(math.pi * k / steps), top + r - r * math.sin(math.pi * k / steps))
            for k in range(steps + 1)]
    return [(x0, foot)] + head + [(x1, foot)]


def gear_points(cx, cy, r, teeth=8, depth=0.7):
    """A cog's outline: teeth stepping between the outer radius and the root."""
    out = []
    for k in range(teeth):
        a = 2 * math.pi * k / teeth
        step = 2 * math.pi / teeth
        for da, rr in ((-0.3, depth), (-0.16, 1.0), (0.16, 1.0), (0.3, depth)):
            out.append((cx + r * rr * math.cos(a + da * step), cy + r * rr * math.sin(a + da * step)))
    return out


def gear(svg, cx, cy, r, name='gear'):
    """A polished brass cog medallion lit from above, as the reference paints them: ten short teeth outlined once,
    in LINE, bright gold shading to the body tone down the cog, a thin dark ring round a gold rim, and inside it a
    big teal glass window, half the cog across, with a pale sheen along its upper edge and a glint, round a brass hub."""
    teeth = gear_teeth(r)
    ring_w = max(r * 0.08, MIN_DETAIL)      # the dark ring and the gold disc each at least a screen px wide, so a
    ring_r = r * 0.62                       # small gear's rings don't blur into one
    disc_r = ring_r - ring_w
    face_r = disc_r - ring_w
    svg.open(name)
    svg.path(poly(gear_points(cx, cy, r, teeth=teeth, depth=GEAR_ROOT)), (GOLD['lit'], GOLD['body'], cy - r, cy + r),
             line_of(GOLD['shade']), LINE, name='cog')
    svg.path(circle(cx, cy, ring_r), GOLD['shade'], name='cog ring')
    svg.path(circle(cx, cy, disc_r), (GOLD['lit'], GOLD['body'], cy - disc_r, cy + disc_r), name='cog disc')
    svg.path(circle(cx, cy, face_r), (GLASS['body'], TEAL['shade'], cy - face_r, cy + face_r), name='cog face')
    s = face_r / 0.46
    sheen = 'M%s,%s A%s,%s 0 0,1 %s,%s A%s,%s 0 0,0 %s,%s Z' % (
        f(cx - s * 0.4), f(cy - s * 0.2), f(s * 0.44), f(s * 0.44), f(cx + s * 0.4), f(cy - s * 0.2),
        f(s * 0.34), f(s * 0.34), f(cx - s * 0.4), f(cy - s * 0.2))
    svg.path(sheen, mix(GLASS['lit'], '#ffffff', 0.6), name='cog sheen')
    svg.path(circle(cx, cy, max(r * 0.14, MIN_DETAIL)), GOLD['lit'], name='cog hub')
    svg.path(circle(cx + face_r * 0.5, cy - face_r * 0.5, max(r * 0.14, MIN_DETAIL)), mix(GLASS['lit'], '#ffffff', 0.8),
             name='cog glint')
    svg.close()


def gear_teeth(r):
    """How many teeth a gear of radius r has: GEAR_TEETH on the cab's gear, fewer on a smaller one so every tooth
    keeps the cab gear's pitch and reads at the screen size; never fewer than GEAR_TEETH_MIN."""
    pitch = 2 * math.pi * GEARS['train-cab-gear'] / GEAR_TEETH
    return max(GEAR_TEETH_MIN, round(2 * math.pi * r / pitch))


def swag(svg, x0, x1, y, dip, name='swag', y1=None):
    """A red bunting ribbon hung between two points, sagging dip px in the middle; y1 is the far end's height when
    it differs from the near end's."""
    cx = (x0 + x1) / 2
    y1 = y if y1 is None else y1
    d = 'M%s,%s Q%s,%s %s,%s' % (f(x0), f(y), f(cx), f(max(y, y1) + 2 * dip), f(x1), f(y1))
    svg.stroke(d, line_of(RED['shade']), 4.8 + 2 * EDGE, name=name + ' outline')
    svg.stroke(d, mix(RED['body'], MAROON['shade'], 0.3), 4.8, name=name)
    for x, ty in ((x0, y), (x1, y1)):
        svg.path(circle(x, ty, 3.0), GOLD['body'], line_of(GOLD['shade']), DETAIL_LINE, name=name + ' tassel')



# ================================================================ towers: what stands on the boiler and the roofs

def foot_curve(cx, a, top, r=None, steps=16):
    """The near half of the foot of a tower of half width a standing at x cx on a barrel of radius r whose top line
    is at y top, from its front corner round to its rear corner: where the tower's cylinder meets the barrel, the
    foot drops below the top line towards the near flank, and the oblique view shifts the near side down and left.
    r None is a flat top: the foot is the near half of the ring the view makes of it."""
    pts = []
    for k in range(steps + 1):
        th = math.pi * k / steps
        z = a * math.sin(th)
        drop = SADDLE_SOFTEN * (r - math.sqrt(max(0.0, r * r - z * z))) if r else 0
        x, y = project(cx + a * math.cos(th), top + drop, -z)
        if pts and x > pts[-1][0]:
            break
        pts.append((x, y))
    return pts + [(cx - a, top)]


def foot_y(curve, x):
    """The foot's y at x, between its samples."""
    for (x1, y1), (x0, y0) in zip(curve, curve[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0) if x1 > x0 else 0
            return y0 + (y1 - y0) * t
    return curve[0][1] if x > curve[0][0] else curve[-1][1]


def between(curve, x0, x1):
    """The foot's points from x1 back to x0, x1 > x0, with the ends interpolated."""
    return [(x1, foot_y(curve, x1))] + [(x, y) for x, y in curve if x0 < x < x1] + [(x0, foot_y(curve, x0))]


def saddle(svg, cx, a, top, r, flare, name='saddle'):
    """The flared brass foot a tower of half width a is seated by: a lip that spreads flare px wider as it meets
    the barrel of radius r (None for a flat top), its lower edge the foot curve it wraps with no outline across
    the join and a soft shadow under it, so the tower reads as built into what it stands on rather than set on it."""
    y0 = top - flare - 1
    curve = foot_curve(cx, a + flare, top, r)
    d = 'M%s,%s L%s,%s Q%s,%s %s,%s ' % (f(cx - a), f(y0), f(cx + a), f(y0), f(cx + a), f(top - 1),
                                        f(curve[0][0]), f(curve[0][1]))
    d += ' '.join('L%s,%s' % (f(x), f(y)) for x, y in curve[1:])
    d += ' Q%s,%s %s,%s Z' % (f(cx - a), f(top - 1), f(cx - a), f(y0))
    svg.path(poly(curve + [(x, y + 2) for x, y in reversed(curve)]), INK, name=name + ' shadow', extra=' fill-opacity="0.18"')
    svg.path(d, (GOLD['lit'], GOLD['shade'], y0, top + flare), name=name)
    svg.stroke('M%s,%s L%s,%s Q%s,%s %s,%s M%s,%s Q%s,%s %s,%s' % (
        f(cx - a), f(y0), f(cx + a), f(y0), f(cx + a), f(top - 1), f(curve[0][0]), f(curve[0][1]), f(cx - a), f(y0),
        f(cx - a), f(top - 1), f(curve[-1][0]), f(curve[-1][1])), line_of(GOLD['shade']), DETAIL_LINE, name=name + ' edge')
    svg.path(poly([(cx + a * 0.3, y0 + 0.8), (cx + a * 0.7, y0 + 0.8), (cx + a * 0.75, top - 1.5), (cx + a * 0.35, top - 1.5)]),
             GOLD['lit'], name=name + ' sheen')


def cylinder_bands(svg, cx, a, y_top, curve, colours, name):
    """The shading of an upright cylinder from y_top down to its foot: a shade band up its left, a lit band and a
    highlight up its right, each ending on the foot curve."""
    def band(x0, x1, fill, opacity, label):
        pts = [(x0, y_top), (x1, y_top)] + between(curve, x0, x1)
        svg.path(poly(pts), fill, name=name + ' ' + label, extra=' fill-opacity="%s"' % opacity)
    band(cx - a, cx - a * 0.45, colours['deep'] if 'deep' in colours else colours['shade'], 0.7, 'shade')
    band(cx - a * 0.45, cx - a * 0.1, colours['shade'], 0.3, 'half shade')
    band(cx + a * 0.3, cx + a * 0.8, colours['lit'], 0.55, 'lit')
    band(cx + a * 0.45, cx + a * 0.62, mix(colours['lit'], '#ffffff', 0.7), 0.9, 'highlight')


def crown(svg, cx, a, top, height, colours, name, onion=False):
    """A rounded cap on a cylinder: a half ellipse a wide and height tall whose foot is at top + height, or an onion
    that swells out past the cylinder and draws up to a point, shaded down its left and lit on its upper right."""
    y = top + height
    if onion:
        d = 'M%s,%s C%s,%s %s,%s %s,%s C%s,%s %s,%s %s,%s Z' % (
            f(cx - a), f(y), f(cx - a * 1.1), f(y - height * 0.8), f(cx - a * 0.2), f(y - height * 0.7), f(cx), f(top),
            f(cx + a * 0.2), f(y - height * 0.7), f(cx + a * 1.1), f(y - height * 0.8), f(cx + a), f(y))
        shade = 'M%s,%s C%s,%s %s,%s %s,%s L%s,%s Z' % (
            f(cx - a), f(y), f(cx - a * 1.1), f(y - height * 0.8), f(cx - a * 0.2), f(y - height * 0.7), f(cx), f(top),
            f(cx - a * 0.25), f(y))
    else:
        d = 'M%s,%s A%s,%s 0 0,1 %s,%s Z' % (f(cx - a), f(y), f(a), f(height), f(cx + a), f(y))
        shade = 'M%s,%s A%s,%s 0 0,1 %s,%s L%s,%s A%s,%s 0 0,0 %s,%s Z' % (
            f(cx - a), f(y), f(a), f(height), f(cx - a * 0.2), f(top + height * 0.1), f(cx - a * 0.2), f(y),
            f(a * 0.5), f(height * 0.9), f(cx - a * 0.5), f(y))
    svg.path(d, (colours['lit'], colours['body'], top, y), line_of(colours['shade']), LINE, name=name)
    svg.path(shade, colours['shade'], name=name + ' shade', extra=' fill-opacity="0.6"')
    svg.path('M%s,%s Q%s,%s %s,%s' % (f(cx + a * 0.1), f(top + height * 0.12), f(cx + a * 0.55), f(top + height * 0.15),
                                      f(cx + a * 0.7), f(top + height * 0.55)), 'none', mix(colours['lit'], '#ffffff', 0.75),
             2.4, name=name + ' sheen')


def knob(svg, cx, cy, r, name='knob'):
    """A brass ball: its dark edge is a larger disc under it rather than a stroke, so small knobs keep a fill."""
    svg.path(circle(cx, cy, r + EDGE), line_of(GOLD['shade']), name=name + ' edge')
    svg.path(circle(cx, cy, r), (GOLD['lit'], GOLD['shade'], cy - r, cy + r), name=name)
    if r >= 3:
        svg.path(circle(cx + r * 0.3, cy - r * 0.3, r * 0.4), GOLD['lit'], name=name + ' glint')


def tower_body(svg, cx, a, y_top, curve, colours, name):
    """An upright cylinder's side from y_top down to its foot curve, in the body tone, outlined, shaded."""
    pts = [(cx - a, y_top), (cx + a, y_top)] + curve
    svg.path(poly(pts), colours['body'], line_of(colours['shade']), LINE, name=name)
    cylinder_bands(svg, cx, a, y_top, curve, colours, name)


def gold_ring(svg, cx, a, y0, y1, curve=None, name='ring'):
    """A brass band round a tower between y0 and y1; following the foot curve below if one is given."""
    if curve is None:
        pts = [(cx - a, y0), (cx + a, y0), (cx + a, y1), (cx - a, y1)]
    else:
        pts = [(cx - a, y0), (cx + a, y0)] + [(x, y + (y1 - y0)) for x, y in curve]
    svg.path(poly(pts), (GOLD['lit'], GOLD['shade'], y0, y1), line_of(GOLD['shade']), DETAIL_LINE, name=name)
    svg.path(poly([(cx + a * 0.3, y0 + 0.8), (cx + a * 0.7, y0 + 0.8), (cx + a * 0.7, y1 - 0.8), (cx + a * 0.3, y1 - 0.8)]),
             GOLD['lit'], name=name + ' sheen')


def bell_dome(svg, cx, top, a, base_top, r, name, lantern=False):
    """A brass bell dome standing on a barrel: a cylinder (with a band of green lantern glass if lantern) seated by
    a flared foot, a domed crown and a finial knob."""
    svg.open(name)
    curve = foot_curve(cx, a, base_top, r)
    crown_h = a * 1.1
    tower_body(svg, cx, a, top + crown_h, curve, GOLD, 'dome')
    saddle(svg, cx, a, base_top, r, a * 0.3)
    if lantern:
        y0, y1 = top + crown_h + 2.5, top + crown_h + 10.5
        svg.path(poly([(cx - a + 1.5, y0), (cx + a - 1.5, y0), (cx + a - 1.5, y1), (cx - a + 1.5, y1)]),
                 ('#b9f0a6', '#3f9a58', y0, y1), line_of(GOLD['shade']), DETAIL_LINE, name='lantern glass')
        for k in range(1, 3):
            x = cx - a + 1.5 + (2 * a - 3) * k / 3
            svg.stroke('M%s,%s L%s,%s' % (f(x), f(y0 + 0.5), f(x), f(y1 - 0.5)), GOLD['shade'], DETAIL_LINE, name='lantern bar')
        svg.path(poly([(cx + 1.5, y0 + 1), (cx + a - 4, y0 + 1), (cx + a - 4, y0 + 3), (cx + 1.5, y0 + 3)]), '#e4ffd8',
                 name='lantern glint')
        gold_ring(svg, cx, a + 0.5, y1, y1 + 3, name='lantern ring')
        gold_ring(svg, cx, a + 0.5, y0 - 3, y0, name='lantern ring')
    crown(svg, cx, a, top, crown_h, GOLD, 'crown', onion=True)
    knob(svg, cx, top - 1.5, 3.2, name='finial')
    svg.close()


def topper(svg, cx, ridge_y, a, name='topper'):
    """A small brass finial on a roof's ridge: a gold ball on a short gold stub, all gold so it reads as one simple
    piece at the screen size."""
    svg.open(name)
    svg.path(poly([(cx - a * 0.6, ridge_y - 3), (cx + a * 0.6, ridge_y - 3), (cx + a, ridge_y + 3), (cx - a, ridge_y + 3)]),
             GOLD['body'], line_of(GOLD['shade']), DETAIL_LINE, name='stub')
    knob(svg, cx, ridge_y - 4.5, a * 0.75)
    svg.close()


# ================================================================ carriages

def roof_edge(x0, x1, top, eave, curve):
    """The near edge of a domed roof from x0 to x1, as points: up from the eave at each end to the crown."""
    pts = []
    steps = 6
    for k in range(steps + 1):
        t = k / steps
        pts.append((x0 - 1 + (curve + 1) * t, eave - (eave - top) * math.sin(math.pi / 2 * t)))
    for k in range(steps + 1):
        t = k / steps
        pts.append((x1 - curve + (curve + 1) * t, top + (eave - top) * (1 - math.cos(math.pi / 2 * t))))
    return pts


def roof(svg, x0, x1, top, eave, curve, name):
    """A barrel-vaulted roof seen a little from above, one rounded silhouette: the ridge shows RIDGE_LIFT above the
    crown of the near edge, lit, with the same end curves as the near edge so the roof's two ends mirror each other
    (a receding end face would peak at one end only); below the crown the near flank darkens down to the gold eave
    band, the bottom of the one silhouette, its ends the roof's ends; a brass rail is seated along the ridge; one
    outline runs round the whole."""
    edge = roof_edge(x0, x1, top, eave, curve)
    ridge = [(x, y - RIDGE_LIFT) for x, y in edge[2:12]]
    trim_top, trim_bottom = eave - 4, eave + 1
    whole = edge[:3] + ridge + edge[11:] + [(x1 + 1, trim_bottom), (x0 - 1, trim_bottom)]
    svg.open(name)
    svg.path(poly(whole), (MAROON['body'], MAROON['shade'], top, trim_top), name='roof flank')
    svg.path(poly(ridge + list(reversed(edge[2:12]))), (mix(MAROON['lit'], '#ffffff', 0.25), MAROON['body'], top - RIDGE_LIFT, top + 1),
             name='roof top')
    rail = ridge[2:8]
    svg.path(poly([(x, y - 1.6) for x, y in rail] + [(x, y + 1.6) for x, y in reversed(rail)]),
             (GOLD['lit'], GOLD['shade'], top - RIDGE_LIFT - 1.6, top - RIDGE_LIFT + 1.6), line_of(GOLD['shade']), DETAIL_LINE,
             name='ridge trim')
    svg.path(poly([(x0 - 1, trim_top), (x1 + 1, trim_top), (x1 + 1, trim_bottom), (x0 - 1, trim_bottom)]),
             (GOLD['lit'], GOLD['shade'], trim_top, trim_bottom), name='eave trim')
    svg.path(poly([(x0, trim_top + 1), (x1, trim_top + 1), (x1, trim_top + 2.5), (x0, trim_top + 2.5)]), GOLD['lit'],
             name='eave trim sheen')
    svg.stroke('M%s,%s L%s,%s' % (f(x0 - 1), f(trim_top), f(x1 + 1), f(trim_top)), line_of(GOLD['shade']), DETAIL_LINE,
               name='eave trim edge')
    svg.path(poly(whole), 'none', line_of(MAROON['body']), LINE, name='roof outline')
    svg.close()


def carriage_roof(svg, x0, x1):
    roof(svg, x0, x1, CAR_ROOF_TOP, CAR_EAVE, 16, 'roof')
    for cx in (x0 + TOPPER_IN, x1 - TOPPER_IN):
        topper(svg, cx, CAR_ROOF_TOP - RIDGE_LIFT, TOPPER_HALF)


def carriage_window(svg, cx):
    half = WINDOW_W / 2
    frame = arch(cx - half - 2.5, WINDOW_TOP - 2.5, cx + half + 2.5, WINDOW_SILL + 2)
    svg.path(poly(frame), GOLD['body'], name='window frame')
    pane = arch(cx - half, WINDOW_TOP, cx + half, WINDOW_SILL)
    svg.path(poly(pane), GLASS['body'], name='pane')
    svg.path(poly([(cx - half + 1, WINDOW_TOP + 4), (cx + half - 1, WINDOW_TOP + 4), (cx + half - 1, WINDOW_TOP + 7),
                   (cx - half + 1, WINDOW_TOP + 7)]), mix(GLASS['lit'], GLASS['body'], 0.5), name='pane light')
    svg.path(poly([(cx - half, WINDOW_SILL), (cx - half, WINDOW_TOP + half + 1), (cx + half * 0.2, WINDOW_SILL)]),
             GLASS['shade'], name='pane shade', extra=' fill-opacity="0.25"')


def carriage_door(svg, x0):
    """A narrow door with its own arched window, x0 its rear edge; one stands in from each end."""
    svg.path(poly([(x0, CAR_EAVE + 1), (x0 + 10, CAR_EAVE + 1), (x0 + 10, CAR_SKIRT - 1), (x0, CAR_SKIRT - 1)]),
             CREAM['shade'], line_of(CREAM['shade']), DETAIL_LINE, name='door')
    svg.path(poly(arch(x0 + 2, WINDOW_TOP + 1, x0 + 8, WINDOW_SILL)), (GLASS['lit'], GLASS['body'], WINDOW_TOP, WINDOW_SILL),
             name='door pane')


def carriage_end(svg, x1):
    """The carriage's front end wall, the dark face the oblique view shows ahead of its front edge."""
    svg.path(poly(front_face(x1, CAR_EAVE + 1, CAR_SKIRT)), mix(TEAL['deep'], TEAL['shade'], 0.5),
             line_of(TEAL['shade']), DETAIL_LINE, name='end wall')
    (gx, gy), = recede([(x1, CAR_EAVE + 6)], DEPTH * 0.5)
    svg.path(poly([(x1 + 2, CAR_EAVE + 5), (gx, gy), (gx, gy + 12), (x1 + 2, CAR_EAVE + 17)]), GLASS['shade'],
             name='end window')


def banner(svg, x0, x1):
    """A green banner hung from a gold rod below the belt, its swallowtail reaching under the skirt."""
    mid = (x0 + x1) / 2
    flag = [(x0, CAR_BELT - 1), (x1, CAR_BELT - 1), (x1, CAR_SKIRT + 7), (mid, CAR_SKIRT + 2), (x0, CAR_SKIRT + 7)]
    svg.path(poly(flag), (OLIVE['lit'], OLIVE['body'], CAR_BELT, CAR_SKIRT + 7), line_of(OLIVE['shade']), DETAIL_LINE,
             name='banner')
    svg.path(poly([(x0 - 1, CAR_BELT - 3), (x1 + 1, CAR_BELT - 3), (x1 + 1, CAR_BELT), (x0 - 1, CAR_BELT)]),
             GOLD['body'], name='banner rod')
    svg.path(poly([(x0 + 2, CAR_BELT + 1), (x1 - 2, CAR_BELT + 1), (x1 - 2, CAR_BELT + 3.5), (x0 + 2, CAR_BELT + 3.5)]),
             mix(OLIVE['lit'], '#ffffff', 0.3), name='banner light')


def carriage_body(svg, x0, x1):
    """The body, the same end to end: a door in from each end, three windows about the middle, a swag each side
    of the middle where the medallion gear, its own part, hangs, and a banner at each end."""
    svg.open('body')
    svg.path(poly([(x0, CAR_EAVE), (x1, CAR_EAVE), (x1, CAR_BELT), (x0, CAR_BELT)]), CREAM['body'], name='upper body')
    svg.path(poly([(x0, CAR_EAVE), (x0 + 6, CAR_EAVE), (x0 + 6, CAR_BELT), (x0, CAR_BELT)]), CREAM['shade'],
             name='upper shade', extra=' fill-opacity="0.6"')
    svg.path(poly([(x0, CAR_EAVE), (x1, CAR_EAVE), (x1, CAR_EAVE + 4), (x0, CAR_EAVE + 4)]), INK,
             name='eave shadow', extra=' fill-opacity="0.22"')
    svg.path(poly([(x0, CAR_BELT), (x1, CAR_BELT), (x1, CAR_SKIRT), (x0, CAR_SKIRT)]),
             (OLIVE['body'], mix(OLIVE['shade'], INK, 0.15), CAR_BELT, CAR_SKIRT), name='lower body')
    svg.path(poly([(x0, CAR_BELT), (x0 + 6, CAR_BELT), (x0 + 6, CAR_SKIRT), (x0, CAR_SKIRT)]), OLIVE['shade'],
             name='lower shade', extra=' fill-opacity="0.5"')
    svg.path(poly([(x1 - 4, CAR_EAVE), (x1, CAR_EAVE), (x1, CAR_SKIRT), (x1 - 4, CAR_SKIRT)]),
             CREAM['lit'], name='lit end', extra=' fill-opacity="0.35"')
    svg.path(poly([(x0, CAR_EAVE), (x1, CAR_EAVE), (x1, CAR_SKIRT), (x0, CAR_SKIRT)]), 'none',
             line_of(TEAL['body']), LINE, name='body outline')
    svg.close()
    svg.open('windows')
    carriage_door(svg, x0 + DOOR_IN)
    carriage_door(svg, x1 - DOOR_IN - 10)
    for at in WINDOW_AT:
        carriage_window(svg, x0 + at)
    svg.close()
    svg.path(poly([(x0, CAR_BELT - 1.5), (x1, CAR_BELT - 1.5), (x1, CAR_BELT + 2), (x0, CAR_BELT + 2)]),
             GOLD['body'], name='belt')
    svg.path(poly([(x0, CAR_SKIRT - 3.5), (x1, CAR_SKIRT - 3.5), (x1, CAR_SKIRT - 1), (x0, CAR_SKIRT - 1)]),
             GOLD['shade'], name='skirt trim')
    cx = x0 + WINDOW_AT[1]
    svg.open('bunting')
    swag(svg, x0 + 10, cx, CAR_BELT + 3.5, 3.5, y1=CAR_BELT + 11)
    swag(svg, cx, x1 - 10, CAR_BELT + 11, 3.5, y1=CAR_BELT + 3.5)
    svg.close()
    carriage_end(svg, x1)
    banner(svg, x0 + 1, x0 + 14)
    banner(svg, x1 - 14, x1 - 1)


def carriage_underframe(svg, x0, x1):
    """The dark frame under the skirt the wheels sit in: a bogie frame round each wheel, the steps and the coupling
    hook at each end."""
    svg.open('underframe')
    svg.path(poly(front_face(x1 - 4, CAR_SKIRT, CAR_UNDER)), DARK['body'], name='frame front')
    svg.path(poly([(x0 + 2, CAR_SKIRT), (x1 - 4, CAR_SKIRT), (x1 - 4, CAR_UNDER), (x0 + 2, CAR_UNDER)]), DARK['lit'],
             name='frame')
    r = WHEELS['train-carriage-wheel']
    for wx, _ in axles('train-carriage-wheel'):
        if x0 <= wx <= x1:
            svg.path(rrect(wx - r - 5, CAR_UNDER - 1, wx + r + 5, CAR_UNDER + 2.5, 1.5), DARK['body'], name='bogie')
            svg.path(poly([(wx - r - 3, CAR_UNDER + 0.5), (wx + r + 3, CAR_UNDER + 0.5), (wx + r + 3, CAR_UNDER + 3),
                           (wx - r - 3, CAR_UNDER + 3)]), DARK['lit'], name='bogie edge')
    for x in (x0 + 4, x1 - 8):
        svg.path(poly([(x, CAR_SKIRT + 1), (x + 4, CAR_SKIRT + 1), (x + 4, CAR_UNDER + 4), (x, CAR_UNDER + 4)]),
                 GOLD['shade'], name='step')
    svg.path(poly([(x0 - 7, CAR_SKIRT - 9), (x0 + 2, CAR_SKIRT - 9), (x0 + 2, CAR_SKIRT + 1), (x0 - 7, CAR_SKIRT + 1)]),
             DARK['lit'], name='coupling')
    svg.path(poly([(x0 - 7, CAR_SKIRT - 4), (x0 + 2, CAR_SKIRT - 4), (x0 + 2, CAR_SKIRT - 2), (x0 - 7, CAR_SKIRT - 2)]),
             DARK['body'], name='coupling bar')
    svg.close()


def carriage(svg, k, x0):
    x1 = x0 + CARRIAGE_W
    svg.open('train carriage %d' % k)
    carriage_underframe(svg, x0, x1)
    carriage_body(svg, x0, x1)
    carriage_roof(svg, x0, x1)
    svg.close()


# ================================================================ locomotive

def underframe(svg):
    """The dark frame under the running board, over the wheels' tops."""
    x0, x1, top, bottom = FRAME
    svg.path(poly(front_face(x1 - 6, bottom, UNDERFRAME_BOTTOM)), DARK['body'], name='underframe front')
    svg.path(poly([(x0 + 4, bottom), (x1 - 6, bottom), (x1 - 6, UNDERFRAME_BOTTOM), (x0 + 4, UNDERFRAME_BOTTOM)]),
             DARK['lit'], name='underframe')


def running_board(svg):
    """The running board the boiler and cab stand on: its top face showing behind its near edge, its gold side, and
    the rear buffer."""
    x0, x1, top, bottom = FRAME
    svg.path(poly(top_face([(x0, top), (x1, top)])), TEAL['shade'], line_of(TEAL['shade']), DETAIL_LINE,
             name='running board top')
    svg.path(poly([(x0, top), (x1, top), (x1, bottom), (x0, bottom)]), (GOLD['body'], GOLD['shade'], top, bottom),
             line_of(GOLD['shade']), LINE, name='running board')
    svg.path(poly([(x0 + 1, top + 1), (x1 - 1, top + 1), (x1 - 1, top + 3), (x0 + 1, top + 3)]), GOLD['lit'],
             name='running board trim')
    svg.path(poly([(x0 - 3, top + 1), (x0 + 1, top + 1), (x0 + 1, bottom + 4), (x0 - 3, bottom + 4)]), DARK['shade'],
             name='rear buffer')


def buffer_beam(svg):
    """The gold beam across the loco's front: its own side over the running board's end, its face ahead of
    everything below the smokebox; the pilot hangs from its underside."""
    x0, x1, top, bottom = FRAME
    svg.open('buffer beam')
    svg.path(poly([(BEAM_BACK, top - 1), (x1, top - 1), (x1, bottom + 1), (BEAM_BACK, bottom + 1)]),
             (GOLD['body'], GOLD['shade'], top, bottom), line_of(GOLD['shade']), LINE, name='beam side')
    svg.path(poly([(BEAM_BACK + 1, top + 0.4), (x1, top + 0.4), (x1, top + 2.4), (BEAM_BACK + 1, top + 2.4)]), GOLD['lit'],
             name='beam side sheen')
    svg.path(poly(front_face(x1, top - 1, bottom + 1, DEPTH / 2)), (GOLD['body'], GOLD['shade'], top, bottom),
             line_of(GOLD['shade']), LINE, name='beam face')
    (lx, ly), = recede([(x1, top)], DEPTH / 2)
    svg.path(poly([(x1 + 1, top + 0.4), (lx - 1, ly + 0.4), (lx - 1, ly + 2.4), (x1 + 1, top + 2.4)]), GOLD['lit'],
             name='beam sheen')
    svg.close()


def cab(svg):
    x0, x1 = CAB
    svg.open('cab')
    svg.path(poly(front_face(x1, CAB_EAVE, CAB_FLOOR, DEPTH / 4)), (TEAL['body'], TEAL['shade'], CAB_EAVE, CAB_FLOOR),
             line_of(TEAL['shade']), DETAIL_LINE, name='cab front')    # shallow, so its top stays under the roof's overhang
    svg.path(poly([(x0, CAB_EAVE), (x1, CAB_EAVE), (x1, CAB_FLOOR), (x0, CAB_FLOOR)]),
             (OLIVE['lit'], OLIVE['body'], CAB_SILL, CAB_FLOOR), name='cab wall')
    svg.path(poly([(x0, CAB_EAVE), (x1, CAB_EAVE), (x1, CAB_SILL), (x0, CAB_SILL)]),
             (TEAL['body'], TEAL['shade'], CAB_EAVE, CAB_SILL), name='cab upper wall')
    svg.path(poly([(x0, CAB_EAVE), (x0 + 5, CAB_EAVE), (x0 + 5, CAB_FLOOR), (x0, CAB_FLOOR)]), TEAL['deep'],
             name='cab shade', extra=' fill-opacity="0.5"')
    svg.path(poly([(x0, CAB_EAVE), (x1, CAB_EAVE), (x1, CAB_EAVE + 4), (x0, CAB_EAVE + 4)]), INK, name='cab eave shadow',
             extra=' fill-opacity="0.22"')
    svg.path(poly([(x1 - 3, CAB_EAVE), (x1, CAB_EAVE), (x1, CAB_FLOOR), (x1 - 3, CAB_FLOOR)]), TEAL['lit'],
             name='cab lit edge', extra=' fill-opacity="0.5"')
    svg.path(poly([(x0, CAB_SILL - 1.5), (x1, CAB_SILL - 1.5), (x1, CAB_SILL + 2), (x0, CAB_SILL + 2)]), GOLD['body'],
             name='cab belt')
    svg.path(poly([(x0 + 3, CAB_FLOOR - 4), (x1 - 3, CAB_FLOOR - 4), (x1 - 3, CAB_FLOOR - 1.5), (x0 + 3, CAB_FLOOR - 1.5)]),
             GOLD['shade'], name='cab skirt trim')
    for wx0, wtop, wx1, wsill in CAB_WINDOWS:
        svg.path(rrect(wx0 - 3, wtop - 3, wx1 + 3, wsill + 1, 2), GOLD['body'], line_of(GOLD['shade']), DETAIL_LINE,
                 name='cab window frame')
        svg.path(rrect(wx0, wtop, wx1, wsill - 1, 1), (GLASS['body'], GLASS['shade'], wtop, wsill), name='cab pane')
        svg.path(poly([(wx0 + 2, wtop + 2), (wx1 - 2, wtop + 2), (wx1 - 2, wtop + 5), (wx0 + 2, wtop + 5)]),
                 mix(GLASS['lit'], GLASS['body'], 0.5), name='cab pane glint')
    svg.path(poly([(x0, CAB_EAVE), (x1, CAB_EAVE), (x1, CAB_FLOOR), (x0, CAB_FLOOR)]), 'none', line_of(TEAL['body']),
             LINE, name='cab outline')
    svg.close()


def cab_roof(svg):
    roof(svg, CAB[0] - 5, CAB[1] + 5, CAB_ROOF_TOP, CAB_EAVE, 12, 'cab roof')


def hoop(svg, bx, top, bottom, cy):
    """An upright gold hoop round a barrel between y top and bottom, HOOP_HALF either side of x bx: it stands a
    little proud of the barrel with rounded ends, lit above and shaded under the belly from y cy + 3 down."""
    svg.path(rrect(bx - HOOP_HALF, top - 1, bx + HOOP_HALF, bottom + 1, 1.5), (GOLD['lit'], GOLD['body'], top, cy + 3),
             line_of(GOLD['shade']), DETAIL_LINE, name='band')
    svg.path(poly([(bx - HOOP_HALF, cy + 3), (bx + HOOP_HALF, cy + 3), (bx + HOOP_HALF, bottom - 0.5), (bx - HOOP_HALF, bottom - 0.5)]),
             (GOLD['body'], GOLD['deep'], cy + 3, bottom), name='band shade')
    svg.path(poly([(bx - HOOP_HALF + 1.5, top + 1), (bx + HOOP_HALF - 1.5, top + 1), (bx + HOOP_HALF - 1.5, top + 4),
                   (bx - HOOP_HALF + 1.5, top + 4)]), mix(GOLD['lit'], '#ffffff', 0.5), name='band sheen')


def belt(svg, x0, x1, cy, hoops):
    """The thin gold belt along the boiler's middle from x0 to x1, lengthwise at y cy, a rivet between each pair of
    hoops; the hoops are drawn over it."""
    svg.path(rrect(x0, cy - BELT_HALF, x1, cy + BELT_HALF, 1), (GOLD['lit'], GOLD['shade'], cy - BELT_HALF, cy + BELT_HALF),
             line_of(GOLD['shade']), DETAIL_LINE, name='belt')
    edges = [x0] + list(hoops) + [x1]
    for a, b in zip(edges, edges[1:]):
        svg.path(circle((a + b) / 2, cy, RIVET_R + EDGE), line_of(GOLD['shade']), name='rivet edge')
        svg.path(circle((a + b) / 2, cy, RIVET_R), GOLD['lit'], name='rivet')


def boiler(svg):
    """The boiler barrel: a cylinder shaded in flat bands, bright mint along its top and dark from its middle down
    under its belly, its top line straight so the towers' feet rest on it; a thin riveted gold belt runs along its
    middle, and three gold hoops round it, crossing the belt, stand a little proud of the barrel."""
    x0, x1, cy, r = BOILER
    top, bottom = cy - r, cy + r
    svg.open('boiler')
    svg.path(poly([(x0, top), (x1, top), (x1, bottom), (x0, bottom)]), (TEAL['lit'], TEAL['deep'], top, bottom),
             name='barrel')
    edges = [x0] + list(BOILER_BANDS) + [x1]
    for a, b in zip(edges, edges[1:]):
        svg.path(poly([(a, top), (b, top), (b, bottom), (a, bottom)]), (TEAL['body'], TEAL['deep'], cy - 6, bottom),
                 line_of(TEAL['body']), LINE, name='segment')
        svg.path(poly([(a, top), (b, top), (b, cy - 6), (a, cy - 6)]), mix(TEAL['lit'], TEAL['body'], 0.5), name='segment light')
        svg.path(poly([(a + 2, top + 2), (b - 2, top + 2), (b - 2, top + 5), (a + 2, top + 5)]), mix(TEAL['lit'], '#ffffff', 0.35),
                 name='segment sheen')
        svg.path(poly([(a, cy + 3), (b, cy + 3), (b, bottom), (a, bottom)]), TEAL['deep'], name='segment shade')
    belt(svg, x0, SMOKEBOX[0], cy, BOILER_BANDS)
    for bx in BOILER_BANDS:
        hoop(svg, bx, top, bottom, cy)
    svg.close()


def smokebox(svg):
    """The smokebox ahead of the boiler: a short teal barrel a little fatter than the boiler, a hoop like the
    boiler's where it meets it, its front face ringed by a thick gold circle round its maroon door, seen
    foreshortened ahead of it, with a reflector in the middle of the door, as the reference shows."""
    x0, x1, r = SMOKEBOX
    cy = BOILER[2]
    top, bottom = cy - r, cy + r
    svg.open('smokebox')
    svg.path(poly([(x0, top), (x1, top), (x1, bottom), (x0, bottom)]), (TEAL['lit'], TEAL['deep'], top, bottom),
             line_of(TEAL['body']), LINE, name='smokebox')
    svg.path(poly([(x0 + 2, top + 2), (x1 - 2, top + 2), (x1 - 2, top + 4), (x0 + 2, top + 4)]),
             mix(TEAL['lit'], '#ffffff', 0.65), name='smokebox sheen')
    hoop(svg, x0 + HOOP_HALF, top, bottom, cy)
    svg.path(poly(front_ring(x1, cy, r)), (TEAL['shade'], TEAL['deep'], top, bottom), line_of(TEAL['shade']), DETAIL_LINE,
             name='smokebox front')
    svg.open('smokebox door')
    ring_r = r - 3
    svg.path(poly(front_ring(x1, cy, ring_r)), (GOLD['lit'], GOLD['shade'], top, bottom), line_of(GOLD['shade']), DETAIL_LINE,
             name='door rim')
    svg.path(poly(front_ring(x1 + 2, cy - 0.5, ring_r - FRONT_RING)), (MAROON['body'], MAROON['shade'], top, bottom),
             line_of(MAROON['shade']), DETAIL_LINE, name='door')
    svg.path(poly(front_ring(x1 + 2.5, cy - 1, r * 0.42)), (GOLD['lit'], GOLD['body'], cy - r * 0.42, cy + r * 0.42),
             name='door boss')
    svg.path(poly(front_ring(x1 + 2.5, cy - 1, r * 0.22)), ('#fffae0', '#ffe76a', cy - r * 0.22, cy + r * 0.22),
             name='boss lens')
    svg.close()
    svg.close()


def funnel(svg):
    """The funnel on the boiler's front end, in the flat side view the rest of the train keeps: a dusky maroon stem
    tapering up from a flared brass foot, swelling out in a concave flare to a gold cap whose lip spreads a little
    wider at the top, a gold band where the flare begins; its crown is a profile, no mouth seen from above."""
    cx, top = FUNNEL
    base = BOILER[2] - BOILER[3]
    hb, hs, hc = FUNNEL_HALF
    flare_top, flare_bottom = top + 8, top + 15
    lip = 3.5
    svg.open('funnel')
    curve = foot_curve(cx, hb, base, BOILER[3])
    stack = {'lit': mix(MAROON['body'], '#8a5a52', 0.4), 'body': mix(MAROON['shade'], '#5a3a36', 0.4), 'shade': MAROON['deep'],
             'deep': MAROON['deep']}
    svg.path(poly([(cx - hs, flare_bottom), (cx + hs, flare_bottom)] + curve), stack['body'], line_of(stack['shade']), LINE,
             name='stack')
    cylinder_bands(svg, cx, hb, flare_bottom, curve, stack, 'stack')
    saddle(svg, cx, hb, base, BOILER[3], 2.5)
    flare = 'M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z' % (
        f(cx - hc), f(flare_top), f(cx + hc), f(flare_top), f(cx + hs + 1), f(flare_top + 3), f(cx + hs + 1), f(flare_bottom),
        f(cx - hs - 1), f(flare_bottom), f(cx - hs - 1), f(flare_top + 3), f(cx - hc), f(flare_top))
    svg.path(flare, stack['body'], line_of(stack['shade']), LINE, name='flare')
    svg.path('M%s,%s L%s,%s L%s,%s L%s,%s Q%s,%s %s,%s Z' % (
        f(cx - hc), f(flare_top), f(cx - hc * 0.45), f(flare_top), f(cx - hs * 0.45), f(flare_bottom), f(cx - hs - 1),
        f(flare_bottom), f(cx - hs - 1), f(flare_top + 3), f(cx - hc), f(flare_top)), MAROON['deep'], name='flare shade',
        extra=' fill-opacity="0.55"')
    svg.path(poly([(cx + hc * 0.3, flare_top), (cx + hc * 0.75, flare_top), (cx + hs * 0.8, flare_bottom), (cx + hs * 0.3, flare_bottom)]),
             MAROON['lit'], name='flare lit', extra=' fill-opacity="0.55"')
    gold_ring(svg, cx, hs + 1.5, flare_bottom - 1, flare_bottom + 3, name='flare band')
    cap = [(cx - hc, flare_top + 1), (cx - hc, top + lip), (cx - hc - 1, top + lip), (cx - hc - 1, top), (cx + hc + 1, top),
           (cx + hc + 1, top + lip), (cx + hc, top + lip), (cx + hc, flare_top + 1)]
    svg.path(poly(cap), (GOLD['lit'], GOLD['shade'], top, flare_top + 1), line_of(GOLD['shade']), LINE, name='cap')
    svg.path(poly([(cx - hc, top + lip), (cx - hc * 0.5, top + lip), (cx - hc * 0.5, flare_top + 1), (cx - hc, flare_top + 1)]),
             GOLD['shade'], name='cap shade', extra=' fill-opacity="0.45"')
    svg.path(poly([(cx + hc * 0.25, top + 1), (cx + hc * 0.7, top + 1), (cx + hc * 0.7, flare_top), (cx + hc * 0.25, flare_top)]),
             GOLD['lit'], name='cap sheen')
    svg.stroke('M%s,%s L%s,%s' % (f(cx - hc), f(top + lip), f(cx + hc), f(top + lip)), line_of(GOLD['shade']), DETAIL_LINE,
               name='lip edge')
    svg.close()


def headlamp(svg):
    """The brass headlamp drum on a short stalk standing on the smokebox's top, seen from the side, its glass face
    to the front."""
    cx, top, r = HEADLAMP
    base = BOILER[2] - SMOKEBOX[2]
    svg.open('headlamp')
    tower_body(svg, cx, 4.5, top + r, foot_curve(cx, 4.5, base, SMOKEBOX[2]), DARK, 'lamp stand')
    saddle(svg, cx, 4.5, base, SMOKEBOX[2], 2)
    svg.path(circle(cx, top + r, r), (GOLD['lit'], GOLD['shade'], top, top + 2 * r), line_of(GOLD['shade']), LINE,
             name='lamp')
    svg.path(poly(front_ring(cx + r * 0.6, top + r, r * 0.85)), (GOLD['lit'], GOLD['shade'], top, top + 2 * r),
             name='lamp face ring')
    svg.path(poly(front_ring(cx + r * 0.6, top + r, r * 0.62)), ('#fff6cc', '#f3c95a', top, top + 2 * r), name='lamp lens')
    svg.path(poly(front_ring(cx + r * 0.45, top + r - 2, r * 0.25)), '#ffffff', name='lamp glint')
    knob(svg, cx, top - 0.5, 2.5, name='lamp cap')
    svg.close()


def flag_pole(svg):
    """The pole on the cab roof the pennant hangs from; the pennant is its own part."""
    px, top = FLAG_POLE
    svg.open('flag pole')
    svg.path(poly([(px - 1.5, CAB_ROOF_TOP), (px + 1.5, CAB_ROOF_TOP), (px + 1.5, top), (px - 1.5, top)]), GOLD['shade'],
             name='pole')
    knob(svg, px, top - 2, 3.0, name='pole knob')
    svg.close()


def pennant(svg):
    """The swallowtail pennant hung at FLAG_HANG on the pole, streaming back over the cab."""
    svg.open('train flag')
    svg.path(poly(FLAG), TEAL['body'], line_of(TEAL['body']), DETAIL_LINE, name='pennant')
    svg.path(poly([FLAG[0], (FLAG[0][0], FLAG[0][1] + 5), (FLAG[1][0] + 3, FLAG[1][1] + 5), FLAG[1]]), TEAL['lit'],
             name='pennant sheen', extra=' fill-opacity="0.25"')
    gx, gy, gr = FLAG_GEAR
    svg.path(poly(gear_points(gx, gy, gr, teeth=8, depth=0.72)), (GOLD['lit'], GOLD['body'], gy - gr, gy + gr),
             line_of(GOLD['shade']), LINE, name='pennant gear')
    svg.path(circle(gx, gy, gr * 0.38), TEAL['shade'], line_of(GOLD['shade']), DETAIL_LINE, name='pennant gear eye')
    svg.close()


def cylinders(svg):
    """The cylinder block ahead of the driving wheels: one gold drum lying along the track with a maroon head on
    its front, seen foreshortened ahead of it; one drum, since two thin ones blur together at the screen size, its
    maroon head parting it from the gold pilot."""
    x0, x1, top, bottom = CYLINDER
    rr = (bottom - top) / 2
    cy = (top + bottom) / 2
    svg.open('cylinders')
    svg.path(poly([(x0 + 4, UNDERFRAME_BOTTOM - 1), (x1 - 4, UNDERFRAME_BOTTOM - 1), (x1 - 4, top + 4), (x0 + 4, top + 4)]),
             DARK['body'], line_of(DARK['body']), DETAIL_LINE, name='steam chest')
    svg.path(rrect(x0, top, x1, bottom, 4), (GOLD['lit'], GOLD['shade'], top, bottom), line_of(GOLD['shade']), LINE,
             name='cylinder')
    svg.path(rrect(x0 + 1, top, x0 + 6, bottom, 3), (GOLD['body'], GOLD['deep'], top, bottom), name='cylinder band')
    svg.path(poly([(x0 + 7, top + 2), (x1 - 3, top + 2), (x1 - 3, top + 4.5), (x0 + 7, top + 4.5)]), GOLD['lit'],
             name='cylinder sheen')
    svg.path(poly(front_ring(x1, cy, rr)), (MAROON['lit'], MAROON['deep'], top, bottom), line_of(MAROON['shade']),
             DETAIL_LINE, name='cylinder head')
    svg.path(poly(front_ring(x1, cy, rr * 0.4)), GOLD['body'], name='head boss')
    svg.close()


def pilot(svg):
    """The pilot hanging under the buffer beam ahead of the cylinder's head: a gold top rail running flush under
    the beam from its front corner out over the plough, and from the rail a gold-framed grille leaning forward down
    to the rail head, a few bold gold slats hanging in it over the dark between them, as reads best at the screen
    size; every bar is outlined like the beam, so the beam, the rail and the plough read as one front end."""
    near, front_top, front_foot = PILOT
    bar = 3.2
    rail_top = FRAME[3] + 1                           # the beam's bottom edge
    top, foot = rail_top + FRONT_BAR, RAIL_Y - bar / 2 - EDGE   # the foot bar's outline lands on the rail
    near_foot = near - 2
    svg.open('pilot')
    svg.path(poly([(near, top), (front_top, top), (front_foot, foot), (near_foot, foot)]), DARK['body'],
             line_of(DARK['body']), LINE, name='wedge')
    slats = 4
    for k in range(1, slats):
        t = k / slats
        sx, ex = near + (front_top - near) * t, near_foot + (front_foot - near_foot) * t
        d = 'M%s,%s L%s,%s' % (f(sx), f(top + 1), f(ex), f(foot - 1))
        svg.stroke(d, line_of(GOLD['shade']), 2.6 + 2 * EDGE, name='slat outline')
        svg.stroke(d, GOLD['body'], 2.6, name='slat')
    for (ax, ay), (bx, by), w, name in (((near, top + 1), (near_foot, foot - 1), bar, 'near bar'),
                                        ((front_top, top + 1), (front_foot, foot - 1), bar, 'front bar'),
                                        ((near_foot, foot), (front_foot, foot), bar, 'foot bar')):
        svg.stroke('M%s,%s L%s,%s' % (f(ax), f(ay), f(bx), f(by)), line_of(GOLD['shade']), w + 2 * EDGE, name=name + ' outline')
        svg.stroke('M%s,%s L%s,%s' % (f(ax), f(ay), f(bx), f(by)), GOLD['body'], w, name=name)
    svg.path(poly(top_face([(FRAME[1] + 1, rail_top), (front_top + 3, rail_top)], DEPTH / 3)), GOLD['shade'],
             line_of(GOLD['shade']), DETAIL_LINE, name='top rail top')   # fills under the beam face's receding underside
    svg.path(poly([(FRAME[1] + 1, rail_top), (front_top + 3, rail_top), (front_top + 3, top), (FRAME[1] + 1, top)]),
             (GOLD['body'], GOLD['shade'], rail_top, top), line_of(GOLD['shade']), LINE, name='top rail')
    svg.path(poly([(FRAME[1] + 2, rail_top + 0.8), (front_top + 2, rail_top + 0.8), (front_top + 2, rail_top + 2), (FRAME[1] + 2, rail_top + 2)]),
             GOLD['lit'], name='top rail sheen')
    svg.close()


def front_bar(svg):
    """The one gold bar the grille hangs from: it drops from the bottom of the ring round the smokebox's front,
    turns forward and runs on as the pilot's top rail, so the ring, the bar and the grille read as one gold
    assembly, as the reference paints them."""
    x1, cy, r = SMOKEBOX[1], BOILER[2], SMOKEBOX[2]
    rail_y = FRAME[3] + 1 + FRONT_BAR / 2
    d = 'M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s' % (f(x1), f(cy + r - 3), f(x1), f(rail_y - BAR_BEND), f(x1), f(rail_y),
                                               f(x1 + BAR_BEND), f(rail_y), f(PILOT[1] + 3), f(rail_y))
    svg.open('grille bar')
    svg.stroke(d, line_of(GOLD['shade']), FRONT_BAR + 2 * EDGE, name='bar outline')
    svg.stroke(d, GOLD['body'], FRONT_BAR, name='bar')
    svg.stroke('M%s,%s L%s,%s' % (f(x1 + 0.8), f(cy + r - 1), f(x1 + 0.8), f(rail_y - BAR_BEND)), GOLD['lit'], DETAIL_LINE,
               name='bar sheen')
    svg.close()


def loco(svg):
    """The locomotive, built up as a real one is: the frame, the running board, the cab, the boiler and smokebox on
    the board, the cylinders outside the frame under the smokebox, the pilot hung under the buffer beam ahead of
    them, then what stands on top."""
    svg.open('train loco')
    underframe(svg)
    running_board(svg)
    cab(svg)
    cab_roof(svg)
    boiler(svg)
    smokebox(svg)
    cylinders(svg)
    pilot(svg)
    buffer_beam(svg)
    front_bar(svg)
    bell_dome(svg, STEAM_DOME[0], STEAM_DOME[1], STEAM_DOME[2], BOILER[2] - BOILER[3], BOILER[3], 'steam dome')
    funnel(svg)
    headlamp(svg)
    bell_dome(svg, CAB_DOME[0], CAB_DOME[1], CAB_DOME[2], CAB_ROOF_TOP - RIDGE_LIFT, None, 'cab dome')
    flag_pole(svg)
    svg.close()


# ================================================================ wheels and rods

def axles(tid):
    """[(x, y)] sheet px, the axle of every wheel of this size, rear to front."""
    r = WHEELS[tid]
    y = RAIL_Y - r
    if tid == 'train-drive-wheel':
        return [(x, y) for x in DRIVE_AXLE_XS]
    out = []
    for x0 in CARRIAGE_LEFTS:
        x1 = x0 + CARRIAGE_W
        out += [(x0 + at, y) for at in BOGIE_AT] + [(x1 - at, y) for at in reversed(BOGIE_AT)]
    return out + [(x, y) for x in LEAD_AXLE_XS]


def wheel_groups():
    """[(group id on the sheet, template id)] for every wheel drawn, rear to front."""
    out = []
    for tid in WHEELS:
        name = tid.replace('train-', 'train ').replace('-', ' ')
        out += [('%s %d' % (name, k + 1), tid) for k in range(len(axles(tid)))]
    return out


DRAWN_AXLES = {tid: axles(tid)[0] for tid in WHEELS}     # the wheel of each size that is cut out


def spokes(svg, cx, cy, r_in, r_out, count, width):
    for k in range(count):
        a = 2 * math.pi * k / count
        svg.stroke('M%s,%s L%s,%s' % (f(cx + r_in * math.cos(a)), f(cy + r_in * math.sin(a)),
                                      f(cx + r_out * math.cos(a)), f(cy + r_out * math.sin(a))), GOLD['shade'], width,
                   name='spoke')


def drive_wheel(svg, name, cx, cy):
    """A driving wheel: a dark tyre, a brass rim and four bold spokes about a brass hub, every piece centred on the
    axle so the wheel is the same at every turn; the crank pin is the rod's own boss, drawn over the wheel where
    the rod circles."""
    r = WHEELS['train-drive-wheel']
    svg.open(name)
    svg.path(circle(cx, cy, r), DARK['lit'], line_of(DARK['lit']), LINE, name='tyre')
    svg.path(circle(cx, cy, r - 1), (GOLD['lit'], GOLD['shade'], cy - r, cy + r), name='rim')
    svg.path(circle(cx, cy, r - 4), DARK['shade'], name='wheel well')
    spokes(svg, cx, cy, 2.5, r - 3.5, 4, 2.0)
    svg.path(circle(cx, cy, 4), GOLD['body'], name='hub')
    svg.path(circle(cx, cy, 1.5), GOLD['deep'], name='axle')
    svg.close()


def carriage_wheel(svg, name, cx, cy):
    r = WHEELS['train-carriage-wheel']
    svg.open(name)
    svg.path(circle(cx, cy, r), DARK['lit'], line_of(DARK['lit']), LINE, name='tyre')
    svg.path(circle(cx, cy, r - 0.9), (GOLD['lit'], GOLD['shade'], cy - r, cy + r), name='rim')
    svg.path(circle(cx, cy, r - 3.4), DARK['shade'], name='wheel well')
    spokes(svg, cx, cy, 1.5, r - 3.2, 4, 2.0)
    svg.path(circle(cx, cy, 2.4), GOLD['body'], name='hub')
    svg.close()


def wheels(svg):
    draw = {'train-drive-wheel': drive_wheel, 'train-carriage-wheel': carriage_wheel}
    for (gid, tid), (x, y) in zip(wheel_groups(), [a for tid in WHEELS for a in axles(tid)]):
        draw[tid](svg, gid, x, y)


def rod(svg, name, axles_x):
    """A connecting rod joining a pair of driving wheels' crank pins, drawn where the pins point: ahead of the axles."""
    y = RAIL_Y - WHEELS['train-drive-wheel']
    x0, x1 = axles_x[0] + CRANK_R, axles_x[-1] + CRANK_R
    svg.open(name)
    svg.path(rrect(x1, y - ROD_HALF - EDGE, CYLINDER[0] + 8, y + ROD_HALF + EDGE, ROD_HALF), line_of(GOLD['shade']),
             name='piston rod edge')
    svg.path(rrect(x1, y - ROD_HALF + 0.4, CYLINDER[0] + 8, y + ROD_HALF - 0.4, ROD_HALF - 0.4), GOLD['shade'], name='piston rod')
    svg.path(rrect(x0 - 4 - EDGE, y - ROD_HALF - EDGE, x1 + 4 + EDGE, y + ROD_HALF + EDGE, ROD_HALF + EDGE), line_of(GOLD['shade']),
             name='rod edge')
    svg.path(rrect(x0 - 4, y - ROD_HALF, x1 + 4, y + ROD_HALF, ROD_HALF), GOLD['body'], name='rod')
    for x in axles_x:
        svg.path(circle(x + CRANK_R, y, 3.2 + EDGE), line_of(GOLD['shade']), name='rod boss edge')
        svg.path(circle(x + CRANK_R, y, 3.2), GOLD['body'], name='rod boss')
        svg.path(circle(x + CRANK_R, y, 1.5), GOLD['deep'], name='rod pin')
    svg.close()


def rods(svg):
    """One rod per coupled set; only the first is cut, the template places it once per set."""
    for k, pair in enumerate(ROD_PAIRS):
        rod(svg, 'train rod' if k == 0 else 'train rod %d' % (k + 1), pair)


def gear_hubs(tid):
    """[(x, y)] sheet px, the hub of every gear of this size, rear to front."""
    if tid == 'train-cab-gear':
        return [CAB_GEAR]
    return [(x0 + WINDOW_AT[1], CAR_BELT + MEDALLION_DROP) for x0 in CARRIAGE_LEFTS]


def gear_groups():
    """[(group id on the sheet, template id)] for every gear drawn, rear to front."""
    out = []
    for tid in GEARS:
        name = tid.replace('train-', 'train ').replace('-', ' ')
        hubs = gear_hubs(tid)
        out += [(name if len(hubs) == 1 else '%s %d' % (name, k + 1), tid) for k in range(len(hubs))]
    return out


DRAWN_GEARS = {tid: gear_hubs(tid)[0] for tid in GEARS}     # the gear of each size that is cut out


def gears(svg):
    """The gear emblems, each drawn over its body as its own group so the scene can spin it about its hub."""
    for (gid, tid), (x, y) in zip(gear_groups(), [h for tid in GEARS for h in gear_hubs(tid)]):
        gear(svg, x, y, GEARS[tid], name=gid)


def puff(svg, name, cx, cy, lobes):
    """One puff of steam: white lobes, shaded along their undersides, over a soft outline."""
    svg.open(name)
    for x, y, r in lobes:
        svg.path(circle(cx + x, cy + y, r), SMOKE['line'], name='puff outline', extra=' fill-opacity="0.8"')
    for x, y, r in lobes:
        svg.path(circle(cx + x, cy + y + 1, r - 1), SMOKE['shade'], name='puff shade')
    for x, y, r in lobes:
        svg.path(circle(cx + x + 0.5, cy + y - 1, r - 1.6), SMOKE['lit'], name='puff')
    svg.close()


PUFF_LOBES = {
    'train-smoke-1': [(-26, -4, 15), (-6, -10, 19), (14, 2, 13), (2, 9, 15)],
    'train-smoke-2': [(-18, 4, 14), (-2, -12, 17), (16, -2, 15), (-6, 10, 12), (8, 12, 11)],
    'train-smoke-3': [(-22, -8, 12), (-8, 2, 16), (12, -8, 14), (18, 8, 10), (-2, 14, 11)],
    'train-smoke-4': [(-14, 6, 13), (0, -14, 12), (8, 0, 18), (-20, -8, 9), (22, 10, 9)],      # a tall one, peaked
    'train-smoke-5': [(-28, 2, 11), (-12, -6, 15), (6, -4, 17), (24, 4, 12), (0, 12, 13), (-16, 10, 10)],  # a long low one
}


def smoke(svg):
    """The five puff shapes, each drawn centred where SMOKE_SHAPES puts it."""
    for tid, (cx, cy) in SMOKE_SHAPES.items():
        puff(svg, tid.replace('-', ' '), cx, cy, PUFF_LOBES[tid])


def shadow(svg):
    """The shadow the whole train casts on the track bed, under it from end to end: the sun is high and to the right,
    so it lies just below the wheels and a little to the left."""
    above, below, opacity = SHADOW
    x0, x1 = CARRIAGE_LEFTS[0] - 10, FRAME[1] + 30
    svg.open('train shadow')
    svg.path(rrect(x0, RAIL_Y + above, x1, RAIL_Y + below, 3), INK, name='shadow', extra=' fill-opacity="%s"' % opacity)
    svg.close()


def train(svg):
    """The train on the sheet, layered as the template layers it: the shadow, the wheels, the bodies rear to front
    over them, the gears on the bodies, the rods and the smoke."""
    svg.open('train')
    shadow(svg)
    wheels(svg)
    for k, x0 in enumerate(CARRIAGE_LEFTS):
        carriage(svg, len(CARRIAGE_LEFTS) - k, x0)
    loco(svg)
    gears(svg)
    rods(svg)
    pennant(svg)
    smoke(svg)
    svg.close()


def main():
    svg = Svg()
    train(svg)
    svg.write(cutting.sheet_path('structures/train.svg'))


def centred_part(path, group, grads, name, centre):
    """The group as an image whose centre is exactly centre, for a "center" anchor and pivot."""
    box = svgtools.stem_box(svgtools.element_bbox(group), centre, cutting.PAD)
    return cutting.Part(path, svgtools.part_svg(name, [group], grads, box), box)


def hung_part(path, group, grads, name, hang):
    """The group as an image whose right centre is exactly hang, for a "centerRight" anchor and pivot: the pennant
    hanging at its pole."""
    hx, hy = hang
    x0, y0, x1, y1 = svgtools.element_bbox(group)
    w = math.ceil(hx - (x0 - cutting.PAD))
    w += w % 2
    half = math.ceil(max(hy - (y0 - cutting.PAD), y1 + cutting.PAD - hy))
    box = (hx - w, hy - half, w, 2 * half)
    return cutting.Part(path, svgtools.part_svg(name, [group], grads, box), box)


def cut():
    """[(template id, its image)]: the loco and each carriage without wheels or gears, one wheel of each size centred
    on its axle, one gear of each size centred on its hub, the connecting rod, the pennant hung at its pole, each
    smoke puff shape centred on itself, and the train's shadow."""
    root, grads = cutting.load('structures/train.svg')
    out = []
    bodies = [('train loco', 'train-loco')] + [('train carriage %d' % k, 'train-carriage-%d' % k)
                                               for k in range(1, len(CARRIAGE_LEFTS) + 1)]
    for gid, tid in bodies:
        name = tid.partition('-')[2]
        out.append((tid, cutting.static_part('structures/parts/train/' + name, [cutting.find_group(root, gid)], grads,
                                             tid)))
    for tid, axle in DRAWN_AXLES.items():
        gid = next(g for g, t in wheel_groups() if t == tid)
        out.append((tid, centred_part('structures/parts/train/' + tid.partition('-')[2], cutting.find_group(root, gid),
                                      grads, tid, axle)))
    for tid, hub in DRAWN_GEARS.items():
        gid = next(g for g, t in gear_groups() if t == tid)
        out.append((tid, centred_part('structures/parts/train/' + tid.partition('-')[2], cutting.find_group(root, gid),
                                      grads, tid, hub)))
    out.append(('train-rod', cutting.static_part('structures/parts/train/rod', [cutting.find_group(root, 'train rod')],
                                                 grads, 'train-rod')))
    out.append(('train-flag', hung_part('structures/parts/train/flag', cutting.find_group(root, 'train flag'), grads,
                                        'train-flag', FLAG_HANG)))
    for tid, centre in SMOKE_SHAPES.items():
        out.append((tid, centred_part('structures/parts/train/' + tid.partition('-')[2],
                                      cutting.find_group(root, tid.replace('-', ' ')), grads, tid, centre)))
    out.append(('train-shadow', cutting.static_part('structures/parts/train/shadow',
                                                    [cutting.find_group(root, 'train shadow')], grads, 'train-shadow')))
    return out


def parts():
    return [part for _, part in cut()]


if __name__ == '__main__':
    main()

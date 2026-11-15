#   Writes SVG, run by `python3 -m scene_export render`: scenery/mesa.svg, the TrainMeadow's gear-arch mesa: two
#   flat-topped blocks of rock, the lower one on the left, their cliff faces dropping sheer from each top to a foot
#   the hills in front hide, with a ring-shaped stone gear standing on the upper top among small trees, a waterfall
#   pouring over a low rock ledge in the lower top's lip and down a shaded cleft in the cliff, and the mist where it
#   lands. The land is rock: grass is only a thin cap on each top, its turf dripping a little over the lip. Every
#   tree stands within its top's corners, since past a corner the cliff drops away and a crown there would hang in
#   the sky.
#
#   python3 -m scenery.mesa  ->  mesa.svg
#
#   It stands far off on the left of the sheet, in front of the mountains, so its colours are the reference's hazy
#   ones: the cliffs a pale mauve where the sun reaches them and a lilac blue in shade, both hazing toward the hills'
#   blue at the foot, and no line along the land's edges, as the terrace's far hills have none. Each cliff face is
#   the reference's two tiers: under the cap, slabs of uneven widths that narrow to points at uneven heights, each
#   with a lit plane down its left, a shaded one down its right and a dark crack beside it; below them, rounded rock
#   heaped against the foot, big ones standing high at the back and smaller ones in front. Every outline it does have, the ring's, the ledge's and the trees', is the
#   Esme terrace's: a dark shade of its own shape's colour (scenery/spring_valley.py's edge_of), as thin as the
#   terrace's at that distance, never a navy ink. The trees are the terrace's own kinds: its flame-shaped cypresses
#   (plants/trees.py) hazed as its far shore's are, among round crowns, standing in loose clumps clear of the falls,
#   a clump behind the ring showing through its hole.
#   The sun is to the upper right: the upper block's face is lit and its right edge brightest, the lower block
#   stands in its shadow, the cleft the water runs down is the deepest shade, the ledge's rock is lit along its top
#   right and the ring's upper-right rim catches the light.
#
#   The waterfall is drawn as a strip one FALL_PERIOD tall of streaks that repeat every period (each is clipped to
#   the strip at its place and a period above and below it), so the strip tiles top to bottom and the scene can
#   scroll it with wrap: repeat to make the water fall. Under it is the water's shape, its body drawn in the falls'
#   outline, and the scene masks the strip to that shape (stencil), so as in the reference the water pours from a
#   lip nearly as wide as the sheet below, its right edge dropping straight and its left edge leaning out. Over both
#   is the lip, the water rounding smoothly over it under a white crest, and the mist where the water lands.

import math
import os
import random

from common.painting import Svg, f, mix, poly
from plants import trees as terrace_trees
from scene_export import cutting, svgtools
from scenery.spring_valley import edge_of
from structures.houses import TOWN_LINE_WIDTH

HERE = os.path.dirname(os.path.abspath(__file__))

LINE = TOWN_LINE_WIDTH           # px, the ring's outline, the terrace's for a building across the water
DETAIL_LINE = 0.9                # px, seams and inner edges

# ---------------------------------------------------------------- the land
LEFT, RIGHT = 240, 566           # sheet px, the cliffs' outer edges at their foot
FOOT = 452                       # sheet px, where the land is cut off, hidden under the hills
SPLIT = 408                      # sheet px, where the lower top on the left ends at the riser up to the upper top
BANK_RUN = 5                     # px the riser between the two tops runs for: a sheer step of rock, not a bank
LOWER_LIP, UPPER_LIP = 340, 328  # sheet px, each top's front edge at its ends; the tops dome up between
LOWER_TILT = 5                   # px the lower top's lip drops toward its left end
SHELF = (9, 3)                   # px of each flat top seen above its lip at the top's ends, and the extra toward its middle
BATTER = 30                      # px each cliff's foot stands out past its lip corner, sloping out more the lower it is
SHELF_FADE = 0.3                 # how far the cap shades from its mid green toward the shade at its back edge
GRASS = {'crest': '#e2e89c', 'mid': '#c6d688', 'shade': '#8fb49c'}   # the caps' turf, the reference's yellow-green
# the cliffs' rock: the face in the sun, its brightest lit edge and the warm slab beside the cleft; the shade the
# lower block stands in and the recesses between the columns; the hills' blue every face hazes to at the foot
CLIFF = {'lit': '#e8d8dc', 'face': '#d2c4ce', 'warm': '#dcc6c2', 'facet': '#bcb0cc', 'shade': '#6690d2', 'recess': '#6c8fd0',
         'deep': '#5878be', 'foot': '#6a92d4'}
# the slabs in the sun and in the shadow: each slab takes one of its light's tones, its lit left edge the facet tone
SLABS = {'lit': ('#d8c2cc', '#cbbccc', '#c2b8d0', '#d6bec4'), 'shade': ('#6d92da', '#6489d6', '#7799dc', '#698ed8')}
FACET_TONE = {'lit': '#eadbe0', 'shade': '#93aee6'}
BOULDERS = {'lit': ('#c4b8d0', '#cfc0cb', '#b6b2d4'), 'shade': ('#7a97da', '#6f8ed6', '#86a2dc')}
FOOT_HAZE = (0.5, 30, 50)       # how far each face's colour goes toward the foot's blue, px below the lip it starts, px above the foot it is there
HIDDEN = 44                      # px above the cut-off foot the hills in front hide the cliff from, about
UNDERCUT = 4                     # px, the dark band under the cap where the turf overhangs the rock
DRIPS = (2, 5)                   # px the turf hangs over the lip in tongues, least and most
SLAB_WIDTH = (16, 38)            # px, a broad slab's width under the cap, least and most
SLIVER_WIDTH = (6, 11)           # px, a narrow sliver of rock's width between the broad slabs, least and most
SLIVERS = 0.3                    # share of the slabs that are slivers
SET_BACK = 0.3                   # share of the slabs set back in shade between those standing out, never two together
SET_BACK_SHADE = 0.35            # how far a set-back slab's tone goes toward the deep shade
SET_BACK_REACH = (0.3, 0.65)     # how far down the face a set-back slab's point reaches, least and most
TIPS = ('point', 'point', 'slant', 'blunt')   # how a slab's foot ends: to a point, cut aslant to one side, or blunt
LIT_PLANES = 0.7                 # share of the slabs with a lit plane down their left
SHADE_PLANES = 0.6               # share with a shaded plane down their right
CRACKS = 0.6                     # share with a dark crack down their left side
SLAB_REACH = (0.4, 0.95)         # how far down the face above the hidden foot a slab's point reaches, least and most
SLAB_POINT = (0.8, 1.4)          # px each side of a slab draws in over toward its point, as a share of its width
POINT_LEAST = 14                 # px, the width a narrow slab draws in over as if it were, so a sliver still tapers
SLAB_LEAN = 2                    # px a slab's point may stand off its top's middle either way
WOBBLE = 0.6                     # px a slab's sides waver, so they are not ruled
CRACK = (1.2, 2.2)               # px wide the dark crack down a slab's left side is under the cap, narrowing down
CRACK_REACH = (0.5, 0.85)        # how far down the slab's side its crack runs
LIT_PLANE = (0.15, 0.6)          # share of a slab's width its lit left plane takes under the cap, narrowing to the point
SHADE_PLANE = (0.12, 0.35)       # share of its width its shaded right plane takes, narrowing to the point
PLANE_TONE = {'lit': '#a9a8d2', 'shade': '#5f84cc'}
BOULDER_ROWS = [((22, 46), (30, 60)), ((14, 32), (6, 24))]   # each row of rock heaped at the foot, back to front:
                                 # (px wide least and most, px its top stands above where the hills hide the foot)
BOULDER_DOME = (0.3, 0.55)       # a rock's rounded top's height, as a share of its width, least and most
BOULDER_PEAK = 0.18              # share of its width a rock's crown may stand off its middle either way
BOULDER_FLARE = 0.1              # share of its width a rock's sides spread out by toward the foot
LIT_SLAB = (30, 22)              # px wide the sunlit slabs of the lower block beside the cleft are, at the lip and at the foot
CLEFT_SHADE = (34, 24)           # px past the riser the upper block's shaded left face reaches, at the lip and at the foot
HOLLOW = 3                       # px of shaded rock either side of the cleft the water runs down
SEED = 'mesa'

# ---------------------------------------------------------------- the rock at the falls
ROCK_WINGS = 7                   # px of ledge either side of the strip, the rock shoulders the water pours between
ROCK_DROP = 10                   # px the ledge's face stands below the lip
ROCK_TAPER = 4                   # px the ledge's ends draw in at its foot, so it sits in the cliff as a crag
LIP_SHADOW = 3                   # px, the dark band where the turf overhangs the ledge
ROCK = {'body': CLIFF['facet'], 'lit': CLIFF['lit'], 'shade': CLIFF['shade'], 'deep': CLIFF['deep'], 'wet': CLIFF['deep']}
TONGUES = 3                      # px the turf drapes over the ledge in lobes
POUR_CURL = 7                    # px past the strip's top the lip of water rounds off over it
ROLL_RADIUS = 0.35               # the roll's left shoulder's radius, as a share of the falls' width at the lip
ROLL_RIGHT = 3                   # px, the radius its right shoulder turns down against the rock with
BANKS = ((332, 327), (433, 316))  # sheet px, where the banks the land falls away in either side of the water reach back
                                  # to, as drawn in the markup
BANK_CURVE = 1.35                 # how steep the banks are by the water against how flat they are going back

# ---------------------------------------------------------------- the gear ring
GEAR_TOP = 237                   # sheet px, the topmost tooth's tip
GEAR_CENTRE = (440, 304)
GEAR_OUTER, GEAR_INNER = 60, 41  # px, the ring face's radii
TEETH, TOOTH_HEIGHT = 12, 7
TOOTH_BASE, TOOTH_TIP = 11, 8    # px, half a tooth's width at its base and its tip
BORE_SHIFT = (4, -3)             # px the far side of the hole's bore is offset: the ring seen from a little left and below
BEVEL = 4                        # px, the bevelled ring round the hole
RIVETS = 8                       # round the rim
STONE = {'lit': '#e8d3c3', 'body': '#c0a8ac', 'shade': '#9a9cc2', 'deep': '#7c84b6', 'bore': '#8d86a6'}
LIT_ARC = (-150, 30)             # degrees on screen (y down) of the rim the sun catches
SHADE_ARC = (105, 200)           # the lower left falls into blue shade

# ---------------------------------------------------------------- trees on the top
CROWN_EDGE = 1.1                 # px, a crown's dark underlay showing round it as its outline
TREE = {'lit': '#a8dc8c', 'body': '#62b49a', 'shade': '#4888b8', 'trunk': '#9a8aa0', 'trunk shade': '#6d6890'}
CYPRESS_HAZE = terrace_trees.FAR_TREE_HAZE   # the cypresses are hazed as the terrace's far shore's, the mesa being as far
CYPRESS_SLACK = 1                # px either side a cypress's chipped outline may reach past its half width


def round_tree(x, w, h, trunk=0, lean=0, behind=False):
    """A round-crowned tree: its foot at x, its crown w wide and h tall over a trunk trunk px tall leaning lean px."""
    return dict(kind='round', x=x, w=w, h=h, trunk=trunk, lean=lean, behind=behind)


def cypress(x, hw, h, behind=False):
    """One of the terrace's cypresses: its foot at x, hw its half width at the base, h its height to the tip."""
    return dict(kind='cypress', x=x, hw=hw, h=h, behind=behind)


# the trees, each on the top its foot is on: a loose clump left of the falls on the lower step, tall cypresses
# among round crowns, one small crown right of the falls where the bank climbs; on the upper step a clump behind
# the ring, seen through its hole, and a taller, looser group right of the ring in front of it
TREES = [round_tree(284, 18, 12), cypress(294, 6.5, 32), round_tree(306, 22, 15, trunk=4), cypress(318, 5.5, 24),
         round_tree(324, 14, 9), round_tree(401, 14, 9),
         cypress(440, 7, 36, behind=True), round_tree(455, 22, 15, behind=True), cypress(467, 6, 28, behind=True),
         round_tree(490, 16, 11), cypress(500, 6.5, 32), round_tree(513, 24, 16, trunk=4), round_tree(523, 15, 10)]

# ---------------------------------------------------------------- the waterfall
FALL_X = (350, 378)              # sheet px, the strip's edges; a narrow sheet, three times as tall as wide where it shows
FALL_PERIOD = 96                 # px, the back strip's height, 80 canvas units: its bands repeat every period
FRONT_PERIOD = 126               # px, the front strip's, 105 units, 3.5 s at its speed: the two strips drift past each other
FALL_COPIES = (-1, 1)            # each band is drawn at its place and from a period above to one below, so the strip tiles
NOTCH = 6                        # px the lip dips where the water pours out
LEAN = 3                         # px the falls' left edge leans out over the strip's height, from the lip to its foot
WAVER = (0.8, 2)                 # (px, waves) the left edge wavers about its lean down the strip, still at its ends
LIP = (2, 2, 1.5)                # (px the lip's left end sits under the turf, px its right end stands higher, px it bows up)
CREST = 2.5                      # px, the white crest along the lip and round its shoulder
CREST_GLOW = (2.5, 0.4)          # px the crest blends on below itself, and that band's opacity
POUR_SHADE = 0.35                # opacity of the lip's darker right side
# faint light streaks over the roll, as painted in the markup, each tapering to a point well above the lip's foot so
# they make no comb along it: (share of the way across, px wide at the crest, px its point leans right, px long)
POUR_STREAKS = [(0.16, 0.9, -1.5, 4), (0.3, 0.8, 1.2, 3), (0.44, 1, -1.8, 4.5), (0.6, 0.8, -1.8, 3.5), (0.7, 0.9, -1.5, 4),
                (0.8, 0.8, 1, 3), (0.9, 0.8, -1.4, 3.5)]
STREAK_CLEAR = 2                 # px above the lip's foot the longest streak's point stops
POUR_STREAK = 0.25               # their opacity
WATER = {'pour': '#c6f1fc', 'body': '#46d2f4', 'edge': '#7fe2f8', 'streak': '#ffffff', 'shadow': '#2cb6e8', 'left edge': '#30bce8',
         'band': '#93ecfb', 'band light': '#c4f4fd', 'band core': '#e2fbfe'}   # bright cyan, as in the reference
LEFT_EDGE = 1.2                  # px of light blue down the sheet's left edge, where it turns away from the light
SHADOW_SIDE = 0.18               # share of the strip's width the sheet's deep blue shadow side takes, near its right
PALE_EDGE = 1.5                  # px of pale water along the sheet's right edge, outside its shadow side
SHADOW_FADE = 12                 # px below the lip's foot the shadow side deepens over, from the lip's shade to its own
FOOT_PALE = 0.3                  # how far the body pales toward white at the foam, the water going to foam as it falls
# the two strips of zigzag bands, the back one slow and soft, the front one faster, white and sharper. Each: its period,
# canvas units it falls a frame (a whole number of 2x texture px, or it judders), where in the period each band's top
# is (shares, uneven), px thick, px its teeth hang below it and its notches rise above it, a tooth's width (average
# px, least and most share of that), the share of the way across each band spans (a band short of an edge tapers out),
# and its layers outer to inner: (colour, opacity, px below the band's top, share of its thickness, share of its hang)
STRIPS = {
    'back': {'period': FALL_PERIOD, 'speed': 0.25, 'at': (0.04, 0.4, 0.66), 'thick': 5.5, 'hang': (2, 6), 'notch': (1, 3),
             'tooth': (6.5, 0.6, 1.5), 'spans': [(0, 1), (0, 1), (0, 1)],
             'layers': [('band', 0.5, 0, 1, 1), ('band light', 0.6, 1, 0.6, 0.6)]},
    'front': {'period': FRONT_PERIOD, 'speed': 0.5, 'at': (0.04, 0.34, 0.5, 0.76), 'thick': 3, 'hang': (4, 12),
              'notch': (1, 4), 'tooth': (5, 0.5, 1.6), 'spans': [(0, 1), (0.3, 1), (0, 0.72), (0.15, 0.85)],
              'layers': [('band light', 0.55, 0, 1, 1), ('band core', 0.9, 0.6, 0.5, 0.55)]},
}
BAND_TILT = 0.06                 # px a band's top may rise or drop a px across, so the bands are not ruled
TAPER = 7                        # px a band short of an edge thins out over, to nothing at its end
LIP_ABOVE = 12                   # px above the strip's top the lip's box starts: a whole number of canvas units (6 px = 5)
LIP_SIDE = 6                     # px left of the strip the lip's box starts, likewise, and px of room right of it
SPRAY = {'body': '#f4fcff', 'shade': '#b9ecf9', 'mist': '#eefaff'}
SPRAY_CENTRE = (364, 408)       # just below where the far hills in front hide the falls' foot, so the foam covers the foot
SPRAY_BOX = (30, 18, 60, 30)     # px left and above the centre the spray's parts' box starts, its width and height
# (dx, dy, r) round SPRAY_CENTRE: the still, solid foam the falls end in, a low mound little wider than the falls
FOAM_BED = [(-17, 3, 3.2), (-12, 1.5, 4), (-6, 0.5, 4.6), (0, 0, 4.8), (6, 0.5, 4.6), (12, 1.5, 4), (17, 3, 3.2)]
FOAM_SHADE = (1.5, 0.4)          # px the bed's shade sits below it, and its opacity
MIST = (0, -3, 15, 4)            # (dx, dy, rx, ry) round the centre: the mist breathing over the foam
MIST_OPACITY = 0.35
CHURN_PERIOD = 24                # px, the churn strip's width, 20 canvas units: its dimples repeat every period
CHURN_ABOVE = 12                 # px above the spray's centre the churn strip starts (a whole number of units from the box)
CHURN_HEIGHT = 16                # px, the churn strip's height
# the dimples rolling out over the foam, (dx, dy, rx, ry, opacity) in the churn's period from its left and the centre's
# height: hollows of the foam's shade, big and small, none in a row
DIMPLES = [(3, 2, 3, 1.6, 0.45), (9.5, 5.2, 2.2, 1.2, 0.4), (14, 1.2, 3.4, 1.8, 0.45), (20, 4, 2.6, 1.4, 0.42),
           (6.5, 7, 1, 0.6, 0.5), (17.5, 6.6, 0.9, 0.55, 0.5), (23, 0.5, 1.1, 0.7, 0.4)]
RISING = [[(-4, -2, 2.4), (3, -1.5, 2)], [(2, -2.5, 2.2), (-7, -0.5, 1.9)]]   # two sets of foam heaving out of it in turn, (dx, dy, r)
# the loose water thrown up from it, two sets the scene throws up in turn: [(dx, dy, w, h) streaks], [(dx, dy, r) drops]
THROWN = [([(-6, -7, 1.2, 4), (1, -6, 1.1, 3.5)], [(-15, -1, 0.9), (14, -2, 0.9), (-18, 2, 0.7)]),
          ([(5, -8, 1.2, 4.5), (-3, -6, 1, 3.5)], [(-12, -3, 0.8), (12, -3, 0.7), (18, 2, 0.8)])]


def circle(cx, cy, r):
    return 'M%s,%s A%s,%s 0 1,0 %s,%s A%s,%s 0 1,0 %s,%s Z' % (f(cx - r), f(cy), f(r), f(r), f(cx + r), f(cy), f(r),
                                                              f(r), f(cx - r), f(cy))


def hole(cx, cy, r):
    """A circle wound against circle()'s, so a path holding both leaves it empty under the nonzero fill rule."""
    return 'M%s,%s A%s,%s 0 1,1 %s,%s A%s,%s 0 1,1 %s,%s Z' % (f(cx - r), f(cy), f(r), f(r), f(cx + r), f(cy), f(r),
                                                              f(r), f(cx - r), f(cy))


def edge_x(x_foot, y, lean):
    """An outer cliff's x at height y: x_foot at FOOT, BATTER px in at the lip, steep under the lip and spreading
    out toward the foot."""
    s = (y - UPPER_LIP) / (FOOT - UPPER_LIP)
    return x_foot + lean * BATTER * (1 - s * s)


LIP_LEFT = edge_x(LEFT, LOWER_LIP + LOWER_TILT, 1)     # sheet px, the lower top's left corner
LIP_RIGHT = edge_x(RIGHT, UPPER_LIP, -1)               # sheet px, the upper top's right corner


def step_span(step):
    """(x0, x1) of a top's lip, the lower one ending at the bank, the upper one starting above it."""
    return (LIP_LEFT, SPLIT) if step == 'lower' else (SPLIT + BANK_RUN, LIP_RIGHT)


def share_of(step, x):
    x0, x1 = step_span(step)
    return max(0.0, min(1.0, (x - x0) / (x1 - x0)))


def lip_y(step, x):
    """The top's front edge at x: a low dome along the top, the lower one's dropping toward its left end."""
    t = share_of(step, x)
    if step == 'lower':
        return LOWER_LIP + LOWER_TILT * (1 - t) - 2 * math.sin(math.pi * t) + 1.2 * math.sin(t * 9 + 1) + 0.6 * math.sin(t * 17)
    return UPPER_LIP - 2.5 * math.sin(math.pi * t) + 0.8 * math.sin(t * 13 + 2)


def cap_top_y(step, x):
    return lip_y(step, x) - SHELF[0] - SHELF[1] * math.sin(math.pi * share_of(step, x))


def samples(step, n=24):
    x0, x1 = step_span(step)
    return [x0 + (x1 - x0) * k / n for k in range(n + 1)]


def rock_span():
    """(x0, x1) of the ledge the water pours over, the only rock on the land."""
    return FALL_X[0] - ROCK_WINGS, FALL_X[1] + ROCK_WINGS


def top_y(x):
    """The land's top edge at any x along it: the lower top, the bank climbing to the upper top, the upper top."""
    if x <= SPLIT:
        return lip_y('lower', x)
    if x >= SPLIT + BANK_RUN:
        return lip_y('upper', x)
    t = (x - SPLIT) / BANK_RUN
    return lip_y('lower', SPLIT) + (lip_y('upper', SPLIT + BANK_RUN) - lip_y('lower', SPLIT)) * (0.5 - 0.5 * math.cos(math.pi * t))


# ================================================================ land

def wall(x_foot, lean, n=8):
    """The outer cliff's edge from the foot up to the lip corner."""
    y_lip = top_y(LIP_LEFT if lean > 0 else LIP_RIGHT)
    return [(edge_x(x_foot, FOOT + (y_lip - FOOT) * k / n, lean), FOOT + (y_lip - FOOT) * k / n) for k in range(n + 1)]


def top_edge(n=64):
    """The top edge from the left lip corner to the right one, along both tops and the riser between, down into the
    gap the water pours out of."""
    return [(x, land_top_y(x)) for x in with_gap([LIP_LEFT + (LIP_RIGHT - LIP_LEFT) * k / n for k in range(n + 1)])]


def gap():
    """(x0, x1) of the gap in the land the water pours out of, as in the reference: from where the roll's left
    shoulder comes up to the lip to its right edge, with no turf or rock above the water between."""
    shoulder, _ = pour_outline()
    return shoulder[1][0], FALL_X[1]


def valley_y(x):
    """The highest the land may stand at x: just under the roll's top over the water, then up each bank, steep by the
    water and flattening as it reaches back; no limit beyond the banks."""
    x0, x1 = gap()
    (xl, yl), (xr, yr) = BANKS
    if x0 <= x <= x1:
        return roll_top_y(x) + 1
    near, far, y_far = (x0, xl, yl) if x < x0 else (x1, xr, yr)
    t = (x - near) / (far - near)
    if t >= 1:
        return -math.inf
    y_near = roll_top_y(near) + 1
    return y_near - (y_near - y_far) * (1 - (1 - t) ** BANK_CURVE)


def land_top_y(x):
    """The land's top at x: the tops, cut down to the valley the water pours out of."""
    return max(top_y(x), valley_y(x))


def lowered(x, y):
    return max(y, valley_y(x))


def with_gap(xs):
    """xs with points along the banks added, and the gap's edges, so what follows the land's top runs down the banks."""
    (xl, _), (xr, _) = BANKS
    lo, hi = min(xs), max(xs)
    banks = [xl + (xr - xl) * k / 120 for k in range(121)] + list(gap())
    return sorted({x for x in xs} | {x for x in banks if lo < x < hi})


def outline():
    """The land's silhouette: up the left cliff, along the tops, down the right cliff, and across the hidden foot."""
    return wall(LEFT, 1) + top_edge()[1:-1] + list(reversed(wall(RIGHT, -1)))


def riser_x(y):
    """Where the upper block's left face is at height y: the riser's middle at the lip, leaning out a little by the foot."""
    return SPLIT + BANK_RUN / 2 + 3 * (y - UPPER_LIP) / (FOOT - UPPER_LIP)


def hazed(colour):
    """A face's fill: its colour at the lip, hazing toward the foot's blue by a little above the hidden foot."""
    toward, below, above = FOOT_HAZE
    return (colour, mix(colour, CLIFF['foot'], toward), UPPER_LIP + below, FOOT - above)


def block_span(step):
    """(x0, x1) of a block's face at the lip, the lower one's left of the riser and the upper one's right of it."""
    return (LIP_LEFT, SPLIT) if step == 'lower' else (SPLIT + BANK_RUN, LIP_RIGHT)


def in_the_cleft(x0, x1):
    """Whether a column between x0 and x1 would stand where the water runs down."""
    return x1 > FALL_X[0] - HOLLOW - 2 and x0 < FALL_X[1] + HOLLOW + 2


def slab_edge_x(y):
    """Where the lower block's broad shadow ends and its sunlit slab beside the cleft begins, at height y."""
    t = (y - LOWER_LIP) / (FOOT - LOWER_LIP)
    return FALL_X[0] - HOLLOW - (LIT_SLAB[0] + (LIT_SLAB[1] - LIT_SLAB[0]) * t)


def cleft_shade_x(y):
    """Where the upper block's shaded left face, running from the cleft, ends at height y."""
    t = (y - UPPER_LIP) / (FOOT - UPPER_LIP)
    return riser_x(y) + CLEFT_SHADE[0] + (CLEFT_SHADE[1] - CLEFT_SHADE[0]) * t


def shaded_at(x):
    """Whether a column at x stands in shade: the lower block but for its slab beside the cleft, and the upper block's
    left face from the cleft."""
    y = (UPPER_LIP + FOOT) / 2
    return x < slab_edge_x(y) or FALL_X[1] < x < cleft_shade_x(y)


def visible_foot(x):
    """sheet px, about where the hills in front hide the cliff at x."""
    return FOOT - HIDDEN


def wobbly(p0, p1, rng, n=5):
    """The points from p0 to p1 along a side wavering a little either way, its ends where they are."""
    return [(p0[0] + (p1[0] - p0[0]) * k / n + (rng.uniform(-WOBBLE, WOBBLE) if 0 < k < n else 0),
             p0[1] + (p1[1] - p0[1]) * k / n) for k in range(n + 1)]


def slab_tip(x, w, top, reach, rng):
    """Where a slab's sides end and its foot: (left side's end, the foot's points, right side's end)."""
    tip_y = top + (visible_foot(x) - top) * reach
    run = max(w, POINT_LEAST)
    kind = rng.choice(TIPS)
    if kind == 'slant':
        low_left = rng.random() < 0.5
        foot = [(x + w * (0.1 if low_left else 0.9), tip_y)]
        drop = run * rng.uniform(1.0, 1.6)
        return (x, tip_y - (run * 0.2 if low_left else drop)), foot, (x + w, tip_y - (drop if low_left else run * 0.2))
    if kind == 'blunt':
        mid = x + w * rng.uniform(0.4, 0.6)
        foot = [(mid - w * 0.07, tip_y), (mid + w * 0.07, tip_y - rng.uniform(0, 2))]
    else:
        foot = [(x + w * rng.uniform(0.35, 0.65) + rng.uniform(-SLAB_LEAN, SLAB_LEAN), tip_y)]
    return (x, tip_y - run * rng.uniform(*SLAB_POINT)), foot, (x + w, tip_y - run * rng.uniform(*SLAB_POINT))


def slab(svg, x, w, light, tone, set_back, rng):
    """One slab under the cap in the tone given: its sides running down from the cap and drawing in to its foot. One
    standing out may have a lit plane down its left, a shaded one down its right and a dark crack beside it; one set
    back is darker, ends higher and has none."""
    top_of = lambda xx: lowered(xx, cap_front_y(xx) + 1)
    top = max(top_of(x), top_of(x + w))
    left, foot, right = slab_tip(x, w, top, rng.uniform(*(SET_BACK_REACH if set_back else SLAB_REACH)), rng)
    under = [(x + w * k / 6, top_of(x + w * k / 6)) for k in range(7)]
    outline = under + wobbly((x + w, top_of(x + w)), right, rng)[1:] + foot[::-1] + wobbly(left, (x, top_of(x)), rng)[:-1]
    if set_back:
        svg.path(poly(outline), hazed(mix(tone, CLIFF['deep'], SET_BACK_SHADE)), name='recess')
        return
    svg.path(poly(outline), hazed(tone), name='slab')
    if rng.random() < LIT_PLANES:
        lit = w * rng.uniform(*LIT_PLANE)
        svg.path(poly([(x, top_of(x)), (x + lit, top_of(x + lit)), foot[0], left]), hazed(FACET_TONE[light]),
                 name='lit plane', extra=' fill-opacity="0.7"')
    if rng.random() < SHADE_PLANES:
        shade = w * rng.uniform(*SHADE_PLANE)
        svg.path(poly([(x + w - shade, top_of(x + w - shade)), (x + w, top_of(x + w)), right, foot[-1]]),
                 hazed(PLANE_TONE[light]), name='shade plane', extra=' fill-opacity="0.7"')
    if rng.random() < CRACKS:
        cw, reach = rng.uniform(*CRACK), rng.uniform(*CRACK_REACH)
        end = (x + (left[0] - x) * reach, top_of(x) + (left[1] - top_of(x)) * reach)
        svg.path(poly([(x - cw / 2, top_of(x)), (x + cw / 2, top_of(x)), end]), hazed(CLIFF['deep']), name='crack',
                 extra=' fill-opacity="0.8"')


def column_spans(x0, x1, rng):
    """(x, w) of the slabs side by side from x0 to x1: broad ones with narrow slivers among them, their widths uneven,
    scaled to fill the span."""
    widths = [rng.uniform(*(SLIVER_WIDTH if rng.random() < SLIVERS else SLAB_WIDTH))]
    while sum(widths) < x1 - x0 - SLAB_WIDTH[0] / 2:
        widths.append(rng.uniform(*(SLIVER_WIDTH if rng.random() < SLIVERS else SLAB_WIDTH)))
    scale = (x1 - x0) / sum(widths)
    spans, x = [], x0
    for w in widths:
        spans.append((x, w * scale))
        x += w * scale
    return spans


def slab_row(svg, step, rng):
    """The slabs the block's face is split into, side by side under its cap, none where the water runs down: each
    standing out in a tone of the light other than its standing neighbour's, or now and then set back between two
    that do."""
    x0, x1 = block_span(step)
    cleft = (FALL_X[0] - HOLLOW - 2, FALL_X[1] + HOLLOW + 2)
    runs = [(x0, x1 - 1)] if x0 >= cleft[1] or x1 <= cleft[0] else [(x0, cleft[0]), (cleft[1], x1 - 1)]
    tone, set_back = None, True
    for a, b in runs:
        if b - a < SLIVER_WIDTH[0]:
            continue
        for x, w in column_spans(a, b, rng):
            light = 'shade' if shaded_at(x + w / 2) else 'lit'
            set_back = not set_back and rng.random() < SET_BACK
            if not set_back:
                tone = rng.choice([t for t in SLABS[light] if t != tone])
            slab(svg, x, w, light, tone or SLABS[light][0], set_back, rng)


def lump(x, w, top, rng):
    """A rounded rock's outline: its crown off its middle, one shoulder lower than the other, its sides spreading out a
    little down to the foot."""
    peak = 0.5 + rng.uniform(-BOULDER_PEAK, BOULDER_PEAK)
    dome = w * rng.uniform(*BOULDER_DOME)
    sag = [rng.uniform(0.8, 1.2), rng.uniform(0.8, 1.2)]
    points = []
    for k in range(17):
        t = k / 16
        u = t / peak * 0.5 if t < peak else 0.5 + (t - peak) / (1 - peak) * 0.5
        side = sag[0] if t < peak else sag[1]
        points.append((x + w * t, top + dome * (1 - math.sin(math.pi * u)) * side))
    flare = w * BOULDER_FLARE
    return points + [(x + w + flare, FOOT), (x - flare, FOOT)], (x + w * peak, top), dome


def boulders(svg, step, rng):
    """The rounded rock heaped against the foot of the block's face over the slabs' points, big ones standing high at
    the back and smaller ones lower in front, drawn back to front, each lighter where the sun catches its crown, the
    lowest hidden by the hills."""
    x0, x1 = block_span(step)
    rocks = []
    for widths, rises in BOULDER_ROWS:
        x = max(LEFT, x0 - 2 + rng.uniform(0, 6))
        while x < x1 - 4:
            w = min(rng.uniform(*widths), (RIGHT - x) / (1 + BOULDER_FLARE))
            if not in_the_cleft(x - w * BOULDER_FLARE, x + w * (1 + BOULDER_FLARE)):
                rocks.append((visible_foot(x) - rng.uniform(*rises), x, w))
            x += w * rng.uniform(0.5, 0.9)
    for top, x, w in sorted(rocks):
        x = max(x, LEFT + w * BOULDER_FLARE, edge_x(LEFT, top, 1))
        w = min(w, edge_x(RIGHT, top, -1) - x)
        light = 'shade' if shaded_at(x + w / 2) else 'lit'
        outline, crown, dome = lump(x, w, top, rng)
        svg.path(poly(outline), hazed(rng.choice(BOULDERS[light])), name='boulder')
        crest = outline[:17]
        lit = [p for p in crest if p[0] <= crown[0] + w * 0.08]
        inner = [(px + w * 0.14, py + dome * 0.7) for px, py in reversed(lit)]
        svg.path(poly(lit + inner), hazed(FACET_TONE[light]), name='boulder light', extra=' fill-opacity="0.65"')
        dark = [p for p in crest if p[0] >= crown[0] + w * 0.15] + [outline[17]]
        svg.path(poly(dark + [(px - w * 0.16, py + 2) for px, py in reversed(dark)]), hazed(PLANE_TONE[light]),
                 name='boulder shade', extra=' fill-opacity="0.6"')


def undercut(svg):
    """The dark band under the caps where the turf overhangs the rock, along both tops and down the riser."""
    xs = with_gap([LIP_LEFT + (LIP_RIGHT - LIP_LEFT) * k / 96 for k in range(97)])
    low = lowered
    band = [(x, low(x, cap_front_y(x))) for x in xs] + \
        [(x, low(x, cap_front_y(x) + UNDERCUT + 0.8 * math.sin(x / 4.0))) for x in reversed(xs)]
    svg.path(poly(band), CLIFF['deep'], name='undercut', extra=' fill-opacity="0.7"')


def shelf(svg, step):
    """A flat top seen a little from above: the sunlit cap from its back edge down to its front edge, the lip,
    brightest along the lip, its turf hanging over the lip in tongues."""
    xs = with_gap(samples(step, 48))
    low = lowered
    front = [(x, low(x, cap_front_y(x) + 1)) for x in xs]
    band = [(x, low(x, cap_top_y(step, x))) for x in xs] + list(reversed(front))
    y0, y1 = min(y for _, y in band), max(y for _, y in band)
    drips = [(x, low(x, cap_front_y(x) - 1)) for x in xs] + [(x, low(x, cap_front_y(x) + drip_depth(x))) for x in reversed(xs)]
    svg.path(poly(drips), mix(GRASS['mid'], GRASS['shade'], 0.35), name=step + ' drips')
    svg.path(poly(band), (mix(GRASS['mid'], GRASS['shade'], SHELF_FADE), GRASS['crest'], y0, y1), name=step + ' shelf')


def drip_depth(x):
    """px the turf hangs over the lip at x: tongues of varying length between the least and most."""
    lo, hi = DRIPS
    return lo + (hi - lo) * max(0.0, math.sin(x / 5.3) * 0.7 + 0.3 * math.sin(x / 2.1 + 1)) ** 1.4


def hollow_colour():
    """The shaded rock of the cleft the water runs down."""
    return mix(CLIFF['recess'], CLIFF['deep'], 0.8)


def hollow(svg):
    """The shaded cleft the water runs down the cliff in, and the wet rock in its bed behind the strip."""
    xa, xb = FALL_X
    xs = with_gap([xa - HOLLOW + (xb - xa + 2 * HOLLOW) * k / 16 for k in range(17)])
    top = [(x, land_top_y(x)) for x in xs]
    svg.path(poly(top + [(xb + HOLLOW + 4, FOOT), (xa - HOLLOW - 4, FOOT)]), hollow_colour(), name='hollow')
    wet = [(x, y) for x, y in top if xa - 1 <= x <= xb + 1]
    svg.path(poly(wet + [(xb + 2, FOOT), (xa - 2, FOOT)]), ROCK['wet'], name='wet rock')


def land(svg, rng):
    """The rock of both blocks: each face split into slabs, the lower block's in the shadow's lilac blue and the upper
    block's in the sun's pink-lilac but for its shaded left face from the cleft, boulders heaped at their feet, the
    cleft under the falls, and the undercut under the caps."""
    svg.open('land')
    svg.path(poly(outline()), hazed(CLIFF['facet']), name='rock')
    y = (UPPER_LIP + FOOT) / 2
    svg.path(poly([(x, yy) for x, yy in outline() if x < slab_edge_x(y)] + [(slab_edge_x(FOOT), FOOT), (slab_edge_x(LOWER_LIP), LOWER_LIP - 4)]),
             hazed(CLIFF['shade']), name='shade rock')
    for step in ('lower', 'upper'):
        slab_row(svg, step, rng)
    heap = random.Random(SEED + ' boulders')
    for step in ('lower', 'upper'):
        boulders(svg, step, heap)
    hollow(svg)
    undercut(svg)
    svg.close()


def cap_front_y(x):
    """The lower top's front edge over the ledge, dipping into the notch the waterfall pours out of."""
    y = top_y(x)
    if FALL_X[0] - 8 < x < FALL_X[1] + 8:
        dip = math.cos(math.pi * (x - (FALL_X[0] + FALL_X[1]) / 2) / (FALL_X[1] - FALL_X[0] + 12))
        y += NOTCH * max(0.0, dip)
    return y


def ledge(svg):
    """The low rock ledge the water pours over: a crag set into the lower top's lip, blue-mauve in the shade under the
    turf's overhang and lit along its top right, its ends drawing in at its foot so it sits in the slope."""
    x0, x1 = rock_span()
    xs = [x0 + (x1 - x0) * k / 16 for k in range(17)]
    svg.open('ledge')
    top = [(x, cap_front_y(x) - 1) for x in xs]
    foot = ([(x1 - ROCK_TAPER, top_y(x1) + ROCK_DROP - 3)]
            + [(x, top_y(x) + ROCK_DROP + 2.5 * math.sin(x / 5.0)) for x in reversed(xs[2:-2])]
            + [(x0 + ROCK_TAPER, top_y(x0) + ROCK_DROP - 3)])
    body = top + foot
    svg.path(poly(body), ROCK['body'], name='rock')
    svg.path(poly([(x, y) for x, y in top] + [(x, y + LIP_SHADOW) for x, y in reversed(top)]), ROCK['deep'], name='lip shadow',
             extra=' fill-opacity="0.7"')
    lit = ([(x, cap_front_y(x) + LIP_SHADOW) for x in xs if x > FALL_X[1]]
           + [(x1 - ROCK_TAPER + 1, top_y(x1) + ROCK_DROP - 6), (FALL_X[1] + 2, top_y(FALL_X[1]) + ROCK_DROP - 2)])
    svg.path(poly(lit), ROCK['lit'], name='rock lit')
    shade = ([(x, cap_front_y(x) + LIP_SHADOW) for x in xs if x < FALL_X[0]]
             + [(FALL_X[0] - 2, top_y(FALL_X[0]) + ROCK_DROP - 2), (x0 + ROCK_TAPER - 1, top_y(x0) + ROCK_DROP - 6)])
    svg.path(poly(shade), ROCK['shade'], name='rock shade', extra=' fill-opacity="0.85"')
    for x in (x0 + 4, x1 - 4):
        svg.stroke('M%s,%s L%s,%s' % (f(x), f(cap_front_y(x) + LIP_SHADOW + 2), f(x + 0.8), f(top_y(x) + ROCK_DROP - 4)),
                   mix(ROCK['body'], edge_of(ROCK['body']), 0.5), DETAIL_LINE, name='seam')
    svg.path(poly(body), 'none', edge_of(ROCK['body']), DETAIL_LINE, name='rock outline')
    lobes = [(x, cap_front_y(x) + 1 + TONGUES * max(0.0, math.sin(x / 4.5)) ** 1.5) for x in xs]
    svg.path(poly(lobes + [(x, cap_front_y(x) - 3) for x in reversed(xs)]), mix(GRASS['crest'], GRASS['mid'], 0.4),
             name='turf over the ledge')
    svg.close()


def pour_top_y(x):
    """The water's top at x as it curls forward over the lip: an arc bowing up from its left shoulder to its right
    edge, its left end LIP[0] px under the turf and its right end LIP[1] px higher."""
    xa, xb = fall_edges(FALL_TOP)
    xa += (xb - xa) * ROLL_RADIUS
    u = (x - xa) / (xb - xa)
    left = cap_front_y(xa) + LIP[0]
    return left - LIP[1] * u - LIP[2] * math.sin(math.pi * u)


def pour_outline():
    """([(x, y)] the pour's rounded left shoulder from its top down to the leaning edge, [(x, y)] its top, the lip's
    arc, from the shoulder to where its right shoulder turns down)."""
    xa, xb = fall_edges(FALL_TOP)
    r = (xb - xa) * ROLL_RADIUS
    n = 12
    xs = [xa + r + (xb - ROLL_RIGHT - xa - r) * k / n for k in range(n + 1)]
    top = [(x, pour_top_y(x)) for x in xs]
    cy = top[0][1] + r
    shoulder = [(xa + r - r * math.sin(math.pi / 2 * k / 6), cy - r * math.cos(math.pi / 2 * k / 6)) for k in range(7)]
    return shoulder, top


def right_shoulder():
    """[(x, y)] the pour's right shoulder from the lip's arc's end, turning down to the falls' straight right edge."""
    x0, y0 = pour_outline()[1][-1]
    return [(x0 + ROLL_RIGHT * math.sin(math.pi / 2 * k / 4), y0 + ROLL_RIGHT * (1 - math.cos(math.pi / 2 * k / 4)))
            for k in range(1, 5)]


def roll_top_y(x):
    """The roll's top at x, its arc and its right shoulder."""
    x0, y0 = pour_outline()[1][-1]
    if x <= x0:
        return pour_top_y(x)
    return y0 + ROLL_RIGHT - math.sqrt(max(0.0, ROLL_RIGHT ** 2 - (x - x0) ** 2))


def roll_outline():
    """[(x, y)] round the roll's left shoulder, along the lip's arc and down its right shoulder."""
    shoulder, top = pour_outline()
    return list(reversed(shoulder)) + top + right_shoulder()


def pour(svg):
    """The water rolling over the lip, the whole width of the falls' top, as painted in the markup: pale cyan shading down
    into the falls' body, solid down to its foot, faint light streaks over it and its right side a little darker.
    Its foot is the body's own colour, so where the falls come out from under it there is no line, and its left
    side carries the falls' thread of light blue, or the roll looked a step wider than the water."""
    xb = FALL_X[1]
    y_end = LIP_FOOT
    shoulder, top = pour_outline()
    svg.path(poly(pour_shape()), (WATER['pour'], pour_foot_colour(), min(y for _, y in top), y_end), name='pour')
    shade, pale = shadow_side()
    xs = [shade + (pale - shade) * k / 6 for k in range(7)]
    svg.path(poly([(x, roll_top_y(x) + CREST) for x in xs] + [(pale, y_end), (shade, y_end)]),
             WATER['shadow'], name='pour shade', extra=' fill-opacity="%s"' % POUR_SHADE)
    lower = shoulder[3:]
    svg.path(poly(lower + [(fall_edges(y_end)[0], y_end), (fall_edges(y_end)[0] + LEFT_EDGE, y_end)]
                  + [(x + LEFT_EDGE, y) for x, y in reversed(lower)]), WATER['left edge'], name='pour left edge')
    xa = fall_edges(FALL_TOP)[0]
    for share, width, lean, length in POUR_STREAKS:
        x = xa + (xb - xa) * share
        y = roll_top_y(x) + CREST
        length = min(length, y_end - STREAK_CLEAR - y)
        svg.path(poly([(x, y), (x + width, y), (x + width / 2 + lean, y + length)]), WATER['streak'],
                 name='pour streak', extra=' fill-opacity="%s"' % POUR_STREAK)


def pour_shape():
    """The roll's outline: round its shoulders, along the lip's arc and down to its foot."""
    return roll_outline() + [(FALL_X[1], LIP_FOOT), (fall_edges(LIP_FOOT)[0], LIP_FOOT)]


def pour_foot_colour():
    """The roll's colour at its foot: the falls' body, so the falls carry on from under it without a line."""
    return WATER['body']


def crest(svg):
    """The white crest along the lip's arc and round its shoulder."""
    shoulder, top = pour_outline()
    svg.path(poly(crest_band(shoulder, top, CREST)), WATER['streak'], name='crest')


def crest_glow(svg):
    """The band the crest blends on into the water under it, drawn on its own so the scene can breathe it."""
    shoulder, top = pour_outline()
    glow, opacity = CREST_GLOW
    svg.path(poly(crest_band(shoulder, top, CREST + glow)), WATER['streak'], name='crest glow',
             extra=' fill-opacity="%s"' % opacity)


def crest_band(shoulder, top, thick):
    """The band thick px deep along the lip's arc and in round its shoulders, each shoulder's arc drawn in toward its
    centre."""
    cx, cy = shoulder[0][0], shoulder[-1][1]
    r = cy - shoulder[0][1]
    right = right_shoulder()
    rx, ry = top[-1][0], top[-1][1] + ROLL_RIGHT
    keep = max(0.0, ROLL_RIGHT - thick) / ROLL_RIGHT
    outer = list(reversed(shoulder)) + top + right
    inner = [(rx + (x - rx) * keep, ry + (y - ry) * keep) for x, y in reversed(right)] + \
        [(x, y + thick) for x, y in reversed(top)] + \
        [(cx + (x - cx) * (r - thick) / r, cy + (y - cy) * (r - thick) / r) for x, y in shoulder]
    return outer + inner









def strip_top():
    """sheet px, the strip's top: just under the lowest point of the water's lip, its left shoulder, so the pour and
    the bank drawn over it hide its square top."""
    xa = FALL_X[0] + LEAN
    return math.ceil(cap_front_y(xa + (FALL_X[1] - xa) * ROLL_RADIUS) + LIP[0]) + 1


def shadow_side():
    """(x0, x1) of the deep blue shadow down the sheet's right side, inside the thin pale edge along its right."""
    xa, xb = FALL_X
    return xb - PALE_EDGE - (xb - xa) * SHADOW_SIDE, xb - PALE_EDGE


# ================================================================ gear ring

def ring_point(r, degrees):
    cx, cy = GEAR_CENTRE
    a = math.radians(degrees)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def tooth(centre):
    """One stubby tooth's polygon, rooted a little inside the ring's rim so no gap shows at its base."""
    tip_half = math.degrees(TOOTH_TIP / (GEAR_OUTER + TOOTH_HEIGHT))
    base_half = math.degrees(TOOTH_BASE / GEAR_OUTER)
    return [ring_point(GEAR_OUTER - 2, centre - base_half), ring_point(GEAR_OUTER + TOOTH_HEIGHT * 0.75, centre - tip_half - 0.6),
            ring_point(GEAR_OUTER + TOOTH_HEIGHT, centre - tip_half + 1.2), ring_point(GEAR_OUTER + TOOTH_HEIGHT, centre + tip_half - 1.2),
            ring_point(GEAR_OUTER + TOOTH_HEIGHT * 0.75, centre + tip_half + 0.6), ring_point(GEAR_OUTER - 2, centre + base_half)]


def teeth():
    """[(degrees, polygon)] round the ring, the first straight up."""
    return [(-90 + k * 360.0 / TEETH, tooth(-90 + k * 360.0 / TEETH)) for k in range(TEETH)]


def toothed_outline():
    """The ring's silhouette: the outer circle with its teeth, as a polygon."""
    pts = []
    pitch = 360.0 / TEETH
    base_half = math.degrees(TOOTH_BASE / GEAR_OUTER)
    for centre, shape in teeth():
        for deg in [centre - pitch + base_half + (pitch - 2 * base_half) * j / 4 for j in range(5)]:
            pts.append(ring_point(GEAR_OUTER, deg))
        pts += shape[1:-1]
    return pts


def arc_band(r0, r1, a0, a1, steps=24):
    outer = [ring_point(r1, a0 + (a1 - a0) * k / steps) for k in range(steps + 1)]
    inner = [ring_point(r0, a1 - (a1 - a0) * k / steps) for k in range(steps + 1)]
    return poly(outer + inner)


def within(deg, arc):
    deg = (deg - arc[0]) % 360
    return deg <= (arc[1] - arc[0]) % 360


def gear(svg):
    """The ring: warm stone, a golden rim where the sun strikes its upper right, violet shade lower left, the hole's
    bore showing as a dark edge round the left and bottom of the hole."""
    cx, cy = GEAR_CENTRE
    svg.open('gear ring')
    silhouette = poly(toothed_outline())
    inner = circle(cx, cy, GEAR_INNER)      # wound against the toothed outline
    svg.path(silhouette + ' ' + inner, STONE['body'], name='ring face')
    # the light in two soft steps each way, on the rim only, so the lit and shaded rims blend into the body
    for a0, a1, colour, alpha in ((LIT_ARC[0], LIT_ARC[1], STONE['lit'], 0.75),
                                  (LIT_ARC[0] + 30, LIT_ARC[1] - 30, STONE['lit'], 0.8),
                                  (SHADE_ARC[0], SHADE_ARC[1], STONE['shade'], 0.6),
                                  (SHADE_ARC[0] + 25, SHADE_ARC[1] - 25, STONE['shade'], 0.5)):
        svg.path(arc_band(GEAR_INNER + 1, GEAR_OUTER, a0, a1), colour, name='ring light', extra=' fill-opacity="%s"' % alpha)
    for centre, shape in teeth():
        if within(centre, LIT_ARC):
            svg.path(poly(shape), mix(STONE['body'], STONE['lit'], 0.9), name='tooth lit')
        elif within(centre, SHADE_ARC):
            svg.path(poly(shape), mix(STONE['body'], STONE['shade'], 0.7), name='tooth shade')
    bevel = circle(cx, cy, GEAR_INNER + BEVEL) + ' ' + hole(cx, cy, GEAR_INNER)
    svg.path(bevel, mix(STONE['body'], STONE['deep'], 0.35), name='bevel')
    svg.path(arc_band(GEAR_INNER, GEAR_INNER + BEVEL, SHADE_ARC[0], SHADE_ARC[1] + 20), mix(STONE['lit'], STONE['body'], 0.3),
             name='bevel lit')
    bore = circle(cx, cy, GEAR_INNER) + ' ' + hole(cx + BORE_SHIFT[0], cy + BORE_SHIFT[1], GEAR_INNER - 1)
    svg.path(bore, STONE['bore'], name='bore')
    svg.path(circle(cx, cy, GEAR_INNER), 'none', edge_of(STONE['shade']), DETAIL_LINE, name='hole outline')
    svg.stroke(circle(cx, cy, GEAR_OUTER - 5), mix(STONE['body'], STONE['deep'], 0.5), DETAIL_LINE, name='rim groove')
    for k in range(RIVETS):
        deg = -90 + 360.0 / TEETH / 2 + k * 360.0 / RIVETS
        rx, ry = ring_point(GEAR_OUTER - 10, deg)
        svg.path(circle(rx, ry, 2.2), mix(STONE['body'], STONE['deep'], 0.6), name='rivet')
        svg.path(circle(rx + 0.7, ry - 0.7, 1.1), mix(STONE['lit'], STONE['body'], 0.3), name='rivet light')
    for deg, length in ((-140, 8), (60, 6), (120, 7), (-30, 5), (200, 6)):
        x0, y0 = ring_point(GEAR_OUTER - 3, deg)
        x1, y1 = ring_point(GEAR_OUTER - 3 - length, deg + 7)
        svg.stroke('M%s,%s L%s,%s' % (f(x0), f(y0), f(x1), f(y1)), mix(STONE['body'], STONE['deep'], 0.6), DETAIL_LINE,
                   name='crack')
    svg.path(silhouette, 'none', edge_of(STONE['body']), LINE, name='ring outline')
    svg.close()


# ================================================================ trees

def crown_lobes(x, w, h, base):
    """[(cx, cy, r)] of a crown's four lobes, w wide and h tall over the trunk's top at (x, base)."""
    return [(x, base - h * 0.55, w * 0.5), (x - w * 0.3, base - h * 0.35, w * 0.33), (x + w * 0.3, base - h * 0.38, w * 0.34),
            (x + w * 0.1, base - h * 0.8, w * 0.36)]


def tree_extent(t):
    """(x0, x1) a tree reaches, its outline included."""
    if t['kind'] == 'cypress':
        return t['x'] - t['hw'] - CYPRESS_SLACK, t['x'] + t['hw'] + CYPRESS_SLACK
    lobes = crown_lobes(t['x'] + t['lean'], t['w'], t['h'], 0)
    return min(cx - r for cx, _, r in lobes) - CROWN_EDGE, max(cx + r for cx, _, r in lobes) + CROWN_EDGE


def step_of(x):
    """Which top a tree with its foot at x stands on."""
    return 'lower' if x < SPLIT else 'upper'


def tree_foot(t):
    """Where a tree stands on its top's shelf: a little below the shelf's back edge, varying tree to tree."""
    return cap_top_y(step_of(t['x']), t['x']) + 4 + 4 * abs(math.sin(t['x'] / 3.0))


def tree_shadow(svg, x, w, foot):
    """The pool of shadow a tree stands over."""
    svg.path(poly([(x - w * 0.4 + w * 0.8 * k / 8, foot + 1.5 + 2.5 * math.sin(math.pi * k / 8)) for k in range(9)]
                  + [(x + w * 0.4, foot + 0.5), (x - w * 0.4, foot + 0.5)]), mix(GRASS['mid'], GRASS['shade'], 0.7),
             name='tree shadow', extra=' fill-opacity="0.6"')


def round_crown(svg, t):
    """A round-crowned tree standing on a top's shelf, its top lit from the upper right, its dark underlay its
    outline. A tall one's trunk leans by lean px at its top."""
    x, w, h, trunk, lean = t['x'], t['w'], t['h'], t['trunk'], t['lean']
    foot = tree_foot(t)
    if trunk:
        svg.path(poly([(x - 1.6, foot), (x + 1.6, foot), (x + lean + 1.1, foot - trunk - 2), (x + lean - 1.1, foot - trunk - 2)]),
                 TREE['trunk'], edge_of(TREE['trunk shade']), DETAIL_LINE, name='trunk')
    lobes = crown_lobes(x + lean, w, h, foot - trunk)
    svg.path(' '.join(circle(cx, cy, r + CROWN_EDGE) for cx, cy, r in lobes), edge_of(TREE['shade']), name='crown edge')
    svg.path(' '.join(circle(cx, cy, r) for cx, cy, r in lobes), TREE['body'], name='crown')
    svg.path(' '.join(circle(cx - r * 0.25, cy + r * 0.3, r * 0.75) for cx, cy, r in lobes[:2]), TREE['shade'],
             name='crown shade', extra=' fill-opacity="0.7"')
    svg.path(' '.join(circle(cx + r * 0.35, cy - r * 0.35, r * 0.45) for cx, cy, r in (lobes[2], lobes[3])),
             TREE['lit'], name='crown light', extra=' fill-opacity="0.85"')


def tree(svg, t):
    """The tree standing over its pool of shadow: one of the terrace's cypresses, drawn by its own code and hazed as
    the terrace's far ones, or a round crown."""
    foot = tree_foot(t)
    if t['kind'] == 'cypress':
        tree_shadow(svg, t['x'], t['hw'] * 2.5, foot)
        toward, haze = CYPRESS_HAZE
        terrace_trees.cypress(svg, t['x'], foot - t['h'], t['hw'], foot, rng=random.Random('%s %s' % (SEED, t['x'])),
                              haze_t=haze, toward=toward)
    else:
        tree_shadow(svg, t['x'], t['w'], foot)
        round_crown(svg, t)


def trees(svg, step, behind=False):
    """The trees on that top in front of the ring, or with behind, the ones behind it, back to front."""
    svg.open('trees behind the ring' if behind else step + ' trees')
    for t in sorted((t for t in TREES if step_of(t['x']) == step and bool(t.get('behind')) == behind),
                    key=lambda t: (tree_foot(t), t['x'])):
        tree(svg, t)
    svg.close()




# ================================================================ waterfall and spray

def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def bands(name):
    """[(colour, opacity, points)] the strip's zigzag bands within one period, from the strip's top, each band's layers
    outer to inner: a row of teeth across the strip hanging down under notches rising above it, as in the
    reference, blending out to a lighter core. Each band's teeth are of their own widths, lengths and leans, its top
    tilts a little and the bands sit at uneven heights; a band short of an edge thins out to nothing at its end, so
    the bands are not ruled right across, and no two teeth or bands match."""
    strip = STRIPS[name]
    rng = random.Random(SEED + ' ' + name)
    xa, xb = FALL_X
    thick, (hang0, hang1), notch = strip['thick'], strip['hang'], strip['notch']
    tooth, least, most = strip['tooth']
    out = []
    for at, (s0, s1) in zip(strip['at'], strip['spans']):
        y = FALL_TOP + strip['period'] * at
        tilt = rng.uniform(-BAND_TILT, BAND_TILT)
        x0, x1 = xa + (xb - xa) * s0, xa + (xb - xa) * s1
        edges = [x0 - (rng.uniform(0, tooth) if s0 == 0 else 0)]
        while edges[-1] < x1:
            edges.append(min(edges[-1] + tooth * rng.uniform(least, most), x1 + (tooth if s1 == 1 else 0)))
        points = [a + (b - a) * (0.5 + rng.uniform(-TOOTH_LEAN, TOOTH_LEAN)) for a, b in zip(edges, edges[1:])]
        rises = [rng.uniform(*notch) for _ in edges]
        drops = [rng.uniform(hang0, hang1) for _ in points]

        def full(x):
            """How much of its depth the band has at x: whole, thinning out toward an end short of the strip's edge."""
            k = 1.0
            if s0 > 0:
                k = min(k, smooth((x - x0) / TAPER))
            if s1 < 1:
                k = min(k, smooth((x1 - x) / TAPER))
            return k
        for colour, opacity, below, depth, share in strip['layers']:
            def top(x):
                return y + below + tilt * (x - xa)
            upper, lower = [], []
            for j, x in enumerate(edges):
                upper.append((x, top(x) - rises[j] * share * full(x)))
                if j < len(points):
                    px = points[j]
                    upper.append((px, top(px) + 0.5 * full(px)))
                    lower.append((px, top(px) + (thick * depth + drops[j] * share) * full(px)))
                lower.append((x, top(x) + thick * depth * 0.6 * full(x)))
            out.append((WATER[colour], opacity, upper + list(reversed(lower))))
    return out


TOOTH_LEAN = 0.2                 # share of its width a tooth's point may stand off its middle either way


def lozenge(x, y, w, h, steps=6):
    """A vertical streak as a polygon: a strip from (x, y) w wide and h tall with rounded ends."""
    r = w / 2
    cx = x + r
    top = [(cx + r * math.cos(math.pi + math.pi * k / steps), y + r + r * math.sin(math.pi + math.pi * k / steps))
           for k in range(steps + 1)]
    bottom = [(cx + r * math.cos(math.pi * k / steps), y + h - r + r * math.sin(math.pi * k / steps))
              for k in range(steps + 1)]
    return top + bottom


def ellipse(cx, cy, rx, ry, steps=24):
    return [(cx + rx * math.cos(2 * math.pi * k / steps), cy + ry * math.sin(2 * math.pi * k / steps)) for k in range(steps)]


def clipped(points, y0, y1):
    """The polygon's part between the lines y0 and y1, or [] when none of it is."""
    for keep_below, edge in ((True, y1), (False, y0)):
        out = []
        for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
            a_in = ay <= edge if keep_below else ay >= edge
            b_in = by <= edge if keep_below else by >= edge
            if a_in:
                out.append((ax, ay))
            if a_in != b_in:
                out.append((ax + (bx - ax) * (edge - ay) / (by - ay), edge))
        points = out
        if not points:
            return []
    return points


def clipped_x(points, x0, x1):
    """The polygon's part between the lines x0 and x1, or [] when none of it is."""
    return [(x, y) for y, x in clipped([(y, x) for x, y in points], x0, x1)]


def waterfall(svg, name, periods=1):
    """A strip: its zigzag bands, all within one period, its body being the shape's under it. A band running off the
    strip's top or bottom carries on past the other (each band is clipped to the strip at its place and a period
    above and below it), so the strip tiles. Drawn over more periods, the drawing repeats every period."""
    period = STRIPS[name]['period']
    y0, y1 = FALL_TOP, FALL_TOP + periods * period
    svg.open('falls ' + name)
    for colour, opacity, points in bands(name):
        for copy in range(FALL_COPIES[0], periods + FALL_COPIES[-1]):
            piece = clipped([(x, y + copy * period) for x, y in points], y0, y1)
            if piece:
                svg.path(poly(piece), colour, name='band', extra=' fill-opacity="%s"' % opacity)
    svg.close()


# ---------------------------------------------------------------- the foam

def bed_outline(n=96):
    """[(x, y)] round the foam bed, the mound the FOAM_BED circles make: along their top from left to right and
    back along their foot."""
    cx, cy = SPRAY_CENTRE
    x0 = min(cx + dx - r for dx, _, r in FOAM_BED)
    x1 = max(cx + dx + r for dx, _, r in FOAM_BED)
    top, foot = [], []
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        ys = [(cy + dy - math.sqrt(r * r - (x - cx - dx) ** 2), cy + dy + math.sqrt(r * r - (x - cx - dx) ** 2))
              for dx, dy, r in FOAM_BED if abs(x - cx - dx) < r]
        if ys:
            top.append((x, min(y for y, _ in ys)))
            foot.append((x, max(y for _, y in ys)))
    return top + list(reversed(foot))


def spray(svg):
    """The foam where the water lands: a low solid mound little wider than the falls, its shade still under it, the
    mist breathing over it, and each set of foam rising off it in a group of its own the scene moves on its own."""
    cx, cy = SPRAY_CENTRE
    bed = bed_outline()
    down, opacity = FOAM_SHADE
    svg.open('spray shade')
    svg.path(poly([(x, y + down) for x, y in bed]), SPRAY['shade'], name='spray shade', extra=' fill-opacity="%s"' % opacity)
    svg.close()
    svg.open('spray bed')
    svg.path(poly(bed), SPRAY['body'], name='foam bed')
    svg.close()
    for side, (x0, x1) in (('left', (-1e9, cx)), ('right', (cx, 1e9))):
        svg.open('spray churn mask ' + side)
        svg.path(poly(clipped_x(bed, x0, x1)), '#000000', name='churn mask')
        svg.close()
    dx, dy, rx, ry = MIST
    svg.open('spray mist')
    svg.path(poly(ellipse(cx + dx, cy + dy, rx, ry)), SPRAY['mist'], name='mist', extra=' fill-opacity="%s"' % MIST_OPACITY)
    svg.close()
    for k, puffs in enumerate(RISING):
        svg.open('spray rise %s' % 'ab'[k])
        svg.path(' '.join(circle(cx + dx, cy + dy, r) for dx, dy, r in puffs), SPRAY['body'], name='spray',
                 extra=' fill-opacity="0.8"')
        svg.close()


def churn_box():
    """(x, y, w, h) sheet px of the churn strip: one period wide, left of the spray's centre; the scene draws it there
    and again a period to the right, rolling each out from the centre."""
    cx, cy = SPRAY_CENTRE
    return cx - CHURN_PERIOD, cy - CHURN_ABOVE, CHURN_PERIOD, CHURN_HEIGHT


def churn(svg, periods=1):
    """The strip of dimples rolling out over the foam: each drawn at its place and a period either side, clipped to
    the strip, so it tiles sideways. Drawn over more periods, the drawing repeats every period."""
    x0, y0, w, h = churn_box()
    cx, cy = SPRAY_CENTRE
    svg.open('churn')
    for dx, dy, rx, ry, opacity in DIMPLES:
        for copy in range(-1, periods + 1):
            piece = clipped_x(ellipse(x0 + dx + copy * w, cy + dy, rx, ry), x0, x0 + periods * w)
            if piece:
                svg.path(poly(piece), SPRAY['shade'], name='dimple', extra=' fill-opacity="%s"' % opacity)
    svg.close()


def thrown(svg):
    """Each set of loose water thrown up from the spray, in a group of its own the scene throws up and fades."""
    cx, cy = SPRAY_CENTRE
    for k, (streaks_, drops) in enumerate(THROWN):
        svg.open('thrown water %s' % 'ab'[k])
        for dx, dy, w, h in streaks_:
            svg.path(poly(lozenge(cx + dx, cy + dy, w, h)), SPRAY['mist'], name='thrown water', extra=' fill-opacity="0.8"')
        svg.path(' '.join(circle(cx + dx, cy + dy, r) for dx, dy, r in drops), SPRAY['body'], name='drops',
                 extra=' fill-opacity="0.85"')
        svg.close()


# ================================================================ sheet

def mesa(svg, rng):
    """The clump behind the ring, the ring standing behind the upper top, the mound in front of its lower half, each
    flat top's shelf with its trees standing on it, the upper one first so the lower top's trees stand in front,
    then the ledge at the falls."""
    svg.open('mesa')
    trees(svg, 'upper', behind=True)
    gear(svg)
    land(svg, rng)
    shelf(svg, 'upper')
    trees(svg, 'upper')
    shelf(svg, 'lower')
    trees(svg, 'lower')
    svg.close()


def main():
    svg = Svg()
    rng = random.Random(SEED)
    svg.open('gear-arch mesa')
    mesa(svg, rng)
    falls_shape(svg)
    falls_mask(svg)
    for name in STRIPS:
        waterfall(svg, name)
    falls_lip(svg)
    spray(svg)
    churn(svg)
    thrown(svg)
    svg.close()
    svg.write(cutting.sheet_path('scenery/mesa.svg'))


def fall_edges(y):
    """(left, right) x of the water the frame leaves showing at height y: the right edge the strip's own, dropping
    straight, the left LEAN px in at the lip and leaning out to the strip's edge at its foot, wavering a little."""
    t = max(0.0, min(1.0, (y - FALL_TOP) / FALL_PERIOD))
    return FALL_X[0] + LEAN * (1 - t) + WAVER[0] * math.sin(2 * math.pi * WAVER[1] * t), FALL_X[1]


def fall_width(y):
    """px of the strip the frame leaves showing at height y."""
    left, right = fall_edges(y)
    return right - left


def water_shape():
    """The falls' outline from the strip's top, under the lip, down the leaning edge to the foam, and up the straight
    right edge. The strips are drawn only inside it, so no band passes the foam; the lip is solid over its top, so
    none shows above the lip's foot either, and the lip's foot fades out over water of its own colour, not rock."""
    return roll_outline() + [(FALL_X[1], FOAM_LINE)] + list(reversed(left_edge(LIP_FOOT)))


def left_edge(y0):
    """[(x, y)] down the falls' leaning left edge from y0 to the foam."""
    y1 = FOAM_LINE
    return [(fall_edges(y0 + (y1 - y0) * k / 24)[0], y0 + (y1 - y0) * k / 24) for k in range(25)]


def falls_shape(svg):
    """The water's body in its shape, under the strips: the cyan sheet paling toward the foam as it goes to foam, its
    deep blue shadow side near the right deepening from the lip's shade, the thin pale edge along it, and a thread of
    light blue down its left edge."""
    shade, pale = shadow_side()
    y0, y1 = FALL_TOP, FOAM_LINE
    svg.open('falls shape')
    svg.path(poly(water_shape()), (WATER['body'], mix(WATER['body'], '#ffffff', FOOT_PALE), LIP_FOOT, y1), name='water')
    svg.path(poly(clipped([(shade, y0), (pale, y0), (pale, y1), (shade, y1)], y0, y1)),
             (mix(WATER['body'], WATER['shadow'], POUR_SHADE), WATER['shadow'], LIP_FOOT, LIP_FOOT + SHADOW_FADE),
             name='water shadow')
    svg.path(poly([(pale, y0), (FALL_X[1], y0), (FALL_X[1], y1), (pale, y1)]), WATER['edge'], name='water edge')
    edge = left_edge(LIP_FOOT)
    svg.path(poly(edge + [(x + LEFT_EDGE, y) for x, y in reversed(edge)]), WATER['left edge'], name='water left edge')
    svg.close()


def falls_mask(svg):
    """The water's silhouette in black: the scene adds it to itself, changing nothing, as the mask the front strip is
    cut to, since the engine masks a node only to its earlier siblings and allows one masked node a parent."""
    svg.open('falls mask')
    svg.path(poly(water_shape()), '#000000', name='mask')
    svg.close()


def falls_lip(svg):
    """Drawn over the falls: the water rounding over the lip, its silhouette in black as the mask for the front strip's
    cut over it, its white crest and the crest's glow over them."""
    svg.open('falls lip')
    pour(svg)
    svg.close()
    svg.open('lip mask')
    svg.path(poly(pour_shape()), '#000000', name='lip mask')
    svg.close()
    svg.open('falls crest')
    crest(svg)
    svg.close()
    svg.open('falls crest glow')
    crest_glow(svg)
    svg.close()


def band_spans(name):
    """[(top, bottom)] sheet px of each band of the strip within its first period, its outer layer's."""
    layers = bands(name)[::len(STRIPS[name]['layers'])]
    return [(min(y for _, y in pts), max(y for _, y in pts)) for _, _, pts in layers]


FALL_TOP = strip_top()
LIP_FOOT = FALL_TOP + POUR_CURL
FOAM_LINE = SPRAY_CENTRE[1] + 1      # the falls end here, inside the still foam bed


def lip_box():
    """(x, y, w, h) sheet px of the lip's parts: a whole number of canvas units up and left of the strip's corner, so
    the lip's cuts of the strips line up with the falls', and an even height, as every part's."""
    h = LIP_ABOVE + POUR_CURL
    return FALL_X[0] - LIP_SIDE, FALL_TOP - LIP_ABOVE, FALL_X[1] - FALL_X[0] + 2 * LIP_SIDE, h + h % 2


def spray_box():
    left, up, w, h = SPRAY_BOX
    return SPRAY_CENTRE[0] - left, SPRAY_CENTRE[1] - up, w, h


def strip_part(root, grads, name):
    """A strip as an image exactly one period tall, cut where it hangs from the lip."""
    box = (FALL_X[0], FALL_TOP, FALL_X[1] - FALL_X[0], STRIPS[name]['period'])
    return cutting.Part('scenery/parts/mesa/falls-' + name,
                        svgtools.part_svg('mesa-falls-' + name, [cutting.find_group(root, 'falls ' + name)], grads, box), box)


def cut():
    """[(template id, its image)]: the mesa with its ring and trees, the water's shape and its black silhouette, the
    two strips, the lip's layers and the spray's."""
    root, grads = cutting.load('scenery/mesa.svg')
    box = (FALL_X[0], FALL_TOP, FALL_X[1] - FALL_X[0], FALL_PERIOD)
    falls = [(tid, cutting.Part('scenery/parts/mesa/' + tid[len('mesa-'):],
                                svgtools.part_svg(tid, [cutting.find_group(root, group)], grads, box), box))
             for tid, group in (('mesa-falls-shape', 'falls shape'), ('mesa-falls-mask', 'falls mask'))]
    return [('mesa', cutting.static_part('scenery/parts/mesa/mesa', [cutting.find_group(root, 'mesa')], grads, 'mesa'))] + \
        falls + [('mesa-falls-' + name, strip_part(root, grads, name)) for name in STRIPS] + \
        lip_layers(root, grads) + spray_layers(root, grads)


def lip_layers(root, grads):
    """The lip, its black silhouette, its crest and the crest's glow, cut to the lip's box, and each strip cut again
    from the box's corner, a period tall, to slide over the lip as it does down the falls."""
    x, y, w, h = lip_box()
    lip = layers(root, grads, 'falls-lip', ['falls lip', 'lip mask', 'falls crest', 'falls crest glow'], (x, y, w, h))
    cuts = []
    for tid, name in (('mesa-lip-sheets', 'back'), ('mesa-lip-front', 'front')):
        box = (x, y, w, STRIPS[name]['period'])
        strip = svgtools.part_svg(tid, [cutting.find_group(root, 'falls ' + name)], grads, box)
        cuts.append((tid, cutting.Part('scenery/parts/mesa/' + tid[len('mesa-'):], strip, box)))
    return lip + cuts


def spray_layers(root, grads):
    """The spray's still layers and its rising sets, all cut to one box, and the churn strip, one period wide."""
    out = layers(root, grads, 'spray', ['spray shade', 'spray bed', 'spray churn mask left', 'spray churn mask right',
                                        'spray mist', 'spray rise a', 'spray rise b', 'thrown water a', 'thrown water b'],
                 spray_box())
    box = churn_box()
    strip = svgtools.part_svg('mesa-spray-churn', [cutting.find_group(root, 'churn')], grads, box)
    return out + [('mesa-spray-churn', cutting.Part('scenery/parts/mesa/spray-churn', strip, box))]


def layers(root, grads, name, groups, box):
    """[(template id, its image)] of each group, all cut to the box, so the scene stacks them at one place and
    animates each on its own: the first named mesa-<name>, the rest after their group."""
    elements = [cutting.find_group(root, g) for g in groups]
    ids = ['mesa-' + name] + ['mesa-' + g.replace(' ', '-') for g in groups[1:]]
    return [(tid, cutting.Part('scenery/parts/mesa/' + tid[len('mesa-'):], svgtools.part_svg(tid, [e], grads, box), box))
            for tid, e in zip(ids, elements)]


def parts():
    return [part for _, part in cut()]


if __name__ == '__main__':
    main()

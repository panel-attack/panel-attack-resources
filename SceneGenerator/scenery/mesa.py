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
#   fluted: vertical columns of uneven widths, lighter facets catching the light and deep gaps between them, a
#   fainter lower tier of columns part way down. Every outline it does have, the ring's, the ledge's and the trees', is the
#   Esme terrace's: a dark shade of its own shape's colour (scenery/spring_valley.py's edge_of), as thin as the
#   terrace's at that distance, never a navy ink. The trees are the terrace's own kinds: its flame-shaped cypresses
#   (plants/trees.py) hazed as its far shore's are, among round crowns, standing in loose clumps clear of the falls,
#   a clump behind the ring showing through its hole.
#   The sun is to the upper right: the upper block's face is lit and its right edge brightest, the lower block
#   stands in its shadow, the cleft the water runs down is the deepest shade, the ledge's rock is lit along its top
#   right and the ring's upper-right rim catches the light.
#
#   The waterfall is drawn as a strip one FALL_PERIOD tall whose streaks repeat every period (each is clipped to
#   the strip at its place and a period above and below it), so the strip tiles top to bottom and the scene can
#   scroll it with wrap: repeat to make the water fall. The mist is its own image, drawn over the strip's foot, and
#   the falls frame another, drawn over the strip: the gully's shaded wall covering the strip's left side above a
#   line leaning out down the drop, so as in the reference the water pours from a lip nearly as wide as the sheet
#   below, its right edge dropping straight and its left edge leaning out, and the water rounding smoothly over the
#   lip under a white crest.

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
LEFT, RIGHT = 262, 544           # sheet px, the cliffs' outer edges at their foot
FOOT = 452                       # sheet px, where the land is cut off, hidden under the hills
SPLIT = 408                      # sheet px, where the lower top on the left ends at the riser up to the upper top
BANK_RUN = 5                     # px the riser between the two tops runs for: a sheer step of rock, not a bank
LOWER_LIP, UPPER_LIP = 352, 340  # sheet px, each top's front edge at its ends; the tops dome up between
LOWER_TILT = 5                   # px the lower top's lip drops toward its left end
SHELF = (7, 2)                   # px of each flat top seen above its lip at the top's ends, and the extra toward its middle
BATTER = 8                       # px each cliff's foot stands out past its lip corner: a wall leaning back a little
SHELF_FADE = 0.3                 # how far the cap shades from its mid green toward the shade at its back edge
GRASS = {'crest': '#eef49c', 'mid': '#c2dc86', 'shade': '#96c07a'}   # the caps' turf, the reference's yellow-green
# the cliffs' rock: the face in the sun, its brightest lit edge and the warm slab beside the cleft; the shade the
# lower block stands in and the recesses between the columns; the hills' blue every face hazes to at the foot
CLIFF = {'lit': '#e8d8dc', 'face': '#d2c4ce', 'warm': '#dcc6c2', 'facet': '#bcb0cc', 'shade': '#6690d2', 'recess': '#6c8fd0',
         'deep': '#5878be', 'foot': '#6a92d4'}
# the columns in the sun and in the shadow, two tones by turns, and the deep gap between one column and the next:
# (colour, opacity) over the face
FLUTES = {'lit': (('#ecdee2', 0.65), ('#c6bad0', 0.35)), 'shade': (('#92aadc', 0.5), ('#6a88cc', 0.4))}
GAPS = {'lit': ('#5e84c8', 0.75), 'shade': ('#4670b8', 0.75)}
LIT_SLAB = (30, 22)              # px wide the sunlit slab of the lower block beside the cleft is, at the lip and at the foot
CLEFT_SHADE = (34, 24)           # px past the riser the upper block's shaded left face reaches, at the lip and at the foot
FOOT_HAZE = (0.85, 30, 10)       # how far each face's colour goes toward the foot's blue, px below the lip it starts, px above the foot it is there
UNDERCUT = 5                     # px, the dark band under the cap where the turf overhangs the rock
DRIPS = (2, 8)                   # px the turf hangs over the lip in tongues, least and most
FLUTE_TOP = (6, 14)              # px under the lip a column's rounded top starts, least and most, so the tops are uneven
TIER = 0.55                      # share of the drop below the lip the lower tier of columns starts at
TIER_WIDTH = (3, 7)              # px, a lower-tier column's width, least and most: narrower, being shorter
TIER_FADE = 0.6                  # how strong the lower tier is against the row above it
FLUTE_WIDTH = (5, 20)            # px, a column's width, least and most
FLUTE_GAP = (1, 2.5)             # px between one column and the next, the deep gap
FLUTE_LEAN = 4                   # px a column's foot may be offset from its top either way, so the columns are not ruled
FLUTE_TAPER = 3                  # px a column may narrow or widen by toward its foot
LIT_EDGE = 9                     # px wide the lit band down the upper block's right edge is
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

# ---------------------------------------------------------------- the gear ring
GEAR_TOP = 244                   # sheet px, the topmost tooth's tip
GEAR_CENTRE = (430, 318)
GEAR_OUTER, GEAR_INNER = 66, 46  # px, the ring face's radii
TEETH, TOOTH_HEIGHT = 12, 8
TOOTH_BASE, TOOTH_TIP = 12, 9    # px, half a tooth's width at its base and its tip
BORE_SHIFT = (4, -3)             # px the far side of the hole's bore is offset: the ring seen from a little left and below
BEVEL = 4                        # px, the bevelled ring round the hole
RIVETS = 8                       # round the rim
STONE = {'lit': '#f3e2c4', 'body': '#cdb4ae', 'shade': '#8d8cb4', 'deep': '#6f7fb5', 'bore': '#8d86a6'}
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
FALL_X = (343, 383)              # sheet px, the strip's edges; the frame narrows the water at the lip
FALL_TOP = 356                   # sheet px, the strip's top, in the notch under the lower step's lip
FALL_PERIOD = 96                 # px, the strip's height: its streaks repeat every period
FALL_COPIES = (-1, 1)            # each streak is drawn at its place and from a period above to one below, so the strip tiles
NOTCH = 6                        # px the lip dips where the water pours out
LEAN = 4                         # px the falls' left edge leans out over the strip's height, from the lip to its foot
WAVER = (0.8, 2)                 # (px, waves) the left edge wavers about its lean down the strip, still at its ends
LIP = (2, 5, 2)                  # (px the lip's left end sits under the turf, px its right end stands higher, px it bows up)
CREST = 4.0                      # px, the white crest along the lip
WATER = {'body': '#bfe6f8', 'edge': '#e2f4fc', 'streak': '#ffffff', 'shadow': '#4f8fd2', 'shadow streak': '#8cc0ea'}
SHADOW_SIDE = 0.25               # share of the strip's width the sheet's deep blue shadow side takes, near its right
PALE_EDGE = 1.5                  # px of pale water along the sheet's right edge, outside its shadow side
VEIL = (24, (0.5, 0.38, 0.26, 0.15, 0.06))   # (px down from the lip, white's opacity each step) of the white fading down
STREAKS = 16                     # bright and shaded streaks down the strip
SPRAY = {'body': '#eef6fd', 'shade': '#d8eaf7', 'mist': '#e9f3fc'}
SPRAY_CENTRE = (364, 448)
SPRAY_PUFFS = [(-30, 4, 7), (-18, 0, 9), (-6, -3, 10), (6, -3, 10), (18, 0, 9), (30, 4, 7), (-40, 7, 5), (40, 7, 5),
               (-12, 2, 8), (10, 2, 8)]     # (dx, dy, r) round SPRAY_CENTRE: one low mass of foam
SPRAY_STREAKS = [(-14, -22, 3, 12), (8, -26, 3, 14), (-2, -14, 2.5, 8)]   # (dx, dy, w, h) loose water thrown up from it


def circle(cx, cy, r):
    return 'M%s,%s A%s,%s 0 1,0 %s,%s A%s,%s 0 1,0 %s,%s Z' % (f(cx - r), f(cy), f(r), f(r), f(cx + r), f(cy), f(r),
                                                              f(r), f(cx - r), f(cy))


def hole(cx, cy, r):
    """A circle wound against circle()'s, so a path holding both leaves it empty under the nonzero fill rule."""
    return 'M%s,%s A%s,%s 0 1,1 %s,%s A%s,%s 0 1,1 %s,%s Z' % (f(cx - r), f(cy), f(r), f(r), f(cx + r), f(cy), f(r),
                                                              f(r), f(cx - r), f(cy))


def edge_x(x_foot, y, lean):
    """An outer cliff's x at height y: x_foot at FOOT, leaning back by BATTER at the lip."""
    t = (FOOT - y) / (FOOT - UPPER_LIP)
    return x_foot + lean * BATTER * t


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
    """The top edge from the left lip corner to the right one, along both tops and the riser between."""
    return [(LIP_LEFT + (LIP_RIGHT - LIP_LEFT) * k / n, top_y(LIP_LEFT + (LIP_RIGHT - LIP_LEFT) * k / n)) for k in range(n + 1)]


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


def flute(x0, x1, top_of, lean, taper):
    """A column's polygon: a rounded top at top_of(x), x0 to x1 wide, down to the foot with its foot offset by lean and
    taper px wider each side, or narrower."""
    r = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    top = [(x, top_of(x) + dy) for x, dy in ((x0, r * 0.45), (x0 + r * 0.3, r * 0.12), (cx, 0), (x1 - r * 0.3, r * 0.12), (x1, r * 0.45))]
    return poly(top + [(x1 + lean + taper, FOOT), (x0 + lean - taper, FOOT)])


def column_row(svg, step, rng, top_of, widths=FLUTE_WIDTH, fade=1.0):
    """A row of columns across a block's face, their tops at top_of(x) shifted unevenly, side by side with a deep gap
    between each and the next, of uneven widths, leans and tapers, lighter and darker by turns, none where the water
    runs down, widths px wide; those in shade are the blue-lilac, the rest the sunlit pink, all fainter by fade."""
    x0, x1 = block_span(step)
    x = x0 + rng.uniform(0, 3)
    k = 0
    while x + widths[0] < x1 - 1:
        w = min(rng.uniform(*widths), x1 - 1 - x)
        gap = rng.uniform(*FLUTE_GAP)
        if not in_the_cleft(x, x + w + gap):
            light = 'shade' if shaded_at(x + w / 2) else 'lit'
            colour, alpha = FLUTES[light][k % 2]
            drop = rng.uniform(*FLUTE_TOP)
            svg.path(flute(x, x + w, lambda xx: top_of(xx) + drop, rng.uniform(-FLUTE_LEAN, FLUTE_LEAN),
                           rng.uniform(-FLUTE_TAPER, FLUTE_TAPER)), hazed(colour), name='flute',
                     extra=' fill-opacity="%s"' % round(alpha * fade, 3))
            if x + w + gap < x1 - 1:
                gap_colour, gap_alpha = GAPS[light]
                svg.path(poly([(x + w - 0.5, top_of(x + w) + drop + 2), (x + w + gap, top_of(x + w + gap) + drop + 2),
                               (x + w + gap, FOOT), (x + w - 0.5, FOOT)]), hazed(gap_colour), name='gap',
                         extra=' fill-opacity="%s"' % round(gap_alpha * fade, 3))
            k += 1
        x += w + gap


def flutes(svg, step, rng):
    """The columns down a block's face: a row from under the cap to the foot, and a fainter lower tier starting part way
    down over it, so the face reads as stacked columns."""
    column_row(svg, step, rng, cap_front_y)
    column_row(svg, step, rng, lambda x: lip_y(step, x) + (FOOT - lip_y(step, x)) * TIER, widths=TIER_WIDTH, fade=TIER_FADE)


def undercut(svg):
    """The dark band under the caps where the turf overhangs the rock, along both tops and down the riser."""
    xs = [LIP_LEFT + (LIP_RIGHT - LIP_LEFT) * k / 96 for k in range(97)]
    band = [(x, cap_front_y(x)) for x in xs] + [(x, cap_front_y(x) + UNDERCUT + 0.8 * math.sin(x / 4.0)) for x in reversed(xs)]
    svg.path(poly(band), CLIFF['deep'], name='undercut', extra=' fill-opacity="0.7"')


def shelf(svg, step):
    """A flat top seen a little from above: the sunlit cap from its back edge down to its front edge, the lip,
    brightest along the lip, its turf hanging over the lip in tongues."""
    xs = samples(step, 48)
    front = [(x, cap_front_y(x) + 1) for x in xs]
    band = [(x, cap_top_y(step, x)) for x in xs] + list(reversed(front))
    y0, y1 = min(y for _, y in band), max(y for _, y in band)
    drips = [(x, cap_front_y(x) - 1) for x in xs] + [(x, cap_front_y(x) + drip_depth(x)) for x in reversed(xs)]
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
    y0 = top_y((xa + xb) / 2) + NOTCH
    svg.path(poly([(xa - HOLLOW, y0 - NOTCH), (xb + HOLLOW, y0 - NOTCH), (xb + HOLLOW + 4, FOOT), (xa - HOLLOW - 4, FOOT)]),
             hollow_colour(), name='hollow')
    svg.path(poly([(xa - 1, y0 - NOTCH), (xb + 1, y0 - NOTCH), (xb + 2, FOOT), (xa - 2, FOOT)]), ROCK['wet'], name='wet rock')


def land(svg, rng):
    """The rock of both blocks in the sun's pink-lilac, the broad shadow over the lower block up to its warm sunlit
    slab beside the cleft, the upper block's shaded left face from the cleft and the lit band down its right edge, each
    face fluted, the cleft under the falls, and the undercut under the caps."""
    svg.open('land')
    svg.path(poly(outline()), hazed(CLIFF['face']), name='rock')
    y_corner = top_y(LIP_LEFT)
    for reach, alpha in ((0, 1.0), (-LIT_SLAB[0] * 0.3, 0.4)):
        svg.path(poly([(LIP_LEFT - 1, y_corner - 1), (slab_edge_x(y_corner) + reach, y_corner - 1),
                       (slab_edge_x(FOOT) + reach, FOOT), (LEFT - 1, FOOT)]), hazed(CLIFF['shade']), name='left shade',
                 extra=' fill-opacity="%s"' % alpha)
    svg.path(poly([(slab_edge_x(y_corner), y_corner - 1), (FALL_X[0], y_corner - 1), (FALL_X[0], FOOT), (slab_edge_x(FOOT), FOOT)]),
             hazed(CLIFF['warm']), name='lit slab', extra=' fill-opacity="0.9"')
    y_top = top_y(FALL_X[1])
    for reach, alpha in ((0, 1.0), (-CLEFT_SHADE[0] * 0.3, 0.4)):
        svg.path(poly([(FALL_X[1], y_top - 1), (cleft_shade_x(y_top) + reach, y_top - 1), (cleft_shade_x(FOOT) + reach, FOOT),
                       (FALL_X[1], FOOT)]), hazed(CLIFF['shade']), name='cleft shade', extra=' fill-opacity="%s"' % alpha)
    right = wall(RIGHT, -1)
    svg.path(poly(right + [(x - LIT_EDGE, y) for x, y in reversed(right)]), hazed(CLIFF['lit']), name='lit edge',
             extra=' fill-opacity="0.5"')
    for step in ('lower', 'upper'):
        flutes(svg, step, rng)
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
    arc, from the shoulder to the right edge)."""
    xa, xb = fall_edges(FALL_TOP)
    r = (xb - xa) * ROLL_RADIUS
    n = 12
    top = [(xa + r + (xb - xa - r) * k / n, pour_top_y(xa + r + (xb - xa - r) * k / n)) for k in range(n + 1)]
    cy = top[0][1] + r
    shoulder = [(xa + r - r * math.sin(math.pi / 2 * k / 6), cy - r * math.cos(math.pi / 2 * k / 6)) for k in range(7)]
    return shoulder, top


def pour(svg):
    """The water rolling over the lip, the whole width of the falls' top: light blue under a white crest along the
    lip's arc, its left shoulder rounding over the edge, the shadow side starting a little below the crest."""
    xb = FALL_X[1]
    y_end = FALL_TOP + POUR_CURL
    shoulder, top = pour_outline()
    rim = list(reversed(shoulder)) + top
    svg.path(poly(rim + [(xb, y_end), (fall_edges(y_end)[0], y_end)]), WATER['body'], name='pour')
    shade, pale = shadow_side()
    svg.path(poly([(shade, pour_top_y(shade) + CREST), (pale, pour_top_y(pale) + CREST), (pale, y_end), (shade, y_end)]),
             WATER['shadow'], name='pour shade')
    crest = list(reversed(shoulder[:3])) + top
    svg.path(poly(crest + [(x, y + CREST) for x, y in reversed(crest)]), WATER['streak'], name='crest')








def veil(svg):
    """The white of the water just over the lip, fading down the falls in steps: brightest where the sheet is thin
    and fast, the light blue body showing through lower down."""
    shade, _ = shadow_side()
    step = VEIL[0] / len(VEIL[1])
    for k, alpha in enumerate(VEIL[1]):
        y0, y1 = FALL_TOP + k * step, FALL_TOP + (k + 1) * step
        svg.path(poly([(fall_edges(y0)[0], y0), (shade, y0), (shade, y1), (fall_edges(y1)[0], y1)]), WATER['streak'], name='veil',
                 extra=' fill-opacity="%s"' % alpha)


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
    """The trees on that top in front of the ring, or with behind, the ones behind it."""
    svg.open('trees behind the ring' if behind else step + ' trees')
    for t in TREES:
        if step_of(t['x']) == step and bool(t.get('behind')) == behind:
            tree(svg, t)
    svg.close()


# ================================================================ waterfall and spray

def streaks(rng):
    """[(x, y, w, h, colour)] the strip's streaks within one period, y measured from the strip's top: white wisps
    over the pale left of the sheet, thin pale ones breaking into its shadow side."""
    xa, xb = FALL_X
    shade, pale = shadow_side()
    out = []
    for k in range(STREAKS):
        shaded = k % 4 == 3
        w = rng.uniform(1, 1.8) if shaded else rng.uniform(2, 5)
        x = rng.uniform(shade + 0.5, pale - 0.5 - w) if shaded else rng.uniform(xa + 1, shade - w)
        y = rng.uniform(0, FALL_PERIOD)
        h = rng.uniform(30, 70)
        out.append((x, y, w, h, WATER['shadow streak'] if shaded else WATER['streak']))
    return out


def wisp(x, y, w, h, steps=6):
    """A streak of falling water as a polygon: rounded at its top, w wide, narrowing a little to a blunt end h px below."""
    r = w / 2
    cx = x + r
    top = [(cx + r * math.cos(math.pi + math.pi * k / steps), y + r + r * math.sin(math.pi + math.pi * k / steps))
           for k in range(steps + 1)]
    return top + [(cx + r * 0.8, y + h * 0.8), (cx + r * 0.3, y + h), (cx - r * 0.3, y + h), (cx - r * 0.7, y + h * 0.85)]


def lozenge(x, y, w, h, steps=6):
    """A vertical streak as a polygon: a strip from (x, y) w wide and h tall with rounded ends."""
    r = w / 2
    cx = x + r
    top = [(cx + r * math.cos(math.pi + math.pi * k / steps), y + r + r * math.sin(math.pi + math.pi * k / steps))
           for k in range(steps + 1)]
    bottom = [(cx + r * math.cos(math.pi * k / steps), y + h - r + r * math.sin(math.pi * k / steps))
              for k in range(steps + 1)]
    return top + bottom


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


def waterfall(svg, rng, periods=1):
    """The strip: the water's body with feathered edges and its streaks, all within one period. A streak running
    off the strip's bottom carries on from its top (each streak is clipped to the strip at its place and a period
    above and below it), so the rows at the strip's top are the rows past its bottom and it tiles. Drawn over more
    periods, the drawing repeats every period."""
    xa, xb = FALL_X
    y0, y1 = FALL_TOP, FALL_TOP + periods * FALL_PERIOD
    svg.open('waterfall')
    svg.path(poly([(xa, y0), (xb, y0), (xb, y1), (xa, y1)]), WATER['body'], name='water')
    shade, pale = shadow_side()
    svg.path(poly([(shade, y0), (pale, y0), (pale, y1), (shade, y1)]), WATER['shadow'], name='water shadow')
    svg.path(poly([(pale, y0), (xb, y0), (xb, y1), (pale, y1)]), WATER['edge'], name='water edge')
    for x, y, w, h, colour in streaks(rng):
        for copy in range(FALL_COPIES[0], periods + FALL_COPIES[-1]):
            piece = clipped(wisp(x, y0 + y + copy * FALL_PERIOD, w, h), y0, y1)
            if piece:
                svg.path(poly(piece), colour, name='streak', extra=' fill-opacity="0.9"')
    svg.close()


def spray(svg):
    """The mist where the water lands: a low, wide plume spreading both ways, thinning at its ends."""
    cx, cy = SPRAY_CENTRE
    svg.open('spray')
    svg.path(' '.join(circle(cx + dx, cy + dy + 1.5, r) for dx, dy, r in SPRAY_PUFFS), SPRAY['shade'], name='spray shade',
             extra=' fill-opacity="0.4"')
    svg.path(' '.join(circle(cx + dx, cy + dy, r * 0.9) for dx, dy, r in SPRAY_PUFFS), SPRAY['body'], name='spray', extra=' fill-opacity="0.85"')
    for dx, dy, w, h in SPRAY_STREAKS:
        svg.path(poly(lozenge(cx + dx, cy + dy, w, h)), SPRAY['mist'], name='thrown water', extra=' fill-opacity="0.8"')
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
    ledge(svg)
    svg.close()


def main():
    svg = Svg()
    rng = random.Random(SEED)
    svg.open('gear-arch mesa')
    mesa(svg, rng)
    waterfall(svg, random.Random(SEED + ' waterfall'))
    spray(svg)
    falls_frame(svg)
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


def falls_frame(svg):
    """Drawn over the strip: the gully's shaded wall covering the strip's left side beside the leaning edge, the white
    fading down from the lip, and the water rounding over the lip under its white crest."""
    shoulder, _ = pour_outline()
    xl = FALL_X[0] - HOLLOW - 1
    y0, y1 = shoulder[-1][1], FALL_TOP + FALL_PERIOD
    ys = [y0 + (y1 - y0) * k / 24 for k in range(25)]
    edge = [(fall_edges(y)[0], y) for y in ys]
    turf = [(xl + (shoulder[0][0] - xl) * k / 6, cap_front_y(xl + (shoulder[0][0] - xl) * k / 6) + 1) for k in range(7)]
    svg.open('falls frame')
    svg.path(poly([(xl, y1)] + list(reversed(edge)) + list(reversed(shoulder)) + list(reversed(turf))), hollow_colour(),
             name='left bank')
    veil(svg)
    pour(svg)
    svg.close()


def strip_part(group, grads):
    """The waterfall as an image exactly one period tall, cut where it hangs from the lip."""
    box = (FALL_X[0], FALL_TOP, FALL_X[1] - FALL_X[0], FALL_PERIOD)
    return cutting.Part('scenery/parts/mesa/waterfall', svgtools.part_svg('mesa-waterfall', [group], grads, box), box)


def cut():
    """[(template id, its image)]: the mesa with its ring and trees, the waterfall strip, the spray, and the frame
    drawn over the strip."""
    root, grads = cutting.load('scenery/mesa.svg')
    return [('mesa', cutting.static_part('scenery/parts/mesa/mesa', [cutting.find_group(root, 'mesa')], grads, 'mesa')),
            ('mesa-waterfall', strip_part(cutting.find_group(root, 'waterfall'), grads)),
            ('mesa-spray', cutting.static_part('scenery/parts/mesa/spray', [cutting.find_group(root, 'spray')], grads,
                                               'mesa-spray')),
            ('mesa-falls-frame', cutting.static_part('scenery/parts/mesa/falls-frame', [cutting.find_group(root, 'falls frame')],
                                                     grads, 'mesa-falls-frame'))]


def parts():
    return [part for _, part in cut()]


if __name__ == '__main__':
    main()


#   Library, writes nothing: the train meadow's land, measured in sheet px off
#   panel-attack-references/TrainMeadow/stage.png, in the day valley's terms (scenery/valley.py).

# Each hill back to front: (name, depth 0 far .. 1 near, its top edge as points left to right). A hill that stops
# inside the land runs its ends down under the hill in front. The mesa's foot hides behind the far hills left of
# centre; trees and bushes can stand on any of these edges.
HILLS = [
    ('hills far', 0.0, [(-40, 424), (100, 408), (220, 392), (340, 378), (450, 372), (560, 384), (660, 404), (780, 386),
                        (880, 394), (980, 408), (1100, 392), (1250, 374), (1380, 388), (1480, 404), (1576, 412)]),
    ('hills far left', 0.2, [(-40, 434), (60, 410), (160, 396), (260, 404), (380, 414), (460, 404), (540, 410),
                             (620, 428), (700, 452), (740, 484)]),
    ('hills far centre', 0.25, [(560, 440), (610, 408), (660, 392), (710, 396), (760, 386), (810, 392), (860, 406),
                                (910, 418), (960, 430), (1020, 446), (1100, 472)]),
    ('hills far right', 0.25, [(920, 476), (980, 450), (1040, 420), (1120, 398), (1200, 396), (1280, 410), (1360, 404),
                               (1440, 418), (1576, 440)]),
    ('hills middle', 0.5, [(-40, 478), (100, 452), (220, 436), (340, 432), (460, 440), (580, 452), (700, 462),
                           (820, 470), (940, 470), (1060, 462), (1180, 454), (1300, 450), (1420, 456), (1576, 470)]),
]


# (sunlit crest, mid tone, shaded body) of each hill: the far hills' grass paled and cooled toward the sky's blue by
# the distance, mint green nearer, the sunlit yellow-green of the near hill alone.
FAR = ('#9cdcc8', '#78ccbc', '#54b0b0')
MINT = ('#9eeaa0', '#78e0aa', '#46c0a8')
HILL_COLOURS = {
    'hills far': FAR,
    'hills far left': MINT,
    'hills far centre': ('#a0ecb0', '#7ce4b8', '#4cc0ac'),
    'hills far right': MINT,
    'hills middle': ('#c4f06a', '#92e47a', '#4ec48a'),
}


# Outlines are the Esme terrace's: a line is its shape's shade colour darkened EDGE_SHADE of the way to black, its
# hue and saturation kept, and only the near things have one, as thin as the terrace's at the same distance
# (structures/houses.py TOWN_LINE_WIDTH for the bushes by the meadow, at the train's distance); the hills, the woods
# and the bushes behind the track stand with no line, parted by their colours alone as the terrace's far hills and
# trees are.
EDGE_SHADE = 0.3


# The flat planes slanting across each hill over its shaded body: (x0, x1, drop at x0, drop at x1, depth, tone), as
# the day valley's (scenery/valley_reference.py).
PLANES = {
    'hills far': [(-40, 1576, 0, 0, 16, 'crest'), (660, 1100, 30, 56, 14, 'mid'), (460, 700, 24, 40, 18, 'shade'),
                  (1260, 1576, 22, 36, 18, 'shade')],
    'hills far left': [(-40, 700, 0, 0, 20, 'crest'), (460, 740, 26, 40, 20, 'shade')],
    'hills far centre': [(580, 1060, 0, 0, 22, 'crest'), (760, 1060, 30, 44, 22, 'shade')],
    'hills far right': [(980, 1576, 0, 0, 22, 'crest'), (1200, 1576, 30, 44, 22, 'shade')],
    'hills middle': [(-40, 1576, 0, 0, 34, 'crest'), (200, 760, 36, 60, 12, 'mid'), (900, 1500, 40, 56, 12, 'mid'),
                     (560, 980, 26, 18, 16, 'shade')],
}


# Shaded hollows: how far a hill's shaded plane leans from its mid tone toward its shade.
HOLLOW_SHADE = 0.5


# The scallops round a leafy clump's rim, as a share of the clump's radius: bushes' leaves, and the smaller crowns'.
SCALLOP = 0.5
TREE_SCALLOP = 0.5


# The tree lines along the far hills' feet and the copses on their slopes: (x of the clump's left end, x of its right
# end, the hill its crowns stand on, px their feet stand above that hill's top (negative: on its slope below the
# crest), crown width, crown height, depth 0 far .. 1 near), and their colours far .. near as (body, lit cap, shade).
# A clump standing on 'hills middle' rises behind its crest; one on a far hill stands on its slope.
WOODS = [(600, 660, 'hills far', -22, 8, 7, 0.05), (1260, 1320, 'hills far', -20, 8, 7, 0.05),
         (40, 150, 'hills middle', 2, 18, 15, 0.3), (200, 290, 'hills far left', -26, 13, 11, 0.15),
         (470, 600, 'hills middle', 2, 18, 16, 0.4), (1060, 1180, 'hills middle', 3, 20, 18, 0.5),
         (1380, 1576, 'hills middle', 3, 22, 21, 0.7), (1220, 1290, 'hills far right', -34, 12, 10, 0.1)]
WOODS_COLOURS = (('#5cc0b4', '#9ce8c8', '#48a8a8'), ('#2c9c6a', '#8ad878', '#1c7652'))
TREE_LIT_INSET = (0.42, -0.38, 0.5)   # (core radii right, up, scale) a crown's lit cap is its shape moved to its rim
FRONT_ROW_CAPS = 0.3             # share of a clump's front-row crowns with a lit cap
BACK_ROW_CAPS = 0.0              # share of a clump's back-row crowns showing a cap between the front ones
# The woods are a mixed wood, not a row of balls: each crown takes one of these silhouettes, dealt in shuffled rounds
# so every short row gets them all, its width and height the row's scaled by (w, h): round leafy balls, lumpy
# broadleaf crowns wider than tall, wide flat-topped crowns, pointed firs, tall narrow poplars and low shrubs.
CROWN_SHAPES = {'round': (1.0, 1.0), 'lumpy': (1.3, 0.9), 'flat': (1.4, 0.75), 'fir': (0.75, 1.5), 'poplar': (0.45, 1.6),
                'shrub': (1.2, 0.5)}
TAPER_STEP = 0.35                # the circles of a fir or poplar stand this many base radii apart up its height
TIP_RADIUS = 0.12                # the circle at a fir's or poplar's tip, in base radii, never under 0.6 px
TAPER_LIT = 0.45                 # a fir's or poplar's lit cap is its top share of its height, down its right side


# The leafy bushes standing behind the track and in front of it: (x of centre, y of foot, width, height), each a few
# broad lobes, big and small ones overlapping, and their colours as (body, lit crescent, shade, bright rim or
# highlight): deep blue-teal in the shade, green toward the light. The near bushes are outlined in a shade of their
# teal as the terrace's are, a mid-distance line wide; the far ones stand with no line.
BUSHES_FAR = [(320, 514, 160, 26), (600, 514, 200, 30), (720, 515, 120, 22), (990, 514, 150, 34), (1130, 515, 120, 26),
              (1240, 513, 240, 54), (1360, 515, 150, 34)]
BUSHES_NEAR = [(140, 604, 100, 54), (318, 608, 190, 78), (470, 612, 96, 42), (585, 615, 70, 18),
               (877, 615, 46, 15), (998, 615, 74, 26), (1215, 607, 130, 64), (1400, 608, 170, 82)]
BUSH_COLOURS = ('#06858f', '#40bd5c', '#05697a', '#7ccb4a')
BUSHES_FAR_COLOURS = ('#36bc92', '#74dc98', '#1e9680', '#98e680')
# A far bush's top follows one of these profiles, dealt in shuffled rounds so the row uses them all: an arch, a flat
# hedge top, a hump toward one end, or an arch with the pointed spire of a young conifer rising out of it. A humped
# top's crown stands HUMP_AT of the way in from its end and its far end rises HUMP_LOW of its height; a flat top's
# lobes rise between the FLAT_TOP shares of its height; a spire is SPIRE (height, width) bush heights.
BUSH_PROFILES = ('arch', 'flat', 'humped left', 'humped right', 'spired')
HUMP_AT = 0.18
HUMP_LOW = 0.7
FLAT_TOP = (0.88, 1.0)
SPIRE = (1.35, 0.7)
LOBE_REACH = 0.7                 # a lobe's side circles reach at least this many bush heights from its core, so a low
                                 # small lobe spreads wide and still touches its neighbours
FLAT_LOBE_SPREAD = (0.9, 1.3)    # a flat hedge's lobes are broad, their side circles this far out in core radii
BUSH_BODY_INSET = (0.12, -0.1, 0.88)   # (core radii right, radii up, scale) a lobe's body sits from its shaded shape
BUSH_LIT_INSET = (0.3, -0.26, 0.7)   # ... its lit crescent
BUSH_RIM_INSET = (0.5, -0.45, 0.5)   # ... and a sunny lobe's bright rim, reaching its upper-right edge
BUSH_RIM_FROM = 0.45             # the bright rims sit on the lobes from this share of the way across, rightward
BUSH_LOBES = 2                   # lobes across a bush's top at the least
LOBE_SPAN = 1.4                  # a bush gets a lobe per this many heights of width
LOBE_SPREAD = (0.5, 0.8)         # how far, in core radii, a mound's side circles sit out from its core


# The near bushes, each one leafy mound as in the reference: a bump about every NEAR_BUMP px along its top, each
# bump's radius one of BUMP_SIZES of the spacing between bumps, dealt in shuffled rounds so big and small bumps
# stand side by side, none over 0.6 of the bush's height; the crown somewhere
# CROWN_AT across, the top stepping down from it to SHOULDER_LEAST of the height at its ends (NEAR_DOME 1 a straight
# staircase, above 1 a fuller middle), each step's drop scaled by SHOULDER_STEP so the steps are uneven; the light
# green over each bump and its column moved by MOUND_BODY_INSET (radii right, up, scale) so the bottom of the
# mound stays in shade; and a lit cap along the top of each bump from MOUND_LIT_FROM of the way across, moved by
# MOUND_LIT_INSET.
NEAR_BUMP = 22
# A near mound's top follows one of these profiles, dealt as the far bushes' are: the dome, a flat hedge top, a hump
# to the left or right, or a saddle with a crown SADDLE_AT each way across and the top dipping to SADDLE_DIP of the
# height between them; and a share TIP_CHANCE of its bumps carries a pointed leafy tip, the TIP stack of
# (radius, rise above the bump's centre) in bump radii, where it stays within the bush's height.
MOUND_PROFILES = ('dome', 'flat', 'humped left', 'humped right', 'saddle')
SADDLE_AT = (0.22, 0.78)
SADDLE_DIP = 0.62
TIP_CHANCE = 0.3
TIP = ((0.7, 0.6), (0.5, 1.0), (0.3, 1.35))
BUMP_SIZES = (0.5, 0.62, 0.74, 0.85)
CROWN_AT = (0.45, 0.6)
NEAR_DOME = 1.0
SHOULDER_STEP = (0.7, 1.15)
SHOULDER_LEAST = 0.35
MOUND_BASE = 0.28                # radius, in bush heights, of the row of leaves along a near bush's foot
MOUND_BODY_INSET = (0.04, -0.2, 0.82)
MOUND_LIT_FROM = 0.0
CREASE = 0.75                    # a dark crease between overlapping lobes, as a share of the outline's width
MOUND_LIT_INSET = (0.05, -0.32, 0.8)
# The yellow-green highlight on the bumps from MOUND_HIGHLIGHT_FROM of the way across that rise above
# MOUND_HIGHLIGHT_RISE of the bush's height, moved to their upper right by MOUND_HIGHLIGHT_INSET; and each bush's
# colours mixed toward NEAR_LIGHT by NEAR_LIGHTEN times how much smaller it is than the biggest.
MOUND_HIGHLIGHT_FROM = 0.45
MOUND_HIGHLIGHT_RISE = 0.8
MOUND_HIGHLIGHT_INSET = (0.2, -0.6, 0.5)
NEAR_LIGHT = '#8ad45a'
NEAR_LIGHTEN = 0.35


# The straight, level railway seen edge on: the rails' top at RAIL_TOP the whole width. From the rail top down: one
# thin dark line, the thicker blue-grey band of the metal under it, then one row of boards, their lit ends an on-off
# dash pattern on the dark between them, then the ground.
RAIL_TOP = 517
RAIL = [('rail top', 0, 2, '#355c72'), ('rail head', 2, 5, '#7079a0')]
SLEEPERS = (5, 8, 5, 13, '#5c768f', '#a2d67a')   # (top, bottom below the rail top, a board's width, pitch, the dark between the boards, a board's lit end)
BALLAST = ('#86a85c', '#7a9a52')
TRACK_GROUND = ([(-40, 500), (300, 498), (800, 500), (1200, 497), (1576, 500)], '#a9ec68', '#8fe25c')   # behind the rails
TRACK_SHADOW = (1, '#6cbf6f')    # (px, colour) of the shadow band the track throws on the ground in front
TRACK_FOOT = 556                 # the ground in front of the rails reaches down to here
TRACK_FOOT_COLOURS = ('#a6e85a', '#92d85e')


# The meadow bands the bushes stand on, part of the track's image so the bushes can stand on them: (top edge, colour
# at its top, colour where the next band rises).
TRACK_MEADOW = [
    ([(-40, 552), (200, 548), (500, 546), (800, 550), (1100, 547), (1400, 550), (1576, 552)], '#a8e070', '#86d06a'),
]



# Swathes slanting across the meadow behind the bushes, in the open meadow's planes' terms: (band index, x0, x1, drop
# at x0, drop at x1, depth, colour), lit sweeps and shaded hollows running down to the left as rolls of the ground,
# either side of the menu's strip, which stays plain.
TRACK_MEADOW_PLANES = [
    (0, -40, 460, 4, 30, 30, '#c8f064'), (0, 200, 680, 30, 8, 24, '#7ed060'), (0, 380, 700, 40, 14, 14, '#c8f064'),
    (0, 840, 1240, 6, 34, 28, '#c8f064'), (0, 1000, 1440, 36, 12, 22, '#7ed060'), (0, 1300, 1576, 30, 2, 20, '#c8f064'),
]


# Tufts of grass and drifts of small flowers scattered over the meadow bands, so they are not one flat green: for
# each band list, per band, (tufts, drifts) counts, and the tuft and drift sizes in px. The menu buttons sit over the
# middle of the meadow, so between MEADOW_CALM's x the scatter thins to its share.
MEADOW_TUFTS = {'track': [(90, 12)], 'meadow': [(70, 10), (44, 5), (30, 0)]}
TUFT = (6, 10, '#6cb852', '#78bc4a')      # (min height, max height, colour behind the bushes, colour in the open meadow)
DRIFT = (8, 14, 2.2, 3.2, 20)              # (min dots, max dots, min dot radius, max dot radius, spread in px)
DRIFT_COLOURS = ('#f6a8da', '#fff8fc', '#f6a8da')   # pink and white drifts, pink twice as often
MEADOW_CALM = (680, 860, 0.3)            # (x0, x1, share of the scatter kept) under the menu buttons
SCATTER_INSET = (6, 8)                   # px kept clear under a band's top fringe and above the next band's crest


# The open meadow in front, its few wide bands back to front, each a rolling slope rising to the right: (top edge,
# colour at its top, colour where the next band rises), brightest near the track and darker toward the front. Each
# band's top edge is a fringe of tall grass tufts over the band behind, and lighter and darker planes slant across it
# as the ground's hollows and lit slopes.
MEADOW = [
    ([(-40, 644), (400, 626), (800, 606), (1200, 596), (1576, 590)], '#b0e458', '#8cd058'),
    ([(-40, 690), (500, 714), (1000, 740), (1576, 762)], '#9bd84a', '#84c852'),
    ([(-40, 904), (600, 870), (1100, 840), (1576, 820)], '#8ccb52', '#66b060'),
]


# Planes slanting across the meadow bands: (band index, x0, x1, drop at x0, drop at x1, depth, colour): the shaded
# hollows curving across the far bands, the lit slopes on the near ones.
MEADOW_PLANES = [
    (0, 560, 1576, 40, 4, 30, '#c6ec5a'), (0, 100, 600, 14, 46, 24, '#7bb255'),
    (1, 500, 1300, 36, 70, 40, '#8ad048'), (1, 1000, 1576, 70, 20, 40, '#b0dc52'), (1, -40, 500, 50, 90, 36, '#b0dc52'),
    (2, 100, 900, 40, 90, 60, '#9ad257'), (2, 800, 1576, 100, 30, 56, '#5fa84e'),
]

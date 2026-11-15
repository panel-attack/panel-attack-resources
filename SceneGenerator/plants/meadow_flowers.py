#   Writes SVG, run by `python3 -m scene_export render`: plants/meadow_flowers.svg, the train meadow's big foreground
#   flowers (the pink five-petal flower, white daisies, yellow buttercups, violet and lilac pansies, lilac lupin spikes)
#   and its mossy grey rocks, each standing on its foot.
#
#   python3 -m plants.meadow_flowers  ->  meadow_flowers.svg
#
#   The flowers are the broad five-petal kind of TrainMeadow/source.png, five petals round a coloured centre, each
#   petal turned toward the light from the upper right paler and the ones turned away deeper, a shaded band along each
#   petal's edge away from the light fading out under its outline, on a green stem with broad teal leaves growing from
#   its foot, one of them in front of it. A lupin is a spike of paired
#   florets shrinking up the stem to one bud. A rock is a grey block whose top and right are lit, capped with moss that
#   drapes over its front edge. Everything is outlined the Esme terrace's way (plants/foliage.py): a thin line, Esme's
#   STROKE at most where the template stands largest in the scene, in a dark shade of the shape's own colour, the pink
#   petals in Esme's petal outline and the white ones in its white outline. Every flower comes in a near and a mid
#   size, the mid one drawn smaller with its lines widened for the smaller scale it stands at, so it keeps its outline
#   when the scene places it further back. Ids start with `flower-` so the scene's wind sways them about their foot;
#   the rocks' start with `rock-`. Below the templates the sheet stands a copy of each on its place in the reference
#   (meadow_flowers_reference.py), for comparing; those placements are not parts.

import colorsys
import math
import os
import random

from common.painting import Svg, hexrgb, mix, poly
from plants import foliage
from plants import meadow_flowers_reference as reference
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))

LIGHT = -math.pi / 4            # the light comes from the upper right: this is the direction toward it (y down)
SQUASH = 0.82                   # the squash of a head's centre, facing the viewer tipped back a little
# how a head is seen, all in degrees: (the turn of its petals, the screen direction the head is turned toward, 0 right
# and 90 down, how far it is turned from facing the viewer, how steeply the petals rise out of the head's plane). A
# turned head projects shorter along that direction, and its rising petals foreshorten on the side it is turned toward
# and lengthen on the other, so its centre sits off toward that side and the stem meets it there, as in the reference.
FLAT = (-8, 90, 35, 0)                                  # facing the viewer, tipped back a little: the mid flowers
UP = (172, -90, 40, 18)                                 # turned up at the sky, seen from low in the grass, a petal
                                                        # hanging down on the far side
FACES = {
    'flower-pink-corner': (-4, -10, 20, 40),            # turned right, in toward the middle of the scene, its petals
                                                        # rising steeply so the far ones reach well past the near; one
                                                        # petal points down the leaning stem, covering it
    'flower-pink-near': (-20, -110, 44, 24),
    'flower-daisy-near': UP,
    'flower-buttercup-near': (172, -100, 40, 18),
    'flower-violet-near': (172, -80, 38, 16),
    'flower-lilac-near': UP,
}
PETAL_TONE = 0.2                # a petal facing the light is this far toward the light colour, one facing away
                                # this far toward the shade colour
SHADE_BAND = 0.42               # the shaded band along a petal's edge away from the light, share of its half width
BAND_FADE = 0.4                 # the band fades out round the petal's tip where the tip has narrowed to this share of
                                # the petal's width, short of its notch, and in from its base where it is this narrow
BAND_FOOT = 0.2
OUTLINE_VALUE = 0.7             # an outline keeps its shape's hue at this share of its HSV value, as Esme's petal
                                # outline is to its petals and its leaf outline to its leaves
OUTLINE_SATURATION = 0.5        # and is at least this saturated
MID_STROKE = 2.0                # a mid flower stands back in the meadow, so its lines are this wide there, between
                                # Esme's foreground STROKE and the lines of its distant town
THIN = 0.5                      # a vein, midrib or shine is this share of the outline's width
CENTRE_LINE = 2 / 3             # a flower's centre is outlined this share of the petals' width, as Esme's are

PLUM = '#8a2a5e'                # the pink flower's outline, the dark plum of TrainMeadow/source.png's, as dark as
                                # Esme's rule of outlining a shape in its own hue allows
PINK_LINE = '#c83880'           # its veins and creases, the deeper pink of the source's
FACET = 0.4                     # the band along a petal's lit edge is this far from its tone toward the light colour
VEINS = ((-0.12, 0.58), (0.02, 0.7), (0.14, 0.55))
HEART = 0.45                    # the pink flower's petals are fused into a tube this share of the radius wide at the
                                # centre, so no gap between their narrow bases shows the stem behind    # (sideways lean, reach) of each vein, shares of the petal's
                                # length, so three veins fan out from the centre most of the way to the edge

# petal colours: body, light, shade, outline (None for a dark shade of the body), vein (or None), centre kind
PALETTES = {
    'pink': ('#fd7eb3', '#ffa0cc', '#f8409e', PLUM, PINK_LINE, 'cup'),
    'daisy': ('#fbeedd', '#fffbf4', '#e2d0c8', foliage.WHITE_OUTLINE, None, 'disc'),
    'buttercup': ('#fdd01a', '#ffe768', '#f0aa12', None, None, 'star'),
    'violet': ('#b476fc', '#c894ff', '#9a60ea', None, None, 'cross'),
    'lilac': ('#cdb0e6', '#e4d0f6', '#a888d0', None, None, 'disc'),
}
MOUTH = 0.5                     # its open mouth is this share of the rim's radius
TRUMPET = 1.0                   # the trumpet stands out of the head this many times its rim's radius
CUP_OUTLINE = '#cf7c0a'         # the trumpet's yellow cup is rimmed in orange, not the olive of a dark yellow
CENTRES = {     # fill, shade, shine
    'cup': ('#fcdc25', '#fe9f00', '#fff0a0'),
    'star': ('#f8b310', '#e88a0c', '#fff09a'),
    'disc': ('#ffc918', '#f0a010', '#fff09a'),
    'cross': ('#fdd828', '#f6bc20', '#fff3a0'),
}
STEM = '#4ea847'
STEM_OUTLINE = foliage.LEAF_OUTLINE
LEAF = ('#1fa888', '#62c24e', '#0f7a6a')     # body, lit half, shaded half
LUPIN_ROWS = 6
LUPIN = ('#f6acee', '#fde0f8', '#c262e2')               # tip colour, light, foot colour

ROCK_STONE = {'lit': '#c4a8b0', 'top': '#a8929f', 'mid': '#968ba3', 'grey': '#7d7ba3', 'shade': '#56639a',
              'deep': '#45518a'}
ROCK_MOSS = ('#c8df40', '#eee83c', '#8cc23a')                       # body, lit, the shade along its lip

# a flower's own leaves, broad blades round its foot hiding the lower stem: (height up the stem, angle in degrees from
# upright, length, width share, whether it stands in front of the stem), heights and lengths as shares of the stem's
# length; every leaf grows from a point on the stem, and one of them stands in front of it
CLUMP = [(0.02, -58, 1.0, 0.68, False), (0.04, 54, 1.06, 0.66, False), (0.03, -20, 0.8, 0.6, False),
         (0.1, 38, 0.56, 0.56, True)]
MID_CLUMP = [(0.02, -40, 0.6, 0.4, False), (0.1, 40, 0.5, 0.4, True)]
CORNER_CLUMP = [(0.02, -70, 0.8, 0.62, False), (0.06, 60, 0.7, 0.56, False), (0.04, 25, 0.9, 0.62, False),
                (0.03, -30, 0.85, 0.6, False), (0.2, -56, 0.55, 0.56, True)]
SPIKE_CLUMP = [(0.02, -40, 0.6, 0.4, False), (0.04, 34, 0.64, 0.4, False), (0.03, -12, 0.5, 0.36, False),
               (0.1, 30, 0.4, 0.36, True)]

# each rock's shape in shares of its width (x, from its foot's centre) and height (up): its silhouette from the left
# foot round to the right foot, its facets (tone, points) painted in order, the moss's top edge from left to right, its
# lip hanging back from the last point through the lip points to the first, dripping by drip of the height, and the
# sunlit patch of moss
ROCKS = {
    'ridge': {
        'silhouette': [(-0.5, 0), (-0.42, 0.56), (-0.3, 0.82), (-0.04, 1.0), (0.36, 0.86), (0.5, 0.6), (0.5, 0)],
        'facets': [('mid', [(-0.5, 0), (-0.42, 0.56), (-0.3, 0.82), (-0.18, 0.66), (-0.24, 0.3), (-0.3, 0)]),
                   ('lit', [(-0.3, 0.82), (-0.04, 1.0), (0.08, 0.84), (-0.18, 0.66)]),
                   ('top', [(-0.18, 0.66), (0.08, 0.84), (0.04, 0.5), (-0.24, 0.3)]),
                   ('grey', [(-0.3, 0), (-0.24, 0.3), (0.04, 0.5), (0.0, 0)])],
        'moss': [(-0.14, 0.95), (-0.04, 1.0), (0.36, 0.86), (0.5, 0.6), (0.5, 0.42)],
        'lip': [(0.34, 0.46), (0.16, 0.56), (-0.02, 0.66), (-0.12, 0.84)],
        'drip': 0.12,
        'moss lit': [(0.0, 0.97), (0.34, 0.85), (0.4, 0.74)],
    },
    'knob': {
        'silhouette': [(-0.5, 0), (-0.42, 0.62), (-0.22, 0.9), (0.18, 1.0), (0.46, 0.8), (0.5, 0)],
        'facets': [('lit', [(-0.5, 0), (-0.42, 0.62), (-0.22, 0.9), (-0.18, 0.5), (-0.26, 0)]),
                   ('grey', [(-0.26, 0), (-0.18, 0.5), (0.1, 0.56), (0.12, 0)])],
        'moss': [(-0.42, 0.62), (-0.22, 0.9), (0.18, 1.0), (0.46, 0.8), (0.5, 0.5)],
        'lip': [(0.1, 0.58)],
        'drip': 0.12,
        'moss lit': [(0.0, 0.95), (0.4, 0.82), (0.42, 0.7)],
    },
    'boulder': {
        'silhouette': [(-0.5, 0), (-0.5, 0.4), (-0.47, 0.64), (-0.4, 0.84), (-0.3, 0.96), (-0.18, 1.0), (-0.04, 0.98),
                       (0.1, 0.93), (0.22, 0.86), (0.32, 0.76), (0.4, 0.62), (0.45, 0.46), (0.48, 0.28), (0.5, 0.12),
                       (0.5, 0)],
        'facets': [('grey', [(-0.2, 0), (-0.24, 0.4), (-0.2, 0.72), (0.04, 0.7), (0.12, 0.4), (0.08, 0)]),
                   ('top', [(0.08, 0), (0.12, 0.4), (0.04, 0.7), (0.22, 0.86), (0.32, 0.76), (0.4, 0.62), (0.45, 0.46),
                            (0.48, 0.28), (0.5, 0.12), (0.5, 0)]),
                   ('lit', [(0.3, 0), (0.32, 0.36), (0.26, 0.72), (0.32, 0.76), (0.4, 0.62), (0.45, 0.46), (0.48, 0.28),
                            (0.5, 0.12), (0.5, 0)]),
                   ('shade', [(0.08, 0), (0.12, 0.4), (0.04, 0.7), (0.08, 0.7), (0.15, 0.4), (0.12, 0)]),
                   ('deep', [(-0.2, 0), (-0.24, 0.4), (-0.2, 0.72), (-0.17, 0.7), (-0.2, 0.4), (-0.17, 0)])],
        'moss': [(-0.47, 0.64), (-0.4, 0.84), (-0.3, 0.96), (-0.18, 1.0), (-0.04, 0.98), (0.1, 0.93), (0.22, 0.86),
                 (0.32, 0.76), (0.37, 0.67)],
        'lip': [(0.26, 0.56), (0.1, 0.6), (-0.04, 0.52), (-0.2, 0.6), (-0.36, 0.54)],
        'drip': 0.14,
        'moss lit': [(-0.3, 0.95), (0.2, 0.85), (0.26, 0.77)],
    },
}

# (id, kind, args): every template, in the order they were added, so a new one leaves the earlier ones unchanged.
# flower: (palette, petal radius, petal shape (half width, tip notch, shoulder, tip squareness, and optionally the
#   wave of the tip's edge, the flare of its sides, the width they bulge to halfway to the shoulder, and the width of
#   its base) as shares of the radius, stem length, leaves, and optionally the stem's lean in degrees right of upright);
#   lupin: (spike height, floret size, stem length, leaves);
# rock: (shape in ROCKS, width, height, seed)
# the pink flower's petals: fans from a narrow base to broad squarish lobes with rounded corners, half the radius wide
# either side, lying over their neighbours along their sides so only the seams show and parting in a deep notch
# between the lobes, each lobe with a shallow notch and a wavy edge
PINK_SHAPE = (0.5, 0.06, 0.5, 0.7, 0.05, 0.75, 0.3)
TEMPLATES = [
    ('flower-pink-near', 'flower', ('pink', 70, PINK_SHAPE, 150, CLUMP)),
    ('flower-pink-mid', 'flower', ('pink', 44, PINK_SHAPE, 92, MID_CLUMP)),
    ('flower-daisy-near', 'flower', ('daisy', 34, (0.42, 0.0, 0.58, 1.0), 96, CLUMP)),
    ('flower-daisy-mid', 'flower', ('daisy', 22, (0.42, 0.0, 0.58, 1.0), 62, MID_CLUMP)),
    ('flower-buttercup-near', 'flower', ('buttercup', 36, (0.45, 0.1, 0.62, 0.8), 100, CLUMP)),
    ('flower-buttercup-mid', 'flower', ('buttercup', 23, (0.45, 0.1, 0.62, 0.8), 64, MID_CLUMP)),
    ('flower-violet-near', 'flower', ('violet', 50, (0.42, 0.06, 0.62, 0.8), 120, CLUMP)),
    ('flower-violet-mid', 'flower', ('violet', 32, (0.42, 0.06, 0.62, 0.8), 76, MID_CLUMP)),
    ('flower-lilac-near', 'flower', ('lilac', 46, (0.42, 0.06, 0.62, 0.8), 116, CLUMP)),
    ('flower-lilac-mid', 'flower', ('lilac', 30, (0.42, 0.06, 0.62, 0.8), 74, MID_CLUMP)),
    ('flower-lupin-near', 'lupin', (170, 42, 250, SPIKE_CLUMP)),
    ('flower-lupin-mid', 'lupin', (110, 28, 160, SPIKE_CLUMP)),
    ('rock-wide', 'rock', ('ridge', 290, 112, 3)),
    ('rock-small', 'rock', ('knob', 116, 70, 5)),
    ('rock-tall', 'rock', ('boulder', 224, 100, 8)),
    ('flower-pink-corner', 'flower', ('pink', 70, PINK_SHAPE, 140, CORNER_CLUMP, 36)),
]


def rotate(p, a):
    c, s = math.cos(a), math.sin(a)
    return p[0] * c - p[1] * s, p[0] * s + p[1] * c


def bezier(p0, p1, p2, n=6):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(1, n + 1)]]


def ellipse(c, rx, ry, a=0.0, n=16):
    return [(c[0] + x, c[1] + y) for x, y in
            (rotate((rx * math.cos(2 * math.pi * i / n), ry * math.sin(2 * math.pi * i / n)), a) for i in range(n))]


def shade_of(fill):
    """The outline colour Esme would give a shape of colour fill: its own hue, OUTLINE_VALUE as bright."""
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in hexrgb(fill)))
    return '#%02x%02x%02x' % tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, max(s, OUTLINE_SATURATION), v * OUTLINE_VALUE))


def placement_scale(tid):
    """The largest scale the scene stands the template at, from its places in the reference; 1 for one it never
    places, which stands as drawn."""
    scales = [stand(t, at, size)[1] for t, at, size in reference.FLOWERS if t == tid]
    scales += [width / template_args(t)[1] for t, _, width in reference.ROCKS if t == tid]
    return max(scales, default=1.0)


def line_width(tid, stroke=foliage.STROKE):
    """The width to draw a line on the sheet so it is stroke px wide where the template stands largest, a mid
    flower's MID_STROKE for the distance it stands at (a leaf's stroke thinned in the same proportion)."""
    if tid.endswith('-mid'):
        stroke *= MID_STROKE / foliage.STROKE
    return stroke / placement_scale(tid)


# ---------------------------------------------------------------- flower heads

def petal_local(length, half_width, notch, shoulder, square, jitter, wave=0.0, flare=0.86, base=0.18):
    """One petal in its own frame, growing along +u from the head's centre: a wedge from a narrow base (base of the
    half width), its sides bulging out to flare of the half width by the way to the shoulder (hollowed in when flare
    is small), to a broad squarish tip with rounded corners and a shallow notch, so neighbouring petals part in a V;
    the tip's edge undulates by wave of the length either side of its notch. Returns (left side, tip, right side) as
    lists of (u, v)."""
    r0, b = length * 0.1, half_width * base
    w = half_width * (1 + jitter[0])
    shoulder = length * shoulder
    left = [(r0, -b)] + bezier((r0, -b), (shoulder * 0.6, -w * flare), (shoulder, -w), 6)
    tip = []
    for i in range(1, 16):
        t = -math.pi / 2 + math.pi * i / 16
        c = math.cos(t) ** square
        u = shoulder + (length * (1 + jitter[1]) - shoulder) * c - notch * length * math.exp(-(t / 0.3) ** 2)
        u -= wave * length * (1 - math.cos(4 * t)) / 2 * math.cos(t) ** 0.5
        tip.append((u, w * math.sin(t)))
    right = [(shoulder, w)] + bezier((shoulder, w), (shoulder * 0.6, w * flare), (r0, b), 6)
    return left, tip, right


def placed(points, centre, angle, face=FLAT):
    """Petal points (u, v), u out along a petal growing at angle from the head's centre, as they show on a head seen
    as face says: the petal rises out of the head's plane, the head turns away from the viewer toward the screen
    direction, and the result is projected flat."""
    tan_r = math.tan(math.radians(face[3]))
    return lifted([rotate((u, v), angle) + (u * tan_r,) for u, v in points], centre, face)


def lifted(points, centre, face):
    """Points (x, y, h) of a head seen as face says, (x, y) in the head's plane and h out of it toward the viewer, as
    they show projected flat: the plane foreshortened along the direction the head is turned toward, and a point
    standing out of it shifted the other way."""
    toward, tilt = (math.radians(d) for d in face[1:3])
    nx, ny = math.cos(toward), math.sin(toward)
    cos_t, sin_t = math.cos(tilt), math.sin(tilt)
    out = []
    for x, y, h in points:
        s, t = x * nx + y * ny, y * nx - x * ny
        s = s * cos_t - h * sin_t
        out.append((centre[0] + s * nx - t * ny, centre[1] + s * ny + t * nx))
    return out


def petal_tone(palette, angle):
    body, light, shade = PALETTES[palette][:3]
    t = math.cos(angle - LIGHT)
    return mix(body, light, PETAL_TONE * t) if t > 0 else mix(body, shade, -PETAL_TONE * t)


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def shade_band(left, tip, right, half_width, away):
    """The shaded band along a petal's edge on the side away from the light (away +1 for the right side, -1 for the
    left), in the petal's frame: it follows the edge from the petal's base up its side and round the tip's corner,
    its inner edge set in from the edge by SHADE_BAND of the half width where the petal is at its widest, tapering
    smoothly into the edge toward the base and before the tip's notch, so it fades out instead of ending in a step."""
    corner = [p for p in (tip if away > 0 else tip[::-1]) if p[1] * away > BAND_FADE * half_width]
    side = right if away > 0 else left[::-1]
    outer = corner + side
    inner = []
    for i, (u, v) in enumerate(outer):
        foot = BAND_FADE if i < len(corner) else BAND_FOOT
        depth = SHADE_BAND * half_width * smoothstep((abs(v) / half_width - foot) / (1 - foot))
        inner.append((u, v - away * depth))
    return outer + inner[::-1]


def vein_sliver(length, lean, reach, width):
    """One tapering vein in the petal's frame, a sliver width wide at its foot near the centre narrowing to nothing
    at reach of the length, bowing sideways by lean."""
    spine = [(length * 0.16, 0.0)] + bezier((length * 0.16, 0.0), (length * reach * 0.55, lean * length * 0.55),
                                            (length * reach, lean * length), 8)
    out = []
    for i, (u, v) in enumerate(spine):
        half = width / 2 * (1 - i / len(spine)) ** 0.7
        out.append((u, v - half))
    return out + [spine[-1]] + [(u, v + width / 2 * (1 - i / len(spine)) ** 0.7) for i, (u, v) in enumerate(spine)][::-1]


def head(svg, name, palette, centre, radius, shape, face, seed, width):
    """Five petals round the centre, each outlined width wide in a dark shade of its colour, with its shaded band on
    the side away from the light under the outline, the pink flower's lighter band along its edge toward the light
    and its three veins fanning out from the centre; the head seen as face says, the petals on its far side drawn
    first and the near ones over them."""
    body, light, shade, outline, vein, kind = PALETTES[palette]
    outline = outline or shade_of(body)
    rnd = random.Random(seed)
    turn, toward = math.radians(face[0]), math.radians(face[1])
    squash = math.cos(math.radians(face[2]))
    petals = []
    for i in range(5):
        a = turn - math.pi / 2 + 2 * math.pi * i / 5 + rnd.uniform(-0.08, 0.08)
        length = radius * rnd.uniform(0.94, 1.04)
        jitter = (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.03, 0.03))
        petals.append((a, length, radius * shape[0] * (1 + jitter[0]),
                       petal_local(length, radius * shape[0], shape[1], shape[2], shape[3], jitter, *shape[4:])))
    order = sorted(petals, key=lambda p: math.cos(p[0] - toward))
    if vein:
        svg.path(poly(placed(ellipse((0, 0), radius * HEART, radius * HEART), centre, 0, face)), body, name=name + ' heart')
    for i, (a, length, half_width, (l, t, r)) in enumerate(order):
        pname = '%s petal %d' % (name, i + 1)
        edge = poly(placed(l + t + r, centre, a, face))
        tone = petal_tone(palette, a)
        svg.path(edge, tone, *(() if vein else (outline, width)), name=pname)
        away = 1 if math.sin(LIGHT - a) < 0 else -1      # the side of the petal turned from the light
        if vein:
            svg.path(poly(placed(shade_band(l, t, r, half_width, -away), centre, a, face)), mix(tone, light, FACET),
                     name=pname + ' lit')
        svg.path(poly(placed(shade_band(l, t, r, half_width, away), centre, a, face)), mix(tone, shade, 0.45),
                 name=pname + ' shade')
        if vein:
            lines = [poly(placed(vein_shape, centre, a, face)) for vein_shape in
                     (vein_sliver(length, lean, reach, width * 3.0) for lean, reach in VEINS)]
            svg.path(' '.join(lines), vein, name=pname + ' veins')
        svg.path(edge, 'none', outline, width, name=pname + ' outline')
    flower_centre(svg, name, kind, centre, radius, width * CENTRE_LINE, squash, face)


def lobed(c, rr, lobes, squash=SQUASH, turn=0.0, n=60):
    """A closed outline round c whose radius at angle t is rr * lobes(t)."""
    return [(c[0] + rr * lobes(t) * math.cos(t + turn), c[1] + squash * rr * lobes(t) * math.sin(t + turn))
            for t in [2 * math.pi * i / n for i in range(n)]]


def flower_centre(svg, name, kind, c, radius, width, squash=SQUASH, face=FLAT):
    """The middle of the flower: the pink flower's yellow trumpet, a cup with a scalloped rim on an orange throat
    growing out of where the petals meet, seen as face says, a violet's yellow cross, a buttercup's deep orange star
    round its eye, or a daisy's disc, squashed as the head is turned, each outlined width wide in a dark shade of its
    own yellow."""
    fill, shade, shine = CENTRES[kind]
    rr = radius * (0.18 if kind == 'cup' else 0.3)
    if kind == 'cup':
        foot, height = rr * 0.35, rr * TRUMPET
        cup = lifted([(0, 0, height)], c, face)[0]
        svg.path(poly(lifted([(foot * 1.4 * math.cos(t), foot * 1.4 * math.sin(t), 0) for t in
                              (2 * math.pi * i / 16 for i in range(16))], c, face)),
                 mix(shade, '#c02040', 0.5), name=name + ' throat shadow')
        # the throat's sides run from the rim's edges across the direction the head is turned to its foot's
        toward = math.radians(face[1])
        across = toward + math.pi / 2
        base = [(foot * math.cos(across + t), foot * math.sin(across + t), 0) for t in
                (math.pi * i / 8 for i in range(9))]
        mouth = [(rr * math.cos(across + math.pi + t), rr * math.sin(across + math.pi + t), height) for t in
                 (math.pi * i / 8 for i in range(9))]
        svg.path(poly(lifted(base + mouth, c, face)), shade, shade_of(shade), width, name=name + ' throat')
        angles = [2 * math.pi * i / 80 for i in range(80)]
        rim = lifted([(rr * k * math.cos(t), rr * k * math.sin(t), height) for t, k in
                      ((t, 1 + 0.08 * (1 - math.cos(6 * t))) for t in angles)], c, face)
        svg.path(poly(rim), fill, CUP_OUTLINE, width, name=name + ' centre')
        body = [p for p in rim if math.cos(math.atan2(p[1] - cup[1], p[0] - cup[0]) - LIGHT) < -0.3]
        svg.path(poly(body + [(cup[0] + (x - cup[0]) * 0.3, cup[1] + (y - cup[1]) * 0.3) for x, y in body[::-1]]),
                 mix(fill, shade, 0.8), name=name + ' centre shade')
        # the trumpet's open mouth, deep orange down its throat
        svg.path(poly(lifted([(rr * MOUTH * math.cos(t), rr * MOUTH * math.sin(t), height) for t in angles[::4]], c,
                             face)), shade, name=name + ' centre mouth')
    elif kind == 'cross':
        arms = lobed(c, rr * 0.9, lambda t: 0.42 + 0.58 * abs(math.cos(2 * t)) ** 2, 0.95, 0.12)
        svg.path(poly(arms), fill, shade_of(fill), width, name=name + ' centre')
        svg.path(poly(ellipse(c, rr * 0.22, rr * 0.2)), shade, name=name + ' centre eye')
    elif kind == 'star':
        arms = lobed(c, rr * 0.9, lambda t: 0.62 + 0.38 * abs(math.cos(2.5 * t)) ** 2, squash, -math.pi / 2)
        svg.path(poly(arms), shade, shade_of(shade), width, name=name + ' centre')
        svg.path(poly(ellipse(c, rr * 0.42, rr * 0.38 * squash, n=18)), fill, name=name + ' centre eye')
    else:
        svg.path(poly(ellipse(c, rr, rr * squash, n=20)), fill, shade_of(fill), width, name=name + ' centre')
        svg.path(poly(ellipse((c[0] - rr * 0.18, c[1] + rr * 0.2), rr * 0.7, rr * 0.55 * squash, LIGHT, 18)), shade,
                 name=name + ' centre shade')
        svg.path(poly(ellipse(c, rr * 0.62, rr * 0.5 * squash, n=18)), fill, name=name + ' centre face')


# ---------------------------------------------------------------- stems and leaves

def stem_points(length, bow, n=10):
    return [(bow * length * math.sin(math.pi * i / n), -length * i / n) for i in range(n + 1)]


def stem_top(length, lean, bow=0.03):
    return rotate(stem_points(length, bow)[-1], lean)


def ribbon(pts, width):
    """The outline of a band width wide along the open polyline pts, pointed at both ends: it starts at the first
    point, runs up one side to the last point and back down the other."""
    sides = ([], [])
    for i, (x, y) in enumerate(pts):
        (ax, ay), (bx, by) = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        d = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / d * width / 2, (bx - ax) / d * width / 2
        sides[0].append((x + nx, y + ny))
        sides[1].append((x - nx, y - ny))
    return [pts[0]] + sides[0][1:-1] + [pts[-1]] + sides[1][-2:0:-1]


def stem(svg, name, length, width, line, bow=0.03, lean=0.0):
    """A green stem width wide from the foot (0, 0) up, leaning lean radians right of upright and bowing sideways a
    little, outlined line wide in the leaf outline green; returns the point it ends at."""
    pts = [rotate(p, lean) for p in stem_points(length, bow)]
    svg.path(poly(ribbon(pts, width)), STEM, STEM_OUTLINE, line, name=name + ' stem')
    svg.stroke(poly([(x + width * 0.22, y) for x, y in pts[1:-1]], close=False), mix(STEM, '#b8f070', 0.4),
               line * THIN, name=name + ' stem shine')
    return pts[-1]


def leaf(svg, name, base, angle, length, share, line):
    """A broad pointed teal leaf growing from base, angle (radians) off upright, arching over a little, outlined line
    wide in a dark shade of its teal: its half turned toward the light paler, a midrib down the middle."""
    w = length * share / 2
    sign = 1 if angle >= 0 else -1
    tip = (length, sign * length * 0.12)          # leans down at its tip on the outer side
    mid = (length * 0.5, sign * length * 0.06)

    def frame(pts):
        out = []
        for u, v in pts:
            x, y = rotate((u, v), angle - math.pi / 2)
            out.append((base[0] + x, base[1] + y))
        return out
    upper = bezier((0, 0), (length * 0.42, -w * 1.6), tip, 10)
    lower = bezier(tip, (length * 0.48, w * 1.45), (0, 0), 10)
    rib = bezier((0, 0), (length * 0.5, sign * length * 0.04), (length * 0.9, sign * length * 0.1), 8)
    lit_side = upper if (angle >= 0) else lower[::-1]
    shade_side = lower[::-1] if (angle >= 0) else upper
    svg.path(poly(frame(upper + lower)), LEAF[0], shade_of(LEAF[0]), line, name=name)
    svg.path(poly(frame([(0, 0)] + shade_side + rib[::-1])), LEAF[2], name=name + ' shade')
    svg.path(poly(frame([(0, 0)] + lit_side + rib[::-1])), LEAF[1], name=name + ' lit')
    svg.path(poly(frame([(0, 0)] + shade_side[:4] + [mid])), mix(LEAF[2], LEAF[0], 0.3), name=name + ' base')
    svg.stroke(poly(frame([(0, 0)] + rib), close=False), shade_of(LEAF[0]), line * THIN, name=name + ' midrib')


def stem_point(length, up, lean=0.0, bow=0.03):
    """The point up (a share of the stem's length) up a stem of that length, leaning lean radians, bowing bow."""
    pts = stem_points(length, bow)
    k = min(len(pts) - 2, int(up * (len(pts) - 1)))
    t = up * (len(pts) - 1) - k
    return rotate((pts[k][0] + (pts[k + 1][0] - pts[k][0]) * t, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * t), lean)


def leaves(svg, name, specs, stem_length, line, front, lean=0.0, bow=0.03):
    """The leaves in specs growing from points on the stem leaning lean radians: those behind it (front False) or
    the ones before it."""
    for i, (up, angle, length, share, in_front) in enumerate(specs):
        if in_front == front:
            leaf(svg, '%s leaf %d' % (name, i + 1), stem_point(stem_length, up, lean, bow), math.radians(angle) + lean,
                 length * stem_length, share, line)


def flower(svg, tid, palette, radius, shape, length, leaf_specs, lean=0):
    line, leaf_line, lean = line_width(tid), line_width(tid, foliage.LEAF_STROKE), math.radians(lean)
    leaves(svg, tid, leaf_specs, length, leaf_line, False, lean)
    top = stem(svg, tid, length, radius * 0.09, line, lean=lean)
    leaves(svg, tid, leaf_specs, length, leaf_line, True, lean)
    head(svg, tid + ' head', palette, top, radius, shape, FACES.get(tid, FLAT), tid, line)


# ---------------------------------------------------------------- lupins

def floret(svg, name, c, size, side, line, tone):
    """One lupin floret: a pointed petal leaning up and out from the stem, its upper half paler, its lower deeper,
    tone (0 at the spike's foot, 1 at its tip) taking it from purple-magenta to pink-lilac."""
    body = mix(LUPIN[2], LUPIN[0], tone ** 0.5)
    light, shade = mix(LUPIN[0], LUPIN[1], 0.4 + 0.6 * tone), mix(LUPIN[2], '#9a3ab8', 0.45 - 0.35 * tone)
    a = -math.pi / 2 + side * 1.0

    def frame(pts):
        return [(c[0] + x, c[1] + y) for x, y in (rotate(p, a) for p in pts)]
    outline_pts = [(size * 0.6 * math.cos(t) * (1 + 0.28 * max(0.0, math.cos(t)) ** 6), size * 0.56 * math.sin(t))
                   for t in [2 * math.pi * i / 28 for i in range(28)]]
    svg.path(poly(frame(outline_pts)), body, shade_of(body), line, name=name)
    under = [p for p in outline_pts if p[1] * (side or 1) > 0]
    svg.path(poly(frame(under + [(size * 0.5, (side or 1) * size * 0.06), (-size * 0.4, (side or 1) * size * 0.06)])), shade,
             name=name + ' shade')
    svg.path(poly(frame([(size * (0.1 + 0.55 * i / 8), -(side or 1) * size * 0.2 * math.sin(math.pi * i / 8))
                         for i in range(9)])), light, name=name + ' light')


def lupin(svg, tid, height, size, length, leaf_specs):
    """A lupin: a tapering spike of florets in staggered rows, a pair leaning out on each row and one more in the
    middle behind every other pair so the stem is hidden, shrinking to one small floret pointing up at the tip."""
    line, leaf_line = line_width(tid), line_width(tid, foliage.LEAF_STROKE)
    leaves(svg, tid, leaf_specs, length, leaf_line, False, bow=0.02)
    top = stem(svg, tid, length, size * 0.13, line, bow=0.02)
    leaves(svg, tid, leaf_specs, length, leaf_line, True, bow=0.02)
    rnd = random.Random(tid)
    bottom = top[1] + height
    spike = []
    for k in range(LUPIN_ROWS):
        t = k / (LUPIN_ROWS - 1)
        y = bottom - height * 0.98 * (1 - (1 - t) ** 1.4)
        s = size * (1 - 0.5 * t)
        across = [-1.0, 1.0] if k % 2 == 0 else [0.0, -0.9, 0.9]
        if k == LUPIN_ROWS - 1:
            across = [0.0]
        for off in across:
            c = (top[0] + off * s * 0.52 + rnd.uniform(-1, 1), y + rnd.uniform(-1, 1) - (0.3 * s if off == 0 else 0))
            spike.append((y, abs(off) > 0.1, '%s floret %d' % (tid, len(spike) + 1), c, s, off, t))
    for _, _, name, c, s, off, t in sorted(spike, key=lambda f: (f[0], f[1])):  # top rows first, middles behind
        floret(svg, name, c, s, off, line, t)


# ---------------------------------------------------------------- rocks

def lumpy(a, b, depth, lumps, rnd):
    """Points from a to b along a wavy edge that dips below the straight line between them by up to depth."""
    out = []
    n = lumps * 8
    sizes = [rnd.uniform(0.3, 1.25) for _ in range(lumps)]
    for i in range(1, n + 1):
        t = i / n
        k = min(lumps - 1, int(t * lumps))
        dip = depth * sizes[k] * (0.45 + 0.55 * abs(math.sin(math.pi * t * lumps))) * math.sin(math.pi * t) ** 0.4
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + dip))
    return out


def rock(svg, tid, shape, w, h, seed):
    """A grey stone standing on (0, 0), drawn from its ROCKS shape: its facets, the upturned ones catching the light
    warm and the upright ones under the moss in cool blue shade, then the moss over its top with a ragged lip hanging
    over the front and a deep shadow under the lip; the stone and the moss each outlined in a dark shade of their own
    colour."""
    rnd = random.Random(seed)
    spec = ROCKS[shape]
    line = line_width(tid)

    def at(pts):
        return [(u * w, -v * h) for u, v in pts]
    silhouette = at(spec['silhouette'])
    svg.path(poly(silhouette), ROCK_STONE['shade'], shade_of(ROCK_STONE['shade']), line, name=tid + ' stone')
    for i, (tone, pts) in enumerate(spec['facets']):
        svg.path(poly(at(pts)), ROCK_STONE[tone], name='%s facet %d' % (tid, i + 1))
    top = at(spec['moss'])
    turns = [top[-1]] + at(spec['lip']) + [top[0]]
    lip = []
    for a, b in zip(turns, turns[1:]):
        lip += lumpy(a, b, h * spec['drip'], max(2, round(math.hypot(b[0] - a[0], b[1] - a[1]) / 30)), rnd)
    svg.path(poly(top + [(x, y + h * 0.08) for x, y in lip]), ROCK_STONE['deep'], name=tid + ' moss shadow')
    svg.path(poly(top + lip), ROCK_MOSS[0], shade_of(ROCK_MOSS[0]), line, name=tid + ' moss')
    svg.path(poly(lip + [(x + 1, y - h * 0.05) for x, y in lip[::-1]]), ROCK_MOSS[2], name=tid + ' moss shade')
    lit = at(spec['moss lit'])
    svg.path(poly(lit[:1] + lumpy(lit[0], lit[1], -h * 0.05, 3, rnd) + lit[2:]), ROCK_MOSS[1], name=tid + ' moss lit')


DRAW = {'flower': flower, 'lupin': lupin, 'rock': rock}


def draw(svg, tid):
    """The template tid standing on (0, 0)."""
    _, kind, args = next(t for t in TEMPLATES if t[0] == tid)
    DRAW[kind](svg, tid, *args)


def template_args(tid):
    return next(t for t in TEMPLATES if t[0] == tid)[2]


def stand(tid, at, size):
    """The foot and scale that stand the template so it matches a reference flower: a flower's head centred on at with
    petal radius size, a lupin's spike tip at at with the spike size tall."""
    _, kind, args = next(t for t in TEMPLATES if t[0] == tid)
    if kind == 'flower':
        s = size / args[1]
        top = stem_top(args[3], math.radians(args[5] if len(args) > 5 else 0))
        return (at[0] - top[0] * s, at[1] - top[1] * s), s
    height, floret, length = args[:3]
    s = size / (height + floret * 0.55)
    return (at[0], at[1] + (length + floret * 0.55) * s), s


def preview(svg):
    """A copy of each template stood where its like stands in the reference, scaled to it, in groups for the compare
    specs: the mid flowers back in the meadow first, then the rocks, then each kind of near flower (and every lupin),
    and all of them in one group for the whole foreground."""
    svg.open('reference foreground')
    svg.open('reference mid')
    for tid, at, size in reference.FLOWERS:
        if tid.endswith('-mid') and 'lupin' not in tid:
            foot, s = stand(tid, at, size)
            svg.place('preview ' + tid, tid, foot, (s, s), lambda s_, tid=tid: draw(s_, tid))
    svg.close()
    svg.open('reference rock')
    for tid, foot, width in reference.ROCKS:
        s = width / template_args(tid)[1]
        svg.place('preview ' + tid, tid, foot, (s, s), lambda s_, tid=tid: draw(s_, tid))
    svg.close()
    for kind in ('lupin', 'lilac', 'violet', 'daisy', 'buttercup', 'pink'):
        svg.open('reference ' + kind)
        for tid, at, size in reference.FLOWERS:
            if tid.split('-')[1] == kind and (kind == 'lupin' or not tid.endswith('-mid')):
                foot, s = stand(tid, at, size)
                svg.place('preview ' + tid, tid, foot, (s, s), lambda s_, tid=tid: draw(s_, tid))
        svg.close()
    svg.close()


def main():
    svg = Svg()
    for tid, _, _ in TEMPLATES:
        svg.template(tid, lambda s, tid=tid: draw(s, tid))
    preview(svg)
    svg.write(cutting.sheet_path('plants/meadow_flowers.svg'))


def parts():
    """Each template's image, standing on its foot."""
    root, grads = cutting.load('plants/meadow_flowers.svg')
    return [cutting.foot_part('plants/parts/meadow-flowers/' + g.get('data-template'), list(g), grads,
                              g.get('data-template'))
            for g in root.iter(cutting.NS + 'g') if g.get('data-template') and not g.get('data-at')]


if __name__ == '__main__':
    main()

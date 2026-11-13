#   Writes SVG, run by `python3 -m scene_export render`: plants/wildflowers.svg, the day valley's foreground meadow
#   flowers (tulips, blue five-petal flowers, small lilac and yellow flowers) and grass tufts, each standing on its foot.
#
#   python3 -m plants.wildflowers  ->  wildflowers.svg
#
#   The flowers are drawn with foliage.py's flower and leaf shapes, recoloured, so they keep the terrace daisies' and
#   pink flowers' outline weight, petal shading and size beside them. Ids start with `tulip-`, `flower-` or `grass-` so
#   the scene's wind can tell a swaying flower from a stiff tuft. Below the templates the sheet stands one copy of each
#   on the canvas, for comparing with the reference; those placements are not parts.

import math
import os

from common.painting import Svg, poly
from plants import foliage
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))

FLOWER_SQUASH = 0.94            # the flower faces tilt back a little less than the terrace flowers'
FLOWER_TURN = math.radians(-14)  # the heads turn a little off upright, as the painted ones do
STEM_WIDTH = 2.0                # a stem's green core; its outline is STEM_OUTLINE wider
STEM_OUTLINE = 2.5
SMALL_STEM = (1.4, 1.8)         # (core, outline) of a small flower's stem
TULIP_STEM = (1.6, 2.0)         # (core, outline) of a tulip's stem
SMALL_RADIUS = 14               # flowers below this petal radius get the small stem
STEM_BOW = 0.015                # a stem bows sideways by this share of its length
LEAF_TONE = 'leaf-1'            # the meadow plants' leaves are the deepest of the terrace's greens
LEAF_WIDTH = 0.46               # width / length: a little narrower than a bush leaf
LEAF_STROKE = 2.0
TULIP_LEAF_WIDTH = 0.38         # a tulip's leaves are slim and upright

# petal colours: (gradient top, bottom), outline, throat, petal line, then the centre: (share of the petal radius,
# gradient, outline)
LEMON_CENTRE = (0.17, ('#fffdb8', '#fff06a'), '#d2b232')
PALETTES = {
    'blue': (('#6088fc', '#466cf2'), '#1d3a96', '#3458d0', '#2a4cb8', LEMON_CENTRE),
    'blue-light': (('#4ccaff', '#12aaf6'), '#0a4682', '#1aa0e6', '#1290d4', LEMON_CENTRE),
    'lilac': (('#f0d6fa', '#cda0ee'), '#8a5cc0', '#bf92e4', '#a878d4', (0.26, ('#fff27a', '#f5b52e'), '#d0892a')),
    'yellow': (('#ffffb8', '#f6f478'), '#dccc58', '#f4e862', '#e8da60', (0.5, ('#ffe41c', '#f4cc00'), '#cf9c10')),
}
# tulip colours: (gradient top, bottom), outline, shaded right petal, petal line, highlight
TULIPS = {
    'red': (('#ff5c46', '#f44a32'), '#a82a1c', '#e8402c', '#c8301f', '#ffa868'),
    'yellow': (('#fff68a', '#fbd846'), '#c49018', '#f6cf3e', '#e3b42c', '#fffde8'),
}
TUFT = '#4aae2c'
TUFT_SHADE = '#3a9a24'           # the blades at the back of a tuft

# (id, kind, args): every template, in the order they were added, so a new one leaves the earlier ones unchanged.
# flower: (palette, petal radius, notch, stem length, leaves as (height up the stem, angle in degrees, length))
# tulip: (colours, head width, head height, stem length, leaves); tuft: (blades as (x, lean, height), width)
TEMPLATES = [
    ('tulip-red', 'tulip', ('red', 24, 25, 54, [(10, -122, 25), (18, -60, 25)])),
    ('tulip-yellow', 'tulip', ('yellow', 22, 23, 46, [(8, -60, 22), (12, -122, 23)])),
    ('flower-blue', 'flower', ('blue', 22, 0.55, 48, [(12, -124, 20), (20, -56, 18)])),
    ('flower-blue-light', 'flower', ('blue-light', 24, 0.55, 44, [(10, -56, 20), (18, -124, 17)])),
    ('flower-lilac', 'flower', ('lilac', 10, 0.5, 26, [(6, -58, 11)])),
    ('flower-yellow', 'flower', ('yellow', 9, 0.3, 22, [])),
    ('grass-tuft', 'tuft', ([(-9, -3, 12), (-4.5, -1, 9), (0, 0, 15), (4.5, 1, 8), (9, 3, 11)], 3.0)),
    ('grass-tuft-tall', 'tuft', ([(-10, -4, 17), (-5, -2, 18), (0, 0, 22), (5, 1, 10), (10, 3.5, 14)], 3.0)),
    ('grass-tuft-small', 'tuft', ([(-8, -3, 10), (-4, -1.5, 8), (0, 0, 11), (4, 1.5, 8), (8, 3, 10)], 2.8)),
]
# each flower and tulip again on a short, stiff stem and on a tall one that bows and lets its head nod further over:
# (suffix, stem length share, bow, head turn in degrees)
STEM_VARIANTS = [('short', 0.7, STEM_BOW, -6), ('tall', 1.45, 0.06, -28)]
TEMPLATES += [(tid + '-' + suffix, kind, (*args[:3], round(args[3] * share), args[4], bow, turn))
              for suffix, share, bow, turn in STEM_VARIANTS
              for tid, kind, args in list(TEMPLATES) if kind in ('flower', 'tulip')]
PREVIEW_Y = 300                  # the preview copies stand on this line of the sheet
PREVIEW_GAP = 90


def put(svg, shapes):
    """foliage.py's shapes on the sheet, gradient names turned into the sheet's own gradients."""
    for s in shapes:
        fill = foliage.GRADIENTS.get(s.fill, s.fill)
        line = None if s.stroke == 'none' else s.stroke
        svg.path(s.d, fill, line, s.width, name=s.name)


def recoloured(shapes, palette):
    """The pink flower's shapes in the palette's colours."""
    grad, outline, throat, line, _ = PALETTES[palette]
    swap = {'petal': grad, foliage.PETAL_OUTLINE: outline, foliage.PETAL_THROAT: throat, foliage.PETAL_LINE: line}
    for s in shapes:
        s.fill = swap.get(s.fill, s.fill)
        s.stroke = swap.get(s.stroke, s.stroke)
    return [s for s in shapes if not s.name.endswith((' centre', ' centre shine'))]


def centre(name, c, radius, palette):
    """The flower's own centre, sized and coloured for it rather than the pink flower's: a disc with a shine."""
    share, grad, outline = PALETTES[palette][4]
    cr = radius * share
    disc = [(c[0] + cr * math.cos(a), c[1] + FLOWER_SQUASH * cr * math.sin(a)) for a in [math.pi * i / 10 for i in range(20)]]
    out = [foliage.Shape(name + ' centre', poly(disc), grad, outline, 1.5 if radius < 14 else 2)]
    if cr > 3:
        sx, sy, sr = c[0] - cr * 0.35, c[1] - cr * 0.4, cr * 0.32
        out.append(foliage.Shape(name + ' centre shine', poly([(sx + sr * math.cos(a), sy + sr * math.sin(a))
                                                               for a in [math.pi * i / 6 for i in range(12)]]),
                                 foliage.CENTRE_SHINE))
    return out


def stem_points(length, bow, n=8):
    return [(bow * length * math.sin(math.pi * i / n), -length * i / n) for i in range(n + 1)]


def stem(svg, name, length, width=(STEM_WIDTH, STEM_OUTLINE), bow=STEM_BOW):
    """A green stem from the foot straight up, bowing sideways by bow of its length, and the point it ends at."""
    pts = stem_points(length, bow)
    d = poly(pts, close=False)
    svg.path(d, 'none', foliage.LEAF_OUTLINE, width[0] + width[1], name=name + ' stem')
    svg.path(d, 'none', foliage.STEM, width[0], name=name + ' stem core')
    return pts[-1]


def leaves(svg, name, length, specs, width=LEAF_WIDTH, bow=STEM_BOW):
    for i, (up, angle, size) in enumerate(specs):
        y = -up
        x = bow * length * math.sin(math.pi * up / length)
        put(svg, foliage.leaf('%s leaf %d' % (name, i + 1), (x, y), math.radians(angle), size, LEAF_TONE,
                              bend=0.08 if angle < -90 else -0.08, width=width, stroke=LEAF_STROKE,
                              gloss=False))


def flower(svg, tid, palette, radius, notch, length, leaf_specs, bow=STEM_BOW, turn=None):
    leaves(svg, tid, length, leaf_specs, bow=bow)
    top = stem(svg, tid, length, SMALL_STEM if radius < SMALL_RADIUS else (STEM_WIDTH, STEM_OUTLINE), bow)
    stroke = min(foliage.STROKE, max(1.5, radius / 4.5))
    turn = FLOWER_TURN if turn is None else math.radians(turn)
    put(svg, recoloured(foliage.flower(tid + ' head', top, radius, -math.pi / 2 + turn, FLOWER_SQUASH, stroke=stroke,
                                       notch=notch), palette) + centre(tid, top, radius, palette))


def bezier(p0, p1, p2, n=6):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(1, n + 1)]]


def tulip_head(c, w, h):
    """A tulip's crown standing on c: a cup with a broad, slightly rounded base and nearly straight sides whose
    two outer petals flare out to sharp tips, with the middle petal's taller tip between them in deep V
    notches. Returns its outline, the right petal (turned from the light), the middle petal, and the two
    petal seams."""
    x, b = c
    hw = w / 2
    left_shoulder, right_shoulder = (x - hw * 0.94, b - h * 0.44), (x + hw * 0.94, b - h * 0.44)
    left_tip, right_tip, mid_tip = (x - hw * 0.98, b - h * 0.88), (x + hw * 1.0, b - h * 0.95), (x, b - h * 1.05)
    left_dip, right_dip = (x - hw * 0.4, b - h * 0.52), (x + hw * 0.4, b - h * 0.52)
    bottom = [left_shoulder] + bezier(left_shoulder, (x - hw * 0.86, b - h * 0.04), (x - hw * 0.3, b), 4) + \
        bezier((x - hw * 0.3, b), (x, b + h * 0.03), (x + hw * 0.3, b), 2) + \
        bezier((x + hw * 0.3, b), (x + hw * 0.86, b - h * 0.04), right_shoulder, 4)
    right_side = bezier(right_shoulder, (x + hw * 0.96, b - h * 0.7), right_tip, 4)
    right_in = bezier(right_tip, (x + hw * 0.7, b - h * 0.66), right_dip, 4)
    mid_right = bezier(right_dip, (x + hw * 0.3, b - h * 0.8), mid_tip, 4)
    mid_left = bezier(mid_tip, (x - hw * 0.3, b - h * 0.8), left_dip, 4)
    left_in = bezier(left_dip, (x - hw * 0.7, b - h * 0.62), left_tip, 4)
    left_side = bezier(left_tip, (x - hw * 0.96, b - h * 0.66), left_shoulder, 4)
    outline = bottom + right_side + right_in + mid_right + mid_left + left_in + left_side
    low_left, low_right = (x - hw * 0.2, b - h * 0.08), (x + hw * 0.2, b - h * 0.08)
    seams = ((left_dip, (x - hw * 0.34, b - h * 0.26), low_left), (right_dip, (x + hw * 0.34, b - h * 0.26), low_right))
    right_petal = [right_dip] + bezier(*seams[1], 4) + [p for p in bottom if p[0] > low_right[0] and p[1] < b - 1] + \
        right_side + right_in
    middle = [left_dip] + bezier(*seams[0], 4) + bezier(low_left, (x, b + h * 0.02), low_right, 4) + \
        bezier(low_right, seams[1][1], right_dip, 4) + mid_right + mid_left
    return outline, right_petal, middle, seams


def tulip(svg, tid, colours, w, h, length, leaf_specs, bow=STEM_BOW, turn=None):
    """A tulip on its stem; its cup stays upright whatever the turn, which only the flowers' open faces take."""
    grad, outline, shade, line, light = TULIPS[colours]
    leaves(svg, tid, length, leaf_specs, TULIP_LEAF_WIDTH, bow)
    top = stem(svg, tid, length - h * 0.1, TULIP_STEM, bow)
    head, right, middle, seams = tulip_head((top[0], top[1] + h * 0.06), w, h)
    svg.path(poly(head), grad, outline, 3, name=tid + ' head')
    svg.path(poly(right), shade, name=tid + ' shade')
    svg.path(poly(middle), grad, name=tid + ' middle petal')
    svg.stroke(' '.join(poly(bezier(*seam, 4), close=False) for seam in seams), line, max(1.5, w / 12),
               name=tid + ' lines')
    cx, cy, rx, ry = top[0], top[1] - h * 0.3, w * 0.11, h * 0.2
    svg.path(poly([(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in [2 * math.pi * i / 14 for i in range(14)]]),
             light, name=tid + ' shine')


def tuft(svg, tid, blades, width):
    """Thin rounded blades standing apart along the foot, leaning out a little, the short ones darker."""
    tallest = max(b[2] for b in blades)
    for i, (x, lean, h) in enumerate(sorted(blades, key=lambda b: b[2])):
        base = (x, -width / 2)
        tip = (x + lean, -h)
        mid = ((base[0] + tip[0]) / 2 + lean * 0.3, (base[1] + tip[1]) / 2)
        colour = TUFT_SHADE if h < tallest * 0.6 else TUFT
        svg.stroke(poly([base] + bezier(base, mid, tip, 5), close=False), colour, width, name='%s blade %d' % (tid, i + 1))


DRAW = {'flower': flower, 'tulip': tulip, 'tuft': tuft}


def draw(svg, tid):
    """The template tid standing on (0, 0)."""
    _, kind, args = next(t for t in TEMPLATES if t[0] == tid)
    DRAW[kind](svg, tid, *args)


def main():
    svg = Svg()
    for tid, _, _ in TEMPLATES:
        svg.template(tid, lambda s, tid=tid: draw(s, tid))
    for i, (tid, _, _) in enumerate(TEMPLATES):
        svg.place('preview ' + tid, tid, (PREVIEW_GAP * (i + 1), PREVIEW_Y), (1, 1), lambda s, tid=tid: draw(s, tid))
    svg.write(cutting.sheet_path('plants/wildflowers.svg'))


def parts():
    """Each template's image, standing on its foot."""
    root, grads = cutting.load('plants/wildflowers.svg')
    return [cutting.foot_part('plants/parts/wildflowers/' + g.get('data-template'), list(g), grads,
                              g.get('data-template'))
            for g in root.iter(cutting.NS + 'g') if g.get('data-template') and not g.get('data-at')]


if __name__ == '__main__':
    main()

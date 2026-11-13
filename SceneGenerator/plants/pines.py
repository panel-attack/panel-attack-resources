#   Writes SVG, run by `python3 -m scene_export render`: plants/pines.svg, the day valley's fir trees, each a
#   template standing on its foot: three silhouettes (slim, full, tall) at three distances (near, mid, far).
#
#   python3 -m plants.pines  ->  pines.svg

import math
import os
import random

from common.painting import Svg, f, mix, poly
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))


# A fir is a short trunk under a stack of overlapping triangular tiers, each wider than the one above, with
# sharp upturned points at its lower corners and a hem sagging between them. Every tier has a thick dark outline, a
# dark blue-green rim inside it, a shaded right side, a lit patch down its left and a few soft pale blotches
# (colours sampled off the near firs in stage.png).
FIR_BODY = '#36924c'


FIR_LIT = '#58bd56'


FIR_RIM = '#25604e'              # the shadow just inside a tier's hem and right side, leaning blue like the reference's


FIR_SHADE = '#25594b'            # the right of a tier's face, away from the light


FIR_LINE = '#1f3443'


FIR_BLOTCH = '#7acb66'           # soft pale blotches on a near tier


TRUNK = ('#b5712a', '#8a501f')    # lit left, shaded right


TRUNK_LINE = '#5a3414'


TRUNK_HAZE = 0.4                 # a far trunk takes this share of its crown's haze, so it stays brown


# silhouettes: (half width of the bottom tier, height to the tip, tiers when near), all at the near size
SHAPES = {'slim': (14, 64, 3), 'full': (18, 66, 3), 'tall': (16, 72, 4)}


TRUNK_HEIGHT = 0.17              # visible trunk below the bottom tier, as a share of the height


TRUNK_HALF_WIDTH = 0.28          # trunk half width, as a share of the bottom tier's half width


TIER_REACH = 1.6                 # a tier is this many tier steps tall, so it overlaps the one below it


TIER_NARROWING = 0.38            # the top tier is this much narrower than the bottom one


TIER_SAG = 0.04                  # a tier's hem sags this share of its height below its points in the middle


TIER_TIP = 0.02                  # the points turn up this share of the tier's height


TIER_FLARE = 1.08                # the points stick out this far past the side's line, in half widths


TIER_WAIST = -0.04               # a tier's sides bow inward by this share of its half width (out, when negative)


TIER_RIM = (0.06, 0.11, 0.08)     # the inner rim's width at the top, hem and right side, as shares of the tier's height


# distances: (scale from the near size, extra width, tiers less than near, (colour, share) mixed toward, line
# width, blotches per tier, lit patch width as a share of the half width); far firs are drawn fuller, as their
# small tiers would otherwise read as a thin spire
DISTANCES = {'near': (1.0, 1.0, 0, ('#2a6e8a', 0.0), 2.8, 2, 0.45),
             'mid': (0.64, 1.08, 0, ('#2a6e8a', 0.08), 2.0, 1, 0.42),
             'far': (0.4, 1.2, 1, ('#4f9a8a', 0.3), 1.4, 0, 0.4)}


TEMPLATES = ['pine-%s-%s' % (shape, distance) for distance in DISTANCES for shape in SHAPES]


def tier_outline(top, bottom, hw, rng, dx=0.0):
    """A tier's outline: apex at (0, top), its sides flaring out to pointed tips at (+-hw, bottom), its lower
    edge a skirt sagging down between the tips."""
    h = bottom - top
    waist = hw * TIER_WAIST
    sag = h * TIER_SAG
    jl, jr = rng.uniform(-0.04, 0.04) * hw, rng.uniform(-0.04, 0.04) * hw
    return ('M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z'
            % (f(dx), f(top), f(dx - hw * 0.5 + waist), f(top + h * 0.55), f(dx - hw * TIER_FLARE + jl), f(bottom - h * TIER_TIP),
               f(dx - hw * 0.55), f(bottom + sag * 1.1), f(dx), f(bottom + sag),
               f(dx + hw * 0.55), f(bottom + sag * 1.1), f(dx + hw * TIER_FLARE + jr), f(bottom - h * TIER_TIP),
               f(dx + hw * 0.5 - waist), f(top + h * 0.55), f(dx), f(top)))


def side_x(top, bottom, hw, y):
    """How far the tier's side curve is from its middle at height y, a little inside the drawn outline."""
    h = bottom - top
    cx, cy = hw * 0.5 - hw * TIER_WAIST, h * 0.55
    ex, ey = hw, h * (1 - TIER_TIP)
    target = min(ey, max(0.0, y - top))
    lo, hi = 0.0, 1.0
    for _ in range(24):
        u = (lo + hi) / 2
        if 2 * u * (1 - u) * cy + u * u * ey < target:
            lo = u
        else:
            hi = u
    u = (lo + hi) / 2
    return (2 * u * (1 - u) * cx + u * u * ex) * 0.94


def lit_patch(top, bottom, hw, share, dx):
    """The lit patch down the left of a tier's inner face (top, bottom, hw, centred on dx): from under the apex to
    the hem, between its left side and a line leaning in toward the middle."""
    h = bottom - top
    y0, y1 = top + h * 0.2, bottom - h * TIER_TIP
    outer = [(dx - side_x(top, bottom, hw, y) * 0.95, y) for y in (y0, (y0 + y1) / 2, y1)]
    inner = [(dx - hw * (0.9 - share), bottom), (dx - side_x(top, bottom, hw, y0) * 0.1, y0)]
    return poly(outer + inner)


def shade_side(top, bottom, hw, dx):
    """The right of a tier's inner face (top, bottom, hw, centred on dx), away from the light."""
    h = bottom - top
    ys = [top + h * (1 - TIER_TIP) * i / 8 for i in range(9)]
    outer = [(dx + side_x(top, bottom, hw, y) / 0.94, y) for y in ys]
    return poly([(dx, top)] + outer + [(dx + hw * 0.6, bottom + h * TIER_SAG * 0.6),
                                       (dx + hw * 0.22, bottom + h * TIER_SAG * 0.95), (dx + hw * 0.05, top + h * 0.3)])


def blotches(rng, top, bottom, hw, n, r, dx):
    """n soft round blotches scattered over a tier's inner face, more on its lit left."""
    out = []
    for _ in range(n):
        y = top + (bottom - top) * rng.uniform(0.45, 0.75)
        x = dx + side_x(top, bottom, hw, y) * rng.uniform(-0.6, 0.25)
        rr = r * rng.uniform(0.8, 1.25)
        out.append('M%s,%s A%s,%s 0 1,0 %s,%s A%s,%s 0 1,0 %s,%s Z'
                   % (f(x - rr), f(y), f(rr), f(rr * 0.8), f(x + rr), f(y), f(rr), f(rr * 0.8), f(x - rr), f(y)))
    return out


def tiers(hw, h, n):
    """[(top, bottom, half width)] of the n tiers, bottom first, standing over a trunk on (0, 0)."""
    crown_bottom = -h * TRUNK_HEIGHT
    step = (h + crown_bottom) / (n - 1 + TIER_REACH)
    out = []
    for k in range(n):
        bottom = crown_bottom - k * step
        top = -h if k == n - 1 else bottom - step * TIER_REACH
        out.append((top, bottom, hw * (1 - TIER_NARROWING * k / max(1, n - 1))))
    return out


def trunk(svg, hw, h, toward, t, line):
    """The short trunk standing on (0, 0), reaching up under the bottom tier, lit on its left."""
    tw = max(1.5, hw * TRUNK_HALF_WIDTH)
    top = -h * TRUNK_HEIGHT * 1.6
    svg.path(poly([(-tw, 0), (-tw, top), (tw, top), (tw, 0)]), mix(TRUNK[1], toward, t), mix(TRUNK_LINE, toward, t),
             line * 0.8, name='trunk')
    svg.path(poly([(-tw + line * 0.4, -line * 0.4), (-tw + line * 0.4, top), (tw * 0.1, top), (tw * 0.1, -line * 0.4)]),
             mix(TRUNK[0], toward, t), name='trunk lit')


def fir(svg, shape, distance, rng):
    """The fir of that silhouette at that distance, standing on (0, 0)."""
    scale, wider, fewer, (toward, t), line, n_blotches, lit_share = DISTANCES[distance]
    hw0, h0, n0 = SHAPES[shape]
    hw, h, n = hw0 * scale * wider, h0 * scale, max(3, n0 - fewer)
    stack = tiers(hw, h, n)
    svg.open('fir')
    trunk(svg, hw, h, toward, t * TRUNK_HAZE, line)
    for k, tier in enumerate(stack):
        top, bottom, thw = tier
        outline = tier_outline(top, bottom, thw, rng)
        svg.path(outline, mix(FIR_RIM, toward, t), name='tier')
        th = bottom - top
        r_top, r_hem, r_side = (share * th for share in TIER_RIM)
        itop, ibottom = top + r_top, bottom - r_hem
        ihw = thw * (ibottom - itop) / th - r_side * 0.5
        dx = -r_side * 0.5
        svg.path(tier_outline(itop, ibottom, ihw, random.Random(0), dx), mix(FIR_BODY, toward, t), name='tier face')
        svg.path(shade_side(itop, ibottom, ihw, dx), mix(FIR_SHADE, toward, t), name='tier shade')
        svg.path(lit_patch(itop, ibottom, ihw, lit_share, dx), mix(FIR_LIT, toward, t), name='tier lit')
        if n_blotches:
            spots = blotches(rng, itop, ibottom, ihw, n_blotches, max(0.8, hw * 0.09), dx)
            svg.path(' '.join(spots), mix(FIR_BLOTCH, toward, t), name='blotches')
        svg.path(outline, 'none', mix(FIR_LINE, toward, t), line, name='tier outline')
    svg.close()


def draw(svg, tid):
    """The template tid standing on (0, 0)."""
    _, shape, distance = tid.split('-')
    fir(svg, shape, distance, random.Random(tid))


def main():
    svg = Svg()
    for tid in TEMPLATES:
        svg.template(tid, lambda s: draw(s, tid))
    svg.write(cutting.sheet_path('plants/pines.svg'))


def parts():
    """Each template's image, standing on its foot."""
    root, grads = cutting.load('plants/pines.svg')
    return [cutting.foot_part('plants/parts/pines/' + g.get('data-template'), list(g), grads, g.get('data-template'))
            for g in root.iter(cutting.NS + 'g') if g.get('data-template')]


if __name__ == '__main__':
    main()

#   Writes SVG, run by `python3 -m scene_export render`: scenery/sun.svg, the day valley's sun, its disc and soft
#   glow as one image.
#
#   python3 -m scenery.sun  ->  sun.svg

import os

from common.painting import Svg, f, mix
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))


CENTRE = (1259, 215.5)           # the disc's, measured off DayValley/stage.png, in sheet px
DISC_R = 43.5
GLOW_CENTRE = (1254, 207)        # the glow's own centre sits a little above and left of the disc's
GLOW_WIDE = 1.04                 # the glow is an oval, this much wider than tall; its radii below are its heights
DISC = '#fef7dd'
RIM = ('#fbf9e6', 1.5)          # the disc's edge is a little whiter than its face
GLOW_INNER, GLOW_OUTER = '#fff6d6', '#e4f6ff'   # warm by the disc, a pale sky-white where it fades out
GLOW_TURN = (95, 160)           # radii between which the glow's colour turns from inner to outer

# How opaque the glow is at a distance from the centre, measured off stage.png against the sky beside it: bright
# right at the disc, fading to nothing about five disc radii out.
GLOW_PROFILE = ((40, 0.84), (50, 0.80), (62, 0.74), (74, 0.66), (86, 0.55), (98, 0.43), (110, 0.323),
                (122, 0.227), (134, 0.16), (146, 0.117), (158, 0.085), (170, 0.053), (182, 0.031), (194, 0.019),
                (212, 0.015), (230, 0.01), (248, 0.0))
RING_STEP = 3                    # px between the glow's rings: close enough that no ring edge shows


def glow_at(d):
    for (d0, a0), (d1, a1) in zip(GLOW_PROFILE, GLOW_PROFILE[1:]):
        if d <= d1:
            t = (d - d0) / (d1 - d0)
            return a0 + (a1 - a0) * max(0.0, t)
    return 0.0


def ellipse(r, centre=CENTRE, wide=1.0):
    cx, cy = centre
    rx = r * wide
    return 'M%s,%s A%s,%s 0 1 1 %s,%s A%s,%s 0 1 1 %s,%s Z' % (
        f(cx - rx), f(cy), f(rx), f(r), f(cx + rx), f(cy), f(rx), f(r), f(cx - rx), f(cy))


def glow_rings():
    """(radius, opacity) of each glow ring, largest first. The kit has no radial gradient, so the glow is
    discs of one colour stacked: a ring between two radii is covered by every disc at least that big, and each
    disc's opacity is what makes the stack's coverage there follow GLOW_PROFILE."""
    first, last = GLOW_PROFILE[0][0], GLOW_PROFILE[-1][0]
    radii = list(range(first, last + 1, RING_STEP))
    clear = [1 - glow_at(r - RING_STEP / 2) for r in radii] + [1.0]
    rings = []
    for k, r in enumerate(radii):
        opacity = 1 - clear[k] / clear[k + 1]
        if opacity > 0.001:
            rings.append((r, opacity))
    return list(reversed(rings))


def glow_colour(r):
    t = (r - GLOW_TURN[0]) / (GLOW_TURN[1] - GLOW_TURN[0])
    return mix(GLOW_INNER, GLOW_OUTER, min(1.0, max(0.0, t)))


def sun(svg):
    svg.open('Sun')
    for r, opacity in glow_rings():
        svg.path(ellipse(r, GLOW_CENTRE, GLOW_WIDE), glow_colour(r), name='glow', extra=' fill-opacity="%.4f"' % opacity)
    svg.path(ellipse(DISC_R - RIM[1] / 2), DISC, line=RIM[0], width=RIM[1], name='disc')
    svg.close()


def main():
    svg = Svg()
    sun(svg)
    svg.write(cutting.sheet_path('scenery/sun.svg'))


def parts():
    root, grads = cutting.load('scenery/sun.svg')
    return [cutting.static_part('scenery/parts/sun/sun', [cutting.find_group(root, 'Sun')], grads, 'sun')]


if __name__ == '__main__':
    main()

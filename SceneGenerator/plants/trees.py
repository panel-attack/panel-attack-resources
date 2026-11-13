#   Writes SVG, run by `python3 -m scene_export render`: plants/trees.svg, the cypress and leafy clump templates,
#   each standing on its foot.
#
#   python3 -m plants.trees  ->  trees.svg

import math
import os
import random

from common.painting import (FLOWER, FLOWER_CENTRE, FLOWER_DEEP, HAZE, Svg, blossom, crown_field, f,
                             inside_foliage, land_colours, mix, poly)
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))
# every template, in the order they were added, so a new one leaves the sheet's earlier templates unchanged
TEMPLATES = ['cypress-stout', 'leafy-clump', 'leafy-clump-flowering', 'cypress-slender', 'cypress-slender-hazy',
             'cypress-hazy', 'cypress', 'cypress-broad-far', 'cypress-broad-farthest', 'cypress-full-far',
             'cypress-full-farthest', 'cypress-narrow-far', 'cypress-narrow-farthest', 'far-clump', 'far-clump-round',
             'far-clump-wide', 'far-shrub']


# cypress: a dark body with a chunky, upward-chipped outline, covered in leaf chips: mid green
# chips over most of it and lit chips down the left (sampled off the reference)
CYPRESS = ('#2a8c40', '#0a6650')        # body, top -> bottom


CYPRESS_MID = '#4aa63c'


CYPRESS_LIT = '#92ca3e'


CYPRESS_LINE = '#0a5236'


CYPRESS_SHADE = '#0b5a40'        # right side, away from the sun


CYPRESS_SHADE_FROM = 0.3         # shade starts this share of the half width right of the trunk line


FAR_CYPRESS_HAZE = 0.3           # back-row cypresses are mixed this far toward HAZE


FAR_TREE_HAZE = ('#2a78b8', 0.55)   # (colour, share) the far shore's cypresses are mixed toward: the hills' blue


FARTHEST_TREE_HAZE = ('#3286c4', 0.9)   # (colour, share) the cypresses on the far hill crests are mixed toward


CYPRESS_TAPER = 0.7              # outline fullness: lower keeps the flame wide further up


CYPRESS_TIER = 0.6               # height of one chipped tier of the outline, in half widths at the base


CYPRESS_CHIP = 0.36              # leaf chip width, in half widths at the base


CLUMP_CROWN = 1 / 11             # crown radius as a share of clump width: small lumps, not one dome


# the faint shadow a far tree casts straight down at its foot under the high sun: (colour, opacity by variant,
# how wide and how tall it reaches either side of the trunk, in the tree's widths)
FOOT_SHADOW = dict(colour='#0b4030', opacity={'far': 0.2, 'farthest': 0.12}, width=0.55, height=0.06)


# The cypresses and clumps are each drawn as a shared template, scaled down from the template's size to their
# own where they are placed, so the scene can place one image many times.
# cypress templates: (id, half width, height); a cypress is drawn as the one nearest its height to width
CYPRESS_TEMPLATES = [('cypress-stout', 39, 287), ('cypress', 39, 306), ('cypress-slender', 20, 193),
                     ('cypress-broad', 44, 150), ('cypress-full', 38, 162), ('cypress-narrow', 31, 168)]


# cypress variants: (colour, share) a variant is mixed toward
CYPRESS_VARIANTS = {'hazy': (HAZE, FAR_CYPRESS_HAZE), 'far': FAR_TREE_HAZE, 'farthest': FARTHEST_TREE_HAZE}


# clump templates, plain and flowering, then the far shore's round trees and the low shrubs along its banks:
# (id, width, height, depth, flowers)
CLUMP_TEMPLATES = [('leafy-clump', 84, 68, 1.0, 0), ('leafy-clump-flowering', 92, 70, 0.95, 3),
                   ('far-clump', 76, 68, 1.0, 0), ('far-clump-round', 64, 72, 1.0, 0), ('far-clump-wide', 98, 62, 1.0, 0),
                   ('far-shrub', 96, 38, 1.0, 0)]


def leafy_clump(svg, rng, x, top, w, depth, flowers, base):
    """A domed clump of small leaf crowns standing on base, with blossoms tucked among the
    crowns on its sunlit upper-left."""
    h = base - top
    dome = [(x - w / 2, top + h * 0.95), (x - w * 0.36, top + h * 0.3), (x, top), (x + w * 0.36, top + h * 0.25),
            (x + w / 2, top + h * 0.95)]
    crown_field(svg, rng, dome, base, depth, w * CLUMP_CROWN, 'leafy clump', free_standing=True)
    if flowers:
        shade, petals, centres = [], [], []
        for _ in range(flowers * 3):
            fx, fy = x + rng.uniform(-0.38, 0.1) * w, top + rng.uniform(0.2, 0.55) * h
            fr = rng.uniform(2.2, 3.4)
            if not inside_foliage(dome, fx, fy, fr):
                continue
            parts = blossom(fx, fy, fr)
            shade.append(parts[0])
            petals.append(parts[1])
            centres.append(parts[2])
        if shade:
            leaf = land_colours(depth)[0]
            svg.open('blossoms')
            svg.path(' '.join(shade), mix(FLOWER_DEEP, leaf, 0.2), name='petal shade')
            svg.path(' '.join(petals), mix(FLOWER, leaf, 0.15), name='petals')
            svg.path(' '.join(centres), FLOWER_CENTRE, name='centres')
            svg.close()



def leaf_chip(x, y, w, h, lean):
    """A small upward-pointing leaf chip standing on (x, y)."""
    return ('M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z'
            % (f(x - w / 2), f(y), f(x - w * 0.5), f(y - h * 0.6), f(x + lean), f(y - h),
               f(x + w * 0.5), f(y - h * 0.55), f(x + w / 2), f(y), f(x), f(y + h * 0.22), f(x - w / 2), f(y)))


def foot_shadow(svg, w, variant):
    """The faint shadow a far tree w px wide casts straight down on the ground at its foot, standing on (0, 0)."""
    s = FOOT_SHADOW
    rx, ry = w * s['width'], w * s['height']
    pts = [(rx * math.cos(a), -ry - ry * math.sin(a)) for a in (i * math.pi / 24 for i in range(48))]
    svg.path(poly(pts), s['colour'], name='foot shadow', extra=' fill-opacity="%g"' % s['opacity'][variant])


def draw(svg, tid):
    """The template tid standing on (0, 0)."""
    clump = next((c for c in CLUMP_TEMPLATES if c[0] == tid), None)
    if clump:
        _, tw, th, tdepth, tflowers = clump
        if tid.startswith('far-'):
            foot_shadow(svg, tw, 'far')
        leafy_clump(svg, random.Random(tid), 0, -th, tw, tdepth, tflowers, base=0)
        return
    shape, _, variant = tid.rpartition('-')
    if variant not in CYPRESS_VARIANTS:
        shape = tid
    _, thw, th = next(c for c in CYPRESS_TEMPLATES if c[0] == shape)
    toward, t = CYPRESS_VARIANTS.get(variant, (HAZE, 0.0))
    if variant in FOOT_SHADOW['opacity']:
        foot_shadow(svg, thw * 2, variant)
    cypress(svg, 0, -th, thw, base=0, rng=random.Random(tid), haze_t=t, toward=toward)


def placed_cypress(svg, name, x, top, hw, base, variant=''):
    """The cypress template nearest this one's height to width, of those with the variant ('hazy', 'far' or
    'farthest'), scaled to it and standing on (x, base)."""
    h = base - top
    variant = variant and '-' + variant
    shapes = [t for t in CYPRESS_TEMPLATES if t[0] + variant in TEMPLATES]
    tid, thw, th = min(shapes, key=lambda t: abs(t[2] / t[1] - h / hw))
    tid += variant
    svg.place(name, tid, (x, base), (hw / thw, h / th), lambda s: draw(s, tid))


def placed(svg, name, tid, x, base, h):
    """The clump template tid at its own proportions, h px tall and standing on (x, base)."""
    _, tw, th, _, _ = next(c for c in CLUMP_TEMPLATES if c[0] == tid)
    svg.place(name, tid, (x, base), (h / th, h / th), lambda s: draw(s, tid))


def placed_clump(svg, name, x, top, w, flowers, base):
    """The plain or flowering clump template, scaled to w wide and standing on (x, base) with its top at top."""
    tid = 'leafy-clump-flowering' if flowers else 'leafy-clump'
    _, tw, th, _, _ = next(c for c in CLUMP_TEMPLATES if c[0] == tid)
    svg.place(name, tid, (x, base), (w / tw, (base - top) / th), lambda s: draw(s, tid))


def cypress(svg, x, top, hw, base, rng=None, haze_t=0.0, toward=HAZE):
    """Tall flame-shaped cypress: dark body with a chunky chipped outline and a pointed top,
    covered in stacked leaf chips, mid green with lit chips down its left side, all mixed haze_t toward toward."""
    rng = rng or random.Random(int(x * 7 + top))
    h = base - top

    def half_width(t):
        return hw * max(0.0, 1 - t) ** CYPRESS_TAPER * (0.8 + 0.2 * min(1, t / 0.3))

    tier = hw * CYPRESS_TIER
    n = max(6, int(h / tier))
    # outline: up the left side as tiers, each bulging out to a chip point that leans upward
    left, right = [], []
    for i in range(n):
        t0, tm = i / n, (i + 0.6) / n
        y0, ym = base - h * t0, base - h * tm
        jl, jr = rng.uniform(0.9, 1.12), rng.uniform(0.9, 1.12)
        left.append(((x - half_width(t0) * 0.9, y0), (x - half_width(tm) * 1.06 * jl, y0 - (y0 - ym) * 0.25),
                     (x - half_width(tm) * jl, ym)))
        right.append(((x + half_width(t0) * 0.9, y0), (x + half_width(tm) * 1.06 * jr, y0 - (y0 - ym) * 0.25),
                      (x + half_width(tm) * jr, ym)))
    d = 'M%s,%s' % (f(x - half_width(0) * 0.9), f(base))
    for (sx, sy), (cx, cy), (px, py) in left:
        d += ' L%s,%s Q%s,%s %s,%s' % (f(sx), f(sy), f(cx), f(cy), f(px), f(py))
    d += ' L%s,%s' % (f(x + rng.uniform(-1, 1)), f(top))
    for (sx, sy), (cx, cy), (px, py) in reversed(right):
        d += ' L%s,%s Q%s,%s %s,%s' % (f(px), f(py), f(cx), f(cy), f(sx), f(sy))
    d += ' Z'
    svg.open('cypress')
    svg.path(d, (mix(CYPRESS[0], toward, haze_t), mix(CYPRESS[1], toward, haze_t), top, base),
             mix(CYPRESS_LINE, toward, haze_t), 1.2, name='body')
    ts = [i / 24 for i in range(25)]
    outer = [(x + half_width(tt) * 0.98, base - h * tt) for tt in ts]
    inner = [(x + half_width(tt) * CYPRESS_SHADE_FROM, base - h * tt) for tt in reversed(ts)]
    svg.path(poly(outer + inner), mix(CYPRESS_SHADE, toward, haze_t), name='shaded side')
    mid, lit = [], []
    cw = max(4.0, hw * CYPRESS_CHIP)
    y = base - cw * 0.4
    row = 0
    while y > top + cw * 1.2:
        t = (base - y) / h
        span = half_width(t) * 0.82
        cx = x - span + (cw * 0.5 if row % 2 else 0) + rng.uniform(0, cw * 0.3)
        while cx < x + span - cw * 0.3:
            side = (cx - x) / max(1.0, span)
            if rng.random() > 0.32:
                chip = leaf_chip(cx, y, cw * rng.uniform(0.8, 1.15), cw * rng.uniform(1.1, 1.5), side * cw * 0.25)
                if side < -0.45 or (side < -0.1 and rng.random() < 0.3):
                    lit.append(chip)
                elif side < 0.45:
                    mid.append(chip)
            cx += cw * rng.uniform(0.7, 0.95)
        y -= cw * rng.uniform(0.55, 0.7)
        row += 1
    if mid:
        svg.path(' '.join(mid), mix(CYPRESS_MID, toward, haze_t), name='leaf chips')
    if lit:
        svg.path(' '.join(lit), mix(CYPRESS_LIT, toward, haze_t), name='lit chips')
    svg.close()


def main():
    svg = Svg()
    for tid in TEMPLATES:
        svg.template(tid, lambda s: draw(s, tid))
    svg.write(cutting.sheet_path('plants/trees.svg'))


def parts():
    """Each template's image, standing on its foot."""
    root, grads = cutting.load('plants/trees.svg')
    return [cutting.foot_part('plants/parts/trees/' + g.get('data-template'), list(g), grads, g.get('data-template'))
            for g in root.iter(cutting.NS + 'g') if g.get('data-template')]


if __name__ == '__main__':
    main()

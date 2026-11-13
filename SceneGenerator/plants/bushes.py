#   Writes SVG, run by `python3 -m scene_export render`: plants/bushes.svg, the corner bush: a big rose bush in a
#   gold planter filling the bottom-left corner, in front of the rail and the floor's edge, grown from
#   branches.py's library pieces.
#
#   python3 -m plants.bushes  ->  bushes.svg

import math
import os
import random

import numpy as np

from scene_export import cutting
from furniture.planters import CORNER_LEAF, GOLD_SHEEN, STROKE, Out, add_pieces, bush_layout
from plants import bushes_reference as T
from plants import foliage
from plants.foliage import Shape, poly

HERE = os.path.dirname(os.path.abspath(__file__))

CORNER_RIM_CLEAR = (-30, 55)   # the planter's rim shows bare at the frame's corner, as on the reference
CORNER_FOCUS = (70, 1010)      # the shoots radiate from the middle of the planter's soil
CORNER_FLOWER_K = 1.15         # the flowers measured on the reference read larger once outlined
CORNER_RIM_AT = (78, 122, 166, 204)    # where rosettes spill over the rim, clear of the bare corner
CORNER_SEED = 61


def corner_rim_front(x):
    r = T.CORNER_PLANTER_RIM
    return r['cy'] + r['b'] * math.sqrt(max(0.0, 1 - ((x - r['cx']) / r['a']) ** 2))


def corner_bush_layout():
    """The corner bush as generated before it was thinned by hand (the scene keeps the hand edits): its edge
    runs along the outline in the frame, and rosettes spill over the rim."""
    outline = T.CORNER_BUSH_OUTLINE
    return bush_layout(outline, CORNER_FOCUS, CORNER_LEAF, corner_rim_front, CORNER_SEED, outline[1:-1],
                       CORNER_RIM_AT)


def corner_planter_rim(out):
    """The visible top of the corner bush's gold planter: the rim's lit top face and its front band."""
    r = T.CORNER_PLANTER_RIM
    cx, cy, a, b, band = r['cx'], r['cy'], r['a'], r['b'], r['band']
    front = [(cx + a * math.cos(t), cy + b * math.sin(t)) for t in np.linspace(math.pi, 0, 60)]
    lip = 13
    top = [(x, y) for x, y in front] + [(cx + (a - lip) * math.cos(t), cy + (b - lip * 0.25) * math.sin(t))
                                        for t in np.linspace(0, math.pi, 60)]
    out.shape('corner planter band', front[::-1] + [(x, y + band) for x, y in front], 'gold', 'gold')
    out.shape('corner planter band sheen', [(x, y + 3) for x, y in front[::-1][8:40]]
              + [(x, y + 7) for x, y in front[8:40]], GOLD_SHEEN, opacity=0.6)
    out.shape('corner planter rim top', top, 'gold-pale', 'gold')


def corner_bush_body():
    """The dark mass behind the leaves: the outline drawn in towards the soil, so leaves overhang it."""
    outline = T.CORNER_BUSH_OUTLINE
    fx, fy = CORNER_FOCUS
    left = min(p[0] for p in outline)
    inset = CORNER_LEAF * foliage.MOUND_MASS_INSET
    body = []
    for x, y in outline:
        d = math.hypot(x - fx, y - fy) or 1.0
        k = max(0.0, d - inset) / d
        body.append((fx + (x - fx) * k, fy + (y - fy) * k) if x > left else (x, y + inset * (y < fy - 200)))
    return Shape('corner bush mass', poly(body), 'bush-mass')


def corner_bush_flowers(out):
    rng = random.Random(CORNER_SEED + 1)
    for i, (x, y, r, kind) in enumerate(T.CORNER_BUSH_FLOWERS):
        r *= CORNER_FLOWER_K
        rot, squash = rng.uniform(0, 2 * math.pi), rng.uniform(0.88, 0.97)
        stroke = min(STROKE, max(1.5, r / 4.5))
        name = 'corner bush %s %d' % ('rose' if kind == 'rose' else 'white flower' if kind == 'white' else 'flower', i + 1)
        if kind == 'rose':
            out.add_all(foliage.rose(name, (x, y), r, rot, squash, stroke=stroke))
        else:
            out.add_all(foliage.flower(name, (x, y), r, rot, squash, kind == 'white', stroke=stroke,
                                       notch=foliage.MOUND_WHITE_NOTCH if kind == 'white' else foliage.MOUND_NOTCH))


def corner_bush(out):
    """The corner bush grown from branches.py's library pieces, each a group the scene places by one ref."""
    out.open('Corner bush')
    out.open('corner bush body')
    out.add(corner_bush_body())
    out.close()
    out.open('corner planter')
    corner_planter_rim(out)
    out.close()
    out.open('corner bush leaves')
    add_pieces(out, 'corner bush', corner_bush_layout())
    corner_bush_flowers(out)
    out.close()
    out.close()


def main():
    out = Out()
    corner_bush(out)
    out.write(cutting.sheet_path('plants/bushes.svg'), 'Bushes')


def parts():
    from scene_export import placed_foliage
    return placed_foliage.placed().parts['corner bush']


if __name__ == '__main__':
    main()

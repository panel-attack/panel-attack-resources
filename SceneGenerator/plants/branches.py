#   Library, writes nothing: the stem, rosette and branch pieces scene_export turns into the
#   plants/branches.json templates.
#
#   The shared foliage pieces bushes are gardened from: stems in two lengths and two widths, and camellia
#   rosettes and branches in three sizes, each drawn from foliage.py's leaves and twigs.
#
#     rosette   a shoot seen end on, pointing at the viewer: leaves round a centre at 137.5 degrees to each
#               other, the old ones outermost and splayed wide, the young ones small, upright and on top
#     branch    a woody stem seen from the side, bare at its foot, with leaves alternating along it and
#               side shoots growing from the axils of its upper leaves, the lowest shoot the longest
#
#   Every piece grows from (0, 0) and points up the screen. Each is a list of Draw records in paint order;
#   `python3 -m scene_export layout plants/branches.json` writes them as templates into the game's scenes/.

import math
import os
import random
from dataclasses import dataclass, field

from plants import foliage

HERE = os.path.dirname(os.path.abspath(__file__))
UP = -math.pi / 2

# stems: (length px, width px) of the stem images every piece's stems are placed from
STEM_LENGTHS = {'short': 12.0, 'long': 28.0}
STEM_WIDTHS = {'thin': 2.5, 'thick': 4.0}
SHOOT_STEM = 2.5                 # px across a shoot's stem
BRANCH_STEM = 4.0                # and a branch's woody stem

# leaves
LEAF_WIDTH = 0.54                # width / length of a full grown leaf
LEAF_STROKE = 2.5
LEAF_TWIST = math.radians(10)    # each leaf lies up to this far off its place either way
YOUNG_SIZE = (0.5, 0.65)         # the two leaves at a shoot's tip are this share of a full grown leaf
YOUNG_OFF = (math.radians(18), math.radians(30))   # and stand this far off the stem, still closing round the bud
LEAF_SIZE = (1.05, 0.7)          # a grown leaf's share of the leaf length at a shoot's foot and just below its
                                 # young leaves: the oldest leaves, lowest, have had longest to grow
LEAF_OFF = (math.radians(62), math.radians(40))    # grown leaves stand this far off the stem at a shoot's foot and
                                 # near its tip: the older a leaf the flatter it lies, turned to catch the light
LEAF_OFF_SPREAD = math.radians(7)
INNER_OFF = 0.3                  # a side shoot's leaves on the side facing the leader stand only this share as far
                                 # off, turned outward along the shoot to the light instead of into the bush
INTERNODE = (0.55, 0.42)         # leaf lengths between leaves at a shoot's foot and near its tip, one leaf
                                 # at each node
BUD_GAP = 0.4                    # leaf lengths of stem from the last leaf to the bud
FAR_DARKER = 1                   # a leaf on the far side of the stem is this many tones darker
FAR_SHOW = (0.7, 0.9)            # and shows this share of its length, turned away

# rosettes: (leaves, leaf length px) by size
ROSETTE_SIZES = {'small': (5, 34.0), 'medium': (6, 44.0), 'large': (8, 52.0)}
ROSETTE_TURN = math.radians(137.5)
ROSETTE_HEART = 0.08             # leaf lengths from the centre to each leaf's base, round the bud
ROSETTE_SPLAY = (math.radians(80), math.radians(45))   # the oldest leaf's angle off the axis, the youngest's

# branches: (leaf length px, bare foot in leaf lengths, side shoots, leaves on the leader) by size
BRANCH_SIZES = {'small': (36.0, 0.25, 1, 4), 'medium': (44.0, 0.3, 2, 5), 'large': (52.0, 0.35, 3, 5)}
SIDE_SHOOT_ANGLE = (math.radians(40), math.radians(58))
SIDE_SHOOT_FOOT = (0.7, 0.95)    # leaf lengths of bare stem before a side shoot's first leaf
SIDE_SHOOT_LEAVES = (4, 3)       # leaves on the lowest side shoot and on the highest
SIDE_SHOOT_RISE = 0.5            # a side shoot turns up towards the light this share of its lean off upright
BRANCH_BEND = math.radians(14)   # the leader curves up towards the light this much over its length
VARIANTS = 2                     # of each size

# densities besides the usual: (leaves added to a rosette and to each shoot, side shoots added, internode scale)
DENSITIES = {'sparse': (-1, -1, 1.25), 'dense': (1, 1, 0.85)}


@dataclass
class Draw:
    """One stem or leaf of a piece: kind 'stem' (base, angle, length, width) or 'leaf' (base, angle, length,
    width, tone, bend, gloss); group names the side shoot it belongs to, None for the piece itself."""
    kind: str
    base: tuple
    angle: float
    length: float
    width: float
    tone: int = 0
    bend: float = 0.0
    gloss: bool = False
    group: str = None


@dataclass
class Piece:
    id: str
    draws: list = field(default_factory=list)


@dataclass
class Placement:
    """Where a bush grows a piece: its base at `at` (px), turned by rotation, scaled and, when mirror is set,
    flipped side to side first, as the scene's loader draws a ref with those overrides. role says what the
    piece does in the bush."""
    piece: str
    at: tuple
    rotation: float
    scale: float
    mirror: bool = False
    role: str = ''


def placed(piece, placement):
    """The piece's draws where placement puts them."""
    c, s = math.cos(placement.rotation), math.sin(placement.rotation)
    flip = -1 if placement.mirror else 1

    def point(p):
        x, y = p[0] * flip * placement.scale, p[1] * placement.scale
        return placement.at[0] + c * x - s * y, placement.at[1] + s * x + c * y

    out = []
    for d in piece.draws:
        angle = math.atan2(math.sin(d.angle), math.cos(d.angle) * flip) + placement.rotation
        width = d.width * placement.scale if d.kind == 'stem' else d.width
        out.append(Draw(d.kind, point(d.base), angle, d.length * placement.scale, width, d.tone, d.bend * flip,
                        d.gloss, d.group))
    return out


def lit_tone(angle, young=False, far=False):
    """A leaf's tone from 1 (dark) to 5 (sun): brighter the more it points up towards the light."""
    up = -math.sin(angle)
    tone = 3 + (1 if up > 0.35 else 0) - (1 if up < -0.35 else 0)
    tone += 1 if young else 0
    tone -= FAR_DARKER if far else 0
    return max(1, min(5, tone))


def leaf(base, angle, length, rng, young=False, far=False, show=1.0, group=None):
    angle += rng.uniform(-LEAF_TWIST, LEAF_TWIST)
    drawn = length * show
    tone = lit_tone(angle, young, far)
    return Draw('leaf', base, angle, drawn, LEAF_WIDTH * length / drawn, tone,
                rng.uniform(-0.08, 0.08), tone >= 4 and rng.random() < 0.5, group)


def stem(a, b, width, group=None):
    """The stem from a to b in equal pieces no longer than the long stem image, so none is stretched."""
    length = math.dist(a, b)
    n = max(1, math.ceil(length / STEM_LENGTHS['long'] - 1e-9))
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    return [Draw('stem', (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n), angle, length / n, width,
                 group=group) for i in range(n)]


def walk(start, angle, bend, lengths):
    """The nodes along a stem from start: one after each length, the stem turning bend radians per px."""
    nodes, (x, y) = [], start
    for step in lengths:
        angle += bend * step / 2
        x, y = x + math.cos(angle) * step, y + math.sin(angle) * step
        angle += bend * step / 2
        nodes.append(((x, y), angle))
    return nodes


def shoot(start, angle, size, n, rng, width, group=None, first=None, bend=0.0, bare=0, spacing=1.0, outward=None):
    """A shoot from start along angle with n leaves alternating side to side, the gaps between them closing
    towards the tip and scaled by spacing, ending in two young leaves round its bud; its first bare nodes have
    lost their leaves. Its grown leaves shrink and stand closer to the stem towards the tip, and on a side shoot
    those on the side away from outward (the side growing away from the leader) turn out along the shoot.
    Leaves on the far side of the stem paint under it. Returns (draws, nodes)."""
    gaps = [(first if first is not None else INTERNODE[0] * spacing) * size]
    for k in range(1, n):
        t = k / max(1, n - 1)
        gaps.append(size * spacing * (INTERNODE[0] + (INTERNODE[1] - INTERNODE[0]) * t))
    nodes = walk(start, angle, bend, gaps)
    under, over, stems = [], [], []
    side = rng.choice((-1, 1))
    prev = start
    for k, (p, a) in enumerate(nodes):
        stems += stem(prev, p, width * (1 - 0.3 * k / max(1, n)), group)
        prev = p
        young = k >= n - 2
        t = k / max(1, n - 3)
        if young:
            off, ls = rng.uniform(*YOUNG_OFF), size * rng.uniform(*YOUNG_SIZE)
        else:
            off = LEAF_OFF[0] + (LEAF_OFF[1] - LEAF_OFF[0]) * t + rng.uniform(-LEAF_OFF_SPREAD, LEAF_OFF_SPREAD)
            off *= INNER_OFF if side == -(outward or side) else 1
            ls = size * (LEAF_SIZE[0] + (LEAF_SIZE[1] - LEAF_SIZE[0]) * t) * rng.uniform(0.95, 1.05)
        far = not young and k % 2 == 1
        show = rng.uniform(*FAR_SHOW) if far else 1.0
        d = leaf(p, a + side * off, ls, rng, young, far, show, group)
        if k >= bare:
            (under if far else over).append(d)
        side = -side
    (bud, bud_angle), = walk(prev, nodes[-1][1], bend, [size * BUD_GAP])
    stems += stem(prev, bud, width * 0.7, group)
    over.append(leaf(bud, bud_angle + rng.uniform(-0.15, 0.15), size * 0.38, rng, True, False, 1.0, group))
    return under + stems + over, nodes


def piece_id(kind, size_name, seed, density):
    return '-'.join([kind, size_name] + ([density] if density else []) + [str(seed)])


def rosette(size_name, seed, density=None):
    n, size = ROSETTE_SIZES[size_name]
    n += DENSITIES[density][0] if density else 0
    rng = random.Random(seed)
    phi = rng.uniform(0, 2 * math.pi)
    turn = 2 * math.pi * 2 / 5 if n <= 5 else ROSETTE_TURN   # five leaves sit evenly two fifths round apart
    draws = []
    for k in range(n):
        t = k / (n - 1)
        splay = ROSETTE_SPLAY[0] + (ROSETTE_SPLAY[1] - ROSETTE_SPLAY[0]) * t
        ls = size * rng.uniform(0.92, 1.05) * (1 - 0.2 * t)
        angle = phi + k * turn + rng.uniform(-0.12, 0.12)
        # a leaf splaying towards the top of the screen faces the sun, one towards the foot is in shade
        heart = (math.cos(angle) * size * ROSETTE_HEART, math.sin(angle) * size * ROSETTE_HEART)
        draws.append(leaf(heart, angle, ls, rng, False, False, math.sin(splay)))
    # the two youngest leaves stand up round the bud, so they show short, on top
    up = phi + n * turn
    for k in range(2):
        draws.append(leaf((0.0, 0.0), up + k * math.pi + rng.uniform(-0.3, 0.3), size * rng.uniform(*YOUNG_SIZE),
                          rng, True, False, 0.6))
    return Piece(piece_id('rosette', size_name, seed, density), draws)


def branch(size_name, seed, density=None):
    size, foot, sides, leader = BRANCH_SIZES[size_name]
    more, more_sides, spacing = DENSITIES[density] if density else (0, 0, 1.0)
    sides = max(1, sides + more_sides)
    leader += more
    rng = random.Random(100 + seed)
    lean = rng.uniform(-0.25, 0.25)
    curve = rng.choice((-1, 1)) * BRANCH_BEND
    angle = UP + lean
    n = sides + leader
    total = size * (foot + INTERNODE[0] * spacing * 0.8 * n)
    bend = curve / total
    # the leader: a bare woody foot, then nodes; the lowest nodes' axils hold the side shoots
    # the leaf under each side shoot has fallen, so the shoot shows where it grows from
    leader_draws, nodes = shoot((0.0, 0.0), angle, size, n, rng, BRANCH_STEM, first=foot, bend=bend, bare=sides,
                                spacing=spacing)
    draws = []
    side = 1 if curve < 0 else -1
    for j in range(sides):
        (p, a) = nodes[j]
        t = j / max(1, sides - 1)
        leaves = round(SIDE_SHOOT_LEAVES[0] + (SIDE_SHOOT_LEAVES[1] - SIDE_SHOOT_LEAVES[0]) * t) + more
        sa = a + side * rng.uniform(*SIDE_SHOOT_ANGLE)
        group = 'shoot %d' % (j + 1)
        ss, sfoot = size * rng.uniform(0.85, 0.95), rng.uniform(*SIDE_SHOOT_FOOT)
        length = ss * (sfoot + spacing * sum(INTERNODE) / 2 * (leaves - 1) + BUD_GAP)
        sub, _ = shoot(p, sa, ss, leaves, rng, SHOOT_STEM, group, first=sfoot,
                       bend=-(sa - UP) * SIDE_SHOOT_RISE / length, spacing=spacing, outward=side)
        draws += sub
        side = -side
    return Piece(piece_id('branch', size_name, seed, density), draws + leader_draws)


def library():
    """Each kind and size sparse, then its usual variants, then dense."""
    pieces = []
    for kind in (rosette, branch):
        for size_name in ('small', 'medium', 'large'):
            pieces.append(kind(size_name, 1, 'sparse'))
            for seed in range(1, VARIANTS + 1):
                pieces.append(kind(size_name, seed))
            pieces.append(kind(size_name, 1, 'dense'))
    return pieces


def shapes(piece, origin=(0.0, 0.0)):
    """foliage.py shapes drawing the piece with its base at origin."""
    out = []
    for i, d in enumerate(piece.draws):
        base = (origin[0] + d.base[0], origin[1] + d.base[1])
        name = '%s %s %d' % (piece.id, d.kind, i + 1)
        if d.kind == 'stem':
            out += foliage.twig(name, base, d.angle, d.length, d.width)
        else:
            tone = 'leaf-%d' % d.tone
            out += foliage.leaf(name, base, d.angle, d.length, tone, bend=d.bend, width=d.width,
                                stroke=LEAF_STROKE, gloss=d.gloss, shade=foliage.LEAF_SHADE_DEEP[tone])
    return out

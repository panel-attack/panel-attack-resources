#   Library, writes nothing: the leaf, flower and bush shapes planters.py and branches.py draw.
#
#   Flower bushes for the Esme terrace, drawn in screen space.
#
#   bush() scatters pointed leaves (two greens, each with a darker half whose
#   edge reads as the midrib) and pink five-petal flowers with yellow centres
#   over a dark-green dome, with a few small white filler flowers. vine() hangs
#   a stem with small leaves over a pot rim. Everything is seeded, so the same
#   arguments always give the same bush.
#
#   Shapes come back as Shape records (paint order); write them with
#   svg_path(). Fills are flat colours or the vertical gradients in GRADIENTS.

import math
import random
from dataclasses import dataclass

# ---------------------------------------------------------------- colours
GRADIENTS = {

    'petal': ('#ff9cc0', '#f0609a'),
    'petal-white': ('#ffffff', '#e6eef0'),
    'flower-centre': ('#fff27a', '#f5b52e'),
    'rose-mid': ('#ff86b4', '#ee5290'),
    'rose-cup': ('#e94886', '#d0306e'),
    'bush-mass': ('#1e6a1e', '#0f4a16'),
}
# Leaf tones, darkest (deep, low in the bush) to brightest (on top, facing the high sun): the leaf's
# gradient, its slightly darker far half, its soft midrib and (top tones only) a gloss streak. The steps
# are close, so a bush reads as one softly lit mass; the bush-mass green is kept for the deep gaps.
LEAF_LEVELS = [
    (('#3c9c28', '#24781a'), '#33901f', '#58b23a', None),
    (('#4eae2c', '#2c881c'), '#44a026', '#6cc244', None),
    (('#62c032', '#36981e'), '#56b22c', '#82d250', None),
    (('#78d23a', '#44a822'), '#6cc434', '#98e05c', '#a8ea6a'),
    (('#90e046', '#56b828'), '#82d23e', '#aeec6c', '#c0f480'),
]
LEAF_ALIASES = {'leaf-back': 2, 'leaf-dark': 3, 'leaf-light': 4}     # the named tones other callers use
GRADIENTS.update({'leaf-%d' % (i + 1): grad for i, (grad, _, _, _) in enumerate(LEAF_LEVELS)})
GRADIENTS.update({name: LEAF_LEVELS[k - 1][0] for name, k in LEAF_ALIASES.items()})


def _level(tone):
    return LEAF_LEVELS[(LEAF_ALIASES[tone] if tone in LEAF_ALIASES else int(tone.split('-')[1])) - 1]


LEAF_SHADE = {t: _level(t)[1] for t in GRADIENTS if t.startswith('leaf-')}
LEAF_VEIN = {t: _level(t)[2] for t in LEAF_SHADE}
# a two-tone leaf's far half: the dark end of the tone a level down, so the midrib split reads clearly
LEAF_SHADE_DEEP = {t: LEAF_LEVELS[max(0, LEAF_LEVELS.index(_level(t)) - 1)][0][1] for t in LEAF_SHADE}
LEAF_GLOSS = {t: _level(t)[3] for t in LEAF_SHADE}
LEAF_OUTLINE = '#1d5e1a'
# The sun is high, behind the camera and a little left: on screen the light comes from above, just left
# (x, y with y down, pointing towards the light). Each leaf's shade half is the one turned from it.
LIGHT_2D = (-0.16, -0.99)
CENTRE_SHINE = '#fffbd6'
PETAL_OUTLINE = '#c43a74'
PETAL_THROAT = '#e9578f'
PETAL_LINE = '#d44a82'
ROSE_PETAL = '#ffa3c8'           # the outside of a rose's petals
ROSE_INSIDE_BASE = '#d93a78'     # down in the cup, deepest
ROSE_RIM_LIGHT = '#ffc2da'       # a petal's rolled-back rim catching the light
ROSE_RIM = 0.6                   # the rim runs round a petal's last share of its length
ROSE_RIM_WIDTH = 0.14            # and is this share of its half width across
ROSE_BASE = 0.3                  # petals grow from a ring this share of the radius out, round the stamens
ROSE_STAMENS = 0.26              # the stamen tuft's radius, as a share of the rose's
ROSE_STAMEN_LIFT = 0.08          # and how far it stands up off the face
ROSE_ANTHERS = 11                # bumps round the tuft's edge
ROSE_PISTIL = '#d9d26a'           # the green-yellow pistil in the middle of the stamens
ROSE_WHORLS = [(0.78, 0.6, math.radians(15), '#ff8fbb'), (0.6, 0.47, math.radians(66), '#f56aa2')]
# (length, half width) as shares of the radius, rise off the face, and the colour of the petals' insides,
# paler on the open outer petals and deeper in the cup
ROSE_CUP = 0.55                  # a petal's sides curl in towards the middle by this share of its half width
# per whorl: each petal turns up to this many radians either way, and takes its own step of a shuffled spread
# this wide either way in length, width and lean, so no two petals of a whorl stand alike; the longer a petal
# the further it has opened out. The outer whorl stands even, as the reference's.
ROSE_JITTER = [(0.0, 0.0, 0.0, 0.0), (0.3, 0.2, 0.25, math.radians(8))]
ROSE_WHORL_TURN = math.radians(36)  # each whorl sits in the gaps of the one outside it
# a rose's outer petals stand mirrored left to right, as the reference's: its turn snaps to these steps, so
# an outer petal points straight down the face
ROSE_SYMMETRY = 2 * math.pi / 5
WHITE_OUTLINE = '#8fa59a'
WHITE_THROAT = '#dfe8ea'
CENTRE_OUTLINE = '#d0892a'
STEM = '#2f6b2a'
STEM_BACK = '#255a24'
TWIG = '#2f5a1c'                  # a clipped shrub's shoots, in the shade of its leaves
MASS_OUTLINE = '#245e26'
STROKE = 3
LEAF_STROKE = 2.5

# ---------------------------------------------------------------- shape tuning
LEAF_WIDTH = 0.54                # width / length (lanceolate, ~2.2:1)
LEAF_BEND = 0.12
LEAF_GROW = 1.22                 # bush leaves are this much larger than leaf_size
LEAF_THIN = 1.0                  # and this much sparser than a full cover                 # sideways bow of the midrib, per unit length
PETAL_NOTCH = 0.42               # notch depth between petals (fraction of radius)
FLOWER_SQUASH = (0.78, 0.95)     # vertical squash range: flowers face up and out
FLOWER_SIZES = (1.1, 0.75, 0.5)  # big / medium / small pink flowers, each with FLOWER_JITTER
FLOWER_JITTER = 0.25
FLOWER_SHRINK = 0.88             # a flower that finds no room in FLOWER_SHRINK_EVERY tries shrinks by this
FLOWER_SHRINK_EVERY = 250
FLOWER_MIN_SHRINK = 0.55
FLOWER_SCALE = 0.6               # bush flowers are this much of the flower_size passed in
FLOWER_COUNT = 1.0               # and this many times the flower count asked for
WHITE_FLOWER_SIZE = 0.48         # tiny white blossom radius relative to pink ones
LEAF_SIZE_RANGE = (0.6, 1.15)
TWO_TONE_FLOOR = 3                # two-tone bushes' darkest leaf level
VARIETY_BROAD = 0.25             # with variety, this share of leaves is broad and a little shorter
VARIETY_NARROW = 0.25            # and this share narrow and longer    # bush leaf lengths vary over this range of leaf_size
GLOSS_CHANCE = 0.4               # share of loose (non-bush) leaves with a gloss streak, if their tone has one

VINE_TAPER = 0.45                # a vine's leaves shrink by this share from its rim to its tip
VINE_SPLAY = (0.9, 1.25)         # radians each leaf of a pair turns off the stem

# growth: every leaf and flower grows out of a crown on the plant's base
CROWN_SPREAD = 0.5               # crown points spread this share of the way towards a shoot's x
CROWN_DROP = 0.6                # crowns sit this share of the height below the base line (inside the pot)
FAN = 1.8                       # leaves splay out further from upright than the line from their crown
DROOP = 0.3                     # radians a sideways leaf turns down under its own weight
LEAF_JITTER = 0.25               # random turn of each leaf's axis
LEAF_ARCH = 0.1                  # sideways leaves bow up in the middle (an arching leaf), share of length
STEM_CHANCE = 0.35               # share of leaves whose stem shows from the crown
STEM_SHOW = 0.45                 # stems show from this share of the way out from the crown
STEM_ARCH = 0.12                 # stems bow up by this share of their length
# rosette rings inside the outline ring: (share of the outline's reach the tips sit at, leaf size,
# tip spacing in leaf lengths, layer)
RINGS = [(0.72, 0.95, 0.7, 'mid'), (0.52, 0.9, 0.8, 'mid'), (0.32, 0.85, 0.9, 'front')]
RING_SWEEP = 0.12               # inner rings stay this far (radians) above the base line; the outline
#                                ring alone hangs over the pot's sides
LEAF_MARGIN = 0.5                # leaves may poke this far (px, before the outline stroke) past a silhouette
MASS_REACH = 0.86               # the dark body behind the leaves fills this share of the outline
MIN_LEAF = 0.6                   # shortest a leaf may be cut to by the rim, as a share of its size
FRONT_LOW = 0.0                 # front leaf tips sit this share of the way down to the base line
MID_FORWARD = 0.0
# A bush leaf's tone: mostly its height in the bush and how much it faces up, a little its side (the
# sun is high and only slightly left) and its layer, plus a small random step.
TONE_HEIGHT = 0.6
TONE_UP = 0.22
TONE_LEFT = 0.08
TONE_LAYER = {'back': -0.14, 'mid': 0.0, 'front': 0.06}
TONE_JITTER = 0.07
TONE_SPAN = 0.8                  # the score that maps to the brightest tone                # a middle leaf paints over flowers this many leaf lengths below its tip


@dataclass
class Shape:
    name: str
    d: str
    fill: str
    stroke: str = 'none'
    width: float = 0
    opacity: float = 1.0


def paint(fill):
    return 'url(#%s)' % fill if fill in GRADIENTS else fill


def svg_path(s):
    stroke = '' if s.stroke == 'none' else (' stroke="%s" stroke-width="%g" stroke-linejoin="round" '
                                            'stroke-linecap="round"' % (s.stroke, s.width))
    alpha = '' if s.opacity >= 1 else ' fill-opacity="%g"' % s.opacity
    return '<path id="%s" d="%s" fill="%s"%s%s/>' % (s.name, s.d, paint(s.fill), alpha, stroke)


def gradient_defs(names=None):
    return ''.join('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/>'
                   '<stop offset="1" stop-color="%s"/></linearGradient>' % (k, a, b)
                   for k, (a, b) in GRADIENTS.items() if names is None or k in names)


def poly(points, closed=True):
    return 'M' + ' L'.join('%.1f,%.1f' % p for p in points) + (' Z' if closed else '')


class Namer:
    def __init__(self, prefix):
        self.prefix, self.n = prefix, 0

    def __call__(self, what):
        self.n += 1
        return '%s %s %d' % (self.prefix, what, self.n)


# ---------------------------------------------------------------- leaves

def leaf(name, base, angle, length, tone='leaf-light', bend=None, rng=None, width=LEAF_WIDTH, stroke=LEAF_STROKE,
         gloss=None, shade=None):
    """A pointed oval leaf from base towards angle (radians, screen y down): the leaf, its shade half and
    either a gloss streak on the lit half or a light midrib vein (gloss None picks one at random)."""
    rng = rng or random.Random(0)
    bend = rng.uniform(-LEAF_BEND, LEAF_BEND) if bend is None else bend
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx
    half = width * length / 2
    n = 14

    def centre(t):
        b = bend * length * math.sin(math.pi * t)
        return base[0] + dx * length * t + nx * b, base[1] + dy * length * t + ny * b

    def w(t):
        return half * math.sin(math.pi * t ** 0.8) ** 0.85

    ts = [i / n for i in range(n + 1)]
    left = [(centre(t)[0] + nx * w(t), centre(t)[1] + ny * w(t)) for t in ts]
    right = [(centre(t)[0] - nx * w(t), centre(t)[1] - ny * w(t)) for t in ts]
    outline = left + right[::-1][1:-1]
    inset = stroke * 0.5 + 0.8
    if nx * LIGHT_2D[0] + ny * LIGHT_2D[1] < 0:
        nx, ny = -nx, -ny
        bend = -bend
    t_in = [t for t in ts if 0.06 < t < 0.94]
    shade_edge = [(centre(t)[0] - nx * max(w(t) - inset, 0), centre(t)[1] - ny * max(w(t) - inset, 0)) for t in t_in]
    rib = [centre(t) for t in t_in]
    shapes = [Shape(name, poly(outline), tone, LEAF_OUTLINE, stroke),
              Shape(name + ' shade', poly(rib + shade_edge[::-1]), shade or LEAF_SHADE[tone])]
    if gloss is None:
        gloss = rng.random() < GLOSS_CHANCE
    if length < 9:
        return shapes
    t_v = [t for t in ts if 0.1 <= t <= 0.82]
    vw = max(0.7, length * 0.016)
    a = [(centre(t)[0] + nx * vw * (1 - t), centre(t)[1] + ny * vw * (1 - t)) for t in t_v]
    b = [(centre(t)[0] - nx * vw * (1 - t), centre(t)[1] - ny * vw * (1 - t)) for t in t_v]
    shapes.append(Shape(name + ' vein', poly(a + b[::-1]), LEAF_VEIN[tone]))
    if gloss and LEAF_GLOSS[tone]:
        t_g = [t for t in ts if 0.22 <= t <= 0.66]
        outer = [(centre(t)[0] + nx * w(t) * 0.62, centre(t)[1] + ny * w(t) * 0.62) for t in t_g]
        inner = [(centre(t)[0] + nx * w(t) * (0.62 - 0.18 * math.sin(math.pi * (t - 0.22) / 0.44)),
                  centre(t)[1] + ny * w(t) * (0.62 - 0.18 * math.sin(math.pi * (t - 0.22) / 0.44))) for t in t_g]
        shapes.append(Shape(name + ' gloss', poly(outer + inner[::-1]), LEAF_GLOSS[tone]))
    return shapes


# ---------------------------------------------------------------- flowers

def flower(name, c, radius, rot=0.0, squash=1.0, white=False, stroke=STROKE, notch=PETAL_NOTCH):
    """Five-petal flower: petal outline, darker throat, petal lines, yellow centre. A smaller notch
    gives rounder, fuller petals."""
    petal_notch = notch

    def petals(r, notch=petal_notch, n=80):
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            k = abs(math.cos(2.5 * (a - rot)))
            rr = r * (1 - notch + notch * k ** 0.45)
            pts.append((c[0] + rr * math.cos(a), c[1] + squash * rr * math.sin(a)))
        return pts

    out = [Shape(name, poly(petals(radius)), 'petal-white' if white else 'petal',
                 WHITE_OUTLINE if white else PETAL_OUTLINE, stroke if not white else max(stroke - 1, 1.2))]
    throat = petals(radius * 0.5, 0.3)
    out.append(Shape(name + ' throat', poly([(x + radius * 0.06, y + radius * 0.05) for x, y in throat]),
                     WHITE_THROAT if white else PETAL_THROAT))
    lines = []
    for k in range(5):
        a = rot + (2 * k + 1) * math.pi / 5
        r0, r1 = radius * 0.3, radius * (1 - petal_notch) * 1.02
        lines.append('M%.1f,%.1f L%.1f,%.1f' % (c[0] + r0 * math.cos(a), c[1] + squash * r0 * math.sin(a),
                                                c[0] + r1 * math.cos(a), c[1] + squash * r1 * math.sin(a)))
    out.append(Shape(name + ' lines', ' '.join(lines), 'none', WHITE_OUTLINE if white else PETAL_LINE,
                     max(1.5, radius / 12)))
    cr = radius * (0.26 if not white else 0.32)
    out.append(Shape(name + ' centre', poly([(c[0] + cr * math.cos(a), c[1] + squash * cr * math.sin(a))
                                             for a in [2 * math.pi * i / 20 for i in range(20)]]),
                     'flower-centre', CENTRE_OUTLINE, 1.5 if radius < 14 else 2))
    if cr > 3:
        sx, sy, sr = c[0] - cr * 0.35, c[1] - squash * cr * 0.4, cr * 0.32
        out.append(Shape(name + ' centre shine', poly([(sx + sr * math.cos(a), sy + squash * sr * math.sin(a))
                                                       for a in [2 * math.pi * i / 12 for i in range(12)]]),
                         CENTRE_SHINE))
    return out


def rose(name, c, radius, rot=0.0, squash=1.0, stroke=STROKE):
    """An open semi-double rose tilted back so its face shows squash of its height: two
    whorls of five petals, the inner turned ROSE_WHORL_TURN into the gaps of the outer, the outer longer and
    opened out nearly flat, the inner shorter and standing up into a cup round a tuft of yellow stamens. A
    petal facing the viewer shows its deep pink inside, one facing away its paler outside, each with a pale
    rolled-back rim. Whorls paint from the outside in, each back to front, the stamens between the inner
    whorl's back and front petals so they sit down in the cup."""
    x, y = c
    lean = math.acos(max(-1.0, min(1.0, squash)))
    down = (0.0, math.cos(lean), math.sin(lean))         # the flower's face, down the screen
    axis = (0.0, -math.sin(lean), math.cos(lean))        # the way the flower faces: up and towards the viewer

    def at(v):
        return x + v[0], y + v[1]

    def petal(a, length, wide, rise):
        """A petal turned a round the axis, rise radians up from the face, rounded and widest near its tip,
        its sides curling in: its outline, whether it shows its inside, its depth, and the line of its
        rolled-back rim just inside its outer edge."""
        out_ = tuple(math.cos(a) * (1, 0, 0)[i] + math.sin(a) * down[i] for i in range(3))
        side = tuple(-math.sin(a) * (1, 0, 0)[i] + math.cos(a) * down[i] for i in range(3))
        along = tuple(math.cos(rise) * out_[i] + math.sin(rise) * axis[i] for i in range(3))
        normal = tuple(math.cos(rise) * axis[i] - math.sin(rise) * out_[i] for i in range(3))
        base = radius * ROSE_BASE
        steps = 14
        ts = [math.pi * i / steps for i in range(steps + 1)]
        edge = [((1 - math.cos(t)) / 2, math.sin(t) ** 0.8 * (0.55 + 0.45 * (1 - math.cos(t)) / 2)) for t in ts]
        loop = edge + [(u, -w) for u, w in edge[::-1][1:-1]]

        def point(u, w):
            return at(tuple(out_[i] * base + along[i] * length * u + side[i] * wide * w
                            + normal[i] * ROSE_CUP * wide * w * w for i in range(3)))

        rim = [point(0.5 + (u - 0.5) * 0.9, w * 0.86) for u, w in edge + [(u, -w) for u, w in edge[::-1][1:]]
               if u >= ROSE_RIM]
        depth = along[2] * length * 0.5 + out_[2] * base
        return [point(u, w) for u, w in loop], normal[2] > 0, depth, rim

    out = [Shape(name, poly([at(tuple(radius * 0.6 * (math.cos(t) * (1, 0, 0)[i] + math.sin(t) * down[i])
                                      for i in range(3))) for t in [2 * math.pi * i / 40 for i in range(40)]]),
                 ROSE_INSIDE_BASE, PETAL_OUTLINE, stroke)]

    def stamens():
        """A domed tuft of anthers raised a little off the face, bumpy round its edge, a pistil in its middle."""
        lift = tuple(axis[i] * radius * ROSE_STAMEN_LIFT for i in range(3))
        cx, cy = at(lift)
        sr = radius * ROSE_STAMENS
        tuft = []
        for i in range(ROSE_ANTHERS * 4):
            t = 2 * math.pi * i / (ROSE_ANTHERS * 4) + rot
            r_ = sr * (1 + 0.16 * abs(math.cos(ROSE_ANTHERS * (t - rot) / 2)) ** 0.5)
            tuft.append((cx + r_ * math.cos(t), cy + r_ * squash * math.sin(t)))
        pr = sr * 0.34
        return [Shape(name + ' stamens', poly(tuft), 'flower-centre', CENTRE_OUTLINE, max(1.2, stroke * 0.5)),
                Shape(name + ' pistil', poly([(cx + pr * math.cos(t), cy + 0.1 * sr + pr * squash * math.sin(t))
                                              for t in [2 * math.pi * i / 16 for i in range(16)]]), ROSE_PISTIL,
                      CENTRE_OUTLINE, max(1.0, stroke * 0.35)),
                Shape(name + ' stamen shine', poly([(cx - sr * 0.4 + sr * 0.26 * math.cos(t),
                                                     cy - sr * 0.4 * squash + sr * 0.18 * math.sin(t))
                                                    for t in [2 * math.pi * i / 12 for i in range(12)]]), CENTRE_SHINE)]

    rng = random.Random(round(rot, 3))
    down_turn = math.pi / 2 % (2 * math.pi / 5)
    rot = down_turn + ROSE_SYMMETRY * round((rot - down_turn) / ROSE_SYMMETRY)
    last = len(ROSE_WHORLS) - 1
    for w, (length, wide, rise, inside_fill) in enumerate(ROSE_WHORLS):
        turn = rot + w * ROSE_WHORL_TURN
        petals = []
        twist, grow, broaden, stand = ROSE_JITTER[w]
        shares = [[(i - 2) / 2 for i in range(5)] for _ in range(2)]
        for st in shares:
            rng.shuffle(st)
        for k in range(5):
            a = turn + 2 * math.pi * k / 5 + rng.uniform(-twist, twist)
            g = 1 + grow * shares[0][k]
            pts, inside, depth, rim = petal(a, length * radius * g, wide * radius * g * (1 + broaden * shares[1][k]),
                                            rise - stand * shares[0][k])
            front = w == last and math.sin(a) * math.sin(lean) > 0.05
            petals.append((front, depth, k, pts, inside_fill if inside else ROSE_PETAL, rim))
        line = max(1.2, stroke * 0.75)
        rim_width = max(1.0, wide * radius * ROSE_RIM_WIDTH)
        for front, depth, k, pts, fill, rim in sorted(petals):
            if front and not any(sh.name == name + ' stamens' for sh in out):
                out += stamens()
            out.append(Shape('%s petal %d %d' % (name, w + 1, k + 1), poly(pts), fill, PETAL_OUTLINE, line))
            if w > 0:
                # the cup's rolled rims stand off their petals, a pale band outlined dark either side
                out.append(Shape('%s rim edge %d %d' % (name, w + 1, k + 1), poly(rim, closed=False), 'none',
                                 PETAL_OUTLINE, rim_width + line))
            out.append(Shape('%s rim %d %d' % (name, w + 1, k + 1), poly(rim, closed=False), 'none', ROSE_RIM_LIGHT,
                             rim_width))
    if not any(sh.name == name + ' stamens' for sh in out):
        out += stamens()
    return out


def bud(name, base, angle, length, stroke=STROKE):
    """A closed pink bud on a short stem, with a green calyx cupping its base."""
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx
    start = (base[0] + dx * length * 0.35, base[1] + dy * length * 0.35)

    def pod(t0, t1, width, steps=12):
        side = []
        for i in range(steps + 1):
            t = t0 + (t1 - t0) * i / steps
            w = width * length * math.sin(math.pi * (i / steps) ** 0.7) ** 0.7
            side.append((t, w))
        pts = [(start[0] + dx * length * t + nx * w, start[1] + dy * length * t + ny * w) for t, w in side]
        pts += [(start[0] + dx * length * t - nx * w, start[1] + dy * length * t - ny * w) for t, w in side[::-1][1:-1]]
        return pts

    stem = [(base[0], base[1]), (start[0] + dx * length * 0.1, start[1] + dy * length * 0.1)]
    return [Shape(name + ' stem', poly(stem, closed=False), 'none', STEM, max(2.0, length / 8)),
            Shape(name, poly(pod(0.0, 0.62, 0.24)), 'petal', PETAL_OUTLINE, stroke - 1),
            Shape(name + ' calyx', poly(pod(-0.02, 0.26, 0.22)), 'leaf-light', LEAF_OUTLINE, stroke - 1)]


def twig(name, base, angle, length, width):
    """A straight piece of woody stem from base along angle: an outline and its core."""
    line = poly([base, (base[0] + math.cos(angle) * length, base[1] + math.sin(angle) * length)], closed=False)
    return [Shape(name, line, 'none', LEAF_OUTLINE, width + 2.5), Shape(name + ' core', line, 'none', TWIG, width)]


# ---------------------------------------------------------------- vines

def vine(name, start, direction, length, leaf_size, seed=0, droop=1.0, every=3):
    """A stem hanging from start (a pot rim), heading sideways along direction (-1 / 1) then down. The same
    seed draws the two directions as mirror images of each other."""
    rng = random.Random(seed)
    n = 16
    pts = []
    for i in range(n + 1):
        t = i / n
        x = start[0] + direction * length * (0.35 * t + 0.05 * math.sin(3 * t + seed))
        y = start[1] + length * droop * (t ** 1.4) - length * 0.12 * math.sin(math.pi * t) * (1 - t)
        pts.append((x, y))
    shapes = [Shape(name + ' stem', poly(pts, closed=False), 'none', STEM, max(2.0, leaf_size / 9))]
    # paired leaves at each node, splayed off the stem so it shows between them, smaller towards the tip
    for i in range(every, n, every):
        x, y = pts[i]
        px, py = pts[i - 1]
        along = math.atan2(y - py, x - px)
        size = leaf_size * (1.0 - VINE_TAPER * i / n) * rng.uniform(0.85, 1.0)
        for side in (-1, 1):
            a = along - direction * side * rng.uniform(*VINE_SPLAY)
            tone = rng.choice(['leaf-dark', 'leaf-back'])
            shapes += leaf('%s leaf %d%s' % (name, i, 'ab'[side > 0]), (x, y), a, size, tone,
                           bend=-direction * rng.uniform(-LEAF_BEND, LEAF_BEND), rng=rng)
    x, y = pts[-1]
    px, py = pts[-2]
    shapes += leaf('%s leaf tip' % name, (x, y), math.atan2(y - py, x - px), leaf_size * (1.0 - VINE_TAPER) * 1.1,
                   'leaf-dark', bend=-direction * rng.uniform(-LEAF_BEND, LEAF_BEND), rng=rng)
    return shapes


# ---------------------------------------------------------------- bushes

def bush_mass(name, centre, width, height, seed=0, bumps=9, x_limit=None):
    """The dark-green body showing between the leaves: a lumpy dome whose base corners round off into a
    shallow belly, so no hard corner shows where the leaves stop. x_limit (lo, hi) squeezes it sideways
    to stay out of a keep-out band."""
    rng = random.Random(seed)
    cx, cy = centre
    lo, hi = x_limit if x_limit else (-1e9, 1e9)
    left, right = max(cx - width / 2, lo), min(cx + width / 2, hi)
    mx, half = (left + right) / 2, (right - left) / 2
    pts = []
    n = bumps * 8
    for i in range(n + 1):
        a = math.pi + math.pi * i / n
        lump = 1 + 0.08 * abs(math.sin(bumps * math.pi * i / n + rng.uniform(-0.2, 0.2)))
        pts.append((mx + half * math.cos(a) * lump, cy + height * math.sin(a) * lump))
    for i in range(1, 16):
        a = math.pi * i / 16
        pts.append((mx + half * 0.96 * math.cos(a), cy + height * 0.1 * math.sin(a)))
    return Shape(name, poly(pts), 'bush-mass')


def reach(outline, origin, phi):
    """Distance from origin to the far side of the closed outline along screen direction phi (y up)."""
    dx, dy = math.cos(phi), -math.sin(phi)
    best = 0.0
    n = len(outline)
    for i in range(n):
        (x0, y0), (x1, y1) = outline[i], outline[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        wx, wy = x0 - origin[0], y0 - origin[1]
        t = (wx * ey - wy * ex) / den
        s = (wx * dy - wy * dx) / den
        if t > 0 and 0 <= s <= 1:
            best = max(best, t)
    return best


def droop_angle(radial, rng):
    """A leaf's axis: the direction it grows out from the crown, turned down by gravity the more it lies
    sideways (an upright leaf stands straight, a sideways one arches over and down)."""
    off = math.atan2(math.sin(radial + math.pi / 2), math.cos(radial + math.pi / 2))   # 0 = straight up
    radial = -math.pi / 2 + max(-math.pi, min(math.pi, off * FAN))
    side = math.cos(radial)
    sideways = abs(side) ** 1.5
    sign = 1 if side >= 0 else -1
    lift = max(0.0, -math.sin(radial))           # 1 for straight up
    return radial + sign * (DROOP * sideways * (0.5 + 0.5 * lift) + rng.uniform(-LEAF_JITTER, LEAF_JITTER))


def stem_path(start, end, sag):
    """A stem from start to end, arching up by sag (a share of its length) in the middle."""
    (x0, y0), (x1, y1) = start, end
    L = math.hypot(x1 - x0, y1 - y0)
    ctrl = ((x0 + x1) / 2, (y0 + y1) / 2 - sag * L)
    pts = [((1 - t) ** 2 * x0 + 2 * t * (1 - t) * ctrl[0] + t * t * x1,
            (1 - t) ** 2 * y0 + 2 * t * (1 - t) * ctrl[1] + t * t * y1) for t in [i / 10 for i in range(11)]]
    return poly(pts, closed=False)


def bush(name, centre, width, height, density=1.0, seed=0, leaf_size=36.0, flower_size=17.0,
         flowers=None, whites=None, spill=0.15, mass=True, flower_band=(0.2, 0.92), keep_out=None,
         flower_phi=None, variety=0.0, white_size=WHITE_FLOWER_SIZE, whites_on_top=False, two_tone=False,
         stroke=STROKE, front_hang=0, buds=3, silhouette=None, sweep=(-0.12, math.pi + 0.12), mass_floor=None,
         mass_base=None, rings=None, tone_bias=0.0, flower_spots=None, leaves=True):
    """A flowering plant grown from a crown at centre (the middle of its base, screen px).

    Every leaf grows out of the crown: a stem runs from a crown point (spread along the base) to the
    leaf's base and the leaf points on outwards, its axis the direction away from the crown turned down
    by gravity the more it lies sideways, so upper leaves stand up and side leaves arch over and droop.
    Leaves come in three depths, painted back to front: a back layer (darker) whose tips make the
    outline, a middle layer among the flowers, and a few bright front leaves low down over the base.
    Flowers sit on stems at the ends of the middle layer.

    width x height is the dome the plant fills, or silhouette (a closed screen outline) replaces it over
    the directions in sweep (radians, 0 = right, pi/2 = up). density scales the leaf counts; flowers /
    whites override the flower counts; spill scales leaves hanging over the base line (a pot rim);
    flower_band is the range of dome radius (0 centre, 1 edge) flowers sit in; keep_out is an optional
    (x0, x1) screen band left empty (for a post running through the bush); front_hang leaves hang over
    the front of the base. mass_floor keeps the dark body above that screen y (a pot's rim); mass_base
    (a screen polyline, left to right) instead closes the body along it, e.g. a rim's front edge.
    tone_bias shifts every leaf's tone score (negative = a darker, richer bush). flower_spots, a list of
    (x, y, radius, kind) with kind 'pink', 'white' or 'rose', places the flowers instead of scattering them.
    leaves=False leaves out the leaves and their stems, for a plant whose leaves are library pieces: the
    mass, flowers and buds are where and named as they would be among them.
    """
    rng = random.Random(seed)
    nm = Namer(name)
    potted = mass_floor is not None or mass_base is not None    # growing out of a pot's soil
    leaf_size *= LEAF_GROW
    density *= LEAF_THIN
    cx, cy = centre
    if silhouette is not None:
        xs = [p[0] for p in silhouette]
        width, height = max(xs) - min(xs), cy - min(p[1] for p in silhouette)
    rx, ry = width / 2, height
    dome_area = math.pi / 2 * rx * ry
    leaf_area = 0.36 * leaf_size * leaf_size * LEAF_WIDTH / 0.46
    n_ring = int(math.pi * (rx + ry) / 2 / (leaf_size * 0.68) * density) + 3
    n_spill = int(width / leaf_size * 1.4 * spill / 0.15 * density) if spill > 0 else 0
    n_flowers = flowers if flowers is not None else max(2, int(dome_area / (flower_size * flower_size) * 0.12))
    n_white = whites if whites is not None else max(1, round(n_flowers / 3))
    n_flowers = int(round(n_flowers * FLOWER_COUNT))
    n_white = int(round(n_white * FLOWER_COUNT)) + 1
    flower_size *= FLOWER_SCALE

    def blocked(x, margin=0.0):
        return keep_out is not None and keep_out[0] - margin < x < keep_out[1] + margin

    def dome(phi, rho):
        if silhouette is not None:
            R = reach(silhouette, (cx, cy), phi)
            return cx + math.cos(phi) * R * rho, cy - math.sin(phi) * R * rho
        return cx + math.cos(phi) * rx * rho, cy - math.sin(phi) * ry * rho

    def inside(x, y, margin=0.0):
        """Whether (x, y) lies margin px within the silhouette (always, for a plain dome)."""
        return silhouette is None or outside_by(x, y) <= -margin

    def outside_by(x, y):
        """Distance from (x, y) to the silhouette's edge, negative inside."""
        n = len(silhouette)
        hit, best = False, 1e9
        for i in range(n):
            (x0, y0), (x1, y1) = silhouette[i], silhouette[(i + 1) % n]
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                hit = not hit
            ex, ey = x1 - x0, y1 - y0
            t = max(0.0, min(1.0, ((x - x0) * ex + (y - y0) * ey) / (ex * ex + ey * ey or 1)))
            best = min(best, math.hypot(x - x0 - t * ex, y - y0 - t * ey))
        return -best if hit else best

    def overflow(bx, by, ang, size):
        """How far (px) a leaf's edges poke past the silhouette."""
        dx, dy = math.cos(ang), math.sin(ang)
        half = LEAF_WIDTH * size / 2
        worst = -1e9
        for t in (0.15, 0.3, 0.5, 0.7, 0.9):
            w = half * math.sin(math.pi * t ** 0.8) ** 0.85
            cx_, cy_ = bx + dx * size * t, by + dy * size * t
            for s in (-1, 1):
                worst = max(worst, outside_by(cx_ - dy * w * s, cy_ + dx * w * s))
        return worst

    def crown(x):
        """The crown point a shoot ending above screen x grows from: crowns spread along the base, so a
        wide plant fans from several clumps rather than one point."""
        off = max(-rx * CROWN_SPREAD, min(rx * CROWN_SPREAD, (x - cx) * CROWN_SPREAD))
        return cx + off, cy + ry * CROWN_DROP

    top_y = cy - height
    bottom_y = max(p[1] for p in silhouette) if silhouette is not None else cy
    tone_rng = random.Random(seed + 1)
    var_rng = random.Random(seed + 2)

    def leaf_tone(bx, by, ang, size, layer):
        mx, my = bx + math.cos(ang) * size * 0.5, by + math.sin(ang) * size * 0.5
        h = max(0.0, min(1.0, (bottom_y - my) / max(1.0, bottom_y - top_y)))
        up = max(0.0, -math.sin(ang))
        left = max(-1.0, min(1.0, (cx - mx) / max(1.0, rx)))
        score = (TONE_HEIGHT * h + TONE_UP * up + TONE_LEFT * left + TONE_LAYER[layer] + tone_bias
                 + tone_rng.uniform(-TONE_JITTER, TONE_JITTER))
        return 'leaf-%d' % (1 + round(max(0.0, min(1.0, score / TONE_SPAN)) * (len(LEAF_LEVELS) - 1)))

    items = []
    tones = {'back': ['leaf-back', 'leaf-back', 'leaf-dark'], 'mid': ['leaf-dark', 'leaf-light', 'leaf-light'],
             'front': ['leaf-light']}

    def grow(layer, key, tip, size, tone=None, ang=None):
        """A leaf whose tip is at tip, grown out from the crown with its stem."""
        o = crown(tip[0])
        if potted and tip[1] > cy - leaf_size * 0.5:
            # a leaf ending at or over the rim grows from the soil just above it and lies out over the rim
            o = (cx + (o[0] - cx) * 0.7, cy - leaf_size * 0.35)
        radial = math.atan2(tip[1] - o[1], tip[0] - o[0])
        if ang is None:
            ang = droop_angle(radial, rng)
        reach_px = math.dist(o, tip)
        size = min(size, reach_px * 0.95)
        bx, by = tip[0] - math.cos(ang) * size * 0.97, tip[1] - math.sin(ang) * size * 0.97
        floor = cy - 2
        if potted and by > floor and tip[1] < floor:
            # leaves come up out of the soil: a base below the rim slides up the axis to it, and a leaf
            # left too short turns to grow from the rim straight to its tip
            t = (by - floor) / (by - tip[1])
            if (1 - t) * size >= size * MIN_LEAF:
                bx, by, size = bx + (tip[0] - bx) * t, floor, size * (1 - t)
            else:
                bx, by = o[0], floor
                ang = math.atan2(tip[1] - by, tip[0] - bx)
                size = min(size, math.dist((bx, by), tip) / 0.97)
                bx, by = tip[0] - math.cos(ang) * size * 0.97, tip[1] - math.sin(ang) * size * 0.97
        if silhouette is not None and overflow(bx, by, ang, size) > LEAF_MARGIN:
            # a leaf poking past the outline turns towards the line from its crown, then shrinks; an
            # outline leaf that never fits takes the try that pokes out least
            best = None
            for a2 in (ang, (ang + radial) / 2, radial, radial + (radial - ang) / 2):
                for k in (1.0, 0.85, 0.7, 0.55):
                    s2 = size * k
                    b2 = (tip[0] - math.cos(a2) * s2 * 0.97, tip[1] - math.sin(a2) * s2 * 0.97)
                    over = overflow(b2[0], b2[1], a2, s2)
                    if best is None or over < best[0] - 0.5:
                        best = (over, a2, s2, b2)
                    if over <= LEAF_MARGIN:
                        break
                if best[0] <= LEAF_MARGIN:
                    break
            if best[0] > LEAF_MARGIN and layer != 'back':
                return
            _, ang, size, (bx, by) = best
        if blocked(bx, size * 0.15) or blocked(bx + math.cos(ang) * size * 0.6, 0.0):
            return
        side = math.cos(radial)
        bend = -(1 if side >= 0 else -1) * abs(side) * LEAF_ARCH + rng.uniform(-0.04, 0.04)
        stem = None
        if layer != 'back' and math.dist(o, (bx, by)) > size * 0.25 and rng.random() < STEM_CHANCE:
            # the stem shows from STEM_SHOW of the way out, and never below the base line (the pot's rim)
            f = STEM_SHOW
            if o[1] > cy - 2 and by < cy - 2:
                f = max(f, (o[1] - (cy - 2)) / (o[1] - by))
            if by < cy - 2:
                stem = ((o[0] + (bx - o[0]) * f, o[1] + (by - o[1]) * f), (bx, by))
        items.append((key, 'leaf', (bx, by, ang, size, tone or rng.choice(tones[layer]), bend, stem, layer)))

    # back layer: tips evenly spaced along the outline (by length, so far-reaching lobes are not sparse),
    # with the outline's own corners (its measured lobes) each taking the nearest tip
    tips = []
    if silhouette is not None:
        edge = [dome(p, 1.0) for p in [sweep[0] + (sweep[1] - sweep[0]) * i / 400 for i in range(401)]]
        run = [0.0]
        for a, b in zip(edge, edge[1:]):
            run.append(run[-1] + math.dist(a, b))
        n_ring = int(run[-1] / (leaf_size * 0.62) * density) + 3
        for i in range(n_ring):
            at = run[-1] * (i + rng.uniform(0.35, 0.65)) / n_ring
            k = min(range(len(run)), key=lambda j: abs(run[j] - at))
            tips.append(edge[k])
        corners = [p for p in silhouette
                   if (potted and p[1] > cy + 2) or any(sweep[0] <= math.atan2(cy - p[1], p[0] - cx) + turn <= sweep[1]
                          for turn in (-2 * math.pi, 0, 2 * math.pi))]
        pairs = sorted((math.dist(t, p), j, k) for j, t in enumerate(tips) for k, p in enumerate(corners))
        used_tips, used_corners = set(), set()
        for d, j, k in pairs:
            if d < leaf_size * 0.8 and j not in used_tips and k not in used_corners:
                tips[j] = corners[k]
                used_tips.add(j)
                used_corners.add(k)
        tips += [p for k, p in enumerate(corners) if k not in used_corners]
    else:
        for i in range(n_ring):
            phi = sweep[0] + (sweep[1] - sweep[0]) * (i + rng.uniform(0.2, 0.8)) / n_ring
            tips.append(dome(phi, rng.uniform(0.95, 1.0)))
    for tip in tips:
        size = leaf_size * rng.uniform(0.9, LEAF_SIZE_RANGE[1])
        o = crown(tip[0])
        radial = math.atan2(tip[1] - o[1], tip[0] - o[0])
        ang = droop_angle(radial, rng)
        # the leaf's outer edge, not just its tip, should reach the outline: aim the axis so the
        # leaf's far side stays inside
        grow('back', tip[1], tip, size, ang=ang)

    # inner rings: rosettes of leaves round the crown, each ring's tips on a smaller copy of the outline
    # and offset half a step from the ring outside it, so every leaf shows between the ones behind it;
    # inner rings paint in front (they are nearer the viewer's side of the pot)
    lo, hi = (max(sweep[0], RING_SWEEP), min(sweep[1], math.pi - RING_SWEEP)) if potted else sweep
    for ring_i, (rho, size_k, spacing, layer) in enumerate(RINGS if rings is None else rings):
        edge = [dome(p, rho) for p in [lo + (hi - lo) * i / 200 for i in range(201)]]
        run = [0.0]
        for a_, b_ in zip(edge, edge[1:]):
            run.append(run[-1] + math.dist(a_, b_))
        n = max(2, int(round(run[-1] / (leaf_size * spacing) * density)))
        for i in range(n):
            at = run[-1] * (i + 0.5 + (0.5 if ring_i % 2 == 0 else 0.0) + rng.uniform(-0.2, 0.2)) / n
            at = min(max(at, 0.0), run[-1])
            k = min(range(len(run)), key=lambda j: abs(run[j] - at))
            tip = edge[k]
            if layer == 'front':
                tip = (tip[0], tip[1] + (cy - tip[1]) * FRONT_LOW)
            base_key = 1e5 if layer == 'mid' else 2e5
            grow(layer, base_key + tip[1] + size_k * leaf_size * MID_FORWARD, tip,
                 leaf_size * size_k * rng.uniform(0.9, 1.08))

    for _ in range(n_spill):
        s = rng.choice([-1, 1]) * rng.uniform(0.45, 1.0)
        tip = (cx + s * rx * 0.95, cy + leaf_size * rng.uniform(0.3, 0.6))
        grow('front', 2.5e5 + tip[1], tip, leaf_size * rng.uniform(0.85, 1.1))
    if keep_out is not None:
        # leaves along the edge of the keep-out band lean into it, so the bush overlaps the post's edge
        side = -1 if keep_out[0] > cx else 1
        edge_x = keep_out[0] if side < 0 else keep_out[1]
        if cx - rx < edge_x < cx + rx:
            top = math.sqrt(max(0.0, 1 - ((edge_x - cx) / rx) ** 2)) * ry
            for i, (f, tilt, size) in enumerate(((0.12, 0.75, 0.9), (0.38, -0.35, 1.05), (0.62, 0.3, 0.8),
                                                  (0.85, -0.85, 0.95))):
                bx = edge_x + side * leaf_size * rng.uniform(0.3, 0.6)
                by = cy - top * f * 0.85 + rng.uniform(-4, 4)
                ang = (0 if side < 0 else math.pi) - side * (tilt + rng.uniform(-0.15, 0.15))
                items.append((1.5e5 + rng.uniform(-50, 50), 'leaf', (bx, by, ang, leaf_size * size,
                                                    rng.choice(['leaf-light', 'leaf-dark']), None, None, 'mid')))
    for i in range(front_hang):
        u = (i + 0.5) / front_hang * 1.2 - 0.6 + rng.uniform(-0.08, 0.08)
        size = leaf_size * rng.uniform(0.85, 1.0)
        ang = math.pi / 2 - u * 0.6 + rng.uniform(-0.2, 0.2)
        tip = (cx + u * rx + math.cos(ang) * size, cy - ry * 0.04 + math.sin(ang) * size)
        grow('front', 3e5 + i, tip, size, ang=ang)

    # flowers on stems among the middle leaves
    placed = []
    tries = 0
    total = n_flowers + n_white
    since = 0                  # tries since the last flower went in: a flower that will not fit shrinks
    if flower_spots is not None:
        total = 0
        for fx, fy, r, kind in flower_spots:
            items.append((1.5e5 + fy, 'flower', (fx, fy, r, kind, rng.uniform(0, 2 * math.pi),
                                                 rng.uniform(*FLOWER_SQUASH), crown(fx))))
    while len(placed) < total and tries < 5000:
        tries += 1
        since += 1
        white = len(placed) >= n_flowers
        tier = FLOWER_SIZES[min(len(FLOWER_SIZES) - 1, len(placed) * len(FLOWER_SIZES) // max(1, n_flowers))]
        shrink = max(FLOWER_MIN_SHRINK, FLOWER_SHRINK ** (since // FLOWER_SHRINK_EVERY))
        r = flower_size * (white_size if white else tier) * shrink * rng.uniform(1 - FLOWER_JITTER, 1 + FLOWER_JITTER)
        phi = rng.uniform(0.12 * math.pi, 0.88 * math.pi) if potted else rng.uniform(sweep[0] + 0.3, sweep[1] - 0.3)
        if flower_phi:
            phi = rng.uniform(*flower_phi)
        rho = rng.uniform(*flower_band)
        fx, fy = dome(phi, rho)
        fx, fy = fx - math.cos(phi) * r * 0.6, fy + math.sin(phi) * r * 0.6
        if blocked(fx, r) or not inside(fx, fy, r * 0.9):
            continue
        gap = 0.85 if not white else 0.7
        if any(math.hypot(fx - x, fy - y) < (r + rr) * gap for x, y, rr, _ in placed):
            continue
        placed.append((fx, fy, r, white))
        since = 0
    for fx, fy, r, white in placed:
        o = crown(fx)
        items.append(((4e5 if white and whites_on_top else 1.5e5) + fy, 'flower', (fx, fy, r, white, rng.uniform(0, 2 * math.pi),
                                                              rng.uniform(*FLOWER_SQUASH), o)))

    for _ in range(buds):
        phi = rng.uniform(0.3, math.pi - 0.3)
        bx, by = dome(phi, rng.uniform(0.75, 0.95))
        if not blocked(bx, flower_size) and inside(bx, by, flower_size * 0.75):
            o = crown(bx)
            ang = droop_angle(math.atan2(by - o[1], bx - o[0]), rng)
            items.append((1.5e5 + by, 'bud', ((bx, by), ang, flower_size * 0.75)))

    items.sort(key=lambda it: it[0])
    shapes = []
    if mass:
        limit = None
        if keep_out is not None:
            pad = leaf_size * 0.3
            limit = (-1e9, keep_out[0] - pad) if keep_out[0] > cx else (keep_out[1] + pad, 1e9)
        if silhouette is not None:
            m0, m1 = sweep if sweep[1] - sweep[0] < 1.5 * math.pi else (0.0, 2 * math.pi)
            body = [dome(m0 + (m1 - m0) * i / 60, MASS_REACH) for i in range(61)]
            if limit is not None:
                body = [(min(max(x, limit[0]), limit[1]), y) for x, y in body]
            if mass_floor is not None:
                body = [(x, min(y, mass_floor)) for x, y in body]
            bottom = [(cx, cy)] if mass_base is None else [p for p in mass_base if body[-1][0] <= p[0] <= body[0][0]]
            shapes.append(Shape(nm('mass'), poly(body + bottom), 'bush-mass'))
        else:
            shapes.append(bush_mass(nm('mass'), (cx, cy), width * 0.86, height * 0.8, seed, x_limit=limit))
    for _, kind, data in items:
        if kind == 'leaf' and not leaves:
            if data[6] is not None:
                nm('stem')
            nm('leaf')
        elif kind == 'leaf':
            bx, by, ang, size, tone, bend, stem, layer = data
            tone = leaf_tone(bx, by, ang, size, layer)
            if two_tone:     # a two-tone leaf's lit half stays bright enough to part from the dark mass
                tone = 'leaf-%d' % max(TWO_TONE_FLOOR, int(tone.split('-')[1]))
            width = LEAF_WIDTH
            if variety:
                # mixed leaf shapes, sizes, angles and tones, so neighbours never repeat
                pick = var_rng.random()
                # (the back layer's tips make the fitted outline, so those leaves keep their reach and axis)
                outline_leaf = layer == 'back'
                if pick < VARIETY_BROAD:
                    width = LEAF_WIDTH * 1.3
                    size *= 1.0 if outline_leaf else 0.92
                elif pick < VARIETY_BROAD + VARIETY_NARROW:
                    width = LEAF_WIDTH * 0.68
                    size *= 1.0 if outline_leaf else 1.12
                else:
                    width = LEAF_WIDTH * var_rng.uniform(0.9, 1.1)
                if not outline_leaf:
                    size *= var_rng.uniform(1 - 0.22 * variety, 1 + 0.22 * variety)
                    ang += var_rng.uniform(-0.3, 0.3) * variety
                if var_rng.random() < 0.6 * variety:
                    level = int(tone.split('-')[1]) + var_rng.choice((-1, 1))
                    tone = 'leaf-%d' % max(1, min(len(LEAF_LEVELS), level))
            if stem is not None:
                shapes.append(Shape(nm('stem'), stem_path(stem[0], stem[1], STEM_ARCH), 'none',
                                    STEM_BACK if layer == 'back' else STEM, max(2.0, size / 14)))
            shapes += leaf(nm('leaf'), (bx, by), ang, size, tone, bend=bend, rng=rng, width=width,
                           shade=LEAF_SHADE_DEEP[tone] if two_tone else None,
                           gloss=tone == 'leaf-5' or (tone == 'leaf-4' and tone_rng.random() < 0.5))
        elif kind == 'bud':
            shapes += bud(nm('bud'), *data, stroke=stroke)
        else:
            fx, fy, r, white, rot, squash, o = data
            sx, sy = fx + (o[0] - fx) * 0.25, min(fy + (o[1] - fy) * 0.25, max(fy, cy - 2))
            sx = fx + (o[0] - fx) * (sy - fy) / (o[1] - fy) if o[1] != fy else sx
            shapes.append(Shape(nm('flower stem'), stem_path((sx, sy), (fx, fy), 0.05), 'none', STEM,
                                max(2.0, r / 6)))
            if white == 'rose':
                shapes += rose(nm('rose'), (fx, fy), r, rot, squash, stroke=min(stroke, max(1.5, r / 4.5)))
            else:
                white = white is True or white == 'white'
                shapes += flower(nm('white flower' if white else 'flower'), (fx, fy), r, rot, squash, white,
                                 stroke=min(stroke, max(1.5, r / 4.5)))
    return shapes


# ---------------------------------------------------------------- mound bush
MOUND_LEAF_WIDTH = 0.52          # a mound's leaves are glossy and pointed, about 2:1 like the reference's
MOUND_SPACING = 0.5              # interior leaf bases sit this many leaf lengths apart
MOUND_EDGE_SPACING = 0.55        # outline leaf tips sit this many leaf lengths apart along the outline
FLOWERS_LAST = 1e6                # added to a flower's paint key, so its order among flowers (and name) holds
MOUND_MASS_INSET = 0.45          # the dark body stops this many leaf lengths inside the outline, so the
#                                  outline leaves' tips make the silhouette
MOUND_TONE_JITTER = 0.2          # neighbouring leaves differ more than in a pot's bush: a close-up shrub
MOUND_HANG_EVERY = 1.0           # branches spilling over a pot's rim start this many leaf lengths apart
MOUND_HANG = (0.45, 0.85)        # and grow down over it and out towards the viewer this much
MOUND_HANG_SIZE = (0.9, 1.0)     # with leaves this share of the bush's size
MOUND_TOP_SIZE = 0.62            # a mound's leaves at its top are this share of the size of those at its foot,
#                                  nearer the viewer
MOUND_SHOW = 0.9                 # a clipped shrub's surface leaves face out, so show this share of their length
MOUND_YOUNG_SIZE = (0.9, 0.95)   # and its young leaves are nearly full grown
MOUND_FAN_FOOT = 0.75            # a clipped mound's leaves fan out from a point this share of the way down it,
#                                  so only its lowest leaves droop over the rim
MOUND_FAN = (0.2, 0.6)           # leaves from this share of the way out from that point to this share
MOUND_FAN_KEEP = 0.35            # turn to point out from it, keeping this share of their turn away from that
MOUND_FAN_MAX = math.radians(40) # and at most this much
MOUND_CLIP_MIN = 0.6             # a leaf clipped back to the outline shorter than this share of its size is cut off,
#                                  so the outline is made of whole leaves just touching it
MOUND_NOTCH = 0.3                # a mound's five-petal flowers are round and full
MOUND_WHITE_NOTCH = 0.38         # its daisies keep clearly parted petals
MOUND_LEAF_STROKE = 3.0          # close up, the leaves carry the scene's full outline
BRANCH_SPACING = 1.35            # a mound's inside branches start this many leaf lengths apart
BRANCH_EDGE_SPACING = 1.2        # its outline branches reach the outline this many leaf lengths apart
BRANCH_EDGE_CLEAR = 0.8          # inside branches start this many leaf lengths in from the outline
BRANCH_FLOWER_CLEAR = 1.0        # and this many from a flower, whose own branch grows there
BRANCH_SHOOTS = (2, 3)           # shoots growing from each branch point
BRANCH_SPLIT = (math.radians(22), math.radians(35))  # each shoot turns this far off its branch
BRANCH_LIFT = 0.5                # a branch turns up towards the light by this much before it splits
BRANCH_STEP = 0.1               # a shoot starts this many leaf lengths out from its branch point
SHOOT_LEAVES = (5, 7)
SHOOT_TURN = math.radians(137.5) # each leaf turns this far round the stem from the one below it
SHOOT_GAP = (0.45, 0.22)          # leaf lengths between leaves at a shoot's base and at its tip, so the
#                                  stem shows between them
SHOOT_OFF = (math.radians(30), math.radians(55))     # a leaf's angle off the stem, at the base and tip
SHOOT_COLLAR_OFF = (math.radians(35), math.radians(80))  # the same on a flowering shoot, whose last leaves
#                                  open wide into a collar round the flower
SHOOT_MOSAIC = 0.9               # how far a sideways shoot's leaves turn flat towards the light
SHOOT_YOUNG = 2                  # the youngest leaves at the tip, smaller and lighter
SHOOT_YOUNG_SIZE = (0.58, 0.64)
SHOOT_SHOW = 0.55                # a leaf turns to the light, so shows at least this share of its length
SHOOT_TWIST = math.radians(20)   # each leaf twists on its stalk up to this far either way, so no two lie alike
TWIG_WIDTH = (3.5, 2.0)          # px across a branch's stem and a shoot's stem at its tip


@dataclass
class Spray:
    """Leaves growing from one point: a branch (holding its shoots) or a shoot (holding its leaves).
    origin is that point, angle the screen direction it grows in (radians, screen y down), length how far
    it reaches on screen, facing how much it points at the viewer (1 straight at them, 0 sideways);
    shapes in paint order."""
    name: str
    origin: tuple
    angle: float
    length: float
    shapes: list
    facing: float = 0.0


@dataclass
class ShootLeaf:
    """One leaf of a shoot as seen on screen: base, angle (radians, screen y down) and drawn length;
    size its real length, off its angle off the stem, node its place up the stem from 0, depth how near the
    viewer its middle is."""
    base: tuple
    angle: float
    length: float
    size: float
    off: float
    node: int
    young: bool
    depth: float


def _unit(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _around(d):
    """Two unit vectors at right angles to d and to each other."""
    e1 = _unit(_cross(d, (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (0.0, 1.0, 0.0)))
    return e1, _cross(d, e1)


def _turn(d, off, e):
    """d turned off radians away from itself towards e, a unit vector at right angles to it."""
    return _unit(tuple(d[i] * math.cos(off) + e[i] * math.sin(off) for i in range(3)))


def _round(d, phi):
    """The unit vector at right angles to d, phi radians round it."""
    e1, e2 = _around(d)
    return tuple(e1[i] * math.cos(phi) + e2[i] * math.sin(phi) for i in range(3))


def _flat(d):
    """The unit vector at right angles to d in the screen plane, and how far d is from pointing at the
    viewer (0 straight at them, 1 sideways)."""
    p = _cross(d, (0.0, 0.0, 1.0))
    m = math.hypot(p[0], p[1])
    return (None if m < 1e-6 else (p[0] / m, p[1] / m, 0.0)), m


def _mosaic(d, e, side):
    """e turned round d towards side (+1 or -1) of the screen plane, the more so the more sideways d points:
    leaves and shoots turn on their stalks to lie flat towards the light."""
    p, m = _flat(d)
    if p is None:
        return e
    w = SHOOT_MOSAIC * math.sqrt(m)
    v = tuple((1 - w) * e[i] + w * side * p[i] for i in range(3))
    dot = sum(v[i] * d[i] for i in range(3))
    return _unit(tuple(v[i] - dot * d[i] for i in range(3)))


def shoot_leaves(origin, direction, size, rng, flowering=False, young_size=SHOOT_YOUNG_SIZE):
    """A camellia shoot from origin along direction (x right, y down, z towards the viewer), its leaves
    turning SHOOT_TURN round the stem one above the other, closer together and opening wider towards the
    tip, the youngest smaller. Pointing at the viewer it is a rosette; pointing sideways, its leaves lie
    flat on alternate sides of the stem. A flowering shoot has no young leaves: its last ones open wide
    into a collar round the flower at its tip. Returned far to near, the order they paint in."""
    d = _unit(direction)
    n = rng.randint(*SHOOT_LEAVES)
    phi = rng.uniform(0, 2 * math.pi)
    side = rng.choice((-1, 1))
    out, s = [], 0.0
    for k in range(n):
        t = k / (n - 1)
        young = not flowering and k >= n - SHOOT_YOUNG
        lo, hi = SHOOT_COLLAR_OFF if flowering else SHOOT_OFF
        off = lo + (hi - lo) * t ** 1.5 + rng.uniform(-0.08, 0.08)
        ls = size * (rng.uniform(*young_size) if young else rng.uniform(0.92, 1.05))
        e = _mosaic(d, _round(d, phi + k * SHOOT_TURN + rng.uniform(-0.2, 0.2)), side if k % 2 else -side)
        ld = _turn(d, off, e)
        bx, by, bz = (d[i] * s * size for i in range(3))
        flat = math.hypot(ld[0], ld[1])
        angle = (math.atan2(ld[1], ld[0]) if flat > 1e-6 else phi + k * SHOOT_TURN) + rng.uniform(-SHOOT_TWIST,
                                                                                                  SHOOT_TWIST)
        out.append(ShootLeaf((origin[0] + bx, origin[1] + by), angle, ls * max(SHOOT_SHOW, flat), ls, off, k, young,
                             bz + ld[2] * ls / 2))
        s += SHOOT_GAP[0] + (SHOOT_GAP[1] - SHOOT_GAP[0]) * t
    out.sort(key=lambda l: l.depth)
    return out


def branch_shoots(direction, size, rng, flowering=False, young_size=SHOOT_YOUNG_SIZE):
    """(start, direction, leaves) of each shoot splitting off a branch at (0, 0) growing along direction,
    far to near; start and leaves are relative to the branch point. Facing the viewer the shoots spread
    evenly round the branch; turned sideways they splay apart in the screen plane like fingers, the middle
    of three carrying on along the branch. On a flowering branch the shoot nearest the viewer, last in the
    list, is the flowering one."""
    direction = _unit((direction[0], direction[1] - BRANCH_LIFT, direction[2]))
    n = rng.randint(*BRANCH_SHOOTS)
    psi = rng.uniform(0, 2 * math.pi)
    _, m = _flat(direction)
    ways = []
    for j in range(n):
        spread = -1 + 2 * j / (n - 1)
        split = rng.uniform(*BRANCH_SPLIT) * ((1 - m) + m * abs(spread))
        e = _mosaic(direction, _round(direction, psi + 2 * math.pi * j / n + rng.uniform(-0.3, 0.3)),
                    1 if spread >= 0 else -1)
        ways.append(_turn(direction, split, e))
    ways.sort(key=lambda sd: sd[2])
    out = []
    for j, sd in enumerate(ways):
        start = (sd[0] * size * BRANCH_STEP, sd[1] * size * BRANCH_STEP)
        out.append((start, sd, shoot_leaves(start, sd, size, rng, flowering and j == n - 1, young_size)))
    return out


def _inside(poly_pts, x, y):
    hit = False
    n = len(poly_pts)
    for i in range(n):
        (x0, y0), (x1, y1) = poly_pts[i], poly_pts[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def _centroid(poly_pts):
    """The middle (centre of area) of a closed outline."""
    a = cx = cy = 0.0
    n = len(poly_pts)
    for i in range(n):
        (x0, y0), (x1, y1) = poly_pts[i], poly_pts[(i + 1) % n]
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    return cx / (3 * a), cy / (3 * a)


def _fan_centre(poly_pts):
    """The point a clipped mound's leaves fan out from: below its middle, MOUND_FAN_FOOT of the way down."""
    cx, _ = _centroid(poly_pts)
    ys = [p[1] for p in poly_pts]
    return cx, min(ys) + (max(ys) - min(ys)) * MOUND_FAN_FOOT


def _edge_distance(poly_pts, x, y):
    best = 1e9
    n = len(poly_pts)
    for i in range(n):
        (x0, y0), (x1, y1) = poly_pts[i], poly_pts[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((x - x0) * ex + (y - y0) * ey) / (ex * ex + ey * ey or 1)))
        best = min(best, math.hypot(x - x0 - t * ex, y - y0 - t * ey))
    return best if _inside(poly_pts, x, y) else -best


def mound(name, outline, focus, leaf_size, flower_spots, seed=0, density=1.0, tone_bias=0.0, edge=None, floor=None,
          rim_clear=None):
    """A big rounded flowering shrub seen close up, filling the closed screen outline: a dark body, branches
    of camellia shoots (Spray records holding Spray records) reaching the outline and pointing
    outwards, branches covering the inside (painted top to bottom, so the lower ones are nearer), branches
    spilling over the pot's rim, and flowers (x, y, radius, kind) each at the tip of a shoot of its own
    branch, in that shoot's collar of leaves. Every leaf grows on a shoot.
    The shrub is kept clipped, like the reference's: towards the outline its leaves turn to point out from
    its middle and show nearly their whole length, those at its foot are larger, and any leaf reaching past
    the outline is cut back to it.
    focus is the middle of the dome the branches grow out of (the middle of the planter's soil): a branch
    points along the dome's surface there, at the viewer in the middle and sideways at the outline. edge, a range of
    outline indices, limits the outline leaves to that run (the rest of the outline is off the frame).
    floor(x), the screen y of a pot's rim, keeps the inside branches above it; rim_clear (x0, x1) is a
    stretch of the rim no branch spills over, so the pot shows there. The dark body comes
    first in the list, so a pot can be drawn between it and the leaves."""
    rng = random.Random(seed)
    nm = Namer(name)
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    top, bottom, left, right = min(ys), max(ys), min(xs), max(xs)
    fx0, fy0 = focus
    tone_rng = random.Random(seed + 1)

    def tone(bx, by, ang, size):
        mx, my = bx + math.cos(ang) * size * 0.5, by + math.sin(ang) * size * 0.5
        h = max(0.0, min(1.0, (bottom - my) / (bottom - top)))
        side = max(-1.0, min(1.0, (fx0 - mx) / max(1.0, (right - left) / 2)))
        up = max(0.0, -math.sin(ang))
        rim = 1 - max(0.0, min(1.0, _edge_distance(outline, mx, my) / (leaf_size * 1.5)))
        score = 0.45 * h + 0.2 * up + 0.12 * side - 0.15 * rim * (1 if mx > fx0 else 0) + 0.1 + tone_bias \
            + tone_rng.uniform(-MOUND_TONE_JITTER, MOUND_TONE_JITTER)
        return 'leaf-%d' % (1 + round(max(0.0, min(1.0, score / 0.75)) * (len(LEAF_LEVELS) - 1)))

    items = []      # (paint key, kind, data)

    def dome(x, y, r=None):
        """The direction a branch at (x, y) grows in; r overrides how far out on the dome it is (0 to 1)."""
        dx, dy = x - fx0, y - fy0
        dist = math.hypot(dx, dy) or 1.0
        if r is None:
            r = dist / (reach(outline, focus, math.atan2(-dy, dx)) or dist)
        r = min(0.97, r)
        return (dx / dist * r, dy / dist * r, math.sqrt(1 - r * r))

    def grown(y):
        """The leaf size at screen height y: larger towards the foot, nearer the viewer."""
        return leaf_size * (MOUND_TOP_SIZE + (1 - MOUND_TOP_SIZE) * max(0.0, min(1.0, (y - top) / (bottom - top))))

    def shoots_for(direction, size, flowering=False):
        return branch_shoots(direction, size, rng, flowering, MOUND_YOUNG_SIZE)

    def add_branch(key, origin, direction):
        items.append((key, 'branch', (origin, direction, shoots_for(direction, grown(origin[1]) * rng.uniform(0.9, 1.05)))))

    def tips(shoots):
        for _, _, leaves in shoots:
            for l in leaves:
                yield l.base[0] + math.cos(l.angle) * l.length, l.base[1] + math.sin(l.angle) * l.length

    # outline branches: their furthest leaf tip on the outline, pointing out from the focus
    run_pts = outline if edge is None else outline[edge[0]:edge[1] + 1]
    dense = []
    for a, b in zip(run_pts, run_pts[1:]):
        n = max(1, int(math.dist(a, b) / 2))
        dense += [(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n) for t in range(n)]
    run = [0.0]
    for a, b in zip(dense, dense[1:]):
        run.append(run[-1] + math.dist(a, b))
    n_edge = int(run[-1] / (leaf_size * BRANCH_EDGE_SPACING) * density) + 1
    for i in range(n_edge):
        at = run[-1] * (i + rng.uniform(0.3, 0.7)) / n_edge
        k = min(range(len(run)), key=lambda j: abs(run[j] - at))
        tx, ty = dense[k]
        out_ang = math.atan2(ty - fy0, tx - fx0) + rng.uniform(-0.3, 0.3)
        r = rng.uniform(0.9, 0.97)
        direction = (math.cos(out_ang) * r, math.sin(out_ang) * r, math.sqrt(1 - r * r))
        shoots = shoots_for(direction, grown(ty) * rng.uniform(0.9, 1.05))
        out = max(x * math.cos(out_ang) + y * math.sin(out_ang) for x, y in tips(shoots))
        ox, oy = tx - math.cos(out_ang) * out, ty - math.sin(out_ang) * out
        if _inside(outline, ox, oy):
            items.append((ty - 400, 'branch', ((ox, oy), direction, shoots)))

    # inside: branches from a jittered grid, each growing along the dome
    step = leaf_size * BRANCH_SPACING / math.sqrt(density)
    row = 0
    y = top + step * 0.5
    while y < bottom:
        x = left + (step * 0.5 if row % 2 else 0.0)
        while x < right:
            bx, by = x + rng.uniform(-0.3, 0.3) * step, y + rng.uniform(-0.3, 0.3) * step
            if _edge_distance(outline, bx, by) > leaf_size * BRANCH_EDGE_CLEAR and (floor is None or by < floor(bx) - leaf_size * 0.15) \
                    and all(math.dist((bx, by), f[:2]) > leaf_size * BRANCH_FLOWER_CLEAR for f in flower_spots):
                add_branch(by, (bx, by), dome(bx, by))
            x += step
        y += step * 0.87
        row += 1

    # branches spilling forward over the pot's rim, painted over it
    if floor is not None:
        x = left + rng.uniform(0.2, 0.6) * leaf_size
        while x < right:
            by = floor(x) - leaf_size * 0.3
            if _inside(outline, x, by - 2) and not (rim_clear and rim_clear[0] <= x <= rim_clear[1]):
                out_ = max(-1.0, min(1.0, (x - fx0) / max(1.0, (right - left) / 2)))
                direction = (out_ * 0.5, BRANCH_LIFT + rng.uniform(*MOUND_HANG), 0.7)
                items.append((5000 + x, 'branch', ((x, by), direction,
                                                   shoots_for(direction, grown(by) * rng.uniform(*MOUND_HANG_SIZE)))))
            x += leaf_size * MOUND_HANG_EVERY * rng.uniform(0.8, 1.25)

    # flowers bloom at shoot tips on the outside of the bush, so they paint over everything; each grows on a
    # branch of its own, set back so its flowering shoot's tip is on the flower
    for fx, fy, r, kind in flower_spots:
        direction = dome(fx, fy)
        shoots = shoots_for(direction, max(grown(fy) * rng.uniform(0.9, 1.05), r * 1.9), flowering=True)
        start, _, leaves = shoots[-1]
        tx, ty = max(leaves, key=lambda l: l.node).base
        items.append((fy + r * 0.6 - 0.5, 'branch', ((fx - tx, fy - ty), direction, shoots)))
        items.append((FLOWERS_LAST + fy + r * 0.6, 'flower', (fx, fy, r, kind)))

    items.sort(key=lambda it: it[0])
    inset = leaf_size * MOUND_MASS_INSET
    body = []
    for x, y in outline:
        d = math.hypot(x - fx0, y - fy0) or 1.0
        k = max(0.0, d - inset) / d if (edge is None or left < x) else 1.0
        body.append((fx0 + (x - fx0) * k, fy0 + (y - fy0) * k) if x > left else (x, y + inset * (y < fy0 - 200)))
    shapes = [Shape(nm('mass'), poly(body), 'bush-mass')]

    def draw_leaf(leaf_name, bx, by, ang, size, young=False):
        t = tone(bx, by, ang, size)
        if young:
            t = 'leaf-%d' % min(len(LEAF_LEVELS), int(t.split('-')[1]) + 1)
        return leaf(leaf_name, (bx, by), ang, size, t, rng=rng, width=MOUND_LEAF_WIDTH * rng.uniform(0.92, 1.08),
                    stroke=MOUND_LEAF_STROKE, shade=LEAF_SHADE_DEEP[t],
                    gloss=t in ('leaf-4', 'leaf-5') and rng.random() < 0.7)

    mid = _fan_centre(outline)

    def clipped(bx, by, ang, length, size):
        """A leaf as the gardener leaves it: (angle, length) turned to point out from the middle the further out
        it grows, shown nearly whole, and cut back to the outline; None if that cuts it off."""
        dx, dy = bx - mid[0], by - mid[1]
        out_ = math.atan2(dy, dx)
        far = math.hypot(dx, dy) / (reach(outline, mid, -out_) or 1.0)
        w = max(0.0, min(1.0, (far - MOUND_FAN[0]) / (MOUND_FAN[1] - MOUND_FAN[0])))
        turn = math.atan2(math.sin(ang - out_), math.cos(ang - out_)) * (1 - w * (1 - MOUND_FAN_KEEP))
        limit = math.pi * (1 - w) + MOUND_FAN_MAX * w
        ang = out_ + max(-limit, min(limit, turn))
        length = max(length, size * MOUND_SHOW)
        if _edge_distance(outline, bx, by) <= 0:
            return None
        if _edge_distance(outline, bx + math.cos(ang) * length, by + math.sin(ang) * length) < 0:
            lo, hi = 0.0, length
            for _ in range(14):
                m = (lo + hi) / 2
                if _edge_distance(outline, bx + math.cos(ang) * m, by + math.sin(ang) * m) >= 0:
                    lo = m
                else:
                    hi = m
            length = lo
        return (ang, length) if length >= size * MOUND_CLIP_MIN else None

    def stem(stem_name, a, b, width):
        length = math.dist(a, b)
        if length < 1.0:
            return []
        return twig(stem_name, a, math.atan2(b[1] - a[1], b[0] - a[0]), length, width)

    def draw_branch(branch_name, origin, direction, shoots):
        """The branch's Spray of shoot Sprays, after the stems out to them. A shoot clipped back keeps its stem
        up to its last leaf; one clipped off is left out."""
        ox, oy = origin
        stems, sprays = [], []
        for j, (start, sd, leaves) in enumerate(shoots):
            shoot_name = '%s shoot %d' % (branch_name, j + 1)
            kept = [(l, cut) for l in leaves
                    for cut in [clipped(ox + l.base[0], oy + l.base[1], l.angle, l.length, l.size)] if cut]
            if not kept:
                continue
            last = max(l.node for l, _ in kept)
            nodes = [(ox + start[0], oy + start[1])] + [(ox + l.base[0], oy + l.base[1])
                                                         for l in sorted(leaves, key=lambda l: l.node) if l.node <= last]
            leaf_shapes = []
            for k, (a, b) in enumerate(zip(nodes, nodes[1:])):
                w = TWIG_WIDTH[0] + (TWIG_WIDTH[1] - TWIG_WIDTH[0]) * k / max(1, len(nodes) - 2)
                leaf_shapes += stem('%s stem %d' % (shoot_name, k + 1), a, b, w)
            for l, cut in kept:
                leaf_shapes += draw_leaf('%s leaf %d' % (shoot_name, l.node + 1), ox + l.base[0], oy + l.base[1],
                                         *cut, l.young)
            stems += stem('%s stem %d' % (branch_name, j + 1), origin, (ox + start[0], oy + start[1]), TWIG_WIDTH[0])
            reach_out = max(math.hypot(l.base[0] - start[0], l.base[1] - start[1]) for l, _ in kept)
            sprays.append(Spray(shoot_name, (ox + start[0], oy + start[1]), math.atan2(sd[1], sd[0]), reach_out,
                                leaf_shapes, sd[2]))
        drawn = stems + sprays
        if not sprays:
            return Spray(branch_name, origin, 0.0, 0.0, [], direction[2])
        reach_ = max((math.hypot(x, y) for x, y in tips(shoots)), default=0.0)
        return Spray(branch_name, origin, math.atan2(direction[1], direction[0]), reach_, drawn, direction[2])

    branches = 0
    for key, kind, data in items:
        if kind == 'branch':
            branch = draw_branch('%s branch %d' % (name, branches + 1), *data)
            if branch.shapes:
                branches += 1
                shapes.append(branch)
        else:
            fx, fy, r, kind = data
            rot, squash = rng.uniform(0, 2 * math.pi), rng.uniform(0.88, 0.97)
            st = min(STROKE, max(1.5, r / 4.5))
            if kind == 'rose':
                shapes += rose(nm('rose'), (fx, fy), r, rot, squash, stroke=st)
            else:
                shapes += flower(nm('white flower' if kind == 'white' else 'flower'), (fx, fy), r, rot, squash,
                                 kind == 'white', stroke=st, notch=MOUND_WHITE_NOTCH if kind == 'white' else MOUND_NOTCH)
    return shapes

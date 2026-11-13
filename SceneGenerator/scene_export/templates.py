"""Library, writes nothing: foliage templates: the small set of leaf, flower, rose and bud drawings every foliage piece in the
planters is placed from, and the placement (position, rotation, xScale, yScale) of each piece.

A leaf from foliage.leaf varies in length, width, outline stroke, midrib bend, tone, shade colour,
gloss and direction. A template fixes all of those; an instance scales it to its length (and, for a
template lying along an image axis, its width), mirrors it so its shade half falls on the side turned
from the sun, and rotates it the rest of the way. The leaf's colour gradient runs down the screen, so a
template is drawn already pointing in one of a few directions and the rotation an instance adds stays
small; otherwise a sideways leaf would be lit from its tip instead of along its top edge.

Every template is drawn with its stem (a leaf's base, a flower's centre) on a whole pixel, and its PNG
is cropped so the stem is exactly the image centre: the loader's "center" anchor and pivot."""

import math
from dataclasses import dataclass

from . import GENERATOR  # noqa: F401
from plants import branches
from plants import foliage

LIGHT = foliage.LIGHT_2D

# ---------------------------------------------------------------- what a leaf template may be
# leaf shapes: (width / length, outline stroke / length) of the drawn template, by family and size.
# Families keep foliage.py's two looks apart: 'urn' leaves have the plain shade half of a pot bush, the
# two-tone families ('broad', 'narrow') the deep shade half of the crystal planter's and corner bush's.
LEAF_SHAPES = {
    # name: (family, width, length, stroke)
    'urn-small': ('urn', 0.54, 20, 2.5),
    'urn': ('urn', 0.54, 40, 2.5),
    'broad-small': ('broad', 0.62, 28, 2.5),
    'broad': ('broad', 0.62, 54, 3.0),
    'narrow': ('narrow', 0.37, 52, 2.5),
}
FAMILY_WIDTHS = {'urn': 0.54, 'broad': 0.62, 'narrow': 0.37}
# directions a leaf template is drawn pointing (degrees on screen, y down; -90 is straight up). Leaves
# pointing left use the mirror image of one pointing right.
ORIENTATIONS = (-90,)
BOWS = (-0.07, 0.07)            # midrib bow towards the shade half, as a share of the length
TONES = {1: 'dark', 2: 'shade', 3: 'mid', 4: 'lit', 5: 'sun'}
TONE_MERGE = {}                  # level -> level, to fold rare tones into a neighbour
STEM_PAD = 3                     # px of clear border round a template's ink


def level(tone):
    if tone in foliage.LEAF_ALIASES:
        return foliage.LEAF_ALIASES[tone]
    return int(tone.split('-')[1])


def _normal(angle):
    return -math.sin(angle), math.cos(angle)


def _faces_light(angle):
    """foliage.leaf flips its normal towards the light when this is False."""
    nx, ny = _normal(angle)
    return nx * LIGHT[0] + ny * LIGHT[1] >= 0


def shade_side(angle):
    """Unit vector from the midrib to the leaf's shade half (the side turned from the light)."""
    nx, ny = _normal(angle)
    return (-nx, -ny) if _faces_light(angle) else (nx, ny)


def bow(angle, bend):
    """foliage.leaf's bend expressed as the midrib's bow towards the shade half."""
    return -bend if _faces_light(angle) else bend


def bend_for(angle, bow_):
    return -bow_ if _faces_light(angle) else bow_


@dataclass(frozen=True)
class LeafTemplate:
    shape: str
    level: int
    deep: bool          # two-tone: the shade half is the darker tone a level down
    gloss: bool
    bow: float
    orientation: int

    @property
    def id(self):
        o = {-90: '', -45: '-up-right', 0: '-right', 45: '-down-right', 90: '-down'}.get(
            self.orientation, '-at%d' % self.orientation)
        return 'leaf-%s-%s%s-%s%s' % (self.shape, TONES[self.level], '-gloss' if self.gloss else '',
                                        'bow' if self.bow > 0 else 'arch', o)

    def shapes(self, stem=(0, 0)):
        family, width, length, stroke = LEAF_SHAPES[self.shape]
        tone = 'leaf-%d' % self.level
        shade = (foliage.LEAF_SHADE_DEEP if self.deep else foliage.LEAF_SHADE)[tone]
        angle = math.radians(self.orientation)
        return foliage.leaf(self.id, stem, angle, length, tone, bend=bend_for(angle, self.bow), width=width,
                            stroke=stroke, gloss=self.gloss, shade=shade)


@dataclass(frozen=True)
class FlowerTemplate:
    kind: str           # 'pink', 'white', 'rose'
    radius: float
    notch: float
    rot: float          # radians
    squash: float = 0.88

    @property
    def id(self):
        name = {('pink', foliage.PETAL_NOTCH): 'flower', ('white', foliage.PETAL_NOTCH): 'daisy',
                ('pink', foliage.MOUND_NOTCH): 'flower-round',
                ('white', foliage.MOUND_WHITE_NOTCH): 'daisy-round'}.get((self.kind, self.notch), self.kind)
        if self.kind == 'rose':
            name = 'rose'
        return '%s-%d-%d' % (name, round(self.radius), round(math.degrees(self.rot)))

    def shapes(self, stem=(0, 0)):
        stroke = min(foliage.STROKE, max(1.5, self.radius / 4.5))
        if self.kind == 'rose':
            return foliage.rose(self.id, stem, self.radius, self.rot, self.squash, stroke=stroke)
        return foliage.flower(self.id, stem, self.radius, self.rot, self.squash, self.kind == 'white',
                              stroke=stroke, notch=self.notch)


@dataclass(frozen=True)
class BudTemplate:
    length: float
    orientation: int = -90

    @property
    def id(self):
        return 'bud'

    def shapes(self, stem=(0, 0)):
        return foliage.bud(self.id, stem, math.radians(self.orientation), self.length)


@dataclass(frozen=True)
class TwigTemplate:
    """A piece of stem pointing straight up from its base; an instance stretches it to its length."""
    length: float
    width: float

    @property
    def id(self):
        return 'stem'

    def shapes(self, stem=(0, 0)):
        return foliage.twig(self.id, stem, -math.pi / 2, self.length, self.width)


@dataclass(frozen=True)
class StemTemplate:
    """A stem image of one of branches.py's lengths and widths, pointing straight up from its base."""
    length_name: str
    width_name: str

    @property
    def id(self):
        return 'stem-%s-%s' % (self.length_name, self.width_name)

    @property
    def length(self):
        return branches.STEM_LENGTHS[self.length_name]

    @property
    def width(self):
        return branches.STEM_WIDTHS[self.width_name]

    def shapes(self, stem=(0, 0)):
        return foliage.twig(self.id, stem, -math.pi / 2, self.length, self.width)


@dataclass
class Placement:
    """Where an instance goes: the stem in screen px, rotation (radians), xScale and yScale."""
    template: object
    x: float
    y: float
    rotation: float
    xscale: float
    yscale: float

    def matrix(self):
        """(a, b, c, d, e, f) mapping template px (stem at the origin) to screen px."""
        c, s = math.cos(self.rotation), math.sin(self.rotation)
        return (c * self.xscale, s * self.xscale, -s * self.yscale, c * self.yscale, self.x, self.y)


def _wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def leaf_scales(shape, orientation, length, width):
    """(sx, sy) taking the template to the leaf's length and, along an image axis, width."""
    _, wt, lt, _ = LEAF_SHAPES[shape]
    along = length / lt
    across = length * width / (lt * wt)
    if orientation in (-90, 90):
        return across, along
    if orientation in (0, 180):
        return along, across
    return along, along


def place_leaf(t, base, angle, length, width):
    """The placement of template t that draws the leaf from base along angle: mirrored if needed so the
    shade half falls on the instance's shade side, rotated so the axis points along angle."""
    th = math.radians(t.orientation)
    st = shade_side(th)
    si = shade_side(angle)
    sx0, sy = leaf_scales(t.shape, t.orientation, length, width)
    for mirror in (False, True):
        sx = -sx0 if mirror else sx0
        phi = _wrap(angle - math.atan2(sy * math.sin(th), sx * math.cos(th)))
        c, s = math.cos(phi), math.sin(phi)
        mx, my = sx * st[0], sy * st[1]
        tx, ty = c * mx - s * my, s * mx + c * my
        if tx * si[0] + ty * si[1] > 0:
            return Placement(t, base[0], base[1], phi, sx, sy)
    raise AssertionError('no mirror puts the shade half on the shade side')


def leaf_shape_for(family, length, stroke):
    """The template shape of the family whose stroke-to-length ratio is nearest the leaf's."""
    options = [k for k, v in LEAF_SHAPES.items() if v[0] == family]
    return min(options, key=lambda k: abs(math.log((LEAF_SHAPES[k][3] / LEAF_SHAPES[k][2]) / (stroke / length))))


def leaf_family(p):
    deep = p['shade'] == foliage.LEAF_SHADE_DEEP[p['tone']] and p['shade'] != foliage.LEAF_SHADE[p['tone']]
    if not deep:
        return 'urn', False
    if p['width'] < 0.45:
        return 'narrow', True
    return 'broad', True


def leaf_template(p):
    """The template and placement for a recorded foliage.leaf call."""
    family, deep = leaf_family(p)
    shape = leaf_shape_for(family, p['length'], p['stroke'])
    lv = level(p['tone'])
    lv = TONE_MERGE.get(lv, lv)
    gloss = bool(p['gloss']) and foliage.LEAF_GLOSS['leaf-%d' % level(p['tone'])] is not None
    b = bow(p['angle'], p['bend'])
    q_bow = min(BOWS, key=lambda v: abs(v - b))
    best = None
    for o in ORIENTATIONS:
        t = LeafTemplate(shape, lv, deep, gloss, q_bow, o)
        pl = place_leaf(t, p['base'], p['angle'], p['length'], p['width'])
        if best is None or abs(pl.rotation) < abs(best.rotation) - 1e-9:
            best = pl
    return best


# ---------------------------------------------------------------- flowers
FLOWER_SIZES = (12.0, 16.5, 23.0, 32.0)    # template radii: below 13.5 the stroke scales with the radius
FLOWER_PHASES = (0.0, 36.0)                # petal turn of the templates (degrees; petals repeat every 72)
ROUND_FLOWER_SIZES = (22.0, 30.0)
DAISY_SIZES = (12.0,)
ROUND_DAISY_SIZES = (31.0,)
ROSE_SIZES = (34.0,)
ROSE_TURNS = (2.84, 4.79)     # the swirl turns of the corner bush's two roses


def _nearest_size(sizes, r):
    return min(sizes, key=lambda s: abs(math.log(r / s)))


def flower_template(kind, p):
    """Template and placement for a recorded flower or rose."""
    r, rot, squash = p['radius'], p['rot'], p['squash']
    if kind == 'rose':
        turn = min(ROSE_TURNS, key=lambda v: abs(_wrap(rot - v)))
        t = FlowerTemplate('rose', _nearest_size(ROSE_SIZES, r), 0.0, turn)
        k = r / t.radius
        return Placement(t, p['c'][0], p['c'][1], 0.0, k, k * squash / t.squash)
    white = p['white']
    notch = p['notch']
    if white:
        sizes = ROUND_DAISY_SIZES if notch == foliage.MOUND_WHITE_NOTCH else DAISY_SIZES
    else:
        sizes = ROUND_FLOWER_SIZES if notch == foliage.MOUND_NOTCH else FLOWER_SIZES
    size = _nearest_size(sizes, r)
    deg = math.degrees(rot)
    best = None
    for ph in FLOWER_PHASES:
        resid = (deg - ph + 36) % 72 - 36
        if best is None or abs(resid) < abs(best[1]):
            best = (ph, resid)
    t = FlowerTemplate('white' if white else 'pink', size, notch, math.radians(best[0]))
    k = r / size
    return Placement(t, p['c'][0], p['c'][1], math.radians(best[1]), k, k * squash / t.squash)


BUD_LENGTH = 18.0


def bud_template(p):
    t = BudTemplate(BUD_LENGTH)
    k = p['length'] / t.length
    return Placement(t, p['base'][0], p['base'][1], _wrap(p['angle'] - math.radians(t.orientation)), k, k)


TWIG_LENGTH = 24.0
TWIG_WIDTH = 3.0


def twig_template(p):
    t = TwigTemplate(TWIG_LENGTH, TWIG_WIDTH)
    return Placement(t, p['base'][0], p['base'][1], _wrap(p['angle'] + math.pi / 2), p['width'] / t.width,
                     p['length'] / t.length)


def stem_template(p):
    """The stem image nearest the piece's width, the shortest one it doesn't stretch past, placed along it."""
    width_name = min(branches.STEM_WIDTHS, key=lambda k: abs(branches.STEM_WIDTHS[k] - p['width']))
    fits = [k for k, v in branches.STEM_LENGTHS.items() if v >= p['length'] - 1e-9]
    length_name = min(fits, key=lambda k: branches.STEM_LENGTHS[k]) if fits else \
        max(branches.STEM_LENGTHS, key=branches.STEM_LENGTHS.get)
    t = StemTemplate(length_name, width_name)
    return Placement(t, p['base'][0], p['base'][1], _wrap(p['angle'] + math.pi / 2), p['width'] / t.width,
                     p['length'] / t.length)


def place(record):
    if record.kind == 'stem':
        return stem_template(record.params)
    if record.kind == 'leaf':
        return leaf_template(record.params)
    if record.kind == 'bud':
        return bud_template(record.params)
    if record.kind == 'twig':
        return twig_template(record.params)
    return flower_template(record.kind, record.params)

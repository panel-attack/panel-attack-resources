#   Writes SVG, run by `python3 -m scene_export render`: furniture/planters.svg, the planters sheet.
#   `check` and `fit` print fitting errors and write nothing.
#
#   The terrace planters, built in 3D and drawn through the terrace camera,
#   filled with the screen-space flower bushes from foliage.py.
#
#     Crystal planter  low round gold planter with turquoise tile panels, a gold
#                      lattice and a big diamond gem, holding three crystals
#                      (faceted hexagonal prisms) in a flower bush
#     Left urn         cream urn on a gold foot with teal gems, holding flowers
#     Right urn        the same urn behind the table
#
#   python3 -m furniture.planters  ->  planters.svg

import math
import random
import os
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares

from scene_export import cutting
from plants import branches
from plants import foliage
from common import gems

from furniture import planters_reference as T
from plants.foliage import Shape, poly
from furniture.table_set import Scene, catmull, ring

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- fitting to the reference
# Every turned pot is fitted to rings measured on the reference (planters_reference.py): the base ring
# fixes where the pot stands, and each other ring's height, radius, foreshortening and sideways lean
# are solved so its ellipse lands on the measured one. The reference paints each pot with its own
# perspective (an urn's rim is nearly edge-on while its foot is open), so a pot's depth is squashed
# by a factor that varies with height (Rig) instead of following the terrace camera exactly.

# ---------------------------------------------------------------- crystal planter
VISIBLE_ANGLE = 82                    # wrapped details stop here (degrees from the front)
PLANTER_LIP = 0.03                    # width of the rim's top surface
RIM_BULGE = 0.006                     # the rim band's front face bows out this much
# Body trim, read off the reference's crystal planter (left half; the right half mirrors it). Points are
# (degrees from the front, share of the body height from the body's foot (0) to the rim band's foot (1)).
TRIM_POST = (60, 89)                  # gold post at each end of the body, degrees from the front
TRIM_SWAG = [(-30.0, 1.06), (-19, 0.69), (-4.0, 0.42)]         # strap from the rim down into the gem frame,
                                                                # meeting the low strap under it
TRIM_LOW = [(-2.0, 0.30), (-12, 0.20), (-22, 0.15), (-30, 0.17), (-36, 0.22), (-42, 0.34), (-49.4, 0.55)]   # strap
                                                                # sagging from inside the gem frame, clear of the foot, and
                                                                # rising as the arch's right leg to its sharp peak
TRIM_ARCH = [(-49.4, 0.55), (-61.0, -0.03)]                     # the same strap on from the peak, straight down beside the post
TRIM_STRAP = 0.032
TRIM_SHADOW = [(-27.0, 1.0), (-10.0, 1.0), (-7.0, 0.6)]        # dark gap between the swag, rim and frame
# The body behind the strapwork is set with big irregular flagstones fitted together, as on the crystal
# reference: aqua on the lit left turning slate blue on the right third, each stone with a darker lower-right
# rim, parted from its neighbours by dark grout. Degrees are from the front, f is the share of the body height.
MARBLE_FIELDS = [   # (name, deg0, deg1, f0, f1, fill): broad fields over the base gradient
    ('shade field', 24, 92, -0.05, 0.95, '#0e6e9e'),
    ('shade deep', 52, 92, -0.05, 1.0, '#0a5288'),
]
MARBLE_HUES = [(-90, '#74e6d0'), (-40, '#62dcc8'), (0, '#4cbcc0'), (20, '#3482a6'), (40, '#296b8a'),
               (90, '#1c5070')]   # stone colour by angle: pale mint on the lit left to muted slate blue
MARBLE_ASPECT = 20.0     # the band's height in degrees of its width at the front: stones are laid out square there
MARBLE_STONE = 16.0      # flagstone pitch, degrees; each stone is the patch nearer its jittered seed than any other
MARBLE_ROWS = 2
MARBLE_GROUT = 0.3       # each stone drawn in this far (degrees) from its neighbours, leaving the grout between
MARBLE_BEVEL = (0.14, 0.88, (-1.0, 0.04))   # a stone's lower-right rim: its colour this far toward the seam ink,
                                           # the lit top's share of its size and (degrees, f) shift up-left
MARBLE_SEAM = ('#123c5c', 0.7, 1.6)   # seam ink, how far a stone's rim is mixed toward it, width px
GEM_FRAME_STANDOFF = 0.012            # the front diamond frame stands this far proud of the rim

# Crystals: (name, offset from the planter axis (X, Z), base height, radius, prism length, tip length,
#            lean (X, Z) per unit height, rotation degrees, apex offset, shoulder heights, palette)
# Shoulders scale the prism length at each of the six edges, so the tip facets come out uneven like
# a natural termination instead of a pencil point. Fitted to T.CRYSTAL_POINTS (planters.py fit), then the
# small two made squatter and wider, as cut gems on the crystal reference.
CRYSTALS = [
    ('big crystal', (0.0, 0.08), 0.216, 0.141, 0.514, 0.159, (0.0, 0.0), 30, -0.001,
     (1.0, 0.888, 1.0, 0.98, 1.0, 0.98), 'ice'),
    ('left crystal', (-0.1, -0.02), 0.216, 0.1, 0.235, 0.11, (-0.36, 0.04), 14, -0.021,
     (1.0, 0.92, 0.96, 1.0, 1.08, 1.04), 'violet'),
    ('right crystal', (0.1, -0.01), 0.216, 0.095, 0.255, 0.115, (0.12, 0.04), 33, 0.03,
     (1.0, 0.8, 1.02, 0.96, 0.92, 0.97), 'blue'),
]
# Per palette: side face gradients (top, [middle,] bottom) and tip facet colours, darkest .. lightest;
# outline; the paler inner plane across the lit face. As on the crystal reference: the big crystal aqua on
# the lit side turning royal blue in shade; the left small one magenta on its lit faces and deep blue in
# shade under a pale periwinkle point, the right one cyan-tipped and blue turning violet down each face. A thin dark outline goes round each crystal; the edges between
# its faces are thin light lines.
CRYSTAL_PALETTES = {
    'ice': ([('#1c4f8e', '#1a4a86'), ('#2565a8', '#2a6eb0'), ('#2a72b5', '#3283c0'), ('#6eeedc', '#5dd1d0')],
            ['#2a6aa8', '#3a90c0', '#4ab3ca', '#dcfaf0'], '#1a4a78', ('#92f4e2', '#78e2d8')),
    'violet': ([('#2a44c8', '#3048d8', '#364ce3'), ('#3a64ec', '#3a5ae8', '#4a54e6'), ('#4a6af0', '#4458e8', '#3e50e4'),
                ('#a87cf6', '#cc5ee8', '#e070f0')],
               ['#3a60e0', '#5a6cf0', '#8a7cf4', '#a8b8fa'], '#3a3c8a', ('#e2a4f6', '#f09cf4')),
    'blue': ([('#2c50d8', '#6a40e8', '#a64ff2'), ('#3468e8', '#7a48f0', '#ac5bf7'), ('#4a8cf6', '#8a50f2', '#a64ff2'),
              ('#5a8cf6', '#7a64f2', '#9a52f0')],
             ['#3a6ce8', '#4aa8f4', '#62d4f6', '#7febf8'], '#2c3a88', ('#9ae8fa', '#8a90f6')),
}
# Crystal faces take palette steps by lambert value against LIGHT (thresholds for steps 2 and 3; step 1
# below the first, step 0 only facing away), so lit neighbours differ by one step, not the whole range.
CRYSTAL_SIDE_STEPS = (0.25, 0.42)
CRYSTAL_OUTLINE = 2.5
CRYSTAL_EDGE = 0.9
CRYSTAL_TIP_STEPS = (0.5, 0.82)
LIGHT = np.array([-0.25, 1.0, -0.5])   # towards the sun: high, behind the camera, a little left (shadows.SUN)

# ---------------------------------------------------------------- urn
# (part, rings from planters_reference.LEFT_URN_RINGS bottom to top, paint, outline): a gold disc base,
# a flared cream foot, a gold collar, the deep cream bowl and a pale gold rim band.
URN_PARTS = [
    ('foot', ('base bottom', 'base top'), 'gold-dark', 'gold'),
    ('stem', ('stem foot', 'stem top'), 'cream', 'cream'),
    ('collar', ('stem top', 'collar mid', 'collar top'), 'gold', 'gold'),
    ('bowl', ('bowl 1', 'bowl 2', 'bowl 3', 'bowl 4', 'bowl widest', 'rim bottom'), 'cream', 'cream'),
    ('rim', ('rim bottom', 'rim top'), 'gold-pale', 'gold'),
]
URN_AXIS_RING = 'rim top'              # each urn stands upright on this ring's axis (upright_urn)
URN_UNDERSIDE = 0.85              # share of the bowl below its widest that the underside shade covers
URN_FLUTES = 7                        # broad shallow flutes round the bowl
URN_RIM_LIP = 0.026
URN_INTERIOR = ('#3e4a2c', '#2c3620')    # dark inner wall seen behind the far rim
URN_SOIL_DROP = 0.004                 # soil sits this far below the rim top (a sliver of dark wall shows)
URN_BUSH_LEAF = 0.8                  # urn bush leaf size (times LEAF_SIZE at depth)
URN_BUSH_DENSITY = 1.0
# Glossy leaves spilling forward over the urn's front rim, each drawn on both sides as mirror images:
# (position out from the middle of the rim 0..1, outward turn radians, size). The centre is left clear
# for the rim gem.
URN_RIM_LEAVES = [(0.91, 0.9, 1.05), (0.73, 0.38, 0.9)]
URN_SPILL_SEED = 31                   # both urns' rim leaves, so the two urns match


# ---------------------------------------------------------------- foliage sizes (screen px at REFERENCE_SCALE)
REFERENCE_SCALE = 330.0        # px per eye height at the crystal planter
LEAF_SIZE = 42.0
CRYSTAL_SWEEP = (0.15, math.pi - 0.15)   # the bushes fan upwards only; the leaves at the rim's ends are
#                                         planters_reference.CRYSTAL_SIDE_LEAVES, so none lie along the rim band
CRYSTAL_RIM_LEAVES = 7
# round 9b: three leaf sizes by position, big upright ones at the back and between the crystals (the
# back bush's outline), medium ones angling outwards (the front bush's rings), small ones drooping over the rim
CRYSTAL_TIER_BIG = 1.3
CRYSTAL_RINGS_FRONT = [(0.62, 0.95, 1.0, 'mid'), (0.34, 0.68, 1.15, 'front')]
CRYSTAL_TIER_SMALL = (0.55, 0.7)
CRYSTAL_WHITE_SIZE = 0.7              # white flowers against the pink ones' size
CRYSTAL_FRONT_WHITES = [(648, 634), (724, 634), (878, 630)]   # set inside the leaf mass, left to right
CRYSTAL_FRONT_WHITE_R = 11
CRYSTAL_LEAF = 0.95             # the crystal planter's leaves are smaller than the urns'
# (tip, share of the base-to-tip run): the tall upright leaves before and between the crystals
CRYSTAL_BASE_LEAVES = [((742, 580), 0.6), ((792, 578), 0.6), ((765, 566), 0.62)]
FLOWER_SIZE = 36.0             # the reference's bush flowers are big, ~45 px across at the urn
DEPTH_EXPONENT = 0.4           # foliage grows slower than true perspective towards the camera

MOUND_RINGS = [(0.62, 1.0, 0.95, 'mid'), (0.3, 0.95, 1.1, 'front')]   # fewer, looser rosettes than a pot's
# ---------------------------------------------------------------- colours
STROKE = 3
GRADIENTS = {
    'gold': ('#ffe07a', '#eda93a'),
    'gold-dark': ('#f3bb45', '#c07f2a'),
    'turquoise': ('#4fd6dc', '#1a9fb4'),
    'gold-pale': ('#fff0b0', '#f2c45e'),
    'grout': ('#0b5876', '#0a4462'),
    'marble': ('#0c6e8e', '#1496b2'),
    'gold-face': ('#ffe86a', '#eea02c'),
    'cream': ('#fffaf0', '#f0deb8'),
    'soil': ('#3a7a34', '#2a5e2a'),
}
OUTLINE = {'gold': '#a76a3d', 'turquoise': '#1d8fa5', 'cream': '#b99b62', 'gem': '#0b7f99'}
GOLD_SHEEN = '#fff3b8'
GEM_GOLD = dict(gems.SETTING, line=OUTLINE['gold'])
FLUTE = '#e6d0a2'
TRIM_GAP = '#7a4e44'
GOLD_SHADE = '#dc8e26'

# ---------------------------------------------------------------- lighting
# One sun, high, behind the camera and a little left: tops and the left of each turned part are lit,
# the right turns into shade in two flat steps, and a dark band sits under every overhang.
SHADE_FROM = 24                       # degrees right of the front where the first shade step starts
SHADE_DEEP = 56                       # and the second
SHEEN_FROM, SHEEN_TO = -62, 20       # degrees a top-left sheen arc spans on a small turned part
SHADE_EDGE = 88                       # the steps run to here (the silhouette is just short of 90)
SIDE_SHADES = {                       # part paint: (first step, second step) gradients
    'gold': (('#f8c650', '#dc962e'), ('#eaaa3c', '#c98226')),
    'gold-face': (('#f8cc4a', '#dc9028'), ('#ebb03c', '#c78024')),
    'gold-dark': (('#e4a83c', '#b07226'), ('#d39632', '#9e6420')),
    'gold-pale': (('#f8dc8e', '#e4b450'), ('#efcc76', '#d6a444')),
    'cream': (('#f6ead0', '#e6cfa2'), ('#ead8b2', '#d8bc8a')),
}
OCCLUSION = {'gold': '#7a4210', 'gold-dark': '#6a3a10', 'cream': '#7a5a2a', 'grout': '#021c2a'}
OCCLUSION_DEPTH = 0.016               # world height of the deepest band under a rim or collar
OCCLUSION_STEPS = (1.0, 0.62, 0.3)    # stacked bands, as shares of the depth; each one is OCCLUSION_ALPHA
OCCLUSION_ALPHA = 0.16
# Contact shade on the floor round a pot's foot (the sun is behind the camera, so the cast shadow is
# hidden behind the pot): stacked rings growing out from the foot, each FLOOR_ALPHA.
FLOOR_SHADE = '#0a3048'
FLOOR_STEPS = (1.035, 1.075, 1.13)
FLOOR_ALPHA = 0.14
FLOOR_SHIFT = np.array([1.0, 1.0])  # (x, z) shift of each ring per unit of its growth: the sun's travel
GOLD_FACE_SHADE = ('#f6c446', '#d08624')   # the planter's strapwork on the right of its gem


# ---------------------------------------------------------------- output

class Out:
    def __init__(self):
        self.body = []
        self.gradients = dict(foliage.GRADIENTS)
        self.gradients.update(GRADIENTS)

    def open(self, name):
        self.body.append('<g id="%s">' % name)

    def piece(self, name, placement):
        """A group drawing a branches.py library piece where placement puts it, carrying the placement."""
        self.body.append('<g id="%s" data-piece="%s" data-at="%r,%r" data-rotation="%r" data-scale="%r"%s>'
                         % (name, placement.piece, placement.at[0], placement.at[1], placement.rotation,
                            placement.scale, ' data-mirror="1"' if placement.mirror else ''))

    def close(self):
        self.body.append('</g>')

    def shape(self, name, points, fill, outline=None, width=STROKE, opacity=1.0):
        stroke = 'none' if outline is None else OUTLINE.get(outline, outline)
        self.add(Shape(name, poly(points), fill, stroke, width if outline else 0, opacity))

    def add(self, s):
        fill = 'url(#%s)' % s.fill if s.fill in self.gradients else s.fill
        stroke = '' if s.stroke == 'none' else (' stroke="%s" stroke-width="%g" stroke-linejoin="round" '
                                                'stroke-linecap="round"' % (s.stroke, s.width))
        alpha = '' if s.opacity >= 1 else ' fill-opacity="%g"' % s.opacity
        self.body.append('<path id="%s" d="%s" fill="%s"%s%s/>' % (s.name, s.d, fill, alpha, stroke))

    def add_all(self, shapes):
        for s in shapes:
            self.add(s)

    def write(self, path, group='Planters'):
        def stops(colours):
            return ''.join('<stop offset="%g" stop-color="%s"/>' % (i / (len(colours) - 1), c)
                           for i, c in enumerate(colours))
        defs = ''.join('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1">%s</linearGradient>' % (k, stops(cs))
                       for k, cs in self.gradients.items())
        with open(path, 'w') as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1024" viewBox="0 0 1536 1024">\n')
            f.write('<defs>%s</defs>\n<g id="%s">\n' % (defs, group))
            f.write('\n'.join(self.body))
            f.write('\n</g>\n</svg>\n')


# ---------------------------------------------------------------- helpers

def foot_centre(scene, screen, radius):
    """World centre of a round foot of the given radius whose front edge lands on the screen point."""
    front = scene.cam.unproject_onto_plane(*screen, np.zeros(3), np.array([0, 1.0, 0]))
    d = front - scene.eye
    d[1] = 0
    return front + d / np.linalg.norm(d) * radius * np.array([1, 0, 1])


def wrap(scene, c, r, u, h):
    """Point at arc length u (right positive) round the camera-facing side of radius r(h)."""
    rad = r(h) + 0.003
    theta = math.atan2(c[0], c[2]) + math.pi - u / rad
    return scene.project((c[0] + rad * math.sin(theta), h, c[2] + rad * math.cos(theta)))


def wrapped(scene, c, r, pts, limit=None):
    out = []
    for u, h in pts:
        if limit is not None:
            umax = math.radians(limit) * r(h)
            u = max(-umax, min(umax, u))
        out.append(wrap(scene, c, r, u, h))
    return out


def turned_band(scene, c, r, h0, h1, d0, d1, n=24):
    """The part of a turned surface between heights h0..h1 and d0..d1 degrees from the front."""
    ds = np.linspace(d0, d1, n)
    return wrapped(scene, c, r, [(math.radians(d) * r(h1), h1) for d in ds]
                   + [(math.radians(d) * r(h0), h0) for d in ds[::-1]])


def top_left_sheen(scene, c, r, h, below0, below1, d0=SHEEN_FROM, d1=SHEEN_TO, n=24):
    """A thin sheen arc just under height h, from d0 to d1 degrees (left of the front to a little right)."""
    ds = np.linspace(d0, d1, n)
    return wrapped(scene, c, r, [(math.radians(d) * r(h - below0), h - below0) for d in ds]
                   + [(math.radians(d) * r(h - below1), h - below1) for d in ds[::-1]])


def side_shade(out, scene, c, r, h0, h1, name, paint, outline=None):
    """The two shade steps on the right of a turned part, then its outline again on top."""
    for step, (d0, pair) in enumerate(zip((SHADE_FROM, SHADE_DEEP), SIDE_SHADES[paint])):
        key = '%s-shade-%d' % (paint, step + 1)
        out.gradients[key] = pair
        out.shape('%s shade %d' % (name, step + 1), turned_band(scene, c, r, h0, h1, d0, SHADE_EDGE), key)
    if outline:
        out.shape(name + ' outline', lathe(scene, r, h0, h1), 'none', outline)


def occlusion(out, scene, c, r, h_top, name, fill, depth=OCCLUSION_DEPTH):
    """The soft dark band a rim or collar throws on the surface just under it: stacked low-opacity
    bands, deepest at the overhang."""
    for i, share in enumerate(OCCLUSION_STEPS):
        out.shape('%s occlusion %d' % (name, i + 1),
                  turned_band(scene, c, r, h_top - depth * share, h_top, -SHADE_EDGE, SHADE_EDGE, 48),
                  OCCLUSION.get(fill, fill), opacity=OCCLUSION_ALPHA)


def floor_contact(out, scene, c, h, radius, name):
    """Soft contact shade on the floor round a foot of the given radius, each ring nudged back and right
    (down-sun) by FLOOR_SHIFT of its growth so none of it shows on the sun's side."""
    for i, k in enumerate(FLOOR_STEPS[::-1]):
        shift = radius * (k - 1) * FLOOR_SHIFT
        cc = np.array([c[0] + shift[0], c[1], c[2] + shift[1]])
        out.shape('%s floor contact %d' % (name, i + 1), ring(scene, cc, h, radius * k, 96), FLOOR_SHADE,
                  opacity=FLOOR_ALPHA)


def depth_scale(scene, p):
    return (scene.scale(p) / REFERENCE_SCALE) ** DEPTH_EXPONENT


def ellipse_box(points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def diamond(cu, ch, hw, hh):
    return [(cu, ch - hh), (cu + hw, ch), (cu, ch + hh), (cu - hw, ch)]


def gem(out, scene, c, r, name, cu, ch, hw, hh, outline_width=STROKE, outer=None):
    """A pointed, faceted rhombus gem (gems.py) wrapped on r; outer: half sizes of a gold setting round it."""
    gems.write(out.body, gems.diamond_gem(name, lambda p: wrapped(scene, c, r, p), cu, ch, hw, hh, outer=outer,
                                          gold=GEM_GOLD, stroke=outline_width, stone_stroke=min(outline_width, 2)), group=name)


# ---------------------------------------------------------------- rigs

class Rig:
    """One pot's own view: the terrace camera, with the pot's depth squashed by k(h) along the line of
    sight and its axis leaning sideways by lean(h) world units, both interpolated between the fitted
    rings. It stands in for the Scene everywhere the pot is drawn. An upright rig draws the pot as if it
    stood straight ahead of the camera, then slides it sideways on screen to where it stands (world centre),
    so its rings are level ellipses and its front faces the viewer whatever its place on the terrace."""

    def __init__(self, scene, centre, upright=False):
        self.cam, self.eye = scene.cam, scene.eye
        self.world = np.array(centre, float)
        self.c = np.array([0.0, centre[1], centre[2]], float) if upright else self.world
        self.shift = self.cam.focal * centre[0] / centre[2] if upright else 0.0
        d = np.array([self.world[0], 0.0, self.world[2]])
        self.world_along = d / np.linalg.norm(d)
        d = np.array([self.c[0], 0.0, self.c[2]])
        self.along = d / np.linalg.norm(d)        # squashing along the line of sight keeps the front
        # of the pot on its own axis on screen, so gems and frames on it stay upright
        self.knots = [(0.0, 1.0, 0.0)]

    def _interp(self, h, i):
        ks = sorted(self.knots)
        return float(np.interp(h, [q[0] for q in ks], [q[i] for q in ks]))

    def k(self, h):
        return self._interp(h, 1)

    def lean(self, h):
        return self._interp(h, 2)

    def project(self, p, k=None, lean=None):
        p = np.asarray(p, float)
        h = p[1] - self.c[1]
        k = self.k(h) if k is None else k
        lean = self.lean(h) if lean is None else lean
        local = p - self.c
        d = (k - 1) * (local[0] * self.along[0] + local[2] * self.along[2])
        x, y = self.cam.project(p[0] + d * self.along[0] + lean, p[1], p[2] + d * self.along[2])
        return x + self.shift, y

    def scale(self, p):
        return self.cam.focal / p[2]

    def ring(self, h, r, k=None, lean=None, n=180):
        c = self.c
        return np.array([self.project((c[0] + r * math.sin(t), c[1] + h, c[2] + r * math.cos(t)), k, lean)
                         for t in np.linspace(0, 2 * math.pi, n, endpoint=False)])

    def ellipse(self, h, r, k=None, lean=None):
        """The ring's ellipse as planters_reference measures it: cx, cy, a, b and front-most y."""
        pts = self.ring(h, r, k, lean)
        il, ir = int(np.argmin(pts[:, 0])), int(np.argmax(pts[:, 0]))
        return dict(cx=(pts[il, 0] + pts[ir, 0]) / 2, cy=(pts[il, 1] + pts[ir, 1]) / 2,
                    a=(pts[ir, 0] - pts[il, 0]) / 2, b=(pts[:, 1].max() - pts[:, 1].min()) / 2, fy=pts[:, 1].max())


def ring_residual(got, want):
    keys = ['cx', 'cy' if 'cy' in want else 'fy', 'a'] + (['b'] if want.get('b') is not None else [])
    return [got[k] - want[k] for k in keys]


def fit_rig(scene, rings, upright=False):
    """Solve a Rig and each ring's (height, radius) from the measured rings; the first ring stands on
    the floor. Rings with a measured b set the foreshortening; the others take it from them."""
    cam = scene.cam
    names = list(rings)
    base = rings[names[0]]
    z0 = cam.focal / (base['cy'] - cam.horizon)

    def base_res(v):
        X, Z, r, k = v
        rig = Rig(scene, (X, 0.0, Z), upright)
        return ring_residual(rig.ellipse(0.0, r, k, 0.0), base)
    X, Z, r, k = least_squares(base_res, [(base['cx'] - cam.centre_x) * z0 / cam.focal, z0,
                                          base['a'] * z0 / cam.focal, 1.0]).x
    rig = Rig(scene, (X, 0.0, Z), upright)
    rig.knots = [(0.0, k, 0.0)]
    solved = {names[0]: (0.0, r)}
    order = [n for n in names[1:] if rings[n].get('b') is not None] + \
            [n for n in names[1:] if rings[n].get('b') is None]
    knots = {}
    # rings without a measured b take k from the knots either side, which move as later rings are
    # solved; a few passes settle them, so each ring is drawn where it was measured
    for sweep in range(4):
        for name in order if sweep == 0 else [n for n in order if rings[n].get('b') is None]:
            want = rings[name]
            knots.pop(name, None)
            rig.knots = [(0.0, k, 0.0)] + list(knots.values())
            y = want.get('cy', want.get('fy'))
            guess = [1 - (y - cam.horizon) * Z / cam.focal, want['a'] * Z / cam.focal, 0.0]
            if want.get('b') is not None:
                fit = least_squares(lambda v: ring_residual(rig.ellipse(v[0], v[1], v[3], v[2]), want), guess + [1.0])
                h, r, lean, kk = fit.x
            else:
                fit = least_squares(lambda v: ring_residual(rig.ellipse(v[0], v[1], None, v[2]), want), guess)
                h, r, lean = fit.x
                kk = rig.k(h)
            knots[name] = (h, kk, lean)
            solved[name] = (h, r)
    rig.knots = [(0.0, k, 0.0)] + list(knots.values())
    return rig, solved


def profile(solved, names):
    """Radius as a smooth function of height through the named rings."""
    hs = [solved[n][0] for n in names]
    rs = [solved[n][1] for n in names]
    order = np.argsort(hs)
    hs, rs = np.array(hs)[order], np.array(rs)[order]
    if len(hs) == 2:
        return lambda h: float(np.interp(h, hs, rs))
    f = PchipInterpolator(hs, rs)
    return lambda h: float(f(min(max(h, hs[0]), hs[-1])))


def lathe(rig, r, h0, h1, steps=24, n=144):
    """Outline of the turned surface r(h), h0..h1: the front arc of the bottom ring, the screen
    extremes of the rings in between and the back arc of the top ring."""
    c = rig.c
    ts = np.linspace(0, 2 * math.pi, n, endpoint=False)
    rings = [np.array([rig.project((c[0] + r(h) * math.sin(t), c[1] + h, c[2] + r(h) * math.cos(t))) for t in ts])
             for h in np.linspace(h0, h1, steps)]

    def arc(R, front):
        il, ir = int(np.argmin(R[:, 0])), int(np.argmax(R[:, 0]))
        fwd = [R[(il + i) % n] for i in range((ir - il) % n + 1)]
        bwd = [R[(il - i) % n] for i in range((il - ir) % n + 1)]
        mean = lambda a: sum(p[1] for p in a) / len(a)
        return max(fwd, bwd, key=mean) if front else min(fwd, bwd, key=mean)
    lefts = [R[int(np.argmin(R[:, 0]))] for R in rings]
    rights = [R[int(np.argmax(R[:, 0]))] for R in rings]
    pts = arc(rings[0], True) + rights[1:-1] + arc(rings[-1], False)[::-1] + lefts[::-1][1:-1]
    return [tuple(p) for p in pts]


def surface_uv(rig, r, screen, guess=(0.0, 0.2)):
    """(arc length from the front, height) of the point on the surface r(h) seen at screen."""
    fit = least_squares(lambda v: np.array(wrap(rig, rig.c, r, v[0], v[1])) - screen, guess)
    return tuple(fit.x)


def diamond_uv(rig, r, corners):
    """Centre u, h and half sizes of a diamond whose four tips are measured screen points."""
    uv = {k: surface_uv(rig, r, np.array(p, float)) for k, p in corners.items()}
    cu = (uv['left'][0] + uv['right'][0]) / 2
    ch = (uv['top'][1] + uv['bottom'][1]) / 2
    return cu, ch, (uv['right'][0] - uv['left'][0]) / 2, (uv['top'][1] - uv['bottom'][1]) / 2


def gem_uv(rig, r, centre, half):
    x, y = centre
    return diamond_uv(rig, r, dict(top=(x, y - half[1]), bottom=(x, y + half[1]),
                                   left=(x - half[0], y), right=(x + half[0], y)))


def real_screen(scene, rig, radius):
    """Screen point of the front of a foot of radius at the rig's centre through the true camera, so
    foot_centre(scene, that, radius) gives the rig's centre back (shadows.py places shadows by it)."""
    p = rig.world - rig.world_along * radius
    return tuple(float(v) for v in scene.cam.project(*p))


# ---------------------------------------------------------------- crystals

def frame(axis):
    a = axis / np.linalg.norm(axis)
    e1 = np.cross(a, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(a, e1)
    return a, e1, e2


def hull(points):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def lambert_tones(faces, steps):
    """Each face's palette step from how directly it faces the sun: step 0 only for a face turned away,
    then one step per threshold its lambert value passes."""
    return [(f, 0 if f[0] <= 0 else 1 + sum(f[0] >= t for t in steps)) for f in faces]


def crystal(out, scene, name, base, axis, radius, length, tip, rot, apex_shift, shoulders, palette_name):
    """A cut hexagonal crystal column: six side faces, an uneven six-facet point, each face one flat
    tone picked by how it faces LIGHT, then a paler inner plane on the lit face and a deeper one in shade."""
    sides_pal, tips_pal, outline, facet = CRYSTAL_PALETTES[palette_name]
    key = 'crystal-' + palette_name
    for i, pair in enumerate(sides_pal + [facet]):
        out.gradients['%s-%d' % (key, i)] = pair
    a, e1, e2 = frame(np.asarray(axis, float))
    angles = [math.radians(rot + 60 * k) for k in range(6)]
    bottom = [base + radius * (math.cos(t) * e1 + math.sin(t) * e2) for t in angles]
    top = [p + a * length * s for p, s in zip(bottom, shoulders)]
    apex = base + a * (length + tip) + apex_shift * e1
    core = base + a * length * 0.5
    light = LIGHT / np.linalg.norm(LIGHT)
    faces = []
    for k in range(6):
        j = (k + 1) % 6
        faces.append(('side', k, [bottom[k], bottom[j], top[j], top[k]]))
        faces.append(('tip', k, [top[k], top[j], apex]))
    visible = {'side': [], 'tip': []}
    for kind, k, pts in faces:
        centroid = np.mean(pts, axis=0)
        n = np.cross(pts[1] - pts[0], pts[-1] - pts[0])
        n /= np.linalg.norm(n)
        if np.dot(n, centroid - core) < 0:
            n = -n
        if np.dot(n, scene.eye - centroid) <= 0.01:
            continue
        visible[kind].append((float(np.dot(n, light)), k, pts))
    P = scene.project
    out.open(name)
    every = [P(p) for _, _, pts in visible['side'] + visible['tip'] for p in pts]
    out.shape(name + ' outline', hull(every), outline, outline, CRYSTAL_OUTLINE)
    edge = facet[0]
    sides = lambert_tones(visible['side'], CRYSTAL_SIDE_STEPS)
    tips = lambert_tones(visible['tip'], CRYSTAL_TIP_STEPS)
    for (s, k, pts), tone in sorted(sides, key=lambda f: f[0][1]):
        out.shape('%s side %d' % (name, k + 1), [P(p) for p in pts], '%s-%d' % (key, tone), edge, CRYSTAL_EDGE)
    for (s, k, pts), tone in sorted(tips, key=lambda f: f[0][1]):
        out.shape('%s tip %d' % (name, k + 1), [P(p) for p in pts], tips_pal[tone], edge, CRYSTAL_EDGE)

    def on(pts, su, tv):
        b0, b1, t1, t0 = pts
        return P((1 - tv) * ((1 - su) * b0 + su * b1) + tv * ((1 - su) * t0 + su * t1))

    by_tone = sorted(sides, key=lambda f: (-f[1], -f[0][0]))
    # inner planes: a paler one rising across the lit face, a deeper one at the foot of the darkest
    (s, k, pts), tone = by_tone[0]
    out.shape(name + ' lit facet', [on(pts, 0.0, 0.0), on(pts, 0.0, 0.45), on(pts, 0.5, 0.0)],
              '%s-%d' % (key, len(sides_pal)), edge, CRYSTAL_EDGE)
    if len(by_tone) > 2:
        (s, k, pts), tone = by_tone[-1]
        out.shape(name + ' shade facet', [on(pts, 0.55, 0.0), on(pts, 1.0, 0.0), on(pts, 1.0, 0.55)],
                  '%s-%d' % (key, max(0, tone - 1)), edge, CRYSTAL_EDGE)
    out.close()


# ---------------------------------------------------------------- crystal planter

def trim_uv(body, h0, h1, deg, f):
    h = h0 + (h1 - h0) * f
    return math.radians(deg) * body(h), h


def strap(line, width):
    """A band of the given width along a (u, h) polyline: both edges, offset across it and mitred at its
    corners so a sharp turn keeps the band's full width."""
    pts = np.array(line, float)
    normals = [np.array([a[1] - b[1], b[0] - a[0]]) / np.linalg.norm(b - a) for a, b in zip(pts, pts[1:])]
    left, right = [], []
    for i, p in enumerate(pts):
        n1, n2 = normals[max(i - 1, 0)], normals[min(i, len(normals) - 1)]
        m = (n1 + n2) / np.linalg.norm(n1 + n2)
        n = m * width / 2 / np.dot(m, n1)
        left.append(tuple(p + n))
        right.append(tuple(p - n))
    return left + right[::-1]


def marble_hue(deg):
    for (d0, c0), (d1, c1) in zip(MARBLE_HUES, MARBLE_HUES[1:]):
        if deg <= d1:
            return mix(c0, c1, max(0.0, (deg - d0) / (d1 - d0)))
    return MARBLE_HUES[-1][1]


def mix(a, b, t):
    pa = [int(a[k:k + 2], 16) for k in (1, 3, 5)]
    pb = [int(b[k:k + 2], 16) for k in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * t) for x, y in zip(pa, pb))


def half_plane(poly, p, q):
    """The part of a convex polygon nearer p than q."""
    n, mid = q - p, (p + q) / 2
    side = [float(np.dot(v - mid, n)) for v in poly]
    kept = []
    for i, v in enumerate(poly):
        j = (i + 1) % len(poly)
        if side[i] <= 0:
            kept.append(v)
        if (side[i] < 0) != (side[j] < 0) and side[i] != side[j]:
            kept.append(v + (poly[j] - v) * side[i] / (side[i] - side[j]))
    return kept


def union(polys, resolution=4000):
    """The outlines of the area the polygons cover together, traced off a fine raster of them: one
    outline per separate piece, plus one per hole."""
    pts = np.concatenate([np.asarray(p, float) for p in polys])
    lo = pts.min(axis=0)
    scale = resolution / max(np.ptp(pts, axis=0))
    pad = 4
    w, h = (np.ptp(pts, axis=0) * scale).astype(int) + 2 * pad + 1
    mask = np.zeros((h, w), np.uint8)
    for p in polys:
        q = ((np.asarray(p, float) - lo) * scale + pad) * 16
        cv2.fillPoly(mask, [np.round(q).astype(np.int32)], 255, lineType=cv2.LINE_8, shift=4)
    contours, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    return [[tuple((v - pad) / scale + lo) for v in cv2.approxPolyDP(k, 0.75, True)[:, 0].astype(float)]
            for k in contours if cv2.contourArea(k) >= 64]    # no specks or pinholes under a screen pixel


def densify(pts, step):
    """A closed (u, h) outline with no edge longer than step, so it bends with the surface it is wrapped on."""
    out = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        n = max(1, math.ceil(math.dist(a, b) / step))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    return out


def flagstones(rng):
    """Stones fitted across the band, in (degrees, degrees up) at MARBLE_ASPECT: the cells round seeds
    jittered off a staggered grid, each drawn in by the grout."""
    pitch, top = MARBLE_STONE, MARBLE_ASPECT
    rows = MARBLE_ROWS
    seeds = [np.array([d + rng.uniform(-0.35, 0.35) * pitch, (r + 0.5 + rng.uniform(-0.3, 0.3)) * top / rows])
             for r in range(rows) for d in np.arange(-90 + (r % 2) * pitch / 2, 90 + pitch, pitch)]
    stones = []
    for s in seeds:
        cell = [np.array(v, float) for v in ((-90, 0), (90, 0), (90, top), (-90, top))]
        for o in seeds:
            if o is not s and np.linalg.norm(o - s) < 3 * pitch:
                cell = half_plane(cell, s, o)
        if len(cell) < 3:
            continue
        mid = np.mean(cell, axis=0)
        k = max(0.0, 1 - MARBLE_GROUT / (pitch / 2))
        stones.append([tuple(mid + (v - mid) * k) for v in cell])
    return stones


def chaikin(pts, rounds=2):
    for _ in range(rounds):
        pts = [q for a, b in zip(pts, pts[1:] + pts[:1])
               for q in ((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]),
                         (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))]
    return pts


def body_marble(out, scene, c, body, h0, h1):
    """The flagstones behind the strapwork: mint on the lit left turning slate blue on the right, each
    stone with softened corners, a darker lower-right rim and a dark grout seam round it."""
    rng = random.Random(7)
    P = lambda pts: [trim_uv(body, h0, h1, max(-89.5, min(89.5, d)), f) for d, f in pts]
    clip = lambda pts: [(d, max(0.0, min(1.0, f))) for d, f in pts]
    W = lambda pts: wrapped(scene, c, body, P(clip(pts)), 89.5)
    for name, d0, d1, f0, f1, fill in MARBLE_FIELDS:
        edge = [(d0, f0)] + [(d0 + rng.uniform(-4, 4), f) for f in np.linspace(f0 + 0.2, f1 - 0.2, 4)] + \
               [(d0, f1), (d1, f1), (d1, f0)]
        out.shape('body marble ' + name, W(catmull(edge, 3)), fill)
    shade, share, (sd, sf) = MARBLE_BEVEL
    ink, darken, width = MARBLE_SEAM
    rims, tops = {}, {}
    for stone in flagstones(rng):
        shape = chaikin([(d, g / MARBLE_ASPECT) for d, g in stone])
        cd, cf = np.mean(shape, axis=0)
        hue = marble_hue(cd)
        rims.setdefault(mix(hue, ink, shade), []).append(poly(W(shape)))
        top = [(cd + (x - cd) * share + sd, cf + (y - cf) * share + sf) for x, y in shape]
        tops.setdefault(hue, []).append(poly(W(top)))
    for i, (fill, paths) in enumerate(sorted(rims.items())):
        out.add(Shape('body marble cells %d' % (i + 1), ' '.join(paths), fill, mix(fill, ink, darken), width))
    for i, (fill, paths) in enumerate(sorted(tops.items())):
        out.add(Shape('body marble cell tops %d' % (i + 1), ' '.join(paths), fill))


def trim_straps(body, h0, h1, s):
    """One side's straps (s -1 left, 1 right) as (name, band, sheen) in (u, h), drawn in this order."""
    side = 'left' if s < 0 else 'right'
    straps = [('strap ' + side, [TRIM_LOW, TRIM_ARCH]), ('swag ' + side, [TRIM_SWAG])]
    for name, runs in straps:
        pts, width = [], TRIM_STRAP
        for run in runs:     # each run smoothed on its own, so the strap turns sharply where they meet
            run = catmull([trim_uv(body, h0, h1, s * -d, f) for d, f in run], 6, closed=False)
            pts += run[1:] if pts else run
        top = [(u, h + width * 0.24) for u, h in strap(pts[2:-2], width * 0.22)]
        yield name, above_foot(strap(pts, width), h0), above_foot(top, h0)


def above_foot(pts, h0):
    """The part of a (u, h) outline at or above the body's foot, so no gold hangs onto the plinth."""
    return [tuple(v) for v in half_plane([np.array(v, float) for v in pts], np.array([0.0, h0 + 1]),
                                         np.array([0.0, h0 - 1]))]


def body_trim(out, scene, c, body, h0, h1):
    """The gold strapwork on the body, as on the reference: per side a post at the end, a pointed arch
    bent over stone beside it, a strap curving from the rim into the gem frame and one sagging from the
    frame up into the arch's right leg, so every strap ends on gold; a dark gap shows between the upper
    strap, the rim and the frame. A side's straps and post are one path of gold, their union, so no
    strap's outline crosses another's face."""
    P = lambda pts: [trim_uv(body, h0, h1, d, f) for d, f in pts]
    lim = 89
    for side, s in (('left', -1), ('right', 1)):
        m = lambda pts: [(s * -d, f) for d, f in pts]
        out.shape('trim gap %s' % side, wrapped(scene, c, body, P(m(TRIM_SHADOW)), lim), TRIM_GAP)
        face = 'gold-face' if s < 0 else 'gold-face-shade'
        out.gradients['gold-face-shade'] = GOLD_FACE_SHADE
        straps = list(trim_straps(body, h0, h1, s))
        d0, d1 = TRIM_POST
        post = P([(s * d0, 0.0), (s * d1, 0.0), (s * d1, 1.02), (s * d0, 1.02)])
        gold = [densify(o, 0.005) for o in union([band for _, band, _ in straps] + [post])]
        out.add(Shape('trim gold %s' % side, ' '.join(poly(wrapped(scene, c, body, o, lim)) for o in gold),
                      face, OUTLINE['gold'], 2.5))
        for name, _, top in straps:
            out.shape('trim %s sheen' % name, wrapped(scene, c, body, top, lim),
                      GOLD_SHEEN if s < 0 else '#ffe48a')
        inner = d0 + 3
        sheen = [(s * inner, 0.08), (s * (inner + 5), 0.08), (s * (inner + 5), 0.95), (s * inner, 0.95)]
        if s < 0:
            out.shape('trim post %s sheen' % side, wrapped(scene, c, body, P(sheen), lim), GOLD_SHEEN)
        shade = [(s * (d1 - 9), 0.0), (s * d1, 0.0), (s * d1, 1.0), (s * (d1 - 9), 1.0)]
        out.shape('trim post %s shade' % side, wrapped(scene, c, body, P(shade), lim), GOLD_SHADE)


def crystal_bases(c):
    for name, (dx, dz), h0, radius, length, tip, (lx, lz), rot, shift, shoulders, pal in CRYSTALS:
        yield name, c + np.array([dx, h0, dz]), np.array([lx, 1.0, lz]), radius, length, tip, rot, shift, shoulders, pal


def crystal_bush_spec():
    """The crystal planter's bushes: their leaf size and flower size, the middle of the soil and the rim's ring."""
    rig, R = CRYSTAL_FIT
    hr1, rr1 = R['rim top']
    rim = ring(rig, rig.c, hr1, rr1, 96)
    x0, y0, x1, y1 = ellipse_box(rim)
    k = depth_scale(rig, rig.c)
    return LEAF_SIZE * k * CRYSTAL_LEAF, FLOWER_SIZE * k, ((x0 + x1) / 2, (y0 + y1) / 2 + 2), rim


def crystal_plants():
    """The back bush, then the front."""
    leaf, _, base, rim = crystal_bush_spec()
    floor = front_edge(rim)
    return (plant('crystal planter back bush', T.CRYSTAL_BUSH, base, leaf * CRYSTAL_TIER_BIG, floor, 21),
            plant('crystal planter front bush', T.CRYSTAL_FRONT_BUSH, base, leaf, floor, 28))


def crystal_planter(out, scene):
    rig, R = CRYSTAL_FIT
    c = rig.c
    (hp0, rp0), (hp1, rp1) = R['plinth bottom'], R['plinth top']
    (hb0, _), (hb1, _) = R['body bottom'], R['body top']
    (hr0, rr0), (hr1, rr1) = R['rim bottom'], R['rim top']
    plinth = profile(R, ('plinth bottom', 'plinth top'))
    body = profile(R, ('body bottom', 'body top'))

    def rim_radius(h):
        t = max(0.0, min(1.0, (h - hr0) / (hr1 - hr0)))
        return rr0 + (rr1 - rr0) * t + RIM_BULGE * math.sin(math.pi * t) ** 0.6

    out.open('Crystal planter')
    out.open('crystal planter floor contact')
    floor_contact(out, rig, c, hp0, rp0, 'plinth')
    out.close()
    out.open('crystal planter pot')
    out.shape('plinth', lathe(rig, plinth, hp0, hp1), 'gold-face', 'gold')
    mid = (hp0 + hp1) / 2
    out.shape('plinth sheen', wrapped(rig, c, plinth, [(u, mid + 0.002) for u in np.linspace(-0.9, 0.5, 30)]
                                      + [(u, mid + 0.008) for u in np.linspace(0.5, -0.9, 30)], VISIBLE_ANGLE),
              '#fff2a0')
    side_shade(out, rig, c, plinth, hp0, hp1, 'plinth', 'gold-face', 'gold')
    out.shape('plinth top', ring(rig, c, hp1, rp1, 96), 'gold', 'gold', 2.5)
    out.shape('body', lathe(rig, body, hb0, hb1), 'marble', 'turquoise')
    body_marble(out, rig, c, body, hb0, hr0)
    out.open('body lattice')
    body_trim(out, rig, c, body, hb0, hr0)
    out.close()
    occlusion(out, rig, c, body, hr0, 'body under rim', 'grout')
    out.shape('rim band', lathe(rig, rim_radius, hr0, hr1), 'gold', 'gold')
    out.shape('rim shade', wrapped(rig, c, rim_radius, [(u, hr0 + 0.004) for u in np.linspace(-0.8, 0.8, 30)]
                                   + [(u, hr0 + 0.016) for u in np.linspace(0.8, -0.8, 30)], VISIBLE_ANGLE), '#e6a23a')
    side_shade(out, rig, c, rim_radius, hr0, hr1, 'rim band', 'gold', 'gold')
    out.shape('rim sheen', wrapped(rig, c, rim_radius, [(u, hr1 - 0.008) for u in np.linspace(-0.85, 0.3, 30)]
                                   + [(u, hr1 - 0.02) for u in np.linspace(0.3, -0.85, 30)], VISIBLE_ANGLE), GOLD_SHEEN)
    out.shape('rim top', ring(rig, c, hr1, rr1, 96), 'gold-pale', 'gold')
    out.shape('soil', ring(rig, c, hr1, rr1 - PLANTER_LIP, 96), 'soil', '#245e26')
    out.close()

    x0, y0, x1, y1 = ellipse_box(ring(rig, c, hr1, rr1, 96))
    k = depth_scale(rig, c)
    leaf, fl = LEAF_SIZE * k, FLOWER_SIZE * k
    cx, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
    base = (cx, mid_y + 2)
    leaf *= CRYSTAL_LEAF
    back_plant, front_plant = crystal_plants()
    out.open('crystal planter back bush')
    bush_with_pieces(out, back_plant, foliage.bush(
        'crystal back', base, 0, 0, 0.8, 21, leaf * CRYSTAL_TIER_BIG, fl, flowers=2, whites=2, spill=0.0, variety=1.0,
        white_size=CRYSTAL_WHITE_SIZE, whites_on_top=False, two_tone=True, flower_band=(0.35, 0.7), flower_phi=(1.0, 2.1),
        silhouette=T.CRYSTAL_BUSH, sweep=CRYSTAL_SWEEP, mass_floor=base[1] + 2, rings=[], leaves=False))
    out.close()

    out.open('crystals')
    for name, b, axis, radius, length, tip, rot, shift, shoulders, pal in sorted(crystal_bases(c), key=lambda q: -q[1][2]):
        crystal(out, rig, name, b, axis, radius, length, tip, rot, shift, shoulders, pal)
    out.close()

    out.open('crystal base leaves')
    rng = random.Random(23)
    for i, (tip, size) in enumerate(CRYSTAL_BASE_LEAVES):
        ang = math.atan2(tip[1] - base[1], tip[0] - cx)
        length = math.dist(tip, (cx, base[1])) / 0.97 * size
        b = (tip[0] - math.cos(ang) * length * 0.97, tip[1] - math.sin(ang) * length * 0.97)
        out.add_all(foliage.leaf('crystal base leaf %d' % i, b, ang, length, 'leaf-light', rng=rng,
                                 shade=foliage.LEAF_SHADE_DEEP['leaf-light']))
    out.close()

    front = T.CRYSTAL_FRONT_BUSH
    rim_front = sorted(((x, y + 1.5) for x, y in ring(rig, c, hr1, rr1, 96) if y > mid_y), key=lambda p: p[0])  # over the lip
    out.open('crystal planter front bush')
    bush_with_pieces(out, front_plant, foliage.bush(
        'crystal front', base, 0, 0, 1.0, 28, leaf, fl * 1.3, flowers=7, whites=0, spill=0.0, variety=1.0,
        white_size=CRYSTAL_WHITE_SIZE, whites_on_top=True, two_tone=True, rings=CRYSTAL_RINGS_FRONT,
        flower_band=(0.45, 0.95), silhouette=front, sweep=CRYSTAL_SWEEP, mass_base=rim_front, leaves=False))
    wrng = random.Random(30)
    for i, wc in enumerate(CRYSTAL_FRONT_WHITES):
        out.add_all(foliage.flower('crystal front set white flower %d' % i, wc, CRYSTAL_FRONT_WHITE_R,
                                   wrng.uniform(0, 2 * math.pi), 0.9, True, stroke=2.0))
    out.close()
    out.open('crystal planter rim leaves')     # the front row lying over the rim's top edge
    rng = random.Random(29)
    for i in range(CRYSTAL_RIM_LEAVES):
        u = (i + 0.5) / CRYSTAL_RIM_LEAVES * 2 - 1
        tx = cx + u * (x1 - x0) / 2 * 0.78 + rng.uniform(-4, 4)
        ty = min(rim_front, key=lambda q: abs(q[0] - tx))[1] + rng.uniform(-1, 2)
        ang = math.pi / 2 - u * 1.0 + rng.uniform(-0.2, 0.2)
        length = leaf * rng.uniform(*CRYSTAL_TIER_SMALL)
        b = (tx - math.cos(ang) * length * 0.97, ty - math.sin(ang) * length * 0.97)
        tone = rng.choice(['leaf-light', 'leaf-dark', 'leaf-dark'])
        out.add_all(foliage.leaf('crystal rim leaf %d' % i, b, ang, length, tone, rng=rng,
                                 shade=foliage.LEAF_SHADE_DEEP[tone]))
    out.close()
    out.open('crystal planter side leaves')
    for i, (b, tip) in enumerate(T.CRYSTAL_SIDE_LEAVES):
        ang = math.atan2(tip[1] - b[1], tip[0] - b[0])
        out.add_all(foliage.leaf('crystal side leaf %d' % i, b, ang, math.dist(b, tip) / 0.97,
                                 'leaf-back' if i % 2 else 'leaf-dark', rng=rng))
    out.close()

    out.open('crystal planter gem')
    gem_r = lambda h: rr1 + GEM_FRAME_STANDOFF + 0.002
    fw, fhh = diamond_uv(rig, gem_r, T.CRYSTAL_GEM_FRAME)[2:]
    gu, gh, gw, ghh = diamond_uv(rig, gem_r, T.CRYSTAL_GEM)
    gem(out, rig, c, gem_r, 'front gem', gu, gh, gw, ghh, outer=(fw, fhh))
    out.close()
    out.close()
    return c


# ---------------------------------------------------------------- urns

def soil_patch(scene, c, rim_h, inner_r, drop, n=72):
    """The soil disc sunk drop below the rim, cut to the part seen through the rim opening: each soil point
    is pulled in to the opening's outline where it would show in front of the rim."""
    rim = ring(scene, c, rim_h, inner_r, n)
    soil = ring(scene, c, rim_h - drop, inner_r * 0.97, n)
    cy = sum(p[1] for p in rim) / n
    out = []
    for (sx, sy), (rx, ry) in zip(soil, rim):
        out.append((sx, min(sy, ry) if ry > cy else sy))
    return out


def urn_radius(h):
    """Left urn radius at height h (shadows.py)."""
    for _, h0, h1, f, _, _ in URN_PROFILE:
        if h0 <= h <= h1:
            return f((h - h0) / (h1 - h0))
    return URN_PROFILE[-1][3](1.0)


def upright_urn(rings, gem, rim_gem):
    """The reference's urn leans (its foot stands left of its bowl) and its gems sit off its middle. Each urn
    is drawn upright and mirror-symmetric instead, only the light differing side to side: every ring and both
    gems are stood on the axis of URN_AXIS_RING, which keeps the rim and the bush on it where they were
    measured. Returns (rings, gem, rim gem)."""
    x = rings[URN_AXIS_RING]['cx']
    return ({name: dict(ring, cx=x) for name, ring in rings.items()}, dict(gem, centre=(x, gem['centre'][1])),
            dict(rim_gem, centre=(x, rim_gem['centre'][1])))


LEFT_URN = upright_urn(T.LEFT_URN_RINGS, T.LEFT_URN_GEM, T.LEFT_URN_RIM_GEM)
RIGHT_URN = upright_urn(T.RIGHT_URN_RINGS, T.RIGHT_URN_GEM, T.RIGHT_URN_RIM_GEM)
URN_TARGETS = {     # group: (fitted rig, bowl gem, rim gem, bush outline)
    'Left urn': ('LEFT_URN_FIT', LEFT_URN[1], LEFT_URN[2], T.LEFT_URN_BUSH),
    'Right urn': ('RIGHT_FIT', RIGHT_URN[1], RIGHT_URN[2], T.RIGHT_URN_BUSH),
}


URN_SEEDS = {'Right urn': 41, 'Left urn': 31}


def urn_bush_spec(group):
    """The urn's bush: its leaf size, the middle of its soil and the screen ring of its rim."""
    fit, _, _, bush_outline = URN_TARGETS[group]
    rig, R = globals()[fit]
    rim_h, rim_r = R['rim top']
    rim = ring(rig, rig.c, rim_h, rim_r, 72)
    x0, y0, x1, y1 = ellipse_box(rim)
    k = depth_scale(rig, rig.c)
    return LEAF_SIZE * k * URN_BUSH_LEAF, FLOWER_SIZE * k * 1.15, ((x0 + x1) / 2, (y0 + y1) / 2), rim


def urn_plant(group, seed):
    leaf, _, base, rim = urn_bush_spec(group)
    return plant(group.lower() + ' bush', URN_TARGETS[group][3], base, leaf, front_edge(rim), seed)


def urn(out, scene, group, seed):
    fit, bowl_gem, rim_gem, bush_outline = URN_TARGETS[group]
    rig, R = globals()[fit]
    c = rig.c
    out.open(group)
    out.open(group + ' floor contact')
    foot_r = profile(R, URN_PARTS[0][1])
    floor_contact(out, rig, c, R[URN_PARTS[0][1][0]][0], foot_r(R[URN_PARTS[0][1][0]][0]), group + ' foot')
    out.close()
    out.open(group + ' pot')
    radii = {}
    for part, names, paint, outline in URN_PARTS:
        r = profile(R, names)
        h0, h1 = R[names[0]][0], R[names[-1]][0]
        radii[part] = (r, h0, h1)
        out.shape('%s %s' % (group, part), lathe(rig, r, h0, h1), paint, outline)
        if part in ('foot', 'collar', 'rim'):
            side_shade(out, rig, c, r, h0, h1, '%s %s' % (group, part), paint, outline)
        if part == 'foot':
            mid = (h0 + h1) / 2
            out.shape(group + ' foot sheen', top_left_sheen(rig, c, r, h1, 0.003, 0.007), GOLD_SHEEN)
            out.shape(group + ' foot top surface', ring(rig, c, h1, r(h1), 72), 'gold-pale', 'gold', 2)
        if part == 'stem':
            flutes = []
            for kk in range(-3, 4):
                a = kk * 0.36
                strip = [(a * r(h) - 0.003, h) for h in np.linspace(h0 + 0.006, h1 - 0.004, 6)] + \
                        [(a * r(h) + 0.003, h) for h in np.linspace(h1 - 0.004, h0 + 0.006, 6)]
                flutes.append(poly(wrapped(rig, c, r, strip, 75)))
            out.add(Shape(group + ' stem flutes', ' '.join(flutes), FLUTE))
            side_shade(out, rig, c, r, h0, h1, group + ' stem', paint, outline)
            occlusion(out, rig, c, r, h1, group + ' stem under collar', paint)
        if part == 'collar':
            hm = R['collar mid'][0]
            out.shape(group + ' collar sheen', top_left_sheen(rig, c, r, hm + 0.006, 0.001, 0.005), GOLD_SHEEN)
            occlusion(out, rig, c, r, h1, group + ' collar under bowl', paint, OCCLUSION_DEPTH * 0.7)
        if part == 'bowl':
            bowl = r
            flutes = []
            for kk in range(-URN_FLUTES // 2 + 1, URN_FLUTES // 2 + 1):
                a = kk * math.radians(165 / URN_FLUTES)
                hs = np.linspace(h0 + 0.02, h1 - 0.012, 10)
                strip = [(a * bowl(h) - 0.009, h) for h in hs] + [(a * bowl(h) - 0.003, h) for h in hs[::-1]]
                flutes.append(poly(wrapped(rig, c, bowl, strip, 82)))
            out.add(Shape(group + ' bowl flutes', ' '.join(flutes), FLUTE))
            hw = R['bowl widest'][0]
            for i, share in enumerate(OCCLUSION_STEPS):     # the belly rounding under towards the collar
                out.shape('%s bowl underside %d' % (group, i + 1),
                          turned_band(rig, c, r, h0, h0 + (hw - h0) * URN_UNDERSIDE * share, -SHADE_EDGE, SHADE_EDGE, 48),
                          OCCLUSION['cream'], opacity=OCCLUSION_ALPHA)
            side_shade(out, rig, c, r, h0, h1, group + ' bowl', paint, outline)
            gu, gh, gw, gg = gem_uv(rig, bowl, *bowl_gem.values())
            gem(out, rig, c, bowl, group + ' bowl gem', gu, gh, gw, gg)
            occlusion(out, rig, c, bowl, h1, group + ' bowl under rim', 'cream')
        if part == 'rim':
            rim = r
            out.shape(group + ' rim sheen', wrapped(rig, c, rim, [(u, h1 - 0.012) for u in np.linspace(-0.45, 0.1, 24)]
                                                     + [(u, h1 - 0.02) for u in np.linspace(0.1, -0.45, 24)], 80),
                      GOLD_SHEEN)
            gu, gh, gw, gg = gem_uv(rig, rim, *rim_gem.values())
            gem(out, rig, c, lambda h: rim(h) + 0.003, group + ' rim gem', gu, gh, gw, gg, 2, outer=(gw * 1.4, gg * 1.4))
    rim_h, rim_r = R['rim top']
    out.shape(group + ' rim top', ring(rig, c, rim_h, rim_r, 72), 'gold-pale', 'gold')
    inner_r = rim_r - URN_RIM_LIP
    out.gradients['urn-interior'] = URN_INTERIOR
    out.shape(group + ' interior', ring(rig, c, rim_h, inner_r, 72), 'urn-interior', 'gold', 2)
    out.shape(group + ' soil', soil_patch(rig, c, rim_h, inner_r, URN_SOIL_DROP), 'soil')
    out.close()

    leaf, fl, base, rim_ring = urn_bush_spec(group)
    x0, y0, x1, y1 = ellipse_box(rim_ring)
    out.open(group + ' bush')
    shapes = foliage.bush(
        group, base, 0, 0, URN_BUSH_DENSITY, seed, leaf, fl, flowers=8, whites=5, spill=0.0,
        flower_band=(0.3, 0.92), silhouette=bush_outline, sweep=(-0.35, math.pi + 0.35), mass_floor=base[1] + 3,
        leaves=False)
    # only the library pieces and the flowers: no dark mass, nor the flower stems that ran back into it
    bush_with_pieces(out, urn_plant(group, seed),
                     [s for s in shapes if s.fill != 'bush-mass' and ' flower stem' not in s.name])
    out.close()
    out.open(group + ' rim leaves')
    rng = random.Random(URN_SPILL_SEED + 100)
    cx, a, b = (x0 + x1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    pairs = [(u, turn + rng.uniform(-0.12, 0.12), size, rng.choice(['leaf-dark', 'leaf-dark', 'leaf-back']),
              rng.uniform(-foliage.LEAF_BEND, foliage.LEAF_BEND)) for u, turn, size in URN_RIM_LEAVES]
    leaves = sorted([(side * u, turn, size, tone, side * bend) for u, turn, size, tone, bend in pairs
                     for side in (-1, 1)])
    for i, (u, turn, size, tone, bend) in enumerate(leaves):
        by = (y0 + y1) / 2 + b * math.sqrt(max(0.0, 1 - u * u)) - 3
        out.add_all(foliage.leaf('%s rim leaf %d' % (group, i + 1), (cx + u * a, by - leaf * 0.25),
                                 math.pi / 2 - math.copysign(turn, u), leaf * size * 0.85, tone, bend=bend, rng=rng,
                                 gloss=True))
    out.close()
    out.close()
    return c


# ---------------------------------------------------------------- corner bush
CORNER_LEAF = 64.0             # leaf length, px: big leaves, as on the reference
CORNER_EDGE_EVERY = 85.0       # px of outline between the branches round the edge
CORNER_EDGE_SCALE = 1.3
CORNER_EDGE_TURN = math.radians(15)    # an edge branch points up to this far off straight out from the soil
CORNER_FACE_STEP = 64.0        # px between the rosettes covering the face
CORNER_FACE_SCALE = (1.3, 1.5)         # a face rosette's scale at the bush's top and at its foot
CORNER_RIM_SCALE = 1.45


@dataclass
class Spacing:
    """How far apart a plant's pieces grow, as shares of the corner bush's first spacing; gaps are the
    nearest a piece may stand to another of its kind, in its own leaf lengths."""
    face_step: float = 1.0
    edge_every: float = 1.0
    face_gap: float = 0.0
    edge_gap: float = 0.0


# as the corner bush was thinned by hand: face rosettes 0.8 of a leaf length apart or more, edge branches 0.85
THINNED = Spacing(face_step=1.33, edge_every=1.75, face_gap=0.8, edge_gap=0.85)


@dataclass
class Plant:
    name: str
    layout: list
    outline: list
    focus: tuple
    leaf: float


def dense_run(points):
    """The polyline through points, a point every px."""
    out = []
    for a, b in zip(points, points[1:]):
        n = max(1, int(math.dist(a, b)))
        out += [(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n) for t in range(n)]
    return out


def bush_layout(outline, focus, leaf, floor, seed, edge_run, rim_at=(), spacing=Spacing()):
    """A bush as library pieces (branches.Placement) filling the closed screen outline round its soil's middle
    (focus): branches round the edge (along edge_run) pointing out from the soil, rosettes covering the face,
    painted top down and growing larger towards the foot, nearer the viewer, then large rosettes spilling
    forward over the pot's rim at the x in rim_at. leaf is the bush's leaf length, CORNER_LEAF giving the
    corner bush's sizes; floor(x) is the screen y of the rim's front, which the face stays above."""
    rng = random.Random(seed)
    k = leaf / CORNER_LEAF
    fx, fy = focus
    library = {p.id: p for p in branches.library()}
    by_size = {}
    for pid in library:
        kind, size_name = pid.split('-')[:2]
        by_size.setdefault((kind, size_name), []).append(pid)

    def up(pid):
        return -min(d.base[1] + math.sin(d.angle) * d.length for d in library[pid].draws)

    def down(pid):
        return max(d.base[1] + math.sin(d.angle) * d.length for d in library[pid].draws)

    def leaf_size(p):
        kind, size_name = p.piece.split('-')[:2]
        sizes = branches.ROSETTE_SIZES if kind == 'rosette' else branches.BRANCH_SIZES
        return sizes[size_name][1 if kind == 'rosette' else 0] * p.scale

    def crowded(p, others, gap):
        return any(math.dist(p.at, q.at) < gap * leaf_size(p) for q in others)

    layout = []
    # round the edge: each branch's tip near the outline, its foot back towards the soil
    points = dense_run(edge_run)
    every = CORNER_EDGE_EVERY * k * spacing.edge_every
    edge_scale = CORNER_EDGE_SCALE * k
    for i in range(int(len(points) / every)):
        tx, ty = points[int((i + rng.uniform(0.35, 0.65)) * every)]
        out = math.atan2(ty - fy, tx - fx) + rng.uniform(-CORNER_EDGE_TURN, CORNER_EDGE_TURN)
        room = math.hypot(tx - fx, ty - fy) * 0.8
        fits = [pid for size_name in ('large', 'medium', 'small') for pid in by_size['branch', size_name]
                if up(pid) * edge_scale <= room and 'sparse' not in pid]
        pid = rng.choice(fits[:3]) if fits else 'branch-small-dense-1'
        scale = min(edge_scale, room / up(pid))
        reach = up(pid) * scale * 0.95
        at = (tx - math.cos(out) * reach, ty - math.sin(out) * reach)
        p = branches.Placement(pid, at, math.atan2(math.cos(out), -math.sin(out)), scale, rng.random() < 0.5, 'edge')
        if not crowded(p, layout, spacing.edge_gap):
            layout.append(p)

    # the face: a jittered grid of rosettes, kept off the outline and above the rim
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    top, foot = min(ys), floor(fx)
    step = CORNER_FACE_STEP * k * spacing.face_step
    face = []
    y, row = top + step * 0.6, 0
    while y < foot:
        x = min(xs) + (step * 0.5 if row % 2 else 0.0)
        while x < max(xs):
            px, py = x + rng.uniform(-0.25, 0.25) * step, y + rng.uniform(-0.25, 0.25) * step
            t = max(0.0, min(1.0, (py - top) / (foot - top)))
            size_name = 'small' if t < 0.3 else 'medium' if t < 0.65 else 'large'
            pid = rng.choice(by_size['rosette', size_name])
            scale = (CORNER_FACE_SCALE[0] + (CORNER_FACE_SCALE[1] - CORNER_FACE_SCALE[0]) * t) * k
            if foliage._edge_distance(outline, px, py) > 0.12 * branches.ROSETTE_SIZES[size_name][1] * scale \
                    and py + down(pid) * scale * 0.55 < floor(px):
                p = branches.Placement(pid, (px, py), rng.uniform(-0.35, 0.35), scale, rng.random() < 0.5, 'face')
                if not crowded(p, face, spacing.face_gap):
                    face.append(p)
            x += step
        y += step * 0.87
        row += 1
    layout += sorted(face, key=lambda p: p.at[1])

    # over the rim: large rosettes just above its front, nearest the viewer, their lower leaves spilling over it
    for x in rim_at:
        pid = rng.choice(by_size['rosette', 'large'])
        x += rng.uniform(-6, 6)
        at = (x, floor(x) - branches.ROSETTE_SIZES['large'][1] * CORNER_RIM_SCALE * k * 0.4)
        layout.append(branches.Placement(pid, at, rng.uniform(-0.3, 0.3), CORNER_RIM_SCALE * k, rng.random() < 0.5,
                                         'rim'))
    return layout


def front_edge(rim):
    """floor(x) for a pot's rim (its screen ring): the y of its front edge, held level past its ends."""
    cy = sum(p[1] for p in rim) / len(rim)
    front = sorted((p for p in rim if p[1] >= cy), key=lambda p: p[0])
    xs, ys = [p[0] for p in front], [p[1] for p in front]
    return lambda x: float(np.interp(x, xs, ys))


def upper_run(outline, focus, leaf):
    """The part of a closed outline above its soil, where its edge branches grow, from its lowest point round."""
    closed = dense_run(outline + outline[:1])
    low = max(range(len(closed)), key=lambda i: closed[i][1])
    closed = closed[low:] + closed[:low]
    return [p for p in closed if p[1] < focus[1] - leaf * 0.25]


def plant(name, outline, focus, leaf, floor, seed):
    """A plant laid out like the hand-thinned corner bush, nothing spilling over its rim."""
    focus, leaf = (float(focus[0]), float(focus[1])), float(leaf)
    return Plant(name, bush_layout(outline, focus, leaf, floor, seed, upper_run(outline, focus, leaf), (), THINNED),
                 outline, focus, leaf)


def add_pieces(out, name, layout):
    """Each placed library piece as a group the scene places by one ref: <name> <role> <n>."""
    library = {p.id: p for p in branches.library()}
    for i, p in enumerate(layout):
        gid = '%s %s %d' % (name, p.role, i + 1)
        out.piece(gid, p)
        out.add_all(branches.shapes(branches.Piece(gid, branches.placed(library[p.piece], p))))
        out.close()


def bush_with_pieces(out, plant, shapes):
    """A foliage.bush drawn without its leaves (shapes) round the plant's library pieces: its mass behind them,
    its flowers and buds over them."""
    out.add_all([s for s in shapes if s.fill == 'bush-mass'])
    add_pieces(out, plant.name, plant.layout)
    out.add_all([s for s in shapes if s.fill != 'bush-mass'])


def plant_layouts():
    """Every plant laid out from library pieces but the corner bush, by name."""
    plants = [urn_plant(group, seed) for group, seed in URN_SEEDS.items()] + list(crystal_plants())
    return {p.name: p for p in plants}


# ---------------------------------------------------------------- fitted pots and the names shadows.py reads

SCENE = Scene()
CRYSTAL_FIT = fit_rig(SCENE, T.CRYSTAL_RINGS)
LEFT_URN_FIT = fit_rig(SCENE, LEFT_URN[0], upright=True)
RIGHT_FIT = fit_rig(SCENE, RIGHT_URN[0], upright=True)

_R = CRYSTAL_FIT[1]
PLANTER_BASE = (_R['plinth bottom'][1], _R['plinth top'][0])        # radius, height
PLANTER_STEP = (_R['body bottom'][1], _R['body bottom'][0])
PLANTER_BODY = (_R['body top'][1], _R['body top'][0])
PLANTER_RIM = (_R['rim top'][1], _R['rim top'][0])
CRYSTAL_PLANTER_SCREEN = real_screen(SCENE, CRYSTAL_FIT[0], PLANTER_BASE[0])

_R = LEFT_URN_FIT[1]
URN_PROFILE = []
for _part, _names, _paint, _outline in URN_PARTS:
    _h0, _h1 = _R[_names[0]][0], _R[_names[-1]][0]
    _f = profile(_R, _names)
    URN_PROFILE.append((_part, _h0, _h1, (lambda f, h0, h1: lambda t: f(h0 + (h1 - h0) * t))(_f, _h0, _h1),
                        _paint, _outline))
LEFT_URN_SCREEN = real_screen(SCENE, LEFT_URN_FIT[0], URN_PROFILE[0][3](0))
RIGHT_URN_SCREEN = real_screen(SCENE, RIGHT_FIT[0], URN_PROFILE[0][3](0))


# ---------------------------------------------------------------- check against the reference

def crystal_landmarks(rig):
    """Screen tip and shoulders of each crystal, named as in planters_reference.CRYSTAL_POINTS."""
    out = {}
    for name, base, axis, radius, length, tip, rot, shift, shoulders, _ in crystal_bases(rig.c):
        a, e1, e2 = frame(axis)
        tops = [rig.project(base + radius * (math.cos(t) * e1 + math.sin(t) * e2) + a * length * s)
                for t, s in zip([math.radians(rot + 60 * k) for k in range(6)], shoulders)]
        pts = dict(tip=rig.project(base + a * (length + tip) + shift * e1),
                   shoulder_left=min(tops, key=lambda p: p[0]), shoulder_right=max(tops, key=lambda p: p[0]),
                   ridge=max(tops, key=lambda p: p[1]))
        out[name] = {k: pts[k] for k in T.CRYSTAL_POINTS[name]}
    return out


# ---------------------------------------------------------------- check, on the rendered SVG
# Every measurement is taken from planters.svg as rendered by qlmanage,
# with only some of its groups kept, so the check sees exactly what gets drawn.
CHECK_OBJECTS = {     # object: (pot groups, foliage groups, groups drawn over the foliage, ring targets)
    'crystal planter': (['crystal planter pot'], ['crystal planter back bush', 'crystal base leaves',
                        'crystal planter front bush', 'crystal planter rim leaves', 'crystal planter side leaves'],
                        ['crystals', 'crystal planter gem'], T.CRYSTAL_RINGS),
    'left urn': (['Left urn pot'], ['Left urn bush', 'Left urn rim leaves'], [], LEFT_URN[0]),
    'right urn': (['Right urn pot'], ['Right urn bush', 'Right urn rim leaves'], [], RIGHT_URN[0]),
}
BUSH_OUTLINES = {'crystal planter': T.CRYSTAL_BUSH, 'left urn': T.LEFT_URN_BUSH, 'right urn': T.RIGHT_URN_BUSH}
STROKE_OUT = STROKE / 2          # a rendered edge sits half a stroke outside its path


def render(ids, svg=cutting.sheet_path('furniture/planters.svg')):
    """planters.svg rendered with only the groups in ids (and what they contain); returns RGB and a mask
    of the drawn pixels, both 1536 x 1024."""
    import subprocess, tempfile
    import xml.etree.ElementTree as ET
    ns = 'http://www.w3.org/2000/svg'
    ET.register_namespace('', ns)
    root = ET.parse(svg).getroot()
    keep = set()
    for g in root.iter('{%s}g' % ns):
        if g.get('id') in ids:
            keep |= set(map(id, g.iter()))

    def prune(el):
        for ch in list(el):
            if ch.tag.endswith('defs') or id(ch) in keep:
                continue
            if any(id(e) in keep for e in ch.iter()):
                prune(ch)
            else:
                el.remove(ch)
    prune(root)
    root.set('height', '1536')
    root.set('viewBox', '0 0 1536 1536')
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, 'check.svg')
    ET.ElementTree(root).write(path)
    subprocess.run(['qlmanage', '-t', '-s', '1536', '-o', tmp, path], capture_output=True, check=True)
    rgb = np.array(Image.open(path + '.png').convert('RGB'))[:1024].astype(int)
    return rgb, np.abs(rgb - 255).sum(axis=2) > 30


def ring_rows(mask, rings):
    """For each ring with a centre height: the rendered left and right edge at that row against cx -/+ a
    (+ = ours is wider on that side); for the bottom ring, also the lowest drawn pixel under its centre
    against its front (+ = ours lower)."""
    rows = []
    for name, w in rings.items():
        if 'cy' not in w:
            continue
        y, half = int(round(w['cy'])), max(1, int(round(w.get('b', 1))))
        lo, hi = int(w['cx'] - w['a'] - 30), int(w['cx'] + w['a'] + 30)
        xs = np.where(mask[y - half:y + half + 1, lo:hi].any(axis=0))[0] + lo     # a thin ring's ends wander a row
        if not len(xs):
            rows.append((name, [99.0]))
            continue
        rows.append((name, [(w['cx'] - w['a']) - (xs.min() + STROKE_OUT), (xs.max() - STROKE_OUT) - (w['cx'] + w['a'])]))
    bottom = max((w for w in rings.values() if 'b' in w and 'cy' in w), key=lambda w: w['cy'] + w['b'])
    col = mask[:, int(round(bottom['cx']))]
    ys = np.where(col)[0]
    rows.append(('front of the base', [ys.max() - STROKE_OUT - (bottom['cy'] + bottom['b'])]))
    return rows


def outline_errors(mask, over, outline):
    """Signed distance from each outline point to the rendered silhouette's edge (+ = ours sticks out past
    it); points off the frame or under something drawn over the foliage are skipped."""
    inside = ndimage.distance_transform_edt(mask)
    outside = ndimage.distance_transform_edt(~mask)
    errs = []
    for x, y in outline:
        if x < 0 or over[int(y), int(x)]:
            continue
        errs.append(inside[int(y), int(x)] if mask[int(y), int(x)] else -outside[int(y), int(x)])
    return errs


def crystal_show_rows():
    """Where each crystal disappears behind the bush: the lowest row in its x band whose rendered pixels
    are the crystal's own, against planters_reference.CRYSTAL_SHOW."""
    full, _ = render(['Crystal planter'])
    rows = []
    for name, (x0, x1, want) in T.CRYSTAL_SHOW.items():
        rgb, m = render([name])
        seen = m & (np.abs(rgb - full).sum(axis=2) < 12)
        ys = np.where(seen[:, x0:x1].sum(axis=1) >= 3)[0]      # a row counts once 3 px of it show
        rows.append((name + ' shows down to', [ys.max() - want]))
    return rows


def check():
    rows = []
    for obj, (pot, foliage_ids, over_ids, rings) in CHECK_OBJECTS.items():
        _, pot_mask = render(pot)
        for name, err in ring_rows(pot_mask, rings):
            rows.append((obj, 'pot at ' + name, err))
        _, leaves = render(foliage_ids)
        over = render(over_ids)[1] if over_ids else np.zeros_like(leaves)
        errs = outline_errors(leaves, over, BUSH_OUTLINES[obj])
        rows.append((obj, 'bush outline (%d pts)' % len(errs), errs))
    _, leaves = render(['crystal planter front bush', 'crystal planter rim leaves', 'crystal planter side leaves'])
    errs = outline_errors(leaves, np.zeros_like(leaves), T.CRYSTAL_FRONT_BUSH)
    rows.append(('crystal planter', 'front bush outline (%d pts)' % len(errs), errs))
    for name, err in crystal_show_rows():
        rows.append(('crystal planter', name, err))
    rig = CRYSTAL_FIT[0]
    for name, pts in crystal_landmarks(rig).items():
        for k, p in pts.items():
            t = T.CRYSTAL_POINTS[name][k]
            rows.append(('crystal planter', '%s %s' % (name, k), [p[0] - t[0], p[1] - t[1]]))
    worst = {}
    for obj, name, err in rows:
        m = max(abs(e) for e in err)
        worst[obj] = max(worst.get(obj, 0), m)
        print('%-17s %-34s max %5.1f   %s' % (obj, name, m, ' '.join('%+.1f' % e for e in err)))
    print()
    for obj, m in worst.items():
        print('%-20s worst %.1f px' % (obj, m))


def fit_crystals():
    """Least-squares the crystals' placement and size to planters_reference.CRYSTAL_POINTS; prints CRYSTALS."""
    global CRYSTALS
    rig = CRYSTAL_FIT[0]
    for idx, cr in enumerate(list(CRYSTALS)):
        name = cr[0]

        upright = name == 'big crystal'      # the reference's big crystal stands straight: no lean, and its
        # front ridge drops below the side shoulders, so it fits the front shoulder's height instead

        def build(v, cr=cr):
            dx, h0, radius, length, tip, lean, shift, rot = v
            shoulders = list(cr[9])
            if upright:
                shoulders[1] = lean
                lean = 0.0
            return (name, (dx, cr[1][1]), h0, radius, length, tip, (lean, cr[6][1]), rot, shift, tuple(shoulders),
                    cr[10])

        def res(v):
            CRYSTALS[idx] = build(v)
            got = crystal_landmarks(rig)[name]
            return [g - w for k in got for g, w in zip(got[k], T.CRYSTAL_POINTS[name][k])] + \
                   [0.02 * (v[7] - cr[7]), 20 * (v[0] - cr[1][0]) if upright else 0.0]
        v0 = [cr[1][0], cr[2], cr[3], cr[4], cr[5], cr[9][1] if upright else cr[6][0], cr[8], 30 if upright else cr[7]]
        lo = [-0.4, PLANTER_RIM[1] - 0.1, 0.04, 0.05, 0.03, 0.5 if upright else -1.5, -0.1, -60]
        hi = [0.4, PLANTER_RIM[1] - 0.01, 0.25, 0.9, 0.4, 1.1 if upright else 1.5, 0.1, 120]
        v0 = np.clip(v0, np.array(lo) + 1e-6, np.array(hi) - 1e-6)
        fit = least_squares(res, v0, bounds=(lo, hi))
        CRYSTALS[idx] = build(fit.x)
    for cr in CRYSTALS:
        print('    (%r, (%.3f, %.3f), %.3f, %.3f, %.3f, %.3f, (%.3f, %.3f), %d, %.3f,\n     %r, %r),' % (
            cr[0], cr[1][0], cr[1][1], cr[2], cr[3], cr[4], cr[5], cr[6][0], cr[6][1], round(cr[7]), cr[8], cr[9], cr[10]))


def main():
    out = Out()
    urn(out, SCENE, 'Right urn', 41)
    crystal_planter(out, SCENE)
    urn(out, SCENE, 'Left urn', 31)
    out.write(cutting.sheet_path('furniture/planters.svg'))
    print('wrote planters.svg (%d shapes)' % sum(1 for line in out.body if line.startswith('<path')))


PLANTERS = ['crystal planter', 'left urn', 'right urn']


def parts():
    from scene_export import placed_foliage
    return [part for obj in PLANTERS for part in placed_foliage.placed().parts[obj]]


if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if mode == 'check':
        main()
    {'build': main, 'check': check, 'fit': fit_crystals}[mode]()

#   Writes SVG, run by `python3 -m scene_export render`: furniture/table_set.svg, the table and chairs sheet.
#
#   The round bistro table and its four chairs, built in 3D and drawn through
#   the terrace camera.
#
#   Turned parts (pedestal, table top, seats, cushions) are surfaces of
#   revolution; their outlines are the exact perspective contour of the profile
#   plus the front arc of the bottom ring and the back arc of the top ring.
#   Chair backs are flat drawings placed on a tilted plane behind each seat:
#   the side facing the seat is a teal quilted heart, the outer side a cream
#   panel with a teal gem, and whichever side faces the eye is drawn. Gems and
#   glass panels are wrapped onto the pedestal surface. Outlines are 3px on
#   screen; quilting creases are thinner detail lines.
#
#   python3 -m furniture.table_set  ->  table_set.svg

import math
import os
import re
import sys

import numpy as np
from matplotlib.path import Path
from scipy.spatial import ConvexHull

from common import gems
from furniture import table_set_reference as T
from common.terrace import Camera, built_terrace
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- placement
# The set follows its own painting, panel-attack-references/furniture/table-set/source.png, laid on the stage by
# table_set_reference.py. The painting gives the set its own perspective: the table is seen
# almost straight on from high up and far away (its top and foot rings are nearly the same
# shape), while the chairs' feet splay open, which no single camera gives. So the set has
# two local cameras (horizon y, focal px, centre x; eye one unit above the floor looking
# along +Z, as terrace.Camera), fitted to table_set_reference.py's landmarks (`python3 -m furniture.table_set
# check`). World units below are those cameras' own.
# (horizon, focal, centre x, roll in degrees about ROLL_PIVOT; + = clockwise on screen)
TABLE_CAMERA = (91.9, 3747.0, 1235.7, 0.0)
CHAIR_CAMERA = (456.2, 1789, 1227.2, -0.099)
ROLL_PIVOT = (1235.0, 880.0)
# Screen point on the floor at the middle of the set, the chairs placed round it.
TABLE_SCREEN = (1235.7, 878.8)
# Screen point on the floor under the table's own axis: the painting stands the table's foot lower than
# the middle of the chairs' circle, under a longer pedestal.
TABLE_FLOOR = (1235.7, 897.8)
# Chairs: (name, angle in degrees around the table seen from above; 0 = +X (right),
# 90 = away from the camera, 180 = left, 270 = towards the camera; distance from the
# table axis; extra turn of the chair in degrees, + = anticlockwise seen from above).
# Positions are in the chair camera's world, round TABLE_SCREEN's floor point there.
CHAIRS = [
    ('chair back left', 157.37, 0.4628, -12.92),
    ('chair back right', 30.09, 0.4542, 12.11),
    ('chair front left', 226.11, 0.5887, -7.37),
    ('chair front right', 309.85, 0.6260, 11.55),
]
# Per-chair cheats, as the painting draws each chair on its own: (overall size about
# the seat's floor point, stretch of the back's height, backwards lean of the back, outward
# reach of the feet in seat radii). The back chairs show one foot each, so their toe out
# only follows that foot.
CHAIR_TWEAKS = {
    'chair back left': (1.050, 1.172, -0.050, 0.15),
    'chair back right': (1.005, 1.167, 0.220, 0.50),
    'chair front left': (0.972, 1.023, 0.030, -0.13),
    'chair front right': (0.980, 1.014, 0.050, -0.13),
}
# degrees the back is turned round the seat from straight behind it, towards the table (+)
BACK_TURN = {
    'chair back left': -1.61,
    'chair back right': 10.20,
    'chair front left': 1.66,
    'chair front right': 3.43,
}

# ---------------------------------------------------------------- sizes (eye heights)
# The table is modelled in screen px at its axis (PX world units per px), read off the
# painting on the stage (table_set_reference.py): a 355 x 54 px marble top over a 19 px gold band,
# on an hourglass pedestal of crossing gold straps standing on a wide low foot disc. The foot
# ring is rounder than the top (0.21 against 0.15), which sets TABLE_CAMERA.
PX = 1 / (TABLE_FLOOR[1] - TABLE_CAMERA[0])
TABLE_HEIGHT = 236.35 * PX
TOP_RADIUS = 179.7 * PX
TOP_THICKNESS = 19 * PX
TOP_INSET = 2 * PX               # gold lip showing round the marble
APRON_RADIUS, APRON_DEPTH = 120 * PX, 6 * PX    # gold skirt under the top, hidden by the band from the front
FOOT_RADIUS, FOOT_HEIGHT = 100 * PX, 21 * PX     # the base's skirt, widest at the floor
SKIRT_TOP = 0.9                                   # the base's skirt flares out from this share of FOOT_RADIUS at its top
PLINTH_RADIUS, PLINTH_TOP = 78.5 * PX, 27 * PX   # the lower bell's foot, standing on the plinth's ledge
RING_RADIUS, RING_ROUND = 93 * PX, 4 * PX        # the plinth: a rounded ring round the lattice's foot
# The pedestal: a lattice of gold straps flaring out under the top and a plain bell flaring
# down to the plinth, either side of a collar. (radius, height) in px, top to bottom.
UPPER_LATTICE = [(104, 217.35), (92, 194), (80, 181), (70, 168), (62, 156), (55, 145), (50.5, 133), (47.5, 121), (46.5, 114)]
LOWER_BELL = [(45.5, 99), (56, 70), (66.5, 50), (PLINTH_RADIUS / PX, PLINTH_TOP / PX)]
LOWER_TOP, KNOB_TOP = 99 * PX, 114 * PX       # the collar between the lattice and the bell
NECK_RADIUS, KNOB_BULGE = 47 * PX, 2.5 * PX
LOWER_RADIUS = 46.5 * PX
FLARE_RADIUS = 92 * PX            # lattice radius where it comes out from under the top
# The lattice is drawn as the painting's: a gold ring round the gem whose four edges run on as
# straps to the lattice's edges, mirrored about the gem, and a rib down each side.
STRAP_PX = 13                     # strap width, as the ring's band
STRAP_GAP_PX = 4                  # core showing between a rib and a strap turned down along it
STRAP_STROKE = 2.2                # straps are outlined lighter than the solid gold round them
STRAP_SHADE_PX = 4                # straps whose middle lies this far right of the gem are turned from the light
STRAP_STANDOFF = 3 * PX           # straps stand this far off the core
RING_TONES = {'lit': '#faf480', 'shade': '#fdc534'}
RIB_PX = 11                       # width of the curved rib down each side of the upper lattice
RIB_STREAK = (2.0, 2.6, 0.12)     # a rib's highlight: px in from its outer edge, px wide, share of its height left bare at each end
RING_TUCK_PX = 8                  # how far the ring and straps run on below the lattice, inside the collar
# gems: (angle from the front, height of the centre, half width (arc, px) and half height px)
UPPER_GEM = (0.0, 158.4, 19.3, 31)
RING_OUTER = (38, 58)             # half width and half height px of the ring round the upper gem
LOWER_GEM = (0.0, 59.5, 19, 23)   # angle, height, half sizes px: the bell's one gem
LOWER_GEM_FRAME = (39, 41)        # half sizes px of the gold frame round it
TOP_SHADOW = 26                   # px of pedestal darkened under the top
TOP_SHADOW_LAYERS = [(3, 6), (6, 11), (9, 17)]   # px the top's shadow reaches past its rim on the back cushions
TOP_SHADOW_OPACITY = 0.22

SEAT_HEIGHT = 0.2686
SEAT_RADIUS = 0.1986
SEAT_FRAME = 0.04
CHAIR_SCALE = SEAT_RADIUS / 0.15  # ornaments below were drawn for a 0.15 seat
CUSHION_RADIUS = SEAT_RADIUS * 1
CUSHION_RISE = 0.082
CUSHION_ROUND = 4.0
TUFT_SPACING = 0.058 * CHAIR_SCALE   # quilting diamond size
LEG_SPREAD = 0.208  # leg top distance from seat centre
# leg centreline: (outward offset from LEG_SPREAD, height), rail to toe: a short knee under
# the rail, then a near-straight taper splaying out to the foot, as the reference draws them;
# drawn for a 0.205 rail bottom and stretched to this one
_LEG_K = (SEAT_HEIGHT - SEAT_FRAME) / 0.205
LEG_PROFILE = [(du * CHAIR_SCALE, h * _LEG_K) for du, h in
               [(-0.03, 0.212), (-0.008, 0.185), (0.006, 0.15), (0.004, 0.11), (-0.006, 0.07), (-0.01, 0.042),
                (0.0, 0.022), (0.024, 0.014)]]
LEG_WIDTH = tuple(w * CHAIR_SCALE for w in (0.017, 0.0075, 0.010))   # half-widths at the knee, the ankle and the toe
FOOT_BALL = 0.014 * CHAIR_SCALE
BRACKET_CURL = (0.021 * CHAIR_SCALE, 0.012 * CHAIR_SCALE)    # C-scroll on each knee, just under the rail
RAIL_SHEEN = (0.22, 0.38)        # stripes round the rail, as fractions of its depth from the top
RAIL_SHADE = (0.72, 0.9)
APRON_CURL = (0.016 * CHAIR_SCALE, 0.009 * CHAIR_SCALE)
FOOT_CURL = (0.013 * CHAIR_SCALE, 0.008 * CHAIR_SCALE)
RAIL_SKIN = 0.002
RIM_LIP = 0.011   # the seat rail stands this far out past the cushion, so its top shows as a lip
BACK_RIM = SEAT_RADIUS + RIM_LIP + 0.2 * SEAT_FRAME + RAIL_SKIN   # the back grows out of the seat rail at its top rim
BACK_SETBACK = BACK_RIM          # seat centre to the middle of the back's foot
EDGE_FADE = 0.3                  # back heights over which the frame's thickness grows from the rail
FLARE_CUT = 0.12                 # flare points below this are dropped where they pass the rail's edge
BACK_BEND = 1  # how fast the back flattens above the seat (bend radius per back height)
BACK_TILT = 0.158                # backwards lean per unit height
BACK_HEIGHT = 0.3942  # above the rail, excluding the crest
BACK_THICKNESS = 0.03 * CHAIR_SCALE
BACK_WIDTH = 1.4305  # stretch of the back drawings' u across the seat
BACK_CURVE = 0.0762  # extra backwards lean growing with the square of height, in back heights
BACK_TAPER = 0  # extra width per back height going up (narrower foot, broader top)
TOE_OUT = -0.15  # extra outward reach of the feet, in seat radii, unless CHAIR_TWEAKS says

# ---------------------------------------------------------------- colours
STROKE = 3
DETAIL_STROKE = 2
BEVEL_PX, BEVEL_IN_PX = 3.2, 0.8   # bevel strip width on flat gold shapes, screen px
LIGHT_DIR = (-0.6, 0.8)            # top-left, (screen right, up)
SHEEN_BAND = (28.0, 52.0)          # turned parts: degrees off the front, + = screen left
SHADE_BAND = (-82.0, -55.0)
TURNED_SHEEN = {'gold': '#ffe066', 'turquoise': '#8ff6fa', 'cream': '#ffffff'}
SHEEN = {'gold': '#fff27a', 'strap': '#fefbd8', 'strap shade': '#f6b11d', 'turquoise': '#8ff6fa', 'cream': '#ffffff'}
SHADE = {'gold': '#b05c08', 'strap': '#d88a10', 'strap shade': '#a04a04', 'turquoise': '#1182a6', 'cream': '#e2cc9c'}  # quilting highlight size and offset, in lattice cells
GRADIENTS = {
    'gold': ('#ffc634', '#e58a0a'),          # rail.py's goldGrad, so the set matches the rail
    'gold dark': ('#f0a420', '#c46a06'),
    'turquoise': ('#3fdcea', '#0d98b8'),
    'turquoise light': ('#7aeef4', '#36cadc'),
    'puff': ('#a6f6fa', '#6fe4ee'),
    'cushion puff': ('#5ae6f0', '#2fd0e0'),
    'cushion': ('#00bfd2', '#0088a6'),
    'cream': ('#fff8ea', '#ecd5a8'),
    'marble': ('#f4f2ee', '#e9e4da'),
    'gold band': ('#ffb52a', '#e58a0a'),
    'gold strap': ('#fde25a', '#f5c00b'),   # the pedestal's straps stand out pale against its deep core
    'gold strap shade': ('#f0b030', '#c87010'),   # ...going orange where they turn away to the right
}
OUTLINE = {'gold': '#6e3204', 'strap': '#6a2803', 'strap shade': '#6a2803', 'turquoise': '#0f7f9e', 'cream': '#b99b62', 'none': 'none'}
FACET = '#d9feff'
CREASE = '#0d7090'
BUTTON = '#0c7a98'
CURL = '#d99a35'


class RolledCamera(Camera):
    """terrace.Camera turned on screen about ROLL_PIVOT."""

    def __init__(self, horizon, focal, centre_x, roll=0.0):
        super().__init__(horizon, focal, centre_x)
        self.roll = math.radians(roll)

    def _turn(self, x, y, angle):
        c, s = math.cos(angle), math.sin(angle)
        dx, dy = x - ROLL_PIVOT[0], y - ROLL_PIVOT[1]
        return ROLL_PIVOT[0] + c * dx - s * dy, ROLL_PIVOT[1] + s * dx + c * dy

    def project(self, X, Y, Z):
        return self._turn(*super().project(X, Y, Z), self.roll)

    def unproject_onto_plane(self, x, y, point, normal):
        return super().unproject_onto_plane(*self._turn(x, y, -self.roll), point, normal)


class Scene:
    def __init__(self, camera=None):
        self.cam = RolledCamera(*camera) if camera else built_terrace().camera
        self.eye = np.array([0.0, 1.0, 0.0])

    def project(self, p):
        return self.cam.project(p[0], p[1], p[2])

    def scale(self, p):
        """Screen pixels per world unit at p."""
        return self.cam.focal / p[2]


def fmt(points, closed=True):
    return 'M' + ' L'.join('%.1f,%.1f' % tuple(p) for p in points) + (' Z' if closed else '')


def catmull(points, per=8, closed=True):
    """Dense Catmull-Rom samples through 2D points."""
    p = [np.asarray(q, float) for q in points]
    n = len(p)
    out = []
    segs = n if closed else n - 1
    for i in range(segs):
        a, b, c, d = p[(i - 1) % n], p[i], p[(i + 1) % n], p[(i + 2) % n]
        if not closed:
            a, d = p[max(i - 1, 0)], p[min(i + 2, n - 1)]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                              + (-a + 3 * b - 3 * c + d) * t ** 3))
    if not closed:
        out.append(p[-1])
    return out


def mirrored(half):
    """Right half (u >= 0, listed bottom to top) mirrored into a closed outline."""
    return half + [(-u, v) for u, v in reversed(half) if u > 1e-9]


def spiral(cx, cy, r0, start, sign, width, turns=1.35, n=36):
    """Closed outline of a tapering scroll curl in 2D: a ribbon along an inward spiral."""
    centre = []
    for t in np.linspace(0, 1, n):
        r = r0 * (1 - 0.72 * t)
        a = start + sign * t * turns * 2 * math.pi
        centre.append(np.array([cx + r * math.cos(a), cy + r * math.sin(a)]))
    left, right = [], []
    for k, p in enumerate(centre):
        a, b = centre[max(k - 1, 0)], centre[min(k + 1, n - 1)]
        d = (b - a) / (np.linalg.norm(b - a) + 1e-12)
        nrm = np.array([-d[1], d[0]])
        w = width * (1 - 0.55 * k / (n - 1)) / 2
        left.append(p + nrm * w)
        right.append(p - nrm * w)
    end = centre[-1]
    cap = [end + (left[-1] - end) * 1.0]
    return [tuple(q) for q in left + cap + right[::-1]]


def circle(cx, cy, r, n=20):
    return [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


# ---------------------------------------------------------------- bevels

def _dense_px(pts, step=1.5):
    out = []
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / step)))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    return out


def bevel_strips(pts, toward, w0, w1, threshold=0.25):
    """Crescent strips just inside a closed y-up outline, along the stretch whose
    outward normal faces `toward`. Width tapers from w1 in the middle to w0 at the ends."""
    p = np.array(_dense_px(pts))
    n = len(p)
    if n < 8:
        return []
    area = np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    if area < 0:
        p = p[::-1]
    edge = np.roll(p, -1, axis=0) - p
    en = np.stack([edge[:, 1], -edge[:, 0]], 1)
    en /= np.linalg.norm(en, axis=1, keepdims=True) + 1e-12
    vn = en + np.roll(en, 1, axis=0)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
    lit = vn @ np.array(toward) / np.linalg.norm(toward) > threshold
    lit &= np.sum(en * np.roll(en, 1, axis=0), axis=1) > 0.3
    if lit.all():
        lit[np.argmin(vn @ np.array(toward))] = False
    start = int(np.argmin(lit))
    runs, run = [], []
    for k in range(n):
        i = (start + k) % n
        if lit[i]:
            run.append(i)
        elif run:
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    strips = []
    for run in runs:
        if len(run) < 4:
            continue
        m = len(run)
        taper = [max(0.0, math.sin(math.pi * k / (m - 1))) ** 0.6 for k in range(m)]
        outer = [p[i] - vn[i] * w0 for i in run]
        inner = [p[i] - vn[i] * (w0 + (w1 - w0) * t) for i, t in zip(run, taper)]
        strips.append([tuple(q) for q in outer + inner[::-1]])
    return strips


def screen_bevels(points, w1=BEVEL_PX, w0=BEVEL_IN_PX):
    """(sheen strips, shade strips) inside a screen-space outline, lit from the top left."""
    up = [(x, -y) for x, y in points]
    back = lambda strips: [[(x, -y) for x, y in st] for st in strips]
    return (back(bevel_strips(up, LIGHT_DIR, w0, w1)),
            back(bevel_strips(up, (-LIGHT_DIR[0], -LIGHT_DIR[1]), w0, w1)))


# ---------------------------------------------------------------- surfaces of revolution

def lathe_outline(scene, centre, r, h0, h1, steps=24, arc=48, cap=True):
    """Screen outline of the solid of revolution with radius r(h), h0..h1, axis through centre.
    Without its cap, it ends at the front edge of its top, for a ring whose top is hidden in what
    stands on it."""
    X0, Z0 = centre[0] - scene.eye[0], centre[2] - scene.eye[2]
    D, phi = math.hypot(X0, Z0), math.atan2(X0, Z0)

    def dr(h):
        e = 1e-4
        return (r(min(h + e, h1)) - r(max(h - e, h0))) / (min(h + e, h1) - max(h - e, h0))

    def half_angle(h):
        k = -r(h) + dr(h) * (h - scene.eye[1])
        return math.acos(max(-1.0, min(1.0, k / D)))

    def at(h, theta, rad=None):
        rad = r(h) if rad is None else rad
        return scene.project((centre[0] + rad * math.sin(theta), h, centre[2] + rad * math.cos(theta)))

    hs = np.linspace(h0, h1, steps)
    a0, a1 = half_angle(h0), half_angle(h1)
    pts = [at(h0, t) for t in np.linspace(phi + a0, phi - a0 + 2 * math.pi, arc)]
    pts += [at(h, phi - half_angle(h)) for h in hs[1:-1]]
    if cap:
        pts += [at(h1, t) for t in np.linspace(phi - a1, phi + a1, arc)]
    else:
        # the front edge only from its widest points: past them it runs round the back, a hook over what stands on it
        edge = [at(h1, t) for t in np.linspace(phi - a1, phi + a1 - 2 * math.pi, arc)]
        xs = [x for x, _ in edge]
        i, j = sorted((int(np.argmin(xs)), int(np.argmax(xs))))
        pts += edge[i:j + 1]
    pts += [at(h, phi + half_angle(h)) for h in hs[::-1][1:-1]]
    return pts


def ring(scene, centre, h, rad, n=64):
    return [scene.project((centre[0] + rad * math.sin(t), h, centre[2] + rad * math.cos(t)))
            for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def wrapped(scene, centre, r, outline, angular=False):
    """Flat (u, h) outline wrapped onto the camera-facing side of the surface r(h).
    u is arc length, or the angle from the front when angular."""
    front = math.atan2(centre[0] - scene.eye[0], centre[2] - scene.eye[2]) + math.pi
    out = []
    for u, h in outline:
        rad = r(h) + 0.002
        theta = front - (u if angular else u / rad)
        out.append(scene.project((centre[0] + rad * math.sin(theta), h, centre[2] + rad * math.cos(theta))))
    return out


MITRE_LIMIT = 3


def band(pts, widths):
    """Left and right edges of a band of the given screen half-widths along a screen polyline, mitred so it
    keeps its width round a corner."""
    pts = [np.array(p) for p in pts]
    count = len(pts)
    left, right = [], []
    normal = lambda d: np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-9)
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, count - 1)]
        n_in, n_out = normal(p - a if a is not p else b - p), normal(b - p if b is not p else p - a)
        n = normal(b - a) if np.dot(n_in, n_out) > 0.999 else (n_in + n_out) / (np.linalg.norm(n_in + n_out) + 1e-9)
        w = widths[i] / max(float(np.dot(n, n_in)), 1 / MITRE_LIMIT)
        left.append(p + n * w)
        right.append(p - n * w)
    return left, right


def ribbon(scene, centreline, widths):
    """A tapered band of the given world half-widths along a 3D centreline, offset in screen space."""
    left, right = band([scene.project(p) for p in centreline], [w * scene.scale(p) for w, p in zip(widths, centreline)])
    return catmull(left, 4, closed=False) + catmull(right[::-1], 4, closed=False)


# ---------------------------------------------------------------- svg

class Out:
    def __init__(self):
        self.body = []

    def group(self, name):
        self.body.append('<g id="%s">' % name)

    def end(self):
        self.body.append('</g>')

    def shape(self, name, points, paint, outline, width=STROKE, opacity=1.0):
        fill = 'url(#%s)' % paint.replace(' ', '-') if paint in GRADIENTS else paint
        alpha = ' opacity="%g"' % opacity if opacity < 1 else ''
        self.body.append('<path id="%s" d="%s" fill="%s" stroke="%s" stroke-width="%g" '
                         'stroke-linejoin="round" stroke-linecap="round"%s/>'
                         % (name, fmt(points), fill, OUTLINE.get(outline, outline), width, alpha))

    def bevelled(self, name, points, paint='gold', outline='gold', w1=BEVEL_PX, width=STROKE):
        """A shape with flat light and dark bevel strips inside its outline."""
        self.shape(name, points, paint, outline, width)
        sheen, shade = screen_bevels(points, w1)
        for label, strips, colour in (('sheen', sheen, SHEEN[outline]), ('shade', shade, SHADE[outline])):
            for k, st in enumerate(strips):
                self.shape('%s %s%s' % (name, label, ' %d' % (k + 1) if k else ''), st, colour, 'none')

    def turned(self, scene, name, c, r, h0, h1, paint='gold', outline='gold'):
        """A surface of revolution with vertical sheen and shade bands."""
        self.shape(name, lathe_outline(scene, c, r, h0, h1), paint, outline)
        front = math.atan2(c[0] - scene.eye[0], c[2] - scene.eye[2]) + math.pi
        e = 0.1 * (h1 - h0)
        hs = np.linspace(h0 + e, h1 - e, 10)

        def at(a, h):
            rad = r(h) + 0.001
            t = front + math.radians(a)
            return scene.project((c[0] + rad * math.sin(t), h, c[2] + rad * math.cos(t)))
        for label, (a0, a1), colour in (('sheen', SHEEN_BAND, TURNED_SHEEN[outline]), ('shade', SHADE_BAND, SHADE[outline])):
            self.shape('%s %s' % (name, label), [at(a0, h) for h in hs] + [at(a1, h) for h in hs[::-1]], colour, 'none')

    def line(self, name, points, colour, width=DETAIL_STROKE, opacity=1.0):
        alpha = ' opacity="%g"' % opacity if opacity < 1 else ''
        self.body.append('<path id="%s" d="%s" fill="none" stroke="%s" stroke-width="%g" '
                         'stroke-linejoin="round" stroke-linecap="round"%s/>'
                         % (name, fmt(points, closed=False), colour, width, alpha))

    def write(self, path):
        defs = ''.join('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1">'
                       '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
                       % (k.replace(' ', '-'), a, b) for k, (a, b) in GRADIENTS.items())
        with open(path, 'w') as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1024" viewBox="0 0 1536 1024">\n')
            f.write('<defs>%s</defs>\n<g id="Table set">\n' % defs)
            f.write('\n'.join(self.body))
            f.write('\n</g>\n</svg>\n')


# ---------------------------------------------------------------- table

UNDER = TABLE_HEIGHT - TOP_THICKNESS
APRON_BOTTOM = UNDER - APRON_DEPTH

GOLD_TONES = {'lit': '#ffd23e', 'glint': '#fff27a', 'mid': '#f0a020', 'shade': '#c96e0a', 'deep': '#b05c08'}
MARBLE_LINE = '#a54b07'          # the painting outlines the marble in warm brown, not tan
MARBLE_BACK_LINE = '#b89470'     # and fades that outline along its far edge
MARBLE_TONES = {'shade': '#e6dfd3', 'edge': '#d9ccb6', 'cloud': '#f8f7f4', 'rim': '#f6e8cf', 'vein': '#cdc1af'}
MARBLE_SHEEN = '#fcfbf9'
# faint veins, as (share of the marble's radius, degrees round from screen right) points
MARBLE_VEINS = [[(0.92, 205), (0.7, 192), (0.52, 170), (0.38, 150), (0.3, 128)],
                [(0.95, 40), (0.78, 58), (0.66, 80), (0.55, 100)],
                [(0.85, -25), (0.66, -8), (0.52, 12), (0.45, 30)]]
OCCLUSION = '#b04400'
CREAM_LIGHT = {'light': '#ffffff', 'shade': '#dcbf8a', 'px': 6.0}
SEAT_TUFT_SCALE = 1.25             # seat quilting cell, in TUFT_SPACING: about 6 panels across
TUFT_REACH = 0.99                 # quilting runs this far out over the dome, in cushion radii
TUFT = {'puff': '#00dbe8', 'light': '#0af2f8', 'shade': '#0088a6', 'pit': '#0a5f78', 'crease': '#0a5f78'}
CUSHION_LIGHT = {'sheen': '#c0fdff', 'shade': '#06607a', 'edge px': 5.0}
SUN_TOWARD = np.array([-0.25, 1.0, -0.5]) / math.sqrt(1.3125)   # BRIEF "Lighting": towards the sun
# Quilting, as the reference's cushions: rounded diamond panels, each an opaque pillow
# (darker panel, puff, lighter crown up-left), with short creases and dimples where they meet.
# Tones run from the side away from the sun to the sheen; a panel at level L uses L..L+2.
QUILT = {'tones': ['#056e86', '#0088a6', '#009fbc', '#00bfd2', '#00dbe8', '#0af2f8', '#a6fcff'],
         'seam': '#0a5f78', 'pit': '#054e66', 'corner': 0.22, 'crease': 0.12, 'crease px': 1.0}
BACK_QUILT = 0.045                 # heart cushion quilting cell, in world lengths on the back
SEAT_LIT_RANGE = (0.3, 0.87)       # facing-the-sun values mapped onto levels 0..3
SEAT_SHEEN_PANELS = 3              # the panels nearest the sheen spot get level 4
SEAT_FRONT_BAND = '#0088a6'        # where the dome turns down to the rim
SEAT_GLINT = '#d6ffff'
SEAT_OUTLINE = '#0a5f78'
# Light: the sun is high, behind the camera and a little left (BRIEF "Lighting"). Turned
# parts are shaded by angle from the front (+ = screen left) with colour stops that are
# cut into many narrow flat bands, so the shading reads smooth with no visible steps.
GOLD_STOPS = [(92, '#ffc634'), (62, '#ffd84a'), (44, '#fff07a'), (30, '#ffcf3c'), (0, '#f5a51c'),
              (-30, '#e08a0c'), (-58, '#c87008'), (-92, '#b05c08')]
# the pedestal's turned rings are the straps' pale gold, as the painting's collar and base
PALE_STOPS = [(92, '#ffd84a'), (62, '#fff07a'), (44, '#fffbd0'), (30, '#fff07a'), (0, '#ffd23e'), (-30, '#f5b028'),
              (-58, '#e0901a'), (-92, '#c87008')]
EDGE_STOPS = [(92, '#f8e070'), (64, '#fcf38c'), (46, '#fcf696'), (32, '#f8e468'), (0, '#f2c84a'),
              (-28, '#e6aa3c'), (-56, '#d89434'), (-92, '#bc782a')]



def profile(points):
    """Smooth radius(h) through (radius px, height px) points."""
    from scipy.interpolate import PchipInterpolator
    pts = sorted(points, key=lambda p: p[1])
    f = PchipInterpolator([h * PX for _, h in pts], [r * PX for r, _ in pts])
    lo, hi = pts[0][1] * PX, pts[-1][1] * PX
    return lambda h: float(f(min(max(h, lo), hi)))


upper_lattice = profile(UPPER_LATTICE)
lower_bell = profile(LOWER_BELL)


def knob(h):
    t = (h - LOWER_TOP) / (KNOB_TOP - LOWER_TOP)
    return NECK_RADIUS + KNOB_BULGE * math.sin(math.pi * min(max(t, 0.0), 1.0)) ** 0.6


def foot(h):
    """The base's skirt, its side slanting out down to the floor."""
    t = min(max(h / FOOT_HEIGHT, 0.0), 1.0)
    return FOOT_RADIUS * (1 - (1 - SKIRT_TOP) * t)


def plinth(h):
    """The plinth ring, its top and bottom edges rounded off."""
    t = min(max((h - FOOT_HEIGHT) / (PLINTH_TOP - FOOT_HEIGHT), 0.0), 1.0)
    return RING_RADIUS + RING_ROUND * (math.sin(math.pi * t) - 1)


def turned_at(scene, c, r, lift=0.0004):
    front = math.atan2(c[0] - scene.eye[0], c[2] - scene.eye[2]) + math.pi

    def at(a, h):
        rad = r(h) + lift
        t = front + math.radians(a)
        return scene.project((c[0] + rad * math.sin(t), h, c[2] + rad * math.cos(t)))
    return at


def mix(c0, c1, t):
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def graded(scene, out, name, c, r, h0, h1, stops, per=4, lift=0.0004):
    """Cover the visible side of a turned part with narrow vertical bands whose colours step
    smoothly through the stops (angle from the front, + = screen left)."""
    at = turned_at(scene, c, r, lift)
    hs = np.linspace(h0, h1, 14)
    out.group(name + ' shading')
    k = 0
    for (a0, c0), (a1, c1) in zip(stops, stops[1:]):
        for i in range(per):
            # each band runs half a step into the next one, so no hairline seams show
            u0, u1 = a0 + (a1 - a0) * i / per, a0 + (a1 - a0) * (i + 1.5) / per
            if (a1, i) == (stops[-1][0], per - 1):
                u1 = a1
            k += 1
            out.shape('%s shade %d' % (name, k), [at(u0, h) for h in hs] + [at(u1, h) for h in hs[::-1]],
                      mix(c0, c1, (i + 0.5) / per), 'none')
    out.end()


def hband(scene, c, r, h0, h1, a0=-90, a1=90, lift=0.0004, n=40):
    """A horizontal band round the visible side of a turned part between heights h0 and h1."""
    at = turned_at(scene, c, r, lift)
    ts = np.linspace(a0, a1, n)
    return [at(a, h1) for a in ts] + [at(a, h0) for a in ts[::-1]]


def lens(scene, c, r, h0, h1, a0=-90, a1=90, lift=0.0004, n=40):
    """A band round a turned part like hband, but swelling to h0..h1 in the middle and tapering to points at its ends."""
    at = turned_at(scene, c, r, lift)
    ts = np.linspace(0.0, 1.0, n)
    mid, half = (h0 + h1) / 2, (h1 - h0) / 2
    edge = lambda sign: [at(a0 + (a1 - a0) * t, mid + sign * half * math.sin(math.pi * t) ** 0.7) for t in ts]
    return edge(1) + edge(-1)[::-1]


def occlusion(scene, out, name, c, r, h_top, depth, lift=0.0004, layers=4, opacity=0.13):
    """Soft shade under an overhang: stacked bands growing down from h_top, darkest at the top."""
    out.group(name)
    for k in range(layers):
        d = depth * (k + 1) / layers
        out.shape('%s %d' % (name, k + 1), hband(scene, c, r, h_top - d, h_top, lift=lift), OCCLUSION, 'none', 0, opacity)
    out.end()


def disc(scene, out, name, c, rad, h0, h1, paint='gold', top=True, stops=PALE_STOPS, r=None):
    """A gold disc: rim graded from lit left to shaded right, and its brighter top face. r(h) shapes
    its rim, which is otherwise straight at radius rad."""
    r = r or (lambda h: rad)
    out.group(name)
    out.shape(name + ' rim', lathe_outline(scene, c, r, h0, h1), paint, 'gold')
    graded(scene, out, name + ' rim', c, r, h0 + 0.1 * (h1 - h0), h1 - 0.1 * (h1 - h0), stops)
    if top:
        top = r(h1)
        out.shape(name + ' top', ring(scene, c, h1, top, 96), GOLD_TONES['lit'], 'gold', 2)
        out.shape(name + ' top sheen', arc_band(scene, c, h1, top * 0.6, top * 0.86, 150, 235), GOLD_TONES['glint'], 'none')
        out.shape(name + ' top shade', arc_band(scene, c, h1, top * 0.7, top * 0.95, -50, 20), GOLD_TONES['mid'], 'none')
    out.end()


def arc_band(scene, c, h, r0, r1, a0, a1, n=24):
    """A crescent on a horizontal circle between radii r0 and r1; angles in degrees, 90 = front."""
    def at(rad, t):
        t = math.radians(t)
        return scene.project((c[0] + rad * math.cos(t), h, c[2] - rad * math.sin(t)))
    ts = np.linspace(a0, a1, n)
    return [at(r1, t) for t in ts] + [at(r0, t) for t in ts[::-1]]


# the gems' frames are the pale straps' gold, nearly flat, as the painting's
GEM_GOLD = dict(gems.SETTING, line=OUTLINE['gold'], fill='#fef989', light='#fefbc0', mid='#fde060', low='#fef989', dark='#fdd040')
# the painting's gems are a bright cyan rather than the planters' teal, sampled facet by facet
GEM_STONE = dict(gems.STONE, light='#b8fcfd', mid='#04c4e6', low='#03b8dc', dark='#007db0', glint='#ffffff',
                 rim='#0a4b62')
# the lower bell, sampled from the example: pale cream where it faces the light, orange turned away
BELL_STOPS = [(92, '#f6eb98'), (60, '#fcf8ad'), (0, '#fdf9ae'), (-10, '#fde458'), (-16, '#fbb435'), (-78, '#f4ac30'),
              (-86, '#d88420'), (-92, '#983d0c')]
# the base's discs, sampled from the example: orange gold, pale only where they face the light
BASE_STOPS = [(92, '#fcb70a'), (60, '#fdd32c'), (35, '#fde050'), (15, '#fef06a'), (0, '#fdc625'), (-25, '#f0a818'),
              (-50, '#da7d01'), (-75, '#c86c00'), (-92, '#b05c00')]
# the collar, sampled from the example: brighter and more orange than the pale rings
COLLAR_STOPS = [(92, '#ffbf07'), (60, '#fefa79'), (30, '#fef049'), (0, '#fed919'), (-30, '#fec015'), (-58, '#ec9703'),
                (-92, '#d07000')]
# the lattice's core, seen through its openings: light yellow, going orange away from the light
CORE_STOPS = [(92, '#fff3a0'), (72, '#ffe777'), (58, '#ffdc58'), (15, '#fcca3a'), (-15, '#f6b52a'), (-58, '#eea21e'),
              (-72, '#eba01c'), (-92, '#e89a1c')]
CORE_GLOW = ('#fffbd0', 0.5, 8, 0.1)   # a pale glow rising from the lattice's foot: colour, share of its height, layers, opacity
# (past about 60 degrees the straps crowd together, so the core shows gold there, as the painting's edges)


GEM_GLINT = ((-0.92, 0.0), (-0.12, 0.06), (0.0, 0.0), (-0.12, -0.03))   # a white streak from the left point to the middle


def draw_gem(out, name, mapf, cx, cy, hw, hh, outer=None, glint=GEM_GLINT):
    """Every gem in the set goes through here, so the gem style can be swapped in one place.
    outer: half sizes of a pointed gold setting round it."""
    gems.write(out.body, gems.diamond_gem(name, mapf, cx, cy, hw, hh, outer=outer, steps=6, stone=GEM_STONE,
                                          gold=GEM_GOLD, stroke=STROKE, glint=glint), group=name)


def on_surface(scene, c, r, angle):
    """Maps (u, h) to the screen: u arc length to the right of the line `angle` degrees from
    the front (+ = screen left) on the surface r(h), h a height."""
    front = math.atan2(c[0] - scene.eye[0], c[2] - scene.eye[2]) + math.pi

    def mapf(pts):
        out = []
        for u, h in pts:
            rad = r(h)
            t = front + math.radians(angle) - u / rad
            out.append(scene.project((c[0] + rad * math.sin(t), h, c[2] + rad * math.cos(t))))
        return out
    return mapf


def within(outline, points, tuck=0):
    """Points pushed inside a lathe's screen outline, row by row: what runs past its edge folds
    onto the silhouette, as a band wrapping round it does. With a tuck, they may run on that far below
    its bottom, inside the sides it has that far up, into what stands under it."""
    ys = [y for _, y in outline]
    top, bottom = min(ys) + 1, max(ys) - 1     # a row off its very ends, where it has a width to push into
    pushed = []
    for x, y in points:
        y = min(max(y, top), bottom + tuck)
        lo, hi = span_at([outline], min(y, bottom - tuck))
        pushed.append((min(max(x, lo), hi), y))
    return pushed


def rib(outline, side, width=RIB_PX, rows=40):
    """A band RIB_PX wide down one side of a lathe's screen outline, its outer edge on the silhouette, running on
    straight down behind what stands under it."""
    ys = [y for _, y in outline]
    top, bottom = min(ys) + 0.5, max(ys)
    edge, inner = [], []
    for y in np.linspace(top, bottom + RING_TUCK_PX, rows):
        lo, hi = span_at([outline], min(y, bottom - RING_TUCK_PX))
        x, sign = (lo, 1) if side == 'left' else (hi, -1)
        edge.append((x, y))
        inner.append((x + sign * width, y))
    return edge + inner[::-1]


def rib_streak(outline, side, rows=40):
    """The thin highlight running down a rib just inside its outer edge, tapering off at its ends."""
    inset, width, bare = RIB_STREAK
    ys = [y for _, y in outline]
    top, bottom = min(ys), max(ys)
    outer, inner = [], []
    for k in range(rows):
        t = k / (rows - 1)
        y = top + (bottom - top) * (bare + (1 - 2 * bare) * t)
        lo, hi = span_at([outline], y)
        x, sign = (lo, 1) if side == 'left' else (hi, -1)
        w = width * math.sin(math.pi * t) ** 0.5
        outer.append((x + sign * inset, y))
        inner.append((x + sign * (inset + w), y))
    return outer + inner[::-1]


def strap(a, b, toward, outline, width, inset):
    """The centreline of a band width px wide along the line through screen points a and b, on its side toward
    `toward`, from the outline's top to its bottom. Where the line runs out through the outline's side the band
    turns and runs on down it, inset px in from the edge, as a strap bent round the pedestal."""
    d = (b - a) / np.linalg.norm(b - a)
    if d[1] < 0:
        d = -d
    n = np.array([-d[1], d[0]])
    if np.dot(n, toward - a) < 0:
        n = -n
    ys = [y for _, y in outline]
    top, bottom = min(ys), max(ys)
    centre = []
    for t in np.arange(-800.0, 800.0, 1.0):
        x, y = a + n * width / 2 + d * t
        if top <= y <= bottom + RING_TUCK_PX:
            lo, hi = span_at([outline], min(y, bottom - RING_TUCK_PX))
            lo, hi = lo + inset + width / 2, hi - inset - width / 2
            if lo <= hi:
                centre.append((min(max(x, lo), hi), y))
    # rounded where it bends, or its edges cross over at the corner
    half = int(width)
    xs = [x for x, _ in centre]
    return [(float(np.mean(xs[max(0, i - half):i + half + 1])), y) for i, (_, y) in enumerate(centre)]


def strap_band(centre, width):
    left, right = band(centre, [width / 2] * len(centre))
    return [tuple(p) for p in left + right[::-1]]


def strap_streak(centre, width):
    """The highlight down a strap's left edge, which faces the light whichever way the strap leans."""
    inset, w, _ = RIB_STREAK
    count = len(centre)
    taper = [math.sin(math.pi * k / (count - 1)) ** 0.5 for k in range(count)]
    outer, _ = band(centre, [width / 2 - inset] * count)
    inner, _ = band(centre, [width / 2 - inset - w * t for t in taper])
    return [tuple(p) for p in outer + inner[::-1]]


def lattice(scene, out, name, c, r, h0, h1, gem):
    """The painting's lattice: a gold ring round the gem, its two lower edges running on as straps up to the
    lattice's top, mirrored about the gem whichever way the pedestal turns, and a rib down each side."""
    angle, h, hw, hh = gem
    out.group(name)
    core = lathe_outline(scene, c, r, h0, h1, steps=30)
    out.shape(name + ' core', core, 'gold dark', 'gold')
    graded(scene, out, name + ' core', c, r, h0 + 0.002 * (h1 - h0), h1, CORE_STOPS)
    colour, share, layers, opacity = CORE_GLOW
    for k in range(layers):
        out.shape('%s core glow %d' % (name, k + 1), hband(scene, c, r, h0, h0 + share * (h1 - h0) * (k + 1) / layers),
                  colour, 'none', 0, opacity)
    # set upright on a cylinder through the gem's middle, as the painting stands it, not leaning with the flare
    rad = r(h * PX) + STRAP_STANDOFF * 1.5
    mapf = on_surface(scene, c, lambda q: rad, angle)
    ow, oh = (v * PX for v in RING_OUTER)
    top, right, bottom, left = map(np.array, mapf([(0.0, h * PX + oh), (ow, h * PX), (0.0, h * PX - oh), (-ow, h * PX)]))
    # mirrored about the gem: the side corners level, as far either side of the axis through its tips
    level, half = (left[1] + right[1]) / 2, (right[0] - left[0]) / 2
    axis = lambda y: top[0] + (bottom[0] - top[0]) * (y - top[1]) / (bottom[1] - top[1])
    left, right = np.array([axis(level) - half, level]), np.array([axis(level) + half, level])
    middle = (top + bottom) / 2
    gem_x = axis(middle[1])
    # only the ring's lower edges run on, up and out to the top: below its side corners lie open panels
    for family, edges in (('left', ((left, bottom),)), ('right', ((bottom, right),))):
        for i, (a, b) in enumerate(edges):
            centre = strap(a, b, middle, core, STRAP_PX, RIB_PX + STRAP_GAP_PX)
            band_ = within(core, strap_band(centre, STRAP_PX), RING_TUCK_PX)
            xs = [x for x, _ in band_]
            paint = 'gold strap shade' if (min(xs) + max(xs)) / 2 > gem_x + STRAP_SHADE_PX else 'gold strap'
            label = '%s strap %s %d' % (name, family, 10 * i)
            out.shape(label, band_, paint, paint[5:], STRAP_STROKE)
            out.shape(label + ' sheen', within(core, strap_streak(centre, STRAP_PX), RING_TUCK_PX), SHEEN[paint[5:]], 'none', 0)
    for side, paint_ in (('left', 'gold strap'), ('right', 'gold strap shade')):
        out.shape('%s rib %s' % (name, side), rib(core, side), paint_, paint_[5:], STRAP_STROKE)
        out.shape('%s rib %s sheen' % (name, side), rib_streak(core, side), SHEEN[paint_[5:]], 'none', 0)
    # its tips run on under the top and the collar, the bottom one no further than the collar hides it
    tuck = max(y for _, y in core) + RING_TUCK_PX
    ring = [(x, min(y, tuck)) for x, y in densify([tuple(p) for p in (top, right, bottom, left)], 8)]
    out.shape(name + ' ring', ring, RING_TONES['lit'], 'strap', STRAP_STROKE)
    # its corners run top, right, bottom, left: the right half is the first half
    out.shape(name + ' ring dark half', ring[:len(ring) // 2 + 1], RING_TONES['shade'], 'none', 0)
    out.line(name + ' ring edge', ring + ring[:1], OUTLINE['strap'], STRAP_STROKE)
    draw_gem(out, name + ' gem front', mapf, 0.0, h * PX, hw * PX, hh * PX, glint=None)
    out.end()


def bell(scene, out, name, c, r, h0, h1, gem, frame):
    """A smooth gold bell, lit pale on the left and going orange to the right, with one gem framed on its front."""
    angle, h, hw, hh = gem
    out.group(name)
    out.shape(name, lathe_outline(scene, c, r, h0, h1, steps=30), 'gold', 'gold')
    graded(scene, out, name, c, r, h0 + 0.002 * (h1 - h0), h1, BELL_STOPS)
    draw_gem(out, name + ' gem front', on_surface(scene, c, lambda q: r(q) + STRAP_STANDOFF, angle),
             0.0, h * PX, hw * PX, hh * PX, outer=(frame[0] * PX, frame[1] * PX))
    out.end()


def draw_table(scene, out, c):
    out.group('table')
    out.group('pedestal')
    disc(scene, out, 'pedestal foot', c, FOOT_RADIUS, 0.0, FOOT_HEIGHT, 'gold strap', stops=BASE_STOPS, r=foot)
    out.shape('pedestal foot underside', hband(scene, c, foot, 0.0, 0.22 * FOOT_HEIGHT), '#b66102', 'none', 0, 0.6)
    out.group('pedestal plinth')
    out.shape('pedestal plinth ledge', ring(scene, c, PLINTH_TOP, plinth(PLINTH_TOP), 96), GOLD_TONES['glint'], 'gold')
    out.end()
    bell(scene, out, 'pedestal lower bell', c, lower_bell, PLINTH_TOP, LOWER_TOP, LOWER_GEM, LOWER_GEM_FRAME)
    out.group('pedestal plinth front')
    out.shape('pedestal plinth rim', lathe_outline(scene, c, plinth, FOOT_HEIGHT, PLINTH_TOP, cap=False), 'gold', 'gold')
    graded(scene, out, 'pedestal plinth rim', c, plinth, FOOT_HEIGHT + 0.1 * (PLINTH_TOP - FOOT_HEIGHT),
           PLINTH_TOP - 0.1 * (PLINTH_TOP - FOOT_HEIGHT), BASE_STOPS)
    out.shape('pedestal plinth sheen', hband(scene, c, plinth, FOOT_HEIGHT + 0.55 * (PLINTH_TOP - FOOT_HEIGHT),
                                              FOOT_HEIGHT + 0.8 * (PLINTH_TOP - FOOT_HEIGHT), -20, 75), GOLD_TONES['glint'], 'none')
    out.end()
    occlusion(scene, out, 'pedestal shade under collar', c, lower_bell, LOWER_TOP,
              8 * PX, layers=3)
    lattice(scene, out, 'pedestal upper lattice', c, upper_lattice, KNOB_TOP, APRON_BOTTOM, UPPER_GEM)
    # the top's shadow falling on the upper lattice
    occlusion(scene, out, 'pedestal shade under top', c, lambda h: upper_lattice(h) + STRAP_STANDOFF * 2, APRON_BOTTOM,
              TOP_SHADOW * PX, layers=5, opacity=0.12)
    out.shape('pedestal shade under rim', hband(scene, c, lambda h: upper_lattice(h) + 2 * STRAP_STANDOFF, APRON_BOTTOM - 10 * PX,
                                                APRON_BOTTOM),
              '#6a2601', 'none', 0, 0.5)
    out.group('pedestal collar group')
    out.shape('pedestal collar', lathe_outline(scene, c, knob, LOWER_TOP, KNOB_TOP, cap=False), 'gold', 'gold')
    graded(scene, out, 'pedestal collar', c, knob, LOWER_TOP + 0.12 * (KNOB_TOP - LOWER_TOP),
           KNOB_TOP - 0.08 * (KNOB_TOP - LOWER_TOP), COLLAR_STOPS)
    out.shape('pedestal collar underside', hband(scene, c, knob, LOWER_TOP, LOWER_TOP + 0.25 * (KNOB_TOP - LOWER_TOP)),
              GOLD_TONES['deep'], 'none', 0, 0.6)
    out.shape('pedestal collar sheen', lens(scene, c, knob, KNOB_TOP - 0.45 * (KNOB_TOP - LOWER_TOP),
                                              KNOB_TOP - 0.25 * (KNOB_TOP - LOWER_TOP), -20, 75), GOLD_TONES['glint'], 'none')
    # the painting splits the collar into a thin ring over a fat one
    out.shape('pedestal collar groove', hband(scene, c, knob, KNOB_TOP - 0.3 * (KNOB_TOP - LOWER_TOP),
                                              KNOB_TOP - 0.22 * (KNOB_TOP - LOWER_TOP)), '#9a4a04', 'none', 0, 0.8)
    out.end()
    out.end()

    out.group('table top')
    out.shape('table apron', lathe_outline(scene, c, lambda h: APRON_RADIUS, APRON_BOTTOM, UNDER + 2 * PX), 'gold dark', 'gold')
    graded(scene, out, 'table apron', c, lambda h: APRON_RADIUS, APRON_BOTTOM, UNDER, [(c_, mix(v, '#8a5418', 0.3)) for c_, v in GOLD_STOPS], 2)
    edge = lambda h: TOP_RADIUS
    out.shape('table edge', lathe_outline(scene, c, edge, UNDER, TABLE_HEIGHT), 'gold band', 'gold')
    graded(scene, out, 'table edge', c, edge, UNDER, TABLE_HEIGHT, EDGE_STOPS, 5)
    out.shape('table edge underside', hband(scene, c, edge, UNDER, UNDER + 0.15 * TOP_THICKNESS), '#c86a06', 'none', 0, 0.35)
    out.shape('table edge highlight', hband(scene, c, edge, TABLE_HEIGHT - 0.2 * TOP_THICKNESS, TABLE_HEIGHT - 0.04 * TOP_THICKNESS,
                                            70, 185), '#fdf9c3', 'none', 0, 0.85)
    # wide enough to hide the band's own darker outline along the top's far edge
    out.shape('table lip', ring(scene, c, TABLE_HEIGHT, TOP_RADIUS, 128), 'marble', MARBLE_BACK_LINE, STROKE + 0.5)
    out.shape('table edge bevel', arc_band(scene, c, TABLE_HEIGHT, TOP_RADIUS - TOP_INSET, TOP_RADIUS - 0.2 * PX, 25, 160, 60),
              '#fff4c4', 'none')
    marble = TOP_RADIUS - TOP_INSET
    out.shape('table marble', ring(scene, c, TABLE_HEIGHT, marble, 128), 'marble', 'none', 0)

    def patch(name, a0, a1, r0, r1, colour, wobble=0.04):
        ts = np.linspace(a0, a1, 18)
        pts = [(marble * (r1 + wobble * math.sin(math.radians(5 * t))), t) for t in ts]
        pts += [(marble * (r0 + wobble * math.cos(math.radians(4 * t))), t) for t in ts[::-1]]
        out.shape(name, [scene.project((c[0] + r * math.cos(math.radians(t)), TABLE_HEIGHT, c[2] - r * math.sin(math.radians(t))))
                         for r, t in pts], colour, 'none')
    patch('table marble shade', -45, 80, 0.62, 0.97, MARBLE_TONES['shade'])
    patch('table marble shade edge', -30, 60, 0.86, 0.99, MARBLE_TONES['edge'], 0.01)
    patch('table marble cloud 1', 120, 175, 0.25, 0.7, MARBLE_TONES['cloud'])
    patch('table marble cloud 2', 200, 250, 0.35, 0.8, MARBLE_TONES['cloud'])
    patch('table marble cloud 3', 20, 60, 0.2, 0.55, MARBLE_TONES['cloud'])
    for k, vein in enumerate(MARBLE_VEINS):
        pts = densify_open(vein, 8)
        out.line('table marble vein %d' % (k + 1),
                 [scene.project((c[0] + marble * r * math.cos(math.radians(t)), TABLE_HEIGHT, c[2] - marble * r * math.sin(math.radians(t))))
                  for r, t in pts], MARBLE_TONES['vein'], 2.6, 0.4)
    patch('table marble sheen', 150, 235, 0.5, 0.84, MARBLE_SHEEN, 0.02)
    patch('table marble glint', 175, 205, 0.62, 0.74, '#ffffff', 0.01)
    out.line('table marble front edge', [scene.project((c[0] + marble * math.cos(t), TABLE_HEIGHT, c[2] - marble * math.sin(t)))
                                         for t in np.radians(np.linspace(-8, 188, 80))], MARBLE_LINE, 2)
    out.end()
    out.end()


def densify_open(line, per=6, wiggle=0.005):
    """An open polyline of (r, angle) points, filled in and wavering a little across its run."""
    out = []
    for (r0, t0), (r1, t1) in zip(line, line[1:]):
        for i in range(per):
            f = i / per
            out.append((r0 + (r1 - r0) * f + wiggle * math.sin(7 * (len(out) + 1) / per), t0 + (t1 - t0) * f))
    return out + [line[-1]]


def densify(poly, per=6):
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        out += [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in np.linspace(0, 1, per, endpoint=False)]
    return out


# ---------------------------------------------------------------- chairs

def cushion_r(h):
    t = min(max((h - SEAT_HEIGHT + 0.006) / CUSHION_RISE, 0.0), 1.0)
    return CUSHION_RADIUS * (1 - t ** CUSHION_ROUND) ** (1 / CUSHION_ROUND)


def cushion_height(rho):
    """Height of the cushion dome at distance rho from the seat axis."""
    q = min(rho / CUSHION_RADIUS, 0.999)
    return SEAT_HEIGHT - 0.006 + CUSHION_RISE * (1 - q ** CUSHION_ROUND) ** (1 / CUSHION_ROUND)


# Back drawings in (u, v): u across (arc length, eye heights), v up in back heights,
# v = 0 at the top of the seat rail. Right halves, listed bottom to top.
# The frame starts at the flare tip lying on the rail and runs up the stile to the top.
# A shield: near-straight sides up to the widest point, then shoulders rounding in to the crest.
BACK_FRAME = [(0.2, 0.0), (0.165, 0.004), (0.132, 0.024), (0.112, 0.07), (0.108, 0.16), (0.111, 0.31),
              (0.116, 0.47), (0.118, 0.6), (0.111, 0.74), (0.094, 0.845), (0.07, 0.905), (0.042, 0.935), (0.018, 0.948),
              (0.0, 0.95)]
OUTER_PANEL = [(0, 0.1), (0.05, 0.1), (0.076, 0.16), (0.087, 0.31), (0.093, 0.47), (0.095, 0.6), (0.088, 0.73),
               (0.072, 0.815), (0.045, 0.86), (0.0, 0.875)]
HEART = [(0, 0.25), (0.026, 0.34), (0.05, 0.46), (0.062, 0.58), (0.062, 0.68), (0.052, 0.75), (0.032, 0.78),
         (0.013, 0.762), (0.0, 0.735)]
CREST = [(0, 0.88), (0.036, 0.9), (0.042, 0.93), (0.03, 0.965), (0.012, 0.995), (0.0, 1.04)]
# spirals on the back: (u, v, radius, start angle, turn, width), mirrored left and right
CREST_CURL = (0.036, 0.93, 0.024, -0.8, 1, 0.012)   # C-scrolls rising from the shoulders to the tip
EAR_CURL = (0.084, 0.8, 0.012, 2.6, -1, 0.008)
FILIGREE = (0.034, 0.18, 0.017, 0.35, -1, 0.009)


class ChairBack:
    """The chair back as one shell with the seat rail. Below v = 0 it is the rail's own
    outer surface; above, it bends round the seat at the rail's radius and flattens out
    towards the crest."""

    def __init__(self, scene, s, f, side, height=None, tilt=None):
        self.scene, self.s, self.f, self.side = scene, s, f, side
        self.height = BACK_HEIGHT if height is None else height
        self.up = np.array([0, 1.0, 0]) + (-f) * (BACK_TILT if tilt is None else tilt)

    def radius(self, v):
        return BACK_RIM + BACK_BEND * max(v, 0.0)

    def point(self, u, v, depth=0.0):
        """World point; depth > 0 is outwards, away from the seat."""
        u *= 1 + BACK_TAPER * max(v, 0.0)
        if v < 0:
            h = SEAT_HEIGHT + v * self.height
            a = BACK_WIDTH * u / BACK_RIM
            return rim_point(self.s, self.f, self.side, a, rail_radius(h) + RAIL_SKIN + depth, h)
        R = self.radius(v)
        base = (self.s + np.array([0, SEAT_HEIGHT, 0]) - self.f * BACK_RIM + v * self.height * self.up
                - self.f * BACK_CURVE * self.height * v * v)
        a = BACK_WIDTH * u / R
        return base + self.f * R + (R + depth) * (math.sin(a) * self.side - math.cos(a) * self.f)

    def shape(self, points, depth=0.0):
        return [self.scene.project(self.point(u, v, depth)) for u, v in points]


def quilt_grid(polygon, spacing, offset=(0.0, 0.0)):
    """Diamond quilting over a 2D polygon: each cell's four corners, and the crossings where
    cells meet. Cells and crossings reach one row past the polygon so it can be cut by it."""
    xs, ys = zip(*polygon)
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    c = np.array([(max(xs) + min(xs)) / 2 + offset[0], (max(ys) + min(ys)) / 2 + offset[1]])
    k = math.sqrt(0.5)
    na, nb = np.array([k, k]), np.array([k, -k])
    n = int(span / spacing) + 2
    cells, crossings = [], []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            crossings.append(c + i * spacing * na + j * spacing * nb)
            m = c + (i + 0.5) * spacing * na + (j + 0.5) * spacing * nb
            cells.append([m + 0.5 * spacing * v for v in (na + nb, nb - na, -na - nb, na - nb)])
    return cells, crossings, (na, nb)


def rounded_cell(corners, cut=QUILT['corner']):
    """A quilting cell with its corners rounded off, so neighbours share their edges and leave
    a small hole at each crossing: the dimple."""
    pts = []
    for i, q in enumerate(corners):
        a, b = corners[i - 1], corners[(i + 1) % 4]
        pts += [q + (a - q) * cut, q + (b - q) * cut]
    return catmull([tuple(p) for p in pts], 3)


def pillow(out, name, pts, level):
    """One quilted panel from its screen outline, all opaque: the panel in its darker tone,
    the puff in its own tone shifted up-left, and a lighter crown on its upper left."""
    p = np.array(pts)
    c = p.mean(axis=0)
    w, h = np.ptp(p[:, 0]) + 1e-6, np.ptp(p[:, 1]) + 1e-6
    tones = QUILT['tones']
    out.shape(name, [tuple(q) for q in p], tones[level], 'none')
    out.shape(name + ' puff', [tuple(c + (q - c) * 0.84 + (-0.05 * w, -0.07 * h)) for q in p], tones[level + 1], 'none')
    out.shape(name + ' crown', [tuple(c + (q - c) * 0.42 + (-0.15 * w, -0.17 * h)) for q in p], tones[level + 2], 'none')


def dimple(out, name, centre, arms, width, limit=None):
    """A button point where four panels meet, with short creases running out along the seams
    and tapering to nothing."""
    c = np.array(centre)
    for k, end in enumerate(arms):
        d = np.array(end) - c
        if limit is not None and np.linalg.norm(d) > limit:
            # where the surface turns away a crease would stretch down its side
            d *= limit / np.linalg.norm(d)
        n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-9) * width
        out.shape('%s crease %d' % (name, k + 1), [tuple(c + n), tuple(c + d), tuple(c - n)], QUILT['seam'], 'none')
    r = width * 1.2
    out.shape(name, [(c[0] + 1.3 * r * math.cos(t), c[1] + 0.8 * r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 10, endpoint=False)],
              QUILT['pit'], 'none')


def rail_radius(h):
    return SEAT_RADIUS + RIM_LIP + 0.2 * (h - (SEAT_HEIGHT - SEAT_FRAME))


def rim_point(s, f, side, angle, radius, h):
    """A point on a circle round the seat axis; angle 0 is the middle of the back."""
    return s + radius * (math.sin(angle) * side - math.cos(angle) * f) + np.array([0, h, 0])


def dense_uv(points, step=0.006):
    out = []
    for a, b in zip(points, points[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        out += [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in np.linspace(0, 1, n, endpoint=False)]
    out.append(points[-1])
    return out


class ChairView:
    """A scene that draws one chair scaled by k about its seat's floor point s; the
    eye is moved the other way so what faces it is decided as it will be drawn."""

    def __init__(self, scene, s, k):
        self.scene, self.s, self.k = scene, np.asarray(s, float), k
        self.cam = scene.cam
        self.eye = self.s + (scene.eye - self.s) / k

    def project(self, p):
        return self.scene.project(self.s + self.k * (np.asarray(p, float) - self.s))

    def scale(self, p):
        return self.k * self.scene.scale(self.s + self.k * (np.asarray(p, float) - self.s))


def draw_chair(scene, out, name, s, forward, apron_scrolls=True):
    size, stretch, tilt, toe_out = CHAIR_TWEAKS.get(name, (1.0, 1.0, BACK_TILT, TOE_OUT))
    scene = ChairView(scene, s, size)
    back_height = BACK_HEIGHT * stretch
    f0 = np.array([forward[0], 0.0, forward[1]])
    side0 = np.array([-f0[2], 0.0, f0[0]])
    # the back and the rail are laid out round the seat from the back's middle
    turn = math.radians(BACK_TURN.get(name, 0.0))
    f = f0 * math.cos(turn) + side0 * math.sin(turn)
    side = np.array([-f[2], 0.0, f[0]])
    seat_bottom = SEAT_HEIGHT - SEAT_FRAME
    cushion_top = SEAT_HEIGHT + CUSHION_RISE
    seat_mid = s + np.array([0, SEAT_HEIGHT, 0])
    back = ChairBack(scene, s, f, side, back_height, tilt)
    back_shape = back.shape
    inner_visible = float(np.dot(f, scene.eye - back.point(0, 0.5))) > 0
    v_rail = -SEAT_FRAME / back_height

    def faces_eye(angle, h):
        p = rim_point(s, f, side, angle, rail_radius(h), h)
        n = math.sin(angle) * side - math.cos(angle) * f
        return float(np.dot(n, scene.eye - p)) > 0

    def arc(h, around_back):
        """Angles (from the back's middle) of the rail's half that faces the eye, or of the
        half that faces away, whichever contains the back's middle when around_back."""
        want = faces_eye(0.0, h) if around_back else True
        if not around_back:
            # the eye-facing half, centred on the direction of the eye
            e = scene.eye - s
            mid = math.atan2(float(np.dot(e, side)), float(-np.dot(e, f)))
        else:
            mid = 0.0
        lo = hi = mid
        step = 0.01
        while faces_eye(lo - step, h) == want and hi - lo < 2 * math.pi - 0.1:
            lo -= step
        while faces_eye(hi + step, h) == want and hi - lo < 2 * math.pi - 0.1:
            hi += step
        return lo, hi

    def band_outline(around_back, frame=None):
        """(u, v) outline of half the rail band; with a frame, the frame grows out of its top."""
        (lb, hb), (lt, ht) = arc(seat_bottom, around_back), arc(SEAT_HEIGHT, around_back)
        k = BACK_RIM / BACK_WIDTH
        bottom = [(k * a, v_rail) for a in np.linspace(lb, hb, 60)]
        right = [(k * (hb + (ht - hb) * t), v_rail * (1 - t)) for t in np.linspace(0, 1, 6)[1:]]
        left = [(k * (lt + (lb - lt) * t), v_rail * t) for t in np.linspace(0, 1, 6)[1:]]
        if frame is None:
            top = [(k * a, 0.0) for a in np.linspace(ht, lt, 60)]
        else:
            # flare tips past the rail's turning edge would fold over the cushion: cut them off there
            frame = [(u, v) for u, v in frame if v > FLARE_CUT or k * lt <= u <= k * ht]
            r_tip, l_tip = frame[0][0], frame[-1][0]
            top = [(u, 0.0) for u in np.linspace(k * ht, r_tip, 30) if u > r_tip] + frame
            top += [(u, 0.0) for u in np.linspace(l_tip, k * lt, 30) if u < l_tip]
        return bottom + right + top + left

    def rail_stripes(around_back, label):
        """Flat sheen and shade stripes running round the rail's half, as on the turned parts."""
        lo, hi = arc(seat_bottom + 0.5 * SEAT_FRAME, around_back)
        k = BACK_RIM / BACK_WIDTH
        us = np.linspace(k * lo + 0.012, k * hi - 0.012, 50)
        for part, (a, b), colour in (('sheen', RAIL_SHEEN, TURNED_SHEEN['gold']), ('shade', RAIL_SHADE, SHADE['gold'])):
            band = [(u, v_rail * a) for u in us] + [(u, v_rail * b) for u in us[::-1]]
            out.shape('%s %s %s' % (name, label, part), back_shape(band, 0.001), colour, 'none')

    frame_half = catmull(BACK_FRAME, 6, closed=False)
    frame_line = frame_half + [(-u, v) for u, v in reversed(frame_half) if u > 1e-9]

    def cream_light(label, pts):
        lit, dark = screen_bevels(pts, CREAM_LIGHT['px'], 1.0)
        for k, st in enumerate(dark):
            out.shape('%s shade %d' % (label, k + 1), st, CREAM_LIGHT['shade'], 'none')
        for k, st in enumerate(lit):
            out.shape('%s light %d' % (label, k + 1), st, CREAM_LIGHT['light'], 'none')

    def spiral_pair(label, params, width=2.5):
        cu, cv, cr, start, turn, w = params
        for side_label, sign in (('left', -1), ('right', 1)):
            # spirals are round in world units; v is in back heights
            curl = spiral(sign * cu, 0.0, cr, math.pi / 2 - sign * (math.pi / 2 - start), turn * sign, w)
            out.bevelled('%s back %s %s' % (name, label, side_label),
                         back_shape([(u, cv + y * BACK_WIDTH / back_height) for u, y in curl]), 'gold', 'gold', 1.6, width)

    def draw_back(band_around_back):
        """The back, grown out of the half of the rail behind or in front of the cushion."""
        out.group(name + ' back')
        crest = catmull(mirrored(CREST), 5)
        # seen from behind, u runs right to left on screen; gems light their +u side, so flip it
        gem_shape = back_shape if inner_visible else (lambda pts: back_shape([(-u, v) for u, v in pts]))
        away = BACK_THICKNESS if inner_visible else -BACK_THICKNESS
        # the frame's thickness fades out towards its foot, where it becomes the rail
        # it runs on straight down the stile to the seat rail, below where the flares are cut
        stile = [(u, v) for u, v in frame_line if v >= FLARE_CUT]
        foot = lambda u: [(u, v) for v in np.linspace(0.0, FLARE_CUT, 6, endpoint=False)]
        stile = foot(stile[0][0]) + stile + foot(stile[-1][0])[::-1]
        edge = [scene.project(back.point(u, v, away * min(1.0, max(v, 0.0) / EDGE_FADE))) for u, v in stile]
        # the edge is the stile's side face: lit when it shows on the back's left (BRIEF "Lighting")
        frame_x = np.mean([q[0] for q in back_shape(frame_line)])
        if np.mean([q[0] for q in edge]) < frame_x:
            out.bevelled(name + ' back frame edge', edge, w1=2.5)
        else:
            out.shape(name + ' back frame edge', edge, 'gold dark', 'gold')
        out.bevelled(name + ' back frame and rail', back_shape(dense_uv(band_outline(band_around_back, frame_line))))
        rail_stripes(band_around_back, 'back rail stripe')
        if inner_visible:
            out.shape(name + ' back inner panel', back_shape(catmull(mirrored(OUTER_PANEL), 6)), 'cream', 'gold')
            cream_light(name + ' back inner panel', back_shape(catmull(mirrored(OUTER_PANEL), 6)))
            heart = catmull(mirrored(HEART), 6)
            out.shape(name + ' back cushion', back_shape(heart), QUILT['tones'][1], 'none')
            out.group(name + ' back quilting')
            hull = [tuple(q) for q in np.array(heart)[ConvexHull(np.array(heart)).vertices]]
            inside = Path(np.array(heart))
            # laid out in true lengths across and up the back, then taken back to (u, v)
            to_uv = np.array([1 / BACK_WIDTH, 1 / back_height])
            spacing = BACK_QUILT
            cells, crossings, (na, nb) = quilt_grid([(u * BACK_WIDTH, v * back_height) for u, v in heart], spacing,
                                                    offset=(0.0, 0.01))
            cells = [[q * to_uv for q in c] for c in cells]
            crossings = [q * to_uv for q in crossings]
            na_uv, nb_uv = na * to_uv, nb * to_uv
            for k, c in enumerate(cells):
                m = np.mean(c, axis=0)
                if inside.contains_point(m):
                    q = clip_convex(densify(rounded_cell(c), 2), hull)
                    if len(q) > 3:
                        # lit from the top left: u runs left to right on screen when the inside shows
                        level = int(min(4, max(0, 1 + (m[1] > 0.6) + (m[0] < -0.005) - (m[1] < 0.42))))
                        pillow(out, '%s back panel %d' % (name, k + 1), back_shape(q), level)
            for k, c in enumerate(crossings):
                if inside.contains_point(c, radius=-0.02):
                    w = back.point(*c)
                    ends = back_shape([c + QUILT['crease'] * spacing * v for v in (na_uv, -na_uv, nb_uv, -nb_uv)])
                    dimple(out, '%s back dimple %d' % (name, k + 1), scene.project(w), ends, QUILT['crease px'] * 0.85)
            out.end()
            out.shape(name + ' back cushion outline', back_shape(heart), 'none', QUILT['seam'])
        else:
            panel = catmull(mirrored(OUTER_PANEL), 6)
            lip = [(u * 1.07, 0.49 + (v - 0.49) * 1.03) for u, v in panel]
            out.shape(name + ' back panel recess', back_shape(lip), 'gold dark', 'none')
            out.shape(name + ' back panel', back_shape(panel), 'cream', 'gold')
            cream_light(name + ' back panel', back_shape(panel))
            draw_gem(out, name + ' back gem', gem_shape, 0.0, 0.52, 0.034, 0.165, outer=(0.05, 0.19))
        out.bevelled(name + ' back filigree drop', back_shape(mirrored([(0, 0.125), (0.014, 0.175), (0, 0.235)])), w1=2.0)
        spiral_pair('filigree', FILIGREE, 2.2)
        out.bevelled(name + ' back crest', back_shape(crest), w1=2.5)
        draw_gem(out, name + ' back crest gem', gem_shape, 0.0, 0.975, 0.014, 0.03)
        spiral_pair('crest curl', CREST_CURL)
        spiral_pair('ear', EAR_CURL, 2.2)
        out.end()

    # ---- legs: cabriole S-curves, knee out, slim ankle, curled foot
    def leg(dirn):
        d = dirn / np.linalg.norm(dirn)
        reach = toe_out * SEAT_RADIUS
        line = [s + d * (LEG_SPREAD + du + reach * (1 - h / LEG_PROFILE[0][1]) ** 2) + np.array([0, h, 0])
                for du, h in LEG_PROFILE]
        return d, line

    legs = []
    for label, a, b in (('front left', 1, -1), ('front right', 1, 1), ('back left', -1, -1), ('back right', -1, 1)):
        d, line = leg(a * f0 + b * side0)
        legs.append((np.linalg.norm(line[-1] - scene.eye), label, d, line))
    legs.sort(key=lambda x: -x[0])

    def draw_leg(label, d, line):
        out.group('%s leg %s group' % (name, label))
        knee, ankle, toe = LEG_WIDTH
        widths = [knee * 0.9, knee, knee * 0.95, knee * 0.75, ankle * 1.25, ankle, ankle * 1.1, toe]
        out.bevelled('%s leg %s' % (name, label), ribbon(scene, line, widths))
        up = np.array([0, 1.0, 0])
        foot = line[-1]
        r = FOOT_BALL * scene.scale(foot)
        cx, cy = scene.project(foot)
        out.bevelled('%s foot %s' % (name, label),
                     [(cx + r * 1.3 * math.cos(t), cy + r * 0.8 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)],
                     'gold dark', w1=2.0)
        view = foot - scene.eye
        across = np.array([view[2], 0.0, -view[0]])
        across /= np.linalg.norm(across)
        if float(np.dot(across, d)) < 0:
            across = -across
        toe_curl = spiral(0.0, 0.0, FOOT_CURL[0], -math.pi * 0.4, 1, FOOT_CURL[1])
        out.shape('%s foot %s curl' % (name, label),
                  [scene.project(foot + across * (x + FOOT_CURL[0] * 0.6) + up * (y + FOOT_CURL[0])) for x, y in toe_curl],
                  'gold', 'gold', 2.2)
        out.end()

    def draw_bracket(label, d, line):
        """C-scroll on the knee's outer face, just under the rail."""
        up = np.array([0, 1.0, 0])
        knee = line[1] + d * 0.012
        view = knee - scene.eye
        across = np.array([view[2], 0.0, -view[0]])
        across /= np.linalg.norm(across)
        if scene.project(knee)[0] > scene.project(s)[0]:
            across = -across
        curl = spiral(0.0, 0.0, BRACKET_CURL[0], math.pi * 0.95, -1, BRACKET_CURL[1], turns=1.0)
        out.shape('%s leg %s bracket' % (name, label),
                  [scene.project(knee + across * x + up * y) for x, y in curl], 'gold', 'gold', 2.2)

    # ---- seat
    apron = s + f0 * (rail_radius(seat_bottom + SEAT_FRAME * 0.5)) + np.array([0, seat_bottom + SEAT_FRAME * 0.5, 0])
    apron_visible = float(np.dot(f0, scene.eye - apron)) > 0

    def draw_apron():
        if apron_visible and apron_scrolls:
            for label, sign in (('left', -1), ('right', 1)):
                curl = spiral(sign * 0.02, 0.0, APRON_CURL[0], math.pi - (sign > 0) * math.pi, sign, APRON_CURL[1])
                out.shape('%s apron scroll %s' % (name, label),
                          [scene.project(apron + side0 * x + np.array([0, y, 0])) for x, y in curl], 'gold', 'gold', 2.2)

    def rail_occlusion():
        occlusion(scene, out, name + ' seat rail shade under cushion', s, rail_radius, SEAT_HEIGHT,
                  0.45 * SEAT_FRAME, lift=RAIL_SKIN + 0.001, layers=3, opacity=0.16)

    def draw_rail_behind():
        out.group(name + ' seat rail')
        out.turned(scene, name + ' seat frame', s, rail_radius, seat_bottom, SEAT_HEIGHT)
        # the rail's flat top; the cushion covers all but the lip in front of it
        out.shape(name + ' seat rail top', ring(scene, s, SEAT_HEIGHT, rail_radius(SEAT_HEIGHT) + RAIL_SKIN, 72),
                  GOLD_TONES['lit'], 'gold', 2)
        rail_occlusion()
        out.end()

    def draw_rail_front():
        out.group(name + ' seat rail front group')
        out.bevelled(name + ' seat rail front', back_shape(dense_uv(band_outline(False))))
        rail_stripes(False, 'seat rail stripe')
        rail_occlusion()
        draw_apron()
        out.end()

    def draw_cushion():
        out.group(name + ' cushion group')
        silhouette = lathe_outline(scene, s, cushion_r, SEAT_HEIGHT - 0.006, cushion_top - 0.008, steps=30)
        out.shape(name + ' cushion', silhouette, SEAT_FRONT_BAND, 'none')
        # The quilting is laid out flat by distance along the dome's profile, so the outer panels
        # wrap down over its side as far as the seat rail rather than squeezing at the rim.
        rhos = np.linspace(0, CUSHION_RADIUS * 0.999, 80)
        prof_r = np.append(rhos, CUSHION_RADIUS)
        prof_h = np.append([cushion_height(r) for r in rhos], SEAT_HEIGHT - 0.006)
        prof_s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(prof_r), np.diff(prof_h)))])
        prof_n = np.stack([-np.gradient(prof_h, prof_s), np.gradient(prof_r, prof_s)], 1)
        reach = prof_s[-1] * TUFT_REACH
        disc = circle(0, 0, reach, 48)
        cell = TUFT_SPACING * SEAT_TUFT_SCALE
        cells, crossings, (na, nb) = quilt_grid(disc, cell)

        def lift(p):
            x, z = p
            d = math.hypot(x, z)
            r, h = np.interp(d, prof_s, prof_r), np.interp(d, prof_s, prof_h)
            k = r / d if d > 1e-9 else 0.0
            return s + side * x * k + f * z * k + np.array([0, h, 0])

        def normal(p):
            d = math.hypot(*p)
            radial = (side * p[0] + f * p[1]) / d if d > 1e-9 else np.zeros(3)
            nr, nh = np.interp(d, prof_s, prof_n[:, 0]), np.interp(d, prof_s, prof_n[:, 1])
            n = nr * radial + np.array([0, nh, 0])
            return n / np.linalg.norm(n)

        def facing_sun(p):
            return float(np.dot(normal(p), SUN_TOWARD))

        to_screen = lambda pts: [scene.project(lift(p)) for p in pts]
        panels = []
        for c in cells:
            m = np.mean(c, axis=0)
            if math.hypot(*m) < reach + 0.5 * cell:
                q = clip_convex(densify(rounded_cell(c), 2), disc)
                if len(q) > 3:
                    panels.append((m, q))
        lo, hi = SEAT_LIT_RANGE
        levels = [int(round(3 * min(1.0, max(0.0, (facing_sun(m) - lo) / (hi - lo))))) for m, _ in panels]
        # the sheen: the panels nearest a spot on the dome's top left; where the back stands on
        # the screen left it would hide that spot, so it turns towards the camera
        back_left = scene.project(back.point(0, 0.3))[0] < scene.project(seat_mid)[0]
        a = math.radians(82 if back_left else 150)
        spot = s + np.array([0.45 * CUSHION_RADIUS * math.cos(a), 0, -0.45 * CUSHION_RADIUS * math.sin(a)])
        near = sorted(range(len(panels)), key=lambda i: np.linalg.norm((lift(panels[i][0]) - spot)[[0, 2]]))
        for i in near[:SEAT_SHEEN_PANELS]:
            levels[i] = 4
        # far panels first, so a nearer one's pillow overlaps the one behind it
        order = sorted(range(len(panels)), key=lambda i: -np.linalg.norm(lift(panels[i][0]) - scene.eye))
        out.group(name + ' cushion panels')
        for i in order:
            pillow(out, '%s cushion panel %d' % (name, i + 1), to_screen(panels[i][1]), levels[i])
        out.end()
        out.group(name + ' cushion dimples')
        arm = QUILT['crease'] * cell
        for k, c in enumerate(crossings):
            if math.hypot(*c) < reach * 0.9 and float(np.dot(normal(c), scene.eye - lift(c))) > 0:
                w = lift(c)
                ends = [scene.project(lift(c + arm * v)) for v in (na, -na, nb, -nb)]
                dimple(out, '%s cushion dimple %d' % (name, k + 1), scene.project(w), ends,
                       QUILT['crease px'] * scene.scale(w) / scene.scale(s + np.array([0, SEAT_HEIGHT, 0])),
                       limit=1.2 * arm * scene.scale(w))
        out.end()
        out.shape(name + ' cushion front band', hband(scene, s, cushion_r, SEAT_HEIGHT - 0.006, SEAT_HEIGHT + 0.2 * CUSHION_RISE),
                  SEAT_FRONT_BAND, 'none')
        # one small crisp glint on the brightest panel
        g = lift(panels[near[0]][0])
        gx, gy = scene.project(g)
        gr = 0.012 * CHAIR_SCALE * scene.scale(g)
        out.shape(name + ' cushion glint', [(gx + 1.5 * gr * math.cos(t), gy + 0.6 * gr * math.sin(t))
                                            for t in np.linspace(0, 2 * math.pi, 12, endpoint=False)], SEAT_GLINT, 'none')
        out.shape(name + ' cushion outline', silhouette, 'none', SEAT_OUTLINE)
        out.end()

    # ---- layering, back to front. The rail is split into the half behind the cushion
    # and the half in front of it; the back's frame is one outline with whichever half
    # it stands on, so stile and rail are a single gold piece with no seam.
    # Facing the eye, the back stands on the hidden half, behind the cushion; facing
    # away it stands on the front half. Legs whose feet are further than the seat
    # centre go first; all leg tops tuck under the rail's front half.
    seat_dist = np.linalg.norm(seat_mid - scene.eye)
    out.group(name)
    for dist, label, d, line in legs:
        if dist >= seat_dist:
            draw_leg(label, d, line)
    draw_rail_behind()
    if inner_visible:
        draw_back(True)
    draw_cushion()
    for dist, label, d, line in legs:
        if dist < seat_dist:
            draw_leg(label, d, line)
    if inner_visible:
        draw_rail_front()
    else:
        out.group(name + ' seat rail front group')
        draw_apron()
        out.end()
        draw_back(False)
    out.group(name + ' knee brackets')
    for dist, label, d, line in legs:
        if dist < seat_dist:
            draw_bracket(label, d, line)
    out.end()
    out.end()


def floor_under(scene, screen):
    c = scene.cam.unproject_onto_plane(*screen, np.zeros(3), np.array([0, 1.0, 0]))
    c[1] = 0.0
    return c


def chair_placements(scene):
    """(name, seat floor point, facing (x, z)) in the chair camera's world."""
    c = floor_under(scene, TABLE_SCREEN)
    out = []
    for name, deg, dist, turn in CHAIRS:
        a = math.radians(deg)
        d = np.array([math.cos(a), 0.0, math.sin(a)])
        s = c + d * dist
        t = math.radians(turn)
        fx, fz = -d[0], -d[2]
        out.append((name, s, (fx * math.cos(t) - fz * math.sin(t), fx * math.sin(t) + fz * math.cos(t))))
    return out


def terrace_layout():
    """The set re-expressed on the terrace camera's floor, for shadows: the table's and
    each chair's floor point, each chair's facing, and terrace units per local unit there.
    Feet and seat footprints land under the drawn ones; heights only roughly."""
    terrace = built_terrace().camera
    up = np.array([0, 1.0, 0])

    def convert(scene, p):
        sx, sy = scene.project(p)
        q = terrace.unproject_onto_plane(sx, sy, np.zeros(3), up)
        q[1] = 0.0
        return q, (terrace.focal / q[2]) / (scene.cam.focal / p[2])
    tscene, cscene = Scene(TABLE_CAMERA), Scene(CHAIR_CAMERA)
    table_point, table_k = convert(tscene, floor_under(tscene, TABLE_FLOOR))
    chairs = []
    for name, s, (fx, fz) in chair_placements(cscene):
        q, k = convert(cscene, s)
        ahead, _ = convert(cscene, s + 0.1 * np.array([fx, 0.0, fz]))
        f = (ahead - q) / np.linalg.norm(ahead - q)
        chairs.append((name, q, (f[0], f[2]), k))
    return (table_point, table_k), chairs


def clip_convex(subject, clip):
    """Sutherland-Hodgman: the part of polygon `subject` inside the convex polygon `clip`."""
    clip = np.array(clip, float)
    sign = 1.0 if np.sum(clip[:, 0] * np.roll(clip[:, 1], -1) - np.roll(clip[:, 0], -1) * clip[:, 1]) > 0 else -1.0
    out = [np.array(p, float) for p in subject]
    for a, b in zip(clip, np.roll(clip, -1, axis=0)):
        if not out:
            break
        side = lambda p: sign * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]))
        src, out = out, []
        for p, q in zip(src, src[1:] + src[:1]):
            sp, sq = side(p), side(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                out.append(p + (q - p) * sp / (sp - sq))
    return [tuple(p) for p in out]


def top_shadow_on_cushions(tscene, cscene, out, c, behind):
    """The table top's shadow where the back chairs' cushions pass under its rim. The sun
    (BRIEF "Lighting") throws it down and to the right; shadows.svg sits below this file, so
    it is drawn here, cut to each cushion's outline, as stacked soft layers."""
    rim = np.array(ring(tscene, c, UNDER, TOP_RADIUS, 96))
    out.group('table shadow on cushions')
    for name, s, facing in behind:
        size = CHAIR_TWEAKS.get(name, (1.0,))[0]
        view = ChairView(cscene, s, size)
        cushion = lathe_outline(view, s, cushion_r, SEAT_HEIGHT - 0.006, SEAT_HEIGHT + CUSHION_RISE - 0.008, steps=30)
        for k, (dx, dy) in enumerate(TOP_SHADOW_LAYERS):
            part = clip_convex(cushion, [tuple(p) for p in rim + (dx, dy)])
            if len(part) > 2:
                out.shape('%s shadow from table %d' % (name, k + 1), part, CUSHION_LIGHT['shade'], 'none', 0, TOP_SHADOW_OPACITY)
    out.end()


def draw_set():
    """The whole set, back to front, as an Out."""
    tscene, cscene = Scene(TABLE_CAMERA), Scene(CHAIR_CAMERA)
    c = floor_under(tscene, TABLE_FLOOR)
    out = Out()
    chairs = sorted(chair_placements(cscene), key=lambda x: -np.linalg.norm(x[1] - cscene.eye))
    # the two cameras share no depth, so a chair is behind the table when its seat stands higher on screen
    behind = [ch for ch in chairs if cscene.project(ch[1])[1] < TABLE_SCREEN[1]]
    # the front chairs' cushions hide the back chairs' apron scrolls in the reference
    for name, s, facing in behind:
        draw_chair(cscene, out, name, s, facing, apron_scrolls=False)
    top_shadow_on_cushions(tscene, cscene, out, c, behind)
    draw_table(tscene, out, c)
    behind_names = {ch[0] for ch in behind}
    for name, s, facing in chairs:
        if name not in behind_names:
            draw_chair(cscene, out, name, s, facing)
    return out


# ---------------------------------------------------------------- landmarks (table_set_reference.py)

def drawn_paths(out):
    """{path id: [(x, y), ...]} of every path the set draws."""
    paths = {}
    for line in out.body:
        m = re.search(r'<path id="([^"]+)" d="([^"]+)"', line)
        if m:
            paths[m.group(1)] = [tuple(float(v) for v in xy.split(',')) for xy in re.findall(r'-?[\d.]+,-?[\d.]+', m.group(2))]
    return paths


def bbox(points):
    xs, ys = zip(*points)
    return min(xs), min(ys), max(xs), max(ys)


def span_at(polys, y):
    """Left- and rightmost x where any of the closed polygons crosses height y."""
    xs = []
    for pts in polys:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            if y0 != y1 and (y0 - y) * (y1 - y) <= 0:
                xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    return (min(xs), max(xs)) if xs else (float('nan'), float('nan'))


def _box_error(a, b):
    return max(abs(p - q) for p, q in zip(a, b) if q is not None)


def _diamond_error(points, target):
    x0, y0, x1, y1 = bbox(points)
    (cx, cy), (hw, hh) = T.to_stage(target['centre']), [v * T.SCALE for v in target['half']]
    return max(math.hypot((x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy), abs((x1 - x0) / 2 - hw), abs((y1 - y0) / 2 - hh))


def stage_box(b):
    return T.box_to_stage(b)


def check_table(paths, piece):
    """[(landmark, error in stage px)] of the table against its table_set_reference.py piece."""
    errors = []
    pedestal = [p for k, p in paths.items() if k.startswith(('pedestal upper', 'pedestal lower'))]
    for key, ring in piece['rings'].items():
        cx, cy = T.to_stage((ring['cx'], ring['cy']))
        a, b = ring['a'] * T.SCALE, ring['b'] * T.SCALE
        x0, y0, x1, y1 = bbox(paths['table marble' if key == 'marble' else 'pedestal foot rim'])
        if key == 'marble':
            errors.append((key, max(abs((x0 + x1) / 2 - cx), abs((y0 + y1) / 2 - cy), abs((x1 - x0) / 2 - a),
                                    abs((y1 - y0) / 2 - b))))
        else:
            errors.append((key, max(abs((x0 + x1) / 2 - cx), abs(y1 - (cy + b)), abs((x1 - x0) / 2 - a))))
    for key, p in piece['points'].items():
        x, y = T.to_stage(p)
        if key == 'band front bottom':
            errors.append((key, abs(bbox(paths['table edge'])[3] - y)))
        else:
            left, right = span_at(pedestal, y)
            errors.append((key, abs((left if key.endswith('left') else right) - x)))
    # the collar's top face is hidden behind the upper lattice: its sides and front bottom
    x0, _, x1, y1 = bbox(paths['pedestal collar'])
    tx0, _, tx1, ty1 = stage_box(piece['boxes']['collar'])
    errors.append(('collar', max(abs(x0 - tx0), abs(x1 - tx1), abs(y1 - ty1))))
    for key, d in piece['diamonds'].items():
        gem = 'pedestal %s gem front rim' % {'upper gem': 'upper lattice', 'lower gem': 'lower bell'}[key]
        errors.append((key, _diamond_error(paths[gem], d) if gem in paths else float('inf')))
    return errors


def check_chair(paths, name, piece):
    """[(landmark, error in stage px)] of one chair against its table_set_reference.py piece."""
    errors = []
    for key, p in piece['points'].items():
        x, y = T.to_stage(p)
        if key == 'crest top':
            top = min(paths[name + ' back crest'], key=lambda q: q[1])
            errors.append((key, math.hypot(top[0] - x, top[1] - y)))
        elif key.startswith('back'):
            left, right = span_at([paths[name + ' back frame and rail'], paths[name + ' back frame edge']], y)
            errors.append((key, abs((left if key == 'back left' else right) - x)))
        elif key == 'rail bottom':
            errors.append((key, abs(bbox(paths[name + ' seat frame'])[3] - y)))
    for key, b in piece['boxes'].items():
        path = {'heart': ' back cushion', 'cushion': ' cushion outline'}[key]
        errors.append((key, _box_error(bbox(paths[name + path]), stage_box(b))))
    for key, d in piece.get('diamonds', {}).items():
        errors.append((key, _diamond_error(paths[name + ' back gem rim'], d)))
    feet = [np.mean(v, axis=0) for k, v in paths.items() if re.fullmatch(re.escape(name) + r' foot (front|back) (left|right)', k)]
    for i, f in enumerate(piece['feet']):
        x, y = T.to_stage(f)
        errors.append(('foot %d' % (i + 1), min(math.hypot(q[0] - x, q[1] - y) for q in feet)))
    return errors


def check(out=None):
    """[(piece, landmark, error in stage px)] for every landmark table_set_reference.py measures."""
    paths = drawn_paths(out or draw_set())
    return [(name, key, e) for name, piece in T.PIECES.items()
            for key, e in (check_table(paths, piece) if name == 'table' else check_chair(paths, name, piece))]


def main():
    if sys.argv[1:] == ['check']:
        for piece, key, e in check():
            print('%-18s %-20s %6.1f%s' % (piece, key, e, '' if e <= (6 if piece == 'table' else 9) else '  <--'))
        return
    draw_set().write(cutting.sheet_path('furniture/table_set.svg'))
    print('table set: %d chairs' % len(CHAIRS))


# (part, the table_set.svg groups it holds), back to front
TABLE_PARTS = [('chair back right', ['chair back right']), ('chair back left', ['chair back left']),
               ('table', ['table shadow on cushions', 'table']), ('chair front right', ['chair front right']),
               ('chair front left', ['chair front left'])]


def cut():
    """(images, the nodes drawing them where the scene has them)"""
    root, grads = cutting.load('furniture/table_set.svg')
    subs = {g.get('id'): g for g in cutting.find_group(root, 'Table set')}
    parts, nodes = [], []
    for name, ids in TABLE_PARTS:
        part = cutting.static_part('furniture/parts/table-set/' + cutting.slug(name), [subs[i] for i in ids], grads,
                                   'table set ' + name)
        parts.append(part)
        nodes.append(cutting.image_node(name, part))
    return parts, nodes


def parts():
    return cut()[0]


if __name__ == '__main__':
    main()

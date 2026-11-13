#   Writes SVG, run by `python3 -m scene_export render`: EsmeTerrace/shadows.svg, the floor shadows sheet.
#
#   Soft floor shadows under the props, built in 3D and drawn through the
#   terrace camera.
#
#   Each prop is modelled as a few convex point clouds (a foot ring, a seat
#   disc, a leg strip...). Every point is pushed along the sun direction down
#   onto the floor (Y=0), the hull of the result is clipped to the terrace disc
#   and projected. Positions and sizes are read from the owners' scripts at run
#   time, so re-running this keeps up with them.
#
#   No blur: each shadow is stacked from several flat copies (see LAYERS), each
#   copy in its own low-opacity group (Pixelmator imports group opacity as layer
#   opacity, so overlaps inside a group don't double-darken). Shadows that reach
#   the balustrade's solid faces are drawn on it too.
#
#   python3 -m EsmeTerrace.shadows  ->  shadows.svg

import math
import os

import numpy as np

from furniture import planters
from plants import bushes_reference
from EsmeTerrace import rail
from furniture import table_set
from common.terrace import built_terrace, visible_theta_range
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- light
# Direction the light travels (BRIEF "Lighting"): the sun is high, behind the
# camera and a little to the left, so every shadow falls back and to the right.
SUN = np.array([0.25, -1.0, 0.5])

# ---------------------------------------------------------------- look
SHADOW = '#04607a'
# Soft edges without blur: every shadow is drawn several times, each copy in its
# own low-opacity group. Copy i is the shadow of the object's lower HEIGHT share
# only, widened by a penumbra of BASE + PER_HEIGHT * height, so the copies pile
# up darkest at the contact and thin out towards the far, wider end.
#   (height share, base spread, spread per unit height, group opacity)
def _ramp(n, shares, spreads, base, opacity):
    """n evenly stepped copies between the (first, last) share, spread and base."""
    lerp = lambda ab, t: ab[0] + (ab[1] - ab[0]) * t
    return [(lerp(shares, i / (n - 1)), lerp(base, i / (n - 1)), lerp(spreads, i / (n - 1)), opacity) for i in range(n)]


LAYERS = {
    'cast': _ramp(6, (0.2, 1.0), (0.0, 0.13), (0.0, 0.0), 0.038),
    'contact': _ramp(5, (0.4, 1.0), (0.0, 0.5), (0.004, 0.03), 0.075),
    'pool': _ramp(6, (1.0, 1.0), (0.0, 0.0), (0.0, 0.2), 0.02),
    # chairs: only the legs and the seat cast, softly, so each shadow stays under the chair
    'chair': _ramp(6, (0.12, 0.5), (0.0, 0.06), (0.0, 0.01), 0.035),
}
FORWARD_SPREAD = 0.25                  # penumbra reaching back towards the eye, as a share of the rest
RAIL_BAND = 0.03                       # depth of the occlusion band along the rail foot
POOL = 0.42                            # table-set pool radius, as a fraction of the furthest chair's reach
FOLIAGE = {'crystal': (0.40, 0.30), 'urn': (0.30, 0.25)}   # bush radius, height above the pot rim
BUSH_CROWN = 0.40                      # a bush's crown height as a share of its outline's height (scaled to its width)
BUSH_CONTACT_LIFT = 0.12               # the bush contact is a cast of its lowest leaves this high, so it leans back-right
PENUMBRA_SIDES = 12
TABLE_FOOT_SPOT = 1.07                 # contact ellipse under the table's base disc, in disc radii
CHAIR_FOOT_SPOT = 3.2                  # contact spot under each chair foot, in foot-ball radii

CANVAS = (1536, 1024)


def ring(c, r, h, n=40):
    return [np.array([c[0] + r * math.cos(a), h, c[2] + r * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def to_floor(p):
    return np.array([p[0] - SUN[0] * p[1] / SUN[1], 0.0, p[2] - SUN[2] * p[1] / SUN[1]])


def hull(points):
    """Convex hull of (x, z) points, anticlockwise."""
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in points))
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


def clip(poly, edges):
    """Sutherland-Hodgman clip of a polygon against a convex anticlockwise polygon."""
    out = poly
    for i in range(len(edges)):
        a, b = edges[i], edges[(i + 1) % len(edges)]
        inside = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0
        src, out = out, []
        for j in range(len(src)):
            p, q = src[j], src[(j + 1) % len(src)]
            if inside(q):
                if not inside(p):
                    out.append(meet(p, q, a, b))
                out.append(q)
            elif inside(p):
                out.append(meet(p, q, a, b))
        if not out:
            break
    return out


def meet(p, q, a, b):
    d1 = (q[0] - p[0], q[1] - p[1])
    d2 = (b[0] - a[0], b[1] - a[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    t = ((a[0] - p[0]) * d2[1] - (a[1] - p[1]) * d2[0]) / den
    return (p[0] + t * d1[0], p[1] + t * d1[1])


def spread(p, r):
    """The floor point under p down the sun, with a penumbra ring of radius r round it."""
    f = to_floor(p)
    if r <= 0:
        return [f]
    # light comes from behind the camera, so the soft edge grows away from the eye, hardly towards it
    return [f + r * np.array([math.cos(a), 0.0, math.sin(a) * (FORWARD_SPREAD if math.sin(a) < 0 else 1.0)])
            for a in np.linspace(0, 2 * math.pi, PENUMBRA_SIDES, endpoint=False)]


def lowered(points, share, top):
    """The part of an object below share * top, as points (None if the part starts above it)."""
    cap = share * top
    if min(q[1] for q in points) > cap + 1e-9:
        return None
    return [np.array([q[0], min(q[1], cap), q[2]]) for q in points]


class Shadows:
    def __init__(self):
        self.t = built_terrace()
        self.cam = self.t.camera
        r = self.t.radius
        self.disc = hull([(r * math.sin(a), self.t.centre_z + r * math.cos(a))
                          for a in np.linspace(0, 2 * math.pi, 180, endpoint=False)])
        self.groups = {(kind, i): [] for kind, layers in LAYERS.items() for i in range(len(layers))}
        self.rail_faces = self.rail_bands()

    def floor_from_screen(self, xy):
        p = self.cam.unproject_onto_plane(*xy, np.zeros(3), np.array([0, 1.0, 0]))
        p[1] = 0.0
        return p

    # ------------------------------------------------ the rail as a receiver
    def rail_bands(self):
        """Solid faces of the balustrade in (theta, height): base rail, top rail and the posts.
        The open scrollwork between posts takes no shadow."""
        t = self.t
        lo, hi = visible_theta_range(t, CANVAS[0], margin=80)
        h = rail.RAIL_TOP
        faces = [(lo, hi, 0.0, rail.BASE_RAIL), (lo, hi, h - rail.TOP_RAIL, h)]
        step = rail.BAY / t.radius
        w = rail.POST_HALF / t.radius
        for n in range(int(math.floor(lo / step)), int(math.ceil(hi / step)) + 1):
            faces.append((n * step - w, n * step + w, rail.BASE_RAIL, h - rail.TOP_RAIL))
        return faces

    def on_rail(self, p, r):
        """Where p's sun ray (plus penumbra) meets the rail cylinder, as (theta, height) points."""
        t = self.t
        out = []
        for d in ([np.zeros(3)] if r <= 0 else
                  [r * np.array([math.cos(a), 0.0, math.sin(a)]) for a in np.linspace(0, 2 * math.pi, PENUMBRA_SIDES, endpoint=False)]):
            q = p + d
            x, z = q[0], q[2] - t.centre_z
            dx, dz = SUN[0], SUN[2]
            A, B, C = dx * dx + dz * dz, 2 * (x * dx + z * dz), x * x + z * z - t.radius ** 2
            disc = B * B - 4 * A * C
            if C >= 0 or disc < 0:          # only rays starting on the terrace reach the rail's inner face
                continue
            k = (-B + math.sqrt(disc)) / (2 * A)
            hx, hz = x + k * dx, z + k * dz
            out.append((math.atan2(hx, hz), q[1] + k * SUN[1]))
        return out

    def draw_rail(self, key, name, points, r_of):
        unrolled = [u for q in points for u in self.on_rail(q, r_of(q))]
        if len(unrolled) < 3 or max(v for _, v in unrolled) <= 0:
            return
        shape = hull(unrolled)
        for k, (t0, t1, v0, v1) in enumerate(self.rail_faces):
            poly = clip(shape, [(t0, v0), (t1, v0), (t1, v1), (t0, v1)])
            if len(poly) < 3:
                continue
            dense = []
            for i in range(len(poly)):
                a, b = np.array(poly[i]), np.array(poly[(i + 1) % len(poly)])
                n = max(1, int(abs(b[0] - a[0]) / 0.01))
                dense += [a + (b - a) * j / n for j in range(n)]
            scr = [self.t.on_rail(th, 0.0, v) for th, v in dense]
            self.groups[key].append('<path id="%s on rail %d" d="%s"/>' % (name, k, path_d(scr)))

    # ------------------------------------------------ drawing
    def add(self, kind, name, points3d, top=None, rail=True):
        """Shadow of a convex part, drawn once per layer of its kind; `top` is the height of the
        whole object the part belongs to (its own top by default)."""
        top = top if top is not None else max(q[1] for q in points3d)
        top = max(top, 1e-6)
        for i, (share, base, per_h, _) in enumerate(LAYERS[kind]):
            pts = lowered(points3d, share, top)
            if pts is None:
                continue
            r_of = lambda q: base + per_h * q[1]
            floor = clip(hull([(f[0], f[2]) for q in pts for f in spread(q, r_of(q))]), self.disc)
            if len(floor) >= 3:
                scr = [self.cam.project(x, 0.0, z) for x, z in floor]
                self.groups[(kind, i)].append('<path id="%s %d" d="%s"/>' % (name, i + 1, path_d(scr)))
            if rail:
                self.draw_rail((kind, i), '%s %d' % (name, i + 1), pts, r_of)

    def contact(self, name, c, r, height=0.05):
        """Soft dark ring where a round foot meets the floor."""
        self.add('contact', name + ' contact', ring(c, r, 0.0) + ring(c, r, height), rail=False)

    def turned(self, name, c, profile, top=None, kind='cast'):
        """Cast shadow of a surface of revolution given as [(radius, height)]."""
        pts = []
        for r, h in profile:
            pts += ring(c, r, h)
        self.add(kind, name + ' cast', pts, top)

    def write(self, path):
        body = ['<g id="Shadows">']
        names = {'pool': 'occlusion pool', 'cast': 'cast shadow', 'chair': 'chair shadow', 'contact': 'contact shadow'}
        for kind in ('pool', 'cast', 'chair', 'contact'):
            body.append('<g id="%ss">' % names[kind])
            for i, layer in enumerate(LAYERS[kind]):
                body.append('<g id="%s %d" opacity="%.3f" fill="%s" stroke="none">' % (names[kind], i + 1, layer[3], SHADOW))
                body += ['  ' + q for q in self.groups[(kind, i)]]
                body.append('</g>')
            body.append('</g>')
        body.append('</g>')
        with open(path, 'w') as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n%s\n</svg>\n'
                    % (*CANVAS, *CANVAS, '\n'.join(body)))


def path_d(scr):
    return 'M' + ' L'.join('%.1f,%.1f' % tuple(p) for p in scr) + ' Z'


# ---------------------------------------------------------------- props

def to_terrace(scene, p):
    """A point drawn by one of table_set.py's local cameras, as the terrace floor point under it on screen."""
    sx, sy = scene.project(np.asarray(p, float))
    q = built_terrace().camera.unproject_onto_plane(sx, sy, np.zeros(3), np.array([0, 1.0, 0]))
    q[1] = 0.0
    return q


def table_set_shadow(s):
    """Footprints (pedestal disc, chair feet) are carried over point by point from table_set.py's own
    cameras, so they land exactly under the drawn ones; heights are scaled by terrace_layout's k."""
    (c, k), chairs = table_set.terrace_layout()
    tscene, cscene = table_set.Scene(table_set.TABLE_CAMERA), table_set.Scene(table_set.CHAIR_CAMERA)
    tc = table_set.floor_under(tscene, table_set.TABLE_FLOOR)
    up = np.array([0, 1.0, 0])
    top_h = table_set.TABLE_HEIGHT
    base_ring = [to_terrace(tscene, q) for q in ring(tc, table_set.FOOT_RADIUS, 0.0, 48)]
    s.add('cast', 'table pedestal cast', base_ring + ring(c, k * table_set.LOWER_RADIUS, k * table_set.LOWER_TOP)
          + ring(c, k * table_set.FLARE_RADIUS, k * (top_h - table_set.TOP_THICKNESS)), k * top_h)
    s.add('cast', 'table top cast', ring(c, k * table_set.TOP_RADIUS, k * (top_h - table_set.TOP_THICKNESS), 64)
          + ring(c, k * table_set.TOP_RADIUS, k * top_h, 64), k * top_h)
    grown = [to_terrace(tscene, q) for q in ring(tc, table_set.FOOT_RADIUS * TABLE_FOOT_SPOT, 0.0, 48)]
    s.add('contact', 'table foot contact', grown + [q + up * k * table_set.FOOT_HEIGHT * 1.5 for q in base_ring], rail=False)
    reach = max(np.linalg.norm(seat - c) for _, seat, _, _ in chairs) + k * table_set.SEAT_RADIUS
    s.add('pool', 'table set pool', ring(c, reach * POOL, 0.0, 64) + ring(c, reach * POOL * 0.9, 0.25 * k, 64))
    for (name, seat, _, kc), (_, ls, (fx, fz)) in zip(chairs, table_set.chair_placements(cscene)):
        size, _, _, toe_out = table_set.CHAIR_TWEAKS.get(name, (1.0, 1.0, table_set.BACK_TILT, table_set.TOE_OUT))
        view = table_set.ChairView(cscene, ls, size)
        m = kc * size
        f = np.array([fx, 0.0, fz])
        side = np.array([-f[2], 0.0, f[0]])
        seat_top = m * (table_set.SEAT_HEIGHT + table_set.CUSHION_RISE)
        feet = []
        for a_, b_ in ((1, -1), (1, 1), (-1, -1), (-1, 1)):
            d = a_ * f + b_ * side
            d /= np.linalg.norm(d)
            du, h = table_set.LEG_PROFILE[-1]
            toe = ls + d * (table_set.LEG_SPREAD + du + toe_out * table_set.SEAT_RADIUS * (1 - h / table_set.LEG_PROFILE[0][1]) ** 2)
            feet.append((d, toe))
            spot = [to_terrace(view, q) for q in ring(toe, table_set.FOOT_BALL * CHAIR_FOOT_SPOT, 0.0, 16)]
            s.add('contact', '%s foot contact' % name, spot + [q + up * m * 0.03 for q in spot], rail=False)
        # the seat, legs and feet, from the drawn footprint, as one soft shadow
        under = [to_terrace(view, q) for _, toe in feet for q in ring(toe, table_set.FOOT_BALL, 0.0, 8)]
        s.add('chair', name + ' cast', under + ring(seat, m * table_set.SEAT_RADIUS, m * (table_set.SEAT_HEIGHT - table_set.SEAT_FRAME))
              + ring(seat, m * table_set.CUSHION_RADIUS * 0.9, seat_top), seat_top)
        s.add('contact', name + ' under seat', ring(seat, m * table_set.SEAT_RADIUS * 0.7, 0.0)
              + ring(seat, m * table_set.SEAT_RADIUS * 0.5, m * 0.1), rail=False)


def crystal_points(c, crystal):
    """The hexagonal prism and tip of one of planters.CRYSTALS, as 3D points."""
    name, (dx, dz), h0, radius, length, tip, (lx, lz), rot, shift = crystal[:9]
    shoulders = crystal[9] if len(crystal) > 10 else (1.08,) * 6
    a, e1, e2 = planters.frame(np.array([lx, 1.0, lz]))
    base = c + np.array([dx, h0, dz])
    pts = []
    for k in range(6):
        th = math.radians(rot + 60 * k)
        b = base + radius * (math.cos(th) * e1 + math.sin(th) * e2)
        pts += [b, b + a * length * shoulders[k]]
    pts.append(base + a * (length + tip) + shift * e1)
    return name, pts


def planters_shadow(s):
    sc = planters.Scene() if hasattr(planters, 'Scene') else None
    c = planters.foot_centre(sc, planters.CRYSTAL_PLANTER_SCREEN, planters.PLANTER_BASE[0])
    c[1] = 0.0
    rim_r, rim_h = planters.PLANTER_RIM
    crystals = [crystal_points(c, crystal) for crystal in planters.CRYSTALS]
    top = max(q[1] for _, pts in crystals for q in pts)
    s.turned('crystal planter', c, [(planters.PLANTER_BASE[0], 0.0), (planters.PLANTER_STEP[0], planters.PLANTER_STEP[1]),
                                    (rim_r, rim_h)], top)
    br, bh = FOLIAGE['crystal']
    s.add('cast', 'crystal planter bush cast', ring(c, br, rim_h) + ring(c, br * 0.7, rim_h + bh), top)
    for name, pts in crystals:
        s.add('cast', name + ' cast', pts, top)
    s.contact('crystal planter', c, planters.PLANTER_BASE[0])
    for name, screen in (('left urn', planters.LEFT_URN_SCREEN), ('right urn', planters.RIGHT_URN_SCREEN)):
        foot_r = planters.URN_PROFILE[0][3](0)
        c = planters.foot_centre(sc, screen, foot_r)
        c[1] = 0.0
        rim_h = planters.URN_PROFILE[-1][2]
        prof = [(planters.urn_radius(h), h) for h in np.linspace(0, rim_h, 10)]
        br, bh = FOLIAGE['urn']
        s.turned(name, c, prof, rim_h + bh)
        s.add('cast', name + ' bush cast', ring(c, br, rim_h) + ring(c, br * 0.7, rim_h + bh), rim_h + bh)
        s.contact(name, c, foot_r)


def bush_shadow(s, name, outline):
    """A bush as a round mound: its outline's bottom edge is the mound's front, as wide as the
    outline, and its crown as high as the outline is tall."""
    xs, ys = [max(p[0], 0) for p in outline], [p[1] for p in outline]
    bottom = min(max(ys), CANVAS[1] - 20)
    left, right = s.floor_from_screen((min(xs), bottom)), s.floor_from_screen((max(xs), bottom))
    r = np.linalg.norm(right - left) / 2
    c = (left + right) / 2 + np.array([0.0, 0.0, r])
    top = (max(ys) - min(ys)) / (max(xs) - min(xs)) * 2 * r * BUSH_CROWN
    s.add('cast', name + ' cast', ring(c, r, 0.0) + ring(c, r * 0.6, top), top, rail=False)
    s.add('contact', name + ' contact', ring(c, r * 0.95, 0.0) + ring(c, r * 0.8, BUSH_CONTACT_LIFT), rail=False)


def corner_bush_shadow(s):
    """The corner bush and its planter as one round mound standing on the floor's front edge."""
    bush_shadow(s, 'corner bush', bushes_reference.CORNER_BUSH_OUTLINE)


def rail_shadow(s):
    """The balustrade throws a ladder: the base rail band, the top rail band thrown further towards the
    eye, and a rung under every post."""
    t = s.t
    lo, hi = visible_theta_range(t, CANVAS[0], margin=80)
    thetas = np.linspace(lo, hi, 72)
    outer = [t.floor_point(th) for th in thetas]
    inner = [t.floor_point(th, t.radius - RAIL_BAND) for th in thetas]
    up = lambda p, h: p + np.array([0, h, 0])
    h = rail.RAIL_TOP
    for k in range(len(thetas) - 1):
        s.add('contact', 'rail foot %02d' % k, [outer[k], outer[k + 1], inner[k + 1], inner[k]], rail=False)
        s.add('cast', 'base rail cast %02d' % k, [outer[k], outer[k + 1], up(outer[k], rail.BASE_RAIL), up(outer[k + 1], rail.BASE_RAIL)], rail=False)
        s.add('cast', 'top rail cast %02d' % k, [up(p, hh) for p in (outer[k], outer[k + 1]) for hh in (h - rail.TOP_RAIL, h)], rail=False)
    step = rail.BAY / t.radius
    for n in range(int(math.floor(lo / step)), int(math.ceil(hi / step)) + 1):
        th = n * step
        base, tan = t.floor_point(th), t.tangent(th)
        w = rail.POST_HALF
        s.add('cast', 'rail post %02d' % n, [base + tan * u + np.array([0, v, 0]) for u in (-w, w) for v in (0.0, h)], rail=False)
        w = rail.POST_FOOT['half']
        s.add('contact', 'rail post foot %02d' % n,
              [base + tan * u + np.array([0, v, 0]) for u in (-w, w) for v in (0.0, rail.POST_FOOT['height'] + rail.BASE_RAIL)], rail=False)


def main():
    s = Shadows()
    rail_shadow(s)
    planters_shadow(s)
    corner_bush_shadow(s)
    table_set_shadow(s)
    s.write(cutting.sheet_path('EsmeTerrace/shadows.svg'))
    print('wrote shadows.svg:', {k: len(v) for k, v in s.groups.items()})


# shadows.svg path ids by the object that casts them
SHADOW_OWNERS = [
    ('rail', ('base rail cast', 'rail post', 'rail foot')),
    ('crystal planter', ('crystal planter', 'big crystal', 'left crystal', 'right crystal')),
    ('left urn', ('left urn',)),
    ('right urn', ('right urn',)),
    ('table set', ('table', 'chair')),
    ('corner bush', ('corner bush',)),
]


def shadow_owner(path_id):
    pid = path_id.lower()
    for obj, prefixes in SHADOW_OWNERS:
        if pid.startswith(prefixes):
            return obj
    return None


def cut():
    """{object: its shadow's image}: its shadows.svg paths, and the floor contact its own sheet draws."""
    from scene_export import placed_foliage
    root, grads = cutting.load('EsmeTerrace/shadows.svg')
    top = cutting.find_group(root, 'Shadows')
    out = {}
    for obj, _ in SHADOW_OWNERS:
        el = cutting.filtered(top, lambda pid: shadow_owner(pid) == obj)
        elements, gradients = ([el] if el is not None else []), dict(grads)
        if obj in placed_foliage.OBJECTS:
            sheet, group, _ = placed_foliage.OBJECTS[obj]
            sheet_root, sheet_grads = cutting.load(sheet)
            elements += [sub for sub in cutting.find_group(sheet_root, group) if 'floor contact' in sub.get('id')]
            gradients.update(sheet_grads)
        out[obj] = cutting.static_part('EsmeTerrace/parts/%s/shadow' % cutting.slug(obj), elements, gradients,
                                       obj + ' shadow')
    return out


def parts():
    return list(cut().values())


if __name__ == '__main__':
    main()

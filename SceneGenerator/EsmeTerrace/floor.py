#   Writes SVG, run by `python3 -m scene_export render`: EsmeTerrace/floor_flat.svg (the floor seen
#   from above) and EsmeTerrace/floor.svg (the floor sheet).
#
#   The tiled terrace floor, drawn flat and then laid on the stage floor.
#
#   Step 1 writes floor_flat.svg: the floor seen from straight above, in
#   plan units of 1/100 eye height, centred on the medallion, with +y towards
#   the camera (the bottom of the drawing is the edge nearest the viewer).
#   Edit the numbers below, or edit that SVG by hand and run --project-only.
#
#   Step 2 projects the plan through the stage camera into floor.svg, the sheet
#   scene_export cuts the floor part from.
#
#   The design follows panel-attack-references/EsmeTerrace/source.png, minus its centre
#   motif: a tiled disc, a cream ring set with gold tiles, curved courses of
#   turquoise tiles, an outer cream ring with cream rays on the diagonals,
#   and tiles out to the railing.
#
#   python3 -m EsmeTerrace.floor [--project-only]

import math
import os
import sys

import numpy as np

from common.flat import project
from common.terrace import built_terrace
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))

FLAT = cutting.sheet_path('EsmeTerrace/floor_flat.svg')
OUT = cutting.sheet_path('EsmeTerrace/floor.svg')
CANVAS = (1536, 1024)

# Screen point of the medallion centre; its floor point is found from it.
# x=768 puts it on the stage's centre line (world X=0), so the floor mirrors.
CENTRE_SCREEN = (768.0, 852.0)

# Plan units (1/100 eye height).
DISC_COURSES = (58, 40, 22)      # the plain disc: two courses inwards (12 and 8 tiles), then a round centre stone
CREAM_RING = (58, 72)
INNER_COURSES = (72, 86.5, 101)  # course boundaries between the two cream rings
OUTER_RING = (101, 113)
OUTER_COURSE_DEPTH = 20          # courses beyond the outer ring, out to the rail
TILE_ASPECT = 1.6                # tile length along a course / course depth
COUNT_MULTIPLE = 4               # tiles per course round to this, so each course mirrors left/right and front/back
CREAM_SLABS = (16, 28)           # slabs in the inner and outer cream rings
RAY_WIDTH = (10, 45)             # cream rays on the diagonals: width at the ring, at the rail; laid
                                 # as slabs one outer course deep
# Gold tiles are set in the cream rings on the axes, as deep as the ring and TILE_ASPECT
# times as long, drawn like the turquoise tiles.
OUTER_GOLD_LEFT_OUT = {3}        # the left one: only an edge shows past the lamp bush, a stray shard
# Ray gold tiles lie along each cream ray, the inner end on the ring's outer edge and
# shortened where the canvas edge would cut the outer end; width is a share of the
# ray's width there.
RAY_TILE = dict(long=14, width=0.7)
RAY_TILE_MARGIN = 10             # screen pixels kept between a ray tile's end and the canvas edge
RIM_INSET = -1                   # tuck the tiles this far under the railing's foot
NEAR_Z = 2.0                     # the camera stands on the terrace; drop floor nearer than
                                 # this (eye heights; screen y ~1170, below the canvas)

ARC_STEP = math.radians(2)

TILE_GAP = 0.6                   # tiles are inset this far from their course lines, showing grout
TILE_CORNER = 2.2                # corner rounding of tiles and their sheens
SHEEN_INSET = 3.0                # the lighter facet on each tile: inset from the tile edge,
SHEEN_SHARE = 0.42               # covering this share of the tile's depth on its far (upper) side
LIGHT = (-0.35, -1.0)            # plan direction the sheen faces (far and a little to the left)

STROKE_WIDTH = 3
# Sampled from the reference floor (compare.py, a colour clustering of it, and
# reviews against it). Tiles are shaded in screen pixels, in two steps that
# meet at TINT_STEP_Y: deeper turquoise under the railing, brightening to mint
# by the medallion's far side, then settling to a mid turquoise towards the
# camera. A tile takes the far gradient when its centre is above the step.
FAR_Y = (690, 800)
NEAR_Y = (800, 1024)
TINT_STEP_Y = 800
LIGHT_TILE_EVERY = 7             # every 7th tile is a lighter one
GLINT_FROM_Y = 840               # tiles below this screen y may carry a glint ...
GLINT_EVERY = 3                  # ... every 3rd of them
GLINT = dict(width=3.4, thin=1.3, gap=3.2, inset=3.0)   # two parallel diagonal strips, plan units
GLINT_DIRECTION = (1.0, -0.55)   # plan direction the strips run
COLOURS = {
    'grout': ('groutGrad', None),
    'tile': ('tileGrad', '#14869f'),
    'far tile': ('farTileGrad', '#14869f'),
    'light tile': ('lightTileGrad', '#14869f'),
    'sheen': ('sheenGrad', None),
    'glint': ('glintGrad', None),
    'cream': ('creamGrad', '#c7a75e'),
    'gold tile': ('goldTileGrad', '#c99a2e'),
    'gold sheen': ('goldSheenGrad', None),
    'gold glint': ('goldGlintGrad', None),
}
GRADIENTS = {
    'groutGrad': ('#1494b0', '#1aa0b8', FAR_Y[:1] + NEAR_Y[1:]),
    'farTileGrad': ('#00b9da', '#1fe0d6', FAR_Y),
    'tileGrad': ('#1fe0d6', '#0cc3d3', NEAR_Y),
    'lightTileGrad': ('#5aeedd', '#30d8d8', FAR_Y[:1] + NEAR_Y[1:]),
    'sheenGrad': ('#5ae6e2', '#3cdedb', FAR_Y[:1] + NEAR_Y[1:]),
    'glintGrad': ('#9af7ea', '#86f2e6', NEAR_Y),
    'creamGrad': ('#fff6c8', '#f3df9c', 'shape'),
    'goldTileGrad': ('#ffe680', '#f5cc4c', 'shape'),   # the cream stone's colour, deeper and more vivid
    'goldSheenGrad': ('#fff6c8', '#ffe9a0', 'shape'),
    'goldGlintGrad': ('#fffbe8', '#fff3c4', 'shape'),
}


# ---------------------------------------------------------------- plan geometry (polygons)

def polar(r, a):
    return (r * math.cos(a), r * math.sin(a))


def arc_points(r, a0, a1):
    n = max(2, int(abs(a1 - a0) / ARC_STEP) + 1)
    return [polar(r, a0 + (a1 - a0) * i / (n - 1)) for i in range(n)]


def sector(inner, outer, a0, a1):
    return arc_points(inner, a0, a1) + arc_points(outer, a1, a0)


def ring_of_slabs(inner, outer, count, offset=0.0):
    step = 2 * math.pi / count
    return [sector(inner, outer, offset + i * step, offset + (i + 1) * step) for i in range(count)]


def course_cells(inner, outer, phase):
    """(inner, outer, a0, a1) of each tile in a course. Phase 0 puts a joint on
    the centre line, phase 1 a tile's middle; alternate it for a running bond."""
    mid = (inner + outer) / 2
    raw = 2 * math.pi * mid / (TILE_ASPECT * (outer - inner))
    count = max(COUNT_MULTIPLE, COUNT_MULTIPLE * round(raw / COUNT_MULTIPLE))
    step = 2 * math.pi / count
    off = math.pi / 2 + step / 2 * phase
    return [(inner, outer, off + i * step, off + (i + 1) * step) for i in range(count)]


def tile_outline(inner, outer, a0, a1, gap):
    r0, r1 = inner + gap if inner > 0 else 0, outer - gap
    if a1 - a0 >= 2 * math.pi - 1e-9:
        return arc_points(r1, 0, 2 * math.pi)[:-1]
    if r0 == 0:
        return [(0.0, 0.0)] + arc_points(r1, a0 + gap / r1, a1 - gap / r1)
    return arc_points(r0, a0 + gap / r0, a1 - gap / r0) + arc_points(r1, a1 - gap / r1, a0 + gap / r1)


def rounded(pts, radius, step=0.4):
    """Round the corners of a polygon by about radius, keeping straight and
    arc edges as they are, then drop points the curve doesn't need."""
    p = np.array(pts + pts[:1], float)
    seg = np.hypot(*np.diff(p, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.arange(0, s[-1], step)
    q = np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1)
    w = max(1, int(radius / step))
    k = np.ones(2 * w + 1) / (2 * w + 1)
    for _ in range(2):
        q = np.stack([np.convolve(np.concatenate([q[-w:, i], q[:, i], q[:w, i]]), k, 'valid') for i in (0, 1)], 1)
    return simplify([tuple(v) for v in q], 0.06)


def simplify(pts, tol):
    """Douglas-Peucker on a closed polygon."""
    def dp(a):
        if len(a) < 3:
            return a
        p0, p1 = np.array(a[0]), np.array(a[-1])
        d = p1 - p0
        n = np.hypot(*d) or 1.0
        dist = [abs(d[0] * (q[1] - p0[1]) - d[1] * (q[0] - p0[0])) / n for q in a[1:-1]]
        i = int(np.argmax(dist)) + 1
        if dist[i - 1] <= tol:
            return [a[0], a[-1]]
        return dp(a[:i + 1])[:-1] + dp(a[i:])
    half = len(pts) // 2
    return dp(pts[:half + 1])[:-1] + dp(pts[half:] + pts[:1])[:-1]


def half_plane(poly, normal, level):
    """The part of poly where dot(p, normal) >= level."""
    out = []
    for i, p in enumerate(poly):
        q = poly[i - 1]
        fp, fq = np.dot(p, normal) - level, np.dot(q, normal) - level
        if (fp >= 0) != (fq >= 0):
            t = fq / (fq - fp)
            out.append((q[0] + t * (p[0] - q[0]), q[1] + t * (p[1] - q[1])))
        if fp >= 0:
            out.append(p)
    return out


def tile_shapes(cell, side):
    """The rounded tile, and the lighter facet on its far-left side: one sun
    for the whole floor (BRIEF "Lighting"), so the facet does not mirror."""
    tile = rounded(tile_outline(*cell, TILE_GAP), TILE_CORNER)
    inset = tile_outline(*cell, SHEEN_INSET)
    n = np.array(LIGHT, float)
    n = n / np.hypot(*n)
    d = [np.dot(p, n) for p in inset]
    sheen = half_plane(inset, n, max(d) - SHEEN_SHARE * (max(d) - min(d)))
    return tile, rounded(sheen, TILE_CORNER) if len(sheen) >= 3 else None


def mirror(pts):
    return [(-x, y) for x, y in pts]


def cubic(p0, c1, c2, p3, n=16):
    t = np.linspace(0, 1, n)[:, None]
    p0, c1, c2, p3 = map(np.array, (p0, c1, c2, p3))
    return [tuple(p) for p in (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p3]




# ---------------------------------------------------------------- clipping to the terrace

def clip_region(centre, radius, near_v, sides=180):
    """Convex clip polygon (counter-clockwise in plan coordinates): the
    terrace circle, cut off at plan y = near_v."""
    cx, cy = centre
    pts = [(cx + radius * math.cos(2 * math.pi * k / sides), cy + radius * math.sin(2 * math.pi * k / sides))
           for k in range(sides)]
    return clip_polygon(pts, [(-1e4, near_v), (-1e4, -1e4), (1e4, -1e4), (1e4, near_v)])


def clip_polygon(poly, edges):
    """Sutherland-Hodgman against a convex polygon."""
    out = poly
    for a, b in zip(edges, edges[1:] + edges[:1]):
        if not out:
            break
        inside = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0
        def cross(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            ex, ey = b[0] - a[0], b[1] - a[1]
            t = (ex * (p[1] - a[1]) - ey * (p[0] - a[0])) / (ey * dx - ex * dy)
            return (p[0] + t * dx, p[1] + t * dy)
        src, out = out, []
        for i, p in enumerate(src):
            q = src[i - 1]
            if inside(p):
                if not inside(q):
                    out.append(cross(q, p))
                out.append(p)
            elif inside(q):
                out.append(cross(q, p))
    return out


# ---------------------------------------------------------------- the plan

def medallion_centre():
    cam = built_terrace().camera
    return cam.unproject_onto_plane(*CENTRE_SCREEN, np.zeros(3), np.array([0, 1.0, 0]))


def terrace_in_plan():
    t, c = built_terrace(), medallion_centre()
    return (-c[0] * 100, (c[2] - t.centre_z) * 100), t.radius * 100 - RIM_INSET


def screen_y(p):
    return floor_projection()(p)[1]


def glint(tile_inset, side):
    """Two thin parallel strips running diagonally across the tile's middle,
    the same way on every tile (one light)."""
    c = np.mean(tile_inset, axis=0)
    d = np.array(GLINT_DIRECTION) / np.hypot(*GLINT_DIRECTION)
    n = np.array([-d[1], d[0]])
    g, strips = GLINT, []
    for off, w in ((0.0, g['width']), (g['width'] / 2 + g['gap'] + g['thin'] / 2, g['thin'])):
        lo = np.dot(c, n) + off - w / 2
        band = half_plane(half_plane(tile_inset, n, lo), -n, -(lo + w))
        if len(band) >= 3:
            strips.append(band)
    return strips


def mirror_place(cell):
    """(side, rank) of a tile: side -1 left of the centre line, 1 right, 0 on
    it; rank counts tiles out from the far end of the centre line, so a tile
    and its mirror image share a rank."""
    inner, outer, a0, a1 = cell
    mid = (a0 + a1) / 2
    x = math.cos(mid)
    side = 0 if abs(x) < 1e-9 else (1 if x > 0 else -1)
    from_axis = abs(math.remainder(mid + math.pi / 2, 2 * math.pi))
    return side, int(from_axis / (a1 - a0) + 1e-6), round(inner)


def tile_groups(name, cells, light_every=None):
    tiles, sheens, glints = [], [], []
    for i, cell in enumerate(cells):
        side, rank, course = mirror_place(cell)
        tile, sheen = tile_shapes(cell, side)
        light = light_every and (rank + course) % light_every == 3
        y = screen_y(tuple(np.mean(tile, axis=0)))
        role = 'light tile' if light else ('far tile' if y < TINT_STEP_Y else 'tile')
        tiles.append(('tile %d' % (i + 1), role, tile))
        if sheen and not light:
            sheens.append(('sheen %d' % (i + 1), 'sheen', sheen))
        if y > GLINT_FROM_Y and not light and name != 'disc' and side:
            if (rank + course) % GLINT_EVERY == 1:
                for k, strip in enumerate(glint(tile_outline(*cell, GLINT['inset']), side)):
                    glints.append(('glint %d%s' % (i + 1, 'ab'[k]), 'glint', strip))
    return [(name, tiles), (name + ' sheens', sheens), (name + ' glints', glints)]


def disc_groups():
    cells = []
    for i, (a, b) in enumerate(zip(DISC_COURSES, DISC_COURSES[1:])):
        cells += course_cells(b, a, i % 2)
    cells.append((0, DISC_COURSES[-1], -math.pi / 2, 3 * math.pi / 2))
    return tile_groups('disc', cells)



def gold_groups(name, cells):
    shapes = []
    for i, cell in enumerate(cells):
        tile, sheen = tile_shapes(cell, 0)
        shapes.append(('gold tile %d' % (i + 1), 'gold tile', tile))
        if sheen and len(sheen) >= 3:
            shapes.append(('gold sheen %d' % (i + 1), 'gold sheen', sheen))
        for k, strip in enumerate(glint(tile_outline(*cell, GLINT['inset']), 0)):
            shapes.append(('gold glint %d%s' % (i + 1, 'ab'[k]), 'gold glint', strip))
    return name, shapes


def band_cell(ring, a):
    inner, outer = ring
    half = TILE_ASPECT * (outer - inner) / (inner + outer)
    return (inner, outer, a - half, a + half)


def ray_half_width(r, reach, rim_radius):
    """Half the width of a cream ray at plan radius r."""
    w0, w1 = RAY_WIDTH[0] / 2, RAY_WIDTH[0] / 2 + (RAY_WIDTH[1] - RAY_WIDTH[0]) / 2 * reach / rim_radius
    return w0 + (w1 - w0) * (r - OUTER_RING[1]) / (reach - OUTER_RING[1])


def ray_tile_length(a):
    """RAY_TILE's length, cut back so the outer end stays RAY_TILE_MARGIN inside the canvas."""
    to_screen, long = floor_projection(), RAY_TILE['long']
    inside = lambda r: (RAY_TILE_MARGIN <= to_screen(polar(r, a))[0] <= CANVAS[0] - RAY_TILE_MARGIN
                        and to_screen(polar(r, a))[1] <= CANVAS[1] - RAY_TILE_MARGIN)
    while long > 1 and not inside(OUTER_RING[1] + long):
        long -= 0.5
    return long


def field_cells(reach):
    """(inner, outer, a0, a1) of every tile in the turquoise fields between and beyond the cream rings."""
    inner_cells = []
    for i, (a, b) in enumerate(zip(INNER_COURSES, INNER_COURSES[1:])):
        inner_cells += course_cells(a, b, i % 2)
    outer_cells, r, phase = [], OUTER_RING[1], 0
    while r < reach:
        outer_cells += course_cells(r, r + OUTER_COURSE_DEPTH, phase)
        r, phase = r + OUTER_COURSE_DEPTH, 1 - phase
    return {'inner tiles': inner_cells, 'outer tiles': outer_cells}


def gold_cells(reach, rim_radius):
    """(inner, outer, a0, a1) of the gold tiles in the two cream rings and at the foot of each ray."""
    axes = [k * math.pi / 2 for k in range(4)]
    rays = []
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        inner = OUTER_RING[1]
        outer = inner + ray_tile_length(a)
        mid = (inner + outer) / 2
        half = RAY_TILE['width'] * ray_half_width(mid, reach, rim_radius) / mid
        rays.append((inner, outer, a - half, a + half))
    return {'inner gold tiles': [band_cell(CREAM_RING, a) for a in axes],
            'outer gold tiles': [band_cell(OUTER_RING, a) for k, a in enumerate(axes) if k + 1 not in OUTER_GOLD_LEFT_OUT],
            'ray gold tiles': rays}


def floor_groups():
    rim_centre, rim_radius = terrace_in_plan()
    reach = math.hypot(*rim_centre) + rim_radius
    region = clip_region(rim_centre, rim_radius, (medallion_centre()[2] - NEAR_Z) * 100)
    groups = [('grout', [('grout', 'grout', region)])]

    fields = field_cells(reach)
    groups += tile_groups('outer tiles', fields['outer tiles'], LIGHT_TILE_EVERY)

    rays = []
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        u, v = np.array([math.cos(a), math.sin(a)]), np.array([-math.sin(a), math.cos(a)])
        r0 = OUTER_RING[1]
        while r0 < reach:
            r1 = r0 + OUTER_COURSE_DEPTH
            w0, w1 = ray_half_width(r0, reach, rim_radius), ray_half_width(r1, reach, rim_radius)
            rays.append([tuple(r0 * u + w0 * v), tuple(r1 * u + w1 * v), tuple(r1 * u - w1 * v), tuple(r0 * u - w0 * v)])
            r0 = r1
    groups.append(('rays', [('ray slab %d' % (i + 1), 'cream', p) for i, p in enumerate(rays)]))
    groups.append(('outer ring', [('slab %d' % (i + 1), 'cream', p)
                                  for i, p in enumerate(ring_of_slabs(*OUTER_RING, CREAM_SLABS[1]))]))
    groups += tile_groups('inner tiles', fields['inner tiles'], LIGHT_TILE_EVERY)
    gold = gold_cells(reach, rim_radius)
    groups.append(gold_groups('outer gold tiles', gold['outer gold tiles']))
    groups.append(('cream ring', [('slab %d' % (i + 1), 'cream', p)
                                  for i, p in enumerate(ring_of_slabs(*CREAM_RING, CREAM_SLABS[0]))]))
    groups += disc_groups()
    groups.append(gold_groups('inner gold tiles', gold['inner gold tiles']))
    groups.append(gold_groups('ray gold tiles', gold['ray gold tiles']))

    clipped = []
    for name, items in groups:
        kept = [(n, role, clip_polygon(p, region)) for n, role, p in items]
        clipped.append((name, [(n, role, p) for n, role, p in kept if len(p) >= 3]))
    return clipped


def write_plan(path):
    # 'floor' gradients are in screen pixels (defs pass through the projection
    # untouched); 'shape' gradients run down each shape's own box.
    defs = ''
    for gid, (a, b, span) in GRADIENTS.items():
        box = ('gradientUnits="userSpaceOnUse" x1="0" y1="%d" x2="0" y2="%d"' % span
               if span != 'shape' else 'x1="0" y1="0" x2="0" y2="1"')
        defs += ('<linearGradient id="%s" %s><stop offset="0" stop-color="%s"/>'
                 '<stop offset="1" stop-color="%s"/></linearGradient>' % (gid, box, a, b))
    body = []
    for name, items in floor_groups():
        body.append('<g id="%s">' % name)
        for n, role, pts in items:
            grad, stroke = COLOURS[role]
            line = ('stroke="%s" stroke-width="%s" stroke-linejoin="round"' % (stroke, STROKE_WIDTH)
                    if stroke else 'stroke="none"')
            fill = 'url(#%s)' % grad if grad else 'none'
            body.append('  <path id="%s" d="M%s Z" fill="%s" %s/>'
                        % (n, ' L'.join('%.2f,%.2f' % p for p in pts), fill, line))
        body.append('</g>')
    size = 320
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%d %d %d %d">\n'
                % (2 * size, 2 * size, -size, -size, 2 * size, 2 * size))
        f.write('<defs>%s</defs>\n<g id="Floor tiles">\n%s\n</g>\n</svg>\n' % (defs, '\n'.join(body)))


def floor_projection():
    cam, centre = built_terrace().camera, medallion_centre()

    def to_screen(p):
        return cam.project(centre[0] + p[0] / 100, 0.0, centre[2] - p[1] / 100)
    return to_screen


def main():
    if '--project-only' not in sys.argv:
        write_plan(FLAT)
    project(FLAT, OUT, floor_projection(), *CANVAS)
    print('wrote', OUT)


def parts():
    root, grads = cutting.load('EsmeTerrace/floor.svg')
    return [cutting.static_part('EsmeTerrace/parts/floor/floor', [cutting.find_group(root, 'Floor tiles')], grads,
                                'floor')]


if __name__ == '__main__':
    main()

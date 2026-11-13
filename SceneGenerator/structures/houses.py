#   Writes SVG, run by `python3 -m scene_export render`: structures/houses.svg, the town's houses, each a group.
#
#   python3 -m structures.houses  ->  houses.svg

import math
import os

from common.painting import HAZE, Svg, f, haze, mix, poly
from scenery import town_reference
from structures import houses_reference
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))


# the houses' faces are measured off the Houses reference (see houses_reference.py), a tone it lacks off the
# terrace reference (see town_reference.py)
TOWN_HAZE = 0.06                 # walls and roofs mixed this far toward HAZE


TOWN_LINE_WIDTH = 1.2


TOWN_LINE_DARKEN = 0.38          # outlines are the face's own colour this far toward its dark ink


TOWN_INK = '#2a2f5a'


WINDOW_LINE = '#8a6c58'


SHADOW_INK = '#2a3a6a'           # soft eave and cast shadows: stacked low-opacity layers of this


EAVE_SHADOW = ((3, 0.16), (6, 0.12), (10, 0.08))     # (band height px, opacity) under each wall top


CAST_SHADOW = 0.28               # cast shadow length as a share of building height, falling back-right


CAST_SHADOW_RISE = 0.35          # px up per px right: back-right on the ground


CAST_LAYERS = ((1.0, 0.14), (1.25, 0.1), (1.55, 0.06))   # (growth, opacity) per soft layer


def town_fill(tone, t):
    fill = houses_reference.TONES.get(tone) or town_reference.TONES[tone]
    return haze(fill, t)


def town_line(fill):
    base = fill[1] if isinstance(fill, tuple) else fill
    return mix(base, TOWN_INK, TOWN_LINE_DARKEN)


def ellipse_points(cx, cy, rx, ry, n=16):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


def arched_window(x0, y0, x1, y1):
    r = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    top = [(cx - r * math.cos(math.pi * k / 6), y0 + r - r * math.sin(math.pi * k / 6)) for k in range(7)]
    return [(x0, y1)] + top + [(x1, y1)]


def face_points(face):
    if face[2] == 'ellipse':
        return ellipse_points(*face[3])
    return face[2]


def cast_shadow(svg, b, t):
    """Soft shadow on the ground falling back-right from the building's foot."""
    pts = [p for face in b['faces'] for p in face_points(face)]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    top, foot = min(p[1] for p in pts), max(p[1] for p in pts)
    length = (foot - top) * CAST_SHADOW
    mid = (x0 + x1) / 2
    svg.open('cast shadow')
    for grow, alpha in CAST_LAYERS:
        ln = length * grow
        svg.path(poly([(mid, foot), (x1 + ln * 0.08 * grow, foot), (x1 + ln, foot - ln * CAST_SHADOW_RISE),
                       (mid + ln * 0.8, foot - ln * CAST_SHADOW_RISE)]),
                 mix(SHADOW_INK, HAZE, t), name='shadow layer', extra=' fill-opacity="%s"' % alpha)
    svg.close()


def eave_shadow(svg, points, t):
    """Soft occlusion band under the eave along the top of a rectangular wall."""
    x0, x1 = min(p[0] for p in points), max(p[0] for p in points)
    y0 = min(p[1] for p in points)
    for h, alpha in EAVE_SHADOW:
        svg.path('M%s,%s H%s V%s H%s Z' % (f(x0), f(y0), f(x1), f(y0 + h), f(x0)), mix(SHADOW_INK, HAZE, t),
                 name='eave shadow', extra=' fill-opacity="%s"' % alpha)


def draw_faces(svg, buildings, t, shadows=False):
    for b in buildings:
        svg.open(b['name'])
        if shadows:
            cast_shadow(svg, b, t)
        windows_done = False
        for face in b['faces']:
            name, tone = face[0], face[1]
            fill = town_fill(tone, t)
            svg.path(poly(face_points(face)), fill, town_line(fill), TOWN_LINE_WIDTH, name=name)
            if shadows and name.startswith('wall') and face[2] != 'ellipse' and len(face[2]) == 4:
                eave_shadow(svg, face[2], t)
            # windows sit on the walls, under the roofs drawn after them
            if not windows_done and name.startswith(('roof', 'spire', 'gable')) and b['windows']:
                windows(svg, b['windows'], t, b.get('window tone', 'window'))
                windows_done = True
        if not windows_done and b['windows']:
            windows(svg, b['windows'], t, b.get('window tone', 'window'))
        svg.close()


def windows(svg, boxes, t, tone='window'):
    svg.open('windows')
    fill = town_fill(tone, t)
    for box in boxes:
        svg.path(poly(arched_window(*box)), fill, haze(WINDOW_LINE, t), 1, name='window')
    svg.close()


def main():
    svg = Svg()
    svg.open('buildings')
    draw_faces(svg, houses_reference.BUILDINGS, TOWN_HAZE, shadows=True)
    svg.close()
    svg.write(cutting.sheet_path('structures/houses.svg'))


def template_id(house_id):
    tid = cutting.slug(house_id)
    return tid if tid.startswith('house-') else 'house-' + tid     # never the same as the house's own id


def cut():
    """[(house id, its template id, its image)] back to front."""
    root, grads = cutting.load('structures/houses.svg')
    out = []
    for g in cutting.find_group(root, 'buildings'):
        tid = template_id(g.get('id'))
        out.append((g.get('id'), tid, cutting.static_part('structures/parts/houses/' + tid, [g], grads, tid)))
    return out


def parts():
    return [part for _, _, part in cut()]


if __name__ == '__main__':
    main()

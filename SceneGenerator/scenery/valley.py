#   Writes SVG, run by `python3 -m scene_export render`: scenery/valley.svg, the day valley's land: the rolling hills
#   back to front, teal-blue far off to sunlit yellow-green near, each its own image so trees can stand between them,
#   the knoll the windmill stands on, and the open meadow in front.
#
#   python3 -m scenery.valley  ->  valley.svg

import bisect
import math
import os
import random

from common.painting import SEED, WIDTH, Svg, curve_y, mix, poly
from scene_export import cutting
from scenery import valley_reference as ref
from scenery.landscape import blades, plane, polyline

HERE = os.path.dirname(os.path.abspath(__file__))


LEFT, RIGHT, BOTTOM = -40, 1576, 1040   # the land reaches this far past the sheet's sides and bottom


STEP = 4                         # px between the points a smooth line is drawn through


HILL_OVERLAP = 40                # px a hill reaches below the lowest top of the hill in front, hidden under it


PLANE_POINTS = 12                # points along a plane's top and bottom lines
PLANE_FULLNESS = 0.6             # below 1 keeps a plane near its full depth along its run, tapering only at its ends
PLANE_LEAN = 0.35                # how far a plane's deepest point sits toward its downhill end, as a share of its run


BODY_SHADING = 90                # px below a hill's highest point its body takes to shade from mid tone to shade
CREST_FADE = 0.5                 # how far a sunlit cap fades toward the mid tone at its lowest
FRINGE_HEIGHT = 0.75             # the meadow's grass blades, as a share of the terrace grass's height


def lerp(a, b, t):
    return a + (b - a) * t


def spline(points, step=STEP):
    """A smooth line through the points (Catmull-Rom), sampled about every step px."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        n = max(1, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                                    + (3 * b - a - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(tuple(points[-1]))
    return out


class Line:
    """y along a line running left to right."""
    def __init__(self, points):
        self.points = spline(points)
        self.xs = [p[0] for p in self.points]

    def __call__(self, x):
        i = bisect.bisect_left(self.xs, x)
        if i <= 0:
            return self.points[0][1]
        if i >= len(self.xs):
            return self.points[-1][1]
        (x0, y0), (x1, y1) = self.points[i - 1], self.points[i]
        return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)


# ================================================================ hills
class Hill:
    def __init__(self, name, depth, edge):
        self.name, self.depth = name, depth
        self.edge = spline(edge)
        self.partial = edge[0][0] > LEFT or edge[-1][0] < RIGHT
        self.top = Line(edge)
        self.colours = ref.HILL_COLOURS[name]

    def outline(self, bottom):
        """The hill's shape: its edge, closed straight down from each end that stops inside the land."""
        (x0, _), (x1, _) = self.edge[0], self.edge[-1]
        return self.edge + [(min(x1, RIGHT), bottom), (max(x0, LEFT), bottom)]


def hills():
    return [Hill(*h) for h in ref.HILLS]


def front_of(all_hills, i):
    """The first hill in front of hill i that spans the whole land, or None for the nearest."""
    return next((o for o in all_hills[i + 1:] if not o.partial), None)


def bottom_of(all_hills, i):
    """Where hill i's image ends: far enough below the hill in front's lowest top to stay hidden under it, or past
    the meadow's top for the nearest."""
    front = front_of(all_hills, i)
    lowest = max(y for _, y in front.edge) if front else max(y for _, y in ref.MEADOW[0][0])
    return min(BOTTOM, lowest + HILL_OVERLAP)


def light_plane(hill, x0, x1, drop0, drop1, depth):
    """A flat plane hanging under the hill's top edge from x0 to x1, deepest toward its downhill end."""
    downhill = 1 if hill.top(x1) > hill.top(x0) else -1
    peak = 0.5 + downhill * PLANE_LEAN / 2
    top = []
    for k in range(PLANE_POINTS + 1):
        t = k / PLANE_POINTS
        x = lerp(x0, x1, t)
        top.append((x, hill.top(x) + lerp(drop0, drop1, t)))

    def below(t):
        u = t / (2 * peak) if t <= peak else 0.5 + (t - peak) / (2 * (1 - peak))
        if (x0 <= 0 and t <= peak) or (x1 >= WIDTH and t >= peak):
            u = 0.5
        x = lerp(x0, x1, t)
        return x, hill.top(x) + lerp(drop0, drop1, t) + depth * math.sin(math.pi * u) ** PLANE_FULLNESS
    bottom = [below(k / PLANE_POINTS) for k in range(1, PLANE_POINTS)]
    if x0 <= 0:
        bottom.insert(0, (x0, hill.top(x0) + drop0 + depth))
    if x1 >= WIDTH:
        bottom.append((x1, hill.top(x1) + drop1 + depth))
    return plane(top, bottom)


def draw_hill(svg, all_hills, i):
    hill = all_hills[i]
    crest, mid, shade, line = hill.colours
    bottom = bottom_of(all_hills, i)
    svg.open(hill.name)
    y_top = min(y for _, y in hill.edge)
    svg.path(poly(hill.outline(bottom)), (mid, shade, y_top, y_top + BODY_SHADING), name='grass')
    for x0, x1, drop0, drop1, depth, tone in ref.PLANES.get(hill.name, []):
        if tone == 'crest':
            ys = (hill.top(x0) + drop0, hill.top(x1) + drop1)
            fill = (crest, mix(crest, mid, CREST_FADE), min(ys), max(ys) + depth)
        else:
            fill = mid
        svg.path(light_plane(hill, x0, x1, drop0, drop1, depth), fill, name='lit plane')
    svg.stroke(poly(hill.edge, close=False), line, lerp(*ref.HILL_LINE_WIDTH, hill.depth ** ref.HILL_LINE_GROWTH), name='top edge')
    svg.close()


# ================================================================ meadow
def fine_blades(edge, rng):
    """The terrace grass's blade line along the edge, its blades cut down to the meadow's finer grass."""
    return [(x, curve_y(edge, x) + (y - curve_y(edge, x)) * FRINGE_HEIGHT) for x, y in blades(edge, rng)]


def meadow(svg, rng):
    """The open meadow in front, band behind band, each band's top a fringe of fine grass over the one behind."""
    svg.open('meadow')
    bands = ref.MEADOW
    for k, (edge, top_colour, foot_colour) in enumerate(bands):
        y_top = min(y for _, y in edge)
        y_foot = max(y for _, y in bands[k + 1][0]) if k + 1 < len(bands) else BOTTOM
        svg.path(polyline(fine_blades(edge, rng)) + ' L%d,%d L%d,%d Z' % (RIGHT, BOTTOM, LEFT, BOTTOM),
                 (top_colour, foot_colour, y_top, y_foot), name='band')
    svg.close()


def valley(svg):
    svg.open('Valley')
    all_hills = hills()
    for i in range(len(all_hills)):
        draw_hill(svg, all_hills, i)
    meadow(svg, random.Random('%s meadow' % SEED))
    svg.close()


def main():
    svg = Svg()
    valley(svg)
    svg.write(cutting.sheet_path('scenery/valley.svg'))


def cut():
    """{name: its image}: each hill and the meadow, each where it sits and uncropped past the sheet's edges."""
    root, grads = cutting.load('scenery/valley.svg')
    out = {}
    for g in cutting.find_group(root, 'Valley'):
        name = g.get('id')
        out[name] = cutting.static_part('scenery/parts/valley/' + cutting.slug(name), [g], grads, name, None)
    return out


def parts():
    return list(cut().values())


if __name__ == '__main__':
    main()

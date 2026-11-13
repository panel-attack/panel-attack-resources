#   Writes SVG, run by `python3 -m scene_export render`: plants/broadleaf.svg, the day valley's round broadleaf trees
#   and bushes, each a template standing on its foot: three crowns (round, wide, tall) at two distances (near, mid),
#   two trunkless bushes (round, wide), and the meadow's oaks: round-crowned trees whose trunk splays into roots at
#   its foot and forks into branches reaching up into a cluster of lobes, in three shapes (broad, round, tall) at three
#   distances (near, mid, far).
#
#   python3 -m plants.broadleaf  ->  broadleaf.svg
#
#   Below the templates the sheet stands one copy of each on the canvas, for comparing with the reference; those
#   placements are not parts.

import math
import os
import random

from common.painting import Svg, f, mix, poly
from scene_export import cutting
from plants import pines

HERE = os.path.dirname(os.path.abspath(__file__))


# A crown is one or more domes, back to front, each a cluster of overlapping round lobes with one thick dark outline
# around the lot, so where a dome stands in front of another its outline crosses the one behind. Inside the outline
# each lobe has a darker rim on its right and underside, away from the light coming from the upper left as on the firs,
# and a soft pale disc near its middle (colours sampled off the lollipop trees and bushes in stage.png, lighter and
# yellower than the firs beside them).
CROWN = {'tree': ('#52ab4a', '#409440', '#6cc152')}           # body, rim, pale disc


CROWN_LINE = '#184232'            # the pines' dark outline, leaning green as the reference's round trees do


TRUNK = ('#b5741c', '#7b4228')    # its lit left, its shaded right


TRUNK_LINE = pines.TRUNK_LINE


# trees at the near size, standing on (0, 0): the domes [[(x, y, radius, kind)]] back to front, and the trunk's (x,
# half width at its foot). A lobe's radius is (rx, ry) when it is an ellipse; its kind is 'disc' for a lobe with a
# pale disc, 'fill' for one only filling the gap between the others, and 'shade' for the shaded base along a dome's
# underside, two of them meeting in a notch over the trunk.
SHAPES = {
    'round': ([[(0, -26, 12, 'fill'), (-8, -17, (11, 6), 'shade'), (8, -17, (11, 6), 'shade'),
                (-12, -23, 11.6, 'disc'), (12.5, -25.5, 11.6, 'disc'), (-0.5, -38.5, 14.5, 'disc')]], (0, 5.0)),
    'wide': ([[(-5, -24, 11, 'fill'), (-6, -16, (14, 7), 'shade'), (-15, -20, 10, 'disc'), (-2, -35, 12, 'disc')],
              [(12, -18, 8, 'fill'), (12, -14, (11, 5.5), 'shade'), (6, -17, 8, 'disc'), (19, -17, 8, 'disc'),
               (12, -26, 8.5, 'disc')]], (3, 4.6)),
    'tall': ([[(0, -30, 11, 'fill'), (0, -38, 10, 'fill'), (-7, -17, (10, 6), 'shade'), (7, -17, (10, 6), 'shade'),
               (-9, -25, 9.5, 'disc'), (9, -25, 9.5, 'disc'), (-8, -36, 10, 'disc'), (8, -36, 10, 'disc'),
               (0, -47, 11, 'disc')]], (0, 4.6)),
}


TRUNK_TOP = 15                   # the top of the trunk's rounded cap above its foot at the near size


TRUNK_TAPER = 0.78               # its half width under the cap, as a share of its foot's


# bushes, trunkless, standing on (0, 0), drawn as the oaks' crowns are, after the meadow reference's low dark shrubs:
# clusters back to front, each (x, y, radius), the lowest reaching the foot
BUSHES = {
    'round': [(-38, -14, 14), (-18, -24, 20), (38, -22, 18), (2, -40, 28)],
    'wide': [(-44, -7, 8), (-26, -11, 12), (48, -9, 10), (30, -15, 15), (10, -22, 22)],
}


BUSH_BASE = {'round': (-48, 52, 20), 'wide': (-50, 56, 12)}   # the flat shade along a bush's foot: left, right, height


BUSH_CLOUD = {'line': '#0b4a44', 'under': '#116c66', 'body': '#3d9468', 'cap': '#549f4c'}


BUSH_LOBES = (0.6, 0.8)          # a bush cluster's edge lobes' share of its radius, and its body's size


BUSH_CAP = (0.85, 0.08)          # its light cap's size and shift right, toward the light at the upper right


BUSH_CAPPED = -15                # clusters whose centre is right of this carry a cap, lighting the higher right


RIM = 0.24                       # a lobe's body is this share of its radius smaller than the lobe, nudged up and left


LIT = (0.56, -0.12, -0.12)       # the pale disc's radius and its centre's offset in x and y, as shares of the lobe's


# distances: (scale from the near size, (colour, share) mixed toward, line width); mid trees haze toward the pines'
# mid blue
DISTANCES = {'near': (1.0, ('#2a6e8a', 0.0), 2.8),
             'mid': (0.69, ('#2a6e8a', 0.12), 2.0)}


BUSH_LINE = 2.8


# The oaks, after the meadow reference's trees: a crown drawn as one cloud of round clusters, each a ring of lobes,
# inside one dark outline, its whole silhouette filled with the deep teal of its shade. The clusters' mid green bodies
# sit a little above their own outlines as one mass, so a scalloped teal shadow shows along the underside and in the
# pocket over the trunk; the clusters of the crown's top and right carry lime caps joined into one lit mass. Under
# the crown the trunk shows against the teal, splayed a little at its foot and forking into limbs that reach up into the
# lobes (colours sampled off meadow-stage.png).
OAK_CLOUD = {'line': '#0f5a50', 'under': '#1e716a', 'body': '#409662', 'cap': '#a5d142'}


OAK_TRUNK = ('#7a565a', '#e48c54', '#3e2c34')   # bark, the warm light down its right, its outline


OAK_TRUNK_HAZE = '#a0a8a4'       # a far trunk hazes toward this warm grey rather than the hills' teal


# oak shapes at the near size, standing on (0, 0): the crown's ellipse (centre y, half width, half height), its lobes'
# how far down the lime caps reach (a share of the half height below the centre, at the crown's left and right
# edges), the fork's height as a share of the crown's half height below its centre, the trunk's half widths (at the
# fork, above the roots, across the roots), and the limbs from the fork, each (tip x, tip y) as shares of the crown's
# half width and half height off its centre, its half width at the fork as a share of the trunk's, and a twig (how far
# along the limb, tip x, tip y as the limb's) or None
OAKS = {
    'broad': dict(crown=(-84, 84, 52), caps=(-0.2, 0.3), fork=0.95,
                  trunk=(9, 12, 20),
                  limbs=[(-0.6, 0.25, 0.55, (0.55, -0.4, 0.1)), (-0.2, -0.05, 0.45, None),
                         (0.2, -0.1, 0.45, None), (0.6, 0.2, 0.55, (0.5, 0.45, 0.05))]),
    'round': dict(crown=(-90, 66, 56), caps=(-0.15, 0.3), fork=0.95,
                  trunk=(8.5, 11, 19),
                  limbs=[(-0.55, 0.25, 0.55, (0.6, -0.4, 0.1)), (-0.05, -0.1, 0.45, None),
                         (0.55, 0.2, 0.55, (0.55, 0.42, 0.05))]),
    'tall': dict(crown=(-92, 54, 58), caps=(-0.15, 0.3), fork=0.95,
                 trunk=(8, 10.5, 17),
                 limbs=[(-0.5, 0.25, 0.6, (0.6, -0.42, 0.1)), (0.05, -0.1, 0.45, None),
                        (0.5, 0.2, 0.6, None)]),
}


OAK_TRUNK_SLIM = {'near': 1.0, 'mid': 0.9, 'far': 0.9}   # trunks thin more than the crowns shrink with distance


# a crown's clusters, back to front, each (x, y) off the crown's centre as shares of its half width and half height
# and its radius as a share of the smaller of the two: a lower row whose two middle clusters leave a pocket over the
# trunk, a middle row, and two on top
OAK_CLUSTERS = [(-0.62, 0.42, 0.5), (0.64, 0.4, 0.5), (-0.32, 0.25, 0.38), (0.32, 0.22, 0.38),
                (-0.62, -0.05, 0.62), (0.6, -0.1, 0.66), (0.0, -0.05, 0.55),
                (-0.3, -0.45, 0.5), (0.2, -0.55, 0.6)]


OAK_POCKET = (0.55, 0.45, 0.3)   # the teal shade over the trunk: centre below the crown's, half width, half height


# by distance: a cluster's edge lobes' radius as a share of the cluster's, and its body's size as a share of the
# cluster's, so far crowns keep fewer, larger lobes and a wider shadow side
OAK_LOBES = {'near': (0.4, 0.8), 'mid': (0.45, 0.8), 'far': (0.55, 0.78)}


OAK_CAP_SIZE = (0.85, 0.1)      # a lime cap's size as a share of its cluster's, and its shift right toward the light


OAK_JITTER = 0.15                # an edge lobe's radius and place wander this share of its radius


# oak distances: (scale from the near size, (colour, share) mixed toward, line width); mid oaks haze a little, far ones
# toward the teal of the far hills
OAK_DISTANCES = {'near': (1.0, ('#2a7d8a', 0.0), 2.4),
                 'mid': (0.45, ('#2a7d8a', 0.1), 1.3),
                 'far': (0.25, ('#3fa6b4', 0.22), 0.9)}


OAK_WIDEN = {'near': 1.0, 'mid': 1.1, 'far': 1.3}   # farther crowns spread wider for their height, as the reference's


TEMPLATES = (['broadleaf-%s-%s' % (shape, distance) for distance in DISTANCES for shape in SHAPES]
             + ['bush-%s' % shape for shape in BUSHES]
             + ['oak-%s-%s' % (shape, distance) for distance in OAK_DISTANCES for shape in OAKS])


PREVIEW_Y = 300                  # the preview copies stand on this line of the sheet


PREVIEW_GAP = 100


OAK_PREVIEW = (600, 140, {'near': 240, 'mid': 120, 'far': 70})   # the oak copies' line, first foot x, gap by distance


def circle(x, y, r):
    """A circle of radius r, or an ellipse when r is (rx, ry)."""
    rx, ry = r if isinstance(r, tuple) else (r, r)
    return ('M%s,%s A%s,%s 0 1,0 %s,%s A%s,%s 0 1,0 %s,%s Z'
            % (f(x - rx), f(y), f(rx), f(ry), f(x + rx), f(y), f(rx), f(ry), f(x - rx), f(y)))


def scaled(r, k):
    return tuple(v * k for v in r) if isinstance(r, tuple) else r * k


def lobes_path(lobes, grow=0.0, dx=0.0, dy=0.0):
    """The lobes, each grown by grow and moved by (dx, dy), as shares of its radius."""
    out = []
    for x, y, r, _ in lobes:
        rx, ry = r if isinstance(r, tuple) else (r, r)
        out.append(circle(x + dx * min(rx, ry), y + dy * min(rx, ry), scaled(r, 1 + grow)))
    return ' '.join(out)


def dome(svg, lobes, colours, toward, t, line):
    """The lobes as one dome: outlined all round, a darker rim to each lobe's right and underside, its shaded base
    left in the rim's colour, and a pale disc on each disc lobe."""
    body, rim, lit = (mix(c, toward, t) for c in colours)
    outline = lobes_path(lobes)
    svg.path(outline, mix(CROWN_LINE, toward, t), mix(CROWN_LINE, toward, t), line * 2, name='dome outline')
    svg.path(outline, rim, name='dome rim')
    lit_base = [circle(x - r[0] * 0.25, y - r[1] * 0.3, (r[0] * 0.8, r[1] * 0.75)) for x, y, r, kind in lobes
                if kind == 'shade']
    svg.path(' '.join([lobes_path([l for l in lobes if l[3] != 'shade'], -RIM, -RIM * 1.0, -RIM * 0.5)] + lit_base),
             body, name='dome')
    discs = [circle(x + r * LIT[1], y + r * LIT[2], scaled(r, LIT[0])) for x, y, r, kind in lobes if kind == 'disc']
    svg.path(' '.join(discs), lit, name='dome lit')


def trunk(svg, x, foot_hw, scale, toward, t, line):
    """The short stub of a trunk standing on (x, 0), nearly straight sided, its rounded cap hidden behind the
    crown, lit on its left."""
    top, hw = TRUNK_TOP * scale, foot_hw * TRUNK_TAPER
    shoulder = top - hw
    svg.path('M%s,0 L%s,%s Q%s,%s %s,%s Q%s,%s %s,%s L%s,0 Z'
             % (f(x - foot_hw), f(x - hw), f(-shoulder), f(x - hw), f(-top), f(x), f(-top), f(x + hw), f(-top),
                f(x + hw), f(-shoulder), f(x + foot_hw)), mix(TRUNK[1], toward, t), mix(TRUNK_LINE, toward, t),
             line * 0.8, name='trunk')
    inset = line * 0.4
    svg.path(poly([(x - foot_hw + inset, -inset), (x - hw + inset, -shoulder), (x - hw * 0.3, -top + inset),
                   (x + hw * 0.2, -shoulder), (x + foot_hw * 0.2, -inset)]), mix(TRUNK[0], toward, t), name='trunk lit')


def tree(svg, shape, distance):
    """The broadleaf tree of that crown at that distance, standing on (0, 0)."""
    scale, (toward, t), line = DISTANCES[distance]
    domes, (tx, foot_hw) = SHAPES[shape]
    svg.open('tree')
    trunk(svg, tx * scale, foot_hw * scale, scale, toward, t * pines.TRUNK_HAZE, line)
    for lobes in domes:
        dome(svg, [(x * scale, y * scale, scaled(r, scale), kind) for x, y, r, kind in lobes], CROWN['tree'], toward, t,
             line)
    svg.close()


def bush(svg, shape):
    """The trunkless bush of that shape, its lowest clusters standing on (0, 0)."""
    rng = random.Random('bush-' + shape)
    clusters = [(x, y, r, cluster(x, y, r, BUSH_LOBES[0], rng)) for x, y, r in BUSHES[shape]]
    svg.open('bush')
    left, right, height = BUSH_BASE[shape]
    cloud(svg, clusters, BUSH_CLOUD, BUSH_LINE, BUSH_LOBES[1], lambda x, y: x > BUSH_CAPPED, BUSH_CAP,
          base=poly([(left, 0), (right, 0), (right, -height), (left, -height)]))
    svg.close()


def limb(points, widths):
    """The outline of a limb along points, its half width at each point given by widths, rounded off at its tip."""
    left, right = [], []
    for i, ((x, y), w) in enumerate(zip(points, widths)):
        (ax, ay), (bx, by) = points[max(0, i - 1)], points[min(len(points) - 1, i + 1)]
        d = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / d, (bx - ax) / d
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return poly(left + [points[-1]] + right[::-1])


def bend(a, c, b, n=6):
    """n + 1 points along the quadratic curve from a over c to b."""
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0],
             (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]) for t in (i / n for i in range(n + 1))]


def oak_limbs(o, k, slim):
    """The trunk and its limbs and twigs at scale k, their widths slimmed by slim, each (points, half widths), and the
    trunk's lit side."""
    cy, ax, ay = (v * k for v in o['crown'])
    fork = cy + ay * o['fork']
    top, mid, root = (v * k * slim for v in o['trunk'])
    limbs = [([(0, 0), (0, 0.12 * fork), (0, 0.4 * fork), (0, fork)], [root, mid * 1.05, mid, top])]
    for tx, ty, share, twig in o['limbs']:
        tip = (tx * ax, cy + ty * ay)
        base = (tip[0] * 0.1, fork + 2 * k)
        elbow = (tip[0] * 0.8, fork + (tip[1] - fork) * 0.2)
        pts = bend(base, elbow, tip)
        w0 = top * share
        limbs.append((pts, [w0 * (1 - 0.6 * i / 6) for i in range(7)]))
        if twig:
            at, dx, dy = twig
            start = pts[round(at * 6)]
            end = (start[0] + dx * (tip[0] - base[0]), start[1] + dy * (tip[1] - base[1]) - 6 * k)
            limbs.append((bend(start, ((start[0] + end[0]) / 2, start[1] + (end[1] - start[1]) * 0.7), end, 3),
                          [w0 * 0.45, w0 * 0.38, w0 * 0.3, w0 * 0.22]))
    lit = poly([(root * 0.05, -0.6 * k), (root * 1.0, -0.6 * k), (mid * 1.02, 0.15 * fork), (mid * 1.0, 0.45 * fork),
                (top * 1.0, 0.85 * fork), (top * 0.1, 0.65 * fork), (mid * 0.05, 0.3 * fork)])
    return limbs, lit


def cluster(x, y, big, share, rng):
    """A cluster of radius big at (x, y): a ring of small lobes round its edge over a core filling its middle, each
    (x, y, r)."""
    r = big * share
    n = max(5, round(2 * math.pi * (big - r) / (r * 1.5)))
    turn = rng.uniform(0, 2 * math.pi)
    ring = []
    for i in range(n):
        a = turn + 2 * math.pi * i / n
        q = r * (1 + rng.uniform(-OAK_JITTER, OAK_JITTER))
        ring.append((x + (big - q) * math.cos(a), y + (big - q) * math.sin(a), q))
    return ring + [(x, y, big - r * 0.9)]


def oak_clusters(o, k, distance, shape):
    """The crown's clusters at scale k, back to front, each (x, y, radius, lobes)."""
    rng = random.Random(shape + distance)
    cy, ax, ay = (v * k for v in o['crown'])
    m = min(ax, ay)
    share = OAK_LOBES[distance][0]
    ax *= OAK_WIDEN[distance]
    return [(x * ax, cy + y * ay, big * m, cluster(x * ax, cy + y * ay, big * m, share, rng))
            for x, y, big in OAK_CLUSTERS]


def shrunk(lobes, x, y, big, size, shift):
    """The lobes of the cluster of radius big at (x, y) sized by size about its top, and moved right by shift of its
    radius, so their top stays where the cluster's is."""
    return ' '.join(circle(x + (lx - x) * size + shift * big, y + (ly - y) * size - (1 - size) * big, r * size)
                    for lx, ly, r in lobes)


def cloud(svg, clusters, colours, line, size, capped, cap, pocket=None, behind=None, base=None):
    """The clusters as one cloud outlined round its edge and filled with its shade, the clusters' bodies shrunk up off
    them as one mass so the shade shows along the cloud's underside, and one lime mass of caps (size, shift right) on
    the clusters capped(x, y) picks. pocket, an ellipse (x, y, rx, ry), is shade behind the clusters with behind(svg)
    drawn over it; base, a path, is shade joined to the clusters, flattening their foot. Capped clusters that
    overlap are bridged so their caps join into one lit mass."""
    shapes = ' '.join(lobes_path([(x, y, r, '') for x, y, r in lobes]) for _, _, _, lobes in clusters)
    extra = [circle(pocket[0], pocket[1], (pocket[2], pocket[3]))] if pocket else []
    extra += [base] if base else []
    svg.path(' '.join([shapes] + extra), colours['line'], colours['line'], line * 2, name='cloud outline')
    if pocket:
        svg.path(extra[0], colours['under'], name='cloud shade')
    if behind:
        behind(svg)
    svg.path(' '.join([shapes] + ([base] if base else [])), colours['under'], name='cloud shade')
    lit = [c for c in clusters if capped(c[0], c[1])]
    caps = [shrunk(lobes, x, y, big, cap[0] * size, cap[1]) for x, y, big, lobes in lit]
    for i, (x, y, big, _) in enumerate(lit):
        for x2, y2, big2, _ in lit[i + 1:]:
            if math.hypot(x2 - x, y2 - y) < big + big2:
                caps.append(circle((x + x2) / 2 + cap[1] * big, (y + y2) / 2 - (1 - size) * big,
                                   min(big, big2) * cap[0] * size * 0.75))
    svg.path(' '.join(shrunk(lobes, x, y, big, size, 0) for x, y, big, lobes in clusters), colours['body'],
             name='cloud body')
    if caps:
        svg.path(' '.join(caps), colours['cap'], name='cloud cap')


def trunk_limbs(svg, limbs, trunk_lit, colours, line):
    """The trunk and its limbs, outlined as one, and the light down the trunk's right."""
    bark, warm, bark_line = colours
    for points, widths in limbs:
        svg.path(limb(points, widths), bark_line, bark_line, line * 1.4, name='limb outline')
    for points, widths in limbs:
        svg.path(limb(points, widths), bark, name='limb')
    svg.path(trunk_lit, warm, name='bark lit')


def oak(svg, shape, distance):
    """The oak of that shape at that distance, standing on (0, 0)."""
    k, (toward, t), line = OAK_DISTANCES[distance]
    o = OAKS[shape]
    c = {name: mix(colour, toward, t) for name, colour in OAK_CLOUD.items()}
    c['line'] = mix(OAK_CLOUD['line'], toward, min(1.0, t * 1.6))
    clusters = oak_clusters(o, k, distance, shape)
    limbs, trunk_lit = oak_limbs(o, k, OAK_TRUNK_SLIM[distance])
    cy, ax, ay = (v * k for v in o['crown'])
    left, right = o['caps']
    bark, warm, bark_line = (mix(v, OAK_TRUNK_HAZE, t) for v in OAK_TRUNK)
    bark_colours = (bark, mix(warm, bark, min(1.0, t * 3)), bark_line)
    svg.open('oak')
    px, py, ph = OAK_POCKET
    cloud(svg, clusters, c, line, OAK_LOBES[distance][1],
          lambda x, y: y < cy + ay * (left + (right - left) * (x / ax + 1) / 2), OAK_CAP_SIZE,
          (0, cy + px * ay, py * ax, ph * ay), lambda s: trunk_limbs(s, limbs, trunk_lit, bark_colours, line))
    svg.close()


def draw(svg, tid):
    """The template tid standing on (0, 0)."""
    kind, shape = tid.split('-')[:2]
    if kind == 'oak':
        oak(svg, shape, tid.split('-')[2])
    elif kind == 'bush':
        bush(svg, shape)
    else:
        tree(svg, shape, tid.split('-')[2])


def main():
    svg = Svg()
    for tid in TEMPLATES:
        svg.template(tid, lambda s, tid=tid: draw(s, tid))
    for i, tid in enumerate(t for t in TEMPLATES if not t.startswith('oak-')):
        svg.place('preview ' + tid, tid, (PREVIEW_GAP * (i + 1), PREVIEW_Y), (1, 1), lambda s, tid=tid: draw(s, tid))
    line, x, gaps = OAK_PREVIEW
    for tid in (t for t in TEMPLATES if t.startswith('oak-')):
        svg.place('preview ' + tid, tid, (x, line), (1, 1), lambda s, tid=tid: draw(s, tid))
        x += gaps[tid.split('-')[2]]
    svg.write(cutting.sheet_path('plants/broadleaf.svg'))


def parts():
    """Each template's image, standing on its foot."""
    root, grads = cutting.load('plants/broadleaf.svg')
    return [cutting.foot_part('plants/parts/broadleaf/' + g.get('data-template'), list(g), grads,
                              g.get('data-template'))
            for g in root.iter(cutting.NS + 'g') if g.get('data-template') and not g.get('data-at')]


if __name__ == '__main__':
    main()

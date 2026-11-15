import colorsys
import math

import pytest

from plants import foliage, meadow_flowers
from plants import meadow_flowers_reference as reference
from scene_export import cutting, svgtools


@pytest.fixture(scope='module')
def sheet():
    meadow_flowers.main()
    root, _ = cutting.load('plants/meadow_flowers.svg')
    return {g.get('data-template'): g for g in root.iter(cutting.NS + 'g')
            if g.get('data-template') and not g.get('data-at')}


@pytest.fixture(scope='module')
def parts():
    return {p.path.rpartition('/')[2]: p for p in meadow_flowers.parts()}


def flower_ids():
    return [tid for tid, kind, _ in meadow_flowers.TEMPLATES if kind != 'rock']


def rock_ids():
    return [tid for tid, kind, _ in meadow_flowers.TEMPLATES if kind == 'rock']


def stem_points(group, tid):
    stem = next(p for p in group.iter(cutting.NS + 'path') if p.get('id') == tid + ' stem')
    return list(svgtools._points(stem.get('d')))


def stem_top(group, tid):
    return min(stem_points(group, tid), key=lambda p: p[1])


def bottom_centre(part):
    x, y, w, h = part.box
    return x + w / 2, y + h


def test_every_flower_part_stands_on_the_bottom_centre_of_its_stem(sheet, parts):
    for tid in flower_ids():
        foot = stem_points(sheet[tid], tid)[0]
        assert foot == (0, 0), tid
        assert bottom_centre(parts[tid]) == foot, tid


def test_every_flower_stem_grows_up_from_its_foot(sheet):
    for tid in flower_ids():
        assert all(y <= 0 for _, y in stem_points(sheet[tid], tid)), tid


def test_every_rock_stands_on_its_base_centred_on_its_foot(sheet, parts):
    for tid in rock_ids():
        x0, _, x1, y1 = svgtools.union([svgtools.path_bbox(p.get('d')) for p in sheet[tid].iter(cutting.NS + 'path')])
        assert y1 == 0, tid
        assert abs(x0 + x1) <= 0.1 * (x1 - x0), tid
        assert bottom_centre(parts[tid]) == (0, 0), tid


def test_every_kind_comes_in_a_near_and_a_mid_size():
    ids = flower_ids()
    for tid in ids:
        kind = tid.rpartition('-')[0]
        assert kind + '-near' in ids and kind + '-mid' in ids, tid


def turns(points):
    """How far, in degrees, the outline turns at each of its points between the first and the last."""
    out = []
    for a, b, c in zip(points, points[1:], points[2:]):
        t = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(b[1] - a[1], b[0] - a[0]))
        out.append(abs((t + 180) % 360 - 180))
    return out


# The rock behind the big pink flower was a triangle; the reference's rocks are rounded boulders, so its outline
# over the top bends gently at every point instead of turning sharply at a peak.
def test_the_rock_behind_the_pink_flower_is_rounded_over_its_top(sheet):
    stone = next(p for p in sheet['rock-tall'].iter(cutting.NS + 'path') if p.get('id') == 'rock-tall stone')
    silhouette = list(svgtools._points(stone.get('d')))
    assert max(turns(silhouette[1:-1])) <= 30


# The big pink flower grows from the bottom-left corner, its stem leaning in toward the middle of the scene.
def test_the_big_pink_flower_grows_in_from_the_bottom_left_corner():
    tid, at, size = max((f for f in reference.FLOWERS if 'pink' in f[0]), key=lambda f: f[2])
    (x, y), _ = meadow_flowers.stand(tid, at, size)
    assert x <= 40 and y >= 930
    assert math.degrees(math.atan2(at[0] - x, y - at[1])) >= 25


def test_a_leaning_flower_stands_with_its_head_on_its_reference(sheet):
    for tid in (t for t, kind, _ in meadow_flowers.TEMPLATES if kind == 'flower'):
        foot, s = meadow_flowers.stand(tid, (500, 500), 40)
        top = stem_top(sheet[tid], tid)
        assert math.hypot(foot[0] + top[0] * s - 500, foot[1] + top[1] * s - 500) < 0.5, tid


def head_box(group, tid):
    petals = [p for p in group.iter(cutting.NS + 'path') if p.get('id', '').startswith(tid + ' head petal')
              and p.get('stroke') not in (None, 'none')]
    return svgtools.union([svgtools.path_bbox(p.get('d')) for p in petals])


# The front flowers all faced the viewer flat-on, symmetric; in the reference their heads are turned, seen at an
# angle, so the petals on the far side reach further from the centre than the ones on the near side and the centre
# sits off to one side of the head. The big pink flower in the corner turns right, the others up.
@pytest.mark.parametrize('tid, toward', [
    ('flower-pink-corner', (1, 0)),
    ('flower-pink-near', (0, -1)),
    ('flower-daisy-near', (0, -1)),
    ('flower-buttercup-near', (0, -1)),
    ('flower-violet-near', (0, -1)),
    ('flower-lilac-near', (0, -1)),
])
def test_a_front_flower_head_is_turned_with_its_centre_toward_the_near_side(sheet, tid, toward):
    centre = stem_top(sheet[tid], tid)
    x0, y0, x1, y1 = head_box(sheet[tid], tid)
    middle = ((x0 + x1) / 2, (y0 + y1) / 2)
    off = (centre[0] - middle[0]) * toward[0] + (centre[1] - middle[1]) * toward[1]
    assert off >= 0.08 * max(x1 - x0, y1 - y0), (tid, off)


def hls(colour):
    return colorsys.rgb_to_hls(*(int(colour.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)))


def hsv_saturation(colour):
    return colorsys.rgb_to_hsv(*(int(colour.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)))[1]


def stroked(group):
    return [p for p in group.iter(cutting.NS + 'path') if p.get('stroke') not in (None, 'none')]


# Match all the outlines to the Esme style. Esme's shapes are outlined thin, foliage.STROKE (3 px on the
# 2x sheet) at most and 1.2 px at least (its smallest white flowers), so once a template stands at its largest place
# in the scene no line is thicker than that, and every outlined shape still has a line.
@pytest.mark.parametrize('tid', [t for t, _, _ in meadow_flowers.TEMPLATES])
def test_lines_are_thin_as_esmes_where_the_template_stands_largest(sheet, tid):
    scale = meadow_flowers.placement_scale(tid)
    for p in stroked(sheet[tid]):
        width = float(p.get('stroke-width')) * scale
        assert width <= foliage.STROKE + 0.5, (p.get('id'), width)
        if p.get('fill') != 'none':
            assert width >= 1.2, (p.get('id'), width)


# Esme outlines every shape in a dark shade of its own colour, deep pink round pink, grey-green round white,
# dark green round leaves, never near-black. So every outline here keeps its shape's hue and sits between half and
# four fifths as light, and no line on the sheet is darker than Esme's leaf outline.
@pytest.mark.parametrize('tid', [t for t, _, _ in meadow_flowers.TEMPLATES])
def test_every_outline_is_a_dark_shade_of_the_colour_it_surrounds(sheet, tid):
    for p in stroked(sheet[tid]):
        _, light, _ = hls(p.get('stroke'))
        assert light >= hls(foliage.LEAF_OUTLINE)[1] - 0.01, (p.get('id'), p.get('stroke'))
        fill = p.get('fill')
        if fill == 'none':
            continue
        fill_hue, fill_light, _ = hls(fill)
        hue = hls(p.get('stroke'))[0]
        assert 0.45 <= light / fill_light <= 0.8, (p.get('id'), fill, p.get('stroke'))
        if hsv_saturation(fill) > 0.2:
            assert min(abs(hue - fill_hue), 1 - abs(hue - fill_hue)) <= 35 / 360, (p.get('id'), fill, p.get('stroke'))


def paths(group):
    return [p for p in group.iter(cutting.NS + 'path')]


def leaf_outlines(group, tid):
    return [p for p in paths(group) if p.get('id', '').startswith(tid + ' leaf') and p.get('id').count(' ') == 2]


def stem_centreline(group, tid):
    """The stem's centre line, from the ribbon the stem is drawn as: its foot, the midpoints of its two sides, its
    top."""
    ribbon = stem_points(group, tid)
    n = len(ribbon) // 2
    return [ribbon[0]] + [((ribbon[i][0] + ribbon[-i][0]) / 2, (ribbon[i][1] + ribbon[-i][1]) / 2)
                          for i in range(1, n)] + [ribbon[n]]


def distance_to_polyline(p, pts):
    best = math.inf
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy, l2 = bx - ax, by - ay, (bx - ax) ** 2 + (by - ay) ** 2
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2)) if l2 else 0.0
        best = min(best, math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy))
    return best


# On flower-pink-mid's foot: one of the leaves should go in front of the stem on all the flowers.
@pytest.mark.parametrize('tid', flower_ids())
def test_every_flower_has_a_leaf_in_front_of_its_stem(sheet, tid):
    ids = [p.get('id') for p in paths(sheet[tid])]
    after_stem = ids[ids.index(tid + ' stem'):]
    assert any(i in after_stem for i in (p.get('id') for p in leaf_outlines(sheet[tid], tid))), tid


# On flower-lilac-near's small inner leaf: it doesn't look aligned right; it floated beside the bowed stem and
# crossed it. Every leaf grows from a point on the stem.
@pytest.mark.parametrize('tid', flower_ids())
def test_every_leaf_grows_from_a_point_on_the_stem(sheet, tid):
    centre = stem_centreline(sheet[tid], tid)
    for leaf in leaf_outlines(sheet[tid], tid):
        root = list(svgtools._points(leaf.get('d')))[-1]      # the outline runs out along one side and back to the root
        assert distance_to_polyline(root, centre) <= 0.3, (leaf.get('id'), root)


def petal_bands(group, tid):
    """(petal outline points, shade band points) for each petal of the flower's head."""
    by_id = {p.get('id'): list(svgtools._points(p.get('d'))) for p in paths(group)}
    return [(by_id[i[:-len(' shade')]], pts) for i, pts in by_id.items()
            if i.startswith(tid + ' head petal') and i.endswith(' shade')]


def band_inner_edge(outline, band):
    return [p for p in band if distance_to_polyline(p, outline + outline[:1]) > 1e-6]


# On flower-lilac-mid's lower petals: the edge doesn't look right. The shaded band along a petal's edge was
# painted over the inside half of the petal's outline, thinning it to a wobbly line with a dark band against it; the
# outline is stroked again over the band.
@pytest.mark.parametrize('tid', [t for t, kind, _ in meadow_flowers.TEMPLATES if kind == 'flower'])
def test_a_petals_outline_is_drawn_over_its_shade_band(sheet, tid):
    ids = [p.get('id') for p in paths(sheet[tid])]
    for p in paths(sheet[tid]):
        if p.get('id', '').startswith(tid + ' head petal') and p.get('id').endswith(' shade'):
            petal = p.get('id')[:-len(' shade')]
            after = [q for q in paths(sheet[tid])[ids.index(p.get('id')):]
                     if q.get('id', '').startswith(petal + ' ') or q.get('id') == petal]
            outline = next(q for q in paths(sheet[tid]) if q.get('id') == petal + ' outline').get('stroke')
            assert outline not in (None, 'none'), petal
            assert any(q.get('stroke') == outline and q.get('fill') == 'none' for q in after), petal


# and the band ran right round the tip to its notch, where its end showed as a lump; it fades out short of the notch.
@pytest.mark.parametrize('tid', [t for t, kind, _ in meadow_flowers.TEMPLATES if kind == 'flower'])
def test_a_petals_shade_band_fades_out_short_of_the_tips_notch(sheet, tid):
    for outline, band in petal_bands(sheet[tid], tid):
        notch = outline[7 + 7]     # the outline runs up one side (7 points) and round the tip, the notch at its middle
        x0, y0, x1, y1 = svgtools.union([svgtools.path_bbox(poly_d(outline))])
        reach = min(math.hypot(x - notch[0], y - notch[1]) for x, y in band)
        assert reach >= 0.12 * max(x1 - x0, y1 - y0), (tid, reach)


def poly_d(points):
    return 'M ' + ' L '.join('%s %s' % p for p in points) + ' Z'


def pink_ids():
    return [tid for tid, kind, args in meadow_flowers.TEMPLATES if kind == 'flower' and args[0] == 'pink']


def head_paths(group, tid, suffix):
    return [p for p in paths(group) if p.get('id', '').startswith(tid + ' head petal') and p.get('id').endswith(suffix)]


def petal_of(path_id):
    return path_id.rsplit(' ', 1)[0]


def farthest(points, centre):
    return max(math.hypot(x - centre[0], y - centre[1]) for x, y in points)


# On the big pink flower in the corner: it still looked wrong, redo it to match the reference. Its petals were
# thin blades parted by wide gaps; the reference's five petals are broad lobes, half the head's radius wide either
# side of their midrib, lying over their neighbours.
@pytest.mark.parametrize('tid', pink_ids())
def test_a_pink_petal_is_a_broad_lobe(tid):
    half_width = meadow_flowers.template_args(tid)[2][0]
    assert half_width >= 0.5, half_width


# and the reference outlines the pink flower in a dark plum, far darker than Esme's mid pink petal outline.
@pytest.mark.parametrize('tid', pink_ids())
def test_a_pink_petal_is_outlined_in_dark_plum(sheet, tid):
    outlines = head_paths(sheet[tid], tid, ' outline')
    assert outlines
    for p in outlines:
        assert hls(p.get('stroke'))[1] <= 0.36, p.get('stroke')


# and its veins are three to a petal, radiating from the centre well out toward the notch at the petal's tip.
@pytest.mark.parametrize('tid', pink_ids())
def test_a_pink_petal_has_three_long_veins(sheet, tid):
    centre = stem_top(sheet[tid], tid)
    by_id = {p.get('id'): p for p in paths(sheet[tid])}
    veins = head_paths(sheet[tid], tid, ' veins')
    assert veins
    for p in veins:
        assert p.get('d').count('M') >= 3, p.get('id')
        notch = list(svgtools._points(by_id[petal_of(p.get('id'))].get('d')))[7 + 7]
        reach = farthest(list(svgtools._points(p.get('d'))), centre) / math.hypot(notch[0] - centre[0], notch[1] - centre[1])
        assert reach >= 0.4, (p.get('id'), reach)


# and each petal is faceted, a lighter band along its edge toward the light beside the body colour.
@pytest.mark.parametrize('tid', pink_ids())
def test_a_pink_petal_has_a_lit_facet(sheet, tid):
    by_id = {p.get('id'): p for p in paths(sheet[tid])}
    facets = head_paths(sheet[tid], tid, ' lit')
    assert len(facets) == 5
    for p in facets:
        assert hls(p.get('fill'))[1] > hls(by_id[petal_of(p.get('id'))].get('fill'))[1], p.get('id')


def lobes(points, k=4):
    """How many lobes the outline has: points further from its middle than their neighbours k steps either way by a
    visible margin."""
    cx, cy = (sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points))
    n = len(points)
    r = [math.hypot(x - cx, y - cy) for x, y in points]
    return sum(1 for i in range(n) if r[i] >= max(r[(i + j) % n] for j in range(-k, k + 1))
               and r[i] - min(r[(i - k) % n], r[(i + k) % n]) > 0.03 * r[i])


# and the centre is a yellow trumpet with a scalloped rim, not a flat star: its cup's outline bulges into lobes.
@pytest.mark.parametrize('tid', pink_ids())
def test_a_pink_flowers_centre_has_a_scalloped_rim(sheet, tid):
    centre = next(p for p in paths(sheet[tid]) if p.get('id') == tid + ' head centre')
    assert lobes(list(svgtools._points(centre.get('d')))) >= 3


# On the big pink flower in the corner: the petals aren't individually bordered. Each petal was outlined only
# round its lobe, leaving the seams between overlapping petals unlined; each is outlined all the way round.
@pytest.mark.parametrize('tid', pink_ids())
def test_every_pink_petal_is_outlined_all_the_way_round(sheet, tid):
    by_id = {p.get('id'): p for p in paths(sheet[tid])}
    outlines = head_paths(sheet[tid], tid, ' outline')
    assert len(outlines) == 5
    for p in outlines:
        assert p.get('d').rstrip().endswith('Z'), p.get('id')
        edge = list(svgtools._points(by_id[petal_of(p.get('id'))].get('d')))
        assert list(svgtools._points(p.get('d'))) == edge, p.get('id')


def head_part(group, tid, part):
    return list(svgtools._points(next(p for p in paths(group) if p.get('id') == tid + ' head ' + part).get('d')))


def middle_of(points):
    return sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points)


# and its centre looked wrong, not centred, maybe rotated wrong: the trumpet stood off up and right of where the petals
# meet, leaning a fixed way whichever way the head was turned. It grows from where the petals meet.
@pytest.mark.parametrize('tid', pink_ids())
def test_a_pink_flowers_trumpet_grows_from_where_its_petals_meet(sheet, tid):
    centre, radius = stem_top(sheet[tid], tid), meadow_flowers.template_args(tid)[1]
    foot = middle_of(head_part(sheet[tid], tid, 'throat shadow'))
    assert math.hypot(foot[0] - centre[0], foot[1] - centre[1]) <= 0.12 * radius, (tid, foot, centre)


# and it rises out of the head the way the petals rise, its rim a circle seen as the head is turned: foreshortened
# along the direction the head is turned toward.
@pytest.mark.parametrize('tid', pink_ids())
def test_a_pink_flowers_trumpet_is_turned_with_its_head(sheet, tid):
    centre = stem_top(sheet[tid], tid)
    toward = math.radians(meadow_flowers.FACES.get(tid, meadow_flowers.FLAT)[1])
    n = (math.cos(toward), math.sin(toward))
    rim = head_part(sheet[tid], tid, 'centre')
    cup = middle_of(rim)
    tips = middle_of([farthest_point(head_part(sheet[tid], tid, 'petal %d' % i), centre) for i in range(1, 6)])
    assert (cup[0] - centre[0]) * (tips[0] - centre[0]) + (cup[1] - centre[1]) * (tips[1] - centre[1]) > 0, tid
    along = [(x - cup[0]) * n[0] + (y - cup[1]) * n[1] for x, y in rim]
    across = [(y - cup[1]) * n[0] - (x - cup[0]) * n[1] for x, y in rim]
    assert max(along) - min(along) < max(across) - min(across), tid


def farthest_point(points, centre):
    return max(points, key=lambda p: math.hypot(p[0] - centre[0], p[1] - centre[1]))


# Remove the right pink flower. The big pink flower among the right foreground's flowers is gone; the corner one
# on the left and the small mid ones stay.
def test_no_big_pink_flower_stands_in_the_right_foreground():
    assert not [f for f in reference.FLOWERS if f[0].startswith('flower-pink') and f[1][0] > 768 and f[2] > 40]

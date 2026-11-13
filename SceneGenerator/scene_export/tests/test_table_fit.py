import math
import re

import numpy as np
import pytest

from scene_export import GENERATOR  # noqa: F401
from furniture import table_set
from furniture import table_set_reference as T

TABLE_TOLERANCE = 6       # stage px
CHAIR_TOLERANCE = 9


@pytest.fixture(scope='module')
def drawn():
    return table_set.draw_set()


@pytest.fixture(scope='module')
def errors(drawn):
    return table_set.check(drawn)


def ids(out):
    return [m.group(1) for line in out.body for m in [re.search(r'<path id="([^"]+)"', line)] if m]


def landmark_count(piece):
    return sum(len(piece.get(kind, {})) for kind in ('points', 'rings', 'boxes', 'diamonds', 'feet'))


def test_check_measures_every_landmark_of_every_piece(errors):
    assert len(errors) == sum(landmark_count(p) for p in T.PIECES.values())


def test_the_table_meets_the_paintings_landmarks(errors):
    off = [(k, round(e, 1)) for piece, k, e in errors if piece == 'table' and e > TABLE_TOLERANCE]
    assert not off


@pytest.mark.parametrize('name', [n for n in T.PIECES if n.startswith('chair')])
def test_each_chair_meets_the_paintings_landmarks(errors, name):
    off = [(k, round(e, 1)) for piece, k, e in errors if piece == name and e > CHAIR_TOLERANCE]
    assert not off


def test_the_upper_pedestal_is_a_lattice_of_straps_leaning_both_ways(drawn):
    straps = [i for i in ids(drawn) if re.fullmatch(r'pedestal upper lattice strap (left|right) -?\d+', i)]
    assert any(' left ' in s for s in straps) and any(' right ' in s for s in straps)


def test_the_lower_pedestal_is_a_plain_bell_with_no_straps(drawn):
    assert not [i for i in ids(drawn) if i.startswith('pedestal lower') and ' strap' in i]


def test_the_lower_bell_shows_only_its_front_gem(drawn):
    gems = [i for i in ids(drawn) if re.fullmatch(r'pedestal lower bell gem \w+ rim', i)]
    assert gems == ['pedestal lower bell gem front rim']


def test_the_lower_bells_gem_sits_in_a_frame_of_its_own(drawn):
    assert 'pedestal lower bell gem front setting' in ids(drawn)


def test_the_pedestal_has_no_glass_core(drawn):
    assert not [i for i in ids(drawn) if 'glass' in i]


def test_a_hidden_box_side_is_not_measured():
    assert table_set._box_error((0, 0, 10, 10), (None, 1, 10, 10)) == 1


def chair_feet_span(name, toe_out, monkeypatch):
    size, stretch, tilt = table_set.CHAIR_TWEAKS[name][:3]
    monkeypatch.setitem(table_set.CHAIR_TWEAKS, name, (size, stretch, tilt, toe_out))
    cs = table_set.Scene(table_set.CHAIR_CAMERA)
    (n, s, f), = [p for p in table_set.chair_placements(cs) if p[0] == name]
    out = table_set.Out()
    table_set.draw_chair(cs, out, n, s, f)
    feet = [p for k, p in table_set.drawn_paths(out).items() if re.fullmatch(name + r' foot (front|back) (left|right)', k)]
    xs = [x for pts in feet for x, _ in pts]
    return max(xs) - min(xs)


def test_each_chair_splays_its_feet_by_its_own_toe_out(monkeypatch):
    assert chair_feet_span('chair front left', 0.5, monkeypatch) > chair_feet_span('chair front left', -0.2, monkeypatch) + 10


def test_the_upper_lattices_ends_tuck_under_the_collar(drawn):
    names = ids(drawn)
    assert names.index('pedestal collar') > max(n for n, i in enumerate(names) if i.startswith('pedestal upper lattice strap'))


def test_no_strap_sticks_out_past_the_pedestals_silhouette(drawn):
    paths = table_set.drawn_paths(drawn)
    core = paths['pedestal upper lattice core']
    out = []
    for k, pts in paths.items():
        if re.fullmatch(r'pedestal upper lattice strap (left|right) -?\d+', k):
            for x, y in pts:
                if inside(paths['pedestal collar'], (x, y)):
                    continue
                lo, hi = table_set.span_at([core], y)
                if not (lo - 1.5 <= x <= hi + 1.5):
                    out.append((k, x, y))
    assert not out


def test_the_collar_shows_no_top_face_only_its_front_edge(drawn):
    collar = table_set.drawn_paths(drawn)['pedestal collar']
    x0, _, x1, _ = table_set.bbox(collar)
    top = min(collar, key=lambda p: p[1])
    # its highest points are where it turns out of sight at the sides, not the back of a cap
    assert abs(top[0] - (x0 + x1) / 2) > 0.4 * (x1 - x0)


def test_the_collars_top_edge_has_no_hook_rising_inside_its_ends(drawn):
    collar = table_set.drawn_paths(drawn)['pedestal collar']
    x0, _, x1, _ = table_set.bbox(collar)
    top = min(collar, key=lambda p: p[1])
    assert min(top[0] - x0, x1 - top[0]) < 3


def test_a_ribbon_keeps_its_width_round_a_sharp_corner():
    import numpy as np
    scene = table_set.Scene(table_set.TABLE_CAMERA)
    c = np.array(table_set.floor_under(scene, table_set.TABLE_SCREEN))
    h = 150 * table_set.PX
    # an L in the plane facing the camera at the table's middle, its corner at the bottom left
    corner, a, b = c + [0, h, 0], c + [0, h + 0.2, 0], c + [0.2, h, 0]
    line = [a + (corner - a) * t for t in np.linspace(0, 1, 9)] + [corner + (b - corner) * t for t in np.linspace(0, 1, 9)[1:]]
    w = 0.01
    band = table_set.ribbon(scene, line, [w] * len(line))
    k = np.array(scene.project(corner))
    w_px = w * scene.scale(corner)
    legs = [np.array(scene.project(q)) - k for q in (a, b)]
    out = -sum(v / np.linalg.norm(v) for v in legs)
    out /= np.linalg.norm(out)
    # the band's edge along the corner's outer bisector
    reach = max(float(np.dot(np.array(p) - k, out)) for p in band
                if abs(out[0] * (p[1] - k[1]) - out[1] * (p[0] - k[0])) < 0.2 * w_px)
    assert reach > 1.3 * w_px


def test_the_upper_gem_sits_straight_on_the_straps_ring_with_no_setting(drawn):
    names = ids(drawn)
    assert 'pedestal upper lattice ring' in names and 'pedestal upper lattice gem front setting' not in names


def test_the_upper_ring_is_filled_over_the_straps_under_its_gem(drawn):
    names = ids(drawn)
    straps = [n for n, i in enumerate(names) if re.fullmatch(r'pedestal upper lattice strap (left|right) -?\d+', i)]
    ring = names.index('pedestal upper lattice ring')
    assert straps and max(straps) < ring < names.index('pedestal upper lattice gem front rim')


def test_the_upper_ring_spans_the_gem(drawn):
    paths = table_set.drawn_paths(drawn)
    ring, gem = table_set.bbox(paths['pedestal upper lattice ring']), table_set.bbox(paths['pedestal upper lattice gem front rim'])
    assert ring[0] < gem[0] - 4 and ring[2] > gem[2] + 4 and ring[3] > gem[3] + 4


def inside(points, p):
    """Even-odd: whether p is inside the closed outline."""
    x, y = p
    hit = False
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (x1 - x0) * (y - y0) / (y1 - y0):
            hit = not hit
    return hit


def test_the_lower_bell_stands_on_the_plinths_ledge_inside_its_front(drawn):
    names = ids(drawn)
    bell = [n for n, i in enumerate(names) if i.startswith('pedestal lower bell')]
    assert names.index('pedestal plinth ledge') < min(bell) and names.index('pedestal plinth rim') > max(bell)


def test_the_plinth_is_wider_than_the_bell_it_holds(drawn):
    paths = table_set.drawn_paths(drawn)
    ledge, core = table_set.bbox(paths['pedestal plinth ledge']), table_set.bbox(paths['pedestal lower bell'])
    assert ledge[0] < core[0] - 5 and ledge[2] > core[2] + 5


def fills(out):
    return {m.group(1): m.group(2) for line in out.body for m in [re.search(r'<path id="([^"]+)" d="[^"]+" fill="([^"]+)"', line)] if m}


def test_straps_turned_away_from_the_light_are_painted_in_shade(drawn):
    paths, paint = table_set.drawn_paths(drawn), fills(drawn)
    rim = paths['pedestal upper lattice gem front rim']
    gem_x = (table_set.bbox(rim)[0] + table_set.bbox(rim)[2]) / 2
    straps = [k for k in paths if re.fullmatch(r'pedestal upper lattice strap (left|right) -?\d+', k)]
    shaded = [k for k in straps if paint[k] == 'url(#gold-strap-shade)']
    centre_x = lambda k: (table_set.bbox(paths[k])[0] + table_set.bbox(paths[k])[2]) / 2
    assert shaded and all(centre_x(k) > gem_x for k in shaded)
    assert any(paint[k] == 'url(#gold-strap)' for k in straps)



def upper_straps(paths, family):
    return [pts for k, pts in paths.items() if re.fullmatch(r'pedestal upper lattice strap %s -?\d+' % family, k)]


def test_one_family_of_straps_lies_over_the_other(drawn):
    names = ids(drawn)
    family = lambda f: [n for n, i in enumerate(names) if re.fullmatch(r'pedestal upper lattice strap %s -?\d+' % f, i)]
    assert family('left') and family('right') and max(family('left')) < min(family('right'))


def strokes(out):
    return {m.group(1): m.group(2) for line in out.body
            for m in [re.search(r'<path id="([^"]+)" d="[^"]+" fill="[^"]+" stroke="([^"]+)"', line)] if m}


def test_the_upper_ring_is_outlined_like_a_strap(drawn):
    assert strokes(drawn).get('pedestal upper lattice ring') == table_set.OUTLINE['strap']


@pytest.mark.parametrize('side', ['left', 'right'])
def test_a_rib_runs_down_each_side_of_the_upper_lattice_along_its_silhouette(drawn, side):
    paths = table_set.drawn_paths(drawn)
    rib, core = paths['pedestal upper lattice rib %s' % side], paths['pedestal upper lattice core']
    _, y0, _, y1 = table_set.bbox(rib)
    mid = (y0 + y1) / 2
    (lo, hi), (r0, r1) = table_set.span_at([core], mid), table_set.span_at([rib], mid)
    assert (abs(r0 - lo) if side == 'left' else abs(r1 - hi)) < 3 and y1 - y0 > 30


def test_the_marbles_back_edge_is_outlined_lighter_than_its_front(drawn):
    lines = strokes(drawn)
    assert lines['table marble'] != table_set.MARBLE_LINE and lines['table marble front edge'] == table_set.MARBLE_LINE


def test_the_upper_rings_right_half_is_shaded(drawn):
    paths, paint = table_set.drawn_paths(drawn), fills(drawn)
    x0, _, x1, _ = table_set.bbox(paths['pedestal upper lattice ring'])
    s0, _, s1, _ = table_set.bbox(paths['pedestal upper lattice ring dark half'])
    assert s0 > x0 + 0.3 * (x1 - x0) and s1 == x1
    assert paint['pedestal upper lattice ring dark half'] != paint['pedestal upper lattice ring']


def test_the_lower_gems_glint_is_a_streak_from_its_left_point_to_its_middle(drawn):
    gem = 'pedestal lower bell gem front'
    paths = table_set.drawn_paths(drawn)
    x0, y0, x1, y1 = table_set.bbox(paths[gem + ' rim'])
    g0, h0, g1, h1 = table_set.bbox(paths[gem + ' glint'])
    assert g0 < x0 + 0.2 * (x1 - x0) and g1 < (x0 + x1) / 2 + 0.15 * (x1 - x0) and h1 - h0 < 0.25 * (y1 - y0)


def test_the_upper_gem_has_no_glint_across_its_facets(drawn):
    assert 'pedestal upper lattice gem front glint' not in table_set.drawn_paths(drawn)


def test_no_flat_band_cuts_across_the_lattice_backgrounds_gradient_above_the_collar(drawn):
    assert 'pedestal upper lattice foot' not in table_set.drawn_paths(drawn)


def test_the_collars_sheen_tapers_off_at_both_ends(drawn):
    sheen = table_set.drawn_paths(drawn)['pedestal collar sheen']
    # its top edge runs end to end, then its bottom edge back
    n = len(sheen) // 2
    gap = lambda i: math.dist(sheen[i], sheen[len(sheen) - 1 - i])
    assert gap(0) < 0.3 * gap(n // 2) and gap(n - 1) < 0.3 * gap(n // 2)


def test_a_dark_band_lies_under_the_tops_rim(drawn):
    paths = table_set.drawn_paths(drawn)
    x0, _, x1, band = table_set.bbox(paths['table edge'])
    shade = paths['pedestal shade under rim']
    # at the front, just under the band, and no more than a few px deep
    assert inside(shade, ((x0 + x1) / 2, band + 2)) and not inside(shade, ((x0 + x1) / 2, band + 12))


def test_the_base_is_a_skirt_flaring_out_to_its_foot():
    assert table_set.foot(0.0) > 1.08 * table_set.foot(table_set.FOOT_HEIGHT)


def test_the_upper_rings_side_corners_mirror_each_other_about_its_gem(drawn):
    paths = table_set.drawn_paths(drawn)
    gx0, _, gx1, _ = table_set.bbox(paths['pedestal upper lattice gem front rim'])
    ring = paths['pedestal upper lattice ring']
    left, right = min(ring), max(ring)
    gx = (gx0 + gx1) / 2
    assert abs((gx - left[0]) - (right[0] - gx)) < 2 and abs(left[1] - right[1]) < 1.5


def test_the_straps_meet_the_top_mirrored_about_the_gem(drawn):
    paths = table_set.drawn_paths(drawn)
    gx0, _, gx1, _ = table_set.bbox(paths['pedestal upper lattice gem front rim'])
    gx = (gx0 + gx1) / 2
    top = table_set.bbox(paths['pedestal upper lattice core'])[1]
    lo, hi = table_set.span_at([paths['pedestal upper lattice core']], top + 30)
    # where each strap's centre crosses a row near the top, inside the ribs
    xs = sorted(x for k in paths if re.fullmatch(r'pedestal upper lattice strap (left|right) -?\d+', k)
                for x in [sum(table_set.span_at([paths[k]], top + 30)) / 2] if x == x and lo + table_set.RIB_PX < x < hi - table_set.RIB_PX)
    assert xs and all(min(abs((2 * gx - x) - y) for y in xs) < 4 for x in xs)


@pytest.mark.parametrize('gem, piece', [('pedestal upper lattice gem front', 'pedestal upper lattice core'),
                                        ('pedestal lower bell gem front', 'pedestal lower bell')])
def test_each_gem_sits_in_the_middle_of_its_piece(drawn, gem, piece):
    paths = table_set.drawn_paths(drawn)
    x0, y0, x1, y1 = table_set.bbox(paths[gem + ' rim'])
    lo, hi = table_set.span_at([paths[piece]], (y0 + y1) / 2)
    assert abs((x0 + x1) / 2 - (lo + hi) / 2) < 1.5


def test_every_strap_has_a_mirror_twin_in_the_other_family(drawn):
    paths = table_set.drawn_paths(drawn)
    gx0, _, gx1, _ = table_set.bbox(paths['pedestal upper lattice gem front rim'])
    gx = (gx0 + gx1) / 2
    boxes = {f: [table_set.bbox(pts) for pts in upper_straps(paths, f)] for f in ('left', 'right')}
    mirrored = lambda b: (2 * gx - b[2], b[1], 2 * gx - b[0], b[3])
    assert len(boxes['left']) == len(boxes['right'])
    for b in boxes['left']:
        assert min(max(abs(u - v) for u, v in zip(mirrored(b), o)) for o in boxes['right']) < 3


def strap_rows(paths, key, margin=4):
    _, y0, _, y1 = table_set.bbox(paths[key])
    return [(y, table_set.span_at([paths[key]], y)) for y in np.arange(y0 + margin, y1 - margin, 1.0)]


def test_straps_run_inside_the_ribs_never_under_them(drawn):
    paths = table_set.drawn_paths(drawn)
    left, right = paths['pedestal upper lattice rib left'], paths['pedestal upper lattice rib right']
    hidden = lambda p: any(inside(paths[k], p) for k in ('table edge', 'table apron', 'pedestal collar'))
    for k in paths:
        if re.fullmatch(r'pedestal upper lattice strap (left|right) -?\d+', k):
            for y, (lo, hi) in strap_rows(paths, k):
                if hidden((lo, y)) or hidden((hi, y)):
                    continue
                l0, l1 = table_set.span_at([left], y)
                r0, r1 = table_set.span_at([right], y)
                assert not (lo < l1 - 1) and not (hi > r0 + 1), (k, round(y))


def test_the_upper_rings_bottom_tip_runs_on_under_the_collar_unflattened(drawn):
    paths = table_set.drawn_paths(drawn)
    ring, core = paths['pedestal upper lattice ring'], paths['pedestal upper lattice core']
    gx0, _, gx1, _ = table_set.bbox(paths['pedestal upper lattice gem front rim'])
    bottom = table_set.bbox(core)[3]
    # still a point where it goes in behind the collar
    lo, hi = table_set.span_at([ring], bottom - 2)
    assert abs((lo + hi) / 2 - (gx0 + gx1) / 2) < 1.5 and hi - lo < 3 * table_set.STRAP_PX


def test_the_upper_rings_bottom_tip_stays_hidden_behind_the_collar(drawn):
    paths = table_set.drawn_paths(drawn)
    bottom = table_set.bbox(paths['pedestal upper lattice core'])[3]
    below = [p for p in paths['pedestal upper lattice ring'] if p[1] > bottom]
    assert all(inside(paths['pedestal collar'], p) for p in below)


@pytest.mark.parametrize('side', ['left', 'right'])
def test_each_rib_is_lit_by_one_streak_along_its_outer_edge(drawn, side):
    paths = table_set.drawn_paths(drawn)
    rib = paths['pedestal upper lattice rib %s' % side]
    streaks = [k for k in paths if re.fullmatch(r'pedestal upper lattice rib %s (sheen|shade)( \d+)?' % side, k)]
    assert streaks == ['pedestal upper lattice rib %s sheen' % side]
    streak = paths[streaks[0]]
    _, r0, _, r1 = table_set.bbox(rib)
    _, s0, _, s1 = table_set.bbox(streak)
    mid = (s0 + s1) / 2
    lo, hi = table_set.span_at([rib], mid)
    a, b = table_set.span_at([streak], mid)
    assert s1 - s0 > 0.6 * (r1 - r0)
    assert ((a + b) / 2 < (lo + hi) / 2) if side == 'left' else ((a + b) / 2 > (lo + hi) / 2)


def test_each_strap_is_lit_by_one_streak_along_its_left_edge(drawn):
    paths = table_set.drawn_paths(drawn)
    straps = [k for k in paths if re.fullmatch(r'pedestal upper lattice strap (left|right) \d+', k)]
    for key in straps:
        streaks = [k for k in paths if re.fullmatch(re.escape(key) + r' (sheen|shade)( \d+)?', k)]
        assert streaks == [key + ' sheen'], key
        _, y0, _, y1 = table_set.bbox(paths[key])
        mid = (y0 + y1) / 2
        lo, hi = table_set.span_at([paths[key]], mid)
        a, b = table_set.span_at([paths[key + ' sheen']], mid)
        assert (a + b) / 2 < (lo + hi) / 2, key


def crossings(points, y0, y1):
    """Pairs of non-neighbouring edges of a closed outline that cross, among its edges between heights y0 and y1."""
    count = len(points)
    edges = [(points[i], points[(i + 1) % count]) for i in range(count)]
    seen = [i for i, (p, q) in enumerate(edges) if y0 < p[1] < y1 and y0 < q[1] < y1]

    def side(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    found = []
    for k, i in enumerate(seen):
        for j in seen[k + 2:]:
            if (j + 1) % count == i:
                continue
            (a, b), (c, d) = edges[i], edges[j]
            if side(a, b, c) * side(a, b, d) < 0 and side(c, d, a) * side(c, d, b) < 0:
                found.append((i, j))
    return found


def test_no_strap_twists_over_itself_where_it_shows(drawn):
    paths = table_set.drawn_paths(drawn)
    shown_from = table_set.bbox(paths['table apron'])[3]
    shown_to = table_set.bbox(paths['pedestal upper lattice core'])[3] - 2
    for key in [k for k in paths if re.fullmatch(r'pedestal upper lattice strap (left|right) \d+', k)]:
        assert not crossings(paths[key], shown_from, shown_to), key


def test_the_straps_run_on_below_the_lattice_only_behind_the_collar(drawn):
    paths = table_set.drawn_paths(drawn)
    bottom = table_set.bbox(paths['pedestal upper lattice core'])[3]
    for key in [k for k in paths if re.fullmatch(r'pedestal upper lattice strap (left|right) \d+( sheen)?', k)]:
        assert all(inside(paths['pedestal collar'], p) for p in paths[key] if p[1] > bottom), key


@pytest.mark.parametrize('side', ['left', 'right'])
def test_below_the_rings_side_corners_no_strap_runs_down_between_it_and_the_rib(drawn, side):
    paths = table_set.drawn_paths(drawn)
    ring, rib = paths['pedestal upper lattice ring'], paths['pedestal upper lattice rib %s' % side]
    corner = min(ring) if side == 'left' else max(ring)
    bottom = table_set.bbox(paths['pedestal upper lattice core'])[3]
    straps = [k for k in paths if re.fullmatch(r'pedestal upper lattice strap (left|right) \d+', k)]
    for y in np.arange(corner[1] + table_set.STRAP_PX, bottom - table_set.RING_TUCK_PX, 2.0):
        r0, r1 = table_set.span_at([ring], y)
        b0, b1 = table_set.span_at([rib], y)
        x = (b1 + r0) / 2 if side == 'left' else (r1 + b0) / 2
        assert not [k for k in straps if inside(paths[k], (x, y))], round(y)


def test_the_lattice_background_is_a_light_yellow(drawn):
    import colorsys
    paint = fills(drawn)
    bands = [paint[k] for k in paint if re.fullmatch(r'pedestal upper lattice core shade \d+', k)]
    assert bands
    for colour in bands:
        h, l, s = colorsys.rgb_to_hls(*(int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)))
        assert 36 <= h * 360 <= 58 and l >= 0.5, colour


def test_the_lattice_background_brightens_down_toward_its_foot(drawn):
    paths, names = table_set.drawn_paths(drawn), ids(drawn)
    glows = [k for k in names if re.fullmatch(r'pedestal upper lattice core glow \d+', k)]
    assert len(glows) >= 3
    bottom = table_set.bbox(paths['pedestal upper lattice core'])[3]
    tops = [table_set.bbox(paths[k])[1] for k in glows]
    assert tops == sorted(tops, reverse=True) and all(abs(table_set.bbox(paths[k])[3] - bottom) < 3 for k in glows)
    straps = [n for n, i in enumerate(names) if i.startswith('pedestal upper lattice strap')]
    assert max(names.index(k) for k in glows) < min(straps)


def lightness(colour):
    import colorsys
    return colorsys.rgb_to_hls(*(int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)))[1]


def chroma(colour):
    rgb = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return max(rgb) - min(rgb)


def test_the_marble_is_lit_a_clean_white_not_cream(drawn):
    paint = fills(drawn)
    for k in ('table marble cloud 1', 'table marble sheen'):
        assert chroma(paint[k]) <= 0.04, k


def test_the_marbles_shaded_side_is_a_soft_grey_beige(drawn):
    shade = fills(drawn)['table marble shade edge']
    assert lightness(shade) <= 0.86 and chroma(shade) <= 0.15


def test_the_marble_has_faint_veins_across_it(drawn):
    assert len([k for k in ids(drawn) if re.fullmatch(r'table marble vein \d+', k)]) >= 3


def test_the_tops_gold_band_is_a_mellow_gold_not_a_hot_yellow(drawn):
    paint = fills(drawn)
    bands = [paint[k] for k in paint if re.fullmatch(r'table edge shade \d+', k)]
    assert chroma(bands[len(bands) // 2]) <= 0.72

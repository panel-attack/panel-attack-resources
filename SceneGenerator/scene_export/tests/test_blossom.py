import colorsys
import math
import re

import pytest

from common.painting import HEIGHT, Svg, hexrgb
from plants import blossom, blossom_template
from scene_export import cutting


def cut():
    blossom.main()
    return dict(blossom.cut())


def test_each_loose_cluster_hangs_from_the_end_of_its_twig():
    for tid, cluster in blossom.CLUSTERS.items():
        points, _ = blossom.LIMBS[cluster['twig']]
        assert points[-1] == cluster['hang'], tid


def test_each_loose_cluster_image_is_centred_on_where_it_hangs():
    parts = cut()
    for tid, cluster in blossom.CLUSTERS.items():
        x, y, w, h = parts[tid].box
        assert (x + w / 2, y + h / 2) == cluster['hang'], tid


def test_the_loose_clusters_swing_about_where_they_hang():
    nodes = {n['id']: n for n in blossom_template.build()['drawables']}
    for tid in blossom.CLUSTERS:
        assert nodes[tid]['anchor'] == 'center'
        assert nodes[tid]['pivot'] == 'center'


def test_the_trunk_reaches_past_the_left_edge_and_under_the_meadow():
    x, y, w, h = cut()['blossom-trunk'].box
    assert x == 0
    assert y + h >= blossom.MEADOW


def test_the_crown_reaches_past_the_top_edge():
    boxes = [part.box for tid, part in cut().items() if tid.startswith('blossom-crown')]
    assert min(box[1] for box in boxes) == 0
    assert max(box[0] + box[2] for box in boxes) >= blossom.CROWN_REACH


def test_the_trunk_draws_under_the_crown_and_the_loose_clusters():
    order = [n['id'] for n in blossom_template.build()['drawables']]
    assert order[0] == 'blossom-trunk'
    assert all(order.index(tid) > order.index('blossom-trunk') for tid in blossom.CLUSTERS)


def trunk_ids():
    root, _ = cutting.load('plants/blossom.svg')
    return [el.get('id') for el in cutting.find_group(root, 'blossom trunk').iter() if el.tag.endswith('path')]


def test_each_limb_draws_its_body_shade_and_lit_together_back_to_front():
    """After the outlines, each limb's body is followed by its own shade and lit strip, so the next limb, in front,
    covers all three; the trunk, in front of every limb, comes last, then the crotch flares, before the bark streaks
    over it."""
    blossom.main()
    ids = [i for i in trunk_ids() if not i.startswith('limb outline')]
    runs, run = [], None
    for i in ids:
        if i == 'limb' or re.fullmatch(r'limb \d+', i):
            run = [i]
            runs.append(run)
        else:
            run.append(i)
    assert len(runs) == len(blossom.LIMBS)
    assert sum(any(i.startswith('limb shade') for i in run) for run in runs) == 6
    assert sum(any(i.startswith('limb lit') for i in run) for run in runs) == 5
    assert ([re.sub(r' \d+$', '', i) for i in runs[-1]]
            == ['limb', 'limb shade', 'limb lit'] + ['limb flare'] * len(blossom.CROTCHES) + ['bark streaks'])


def test_every_blossom_shades_the_same_one_petal_away_from_the_light():
    for turn in range(-90, 90, 3):
        assert len(blossom.deep_angles(turn)) == 1, turn


def test_the_shaded_petals_stay_close_to_the_petals_body():
    deep, body = hexrgb(blossom.PETAL['deep']), hexrgb(blossom.PETAL['body'])
    assert max(abs(a - b) for a, b in zip(deep, body)) <= 30


def back_ids(gid):
    blossom.main()
    root, _ = cutting.load('plants/blossom.svg')
    return [el.get('id') or '' for el in cutting.find_group(root, gid).iter() if el.tag.endswith('path')]


def test_the_back_mass_is_sealed_before_its_blossoms_are_detailed():
    """Each crown's back layer starts with the one sealed magenta mass, then every shaded blossom drawn over it with
    its petals edged, so no chink shows and the mass is never a flat blob."""
    for gid, back in (('blossom crown left', blossom.BACK_LEFT), ('blossom crown right', blossom.BACK_RIGHT)):
        ids = back_ids(gid)
        assert re.fullmatch(r'back blossom( \d+)?', ids[0]), gid
        assert sum(i.startswith('back blossom edge') for i in ids) == len(back), gid
        assert sum(i.startswith('back blossom pale') for i in ids) == len(back), gid


def test_the_back_blossoms_are_edged_in_a_darker_shade_of_their_own_magenta():
    """The edge is the back's own hue, darker, still a light colour as test_the_blossoms_have_no_dark_line asks."""
    (eh, es, ev), (bh, _, bv) = hsv(blossom.BACK_EDGE), hsv(blossom.BACK)
    assert min(abs(eh - bh), 360 - abs(eh - bh)) <= ESME_HUE_TOLERANCE / 4
    assert 0.8 <= ev / bv <= 0.92
    assert es >= ESME_SATURATION
    assert hsv(blossom.BACK_PALE)[2] > bv


def flower_paths(x, y, r, turn):
    svg = Svg()
    blossom.flower(svg, x, y, r, turn)
    return [(re.search(r'id="([^"]+)"', part).group(1), part) for part in svg.parts if part.startswith('<path')]


def test_each_blossoms_heart_sits_on_the_centre_of_its_pale_petals():
    """All five petals carry a pale inner part centred on the blossom, the shaded one a deeper pale, so the heart sits
    on the centre of the pale ring instead of looking slipped toward the shade."""
    for turn in (0, 15, -20, 40):
        pale = [d for ident, d in flower_paths(100, 100, 50, turn) if ident.startswith('blossom pale')]
        pts = [tuple(map(float, xy.split(','))) for d in pale for xy in re.findall(r'-?[\d.]+,-?[\d.]+', d)]
        assert sum(d.count('M') for d in pale) == 5, turn
        assert sum(x for x, _ in pts) / len(pts) == pytest.approx(100, abs=0.01), turn
        assert sum(y for _, y in pts) / len(pts) == pytest.approx(100, abs=0.01), turn


def test_each_blossoms_heart_is_centred_on_its_petals():
    for ident, d in flower_paths(100, 100, 50, 25):
        if ident.startswith('blossom heart') or ident.startswith('blossom centre'):
            pts = [tuple(map(float, xy.split(','))) for xy in re.findall(r'-?[\d.]+,-?[\d.]+', d)]
            assert sum(x for x, _ in pts) / len(pts) == pytest.approx(100, abs=0.01), ident
            assert sum(y for _, y in pts) / len(pts) == pytest.approx(100, abs=0.01), ident


def exposed_share(front, back, step=4):
    """The share of the back mass's grid points no front blossom covers, each blossom taken as the disc its petals
    fill but for the notches between their tips."""
    corners = [(x - r, y - r, x + r, y + r) for x, y, r, _ in front + back]
    x0, y0 = max(0, min(c[0] for c in corners)), max(0, min(c[1] for c in corners))
    x1, y1 = max(c[2] for c in corners), max(c[3] for c in corners)
    points = [(x, y) for y in range(int(y0), int(y1), step) for x in range(int(x0), int(x1), step)
              if any(math.hypot(x - bx, y - by) < br * blossom.PETAL_DISC for bx, by, br, _ in back)]
    exposed = [p for p in points
               if not any(math.hypot(p[0] - fx, p[1] - fy) < fr * blossom.PETAL_DISC for fx, fy, fr, _ in front)]
    return len(exposed) / len(points)


def test_the_back_mass_shows_only_in_slivers_between_the_blossoms():
    """The front blossoms overlap enough that the shaded mass behind them is never a plain area: in each clump, and
    in the whole crown they compose, little of it is left uncovered."""
    assert exposed_share(blossom.CROWN_LEFT, blossom.BACK_LEFT) <= blossom.EXPOSED
    assert exposed_share(blossom.CROWN_RIGHT, blossom.BACK_RIGHT) <= blossom.EXPOSED
    assert exposed_share(blossom.CROWN, blossom.BACK_CROWN) <= blossom.EXPOSED


def distance_to(polyline, p):
    best = math.inf
    for (ax, ay), (bx, by) in zip(polyline, polyline[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(ax + t * dx - p[0], ay + t * dy - p[1]))
    return best


def test_each_crotch_flares_from_one_limb_edge_round_to_the_next():
    """A flare starts FLARE along the first edge from the crotch's first corner and ends FLARE along the last edge
    from its last corner, so a curve with the corners as its handles leaves each edge along it."""
    for crotch in blossom.CROTCHES:
        start, corners, end = blossom.flare_points(crotch)
        first, last = blossom.edge(*crotch[0]), blossom.edge(*crotch[-1])
        assert distance_to(first, start) < 0.01, crotch
        assert distance_to(last, end) < 0.01, crotch
        assert math.dist(start, corners[0]) == pytest.approx(blossom.reach(crotch)), crotch
        assert math.dist(end, corners[-1]) == pytest.approx(blossom.reach(crotch)), crotch


def test_a_crotch_flares_no_further_than_the_width_of_the_narrowest_limb_it_joins():
    """The fillet under the fork is as small as the fork limb, so it never webs across the right limb's bend; the
    trunk's crotches keep the full flare."""
    for crotch in blossom.CROTCHES:
        narrowest = min(blossom.LIMBS[name][1][0] for name, _ in crotch)
        assert blossom.reach(crotch) == min(blossom.FLARE, 2 * narrowest), crotch
    assert blossom.reach((('fork limb', 'shade'), ('right limb', 'lit'))) < blossom.FLARE


def test_each_crotch_flare_reaches_out_of_the_limbs_it_joins():
    for crotch in blossom.CROTCHES:
        start, _, end = blossom.flare_points(crotch)
        for name, _ in crotch:
            if name != crotch[0][0]:
                assert not blossom.inside(name, start), crotch
            if name != crotch[-1][0]:
                assert not blossom.inside(name, end), crotch


def test_the_corners_where_the_low_limbs_leave_the_trunk_are_flared():
    joined = {frozenset(name for name, _ in crotch) for crotch in blossom.CROTCHES}
    assert frozenset({'trunk', 'left limb'}) in joined
    assert frozenset({'trunk', 'left limb', 'top left limb'}) in joined



def test_each_lit_strip_runs_down_the_side_of_its_limb_facing_the_light():
    """A limb rising up the sheet is lit down its right, one running right across it along its top: the lit edge is
    the one the light reaches, whichever way the limb runs."""
    for name in blossom.LIT:
        lit, shade = blossom.edge(name, 'lit'), blossom.edge(name, 'shade')
        toward = [(a[0] - b[0], a[1] - b[1]) for a, b in zip(lit, shade)]
        assert sum(x * blossom.LIGHT[0] + y * blossom.LIGHT[1] for x, y in toward) > 0, name


def test_the_right_limb_tapers_from_the_trunk_to_its_tip():
    _, widths = blossom.LIMBS['right limb']
    assert all(a > b for a, b in zip(widths, widths[1:]))


def test_the_right_limb_bends_instead_of_running_straight():
    points, _ = blossom.LIMBS['right limb']
    assert max(distance_to([points[0], points[-1]], p) for p in points[1:-1]) >= 8


def test_a_limb_forks_up_from_the_right_limb_toward_the_crown():
    forks = [name for name, (points, _) in blossom.LIMBS.items()
             if name != 'right limb' and blossom.inside('right limb', points[0]) and points[-1][1] < points[0][1] - 20]
    assert forks


def test_the_right_limb_grows_out_of_the_trunk_with_a_flare_above_and_below():
    sides = {dict(crotch)['right limb'] for crotch in blossom.CROTCHES
             if {name for name, _ in crotch} == {'trunk', 'right limb'}}
    assert sides == {'lit', 'shade'}


def test_each_crotch_flare_spans_sky_between_its_limbs_not_a_limb():
    """Where an edge leaves the other limb both ways, as the trunk's side does above and below the right limb, the
    flare takes the way on the crotch's own side: the chord from its start to its end crosses no limb it joins."""
    for crotch in blossom.CROTCHES:
        start, _, end = blossom.flare_points(crotch)
        middle = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        for name, _ in crotch:
            assert not blossom.inside(name, middle), (crotch, name)


def test_a_flare_is_in_shade_unless_every_edge_it_joins_is_lit():
    """The crotch under a limb carries its underside shadow round into the trunk; only the crotch above the right
    limb, between its lit top and the trunk's lit side, is in the bark's body."""
    for crotch in blossom.CROTCHES:
        lit = all(side == 'lit' for _, side in crotch)
        assert blossom.flare_fill(crotch) == blossom.BARK['body' if lit else 'shade'], crotch
    assert sum(all(side == 'lit' for _, side in crotch) for crotch in blossom.CROTCHES) == 1


def inner_shares(inner, points, widths):
    """A strip's inner edge as shares of the half width out from the limb's centre line."""
    return [math.dist(p, c) / w for p, c, w in zip(inner, points, widths)]


def strip_points(strip):
    return [tuple(map(float, v.split(','))) for v in re.findall(r'-?[\d.]+,-?[\d.]+', strip)]


def test_the_lit_strip_is_faceted_not_a_parallel_stripe():
    """The lit face's inner edge breaks at the limb's bends instead of running a constant share of the width."""
    points, widths = blossom.LIMBS['right limb']
    inner = strip_points(blossom.lit_strip(points, widths))[:len(points)]
    shares = inner_shares(inner, points, widths)
    assert max(shares) - min(shares) >= 0.15


def test_the_shade_strip_is_faceted_not_a_parallel_stripe():
    points, widths = blossom.LIMBS['right limb']
    inner = strip_points(blossom.shade_strip(points, widths))[len(points):][::-1]
    shares = inner_shares(inner, points, widths)
    assert max(shares) - min(shares) >= 0.15


def test_the_right_limb_is_warm_bark_like_the_trunk_not_the_crowns_shade():
    assert 'right limb' not in blossom.UPPER


def test_each_shade_strip_reaches_its_limbs_outline():
    """No body colour shows between the outline and the shade down a limb's shaded side."""
    for name in blossom.SHADED:
        strip = blossom.shade_strip(*blossom.LIMBS[name])
        points = [tuple(map(float, xy.split(','))) for xy in re.findall(r'-?[\d.]+,-?[\d.]+', strip)]
        outer = points[:len(blossom.LIMBS[name][0])]
        assert all(distance_to(blossom.edge(name, 'shade'), p) < 0.1 for p in outer), name


BLOSSOM_GROUPS = ('blossom crown left', 'blossom crown right') + tuple(tid.replace('-', ' ') for tid in blossom.CLUSTERS)


def blossom_colours():
    blossom.main()
    root, _ = cutting.load('plants/blossom.svg')
    for gid in BLOSSOM_GROUPS:
        for el in cutting.find_group(root, gid).iter():
            for attr in ('fill', 'stroke'):
                colour = el.get(attr)
                if colour and colour.startswith('#'):
                    yield gid, el.get('id'), colour


def test_the_blossoms_have_no_dark_line():
    """Every fill and stroke in the crowns and loose clusters is a light colour: the blossoms are edged by colour
    change alone, never a dark line."""
    for gid, ident, colour in blossom_colours():
        assert max(hexrgb(colour)) >= 180, (gid, ident, colour)


def test_each_blossom_is_edged_in_a_darker_pink():
    (r, g, b), body = hexrgb(blossom.PETAL['edge']), hexrgb(blossom.PETAL['body'])
    assert r > g and r > b
    assert sum((r, g, b)) < sum(body)


def test_the_back_mass_fills_each_blossoms_centre():
    """A blossom's petals start a little out from its centre, so the back mass, with no line under it, fills each
    centre in its own colour or a pinhole of sky shows through."""
    for x, y, r, turn in blossom.BACK_CROWN:
        subpaths = blossom.back_mass([(x, y, r, turn)]).split('Z')
        rings = [[tuple(map(float, xy.split(','))) for xy in re.findall(r'-?[\d.]+,-?[\d.]+', s)] for s in subpaths
                 if 'C' not in s and 'A' not in s]
        assert any(blossom.within(ring, (x, y)) for ring in rings if ring), (x, y)


# the Esme Terrace's outline style, as test_lantern_tree checks it: the bark's line a dark shade of its own warm
# brown, never near-black or navy, as thin as the Esme outlines
ESME_HUE_TOLERANCE = 40
ESME_LINE_WIDTHS = (2.0, 3.0)


ESME_VALUE_SHARE = (0.4, 0.8)
ESME_SATURATION = 0.45


def hsv(colour):
    r, g, b = (c / 255 for c in hexrgb(colour))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s, v


def not_near_black(colour):
    _, s, v = hsv(colour)
    return v >= 0.3 and s >= ESME_SATURATION


def dark_shade_of(line, fill):
    (lh, _, lv), (fh, _, fv) = hsv(line), hsv(fill)
    return (ESME_VALUE_SHARE[0] <= lv / fv <= ESME_VALUE_SHARE[1]
            and min(abs(lh - fh), 360 - abs(lh - fh)) <= ESME_HUE_TOLERANCE and not_near_black(line))


def test_the_bark_line_is_a_dark_shade_of_the_bark():
    assert dark_shade_of(blossom.BARK['line'], blossom.BARK['body'])
    assert dark_shade_of(blossom.BARK['line'], blossom.UPPER_BARK['body'])
    assert hsv(blossom.BARK['line'])[2] < hsv(blossom.BARK['shade'])[2]


def test_no_stroke_on_the_trunk_is_near_black():
    blossom.main()
    root, _ = cutting.load('plants/blossom.svg')
    for el in cutting.find_group(root, 'blossom trunk').iter():
        stroke = el.get('stroke')
        if stroke and stroke.startswith('#') and stroke != blossom.BARK['shade']:
            assert not_near_black(stroke), (el.get('id'), stroke)


def test_the_bark_outline_is_as_thin_as_esmes():
    assert ESME_LINE_WIDTHS[0] <= blossom.BARK_LINE <= ESME_LINE_WIDTHS[1]

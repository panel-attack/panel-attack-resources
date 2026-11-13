import math
import random
import xml.etree.ElementTree as ET

import pytest

from scene_export import cutting, svgtools, wind
from scenery import clouds, landscape
from plants import trees, trees_template
from EsmeTerrace import EsmeTerrace


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


@pytest.fixture(scope='module')
def built():
    """The terrace as the generators draw it; the scene-editor edits are tested in test_esme_placements."""
    return EsmeTerrace.generated()


@pytest.fixture(scope='module')
def edited():
    return EsmeTerrace.build()


def top(built, node_id):
    return next(n for n in built['drawables'] if n['id'] == node_id)


def group(built, gid):
    return next(n for n in walk(built['drawables']) if n['id'] == gid)


GROUND = ['sky', 'clouds', 'background', 'lake shimmer', 'far trees', 'town', 'near trees', 'rail end shrub', 'floor']


def test_objects_are_in_the_paintings_layer_order(edited):
    assert [n['id'] for n in edited['drawables']] == [g for g in GROUND if g != 'rail end shrub'] + [
        'rail', 'crystal planter', 'left urn', 'right urn', 'table set', 'corner bush']


def test_every_object_draws_its_shadow_then_its_template(edited):
    for obj in edited['drawables'][len(GROUND):]:
        assert [c['id'] for c in obj['children']][-2:] == [obj['id'] + ' shadow', obj['id'] + ' object']


# ---------------------------------------------------------------- the sky and the landscape

def test_the_clouds_are_a_group_of_one_ref_per_cloud(built):
    ids = [c['id'] for c in top(built, 'clouds')['children']]
    assert len(ids) == len(set(ids))
    assert all(c['ref'].startswith('scenery/clouds.json#') for c in top(built, 'clouds')['children'])


def test_the_terrace_sky_is_a_one_png_px_strip_stretched_across_the_canvas():
    from scenery import sky, sky_template
    strip = sky.parts()[0]
    assert (strip.box, strip.strip) == ((0, 0, 2, 1024), True)
    template = next(t for t in sky_template.build()['drawables'] if t['id'] == sky_template.TEMPLATE)
    assert (template['size'], template['pivot']) == ({'width': 1280}, 'topLeft')


def test_the_sky_has_no_wisps(built):
    assert 'wisps' not in {c['id'] for c in top(built, 'clouds')['children']}


def test_the_scene_clouds_voted_down_are_gone(built):
    ids = {c['id'] for c in top(built, 'clouds')['children']}
    assert not ids & {'cloud top left', 'cloud behind peak', 'cloud right edge'}


def test_a_second_set_of_clouds_as_big_as_the_first_waits_off_the_left_edge_to_drift_in(built):
    widths = {cid: cutting.length(part.box[2]) for cid, part in clouds.cut()}
    xs = [(c['overrides']['position']['x'], widths[c['id']]) for c in top(built, 'clouds')['children']]
    in_view = [x for x, w in xs if x + w > 0 and x < wind.SCENE_SIZE[0]]
    waiting = [x for x, w in xs if x + w <= 0]
    assert len(in_view) == len(waiting) == 9 and len(xs) == 18


def test_every_cloud_drifts(built):
    assert all(c['overrides'].get('animationTracks') for c in top(built, 'clouds')['children'])


def test_a_cloud_wraps_round_while_its_whole_image_is_out_of_sight(built):
    widths = {cid: part.box[2] for cid, part in clouds.cut()}
    for cloud in top(built, 'clouds')['children']:
        in_left = cloud['overrides']['animationTracks'][0]['steps'][1]['animateProperties']['x']
        assert in_left <= -cutting.length(widths[cloud['id']]) - wind.OUT_OF_SIGHT, cloud['id']


def test_a_round_4_cloud_is_its_voted_layout_placed_in_the_sky():
    places = {name: at for name, *_, at in clouds.places()}
    for name, seed in clouds.ROUND_4:
        laid = clouds.random_layout(random.Random(seed))
        assert clouds.layout_of(name) == clouds.placed(*laid, places[name]), name


def boxes(built):
    widths = {cid: part.box for cid, part in clouds.cut()}
    return [(c['id'], c['overrides']['position']['x'], c['overrides']['position']['y'], cutting.length(widths[c['id']][2]),
             cutting.length(widths[c['id']][3])) for c in top(built, 'clouds')['children']]


def test_clouds_side_by_side_at_one_depth_stay_apart_all_the_way_round_their_lap(built):
    lap = wind.CLOUD_LAP
    band = {name: i for i, names in enumerate(clouds.bands()) for name in names}
    for i, (a, ax, ay, aw, ah) in enumerate(boxes(built)):
        for b, bx, by, bw, bh in boxes(built)[i + 1:]:
            if band[a] == band[b] and ay < by + bh and by < ay + ah:
                gap = (bx - ax) % lap
                clear = clouds.CLOUD_GAP * min(aw, bw)
                assert aw + clear <= gap <= lap - bw - clear, (a, b)


def test_a_cloud_is_spaced_by_the_box_it_is_drawn_in():
    drawn = {cid: part.box for cid, part in clouds.cut()}
    for name, lobes, left, right, thick, seed, at in clouds.places():
        x0, y0, x1, y1 = clouds.reach(*clouds.placed(lobes, left, right, thick, at), seed)
        bx, by, bw, bh = drawn[name]
        assert x0 <= bx and bx + bw <= x1 and y0 <= by and by + bh <= y1, name
        assert bx - x0 < 6 and x1 - (bx + bw) < 6, name


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    return [order.index(i) for i in range(len(values))]


def test_the_biggest_clouds_stand_nearest_high_in_the_sky():
    laid = clouds.places()
    widths = ranks([right[0] - left[0] for _, _, left, right, *_ in laid])
    heights = ranks([at[1] for *_, at in laid])
    n = len(laid)
    spearman = 1 - 6 * sum((w - h) ** 2 for w, h in zip(widths, heights)) / (n * (n * n - 1))
    assert spearman < -0.8


def x_at(cloud, t):
    steps = cloud['overrides']['animationTracks'][0]['steps']
    t %= sum(s['durationSeconds'] for s in steps)
    x = cloud['overrides']['position']['x']
    for s in steps:
        to = s['animateProperties']['x']
        if t <= s['durationSeconds']:
            return x + (to - x) * t / s['durationSeconds']
        t -= s['durationSeconds']
        x = to
    return x


def test_about_as_many_clouds_stay_in_view_all_the_time(built):
    widths = {cid: cutting.length(part.box[2]) for cid, part in clouds.cut()}
    drifting = [c for c in top(built, 'clouds')['children']]
    for t in range(0, 3 * 3600, 10):
        seen = sum(1 for c in drifting if x_at(c, t) + widths[c['id']] > 0 and x_at(c, t) < wind.SCENE_SIZE[0])
        assert 8 <= seen <= 12, t


def test_the_clouds_at_one_depth_drift_together_so_they_stay_spread_out(built):
    speed = {}
    for c in top(built, 'clouds')['children']:
        steps = c['overrides']['animationTracks'][0]['steps']
        speed[c['id']] = (steps[0]['animateProperties']['x'] - c['overrides']['position']['x']) / steps[0][
            'durationSeconds']
    for band in clouds.bands():
        assert max(speed[n] for n in band) == pytest.approx(min(speed[n] for n in band)), band


def test_a_cloud_shrinks_and_hazes_most_near_the_horizon():
    assert clouds.depth(sum(clouds.CLOUD_DEPTH) / 2) < 0.4


def test_the_clouds_draw_from_the_horizon_up_so_nearer_ones_cover_further_ones(built):
    base = {name: at[1] for name, *_, at in clouds.places()}
    ids = [c for c, *_ in boxes(built)]
    assert [base[c] for c in ids] == sorted((base[c] for c in ids), reverse=True)


def test_a_cloud_further_back_by_the_horizon_is_drawn_smaller():
    lobes, left, right, thick = clouds.random_layout(random.Random(4032))
    near = clouds.sized(*clouds.placed(lobes, left, right, thick, (0, clouds.CLOUD_DEPTH[0])))
    far = clouds.sized(*clouds.placed(lobes, left, right, thick, (0, clouds.CLOUD_DEPTH[1])))
    span = lambda laid: laid[2][0] - laid[1][0]
    assert span(far) == pytest.approx(span(near) * clouds.CLOUD_FAR[0])


def test_a_cloud_further_back_is_hazed_toward_the_sky_behind_it():
    from common.painting import hexrgb
    from scenery import sky
    near, far = (clouds.colours(y) for y in clouds.CLOUD_DEPTH)
    behind = sky.colour_at(clouds.CLOUD_DEPTH[1])
    distance = lambda c: sum((a - b) ** 2 for a, b in zip(hexrgb(c), hexrgb(behind)))
    assert all(distance(f) < distance(n) for n, f in zip(near, far))
    assert near == (clouds.CLOUD_LINE, clouds.CLOUD_TOP, clouds.CLOUD_SHADE)


def random_layouts():
    return [clouds.random_layout(random.Random(seed)) for seed in range(300)]


def test_a_random_cloud_has_a_few_puffs():
    lo, hi = clouds.CLOUD_PUFFS
    assert {len(lobes) for lobes, *_ in random_layouts()} == set(range(lo, hi + 1))


def test_a_random_clouds_biggest_puff_stays_within_the_voted_size():
    lo, hi = clouds.CLOUD_PUFF_SIZE
    assert all(lo <= max(r for *_, r in lobes) <= hi for lobes, *_ in random_layouts())


def test_a_big_random_cloud_has_more_puffs_than_a_small_one():
    sizes = sorted((max(r for *_, r in lobes), len(lobes)) for lobes, *_ in random_layouts())
    third = len(sizes) // 3
    small, big = sizes[:third], sizes[-third:]
    assert sum(n for _, n in big) / third > sum(n for _, n in small) / third + 1.5


def test_a_random_clouds_biggest_puff_is_seldom_at_an_end():
    ends = [max(range(len(lobes)), key=lambda i: lobes[i][2]) in (0, len(lobes) - 1) for lobes, *_ in random_layouts()]
    assert 0 < sum(ends) / len(ends) < 0.25


def test_a_random_clouds_biggest_puff_leads_the_next_but_is_no_lone_ball():
    for lobes, *_ in random_layouts():
        first, second = sorted((r for *_, r in lobes), reverse=True)[:2]
        assert clouds.CLOUD_LEAD[0] <= first / second <= clouds.CLOUD_LEAD[1]


def test_a_random_clouds_tips_lie_either_side_of_its_puffs():
    for lobes, left, right, thick in random_layouts():
        assert left[0] < min(x for x, *_ in lobes) and right[0] > max(x for x, *_ in lobes) and thick > 0


def test_a_cloud_is_drawn_smaller_than_laid_out_shrinking_toward_the_middle_of_its_base():
    assert clouds.CLOUD_SIZE < 1
    for name, lobes, left, right, thick in clouds.layouts():
        mx, my = (left[0] + right[0]) / 2, (left[1] + right[1]) / 2
        k = clouds.CLOUD_SIZE * clouds.depth_size(my)
        small, (xl, yl), (xr, yr), small_thick = clouds.sized(lobes, left, right, thick)
        assert ((xl + xr) / 2, (yl + yr) / 2) == pytest.approx((mx, my)), name
        assert xr - xl == pytest.approx((right[0] - left[0]) * k), name
        assert small_thick == pytest.approx(thick * k), name
        for (cx, cy, r), (sx, sy, sr) in zip(lobes, small):
            assert (sx - mx, sy - my, sr) == pytest.approx(((cx - mx) * k, (cy - my) * k, r * k)), name


def test_a_cloud_whose_puffs_all_sit_on_its_underside_draws_no_empty_path():
    from common.painting import Svg
    lobes, left, right, thick = [(0, 212, 10), (20, 214, 10), (40, 212, 10)], (-20, 205), (60, 205), 4
    hidden, *_ = clouds.build(*clouds.sized(lobes, left, right, thick), random.Random(1))
    assert hidden == []
    svg = Svg()
    clouds.draw_cloud(svg, 'low cloud', lobes, left, right, thick, random.Random(1))
    assert not any(' d=""' in part for part in svg.parts)


def test_a_cloud_has_no_straight_edge_so_no_flat_base_and_no_cut_side():
    for cid, part in clouds.cut():
        for p in ET.fromstring(part.svg).iter('{%s}path' % svgtools.SVG_NS):
            x = y = None
            for cmd, nums in svgtools._segments(p.get('d')):
                if cmd == 'L' and x is not None:
                    assert math.hypot(nums[0] - x, nums[1] - y) < 4, cid
                if nums:
                    x, y = nums[-2], nums[-1]


def curls():
    for name, lobes, left, right, thick in clouds.layouts():
        hidden, top, row, tails = clouds.build(*clouds.sized(lobes, left, right, thick), random.Random(1))
        found = clouds.curl(top, hidden + tails, row, 0)
        if found:
            i, pts, _ = found
            yield name, top[i], hidden + tails + top[:i], top[i + 1:] + row, pts


def test_the_big_clouds_have_a_curl():
    assert 'cloud centre right' in {name for name, *_ in curls()}


def test_a_curl_starts_on_the_outline_of_its_puff():
    for name, puff, behind, after, pts in curls():
        x, y = pts[0]
        assert ((x - puff[0]) / puff[2]) ** 2 + ((y - puff[1]) / puff[3]) ** 2 == pytest.approx(1, abs=0.02), name
        assert not any(clouds.inside(x, y, o, 1.0) for o in behind + after), name


def test_a_curl_carries_its_puffs_edge_on_over_the_puff_behind():
    for name, puff, behind, after, pts in curls():
        x, y = pts[len(pts) // 8]
        assert any(clouds.inside(x, y, b, 1.0) for b in behind), name


def test_a_curl_lies_on_its_own_puff_with_nothing_drawn_over_it():
    for name, puff, behind, after, pts in curls():
        for x, y in pts:
            assert clouds.inside(x, y, puff, 1.02), name
            assert not any(clouds.inside(x, y, a, 1.0) for a in after), name


def test_the_landscape_image_leaves_out_the_sky_the_clouds_the_town_and_the_trees_beyond_the_rail():
    svg = landscape.cut()['background'].svg
    assert 'Mountains' in svg
    for gone in ('id="sky"', 'cloud top left', 'buildings', 'cypress', 'leafy clump', 'near woods',
                 'Flowering shrubs', 'lake below rail'):
        assert gone not in svg, gone


def test_the_landscapes_hills_are_bare_rolling_land_with_no_tree_crowns():
    assert 'crown' not in landscape.cut()['background'].svg


def test_the_snow_capped_peak_stands_right_of_centre():
    root = ET.fromstring(landscape.cut()['background'].svg)
    snow = next(p for p in root.iter('{%s}path' % svgtools.SVG_NS) if p.get('id') == 'snow')
    x0, y0, x1, y1 = svgtools.element_bbox(snow)
    assert (x0 + x1) / 2 > landscape.WIDTH * 0.6


# ---------------------------------------------------------------- the town and the trees beyond the rail

def tree_refs(nodes, prefix=''):
    return [n for n in walk(nodes) if n.get('ref', '').startswith(trees_template.OUTPUT + '#' + prefix)]


def test_each_house_is_its_own_template_placed_once(built):
    houses = group(built, 'buildings')['children']
    assert [h['id'] for h in houses] == ['far gable', 'far right house', 'cottage', 'red house', 'tall tower',
                                         'small tower', 'orange wing', 'manor']
    assert len({h['ref'] for h in houses}) == 8


def test_every_cypress_is_placed_from_a_few_shared_cypress_templates(built):
    cypresses = tree_refs([top(built, 'town'), top(built, 'near trees')], 'cypress')
    assert len(cypresses) == 18
    assert 3 <= len({c['ref'] for c in cypresses}) <= 5


def test_the_hazy_back_row_cypresses_use_hazy_templates(built):
    back = tree_refs(group(built, 'back row')['children'])
    assert back and all(c['ref'].endswith('-hazy') for c in back)
    near = tree_refs(group(built, 'feature cypresses')['children'])
    assert near and not any(c['ref'].endswith('-hazy') for c in near)


def test_the_leafy_clumps_among_the_houses_share_two_templates(built):
    clumps = tree_refs(group(built, 'trees among houses')['children'], 'leafy-clump')
    assert len(clumps) == 6
    assert {c['ref'].partition('#')[2] for c in clumps} == {'leafy-clump', 'leafy-clump-flowering'}


def test_a_hazy_cypress_of_any_shape_is_drawn_from_a_hazy_template():
    from common.painting import Svg
    svg = Svg()
    trees.placed_cypress(svg, 'stout hazy cypress', 0, -100, 20, 0, variant='hazy')
    assert 'data-template="cypress-hazy"' in svg.parts[0]


def test_no_tree_draws_its_template_larger_than_its_png(built):
    for n in tree_refs(built['drawables']):
        o = n['overrides']
        assert max(abs(o['xScale']), abs(o['yScale'])) <= 1.0 + 1e-9, n['id']


def markers():
    root = ET.parse(cutting.sheet_path('EsmeTerrace/background.svg')).getroot()
    return {g.get('id'): g for g in root.iter(cutting.NS + 'g') if g.get('data-template')}


def test_a_tree_stands_where_background_svg_draws_it(built):
    placed = markers()
    assert len(placed) == 24 + len(tree_refs([top(built, 'far trees')]))
    for n in tree_refs(built['drawables']):
        g = placed.pop(n['id'])
        assert n['ref'] == trees_template.OUTPUT + '#' + g.get('data-template')
        x, y = (float(v) for v in g.get('data-at').split(','))
        sx, sy = (float(v) for v in g.get('data-scale').split(','))
        o = n['overrides']
        assert cutting.sheet_point(o['position']) == pytest.approx((x, y), abs=0.6)
        assert (o['xScale'], o['yScale']) == pytest.approx((sx, sy), abs=1e-5)
    assert placed == {}


def test_background_svg_draws_each_tree_as_its_template():
    root = ET.parse(cutting.sheet_path('plants/trees.svg')).getroot()
    shapes = {g.get('data-template'): [p.get('d') for p in g.iter(cutting.NS + 'path')]
              for g in root.iter(cutting.NS + 'g') if g.get('data-template')}
    for tid, g in markers().items():
        assert [p.get('d') for p in g.iter(cutting.NS + 'path')] == shapes[g.get('data-template')], tid


def test_nothing_beyond_the_rail_covers_the_meadow_with_water():
    assert 'lake below rail' not in open(cutting.sheet_path('EsmeTerrace/background.svg')).read()


def test_the_near_woods_and_flowering_shrubs_are_their_own_images(built):
    near = {n['id']: n for n in group(built, 'near trees')['children']}
    for name in ('near woods left', 'near woods right', 'flowering shrubs'):
        assert 'filePath' in near[name], name


# ---------------------------------------------------------------- the woods on the lake's far shore

def tall(n):
    """How tall the ref draws its tree, in canvas px."""
    tid = n['ref'].partition('#')[2].removesuffix('-hazy').removesuffix('-farthest').removesuffix('-far').removesuffix('-bank')
    heights = {t[0]: t[2] for t in trees.CYPRESS_TEMPLATES + trees.CLUMP_TEMPLATES}
    return n['overrides']['yScale'] * heights[tid]


def foot(n):
    return cutting.sheet_point(n['overrides']['position'])


def far(built, name):
    return tree_refs(group(built, name)['children'])


def test_the_far_trees_are_all_refs_to_the_tree_templates(built):
    leaves = [n for n in walk([top(built, 'far trees')]) if not n.get('children')]
    assert leaves and leaves == tree_refs([top(built, 'far trees')])


def test_a_dense_band_of_trees_stands_along_the_far_waterline(built):
    waterline = next(bottom for name, _, bottom, *_ in landscape.HILLS if name == 'far hills')
    band = far(built, 'far shore trees')
    xs = sorted(foot(n)[0] for n in band)
    assert xs[0] < 450 and xs[-1] > 1150
    assert max(b - a for a, b in zip(xs, xs[1:])) < 40
    assert all(abs(foot(n)[1] - landscape.curve_y(waterline, foot(n)[0])) < 30 for n in band)


def test_the_band_mixes_pointed_cypresses_with_round_leafy_clumps(built):
    kinds = [n['ref'].partition('#')[2].startswith('cypress') for n in far(built, 'far shore trees')]
    assert 0.4 < sum(kinds) / len(kinds) < 0.8


def test_the_band_thickens_into_bigger_trees_on_the_banks_at_either_end(built):
    band = [tall(n) for n in far(built, 'far shore trees')]
    for side in ('left bank trees', 'right bank trees'):
        bank = far(built, side)
        assert len(bank) > 15, side
        assert max(tall(n) for n in bank) > max(band) * 1.3, side


def test_the_hill_crests_are_lined_with_tiny_hazy_trees(built):
    crest = far(built, 'far ridge trees')
    shore = far(built, 'far shore trees')
    assert len(crest) > 20
    assert max(tall(n) for n in crest) < sorted(tall(n) for n in shore)[len(shore) // 2]
    assert all(n['ref'].endswith('-farthest') for n in crest)


def test_a_bank_tree_further_up_the_slope_is_drawn_smaller_and_behind(built):
    for side in ('left bank trees', 'right bank trees'):
        ys = [foot(n)[1] for n in far(built, side)]
        assert ys == sorted(ys), side
        bank = [n for n in far(built, side) if 'foot' not in n['id'] and 'shrub' not in n['id']]
        xs = [foot(n)[0] for n in bank]
        outer_end = min(xs) if side.startswith('left') else max(xs)
        slope = [n for n in bank if abs(foot(n)[0] - outer_end) < (max(xs) - min(xs)) / 3]
        upper, lower = slope[:len(slope) // 3], slope[-len(slope) // 3:]
        assert sum(map(tall, upper)) / len(upper) < sum(map(tall, lower)) / len(lower) * 0.8, side


def far_kinds(built):
    refs = [n['ref'].partition('#')[2] for n in tree_refs([top(built, 'far trees')])]
    return [r for r in refs if r.startswith('cypress')], [r for r in refs if not r.startswith('cypress')]


def test_every_far_cypress_is_drawn_from_the_far_template_or_the_hazier_farthest_one(built):
    cypresses, _ = far_kinds(built)
    assert cypresses and all(r.endswith(('-far', '-farthest')) for r in cypresses)


def test_the_far_round_trees_come_in_several_shapes_all_in_the_leafy_clumps_green(built):
    _, clumps = far_kinds(built)
    assert len(set(clumps) - {'far-shrub'}) >= 3
    depth = {c[0]: c[3] for c in trees.CLUMP_TEMPLATES}
    assert {depth[c] for c in clumps} == {depth['leafy-clump']}


def test_the_far_cypresses_come_in_several_shapes(built):
    cypresses, _ = far_kinds(built)
    assert len({c for c in cypresses if c.endswith('-far')}) >= 3


def far_templates():
    return [t for t in trees.TEMPLATES if t.endswith(('-far', '-farthest')) or t.startswith('far-')]


@pytest.mark.parametrize('tid', far_templates())
def test_a_far_tree_casts_a_faint_flat_shadow_on_the_ground_straight_under_its_foot_as_from_an_overhead_sun(tid):
    import re
    from common.painting import Svg
    svg = Svg()
    trees.draw(svg, tid)
    shadow = next(p for p in svg.parts if p.startswith('<path'))
    assert 'foot shadow' in shadow
    opacity = float(re.search(r'fill-opacity="([^"]*)"', shadow).group(1))
    nums = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', re.search(r' d="([^"]*)"', shadow).group(1))]
    xs, ys = nums[0::2], nums[1::2]
    assert max(ys) <= 0 and max(ys) - min(ys) < (max(xs) - min(xs)) * 0.2
    assert abs(max(xs) + min(xs)) / 2 <= (max(xs) - min(xs)) * 0.05
    assert opacity <= 0.25


def template_colours(tid):
    from common.painting import Svg
    import re
    svg = Svg()
    trees.draw(svg, tid)
    text = ' '.join(svg.parts) + ' '.join(' '.join(k[:2]) for k in svg.grads)
    return re.findall(r'#[0-9a-f]{6}', text)


def distance_to_hills(tid):
    from common.painting import hexrgb
    blue = hexrgb(trees.FAR_TREE_HAZE[0])
    colours = template_colours(tid)
    return sum(sum((a - b) ** 2 for a, b in zip(hexrgb(c), blue)) ** 0.5 for c in colours) / len(colours)


def far_cypress_shapes():
    return [t.removesuffix('-far') for t in trees.TEMPLATES if t.startswith('cypress') and t.endswith('-far')]


@pytest.mark.parametrize('shape', far_cypress_shapes())
def test_a_far_cypress_is_nearer_the_far_hills_blue(shape):
    assert distance_to_hills(shape + '-far') < distance_to_hills(shape) * 0.75


@pytest.mark.parametrize('shape', far_cypress_shapes())
def test_a_farthest_cypress_is_nearer_the_far_hills_blue_again(shape):
    assert shape + '-farthest' in trees.TEMPLATES
    assert distance_to_hills(shape + '-farthest') < distance_to_hills(shape + '-far') * 0.75


def mean_colour(tid):
    from common.painting import hexrgb
    colours = [hexrgb(c) for c in template_colours(tid)]
    return [sum(c[i] for c in colours) / len(colours) for i in range(3)]


@pytest.mark.parametrize('side, hill, bank', [('left bank trees', 'left hill', 'left bank'),
                                              ('right bank trees', 'right hill', 'right bank')])
def test_a_bank_tree_stands_on_land_not_in_the_lake(built, side, hill, bank):
    lines = {name: bottom for name, _, bottom, *_ in landscape.HILLS}
    for n in far(built, side):
        x, y = foot(n)
        edge = lines[bank] if lines[bank][0][0] <= x <= lines[bank][-1][0] else lines[hill]
        assert y <= landscape.curve_y(edge, x) + 0.4, n['id']   # positions snap to half a unit, 0.6 sheet px


@pytest.mark.parametrize('side, outer_is_left', [('left bank trees', True), ('right bank trees', False)])
def test_a_banks_biggest_trees_stand_at_its_outer_end_away_from_the_lake(built, side, outer_is_left):
    bank = sorted(far(built, side), key=lambda n: foot(n)[0], reverse=not outer_is_left)
    xs = [foot(n)[0] for n in bank]
    third = abs(xs[-1] - xs[0]) / 3
    outer = [tall(n) for n in bank if abs(foot(n)[0] - xs[0]) < third]
    lake_end = [tall(n) for n in bank if abs(foot(n)[0] - xs[-1]) < third]
    assert max(lake_end) < max(outer) * 0.8


def test_the_bands_back_rows_are_hazier_than_its_front_row(built):
    waterline = next(bottom for name, _, bottom, *_ in landscape.HILLS if name == 'far hills')
    for n in far(built, 'far shore trees'):
        if n['ref'].partition('#')[2].startswith('cypress'):
            x, y = foot(n)
            assert n['ref'].endswith('-farthest') == (landscape.curve_y(waterline, x) - y > 8), n['id']


def test_the_crest_trees_stand_in_one_row_on_their_stands_ridge(built):
    from EsmeTerrace import background
    ridges = {name: top for name, top, *_ in landscape.HILLS}
    for n in far(built, 'far ridge trees'):
        x, y = foot(n)
        hill = next(h for x0, x1, h in background.FAR_CREST_STANDS if x0 <= x <= x1)
        assert 0 <= y - landscape.curve_y(ridges[hill], x) <= tall(n) * 0.3, n['id']


def test_the_hill_faces_behind_the_banks_are_wooded(built):
    slope = far(built, 'far slope trees')
    xs = sorted(foot(n)[0] for n in slope)
    for x0, x1 in [(30, 380), (1280, 1530)]:
        inside = [x0] + [x for x in xs if x0 < x < x1] + [x1]
        assert max(b - a for a, b in zip(inside, inside[1:])) < 30, (x0, x1)
    median = lambda ns: sorted(map(tall, ns))[len(ns) // 2]
    assert max(map(tall, far(built, 'far ridge trees'))) < median(slope) < median(far(built, 'far shore trees'))
    assert all(n['ref'].endswith('-farthest') for n in slope)


def test_the_hill_face_woods_stand_behind_the_band_and_the_banks(built):
    groups = [n['id'] for n in top(built, 'far trees')['children']]
    assert groups.index('far slope trees') < min(groups.index(g) for g in
                                                 ('far shore trees', 'left bank trees', 'right bank trees'))


@pytest.mark.parametrize('side', ['left bank trees', 'right bank trees'])
def test_a_banks_biggest_trees_are_all_cypresses(built, side):
    biggest = sorted(far(built, side), key=tall)[-8:]
    assert all('#cypress' in n['ref'] for n in biggest)


@pytest.mark.parametrize('side', ['left bank trees', 'right bank trees'])
def test_a_big_bank_cypress_has_a_round_tree_in_front_of_its_foot(built, side):
    from EsmeTerrace import background
    bank = far(built, side)
    big = [i for i, n in enumerate(bank) if '#cypress' in n['ref'] and tall(n) > background.FAR_BANK_DARK_FROM]
    assert big
    for i in big:
        n = bank[i]
        x, y = foot(n)
        assert any('#far-clump' in m['ref'] and abs(foot(m)[0] - x) < tall(n) * 0.6
                   and foot(m)[1] >= y for m in bank[i + 1:]), n['id']


BANKS = [('left bank trees', 'left hill', 'left bank'), ('right bank trees', 'right hill', 'right bank')]


def bank_span(x, hill, bank):
    """Where a bank's woods may stand at x: from under the hill's crest down to the water."""
    from EsmeTerrace import background
    lines = {name: (top, bottom) for name, top, bottom, *_ in landscape.HILLS}
    shore = lines[bank][1] if lines[bank][1][0][0] <= x <= lines[bank][1][-1][0] else lines[hill][1]
    lower = landscape.curve_y(shore, x)
    return min(landscape.curve_y(lines[hill][0], x) + background.FAR_BANK_FROM, lower), lower


@pytest.mark.parametrize('side, hill, bank', BANKS)
def test_most_bank_trees_stand_in_the_lower_half_of_their_bank_toward_the_water(built, side, hill, bank):
    standing = [n for n in far(built, side) if 'shrub' not in n['id']]
    low = 0
    for n in standing:
        x, y = foot(n)
        upper, lower = bank_span(x, hill, bank)
        low += y - upper >= (lower - upper) / 2
    assert low >= 0.65 * len(standing)


@pytest.mark.parametrize('side, hill, bank', BANKS)
def test_low_shrubs_line_a_banks_shore(built, side, hill, bank):
    shrubs = [n for n in far(built, side) if n['ref'].endswith('#far-shrub')]
    assert len(shrubs) >= 8
    for n in shrubs:
        x, y = foot(n)
        assert -0.4 <= bank_span(x, hill, bank)[1] - y <= 6, n['id']     # positions snap to half a unit


# ---------------------------------------------------------------- the lake

def test_the_lake_shimmer_lies_over_the_landscape_and_under_the_far_trees(built):
    order = [n['id'] for n in built['drawables']]
    assert order.index('background') < order.index('lake shimmer') < order.index('far trees')


def test_the_lake_shimmers_two_sets_of_glints_twinkling_in_turn(built):
    a, b = top(built, 'lake shimmer')['children']
    assert [n['ref'].partition('#')[2] for n in (a, b)] == ['lake-shimmer-a', 'lake-shimmer-b']
    assert a['overrides'].get('alpha', 1) > b['overrides']['alpha']
    assert a['overrides']['animationTracks'] and b['overrides']['animationTracks']

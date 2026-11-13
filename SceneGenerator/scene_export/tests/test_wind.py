import json
import os

import pytest

from scene_export import wind


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


SIZES = {'EsmeTerrace/parts/clouds/cloud-high': (200, 60), 'EsmeTerrace/parts/clouds/cloud-low': (100, 30)}


def scene_doc():
    return {'drawables': [
        {'id': 'sky', 'filePath': 'EsmeTerrace/parts/sky/sky', 'position': {'x': 0, 'y': 0}},
        {'id': 'clouds', 'children': [
            {'id': 'cloud high', 'filePath': 'EsmeTerrace/parts/clouds/cloud-high', 'position': {'x': 40, 'y': -33}},
            {'id': 'cloud low', 'filePath': 'EsmeTerrace/parts/clouds/cloud-low', 'position': {'x': 500, 'y': 133}}]},
        {'id': 'urn', 'children': [
            {'id': 'urn body', 'filePath': 'EsmeTerrace/parts/urn/body', 'position': {'x': 10, 'y': 10}},
            {'id': 'urn bush edge 1', 'ref': 'plants/branches.json#branch-small-1',
             'overrides': {'position': {'x': 20, 'y': 30}, 'rotation': 0.5, 'xScale': 0.7, 'yScale': 0.7}},
            {'id': 'urn bush face 2', 'ref': 'plants/branches.json#rosette-small-1',
             'overrides': {'position': {'x': 25, 'y': 35}, 'xScale': 0.7, 'yScale': 0.7}},
            {'id': 'urn bush flower 1', 'ref': 'plants/flowers.json#flower-12-36',
             'overrides': {'position': {'x': 22, 'y': 28}, 'rotation': -0.2}},
            {'id': 'far bush edge 1', 'ref': 'plants/branches.json#branch-small-1',
             'overrides': {'position': {'x': 1167, 'y': 30}, 'rotation': 0.5}}]}]}


def windy():
    """The scene_doc as a generator writes it: each cloud drifting, then every plant swayed."""
    doc = scene_doc()
    for cloud in by_id(doc, 'clouds')['children']:
        cloud['animationTracks'] = wind.drift(cloud, SIZES[cloud['filePath']][0])
    return {'drawables': wind.swayed(doc['drawables'])}


def by_id(doc, node_id):
    return next(n for n in walk(doc['drawables']) if n['id'] == node_id)


def track(node):
    [t] = (node['overrides'] if 'ref' in node else node)['animationTracks']
    return t


def rotations(node):
    return [s['animateProperties']['rotation'] for s in track(node)['steps']]


def leans(node):
    """The plant's rotation away from its own at each step, as a share of its kind's sway."""
    base = node['overrides'].get('rotation', 0)
    return [(r - base) / wind.sway_of(node) for r in rotations(node)]


# ---------------------------------------------------------------- clouds

def cloud_xs(node):
    return [s['animateProperties']['x'] for s in track(node)['steps']]


def test_a_cloud_drifts_off_the_right_edge_comes_back_in_from_the_left_and_returns_to_its_place():
    cloud = by_id(windy(), 'cloud high')
    assert track(cloud)['loopTrack'] is True
    off_right, in_left, home = cloud_xs(cloud)
    assert off_right >= wind.SCENE_SIZE[0]
    assert in_left <= -SIZES['EsmeTerrace/parts/clouds/cloud-high'][0]
    assert home == 40


def test_a_cloud_comes_round_again_after_two_screen_widths_so_a_second_set_waits_off_screen():
    off_right, in_left, home = cloud_xs(by_id(windy(), 'cloud high'))
    assert off_right - in_left == 2 * wind.SCENE_SIZE[0]


def test_a_cloud_jumps_back_to_the_left_at_once_while_out_of_sight():
    steps = track(by_id(windy(), 'cloud high'))['steps']
    assert 0 < steps[1]['durationSeconds'] < 0.01


def test_a_cloud_moves_at_a_steady_speed():
    cloud = by_id(windy(), 'cloud high')
    off_right, in_left, home = cloud_xs(cloud)
    steps = track(cloud)['steps']
    assert all(s['easeType'] == 'linear' for s in steps)
    assert (off_right - 40) / steps[0]['durationSeconds'] == pytest.approx((home - in_left) / steps[2]['durationSeconds'])


def speed(cloud):
    off_right, _, _ = cloud_xs(cloud)
    return (off_right - cloud['position']['x']) / track(cloud)['steps'][0]['durationSeconds']


def test_a_far_cloud_near_the_horizon_crawls_compared_with_a_high_one_in_front():
    doc = windy()
    assert speed(by_id(doc, 'cloud high')) > 6 * speed(by_id(doc, 'cloud low'))


# ---------------------------------------------------------------- plants

PLANTS = ('urn bush edge 1', 'urn bush face 2', 'urn bush flower 1', 'far bush edge 1')


def test_every_plant_moves_with_the_same_wind():
    doc = windy()
    first = leans(by_id(doc, PLANTS[0]))
    for plant in PLANTS[1:]:
        assert leans(by_id(doc, plant)) == pytest.approx(first)


def test_the_wind_gusts_stronger_and_softer():
    lean = [abs(x) for x in leans(by_id(windy(), PLANTS[0]))]
    assert max(lean) > 0.9
    assert min(x for x in lean if x > 0) < 0.3


def test_the_plants_bend_downwind_more_than_back_in_a_gust():
    lean = leans(by_id(windy(), PLANTS[0]))
    assert sum(lean) > 0


def test_every_plant_takes_the_same_time_to_go_through_the_wind_so_they_stay_together():
    doc = windy()
    for plant in PLANTS:
        steps = track(by_id(doc, plant))['steps']
        total = sum(s['durationSeconds'] + s.get('delaySeconds', 0) for s in steps)
        assert total == pytest.approx(wind.WIND_SECONDS)


def test_the_wind_reaches_plants_on_the_left_first():
    doc = windy()
    near, far = (track(by_id(doc, p))['steps'][0].get('delaySeconds', 0) for p in ('urn bush edge 1', 'far bush edge 1'))
    assert far - near > 0.5 * wind.WAVE_SECONDS


def test_a_plant_ends_the_wind_at_its_own_rotation_so_the_loop_doesnt_jump():
    doc = windy()
    for plant in PLANTS:
        node = by_id(doc, plant)
        assert rotations(node)[-1] == node['overrides'].get('rotation', 0)
        assert track(node)['loopTrack'] is True


def test_flowers_move_more_than_branches_and_rosettes_least():
    doc = windy()
    flower, branch, rosette = (wind.sway_of(by_id(doc, p)) for p in ('urn bush flower 1', 'urn bush edge 1',
                                                                     'urn bush face 2'))
    assert flower > branch > rosette


def test_the_strongest_gust_stays_subtle():
    doc = windy()
    for plant in PLANTS:
        node = by_id(doc, plant)
        base = node['overrides'].get('rotation', 0)
        assert max(abs(r - base) for r in rotations(node)) <= 0.08


def test_the_wind_is_the_same_every_export():
    assert windy() == windy()


def test_images_that_arent_clouds_or_plants_hold_still():
    doc = windy()
    for node_id in ('sky', 'urn body', 'urn', 'clouds'):
        assert 'animationTracks' not in by_id(doc, node_id)


def test_a_ref_node_only_gets_the_keys_the_loader_allows():
    for n in walk(windy()['drawables']):
        if 'ref' in n:
            assert set(n) <= {'id', 'ref', 'overrides', 'templateOnly'}


@pytest.mark.parametrize('overrides', [{'rotation': 0.5}, {'position': {'y': 30}, 'rotation': 0.5}])
def test_a_plant_placed_at_the_left_edge_with_no_x_override_gets_the_wind_first(overrides):
    node = {'id': 'edge bush 1', 'ref': 'plants/branches.json#branch-small-1', 'overrides': overrides}
    [track] = wind.sway(node)
    assert track['steps'][0]['delaySeconds'] <= wind.WAVE_JITTER


def test_a_plant_can_sway_after_the_delay_it_was_given():
    node = {'id': 'urn bush 1', 'ref': 'plants/branches.json#branch-small-1', 'overrides': {'position': {'x': 900}}}
    [track] = wind.sway(node, delay=0.25)
    steps = track['steps']
    assert steps[0]['delaySeconds'] == 0.25
    assert sum(s['durationSeconds'] for s in steps) + 0.25 == pytest.approx(sum(s for s, _ in wind.WIND))


def test_swaying_leaves_the_nodes_alone():
    doc = scene_doc()
    wind.swayed(doc['drawables'])
    assert doc == scene_doc()


# ---------------------------------------------------------------- the lake

def twinkling(start_bright):
    node = {'id': 'glints', 'ref': 'scenery/landscape.json#lake-shimmer-a', 'overrides': {'position': {'x': 0, 'y': 220}}}
    node['overrides'].update(wind.twinkle(node['overrides'], start_bright))
    return node['overrides']


def alphas(overrides):
    track = next(t for t in overrides['animationTracks'] if 'alpha' in t['steps'][0]['animateProperties'])
    return [overrides.get('alpha', 1)] + [s['animateProperties']['alpha'] for s in track['steps']]


def test_a_set_of_glints_fades_down_and_back_up_and_loops_where_it_started():
    a = alphas(twinkling(True))
    assert a[0] == a[-1] == 1 and min(a) < 0.4


def test_the_two_sets_of_glints_twinkle_in_turn():
    a, b = alphas(twinkling(True)), alphas(twinkling(False))
    assert all(abs((x + y) - (a[0] + b[0])) < 1e-9 for x, y in zip(a, b))
    assert b[0] < 0.4


def test_the_glints_ripple_a_little_sideways_and_come_back():
    o = twinkling(True)
    track = next(t for t in o['animationTracks'] if 'x' in t['steps'][0]['animateProperties'])
    xs = [s['animateProperties']['x'] for s in track['steps']]
    assert xs[-1] == o['position']['x'] and 0 < max(abs(x - o['position']['x']) for x in xs) <= 3

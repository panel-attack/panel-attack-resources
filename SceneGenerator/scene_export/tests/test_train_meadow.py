import MainMenu
from EsmeTerrace import EsmeTerrace
from TrainMeadow import TrainMeadow
from scene_export import cutting, wind
from scenery import sky, sky_template
from structures import train


def nodes():
    return list(cutting.walk(TrainMeadow.build()['drawables']))


def node(suffix):
    return next(n for n in nodes() if n['id'].endswith(suffix))


def tracks(n):
    return n.get('animationTracks', []) + n.get('overrides', {}).get('animationTracks', [])


def test_the_main_menu_shows_the_train_meadow():
    assert MainMenu.SCENE_NAME == 'TrainMeadow'


def test_the_train_slides_only_across_on_its_rails_its_shape_never_changing():
    crossing = node('crossing train')
    assert crossing['overrides']['position']['y'] == train.RAIL_Y / 2
    animated = {p for t in tracks(crossing) for s in t['steps'] for p in s['animateProperties']}
    assert animated == {'x'}


def test_the_train_enters_wholly_off_the_left_and_leaves_wholly_off_the_right():
    crossing = node('crossing train')
    start = crossing['overrides']['position']['x']
    end = tracks(crossing)[0]['steps'][0]['animateProperties']['x']
    assert start + TrainMeadow.TRAIN_LENGTH / 2 <= 0
    assert end >= 768


def test_the_train_slides_at_the_speed_its_wheels_turn():
    crossing = node('crossing train')
    step = tracks(crossing)[0]['steps'][0]
    distance = step['animateProperties']['x'] - crossing['overrides']['position']['x']
    assert abs(distance * 2 / step['durationSeconds'] - train.TRAIN_SPEED) < 0.5


def test_the_lanterns_and_banner_swing():
    hangers = [n for n in nodes() if n.get('ref', '').split('#')[-1] in TrainMeadow.HANGER_TEMPLATES]
    assert len(hangers) == 2 and all(tracks(n) for n in hangers)


def test_the_lanterns_and_banner_rest_hanging_straight_down_and_swing_out_from_there():
    for n in (n for n in nodes() if n.get('ref', '').split('#')[-1] in TrainMeadow.HANGER_TEMPLATES):
        assert n['overrides'].get('rotation', 0) == 0
        steps = tracks(n)[0]['steps']
        assert steps[-1]['animateProperties']['rotation'] == 0


def test_every_swing_names_a_hanger_of_the_lantern_tree():
    assert set(TrainMeadow.HANGER_SWING) == set(TrainMeadow.HANGER_TEMPLATES)


def test_every_foreground_flower_sways_and_no_rock_does():
    placed = [n for n in nodes() if 'meadow_flowers.json#' in n.get('ref', '')]
    flowers = [n for n in placed if '#flower-' in n['ref']]
    rocks = [n for n in placed if '#rock-' in n['ref']]
    assert flowers and rocks
    assert all(tracks(n) for n in flowers) and not any(tracks(n) for n in rocks)


def test_the_near_bushes_stand_behind_both_trees():
    order = [n['id'] for n in TrainMeadow.build()['drawables']]
    bushes = order.index('meadow bushes')
    assert bushes < order.index('meadow blossom tree') and bushes < order.index('meadow lantern tree')


# ---------------------------------------------------------------- the sky and the clouds

def terrace_nodes():
    return list(cutting.walk(EsmeTerrace.build()['drawables']))


def cloud_nodes(all_nodes):
    return [n for n in all_nodes if 'clouds.json#' in n.get('ref', '')]


def test_the_meadow_shares_the_terraces_sky_image():
    terrace_sky = next(n for n in terrace_nodes() if n['id'] == 'sky')
    assert node('meadow sky')['ref'] == terrace_sky['ref'] == sky_template.OUTPUT + '#' + sky_template.TEMPLATE


def test_no_sky_is_drawn_for_the_meadow_alone():
    assert not hasattr(sky_template, 'TRAIN_MEADOW_TEMPLATE')
    assert [t['id'] for t in sky_template.build()['drawables']] == [sky_template.TEMPLATE, sky_template.DAY_VALLEY_TEMPLATE]
    assert len(sky.parts()) == 2


def test_the_clouds_are_the_terraces_clouds_in_other_places():
    terrace = {n['ref']: n['overrides']['position'] for n in cloud_nodes(terrace_nodes())}
    meadow = cloud_nodes(nodes())
    assert len(meadow) >= 6
    for n in meadow:
        assert n['ref'] in terrace
        assert n['overrides']['position'] != terrace[n['ref']]


def test_the_clouds_vary_in_opacity():
    alphas = {n['overrides'].get('alpha', 1) for n in cloud_nodes(nodes())}
    assert len(alphas) > 1 and all(0 < a <= 1 for a in alphas)


def test_every_cloud_drifts_in_the_wind():
    for n in cloud_nodes(nodes()):
        assert all(set(s['animateProperties']) == {'x'} for t in tracks(n) for s in t['steps'])


def test_clouds_wait_off_the_left_edge_to_follow_the_ones_in_view():
    xs = [n['overrides']['position']['x'] for n in cloud_nodes(nodes())]
    assert any(x < -200 for x in xs) and any(0 < x < wind.SCENE_SIZE[0] for x in xs)

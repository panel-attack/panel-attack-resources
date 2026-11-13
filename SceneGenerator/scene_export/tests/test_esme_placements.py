from EsmeTerrace import placements
from scene_export import wind

BODY = {'id': 'urn body', 'filePath': 'furniture/parts/urn/body', 'position': {'x': 100, 'y': 200}}
BACK_BUSH = {'id': 'urn back bush', 'filePath': 'furniture/parts/urn/back-bush', 'position': {'x': 90, 'y': 180}}
CUT_LEAF = {'id': 'urn leaf 1', 'ref': 'plants/leaves.json#leaf-a', 'overrides': {'position': {'x': 1, 'y': 2}}}
LEAF = {'id': 'urn leaf 1', 'ref': 'plants/leaves.json#leaf-a', 'x': 110, 'y': 190, 'rotation': 0.1, 'xScale': -0.5,
        'yScale': 0.5, 'delay': 0.3}


def test_an_objects_plants_are_drawn_where_the_placements_put_them_swaying_after_their_delay():
    body, leaf = placements.planted([BODY, CUT_LEAF], [{'image': 'urn body'}, LEAF])
    assert body == BODY
    expected = {'id': 'urn leaf 1', 'ref': 'plants/leaves.json#leaf-a',
                'overrides': {'position': {'x': 110, 'y': 190}, 'rotation': 0.1, 'xScale': -0.5, 'yScale': 0.5}}
    assert leaf == dict(expected, overrides=dict(expected['overrides'],
                                                 animationTracks=wind.sway(expected, delay=0.3)))


def test_an_image_placed_at_x_y_is_drawn_there():
    [body] = placements.planted([BODY], [{'image': 'urn body', 'x': 106, 'y': 199}])
    assert body == dict(BODY, position={'x': 106, 'y': 199})


def test_an_image_the_placements_leave_out_is_not_drawn():
    assert placements.planted([BODY, BACK_BUSH], [{'image': 'urn body'}]) == [BODY]


def test_a_plant_placed_without_a_delay_stands_still():
    still = {k: v for k, v in LEAF.items() if k != 'delay'}
    [leaf] = placements.planted([BODY], [still])
    assert 'animationTracks' not in leaf['overrides']


def scene():
    return [{'id': 'clouds', 'children': [
                {'id': 'cloud', 'ref': 'c.json#cloud', 'overrides': {
                    'position': {'x': 10, 'y': 5},
                    'animationTracks': [{'steps': [{'durationSeconds': 9, 'animateProperties': {'x': 400}}]}]}}]},
            {'id': 'trees', 'children': [{'id': 'tree', 'ref': 't.json#tree', 'overrides': {'position': {'x': 1, 'y': 2},
                                                                                           'xScale': 1.2}},
                                         {'id': 'tree 2', 'ref': 't.json#tree', 'overrides': {'position': {'x': 3}}}]}]


def cloud(nodes):
    return nodes[0]['children'][0]['overrides']


def test_placing_a_node_sets_its_overrides_and_leaves_its_tracks():
    out = placements.placed(scene(), {'clouds': {'cloud': {'position': {'x': 50, 'y': 7}}},
                                      'trees': {'tree': {'position': {'x': 4, 'y': 5}, 'xScale': 1, 'yScale': 0.9}}})
    assert cloud(out) == dict(cloud(scene()), position={'x': 50, 'y': 7})
    assert out[1]['children'][0]['overrides'] == {'position': {'x': 4, 'y': 5}, 'xScale': 1, 'yScale': 0.9}


def test_moving_a_node_moves_its_tracks_with_it():
    out = placements.moved(scene(), {'clouds': {'cloud': {'x': 50, 'y': 7}}})
    assert cloud(out)['position'] == {'x': 50, 'y': 7}
    assert cloud(out)['animationTracks'][0]['steps'][0]['animateProperties'] == {'x': 440}


def test_a_node_left_out_is_not_drawn():
    out = placements.without(scene(), [['trees', 'tree 2']])
    assert [n['id'] for n in out[1]['children']] == ['tree']


def test_a_node_added_is_drawn_where_it_was_added():
    rosette = {'id': 'rosette', 'ref': 'plants/branches.json#rosette', 'overrides': {'position': {'x': 1, 'y': 2}}}
    out = placements.added(scene(), [{'under': ['trees'], 'at': 1, 'node': rosette}])
    assert [n['id'] for n in out[1]['children']] == ['tree', 'rosette', 'tree 2']


def test_editing_leaves_the_scene_it_was_given_alone():
    nodes = scene()
    placements.moved(placements.placed(nodes, {'clouds': {'cloud': {'position': {'x': 50}}}}), {})
    placements.without(nodes, [['trees', 'tree']])
    assert nodes == scene()


# ---------------------------------------------------------------- the terrace

def walk(nodes, path=()):
    for n in nodes:
        yield path + (n.get('id'),), n
        yield from walk(n.get('children', []), path + (n.get('id'),))


def test_each_planted_object_draws_its_images_and_plants_as_placed():
    from furniture import planters_template
    from plants import bushes_template
    templates = {t['id']: t for m in (planters_template, bushes_template) for t in m.build()['drawables']}
    names = dict(planters_template.TEMPLATES, **bushes_template.TEMPLATES)
    for obj, items in placements.load()['objects'].items():
        drawn = [n['id'] for n in templates[names[obj]]['children']]
        assert drawn == [i.get('image') or i['id'] for i in items], obj


def test_the_terrace_draws_nothing_it_leaves_out_and_what_was_added():
    from EsmeTerrace import EsmeTerrace
    drawn = dict(walk(EsmeTerrace.build()['drawables']))
    data = placements.load()
    assert not [p for p in data['left out'] if tuple(p) in drawn]
    for a in data['added']:
        assert tuple(a['under']) + (a['node']['id'],) in drawn

import pytest

from scene_export import game


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


def scene_doc():
    return {'drawables': [
        {'id': 'floor', 'filePath': 'EsmeTerrace/parts/floor/floor', 'position': {'x': 0, 'y': 320}},
        {'id': 'urn', 'children': [
            {'id': 'urn object', 'ref': 'furniture/planters.json#left-urn', 'overrides': {'position': {'x': 10, 'y': 10}}},
            {'id': 'urn shadow', 'filePath': 'EsmeTerrace/parts/urn/shadow', 'position': {'x': 8, 'y': 30}}]}]}


def test_every_image_path_in_the_theme_copy_is_inside_the_themes_scenes_folder():
    doc = game.theme_file(scene_doc())
    paths = [n['filePath'] for n in walk(doc['drawables']) if 'filePath' in n]
    assert paths == ['scenes/EsmeTerrace/parts/floor/floor', 'scenes/EsmeTerrace/parts/urn/shadow']


@pytest.mark.parametrize('ref, want', [
    ('furniture/planters.json#left-urn', 'scenes/furniture/planters.json#left-urn'),
    ('EsmeTerrace/EsmeTerrace.json', 'scenes/EsmeTerrace/EsmeTerrace.json'),
    ('leaf-broad-1', 'leaf-broad-1'),
])
def test_a_file_ref_in_the_theme_copy_is_from_the_theme_folder_like_image_paths(ref, want):
    doc = game.theme_file({'drawables': [{'id': 'x', 'ref': ref}]})
    assert doc['drawables'][0]['ref'] == want


def test_making_the_theme_copy_leaves_the_generators_doc_alone():
    doc = scene_doc()
    game.theme_file(doc)
    assert doc == scene_doc()


# ---------------------------------------------------------------- the screen

@pytest.mark.parametrize('flag, want', [('loopTrack', 'loop'), ('yoyo', 'yoyo')])
def test_the_theme_copy_repeats_tracks_the_way_the_game_reads_them(flag, want):
    doc = {'drawables': [{'id': 'cloud', 'animationTracks': [{flag: True, 'steps': []}]}]}

    track = game.theme_file(doc)['drawables'][0]['animationTracks'][0]

    assert track == {'repeat': want, 'steps': []}


def test_the_theme_copy_repeats_tracks_placed_by_overrides():
    doc = {'drawables': [{'id': 'cloud', 'ref': 'scenery/clouds.json#cloud-mid',
                          'overrides': {'animationTracks': [{'loopTrack': True, 'steps': []}]}}]}

    track = game.theme_file(doc)['drawables'][0]['overrides']['animationTracks'][0]

    assert track == {'repeat': 'loop', 'steps': []}


def test_the_theme_copy_writes_numbers_with_at_most_four_decimals_like_the_scene_editor():
    doc = {'drawables': [{'id': 'leaf', 'ref': 'plants/leaves.json#leaf-a', 'overrides': {
        'rotation': 0.27759247291569733, 'xScale': 0.5,
        'animationTracks': [{'loopTrack': True, 'steps': [
            {'durationSeconds': 618.3333333333337, 'delaySeconds': 0.12345678, 'animateProperties': {'x': 1286.66666667}},
            {'durationSeconds': 2, 'animateProperties': {'rotation': 1.0000000000000002}}]}]}}]}

    overrides = game.theme_file(doc)['drawables'][0]['overrides']
    first, second = overrides['animationTracks'][0]['steps']

    assert overrides['rotation'] == 0.2776 and overrides['xScale'] == 0.5
    assert first == {'durationSeconds': 618.3333, 'delaySeconds': 0.1235, 'animateProperties': {'x': 1286.6667}}
    assert second['animateProperties']['rotation'] == 1 and isinstance(second['animateProperties']['rotation'], int)

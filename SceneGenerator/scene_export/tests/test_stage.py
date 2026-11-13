import json
import os

import pytest

from scene_export import game, stage

SCENE = {'drawables': [
    {'id': 'sky', 'ref': 'scenery/sky.json#sky-a', 'overrides': {'position': {'y': -66.66666}}},
    {'id': 'bush', 'ref': 'plants/bushes.json#bush'},
    {'id': 'floor', 'filePath': 'S/parts/floor', 'animationTracks': [{'loopTrack': True, 'steps': []}]}]}
DOCS = {
    'S/S.json': SCENE,
    'scenery/sky.json': {'drawables': [{'id': 'sky-a', 'filePath': 'scenery/parts/sky/a', 'templateOnly': True},
                                       {'id': 'sky-b', 'filePath': 'scenery/parts/sky/b', 'templateOnly': True}]},
    'plants/bushes.json': {'drawables': [{'id': 'bush', 'templateOnly': True, 'children': [
        {'id': 'bush leaf', 'ref': 'plants/leaves.json#leaf'}]}]},
    'plants/leaves.json': {'drawables': [{'id': 'leaf', 'filePath': 'plants/parts/leaf', 'templateOnly': True},
                                         {'id': 'unused', 'filePath': 'plants/parts/other', 'templateOnly': True}]},
    'plants/trees.json': {'drawables': [{'id': 'oak', 'filePath': 'plants/parts/oak', 'templateOnly': True}]},
}


def test_the_stage_background_is_one_canvas_container_holding_the_scene():
    background = stage.files(DOCS, 'S/S.json')['background.json']
    [canvas] = background['drawables']
    assert canvas['size'] == {'width': game.CANVAS[0], 'height': game.CANVAS[1]}
    assert [c['id'] for c in canvas['children']] == ['sky', 'bush', 'floor']
    game.check_root(background, 'S')


def test_the_stage_draws_its_images_and_refs_from_the_stage_folder():
    floor = stage.files(DOCS, 'S/S.json')['background.json']['drawables'][0]['children'][2]
    assert floor['filePath'] == 'S/parts/floor'
    assert stage.files(DOCS, 'S/S.json')['plants/bushes.json']['drawables'][0]['children'][0]['ref'] == \
        'plants/leaves.json#leaf'


def test_the_stage_reads_like_a_theme_file():
    floor = stage.files(DOCS, 'S/S.json')['background.json']['drawables'][0]['children'][2]
    assert floor['animationTracks'] == [{'repeat': 'loop', 'steps': []}]
    sky = stage.files(DOCS, 'S/S.json')['background.json']['drawables'][0]['children'][0]
    assert sky['overrides']['position'] == {'y': -66.6667}


def test_the_stage_holds_only_the_templates_its_scene_draws():
    out = stage.files(DOCS, 'S/S.json')
    assert sorted(out) == ['background.json', 'plants/bushes.json', 'plants/leaves.json', 'scenery/sky.json']
    assert [t['id'] for t in out['scenery/sky.json']['drawables']] == ['sky-a']
    assert [t['id'] for t in out['plants/leaves.json']['drawables']] == ['leaf']


def test_the_stage_folder_gets_its_files_and_the_pngs_it_draws(tmp_path):
    pngs = tmp_path / 'scenes'
    for p in ('S/parts/floor', 'scenery/parts/sky/a', 'scenery/parts/sky/b', 'plants/parts/leaf'):
        os.makedirs(pngs / os.path.dirname(p), exist_ok=True)
        (pngs / (p + '@2x.png')).write_bytes(p.encode())
    out = tmp_path / 'Esme'
    stage.write(DOCS, 'S/S.json', str(out), str(pngs))
    written = sorted(os.path.relpath(os.path.join(f, n), out) for f, _, ns in os.walk(out) for n in ns)
    assert written == ['S/parts/floor@2x.png', 'background.json', 'plants/bushes.json', 'plants/leaves.json',
                       'plants/parts/leaf@2x.png', 'scenery/parts/sky/a@2x.png', 'scenery/sky.json']
    assert (out / 'plants/parts/leaf@2x.png').read_bytes() == b'plants/parts/leaf'
    assert json.loads((out / 'background.json').read_text())['drawables'][0]['id'] == 'canvas'


def test_a_stage_missing_a_png_it_draws_is_refused_naming_it(tmp_path):
    with pytest.raises(SystemExit, match='plants/parts/leaf'):
        stage.write(DOCS, 'S/S.json', str(tmp_path / 'Esme'), str(tmp_path / 'none'))


def test_the_stage_command_refuses_a_scene_layout_doesnt_make_naming_the_ones_it_does(tmp_path):
    from scene_export import __main__
    with pytest.raises(SystemExit, match='EsmeTerrace/EsmeTerrace.json'):
        __main__.main(['stage', 'Nope/Nope.json', str(tmp_path)])


# ---------------------------------------------------------------- the theme

MENU_DOCS = {**DOCS, 'M.json': game.canvas([{'id': 'scene', 'ref': 'S/S.json'}]),
             'Other/Other.json': {'drawables': [{'id': 'oak', 'ref': 'plants/trees.json#oak'}]}}


def test_the_theme_holds_only_the_files_its_main_menu_draws():
    assert sorted(stage.theme(MENU_DOCS, 'M.json')) == ['M.json', 'S/S.json', 'plants/bushes.json',
                                                         'plants/leaves.json', 'scenery/sky.json']


def test_the_theme_holds_only_the_templates_its_main_menu_draws():
    assert [t['id'] for t in stage.theme(MENU_DOCS, 'M.json')['plants/leaves.json']['drawables']] == ['leaf']


def test_the_theme_draws_its_images_and_refs_from_its_scenes_folder():
    out = stage.theme(MENU_DOCS, 'M.json')
    assert out['M.json']['drawables'][0]['children'][0]['ref'] == 'scenes/S/S.json'
    assert out['S/S.json']['drawables'][2]['filePath'] == 'scenes/S/parts/floor'


def test_layout_writes_the_theme_and_the_pngs_it_draws_from_the_renders(tmp_path):
    from scene_export import layout, store
    renders = tmp_path / 'renders'
    for p in ('S/parts/floor', 'scenery/parts/sky/a', 'scenery/parts/sky/b', 'plants/parts/leaf', 'plants/parts/oak'):
        os.makedirs(renders / os.path.dirname(p), exist_ok=True)
        (renders / (p + '@2x.png')).write_bytes(p.encode())
    scenes = tmp_path / 'scenes'

    layout.write_theme(MENU_DOCS, 'M.json', store.Store(str(scenes)), str(renders))

    written = sorted(os.path.relpath(os.path.join(f, n), scenes) for f, _, ns in os.walk(scenes) for n in ns
                     if not n.startswith('.'))
    assert written == ['M.json', 'S/S.json', 'S/parts/floor@2x.png', 'plants/bushes.json', 'plants/leaves.json',
                       'plants/parts/leaf@2x.png', 'scenery/parts/sky/a@2x.png', 'scenery/sky.json']

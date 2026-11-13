import json
import os

import pytest

from scene_export import store


@pytest.fixture
def scenes(tmp_path):
    return store.Store(str(tmp_path), clock=lambda: '20261023-101500')


def read(path):
    with open(path, 'rb') as f:
        return f.read()


def manifest(scenes):
    with open(os.path.join(scenes.root, '.manifest.json')) as f:
        return json.load(f)


def test_a_new_file_is_written_and_recorded_in_the_manifest(scenes):
    path = os.path.join(scenes.root, 'EsmeTerrace', 'EsmeTerrace.json')
    assert scenes.write(path, b'{}') == 'written'
    assert read(path) == b'{}'
    assert manifest(scenes) == {'EsmeTerrace/EsmeTerrace.json': store.sha256(b'{}')}


def test_rewriting_the_same_bytes_leaves_the_file_and_makes_no_backup(scenes):
    path = os.path.join(scenes.root, 'a.json')
    scenes.write(path, b'1')
    assert scenes.write(path, b'1') == 'unchanged'
    assert not os.path.exists(os.path.join(scenes.root, '.backup'))


def test_replacing_a_generated_file_moves_the_old_one_to_the_backup_folder(scenes):
    path = os.path.join(scenes.root, 'shared', 'parts', 'foliage', 'leaf@2x.png')
    scenes.write(path, b'old')
    assert scenes.write(path, b'new') == 'written'
    backup = os.path.join(scenes.root, '.backup', 'shared', 'parts', 'foliage', 'leaf@2x-20261023-101500.png')
    assert read(backup) == b'old'
    assert read(path) == b'new'
    assert manifest(scenes)['shared/parts/foliage/leaf@2x.png'] == store.sha256(b'new')


def test_a_second_backup_in_the_same_second_keeps_the_first(scenes):
    path = os.path.join(scenes.root, 'a.json')
    scenes.write(path, b'1')
    scenes.write(path, b'2')
    scenes.write(path, b'3')
    backups = sorted(os.listdir(os.path.join(scenes.root, '.backup')))
    assert len(backups) == 2
    assert {read(os.path.join(scenes.root, '.backup', b)) for b in backups} == {b'1', b'2'}


def test_a_file_edited_since_generation_is_skipped(scenes):
    path = os.path.join(scenes.root, 'a.json')
    scenes.write(path, b'generated')
    with open(path, 'wb') as f:
        f.write(b'edited by hand')
    assert scenes.write(path, b'regenerated') == 'skipped'
    assert read(path) == b'edited by hand'
    assert scenes.skipped == ['a.json']


def test_a_file_the_generator_never_wrote_is_skipped(scenes):
    path = os.path.join(scenes.root, 'a.json')
    with open(path, 'wb') as f:
        f.write(b'drawn by hand')
    assert scenes.write(path, b'generated') == 'skipped'
    assert read(path) == b'drawn by hand'


def test_force_replaces_an_edited_file_after_backing_it_up(tmp_path):
    scenes = store.Store(str(tmp_path), force=['a.json'], clock=lambda: '20261023-101500')
    path = os.path.join(scenes.root, 'a.json')
    scenes.write(path, b'generated')
    with open(path, 'wb') as f:
        f.write(b'edited')
    assert scenes.write(path, b'regenerated') == 'written'
    assert read(path) == b'regenerated'
    assert read(os.path.join(scenes.root, '.backup', 'a-20261023-101500.json')) == b'edited'


def test_force_accepts_an_absolute_path(tmp_path):
    path = os.path.join(str(tmp_path), 'x', 'a.json')
    scenes = store.Store(str(tmp_path), force=[path], clock=lambda: '20261023-101500')
    os.makedirs(os.path.dirname(path))
    with open(path, 'wb') as f:
        f.write(b'hand')
    assert scenes.write(path, b'gen') == 'written'


def test_install_moves_a_rendered_file_into_place(scenes, tmp_path):
    rendered = os.path.join(str(tmp_path), 'render.png')
    with open(rendered, 'wb') as f:
        f.write(b'png')
    path = os.path.join(scenes.root, 'p@2x.png')
    assert scenes.install(rendered, path) == 'written'
    assert read(path) == b'png'
    assert manifest(scenes)['p@2x.png'] == store.sha256(b'png')


def test_paths_outside_the_scenes_folder_are_refused(scenes, tmp_path):
    with pytest.raises(ValueError):
        scenes.write(os.path.join(str(tmp_path), '..', 'escape.json'), b'x')


def test_edited_lists_generated_files_whose_hash_changed(scenes):
    a = os.path.join(scenes.root, 'a.json')
    b = os.path.join(scenes.root, 'b.json')
    scenes.write(a, b'1')
    scenes.write(b, b'2')
    with open(b, 'wb') as f:
        f.write(b'changed')
    assert scenes.edited() == ['b.json']


def test_protected_tells_before_rendering_whether_a_write_would_be_skipped(tmp_path):
    scenes = store.Store(str(tmp_path), force=['c.png'])
    a, b, c, d = (os.path.join(scenes.root, n) for n in ('a.png', 'b.png', 'c.png', 'd.png'))
    scenes.write(a, b'gen')
    for p in (b, c):
        with open(p, 'wb') as f:
            f.write(b'hand')
    assert [scenes.protected(p) for p in (a, b, c, d)] == [False, True, False, False]


@pytest.fixture
def game(tmp_path):
    return store.Store(str(tmp_path / 'scenes'), state=str(tmp_path / 'generator'), clock=lambda: '20261023-101500')


def test_a_store_with_a_state_folder_keeps_its_manifest_there(game, tmp_path):
    game.write(os.path.join(game.root, 'a.json'), b'1')
    assert json.load(open(tmp_path / 'generator' / '.manifest.json')) == {'a.json': store.sha256(b'1')}
    assert not os.path.exists(os.path.join(game.root, '.manifest.json'))


def test_a_store_with_a_state_folder_keeps_its_backups_there(game, tmp_path):
    path = os.path.join(game.root, 'E', 'a.json')
    game.write(path, b'1')
    game.write(path, b'2')
    assert read(tmp_path / 'generator' / '.backup' / 'E' / 'a-20261023-101500.json') == b'1'
    assert sorted(os.listdir(game.root)) == ['E']


def test_replace_writes_a_new_file(game):
    path = os.path.join(game.root, 'plants', 'branches.json')
    assert game.replace(path, b'1') == 'written'
    assert read(path) == b'1'


def test_replace_leaves_a_file_with_the_same_bytes_and_makes_no_backup(game, tmp_path):
    path = os.path.join(game.root, 'a.json')
    game.replace(path, b'1')
    assert game.replace(path, b'1') == 'unchanged'
    assert not os.path.exists(tmp_path / 'generator' / '.backup')


def test_replace_backs_up_a_file_with_other_bytes_before_writing(game, tmp_path):
    path = os.path.join(game.root, 'plants', 'branches.json')
    os.makedirs(os.path.dirname(path))
    with open(path, 'wb') as f:
        f.write(b'edited in the editor')
    assert game.replace(path, b'generated') == 'replaced'
    assert read(path) == b'generated'
    assert read(tmp_path / 'generator' / '.backup' / 'plants' / 'branches-20261023-101500.json') == b'edited in the editor'

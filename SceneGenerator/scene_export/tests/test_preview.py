import json

from scene_export import preview


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc))


def test_a_file_ref_is_read_from_the_root_folder_like_image_paths(tmp_path):
    write(tmp_path / 'scenes/plants/leaves.json', {'drawables': [{'id': 'leaf', 'templateOnly': True, 'filePath': 'x'}]})
    write(tmp_path / 'scenes/Esme/Esme.json', {'drawables': [{'id': 'a', 'ref': 'scenes/plants/leaves.json#leaf'}]})
    scene = preview.Scene(str(tmp_path / 'scenes/Esme/Esme.json'), str(tmp_path))
    assert scene.doc['drawables'][0]['filePath'] == 'x'


def test_a_scene_previews_from_its_theme_folder_when_no_root_is_given(tmp_path):
    write(tmp_path / 'scenes/plants/leaves.json', {'drawables': [{'id': 'leaf', 'templateOnly': True}]})
    write(tmp_path / 'scenes/Esme/Esme.json', {'drawables': [{'id': 'a', 'ref': 'scenes/plants/leaves.json#leaf'}]})
    assert preview.render(str(tmp_path / 'scenes/Esme/Esme.json'), size=(4, 4)).size == (4, 4)

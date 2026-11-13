import os

import pytest

import scene_export
from scene_export import BUILD, GENERATOR, cutting, export


def test_a_sheet_is_drawn_under_build_at_its_generators_path():
    assert cutting.sheet_path('plants/trees.svg') == os.path.join(BUILD, 'sheets', 'plants', 'trees.svg')


def test_no_sheet_is_drawn_outside_build():
    outside = [os.path.join(folder, n) for folder, _, names in os.walk(GENERATOR)
               if not (folder + os.sep).startswith(BUILD + os.sep) for n in names if n.endswith('.svg')]
    assert outside == []


def test_pixelmator_opens_a_file_under_build():
    assert export.SLOT == os.path.join(BUILD, 'pixelmator', 'import.svg')


def test_an_unset_folder_variable_names_a_folder_under_build(monkeypatch):
    monkeypatch.delenv('SCENE_REFERENCES', raising=False)
    assert scene_export.folder_from('SCENE_REFERENCES') == os.path.join(BUILD, 'SCENE_REFERENCES is unset')


def test_a_missing_folder_stops_naming_its_variable(tmp_path):
    with pytest.raises(SystemExit, match='SCENE_GAME_THEME'):
        scene_export.required(str(tmp_path / 'missing'), 'SCENE_GAME_THEME')

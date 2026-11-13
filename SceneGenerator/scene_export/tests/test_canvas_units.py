import pytest

from scene_export import cutting, wind
from scene_export.cutting import Part

CROP = (720 - 1024 * 5 / 6) / 2


def test_a_sheet_point_lands_on_the_canvas_with_the_scenes_crop():
    assert cutting.point(0, 0) == {'x': 0, 'y': -66.5}
    assert cutting.point(1536, 1024) == {'x': 1280, 'y': 786.5}


def test_a_sheet_point_snaps_to_half_a_unit():
    assert cutting.point(3, 81) == {'x': 2.5, 'y': 1}


def test_a_sheet_length_is_five_sixths_of_a_unit_a_pixel():
    assert cutting.length(6) == 5


def test_an_image_is_placed_with_its_top_left_on_a_whole_unit():
    node = cutting.image_node('floor', Part('x/floor', '', (100, 300, 10, 10)))
    assert node['position'] == {'x': 83, 'y': 183}


def test_a_half_unit_top_left_rounds_up():
    assert cutting.corner(3, 100)['x'] == 3


def test_an_objects_template_is_drawn_from_a_whole_unit():
    children = [cutting.image_node('urn body', Part('x/body', '', (100, 300, 10, 10))),
                {'id': 'leaf', 'ref': 'f.json#leaf', 'overrides': {'position': cutting.point(130, 310)}}]
    template = cutting.object_template('urn', children)
    ref = cutting.object_ref('urn object', 'f.json', 'urn', children)
    assert ref['overrides']['position'] == {'x': 83, 'y': 183}
    assert template['children'][0]['position'] == {'x': 0, 'y': 0}
    assert template['children'][1]['overrides']['position'] == {'x': 25.5, 'y': 8.5}


def test_the_wind_blows_across_the_canvas():
    assert wind.SCENE_SIZE == (1280, 720)


def test_a_clouds_lap_is_two_canvas_widths():
    track, = wind.drift({'position': {'x': 100, 'y': 0}}, 50, speed=10)
    off_right, back, home = (s['animateProperties']['x'] for s in track['steps'])
    assert (off_right, off_right - back, home) == (1280 + wind.OUT_OF_SIGHT, 2560, 100)

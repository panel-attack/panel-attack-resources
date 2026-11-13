import json
import os

import pytest
from PIL import Image

from scene_export import REFERENCES
from structures import houses_reference as H
from scenery import town_reference

NAMES = ['far gable', 'far right house', 'cottage', 'red house', 'tall tower', 'small tower', 'orange wing', 'manor']

pytestmark = pytest.mark.skipif(not os.path.isdir(REFERENCES), reason='SCENE_REFERENCES names no folder')


def points(face):
    if face[2] == 'ellipse':
        cx, cy, rx, ry = face[3]
        return [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    return face[2]


def test_the_town_is_the_eight_houses_of_the_houses_reference_back_to_front():
    assert [h['name'] for h in H.HOUSES] == NAMES


def test_a_house_lands_on_the_stage_at_the_shared_scale_plus_its_own_offset():
    house = H.HOUSES[0]
    (x, y), (dx, dy) = house['faces'][0][2][0], house['offset']
    staged = H.stage_building(house)
    assert staged['faces'][0][2][0] == pytest.approx((x * H.SCALE + dx, y * H.SCALE + dy))


def test_every_face_and_window_is_inside_its_houses_stage_box():
    for house in H.HOUSES:
        x0, y0, x1, y1 = H.stage_box(house)
        staged = H.stage_building(house)
        for face in staged['faces']:
            for x, y in points(face):
                assert x0 <= x <= x1 and y0 <= y <= y1, (house['name'], face[0])
        for wx0, wy0, wx1, wy1 in staged['windows']:
            assert x0 <= wx0 < wx1 <= x1 and y0 <= wy0 < wy1 <= y1, house['name']


def test_every_tone_a_house_uses_has_a_fill():
    for house in H.HOUSES:
        for face in house['faces']:
            assert face[1] in H.TONES or face[1] in town_reference.TONES, (house['name'], face[1])


def test_the_houses_in_one_cluster_share_one_offset_so_they_overlap_as_in_the_reference():
    offsets = {h['name']: h['offset'] for h in H.HOUSES}
    assert offsets['manor'] == offsets['orange wing'] == offsets['tall tower'] == offsets['small tower']


@pytest.mark.parametrize('name', ['tall tower', 'small tower', 'orange wing', 'manor'])
def test_a_cluster_houses_walls_run_down_to_the_terrace_rails_foot_so_they_show_between_its_balusters(name):
    rail_foot = 706     # stage px, the rail's foot behind the small tower, off EsmeTerrace's rail@2x.png
    staged = H.stage_building(next(h for h in H.HOUSES if h['name'] == name))
    walls = [face for face in staged['faces'] if face[0].startswith('wall')]
    assert walls and all(max(y for _, y in face[2]) >= rail_foot for face in walls)


def test_each_house_has_a_reference_crop_and_json(tmp_path):
    H.write_reference(str(tmp_path))
    assert Image.open(tmp_path / 'source.png').size == Image.open(H.SOURCE).size
    for house in H.HOUSES:
        slug = H.slug(house['name'])
        with open(tmp_path / (slug + '.json')) as f:
            doc = json.load(f)
        assert doc['name'] == house['name'] and doc['slug'] == slug and doc['source'] == 'source.png'
        assert doc['scale'] == H.SCALE
        assert doc['stage_box'] == pytest.approx(list(H.stage_box(house)))
        assert doc['source_box'] == pytest.approx(list(H.source_box(house)))
        assert [f['name'] for f in doc['faces']] == [f[0] for f in house['faces']]
        x0, y0, x1, y1 = doc['stage_box']
        crop = Image.open(tmp_path / (slug + '.png'))
        assert crop.size == (round(x1 - x0), round(y1 - y0))


def test_the_reference_folder_holds_the_written_files():
    folder = os.path.join(REFERENCES, 'structures', 'houses')
    for house in H.HOUSES:
        slug = H.slug(house['name'])
        assert os.path.exists(os.path.join(folder, slug + '.png')), slug
        assert os.path.exists(os.path.join(folder, slug + '.json')), slug

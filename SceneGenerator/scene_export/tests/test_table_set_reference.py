import json
import os

import pytest
from PIL import Image

from scene_export import REFERENCES
from furniture import table_set_reference as T

pytestmark = pytest.mark.skipif(not os.path.isdir(REFERENCES), reason='SCENE_REFERENCES names no folder')


@pytest.fixture(scope='module')
def written(tmp_path_factory):
    out = tmp_path_factory.mktemp('table-set')
    source = os.path.join(REFERENCES, 'furniture', 'table-set', 'source.png')
    T.generate(source, str(out))
    return str(out)


SLUGS = ['table-set'] + [T.slug(n) for n in T.PIECES]


def read(folder, slug):
    with open(os.path.join(folder, slug + '.json')) as f:
        return json.load(f)


def test_the_reference_maps_onto_the_stage_by_one_scale_and_offset():
    x, y = T.to_stage((100, 200))
    assert (x, y) == pytest.approx((T.OFFSET[0] + 100 * T.SCALE, T.OFFSET[1] + 200 * T.SCALE))


def test_the_table_axis_lands_on_the_floor_point_table_py_draws_it_on():
    from furniture import table_set
    x, _ = T.to_stage((T.TABLE_AXIS_X, 0))
    assert x == pytest.approx(table_set.TABLE_SCREEN[0], abs=1)


def test_generate_writes_the_source_and_a_png_and_json_for_the_set_and_each_piece(written):
    names = set(os.listdir(written))
    assert 'source.png' in names
    for slug in SLUGS:
        assert slug + '.png' in names and slug + '.json' in names


def test_a_piece_json_says_where_its_crop_came_from_and_where_it_goes(written):
    for slug in SLUGS:
        doc = read(written, slug)
        assert {'name', 'slug', 'source', 'source_box', 'stage_box', 'scale'} <= set(doc)
        assert doc['slug'] == slug and doc['source'] == 'source.png' and doc['scale'] == T.SCALE
        x0, y0, x1, y1 = doc['source_box']
        assert doc['stage_box'] == pytest.approx(list(T.to_stage((x0, y0)) + T.to_stage((x1, y1))), abs=0.01)


def test_a_piece_png_is_its_crop_resampled_to_its_stage_box(written):
    for slug in SLUGS:
        x0, y0, x1, y1 = read(written, slug)['stage_box']
        assert Image.open(os.path.join(written, slug + '.png')).size == (round(x1 - x0), round(y1 - y0))


def test_landmarks_are_written_in_stage_px(written):
    doc = read(written, 'table')
    top = T.PIECES['table']['rings']['marble']
    ring = doc['rings']['marble']
    assert (ring['cx'], ring['cy']) == pytest.approx(T.to_stage((top['cx'], top['cy'])))
    assert (ring['a'], ring['b']) == pytest.approx((top['a'] * T.SCALE, top['b'] * T.SCALE))
    crest = T.PIECES['chair front left']['points']['crest top']
    assert read(written, 'chair-front-left')['points']['crest top'] == pytest.approx(list(T.to_stage(crest)))


def test_every_chair_has_its_crest_cushion_and_visible_feet():
    for name, piece in T.PIECES.items():
        if name.startswith('chair'):
            assert 'crest top' in piece['points'] and 'cushion' in piece['boxes'] and piece['feet']


def test_a_box_side_hidden_behind_another_piece_stays_unknown_on_the_stage():
    x0, y0, x1, y1 = T.stage_landmarks({'boxes': {'cushion': (None, 10.0, 20.0, 30.0)}})['boxes']['cushion']
    assert x0 is None and (y0, x1, y1) == pytest.approx((T.to_stage((0, 10))[1],) + T.to_stage((20, 30)))


def test_each_cushion_side_hidden_behind_a_chair_back_is_left_unknown():
    hidden = {'chair back left': 0, 'chair front left': 0, 'chair back right': 2, 'chair front right': 2}
    for name, side in hidden.items():
        assert T.PIECES[name]['boxes']['cushion'][side] is None

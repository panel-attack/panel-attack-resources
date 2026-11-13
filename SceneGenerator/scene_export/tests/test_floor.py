import colorsys
import math

import numpy as np
import pytest

from EsmeTerrace import floor


@pytest.fixture(scope='module')
def fields():
    rim_centre, rim_radius = floor.terrace_in_plan()
    return floor.field_cells(math.hypot(*rim_centre) + rim_radius)


@pytest.fixture(scope='module')
def groups():
    return dict(floor.floor_groups())


@pytest.mark.parametrize('field', ['inner tiles', 'outer tiles'])
def test_every_tile_in_a_field_is_as_deep_as_the_others_wherever_it_lies_round_the_circle(fields, field):
    depths = {round(outer - inner, 6) for inner, outer, _, _ in fields[field]}
    assert len(depths) == 1


@pytest.mark.parametrize('field', ['inner tiles', 'outer tiles'])
def test_every_tile_in_a_field_is_about_as_long_as_the_others_wherever_it_lies_round_the_circle(fields, field):
    lengths = [(a1 - a0) * (inner + outer) / 2 for inner, outer, a0, a1 in fields[field]]
    assert max(lengths) < 1.25 * min(lengths)


INLAYS = ['inner gold tiles', 'outer gold tiles', 'ray gold tiles']


@pytest.fixture(scope='module')
def gold():
    rim_centre, rim_radius = floor.terrace_in_plan()
    return floor.gold_cells(math.hypot(*rim_centre) + rim_radius, rim_radius)


def test_the_gold_tiles_sit_where_the_stars_and_ray_diamonds_were(gold):
    assert [len(gold[g]) for g in INLAYS] == [4, 3, 4]


@pytest.mark.parametrize('inlay, ring', [('inner gold tiles', floor.CREAM_RING), ('outer gold tiles', floor.OUTER_RING)])
def test_a_gold_tile_in_a_cream_ring_is_shaped_like_a_turquoise_tile_as_deep_as_the_ring(gold, inlay, ring):
    for inner, outer, a0, a1 in gold[inlay]:
        assert (inner, outer) == ring
        assert (a1 - a0) * (inner + outer) / 2 == pytest.approx(floor.TILE_ASPECT * (outer - inner))


@pytest.mark.parametrize('inlay', INLAYS)
def test_a_gold_tile_is_drawn_like_a_near_turquoise_tile_with_its_sheen_and_glint(groups, gold, inlay):
    drawn = [(role, pts) for _, role, pts in groups[inlay]]
    expected = []
    for cell in gold[inlay]:
        tile, sheen = floor.tile_shapes(cell, 0)
        expected += [('gold tile', tile)] + ([('gold sheen', sheen)] if sheen and len(sheen) >= 3 else [])
        expected += [('gold glint', strip) for strip in floor.glint(floor.tile_outline(*cell, floor.GLINT['inset']), 0)]
    assert len(drawn) == len(expected)
    for (role, pts), (want_role, want) in zip(drawn, expected):
        assert role == want_role
        assert np.allclose(pts, floor.clip_polygon(want, floor_region()))


def floor_region():
    rim_centre, rim_radius = floor.terrace_in_plan()
    return floor.clip_region(rim_centre, rim_radius, (floor.medallion_centre()[2] - floor.NEAR_Z) * 100)


def hls(colour):
    return colorsys.rgb_to_hls(*(int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)))


@pytest.mark.parametrize('end', [0, 1])
def test_the_gold_is_the_cream_stones_colour_made_more_vibrant(end):
    cream = hls(floor.GRADIENTS[floor.COLOURS['cream'][0]][end])
    gold = hls(floor.GRADIENTS[floor.COLOURS['gold tile'][0]][end])
    assert abs(gold[0] - cream[0]) * 360 < 8
    assert gold[2] >= cream[2] and gold[1] < cream[1]


def test_each_cream_ray_is_laid_as_slabs_no_deeper_than_a_course_beside_it(groups):
    slabs = groups['rays']
    assert len(slabs) > 4
    for _, role, pts in slabs:
        radii = [math.hypot(*p) for p in pts]
        assert role == 'cream'
        assert max(radii) - min(radii) <= floor.OUTER_COURSE_DEPTH + 1, pts

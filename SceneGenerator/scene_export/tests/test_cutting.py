import copy
import xml.etree.ElementTree as ET

import pytest

from scene_export import cutting, preview, templates as T


# ---------------------------------------------------------------- placement maths

def test_an_image_node_sits_at_its_parts_box_in_scene_units():
    part = cutting.Part('furniture/parts/left-urn/body', '<svg/>', (300, 410, 220, 340))
    assert cutting.image_node('left urn body', part) == {'id': 'left urn body', 'filePath': part.path,
                                                         'position': {'x': 150, 'y': 205}}


def test_an_image_ref_places_its_template_where_the_part_sits():
    part = cutting.Part('scenery/parts/clouds/wisps', '<svg/>', (61, 40, 300, 90))
    assert cutting.image_ref('wisps', 'scenery/clouds.json', 'cloud-wisps', part) == {
        'id': 'wisps', 'ref': 'scenery/clouds.json#cloud-wisps', 'overrides': {'position': {'x': 30.5, 'y': 20}}}


def test_a_marker_ref_places_its_template_where_the_generator_drew_it():
    g = ET.Element('g', {'id': 'cypress 1', 'data-template': 'cypress', 'data-at': '101,64.5', 'data-scale': '-1,0.75'})
    assert cutting.marker_ref(g, 'plants/trees.json') == {
        'id': 'cypress 1', 'ref': 'plants/trees.json#cypress',
        'overrides': {'position': {'x': 50.5, 'y': 32.25}, 'xScale': -1, 'yScale': 0.75}}


def stem_overrides(pl):
    """A foliage ref's overrides as placed_foliage writes them, with the anchor its template has."""
    return {'position': {'x': pl.x / 2, 'y': pl.y / 2}, 'rotation': pl.rotation, 'xScale': pl.xscale,
            'yScale': pl.yscale, 'anchor': 'center', 'pivot': 'center'}


def test_the_loader_puts_a_template_stem_on_the_instance_stem():
    # a template PNG 40 x 60 px (20 x 30 units) with its stem at the centre
    pl = T.Placement(None, 101.0, 64.5, 0.6, -1.5, 0.75)
    m = preview.node_matrix(stem_overrides(pl), 20, 30)
    assert preview.apply(m, 10, 15) == pytest.approx((101.0 / 2, 64.5 / 2))


def test_the_loader_turns_and_scales_a_template_about_its_stem_like_the_svg_placement():
    pl = T.Placement(None, 101.0, 64.5, 0.6, -1.5, 0.75)
    m = preview.node_matrix(stem_overrides(pl), 20, 30)
    # a template point 4 px right of and 10 px above the stem
    x, y = preview.apply(m, 10 + 2, 15 - 5)
    a, b, c, d, e, f = pl.matrix()
    want = (a * 4 + c * -10 + e, b * 4 + d * -10 + f)
    assert (x * 2, y * 2) == pytest.approx(want)


def test_a_topleft_node_without_rotation_is_a_plain_offset():
    m = preview.node_matrix({'position': {'x': 3, 'y': 4}}, 10, 10)
    assert preview.apply(m, 1, 1) == pytest.approx((4, 5))


# ---------------------------------------------------------------- objects

def track(**keyframes):
    return [{'loopTrack': True, 'steps': [{'durationSeconds': 1, 'easeType': 'linear', 'animateProperties': keyframes}]}]


def urn():
    return [
        {'id': 'left urn body', 'filePath': 'furniture/parts/left-urn/body', 'position': {'x': 100.4, 'y': 350.6}},
        {'id': 'left urn bush face 1', 'ref': 'plants/leaves.json#leaf-broad-1',
         'overrides': {'position': {'x': 120, 'y': 340}, 'rotation': 0.5}},
        {'id': 'left urn bush edge 1', 'ref': 'plants/branches.json#branch-small-1',
         'overrides': {'position': {'x': 110, 'y': 345}, 'animationTracks': track(x=112, rotation=0.2)}}]


def test_an_objects_template_is_drawn_from_its_first_images_rounded_place():
    template = cutting.object_template('left-urn', urn())
    body, face, edge = template['children']
    assert template['templateOnly'] is True
    assert body['position'] == {'x': pytest.approx(0.4), 'y': pytest.approx(-0.4)}
    assert face['overrides']['position'] == {'x': 20, 'y': -11}


def test_an_objects_template_moves_its_tracks_with_its_nodes():
    edge = cutting.object_template('left-urn', urn())['children'][2]
    assert edge['overrides']['animationTracks'][0]['steps'][0]['animateProperties'] == {'x': 12, 'rotation': 0.2}


def test_an_objects_ref_draws_its_template_where_its_nodes_were():
    assert cutting.object_ref('left urn object', 'furniture/planters.json', 'left-urn', urn()) == {
        'id': 'left urn object', 'ref': 'furniture/planters.json#left-urn', 'overrides': {'position': {'x': 100, 'y': 351}}}


def test_making_an_objects_template_leaves_its_nodes_alone():
    nodes = urn()
    cutting.object_template('left-urn', nodes)
    assert nodes == urn()


def test_a_node_without_a_place_cannot_move_into_a_template():
    with pytest.raises(ValueError):
        cutting.shifted([{'id': 'loose', 'children': []}], (0, 0))

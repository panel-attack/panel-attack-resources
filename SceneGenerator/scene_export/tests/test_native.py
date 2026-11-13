import pytest

from scene_export import game, native, svgtools


# ---------------------------------------------------------------- native size

def test_native_pixels_are_the_drawing_pixels_scaled_to_the_canvas_and_even():
    assert [native.native_px(px) for px in (316, 260, 350, 34, 86, 1536)] == [526, 434, 584, 56, 144, 2560]


def test_native_pixels_of_a_part_drawn_at_half_its_sheet_size():
    assert native.native_px(316, 0.5) == 264


def part_svg(w, h):
    return svgtools.part_svg('p', [], {}, (0, 0, w, h)).replace('<g id="p"/>', '<g id="p"><path d="M0 0L6 4"/></g>')


def test_a_part_svg_is_drawn_at_its_native_size_from_its_top_left():
    text = native.native_svg(part_svg(6, 4))

    assert '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6" viewBox="0 0 6 3.6" preserveAspectRatio="none">' in text
    assert '<path d="M0 0L6 4"/>' in text


def test_a_part_svg_at_half_its_sheet_size_keeps_its_centre_anchor_in_the_middle():
    text = native.native_svg(part_svg(100, 61), (0.5, 0.5), 'center')

    assert '<svg xmlns="http://www.w3.org/2000/svg" width="84" height="50" viewBox="-0.4 0.5 100.8 60" preserveAspectRatio="none">' in text


def test_a_part_svg_keeps_its_bottom_centre_anchor_on_its_foot():
    text = native.native_svg(part_svg(100, 61), (0.5, 0.5), 'bottomCenter')

    assert 'viewBox="-0.4 1 100.8 60"' in text


def test_a_part_is_built_at_the_size_its_png_is_drawn_at():
    from scene_export.cutting import Part
    part = Part('p/leaf', part_svg(100, 61), (300, 200, 100, 61))

    built = native.native_part(part, (0.5, 0.5), 'center')

    assert (built.path, built.size) == ('p/leaf', (84, 50))
    assert built.svg == native.native_svg(part.svg, (0.5, 0.5), 'center')


def test_a_strip_part_is_built_one_png_px_wide_at_its_full_height():
    from scene_export.cutting import Part
    from scene_export import svgtools
    part = Part('p/sky', part_svg(2, 1024), (0, 0, 2, 1024), strip=True)

    built = native.native_part(part)

    assert built.size == (1, 1706)
    assert 'width="1" height="1706" viewBox="0 0 2 1023.6"' in built.svg
    assert svgtools.validate(built.svg, native=True, strip=True) == []


def test_a_part_svg_drawn_at_its_native_size_is_in_the_form_the_build_writes():
    from scene_export import svgtools
    built = native.native_svg(part_svg(100, 61), (0.5, 0.5), 'center')
    assert svgtools.validate(built, native=True) == []
    assert svgtools.validate(built) != []


def test_a_native_svg_with_an_empty_viewbox_is_refused():
    from scene_export import svgtools
    built = native.native_svg(part_svg(100, 61)).replace('viewBox="0 0 99.6 61.2"', 'viewBox="0 0 0 61"')
    assert svgtools.validate(built, native=True) == ['viewBox \'0 0 0 61\' must be four numbers with a size']


def test_a_one_px_wide_svg_is_refused_unless_it_is_a_strip():
    from scene_export import svgtools
    one = part_svg(2, 1024).replace('width="2"', 'width="1"').replace('viewBox="0 0 2 1024"', 'viewBox="0 0 1 1024"')
    assert svgtools.validate(one) == ['size 1 x 1024 must be even and at least 2']


# ---------------------------------------------------------------- resolution

def scene(*children):
    return {'drawables': [{'id': 'scene', 'children': list(children)}]}


def leaf_ref(node_id, scale, x=0, **more):
    return {'id': node_id, 'ref': 'f.json#leaf', 'overrides': dict(position={'x': x, 'y': 0}, xScale=scale,
                                                                  yScale=scale, **more)}


TEMPLATES = {'drawables': [{'id': 'leaf', 'filePath': 'p/leaf', 'anchor': 'center', 'pivot': 'center',
                            'templateOnly': True},
                           {'id': 'rock', 'filePath': 'p/rock', 'templateOnly': True}]}


def test_a_part_drawn_at_one_scale_is_drawn_at_exactly_that_scale():
    docs = {'S.json': scene(leaf_ref('a', 0.4), leaf_ref('b', -0.4)), 'f.json': TEMPLATES}
    assert native.resolutions(docs, ['S.json']) == {'p/leaf': (0.4, 0.4)}


def test_a_repeating_part_stays_at_its_sheet_size():
    docs = {'S.json': scene({'id': 'fall', 'filePath': 'p/fall', 'wrap': 'repeat', 'xScale': 0.5, 'yScale': 0.5})}
    assert native.resolutions(docs, ['S.json']) == {}


def test_a_part_stretched_to_a_size_stays_at_its_sheet_size():
    docs = {'S.json': scene({'id': 'sky', 'filePath': 'p/sky', 'size': {'width': 1280}, 'pivot': 'topLeft'})}
    assert native.resolutions(docs, ['S.json']) == {}


def test_resolving_divides_each_ref_scale_and_keyframe_by_the_resolution():
    grow = [{'repeat': 'loop', 'steps': [{'durationSeconds': 1, 'animateProperties': {'xScale': 0.5, 'yScale': 1}}]}]
    docs = {'S.json': scene(leaf_ref('a', 0.25), leaf_ref('b', 0.5, animationTracks=grow), leaf_ref('c', 2)),
            'f.json': TEMPLATES}

    out, _ = native.resolved(docs, ['S.json'], {'p/leaf': (10, 10)})

    a, b, c = out['S.json']['drawables'][0]['children']
    assert (a['overrides']['xScale'], b['overrides']['xScale']) == (0.125, 0.25)
    assert 'yScale' not in c['overrides']
    assert b['overrides']['animationTracks'][0]['steps'][0]['animateProperties'] == {'xScale': 0.25, 'yScale': 0.5}
    assert a['overrides']['position'] == {'x': 0, 'y': 0}


def test_resolving_moves_an_image_drawn_from_its_top_left_and_scaled_about_its_centre_so_it_draws_in_place():
    docs = {'S.json': scene({'id': 'oak', 'filePath': 'p/oak', 'position': {'x': 100, 'y': 50}, 'xScale': 0.5,
                             'yScale': 0.5})}

    out, rs = native.resolved(docs, ['S.json'], {'p/oak': (40, 20)})

    oak = out['S.json']['drawables'][0]['children'][0]
    assert rs == {'p/oak': (0.5, 0.5)}
    assert oak == {'id': 'oak', 'filePath': 'p/oak', 'position': {'x': 110, 'y': 55}}


def test_resolving_leaves_a_template_and_a_ref_scaled_about_its_anchor_where_they_are():
    docs = {'S.json': scene({'id': 'r', 'ref': 'f.json#rock', 'overrides': {'xScale': 0.5, 'yScale': 0.5,
                                                                          'pivot': 'topLeft'}}),
            'f.json': TEMPLATES}

    out, _ = native.resolved(docs, ['S.json'], {'p/rock': (40, 20)})

    rock = out['S.json']['drawables'][0]['children'][0]['overrides']
    assert rock == {'pivot': 'topLeft'}
    assert out['f.json'] == TEMPLATES


def test_resolving_a_ref_drawn_at_its_resolution_draws_its_png_at_scale_one():
    docs = {'S.json': scene(leaf_ref('a', 0.4), leaf_ref('b', 0.4, x=50)), 'f.json': TEMPLATES}

    out, _ = native.resolved(docs, ['S.json'], {'p/leaf': (10, 10)})

    assert {i.scale for i in native.instances(out, ['S.json'], SIZES)} == {(1, 1)}


def test_resolving_draws_a_whole_file_ref_as_its_file_draws():
    docs = {'S.json': scene({'id': 'all', 'ref': 'L.json', 'overrides': {'position': {'x': 3, 'y': 0}}}),
            'L.json': scene(leaf_ref('a', 0.4)), 'f.json': TEMPLATES}

    out, rs = native.resolved(docs, ['S.json'], {'p/leaf': (10, 10)})

    assert rs == {'p/leaf': (0.4, 0.4)}
    assert out['S.json'] == docs['S.json']
    assert 'xScale' not in out['L.json']['drawables'][0]['children'][0]['overrides']


# ---------------------------------------------------------------- the check

SIZES = {'p/leaf': (10, 10), 'p/rock': (10, 6), 'p/oak': (40, 20)}.get


def test_a_part_used_once_drawn_at_its_size_on_a_whole_unit_passes():
    native.check({'S.json': scene({'id': 'oak', 'filePath': 'p/oak', 'position': {'x': 3, 'y': 4}})}, ['S.json'], SIZES)


def test_a_part_used_once_drawn_scaled_is_refused_naming_it():
    docs = {'S.json': scene({'id': 'oak', 'filePath': 'p/oak', 'position': {'x': 3, 'y': 4}, 'xScale': 1.2,
                             'yScale': 1.2})}
    with pytest.raises(ValueError, match='p/oak: drawn at scale 1.2'):
        native.check(docs, ['S.json'], SIZES)


def test_a_part_used_once_off_a_whole_unit_is_refused_naming_it():
    docs = {'S.json': scene({'id': 'oak', 'filePath': 'p/oak', 'position': {'x': 3.5, 'y': 4}})}
    with pytest.raises(ValueError, match='p/oak: its top left 3.5, 4'):
        native.check(docs, ['S.json'], SIZES)


def test_a_part_drawn_twice_at_one_scale_counts_as_used_once():
    docs = {'S.json': scene(leaf_ref('a', 0.5, x=1), leaf_ref('b', 0.5, x=40)), 'f.json': TEMPLATES}
    with pytest.raises(ValueError, match='p/leaf'):
        native.check(docs, ['S.json'], SIZES)


@pytest.mark.parametrize('more', [{'rotation': 0.3}, {'animationTracks': [
    {'repeat': 'loop', 'steps': [{'durationSeconds': 1, 'animateProperties': {'rotation': 0.1}}]}]}])
def test_a_rotated_or_swaying_part_used_once_may_be_scaled(more):
    native.check({'S.json': scene(leaf_ref('a', 0.5, **more)), 'f.json': TEMPLATES}, ['S.json'], SIZES)


def test_a_part_used_once_stretched_to_a_size_may_be_scaled():
    sky = {'id': 'sky', 'filePath': 'p/oak', 'size': {'width': 1280}, 'pivot': 'topLeft', 'position': {'x': 0.5}}
    native.check({'S.json': scene(sky)}, ['S.json'], SIZES)


def test_a_part_drawn_anywhere_larger_than_its_png_is_refused_naming_it_and_the_scale():
    docs = {'S.json': scene(leaf_ref('a', 0.5), leaf_ref('b', 2)), 'f.json': TEMPLATES}
    with pytest.raises(ValueError, match='p/leaf: drawn at 2x its PNG'):
        native.check(docs, ['S.json'], SIZES)


def test_a_swaying_part_drawn_larger_than_its_png_is_refused():
    sway = {'animationTracks': [{'repeat': 'loop', 'steps': [{'durationSeconds': 1,
                                                             'animateProperties': {'rotation': 0.1}}]}]}
    docs = {'S.json': scene(leaf_ref('a', 1.5, rotation=0.3, **sway)), 'f.json': TEMPLATES}
    with pytest.raises(ValueError, match='p/leaf: drawn at 1.5x its PNG'):
        native.check(docs, ['S.json'], SIZES)


def test_a_part_drawn_at_several_scales_is_exported_at_the_largest_so_none_is_drawn_larger():
    docs = {'S.json': scene(leaf_ref('a', 0.25), leaf_ref('b', 0.5), leaf_ref('c', 2)), 'f.json': TEMPLATES}
    assert native.resolutions(docs, ['S.json']) == {'p/leaf': (2, 2)}


def test_a_template_drawn_at_several_scales_may_be_scaled():
    native.check({'S.json': scene(leaf_ref('a', 0.5), leaf_ref('b', 0.7)), 'f.json': TEMPLATES}, ['S.json'], SIZES)


def test_aligning_moves_a_part_used_once_onto_a_whole_unit_half_a_unit_rounding_up():
    docs = {'S.json': scene({'id': 'oak', 'filePath': 'p/oak', 'position': {'x': 3.5, 'y': 4.2}},
                            {'id': 'r', 'ref': 'f.json#rock', 'overrides': {'position': {'x': 7.3, 'y': 1}}}),
            'f.json': TEMPLATES}

    out = native.aligned(docs, ['S.json'], SIZES)

    oak, rock = out['S.json']['drawables'][0]['children']
    assert oak['position'] == {'x': 4, 'y': 4}
    assert rock['overrides']['position'] == {'x': 7, 'y': 1}
    native.check(out, ['S.json'], SIZES)


def test_aligning_leaves_a_part_whose_places_disagree_where_it_is():
    obj = {'drawables': [{'id': 'urn', 'templateOnly': True, 'children': [
        {'id': 'body', 'filePath': 'p/oak', 'position': {'x': 0, 'y': 0}}]}]}
    docs = {'S.json': scene({'id': 'a', 'ref': 'o.json#urn', 'overrides': {'position': {'x': 0.3, 'y': 0}}},
                            {'id': 'b', 'ref': 'o.json#urn', 'overrides': {'position': {'x': 50.6, 'y': 0}}}),
            'o.json': obj}

    assert native.aligned(docs, ['S.json'], SIZES) == docs


# ---------------------------------------------------------------- the root file

def test_the_screen_is_one_canvas_sized_container_holding_the_scene():
    assert game.screen_scene('TrainMeadow') == {'drawables': [{
        'id': 'canvas', 'size': {'width': 1280, 'height': 720},
        'children': [{'id': 'TrainMeadow scene', 'ref': 'TrainMeadow/TrainMeadow.json'}]}]}


def test_a_root_file_of_one_canvas_container_passes():
    game.check_root(game.screen_scene('TrainMeadow'), 'TrainMeadow')
    game.check_root({'drawables': [{'id': 'c', 'size': {'width': 1280, 'height': 720}, 'position': {'x': 0, 'y': 0},
                                    'children': []}]}, 'Esme')


@pytest.mark.parametrize('change', [
    lambda c: c.update(xScale=1.6667, yScale=1.6667),
    lambda c: c.update(position={'x': 0, 'y': -66.6667}),
    lambda c: c.update(size={'width': 768, 'height': 512}),
    lambda c: c.pop('size'),
    lambda c: c.update(filePath='scenes/sky'),
    lambda c: c.update(ref='scenes/x.json#canvas'),
    lambda c: c.update(rotation=0.1),
])
def test_a_root_file_whose_container_is_not_the_canvas_is_refused_naming_the_scene(change):
    doc = game.screen_scene('TrainMeadow')
    change(doc['drawables'][0])

    with pytest.raises(ValueError, match='TrainMeadow'):
        game.check_root(doc, 'TrainMeadow')


def test_a_root_file_with_more_than_the_canvas_at_the_top_is_refused():
    doc = game.screen_scene('TrainMeadow')
    doc['drawables'].append({'id': 'sky', 'filePath': 'scenes/sky'})

    with pytest.raises(ValueError, match='TrainMeadow'):
        game.check_root(doc, 'TrainMeadow')


def test_layout_refuses_to_write_a_root_file_without_the_canvas(tmp_path):
    from scene_export import layout, store
    st = store.Store(str(tmp_path), state=str(tmp_path / 'gen'))
    old = {'drawables': [{'id': 'TrainMeadow on the canvas', 'xScale': 1.6667, 'yScale': 1.6667,
                          'children': [{'id': 'TrainMeadow scene', 'ref': 'TrainMeadow/TrainMeadow.json'}]}]}

    with pytest.raises(ValueError, match='MainMenu'):
        layout.write_docs({'MainMenu.json': old}, ['MainMenu.json'], st, roots=['MainMenu.json'])
    assert not (tmp_path / 'MainMenu.json').exists()


# ---------------------------------------------------------------- layout

def test_layout_draws_a_part_used_once_at_its_png_size_on_a_whole_unit():
    from scene_export import layout
    docs = {'S.json': scene({'id': 'oak', 'filePath': 'p/oak', 'position': {'x': 100.2, 'y': 50}, 'xScale': 0.5,
                             'yScale': 0.5})}

    out, rs = layout.finished(docs, ['S.json'], {'p/oak': (48, 24)})

    assert rs == {'p/oak': (0.5, 0.5)}
    assert out['S.json']['drawables'][0]['children'][0] == {'id': 'oak', 'filePath': 'p/oak',
                                                            'position': {'x': 110, 'y': 55}}


def test_layout_refuses_a_part_used_once_it_cannot_put_on_a_whole_unit():
    from scene_export import layout
    obj = {'drawables': [{'id': 'urn', 'templateOnly': True, 'children': [
        {'id': 'body', 'filePath': 'p/oak', 'position': {'x': 0, 'y': 0}}]}]}
    docs = {'S.json': scene({'id': 'a', 'ref': 'o.json#urn', 'overrides': {'position': {'x': 0.3, 'y': 0}}},
                            {'id': 'b', 'ref': 'o.json#urn', 'overrides': {'position': {'x': 50.6, 'y': 0}}}),
            'o.json': obj}

    with pytest.raises(ValueError, match='p/oak: its top left 0.3, 0 is off a whole canvas unit'):
        layout.finished(docs, ['S.json'], {'p/oak': (48, 24)})


def test_the_scenes_lay_out_with_no_part_drawn_larger_than_its_png():
    from scene_export import layout
    layout.planned.cache_clear()
    layout.planned()


# A part reused at several scales is exported at its largest drawn scale on each axis, so its PNG can have other
# proportions than its art; the renderer letterboxes such an SVG unless it is told to stretch it to fill
def test_a_part_svg_drawn_at_another_scale_on_each_axis_stretches_to_fill_its_png():
    built = native.native_svg(part_svg(100, 61), (1.0, 0.5))

    assert 'preserveAspectRatio="none"' in built
    assert svgtools.validate(built, native=True) == []


def test_a_strip_stretches_to_fill_its_png():
    from scene_export.cutting import Part
    part = Part('p/sky', part_svg(2, 1024), (0, 0, 2, 1024), strip=True)

    assert 'preserveAspectRatio="none"' in native.native_part(part).svg


def test_a_native_svg_that_would_be_letterboxed_is_refused():
    built = native.native_svg(part_svg(100, 61), (1.0, 0.5)).replace(' preserveAspectRatio="none"', '')

    assert svgtools.validate(built, native=True) == [
        'viewBox \'0 0 99.6 60\' has other proportions than 166 x 50, so it must have preserveAspectRatio="none"']

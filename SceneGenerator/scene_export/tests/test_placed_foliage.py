import re

import pytest

from scene_export import placed_foliage as P, wind
from furniture import planters, planters_template
from plants import branches, bushes, bushes_template


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


@pytest.fixture(scope='module')
def placed():
    return P.placed()


BRANCH = P.BRANCHES + '#'
PLANT_OBJECTS = {'left urn bush': 'left urn', 'right urn bush': 'right urn',
                 'crystal planter back bush': 'crystal planter', 'crystal planter front bush': 'crystal planter'}
STEMS = {'stem-short-thin', 'stem-short-thick', 'stem-long-thin', 'stem-long-thick'}
FOLIAGE_REF = re.compile(r'plants/(leaves|flowers|roses|stems)\.json#')


def assert_placed_as_laid_out(nodes, layout):
    assert [n['ref'] for n in nodes] == [BRANCH + p.piece for p in layout]
    for node, p in zip(nodes, layout):
        o = node['overrides']
        position = o.get('position', {})
        assert (position.get('x', 0), position.get('y', 0)) == pytest.approx((p.at[0] / 2, p.at[1] / 2), abs=1e-3)
        assert o['rotation'] == pytest.approx(p.rotation, abs=1e-5)
        assert (o['xScale'], o['yScale']) == pytest.approx(((-1 if p.mirror else 1) * p.scale, p.scale), abs=1e-5)


# ---------------------------------------------------------------- the bushes

def test_the_corner_bush_places_each_piece_of_its_layout_by_one_ref(placed):
    pieces = [n for n in placed.children['corner bush'] if n.get('ref', '').startswith(BRANCH)]
    assert_placed_as_laid_out(pieces, bushes.corner_bush_layout())


def test_every_leaf_and_stem_of_the_corner_bush_comes_from_a_library_piece(placed):
    loose = [n['ref'] for n in walk(placed.children['corner bush']) if re.search(r'#(leaf|stem)', n.get('ref', ''))]
    assert loose == []


def test_each_plant_places_each_piece_of_its_layout_by_one_ref(placed):
    for name, plant in planters.plant_layouts().items():
        nodes = [n for n in placed.children[PLANT_OBJECTS[name]]
                 if n['id'].startswith(name + ' ') and n.get('ref', '').startswith(BRANCH)]
        assert_placed_as_laid_out(nodes, plant.layout)


def test_no_plant_bush_has_loose_leaves_or_leaf_stems(placed):
    loose = [n['id'] for obj in set(PLANT_OBJECTS.values()) for n in walk(placed.children[obj])
             if re.fullmatch(r'.* (bush|back bush|front bush) (leaf|stem) \d+', n['id'])]
    assert loose == []


def test_a_pots_body_image_holds_no_bush_mass(placed):
    for obj in set(PLANT_OBJECTS.values()):
        body = next(p for p in placed.parts[obj] if p.path.endswith('/body'))
        assert ' mass ' not in body.svg, obj


def test_a_plants_mass_is_its_own_image_drawn_before_its_pieces(placed):
    # the urns' plants have no mass (see test_urns)
    for name, obj in PLANT_OBJECTS.items():
        if obj != 'crystal planter':
            continue
        ids = [n['id'] for n in placed.children[obj]]
        assert 'filePath' in placed.children[obj][ids.index(name)], name
        first_piece = next(i for i, n in enumerate(ids) if n.startswith(name + ' '))
        assert ids.index(name) < first_piece, name


def test_the_templates_sway_every_plant_they_place():
    docs = planters_template.build()['drawables'] + bushes_template.build()['drawables']
    plants = [n for n in walk(docs) if any(r in n.get('ref', '') for r in wind.PLANT_REFS)]
    assert plants and all(n['overrides'].get('animationTracks') for n in plants)


def test_a_templates_refs_are_named_by_object_and_reference_numbered_in_draw_order():
    templates = {**planters_template.TEMPLATES, **bushes_template.TEMPLATES}
    for t in planters_template.build()['drawables'] + bushes_template.build()['drawables']:
        obj = next(o for o, tid in templates.items() if tid == t['id'])
        counts = {}
        for n in t['children']:
            if 'ref' in n:
                ref_id = n['ref'].partition('#')[2]
                counts[ref_id] = counts.get(ref_id, 0) + 1
                assert n['id'] == '%s %s %d' % (obj, ref_id, counts[ref_id])


# ---------------------------------------------------------------- the library pieces

def library(placed):
    return {t['id']: t for t in placed.library}


def test_no_ref_overrides_a_position_axis_its_template_already_sits_at(placed):
    nodes = [n for obj in placed.children.values() for n in walk(obj)] + [n for t in placed.library for n in walk([t])]
    positions = [n['overrides']['position'] for n in nodes if 'position' in n.get('overrides', {})]
    assert positions
    assert [p for p in positions if not p or 0 in p.values()] == []


def test_every_library_piece_is_a_json_template(placed):
    assert set(library(placed)) == {p.id for p in branches.library()}
    for t in placed.library:
        assert t['templateOnly'] is True and 'filePath' not in t and t['children']


def test_a_library_piece_draws_from_the_foliage_templates(placed):
    refs = [n['ref'] for n in walk(placed.library) if 'ref' in n]
    assert refs
    for r in refs:
        f, _, rid = r.partition('#')
        assert f == P.foliage_file(rid) and rid in placed.templates, r


def test_a_branch_draws_its_stems_from_the_stem_templates(placed):
    branch = library(placed)['branch-large-1']
    stems = {n['ref'].partition('#')[2] for n in walk(branch['children']) if 'stem' in n.get('ref', '')}
    assert stems and stems <= STEMS
    assert {'stem-long-thick', 'stem-long-thin'} & stems


def test_a_branchs_side_shoot_is_a_group_at_where_it_grows(placed):
    shoots = [c for c in library(placed)['branch-large-1']['children'] if c['id'].startswith('branch-large-1 shoot ')]
    assert len(shoots) == 3
    for s in shoots:
        assert set(s) == {'id', 'position', 'children'} and s['children']


# ---------------------------------------------------------------- the foliage templates

def test_the_stems_are_foliage_templates_in_two_lengths_and_two_widths(placed):
    assert STEMS <= set(placed.templates)


def test_every_foliage_template_is_template_only_and_centred_on_its_stem():
    for group in ('leaves', 'flowers', 'roses', 'stems'):
        for t in P.template_file(group)['drawables']:
            assert t['templateOnly'] is True
            assert t['anchor'] == 'center' and t['pivot'] == 'center'


def test_no_stem_piece_is_stretched_past_its_png(placed):
    for n in walk(placed.library):
        if '#stem-' in n.get('ref', ''):
            assert abs(n['overrides']['yScale']) <= 1.0 + 1e-9, n['id']


def test_no_ref_draws_its_foliage_template_larger_than_its_png(placed):
    for n in walk([n for nodes in placed.children.values() for n in nodes] + placed.library):
        if FOLIAGE_REF.match(n.get('ref', '')):
            o = n['overrides']
            assert max(abs(o['xScale']), abs(o['yScale'])) <= 1.0 + 1e-9, n['id']


def test_no_library_leaf_is_drawn_larger_than_its_png_where_the_bush_grows_it(placed):
    templates = library(placed)
    for node in [n for nodes in placed.children.values() for n in walk(nodes) if n.get('ref', '').startswith(BRANCH)]:
        o = node['overrides']
        scale = max(abs(o['xScale']), abs(o['yScale']))
        for n in walk(templates[node['ref'].partition('#')[2]]['children']):
            if FOLIAGE_REF.match(n.get('ref', '')):
                inner = n['overrides']
                assert scale * max(abs(inner['xScale']), abs(inner['yScale'])) <= 1.0 + 1e-6, (node['id'], n['id'])

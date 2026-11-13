import importlib
import json
import os
import posixpath

import pytest

from scene_export import GAME_SCENES, GAME_THEME, svgtools, __main__ as main


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


@pytest.fixture(scope='module')
def docs():
    return {name: importlib.import_module(name) for name in main.JSON_MODULES}


@pytest.fixture(scope='module')
def built(docs):
    return {m.OUTPUT: m.build() for m in docs.values()}


@pytest.fixture(scope='module')
def parts():
    return {name: importlib.import_module(name).parts() for name in main.IMAGE_MODULES}


def is_template_file(doc):
    return all(n.get('templateOnly') for n in doc['drawables'])


def test_no_two_modules_write_the_same_json_file(docs):
    outputs = [m.OUTPUT for m in docs.values()]
    assert len(outputs) == len(set(outputs))


def test_a_template_module_is_named_for_its_file_and_a_scene_module_for_its_scene(docs, built):
    for name, m in docs.items():
        stem = posixpath.splitext(m.OUTPUT)[0].replace('-', '_').replace('/', '.')
        want = stem + '_template' if is_template_file(built[m.OUTPUT]) else stem
        assert name == want, m.OUTPUT


def test_a_file_holds_only_templates_or_none(built):
    for rel, doc in built.items():
        flags = {bool(n.get('templateOnly')) for n in walk(doc['drawables'])}
        if is_template_file(doc):
            continue
        assert flags == {False}, rel


def test_every_ref_names_a_template_another_module_writes(built):
    templates = {(rel, n['id']) for rel, doc in built.items() for n in doc['drawables'] if n.get('templateOnly')}
    for rel, doc in built.items():
        for n in walk(doc['drawables']):
            if 'ref' in n:
                file, _, tid = n['ref'].partition('#')
                if tid:
                    assert (file, tid) in templates, (rel, n['id'], n['ref'])
                else:
                    assert file in built, (rel, n['id'], n['ref'])


def test_no_two_image_modules_make_the_same_part(parts):
    paths = [p.path for ps in parts.values() for p in ps]
    assert len(paths) == len(set(paths))


def test_an_image_modules_parts_are_in_the_parts_folder_beside_it(parts):
    for name, ps in parts.items():
        folder = name.rpartition('.')[0].replace('.', '/') + '/parts/'
        assert ps, name
        assert all(p.path.startswith(folder) for p in ps), name


def test_every_image_a_json_file_places_has_a_module_making_it(built, parts):
    made = {p.path for ps in parts.values() for p in ps}
    for rel, doc in built.items():
        for n in walk(doc['drawables']):
            if 'filePath' in n:
                assert n['filePath'] in made, (rel, n['id'])


def test_every_id_is_used_once_across_the_files(built):
    ids = [n['id'] for doc in built.values() for n in walk(doc['drawables'])]
    assert len(ids) == len(set(ids))


def test_a_ref_node_only_has_the_keys_the_loader_allows(built):
    for rel, doc in built.items():
        for n in walk(doc['drawables']):
            if 'ref' in n:
                assert set(n) <= {'id', 'ref', 'overrides', 'templateOnly'}, (rel, n['id'])


def test_draw_order_is_file_order(built):
    assert not [n['id'] for doc in built.values() for n in walk(doc['drawables']) if 'drawPass' in n]


def test_every_part_svg_is_in_the_generators_form(parts):
    for ps in parts.values():
        for p in ps:
            assert svgtools.validate(p.svg) == [], p.path


@pytest.mark.skipif(not os.path.exists(os.path.join(GAME_SCENES, 'EsmeTerrace', 'EsmeTerrace.json')),
                    reason='the scene has not been laid out')
def test_every_image_path_in_the_game_files_has_its_png():
    drawables = []
    for folder, dirs, names in os.walk(GAME_SCENES):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if folder == GAME_SCENES:
            continue        # the theme's own screens, not the generators'
        for name in names:
            if name.endswith('.json') and not name.startswith('.'):
                with open(os.path.join(folder, name)) as f:
                    drawables += json.load(f)['drawables']
    missing = [n['filePath'] for n in walk(drawables)
               if 'filePath' in n and not os.path.exists(os.path.join(GAME_THEME, n['filePath'] + '@2x.png'))]
    assert missing == []

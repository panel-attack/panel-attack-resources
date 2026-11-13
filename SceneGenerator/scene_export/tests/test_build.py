import json
import os
from types import SimpleNamespace

from scene_export import __main__ as build
from scene_export.cutting import Part


def part(path, svg='<svg/>'):
    return Part(path, svg, (0, 0, 8, 4))


def svg_at(root, rel):
    return os.path.join(str(root), rel + '.svg')


def test_part_svgs_are_written_at_their_scene_path(tmp_path, monkeypatch):
    monkeypatch.setattr(build.svgtools, 'validate', lambda svg, strip=False, native=False: [])
    build.write_build([part('furniture/parts/table-set/table')], str(tmp_path / 'Scenes'), str(tmp_path / 'index.json'))
    assert open(svg_at(tmp_path / 'Scenes', 'furniture/parts/table-set/table')).read() == '<svg/>'


def test_the_index_lists_each_part_with_its_svg_and_size(tmp_path, monkeypatch):
    monkeypatch.setattr(build.svgtools, 'validate', lambda svg, strip=False, native=False: [])
    build.write_build([part('plants/parts/roses/rose')], str(tmp_path / 'Scenes'), str(tmp_path / 'index.json'))
    assert json.load(open(tmp_path / 'index.json')) == [
        {'path': 'plants/parts/roses/rose', 'svg': 'plants/parts/roses/rose.svg', 'width': 8, 'height': 4}]


def test_a_part_the_build_no_longer_makes_has_its_svg_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(build.svgtools, 'validate', lambda svg, strip=False, native=False: [])
    root, index = str(tmp_path / 'Scenes'), str(tmp_path / 'index.json')
    build.write_build([part('plants/parts/roses/a'), part('plants/parts/roses/b')], root, index)
    build.write_build([part('plants/parts/roses/a')], root, index)
    assert not os.path.exists(svg_at(root, 'plants/parts/roses/b'))


def test_an_svg_the_build_never_wrote_is_left_alone(tmp_path, monkeypatch):
    monkeypatch.setattr(build.svgtools, 'validate', lambda svg, strip=False, native=False: [])
    root, index = tmp_path / 'Scenes', str(tmp_path / 'index.json')
    (root / 'plants/parts/roses').mkdir(parents=True)
    (root / 'plants/parts/roses/hand.svg').write_text('mine')
    build.write_build([part('plants/parts/roses/a')], str(root), index)
    assert (root / 'plants/parts/roses/hand.svg').read_text() == 'mine'


def test_write_build_returns_the_parts_whose_svg_changed(tmp_path, monkeypatch):
    monkeypatch.setattr(build.svgtools, 'validate', lambda svg, strip=False, native=False: [])
    root, index = str(tmp_path / 'Scenes'), str(tmp_path / 'index.json')
    build.write_build([part('a/parts/x/one'), part('a/parts/x/two')], root, index)
    changed = build.write_build([part('a/parts/x/one'), part('a/parts/x/two', '<svg id="new"/>')], root, index)
    assert changed == ['a/parts/x/two']


INDEX = [{'path': 'furniture/parts/table-set/table'}, {'path': 'furniture/parts/table-set/chair-back-left'},
         {'path': 'plants/parts/roses/rose'}]


def chosen(**kw):
    args = dict(names=[], every=False, changed=[], has_png=lambda path: True)
    args.update(kw)
    return [p['path'] for p in build.to_render(INDEX, **args)]


def test_with_no_names_only_parts_whose_svg_changed_are_rendered():
    assert chosen(changed=['plants/parts/roses/rose']) == ['plants/parts/roses/rose']


def test_with_no_names_a_part_without_its_png_is_rendered():
    assert chosen(has_png=lambda path: path != 'furniture/parts/table-set/table') == ['furniture/parts/table-set/table']


def test_named_parts_are_rendered_though_unchanged():
    assert chosen(names=['table-set']) == ['furniture/parts/table-set/table', 'furniture/parts/table-set/chair-back-left']


def test_every_renders_all_parts():
    assert chosen(every=True) == [p['path'] for p in INDEX]


def written_by_layout(monkeypatch, names):
    written = []
    monkeypatch.setattr(build.layout, 'write', lambda *names: written.append(names))
    build.write_layout(names)
    return written


def test_layout_with_no_names_writes_the_whole_theme(monkeypatch):
    assert written_by_layout(monkeypatch, []) == [()]


def test_layout_writes_only_the_named_files(monkeypatch):
    assert written_by_layout(monkeypatch, ['plants/blossom.json']) == [('plants/blossom.json',)]

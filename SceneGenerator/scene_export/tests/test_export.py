import pytest

from scene_export import export, store

INDEX = [{'path': p} for p in (
    'EsmeTerrace/parts/left-urn/body', 'EsmeTerrace/parts/left-urn/shadow', 'EsmeTerrace/parts/right-urn/body',
    'shared/parts/foliage/leaf-urn-mid-arch', 'shared/parts/foliage/rose-34-163')]


def paths(sel):
    return [p['path'] for p in sel]


def test_no_names_selects_every_part():
    assert paths(export.select(INDEX, [])) == paths(INDEX)


def test_a_group_name_selects_its_folder():
    assert paths(export.select(INDEX, ['left-urn'])) == INDEX_PATHS[:2]


def test_a_group_can_be_named_like_its_scene_object():
    assert paths(export.select(INDEX, ['left urn'])) == INDEX_PATHS[:2]


def test_a_part_can_be_named_by_its_tail_or_full_path():
    assert paths(export.select(INDEX, ['right-urn/body'])) == ['EsmeTerrace/parts/right-urn/body']
    assert paths(export.select(INDEX, ['shared/parts/foliage/rose-34-163'])) == ['shared/parts/foliage/rose-34-163']


def test_a_template_can_be_named_by_its_id():
    assert paths(export.select(INDEX, ['rose-34-163'])) == ['shared/parts/foliage/rose-34-163']


def test_parts_keep_the_index_order_and_appear_once():
    assert paths(export.select(INDEX, ['right-urn', 'left-urn/body', 'left-urn'])) == [
        'EsmeTerrace/parts/left-urn/body', 'EsmeTerrace/parts/left-urn/shadow', 'EsmeTerrace/parts/right-urn/body']


def test_an_unknown_name_is_an_error():
    with pytest.raises(ValueError):
        export.select(INDEX, ['lamp post'])


INDEX_PATHS = paths(INDEX)


def test_a_render_with_the_same_pixels_counts_as_the_same_image(tmp_path):
    from PIL import Image
    a, b, c = (str(tmp_path / n) for n in ('a.png', 'b.png', 'c.png'))
    Image.new('RGBA', (4, 2), (1, 2, 3, 255)).save(a)
    Image.new('RGBA', (4, 2), (1, 2, 3, 255)).save(b, compress_level=0)
    Image.new('RGBA', (4, 2), (1, 2, 4, 255)).save(c)
    assert export.same_pixels(a, b)
    assert not export.same_pixels(a, c)
    assert not export.same_pixels(a, str(tmp_path / 'missing.png'))


def test_a_part_is_rendered_from_its_svg_and_its_png_goes_into_the_game_scenes_folder(tmp_path, monkeypatch):
    from PIL import Image
    part = {'path': 'structures/parts/houses/house-manor', 'svg': 'structures/parts/houses/house-manor.svg',
            'width': 4, 'height': 2}
    svgs, game = tmp_path / 'Scenes', tmp_path / 'scenes'
    (svgs / 'structures/parts/houses').mkdir(parents=True)
    (svgs / 'structures/parts/houses/house-manor.svg').write_text('<svg/>')
    monkeypatch.setattr(export, 'SVG_SCENES', str(svgs))
    monkeypatch.setattr(export, 'RENDERS', str(tmp_path / 'png'))
    monkeypatch.setattr(export, 'SLOT', str(tmp_path / 'slot.svg'))
    opened = []

    def fake_osascript(args, **kw):
        opened.append((args[2], open(args[2]).read()))
        Image.new('RGBA', (4, 2), (255, 0, 0, 255)).save(args[3])

        class Done:
            returncode, stdout, stderr = 0, 'ok', ''
        return Done()
    monkeypatch.setattr(export.subprocess, 'run', fake_osascript)
    assert export.export_one(part, 5, store.Store(str(game), state=str(tmp_path / 'gen'))) == 'written'
    assert opened == [(str(tmp_path / 'slot.svg'), '<svg/>')]
    assert (game / 'structures/parts/houses/house-manor@2x.png').exists()

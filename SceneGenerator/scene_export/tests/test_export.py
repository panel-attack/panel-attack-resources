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
    opened, run = [], export.subprocess.run

    def fake_osascript(args, **kw):
        if args[0] != 'osascript':
            return run(args, **kw)
        opened.append((args[2], open(args[2]).read()))
        Image.new('RGBA', (4, 2), (255, 0, 0, 255)).save(args[3])

        class Done:
            returncode, stdout, stderr = 0, 'ok', ''
        return Done()
    monkeypatch.setattr(export.subprocess, 'run', fake_osascript)
    assert export.export_one(part, 5, store.Store(str(game), state=str(tmp_path / 'gen'))) == 'written'
    assert opened == [(str(tmp_path / 'slot.svg'), '<svg/>')]
    assert (game / 'structures/parts/houses/house-manor@2x.png').exists()


def test_a_rendered_png_carries_its_license(tmp_path, monkeypatch):
    import json
    import subprocess
    from PIL import Image
    part = {'path': 'structures/parts/houses/house-manor', 'svg': 'structures/parts/houses/house-manor.svg',
            'width': 4, 'height': 2}
    svgs, game = tmp_path / 'Scenes', tmp_path / 'scenes'
    (svgs / 'structures/parts/houses').mkdir(parents=True)
    (svgs / 'structures/parts/houses/house-manor.svg').write_text('<svg/>')
    monkeypatch.setattr(export, 'SVG_SCENES', str(svgs))
    monkeypatch.setattr(export, 'RENDERS', str(tmp_path / 'png'))
    monkeypatch.setattr(export, 'SLOT', str(tmp_path / 'slot.svg'))
    run = subprocess.run

    def fake_osascript(args, **kw):
        if args[0] != 'osascript':
            return run(args, **kw)
        Image.new('RGBA', (4, 2), (255, 0, 0, 255)).save(args[3])

        class Done:
            returncode, stdout, stderr = 0, 'ok', ''
        return Done()
    monkeypatch.setattr(export.subprocess, 'run', fake_osascript)
    export.export_one(part, 5, store.Store(str(game), state=str(tmp_path / 'gen')))

    png = str(game / 'structures/parts/houses/house-manor@2x.png')
    tags = json.loads(run(['exiftool', '-j', '-XMP-cc:all', '-XMP-dc:all', png], capture_output=True, text=True).stdout)[0]
    assert tags['AttributionName'] == 'JamBox' and tags['Creator'] == 'JamBox'
    assert tags['License'] == 'https://creativecommons.org/licenses/by-sa/4.0/'
    assert tags['Rights'] == ('Copyright, JamBox, 2026. This work is licensed under the Creative Commons Attribution '
                              'ShareAlike 4.0 International License. To view a copy of this license, visit '
                              'https://creativecommons.org/licenses/by-sa/4.0/')


# Grey pixels at the borders. Pixelmator writes every transparent pixel as transparent black, and the game draws
# the 2x PNGs scaled with linear filtering, which blends an edge toward that black: a grey halo round white foam, a
# dark line under the lip. So every PNG's transparent pixels take the colour of the nearest painted pixel before it is
# installed; their alpha stays 0.
def test_transparent_pixels_take_the_colour_of_the_nearest_painted_pixel(tmp_path):
    from PIL import Image
    path = str(tmp_path / 'edge.png')
    im = Image.new('RGBA', (5, 3), (0, 0, 0, 0))
    im.putpixel((1, 1), (255, 250, 240, 255))
    im.putpixel((3, 1), (10, 20, 30, 128))
    im.save(path)
    export.bleed(path)
    out = Image.open(path).convert('RGBA')
    assert out.getpixel((1, 1)) == (255, 250, 240, 255) and out.getpixel((3, 1)) == (10, 20, 30, 128)
    assert out.getpixel((0, 0)) == (255, 250, 240, 0) and out.getpixel((0, 2)) == (255, 250, 240, 0)
    assert out.getpixel((4, 0)) == (10, 20, 30, 0) and out.getpixel((4, 2)) == (10, 20, 30, 0)
    assert all(out.getpixel((x, y))[3] == (255 if (x, y) == (1, 1) else 128 if (x, y) == (3, 1) else 0)
               for x in range(5) for y in range(3))


def test_an_all_transparent_or_all_opaque_image_is_left_as_it_is(tmp_path):
    from PIL import Image
    for px in ((0, 0, 0, 0), (9, 8, 7, 255)):
        path = str(tmp_path / 'flat.png')
        Image.new('RGBA', (3, 2), px).save(path)
        export.bleed(path)
        assert list(Image.open(path).convert('RGBA').getdata()) == [px] * 6


def test_a_rendered_png_is_bled_before_it_is_installed(tmp_path, monkeypatch):
    from PIL import Image
    part = {'path': 'structures/parts/houses/house-manor', 'svg': 'structures/parts/houses/house-manor.svg',
            'width': 4, 'height': 2}
    svgs, game = tmp_path / 'Scenes', tmp_path / 'scenes'
    (svgs / 'structures/parts/houses').mkdir(parents=True)
    (svgs / 'structures/parts/houses/house-manor.svg').write_text('<svg/>')
    monkeypatch.setattr(export, 'SVG_SCENES', str(svgs))
    monkeypatch.setattr(export, 'RENDERS', str(tmp_path / 'png'))
    monkeypatch.setattr(export, 'SLOT', str(tmp_path / 'slot.svg'))
    run = export.subprocess.run

    def fake_osascript(args, **kw):
        if args[0] != 'osascript':
            return run(args, **kw)
        im = Image.new('RGBA', (4, 2), (0, 0, 0, 0))
        im.putpixel((1, 0), (200, 100, 50, 255))
        im.save(args[3])

        class Done:
            returncode, stdout, stderr = 0, 'ok', ''
        return Done()
    monkeypatch.setattr(export.subprocess, 'run', fake_osascript)
    export.export_one(part, 5, store.Store(str(game), state=str(tmp_path / 'gen')))
    out = Image.open(game / 'structures/parts/houses/house-manor@2x.png').convert('RGBA')
    assert out.getpixel((3, 1)) == (200, 100, 50, 0) and out.getpixel((1, 0)) == (200, 100, 50, 255)


def test_a_nearly_transparent_black_pixel_takes_a_painted_neighbours_colour_too(tmp_path):
    """Pixelmator loses the colour of a pixel whose alpha rounds to 1 or 2, writing it black: it is recoloured like
    a transparent one, its alpha kept."""
    from PIL import Image
    path = str(tmp_path / 'edge.png')
    im = Image.new('RGBA', (4, 1), (0, 0, 0, 0))
    im.putpixel((1, 0), (200, 100, 50, 255))
    im.putpixel((2, 0), (0, 0, 0, 1))
    im.save(path)
    export.bleed(path)
    out = Image.open(path).convert('RGBA')
    assert out.getpixel((2, 0)) == (200, 100, 50, 1) and out.getpixel((3, 0)) == (200, 100, 50, 0)

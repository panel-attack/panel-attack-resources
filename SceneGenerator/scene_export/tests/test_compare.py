from PIL import Image

from scene_export import compare


def card(size, bg, box, colour):
    im = Image.new('RGBA', size, bg)
    im.paste(Image.new('RGBA', (box[2] - box[0], box[3] - box[1]), colour), box[:2])
    return im


PINK = (240, 100, 160, 255)


def test_fitting_crops_the_reference_to_what_stands_off_its_background():
    ref = card((100, 80), (10, 10, 10, 255), (30, 20, 70, 40), PINK)
    assert compare.content_box(ref) == (30, 20, 70, 40)


def test_fitting_crops_ours_to_its_opaque_pixels():
    ours = card((200, 200), (0, 0, 0, 0), (50, 60, 130, 100), PINK)
    assert compare.content_box(ours) == (50, 60, 130, 100)


def test_fitting_scales_ours_to_the_references_content():
    ref = card((100, 80), (10, 10, 10, 255), (30, 20, 70, 40), PINK)
    ours = card((200, 200), (0, 0, 0, 0), (50, 60, 130, 100), PINK)
    r, o = compare.fit(ref, ours)
    assert r.size == o.size == (40, 20)


def test_a_stage_box_crops_ours_where_the_reference_was_cut_from():
    ours = card((300, 300), (0, 0, 0, 0), (100, 120, 110, 130), PINK)
    ref = Image.new('RGBA', (20, 20), (255, 255, 255, 255))
    r, o = compare.at_stage_box(ref, ours, (95.4, 115.2))
    assert o.size == (20, 20) and o.getpixel((5, 5))[:3] == PINK[:3]


def test_the_sheet_puts_reference_ours_and_their_blend_side_by_side():
    ref = Image.new('RGB', (30, 20), 'white')
    sheet = compare.sheet(ref, ref, zoom=2)
    assert sheet.size == (3 * 60 + 2 * compare.GAP, 40)


def test_each_round_takes_the_next_number(tmp_path):
    for name in ('round-01.png', 'round-02.png', 'round-02-ours.png', 'notes.txt'):
        (tmp_path / name).write_bytes(b'')
    assert compare.next_round(str(tmp_path)) == 3


def test_a_rendered_svg_keeps_its_pixels_where_the_svg_put_them(tmp_path):
    svg = tmp_path / 'wide.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="100" viewBox="0 0 300 100">'
                   '<rect x="250" y="80" width="20" height="10" fill="#ff0000"/></svg>')
    im = compare.render_svg(str(svg))
    assert im.getpixel((260, 85))[:3] == (255, 0, 0)


def test_a_spec_asking_to_fit_scales_an_svg_group_to_the_references_content():
    ref = card((100, 80), (0, 0, 0, 0), (30, 20, 70, 40), PINK)
    ours = card((200, 200), (0, 0, 0, 0), (50, 60, 130, 100), PINK)
    r, o, _ = compare.framed({'svg': 'x.svg', 'group': 'g', 'fit': True}, ref, ours, '.')
    assert r.size == o.size == (40, 20)

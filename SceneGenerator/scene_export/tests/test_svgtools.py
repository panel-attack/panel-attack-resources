import pytest

from scene_export import svgtools


def test_path_bbox_covers_every_command():
    d = 'M10,20 L30,25 H40 V5 C50,6 51,7 52,30 Q60,40 12,41 Z'
    assert svgtools.path_bbox(d) == (10, 5, 60, 41)


def test_path_bbox_reads_numbers_without_separators():
    assert svgtools.path_bbox('M-1.5-2L3e1,4') == (-1.5, -2, 30, 4)


def test_shift_path_moves_every_coordinate():
    d = 'M10,20 L30,25 H40 V5 C50,6 51,7 52,30 Q60,40 12,41 Z'
    assert svgtools.shift_path(d, 10, 5) == 'M0,15 L20,20 H30 V0 C40,1 41,2 42,25 Q50,35 2,36 Z'


def test_crop_box_pads_and_rounds_out_to_even_pixels():
    # bbox 10.2..33.7 x 5..20, pad 4 -> 6.2..37.7 -> floor/ceil 6..38 = 32 wide (even); 1..24 = 23 -> 24
    assert svgtools.crop_box((10.2, 5, 33.7, 20), pad=4) == (6, 1, 32, 24)


def test_crop_box_keeps_an_even_size_when_clamped_to_the_canvas():
    x, y, w, h = svgtools.crop_box((0, 0, 1535.5, 1023), pad=4, canvas=(1536, 1024))
    assert (x, y) == (0, 0) and (w, h) == (1536, 1024)


def test_stem_box_puts_the_stem_exactly_at_the_centre():
    # stem at (100, 50); ink reaches 30 left, 10 right, 40 up, 6 down; pad 2
    x, y, w, h = svgtools.stem_box((70, 10, 110, 56), (100, 50), pad=2)
    assert (x + w / 2, y + h / 2) == (100, 50)
    assert x <= 68 and x + w >= 112 and y <= 8 and y + h >= 58
    assert w % 2 == 0 and h % 2 == 0


def test_stem_box_needs_an_integer_stem():
    with pytest.raises(ValueError):
        svgtools.stem_box((0, 0, 10, 10), (5.5, 5), pad=1)


def test_scale_path_scales_every_coordinate_about_the_origin():
    d = 'M10,-20 L30,25 H40 V5 C50,6 51,7 52,30 Q60,40 12,41 Z'
    assert svgtools.scale_path(d, 1.5) == 'M15,-30 L45,37.5 H60 V7.5 C75,9 76.5,10.5 78,45 Q90,60 18,61.5 Z'

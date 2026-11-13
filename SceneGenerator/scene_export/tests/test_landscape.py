import xml.etree.ElementTree as ET

import pytest

from common.painting import HEIGHT, WIDTH, Svg
from scene_export import cutting, svgtools
from scenery import landscape


@pytest.fixture(scope='module')
def village():
    svg = Svg()
    landscape.far_village(svg)
    return ET.fromstring('<svg xmlns="%s">%s</svg>' % (svgtools.SVG_NS, '\n'.join(svg.parts)))


def ids(root):
    return [e.get('id') for e in root.iter() if e.get('id')]


def group(root, gid):
    return cutting.find_group(root, gid)


def test_the_far_village_draws_no_houses(village):
    assert not [i for i in ids(village) if i.startswith(('wall', 'roof', 'spire', 'gable', 'window'))]


def test_the_meadow_runs_across_the_whole_width_down_to_the_bottom(village):
    x0, y0, x1, y1 = svgtools.element_bbox(group(village, 'meadow'))
    assert x0 <= 0 and x1 >= WIDTH and y1 >= HEIGHT


def test_the_meadow_starts_at_the_lakes_near_shore():
    assert landscape.meadow_top(800) == pytest.approx(landscape.curve_y(landscape.TOWN_BANK, 800))


@pytest.mark.parametrize('x, woods_foot', [(100, 600), (380, 560)])
def test_the_meadow_starts_below_the_left_woods_so_it_never_covers_them(x, woods_foot):
    assert landscape.meadow_top(x) >= woods_foot


def test_trees_are_scattered_across_the_meadow():
    trees = landscape.meadow_trees()
    assert len(trees) >= 8
    xs = [x for kind, x, base, w in trees]
    assert max(xs) - min(xs) > WIDTH * 0.6
    assert all(base > landscape.meadow_top(x) + w * 0.2 for kind, x, base, w in trees)


def test_the_meadow_trees_are_drawn_back_to_front():
    bases = [base for kind, x, base, w in landscape.meadow_trees()]
    assert bases == sorted(bases)


def test_every_meadow_tree_is_drawn(village):
    drawn = [g for g in group(village, 'meadow trees') if g.get('id').startswith('meadow tree ')]
    assert len(drawn) == len(landscape.meadow_trees())


def test_each_tree_is_drawn_as_the_kind_the_layout_names(village):
    drawn = [g for g in group(village, 'meadow trees') if g.get('id').startswith('meadow tree ')]
    for (kind, x, base, w), g in zip(landscape.meadow_trees(), drawn):
        assert g[0].get('id').startswith({'cypress': 'cypress', 'bush': 'ball bush'}[kind]), g.get('id')


def test_a_ball_bush_is_wider_than_tall():
    svg = Svg()
    landscape.ball_bush(svg, landscape.random.Random(1), 200, 300, 120, 1.0)
    root = ET.fromstring('<svg xmlns="%s">%s</svg>' % (svgtools.SVG_NS, '\n'.join(svg.parts)))
    x0, y0, x1, y1 = svgtools.element_bbox(group(root, 'ball bush'))
    assert x1 - x0 > (y1 - y0) * 1.2 and y1 <= 300 + 5   # bboxes come from curve control points, a little outside the circles


def test_a_row_of_bushes_lines_the_near_shore(village):
    x0, y0, x1, y1 = svgtools.element_bbox(group(village, 'shore bushes'))
    assert x0 <= landscape.MEADOW_SHORE[0] + 40 and x1 >= landscape.MEADOW_SHORE[1] - 40
    assert y1 < landscape.meadow_top(800) + 60


def test_a_meadow_cypress_is_a_cone_of_leaf_balls_widest_at_its_foot():
    svg = Svg()
    landscape.cone_cypress(svg, landscape.random.Random(1), 200, 400, 60, 180, 1.0)
    root = ET.fromstring('<svg xmlns="%s">%s</svg>' % (svgtools.SVG_NS, '\n'.join(svg.parts)))
    balls = [svgtools.element_bbox(p) for p in root.iter() if (p.get('id') or '').startswith('ball shade')]
    def width(y0, y1):
        row = [b for b in balls if y0 <= (b[1] + b[3]) / 2 < y1]
        return max(b[2] for b in row) - min(b[0] for b in row)
    assert width(220, 280) < width(340, 400) * 0.6
    x0, y0, x1, y1 = svgtools.element_bbox(group(root, 'cypress'))
    assert y0 >= 220 - 5 and y1 <= 400 + 5


def test_daisies_are_strewn_across_the_meadow(village):
    x0, y0, x1, y1 = svgtools.element_bbox(group(village, 'daisies'))
    assert x1 - x0 > WIDTH * 0.6 and y0 > landscape.MEADOW_FAR


def test_two_rocks_lie_in_the_foreground(village):
    rocks = [g for g in group(village, 'rocks') if g.get('id').startswith('rock')]
    assert len(rocks) == 2
    assert all(svgtools.element_bbox(r)[1] > HEIGHT * 0.85 for r in rocks)


def test_tall_grass_grows_along_the_bottom_edge(village):
    x0, y0, x1, y1 = svgtools.element_bbox(group(village, 'tall grass'))
    assert y1 >= HEIGHT - 5 and x1 - x0 > WIDTH * 0.8


# ---------------------------------------------------------------- the lake's reflections and glints

@pytest.mark.parametrize('x, y', [(700, 500), (200, 530), (1300, 510)])
def test_mid_lake_is_open_water(x, y):
    assert landscape.on_open_water(x, y)


@pytest.mark.parametrize('x, y', [(700, 420), (100, 470), (1400, 480), (800, 560), (700, 456)])
def test_hills_their_sand_and_the_near_meadow_are_not_open_water(x, y):
    assert not landscape.on_open_water(x, y)


def inside(pts, x, y):
    hit = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def lightness(colour):
    return sum(int(colour[i:i + 2], 16) for i in (1, 3, 5))


def shore_hills():
    return [(name, bottom) for name, _, bottom, _, _, (_, sand) in landscape.HILLS if sand]


@pytest.mark.parametrize('name, bottom', shore_hills())
def test_each_shore_is_reflected_in_a_darker_band_on_the_water_just_under_its_waterline(name, bottom):
    shape, colour = landscape.reflections()[name]
    assert lightness(colour) < lightness(landscape.LAKE_COLOURS[0])
    xs = [x for x in range(int(bottom[0][0]) + 20, int(bottom[-1][0]) - 20, 10)
          if landscape.on_open_water(x, landscape.curve_y(bottom, x) + 8)]
    assert xs, name
    for x in xs:
        assert inside(shape, x, landscape.curve_y(bottom, x) + 8), (name, x)


@pytest.mark.parametrize('name, bottom', shore_hills())
def test_a_reflection_hangs_from_its_waterline_no_further_than_a_shore_tree_is_tall(name, bottom):
    shape, _ = landscape.reflections()[name]
    for x, y in shape:
        assert -0.5 <= y - landscape.curve_y(bottom, x) <= 30, (name, x, y)


@pytest.fixture(scope='module')
def glints():
    return landscape.glints()


def test_the_lake_has_two_sets_of_glints_to_twinkle_in_turn(glints):
    a, b = glints
    assert len(a) > 40 and len(b) > 40


def test_every_glint_lies_on_open_water(glints):
    for x0, y, x1, _ in glints[0] + glints[1]:
        for x in (x0, (x0 + x1) / 2, x1):
            assert landscape.on_open_water(x, y), (x, y)


def test_glints_are_longer_and_thicker_nearer_the_viewer(glints):
    every = sorted(glints[0] + glints[1], key=lambda g: g[1])
    far, near = every[:len(every) // 3], every[-len(every) // 3:]
    assert sum(g[2] - g[0] for g in near) / len(near) > 1.3 * sum(g[2] - g[0] for g in far) / len(far)
    assert sum(g[3] for g in near) / len(near) > sum(g[3] for g in far) / len(far)


def test_the_glints_are_drawn_as_their_own_images_apart_from_the_landscape():
    parts = landscape.cut()
    assert {'shimmer a', 'shimmer b'} <= set(parts)
    root = ET.fromstring(parts['background'].svg)
    assert not [i for i in ids(root) if 'glint' in i and 'shore' not in i]


# The mountains are the one generator every scene's peaks come from: a range may carry its own snowcap as a
# seventh item, a snowcap layer given as None is left out, and shaded snow may be flat facets as well as wedges.
def mountain_svg(ranges, **kw):
    svg = Svg()
    landscape.mountains(svg, ranges, snowy=None, **kw)
    return ET.fromstring('<svg xmlns="%s">%s</svg>' % (svgtools.SVG_NS, '\n'.join(svg.parts)))


CAP = (None, ('#c6dafa', [[(100, 50), (104, 80), (90, 60)]]), ('#fffdf4', [[(100, 50), (130, 70), (110, 75)]]), None)


def test_a_range_carrying_its_own_snowcap_wears_it():
    ranges = [('capped', '#7eb1f9', '#2290e8', [(0, 100), (100, 50), (200, 100)], [], [], CAP),
              ('bare', '#7eb1f9', '#2290e8', [(0, 100), (100, 50), (200, 100)], [], [])]
    root = mountain_svg(ranges, foot=200)
    assert group(root, 'capped').find(".//*[@id='snow peak']") is not None
    assert group(root, 'bare').find(".//*[@id='snow peak']") is None


def test_a_snowcap_layer_given_as_none_is_left_out():
    ranges = [('capped', '#7eb1f9', '#2290e8', [(0, 100), (100, 50), (200, 100)], [], [], CAP)]
    assert {i for i in ids(mountain_svg(ranges, foot=200)) if 'snow' in i or 'rock' in i} == {'snow peak', 'snow shade', 'snow'}


def test_shaded_snow_may_be_flat_facets_as_well_as_wedges():
    ranges = [('capped', '#7eb1f9', '#2290e8', [(0, 100), (100, 50), (200, 100)], [], [], CAP)]
    shade = mountain_svg(ranges, foot=200).find(".//*[@id='snow shade']")
    assert shade.get('d') == landscape.poly(CAP[1][1][0])

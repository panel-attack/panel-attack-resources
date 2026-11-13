import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import xml.etree.ElementTree as ET

import conftest
import pytest

from common.painting import WIDTH, Svg
from scene_export import cutting, svgtools
from scenery import alps, landscape, spring_peaks, spring_valley, valley


# The day valley's sheets as they were before the train meadow was drawn beside them: its generators are reused, not
# changed, so their output stays byte for byte what it was.
DAY_VALLEY_SHEETS = {'valley': '978ee949a59f6a339fbe404b309ddb7c1eba9a2d6ecaa8649d48c51756b2a26e',
                     'alps': '241eca281821ca7acb0387594c26b92cadfeea72bb0e38a37bc4cf242a574f8f'}


def written_hash(module, tmp_path, monkeypatch):
    monkeypatch.setattr(cutting, 'SHEETS', str(tmp_path))
    module.main()
    path = cutting.sheet_path('scenery/' + module.__name__.split('.')[-1] + '.svg')
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


@pytest.mark.parametrize('name, module', [('valley', valley), ('alps', alps)])
def test_the_day_valleys_sheets_are_what_they_were(name, module, tmp_path, monkeypatch):
    assert written_hash(module, tmp_path, monkeypatch) == DAY_VALLEY_SHEETS[name]


@pytest.fixture(scope='module')
def land():
    svg = Svg()
    spring_valley.spring_valley(svg)
    return ET.fromstring('<svg xmlns="%s">%s</svg>' % (svgtools.SVG_NS, '\n'.join(svg.parts)))


@pytest.fixture(scope='module')
def peaks():
    svg = Svg()
    spring_peaks.spring_peaks(svg)
    return ET.fromstring('<svg xmlns="%s">%s</svg>' % (svgtools.SVG_NS, '\n'.join(svg.parts)))


@pytest.mark.parametrize('x', [-40, 0, 400, 768, 1200, WIDTH, 1576])
def test_the_rail_tops_are_level_at_517_across_the_sheet_and_beyond(x):
    assert spring_valley.rail_top(x) == spring_valley.RAIL_TOP == 517


def test_the_rail_top_is_drawn_as_one_level_line_past_both_sides(land):
    rail = cutting.find_group(land, 'track').find(".//*[@id='rail top']")
    x0, y0, x1, y1 = svgtools.element_bbox(rail)
    assert x0 <= -40 and x1 >= WIDTH + 40
    assert y0 == pytest.approx(spring_valley.RAIL_TOP, abs=0.01)


def test_the_track_runs_level_the_whole_width(land):
    x0, y0, x1, y1 = svgtools.element_bbox(cutting.find_group(land, 'track'))
    assert x0 <= -40 and x1 >= WIDTH + 40
    assert y0 <= spring_valley.RAIL_TOP < y1


def test_every_land_image_reaches_past_the_sheets_sides(land):
    for g in cutting.find_group(land, 'Spring Valley'):
        if g.get('id') in spring_valley.SPANS_THE_LAND:
            x0, y0, x1, y1 = svgtools.element_bbox(g)
            assert x0 <= 0 and x1 >= WIDTH, g.get('id')


def test_the_meadow_runs_down_past_the_sheets_bottom(land):
    x0, y0, x1, y1 = svgtools.element_bbox(cutting.find_group(land, 'meadow'))
    assert y1 >= 1024


def test_the_bushes_stand_in_front_of_the_track_above_the_meadow_flowers(land):
    x0, y0, x1, y1 = svgtools.element_bbox(cutting.find_group(land, 'bushes'))
    assert y0 > spring_valley.RAIL_TOP and 520 <= y0 <= 560 and 595 <= y1 <= 625   # bboxes include arc control points


def test_the_hills_are_drawn_back_to_front_as_separate_images(land):
    names = [g.get('id') for g in cutting.find_group(land, 'Spring Valley')]
    assert names.index('hills far') < names.index('hills middle') < names.index('track') < names.index('bushes') \
        < names.index('meadow')


def test_the_big_peaks_summit_is_near_the_references(peaks):
    x0, y0, x1, y1 = svgtools.element_bbox(cutting.find_group(peaks, 'massif'))
    assert y0 == pytest.approx(160, abs=8) and x0 < 965 < x1


# The track is the reference's seen edge on, nothing more: one thin dark line, a thicker blue-grey band for the
# metal under it, and under that one row of boards, their lit ends an on-off dash pattern on the dark between them.
def track_band(land, name):
    return svgtools.element_bbox(cutting.find_group(land, 'track').find(".//*[@id='%s']" % name))


def test_the_rail_is_a_thin_dark_line_over_a_thicker_grey_band(land):
    line, metal = track_band(land, 'rail top'), track_band(land, 'rail head')
    assert line[1] == spring_valley.RAIL_TOP and line[3] - line[1] <= 2
    assert metal[1] == line[3] and metal[3] - metal[1] >= 1.5 * (line[3] - line[1])
    assert metal[3] - metal[1] <= 5


def test_the_track_has_no_far_rail_ballast_or_shoulders(land):
    ids = [p.get('id', '') for p in cutting.find_group(land, 'track').iter()]
    assert not [i for i in ids if i.startswith(('far rail', 'ballast', 'far shoulder', 'near shoulder', 'bed edge', 'tie end'))]


def test_one_row_of_boards_lies_under_the_metal_as_an_on_off_pattern(land):
    track = cutting.find_group(land, 'track')
    metal, between = track_band(land, 'rail head'), track_band(land, 'between the boards')
    boards = [svgtools.element_bbox(p) for p in track.iter() if p.get('id', '').split(' ')[0] == 'sleeper']
    assert between[1] == metal[3] and len(boards) > 40
    top, bottom, width, pitch = spring_valley.ref.SLEEPERS[:4]
    assert between[3] - between[1] == pytest.approx(bottom - top, abs=0.06)
    for x0, y0, x1, y1 in boards:
        assert (y0, y1) == (between[1], between[3])
        assert x1 - x0 == pytest.approx(width, abs=0.06)
    lefts = sorted(x0 for x0, _, _, _ in boards)
    assert all(b - a == pytest.approx(pitch, abs=0.06) for a, b in zip(lefts, lefts[1:]))
    assert width < pitch - width


# The land in front of the mountains reads as the reference's: the woods are rows of small tree crowns, not a few
# domes; a bush's silhouette is a leafy clump of many small scallops round its lobes; the hills have shaded hollows
# as well as lit planes; the hedge of near bushes mixes big and small bushes.
def test_the_woods_are_rows_of_small_tree_crowns(land):
    trees = [p for p in cutting.find_group(land, 'woods').iter() if p.get('id', '').startswith('tree')]
    assert len(trees) >= 60
    for p in trees:
        x0, y0, x1, y1 = svgtools.element_bbox(p)
        assert x1 - x0 <= 60, p.get('id')


def test_a_bush_silhouette_is_a_leafy_clump_of_scallops():
    import random
    circles = spring_valley.bush_silhouette(300, 600, 200, 70, random.Random(1))
    radii = sorted(r for _, _, r in circles)
    assert len(circles) >= 3 * spring_valley.ref.BUSH_LOBES
    assert radii[-1] / radii[0] >= 3


def test_the_middle_hill_has_shaded_hollows_as_well_as_lit_planes(land):
    ids = [p.get('id', '') for p in cutting.find_group(land, 'hills middle').iter()]
    assert any(i.startswith('shade plane') for i in ids)
    assert any(i.startswith('lit plane') for i in ids)


def test_the_near_hedge_mixes_big_and_small_bushes():
    heights = [h for _, _, _, h in spring_valley.ref.BUSHES_NEAR]
    assert max(heights) / min(heights) >= 2


# The far hills are rolling grass fading into the distance, not rock: rounded crests with soft lit caps and soft
# shaded slopes, no hard-edged facets, and copses on them for scale.
@pytest.mark.parametrize('name', ['hills far', 'hills far left', 'hills far centre', 'hills far right'])
def test_a_far_hill_has_no_angular_facets(land, name):
    ids = [p.get('id', '') for p in cutting.find_group(land, name).iter()]
    assert not [i for i in ids if i.startswith(('fold', 'lit fold'))]


def test_copses_stand_on_the_farthest_hill():
    assert any(hill == 'hills far' for _, _, hill, _, _, _, _ in spring_valley.ref.WOODS)


# The peaks meet the green hills as in the reference: their rock keeps its blue down to its foot and the foothills
# in front are no more than a thin band of distant hills under the far hills' crests.
def test_the_foothills_are_a_thin_band_under_the_far_hills(peaks):
    x0, y0, x1, y1 = svgtools.element_bbox(cutting.find_group(peaks, 'Foothills'))
    assert y0 >= 362


def test_the_peaks_rock_stays_blue_at_its_foot():
    assert spring_peaks.ref.HAZE[1] <= 0.4


# The open meadow under the track is not one flat green: lighter and darker swathes roll across the band behind the
# bushes, tufts of grass stand scattered over it, and drifts of small pink and white flowers speckle it.
def test_swathes_roll_across_the_meadow_behind_the_bushes(land):
    ids = [p.get('id', '') for p in cutting.find_group(land, 'track').iter()]
    assert len([i for i in ids if i.startswith('swathe')]) >= 3


def test_tufts_and_flower_drifts_are_scattered_over_the_meadow(land):
    for group in ('track', 'meadow'):
        ids = [p.get('id', '') for p in cutting.find_group(land, group).iter()]
        assert len([i for i in ids if i.startswith('tuft')]) >= 20, group
        assert len([i for i in ids if i.startswith('drift')]) >= 6, group


# The peaks are drawn by the terrace's mountain generator alone (scenery/landscape.py): their rock, lit planes,
# gullies and snowcaps are all its, given the train meadow's shapes, so spring_peaks draws no snow of its own.
def test_every_peaks_snowcap_is_drawn_by_the_terraces_generator(monkeypatch):
    capped = []
    monkeypatch.setattr(landscape, 'snowcap', lambda svg, *cap: capped.append(cap))
    svg = Svg()
    spring_peaks.spring_peaks(svg)
    snowy = [rng for _, _, ranges in spring_peaks.IMAGES for rng in ranges if len(rng) > 6]
    assert capped == [rng[6] for rng in snowy]
    assert not any('snow' in part for part in svg.parts)


# The near bushes are not one bush repeated, as in the reference: a wide dome of many leafy bumps, small clumps of two
# or three, low mounds and tall ones, each with bumps of uneven size.
def near_bushes(land):
    return [g for g in cutting.find_group(land, 'bushes') if g.get('id', '').startswith('bush')]


def lobes_of(bush):
    return [p for p in bush if p.get('id', '').split(' ')[0] == 'lobe']


def test_the_near_bushes_differ_in_how_many_lobes_they_have(land):
    assert len({len(lobes_of(b)) for b in near_bushes(land)}) >= 3


def test_a_wide_near_bush_has_bumps_of_uneven_size(land):
    widest = max(near_bushes(land), key=lambda b: svgtools.element_bbox(b)[2] - svgtools.element_bbox(b)[0])
    bumps = [p for p in widest if p.get('id', '').split(' ')[0] == 'lit']   # each bump's lit cap, its own size
    widths = [svgtools.element_bbox(p)[2] - svgtools.element_bbox(p)[0] for p in bumps]
    assert len(widths) >= 4 and max(widths) / min(widths) >= 1.5


def test_the_near_bushes_range_from_low_mounds_to_tall_domes():
    shapes = [h / w for _, _, w, h in spring_valley.ref.BUSHES_NEAR]
    assert max(shapes) / min(shapes) >= 1.8


def test_a_near_bush_is_outlined_only_round_its_whole_silhouette(land):
    for b in near_bushes(land):
        assert len([p for p in b if p.get('id', '').split(' ')[0] == 'outline']) == 1, b.get('id')


# The near bushes are shaded like the reference's: a yellow-green highlight on the lobes to the upper right of each
# bush, and the small bushes a step lighter than the big ones. They stand as separate mounds with meadow between the
# small ones, no two neighbours the same size, and their feet staggered up and down the slope.
def part_named(bush, name):
    return [p for p in bush if p.get('id', '').split(' ')[0] == name]


def lightness(colour):
    return sum(int(colour[k:k + 2], 16) for k in (1, 3, 5))


def test_a_near_bush_has_a_yellow_green_highlight_to_its_upper_right(land):
    for b in near_bushes(land):
        x0, y0, x1, y1 = svgtools.element_bbox(part_named(b, 'outline')[0])
        lights = part_named(b, 'highlight')
        assert lights, b.get('id')
        for p in lights:
            r, g, bl = (int(p.get('fill')[k:k + 2], 16) for k in (1, 3, 5))
            assert r > bl and g > r
            hx0, hy0, hx1, hy1 = svgtools.element_bbox(p)
            assert (hx0 + hx1) / 2 > (x0 + x1) / 2 - (x1 - x0) * 0.1 and (hy0 + hy1) / 2 < (y0 + y1) / 2


def test_the_smallest_near_bush_is_lighter_than_the_biggest(land):
    def size(b):
        x0, y0, x1, y1 = svgtools.element_bbox(b)
        return (x1 - x0) * (y1 - y0)
    bushes = sorted(near_bushes(land), key=size)
    assert lightness(part_named(bushes[0], 'mass')[0].get('fill')) > lightness(part_named(bushes[-1], 'mass')[0].get('fill'))


def test_the_small_near_bushes_stand_apart_with_meadow_between():
    placed = sorted(spring_valley.ref.BUSHES_NEAR)
    for k, (x, _, w, _) in enumerate(placed):
        if w < 90:
            gaps = [abs(x - ox) - (w + ow) / 2 for j, (ox, _, ow, _) in enumerate(placed) if j != k]
            assert min(gaps) >= 20, x


def test_no_two_neighbouring_near_bushes_are_the_same_size():
    placed = sorted(spring_valley.ref.BUSHES_NEAR)
    for (_, _, w0, h0), (x, _, w1, h1) in zip(placed, placed[1:]):
        assert max(w0 * h0, w1 * h1) / min(w0 * h0, w1 * h1) >= 1.6, x


def test_the_near_bushes_feet_are_staggered():
    feet = [foot for _, foot, _, _ in spring_valley.ref.BUSHES_NEAR]
    assert max(feet) - min(feet) >= 10


def lowest_point(path):
    """The lowest y a path's curve passes through: its segments' end points, not the arcs' control points."""
    ys = []
    for cmd, nums in svgtools._segments(path.get('d')):
        if cmd == 'V':
            ys += nums
        elif cmd not in ('H', 'Z'):
            ys += nums[1::2] if cmd != 'C' else nums[5::6]
    return max(ys)


def test_a_near_bush_stands_on_a_flat_dark_foot_over_its_outline(land):
    for b in near_bushes(land):
        ids = [p.get('id', '') for p in b]
        foot, = part_named(b, 'foot')
        outline, = part_named(b, 'outline')
        assert ids.index(foot.get('id')) > ids.index(outline.get('id'))
        assert lowest_point(foot) >= lowest_point(outline) + float(outline.get('stroke-width')) / 2


# The land's outlines are the Esme terrace's: every line a dark shade of its own shape's colour, none near-black or a
# navy ink, none thicker than the terrace's near lines; the hills, the woods on them and the bushes behind the track
# stand with no outline at all, parted by shade as the terrace's distant trees and hills are, while the near bushes
# keep a thin tinted line as wide as the terrace's at the train's distance.
@pytest.fixture(scope='module')
def sheet():
    svg = Svg()
    spring_valley.spring_valley(svg)
    return conftest.sheet_of(svg)


def test_every_outline_is_a_dark_shade_of_its_own_shapes_colour(sheet):
    for ident, line, _, fills in conftest.outlines(*sheet):
        assert any(conftest.is_shade_of(line, fill) for fill in fills), (ident, line, sorted(fills))


def test_every_outline_is_as_thin_as_the_terraces(sheet):
    lo, hi = conftest.ESME_LINE_WIDTHS
    for ident, _, width, _ in conftest.outlines(*sheet):
        assert lo <= width <= hi, (ident, width)


@pytest.mark.parametrize('name', ['hills far', 'hills far left', 'hills far centre', 'hills far right', 'hills middle',
                                  'woods', 'bushes far'])
def test_the_distant_land_has_no_outline(land, name):
    assert not [p for p in cutting.find_group(land, name).iter() if p.get('stroke')]


def test_the_near_bushes_keep_a_line_as_wide_as_the_terraces_at_the_trains_distance(land):
    from structures.houses import TOWN_LINE_WIDTH
    strokes = [p for p in cutting.find_group(land, 'bushes').iter() if p.get('id', '').startswith('outline')]
    assert len(strokes) == len(spring_valley.ref.BUSHES_NEAR)
    assert all(float(p.get('stroke-width')) == TOWN_LINE_WIDTH for p in strokes)


def test_an_outline_keeps_its_shapes_hue_and_saturation_and_darkens_it():
    for colour in ('#05697a', '#cdb4ae', '#4ec48a'):
        h, s, v = conftest.hsv(colour)
        lh, ls, lv = conftest.hsv(spring_valley.edge_of(colour))
        assert abs(lh - h) < 0.01 and abs(ls - s) < 0.02 and lv == pytest.approx(v * 0.7, abs=0.01)


# The tree line is a mixed wood, not a row of balls: a crown is one of several silhouettes, round, lumpy broadleaf,
# wide flat-topped, pointed fir, tall narrow poplar or low shrub, drawn from the same circle unions, and every clump's
# front row mixes tall narrow crowns with wide low ones.
def crown_of(shape, w=20, h=18):
    import random
    return spring_valley.crown(100, 400, w, h, random.Random(shape), shape)


def crown_box(circles):
    return (min(cx - r for cx, _, r in circles), min(cy - r for _, cy, r in circles),
            max(cx + r for cx, _, r in circles), max(cy + r for _, cy, r in circles))


def test_the_woods_crowns_come_in_several_shapes():
    assert {'round', 'lumpy', 'flat', 'fir', 'poplar', 'shrub'} <= set(spring_valley.ref.CROWN_SHAPES)


def test_a_fir_crown_tapers_to_a_point_at_its_top():
    circles = crown_of('fir')
    tip = min(circles, key=lambda c: c[1] - c[2])
    assert tip[2] <= 0.25 * max(r for _, _, r in circles)
    x0, y0, x1, y1 = crown_box(circles)
    assert (y1 - y0) / (x1 - x0) >= 1.5


def test_a_poplar_crown_is_more_than_twice_as_tall_as_it_is_wide():
    x0, y0, x1, y1 = crown_box(crown_of('poplar'))
    assert (y1 - y0) / (x1 - x0) >= 2


def test_a_flat_crown_is_wider_than_tall_with_a_level_top():
    circles = crown_of('flat')
    x0, y0, x1, y1 = crown_box(circles)
    assert (x1 - x0) / (y1 - y0) >= 1.3
    tops = sorted(cy - r for _, cy, r in circles)[:3]
    assert tops[-1] - tops[0] <= 0.1 * (y1 - y0)


def test_a_shrub_is_low_and_wide():
    x0, y0, x1, y1 = crown_box(crown_of('shrub'))
    assert (x1 - x0) / (y1 - y0) >= 1.6


def test_a_lumpy_crown_is_not_symmetric_about_its_middle():
    circles = crown_of('lumpy')
    x0, y0, x1, y1 = crown_box(circles)
    top = min(circles, key=lambda c: c[1] - c[2])
    assert abs(top[0] - (x0 + x1) / 2) >= 0.1 * (x1 - x0)


def test_every_clump_of_the_woods_mixes_tall_narrow_and_wide_low_crowns(land):
    for clump in cutting.find_group(land, 'woods'):
        shapes = []
        for p in clump.iter():
            if p.get('id', '').startswith('body'):
                x0, y0, x1, y1 = svgtools.element_bbox(p)
                shapes.append((y1 - y0) / (x1 - x0))
        assert min(shapes) <= 0.9 and max(shapes) >= 1.5, clump.get('id')


# The far bushes are not all the same arched row of lobes: a bush's top follows one of several profiles, an arch, a
# flat hedge top, a hump to one side, or an arch with a pointed spire of a young conifer rising out of it, and the
# bushes behind the track use all of them.
def far_bush_tops(profile, w=200, h=40):
    import random
    top, _ = spring_valley.bush_lobes(300, 600, w, h, random.Random(profile), profile)
    return [min(cy - r for _, cy, r in lobe) for lobe in top]


def test_a_flat_bush_has_a_level_top():
    tops = far_bush_tops('flat')
    assert max(tops) - min(tops) <= 0.2 * 40


def test_a_humped_bush_is_tallest_toward_one_end():
    for profile in ('humped left', 'humped right'):
        tops = far_bush_tops(profile)
        k = tops.index(min(tops))
        assert k < len(tops) / 3 if profile == 'humped left' else k >= 2 * len(tops) / 3, profile


def test_a_spired_bush_has_one_lobe_taller_than_it_is_wide():
    import random
    top, _ = spring_valley.bush_lobes(300, 600, 200, 40, random.Random('spired'), 'spired')
    shapes = []
    for lobe in top:
        x0, y0, x1, y1 = crown_box(lobe)
        shapes.append((y1 - y0) / (x1 - x0))
    assert max(shapes) >= 1.4 and min(shapes) <= 1.0


def test_the_bushes_behind_the_track_use_every_profile():
    import random
    profiles = spring_valley.bush_profiles(len(spring_valley.ref.BUSHES_FAR), random.Random(1))
    assert set(profiles) == set(spring_valley.ref.BUSH_PROFILES)


# The near bushes' mounds are not all one dome with its crown near the middle: a mound's top follows one of several
# profiles too, a dome, a flat hedge, a hump to the left or right, a saddle with two crowns, and a few leafy tips
# stand up pointed out of the bumps.
def mound_tops(profile, w=180, h=70):
    import random
    bumps = spring_valley.mound_bumps(300, 600, w, h, random.Random(profile), profile)
    return [600 - (bump[1] - bump[2]) for bump, _ in bumps]


def test_a_humped_mound_is_tallest_toward_that_end():
    for profile, side in (('humped left', 0), ('humped right', 1)):
        tops = mound_tops(profile)
        k = tops.index(max(tops))
        assert (k < len(tops) / 3) if side == 0 else (k >= 2 * len(tops) / 3), profile


def test_a_saddle_mound_has_two_crowns_with_a_dip_between():
    tops = mound_tops('saddle')
    n = len(tops)
    left, right = max(tops[:n // 3]), max(tops[2 * n // 3:])
    assert min(tops[n // 3:2 * n // 3]) < min(left, right) * 0.85


def test_a_flat_mound_has_a_level_top_across_its_middle():
    tops = mound_tops('flat')
    n = len(tops)
    middle = tops[n // 4:n - n // 4]
    assert max(middle) - min(middle) <= 0.15 * 70


def test_the_near_bushes_use_every_mound_profile():
    import random
    profiles = spring_valley.bush_profiles(len(spring_valley.ref.BUSHES_NEAR), random.Random(1),
                                           spring_valley.ref.MOUND_PROFILES)
    assert set(profiles) == set(spring_valley.ref.MOUND_PROFILES)


def test_some_near_bush_bumps_carry_a_pointed_tip(land):
    assert any(p.get('id', '').startswith('tip') for b in near_bushes(land) for p in b.iter())

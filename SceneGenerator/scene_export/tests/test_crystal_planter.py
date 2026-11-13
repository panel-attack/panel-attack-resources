import math
import random
import re

import numpy as np
import pytest

from scene_export import GENERATOR  # noqa: F401
from furniture import planters


@pytest.fixture(scope='module')
def paths():
    out = planters.Out()
    planters.crystal_planter(out, planters.SCENE)
    return {m.group(1): m.group(0) for line in out.body for m in [re.search(r'<path id="([^"]+)"[^>]*>', line)] if m}


def attr(path, name):
    m = re.search(r' %s="([^"]+)"' % name, path)
    return m and m.group(1)


def area(pts):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def luminance(colour):
    r, g, b = (int(colour[k:k + 2], 16) for k in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b


def test_the_crystals_carry_no_white_strips_or_star_glints(paths):
    assert not [k for k in paths if re.fullmatch(r'(big|left|right) crystal .*(sheen|highlight|glare|glint).*', k)]


def test_the_bodys_stones_are_outlined_by_seams_darker_than_the_stones(paths):
    cells = [p for k, p in paths.items() if k.startswith('body marble cells ')]
    assert cells
    for p in cells:
        assert attr(p, 'stroke') and luminance(attr(p, 'stroke')) < luminance(attr(p, 'fill'))


def test_the_bodys_stones_have_no_streaked_highlights_or_veins(paths):
    assert not [k for k in paths if k.startswith(('body marble highlights', 'body marble veins'))]


def test_a_three_colour_gradient_is_written_with_its_middle_colour_halfway(tmp_path):
    out = planters.Out()
    out.gradients['three'] = ('#000000', '#111111', '#222222')
    out.write(str(tmp_path / 'three.svg'))
    svg = (tmp_path / 'three.svg').read_text()
    assert '<stop offset="0.5" stop-color="#111111"/><stop offset="1" stop-color="#222222"/>' in svg


def test_the_big_crystal_shows_two_side_faces_with_no_sliver_beside_them(paths):
    assert sorted(k for k in paths if re.fullmatch(r'big crystal side \d+', k)) == ['big crystal side 1',
                                                                                   'big crystal side 2']


def test_the_right_crystals_front_shoulder_sits_well_below_its_side_shoulders():
    rig, _ = planters.CRYSTAL_FIT
    _, b, axis, radius, length, _, rot, _, shoulders, _ = next(q for q in planters.crystal_bases(rig.c)
                                                               if q[0] == 'right crystal')
    a, e1, e2 = planters.frame(np.asarray(axis, float))
    tops = []
    for k in range(6):
        t = math.radians(rot + 60 * k)
        top = b + radius * (math.cos(t) * e1 + math.sin(t) * e2) + a * length * shoulders[k]
        tops.append((float(np.dot(top - rig.c, rig.eye - rig.c)), rig.project(top)[1]))
    front = max(tops)
    assert all(front[1] >= y + 8 for d, y in tops if d != front[0] and d > 0.5)


def test_the_bodys_flagstones_tile_the_band_without_overlapping():
    stones = planters.flagstones(random.Random(7))
    covered = sum(area(s) for s in stones)
    band = 180 * planters.MARBLE_ASPECT
    assert 0.85 * band <= covered <= band
    assert len(stones) >= 12


def test_the_big_crystals_point_is_its_two_front_facets_with_no_sliver_on_its_shoulder(paths):
    assert sorted(k for k in paths if re.fullmatch(r'big crystal tip \d+', k)) == ['big crystal tip 1',
                                                                                  'big crystal tip 2']


def gem_frame_band():
    """The gem's gold frame in the band's (degrees, share of the body height): centre and half sizes."""
    rig, R = planters.CRYSTAL_FIT
    (hb0, _), (hr0, _), (_, rr1) = R['body bottom'], R['rim bottom'], R['rim top']
    gem_r = lambda h: rr1 + planters.GEM_FRAME_STANDOFF + 0.002
    _, _, fw, fhh = planters.diamond_uv(rig, gem_r, planters.T.CRYSTAL_GEM_FRAME)
    gu, gh = planters.diamond_uv(rig, gem_r, planters.T.CRYSTAL_GEM)[:2]
    span = hr0 - hb0
    return math.degrees(gu / rr1), (gh - hb0) / span, math.degrees(fw / rr1), fhh / span


def near_line(p, line, reach):
    """Whether p is within reach degrees of the polyline, heights counted in degrees as the stones are."""
    k = np.array([1.0, planters.MARBLE_ASPECT])
    for a, b in zip(line, line[1:]):
        a, b, q = np.array(a) * k, np.array(b) * k, np.array(p) * k
        t = max(0.0, min(1.0, np.dot(q - a, b - a) / np.dot(b - a, b - a)))
        if np.linalg.norm(q - (a + t * (b - a))) <= reach:
            return True
    return False


def test_every_gold_strap_ends_on_gold_with_no_cut_end_left_on_the_stone():
    cd, cf, hw, hh = gem_frame_band()
    lines = {'arch': planters.TRIM_ARCH, 'swag': planters.TRIM_SWAG, 'low': planters.TRIM_LOW}
    for name, line in lines.items():
        for d, f in (line[0], line[-1]):
            on_gold = (f <= 0 or f >= 1 or abs(d) >= planters.TRIM_POST[0]
                       or abs(d - cd) / hw + abs(f - cf) / hh <= 0.95
                       or any(near_line((d, f), other, 0.6) for o, other in lines.items() if o != name))
            assert on_gold, (name, (d, f))


def straps(side):
    _, R = planters.CRYSTAL_FIT
    body = planters.profile(R, ('body bottom', 'body top'))
    h0, h1 = R['body bottom'][0], R['rim bottom'][0]
    return h0, {name: band for name, band, _ in planters.trim_straps(body, h0, h1, side)}


@pytest.mark.parametrize('side', [-1, 1])
def test_no_strap_hangs_past_the_bodys_foot_onto_the_plinth(side):
    h0, bands = straps(side)
    for name, band in bands.items():
        assert min(h for _, h in band) >= h0 - 1e-9, name


@pytest.mark.parametrize('side', [-1, 1])
def test_the_strap_sags_clear_of_the_bodys_foot_between_the_gem_and_the_arch(side):
    h0, bands = straps(side)
    _, R = planters.CRYSTAL_FIT
    reach = math.radians(40) * planters.profile(R, ('body bottom', 'body top'))(h0)
    sag = [h for u, h in next(band for name, band in bands.items() if name.startswith('strap')) if abs(u) < reach]
    assert sag and min(sag) > h0 + 0.003


def test_two_overlapping_squares_join_into_one_outline_of_their_combined_area():
    outlines = planters.union([[(0, 0), (1, 0), (1, 1), (0, 1)], [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]])
    assert len(outlines) == 1
    assert area(outlines[0]) == pytest.approx(1.75, rel=0.01)


def test_each_sides_straps_and_post_are_one_gold_path_with_its_own_outline(paths):
    for side in ('left', 'right'):
        gold = paths['trim gold %s' % side]
        assert attr(gold, 'stroke') and attr(gold, 'fill')
        assert gold.count('M') == 1
        loose = [k for k in paths if re.fullmatch(r'trim (outline|low strap|arch|swag|post) %s' % side, k)]
        assert loose == []


def test_a_strap_keeps_its_full_width_round_a_sharp_corner():
    band = planters.strap([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)], 0.2)
    assert any(math.dist(v, (1.1, -0.1)) < 1e-9 for v in band)


def test_the_low_strap_rises_into_the_arch_and_over_its_sharp_peak_down_to_the_foot():
    low, arch = planters.TRIM_LOW, planters.TRIM_ARCH
    assert low[-1] == arch[0]
    k = np.array([1.0, planters.MARBLE_ASPECT])
    back = (np.array(low[-2]) - np.array(low[-1])) * k
    down = (np.array(arch[1]) - np.array(arch[0])) * k
    assert np.dot(back, down) / np.linalg.norm(back) / np.linalg.norm(down) > math.cos(math.radians(120))
    assert arch[-1][1] <= 0 and abs(arch[-1][0]) >= 55


def test_each_side_has_one_strap_and_one_swag_each_with_a_sheen(paths):
    for side in ('left', 'right'):
        assert {'trim strap %s sheen' % side, 'trim swag %s sheen' % side} <= set(paths)
        assert not [k for k in paths if re.fullmatch(r'trim (arch|low strap) %s.*' % side, k)]


def test_the_golds_outline_bends_round_the_pot_with_no_long_straight_chords(paths):
    for side in ('left', 'right'):
        nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', attr(paths['trim gold %s' % side], 'd'))]
        pts = list(zip(nums[0::2], nums[1::2]))
        assert max(math.dist(a, b) for a, b in zip(pts, pts[1:] + pts[:1])) <= 4.0, side

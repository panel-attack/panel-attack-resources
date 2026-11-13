import random
import xml.etree.ElementTree as ET

import conftest
import pytest
from PIL import ImageChops

from common.painting import Svg
from scene_export import compare, cutting, svgtools
from scenery import mesa, mesa_template


@pytest.fixture(scope='module')
def parts():
    mesa.main()
    return dict(mesa.cut())


def test_the_waterfall_strip_is_one_period_tall(parts):
    assert parts['mesa-waterfall'].box[3] == mesa.FALL_PERIOD


PERIODS = 4          # tall enough that Quick Look renders the drawing pixel for pixel instead of as a padded icon


def test_the_waterfall_strip_tiles_without_a_seam(tmp_path):
    """The water drawn over several periods is the strip stacked: each period is the first again, so the scene can
    repeat the strip top to bottom."""
    svg = Svg()
    mesa.waterfall(svg, random.Random(mesa.SEED + ' waterfall'), periods=PERIODS)
    sheet = tmp_path / 'periods.svg'
    svg.write(str(sheet))
    root = ET.parse(str(sheet)).getroot()
    w, h = mesa.FALL_X[1] - mesa.FALL_X[0], mesa.FALL_PERIOD
    box = (mesa.FALL_X[0], mesa.FALL_TOP, w, PERIODS * h)
    stacked = tmp_path / 'periods-part.svg'
    stacked.write_text(svgtools.part_svg('periods', [cutting.find_group(root, 'waterfall')], {}, box))
    im = compare.render_svg(str(stacked))
    first = im.crop((0, 0, w, h))
    assert first.getchannel('A').getextrema() == (255, 255)
    for k in range(1, PERIODS):
        diff = ImageChops.difference(first, im.crop((0, k * h, w, (k + 1) * h))).convert('L')
        assert max(diff.getdata()) <= 8, 'period %d differs from the first' % (k + 1)


def test_the_waterfall_hangs_from_the_lower_steps_lip(parts):
    assert parts['mesa-waterfall'].box[1] == mesa.FALL_TOP
    assert mesa.FALL_TOP >= mesa.LOWER_LIP


def test_the_spray_sits_at_the_waterfalls_foot(parts):
    fall, spray = parts['mesa-waterfall'].box, parts['mesa-spray'].box
    assert fall[0] < spray[0] + spray[2] / 2 < fall[0] + fall[2]
    assert spray[1] < mesa.FOOT < spray[1] + spray[3]


def test_the_gear_ring_stands_on_the_upper_step():
    cx, cy = mesa.GEAR_CENTRE
    assert cy + mesa.GEAR_OUTER > mesa.UPPER_LIP - mesa.SHELF[0]
    assert cy - mesa.GEAR_OUTER - mesa.TOOTH_HEIGHT == pytest.approx(mesa.GEAR_TOP)


def test_the_waterfall_template_repeats_and_scrolls_down_one_period_a_loop():
    doc = mesa_template.build()
    fall = next(n for n in doc['drawables'] if n['id'] == 'mesa-waterfall')
    assert fall['wrap'] == 'repeat'
    track, = fall['animationTracks']
    assert track['repeat'] == 'loop'
    step, = track['steps']
    assert step['animateProperties'] == {'scrollY': -mesa.FALL_PERIOD / 2}
    assert step['easeType'] == 'linear'


def test_every_mesa_template_is_only_a_template():
    doc = mesa_template.build()
    assert [n['id'] for n in doc['drawables']] == ['mesa', 'mesa-waterfall', 'mesa-spray', 'mesa-falls-frame']
    assert all(n['templateOnly'] for n in doc['drawables'])


# The land is the reference's: two flat-topped blocks of rock with sheer cliff faces, fluted by vertical columns and
# cracks, and grass only as a thin cap on each top. The cliffs lean back only a little from foot to lip, a wall, not
# a slope.
def test_the_cliffs_drop_sheer_from_lip_to_foot():
    drop = mesa.FOOT - mesa.UPPER_LIP
    assert 0 < mesa.edge_x(mesa.LEFT, mesa.LOWER_LIP, 1) - mesa.edge_x(mesa.LEFT, mesa.FOOT, 1) <= drop / 6
    assert 0 < mesa.edge_x(mesa.RIGHT, mesa.FOOT, -1) - mesa.edge_x(mesa.RIGHT, mesa.UPPER_LIP, -1) <= drop / 6


def land_group(parts):
    root = ET.parse(cutting.sheet_path('scenery/mesa.svg')).getroot()
    grads = {gid: tuple(s.get('stop-color') for s in g) for gid, g in cutting.load('scenery/mesa.svg')[1].items()}
    return root.find(".//*[@id='land']"), grads


def test_the_cliff_faces_are_rock_not_grass(parts):
    """Every colour filled in the land below the caps is the cliffs' rock; none of the grass's."""
    land, grads = land_group(parts)
    fills = conftest.solid_fills(land, grads)
    assert fills
    for fill in fills:
        assert not any(conftest.is_shade_of(fill, g) or fill == g for g in mesa.GRASS.values()), fill
        assert conftest.hsv(fill)[0] > 0.55 or conftest.hsv(fill)[1] < conftest.GREY, fill   # blue through mauve, no green


def test_the_cliffs_are_fluted_with_vertical_columns(parts):
    """Each block's face is cut into columns: many flutes, each much taller than wide, over both blocks."""
    land, _ = land_group(parts)
    flutes = [p for p in land.iter() if p.get('id', '').split(' ')[0] == 'flute']
    assert len(flutes) >= 12
    for p in flutes:
        x0, y0, x1, y1 = svgtools.element_bbox(p)
        assert y1 - y0 >= 2.5 * (x1 - x0), p.get('id')
    centres = [sum(svgtools.element_bbox(p)[0::2]) / 2 for p in flutes]
    assert any(c < mesa.SPLIT for c in centres) and any(c > mesa.SPLIT for c in centres)


def test_the_grass_is_only_a_thin_cap_on_each_top(parts):
    """The grass on each block is a cap along its top, a small share of the drop to the foot from the cap's back edge to
    the end of the turf dripping over the lip."""
    root = ET.parse(cutting.sheet_path('scenery/mesa.svg')).getroot()
    for step in ('lower', 'upper'):
        assert root.find(".//*[@id='%s shelf']" % step) is not None and root.find(".//*[@id='%s drips']" % step) is not None
        for x in mesa.samples(step, 48):
            assert mesa.cap_front_y(x) + mesa.drip_depth(x) - mesa.cap_top_y(step, x) <= (mesa.FOOT - mesa.UPPER_LIP) / 4, (step, x)


def test_every_tree_stands_within_the_islands_top(parts):
    """No crown hangs past a top's corner into the sky: the banks slope away under the lip, so past the corner is air."""
    for t in mesa.TREES:
        x0, x1 = mesa.tree_extent(t)
        assert mesa.LIP_LEFT <= x0 and x1 <= mesa.LIP_RIGHT, t


def test_no_tree_stands_over_the_falls():
    """The ledge the water pours over is clear of crowns: a tree there would hang over the falls' top."""
    r0, r1 = mesa.rock_span()
    for t in mesa.TREES:
        x0, x1 = mesa.tree_extent(t)
        assert x1 <= r0 or x0 >= r1, t


def test_cypresses_from_the_terrace_stand_among_the_round_trees(parts):
    """The terrace's flame-shaped cypresses (plants/trees.py) stand on both tops among the round crowns."""
    kinds = {(t['kind'], mesa.step_of(t['x'])) for t in mesa.TREES}
    assert {('cypress', 'lower'), ('cypress', 'upper'), ('round', 'lower'), ('round', 'upper')} <= kinds
    root = ET.parse(cutting.sheet_path('scenery/mesa.svg')).getroot()
    assert len([g for g in root.iter() if g.get('id', '').startswith('cypress')]) >= 3


def test_some_trees_stand_behind_the_ring(parts):
    """A clump behind the ring shows through its hole: drawn before the ring, standing within the hole's span."""
    cx, cy = mesa.GEAR_CENTRE
    behind = [t for t in mesa.TREES if t.get('behind')]
    assert behind
    for t in behind:
        x0, x1 = mesa.tree_extent(t)
        assert cx - mesa.GEAR_INNER < (x0 + x1) / 2 < cx + mesa.GEAR_INNER, t
    root = ET.parse(cutting.sheet_path('scenery/mesa.svg')).getroot()
    ids = [g.get('id', '') for g in cutting.find_group(root, 'mesa')]
    assert ids.index('trees behind the ring') < ids.index('gear ring')


def test_the_upper_steps_trees_are_not_a_uniform_row():
    """Sizes vary and the gaps between neighbours vary: clumps and openings, not a picket row under the arch."""
    upper = sorted((t for t in mesa.TREES if mesa.step_of(t['x']) == 'upper'), key=lambda t: t['x'])
    gaps = [b['x'] - a['x'] for a, b in zip(upper, upper[1:])]
    assert max(gaps) - min(gaps) >= 8
    assert len({round(t['h']) for t in upper}) >= 4


# The falls are the reference's: a sheet of water pouring from a lip nearly as wide as the water below, its right edge
# dropping straight down beside the upper step and its left edge leaning out steadily the whole way down, the water on
# the shelf spanning the lip as it rounds over it. The strip stays a tiling rectangle; the frame drawn over it hides
# the strip's left side above the lean.
def test_the_falls_pour_from_a_lip_nearly_as_wide_as_the_water_below():
    full = mesa.FALL_X[1] - mesa.FALL_X[0]
    assert mesa.fall_width(mesa.FALL_TOP) >= full * 0.7
    assert mesa.fall_width(mesa.FALL_TOP + mesa.FALL_PERIOD) == full


def test_the_falls_right_edge_drops_straight_down():
    for k in range(11):
        assert mesa.fall_edges(mesa.FALL_TOP + mesa.FALL_PERIOD * k / 10)[1] == mesa.FALL_X[1]


def test_the_falls_left_edge_leans_out_only_a_little():
    top, foot = (mesa.fall_edges(mesa.FALL_TOP + mesa.FALL_PERIOD * t)[0] for t in (0, 1))
    assert 0 < top - foot <= (mesa.FALL_X[1] - mesa.FALL_X[0]) * 0.12


def test_the_falls_left_edge_wavers_gently_about_its_lean():
    top, foot = (mesa.fall_edges(mesa.FALL_TOP + mesa.FALL_PERIOD * t)[0] for t in (0, 1))
    off = [mesa.fall_edges(mesa.FALL_TOP + mesa.FALL_PERIOD * k / 40)[0] - (top + (foot - top) * k / 40)
           for k in range(41)]
    assert 0.3 <= max(abs(o) for o in off) <= 1.5


def test_the_water_on_the_shelf_spans_the_lip(parts):
    root = ET.fromstring(open(cutting.sheet_path('scenery/mesa.svg')).read())
    x0, _, x1, _ = svgtools.element_bbox(root.find(".//*[@id='pour']"))
    assert x1 - x0 >= (mesa.FALL_X[1] - mesa.FALL_X[0]) * 0.7 - 1


def test_the_falls_frame_does_not_rise_above_the_turf_at_the_lip(parts):
    root = ET.fromstring(open(cutting.sheet_path('scenery/mesa.svg')).read())
    frame = root.find(".//*[@id='falls frame']")
    xa, xb = mesa.FALL_X
    turf = min(mesa.cap_front_y(x) for x in range(xa - mesa.HOLLOW - 1, xb + 1))
    assert svgtools.element_bbox(frame)[1] >= turf


# The lip is a smooth roll of water: its top a convex arc curling forward over the ledge with a white crest along it,
# light blue under the crest, and nothing jagged about it: no dark recess above it, no drips hanging from it. The
# frame's bank beside the water is the gully's own shade, so it merges into the gully behind the strip.
def frame_parts():
    root = ET.fromstring(open(cutting.sheet_path('scenery/mesa.svg')).read())
    return list(root.find(".//*[@id='falls frame']").iter())


def frame_part(name):
    return [p for p in frame_parts() if p.get('id', '') == name or p.get('id', '').startswith(name + ' ')
            and p.get('id', '')[len(name) + 1:].isdigit()]


def test_the_lip_is_a_convex_arc_higher_on_the_right():
    _, top = mesa.pour_outline()
    mid = top[len(top) // 2][1]
    assert mid < (top[0][1] + top[-1][1]) / 2 - 1
    assert top[-1][1] < top[0][1]


def test_a_white_crest_runs_along_the_lip(parts):
    crest, = frame_part('crest')
    x0, y0, x1, y1 = svgtools.element_bbox(crest)
    assert crest.get('fill') == mesa.WATER['streak']
    top = [y for _, y in mesa.pour_outline()[1]]
    assert x1 - x0 >= (mesa.FALL_X[1] - mesa.FALL_X[0]) * 0.6
    assert y0 <= min(top) + 0.5 and y1 - y0 <= max(top) - min(top) + mesa.CREST + 4


def test_the_water_under_the_crest_is_light_blue(parts):
    pour, = frame_part('pour')
    r, g, b = (int(pour.get('fill')[k:k + 2], 16) for k in (1, 3, 5))
    assert b > g > r and r < 0xd0
    assert max(mesa.VEIL[1]) <= 0.5


def test_the_lip_has_no_drips_or_recess(parts):
    names = {p.get('id', '').split(' ')[0] for p in frame_parts() if p.get('id')}
    assert not names & {'drip', 'recess', 'overhang'}, names
    assert names == {'falls', 'left', 'veil', 'pour', 'crest'}, names


def test_the_frames_bank_is_the_gullys_shade(parts):
    bank, = frame_part('left bank')
    assert bank.get('fill') == mesa.hollow_colour()


def test_the_falls_frame_draws_over_the_strip():
    assert [tid for tid, _ in mesa.cut()].index('mesa-falls-frame') > [tid for tid, _ in mesa.cut()].index('mesa-waterfall')


# The mesa's outlines are the Esme terrace's (scene_export/tests/conftest.py): the land, far off, has no line at all
# as the terrace's far hills have none; the ring's, the ledge's and the trees' are each a thin dark shade of their
# own shape's colour, none mixed toward a navy ink, the ring's as wide as the terrace's castle across the water.
@pytest.fixture(scope='module')
def sheet(parts):
    root = ET.parse(cutting.sheet_path('scenery/mesa.svg')).getroot()
    grads = {gid: tuple(s.get('stop-color') for s in g) for gid, g in cutting.load('scenery/mesa.svg')[1].items()}
    return root, grads


def test_every_outline_is_a_dark_shade_of_its_own_shapes_colour(sheet):
    for ident, line, _, fills in conftest.outlines(*sheet):
        assert any(conftest.is_shade_of(line, fill) for fill in fills), (ident, line, sorted(fills))


def test_every_outline_is_as_thin_as_the_terraces(sheet):
    lo, hi = conftest.ESME_LINE_WIDTHS
    for ident, _, width, _ in conftest.outlines(*sheet):
        assert lo <= width <= hi, (ident, width)


def test_the_ring_is_outlined_in_a_shade_of_its_own_stone_a_castles_line_wide(sheet):
    from structures.houses import TOWN_LINE_WIDTH
    root, _ = sheet
    ring = root.find(".//*[@id='ring outline']")
    assert conftest.is_shade_of(ring.get('stroke'), mesa.STONE['body'])
    assert float(ring.get('stroke-width')) == TOWN_LINE_WIDTH


def test_the_land_has_no_outline(sheet):
    root, _ = sheet
    strokes = [p.get('id', '').split(' ')[0] for p in cutting.find_group(root, 'mesa').iter() if p.get('stroke')]
    assert not {'top', 'upper', 'lower'} & set(strokes), strokes


import math
import re
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


# The falls are two strips of zigzag bands over the water's shape, each scrolling down at its own speed and repeating
# over its own period, the back one slow and soft, the front one faster, white and sharper: together their pattern
# only comes round again after many seconds. Each strip is cut from the strip's corner, exactly one period tall.
def test_each_strip_is_one_period_tall_and_hangs_from_the_strips_corner(parts):
    for name in mesa.STRIPS:
        box = parts['mesa-falls-' + name].box
        assert box[:2] == (mesa.FALL_X[0], mesa.FALL_TOP)
        assert box[3] == mesa.STRIPS[name]['period']


def test_the_strips_periods_differ():
    periods = [s['period'] for s in mesa.STRIPS.values()]
    assert len(set(periods)) == len(periods)


def test_each_strips_period_is_a_whole_number_of_canvas_units():
    """A strip's PNG is its period tall at 2x; a period off a whole unit would round, and the strip would scroll by
    less than it repeats and judder once a loop."""
    for s in mesa.STRIPS.values():
        assert cutting.length(s['period']) == pytest.approx(round(cutting.length(s['period'])))


PERIODS = 4          # tall enough that Quick Look renders the drawing pixel for pixel instead of as a padded icon


@pytest.mark.parametrize('name', list(mesa.STRIPS))
def test_each_strip_tiles_without_a_seam(tmp_path, name):
    """The water drawn over several periods is the strip stacked: each period is the first again, so the scene can
    repeat the strip top to bottom."""
    svg = Svg()
    mesa.waterfall(svg, name, periods=PERIODS)
    sheet = tmp_path / 'periods.svg'
    svg.write(str(sheet))
    root = ET.parse(str(sheet)).getroot()
    w, h = mesa.FALL_X[1] - mesa.FALL_X[0], mesa.STRIPS[name]['period']
    box = (mesa.FALL_X[0], mesa.FALL_TOP, w, PERIODS * h)
    stacked = tmp_path / 'periods-part.svg'
    stacked.write_text(svgtools.part_svg('periods', [cutting.find_group(root, 'falls ' + name)], {}, box))
    im = compare.render_svg(str(stacked))
    first = im.crop((0, 0, w, h))
    assert first.getchannel('A').getextrema()[1] >= 200
    for k in range(1, PERIODS):
        diff = ImageChops.difference(first, im.crop((0, k * h, w, (k + 1) * h))).convert('L')
        assert max(diff.getdata()) <= 8, 'period %d differs from the first' % (k + 1)


def test_the_waterfall_hangs_from_the_lower_steps_lip(parts):
    assert parts['mesa-falls-back'].box[1] == mesa.FALL_TOP
    assert mesa.FALL_TOP >= mesa.LOWER_LIP


def test_the_spray_is_centred_under_the_waterfall(parts):
    fall, spray = parts['mesa-falls-back'].box, parts['mesa-spray'].box
    assert fall[0] < spray[0] + spray[2] / 2 < fall[0] + fall[2]


def test_the_gear_stands_behind_the_upper_top():
    cx, cy = mesa.GEAR_CENTRE
    assert cy + mesa.GEAR_OUTER > mesa.UPPER_LIP - mesa.SHELF[0]
    assert cy - mesa.GEAR_OUTER - mesa.TOOTH_HEIGHT == pytest.approx(mesa.GEAR_TOP)


def falls_container():
    doc = mesa_template.build()
    return next(n for n in doc['drawables'] if n['id'] == 'mesa-falls')


def falls_nodes():
    """(shape, back strip, front mask, front strip) of the falls template."""
    shape, back, front = falls_container()['children']
    mask, threads = front['children']
    return shape, back, mask, threads


def scroll_step(node, key='scrollY'):
    track, = node['animationTracks']
    assert track['repeat'] == 'loop'
    step, = track['steps']
    assert step['easeType'] == 'linear'
    return step['durationSeconds'], step['animateProperties'][key]


def test_each_strip_repeats_and_scrolls_down_its_own_period_a_loop():
    _, back, _, front = falls_nodes()
    for node, name in ((back, 'back'), (front, 'front')):
        assert node['wrap'] == 'repeat'
        seconds, scroll = scroll_step(node)
        assert scroll == -cutting.length(mesa.STRIPS[name]['period'])


def test_each_strip_scrolls_in_even_steps_of_whole_texture_pixels():
    """The strips are 2x PNGs scrolled by whole texture pixels, so a speed moving one uneven steps judders: each moves
    whole texture pixels every frame, or one every whole number of frames. The front strip falls faster than the back."""
    _, back, _, front = falls_nodes()
    speeds = []
    for node in (back, front):
        seconds, scroll = scroll_step(node)
        pixels_a_frame = 2 * -scroll / seconds / mesa_template.FRAMES_A_SECOND
        even = pixels_a_frame if pixels_a_frame >= 1 else 1 / pixels_a_frame
        assert even == pytest.approx(round(even), abs=1e-3)
        speeds.append(pixels_a_frame)
    assert speeds[1] > speeds[0] > 0


# The faster animation was too fast. With the cypresses 15-25 m tall a sheet px is about half a metre, so the
# falls drop about 30 m, which water takes about 2.5 s to fall: sqrt(2h/g). The strips fall at the even speeds either
# side of that, the front a little quicker and the back a little slower.
def test_the_water_takes_a_realistic_time_to_fall():
    drop = mesa.FOAM_LINE - mesa.FALL_TOP
    for name, low, high in (('front', 1.5, 2.5), ('back', 2.5, 3.5)):
        seconds = drop / (mesa.STRIPS[name]['period'] / mesa_template.period_seconds(name))
        assert low <= seconds <= high, (name, seconds)


def test_the_strips_pattern_only_comes_round_again_after_many_seconds():
    _, back, _, front = falls_nodes()
    frames = [round(scroll_step(n)[0] * mesa_template.FRAMES_A_SECOND) for n in (back, front)]
    assert math.lcm(*frames) >= 20 * mesa_template.FRAMES_A_SECOND


def test_the_strips_only_draw_inside_the_waters_shape(parts):
    """The water's shape is drawn first and the back strip is masked to it; the front strip is masked to the
    water's silhouette drawn again in black, added to the scene so it changes nothing, since the engine masks a node
    only to its earlier siblings and allows one masked node a parent."""
    shape, back, mask, threads = falls_nodes()
    assert shape['filePath'] == parts['mesa-falls-shape'].path and not shape.get('stencil')
    assert back['filePath'] == parts['mesa-falls-back'].path and back['stencil'] is True
    assert mask['filePath'] == parts['mesa-falls-mask'].path and mask['blendMode'] == 'add' and not mask.get('stencil')
    assert threads['filePath'] == parts['mesa-falls-front'].path and threads['stencil'] is True
    assert parts['mesa-falls-shape'].box == parts['mesa-falls-mask'].box == parts['mesa-falls-back'].box[:3] + (mesa.FALL_PERIOD,)
    for node in (shape, back, mask, threads):
        assert node.get('position', {'x': 0, 'y': 0}) == {'x': 0, 'y': 0}


def test_the_mask_is_the_waters_silhouette_in_black(parts):
    root = ET.fromstring(parts['mesa-falls-mask'].svg)
    fills = {p.get('fill') for p in root.iter() if p.get('fill')}
    assert fills == {'#000000'}
    mask = next(p for p in root.iter() if p.get('fill') == '#000000')
    shape = ET.fromstring(parts['mesa-falls-shape'].svg).find(".//*[@id='water']")
    assert mask.get('d') == shape.get('d')


def test_a_masked_node_never_follows_another_masked_node_under_one_parent():
    """The engine draws a masked node's earlier siblings as its mask with no parent of their own, so an earlier
    masked sibling would fail; each masked node gets a parent of its own instead."""
    for node in cutting.walk(mesa_template.build()['drawables']):
        seen = False
        for child in node.get('children', []):
            assert not (seen and child.get('stencil')), (node['id'], child['id'])
            seen = seen or bool(child.get('stencil'))


def test_every_mesa_template_is_only_a_template():
    doc = mesa_template.build()
    assert [n['id'] for n in doc['drawables']] == ['mesa', 'mesa-falls', 'mesa-falls-lip', 'mesa-spray']
    assert all(n['templateOnly'] for n in doc['drawables'])


def test_the_falls_are_placed_where_the_strip_hangs(parts):
    placed = dict(mesa_template.placements())
    assert list(placed) == ['mesa', 'mesa-falls', 'mesa-falls-lip', 'mesa-spray']
    assert placed['mesa-falls'].box == parts['mesa-falls-back'].box


# The sides slope out a little toward the foot instead of standing straight, steep under the lip and
# spreading out lower down, as a cliff's foot does.
def outward(x_foot, lean, y):
    """px the cliff stands out at height y past where it meets the lip."""
    return lean * (mesa.edge_x(x_foot, mesa.UPPER_LIP, lean) - mesa.edge_x(x_foot, y, lean))


@pytest.mark.parametrize('x_foot, lean', [(mesa.LEFT, 1), (mesa.RIGHT, -1)])
def test_the_cliffs_slope_out_toward_their_foot(x_foot, lean):
    seen = mesa.FOOT - mesa.HIDDEN
    assert 12 <= outward(x_foot, lean, seen) <= (seen - mesa.UPPER_LIP) / 4


@pytest.mark.parametrize('x_foot, lean', [(mesa.LEFT, 1), (mesa.RIGHT, -1)])
def test_the_cliffs_slope_spreads_out_lower_down(x_foot, lean):
    seen = mesa.FOOT - mesa.HIDDEN
    middle = (mesa.UPPER_LIP + seen) / 2
    upper, lower = outward(x_foot, lean, middle), outward(x_foot, lean, seen) - outward(x_foot, lean, middle)
    assert lower >= 1.5 * upper


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


def named(land, kind):
    return [p for p in land.iter() if p.get('id', '').split(' ')[0] == kind]


def width_at(points, y):
    xs = [x0 + (x1 - x0) * (y - y0) / (y1 - y0) for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1])
          if min(y0, y1) <= y <= max(y0, y1) and y0 != y1]
    return max(xs) - min(xs) if xs else 0


def test_the_cliffs_upper_tier_is_slabs_tapering_to_points(parts):
    """The face under each cap is split into slabs, as in the reference: uneven widths, each narrowing to a point at
    its foot rather than rounding off like a finger, over both blocks."""
    land, _ = land_group(parts)
    slabs = named(land, 'slab')
    assert len(slabs) + len(named(land, 'recess')) >= 12
    widths = []
    for p in slabs:
        points = list(svgtools._points(p.get('d')))
        x0, y0, x1, y1 = svgtools.element_bbox(p)
        widths.append(x1 - x0)
        assert width_at(points, y0 + 0.9 * (y1 - y0)) <= 0.5 * width_at(points, y0 + 0.1 * (y1 - y0)), p.get('id')
    assert max(widths) >= 1.6 * min(widths)
    centres = [sum(svgtools.element_bbox(p)[0::2]) / 2 for p in slabs]
    assert any(c < mesa.SPLIT for c in centres) and any(c > mesa.SPLIT for c in centres)


def test_the_slabs_end_at_uneven_heights(parts):
    """No row of slab tips lines up: their feet spread over a good share of the face."""
    land, _ = land_group(parts)
    feet = [svgtools.element_bbox(p)[3] for p in named(land, 'slab')]
    assert max(feet) - min(feet) >= 0.25 * (mesa.FOOT - mesa.UPPER_LIP)


def test_the_slabs_are_not_a_repeating_row(parts):
    """The slabs vary as the reference's do: narrow slivers among broad faces, some set back in shade between those
    standing out, and no two side by side in the same tone."""
    land, grads = land_group(parts)
    slabs = sorted(named(land, 'slab'), key=lambda p: svgtools.element_bbox(p)[0])
    widths = [svgtools.element_bbox(p)[2] - svgtools.element_bbox(p)[0] for p in slabs]
    assert max(widths) >= 3 * min(widths)
    assert len(named(land, 'recess')) >= 3
    fills = [grads.get(p.get('fill', '')[5:-1], p.get('fill')) for p in slabs]
    assert all(a != b for a, b in zip(fills, fills[1:]))


def test_rounded_rocks_are_heaped_up_the_lower_face(parts):
    """The lower tier is rounded rock heaped against the face, as in the reference: many of them, of uneven sizes,
    the highest reaching up past the middle of the face above where the hills hide it."""
    land, _ = land_group(parts)
    boxes = [svgtools.element_bbox(p) for p in named(land, 'boulder')]
    assert len(boxes) >= 12
    tops = [b[1] for b in boxes]
    middle = (mesa.UPPER_LIP + mesa.FOOT - mesa.HIDDEN) / 2
    assert min(tops) <= middle
    sizes = [b[2] - b[0] for b in boxes]
    assert max(sizes) >= 1.8 * min(sizes)


def test_every_boulder_stays_within_the_cliffs_foot(parts):
    """The boulders heaped at the foot stay within the cliffs' sloping outer edges, so none bulges out into the sky."""
    land, _ = land_group(parts)
    for p in land.iter():
        if p.get('id', '').split(' ')[0] == 'boulder':
            for x, y in svgtools._points(p.get('d')):
                assert mesa.edge_x(mesa.LEFT, y, 1) - 0.5 <= x <= mesa.edge_x(mesa.RIGHT, y, -1) + 0.5, (p.get('id'), x, y)


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
# the shelf spanning the lip as it rounds over it. The strips stay tiling rectangles, masked to the water's shape.
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


def test_the_roll_does_not_rise_above_the_turf_at_the_lip(parts):
    root = ET.fromstring(open(cutting.sheet_path('scenery/mesa.svg')).read())
    lip = root.find(".//*[@id='pour']")
    xa, xb = mesa.FALL_X
    turf = min(mesa.cap_front_y(x) for x in range(xa - mesa.HOLLOW - 1, xb + 1))
    assert svgtools.element_bbox(lip)[1] >= turf


# The lip is a smooth roll of water: its top a convex arc curling forward over the ledge with a white crest along it,
# light blue under the crest, and nothing jagged about it: no dark recess above it, no drips hanging from it.
def lip_parts():
    root = ET.fromstring(open(cutting.sheet_path('scenery/mesa.svg')).read())
    return [p for g in ('falls lip', 'falls crest', 'falls crest glow') for p in root.find(".//*[@id='%s']" % g).iter()]


def lip_part(name):
    return [p for p in lip_parts() if p.get('id', '') == name or p.get('id', '').startswith(name + ' ')
            and p.get('id', '')[len(name) + 1:].isdigit()]


def test_the_lip_is_a_convex_arc_higher_on_the_right():
    _, top = mesa.pour_outline()
    mid = top[len(top) // 2][1]
    assert mid < (top[0][1] + top[-1][1]) / 2 - 1
    assert top[-1][1] < top[0][1]


def test_a_white_crest_runs_along_the_lip(parts):
    crest, = lip_part('crest')
    x0, y0, x1, y1 = svgtools.element_bbox(crest)
    assert crest.get('fill') == mesa.WATER['streak']
    top = [y for _, y in mesa.pour_outline()[1]]
    assert x1 - x0 >= (mesa.FALL_X[1] - mesa.FALL_X[0]) * 0.6
    shoulder, _ = mesa.pour_outline()
    assert y0 <= min(top) + 0.5 and y1 <= max(y for _, y in shoulder) + 0.5


def test_the_water_under_the_crest_is_light_blue(parts):
    r, g, b = (int(mesa.WATER['pour'][k:k + 2], 16) for k in (1, 3, 5))
    assert b > g > r and r < 0xd0


def test_the_lip_has_no_drips_or_recess(parts):
    names = {p.get('id', '').split(' ')[0] for p in lip_parts() if p.get('id')}
    assert names == {'falls', 'pour', 'crest'}, names


def test_the_lip_and_spray_draw_over_the_falls():
    order = [tid for tid, _ in mesa_template.placements()]
    assert order.index('mesa-falls') < order.index('mesa-falls-lip') < order.index('mesa-spray')


def inside(pts, x, y):
    hit = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


# An animation at the lip, one of the falls and one at the foot, none overlapping or clipping through another.
# The falls reach up under the lip to the roll's outline, so the lip's foot fades out over solid water of its own colour
# and not over the rock: a shape ending at the lip's foot left a line there, the rock showing through where both
# the lip's and the shape's edge texels are half transparent. They end inside the still foam at their foot.
def test_the_falls_reach_up_under_the_lip():
    shape = mesa.water_shape()
    assert min(y for _, y in shape) == pytest.approx(min(y for _, y in mesa.pour_shape()))
    x = (mesa.FALL_X[0] + mesa.FALL_X[1]) / 2
    assert inside(shape, x, mesa.FALL_TOP + 0.5) and inside(shape, x, mesa.LIP_FOOT - 0.5)
    assert not inside(shape, x, mesa.pour_top_y(x) - 0.5)


# The left side showed the square of the falls' animation past the lip. As in the reference, the roll's
# rounded shoulders are the water's outermost edge: no band shows outside them.
def test_no_band_shows_outside_the_rolls_round_shoulders():
    shape, roll = mesa.water_shape(), mesa.pour_shape()
    ys = [mesa.FALL_TOP + 0.25 + 0.5 * k for k in range(int((mesa.LIP_FOOT - mesa.FALL_TOP) * 2))]
    for y in ys:
        for k in range(int((mesa.FALL_X[1] - mesa.FALL_X[0] + 4) * 2)):
            x = mesa.FALL_X[0] - 2 + 0.25 + 0.5 * k
            if inside(shape, x, y):
                assert inside(roll, x, y), (x, y)


def test_the_roll_rounds_off_its_right_shoulder_too():
    """As in the reference the water turns down at its right end too, not in a square corner against the rock."""
    roll = mesa.pour_shape()
    xb = mesa.FALL_X[1]
    top = mesa.pour_top_y(xb)
    assert not inside(roll, xb - 0.3, top + 0.3)
    assert inside(roll, xb - 0.3, top + mesa.ROLL_RIGHT + 0.5)


# Make the top look like the water comes from somewhere. The reference has no grass above the water: the turf
# and the rock stop at the roll's top, so the water pours out of a gap with the land behind it, not from under turf.
def test_no_turf_or_rock_rises_over_the_water(parts):
    root = ET.fromstring(open(cutting.sheet_path('scenery/mesa.svg')).read())
    land = list(root.find(".//*[@id='land']").iter('{http://www.w3.org/2000/svg}path')) + list(root.find(".//*[@id='land']").iter('path'))
    turf = [p for p in root.find(".//*[@id='mesa']").iter() if p.get('id', '').startswith('lower ')]
    _, top = mesa.pour_outline()
    for p in land + turf:
        d = p.get('d', '')
        if p.get('fill') == 'none' or re.search('[^MLZ0-9.,\\s-]', d):
            continue
        pts = [tuple(map(float, xy.split(','))) for xy in re.findall('-?[0-9.]+,-?[0-9.]+', d)]
        for x, y in top[1:] + mesa.right_shoulder()[:2]:
            assert not inside(pts, x, mesa.roll_top_y(x) - 1.5), (p.get('id'), x)


# The cut: the turf and rock fall away either side of the water in two curving banks, steep by the water
# and flattening as they reach back, so the water pours out of a valley in the land.
def test_the_land_falls_away_in_banks_either_side_of_the_water(parts):
    root = ET.fromstring(open(cutting.sheet_path('scenery/mesa.svg')).read())
    land = list(root.find(".//*[@id='land']").iter('path'))
    turf = [p for p in root.find(".//*[@id='mesa']").iter() if p.get('id', '').split(' ')[0] in ('lower', 'upper')]
    (xl, _), (xr, _) = mesa.BANKS
    x0, x1 = mesa.gap()
    xs = [xl + (x0 - xl) * k / 10 for k in range(1, 10)] + [x1 + (xr - x1) * k / 10 for k in range(1, 10)]
    for p in land + turf:
        d = p.get('d', '')
        if p.get('fill') == 'none' or re.search('[^MLZ0-9.,\\s-]', d):
            continue
        pts = [tuple(map(float, xy.split(','))) for xy in re.findall('-?[0-9.]+,-?[0-9.]+', d)]
        for x in xs:
            assert not inside(pts, x, mesa.valley_y(x) - 1), (p.get('id'), x)


def test_the_banks_are_steep_by_the_water_and_flatten_going_back():
    (xl, yl), (xr, yr) = mesa.BANKS
    x0, x1 = mesa.gap()
    for near, far, y_far in ((x0, xl, yl), (x1, xr, yr)):
        mid = mesa.valley_y((near + far) / 2)
        y_near = mesa.valley_y(near + (far - near) * 0.01)
        assert mid < (y_near + y_far) / 2 - 2


def test_the_shadow_side_still_deepens_from_the_lips_foot(parts):
    """The lip hides the shape above its foot, so the shadow side's fade from the lip's shade starts there."""
    root = ET.fromstring(parts['mesa-falls-shape'].svg)
    shadow = root.find(".//*[@id='water shadow']")
    grad = root.find(".//*[@id='%s']" % shadow.get('fill')[5:-1])
    assert float(grad.get('y1')) + parts['mesa-falls-shape'].box[1] == pytest.approx(mesa.LIP_FOOT)


def test_the_falls_end_inside_the_still_foam():
    shape = mesa.water_shape()
    assert max(y for _, y in shape) == pytest.approx(mesa.FOAM_LINE)
    cx, cy = mesa.SPRAY_CENTRE
    for y in (mesa.FOAM_LINE - 0.5, mesa.FOAM_LINE):
        left, right = mesa.fall_edges(y)
        for k in range(21):
            x = left + (right - left) * k / 20
            assert any((x - cx - dx) ** 2 + (y - cy - dy) ** 2 < r * r for dx, dy, r in mesa.FOAM_BED), (x, y)


def test_the_foam_bed_is_solid(parts):
    root = ET.fromstring(open(cutting.sheet_path('scenery/mesa.svg')).read())
    bed = root.find(".//*[@id='foam bed']")
    assert bed is not None and bed.get('fill-opacity') is None


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


def template(tid):
    return next(n for n in mesa_template.build()['drawables'] if n['id'] == tid)


def tracked(node, key):
    """The values a node's tracks take its property to, in order."""
    return [step['animateProperties'][key] for track in node.get('animationTracks', []) for step in track['steps']
            if key in step['animateProperties']]


# The lip has no glints, and no streaks slide over it. The lip's own animation is
# the slow back strip itself: its soft bands pass under the crest, over the glassy roll, and on down into the falls
# without a break, where the faster white bands come out from under the lip over them; and the crest's glow breathes.
def lip_nodes():
    face, sheets, front_layer, crest, glow = template('mesa-falls-lip')['children']
    return face, sheets, front_layer, crest, glow


def test_the_back_strip_passes_under_the_crest_and_down_the_roll(parts):
    face, sheets, _, crest, glow = lip_nodes()
    assert face == {'id': 'lip', 'filePath': parts['mesa-falls-lip'].path}
    assert crest == {'id': 'crest', 'filePath': parts['mesa-falls-crest'].path}
    assert sheets['filePath'] == parts['mesa-lip-sheets'].path and sheets['stencil'] is True
    assert sheets['wrap'] == 'repeat'
    assert sheets['animationTracks'] == falls_nodes()[1]['animationTracks']
    assert parts['mesa-lip-sheets'].box[:2] == parts['mesa-falls-lip'].box[:2] == parts['mesa-falls-crest'].box[:2]
    assert parts['mesa-lip-sheets'].box[3] == mesa.FALL_PERIOD
    assert not [tid for tid in parts if 'glint' in tid or 'streaks' in tid]


def test_the_front_strip_passes_over_the_lip_too(parts):
    """The fast white bands run over the roll as well, in a container of their own after the back strip's: the
    roll's silhouette in black as their mask, then the front strip cut at the lip's corner, scrolling as the falls'."""
    _, _, layer, _, _ = lip_nodes()
    mask, front = layer['children']
    assert mask['filePath'] == parts['mesa-lip-mask'].path and mask['blendMode'] == 'add' and not mask.get('stencil')
    assert front['filePath'] == parts['mesa-lip-front'].path and front['stencil'] is True and front['wrap'] == 'repeat'
    assert front['animationTracks'] == falls_nodes()[3]['animationTracks']
    assert parts['mesa-lip-front'].box[:2] == parts['mesa-lip-mask'].box[:2] == parts['mesa-falls-lip'].box[:2]
    assert parts['mesa-lip-front'].box[3] == mesa.FRONT_PERIOD
    root = ET.fromstring(parts['mesa-lip-mask'].svg)
    assert {p.get('fill') for p in root.iter() if p.get('fill')} == {'#000000'}
    pour = ET.fromstring(parts['mesa-falls-lip'].svg).find(".//*[@id='pour']")
    assert next(p for p in root.iter() if p.get('fill') == '#000000').get('d') == pour.get('d')


@pytest.mark.parametrize('cut, falls', [('mesa-lip-sheets', 'mesa-falls-back'), ('mesa-lip-front', 'mesa-falls-front')])
def test_the_lips_cut_of_each_strip_lines_up_with_the_falls(parts, cut, falls):
    """Both cuts of a strip scroll alike, so they show the same water at the same place as long as the lip's
    corner is a whole number of canvas units from the strip's: then a band crosses the lip's foot without a step."""
    lip, falls = parts[cut].box, parts[falls].box
    assert lip[1] < falls[1]
    for d in (falls[0] - lip[0], falls[1] - lip[1]):
        assert cutting.length(d) == pytest.approx(round(cutting.length(d)), abs=1e-9), d


def test_the_lips_left_edge_is_threaded_like_the_falls(parts):
    """The falls' left edge is a thread of light blue; without one the roll looked a step wider than the water."""
    thread, = lip_part('pour left edge')
    assert thread.get('fill') == mesa.WATER['left edge']
    xs = [x for x, _ in svgtools._points(thread.get('d'))]
    assert max(xs) - min(xs) <= mesa.LEFT_EDGE + mesa.LEAN + mesa.WAVER[0]


def test_the_lips_cut_of_the_back_strip_is_the_falls_drawn_higher(parts):
    """The sheet's strip is drawn a period above and below its place, so a cut from above the strip's top holds the
    same bands, moved by the whole periods between."""
    lip_cut = ET.fromstring(parts['mesa-lip-sheets'].svg)
    falls_cut = ET.fromstring(parts['mesa-falls-back'].svg)
    assert len(list(lip_cut.iter('{%s}path' % svgtools.SVG_NS))) >= len(list(falls_cut.iter('{%s}path' % svgtools.SVG_NS)))


def test_the_crests_glow_breathes_on_the_front_strips_beat(parts):
    _, _, _, _, glow = lip_nodes()
    assert glow['filePath'] == parts['mesa-falls-crest-glow'].path
    track, = glow['animationTracks']
    assert track['repeat'] == 'yoyo'
    alphas = tracked(glow, 'alpha')
    assert alphas and all(0 < a <= 1 for a in alphas) and glow['alpha'] != alphas[-1]
    seconds = sum(s['durationSeconds'] + s.get('delaySeconds', 0) for s in track['steps'])
    front = scroll_step(falls_nodes()[3])[0]
    assert (2 * seconds) / front == pytest.approx(round(2 * seconds / front))


def band_spans(name):
    """[(top, bottom)] sheet px of each band of the strip within its first period, its outer layer's."""
    layers = mesa.bands(name)
    per_band = len(mesa.STRIPS[name]['layers'])
    return [(min(y for _, y in pts), max(y for _, y in pts)) for _, _, pts in layers[::per_band]]


def test_the_foam_rises_and_throws_as_the_front_bands_land(parts):
    """Each set of foam and thrown water loops over a whole number of the front strip's periods, and rises just as
    one of its bands' teeth reach the foam."""
    period_s, scroll = scroll_step(falls_nodes()[3])
    speed = mesa.STRIPS['front']['period'] / period_s
    landings = [(bottom - mesa.FALL_TOP) % mesa.STRIPS['front']['period'] for _, bottom in band_spans('front')]
    for node in spray_children('mesa-spray-rise-') + spray_children('mesa-thrown-water-'):
        steps = node['animationTracks'][0]['steps']
        loop = sum(st['durationSeconds'] + st.get('delaySeconds', 0) for st in steps)
        assert loop / period_s == pytest.approx(round(loop / period_s), abs=1e-6) and round(loop / period_s) >= 1
        start = steps[0].get('delaySeconds', 0)
        foot = (mesa.FOAM_LINE - mesa.FALL_TOP - speed * start) % mesa.STRIPS['front']['period']
        assert min(abs(foot - y) for y in landings) <= 1, (node['id'], foot, landings)


def spray_children(prefix):
    return [n for n in template('mesa-spray')['children'] if n['id'].startswith(prefix)]


# The foam must move around and look organic, not a gel blob growing. The foam bed churns: a strip of dimples
# rolls out from under the falls to each side over the still bed, masked to its half of the bed, and a mist breathes
# over it; nothing scales the spray as a whole.
def churn_nodes():
    sides = [n for n in template('mesa-spray')['children'] if n['id'].startswith('mesa-spray-churn-')]
    assert [n['id'] for n in sides] == ['mesa-spray-churn-left', 'mesa-spray-churn-right']
    return [tuple(n['children']) for n in sides]


def test_the_foam_churns_outward_from_under_the_falls_to_each_side(parts):
    (lmask, left), (rmask, right) = churn_nodes()
    for mask, side in ((lmask, 'left'), (rmask, 'right')):
        assert mask['filePath'] == parts['mesa-spray-churn-mask-' + side].path and mask['blendMode'] == 'add'
    for strip in (left, right):
        assert strip['filePath'] == parts['mesa-spray-churn'].path and strip['stencil'] is True
        assert strip['wrap'] == 'repeat'
    _, lscroll = scroll_step(left, 'scrollX')
    _, rscroll = scroll_step(right, 'scrollX')
    assert lscroll > 0 > rscroll and lscroll == -rscroll == cutting.length(mesa.CHURN_PERIOD)


def test_the_churn_rolls_slowly_by_whole_texture_pixels():
    (_, left), _ = churn_nodes()
    seconds, scroll = scroll_step(left, 'scrollX')
    units_a_frame = scroll / seconds / mesa_template.FRAMES_A_SECOND
    assert 2 * units_a_frame == pytest.approx(round(2 * units_a_frame), abs=1e-3)
    assert 0 < units_a_frame <= 0.5


def test_the_churn_strip_is_one_period_wide_and_sits_on_whole_units(parts):
    churn = parts['mesa-spray-churn'].box
    assert churn[2] == mesa.CHURN_PERIOD
    assert cutting.length(mesa.CHURN_PERIOD) == pytest.approx(round(cutting.length(mesa.CHURN_PERIOD)))
    spray = parts['mesa-spray'].box
    for side in ('left', 'right'):
        mask = parts['mesa-spray-churn-mask-' + side].box
        assert mask == spray
    (_, left), (_, right) = churn_nodes()
    for node, x in ((left, mesa.SPRAY_CENTRE[0] - mesa.CHURN_PERIOD), (right, mesa.SPRAY_CENTRE[0])):
        pos = node['position']
        assert pos['x'] == pytest.approx(round(pos['x'])) and pos['y'] == pytest.approx(round(pos['y']))
        assert pos['x'] == pytest.approx(cutting.length(x - spray[0]))


def test_the_churn_tiles_sideways_without_a_seam():
    """The churn drawn over several periods is the strip laid side by side: each period is the first again, so the
    scene can repeat the strip sideways. (Quick Look shrinks a strip this small, so the drawing is rasterised here.)"""
    from PIL import Image, ImageDraw
    svg = Svg()
    mesa.churn(svg, periods=3)
    root, _ = conftest.sheet_of(svg)
    x, y, w, h = mesa.churn_box()
    k, fine = 2, 16          # px a sheet px, drawn fine times finer and averaged down, so a shape's edge is its coverage
    im = Image.new('L', (3 * w * k * fine, h * k * fine), 0)
    for path in root.iter('{%s}path' % svgtools.SVG_NS):
        pts = [tuple(map(float, p.split(','))) for p in path.get('d').replace('M', '').replace('Z', '').split(' L')]
        layer = Image.new('L', im.size, 0)
        ImageDraw.Draw(layer).polygon([((px - x) * k * fine, (py - y) * k * fine) for px, py in pts],
                                      fill=round(255 * float(path.get('fill-opacity', 1))))
        im = ImageChops.lighter(im, layer)
    im = im.reduce(fine)
    first = im.crop((0, 0, w * k, h * k))
    assert first.getextrema()[1] > 0
    for n in range(1, 3):
        diff = ImageChops.difference(first, im.crop((n * w * k, 0, (n + 1) * w * k, h * k)))
        assert max(diff.getdata()) <= 4, 'period %d differs from the first' % (n + 1)


def test_the_churn_masks_are_the_beds_halves_in_black(parts):
    cx = mesa.SPRAY_CENTRE[0]
    for side in ('left', 'right'):
        root = ET.fromstring(parts['mesa-spray-churn-mask-' + side].svg)
        paths = [p for p in root.iter('{%s}path' % svgtools.SVG_NS)]
        assert paths and all(p.get('fill') == '#000000' for p in paths)
        x0, _, x1, _ = svgtools.element_bbox(root)
        box = parts['mesa-spray-churn-mask-' + side].box
        if side == 'left':
            assert x1 <= cx - box[0] + 0.6 and x0 < cx - box[0] - 8
        else:
            assert x0 >= cx - box[0] - 0.6 and x1 > cx - box[0] + 8


def test_the_mist_breathes_over_the_foam_and_never_goes_out(parts):
    mist, = spray_children('mesa-spray-mist')
    track, = mist['animationTracks']
    assert track['repeat'] == 'yoyo'
    alphas = tracked(mist, 'alpha')
    assert alphas and min(alphas) > 0 and mist.get('alpha', 1) != alphas[-1]
    root = ET.fromstring(parts['mesa-spray-mist'].svg)
    assert all(float(p.get('fill-opacity', 1)) < 0.6 for p in root.iter('{%s}path' % svgtools.SVG_NS))


def test_nothing_scales_the_spray_as_a_whole():
    for node in cutting.walk(template('mesa-spray')['children']):
        assert not tracked(node, 'xScale') and not tracked(node, 'yScale')


def test_no_puff_of_foam_drifts_as_a_blob_of_its_own():
    assert not spray_children('mesa-spray-puff-')


def test_the_rising_foam_heaves_out_of_the_bed():
    """Foam rising clear of the bed and floating up the falls read as bubbles: each puff starts in the bed and
    lifts little further than its own size."""
    for puffs in mesa.RISING:
        for dx, dy, r in puffs:
            assert any((dx - bx) ** 2 + (dy - by) ** 2 < (r + br) ** 2 for bx, by, br in mesa.FOAM_BED), (dx, dy)
    rise, _, lift, _ = mesa_template.RISE
    assert lift <= 2 * max(r for puffs in mesa.RISING for _, _, r in puffs)


def test_foam_rises_off_the_spray_in_turn_and_fades(parts):
    rising = spray_children('mesa-spray-rise-')
    assert len(rising) == 2
    for foam in rising:
        assert foam['alpha'] == 0 and min(tracked(foam, 'y')) < 0 and tracked(foam, 'alpha')[-1] == 0


def test_water_is_thrown_up_from_the_spray_and_fades(parts):
    thrown = spray_children('mesa-thrown-water-')
    assert len(thrown) == 2
    for drops in thrown:
        assert parts[drops['id']].box == parts['mesa-spray'].box
        assert drops['alpha'] == 0 and drops['animationTracks'][0]['repeat'] == 'loop'
        assert min(tracked(drops, 'y')) < 0 and tracked(drops, 'alpha')[-1] == 0
    loops = [sum(s['durationSeconds'] + s.get('delaySeconds', 0) for s in d['animationTracks'][0]['steps']) for d in thrown]
    assert loops[0] == pytest.approx(loops[1])


# Waterfalls don't make nearly as big a splash: the foam is a low band little wider than the falls, as in the
# reference, its drops and rising foam staying close over it.
FALL_WIDTH = mesa.FALL_X[1] - mesa.FALL_X[0]


def splash_extents():
    """(px out from the spray's middle, px up above it) the splash reaches at most, its moves included."""
    out, up = [], []
    for dx, dy, r in mesa.FOAM_BED:
        out.append(abs(dx) + r)
        up.append(-dy + r)
    for puffs in mesa.RISING:
        for dx, dy, r in puffs:
            out.append(abs(dx) + r)
            up.append(-dy + r + mesa_template.RISE[2])
    for streaks_, drops in mesa.THROWN:
        for dx, dy, w, h in streaks_:
            out.append(max(abs(dx), abs(dx + w)))
            up.append(-dy + mesa_template.THROW[2])
        for dx, dy, r in drops:
            out.append(abs(dx) + r)
            up.append(-dy + r + mesa_template.THROW[2])
    dx, dy, rx, ry = mesa.MIST
    out.append(abs(dx) + rx)
    up.append(-dy + ry)
    return max(out), max(up)


def test_the_splash_is_little_wider_than_the_falls():
    out, _ = splash_extents()
    assert 2 * out <= 1.5 * FALL_WIDTH, 2 * out


def test_the_splash_stays_low_over_the_pool():
    _, up = splash_extents()
    assert up <= 0.45 * FALL_WIDTH, up


# The water is like the reference: bright cyan, falling in zigzag bands of lighter water across the sheet.
def rgb(colour):
    return tuple(int(colour[k:k + 2], 16) for k in (1, 3, 5))


def test_the_water_is_cyan():
    r, g, b = rgb(mesa.WATER['body'])
    assert g >= 0.8 * b and r <= 0.5 * g, mesa.WATER['body']


def spikes(points):
    """How many points of the polygon stand lower than both their neighbours: its downward points."""
    return sum(1 for a, p, b in zip(points[-1:] + points[:-1], points, points[1:] + points[:1]) if p[1] > a[1] and p[1] > b[1])


@pytest.mark.parametrize('name', list(mesa.STRIPS))
def test_the_water_falls_in_zigzag_bands_across_it(name):
    bands = mesa.bands(name)
    assert len(bands) >= 3
    for _, _, points in bands:
        xs = [x for x, _ in points]
        assert max(xs) - min(xs) >= 0.5 * FALL_WIDTH
        assert spikes(points) >= 3


def test_no_vertical_threads_run_down_the_water(parts):
    root, _ = cutting.load('scenery/mesa.svg')
    for name in mesa.STRIPS:
        names = {p.get('id', '').split(' ')[0] for p in cutting.find_group(root, 'falls ' + name).iter() if p.get('id')}
        assert 'streak' not in names, names


# The zigzags looked too uniform and weren't blended, and the water under the lip was cut off flat. Now the
# middle looked repetitive: the bands differ in width, length, span and spacing, and the two strips drift past each
# other.
def outer_bands(name):
    per_band = len(mesa.STRIPS[name]['layers'])
    return [points for _, _, points in mesa.bands(name)[::per_band]]


def tips(points):
    """[(x, y)] the polygon's downward points, left to right."""
    return sorted(p for a, p, b in zip(points[-1:] + points[:-1], points, points[1:] + points[:1]) if p[1] > a[1] and p[1] > b[1])


@pytest.mark.parametrize('name', list(mesa.STRIPS))
def test_the_zigzags_teeth_differ_in_width(name):
    for points in outer_bands(name):
        xs = [x for x, _ in tips(points)]
        gaps = [b - a for a, b in zip(xs, xs[1:])]
        assert max(gaps) >= 1.4 * min(gaps), gaps


@pytest.mark.parametrize('name', list(mesa.STRIPS))
def test_the_zigzags_teeth_differ_in_length(name):
    for points in outer_bands(name):
        ys = [y for _, y in tips(points)]
        assert max(ys) - min(ys) >= 2.5, ys


def test_the_front_bands_are_not_all_ruled_right_across():
    spans = [max(x for x, _ in pts) - min(x for x, _ in pts) for pts in outer_bands('front')]
    assert min(spans) <= 0.8 * FALL_WIDTH < 0.95 * FALL_WIDTH <= max(spans), spans


def test_the_bands_are_not_evenly_spaced():
    for name in mesa.STRIPS:
        tops = sorted(top for top, _ in band_spans(name))
        period = mesa.STRIPS[name]['period']
        gaps = [b - a for a, b in zip(tops, tops[1:])] + [tops[0] + period - tops[-1]]
        assert max(gaps) >= 1.3 * min(gaps), (name, gaps)


@pytest.mark.parametrize('name', list(mesa.STRIPS))
def test_each_band_blends_out_from_a_lighter_core(name):
    layers = mesa.bands(name)
    per_band = len(mesa.STRIPS[name]['layers'])
    assert per_band >= 2
    for k in range(len(layers) // per_band):
        band = layers[k * per_band:(k + 1) * per_band]
        opacities = [o for _, o, _ in band]
        assert opacities == sorted(opacities) and opacities[0] <= 0.6, opacities
        assert sum(rgb(band[-1][0])) > sum(rgb(band[0][0]))
    assert mesa.bands('front')[per_band - 1][0] == mesa.WATER['band core']


def test_the_back_strip_is_softer_than_the_front():
    back = max(o for _, o, _ in mesa.bands('back'))
    front = max(o for _, o, _ in mesa.bands('front'))
    assert back < front


def test_the_back_bands_are_plain_to_see():
    """Too faint, the back strip never showed and the falls repeated on the front strip's short period alone."""
    assert min(o for _, o, _ in mesa.bands('back')) >= 0.5


def test_the_front_strip_has_more_bands_over_a_longer_period_than_the_back():
    """Three bands in a short period came round visibly often: the front strip gets a longer period, more bands in
    it, and so a longer wait before the two strips' pattern repeats."""
    assert mesa.FRONT_PERIOD > mesa.FALL_PERIOD
    assert len(mesa.band_spans('front')) > len(mesa.band_spans('back'))


def test_nothing_of_the_lip_hangs_below_its_foot(parts):
    for group in ('falls lip', 'falls crest', 'falls crest glow'):
        root = ET.fromstring(open(cutting.sheet_path('scenery/mesa.svg')).read())
        assert svgtools.element_bbox(root.find(".//*[@id='%s']" % group))[3] <= mesa.LIP_FOOT + 1e-6


def test_the_lip_is_solid_down_to_its_foot(parts, tmp_path):
    """No band shows through the lip: the row of it just over its foot is opaque across the water."""
    part = parts['mesa-falls-lip']
    path = tmp_path / 'lip.svg'
    path.write_text(part.svg)
    im = compare.render_svg(str(path)).getchannel('A')
    x0, y0, w, h = part.box
    sx, sy = im.size[0] / w, im.size[1] / h
    y = int((mesa.LIP_FOOT - 0.25 - y0) * sy)
    left, right = mesa.fall_edges(mesa.LIP_FOOT)
    for x in range(int((left + 1 - x0) * sx), int((right - x0) * sx)):
        assert im.getpixel((x, y)) == 255, (x, y)


def test_the_lips_foot_is_the_falls_own_colour():
    """The roll shades from pale under the crest to the body's cyan at its foot, so where the falls come out from
    under it there is no line."""
    assert mesa.pour_foot_colour() == mesa.WATER['body']


# The lip: the white crest wraps the whole rounded shoulder and blends down into pale cyan, faint light
# streaks run over the water, and its right side only darkens a little instead of a deep blue stripe.
def test_the_crest_wraps_the_whole_shoulder(parts):
    crest, = lip_part('crest')
    x0, _, _, y1 = svgtools.element_bbox(crest)
    shoulder, _ = mesa.pour_outline()
    assert x0 <= min(x for x, _ in shoulder) + 0.3
    assert y1 >= max(y for _, y in shoulder) - 0.5


def test_the_crest_blends_into_the_water(parts):
    glow = lip_part('crest glow')
    assert glow and all(p.get('fill') == mesa.WATER['streak'] and float(p.get('fill-opacity')) < 1 for p in glow)


def test_the_water_under_the_crest_starts_pale():
    r, g, b = rgb(mesa.WATER['pour'])
    assert r >= 0xb0, mesa.WATER['pour']


def test_light_streaks_run_over_the_lip(parts):
    streaks = lip_part('pour streak')
    assert len(streaks) >= 4
    assert all(float(p.get('fill-opacity')) <= 0.5 for p in streaks)


def test_the_lips_right_side_only_darkens_a_little(parts):
    shade, = lip_part('pour shade')
    assert float(shade.get('fill-opacity')) <= 0.5


# The lip's animation didn't look right. Part of it was the still streaks: hairlines running from the crest
# hard onto the lip's foot, a comb along it. Each tapers out to a point well above the foot instead.
def test_the_still_streaks_taper_out_above_the_lips_foot(parts):
    streaks = lip_part('pour streak')
    assert len(streaks) >= 4
    for p in streaks:
        _, _, _, y1 = svgtools.element_bbox(p)
        assert y1 <= mesa.LIP_FOOT - 1.5, y1


# The tree order on the mesa needs to be audited so the layering looks good. The trees on each top were drawn
# left to right, so a tree standing nearer the cliff's edge could be drawn behind one standing further back; each top's
# trees are drawn back to front, the one whose foot is furthest back first.
@pytest.mark.parametrize('step, behind', [('lower', False), ('upper', False), ('upper', True)])
def test_the_trees_on_each_top_are_drawn_back_to_front(step, behind):
    svg = Svg()
    mesa.trees(svg, step, behind)
    root, _ = conftest.sheet_of(svg)
    feet = [max(y for _, y in svgtools._points(p.get('d'))) for p in root.iter('{%s}path' % svgtools.SVG_NS)
            if p.get('id', '').startswith('tree shadow')]
    assert len(feet) == sum(1 for t in mesa.TREES if mesa.step_of(t['x']) == step and bool(t['behind']) == behind)
    assert feet == sorted(feet), feet

import colorsys
import math
import re

import pytest

from common.painting import Svg
from EsmeTerrace import rail
from furniture import table_set
from scene_export import cutting, svgtools
from structures import houses, train, train_template


def wheel_parts():
    return [(tid, part) for tid, part in train.cut() if tid in train.WHEELS]


def train_children():
    doc = train_template.build()
    node = next(n for n in doc['drawables'] if n['id'] == 'train')
    return node['children']


def wheel_refs():
    return [n for n in train_children() if n['ref'].endswith(tuple('#' + tid for tid in train.WHEELS))]


def radius_of(ref):
    return train.WHEELS[ref['ref'].partition('#')[2]]


def test_every_wheel_image_is_centred_on_its_axle():
    for tid, part in wheel_parts():
        x, y, w, h = part.box
        assert (x + w / 2, y + h / 2) == train.DRAWN_AXLES[tid], tid


def test_every_wheel_template_turns_about_its_centre():
    for node in train_template.build()['drawables']:
        if node['id'] in train.WHEELS:
            assert node['anchor'] == 'center' and node['pivot'] == 'center', node['id']


def test_every_wheel_rests_on_the_rail():
    for tid, radius in train.WHEELS.items():
        for x, y in train.axles(tid):
            assert y + radius == train.RAIL_Y, (tid, x)


def test_every_drawn_wheel_bottom_is_on_the_rail_line():
    root, _ = cutting.load('structures/train.svg')
    for gid, _ in train.wheel_groups():
        box = svgtools.element_bbox(cutting.find_group(root, gid))
        assert abs(box[3] - train.RAIL_Y) <= train.LINE / 2 + 1e-6, gid


def test_every_wheel_in_the_train_template_stands_on_the_rail():
    for ref in wheel_refs():
        assert ref['overrides']['position']['y'] + radius_of(ref) / 2 == 0, ref['id']


def test_wheel_spin_matches_the_rolling_speed():
    for ref in wheel_refs():
        track, = ref['overrides']['animationTracks']
        step, = track['steps']
        assert track['repeat'] == 'loop' and step['easeType'] == 'linear'
        turn = step['animateProperties']['rotation'] - ref['overrides']['rotation']
        assert turn > 0, 'the wheels turn clockwise, the train runs to the right'
        rolled = turn * radius_of(ref) / step['durationSeconds']
        assert abs(rolled - train.TRAIN_SPEED) < 0.05, ref['id']


def rod_refs():
    return [n for n in train_children() if n['ref'].endswith('#train-rod')]


def test_a_rod_couples_every_pair_of_driving_wheels():
    rods = rod_refs()
    assert len(rods) == len(train.ROD_PAIRS)
    xs = [r['overrides']['position']['x'] for r in rods]
    gaps = [round(b - a, 3) for a, b in zip(xs, xs[1:])]
    assert gaps == [(b[0] - a[0]) / 2 for a, b in zip(train.ROD_PAIRS, train.ROD_PAIRS[1:])]


def test_every_rod_circles_with_its_crank():
    for rod in rod_refs():
        bx, by = train_template.rod_base(rod['id'])
        tracks = {step_key(t): t for t in rod['overrides']['animationTracks']}
        r = train.CRANK_R / 2
        xs = [s['animateProperties']['x'] for s in tracks['x']['steps']]
        ys = [s['animateProperties']['y'] for s in tracks['y']['steps']]
        angles = [(train_template.DRIVE_START_QUARTERS + k) * math.pi / 2 for k in range(1, 5)]
        assert xs == pytest.approx([bx - r + r * math.cos(a) for a in angles], abs=0.002), rod['id']
        assert ys == pytest.approx([by + r * math.sin(a) for a in angles], abs=0.002), rod['id']
        turn = 2 * math.pi * train.WHEELS['train-drive-wheel'] / train.TRAIN_SPEED
        assert abs(sum(s['durationSeconds'] for s in tracks['x']['steps']) - turn) < 1e-3
        assert abs(sum(s['durationSeconds'] for s in tracks['y']['steps']) - turn) < 1e-3


def step_key(track):
    return next(iter(track['steps'][0]['animateProperties']))


# The train is drawn in one oblique view: its side faces the viewer undistorted (so its wheels stay circles and spin
# about their axles), and everything on its far side lies a little to the right and above its near side, so the
# fronts of things show foreshortened ahead of them and the tops of roofs show above them.
def test_the_far_side_of_the_train_lies_right_of_and_above_its_near_side():
    x, y = train.project(100, 500, train.DEPTH)
    assert x > 100 and y < 500


def test_the_locos_smokebox_door_is_a_foreshortened_face_ahead_of_its_side():
    root, _ = cutting.load('structures/train.svg')
    x0, y0, x1, y1 = svgtools.element_bbox(cutting.find_group(root, 'smokebox door'))
    assert (x0 + x1) / 2 == pytest.approx(train.SMOKEBOX[1], abs=train.LINE)
    assert x1 - x0 < 0.7 * (y1 - y0)


def test_every_carriage_roof_shows_its_top_above_its_near_edge():
    root, _ = cutting.load('structures/train.svg')
    for k in range(1, len(train.CARRIAGE_LEFTS) + 1):
        carriage = cutting.find_group(root, 'train carriage %d' % k)
        top = next(g for g in carriage.iter() if g.get('id', '').startswith('roof top'))
        x0, y0, x1, y1 = svgtools.element_bbox(top)
        assert y0 < train.CAR_ROOF_TOP - 4 and y1 <= train.CAR_EAVE + train.LINE, k


# What is in front of what: the sheet draws the train as the template layers it, so the compare sheet shows what
# the game shows: the shadow the train casts on the bed first, then the wheels, then the bodies whose frames and
# skirts hide the wheels' tops, then the rods over the wheels.
def test_the_sheet_layers_the_train_as_the_template_does():
    root, _ = cutting.load('structures/train.svg')
    order = [g.get('id') for g in cutting.find_group(root, 'train')]
    first_wheel = min(order.index(gid) for gid, _ in train.wheel_groups())
    assert order.index('train shadow') < first_wheel < order.index('train carriage 3') < order.index('train loco') \
        < order.index('train rod')


def test_the_shadow_is_the_first_thing_the_template_draws():
    assert train_children()[0]['ref'].endswith('#train-shadow')


def test_every_frame_hides_the_top_of_its_wheels():
    for tid, r in train.WHEELS.items():
        hidden_to = train.UNDERFRAME_BOTTOM if tid == 'train-drive-wheel' else train.CAR_UNDER
        axle_y = train.RAIL_Y - r
        assert hidden_to > axle_y - r * 0.5, tid


def test_every_carriage_hangs_a_crest_banner_at_each_end():
    root, _ = cutting.load('structures/train.svg')
    for k in (1, 2, 3):
        carriage = cutting.find_group(root, 'train carriage %d' % k)
        banners = [e for e in carriage.iter() if re.fullmatch(r'banner( \d+)?', e.get('id') or '')]
        assert len(banners) == 2, (k, [b.get('id') for b in banners])
        xs = sorted(svgtools.element_bbox(b)[0] for b in banners)
        x0 = train.CARRIAGE_LEFTS[3 - k]
        assert xs[0] < x0 + 20 and xs[1] > x0 + train.CARRIAGE_W - 20, (k, xs)
        for b in banners:
            assert svgtools.element_bbox(b)[3] > train.CAR_SKIRT + 2, (k, b.get('id'))


# The smoke is a steady stream: every puff lives the same period on the same kind of path, rising and growing at a
# constant rate, and the puffs are spread evenly along it, each starting part way up where the one before it will
# be a cadence later. The engine repeats a step's delaySeconds every loop, so a delay would give each puff its
# own period; the stagger is in where each puff starts instead.
def smoke_refs():
    return [n for n in train_children() if '#train-smoke' in n['ref']]


def track_of(ref, prop):
    return next(t for t in ref['overrides']['animationTracks'] if prop in t['steps'][0]['animateProperties'])


def period(track):
    return round(sum(s['durationSeconds'] for s in track['steps']), 3)


def test_the_smoke_is_several_puffs_with_no_delay_and_one_period():
    puffs = smoke_refs()
    assert len(puffs) >= 3
    periods = {period(t) for p in puffs for t in p['overrides']['animationTracks']}
    assert len(periods) == 1, periods
    assert not any('delaySeconds' in s for p in puffs for t in p['overrides']['animationTracks'] for s in t['steps'])


def test_every_puff_rises_and_grows_at_one_constant_rate():
    for puff in smoke_refs():
        track = track_of(puff, 'y')
        y0 = puff['overrides']['position']['y']
        rises = []
        for step in track['steps']:
            y1 = step['animateProperties']['y']
            if step['durationSeconds'] > 0.1:
                assert step['easeType'] == 'linear', puff['id']
                rises.append((y1 - y0) / step['durationSeconds'])
            y0 = y1
        assert rises and max(rises) - min(rises) < 0.05, (puff['id'], rises)
        assert rises[0] < 0, 'puffs rise'


def test_the_puffs_start_evenly_spaced_along_the_rise():
    puffs = smoke_refs()
    phases = sorted(train_template.smoke_phase(k) for k in range(len(puffs)))
    gaps = [round(b - a, 6) for a, b in zip(phases, phases[1:])]
    assert len(set(gaps)) == 1 and 0 < phases[0] < gaps[0]
    for k, puff in enumerate(puffs):
        y_start = puff['overrides']['position']['y']
        track = track_of(puff, 'y')
        y_end = track['steps'][0]['animateProperties']['y']
        y_funnel = track['steps'][1]['animateProperties']['y']
        assert abs((y_start - y_funnel) / (y_end - y_funnel) - train_template.smoke_phase(k)) < 0.01, puff['id']


def test_the_puffs_differ_in_shape_rotation_and_drift():
    puffs = smoke_refs()
    assert len({p['ref'] for p in puffs}) >= 2
    assert len({p['overrides'].get('rotation', 0) for p in puffs}) >= 3
    drifts = {track_of(p, 'x')['steps'][0]['animateProperties']['x'] - p['overrides']['position']['x'] for p in puffs}
    assert len(drifts) >= 2


def test_every_smoke_image_is_centred_so_it_grows_about_its_middle():
    for node in train_template.build()['drawables']:
        if node['id'].startswith('train-smoke'):
            assert node['anchor'] == 'center' and node['pivot'] == 'center', node['id']


# The wheels start at different angles so the train isn't a row of identical spokes; the driving wheels one rod
# couples must share one angle, and the rod starts where their crank pins then are.
def test_the_wheels_start_at_different_angles():
    starts = [n['overrides'].get('rotation', 0) for n in wheel_refs() if n['ref'].endswith('#train-carriage-wheel')]
    assert len(set(starts)) >= 3, starts


def test_coupled_driving_wheels_share_one_starting_angle():
    for pair in train.ROD_PAIRS:
        drivers = [n for n in wheel_refs() if n['ref'].endswith('#train-drive-wheel')
                   and round(n['overrides']['position']['x'] * 2 + train_template.TRAIN_ORIGIN[0]) in pair]
        assert len(drivers) == len(pair)
        assert len({n['overrides'].get('rotation', 0) for n in drivers}) == 1


def test_the_rod_starts_at_its_wheels_crank_pins():
    for rod, pair in zip(rod_refs(), train.ROD_PAIRS):
        angle = train_template.DRIVE_START_QUARTERS * math.pi / 2
        driver = next(n for n in wheel_refs() if n['ref'].endswith('#train-drive-wheel')
                      and round(n['overrides']['position']['x'] * 2 + train_template.TRAIN_ORIGIN[0]) == pair[0])
        assert driver['overrides'].get('rotation', 0) == pytest.approx(angle)
        r = train.CRANK_R / 2
        at = rod['overrides']['position']
        base = train_template.rod_base(rod['id'])
        assert at['x'] == pytest.approx(base[0] - r + r * math.cos(angle), abs=0.002)
        assert at['y'] == pytest.approx(base[1] + r * math.sin(angle), abs=0.002)


# The pennant is its own part pivoting at the pole, so it can flutter as the train runs.
def test_the_flag_pivots_at_the_pole():
    parts = dict(train.cut())
    x, y, w, h = parts['train-flag'].box
    assert (x + w, y + h / 2) == train.FLAG_HANG
    node = next(n for n in train_template.build()['drawables'] if n['id'] == 'train-flag')
    assert node['anchor'] == 'centerRight' and node['pivot'] == 'centerRight'


def test_the_flag_flutters_a_little_at_the_pole():
    flag = next(n for n in train_children() if n['ref'].endswith('#train-flag'))
    assert flag['overrides']['position'] == {'x': pytest.approx(train.FLAG_HANG[0] / 2 - train_template.TRAIN_ORIGIN[0] / 2),
                                             'y': pytest.approx(train.FLAG_HANG[1] / 2 - train_template.TRAIN_ORIGIN[1] / 2)}
    tracks = flag['overrides']['animationTracks']
    assert tracks and all(t['repeat'] in ('yoyo', 'loop') for t in tracks)
    turn = track_of(flag, 'rotation')
    swing = max(abs(s['animateProperties']['rotation']) for s in turn['steps'])
    assert 0 < swing < 0.25
    assert 0.5 <= period(turn) <= 3


def test_the_loco_image_has_no_pennant_of_its_own():
    root, _ = cutting.load('structures/train.svg')
    ids = {e.get('id') for e in cutting.find_group(root, 'train loco').iter()}
    assert not any(i and i.startswith('pennant') for i in ids), ids & {'pennant'}


# Each carriage is symmetrical end to end: its windows, doors, banners, swags and roof toppers sit evenly about its
# middle, its medallion gear hangs on the middle; only the front face the oblique view adds lies to one side.
def test_every_carriage_is_symmetrical_end_to_end():
    root, _ = cutting.load('structures/train.svg')
    for k in range(1, len(train.CARRIAGE_LEFTS) + 1):
        x0 = train.CARRIAGE_LEFTS[len(train.CARRIAGE_LEFTS) - k]
        mid = x0 + train.CARRIAGE_W / 2
        carriage = cutting.find_group(root, 'train carriage %d' % k)
        for kind in ('window frame', 'door', 'banner', 'swag', 'topper'):
            els = [e for e in carriage.iter() if re.fullmatch(kind + r'( \d+)?', e.get('id') or '')]
            assert els, (k, kind)
            centres = [(b[0] + b[2]) / 2 for b in map(svgtools.element_bbox, els)]
            shift = sum(centres) / len(centres) - mid
            assert -0.5 <= shift <= train.RECEDE[0] * train.DEPTH / 2 + 0.5, (k, kind, shift)
            offsets = sorted(round(c - mid - shift, 1) for c in centres)
            assert offsets == sorted(round(-o, 1) for o in offsets), (k, kind, offsets)


# The towers stand on the round boiler and the roofs: each one's foot wraps the curve it sits on, dipping below
# the barrel's top line on the near side.
def is_foot(eid):
    """Whether this element id is a tower's foot plate itself, not its sheen, edge or shadow."""
    return (eid or '').startswith('saddle') and not any(w in eid for w in ('sheen', 'edge', 'shadow'))


def test_every_boiler_tower_foot_wraps_the_boiler():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    boiler_top = train.BOILER[2] - train.BOILER[3]
    for gid in ('steam dome', 'funnel'):
        foot = next(e for e in cutting.find_group(loco, gid).iter() if is_foot(e.get('id')))
        x0, y0, x1, y1 = svgtools.element_bbox(foot)
        assert y1 > boiler_top + 1.5 and y0 < boiler_top, (gid, y0, y1)


# The loco's front is built as a real one is: the pilot hangs below the buffer beam ahead of the cylinders, with
# the lead wheel behind its slats.
def test_the_pilot_hangs_under_the_buffer_beam_ahead_of_the_cylinders():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    order = [g.get('id') for g in loco]
    assert order.index('cylinders') < order.index('pilot') < order.index('buffer beam')
    px0, py0, px1, py1 = svgtools.element_bbox(cutting.find_group(loco, 'pilot'))
    assert py0 >= train.FRAME[3] - 4 and abs(py1 - train.RAIL_Y) < 2
    assert px0 >= train.CYLINDER[1] - 6


def test_a_lead_wheel_stands_behind_the_pilot():
    lead = [x for x, _ in train.axles('train-carriage-wheel') if x > train.CYLINDER[1]]
    assert len(lead) == 1
    root, _ = cutting.load('structures/train.svg')
    px0, _, px1, _ = svgtools.element_bbox(cutting.find_group(cutting.find_group(root, 'train loco'), 'pilot'))
    assert px0 < lead[0] < px1


# The smokebox door sits on the smokebox front above the buffer beam, the beam runs across the front below it and
# the pilot hangs below the beam: three things one above the other, none running into the next.
def test_the_smokebox_door_stops_above_the_buffer_beam():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    _, _, _, door_bottom = svgtools.element_bbox(cutting.find_group(loco, 'smokebox door'))
    _, beam_top, _, beam_bottom = svgtools.element_bbox(cutting.find_group(loco, 'buffer beam'))
    _, pilot_top, _, _ = svgtools.element_bbox(cutting.find_group(loco, 'pilot'))
    assert door_bottom <= train.FRAME[2] - 1
    assert beam_top < train.FRAME[2] + 1 and beam_bottom > train.FRAME[3] - 1
    assert pilot_top >= train.FRAME[2]


def test_the_buffer_beam_is_a_slab_across_the_front_with_its_own_side():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    beam_x0, _, beam_x1, _ = svgtools.element_bbox(cutting.find_group(loco, 'buffer beam'))
    assert beam_x0 <= train.FRAME[1] - 15 and beam_x1 > train.FRAME[1] + 8
    assert train.CYLINDER[2] >= train.FRAME[3]


# The grille is gold slats hanging in a gold frame with dark gaps between them, as the
# reference paints it; a few bold slats, since at the screen size a fine grille shimmers.
def test_the_pilot_is_gold_slats_over_a_dark_wedge():
    root, _ = cutting.load('structures/train.svg')
    pilot = cutting.find_group(cutting.find_group(root, 'train loco'), 'pilot')
    wedge, = ids_matching(pilot, r'wedge( \d+)?')
    assert wedge.get('fill').startswith('#') and luminance(wedge.get('fill')) < 100, wedge.get('fill')
    slats = ids_matching(pilot, r'slat( \d+)?')
    assert 3 <= len(slats) <= 5 and all(float(e.get('stroke-width')) >= train.MIN_DETAIL for e in slats)


def test_the_boiler_and_cylinders_sit_on_the_running_board():
    assert train.BOILER[2] + train.BOILER[3] <= train.FRAME[2]
    assert train.BOILER[2] + train.SMOKEBOX[2] <= train.FRAME[2] + 2
    assert train.CYLINDER[2] >= train.FRAME[2]


# Each tower is seated by one flared foot that wraps the barrel or roof it stands on, not a plate and a skirt
# stacked on each other.
def test_every_tower_has_one_foot():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    for gid in ('steam dome', 'funnel', 'headlamp', 'cab dome'):
        ids = [e.get('id') or '' for e in cutting.find_group(loco, gid).iter()]
        feet = [i for i in ids if is_foot(i)]
        assert len(feet) == 1, (gid, feet)
        assert not any(i.startswith('skirt') or i.startswith('collar') for i in ids), (gid, ids)


# The train is drawn for the size it is shown at: the 1536 px sheet fills about 1280 screen px, so a detail has to
# be about 2 screen px, 2.4 sheet px, to hold; thinner strokes and smaller circles turn to mush or shimmer.
def test_every_stroke_and_circle_is_drawn_for_the_screen_size(monkeypatch):
    root, _ = cutting.load('structures/train.svg')
    widths = [float(e.get('stroke-width')) for e in root.iter() if e.get('stroke-width')]
    assert min(widths) >= train.DETAIL_LINE, sorted(widths)[:5]
    radii = []
    drawn = train.circle
    monkeypatch.setattr(train, 'circle', lambda cx, cy, r: radii.append(r) or drawn(cx, cy, r))
    train.train(Svg())
    assert min(radii) >= train.MIN_DETAIL / 2, sorted(radii)[:5]
    assert train.LINE >= train.MIN_DETAIL


# At the screen size the cab roof must be a slab of colour, not a line, and the door's maroon ring between its gold
# rim and its boss must be wide enough to read.
def test_the_cab_roof_is_a_slab_at_the_screen_size():
    assert train.CAB_EAVE - train.CAB_ROOF_TOP >= 5 * train.MIN_DETAIL


def test_the_smokebox_door_shows_its_maroon_ring():
    root, _ = cutting.load('structures/train.svg')
    door = cutting.find_group(cutting.find_group(root, 'train loco'), 'smokebox door')
    disc, = [e for e in door.iter() if (e.get('id') or '').startswith('door') and 'boss' not in e.get('id')
             and 'rim' not in e.get('id')]
    boss, = [e for e in door.iter() if (e.get('id') or '').startswith('door boss')]
    _, top, _, bottom = svgtools.element_bbox(disc)
    _, boss_top, _, boss_bottom = svgtools.element_bbox(boss)
    assert boss_top - top >= 2 * train.MIN_DETAIL and bottom - boss_bottom >= 2 * train.MIN_DETAIL


def carriage_gear(root, k):
    """The medallion gear group of carriage k, counted from the front."""
    tid = 'train-carriage-gear'
    gid = [g for g, t in train.gear_groups() if t == tid][len(train.CARRIAGE_LEFTS) - k]
    return cutting.find_group(root, gid)


def test_every_carriage_medallion_hangs_below_the_windows_on_the_middle():
    root, _ = cutting.load('structures/train.svg')
    for k in range(1, len(train.CARRIAGE_LEFTS) + 1):
        x0, top, x1, _ = svgtools.element_bbox(carriage_gear(root, k))
        assert top >= train.WINDOW_SILL - 1, top
        assert (x0 + x1) / 2 == pytest.approx(train.CARRIAGE_LEFTS[len(train.CARRIAGE_LEFTS) - k] + train.CARRIAGE_W / 2, abs=0.5)


# The roofs read symmetric: the oblique projection's receding roof end would make one end a peak, so the roof's
# raised ridge and its toppers mirror about the carriage's middle, at one height, and so does the cab's.
def test_every_carriage_roof_and_its_toppers_mirror_about_its_middle():
    root, _ = cutting.load('structures/train.svg')
    for k in range(1, len(train.CARRIAGE_LEFTS) + 1):
        x0 = train.CARRIAGE_LEFTS[len(train.CARRIAGE_LEFTS) - k]
        mid = x0 + train.CARRIAGE_W / 2
        carriage = cutting.find_group(root, 'train carriage %d' % k)
        for kind in ('roof flank', 'roof top', 'ridge trim'):
            el = next(e for e in carriage.iter() if re.fullmatch(kind + r'( \d+)?', e.get('id') or ''))
            bx0, _, bx1, _ = svgtools.element_bbox(el)
            assert abs((bx0 + bx1) / 2 - mid) <= 0.5, (k, kind, bx0, bx1)
        toppers = [e for e in carriage.iter() if re.fullmatch(r'topper( \d+)?', e.get('id') or '')]
        assert len(toppers) == 2
        (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = map(svgtools.element_bbox, toppers)
        assert abs(ay0 - by0) <= 0.25 and abs(ay1 - by1) <= 0.25, (k, ay0, by0, ay1, by1)
        assert abs((ax0 - mid) + (bx1 - mid)) <= 0.5, (k, ax0, bx1)


def test_every_topper_stands_at_one_height_along_the_train():
    root, _ = cutting.load('structures/train.svg')
    tops = [svgtools.element_bbox(e)[1] for e in root.iter() if re.fullmatch(r'topper( \d+)?', e.get('id') or '')]
    assert len(tops) == 2 * len(train.CARRIAGE_LEFTS) and max(tops) - min(tops) <= 0.25, tops


def test_the_cab_dome_stands_on_the_cab_roofs_ridge_middle():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    dx0, _, dx1, _ = svgtools.element_bbox(cutting.find_group(loco, 'cab dome'))
    rx0, _, rx1, _ = svgtools.element_bbox(cutting.find_group(loco, 'cab roof'))
    assert abs((dx0 + dx1) / 2 - (rx0 + rx1) / 2) <= 1, (dx0, dx1, rx0, rx1)


def ids_matching(group, pattern):
    return [e for e in group.iter() if re.fullmatch(pattern, e.get('id') or '')]


def luminance(colour):
    r, g, b = (int(colour[k:k + 2], 16) for k in (1, 3, 5))
    return 0.3 * r + 0.59 * g + 0.11 * b


# The cab has one big window centred on its side and a bold, outlined gear emblem.
def test_the_cab_has_one_big_window_centred_and_a_bold_gear():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    frames = ids_matching(loco, r'cab window frame( \d+)?')
    assert len(frames) == 1, len(frames)
    x0, _, x1, _ = svgtools.element_bbox(frames[0])
    assert abs((x0 + x1) / 2 - sum(train.CAB) / 2) <= 1 and x1 - x0 >= 0.5 * (train.CAB[1] - train.CAB[0])
    cog, = ids_matching(cutting.find_group(root, 'train cab gear'), r'cog( \d+)?')
    assert float(cog.get('stroke-width') or 0) >= train.LINE
    x0, y0, x1, y1 = svgtools.element_bbox(cog)
    assert ((x0 + x1) / 2, (y0 + y1) / 2) == pytest.approx(train.CAB_GEAR, abs=0.5)


# The roof toppers are simple all-gold shapes: a few gold pieces, no dark collar or shadow.
def test_every_topper_is_simple_and_all_gold():
    root, _ = cutting.load('structures/train.svg')
    for topper in ids_matching(root, r'topper( \d+)?'):
        pieces = [e for e in topper.iter() if e.get('d')]
        assert 1 <= len(pieces) <= 4, len(pieces)
        for e in pieces:
            assert 'fill-opacity' not in e.attrib and e.get('fill') != train.INK, e.get('id')


# The ribbon hangs from each end of the carriage to the medallion's centre and passes under it.
def test_every_carriage_swag_runs_under_the_medallion_centre():
    root, _ = cutting.load('structures/train.svg')
    for k in range(1, len(train.CARRIAGE_LEFTS) + 1):
        carriage = cutting.find_group(root, 'train carriage %d' % k)
        mx0, _, mx1, _ = svgtools.element_bbox(carriage_gear(root, k))
        mid = (mx0 + mx1) / 2
        left, right = sorted(ids_matching(carriage, r'swag( \d+)?'), key=lambda e: svgtools.element_bbox(e)[0])
        assert svgtools.element_bbox(left)[2] >= mid - 1 and svgtools.element_bbox(right)[0] <= mid + 1
        x0 = train.CARRIAGE_LEFTS[len(train.CARRIAGE_LEFTS) - k]
        assert svgtools.element_bbox(left)[0] <= x0 + 12 and svgtools.element_bbox(right)[2] >= x0 + train.CARRIAGE_W - 12
        order = [e.get('id') for e in root.iter() if e.get('id')]
        assert order.index(left.get('id')) < order.index(carriage_gear(root, k).get('id'))


# The cab dome stands on the top of the cab roof: its crown's foot is on the ridge, neither above nor sunk in.
def test_the_cab_dome_stands_on_the_cab_roofs_top():
    root, _ = cutting.load('structures/train.svg')
    dome = cutting.find_group(cutting.find_group(root, 'train loco'), 'cab dome')
    crown, = ids_matching(dome, r'crown( \d+)?')
    _, _, _, foot = svgtools.element_bbox(crown)
    ridge = train.CAB_ROOF_TOP - train.RIDGE_LIFT
    assert ridge - 4 <= foot <= ridge + 2, (foot, ridge)


# The boiler bands are bold gold hoops shaded round the barrel.
def test_the_boiler_bands_are_bold_gold_and_shaded():
    root, _ = cutting.load('structures/train.svg')
    boiler = cutting.find_group(cutting.find_group(root, 'train loco'), 'boiler')
    bands = ids_matching(boiler, r'band( \d+)?')
    assert len(bands) == len(train.BOILER_BANDS)
    for band in bands:
        x0, _, x1, _ = svgtools.element_bbox(band)
        assert x1 - x0 >= 3 * train.MIN_DETAIL, x1 - x0
    assert len(ids_matching(boiler, r'band shade( \d+)?')) == len(bands)
    assert len(ids_matching(boiler, r'band sheen( \d+)?')) == len(bands)


# The pilot is mostly gold with light gaps, not dark slats.
def test_the_pilot_slats_are_light():
    root, _ = cutting.load('structures/train.svg')
    pilot = cutting.find_group(cutting.find_group(root, 'train loco'), 'pilot')
    for slat in ids_matching(pilot, r'slat( \d+)?'):
        assert luminance(slat.get('stroke')) >= 110, slat.get('stroke')


# Match all the outlines to the Esme style, which thins its lines with distance. The train stands
# at the Esme Terrace's castle's distance, so its outlines are as wide as the castle's and its seams as wide as the
# castle's window lines, thinner still; the dark edge discs and strokes under the brass pieces show the same half
# stroke round them that a centred outline would.
def test_the_outlines_are_as_wide_as_esmes_at_the_same_distance():
    assert train.LINE == houses.TOWN_LINE_WIDTH
    castle, _ = cutting.load('structures/houses.svg')
    window_lines = {float(e.get('stroke-width')) for e in castle.iter() if e.get('id', '').startswith('window') and e.get('stroke-width')}
    assert window_lines == {train.DETAIL_LINE} and train.DETAIL_LINE < train.LINE
    assert train.EDGE == train.LINE / 2
    root, _ = cutting.load('structures/train.svg')
    widths = [float(e.get('stroke-width')) for e in root.iter() if e.get('stroke-width')]
    assert max(widths) <= 4.8 + 2 * train.EDGE, sorted(widths)[-5:]


def hsv(colour):
    return colorsys.rgb_to_hsv(*(int(colour[k:k + 2], 16) / 255 for k in (1, 3, 5)))


def hue_apart(a, b):
    d = abs(a - b) % 1
    return min(d, 1 - d)


# Every gold piece is outlined in the Esme Terrace's own gold line, whichever tone of gold it is painted in.
def test_gold_is_outlined_in_esmes_gold_line():
    for tone in train.GOLD.values():
        assert train.line_of(tone) == rail.GOLD_LINE


# Every other material is outlined in a dark of its own hue that keeps the colour's saturation, as the Esme Terrace
# paints its teal cushions in deep teal and its white stone in warm grey: never greyed toward black.
def test_every_outline_is_a_saturated_dark_of_its_own_colour():
    for material in (train.TEAL, train.MAROON, train.OLIVE, train.CREAM, train.GLASS, train.RED, train.DARK):
        for tone in material.values():
            h, s, v = hsv(tone)
            lh, ls, lv = hsv(train.line_of(tone))
            assert hue_apart(lh, h) <= 0.03, (tone, train.line_of(tone))
            assert ls >= min(s, 0.5) - 0.02 and ls >= 0.45, (tone, train.line_of(tone))
            assert 0.4 * v <= lv <= 0.8 * v, (tone, train.line_of(tone))


# The rule reproduces the Esme Terrace's own outlines from its own fills: the table set's cushion and cream.
def test_the_outline_rule_reproduces_esmes_lines():
    for fill, esme_line in ((table_set.GRADIENTS['cushion'][0], table_set.OUTLINE['turquoise']),
                            (table_set.GRADIENTS['cream'][0], table_set.OUTLINE['cream'])):
        ours = train.line_of(fill)
        for k in (1, 3, 5):
            assert abs(int(ours[k:k + 2], 16) - int(esme_line[k:k + 2], 16)) <= 24, (fill, ours, esme_line)


def gear_groups():
    root, _ = cutting.load('structures/train.svg')
    return [cutting.find_group(root, gid) for gid, _ in train.gear_groups()]


def test_every_gear_is_outlined_once_in_line_with_no_edge_under_it():
    for group in gear_groups():
        assert not ids_matching(group, r'cog edge( \d+)?'), group.get('id')
        cog, = ids_matching(group, r'cog( \d+)?')
        assert float(cog.get('stroke-width')) == train.LINE


# The gears are shinier: each cog is brass lit from above, a bright sheen across its upper
# teeth and a glint on its ring, and the carriage medallions match the cab's.
def test_every_gear_is_shiny_brass():
    for group in gear_groups():
        cog, = ids_matching(group, r'cog( \d+)?')
        assert cog.get('fill').startswith('url(#'), group.get('id')
        sheen, = ids_matching(group, r'cog sheen( \d+)?')
        glint, = ids_matching(group, r'cog glint( \d+)?')
        for e in (sheen, glint):
            assert luminance(e.get('fill')) > luminance(train.GOLD['lit']), (group.get('id'), e.get('id'))
        _, sheen_top, _, sheen_bottom = svgtools.element_bbox(sheen)
        _, top, _, bottom = svgtools.element_bbox(cog)
        assert sheen_bottom < (top + bottom) / 2, 'the sheen is on the upper, lit half'


def test_the_carriage_gears_are_drawn_as_the_cab_gear_is():
    kinds = [sorted(re.sub(r' \d+$', '', e.get('id')) for e in g.iter() if e.get('id') and e is not g) for g in gear_groups()]
    assert all(k == kinds[0] for k in kinds), kinds


# The gears turn while the train crosses, as the wheels do. Each gear is its own part cut out
# centred on its hub, drawn over its body, spinning steadily, decoratively slower than the wheels, its teeth
# running at one speed whatever its size.
def gear_refs():
    return [n for n in train_children() if n['ref'].endswith(tuple('#' + tid for tid in train.GEARS))]


def test_every_gear_image_is_centred_on_its_hub():
    parts = dict(train.cut())
    for tid, (cx, cy) in train.DRAWN_GEARS.items():
        x, y, w, h = parts[tid].box
        assert (x + w / 2, y + h / 2) == (cx, cy), tid


def test_every_gear_template_turns_about_its_centre():
    for node in train_template.build()['drawables']:
        if node['id'] in train.GEARS:
            assert node['anchor'] == 'center' and node['pivot'] == 'center', node['id']


def test_a_gear_is_placed_on_every_hub():
    refs = gear_refs()
    hubs = [(x, y) for tid in train.GEARS for x, y in train.gear_hubs(tid)]
    assert len(refs) == len(hubs) == 1 + len(train.CARRIAGE_LEFTS)
    ox, oy = train_template.TRAIN_ORIGIN
    placed = [(r['overrides']['position']['x'] * 2 + ox, r['overrides']['position']['y'] * 2 + oy) for r in refs]
    assert placed == hubs


def test_every_gear_spins_steadily_slower_than_the_wheels():
    wheel_turn = min(train_template.turn_seconds(tid) for tid in train.WHEELS)
    for ref in gear_refs():
        track, = ref['overrides']['animationTracks']
        step, = track['steps']
        assert track['repeat'] == 'loop' and step['easeType'] == 'linear'
        turn = step['animateProperties']['rotation'] - ref['overrides']['rotation']
        assert abs(turn) == pytest.approx(2 * math.pi, abs=1e-4)
        assert step['durationSeconds'] > 2 * wheel_turn, ref['id']
        r = train.GEARS[ref['ref'].partition('#')[2]]
        assert abs(2 * math.pi * r / step['durationSeconds'] - train.GEAR_TOOTH_SPEED) < 0.05, ref['id']


def test_the_gears_are_drawn_over_the_bodies_under_the_rods():
    root, _ = cutting.load('structures/train.svg')
    order = [g.get('id') for g in cutting.find_group(root, 'train')]
    gears = [order.index(gid) for gid, _ in train.gear_groups()]
    assert order.index('train loco') < min(gears) and max(gears) < order.index('train rod')
    refs = [n['ref'].partition('#')[2] for n in train_children()]
    assert refs.index('train-loco') < refs.index('train-cab-gear') < refs.index('train-rod')
    for body in ('train loco', 'train carriage 1', 'train carriage 2', 'train carriage 3'):
        ids = {e.get('id') or '' for e in cutting.find_group(root, body).iter()}
        assert not any(i.startswith('cog') for i in ids), body


# Every stroke on the sheet is painted with a colour or a gradient reference: a gradient tuple written into a
# stroke attribute is no paint at all, and the dark outline under it is all that shows.
def test_every_stroke_on_the_sheet_is_a_paint():
    root, _ = cutting.load('structures/train.svg')
    for e in root.iter():
        stroke = e.get('stroke')
        if stroke is not None:
            assert stroke.startswith('#') or stroke.startswith('url('), (e.get('id'), stroke)


# The pennant's gear is its emblem: large, centred in the pennant's field between the pole and the swallowtail's
# notch, and outlined like the other gears so it stands out from the green.
def test_the_pennant_gear_is_large_and_centred_in_the_pennant_field():
    root, _ = cutting.load('structures/train.svg')
    flag = cutting.find_group(root, 'train flag')
    gear = next(e for e in flag.iter() if e.get('id') == 'pennant gear')
    x0, y0, x1, y1 = svgtools.element_bbox(gear)
    pole_x, notch_x = train.FLAG[0][0], train.FLAG[2][0]
    top, bottom = train.FLAG[0][1], train.FLAG[-1][1]
    assert (x0 + x1) / 2 == pytest.approx((pole_x + notch_x) / 2, abs=0.5)
    assert (y0 + y1) / 2 == pytest.approx((top + bottom) / 2, abs=0.5)
    assert y1 - y0 >= 0.75 * (bottom - top)
    assert gear.get('stroke') is not None and gear.get('stroke') != 'none'


def test_every_wheel_and_gear_turns_one_whole_turn_from_where_it_starts_so_its_loop_is_seamless():
    spinning = [n for n in train_children() if n['ref'].endswith(tuple('#' + t for t in (*train.WHEELS, *train.GEARS)))]
    assert spinning
    for n in spinning:
        start = n['overrides']['rotation']
        end = n['overrides']['animationTracks'][0]['steps'][-1]['animateProperties']['rotation']
        assert abs(abs(end - start) - 2 * math.pi) < 1e-4, n['id']


# The train is a flat side view: the funnel's crown is a flared cap profile, no top-down
# ellipse of its mouth above it.
def test_the_funnel_crown_is_a_side_view_profile():
    root, _ = cutting.load('structures/train.svg')
    funnel = cutting.find_group(cutting.find_group(root, 'train loco'), 'funnel')
    ids = [e.get('id') or '' for e in funnel.iter()]
    assert not any(i.startswith('cap top') or i.startswith('mouth') for i in ids), ids
    _, y0, _, _ = svgtools.element_bbox(funnel)
    assert y0 >= train.FUNNEL[1] - train.LINE, y0


# The roof trim is part of the roof: the gold eave band lies within the roof's silhouette, its ends where the roof's
# ends are, and the flank is shaded down to it rather than carrying a pasted stripe.
def test_every_roof_trim_lies_within_the_roofs_silhouette():
    root, _ = cutting.load('structures/train.svg')
    roofs = [cutting.find_group(cutting.find_group(root, 'train loco'), 'cab roof')]
    for k in range(1, len(train.CARRIAGE_LEFTS) + 1):
        roofs += ids_matching(cutting.find_group(root, 'train carriage %d' % k), r'roof( \d+)?')
    assert len(roofs) == 1 + len(train.CARRIAGE_LEFTS)
    for roof in roofs:
        flank, = ids_matching(roof, r'roof flank( \d+)?')
        trim, = ids_matching(roof, r'eave trim( \d+)?')
        fx0, _, fx1, fy1 = svgtools.element_bbox(flank)
        tx0, _, tx1, ty1 = svgtools.element_bbox(trim)
        assert tx0 >= fx0 - 0.01 and tx1 <= fx1 + 0.01, (roof.get('id'), fx0, tx0, tx1, fx1)
        assert ty1 <= fy1 + 0.01, (roof.get('id'), ty1, fy1)
        assert not ids_matching(roof, r'roof flank shade( \d+)?'), roof.get('id')


# The boiler's top line is straight, so the towers' feet rest on it; the bands stand a little proud of it with
# rounded ends, and the steam dome is seated by a wide flared foot.
def test_the_towers_feet_rest_on_a_straight_boiler_line():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    boiler = cutting.find_group(loco, 'boiler')
    top = train.BOILER[2] - train.BOILER[3]
    for segment in ids_matching(boiler, r'segment( \d+)?'):
        _, y0, _, _ = svgtools.element_bbox(segment)
        assert y0 >= top - train.LINE / 2 - 0.01, (segment.get('id'), y0)
    for band in ids_matching(boiler, r'band( \d+)?'):
        _, y0, _, _ = svgtools.element_bbox(band)
        assert y0 < top - 0.5, (band.get('id'), y0)
    foot = next(e for e in cutting.find_group(loco, 'steam dome').iter() if is_foot(e.get('id')))
    x0, _, x1, _ = svgtools.element_bbox(foot)
    assert x1 - x0 >= 2 * train.STEAM_DOME[2] + 8, x1 - x0


# The front end is one assembly: the pilot's top rail runs flush under the buffer beam, its wedge hangs ahead of the
# cylinder's head, and the cylinder hangs from the frame by a dark steam chest.
def test_the_front_end_joins_up_as_one_pilot_assembly():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    pilot = cutting.find_group(loco, 'pilot')
    rail, = ids_matching(pilot, r'top rail( \d+)?')
    _, rail_top, _, _ = svgtools.element_bbox(rail)
    _, _, _, beam_bottom = svgtools.element_bbox(cutting.find_group(loco, 'buffer beam'))
    assert abs(rail_top - beam_bottom) <= train.LINE + 0.01, (rail_top, beam_bottom)
    assert not ids_matching(pilot, r'top bar( \d+)?')
    wedge, = ids_matching(pilot, r'wedge( \d+)?')
    wx0, _, _, _ = svgtools.element_bbox(wedge)
    assert wx0 >= train.CYLINDER[1] + train.RECEDE[0] * (train.CYLINDER[3] - train.CYLINDER[2]) / 2, wx0
    cylinders = cutting.find_group(loco, 'cylinders')
    chest, = ids_matching(cylinders, r'steam chest( \d+)?')
    _, cy0, _, cy1 = svgtools.element_bbox(chest)
    assert cy0 <= train.UNDERFRAME_BOTTOM and cy1 >= train.CYLINDER[2] + 1, (cy0, cy1)


# The driving wheel is rotationally symmetric, so it spins without a lump going round: evenly spaced spokes and
# everything else a disc on the axle; the rod's own bosses mark the crank pins.
def test_the_drive_wheel_is_rotationally_symmetric():
    root, _ = cutting.load('structures/train.svg')
    gid = next(g for g, t in train.wheel_groups() if t == 'train-drive-wheel')
    wheel = cutting.find_group(root, gid)
    ax, ay = train.DRAWN_AXLES['train-drive-wheel']
    assert not ids_matching(wheel, r'crank pin( \d+)?')
    spokes = ids_matching(wheel, r'spoke( \d+)?')
    assert len(spokes) >= 3
    angles = sorted(math.atan2((b[1] + b[3]) / 2 - ay, (b[0] + b[2]) / 2 - ax) % (2 * math.pi)
                    for b in map(svgtools.element_bbox, spokes))
    gaps = [round(b - a, 3) for a, b in zip(angles, angles[1:])]
    assert len(set(gaps)) == 1, gaps
    for e in wheel.iter():
        if e.get('d') and e not in spokes:
            x0, y0, x1, y1 = svgtools.element_bbox(e)
            assert ((x0 + x1) / 2, (y0 + y1) / 2) == pytest.approx((ax, ay), abs=0.01), e.get('id')


# A gear's teeth and rings are drawn no finer than the screen can show: a tooth pitch of a few screen px and each
# ring at least a screen px wide, whatever the gear's size.
def test_every_gear_is_drawn_no_finer_than_the_screen_shows():
    for group in gear_groups():
        cog, = ids_matching(group, r'cog( \d+)?')
        teeth = len(re.findall(r'[ML]', cog.get('d'))) // 4
        x0, _, x1, _ = svgtools.element_bbox(cog)
        r = (x1 - x0 - train.LINE) / 2
        assert 2 * math.pi * r / teeth >= 3 * train.MIN_DETAIL, (group.get('id'), teeth, r)
        widths = [svgtools.element_bbox(ids_matching(group, kind)[0])[2] - svgtools.element_bbox(ids_matching(group, kind)[0])[0]
                  for kind in (r'cog ring( \d+)?', r'cog disc( \d+)?', r'cog face( \d+)?')]
        for outer, inner in zip(widths, widths[1:]):
            assert (outer - inner) / 2 >= train.MIN_DETAIL * 0.8, (group.get('id'), widths)


# Five puff shapes, each its own silhouette, and the puff cycle uses every one.
def test_there_are_five_distinct_puff_shapes_all_in_the_cycle():
    assert len(train.SMOKE_SHAPES) >= 5
    lobes = [tuple(train.PUFF_LOBES[tid]) for tid in train.SMOKE_SHAPES]
    assert len(set(lobes)) == len(lobes)
    used = {image for image, *_ in train_template.SMOKE_PUFFS}
    assert used == set(train.SMOKE_SHAPES), used


# The boiler wears a thin gold belt along its middle, lengthwise, studded with rivets, and
# the hoops cross over it.
def test_the_boiler_wears_a_riveted_gold_belt_along_its_middle():
    root, _ = cutting.load('structures/train.svg')
    boiler = cutting.find_group(cutting.find_group(root, 'train loco'), 'boiler')
    belt, = ids_matching(boiler, r'belt( \d+)?')
    x0, y0, x1, y1 = svgtools.element_bbox(belt)
    assert x0 <= train.BOILER[0] + 0.5 and x1 >= train.SMOKEBOX[0] - 0.5, (x0, x1)
    assert (y0 + y1) / 2 == pytest.approx(train.BOILER[2], abs=0.5)
    assert 2 * train.MIN_DETAIL <= y1 - y0 <= 5, y1 - y0
    rivets = ids_matching(boiler, r'rivet( \d+)?')
    assert len(rivets) >= 3
    hoops = [svgtools.element_bbox(b) for b in ids_matching(boiler, r'band( \d+)?')]
    for rivet in rivets:
        rx0, ry0, rx1, ry1 = svgtools.element_bbox(rivet)
        assert (ry0 + ry1) / 2 == pytest.approx(train.BOILER[2], abs=0.5), rivet.get('id')
        assert not any(hx0 <= (rx0 + rx1) / 2 <= hx1 for hx0, _, hx1, _ in hoops), rivet.get('id')
    order = [e.get('id') or '' for e in boiler.iter()]
    assert order.index(belt.get('id')) < min(order.index(b.get('id')) for b in ids_matching(boiler, r'band( \d+)?'))


# Every upright gold hoop round the barrel is the same width: the boiler's and the smokebox's.
def test_every_hoop_round_the_barrel_is_one_width():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    hoops = ids_matching(cutting.find_group(loco, 'boiler'), r'band( \d+)?')
    smokebox_hoops = ids_matching(cutting.find_group(loco, 'smokebox'), r'band( \d+)?')
    assert smokebox_hoops
    widths = {round(b[2] - b[0], 2) for b in map(svgtools.element_bbox, hoops + smokebox_hoops)}
    assert len(widths) == 1, widths


# The smokebox front is ringed by a thick gold circle, outlined like the other gold.
def test_the_front_ring_is_a_thick_outlined_gold_circle():
    root, _ = cutting.load('structures/train.svg')
    door = cutting.find_group(cutting.find_group(root, 'train loco'), 'smokebox door')
    rim, = ids_matching(door, r'door rim( \d+)?')
    disc, = ids_matching(door, r'door( \d+)?')
    _, ry0, _, ry1 = svgtools.element_bbox(rim)         # measured up the face: across it the view foreshortens
    _, dy0, _, dy1 = svgtools.element_bbox(disc)
    assert ((ry1 - ry0) - (dy1 - dy0)) / 2 >= 5, (ry1 - ry0, dy1 - dy0)
    assert rim.get('stroke') == rail.GOLD_LINE


# One gold bar drops from the front ring, curves forward and runs on as the pilot's top rail, so the ring, the bar
# and the grille read as one gold assembly.
def test_one_gold_bar_joins_the_front_ring_to_the_pilots_rail():
    root, _ = cutting.load('structures/train.svg')
    loco = cutting.find_group(root, 'train loco')
    order = [g.get('id') for g in loco]
    assert order.index('buffer beam') < order.index('grille bar')
    bar, = ids_matching(cutting.find_group(loco, 'grille bar'), r'bar( \d+)?')
    assert bar.get('stroke') in train.GOLD.values() and 'Q' in bar.get('d')
    bx0, by0, bx1, by1 = svgtools.element_bbox(bar)
    _, _, _, ring_bottom = svgtools.element_bbox(cutting.find_group(loco, 'smokebox door'))
    rail, = ids_matching(cutting.find_group(loco, 'pilot'), r'top rail( \d+)?')
    _, ry0, rx1, ry1 = svgtools.element_bbox(rail)
    assert by0 <= ring_bottom + 0.01, (by0, ring_bottom)
    assert (ry0 + ry1) / 2 - 0.5 <= by1 - float(bar.get('stroke-width')) / 2 <= (ry0 + ry1) / 2 + 0.5, (by1, ry0, ry1)
    assert bx1 >= rx1 - 0.5, (bx1, rx1)

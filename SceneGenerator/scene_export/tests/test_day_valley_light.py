from DayValley import DayValley
from plants import broadleaf
from scene_export import cutting


def nodes():
    return list(cutting.walk(DayValley.build()['drawables']))


def test_no_sun_shows_as_it_stands_high_above_the_frame():
    assert not any('sun' in n.get('ref', '') or n['id'] == 'valley sun' for n in nodes())


def test_every_tree_and_bush_stands_as_drawn_lit_from_the_upper_right():
    trees = [n for n in nodes() if '#oak-' in n.get('ref', '') or '#bush-' in n.get('ref', '')]
    assert trees and all(n['overrides']['xScale'] > 0 for n in trees)


def test_every_fir_stands_mirrored_as_its_drawing_is_lit_from_the_upper_left():
    firs = [n for n in nodes() if '#pine-' in n.get('ref', '')]
    assert firs and all(n['overrides']['xScale'] < 0 for n in firs)


def test_every_flower_stands_mirrored_as_its_drawing_is_lit_from_the_upper_left():
    flowers = [n for n in nodes() if '#flower-' in n.get('ref', '') or '#tulip-' in n.get('ref', '')]
    assert flowers and all(n['overrides']['xScale'] < 0 for n in flowers)


def test_a_bush_cap_shifts_right_toward_the_light():
    assert broadleaf.BUSH_CAP[1] > 0


def test_the_sails_turn_slowly():
    sails = next(n for n in DayValley.turning_windmill()['children'] if n['id'] == 'sails')
    assert sails['overrides']['animationTracks'][0]['steps'][0]['durationSeconds'] >= 16

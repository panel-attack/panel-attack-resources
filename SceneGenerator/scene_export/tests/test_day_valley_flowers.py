import math
import statistics

from DayValley import DayValley
from scene_export import wind


def flower_nodes():
    return [n for nodes in DayValley.flowers_by_ground().values() for n in nodes
            if '#flower-' in n['ref'] or '#tulip-' in n['ref']]


def test_flowers_lean_either_way_no_further_than_the_most_lean():
    leans = [n['overrides'].get('rotation', 0) for n in flower_nodes()]
    assert min(leans) < 0 < max(leans)
    assert max(abs(r) for r in leans) <= DayValley.FLOWER_LEAN


def test_flowers_grow_on_short_and_tall_stems():
    refs = [n['ref'] for n in flower_nodes()]
    assert any(r.endswith('-short') for r in refs)
    assert any(r.endswith('-tall') for r in refs)


def blooms():
    return [p for p in DayValley.flower_plants() if not p[0].startswith('grass-')]


def nearest(plants, i):
    _, x, y, _ = plants[i]
    return min((p for k, p in enumerate(plants) if k != i), key=lambda p: math.hypot(p[1] - x, p[2] - y))


def test_flowers_stand_unevenly_spaced():
    plants = blooms()
    gaps = [math.hypot(nearest(plants, i)[1] - x, nearest(plants, i)[2] - y) / h for i, (_, x, y, h) in enumerate(plants)]
    assert statistics.pstdev(gaps) / statistics.mean(gaps) >= 0.4


def test_no_flowers_stand_in_a_tight_bunch():
    plants = blooms()
    assert all(math.hypot(nearest(plants, i)[1] - x, nearest(plants, i)[2] - y) >= DayValley.FLOWER_CLOSEST * h * 0.75
               for i, (_, x, y, h) in enumerate(plants))


def test_neighbouring_flowers_seldom_stand_level_in_a_row():
    plants = blooms()
    level = [abs(nearest(plants, i)[2] - y) < 0.25 * abs(nearest(plants, i)[1] - x) for i, (_, x, y, _) in enumerate(plants)]
    assert sum(level) / len(level) <= 0.25


def test_single_strays_grow_out_in_the_open_grass():
    plants = blooms()
    out = [p for p in plants if DayValley.drift_thickness(p[1], p[2]) < DayValley.DRIFT_THICK - DayValley.STRAY_CLEAR]
    alone = [p for p in out if all(math.hypot(q[1] - p[1], q[2] - p[2]) >= 3 * p[3] for q in plants if q is not p)]
    assert len(alone) >= 8
    assert len(out) <= len(plants) * 0.2



def plant_nodes():
    return [n for nodes in DayValley.flowers_by_ground().values() for n in nodes]


def swing(node):
    base = node['overrides'].get('rotation', 0)
    return max(abs(s['animateProperties']['rotation'] - base) for t in node['overrides']['animationTracks'] for s in t['steps'])


def test_every_flower_and_tuft_sways_in_the_breeze():
    assert all(node['overrides'].get('animationTracks') and swing(node) > 0 for node in plant_nodes())


def test_the_meadow_sways_more_gently_than_the_terrace():
    assert all(swing(node) <= 0.5 * wind.sway_of(node) for node in plant_nodes())

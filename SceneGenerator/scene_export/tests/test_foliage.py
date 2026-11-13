import math
import random

import pytest

from scene_export import capture
from plants import foliage

OUTLINE = [(0, 300), (0, 0), (150, -20), (300, 0), (300, 300)]
FOCUS = (150, 320)
LEAF = 50
TOWARDS_VIEWER, SIDEWAYS = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)


def shoot(direction, seed=0):
    return foliage.shoot_leaves((0.0, 0.0), direction, LEAF, random.Random(seed))


def by_node(leaves):
    return sorted(leaves, key=lambda l: l.node)


def test_a_shoot_has_five_to_seven_leaves():
    assert all(5 <= len(shoot(SIDEWAYS, seed)) <= 7 for seed in range(20))


def test_a_shoots_two_youngest_leaves_are_at_its_tip():
    for seed in range(20):
        leaves = by_node(shoot(SIDEWAYS, seed))
        assert [l.young for l in leaves] == [False] * (len(leaves) - 2) + [True, True]


def test_a_shoots_young_leaves_are_smaller():
    for seed in range(20):
        leaves = by_node(shoot(SIDEWAYS, seed))
        assert all(l.size <= 0.7 * leaves[0].size for l in leaves if l.young)


def test_a_shoots_leaves_open_out_towards_its_tip():
    for seed in range(20):
        leaves = by_node(shoot(SIDEWAYS, seed))
        assert leaves[0].off < math.radians(40) and leaves[-1].off > math.radians(48)


def test_a_shoots_leaves_crowd_together_towards_its_tip():
    for seed in range(20):
        xs = [l.base[0] for l in by_node(shoot(SIDEWAYS, seed))]
        gaps = [b - a for a, b in zip(xs, xs[1:])]
        assert gaps[-1] < gaps[0]


def test_a_shoot_facing_the_viewer_is_a_rosette():
    for seed in range(20):
        angles = sorted(l.angle % (2 * math.pi) for l in shoot(TOWARDS_VIEWER, seed))
        gaps = [b - a for a, b in zip(angles, angles[1:])] + [angles[0] + 2 * math.pi - angles[-1]]
        assert max(gaps) < math.radians(130)


def test_a_shoot_pointing_sideways_fans_out_on_both_sides_of_its_stem():
    for seed in range(20):
        leaves = shoot(SIDEWAYS, seed)
        assert all(math.cos(l.angle) > 0 for l in leaves)
        assert any(math.sin(l.angle) > 0.2 for l in leaves) and any(math.sin(l.angle) < -0.2 for l in leaves)



def test_a_sideways_shoots_leaves_lie_flat_towards_the_viewer():
    for seed in range(20):
        assert all(l.length >= 0.85 * l.size for l in shoot(SIDEWAYS, seed))


def test_a_sideways_shoots_leaves_alternate_sides_of_its_stem():
    for seed in range(20):
        sides = [math.sin(l.angle) > 0 for l in by_node(shoot(SIDEWAYS, seed))]
        assert all(a != b for a, b in zip(sides, sides[1:])), seed


def test_a_sideways_shoots_leaves_sit_apart_along_its_stem():
    for seed in range(20):
        xs = [l.base[0] for l in by_node(shoot(SIDEWAYS, seed))]
        assert all(b - a >= 0.2 * LEAF for a, b in zip(xs, xs[1:])), seed

def test_every_leaf_of_a_shoot_shows_at_least_half_its_length():
    for direction in (TOWARDS_VIEWER, SIDEWAYS, (0.6, -0.6, math.sqrt(0.28))):
        assert all(l.length >= 0.5 * l.size - 1e-9 for l in shoot(direction))


def test_a_shoots_leaves_are_painted_far_to_near():
    for direction in (TOWARDS_VIEWER, SIDEWAYS, (0.6, -0.6, math.sqrt(0.28))):
        depths = [l.depth for l in shoot(direction)]
        assert depths == sorted(depths)


def test_a_rosettes_young_leaves_are_painted_on_top():
    leaves = shoot(TOWARDS_VIEWER)
    assert [l.young for l in leaves[-2:]] == [True, True]


@pytest.fixture(scope='module')
def mound():
    with capture.recording() as records:
        shapes = foliage.mound('m', OUTLINE, FOCUS, LEAF, [], seed=3)
    return shapes, records


def branches(shapes):
    return [s for s in shapes if isinstance(s, foliage.Spray)]


def shoots(branch):
    return branches(branch.shapes)


def leaf_records(spray, records, kind='leaf'):
    names = {s.name for s in spray.shapes if not isinstance(s, foliage.Spray)}
    return [r for r in records.values() if r.kind == kind and names & set(r.names)]


def tip(r):
    p = r.params
    return p['base'][0] + math.cos(p['angle']) * p['length'], p['base'][1] + math.sin(p['angle']) * p['length']


def test_a_mound_grows_branches_of_two_or_three_shoots(mound):
    shapes, _ = mound
    assert len(branches(shapes)) >= 5
    for b in branches(shapes):
        assert 2 <= len(shoots(b)) <= 3, b.name


def test_a_branchs_shoots_start_close_to_it(mound):
    shapes, _ = mound
    for b in branches(shapes):
        assert all(math.dist(s.origin, b.origin) < 0.5 * LEAF for s in shoots(b)), b.name


def test_most_shoots_of_a_clipped_mound_keep_five_to_seven_leaves(mound):
    shapes, records = mound
    counts = [len(leaf_records(s, records)) for b in branches(shapes) for s in shoots(b)]
    assert max(counts) <= 7
    assert sum(5 <= c for c in counts) >= 0.6 * len(counts)


def test_a_shoot_clipped_back_to_nothing_is_left_out(mound):
    shapes, records = mound
    assert all(leaf_records(s, records) for b in branches(shapes) for s in shoots(b))


def reaches_outline(b, records):
    return any(foliage._edge_distance(OUTLINE, *tip(r)) < 0.1 * LEAF for s in shoots(b) for r in leaf_records(s, records))


def test_a_mounds_branches_face_the_viewer_in_the_middle_and_turn_away_at_its_edges(mound):
    shapes, records = mound
    inside = [b for b in branches(shapes) if not reaches_outline(b, records)]
    middle = min(inside, key=lambda b: math.dist(b.origin, (150, 150)))
    edge = min(branches(shapes), key=lambda b: foliage._edge_distance(OUTLINE, *b.origin))
    assert middle.facing > 0.7
    assert edge.facing < 0.5


def test_a_mounds_young_leaves_are_lighter_than_its_older_ones(mound):
    shapes, records = mound
    young, old = [], []
    for b in branches(shapes):
        for s in shoots(b):
            leaves = sorted(leaf_records(s, records), key=lambda r: int(r.name.rsplit(' ', 1)[1]))
            if len(leaves) < 5:
                continue        # clipped back, so its last leaves are not its young ones
            levels = [int(r.params['tone'].split('-')[1]) for r in leaves]
            young += levels[-2:]
            old += levels[:-2]
    assert sum(young) / len(young) > sum(old) / len(old) + 0.5


def test_a_branchs_shoots_lean_up_towards_the_light():
    ys = [d[1] for seed in range(20) for _, d, _ in foliage.branch_shoots(SIDEWAYS, LEAF, random.Random(seed))]
    assert sum(ys) / len(ys) < -0.15

def test_a_sideways_branchs_shoots_splay_apart_on_screen():
    for seed in range(20):
        shoots = foliage.branch_shoots(SIDEWAYS, LEAF, random.Random(seed))
        assert all(math.hypot(d[0], d[1]) > 0.85 for _, d, _ in shoots), seed
        angles = sorted(math.atan2(d[1], d[0]) for _, d, _ in shoots)
        assert all(b - a > 0.35 for a, b in zip(angles, angles[1:])), seed

def test_a_sideways_branchs_shoots_start_a_little_way_out_from_it():
    for seed in range(20):
        for start, _, _ in foliage.branch_shoots(SIDEWAYS, LEAF, random.Random(seed)):
            assert math.hypot(*start) >= 0.08 * LEAF, seed


def test_each_shoot_draws_its_stem_from_where_it_starts(mound):
    shapes, records = mound
    for b in branches(shapes):
        for s in shoots(b):
            if len(leaf_records(s, records)) < 2:
                continue
            stems = leaf_records(s, records, 'twig')
            assert stems, s.name
            assert min(math.dist(r.params['base'], s.origin) for r in stems) < 1e-6, s.name


def test_a_shoots_stem_is_under_its_leaves(mound):
    shapes, _ = mound
    for b in branches(shapes):
        for s in shoots(b):
            kinds = ['stem' if ' stem ' in x.name else 'leaf' for x in s.shapes]
            assert kinds == sorted(kinds, key=lambda k: k != 'stem'), s.name


def test_each_branch_draws_a_stem_out_to_each_of_its_shoots(mound):
    shapes, records = mound
    for b in branches(shapes):
        stems = leaf_records(b, records, 'twig')
        for s in shoots(b):
            assert any(math.dist(r.params['base'], b.origin) < 1e-6 and math.dist(tip(r), s.origin) < 1e-6
                       for r in stems), s.name


def test_a_sideways_shoots_leaves_vary_in_how_far_they_turn_off_its_stem():
    turns = [abs(math.atan2(math.sin(l.angle), math.cos(l.angle)))
             for seed in range(20) for l in by_node(shoot(SIDEWAYS, seed))[1:2]]
    assert max(turns) - min(turns) > math.radians(20)


def test_a_white_flower_has_lines_between_its_petals():
    assert 'f lines' in [s.name for s in foliage.flower('f', (0, 0), 30.0, white=True)]


def rose_shapes():
    return foliage.rose('r', (0.0, 0.0), 34.0)


def test_a_rose_is_built_of_separate_outlined_petals():
    petals = [s for s in rose_shapes() if s.name.startswith('r petal ')]
    assert len(petals) >= 10 and all(s.stroke != 'none' for s in petals)


def path_points(d):
    return [tuple(map(float, p.split(','))) for p in d.replace('M', ' ').replace('L', ' ').replace('Z', ' ').split()]


def whorls(shapes):
    """{whorl: [petal shape]} of a rose's petals, named '<name> petal <whorl> <k>', outermost whorl 1."""
    out = {}
    for s in shapes:
        parts = s.name.split()
        if len(parts) == 4 and parts[1] == 'petal':
            out.setdefault(int(parts[2]), []).append(s)
    return out


def test_a_semi_double_rose_has_two_whorls_of_five_petals():
    assert {w: len(ps) for w, ps in whorls(rose_shapes()).items()} == {1: 5, 2: 5}


def test_a_semi_double_roses_open_middle_shows_its_yellow_stamens():
    assert any(s.fill == 'flower-centre' for s in rose_shapes())


def test_a_roses_stamens_sit_in_its_cup_behind_its_front_inner_petals():
    shapes = foliage.rose('r', (0.0, 0.0), 34.0, squash=0.8)
    names = [s.name for s in shapes]
    stamens = names.index('r stamens')
    inner = [names.index(s.name) for s in whorls(shapes)[2]]
    assert min(inner) < stamens < max(inner)


def hull(points):
    pts = sorted(set(points))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(pts[::-1])


def inside(poly, p, slack=0.5):
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) < -slack * math.hypot(bx - ax, by - ay):
            return False
    return True


@pytest.mark.parametrize('squash, rot', [(1.0, 0.3), (0.9, 2.84), (0.8, 4.79), (0.75, 2.0)])
def test_a_roses_stamens_stay_inside_its_inner_cup(squash, rot):
    shapes = foliage.rose('r', (0.0, 0.0), 80.0, squash=squash, rot=rot)
    cup = hull([p for s in whorls(shapes)[max(whorls(shapes))] for p in path_points(s.d)])
    stamens = next(s for s in shapes if s.name == 'r stamens')
    assert all(inside(cup, p) for p in path_points(stamens.d))


def mirror_gap(petal, others):
    """How far the petal's outline, mirrored left to right, lies from the nearest of the others' outlines."""
    pts = [(-x, y) for x, y in path_points(petal.d)]
    return min(max(min(math.hypot(x - u, y - v) for u, v in path_points(o.d)) for x, y in pts) for o in others)


@pytest.mark.parametrize('squash, rot', [(0.88, 2.84), (0.88, 4.79), (1.0, 1.1)])
def test_a_roses_outer_petals_mirror_each_other_left_to_right(squash, rot):
    petals = whorls(foliage.rose('r', (0.0, 0.0), 80.0, squash=squash, rot=rot))[1]
    assert all(mirror_gap(p, petals) < 1.0 for p in petals)


def spread(values):
    return (max(values) - min(values)) / (sum(values) / len(values))


@pytest.mark.parametrize('rot', [0.3, 2.84, 4.79, 2.0, 1.1])
def test_a_roses_inner_petals_each_stand_up_their_own_way(rot):
    inner = whorls(foliage.rose('r', (0.0, 0.0), 80.0, rot=rot))[2]
    reach, width = [], []
    for s in inner:
        pts = path_points(s.d)
        tip = max(pts, key=lambda p: math.hypot(*p))
        a = math.atan2(tip[1], tip[0])
        reach.append(math.hypot(*tip))
        width.append(max(abs(-math.sin(a) * x + math.cos(a) * y) for x, y in pts))
    assert spread(reach) >= 0.2 and spread(width) >= 0.25


def test_a_roses_inner_petals_are_outlined_as_thick_as_its_outer_ones():
    widths = {w: {s.width for s in ps} for w, ps in whorls(rose_shapes()).items()}
    assert widths[2] == widths[1]


def test_a_roses_inner_rims_are_edged_dark_on_both_sides():
    shapes = {s.name: s for s in rose_shapes()}
    for k in range(1, 6):
        rim, edge = shapes['r rim 2 %d' % k], shapes['r rim edge 2 %d' % k]
        names = list(shapes)
        assert edge.stroke == foliage.PETAL_OUTLINE and edge.width > rim.width and edge.d == rim.d
        assert names.index('r rim edge 2 %d' % k) < names.index('r rim 2 %d' % k)


def test_a_roses_outer_petals_open_out_furthest():
    reach = {w: max(math.hypot(*p) for s in ps for p in path_points(s.d)) for w, ps in whorls(rose_shapes()).items()}
    assert len(reach) >= 2
    assert [reach[w] for w in sorted(reach)] == sorted(reach.values(), reverse=True)


def test_a_roses_whorls_paint_from_the_outside_in():
    names = [s.name for s in rose_shapes()]
    firsts = [names.index(ps[0].name) for _, ps in sorted(whorls(rose_shapes()).items())]
    lasts = [names.index(ps[-1].name) for _, ps in sorted(whorls(rose_shapes()).items())]
    assert len(firsts) >= 2 and all(l < f for l, f in zip(lasts, firsts[1:]))


def test_you_see_into_a_roses_cup_over_its_back_petals_and_the_outside_of_its_front_ones():
    shapes = foliage.rose('r', (0.0, 0.0), 34.0, squash=0.8)
    inner = whorls(shapes)[max(whorls(shapes))]
    ys = {s.name: sum(y for _, y in path_points(s.d)) / len(path_points(s.d)) for s in inner}
    mid = sum(ys.values()) / len(ys)
    back = [s for s in inner if ys[s.name] < mid]
    front = max(inner, key=lambda s: ys[s.name])
    assert back and all(s.fill != foliage.ROSE_PETAL for s in back)
    assert front.fill == foliage.ROSE_PETAL


def flatten(shapes):
    for s in shapes:
        if isinstance(s, foliage.Spray):
            yield from flatten(s.shapes)
        else:
            yield s


SPOTS = [(150, 120, 20, 'pink'), (90, 200, 18, 'rose'), (220, 230, 16, 'white')]


def rim(x):
    return 270.0


@pytest.fixture(scope='module')
def flowering():
    with capture.recording() as records:
        shapes = foliage.mound('m', OUTLINE, FOCUS, LEAF, SPOTS, seed=3, floor=rim)
    return shapes, records


def test_every_leaf_of_a_mound_grows_on_a_shoot(flowering):
    shapes, records = flowering
    on_shoots = {s.name for b in branches(shapes) for sh in shoots(b) for s in sh.shapes}
    leaves = [r for r in records.values() if r.kind == 'leaf' and r.names[0].startswith('m ')]
    assert leaves and all(set(r.names) & on_shoots for r in leaves)


def shoot_tip(shoot, records):
    leaves = leaf_records(shoot, records)
    return max(leaves, key=lambda r: int(r.name.rsplit(' ', 1)[1])).params['base']


def flowering_shoot(spot, shapes, records):
    x, y, r, _ = spot
    return min((s for b in branches(shapes) for s in shoots(b)), key=lambda s: math.dist(shoot_tip(s, records), (x, y)))


def test_each_flower_of_a_mound_blooms_at_the_tip_of_a_shoot(flowering):
    shapes, records = flowering
    for spot in SPOTS:
        assert math.dist(shoot_tip(flowering_shoot(spot, shapes, records), records), spot[:2]) < 0.2 * spot[2], spot


def test_a_flowers_collar_of_leaves_reaches_out_past_its_petals(flowering):
    shapes, records = flowering
    for x, y, r, kind in SPOTS:
        s = flowering_shoot((x, y, r, kind), shapes, records)
        assert sum(math.dist(tip(l), (x, y)) > 1.3 * r for l in leaf_records(s, records)) >= 3, kind


def test_a_mounds_branches_spill_over_its_pots_rim(flowering):
    shapes, records = flowering
    spilling = [b for b in branches(shapes) if any(tip(l)[1] > rim(0) + 0.3 * LEAF
                                                   for s in shoots(b) for l in leaf_records(s, records))]
    assert len(spilling) >= 3


def mound_leaves(records):
    return [r for r in records.values() if r.kind == 'leaf' and r.names[0].startswith('m ')]


def test_a_mound_is_clipped_so_no_leaf_reaches_past_its_outline(flowering):
    _, records = flowering
    assert all(foliage._edge_distance(OUTLINE, *tip(r)) > -2 for r in mound_leaves(records))


def test_a_mounds_outer_leaves_fan_out_from_low_in_it(flowering):
    _, records = flowering
    cx, cy = foliage._fan_centre(OUTLINE)
    off = []
    for r in mound_leaves(records):
        bx, by = r.params['base']
        phi = math.atan2(by - cy, bx - cx)
        if math.hypot(bx - cx, by - cy) > 0.6 * foliage.reach(OUTLINE, (cx, cy), -phi):
            d = r.params['angle'] - phi
            off.append(abs(math.atan2(math.sin(d), math.cos(d))))
    assert len(off) >= 20
    assert sum(o < math.radians(45) for o in off) >= 0.9 * len(off)


def test_a_mounds_unclipped_leaves_show_nearly_their_full_length(flowering):
    shapes, records = flowering
    for b in branches(shapes):
        for s in shoots(b):
            whole = [r for r in leaf_records(s, records) if foliage._edge_distance(OUTLINE, *tip(r)) > 2]
            if len(whole) >= 2:
                lengths = [r.params['length'] for r in whole]
                assert min(lengths) >= 0.75 * max(lengths), s.name


def test_a_mounds_lower_leaves_are_larger(flowering):
    _, records = flowering
    leaves = sorted(mound_leaves(records), key=lambda r: r.params['base'][1])
    third = len(leaves) // 3
    top = sum(r.params['length'] for r in leaves[:third]) / third
    low = sum(r.params['length'] for r in leaves[-third:]) / third
    assert low > 1.2 * top


def test_a_mounds_flowers_paint_over_all_its_stems():
    spots = SPOTS
    with capture.recording():
        shapes = list(flatten(foliage.mound('m', OUTLINE, FOCUS, LEAF, spots, seed=3)))
    names = [s.name for s in shapes]
    stems = [i for i, n in enumerate(names) if ' stem ' in n + ' ']
    flowers = [i for i, n in enumerate(names) if n.split()[1] in ('flower', 'rose', 'white')]
    assert stems and flowers and max(stems) < min(flowers)

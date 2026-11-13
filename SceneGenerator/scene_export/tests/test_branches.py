import math

import pytest

from scene_export import GENERATOR  # noqa: F401
from plants import branches


DENSITIES = (None, 'sparse', 'dense')


def leaves(piece, group=None):
    return [d for d in piece.draws if d.kind == 'leaf' and d.group == group]


def all_branches():
    """(piece, leaf length) for every branch in the library"""
    for size_name, (size, *_) in branches.BRANCH_SIZES.items():
        for density in DENSITIES:
            for seed in (1, 2):
                yield branches.branch(size_name, seed, density), size


def test_the_library_has_rosettes_and_branches_in_three_sizes():
    ids = {p.id for p in branches.library()}
    for kind in ('rosette', 'branch'):
        for size in ('small', 'medium', 'large'):
            assert '%s-%s-1' % (kind, size) in ids


def test_the_library_has_a_sparse_and_a_dense_variant_of_each_size():
    ids = {p.id for p in branches.library()}
    for kind in ('rosette', 'branch'):
        for size in ('small', 'medium', 'large'):
            for density in ('sparse', 'dense'):
                assert '%s-%s-%s-1' % (kind, size, density) in ids


def test_a_denser_piece_has_more_leaves():
    for kind in (branches.rosette, branches.branch):
        for size in ('small', 'medium', 'large'):
            count = [len([d for d in kind(size, 1, density).draws if d.kind == 'leaf'])
                     for density in ('sparse', None, 'dense')]
            assert count == sorted(set(count)), (kind.__name__, size, count)


def test_a_denser_branch_has_more_side_shoots():
    for size in ('small', 'medium', 'large'):
        count = [len({d.group for d in branches.branch(size, 1, density).draws if d.group})
                 for density in ('sparse', None, 'dense')]
        assert count[0] <= count[1] < count[2] and count[0] >= 1, (size, count)


def test_a_bigger_branch_has_bigger_leaves():
    small = max(d.length for d in leaves(branches.branch('small', 1)))
    large = max(d.length for d in leaves(branches.branch('large', 1)))
    assert large > small * 1.2


def test_a_branch_grows_side_shoots():
    for size in ('small', 'medium', 'large'):
        groups = {d.group for d in branches.branch(size, 1).draws if d.group}
        assert len(groups) == branches.BRANCH_SIZES[size][2]


def test_a_branchs_foot_is_bare_stem():
    piece = branches.branch('large', 1)
    size = branches.BRANCH_SIZES['large'][0]
    lowest = max(d.base[1] for d in piece.draws if d.kind == 'leaf')
    assert lowest < -0.5 * size


def test_a_branchs_first_side_shoot_grows_close_to_its_foot():
    for piece, size in all_branches():
        first = next(d for d in piece.draws if d.kind == 'stem' and d.group == 'shoot 1')
        assert math.hypot(*first.base) < 0.5 * size, piece.id


def test_each_leaf_on_a_branch_grows_from_a_spot_of_its_own_with_space_before_the_next():
    for piece, size in all_branches():
        for group in {d.group for d in piece.draws}:
            bases = [d.base for d in leaves(piece, group)]
            for i, a in enumerate(bases):
                for b in bases[i + 1:]:
                    assert math.dist(a, b) > 0.3 * size, (piece.id, group)


def grown(d):
    """A leaf's full length, before a far leaf is drawn short"""
    return d.width * d.length / branches.LEAF_WIDTH


def mature_leaves(piece, group):
    """The group's leaves from its foot up, without the two young leaves and the bud at its tip"""
    foot = next(d.base for d in piece.draws if d.kind == 'stem' and d.group == group)
    return sorted(leaves(piece, group), key=lambda d: math.dist(d.base, foot))[:-3]


def test_a_shoots_leaves_are_biggest_at_its_foot_and_shrink_towards_its_tip():
    for piece, size in all_branches():
        for group in {d.group for d in piece.draws}:
            mature = mature_leaves(piece, group)
            if len(mature) >= 2:
                assert grown(mature[-1]) < 0.85 * max(grown(d) for d in mature[:2]), (piece.id, group)


def test_a_side_shoots_leaves_point_away_from_the_leader():
    for piece, size in all_branches():
        for group in {d.group for d in piece.draws} - {None}:
            first = next(d for d in piece.draws if d.kind == 'stem' and d.group == group)
            outward = 1 if math.cos(first.angle) > 0 else -1
            for d in mature_leaves(piece, group):
                assert math.cos(d.angle) * outward > -0.15, (piece.id, group, math.degrees(d.angle))


def test_a_rosettes_leaves_go_all_the_way_round():
    for size in ('small', 'medium', 'large'):
        for density in DENSITIES:
            angles = sorted(d.angle % (2 * math.pi) for d in leaves(branches.rosette(size, 1, density)))
            gaps = [b - a for a, b in zip(angles, angles[1:])] + [angles[0] + 2 * math.pi - angles[-1]]
            assert max(gaps) < math.radians(110), (size, density)


def test_a_rosettes_young_leaves_are_the_smallest_and_paint_last():
    piece = branches.rosette('large', 1)
    assert max(d.length for d in piece.draws[-2:]) < min(d.length for d in piece.draws[:3])


def test_every_stem_is_one_of_two_widths():
    for piece in branches.library():
        for d in piece.draws:
            if d.kind == 'stem':
                assert any(abs(d.width - w) < 1.6 for w in branches.STEM_WIDTHS.values())


def test_no_stem_is_longer_than_the_long_stem_image():
    for piece in branches.library():
        for d in piece.draws:
            if d.kind == 'stem':
                assert d.length <= branches.STEM_LENGTHS['long'] + 1e-9, piece.id


def loader_point(placement, p):
    """Where the loader draws the piece's point p: mirrored and scaled, turned, then moved to the placement"""
    x, y = (-p[0] if placement.mirror else p[0]) * placement.scale, p[1] * placement.scale
    c, s = math.cos(placement.rotation), math.sin(placement.rotation)
    return placement.at[0] + c * x - s * y, placement.at[1] + s * x + c * y


def test_a_placed_piece_sits_where_the_loader_draws_it():
    piece = branches.branch('large', 1)
    placement = branches.Placement(piece.id, (100.0, 200.0), 0.7, 1.2, True)
    for d, p in zip(piece.draws, branches.placed(piece, placement)):
        assert math.dist(p.base, loader_point(placement, d.base)) < 1e-9
        tip = (d.base[0] + math.cos(d.angle) * d.length, d.base[1] + math.sin(d.angle) * d.length)
        placed_tip = (p.base[0] + math.cos(p.angle) * p.length, p.base[1] + math.sin(p.angle) * p.length)
        assert math.dist(placed_tip, loader_point(placement, tip)) < 1e-9


def test_a_placed_stem_is_scaled_across_and_a_leaf_keeps_its_shape():
    piece = branches.branch('large', 1)
    placement = branches.Placement(piece.id, (0.0, 0.0), 0.0, 1.5, False)
    for d, p in zip(piece.draws, branches.placed(piece, placement)):
        assert p.width == pytest.approx(d.width * 1.5 if d.kind == 'stem' else d.width)


def test_a_mirrored_leaf_bows_the_other_way():
    piece = branches.branch('large', 1)
    placement = branches.Placement(piece.id, (0.0, 0.0), 0.0, 1.0, True)
    for d, p in zip(piece.draws, branches.placed(piece, placement)):
        assert p.bend == -d.bend

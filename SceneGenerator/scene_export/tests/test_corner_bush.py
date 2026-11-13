import math

import pytest

from scene_export import GENERATOR  # noqa: F401
from plants import branches
from plants import foliage
from plants import bushes
from plants import bushes_reference as T


@pytest.fixture(scope='module')
def layout():
    return bushes.corner_bush_layout()


def role(layout, name):
    return [p for p in layout if p.role == name]


def pointing(p):
    """The screen direction the placed piece grows in: its up, turned"""
    return math.sin(p.rotation), -math.cos(p.rotation)


def leaf_size(p):
    kind, size_name = p.piece.split('-')[:2]
    sizes = branches.ROSETTE_SIZES if kind == 'rosette' else branches.BRANCH_SIZES
    return sizes[size_name][1 if kind == 'rosette' else 0] * p.scale


def rim_front(x):
    r = T.CORNER_PLANTER_RIM
    return r['cy'] + r['b'] * math.sqrt(max(0.0, 1 - ((x - r['cx']) / r['a']) ** 2))


def test_every_piece_is_one_from_the_library(layout):
    ids = {p.id for p in branches.library()}
    assert layout and all(p.piece in ids for p in layout)


def test_every_piece_grows_from_inside_the_bush(layout):
    for p in layout:
        assert foliage._inside(T.CORNER_BUSH_OUTLINE, *p.at), p


def test_branches_round_the_edge_point_away_from_the_middle_of_the_soil(layout):
    edge = role(layout, 'edge')
    assert len(edge) >= 6
    for p in edge:
        out = (p.at[0] - bushes.CORNER_FOCUS[0], p.at[1] - bushes.CORNER_FOCUS[1])
        dx, dy = pointing(p)
        assert (dx * out[0] + dy * out[1]) / math.hypot(*out) > math.cos(math.radians(50)), p


def test_the_face_is_rosettes_facing_the_viewer(layout):
    face = role(layout, 'face')
    assert len(face) >= 6
    assert all(p.piece.startswith('rosette-') for p in face)


def test_rosettes_just_above_the_rim_spill_their_lower_leaves_over_it(layout):
    rim = role(layout, 'rim')
    assert len(rim) >= 3
    for p in rim:
        assert p.piece.startswith('rosette-large-'), p
        assert rim_front(p.at[0]) - leaf_size(p) < p.at[1] < rim_front(p.at[0]), p


def test_nothing_spills_over_the_bare_stretch_of_rim_at_the_frames_corner(layout):
    lo, hi = bushes.CORNER_RIM_CLEAR
    assert not [p for p in role(layout, 'rim') if lo <= p.at[0] <= hi]


def test_the_leaves_are_bigger_at_the_foot_of_the_bush_than_at_its_top(layout):
    face = sorted(role(layout, 'face'), key=lambda p: p.at[1])
    third = len(face) // 3
    top, foot = face[:third], face[-third:]
    assert sum(map(leaf_size, foot)) / len(foot) > 1.15 * sum(map(leaf_size, top)) / len(top)


def test_the_edge_paints_first_then_the_face_from_the_top_down_then_the_rim(layout):
    order = {'edge': 0, 'face': 1, 'rim': 2}
    assert [order[p.role] for p in layout] == sorted(order[p.role] for p in layout)
    face = [p.at[1] for p in role(layout, 'face')]
    assert face == sorted(face)

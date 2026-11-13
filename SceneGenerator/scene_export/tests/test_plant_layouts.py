import math

import pytest

from scene_export import GENERATOR  # noqa: F401
from plants import branches
from plants import foliage
from furniture import planters

PLANTS = ['left urn bush', 'right urn bush', 'crystal planter back bush', 'crystal planter front bush']


@pytest.fixture(scope='module')
def plants():
    return planters.plant_layouts()


def role(plant, name):
    return [p for p in plant.layout if p.role == name]


def leaf_size(p):
    kind, size_name = p.piece.split('-')[:2]
    sizes = branches.ROSETTE_SIZES if kind == 'rosette' else branches.BRANCH_SIZES
    return sizes[size_name][1 if kind == 'rosette' else 0] * p.scale


def nearest(p, others):
    """How far p is from the nearest of others, in p's own leaf lengths."""
    return min(math.dist(p.at, q.at) for q in others if q is not p) / leaf_size(p)


def test_every_plant_but_the_corner_bush_is_laid_out_from_library_pieces(plants):
    ids = {p.id for p in branches.library()}
    assert sorted(plants) == sorted(PLANTS)
    for name, plant in plants.items():
        assert plant.layout and all(p.piece in ids for p in plant.layout), name


def test_every_piece_grows_from_inside_its_plant(plants):
    for name, plant in plants.items():
        for p in plant.layout:
            assert foliage._inside(plant.outline, *p.at), (name, p)


def test_edge_branches_point_away_from_the_plants_soil(plants):
    for name, plant in plants.items():
        edge = role(plant, 'edge')
        assert len(edge) >= 2, name
        for p in edge:
            out = (p.at[0] - plant.focus[0], p.at[1] - plant.focus[1])
            dx, dy = math.sin(p.rotation), -math.cos(p.rotation)
            assert (dx * out[0] + dy * out[1]) / math.hypot(*out) > math.cos(math.radians(50)), (name, p)


def test_the_face_is_rosettes_sized_to_the_plants_leaves(plants):
    for name, plant in plants.items():
        face = role(plant, 'face')
        assert len(face) >= 3, name
        assert all(p.piece.startswith('rosette-') for p in face), name
        mean = sum(map(leaf_size, face)) / len(face)
        assert 0.7 * plant.leaf < mean < 1.5 * plant.leaf, (name, mean, plant.leaf)


def test_face_rosettes_stand_as_far_apart_as_on_the_hand_thinned_corner_bush(plants):
    for name, plant in plants.items():
        face = role(plant, 'face')
        assert min(nearest(p, face) for p in face) >= 0.8, name


def test_edge_branches_stand_as_far_apart_as_on_the_hand_thinned_corner_bush(plants):
    for name, plant in plants.items():
        edge = role(plant, 'edge')
        assert min(nearest(p, edge) for p in edge) >= 0.85, name


def test_nothing_spills_over_the_rim_as_on_the_hand_thinned_corner_bush(plants):
    for name, plant in plants.items():
        assert not role(plant, 'rim'), name

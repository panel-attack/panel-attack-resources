import re

import numpy as np
import pytest
from scipy.spatial import cKDTree

from scene_export import GENERATOR  # noqa: F401
from furniture import planters

URNS = ['Left urn', 'Right urn']
POT = ['foot', 'stem', 'collar', 'bowl', 'rim', 'rim top']
AXIS_TOLERANCE = 1.5      # sheet px
MATCH_TOLERANCE = 1.0


@pytest.fixture(scope='module')
def drawn():
    shapes = {}
    for group in URNS:
        out = planters.Out()
        planters.urn(out, planters.SCENE, group, planters.URN_SEEDS[group])
        shapes[group] = {m.group(1): points(m.group(2)) for line in out.body
                         for m in [re.search(r'<path id="([^"]+)" d="([^"]+)"', line)] if m}
    return shapes


def points(d):
    nums = [float(v) for v in re.sub('[MLZ,]', ' ', d).split()]
    return np.array(list(zip(nums[0::2], nums[1::2])))


def scan(polygon, y):
    xs = []
    for (x0, y0), (x1, y1) in zip(polygon, np.roll(polygon, -1, axis=0)):
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return xs


def silhouette(shapes, group):
    """(y, left x, right x) of the pot's outline, every px from its rim to its foot."""
    polys = [shapes['%s %s' % (group, part)] for part in POT]
    top = min(p[:, 1].min() for p in polys)
    bottom = max(p[:, 1].max() for p in polys)
    rows = []
    for y in np.arange(np.ceil(top) + 0.5, bottom - 0.5):
        xs = [x for p in polys for x in scan(p, y)]
        if xs:
            rows.append((y, min(xs), max(xs)))
    return np.array(rows)


def axis(shapes, group):
    rows = silhouette(shapes, group)
    return float(np.median((rows[:, 1] + rows[:, 2]) / 2))


def named(shapes, prefix):
    return np.concatenate([p for k, p in shapes.items() if k.startswith(prefix)])


def mirror_gap(a, b, x):
    """How far the worst point of a, mirrored about the column x, lies from the nearest point of b."""
    m = np.column_stack([2 * x - a[:, 0], a[:, 1]])
    return float(cKDTree(b).query(m)[0].max())


@pytest.mark.parametrize('group', URNS)
def test_every_row_of_the_pot_is_centred_on_one_axis(drawn, group):
    rows = silhouette(drawn[group], group)
    centres = (rows[:, 1] + rows[:, 2]) / 2
    off = np.abs(centres - np.median(centres))
    assert off.max() <= AXIS_TOLERANCE, 'row y %.1f is %.1f px off the axis' % (rows[off.argmax(), 0], off.max())


@pytest.mark.parametrize('group', URNS)
@pytest.mark.parametrize('gem', ['bowl gem', 'rim gem'])
def test_each_gem_is_centred_on_the_pot_axis(drawn, group, gem):
    pts = named(drawn[group], '%s %s' % (group, gem))
    centre = (pts[:, 0].min() + pts[:, 0].max()) / 2
    assert abs(centre - axis(drawn[group], group)) <= AXIS_TOLERANCE


@pytest.mark.parametrize('group', URNS)
def test_each_gem_stands_upright(drawn, group):
    rim = drawn[group]['%s bowl gem rim' % group]
    top, bottom = rim[rim[:, 1].argmin()], rim[rim[:, 1].argmax()]
    assert abs(top[0] - bottom[0]) <= AXIS_TOLERANCE


@pytest.mark.parametrize('group', URNS)
def test_the_rim_leaves_mirror_about_the_pot_axis(drawn, group):
    pts = named(drawn[group], '%s rim leaf' % group)
    assert mirror_gap(pts, pts, axis(drawn[group], group)) <= AXIS_TOLERANCE


@pytest.mark.parametrize('group', URNS)
@pytest.mark.parametrize('part', ['mass', 'flower stem', 'vine'])
def test_an_urn_has_no_bush_mass_bare_flower_stems_or_hanging_vines(drawn, group, part):
    assert not [k for k in drawn[group] if k.startswith('%s %s' % (group, part))]


def test_the_right_urns_pot_matches_the_left_ones(drawn):
    left, right = (silhouette(drawn[g], g) for g in URNS)
    shift = axis(drawn['Right urn'], 'Right urn') - axis(drawn['Left urn'], 'Left urn')
    assert len(left) == len(right)
    assert np.abs(right[:, 1:] - shift - left[:, 1:]).max() <= MATCH_TOLERANCE


def test_the_right_urns_rim_leaves_match_the_left_ones(drawn):
    left, right = (named(drawn[g], '%s rim leaf' % g) for g in URNS)
    shift = axis(drawn['Right urn'], 'Right urn') - axis(drawn['Left urn'], 'Left urn')
    moved = right - np.array([shift, 0.0])
    assert float(cKDTree(left).query(moved)[0].max()) <= MATCH_TOLERANCE


@pytest.mark.parametrize('group', URNS)
def test_an_urns_bowl_has_no_upright_highlight_stripe(drawn, group):
    assert '%s bowl sheen' % group not in drawn[group]

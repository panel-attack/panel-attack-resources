from scenery.valley_reference import HILLS
from common.painting import f
from structures import windmill


def knoll_y(x):
    points = next(p for name, _, p in HILLS if name == 'windmill knoll')
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    raise ValueError(x)


def test_placing_moves_the_drawn_hub_onto_the_hub():
    assert windmill.placed(*windmill.DRAWN_HUB) == windmill.HUB


def test_placing_scales_about_the_hub():
    hx, hy = windmill.DRAWN_HUB
    x, y = windmill.placed(hx + 10, hy - 20)
    assert (x - windmill.HUB[0], y - windmill.HUB[1]) == (10 * windmill.PLACE_SCALE, -20 * windmill.PLACE_SCALE)


def test_a_placed_path_moves_every_point():
    hx, hy = windmill.DRAWN_HUB
    d = windmill.placed_path('M%s,%s L%s,%s Z' % (hx, hy, hx + 10, hy))
    assert d == 'M%s,%s L%s,%s Z' % (f(windmill.HUB[0]), f(windmill.HUB[1]), f(windmill.HUB[0] + 10 * windmill.PLACE_SCALE),
                                     f(windmill.HUB[1]))


def test_the_tower_stands_on_the_knoll():
    x, foot = windmill.placed(windmill.TOWER_AXIS_FOOT, windmill.TOWER_FOOT)
    assert 0 <= foot - knoll_y(x) <= 6


def test_every_fence_post_stands_on_the_knoll():
    for posts in windmill.FENCE_RUNS.values():
        for (x, foot), _ in posts:
            px, py = windmill.placed(x, foot)
            assert abs(py - knoll_y(px) - windmill.FENCE_SINK) < 1e-6


def test_the_fence_mirrors_about_the_tower():
    axis = windmill.placed(windmill.TOWER_AXIS_FOOT, windmill.TOWER_FOOT)[0]
    left = [windmill.placed(*foot) for foot, _ in windmill.FENCE_RUNS['left fence']]
    right = [windmill.placed(*foot) for foot, _ in windmill.FENCE_RUNS['right fence']]
    assert len(left) == len(right)
    for (lx, ly), (rx, ry) in zip(left, reversed(right)):
        assert abs((axis - lx) - (rx - axis)) < 1e-6
        assert abs(ly - ry) < 1e-6


def test_the_door_stands_on_the_tower_floor():
    assert windmill.DOOR[3] == windmill.TOWER_FOOT


def test_the_tower_is_lit_on_its_right_and_shaded_on_its_left():
    y = (windmill.TOWER_TOP + windmill.TOWER_FOOT) / 2
    axis = windmill.tower_x(y, 0.5)
    assert min(windmill.tower_x(y, s) for s in windmill.LIT_STRIP) > axis
    assert max(windmill.tower_x(y, s) for s in windmill.SHADE_STRIP) < axis


def test_fence_posts_are_evenly_spaced():
    for posts in windmill.FENCE_RUNS.values():
        gaps = [b[0][0] - a[0][0] for a, b in zip(posts, posts[1:])]
        assert max(gaps) - min(gaps) < 1e-6

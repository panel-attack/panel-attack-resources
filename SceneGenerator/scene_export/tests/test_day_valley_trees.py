from DayValley import DayValley


def test_a_copse_grows_all_its_trees_close_together():
    for hill, x, count, spread, _ in DayValley.COPSES:
        trees = [t for t in DayValley.copse_trees() if t[1] == hill and abs(t[2] - x) <= spread / 2]
        assert len(trees) == count


def test_the_farthest_hill_is_wooded_across_its_width():
    xs = sorted(x for _, hill, x, _, _ in DayValley.copse_trees() + DayValley.BACK_TREES if hill == 'hills far')
    assert len(xs) >= 30
    assert max(b - a for a, b in zip([0] + xs, xs + [1536])) <= 260


def test_no_copse_tree_stands_behind_the_hill_in_front():
    points = {name: pts for name, _, pts in DayValley.HILLS}
    for _, hill, x, drop, _ in DayValley.copse_trees():
        assert DayValley.hill_under((x, DayValley.edge_y(points[hill], x) + drop)) == hill


def test_the_far_hills_grow_firs_among_their_oaks():
    far = {name for name, depth, _ in DayValley.HILLS if depth <= 0.25}
    trees = [t for t in DayValley.copse_trees() + DayValley.BACK_TREES if t[1] in far]
    firs = [t for t in trees if t[0].startswith('pine-')]
    assert 0.3 <= len(firs) / len(trees) <= 0.6

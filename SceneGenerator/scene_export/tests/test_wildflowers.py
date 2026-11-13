from plants import wildflowers


def stem_length(tid):
    _, kind, args = next(t for t in wildflowers.TEMPLATES if t[0] == tid)
    return args[3]


def test_every_flower_has_a_short_and_a_tall_stemmed_variant():
    for tid, kind, _ in wildflowers.TEMPLATES:
        if kind in ('flower', 'tulip') and not tid.endswith(('-short', '-tall')):
            assert stem_length(tid + '-short') < stem_length(tid) < stem_length(tid + '-tall')


def test_a_bowed_stem_bends_to_one_side_and_ends_back_over_its_foot():
    pts = wildflowers.stem_points(40, 0.05)
    assert max(x for x, _ in pts) == 40 * 0.05
    assert abs(pts[-1][0]) < 1e-9

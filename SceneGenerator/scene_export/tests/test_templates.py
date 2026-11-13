import math

from scene_export import templates as T
from scene_export.capture import Foliage


def rose(rot):
    return T.flower_template('rose', {'c': (10, 20), 'radius': 34.0, 'rot': rot, 'squash': 0.88})


def test_a_rose_uses_the_template_turned_nearest_its_own_swirl(monkeypatch):
    monkeypatch.setattr(T, 'ROSE_TURNS', (1.0, 4.0))
    assert rose(4.2).template.rot == 4.0
    assert rose(1.1).template.rot == 1.0
    assert rose(1.0 + 2 * math.pi).template.rot == 1.0


def test_a_stem_is_placed_from_the_stem_template_reaching_its_tip():
    pl = T.place(Foliage('twig', 's', {'base': (10.0, 20.0), 'angle': 0.4, 'length': 37.0, 'width': 3.0}))
    a, b, c, d, e, f = pl.matrix()
    x, y = 0.0, -pl.template.length
    assert pl.template.id == 'stem'
    assert math.isclose(a * x + c * y + e, 10 + 37 * math.cos(0.4), abs_tol=1e-6)
    assert math.isclose(b * x + d * y + f, 20 + 37 * math.sin(0.4), abs_tol=1e-6)
    assert math.isclose(abs(pl.xscale) * pl.template.width, 3.0)

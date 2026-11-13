from common.painting import Svg
from scenery import valley


def test_the_valley_has_no_road():
    svg = Svg()
    valley.valley(svg)
    assert not any(part.startswith('<g id="road') for part in svg.parts)

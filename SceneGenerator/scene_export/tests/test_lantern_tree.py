import colorsys
import re

import pytest

from common.painting import hexrgb
from EsmeTerrace import rail
from plants import foliage, lantern_tree, lantern_tree_template
from scene_export import cutting


def hanger_parts():
    return {tid: part for tid, part in lantern_tree.cut() if tid.partition('lantern-tree-')[2] in lantern_tree.HANGERS}


def test_each_hanger_pivots_where_it_hangs():
    """A lantern's or the banner's image has the point it hangs from at its top centre, so a topCenter pivot is it."""
    for tid, part in hanger_parts().items():
        hang, _ = lantern_tree.HANGERS[tid.partition('lantern-tree-')[2]]
        x, y, w, h = part.box
        assert (x + w / 2, y) == hang, tid


def test_each_hanger_hangs_from_the_reach_limb():
    for name, (hang, _) in lantern_tree.HANGERS.items():
        assert lantern_tree.distance_to_limb(hang, lantern_tree.HANGER_LIMB) == 0, name


def test_hanger_templates_anchor_and_pivot_at_the_top_centre():
    nodes = {n['id']: n for n in lantern_tree_template.build()['drawables']}
    for name in lantern_tree.HANGERS:
        node = nodes['lantern-tree-' + name]
        assert node['anchor'] == 'topCenter' and node['pivot'] == 'topCenter', name
    for name in ('crown-back', 'trunk', 'crown'):
        assert 'anchor' not in nodes['lantern-tree-' + name]


def test_a_hang_box_puts_the_hang_point_at_its_top_centre():
    x, y, w, h = lantern_tree.hang_box((10.5, 20.0, 30.0, 70.2), (18, 20), 4)
    assert (x + w / 2, y) == (18, 20)
    assert w % 2 == 0 and h % 2 == 0
    assert x <= 10.5 - 4 and x + w >= 30.0 + 4 and y + h >= 70.2 + 4


def test_one_lantern_and_the_banner_hang_from_the_limb():
    assert set(lantern_tree.HANGERS) == {'lantern-left', 'banner'}


def banner_ids():
    lantern_tree.main()
    root, _ = cutting.load('plants/lantern_tree.svg')
    return [el.get('id') for el in cutting.find_group(root, 'lantern tree banner').iter() if el.tag.endswith('path')]


def test_the_banner_hangs_its_cloth_over_a_rod_tied_to_the_limb():
    """A round gold rod with a finial at each end, tied to the limb by a cord at each end, the cloth's top wrapped
    over the rod as a sleeve: no plank and no single rope."""
    ids = banner_ids()
    assert sum(bool(re.fullmatch(r'cord( \d+)?', i)) for i in ids) == 2
    assert sum(bool(re.fullmatch(r'finial( \d+)?', i)) for i in ids) == 2
    assert any(i.startswith('rod') for i in ids)
    assert any(i.startswith('sleeve') for i in ids)
    assert not any(i.startswith(('bar', 'rope')) for i in ids)


def test_the_lantern_and_the_banner_hang_well_apart_and_well_below_the_limb():
    """The reach limb runs out far enough left that the lantern and the banner hang well apart, each on a long
    rope or long cords so it hangs well below the limb, as in lantern-tree.jpg."""
    (lantern_x, _), _ = lantern_tree.HANGERS['lantern-left']
    (banner_x, _), _ = lantern_tree.HANGERS['banner']
    (_, _, tip), _ = lantern_tree.LIMBS[lantern_tree.HANGER_LIMB]
    assert tip[0] <= 1300
    assert banner_x - lantern_x >= 90
    assert lantern_tree.LANTERN['chain'] >= 50
    assert lantern_tree.BANNER['cord'][0] >= 45


# the Esme Terrace's outline style at the foreground's distance: every shape edged in its own hue at about 0.5 to 0.7
# of its value, never near-black or navy, LEAF_OUTLINE on the leaves and GOLD_LINE on the gold, 3 px outlines and
# 1.5 to 2 px detail lines
ESME_HUE_TOLERANCE = 40          # degrees between an outline's hue and its body's, as the Esme leaf outline is off its leaves
ESME_LINE_WIDTHS = (2.0, 3.0)    # px on the sheet, the Esme outlines' range (its leaves 2.5 to 3, its gold 3)
ESME_DETAIL_WIDTHS = (1.5, 3.0)  # ... and its detail lines' (gem outlines 1.5 to 2.5)


ESME_VALUE_SHARE = (0.4, 0.8)    # an Esme line's HSV value as a share of its body's (its leaves 0.45, its gold 0.5)
ESME_SATURATION = 0.45           # an Esme line stays this saturated (HSV): a colour, never black or navy


def hsv(colour):
    r, g, b = (c / 255 for c in hexrgb(colour))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s, v


def not_near_black(colour):
    """A line that is a colour, not black or navy: not too dark and still saturated."""
    _, s, v = hsv(colour)
    return v >= 0.3 and s >= ESME_SATURATION


def dark_shade_of(line, fill):
    """Whether line is fill's own hue at the Esme lines' share of its value."""
    (lh, _, lv), (fh, _, fv) = hsv(line), hsv(fill)
    return (ESME_VALUE_SHARE[0] <= lv / fv <= ESME_VALUE_SHARE[1]
            and min(abs(lh - fh), 360 - abs(lh - fh)) <= ESME_HUE_TOLERANCE and not_near_black(line))


def tree_strokes():
    lantern_tree.main()
    root, _ = cutting.load('plants/lantern_tree.svg')
    for el in cutting.find_group(root, 'lantern tree').iter():
        stroke = el.get('stroke')
        if stroke and stroke.startswith('#'):
            yield el.get('id'), stroke


@pytest.mark.parametrize('palette', ['CLOUD', 'BARK', 'ROPE', 'GOLD', 'CLOTH'])
def test_each_outline_is_a_dark_shade_of_its_own_colour(palette):
    colours = getattr(lantern_tree, palette)
    assert dark_shade_of(colours['line'], colours['body']), (palette, colours['line'])


def test_the_crown_and_the_gold_take_the_esme_lines():
    assert lantern_tree.CLOUD['line'] == foliage.LEAF_OUTLINE
    assert lantern_tree.GOLD['line'] == rail.GOLD_LINE


def test_no_stroke_in_the_tree_is_near_black():
    """Every line that is not a tint of the thing it marks (a groove in the bark's deep, a ring in the gold's shade)."""
    tints = {colour for palette in ('CLOUD', 'BARK', 'ROPE', 'GOLD', 'CLOTH', 'CRYSTAL')
             for key, colour in getattr(lantern_tree, palette).items() if key != 'line'}
    for ident, stroke in tree_strokes():
        if stroke not in tints:
            assert not_near_black(stroke), (ident, stroke)


def test_the_outlines_are_as_thin_as_esmes():
    assert ESME_LINE_WIDTHS[0] <= lantern_tree.SILHOUETTE_LINE <= ESME_LINE_WIDTHS[1]
    assert ESME_LINE_WIDTHS[0] <= lantern_tree.BARK_LINE <= ESME_LINE_WIDTHS[1]
    assert ESME_DETAIL_WIDTHS[0] <= lantern_tree.DETAIL_LINE <= ESME_DETAIL_WIDTHS[1]


def test_each_cluster_of_the_crown_is_outlined_on_its_own():
    """As the Esme bushes edge every leaf, each cluster carries its own outline, so a dark green edge parts it from
    the cluster behind it instead of one outline round the whole crown."""
    lantern_tree.main()
    root, _ = cutting.load('plants/lantern_tree.svg')
    for group, places in (('lantern tree crown', lantern_tree.CLUSTERS), ('lantern tree crown-back', lantern_tree.CLUSTERS_BACK)):
        ids = [el.get('id') or '' for el in cutting.find_group(root, group).iter()]
        assert sum(i.startswith('cluster outline') for i in ids) == len(places), group


def test_the_crowns_shade_is_a_shade_of_its_own_green():
    """The shade along the clusters' undersides is the Esme leaves' darker green, not a teal rim."""
    assert dark_shade_of(lantern_tree.CLOUD['under'], lantern_tree.CLOUD['body'])
    assert lantern_tree.CLOUD['under'] == foliage.LEAF_SHADE_DEEP['leaf-dark']

import re
import xml.etree.ElementTree as ET

import pytest

from common.painting import Svg
from scene_export import svgtools
from scenery import alps_reference, landscape, spring_peaks
from scenery import spring_peaks_reference as ref


# The train meadow's peaks are the terrace's mountain generator drawing Esme's ranges with variation: Esme's
# palette, haze, ridge line and snow layers, the train meadow's own layout of peaks.
def drawn(draw):
    svg = Svg()
    draw(svg)
    return ET.fromstring('<svg xmlns="%s">%s</svg>' % (svgtools.SVG_NS, '\n'.join(svg.parts)))


def colours(root):
    return set(re.findall(r'#[0-9a-fA-F]{6}', ET.tostring(root, encoding='unicode')))


def group(root, gid):
    return root.find(".//*[@id='%s']" % gid)


def base_id(el):
    """An element's id without the number the sheet adds to repeats: 'snow 3' is a 'snow'."""
    return re.sub(r' \d+$', '', el.get('id', ''))


def snow_peaks(root):
    return [g for g in root.iter() if base_id(g) == 'snow peak']


@pytest.fixture(scope='module')
def esme():
    def draw(svg):
        landscape.mountains(svg, alps_reference.FAR_RANGES, snowy=None, haze=alps_reference.HAZE,
                            foot=alps_reference.FOOT, outline=alps_reference.OUTLINE, group='far')
        landscape.mountains(svg, alps_reference.MASSIF_RANGES, snowy='massif', snow=alps_reference.SNOWCAP,
                            haze=alps_reference.HAZE, foot=alps_reference.FOOT, outline=alps_reference.OUTLINE,
                            group='massif')
    return drawn(draw)


@pytest.fixture(scope='module')
def peaks():
    return drawn(spring_peaks.spring_peaks)


def test_the_rock_haze_and_ridge_line_are_esmes():
    assert ref.HAZE is alps_reference.HAZE
    assert ref.OUTLINE is alps_reference.OUTLINE
    assert not hasattr(ref, 'FAR_OUTLINE')


def test_every_mountain_colour_is_one_esmes_mountains_use(esme, peaks):
    esme_colours = colours(esme)
    for name, gid, _ in spring_peaks.IMAGES:
        if name != 'foothills':
            assert colours(group(peaks, gid)) <= esme_colours, name


def test_there_is_no_snowcap_code_or_palette_of_its_own():
    for gone in ('cap', 'tongues', 'capped', 'ridge_at', 'along'):
        assert not hasattr(spring_peaks, gone), gone
    for gone in ('CAPS', 'TOOTH', 'SHADED_SHARE', 'SNOW', 'FAR_OUTLINE'):
        assert not hasattr(ref, gone), gone


def test_the_massifs_snow_is_the_snowcap_in_esmes_four_layers(esme, peaks):
    esme_layers = {base_id(p): p.get('fill') for p in group(esme, 'snow peak')}
    ours = {base_id(p): p.get('fill') for p in snow_peaks(group(peaks, 'Massif'))[0]}
    assert ours == esme_layers
    assert set(ours) == {'light rock', 'snow shade', 'snow', 'snow streaks'}


def test_the_massif_stands_over_the_middle_with_snowy_peaks_on_its_left(peaks):
    snow = next(p for p in group(peaks, 'Massif').iter() if base_id(p) == 'snow')
    x0, _, x1, _ = svgtools.element_bbox(snow)
    assert 0.55 * landscape.WIDTH < (x0 + x1) / 2 < 0.72 * landscape.WIDTH
    assert len(snow_peaks(group(peaks, 'Left peaks'))) >= 2
    assert not snow_peaks(group(peaks, 'Far ranges'))


def test_cut_keeps_the_five_images_the_train_meadow_places():
    assert list(spring_peaks.cut()) == ['far ranges', 'left peaks', 'massif', 'right peak', 'foothills']

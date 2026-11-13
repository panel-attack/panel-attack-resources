#   Writes SVG, run by `python3 -m scene_export render`: scenery/spring_peaks.svg, the train meadow's snowy blue
#   mountains drawn as the day valley's are (scenery/alps.py, scenery/landscape.py): the pale far range across the
#   back, the snowy peaks on the left, the big snow-capped peak above the train (Massif) and the peak in front of its
#   right flank, and the forested foothills along their feet, each its own image. Every range and snowcap is laid
#   out in scenery/spring_peaks_reference.py in the day valley's palette.
#
#   python3 -m scenery.spring_peaks  ->  spring_peaks.svg

import os

from common.painting import Svg
from scene_export import cutting
from scenery import spring_peaks_reference as ref
from scenery.landscape import mountains

HERE = os.path.dirname(os.path.abspath(__file__))


# (image name, group id, its ranges back to front)
IMAGES = [('far ranges', 'Far ranges', ref.FAR_RANGES),
          ('left peaks', 'Left peaks', ref.LEFT_RANGES),
          ('massif', 'Massif', ref.MASSIF_RANGES),
          ('right peak', 'Right peak', ref.RIGHT_RANGES),
          ('foothills', 'Foothills', ref.FOOTHILL_RANGES)]


def spring_peaks(svg):
    svg.open('Spring Peaks')
    for name, group, ranges in IMAGES:
        mountains(svg, ranges, snowy=None, haze=ref.HAZE, foot=ref.FOOT, outline=ref.OUTLINE, group=group)
    svg.close()


def main():
    svg = Svg()
    spring_peaks(svg)
    svg.write(cutting.sheet_path('scenery/spring_peaks.svg'))


def cut():
    """{name: its image}: each group of peaks, back to front, where it sits."""
    root, grads = cutting.load('scenery/spring_peaks.svg')
    return {name: cutting.static_part('scenery/parts/spring-peaks/' + cutting.slug(name),
                                      [cutting.find_group(root, group)], grads, name)
            for name, group, _ in IMAGES}


def parts():
    return list(cut().values())


if __name__ == '__main__':
    main()

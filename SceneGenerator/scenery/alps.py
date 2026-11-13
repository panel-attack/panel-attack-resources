#   Writes SVG, run by `python3 -m scene_export render`: scenery/alps.svg, the day valley's mountains drawn as the
#   terrace's are (scenery/landscape.py): the low lilac ranges across the back on both sides (Far range), and the
#   big snow-capped peak right of centre with its small snowy shoulder peak (Massif).
#
#   python3 -m scenery.alps  ->  alps.svg

import os

from common.painting import Svg
from scene_export import cutting
from scenery.alps_reference import FAR_RANGES, FOOT, HAZE, MASSIF_RANGES, OUTLINE, SNOWCAP
from scenery.landscape import mountains

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    svg = Svg()
    svg.open('Alps')
    svg.open('Far range')
    mountains(svg, FAR_RANGES, snowy=None, haze=HAZE, foot=FOOT, outline=OUTLINE, group='far ranges')
    svg.close()
    svg.open('Massif')
    mountains(svg, MASSIF_RANGES, snowy='massif', snow=SNOWCAP, haze=HAZE, foot=FOOT, outline=OUTLINE,
              group='massif ranges')
    svg.close()
    svg.close()
    svg.write(cutting.sheet_path('scenery/alps.svg'))


def cut():
    """{'far range': the far range's image, 'massif': the massif's}"""
    root, grads = cutting.load('scenery/alps.svg')
    return {name: cutting.static_part('scenery/parts/alps/' + cutting.slug(name),
                                      [cutting.find_group(root, group)], grads, name)
            for name, group in (('far range', 'Far range'), ('massif', 'Massif'))}


def parts():
    return list(cut().values())


if __name__ == '__main__':
    main()

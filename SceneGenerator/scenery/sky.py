#   Writes SVG, run by `python3 -m scene_export render`: scenery/sky.svg, the skies behind everything: the
#   Esme terrace's, behind the train meadow too, and the day valley's.
#
#   python3 -m scenery.sky  ->  sky.svg

import os

from common.painting import HEIGHT, WIDTH, Svg, mix
from scene_export import cutting

HERE = os.path.dirname(os.path.abspath(__file__))


SKY_TOP, SKY_HORIZON = '#22b0fb', '#7ae6fd'


SKY_GRADIENT_END = 383           # y where the sky reaches its pale colour

def colour_at(y):
    return mix(SKY_TOP, SKY_HORIZON, min(1.0, max(0.0, y / SKY_GRADIENT_END)))


def sky(svg):
    svg.open('Sky')
    svg.path('M0,0 H%d V%d H0 Z' % (WIDTH, HEIGHT), (SKY_TOP, SKY_HORIZON, 0, SKY_GRADIENT_END), name='sky')
    svg.close()


# The day valley's sky, measured off DayValley/meadow-stage.png as (y, colour) stops: deep blue at the top paling
# faster and faster toward the mountains, then held at the horizon colour down past the visible band.
DAY_VALLEY_STOPS = ((80, '#37aefd'), (140, '#3cb2fc'), (180, '#4abdfd'), (260, '#69cef8'), (400, '#86dafa'),
                    (620, '#a6e3fd'))


def day_valley_sky(svg):
    """The kit's gradients have two stops, so the sky is one full-height rectangle per stretch between stops,
    each starting where the one under it reaches the stretch's first colour, so they join without a seam."""
    svg.open('Sky Day Valley')
    for (y0, a), (y1, b) in zip(DAY_VALLEY_STOPS, DAY_VALLEY_STOPS[1:]):
        top = 0 if y0 == DAY_VALLEY_STOPS[0][0] else y0
        svg.path('M0,%d H%d V%d H0 Z' % (top, WIDTH, HEIGHT), (a, b, y0, y1), name='sky')
    svg.close()


def main():
    svg = Svg()
    sky(svg)
    day_valley_sky(svg)
    svg.write(cutting.sheet_path('scenery/sky.svg'))


def parts():
    root, grads = cutting.load('scenery/sky.svg')
    return [cutting.static_part('scenery/parts/sky/sky', [cutting.find_group(root, 'Sky')], grads, 'sky'),
            cutting.static_part('scenery/parts/sky/sky-day-valley', [cutting.find_group(root, 'Sky Day Valley')], grads,
                                'sky-day-valley')]


if __name__ == '__main__':
    main()

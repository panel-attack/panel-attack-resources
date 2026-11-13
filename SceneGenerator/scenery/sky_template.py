#   Writes JSON, run by `python3 -m scene_export layout`: scenery/sky.json in the game's scenes/, a template per sky.
#
#   python3 -m scenery.sky_template  ->  the game's scenes/scenery/sky.json

from scene_export import cutting, layout
from scenery import sky

OUTPUT = 'scenery/sky.json'
TEMPLATE = 'sky-esme-terrace'
DAY_VALLEY_TEMPLATE = 'sky-day-valley'


def build():
    terrace, day_valley = sky.parts()
    return {'drawables': [cutting.image_template(TEMPLATE, terrace),
                          cutting.image_template(DAY_VALLEY_TEMPLATE, day_valley)]}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

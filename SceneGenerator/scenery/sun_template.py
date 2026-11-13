#   Writes JSON, run by `python3 -m scene_export layout`: scenery/sun.json in the game's scenes/, the sun template.
#
#   python3 -m scenery.sun_template  ->  the game's scenes/scenery/sun.json

from scene_export import cutting, layout
from scenery import sun

OUTPUT = 'scenery/sun.json'
TEMPLATE = 'sun'


def build():
    return {'drawables': [cutting.image_template(TEMPLATE, sun.parts()[0])]}


if __name__ == '__main__':
    layout.write(OUTPUT)

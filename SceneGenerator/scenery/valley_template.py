#   Writes JSON, run by `python3 -m scene_export layout`: scenery/valley.json in the game's scenes/, a template per
#   valley part: each hill back to front, then the meadow.
#
#   python3 -m scenery.valley_template  ->  the game's scenes/scenery/valley.json

from scene_export import cutting, layout
from scenery import valley

OUTPUT = 'scenery/valley.json'


def build():
    return {'drawables': [cutting.image_template(cutting.slug(name), part) for name, part in valley.cut().items()]}


if __name__ == '__main__':
    layout.write(OUTPUT)

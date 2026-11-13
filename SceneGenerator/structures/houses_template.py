#   Writes JSON, run by `python3 -m scene_export layout`: structures/houses.json in the game's scenes/, a
#   template per house.
#
#   python3 -m structures.houses_template  ->  the game's scenes/structures/houses.json

from scene_export import cutting, layout
from structures import houses

OUTPUT = 'structures/houses.json'


def build():
    return {'drawables': [cutting.image_template(tid, part) for _, tid, part in houses.cut()]}


if __name__ == '__main__':
    layout.write(OUTPUT)

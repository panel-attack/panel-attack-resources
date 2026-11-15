#   Writes JSON, run by `python3 -m scene_export layout`: structures/airship.json in the game's scenes/, the
#   template of Magellan's airship, one image.
#
#   python3 -m structures.airship_template  ->  the game's scenes/structures/airship.json

from scene_export import cutting, layout
from structures import airship

OUTPUT = 'structures/airship.json'


def build():
    return {'drawables': [cutting.image_template(tid, part) for tid, part in airship.cut()]}


if __name__ == '__main__':
    layout.write(OUTPUT)

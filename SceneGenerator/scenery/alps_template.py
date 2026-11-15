#   Writes JSON, run by `python3 -m scene_export layout`: scenery/alps.json in the game's scenes/, the day valley's
#   far range and massif templates.
#
#   python3 -m scenery.alps_template  ->  the game's scenes/scenery/alps.json

from scene_export import cutting, layout
from scenery import alps

OUTPUT = 'scenery/alps.json'
TEMPLATES = {'far range': 'alps-far-range', 'massif': 'alps-massif'}


def build():
    images = alps.cut()
    return {'drawables': [cutting.image_template(tid, images[name]) for name, tid in TEMPLATES.items()]}


if __name__ == '__main__':
    layout.write(OUTPUT)

#   Writes JSON, run by `python3 -m scene_export layout`: scenery/landscape.json in the game's scenes/, the
#   landscape, the far village (the meadow and its trees) and the lake's two sets of glints templates.
#
#   python3 -m scenery.landscape_template  ->  the game's scenes/scenery/landscape.json

from scene_export import cutting, layout
from scenery import landscape

OUTPUT = 'scenery/landscape.json'
TEMPLATES = {'background': 'landscape-esme-terrace', 'far village': 'far-village', 'shimmer a': 'lake-shimmer-a',
             'shimmer b': 'lake-shimmer-b'}


def build():
    images = landscape.cut()
    return {'drawables': [cutting.image_template(tid, images[name]) for name, tid in TEMPLATES.items()]}


if __name__ == '__main__':
    layout.write(OUTPUT)

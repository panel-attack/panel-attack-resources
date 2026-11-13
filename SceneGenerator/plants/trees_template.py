#   Writes JSON, run by `python3 -m scene_export layout`: plants/trees.json in the game's scenes/, the cypress
#   and leafy clump templates, each standing on its foot.
#
#   python3 -m plants.trees_template  ->  the game's scenes/plants/trees.json

from scene_export import layout
from plants import trees

OUTPUT = 'plants/trees.json'


def build():
    return {'drawables': [{'id': p.path.rpartition('/')[2], 'filePath': p.path, 'anchor': 'bottomCenter',
                           'pivot': 'bottomCenter', 'templateOnly': True} for p in trees.parts()]}


if __name__ == '__main__':
    layout.write(OUTPUT)

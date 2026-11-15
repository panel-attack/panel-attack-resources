#   Writes JSON, run by `python3 -m scene_export layout`: plants/pines.json in the game's scenes/, the day
#   valley's fir templates, each standing on its foot.
#
#   python3 -m plants.pines_template  ->  the game's scenes/plants/pines.json

from scene_export import layout
from plants import pines

OUTPUT = 'plants/pines.json'


def build():
    return {'drawables': [{'id': p.path.rpartition('/')[2], 'filePath': p.path, 'anchor': 'bottomCenter',
                           'pivot': 'bottomCenter', 'templateOnly': True} for p in pines.parts()]}


if __name__ == '__main__':
    layout.write(OUTPUT)

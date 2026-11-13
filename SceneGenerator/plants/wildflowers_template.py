#   Writes JSON, run by `python3 -m scene_export layout`: plants/wildflowers.json in the game's scenes/, the day
#   valley's meadow flower and grass tuft templates, each standing on its foot.
#
#   python3 -m plants.wildflowers_template  ->  the game's scenes/plants/wildflowers.json

from scene_export import layout
from plants import wildflowers

OUTPUT = 'plants/wildflowers.json'


def build():
    return {'drawables': [{'id': p.path.rpartition('/')[2], 'filePath': p.path, 'anchor': 'bottomCenter',
                           'pivot': 'bottomCenter', 'templateOnly': True} for p in wildflowers.parts()]}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

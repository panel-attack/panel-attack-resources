#   Writes JSON, run by `python3 -m scene_export layout`: plants/meadow_flowers.json in the game's scenes/, the train
#   meadow's foreground flower and mossy rock templates, each standing on its foot, so a placed flower sways about
#   the foot of its stem.
#
#   python3 -m plants.meadow_flowers_template  ->  the game's scenes/plants/meadow_flowers.json

from scene_export import layout
from plants import meadow_flowers

OUTPUT = 'plants/meadow_flowers.json'


def build():
    return {'drawables': [{'id': p.path.rpartition('/')[2], 'filePath': p.path, 'anchor': 'bottomCenter',
                           'pivot': 'bottomCenter', 'templateOnly': True} for p in meadow_flowers.parts()]}


if __name__ == '__main__':
    layout.write(OUTPUT)

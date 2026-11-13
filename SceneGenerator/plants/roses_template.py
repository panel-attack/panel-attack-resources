#   Writes JSON, run by `python3 -m scene_export layout`: plants/roses.json in the game's scenes/, the
#   rose templates the planters, the corner bush and branches.py's pieces place.
#
#   python3 -m plants.roses_template  ->  the game's scenes/plants/roses.json

from scene_export import layout, placed_foliage

OUTPUT = 'plants/roses.json'


def build():
    return placed_foliage.template_file('roses')


if __name__ == '__main__':
    layout.write(OUTPUT)

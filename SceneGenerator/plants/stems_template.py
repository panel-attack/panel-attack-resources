#   Writes JSON, run by `python3 -m scene_export layout`: plants/stems.json in the game's scenes/, the
#   stem templates the planters, the corner bush and branches.py's pieces place.
#
#   python3 -m plants.stems_template  ->  the game's scenes/plants/stems.json

from scene_export import layout, placed_foliage

OUTPUT = 'plants/stems.json'


def build():
    return placed_foliage.template_file('stems')


if __name__ == '__main__':
    layout.write(OUTPUT)

#   Writes JSON, run by `python3 -m scene_export layout`: plants/leaves.json in the game's scenes/, the
#   leaf templates the planters, the corner bush and branches.py's pieces place.
#
#   python3 -m plants.leaves_template  ->  the game's scenes/plants/leaves.json

from scene_export import layout, placed_foliage

OUTPUT = 'plants/leaves.json'


def build():
    return placed_foliage.template_file('leaves')


if __name__ == '__main__':
    layout.write(OUTPUT)

#   Writes JSON, run by `python3 -m scene_export layout`: plants/branches.json in the game's scenes/, every
#   piece of branches.py's library as a template drawn from the leaf and stem templates.
#
#   python3 -m plants.branches_template  ->  the game's scenes/plants/branches.json

from scene_export import layout, placed_foliage

OUTPUT = 'plants/branches.json'


def build():
    return {'drawables': placed_foliage.placed().library}


if __name__ == '__main__':
    layout.write(OUTPUT)

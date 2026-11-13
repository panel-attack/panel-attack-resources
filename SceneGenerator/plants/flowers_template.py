#   Writes JSON, run by `python3 -m scene_export layout`: plants/flowers.json in the game's scenes/, the
#   flower, daisy and bud templates the planters, the corner bush and branches.py's pieces place.
#
#   python3 -m plants.flowers_template  ->  the game's scenes/plants/flowers.json

from scene_export import layout, placed_foliage

OUTPUT = 'plants/flowers.json'


def build():
    return placed_foliage.template_file('flowers')


if __name__ == '__main__':
    layout.write(OUTPUT)

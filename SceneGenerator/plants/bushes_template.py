#   Writes JSON, run by `python3 -m scene_export layout`: plants/bushes.json in the game's scenes/, the corner
#   bush template: its image and the refs to its library pieces and flowers, swaying in the wind.
#
#   python3 -m plants.bushes_template  ->  the game's scenes/plants/bushes.json

from scene_export import cutting, layout, placed_foliage, wind

OUTPUT = 'plants/bushes.json'
TEMPLATES = {'corner bush': 'corner-bush'}


def build():
    children = placed_foliage.placed().children
    return {'drawables': [cutting.object_template(tid, wind.swayed(placed_foliage.named_by_reference(obj, children[obj])))
                          for obj, tid in TEMPLATES.items()]}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

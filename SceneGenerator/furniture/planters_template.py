#   Writes JSON, run by `python3 -m scene_export layout`: furniture/planters.json in the game's scenes/, a
#   template per planter: its images and the refs to its library pieces and flowers, swaying in the wind.
#
#   python3 -m furniture.planters_template  ->  the game's scenes/furniture/planters.json

from scene_export import cutting, layout, placed_foliage, wind

OUTPUT = 'furniture/planters.json'
TEMPLATES = {'crystal planter': 'crystal-planter', 'left urn': 'left-urn', 'right urn': 'right-urn'}


def build():
    children = placed_foliage.placed().children
    return {'drawables': [cutting.object_template(tid, wind.swayed(placed_foliage.named_by_reference(obj, children[obj])))
                          for obj, tid in TEMPLATES.items()]}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

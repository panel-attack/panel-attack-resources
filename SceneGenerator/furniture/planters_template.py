#   Writes JSON, run by `python3 -m scene_export layout`: furniture/planters.json in the game's scenes/, a
#   template per planter: its images and the refs to its library pieces and flowers, swaying in the wind.
#
#   python3 -m furniture.planters_template  ->  the game's scenes/furniture/planters.json

from scene_export import cutting, layout
from EsmeTerrace import placements

OUTPUT = 'furniture/planters.json'
TEMPLATES = {'crystal planter': 'crystal-planter', 'left urn': 'left-urn', 'right urn': 'right-urn'}


def build():
    return {'drawables': [cutting.object_template(tid, placements.object_children(obj)) for obj, tid in TEMPLATES.items()]}


if __name__ == '__main__':
    layout.write(OUTPUT)

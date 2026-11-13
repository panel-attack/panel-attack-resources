#   Writes JSON, run by `python3 -m scene_export layout`: scenery/clouds.json in the game's scenes/, a template
#   per cloud.
#
#   python3 -m scenery.clouds_template  ->  the game's scenes/scenery/clouds.json

from scene_export import cutting, layout
from scenery import clouds

OUTPUT = 'scenery/clouds.json'


def template_id(cloud_id):
    name = cutting.slug(cloud_id)
    return name if name.startswith('cloud') else 'cloud-' + name


def build():
    return {'drawables': [cutting.image_template(template_id(cid), part) for cid, part in clouds.cut_all()]}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

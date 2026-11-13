#   Writes JSON, run by `python3 -m scene_export layout`: scenery/spring_valley.json in the game's scenes/, a template
#   per part of the train meadow's land: each hill back to front, the woods, the bushes, the track and the meadow.
#
#   python3 -m scenery.spring_valley_template  ->  the game's scenes/scenery/spring_valley.json

from scene_export import cutting, layout
from scenery import spring_valley

OUTPUT = 'scenery/spring_valley.json'


def template_id(name):
    return 'spring-valley-' + cutting.slug(name)


def build():
    return {'drawables': [cutting.image_template(template_id(name), part) for name, part in spring_valley.cut().items()]}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

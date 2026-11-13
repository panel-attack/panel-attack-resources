#   Writes JSON, run by `python3 -m scene_export layout`: scenery/spring_peaks.json in the game's scenes/, a template
#   per group of the train meadow's peaks, back to front.
#
#   python3 -m scenery.spring_peaks_template  ->  the game's scenes/scenery/spring_peaks.json

from scene_export import cutting, layout
from scenery import spring_peaks

OUTPUT = 'scenery/spring_peaks.json'


def template_id(name):
    return 'spring-peaks-' + cutting.slug(name)


def build():
    return {'drawables': [cutting.image_template(template_id(name), part) for name, part in spring_peaks.cut().items()]}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

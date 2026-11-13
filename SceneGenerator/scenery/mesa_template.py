#   Writes JSON, run by `python3 -m scene_export layout`: scenery/mesa.json in the game's scenes/, the gear-arch
#   mesa's templates: the mesa with its ring and trees, the waterfall and the spray at its foot. The waterfall's
#   image repeats and scrolls down one period a loop, so the water falls without a seam.
#
#   python3 -m scenery.mesa_template  ->  the game's scenes/scenery/mesa.json

from scene_export import cutting, layout
from scenery import mesa

OUTPUT = 'scenery/mesa.json'

FALL_SECONDS = 0.9               # one period of the water's fall; a far-off fall moves slowly


def falling():
    """The track scrolling the strip down one period, in scene units (half its pixels), then starting over."""
    return [{'repeat': 'loop', 'steps': [{'durationSeconds': FALL_SECONDS, 'easeType': 'linear',
                                          'animateProperties': {'scrollY': -mesa.FALL_PERIOD / 2}}]}]


def build():
    out = []
    for tid, part in mesa.cut():
        node = cutting.image_template(tid, part)
        if tid == 'mesa-waterfall':
            node.update(wrap='repeat', animationTracks=falling())
        out.append(node)
    return {'drawables': out}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

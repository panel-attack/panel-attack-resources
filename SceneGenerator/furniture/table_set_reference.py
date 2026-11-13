#   Writes PNG and JSON into panel-attack-references/furniture/table-set/ when run on its own (render never runs
#   it): the reference crops and landmarks table_set.py fits to. Imported, it writes nothing.
#
#   Landmarks of the table set measured on its own reference painting,
#   panel-attack-references/furniture/table-set/source.png (577 x 400, a close-up of the set: a round
#   cream marble top on a gold hourglass lattice pedestal set with blue gems, two
#   gold chairs either side with quilted heart backs, tufted cushions and scrolled
#   cabriole legs). Read off 3x zoom crops with a 10 px grid, in source px.
#   table_set.py fits its 3D pieces to these, and `python3 -m furniture.table_set check` prints the
#   error of every landmark.
#
#   The painting is laid on the stage by one scale and offset (to_stage), chosen
#   so the set fills the area the old set did: the pedestal's axis on
#   table_set.TABLE_SCREEN and the chairs' crests and feet spanning the same height.
#
#   python3 -m furniture.table_set_reference [painting.png]
#       copies the painting to panel-attack-references/furniture/table-set/source.png (when given) and
#       writes, per piece and for the whole set, <slug>.png beside it
#       (its crop resampled to stage px) and <slug>.json (where the crop came
#       from, where it goes on the 1536 x 1024 canvas and its landmarks in stage px).
#
#   Landmark kinds, all in source px here:
#     points    named (x, y)
#     rings     a horizontal circle as the ellipse it draws: cx, cy, a, b
#     boxes     (x0, y0, x1, y1); None for a side hidden behind another piece
#     diamonds  a gem: centre (x, y) and half sizes (w, h)
#     feet      the centre of each visible scroll foot's curl

import json
import os
import re
import shutil
import sys

from PIL import Image

from scene_export import REFERENCES
FOLDER = os.path.join(REFERENCES, 'furniture', 'table-set')
SOURCE = 'source.png'
SCALE = 1.15
OFFSET = (903.0, 520.0)
SOURCE_SIZE = (577, 400)
# The painting's pedestal leans: the top is centred on 291.7, the waist on 288.5 and the foot
# on 287.5; the axis is taken between them.
TABLE_AXIS_X = 289.3

PIECES = {
    'table': {
        'box': (130, 95, 452, 340),
        'rings': {
            'marble': dict(cx=291.7, cy=123.0, a=154.5, b=23.5),
            'base': dict(cx=286.0, cy=328.5, a=84.0, b=17.0),        # the foot disc's floor ring, front 345.5
        },
        'points': {
            'band front bottom': (291.7, 163.3),
            'pedestal top left': (210.0, 165.0), 'pedestal top right': (370.0, 165.0),
            'waist left': (250.0, 233.0), 'waist right': (327.0, 233.0),
            'lower bottom left': (219.0, 300.0), 'lower bottom right': (355.0, 300.0),   # where the straps meet the foot
        },
        'boxes': {
            'collar': (247.4, 237.0, 328.0, 253.0),
        },
        # the painting sets its gems 5 or 6 px left of its axis; ours are centred, as the clean example's,
        # so the lattice mirrors about them
        'diamonds': {
            'upper gem': dict(centre=(TABLE_AXIS_X, 203.5), half=(17.0, 26.5)),
            'lower gem': dict(centre=(TABLE_AXIS_X, 289.0), half=(14.5, 26.0)),
        },
        'feet': [],
    },
    'chair back left': {
        'box': (30, 15, 212, 328),
        'points': {'crest top': (71.7, 23.3), 'back left': (35.0, 76.7), 'back right': (128.0, 93.0)},
        'boxes': {'heart': (60.0, 53.3, 107.0, 143.3), 'cushion': (None, 161.7, 205.0, 206.0)},
        'feet': [(146.7, 318.3)],
    },
    'chair front left': {
        'box': (5, 80, 215, 385),
        'points': {'crest top': (31.7, 87.0), 'back left': (11.7, 143.0), 'rail bottom': (150.0, 278.0)},
        'boxes': {'cushion': (None, 213.5, 208.5, 265.0)},
        'diamonds': {'back gem': dict(centre=(42.0, 171.7), half=(14.0, 31.7))},
        'feet': [(36.7, 340.0), (105.0, 371.7), (203.3, 346.7)],
    },
    'chair back right': {
        'box': (355, 17, 535, 330),
        'points': {'crest top': (488.7, 25.0), 'back left': (438.7, 76.7), 'back right': (527.0, 93.0)},
        'boxes': {'heart': (453.7, 63.3, 503.7, 150.0), 'cushion': (362.0, 165.0, None, 206.0)},
        'feet': [(432.0, 321.7)],
    },
    'chair front right': {
        'box': (360, 80, 577, 385),
        'points': {'crest top': (557.0, 86.7), 'back left': (500.3, 143.0), 'rail bottom': (432.0, 280.0)},
        'boxes': {'cushion': (370.3, 216.7, None, 266.7)},
        'diamonds': {'back gem': dict(centre=(543.0, 174.0), half=(14.0, 32.5))},
        'feet': [(367.0, 356.7), (478.7, 375.0), (547.0, 346.7)],
    },
}


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def to_stage(p):
    return (OFFSET[0] + p[0] * SCALE, OFFSET[1] + p[1] * SCALE)


def _r(v):
    return round(v, 3)


def box_to_stage(box):
    """(x0, y0, x1, y1) in stage px, a hidden (None) side staying None."""
    return [None if v is None else OFFSET[i % 2] + v * SCALE for i, v in enumerate(box)]


def stage_landmarks(piece):
    """The piece's landmarks with every position and size in stage px."""
    pt = lambda p: [_r(v) for v in to_stage(p)]
    out = {}
    if piece.get('points'):
        out['points'] = {k: pt(p) for k, p in piece['points'].items()}
    if piece.get('rings'):
        out['rings'] = {k: dict(zip(('cx', 'cy'), pt((r['cx'], r['cy']))), a=_r(r['a'] * SCALE), b=_r(r['b'] * SCALE))
                        for k, r in piece['rings'].items()}
    if piece.get('boxes'):
        out['boxes'] = {k: [None if v is None else _r(v) for v in box_to_stage(b)] for k, b in piece['boxes'].items()}
    if piece.get('diamonds'):
        out['diamonds'] = {k: dict(centre=pt(d['centre']), half=[_r(v * SCALE) for v in d['half']])
                           for k, d in piece['diamonds'].items()}
    out['feet'] = [pt(f) for f in piece.get('feet', [])]
    return out


def stage_box(box):
    return [_r(v) for v in to_stage(box[:2]) + to_stage(box[2:])]


def crop(image, box):
    x0, y0, x1, y1 = stage_box(box)
    return image.crop(box).resize((round(x1 - x0), round(y1 - y0)), Image.LANCZOS)


def describe(name, box, landmarks):
    return dict(name=name, slug=slug(name), source=SOURCE, source_box=list(box),
                stage_box=stage_box(box), scale=SCALE, **landmarks)


def write(folder, name, image, box, landmarks):
    crop(image, box).save(os.path.join(folder, slug(name) + '.png'))
    with open(os.path.join(folder, slug(name) + '.json'), 'w') as f:
        json.dump(describe(name, box, landmarks), f, indent=1)
        f.write('\n')


def generate(painting, folder=FOLDER):
    os.makedirs(folder, exist_ok=True)
    source = os.path.join(folder, SOURCE)
    if os.path.abspath(painting) != os.path.abspath(source):
        shutil.copyfile(painting, source)
    image = Image.open(source).convert('RGBA')
    if image.size != SOURCE_SIZE:
        raise ValueError('%s is %d x %d, the landmarks were read off a %d x %d painting'
                         % ((painting,) + image.size + SOURCE_SIZE))
    pieces = {slug(n): stage_landmarks(p) for n, p in PIECES.items()}
    write(folder, 'table set', image, (0, 0) + SOURCE_SIZE, {'pieces': pieces})
    for name, piece in PIECES.items():
        write(folder, name, image, piece['box'], stage_landmarks(piece))


if __name__ == '__main__':
    generate(sys.argv[1] if len(sys.argv) > 1 else os.path.join(FOLDER, SOURCE))
    print('wrote', os.path.relpath(FOLDER))

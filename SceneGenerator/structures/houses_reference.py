#   Writes PNG and JSON into panel-attack-references/structures/houses/ when run on its own (render never runs
#   it): the reference crops houses.py draws the houses from. Imported, it writes nothing.
#
#   The town's eight houses, measured off panel-attack-references/structures/houses/source.png (the Houses reference: the town
#   beyond the balcony, 695 x 275 px) and laid onto the stage.
#
#   Every house is a list of flat faces drawn back to front, each a named polygon
#   (or an 'ellipse') with a tone from TONES, plus arched windows as (x0, y0, x1, y1) boxes. Here the
#   corners are in source px, read off 6-14x zoom crops with a 5 px grid. Wall bottoms hidden behind
#   the reference's trees and flowers run down to the house's foot.
#
#   A house lands on the stage at the one shared SCALE plus its own offset (stage px), so the houses keep
#   the reference's sizes relative to each other. The manor, its orange wing and the two towers overlap
#   in the reference, so they share one offset; the others are spread along the stage's town band where
#   the urns, the crystal and the cypresses leave them room.
#
#   python3 -m structures.houses_reference  ->  panel-attack-references/structures/houses/: source.png, and per house <slug>.png (its crop of
#   the source, resampled to its stage box) and <slug>.json (its boxes, scale and stage px faces).

import json
import os
import re
import shutil

from scene_export import REFERENCES

REFERENCE_DIR = os.path.join(REFERENCES, 'structures', 'houses')
SOURCE = os.path.join(REFERENCE_DIR, 'source.png')
SCALE = 1.3                     # stage px per source px

CLUSTER = (480.0, 260.5)        # manor, orange wing, tall tower, small tower
CLUSTER_FOOT = 346              # source px, past the reference's foot (222): the cluster's walls run down behind
                                # the terrace rail to its foot, so they show between its balusters

HOUSES = [
    {
        'name': 'far gable',
        'offset': (426.6, 203.5),
        'faces': [
            ('wall', 'far gable wall', [(121, 218), (129, 218), (129, 232), (121, 232)]),
            ('gable lit', 'far gable lit', [(124.5, 205), (119.5, 219), (125.5, 219)]),
            ('gable shade', 'far gable shade', [(124.5, 205), (125.5, 219), (130, 219)]),
        ],
        'windows': [],
    },
    {
        'name': 'far right house',
        'offset': (469.8, 309.3),
        'faces': [
            ('chimney lit', 'chimney lit', [(628.5, 90), (631, 90), (631, 95), (628.5, 95)]),
            ('chimney shade', 'chimney shade', [(631, 90), (633, 90), (633, 95), (631, 95)]),
            ('chimney cap', 'house chimney cap', [(628, 88.8), (633.5, 88.8), (633.5, 90.5), (628, 90.5)]),
            ('wall front', 'house wall lit', [(609, 121), (640.5, 121), (640.5, 162), (609, 162)]),
            ('roof', 'orange roof', [(624, 94), (647, 94), (643.5, 119), (603.5, 119)]),
            ('eave', 'orange eave', [(603.5, 118.5), (643.5, 118.5), (643, 121.5), (604.5, 121.5)]),
            ('dormer wall', 'house wall lit', [(624.5, 106.5), (629, 106.5), (629, 113.5), (624.5, 113.5)]),
            ('dormer glass', 'house glass', [(625.5, 108), (628, 108), (628, 113), (625.5, 113)]),
            ('dormer roof', 'orange dormer', [(623.5, 107.5), (626.5, 104), (629.5, 107.5)]),
            ('dormer roof side', 'orange dormer side', [(626.5, 104), (632, 104.5), (637, 108), (631, 113),
                                                         (629.5, 107.5)]),
        ],
        'windows': [(616, 128, 619, 141), (628, 128, 632, 141)],
    },
    {
        'name': 'cottage',
        'offset': (450.9, 213.0),
        'faces': [
            ('chimney lit', 'chimney lit', [(65, 203), (67, 203), (67, 208), (65, 208)]),
            ('chimney shade', 'chimney shade', [(67, 203), (68.5, 203), (68.5, 208), (67, 208)]),
            ('chimney cap', 'house chimney cap', [(64.5, 201.8), (69, 201.8), (69, 203.5), (64.5, 203.5)]),
            ('wall front', 'house wall lit', [(41, 229), (80, 229), (80, 252), (41, 252)]),
            ('wall side', 'house wall shade', [(80, 229), (85.5, 229), (85.5, 252), (80, 252)]),
            ('roof front', 'orange roof', [(54, 207), (89, 207.5), (80, 228), (38, 227)]),
            ('roof hip', 'orange roof hip', [(89, 207.5), (90.5, 208), (86, 228), (80, 228)]),
            ('eave', 'orange eave', [(37.5, 226.5), (86.5, 227.5), (86, 230), (38, 229.5)]),
            ('dormer wall', 'house wall lit', [(58, 219.5), (63, 219.5), (63, 225.5), (58, 225.5)]),
            ('dormer glass', 'house glass', [(59.2, 220.8), (61.8, 220.8), (61.8, 225), (59.2, 225)]),
            ('dormer roof', 'orange dormer', [(57, 220.5), (60.5, 216), (64, 220.5)]),
            ('dormer roof side', 'orange dormer side', [(60.5, 216), (66, 216), (69, 221), (63.5, 224), (64, 220.5)]),
        ],
        'windows': [(48, 233, 50.5, 240), (61, 234, 64, 241), (71, 235, 75, 243)],
    },
    {
        'name': 'red house',
        'offset': (396.8, 242.5),
        'faces': [
            ('chimney left', 'chimney lit', [(187, 170.5), (190, 170.5), (190, 176), (187, 176)]),
            ('chimney middle lit', 'chimney lit', [(210, 168), (212.5, 168), (212.5, 176), (210, 176)]),
            ('chimney middle shade', 'chimney shade', [(212.5, 168), (214.5, 168), (214.5, 176), (212.5, 176)]),
            ('chimney middle cap', 'house chimney cap', [(209, 166.5), (215, 166.5), (215, 168.5), (209, 168.5)]),
            ('chimney right lit', 'chimney lit', [(226, 168), (228.5, 168), (228.5, 176), (226, 176)]),
            ('chimney right shade', 'chimney shade', [(228.5, 168), (230.5, 168), (230.5, 176), (228.5, 176)]),
            ('chimney right cap', 'house chimney cap', [(225.5, 166.5), (231, 166.5), (231, 168.5),
                                                        (225.5, 168.5)]),
            ('wall front', 'house wall lit', [(169, 200), (224, 200), (224, 240), (169, 240)]),
            ('wall side', 'house wall shade', [(224, 200), (236, 200), (236, 240), (224, 240)]),
            ('roof front', 'rose roof', [(179, 175), (234, 175), (226, 198), (164.5, 198)]),
            ('roof hip', 'rose roof hip', [(234, 175), (242, 186.5), (238, 198), (226, 198)]),
            ('eave', 'rose eave', [(164, 197), (238.5, 197), (237.5, 200.5), (165, 200.5)]),
            ('dormer wall', 'house wall lit', [(188, 187), (193, 187), (193, 196), (188, 196)]),
            ('dormer glass', 'house glass', [(189.3, 189.5), (191.7, 189.5), (191.7, 195), (189.3, 195)]),
            ('dormer roof', 'rose dormer', [(186.5, 188), (190, 183.5), (193.5, 188)]),
            ('dormer roof side', 'rose dormer side', [(190, 183.5), (197, 184), (201, 188.5), (194.5, 192),
                                                       (193.5, 188)]),
        ],
        'windows': [(175.5, 206, 179, 215), (187, 206, 190.5, 215), (198, 206, 201, 215)],
    },
    {
        'name': 'tall tower',
        'offset': CLUSTER,
        'faces': [
            ('wall front', 'tower wall lit', [(454, 71), (474.5, 71), (474.5, CLUSTER_FOOT), (454, CLUSTER_FOOT)]),
            ('wall side', 'tower wall shade', [(474.5, 71), (498.5, 71), (498.5, CLUSTER_FOOT), (474.5, CLUSTER_FOOT)]),
            ('spire lit', 'terracotta spire lit', [(476, 19), (450.5, 69.5), (475.5, 69.5)]),
            ('spire shade', 'terracotta spire shade', [(476, 19), (475.5, 69.5), (503, 69.5)]),
            ('eave', 'terracotta spire eave', [(450, 69), (503.5, 69), (503, 72), (451, 72)]),
            ('finial stem', 'finial gold', [(475.6, 14), (476.4, 14), (476.4, 19.5), (475.6, 19.5)]),
            ('finial ball', 'finial gold', 'ellipse', (476, 12.5, 4.5, 3.6)),
            ('finial spike', 'finial gold', [(475, 9.5), (476, 2.5), (477, 9.5)]),
        ],
        'windows': [(462.5, 79, 465.5, 92), (484, 79, 487, 92), (485, 115, 487.5, 123)],
    },
    {
        'name': 'small tower',
        'offset': CLUSTER,
        'faces': [
            ('wall front', 'tower wall lit', [(515, 107), (537, 107), (537, CLUSTER_FOOT), (515, CLUSTER_FOOT)]),
            ('wall side', 'tower wall shade', [(537, 107), (561, 107), (561, CLUSTER_FOOT), (537, CLUSTER_FOOT)]),
            ('spire lit', 'red spire lit', [(537.5, 61), (510.5, 105.5), (537, 105.5)]),
            ('spire shade', 'red spire shade', [(537.5, 61), (537, 105.5), (565.5, 105.5)]),
            ('eave', 'red spire eave', [(510, 105), (566, 105), (565, 108), (511, 108)]),
            ('finial stem', 'finial gold', [(537.1, 56), (537.9, 56), (537.9, 61.5), (537.1, 61.5)]),
            ('finial ball', 'finial gold', 'ellipse', (537.5, 54.5, 3.0, 2.6)),
            ('finial spike', 'finial gold', [(536.8, 52.5), (537.5, 49), (538.2, 52.5)]),
        ],
        'windows': [(523, 115, 527, 128), (547, 115, 550.5, 127)],
    },
    {
        'name': 'orange wing',
        'offset': CLUSTER,
        'faces': [
            ('chimney left lit', 'chimney lit', [(353, 122.5), (355.5, 122.5), (355.5, 131), (353, 131)]),
            ('chimney left shade', 'chimney shade', [(355.5, 122.5), (358, 122.5), (358, 131), (355.5, 131)]),
            ('chimney left cap', 'house chimney cap', [(352.5, 121), (358.5, 121), (358.5, 123), (352.5, 123)]),
            ('chimney right lit', 'chimney lit', [(368.5, 122.5), (371, 122.5), (371, 131), (368.5, 131)]),
            ('chimney right shade', 'chimney shade', [(371, 122.5), (373.5, 122.5), (373.5, 131), (371, 131)]),
            ('chimney right cap', 'house chimney cap', [(368, 121), (374, 121), (374, 123), (368, 123)]),
            ('wall front', 'house wall lit', [(328, 166), (366, 166), (366, CLUSTER_FOOT), (328, CLUSTER_FOOT)]),
            ('roof', 'orange roof', [(349, 131), (388, 131), (396, 165), (323.5, 165.5)]),
            ('eave', 'orange eave', [(323, 164.5), (396, 164.5), (396, 167.5), (324, 167.5)]),
            ('dormer wall', 'house wall lit', [(351, 154.5), (356, 154.5), (356, 161), (351, 161)]),
            ('dormer glass', 'house glass', [(352.3, 155.8), (354.7, 155.8), (354.7, 160), (352.3, 160)]),
            ('dormer roof', 'orange dormer', [(349.5, 155.5), (353.5, 149.5), (357.5, 155.5)]),
            ('dormer roof side', 'orange dormer side', [(353.5, 149.5), (358.5, 149.5), (363, 154.5),
                                                         (357.5, 155.5)]),
        ],
        'windows': [(341, 176, 346, 189), (356.5, 177, 360.5, 195)],
    },
    {
        'name': 'manor',
        'offset': CLUSTER,
        'faces': [
            ('chimney left lit', 'chimney lit', [(410, 100), (417, 100), (417, 120), (410, 120)]),
            ('chimney left shade', 'chimney shade', [(417, 100), (424, 100), (424, 120), (417, 120)]),
            ('chimney left cap', 'slate cap', [(408, 96.5), (425, 96.5), (425, 100.5), (408, 100.5)]),
            ('chimney right lit', 'chimney lit', [(433, 100), (440, 100), (440, 118), (433, 118)]),
            ('chimney right shade', 'chimney shade', [(440, 100), (447, 100), (447, 118), (440, 118)]),
            ('chimney right cap', 'slate cap', [(431.5, 96.5), (448.5, 96.5), (448.5, 100.5), (431.5, 100.5)]),
            ('wall front', 'manor wall lit', [(362, 175), (422.5, 175), (422.5, CLUSTER_FOOT), (362, CLUSTER_FOOT)]),
            ('wall side', 'manor wall shade', [(422.5, 175), (488, 175), (488, CLUSTER_FOOT), (422.5, CLUSTER_FOOT)]),
            ('roof', 'slate roof', [(394, 115), (460.5, 115), (495, 171), (424, 174)]),
            ('roof hip', 'manor slate hip', [(394, 115), (357, 171.5), (424, 174)]),
            ('eave', 'slate roof eave', [(356, 171), (424, 173.5), (495.5, 170.5), (495.5, 173.5), (424, 176.5),
                                         (357, 174.5)]),
            ('dormer left wall', 'house wall lit', [(386.5, 157), (393.5, 157), (393.5, 165), (386.5, 165)]),
            ('dormer left glass', 'house glass', [(388.3, 158.3), (391.7, 158.3), (391.7, 164), (388.3, 164)]),
            ('dormer left roof', 'slate dormer', [(384.5, 158), (390, 151.5), (395.5, 158)]),
            ('dormer right wall', 'manor wall shade', [(448, 154), (458.5, 154), (458.5, 164.5), (448, 164.5)]),
            ('dormer right glass', 'house glass', [(453.5, 156), (457.5, 156), (457.5, 163.5), (453.5, 163.5)]),
            ('dormer right roof', 'slate dormer', [(445.5, 154.5), (451, 147), (457, 147), (460, 154)]),
        ],
        'windows': [(378, 184, 383, 200), (401, 184, 406, 201), (437, 184, 442, 201), (456, 182, 460.5, 198),
                    (471, 182, 475, 196)],
    },
]

# fill per tone: a colour, or (top, bottom) for a vertical gradient; sampled from the source's faces where
# its trees and flowers leave them clear
TONES = {
    'house wall lit': ('#fbeabf', '#f0d9ac'),
    'house wall shade': ('#d2bba6', '#c1a894'),
    'manor wall lit': ('#fcedc2', '#f5e0b2'),
    'manor wall shade': ('#c9b49c', '#c4b195'),
    'tower wall lit': ('#fbefc8', '#f1dfb6'),
    'tower wall shade': ('#c9b4a6', '#bea898'),
    'chimney lit': '#efe6d6',
    'chimney shade': '#b5a49d',
    'house chimney cap': '#c9b5ae',
    'house glass': ('#3c4f70', '#5a6c8c'),
    'orange roof': ('#fb9a60', '#fca86c'),
    'orange roof hip': '#d27a5a',
    'orange eave': '#a0614f',
    'orange dormer': '#e48a5c',
    'orange dormer side': '#b0614b',
    'rose roof': ('#eb828a', '#f18884'),
    'rose roof hip': '#b0697a',
    'rose eave': '#a4707a',
    'rose dormer': '#e98a90',
    'rose dormer side': '#9c5872',
    'terracotta spire lit': ('#fba06f', '#fb9565'),
    'terracotta spire shade': ('#9a5253', '#9c505d'),
    'terracotta spire eave': '#674f58',
    'red spire lit': ('#f99377', '#fb8c73'),
    'red spire shade': ('#9d4d5a', '#a25361'),
    'red spire eave': '#7f535f',
    'finial gold': ('#f8eb5f', '#f4bf2b'),
    'slate cap': '#3f6fa6',
    'slate roof': ('#3364a8', '#3667ac'),
    'manor slate hip': ('#93abd6', '#8aa3d0'),
    'slate roof eave': '#325481',
    'slate dormer': '#638ec7',
    'far gable wall': '#e2d8bc',
    'far gable lit': '#d58087',
    'far gable shade': '#8b7884',
}
WINDOW_TONE = 'house glass'


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def _to_stage(house, x, y):
    dx, dy = house['offset']
    return (x * SCALE + dx, y * SCALE + dy)


def _face_points(face):
    if face[2] == 'ellipse':
        cx, cy, rx, ry = face[3]
        return [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    return face[2]


def source_box(house):
    pts = [p for face in house['faces'] for p in _face_points(face)]
    pts += [(w[0], w[1]) for w in house['windows']] + [(w[2], w[3]) for w in house['windows']]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def stage_box(house):
    x0, y0, x1, y1 = source_box(house)
    return _to_stage(house, x0, y0) + _to_stage(house, x1, y1)


def stage_building(house):
    """The house as draw_faces draws it, in stage px."""
    faces = []
    for face in house['faces']:
        if face[2] == 'ellipse':
            cx, cy, rx, ry = face[3]
            faces.append((face[0], face[1], 'ellipse', _to_stage(house, cx, cy) + (rx * SCALE, ry * SCALE)))
        else:
            faces.append((face[0], face[1], [_to_stage(house, x, y) for x, y in face[2]]))
    windows = [_to_stage(house, w[0], w[1]) + _to_stage(house, w[2], w[3]) for w in house['windows']]
    return {'name': house['name'], 'faces': faces, 'windows': windows, 'window tone': WINDOW_TONE}


BUILDINGS = [stage_building(h) for h in HOUSES]


def house_json(house):
    staged = stage_building(house)
    faces = []
    for face in staged['faces']:
        entry = {'name': face[0], 'tone': face[1], 'fill': TONES.get(face[1])}
        if face[2] == 'ellipse':
            entry['ellipse'] = [round(v, 2) for v in face[3]]
        else:
            entry['points'] = [[round(x, 2), round(y, 2)] for x, y in face[2]]
        faces.append(entry)
    return {
        'name': house['name'],
        'slug': slug(house['name']),
        'source': 'source.png',
        'source_box': list(source_box(house)),
        'stage_box': [round(v, 2) for v in stage_box(house)],
        'scale': SCALE,
        'offset': list(house['offset']),
        'faces': faces,
        'windows': [[round(v, 2) for v in w] for w in staged['windows']],
    }


def write_reference(folder=REFERENCE_DIR):
    from PIL import Image

    os.makedirs(folder, exist_ok=True)
    if os.path.abspath(os.path.join(folder, 'source.png')) != os.path.abspath(SOURCE):
        shutil.copyfile(SOURCE, os.path.join(folder, 'source.png'))
    source = Image.open(SOURCE).convert('RGB')
    for house in HOUSES:
        doc = house_json(house)
        x0, y0, x1, y1 = doc['stage_box']
        crop = source.crop(tuple(round(v) for v in doc['source_box']))
        crop.resize((round(x1 - x0), round(y1 - y0)), Image.LANCZOS).save(os.path.join(folder, doc['slug'] + '.png'))
        with open(os.path.join(folder, doc['slug'] + '.json'), 'w') as f:
            json.dump(doc, f, indent=1)
            f.write('\n')


if __name__ == '__main__':
    write_reference()

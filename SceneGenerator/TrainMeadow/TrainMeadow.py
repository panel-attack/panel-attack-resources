#   Writes JSON, run by `python3 -m scene_export layout`: TrainMeadow/TrainMeadow.json in the game's scenes/, the
#   spring meadow the main menu shows, lit from the upper right. It draws, back to front: the sky, the clouds drifting
#   in the wind, the snowy peaks, the far hills with the gear-arch mesa and its waterfall among them, the woods and
#   the middle hills, the track with the train crossing on it, the bushes, the blossom tree framing the left and the
#   lantern tree framing the right in front of them, the meadow, and the big flowers and mossy rocks in front.
#
#   The track runs straight and level, parallel to the picture, so the train stays one distance away the whole way
#   across: drawn once as a pure side view, it only slides in x and never needs to change shape. It slides at the
#   speed its wheels turn, from wholly off the left edge to wholly off the right, waits out of sight, and comes again.
#
#   python3 -m TrainMeadow.TrainMeadow  ->  the game's scenes/TrainMeadow/TrainMeadow.json

import dataclasses

from scene_export import cutting, layout, wind
from scenery import clouds, clouds_template, mesa, mesa_template, sky, sky_template
from scenery import spring_peaks, spring_peaks_template, spring_valley, spring_valley_template
from structures import train, train_template
from plants import blossom, blossom_template, lantern_tree, lantern_tree_template, meadow_flowers, meadow_flowers_template
from plants import meadow_flowers_reference

OUTPUT = 'TrainMeadow/TrainMeadow.json'

# The terrace's clouds, back to front: (cloud id, the top left of its image in sheet px, its opacity). The same images
# the terrace drifts, placed over the peaks instead and thinned the further back they stand, so the sky reads as its
# own; half wait off the left edge for the wind to bring them in behind the ones in view, as the terrace's do.
SKY_CLOUDS = [
    ('cloud r4-20', (660, 215), 0.75),
    ('cloud r4-08', (1150, 205), 0.75),
    ('cloud right small', (830, 236), 0.7),
    ('cloud right', (-300, 225), 0.75),
    ('cloud r4-24', (-700, 200), 0.7),
    ('cloud r4-25', (-1100, 230), 0.75),
    ('cloud behind lamp', (-420, 60), 0.9),
    ('cloud mid', (700, 150), 0.85),
    ('cloud r4-23', (1090, 145), 0.85),
    ('cloud r4-34', (-1450, 110), 0.9),
    ('cloud r4-14', (-1200, 70), 0.85),
    ('cloud r4-09', (-700, 140), 0.85),
    ('cloud centre right', (640, 10), 1.0),
    ('cloud r4-27', (1140, -30), 0.95),
    ('cloud r4-33', (-900, 0), 1.0),
    ('cloud r4-06', (-250, -20), 0.95),
]
TRAIN_LENGTH = max(part.box[0] + part.box[2] for tid, part in train.cut()
                   if tid == 'train-loco') - train_template.TRAIN_ORIGIN[0]  # sheet px, rear to the loco's front
TRAIN_CLEAR = 50                    # canvas units past each edge the train starts and ends, so its smoke is gone too
TRAIN_WAIT = 12                     # seconds out of sight before the next crossing
HANGER_TEMPLATES = ['lantern-tree-' + name for name in lantern_tree.HANGERS]
HANGER_SWING = {'lantern-tree-lantern-left': (0.07, 2.6),
                'lantern-tree-banner': (0.04, 3.4)}            # (radians either way, seconds a swing)
CLUSTER_SWING = {'blossom-cluster-branch': (0.05, 3.0), 'blossom-cluster-top': (0.04, 3.6),
                 'blossom-cluster-edge': (0.07, 2.4)}          # (radians either way, seconds a swing)
FLOWER_SWAY = 0.5                   # of the terrace plants' sway in the wind


def num(v, places=3):
    return cutting.num(v, places)


def drifting_clouds():
    images, children = dict(clouds.cut()), []
    for cid, at, alpha in SKY_CLOUDS:
        part = dataclasses.replace(images[cid], box=at + images[cid].box[2:])
        node = cutting.image_ref(cid, clouds_template.OUTPUT, clouds_template.template_id(cid), part)
        if alpha < 1:
            node['overrides']['alpha'] = alpha
        node['overrides']['animationTracks'] = wind.drift(node['overrides'], cutting.length(part.box[2]), clouds.speed(cid))
        children.append(node)
    return {'id': 'clouds', 'children': children}


def placed(node_id, file, parts):
    """A ref to each template in parts, where its generator drew it."""
    return {'id': node_id, 'children': [cutting.image_ref(tid, file, tid, part) for tid, part in parts]}


def peaks():
    return {'id': 'peaks', 'children': [
        cutting.image_ref(name, spring_peaks_template.OUTPUT, spring_peaks_template.template_id(name), part)
        for name, part in spring_peaks.cut().items()]}


def land(names):
    parts = spring_valley.cut()
    return [cutting.image_ref(name, spring_valley_template.OUTPUT, spring_valley_template.template_id(name), parts[name])
            for name in names]


def crossing_train():
    start = -cutting.length(TRAIN_LENGTH) - TRAIN_CLEAR
    end = wind.SCENE_SIZE[0] + TRAIN_CLEAR
    return {'id': 'crossing train', 'ref': train_template.OUTPUT + '#train', 'overrides': {
        'position': {'x': num(start), 'y': cutting.corner(0, train.RAIL_Y)['y']},
        'animationTracks': [{'repeat': 'loop', 'steps': [
            {'delaySeconds': TRAIN_WAIT, 'durationSeconds': num((end - start) / cutting.length(train.TRAIN_SPEED), 4),
             'easeType': 'linear', 'animateProperties': {'x': num(end)}}]}]}}


def swinging(node, amount, seconds):
    """The node swinging about its pivot amount radians either way and back."""
    node['overrides']['rotation'] = -amount
    node['overrides']['animationTracks'] = [{'repeat': 'yoyo', 'steps': [
        {'durationSeconds': seconds, 'easeType': 'sineinout', 'animateProperties': {'rotation': amount}}]}]
    return node


def swinging_from_rest(node, amount, seconds):
    """The node hanging straight down at rest, swinging out amount radians one way, across to the other and back."""
    node['overrides']['animationTracks'] = [{'repeat': 'loop', 'steps': [
        {'durationSeconds': num(seconds / 2), 'easeType': 'sineout', 'animateProperties': {'rotation': amount}},
        {'durationSeconds': seconds, 'easeType': 'sineinout', 'animateProperties': {'rotation': -amount}},
        {'durationSeconds': num(seconds / 2), 'easeType': 'sinein', 'animateProperties': {'rotation': 0}}]}]
    return node


def hung_at(node, hang):
    node['overrides']['position'] = cutting.point(*hang)
    return node


def blossom_tree():
    children = []
    for tid, part in blossom.cut():
        node = cutting.image_ref(tid, blossom_template.OUTPUT, tid, part)
        if tid in blossom.CLUSTERS:
            node = swinging(hung_at(node, blossom.CLUSTERS[tid]['hang']), *CLUSTER_SWING[tid])
        children.append(node)
    return {'id': 'blossom tree', 'children': children}


def lantern_tree_node():
    children = []
    for tid, part in lantern_tree.cut():
        node = cutting.image_ref(tid, lantern_tree_template.OUTPUT, tid, part)
        if tid in HANGER_SWING:
            hang, _ = lantern_tree.HANGERS[tid.partition('lantern-tree-')[2]]
            node = swinging_from_rest(hung_at(node, hang), *HANGER_SWING[tid])
        children.append(node)
    return {'id': 'lantern tree', 'children': children}


def standing(node_id, tid, foot, scale):
    return {'id': node_id, 'ref': meadow_flowers_template.OUTPUT + '#' + tid, 'overrides': {
        'position': cutting.point(*foot), 'xScale': num(scale, 5), 'yScale': num(scale, 5)}}


def foreground():
    """The rocks, then the flowers back to front by their feet, each flower swaying."""
    rocks = [standing('rock %d' % k, tid, foot, width / meadow_flowers.template_args(tid)[1])
             for k, (tid, foot, width) in enumerate(meadow_flowers_reference.ROCKS)]
    stood = sorted((meadow_flowers.stand(tid, at, size) + (tid,) for tid, at, size in meadow_flowers_reference.FLOWERS),
                   key=lambda s: s[0][1])
    flowers = []
    for k, (foot, scale, tid) in enumerate(stood):
        node = standing('flower %d' % k, tid, foot, scale)
        node['overrides']['animationTracks'] = wind.sway(node, FLOWER_SWAY)
        flowers.append(node)
    return {'id': 'foreground', 'children': rocks + flowers}


def in_the_meadow(drawables):
    """The nodes with every id begun 'meadow ', as ids are unique across the files and other scenes place the same
    clouds."""
    for n in cutting.walk(drawables):
        n['id'] = 'meadow ' + n['id']
    return drawables


def build():
    return {'drawables': in_the_meadow([
        cutting.image_ref('sky', sky_template.OUTPUT, sky_template.TEMPLATE, sky.parts()[0]),
        drifting_clouds(),
        peaks(),
        *land(['hills far']),
        placed('gear mesa', mesa_template.OUTPUT, mesa_template.placements()),
        *land(['hills far left', 'hills far centre', 'hills far right', 'woods', 'hills middle', 'bushes far', 'track']),
        crossing_train(),
        *land(['bushes']),
        blossom_tree(),
        lantern_tree_node(),
        *land(['meadow']),
        foreground(),
    ])}


if __name__ == '__main__':
    layout.write(OUTPUT)

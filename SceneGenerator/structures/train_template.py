#   Writes JSON, run by `python3 -m scene_export layout`: structures/train.json in the game's scenes/, the train's
#   templates: an image template per part (the loco, each carriage, each wheel size, each gear size, the connecting
#   rod, a smoke puff, the train's shadow on the bed) and one `train` template that assembles them, so a scene places one ref and slides it in x.
#
#   python3 -m structures.train_template  ->  the game's scenes/structures/train.json
#
#   The train template's origin is TRAIN_ORIGIN: the rear of the last carriage, on the rail tops, so a scene standing
#   the train on a track places the ref at y = rail top / 2. Each wheel spins about its centre, its axle, one turn
#   per circumference rolled at TRAIN_SPEED, clockwise as the train runs to the right, each from its own starting
#   angle so the spokes don't all line up; the driving wheels one rod couples share one angle. The connecting rod
#   circles with the crank pins from that angle: its x and y tracks are the cosine and sine of the wheel's turn,
#   made of sine-eased quarter-turn steps. The gear emblems spin about their hubs over their bodies, decoratively
#   slower than the wheels, their teeth all running at GEAR_TOOTH_SPEED, the cab's one way and the carriages'
#   alternately.
#
#   The smoke is a steady stream of puffs rising from the funnel, each growing and fading at a constant rate over
#   one life, SMOKE_SECONDS. The engine repeats a step's delaySeconds on every loop, so staggering the puffs by a
#   delay would give each its own period and bunch them up; instead every puff has the same period and starts part
#   way along the rise, at its own phase: it finishes that life, snaps back to the funnel while it is invisible and
#   rises again to where it started, so the loop closes without a jump. The puffs differ in shape, size, drift and
#   turn so the stream doesn't repeat visibly. The pennant on the cab roof flutters about the pole.

import math

from scene_export import cutting, layout
from structures import train

OUTPUT = 'structures/train.json'

TRAIN_ORIGIN = (train.CARRIAGE_LEFTS[0] - 1, train.RAIL_Y)      # sheet px: the template's (0, 0)
SMOKE_RISE = (-24, -62)          # scene units a puff drifts back and rises over its life
SMOKE_SCALE = (0.55, 2.4)        # a puff's scale when it leaves the funnel and when it is gone
SMOKE_SECONDS = 3.2              # a puff's life
SMOKE_ALPHA = 0.9                # a fresh puff's opacity; it fades to nothing at the end of its life
SMOKE_FADE_IN = 0.25             # seconds a puff takes to appear at the funnel mouth
SMOKE_SNAP = 0.02                # seconds a spent, invisible puff takes to snap back to the funnel
SMOKE_PUFFS = [                  # (image, radians it is turned, extra drift (x, y) in scene units, size, mirrored)
    ('train-smoke-1', 0.0, (0, 0), 1.0, False),
    ('train-smoke-2', 0.7, (-5, 3), 0.88, True),
    ('train-smoke-3', -0.55, (4, -4), 1.1, False),
    ('train-smoke-4', 1.35, (-2, 2), 0.95, False),
    ('train-smoke-5', 0.25, (2, -2), 1.0, True),
    ('train-smoke-2', -1.1, (-4, 4), 0.9, False),
]
SMOKE_TURN = 0.35                # radians a puff turns over its life, alternately each way
WHEEL_STARTS = (0.0, 0.35, 0.8, 0.17, 0.62, 0.95, 0.5)   # radians each free wheel starts turned, in turn
DRIVE_START_QUARTERS = 1         # quarter turns the coupled driving wheels and their rod start turned
GEAR_STARTS = (0.0, 0.2, 0.39, 0.1)      # radians each gear starts turned, in turn
FLAG_FLUTTER = (0.06, 1.4, 0.05, 0.9)   # radians the pennant swings either way and seconds a swing; how much its
                                 # width ripples and seconds a ripple


def num(v, places=3):
    return cutting.num(v, places)


def turn_seconds(tid):
    """Seconds one turn of this wheel takes at TRAIN_SPEED."""
    return 2 * math.pi * train.WHEELS[tid] / train.TRAIN_SPEED


def spin_track(seconds, start, way=1):
    """One whole turn from start a loop, so the loop's snap back to start is invisible."""
    return {'repeat': 'loop', 'steps': [{'durationSeconds': num(seconds, 4), 'easeType': 'linear',
                                         'animateProperties': {'rotation': num(start + way * 2 * math.pi, 6)}}]}


def wheel_start(tid, k, x):
    """Radians the k-th wheel of this size, on the axle at sheet x, starts turned."""
    if tid == 'train-drive-wheel' and any(x in pair for pair in train.ROD_PAIRS):
        return DRIVE_START_QUARTERS * math.pi / 2
    return WHEEL_STARTS[k % len(WHEEL_STARTS)]


def wheel_refs(images):
    out = []
    for (gid, tid), (x, y) in zip(train.wheel_groups(), [a for tid in train.WHEELS for a in train.axles(tid)]):
        k = len(out)
        start = wheel_start(tid, k, x)
        out.append({'id': gid, 'ref': OUTPUT + '#' + tid,
                    'overrides': {'position': {'x': num(x / 2), 'y': num(y / 2)}, 'rotation': num(start, 6),
                                  'animationTracks': [spin_track(turn_seconds(tid), start)]}})
    return out


def gear_turn_seconds(tid):
    """Seconds one turn of this gear takes with its teeth running at GEAR_TOOTH_SPEED."""
    return 2 * math.pi * train.GEARS[tid] / train.GEAR_TOOTH_SPEED


def gear_refs(images):
    """One gear image of each size placed on every hub of that size, spinning: the cab's clockwise, the carriages'
    alternately."""
    out = []
    for (gid, tid), (x, y) in zip(train.gear_groups(), [h for tid in train.GEARS for h in train.gear_hubs(tid)]):
        k = len(out)
        way = -1 if k % 2 else 1
        start = GEAR_STARTS[k % len(GEAR_STARTS)]
        out.append({'id': gid, 'ref': OUTPUT + '#' + tid,
                    'overrides': {'position': {'x': num(x / 2), 'y': num(y / 2)}, 'rotation': num(start, 6),
                                  'animationTracks': [spin_track(gear_turn_seconds(tid), start, way)]}})
    return out


def crank_at(bx, by, angle):
    """Where the rod's image sits when the crank pins are turned angle radians from pointing ahead of the axles,
    where the image was drawn."""
    r = train.CRANK_R / 2
    return bx - r + r * math.cos(angle), by + r * math.sin(angle)


def crank_tracks(bx, by):
    """The rod's x and y over one turn of the driving wheels from their starting angle: x runs as the cosine, y as
    the sine, each a quarter turn a step, eased as that quarter of the wave is."""
    quarter = num(turn_seconds('train-drive-wheel') / 4, 4)
    xs, ys = [], []
    for k in range(1, 5):
        q = DRIVE_START_QUARTERS + k - 1
        x, y = crank_at(bx, by, (q + 1) * math.pi / 2)
        xs.append({'durationSeconds': quarter, 'easeType': 'sinein' if q % 2 == 0 else 'sineout',
                   'animateProperties': {'x': num(x)}})
        ys.append({'durationSeconds': quarter, 'easeType': 'sineout' if q % 2 == 0 else 'sinein',
                   'animateProperties': {'y': num(y)}})
    return [{'repeat': 'loop', 'steps': xs}, {'repeat': 'loop', 'steps': ys}]


def rod_base(rod_id):
    """Template units: where the rod image of this rod sits with the pins pointing ahead, as it was drawn."""
    k = int(rod_id.split()[-1]) - 1
    x, y, _, _ = dict(train.cut())['train-rod'].box
    pair = train.ROD_PAIRS[k]
    return (num(x / 2 + (pair[0] - train.ROD_PAIRS[0][0]) / 2 - TRAIN_ORIGIN[0] / 2),
            num(y / 2 - TRAIN_ORIGIN[1] / 2))


def rod_refs(images):
    """The one rod image placed once per coupled pair, each circling with its pair's cranks."""
    part = images['train-rod']
    out = []
    for k, pair in enumerate(train.ROD_PAIRS):
        node = cutting.image_ref('train rod %d' % (k + 1), OUTPUT, 'train-rod', part)
        at = node['overrides']['position']
        bx, by = at['x'] + (pair[0] - train.ROD_PAIRS[0][0]) / 2, at['y']
        x, y = crank_at(bx, by, DRIVE_START_QUARTERS * math.pi / 2)
        node['overrides']['position'] = {'x': num(x), 'y': num(y)}
        node['overrides']['animationTracks'] = crank_tracks(bx, by)
        out.append(node)
    return out


def smoke_phase(k):
    """How far along its life the k-th puff starts: the puffs are spread evenly along the rise, none at the mouth."""
    return (k + 0.5) / len(SMOKE_PUFFS)


def smoke_state(k, t):
    """A puff's x, y, scales and rotation t of the way through its life."""
    image, turned, (ex, ey), size, mirrored = SMOKE_PUFFS[k]
    cx, cy = (v / 2 for v in train.SMOKE_AT)
    dx, dy = SMOKE_RISE[0] + ex, SMOKE_RISE[1] + ey
    scale = (SMOKE_SCALE[0] + (SMOKE_SCALE[1] - SMOKE_SCALE[0]) * t) * size
    turn = turned + SMOKE_TURN * t * (-1 if k % 2 else 1)
    return {'x': num(cx + dx * t), 'y': num(cy + dy * t), 'xScale': num(-scale if mirrored else scale),
            'yScale': num(scale), 'rotation': num(turn, 4)}


def smoke_alpha(t):
    """A puff's opacity t of the way through its life: it appears over SMOKE_FADE_IN, then thins to nothing."""
    life = SMOKE_SECONDS
    if t * life < SMOKE_FADE_IN:
        return SMOKE_ALPHA * t * life / SMOKE_FADE_IN
    return SMOKE_ALPHA * (1 - (t * life - SMOKE_FADE_IN) / (life - SMOKE_FADE_IN))


def smoke_refs(images):
    out = []
    for k, (image, _, _, _, _) in enumerate(SMOKE_PUFFS):
        p = smoke_phase(k)
        start, end, mouth = smoke_state(k, p), smoke_state(k, 1), smoke_state(k, 0)
        rest, back = num(SMOKE_SECONDS * (1 - p), 4), num(SMOKE_SECONDS * p, 4)
        motion = [{'durationSeconds': rest, 'easeType': 'linear', 'animateProperties': end},
                  {'durationSeconds': SMOKE_SNAP, 'easeType': 'linear', 'animateProperties': mouth},
                  {'durationSeconds': back, 'easeType': 'linear', 'animateProperties': start}]
        alpha = [{'durationSeconds': rest, 'easeType': 'linear', 'animateProperties': {'alpha': 0}},
                 {'durationSeconds': SMOKE_SNAP, 'easeType': 'linear', 'animateProperties': {'alpha': 0}},
                 {'durationSeconds': SMOKE_FADE_IN, 'easeType': 'linear', 'animateProperties': {'alpha': SMOKE_ALPHA}},
                 {'durationSeconds': num(SMOKE_SECONDS * p - SMOKE_FADE_IN, 4), 'easeType': 'linear',
                  'animateProperties': {'alpha': num(smoke_alpha(p))}}]
        overrides = {'position': {'x': start['x'], 'y': start['y']}, 'xScale': start['xScale'], 'yScale': start['yScale'],
                     'rotation': start['rotation'], 'alpha': num(smoke_alpha(p)),
                     'animationTracks': [{'repeat': 'loop', 'steps': motion}, {'repeat': 'loop', 'steps': alpha}]}
        out.append({'id': 'train smoke %d' % (k + 1), 'ref': OUTPUT + '#' + image, 'overrides': overrides})
    return out


def flag_refs(images):
    """The pennant hung at the pole, swinging a little either way and rippling in width as the train runs."""
    swing, swing_seconds, ripple, ripple_seconds = FLAG_FLUTTER
    x, y = train.FLAG_HANG
    return [{'id': 'train flag', 'ref': OUTPUT + '#train-flag', 'overrides': {
        'position': {'x': num(x / 2), 'y': num(y / 2)}, 'rotation': num(-swing, 4), 'xScale': 1,
        'animationTracks': [
            {'repeat': 'yoyo', 'steps': [{'durationSeconds': swing_seconds, 'easeType': 'sineinout',
                                          'animateProperties': {'rotation': num(swing, 4)}}]},
            {'repeat': 'yoyo', 'steps': [{'durationSeconds': ripple_seconds, 'easeType': 'sineinout',
                                          'animateProperties': {'xScale': num(1 - ripple)}}]}]}}]


def body_refs(images):
    out = []
    for tid in ('train-carriage-3', 'train-carriage-2', 'train-carriage-1', 'train-loco'):
        out.append(cutting.image_ref(tid.replace('-', ' '), OUTPUT, tid, images[tid]))
    return out


def shadow_refs(images):
    return [cutting.image_ref('train shadow', OUTPUT, 'train-shadow', images['train-shadow'])]


def train_template():
    images = dict(train.cut())
    children = (shadow_refs(images) + wheel_refs(images) + body_refs(images) + gear_refs(images) + rod_refs(images)
                + flag_refs(images) + smoke_refs(images))
    origin = (TRAIN_ORIGIN[0] / 2, TRAIN_ORIGIN[1] / 2)
    return {'id': 'train', 'templateOnly': True, 'children': cutting.shifted(children, origin)}


def build():
    out = []
    for tid, part in train.cut():
        node = cutting.image_template(tid, part)
        if tid in train.WHEELS or tid in train.GEARS or tid.startswith('train-smoke'):
            node.update(anchor='center', pivot='center')
        elif tid == 'train-flag':
            node.update(anchor='centerRight', pivot='centerRight')
        out.append(node)
    out.append(train_template())
    return {'drawables': out}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

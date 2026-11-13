"""Library, writes nothing: the wind written into the scene: each cloud drifts across to the right and wraps round out of sight, the high
ones in front faster than the low ones by the horizon. Every plant piece and flower placed in the scene follows one
shared wind about its own rotation: calm, then gusts that build, bend everything downwind and die away, reaching the
plants on the left a moment before the ones on the right. Flowers move most and rosettes least. The breeze ruffles
the lake too: its two sets of glints fade in turn and ripple a little sideways.

The tracks are absolute values worked out from where each node is placed; the scene editor moves a node's keyframes
with it when it is moved, rotated or scaled, so they keep animating from the edited place."""

import copy
import math
import random

from .cutting import GAME_CANVAS

SCENE_SIZE = GAME_CANVAS

FRONT_CLOUD = (-100 / 3, 35 / 3)    # (y, canvas units a second) of a high cloud in front, its top above the canvas
HORIZON_CLOUD = (425 / 3, 1.0)      # and of one low down near the horizon, drifting slowest
OUT_OF_SIGHT = 20 / 3               # canvas units past the canvas edge a cloud wraps at
CLOUD_LAP = 2 * SCENE_SIZE[0]       # canvas units a cloud drifts before it comes round again, so half the clouds
                                    # wait off the left edge as a second set while the rest are in view
JUMP_SECONDS = 0.001                # flux never finishes a tween of no time

WIND_SECONDS = 48.0                 # one pass through the gusts, then it repeats
GUST_EVERY = 3.0                    # seconds between the wind's strength changing course
CALM = (0.15, 0.3)                  # the wind's strength between gusts, 1 the strongest gust
GUSTS = ((0.95, 1.0), (0.65, 0.85), (0.75, 0.9))
DOWNWIND = 0.65                     # a swing back in a gust still leans 2 * DOWNWIND - 1 of the way downwind
SWING_SECONDS = (1.2, 0.55)         # one swing in a calm and in the strongest gust
SETTLE_SECONDS = 3.0                # the last swing back upright, longer than any plant waits for the wind
WAVE_SECONDS = 1.2                  # for the wind to cross the terrace from left to right
WAVE_JITTER = 0.25
SWAY = {'flower': 0.07, 'daisy': 0.07, 'bud': 0.07, 'tulip': 0.07, 'rose': 0.06, 'leaf': 0.055, 'grass': 0.05,
        'branch': 0.045, 'rosette': 0.025}           # radians a plant leans in the strongest gust, by its template's kind
TWINKLE_SECONDS = 1.6              # for a set of glints to fade from bright to dim
TWINKLE_DIM = 0.15                 # a set of glints' alpha at its dimmest
RIPPLE = (2.5, 2.3)                # (canvas units, seconds) a set of glints slides sideways and back
PLANT_REFS = ('branches.json#', 'leaves.json#', 'flowers.json#', 'roses.json#', 'stems.json#')


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get('children', []))


def cloud_speed(y):
    t = min(1.0, max(0.0, (y - FRONT_CLOUD[0]) / (HORIZON_CLOUD[0] - FRONT_CLOUD[0])))
    return FRONT_CLOUD[1] + (HORIZON_CLOUD[1] - FRONT_CLOUD[1]) * t


def drift(placed, width, speed=None):
    """Off the right edge, back a lap to the left out of sight, and on to its own place, at a steady speed, by default
    the one for its height. placed holds the cloud's position, width is its image's in canvas units."""
    x, speed = placed['position']['x'], speed or cloud_speed(placed['position']['y'])
    off_right = SCENE_SIZE[0] + OUT_OF_SIGHT
    in_left = off_right - CLOUD_LAP

    def step(to, seconds):
        return {'durationSeconds': seconds, 'easeType': 'linear', 'animateProperties': {'x': to}}
    return [{'loopTrack': True, 'steps': [step(off_right, (off_right - x) / speed), step(in_left, JUMP_SECONDS),
                                          step(x, (x - in_left) / speed)]}]


def twinkle(placed, bright):
    """The overrides that fade a set of glints from bright to dim and back, or from dim when bright is False so it
    twinkles in turn with the other set, while it slides sideways and back, the other set the other way."""
    dim, x = TWINKLE_DIM, placed['position']['x']
    start, turn = (1, dim) if bright else (dim, 1)
    amount, seconds = RIPPLE

    def step(props, seconds):
        return {'durationSeconds': seconds, 'easeType': 'sineinout', 'animateProperties': props}
    tracks = [{'loopTrack': True, 'steps': [step({'alpha': turn}, TWINKLE_SECONDS),
                                            step({'alpha': start}, TWINKLE_SECONDS)]},
              {'loopTrack': True, 'steps': [step({'x': x + (amount if bright else -amount)}, seconds),
                                            step({'x': x}, seconds)]}]
    return dict({} if bright else {'alpha': dim}, animationTracks=tracks)


def gust_strength():
    """The wind's strength through one pass, as a function of seconds: calm, with gusts building and dying away."""
    rng = random.Random('gusts')
    keys = [rng.uniform(*CALM) for _ in range(int((WIND_SECONDS - SETTLE_SECONDS) / GUST_EVERY) + 1)]
    for i, peak in zip((3, 7, 11), GUSTS):
        keys[i] = rng.uniform(*peak)
        keys[i - 1] = keys[i + 1] = (keys[i] + CALM[1]) / 2
    keys[0] = keys[-1] = CALM[0]

    def strength(t):
        i = min(int(t / GUST_EVERY), len(keys) - 2)
        u = (1 - math.cos(math.pi * min(1.0, t / GUST_EVERY - i))) / 2
        return keys[i] + (keys[i + 1] - keys[i]) * u
    return strength


def wind():
    """[(seconds, lean)] for every swing of one pass, the lean a share of a plant's sway, ending upright."""
    strength, rng = gust_strength(), random.Random('swings')
    swings, t, downwind = [], 0.0, True
    while t < WIND_SECONDS - SETTLE_SECONDS - SWING_SECONDS[0] * 1.1:
        s = strength(t)
        seconds = (SWING_SECONDS[0] + (SWING_SECONDS[1] - SWING_SECONDS[0]) * s) * rng.uniform(0.9, 1.1)
        swings.append((seconds, s if downwind else s * (2 * DOWNWIND - 1)))
        t, downwind = t + seconds, not downwind
    swings.append((WIND_SECONDS - t, 0.0))
    return swings


WIND = wind()


def sway_of(node):
    return SWAY[node['ref'].partition('#')[2].split('-')[0]]


def sway(node, share=1.0, delay=None):
    """The plant following the wind about its own rotation, as late as the wind takes to reach it from the left or
    after delay seconds, leaning share of its kind's sway."""
    overrides = node['overrides']
    base, amount = overrides.get('rotation', 0), share * sway_of(node)
    lag = delay if delay is not None else (overrides.get('position', {}).get('x', 0) / SCENE_SIZE[0] * WAVE_SECONDS
                                           + random.Random(node['id']).uniform(0, WAVE_JITTER))
    steps = [{'durationSeconds': seconds, 'easeType': 'sineinout', 'animateProperties': {'rotation': base + lean * amount}}
             for seconds, lean in WIND]
    steps[0]['delaySeconds'] = lag
    steps[-1]['durationSeconds'] -= lag
    steps[-1]['animateProperties']['rotation'] = base
    return [{'loopTrack': True, 'steps': steps}]


def swayed(nodes):
    """Copies of the nodes, placed in canvas units, with a track on every plant among them."""
    nodes = copy.deepcopy(nodes)
    for n in walk(nodes):
        if any(r in n.get('ref', '') for r in PLANT_REFS):
            n['overrides']['animationTracks'] = sway(n)
    return nodes

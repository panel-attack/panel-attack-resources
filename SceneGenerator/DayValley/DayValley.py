#   Writes JSON, run by `python3 -m scene_export layout`: DayValley/DayValley.json in the game's scenes/, the sunny
#   meadow valley the main menu shows, lit by a sun high above the frame's top right, out of sight: the trees and the
#   windmill are drawn lit from there, and the flowers and firs, drawn lit from the upper left, are all mirrored. It draws, back
#   to front: the sky, the clouds drifting in the wind, Magellan's airship crossing high up, the purple ranges and the snowy peak, then each rolling hill with the
#   trees standing on it, the windmill turning on its knoll, the near hill and the open meadow the menu stands over.
#   Everything is a ref to a template, placed where its generator drew it or stood on a hill.
#
#   python3 -m DayValley.DayValley  ->  the game's scenes/DayValley/DayValley.json

import dataclasses
import math
import random

from scene_export import cutting, layout, wind
from scenery import alps, alps_template, clouds, clouds_template, sky, sky_template
from scenery import valley, valley_template
from scenery.valley_reference import HILLS, MEADOW
from structures import airship_template, windmill, windmill_template
from plants import broadleaf, broadleaf_template, pines, pines_template, wildflowers, wildflowers_template

OUTPUT = 'DayValley/DayValley.json'

# The clouds back to front: (cloud id, the top left of its image in sheet px, or None where clouds.py drew it). Big
# flat-bottomed banks fill the top corners, cut by the frame; two small puffs float over the middle, high above the
# ranges; thin wisps streak across the top, and the peak's ridges stay clear.
SKY_CLOUDS = [
    ('cloud wisp left', None),
    ('cloud wisp right', None),
    ('cloud wisp low', None),
    ('cloud r4-09', (540, 124)),
    ('cloud r4-23', (832, 102)),
    ('cloud r4-27', (1290, 46)),
    ('cloud r4-33', (-12, 56)),
]
SAIL_TURN = 18.0                    # seconds for one turn of the sails, anticlockwise as on a Dutch mill
AIRSHIP_PATH = ((780, -72), 82)     # (x from, x to) and y in scene units: it crosses right to left high in the sky
AIRSHIP_CROSSING = (70, 45)         # seconds to cross, seconds out of sight before the next crossing
AIRSHIP_BOB = (78.4, 4.0)           # (y, seconds) it bobs up to and back
AIRSHIP_SCALE = (0.216, 0.252)      # it grows slightly as it crosses, coming nearer
AIRSHIP_ROCK = (0.03, 3.5)          # (radians, seconds) it rocks to and back

# The trees and bushes, each standing on the frontmost hill whose top runs above its foot: (template, foot in sheet
# px, height px).
TREES = [
    ('oak-broad-near', (120, 424), 150),
    ('oak-round-mid', (246, 432), 92),
    ('oak-round-far', (546, 430), 42),
    ('oak-broad-mid', (632, 445), 60),
    ('oak-broad-far', (803, 485), 36),
    ('oak-round-far', (846, 487), 40),
    ('oak-round-far', (887, 380), 24),
    ('oak-broad-far', (915, 381), 22),
    ('oak-round-mid', (1455, 406), 76),
    ('bush-wide', (55, 432), 36),
    ('bush-round', (170, 432), 26),
    ('bush-wide', (315, 446), 30),
    ('bush-round', (1335, 466), 40),
    ('bush-wide', (1512, 502), 22),
]

# The small trees dotted along the far and middle hills, behind the windmill's sails: (template, hill, x, px below
# the hill's top, height px). Each stands just under its hill's top edge, so the hills in front hide none of it.
BACK_TREES = [
    ('oak-round-far', 'hills far left', 96, 8, 16),
    ('oak-broad-far', 'hills far left', 205, 10, 15),
    ('oak-round-far', 'hills far left', 330, 9, 17),
    ('oak-broad-far', 'hills far centre', 515, 8, 16),
    ('pine-tall-far', 'hills far centre', 590, 7, 22),
    ('oak-round-far', 'hills far right', 965, 7, 16),
    ('pine-slim-far', 'hills far right', 1015, 8, 20),
    ('pine-tall-far', 'hills far right', 1235, 8, 22),
    ('oak-round-far', 'hills far right', 1300, 7, 16),
    ('oak-broad-far', 'hills far right', 1425, 7, 15),
    ('oak-round-far', 'hills far hump', 950, 8, 19),
    ('oak-tall-mid', 'hills middle left', 335, 10, 26),
    ('oak-round-mid', 'hills middle left', 420, 12, 24),
    ('oak-broad-far', 'hills middle left', 455, 10, 22),
    ('oak-round-mid', 'hills middle hump', 1000, 9, 26),
    ('oak-broad-far', 'hills middle hump', 1065, 10, 22),
    ('oak-tall-mid', 'hills middle right', 1190, 10, 30),
    ('oak-broad-mid', 'hills middle right', 1270, 9, 28),
    ('oak-round-far', 'hills middle right', 1370, 9, 26),
    ('pine-slim-far', 'hills far left', 140, 9, 18),
    ('pine-full-far', 'hills far left', 270, 10, 20),
    ('oak-broad-far', 'hills far right', 1120, 8, 14),
    ('oak-round-far', 'hills far right', 1365, 7, 15),
    ('pine-full-far', 'hills far right', 1500, 8, 21),
    ('oak-broad-far', 'hills middle left', 30, 10, 20),
    ('oak-round-far', 'hills middle right', 1520, 9, 24),
]

# Copses: small woods of trees standing close together along a hill, where the back hills were bare: (hill, middle
# x, trees, px they spread across, height px). Each tree stands a little lower or higher down its hill's face and a
# little larger or smaller, but never so far down that the hill in front hides its foot.
COPSES = [
    ('hills far', 40, 5, 90, 11),
    ('hills far', 190, 6, 130, 12),
    ('hills far', 360, 5, 110, 11),
    ('hills far', 540, 6, 130, 12),
    ('hills far', 720, 5, 110, 11),
    ('hills far', 890, 6, 130, 12),
    ('hills far', 1060, 5, 100, 11),
    ('hills far', 1250, 5, 110, 11),
    ('hills far', 1410, 6, 130, 12),
    ('hills far', 1520, 3, 50, 11),
    ('hills far left', 40, 5, 90, 18),
    ('hills far centre', 760, 6, 110, 19),
    ('hills far right', 1100, 5, 90, 19),
    ('hills far right', 1380, 6, 120, 19),
    ('hills middle left', 190, 6, 130, 32),
    ('hills middle', 700, 6, 120, 34),
    ('hills middle hump', 880, 5, 100, 32),
    ('hills middle right', 1470, 6, 110, 40),
    ('hills middle near', 990, 4, 100, 42),
    ('hills near middle', 450, 4, 90, 52),
]
COPSE_DROP = (5, 16)                 # px below the hill's top a copse tree's foot stands, at the least and most
COPSE_SIZES = (0.8, 1.15)            # a copse tree's height, as a share of its copse's
# Firs grow among the oaks on the far hills, so the distance isn't one kind of tree: each copse there is mostly oak,
# mixed, or a fir wood, by the share of firs it draws from these. Nearer hills keep to oaks but for a few mixed woods.
FAR_FIRS, NEAR_FIRS = (0.15, 0.5, 0.85), (0.0, 0.0, 0.0, 0.3)
FAR_DEPTH = 0.25                     # hills this far back or farther are the far hills
FIR_TALL = 1.3                       # a fir stands this much taller than an oak of its copse, slim as it is

# The flowers and grass tufts over the near hills and the meadow, grown the way a meadow grows them: in loose drifts
# where one kind has seeded itself, thinning out at their edges into open grass, never in tight bunches. Two smooth
# noise fields, measured in DRIFT_SIZE and bent by a third so no two drifts share a size or shape, say how thick the
# flowers grow at a spot and which kind grows there; where two kinds meet they mix. A plant stands FLOWER_SPACING of
# its own height from the next, but some seed a companion or two as near as FLOWER_CLOSEST, so they stand unevenly as
# wild flowers do, and a few strays grow out alone in the open grass. They grow from FLOWER_HEIGHT[0] px at
# FLOWER_SPAN[0] down to FLOWER_HEIGHT[1] px at the bottom, nearer, each FLOWER_JITTER larger or smaller.
FLOWER_SPAN = (440, 985)             # sheet y the flowers start at, and where they stop
FLOWER_HEIGHT = (8, 66)              # px tall at FLOWER_SPAN's top .. bottom
FLOWER_JITTER = 0.25
FLOWER_SPACING = 1.9                 # heights apart, at the least, but for companions
FLOWER_CLOSEST = 0.8                 # heights apart a companion may stand, at the least
COMPANIONS = (0, 1, 1, 2, 2, 3)      # how many companions a flower in a drift seeds, one of these at random
FLOWER_TRIES = 60000
DRIFT_SIZE = (260, 90)               # px a drift spans across and down the sheet, at the meadow's middle
DRIFT_THICK = 0.54                   # density noise above this grows flowers, thickest at 1
DRIFT_BEND = 0.9                     # how far the bending noise moves a drift, in drifts
OPEN_STRAYS = 0.15                   # the chance a lone stray grows where the drifts leave open grass
STRAY_CLEAR = 0.05                   # how far below DRIFT_THICK the open grass a stray grows in lies, clear of drifts
STRAY_SPACING = 3.0                  # heights a lone stray stands from any other flower, at the least
KIND_MIX = 0.35                      # how far into the next kind a flower may reach where two drifts meet, in kinds
FLOWER_CLEAR = 10                    # px kept clear round the windmill's tower
SMALL_FLOWER = 22                    # px: below this only the small flowers and tufts stand
NEAR_FLOWERS = ['flower-blue', 'flower-lilac', 'flower-yellow', 'flower-blue-light', 'tulip-red', 'tulip-yellow']
FAR_FLOWERS = ['flower-blue-light', 'flower-lilac', 'flower-yellow', 'flower-lilac']
KIND_SIZE = 1.6                      # one kind's patch spans this many drifts
STRAY_SHARE = 0.12                   # of the flowers in a drift, a kind seeded from elsewhere
TUFTS = ['grass-tuft', 'grass-tuft-tall', 'grass-tuft-small']
TUFT_SPACING = 3.0                   # tufts grow everywhere, this many of their heights apart
STEMS = ['', '-short', '-tall']      # a flower grows on its kind's own stem, a short one or a tall one, equally often;
                                     # its head is the same size whichever, so a tall stem stands it taller
MEADOW_SWAY = 0.4                    # of the terrace plants' sway in the wind, a gentle breeze over the meadow
FLOWER_LEAN = 0.3                    # radians a flower leans at the most, either way, most of them less


def num(v, places=3):
    return cutting.num(v, places)


def edge_y(points, x):
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[0][1] if x < points[0][0] else points[-1][1]


def standing(node_id, file, tid, foot, scale, mirror=False, lean=0.0):
    """Draws a template anchored at its foot standing on foot, a sheet px point, leaning lean radians about it."""
    overrides = {'position': {'x': num(foot[0] / 2), 'y': num(foot[1] / 2)},
                 'xScale': num(-scale if mirror else scale, 5), 'yScale': num(scale, 5)}
    if lean:
        overrides['rotation'] = num(lean, 4)
    return {'id': node_id, 'ref': file + '#' + tid, 'overrides': overrides}


def tree_sizes():
    return {p.path.rpartition('/')[2]: p.box[3] - 2 * cutting.PAD for p in broadleaf.parts() + pines.parts()}


def hill_under(foot):
    """The frontmost hill whose top edge runs above foot, so the hills in front of it hide nothing it stands on."""
    return [name for name, _, points in HILLS if edge_y(points, foot[0]) <= foot[1]][-1]


def trees_on(hill, sizes):
    out = []
    for i, (tid, foot, height) in enumerate(TREES):
        if hill_under(foot) == hill:
            out.append(standing('%s tree %d' % (hill, i + 1), broadleaf_template.OUTPUT, tid, foot,
                                height / sizes[tid]))
    out.sort(key=lambda n: n['overrides']['position']['y'])
    return out


def copse_trees():
    """[(template, hill, x, px below the hill's top, height)]: every copse's trees, spaced across it with a little
    jitter."""
    points, depths, out = dict((n, pts) for n, _, pts in HILLS), dict((n, d) for n, d, _ in HILLS), []
    for hill, middle, count, spread, height in COPSES:
        rng = random.Random('%s copse %d' % (hill, middle))
        firs = rng.choice(FAR_FIRS if depths[hill] <= FAR_DEPTH else NEAR_FIRS)
        for k in range(count):
            x = round(middle + spread * ((k + 0.5) / count - 0.5 + rng.uniform(-0.3, 0.3) / count))
            drop = rng.randint(*COPSE_DROP)
            while drop > COPSE_DROP[0] and hill_under((x, edge_y(points[hill], x) + drop)) != hill:
                drop -= 1
            size = height * rng.uniform(*COPSE_SIZES)
            if rng.random() < firs:
                size = round(size * FIR_TALL)
                tid = 'pine-%s-%s' % (rng.choice(['slim', 'full', 'tall']), 'far' if size < 28 else 'mid')
            else:
                size = round(size)
                tid = 'oak-%s-%s' % (rng.choice(['broad', 'round', 'tall']), 'far' if size < 22 else 'mid')
            out.append((tid, hill, x, drop, size))
    return out


def back_trees_on(hill, sizes):
    points, out = dict((n, pts) for n, _, pts in HILLS), []
    for i, (tid, on, x, drop, height) in enumerate(BACK_TREES + copse_trees()):
        if on == hill:
            foot = (x, round(edge_y(points[on], x) + drop))
            fir = tid.startswith('pine-')
            out.append(standing('%s back tree %d' % (hill, i + 1),
                                pines_template.OUTPUT if fir else broadleaf_template.OUTPUT, tid, foot,
                                height / sizes[tid], mirror=fir))
    return out


def flower_height(y):
    u = max(0.0, (y - FLOWER_SPAN[0]) / (FLOWER_SPAN[1] - FLOWER_SPAN[0]))
    return FLOWER_HEIGHT[0] + (FLOWER_HEIGHT[1] - FLOWER_HEIGHT[0]) * u ** 1.3


def off_tower(x, y, tower):
    tx, ty, tw, th = tower
    return not (tx - FLOWER_CLEAR <= x <= tx + tw + FLOWER_CLEAR and ty <= y <= ty + th + FLOWER_CLEAR)


class Noise:
    """Smooth value noise on the sheet: a lattice of random values eased between, two octaves, 0 .. 1."""

    def __init__(self, seed):
        rng = random.Random(seed)
        self.values = [[rng.random() for _ in range(64)] for _ in range(64)]

    def lattice(self, u, v):
        i, j = math.floor(u), math.floor(v)
        fu, fv = u - i, v - j
        fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
        at = lambda a, b: self.values[(j + b) % 64][(i + a) % 64]
        top = at(0, 0) + (at(1, 0) - at(0, 0)) * fu
        bottom = at(0, 1) + (at(1, 1) - at(0, 1)) * fu
        return top + (bottom - top) * fv

    def __call__(self, x, y, size=1.0):
        """The noise at sheet (x, y), its drifts size times DRIFT_SIZE and shrinking with distance as the flowers do."""
        shrink = size * flower_height(y) / flower_height(sum(FLOWER_SPAN) / 2)
        u, v = x / (DRIFT_SIZE[0] * shrink), y / (DRIFT_SIZE[1] * shrink)
        return (2 * self.lattice(u, v) + self.lattice(2.3 * u + 17, 2.3 * v + 5)) / 3


BEND = Noise('meadow drift bends')
THICK = Noise('meadow flower drifts')


def bent(x, y):
    """(x, y) moved by the bending noise, so drifts measured from it take every size and shape."""
    u = BEND(x, y, 1.3) - 0.5
    v = BEND(x + 911, y + 377, 1.3) - 0.5
    return x + 2 * u * DRIFT_BEND * DRIFT_SIZE[0], y + 2 * v * DRIFT_BEND * DRIFT_SIZE[1]


def drift_thickness(x, y):
    """0 .. 1: how thick the flowers grow at sheet (x, y); above DRIFT_THICK they grow in a drift."""
    return THICK(*bent(x, y))


def on_ground(x, y, tower):
    surface = ('hills near middle', 'windmill knoll', 'hills near')
    if y < edge_y(MEADOW[0][0], x) and hill_under((x, y)) not in surface:
        return False
    return off_tower(x, y, tower)


def spread(rng, keep, spacing, tower, companions=lambda x, y: 0, among=()):
    """Feet (x, y, height) on the ground, dart thrown: one is kept when keep(x, y) says so and it stands spacing of
    its height from every one kept before it. Each kept one seeds companions(x, y) more round it, as near as
    FLOWER_CLOSEST. Feet already among them are kept clear of but not returned."""
    feet = list(among)

    def room(x, y, h, apart):
        return on_ground(x, y, tower) and all(math.hypot(x - fx, y - fy) >= apart * max(h, fh) for fx, fy, fh in feet)

    for _ in range(FLOWER_TRIES):
        x, y = rng.uniform(-10, 1546), rng.uniform(*FLOWER_SPAN)
        if not keep(x, y):
            continue
        h = flower_height(y) * rng.uniform(1 - FLOWER_JITTER, 1 + FLOWER_JITTER)
        if not room(x, y, h, spacing):
            continue
        feet.append((x, y, h))
        for _ in range(companions(x, y)):
            a, d = rng.uniform(0, 2 * math.pi), h * rng.uniform(FLOWER_CLOSEST, 1.5 * FLOWER_CLOSEST)
            cx, cy = x + d * math.cos(a), y + d * math.sin(a)
            ch = flower_height(cy) * rng.uniform(1 - FLOWER_JITTER, 1 + FLOWER_JITTER) if FLOWER_SPAN[0] <= cy <= FLOWER_SPAN[1] else 0
            if ch and room(cx, cy, ch, FLOWER_CLOSEST):
                feet.append((cx, cy, ch))
    return feet[len(among):]


def grows(rng, x, y):
    """Whether a flower takes root in a drift at sheet (x, y), the more likely the thicker the drift."""
    return rng.random() < (drift_thickness(x, y) - DRIFT_THICK) / (1 - DRIFT_THICK)


def strays_at(rng, x, y):
    """Whether a lone stray takes root at sheet (x, y), out in the open grass well clear of the drifts."""
    return drift_thickness(x, y) < DRIFT_THICK - STRAY_CLEAR and rng.random() < OPEN_STRAYS


def flower_kind(rng, kinds, kind, x, y):
    """Which of kinds grows at sheet (x, y): its drift's kind, mixing into the next where two drifts meet, or now and
    then a stray of any kind."""
    if rng.random() < STRAY_SHARE:
        return kinds[rng.randrange(len(kinds))]
    at = (kind(*bent(x, y), KIND_SIZE) - 0.25) / 0.5 * len(kinds) + rng.uniform(-KIND_MIX, KIND_MIX)
    return kinds[int(min(len(kinds) - 1, max(0, at)))]


def flower_plants():
    """[(template, x, y, height)]: the flowers in their drifts and out as strays, and the tufts all over."""
    rng, tower = random.Random('meadow flowers'), dict(windmill.cut())['windmill-tower'].box
    kind = Noise('meadow flower kinds')
    seeds = lambda x, y: rng.choice(COMPANIONS) if drift_thickness(x, y) >= DRIFT_THICK else 0
    blooms = spread(rng, lambda x, y: grows(rng, x, y), FLOWER_SPACING, tower, seeds)
    blooms += spread(rng, lambda x, y: strays_at(rng, x, y), STRAY_SPACING, tower, among=blooms)
    plants = [(flower_kind(rng, NEAR_FLOWERS if h >= SMALL_FLOWER else FAR_FLOWERS, kind, x, y), x, y, h)
              for x, y, h in blooms]
    tufts = spread(rng, lambda x, y: True, TUFT_SPACING, tower)
    plants += [(rng.choice(TUFTS), x, y, h * 0.45) for x, y, h in tufts]
    return sorted(plants, key=lambda p: p[2])


def flowers_by_ground():
    """{hill name or 'meadow': [flower nodes]}, each flower standing on the ground under its foot."""
    rng, sizes, out = random.Random('meadow flower turns'), flower_sizes(), {}
    for i, (tid, x, y, h) in enumerate(flower_plants()):
        ground = 'meadow' if y >= edge_y(MEADOW[0][0], x) else hill_under((x, y))
        scale, mirror, stem, lean = h / sizes[tid], rng.random() < 0.5, '', 0.0
        if not tid.startswith('grass-'):
            mirror, stem, lean = True, rng.choice(STEMS), rng.triangular(-FLOWER_LEAN, FLOWER_LEAN, 0.0)
        node = standing('%s flower %d' % (ground, i + 1), wildflowers_template.OUTPUT, tid + stem, (round(x), round(y)),
                        scale, mirror, lean)
        node['overrides']['animationTracks'] = wind.sway(node, MEADOW_SWAY)
        out.setdefault(ground, []).append(node)
    return out


def flower_sizes():
    return {p.path.rpartition('/')[2]: p.box[3] - 2 * cutting.PAD for p in wildflowers.parts()}


def hill_node(name, images, sizes, flowers):
    hill = cutting.image_ref(name, valley_template.OUTPUT, cutting.slug(name), images[name])
    standing_trees = back_trees_on(name, sizes) + trees_on(name, sizes)
    standing_trees.sort(key=lambda n: n['overrides']['position']['y'])
    growing = flowers.get(name, [])
    return {'id': name + ' and its trees', 'children': [hill]
            + ([{'id': name + ' flowers', 'children': growing}] if growing else [])
            + ([{'id': name + ' trees', 'children': standing_trees}] if standing_trees else [])}


def drifting_clouds():
    images, children = dict(clouds.cut_all()), []
    for cid, at in SKY_CLOUDS:
        part = images[cid]
        if at is not None:
            part = dataclasses.replace(part, box=at + part.box[2:])
        node = cutting.image_ref(cid, clouds_template.OUTPUT, clouds_template.template_id(cid), part)
        node['overrides']['animationTracks'] = wind.drift(node['overrides'], part.box[2] / 2, clouds.speed(cid))
        children.append(node)
    return {'id': 'clouds', 'children': children}



def airship():
    (x_from, x_to), y = AIRSHIP_PATH
    crossing, wait = AIRSHIP_CROSSING
    bob_y, bob_seconds = AIRSHIP_BOB
    small, large = AIRSHIP_SCALE
    rock, rock_seconds = AIRSHIP_ROCK
    return {'id': 'airship', 'position': {'x': x_from, 'y': y}, 'animationTracks': [
        {'repeat': 'loop', 'steps': [{'delaySeconds': wait, 'durationSeconds': crossing, 'easeType': 'linear',
                                      'animateProperties': {'x': x_to}}]},
        {'repeat': 'yoyo', 'steps': [{'durationSeconds': bob_seconds, 'easeType': 'sineinout',
                                      'animateProperties': {'y': bob_y}}]}],
        'children': [{'id': 'airship nearing', 'xScale': small, 'yScale': small, 'animationTracks': [
            {'repeat': 'loop', 'steps': [{'delaySeconds': wait, 'durationSeconds': crossing, 'easeType': 'sineinout',
                                          'animateProperties': {'xScale': large, 'yScale': large}}]}],
            'children': [{'id': 'airship image', 'ref': airship_template.OUTPUT + '#airship', 'overrides': {
                'pivot': 'topLeft', 'animationTracks': [
                    {'repeat': 'yoyo', 'steps': [{'durationSeconds': rock_seconds, 'easeType': 'sineinout',
                                                  'animateProperties': {'rotation': rock}}]}]}}]}]}


def turning_windmill():
    images = dict(windmill.cut())
    fence = cutting.image_ref('fence', windmill_template.OUTPUT, 'windmill-fence', images['windmill-fence'])
    tower = cutting.image_ref('tower', windmill_template.OUTPUT, 'windmill-tower', images['windmill-tower'])
    hub = windmill.HUB
    sails = {'id': 'sails', 'ref': windmill_template.OUTPUT + '#windmill-sails',
             'overrides': {'position': {'x': num(hub[0] / 2), 'y': num(hub[1] / 2)}, 'animationTracks': [
                 {'repeat': 'loop', 'steps': [{'durationSeconds': SAIL_TURN, 'easeType': 'linear',
                                               'animateProperties': {'rotation': num(-2 * math.pi, 6)}}]}]}}
    return {'id': 'windmill', 'children': [fence, tower, sails]}


def in_the_valley(drawables):
    """The nodes with every id begun 'valley ', as ids are unique across the files and the terrace places the same
    clouds."""
    for n in cutting.walk(drawables):
        n['id'] = 'valley ' + n['id']
    return drawables


def build():
    images, sizes, flowers = valley.cut(), tree_sizes(), flowers_by_ground()
    mountains = alps.cut()
    hills = [name for name, _, _ in HILLS]
    knoll = hills.index('windmill knoll') + 1
    return {'drawables': in_the_valley([
        cutting.image_ref('sky', sky_template.OUTPUT, sky_template.DAY_VALLEY_TEMPLATE, sky.parts()[1]),
        drifting_clouds(),
        airship(),
        {'id': 'mountains', 'children': [
            cutting.image_ref(name, alps_template.OUTPUT, tid, mountains[name])
            for name, tid in alps_template.TEMPLATES.items()]},
    ] + [hill_node(name, images, sizes, flowers) for name in hills[:knoll]] + [turning_windmill()]
      + [hill_node(name, images, sizes, flowers) for name in hills[knoll:]]
      + [cutting.image_ref('meadow', valley_template.OUTPUT, 'meadow', images['meadow']),
         {'id': 'meadow flowers', 'children': flowers.get('meadow', [])}])}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

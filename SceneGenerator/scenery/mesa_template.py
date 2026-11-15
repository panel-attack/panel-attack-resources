#   Writes JSON, run by `python3 -m scene_export layout`: scenery/mesa.json in the game's scenes/, the gear-arch
#   mesa's templates: the mesa with its ring and trees, the falls, their lip and the spray at their foot.
#
#   The falls are the water's shape and two strips of zigzag bands masked to it, each repeating and scrolling down its
#   own period a loop at its own speed: the back strip slow and soft, the front one twice as fast and white, so the
#   two drift past each other and their pattern only comes round again after many seconds. The lip is the roll of
#   water over the ledge with both strips cut again from the lip's corner sliding over it, under its crest, whose
#   glow breathes on the front strip's beat. At the foot a strip of dimples rolls out over the still foam to each
#   side from under the falls, a mist breathes over it, and foam and drops rise as the front strip's bands land.
#
#   The engine (AnimationLoader.lua) masks a node to the union of its earlier siblings and allows one masked node a
#   parent, since it draws those siblings as the mask with no parent of their own. So every masked node after the
#   first sits in a container of its own with its mask before it: the water's silhouette in black, added to the
#   scene (blendMode add), which changes nothing it draws over.
#
#   python3 -m scenery.mesa_template  ->  the game's scenes/scenery/mesa.json

import math

from scene_export import cutting, layout
from scenery import mesa

OUTPUT = 'scenery/mesa.json'

FRAMES_A_SECOND = 60
CHURN_UNITS_A_FRAME = 0.5        # canvas units the foam's dimples roll out a frame: one 2x texture px, so no judder
RISE = (2, 0.4, 4, 0.7)          # canvas units a set of foam heaves up while it shows and seconds, then while it fades
THROW = (2.5, 0.25, 4.5, 0.55)   # canvas units a set of thrown water rises while it shows and seconds, then while it fades
GLOW = (0.4, 1)                  # the crest glow's alpha, dimmest and brightest, breathing over a front period
MIST = (0.55, 1, 1.5)            # the mist's alpha, thinnest and thickest, and seconds each way


def scrolling(key, units, seconds):
    """The track scrolling a repeating image by units along key over seconds, then starting over."""
    return [{'repeat': 'loop', 'steps': [{'durationSeconds': cutting.num(seconds, 4), 'easeType': 'linear',
                                          'animateProperties': {key: cutting.num(units)}}]}]


def falling(name):
    """The track scrolling the strip down one period, in canvas units, at its speed, then starting over."""
    period = cutting.length(mesa.STRIPS[name]['period'])
    return scrolling('scrollY', -period, period_seconds(name))


def period_seconds(name):
    """Seconds the strip takes to scroll one period."""
    return cutting.length(mesa.STRIPS[name]['period']) / mesa.STRIPS[name]['speed'] / FRAMES_A_SECOND


def falls(parts):
    """The water's shape with the back strip masked to it, then the front strip masked to the shape's silhouette in a
    container of its own, all drawn from the strip's corner."""
    return {'id': 'mesa-falls', 'templateOnly': True, 'children': [
        {'id': 'falls-shape', 'filePath': parts['mesa-falls-shape'].path},
        {'id': 'falls-back', 'filePath': parts['mesa-falls-back'].path, 'stencil': True, 'wrap': 'repeat',
         'animationTracks': falling('back')},
        {'id': 'falls-front-layer', 'children': [
            {'id': 'falls-front-mask', 'filePath': parts['mesa-falls-mask'].path, 'blendMode': 'add'},
            {'id': 'falls-front', 'filePath': parts['mesa-falls-front'].path, 'stencil': True, 'wrap': 'repeat',
             'animationTracks': falling('front')}]}]}


def breathing(low, high, seconds):
    """The track taking a node's alpha from low to high over seconds and back, over and over."""
    return [{'repeat': 'yoyo', 'steps': [{'durationSeconds': cutting.num(seconds, 4), 'easeType': 'sineinout',
                                          'animateProperties': {'alpha': high}}]}]


def lip(parts):
    """The roll of water over the lip, the back strip masked to it sliding over it with the falls, the front strip
    likewise in a container of its own with the roll's silhouette as its mask, the crest over them, and the crest's
    glow breathing on the front strip's beat."""
    low, high = GLOW
    return {'id': 'mesa-falls-lip', 'templateOnly': True, 'children': [
        {'id': 'lip', 'filePath': parts['mesa-falls-lip'].path},
        {'id': 'lip-sheets', 'filePath': parts['mesa-lip-sheets'].path, 'stencil': True, 'wrap': 'repeat',
         'animationTracks': falling('back')},
        {'id': 'lip-front-layer', 'children': [
            {'id': 'lip-mask', 'filePath': parts['mesa-lip-mask'].path, 'blendMode': 'add'},
            {'id': 'lip-front', 'filePath': parts['mesa-lip-front'].path, 'stencil': True, 'wrap': 'repeat',
             'animationTracks': falling('front')}]},
        {'id': 'crest', 'filePath': parts['mesa-falls-crest'].path},
        {'id': 'crest-glow', 'filePath': parts['mesa-falls-crest-glow'].path, 'alpha': low,
         'animationTracks': breathing(low, high, period_seconds('front') / 2)}]}


def landings():
    """Seconds into the front strip's period at which each of its bands' teeth reach the foam, earliest first."""
    speed = mesa.STRIPS['front']['period'] / period_seconds('front')
    return sorted((mesa.FOAM_LINE - bottom) % mesa.STRIPS['front']['period'] / speed
                  for _, bottom in mesa.band_spans('front'))


def throwing(first, rise, rise_s, lift, fade_s):
    """The track throwing a set up as a front band lands in the foam, fading as it rises, looping over a whole number
    of the front strip's periods so it keeps the bands' beat: the first set with the earliest band, the second with
    the band landing nearest half a loop later."""
    period = period_seconds('front')
    loop = period * math.ceil(2 * (rise_s + fade_s) / period)
    lands = landings()
    start = lands[0]
    if not first:
        times = [t + k * period for k in range(math.ceil(loop / period)) for t in lands]
        start = min((t for t in times if t + rise_s + fade_s <= loop), key=lambda t: abs(t - start - loop / 2))
    steps = [{'durationSeconds': rise_s, 'easeType': 'quadout', 'animateProperties': {'alpha': 1, 'y': -rise}},
             {'durationSeconds': fade_s, 'easeType': 'quadin', 'animateProperties': {'alpha': 0, 'y': -lift}},
             {'durationSeconds': round(loop - start - rise_s - fade_s, 6), 'easeType': 'linear',
              'animateProperties': {'alpha': 0}}]
    if start:
        steps[0]['delaySeconds'] = round(start, 6)
    return [{'repeat': 'loop', 'steps': steps}]


def churning(parts, side):
    """A container of its own for each side's churn: the bed's half in black as its mask, then the strip of dimples
    masked to it, placed a period left of the spray's centre or at it, rolling out from the centre: the left side
    scrolls on so its dimples move left, the right side back."""
    spray, churn = parts['mesa-spray'].box, parts['mesa-spray-churn'].box
    x = churn[0] + (0 if side == 'left' else mesa.CHURN_PERIOD)
    units = cutting.length(mesa.CHURN_PERIOD)
    seconds = units / CHURN_UNITS_A_FRAME / FRAMES_A_SECOND
    return {'id': 'mesa-spray-churn-' + side, 'children': [
        {'id': 'churn-mask-' + side, 'filePath': parts['mesa-spray-churn-mask-' + side].path, 'blendMode': 'add'},
        {'id': 'churn-' + side, 'filePath': parts['mesa-spray-churn'].path, 'stencil': True, 'wrap': 'repeat',
         'position': {'x': cutting.num(cutting.length(x - spray[0])), 'y': cutting.num(cutting.length(churn[1] - spray[1]))},
         'animationTracks': scrolling('scrollX', units if side == 'left' else -units, seconds)}]}


def spray(parts):
    """The spray's still shade and solid bed, the churn rolling out over the bed to each side, the mist breathing
    over it, foam rising off it in turn, and the loose water thrown up from it in turn."""
    low, high, seconds = MIST
    rising = [{'id': tid, 'filePath': parts[tid].path, 'alpha': 0, 'animationTracks': throwing(k == 0, *RISE)}
              for k, tid in enumerate(['mesa-spray-rise-a', 'mesa-spray-rise-b'])]
    thrown = [{'id': tid, 'filePath': parts[tid].path, 'alpha': 0, 'animationTracks': throwing(k == 0, *THROW)}
              for k, tid in enumerate(['mesa-thrown-water-a', 'mesa-thrown-water-b'])]
    return {'id': 'mesa-spray', 'templateOnly': True, 'children': [
        {'id': 'spray-shade', 'filePath': parts['mesa-spray'].path},
        {'id': 'spray-bed', 'filePath': parts['mesa-spray-bed'].path},
        churning(parts, 'left'), churning(parts, 'right'),
        {'id': 'mesa-spray-mist', 'filePath': parts['mesa-spray-mist'].path, 'alpha': low,
         'animationTracks': breathing(low, high, seconds)}] + rising + thrown}


def placements():
    """[(template id, the part where it is placed)], in drawing order."""
    parts = dict(mesa.cut())
    return [('mesa', parts['mesa']), ('mesa-falls', parts['mesa-falls-back']), ('mesa-falls-lip', parts['mesa-falls-lip']),
            ('mesa-spray', parts['mesa-spray'])]


def build():
    parts = dict(mesa.cut())
    return {'drawables': [cutting.image_template('mesa', parts['mesa']), falls(parts), lip(parts), spray(parts)]}


if __name__ == '__main__':
    layout.write(OUTPUT)

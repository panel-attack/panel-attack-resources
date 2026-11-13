#   Writes JSON, run by `python3 -m scene_export layout`: EsmeTerrace/EsmeTerrace.json in the game's scenes/, the
#   terrace scene. It draws, back to front: the sky, the clouds drifting in the wind, the landscape, the lake's
#   glints twinkling, the woods on its far shore, the town, the trees beyond the rail and the lake below it, then
#   the floor, the rail and each object on its shadow, in the original painting's layer order. Everything but the images drawn only for this
#   camera (background.py's, the floor, the rail and the shadows) is a ref to a template, placed where its generator
#   drew it.
#
#   python3 -m EsmeTerrace.EsmeTerrace  ->  the game's scenes/EsmeTerrace/EsmeTerrace.json

from scene_export import cutting, layout, wind
from scenery import clouds, clouds_template, landscape, landscape_template, sky, sky_template
from structures import houses, houses_template
from plants import bushes_template
from furniture import planters_template, table_set, table_set_template
from EsmeTerrace import background, floor, placements, rail, shadows

OUTPUT = 'EsmeTerrace/EsmeTerrace.json'


def by_id(nodes):
    return {n['id']: n for n in nodes}


def drifting_clouds():
    children = []
    for cid, part in clouds.cut():
        node = cutting.image_ref(cid, clouds_template.OUTPUT, clouds_template.template_id(cid), part)
        node['overrides']['animationTracks'] = wind.drift(node['overrides'], cutting.length(part.box[2]), clouds.speed(cid))
        children.append(node)
    return {'id': 'clouds', 'children': children}


def lake_shimmer():
    images = landscape.cut()
    children = []
    for name, bright in (('shimmer a', True), ('shimmer b', False)):
        node = cutting.image_ref('lake ' + name, landscape_template.OUTPUT, landscape_template.TEMPLATES[name],
                                 images[name])
        node['overrides'].update(wind.twinkle(node['overrides'], bright))
        children.append(node)
    return {'id': 'lake shimmer', 'children': children}


def town(drawn):
    trees = by_id(drawn['town']['children'])
    return {'id': 'town', 'children': [
        cutting.image_ref('far village', landscape_template.OUTPUT, landscape_template.TEMPLATES['far village'],
                          landscape.cut()['far village']),
        trees['cypresses behind houses'],
        {'id': 'buildings', 'children': [cutting.image_ref(hid, houses_template.OUTPUT, tid, part)
                                         for hid, tid, part in houses.cut()]},
        trees['trees among houses'],
        trees['town cypresses'],
    ]}


def on_its_shadow(obj, shadow, file, template_id, children):
    return {'id': obj, 'children': [cutting.image_node(obj + ' shadow', shadow),
                                    cutting.object_ref(obj + ' object', file, template_id, children)]}


def generated():
    """The terrace as the generators draw it, before the scene-editor edits."""
    drawn = by_id(background.cut()[1])
    shadow = shadows.cut()
    objects = [(obj, planters_template.OUTPUT, tid, placements.object_children(obj))
               for obj, tid in planters_template.TEMPLATES.items()]
    objects.append(('table set', table_set_template.OUTPUT, table_set_template.TEMPLATE, table_set.cut()[1]))
    objects += [(obj, bushes_template.OUTPUT, tid, placements.object_children(obj))
                for obj, tid in bushes_template.TEMPLATES.items()]
    return {'drawables': [
        cutting.image_ref('sky', sky_template.OUTPUT, sky_template.TEMPLATE, sky.parts()[0]),
        drifting_clouds(),
        cutting.image_ref('background', landscape_template.OUTPUT, landscape_template.TEMPLATES['background'],
                          landscape.cut()['background']),
        lake_shimmer(),
        drawn['far trees'],
        town(drawn),
        drawn['near trees'],
        drawn['rail end shrub'],
        cutting.image_node('floor', floor.parts()[0]),
        {'id': 'rail', 'children': [cutting.image_node('rail shadow', shadow['rail']),
                                    cutting.image_node('rail rail', rail.parts()[0])]},
    ] + [on_its_shadow(obj, shadow[obj], file, tid, children) for obj, file, tid, children in objects]}


def build():
    return {'drawables': placements.terrace(generated()['drawables'])}


if __name__ == '__main__':
    layout.write(OUTPUT)

#   Writes JSON, run by `python3 -m scene_export layout`: structures/windmill.json in the game's scenes/, the
#   windmill's tower, sails and fence templates. The sails turn about their centre, the hub, so their anchor and
#   pivot are "center".
#
#   python3 -m structures.windmill_template  ->  the game's scenes/structures/windmill.json

from scene_export import cutting, layout
from structures import windmill

OUTPUT = 'structures/windmill.json'


def build():
    out = []
    for tid, part in windmill.cut():
        node = cutting.image_template(tid, part)
        if tid == 'windmill-sails':
            node.update(anchor='center', pivot='center')
        out.append(node)
    return {'drawables': out}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

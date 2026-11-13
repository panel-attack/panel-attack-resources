#   Writes JSON, run by `python3 -m scene_export layout`: plants/lantern_tree.json in the game's scenes/, the
#   TrainMeadow lantern tree's templates: its trunk and crown as images, and the lantern and the gear banner
#   hanging from its limb, each anchored and pivoting at its top centre, the point it hangs from, so the scene can
#   swing it.
#
#   python3 -m plants.lantern_tree_template  ->  the game's scenes/plants/lantern_tree.json

from scene_export import cutting, layout
from plants import lantern_tree

OUTPUT = 'plants/lantern_tree.json'


def build():
    out = []
    for tid, part in lantern_tree.cut():
        node = cutting.image_template(tid, part)
        if tid.partition('lantern-tree-')[2] in lantern_tree.HANGERS:
            node.update(anchor='topCenter', pivot='topCenter')
        out.append(node)
    return {'drawables': out}


if __name__ == '__main__':
    layout.write(OUTPUT)

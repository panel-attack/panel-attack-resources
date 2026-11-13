#   Writes JSON, run by `python3 -m scene_export layout`: plants/blossom.json in the game's scenes/, the train
#   meadow's blossom tree templates: the trunk and the two crown clumps as images placed where they sit, and the
#   loose clusters, each swinging about where it hangs from its twig, so their anchor and pivot are "center".
#
#   python3 -m plants.blossom_template  ->  the game's scenes/plants/blossom.json

from scene_export import cutting, layout
from plants import blossom

OUTPUT = 'plants/blossom.json'


def build():
    out = []
    for tid, part in blossom.cut():
        node = cutting.image_template(tid, part)
        if tid in blossom.CLUSTERS:
            node.update(anchor='center', pivot='center')
        out.append(node)
    return {'drawables': out}


if __name__ == '__main__':
    layout.write(OUTPUT)

#   Writes JSON, run by `python3 -m scene_export layout`: plants/broadleaf.json in the game's scenes/, the day
#   valley's round broadleaf tree and bush templates, each standing on its foot.
#
#   python3 -m plants.broadleaf_template  ->  the game's scenes/plants/broadleaf.json

from scene_export import layout
from plants import broadleaf

OUTPUT = 'plants/broadleaf.json'


def build():
    return {'drawables': [{'id': p.path.rpartition('/')[2], 'filePath': p.path, 'anchor': 'bottomCenter',
                           'pivot': 'bottomCenter', 'templateOnly': True} for p in broadleaf.parts()]}


if __name__ == '__main__':
    layout.write(OUTPUT, build())

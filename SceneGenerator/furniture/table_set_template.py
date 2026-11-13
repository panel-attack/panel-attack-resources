#   Writes JSON, run by `python3 -m scene_export layout`: furniture/table-set.json in the game's scenes/, the
#   table and chairs template.
#
#   python3 -m furniture.table_set_template  ->  the game's scenes/furniture/table-set.json

from scene_export import cutting, layout
from furniture import table_set

OUTPUT = 'furniture/table-set.json'
TEMPLATE = 'table-set'


def build():
    return {'drawables': [cutting.object_template(TEMPLATE, table_set.cut()[1])]}


if __name__ == '__main__':
    layout.write(OUTPUT)

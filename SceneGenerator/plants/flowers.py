#   Writes SVG, run by `python3 -m scene_export render`: no sheet; render writes each flower, daisy and bud template's part
#   straight from templates.py, drawn about its stem at the resolution the largest ref to it needs.

from scene_export import placed_foliage


def parts():
    return placed_foliage.template_parts('flowers')

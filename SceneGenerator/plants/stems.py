#   Writes SVG, run by `python3 -m scene_export render`: no sheet; render writes each stem template's part
#   straight from templates.py, drawn about its stem at its template size.

from scene_export import placed_foliage


def parts():
    return placed_foliage.template_parts('stems')

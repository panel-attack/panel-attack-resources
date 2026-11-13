import colorsys
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scene_export import svgtools


# The Esme terrace's outline style, measured on its sheet (scenery/landscape.py, plants/broadleaf.py): a line is a
# dark shade of the shape's own colour, never near-black or a navy ink, and as thin as 0.9 px far off to 2.8 px near.
ESME_LINE_WIDTHS = (0.9, 3.0)
HUE_SLACK = 25 / 360.0
GREY = 0.15                      # below this saturation a colour has no hue to match
NEAR_BLACK = 64 / 255.0          # a line's value below this is near-black


def hsv(colour):
    r, g, b = (int(colour[k:k + 2], 16) / 255.0 for k in (1, 3, 5))
    return colorsys.rgb_to_hsv(r, g, b)


def is_shade_of(line, fill):
    """Whether line is a dark shade of fill: the same hue, darker, no greyer, and not near-black."""
    lh, ls, lv = hsv(line)
    fh, fs, fv = hsv(fill)
    hue_off = min(abs(lh - fh), 1 - abs(lh - fh))
    same_hue = hue_off <= HUE_SLACK or min(ls, fs) < GREY
    return same_hue and lv < fv and ls >= fs * 0.5 and lv >= NEAR_BLACK


def solid_fills(group, grads):
    """Every solid colour filled in the group, a gradient's stops included."""
    out = set()
    for p in group.iter():
        fill = p.get('fill', 'none')
        if fill.startswith('#'):
            out.add(fill)
        elif fill.startswith('url('):
            out.update(grads[fill[5:-1]])
    return out


def outlines(root, grads):
    """[(id, stroke colour, width, the solid fills of its innermost group)] of every outline on the sheet: a stroked
    path, unless it is lighter than every fill of its group, a highlight rather than an outline."""
    parents = {child: parent for parent in root.iter() for child in parent}
    out = []
    for p in root.iter('{%s}path' % svgtools.SVG_NS):
        fills = solid_fills(parents[p], grads)
        if p.get('stroke') and any(hsv(p.get('stroke'))[2] < hsv(fill)[2] for fill in fills):
            out.append((p.get('id'), p.get('stroke'), float(p.get('stroke-width')), fills))
    return out


def sheet_of(svg):
    """(root, {gradient id: its stop colours}) of a drawn Svg."""
    root = ET.fromstring('<svg xmlns="%s">%s</svg>' % (svgtools.SVG_NS, '\n'.join(svg.parts)))
    return root, {gid: (c0, c1) for (c0, c1, _, _), gid in svg.grads.items()}


def pytest_sessionstart(session):
    """Draws the sheets the tests read when there are none yet, as on a fresh checkout."""
    from scene_export import SHEETS, __main__ as main
    if not os.path.isdir(SHEETS):
        main.draw_sheets()

#   Library, writes nothing: reference measurements planters.py fits to.
#
#   Landmarks of the planters measured on panel-attack-references/EsmeTerrace/source.png
#   (screen px, read off 3-5x zoom crops with a 10 px grid). planters.py fits
#   its 3D pieces to these, and `python3 -m furniture.planters check` prints the error
#   of every landmark.
#
#   A ring is one horizontal circle of a turned pot, as the ellipse it draws:
#     cx, cy  centre (cy is the height of its left and right extremes)
#     a       half width
#     b       half height, when the ellipse's front and back (or its
#             curvature) can be read; None takes the foreshortening from the
#             rings either side
#     fy      front-most y, given instead of cy when only the front shows
#   Outlines are closed screen polygons round a bush's leaves and flowers.

# ---------------------------------------------------------------- crystal planter
CRYSTAL_RINGS = {
    'plinth bottom': dict(cx=767.5, cy=723.0, a=160.5, b=33.0),     # front 756
    'plinth top': dict(cx=767.5, cy=709.0, a=160.5, b=28.0),        # front 737
    'body bottom': dict(cx=768.0, fy=731.0, a=143.0),
    'body top': dict(cx=768.0, fy=672.0, a=141.0),
    'rim bottom': dict(cx=768.5, cy=659.0, a=143.5, b=21.0),        # front 680; round 8: seen from above
    'rim top': dict(cx=768.5, cy=639.0, a=143.5, b=18.0),           # front 657, its lit top face shows
}
CRYSTAL_GEM_FRAME = dict(top=(769, 634), bottom=(769, 730), left=(732, 680), right=(805, 680))
CRYSTAL_GEM = dict(top=(768, 650), bottom=(768, 712), left=(745, 680), right=(791, 680))
# Crystal points: the apex, and the corners where the prism meets the point (shoulders); the big
# crystal's front ridge is the lowest of those corners.
CRYSTAL_POINTS = {
    'big crystal': dict(tip=(768, 420), shoulder_left=(725.5, 472), shoulder_right=(810.5, 471),
                        ridge=(764.5, 494)),
    'left crystal': dict(tip=(699.5, 532), shoulder_left=(685.5, 566), shoulder_right=(739.5, 555.5)),
    'right crystal': dict(tip=(836, 523), shoulder_left=(799, 550), shoulder_right=(850, 560)),
}
CRYSTAL_BUSH = [(603, 678), (594, 640), (602, 612), (618, 585), (640, 562), (663, 547), (690, 540),
                (720, 560), (768, 570), (815, 560), (845, 545), (872, 539), (897, 560), (917, 595),
                (935, 632), (931, 668), (905, 656), (768, 657), (630, 656)]
# The lower bush in front of the crystals: its leaves and flowers cover the small crystals below y ~606
# and the big one below ~592; its front leaves end on the rim's top edge.
CRYSTAL_FRONT_BUSH = [(603, 678), (598, 645), (608, 615), (622, 600), (640, 588), (660, 580), (685, 582),
                      (700, 598), (720, 607), (745, 602), (768, 592), (790, 602), (815, 600), (832, 580),
                      (852, 572), (872, 588), (895, 598), (915, 615), (930, 640), (931, 668), (905, 656),
                      (768, 657), (630, 656)]
# The leaves lying over the rim's ends and hanging off them: (base, tip).
CRYSTAL_SIDE_LEAVES = [((636, 641), (597, 640)), ((624, 650), (603, 679)), ((900, 640), (935, 634)),
                       ((912, 648), (931, 669))]
# Where each crystal disappears behind the bush: (x0, x1, lowest visible y) of the crystal's own colour.
CRYSTAL_SHOW = {'left crystal': (690, 735, 607), 'big crystal': (735, 800, 590), 'right crystal': (800, 840, 605)}

# ---------------------------------------------------------------- left urn
LEFT_URN_RINGS = {
    'base bottom': dict(cx=393.5, cy=733.0, a=66.5, b=14.0),        # front 747
    'base top': dict(cx=393.5, cy=718.0, a=66.5, b=13.0),           # front 731
    'stem foot': dict(cx=394.5, fy=729.5, a=54.5),
    'stem top': dict(cx=393.0, fy=711.0, a=40.0),
    'collar mid': dict(cx=393.5, cy=699.0, a=43.5),
    'collar top': dict(cx=393.5, cy=691.0, a=43.0),
    # the bowl is drawn a few px right of the foot's axis (centre 393.5 at the collar, ~401 at its widest);
    # both sides read where the leaves leave them clear (left side at x 324..350, right at 436..478)
    'bowl 1': dict(cx=393.5, cy=690.0, a=43.5),
    'bowl 2': dict(cx=396.75, cy=685.0, a=50.75),
    'bowl 3': dict(cx=398.25, cy=675.0, a=64.25),
    'bowl 4': dict(cx=401.0, cy=662.0, a=75.0),
    'bowl widest': dict(cx=400.75, cy=654.0, a=80.0),             # round 8: bulges past the rim
    'rim bottom': dict(cx=401.5, cy=628.0, a=77.5, b=13.0),         # front 641; round 8: seen from above
    'rim top': dict(cx=401.5, cy=607.0, a=77.5, b=12.0),            # front 619
}
LEFT_URN_GEM = dict(centre=(410.5, 668), half=(17, 21))
LEFT_URN_RIM_GEM = dict(centre=(411.75, 631), half=(8, 7.75))
LEFT_URN_BUSH = [(265, 625), (276, 600), (288, 575), (300, 553), (322, 530), (345, 512), (385, 505),
                 (426, 497), (452, 508), (478, 540), (500, 560), (513, 585), (520, 612), (515, 642),
                 (470, 628), (400, 625), (320, 630), (275, 640)]
LEFT_URN_VINES = dict(left=(305, 715), right=(497, 700))          # lowest leaf tips of the hanging vines

# ---------------------------------------------------------------- right urn (behind the table)
# Round 10: the right urn is the left one mirrored across the terrace's centre line (world X -> -X), so it
# stands at the same depth and is the same size. The camera looks straight down +Z, so that mirror is
# exactly the screen mirror about the camera's centre column; every landmark is mirrored there and the
# rig is fitted to them like the left urn's (the lean flips with it, keeping the bowl leaning inwards).
# The table set draws over it.
MIRROR_X = 768.0                      # terrace.built_terrace().camera.centre_x


def _mirror(x, y):
    return (2 * MIRROR_X - x, y)


RIGHT_URN_RINGS = {name: dict(ring, cx=2 * MIRROR_X - ring['cx']) for name, ring in LEFT_URN_RINGS.items()}
RIGHT_URN_GEM = dict(centre=_mirror(*LEFT_URN_GEM['centre']), half=LEFT_URN_GEM['half'])
RIGHT_URN_RIM_GEM = dict(centre=_mirror(*LEFT_URN_RIM_GEM['centre']), half=LEFT_URN_RIM_GEM['half'])
RIGHT_URN_BUSH = [_mirror(x, y) for x, y in LEFT_URN_BUSH]
RIGHT_URN_VINES = dict(left=_mirror(*LEFT_URN_VINES['right']), right=_mirror(*LEFT_URN_VINES['left']))

#   Library, writes nothing: reference measurements bushes.py draws the corner bush to.
#
#   Read off panel-attack-references/EsmeTerrace/source-left-bush.webp scaled to 1536 x 1024 (the right side pulled in ~10 px,
#   since the outline leaves' tips poke a little past it): a big rounded rose bush in a
#   gold planter filling the bottom-left corner, in front of the rail and over the floor's front edge.

CORNER_BUSH_OUTLINE = [(-20, 1044), (-20, 620), (10, 618), (35, 632), (55, 650), (78, 668), (100, 690),
                       (114, 706), (126, 730), (146, 738), (163, 760), (181, 777), (200, 782), (210, 815),
                       (225, 840), (232, 865), (234, 890), (230, 912), (234, 934), (237, 958), (240, 982),
                       (224, 1008), (210, 1044)]
# (x, y, radius, kind): five-petal pinks, two full roses, white daisies
CORNER_BUSH_FLOWERS = [
    (15, 673, 18, 'pink'), (45, 696, 18, 'pink'), (88, 727, 23, 'pink'), (20, 755, 25, 'pink'),
    (72, 867, 27, 'pink'), (188, 853, 23, 'pink'),
    (82, 800, 28, 'rose'), (125, 873, 32, 'rose'),
    (112, 773, 26, 'white'), (32, 808, 29, 'white'), (143, 823, 26, 'white'), (142, 925, 25, 'white'),
]
# The planter's rim: an ellipse (centre, half width, half height) and the depth of its front band
CORNER_PLANTER_RIM = dict(cx=78, cy=964, a=136, b=28, band=34)

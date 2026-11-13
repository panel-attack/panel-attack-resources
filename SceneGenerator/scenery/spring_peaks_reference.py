#   Library, writes nothing: the train meadow's snowy mountains, laid out in sheet px over
#   panel-attack-references/TrainMeadow/stage.png and drawn as the day valley's are (scenery/alps_reference.py): the
#   same rock blues, lilac lit planes, gullies, haze, ridge line and snow layers, in the train meadow's own layout.
#   In the terrace mountains' terms (scenery/landscape.py): faceted ranges of (name, blue, lit, ridge, lit planes,
#   gullies as (top, bottom, half width)) and, on a snowy peak, its snowcap of (light strips, shaded snow, snow, snow
#   streaks), back to front. Light comes from the right as on the day valley: a lilac lit plane lies right of each
#   summit, cut by blue gullies, and the snow's sunlit facets lie down the right ridge with light rock strips up the
#   shaded left flank.

from scenery import alps_reference as alps

# The day valley's palette, read off its ranges so the two stages' rock and snow stay one colour.
FAR_BLUE, FAR_LIT = alps.FAR_RANGES[0][1:3]           # the low lilac ranges' rock and lit planes
GULLY = alps.FAR_RANGES[0][4][3][0]                   # the deeper blue plane down a far summit's left flank
MASSIF_BLUE, MASSIF_LIT = alps.MASSIF_RANGES[0][1:3]  # the big peak's rock and the lit plane down its right flank
UNDER_SNOW, LOWER_SLOPE, LONG_FOOT, FOOT_FACET = [plane[0] for plane in alps.MASSIF_RANGES[0][4][1:5]]
#   ... its pale plane under the snow, the paler lower slopes, the palest long foot and the small lilac foot facet
RIGHT_BLUE, RIGHT_LIT = alps.MASSIF_RANGES[1][1:3]    # the nearer lilac range's rock and lit planes
RIGHT_SLIVER = alps.MASSIF_RANGES[1][4][1][0]         # the narrow plane straight down from its summit
LIGHT_ROCK, SNOW_SHADE, SNOW_WHITE, SNOW_STREAK = [layer[0] for layer in alps.SNOWCAP]


HAZE = alps.HAZE
OUTLINE = alps.OUTLINE
FOOT = 440                       # the feet stop here, under the hills in front from about y 345


# The low pale range across the whole back, Esme's far range: a summit behind the blossom tree on the left and
# the twin summits behind the lantern tree on the right, the middle hidden under the peaks in front.
FAR_RANGES = [
    ('far range', FAR_BLUE, FAR_LIT,
     [(-40, 374), (20, 350), (80, 338), (130, 346), (175, 306), (215, 336), (245, 330), (280, 348), (320, 372),
      (350, 392), (420, 404), (600, 410), (900, 410), (1180, 356), (1230, 326), (1270, 310), (1310, 296),
      (1350, 318), (1385, 304), (1420, 324), (1470, 338), (1520, 346), (1576, 354)],
     [[(175, 306), (215, 336), (245, 330), (280, 348), (268, 368), (240, 372), (212, 362), (186, 344), (166, 324)],
      [(1310, 296), (1350, 318), (1340, 340), (1316, 336), (1298, 318)],
      [(1385, 304), (1420, 324), (1470, 338), (1520, 346), (1576, 354), (1576, 372), (1500, 372), (1440, 360),
       (1400, 336), (1376, 318)],
      (GULLY, [(175, 308), (166, 324), (150, 350), (120, 350), (130, 346), (152, 326)]),
      (GULLY, [(1385, 306), (1376, 318), (1360, 340), (1340, 340), (1350, 320)])],
     [((182, 316), (212, 364), 4), ((1392, 312), (1430, 356), 4), ((1316, 304), (1338, 336), 3)]),
]


# The snowy peaks left of the big one, nearer and bluer each step toward it: the far caps in the far range's
# lilac, the mid peak in the nearer lilac range's, and the shoulder peak standing in front of the big peak's left
# flank in the big peak's own blue. Every range spreads wide at its foot, so the peaks overlap into one mass.
LEFT_RANGES = [
    ('far left peaks', FAR_BLUE, FAR_LIT,
     [(40, 440), (140, 392), (240, 356), (300, 338), (335, 328), (372, 304), (402, 340), (430, 336), (480, 348),
      (560, 376), (660, 404), (760, 440)],
     [[(372, 304), (402, 340), (430, 336), (480, 348), (466, 372), (430, 380), (398, 370), (365, 352), (362, 326)],
      (GULLY, [(372, 306), (362, 326), (350, 352), (322, 352), (335, 330)])],
     [((378, 312), (410, 370), 4)],
     (None, None,
      (SNOW_WHITE, [[(358, 322), (372, 304), (386, 322), (394, 332), (384, 332), (378, 344), (370, 328), (362, 334),
               (356, 326)]]),
      None)),
    ('left mid peak', RIGHT_BLUE, RIGHT_LIT,
     [(240, 440), (340, 380), (420, 336), (480, 304), (548, 276), (590, 302), (640, 334), (710, 362), (800, 390),
      (900, 420), (980, 440)],
     [[(548, 276), (590, 302), (640, 334), (710, 362), (700, 392), (660, 400), (610, 380), (560, 340), (540, 300)],
      (RIGHT_SLIVER, [(548, 278), (542, 320), (536, 440), (500, 440), (520, 330)])],
     [((560, 290), (600, 350), 5), ((590, 310), (625, 360), 4), ((535, 300), (515, 330), 3)],
     ((LIGHT_ROCK, [((545, 300), (500, 330), 5), ((556, 330), (470, 372), 7)]),
      None,
      (SNOW_WHITE, [[(520, 290), (548, 276), (590, 302), (604, 318), (590, 316), (580, 330), (568, 312), (552, 304),
               (540, 320), (530, 300), (522, 296)]]),
      (SNOW_STREAK, [((560, 290), (585, 310), 2)]))),
    ('left shoulder peak', MASSIF_BLUE, MASSIF_LIT,
     [(440, 440), (520, 380), (600, 330), (660, 294), (715, 254), (760, 290), (810, 324), (880, 356), (970, 390),
      (1060, 420), (1120, 440)],
     [[(715, 254), (760, 290), (810, 324), (880, 356), (900, 440), (700, 440), (690, 330), (700, 280)],
      (UNDER_SNOW, [(714, 256), (690, 274), (660, 294), (640, 306), (646, 314), (668, 302), (696, 282), (712, 268)]),
      (LOWER_SLOPE, [(440, 440), (520, 380), (600, 330), (640, 306), (660, 320), (700, 340), (690, 440), (400, 440)])],
     [((770, 300), (820, 410), 4), ((800, 318), (840, 390), 3)],
     ((LIGHT_ROCK, [((712, 282), (660, 318), 6), ((720, 320), (620, 380), 9)]),
      (SNOW_SHADE, [((706, 268), (680, 286), 3)]),
      (SNOW_WHITE, [[(678, 284), (696, 268), (715, 254), (740, 274), (760, 290), (782, 306), (770, 310), (755, 302),
               (744, 316), (732, 296), (718, 288), (710, 310), (700, 292), (688, 296), (680, 290)],
              [(735, 300), (752, 296), (764, 312), (772, 334), (756, 326), (742, 316)]]),
      (SNOW_STREAK, [((730, 270), (752, 292), 2), ((750, 286), (778, 304), 3)]))),
]


# The big snow-capped peak above the train's crossing with its small snowy shoulder on the left and its twin
# summit on the right, drawn as the day valley's big peak: a lit plane down the right flank, a pale plane under the
# snow on the left, the paler lower slopes out to the long left foot, and the snow over the apex with a toothed lower
# edge, a tongue down the central gully, light rock strips up the left flank and shaded streaks across the sunlit snow.
MASSIF_RANGES = [
    ('massif', MASSIF_BLUE, MASSIF_LIT,
     [(300, 440), (420, 400), (540, 362), (640, 332), (720, 310), (780, 290), (815, 276), (838, 240), (852, 218),
      (872, 240), (890, 232), (925, 195), (965, 158), (995, 195), (1022, 222), (1040, 210), (1062, 240),
      (1120, 290), (1200, 330), (1300, 366), (1420, 404), (1576, 440)],
     [[(1000, 230), (1022, 222), (1040, 210), (1062, 240), (1120, 290), (1200, 330), (1300, 366), (1420, 404),
       (1470, 440), (1040, 440), (990, 320), (985, 260)],
      (UNDER_SNOW, [(963, 160), (945, 175), (925, 195), (908, 214), (890, 232), (896, 244), (914, 236), (934, 218),
                    (950, 196), (962, 178)]),
      (LOWER_SLOPE, [(300, 440), (420, 400), (540, 362), (640, 332), (720, 310), (780, 290), (815, 276), (838, 240),
                     (852, 218), (872, 240), (890, 232), (910, 255), (960, 280), (1000, 300), (1010, 440), (260, 440)]),
      (LONG_FOOT, [(300, 440), (420, 400), (540, 362), (640, 332), (720, 310), (780, 290), (800, 282), (796, 320),
                   (780, 350), (770, 440), (260, 440)]),
      (FOOT_FACET, [(820, 274), (836, 290), (815, 298), (775, 306), (735, 314), (760, 300), (795, 286)])],
     [((1090, 290), (1130, 372), 6), ((1150, 300), (1186, 370), 5)],
     ((LIGHT_ROCK, [((962, 200), (905, 240), 8), ((970, 250), (760, 340), 14), ((860, 246), (800, 276), 8),
                    ((830, 250), (770, 296), 5)]),
      (SNOW_SHADE, [((950, 184), (912, 210), 4)]),
      (SNOW_WHITE, [[(965, 158), (995, 195), (1022, 222), (1040, 210), (1062, 240), (1085, 260), (1108, 280),
                     (1092, 284), (1072, 266), (1054, 256), (1036, 250), (1022, 282), (1006, 240), (988, 232),
                     (978, 266), (970, 224), (966, 196), (963, 172)],
                    [(1000, 250), (1030, 243), (1050, 262), (1058, 290), (1066, 318), (1048, 300), (1030, 286),
                     (1010, 270)],
                    [(964, 160), (945, 175), (925, 195), (908, 214), (890, 232), (894, 238), (912, 220), (930, 202),
                     (950, 182), (966, 166)],
                    [(838, 240), (852, 218), (872, 240), (880, 242), (868, 252), (856, 244), (846, 256), (836, 246)]]),
      (SNOW_STREAK, [((1000, 200), (1030, 232), 2.5), ((1030, 222), (1060, 250), 2.5), ((1045, 232), (1080, 258), 4)]))),
]


# The bare lilac peak standing in front of the big peak's right flank, as the day valley's right range: a lit
# plane down its right flank cut by gullies and a narrow deeper plane straight down from the summit.
RIGHT_RANGES = [
    ('right peak', RIGHT_BLUE, RIGHT_LIT,
     [(900, 440), (980, 380), (1050, 326), (1095, 286), (1125, 256), (1152, 280), (1182, 302), (1240, 330),
      (1320, 360), (1420, 392), (1530, 420), (1576, 440)],
     [[(1125, 256), (1152, 280), (1182, 302), (1240, 330), (1320, 360), (1420, 392), (1440, 440), (1160, 440),
       (1110, 330), (1112, 280)],
      (RIGHT_SLIVER, [(1125, 258), (1112, 290), (1100, 440), (1060, 440), (1090, 330)])],
     [((1150, 290), (1200, 380), 5), ((1190, 310), (1240, 400), 4), ((1110, 284), (1090, 320), 3)]),
]


# A thin band of distant hills at the mountains' feet, blue-green like the far hills whose crests stand just in
# front and cover most of it, so the peaks' rock meets the green hills with only slivers of it showing in the dips.
FOOTHILL_RANGES = [
    ('foothills', '#4cbcc4', '#74d4c8',
     [(-40, 392), (80, 384), (200, 376), (300, 372), (400, 378), (480, 384), (560, 378), (660, 370), (760, 366),
      (860, 370), (960, 378), (1060, 374), (1160, 368), (1260, 364), (1360, 370), (1460, 378), (1576, 384)],
     [[(-40, 392), (80, 384), (200, 376), (300, 372), (280, 420), (-40, 420)],
      [(480, 384), (560, 378), (660, 370), (760, 366), (740, 420), (500, 420)],
      [(960, 378), (1060, 374), (1160, 368), (1260, 364), (1240, 420), (980, 420)]],
     []),
]

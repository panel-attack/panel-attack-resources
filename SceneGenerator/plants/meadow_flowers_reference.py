#   Library, writes nothing: where the train meadow's foreground flowers and mossy rocks stand in TrainMeadow/stage.png,
#   in sheet px, so meadow_flowers.py can stand a copy of each template on its reference for comparing.
#
#   Flowers: (template, head centre, head radius in the reference). The flower is placed scaled so its head's petal
#   radius matches, standing on its foot below the head; a lupin is given by
#   its spike's tip and the spike's height. Rocks: (template, foot, width in the reference).

FLOWERS = [
    ('flower-lupin-near', (1454, 570), 150),
    ('flower-lupin-mid', (1396, 626), 100),
    ('flower-lupin-mid', (1512, 616), 56),
    ('flower-lupin-mid', (32, 578), 100),
    ('flower-lupin-mid', (66, 606), 84),
    ('flower-lupin-mid', (106, 652), 60),
    ('flower-violet-mid', (110, 690), 22),
    ('flower-pink-mid', (364, 708), 22),
    ('flower-daisy-mid', (392, 680), 16),
    ('flower-daisy-mid', (428, 686), 15),
    ('flower-pink-mid', (466, 730), 30),
    ('flower-daisy-mid', (640, 748), 17),
    ('flower-daisy-mid', (678, 756), 16),
    ('flower-daisy-mid', (606, 772), 15),
    ('flower-pink-mid', (720, 782), 18),
    ('flower-pink-mid', (1226, 680), 17),
    ('flower-pink-mid', (1262, 700), 18),
    ('flower-violet-mid', (1182, 698), 22),
    ('flower-daisy-mid', (1064, 708), 16),
    ('flower-pink-mid', (1100, 722), 16),
    ('flower-pink-mid', (1030, 732), 15),
    ('flower-lilac-mid', (880, 895), 15),
    ('flower-lilac-mid', (920, 884), 14),
    ('flower-lilac-near', (1497, 750), 34),
    ('flower-violet-mid', (1369, 764), 26),
    ('flower-daisy-near', (277, 795), 36),
    ('flower-buttercup-near', (415, 792), 48),
    ('flower-buttercup-near', (476, 838), 48),
    ('flower-daisy-near', (345, 850), 48),
    ('flower-violet-near', (595, 857), 44),
    ('flower-violet-near', (548, 898), 40),
    ('flower-violet-near', (655, 895), 42),
    ('flower-daisy-near', (1267, 842), 36),
    ('flower-daisy-near', (1190, 865), 36),
    ('flower-daisy-near', (1142, 905), 30),
    ('flower-pink-near', (1312, 875), 58),
    ('flower-violet-near', (1440, 832), 72),
    ('flower-pink-corner', (150, 800), 112),
]

ROCKS = [
    ('rock-tall', (196, 724), 226),
    ('rock-small', (1004, 862), 118),
    ('rock-wide', (1196, 862), 296),
]

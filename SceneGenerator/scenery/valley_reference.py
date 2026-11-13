#   Library, writes nothing: the valley's lines and colours, measured in sheet px off
#   panel-attack-references/DayValley/meadow-stage.png (the meadow painting placed on the 1536 x 1024 sheet).

# Each hill back to front: (name, depth 0 far .. 1 near, its top edge as points left to right). A hill that stops
# inside the land runs its ends down under the hill in front. Trees stand on these edges. The windmill knoll's top is
# even either side of the tower's axis, x 1236, so the fence either side of it can mirror.
HILLS = [
    ('hills far', 0.0, [(-40, 264), (60, 262), (150, 280), (240, 298), (330, 290), (440, 296), (560, 280), (660, 272),
                        (760, 282), (860, 302), (960, 300), (1060, 286), (1160, 296), (1280, 284), (1400, 274),
                        (1576, 282)]),
    ('hills far left', 0.15, [(-40, 282), (50, 280), (150, 296), (250, 324), (350, 352), (430, 372), (500, 392),
                              (560, 440)]),
    ('hills far centre', 0.1, [(340, 400), (450, 330), (580, 298), (680, 288), (780, 296), (880, 326), (960, 380)]),
    ('hills far right', 0.15, [(700, 440), (770, 372), (860, 342), (960, 328), (1040, 330), (1120, 340),
                               (1200, 330), (1300, 310), (1400, 298), (1480, 300), (1576, 310)]),
    ('hills far hump', 0.25, [(500, 420), (600, 362), (720, 340), (840, 340), (940, 360), (1010, 400), (1050, 440)]),
    ('hills middle left', 0.4, [(-40, 346), (60, 338), (170, 350), (270, 374), (370, 392), (450, 402), (530, 422),
                                (580, 470)]),
    ('hills middle', 0.45, [(340, 490), (420, 432), (540, 404), (660, 398), (770, 410), (860, 440), (910, 490)]),
    ('hills middle hump', 0.48, [(640, 480), (740, 422), (860, 396), (980, 390), (1080, 402), (1150, 438),
                                 (1190, 490)]),
    ('hills middle right', 0.5, [(1040, 480), (1110, 438), (1200, 414), (1320, 404), (1440, 400), (1576, 404)]),
    ('hills middle near', 0.55, [(660, 520), (740, 480), (830, 458), (930, 448), (1030, 452), (1120, 470),
                                 (1180, 500)]),
    ('hills near middle', 0.65, [(250, 492), (330, 450), (420, 431), (510, 426), (600, 433), (690, 456), (780, 478),
                                 (870, 493), (980, 500), (1100, 508)]),
    ('windmill knoll', 0.85, [(760, 566), (830, 528), (900, 506), (960, 487), (1020, 474), (1066, 469), (1126, 464),
                              (1186, 463), (1236, 462), (1286, 463), (1346, 464), (1406, 469), (1452, 477),
                              (1510, 498), (1576, 524)]),
    ('hills near', 1.0, [(-40, 424), (40, 424), (130, 421), (220, 427), (300, 440), (380, 457), (460, 477),
                         (540, 492), (640, 509), (740, 523), (860, 537), (980, 549), (1100, 556), (1240, 563),
                         (1400, 570), (1576, 579)]),
]


# (sunlit crest, mid tone, shaded body, outline) of each hill: teal-blue far off, teal-green in the middle, the
# sunlit yellow-green of the near hills. A hill's body shades from its mid tone under its top down to its shaded
# colour; its planes are lit over it.
BLUE = ('#5cbdc4', '#38a2cc', '#2e94c4', '#2a80b0')
TEAL_BLUE = ('#66c4b6', '#3ba4c8', '#3098c0', '#2a80b0')
TEAL = ('#90d488', '#7cca96', '#46a8b2', '#1a5a5a')
HILL_COLOURS = {
    'hills far': BLUE,
    'hills far left': BLUE,
    'hills far centre': TEAL_BLUE,
    'hills far right': TEAL_BLUE,
    'hills middle left': TEAL,
    'hills far hump': ('#5ec0b6', '#4fb2a8', '#3a9eb6', '#22707a'),
    'hills middle': TEAL,
    'hills middle hump': TEAL,
    'hills middle right': ('#a8d84a', '#7cbe4f', '#4ea658', '#1f7150'),
    'hills middle near': ('#9ccf5a', '#6cbc78', '#4fa88a', '#22704f'),
    'hills near middle': ('#b9e046', '#8cc84a', '#56a86c', '#22704f'),
    'windmill knoll': ('#c6e03e', '#8ac945', '#51a458', '#0f6348'),
    'hills near': ('#cfe23c', '#a3d13b', '#4da25a', '#0a5e45'),
}


HILL_LINE_WIDTH = (0.9, 3.4)             # px the outline along a hill's top is, far .. near
HILL_LINE_GROWTH = 2.2                   # above 1 keeps far outlines thin until the near hills


# The flat planes slanting across each hill over its shaded body: (x0, x1, drop at x0, drop at x1, depth, tone).
# A plane's top runs from x0 to x1 the given px below the hill's top edge; its bottom bulges depth px below that,
# most toward its downhill end, and it tapers to a point at each end inside the sheet. tone is 'crest' (sunlit) or
# 'mid'. A cap hugging the crest has no drop; a streak lower down slants across the slope.
PLANES = {
    'hills far': [(-40, 1576, 0, 0, 12, 'crest')],
    'hills far left': [(-40, 470, 0, 0, 18, 'crest'), (120, 420, 30, 70, 6, 'crest')],
    'hills far centre': [(400, 900, 0, 0, 18, 'crest'), (560, 900, 30, 66, 6, 'crest')],
    'hills far right': [(740, 1576, 0, 0, 16, 'crest'), (1000, 1320, 34, 64, 6, 'crest')],
    'hills middle left': [(-40, 520, 0, 0, 30, 'crest'), (160, 520, 40, 80, 8, 'crest')],
    'hills far hump': [(560, 1000, 0, 0, 20, 'crest'), (700, 1000, 30, 60, 6, 'crest')],
    'hills middle': [(400, 880, 0, 0, 24, 'crest'), (560, 880, 28, 58, 6, 'crest')],
    'hills middle hump': [(700, 1170, 0, 0, 24, 'crest'), (860, 1160, 30, 60, 6, 'crest')],
    'hills middle right': [(1080, 1576, 0, 0, 50, 'crest'), (1240, 1520, 40, 70, 10, 'crest')],
    'hills middle near': [(700, 1160, 0, 0, 40, 'crest')],
    'hills near middle': [(320, 1100, 0, 0, 48, 'crest'), (520, 960, 40, 66, 10, 'crest')],
    'windmill knoll': [(820, 1480, 0, 0, 34, 'crest'), (1240, 1540, 46, 74, 18, 'crest'), (880, 1160, 44, 56, 12, 'mid')],
    'hills near': [(-40, 760, 0, 0, 70, 'crest'), (560, 1576, 0, 0, 22, 'crest'), (120, 520, 70, 50, 22, 'mid'),
                   (200, 700, 40, 80, 12, 'crest')],
}


# The open meadow in front, its bands back to front: (top edge, colour at its top, colour where the next band
# rises). Each band's top edge is a fringe of fine grass blades over the band behind.
MEADOW = [
    ([(-40, 596), (0, 582), (120, 563), (250, 549), (420, 540), (620, 536), (820, 543), (1000, 557), (1200, 566),
      (1400, 574), (1576, 586)], '#c4e23e', '#94c944'),
    ([(-40, 606), (200, 590), (480, 584), (760, 592), (1040, 586), (1300, 596), (1576, 600)], '#98cb44', '#88c34a'),
    ([(-40, 622), (240, 610), (520, 616), (820, 606), (1120, 614), (1380, 604), (1576, 608)], '#84c24b', '#7bbc4e'),
    ([(-40, 684), (50, 682), (400, 668), (768, 680), (1100, 676), (1480, 649), (1576, 646)], '#5aa95c', '#459960'),
]

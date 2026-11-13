#   Writes JSON, run by `python3 -m scene_export layout`: MainMenu.json in the game's scenes/, the main menu
#   screen drawing the day valley scene over its whole 1280 x 720 canvas.
#
#   python3 -m MainMenu  ->  the game's scenes/MainMenu.json

from scene_export import game, layout, wind

OUTPUT = 'MainMenu.json'
SCENE_NAME = 'DayValley'


def build():
    return game.screen_scene(SCENE_NAME, wind.SCENE_SIZE)


if __name__ == '__main__':
    layout.write(OUTPUT, build())

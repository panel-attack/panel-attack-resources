#   Writes JSON, run by `python3 -m scene_export layout`: MainMenu.json in the game's scenes/, the main menu
#   screen: the canvas container holding the scene SCENE_NAME names.
#
#   python3 -m MainMenu  ->  the game's scenes/MainMenu.json

from scene_export import game, layout

OUTPUT = 'MainMenu.json'
ROOT = True                     # a file the game loads: one canvas container, checked before it is written
SCENE_NAME = 'TrainMeadow'


def build():
    return game.screen_scene(SCENE_NAME)


if __name__ == '__main__':
    layout.write(OUTPUT)

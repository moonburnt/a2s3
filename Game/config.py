import logging

log = logging.getLogger(__name__)

#module where I specify default config settings to reffer to from other modules

FLOOR_TEXTURE = 'Textures/floor.png'
CHARACTER_TEXTURE = 'Textures/character.png'
ENEMY_TEXTURE = 'Textures/enemy.png'
MENU_BGM = 'BGM/menu_theme.ogg'
#the height where character sprite will reside
#I dont understand the exact mechanism and will probably get issues in future
#but for now layers difference needs to be kind of the same as half of sprite's y
ENTITY_LAYER = 16
FLOOR_LAYER = ENTITY_LAYER-16
#whatever below are variables that could be changed by user... potentially
WINDOW_SIZE = {"x": 1280, "y": 720}
#WINDOW_X = 1280
#WINDOW_Y = 720
#this is a float between 0 and 1, e.g 75 equals to "75%"
MUSIC_VOLUME = 0.75
#key is the name of action, value is the name of key in panda syntax
CONTROLS = {"move_up": "arrow_up", "move_down": "arrow_down",
            "move_left": "arrow_left", "move_right": "arrow_right"}

#it may be nice to add minimal allowed size check, but not today
MAP_SIZE = {"x": 600, "y": 300}

from os.path import join
import logging

log = logging.getLogger(__name__)

#module where I specify default config settings to reffer to from other modules

GAME_DIR = '.'
SPRITE_DIR = join(GAME_DIR, 'Sprites')
MUSIC_DIR = join(GAME_DIR, 'BGM')
SFX_DIR = join(GAME_DIR, 'SFX')

#default (x, y) of sprites, to dont specify these manually when not necessary.
#also to make some things that rely on these variables to adjust their values
#on fly in case they will be changed
DEFAULT_SPRITE_SIZE = (32, 32)
#the height where character sprite will reside
#I dont understand the exact mechanism and will probably get issues in future
#but for now layers difference needs to be kind of the same as half of sprite's y
ENTITY_LAYER = DEFAULT_SPRITE_SIZE[0]
FLOOR_LAYER = ENTITY_LAYER-DEFAULT_SPRITE_SIZE[0] #effectively zero
#whatever below are variables that could be changed by user... potentially
WINDOW_SIZE = (1280, 720)
#this is a float between 0 and 1, e.g 75 equals to "75%"
MUSIC_VOLUME = 0.75
#key is the name of action, value is the name of key in panda syntax
CONTROLS = {"move_up": "arrow_up", "move_down": "arrow_down",
            "move_left": "arrow_left", "move_right": "arrow_right",
            "attack": "z"}
#placeholder stats to use
#later I will build this from jsons or whatever configuration files I will choose
STATS = {'default': {'hp': 50, 'dmg': 0, 'mov_spd': 1},
         'player': {"hp": 100, "dmg": 10, 'mov_spd': 3},
         'enemy': {"hp": 100, "dmg": 10, 'mov_spd': 2}}
#it may be nice to add minimal allowed size check, but not today
MAP_SIZE = (600, 300)

#debug stuff
SHOW_COLLISIONS = False

from os.path import join
from panda3d.core import SamplerState
import logging

log = logging.getLogger(__name__)

#module where I specify default config settings to reffer to from other modules

GAME_DIR = '.'
SPRITE_DIR = join(GAME_DIR, 'Sprites')
MUSIC_DIR = join(GAME_DIR, 'BGM')
SFX_DIR = join(GAME_DIR, 'SFX')
GAME_NAME = "There Will Be Game's Name"

#default sprite filtering mode. This is applied to all textures to ensure that
#they wont look blurry or weird
DEFAULT_SPRITE_FILTER = SamplerState.FT_nearest
#default (x, y) of sprites, to dont specify these manually when not necessary.
#also to make some things that rely on these variables to adjust their values
#on fly in case they will be changed
DEFAULT_SPRITE_SIZE = (32, 32)
#the height where character sprite will reside. This need to be half of default
#sprite's size's y, because character's placement counts from center of char's
#object. Make it lower - and legs will be below ground. Higher - and chararacters
#will fly above the ground. This will backfire if there are characters of different
#heights, but for now it will do. And floor layer is always zero. Because yes
ENTITY_LAYER = (DEFAULT_SPRITE_SIZE[1]/2)
FLOOR_LAYER = 0
#whatever below are variables that could be changed by user... potentially
DEFAULT_WINDOW_SIZE = (1280, 720)
WINDOW_SIZE = DEFAULT_WINDOW_SIZE
FULLSCREEN = False
#this is a float between 0 and 1, e.g 75 equals to "75%"
MUSIC_VOLUME = 0.75
SFX_VOLUME = 0.75
#key is the name of action, value is the name of key in panda syntax
CONTROLS = {"move_up": "w", "move_down": "s",
            "move_left": "a", "move_right": "d",
            "attack": "mouse1"}
#placeholder stats to use
#later I will build this from jsons or whatever configuration files I will choose
STATS = {'default': {'hp': 50, 'dmg': 0, 'mov_spd': 1, 'skills': ['atk_0']},
         'player': {"hp": 100, "dmg": 10, 'mov_spd': 3, 'skills': ['atk_0']},
         'enemy': {"hp": 100, "dmg": 10, 'mov_spd': 2, 'skills': ['atk_0']}}

#TODO: rename cd (cooldown) to something like atk_speed and make it work the opposite,
#e.g the more the value - less time it gets to strike again. Also it may be a good
#idea to keep different attack's anims and damage in related subdics, instead of
#relying on global stats and other functions. But thats to solve in future
#"used" is effectively an equal to "on cooldown"
SKILLS = {'atk_0': {'name': 'Basic Attack', 'def_cd': 2, 'cur_cd': 0, 'used': False}}

#animation frames for each action. Tuple[0] is the first frame, tuple[1] is the last
#e.g, for static things, setting it to something like (0, 0) is ok
ANIMS = {'player': {'idle_right': (0,0), 'idle_left': (1,1), 'move_right': (4,7), 'move_left': (8,11)},
         'enemy': {'idle_right': (0,0), 'idle_left': (1,1), 'move_right': (0,0), 'move_left': (1,1)}}

#it may be nice to add minimal allowed size check, but not today
MAP_SIZE = (600, 300)
MAX_ENEMY_COUNT = 10
ENEMY_SPAWN_TIME = 5

#debug stuff
SHOW_COLLISIONS = False
FPS_METER = False

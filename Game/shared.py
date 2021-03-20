#module where I specify variables to reffer to and to override from other modules

import logging

log = logging.getLogger(__name__)

GAME_NAME = "A2S3"

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

#WALLS_COLLISION_MASK = 0X28
#ENEMY_PROJECTILE_COLLISION_MASK = 0X04

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
STATS = {'default': {'hp': 50, 'dmg': 1, 'mov_spd': 1, 'skills': ['atk_0']},
         'player': {"hp": 100, "dmg": 10, 'mov_spd': 3, 'skills': ['atk_0']},
         'enemy': {"hp": 50, "dmg": 10, 'mov_spd': 2, 'skills': ['atk_0']}}

#TODO: rename cd (cooldown) to something like atk_speed and make it work the opposite,
#e.g the more the value - less time it gets to strike again. Also it may be a good
#idea to keep different attack's anims and damage in related subdics, instead of
#relying on global stats and other functions. But thats to solve in future
#"used" is effectively an equal to "on cooldown"
SKILLS = {'atk_0': {'name': 'Basic Attack', 'def_cd': 0.5, 'cur_cd': 0, 'used': False}}

#animation frames for each action. Tuple[0] is the first frame, tuple[1] is the last
#e.g, for static things, setting it to something like (0, 0) is ok
#todo: maybe move attack anim somewhere else, idk
ANIMS = {'player': {'idle_right': (0,0), 'idle_left': (4,4), 'move_right': (8,11),
                    'move_left': (12,15), 'attack_right': (16,19), 'attack_left': (20, 23),
                    'hurt_right': (24, 27), 'hurt_left': (28, 31)},
         'enemy': {'idle_right': (0,0), 'idle_left': (4,4), 'move_right': (0,3),
                   'move_left': (4,7), 'attack_right': (8,11), 'attack_left': (12,15),
                   'hurt_right': (16, 19), 'hurt_left': (20, 23)},
         'attack': {'default': (0, 3)}}

#it may be nice to add minimal allowed size check, but not today
MAP_SIZE = (600, 300)

#debug stuff
SHOW_COLLISIONS = False
FPS_METER = False

## Variables that should be overwritten to use
start_game = None
exit_game = None
restart_level = None
exit_level = None

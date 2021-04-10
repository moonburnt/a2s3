## a2s3 - action arena game, written in python + panda3d
## Copyright (c) 2021 moonburnt
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see https://www.gnu.org/licenses/gpl-3.0.txt

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

#these are collision categories, referring to multiple objects of one type that
#can collide with others and trigger some functions on collision with selected type
ENEMY_CATEGORY = "enemy"
PLAYER_CATEGORY = "player"
PLAYER_PROJECTILE_CATEGORY = "player_projectile"

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
         'cuboid': {"hp": 50, "dmg": 10, 'mov_spd': 2, 'skills': ['atk_0']}}

#TODO: rename cd (cooldown) to something like atk_speed and make it work the opposite,
#e.g the more the value - less time it gets to strike again. Also it may be a good
#idea to keep different attack's anims and damage in related subdics, instead of
#relying on global stats and other functions. But thats to solve in future
#"used" is effectively an equal to "on cooldown"
SKILLS = {'atk_0': {'name': 'Basic Attack', 'def_cd': 0.5, 'cur_cd': 0, 'used': False}}

#I have no idea why, but if 'loop' isnt set to True for single-sprite animations,
#they just refuse to work. #TODO #NEEDFIX
SPRITES = {'player': [{'action': 'idle_right', 'sprites': (0, 0), 'loop': True},
                      {'action': 'idle_left', 'sprites': (4, 4), 'loop': True},
                      {'action': 'move_right', 'sprites': (8, 11), 'loop': True},
                      {'action': 'move_left', 'sprites': (12, 15), 'loop': True},
                      {'action': 'attack_right', 'sprites': (16, 19), 'loop': True},
                      {'action': 'attack_left', 'sprites': (20, 23), 'loop': True},
                      {'action': 'hurt_right', 'sprites': (24, 27)},
                      {'action': 'hurt_left', 'sprites': (28, 31)},
                      {'action': 'dying_left', 'sprites': (32, 35)},
                      {'action': 'dying_right', 'sprites': (36, 39)}],
           'cuboid': [{'action': 'idle_right', 'sprites': (0, 0), 'loop': True},
                      {'action': 'idle_left', 'sprites': (4, 4), 'loop': True},
                      {'action': 'move_right', 'sprites': (0, 3), 'loop': True},
                      {'action': 'move_left', 'sprites': (4, 7), 'loop': True},
                      {'action': 'attack_right', 'sprites': (8, 11), 'loop': True},
                      {'action': 'attack_left', 'sprites': (12, 15), 'loop': True},
                      {'action': 'hurt_right', 'sprites': (16, 19)},
                      {'action': 'hurt_left', 'sprites': (20, 23)},
                      {'action': 'dying_left', 'sprites': (23, 26)},
                      {'action': 'dying_right', 'sprites': (27, 30)}],
           'attack': [{'action': 'default', 'sprites': (0, 3)}]}

#it may be nice to add minimal allowed size check, but not today
MAP_SIZE = (600, 300)

#debug stuff
SHOW_COLLISIONS = False
FPS_METER = False

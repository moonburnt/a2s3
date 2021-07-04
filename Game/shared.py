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
from . import assets_loader
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
ENEMY_PROJECTILE_CATEGORY = "enemy_projectile"

#WALLS_COLLISION_MASK = 0X28

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

#it may be nice to add minimal allowed size check, but not today
MAP_SIZE = (600, 300)

#debug stuff
SHOW_COLLISIONS = False
FPS_METER = False

class Settings:
    pass

class GameData:
    pass

class InterfaceStorage:
    def __init__(self):
        self.storage = {}
        self.currently_active = {}

    def add(self, item, name:str):
        self.storage[name] = item

    def check(self, name:str):
        if name in self.storage:
            return True
        else:
            log.debug(f"{name} doesnt exist in storage!")
            return False

    def show(self, name:str):
        if self.check(name):
            self.currently_active[name] = self.storage[name]
            self.storage[name].show()

            log.info(f"Showing {name} ui")

    def hide(self, name:str):
        if self.check(name):
            if getattr(self.currently_active, name, None):
                self.currently_active.pop(name)
            self.storage[name].hide()

            log.info(f"Hid {name} ui")

    def switch(self, name:str):
        '''Switch CURRENT_INTERFACE menu to one passed as argument'''
        #this is kind of nasty thing. But if used correctly, it should allow to
        #easily switch active interfaces from one to another, in case only one
        #can exist at given time
        if self.currently_active:
            for item in self.currently_active:
                self.storage[item].hide()
            self.currently_active = {}

        self.show(name)

level = None
game_data = GameData()
ui = InterfaceStorage()
assets = assets_loader.AssetsLoader()

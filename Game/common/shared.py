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

# Module where I specify variables to reffer to and to override from other modules.
# If possible, it shouldnt import stuff from any other internal modules/packages,
# except for content of ".common". Its meant to be imported as a whole (e.g "from
# Game.common import shared"), coz otherwise variables get copied and not linked,
# which breaks whole "cross-module sharing" thing and kills purpose of this

from .. import assets_loader, userdata
from . import classes
from copy import deepcopy
import logging

log = logging.getLogger(__name__)

# General / "hardcoded" game data, accessible from other modules
game_data = classes.Storage()
game_data.name = "A2S3"

# (x, y) of sprites, to avoid specifying these manually except when necessary.
# Also to enable autoadjusting of values for things that rely on these
game_data.sprite_size = (32, 32)
game_data.hitbox_size = game_data.sprite_size[0] / 2
# The height at which character's object will appear. This needs to be half of
# character object's y, because character's placement counts from center of it.
# Thus making it lower make legs appear under ground; higher - make char flow.
# This may backfire at some point, but for now will do. Also this will probably
# become obsolete, if we will ever get actual "solid" floor with gravity #TODO
game_data.entity_layer = game_data.sprite_size[1] / 2
# Floor layer is always zero. Because yes
game_data.floor_layer = 0

# These are collision category names, used to mark multiple objects of same type
# to always act the same on collision with other type (and thus make writing of
# collision rules way easier and consistent)
game_data.enemy_category = "enemy"
game_data.player_category = "player"
game_data.player_projectile_category = "player_projectile"
game_data.enemy_projectile_category = "enemy_projectile"

# Default map size. I will probably purge this later in favor of per-map configs
# #TODO
game_data.map_size = (600, 300)

# Value of set_p() applied to floor's tiles
game_data.floor_angle = -90

# Default variables for things that can be altered by user
default_settings = classes.Storage()
default_settings.window_size = (1280, 720)  # (x, y)
default_settings.fullscreen = False
# These are floats between 0 and 1, e.g 75 equals to "75%"
default_settings.music_volume = 0.75
default_settings.sfx_volume = 0.75

# I may want to introduce separate storage for that, at some point #TODO
# Key is the name of action, value is the name of key in panda syntax
default_settings.controls = {
    "move_up": "w",
    "move_down": "s",
    "move_left": "a",
    "move_right": "d",
    "attack": "mouse1",
}

# Debug stuff, which probably wont have option in in-game menu, but will be
# possible to toggle via launch argumenta
default_settings.show_collisions = False
default_settings.fps_meter = False

# Copying storage with default settings to be able to override them, but also use
# defaults as fallback in case these dont match some checks or something
# I can probably use same approach to set default values for other things, like
# skill data, entity data, etc #TODO
settings = deepcopy(default_settings)

# Storages for custom sound managers, must be initialized from GameWindow's init
music_player = None
sfx_manager = None

# Storage for class used to build consistent ui parts
ui_builder = None

# Storage for current level's instance, same as above
level = None

# Storage for various ui types, providing easy interface to switch between items
ui = classes.InterfaceStorage()

# Storage for assets. Since for now it doesnt break stuff, its initialized there
# and not via GameWindow like sound managers. #TODO: remake in case of emergence
assets = assets_loader.AssetsLoader()

# Manager for user settings and stuff
user_data = userdata.UserdataManager()
# Doing this from here, coz else ShowBase hasnt been affected by logging lvls
user_data.load_settings()

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

from Game.common import *
from Game.game_window import *
from Game.entity2d import *
from Game.map_loader import *
from Game.assets_loader import *
from Game.collision_events import *
from Game.level_loader import *
from Game.userdata import *
from Game.interface import *
from Game.music_manager import *
from Game.skill import *

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

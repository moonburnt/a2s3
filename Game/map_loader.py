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

import logging
from panda3d.core import (CardMaker, TextureStage, CollisionPlane,
                          Plane, CollisionNode)
from math import ceil
from Game import shared

log = logging.getLogger(__name__)

#module where I specify everything related to generating and loading maps

class FlatMap:
    def __init__(self, texture, size, scale = None):
        if not scale or scale < 1:
            scale = 1

        raw_size_x = size[0]*scale
        raw_size_y = size[1]*scale
        self.size_x = raw_size_x
        self.size_y = raw_size_y
        self.texture = texture
        log.debug(f"Generating map of size {self.size_x}x{self.size_y}")
        self.map_size = (-self.size_x/2, self.size_x/2, -self.size_y/2, self.size_y/2)
        self.create_floor()
        #TODO: add bool to either generate only some borders or none, to provide
        #ability to fall/kick enemies into the void. This will require addition of
        #collision node to floor, aswell as checks to ensure that entity hasnt fell
        self.add_border_walls()

        #taking advantage of enemies not colliding with map borders and spawning
        #them outside of the map's corners. Idk about the numbers and if they should
        #be related to sprite size in anyway. Basically anything will do for now
        #later we will add some "fog of war"-like effect above map's borders, so
        #enemies spawning on these positions will seem more natural

        #TODO: it may be good idea to make these configurable, instead of hardcoding
        #these to just "outside of map's corners"
        self.enemy_spawnpoints = [(self.map_size[1] + 32, self.map_size[3] + 32),
                                  (self.map_size[0] - 32, self.map_size[2] - 32),
                                  (self.map_size[1] + 32, self.map_size[2] - 32),
                                  (self.map_size[0] - 32, self.map_size[3] + 32)]

        #TODO: make this configurable aswell. For now its just center of map
        self.player_spawnpoint = 0, 0, shared.game_data.entity_layer

    def create_floor(self):
        '''Generate flat floor of size, provided to class'''
        #todo: add fallback values in case size hasnt been specified
        log.debug(f"Generating the floor")

        #initializing new cardmaker object
        #which is essentially our go-to way to create flat models
        floor = CardMaker('floor')
        #setting up card size
        floor.set_frame(*self.map_size)
        #attaching card to render and creating it's object
        #I honestly dont understand the difference between
        #this and card.reparent_to(render)
        #but both add object to scene graph, making it visible
        floor_object = render.attach_new_node(floor.generate())
        floor_object.set_texture(self.texture)
        #determining how often do we need to repeat our texture
        texture_x = self.texture.get_orig_file_x_size()
        texture_y = self.texture.get_orig_file_y_size()
        repeats_x = ceil(self.size_x/texture_x)
        repeats_y = ceil(self.size_y/texture_y)
        #repeating texture to avoid stretching when possible
        floor_object.set_tex_scale(TextureStage.getDefault(), repeats_x, repeats_y)
        #arranging card's angle
        floor_object.look_at((0, 0, -1))
        floor_object.set_pos(0, 0, shared.game_data.floor_layer)

    def add_border_walls(self):
        '''Attaching invisible walls to map's borders, to avoid falling off map'''
        log.debug("Adding invisible walls to collide with on map's borders")
        wall_coordinates = [((self.map_size[0], 0, 0), (self.map_size[1], 0, 0)),
                            ((-self.map_size[0], 0, 0), (-self.map_size[1], 0, 0)),
                            ((0, self.map_size[2], 0), (0, self.map_size[3], 0)),
                            ((0, -self.map_size[2], 0), (0, -self.map_size[3], 0))]

        for sizes in wall_coordinates:
            wall_node = CollisionNode("wall")
            #it looks like without adding node to pusher (we dont need that there),
            #masks wont work. Thus for now I wont use them, as defaults seem to work
            #wall_node.set_collide_mask(BitMask32(shared.WALLS_COLLISION_MASK))
            wall_node.add_solid(CollisionPlane(Plane(*sizes)))
            wall = render.attach_new_node(wall_node)

            #adding tag with wall's coordinations, so it will be possible to
            #push entities back if these collide with wall
            #because calling .get_pos() will return LPoint3f(0,0,0)
            wall_node.set_python_tag("position", sizes)

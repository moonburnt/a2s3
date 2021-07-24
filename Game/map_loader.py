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
from panda3d.core import (
    CardMaker,
    TextureStage,
    CollisionPlane,
    Plane,
    CollisionNode,
    SamplerState,
    Texture,
)
from Game import shared

log = logging.getLogger(__name__)

# module where I specify everything related to generating and loading maps


class FlatMap:
    """Generate flat map with provided settings"""

    def __init__(self, texture: Texture, size: tuple, scale=None, scene=None):
        # if not scale or scale < 1:
        #    scale = 1

        # same as above
        scale = scale if (scale and scale > 1) else 1

        self.size_x = size[0] * scale
        self.size_y = size[1] * scale
        self.texture = texture

        self.scene = scene or render
        self.map_size = None
        self.floor = None
        self.enemy_spawnpoints = None
        self.player_spawnpoint = None

        # attempting to fix "flickering" on movement. This will soap the texture
        # tho - thus I either shouldnt make floor detailed and attach such things
        # exclusively as billboards... Or, well, search for better solution #TODO
        # this also wont solve the issue completely. But for now it will do #TODO
        # there is no mipmap for magfilter, if manual can be trusted
        self.texture.set_magfilter(SamplerState.FT_linear)
        self.texture.set_minfilter(SamplerState.FT_linear_mipmap_linear)

        # this should apply filtering on texture, to improve things a bit further
        # however, since this value depends on gpu, I cant do it right away. And
        # I have no idea where to get max supported value, thus its commented
        # #TODO
        # self.texture.set_anisotropic_degree(16)

    def generate(self, scene=None):
        """Generate map out of provided data"""
        # This is there in case we will add subnodes to render dedicated to each
        # state of map. Default is set to "render" on init
        self.scene = scene or self.scene

        self.create_floor()
        # TODO: add bool to either generate only some borders or none, to provide
        # ability to fall/kick enemies into the void. This will require addition
        # of collision node to floor, aswell as checks to ensure that entity hasnt
        # fell. Maybe basic gravity, idk
        self.add_borders()

        # TODO: it may be good idea to make these configurable
        self.enemy_spawnpoints = [
            (self.map_size[1], self.map_size[3]),
            (self.map_size[0], self.map_size[2]),
            (self.map_size[1], self.map_size[2]),
            (self.map_size[0], self.map_size[3]),
        ]

        # TODO: make this configurable aswell. For now its just center of map
        self.player_spawnpoint = 0, 0, shared.game_data.entity_layer

    def create_floor(self):
        """Generate flat floor of size, provided to class"""
        # todo: add fallback values in case size hasnt been specified
        log.debug(f"Generating the floor")

        # Determining how much full textures we can fit in provided sizes
        repeats_x = int(self.size_x / self.texture.get_orig_file_x_size())
        repeats_y = int(self.size_y / self.texture.get_orig_file_y_size())

        # Adjusting map size, to ensure it fits floor's texture perfectly
        self.size_x = repeats_x * self.texture.get_orig_file_x_size()
        self.size_y = repeats_y * self.texture.get_orig_file_y_size()

        self.map_size = (
            -self.size_x / 2,
            self.size_x / 2,
            -self.size_y / 2,
            self.size_y / 2,
        )

        # initializing new cardmaker object
        # which is essentially our go-to way to create flat models
        floor_card = CardMaker("floor")
        floor_card.set_frame(self.map_size)

        # attaching card to render and creating it's object
        floor_object = self.scene.attach_new_node(floor_card.generate())
        floor_object.set_texture(self.texture)
        # repeating texture to avoid stretching when possible
        floor_object.set_tex_scale(TextureStage.getDefault(), repeats_x, repeats_y)
        # arranging card's angle
        floor_object.look_at((0, 0, -1))
        floor_object.set_pos(0, 0, shared.game_data.floor_layer)
        self.floor = floor_object

    def add_borders(self):
        """Attach invisible walls to map's borders, to avoid falling off map"""
        log.debug("Adding invisible walls to collide with on map's borders")
        wall_coordinates = [
            ((self.map_size[0], 0, 0), (self.map_size[1], 0, 0)),
            ((-self.map_size[0], 0, 0), (-self.map_size[1], 0, 0)),
            ((0, self.map_size[2], 0), (0, self.map_size[3], 0)),
            ((0, -self.map_size[2], 0), (0, -self.map_size[3], 0)),
        ]

        for sizes in wall_coordinates:
            wall_node = CollisionNode("wall")
            # it looks like without adding node to pusher (we dont need that there),
            # masks wont work. Thus for now I wont use them, as defaults seem to work
            # wall_node.set_collide_mask(BitMask32(shared.WALLS_COLLISION_MASK))
            wall_node.add_solid(CollisionPlane(Plane(*sizes)))
            wall = self.scene.attach_new_node(wall_node)

            # adding tag with wall's coordinations, so it will be possible to
            # push entities back if these collide with wall
            # because calling .get_pos() will return LPoint3f(0,0,0)
            wall_node.set_python_tag("position", sizes)

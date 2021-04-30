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
from panda3d.core import CollisionSphere, CollisionNode, BitMask32, PandaNode
import p3dss
from Game import shared

log = logging.getLogger(__name__)

class Entity2D:
    '''Main class, dedicated to creation of collideable 2D objects.'''

    def __init__(self, name: str, category: str,
                 spritesheet = None, animations = None,
                 hitbox_size: int = None, collision_mask = None,
                 sprite_size: tuple = None, scale: int = None, position = None):
        self.name = name
        log.debug(f"Initializing {self.name} object")

        self.category = category

        if not sprite_size:
            sprite_size = shared.DEFAULT_SPRITE_SIZE

        log.debug(f"{self.name}'s size has been set to {sprite_size}")

        self.category = category

        if spritesheet and animations:
            self.animation = p3dss.SpritesheetObject(name, spritesheet,
                                                      animations, sprite_size)
            self.node = self.animation.node
            #legacy proxy function that turned to be kind of nicer way to
            #update anims, than calling for switch manually
            self.change_animation = self.animation.switch

        else:
            #if we didnt get valid sprite data - create placeholder invisible
            #node to attach hitbox and other stuff to
            placeholder_node = PandaNode(name)
            self.node = render.attach_new_node(placeholder_node)

            #dummy placeholder to avoid breakage in case some object tried to
            #load invalid spritesheet and then toggle its anims
            def placeholder_anim_changer(action):
                pass

            self.change_animation = placeholder_anim_changer

        #if no position has been received - wont set it up
        if position:
            self.node.set_pos(*position)

        #setting character's collisions
        entity_collider = CollisionNode(self.category)

        #if no collision mask has been received - using defaults
        if collision_mask:
            entity_collider.set_from_collide_mask(BitMask32(collision_mask))
            entity_collider.set_into_collide_mask(BitMask32(collision_mask))

        #TODO: move this to be under character's legs
        #right now its centered on character's center
        if hitbox_size:
            self.hitbox_size = hitbox_size
        else:
            #coz its sphere and not oval - it doesnt matter if we use x or y
            #but, for sake of convenience - we are going for size_y
            self.hitbox_size = (sprite_size[1]/2)

        entity_collider.add_solid(CollisionSphere(0, 0, 0, self.hitbox_size))
        self.collision = self.node.attach_new_node(entity_collider)

        if scale:
            self.node.set_scale(scale)

        #death status, that may be usefull during cleanup
        self.dead = False

        #attaching python tags to node, so these will be accessible during
        #collision events and similar stuff
        self.node.set_python_tag("name", self.name)
        self.node.set_python_tag("category", self.category)

        #I thought to put ctrav there, but for whatever reason it glitched projectile
        #to fly into left wall. So I moved it to Creature subclass

        #debug function to show collisions all time
        if shared.SHOW_COLLISIONS:
           self.collision.show()

    def die(self):
        '''Function that should be triggered when entity is about to die'''
        self.collision.remove_node()
        self.dead = True
        log.debug(f"{self.name} is now dead")


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
from Game import entity2d, shared

log = logging.getLogger(__name__)

#module for 2d projectiles

PLAYER_PROJECTILE_COLLISION_MASK = 0X09
CATEGORY = shared.PLAYER_PROJECTILE_CATEGORY

HIT_SCORE = 10
KILL_SCORE = 15

class Projectile(entity2d.Entity2D):
    '''Subclass of Entity2D, dedicated to creation of collideable effects'''
    def __init__(self, name, direction, damage = 0, object_size = None,
                 spritesheet = None, sprite_size = None, hitbox_size = None,
                 collision_mask = None, position = None, animations_speed = None):
        #for now we are only adding these to player, so no need for other masks
        #todo: split this thing into 2 subclasses: for player's and enemy's stuff
        collision_mask = PLAYER_PROJECTILE_COLLISION_MASK
        category = CATEGORY
        super().__init__(name, category, spritesheet, sprite_size, hitbox_size,
                         collision_mask, position, animations_speed)

        self.damage = damage
        self.object.set_python_tag("damage", self.damage)
        self.current_animation = 'default'
        #todo: make this configurable from dictionary, idk
        self.lifetime = 0.1
        self.dead = False

        #Idk about numbers. These work if caster is player, but what s about enemies?
        one, two, _ = direction
        self.object.look_at(one, two, 1)

        if object_size:
            self.object.set_scale(object_size)

        #schedulging projectile to die in self.lifetime seconds after spawn
        #I've heard this is not the best way to do that, coz do_method_later does
        #things based on frames and not real time. But for now it will do
        base.task_mgr.do_method_later(self.lifetime, self.die, "remove projectile")

    def die(self, event):
        super().die()
        return

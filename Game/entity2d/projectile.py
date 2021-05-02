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

#PLAYER_PROJECTILE_COLLISION_MASK = 0X09
#ENEMY_PROJECTILE_COLLISION_MASK = 0X04
PLAYER_PROJECTILE_COLLISION_MASK = 0X09
ENEMY_PROJECTILE_COLLISION_MASK = 0X04

class Projectile(entity2d.Entity2D):
    '''Subclass of Entity2D, dedicated to creation of collideable effects'''
    def __init__(self, name:str, category:str, position, damage = 0,
                 effects = None, scale = 0, hitbox_size = 0, target = None, #speed = 0,
                 lifetime = 0, direction = None, scale_modifier = None, angle = 0,
                 die_on_object_collision:bool = False,
                 die_on_creature_collision:bool = False):
        self.name = name

        if category == shared.PLAYER_PROJECTILE_CATEGORY:
            collision_mask = PLAYER_PROJECTILE_COLLISION_MASK
        elif category == shared.ENEMY_PROJECTILE_CATEGORY:
            collision_mask = ENEMY_PROJECTILE_COLLISION_MASK
        else:
            #this shouldnt happen, but just in case
            collision_mask = None

        #just like with other entities - no safety checks for now, will explode
        #on invalid name
        data = base.assets.projectiles[name]

        #its probably possible to do this in less ugly way, but whatever
        assets = data.get('Assets', None)
        if assets:
            spritesheet = data['Assets'].get('sprite', None)
            animations = data.get('Animations', None)
        else:
            spritesheet = None
            animations = None

        #doing it like that, coz default value from projectile's config can be
        #overriden on init. Say, by skill's values
        projectile_hitbox = hitbox_size or data['Main'].get('hitbox_size', 0)

        projectile_scale = scale or data['Main'].get('scale', 1)
        #scale modifier is variable that tweaks raw scale value. Say, if we want
        #to adjust default scale to match some other entity
        if scale_modifier:
            projectile_scale = projectile_scale*scale_modifier

        #idk about this. Really. It will most likely break with introduction of
        #new skill's projectile behaviours and need rework. Like, idk - add bool
        #to init with "keep_distance: True/False" or something
        if direction:
            self.direction = direction
            #setting projectile to already spawn with directional offset, because
            #otherwise all the direction tracking will do no good on movement
            position = position + self.direction
        else:
            self.direction = 0

        super().__init__(name = name,
                         category = category,
                         #spritesheet = base.assets.sprite[spritesheet],
                         spritesheet = base.assets.sprite.get(spritesheet, None),
                         animations = animations,
                         hitbox_size = projectile_hitbox,
                         collision_mask = collision_mask,
                         #sprite_size = sprite_size,
                         scale = projectile_scale,
                         position = position)

        #optionally enabling billboard effect for projectile, in case it has such
        #setting in config. I could probably pass it to entity2d directly, idk
        if data['Main'].get('billboard', False):
            self.node.set_billboard_point_eye()
        else:
            #idk about numbers and if it will explode on weird map angles, but
            #for now it kinda works. Dropped it there, coz if its used together
            #with billboard, node will never face camera like its invisible
            one, two, _ = position
            self.node.look_at(one, two, 1)

        #due to addition of placeholder function that successfully does nothing
        #in case anim doesnt exist, its not necessary anymore to check for
        #existance of spriteseet and animations in order to cast this function
        self.change_animation('default')

        self.damage = damage
        self.node.set_python_tag("damage", self.damage)
        if effects:
            self.effects = effects
            self.node.set_python_tag("effects", self.effects)
        self.dead = False

        default_angle = data['Main'].get('angle', 0)
        #this will look kinda weird on projectiles with billboard, but for now
        #Im not fixing it, because Im unsure of how it should work. #TODO
        if angle or default_angle:
            angle += default_angle
            #rotating projectile around 2d axis to match the shooting angle
            #I have no idea how if it will work for enemies tho
            self.node.set_r(angle)

        if lifetime:
            self.lifetime = lifetime
            #schedulging projectile to die in self.lifetime seconds after spawn
            base.task_mgr.add(self.dying_task,
                            f"dying task of projectile {self.name}")

        #its probably possible to do it in less ugly way
        if die_on_object_collision or die_on_creature_collision:
            #coz there is no point in traversing projectile itself otherwise
            base.cTrav.add_collider(self.collision, base.chandler)
            self.node.set_python_tag("die_command", self.die)

        if die_on_creature_collision:
            self.node.set_python_tag("die_on_creature_collision", True)

        if die_on_object_collision:
            self.node.set_python_tag("die_on_object_collision", True)

    def dying_task(self, event):
        #ensuring that projectile didnt die already
        if self.dead or not self.node:
            return

        dt = globalClock.get_dt()
        self.lifetime -= dt

        if self.lifetime > 0:
            return event.cont

        self.die()
        #super().die()
        #moved it there, because death of creature required it
        #self.node.remove_node()
        return

    def die(self):
        super().die()

        #TODO: add ability to play death animation and only then remove node
        #Right now its impossible, because we dont know the exact lengh of that
        #anim. Maybe I should add something like optional "length" setting into
        #projectile's config file?

        self.node.remove_node()
        #self.dying_task(0)

class ChasingProjectile(Projectile):
    '''Projectile that always follows its target. Aside from usual projectile's
    stuff, receive "target" variable, which should be NodePath'''
    def __init__(self, name:str, category:str, position, target, damage = 0,
                 effects = None, scale = 0, hitbox_size = 0, speed = 0,
                 lifetime = 0, direction = None, scale_modifier = None, angle = 0,
                 die_on_object_collision:bool = False,
                 die_on_creature_collision:bool = False):

        self.target = target
        if speed:
            self.speed = speed
        else:
            self.speed = 1

        super().__init__(name = name,
                         category = category,
                         position = position,
                         damage = damage,
                         effects = effects,
                         scale = scale,
                         hitbox_size = hitbox_size,
                         #I dont think speed should be there
                         #speed = speed
                         lifetime = lifetime,
                         direction = direction,
                         scale_modifier = scale_modifier,
                         angle = angle,
                         die_on_object_collision = die_on_object_collision,
                         die_on_creature_collision = die_on_creature_collision)

        base.task_mgr.add(self.follow_task, f"following task of {self.name}")

    def follow_task(self, event):
        '''Taskmanager task that make projectile follow the target'''
        if self.dead or not self.node or not self.target:
            return

        projectile_position = self.node.get_pos()

        vector_to_target = (self.target.get_pos() + self.direction) - projectile_position
        vector_to_target.normalize()

        #workaround to ensure node will its stay on its original layer
        vxy = vector_to_target.get_xy()
        new_pos = projectile_position + (vxy*self.speed, 0)

        self.node.set_pos(new_pos)
        return event.cont

class MovingProjectile(Projectile):
    '''Projectile that moves into specified direction with provided speed'''
    def __init__(self, name:str, category:str, position, direction, speed,
                 damage = 0, effects = None, scale = 0, hitbox_size = 0,
                 lifetime = 0, scale_modifier = None, angle = 0,
                 die_on_object_collision:bool = False,
                 die_on_creature_collision:bool = False):

        #I could probably move direction there too, since its mandatory anyway
        self.speed = speed

        super().__init__(name = name,
                         category = category,
                         position = position,
                         damage = damage,
                         effects = effects,
                         scale = scale,
                         hitbox_size = hitbox_size,
                         #I dont think speed should be there
                         #speed = speed
                         lifetime = lifetime,
                         direction = direction,
                         scale_modifier = scale_modifier,
                         angle = angle,
                         die_on_object_collision = die_on_object_collision,
                         die_on_creature_collision = die_on_creature_collision)

        #normalizing direction, to fix issue with projectile moving too fast
        #It has to be done after init, coz original direction is needed there
        self.direction.normalize()

        base.task_mgr.add(self.move_task, f"moving task of {self.name}")

    def move_task(self, event):
        '''Taskmanager task that make projectile fly in specified direction'''
        if self.dead or not self.node:
            return

        new_position = self.node.get_pos() + self.direction*self.speed

        self.node.set_pos(new_position)
        return event.cont

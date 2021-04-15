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
from panda3d.core import CollisionSphere, CollisionNode, BitMask32
from Game import shared, spritesheet_cutter, animation, skill

log = logging.getLogger(__name__)

#module with general classes used as parents for 2d entity objects

class Entity2D:
    '''Main class, dedicated to creation of collideable 2D objects.'''

    def __init__(self, name: str, category: str, spritesheet, animations,
                 hitbox_size: int = None, collision_mask = None,
                 sprite_size: tuple = None, position = None):
        self.name = name
        log.debug(f"Initializing {self.name} object")

        self.category = category

        if not sprite_size:
            sprite_size = shared.DEFAULT_SPRITE_SIZE

        log.debug(f"{self.name}'s size has been set to {sprite_size}")

        self.category = category

        self.animation = animation.AnimatedObject(name, spritesheet, animations, sprite_size)
        self.object = self.animation.object

        #if no position has been received - wont set it up
        if position:
            self.object.set_pos(*position)

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
        self.collision = self.object.attach_new_node(entity_collider)

        #death status, that may be usefull during cleanup
        self.dead = False

        #attaching python tags to object node, so these will be accessible during
        #collision events and similar stuff
        self.object.set_python_tag("name", self.name)
        self.object.set_python_tag("category", self.category)

        #I thought to put ctrav there, but for whatever reason it glitched projectile
        #to fly into left wall. So I moved it to Creature subclass

        #debug function to show collisions all time
        #if shared.SHOW_COLLISIONS:
        #   self.collision.show()

    def change_animation(self, action):
        '''Proxy function that triggers self.animation's switch. Kept there for
        backwards compatibility, also seems to be nicer way to call things'''
        self.animation.switch(action)

    def die(self):
        '''Function that should be triggered when entity is about to die'''
        self.collision.remove_node()
        self.dead = True
        log.debug(f"{self.name} is now dead")

class Creature(Entity2D):
    '''Subclass of Entity2D, dedicated to generation of player and enemies'''
    def __init__(self, name: str, category: str, spritesheet, animations: dict,
                 stats: dict, skills: list, death_sound: str = None, hitbox_size: int = None,
                 collision_mask = None, sprite_size: tuple = None, position = None):
        #Initializing all the stuff from parent class'es init to be done
        super().__init__(name, category, spritesheet, animations, hitbox_size,
                         collision_mask, sprite_size,  position)

        if death_sound and (death_sound in base.assets.sfx):
            self.death_sound = base.assets.sfx[death_sound]
        else:
            log.warning(f"{name} has no custom death sound, using fallback")
            self.death_sound = base.assets.sfx['default_death']

        self.direction = 'right'
        self.change_animation(f'idle_{self.direction}')
        #its .copy() coz otherwise we will link to dictionary itself, which will
        #cause any change to stats of one enemy to affect every other enemy
        self.stats = stats.copy()

        #list with timed status effects. When any of these reach 0 - they get ignored
        self.status_effects = {}

        self.object.set_python_tag("stats", self.stats)
        self.object.set_python_tag("get_damage", self.get_damage)

        #shenanigans for skills
        self.object.set_python_tag("dead", self.dead)
        self.object.set_python_tag("direction", self.direction)
        self.object.set_python_tag("change_animation", self.change_animation)
        #self.using_skill = False
        #setting it like that, because there doesnt seem to be the way to update
        #variable linked to tag - only to override it. Or maybe I didnt find it
        self.object.set_python_tag("using_skill", False)
        self.object.set_python_tag("status_effects", self.status_effects)

        if skills:
            #I should probably rework this into list or idk
            entity_skills = {}
            for item in skills:
                if item in base.assets.skills:
                    skill_instance = skill.Skill(item, self.object)
                    entity_skills[item] = skill_instance
            self.skills = entity_skills
        else:
            self.skills = None

        #attaching our object's collisions to traverser
        #otherwise they wont be detected
        base.cTrav.add_collider(self.collision, base.chandler)

        #billboard is effect to ensure that object always face camera the same
        #e.g this is the key to achieve that "2.5D style" I aim for
        self.object.set_billboard_point_eye()

        base.task_mgr.add(self.status_effects_handler, "status effects handler")

        #used to avoid issue with getting multiple damage func calls per frame
        #see game_window's damage functions
        self.last_collision_time = 0
        self.object.set_python_tag("last_collision_time", self.last_collision_time)

        #proxifying self.apply_effect, so it will be possible for skills and
        #projectiles to trigger this function
        self.object.set_python_tag("apply_effect", self.apply_effect)

    def status_effects_handler(self, event):
        '''Meant to run as taskmanager routine. Each frame, reduce lengh of active
        status effects. When it reaches 0 - remove status effect'''
        if not self.status_effects:
            return event.cont

        #removing the task from being called again if target is already dead
        if self.dead:
            return

        dt = globalClock.get_dt()
        #copying to avoid causing issues by changing dic size during for loop
        se = self.status_effects.copy()
        for effect in se:
            self.status_effects[effect] -= dt
            if self.status_effects[effect] <= 0:
                del self.status_effects[effect]
                log.debug(f"{effect} effect has expired on {self.name}")

        return event.cont

    def apply_effect(self, effect: str, length):
        '''Apply provided effect to creature'''
        #there is probably a better way to do this
        if effect in self.status_effects:
            self.status_effects[effect] += length
        else:
            self.status_effects[effect] = length

        log.info(f"{self.name} has got {effect} for {length} seconds")

    def get_damage(self, amount: int = None, effects = None):
        '''Whatever stuff procs when target is about to get hurt'''
        #not getting any damage in case we are invulnerable
        if 'immortal' in self.status_effects:
            return

        #for now I've found it to be the most flexible way to apply any effects
        #to entity. But I may be wrong
        if effects:
            for effect, length in vars(effects).items():
                self.apply_effect(effect, length)

        #this is probably not right, but right now I find it correct
        if not amount:
            return

        self.stats['hp'] -= amount
        log.debug(f"{self.name} has received {amount} damage "
                  f"and is now on {self.stats['hp']} hp")

        if self.stats['hp'] <= 0:
            self.die()
            return

        #this is placeholder. May need to track target's name in future to play
        #different damage sounds
        base.assets.sfx['damage'].play()

        #disabled it, coz its broken if entity dont get stunned. Will replace with
        #color scale, once I will figure out how to apply whiteness (since out of
        #box its only possible to change color's rgba values down to darkness
        #self.change_animation(f"hurt_{self.direction}")
        #self.object.set_color_scale(0.9, 0.9, 0.9, 1)
        #self.object.set_color(0, 0, 0, 1)

    def die(self):
        super().die()
        #Death of creature is a bit different than death of other entities, because
        #we dont remove object node itself right away, but keep it to rot. And
        #then, with some additional taskmanager task, clean things up
        self.change_animation(f'dying_{self.direction}')

        self.death_sound.play()

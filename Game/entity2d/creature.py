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
from direct.interval.LerpInterval import LerpColorScaleInterval
from direct.interval.IntervalGlobal import Sequence, Func, Wait
from Game import entity2d, skill

log = logging.getLogger(__name__)

LOOK_RIGHT = 0
LOOK_LEFT = 180

class Creature(entity2d.Entity2D):
    '''Subclass of Entity2D, dedicated to generation of player and enemies'''
    def __init__(self, name: str, category: str, spritesheet, animations: dict,
                 stats: dict, skills: list, death_sound: str = None, hitbox_size: int = None,
                 collision_mask = None, sprite_size: tuple = None, scale = None, position = None):
        #Initializing all the stuff from parent class'es init to be done
        super().__init__(name, category, spritesheet, animations, hitbox_size,
                         collision_mask, sprite_size, scale, position)

        #magic that allows for rotating node around its h without making it look
        #invisible. Idk why its not enabled by default - guess its to save some
        #resources, thus Im doing it there and not during base entity2d init
        self.object.set_two_sided(True)

        if death_sound and (death_sound in base.assets.sfx):
            self.death_sound = base.assets.sfx[death_sound]
        else:
            log.warning(f"{name} has no custom death sound, using fallback")
            self.death_sound = base.assets.sfx['default_death']

        self.direction = 'right'
        self.change_animation('idle')
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

        #default rgba values. Saved on init, used in blinking
        self.default_colorscheme = self.object.get_color_scale()

    def change_direction(self, direction):
        '''Change direction, creature face, in case it didnt face this way already'''
        if direction != self.direction:
            if direction == "right":
                self.object.set_h(LOOK_RIGHT)
            else:
                self.object.set_h(LOOK_LEFT)
            self.direction = direction
            log.debug(f"{self.name} is now facing {self.direction}")

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

        #self.blink(rgba = (0.1, 0.1, 0.1, 1), length = 0.5)
        #self.blink(rgba = (0.1, 0.1, 0.1, 1), length = 0.5, fade_in = True)
        self.blink(rgba = (0.1, 0.1, 0.1, 1), length = 0.5, fade_out = True)
        #self.blink(rgba = (0.1, 0.1, 0.1, 1), length = 0.5,
                            #fade_in = True, fade_out = True)

        #this is placeholder. May need to track target's name in future to play
        #different damage sounds
        base.assets.sfx['damage'].play()

    def blink(self, rgba: tuple, length, fade_in: bool = False, fade_out: bool = False):
        '''Make creature blink with provided rgba color for length amount of time.
        Can be usefull to highlight various effects - getting healed, damage, etc'''

        # TODO: add ability to set not just rgba, but also lightness
        #right now its only possible to make object blink in darker shades, which
        #is done by mixing rgb values. Its not possible to make object blink in
        #white tones, which is one of (together with red) default ways to highlight
        #getting damage with color in these types of games

        if (rgba == self.default_colorscheme) or length <= 0:
            #coz it wont do anything at this point anyway
            return

        sequence = Sequence(name = f"Blinking {self.name} with color {rgba}")

        if fade_in and fade_out:
            length = length / 2

        if fade_in:
            fade_in_effect = LerpColorScaleInterval(
                                         nodePath = self.object,
                                         duration = (length),
                                         colorScale = rgba,
                                         startColorScale = self.default_colorscheme
                                         )
            sequence.append(fade_in_effect)
        else:
            sequence.append(Func(self.object.set_color_scale, rgba))

        if fade_out:
            fade_out_effect = LerpColorScaleInterval(
                                         nodePath = self.object,
                                         duration = (length),
                                         colorScale = self.default_colorscheme,
                                         startColorScale = rgba
                                         )
            sequence.append(fade_out_effect)
        else:
            if not fade_in:
                sequence.append(Wait(length))
            sequence.append(Func(self.object.set_color_scale,
                                 self.default_colorscheme))

        sequence.start()

    def die(self):
        super().die()
        #Death of creature is a bit different than death of other entities, because
        #we dont remove object node itself right away, but keep it to rot. And
        #then, with some additional taskmanager task, clean things up
        #self.change_animation(f'dying_{self.direction}')
        self.change_animation(f'dying')

        self.death_sound.play()

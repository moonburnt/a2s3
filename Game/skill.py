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

# Module where Im trying to implement entity-independant skills, configurable
# from toml files. Very WIP, grep for '#TODO's

import logging
from Game import entity2d, shared

log = logging.getLogger(__name__)

class Skill:
    '''Class dedicated to entity-independant skills'''
    def __init__(self, name:str, caster):
        #Name of skill
        self.name = name

        #Whoever casts the skill. Based on this, we should eventually calculate
        #skill's position, skill category, damage and other stuff. Well, actually
        #we should probably provide other vars for that, but for now, since I have
        #no idea how to design this whole class yet, Im sticking to that
        self.caster = caster
        self.caster_stats = self.caster.get_python_tag("stats")

        #No safety checks rn, will crash if skill has no config file
        data = base.assets.skills[self.name]
        main = data['Main']

        #data storage class, which we will instance and attach optional variables to
        class Storage:
            pass

        #whatever data we can get from configuration file
        self.caster_animation = main.get('caster_animation', None)

        #Commented out, since its not supported yet. #TODO
        #self.caster_animation_speed = main.get('caster_animation_speed', 0)

        #Amount of time, caster will be enforced to play self.caster_animation
        #(if not None and unless got damage) and be unable to cast any other skills
        self.cast_time = main.get('cast_time', 0)

        #Well, skill's cooldown
        self.cooldown = main.get('cooldown', 0)

        #Projectile spawned by skill, in case skill has that thing
        projectile_data = data.get('Projectile', None)
        if projectile_data and projectile_data.get('name', None):
            self.projectile = Storage()
            self.projectile.name = projectile_data['name']
        else:
            self.projectile = None

        if 'Effects' in data:
            effects = data['Effects']
        else:
            effects = None

        if self.projectile:
            #stuff below is located there, because for the time being it makes
            #no sense to load it if skill has no projectiles attached to it, as
            #these only affect projectile
            self.projectile.scale = projectile_data.get('scale', 0)
            self.projectile.hitbox = projectile_data.get('hitbox', 0)
            self.projectile.lifetime = projectile_data.get('lifetime', 0)
            self.projectile.knockback = projectile_data.get('knockback', 0)
            self.projectile.spawn_offset = projectile_data.get('spawn_offset', 0)
            self.projectile.die_on_object_collision = projectile_data.get('die_on_object_collision', False)
            self.projectile.die_on_creature_collision = projectile_data.get('die_on_creature_collision', False)
            #max is there to ensure that no negative ricochet values can be attached
            self.projectile.ricochets_amount = max(0, projectile_data.get('ricochets_amount', 0))

            self.projectile.behavior = projectile_data.get('behavior', None)
            #specify whatever correct variables there, except for "stationary",
            #because stationary projectile doesnt move anywhere
            if self.projectile.behavior == "follow_caster":
                self.projectile.target = self.caster
                #setting it there coz it should follow the caster with caster's spd
                self.projectile.speed = self.caster_stats.get('mov_spd', 0)
            else:
                self.projectile.target = None
                self.projectile.speed = projectile_data.get('speed', 0)

            if (projectile_data.get('scale_with_caster', False) and
                                         self.caster.get_scale() != 1):
                self.projectile.scale_modifier = self.caster.get_scale()[0]
            else:
                self.projectile.scale_modifier = 0

            caster_category = self.caster.get_python_tag("category")

            if caster_category == shared.PLAYER_CATEGORY:
                self.projectile.category = shared.PLAYER_PROJECTILE_CATEGORY
            else:
                self.projectile.category = shared.ENEMY_PROJECTILE_CATEGORY

            #Idk about current format, but Im trying to make it easy to use below
            #without need to store useless variables in memory
            if 'Stats' in data:
                self.stats = Storage()
                dstats = data['Stats']

                dmg = dstats.get('dmg', 0)
                dmg_multiplier = dstats.get('dmg_multiplier', 0)
                if dmg or dmg_multiplier:
                    self.stats.dmg = Storage()
                    self.stats.dmg.value = dmg
                    self.stats.dmg.multiplier = dmg_multiplier
                else:
                    self.stats.dmg = None
            else:
                self.stats = None

            if effects and 'target' in effects:
                dteffects = effects['target']
                self.target_effects = Storage()

                self.target_effects.stun = dteffects.get('stun', 0)
            else:
                self.target_effects = None

        if effects and 'caster' in effects:
            dceffects = effects['caster']
            self.caster_effects = Storage()

            self.caster_effects.stun = dceffects.get('stun', 0)
        else:
            self.caster_effects = None

        #This is a timer variable, that resets to self.cooldown when it reach 0
        if self.cooldown:
            self.current_cooldown = 0

        #Same as above, but for self.cast_time
        if self.cast_time:
            self.current_cast_time = 0

        #Based on this, we determine if skill can be casted right now or not
        #idk if I can get rid of it
        self.used = False

    def calculate_stat(self, stat_name:str):
        '''Calculates, how much of provided stat skill will pass to projectile,
        based on (stat+self.caster_stats['stat'])*multiplier'''
        if self.stats and getattr(self.stats, stat_name, None):
            stat = getattr(self.stats, stat_name)
            caster_stat = self.caster_stats.get(stat_name, 0)
            calculated_stat = (stat.value + caster_stat) * stat.multiplier

            return calculated_stat
        else:

            return 0

    def cast(self, position = None, direction = None, angle = None):
        '''Casts the skill'''
        #TODO: maybe configure position and angle automatically, based on caster?

        #if self.caster.get_python_tag("using_skill") or self.used:
        if self.used or self.caster.get_python_tag("using_skill"):
            return

        log.info(f"{self.caster} casts skill {self.name}")

        if self.cast_time:
            self.caster.set_python_tag("using_skill", True)
            self.current_cast_time = self.cast_time
            base.task_mgr.add(self.cast_time_handler,
                            f"cast time handler of {self.caster}'s {self.name} skill")

        if self.caster_animation:
            #since custom values for animation playback arent implemented yet,
            #not worrying about speed at all
            #if self.caster_speed =
            change_func = self.caster.get_python_tag("change_animation")
            change_func(self.caster_animation)

        if self.caster_effects:
            # and self.buff_caster:
            #This may not look like it, but it actually applies custom values
            buff_caster = self.caster.get_python_tag("apply_effect")

            if self.caster_effects.stun:
                #caster_effects['stun'] = self.caster_effects.stun
                #print('stun', self.caster_effects.stun, self.buff_caster)
                buff_caster('stun', self.caster_effects.stun)


        if self.cooldown:
            #there is no point to flip this switch if skill has no cd, I think
            self.used = True
            self.current_cooldown = self.cooldown
            #and there is no point to reset cd if it equals 0 since start
            base.task_mgr.add(self.cooldown_handler,
                            f"cooldown handler of {self.caster}'s {self.name} skill")

        if self.projectile:
            #there is no point to do manual safety check anymore, coz I moved it
            #to the calculation function itself
            dmg = self.calculate_stat('dmg')

            if not position:
                position = self.caster.get_pos()

            #I could just import offsets with 1 being replacement value in case
            #its not set, but I thought this will be better
            if self.projectile.spawn_offset:
                direction = direction * self.projectile.spawn_offset

            #TODO: add ability to pass knockbass to projectile

            #if self.projectile.target:
            if self.projectile.behavior == "follow_caster":
                projectile = entity2d.ChasingProjectile(
                    name = self.projectile.name,
                    #this will explode on None, but it
                    #shouldnt happen... I guess
                    category = self.projectile.category,
                    position = position,
                    target = self.projectile.target,
                    #this shouldnt do anything on None or 0
                    direction = direction,
                    scale = self.projectile.scale,
                    damage = dmg,
                    #same for all of these
                    hitbox_size = self.projectile.hitbox,
                    lifetime = self.projectile.lifetime,
                    effects = self.target_effects,
                    scale_modifier = self.projectile.scale_modifier,
                    speed = self.projectile.speed,
                    angle = angle,
                    die_on_object_collision = self.projectile.die_on_object_collision,
                    die_on_creature_collision = self.projectile.die_on_creature_collision,
                    )

            elif self.projectile.behavior == "move_towards_direction":
                projectile = entity2d.MovingProjectile(
                    name = self.projectile.name,
                    category = self.projectile.category,
                    position = position,
                    direction = direction,
                    speed = self.projectile.speed,
                    scale = self.projectile.scale,
                    damage = dmg,
                    hitbox_size = self.projectile.hitbox,
                    lifetime = self.projectile.lifetime,
                    effects = self.target_effects,
                    scale_modifier = self.projectile.scale_modifier,
                    angle = angle,
                    die_on_object_collision = self.projectile.die_on_object_collision,
                    die_on_creature_collision = self.projectile.die_on_creature_collision,
                    ricochets_amount = self.projectile.ricochets_amount,
                    )
            else:
                projectile = entity2d.Projectile(
                    name = self.projectile.name,
                    category = self.projectile.category,
                    position = position,
                    direction = direction,
                    scale = self.projectile.scale,
                    damage = dmg,
                    hitbox_size = self.projectile.hitbox,
                    lifetime = self.projectile.lifetime,
                    effects = self.target_effects,
                    scale_modifier = self.projectile.scale_modifier,
                    angle = angle,
                    die_on_object_collision = self.projectile.die_on_object_collision,
                    die_on_creature_collision = self.projectile.die_on_creature_collision,
                    )

            #maybe I should attach it to skill itself instead? or to caster? and
            #destroy together? Hmmm.... #TODO
            base.level.projectiles.append(projectile)

    def cast_time_handler(self, event):
        '''Same as cooldown handler, but for self.cast_time'''
        #safety check that disables routine if caster has died
        #if not self.caster or self.caster.dead:
        if not self.caster or self.caster.get_python_tag("dead"):
            return

        dt = globalClock.get_dt()

        self.current_cast_time -= dt
        if self.current_cast_time <= 0:
            self.current_cast_time = 0
            self.caster.set_python_tag("using_skill", False)
            return

        return event.cont

    def cooldown_handler(self, event):
        '''Intended to be used as taskmanager routine, triggered on skill's cast.
        If self.cooldown > 0, count self.current_cooldown to 0, then reset it
        back to self.current_cooldown = self.cooldown, making skill available to
        re-cast again'''

        #safety check that disables routine if caster has died
        #if not self.caster or self.caster.dead:
        if not self.caster or self.caster.get_python_tag("dead"):
            return

        dt = globalClock.get_dt()

        self.current_cooldown -= dt
        if self.current_cooldown <= 0:
            self.used = False
            self.current_cooldown = 0
            #self.current_cooldown = self.default_cooldown
            return

        return event.cont

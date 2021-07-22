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
from panda3d.core import Vec3, NodePath
import p3dss
from random import randint
from Game import entity2d, skill, shared

log = logging.getLogger(__name__)

# silencing p3dss logger from printing everything below ERROR level, coz otherwise
# it will return too much warnings, related to missing head's animations
p3dss_logger = logging.getLogger("p3dss")
p3dss_logger.setLevel(logging.ERROR)

MINIMUM_ALLOWED_DAMAGE = 1
DODGE_CHANCE_RANGE = (0, 100)
MAX_DODGE_CHANCE = 75
HEAD_HEIGHT = 0.2  # relatively to player height, not scene


class Creature(entity2d.Entity2D):
    """Subclass of Entity2D, dedicated to generation of player and enemies"""

    def __init__(
        self, name: str, category: str, data: dict, collision_mask=None, scale=None
    ):

        # First, lets extract all data unified for all creatures from our dict.
        # Safety checks are all over the place - some instances are secured, others
        # will cause crash on invalid/non-existing data
        stats = data["Stats"]
        skills = data["Main"].get("skills", None)
        hitbox_size = data["Main"].get("hitbox_size", None)

        if data.get("Assets", None):
            head = data["Assets"].get("head", None)
            if head:
                default_head = data["Assets"].get("default_head", None)
                # there should be parsing of head config
                head_data = shared.assets.heads.get(head, None)
            else:
                head_data = None

            body = data["Assets"].get("body", None)
            if body and (body in shared.assets.bodies):
                body_data = shared.assets.bodies[body]
                # not checking if "main" exists, coz it should be already filtered
                # out by assets loader
                bspritesheet_name = body_data["Main"].get("spritesheet", None)
                if bspritesheet_name and (bspritesheet_name in shared.assets.sprite):
                    bspritesheet = shared.assets.sprite[bspritesheet_name]
                    # idk if this will break at some point
                    sprite_size = body_data["Main"].get("size", None)
                    animations = body_data.get("Animations", None)
                else:
                    bspritesheet = (None,)
                    animations = (None,)
                    sprite_size = None
            else:
                bspritesheet = (None,)
                animations = (None,)
                sprite_size = None

            if data["Assets"].get("Sounds", None):
                death_sound = data["Assets"]["Sounds"].get("death", None)
            else:
                death_sound = None
        else:
            bspritesheet = (None,)
            animations = (None,)
            sprite_size = (None,)
            death_sound = None

        parts = []

        if bspritesheet and animations:
            body = p3dss.SpritesheetObject(
                name=f"{name}_body",
                spritesheet=bspritesheet,
                sprites=animations,
                sprite_size=sprite_size or shared.game_data.sprite_size,
                parent=NodePath(),
            )
            parts.append(entity2d.VisualsNode(body, (0, 0, 0), 0.0, 0, False))

        # placeholder code that implements support for attachable heads
        # not really efficient, I should probably do it somewhere else
        # its func coz vars overlapped with other init stuff
        if (
            head_data
            and head_data["Main"].get("spritesheet", None)
            and (head_data["Main"]["spritesheet"] in shared.assets.sprite)
            and head_data.get("Animations")
        ):
            # if no head has been set to start with, or head doesnt exist - setting
            # up the very first one to be shown instead
            starting_head = default_head or head_data["Main"].get("default_head", None)
            if starting_head and head_data["Animations"].get(starting_head, None):
                sprites = head_data["Animations"][starting_head]
            else:
                head_name = list(head_data["Animations"].keys())[0]
                sprites = head_data["Animations"][head_name]

            default_action = list(sprites.keys())[0]
            # if default action's sprite isnt single - it should be tuple or list
            if isinstance(sprites[default_action]["sprites"], int):
                default_sprite = sprites[default_action]["sprites"]
            else:
                default_sprite = sprites[default_action]["sprites"][0]

            hspritesheet_name = head_data["Main"]["spritesheet"]
            hspritesheet = shared.assets.sprite[hspritesheet_name]

            head = p3dss.SpritesheetObject(
                name=f"{name}_head",
                spritesheet=hspritesheet,
                sprites=sprites,
                sprite_size=(
                    head_data["Main"].get("size", None) or shared.game_data.sprite_size
                ),
                default_sprite=default_sprite,
                parent=NodePath(),
                default_action=default_action,
            )

            # Depending on values, sprite may render slightly different.
            # Been told that it happens because of lack of antialiasing #TODO
            # self.head.node.set_pos(0.2, 0, 5)
            position = tuple(head_data["Main"].get("position", (0, 0, 0)))
            parts.append(entity2d.VisualsNode(head, position, HEAD_HEIGHT, 0, True))

        # Initializing all the stuff from parent class'es init to be done
        super().__init__(
            name=name,
            category=category,
            hitbox_size=hitbox_size,
            collision_mask=collision_mask,
            scale=scale,
            animated_parts=parts,
        )

        if death_sound and (death_sound in shared.assets.sfx):
            self.death_sound = shared.assets.sfx[death_sound]
        else:
            log.warning(f"{name} has no custom death sound, using fallback")
            self.death_sound = shared.assets.sfx["default_death"]

        self.change_animation("idle")
        # its .copy() coz otherwise we will link to dictionary itself, which will
        # cause any change to stats of one enemy to affect every other enemy
        self.stats = stats.copy()

        # list with timed status effects. When any of these reach 0 - they get ignored
        self.status_effects = {}

        self.node.set_python_tag("stats", self.stats)
        self.node.set_python_tag("get_damage", self.get_damage)

        # shenanigans for skills
        self.node.set_python_tag("dead", self.dead)
        self.node.set_python_tag("direction", self.direction)
        self.node.set_python_tag("change_animation", self.change_animation)
        # self.using_skill = False
        # setting it like that, because there doesnt seem to be the way to update
        # variable linked to tag - only to override it. Or maybe I didnt find it
        self.node.set_python_tag("using_skill", False)
        self.node.set_python_tag("status_effects", self.status_effects)

        self.node.set_python_tag("mov_speed", self.stats["mov_spd"])

        if skills:
            # I should probably rework this into list or idk
            entity_skills = {}
            for item in skills:
                if item in shared.assets.skills:
                    skill_instance = skill.Skill(item, self.node)
                    entity_skills[item] = skill_instance
            self.skills = entity_skills
        else:
            self.skills = None

        # attaching our node's collisions to traverser
        # otherwise they wont be detected
        base.cTrav.add_collider(self.collision, base.chandler)

        # billboard is effect to ensure that node always face camera the same
        # e.g this is the key to achieve that "2.5D style" I aim for
        self.node.set_billboard_point_eye()

        # used to avoid issue with getting multiple damage func calls per frame
        # see game_window's damage functions
        self.last_collision_time = 0
        self.node.set_python_tag("last_collision_time", self.last_collision_time)

        # proxifying self.apply_effect, so it will be possible for skills and
        # projectiles to trigger this function
        self.node.set_python_tag("apply_effect", self.apply_effect)

        # default rgba values. Saved on init, used in blinking
        self.default_colorscheme = self.node.get_color_scale()

    def spawn(self, position):
        """Spawn entity on provided position"""
        super().spawn(position)
        base.task_mgr.add(self.status_effects_handler, "status effects handler")

    def status_effects_handler(self, event):
        """Meant to run as taskmanager routine. Each frame, reduce lengh of active
        status effects. When it reaches 0 - remove status effect"""
        if not self.status_effects:
            return event.cont

        # removing the task from being called again if target is already dead
        if self.dead:
            return

        dt = globalClock.get_dt()
        # copying to avoid causing issues by changing dic size during for loop
        se = self.status_effects.copy()
        for effect in se:
            self.status_effects[effect] -= dt
            if self.status_effects[effect] <= 0:
                del self.status_effects[effect]
                log.debug(f"{effect} effect has expired on {self.name}")

        return event.cont

    def apply_effect(self, effect: str, length):
        """Apply provided effect to creature"""
        # there is probably a better way to do this
        if effect in self.status_effects:
            self.status_effects[effect] += length
        else:
            self.status_effects[effect] = length

        log.info(f"{self.name} has got {effect} for {length} seconds")

    def get_damage(self, amount: int = 0, effects=None):
        """Whatever stuff procs when target is about to get hurt"""
        # not getting any damage in case we are invulnerable. I should probably
        # move this below effects. Or add separate stat that will check if its
        # possible to apply effects right now. #TODO
        if "immortal" in self.status_effects:
            return

        # idk if it should be there or below effects :/
        # this also doesnt check for hit chance yet. Idk if I will add that stat,
        # will see #TODO
        dodge = self.stats.get("dodge", 0)
        # ensuring that we dont have negative dodge value right now, due to debuff
        # or some other shenanigans
        if dodge > 0:
            # ensuring that chance to dodge will never be more than MAX_DODGE_CHANCE
            dodge = min(MAX_DODGE_CHANCE, dodge)
            hit_chance = randint(*DODGE_CHANCE_RANGE)
            # idk if it should be just "<" instead
            if hit_chance <= dodge:
                log.info(
                    f"{self.name} has dodged attack "
                    f"({hit_chance} hit, {dodge} dodge chance)"
                )
                return

        # for now I've found it to be the most flexible way to apply any effects
        # to entity. But I may be wrong
        if effects:
            for effect, length in vars(effects).items():
                self.apply_effect(effect, length)

        # Ensuring that in case skill casted on us is just effects spell, we wont
        # get any damage calculations done. Idk if I should move blinking above
        if not amount:
            return

        # TODO: maybe crease empty defence stat on stats import? Thus there wont
        # be need in that check
        defence = self.stats.get("defence", 0)
        # ensuring that we wont get more damage on negative def values
        if defence > 0:
            amount = amount - defence
            # ensuring that regardless of our defence we will always get at least
            # hardcoded minimum of damage
            amount = max(MINIMUM_ALLOWED_DAMAGE, amount)

        self.stats["hp"] -= amount
        log.debug(
            f"{self.name} has received {amount} damage "
            f"and is now on {self.stats['hp']} hp"
        )

        if self.stats["hp"] <= 0:
            self.die()
            return

        self.blink(rgba=(0.1, 0.1, 0.1, 1), length=0.5, fade_out=True)

        # this is placeholder. May need to track target's name in future to play
        # different damage sounds
        shared.assets.sfx["damage"].play()

    def blink(self, rgba: tuple, length, fade_in: bool = False, fade_out: bool = False):
        """Make creature blink with provided rgba color for length amount of time.
        Can be usefull to highlight various effects - getting healed, damage, etc"""

        # TODO: add ability to set not just rgba, but also lightness
        # right now its only possible to make node blink in darker shades, which
        # is done by mixing rgb values. Its not possible to make node blink in
        # white tones, which is one of (together with red) default ways to highlight
        # getting damage with color in these types of games

        if (rgba == self.default_colorscheme) or length <= 0:
            # coz it wont do anything at this point anyway
            return

        sequence = Sequence(name=f"Blinking {self.name} with color {rgba}")

        if fade_in and fade_out:
            length = length / 2

        if fade_in:
            fade_in_effect = LerpColorScaleInterval(
                nodePath=self.node,
                duration=(length),
                colorScale=rgba,
                startColorScale=self.default_colorscheme,
            )
            sequence.append(fade_in_effect)
        else:
            sequence.append(Func(self.node.set_color_scale, rgba))

        if fade_out:
            fade_out_effect = LerpColorScaleInterval(
                nodePath=self.node,
                duration=(length),
                colorScale=self.default_colorscheme,
                startColorScale=rgba,
            )
            sequence.append(fade_out_effect)
        else:
            if not fade_in:
                sequence.append(Wait(length))
            sequence.append(Func(self.node.set_color_scale, self.default_colorscheme))

        sequence.start()

    def die(self):
        super().die()

        if self.death_sound:
            self.death_sound.play()

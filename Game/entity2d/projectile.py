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

from panda3d.core import NodePath, CollisionSphere
import p3dss
from Game import entity2d, shared
import logging

log = logging.getLogger(__name__)

# module for 2d projectiles
PLAYER_PROJECTILE_COLLISION_MASK = 0x09
ENEMY_PROJECTILE_COLLISION_MASK = 0x04


class Projectile(entity2d.Entity2D):
    """Subclass of Entity2D, dedicated to creation of collideable effects"""

    def __init__(
        self,
        name: str,
        category: str,
        damage=0,
        effects=None,
        scale=0,
        hitbox_size=0,
        lifetime=0,
        scale_modifier=None,
        die_on_object_collision: bool = False,
        die_on_creature_collision: bool = False,
    ):
        self.name = name

        if category == shared.game_data.player_projectile_category:
            collision_mask = PLAYER_PROJECTILE_COLLISION_MASK
        elif category == shared.game_data.enemy_projectile_category:
            collision_mask = ENEMY_PROJECTILE_COLLISION_MASK
        else:
            # this shouldnt happen, but just in case
            collision_mask = None

        # just like with other entities - no safety checks for now, will explode
        # on invalid name
        data = shared.assets.projectiles[name]

        # its probably possible to do this in less ugly way, but whatever
        assets = data.get("Assets", None)
        if assets:
            sheet = data["Assets"].get("sprite", None)
            animations = data.get("Animations", None)
            sprite_sizes = data.get("size", None)
        else:
            sprite_sizes = None
            sheet = None
            animations = None

        spritesheet = shared.assets.sprite.get(sheet, None)

        # doing it like that, coz default value from projectile's config can be
        # overriden on init. Say, by skill's values
        projectile_hitbox = hitbox_size or data["Main"].get("hitbox_size", 0)

        projectile_scale = scale or data["Main"].get("scale", 1)
        # scale modifier is variable that tweaks raw scale value. Say, if we want
        # to adjust default scale to match some other entity
        if scale_modifier:
            projectile_scale = projectile_scale * scale_modifier

        self.direction = 0

        parts = []
        if spritesheet and animations:
            body = p3dss.SpritesheetNode(
                name=f"{name}_body",
                spritesheet=spritesheet,
                sprite_sizes=sprite_sizes or shared.game_data.sprite_size,
                # #TODO: add ability to set custom scale
                scale=shared.game_data.node_scale,
            )

            for sprite_name in list(animations):
                item = p3dss.SpritesheetItem(
                    name=sprite_name,
                    sprites=animations[sprite_name]["sprites"],
                    loop=animations[sprite_name].get("loop", False),
                    playback_speed=animations[sprite_name].get(
                        "speed", shared.game_data.playback_speed
                    ),
                )
                body.add_item(item)

            parts.append(entity2d.VisualsNode(body, (0, 0, 0), 0.0, 0, False))

        # #TODO: make shape configurable (say, for rays)
        collision_settings = entity2d.CollisionSettings(
            shape=CollisionSphere,
            size=(0, 0, 0, projectile_hitbox),
            position=None,
            mask=collision_mask or None,
        )

        super().__init__(
            name=name,
            category=category,
            collision_settings=collision_settings,
            scale=projectile_scale,
            animated_parts=parts,
        )

        # optionally enabling billboard effect for projectile, in case it has such
        # setting in config. I could probably pass it to entity2d directly, idk
        if data["Main"].get("billboard", False):
            self.node.set_billboard_point_eye()

        # if projectile has no visuals attached to it, this wont do anything -
        # thanks to new placeholder function that works as null point for this
        self.change_animation("default")

        self.damage = damage
        self.node.set_python_tag("damage", self.damage)
        if effects:
            self.effects = effects
            self.node.set_python_tag("effects", self.effects)
        self.dead = False

        self.default_angle = data["Main"].get("angle", 0)

        if lifetime:
            self.lifetime = lifetime

        # its probably possible to do it in less ugly way
        if die_on_object_collision or die_on_creature_collision:
            # I should probably add collider on spawn, idk #TODO

            # coz there is no point in traversing projectile itself otherwise
            base.cTrav.add_collider(self.collision, base.chandler)
            self.node.set_python_tag("die_command", self.die)

        if die_on_creature_collision:
            self.node.set_python_tag("die_on_creature_collision", True)

        if die_on_object_collision:
            self.node.set_python_tag("die_on_object_collision", True)

    def spawn(self, position, direction=None, angle: int = 0, **kwargs):
        """Spawns the projectile on provided position"""

        # idk about this. Really. It will most likely break with introduction of
        # new skill's projectile behaviours and need rework. Like, idk - add bool
        # to init with "keep_distance: True/False" or something
        if direction:
            self.direction = direction

            position = position + direction

        # TODO: add ability to override stats (dmg, speed) on cast
        super().spawn(position)

        if not self.node.has_billboard():
            # idk about numbers and if it will explode on weird map angles, but
            # for now it kinda works. Dropped it there, coz if its used together
            # with billboard, node will never face camera like its invisible
            one, two, _ = position
            self.node.look_at(one, two, 1)

        # this will look kinda weird on projectiles with billboard, but for now
        # Im not fixing it, because Im unsure of how it should work. #TODO
        if angle or self.default_angle:
            angle += self.default_angle
            # rotating projectile around 2d axis to match the shooting angle
            # I have no idea how if it will work for enemies tho
            self.node.set_r(angle)

        # target does nothing, for now. May come handly in future
        if self.lifetime:
            # schedulging projectile to die in self.lifetime seconds after spawn
            base.task_mgr.add(self.dying_task, f"dying task of projectile {self.name}")

    def dying_task(self, event):
        # ensuring that projectile didnt die already
        if self.dead or not self.node:
            return

        dt = globalClock.get_dt()
        self.lifetime -= dt

        if self.lifetime > 0:
            return event.cont

        self.die()
        # super().die()
        # moved it there, because death of creature required it
        # self.node.remove_node()
        return

    def die(self):
        super().die()

        # TODO: add ability to play death animation and only then remove node
        # Right now its impossible, because we dont know the exact lengh of that
        # anim. Maybe I should add something like optional "length" setting into
        # projectile's config file?

        self.node.remove_node()
        # self.dying_task(0)


class ChasingProjectile(Projectile):
    """Projectile that always follows its target.
    Aside from usual projectile's stuff, should receive "target" NodePath on spawn
    """

    def __init__(
        self,
        name: str,
        category: str,
        damage=0,
        effects=None,
        scale=0,
        hitbox_size=0,
        speed=0,
        lifetime=0,
        scale_modifier=None,
        die_on_object_collision: bool = False,
        die_on_creature_collision: bool = False,
    ):

        self.target = None
        if speed:
            self.speed = speed
        else:
            self.speed = 1

        super().__init__(
            name=name,
            category=category,
            damage=damage,
            effects=effects,
            scale=scale,
            hitbox_size=hitbox_size,
            # I dont think speed should be there
            # speed = speed
            lifetime=lifetime,
            scale_modifier=scale_modifier,
            die_on_object_collision=die_on_object_collision,
            die_on_creature_collision=die_on_creature_collision,
        )
        self.node.set_python_tag("mov_spd", self.speed)

    def spawn(self, **kwargs):
        self.target = kwargs["target"]
        super().spawn(**kwargs)
        base.task_mgr.add(self.follow_task, f"following task of {self.name}")

    def follow_task(self, event):
        """Taskmanager task that make projectile follow the target"""
        if self.dead or not self.node or not self.target:
            return

        projectile_position = self.node.get_pos()

        vector_to_target = (
            self.target.get_pos() + self.direction
        ) - projectile_position
        vector_to_target.normalize()

        # workaround to ensure node will its stay on its original layer
        vxy = vector_to_target.get_xy()
        new_pos = projectile_position + (vxy * self.speed, 0)

        self.node.set_pos(new_pos)
        return event.cont


class MovingProjectile(Projectile):
    """Projectile that moves into specified direction with provided speed"""

    def __init__(
        self,
        name: str,
        category: str,
        speed,
        damage=0,
        effects=None,
        scale=0,
        hitbox_size=0,
        lifetime=0,
        scale_modifier=None,
        ricochets_amount: int = 0,
        die_on_object_collision: bool = False,
        die_on_creature_collision: bool = False,
    ):

        # I could probably move direction there too, since its mandatory anyway
        self.speed = speed

        super().__init__(
            name=name,
            category=category,
            damage=damage,
            effects=effects,
            scale=scale,
            hitbox_size=hitbox_size,
            # I dont think speed should be there
            # speed = speed
            lifetime=lifetime,
            scale_modifier=scale_modifier,
            die_on_object_collision=die_on_object_collision,
            die_on_creature_collision=die_on_creature_collision,
        )

        # it makes no sense to ricochet chasing or static projectile, thus its there
        if ricochets_amount:
            self.node.set_python_tag("ricochets_amount", ricochets_amount)

        self.node.set_python_tag("mov_spd", self.speed)

    def spawn(self, **kwargs):
        super().spawn(**kwargs)
        # normalizing direction, to fix issue with projectile moving too fast
        # it has to be done after parent's spawn, coz we need original direction
        # for sprite rotation and to make chasing projectile work
        self.direction.normalize()
        # doing so to enable support for ricochets
        # doing it after spawn, coz self.direction is set in parent
        self.node.set_python_tag("direction", self.direction)

        base.task_mgr.add(self.move_task, f"moving task of {self.name}")

    def move_task(self, event):
        """Taskmanager task that make projectile fly in specified direction"""
        if self.dead or not self.node:
            return

        # new_position = self.node.get_pos() + self.direction*self.speed
        direction = self.node.get_python_tag("direction")
        new_position = self.node.get_pos() + direction * self.speed

        self.node.set_pos(new_position)
        return event.cont

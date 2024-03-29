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
from panda3d.core import Vec2
from Game import entity2d, shared

log = logging.getLogger(__name__)

# module where I specify whatever stuff related to enemies

ENEMY_COLLISION_MASK = 0x03

HIT_SCORE = 10
KILL_SCORE = 15
ROT_TIMER = 15


class Enemy(entity2d.Creature):
    """Subclass of Creature, dedicated to creation of enemies. Accepts everything
    like entity2d.Creature, but also affix. Which can be either "Normal", "Big" or
    "Small". Based on affix, size, health and movement speed of enemy will get altered"""

    def __init__(self, name: str, affix: str = "Normal"):
        # this is hopefully temporary stuff, because it seems bad to call for that
        # stuff twice
        if affix == "Big":
            self.affix = affix
            scale = 2
        elif affix == "Small":
            self.affix = affix
            scale = 0.5
        else:
            self.affix = "Normal"
            # its 0 and not 1, coz there this way it will be passed as False and
            # no actual rescale will occur (coz default scale is 1 anyway)
            scale = 0

        super().__init__(
            name=name,
            category=shared.game_data.enemy_category,
            data=shared.assets.enemies[name],
            collision_mask=ENEMY_COLLISION_MASK,
            scale=scale,
        )

        self.rot_timer = ROT_TIMER
        self.can_be_removed = False

        if self.affix == "Big":
            # if enemy is big - reducing movement speed by 25%, but increasing
            # hp by 25% and size by x2
            self.stats["mov_spd"] = (self.stats["mov_spd"] / 100) * 75
            self.stats["hp"] = (self.stats["hp"] / 100) * 125
            # self.object.set_scale(2)
        elif self.affix == "Small":
            # if enemy is small - increasing movement speed by 25%, but reducing
            # hp by 25% and size by x2
            self.stats["mov_spd"] = (self.stats["mov_spd"] / 100) * 125
            self.stats["hp"] = (self.stats["hp"] / 100) * 75
            # self.object.set_scale(0.5)
        else:
            pass

        # base.task_mgr.add(self.ai_movement_handler, "enemy movement handler")

    def spawn(self, position):
        super().spawn(position)
        base.task_mgr.add(self.ai_movement_handler, "enemy movement handler")

    def ai_movement_handler(self, event):
        """This is but nasty hack to make enemies follow character. TODO: remake
        and move to its own module"""
        # TODO: maybe make it possible to chase not for just player?
        # TODO: not all enemies need to behave this way. e.g, for example, we can
        # only affect enemies that have their ['ai'] set to ['chaser']...
        # or something among these lines, will see in future

        # disable this handler if the enemy or player are dead. Without it, game
        # will crash the very next second after one of these events occur
        if self.dead or shared.level.player.dead:
            return

        if "stun" in self.status_effects:
            return event.cont

        player_position = shared.level.player.node.get_pos()
        mov_speed = self.stats["mov_spd"]

        enemy_position = self.node.get_pos()
        vector_to_player = player_position - enemy_position
        distance_to_player = vector_to_player.length()
        # normalizing vector is the key to avoid "flickering" effect, as its
        # basically ignores whatever minor difference in placement there are
        # I dont know how it works, lol
        vector_to_player = vector_to_player.normalized()

        # workaround to ensure enemy will stay on its layer, even if its different
        # from player due to size difference or whatever else reasons
        vxy = vector_to_player.get_xy()
        # new_pos = enemy_position + (vector_to_player*mov_speed)
        new_pos = enemy_position + (vxy * mov_speed, 0)
        pos_diff = enemy_position - new_pos

        self.node.set_python_tag("mov_spd", mov_speed)

        action = "idle"

        # trying to find angle that wont suck. Basically its the same thing, as
        # with player. Really thinking about moving it to skill itself #TODO
        hit_vector_x, hit_vector_y = vxy
        hit_vector_2D = -hit_vector_x, hit_vector_y

        y_vec = Vec2(0, 1)
        angle = y_vec.signed_angle_deg(hit_vector_2D)

        # it may be good idea to also track camera angle, if I will decide
        # to implement camera controls, at some point or another. #TODO
        if pos_diff[0] > 0:
            self.change_direction("right")
        else:
            self.change_direction("left")

        # this thing basically makes enemy move till it hit player, than play
        # attack animation. May backfire if player's sprite size is not equal
        # to player's hitbox
        if distance_to_player > shared.game_data.sprite_size[0] * 2:
            action = "move"
        else:
            # cast the very first skill available. #TODO: add something to affect
            # order of skills in self.skills
            skill = self.get_available_skill()
            if skill:
                # skill.cast(direction = (vector_to_player*(shared.DEFAULT_SPRITE_SIZE[0]/2)),
                skill.cast(direction=vector_to_player, angle=angle)

        # workaround for issue when enemy keeps running into player despite already
        # colliding with it, which cause enemy's animation to go wild.
        # idk about the numbers yet. I think, ideally it should be calculated from
        # player's hitbox and enemy's hitbox... but for now this will do
        if distance_to_player > 6:
            self.node.set_pos(new_pos)
        # self.object.set_pos(new_pos)

        if not self.node.get_python_tag("using_skill"):
            self.change_animation(action)

        return event.cont

    def get_available_skill(self):
        """Iterate thought all known skills and return first that has 0 cooldown"""
        for skill in self.skills:
            if not self.skills[skill].used:
                return self.skills[skill]

    def get_damage(self, amount=None, effects=None):
        if self.dead:
            return
        super().get_damage(amount, effects)
        # increasing score, based on HIT_SCORE value. It may be good idea to, instead,
        # increase it based on amount of damage received. But thats #TODO in future
        shared.level.increase_score_multiplier()
        shared.level.increase_score(HIT_SCORE)

    def mark_for_removal(self, event):
        """Taskmanager routine that remove enemy node and marks instance for
        removal from enemies list"""
        dt = globalClock.get_dt()
        self.rot_timer -= dt
        if self.rot_timer > 0:
            return event.cont

        self.can_be_removed = True
        self.animation = None
        self.node.remove_node()
        return

    def die(self):
        super().die()

        # remove enemy's gibs after self.rot_timer seconds
        base.task_mgr.add(self.mark_for_removal, "mark for removal")

        # for now this increase score based on HIT_SCORE+KILL_SCORE.
        # I dont think its a trouble, but may tweak at some point
        shared.level.increase_score(KILL_SCORE)
        # increase player's kill counter
        shared.level.kill_counter += 1
        log.debug(f"Kill counter has been increased to {shared.level.kill_counter}")
        # reduce enemy counter
        shared.level.enemy_amount -= 1

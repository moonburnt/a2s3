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

# various stuff triggered on collisions of certain objects

import logging
from panda3d.core import Vec3, CollisionEntry, NodePath
from time import time
from Game import shared

log = logging.getLogger(__name__)

# pause between calls to per-node's damage function. Making it anyhow lower will
# reintroduce the bug with multiple damage calls occuring during single frame
COLLISION_CHECK_PAUSE = 0.2


def check_damage_possibility(target: NodePath) -> bool:
    """Check if its possible to damage specified target right now, based
    on its "last_collision_time" python tag"""
    # this is a workaround for issue caused by multiple collisions occuring
    # at single frame, so damage check function cant keep up with it. Basically,
    # we allow new target's collisions to only trigger damage function each
    # 0.2 seconds. It may be good idea to abandon this thing in future in favor
    # of something like collisionhandlerqueue, but for now it works

    last_collision_time = target.get_python_tag("last_collision_time")
    current_time = time()
    if current_time - last_collision_time < COLLISION_CHECK_PAUSE:
        return False

    return True


def creature_with_projectile(creature: str, collision: CollisionEntry):
    """Things to do when creature collides with projectile.
    Creature resembles category of creature, to which collision applies
    (either player or enemy)"""
    # In current implementation we dont filter category of projectile, leaving
    # it to tracked events that trigger this function. This may cause issues

    # Determining if we are working with player collision or enemy collision
    if creature == shared.game_data.player_category:
        category = shared.game_data.player_category
    else:
        category = shared.game_data.enemy_category

    # At first - lets get raw data about what collided with what
    hitter = collision.get_from_node_path().get_parent()
    target = collision.get_into_node_path().get_parent()
    hitter_category = hitter.get_python_tag("category")
    target_category = target.get_python_tag("category")

    # workaround for "None Type" exception that rarely occurs if one of colliding
    # nodes has died the very second it needs to be used in another collision
    if not hitter_category or not target_category:
        log.warning(f"{hitter} or {target} is dead, ignored collision")
        return

    # Now lets maybe flip over hitter and target based on their category
    if hitter_category == category:
        hitter, target = target, hitter

    # Checking if its even possible to hit creature right now
    if not check_damage_possibility(target):
        log.debug("Collision cant occur right now")
        return
    target.set_python_tag("last_collision_time", time())

    # Finally, lets get required stats from projectile and damage target
    damage = hitter.get_python_tag("damage")
    damage_function = target.get_python_tag("get_damage")
    effects = hitter.get_python_tag("effects")
    log.debug(
        f"Attempting to deal {damage} damage to "
        f"{target.get_python_tag('name')} ({target.get_python_tag('id')})"
    )
    damage_function(damage, effects)

    # Checking if projectile should die on collision with creature
    if not hitter.get_python_tag("die_on_creature_collision"):
        return

    kill_hitter = hitter.get_python_tag("die_command")
    if kill_hitter:
        kill_hitter()


def creature_with_border(collision: CollisionEntry):
    """Function that triggers if creature collides with map's border.
    It pushes creatures back"""
    col_obj = collision.get_from_node_path().get_parent()
    # safety check for situations when object is in process of dying but hasnt
    # been removed completely yet
    if not col_obj:
        log.warning(f"{col_obj} seems to be dead, collision wont occur")
        return

    # getting pos like that, because of how map borders work
    wall_pos = collision.get_into_node_path().get_python_tag("position")[0]

    col_pos = col_obj.get_pos()

    vector = col_pos - wall_pos
    vx, vy = vector.get_xy()

    # this will be ideal knockback if we collide with wall right on its center
    knockback = col_obj.get_python_tag("mov_spd")

    # workaround to fix the issue with entity running into a wall getting
    # pushed to wall's center. This way it wont hapen anymore... I think
    if wall_pos[1] < 0:
        vx = 0
        vy = 1
    elif wall_pos[1] > 0:
        vx = 0
        vy = -1
    else:
        pass

    if wall_pos[0] < 0:
        vx = 1
        vy = 0
    elif wall_pos[0] > 0:
        vx = -1
        vy = 0
    else:
        pass

    vector = Vec3(vx, vy, 0).normalized()

    # this works for entities with any movement speed. However, there is some
    # old issue, I was unable to fix:
    # - Character will get pushed back as far as its running speed is. Meaning
    # creatures that move faster will get pushed closer to map's center. Its
    # not an issue for enemies (I think), but it may get annoying for player.
    #
    # For now, I have no idea how to solve both of these. Maybe at some point
    # I will re-implement collisionhandlerpusher for player, to deal with the
    # most annoying part of it #TODO
    new_pos = col_pos - vector * knockback

    col_obj.set_pos(new_pos)


def projectile_with_border(collision: CollisionEntry):
    """Function that triggers if projectile collides with map's border"""
    # It may need rework if I will ever implement ability to push objects
    col_obj = collision.get_from_node_path().get_parent()

    ricochets_amount = col_obj.get_python_tag("ricochets_amount")
    direction = col_obj.get_python_tag("direction")
    # this will break on negative ricochets_amount, but it shouldnt happen
    if ricochets_amount and direction:
        col_obj.set_python_tag("ricochets_amount", (ricochets_amount - 1))

        wall_pos = collision.get_into_node_path().get_python_tag("position")[0]

        x, y, h = direction

        if wall_pos[0]:
            x = -x
            # dont ask me why and how rotation works, because "it just works"
            col_obj.set_h(180)

        if wall_pos[1]:
            y = -y

        col_obj.set_python_tag("direction", Vec3(x, y, h))
        # see comment above. I have no idea why it works and it will probably
        # break on billboard projectiles #TODO
        col_obj.set_r(-(col_obj.get_r()))

        # returning right there, because ricochets override whatever below
        return

    if not col_obj.get_python_tag("die_on_object_collision"):
        return

    kill_hitter = col_obj.get_python_tag("die_command")
    if kill_hitter:
        kill_hitter()

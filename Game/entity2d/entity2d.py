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

from panda3d.core import CollisionSphere, CollisionNode, BitMask32, PandaNode, NodePath
import p3dss
from collections import namedtuple
from Game import shared
import logging

log = logging.getLogger(__name__)

LOOK_RIGHT = 0
LOOK_LEFT = 180

VisualsNode = namedtuple(
    "VisualsNode", ["instance", "position", "layer", "scale", "remove_on_death"]
)


class Entity2D:
    """Main class, dedicated to creation of collideable 2D objects."""

    def __init__(
        self,
        name: str,
        category: str,
        hitbox_size: int = None,
        collision_mask=None,
        scale: int = None,
        animated_parts: list = None,
        static_parts: list = None,
    ):
        self.name = name
        log.debug(f"Initializing {self.name} object")

        self.category = category

        # creating empty node to attach everything to. This way it will be easier
        # to attach other objects (like floating text and such), coz offset trickery
        # from animation wont affect other items attached to node (since its not
        # a parent anymore, but just another child)
        entity_node = PandaNode(name)
        # for now, self.node will be empty nodepath - we will reparent it to render
        # on spawn, to dont overflood it with reference entity instances
        self.node = NodePath(entity_node)

        # separate visuals node, to which parts from below will be attached
        vn = PandaNode(f"{name}_visuals")
        self.visuals = self.node.attach_new_node(vn)

        # this allows for rotating node around its h without making it invisible
        self.visuals.set_two_sided(True)

        # storage for entity parts (visuals) that will be attached to entity node.
        # static parts is used for stuff that is SpritesheetObject and doesnt have
        # switcher in it. Animated_parts reffers to thing that need to be changed
        # in case some related even occurs
        self.static_parts = static_parts or []
        self.animated_parts = animated_parts or []

        # setting character's collisions
        entity_collider = CollisionNode(self.category)

        # if no collision mask has been received - using defaults
        if collision_mask:
            entity_collider.set_from_collide_mask(BitMask32(collision_mask))
            entity_collider.set_into_collide_mask(BitMask32(collision_mask))

        # TODO: move this to be under character's legs
        # right now its centered on character's center
        self.hitbox_size = hitbox_size or shared.game_data.hitbox_size

        entity_collider.add_solid(CollisionSphere(0, 0, 0, self.hitbox_size))
        self.collision = self.node.attach_new_node(entity_collider)

        self.direction = None

        # initializing visual parts added with self.add_part()
        if self.static_parts or self.animated_parts:
            for sp in self.static_parts:
                sp.instance.wrt_reparent_to(self.visuals)
                if sp.position:
                    sp.instance.set_pos(sp.position)
                if sp.scale:
                    sp.instance.set_scale(sp.scale)

            for ap in self.animated_parts:
                ap.instance.node.wrt_reparent_to(self.visuals)
                if ap.position:
                    ap.instance.node.set_pos(ap.position)
                if ap.scale:
                    ap.instance.node.set_scale(ap.scale)

        # this will rescale whole node with all parts attached to it
        # in case some part as already been rescaled above - it will be rescaled
        # again, which may cause issues
        if scale:
            self.node.set_scale(scale)

        self.change_direction("right")

        # death status, that may be usefull during cleanup
        self.dead = False

        # attaching python tags to node, so these will be accessible during
        # collision events and similar stuff
        self.node.set_python_tag("name", self.name)
        self.node.set_python_tag("category", self.category)

        # I thought to put ctrav there, but for whatever reason it glitched proj
        # to fly into left wall. So I moved it to Creature subclass

        # debug function to show collisions all time
        if shared.settings.show_collisions:
            self.collision.show()

    def add_part(
        self,
        instance,
        position: tuple = (0, 0, 0),
        layer: float = 0.0,
        scale: int = 0,
        remove_on_death: bool = True,
    ):
        """Attach provided visual part to node"""
        data = VisualsNode(instance, position, layer, scale, remove_on_death)

        if isinstance(instance, p3dss.SpritesheetObject):
            self.animated_parts.append(data)
        else:
            self.static_parts.append(data)

    def change_animation(self, action):
        """Change animation of self.animated_parts items"""
        for item in self.animated_parts:
            item.instance.switch(action)
        # log.debug(f"Changed animation of {self.name} to {action}")

    def change_direction(self, direction: str):
        """Change direction of sprite (left/right)"""
        if direction == self.direction:
            return

        if direction == "right":
            # this is done to rotate all visuals. For the most, its enough
            self.visuals.set_h(LOOK_RIGHT)
            # however, our parts may overlap eachother on rotation in non-desired
            # way. To fix that, we also change their height levels (which are on
            # y, for panda-only-knows reasons)
            for item in self.animated_parts:
                item.instance.node.set_y(-item.layer)
            for item in self.static_parts:
                item.instance.node.set_y(-item.layer)
        else:
            self.visuals.set_h(LOOK_LEFT)

            for item in self.animated_parts:
                item.instance.node.set_y(item.layer)
            for item in self.static_parts:
                item.instance.set_y(item.layer)

        self.direction = direction
        log.debug(f"{self.name} is now facing {self.direction}")

    def spawn(self, position):
        """ "Attach node to scene graph and spawn entity at specified position"""
        # I may want to add further spawn options later. Like stats modificators
        # or scale modificators #TODO
        # I also have no idea if there should be some safety bool ("self.spawned")
        # to avoid breakage in case someone would try to use this func more than
        # once per entity #TODO
        self.node.wrt_reparent_to(render)
        self.node.set_pos(*position)
        log.debug(f"{self.name} has been spawned at {position}")

    def die(self):
        """Function that should be triggered when entity is about to die"""
        self.collision.remove_node()
        self.dead = True
        self.change_animation("dying")

        for ap in self.animated_parts:
            if ap.remove_on_death:
                ap.instance.node.remove_node()

        for sp in self.static_parts:
            if sp.remove_on_death:
                sp.instance.remove_node()
        log.debug(f"{self.name} is now dead")

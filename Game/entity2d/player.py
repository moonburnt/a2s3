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
from panda3d.core import Point3, Plane, Vec2, Vec3
from math import sqrt
from Game import shared, entity2d

log = logging.getLogger(__name__)

#module where I specify player's class

PLAYER_COLLISION_MASK = 0X06

class Player(entity2d.Creature):
    '''Subclass of Creature, dedicated to creation of player'''
    def __init__(self, name:str, position = None):
        collision_mask = PLAYER_COLLISION_MASK
        category = shared.PLAYER_CATEGORY

        #this will crash on invalid, no safety checks for now
        #data = base.assets.classes[name]
        data = shared.assets.classes[name]

        super().__init__(name = name,
                         category = category,
                         data = data,
                         collision_mask = collision_mask,
                         position = position)

        base.task_mgr.add(self.controls_handler,
                        f"controls handler of {self.name}")
        #the thing to track mouse position relatively to map. See get_mouse_vector.
        #It probably could be better to move this thing to map func/class instead?
        #TODO
        self.ground_plane = Plane((0,0,1), (0,0,0))

        #this is quite a resource-consuming task, but hopefully it wont be too
        #much of an issue...
        self.mouse_vector = Vec3(0, 0, 0)
        base.task_mgr.add(self.get_mouse_vector,
                        f"mouse vector tracker of {self.name}")

    def get_mouse_vector(self, event):
        '''Task manager routine that tracks vector of mouse, relatively to player'''
        if self.dead:
            return

        mouse_watcher = base.mouseWatcherNode

        #safety check to avoid crash if mouse has got out of window
        if not mouse_watcher.has_mouse():
            return event.cont

        #long story short, what happens there: we are getting mouse pointer's
        #position, then trying to translate it to the ground via plane.
        #this could probably be done faster and better, but for now it works
        mouse_pos = mouse_watcher.get_mouse()

        mouse_pos_3d = Point3()
        near = Point3()
        far = Point3()

        base.camLens.extrude(mouse_pos, near, far)
        self.ground_plane.intersects_line(mouse_pos_3d,
                                     render.get_relative_point(base.camera, near),
                                     render.get_relative_point(base.camera, far))

        hit_vector = mouse_pos_3d - self.node.get_pos()
        hit_vector.normalize()

        #updating mouse vector
        self.mouse_vector = hit_vector

        return event.cont


    def controls_handler(self, event):
        '''
        Intended to be used as part of task manager routine. Automatically receive
        event from task manager, checks if buttons are pressed and log it. Then
        return event back to task manager, so it keeps running in loop
        '''
        #safety check to ensure that player isnt dead, otherwise it will crash
        if self.dead:
            return event.cont

        if 'stun' in self.status_effects:
            return event.cont

        #idk if I need to export this to variable or call directly
        #in case it will backfire - turn this var into direct dictionary calls
        mov_speed = self.stats['mov_spd']

        #change the direction character face, based on mouse pointer position
        #this may need some tweaking if I will decide to add gamepad support
        #basically, the idea is the following: since camera is centered right
        #above our character, our char is the center of screen. Meaning positive
        #x will mean pointer is facing right and negative: pointer is facing left.
        #And thus char should do the same. This is kind of hack and will also
        #need tweaking if more sprites will be added. But for now it works
        #hint: this can also be used together with move buttons. E.g mouse change
        #the direction head/eyes face and keys change body. But that will depend
        #on amount of animations I would obtain. For now, lets leave it like that
        mouse_watcher = base.mouseWatcherNode
        #ensuring that mouse pointer is part of game's window right now
        if mouse_watcher.has_mouse():
            mouse_x = mouse_watcher.get_mouse_x()
            #independant direction change allows us to rotate node without resetting
            #animation frame. May be bad on characters that have facial features
            #only appearing on one side, but thats a minor annoyance
            if mouse_x > 0:
                self.change_direction('right')
            else:
                self.change_direction('left')

        #saving action to apply to our animation. Default is idle
        action = 'idle'

        #workaround for player moving faster diagonally than horizontally
        #it can be probably do prettier by normalizing vectors we are setting pos
        #to, but I was never able to achieve that without making player fly
        if ((shared.level.controls_status["move_up"] and
             shared.level.controls_status["move_left"]) or
            ((shared.level.controls_status["move_up"] and
             shared.level.controls_status["move_right"])) or
            ((shared.level.controls_status["move_down"] and
             shared.level.controls_status["move_left"])) or
            ((shared.level.controls_status["move_down"] and
             shared.level.controls_status["move_right"]))):
                 mov_speed = mov_speed / sqrt(2)

        if shared.level.controls_status["move_up"]:
            self.node.set_pos(self.node.get_pos() + (0, -mov_speed, 0))
            action = "move"
        if shared.level.controls_status["move_down"]:
            self.node.set_pos(self.node.get_pos() + (0, mov_speed, 0))
            action = "move"
        if shared.level.controls_status["move_left"]:
            self.node.set_pos(self.node.get_pos() + (mov_speed, 0, 0))
            action = "move"
        if shared.level.controls_status["move_right"]:
            self.node.set_pos(self.node.get_pos() + (-mov_speed, 0, 0))
            action = "move"

        #using it like that, because due to requirement to somehow pass caster to
        #skill, Im unable to set using_skill to be a normal variable
        if shared.level.controls_status["attack"] and not self.node.get_python_tag("using_skill"):

            hit_vector_x, hit_vector_y = self.mouse_vector.get_xy()
            #y has to be flipped if billboard_effect is active. Otherwise x has
            #to be flipped. Idk why its this way, probs coz first cam's num is 0
            #hit_vector_2D = hit_vector_x, -hit_vector_y
            hit_vector_2D = -hit_vector_x, hit_vector_y

            y_vec = Vec2(0, 1)
            angle = y_vec.signed_angle_deg(hit_vector_2D)

            #placeholder that picks up first skill from dictionary.
            #TODO: add some proper way to attach skills to buttons
            skill = list(self.skills.keys())[0]

            #pos_diff = shared.DEFAULT_SPRITE_SIZE[0]/2
            #proj_direction = self.mouse_vector * pos_diff
            #self.skills['Slash'].cast(direction = self.mouse_vector,

            #this should solve the issue with projectile not spawning if cursor
            #is located directly on top of player's head. However, the problem
            #with projectile spawning closer to player's center (in the very same
            #case) still remains - I have no idea how to solve it yet. #TODO
            direction = Vec3(self.mouse_vector[0], self.mouse_vector[1], 0)
            self.skills[skill].cast(direction = direction,
                                    angle = angle)

        #interrupting animation update tasks, in case we are in the middle of
        #casting skill. Iirc there is some case when it may backfire, but I cant
        #remember it. Wooops... #TODO
        #if not self.using_skill:
        if not self.node.get_python_tag("using_skill"):
            self.change_animation(action)

        #it works a bit weird, but if we wont return .cont of task we received,
        #then task will run just once and then stop, which we dont want
        return event.cont

    def get_damage(self, amount = None, effects = None):
        #giving player invinsibility frames on received damage
        #these shouldnt stack... I think? May backfire in future, idk
        super().get_damage(amount, effects)
        #commented immortality stuff out, coz its most likely will be removed

        #this check is there to avoid stacking up immortality
        #if not 'immortal' in self.status_effects:
            #this is a bit longer than stun lengh, to let player escape
        #    self.status_effects['immortal'] = 0.7
        #updating the value on player's hp gui
        shared.level.player_hud.update_hp(self.stats['hp'])
        shared.level.reset_score_multiplier()

    def die(self):
        super().die()

        shared.level.on_player_death()

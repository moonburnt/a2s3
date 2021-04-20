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

#This module is my attempt to move all anims-related garbage from entity2d into
#separate module. Eventually it should allow for spritesheet-powered buttons and
#other interface shenanigans, aswell as objects that dont need all the entity
#stuff to function (say, for hats/heads/whatever vanity)

import logging
from panda3d.core import CardMaker, TextureStage, Texture
from Game import shared, spritesheet_cutter

log = logging.getLogger(__name__)

DEFAULT_ANIMATIONS_SPEED = 0.1

class AnimatedObject:
    '''Create 2D CardMaker node out of provided spritesheet and sprite data.
    Can be then used to show various animations from provided sheet'''
    def __init__(self, name:str, spritesheet, sprites: list, sprite_size:int, default_sprite:int = 0):
        #name of animated object
        self.name = name
        self.size = sprite_size
        self.spritesheet = spritesheet

        size_x, size_y = self.size
        log.debug(f"{self.name}'s size has been set to {size_x}x{size_y}")

        #the magic that allows textures to be mirrored. With that thing being
        #there, its possible to use values in range 1-2 to get versions of sprites
        #that will face the opposite direction, removing the requirement to draw
        #them with hands. Without thing thing being there, 0 and 1 will be threated
        #as same coordinates, coz "out of box" texture wrap mode is "repeat"
        self.spritesheet.set_wrap_u(Texture.WM_mirror)
        self.spritesheet.set_wrap_v(Texture.WM_mirror)

        sprite_data = spritesheet_cutter.cut_spritesheet(self.spritesheet, self.size)

        horizontal_scale, vertical_scale = sprite_data['offset_steps']
        offsets = sprite_data['offsets']

        #entity2d used to create this with category. Idk
        entity_frame = CardMaker(self.name)
        #setting frame's size. Say, for 32x32 sprite all of these need to be 16
        entity_frame.set_frame(-(size_x/2), (size_x/2), -(size_y/2), (size_y/2))

        #settings this to base.render wont work - I tried
        self.node = render.attach_new_node(entity_frame.generate())
        self.node.set_texture(self.spritesheet)

        #okay, this does the magic
        #basically, to show the very first sprite of 2 in row, we set tex scale
        #to half (coz half is our normal char's size). If we will need to use it
        #with sprites other than first - then we also should adjust offset accordingly
        #entity_object.set_tex_offset(TextureStage.getDefault(), 0.5, 0)
        #entity_object.set_tex_scale(TextureStage.getDefault(), 0.5, 1)
        self.node.set_tex_scale(TextureStage.getDefault(),
                                    horizontal_scale, vertical_scale)

        #now, to use the stuff from cut_spritesheet function.
        #lets say, we need to use second sprite from sheet. Just do:
        #entity_object.set_tex_offset(TextureStage.getDefault(), *offsets[1])
        self.node.set_tex_offset(TextureStage.getDefault(),
                                     *offsets[default_sprite])

        #enable support for alpha channel. This is a float, e.g making it non-100%
        #will require values between 0 and 1
        self.node.set_transparency(1)

        #setting this to None may cause crashes on few rare cases, but going
        #for "idle_right" wont work for projectiles... So I technically add it
        #there for anims updater, but its meant to be overwritten at 100% cases
        self.current_animation = None

        self.animations = {}
        #this can be a bit complicated to tweak later, because sprites become
        #offsets and offsets become sprites... Idk what Im typing anymore lol
        for sprite in sprites:
            animation = Animation(name = sprite,
                                  sprites = offsets,
                                  animation_offsets = sprites[sprite]['sprites'],
                                  parent = self.node,
                                  loop = sprites[sprite].get('loop', False),
                                  speed = sprites[sprite].get('speed', DEFAULT_ANIMATIONS_SPEED))
            self.animations[sprite] = animation

    def play(self, animation:str):
        '''Make node play selected animation instead of whatever else plays'''
        #safety check to ensure that we wont crash everything with exception by
        #trying to play animation that doesnt exist
        if not animation in self.animations:
            log.warning(f"{self.name} has no animation named {animation}!")
            return

        self.stop()

        self.current_animation = self.animations[animation]
        self.current_animation.play()
        log.debug(f"{self.name} currently playing {self.current_animation.name}")

    def switch(self, animation: str):
        '''Play new animation, but only if its different from current one'''
        if not self.current_animation or self.current_animation.name != animation:
            self.play(animation)

    def stop(self):
        '''Stops current animation from playing'''
        if self.current_animation:
            self.current_animation.stop()
            log.debug(f"{self.name} has stopped playback of {self.current_animation.name}")

#idk if I should begin its name it with _, since it shouldnt be called manually,
#but only from AnimatedObject's sprite initialization
class Animation:
    '''Animation node. Meant to be initalized from AnimatedObject. Holds one
    animation from spritesheet with provided playback settings'''
    def __init__(self, name:str, sprites: list, animation_offsets:tuple,
                 parent, loop: bool, speed:float = DEFAULT_ANIMATIONS_SPEED):
        #name of the animation itself
        self.name = name

        #parent node, to which animation applies.
        #Must be AnimatedObject with spritesheet texture attached to it
        self.parent = parent

        #playback speed of animation
        self.speed = speed

        self.timer = self.speed

        #what to do at the end of animation. Either keep it playing or stop at last frame
        self.loop = loop

        #current status of animation's playback
        self.playing = False

        self.sprites = sprites
        self.offsets = animation_offsets
        self.current_frame = self.offsets[0]

    #maybe add ability to override speed and loop policies for once?
    def play(self):
        '''Plays the animation'''

        def update_animation(event):
            if not self.parent or not self.playing:
                return

            #ensuring that whatever below only runs if enough time has passed
            dt = globalClock.get_dt()
            self.timer -= dt
            if self.timer > 0:
                return event.cont

            #log.debug("Updating anims")
            #resetting anims timer, so countdown above will start again
            self.timer = self.speed

            #Right now there is a bug that breaks playback of single-sprite
            #actions. I didnt find any good workaround yet, maybe will make
            #separate function for these. #TODO
            if self.current_frame < self.offsets[1]:
                self.current_frame += 1
            else:
                #if looping is disabled - keep the last frame and destroy task
                if not self.loop:
                    self.playing = False
                    return

                self.current_frame = self.offsets[0]

            self.parent.set_tex_offset(TextureStage.getDefault(),
                                       *self.sprites[self.current_frame])

            return event.cont

        #this way we wont need to set starting frame manually
        self.current_frame = self.offsets[0]
        self.playing = True
        base.task_mgr.add(update_animation,
                        f"updates animation {self.name} of {self.parent}")

    def stop(self):
        '''Stops animation playback'''
        #unless I've messed up, this should stop the task from above
        self.playing = False

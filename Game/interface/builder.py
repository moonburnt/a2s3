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

# stuff to create ui parts with consistent style across application

from direct.gui.DirectGui import (DirectButton, DirectLabel,
                                  DirectSlider, DirectOptionMenu)
from .parts import *
from Game import shared
import logging

log = logging.getLogger(__name__)

#its class and not set of functions, coz I wasnt able to make these work properly
#otherwise, due to initialization order shenanigans loading textures after this
class InterfaceBuilder:
    """Produce UI parts with consistent style.
    Arguments accepted during init will be used in creation of all parts.
    Meant to be used with pixel2d
    """
    def __init__(self, button_textures: tuple, frame_texture, wide_frame_texture,
                                        select_sfx, hover_sfx,
                                        text_pos:tuple, text_scale:float,
                                        button_size:tuple = None,
                                        button_scale:tuple = None,
                                        frame_size:tuple = None,
                                        frame_scale:tuple = None,
                                        wide_frame_size:tuple = None,
                                        wide_frame_scale:tuple = None,
                                        ):
        #directgui autoassigns sequence of textures to button's different states
        #thats why its expected to be tuple
        self.button_textures = button_textures
        self.frame_texture = frame_texture
        self.wide_frame_texture = wide_frame_texture
        self.select_sfx = select_sfx
        self.hover_sfx = hover_sfx

        def get_texture_size(texture):
            x = texture.getOrigFileXSize()
            y = texture.getOrigFileYSize()
            return (x, 1, y)

        #coz this should reflect size differences from texture size
        #this will break if we cant x/y without trail
        def get_texture_scale(texture):
            x = texture.getOrigFileXSize()
            y = texture.getOrigFileYSize()
            scale_x = x / y
            scale_y = 1
            return (-scale_x, scale_x, -scale_y, scale_y)

        self.button_size = (button_size or
                            get_texture_size(self.button_textures[0]))
        self.button_scale = (button_scale or
                            get_texture_scale(self.button_textures[0]))

        self.frame_size = frame_size or get_texture_size(self.frame_texture)
        self.frame_scale = frame_scale or get_texture_scale(self.frame_texture)

        self.wide_frame_size = (wide_frame_size or
                                get_texture_size(self.wide_frame_texture))
        self.wide_frame_scale = (wide_frame_scale or
                                get_texture_scale(self.wide_frame_texture))

        self.text_pos = text_pos
        self.text_scale = text_scale

    def make_button(self, parent, pos:tuple, text:str = "", command = None):
        """Get button of default format with provided args."""
        # if not command:
            # def placeholder_command(*args, **kwargs):
                # pass
            # command = placeholder_command

        #same as commented out above
        command = command or (lambda *args, **kwargs: None)

        button = DirectButton(
                            text = text,
                            command = command,
                            pos = pos,
                            text_scale = self.text_scale,
                            text_pos = self.text_pos,
                            scale = self.button_size,
                            frameTexture = self.button_textures,
                            frameSize = self.button_scale,
                            clickSound = self.select_sfx,
                            rolloverSound = self.hover_sfx,
                            parent = parent,
                            )

        return button

    def make_label(self, parent, pos:tuple, text:str = "", scale:int = 0,
                                                        text_pos:tuple = None):
        """Get label of default format with provided args."""
        frame_scale = self.frame_scale
        if scale:
            frame_scale = (frame_scale[0]*scale,
                           frame_scale[1]*scale,
                           frame_scale[2]*scale,
                           frame_scale[3]*scale)

        text_pos = text_pos or self.text_pos

        label = DirectLabel(
                            text = text,
                            pos = pos,
                            frameTexture = self.frame_texture,
                            frameSize = frame_scale,
                            text_scale = self.text_scale,
                            text_pos = text_pos,
                            scale = self.frame_size,
                            parent = parent,
                            )

        return label

    def make_wide_label(self, parent, pos:tuple, text:str = "", scale:int = 0,
                                                        text_pos:tuple = None):
        """Get wide label of default format with provided args."""
        frame_scale = self.wide_frame_scale
        if scale:
            frame_scale = (frame_scale[0]*scale,
                           frame_scale[1]*scale,
                           frame_scale[2]*scale,
                           frame_scale[3]*scale)

        text_pos = text_pos or self.text_pos

        label = DirectLabel(
                            text = text,
                            pos = pos,
                            frameTexture = self.wide_frame_texture,
                            frameSize = frame_scale,
                            text_scale = self.text_scale,
                            text_pos = text_pos,
                            scale = self.wide_frame_size,
                            parent = parent,
                            )

        return label

    def make_slider(self, parent, pos:tuple, value, command = None):
        """Get slider of default format with provided args."""
        command = command or (lambda *args, **kwargs: None)

        slider = DirectSlider(
                            command = command,
                            pos = pos,
                            scale = (256, 1, 128),
                            value = value,
                            parent = parent,
                            )

        return slider

    def make_dialog_buttons(self, parent, pos:tuple,
                            back_text:str = "", forward_text:str = "",
                            back_command = None, forward_command = None):
        """Get dialog with two buttons of default format with provided args."""
        dialog_buttons = DialogButtons(
                            back_text = back_text,
                            back_command = back_command,
                            forward_text = forward_text,
                            forward_command = forward_command,
                            gap = 130,
                            pos = pos,
                            button_scale = self.button_size,
                            text_pos = self.text_pos,
                            text_scale = self.text_scale,
                            button_texture = self.button_textures,
                            button_size = self.button_scale,
                            click_sound = self.select_sfx,
                            rollover_sound = self.hover_sfx,
                            parent = parent,
                            )

        return dialog_buttons

    def make_option_menu(self, parent, pos:tuple, items:list, initial_item:int,
                                                                command = None):
        """Get option menu of default format with provided args."""
        command = command or (lambda *args, **kwargs: None)

        #TODO: replace this garbage with self-made carousel
        option_menu = DirectOptionMenu(
                            command = command,
                            items = items,
                            initialitem = initial_item,
                            pos = pos,
                            text_pos = self.text_pos,
                            text_scale = self.text_scale,
                            text_align = TextNode.ACenter,
                            popupMarker_scale = 0.01,
                            scale = self.button_size,
                            frameTexture = self.button_textures,
                            frameSize = self.button_scale,
                            popupMarker_image = None,
                            clickSound = self.select_sfx,
                            rolloverSound = self.hover_sfx,
                            parent = parent,
                            )

        return option_menu

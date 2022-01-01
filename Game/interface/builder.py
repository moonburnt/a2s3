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

from direct.gui.DirectGui import (
    DirectButton,
    DirectLabel,
    DirectSlider,
    DirectOptionMenu,
    DGG,
)
from collections import namedtuple
from Game.interface.parts import *
from Game import shared
import logging

log = logging.getLogger(__name__)

# The idea was to group pos and alignment together, coz same pos on different
# align will produce completely different results. But we can actually expand it
# further and also include scale. Maybe some other text properties l8r, idk #TODO
TextStyle = namedtuple("TextStyle", ["alignment", "position", "scale"])


def get_texture_size(texture):
    """Get size of texture in DirectGUI's measurement values"""
    # Safety check to ensure it works for both p3dss-generates sprites
    # and images loaded from disk
    x = texture.getOrigFileXSize() or texture.getXSize()
    y = texture.getOrigFileYSize() or texture.getYSize()
    return (x, 1, y)


def get_texture_scale(texture):
    """Get scale of texture in DirectGUI's measurement values"""
    x = texture.getOrigFileXSize() or texture.getXSize()
    y = texture.getOrigFileYSize() or texture.getYSize()
    return (-x, x, -y, y)


# its class and not set of functions, coz I wasnt able to make these work properly
# otherwise, due to initialization order shenanigans loading textures after this
class InterfaceBuilder:
    """Produce UI parts with consistent style.
    Arguments accepted during init will be used in creation of all parts.
    Meant to be used with pixel2d
    """

    def __init__(
        self,
        button_textures: tuple,
        frame_texture,
        wide_frame_texture,
        select_sfx,
        hover_sfx,
        text_styles: dict,
        icon_pos: tuple,
        default_text_style: "str" = None,
        button_size: tuple = None,
        button_scale: tuple = None,
        frame_size: tuple = None,
        frame_scale: tuple = None,
        wide_frame_size: tuple = None,
        wide_frame_scale: tuple = None,
    ):
        # directgui autoassigns sequence of textures to button's different states
        # thats why its expected to be tuple
        self.button_textures = button_textures
        self.frame_texture = frame_texture
        self.wide_frame_texture = wide_frame_texture
        self.select_sfx = select_sfx
        self.hover_sfx = hover_sfx

        self.button_size = button_size or get_texture_size(self.button_textures[0])
        self.button_scale = button_scale or get_texture_scale(self.button_textures[0])

        self.frame_size = frame_size or get_texture_size(self.frame_texture)
        self.frame_scale = frame_scale or get_texture_scale(self.frame_texture)

        self.wide_frame_size = wide_frame_size or get_texture_size(
            self.wide_frame_texture
        )
        self.wide_frame_scale = wide_frame_scale or get_texture_scale(
            self.wide_frame_texture
        )

        self.text_styles = text_styles
        self.default_text_style = (
            default_text_style or self.text_styles[list(self.text_styles)[0]]
        )

        self.icon_pos = icon_pos

    def make_button(
        self,
        parent,
        pos: tuple,
        text: str = "",
        icon=None,
        icon_pos: tuple = None,
        text_style: str = None,
        command=None,
    ):
        """Get button of default format with provided args."""
        # if not command:
        # def placeholder_command(*args, **kwargs):
        # pass
        # command = placeholder_command

        # same as commented out above
        command = command or (lambda *args, **kwargs: None)
        if text_style:
            text_style = self.text_styles[text_style]
        else:
            text_style = self.default_text_style

        # collecting arguments into kwargs, to avoid duplicating whole thing
        # solely due to icon-related shenanigans
        kwargs = {
            "text": text,
            "command": command,
            "pos": pos,
            "text_scale": text_style.scale,
            "text_pos": text_style.position,
            "text_align": text_style.alignment,
            "relief": DGG.FLAT,
            "frameTexture": self.button_textures,
            "frameSize": self.button_scale,
            "clickSound": self.select_sfx,
            "rolloverSound": self.hover_sfx,
            "parent": parent,
        }
        if icon:
            kwargs["image"] = icon
            kwargs["image_scale"] = get_texture_size(icon)
            kwargs["image_pos"] = icon_pos or self.icon_pos

        return DirectButton(**kwargs)

    def _make_label(
        self,
        parent,
        frame_scale,
        texture,
        pos: tuple,
        text: str = "",
        scale: int = 0,
        text_pos: tuple = None,
        icon=None,
        icon_pos: tuple = None,
        text_style: str = None,
    ):

        if scale:
            frame_scale = (
                frame_scale[0] * scale,
                frame_scale[1] * scale,
                frame_scale[2] * scale,
                frame_scale[3] * scale,
            )

        if text_style:
            text_style = self.text_styles[text_style]
        else:
            text_style = self.default_text_style

        kwargs = {
            "text": text,
            "pos": pos,
            "frameTexture": texture,
            "frameSize": frame_scale,
            "relief": DGG.FLAT,
            "text_scale": text_style.scale,
            "text_pos": text_pos or text_style.position,
            "text_align": text_style.alignment,
            "parent": parent,
        }
        if icon:
            kwargs["image"] = icon
            kwargs["image_scale"] = get_texture_size(icon)
            kwargs["image_pos"] = icon_pos or self.icon_pos

        return DirectLabel(**kwargs)

    def make_label(
        self,
        parent,
        pos: tuple,
        text: str = "",
        scale: int = 0,
        text_pos: tuple = None,
        icon=None,
        icon_pos: tuple = None,
        text_style: str = None,
    ):
        """Get label of default format with provided args."""

        label = self._make_label(
            parent=parent,
            frame_scale=self.frame_scale,
            texture=self.frame_texture,
            pos=pos,
            text=text,
            scale=scale,
            text_pos=text_pos,
            icon=icon,
            icon_pos=icon_pos,
            text_style=text_style,
        )

        return label

    def make_wide_label(
        self,
        parent,
        pos: tuple,
        text: str = "",
        scale: int = 0,
        text_pos: tuple = None,
        icon=None,
        icon_pos: tuple = None,
        text_style: str = None,
    ):
        """Get wide label of default format with provided args."""
        label = self._make_label(
            parent=parent,
            frame_scale=self.wide_frame_scale,
            texture=self.wide_frame_texture,
            pos=pos,
            text=text,
            scale=scale,
            text_pos=text_pos,
            icon=icon,
            icon_pos=icon_pos,
            text_style=text_style,
        )

        return label

    def make_slider(self, parent, pos: tuple, value, command=None):
        """Get slider of default format with provided args."""
        command = command or (lambda *args, **kwargs: None)

        slider = DirectSlider(
            command=command,
            pos=pos,
            scale=(256, 1, 128),
            value=value,
            parent=parent,
            relief=DGG.FLAT,
        )

        return slider

    def make_dialog_buttons(
        self,
        parent,
        pos: tuple,
        back_text: str = "",
        forward_text: str = "",
        back_command=None,
        forward_command=None,
        text_style: str = None,
    ):
        """Get dialog with two buttons of default format with provided args."""
        if text_style:
            text_style = self.text_styles[text_style]
        else:
            text_style = self.default_text_style

        dialog_buttons = DialogButtons(
            back_text=back_text,
            back_command=back_command,
            forward_text=forward_text,
            forward_command=forward_command,
            gap=130,
            pos=pos,
            button_scale=self.button_size,
            text_pos=text_style.position,
            text_scale=text_style.scale,
            button_texture=self.button_textures,
            button_size=self.button_scale,
            click_sound=self.select_sfx,
            rollover_sound=self.hover_sfx,
            parent=parent,
        )

        return dialog_buttons

    def make_option_menu(
        self,
        parent,
        pos: tuple,
        items: list,
        initial_item: int,
        command=None,
        text_style: str = None,
    ):
        """Get option menu of default format with provided args."""
        command = command or (lambda *args, **kwargs: None)
        if text_style:
            text_style = self.text_styles[text_style]
        else:
            text_style = self.default_text_style

        # TODO: replace this garbage with self-made carousel
        option_menu = DirectOptionMenu(
            command=command,
            items=items,
            initialitem=initial_item,
            pos=pos,
            text_scale=text_style.scale,
            text_pos=text_style.position,
            text_align=text_style.alignment,
            item_text_scale=text_style.scale,
            item_text_pos=text_style.position,
            item_text_align=text_style.alignment,
            item_frameTexture=self.button_textures,
            # this doesnt seem to do anyting - its always default
            item_frameSize=self.button_scale,
            item_image_scale=self.button_size,
            # this doesnt seem to do anything - transparency still
            # doesnt work
            item_relief=DGG.FLAT,
            item_rolloverSound=self.hover_sfx,
            item_clickSound=self.select_sfx,
            highlightColor=(1, 1, 1, 1),
            popupMarker_scale=10,
            frameTexture=self.button_textures,
            frameSize=self.button_scale,
            # this doesnt seem to do anything
            relief=DGG.FLAT,
            popupMarker_relief=None,
            popupMarker_image=None,
            clickSound=self.select_sfx,
            rolloverSound=self.hover_sfx,
            parent=parent,
        )

        # this doesnt seem to do anything either
        option_menu.set_transparency(True)

        return option_menu

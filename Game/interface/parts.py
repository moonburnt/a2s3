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

# custom ui parts

import logging
from panda3d.core import NodePath
from direct.gui.OnscreenText import OnscreenText, TextNode
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectSlider, DGG

# from direct.gui.OnscreenImage import OnscreenImage

from Game import shared

log = logging.getLogger(__name__)


class TextMsg:
    """Simple text message.
    Basically a wrapper on top of OnscreenText with sane argument names.
    Has limited set of supported functions, in comparison with original.
    """

    # **kwargs is there to accept garbage items passed from childs. Should be
    # removed when childs will get proper init args instead of these #TODO
    def __init__(
        self,
        text: str,
        text_pos: tuple = (0, 0),
        text_align=TextNode.ACenter,
        text_scale: float = 0.1,
        text_color: tuple = (1, 1, 1, 1),
        parent=None,
        **kwargs
    ):

        self.msg = OnscreenText(
            pos=text_pos,
            align=text_align,
            scale=text_scale,
            fg=text_color,
            parent=parent or base.aspect2d,
            mayChange=True,
        )

        self.set_text(text)
        self.hide()

    # None of these functions is necessary - I just want to provide unified way
    # to do these things for all childs. And to avoid camelCase where possible.
    # I may remove these in future, if it will seem pointless
    def set_text(self, text: str):
        """Set message's text"""
        self.msg.setText(text)

    def hide(self):
        """Hide message"""
        self.msg.hide()

    def show(self):
        """Show message"""
        self.msg.show()


class LoadingScreen(TextMsg):
    """Simple loading screen.
    Meant to be used when we do some calculations that may slow/freeze game
    window (such as level loading)
    """

    # using kwargs for now as lazy proxy to TextMsg. Should change in future #TODO
    def __init__(self, **kwargs):
        if not "text" in kwargs:
            kwargs["text"] = "Loading..."

        super().__init__(**kwargs)
        # todo: add configurable bg image, maybe progress bar


class Popup(TextMsg):
    """Auto-hiding notification-like message"""

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", None) or "Popup"
        self.duration = kwargs.get("duration", None) or 1

        if not "text" in kwargs:
            kwargs["text"] = ""

        super().__init__(**kwargs)

    def set_duration(self, duration):
        """Set popup's duration. Expected to be positive number"""
        # duration may be both int and float, idk how to do that yet
        self.duration = duration

    def show(self):
        """Show message"""
        # TODO: add ability to use some visual effects
        super().show()

        # todo: maybe remake it into lerp, so there wont be need to involve base.
        # this function is hidden inside, coz we have no use for it outside
        def hide_popup_task(event):
            self.hide()
            return

        base.task_mgr.do_method_later(self.duration, hide_popup_task, self.name)


class DialogButtons:
    """Two buttons - one for going backward, other for going forward/confirming"""

    # TODO: maybe add optional middle button (to split "forward" and "ok")?
    def __init__(
        self,
        back_text: str = "",
        forward_text: str = "",
        back_command=None,
        forward_command=None,
        gap=1,
        pos: tuple = (0, 0, 0),
        button_scale: tuple = (1, 1, 1),
        text_pos: tuple = (0, 0),
        text_scale: float = 0.1,
        button_texture=None,
        button_size: tuple = (1, 1, 1),
        click_sound=None,
        rollover_sound=None,
        parent=None,
        name: str = "Dialog Buttons",
        **kwargs
    ):
        parent = parent or base.aspect2d

        self.frame = NodePath(name)
        self.frame.reparent_to(parent)
        self.frame.set_transparency(True)

        back_command = back_command or (lambda *args, **kwargs: None)
        forward_command = forward_command or (lambda *args, **kwargs: None)

        x, h, y = pos
        back_x = x - gap
        back_pos = back_x, h, y
        forward_x = x + gap
        forward_pos = forward_x, h, y

        self.back_button = DirectButton(
            text=back_text,
            command=back_command,
            pos=back_pos,
            text_pos=text_pos,
            text_scale=text_scale,
            image_scale=button_scale,
            frameTexture=button_texture,
            frameSize=button_size,
            relief=DGG.FLAT,
            clickSound=click_sound,
            rolloverSound=rollover_sound,
            parent=self.frame,
        )

        self.forward_button = DirectButton(
            text=forward_text,
            command=forward_command,
            pos=forward_pos,
            text_pos=text_pos,
            text_scale=text_scale,
            image_scale=button_scale,
            frameTexture=button_texture,
            frameSize=button_size,
            relief=DGG.FLAT,
            clickSound=click_sound,
            rolloverSound=rollover_sound,
            parent=self.frame,
        )

    def show():
        """Show buttons"""
        self.frame.show()

    def hide():
        """Hide buttons"""
        self.frame.hide()


# TODO: maybe add subclasses for FullscreenMenu and Submenu, in case it will
# affect button sizes
class Menu:
    """Parent class for all huds and menus"""

    def __init__(self, name: str, parent=None):
        if not parent:
            parent = base.aspect2d
        # "frame" is nodepath object, to which everything else will be attached
        # doing things this way will make it possible to toggle gui elements
        # together, aswell as apply some properties to all of them at once
        self.frame = NodePath(name)

        # reparenting this thing to pixel2d make buttons scale pixel-perfectly.
        # In case scale equals image size, obviously.
        # On other side, it adds requirement to manually calculate position based
        # on window's size, since with pixel2d placement of items is calculated
        # not from center, but from top left corner of window
        self.frame.reparent_to(parent)

        # enabling transparency to all buttons in menu
        self.frame.set_transparency(True)

        # this will change the default behavior of menus, but to me it will make
        # things more convenient. E.g if you need to show something - do it manually
        self.hide()

    # I dont actually need to attach these, but doing so will make toggling class easier
    def hide(self):
        """Hide menu"""
        self.frame.hide()

    def show(self):
        """Show menu"""
        self.frame.show()

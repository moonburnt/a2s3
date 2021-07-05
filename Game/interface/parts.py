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
#from direct.gui.OnscreenImage import OnscreenImage

from Game import shared

log = logging.getLogger(__name__)

class TextMsg:
    def __init__(self, text:str, text_pos:tuple = (0, 0),
                       text_align = TextNode.ACenter, text_scale:float = 0.1,
                       text_color:tuple = (1, 1, 1, 1), parent = None, **kwargs):

        self.msg = OnscreenText(pos = text_pos,
                                align = text_align,
                                scale = text_scale,
                                fg = text_color,
                                parent = parent or base.aspect2d,
                                mayChange = True)

        self.set_text(text)
        self.hide()

    #None of these functions is necessary - I just want to provide unified way
    #to do these things for all childs. And to avoid camelCase where possible.
    #I may remove these in future, if it will seem pointless
    def set_text(self, text:str):
        self.msg.setText(text)

    def hide(self):
        self.msg.hide()

    def show(self):
        self.msg.show()

class LoadingScreen(TextMsg):
    '''Meta class for filler screens used when we do some calculations that may
    slow/freeze game window (such as level loading)'''
    def __init__(self, **kwargs):
        if not "text" in kwargs:
            kwargs["text"] = "Loading..."

        super().__init__(**kwargs)
        #todo: add configurable bg image, maybe progress bar

class Popup(TextMsg):
    '''Meta class for messages that appear on certain actions and auto-hide after
    certain amount of time has been passed'''
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", None) or "Popup"
        self.duration = kwargs.get("duration", None) or 1

        if not "text" in kwargs:
            kwargs["text"] = ""

        super().__init__(**kwargs)

    def set_duration(self, duration):
        '''Set popup's duration. Expected to be positive number'''
        #duration may be both int and float, idk how to do that yet
        self.duration = duration

    def show(self):
        #TODO: add ability to use some visual effects
        super().show()

        #todo: maybe remake it into lerp, so there wont be need to involve base.
        #this function is hidden inside, coz we have no use for it outside
        def hide_popup_task(event):
            self.hide()
            return

        base.task_mgr.do_method_later(self.duration, hide_popup_task, self.name)

class Menu:
    '''Main class for all huds and menus. Require nodepath name to be passed as
    argument during initialization process'''
    def __init__(self, name, parent = None):
        if not parent:
            parent = base.aspect2d
        #"frame" is nodepath object, to which everything else will be attached
        #doing things this way will make it possible to toggle gui elements
        #together, aswell as apply some properties to all of them at once
        self.frame = NodePath(name)

        #reparenting this thing to pixel2d make buttons scale pixel-perfectly.
        #In case scale equals image size, obviously.
        #On other side, it adds requirement to manually calculate position based
        #on window's size, since with pixel2d placement of items is calculated
        #not from center, but from top left corner of window
        self.frame.reparent_to(parent)

        #enabling transparency to all buttons in menu
        self.frame.set_transparency(True)

        #basically, the thing is - directgui can automatically assign multiple
        #textures to different button's events, if they are passed as list or
        #tuple in correct order. And thats what we are doing there
        self.button_textures = (shared.assets.sprite['button'],
                                shared.assets.sprite['button_active'],
                                shared.assets.sprite['button_selected'])

        self.hover_sfx = shared.assets.sfx['menu_hover']
        self.select_sfx = shared.assets.sfx['menu_select']

        #this will change the default behavior of menus, but to me it will make
        #things more convenient. E.g if you need to show something - do it manually
        self.hide()

    #I dont actually need to attach these, but doing so will make toggling class easier
    def hide(self):
        self.frame.hide()

    def show(self):
        self.frame.show()

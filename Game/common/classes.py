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

# various common data types used across the game
import logging
from types import SimpleNamespace

log = logging.getLogger(__name__)

class Storage(SimpleNamespace):
    pass

class InterfaceStorage:
    def __init__(self):
        self.storage = {}
        self.currently_active = {}

    def add(self, item, name:str):
        self.storage[name] = item

    def check(self, name:str):
        if name in self.storage:
            return True
        else:
            log.debug(f"{name} doesnt exist in storage!")
            return False

    def show(self, name:str):
        if self.check(name):
            self.currently_active[name] = self.storage[name]
            self.storage[name].show()

            log.info(f"Showing {name} ui")

    def hide(self, name:str):
        if self.check(name):
            if getattr(self.currently_active, name, None):
                self.currently_active.pop(name)
            self.storage[name].hide()

            log.info(f"Hid {name} ui")

    def switch(self, name:str):
        '''Switch CURRENT_INTERFACE menu to one passed as argument'''
        #this is kind of nasty thing. But if used correctly, it should allow to
        #easily switch active interfaces from one to another, in case only one
        #can exist at given time
        if self.currently_active:
            for item in self.currently_active:
                self.storage[item].hide()
            self.currently_active = {}

        self.show(name)

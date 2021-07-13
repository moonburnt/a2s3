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
    """Storage for interface items.
    Provides some handy functions to make switching between UIs easier
    """
    def __init__(self):
        self.storage = {}
        self.currently_active = {}
        #this will make it possible to revert to previous switch state.
        #for the time being, it only works once - I may do something about it l8r
        #like, idk - introduce state checkpoints or something? #TODO
        self.previous = []

    def add(self, item, name:str):
        """Add interface into self.storage"""
        self.storage[name] = item

    def check(self, name:str):
        """Check if interface exists in self.storage"""
        if name in self.storage:
            return True
        else:
            log.debug(f"{name} doesnt exist in storage!")
            return False

    def show(self, name:str):
        """Show item with provided name, if it exists in self.storage"""
        if self.check(name):
            self.currently_active[name] = self.storage[name]
            self.storage[name].show()

            log.info(f"Showing {name} ui")

    def hide(self, name:str):
        """Hide item with provided name, if it exists in self.storage"""
        if self.check(name):
            if getattr(self.currently_active, name, None):
                self.currently_active.pop(name)
            self.storage[name].hide()

            log.info(f"Hid {name} ui")

    def switch(self, name:str):
        """Hide active menus and show item with provided name instead"""
        #TODO: maybe add ability to pass multiple items?

        #this is kind of nasty thing. But if used correctly, it should allow to
        #easily switch active interfaces from one to another, in case only one
        #can exist at given time
        if self.previous:
            self.previous = []

        if self.currently_active:
            for item in self.currently_active:
                #adding just names to use with self.show()
                self.previous.append(item)
                self.storage[item].hide()
            self.currently_active = {}

        self.show(name)

    def show_previous(self):
        """Show menu state before last call of self.switch(), if available"""
        #TODO: maybe add ability to exclude specific ui types from showcase,
        #coz rn it shows popups and stuff, which may be unwanted
        if not self.previous:
            log.debug("There are no previous screens saved in memory!")
            return

        #copying current list state, coz switch() will overwrite it
        previous = self.previous.copy()

        #this is far from perfect, but will do for now
        #switching to first elem in self.previous, then manually showin others
        self.switch(self.previous[0])

        #this will be skipped if previous has but one elem in list, I think
        for item in previous[1:]:
            self.show(item)

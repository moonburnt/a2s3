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

        #storage meant to address issue with "previous" storage allowing to only
        #switch back and forth between two combinations of items. With this, it
        #should be possible to dump whole self.currently_active as named blueprint,
        #to retrieve and reuse in future
        self.blueprints = {}

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

    #this should NEVER have switch'es default set to True, coz its used in
    #self.switch() and this will cause endless recursion
    def show(self, name:str, switch:bool = False):
        """Show item with provided name, if it exists in self.storage.
        If switch - then also hide currently shown items.
        """
        if switch:
            self.switch(name)

        if self.check(name):
            self.currently_active[name] = self.storage[name]
            self.storage[name].show()

            log.debug(f"Showing {name} ui")

    def hide(self, name:str):
        """Hide item with provided name, if it exists in self.storage"""
        if self.check(name):
            if getattr(self.currently_active, name, None):
                self.currently_active.pop(name)
            self.storage[name].hide()

            log.debug(f"Hid {name} ui")

    def save_blueprint(self, name:str, items:list = []):
        """Save self.currently_active or items into named blueprints storage"""
        if not items:
            names = []
            for item in self.currently_active:
                names.append(item)
        else:
            #this may backfire since there is no check to ensure items exist
            names = items

        self.blueprints[name] = names
        log.debug(f"Saved {names} into blueprint storage as {name}")

    def show_multiple(self, items:list, switch:bool = False):
        """Show multiple items at once.
        If switch - then also hide currently shown items
        """
        #this will be used to skip first item in list, if its passed to switch
        list_start = 0
        if switch:
            self.switch(items[0])
            list_start = 1

        #this will be skipped if previous has but one elem in list, I think
        for item in items[list_start:]:
            self.show(item)

    def load_blueprint(self, name:str):
        """Switch from currently active items to saved blueprint"""
        if not name in self.blueprints:
            log.error(f"{name} doesnt exist in blueprints storage!")
            return

        blueprint = self.blueprints[name]
        self.show_multiple(blueprint)

    #TODO: maybe rename "keep_current_as" to something else
    def switch(self, name:str, keep_current_as:str = None):
        """Hide active menus and show item with provided name instead"""
        current_items = []

        for item in self.currently_active:
            #adding just names to use with self.show()
            current_items.append(item)
            self.storage[item].hide()
        self.currently_active = {}

        #save current items into named blueprint
        if keep_current_as:
            self.save_blueprint(keep_current_as, current_items)

        self.previous = current_items

        self.show(name)

    def show_previous(self, exclude: list = [], keep_current_as:str = None):
        """Show menu state before last call of self.switch(), if available"""
        if not self.previous:
            log.debug("There are no previous screens saved in memory!")
            return

        if keep_current_as:
            self.save_blueprint(keep_current_as)

        previous = self.previous.copy()
        #if exclude list has been passed - removing matching items from previous
        for item in exclude:
            if item in previous:
                previous.remove(item)

        #copying current list state, coz switch() will overwrite it
        self.show_multiple(previous, switch = True)

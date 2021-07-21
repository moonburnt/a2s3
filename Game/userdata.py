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

# module where I specify functions related to loading game assets into memory

from os import makedirs
from os.path import join, isfile
from sys import exit
import json
import logging

log = logging.getLogger(__name__)

USER_DIR = join(".", "User")  # this will most likely be temp dir and removed later
# TODO: move these to os-specific places
DATA_DIR = join(USER_DIR, "Data")
# maybe save it in different place.
# say, data in .local/share and settings in .config #TODO
SETTINGS_DIR = join(USER_DIR, "Settings")

LEADERBOARDS = "leaderboards.json"


class UserdataManager:
    def __init__(self, data_path: str = None, settings_path: str = None):
        # coz we may want to override these with launch arg
        self.settings_path = settings_path or SETTINGS_DIR
        self.data_path = settings_path or DATA_DIR

        self.lb_file = join(self.data_path, LEADERBOARDS)

        self.settings = {}  # thou shall be game settings
        self.leaderboards = []  # these are leaderboards
        # there will be more later, like game's progress and stuff

        # attempting to create default dirs in case they dont exist
        for directory in (self.settings_path, self.data_path):
            try:
                makedirs(directory, exist_ok=True)
            except Exception as e:
                log.critical(f"Unable to create {directory}: {e}")
                exit(2)

    # not implemented "ini/toml -> panda's internal format" converter yet, stub
    # TODO
    def load_settings(self):
        pass

    def load_leaderboards(self):
        """Load self.lb_file into self.leaderboards"""
        try:
            with open(self.lb_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            log.warning(f"Unable to find leaderboards file on {self.lb_file}")
            data = []
            # we may want to try to create empty file there, idk #TODO

        if data:
            # sorting list by internal scores, just to ensure its correct
            data.sort(key=(lambda x: x["score"]), reverse=True)

        self.leaderboards = data
        log.debug(f"Successfully loaded leaderboard into memory")

    # this is "leaderboard" and not "leaderboards", coz l8r we will add lb types
    # to specify in args #TODO
    def update_leaderboard(self, score: int, player_class: str, lb_length: int = 10):
        """Add new score to self.leaderboards, if its higher than old scores"""
        position = 0

        # ensuring lb isnt empty
        if self.leaderboards:
            # checking if score deserves to be on lb at all
            # this will crash if lb has incorrect format, but its okay since it
            # shouldnt be edited by hand
            if (
                len(self.leaderboards) >= lb_length
                and score <= self.leaderboards[-1]["score"]
            ):
                log.debug(f"{score} is too low, wont add to leaderboard")
                return

            for pos, item in enumerate(self.leaderboards):
                if score > item["score"]:
                    position = pos
                    break

        data = {}
        data["score"] = score
        data["player_class"] = player_class

        # add item to lb at specified position
        self.leaderboards.insert(position, data)

        # update leaderboard to cut unwanted parts
        self.leaderboards = self.leaderboards[:lb_length]
        log.debug(f"Successfully updated leaderboard with {data}")

    def save_leaderboards(self):
        """Save self.leaderboards into leaderboard.json"""
        with open(self.lb_file, "w") as f:
            json.dump(self.leaderboards, f)
            log.debug(f"Successfully saved leaderboard as {self.lb_file}")

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
from panda3d.core import loadPrcFileData
from Game import assets_loader
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
    """Load up settings and savefiles"""

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

    # #TODO: add support for custom config format and load it from disk
    def load_settings(self):
        """Load up engine's settings, to avoid depending on panda's defaults"""
        # First, lets set stuff from Confauto.prc, which wont be changed anyway
        loadPrcFileData(
            "default_settings",
            """
        load-file-type egg pandaegg
        load-file-type p3assimp
        load-audio-type * p3ffmpeg
        load-video-type * p3ffmpeg
        egg-object-type-portal          <Scalar> portal { 1 }
        egg-object-type-polylight       <Scalar> polylight { 1 }
        egg-object-type-seq24           <Switch> { 1 } <Scalar> fps { 24 }
        egg-object-type-seq12           <Switch> { 1 } <Scalar> fps { 12 }
        egg-object-type-indexed         <Scalar> indexed { 1 }
        egg-object-type-seq10           <Switch> { 1 } <Scalar> fps { 10 }
        egg-object-type-seq8            <Switch> { 1 } <Scalar> fps { 8 }
        egg-object-type-seq6            <Switch> { 1 } <Scalar>  fps { 6 }
        egg-object-type-seq4            <Switch> { 1 } <Scalar>  fps { 4 }
        egg-object-type-seq2            <Switch> { 1 } <Scalar>  fps { 2 }

        egg-object-type-binary          <Scalar> alpha { binary }
        egg-object-type-dual            <Scalar> alpha { dual }
        egg-object-type-glass           <Scalar> alpha { blend_no_occlude }
        egg-object-type-model           <Model> { 1 }
        egg-object-type-dcs             <DCS> { 1 }
        egg-object-type-notouch         <DCS> { no_touch }
        egg-object-type-barrier         <Collide> { Polyset descend }
        egg-object-type-sphere          <Collide> { Sphere descend }
        egg-object-type-invsphere       <Collide> { InvSphere descend }
        egg-object-type-tube            <Collide> { Tube descend }
        egg-object-type-trigger         <Collide> { Polyset descend intangible }
        egg-object-type-trigger-sphere  <Collide> { Sphere descend intangible }
        egg-object-type-floor           <Collide> { Polyset descend level }
        egg-object-type-dupefloor       <Collide> { Polyset keep descend level }
        egg-object-type-bubble          <Collide> { Sphere keep descend }
        egg-object-type-ghost           <Scalar> collide-mask { 0 }
        egg-object-type-glow            <Scalar> blend { add }
        load-file-type p3ptloader
        egg-object-type-direct-widget   <Scalar> collide-mask { 0x80000000 } <Collide> { Polyset descend }
        cull-bin gui-popup 60 unsorted
        default-model-extension .egg

        load-display pandagl
        aux-display p3headlessgl
        #load-display p3tinydisplay

        framebuffer-hardware #t
        framebuffer-software #f

        depth-bits 1
        color-bits 1 1 1
        alpha-bits 0
        stencil-bits 0
        multisamples 0

        model-path    $MAIN_DIR
        model-path    $THIS_PRC_DIR/..
        model-path    $THIS_PRC_DIR/../models

        want-directtools  #f
        want-tk           #f

        want-pstats            #f

        audio-library-name p3openal_audio

        use-movietexture #t

        hardware-animated-vertices #f

        model-cache-dir $XDG_CACHE_HOME/panda3d
        model-cache-textures #f

        basic-shaders-only #f

        # This makes window spawn on center of screen
        win-origin -2 -2
        """,
        )

        # Now lets load custom stuff that shouldnt be overriden
        loadPrcFileData(
            "hardcoded_settings",
            (
                # Notify levels of built-in messages. Defaults were "warning"
                "notify-level error\n"
                "default-directnotify-level error\n"
                # Disables autorescaling of textures, sides of which arent power
                # of 2. Which fixes the issue with ugly upscaled logo
                "textures-power-2 none\n"
                # Path to custom cursor. Must be .ico
                # If path-based settings are incorrect - engine will use default
                f"cursor-filename {join(assets_loader.UI_DIR, 'cursor.ico')}\n"
                # Custom font to be used everywhere instead of default
                f"text-default-font {join(assets_loader.FONTS_DIR, 'romulus.ttf')}\n"
            ),
        )

        # And then we load things that we may want to overwrite in future #TODO
        loadPrcFileData(
            "customizable_settings",
            """
        # This toggles up fps meter
        show-frame-rate-meter #f

        # This changes default window size
        win-size 800 600

        # This toggles fullscreen. You need to change #f to #t for that
        fullscreen #f
        """,
        )

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

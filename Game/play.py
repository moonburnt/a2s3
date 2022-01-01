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

# game launcher script

import logging

from Game.common import shared
from Game import game_window

import argparse

log = logging.getLogger()
log.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt="[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)

ap = argparse.ArgumentParser()
ap.add_argument(
    "--debug",
    action="store_true",
    help="Debug option. Adds debug messages to log output",
)
ap.add_argument(
    "--show-collisions",
    action="store_true",
    help="Debug option. Enable showcase of objects' collisions",
)
ap.add_argument(
    "--music-vol",
    type=int,
    help="Override default music volume. Should be between 0 and 100",
)
ap.add_argument(
    "--sfx-vol",
    type=int,
    help="Override default music volume. Should be between 0 and 100",
)
ap.add_argument("--show-fps", help="Enable fps meter", action="store_true")
ap.add_argument(
    "--window-x",
    type=int,
    help=(
        "Override window's X. Cant be less than " f"{shared.settings.window_size[0]}"
    ),
)
ap.add_argument(
    "--window-y",
    type=int,
    help=(
        "Override window's Y. Cant be less than " f"{shared.settings.window_size[1]}"
    ),
)
args = ap.parse_args()

if args.debug:
    log.setLevel(logging.DEBUG)

if args.show_collisions:
    shared.settings.show_collisions = True

if args.show_fps:
    shared.settings.fps_meter = True

if args.music_vol is not None and (0 <= args.music_vol <= 100):
    shared.settings.music_volume = args.music_vol / 100
    log.debug(f"Music volume has been set to {args.music_vol}%")

if args.sfx_vol is not None and (0 <= args.sfx_vol <= 100):
    shared.settings.sfx_volume = args.sfx_vol / 100
    log.debug(f"Music volume has been set to {args.sfx_vol}%")

if args.window_x and (args.window_x > shared.settings.window_size[0]):
    win_y = shared.settings.window_size[1]
    shared.settings.window_size = (args.window_x, win_y)

if args.window_y and (args.window_y > shared.settings.window_size[1]):
    win_x = shared.settings.window_size[0]
    shared.settings.window_size = (win_x, args.window_y)

play = game_window.GameWindow()
log.info("Running the game")
try:
    play.run()
except Exception as e:
    log.critical(e)
    exit(2)

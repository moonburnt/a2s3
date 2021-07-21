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

# The local equal of "Main"

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from Game.common import shared
from Game import assets_loader, level_loader, interface, music_manager

log = logging.getLogger(__name__)


class GameWindow(ShowBase):
    def __init__(self):
        log.debug("Setting up the window")
        super().__init__()

        loading = interface.LoadingScreen()
        shared.ui.add(loading, "loading")
        shared.ui.switch("loading")

        # disabling mouse to dont mess with camera
        self.disable_mouse()

        log.debug("Loading assets")
        shared.assets.load_all()

        log.debug("Initializing interface builder")
        shared.ui_builder = interface.builder.InterfaceBuilder(
            button_textures=(
                shared.assets.sprite["button"],
                shared.assets.sprite["button_active"],
                shared.assets.sprite["button_selected"],
            ),
            frame_texture=shared.assets.sprite["frame"],
            wide_frame_texture=shared.assets.sprite["frame_wide"],
            select_sfx=shared.assets.sfx["menu_select"],
            hover_sfx=shared.assets.sfx["menu_hover"],
            text_pos=(0, -8),
            text_scale=30,
        )

        log.debug("Loading user data")
        shared.user_data.load_leaderboards()

        log.debug("Configuring game's window")
        # setting up resolution
        screen_info = base.pipe.getDisplayInformation()
        # this is ugly, but it works, for now
        # basically we are ensuring that custom window's resolution isnt bigger
        # than screen size. And if yes - using default resolution instead

        # idk why, but these require at least something to display max available window size
        max_res = (
            screen_info.getDisplayModeWidth(0),
            screen_info.getDisplayModeHeight(0),
        )

        for cr, mr in zip(shared.settings.window_size, max_res):
            if cr > mr:
                log.warning(
                    "Requested resolution is bigger than screen size, "
                    "will use defaults instead"
                )
                shared.settings.window_size = shared.default_settings.window_size

        window_settings = WindowProperties()
        window_settings.set_size(shared.settings.window_size)

        # ensuring that window cant be resized by dragging its borders around
        window_settings.set_fixed_size(True)
        # toggling fullscreen/windowed mode
        window_settings.set_fullscreen(shared.settings.fullscreen)
        # setting window's title
        window_settings.set_title(shared.game_data.name)
        # applying settings to our window
        self.win.request_properties(window_settings)
        log.debug(f"Resolution has been set to {shared.settings.window_size}")

        # turning on fps meter, in case its enabled in settings
        base.setFrameRateMeter(shared.settings.fps_meter)

        # change background color to black. #TODO: move this to map generation,
        # make it possible to set to other values, aswell as pictures
        self.win.set_clear_color((0, 0, 0, 1))

        log.debug("Setting up the sound")
        # setting volume so it should apply to all music tracks
        # thats about where shared.settings break. I have no idea why, for now

        shared.music_player = music_manager.MusicPlayer()
        shared.music_player.set_player_volume(shared.settings.music_volume)

        # same goes for sfx manager, which is a separate thing
        shared.sfx_manager = base.sfxManagerList[0]
        shared.sfx_manager.set_volume(shared.settings.sfx_volume)

        shared.music_player.crossfade(shared.assets.music["menu_theme"])

        # TODO: create separate storage for scenes

        log.debug("Configuring UI")
        # these need to be this way, coz menu buttons dont accept activated funcs
        def update_scores():
            return shared.user_data.leaderboards

        leaderboard = interface.Leaderboard(
            back_command=shared.ui.show_previous,
            update_scores_command=update_scores,
        )

        shared.ui.add(leaderboard, "leaderboard")

        def show_lb():
            shared.ui.switch("leaderboard")

        def set_map():
            shared.ui.switch("map settings")

        def options():
            shared.ui.switch("options")

        main_menu = interface.MainMenu(
            play_command=set_map,
            show_leaderboard_command=show_lb,
            options_command=options,
            exit_command=self.exit_game,
            logo_img=shared.assets.sprite["logo"],
        )

        options_menu = interface.OptionsMenu(
            back_command=shared.ui.show_previous,
        )

        map_settings = interface.MapSettings(
            play_command=self.start_game,
            back_command=shared.ui.show_previous,
            player_classes=list(shared.assets.classes.keys()),
        )

        shared.ui.add(main_menu, "main")
        shared.ui.add(options_menu, "options")
        shared.ui.add(map_settings, "map settings")

        log.debug("Doing misc stuff")
        leaderboard.update_visible_scores()

        shared.ui.switch("main")

    def start_game(self, player_class, map_scale):
        """Hide main menu frame and load up the level"""
        log.debug("Loading up the level")
        # when I will remake assets loader to only load data necessary for current
        # scene, it will be usefull to call switch here to show loading screen
        # self.main_menu.hide()

        shared.level = level_loader.LoadLevel(player_class, map_scale)

    def exit_game(self):
        """Run whatever cleanup tasks and exit the game"""
        # TODO: maybe save up some stuff and remove unused garbage from memory?
        log.info("Exiting the game... Bye :(")
        shared.music_player.stop_all()
        # this doesnt have the snek case version
        base.userExit()

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

#The local equal of "Main"

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from Game import shared, assets_loader, level_loader, interface, music_player

log = logging.getLogger(__name__)

class GameWindow(ShowBase):
    def __init__(self):
        log.debug("Setting up the window")
        super().__init__()

        loading = interface.LoadingScreen()
        shared.ui.add(loading, "loading")
        shared.ui.switch("loading")

        #disabling mouse to dont mess with camera
        self.disable_mouse()

        log.debug("Loading assets")
        #self.assets = assets_loader.AssetsLoader()
        #shared.game_data.assets = assets_loader.AssetsLoader()
        shared.assets.load_all()

        log.debug("Configuring game's window")
        #setting up resolution
        screen_info = base.pipe.getDisplayInformation()
        #this is ugly, but it works, for now
        #basically we are ensuring that custom window's resolution isnt bigger
        #than screen size. And if yes - using default resolution instead

        #idk why, but these require at least something to display max available window size
        max_res = (screen_info.getDisplayModeWidth(0),
                   screen_info.getDisplayModeHeight(0))

        for cr, mr in zip(shared.WINDOW_SIZE, max_res):
            if cr > mr:
                log.warning("Requested resolution is bigger than screen size, "
                            "will use defaults instead")
                resolution = shared.DEFAULT_WINDOW_SIZE
                break
            else:
                resolution = shared.WINDOW_SIZE

        window_settings = WindowProperties()
        window_settings.set_size(resolution)

        #ensuring that window cant be resized by dragging its borders around
        window_settings.set_fixed_size(True)
        #toggling fullscreen/windowed mode
        window_settings.set_fullscreen(shared.FULLSCREEN)
        #setting window's title
        window_settings.set_title(shared.GAME_NAME)
        #applying settings to our window
        self.win.request_properties(window_settings)
        log.debug(f"Resolution has been set to {resolution}")

        log.debug("Setting up the sound")
        #setting volume so it should apply to all music tracks
        #self.music_player = music_player.MusicPlayer()
        #self.music_player.set_player_volume(shared.MUSIC_VOLUME)
        shared.game_data.music_player = music_player.MusicPlayer()
        shared.game_data.music_player.set_player_volume(shared.MUSIC_VOLUME)

        #same goes for sfx manager, which is a separate thing
        #self.sfx_manager = base.sfxManagerList[0]
        #self.sfx_manager.set_volume(shared.SFX_VOLUME)
        shared.game_data.sfx_manager = base.sfxManagerList[0]
        shared.game_data.sfx_manager.set_volume(shared.SFX_VOLUME)

        #self.music_player.crossfade(self.assets.music['menu_theme'])
        shared.game_data.music_player.crossfade(shared.assets.music['menu_theme'])

        #turning on fps meter, in case its enabled in settings
        base.setFrameRateMeter(shared.FPS_METER)

        #change background color to black. #TODO: move this to map generation,
        #make it possible to set to other values, aswell as pictures
        self.win.set_clear_color((0,0,0,1))

        #TODO: create separate storage for scenes

        #these need to be this way, coz menu buttons dont accept activated funcs
        def set_map():
            shared.ui.switch("map settings")

        def options():
            shared.ui.switch("options")

        def show_menu():
            shared.ui.switch("main")

        main_menu = interface.MainMenu(
                                play_command = set_map,
                                options_command = options,
                                exit_command = self.exit_game,
                                )

        options_menu = interface.OptionsMenu(
                                back_command = show_menu,
                                )

        map_settings = interface.MapSettings(
                                play_command = self.start_game,
                                back_command = show_menu,
                                            )

        shared.ui.add(main_menu, "main")
        shared.ui.add(options_menu, "options")
        shared.ui.add(map_settings, "map settings")

        shared.ui.switch("main")

    def start_game(self, player_class, map_scale):
        '''Hide main menu frame and load up the level'''
        log.debug("Loading up the level")
        #when I will remake assets loader to only load data necessary for current
        #scene, it will be usefull to call switch here to show loading screen
        #self.main_menu.hide()

        shared.level = level_loader.LoadLevel(player_class, map_scale)

    def exit_game(self):
        '''Run whatever cleanup tasks and exit the game'''
        #TODO: maybe save up some stuff and remove unused garbage from memory?
        log.info("Exiting the game... Bye :(")
        shared.game_data.music_player.stop_all()
        #this doesnt have the snek case version
        base.userExit()

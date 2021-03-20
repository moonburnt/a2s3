#thou shall be file where I do everything related to game rendering
#effectively "Main", ye

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from Game import shared, assets_loader, level_loader, interface

log = logging.getLogger(__name__)

class GameWindow(ShowBase):
    def __init__(self):
        log.debug("Setting up the window")
        ShowBase.__init__(self)

        #disabling mouse to dont mess with camera
        self.disable_mouse()

        log.debug("Loading assets")
        self.assets = assets_loader.AssetsLoader()

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
        #setting volume like that, so it should apply to all music tracks
        music_mgr = base.musicManager
        music_mgr.set_volume(shared.MUSIC_VOLUME)
        #same goes for sfx manager, which is a separate thing
        sfx_mgr = base.sfxManagerList[0]
        sfx_mgr.set_volume(shared.SFX_VOLUME)
        menu_theme = self.assets.music['menu_theme']
        menu_theme.set_loop(True)
        menu_theme.play()

        #turning on fps meter, in case its enabled in settings
        base.setFrameRateMeter(shared.FPS_METER)

        #change background color to black. #TODO: move this to map generation,
        #make it possible to set to other values, aswell as pictures
        self.win.set_clear_color((0,0,0,1))

        shared.start_game = self.start_game
        shared.exit_game = self.exit_game
        self.main_menu = interface.MainMenu()

    def start_game(self):
        '''Hide main menu frame and load up the level'''
        log.debug("Loading up the level")
        self.main_menu.hide()

        #todo: add all the configurable stuff there as init options, like map size and such
        self.level = level_loader.LoadLevel()

    def exit_game(self):
        '''Run whatever cleanup tasks and exit the game'''
        #TODO: maybe save up some stuff and remove unused garbage from memory?
        log.info("Exiting the game... Bye :(")
        #this doesnt have the snek case version
        base.userExit()

#thou shall be file where I do everything related to game rendering
#effectively "Main", ye

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from Game import config, assets_loader, level_loader

log = logging.getLogger(__name__)

class GameWindow(ShowBase):
    def __init__(self):
        log.debug("Setting up the window")
        ShowBase.__init__(self)

        #disabling mouse to dont mess with camera
        self.disable_mouse()

        log.debug("Loading assets")
        config.ASSETS = assets_loader.load_assets()
        self.assets = config.ASSETS

        log.debug("Configuring game's window")
        #setting up resolution
        screen_info = base.pipe.getDisplayInformation()
        #this is ugly, but it works, for now
        #basically we are ensuring that custom window's resolution isnt bigger
        #than screen size. And if yes - using default resolution instead

        #idk why, but these require at least something to display max available window size
        max_res = (screen_info.getDisplayModeWidth(0),
                   screen_info.getDisplayModeHeight(0))

        for cr, mr in zip(config.WINDOW_SIZE, max_res):
            if cr > mr:
                log.warning("Requested resolution is bigger than screen size, "
                            "will use defaults instead")
                resolution = config.DEFAULT_WINDOW_SIZE
                break
            else:
                resolution = config.WINDOW_SIZE

        window_settings = WindowProperties()
        window_settings.set_size(resolution)

        #ensuring that window cant be resized by dragging its borders around
        window_settings.set_fixed_size(True)
        #toggling fullscreen/windowed mode
        window_settings.set_fullscreen(config.FULLSCREEN)
        #setting window's title
        window_settings.set_title(config.GAME_NAME)
        #applying settings to our window
        self.win.request_properties(window_settings)
        log.debug(f"Resolution has been set to {resolution}")

        #change background color to black. #TODO: move this to map generation,
        #make it possible to set to other values, aswell as pictures
        self.win.set_clear_color((0,0,0,1))

        #todo: add all the configurable stuff there as init options, like map size and such
        self.level = level_loader.LoadLevel()

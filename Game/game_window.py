#thou shall be file where I do everything related to game rendering
#effectively "Main", ye

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, NodePath
from Game import config, assets_loader, level_loader
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenImage import OnscreenImage

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

        log.debug("Setting up the sound")
        #setting volume like that, so it should apply to all music tracks
        music_mgr = base.musicManager
        music_mgr.set_volume(config.MUSIC_VOLUME)
        #same goes for sfx manager, which is a separate thing
        sfx_mgr = base.sfxManagerList[0]
        sfx_mgr.set_volume(config.SFX_VOLUME)
        menu_theme = self.assets.music['menu_theme']
        menu_theme.set_loop(True)
        menu_theme.play()

        #turning on fps meter, in case its enabled in settings
        base.setFrameRateMeter(config.FPS_METER)

        #change background color to black. #TODO: move this to map generation,
        #make it possible to set to other values, aswell as pictures
        self.win.set_clear_color((0,0,0,1))

        self.main_menu = NodePath("main menu")
        #reparenting this thing to pixel2d make buttons scale pixel-perfectly.
        #In case scale equals image size, obviously.
        #On other side, it adds requirement to manually calculate position based
        #on window's size, since with pixel2d placement of items is calculated
        #not from center, but from top left corner of window
        self.main_menu.reparent_to(pixel2d)
        self.main_menu.show()

        #basically, the thing is - directgui can automatically assign multiple
        #textures to different button's events, if they are passed as list or
        #tuple in correct order. And thats what we are doing there
        self.button_textures = (self.assets.sprite['button'],
                                self.assets.sprite['button_active'],
                                self.assets.sprite['button_selected'])

        self.game_logo = OnscreenImage(image = self.assets.sprite['logo'],
                                       scale = (122, 1, 53),
                                       pos = (150, 1, -100),
                                       parent = self.main_menu)

        #not assigning "self" stuff, coz Im not referring to these from elsewhere
        start_button = DirectButton(text = "Play",
                                    command = self.start_game,
                                    pos = (150, 1, -300),
                                    text_scale = 1,
                                    text_pos = (0,-0.25),
                                    scale = (64, 1, 32),
                                    frameTexture = self.button_textures,
                                    frameSize = (-2, 2, -1, 1),
                                    parent = self.main_menu)

        exit_button = DirectButton(text = "Exit",
                                   command = self.exit_game,
                                   pos = (150, 1, -400),
                                   text_pos = (0,-0.25),
                                   scale = (64, 1, 32),
                                   frameTexture = self.button_textures,
                                   frameSize = (-2, 2, -1, 1),
                                   parent = self.main_menu)

        #enabling transparency to all buttons in main_menu
        self.main_menu.set_transparency(True)

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

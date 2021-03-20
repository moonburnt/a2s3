#module for various huds

import logging
from panda3d.core import NodePath
from direct.gui.DirectGui import DirectButton, DirectLabel
from direct.gui.OnscreenText import OnscreenText, TextNode
from direct.gui.OnscreenImage import OnscreenImage

from Game import shared

log = logging.getLogger(__name__)

class Menu:
    '''Main class for all huds and menus. Require nodepath name to be passed as
    argument during initialization process'''
    def __init__(self, name, parent = None):
        if not parent:
            parent = base.aspect2d
        #"frame" is nodepath object, to which everything else will be attached
        #doing things this way will make it possible to toggle gui elements
        #together, aswell as apply some properties to all of them at once
        self.frame = NodePath(name)

        #reparenting this thing to pixel2d make buttons scale pixel-perfectly.
        #In case scale equals image size, obviously.
        #On other side, it adds requirement to manually calculate position based
        #on window's size, since with pixel2d placement of items is calculated
        #not from center, but from top left corner of window
        self.frame.reparent_to(parent)

        #enabling transparency to all buttons in menu
        self.frame.set_transparency(True)

        #basically, the thing is - directgui can automatically assign multiple
        #textures to different button's events, if they are passed as list or
        #tuple in correct order. And thats what we are doing there
        self.button_textures = (base.assets.sprite['button'],
                                base.assets.sprite['button_active'],
                                base.assets.sprite['button_selected'])

    #I dont actually need to attach these, but doing so will make toggling class easier
    def hide(self):
        self.frame.hide()

    def show(self):
        self.frame.show()

class MainMenu(Menu):
    def __init__(self):
        name = "main menu"
        parent = base.pixel2d
        super().__init__(name, parent)
        # self.main_menu = NodePath("main menu")
        # #reparenting this thing to pixel2d make buttons scale pixel-perfectly.
        # #In case scale equals image size, obviously.
        # #On other side, it adds requirement to manually calculate position based
        # #on window's size, since with pixel2d placement of items is calculated
        # #not from center, but from top left corner of window
        # self.main_menu.reparent_to(pixel2d)
        # self.main_menu.show()

        self.game_logo = OnscreenImage(image = base.assets.sprite['logo'],
                                       scale = (122, 1, 53),
                                       pos = (150, 1, -100),
                                       parent = self.frame)

        #not assigning "self" stuff, coz Im not referring to these from elsewhere
        start_button = DirectButton(text = "Play",
                                    command = shared.start_game,
                                    pos = (150, 1, -300),
                                    text_scale = 1,
                                    text_pos = (0,-0.25),
                                    scale = (64, 1, 32),
                                    frameTexture = self.button_textures,
                                    frameSize = (-2, 2, -1, 1),
                                    parent = self.frame)

        exit_button = DirectButton(text = "Exit",
                                   command = shared.exit_game,
                                   pos = (150, 1, -400),
                                   text_pos = (0,-0.25),
                                   scale = (64, 1, 32),
                                   frameTexture = self.button_textures,
                                   frameSize = (-2, 2, -1, 1),
                                   parent = self.frame)

class DeathScreen(Menu):
    '''Screen shown on player's death'''
    def __init__(self):
        name = "death screen"
        parent = base.aspect2d
        super().__init__(name, parent)

        self.high_score = DirectLabel(text = "Your score is 0",
                                      pos = (0, 0, 0.1),
                                      scale = 0.1,
                                      frameTexture = base.assets.sprite['frame'],
                                      frameSize = (-4.5, 4.5, -0.5, 1),
                                      parent = self.frame)

        self.restart_button = DirectButton(text = "Restart",
                                           command = shared.restart_level,
                                           pos = (0, 0, -0.1),
                                           scale = 0.1,
                                           frameTexture = self.button_textures,
                                           frameSize = (-3, 3, -0.5, 1),
                                           parent = self.frame)

        self.exit_level_button = DirectButton(text = "Back to Menu",
                                              command = shared.exit_level,
                                              pos = (0, 0, -0.3),
                                              scale = 0.1,
                                              frameTexture = self.button_textures,
                                              frameSize = (-3, 3, -0.5, 1),
                                              parent = self.frame)

        self.exit_button = DirectButton(text = "Exit",
                                        command = shared.exit_game,
                                        pos = (0, 0, -0.5),
                                        scale = 0.1,
                                        frameTexture = self.button_textures,
                                        frameSize = (-3, 3, -0.5, 1),
                                        parent = self.frame)

    def update_score(self, value):
        '''Change dispayed self.high_score to provided value'''
        self.high_score.setText(f"Your score is {value}")

class PlayerHUD(Menu):
    '''Player's hud, displayed in game. Wave counter, player's hp, etc'''
    def __init__(self):
        name = "player hud"
        parent = base.aspect2d
        super().__init__(name, parent)

        #create white-colored text with player's hp above player's head
        #TODO: maybe move it to top left, add some image on background
        self.player_hp = OnscreenText(text = str(0),
                                      pos = (0, 0.01),
                                      scale = 0.05,
                                      fg = (1,1,1,1),
                                      parent = self.frame,
                                      mayChange = True)

        self.score = OnscreenText(text = "Score: 0",
                                  pos = (-1.7, 0.9),
                                  #alignment side may look non-obvious, depending
                                  #on position and text it applies to
                                  align = TextNode.ALeft,
                                  scale = 0.05,
                                  fg = (1,1,1,1),
                                  parent = self.frame,
                                  mayChange = True)

        #visually it should be below score itself... I think?
        self.score_multiplier = OnscreenText(text = "Multiplier: 1",
                                             pos = (-1.7, 0.85),
                                             align = TextNode.ALeft,
                                             scale = 0.05,
                                             fg = (1,1,1,1),
                                             parent = self.frame,
                                             mayChange = True)

        #this one should be displayed on right... I think?
        self.enemy_amount = OnscreenText(text = "Enemies Left: 0",
                                         pos = (1.7, 0.85),
                                         align = TextNode.ARight,
                                         scale = 0.05,
                                         fg = (1,1,1,1),
                                         parent = self.frame,
                                         mayChange = True)

    def update_hp(self, value):
        '''Update self.player_hp to provided value'''
        self.player_hp.setText(str(value))

    def update_score(self, value):
        self.score.setText(f"Score: {value}")

    def update_multiplier(self, value):
        self.score_multiplier.setText(f"Multiplier: {value}")

    def update_enemy_counter(self, value):
        self.enemy_amount.setText(f"Enemies Left: {value}")

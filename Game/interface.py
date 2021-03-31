#module for various huds

import logging
from panda3d.core import NodePath
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectOptionMenu
from direct.gui.OnscreenText import OnscreenText, TextNode
from direct.gui.OnscreenImage import OnscreenImage

from Game import shared

log = logging.getLogger(__name__)

CURRENT_INTERFACE = None

def switch(menu):
    '''Switch CURRENT_INTERFACE menu to one passed as argument'''
    #this is kind of nasty thing. But if used correctly, it should allow to easily
    #switch active interfaces from one to another, in case only one can exist at
    #given time. Manual usage of hide/show functions still make sense, in case
    #some guis need to coexist
    global CURRENT_INTERFACE
    if CURRENT_INTERFACE:
        CURRENT_INTERFACE.hide()
    CURRENT_INTERFACE = menu
    menu.show()

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

        self.hover_sfx = base.assets.sfx['menu_hover']
        self.select_sfx = base.assets.sfx['menu_select']

        #this will change the default behavior of menus, but to me it will make
        #things more convenient. E.g if you need to show something - do it manually
        self.hide()

    #I dont actually need to attach these, but doing so will make toggling class easier
    def hide(self):
        self.frame.hide()

    def show(self):
        self.frame.show()

class MainMenu(Menu):
    def __init__(self, play_command, exit_command):
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
                                    command = play_command,
                                    pos = (150, 1, -300),
                                    text_scale = 1,
                                    text_pos = (0,-0.25),
                                    scale = (64, 1, 32),
                                    frameTexture = self.button_textures,
                                    frameSize = (-2, 2, -1, 1),
                                    clickSound = self.select_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame)

        exit_button = DirectButton(text = "Exit",
                                   command = exit_command,
                                   pos = (150, 1, -400),
                                   text_pos = (0,-0.25),
                                   scale = (64, 1, 32),
                                   frameTexture = self.button_textures,
                                   frameSize = (-2, 2, -1, 1),
                                   clickSound = self.select_sfx,
                                   rolloverSound = self.hover_sfx,
                                   parent = self.frame)

class MapSettings(Menu):
    '''Menu where player can change map scale and other things'''
    def __init__(self, play_command, back_command):
        name = "map settings"
        parent = base.aspect2d
        super().__init__(name, parent)

        self.play_command = play_command
        self.map_scale = 1
        #this is extremely stupid, but this thing require strings, not ints
        self.map_scales = ["1", "2", "3", "4", "5"]

        selection_title = DirectLabel(text = "Map Scale:",
                                      pos = (0, 0, 0.3),
                                      scale = 0.1,
                                      frameTexture = base.assets.sprite['frame'],
                                      frameSize = (-3, 3, -0.5, 1),
                                      parent = self.frame)

        #this thing looks ugly and there seem to be no way to apply texture to
        #popup list. TODO: make a custom bicycle to handle that functionality

        #also this thing doesnt show text. Ehh...
        map_scale_selection = DirectOptionMenu(
                                    command = self.update_map_scale,
                                    items = self.map_scales,
                                    initialitem = 0,
                                    pos = (0, 0, 0.1),
                                    popupMarker_scale = 0.1,
                                    scale = 0.1,
                                    frameTexture = self.button_textures,
                                    frameSize = (-3, 3, -0.5, 1),
                                    #clickSound = self.select_sfx,
                                    clickSound = self.hover_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame)

        start_button = DirectButton(text = "Play",
                                    command = self.run_level,
                                    pos = (0.3, 0, -0.1),
                                    scale = 0.1,
                                    frameTexture = self.button_textures,
                                    frameSize = (-3, 3, -0.5, 1),
                                    clickSound = self.select_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame)

        back_button = DirectButton(text = "Back",
                                    command = back_command,
                                    pos = (-0.3, 0, -0.1),
                                    scale = 0.1,
                                    frameTexture = self.button_textures,
                                    frameSize = (-3, 3, -0.5, 1),
                                    clickSound = self.select_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame)

    def update_map_scale(self, scale):
        self.map_scale = scale
        log.info(f"Map scale has been set to {self.map_scale}")

    def run_level(self):
        #this is done like that, because this stupid gui framework cant even
        #autopick updated self.map_scale value. Gross
        map_scale = int(self.map_scale)
        self.play_command(map_scale)

class DeathScreen(Menu):
    '''Screen shown on player's death'''
    def __init__(self, restart_command, exit_level_command, exit_game_command):
        name = "death screen"
        parent = base.aspect2d
        super().__init__(name, parent)

        #not setting text, coz it will be overwritten anyway
        #TODO: set align to be on left. Maybe replae death_message's DirectLabel
        #with OnscreenText and draw frame on background?
        self.death_message = DirectLabel(
                                      pos = (0, 0, 0.3),
                                      scale = 0.1,
                                      frameTexture = base.assets.sprite['frame'],
                                      frameSize = (-4.5, 4.5, -2.5, 1),
                                      parent = self.frame)

        self.restart_button = DirectButton(text = "Restart",
                                           command = restart_command,
                                           pos = (0, 0, -0.1),
                                           scale = 0.1,
                                           frameTexture = self.button_textures,
                                           frameSize = (-3, 3, -0.5, 1),
                                           clickSound = self.select_sfx,
                                           rolloverSound = self.hover_sfx,
                                           parent = self.frame)

        self.exit_level_button = DirectButton(text = "Back to Menu",
                                              command = exit_level_command,
                                              pos = (0, 0, -0.3),
                                              scale = 0.1,
                                              frameTexture = self.button_textures,
                                              frameSize = (-3, 3, -0.5, 1),
                                              clickSound = self.select_sfx,
                                              rolloverSound = self.hover_sfx,
                                              parent = self.frame)

        self.exit_button = DirectButton(text = "Exit",
                                        command = exit_game_command,
                                        pos = (0, 0, -0.5),
                                        scale = 0.1,
                                        frameTexture = self.button_textures,
                                        frameSize = (-3, 3, -0.5, 1),
                                        clickSound = self.select_sfx,
                                        rolloverSound = self.hover_sfx,
                                        parent = self.frame)

    def update_death_message(self, score: int, wave: int, killed: int):
        '''Change dispayed self.high_score to provided value'''
        self.death_message.setText(f"Score: {score}\n"
                                   f"Last Wave: {wave}\n"
                                   f"Enemies Killed: {killed}")

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

        #these should be displayer on right, I think
        #visually it should be below score itself... I think?
        self.current_wave = OnscreenText(text = "Current Wave: 0",
                                         pos = (1.7, 0.9),
                                         #pos = (1.35, 0.9),
                                         align = TextNode.ARight,
                                         #align = TextNode.ALeft,
                                         scale = 0.05,
                                         fg = (1,1,1,1),
                                         parent = self.frame,
                                         mayChange = True)

        self.enemy_amount = OnscreenText(text = "Enemies Left: 0",
                                         pos = (1.7, 0.85),
                                         #pos = (1.35, 0.85),
                                         align = TextNode.ARight,
                                         #align = TextNode.ALeft,
                                         scale = 0.05,
                                         fg = (1,1,1,1),
                                         parent = self.frame,
                                         mayChange = True)

        #idk if these should be there or on separate hud, but for now will keep em
        self.wave_cleared_msg = OnscreenText(text = "Wave Cleared!",
                                         pos = (0, 0.85),
                                         align = TextNode.ACenter,
                                         scale = 0.1,
                                         fg = (1,1,1,1),
                                         parent = self.frame,
                                         mayChange = True)
        self.wave_cleared_msg.hide()

        self.new_wave_msg = OnscreenText(text = "Wave 0",
                                         pos = (0, 0.85),
                                         align = TextNode.ACenter,
                                         scale = 0.1,
                                         fg = (1,1,1,1),
                                         parent = self.frame,
                                         mayChange = True)
        self.new_wave_msg.hide()

        self.kill_requirement_msg = OnscreenText(text = "Kill 0 Enemies To Proceed",
                                         pos = (0, 0.75),
                                         align = TextNode.ACenter,
                                         scale = 0.05,
                                         fg = (1,1,1,1),
                                         parent = self.frame,
                                         mayChange = True)
        self.kill_requirement_msg.hide()

    def show_wave_cleared(self):
        '''Inform player that wave has been cleared, then hide message after 2 secs'''
        #TODO: rename this function to something less stupid

        #this can probably be done with lerp intervals, but I currently have no
        #access to panda docs to find out how to do that properly
        log.debug("Showing 'wave cleared' message")
        self.wave_cleared_msg.show()

        def wave_hide_task(event):
            self.wave_cleared_msg.hide()
            return

        base.task_mgr.do_method_later(2, wave_hide_task, "hide 'wave cleared' msg")

    def show_new_wave_msg(self, wave_number: int, kill_requirement: int):
        '''Inform player that new wave has started and how many enemies they need
        to kill to proceed further'''
        log.debug("Showing new wave messages")
        self.new_wave_msg.setText(f"Wave {wave_number}")
        self.kill_requirement_msg.setText(f"Kill {kill_requirement} Enemies To Proceed")
        self.new_wave_msg.show()
        self.kill_requirement_msg.show()

        #this function is hidden inside, coz we have no use for it outside
        def wave_hide_task(event):
            self.new_wave_msg.hide()
            self.kill_requirement_msg.hide()
            return

        base.task_mgr.do_method_later(2.5, wave_hide_task, "hide 'new wave' msg")

    def update_hp(self, value: int):
        '''Update self.player_hp to provided value'''
        self.player_hp.setText(str(value))

    def update_score(self, value: int):
        '''Update self.score to provided value'''
        self.score.setText(f"Score: {value}")

    def update_multiplier(self, value: float):
        '''Update selt.score_multiplier to provided value'''
        self.score_multiplier.setText(f"Multiplier: {value}")

    def update_enemy_counter(self, value: int):
        '''Update self.enemy_amount to provided value'''
        self.enemy_amount.setText(f"Enemies Left: {value}")

    def update_current_wave(self, value: int):
        '''Update self.current_wave to provided value'''
        self.current_wave.setText(f"Current Wave: {value}")

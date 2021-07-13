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

#module for various huds

import logging
from panda3d.core import NodePath
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectOptionMenu, DirectSlider
from direct.gui.OnscreenText import OnscreenText, TextNode
from direct.gui.OnscreenImage import OnscreenImage
from .parts import *
from Game import shared

log = logging.getLogger(__name__)

class MainMenu(Menu):
    def __init__(self, play_command, show_leaderboard_command,
                                options_command, exit_command):
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

        self.game_logo = OnscreenImage(
                                    image = shared.assets.sprite['logo'],
                                    scale = (122, 1, 53),
                                    pos = (150, 1, -100),
                                    parent = self.frame,
                                    )

        #not assigning "self" stuff, coz Im not referring to these from elsewhere
        start_button = DirectButton(
                                    text = "Play",
                                    command = play_command,
                                    pos = (150, 1, -300),
                                    text_scale = 0.8,
                                    text_pos = (0,-0.25),
                                    scale = (64, 1, 32),
                                    frameTexture = self.button_textures,
                                    frameSize = (-2, 2, -1, 1),
                                    clickSound = self.select_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame,
                                    )

        options_button = DirectButton(
                                    text = "Options",
                                    command = options_command,
                                    pos = (150, 1, -400),
                                    text_scale = 0.8,
                                    text_pos = (0, -0.25),
                                    scale = (64, 1, 32),
                                    frameTexture = self.button_textures,
                                    frameSize = (-2, 2, -1, 1),
                                    clickSound = self.select_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame,
                                    )

        show_lb_button = DirectButton(
                                    text = "Leaderboard",
                                    command = show_leaderboard_command,
                                    pos = (150, 1, -500),
                                    text_scale = 0.8,
                                    text_pos = (0, -0.25),
                                    scale = (64, 1, 32),
                                    frameTexture = self.button_textures,
                                    frameSize = (-2, 2, -1, 1),
                                    clickSound = self.select_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame,
                                    )

        exit_button = DirectButton(
                                    text = "Exit",
                                    command = exit_command,
                                    pos = (150, 1, -600),
                                    text_scale = 0.8,
                                    text_pos = (0,-0.25),
                                    scale = (64, 1, 32),
                                    frameTexture = self.button_textures,
                                    frameSize = (-2, 2, -1, 1),
                                    clickSound = self.select_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame,
                                    )

class OptionsMenu(Menu):
    '''Options menu where player can change game options such as volume.'''

    def __init__(self, back_command):
        super().__init__("options menu", base.aspect2d)

        self.back_command = back_command

        # Current value, updated via sliders
        self.music_volume = shared.settings.music_volume
        self.sfx_volume = shared.settings.sfx_volume
        # Save them to restore if player clicks 'back' without saving
        self.old_music_volume = shared.settings.music_volume
        self.old_sfx_volume = shared.settings.sfx_volume

        options_label = DirectLabel(text = "Options",
                                    pos = (0, 0, 0.8),
                                    scale = 0.1,
                                    frameTexture = shared.assets.sprite["frame"],
                                    frameSize = (-3, 3, -0.5, 1),
                                    parent = self.frame)

        music_label = DirectLabel(text = "Music",
                                  pos = (-0.5, 0, 0.5),
                                  scale = 0.1,
                                  frameTexture = shared.assets.sprite["frame"],
                                  frameSize = (-3, 3, -0.5, 1),
                                  parent = self.frame)

        self.music_slider = DirectSlider(pos = (0.3, 0, 0.5),
                                         scale = 0.4,
                                         parent = self.frame,
                                         value = shared.settings.music_volume,
                                         command = self.update_music_volume)

        sfx_label = DirectLabel(text = "SFX",
                                pos = (-0.5, 0, 0.2),
                                scale = 0.1,
                                frameTexture = shared.assets.sprite["frame"],
                                frameSize = (-3, 3, -0.5, 1),
                                parent = self.frame)

        self.sfx_slider = DirectSlider(pos = (0.3, 0, 0.2),
                                       scale = 0.4,
                                       parent = self.frame,
                                       value = shared.settings.sfx_volume,
                                       command = self.update_sfx_volume)

        ok_button = DirectButton(text = "Ok",
                                 command = self.save_and_close,
                                 pos = (-0.3, 0, -0.3),
                                 scale = 0.1,
                                 frameTexture = self.button_textures,
                                 frameSize = (-3, 3, -0.5, 1),
                                 clickSound = self.select_sfx,
                                 rolloverSound = self.hover_sfx,
                                 parent = self.frame)

        back_button = DirectButton(text = "Back",
                                    command = self.restore_and_close,
                                    pos = (0.4, 0, -0.3),
                                    scale = 0.1,
                                    frameTexture = self.button_textures,
                                    frameSize = (-3, 3, -0.5, 1),
                                    clickSound = self.select_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame)

    def save_and_close(self):
        '''Save options and return to parent menu.'''

        log.info("Saving options...")
        shared.settings.music_volume = self.music_volume
        shared.settings.sfx_volume = self.sfx_volume

        self.old_music_volume = self.music_volume
        self.old_sfx_volume = self.sfx_volume

        self.back_command()

    def restore_and_close(self):
        '''Restore previous options' values and return to parent menu.'''

        shared.music_player.set_player_volume(self.old_music_volume)
        shared.sfx_manager.set_volume(self.old_sfx_volume)

        self.music_slider.setValue(self.old_music_volume)
        self.sfx_slider.setValue(self.old_sfx_volume)

        self.back_command()

    def update_music_volume(self):
        self.music_volume = self.music_slider["value"]
        shared.music_player.set_player_volume(self.music_volume)

    def update_sfx_volume(self):
        self.sfx_volume = self.sfx_slider["value"]
        shared.sfx_manager.set_volume(self.sfx_volume)

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

        #this will probably crash on no classes... but, like - you wont be able
        #to play anyway at this point, so why bother?
        self.player_class = list(shared.assets.classes.keys())[0]
        self.player_classes = list(shared.assets.classes.keys())

        #this is placeholder too. Maybe I should even move it to separate screen?
        #it may be also good idea to right away check if class has all the necessary
        #data (and wont crash the game) and only then allow it there. But idk if
        #checks should be done there or during assets loading. Prolly second. #TODO
        class_selection_title = DirectLabel(text = "Player Class:",
                                      pos = (0, 0, 0.7),
                                      scale = 0.1,
                                      frameTexture = shared.assets.sprite['frame'],
                                      frameSize = (-3, 3, -0.5, 1),
                                      parent = self.frame)

        class_selection = DirectOptionMenu(
                                    command = self.select_class,
                                    items = self.player_classes,
                                    initialitem = 0,
                                    pos = (0, 0, 0.5),
                                    #idk how to set align to this thing properly,
                                    #coz the most obvious arg refuses to work.
                                    #wont even bother, since its temporary ui
                                    #anyway and should be replaced with proper
                                    #self-made carousel later. #TODO
                                    text_pos = (-2.5, 0, 0),
                                    popupMarker_scale = 0.1,
                                    scale = 0.1,
                                    frameTexture = self.button_textures,
                                    frameSize = (-3, 3, -0.5, 1),
                                    #clickSound = self.select_sfx,
                                    clickSound = self.hover_sfx,
                                    rolloverSound = self.hover_sfx,
                                    parent = self.frame)

        map_selection_title = DirectLabel(text = "Map Scale:",
                                      pos = (0, 0, 0.3),
                                      scale = 0.1,
                                      frameTexture = shared.assets.sprite['frame'],
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

    #TODO: add something like "reset:bool" flag that will set up reset policy in
    #case we switch to other interface. Coz right now we need to do it manually
    #(see options menu), and Im tired of it, thus wont bother adding there. For now

    def select_class(self, classname):
        self.player_class = classname
        log.info(f"Player class has been set to {self.player_class}")

    def update_map_scale(self, scale):
        self.map_scale = scale
        log.info(f"Map scale has been set to {self.map_scale}")

    def run_level(self):
        #this is done like that, because this stupid gui framework cant even
        #autopick updated self.map_scale value. Gross
        map_scale = int(self.map_scale)
        self.play_command(player_class = self.player_class,
                          map_scale = map_scale)

class DeathScreen(Menu):
    '''Screen shown on player's death'''
    def __init__(self, show_leaderboard_command, restart_command,
                       exit_level_command, exit_game_command):
        name = "death screen"
        parent = base.aspect2d
        super().__init__(name, parent)

        #not setting text, coz it will be overwritten anyway
        #TODO: set align to be on left. Maybe replae death_message's DirectLabel
        #with OnscreenText and draw frame on background?
        self.death_message = DirectLabel(
                            pos = (0, 0, 0.3),
                            scale = 0.1,
                            frameTexture = shared.assets.sprite['frame'],
                            frameSize = (-4.5, 4.5, -2.5, 1),
                            parent = self.frame,
                            )

        self.restart_button = DirectButton(
                            text = "Restart",
                            command = restart_command,
                            pos = (0, 0, -0.1),
                            scale = 0.1,
                            frameTexture = self.button_textures,
                            frameSize = (-3, 3, -0.5, 1),
                            clickSound = self.select_sfx,
                            rolloverSound = self.hover_sfx,
                            parent = self.frame,
                            )

        self.show_lb_button = DirectButton(
                            text = "Leaderboards",
                            command = show_leaderboard_command,
                            pos = (0, 0, -0.3),
                            scale = 0.1,
                            frameTexture = self.button_textures,
                            frameSize = (-3, 3, -0.5, 1),
                            clickSound = self.select_sfx,
                            rolloverSound = self.hover_sfx,
                            parent = self.frame,
                            )

        self.exit_level_button = DirectButton(
                            text = "Back to Menu",
                            command = exit_level_command,
                            pos = (0, 0, -0.5),
                            scale = 0.1,
                            frameTexture = self.button_textures,
                            frameSize = (-3, 3, -0.5, 1),
                            clickSound = self.select_sfx,
                            rolloverSound = self.hover_sfx,
                            parent = self.frame,
                            )

        self.exit_button = DirectButton(
                            text = "Exit",
                            command = exit_game_command,
                            pos = (0, 0, -0.7),
                            scale = 0.1,
                            frameTexture = self.button_textures,
                            frameSize = (-3, 3, -0.5, 1),
                            clickSound = self.select_sfx,
                            rolloverSound = self.hover_sfx,
                            parent = self.frame,
                            )

        #idk if this should be there either. But will do for now
        self.dn_duration = 2

        #notice how its parent is different
        self.death_notification = Popup(
                            text = "Death",
                            text_scale = 0.5,
                            parent = base.aspect2d,
                            duration = self.dn_duration,
                            )

    def update_death_message(self, score: int, wave: int, killed: int):
        '''Change dispayed self.high_score to provided value'''
        self.death_message.setText(f"Score: {score}\n"
                                   f"Last Wave: {wave}\n"
                                   f"Enemies Killed: {killed}")

    def show(self):
        #Overriding default "show" function, to first show death message and
        #only then display the highscores/restart menu

        #I need to specify it there, coz super cant handle calling for functions
        #of parent class from multi-layered function
        sup = super().show

        def show_frame(event):
            sup()
            return

        self.death_notification.show()
        base.task_mgr.do_method_later(self.dn_duration, show_frame, "show death screen")

class PlayerHUD(Menu):
    '''Player's hud, displayed in game. Wave counter, player's hp, etc'''
    def __init__(self):
        name = "player hud"
        parent = base.aspect2d
        super().__init__(name, parent)

        #create white-colored text with player's hp above player's head
        #TODO: maybe move it to top left, add some image on background
        self.player_hp = OnscreenText(text = str(0),
                                      pos = (0, 0.05),
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
        #also idk about styling. I tried to make it look somehow ok, but idk
        self.wave_cleared_msg =     Popup(
                                         text = "Wave Cleared!",
                                         text_pos = (0, 0.85),
                                         text_scale = 0.1,
                                         parent = self.frame,
                                         duration = 2
                                         )

        self.new_wave_msg =         Popup(
                                         text_pos = (0, 0.85),
                                         text_scale = 0.1,
                                         parent = self.frame,
                                         duration = 2.5
                                         )

        self.kill_requirement_msg = Popup(
                                         text_pos = (0, 0.75),
                                         text_scale = 0.05,
                                         parent = self.frame,
                                         duration = 2.5
                                         )

    def show_new_wave_msg(self, wave_number: int, kill_requirement: int):
        '''Inform player that new wave has started and how many enemies they need
        to kill to proceed further'''
        log.debug("Showing new wave messages")
        self.new_wave_msg.set_text(f"Wave {wave_number}")
        self.kill_requirement_msg.set_text(f"Kill {kill_requirement} Enemies To Proceed")
        self.new_wave_msg.show()
        self.kill_requirement_msg.show()

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

#TODO: create new "table" class, use it instead of having to place stuff manually
class Leaderboard(Menu):
    def __init__(self, back_command, update_scores_command):
        name = "leaderboard"
        parent = base.aspect2d
        super().__init__(name, parent)

        self.update_scores_command = update_scores_command

        title = DirectLabel(
                            text = "Leaderboard",
                            pos = (0, 0, 0.7),
                            scale = 0.1,
                            frameTexture = shared.assets.sprite['frame'],
                            frameSize = (-4.5, 4.5, -1, 1),
                            parent = self.frame,
                            )

        labels_frame = DirectLabel(
                            pos = (0, 0, 0.1),
                            scale = 0.1,
                            frameTexture = shared.assets.sprite['frame'],
                            frameSize = (-7, 7, -4.5, 4.5),
                            parent = self.frame,
                            )

        self.scores = []

        y = 3.4
        #coz we have 10 leaderboard items
        for num in range(0, 10):
            score_label = OnscreenText(
                            text = "",
                            pos = (0, y),
                            scale = 0.7,
                            parent = labels_frame,
                            )

            self.scores.append(score_label)
            #decrease height of message with each new item, to add it under prev
            y -= 0.8

        self.back_button = DirectButton(
                            text = "Back",
                            #TODO: maybe make ui switcher save last shown screen?
                            command = back_command,
                            pos = (0, 0, -0.7),
                            scale = 0.1,
                            frameTexture = self.button_textures,
                            frameSize = (-3, 3, -0.5, 1),
                            clickSound = self.select_sfx,
                            rolloverSound = self.hover_sfx,
                            parent = self.frame,
                            )

    def update_visible_scores(self):
        """Update score labels"""
        leaderboards = self.update_scores_command()
        if not leaderboards:
            return

        #this will break if length of lb is bigger than local score table
        for num, value in enumerate(leaderboards):
            #I could prolly write it in one line instead #TODO
            label = self.scores[num]
            score = value['score']
            player = value['player_class']
            pos = num+1
            text = f"{pos}. Score: {score} Class: {player}"
            label.setText(text)


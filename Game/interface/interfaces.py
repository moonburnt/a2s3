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

# module for various huds

import logging
from panda3d.core import NodePath
from direct.gui.OnscreenText import OnscreenText, TextNode
from direct.gui.OnscreenImage import OnscreenImage
from .parts import *
from Game import shared

log = logging.getLogger(__name__)


class MainMenu(Menu):
    """Game's main menu, appearing right after launch"""

    def __init__(
        self,
        play_command,
        show_leaderboard_command,
        options_command,
        exit_command,
        logo_img,
    ):
        super().__init__("main menu", base.pixel2d)

        # reparenting this thing to pixel2d make buttons scale pixel-perfectly.
        # In case scale equals image size, obviously.
        # On other side, it adds requirement to manually calculate position based
        # on window's size, since with pixel2d placement of items is calculated
        # not from center, but from top left corner of window
        # TODO: add ability to auto-adjust position, coz rn its based on 1280x720
        # this will be critical when I will implement resolution slider

        # Ensuring it works for both virtual and real textures
        logo_x = logo_img.getOrigFileXSize() or logo_img.getXSize()
        logo_y = logo_img.getOrigFileYSize() or logo_img.getYSize()
        logo_size = (logo_x, 1, logo_y)
        # right now this has some weird blurrines. Thus far I was unable to find
        # the culprit #TODO
        game_logo = OnscreenImage(
            image=logo_img,
            scale=logo_size,
            pos=(150, 1, -100),
            parent=self.frame,
        )

        # not assigning "self", coz Im not addressing to these from anywhere else
        start_button = shared.ui_builder.make_button(
            text="Play",
            pos=(150, 1, -300),
            command=play_command,
            parent=self.frame,
            # #TODO: mybe make icons configurable on init
            icon=shared.assets.ui["ui_icons_1"],
            text_style="left",
        )

        options_button = shared.ui_builder.make_button(
            text="Options",
            pos=(150, 1, -400),
            command=options_command,
            parent=self.frame,
            icon=shared.assets.ui["ui_icons_7"],
            text_style="left",
        )

        show_lb_button = shared.ui_builder.make_button(
            text="Leaderboard",
            pos=(150, 1, -500),
            command=show_leaderboard_command,
            parent=self.frame,
            icon=shared.assets.ui["ui_icons_2"],
            text_style="left",
        )

        exit_button = shared.ui_builder.make_button(
            text="Exit",
            pos=(150, 1, -600),
            command=exit_command,
            parent=self.frame,
            icon=shared.assets.ui["ui_icons_0"],
            text_style="left",
        )


class OptionsMenu(Menu):
    """Menu where player can change game's settings"""

    def __init__(self, back_command):
        super().__init__("options menu", base.pixel2d)

        self.back_command = back_command

        # Current value, updated via sliders
        self.music_volume = shared.settings.music_volume
        self.sfx_volume = shared.settings.sfx_volume
        # Save them to restore if player clicks 'back' without saving
        self.old_music_volume = shared.settings.music_volume
        self.old_sfx_volume = shared.settings.sfx_volume

        options_label = shared.ui_builder.make_wide_label(
            text="Options",
            pos=(640, 1, -100),
            parent=self.frame,
        )

        music_label = shared.ui_builder.make_wide_label(
            text="Music Volume",
            pos=(200, 1, -200),
            parent=self.frame,
            icon=shared.assets.ui["ui_icons_4"],
            text_style="left",
        )

        self.music_slider = shared.ui_builder.make_slider(
            value=shared.settings.music_volume,
            command=self.update_music_volume,
            pos=(640, 1, -200),
            parent=self.frame,
        )

        sfx_label = shared.ui_builder.make_wide_label(
            text="SFX Volume",
            pos=(200, 1, -300),
            parent=self.frame,
            icon=shared.assets.ui["ui_icons_5"],
            text_style="left",
        )

        self.sfx_slider = shared.ui_builder.make_slider(
            value=shared.settings.sfx_volume,
            command=self.update_sfx_volume,
            pos=(640, 1, -300),
            parent=self.frame,
        )

        dialog_buttons = shared.ui_builder.make_dialog_buttons(
            pos=(640, 1, -600),
            back_text="Back",
            back_command=self.restore_and_close,
            forward_text="Save",
            forward_command=self.save_and_close,
            parent=self.frame,
        )

    def save_and_close(self):
        """Save options and return to parent menu."""
        log.info("Saving options...")
        shared.settings.music_volume = self.music_volume
        shared.settings.sfx_volume = self.sfx_volume

        self.old_music_volume = self.music_volume
        self.old_sfx_volume = self.sfx_volume

        self.back_command()

    def restore_and_close(self):
        """Restore previous options' values and return to parent menu."""
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
    """Menu where player can change level's settings and similar stuff"""

    def __init__(self, play_command, back_command, player_classes: list):
        super().__init__("map settings", base.pixel2d)

        self.play_command = play_command
        self.map_scale = 1
        # this is extremely stupid, but this thing require strings, not ints
        self.map_scales = ["1", "2", "3", "4", "5"]

        self.player_class = player_classes[0]

        # this is placeholder too. Maybe I should even move it to separate screen?
        # it may be also good idea to right away check if class has all the necessary
        # data (and wont crash the game) and only then allow it there. But idk if
        # checks should be done there or during assets loading. Prolly second. #TODO
        class_selection_title = shared.ui_builder.make_wide_label(
            text="Player Class:",
            pos=(200, 1, -100),
            parent=self.frame,
            icon=shared.assets.ui["ui_icons_6"],
            text_style="left",
        )

        class_selection = shared.ui_builder.make_option_menu(
            command=self.select_class,
            items=player_classes,
            initial_item=0,
            pos=(640, 1, -100),
            parent=self.frame,
        )

        map_selection_title = shared.ui_builder.make_wide_label(
            text="Map Scale:",
            pos=(200, 1, -200),
            parent=self.frame,
            icon=shared.assets.ui["ui_icons_3"],
            text_style="left",
        )

        map_scale_selection = shared.ui_builder.make_option_menu(
            command=self.update_map_scale,
            items=self.map_scales,
            initial_item=0,
            pos=(640, 1, -200),
            parent=self.frame,
        )

        dialog_buttons = shared.ui_builder.make_dialog_buttons(
            pos=(640, 1, -600),
            back_text="Back",
            back_command=back_command,
            forward_text="Play",
            forward_command=self.run_level,
            parent=self.frame,
        )

    # TODO: add something like "reset:bool" flag that will set up reset policy in
    # case we switch to other interface. Coz right now we need to do it manually
    # (see options menu), and Im tired of it, thus wont bother adding there. For now
    def select_class(self, classname):
        self.player_class = classname
        log.info(f"Player class has been set to {self.player_class}")

    def update_map_scale(self, scale):
        self.map_scale = scale
        log.info(f"Map scale has been set to {self.map_scale}")

    def run_level(self):
        self.play_command(player_class=self.player_class, map_scale=int(self.map_scale))


class DeathScreen(Menu):
    """Screen shown on player's death"""

    def __init__(self, show_leaderboard_command, restart_command, exit_level_command):
        # I need to implement submenus at some point and remake it with that thing
        # TODO
        super().__init__("death screen", base.pixel2d)

        # not setting text, coz it will be overwritten anyway
        self.death_msg = shared.ui_builder.make_wide_label(
            pos=(640, 1, -300),
            parent=self.frame,
            scale=2,
            text_pos=(0, 20),
        )

        restart_button = shared.ui_builder.make_button(
            text="Restart",
            command=restart_command,
            pos=(640, 1, -400),
            parent=self.frame,
        )

        show_lb_button = shared.ui_builder.make_button(
            text="Leaderboards",
            command=show_leaderboard_command,
            pos=(640, 1, -500),
            parent=self.frame,
        )

        exit_level_button = shared.ui_builder.make_button(
            text="Back to Menu",
            command=exit_level_command,
            pos=(640, 1, -600),
            parent=self.frame,
        )

        # idk if this should be there either. But will do for now
        self.dn_duration = 2

        # notice how its parent is different
        self.death_notification = Popup(
            text="Death",
            text_scale=0.5,
            parent=base.aspect2d,
            duration=self.dn_duration,
        )

    def update_death_message(self, score: int, wave: int, killed: int):
        """Change counters displayed on death_msg to provided values"""
        self.death_msg.setText(
            f"Score: {score}\n" f"Last Wave: {wave}\n" f"Enemies Killed: {killed}"
        )

    def show(self):
        # Overriding default "show" function, to first show death message and
        # only then display the highscores/restart menu

        # I need to specify it there, coz super cant handle calling for functions
        # of parent class from multi-layered function
        sup = super().show

        def show_frame(event):
            sup()
            return

        self.death_notification.show()
        base.task_mgr.do_method_later(self.dn_duration, show_frame, "show death screen")


class PlayerHUD(Menu):
    """Player's hud, displayed in game. Wave counter, player's hp, etc"""

    def __init__(self):
        # this doesnt depend on pixel2d yet, coz it doesnt include any images
        super().__init__("player hud", base.aspect2d)

        # create white-colored text with player's hp above player's head
        # TODO: maybe move it to top left, add some image on background
        self.player_hp = OnscreenText(
            text=str(0),
            pos=(0, 0.05),
            scale=0.05,
            fg=(1, 1, 1, 1),
            parent=self.frame,
            mayChange=True,
        )

        self.score = OnscreenText(
            text="Score: 0",
            pos=(-1.7, 0.9),
            # alignment side may look non-obvious,
            # depending on position and text
            align=TextNode.ALeft,
            scale=0.05,
            fg=(1, 1, 1, 1),
            parent=self.frame,
            mayChange=True,
        )

        # visually it should be below score itself... I think?
        self.score_multiplier = OnscreenText(
            text="Multiplier: 1",
            pos=(-1.7, 0.85),
            align=TextNode.ALeft,
            scale=0.05,
            fg=(1, 1, 1, 1),
            parent=self.frame,
            mayChange=True,
        )

        self.current_wave = OnscreenText(
            text="Current Wave: 0",
            pos=(1.7, 0.9),
            align=TextNode.ARight,
            scale=0.05,
            fg=(1, 1, 1, 1),
            parent=self.frame,
            mayChange=True,
        )

        self.enemy_amount = OnscreenText(
            text="Enemies Left: 0",
            pos=(1.7, 0.85),
            align=TextNode.ARight,
            scale=0.05,
            fg=(1, 1, 1, 1),
            parent=self.frame,
            mayChange=True,
        )

        # idk if these should be there or on separate hud, but for now it will do
        # also idk about styling. I tried to make it look somehow ok, but idk
        self.wave_cleared_msg = Popup(
            text="Wave Cleared!",
            text_pos=(0, 0.85),
            text_scale=0.1,
            parent=self.frame,
            duration=2,
        )

        self.new_wave_msg = Popup(
            text_pos=(0, 0.85),
            text_scale=0.1,
            parent=self.frame,
            duration=2.5,
        )

        self.kill_req_msg = Popup(
            text_pos=(0, 0.75),
            text_scale=0.05,
            parent=self.frame,
            duration=2.5,
        )

    def show_new_wave_msg(self, wave_number: int, kill_requirement: int):
        """Inform player about begining of new wave and its clear conditions"""
        log.debug("Showing new wave messages")
        self.new_wave_msg.set_text(f"Wave {wave_number}")
        self.kill_req_msg.set_text(f"Kill {kill_requirement} Enemies To Proceed")
        self.new_wave_msg.show()
        self.kill_req_msg.show()

    def update_hp(self, value: int):
        """Update self.player_hp to provided value"""
        self.player_hp.setText(str(value))

    def update_score(self, value: int):
        """Update self.score to provided value"""
        self.score.setText(f"Score: {value}")

    def update_multiplier(self, value: float):
        """Update selt.score_multiplier to provided value"""
        self.score_multiplier.setText(f"Multiplier: {value}")

    def update_enemy_counter(self, value: int):
        """Update self.enemy_amount to provided value"""
        self.enemy_amount.setText(f"Enemies Left: {value}")

    def update_current_wave(self, value: int):
        """Update self.current_wave to provided value"""
        self.current_wave.setText(f"Current Wave: {value}")


# TODO: create new "table" class, use it instead of having to place stuff manually
class Leaderboard(Menu):
    def __init__(self, back_command, update_scores_command):
        super().__init__("leaderboard", base.pixel2d)

        self.update_scores_command = update_scores_command

        title = shared.ui_builder.make_wide_label(
            text="Leaderboard",
            pos=(640, 1, -100),
            parent=self.frame,
        )

        labels_frame = shared.ui_builder.make_label(
            pos=(640, 1, -360),
            parent=self.frame,
            scale=3,
        )

        self.scores = []

        y = 150
        # coz we have 10 leaderboard items
        for num in range(0, 10):
            score_label = OnscreenText(
                text="",
                pos=(0, y),
                scale=30,
                parent=labels_frame,
            )

            self.scores.append(score_label)
            # decrease height of message with each new item, to add it under prev
            y -= 35

        back_button = shared.ui_builder.make_button(
            text="Back",
            command=back_command,
            pos=(640, 1, -600),
            parent=self.frame,
        )

    def update_visible_scores(self):
        """Update score labels"""
        leaderboards = self.update_scores_command()
        if not leaderboards:
            return

        # this will break if length of lb is bigger than local score table
        for num, value in enumerate(leaderboards):
            # I could prolly write it in one line instead #TODO
            label = self.scores[num]
            score = value["score"]
            player = value["player_class"]
            pos = num + 1
            text = f"{pos}. Score: {score} Class: {player}"
            label.setText(text)

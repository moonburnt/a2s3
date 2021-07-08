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

#module dedicated to playing BGM

import p3dae
import logging

log = logging.getLogger(__name__)

class MusicPlayer:
    '''Main class dedicated to music operations. For now, meant to be initialized
    from ShowBase or its derivatives, due to usage of "base" global'''
    def __init__(self):
        log.debug("Initializing music player")
        #stuff that currently plays
        self.currently_playing = set()
        #this is different from music player's volume
        self.default_song_volume = 1.0
        #variable that determine if songs can be looped or not by default
        self.default_loop_policy = True

        self.music_manager = base.musicManager
        self.music_player = p3dae.AudioEffects()
        #increasing amount of songs allowed to play at once to 2. This will allow to
        #perform crossfade, but this is also the reason why we track what plays
        self.set_concurrent_songs_limit(2)

    def set_player_volume(self, volume: float):
        '''Set musicManager's volume. Not to be confused with song volume'''
        log.debug(f"Setting player's volume to {volume}")
        self.music_manager.set_volume(volume)

    def set_concurrent_songs_limit(self, value: int):
        '''Set amount of songs that can play at once. Cant be lower than 2'''
        if value < 2:
            value = 2

        self.music_manager.set_concurrent_sound_limit(value)
        log.debug(f"Music player's concurrent songs limit has been set to {value}")

    def set_default_loop_policy(self, toggle: bool):
        '''Override default loop policy'''
        self.default_loop_policy = toggle
        log.debug(f"Default loop policy has been set to {toggle}")

    def play(self, song, loop = None, reset_volume = True, stop_current = True, fade_speed = 0):
        '''Play the song. Meant to be used instead of default "play" command, as
        it also adds song to self.currently_playing. If reset_volume = True, set
        song's volume to default before playback. If stop_current - also reset
        self.currently_playing and stop all the songs that already play'''
        if stop_current and self.currently_playing:
            for item in self.currently_playing:
                item.stop()
            self.currently_playing = set()

        #I tried to pass this directly, but it didnt work
        if not loop:
            loop = self.default_loop_policy
        song.set_loop(loop)

        if reset_volume:
            self.reset_volume(song)

        if fade_speed:
            self.currently_playing.add(song)
            self.music_player.fade_in(song = song,
                                volume = self.default_song_volume,
                                speed = fade_speed)
        else:
            song.play()

        self.currently_playing.add(song)
        log.debug(f"Playing {song}")

    def stop(self, song, fade_speed = 0):
        '''Stop the song and remove it from self.currently_playing'''
        if fade_speed:
            self.music_player.fade_out(song = song,
                                 speed = fade_speed,
                                 stop = True,
                                 reset_volume = True)
        else:
           song.stop()

        if song in self.currently_playing:
            self.currently_playing.remove(song)

        log.debug(f"{song} has been stopped")

    def stop_all(self, fade_speed = 0):
        '''Stop all the currently playing songs and clear self.currently_playing'''
        if not self.currently_playing:
            return

        #because we cant change size of items during iteration, and
        #stopping will remove song from self.currently_playing
        songs = self.currently_playing.copy()
        for item in songs:
            self.stop(item, fade_speed = fade_speed)

        log.debug("Stopped all songs")

    def reset_volume(self, song):
        '''Reset some song's volume to default'''
        song.set_volume(self.default_song_volume)
        log.debug(f"{song}'s volume has been reset to default")

    def crossfade(self, song, loop:bool = None, speed = 0.5):
        '''Fade in provided song, while silencing and then stopping and removing
        from self.currently_playing what currently plays'''
        active_songs = self.currently_playing.copy()

        if not loop:
            loop = self.default_loop_policy

        if not speed:
            self.play(song = song,
                      loop = loop)
            return

        self.music_player.crossfade(song = song,
                              active_songs = active_songs,
                              stop_active = True,
                              fade_in_volume = self.default_song_volume,
                              reset_volume = True,
                              fade_out_speed = speed,
                              fade_in_speed = speed,
                              )

        #resettings list of active tracks
        self.currently_playing = set()
        self.currently_playing.add(song)

#module dedicated for playing BGM

import logging
from direct.interval.LerpInterval import LerpFunctionInterval
from direct.interval.IntervalGlobal import *

log = logging.getLogger(__name__)

class MusicPlayer:
    '''Main class dedicated to music operations. For now, means to be initialized
    from ShowBase or its derivatives'''
    def __init__(self):
        log.debug("Initializing music player")
        #stuff that currently plays
        self.currently_playing = set()
        #this is different from music player's volume
        self.default_song_volume = 1.0
        #variable that determine if songs can be looped or not by default
        self.default_loop_policy = True

        self.music_manager = base.musicManager
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
        '''Yet another way to override default loop policy'''
        self.default_loop_policy = toggle
        log.debug(f"Default loop policy has been set to {toggle}")

    def play(self, song, loop = None, reset_volume = True, stop_current = True, fade_speed = 0):
        '''Play the song normally. Meant to be used instead of default "play"
        command, as it also overwrites what currently plays. If reset_volume = True,
        also set song's volume to default'''
        if stop_current and self.currently_playing:
            for item in self.currently_playing:
                item.stop()
            self.currently_playing = {}

        #I tried to pass this directly, but it didnt work
        if not loop:
            loop = self.default_loop_policy
        song.set_loop(loop)

        if reset_volume:
            self.reset_volume(song)

        if fade_speed:
            self._fade_in(song, speed = fade_speed)

        song.play()
        self.currently_playing.add(song)
        log.debug(f"Playing {song}")

    def stop(self, song, fade_speed = 0):
        '''Stop the song and remove it from what currently plays'''
        if fade_speed:
            self._fade_out(song, speed = fade_speed)
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

    def _fade_out(self, song, speed = 0.5):
        '''Slowly decrease song's volume within 'speed' amount of seconds, then stop it'''
        fade_out_interval = LerpFunctionInterval(song.set_volume,
                                                 duration = speed,
                                                 fromData = song.get_volume(),
                                                 toData = 0)

        log.debug(f"Fading out {song}")
        fade_out_interval.start()

    def _fade_in(self, song, speed = 0.5):
        fade_in_interval = LerpFunctionInterval(song.set_volume,
                                                duration = speed,
                                                fromData = 0,
                                                toData = self.default_song_volume)

        log.debug(f"Fading in {song}")
        fade_in_interval.start()

    def crossfade(self, song, loop = None, speed = 10):
        if not loop:
            loop = self.default_loop_policy

        parallel = Parallel()

        if self.currently_playing:
            songs = self.currently_playing.copy()
            for item in self.currently_playing:
                parallel.append(Func(self.stop, song = item, fade_speed = speed))

        parallel.append(Func(self.play, song = song, loop = loop,
                             fade_speed = speed, stop_current = False))
        log.debug(f"Crossfading {song}")
        parallel.start()

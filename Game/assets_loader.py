#module where I specify functions related to loading game assets into memory
from os import listdir
from os.path import isfile, isdir, basename, join, splitext
from Game import config
import logging

log = logging.getLogger(__name__)

GAME_DIR = '.'
ASSETS_DIR = join(GAME_DIR, 'Assets')
SPRITE_DIR = join(ASSETS_DIR, 'Sprites')
MUSIC_DIR = join(ASSETS_DIR, 'BGM')
SFX_DIR = join(ASSETS_DIR, 'SFX')

class AssetsLoader:
    def __init__(self):
        #this will load all the default assets into memory. It may be good idea
        #to allow loading of custom assets on top of these in future, for modding
        self.music = self.load_assets(MUSIC_DIR, "music")
        self.sfx = self.load_assets(SFX_DIR, "sfx")
        self.sprite = self.load_assets(SPRITE_DIR, "sprite")

    def get_files(self, pathtodir):
        '''
        Receives str(path to directory with files), returns list(files in directory)
        '''
        files = []

        log.debug(f"Attempting to parse directory {pathtodir}")
        directory_content = listdir(pathtodir)
        log.debug(f"Uncategorized content inside is: {directory_content}")

        for item in directory_content:
            log.debug(f"Processing {item}")
            itempath = join(pathtodir, item)
            if isdir(itempath):
                log.debug(f"{itempath} leads to directory, attempting "
                           "to process its content")
                files += self.get_files(itempath)
            else:
                #assuming that everything that isnt directory is file
                log.debug(f"{itempath} leads to file, adding to list")
                files.append(itempath)

        log.debug(f"Got following files in total: {files}")
        return files

    def load_assets(self, pathtodir, media_type):
        '''
        Receives str(path to dir with files) and type of media in this directory
        (the allowed types are "music", "sfx" and "sprite". Loads all files
        inside dir into memory by using related loader function. Then returns
        dictionary looking like {{'filename_without_extension': file object}}
        '''

        files = self.get_files(pathtodir)

        if media_type == "music":
            funcname = loader.load_music
        elif media_type == "sfx":
            funcname = loader.load_sfx
        #I should probably raise type error or something on else instead, idk
        else:
            funcname = loader.load_texture

        data = {}
        for item in files:
            name_of_file = basename(item)
            name_without_extension = splitext(name_of_file)[0]
            data[name_without_extension] = funcname(item)

        return data

#module where I specify functions related to loading game assets into memory
from os import listdir
from os.path import isfile, isdir, basename, join, splitext
from Game import config
import logging

log = logging.getLogger(__name__)

SPRITE_DIR = config.SPRITE_DIR
MUSIC_DIR = config.MUSIC_DIR
SFX_DIR = config.SFX_DIR

def get_files(pathtodir):
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
            files += get_files(itempath)
        else:
            #assuming that everything that isnt directory is file
            log.debug(f"{itempath} leads to file, adding to list")
            files.append(itempath)

    log.debug(f"Got following files in total: {files}")
    return files

def assets_loader(pathtodir, funcname):
    '''
    Receives str(path to dir with files) and name of function used to load them.
    Loads all files inside dir into memory by using that function. Then returns
    dictionary looking like {{'filename_without_extension': file object}}
    '''

    music_files = get_files(pathtodir)

    data = {}
    for item in music_files:
        name_of_file = basename(item)
        name_without_extension = splitext(name_of_file)[0]
        data[name_without_extension] = funcname(item)

    return data

def load_assets():
    '''Meta function used to batch-load all assets from default directories into
    memory. Returns dictionary containing dictionaries with related data'''

    music = assets_loader(MUSIC_DIR, loader.load_music)
    sfx = assets_loader(SFX_DIR, loader.load_sfx)
    sprite = assets_loader(SPRITE_DIR, loader.load_texture)

    assets = {}
    assets['music'] = music
    assets['sfx'] = sfx
    assets['sprites'] = sprite

    log.debug(f"Successfully loaded {assets}")
    return assets

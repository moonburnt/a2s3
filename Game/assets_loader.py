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

# module where I specify functions related to loading game assets into memory

from os import listdir
from os.path import isfile, isdir, basename, join, splitext
from toml import load as tomload
import json
from panda3d.core import SamplerState
from p3dss import processor
import logging

log = logging.getLogger(__name__)

GAME_DIR = "."
ASSETS_DIR = join(GAME_DIR, "Assets")
UI_DIR = join(ASSETS_DIR, "UI")
SPRITE_DIR = join(ASSETS_DIR, "Sprites")
MUSIC_DIR = join(ASSETS_DIR, "BGM")
SFX_DIR = join(ASSETS_DIR, "SFX")
ENTITY_DIR = join(ASSETS_DIR, "Entity")
CLASSES_DIR = join(ENTITY_DIR, "Classes")
ENEMIES_DIR = join(ENTITY_DIR, "Enemies")
SKILLS_DIR = join(ENTITY_DIR, "Skills")
PROJECTILES_DIR = join(ENTITY_DIR, "Projectiles")
HEADS_DIR = join(ENTITY_DIR, "Heads")
BODIES_DIR = join(ENTITY_DIR, "Bodies")
FONTS_DIR = join(ASSETS_DIR, "Fonts")


class AssetsLoader:
    def __init__(self):
        # this will load all the default assets into memory. With reworked loader,
        # it should conceptually be possible to load custom stuff on top of these
        # in future. E.g for modding and such purposes
        self.music = {}
        self.sfx = {}
        self.ui = {}
        self.sprite = {}
        self.classes = {}
        self.enemies = {}
        self.skills = {}
        self.projectiles = {}
        self.heads = {}
        self.bodies = {}

        # self.load_all()

    def get_files(
        self,
        pathtodir: str,
        include_subdirs: bool = False,
        extension: str = None,
        case_insensitive: bool = True,
    ) -> list:
        """Fetches and returns list of files in provided directory. Optionally
        may include subdirectories and seek for specific file extension"""
        files = []

        log.debug(f"Attempting to parse directory {pathtodir}")
        directory_content = listdir(pathtodir)
        log.debug(f"Uncategorized content inside is: {directory_content}")

        for item in directory_content:
            log.debug(f"Processing {item}")
            itempath = join(pathtodir, item)
            if isdir(itempath):
                if include_subdirs:
                    log.debug(
                        f"{itempath} leads to directory, attempting "
                        "to process its content"
                    )
                    files += self.get_files(itempath, include_subdirs, extension)
            else:
                # assuming that everything that isnt directory is file
                log.debug(f"{itempath} leads to file")
                if extension:
                    # there is probably a prettier way to do that
                    if case_insensitive:
                        file_ext = splitext(itempath)[-1].lower()
                        ext = extension.lower()
                    else:
                        file_ext = splitext(itempath)[-1]
                        ext = extension

                    if file_ext == ext:
                        log.debug(f"{itempath} has valid extension")
                        files.append(itempath)

                else:
                    files.append(itempath)

        log.debug(f"Got following files in total: {files}")
        return files

    def get_textures(self, pathtodir: str, extension: str = ".png") -> dict:
        """Get textures from provided directory"""
        files = self.get_files(pathtodir, extension=extension)

        data = {}
        for item in files:
            name_of_file = basename(item)
            name_without_extension = splitext(name_of_file)[0]
            try:
                sprite = loader.load_texture(item)
                sprite.set_magfilter(SamplerState.FT_nearest)
                sprite.set_minfilter(SamplerState.FT_nearest)
            except Exception as e:
                log.warning(f"Unable to fetch {item}: {e}")
                continue
            data[name_without_extension] = sprite

        return data

    def get_jsons(self, pathtodir: str, extension: str = ".json") -> dict:
        """Get jsons from provided directory"""
        files = self.get_files(pathtodir, extension=extension)

        data = {}
        for item in files:
            name_of_file = basename(item)
            name_without_ext = splitext(name_of_file)[0]
            try:
                with open(item, "r") as f:
                    content = json.load(f)
            except Exception as e:
                log.warning(f"Unable to fetch {item}: {e}")
                continue
            data[name_without_ext] = content

        return data

    def get_spritesheet_descriptions(
        self, pathtodir: str, extension: str = ".ss"
    ) -> dict:
        """Get spritesheet descriptions from provided directory"""
        data = self.get_jsons(pathtodir, extension=extension)
        # filtering invalid descriptions.
        # Doing like that to avoid crash on dict size change
        keys = list(data.keys())
        for item in keys:
            if (
                not "sprite_size" in data[item]
                or
                # assumed first wont trigger on existing but empty
                # #TODO: maybe add type/length check?
                not data[item]["sprite_size"]
                or not "batch_cutting" in data[item]
                or not "sprites" in data[item]
            ):
                data.pop(item)

        return data

    def get_tomls(self, pathtodir: str, extension: str = ".toml") -> dict:
        """Get tomls from provided directory"""
        files = self.get_files(pathtodir, extension=extension)
        data = {}
        for item in files:
            try:
                toml_content = tomload(item)
                internal_name = toml_content["Main"]["name"]
            except Exception as e:
                log.warning(f"{item} has invalid format: {e}. Wont import")
                continue
            else:
                data[internal_name] = toml_content

        return data

    def load_ui(self, pathtodir: str, extension: str = ".png"):
        textures = self.get_textures(pathtodir, extension=extension)
        descriptions = self.get_spritesheet_descriptions(pathtodir)

        described_sheets = [x for x in list(textures) if x in list(descriptions)]

        # will crash on duplicates, shouldnt happen
        for sheet in described_sheets:
            # for now, all processed items get removed from textures list
            # and results of processing with overlapping names will overwrite
            # whatever is already in textures. Its made on purpose to provide
            # smooth transition from textures to sheets. However it may break
            # stuff in some cases and, maybe, require rework or some switch #TODO

            # for now, only batch cutting is supported. Precise sprite cutting
            # is something I will need to add in future #TODO
            # textures[sheet].set_keep_ram_image(True)
            if descriptions[sheet]["batch_cutting"]:
                # avoiding possible issues with incorrect sized/formats
                try:
                    sprites = processor.get_textures(
                        spritesheet=textures[sheet],
                        sprite_sizes=tuple(descriptions[sheet]["sprite_size"]),
                    )
                except Exception as e:
                    log.warning(f"Unable to cut {sheet}: {e}")
                    pass
                else:
                    sprite_data = {}
                    for sprite in sprites:
                        sprite.set_magfilter(SamplerState.FT_nearest)
                        sprite.set_minfilter(SamplerState.FT_nearest)
                        # will crash on empty, shouldnt happen
                        sprite_data[sprite.get_name()] = sprite

                    # maybe should do that after removal of original file?
                    textures = {**textures, **sprite_data}

                    # textures[f"{sheet}_sprites"] = sprites
                    textures[sheet] = sprites
            textures.pop(sheet)

        log.debug("Updating UI storage")
        self.ui = textures

    def load_music(self, pathtodir: str, extension: str = ".ogg"):
        """Load and update currently known music from provided directory and its subdirs"""
        files = self.get_files(pathtodir, extension=extension)

        data = {}
        for item in files:
            name_of_file = basename(item)
            name_without_extension = splitext(name_of_file)[0]
            data[name_without_extension] = loader.load_music(item)

        log.debug("Updating music storage")
        self.music = {**self.music, **data}

    def load_sfx(self, pathtodir: str, extension: str = ".ogg"):
        """Load and update currently known sfx from provided directory and its subdirs"""
        files = self.get_files(pathtodir, extension=extension)

        data = {}
        for item in files:
            name_of_file = basename(item)
            name_without_extension = splitext(name_of_file)[0]
            data[name_without_extension] = loader.load_sfx(item)

        log.debug("Updating sfx storage")
        self.sfx = {**self.sfx, **data}

    def load_sprite(self, pathtodir: str, extension: str = ".png"):
        """Load and update currently known sprites from provided directory"""
        data = self.get_textures(pathtodir)

        log.debug("Updating sprite storage")
        self.sprite = {**self.sprite, **data}

    def load_classes(self, pathtodir: str):
        """Load and update configuration files of player classes from provided
        directory and its subdirs"""
        data = self.get_tomls(pathtodir, ".player")
        log.debug("Updating player classes storage")
        self.classes = {**self.classes, **data}

    def load_enemies(self, pathtodir: str):
        """Load and update enemy configuration files from provided directory
        and its subdirs"""
        data = self.get_tomls(pathtodir, ".enemy")
        log.debug("Updating enemies storage")
        self.enemies = {**self.enemies, **data}

    def load_skills(self, pathtodir: str):
        """Load and update skill configuration files from provided directory
        and its subdirs"""
        data = self.get_tomls(pathtodir, ".skill")
        log.debug("Updating skills storage")
        self.skills = {**self.skills, **data}

    def load_projectiles(self, pathtodir: str):
        """Load and update projectile configuration files from provided directory
        and its subdirs"""
        data = self.get_tomls(pathtodir, ".projectile")
        log.debug("Updating projectiles storage")
        self.projectiles = {**self.projectiles, **data}

    def load_heads(self, pathtodir: str):
        """Load and update head configuration files from provided directory
        and its subdirs"""
        data = self.get_tomls(pathtodir, ".head")
        log.debug("Updating heads storage")
        self.heads = {**self.heads, **data}

    def load_bodies(self, pathtodir: str):
        """Load and update body configuration files from provided directory
        and its subdirs"""
        data = self.get_tomls(pathtodir, ".body")
        log.debug("Updating bodies storage")
        self.bodies = {**self.bodies, **data}

    def load_all(self):
        """Load all assets from default paths"""
        self.load_ui(UI_DIR)
        self.load_music(MUSIC_DIR)
        self.load_sfx(SFX_DIR)
        self.load_sprite(SPRITE_DIR)
        self.load_classes(CLASSES_DIR)
        self.load_enemies(ENEMIES_DIR)
        self.load_skills(SKILLS_DIR)
        self.load_projectiles(PROJECTILES_DIR)
        self.load_heads(HEADS_DIR)
        self.load_bodies(BODIES_DIR)

    def reset(self):
        """Reset assets dictionaries to empty state"""
        self.ui = {}
        self.music = {}
        self.sfx = {}
        self.sprite = {}
        self.classes = {}
        self.enemies = {}
        self.skills = {}
        self.projectiles = {}
        self.heads = {}
        self.bodies = {}

    def reload(self):
        """Reset assets dictionaries to be empty, then load defaults"""
        self.reset()
        self.load_all()

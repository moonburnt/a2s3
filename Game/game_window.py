#thou shall be file where I do everything related to game rendering
#effectively "Main", ye

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (WindowProperties, CollisionTraverser,
                          CollisionHandlerPusher)

from Game import entities, map_loader, config

log = logging.getLogger(__name__)

FLOOR_TEXTURE = config.FLOOR_TEXTURE
CHARACTER_TEXTURE = config.CHARACTER_TEXTURE
ENEMY_TEXTURE = config.ENEMY_TEXTURE
MENU_BGM = config.MENU_BGM
ENTITY_LAYER = config.ENTITY_LAYER
WINDOW_SIZE = config.WINDOW_SIZE
MUSIC_VOLUME = config.MUSIC_VOLUME
CONTROLS = config.CONTROLS
MAP_SIZE = config.MAP_SIZE

class Main(ShowBase):
    def __init__(self):
        log.debug("Setting up the window")
        ShowBase.__init__(self)

        #disabling mouse to dont mess with camera
        self.disable_mouse()

        log.debug("Resizing the window")
        window_settings = WindowProperties()
        window_settings.set_size(WINDOW_SIZE['x'], WINDOW_SIZE['y'])
        self.win.request_properties(window_settings)

        log.debug(f"Generating the map")
        map_loader.flat_map_generator(FLOOR_TEXTURE, MAP_SIZE['x'], MAP_SIZE['y'])

        log.debug(f"Initializing player")
        self.player_object, player_collision = entities.entity_2D("player", CHARACTER_TEXTURE, 32, 32)
        #setting character's position to always render on ENTITY_LAYER
        #setting this lower may cause glitches, as below lies the FLOOR_LAYER
        self.player_object.set_pos(0, 0, ENTITY_LAYER)

        log.debug(f"Initializing enemy")
        self.enemy_object, enemy_collision = entities.entity_2D("enemy", ENEMY_TEXTURE, 32, 32)
        #this is a temporary position, except for layer.
        #in real game, these will be spawned at random places
        self.enemy_object.set_pos(0, 30, ENTITY_LAYER)

        log.debug(f"Initializing collision processors")
        #I dont exactly understand the syntax, but other variable names failed
        #seems like these are inherited from ShowBase the same way as render
        #also "base" isnt typo, but thing of similar matter
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        self.pusher.set_horizontal(False)
        base.pusher.add_collider(player_collision, self.player_object)
        base.cTrav.add_collider(player_collision, self.pusher)
        #showing all collisions on the scene (e.g visible to render)
        #this is better than manually doing collision.show() for each object
        self.cTrav.show_collisions(render)

        #this will set camera to be right above card.
        #changing first value will rotate the floor
        #changing second - change the angle from which we see floor
        #the last one is zoom. Negative values flip the screen
        #maybe I should add ability to change camera's angle, at some point?
        self.camera.set_pos(0, 700, 500)
        self.camera.look_at(0, 0, 0)
        #making camera always follow character
        self.camera.reparent_to(self.player_object)

        log.debug(f"Setting up background music")
        menu_theme = loader.load_music(MENU_BGM)
        menu_theme.set_loop(True)
        menu_theme.set_volume(MUSIC_VOLUME)
        menu_theme.play()

        log.debug(f"Initializing controls handler")
        #taskMgr is function that runs on background each frame
        #and execute whatever functions are attached to it with .add()
        self.task_manager = taskMgr.add(self.controls_handler, "controls handler")

        #dictionary that stores default state of keys
        self.controls_status = {"move_up": False, "move_down": False,
                                "move_left": False, "move_right": False}

        #.accept() is method that receive input from buttons and perform stuff
        #its format is the following:
        #first is name-state of key (name is in english, but any layout is supported)
        #second is function that gets called if this button event has happend
        #optional third can be used to pass arguments to second function
        self.accept(CONTROLS['move_up'], self.change_key_state, ["move_up", True])
        #"-up" prefix means key has been released
        #I know how ugly it looks, but for now it works
        self.accept(f"{CONTROLS['move_up']}-up", self.change_key_state, ["move_up", False])
        self.accept(CONTROLS['move_down'], self.change_key_state, ["move_down", True])
        self.accept(f"{CONTROLS['move_down']}-up", self.change_key_state, ["move_down", False])
        self.accept(CONTROLS['move_left'], self.change_key_state, ["move_left", True])
        self.accept(f"{CONTROLS['move_left']}-up", self.change_key_state, ["move_left", False])
        self.accept(CONTROLS['move_right'], self.change_key_state, ["move_right", True])
        self.accept(f"{CONTROLS['move_right']}-up", self.change_key_state, ["move_right", False])

    def change_key_state(self, key_name, key_status):
        '''Receive str(key_name) and bool(key_status).
        Change key_status of related key in self.controls_status'''
        self.controls_status[key_name] = key_status
        log.debug(f"{key_name} has been set to {key_status}")

    def controls_handler(self, action):
        '''Intended to be used as part of task manager routine.
        Automatically receive action from task manager,
        checks if buttons are pressed and log it. Then
        return action back to task manager, so it keeps running in loop'''

        #In future, these speed values may be affected by some items
        if self.controls_status["move_up"]:
            self.player_object.setPos(self.player_object.getPos() + (0, -3, 0))
        if self.controls_status["move_down"]:
            self.player_object.setPos(self.player_object.getPos() + (0, 3, 0))
        if self.controls_status["move_left"]:
            self.player_object.setPos(self.player_object.getPos() + (3, 0, 0))
        if self.controls_status["move_right"]:
            self.player_object.setPos(self.player_object.getPos() + (-3, 0, 0))

        #it works a bit weird, but if we wont return .cont of task we received,
        #then task will run just once and then stop, which we dont want
        return action.cont

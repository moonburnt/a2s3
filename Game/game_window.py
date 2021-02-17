#thou shall be file where I do everything related to game rendering
#effectively "Main", ye

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (WindowProperties, CardMaker, Texture, SamplerState,
                          CollisionTraverser, CollisionHandlerPusher,
                          CollisionSphere, CollisionPlane, Plane, CollisionNode)

log = logging.getLogger(__name__)

#these will be constants determined in other file
FLOOR_TEXTURE = 'Textures/floor.png'
CHARACTER_TEXTURE = 'Textures/character.png'
ENEMY_TEXTURE = 'Textures/enemy.png'
MENU_BGM = 'BGM/menu_theme.ogg'
#the height where character sprite will reside
CHARACTER_LAYER = 1
FLOOR_LAYER = 0

#whatever below are variables that could be changed by user... potentially
WINDOW_X = 1280
WINDOW_Y = 720
#this is a float between 0 and 1, e.g 75 equals to "75%"
MUSIC_VOLUME = 0.75
#key is the name of action, value is the name of key in panda syntax
CONTROLS = {"move_up": "arrow_up", "move_down": "arrow_down",
            "move_left": "arrow_left", "move_right": "arrow_right"}

#it may be nice to add minimal allowed size check, but not today
MAP_SIZE = {"x": 600, "y": 300}

class Main(ShowBase):
    def __init__(self):
        log.debug("Setting up the window")
        ShowBase.__init__(self)

        map_size = (-MAP_SIZE['x']/2, MAP_SIZE['x']/2, -MAP_SIZE['y']/2, MAP_SIZE['y']/2)

        self.disable_mouse()

        log.debug("Resizing the window")
        window_settings = WindowProperties()
        window_settings.set_size(WINDOW_X, WINDOW_Y)
        self.win.request_properties(window_settings)

        log.debug("Initializing floor")
        #initializing new cardmaker object
        #which is essentially our go-to way to create flat models
        floor = CardMaker('floor')
        #setting up card size
        floor.set_frame(*map_size)
        #attaching card to render and creating it's object
        #I honestly dont understand the difference between
        #this and card.reparent_to(render)
        #but both add object to scene graph, making it visible
        floor_card = render.attach_new_node(floor.generate())
        #loading texture
        floor_image = loader.load_texture(FLOOR_TEXTURE)
        #settings its wrap modes (e.g the way it acts if it ends before model
        floor_image.set_wrap_u(Texture.WM_repeat)
        floor_image.set_wrap_v(Texture.WM_repeat)
        #applying texture to card
        floor_card.set_texture(floor_image)
        #arranging card's angle
        floor_card.look_at((0, 0, -1))
        #and position
        floor_card.set_pos(0, 0, FLOOR_LAYER)

        log.debug(f"Adding invisible walls to collide with")
        #I can probably put this on cycle, but whatever
        wall_node = CollisionNode("wall")
        wall_node.add_solid(CollisionPlane(Plane((map_size[0], 0, 0),
                                                 (map_size[1], 0, 0))))
        wall = render.attach_new_node(wall_node)

        wall_node = CollisionNode("wall")
        wall_node.add_solid(CollisionPlane(Plane((-map_size[0], 0, 0),
                                                 (-map_size[1], 0, 0))))
        wall = render.attach_new_node(wall_node)

        wall_node = CollisionNode("wall")
        wall_node.add_solid(CollisionPlane(Plane((0, map_size[2], 0),
                                                 (0, map_size[3], 0))))
        wall = render.attach_new_node(wall_node)

        wall_node = CollisionNode("wall")
        wall_node.add_solid(CollisionPlane(Plane((0, -map_size[2], 0),
                                                 (0, -map_size[3], 0))))
        wall = render.attach_new_node(wall_node)

        log.debug(f"Initializing character")
        character = CardMaker('player')
        #character.set_frame_fullscreen_quad()
        #setting character's card to be 32x32, just like picture
        character.set_frame(-16, 16, -16, 16)
        #Im thinking about renaming this to "character object"
        self.character_card = render.attach_new_node(character.generate())
        character_image = loader.load_texture(CHARACTER_TEXTURE)
        #setting filtering method to dont blur our sprite
        character_image.set_magfilter(SamplerState.FT_nearest)
        character_image.set_minfilter(SamplerState.FT_nearest)
        self.character_card.set_texture(character_image)
        self.character_card.look_at((0, 0, -1))
        #setting character's position to always render on CHARACTER_LAYER
        self.character_card.set_pos(0, 0, CHARACTER_LAYER)
        #enable support for alpha channel
        #this is a float, e.g making it non-100% will require
        #values between 0 and 1
        self.character_card.set_transparency(1)

        #setting character's collisions
        collider = CollisionNode("player")
        #TODO: move this to be under character's legs
        #right now its centered on character's center
        collider.add_solid(CollisionSphere(0, 0, 0, 15))
        character_collision = self.character_card.attach_new_node(collider)

        log.debug(f"Initializing enemy")
        enemy = CardMaker('enemy')
        enemy.set_frame(-16, 16, -16, 16)
        self.enemy_object = render.attach_new_node(enemy.generate())
        enemy_image = loader.load_texture(ENEMY_TEXTURE)
        enemy_image.set_magfilter(SamplerState.FT_nearest)
        enemy_image.set_minfilter(SamplerState.FT_nearest)
        self.enemy_object.set_texture(enemy_image)
        self.enemy_object.look_at((0, 0, -1))
        #its position is termorary, except layer - later to be decided randomly
        self.enemy_object.set_pos(0, 30, CHARACTER_LAYER)
        self.enemy_object.set_transparency(1)
        #billboard is effect to ensure that object always face camera the same
        #however this one has a flaw - it rotates horizontally when I move char
        #will leave it as is for now, but #TODO: fix or make custom billboard
        self.enemy_object.set_billboard_axis()

        collider = CollisionNode("enemy")
        collider.add_solid(CollisionSphere(0, 0, 0, 15))
        enemy_collision = self.enemy_object.attach_new_node(collider)

        log.debug(f"Initializing collision processors")
        #I dont exactly understand the syntax, but other variable names failed
        #seems like these are inherited from ShowBase the same way as render
        #also "base" isnt typo, but thing of similar matter
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        self.pusher.set_horizontal(False)
        base.pusher.add_collider(character_collision, self.character_card)
        base.cTrav.add_collider(character_collision, self.pusher)
        #showing all collisions on the scene (e.g visible to render)
        #this is better than manually doing collision.show() for each object
        self.cTrav.show_collisions(render)

        #this will set camera to be right above card.
        #changing first value will rotate the floor
        #changing second - change the angle from which we see floor
        #the last one is zoom. Negative values flip the screen
        #maybe I should add ability to change camera's angle, at some point?
        self.camera.set_pos(0, -700, -500)
        self.camera.look_at(0, 0, 0)
        #making camera always follow character
        self.camera.reparent_to(self.character_card)

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
            log.debug("Moving up!")
            self.character_card.setPos(self.character_card.getPos() + (0, 3, 0))
        if self.controls_status["move_down"]:
            log.debug("Moving down!")
            self.character_card.setPos(self.character_card.getPos() + (0, -3, 0))
        if self.controls_status["move_left"]:
            log.debug("Moving left!")
            self.character_card.setPos(self.character_card.getPos() + (-3, 0, 0))
        if self.controls_status["move_right"]:
            log.debug("Moving right!")
            self.character_card.setPos(self.character_card.getPos() + (3, 0, 0))

        #it works a bit weird, but if we wont return .cont of task we received,
        #then task will run just once and then stop, which we dont want
        return action.cont

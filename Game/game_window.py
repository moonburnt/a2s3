#thou shall be file where I do everything related to game rendering
#effectively "Main", ye

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, CardMaker, Texture

log = logging.getLogger(__name__)

WINDOW_X = 1280
WINDOW_Y = 720
FLOOR_TEXTURE = 'Textures/floor.png'
CHARACTER_TEXTURE = 'Textures/character.png'
MENU_BGM = 'BGM/menu_theme.ogg'
#this is a float between 0 and 1, e.g 75 equals to "75%"
MUSIC_VOLUME = 0.75
#the height where character sprite will reside
CHARACTER_LAYER = 1

class Main(ShowBase):
    def __init__(self):
        log.debug("Setting up the window")
        ShowBase.__init__(self)

        self.disable_mouse()

        log.debug("Resizing the window")
        window_settings = WindowProperties()
        window_settings.set_size(WINDOW_X, WINDOW_Y)
        self.win.request_properties(window_settings)

        log.debug("Loading the floor")
        #initializing new cardmaker object
        #which is essentially our go-to way to create flat models
        floor = CardMaker('floor')
        #setting up card's size
        #floor.set_frame_fullscreen_quad()
        floor.set_frame(-300, 300, -300, 300)
        #attaching card to render and creating it's object
        #I honestly dont understand the difference between
        #this and card.reparent_to(render)
        #but both add object to scene graph, making it visible
        floor_card = render.attach_new_node(floor.generate())
        #card = floor.generate()
        #loading texture
        floor_image = loader.load_texture(FLOOR_TEXTURE)
        #settings its wrap modes (e.g the way it acts if it ends before model
        floor_image.set_wrap_u(Texture.WM_repeat)
        floor_image.set_wrap_v(Texture.WM_repeat)
        #applying texture to card
        floor_card.set_texture(floor_image)
        #arranging card's angle
        floor_card.look_at((0, 0, -1))

        log.debug(f"Loading character")
        character = CardMaker('character')
        #character.set_frame_fullscreen_quad()
        #setting character's card to be 32x32, just like picture
        character.set_frame(-16, 16, -16, 16)
        character_card = render.attach_new_node(character.generate())
        character_image = loader.load_texture(CHARACTER_TEXTURE)
        character_card.set_texture(character_image)
        character_card.look_at((0, 0, -1))
        #setting character's position to always render on CHARACTER_LAYER
        character_card.set_pos(0, 0, CHARACTER_LAYER)
        #enable support for alpha channel
        #this is a float, e.g making it non-100% will require
        #values between 0 and 1
        character_card.set_transparency(1)

        #this will set camera to be right above card.
        #changing first value will rotate the floor
        #changing second - change the angle from which we see floor
        #the last one is zoom. Should never be less than 2
        self.camera.set_pos(0, 0, 2000)
        self.camera.look_at(0, 0, 0)

        log.debug(f"Setting up background music")
        menu_theme = loader.load_music(MENU_BGM)
        menu_theme.set_loop(True)
        menu_theme.set_volume(MUSIC_VOLUME)
        menu_theme.play()

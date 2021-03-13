import logging
from panda3d.core import (CardMaker, TextureStage, CollisionPlane,
                          Plane, CollisionNode)
from math import ceil
from Game import config

log = logging.getLogger(__name__)

#module where I specify everything related to generating and loading maps

FLOOR_LAYER = config.FLOOR_LAYER
ENTITY_LAYER = config.ENTITY_LAYER

class FlatMap:
    def __init__(self, texture, size):
        self.size_x, self.size_y = size
        self.texture = texture
        log.debug(f"Generating map of size {self.size_x}x{self.size_y}")
        self.map_size = (-self.size_x/2, self.size_x/2, -self.size_y/2, self.size_y/2)
        self.create_floor()
        #TODO: add bool to either generate only some borders or none, to provide
        #ability to fall/kick enemies into the void. This will require addition of
        #collision node to floor, aswell as checks to ensure that entity hasnt fell
        self.add_border_walls()

        #taking advantage of enemies not colliding with map borders and spawning
        #them outside of the map's corners. Idk about the numbers and if they should
        #be related to sprite size in anyway. Basically anything will do for now
        #later we will add some "fog of war"-like effect above map's borders, so
        #enemies spawning on these positions will seem more natural

        #TODO: it may be good idea to make these configurable, instead of hardcoding
        #these to just "outside of map's corners"
        self.enemy_spawnpoints = [(self.map_size[1] + 32, self.map_size[3] + 32),
                                  (self.map_size[0] - 32, self.map_size[2] - 32),
                                  (self.map_size[1] + 32, self.map_size[2] - 32),
                                  (self.map_size[0] - 32, self.map_size[3] + 32)]

        #TODO: make this configurable aswell. For now its just center of map
        self.player_spawnpoint = 0, 0, ENTITY_LAYER

    def create_floor(self):
        '''Generate flat floor of size, provided to class'''
        #todo: add fallback values in case size hasnt been specified
        log.debug(f"Generating the floor")

        #initializing new cardmaker object
        #which is essentially our go-to way to create flat models
        floor = CardMaker('floor')
        #setting up card size
        floor.set_frame(*self.map_size)
        #attaching card to render and creating it's object
        #I honestly dont understand the difference between
        #this and card.reparent_to(render)
        #but both add object to scene graph, making it visible
        floor_object = render.attach_new_node(floor.generate())
        floor_object.set_texture(self.texture)
        #determining how often do we need to repeat our texture
        texture_x = self.texture.get_orig_file_x_size()
        texture_y = self.texture.get_orig_file_y_size()
        repeats_x = ceil(self.size_x/texture_x)
        repeats_y = ceil(self.size_y/texture_y)
        #repeating texture to avoid stretching when possible
        floor_object.set_tex_scale(TextureStage.getDefault(), repeats_x, repeats_y)
        #arranging card's angle
        floor_object.look_at((0, 0, -1))
        floor_object.set_pos(0, 0, FLOOR_LAYER)

    def add_border_walls(self):
        '''Attaching invisible walls to map's borders, to avoid falling off map'''
        log.debug("Adding invisible walls to collide with on map's borders")
        wall_coordinates = [((self.map_size[0], 0, 0), (self.map_size[1], 0, 0)),
                            ((-self.map_size[0], 0, 0), (-self.map_size[1], 0, 0)),
                            ((0, self.map_size[2], 0), (0, self.map_size[3], 0)),
                            ((0, -self.map_size[2], 0), (0, -self.map_size[3], 0))]

        for sizes in wall_coordinates:
            wall_node = CollisionNode("wall")
            #it looks like without adding node to pusher (we dont need that there),
            #masks wont work. Thus for now I wont use them, as defaults seem to work
            #wall_node.set_collide_mask(BitMask32(config.WALLS_COLLISION_MASK))
            wall_node.add_solid(CollisionPlane(Plane(*sizes)))
            wall = render.attach_new_node(wall_node)

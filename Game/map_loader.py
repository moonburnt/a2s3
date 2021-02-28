import logging
from panda3d.core import (CardMaker, TextureStage, CollisionPlane,
                          Plane, CollisionNode)
from math import ceil
from Game import config

log = logging.getLogger(__name__)

#module where I specify everything related to generating and loading maps

FLOOR_LAYER = config.FLOOR_LAYER
DEFAULT_SPRITE_FILTER = config.DEFAULT_SPRITE_FILTER

def flat_map_generator(texture, size):
    '''Receive str(path to texture) and tuple with size values (x, y). Generate
    flat map of selected size and attach invisible walls to its borders'''
    #todo: add fallback values in case size hasnt been specified
    size_x, size_y = size
    log.debug(f"Generating map of size {size_x}x{size_y}")
    map_size = (-size_x/2, size_x/2, -size_y/2, size_y/2)

    #removing the blur from our texture
    texture.set_magfilter(DEFAULT_SPRITE_FILTER)
    texture.set_minfilter(DEFAULT_SPRITE_FILTER)
    #initializing new cardmaker object
    #which is essentially our go-to way to create flat models
    floor = CardMaker('floor')
    #setting up card size
    floor.set_frame(*map_size)
    #attaching card to render and creating it's object
    #I honestly dont understand the difference between
    #this and card.reparent_to(render)
    #but both add object to scene graph, making it visible
    floor_object = render.attach_new_node(floor.generate())
    floor_object.set_texture(texture)
    #determining how often do we need to repeat our texture
    texture_x = texture.get_orig_file_x_size()
    texture_y = texture.get_orig_file_y_size()
    repeats_x = ceil(size_x/texture_x)
    repeats_y = ceil(size_y/texture_y)
    #repeating texture to avoid stretching when possible
    floor_object.set_tex_scale(TextureStage.getDefault(), repeats_x, repeats_y)
    #arranging card's angle
    floor_object.look_at((0, 0, -1))
    floor_object.set_pos(0, 0, FLOOR_LAYER)

    log.debug("Adding invisible walls to collide with on map's borders")
    wall_coordinates = [((map_size[0], 0, 0), (map_size[1], 0, 0)),
                        ((-map_size[0], 0, 0), (-map_size[1], 0, 0)),
                        ((0, map_size[2], 0), (0, map_size[3], 0)),
                        ((0, -map_size[2], 0), (0, -map_size[3], 0))]

    for sizes in wall_coordinates:
        wall_node = CollisionNode("wall")
        #it looks like without adding node to pusher (we dont need that there),
        #masks wont work. Thus for now I wont use them, as defaults seem to work
        wall_node.add_solid(CollisionPlane(Plane(*sizes)))
        wall = render.attach_new_node(wall_node)

import logging
from panda3d.core import CardMaker, Texture, CollisionPlane, Plane, CollisionNode
from Game import config

log = logging.getLogger(__name__)

#module where I specify character and other 2d objects

FLOOR_LAYER = config.FLOOR_LAYER

def flat_map_generator(texture, size_x, size_y):
    '''Receive str(path to texture), int(size x) and int(size y). Generate
    flat map of selected size and attach invisible walls to its borders'''
    log.debug(f"Generating map")

    map_size = (-size_x/2, size_x/2, -size_y/2, size_y/2)
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
    floor_texture = loader.load_texture(texture)
    #settings its wrap modes (e.g the way it acts if it ends before model
    floor_texture.set_wrap_u(Texture.WM_repeat)
    floor_texture.set_wrap_v(Texture.WM_repeat)
    floor_card.set_texture(floor_texture)
    #arranging card's angle
    floor_card.look_at((0, 0, -1))
    floor_card.set_pos(0, 0, FLOOR_LAYER)


    log.debug(f"Adding invisible walls to collide with on map's borders")
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

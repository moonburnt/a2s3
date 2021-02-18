import logging
from panda3d.core import CardMaker, SamplerState, CollisionSphere, CollisionNode

log = logging.getLogger(__name__)

#module where I specify character and other 2d objects

def entity_2D(name, texture, size_x, size_y):
    '''Receive str(name), str(path to texture), int(size x) and int(size y)
    Returns entity's object and enemy's collisions'''
    log.debug(f"Initializing {name} object")

    entity_texture = loader.load_texture(texture)
    #setting filtering method to dont blur our sprite
    entity_texture.set_magfilter(SamplerState.FT_nearest)
    entity_texture.set_minfilter(SamplerState.FT_nearest)

    entity_frame = CardMaker(name)
    #setting character's size. Say, for 32x32 all of these need to be 16
    entity_frame.set_frame(-(size_x/2), (size_x/2), -(size_y/2), (size_y/2))

    entity_object = render.attach_new_node(entity_frame.generate())
    entity_object.set_texture(entity_texture)
    #billboard is effect to ensure that object always face camera the same
    #e.g this is the key to achieve that "2.5D style" I aim for
    entity_object.set_billboard_point_eye()
    #enable support for alpha channel
    #this is a float, e.g making it non-100% will require
    #values between 0 and 1
    entity_object.set_transparency(1)

    #setting character's collisions
    entity_collider = CollisionNode(name)
    #TODO: move this to be under character's legs
    #right now its centered on character's center
    entity_collider.add_solid(CollisionSphere(0, 0, 0, 15))
    entity_collision = entity_object.attach_new_node(entity_collider)

    #todo: maybe move ctrav stuff there

    return entity_object, entity_collision

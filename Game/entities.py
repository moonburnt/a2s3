import logging
from panda3d.core import CardMaker, SamplerState, CollisionSphere, CollisionNode
from Game import config

log = logging.getLogger(__name__)

#module where I specify character and other 2d objects

STATS = config.STATS

def entity_2D(name, texture, size=None):
    '''Receive str(name), str(path to texture). Optionally receive size=(x, y).
    Generate 2D object of selected size (if none - then based on image size).
    Returns dictionary with entity's name, stats, object, and collision.
    E.g dic['name']['stats']['object']['collision']'''
    log.debug(f"Initializing {name} object")

    if not size:
        log.debug("Attempting to determine object size from image")
        size_x = texture.get_orig_file_x_size()
        size_y = texture.get_orig_file_y_size()
    else:
        size_x, size_y = size
    log.debug(f"{name}'s size has been set to {size_x}x{size_y}")

    #setting filtering method to dont blur our sprite
    texture.set_magfilter(SamplerState.FT_nearest)
    texture.set_minfilter(SamplerState.FT_nearest)

    entity_frame = CardMaker(name)
    #setting frame's size. Say, for 32x32 sprite all of these need to be 16
    entity_frame.set_frame(-(size_x/2), (size_x/2), -(size_y/2), (size_y/2))

    entity_object = render.attach_new_node(entity_frame.generate())
    entity_object.set_texture(texture)
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

    #attempting to find stats of entity with name {name} in STATS
    #if not found - will fallback to STATS['default']
    if name in STATS:
        entity_stats = STATS[name]
    else:
        entity_stats = STATS['default']
    log.debug(f"Set {name}'s stats to be {entity_stats}")

    entity = {}
    entity['name'] = name
    entity['stats'] = entity_stats
    entity['object'] = entity_object
    entity['collision'] = entity_collision

    return entity

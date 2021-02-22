import logging
from panda3d.core import CardMaker, TextureStage, CollisionSphere, CollisionNode
from Game import config

log = logging.getLogger(__name__)

#module where I specify character and other 2d objects

STATS = config.STATS
SKILLS = config.SKILLS
DEFAULT_SPRITE_SIZE = config.DEFAULT_SPRITE_SIZE
DEFAULT_SPRITE_FILTER = config.DEFAULT_SPRITE_FILTER

#maybe move this to some other module? idk
#also it would be good idea to make spritesheets not on per-character, but on
#per-image base. But this would require some standard sprite size to be set
def cut_spritesheet(spritesheet, size):
    '''Receive str(path to spritesheet) and tuple of sprite size = (x, y). Based
    on sprite size and size of spritesheet, make list of offsets for each sprite
    on the sheet, which can later be used to select, some particular sprite to use.
    Then returns said list to function that requested it'''

    #for now, this has 2 limitations:
    # 1. Spritesheet HAS TO DIVIDE TO PROVIDED SPRITE SIZE WITHOUT REMAINDER. If
    #it doesnt cut to perfect sprites, you will get strange results during using
    #some of these sprites.
    # 2. There should be EVEN amount of sprite rows and columns. Otherwise - see
    #above. This is because of limitation of set_tex_offset() and set_tex_scale()
    #functions, both of which operate with floats between 0 and 1 to determine the
    #position. And, as you can guess - you cant divide 1 to odd number perfectly.
    #I assume, its possible to fix both of these. But right now I have no idea how
    #As for first - maybe cut garbage data with PNMimage module, before processing?

    log.debug(f"Attempting to cut spritesheet into sprites of {size} size")
    size_x, size_y = size

    #Determining amount of sprites in each row
    spritesheet_x = spritesheet.get_orig_file_x_size()
    spritesheet_y = spritesheet.get_orig_file_y_size()

    sprite_columns = int(spritesheet_x / size_x)
    sprite_rows = int(spritesheet_y / size_y)
    log.debug(f"Our sheet has {sprite_columns}x{sprite_rows} sprites")

    #idk if these should be flipped - its 3 am
    #this may backfire on values bigger than one... but it should never happen
    horizontal_offset_step = 1/sprite_columns
    vertical_offset_step = 1/sprite_rows
    log.debug(f"Offset steps are {horizontal_offset_step, vertical_offset_step}")

    offsets = []

    #dont ask questions, "it just works".
    #Basically, the thing is: originally, I did the following:
    #for row in range(0, sprite_rows):
    #BUT, this made offsets list start from bottom layer to top, which worked but
    #broke the whole "from top left to bottom right" style of image processing.
    #So I went for this "kinda hacky" solution. It works on 2x2 sheet, idk about
    #anything bigger than that
    for row in range(sprite_rows-1, -1, -1):
        log.debug(f"Processing row {row}")
        for column in range(0, sprite_columns):
            log.debug(f"Processing column {column}")
            horizontal_offset = column * horizontal_offset_step
            vertical_offset = row * vertical_offset_step
            log.debug(f"Got offsets: {horizontal_offset, vertical_offset}")
            offsets.append((horizontal_offset, vertical_offset))
    log.debug(f"Spritesheet contain following offsets: {offsets}")

    #maybe rename it into something more convenient?
    sprites = {}
    sprites['offset_steps'] = (horizontal_offset_step, vertical_offset_step)
    sprites['offsets'] = offsets

    log.debug(f"Got following data: {sprites}, returning")

    return sprites

def change_sprite(entity, sprite):
    '''Receive entity dictionary (from make_object function) and sprite number.
    Change entity's sprite to be selected number'''
    #this isnt the best thing in the world, as it cant iterate tru sprites yet
    #TODO: add ability to play selected animation sets with specified speed
    if entity['current_sprite'] != sprite:
        log.debug(f"Changing sprite of {entity['name']} to {sprite}")
        entity['object'].set_tex_offset(TextureStage.getDefault(),
                                        *entity['sprites'][sprite])
        entity['current_sprite'] = sprite

def make_object(name, texture, size = None):
    '''Receive str(name), str(path to texture). Optionally receive tuple size(x, y).
    Generate 2D object of selected size (if none - then based on image size).
    Returns dictionary with entity's name, stats, object, and collision.
    E.g dic['name']['stats']['object']['collision']'''
    log.debug(f"Initializing {name} object")

    if not size:
        size = DEFAULT_SPRITE_SIZE

    size_x, size_y = size
    log.debug(f"{name}'s size has been set to {size_x}x{size_y}")

    #setting filtering method to dont blur our sprite
    texture.set_magfilter(DEFAULT_SPRITE_FILTER)
    texture.set_minfilter(DEFAULT_SPRITE_FILTER)

    sprite_data = cut_spritesheet(texture, size)

    horizontal_scale, vertical_scale = sprite_data['offset_steps']
    #vertical_scale = vertical_offset_step
    offsets = sprite_data['offsets']

    entity_frame = CardMaker(name)
    #setting frame's size. Say, for 32x32 sprite all of these need to be 16
    entity_frame.set_frame(-(size_x/2), (size_x/2), -(size_y/2), (size_y/2))

    entity_object = render.attach_new_node(entity_frame.generate())
    entity_object.set_texture(texture)

    #okay, this does the magic
    #basically, to show the very first sprite of 2 in row, we set tex scale to half
    #(coz half is our normal char's size). If we will need to use it with sprites
    #other than first - then we also should adjust set_tex_offset accordingly
    #entity_object.set_tex_offset(TextureStage.getDefault(), 0.5, 0)
    #entity_object.set_tex_scale(TextureStage.getDefault(), 0.5, 1)
    entity_object.set_tex_scale(TextureStage.getDefault(), horizontal_scale, vertical_scale)

    #there is an interesting behavior of set_tex_offset worth remembering: 0, 0
    #and 1, 1 are equal things (and every other variation of 0 and 1. Meaning the
    #following 3 lines will be threated identically
    #entity_object.set_tex_offset(TextureStage.getDefault(), 1, 1)
    #entity_object.set_tex_offset(TextureStage.getDefault(), 0, 0)
    #entity_object.set_tex_offset(TextureStage.getDefault(), 0, 1)
    #this can be altered by manually setting texture wrap mode, but by default
    #thats what we get (iirc said mode is set to "repeat" out of box)

    #now, to use the stuff from cut_spritesheet function.
    #lets say, we need to use second sprite from sheet. Just do:
    #entity_object.set_tex_offset(TextureStage.getDefault(), *offsets[1])
    #but, by default, offset should be always set to 0. In case our object has
    #just one sprite. Or something like that
    default_sprite = 0
    entity_object.set_tex_offset(TextureStage.getDefault(), *offsets[default_sprite])

    #billboard is effect to ensure that object always face camera the same
    #e.g this is the key to achieve that "2.5D style" I aim for
    entity_object.set_billboard_point_eye()
    #enable support for alpha channel. This is a float, e.g making it non-100%
    #will require values between 0 and 1
    entity_object.set_transparency(1)

    #setting character's collisions
    entity_collider = CollisionNode(name)
    #TODO: move this to be under character's legs
    #right now its centered on character's center
    #coz its sphere and not oval - it doesnt matter if we use size_x or size_y
    #but, for sake of convenience - we are going for size_y
    entity_collider.add_solid(CollisionSphere(0, 0, 0, (size_y/2)))
    entity_collision = entity_object.attach_new_node(entity_collider)

    #todo: maybe move ctrav stuff there

    #attempting to find stats of entity with name {name} in STATS
    #if not found - will fallback to STATS['default']
    if name in STATS:
        entity_stats = STATS[name]
    else:
        entity_stats = STATS['default']
    log.debug(f"Set {name}'s stats to be {entity_stats}")

    #this is probably not the best way, but whatever - temporary solution
    #also this will crash if there are no skills, but that shouldnt happen
    entity_skills = {}
    for item in entity_stats['skills']:
        if item in SKILLS:
            entity_skills[item] = SKILLS[item].copy()

    entity = {}
    entity['name'] = name
    #its .copy() coz otherwise we will link to dictionary itself
    #and any change to stats of one enemy will affect other enemies
    #but this way, everything should be fine
    entity['stats'] = entity_stats.copy()
    entity['skills'] = entity_skills
    entity['object'] = entity_object
    entity['collision'] = entity_collision
    entity['sprites'] = offsets
    #this should be later remade to be "current animation" instead
    entity['current_sprite'] = default_sprite

    return entity

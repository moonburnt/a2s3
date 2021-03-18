import logging
from panda3d.core import (CardMaker, TextureStage, CollisionSphere, CollisionNode,
                          Texture, BitMask32)
from Game import config, spritesheet_cutter

log = logging.getLogger(__name__)

#module with general classes used as parents for 2d entity objects

STATS = config.STATS
SKILLS = config.SKILLS
ANIMS = config.ANIMS
DEFAULT_SPRITE_SIZE = config.DEFAULT_SPRITE_SIZE
DEFAULT_ANIMATIONS_SPEED = 0.1

class Entity2D:
    '''
    Main class, dedicated to creation of collideable 2D objects.
    '''
    def __init__(self, name, spritesheet = None, sprite_size = None,
                 hitbox_size = None, collision_mask = None, position = None,
                 animations_speed = None):
        log.debug(f"Initializing {name} object")

        if not animations_speed:
            animations_speed = DEFAULT_ANIMATIONS_SPEED
        self.animations_timer = animations_speed
        self.animations_speed = animations_speed

        if not sprite_size:
            sprite_size = DEFAULT_SPRITE_SIZE

        if not spritesheet:
            #I cant link assets above, coz their default value is None
            texture = base.assets.sprite[name]
        else:
            texture = base.assets.sprite[spritesheet]

        size_x, size_y = sprite_size
        log.debug(f"{name}'s size has been set to {size_x}x{size_y}")

        #the magic that allows textures to be mirrored. With that thing being
        #there, its possible to use values in range 1-2 to get versions of sprites
        #that will face the opposite direction, removing the requirement to draw
        #them with hands. Without thing thing being there, 0 and 1 will be threated
        #as same coordinates, coz "out of box" texture wrap mode is "repeat"
        texture.set_wrap_u(Texture.WM_mirror)
        texture.set_wrap_v(Texture.WM_mirror)
        sprite_data = spritesheet_cutter.cut_spritesheet(texture, sprite_size)

        horizontal_scale, vertical_scale = sprite_data['offset_steps']
        offsets = sprite_data['offsets']

        entity_frame = CardMaker(name)
        #setting frame's size. Say, for 32x32 sprite all of these need to be 16
        entity_frame.set_frame(-(size_x/2), (size_x/2), -(size_y/2), (size_y/2))

        entity_object = render.attach_new_node(entity_frame.generate())
        entity_object.set_texture(texture)

        #okay, this does the magic
        #basically, to show the very first sprite of 2 in row, we set tex scale
        #to half (coz half is our normal char's size). If we will need to use it
        #with sprites other than first - then we also should adjust offset accordingly
        #entity_object.set_tex_offset(TextureStage.getDefault(), 0.5, 0)
        #entity_object.set_tex_scale(TextureStage.getDefault(), 0.5, 1)
        entity_object.set_tex_scale(TextureStage.getDefault(),
                                    horizontal_scale, vertical_scale)

        #now, to use the stuff from cut_spritesheet function.
        #lets say, we need to use second sprite from sheet. Just do:
        #entity_object.set_tex_offset(TextureStage.getDefault(), *offsets[1])
        #but, by default, offset should be always set to 0. In case our object
        #has just one sprite. Or something like that
        default_sprite = 0
        entity_object.set_tex_offset(TextureStage.getDefault(),
                                     *offsets[default_sprite])

        #enable support for alpha channel. This is a float, e.g making it non-100%
        #will require values between 0 and 1
        entity_object.set_transparency(1)

        #if no position has been received - wont set it up
        if position:
            entity_object.set_pos(*position)

        #setting character's collisions
        entity_collider = CollisionNode(name)

        #if no collision mask has been received - using defaults
        if collision_mask:
            entity_collider.set_from_collide_mask(BitMask32(collision_mask))
            entity_collider.set_into_collide_mask(BitMask32(collision_mask))

        #TODO: move this to be under character's legs
        #right now its centered on character's center
        if hitbox_size:
            self.hitbox_size = hitbox_size
        else:
            #coz its sphere and not oval - it doesnt matter if we use x or y
            #but, for sake of convenience - we are going for size_y
            self.hitbox_size = (size_y/2)

        entity_collider.add_solid(CollisionSphere(0, 0, 0, self.hitbox_size))
        entity_collision = entity_object.attach_new_node(entity_collider)

        #this will explode if its not, but I dont have a default right now
        if name in ANIMS:
            entity_anims = ANIMS[name]

        self.name = name
        self.object = entity_object
        self.collision = entity_collision
        self.sprites = offsets
        #setting this to None may cause crashes on few rare cases, but going
        #for "idle_right" wont work for projectiles... So I technically add it
        #there for anims updater, but its meant to be overwritten at 100% cases
        self.current_animation = None
        #this will always be 0, so regardless of consistency I will live it be
        self.current_frame = default_sprite
        self.animations = entity_anims
        #death status, that may be usefull during cleanup
        self.dead = False

        #attaching python tags to object node, so these will be accessible during
        #collision events and similar stuff
        self.object.set_python_tag("name", self.name)

        #I thought to put ctrav there, but for whatever reason it glitched projectile
        #to fly into left wall. So I moved it to Creature subclass

        #debug function to show collisions all time
        #self.collision.show()

        #do_method_later wont work there, coz its indeed based on frames
        base.task_mgr.add(self.update_anims, "update entity's animations")

    def update_anims(self, event):
        '''Meant to run as taskmanager routine. Update entity's animation's frame
        each self.animations_speed seconds'''
        #safety check to dont do anything if custom anim isnt set or entity is
        #already dead. #Will maybe remove death statement later (coz gibs), idk
        if self.dead or not self.current_animation:
            return event.cont

        #ensuring that whatever below only runs if enough time has passed
        dt = globalClock.get_dt()
        self.animations_timer -= dt
        if self.animations_timer > 0:
            return event.cont

        #log.debug("Updating anims")
        #resetting anims timer, so countdown above will start again
        self.animations_timer = self.animations_speed

        if self.current_frame < self.animations[self.current_animation][1]:
            self.current_frame += 1
        else:
            self.current_frame = self.animations[self.current_animation][0]

        self.object.set_tex_offset(TextureStage.getDefault(),
                                   *self.sprites[self.current_frame])

        return event.cont

    def change_animation(self, action):
        '''Receive the name of new action. If current entity's animation is not
        it - then change entity's animation to match that action'''
        if self.current_animation != action:
            log.debug(f"Changing animation of {self.name} to {action}")
            self.current_frame = self.animations[action][0]
            self.current_animation = action

    def die(self):
        self.collision.remove_node()
        #idk if cleaning up tags will make sense if node will be removed anyway
        #left it there for future reference
        # python_tags = self.object.get_python_tags().copy()
        # for item in python_tags:
            # self.object.clear_python_tag(item)
        # del python_tags
        #it may be good idea for creatures to dont remove the node on death, but
        #play some death animation and then leave gibs on floor for a while. #TODO
        self.object.remove_node()
        self.dead = True
        log.debug(f"{self.name} is now dead")

class Creature(Entity2D):
    '''Subclass of Entity2D, dedicated to generation of player and enemies'''
    def __init__(self, name, spritesheet = None, sprite_size = None,
                 hitbox_size = None, collision_mask = None, position = None,
                 animations_speed = None):
        #Initializing all the stuff from parent class'es init to be done
        super().__init__(name, spritesheet, sprite_size, hitbox_size,
                         collision_mask, position, animations_speed)
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

        self.direction = 'right'
        self.current_animation = f'idle_{self.direction}'
        #its .copy() coz otherwise we will link to dictionary itself, which will
        #cause any change to stats of one enemy to affect every other enemy
        self.stats = entity_stats.copy()
        self.skills = entity_skills

        #list with timed status effects. When any of these reach 0 - they get ignored
        self.status_effects = {}

        self.object.set_python_tag("stats", self.stats)
        self.object.set_python_tag("get_damage", self.get_damage)

        #attaching our object's collisions to pusher and traverser
        #TODO: this way enemies will collide with walls too. Idk how to solve it
        #yet, without attaching walls to pusher (which will break them)
        #config.PUSHER.add_collider(self.collision, self.object)
        #config.CTRAV.add_collider(self.collision, config.PUSHER)
        base.pusher.add_collider(self.collision, self.object)
        base.cTrav.add_collider(self.collision, base.pusher)

        #billboard is effect to ensure that object always face camera the same
        #e.g this is the key to achieve that "2.5D style" I aim for
        self.object.set_billboard_point_eye()

        base.task_mgr.add(self.status_effects_handler, "status effects handler")

        #used to avoid issue with getting multiple damage func calls per frame
        #see game_window's damage functions
        self.last_collision_time = 0
        self.object.set_python_tag("last_collision_time", self.last_collision_time)

    def status_effects_handler(self, event):
        '''Meant to run as taskmanager routine. Each frame, reduce lengh of active
        status effects. When it reaches 0 - remove status effect'''
        if not self.status_effects:
            return event.cont

        #removing the task from being called again if target is already dead
        if self.dead:
            return

        dt = globalClock.get_dt()
        #copying to avoid causing issues by changing dic size during for loop
        se = self.status_effects.copy()
        for effect in se:
            self.status_effects[effect] -= dt
            if self.status_effects[effect] <= 0:
                del self.status_effects[effect]
                log.debug(f"{effect} effect has expired on {self.name}")

        return event.cont

    def get_damage(self, amount = None):
        '''Whatever stuff procs when target is about to get hurt'''
        if not amount:
            amount = 0

        #not getting any damage in case we are invulnerable
        if 'immortal' in self.status_effects:
            return

        self.stats['hp'] -= amount
        log.debug(f"{self.name} has received {amount} damage "
                  f"and is now on {self.stats['hp']} hp")

        if self.stats['hp'] <= 0:
            self.die()
            return

        #attempt to stun target for 0.5 seconds on taking damage. #TODO: make
        #configurable from skill's stats
        try:
            self.status_effects['stun'] += 0.5
        except KeyError:
            self.status_effects['stun'] = 0.5

        #this is placeholder. May need to track target's name in future to play
        #different damage sounds
        base.assets.sfx['damage'].play()

        self.change_animation(f"hurt_{self.direction}")

    def die(self):
        death_sound = f"{self.name}_death"
        #playing different sounds, depending if target has its own death sound or not
        try:
            base.assets.sfx[death_sound].play()
        except KeyError:
            log.warning(f"{self.name} has no custom death sound, using fallback")
            base.assets.sfx['default_death'].play()

        super().die()

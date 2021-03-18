import logging
from Game import config, entity2d

log = logging.getLogger(__name__)

#module where I specify character and other 2d objects

PLAYER_PROJECTILE_COLLISION_MASK = config.PLAYER_PROJECTILE_COLLISION_MASK

HIT_SCORE = 10
KILL_SCORE = 15

class Projectile(entity2d.Entity2D):
    '''Subclass of Entity2D, dedicated to creation of collideable effects'''
    def __init__(self, name, direction, damage = 0, object_size = None,
                 spritesheet = None, sprite_size = None, hitbox_size = None,
                 collision_mask = None, position = None, animations_speed = None):
        #for now we are only adding these to player, so no need for other masks
        #todo: split this thing into 2 subclasses: for player's and enemy's stuff
        collision_mask = PLAYER_PROJECTILE_COLLISION_MASK
        super().__init__(name, spritesheet, sprite_size, hitbox_size,
                         collision_mask, position, animations_speed)

        self.damage = damage
        self.object.set_python_tag("damage", self.damage)
        self.current_animation = 'default'
        #todo: make this configurable from dictionary, idk
        self.lifetime = 0.1
        self.dead = False

        #Idk about numbers. These work if caster is player, but what s about enemies?
        one, two, _ = direction
        self.object.look_at(one, two, 1)

        if object_size:
            self.object.set_scale(object_size)

        #schedulging projectile to die in self.lifetime seconds after spawn
        #I've heard this is not the best way to do that, coz do_method_later does
        #things based on frames and not real time. But for now it will do
        base.task_mgr.do_method_later(self.lifetime, self.die, "remove projectile")

    def die(self, event):
        super().die()
        return

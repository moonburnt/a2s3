## a2s3 - action arena game, written in python + panda3d
## Copyright (c) 2021 moonburnt
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see https://www.gnu.org/licenses/gpl-3.0.txt

import logging
from Game import entity2d, shared

log = logging.getLogger(__name__)

#module where I specify whatever stuff related to enemies

ENEMY_COLLISION_MASK = 0X03

HIT_SCORE = 10
KILL_SCORE = 15
ROT_TIMER = 15

class Enemy(entity2d.Creature):
    '''Subclass of Creature, dedicated to creation of enemies. Accepts everything
    like entity2d.Creature, but also affix. Which can be either "Normal", "Big" or
    "Small". Based on affix, size, health and movement speed of enemy will get altered'''
    def __init__(self, name:str, affix:str = "Normal", position = None):
        collision_mask = ENEMY_COLLISION_MASK
        category = shared.ENEMY_CATEGORY

        data = base.assets.enemies[name]
        spritesheet = data['Assets']['sprite']

        super().__init__(name = data['Main']['name'],
                         category = category,
                         spritesheet = base.assets.sprite[spritesheet],
                         animations = data['Animations'],
                         stats = data['Stats'],
                         skills = data['Main'].get('skills', None),
                         death_sound = data['Assets']['death_sound'],
                         hitbox_size = data['Main'].get('hitbox_size', None),
                         collision_mask = collision_mask,
                         position = position)

        self.rot_timer = ROT_TIMER
        self.can_be_removed = False

        if affix in ("Normal", "Big", "Small"):
            self.affix = affix
        else:
            self.affix = "Normal"

        if self.affix == "Big":
            #if enemy is big - reducing movement speed by 25%, but increasing
            #hp by 25% and size by x2
            self.stats['mov_spd'] = (self.stats['mov_spd']/100)*75
            self.stats['hp'] = (self.stats['hp']/100)*125
            self.object.set_scale(2)
        elif self.affix == "Small":
            #if enemy is small - increasing movement speed by 25%, but reducing
            #hp by 25% and size by x2
            self.stats['mov_spd'] = (self.stats['mov_spd']/100)*125
            self.stats['hp'] = (self.stats['hp']/100)*75
            self.object.set_scale(0.5)
        else:
            pass

        base.task_mgr.add(self.ai_movement_handler, "enemy movement handler")

        #id variable that will be set from game_window. Placed it there to avoid
        #possible crashes and to remind that its a thing that exists
        self.id = None

    def ai_movement_handler(self, event):
        '''This is but nasty hack to make enemies follow character. TODO: remake
        and move to its own module'''
        #TODO: maybe make it possible to chase not for just player?
        #TODO: not all enemies need to behave this way. e.g, for example, we can
        #only affect enemies that have their ['ai'] set to ['chaser']...
        #or something among these lines, will see in future

        #disable this handler if the enemy or player are dead. Without it, game
        #will crash the very next second after one of these events occur
        if self.dead or base.level.player.dead:
            return

        if 'stun' in self.status_effects:
            return event.cont

        player_position = base.level.player.object.get_pos()
        mov_speed = self.stats['mov_spd']

        enemy_position = self.object.get_pos()
        vector_to_player = player_position - enemy_position
        distance_to_player = vector_to_player.length()
        #normalizing vector is the key to avoid "flickering" effect, as its
        #basically ignores whatever minor difference in placement there are
        #I dont know how it works, lol
        vector_to_player.normalize()

        #workaround to ensure enemy will stay on its layer, even if its different
        #from player due to size difference or whatever else reasons
        vxy = vector_to_player.get_xy()
        #new_pos = enemy_position + (vector_to_player*mov_speed)
        new_pos = enemy_position + (vxy*mov_speed, 0)
        pos_diff = enemy_position - new_pos

        action = 'idle'

        #it may be good idea to also track camera angle, if I will decide
        #to implement camera controls, at some point or another
        if pos_diff[0] > 0:
            self.direction = 'right'
        else:
            self.direction = 'left'

        #this thing basically makes enemy move till it hit player, than play
        #attack animation. May backfire if player's sprite size is not equal
        #to player's hitbox
        if distance_to_player > shared.DEFAULT_SPRITE_SIZE[0]*2:
            action = 'move'
        else:
            action = 'attack'

        #workaround for issue when enemy keeps running into player despite already
        #colliding with it, which cause enemy's animation to go wild.
        #idk about the numbers yet. I think, ideally it should be calculated from
        #player's hitbox and enemy's hitbox... but for now this will do
        if distance_to_player > 6:
            self.object.set_pos(new_pos)
        #self.object.set_pos(new_pos)
        self.change_animation(f'{action}_{self.direction}')

        return event.cont

    def get_damage(self, amount = None):
        if self.dead:
            return
        super().get_damage(amount)
        #increasing score, based on HIT_SCORE value. It may be good idea to, instead,
        #increase it based on amount of damage received. But thats #TODO in future
        base.level.increase_score_multiplier()
        base.level.increase_score(HIT_SCORE)

    def mark_for_removal(self, event):
        '''Taskmanager routine that remove object's node and marks instance for
        removal from enemies list'''
        dt = globalClock.get_dt()
        self.rot_timer -= dt
        if self.rot_timer > 0:
            return event.cont

        self.can_be_removed = True
        self.animation = None
        self.object.remove_node()
        return

    def die(self):
        super().die()

        #remove enemy's gibs after self.rot_timer seconds
        base.task_mgr.add(self.mark_for_removal, "mark for removal")

        #for now this increase score based on HIT_SCORE+KILL_SCORE.
        #I dont think its a trouble, but may tweak at some point
        base.level.increase_score(KILL_SCORE)
        #increase player's kill counter
        base.level.kill_counter += 1
        log.debug(f"Kill counter has been increased to {base.level.kill_counter}")
        #reduce enemy counter
        base.level.enemy_amount -= 1

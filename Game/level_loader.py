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

#module dedicated to manage per-level stuff

import logging
from panda3d.core import CollisionTraverser, CollisionHandlerEvent, PandaNode, Vec3
from time import time
from random import randint, choice
from Game import entity2d, map_loader, shared, interface

log = logging.getLogger(__name__)

DEAD_CLEANUP_TIME = 5
#pause between calls to per-node's damage function. Making it anyhow lower will
#reintroduce the bug with multiple damage calls occuring during single frame
COLLISION_CHECK_PAUSE = 0.2
DEFAULT_SCORE_VALUE = 0
DEFAULT_SCORE_MULTIPLIER = 1
MAX_SCORE_MULTIPLIER = 5 #maybe just make it MULTIPLIER_INCREASE_STEP*10 ?
MULTIPLIER_INCREASE_STEP = 0.5

#this designed to work like that: default amount is amount of enemies on first wave
DEFAULT_ENEMIES_AMOUNT = 10
#lengh of pause between waves (in seconds)
PAUSE_BETWEEN_WAVES = 3
#maximum amount of enemies on screen
MAX_ENEMY_COUNT = 30
#pause between spawn checks
ENEMY_SPAWN_TIME = 2

#chance of unique enemy to spawn, in %
UNIQUE_ENEMY_CHANCE = 25

class LoadLevel:
    def __init__(self, player_class, map_scale: int):
        shared.ui.switch("loading")
        self.map_scale = map_scale
        self.player_class = player_class
        #doing it there before everything else to avoid issues during generation
        #of walls and entity objects
        log.debug("Setting up collision processors")
        base.cTrav = CollisionTraverser()
        base.chandler = CollisionHandlerEvent()
        #showing all occuring collisions. This is debatably better than manually
        #enabling collision.show() for each entity entry
        if shared.settings.show_collisions:
            base.cTrav.show_collisions(render)

        #this way we are basically naming the events we want to track, so these
        #will be possible to handle via base.accept and do the stuff accordingly
        #"in" is what happens when one object start colliding with another
        #"again" is if object continue to collide with another
        #"out" is when objects stop colliding
        base.chandler.addInPattern('%fn-into-%in')
        base.chandler.addAgainPattern('%fn-again-%in')
        #we dont need this one there
        #base.pusher.addOutPattern('%fn-out-%in')

        #tracking all the collision events related to instances of player colliding
        #with enemy projectile and causing related function to trigger on these
        base.accept(f'{shared.game_data.player_category}-into-{shared.game_data.enemy_projectile_category}',
                                                                    self.damage_player)
        base.accept(f'{shared.game_data.enemy_projectile_category}-into-{shared.game_data.player_category}',
                                                                    self.damage_player)
        base.accept(f'{shared.game_data.player_category}-again-{shared.game_data.enemy_projectile_category}',
                                                                    self.damage_player)
        base.accept(f'{shared.game_data.enemy_projectile_category}-again-{shared.game_data.player_category}',
                                                                    self.damage_player)

        #also tracking collisions of enemy with player's attack projectile
        base.accept(f'{shared.game_data.player_projectile_category}-into-{shared.game_data.enemy_category}', self.damage_enemy)
        base.accept(f'{shared.game_data.enemy_category}-into-{shared.game_data.player_projectile_category}', self.damage_enemy)
        base.accept(f'{shared.game_data.player_projectile_category}-again-{shared.game_data.enemy_category}', self.damage_enemy)
        base.accept(f'{shared.game_data.enemy_category}-again-{shared.game_data.player_projectile_category}', self.damage_enemy)

        #tracking collisions with walls, in order to create custom pusher-like
        #behaviour with collisioneventhandler
        base.accept(f'{shared.game_data.player_category}-into-wall', self.on_wall_collision)
        base.accept(f'{shared.game_data.player_category}-again-wall', self.on_wall_collision)
        base.accept(f'{shared.game_data.enemy_category}-into-wall', self.on_wall_collision)
        base.accept(f'{shared.game_data.enemy_category}-again-wall', self.on_wall_collision)

        #temporary solution for tracking collision of projectiles with objects
        #TODO: find a better name for function, add support for non-wall objects
        base.accept(f'{shared.game_data.player_projectile_category}-into-wall', self.on_object_collision)
        #base.accept(f'{shared.game_data.player_projectile_category}-again-wall', self.on_object_collision)
        base.accept(f'{shared.game_data.enemy_projectile_category}-into-wall', self.on_object_collision)
        #base.accept(f'{shared.game_data.enemy_projectile_category}-again-wall', self.on_object_collision)

        log.debug("Setting up camera")
        #this will set camera to be right above card.
        #changing first value will rotate the floor
        #changing second - change the angle from which we see floor
        #the last one is zoom. Negative values flip the screen
        #maybe I should add ability to change camera's angle, at some point?
        base.camera.set_pos(0, 700, 500)
        base.camera.look_at(0, 0, 0)

        log.debug("Initializing UI")
        self.player_hud = interface.PlayerHUD()
        #initializing death screen
        self.death_screen = interface.DeathScreen(
                                        restart_command = self.restart_level,
                                        exit_level_command = self.exit_level,
                                        exit_game_command = base.exit_game,
                                        )

        shared.ui.add(self.player_hud, "player hud")
        shared.ui.add(self.death_screen, "death screen")

        log.debug("Initializing handlers")
        #task manager is function that runs on background each frame and execute
        #whatever functions are attached to it
        base.task_mgr.add(self.remove_dead, "remove dead")

        #dictionary that stores default state of keys
        self.controls_status = {"move_up": False, "move_down": False,
                                "move_left": False, "move_right": False, "attack": False}

        #.accept() is method that track panda's events and perform certain functions
        #once these occur. "-up" prefix means key has been released
        base.accept(shared.settings.controls['move_up'],
                    self.change_key_state, ["move_up", True])
        base.accept(f"{shared.settings.controls['move_up']}-up",
                    self.change_key_state, ["move_up", False])
        base.accept(shared.settings.controls['move_down'],
                    self.change_key_state, ["move_down", True])
        base.accept(f"{shared.settings.controls['move_down']}-up",
                    self.change_key_state, ["move_down", False])
        base.accept(shared.settings.controls['move_left'],
                    self.change_key_state, ["move_left", True])
        base.accept(f"{shared.settings.controls['move_left']}-up",
                    self.change_key_state, ["move_left", False])
        base.accept(shared.settings.controls['move_right'],
                    self.change_key_state, ["move_right", True])
        base.accept(f"{shared.settings.controls['move_right']}-up",
                    self.change_key_state, ["move_right", False])
        base.accept(shared.settings.controls['attack'],
                    self.change_key_state, ["attack", True])
        base.accept(f"{shared.settings.controls['attack']}-up",
                    self.change_key_state, ["attack", False])

        #TODO: dont autoload it, let loading screen handle this
        self.setup_level()

    def change_key_state(self, key_name, key_status):
        '''Receive str(key_name) and bool(key_status).
        Change key_status of related key in self.controls_status'''
        self.controls_status[key_name] = key_status
        log.debug(f"{key_name} has been set to {key_status}")

    def follow_player(self, event):
        '''Taskmanager routine that updates self.player_follower and sets its
        position to be the same as player. For as long as player is alive, ofc'''
        if self.player.dead or not self.player.node:
            return

        self.player_follower.set_pos(self.player.node.get_pos())
        return event.cont

    def setup_level(self):
        '''Set default level's variables'''
        log.debug("Generating the map")
        self.map = map_loader.FlatMap(shared.assets.sprite['floor'],
                                      size = shared.game_data.map_size,
                                      scale = self.map_scale)

        log.debug("Initializing player")
        #character's position should always render on shared.game_data.entity_layer
        #setting this lower may cause glitches, as below lies the floor_layer
        #hitbox is adjusted to match our current sprites. In case of change - will
        #need to tweak it manually
        self.player = entity2d.Player(self.player_class,
                                      position = self.map.player_spawnpoint)

        self.wave_number = 0
        self.enemy_increase = 10
        self.enemies_this_wave = DEFAULT_ENEMIES_AMOUNT
        #TODO: rework this thing to spawn multiple enemies per tick
        self.enemy_spawn_timer = ENEMY_SPAWN_TIME
        self.pause_between_waves = PAUSE_BETWEEN_WAVES

        #these will be our lists to store enemies and projectiles to reffer to
        self.enemies = []
        self.projectiles = []
        #and this is amount of time, per which dead objects get removed from these
        self.cleanup_timer = DEAD_CLEANUP_TIME

        #variable for enemy spawner to make debugging process easier. Basically,
        #its meant to increase with each new enemy and never reset until game over.
        #this can also be potentially used for some highscore stats
        self.enemy_id = 0

        #amount of enemies, killed by player
        self.kill_counter = 0

        #score is, well, a thing that increase each time you hit/kill enemy.
        #in future there may be ability to spend it on some powerups, but for
        #now its only there for future leaderboards
        self.score = 0
        #score multiplier is a thing, that, well, increase amount of score gained
        #for each action. For now, the idea is following: for each 10 hits to enemy
        #without taking damage, you increase it by MULTIPLIER_INCREASE_STEP. Getting
        #damage resets it to default value (which is 1). It may be good idea to
        #make it instead increase if player is using different skills in order
        #to kill enemies (and not repeating autoattack). But for now thats about it
        self.score_multiplier = 1
        #as said above - when below reaches 9 (coz count from 0), multiplier increase
        self.multiplier_increase_counter = 0
        #its variable and not len of enemy list, coz it doesnt clean up right away
        self.enemy_amount = 0

        #its done there and not in init, otherwise self.cleanup() will break it
        #setting up the node to which camera will be attached. Its goal is to
        #be contantly updated with task that will always set its position to
        #player's. Its done this way, because otherwise mirroring player's node
        #will also mirror camera. But in future it may also allow for some funny
        #stuff, like easy camera offsets and such.
        player_follower = PandaNode("player follower")
        self.player_follower = render.attach_new_node(player_follower)

        #making camera always follow character
        #base.camera.reparent_to(self.player.object)
        base.camera.reparent_to(self.player_follower)

        shared.music_player.crossfade(shared.assets.music['battle'])

        #its important to sync items there, otherwise they will show incorrect
        #values before related event occurs for first time
        #self.update_player_hud()
        base.task_mgr.add(self.update_player_hud, "player hud autoupdater")
        shared.ui.switch("player hud")

        base.task_mgr.add(self.wave_changer, "wave changer")

        #enabling self.player_follower to autoupdate
        base.task_mgr.add(self.follow_player, "player follower routine for camera")

    def spawn_enemies(self, event):
        '''If amount of enemies is less than MAX_ENEMY_COUNT: spawns enemy each
        ENEMY_SPAWN_TIME seconds. Meant to be ran as taskmanager routine'''
        #safety check to dont spawn more enemies if player is dead
        if self.player.dead:
            return

        if self.enemies_this_wave <= 0:
            #if not self.enemies:
            if self.enemy_amount <= 0:
                log.info("Wave cleared, initializing wave changer")
                self.player_hud.wave_cleared_msg.show()
                base.task_mgr.add(self.wave_changer, "wave changer")
                return
            return event.cont

        #this clock runs on background and updates each frame
        #e.g 'dt' will always be the amount of time passed since last frame
        #and no, "from time import sleep" wont fit for this - game will freeze
        #because in its core, task manager isnt like multithreading but async
        dt = globalClock.get_dt()

        #similar method can also be used for skill cooldowns, probably anims stuff
        self.enemy_spawn_timer -= dt
        if self.enemy_spawn_timer <= 0:
            log.debug("Checking if we can spawn enemy")
            self.enemy_spawn_timer = ENEMY_SPAWN_TIME
            if self.enemy_amount < MAX_ENEMY_COUNT:
                log.debug("Initializing enemy")
                #determining the distance to player from each spawnpoint and
                #spawning enemies on the furthest. Depending on map type, it may be
                #not best behavior. But for now it will do, as it solves the issue
                #with enemies spawning on top of player if player is sitting at
                #map's very corner. #TODO: add more "pick spawnpoint" variations
                player_position = self.player.node.get_pos()

                spawns = []
                for spawnpoint in self.map.enemy_spawnpoints:
                    spawn = *spawnpoint, shared.game_data.entity_layer
                    vec_to_player = player_position - spawn
                    vec_length = vec_to_player.length()
                    #spawns.append((vec_length, spawn))
                    spawns.append((vec_length, spawnpoint))

                #sort spawns by the very first number in tuple (which is lengh)
                spawns.sort()

                #picking up the spawn from last list's entry (e.g the furthest from player)
                #spawn_position = spawns[-1][1]
                spawn_xy = spawns[-1][1]

                #determining type of enemy to spawn
                spawn_chance = randint(0, 100)
                if spawn_chance < UNIQUE_ENEMY_CHANCE:
                    #for now there are only 2 types of enemies, choosing from them
                    affix = choice(("Big", "Small"))
                    #nasty workaround to avoid flying of small enemies and falling
                    #through the floor of big enemies. Once I will implement floor
                    #collision, this can be removed. #TODO
                    if affix == "Small":
                        spawn_position = *spawn_xy, shared.game_data.entity_layer/2
                    else:
                        spawn_position = *spawn_xy, shared.game_data.entity_layer*2
                else:
                    affix = "Normal"
                    spawn_position = *spawn_xy, shared.game_data.entity_layer

                enemy_type = "Cuboid"
                log.debug(f"Spawning {affix} {enemy_type} on {spawn_position}")
                enemy = entity2d.Enemy(name = enemy_type,
                                       position = spawn_position,
                                       affix = affix)
                enemy.id = self.enemy_id
                enemy.node.set_python_tag("id", enemy.id)
                self.enemy_id += 1
                self.enemy_amount += 1
                self.enemies_this_wave -= 1
                self.enemies.append(enemy)
                log.debug(f"There are currently {self.enemy_amount} enemies on screen")

        return event.cont

    def wave_changer(self, event):
        '''Taskmanager routine that runs between waves'''
        if self.player.dead:
            return

        dt = globalClock.get_dt()

        self.pause_between_waves -= dt
        if self.pause_between_waves > 0:
            return event.cont

        log.debug("Attempting to change the wave")
        self.pause_between_waves = PAUSE_BETWEEN_WAVES
        self.wave_number += 1

        #this formula is questionable at best, but for now it will do
        self.enemies_this_wave = int((DEFAULT_ENEMIES_AMOUNT/100)*self.enemy_increase*self.wave_number)
        #ensuring that no empty waves can occur
        if self.enemies_this_wave <= 1:
            self.enemies_this_wave = 1

        self.enemy_increase += int(self.enemy_increase/self.wave_number)
        log.debug(f"Enemy increase has been set to {self.enemy_increase}")

        #todo: show message about beginning of new wave
        log.info(f"Starting wave {self.wave_number} with {self.enemies_this_wave} enemies")
        self.player_hud.show_new_wave_msg(wave_number = self.wave_number,
                                          kill_requirement = self.enemies_this_wave)
        base.task_mgr.add(self.spawn_enemies, "enemy spawner")
        return

    def remove_dead(self, event):
        '''Designed to run as taskmanager routine. Each self.cleanup_timer secs,
        remove all dead enemies and projectiles from related lists'''
        #shutdown the task if player has died, coz there is no point
        if self.player.dead:
            return

        dt = globalClock.get_dt()
        self.cleanup_timer -= dt
        if self.cleanup_timer > 0:
            return event.cont

        self.cleanup_timer = DEAD_CLEANUP_TIME
        log.debug(f"Cleaning up dead entities from memory")
        for entity in self.enemies:
            #if entity.dead:
            if entity.can_be_removed:
                self.enemies.remove(entity)

        for entity in self.projectiles:
            if entity.dead:
                self.projectiles.remove(entity)

        return event.cont

    def sort_collision(self, collision_event, hitter_category: str):
        '''Getting collision event and name of python tag "category", we are seeking
        for. Checking both collisions for this tag and return tuple of objects (hitter,
        target) (actual objects, NOT collision nodes). If none match, return None'''
        #maybe I should rename this function to something like "find hitter", idk

        hit = collision_event.get_from_node_path()
        hitter_object = hit.get_parent()
        tar = collision_event.get_into_node_path()
        target_object = tar.get_parent()

        #log.debug(f"{hit} collides with {tar}")

        hit_category = hitter_object.get_python_tag("category")
        tar_category = target_object.get_python_tag("category")

        #workaround for "None Type" exception that rarely occurs if one of colliding
        #nodes has died the very second it needs to be used in another collision
        if not hit_category or not tar_category:
            log.warning(f"Either {hitter_object} or {target_object} is dead, "
                         "collision wont occur")
            return

        if hit_category == hitter_category:
            hitter = hitter_object
            target = target_object
        elif tar_category == hitter_category:
            hitter = target_object
            target = hitter_object
        else:
            log.warning(f"No nodes with {hitter_category} category tag has been "
                        f"found in {collision_event} collision!")
            return

        return (hitter, target)

    def check_damage_possibility(self, target):
        '''Checking if its possible to damage specified target right now, based
        on its "last_collision_time" python tag'''
        #this is a workaround for issue caused by multiple collisions occuring
        #at single frame, so damage check function cant keep up with it. Basically,
        #we allow new target's collisions to only trigger damage function each
        #0.2 seconds. It may be good idea to abandon this thing in future in favor
        #of something like collisionhandlerqueue, but for now it works

        last_collision_time = target.get_python_tag("last_collision_time")
        current_time = time()
        if current_time - last_collision_time < COLLISION_CHECK_PAUSE:
            return False

        return True

    def damage_player(self, entry):
        '''Should be called from base.accept event handler when player collides
        with something that may hurt it. Checks if its possible to deal damage
        right now, then trigger player's "get_damage" function'''

        #colliders = self.sort_collision(entry, shared.game_data.enemy_category)
        colliders = self.sort_collision(entry, shared.game_data.enemy_projectile_category)
        if not colliders:
            #log.warning("Collision cant occur")
            return

        hitter, target = colliders

        if not self.check_damage_possibility(target):
            #log.debug("Collision cant occur right now")
            return

        target.set_python_tag("last_collision_time", time())

        #ds = hitter.get_python_tag("stats")
        #damage = ds['dmg']
        damage = hitter.get_python_tag("damage")
        damage_function = target.get_python_tag("get_damage")
        effects = hitter.get_python_tag("effects")

        log.debug(f"Attempting to deal {damage} damage to player")
        damage_function(damage, effects)

        if not hitter.get_python_tag("die_on_creature_collision"):
            return

        kill_hitter = hitter.get_python_tag("die_command")
        if kill_hitter:
            kill_hitter()

    def damage_enemy(self, entry):
        '''Should be called from base.accept event handler when enemy collides
        with something that may hurt it. Checks if its possible to deal damage
        right now, then trigger enemy's "get_damage" function'''

        colliders = self.sort_collision(entry, shared.game_data.player_projectile_category)
        if not colliders:
            #log.warning("Collision cant occur")
            return

        hitter, target = colliders

        if not self.check_damage_possibility(target):
            #log.debug("Collision cant occur right now")
            return

        #idk if I should've saved time from above...
        target.set_python_tag("last_collision_time", time())

        damage = hitter.get_python_tag("damage")
        damage_function = target.get_python_tag("get_damage")
        effects = hitter.get_python_tag("effects")

        target_name = target.get_python_tag('name')
        target_id = target.get_python_tag('id')
        log.debug(f"Attempting to deal {damage} damage to {target_name} ({target_id})")
        damage_function(damage, effects)

        #now solving the case when projectile needs to die on collision with creature
        if not hitter.get_python_tag("die_on_creature_collision"):
            return

        kill_hitter = hitter.get_python_tag("die_command")
        if kill_hitter:
            kill_hitter()

    def on_wall_collision(self, entry):
        '''Function that triggers if player or enemy collides with wall and pushes
        them back'''
        col = entry.get_from_node_path()
        col_obj = col.get_parent()
        wall = entry.get_into_node_path()
        #safety check for situations when object is in process of dying but hasnt
        #been removed completely yet
        if not col_obj:
            log.warning(f"{col} seems to be dead, collision wont occur")
            return

        #print(f"{col_obj} collides with wall")

        #first, lets get wall's parent, coz render/wall/wall is collision node,
        #and our tags are attached to render/wall, which is nodepath itself
        wall_obj = wall.get_parent()
        #getting pos like that, because of check mapgen's comments on wall init
        wall_pos = wall.get_python_tag("position")[0]

        col_pos = col_obj.get_pos()

        vector = col_pos - wall_pos
        vector.normalize()

        vx, vy = vector.get_xy()

        col_obj_stats = col_obj.get_python_tag("stats")
        #this will be ideal knockback if we collide with wall right on its center
        knockback = col_obj_stats['mov_spd']
        #knockback = col_obj_spd

        #workaround to fix the issue with entity running into a wall getting
        #pushed to wall's center. This way it wont hapen anymore... I think
        if wall_pos[1] < 0:
            vx = 0
            vy = 1
        elif wall_pos[1] > 0:
            vx = 0
            vy = -1
        else:
            pass

        if wall_pos[0] < 0:
            vx = 1
            vy = 0
        elif wall_pos[0] > 0:
            vx = -1
            vy = 0
        else:
            pass

        #this works for entities with any movement speed. However, there are two
        #old issues, I was unable to fix:
        # - If you will keep trying to run into the wall diagonally, your screen
        #will shake.
        # - Character will get pushed back as far as its running speed is. Meaning
        #creatures that move faster will get pushed closer to map's center. Its
        #not an issue for enemies (I think), but it may get annoying for player.
        #
        # For now, I have no idea how to solve both of these. Maybe at some point
        #I will re-implement collisionhandlerpusher for player, to deal with the
        #most annoying part of it #TODO
        new_pos = col_pos - (vx*knockback, vy*knockback, 0)

        col_obj.set_pos(new_pos)

    def on_object_collision(self, entry):
        '''Function that triggers if projectile collides with non-creature objects
        (walls and such)'''
        #It may need rework if I will ever implement ability to push objects
        col = entry.get_from_node_path()
        col_obj = col.get_parent()

        ricochets_amount = col_obj.get_python_tag("ricochets_amount")
        direction = col_obj.get_python_tag("direction")
        #this will break on negative ricochets_amount, but it shouldnt happen
        if ricochets_amount and direction:
            col_obj.set_python_tag("ricochets_amount", (ricochets_amount - 1))

            #this workaround obviously wont work for non-wall objects
            #but for now it will do #TODO
            wall = entry.get_into_node_path()
            wall_pos = wall.get_python_tag("position")[0]

            x, y, h = direction

            if wall_pos[0]:
                x = -x
                #dont ask me why and how rotation works, because "it just works"
                col_obj.set_h(180)

            if wall_pos[1]:
                y = -y

            col_obj.set_python_tag("direction", Vec3(x, y, h))
            #see comment above. I have no idea why it works and it will probably
            #break on billboard projectiles #TODO
            col_obj.set_r(-(col_obj.get_r()))

            #returning right there, because ricochets override whatever below
            return

        if not col_obj.get_python_tag("die_on_object_collision"):
            return

        kill_hitter = col_obj.get_python_tag("die_command")
        if kill_hitter:
            kill_hitter()

    def increase_score(self, amount):
        '''Increase score variable and displayed score amount by int(amount * self.score_multiplier)'''
        increase = amount*self.score_multiplier
        self.score += int(increase)
        log.debug(f"Increased score to {self.score}")

    def increase_score_multiplier(self):
        '''If self.score_multiplier is less than MAX_SCORE_MULTIPLIER - increase
        self.multiplier_increase_counter by 1. If it reaches 9 - increase
        self.score_multiplier by MULTIPLIER_INCREASE_STEP'''
        if self.score_multiplier >= MAX_SCORE_MULTIPLIER:
            log.debug("Already have max score multiplier, wont increase")
            return

        self.multiplier_increase_counter += 1
        if self.multiplier_increase_counter < 10:
            return

        self.multiplier_increase_counter = 0
        self.score_multiplier += MULTIPLIER_INCREASE_STEP
        log.debug(f"Increased score multiplier to {self.score_multiplier}")

    def reset_score_multiplier(self):
        '''Reset score multiplayer to defaults'''
        self.score_multiplier = DEFAULT_SCORE_MULTIPLIER
        self.multiplier_increase_counter = 0
        log.debug(f"Reset score multiplier to {self.score_multiplier}")

    def update_player_hud(self, event):
        '''Meant to be ran as taskmanager routine.
           Update all player hud elements to be in sync'''
        #todo: remake this into taskmanager thing that runs each frame
        #this way, there will be no need for dozen of other functions above
        if self.player.dead:
            return

        self.player_hud.update_hp(self.player.stats['hp'])
        self.player_hud.update_enemy_counter(self.enemy_amount)
        self.player_hud.update_multiplier(self.score_multiplier)
        self.player_hud.update_score(self.score)
        self.player_hud.update_current_wave(self.wave_number)

        return event.cont

    def on_player_death(self):
        '''Function called when player has died'''
        #TODO: rename this function to something less stupid
        self.death_screen.update_death_message(self.score,
                                               self.wave_number,
                                               self.kill_counter)

        shared.music_player.crossfade(shared.assets.music['death'])

        #interface.switch(self.death_screen)
        shared.ui.switch("death screen")

    def restart_level(self):
        '''Restarts a level from zero'''
        self.cleanup()
        self.setup_level()

    def cleanup(self):
        '''Remove whatever garbage has got stuck to scene'''
        #reparenting camera to render itself, to keep it above scene's center.
        #Otherwise it will keep showing player's remains regardless of stuff below
        base.camera.reparent_to(render)

        #this magic function remove all the nodes from scene, nullifying the need
        #to manually call .die() for each enemy and projectile. There is a caveat
        #tho - if I will ever attach some gui part of similar thing to base.render,
        #these will be gone too... I think.
        base.render.node().removeAllChildren()

        #JUST IN CASE, removing player object.
        self.player.node.remove_node()

        self.player = None
        self.enemies = None
        self.projectiles = None

    def exit_level(self):
        '''Exit level to main menu'''
        self.cleanup()

        shared.music_player.crossfade(shared.assets.music['menu_theme'])
        shared.ui.switch("main")

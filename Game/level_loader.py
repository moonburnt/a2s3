#module dedicated to manage per-level stuff

import logging
from direct.gui.OnscreenText import OnscreenText, TextNode, CollisionTraverser, CollisionHandlerPusher
from panda3d.core import NodePath
from time import time
from Game import entity_2D, map_loader, config
from direct.gui.DirectGui import DirectButton, DirectLabel

log = logging.getLogger(__name__)

ENTITY_LAYER = config.ENTITY_LAYER
DEAD_CLEANUP_TIME = 5
#pause between calls to per-node's damage function. Making it anyhow lower will
#reintroduce the bug with multiple damage calls occuring during single frame
COLLISION_CHECK_PAUSE = 0.2
DEFAULT_SCORE_VALUE = 0
DEFAULT_SCORE_MULTIPLIER = 1
MAX_SCORE_MULTIPLIER = 5 #maybe just make it MULTIPLIER_INCREASE_STEP*10 ?
MULTIPLIER_INCREASE_STEP = 0.5

#this designed to work like that: default amount is amount of enemies on first wave
DEFAULT_ENEMIES_AMOUNT = 5
#and multiplier is like current_amount*enemy_multiplier. So, basically. If our
#first wave has 5 enemies, second will have int(5*1.5), 2nd - int(7*1.5). And so on
ENEMY_MULTIPLIER = 1.5
#lengh of pause between waves (in seconds)
PAUSE_BETWEEN_WAVES = 5
#maximum amount of enemies on screen
MAX_ENEMY_COUNT = 10
#pause between spawn checks
ENEMY_SPAWN_TIME = 2

class LoadLevel:
    def __init__(self):
        #doing it there before everything else to avoid issues during generation
        #of walls and entity objects
        log.debug("Initializing collision processors")
        base.cTrav = CollisionTraverser()
        base.pusher = CollisionHandlerPusher()
        #avoiding the issue with entities falling under the floor on some collisions
        base.pusher.set_horizontal(True)
        #showing all occuring collisions. This is debatably better than manually
        #enabling collision.show() for each entity entry
        if config.SHOW_COLLISIONS:
            base.cTrav.show_collisions(render)

        log.debug("Generating the map")
        self.map = map_loader.FlatMap(base.assets.sprite['floor'], size = config.MAP_SIZE)

        log.debug("Initializing player")
        #character's position should always render on ENTITY_LAYER
        #setting this lower may cause glitches, as below lies the FLOOR_LAYER
        #hitbox is adjusted to match our current sprites. In case of change - will
        #need to tweak it manually
        self.player = entity_2D.Player("player", position = self.map.player_spawnpoint,
                                       hitbox_size = 6)

        log.debug("Initializing enemy spawner")
        self.wave_number = 1
        self.enemies_left = DEFAULT_ENEMIES_AMOUNT
        #TODO: rework this thing to spawn multiple enemies per tick
        self.enemy_spawn_timer = ENEMY_SPAWN_TIME

        #these will be our dictionaries to store enemies and projectiles to reffer to
        self.enemies = []
        self.projectiles = []
        #and this is amount of time, per which dead objects get removed from these
        self.cleanup_timer = DEAD_CLEANUP_TIME

        #variable for enemy spawner to make debugging process easier. Basically,
        #its meant to increase with each new enemy and never reset until game over.
        #this can also be potentially used for some highscore stats
        self.enemy_id = 0

        log.debug("Setting up collision event patterns")
        #this way we are basically naming the events we want to track, so these
        #will be possible to handle via base.accept and do the stuff accordingly
        #"in" is what happens when one object start colliding with another
        #"again" is if object continue to collide with another
        #"out" is when objects stop colliding
        base.pusher.addInPattern('%fn-into-%in')
        base.pusher.addAgainPattern('%fn-again-%in')
        #we dont need this one there
        #base.pusher.addOutPattern('%fn-out-%in')

        #because in our current version we need to deal damage to player on collide
        #regardless who started collided with whom - tracking all these events to
        #run function that deals damage to player. I have no idea why, but passing
        #things arguments to "damage target" function directly, like we did with
        #controls, didnt work. So we are using kind of "proxy function" to do that
        base.accept('player-into-enemy', self.damage_player)
        base.accept('enemy-into-player', self.damage_player)
        base.accept('player-again-enemy', self.damage_player)
        base.accept('enemy-again-player', self.damage_player)

        #also tracking collisions of enemy with player's attack projectile
        base.accept('attack-into-enemy', self.damage_enemy)
        base.accept('enemy-into-attack', self.damage_enemy)
        base.accept('attack-again-enemy', self.damage_enemy)
        base.accept('enemy-again-attack', self.damage_enemy)

        log.debug("Setting up camera")
        #this will set camera to be right above card.
        #changing first value will rotate the floor
        #changing second - change the angle from which we see floor
        #the last one is zoom. Negative values flip the screen
        #maybe I should add ability to change camera's angle, at some point?
        base.camera.set_pos(0, 700, 500)
        base.camera.look_at(0, 0, 0)
        #making camera always follow character
        base.camera.reparent_to(self.player.object)

        log.debug("Initializing player HUD")
        #with that thing being there, we are able to toggle player_hud with one
        #command together, without need to manually call for each node
        #TODO: move hud to separate module, maybe class
        self.player_hud = NodePath("player_hud")
        self.player_hud.reparent_to(base.aspect2d)
        self.player_hud.show()

        #create white-colored text with player's hp above player's head
        #TODO: move it to top left, add some image on background
        self.player_hp_ui = OnscreenText(text = f"{self.player.stats['hp']}",
                                         pos = (0, 0.01),
                                         scale = 0.05,
                                         fg = (1,1,1,1),
                                         parent = self.player_hud,
                                         mayChange = True)

        #score is, well, a thing that increase each time you hit/kill enemy.
        #in future there may be ability to spend it on some powerups, but for
        #now its only there for future leaderboards
        self.score = 0
        self.score_ui = OnscreenText(text = f"Score: {self.score}",
                                     pos = (-1.7, 0.9),
                                     #alignment side may look non-obvious, depending
                                     #on position and text it applies to
                                     align = TextNode.ALeft,
                                     scale = 0.05,
                                     fg = (1,1,1,1),
                                     parent = self.player_hud,
                                     mayChange = True)

        #score multiplier is a thing, that, well, increase amount of score gained
        #for each action. For now, the idea is following: for each 10 hits to enemy
        #without taking damage, you increase it by MULTIPLIER_INCREASE_STEP. Getting
        #damage resets it to default value (which is 1). It may be good idea to
        #make it instead increase if player is using different skills in order
        #to kill enemies (and not repeating autoattack). But for now thats about it
        self.score_multiplier = 1
        #as said above - when below reaches 9 (coz count from 0), multiplier increase
        self.multiplier_increase_counter = 0
        #visually it should be below score itself... I think?
        self.score_multiplier_ui = OnscreenText(text = f"Multiplier: {self.score_multiplier}",
                                                pos = (-1.7, 0.85),
                                                align = TextNode.ALeft,
                                                scale = 0.05,
                                                fg = (1,1,1,1),
                                                parent = self.player_hud,
                                                mayChange = True)

        #its variable and not len of enemy list, coz it doesnt clean up right away
        self.enemy_amount = 0
        #this one should be displayed on right... I think?
        self.enemy_amount_ui = OnscreenText(text = f"Enemies Left: {self.enemy_amount}",
                                            pos = (1.7, 0.85),
                                            align = TextNode.ARight,
                                            scale = 0.05,
                                            fg = (1,1,1,1),
                                            parent = self.player_hud,
                                            mayChange = True)

        #And this will be "game over" screen, shown on player's death
        #I REALLY need to move these somewhere else, at this point...
        self.death_screen = NodePath("death_screen")
        self.death_screen.reparent_to(base.aspect2d)
        self.death_screen.hide()

        self.high_score = DirectLabel(text = f"Your score is {self.score}",
                                      pos = (0, 0, 0.1),
                                      scale = 0.1,
                                      frameTexture = base.assets.sprite['button_active'],
                                      frameSize = (-4.5, 4.5, -0.5, 1),
                                      parent = self.death_screen)

        self.exit_button = DirectButton(text = "Restart",
                                        command = self.restart_level,
                                        pos = (0, 0, -0.1),
                                        scale = 0.1,
                                        frameTexture = base.button_textures,
                                        frameSize = (-1.5, 1.5, -0.5, 1),
                                        parent = self.death_screen)

        self.exit_button = DirectButton(text = "Exit",
                                        command = base.exit_game,
                                        pos = (0, 0, -0.3),
                                        scale = 0.1,
                                        frameTexture = base.button_textures,
                                        frameSize = (-1.5, 1.5, -0.5, 1),
                                        parent = self.death_screen)

        log.debug(f"Initializing controls handler")
        #task manager is function that runs on background each frame and execute
        #whatever functions are attached to it
        base.task_mgr.add(self.spawn_enemies, "enemy spawner")
        base.task_mgr.add(self.remove_dead, "remove dead")

        #dictionary that stores default state of keys
        self.controls_status = {"move_up": False, "move_down": False,
                                "move_left": False, "move_right": False, "attack": False}

        #.accept() is method that track panda's events and perform certain functions
        #once these occur. "-up" prefix means key has been released
        base.accept(config.CONTROLS['move_up'],
                    self.change_key_state, ["move_up", True])
        base.accept(f"{config.CONTROLS['move_up']}-up",
                    self.change_key_state, ["move_up", False])
        base.accept(config.CONTROLS['move_down'],
                    self.change_key_state, ["move_down", True])
        base.accept(f"{config.CONTROLS['move_down']}-up",
                    self.change_key_state, ["move_down", False])
        base.accept(config.CONTROLS['move_left'],
                    self.change_key_state, ["move_left", True])
        base.accept(f"{config.CONTROLS['move_left']}-up",
                    self.change_key_state, ["move_left", False])
        base.accept(config.CONTROLS['move_right'],
                    self.change_key_state, ["move_right", True])
        base.accept(f"{config.CONTROLS['move_right']}-up",
                    self.change_key_state, ["move_right", False])
        base.accept(config.CONTROLS['attack'],
                    self.change_key_state, ["attack", True])
        base.accept(f"{config.CONTROLS['attack']}-up",
                    self.change_key_state, ["attack", False])

    def change_key_state(self, key_name, key_status):
        '''Receive str(key_name) and bool(key_status).
        Change key_status of related key in self.controls_status'''
        self.controls_status[key_name] = key_status
        log.debug(f"{key_name} has been set to {key_status}")

    def spawn_enemies(self, event):
        '''If amount of enemies is less than MAX_ENEMY_COUNT: spawns enemy each
        ENEMY_SPAWN_TIME seconds. Meant to be ran as taskmanager routine'''
        #safety check to dont spawn more enemies if player is dead
        if not self.player.object:
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
                player_position = self.player.object.get_pos()

                spawns = []
                for spawnpoint in self.map.enemy_spawnpoints:
                    spawn = *spawnpoint, ENTITY_LAYER
                    vec_to_player = player_position - spawn
                    vec_length = vec_to_player.length()
                    spawns.append((vec_length, spawn))

                #sort spawns by the very first number in tuple (which is lengh)
                spawns.sort()

                #picking up the spawn from last list's entry (e.g the furthest from player)
                spawn_position = spawns[-1][1]
                log.debug(f"Spawning enemy on {spawn_position}")
                enemy = entity_2D.Enemy("enemy", position = spawn_position,
                                        hitbox_size = 12)
                enemy.id = self.enemy_id
                enemy.object.set_python_tag("id", enemy.id)
                self.enemy_id += 1
                self.update_enemy_counter(1)
                self.enemies.append(enemy)
                log.debug(f"There are currently {self.enemy_amount} enemies on screen")

        return event.cont

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
            if entity.dead:
                self.enemies.remove(entity)

        for entity in self.projectiles:
            if entity.dead:
                self.projectiles.remove(entity)

        return event.cont

    def damage_player(self, entry):
        '''Deals damage to player when it collides with some object that should
        hurt. Intended to be used from base.accept event handler'''
        hit = entry.get_from_node_path()
        tar = entry.get_into_node_path()

        #log.debug(f"{hit} collides with {tar}")

        #we are using "get_net_python_tag" over just "get_tag", coz this one will
        #search for whole tree, instead of just selected node. And since the node
        #we get via methods above is not the same as node we want - this is kind
        #of what we should use
        hit_name = hit.get_net_python_tag("name")
        tar_name = tar.get_net_python_tag("name")

        #workaround for "None Type" exception that rarely occurs if one of colliding
        #nodes has died the very second it needs to be used in another collision
        if not hit_name or not tar_name:
            log.warning("One of targets is dead, no damage will be calculated")
            return

        #bcuz we will damage player anyway - ensuring that object used as damage
        #source is not the player but whatever else it collides with
        if hit_name == "enemy":
            dmg_source = hit
            target = tar
        else:
            dmg_source = tar
            target = hit

        #this is a workaround for issue caused by multiple collisions occuring
        #at single frame, so damage check function cant keep up with it. Basically,
        #we allow new target's collisions to only trigger damage function each
        #0.2 seconds. It may be good idea to abandon this thing in future in favor
        #of something like collisionhandlerqueue, but for now it works
        tct = target.get_net_python_tag("last_collision_time")
        x = time()
        if x - tct < COLLISION_CHECK_PAUSE:
            return

        target.set_python_tag("last_collision_time", x)

        ds = dmg_source.get_net_python_tag("stats")
        dmg = ds['dmg']
        dmgfunc = target.get_net_python_tag("get_damage")
        dmgfunc(dmg)

    def damage_enemy(self, entry):
        #nasty placeholder to make enemy receive damage from collision with player's
        #projectile. Will need to rework it and merge with "damage_player" into
        #something like "damage_target" or idk
        hit = entry.get_from_node_path()
        tar = entry.get_into_node_path()

        #log.debug(f"{hit} collides with {tar}")

        hit_name = hit.get_net_python_tag("name")
        tar_name = tar.get_net_python_tag("name")

        if not hit_name or not tar_name:
            log.warning("One of targets is dead, no damage will be calculated")
            return

        if hit_name == "attack":
            dmg_source = hit
            target = tar
        else:
            dmg_source = tar
            target = hit

        tct = target.get_net_python_tag("last_collision_time")
        x = time()
        if x - tct < COLLISION_CHECK_PAUSE:
            return

        target.set_python_tag("last_collision_time", x)

        dmg = dmg_source.get_net_python_tag("damage")
        dmgfunc = target.get_net_python_tag("get_damage")

        target_name = target.get_net_python_tag('name')
        target_id = target.get_net_python_tag('id')
        log.debug(f"Attempting to deal damage to {target_name} ({target_id})")
        dmgfunc(dmg)

    def update_score(self, amount):
        '''Update score variable and displayed score amount by int(amount * self.score_multiplier)'''
        increase = amount*self.score_multiplier
        self.score += int(increase)
        self.score_ui.setText(f"Score: {self.score}")
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
        self.score_multiplier_ui.setText(f"Multiplier: {self.score_multiplier}")
        log.debug(f"Increased score multiplier to {self.score_multiplier}")

    def reset_score_multiplier(self):
        '''Reset score multiplayer to defaults'''
        self.score_multiplier = DEFAULT_SCORE_MULTIPLIER
        self.multiplier_increase_counter = 0
        self.score_multiplier_ui.setText(f"Multiplier: {self.score_multiplier}")
        log.debug(f"Reset score multiplier to {self.score_multiplier}")

    def update_enemy_counter(self, amount):
        '''Update self.enemy_amount by int amount. By default its +'''
        self.enemy_amount += amount
        self.enemy_amount_ui.setText(f"Enemies Left: {self.enemy_amount}")
        log.debug(f"Enemy amount has been set to {self.enemy_amount}")

    def restart_level(self):
        '''Restarts a level from zero'''
        for enemy in self.enemies:
            enemy.die()
        for projectile in self.projectiles:
            #this require something to be passed as argument, because usually it
            #runs as taskmanager routine with events
            projectile.die(0)
        #It doesnt seem like I need to reset other variables tho...
        self.enemies = []
        self.projectiles = []
        self.death_screen.hide()
        base.start_game()

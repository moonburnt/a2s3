#thou shall be file where I do everything related to game rendering
#effectively "Main", ye

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (WindowProperties, CollisionTraverser,
                          CollisionHandlerPusher, TextureStage)
from random import randint
from Game import entity_2D, map_loader, config, assets_loader

log = logging.getLogger(__name__)

ENTITY_LAYER = config.ENTITY_LAYER
DEFAULT_SPRITE_SIZE = config.DEFAULT_SPRITE_SIZE
MAX_ENEMY_COUNT = config.MAX_ENEMY_COUNT
ENEMY_SPAWN_TIME = config.ENEMY_SPAWN_TIME
ANIMATIONS_UPDATE_TIME = 0.1

class Main(ShowBase):
    def __init__(self):
        log.debug("Setting up the window")
        ShowBase.__init__(self)

        #disabling mouse to dont mess with camera
        self.disable_mouse()

        log.debug("Loading assets")
        self.assets = assets_loader.load_assets()

        log.debug("Configuring game's window")
        #setting up resolution
        screen_info = base.pipe.getDisplayInformation()
        #this is ugly, but it works, for now
        #basically we are ensuring that custom window's resolution isnt bigger
        #than screen size. And if yes - using default resolution instead

        #idk why, but these require at least something to display max available window size
        max_res = (screen_info.getDisplayModeWidth(0),
                   screen_info.getDisplayModeHeight(0))

        for cr, mr in zip(config.WINDOW_SIZE, max_res):
            if cr > mr:
                log.warning("Requested resolution is bigger than screen size, "
                            "will use defaults instead")
                resolution = config.DEFAULT_WINDOW_SIZE
                break
            else:
                resolution = config.WINDOW_SIZE

        window_settings = WindowProperties()
        window_settings.set_size(resolution)

        #ensuring that window cant be resized by dragging its borders around
        window_settings.set_fixed_size(True)
        #toggling fullscreen/windowed mode
        window_settings.set_fullscreen(config.FULLSCREEN)
        #setting window's title
        window_settings.set_title(config.GAME_NAME)
        #applying settings to our window
        self.win.request_properties(window_settings)
        log.debug(f"Resolution has been set to {resolution}")

        log.debug("Generating the map")
        map_loader.flat_map_generator(self.assets['sprites']['floor'],
                                      size = config.MAP_SIZE)
        #taking advantage of enemies not colliding with map borders and spawning
        #them outside of the map's corners. Idk about the numbers and if they should
        #be related to sprite size in anyway. Basically anything will do for now
        #later we will add some "fog of war"-like effect above map's borders, so
        #enemies spawning on these positions will seem more natural
        self.enemy_spawnpoints = [((config.MAP_SIZE[0]/2)+32, (config.MAP_SIZE[1]/2)+32),
                                  ((-config.MAP_SIZE[0]/2)-32, (-config.MAP_SIZE[1]/2)-32),
                                  ((config.MAP_SIZE[0]/2)+32, (-config.MAP_SIZE[1]/2)-32),
                                  ((-config.MAP_SIZE[0]/2)-32, (config.MAP_SIZE[1]/2)+32)]

        log.debug("Initializing player")
        self.player = entity_2D.Entity2D("player", self.assets['sprites']['character'])
        #setting character's position to always render on ENTITY_LAYER
        #setting this lower may cause glitches, as below lies the FLOOR_LAYER
        self.player.object.set_pos(0, 0, ENTITY_LAYER)

        log.debug("Initializing enemy spawner")
        self.enemy_spawn_timer = ENEMY_SPAWN_TIME
        self.enemies = []

        #variable working as "step" per which anims get updated
        self.animations_update_time = ANIMATIONS_UPDATE_TIME

        log.debug("Initializing collision processors")
        #I dont exactly understand the syntax, but other variable names failed
        #seems like these are inherited from ShowBase the same way as render
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        self.pusher.set_horizontal(False)

        #this way we are basically naming the events we want to track, so these
        #will be possible to handle via self.accept and do the stuff accordingly
        #"in" is what happens when one object start colliding with another
        #"again" is if object continue to collide with another
        #"out" is when objects stop colliding
        self.pusher.addInPattern('%fn-into-%in')
        self.pusher.addAgainPattern('%fn-again-%in')
        #we dont need this one there
        #self.pusher.addOutPattern('%fn-out-%in')

        #because in our current version we need to deal damage to player on collide
        #regardless who started collided with whom - tracking all these events to
        #run function that deals damage to player. I have no idea why, but passing
        #things arguments to "damage target" function directly, like we did with
        #controls, didnt work. So we are using kind of "proxy function" to do that
        self.accept('player-into-enemy', self.damage_player)
        self.accept('enemy-into-player', self.damage_player)
        self.accept('player-again-enemy', self.damage_player)
        self.accept('enemy-again-player', self.damage_player)

        self.pusher.add_collider(self.player.collision, self.player.object)
        self.cTrav.add_collider(self.player.collision, self.pusher)
        #showing all collisions on the scene (e.g visible to render)
        #this is better than manually doing collision.show() for each object
        if config.SHOW_COLLISIONS:
            self.cTrav.show_collisions(render)

        #this will set camera to be right above card.
        #changing first value will rotate the floor
        #changing second - change the angle from which we see floor
        #the last one is zoom. Negative values flip the screen
        #maybe I should add ability to change camera's angle, at some point?
        self.camera.set_pos(0, 700, 500)
        self.camera.look_at(0, 0, 0)
        #making camera always follow character
        self.camera.reparent_to(self.player.object)

        log.debug(f"Setting up background music")
        #setting volume like that, so it should apply to all music tracks
        music_mgr = base.musicManager
        music_mgr.set_volume(config.MUSIC_VOLUME)
        #same goes for sfx manager, which is a separate thing
        sfx_mgr = base.sfxManagerList[0]
        sfx_mgr.set_volume(config.SFX_VOLUME)
        menu_theme = self.assets['music']['menu_theme']
        menu_theme.set_loop(True)
        menu_theme.play()

        #enabling fps meter
        base.setFrameRateMeter(config.FPS_METER)

        log.debug(f"Initializing controls handler")
        #taskMgr is function that runs on background each frame
        #and execute whatever functions are attached to it with .add()
        self.task_manager = taskMgr.add(self.controls_handler,
                                        "controls handler")
        #adding movement handler to task manager
        self.task_manager = taskMgr.add(self.ai_movement_handler,
                                        "ai movement handler")
        self.task_manager = taskMgr.add(self.spawn_enemies,
                                        "enemy spawner")
        self.task_manager = taskMgr.add(self.animations_handler,
                                        "animations handler")

        #dictionary that stores default state of keys
        self.controls_status = {"move_up": False, "move_down": False,
                                "move_left": False, "move_right": False, "attack": False}

        #.accept() is method that track panda's events and perform certain functions
        #once these occur. "-up" prefix means key has been released
        self.accept(config.CONTROLS['move_up'],
                    self.change_key_state, ["move_up", True])
        self.accept(f"{config.CONTROLS['move_up']}-up",
                    self.change_key_state, ["move_up", False])
        self.accept(config.CONTROLS['move_down'],
                    self.change_key_state, ["move_down", True])
        self.accept(f"{config.CONTROLS['move_down']}-up",
                    self.change_key_state, ["move_down", False])
        self.accept(config.CONTROLS['move_left'],
                    self.change_key_state, ["move_left", True])
        self.accept(f"{config.CONTROLS['move_left']}-up",
                    self.change_key_state, ["move_left", False])
        self.accept(config.CONTROLS['move_right'],
                    self.change_key_state, ["move_right", True])
        self.accept(f"{config.CONTROLS['move_right']}-up",
                    self.change_key_state, ["move_right", False])
        self.accept(config.CONTROLS['attack'],
                    self.change_key_state, ["attack", True])
        self.accept(f"{config.CONTROLS['attack']}-up",
                    self.change_key_state, ["attack", False])

    def change_key_state(self, key_name, key_status):
        '''Receive str(key_name) and bool(key_status).
        Change key_status of related key in self.controls_status'''
        self.controls_status[key_name] = key_status
        log.debug(f"{key_name} has been set to {key_status}")

    def controls_handler(self, event):
        '''
        Intended to be used as part of task manager routine. Automatically receive
        event from task manager, checks if buttons are pressed and log it. Then
        return event back to task manager, so it keeps running in loop
        '''
        #safety check to ensure that player isnt dead, otherwise it will crash
        if not self.player.object:
            return event.cont

        #manipulating cooldowns on player's skills. It may be good idea to move
        #it to separate routine and check cooldowns of all entities on screen
        dt = globalClock.get_dt()

        #this seem to work reasonably decent. Not to jinx tho
        skills = self.player.skills
        for skill in skills:
            if skills[skill]['used']:
                skills[skill]['cur_cd'] -= dt
                if skills[skill]['cur_cd'] <= 0:
                    log.debug(f"Player's {skills[skill]['name']} has been recharged")
                    skills[skill]['used'] = False
                    skills[skill]['cur_cd'] = skills[skill]['def_cd']

        #idk if I need to export this to variable or call directly
        #in case it will backfire - turn this var into direct dictionary calls
        mov_speed = self.player.stats['mov_spd']

        #change the direction character face, based on mouse pointer position
        #this may need some tweaking if I will decide to add gamepad support
        #basically, the idea is the following: since camera is centered right
        #above our character, our char is the center of screen. Meaning positive
        #x will mean pointer is facing right and negative: pointer is facing left.
        #And thus char should do the same. This is kind of hack and will also
        #need tweaking if more sprites will be added. But for now it works
        #hint: this can also be used together with move buttons. E.g mouse change
        #the direction head/eyes face and keys change body. But that will depend
        #on amount of animations I would obtain. For now, lets leave it like that
        direction = 'right'
        mouse_watcher = base.mouseWatcherNode
        #ensuring that mouse pointer is part of game's window right now
        if mouse_watcher.has_mouse():
            mouse_x = mouse_watcher.get_mouse_x()
            if mouse_x > 0:
                direction = 'right'
            else:
                direction = 'left'

        #saving action to apply to our animation. Default is idle
        action = 'idle'

        #In future, these speed values may be affected by some items
        player_object = self.player.object
        if self.controls_status["move_up"]:
            player_object.set_pos(player_object.get_pos() + (0, -mov_speed, 0))
            action = "move"
        if self.controls_status["move_down"]:
            player_object.set_pos(player_object.get_pos() + (0, mov_speed, 0))
            action = "move"
        if self.controls_status["move_left"]:
            player_object.set_pos(player_object.get_pos() + (mov_speed, 0, 0))
            action = "move"
        if self.controls_status["move_right"]:
            player_object.set_pos(player_object.get_pos() + (-mov_speed, 0, 0))
            action = "move"

        #this is placeholder, that will automatically deal damage to first enemy
        #todo: collision check, etc etc etc
        if self.controls_status["attack"] and not skills['atk_0']['used']:
            skills['atk_0']['used'] = True
            #temporary check to ensure that we still have alive enemies
            if self.enemies:
                self.damage_target(self.enemies[0], self.player.stats['dmg'])

        #this is kinda awkward coz its tied to cooldown and may look weird
        #I may do something about that later... Like add "skill_cast_time" or idk
        if skills['atk_0']['used']:
            action = "attack"

        entity_2D.change_animation(self.player, f"{action}_{direction}")

        #it works a bit weird, but if we wont return .cont of task we received,
        #then task will run just once and then stop, which we dont want
        return event.cont

    def animations_handler(self, event):
        '''Meant to run as taskmanager routine. For each object on screen, update
        its animation's frame each self.animation_update_time seconds'''
        #safety check to avoid crash if player is already dead. Maybe I shouldnt
        #stop all anims and just remove player's object from list of things to update?
        if not self.player.object:
            return event.cont

        dt = globalClock.get_dt()

        self.animations_update_time -= dt

        #ensuring that whatever below only runs if enough time has passed
        if self.animations_update_time > 0:
            return event.cont

        #log.debug("Updating anims")
        #resetting anims timer, so countdown above will start again
        self.animations_update_time = ANIMATIONS_UPDATE_TIME

        #this is probably not the best way to iterate, but whatever
        for entity in self.player, *self.enemies:
            anim = entity.current_animation
            if entity.current_frame < entity.animations[anim][1]:
                entity.current_frame += 1
            else:
                entity.current_frame = entity.animations[anim][0]

            frame = entity.current_frame
            #I probably shouldnt keep this there but move to entity2d, but whatever
            entity.object.set_tex_offset(TextureStage.getDefault(),
                                            *entity.sprites[frame])

        return event.cont

    def ai_movement_handler(self, event):
        '''This is but nasty hack to make enemies follow character. TODO: remake
        and move to its own module'''
        #TODO: maybe make it possible to chase not for just player?
        #TODO: not all enemies need to behave this way. e.g, for example, we can
        #only affect enemies that have their ['ai'] set to ['chaser']...
        #or something among these lines, will see in future

        #hack to ignore this handler if the last enemy has died. Without it, game
        #will crash the very next second after last kill
        if not self.enemies or not self.player.object:
            return event.cont

        player_position = self.player.object.get_pos()
        for enemy in self.enemies:
            mov_speed = enemy.stats['mov_spd']

            enemy_position = enemy.object.get_pos()
            vector_to_player = player_position - enemy_position
            distance_to_player = vector_to_player.length()
            #normalizing vector is the key to avoid "flickering" effect, as its
            #basically ignores whatever minor difference in placement there are
            #I dont know the guts, but I believe it just cuts float's tail?
            vector_to_player.normalize()

            new_pos = enemy_position + (vector_to_player*mov_speed)
            pos_diff = enemy_position - new_pos

            action = 'idle'
            direction = 'right'

            #it may be good idea to also track camera angle, if I will decide
            #to implement camera controls, at some point or another
            if pos_diff[0] > 0:
                direction = 'right'
            else:
                direction = 'left'

            #this thing basically makes enemy move till it hit player, than play
            #attack animation. May backfire if player's sprite size is not equal
            #to player's hitbox
            if distance_to_player > DEFAULT_SPRITE_SIZE[0]:
                action = 'move'
                enemy.object.set_pos(new_pos)
            else:
                action = 'attack'

            #it may be wiser to move the thing there, but maybe later
            #enemy['object'].set_pos(new_pos)
            entity_2D.change_animation(enemy, f'{action}_{direction}')

        return event.cont

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
            enemy_amount = len(self.enemies)+1
            if enemy_amount <= MAX_ENEMY_COUNT:
                log.debug("Initializing enemy")
                enemy = entity_2D.Entity2D("enemy", self.assets['sprites']['enemy'])
                #picking up random spawnpoint out of available
                #there is -1 coz randint include the second number you pass to
                #it, not like "in range". E.g without it we will get "out of bound"
                spawnpoint = randint(0, len(self.enemy_spawnpoints)-1)
                log.debug(f"Spawning enemy on spawnpoint {spawnpoint}")
                enemy.object.set_pos(*self.enemy_spawnpoints[spawnpoint], ENTITY_LAYER)
                self.enemies.append(enemy)
                log.debug(f"There are currently {enemy_amount} enemies on screen")

        return event.cont

    def damage_target(self, target, amount = 0):
        '''Receive name of target. Optionally receive int(amount of damage).
        If not specified - will use 0. Decrease target's stats['hp'] by damage'''
        #I probably dont need to return this, for as long as its used on self. objects
        #I cant assign variables there, coz it will break the thing
        target.stats['hp'] -= amount
        log.debug(f"{target.name} has received {amount} damage "
                  f"and is now on {target.stats['hp']} hp")

        #idk if it should be there or on separate loop, but for now it will do
        if target.stats['hp'] <= 0:
            self.kill(target)
            return

        #this is placeholder. May need to track target's name in future to play
        #different damage sounds
        self.assets['sfx']['damage'].play()

    def kill(self, target):
        '''Receive name of target. Then remove its nodes, object and target itself.
        Log that target has been killed and play death sound'''
        #doing whatever stuff related to killing the player, coz its quite different.
        #maybe I should move player's death to another function, at some point?
        if target == self.player:
            position = self.player.object.get_pos()
            self.camera.reparent_to(render)
            self.cTrav.remove_collider(self.player.collision)
            self.pusher.remove_collider(self.player.collision)
            #we wont delete player variable itself tho, at least for now. Coz
            #otherwise many other functions would collapse
        #saving name into variable to print into debug output after target's clear
        name = target.name
        #it may be good idea to dont remove the node on death, but play some death
        #animation and then leave gibs on floor for a while. #TODO
        target.collision.remove_node()
        target.object.remove_node()
        #ensuring that the object we are killing is part of enemy gang.
        #If so - removing leftover data from enemies list
        if target in self.enemies:
            self.enemies.remove(target)
        log.debug(f"{name} is now dead")

        death_sound = f"{name}_death"
        #playing different sounds, depending if target has its own death sound or not
        try:
            self.assets['sfx'][death_sound].play()
        except KeyError:
            log.warning(f"{name} has no custom death sound, using fallback")
            self.assets['sfx']['default_death'].play()

    def damage_player(self, entry):
        '''Deals damage to player when it collides with some object that should
        hurt. Intended to be used from self.accept event handler'''
        hitter = entry.get_from_node_path()
        target = entry.get_into_node_path()

        log.debug(f"{hitter} collides with {target}")

        #we are using "get_net_python_tag" over just "get_tag", coz this one will
        #search for whole tree, instead of just selected node. And since the node
        #we get via methods above is not the same as node we want - this is kind
        #of what we should use
        hit_name = hitter.get_net_python_tag("name")
        tar_name = target.get_net_python_tag("name")

        #bcuz we will damage player anyway - ensuring that object used as damage
        #source is not the player but whatever else it collides with
        if hit_name == "player":
            dmg_source = target
        else:
            dmg_source = hitter

        ds = dmg_source.get_net_python_tag("stats")
        dmg = ds['dmg']
        self.damage_target(self.player, dmg)

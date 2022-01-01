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

# module dedicated to manage per-level stuff

import logging
from panda3d.core import CollisionTraverser, CollisionHandlerEvent, PandaNode, Vec3
from time import time
from random import randint, choice
from Game import entity2d, map_loader, shared, interface, collision_events

log = logging.getLogger(__name__)

DEAD_CLEANUP_TIME = 5
DEFAULT_SCORE_VALUE = 0
DEFAULT_SCORE_MULTIPLIER = 1
MAX_SCORE_MULTIPLIER = 5  # maybe just make it MULTIPLIER_INCREASE_STEP*10 ?
MULTIPLIER_INCREASE_STEP = 0.5

# this designed to work like that: default amount is amount of enemies on first wave
DEFAULT_ENEMIES_AMOUNT = 10
# lengh of pause between waves (in seconds)
PAUSE_BETWEEN_WAVES = 3
# maximum amount of enemies on screen
MAX_ENEMY_COUNT = 30
# pause between spawn checks
ENEMY_SPAWN_TIME = 2

# chance of unique enemy to spawn, in %
UNIQUE_ENEMY_CHANCE = 25


class LoadLevel:
    def __init__(self, player_class, map_scale: int):
        shared.ui.switch("loading")
        self.map_scale = map_scale
        self.player_class = player_class
        # doing it there before everything else to avoid issues during generation
        # of walls and entity objects
        log.debug("Setting up collision processors")
        base.cTrav = CollisionTraverser()
        base.chandler = CollisionHandlerEvent()
        # showing all occuring collisions. This is debatably better than manually
        # enabling collision.show() for each entity entry
        if shared.settings.show_collisions:
            base.cTrav.show_collisions(render)

        # this way we are basically naming the events we want to track, so these
        # will be possible to handle via base.accept and do the stuff accordingly
        # "in" is what happens when one object start colliding with another
        # "again" is if object continue to collide with another
        # "out" is when objects stop colliding
        base.chandler.addInPattern("%fn-into-%in")
        base.chandler.addAgainPattern("%fn-again-%in")
        # we dont need this one there
        # base.pusher.addOutPattern('%fn-out-%in')

        # tracking all the collision events related to instances of player colliding
        # with enemy projectile and causing related function to trigger on these
        base.accept(
            f"{shared.game_data.player_category}-into-{shared.game_data.enemy_projectile_category}",
            collision_events.creature_with_projectile,
            [shared.game_data.player_category],
        )
        base.accept(
            f"{shared.game_data.enemy_projectile_category}-into-{shared.game_data.player_category}",
            collision_events.creature_with_projectile,
            [shared.game_data.player_category],
        )
        base.accept(
            f"{shared.game_data.player_category}-again-{shared.game_data.enemy_projectile_category}",
            collision_events.creature_with_projectile,
            [shared.game_data.player_category],
        )
        base.accept(
            f"{shared.game_data.enemy_projectile_category}-again-{shared.game_data.player_category}",
            collision_events.creature_with_projectile,
            [shared.game_data.player_category],
        )

        # also tracking collisions of enemy with player's attack projectile
        base.accept(
            f"{shared.game_data.player_projectile_category}-into-{shared.game_data.enemy_category}",
            collision_events.creature_with_projectile,
            [shared.game_data.enemy_category],
        )
        base.accept(
            f"{shared.game_data.enemy_category}-into-{shared.game_data.player_projectile_category}",
            collision_events.creature_with_projectile,
            [shared.game_data.enemy_category],
        )
        base.accept(
            f"{shared.game_data.player_projectile_category}-again-{shared.game_data.enemy_category}",
            collision_events.creature_with_projectile,
            [shared.game_data.enemy_category],
        )
        base.accept(
            f"{shared.game_data.enemy_category}-again-{shared.game_data.player_projectile_category}",
            collision_events.creature_with_projectile,
            [shared.game_data.enemy_category],
        )

        # tracking collisions with map borders, in order to create custom
        # pusher-like behaviour with collisioneventhandler
        base.accept(
            f"{shared.game_data.player_category}-into-{shared.game_data.border_category}",
            collision_events.entity_with_border,
        )
        base.accept(
            f"{shared.game_data.player_category}-again-{shared.game_data.border_category}",
            collision_events.entity_with_border,
        )
        base.accept(
            f"{shared.game_data.enemy_category}-into-{shared.game_data.border_category}",
            collision_events.entity_with_border,
        )
        base.accept(
            f"{shared.game_data.enemy_category}-again-{shared.game_data.border_category}",
            collision_events.entity_with_border,
        )

        # same for projectiles
        base.accept(
            f"{shared.game_data.player_projectile_category}-into-{shared.game_data.border_category}",
            collision_events.entity_with_border,
        )
        base.accept(
            f"{shared.game_data.enemy_projectile_category}-into-{shared.game_data.border_category}",
            collision_events.entity_with_border,
        )

        # pushing enemies from eachother
        base.accept(
            f"{shared.game_data.enemy_category}-into-{shared.game_data.enemy_category}",
            collision_events.entity_with_entity,
        )
        base.accept(
            f"{shared.game_data.enemy_category}-again-{shared.game_data.enemy_category}",
            collision_events.entity_with_entity,
        )

        log.debug("Setting up camera")
        # this will set camera to be right above card.
        # changing first value will rotate the floor
        # changing second - change the angle from which we see floor
        # the last one is zoom. Negative values flip the screen
        # maybe I should add ability to change camera's angle, at some point?
        base.camera.set_pos(0, 700, 500)
        base.camera.look_at(0, 0, 0)

        log.debug("Initializing UI")
        self.player_hud = interface.PlayerHUD()

        # initializing death screen
        def show_lb():
            shared.ui.storage["leaderboard"].update_visible_scores()
            shared.ui.switch("leaderboard")

        self.death_screen = interface.DeathScreen(
            show_leaderboard_command=show_lb,
            restart_command=self.restart_level,
            exit_level_command=self.exit_level,
        )

        shared.ui.add(self.player_hud, "player hud")
        shared.ui.add(self.death_screen, "death screen")

        log.debug("Initializing handlers")
        # task manager is function that runs on background each frame and execute
        # whatever functions are attached to it
        base.task_mgr.add(self.remove_dead, "remove dead")

        # dictionary that stores default state of keys
        self.controls_status = {
            "move_up": False,
            "move_down": False,
            "move_left": False,
            "move_right": False,
            "attack": False,
        }

        # .accept() is method that track panda's events and perform certain functions
        # once these occur. "-up" prefix means key has been released
        base.accept(
            shared.settings.controls["move_up"],
            self.change_key_state,
            ["move_up", True],
        )
        base.accept(
            f"{shared.settings.controls['move_up']}-up",
            self.change_key_state,
            ["move_up", False],
        )
        base.accept(
            shared.settings.controls["move_down"],
            self.change_key_state,
            ["move_down", True],
        )
        base.accept(
            f"{shared.settings.controls['move_down']}-up",
            self.change_key_state,
            ["move_down", False],
        )
        base.accept(
            shared.settings.controls["move_left"],
            self.change_key_state,
            ["move_left", True],
        )
        base.accept(
            f"{shared.settings.controls['move_left']}-up",
            self.change_key_state,
            ["move_left", False],
        )
        base.accept(
            shared.settings.controls["move_right"],
            self.change_key_state,
            ["move_right", True],
        )
        base.accept(
            f"{shared.settings.controls['move_right']}-up",
            self.change_key_state,
            ["move_right", False],
        )
        base.accept(
            shared.settings.controls["attack"], self.change_key_state, ["attack", True]
        )
        base.accept(
            f"{shared.settings.controls['attack']}-up",
            self.change_key_state,
            ["attack", False],
        )

        # TODO: dont autoload it, let loading screen handle this
        self.setup_level()

    def change_key_state(self, key_name, key_status):
        """Receive str(key_name) and bool(key_status).
        Change key_status of related key in self.controls_status"""
        self.controls_status[key_name] = key_status
        log.debug(f"{key_name} has been set to {key_status}")

    def follow_player(self, event):
        """Taskmanager routine that updates self.player_follower and sets its
        position to be the same as player. For as long as player is alive, ofc"""
        if self.player.dead or not self.player.node:
            return

        self.player_follower.set_pos(self.player.node.get_pos())
        return event.cont

    def setup_level(self):
        """Set default level's variables"""
        log.debug("Generating the map")
        self.map = map_loader.FlatMap(
            shared.assets.sprite["floor"],
            size=shared.game_data.map_size,
            scale=self.map_scale,
        )
        self.map.generate()

        log.debug("Initializing player")
        # variables for spawners to make debugging process easier. Basically,
        # its meant to increase with each new creature of that type and never
        # reset until game over. This can also be potentially used for some
        # highscore stats
        self.enemy_id = 0
        # same for player, to unify the process
        self.player_id = 0

        # character's position should always render on shared.game_data.entity_layer
        # setting this lower may cause glitches, as below lies the floor_layer
        # hitbox is adjusted to match our current sprites. In case of change - will
        # need to tweak it manually
        self.player = entity2d.Player(self.player_class)
        self.player.spawn(self.map.player_spawnpoint)
        self.player.id = self.player_id
        self.player.node.set_python_tag("id", self.player.id)
        self.player_id += 1

        self.wave_number = 0
        self.enemy_increase = 10
        self.enemies_this_wave = DEFAULT_ENEMIES_AMOUNT
        # TODO: rework this thing to spawn multiple enemies per tick
        self.enemy_spawn_timer = ENEMY_SPAWN_TIME
        self.pause_between_waves = PAUSE_BETWEEN_WAVES

        # these will be our lists to store enemies and projectiles to reffer to
        self.enemies = []
        self.projectiles = []
        # and this is amount of time, per which dead objects get removed from these
        self.cleanup_timer = DEAD_CLEANUP_TIME

        # amount of enemies, killed by player
        self.kill_counter = 0

        # score is, well, a thing that increase each time you hit/kill enemy.
        # in future there may be ability to spend it on some powerups, but for
        # now its only there for future leaderboards
        self.score = 0
        # score multiplier is a thing, that, well, increase amount of score gained
        # for each action. For now, the idea is following: for each 10 hits to enemy
        # without taking damage, you increase it by MULTIPLIER_INCREASE_STEP. Getting
        # damage resets it to default value (which is 1). It may be good idea to
        # make it instead increase if player is using different skills in order
        # to kill enemies (and not repeating autoattack). But for now thats about it
        self.score_multiplier = 1
        # as said above - when below reaches 9 (coz count from 0), multiplier increase
        self.multiplier_increase_counter = 0
        # its variable and not len of enemy list, coz it doesnt clean up right away
        self.enemy_amount = 0

        # its done there and not in init, otherwise self.cleanup() will break it
        # setting up the node to which camera will be attached. Its goal is to
        # be contantly updated with task that will always set its position to
        # player's. Its done this way, because otherwise mirroring player's node
        # will also mirror camera. But in future it may also allow for some funny
        # stuff, like easy camera offsets and such.
        player_follower = PandaNode("player follower")
        self.player_follower = render.attach_new_node(player_follower)

        # making camera always follow character
        # base.camera.reparent_to(self.player.object)
        base.camera.reparent_to(self.player_follower)

        shared.music_player.crossfade(shared.assets.music["battle"])

        # its important to sync items there, otherwise they will show incorrect
        # values before related event occurs for first time
        # self.update_player_hud()
        base.task_mgr.add(self.update_player_hud, "player hud autoupdater")
        shared.ui.switch("player hud")

        base.task_mgr.add(self.wave_changer, "wave changer")

        # enabling self.player_follower to autoupdate
        base.task_mgr.add(self.follow_player, "player follower routine for camera")

    def spawn_enemies(self, event):
        """If amount of enemies is less than MAX_ENEMY_COUNT: spawns enemy each
        ENEMY_SPAWN_TIME seconds. Meant to be ran as taskmanager routine"""
        # safety check to dont spawn more enemies if player is dead
        if self.player.dead:
            return

        if self.enemies_this_wave <= 0:
            # if not self.enemies:
            if self.enemy_amount <= 0:
                log.info("Wave cleared, initializing wave changer")
                self.player_hud.wave_cleared_msg.show()
                base.task_mgr.add(self.wave_changer, "wave changer")
                return
            return event.cont

        # this clock runs on background and updates each frame
        # e.g 'dt' will always be the amount of time passed since last frame
        # and no, "from time import sleep" wont fit for this - game will freeze
        # because in its core, task manager isnt like multithreading but async
        dt = globalClock.get_dt()

        # similar method can also be used for skill cooldowns, probably anims stuff
        self.enemy_spawn_timer -= dt
        if self.enemy_spawn_timer <= 0:
            log.debug("Checking if we can spawn enemy")
            self.enemy_spawn_timer = ENEMY_SPAWN_TIME
            if self.enemy_amount < MAX_ENEMY_COUNT:
                log.debug("Initializing enemy")
                # determining the distance to player from each spawnpoint and
                # spawning enemies on the furthest. Depending on map type, it may be
                # not best behavior. But for now it will do, as it solves the issue
                # with enemies spawning on top of player if player is sitting at
                # map's very corner. #TODO: add more "pick spawnpoint" variations
                player_position = self.player.node.get_pos()

                spawns = []
                for spawnpoint in self.map.enemy_spawnpoints:
                    spawn = *spawnpoint, shared.game_data.entity_layer
                    vec_to_player = player_position - spawn
                    vec_length = vec_to_player.length()
                    # spawns.append((vec_length, spawn))
                    spawns.append((vec_length, spawnpoint))

                # sort spawns by the very first number in tuple (which is lengh)
                spawns.sort()

                # picking up the spawn from last list's entry (e.g the furthest from player)
                # spawn_position = spawns[-1][1]
                spawn_xy = spawns[-1][1]

                # determining type of enemy to spawn
                spawn_chance = randint(0, 100)
                if spawn_chance < UNIQUE_ENEMY_CHANCE:
                    # for now there are only 2 types of enemies, choosing from them
                    affix = choice(("Big", "Small"))
                    # nasty workaround to avoid flying of small enemies and falling
                    # through the floor of big enemies. Once I will implement floor
                    # collision, this can be removed. #TODO
                    if affix == "Small":
                        spawn_position = *spawn_xy, shared.game_data.entity_layer / 2
                    else:
                        spawn_position = *spawn_xy, shared.game_data.entity_layer * 2
                else:
                    affix = "Normal"
                    spawn_position = *spawn_xy, shared.game_data.entity_layer

                enemy_type = "Cuboid"
                log.debug(f"Spawning {affix} {enemy_type} on {spawn_position}")
                enemy = entity2d.Enemy(name=enemy_type, affix=affix)
                enemy.spawn(spawn_position)
                enemy.id = self.enemy_id
                enemy.node.set_python_tag("id", enemy.id)
                self.enemy_id += 1
                self.enemy_amount += 1
                self.enemies_this_wave -= 1
                self.enemies.append(enemy)
                log.debug(f"There are currently {self.enemy_amount} enemies on screen")

        return event.cont

    def wave_changer(self, event):
        """Taskmanager routine that runs between waves"""
        if self.player.dead:
            return

        dt = globalClock.get_dt()

        self.pause_between_waves -= dt
        if self.pause_between_waves > 0:
            return event.cont

        log.debug("Attempting to change the wave")
        self.pause_between_waves = PAUSE_BETWEEN_WAVES
        self.wave_number += 1

        # this formula is questionable at best, but for now it will do
        self.enemies_this_wave = int(
            (DEFAULT_ENEMIES_AMOUNT / 100) * self.enemy_increase * self.wave_number
        )
        # ensuring that no empty waves can occur
        if self.enemies_this_wave <= 1:
            self.enemies_this_wave = 1

        self.enemy_increase += int(self.enemy_increase / self.wave_number)
        log.debug(f"Enemy increase has been set to {self.enemy_increase}")

        # todo: show message about beginning of new wave
        log.info(
            f"Starting wave {self.wave_number} with {self.enemies_this_wave} enemies"
        )
        self.player_hud.show_new_wave_msg(
            wave_number=self.wave_number, kill_requirement=self.enemies_this_wave
        )
        base.task_mgr.add(self.spawn_enemies, "enemy spawner")
        return

    def remove_dead(self, event):
        """Designed to run as taskmanager routine. Each self.cleanup_timer secs,
        remove all dead enemies and projectiles from related lists"""
        # shutdown the task if player has died, coz there is no point
        if self.player.dead:
            return

        dt = globalClock.get_dt()
        self.cleanup_timer -= dt
        if self.cleanup_timer > 0:
            return event.cont

        self.cleanup_timer = DEAD_CLEANUP_TIME
        log.debug(f"Cleaning up dead entities from memory")
        for entity in self.enemies:
            # if entity.dead:
            if entity.can_be_removed:
                self.enemies.remove(entity)

        for entity in self.projectiles:
            if entity.dead:
                self.projectiles.remove(entity)

        return event.cont

    def increase_score(self, amount):
        """Increase score variable and displayed score amount by int(amount * self.score_multiplier)"""
        increase = amount * self.score_multiplier
        self.score += int(increase)
        log.debug(f"Increased score to {self.score}")

    def increase_score_multiplier(self):
        """If self.score_multiplier is less than MAX_SCORE_MULTIPLIER - increase
        self.multiplier_increase_counter by 1. If it reaches 9 - increase
        self.score_multiplier by MULTIPLIER_INCREASE_STEP"""
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
        """Reset score multiplayer to defaults"""
        self.score_multiplier = DEFAULT_SCORE_MULTIPLIER
        self.multiplier_increase_counter = 0
        log.debug(f"Reset score multiplier to {self.score_multiplier}")

    def update_player_hud(self, event):
        """Meant to be ran as taskmanager routine.
        Update all player hud elements to be in sync"""
        # todo: remake this into taskmanager thing that runs each frame
        # this way, there will be no need for dozen of other functions above
        if self.player.dead:
            return

        self.player_hud.update_hp(self.player.stats["hp"])
        self.player_hud.update_enemy_counter(self.enemy_amount)
        self.player_hud.update_multiplier(self.score_multiplier)
        self.player_hud.update_score(self.score)
        self.player_hud.update_current_wave(self.wave_number)

        return event.cont

    def on_player_death(self):
        """Function called when player has died"""
        # TODO: rename this function to something less stupid
        self.death_screen.update_death_message(
            self.score,
            self.wave_number,
            self.kill_counter,
        )

        shared.music_player.crossfade(shared.assets.music["death"])

        # interface.switch(self.death_screen)
        shared.user_data.update_leaderboard(
            score=self.score,
            player_class=self.player_class,
        )
        shared.user_data.save_leaderboards()

        shared.ui.switch("death screen")

    def restart_level(self):
        """Restarts a level from zero"""
        self.cleanup()
        self.setup_level()

    def cleanup(self):
        """Remove whatever garbage has got stuck to scene"""
        # reparenting camera to render itself, to keep it above scene's center.
        # Otherwise it will keep showing player's remains regardless of stuff below
        base.camera.reparent_to(render)

        # this magic function remove all the nodes from scene, nullifying the need
        # to manually call .die() for each enemy and projectile. There is a caveat
        # tho - if I will ever attach some gui part of similar thing to base.render,
        # these will be gone too... I think.
        base.render.node().removeAllChildren()

        # JUST IN CASE, removing player object.
        self.player.node.remove_node()

        self.player = None
        self.enemies = None
        self.projectiles = None

    def exit_level(self):
        """Exit level to main menu"""
        self.cleanup()

        shared.music_player.crossfade(shared.assets.music["menu_theme"])
        shared.ui.switch("main")

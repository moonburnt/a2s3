import logging
from panda3d.core import Point3, Plane, Vec2
from Game import config, entity2d

log = logging.getLogger(__name__)

#module where I specify character and other 2d objects

DEFAULT_SPRITE_SIZE = config.DEFAULT_SPRITE_SIZE

PLAYER_COLLISION_MASK = config.PLAYER_COLLISION_MASK

class Player(entity2d.Creature):
    '''Subclass of Creature, dedicated to creation of player'''
    def __init__(self, name, spritesheet = None, sprite_size = None,
                 hitbox_size = None, collision_mask = None, position = None,
                 animations_speed = None):
        collision_mask = PLAYER_COLLISION_MASK
        super().__init__(name, spritesheet, sprite_size, hitbox_size,
                         collision_mask, position, animations_speed)

        base.task_mgr.add(self.controls_handler, "controls handler")
        #the thing to track mouse position relatively to map. See attack handling
        #It probably could be better to move this thing to map func/class instead?
        #TODO
        self.ground_plane = Plane((0,0,1), (0,0,0))

    def controls_handler(self, event):
        '''
        Intended to be used as part of task manager routine. Automatically receive
        event from task manager, checks if buttons are pressed and log it. Then
        return event back to task manager, so it keeps running in loop
        '''
        #safety check to ensure that player isnt dead, otherwise it will crash
        if self.dead:
            return event.cont

        #manipulating cooldowns on player's skills. It may be good idea to move
        #it to separate routine and check cooldowns of all entities on screen
        dt = globalClock.get_dt()

        #this seem to work reasonably decent. Not to jinx tho
        skills = self.skills
        for skill in skills:
            if skills[skill]['used']:
                skills[skill]['cur_cd'] -= dt
                if skills[skill]['cur_cd'] <= 0:
                    log.debug(f"Player's {skills[skill]['name']} has been recharged")
                    skills[skill]['used'] = False
                    skills[skill]['cur_cd'] = skills[skill]['def_cd']

        if 'stun' in self.status_effects:
            return event.cont

        #idk if I need to export this to variable or call directly
        #in case it will backfire - turn this var into direct dictionary calls
        mov_speed = self.stats['mov_spd']

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
        mouse_watcher = base.mouseWatcherNode
        #ensuring that mouse pointer is part of game's window right now
        if mouse_watcher.has_mouse():
            mouse_x = mouse_watcher.get_mouse_x()
            if mouse_x > 0:
                self.direction = 'right'
            else:
                self.direction = 'left'

        #saving action to apply to our animation. Default is idle
        action = 'idle'

        #In future, these speed values may be affected by some items
        player_object = self.object
        if base.level.controls_status["move_up"]:
            player_object.set_pos(player_object.get_pos() + (0, -mov_speed, 0))
            action = "move"
        if base.level.controls_status["move_down"]:
            player_object.set_pos(player_object.get_pos() + (0, mov_speed, 0))
            action = "move"
        if base.level.controls_status["move_left"]:
            player_object.set_pos(player_object.get_pos() + (mov_speed, 0, 0))
            action = "move"
        if base.level.controls_status["move_right"]:
            player_object.set_pos(player_object.get_pos() + (-mov_speed, 0, 0))
            action = "move"

        #this is placeholder - its janky and spawns right above the player. #TODO
        if base.level.controls_status["attack"] and not skills['atk_0']['used']:
            skills['atk_0']['used'] = True

            #make player impossible to move on cast. It make controls a bit janky,
            #but remove that issue when player moving to some direction can catch
            #its own projectile. I may reconsider the way it works in future
            #self.status_effects['stun'] = skills['atk_0']['def_cd']/4
            self.status_effects['stun'] = 0.1

            #long story short, what happens there: we are getting mouse pointer's
            #position, then trying to translate it to the ground via plane.
            #this could probably be done faster and better, but for now it works
            mouse_pos = mouse_watcher.get_mouse()

            mouse_pos_3d = Point3()
            near = Point3()
            far = Point3()

            base.camLens.extrude(mouse_pos, near, far)
            self.ground_plane.intersects_line(mouse_pos_3d,
                                         render.get_relative_point(base.camera, near),
                                         render.get_relative_point(base.camera, far))

            hit_vector = mouse_pos_3d - player_object.get_pos()
            hit_vector.normalize()

            hit_vector_x, hit_vector_y = hit_vector.get_xy()
            #y has to be flipped if billboard_effect is active. Otherwise x has
            #to be flipped. Idk why its this way, probs coz first cam's num is 0
            #hit_vector_2D = hit_vector_x, -hit_vector_y
            hit_vector_2D = -hit_vector_x, hit_vector_y

            y_vec = Vec2(0, 1)
            angle = y_vec.signed_angle_deg(hit_vector_2D)

            pos_diff = DEFAULT_SPRITE_SIZE[0]/2
            #this is a bit awkward with billboard effect, coz slashing below
            #make projectile go into the ground. I should do something about it
            #TODO
            proj_pos = player_object.get_pos() + hit_vector*pos_diff
            attack = entity2d.Projectile("attack",
                                position = proj_pos,
                                #position = player_object.get_pos(),
                                direction = proj_pos,
                                #object_size = (1.2, 1.2, 1.2),
                                damage = self.stats['dmg'])

            #rotating projectile around 2d axis to match the shooting angle
            attack.object.set_r(angle)
            base.level.projectiles.append(attack)

        #this is kinda awkward coz its tied to cooldown and may look weird. I
        #may do something about that later... Like add "skill_cast_time" or idk
        if skills['atk_0']['used']:
            action = "attack"

        self.change_animation(f"{action}_{self.direction}")

        #it works a bit weird, but if we wont return .cont of task we received,
        #then task will run just once and then stop, which we dont want
        return event.cont

    def get_damage(self, amount = None):
        #giving player invinsibility frames on received damage
        #these shouldnt stack... I think? May backfire in future, idk
        super().get_damage(amount)
        #this check is there to avoid stacking up immortality
        if not 'immortal' in self.status_effects:
            #this is a bit longer than stun lengh, to let player escape
            self.status_effects['immortal'] = 0.7
        #updating the value on player's hp gui
        base.level.player_hp_ui.setText(f"{self.stats['hp']}")
        base.level.reset_score_multiplier()

    def die(self):
        #disable hud on death. This is not the most optimal thing, since it stays
        #there on background, just in hidden form. But for now it will do
        base.level.player_hud.hide()
        position = self.object.get_pos()
        #reparenting camera, to avoid crash on removal of player's node.
        #This may be unnecessary if we will implement gibs handler
        base.camera.reparent_to(render)
        super().die()

        #kinda nasty way to update the score part of death screen
        base.level.high_score.setText(f"Your score is {base.level.score}")
        base.level.death_screen.show()

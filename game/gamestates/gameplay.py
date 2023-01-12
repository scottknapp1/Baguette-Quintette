import pyasge
from game.gamedata import GameData
from game.gamestates.gamestate import GameState
from game.gamestates.gamestate import GameStateID
from game.gameobjects.enemyStuff import enemy
from game.gameobjects.enemyStuff.enemyTypeEnum import EnemyTypes
from game.gameobjects.weaponTypes import GunTypes
from game.gameobjects.Player import Player
from game.component import floatIntersects, spriteIntersects
from game.gameobjects.damageType import DamageType
from game.gameobjects.SoundHandler import TrackIndex


class GamePlay(GameState):

    def __init__(self, data: GameData) -> None:
        super().__init__(data)
        self.id = GameStateID.GAMEPLAY
        self.data.renderer.setClearColour(pyasge.COLOURS.BLACK)

        self.player = Player(data)
        self.data.player = self.player  # Creates a reference / pointer to the player for the enemy behaviour trees.
        self.player_movement = [0, 0]

        # sets up the camera and points it at the player
        self.camera = pyasge.Camera(self.player.spawnLocation, self.data.game_res[0], self.data.game_res[1])
        self.camera.zoom = 5

        self.player_moving = False
        self.footsteps_instanced = False
        self.allow_teleport = False
        self.allow_movement = True
        self.last_checkpoint = None
        self.destination_tp = []
        self.active_spikes = []
        self.active_chest = None
        self.footstep_timer = 0
        self.footstep = False
        self.death_played = False
        self.room_current = 0
        self.spike_dmg_cooldown = 0
        self.previous_room = None
        self.shader_timer = 0

        self.active_enemies = []
        self.data.retract_enemies = self.returnEnemies  # Stores a function to the returnEnemies function so that enemies can be returned within

    def click_handler(self, event: pyasge.ClickEvent) -> None:
        # depending on the mouse button pressed the current equipped weapon will switch/change
        if event.button is pyasge.MOUSE.MOUSE_BTN2 and \
                event.action is pyasge.MOUSE.BUTTON_PRESSED:
            if not self.player.bowEquipped:
                self.data.UserInterface.initWeaponSprite(GunTypes.SWORD)

                self.player.switchWeapons()
            elif not self.player.isShooting and not self.player.isAttacking:
                self.player.drawingString = True

        if event.button is pyasge.MOUSE.MOUSE_BTN2 and \
                event.action is pyasge.MOUSE.BUTTON_RELEASED and self.player.drawingString:
            self.player.rangeAttack()

        if event.button is pyasge.MOUSE.MOUSE_BTN1 and \
                event.action is pyasge.MOUSE.BUTTON_PRESSED:
            if self.player.bowEquipped:
                self.data.UserInterface.initWeaponSprite(GunTypes.BOW)
                self.player.switchWeapons()
            if not self.player.isAttacking and not self.player.isShooting:
                self.player.isAttacking = True
                for enem in self.active_enemies:
                    self.player.attack(enem)

    def move_handler(self, event: pyasge.MoveEvent) -> None:
        pass

    def update_inputs(self):
        # update controller inputs
        if self.data.gamepad.connected:
            if self.data.gamepad.RIGHT_TRIGGER > 0.1:
                if self.player.bowEquipped:
                    self.player.switchWeapons()
                if not self.player.isAttacking:
                    self.player.isAttacking = True
                    for enemy in self.active_enemies:
                        self.player.attack(enemy)

            # trigger inputs for shooting
            if self.data.gamepad.LEFT_TRIGGER > 0.1:
                if not self.player.bowEquipped:
                    self.player.switchWeapons()
                elif not self.player.isShooting and not self.player.isAttacking:
                    self.player.drawingString = True

            if self.data.prev_gamepad.LEFT_TRIGGER > 0.95:
                self.player.drawn = True

            if self.data.gamepad.LEFT_TRIGGER < 0.1 and self.player.drawingString and self.player.drawn:
                self.player.rangeAttack()
                self.player.drawn = False

            # interact button for the controller
            if self.data.gamepad.A:
                self.allow_teleport = True
                if self.checkChestCollisions():
                    self.chestInteract()
            if not self.data.gamepad.A and self.allow_teleport:
                self.allow_teleport = False

            # handles the player's  vector when the gamepad is connected
            if self.data.inputs.getGamePad().AXIS_LEFT_Y < -0.1:
                self.player_movement[1] = -1
            if self.data.inputs.getGamePad().AXIS_LEFT_Y > 0.1:
                self.player_movement[1] = 1
            if self.data.inputs.getGamePad().AXIS_LEFT_X < -0.1:
                self.player_movement[0] = -1
            if self.data.inputs.getGamePad().AXIS_LEFT_X > 0.1:
                self.player_movement[0] = 1

            if self.data.inputs.getGamePad().AXIS_LEFT_Y > -0.1 and self.player_movement[1] != 1:
                self.player_movement[1] = 0
            if self.data.inputs.getGamePad().AXIS_LEFT_Y < 0.1 and self.player_movement[1] != -1:
                self.player_movement[1] = 0
            if self.data.inputs.getGamePad().AXIS_LEFT_X > -0.1 and self.player_movement[0] != 1:
                self.player_movement[0] = 0
            if self.data.inputs.getGamePad().AXIS_LEFT_X < 0.1 and self.player_movement[0] != -1:
                self.player_movement[0] = 0

    def key_handler(self, event: pyasge.KeyEvent) -> None:

        # Handles the key presses for the player movement
        if event.action == pyasge.KEYS.KEY_PRESSED:
            if event.key == pyasge.KEYS.KEY_W:
                self.player_movement[1] = -1
            if event.key == pyasge.KEYS.KEY_S:
                self.player_movement[1] = 1
            if event.key == pyasge.KEYS.KEY_A:
                self.player_movement[0] = -1
            if event.key == pyasge.KEYS.KEY_D:
                self.player_movement[0] = 1

        # Handles the key releases for the player movement
        if event.action == pyasge.KEYS.KEY_RELEASED:
            if event.key == pyasge.KEYS.KEY_W and self.player_movement[1] != 1:
                self.player_movement[1] = 0
            if event.key == pyasge.KEYS.KEY_S and self.player_movement[1] != -1:
                self.player_movement[1] = 0
            if event.key == pyasge.KEYS.KEY_A and self.player_movement[0] != 1:
                self.player_movement[0] = 0
            if event.key == pyasge.KEYS.KEY_D and self.player_movement[0] != -1:
                self.player_movement[0] = 0

        # Interact button
        if event.action == pyasge.KEYS.KEY_RELEASED:
            if event.key == pyasge.KEYS.KEY_E:
                self.allow_teleport = False
        elif event.action == pyasge.KEYS.KEY_PRESSED:
            if event.key == pyasge.KEYS.KEY_E:
                self.allow_teleport = True
                if self.checkChestCollisions():
                    self.chestInteract()

        # This handles the footsteps
        if self.player_movement[0] != 0:
            self.player_moving = True
        elif self.player_movement[1] != 0:
            self.player_moving = True
        else:
            self.player_moving = False

        ####################### DEBUG KEY PLEASE KILL BEFORE SUBMISSION
        if event.key == pyasge.KEYS.KEY_PERIOD:
            self.data.bread = 4

    def chestInteract(self):
        # this handles the chests, one restores life, the other gives the player an additional baguette
        if self.active_chest[1] == 1:  # if type is a health chest.
            self.player.resetHealth()
            self.data.GameAudio.PlayEffect(TrackIndex.Chest)
            self.data.UserInterface.initHealth(self.player.health)

        elif self.active_chest[1] == 2:
            if not len(self.active_enemies):
                self.data.chests.remove(self.active_chest)
                self.active_chest = None
                self.data.bread += 1
                self.data.UserInterface.showBaguetteTextbox()
                self.data.UserInterface.initBaguette(self.data.bread)
                self.data.GameAudio.PlayEffect(TrackIndex.Chest)

    # Once E is pressed, searches the teleporters lists for the one the player is currently standing on, when found,
    # it will search if it has a brother by checking the pair value of the previous and next teleporter in the list
    # Thats also why we had to implement a sort in gamemap.py
    def teleInteract(self, teleporter, index):
        map_tps = self.data.teleporters
        # checks neighbor below
        if map_tps[index - 1][0] == teleporter[0]:
            destination = map_tps[index - 1]
        # checks neighbor above
        elif map_tps[index + 1][0] == teleporter[0]:
            destination = map_tps[index + 1]

        else:
            # prevents random teleportation if the teleporter doesn't have a brother
            destination = teleporter

        # Fixes the cursor to be in the same position of the screen after the teleport happens
        mouse_x = destination[1] - self.player.sprite.x
        mouse_y = destination[2] - self.player.sprite.y
        self.data.cursor.x += mouse_x
        self.data.cursor.y += mouse_y

        # updates the player location with the teleporter location
        self.player.sprite.x = destination[1]
        self.player.sprite.y = destination[2]

        # Updates the new active room number
        self.room_current = destination[5]

        # using the new player location the sword sprite gets placed propely in the screen
        self.player.sword.x = self.player.sprite.x - 9
        self.player.sword.y = self.player.sprite.y - 8
        # same for the bow
        self.player.bow.x = self.player.sprite.x
        self.player.bow.y = self.player.sprite.y
        self.allow_movement = True

    def updateCheckpoint(self):
        # checks if the player has been inside a teleporter, if it did,
        # it will update the last checkpoint the player has been on
        for checkpoint in self.data.checkpoints:

            if not checkpoint[0] == self.last_checkpoint:

                if floatIntersects(self.player.sprite.x, self.player.sprite.y, self.player.sprite.width,
                                   self.player.sprite.height, checkpoint[1], checkpoint[2], checkpoint[3],
                                   checkpoint[4]):
                    self.last_checkpoint = checkpoint[0]
                    checkpoint_xy = pyasge.Point2D(checkpoint[1] + (checkpoint[3] / 2),
                                                   checkpoint[2] + (checkpoint[4] / 2))
                    self.data.player.setPlayerRespawnPoint(checkpoint_xy)
                    break

    def fixed_update(self, game_time: pyasge.GameTime) -> None:
        for enemi in self.active_enemies:
            enemi.fixedUpdate(game_time)

    def update(self, game_time: pyasge.GameTime) -> GameStateID:
        # updates the timer for the shader
        self.shader_timer += game_time.fixed_timestep
        self.data.shaders["background_void"].uniform("time").set(self.shader_timer)

        # Plays footsteps when moving
        self.data.GameAudio.PlayFootsteps(game_time, self.player_moving)
        # checks if the player is colliding with nearby walls and moves it
        # if the player has 0 health movement will be nullified
        if self.allow_movement:
            if self.player.health <= 0:
                self.player_movement = [0, 0]

                if not self.death_played:
                    # plays the most iconic death sound of all time
                    self.data.GameAudio.PlayEffect(TrackIndex.oof)
                    self.death_played = True
            else:
                self.death_played = False

            self.player.update(game_time, self.player_movement[0], self.player_movement[1])

        # handles the spawning of the enemies if the player enters a new room
        if self.room_current is not self.previous_room:
            self.roomChecksReloader()

        # Enemy updater
        for enemy in self.active_enemies:
            enemy.update(game_time)

            # collision check for arrows
            self.player.checkArrowCollisions(enemy)

            if enemy.health < 1:
                self.active_enemies.remove(enemy)
                self.data.UserInterface.setEnemiesNumber(len(self.active_enemies))

        # Checks collision with the spikes
        self.check_spikes(game_time)
        self.updateCheckpoint()
        self.update_camera()
        self.update_inputs()
        self.teleUpdater()

        # lose condition
        if self.player.health <= 0 and self.player.lives == 1:
            self.data.UserInterface.transitionAnim()
            # wait for black bars to go down completely
            if self.data.UserInterface.transitionFeedback():
                return GameStateID.GAME_OVER

        # win condition
        if len(self.data.spawns) == 0 and len(self.active_enemies) == 0 and self.data.bread >= 4:
            self.data.UserInterface.transitionAnim()
            # wait for black bars to go down completely
            if self.data.UserInterface.transitionFeedback():
                return GameStateID.WINNER_WINNER

        return GameStateID.GAMEPLAY

    def teleUpdater(self):
        # displays a sign when standing on a teleporter, also makes teleporting possible in the first place
        for index, teleporter in enumerate(self.data.teleporters):

            # checks if the player is standing on a teleporter
            if floatIntersects(self.player.sprite.x, self.player.sprite.y, self.player.sprite.width,
                               self.player.sprite.height, teleporter[1], teleporter[2], teleporter[3], teleporter[4]):

                if len(self.active_enemies) == 0:
                    self.data.UserInterface.renderDialogueBox(True)

                    # if it is, calls the teleporting algorithm, and if E is pressed, teleportation will be allowed
                    if self.allow_teleport:
                        self.data.UserInterface.transitionAnim()
                        self.destination_tp = [teleporter, index]
                        # safely turns off the teleporting if the player keeps E pressed
                        self.allow_teleport = False
                        self.allow_movement = False

                    if self.data.UserInterface.transitionFeedback():
                        self.teleInteract(self.destination_tp[0], self.destination_tp[1])

                else:
                    self.data.UserInterface.renderDialogueBox(False)

    def check_spikes(self, game_time):
        # life gets decreased by 5 every half a second if player is on a spike
        # only checks the spikes in the active room
        if len(self.active_spikes):
            for spikes in self.active_spikes:
                if floatIntersects(spikes[0], spikes[1], spikes[2], spikes[3], self.player.sprite.x,
                                   self.player.sprite.y,
                                   self.player.sprite.width, self.player.sprite.height):
                    self.spike_dmg_cooldown += game_time.fixed_timestep
                    if self.spike_dmg_cooldown > 0.5:
                        self.player.receiveDamage(5, DamageType.normal_damage)
                        self.spike_dmg_cooldown = 0

    def roomChecksReloader(self):
        self.spawn_room_enemies()
        self.data.UserInterface.setEnemiesNumber(len(self.active_enemies))
        self.previous_room = self.room_current
        # Spike handler
        self.active_spikes.clear()
        for spikes in self.data.spikes:
            if spikes[4] == self.room_current:
                self.active_spikes.append(spikes)
        # Chest handler
        self.active_chest = None
        for chest in self.data.chests:
            if chest[0] == self.room_current:
                self.active_chest = chest

    def spawn_room_enemies(self):

        # rolls trough the enemy list and spawns all the enemies with the same room number as the current room
        # and also appends them into a list for them later to be removed
        spawns_to_remove = []
        for spawn in self.data.spawns:
            if spawn[0] == self.room_current:
                if self.room_current == 17:     # room 17 being the main boss room.
                    if self.data.bread != 4:
                        return

                if spawn[1] == 5:
                    self.data.GameAudio.PlayMusic(TrackIndex.Boss_music)
                type_enum: EnemyTypes = EnemyTypes(spawn[1])
                self.active_enemies.append(getattr(enemy, type_enum.name)(self.data, spawn))
                spawns_to_remove.append(spawn)

        # a bug was preventing this to be made in a single loop, so we created two
        for enem in spawns_to_remove:
            self.data.spawns.remove(enem)

        self.previous_room = self.room_current

    def checkChestCollisions(self):
        if self.active_chest is not None:
            if floatIntersects(self.active_chest[2], self.active_chest[3], self.active_chest[4], self.active_chest[5],
                               self.player.sprite.x, self.player.sprite.y, self.player.sprite.width,
                               self.player.sprite.height):
                return True
            else:
                return False
        else:
            return False

    def returnEnemies(self):
        # moves all the active enemies back to the spawn list
        # (for when the player dies)
        for enem in self.active_enemies:
            self.data.spawns.append(enem.spawn_details)

        self.active_enemies.clear()
        self.room_current = self.last_checkpoint

    def update_camera(self):
        """ Updates the camera based on gamepad input"""
        # makes the camera look at the player
        self.camera.lookAt(self.player.sprite.midpoint)

    def render(self, game_time: pyasge.GameTime) -> None:
        """ Renders the game world """
        self.data.renderer.setViewport(pyasge.Viewport(0, 0, self.data.game_res[0], self.data.game_res[1]))
        self.data.renderer.setProjectionMatrix(self.camera.view)
        self.data.game_map.render(self.data.renderer, game_time)

        for active_enemy in self.active_enemies:
            active_enemy.render()

        self.player.render()

    def render_ui(self) -> None:
        # UI is handled elsewhere
        pass

    def to_world(self, pos: pyasge.Point2D) -> pyasge.Point2D:
        """
        Converts from screen position to world position
        :param pos: The position on the current game window camera
        :return: Its actual/absolute position in the game world
        """
        view = self.camera.view
        x = (view.max_x - view.min_x) / self.data.game_res[0] * pos.x
        y = (view.max_y - view.min_y) / self.data.game_res[1] * pos.y
        x = view.min_x + x
        y = view.min_y + y

        return pyasge.Point2D(x, y)

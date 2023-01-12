import pyasge
import math
from game.gamedata import GameData
from game.gameobjects.SpriteAnimator import SpriteAnimator
from game.gameobjects.enemyStuff.enemy import Enemy
from game.component import floatIntersects
from game.component import spriteIntersects
from game.gameobjects.projectile import Projectile, DamageType
from game.gameobjects.SoundHandler import TrackIndex


class Player:

    def __init__(self, game_data: GameData):
        self.data = game_data

        # General
        self.sprite = pyasge.Sprite()
        self.anim = SpriteAnimator(self.sprite, game_data.textures["player"]["healthy"])
        self.sprite.z_order = 120
        self.virtual_wall_x = 0
        self.virtual_wall_y = 0
        self.speed = 85

        # Health & UI
        self.health = 100
        self.max_health = 100
        self.lives = 3
        self.data.UserInterface.initHealth(self.health)
        self.data.UserInterface.setLivesLeft(self.lives)

        # Spawning
        self.respawn_position = None    # Variable containing the X and Y of the respawn point
        self.closestXTile = 107
        self.closestYTile = 115
        self.spawnLocation = self.data.game_map.world([self.closestXTile, self.closestYTile])
        self.sprite.x = self.spawnLocation.x
        self.sprite.y = self.spawnLocation.y

        # Damage
        self.damaged = False
        self.damaged_type = None
        self.damage_timer = 0

        # Sword
        self.sword = pyasge.Sprite()
        self.swordAnim = SpriteAnimator(self.sword, game_data.textures["player"]["swordAttack"])
        self.sword.z_order = 119
        self.isAttacking = False
        self.meleeDamage = 40
        self.attackTimer = 0

        # Bow
        self.bow = pyasge.Sprite()
        self.bowAnim = SpriteAnimator(self.bow, game_data.textures["player"]["drawString"])
        self.bow.z_order = 121
        self.bow.x = self.sprite.x
        self.bow.y = self.sprite.y
        self.bowEquipped = False
        self.targetRotation = None
        self.drawingString = False
        self.drawn = False
        self.isShooting = False
        self.rangeDamage = 25
        self.shootTimer = 0

        self.arrows = []
        self.arrow_num = -1

        # Controller
        if self.data.gamepad.connected:
            self.data.cursor.opacity = 0

    def update(self, game_time: pyasge.GameTime, vector_x, vector_y):
        # plays the transition animation when the player dies
        if self.health <= 0:
            self.data.UserInterface.transitionAnim()
            if self.data.UserInterface.transitionFeedback():
                self.respawn()

        # Updates the direction of the sprite using the vector, diagonal movement is possible
        # Also uses a virtual wall to identify "actual" walls.
        # It also moves the position of the mouse cursor and the sword in the screen.
        self.updateMovements(game_time, vector_x, vector_y)

        self.updateDamageIndicator(game_time)

        self.UpdateBowAndArrow(game_time)

        self.updateSword(game_time)

        # Handles the sprite animation, alternates idle and moving.
        self.updateSprite(game_time, vector_x, vector_y)

    def updateSprite(self, game_time, vector_x, vector_y):
        if vector_x == 0 and vector_y == 0:
            self.anim.animateSprite(game_time, 0)
        else:
            self.anim.animateSprite(game_time, 1)

        # flips the sprite if needed
        if not self.isAttacking and not self.isShooting:
            if vector_x == -1:
                if not self.sprite.isFlippedOnX():
                    self.flipX()
            elif vector_x == 1:
                if self.sprite.isFlippedOnX():
                    self.flipNormal()
        else:
            # adapts the flipping of the sprite with the controller input
            if not self.data.gamepad.connected:
                if self.data.cursor.x > self.getMidPosition().x:
                    self.flipNormal()
                else:
                    self.flipX()
            else:
                pass

    def updateSword(self, game_time):
        # Handles melee attacking animation
        if self.isAttacking:
            self.attackTimer += game_time.fixed_timestep
            self.swordAnim.animateSprite(game_time, 0)

            # cooldown bar for the sword
            self.data.UserInterface.setCharge((self.attackTimer * 100) / 0.40)

            if self.attackTimer >= 0.40:
                self.swordAnim.resetAnimation()
                self.attackTimer = 0
                self.isAttacking = False

    def UpdateBowAndArrow(self, game_time):
        if self.bowEquipped:
            self.rotateBow()
        if self.drawingString:
            self.bowAnim.animateSprite(game_time, 2)
        # handles ranged shooting
        if self.isShooting:
            self.drawingString = False
            self.bowAnim.resetAnimation()
            self.shootTimer += game_time.fixed_timestep

            # cooldown bar for the bow
            self.data.UserInterface.setCharge((self.shootTimer * 100) / 0.30)

            if self.shootTimer >= 0.30:
                self.shootTimer = 0
                self.isShooting = False

        # if arrows have been shot updates them
        if len(self.arrows):
            for arrow in self.arrows:
                arrow.update(game_time)

                tile = self.data.game_map.tile(pyasge.Point2D(arrow.sprite.x + arrow.sprite.width / 2,
                                                              arrow.sprite.y + arrow.sprite.height / 2))
                if self.data.costs[tile[1]][tile[0]] >= 10:
                    self.arrows.remove(arrow)
                    self.arrow_num -= 1

    def updateMovements(self, game_time, vector_x, vector_y):
        self.tileCollisionCheck()

        if vector_x == 1 and self.virtual_wall_x != 1:
            self.sprite.x += 1 * self.speed * game_time.fixed_timestep
            self.sword.x += 1 * self.speed * game_time.fixed_timestep
            self.bow.x += 1 * self.speed * game_time.fixed_timestep
            self.data.cursor.x += 1 * self.speed * game_time.fixed_timestep

        elif vector_x == -1 and self.virtual_wall_x != 2:
            self.sprite.x += -1 * self.speed * game_time.fixed_timestep
            self.sword.x += -1 * self.speed * game_time.fixed_timestep
            self.bow.x += -1 * self.speed * game_time.fixed_timestep
            self.data.cursor.x += -1 * self.speed * game_time.fixed_timestep
        if vector_y == 1 and self.virtual_wall_y != 1:
            self.sprite.y += 1 * self.speed * game_time.fixed_timestep
            self.sword.y += 1 * self.speed * game_time.fixed_timestep
            self.bow.y += 1 * self.speed * game_time.fixed_timestep
            self.data.cursor.y += 1 * self.speed * game_time.fixed_timestep

        elif vector_y == -1 and self.virtual_wall_y != 2:
            self.sprite.y += -1 * self.speed * game_time.fixed_timestep
            self.sword.y += -1 * self.speed * game_time.fixed_timestep
            self.bow.y += -1 * self.speed * game_time.fixed_timestep
            self.data.cursor.y += -1 * self.speed * game_time.fixed_timestep

    def updateDamageIndicator(self, game_time):
        # Applies a shader as the player gets hit.
        if self.damaged:
            self.damage_timer += game_time.fixed_timestep
            self.data.shaders[self.damaged_type.name].uniform("time").set(self.damage_timer)

            if self.damage_timer > 1:
                self.damaged = False
                self.damage_timer = 0

    def rotateBow(self):
        if not self.data.gamepad.connected:
            self.targetRotation = -math.atan2((self.bow.x + 8) - self.data.cursor.x,
                                          (self.bow.y + 8) - self.data.cursor.y) - 300
        else:
            self.targetRotation = math.atan2(self.data.gamepad.AXIS_RIGHT_X, -self.data.gamepad.AXIS_RIGHT_Y) - 80
        self.bow.rotation = self.targetRotation

    def switchWeapons(self):
        if self.bowEquipped:
            self.bowEquipped = False
        else:
            self.bowEquipped = True

    def flipX(self):
        self.sprite.flip_flags = pyasge.Sprite.FlipFlags.FLIP_X
        self.sword.flip_flags = pyasge.Sprite.FlipFlags.FLIP_X
        self.sword.x = self.sprite.x - 11
        self.sword.y = self.sprite.y - 8

    def flipNormal(self):
        self.sprite.flip_flags = pyasge.Sprite.FlipFlags.NORMAL
        self.sword.flip_flags = pyasge.Sprite.FlipFlags.NORMAL
        self.sword.x = self.sprite.x - 6
        self.sword.y = self.sprite.y - 8

    def tileCollisionCheck(self):
        # updates the current position of the player
        self.closestXTile = int((self.sprite.x + self.sprite.width / 2) / 16)
        self.closestYTile = int((self.sprite.y + self.sprite.height / 2) / 16)

        # checks if one of the nearby tiles in the Y axis is blocking the player
        if self.data.costs[self.closestYTile - 1][self.closestXTile] >= 10:
            self.virtual_wall_y = 2
        elif self.data.costs[self.closestYTile + 1][self.closestXTile] >= 10:
            self.virtual_wall_y = 1
        else:
            self.virtual_wall_y = 0

        # checks if one of the nearby tiles in the X axis is blocking the player
        if self.data.costs[self.closestYTile][self.closestXTile - 1] >= 10:
            self.virtual_wall_x = 2
        elif self.data.costs[self.closestYTile][self.closestXTile + 1] >= 10:
            self.virtual_wall_x = 1
        else:
            self.virtual_wall_x = 0

    def getMidPosition(self):
        return pyasge.Point2D(self.sprite.x + self.sprite.width / 2, self.sprite.y + self.sprite.height / 2)

    def receiveDamage(self, damage, damage_type: DamageType):
        self.health -= damage
        self.data.UserInterface.updateHealth(self.health)
        self.damaged = True

        # Updates the look of the player in relation to the current health.
        if self.health > self.max_health * 0.75:
            self.anim = SpriteAnimator(self.sprite, self.data.textures["player"]["healthy"])
        elif self.max_health * 0.75 > self.health > self.max_health * 0.55:
            self.anim = SpriteAnimator(self.sprite, self.data.textures["player"]["damaged1"])
        elif self.max_health * 0.50 > self.health > self.max_health * 0.25:
            self.anim = SpriteAnimator(self.sprite, self.data.textures["player"]["damaged2"])
        elif self.health < self.max_health * 0.25:
            self.anim = SpriteAnimator(self.sprite, self.data.textures["player"]["damaged3"])

        self.damage_timer = 0
        self.damaged_type = damage_type

    def setPlayerRespawnPoint(self, new_position):
        # Saves the new player spawn-point
        self.respawn_position = new_position

    def attack(self, enemy: Enemy):
        if self.checkCollision(enemy):
            enemy.receiveDamage(self.meleeDamage, DamageType.normal_damage)

    def rangeAttack(self):
        # Handles everything about the player shooting arrows
        self.arrow_num += 1
        self.arrows.append(Projectile(DamageType.normal_damage, self.data.textures["projectile"]["arrow"],
                                      self.bow.x + 2, self.bow.y + 2))
        self.shootTimer = 0

        if not self.data.gamepad.connected:
            direction = pyasge.Point2D(self.sprite.x + 8 - self.data.cursor.x,
                                       self.sprite.y + 8 - self.data.cursor.y)
        else:
            direction = pyasge.Point2D(math.cos(self.targetRotation), math.sin(self.targetRotation))

        normalise = math.sqrt(direction.x * direction.x + direction.y * direction.y)
        direction.x /= normalise
        direction.y /= normalise

        self.rotateBow()
        self.arrows[self.arrow_num].setDirectionFloats(-direction.x, -direction.y)
        self.arrows[self.arrow_num].setRotation(self.targetRotation)
        self.isShooting = True

    def checkCollision(self, enemy):
        #  if self.data.cursor.x < self.getMidPosition().x:
        if self.sprite.isFlippedOnX():
            right = self.getMidPosition().x
            left = self.sprite.x - 16
        else:
            right = (self.sprite.x + self.sprite.width) + 16
            left = self.getMidPosition().x

        top = self.sprite.y - 16
        bottom = (self.sprite.y + self.sprite.width) + 16
        width = right - left
        height = bottom - top

        # returns true if the collision between enemy and collision box is true
        if floatIntersects(left, top, width, height, enemy.sprite.x, enemy.sprite.y,
                           enemy.sprite.width, enemy.sprite.height):
            return True
        return False

    def checkArrowCollisions(self, enemy: Enemy):
        for arrow in self.arrows:
            if spriteIntersects(arrow.sprite, enemy.sprite):
                enemy.receiveDamage(self.rangeDamage, DamageType.normal_damage)
                self.arrows.remove(arrow)
                self.arrow_num -= 1

    def respawn(self):
        # retracts the active enemies
        self.data.retract_enemies()
        # If the players called the last checkpoint saved will be called and the player will be respawned again
        if self.lives != 1:
            self.lives -= 1
            self.health = self.max_health
            self.anim = SpriteAnimator(self.sprite, self.data.textures["player"]["healthy"])
            self.damaged = False
            self.sprite.x = self.respawn_position.x
            self.sprite.y = self.respawn_position.y

            # restarts the stage music and plays a death sound
            self.data.GameAudio.PlayMusic(TrackIndex.Stage_music)

            # updates the user interface after the player dies
            self.data.UserInterface.initHealth(self.health)
            self.data.UserInterface.setLivesLeft(self.lives)

    def resetHealth(self):
        self.health = self.max_health
            
    def render(self):
        if not self.bowEquipped:
            if self.isAttacking:
                self.data.renderer.render(self.sword)
        else:
            self.data.renderer.render(self.bow)

        for arrow in self.arrows:
            self.data.renderer.render(arrow.sprite)

        if not self.damaged:
            self.data.renderer.render(self.sprite)
        else:
            self.data.renderer.shader = self.data.shaders[self.damaged_type.name]
            self.data.renderer.render(self.sprite)
            self.data.renderer.shader = None

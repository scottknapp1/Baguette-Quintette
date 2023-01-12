import pyasge
import math
import random
from abc import ABC, abstractmethod
from game.gamedata import GameData
from game.gameobjects.SpriteAnimator import SpriteAnimator
from game.gameobjects.enemyStuff.enemyTexturesEnum import EnemyTextures
from game.component import spriteIntersects, floatIntersects
from game.gameobjects.projectile import Projectile, DamageType

from game.gameobjects.enemyStuff.behaviourtree import BehaviourTreeMelee, BehaviourTreeMage, \
    BehaviourTreeTeleporter, BehaviourTreeRanger, BehaviourTreeBoss, resolve


class Enemy(ABC):

    @abstractmethod
    def __init__(self, game_data: GameData, spawn) -> None:
        self.data = game_data
        self.sprite = pyasge.Sprite()
        self.sprite.z_order = 100
        self.position = pyasge.Point2D(0, 0)

        self.health = 0
        self.speed = 0
        self.damaged = False
        self.damage_timer = 0
        self.damaged_type = None

        self.melee_attack_damage = 0
        self.attack_timer = 0

        self.route = []
        self.direction = pyasge.Point2D(0, 0)
        self.re_route_timer = 0

        self.attack_player_range = 0
        # Range is used for different things depending on type.
        # For Melee, we use it to avoid checking collisions when player is far away.
        # for Mage & Ranger, we use it to check whether the enemy should shoot.
        # For Teleporter, it does nothing.
        # For Bug / Boss it is used to determine when the enemy should behave like a Melee or a Ranger.

        self.behaviour = None
        self.anim = None
        self.running = False    # For animation.

        self.spawn_details = spawn  # So that we can retract enemies on death (re-append to self.data.spawns).

    @staticmethod
    def randomTexture(range_min, range_max) -> EnemyTextures:
        texture_num = random.randint(range_min, range_max)
        return EnemyTextures(texture_num)

    def spawn(self, x, y):
        self.sprite.x = x
        self.sprite.y = y

    def animate(self, game_time: pyasge.GameTime):
        if self.running:
            self.anim.animateSprite(game_time, 1)
        else:
            self.anim.animateSprite(game_time, 0)

    # Adjusts route so that sprite's centre is moved along route, not its origin.
    def centreRoute(self, path: list[pyasge.Point2D]) -> None:
        self.route = path

        for step in self.route:
            # Offsets each step in the route by half of our enemy sprite.
            step.x -= (self.sprite.width * self.sprite.scale) * 0.5
            step.y -= (self.sprite.height * self.sprite.scale) * 0.5

        # Need to pop current location to avoid the mage dance (enemies returning to tile middle on updating route).
        self.route.pop(0)

        self.setDirection()

    def setDirection(self):
        if len(self.route):
            if self.route[0] == self.position:
                return

        self.direction.x = self.route[0].x - self.sprite.x
        self.direction.y = self.route[0].y - self.sprite.y
        normalise = math.sqrt(self.direction.x * self.direction.x + self.direction.y * self.direction.y)
        self.direction.x /= normalise
        self.direction.y /= normalise

        self.flipSprite()

    def flipSprite(self):
        if self.direction.x < 0:
            if not self.sprite.isFlippedOnX():
                self.sprite.flip_flags = pyasge.Sprite.FlipFlags.FLIP_X

        elif self.direction.x > 0:
            if self.sprite.isFlippedOnX():
                self.sprite.flip_flags = pyasge.Sprite.FlipFlags.NORMAL

    def update(self, game_time: pyasge.GameTime):
        self.damage_timer += game_time.fixed_timestep
        self.attack_timer += game_time.fixed_timestep
        self.re_route_timer += game_time.fixed_timestep

        if self.damaged:
            self.damage_timer += game_time.fixed_timestep
            self.data.shaders[self.damaged_type.name].uniform("time").set(self.damage_timer)

            if self.damage_timer > 1:
                self.damage_timer = 0
                self.damaged = False

    def fixedUpdate(self, game_time: pyasge.GameTime):
        self.position = pyasge.Point2D(self.sprite.x, self.sprite.y)

        if len(self.route) > 1:
            if abs(self.position.distance(self.route[0])) < self.speed * 0.02:
                self.position = self.route.pop(0)
                self.setDirection()
            else:
                self.position += self.direction * self.speed * game_time.fixed_timestep

            self.sprite.x = self.position.x
            self.sprite.y = self.position.y
            self.running = True

        elif len(self.route) == 1:
            self.route.pop(0)   # Pop last step in route to avoid pathfinding on top of player / on same tile as player.

        else:
            self.running = False

    def attack(self):
        if self.attack_timer > 1:
            if self.getMidPosition().distance(self.data.player.getMidPosition()) < self.attack_player_range:
                if self.checkCollision():
                    self.route.clear()
                    self.data.player.receiveDamage(self.melee_attack_damage, DamageType.normal_damage)
                    self.attack_timer = 0

    # Collision check for the melee attack.
    def checkCollision(self) -> bool:

        # Moves the collision box in front of the sprite and gives it a size.
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

        if floatIntersects(left, top, width, height, self.data.player.sprite.x, self.data.player.sprite.y,
                           self.data.player.sprite.width, self.data.player.sprite.height):
            return True
        return False

    def receiveDamage(self, damage, damage_type: DamageType):
        self.health -= damage
        self.damaged_type = damage_type
        self.damage_timer = 0
        self.damaged = True

    def getMidPosition(self):
        return pyasge.Point2D(self.sprite.x + self.sprite.width / 2, self.sprite.y + self.sprite.height / 2)

    def render(self):
        if not self.damaged:
            self.data.renderer.render(self.sprite)
        else:
            self.data.renderer.shader = self.data.shaders[self.damaged_type.name]
            self.data.renderer.render(self.sprite)
            self.data.renderer.shader = None


class RangedEnemy(Enemy):
    @abstractmethod
    def __init__(self, game_data: GameData, spawn):
        super().__init__(game_data, spawn)

        self.projectiles = []
        self.projectile_num = -1
        self.projectile_timer = random.randint(0, 50) / 100   # Gives some variation in the intervals in enemy shooting.
        self.projectile_type = None
        self.damage_dealt_type = None

        self.ranged_attack_damage = 0
        self.max_offset_distance = 0
        # ^^^ Not all ranged enemies make use of this,
        # but it needs to exist in the base class.
        # Is used for how far from the player to generate a target.

    def fireAtPlayer(self):
        if self.projectile_timer > random.randint(10, 20) / 10:     # More variation in shooting intervals b/w enemies.
            self.projectile_timer = 0
            self.projectile_num += 1

            # Would use switch case but sad.
            # This will only run for Boss.
            # Is necessary as Boss randomises projectile type and need to map that to appropriate shader.
            if self.damage_dealt_type is None:
                if self.projectile_type == "magic":
                    self.damage_dealt_type = DamageType.magic_damage
                elif self.projectile_type == "tusk":
                    self.damage_dealt_type = DamageType.normal_damage
                elif self.projectile_type == "potion":
                    self.damage_dealt_type = DamageType.poison_damage

            self.projectiles.append(Projectile(self.damage_dealt_type,
                                               self.data.textures["projectile"][self.projectile_type],
                                               self.getMidPosition().x, self.getMidPosition().y))

            # Creates a direction for the projectile vector.
            direction = pyasge.Point2D(0, 0)
            direction.x = self.data.player.sprite.x - self.getMidPosition().x
            direction.y = self.data.player.sprite.y - self.getMidPosition().y

            normalise = math.sqrt(direction.x * direction.x + direction.y * direction.y)
            direction.x /= normalise
            direction.y /= normalise

            self.projectiles[self.projectile_num].setDirection(direction)

    def teleport(self) -> bool:
        target_location = self.generateRangedEnemyTargetOffset()

        cost = self.data.costs[target_location[1]][target_location[0]]
        teleport_point = self.data.game_map.world(target_location)

        if cost < 6 and cost != 0:  # Checks cost is not collidable & is not outside of the rooms.
            try:
                resolve(teleport_point, self.data, self)
            except:
                return False
                # If the pathfinding crashes, enemy is not in same room as player...
                # & so that target is not a viable teleport option.

            self.sprite.x = teleport_point.x - self.sprite.width / 2
            self.sprite.y = teleport_point.y - self.sprite.height / 2

            self.direction.x = self.data.player.sprite.x - self.sprite.x
            self.flipSprite()

            self.re_route_timer = 0

            return True
        return False

    def generateRangedEnemyTargetOffset(self):
        player = self.data.game_map.tile(self.data.player.getMidPosition())
        x_tile_offset = random.randint(2, self.max_offset_distance)
        y_tile_offset = random.randint(2, self.max_offset_distance)

        if random.randint(0, 1) == 1:
            x_tile_offset = -x_tile_offset

        if random.randint(0, 1) == 1:
            y_tile_offset = - y_tile_offset

        return int(player[0] + x_tile_offset), int(player[1] + y_tile_offset)

    def update(self, game_time: pyasge.GameTime):
        super().update(game_time)

        self.projectile_timer += game_time.fixed_timestep
        self.behaviour.root.tick(self, self.data, self.re_route_timer)

        for projectile in self.projectiles:
            projectile.update(game_time)

            tile = self.data.game_map.tile(pyasge.Point2D(projectile.getMidPosition().x,
                                                          projectile.getMidPosition().y))

            if self.data.costs[tile[1]][tile[0]] >= 10:     # Checks if projectile collided with an obstacle.
                self.projectiles.remove(projectile)
                self.projectile_num -= 1

            elif spriteIntersects(self.data.player.sprite, projectile.sprite):  # Check for player collision.
                self.data.player.receiveDamage(self.ranged_attack_damage, projectile.damage_type)
                self.projectiles.remove(projectile)
                self.projectile_num -= 1

    def render(self):
        super().render()

        for projectile in self.projectiles:
            projectile.render(self.data.renderer)


class Melee(Enemy):
    def __init__(self, game_data: GameData, spawn) -> None:
        super().__init__(game_data, spawn)
        self.health = 100
        self.speed = 70

        self.melee_attack_damage = 1
        self.attack_player_range = 3 * 16   # 3 Tiles

        self.behaviour = BehaviourTreeMelee()
        self.anim = SpriteAnimator(self.sprite, self.data.textures["melee"][self.randomTexture(1, 4).name])
        # ^^^ Randomly grabs a melee sprite.
        self.spawn(spawn[2], spawn[3])
        # ^^^ Must happen after setting up SpriteAnimator as size is changed within SpriteAnimator.

    def update(self, game_time: pyasge.GameTime):
        super().update(game_time)
        self.behaviour.root.tick(self, self.data, self.re_route_timer)  # does this belong in update or fixedUpdate?
        self.animate(game_time)


class Mage(RangedEnemy):
    def __init__(self, game_data: GameData, spawn) -> None:
        super().__init__(game_data, spawn)
        self.health = 100
        self.speed = 60

        self.ranged_attack_damage = 4
        self.attack_player_range = 7 * 16   # 7 Tiles
        self.damage_dealt_type = DamageType.magic_damage
        self.projectile_type = "magic"

        self.behaviour = BehaviourTreeMage()
        self.anim = SpriteAnimator(self.sprite, self.data.textures["mage"][self.randomTexture(5, 6).name])
        self.spawn(spawn[2], spawn[3])
        # ^^^ Must happen after setting up SpriteAnimator as size is changed within SpriteAnimator.

    def update(self, game_time: pyasge.GameTime):
        super().update(game_time)
        self.animate(game_time)


class Teleporter(RangedEnemy):
    def __init__(self, game_data: GameData, spawn) -> None:
        super().__init__(game_data, spawn)
        self.health = 100

        self.max_offset_distance = 8    # This offset is for teleportation.
        self.ranged_attack_damage = 6
        self.damage_dealt_type: DamageType = DamageType.poison_damage
        self.projectile_type = "potion"

        self.behaviour = BehaviourTreeTeleporter()
        self.anim = SpriteAnimator(self.sprite, self.data.textures["teleporter"]["cloaked"])
        self.spawn(spawn[2], spawn[3])
        # ^^^ Must happen after setting up SpriteAnimator as size is changed within SpriteAnimator.

    def update(self, game_time: pyasge.GameTime):
        super().update(game_time)
        self.anim.animateSprite(game_time, 0)

    def receiveDamage(self, damage, damage_type: DamageType):
        super().receiveDamage(damage, damage_type)
        self.re_route_timer = 100
        # Just forces Teleporter to teleport on receiving damage.
        # Doesn't need to be 100, just anything above range.


class Ranger(RangedEnemy):
    def __init__(self, game_data: GameData, spawn) -> None:
        super().__init__(game_data, spawn)
        self.health = 100
        self.speed = 80

        self.ranged_attack_damage = 2
        self.attack_player_range = 12 * 16   # 12 Tiles
        self.max_offset_distance = 8    # This offset is for pathfinding.
        self.damage_dealt_type: DamageType = DamageType.normal_damage
        self.projectile_type = "tusk"

        self.behaviour = BehaviourTreeRanger()
        self.anim = SpriteAnimator(self.sprite, self.data.textures["ranger"][self.randomTexture(8, 9).name])
        self.spawn(spawn[2], spawn[3])

    def update(self, game_time: pyasge.GameTime):
        super().update(game_time)
        self.animate(game_time)


class BigBoss(RangedEnemy):
    def __init__(self, game_data: GameData, spawn) -> None:
        super().__init__(game_data, spawn)
        self.behaviour = BehaviourTreeBoss()
        self.health = 250
        self.speed = 82.5
        self.melee_attack_damage = 20
        self.ranged_attack_damage = 5
        self.rapid_fire_mode = False
        self.rapid_fire_timer = 0
        self.attack_player_range = 6 * 16   # 6 Tiles
        self.max_offset_distance = 15  # This offset is for teleportation.
        self.anim = SpriteAnimator(self.sprite, self.data.textures["boss"]["bug"])
        self.spawn(spawn[2], spawn[3])
        self.isAttacking = False
        self.attackAnimationTimer = 0

    def fireAtPlayer(self):
        if self.rapid_fire_mode:
            self.projectile_timer = 100
            # Just allows projectiles to bypass fire_rate limit.
            # Doesn't need to be 100, just anything above range.

        self.projectile_type = random.choice(["magic", "tusk", "potion"])
        self.damage_dealt_type = None
        # ^^^ Forces the base fireAtPlayer() to map projectile_type to damage_type,
        # which controls which shader is used for player damage indicator.

        super().fireAtPlayer()

    def update(self, game_time: pyasge.GameTime):
        super().update(game_time)
        self.animate(game_time)

        if self.rapid_fire_mode:
            self.rapid_fire_timer += game_time.fixed_timestep
            if self.rapid_fire_timer > 3:
                self.rapid_fire_timer = 0
                self.rapid_fire_mode = False

    def fixedUpdate(self, game_time: pyasge.GameTime):
        super().fixedUpdate(game_time)
        current_tile = self.data.game_map.tile(self.getMidPosition())

        if self.data.costs[current_tile[1]][current_tile[0]] > 9 or self.data.costs[current_tile[1]][current_tile[0]] == 0:

            teleported = False
            while not teleported:
                # Has to loop to find viable teleport target.
                target_location = self.generateRangedEnemyTargetOffset()

                teleport_point = self.data.game_map.world(target_location)
                try:
                    resolve(teleport_point, self.data, self)
                except:
                    return False
                # If the pathfinding crashes, enemy is not in same room as player...
                # & so that target is not a viable teleport option.

                self.sprite.x = teleport_point.x - self.sprite.width / 2
                self.sprite.y = teleport_point.y - self.sprite.height / 2

                self.direction.x = self.data.player.sprite.x - self.sprite.x
                self.flipSprite()

                self.re_route_timer = 0
                self.route.clear()

                teleported = True

    def receiveDamage(self, damage, damage_type: DamageType):
        super().receiveDamage(damage, damage_type)

        teleported = False
        while not teleported:
            teleported = self.teleport()
            # Has to loop to find viable teleport target.

        self.route.clear()  # Forces pathfinding to re-route.

        self.rapid_fire_mode = True
        self.projectile_timer = 100
        # Above 2 lines initiate rapid fire mode.

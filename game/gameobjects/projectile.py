import pyasge
from game.gameobjects.damageType import DamageType
from game.gameobjects.SpriteAnimator import SpriteAnimator


class Projectile:

    def __init__(self, damage_type: DamageType, texture_dict, x, y):
        self.damage_type = damage_type

        self.sprite = pyasge.Sprite()
        self.anim = SpriteAnimator(self.sprite, texture_dict)
        self.sprite.z_order = 95
        self.sprite.x = x
        self.sprite.y = y
        self.speed = 150
        self.vect_x = 0
        self.vect_y = 0

    def setDirection(self, direction: pyasge.Point2D):
        self.vect_x = direction.x
        self.vect_y = direction.y

    def setDirectionFloats(self, x, y):
        self.vect_x = x
        self.vect_y = y

    def setRotation(self, target_rotation):
        self.sprite.rotation = target_rotation

    def getMidPosition(self):
        return pyasge.Point2D(self.sprite.x + self.sprite.width / 2, self.sprite.y + self.sprite.height / 2)

    def update(self, game_time: pyasge.GameTime):
        self.anim.animateSprite(game_time, 0)

        self.sprite.x += self.vect_x * self.speed * game_time.fixed_timestep
        self.sprite.y += self.vect_y * self.speed * game_time.fixed_timestep

    def render(self, renderer):
        renderer.render(self.sprite)

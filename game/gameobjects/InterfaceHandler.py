import pyasge
from game.gamedata import GameData
from game.gamestates.gamestate import GameStateID
from game.gameobjects.weaponTypes import GunTypes


class UIHandler:

    def __init__(self, game_data: GameData):
        self.data = game_data
        self.time_elapsed = 0
        self.opacity_timer = 0
        self.target = None
        self.scale_multiplier = 1
        self.speed = 20
        self.charge_value_1percent = 0
        self.transition_feedback = False
        self.transitioning = False
        self.render_dialogue_box = False
        self.on_stairs = False
        self.n_hearts = None
        self.summon_baguette_textbox = False

        # UI elements
        self.hearts_UI = []
        self.black_bars = []
        self.baguette_UI = []
        self.player_lives_UI = pyasge.Text
        self.enemies_UI_text = pyasge.Text
        self.enemies_UI_sprite = pyasge.Sprite()
        self.cooldown_UI = pyasge.Sprite()
        self.cooldown_charge = pyasge.Sprite()
        self.gun_UI = pyasge.Sprite()
        self.dialogue_box = pyasge.Sprite()
        self.player_icon_UI = pyasge.Sprite()
        self.baguette_textbox = pyasge.Sprite()
        self.background_shader = pyasge.Sprite()

        self.gun_UI.loadTexture("data/map/TileSheet.png")

        self.init()
        self.initBaguette(0)
        self.initBaguetteTextbox()
        self.initWeaponSprite(GunTypes.BOW)

    def init(self):

        # Initializes two black bars for the transition effect
        for i in range(0, 2):
            self.black_bars.append(pyasge.Sprite())
            self.black_bars[i].loadTexture("data/textures/black_bar.png")
            self.black_bars[i].z_order = 127

            if i == 1:
                # spawns a bar on top outside the screen boundaries
                self.black_bars[i].y = -self.black_bars[i].height
            else:
                # spawns a bar below the screen boundaries
                self.black_bars[i].y = self.data.game_res[1]

        # Number of enemies left
        self.enemies_UI_text = pyasge.Text(self.data.fonts["UI"])
        self.enemies_UI_text.string = "0"
        self.enemies_UI_text.scale = 4
        self.enemies_UI_text.position = [self.data.game_res[0] * 0.1, self.data.game_res[1] * 0.94]
        self.enemies_UI_text.colour = pyasge.COLOURS.WHITE

        # sprite for the enemies left
        self.enemies_UI_sprite.loadTexture("data/textures/Enemies_counter.png")
        self.enemies_UI_sprite.z_order = 126
        self.enemies_UI_sprite.scale = 4
        self.enemies_UI_sprite.x = self.data.game_res[0] * 0.03
        self.enemies_UI_sprite.y = self.data.game_res[1] * 0.85

        # Dialogue box
        self.dialogue_box.loadTexture("data/textures/dialogue_placeholder_travel.png")
        self.dialogue_box.z_order = 126
        self.dialogue_box.opacity = 0.8
        self.dialogue_box.x = self.data.game_res[0] / 2 - self.dialogue_box.width / 2
        self.dialogue_box.y = self.data.game_res[1] / 2 - self.dialogue_box.height / 2 - self.data.game_res[1] / 12

        # number of player lives left
        self.player_lives_UI = pyasge.Text(self.data.fonts["UI"])
        self.player_lives_UI.string = "0"
        self.player_lives_UI.scale = 2.8
        self.player_lives_UI.position = [self.data.game_res[0] * 0.055, self.data.game_res[1] * 0.225]
        self.player_lives_UI.colour = pyasge.COLOURS.WHITE

        # Player icon, reference to display lives
        self.player_icon_UI.loadTexture("data/knight/knight_idle_anim_f0.png")
        self.player_icon_UI.z_order = 126
        self.player_icon_UI.scale = 4.5
        self.player_icon_UI.x = self.data.game_res[0] * 0.02
        self.player_icon_UI.y = self.data.game_res[1] * 0.17

        # Background shader
        self.background_shader.width = self.data.game_res[0]
        self.background_shader.height = self.data.game_res[1]
        self.background_shader.z_order = -120
        self.background_shader.colour = pyasge.COLOURS.BLACK

    def initHealth(self, player_health_total):
        # updates the player health when given
        player_health = int(player_health_total / 10)
        self.n_hearts = (player_health * 2)
        self.hearts_UI.clear()

        # creates the row of hearts in the user interface
        for i in range(0, player_health):
            self.hearts_UI.append(pyasge.Sprite())
            self.hearts_UI[i].loadTexture("data/map/TileSheet.png")
            self.hearts_UI[i].src_rect = [289, 258, 13, 12]
            self.hearts_UI[i].scale = 0.1
            self.hearts_UI[i].z_order = 126
            self.hearts_UI[i].x = (self.data.game_res[0] * 0.03) + (
                    self.hearts_UI[i].width * self.hearts_UI[i].scale) * i * 1.1
            self.hearts_UI[i].y = self.data.game_res[1] * 0.04

    def updateHealth(self, health):
        # handles decrease of life in the health bar
        new_n_hearts = int(health / 5)

        # if the number of hearth we currently display is more than the number of hearth of the current life it pops one
        # Also, the life is divided in 20 points with 10 hearts, if the point is not even the hearth won't be popped
        # but displayed half.
        if self.n_hearts > new_n_hearts:
            if self.n_hearts % 2 and not len(self.hearts_UI) == 1:
                self.hearts_UI.pop()
                self.n_hearts -= 1
            else:
                self.hearts_UI[len(self.hearts_UI) - 1].src_rect = [305, 258, 13, 12]
                self.n_hearts -= 1

    def initBaguette(self, baguettes):
        self.baguette_UI.clear()
        # creates the row of baguettes
        for i in range(0, 5):
            self.baguette_UI.append(pyasge.Sprite())
            # This baguette was made by a friend of mine, give 0.000001% of the grade to him
            self.baguette_UI[i].loadTexture("data/textures/baguette_pixelart.png")
            self.baguette_UI[i].z_order = 126
            self.baguette_UI[i].scale = 0.035
            self.baguette_UI[i].x = (self.data.game_res[0] * 0.03) + (
                    self.baguette_UI[i].width * self.baguette_UI[i].scale) * i * 0.9
            self.baguette_UI[i].y = self.data.game_res[1] * 0.10

        # turns black the baguettes that the player do not have
        for i in range(4, baguettes - 1, -1):
            self.baguette_UI[i].colour = pyasge.COLOURS.GREYBLACK

    def initWeaponSprite(self, gun):
        # depending on the enum loads the current gun that gets passed
        if gun == GunTypes.BOW:
            self.gun_UI.src_rect = [333, 25, 22, 23]
        elif gun == GunTypes.SWORD:
            self.gun_UI.src_rect = [319, 179, 20, 27]

        # moves the positioning point of the sprite from top left to bottom right
        self.gun_UI.z_order = 126
        self.gun_UI.scale = 0.5
        self.gun_UI.x = (self.data.game_res[0] * 0.97) - self.gun_UI.width * self.gun_UI.scale
        self.gun_UI.y = (self.data.game_res[1] * 0.91) - self.gun_UI.height * self.gun_UI.scale

        # Cooldown bar (gun related)
        # Automatically places the cooldown bar under the gun in use
        self.cooldown_UI.loadTexture("data/textures/charge_bar.png")
        self.cooldown_UI.z_order = 125
        self.cooldown_UI.x = self.gun_UI.x
        self.cooldown_UI.y = self.gun_UI.y + self.gun_UI.height * self.gun_UI.scale
        self.cooldown_UI.width = self.gun_UI.width * self.gun_UI.scale

        # initializes the sprite that will fill up the charge
        self.cooldown_charge.colour = pyasge.COLOURS.GREEN
        self.cooldown_charge.z_order = 126
        self.cooldown_charge.x = self.cooldown_UI.x + self.cooldown_UI.width / 32
        self.cooldown_charge.y = self.cooldown_UI.y + self.cooldown_UI.height / 4
        self.charge_value_1percent = (self.cooldown_UI.width * 0.945) / 100
        self.cooldown_charge.width = 0
        self.cooldown_charge.height = self.cooldown_UI.height / 2

    def initBaguetteTextbox(self):
        # Inits the text on screen that pops out when gathering a baguette
        self.baguette_textbox.loadTexture("data/Logo/baguette_obtained.png")
        self.baguette_textbox.z_order = 126
        self.baguette_textbox.scale = 0.3
        self.baguette_textbox.x = (self.data.game_res[0] / 2) - (
                    self.baguette_textbox.width * self.baguette_textbox.scale) / 2
        self.baguette_textbox.y = (self.data.game_res[1] / 2) - (
                    self.baguette_textbox.height * self.baguette_textbox.scale) / 2
        self.baguette_textbox.opacity = 0

    def showBaguetteTextbox(self):
        # is true when baguette is supposed to show on screen
        self.summon_baguette_textbox = True

    # Simply updates the on-screen number of active enemies
    def setEnemiesNumber(self, enemies):
        self.enemies_UI_text.string = str(enemies)

    # same thing as the one above but with lives
    def setLivesLeft(self, lives):
        self.player_lives_UI.string = str(lives)

    # accepts a value from 0 to 100 which will be the charge level of the cooldown bar
    def setCharge(self, charge):
        self.cooldown_charge.width = self.charge_value_1percent * charge

    def renderDialogueBox(self, travel_possible):
        # changes the texture if you can use the teleporters or not
        if travel_possible:
            if self.data.gamepad.connected:
                self.dialogue_box.loadTexture("data/textures/dialogue_placeholder_travel_gamepad.png")
            else:
                self.dialogue_box.loadTexture("data/textures/dialogue_placeholder_travel.png")
        else:
            self.dialogue_box.loadTexture("data/textures/dialogue_placeholder_noentry.png")

        self.render_dialogue_box = True
        pass

    def transitionAnim(self):
        # when called, the animation for the black bars to come down for a transition will play
        # The animation will play regardless of the transition happening or not if not coded correctly
        if not self.transitioning:
            self.target = [0, self.data.game_res[1] - self.black_bars[0].height]
            self.time_elapsed = 0
            self.transitioning = True

    def transitionFeedback(self) -> bool:
        # returns true when the transition is at its midpoint (when screen is completely black)
        return self.transition_feedback

    def updateUI(self, game_time: pyasge.GameTime):
        # the dialogue box is always rendered but its opacity always 0, when standing on a teleported it will
        # appear back on screen
        if self.render_dialogue_box and self.dialogue_box.opacity <= 0.9:
            self.dialogue_box.opacity += game_time.fixed_timestep * 7
        elif not self.render_dialogue_box and self.dialogue_box.opacity >= 0:
            self.dialogue_box.opacity -= game_time.fixed_timestep * 7
        self.render_dialogue_box = False

        if len(self.hearts_UI) > 0:
            # handles the animation for the health bar
            if 0.08 > self.hearts_UI[len(self.hearts_UI) - 1].scale:
                self.scale_multiplier = 1
            elif self.hearts_UI[len(self.hearts_UI) - 1].scale > 0.12:
                self.scale_multiplier = -1

            self.hearts_UI[len(self.hearts_UI) - 1].scale += self.scale_multiplier * game_time.fixed_timestep / 20

        if self.transitioning:

            self.time_elapsed += game_time.fixed_timestep

            # reached the midpoint retracts the black bars and outputs a true (if called)
            if 0.5 < self.time_elapsed < 0.52:
                self.target = [-self.black_bars[0].height - 200, self.data.game_res[1] + 200]
                self.transition_feedback = True
            else:
                self.transition_feedback = False

            # Stops the transition from happening
            if self.time_elapsed > 1.2:
                self.transitioning = False

            # Moves the bars up and down progressively
            self.black_bars[1].y += (self.target[0] - self.black_bars[1].y) / self.speed
            self.black_bars[0].y += (self.target[1] - self.black_bars[0].y) / self.speed

        if self.summon_baguette_textbox:
            self.opacity_timer += game_time.fixed_timestep

            # Summons the mighty baguette indicator! (baguette obtained)
            if self.opacity_timer <= 0.2 and self.baguette_textbox.opacity < 0.9:
                self.baguette_textbox.opacity += game_time.fixed_timestep * 10
            elif self.opacity_timer >= 0.8 and self.baguette_textbox.opacity >= 0:
                self.baguette_textbox.opacity -= game_time.fixed_timestep * 10
            elif self.opacity_timer > 1:
                self.opacity_timer = 0
                self.summon_baguette_textbox = False

    def renderUI(self, state):
        # gets rendered everywhere for the transition animation
        # other elements placed here will also render everywhere in the game as a UI element
        for black_bar in self.black_bars:
            self.data.renderer.render(black_bar)

        if state == GameStateID.GAMEPLAY:
            self.data.renderer.render(self.enemies_UI_text)
            self.data.renderer.render(self.player_lives_UI)
            self.data.renderer.render(self.enemies_UI_sprite)
            self.data.renderer.render(self.cooldown_UI)
            self.data.renderer.render(self.cooldown_charge)
            self.data.renderer.render(self.gun_UI)
            self.data.renderer.render(self.dialogue_box)
            self.data.renderer.render(self.player_icon_UI)
            self.data.renderer.render(self.baguette_textbox)

            for heart in self.hearts_UI:
                self.data.renderer.render(heart)

            for baguette in self.baguette_UI:
                self.data.renderer.render(baguette)

            self.data.renderer.shader = self.data.shaders["background_void"]
            self.data.renderer.render(self.background_shader)
            self.data.renderer.shader = None

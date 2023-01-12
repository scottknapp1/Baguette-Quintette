import pyasge

from game.gamestates.gamestate import GameState
from game.gamestates.gamestate import GameStateID
from game.gamedata import GameData
from game.gameobjects.SoundHandler import TrackIndex


class GameMenu(GameState):

    def __init__(self, gamedata: GameData) -> None:
        super().__init__(gamedata)
        self.data.renderer.setClearColour(pyasge.COLOURS.WHITE)
        self.id = GameStateID.START_MENU
        self.background = pyasge.Sprite()
        self.game_logo = pyasge.Sprite()
        self.cursorette = pyasge.Sprite()   # cursor + baguette = cersorette
        self.scrolling_background_part1 = pyasge.Sprite()
        self.scrolling_background_part2 = pyasge.Sprite()

        self.transition = False
        self.scrolling = False
        self.play_option = None
        self.exit_option = None
        self.menu_text = None
        self.opacity = 1.0
        self.menu_option = 0
        self.time_elapsed = 0
        self.animation_distance_exit = -1600
        self.animation_distance_play = 2680
        self.scrolling_speed = 150

        self.data.GameAudio.PlayMusic(TrackIndex.Title_music)
        self.init()

    def init(self):

        # loads the intial background before the scrolling
        self.background.loadTexture("data/background/scrolling_start_screen.jpg")
        self.background.setMagFilter(pyasge.MagFilter.LINEAR)
        # automatically scales the menu image to fit the screen, image has to be in 16:9
        self.background.scale = self.data.game_res[0] / self.background.width
        self.background.z_order = -99

        # initialises scrolling bg 1
        self.scrolling_background_part1.loadTexture("data/background/scrolling_start_2.jpg")
        self.scrolling_background_part1.setMagFilter(pyasge.MagFilter.LINEAR)
        self.scrolling_background_part1.scale = self.data.game_res[0] / self.background.width
        self.scrolling_background_part1.z_order = -100

        # initialises scrolling bg 2
        self.scrolling_background_part2.loadTexture("data/background/scrolling_start_2.jpg")
        self.scrolling_background_part2.setMagFilter(pyasge.MagFilter.LINEAR)
        self.scrolling_background_part2.scale = self.data.game_res[0] / self.background.width
        self.scrolling_background_part2.z_order = -100
        self.scrolling_background_part2.flip_flags = pyasge.Sprite.FlipFlags.FLIP_X
        self.scrolling_background_part2.x -= self.data.game_res[0]

        # loads the game logo
        self.game_logo.loadTexture("data/Logo/Menu_logo_new.png")
        self.game_logo.setMagFilter(pyasge.MagFilter.LINEAR)
        self.game_logo.scale = 0.7
        self.game_logo.x = (self.data.game_res[0] / 2) - (self.game_logo.width / 2 * 0.7)
        self.game_logo.y = -1500
        self.game_logo.z_order = 100

        # loads the baguette indicator
        self.cursorette.loadTexture("data/textures/baguette_indicator.png")
        self.cursorette.setMagFilter(pyasge.MagFilter.LINEAR)
        self.cursorette.scale = 0.1
        self.cursorette.z_order = 99
        self.cursorette.x = -1000
        self.cursorette.y = -1000

        self.exit_option = pyasge.Text(self.data.fonts["game"])
        self.exit_option.string = "MAYBE ANOTHER DAY..."
        self.exit_option.scale = 3
        self.exit_option.position = [0, 1000]
        self.exit_option.colour = pyasge.COLOURS.WHITE

        self.play_option = pyasge.Text(self.data.fonts["game"])
        self.play_option.string = "GET THOSE BAGUETTES BACK!"
        self.play_option.scale = 3
        self.play_option.position = [0, 900]
        self.play_option.colour = pyasge.COLOURS.CRIMSON

    def click_handler(self, event: pyasge.ClickEvent) -> None:
        pass

    def update_inputs(self):
        if self.data.gamepad.connected:
            if self.menu_option == 0 and self.data.inputs.getGamePad().AXIS_LEFT_Y > 0.1 or self.menu_option == 1 and \
                    self.data.inputs.getGamePad().AXIS_LEFT_Y < -0.1:
                self.change_menu_option()

            if self.data.gamepad.A and not self.transition:
                self.select_menu_option()

    def key_handler(self, event: pyasge.KeyEvent) -> None:
        # menu options for main menu
        if event.action == pyasge.KEYS.KEY_PRESSED:
            if event.key == pyasge.KEYS.KEY_UP or event.key == pyasge.KEYS.KEY_DOWN:
                self.change_menu_option()

            if event.key == pyasge.KEYS.KEY_ENTER:  # options for main menu
                self.select_menu_option()

    def change_menu_option(self):
        # plays a jingle when switching the options in the menu
        self.data.GameAudio.PlayEffect(TrackIndex.Menu_jingle)

        self.menu_option = 1 - self.menu_option

        if self.menu_option == 0:
            self.play_option.colour = pyasge.COLOURS.CRIMSON
            self.exit_option.colour = pyasge.COLOURS.WHITE

        elif self.menu_option == 1:
            self.play_option.colour = pyasge.COLOURS.WHITE
            self.exit_option.colour = pyasge.COLOURS.CRIMSON

    def select_menu_option(self):
        if self.menu_option == 0:
            self.data.GameAudio.PlayEffect(TrackIndex.Transition)
            self.data.UserInterface.transitionAnim()
            self.transition = True
        else:
            exit()

    def move_handler(self, event: pyasge.MoveEvent) -> None:
        pass

    def fixed_update(self, game_time: pyasge.GameTime) -> None:
        pass

    def update(self, game_time: pyasge.GameTime) -> GameStateID:
        self.update_inputs()

        # slowly spawns the logo on screen
        if not self.game_logo.y == -50:
            self.game_logo.y += (-50 - self.game_logo.y) / 80

        # slowly spawns play option
        if not self.animation_distance_exit == (self.data.game_res[0] / 2 - self.exit_option.width / 2):
            self.animation_distance_exit += ((self.data.game_res[0] / 2 - self.exit_option.width / 2) -
                                             self.animation_distance_exit) / 80
            self.exit_option.position = [self.animation_distance_exit, 1000]

            if self.menu_option == 0:
                self.cursorette.x = self.animation_distance_play - (self.cursorette.width * 0.1)
                self.cursorette.y = 850

        # slowly spawns quit option
        if not self.animation_distance_play == (self.data.game_res[0] / 2 - self.play_option.width / 2):
            self.animation_distance_play += ((self.data.game_res[0] / 2 - self.play_option.width / 2) -
                                             self.animation_distance_play) / 80
            self.play_option.position = [self.animation_distance_play, 900]

            if self.menu_option == 1:
                self.cursorette.x = self.animation_distance_exit - (self.cursorette.width * 0.1)
                self.cursorette.y = 950

        # moves the background sprites if scrolling is on
        if self.scrolling:
            # scrolls the sprites to the screen
            self.scrolling_background_part1.x += game_time.fixed_timestep * self.scrolling_speed
            self.scrolling_background_part2.x += game_time.fixed_timestep * self.scrolling_speed

            # moves the backgrounds back to continue an endless scrolling
            if self.scrolling_background_part1.x >= self.data.game_res[0]:
                self.scrolling_background_part1.x = \
                    self.scrolling_background_part2.x - self.scrolling_background_part2.width

            if self.scrolling_background_part2.x >= self.data.game_res[0]:
                self.scrolling_background_part2.x = \
                    self.scrolling_background_part1.x - self.scrolling_background_part1.width
        else:
            self.time_elapsed += game_time.fixed_timestep

        # fades the opacity at a certain point in time
        if 10.5 <= self.time_elapsed < 11.5:
            self.opacity -= game_time.fixed_timestep
        elif 11.5 <= self.time_elapsed < 12.5:
            self.opacity += game_time.fixed_timestep

        # turns on scrolling when time elapsed is over 11.5
        if self.time_elapsed >= 11.5 and not self.scrolling:
            self.scrolling = True

        if self.transition and self.data.UserInterface.transitionFeedback():
            # plays the main music one the game starts
            self.data.GameAudio.PlayMusic(TrackIndex.Stage_music)
            return GameStateID.GAMEPLAY

        return GameStateID.START_MENU

    def render(self, game_time: pyasge.GameTime) -> None:

        self.data.renderer.render(self.game_logo)
        self.data.renderer.render(self.cursorette)
        self.data.renderer.render(self.play_option)
        self.data.renderer.render(self.exit_option)

        self.data.shaders["opacity"].uniform("rgba").set([1.0, 1.0, 1.0, self.opacity])
        self.data.renderer.shader = self.data.shaders["opacity"]

        if self.scrolling:
            self.data.renderer.render(self.scrolling_background_part2)
            self.data.renderer.render(self.scrolling_background_part1)
        else:
            self.data.renderer.render(self.background)

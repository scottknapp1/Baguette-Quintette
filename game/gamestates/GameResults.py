import pyasge

from game.gamestates.gamestate import GameState, GameStateID
from game.restart import restart
from game.gamedata import GameData
from game.gameobjects.SoundHandler import TrackIndex


class GameResults(GameState):

    def __init__(self, data: GameData) -> None:
        super().__init__(data)
        vp = self.data.renderer.resolution_info.viewport
        self.data.renderer.setProjectionMatrix(0, 0, vp.w, vp.h)
        self.id = None

        #  Game over screen
        self.background = pyasge.Sprite()
        self.baguette_logo = pyasge.Sprite()
        self.cursorette = pyasge.Sprite()

        self.animation_distance_exit = 2680
        self.animation_distance_replay = 2680
        self.offset = 100
        self.logo_y = -100

        self.menu_option = 0
        self.option_exit = None
        self.game_replay = None
        self.transition = False

        self.init()

    def init(self):

        # initialization of text
        self.game_replay = pyasge.Text(self.data.fonts["game"])
        self.game_replay.string = "FRASE BELLA IN ITALIANO"
        self.game_replay.scale = 3
        self.game_replay.position = [-1000, 900]
        self.game_replay.colour = pyasge.COLOURS.CRIMSON

        self.option_exit = pyasge.Text(self.data.fonts["game"])
        self.option_exit.string = "FRASE BELLA IN ITALIANO"
        self.option_exit.scale = 3
        self.option_exit.position = [-1000, 1000]
        self.option_exit.colour = pyasge.COLOURS.WHITE

        # loads the baguette indicator
        self.cursorette.loadTexture("data/textures/baguette_indicator.png")
        self.cursorette.setMagFilter(pyasge.MagFilter.LINEAR)
        self.cursorette.scale = 0.1
        self.cursorette.z_order = 99
        self.cursorette.x = -1000
        self.cursorette.y = -1000

    def click_handler(self, event: pyasge.ClickEvent) -> None:
        pass

    def update_inputs(self):
        if self.data.gamepad.connected:
            if self.menu_option == 0 and self.data.inputs.getGamePad().AXIS_LEFT_Y > 0.1 or \
                    self.menu_option == 1 and self.data.inputs.getGamePad().AXIS_LEFT_Y < -0.1:
                self.change_menu_option()

            if self.data.gamepad.A and not self.transition:
                self.select_menu_option()

    def key_handler(self, event: pyasge.KeyEvent) -> None:

        if event.action == pyasge.KEYS.KEY_PRESSED:
            if event.key == pyasge.KEYS.KEY_UP or event.key == pyasge.KEYS.KEY_DOWN:
                self.change_menu_option()

            elif event.key == pyasge.KEYS.KEY_ENTER:  # options for game over
                self.select_menu_option()

    def change_menu_option(self):
        self.data.GameAudio.PlayEffect(TrackIndex.Menu_jingle)
        self.menu_option = 1 - self.menu_option

        if self.menu_option == 0:
            self.game_replay.colour = pyasge.COLOURS.CRIMSON
            self.option_exit.colour = pyasge.COLOURS.WHITE

        elif self.menu_option == 1:
            self.game_replay.colour = pyasge.COLOURS.WHITE
            self.option_exit.colour = pyasge.COLOURS.CRIMSON

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

        # scrolls through the lost game screen and slows at the end
        if not self.background.x <= (-self.background.width + self.data.game_res[0]):
            self.background.x += ((-self.background.width + self.data.game_res[
                0] - self.offset) - self.background.x) / 200

        # slowly spawns UI elements when scrolling background is close to the end
        if self.background.x <= (-self.background.width + (self.data.game_res[0] * 1.5)):
            # slowly spawns the logo on screen
            if not self.baguette_logo.y <= self.logo_y:
                self.baguette_logo.y += (self.logo_y - self.baguette_logo.y) / 80

            # slowly spawns replay option
            if not self.animation_distance_exit <= (self.data.game_res[0] / 2 - self.option_exit.width / 2):
                self.animation_distance_exit += ((self.data.game_res[0] / 2 - self.option_exit.width / 2) -
                                                 self.animation_distance_exit) / 80
                self.option_exit.position = [self.animation_distance_exit, 1000]

                if self.menu_option == 1:
                    self.cursorette.x = self.animation_distance_exit - (self.cursorette.width * 0.1)
                    self.cursorette.y = 950

            # slowly spawns quit option
            if not self.animation_distance_replay <= (self.data.game_res[0] / 2 - self.game_replay.width / 2):
                self.animation_distance_replay += ((self.data.game_res[0] / 2 - self.game_replay.width / 2) -
                                                   self.animation_distance_replay) / 80
                self.game_replay.position = [self.animation_distance_replay, 900]

                if self.menu_option == 0:
                    self.cursorette.x = self.animation_distance_replay - (self.cursorette.width * 0.1)
                    self.cursorette.y = 850

        if self.transition and self.data.UserInterface.transitionFeedback():
            self.data.GameAudio.PlayMusic(TrackIndex.Title_music)
            restart(self.data)
            return GameStateID.START_MENU

        return self.id

    def render(self, game_time: pyasge.GameTime) -> None:
        # render the game over menu here
        self.data.renderer.render(self.background)
        self.data.renderer.render(self.game_replay)
        self.data.renderer.render(self.option_exit)
        self.data.renderer.render(self.baguette_logo)
        self.data.renderer.render(self.cursorette)

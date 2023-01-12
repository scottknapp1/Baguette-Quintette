import random
import json

import pyasge

from game.gamedata import GameData
from game.gameobjects.InterfaceHandler import UIHandler
from game.gameobjects.gamemap import GameMap
from game.gamestates.Gamemenu import GameMenu
from game.gamestates.gameover import GameOver
from game.gamestates.gameplay import GamePlay
from game.gamestates.gamestate import GameStateID
from game.gamestates.gamewon import GameWon
from game.gameobjects.SoundHandler import SoundHandler


class MyASGEGame(pyasge.ASGEGame):
    """The ASGE Game in Python."""

    def __init__(self, settings: pyasge.GameSettings):
        """
        The constructor for the game.

        The constructor is responsible for initialising all the needed
        subsystems,during the game's running duration. It directly
        inherits from pyasge.ASGEGame which provides the window
        management and standard game loop.

        :param settings: The game settings
        """
        pyasge.ASGEGame.__init__(self, settings)
        self.data = GameData()
        self.renderer.setBaseResolution(self.data.game_res[0], self.data.game_res[1], pyasge.ResolutionPolicy.MAINTAIN)
        random.seed(a=None, version=2)

        self.data.game_map = GameMap(self.renderer, "data/map/DungeonMap.tmx", self.data)
        self.data.inputs = self.inputs
        self.data.renderer = self.renderer

        # loads shader
        self.data.shaders["normal_damage"] = self.data.renderer.loadPixelShader("/data/shaders/damage.frag")
        self.data.shaders["normal_damage"].uniform("rgb").set([1.38, 0.03, 0.03])
        self.data.shaders["normal_damage"].uniform("differences").set([-0.38, 0.97, 0.97])

        self.data.shaders["magic_damage"] = self.data.renderer.loadPixelShader("/data/shaders/damage.frag")
        self.data.shaders["magic_damage"].uniform("rgb").set([0.35, 0, 0.38])
        self.data.shaders["magic_damage"].uniform("differences").set([0.65, 1, 0.62])

        self.data.shaders["poison_damage"] = self.data.renderer.loadPixelShader("/data/shaders/damage.frag")
        self.data.shaders["poison_damage"].uniform("rgb").set([0.26, 0.64, 0.09])
        self.data.shaders["poison_damage"].uniform("differences").set([0.74, 0.36, 0.91])

        self.data.shaders["opacity"] = self.data.renderer.loadPixelShader("/data/shaders/opacity_shader.frag")
        self.data.shaders["background_void"] = self.data.renderer.loadPixelShader("data/shaders/background.frag")
        self.data.prev_gamepad = self.data.gamepad = self.inputs.getGamePad()
        self.data.sprite_sheet = "data/map/TileSheet.png"
        with open("game/gameobjects/textures.json", mode="r", encoding="utf8") as Textures:

            self.data.textures = json.loads(Textures.read())

        # setup the background and load the fonts for the game
        self.init_audio()
        self.init_cursor()
        self.init_fonts()

        # register the key and mouse click handlers for this class
        self.key_id = self.data.inputs.addCallback(pyasge.EventType.E_KEY, self.key_handler)
        self.mouse_id = self.data.inputs.addCallback(pyasge.EventType.E_MOUSE_CLICK, self.click_handler)
        self.mousemove_id = self.data.inputs.addCallback(pyasge.EventType.E_MOUSE_MOVE, self.move_handler)

        # start the game in the menu
        self.current_state = GameMenu(self.data)
        # self.current_state = GameWon(self.data)

        # Initializes the interface handler
        self.data.UserInterface = UIHandler(self.data)

    def init_cursor(self):
        """Initialises the mouse cursor and hides the OS cursor."""
        self.data.cursor = pyasge.Sprite()
        self.data.cursor.loadTexture("/data/textures/cursors.png")
        self.data.cursor.width = 11
        self.data.cursor.height = 11
        self.data.cursor.src_rect = [0, 0, 11, 11]
        self.data.cursor.scale = 1
        self.data.cursor.setMagFilter(pyasge.MagFilter.NEAREST)
        self.data.cursor.z_order = 126
        self.data.inputs.setCursorMode(pyasge.CursorMode.HIDDEN)

        # CURSORETTE
        # Having a baguette as a cursor is cute but not practical
        #self.data.cursor = pyasge.Sprite()
        #self.data.cursor.loadTexture("data/textures/cursor.png")
        #self.data.cursor.scale = 0.007
        #self.data.cursor.setMagFilter(pyasge.MagFilter.LINEAR)
        #self.data.cursor.z_order = 126
        #self.data.inputs.setCursorMode(pyasge.CursorMode.HIDDEN)

    def init_audio(self) -> None:
        """Plays the background audio."""
        self.data.GameAudio = SoundHandler(self.data)

    def init_fonts(self) -> None:
        """Loads the game fonts."""
        self.data.fonts['game'] = self.renderer.loadFont('data/Font/DWARVESC.TTF', 28, 4)
        self.data.fonts['UI'] = self.renderer.loadFont('data/Font/Born2bSportyV2.ttf', 28, 4)

    def move_handler(self, event: pyasge.MoveEvent) -> None:
        """Handles the mouse movement and delegates to the active state."""
        self.data.cursor.x = event.x
        self.data.cursor.y = event.y
        self.current_state.move_handler(event)

    def click_handler(self, event: pyasge.ClickEvent) -> None:
        """Forwards click events on to the active state."""
        self.current_state.click_handler(event)

    def key_handler(self, event: pyasge.KeyEvent) -> None:
        """Forwards Key events on to the active state."""
        self.current_state.key_handler(event)
        if event.key == pyasge.KEYS.KEY_ESCAPE:
            self.signalExit()

    def fixed_update(self, game_time: pyasge.GameTime) -> None:
        """Processes fixed updates."""
        self.current_state.fixed_update(game_time)

        if self.data.gamepad.connected and self.data.gamepad.START:
            self.signalExit()

    def update(self, game_time: pyasge.GameTime) -> None:
        self.data.gamepad = self.inputs.getGamePad()
        self.data.prev_gamepad = self.data.gamepad

        # updates the UI handler constantly
        self.data.UserInterface.updateUI(game_time)

        # delegate the update logic to the active state
        new_state = self.current_state.update(game_time)
        if self.current_state.id != new_state:
            if new_state is GameStateID.START_MENU:
                self.current_state = GameMenu(self.data)
            elif new_state is GameStateID.GAMEPLAY:
                self.current_state = GamePlay(self.data)
            elif new_state is GameStateID.GAME_OVER:
                self.current_state = GameOver(self.data)
            elif new_state is GameStateID.WINNER_WINNER:
                self.current_state = GameWon(self.data)

    def render(self, game_time: pyasge.GameTime) -> None:
        """Renders the game state and mouse cursor"""
        # renders the render panel in the current active game state
        self.current_state.render(game_time)
        self.renderer.render(self.data.cursor)

        # renders the User Interface
        # set a new view that covers the width and height of game
        camera_view = pyasge.CameraView(self.data.renderer.resolution_info.view)
        vp = self.data.renderer.resolution_info.viewport
        self.data.renderer.setProjectionMatrix(0, 0, vp.w, vp.h)
        # passes the current game state to render the interface for the game state
        self.data.UserInterface.renderUI(self.current_state.id)
        # this restores the original camera view
        self.data.renderer.setProjectionMatrix(camera_view)

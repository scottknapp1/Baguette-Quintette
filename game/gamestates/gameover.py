import pyasge

from game.gamestates.gamestate import GameStateID
from game.gamestates.GameResults import GameResults
from game.gamedata import GameData
from game.gameobjects.SoundHandler import TrackIndex

class GameOver(GameResults):

    def __init__(self, data: GameData) -> None:
        super().__init__(data)
        self.id = GameStateID.GAME_OVER
        self.logo_y = -40

        # big long image for da loss
        self.background.loadTexture("data/background/background_lost.png")
        self.background.scale = self.data.game_res[1] / self.background.height
        self.background.x = self.data.game_res[0] * 0.2
        self.background.z_order = -100

        # logo initialize
        self.baguette_logo.loadTexture("data/Logo/logo_lost.png")
        self.baguette_logo.setMagFilter(pyasge.MagFilter.LINEAR)
        self.baguette_logo.scale = 0.6
        self.baguette_logo.x = self.data.game_res[0] * 0.03
        # starting Y of the logo
        self.baguette_logo.y = 1200
        self.baguette_logo.z_order = 100

        # changes the text in the end screen
        self.game_replay.string = "I WILL NEVER GIVE UP!"
        self.option_exit.string = "I AM NOT WORTHY..."

        # for the game over music
        self.data.GameAudio.PlayMusic(TrackIndex.lost_music)

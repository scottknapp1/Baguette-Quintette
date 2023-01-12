import pyasge

from game.gamestates.gamestate import GameStateID
from game.gamestates.GameResults import GameResults
from game.gamedata import GameData
from game.gameobjects.SoundHandler import TrackIndex


class GameWon(GameResults):

    def __init__(self, data: GameData) -> None:
        super().__init__(data)
        self.id = GameStateID.WINNER_WINNER
        self.logo_y = -20

        # big long image for da win
        self.background.loadTexture("data/background/background_win.png")
        self.background.scale = self.data.game_res[1] / self.background.height
        self.background.x = self.data.game_res[0] * 0.2
        self.background.z_order = -100

        # logo initialize
        self.baguette_logo.loadTexture("data/Logo/logo_win.png")
        self.baguette_logo.setMagFilter(pyasge.MagFilter.LINEAR)
        self.baguette_logo.scale = 0.6
        self.baguette_logo.x = 0
        # starting Y of the logo
        self.baguette_logo.y = 1200
        self.baguette_logo.z_order = 100

        # changes the text in the end screen
        self.game_replay.string = "HELP ANOTHER VILLAGE!"
        self.option_exit.string = "MY JOB HERE IS DONE"

        # Music for the state
        self.data.GameAudio.PlayMusic(TrackIndex.win_music)


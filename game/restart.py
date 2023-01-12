from game.gamedata import GameData
from game.gameobjects.Player import Player
from game.gameobjects.gamemap import GameMap
from game.gameobjects.InterfaceHandler import UIHandler


def restart(data: GameData):
    # this just resets all the assest to make the game playable again
    data.game_map.initMap()
    data.player = Player(data)
    data.bread = 0
    data.UserInterface.initBaguette(0)
    # RESTARTING THE AUDIO ENGINE IS NEEDED BUT MAY BREAK THE GAME
    data.GameAudio.RestartAudio()
    # hello this is a comment to make this function look more complicated even
    # if it is only two lines of code!

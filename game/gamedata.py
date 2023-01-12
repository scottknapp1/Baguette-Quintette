import pyasge


class GameData:
    """
    GameData stores the data that needs to be shared

    When using multiple states in a game, you will find that
    some game data needs to be shared. GameData can be used to
    share access to data that the game and any running states may
    need.
    """

    def __init__(self) -> None:
        # UI data
        self.UserInterface = None

        # Sound data
        self.GameAudio = None

        # game data
        self.player = None
        self.cursor = None
        self.fonts = {}
        self.game_map = None
        self.game_res = [1920, 1080]
        self.inputs = None
        self.gamepad = None
        self.prev_gamepad = None
        self.renderer = None
        self.shaders: dict[str, pyasge.Shader] = {}
        self.retract_enemies = None
        self.bread = 0

        # Map loader Data
        self.costs = None
        self.checkpoints = None
        self.spawns = None
        self.chests = None
        self.teleporters = None
        self.spikes = None

        # Enemy Textures
        self.textures = None

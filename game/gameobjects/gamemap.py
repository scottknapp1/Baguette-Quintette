import copy
from functools import partial
import random
from typing import Tuple

import numpy
import numpy as np
import pyasge
import pytmx
from pytmx import TiledTileLayer


# Quick sort alogithm for the teleporters
# needed for correct function if the teleporters are not in order in the tilemap files
def sort(data):
    if len(data) < 2:  # checks if more than 1 element
        return data

    pivot = random.randint(0, len(data) - 1)
    left = []
    equal = []
    right = []

    for i in range(len(data)):
        if data[i][0] < data[pivot][0]:  # less than pivot
            right.append(data[i])
        elif data[i][0] == (data[pivot][0]):  # more than pivot
            equal.append(data[i])
        else:
            left.append(data[i])

    left = sort(left)
    right = sort(right)
    data = left + equal + right  # combines the array back together

    return data  # return array back to game sorted


def other_library_loader(renderer: pyasge.Renderer, filename, colorkey, **kwargs):
    """Converts a tmx tile into a `pyasge.Tile`"""

    def extract_image(rect, flags):
        pyasge_tile = pyasge.Tile()
        pyasge_tile.texture = renderer.loadTexture(filename)
        pyasge_tile.texture.setMagFilter(pyasge.MagFilter.NEAREST)
        pyasge_tile.width = rect[2]
        pyasge_tile.height = rect[3]
        pyasge_tile.src_rect = rect
        pyasge_tile.visible = True

        # rotate the tile on both axis if needed
        if flags.flipped_diagonally:
            if flags.flipped_vertically:
                pyasge_tile.rotation = 4.71239
            else:
                pyasge_tile.rotation = 1.5708

        # or maybe just on a single axis
        else:
            if flags.flipped_horizontally:
                pyasge_tile.src_rect[0] += pyasge_tile.src_rect[2]
                pyasge_tile.src_rect[2] *= -1

            if flags.flipped_vertically:
                pyasge_tile.src_rect[1] += pyasge_tile.src_rect[3]
                pyasge_tile.src_rect[3] *= -1

        return pyasge_tile

    return extract_image


class GameMap:
    """
    The GameMap is the heart of soul of the game world.

    It's made up from tiles that are stored in 2D dimensional arrays.
    To improve performance when rendering the game, these tiles are
    pre-rendered on to a large texture and rendered in a single pass
    """

    def __init__(self, renderer: pyasge.Renderer, tmx_file: str, data) -> None:
        # data reference for the map loader
        self.data = data
        self.redraw = None
        self.tile_map = None

        # Stores all the map data
        self.tmxdata = pytmx.TiledMap(tmx_file, partial(other_library_loader, renderer))

        # set the map's dimensions and tile sizes
        self.width = self.tmxdata.width
        self.height = self.tmxdata.height
        self.tile_size = [int(self.tmxdata.tilewidth), int(self.tmxdata.tileheight)]

        """create a new render target and sprite to store the render texture"""
        self.rt = pyasge.RenderTarget(
            renderer,
            self.width * self.tile_size[0], self.height * self.tile_size[1],
            pyasge.Texture.Format.RGBA, 1)

        self.initMap()

    def initMap(self):
        # Here it comes the mapLoader itself!

        # map_list
        self.tile_map = []

        # Object lists
        self.data.costs = []
        self.data.checkpoints = []
        self.data.spawns = []
        self.data.chests = []
        self.data.teleporters = []
        self.data.spikes = []

        # Stores the checkpoint areas
        # List composition Room N. X, Y, width and height
        for obj in self.tmxdata.layernames["Checkpoints"]:
            self.data.checkpoints.append([obj.Room, obj.x, obj.y, obj.width, obj.height])

        # Stores the SpawnPoint for the enemies
        # List composition Room N., Type, X, Y
        for obj in self.tmxdata.layernames["Spawns"]:
            self.data.spawns.append([obj.Room, obj.Type, obj.x, obj.y])

        # Stores the chest areas
        # List composition Type, X, Y, width and height
        for obj in self.tmxdata.layernames["Chests"]:
            self.data.chests.append([obj.Room, obj.Type, obj.x, obj.y, obj.width, obj.height])

        # Stores the teleporters
        # List composition Pair, X, Y, width, height and Room
        map_tps = []

        for obj in self.tmxdata.layernames["Teleporters"]:
            map_tps.append([obj.Pair, obj.x, obj.y, obj.width, obj.height, obj.Room])

        # it is needed here to reorder the teleporters list as the teleportation function
        # checks the index + 1 and index - 1 of the teleporter the player is standing on
        # if one of the two is his brother, the location of the player will be updated
        self.data.teleporters = sort(map_tps)
        self.data.teleporters.reverse()

        # Stores the spikes location
        # List composition X, Y, width, height and Room
        for obj in self.tmxdata.layernames["Spikes"]:
            self.data.spikes.append([obj.x, obj.y, obj.width, obj.height, obj.Room])

        # it initialises a list and fills it with 0s
        self.data.costs = [[0 for i in range(self.tmxdata.width)] for j in range(self.tmxdata.height)]

        # creates a list containing the two layers who are responsible for the walkable area of the map
        cost_layers = []
        cost_layers.append(self.tmxdata.layernames["Collidables"])
        cost_layers.append(self.tmxdata.layernames["SpikesVisuals"])
        cost_layers.append(self.tmxdata.layernames["Floor"])
        # cycles trough the tiles in those layers and gets the "cost" value
        for layer in cost_layers:
            for x, y, tile in layer.tiles():
                # update the cost map with using the layer cost
                self.data.costs[y][x] += layer.properties["cost"]

        # appends all the visible tiles to the tile_map list for rendering
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, TiledTileLayer):

                tiles = [[None for i in range(layer.width)] for j in range(layer.height)]
                for x, y, tile in layer.tiles():
                    # use the tile image to create and position the map
                    tiles[y][x] = pyasge.Tile(tile)
                    tiles[y][x].width = self.tile_size[0]
                    tiles[y][x].height = self.tile_size[1]

                self.tile_map.append((layer.name, tiles))

        self.redraw = True
        # self.blit(renderer, self.height * self.tile_size[0], self.width * self.tile_size[1])

    def tile(self, world_space: pyasge.Point2D) -> Tuple[int, int]:
        """ Translate world space co-ordinates to tile location

        Given a position in the game world, this function will find the
        corresponding tile it resides in. This can be used to retrieve
        data from the cost map.

        Args:
            world_space (pygame.Vector2): The world-space position to convert
        """

        tile = int(world_space.x / self.tile_size[0]), int(world_space.y / self.tile_size[1])
        return tile

    def world(self, tile_xy: Tuple[int, int]) -> pyasge.Point2D:
        """ Translate tile location to world space

        Given a tile location, this function will convert it to a
        position within the game world. It will always offset the
        position by the midpoint of the tile i.e. it's middle location

        Args:
            tile_xy (Tuple[int,int]):The tile location to convert
        """

        return pyasge.Point2D(
            ((tile_xy[0] + 1) * self.tile_size[0]) - (self.tile_size[0] * 0.5),
            ((tile_xy[1] + 1) * self.tile_size[1]) - (self.tile_size[1] * 0.5))

    def render(self, renderer: pyasge.Renderer, game_time: pyasge.GameTime) -> None:
        """ Renders the map and redraws it if needed """
        px_wide = self.width * self.tile_size[0]
        px_high = self.height * self.tile_size[1]

        if self.redraw:
            self.blit(renderer, px_high, px_wide)

        renderer.render(self.rt.buffers[0], [0, 0, px_wide, px_high], 0, 0, px_wide, px_high, 0)

    def blit(self, renderer, px_high, px_wide):
        """ Renders the game world in to a large single MSAA texture """

        # backup the current viewport and camera settings
        camera_view = np.array(renderer.resolution_info.view, copy=True)
        screen_viewport = pyasge.Viewport(renderer.resolution_info.viewport)

        # I'm experimenting with cameras here, those are temporary and may need to be removed later, or not,
        # they work greatly
        # Nvm i'm a moron - Simon
        # self.camera = pyasge.Camera(px_wide, px_high)
        # self.camera.lookAt(pyasge.Point2D(0, 0))

        # attach the offscreen texture and ensure whole map is framed
        renderer.setRenderTarget(self.rt)
        # renderer.setProjectionMatrix(self.camera.view)  # Imported the new camera here
        renderer.setProjectionMatrix(0, 0, px_wide, px_high)
        renderer.setViewport(pyasge.Viewport(0, 0, px_wide, px_high))

        # render the map
        for layer in self.tile_map:
            for row_index, row in enumerate(layer[1]):
                for col_index, tile in enumerate(row):
                    if tile:
                        renderer.render(tile,
                                        col_index * self.tile_size[0],
                                        row_index * self.tile_size[1])

        # detach the off-screen texture and reset viewport and camera
        renderer.setRenderTarget(None)
        renderer.setViewport(screen_viewport)
        renderer.setProjectionMatrix(camera_view)

        # resolves the MSAA texture, ready for rendering
        self.rt.resolve()
        self.redraw = False

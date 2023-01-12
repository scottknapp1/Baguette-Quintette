import pyasge
import heapq
from typing import Dict, List, Tuple, TypeVar, Optional
from game.gamedata import GameData

T = TypeVar('T')

Location = TypeVar('Location')


# code base from https://medium.com/@nicholas.w.swift/easy-a-star-pathfinding-7e6689c7f7b2
# https://www.redblobgames.com/pathfinding/a-star/implementation.html original source


class PriorityQueue:

    def __init__(self):
        self.elements: List[Tuple[float, T]] = []

    def empty(self) -> bool:
        return not self.elements

    def put(self, item: T, priority: float):
        heapq.heappush(self.elements, (priority, item))

    def get(self) -> T:
        return heapq.heappop(self.elements)[1]


def get_neighbours(game_data, current_node: Location, map_width, map_height) -> List[Location]:
    neighbours = []
    for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        node_position = (current_node[0] + new_position[0], current_node[1] + new_position[1])  # each eight neighbours

        if node_position[0] > map_width - 1 or node_position[0] < 0 or \
                node_position[1] > map_height - 1 or node_position[1] < 0:  # checks neighbour is in the map
            continue

        if game_data.costs[node_position[1]][node_position[0]] != 1:  # checks node cost
            continue

        neighbours.append(node_position)  # add to new position list

    return neighbours


def heuristic(a: Location, b: Location) -> float:  # H value under estimate  of most direct path
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)


def a_star_priority(game_data, start: Location, goal: Location):

    map_width = game_data.game_map.width  # maps size
    map_height = game_data.game_map.height

    frontier = PriorityQueue()  # Create priority queue
    frontier.put(start, 0)  # Put in starting node with the highest priority
    came_from: Dict[Location, Optional[Location]] = {}
    cost_so_far: Dict[Location, float] = {}
    came_from[start] = None  # neighbours from nodes being checked
    cost_so_far[start] = 0

    while not frontier.empty():
        current: Location = frontier.get()  # Current is now highest priority element from queue

        if current == goal:  # if end is met stops search
            break

        for node in get_neighbours(game_data, current, map_width, map_height):
            new_cost = cost_so_far[current] + game_data.costs[node[1]][node[0]]
            # adds cost of current node to neighbours

            if node not in cost_so_far or new_cost < cost_so_far[node]:  # checks if current cost is cheaper
                cost_so_far[node] = new_cost
                priority = new_cost + heuristic(node, goal)  # adds new cost and predicted cost to priority list
                frontier.put(node, priority)
                came_from[node] = current  # adds to list of nodes visited

    return came_from  # returns cheapest path


def reconstruct_path(came_from: Dict[Location, Location],
                     start: Location, goal: Location) -> List[Location]:

    current: Location = goal  # sets when we want to go
    path: List[Location] = []   # makes list of cheapest path
    while current != start:  # will fail if no path found
        path.append(current)
        current = came_from[current]
    path.append(start)  # sets up start location
    path.reverse()
    return path


def resolve(xy: pyasge.Point2D, data: GameData, enemy):
    # convert point to tile location
    tile_loc = data.game_map.tile(xy)  # last stop on journey
    tile_cost = data.costs[tile_loc[1]][tile_loc[0]]

    # use these to make sure you don't go out of bounds when checking neighbours
    # map_width = data.game_map.width
    # map_height = data.game_map.height

    # here's an example of tiles that the player should visit
    tiles_to_visit = []  # path

    # return a list of tile positions to follow
    start = data.game_map.tile(enemy.getMidPosition())
    end = tile_loc

    if tile_cost < 5:  # stops from clicking on any tiles over cost of 10
        path_finding = a_star_priority(data, start, end)

        cords_list = reconstruct_path(path_finding, start, end)  # takes cheapest math and sets the start to end route

        for coordinates in cords_list:
            tiles_to_visit.append(data.game_map.world(coordinates))  # converts map cords to tiles to visit list

    path = []
    for tile in tiles_to_visit:  # runs though the list and sets the path
        path.append(tile)
    return path

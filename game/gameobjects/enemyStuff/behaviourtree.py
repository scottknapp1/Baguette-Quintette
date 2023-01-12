import random
from enum import IntEnum
from game.gameobjects.enemyStuff.PathFinding import resolve, get_neighbours


class NodeType(IntEnum):
    SELECTOR = 1
    SEQUENCE = 2
    DECORATOR = 3
    LEAF = 4


class ReturnType(IntEnum):
    # return types
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3


class Node:
    def __init__(self):  # parent class

        self.children = []


class Root(Node):
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        return self.children[0].tick(enemy, data, timer)  # start of tree


class Sequence(Node):  # when one of its children returns failure or running it stops
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        for c in self.children:
            response = c.tick(enemy, data, timer)
            if response != ReturnType.SUCCESS:
                return response
        return ReturnType.SUCCESS


class Selector(Node):  # returns success or running
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        for c in self.children:
            response = c.tick(enemy, data, timer)
            if response != ReturnType.FAILURE:
                return response
        return ReturnType.FAILURE


class MoveMelee(Node):
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        if not len(enemy.route):

            target = data.player.getMidPosition()
            target_cost = data.game_map.tile(target)

            distance = target.distance(enemy.getMidPosition())

            if distance > 24:
                # only pathfinds if the distance between player and enemy is greater than a tile & a half.

                if data.costs[target_cost[1]][target_cost[0]] < 6:
                    # only pathfinds if the cost of the player position (target) is walkable (less than 6).

                    enemy.centreRoute((resolve(target, data, enemy)))  # moves enemy using pathfinder
                    return ReturnType.RUNNING

        return ReturnType.SUCCESS


class MoveMage(Node):
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        if not len(enemy.route):

            target = data.player.getMidPosition()
            target_cost = data.game_map.tile(target)

            distance = target.distance(enemy.getMidPosition())

            if distance > 24:
                # only pathfinds if the distance between player and enemy is greater than a tile & a half.

                if data.costs[target_cost[1]][target_cost[0]] < 6:
                    # only pathfinds if the cost of target tile is walkable (less than 6).

                    enemy.centreRoute((resolve(target, data, enemy)))
                    return ReturnType.RUNNING

        return ReturnType.SUCCESS


class MoveTeleporter(Node):

    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        if timer > random.uniform(4, 8):    # teleports at intervals of somewhere between 4 and 8.
            if enemy.teleport():
                return ReturnType.RUNNING

        return ReturnType.SUCCESS


class MoveRanger(Node):

    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):

        if not len(enemy.route):
            target_tile = enemy.generateRangedEnemyTargetOffset()
            target_world = data.game_map.world(target_tile)

            if timer > random.uniform(1, 3):    # Re-roots at intervals of somewhere between 4 and 8.

                if data.costs[target_tile[1]][target_tile[0]] < 6 and data.costs[target_tile[1]][target_tile[0]] != 0:
                    # only pathfinds if the cost of target tile is walkable (less than 6).
                    try:
                        enemy.centreRoute((resolve(target_world, data, enemy)))
                        if enemy.route != 0:
                            enemy.re_route_timer = 0
                            # Resets re-route timer so timer has to tick up before next re-root.
                    except:
                        return ReturnType.SUCCESS

                    return ReturnType.RUNNING

        return ReturnType.SUCCESS


class AttackMelee(Node):
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        enemy.attack()  # function allowing  melee attacking
        return ReturnType.RUNNING


class AttackRanged(Node):
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        if enemy.fireAtPlayer():  # function allowing  mages & other ranged classes to fire attack.
            return ReturnType.RUNNING
        return ReturnType.SUCCESS


class AttackTeleporter(Node):
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        enemy.fireAtPlayer()  # function allowing teleporters to fire attacking
        return ReturnType.RUNNING


class EnemyPathReset(Node):  # if player is in range of ai enemies
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        if timer > 1:
            enemy.route.clear()  # dont delete again please
            enemy.re_route_timer = 0
            return ReturnType.RUNNING

        return ReturnType.SUCCESS


class PlayerInRange(Node):  # if player is within a certain range of ai enemies
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        if enemy.getMidPosition().distance(data.player.getMidPosition()) < enemy.attack_player_range:
            return ReturnType.SUCCESS
        return ReturnType.RUNNING


class PlayerInRangeBoss(Node):  # if player is in range of ai enemies
    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        if enemy.getMidPosition().distance(data.player.getMidPosition()) < enemy.attack_player_range:
            return ReturnType.SUCCESS
        return ReturnType.FAILURE


class Inverter(Node):

    def __init__(self):
        super().__init__()

    def tick(self, enemy, data, timer):
        response = self.children[0].tick(enemy, data, timer)

        if response == ReturnType.SUCCESS:
            return ReturnType.FAILURE
        if response == ReturnType.FAILURE:
            return ReturnType.SUCCESS
        return ReturnType.RUNNING


class BehaviourTreeMelee:
    def __init__(self):
        self.root = Root()
        self.build_tree()

    def build_tree(self):
        # first layer of tree
        self.root.children.append(Sequence())
        self.root.children[0].children.append(EnemyPathReset())
        self.root.children[0].children.append(MoveMelee())
        self.root.children[0].children.append(AttackMelee())


class BehaviourTreeMage:
    def __init__(self):
        self.root = Root()
        self.build_tree()

    def build_tree(self):
        # first layer of tree
        self.root.children.append(Sequence())
        self.root.children[0].children.append(EnemyPathReset())
        self.root.children[0].children.append(MoveMage())
        self.root.children[0].children.append(PlayerInRange())
        self.root.children[0].children.append(AttackRanged())


class BehaviourTreeTeleporter:
    def __init__(self):
        self.root = Root()
        self.build_tree()

    def build_tree(self):
        # first layer of tree
        self.root.children.append(Sequence())
        self.root.children[0].children.append(MoveTeleporter())
        self.root.children[0].children.append(AttackTeleporter())


class BehaviourTreeRanger:
    def __init__(self):
        self.root = Root()
        self.build_tree()

    def build_tree(self):
        # first layer of tree
        self.root.children.append(Sequence())
        self.root.children[0].children.append(MoveRanger())
        self.root.children[0].children.append(PlayerInRange())
        self.root.children[0].children.append(AttackRanged())


class BehaviourTreeBoss:

    def __init__(self):
        self.root = Root()
        self.build_tree()

    def build_tree(self):
        # first layer of tree
        self.root.children.append(Selector())

        # second layer
        self.root.children[0].children.append(Sequence())  # melee sequence
        self.root.children[0].children.append(Sequence())  # ranger sequence

        # third layer
        self.root.children[0].children[0].children.append(PlayerInRangeBoss())
        self.root.children[0].children[0].children.append(EnemyPathReset())
        self.root.children[0].children[0].children.append(MoveMelee())
        self.root.children[0].children[0].children.append(AttackMelee())
        self.root.children[0].children[1].children.append(MoveRanger())
        self.root.children[0].children[1].children.append(AttackRanged())

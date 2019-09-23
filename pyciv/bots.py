import random
import numpy as np
from collections import Counter

from . import YIELD_TYPES
from . import utils as civutils
from .utils import Action
from .buildings import BUILDINGS
from .units import UNITS


MAX_ITER = 10


class BasicBot:
    def __init__(self, civ, **kwargs):
        self.civ = civ
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_action(self, game):
        civ = self.civ
        actions = []
        for city in civ.cities:
            actions += self.city_actions(city, game)
        for unit in civ.units:
            if unit.moves > 0:
                if unit._type == 'settler':
                    actions += self.settler_actions(unit, game)
                if unit._type == 'worker':
                    actions += self.worker_actions(unit, game)
                if unit._type == 'combat':
                    actions += self.combat_actions(unit, game)
        if len(actions) > 0:
            action = random.choice(actions)
        else:
            action = Action('end_turn')
        return action

    def city_actions(self, city, game):
        actions = []
        for target in city.get_targets(game):
            actions.append(Action('range_attack', city=city, target=target))
        if city.prod is None:
            for prod_opt in city.prod_options():
                actions.append(Action('build', city=city, target=prod_opt))
        return actions

    def settler_actions(self, unit, game):
        # By default, try to settle in place
        if 'settle' in unit.actions(game):
            actions = [Action('settle', unit=unit)]
        else:
            actions = []
        # Move if we can find a better settling spot
        pos = unit.pos
        tile = game.board[pos]
        moves = unit.get_moves(game)
        neighbors = civutils.neighbors(pos, game.board, 2)
        tiles = [tile] + neighbors
        scores = {}
        for t in tiles:
            score = game.settler_score(t.pos, game.find_civ(unit.civ))
            if t.moves <= unit.movement and score > 0:
                scores[t.pos] = score
        if scores:
            best = max(scores.keys(), key=lambda x: scores[x])
            if best != pos:
                path, costs = civutils.find_best_path(pos, best, game)
                target = None
                for i in range(1, len(path)):
                    if costs[path[i]] <= unit.moves:
                        target = game.board[path[i]]
                    else:
                        break
                if target:
                    actions = [Action('move', unit=unit, target=target)]
        return actions

    def worker_actions(self, unit, game):
        # By default, do something on current tile
        actions = [Action(a, unit=unit) for a in unit.actions(game) if a != 'move']
        pos = unit.pos
        tiles = game.board.tiles()
        scores = {}
        for t in tiles:
            score = game.worker_score(t.pos, game.find_civ(unit.civ))
            if t.moves <= unit.movement and score > 0:
                scores[t.pos] = score
        if scores:
            best = max(scores.keys(), key=lambda x: scores[x])
            if best != pos:
                path, costs = civutils.find_best_path(pos, best, game)
                target = None
                for i in range(1, len(path)):
                    if costs[path[i]] <= unit.moves:
                        target = game.board[path[i]]
                    else:
                        break
                if target:
                    actions = [Action('move', unit=unit, target=target)]
        return actions

    def combat_actions(self, unit, game):
        # By default, fortify
        actions = [Action('fortify', unit=unit)]
        tile = game.board[unit.pos]
        attack_type = unit.attack + ' attack'
        target_tiles = unit.get_targets(game)
        move_tiles = unit.get_moves(game)
        if target_tiles:
            weights = []
            for target_tile in target_tiles:
                target_unit = game.get_unit(target_tile)
                target_city = game.get_city(target_tile)
                if target_city or target_unit:
                    actions.append(Action(attack_type, unit=unit, target=target_tile))
        if move_tiles:
            paths = []
            for civ in game.civs:
                if civ.name != unit.civ:
                    targets = civ.cities + civ.units
                    for t in targets:
                        path, costs = civutils.find_best_path(unit.pos, t.pos, game)
                        paths.append((path, costs))
            if paths:
                for path, costs in paths:
                    target = None
                    for i in range(1, len(path)):
                        tile = game.board[path[i]]
                        if costs[path[i]] <= unit.moves and tile in move_tiles:
                            target = tile
                        else:
                            break
                    if target:
                        actions.append(Action('move', unit=unit, target=target))
        return actions

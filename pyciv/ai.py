import random
import numpy as np
from collections import Counter

from . import YIELD_TYPES
from . import utils as civutils


MAX_ITER = 10


class AI:
    def __init__(self, civ, **kwargs):
        self.civ = civ
        for k, v in kwargs.items():
            setattr(self, k, v)

    def play(self, game):
        civ = self.civ
        for unit in civ.units:
            action, target = self.unit_action(unit, game)
            if action is not None:
                if action == 'move':
                    game.move_unit(unit, target)
                elif action == 'settle':
                    game.settle(unit)
                elif 'attack' in action:
                    game.combat_action(unit, target, action)
                elif unit._class == 'worker':
                    game.worker_action(unit, action)
#            i = 0
#            while unit.actions(game) and i < MAX_ITER:
#                action = random.choice(unit.actions(game))
#                if action == 'move':
#                    moves = unit.get_moves(game)
#                    if moves:
#                        move = random.choice(moves)
#                        game.move_unit(unit, move)
#                elif action == 'settle':
#                    game.settle(unit)
#                    break
#                elif 'attack' in action:
#                    targets = unit.get_targets(game)
#                    if targets:
#                        target = random.choice(targets)
#                        game.combat_action(unit, target, action)
#                elif unit._class == 'worker':
#                    game.worker_action(unit, action)
#                i += 1
        for city in civ:
            if not city.prod:
                prod_opts = city.prod_options()
                if prod_opts:
                    prod = random.choice(prod_opts)
                    city.begin_prod(prod)

    def unit_action(self, unit, game):
        choices = []
        for action in unit.actions(game):
            if action == 'move':
                moves = unit.get_moves(game)
                for move in moves:
                    choices.append((action, move, 1))
            elif action == 'settle':
                choices.append((action, None, 1))
            elif 'attack' in action:
                targets = unit.get_targets(game)
                if targets:
                    for target in targets:
                        choices.append((action, target, 1))
            elif unit._class == 'worker':
                choices.append((action, None, 1))
        if len(choices) > 0:
            actions, targets, weights = zip(*choices)
            idx = random.choices(range(len(weights)), weights)[0]
            return actions[idx], targets[idx]
        else:
            return None, None

    def city_action(self, city, game):
        choices = []
        prod_opts = city.prod_options()
        for prod in prod_opts:
            choices.append(prod, prod.cost['production'])
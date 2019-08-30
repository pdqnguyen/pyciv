import random
import numpy as np
from collections import Counter

from . import YIELD_TYPES
from . import utils as civutils
from .buildings import BUILDINGS
from .units import UNITS


MAX_ITER = 10


class AI:
    def __init__(self, civ, **kwargs):
        self.civ = civ
        for k, v in kwargs.items():
            setattr(self, k, v)

    def play(self, game):
        civ = self.civ
        print(civ.name)
        for unit in civ.units:
            i = 0
            max_attempts = unit.moves
            while unit.moves > 0 and i < max_attempts:
                eval('self.{}_action(unit, game)'.format(unit._type))
                i += 1
        for city in civ:
            if not city.prod:
                prod_opts = city.prod_options()
                if prod_opts:
                    prod = random.choice(prod_opts)
                    city.begin_prod(prod)

    def settler_action(self, unit, game):
        pos = unit.pos
        tile = game.board[pos]
        neighbors = civutils.neighbors(pos, game.board, 2)
        tiles = [tile] + neighbors
        scores = {}
        for t in [tile] + tiles:
            score = game.settler_score(t.pos, game.find_civ(unit.civ))
            if t.moves <= unit.movement and score > 0:
                scores[t.pos] = score
        if scores:
            best = max(scores.keys(), key=lambda x: scores[x])
            if best == pos:
                game.settle(unit)
            else:
                path, _ = civutils.find_best_path(pos, best, game)
                game.move_unit(unit, game.board[path[1]])
        elif 'settle' in unit.actions(game):
            game.settle(unit)
        else:
            nb = random.choice(civutils.neighbors(pos, game.board))
            game.move_unit(unit, nb)

    def worker_action(self, unit, game):
        pos = unit.pos
        tiles = game.board.tiles()
        scores = {}
        for t in tiles:
            score = game.worker_score(t.pos, game.find_civ(unit.civ))
            if t.moves <= unit.movement and score > 0:
                scores[t.pos] = score
        if scores:
            best = max(scores.keys(), key=lambda x: scores[x])
            if best == pos:
                actions = [action for action in unit.actions(game) if action != 'move']
                if actions:
                    action = random.choice(actions)
                    game.worker_action(unit, action)
            else:
                path, cost = civutils.find_best_path(pos, best, game)
                game.move_unit(unit, game.board[path[1]])
        else:
            nb = random.choice(civutils.neighbors(pos, game.board))
            game.move_unit(unit, nb)

    def combat_action(self, unit, game):
        tile = game.board[unit.pos]
        attack_type = unit.attack + ' attack'
        target_tiles = unit.get_targets(game)
        move_tiles = unit.get_moves(game)
        if target_tiles:
            weights = []
            for target_tile in target_tiles:
                target_unit = game.get_unit(target_tile)
                target_city = game.get_city(target_tile)
                if target_city:
                    if target_city.hp == 0:
                        w = 100
                    elif target_unit:
                        atk_dmg, def_dmg = civutils.calc_city_damage(unit, target_city, tile, target_tile, attack_type, garrison=target_unit)
                        w = atk_dmg - def_dmg
                    else:
                        atk_dmg, def_dmg = civutils.calc_city_damage(unit, target_city, tile, target_tile, attack_type)
                        w = atk_dmg - def_dmg
                elif target_unit:
                    atk_dmg, def_dmg = civutils.calc_unit_damage(unit, target_unit, tile, target_tile, attack_type)
                    w = atk_dmg - def_dmg
                else:
                    w = 0
                weights.append(max(w, 0))
            if max(weights) > 0:
                weights = np.array(weights) / sum(weights)
                target_tile = np.random.choice(target_tiles, p=weights)
                game.combat_action(unit, target_tile, attack_type)
                return
            elif unit.hp > 30:
                game.combat_action(unit, tile, 'fortify')
                return
            else:
                pass
        if move_tiles:
            paths = []
            for civ in game.civs:
                if civ.name != unit.civ:
                    for city in civ.cities:
                        path, cost = civutils.find_best_path(unit.pos, city.pos, game)
                        if len(path) > 2:
                            paths.append((path, cost))
            if paths:
                shortest_path = min(paths, key=lambda x: x[1])[0]
                game.move_unit(unit, game.board[shortest_path[1]])
            else:
                game.move_unit(unit, random.choice(civutils.neighbors(unit.pos, game.board)))
            return
        if 'fortify' in unit.actions(game):
            game.combat_action(unit, tile, 'fortify')
            return

    def city_action(self, city, game):
        civ = game.find_civ(city.civ)
        prod_opts = city.prod_options()
        weights = []
        for prod in prod_opts:
            w = 1
            if prod == 'worker':
                workers = [u for u in civ.units if u._class == 'worker']
                if len(workers) > 3:
                    w = 0
            weights.append(w)
        prod = np.random.choice(prod_opts, p=weights)
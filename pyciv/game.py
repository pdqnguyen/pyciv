import random
import time
import numpy as np

from . import mapmaker
from .civilizations import Civilization
from .render import RenderGame
from . import utils as civutils
from .buildings import Building
from .units import Unit
from .ai import AI
from .improvements import improvement_options

MAX_ITER = 1000
MIN_CITY_SEP = 4
MAP_ATTEMPTS = 10

class Game(object):
    def __init__(self, shape, civs, leaders, map_config_file=None, ai_only=False):
        self.shape = shape
        self.civs = [Civilization(civ, leaders) for civ in civs]
        self._init_ai()
        if ai_only:
            self.humans = []
        else:
            self.humans = civs[0]
        self._init_map(map_config_file=map_config_file)
        self._init_civs()
        self.turn = 0
        self.active = 0

    def _init_ai(self):
        ai = {}
        for civ in self.civs:
            ai[civ.name] = AI(civ)
        self.ai = ai

    def _init_map(self, map_config_file=None):
        for _ in range(MAP_ATTEMPTS):
            try:
                self.board = mapmaker.make(self.shape, map_config_file=map_config_file)
            except:
                raise
            else:
                return
        raise RuntimeError("failed to generate map")

    def _init_civs(self):
        open_tiles = [tile for tile in self.board if tile.base != 'ocean' and 'mountain' not in tile.features]
        for civ in self.civs:
            i = 0
            while open_tiles and i < MAX_ITER:
                random.shuffle(open_tiles)
                tile1 = open_tiles.pop(0)
                if (tile1.base != 'ocean') and ('ice' not in tile1.features) and ('mountain' not in tile1.features) and (not self.get_civ(tile1)):
                    neighbors = civutils.neighbors(tile1.pos, self.board, 5)
                    if not any(self.get_unit(nb) for nb in neighbors):
                        tile2 = random.choice(civutils.neighbors(tile1.pos, self.board, 1))
                        unit1_name = 'unit' + civutils.random_str(8)
                        unit2_name = 'unit' + civutils.random_str(8)
                        self.add_unit(tile1, civ, unit1_name, 'settler')
                        self.add_unit(tile2, civ, unit2_name, 'warrior')
#                         for nb in civutils.neighbors(tile1.pos, self.board, 1)[:]:
#                             self.add_unit(nb, civ, unit2_name, 'warrior')
                        break
                i += 1

    def active_civ(self):
        return self.civs[self.active]

    def find_civ(self, name):
        for civ in self.civs:
            if civ.name == name:
                return civ

    def get_civ(self, tile):
        for civ in self.civs:
            if tile in civ.tiles():
                return civ

    def get_city(self, tile, any_tile=False):
        for civ in self.civs:
            for city in civ:
                if any_tile:
                    if tile in city.tiles:
                        return city
                else:
                    if tile == city.tiles[0]:
                        return city

    def get_units(self, tile):
        units = []
        for civ in self.civs:
            for unit in civ.units:
                if tile:
                    if tile.pos == unit.pos:
                        units.append(unit)
        return units

    def get_unit(self, tile):
        units = self.get_units(tile)
        unit_types = [unit._type for unit in units]
        if 'combat' in unit_types:
            return units[unit_types.index('combat')]
        elif len(units) > 0:
            return units[0]
        else:
            return None

    def add_city(self, tile, civ, name, **kwargs):
        tile.remove_features(*['forest', 'rainforest'])
        tiles = [tile] + self.board.get_neighbors(tile)
        city = civ.add_city(tiles, name, **kwargs)
        return city

    def add_unit(self, tile, civ, name, _class, **kwargs):
        unit = civ.add_unit(tile, name, _class, **kwargs)
        return unit

    def change_civ(self, city, new_civ):
        old_civ = self.find_civ(city.civ)
        city.reassign(new_civ.name)
        new_civ.append_city(city)
        old_civ.remove_city(city)

    def move_unit(self, unit, tile):
        if tile in unit.get_moves(self):
            path, cost = civutils.find_best_path(unit.pos, tile.pos, self)
            unit.move(tile.pos, cost)
        else:
            print("invalid move")

    def settle(self, unit):
        tile = self.board[unit.pos]
        civ = self.find_civ(unit.civ)
        name = 'city' + civutils.random_str(8)
        capital = (False if civ.capital else True)
        self.add_city(tile, civ, name, capital=capital)
        civ.remove_unit(unit)

    def settler_score(self, pos, civ):
        tile = self.board[pos]
        tile_civ = self.get_civ(tile)
        occupied = (tile_civ and (tile_civ != civ))
        near_city = any(self.get_city(nb) for nb in civutils.neighbors(pos, self.board, r=3))
        if occupied or near_city:
            return 0
        else:
            total = sum(tile.yields.values())
            for nb in civutils.neighbors(pos, self.board, r=1):
                if self.get_civ(nb):
                    total += 0
                elif nb.resources:
                    total += 2 * sum(nb.yields.values())
                else:
                    total += sum(nb.yields.values())
            return total

    def settler_scores(self, settler):
        out = np.zeros_like(self.board)
        for i in range(out.shape[0]):
            for j in range(out.shape[1]):
                pos = (i, j)
                out[pos] = self.settler_score(pos, self.find_civ(settler.civ))
        return out

    def worker_action(self, unit, action):
        tile = self.board[unit.pos]
        if action == 'chop':
            if 'forest' in tile.features:
                tile.remove_features('forest')
            elif 'rainforest' in tile.features:
                tile.remove_features('rainforest')
            self.get_city(tile, any_tile=True).prod_progress += 20
        elif action == 'harvest':
            tile.remove_features(*tile.features)
            self.get_city(tile, any_tile=True).pp += 20
        else:
            tile.add_improvement(action)
        unit.move(unit.pos, 1)
        unit.builds -= 1
        if unit.builds == 0:
            del unit

    def worker_score(self, pos, civ):
        tile = self.board[pos]
        tile_civ = self.get_civ(tile)
        if tile_civ == civ and not self.get_city(tile) and improvement_options(tile):
            if tile.resources:
                return 2 * sum(tile.yields.values())
            else:
                return sum(tile.yields.values())
        else:
            return 0

    def worker_scores(self, worker):
        out = np.zeros_like(self.board)
        for i in range(out.shape[0]):
            for j in range(out.shape[1]):
                pos = (i, j)
                out[pos] = self.worker_score(pos, self.find_civ(worker.civ))
        return out

    def combat_action(self, unit, target_tile, action):
        unit_tile = self.board[unit.pos]
        civ = self.find_civ(unit.civ)
        target_city = self.get_city(target_tile)
        target_unit = self.get_unit(target_tile)
        if 'attack' in action:
            if target_city:
                target_civ = self.find_civ(target_city.civ)
                if civ != target_civ:
                    unit.unfortify()
                    atk_dmg, def_dmg = civutils.calc_city_damage(unit, target_city, unit_tile, target_tile, action, garrison=target_unit)
                    target_city.damage(atk_dmg)
                    unit.damage(def_dmg)
                    hp = unit.hp
                    target_hp = target_city.hp
                    if action == 'melee attack':
                        if hp > 0 and target_hp <= 0:
                            print("{} ({}) took over {} ({})".format(unit._class, civ.name, target_city.name, target_civ.name))
                            self.change_civ(target_city, civ)
                            if target_unit:
                                target_civ.remove_unit(target_unit)
                            self.move_unit(unit, target_tile)
                            unit.move(unit.pos, unit.moves)
                            unit.update_exp(2)
                            target_city.update_hp(50)
                        elif hp <= 0 and target_hp > 0:
                            print("{} ({}) died while attacking {} ({})".format(unit._class, civ.name, target_city.name, target_civ.name))
                            civ.remove_unit(unit)
                        else:
                            unit.move(unit.pos, unit.moves)
                            unit.update_exp(2)
                    elif action == 'range attack':
                        unit.move(unit.pos, unit.moves)
                        unit.update_exp(1)
            elif target_unit:
                target_unit_type = type(target_unit).__name__
                target_civ = self.find_civ(target_unit.civ)
                if civ != target_civ:
                    unit.unfortify()
                    if target_unit_type == 'CombatUnit':
                        atk_dmg, def_dmg = civutils.calc_unit_damage(unit, target_unit, unit_tile, target_tile, action)
                        print("{} ({}) did {} damage to {} ({})".format(unit._class, civ.name, atk_dmg, target_unit._class, target_civ.name))
                        print("{} ({}) did {} damage to {} ({})".format(target_unit._class, target_civ.name, def_dmg, unit._class, civ.name))
                        target_unit.damage(atk_dmg)
                        unit.damage(def_dmg)
                        hp = unit.hp
                        target_hp = target_unit.hp
                        if hp > 0 and target_hp <= 0:
                            print("{} ({}) killed {} ({})".format(unit._class, civ.name, target_unit._class, target_civ.name))
                            target_civ.remove_unit(target_unit)
                            if action == 'melee attack':
                                unit.move(target_tile.pos, target_tile.moves)
                            else:
                                unit.move(unit.pos, 1)
                            unit.update_exp(2)
                        elif hp <= 0 and target_hp > 0:
                            print("{} ({}) died while attacking {} ({})".format(unit._class, civ.name, target_unit._class, target_civ.name))
                            civ.remove_unit(unit)
                            target_unit.update_exp(1)
                        elif hp <= 0 and target_hp <= 0:
                            print("{} ({}) and {} ({}) died fighting".format(unit._class, civ.name, target_unit._class, target_civ.name))
                            civ.remove_unit(unit)
                            target_civ.remove_unit(target_unit)
                        else:
                            target_unit.update_exp(1)
                            unit.move(unit.pos, 1)
                            unit.update_exp(2)
                    elif target_unit_type in ['WorkerUnit', 'SettlerUnit']:
                        print("{} ({}) killed {} ({})".format(unit._class, civ.name, target_unit._class, target_civ.name))
                        target_civ.remove_unit(target_unit)
                        if action == 'melee attack':
                            unit.move(target_tile.pos, target_tile.moves)
        elif action == 'fortify':
            unit.fortify()
            unit.move(unit.pos, unit.moves)

    def end_turn(self):
        civ = self.active_civ()
        for city in civ:
            new_item = city.update_prod()
            if new_item:
                if isinstance(new_item, Building):
                    city.add_building(new_item)
                elif isinstance(new_item, Unit):
                    unit = new_item
                    for tile in city:
                        if not self.get_unit(tile):
                            self.add_unit(tile, civ, unit.name, unit._class)
                            break
            city.update_pp()
            city.update_tiles(self)
            civ.update_totals(city.yields)
            city.update_hp()
        units = civ.units
        for unit in units:
            unit.end_turn(self)
            if unit._class == 'worker':
                if unit.builds == 0:
                    civ.remove_unit(unit)
        self.active += 1
        if self.active >= len(self.civs):
            self.active = 0
            self.turn += 1

    def cpu_turn(self):
        self.ai[self.active_civ().name].play(self)
        self.end_turn()
import random
import time

from . import mapmaker
from .civilizations import Civilization
from .render import RenderGame
from . import utils as civutils
from .buildings import Building
from .units import Unit

MAX_ITER = 1000
MIN_CITY_SEP = 4
CITIES_PER_CIV = 1

class Game(object):
    def __init__(self, shape, civs, leaders, map_config_file=None):
        self.shape = shape
        self.civs = [Civilization(civ, leaders) for civ in civs]
        self.humans = civs[:1]
        self._init_map(map_config_file=map_config_file)
        self._init_civs()
        self.turn = 0
        self.active = 0

    def _init_map(self, map_config_file=None):
        for _ in range(5):
            try:
                self.board = mapmaker.make(self.shape, map_config_file=map_config_file)
            except:
                pass
            else:
                return
        raise RuntimeError("failed to generate map")

    def _init_civs(self):
        open_tiles = [tile for tile in self.board]
        civ_tiles = []
        n_cities_total = 1
        for civ in self.civs:
            n_cities = 0
            i = 0
            while n_cities < CITIES_PER_CIV and open_tiles and i < MAX_ITER:
                random.shuffle(open_tiles)
                tile1 = open_tiles.pop(0)
                if (tile1.base != 'ocean') and ('ice' not in tile1.features) and ('mountain' not in tile1.features) and (not self.get_civ(tile1)):
                    nearby_cities = False
                    for tile2 in civ_tiles:
                        d = civutils.distance(tile1.pos, tile2.pos, self.shape[0] - 1)
                        if d < MIN_CITY_SEP:
                            nearby_cities = True
                            break
                    if not nearby_cities:
                        city_name = 'city' + civutils.random_str(8)
                        unit_name = 'unit' + civutils.random_str(8)
                        #city = self.add_city(tile1, civ, city_name, capital=True)
                        unit = self.add_unit(tile1, civ, unit_name, 'warrior')
                        #city.begin_prod('monument')
                        civ_tiles += [tile1]
                        n_cities_total += 1
                        n_cities += 1
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

    def get_unit(self, tile):
        for civ in self.civs:
            for unit in civ.units:
                if tile:
                    if tile.pos == unit.pos:
                        return unit

    def add_city(self, tile, civ, name, **kwargs):
        tile.remove_features(*['forest', 'rainforest'])
        tiles = [tile] + self.board.get_neighbors(tile)
        city = civ.add_city(tiles, name, **kwargs)
        return city

    def add_unit(self, tile, civ, name, _class, **kwargs):
        unit = civ.add_unit(tile, name, _class, **kwargs)
        return unit

    def move_unit(self, unit, tile):
        tiles_in_range = civutils.tiles_in_range(unit.pos, 1, self.shape)
        if (tile.pos in tiles_in_range) and (unit.moves >= tile.moves):
            target_unit = self.get_unit(tile)
            target_city = self.get_city(tile)
            if target_unit:
                if target_unit.civ != unit.civ or target_unit._class != unit._class:
                    print("another unit is in the way")
                    return
            if target_city:
                if target_city.civ != unit.civ:
                    print("cannot enter enemy city")
                    return
            if type(unit).__name__ == 'CombatUnit':
                unit.unfortify()
            unit.move(tile.pos, tile.moves)
        else:
            print("invalid move")

    def settle(self, unit):
        tile = self.board[unit.pos]
        civ = self.find_civ(unit.civ)
        name = 'city' + civutils.random_str(8)
        capital = (False if civ.capital else True)
        self.add_city(tile, civ, name, capital=capital)
        civ.remove_unit(unit)

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

    def combat_action(self, unit, target_tile, action):
        unit_tile = self.board[unit.pos]
        target_unit = self.get_unit(target_tile)
        if target_unit:
            target_unit_type = type(target_unit).__name__
            target_civ = self.find_civ(target_unit.civ)
            civ = self.find_civ(unit.civ)
            if civ!= target_civ:
                if action == 'melee':
                    unit.unfortify()
                    if target_unit_type == 'CombatUnit':
                        strength_diff = unit.atk_strength(unit_tile) - target_unit.def_strength(target_tile)
                        atk_dmg = 30 * 1.041 ** (strength_diff) #* random.uniform(0.75, 1.25)
                        def_dmg = 30 * 1.041 ** (-strength_diff) #* random.uniform(0.75, 1.25)
                        print("{} ({}) did {} damage to {} ({})".format(unit.name, civ.name, atk_dmg, target_unit.name, target_civ.name))
                        print("{} ({}) did {} damage to {} ({})".format(target_unit.name, target_civ.name, def_dmg, unit.name, civ.name))
                        target_unit.damage(atk_dmg)
                        unit.damage(def_dmg)
                        hp = unit.hp
                        target_hp = target_unit.hp
                        if hp > 0 and target_hp <= 0:
                            print("{} ({}) killed {} ({})".format(unit.name, civ.name, target_unit.name, target_civ.name))
                            target_civ.remove_unit(target_unit)
                            self.move_unit(unit, target_tile)
                        elif hp <= 0 and target_hp > 0:
                            print("{} ({}) died while attacking {} ({})".format(unit.name, civ.name, target_unit.name, target_civ.name))
                            civ.remove_unit(unit)
                        elif hp <= 0 and target_hp <= 0:
                            print("{} ({}) and {} ({}) died fighting".format(unit.name, civ.name, target_unit.name, target_civ.name))
                            civ.remove_unit(unit)
                            target_civ.remove_unit(target_unit)
                        else:
                            unit.move(unit.pos, 1)
                    elif target_unit_type in ['WorkerUnit', 'SettlerUnit']:
                        print("{} ({}) killed {} ({})".format(unit.name, civ.name, target_unit.name, target_civ.name))
                        civ.remove_unit(target_unit)
                        self.move_unit(unit, target_tile)
                elif action == 'fortified':
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
        for civ in self.civs:
            units = civ.units
            for unit in units:
                unit.reset_moves()
                if unit._class == 'worker':
                    if unit.builds == 0:
                        civ.remove_unit(unit)
        self.turn += 1
        self.active += 1
        if self.active >= len(self.civs):
            self.active = 0

    def cpu_turn(self):
        civ = self.active_civ()
        for unit in civ.units:
            i = 0
            while unit.actions(self) and i < MAX_ITER:
                action = random.choice(unit.actions(self))
                if action == 'move':
                    move_opts = unit.get_moves(self)
                    if move_opts:
                        dest = self.board[random.choice(move_opts)]
                        self.move_unit(unit, dest)
                elif action == 'settle':
                    self.settle(unit)
                    break
                elif action == 'melee':
                    targets = unit.get_targets(self)
                    if targets:
                        target = self.board[random.choice(targets)]
                        self.combat_action(unit, target, 'melee')
                elif unit._class == 'worker':
                    self.worker_action(unit, action)
                i += 1
        for city in civ:
            if not city.prod:
                prod_opts = city.prod_options()
                if prod_opts:
                    prod = random.choice(prod_opts)
                    city.begin_prod(prod)
        self.end_turn()
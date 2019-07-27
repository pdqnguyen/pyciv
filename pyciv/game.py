import random
import time

from . import mapmaker
from .civilizations import Civilization
from .render import RenderGame
from . import utils as civutils

MAX_ITER = 1000
MIN_CITY_SEP = 4
CITIES_PER_CIV = 1

class Game(object):
    def __init__(self, shape, civs, leaders, map_config_file=None):
        self.shape = shape
        self.civs = [Civilization(civ, leaders) for civ in civs]
        self.humans = civs[:2]
        self._init_map(map_config_file=map_config_file)
        self._init_cities()
        self.turn = 0
        self.active = 0

    def _init_map(self, map_config_file=None):
        for _ in range(5):
            try:
                self.board = mapmaker.make(self.shape, map_config_file=map_config_file)
            except:
                continue
            else:
                return
        raise RuntimeError("failed to generate map")

    def _init_cities(self):
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
                        city = self.add_city(tile1, civ, city_name, capital=True)
                        unit = self.add_unit(tile1, civ, unit_name, 'settler')
                        city.begin_prod('monument')
                        civ_tiles += city.tiles
                        n_cities_total += 1
                        n_cities += 1
                i += 1

    def add_city(self, tile, civ, name, **kwargs):
        tiles = [tile] + self.board.get_neighbors(tile)
        city = civ.add_city(tiles, name, **kwargs)
        return city

    def add_unit(self, tile, civ, name, _class, **kwargs):
        civ = self.get_civ(tile)
        unit = civ.add_unit(tile, name, _class, **kwargs)
        return unit

    def get_civ(self, tile):
        for civ in self.civs:
            if tile in civ.tiles():
                return civ

    def get_city(self, tile):
        for civ in self.civs:
            for city in civ:
                if tile == city.tiles[0]:
                    return city

    def get_unit(self, tile):
        for civ in self.civs:
            for unit in civ.units:
                if tile:
                    if tile.pos == unit.pos:
                        return unit

    def move_unit(self, unit, tile):
        tiles_in_range = civutils.tiles_in_range(unit.pos, 1, self.board.shape[0] - 1)
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
            unit.move(tile.pos, tile.moves)
        else:
            print("invalid move")

    def active_civ(self):
        return self.civs[self.active]

    def end_turn(self):
        self.active_civ().update()
        for civ in self.civs:
            for unit in civ.units:
                unit.reset_moves()
        self.turn += 1
        self.active += 1
        if self.active >= len(self.civs):
            self.active = 0

    def cpu_turn(self):
        time.sleep(0.5)
        self.end_turn()
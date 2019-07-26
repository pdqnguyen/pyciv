import random
import time

from . import mapmaker
from .civilizations import Civilization
from .render import RenderGame
from .utils import distance

MAX_ITER = 1000
MIN_CITY_SEP = 4
CITIES_PER_CIV = 1

class Game(object):
    def __init__(self, shape, civs, leaders, map_config_file=None):
        self.shape = shape
        self.civs = [Civilization(civ, leaders) for civ in civs]
        self.humans = civs[0]
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
                break

    def _init_cities(self):
        open_tiles = [tile for tile in self.board]
        civ_tiles = []
        city_name = 1
        for civ in self.civs:
            n_cities = 0
            i = 0
            while n_cities < CITIES_PER_CIV and open_tiles and i < MAX_ITER:
                random.shuffle(open_tiles)
                tile1 = open_tiles.pop(0)
                if (tile1.base != 'ocean') and ('ice' not in tile1.features) and ('mountain' not in tile1.features) and (not self.get_civ(tile1)):
                    nearby_cities = False
                    for tile2 in civ_tiles:
                        d = distance(tile1, tile2, self.shape[0])
                        if d < MIN_CITY_SEP:
                            nearby_cities = True
                            break
                    if not nearby_cities:
                        name = 'city' + str(city_name)
                        city_name += 1
                        city_tiles = [tile1] + self.board.get_neighbors(tile1)
                        city = civ.add_city(city_tiles, name, capital=True)
                        city.begin_prod('monument')
                        n_cities += 1
                        civ_tiles += city_tiles
                i += 1

    def get_civ(self, tile):
        for civ in self.civs:
            if tile in civ.tiles():
                return civ

    def get_city(self, tile):
        for civ in self.civs:
            for city in civ:
                if tile in city.tiles:
                    return city

    def active_civ(self):
        return self.civs[self.active]

    def end_turn(self):
        for civ in self.civs:
            for city in civ:
                city.update_prod()
                city.update_pp()
        self.turn += 1
        self.active += 1
        if self.active >= len(self.civs):
            self.active = 0

    def cpu_turn(self):
        time.sleep(0.5)
        self.end_turn()
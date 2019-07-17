import random

from . import mapmaker
from .render import RenderGame
from .utils import distance

MAX_ITER = 1000
MIN_CITY_SEP = 4
CITIES_PER_CIV = 1

class Game(object):
    def __init__(self, shape, civs, map_config_file=None):
        self.shape = shape
        self.civs = civs
        self._init_map(map_config_file=map_config_file)
        self._init_cities()
        self.turn = 0
        self.active = 0

    def _init_map(self, map_config_file=None):
        self.board = mapmaker.make(self.shape, map_config_file=map_config_file)

    def _init_cities(self):
        for civ in self.civs:
            cities = []
            i = 0
            open_tiles = [tile for tile in self.board]
            while len(cities) < CITIES_PER_CIV and open_tiles and i < MAX_ITER:
                random.shuffle(open_tiles)
                tile1 = open_tiles.pop(0)
                if (tile1.base != 'ocean') and ('ice' not in tile1.features) and ('mountain' not in tile1.features) and (not tile1.city):
                    nearby_cities = False
                    nearby_tiles = []
                    for tile2 in open_tiles:
                        d = distance(tile1, tile2, self.shape[0])
                        if d < MIN_CITY_SEP:
                            nearby_tiles.append(tile2)
                            if tile2.civ:
                                nearby_cities = True
                    open_tiles = [t for t in open_tiles if t not in nearby_tiles]
                    if not nearby_cities:
                        name = 'city'
                        self.board.add_city(tile1.x, tile1.y, name, civ, capital=True)
                        cities.append(name)
                i += 1

    def active_civ(self):
        return self.civs[self.active]

    def next_turn(self):
        self.turn += 1
        self.active += 1
        if self.active >= len(self.civs):
            self.active = 0

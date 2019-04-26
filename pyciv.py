#! /usr/bin/python

from argparse import ArgumentParser
import mapmaker
from render import RenderGame
from tile import City
import random

MAX_ITER = 1000
MIN_CITY_SEP = 4
CITIES_PER_CIV = 1

class Game(object):
    def __init__(self, shape, civs):
        self.shape = shape
        self.civs = civs
        self._init_map()
        self._init_cities()
        self.turn = 0

    def _init_map(self):
        self.board = mapmaker.make(self.shape)

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
                        dx = tile2.x - tile1.x
                        dy = tile2.y - tile1.y
                        adx = abs(dx)
                        ady = abs(dy)
                        if ((dx < 0) ^ ((tile1.y & 1) == 1)):
                            adx = max(0, adx - (ady + 1) / 2)
                        else:
                            adx = max(0, adx - (ady) / 2)
                        d = adx + ady
                        if d < MIN_CITY_SEP:
                            nearby_tiles.append(tile2)
                            if tile2.city:
                                nearby_cities = True
                    open_tiles = [t for t in open_tiles if t not in nearby_tiles]
                    if not nearby_cities:
                        name = 'city'
                        self.board.add_city(tile1.x, tile1.y, name, civ)
                        cities.append(name)
                i += 1

    def next_turn(self):
        self.turn += 1


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("board", nargs=2, type=int)
    parser.add_argument("--screen", nargs=2, type=int, default=(1280, 720))
    parser.add_argument("--rate", type=int, default=30)
    args = parser.parse_args()
    game = Game(args.board, civs=['France', 'England', 'America'])
    RenderGame(game, screen=args.screen, rate=args.rate).render()

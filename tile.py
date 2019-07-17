#! /usr/bin/python

import numpy as np

from bases import BASE_YIELDS, BASE_MOVES
from features import FEATURE_YIELDS, FEATURE_MOVES
from resources import RESOURCE_YIELDS
from buildings import Building

YIELD_TYPES = ['food', 'production', 'gold', 'culture', 'faith', 'science']


class TileYield(object):
    def __init__(self, **yields):
        for y in YIELD_TYPES:
            val = yields.get(y, 0)
            setattr(self, y, val)

    def __str__(self):
        s = ""
        d = {y: getattr(self, y, 0) for y in YIELD_TYPES}
        for y, val in self.__dict__.items():
            if val > 0:
                s += "{y}: {val}\n".format(y=y, val=val)
        return s

    def update(self, **d):
        for y, val in d.items():
            setattr(self, y, val)

    def add(self, **d):
        for y, val in d.items():
            old = getattr(self, y)
            setattr(self, y, old + val)

    def subtract(self, **d):
        for y, val in d.items():
            old = getattr(self, y)
            setattr(self, y, old - val)


class Tile(object):
    def __init__(self, x, y, base, features=[], civ=None):
        self.x = x
        self.y = y
        self.base = base
        self.features = []
        self.civ = civ

        # Add base and features
        self.set_base(base)
        for feature in features:
            self.add_feature(feature)

        # Initialize other stuff
        self.city = None
        self.improvements = []
        self.resources = []

    def set_base(self, base):
        self.base = base
        self.moves = BASE_MOVES[base]

    def add_feature(self, feature):
        if feature not in self.features:
            self.features.append(feature)
            self.moves += FEATURE_MOVES[feature]

    def has_feature(self, *features):
        return any(f in self.features for f in features)

    def remove_feature(self, feature):
        del self.features[self.features.index(feature)]
        self.moves -= FEATURE_MOVES[feature]

    def add_city(self, name, civ):
        self.city = City(self.x, self.y, name, civ)
        self.civ = civ
        self.features = []

    def remove_city(self):
        self.city = None

    def add_resource(self, resource):
        self.resources.append(resource)

    def remove_resource(self, resource):
        del self.resources[self.resources.index(resource)]

    @property
    def n_features(self):
        return len(self.features)

    def neighbor(self, n):
        if self.y % 2 != 0:
            dx = [0, 1, 1, 1, 0, -1]
            dy = [1, 1, 0, -1, -1, 0]
        else:
            dx = [-1, 0, 1, 0, -1, -1]
            dy = [1, 1, 0, -1, -1, 0]
        x = self.x + dx[n]
        y = self.y + dy[n]
        return x, y

    def set_civ(self, civ):
        self.civ = civ

    def __repr__(self):
        s = "<tile.Tile at ({x}, {y}), base={base}, n_features={n_features}>".format(**self.__dict__, n_features=self.n_features)
        return s

    @property
    def yields(self):
        out = {y: 0 for y in YIELD_TYPES}
        out.update(**BASE_YIELDS[self.base])
        for f in self.features:
            for y in YIELD_TYPES:
                out[y] += FEATURE_YIELDS[f].get(y, 0)
        for r in self.resources:
            for y in YIELD_TYPES:
                out[y] += RESOURCE_YIELDS[r].get(y, 0)
        if self.city:
            for y, val in out.items():
                if y == 'science':
                    val += self.city.p
                for b in self.city.buildings:
                    val += getattr(b, y, 0)
                    mod = y + '_modifier'
                    val *= getattr(b, mod, 1)
        return out

    def print_yields(self):
        s = ""
        for y, val in self.yields.items():
            if val > 0:
                s += "{y}: {val}\n".format(y=y, val=val)
        return s


class City(object):
    def __init__(self, x, y, name, civ, p=1, buildings=['palace']):
        self.x = x
        self.y = y
        self.name = name
        self.civ = civ
        self.p = p
        self._init_buildings(buildings)

    def _init_buildings(self, buildings=[]):
        self.buildings = []
        for b in buildings:
            self.buildings.append(Building(b))

    def grow(self, n=1):
        self.p += n

    @property
    def yields(self):
        out = {y: 0 for y in YIELD_TYPES}
        for y, val in out.items():
            mod = 1
            if y == 'science':
                val += self.p
            for b in self.buildings:
                val += getattr(b.yields, y, 0)
                mod += getattr(b.modifiers, y, 1)
            out[y] += val * mod
        return out


class TileArray(np.ndarray):
    def __new__(cls, shape=(1, 1)):
        new = super().__new__(cls, shape=shape, dtype=object)
        return new

    def set_tile(self, tile):
        self[tile.x, tile.y] = tile

    def fill(self, base):
        for x in range(self.shape[0]):
            for y in range(self.shape[1]):
                self.set_tile(Tile(x, y, base))

    def findall(self, base=None, feature=None):
        out = []
        for tile in self:
            if base and tile.base == base:
                out.append(tile)
            elif feature and tile.feature == feature:
                out.append(tile)
        return out

    def tiles(self):
        return [tile for tile in self]

    @property
    def n_tiles(self):
        return len([tile for tile in self if tile is not None])

    @property
    def n_land_tiles(self):
        out = 0
        for tile in self:
            if tile is not None:
                if tile.base not in ['ocean', 'lake']:
                    out += 1
        return out

    @property
    def equator(self):
        return self.shape[1] / 2.

    def get_neighbors(self, tile):
        out = []
        for i in range(6):
            new_x, new_y = tile.neighbor(i)
            if (
                    new_x >= 0 and
                    new_x < self.shape[0] and
                    new_y >= 0 and
                    new_y < self.shape[1]
            ):
                out.append(self[new_x, new_y])
        return out

    def search_neighbors(
            self, tile, include_bases=[], include_features=[],
            exclude_bases=[], exclude_features=[]):
        out = []
        for i in range(6):
            new_x, new_y = tile.neighbor(i)
            if (
                    new_x >= 0 and
                    new_x < self.shape[0] and
                    new_y >= 0 and
                    new_y < self.shape[1]
            ):
                if include_bases:
                    match_bases = (self[new_x, new_y].base in include_bases)
                elif exclude_bases:
                    match_bases = not (self[new_x, new_y].base in exclude_bases)
                else:
                    match_bases = True
                if include_features:
                    match_features = all(x in self[new_x, new_y].features for x in include_features)
                elif exclude_features:
                    match_features = not any(x in self[new_x, new_y].features for x in exclude_features)
                else:
                    match_features = True
                if match_bases and match_features:
                    out.append((new_x, new_y))
        return out

    def add_city(self, x, y, name, civ):
        tile = self[x, y]
        tile.add_city(name, civ)
        for neighbor in self.get_neighbors(tile):
            neighbor.set_civ(civ)

    def __iter__(self):
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                tile = self[i, j]
                if tile is not None:
                    yield tile

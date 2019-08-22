import numpy as np

from . import YIELD_TYPES
from .bases import BASE_YIELDS, BASE_MOVES
from .features import FEATURE_YIELDS, FEATURE_MOVES
from .resources import RESOURCE_YIELDS
from .improvements import IMPROVEMENT_YIELDS
from .buildings import Building
from .utils import neighbor


class Tile(object):
    def __init__(self, x, y, base, features=[]):
        self.x = x
        self.y = y
        self.base = base
        self.features = []

        # Add base and features
        self.set_base(base)
        for feature in features:
            self.add_feature(feature)

        # Initialize other stuff
        self.improvements = []
        self.resources = []

    @property
    def pos(self):
        return self.x, self.y

    def set_base(self, base):
        self.base = base
        self.moves = BASE_MOVES[base]

    def add_feature(self, feature):
        if feature not in self.features:
            self.features.append(feature)
            self.moves += FEATURE_MOVES[feature]

    def has_feature(self, *features):
        return any(f in self.features for f in features)

    def remove_features(self, *features):
        for feature in features:
            if feature in self.features:
                del self.features[self.features.index(feature)]
                self.moves -= FEATURE_MOVES[feature]

    def add_resource(self, resource):
        self.resources.append(resource)

    def remove_resource(self, resource):
        del self.resources[self.resources.index(resource)]

    def add_improvement(self, improvement):
        self.improvements.append(improvement)

    @property
    def n_features(self):
        return len(self.features)

    def neighbor(self, n, xmax):
        return neighbor(self.pos, n, xmax)

    def __repr__(self):
        s = "<tile.Tile at ({x}, {y}), base={base}, n_features={n_features}>".format(**self.__dict__, n_features=self.n_features)
        return s

    @property
    def yields(self):
        out = {y: 0 for y in YIELD_TYPES}
        out.update(**BASE_YIELDS[self.base])
        for y in YIELD_TYPES:
            for f in self.features:
                out[y] += FEATURE_YIELDS[f].get(y, 0)
            for r in self.resources:
                out[y] += RESOURCE_YIELDS[r].get(y, 0)
            for i in self.improvements:
                out[y] += IMPROVEMENT_YIELDS[i].get(y, 0)
            out[y] = max(0, out[y])
        return out

    def print_yields(self):
        s = ""
        for y, val in self.yields.items():
            if val > 0:
                s += "{y}: {val}\n".format(y=y, val=val)
        return s

    def attack_modifier(self):
        mod = 1
        if 'hill' in self.features:
            mod *= 1.25
        if 'mountain' in self.features:
            mod *= 1.5
        return mod

    def defense_modifier(self):
        mod = 1
        if self.base == 'ocean':
            mod /= 1.25
        if 'hill' in self.features:
            mod *= 1.25
        if 'mountain' in self.features:
            mod *= 1.5
        if 'forest' in self.features or 'rainforest' in self.features:
            mod *= 1.25
        if 'floodplain' in self.features:
            mod /= 1.25
        return mod


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

    def contains(self, pos):
        return (
            pos[0] >= 0 and
            pos[0] < self.shape[0] and
            pos[1] >= 0 and
            pos[1] < self.shape[1]
        )

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
            new_x, new_y = tile.neighbor(i, self.shape[0])
            if new_x < 0:
                new_x = self.shape[0] - 1
            elif new_x >= self.shape[0]:
                new_x = 0
            if new_y < 0:
                new_y = self.shape[1] - 1
            elif new_y >= self.shape[1]:
                new_y = 0
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

    def __iter__(self):
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                tile = self[i, j]
                if tile is not None:
                    yield tile

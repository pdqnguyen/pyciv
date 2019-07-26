from . import YIELD_TYPES
from .buildings import Building, BUILDINGS


class City(object):
    def __init__(self, tiles, name, civ, domain=[], pp=1, buildings=[], capital=False):
        self.tiles = tiles
        self.x = self.tiles[0].x
        self.y = self.tiles[1].y
        self.name = name
        self.civ = civ
        self.domain = domain
        self.pp = pp
        self.pp_progress = 0
        self.prod = None
        self.prod_progress = 0
        self._init_buildings(buildings=buildings, capital=capital)
        self.capital = capital

    def __iter__(self):
        for tile in self.tiles:
            yield tile

    def _init_buildings(self, buildings=[], capital=False):
        if capital and 'palace' not in buildings:
            buildings.append('palace')
        self.buildings = [Building(b) for b in buildings]

    def build(self, *args):
        for building in args:
            self.buildings.append(building)

    def grow(self, n=1):
        self.pp += n

    def begin_prod(self, building):
        print("Beginning production of " + building)
        self.prod = Building(building)
        self.prod_progress = 0

    def update_prod(self):
        self.prod_progress += self.yields['production']
        if self.prod:
            cost = self.prod.cost['production']
            if self.prod_progress > cost:
                self.build(self.prod)
                self.prod = None
                self.prod_progress -= max(self.prod_progress, cost)

    def prod_options(self):
        out = []
        for k, v in BUILDINGS.items():
            if not any(k == b.name for b in self.buildings):
                out.append(k)
        return out

    def update_pp(self):
        self.pp_progress += self.yields['food']
        while True:
            n = self.pp - 1
            cost = 15 + 8 * n + n ** 1.5
            if self.pp_progress > cost:
                self.grow(1)
                self.pp_progress -= cost
            else:
                break

    @property
    def yields(self):
        out = {y: 0 for y in YIELD_TYPES}
        for y in YIELD_TYPES:
            for tile in self:
                out[y] += tile.yields.get(y, 0)
        for y, val in out.items():
            mod = 1
            if y == 'science':
                val += self.pp
            for b in self.buildings:
                val += b.yields.get(y, 0)
                mod += b.modifiers.get(y, 1)
            out[y] += val * mod
        return out
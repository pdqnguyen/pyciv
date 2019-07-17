from . import YIELD_TYPES
from .buildings import Building


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
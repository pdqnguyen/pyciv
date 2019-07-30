from .city import City
from .units import create_unit
from . import YIELD_TYPES

CIV_COLORS = {
    'France': 'red',
    'America': 'blue',
    'England': 'crimson'
}

class Civilization(object):
    def __init__(self, name, leader):
        self.name = name
        self.leader = leader
        self.cities = []
        self.capital = None
        self.units = []
        self.science = 0
        self.culture = 0
        self.faith = 0
        self.gold = 0

    def __iter__(self):
        for city in self.cities:
            yield city

    @property
    def yields(self):
        out = {y: 0 for y in YIELD_TYPES}
        for y in YIELD_TYPES:
            for city in self:
                out[y] += city.yields.get(y, 0)
        return out

    @property
    def totals(self):
        out = {yd: getattr(self, yd, 0) for yd in YIELD_TYPES}
        out['population'] = sum(city.pp for city in self)
        return out

    def tiles(self):
        tiles = []
        for city in self:
            tiles += city.tiles
        return tiles

    def add_city(self, tiles, name, **kwargs):
        kwargs['civ'] = self.name
        tiles[0].remove_features(tiles[0].features)
        city = City(tiles, name, **kwargs)
        self.cities.append(city)
        if kwargs.get('capital', False):
            self.capital = city
        return city

    def add_unit(self, tile, name, unit_class, **kwargs):
        kwargs['pos'] = tile.pos
        kwargs['civ'] = self.name
        unit = create_unit(name, unit_class, **kwargs)
        self.units.append(unit)
        return unit

    def remove_unit(self, unit):
        del self.units[self.units.index(unit)]

    def update_totals(self, yields):
        self.science += yields['science']
        self.culture += yields['culture']
        self.faith += yields['faith']
        self.gold += yields['gold']
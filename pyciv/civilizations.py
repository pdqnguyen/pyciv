from .city import City
from .units import create_unit

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

    def __iter__(self):
        for city in self.cities:
            yield city

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

    def update(self):
        for city in self:
            city.update_prod()
            city.update_pp()
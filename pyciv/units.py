from . import utils as civutils
from .improvements import improvement_options

UNITS = {
    'settler': {
        'type': 'settler',
        'movement': 2,
        'cost': {
            'gold': 100,
            'production': 50
        }
    },
    'worker': {
        'type': 'worker',
        'movement': 2,
        'cost': {
            'gold': 50,
            'production': 30
        }
    },
    'warrior': {
        'type': 'combat',
        'movement': 2,
        'cost': {
            'gold': 30,
            'production': 20
        },
        'strength': 10
    }
}

def create_unit(name, unit_class, **kwargs):
    kwargs['_class'] = unit_class
    d = UNITS[unit_class].copy()
    unit_type = d.pop('type')
    kwargs.update(**d)
    cls_ = eval(unit_type[0].upper() + unit_type[1:].lower() + 'Unit')
    return cls_(name, **kwargs)


class Unit:
    def __init__(self, name, _class=None, pos=None, civ=None, movement=2, moves=2, cost=None):
        self.name = name
        self._class = _class
        self.pos = pos
        self.civ = civ
        self.movement = movement
        self.moves = moves
        self.cost = cost

    def move(self, new_pos, moves):
        self.pos = new_pos
        self.moves -= moves
        return

    def reset_moves(self):
        self.moves = self.movement

    def get_moves(self, game):
        out = []
        tiles_in_range = civutils.tiles_in_range(self.pos, 1, game.shape)
        for x, y in tiles_in_range:
            tile = game.board[x, y]
            if self.moves >= tile.moves:
                target_unit = game.get_unit(tile)
                target_city = game.get_city(tile)
                if not target_unit and not target_city:
                    out.append((x, y))
                elif target_unit:
                    if target_unit.civ == self.civ and target_unit._class != self._class:
                        out.append((x, y))
                elif target_city:
                    if target_city.civ == self.civ:
                        out.append((x, y))
        return out


class SettlerUnit(Unit):
    def __init__(self, name, **kwargs):
        super(SettlerUnit, self).__init__(name, **kwargs)

    def actions(self, game):
        out = (['move'] if self.get_moves(game) else [])
        nearby_tiles = civutils.neighbors(self.pos, game.board, r=3)
        if not any(game.get_city(tile) for tile in nearby_tiles):
            out.append('settle')
        return out


class WorkerUnit(Unit):
    def __init__(self, name, **kwargs):
        self.builds = kwargs.get('builds', 4)
        super(WorkerUnit, self).__init__(name, **kwargs)

    def actions(self, game):
        out = (['move'] if self.get_moves(game) else [])
        if self.moves == 0:
            return out
        tile = game.board[self.pos]
        civ = game.get_civ(tile)
        city = game.get_city(tile)
        civ_name = (civ.name if civ else '')
        if self.civ == civ_name and not city:
            if ('forest' in tile.features or 'rainforest' in tile.features) and 'lumber mill' not in tile.improvements:
                out.append('chop')
            out += improvement_options(tile)
        return out


class SupportUnit(Unit):
    def __init__(self, name, **kwargs):
        super(CivilianUnit, self).__init__(name, **kwargs)


class CombatUnit(Unit):
    def __init__(self, name, **kwargs):
        self.max_hp = kwargs.pop('max_hp', 100)
        self.hp = kwargs.pop('hp', 100)
        self.strength = kwargs.pop('strength', 10)
        super(CombatUnit, self).__init__(name, **kwargs)

    def actions(self, game):
        out = (['move'] if self.get_moves(game) else [])
        out += ['fortify']
        neighbors = civutils.neighbors(self.pos, game.board)
        for nb in neighbors:
            target_civ = getattr(game.get_unit(nb), 'civ', None)
            if target_civ is not None and target_civ != self.civ:
                out.append('melee')
        return out

    def get_targets(self, game):
        out = []
        tiles_in_range = civutils.tiles_in_range(self.pos, 1, game.shape)
        for x, y in tiles_in_range:
            tile = game.board[x, y]
            if self.moves >= tile.moves:
                target_unit = game.get_unit(tile)
                target_city = game.get_city(tile)
                if target_unit:
                    if target_unit.civ != self.civ:
                        out.append((x, y))
        return out

    def damage(self, dmg):
        self.hp -= dmg
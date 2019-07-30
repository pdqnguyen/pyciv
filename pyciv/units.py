from . import utils as civutils
from .improvements import improvement_options

UNITS = {
    'settler': {
        'type': 'settler',
        'movement': 2,
        'cost': {
            'gold': 100,
            'production': 1
        }
    },
    'worker': {
        'type': 'worker',
        'movement': 2,
        'cost': {
            'gold': 100,
            'production': 1
        }
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
    def __init__(self, name, _class=None, pos=None, civ=None, movement=2, cost=None):
        self.name = name
        self._class = _class
        self.pos = pos
        self.civ = civ
        self.max_hp = 100
        self.hp = 100
        self.movement = 10
        self.moves = 10
        self.cost = cost

    def move(self, new_pos, moves):
        self.pos = new_pos
        self.moves -= moves
        return

    def reset_moves(self):
        self.moves = self.movement


class CivilianUnit(Unit):
    def __init__(self, name, **kwargs):
        super(CivilianUnit, self).__init__(name, **kwargs)


class SettlerUnit(CivilianUnit):
    def __init__(self, name, **kwargs):
        super(SettlerUnit, self).__init__(name, **kwargs)

    def actions(self, game):
        out = (['Move'] if self.moves else [])
        nearby_tiles = civutils.tiles_in_range(self.pos, 3, game.shape[0])
        if not any(game.get_city(tile) for tile in nearby_tiles):
            out.append('Settle')
        return out

    def settle(self, game):
        game.settle(self)


class WorkerUnit(CivilianUnit):
    def __init__(self, name, **kwargs):
        super(WorkerUnit, self).__init__(name, **kwargs)

    def actions(self, game):
        out = (['Move'] if self.moves else [])
        tile = game.board[self.pos]
        civ = game.get_civ(tile)
        city = game.get_city(tile)
        civ_name = (civ.name if civ else '')
        if self.civ == civ_name and not city:
            if 'forest' in tile.features or 'rainforest' in tile.features:
                out.append('chop')
            else:
                out += improvement_options(tile)
        return out


class SupportUnit(Unit):
    def __init__(self, name, **kwargs):
        super(CivilianUnit, self).__init__(name, **kwargs)


class CombatUnit(Unit):
    def __init__(self, name, **kwargs):
        super(CombatUnit, self).__init__(name, **kwargs)
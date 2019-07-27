from . import utils as civutils

UNITS = {
    'settler': {
        'type': 'settler',
        'movement': 2,
    }
}

def create_unit(name, unit_class, **kwargs):
    kwargs['_class'] = unit_class
    unit_type = UNITS[unit_class]['type']
    cls_ = eval(unit_type[0].upper() + unit_type[1:].lower() + 'Unit')
    return cls_(name, **kwargs)

class Unit:
    def __init__(self, name, _class=None, pos=None, civ=None, movement=2):
        self.name = name
        self._class = _class
        self.pos = pos
        self.civ = civ
        self.max_hp = 100
        self.hp = 100
        self.movement = 10
        self.moves = 10

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
        self.actions = ['settle']

    def settle(self, game):
        game.add_city(game.board[self.pos], 'city' + civutils.random_str(8))
        del self

class SupportUnit(Unit):
    def __init__(self, name, **kwargs):
        super(CivilianUnit, self).__init__(name, **kwargs)

class CombatUnit(Unit):
    def __init__(self, name, **kwargs):
        super(CombatUnit, self).__init__(name, **kwargs)
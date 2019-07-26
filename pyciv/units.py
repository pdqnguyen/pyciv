class Unit:
    def __init__(self, name, _type=None, max_moves=2):
        self.name = name
        self.type = _type
        self.max_hp = 100
        self.hp = 100
        self.max_moves = 2
        self.moves = 2

class CivilianUnit(Unit):
    def __init__(self, name):
        super(CivilianUnit, self).__init__(self, name, type='civilian')

class CombatUnit(Unit):
    def __init__(self, name):
        super(CombatUnit, self).__init__(self, name, type='combat')
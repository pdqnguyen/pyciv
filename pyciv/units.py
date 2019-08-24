from . import utils as civutils
from .improvements import improvement_options

UNITS = {
    'settler': {
        'type': 'settler',
        'movement': 2,
        'cost': {
            'gold': 200,
            'production': 70
        }
    },
    'worker': {
        'type': 'worker',
        'movement': 2,
        'cost': {
            'gold': 200,
            'production': 70
        }
    },
    'warrior': {
        'type': 'combat',
        'movement': 2,
        'cost': {
            'gold': 160,
            'production': 60
        },
        'strength': 10,
        'attack': 'melee'
    },
    'archer': {
        'type': 'combat',
        'movement': 2,
        'cost': {
            'gold': 160,
            'production': 60
        },
        'strength': 7,
        'attack': 'range',
        'range': 2,
        'range_strength': 5
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
    def __init__(self, name, _class=None, pos=None, civ=None, movement=2, cost=None, **kwargs):
        self.name = name
        self._class = _class
        self._type = UNITS[self._class]['type']
        self.pos = pos
        self.civ = civ
        self.movement = movement
        self.moves = movement
        self.cost = cost
        for k, v in kwargs.items():
            setattr(self, k, v)

    def move(self, new_pos, moves):
        self.pos = new_pos
        self.moves -= moves
        return

    def reset_moves(self):
        self.moves = self.movement

    def get_moves(self, game):
        out = []
        neighbors = civutils.neighbors(self.pos, game.board, r=self.moves)
        for tile in neighbors:
            path, cost = civutils.find_best_path(self.pos, tile.pos, game)
            if cost <= self.moves:
                if self.moves >= tile.moves:
                    target_unit = game.get_unit(tile)
                    target_city = game.get_city(tile)
                    if not target_unit and not target_city:
                        out.append(tile)
                    elif target_unit:
                        if target_unit.civ == self.civ and target_unit._type != self._type:
                            out.append(tile)
                    elif target_city:
                        if target_city.civ == self.civ:
                            out.append(tile)
        return out


class SettlerUnit(Unit):
    def __init__(self, name, **kwargs):
        super(SettlerUnit, self).__init__(name, **kwargs)

    def actions(self, game):
        out = (['move'] if self.get_moves(game) else [])
        if self.moves > 0:
            nearby_tiles = civutils.neighbors(self.pos, game.board, r=3)
            if game.settler_score(self.pos, game.find_civ(self.civ)) > 0:
                out.append('settle')
        return out

    def def_strength(self, tile):
        return 0

    def end_turn(self, game):
        self.reset_moves()


class WorkerUnit(Unit):
    def __init__(self, name, **kwargs):
        self.builds = kwargs.get('builds', 4)
        super(WorkerUnit, self).__init__(name, **kwargs)

    def actions(self, game):
        out = (['move'] if self.get_moves(game) else [])
        if self.moves > 0:
            tile = game.board[self.pos]
            civ = game.get_civ(tile)
            city = game.get_city(tile)
            civ_name = (civ.name if civ else '')
            if self.civ == civ_name and not city:
                if ('forest' in tile.features or 'rainforest' in tile.features) and 'lumber mill' not in tile.improvements:
                    out.append('chop')
                out += improvement_options(tile)
        return out

    def def_strength(self, tile):
        return 0

    def end_turn(self, game):
        self.reset_moves()


class SupportUnit(Unit):
    def __init__(self, name, **kwargs):
        super(CivilianUnit, self).__init__(name, **kwargs)


class CombatUnit(Unit):
    def __init__(self, name, **kwargs):
        self.max_hp = kwargs.pop('max_hp', 100)
        self.hp = kwargs.pop('hp', 100)
        self.exp = 0
        self.level = 1
        self.fortified = kwargs.pop('fortified', False)
        super(CombatUnit, self).__init__(name, **kwargs)

    def atk_strength(self, tile):
        if self.attack == 'melee':
            out = self.strength
        elif self.attack == 'range':
            out = self.range_strength
        out *= civutils.level_modifier(self.level)
        out *= tile.attack_modifier()
        return out

    def def_strength(self, tile):
        out = self.strength
        out *= civutils.level_modifier(self.level)
        out *= tile.defense_modifier()
        if self.fortified:
            out *= 1.5
        return out

    def actions(self, game):
        out = (['move'] if self.get_moves(game) else [])
        if self.moves == 0:
            return out
        if not self.fortified:
            out.append('fortify')
        if self.get_targets(game):
            out.append(self.attack + ' attack')
        return out

    def get_targets(self, game):
        out = []
        range_ = getattr(self, 'range', 1)
        for tile in civutils.neighbors(self.pos, game.board, range_):
            if not (self.attack == 'melee' and self.moves < tile.moves):
                target_unit = game.get_unit(tile)
                target_city = game.get_city(tile)
                if game.get_unit(tile):
                    target_civ = getattr(game.get_unit(tile), 'civ', None)
                elif game.get_city(tile):
                    target_civ = getattr(game.get_city(tile), 'civ', None)
                else:
                    target_civ = None
                if target_civ is not None and target_civ != self.civ:
                    out.append(tile)
        return out

    def damage(self, dmg):
        self.hp -= int(dmg)

    def fortify(self):
        self.moves = 0
        self.fortified = True

    def unfortify(self):
        self.fortified = False

    def end_turn(self, game):
        self.reset_moves()
        if self.fortified:
            civ = game.get_civ(game.board[self.pos])
            if getattr(civ, 'name', None) == self.civ:
                self.update_hp(30)
            else:
                self.update_hp(10)

    def update_hp(self, hp=10):
        if self.hp < 100:
            self.hp = min(100, self.hp + int(hp))

    def update_exp(self, exp=1):
        self.exp += int(exp)
        cost = civutils.level_cost(self.level)
        if self.exp >= cost:
            print("{} leveled up".format(self.name))
            self.exp = 0
            self.level += 1
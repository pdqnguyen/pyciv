import random
import string
from math import *


def tiles_in_range(pos, r, shape):
    out = [pos]
    seeds = out[:]
    for _ in range(r):
        new_out = []
        for seed in seeds:
            for n in range(6):
                nb = neighbor(seed, n, shape[0] - 1)
                if (nb[1] < shape[1]) and (nb not in out):
                    new_out.append(nb)
        out += new_out
        seeds = new_out[:]
    return out


def neighbor(pos, n, xmax):
    if pos[1] % 2 != 0:
        dx = [0, 1, 1, 1, 0, -1]
        dy = [1, 1, 0, -1, -1, 0]
    else:
        dx = [-1, 0, 1, 0, -1, -1]
        dy = [1, 1, 0, -1, -1, 0]
    x = pos[0] + dx[n]
    if x > xmax:
        x -= xmax + 1
    elif x < 0:
        x += xmax + 1
    y = pos[1] + dy[n]
    return x, y


def neighbors(pos, board, r=1):
    return [board[x, y] for x, y in tiles_in_range(pos, r, board.shape) if (x, y) != pos]


def distance(pos1, pos2, xmax):
    x1, y1 = pos1
    x2, y2 = pos2
    dx1 = x2 - x1
    dx2 = x2 - (x1 + xmax)
    dx = (dx1 if abs(dx1) < abs(dx2) else dx2)
    dy = y2 - y1
    adx = abs(dx)
    ady = abs(dy)
    if ((dx < 0) ^ ((y1 & 1) == 1)):
        adx = max(0, adx - (ady + 1) / 2)
    else:
        adx = max(0, adx - (ady) / 2)
    d = ceil(adx + ady)
    return d


def pp_cost(pp):
    n = pp - 1
    return (15 + 8 * n + n ** 1.5)


def tile_cost(ntiles):
    return (10 + (6 * (ntiles - 7)) ** 1.3)


def level_cost(level):
    return round(10 * sqrt(level))


def level_modifier(level):
    return 1. + 0.5 * (level - 1)


def calc_unit_damage(unit1, unit2, unit1_tile, unit2_tile, attack):
    return calc_damage(unit1.atk_strength(unit1_tile), unit2.def_strength(unit2_tile), attack)


def calc_city_damage(unit, city, unit_tile, city_tile, attack, garrison=None):
    def_strength = city.def_strength(city_tile)
    if garrison:
        if garrison._type == 'combat':
            def_strength += garrison.def_strength(city_tile)
    return calc_damage(unit.atk_strength(unit_tile), def_strength, attack)


def calc_damage(strength1, strength2, attack):
    strength_diff = strength1 - strength2
    strength_diff = min(100, max(-100, strength_diff))
    atk_dmg = 30 * 1.041 ** (strength_diff) #* random.uniform(0.75, 1.25)
    if attack == 'melee attack':
        def_dmg = 30 * 1.041 ** (-strength_diff) #* random.uniform(0.75, 1.25)
    elif attack == 'range attack':
        def_dmg = 0
    atk_dmg = min(100, int(atk_dmg))
    def_dmg = min(100, int(def_dmg))
    return atk_dmg, def_dmg


def random_str(n):
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(n)])
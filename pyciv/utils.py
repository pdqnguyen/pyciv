import random
import string
import math
import multiprocessing as mp
import numpy as np
from queue import PriorityQueue


NEIGHBOR_DX = {
    0: [-1, 0, 1, 0, -1, -1],
    1: [0, 1, 1, 1, 0, -1]
}
NEIGHBOR_DY = [1, 1, 0, -1, -1, 0]


class Action:

    def __init__(self, name, city=None, unit=None, target=None):
        self.name = name
        self.city = city
        self.unit = unit
        self.target = target


def tiles_in_range(pos, r, shape):
    out = []
    seeds = [pos]
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
    x = pos[0] + NEIGHBOR_DX[pos[1] % 2][n]
    if x > xmax:
        x -= xmax + 1
    elif x < 0:
        x += xmax + 1
    y = pos[1] + NEIGHBOR_DY[n]
    return x, y


def neighbors(pos, board, r=1):
    shape = board.shape
    out = []
    seeds = [board[pos]]
    for _ in range(r):
        new_out = []
        for seed in seeds:
            for n in range(6):
                x, y = neighbor(seed.pos, n, shape[0] - 1)
                if y < shape[1]:
                    tile = board[x, y]
                    if (tile not in out):
                        new_out.append(tile)
        out += new_out
        seeds = new_out[:]
    return out


def create_path(start, end, xmax, wrap=False, max_iter=100):
    if wrap:
        if end[0] < start[0]:
            end = (end[0] + (xmax + 1), end[1])
        else:
            start = (start[0] + (xmax + 1), start[1])
    path = [start]
    i = 0
    while path[-1] != end and i < max_iter:
        start = path[-1]
        dy = end[1] - start[1]
        if dy % 2 == 0:
            dx = end[0] - start[0]
        elif start[1] % 2 != 0:
            dx = end[0] - 0.5 - start[0]
        else:
            dx = end[0] +  0.5 - start[0]
        angle = math.atan2(dy, dx)
        n = int(-(angle - 5 * math.pi / 6) * 3 / math.pi % 6)
        if wrap:
            path.append(neighbor(start, n, xmax * 2))
        else:
            path.append(neighbor(start, n, xmax))
        i += 1
    if wrap:
        path_wrapped = []
        for x, y in path:
            if x > xmax:
                path_wrapped.append((x - (xmax + 1), y))
            else:
                path_wrapped.append((x, y))
        path = path_wrapped
    return path


def calc_path_moves(path, board):
    return sum(board[p].moves for p in path[1:])


def find_best_path(start, goal, game):
    unit = game.get_unit(game.board[start])
    class PriorityEntry(object):
        def __init__(self, priority, data):
            self.data = data
            self.priority = priority
        def __lt__(self, other):
            return self.priority < other.priority
    frontier = PriorityQueue()
    frontier.put(PriorityEntry(0, start))
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    while not frontier.empty():
        current = frontier.get()
        if current.data == goal:
            break
        for i in range(6):
            nb = neighbor(current.data, i, game.board.shape[0] - 1)
            if game.board.contains(nb):
                nb_cost = game.board[nb].moves
                nb_unit = game.get_unit(game.board[nb])
                if unit is not None and nb_unit is not None:
                    if unit.civ != nb_unit.civ or unit._type == nb_unit._type:
                        nb_cost += 100
                new_cost = cost_so_far[current.data] + nb_cost
                if nb not in cost_so_far or new_cost < cost_so_far[nb]:
                    cost_so_far[nb] = new_cost
                    priority = new_cost
                    frontier.put(PriorityEntry(new_cost, nb))
                    came_from[nb] = current.data
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path = path[::-1]
    return path, cost_so_far


def distance(pos1, pos2, xsize):
    x1, y1 = pos1
    x2, y2 = pos2
    dx1 = x2 - x1
    dx2 = x2 - (x1 + xsize)
    dx3 = (x2 + xsize) - x1
    dx = min([dx1, dx2, dx3], key=abs)
    dy = y2 - y1
    adx = abs(dx)
    ady = abs(dy)
    if ((dx < 0) ^ ((y1 & 1) == 1)):
        adx = max(0, adx - (ady + 1) / 2)
    else:
        adx = max(0, adx - (ady) / 2)
    d = math.ceil(adx + ady)
    return d


def pp_cost(pp):
    n = pp - 1
    return (15 + 3 * n + n ** 1.3)


def tile_cost(ntiles):
    return (10 + (6 * (ntiles - 7)) ** 1.3)


def level_cost(level):
    return round(10 * math.sqrt(level))


def level_modifier(level):
    return 1. + 0.2 * (level - 1)


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
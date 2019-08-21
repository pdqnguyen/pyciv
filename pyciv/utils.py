import random
import string
import math
import multiprocessing as mp
import numpy as np


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


def perturb_path(path, board, forward=True):
    xmax = board.shape[0] - 1
    ymax = board.shape[1] - 1
    weights = np.array([board[p].moves for p in path[1:]]).astype(float)
    weights /= weights.sum()
    i = np.random.choice(range(1, len(path)), p=weights)
    nbs = []
    for j in range(6):
        nb = neighbor(path[i - 1], j, xmax)
        if nb not in path and nb[1] <= ymax:
            nb_nbs = [neighbor(nb, k, xmax) for k in range(6)]
            if not (nb in nb_nbs and path[i - 1] in nb_nbs):
                nbs.append(nb)
    if nbs:
        weights = np.array([1 / board[nb].moves for nb in nbs])
        weights /= weights.sum()
        new_tile = nbs[np.random.choice(range(len(nbs)), p=weights)]
        if path[-1] == (6, 2):
            print(path[i - 1], nbs, nb)
        if forward:
            segment1 = create_path(new_tile, path[-1], xmax)
            segment2 = create_path(new_tile, path[-1], xmax, wrap=True)
            segment = min((segment1, segment2), key=lambda x: calc_path_moves(x, board))
            new_path = path[:i] + segment
        else:
            segment1 = create_path(path[0], new_tile, xmax)
            segment2 = create_path(path[0], new_tile, xmax, wrap=True)
            segment = min((segment1, segment2), key=lambda x: calc_path_moves(x, board))
            new_path = segment + path[i - 1:]
        return new_path


def find_best_path(start, end, board, max_iter=300):
    xmax = board.shape[0] - 1
    ymax = board.shape[1] - 1
    path1 = create_path(start, end, xmax)
    path2 = create_path(start, end, xmax, wrap=True)
    if len(path1) < 3:
        return path1
    elif len(path2) < 3:
        return path2
    paths1 = [path1]
    paths2 = [path2]
    moves1 = [calc_path_moves(path1, board)]
    moves2 = [calc_path_moves(path2, board)]
    for _ in range(max_iter):
        for paths in [paths1, paths2]:
#         for paths, moves in zip([paths1, paths2], [moves1, moves2]):
#             weights = np.array([1. / calc_path_moves(path, board) for path in paths])
#             weights /= weights.sum()
#             path = paths[np.random.choice(range(len(paths)), p=weights)]
            path = random.choice(paths)
            for forward in [True, False]:
                new_path = perturb_path(path, board, forward=forward)
                if new_path:
                    paths.append(new_path)
#                     moves.append(calc_path_moves(new_path, board))
#         if max_iter % 100:
#             min_moves = min(moves1 + moves2)
#             idx1 = np.flatnonzero(moves1 < 1.5 * min_moves)
#             idx2 = np.flatnonzero(moves2 < 1.5 * min_moves)
#             paths1 = [paths1[i] for i in idx1]
#             paths2 = [paths2[i] for i in idx2]
#             moves1 = [moves1[i] for i in idx1]
#             moves2 = [moves2[i] for i in idx2]
    best_path = min(paths1 + paths2, key=lambda x: calc_path_moves(x, board))
    return best_path


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
    return (15 + 8 * n + n ** 1.5)


def tile_cost(ntiles):
    return (10 + (6 * (ntiles - 7)) ** 1.3)


def level_cost(level):
    return round(10 * math.sqrt(level))


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
import random
import string
from math import ceil


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


def random_str(n):
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(n)])
from math import ceil

def distance(tile1, tile2, xmax):
    dx1 = tile2.x - tile1.x
    dx2 = tile2.x - (tile1.x + xmax)
    dx = (dx1 if abs(dx1) < abs(dx2) else dx2)
    dy = tile2.y - tile1.y
    adx = abs(dx)
    ady = abs(dy)
    if ((dx < 0) ^ ((tile1.y & 1) == 1)):
        adx = max(0, adx - (ady + 1) / 2)
    else:
        adx = max(0, adx - (ady) / 2)
    d = ceil(adx + ady)
    return d
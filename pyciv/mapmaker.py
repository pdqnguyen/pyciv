#! /usr/bin/python

import numpy as np
import random
from configparser import ConfigParser

from .tile import Tile, TileArray
from .features import FEATURES

MAP_CONFIG_FILE = 'map.ini'


MAX_ITER = 10000


def get_config(map_config_file=MAP_CONFIG_FILE):
    config = ConfigParser()
    config.read(map_config_file)
    base_config = {}
    feature_config = {}
    for section in config.sections():
        sub_dict = {}
        for name, value in config.items(section):
            try:
                sub_dict[name] = int(value)
            except ValueError:
                try:
                    sub_dict[name] = float(value)
                except ValueError:
                    sub_dict[name] = value
        if section == 'base':
            base_config = sub_dict
        else:
            feature_config[section] = sub_dict
    return base_config, feature_config


def generate_base(y, board):
    dist = abs((y - board.equator) / board.equator)
    dist = random.normalvariate(dist, 0.05)
    if dist < 0.1:
        base = 'grassland'
    elif 0.1 <= dist < 0.3:
        base = 'plains'
    elif 0.3 <= dist < 0.5:
        base = 'desert'
    elif 0.5 <= dist < 0.7:
        base = 'plains'
    else:
        base = 'tundra'
    return base


def get_tiles_for_landmass(tiles):
    out = [
        t for t in tiles if (
            t.base == 'ocean' and
            not t.features)
    ]
    return out


def get_tiles_for_mountain(tiles):
    out = [
        t for t in tiles if (
            t.base != 'ocean' and
            t.base != 'grassland' and
            not t.features)
    ]
    return out


def get_tiles_for_hill(tiles):
    out = [
        t for t in tiles if (
            t.base != 'ocean' and
            not t.features)
    ]
    return out


def get_tiles_for_forest(tiles):
    exclude_features = ['mountain', 'rainforest', 'ice', 'snow']
    out = [
        t for t in tiles if (
            t.base != 'ocean' and
            t.base != 'desert' and
            not t.has_feature(*exclude_features))
    ]
    return out


def get_tiles_for_rainforest(tiles):
    exclude_features = ['mountain', 'forest', 'ice', 'snow']
    out = [
        t for t in tiles if (
            t.base != 'ocean' and
            t.base != 'desert' and
            t.base != 'tundra' and
            not t.has_feature(*exclude_features))
    ]
    return out


def get_tiles_for_snow(tiles):
    exclude_features = ['rainforest', 'ice']
    out = [
        t for t in tiles if (
            t.base == 'tundra' and
            not t.has_feature(*exclude_features))
    ]
    return out


def build_landmass(
        board,
        size,
        stretch=0
):
    tiles = get_tiles_for_landmass(board.tiles())
    if len(tiles) == 0:
        return
    random.shuffle(tiles)
    seed = tiles.pop(0)
    base = generate_base(seed.y, board)
    seed.set_base(base)
    out = [seed]
    j = 0
    while len(out) < size and j < MAX_ITER:
        if random.random() < stretch:
            tile = out[-1]
        else:
            tile = random.choice(out)
        neighbors = get_tiles_for_landmass(
            board.get_neighbors(tile))
        if neighbors:
            new = random.choice(neighbors)
            base = generate_base(new.y, board)
            new.set_base(base)
            out.append(new)
        j += 1
    return out


def build_coastline(board, landmass, max_coast_width=1, coast_density=1):
    coasts = []
    for tile in landmass:
        neighbors = get_tiles_for_landmass(
            board.get_neighbors(tile))
        for neighbor in neighbors:
            neighbor.add_feature('coast')
            coasts.append(neighbor)
    for _ in range(max_coast_width):
        new_coasts = []
        for tile in coasts:
            neighbors = get_tiles_for_landmass(
                board.get_neighbors(tile))
            for neighbor in neighbors:
                if random.random() < coast_density:
                    neighbor.add_feature('coast')
                    new_coasts.append(neighbor)
        coasts += new_coasts
    return coasts


def build_icecaps(board, max_ice_width=1, ice_density=1):
    ice = []
    for tile in board:
        if tile.y == 0 or tile.y == board.shape[1] - 1:
            tile.add_feature('ice')
            ice.append(tile)
    # Ice sheet extension
    for _ in range(max_ice_width):
        new_ice = []
        for tile in ice:
            neighbors = [n for n in board.get_neighbors(tile) if n.base != 'ice']
            for neighbor in neighbors:
                if random.random() < ice_density:
                    neighbor.add_feature('ice')
                    new_ice.append(neighbor)
        ice += new_ice
    return ice


def build_feature(board, feature, size, stretch=0):
    tile_func = eval('get_tiles_for_' + feature)
    tiles = tile_func(board.tiles())
    if len(tiles) == 0:
        return
    random.shuffle(tiles)
    seed = tiles.pop(0)
    seed.add_feature(feature)
    out = [seed]
    for _ in range(MAX_ITER):
        if random.random() < stretch:
            tile = out[-1]
        else:
            tile = random.choice(out)
        neighbors = tile_func(
            board.get_neighbors(tile))
        if neighbors:
            neighbor = random.choice(neighbors)
            neighbor.add_feature(feature)
            out.append(neighbor)
        if len(out) >= size:
            break
    return out


def make(shape, map_config_file=None):
    if map_config_file is None:
        map_config_file = MAP_CONFIG_FILE
    base_config, feature_config = get_config(map_config_file=map_config_file)
    board = TileArray(shape=shape)
    board.fill('ocean')
    conts = []
    isls = []
    avg_num_continents = base_config['avg_num_continents']
    std_num_continents = base_config['std_num_continents']
    avg_num_islands = base_config['avg_num_islands']
    std_num_islands = base_config['std_num_islands']
    if std_num_continents > 0:
        n_conts = random.normalvariate(avg_num_continents, std_num_continents)
        n_conts = max(2, int(round(n_conts)))
    else:
        n_conts = avg_num_continents
    n_isls = random.normalvariate(avg_num_islands, std_num_islands)
    n_isls = int(round(n_isls))
    avg_cont_size = int(base_config['land_ratio'] * board.size / n_conts)
    std_cont_size = std_num_continents * avg_cont_size
    min_cont_size = int(0.1 * avg_cont_size)
    for _ in range(MAX_ITER):
        cont_size = random.normalvariate(
            avg_cont_size, std_cont_size)
        cont_size = max(min_cont_size, cont_size)
        cont = build_landmass(board, cont_size, stretch=base_config['continent_stretch'])
        build_coastline(board, cont)
        if len(cont) >= min_cont_size:
            conts.append(cont)
        else:
            isls.append(cont)
        if len(conts) >= n_conts:
            break
    for _ in range(MAX_ITER):
        isl_size = random.randint(1, min_cont_size - 1)
        isl = build_landmass(board, isl_size, stretch=base_config['island_stretch'])
        build_coastline(
            board,
            isl,
            max_coast_width=base_config['max_coast_width'],
            coast_density=base_config['coast_density'])
        isls.append(isl)
        if len(isls) >= n_isls:
            break
    build_icecaps(
        board,
        max_ice_width=base_config['max_ice_width'],
        ice_density=base_config['ice_density'])
    n_land = len([t for t in board if t.base != 'ocean'])
    for feature, d in feature_config.items():
        n_tiles = int(d['coverage'] * n_land)
        tiles = []
        avg_group_size = int(d['group'] * n_tiles / n_conts)
        std_group_size = avg_group_size
        for _ in range(MAX_ITER):
            group_size = random.normalvariate(avg_group_size, std_group_size)
            group = build_feature(
                board,
                feature,
                group_size,
                stretch=d['stretch'])
            tiles += group
            if len(tiles) >= n_tiles:
                break
    return board

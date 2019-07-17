#! /usr/bin/python

BASES = ['ocean', 'lake', 'desert', 'tundra', 'plains', 'grassland']

BASE_YIELDS = {
    'ocean': {
        'food': 1
    },
    'lake': {
        'food': 1
    },
    'desert': {
        'food': 1
    },
    'tundra': {
        'food': 1
    },
    'plains': {
        'food': 2,
        'production': 1
    },
    'grassland': {
        'food': 3
    }
}

BASE_MOVES = {
    'ocean': 2,
    'lake': 2,
    'desert': 1,
    'tundra': 1,
    'plains': 1,
    'grassland': 1
}

BASE_COLORS = {
    'ocean': 'blue',
    'lake': 'aquamarine',
    'desert': 'beige',
    'tundra': 'gray',
    'plains': 'goldenrod',
    'grassland': 'green'
}

BASE_FEATURES = {
    'ocean': ['coast'],
    'lake': ['coast'],
    'desert': ['floodplain', 'hill', 'mountain'],
    'tundra': ['hill', 'mountain', 'forest', 'snow', 'ice'],
    'plains': ['hill', 'mountain', 'forest', 'rainforest', 'snow'],
    'grassland': ['hill', 'forest', 'rainforest', 'snow']
}

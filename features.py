#! /usr/bin/python

FEATURES = ['coast', 'floodplain', 'hill', 'mountain', 'forest', 'rainforest', 'snow', 'ice']

FEATURE_YIELDS = {
    'coast': {
        'food': 2
    },
    'floodplain' : {
        'food': 3,
    },
    'hill': {
        'production': 1
    },
    'mountain': {
        'food': -2,
        'production': 1,
        'faith': 1
    },
    'forest': {
        'food': 1,
        'production': 2,
    },
    'rainforest': {
        'food': 2,
        'production': 1,
    },
    'snow': {
        'food': -1,
        'production': -1
    },
    'ice': {
        'food': -2,
        'production': -2
    }
}

FEATURE_MOVES = {
    'coast': 0,
    'floodplain': 1,
    'hill': 1,
    'mountain': 10,
    'forest': 1,
    'rainforest': 1,
    'snow': 1,
    'ice': 10
}

FEATURE_COLORS = {
    'coast': 'royalblue',
    'floodplain': 'springgreen',
    'hill': 'tan',
    'mountain': 'black',
    'forest': 'darkgreen',
    'rainforest': 'yellowgreen',
    'snow': 'white',
    'ice': 'lightsteelblue'
}

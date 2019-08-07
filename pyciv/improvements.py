from .resources import RESOURCE_IMPROVEMENTS

IMPROVEMENTS = ['farm', 'mine', 'pasture', 'lumber mill']

IMPROVEMENT_YIELDS = {
    'farm': {
        'food': 2
    },
    'mine' : {
        'production': 2
    },
    'pasture': {
        'food': 1,
        'production': 1,
    },
    'lumber mill': {
        'production': 2,
    },
    'plantation': {
        'food': 1,
        'gold': 1
    }
}

IMPROVEMENT_BASES = {
    'farm': ['plains', 'grassland'],
    'mine': ['plains', 'grassland', 'desert', 'tundra'],
    'pasture': ['plains', 'grassland', 'desert', 'tundra'],
    'lumber mill': ['plains', 'grassland', 'desert', 'tundra']
}

IMPROVEMENT_FEATURES = {
    'farm': [None, 'floodplain', 'hill'],
    'mine': ['hill', 'mountain'],
    'lumber mill': ['forest', 'rainforest'],
    'plantation': [None]
}


def improvement_options(tile):
    if tile.improvements:
        return []
    out = []
    base = tile.base
    features = tile.features
    resources = tile.resources
    if resources:
        if ('forest' not in features) and ('rainforest' not in features):
            out += [RESOURCE_IMPROVEMENTS[res] for res in resources]
    if base in ['plains', 'grassland']:
        if (not features) or features == ['floodplain'] or features == ['hill']:
            out.append('farm')
    if base in ['plains', 'grassland', 'desert', 'tundra']:
        if ('forest' in features) or ('rainforest' in features):
            out.append('lumber mill')
        elif ('hill' in features) or ('mountain' in features):
            out.append('mine')
    return sorted(set(out))
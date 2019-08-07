RESOURCES = ['wheat', 'horse', 'iron', 'cattle', 'sheep', 'bananas']

RESOURCE_YIELDS = {
    'wheat': {
        'food': 1
    },
    'horse': {
        'production': 1
    },
    'iron': {
        'production': 1
    },
    'cattle': {
        'food': 1
    },
    'sheep': {
        'food': 1
    },
    'bananas': {
        'food': 1
    }
}

RESOURCE_BASES = {
    'wheat': ['plains', 'grassland', 'desert'],
    'horse': ['plains', 'grassland', 'desert'],
    'iron': ['plains', 'grassland', 'desert'],
    'cattle': ['plains', 'grassland', 'desert'],
    'sheep': ['plains', 'grassland', 'desert'],
    'bananas': ['plains', 'grassland']
}

RESOURCE_FEATURES = {
    'wheat': [None, 'floodplains', 'hill'],
    'horse': [None, 'hill'],
    'iron': [None, 'hill'],
    'cattle': [None, 'hill'],
    'sheep': [None, 'hill'],
    'bananas': ['rainforest']
}

RESOURCE_IMPROVEMENTS = {
    'wheat': 'farm',
    'horse': 'pasture',
    'iron': 'mine',
    'cattle': 'pasture',
    'sheep': 'pasture',
    'bananas': 'plantation'
}

def resource_options(tile):
    out = []
    if tile.resources:
        return out
    else:
        for res in RESOURCES:
            bases = RESOURCE_BASES.get(res, [])
            features = RESOURCE_FEATURES.get(res, [])
            if tile.base in bases:
                if None in features and not tile.features:
                    out.append(res)
                elif any(f in features for f in tile.features) and not any(f not in features for f in tile.features):
                    out.append(res)
        return out
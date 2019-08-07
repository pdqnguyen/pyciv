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
    'pasture': [None, 'hill'],
    'lumber mill': ['forest', 'rainforest']
}


def improvement_options(tile):
    out = []
    if tile.improvements:
        return out
    elif tile.resources:
        for resource in tile.resources:
            imp = RESOURCE_IMPROVEMENTS[resource]
            if imp not in out:
                out.append(imp)
        return out
    else:
        for imp in IMPROVEMENTS:
            bases = IMPROVEMENT_BASES[imp]
            features = IMPROVEMENT_FEATURES[imp]
            if tile.base in bases:
                if None in features and not tile.features:
                    out.append(imp)
                elif any(f in features for f in tile.features):
                    out.append(imp)
        return out
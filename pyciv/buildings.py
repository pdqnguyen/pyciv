#! /usr/bin/python

BUILDINGS = {
    'palace': {
        'yields': {
            'production': 1,
            'gold': 1,
            'culture': 1
        },
        'modifiers': {},
        'cost': {}
    },
    'monument': {
        'yields': {
            'culture': 2
        },
        'modifiers': {},
        'cost': {
            'production': 30,
            'cost': 100
        }
    }
}


class Building(object):
    def __init__(self, name):
        self.name = name
        d = BUILDINGS[name]
        self.yields = d['yields']
        self.modifiers = d['modifiers']
        self.cost = d['cost']

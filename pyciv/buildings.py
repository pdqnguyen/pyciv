#! /usr/bin/python

BUILDINGS = {
    'palace': {
        'yields': {
            'production': 1,
            'gold': 1,
            'culture': 1
        },
        'modifiers': {},
        'cost': {
            'production': 0,
            'cost': 0
        },
        'require': {}
    },
    'monument': {
        'yields': {
            'culture': 2
        },
        'modifiers': {},
        'cost': {
            'production': 30,
            'cost': 100
        },
        'require': {}
    },
    'shrine': {
        'yields': {
            'faith': 2
        },
        'modifiers': {},
        'cost': {
            'production': 30,
            'cost': 100
        },
        'require': {}
    },
    'granary': {
        'yields': {
            'food': 2
        },
        'modifiers': {
            'food': 1.1
        },
        'cost': {
            'production': 50,
            'cost': 130
        },
        'require': {}
    }
}


class Building(object):
    def __init__(self, name):
        self.name = name
        d = BUILDINGS[name]
        self.yields = d['yields']
        self.modifiers = d['modifiers']
        self.cost = d['cost']

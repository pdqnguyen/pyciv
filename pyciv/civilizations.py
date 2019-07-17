#! /usr/bin/python

CIV_COLORS = {
    'France': 'red',
    'America': 'blue',
    'England': 'crimson'
}

class Civilization(object):
    def __init__(self, name, leader):
        self.name = name
        self.leader = leader
"""This module is to define the seeded soldiers and warband members for the ledger on creation. Any new members
should be added to this module.
"""

SOLDIER_TYPES = {
    "thug" : {
        "move": 7, "fight": 1, "shoot": 0, "armour": 10, "will": 0, "health": 10, "items" : ["dagger"], "hire_cost": 20,
    },
    "archer" : {
        "move": 6, "fight": 1, "shoot": 2, "armour": 11, "will": 0, "health": 10, "items" : ["dagger", "bow", "quiver", "light_armour"], "hire_cost": 25,
    },
    "thief" : {
        "move": 7, "fight": 1, "shoot": 0, "armour": 10, "will": 0, "health": 10, "items" : ["dagger"], "hire_cost": 20, 
    },
    "infantryman" : {
        "move": 7, "fight": 1, "shoot": 0, "armour": 10, "will": 0, "health": 10, "items" : ["dagger"], "hire_cost": 20,
    },
}
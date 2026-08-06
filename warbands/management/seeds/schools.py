"""This module is to define the school alignments for the ledger on creation. Any new alignments
should be added to this module.
"""
from enum import IntEnum

class alignment(IntEnum):
    ALIGNED = 2
    NEUTRAL = 4
    OPPOSED = 6
    
SCHOOL_ALIGNMENTS = {
    "chronomancer": {
        "elementalist": alignment.ALIGNED, 
        "enchanter": alignment.OPPOSED, 
        "illusionist": alignment.NEUTRAL, 
        "necromancer": alignment.ALIGNED,
        "sigilist": alignment.NEUTRAL, 
        "thaumaturge": alignment.NEUTRAL,
        "witch": alignment.NEUTRAL,
        "soothsayer": alignment.ALIGNED,
        "summoner": alignment.NEUTRAL,
    },
    "elementalist": {
        "chronomancer": alignment.ALIGNED, 
        "enchanter": alignment.ALIGNED, 
        "illusionist": alignment.OPPOSED, 
        "necromancer": alignment.NEUTRAL,
        "sigilist": alignment.NEUTRAL, 
        "thaumaturge": alignment.NEUTRAL, 
        "witch": alignment.NEUTRAL, 
        "soothsayer": alignment.NEUTRAL, 
        "summoner": alignment.ALIGNED,
    },
    "enchanter": {
        "chronomancer": alignment.OPPOSED, 
        "elementalist": alignment.ALIGNED, 
        "illusionist": alignment.NEUTRAL, 
        "necromancer": alignment.NEUTRAL,
        "sigilist": alignment.ALIGNED, 
        "thaumaturge": alignment.NEUTRAL, 
        "witch": alignment.ALIGNED, 
        "soothsayer": alignment.NEUTRAL, 
        "summoner": alignment.NEUTRAL,
    },
    "illusionist": {
        "chronomancer": alignment.NEUTRAL, 
        "elementalist": alignment.OPPOSED, 
        "enchanter": alignment.NEUTRAL, 
        "necromancer": alignment.NEUTRAL,
        "sigilist": alignment.ALIGNED, 
        "thaumaturge": alignment.ALIGNED, 
        "witch": alignment.NEUTRAL, 
        "soothsayer": alignment.ALIGNED, 
        "summoner": alignment.NEUTRAL,
    },
    "necromancer": {
        "chronomancer": alignment.ALIGNED, 
        "elementalist": alignment.ALIGNED, 
        "enchanter": alignment.NEUTRAL, 
        "illusionist": alignment.ALIGNED,
        "sigilist": alignment.ALIGNED, 
        "thaumaturge": alignment.OPPOSED, 
        "witch": alignment.ALIGNED, 
        "soothsayer": alignment.NEUTRAL, 
        "summoner": alignment.ALIGNED,
    },
    "sigilist": {
        "chronomancer": alignment.NEUTRAL, 
        "elementalist": alignment.NEUTRAL, 
        "enchanter": alignment.ALIGNED, 
        "illusionist": alignment.ALIGNED,
        "necromancer": alignment.NEUTRAL, 
        "thaumaturge": alignment.ALIGNED, 
        "witch": alignment.NEUTRAL, 
        "soothsayer": alignment.NEUTRAL, 
        "summoner": alignment.OPPOSED,
    },
    "thaumaturge": {
        "chronomancer": alignment.NEUTRAL, 
        "elementalist": alignment.NEUTRAL, 
        "enchanter": alignment.NEUTRAL, 
        "illusionist": alignment.ALIGNED,
        "necromancer": alignment.OPPOSED, 
        "sigilist": alignment.ALIGNED, 
        "witch": alignment.NEUTRAL, 
        "soothsayer": alignment.ALIGNED, 
        "summoner": alignment.NEUTRAL,
    },
    "witch": {
        "chronomancer": alignment.NEUTRAL, 
        "elementalist": alignment.NEUTRAL, 
        "enchanter": alignment.ALIGNED, 
        "illusionist": alignment.NEUTRAL,
        "necromancer": alignment.ALIGNED, 
        "sigilist": alignment.NEUTRAL, 
        "thaumaturge": alignment.NEUTRAL, 
        "soothsayer": alignment.OPPOSED, 
        "summoner": alignment.ALIGNED,
    },
}
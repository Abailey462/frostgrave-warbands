"""This module is to define the bases and upgrades for the ledger on creation. Any new bases
or upgrades should be added to this module.
"""

HOME_BASE_UPGRADES = {
    # name: (description, cost, troop_cost_modifier, discounted_spell_names, spell_cost_modifier)
    "carrier_pidgeon": (
        "Hiring members to your warband costs 10gc less.", 40, -10, [], 0,
    ),
    "reinforced_door": (
        "Your home base is harder to break into between scenarios.", 30, 0, [], 0,
    ),
    "runed_tome": (
        "A well-worn tome of annotations that makes three particular spells easier to cast.",
        50, 0, ["bone_dart", "spell_eater", "animate_skull"], -2,
    ),
}

HOME_BASE_TYPES = {
    "treasury": (
        "After each game, roll.\n2-16: add that many gold crowns to the treasury.\n"
        "17-18: add 100gc to that number.\n19-20: warband finds a treasure."
    ),
    "brewery": "brewery_description.",
}
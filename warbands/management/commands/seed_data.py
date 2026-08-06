"""
Seeds the database with Frostgrave reference data (schools, spells, items,
soldier types, home base upgrades) plus a demo user/wizard/warband and the
mortal enemy, based on the original YAML export.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from warbands.management.seeds import *
from warbands.models import (
    HomeBaseType,
    HomeBaseUpgrade,
    Item,
    MonsterType,
    School,
    SchoolAffinity,
    SoldierType,
    Spell,
)


class Command(BaseCommand):
    help = "Seed reference data and demo wizard/warband/mortal enemy."

    @transaction.atomic
    def handle(self, *args, **options):
        """Handle the seeding of initial data.
        """
        schools = self._seed_schools_and_spells()
        self._seed_affinities(schools)
        items = self._seed_items()
        self._seed_grimoire_items(items)
        self._seed_soldier_types(items)
        self._seed_monster_types()
        self._seed_home_base()

    def _seed_schools_and_spells(self):
        """Seed the initial schools and spells to be available to the user.
        """
        schools = {}
        for school_name, spells in SPELLS.items():
            school, _ = School.objects.get_or_create(name=school_name)
            schools[school_name] = school

            for spell_name, spell_data in spells.items():
                Spell.objects.get_or_create(
                    name=spell_name, school=school, defaults={"xp_cost": spell_data["cost"], "description": spell_data["description"]}
                )
        return schools

    def _seed_affinities(self, schools):
        """Seed the initial school affinities to be available to the user.

        Args:
            schools: The list of schools to seed affinities for.
        """
        for school_name, others in SCHOOL_ALIGNMENTS.items():
            school = schools[school_name]
            for other_name, alignment in others.items():
                other = schools.get(other_name)
                if not other:
                    continue
                SchoolAffinity.objects.update_or_create(
                    school=school, other_school=other, defaults={"value": alignment}
                )
                SchoolAffinity.objects.update_or_create(
                    school=other, other_school=school, defaults={"value": alignment}
                )

    def _seed_items(self):
        """Seed the initial items to be available to the user.
        """
        items = {}
        for name, description in ITEMS.items():
            item, _ = Item.objects.get_or_create(name=name, defaults={"description": description})
            items[name] = item
        return items

    def _seed_grimoire_items(self, items):
        """Seed the initial grimoires to be available to the user.

        Args:
            items: List of items to seed grimoires to.
        """
        for _, spells in SPELLS.items():
            for spell_name, _ in spells.items():
                spell = Spell.objects.filter(name=spell_name).first()
                if not spell:
                    continue
                item_name = f"grimoire_{spell}"
                item, _ = Item.objects.get_or_create(
                    name=item_name,
                    defaults={
                        "description": f"A tome containing the {spell_name.replace('_', ' ')} spell.",
                        "grants_spell": spell,
                    },
                )
                items[item_name] = item,

    def _seed_soldier_types(self, items):
        """Seed the soldier types to be available to the user.

        Args:
            items: Items that are available to soldiers.
        """
        soldier_types = {}
        for name, data in SOLDIER_TYPES.items():
            st, _ = SoldierType.objects.get_or_create(
                name=name,
                defaults={
                    "move": data["move"], "fight": data["fight"], "shoot": data["shoot"],
                    "armour": data["armour"], "will": data["will"], "health": data["health"],
                    "hire_cost": data["hire_cost"],
                },
            )
            st.base_items.set([items[i] for i in data["items"] if i in items])
            soldier_types[name] = st
        return soldier_types

    def _seed_monster_types(self):
        """Seed the monster types to be available to the user.
        """
        thief_stats = SOLDIER_TYPES["thief"]
        for name, description in [
            ("giant_rat", "A rat swollen to the size of a dog by some lingering magic."),
            ("construct", "An animated assemblage of stone, bone, or scrap, bound to a single purpose."),
        ]:
            MonsterType.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "move": thief_stats["move"], "fight": thief_stats["fight"], "shoot": thief_stats["shoot"],
                    "armour": thief_stats["armour"], "will": thief_stats["will"], "health": thief_stats["health"],
                },
            )

    def _seed_home_base(self):
        """Seed the home bases to be available to the user.
        """
        for name, description in HOME_BASE_TYPES.items():
            HomeBaseType.objects.get_or_create(name=name, defaults={"description": description})
        for name, (description, cost, troop_mod, discounted_spell_names, spell_mod) in HOME_BASE_UPGRADES.items():
            upgrade, _ = HomeBaseUpgrade.objects.get_or_create(
                name=name,
                defaults={
                    "description": description, "cost": cost,
                    "troop_cost_modifier": troop_mod, "spell_cost_modifier": spell_mod,
                },
            )
            if discounted_spell_names:
                spells = Spell.objects.filter(name__in=discounted_spell_names)
                upgrade.discounted_spells.set(spells)
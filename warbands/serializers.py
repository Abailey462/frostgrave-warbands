from rest_framework import serializers

from .models import (
    Apprentice,
    Game,
    HomeBaseType,
    HomeBaseUpgrade,
    Item,
    MonsterType,
    MortalEnemy,
    Purchase,
    School,
    Soldier,
    SoldierType,
    Spell,
    Warband,
    Wizard,
    WizardItem,
    WizardSpell,
)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "description", "grants_spell"]


class SpellSerializer(serializers.ModelSerializer):
    school = serializers.StringRelatedField()

    class Meta:
        model = Spell
        fields = ["id", "name", "school", "xp_cost", "description"]


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ["id", "name", "description"]


class SoldierTypeSerializer(serializers.ModelSerializer):
    base_items = ItemSerializer(many=True, read_only=True)

    class Meta:
        model = SoldierType
        fields = ["id", "name", "move", "fight", "shoot", "armour", "will", "health", "hire_cost", "base_items"]


class SoldierSerializer(serializers.ModelSerializer):
    soldier_type = SoldierTypeSerializer(read_only=True)
    soldier_type_id = serializers.PrimaryKeyRelatedField(
        source="soldier_type", queryset=SoldierType.objects.all(), write_only=True
    )
    items = ItemSerializer(many=True, read_only=True)
    item_ids = serializers.PrimaryKeyRelatedField(
        source="items", queryset=Item.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Soldier
        fields = [
            "id", "warband", "soldier_type", "soldier_type_id", "name", "description",
            "current_health", "price_paid",
            "move", "fight", "shoot", "armour", "will", "health", "items", "item_ids",
        ]


class MonsterTypeSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True, read_only=True)

    class Meta:
        model = MonsterType
        fields = ["id", "name", "description", "move", "fight", "shoot", "armour", "will", "health", "items"]


class WizardItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(source="item", queryset=Item.objects.all(), write_only=True)

    class Meta:
        model = WizardItem
        fields = ["id", "item", "item_id", "quantity", "location"]


class WizardSpellSerializer(serializers.ModelSerializer):
    """A spell the wizard has actually learned. Grimoires (unlearned spells)
    show up under wizard_items instead, via Item.grants_spell. Casting cost
    is backend-computed (base + school modifier - points invested); only
    points_invested is directly editable by the wizard's owner."""
    spell = SpellSerializer(read_only=True)
    spell_id = serializers.PrimaryKeyRelatedField(source="spell", queryset=Spell.objects.all(), write_only=True)
    base_casting_cost = serializers.ReadOnlyField()
    casting_modifier = serializers.ReadOnlyField()
    computed_casting_cost = serializers.ReadOnlyField()
    final_casting_cost = serializers.ReadOnlyField()

    class Meta:
        model = WizardSpell
        fields = [
            "id", "spell", "spell_id",
            "base_casting_cost", "casting_modifier", "computed_casting_cost",
            "points_invested", "final_casting_cost",
        ]


class WarbandNestedSerializer(serializers.ModelSerializer):
    soldiers = SoldierSerializer(many=True, read_only=True)

    class Meta:
        model = Warband
        fields = ["id", "name", "soldiers"]


class ApprenticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apprentice
        fields = ["id", "name", "current_health", "move", "fight", "shoot", "armour", "will", "health"]


class MortalEnemySerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True, read_only=True)
    warband = WarbandNestedSerializer(read_only=True)
    ranged_attack_primary = serializers.StringRelatedField()
    ranged_attack_secondary = serializers.StringRelatedField()
    utility_primary = serializers.StringRelatedField()
    utility_secondary = serializers.StringRelatedField()
    out_of_game_primary = serializers.StringRelatedField()
    out_of_game_secondary = serializers.StringRelatedField()

    class Meta:
        model = MortalEnemy
        fields = [
            "id", "name", "type", "current_health",
            "move", "fight", "shoot", "armour", "will", "health",
            "items", "warband",
            "ranged_attack_primary", "ranged_attack_secondary",
            "utility_primary", "utility_secondary",
            "out_of_game_primary", "out_of_game_secondary",
        ]


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ["id", "kind", "amount", "description", "created_at"]


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = [
            "id", "title", "treasures_earned", "gold_earned", "items_earned",
            "monsters_killed", "successful_spells", "unsuccessful_spells",
            "bonus_xp", "total_xp", "created_at",
        ]


class WizardSerializer(serializers.ModelSerializer):
    wizard_items = WizardItemSerializer(many=True, read_only=True)
    wizard_spells = WizardSpellSerializer(many=True, read_only=True)
    warband = WarbandNestedSerializer(read_only=True)
    apprentice = ApprenticeSerializer(read_only=True)
    mortal_enemy = MortalEnemySerializer(read_only=True)
    purchases = PurchaseSerializer(many=True, read_only=True)
    games = GameSerializer(many=True, read_only=True)
    total_treasures = serializers.ReadOnlyField()
    school = serializers.StringRelatedField()
    home_base_type = serializers.StringRelatedField()
    home_base_upgrades = serializers.StringRelatedField(many=True)

    class Meta:
        model = Wizard
        fields = [
            "id", "name", "school", "level", "experience", "gold",
            "current_health", "move", "fight", "shoot", "armour", "will", "health",
            "home_base_type", "home_base_upgrades",
            "wizard_items", "wizard_spells", "warband",
            "apprentice", "mortal_enemy", "purchases", "games", "total_treasures",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

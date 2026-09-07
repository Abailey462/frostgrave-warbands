from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import (
    Apprentice,
    Game,
    HomeBaseType,
    HomeBaseUpgrade,
    Item,
    MortalEnemy,
    Soldier,
    SoldierType,
    Spell,
    Wizard,
)

STAT_FIELDS = ["move", "fight", "shoot", "armour", "will", "health"]


class SignupForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ["username"]


class WizardForm(forms.ModelForm):
    """Used only for creating a wizard. School is chosen once, here, and
    determines the casting-cost modifier for spells outside that school.
    Home base is deliberately excluded — it's set later from the dedicated
    Home Base section, not at creation time."""

    hire_apprentice = forms.BooleanField(
        required=False, initial=True,
        label="Hire an apprentice for 100gc?",
        help_text="Wizards start with 400gc. Skip this to keep all 400.",
    )

    class Meta:
        model = Wizard
        fields = [
            "name", "school", "level", "current_health",
            "move", "fight", "shoot", "armour", "will", "health",
        ]
        widgets = {f: forms.NumberInput(attrs={"class": "num-input"})
                   for f in ["level", "current_health", "move", "fight", "shoot", "armour", "will", "health"]}


class WizardStatsForm(forms.ModelForm):
    """Used to edit an existing wizard's stats. Deliberately excludes
    `school`, which is set once at creation, so re-saving stats can never
    silently clear it."""

    class Meta:
        model = Wizard
        fields = [
            "name", "level", "current_health",
            "move", "fight", "shoot", "armour", "will", "health",
        ]
        widgets = {f: forms.NumberInput(attrs={"class": "num-input"})
                   for f in ["level", "current_health", "move", "fight", "shoot", "armour", "will", "health"]}


class ApprenticeForm(forms.ModelForm):
    class Meta:
        model = Apprentice
        fields = ["name", "current_health"]
        widgets = {"current_health": forms.NumberInput(attrs={"class": "num-input"})}


class MortalEnemyForm(forms.ModelForm):
    class Meta:
        model = MortalEnemy
        fields = [
            "name", "type", "current_health",
            "move", "fight", "shoot", "armour", "will", "health",
            "ranged_attack_primary", "ranged_attack_secondary",
            "utility_primary", "utility_secondary",
            "out_of_game_primary", "out_of_game_secondary",
        ]
        widgets = {f: forms.NumberInput(attrs={"class": "num-input"})
                   for f in ["current_health", "move", "fight", "shoot", "armour", "will", "health"]}


class GoldExperienceForm(forms.Form):
    gold_delta = forms.IntegerField(required=False, initial=0, min_value=0)
    experience_delta = forms.IntegerField(required=False, initial=0, min_value=0)


class SoldierTypeChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, wizard=None, **kwargs):
        self.wizard = wizard
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        cost = self.wizard.effective_hire_cost(obj) if self.wizard else obj.hire_cost
        return f"{obj.name.replace('_', ' ').title()} — {cost}gc"


class AddSoldierForm(forms.Form):
    name = forms.CharField(required=False, max_length=100)

    def __init__(self, *args, wizard=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["soldier_type"] = SoldierTypeChoiceField(
            queryset=SoldierType.objects.all(), wizard=wizard
        )


class AddWizardItemForm(forms.Form):
    item = forms.ModelChoiceField(queryset=Item.objects.all())
    quantity = forms.IntegerField(initial=1, min_value=1)
    location = forms.ChoiceField(choices=[
        ("wizard", "Wizard's pack"),
        ("apprentice", "Apprentice's pack"),
        ("vault", "Vault"),
    ], initial="vault")


class AddMortalEnemyItemForm(forms.Form):
    item = forms.ModelChoiceField(queryset=Item.objects.all())


class AddWizardSpellForm(forms.Form):
    """Add a spell the wizard has actually learned. The casting cost is
    computed automatically from the spell's admin-set base cost plus the
    wizard's school-alignment modifier — not entered here. Grimoires
    (unlearned spells) are tracked as Items instead — see AddWizardItemForm."""
    spell = forms.ModelChoiceField(queryset=Spell.objects.select_related("school").all())


class HomeBaseTypeForm(forms.ModelForm):
    class Meta:
        model = Wizard
        fields = ["home_base_type"]


class HomeBaseUpgradeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.name.replace('_', ' ').title()} — {obj.cost}gc"


class BuyHomeBaseUpgradeForm(forms.Form):
    upgrade = HomeBaseUpgradeChoiceField(queryset=HomeBaseUpgrade.objects.none())

    def __init__(self, *args, wizard=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = HomeBaseUpgrade.objects.all()
        if wizard is not None:
            queryset = queryset.exclude(id__in=wizard.home_base_upgrades.values_list("id", flat=True))
        self.fields["upgrade"].queryset = queryset


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = [
            "title", "treasures_earned", "gold_earned", "items_earned",
            "monsters_killed", "successful_spells", "unsuccessful_spells",
            "bonus_xp",
        ]
        widgets = {
            f: forms.NumberInput(attrs={"class": "num-input"})
            for f in ["treasures_earned", "gold_earned", "monsters_killed",
                       "successful_spells", "unsuccessful_spells", "bonus_xp"]
        }

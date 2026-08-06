from itertools import groupby

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AddMortalEnemyItemForm,
    AddSoldierForm,
    AddWizardItemForm,
    AddWizardSpellForm,
    ApprenticeForm,
    BuyHomeBaseUpgradeForm,
    GameForm,
    GoldExperienceForm,
    HomeBaseTypeForm,
    MortalEnemyForm,
    SignupForm,
    WizardForm,
    WizardStatsForm,
)
from .models import (
    Apprentice,
    Game,
    MortalEnemy,
    MonsterType,
    Purchase,
    Soldier,
    Spell,
    Warband,
    Wizard,
    WizardItem,
    WizardSpell,
    get_aligned_and_neutral_schools,
)


def _get_owned_wizard(request, wizard_id):
    return get_object_or_404(Wizard, id=wizard_id, owner=request.user)


def _get_owned_mortal_enemy(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    return get_object_or_404(MortalEnemy, wizard=wizard)


def signup(request):
    if request.user.is_authenticated:
        return redirect("warband-list")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("warband-list")
    else:
        form = SignupForm()
    return render(request, "warbands/signup.html", {"form": form})


@login_required
def warband_list(request):
    wizards = Wizard.objects.filter(owner=request.user).select_related("warband", "home_base_type", "school")
    return render(request, "warbands/warband_list.html", {"wizards": wizards})


@login_required
def wizard_create(request):
    if request.method == "POST":
        form = WizardForm(request.POST)
        if form.is_valid():
            hire_apprentice = form.cleaned_data["hire_apprentice"]
            wizard = form.save(commit=False)
            wizard.owner = request.user
            # Home base is deliberately not set at creation time — added
            # later from the Home Base section of the editor.
            wizard.save()

            Warband.objects.create(wizard=wizard, name=f"{wizard.name}'s Warband")

            if hire_apprentice:
                wizard.gold = max(0, wizard.gold - 100)
                wizard.save(update_fields=["gold"])
                Apprentice.default_for_wizard(wizard).save()

            mortal_enemy = MortalEnemy.objects.create(wizard=wizard, name=f"{wizard.name}'s Mortal Enemy")
            Warband.objects.create(mortal_enemy=mortal_enemy, name=f"{mortal_enemy.name}'s Warband")

            messages.success(request, "Wizard created! Now choose your 8 starting spells.")
            return redirect("wizard-choose-spells", wizard_id=wizard.id)
    else:
        form = WizardForm()
    return render(request, "warbands/wizard_form.html", {"form": form, "creating": True})


@login_required
def wizard_choose_starting_spells(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)

    if wizard.wizard_spells.exists():
        messages.info(request, "Starting spells have already been chosen for this wizard.")
        return redirect("wizard-detail", wizard_id=wizard.id)

    if wizard.school is None:
        messages.error(request, "This wizard has no school set, so starting spells can't be computed.")
        return redirect("wizard-detail", wizard_id=wizard.id)

    aligned_schools, neutral_schools = get_aligned_and_neutral_schools(wizard.school)
    primary_spells = Spell.objects.filter(school=wizard.school).order_by("name")
    aligned_spells = Spell.objects.filter(school__in=aligned_schools).select_related("school").order_by("school__name", "name")
    neutral_spells = Spell.objects.filter(school__in=neutral_schools).select_related("school").order_by("school__name", "name")

    selected_primary_ids = []
    selected_aligned_ids = []
    selected_neutral_ids = []

    if request.method == "POST":
        primary_ids = request.POST.getlist("primary_spells")
        aligned_ids = request.POST.getlist("aligned_spells")
        neutral_ids = request.POST.getlist("neutral_spells")
        selected_primary_ids = primary_ids
        selected_aligned_ids = aligned_ids
        selected_neutral_ids = neutral_ids

        errors = []
        if len(primary_ids) != 3:
            errors.append("Choose exactly 3 spells from your primary school.")
        if len(aligned_ids) != 3:
            errors.append("Choose exactly 3 spells from aligned schools.")
        if len(neutral_ids) != 2:
            errors.append("Choose exactly 2 spells from neutral schools.")

        chosen_primary = list(primary_spells.filter(id__in=primary_ids))
        chosen_aligned = list(aligned_spells.filter(id__in=aligned_ids))
        chosen_neutral = list(neutral_spells.filter(id__in=neutral_ids))

        if not errors:
            if len(chosen_primary) != len(set(primary_ids)):
                errors.append("One or more primary spell selections were invalid.")
            if len(chosen_aligned) != len(set(aligned_ids)):
                errors.append("One or more aligned spell selections were invalid.")
            if len(chosen_neutral) != len(set(neutral_ids)):
                errors.append("One or more neutral spell selections were invalid.")

        if not errors:
            aligned_school_ids = [s.school_id for s in chosen_aligned]
            if len(set(aligned_school_ids)) != len(aligned_school_ids):
                errors.append("No two aligned-school spells may come from the same school.")
            neutral_school_ids = [s.school_id for s in chosen_neutral]
            if len(set(neutral_school_ids)) != len(neutral_school_ids):
                errors.append("No two neutral-school spells may come from the same school.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            for spell in chosen_primary + chosen_aligned + chosen_neutral:
                WizardSpell.objects.get_or_create(wizard=wizard, spell=spell)
            messages.success(request, "Starting spells learned!")
            return redirect("wizard-detail", wizard_id=wizard.id)

    context = {
        "wizard": wizard,
        "primary_spells": primary_spells,
        "aligned_spells": aligned_spells,
        "neutral_spells": neutral_spells,
        "selected_primary_ids": [int(i) for i in selected_primary_ids if i.isdigit()],
        "selected_aligned_ids": [int(i) for i in selected_aligned_ids if i.isdigit()],
        "selected_neutral_ids": [int(i) for i in selected_neutral_ids if i.isdigit()],
    }
    return render(request, "warbands/wizard_choose_spells.html", context)


@login_required
def wizard_detail(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    warband = getattr(wizard, "warband", None)
    apprentice = getattr(wizard, "apprentice", None)
    mortal_enemy = getattr(wizard, "mortal_enemy", None)
    mortal_enemy_warband = getattr(mortal_enemy, "warband", None) if mortal_enemy else None

    all_wizard_items = wizard.wizard_items.select_related("item", "item__grants_spell")

    wizard_spells = list(
        wizard.wizard_spells.select_related("spell", "spell__school").order_by("spell__school__name", "spell__name")
    )
    spells_by_school = [
        (school, list(spells))
        for school, spells in groupby(wizard_spells, key=lambda ws: ws.spell.school)
    ]

    context = {
        "wizard": wizard,
        "warband": warband,
        "soldiers": warband.soldiers.select_related("soldier_type").prefetch_related("items") if warband else [],
        "wizard_carried_items": all_wizard_items.filter(location="wizard"),
        "apprentice_carried_items": all_wizard_items.filter(location="apprentice"),
        "vaulted_items": all_wizard_items.filter(location="vault"),
        "spells_by_school": spells_by_school,
        "gold_xp_form": GoldExperienceForm(),
        "add_soldier_form": AddSoldierForm(wizard=wizard),
        "add_item_form": AddWizardItemForm(),
        "add_spell_form": AddWizardSpellForm(),
        "wizard_form": WizardStatsForm(instance=wizard),

        "apprentice": apprentice,
        "apprentice_form": ApprenticeForm(instance=apprentice) if apprentice else None,

        "mortal_enemy": mortal_enemy,
        "mortal_enemy_form": MortalEnemyForm(instance=mortal_enemy) if mortal_enemy else None,
        "mortal_enemy_warband": mortal_enemy_warband,
        "mortal_enemy_soldiers": (
            mortal_enemy_warband.soldiers.select_related("soldier_type").prefetch_related("items")
            if mortal_enemy_warband else []
        ),
        "mortal_enemy_items": mortal_enemy.items.all() if mortal_enemy else [],
        "add_mortal_enemy_soldier_form": AddSoldierForm(),
        "add_mortal_enemy_item_form": AddMortalEnemyItemForm(),

        "home_base_type_form": HomeBaseTypeForm(instance=wizard),
        "home_base_upgrade_form": BuyHomeBaseUpgradeForm(wizard=wizard),
        "owned_upgrades": wizard.home_base_upgrades.all(),

        "purchases": wizard.purchases.all(),

        "games_with_forms": [(game, GameForm(instance=game)) for game in wizard.games.all()],

        "monster_types": MonsterType.objects.prefetch_related("items").all(),
        "all_spells": Spell.objects.select_related("school").order_by("school__name", "name"),
    }
    return render(request, "warbands/wizard_detail.html", context)


@login_required
@require_POST
def wizard_delete(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    name = wizard.name
    wizard.delete()
    messages.success(request, f"{name} has been deleted.")
    return redirect("warband-list")


@login_required
@require_POST
def wizard_update_stats(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    form = WizardStatsForm(request.POST, instance=wizard)
    if form.is_valid():
        form.save()
        messages.success(request, "Wizard stats updated.")
    else:
        messages.error(request, "Could not update wizard stats.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def wizard_adjust_gold_xp(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    form = GoldExperienceForm(request.POST)
    if form.is_valid():
        gold_delta = form.cleaned_data.get("gold_delta") or 0
        xp_delta = form.cleaned_data.get("experience_delta") or 0
        wizard.gold = max(0, wizard.gold + gold_delta)
        wizard.experience = max(0, wizard.experience + xp_delta)
        wizard.save(update_fields=["gold", "experience"])
        messages.success(request, "Gold / experience updated.")
    return redirect("wizard-detail", wizard_id=wizard.id)


# ---------------------------------------------------------------------------
# Home base
# ---------------------------------------------------------------------------

@login_required
@require_POST
def wizard_set_home_base(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    form = HomeBaseTypeForm(request.POST, instance=wizard)
    if form.is_valid():
        form.save()
        messages.success(request, "Home base set.")
    else:
        messages.error(request, "Could not set home base.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def wizard_buy_home_base_upgrade(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    form = BuyHomeBaseUpgradeForm(request.POST, wizard=wizard)
    if form.is_valid():
        upgrade = form.cleaned_data["upgrade"]
        if wizard.gold < upgrade.cost:
            messages.error(request, f"Not enough gold — {upgrade} costs {upgrade.cost}gc.")
        else:
            wizard.gold -= upgrade.cost
            wizard.save(update_fields=["gold"])
            wizard.home_base_upgrades.add(upgrade)
            Purchase.objects.create(
                wizard=wizard, kind="home_base_upgrade", amount=upgrade.cost,
                description=f"Bought {upgrade} upgrade", home_base_upgrade=upgrade,
            )
            messages.success(request, f"Purchased {upgrade} for {upgrade.cost}gc.")
    else:
        messages.error(request, "Could not purchase upgrade.")
    return redirect("wizard-detail", wizard_id=wizard.id)


# ---------------------------------------------------------------------------
# Purchases (undo for a refund)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def purchase_undo(request, wizard_id, purchase_id):
    wizard = _get_owned_wizard(request, wizard_id)
    purchase = get_object_or_404(Purchase, id=purchase_id, wizard=wizard)

    if purchase.kind == "soldier" and purchase.soldier_id:
        purchase.soldier.delete()  # cascades and deletes this Purchase row too
    elif purchase.kind == "home_base_upgrade" and purchase.home_base_upgrade_id:
        wizard.home_base_upgrades.remove(purchase.home_base_upgrade)
        purchase.delete()
    else:
        purchase.delete()

    wizard.gold += purchase.amount
    wizard.save(update_fields=["gold"])
    messages.success(request, f"Undone: {purchase.description}. Refunded {purchase.amount}gc.")
    return redirect("wizard-detail", wizard_id=wizard.id)


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

@login_required
@require_POST
def wizard_add_item(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    form = AddWizardItemForm(request.POST)
    if form.is_valid():
        WizardItem.objects.create(
            wizard=wizard,
            item=form.cleaned_data["item"],
            quantity=form.cleaned_data["quantity"],
            location=form.cleaned_data["location"],
        )
        messages.success(request, "Item added.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def wizard_remove_item(request, wizard_id, wizard_item_id):
    wizard = _get_owned_wizard(request, wizard_id)
    WizardItem.objects.filter(id=wizard_item_id, wizard=wizard).delete()
    messages.success(request, "Item removed.")
    return redirect("wizard-detail", wizard_id=wizard.id)


# ---------------------------------------------------------------------------
# Spells
# ---------------------------------------------------------------------------

@login_required
@require_POST
def wizard_add_spell(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    form = AddWizardSpellForm(request.POST)
    if form.is_valid():
        spell = form.cleaned_data["spell"]
        WizardSpell.objects.get_or_create(wizard=wizard, spell=spell)
        messages.success(request, "Spell added.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def wizard_remove_spell(request, wizard_id, wizard_spell_id):
    wizard = _get_owned_wizard(request, wizard_id)
    WizardSpell.objects.filter(id=wizard_spell_id, wizard=wizard).delete()
    messages.success(request, "Spell removed.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def wizard_spell_update_points(request, wizard_id, wizard_spell_id):
    wizard = _get_owned_wizard(request, wizard_id)
    wizard_spell = get_object_or_404(WizardSpell, id=wizard_spell_id, wizard=wizard)
    try:
        wizard_spell.points_invested = max(
            0, int(request.POST.get("points_invested", wizard_spell.points_invested))
        )
        wizard_spell.save(update_fields=["points_invested"])
        messages.success(request, "Points updated.")
    except (TypeError, ValueError):
        messages.error(request, "Invalid points value.")
    return redirect("wizard-detail", wizard_id=wizard.id)


# ---------------------------------------------------------------------------
# Wizard's own warband
# ---------------------------------------------------------------------------

@login_required
@require_POST
def warband_add_soldier(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    warband = getattr(wizard, "warband", None)
    if warband is None:
        warband = Warband.objects.create(wizard=wizard, name=f"{wizard.name}'s Warband")
    form = AddSoldierForm(request.POST, wizard=wizard)
    if form.is_valid():
        soldier_type = form.cleaned_data["soldier_type"]
        cost = wizard.effective_hire_cost(soldier_type)
        if wizard.gold < cost:
            messages.error(request, f"Not enough gold — a {soldier_type} costs {cost}gc.")
        else:
            wizard.gold -= cost
            wizard.save(update_fields=["gold"])
            soldier = Soldier.objects.create(
                warband=warband,
                soldier_type=soldier_type,
                name=form.cleaned_data.get("name") or "",
                current_health=soldier_type.health or 10,
                price_paid=cost,
            )
            Purchase.objects.create(
                wizard=wizard, kind="soldier", amount=cost,
                description=f"Hired {soldier_type}" + (f" ({soldier.name})" if soldier.name else ""),
                soldier=soldier,
            )
            messages.success(request, f"Hired a {soldier_type} for {cost}gc.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def warband_sell_soldier(request, wizard_id, soldier_id):
    wizard = _get_owned_wizard(request, wizard_id)
    soldier = get_object_or_404(Soldier, id=soldier_id, warband__wizard=wizard)
    refund = soldier.price_paid
    soldier.delete()
    wizard.gold += refund
    wizard.save(update_fields=["gold"])
    messages.success(request, f"Sold soldier for {refund}gc.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def warband_retire_soldier(request, wizard_id, soldier_id):
    wizard = _get_owned_wizard(request, wizard_id)
    soldier = get_object_or_404(Soldier, id=soldier_id, warband__wizard=wizard)
    soldier.delete()
    messages.success(request, "Soldier retired (no gold returned).")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def soldier_update_health(request, wizard_id, soldier_id):
    wizard = _get_owned_wizard(request, wizard_id)
    soldier = get_object_or_404(Soldier, id=soldier_id, warband__wizard=wizard)
    try:
        soldier.current_health = int(request.POST.get("current_health", soldier.current_health))
        soldier.save(update_fields=["current_health"])
    except (TypeError, ValueError):
        messages.error(request, "Invalid health value.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def soldier_update_description(request, wizard_id, soldier_id):
    wizard = _get_owned_wizard(request, wizard_id)
    soldier = get_object_or_404(Soldier, id=soldier_id, warband__wizard=wizard)
    soldier.description = request.POST.get("description", "") or None
    soldier.save(update_fields=["description"])
    messages.success(request, "Description updated.")
    return redirect("wizard-detail", wizard_id=wizard.id)


# ---------------------------------------------------------------------------
# Apprentice
# ---------------------------------------------------------------------------

@login_required
@require_POST
def apprentice_update_stats(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    apprentice = get_object_or_404(Apprentice, wizard=wizard)
    form = ApprenticeForm(request.POST, instance=apprentice)
    if form.is_valid():
        form.save()
        messages.success(request, "Apprentice updated.")
    else:
        messages.error(request, "Could not update apprentice.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def apprentice_hire(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    if hasattr(wizard, "apprentice"):
        messages.info(request, "This wizard already has an apprentice.")
        return redirect("wizard-detail", wizard_id=wizard.id)
    cost = 100
    if wizard.gold < cost:
        messages.error(request, f"Not enough gold — hiring an apprentice costs {cost}gc.")
    else:
        wizard.gold -= cost
        wizard.save(update_fields=["gold"])
        Apprentice.default_for_wizard(wizard).save()
        messages.success(request, f"Apprentice hired for {cost}gc.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def apprentice_retire(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    apprentice = get_object_or_404(Apprentice, wizard=wizard)
    apprentice.delete()
    messages.success(request, "Apprentice retired (no gold returned).")
    return redirect("wizard-detail", wizard_id=wizard.id)


# ---------------------------------------------------------------------------
# Mortal enemy (own wizard-like stat block + own warband, per wizard)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def mortal_enemy_update_stats(request, wizard_id):
    mortal_enemy = _get_owned_mortal_enemy(request, wizard_id)
    form = MortalEnemyForm(request.POST, instance=mortal_enemy)
    if form.is_valid():
        form.save()
        messages.success(request, "Mortal enemy updated.")
    else:
        messages.error(request, "Could not update mortal enemy.")
    return redirect("wizard-detail", wizard_id=wizard_id)


@login_required
@require_POST
def mortal_enemy_add_item(request, wizard_id):
    mortal_enemy = _get_owned_mortal_enemy(request, wizard_id)
    form = AddMortalEnemyItemForm(request.POST)
    if form.is_valid():
        mortal_enemy.items.add(form.cleaned_data["item"])
        messages.success(request, "Item added to mortal enemy.")
    return redirect("wizard-detail", wizard_id=wizard_id)


@login_required
@require_POST
def mortal_enemy_remove_item(request, wizard_id, item_id):
    mortal_enemy = _get_owned_mortal_enemy(request, wizard_id)
    mortal_enemy.items.remove(item_id)
    messages.success(request, "Item removed from mortal enemy.")
    return redirect("wizard-detail", wizard_id=wizard_id)


@login_required
@require_POST
def mortal_enemy_add_soldier(request, wizard_id):
    mortal_enemy = _get_owned_mortal_enemy(request, wizard_id)
    warband = getattr(mortal_enemy, "warband", None)
    if warband is None:
        warband = Warband.objects.create(mortal_enemy=mortal_enemy, name=f"{mortal_enemy.name}'s Warband")
    form = AddSoldierForm(request.POST)
    if form.is_valid():
        soldier_type = form.cleaned_data["soldier_type"]
        Soldier.objects.create(
            warband=warband,
            soldier_type=soldier_type,
            name=form.cleaned_data.get("name") or "",
            current_health=soldier_type.health or 10,
        )
        messages.success(request, "Soldier added to mortal enemy's warband.")
    return redirect("wizard-detail", wizard_id=wizard_id)


@login_required
@require_POST
def mortal_enemy_remove_soldier(request, wizard_id, soldier_id):
    mortal_enemy = _get_owned_mortal_enemy(request, wizard_id)
    Soldier.objects.filter(id=soldier_id, warband__mortal_enemy=mortal_enemy).delete()
    messages.success(request, "Soldier removed from mortal enemy's warband.")
    return redirect("wizard-detail", wizard_id=wizard_id)


@login_required
@require_POST
def mortal_enemy_soldier_update_health(request, wizard_id, soldier_id):
    mortal_enemy = _get_owned_mortal_enemy(request, wizard_id)
    soldier = get_object_or_404(Soldier, id=soldier_id, warband__mortal_enemy=mortal_enemy)
    try:
        soldier.current_health = int(request.POST.get("current_health", soldier.current_health))
        soldier.save(update_fields=["current_health"])
    except (TypeError, ValueError):
        messages.error(request, "Invalid health value.")
    return redirect("wizard-detail", wizard_id=wizard_id)


@login_required
@require_POST
def mortal_enemy_soldier_update_description(request, wizard_id, soldier_id):
    mortal_enemy = _get_owned_mortal_enemy(request, wizard_id)
    soldier = get_object_or_404(Soldier, id=soldier_id, warband__mortal_enemy=mortal_enemy)
    soldier.description = request.POST.get("description", "") or None
    soldier.save(update_fields=["description"])
    messages.success(request, "Description updated.")
    return redirect("wizard-detail", wizard_id=wizard_id)


# ---------------------------------------------------------------------------
# Games — one record per scenario played
# ---------------------------------------------------------------------------

@login_required
@require_POST
def game_create(request, wizard_id):
    wizard = _get_owned_wizard(request, wizard_id)
    game_number = wizard.games.count() + 1
    Game.objects.create(wizard=wizard, title=f"Game {game_number}")
    messages.success(request, "New game added.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def game_update(request, wizard_id, game_id):
    wizard = _get_owned_wizard(request, wizard_id)
    game = get_object_or_404(Game, id=game_id, wizard=wizard)
    form = GameForm(request.POST, instance=game)
    if form.is_valid():
        form.save()
        messages.success(request, "Game updated.")
    else:
        messages.error(request, "Could not update game.")
    return redirect("wizard-detail", wizard_id=wizard.id)


@login_required
@require_POST
def game_delete(request, wizard_id, game_id):
    wizard = _get_owned_wizard(request, wizard_id)
    game = get_object_or_404(Game, id=game_id, wizard=wizard)
    game.delete()
    messages.success(request, "Game deleted.")
    return redirect("wizard-detail", wizard_id=wizard.id)

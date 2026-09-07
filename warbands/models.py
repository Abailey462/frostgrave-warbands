from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


# ---------------------------------------------------------------------------
# Reference / lookup data (seeded from YAML, editable in admin)
# ---------------------------------------------------------------------------

class School(models.Model):
    """A school of magic (Elementalist, Necromancer, etc.)."""
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name.title()


class SchoolAffinity(models.Model):
    """
    How aligned two schools are (used for e.g. determining apprentice
    school compatibility / cross-school learning cost). Value follows the
    source data scale (2 = opposed, 4 = neutral, 6 = aligned).
    """
    school = models.ForeignKey(School, related_name="affinities", on_delete=models.CASCADE)
    other_school = models.ForeignKey(School, related_name="affinities_reverse", on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("school", "other_school")
        verbose_name_plural = "School affinities"

    def __str__(self):
        return f"{self.school} <-> {self.other_school}: {self.value}"


def compute_casting_modifier(wizard_school, spell_school):
    """
    Schools aligned at 2 are aligned, 4 is neutral, 6 is opposed — that
    value is added straight to a spell's base casting cost. A wizard's own
    school always costs +0. If the wizard hasn't picked a school yet, no
    modifier is applied.
    """
    if wizard_school is None:
        return 0
    if wizard_school.id == spell_school.id:
        return 0
    affinity = SchoolAffinity.objects.filter(school=wizard_school, other_school=spell_school).first()
    return affinity.value if affinity else 4


def get_aligned_and_neutral_schools(primary_school):
    """
    For starting-spell selection: schools at affinity 2 are "aligned",
    affinity 4 are "neutral". Opposed (6) schools aren't offered for
    starting spells.
    """
    if primary_school is None:
        return School.objects.none(), School.objects.none()
    aligned_ids = SchoolAffinity.objects.filter(
        school=primary_school, value=2
    ).values_list("other_school_id", flat=True)
    neutral_ids = SchoolAffinity.objects.filter(
        school=primary_school, value=4
    ).values_list("other_school_id", flat=True)
    return School.objects.filter(id__in=aligned_ids), School.objects.filter(id__in=neutral_ids)


class Spell(models.Model):
    """A single spell, belonging to one school, with an XP cost to learn."""
    name = models.CharField(max_length=64)
    school = models.ForeignKey(School, related_name="spells", on_delete=models.CASCADE)
    xp_cost = models.PositiveIntegerField(default=0, help_text="Experience cost to learn this spell.")
    base_casting_cost = models.PositiveSmallIntegerField(
        default=10,
        help_text="Admin-set base difficulty to cast this spell, before any school-alignment modifier.",
    )
    description = models.TextField(null=True, blank=True, default=None)

    class Meta:
        unique_together = ("name", "school")
        ordering = ["school__name", "name"]

    def __str__(self):
        return f"{self.name.replace('_', ' ').title()} ({self.school})"


class Item(models.Model):
    """Equipment / treasury items available in the game."""
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    # Some items (e.g. grimoires) teach a specific spell when used/found.
    grants_spell = models.ForeignKey(
        Spell, null=True, blank=True, related_name="granting_items", on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name.replace("_", " ").title()


class SoldierType(models.Model):
    """A template for a type of hired soldier (thug, archer, etc.)."""
    name = models.CharField(max_length=64, unique=True)
    move = models.PositiveSmallIntegerField(null=True, blank=True)
    fight = models.SmallIntegerField(null=True, blank=True)
    shoot = models.SmallIntegerField(null=True, blank=True)
    armour = models.PositiveSmallIntegerField(null=True, blank=True)
    will = models.SmallIntegerField(null=True, blank=True)
    health = models.PositiveSmallIntegerField(null=True, blank=True)
    base_items = models.ManyToManyField(Item, blank=True, related_name="soldier_types")
    hire_cost = models.PositiveIntegerField(default=0, help_text="Gold crowns to hire.")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name.title()


class MonsterType(models.Model):
    """
    A monster stat block (giant rat, construct, etc). Added and edited only
    through /admin — there is no public-facing create/edit form. Shown
    read-only, searchable, in the Monsters tab on a wizard's page.
    """
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(null=True, blank=True, default=None)
    move = models.PositiveSmallIntegerField(null=True, blank=True)
    fight = models.SmallIntegerField(null=True, blank=True)
    shoot = models.SmallIntegerField(null=True, blank=True)
    armour = models.PositiveSmallIntegerField(null=True, blank=True)
    will = models.SmallIntegerField(null=True, blank=True)
    health = models.PositiveSmallIntegerField(null=True, blank=True)
    items = models.ManyToManyField(Item, blank=True, related_name="monster_types")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Monster types"

    def __str__(self):
        return self.name.title()


class HomeBaseType(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name.replace("_", " ").title()


class HomeBaseUpgrade(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    cost = models.PositiveIntegerField(default=0, help_text="Gold crowns to purchase this upgrade.")

    troop_cost_modifier = models.IntegerField(
        default=0,
        help_text="Gold crowns added to (or, if negative, subtracted from) the hire cost of EVERY "
                   "soldier type while this upgrade is owned. E.g. -10 for something like Carrier Pigeon.",
    )
    discounted_spells = models.ManyToManyField(
        Spell, blank=True, related_name="discounting_upgrades",
        help_text="Specific spells whose casting cost is affected by spell_cost_modifier below, "
                   "for any wizard who owns this upgrade and has learned that spell.",
    )
    spell_cost_modifier = models.IntegerField(
        default=0,
        help_text="Casting cost added to (or, if negative, subtracted from) each spell in "
                   "discounted_spells above, while this upgrade is owned.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Player-owned wizard
# ---------------------------------------------------------------------------
XP_COST_PER_POINT = 100

class Wizard(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="wizards", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100, default="Unnamed Wizard")
    school = models.ForeignKey(
        School, null=True, blank=True, related_name="wizards", on_delete=models.SET_NULL,
        help_text="Chosen when the wizard is created. Determines the casting-cost modifier for spells outside this school.",
    )

    level = models.PositiveSmallIntegerField(default=1)
    experience = models.PositiveIntegerField(default=0)
    gold = models.PositiveIntegerField(default=400, help_text="Wizards start with 400gc.")

    current_health = models.SmallIntegerField(default=16)
    move = models.PositiveSmallIntegerField(default=6)
    fight = models.SmallIntegerField(default=2)
    shoot = models.SmallIntegerField(default=0)
    armour = models.PositiveSmallIntegerField(default=10)
    will = models.SmallIntegerField(default=4)
    health = models.PositiveSmallIntegerField(default=16)

    home_base_type = models.ForeignKey(
        HomeBaseType, null=True, blank=True, related_name="wizards", on_delete=models.SET_NULL
    )
    home_base_upgrades = models.ManyToManyField(HomeBaseUpgrade, blank=True, related_name="wizards")

    spells = models.ManyToManyField(Spell, through="WizardSpell", related_name="known_by_wizards")
    items = models.ManyToManyField(Item, through="WizardItem", related_name="owned_by_wizards")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (Lv {self.level})"

    @property
    def total_treasures(self):
        return self.games.aggregate(total=models.Sum("treasures_earned"))["total"] or 0

    @property
    def troop_cost_modifier_total(self):
        return sum(u.troop_cost_modifier for u in self.home_base_upgrades.all())

    def effective_hire_cost(self, soldier_type):
        return max(0, soldier_type.hire_cost + self.troop_cost_modifier_total)

    def spend_experience(self, amount):
        """Deduct `amount` XP, leveling up by 1 for every full 100xp spent
        (every XP-charging action in this app always spends in multiples
        of XP_COST_PER_POINT, so this stays exact). Returns False and
        makes no changes if the wizard can't afford it."""
        if amount <= 0:
            return True
        if amount > self.experience:
            return False
        self.experience -= amount
        self.level += amount // 100
        return True


class Apprentice(models.Model):
    """
    Every wizard has exactly one apprentice. By default an apprentice's
    stats mirror the wizard's, except -2 health and -2 will, but they can
    be edited independently afterwards.
    """
    wizard = models.OneToOneField(Wizard, related_name="apprentice", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="Apprentice")

    current_health = models.SmallIntegerField(default=14)
    move = models.PositiveSmallIntegerField(default=6)
    fight = models.SmallIntegerField(default=2)
    shoot = models.SmallIntegerField(default=0)
    armour = models.PositiveSmallIntegerField(default=10)
    will = models.SmallIntegerField(default=2)
    health = models.PositiveSmallIntegerField(default=14)

    @classmethod
    def default_for_wizard(cls, wizard):
        """Build an (unsaved) apprentice derived from a wizard's current stats."""
        return cls(
            wizard=wizard,
            name=f"{wizard.name}'s Apprentice",
            move=wizard.move,
            fight=wizard.fight,
            shoot=wizard.shoot,
            armour=wizard.armour,
            will=max(0, wizard.will - 2),
            health=max(1, wizard.health - 2),
            current_health=max(1, wizard.health - 2),
        )

    def __str__(self):
        return f"{self.name} (apprentice of {self.wizard.name})"


class WizardSpell(models.Model):
    """
    A spell the wizard has actually learned (grimoires that haven't been
    learned yet are tracked as Items, not here).

    The base casting cost comes from Spell.base_casting_cost (admin-only).
    The school-alignment modifier is computed automatically from the
    wizard's school vs. the spell's school. Rather than editing the final
    cost directly, the wizard invests points into a spell (e.g. from
    leveling up) which lower it: final = base + modifier - points_invested.
    """
    wizard = models.ForeignKey(Wizard, related_name="wizard_spells", on_delete=models.CASCADE)
    spell = models.ForeignKey(Spell, related_name="wizard_links", on_delete=models.CASCADE)
    points_invested = models.PositiveSmallIntegerField(
        default=0, help_text="Points spent lowering this spell's casting cost."
    )

    class Meta:
        unique_together = ("wizard", "spell")

    @property
    def base_casting_cost(self):
        return self.spell.base_casting_cost

    @property
    def casting_modifier(self):
        return compute_casting_modifier(self.wizard.school, self.spell.school)

    @property
    def computed_casting_cost(self):
        """Base + modifier, before any points are spent or upgrades applied."""
        return self.base_casting_cost + self.casting_modifier

    @property
    def upgrade_discount(self):
        """Sum of spell_cost_modifier from any owned home base upgrade that targets this spell."""
        total = 0
        for upgrade in self.wizard.home_base_upgrades.all():
            if upgrade.discounted_spells.filter(id=self.spell_id).exists():
                total += upgrade.spell_cost_modifier
        return total

    @property
    def final_casting_cost(self):
        """Base + modifier + upgrade discount - points invested, floored at 0."""
        return max(0, self.computed_casting_cost + self.upgrade_discount - self.points_invested)

    def __str__(self):
        return f"{self.wizard} - {self.spell}"


class WizardItem(models.Model):
    LOCATION_CHOICES = [
        ("wizard", "Carried by Wizard"),
        ("apprentice", "Carried by Apprentice"),
        ("vault", "Vault"),
    ]
    wizard = models.ForeignKey(Wizard, related_name="wizard_items", on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name="wizard_links", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    location = models.CharField(max_length=16, choices=LOCATION_CHOICES, default="vault")

    class Meta:
        unique_together = ("wizard", "item", "location")

    def __str__(self):
        return f"{self.wizard} - {self.item} x{self.quantity} ({self.get_location_display()})"


# ---------------------------------------------------------------------------
# NPC mortal enemy — each wizard has their own, not a global one
# ---------------------------------------------------------------------------

class MortalEnemy(models.Model):
    wizard = models.OneToOneField(Wizard, related_name="mortal_enemy", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="Mortal Enemy")
    type = models.CharField(max_length=64, default="humanoid")
    current_health = models.SmallIntegerField(default=16)
    move = models.PositiveSmallIntegerField(default=6)
    fight = models.SmallIntegerField(default=2)
    shoot = models.SmallIntegerField(default=0)
    armour = models.PositiveSmallIntegerField(default=10)
    will = models.SmallIntegerField(default=4)
    health = models.PositiveSmallIntegerField(default=16)

    items = models.ManyToManyField(Item, blank=True, related_name="mortal_enemies")

    ranged_attack_primary = models.ForeignKey(
        Spell, null=True, blank=True, related_name="+", on_delete=models.SET_NULL
    )
    ranged_attack_secondary = models.ForeignKey(
        Spell, null=True, blank=True, related_name="+", on_delete=models.SET_NULL
    )
    utility_primary = models.ForeignKey(
        Spell, null=True, blank=True, related_name="+", on_delete=models.SET_NULL
    )
    utility_secondary = models.ForeignKey(
        Spell, null=True, blank=True, related_name="+", on_delete=models.SET_NULL
    )
    out_of_game_primary = models.ForeignKey(
        Spell, null=True, blank=True, related_name="+", on_delete=models.SET_NULL
    )
    out_of_game_secondary = models.ForeignKey(
        Spell, null=True, blank=True, related_name="+", on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Warbands (the hired soldiers belonging to a Wizard or a MortalEnemy)
# ---------------------------------------------------------------------------

class Warband(models.Model):
    name = models.CharField(max_length=100, default="Warband")
    wizard = models.OneToOneField(
        Wizard, null=True, blank=True, related_name="warband", on_delete=models.CASCADE
    )
    mortal_enemy = models.OneToOneField(
        MortalEnemy, null=True, blank=True, related_name="warband", on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(wizard__isnull=False, mortal_enemy__isnull=True)
                    | models.Q(wizard__isnull=True, mortal_enemy__isnull=False)
                ),
                name="warband_belongs_to_exactly_one_owner",
            )
        ]

    def __str__(self):
        return self.name


class Soldier(models.Model):
    warband = models.ForeignKey(Warband, related_name="soldiers", on_delete=models.CASCADE)
    soldier_type = models.ForeignKey(SoldierType, related_name="soldiers", on_delete=models.PROTECT)
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(
        null=True, blank=True, default=None,
        help_text="A short paragraph about this warband member, if any.",
    )
    current_health = models.SmallIntegerField(default=10)
    price_paid = models.PositiveIntegerField(
        default=0, help_text="Gold crowns paid to hire this soldier (refunded in full when sold)."
    )

    # Optional per-soldier overrides of the soldier type's base stats.
    move = models.PositiveSmallIntegerField(null=True, blank=True)
    fight = models.SmallIntegerField(null=True, blank=True)
    shoot = models.SmallIntegerField(null=True, blank=True)
    armour = models.PositiveSmallIntegerField(null=True, blank=True)
    will = models.SmallIntegerField(null=True, blank=True)
    health = models.PositiveSmallIntegerField(null=True, blank=True)

    items = models.ManyToManyField(Item, blank=True, related_name="soldiers")

    def effective_stat(self, stat_name):
        override = getattr(self, stat_name)
        if override is not None:
            return override
        return getattr(self.soldier_type, stat_name)

    @property
    def effective_move(self):
        return self.effective_stat("move")

    @property
    def effective_fight(self):
        return self.effective_stat("fight")

    @property
    def effective_shoot(self):
        return self.effective_stat("shoot")

    @property
    def effective_armour(self):
        return self.effective_stat("armour")

    @property
    def effective_will(self):
        return self.effective_stat("will")

    @property
    def effective_health(self):
        return self.effective_stat("health")

    def __str__(self):
        return self.name or f"{self.soldier_type} #{self.pk}"


# ---------------------------------------------------------------------------
# Purchase ledger — lets a wizard undo a gold-spending action for a refund
# ---------------------------------------------------------------------------

class Purchase(models.Model):
    KIND_CHOICES = [
        ("soldier", "Soldier Hire"),
        ("home_base_upgrade", "Home Base Upgrade"),
    ]
    wizard = models.ForeignKey(Wizard, related_name="purchases", on_delete=models.CASCADE)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    amount = models.PositiveIntegerField(help_text="Gold crowns spent.")
    description = models.CharField(max_length=200)

    # Exactly one of these is set, matching `kind`. Deleting the underlying
    # soldier (e.g. via sell/retire) cascades away the purchase record too,
    # so "Undo" only ever shows purchases that are still reversible.
    soldier = models.ForeignKey(
        Soldier, null=True, blank=True, related_name="purchase_record", on_delete=models.CASCADE
    )
    home_base_upgrade = models.ForeignKey(
        HomeBaseUpgrade, null=True, blank=True, related_name="purchase_records", on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.description} ({self.amount}gc)"


# ---------------------------------------------------------------------------
# Games — one record per scenario played, tabbed on the wizard's page
# ---------------------------------------------------------------------------

class Game(models.Model):
    wizard = models.ForeignKey(Wizard, related_name="games", on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True, help_text="Optional label, e.g. 'The Frozen Vault'.")

    treasures_earned = models.PositiveIntegerField(default=0)
    gold_earned = models.PositiveIntegerField(default=0)
    items_earned = models.TextField(blank=True, help_text="Items found from treasure this game.")
    monsters_killed = models.PositiveIntegerField(default=0)
    successful_spells = models.PositiveIntegerField(default=0)
    unsuccessful_spells = models.PositiveIntegerField(default=0)
    bonus_xp = models.PositiveIntegerField(default=0)
    total_xp = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        computed = (
            self.successful_spells * 10
            + self.unsuccessful_spells * 5
            + self.monsters_killed * 5
            + self.bonus_xp
        )
        self.total_xp = min(300, computed)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Game #{self.pk}"



# ---------------------------------------------------------------------------
# Treasure tables — admin-managed reference grids of arbitrary size
# ---------------------------------------------------------------------------

class TreasureTable(models.Model):
    """An admin-managed table (e.g. the game's core treasure table),
    rendered as a grid. No public create/edit form — see /admin. `matrix`
    is a list of rows, each row a list of cell values, so the grid can be
    any size."""
    title = models.CharField(max_length=100, unique=True)
    matrix = models.JSONField(
        default=list, blank=True,
        help_text='A list of rows, each row a list of cells, e.g. [["Roll", "Result"], ["1-5", "Nothing"]].',
    )
    is_base = models.BooleanField(
        default=False,
        help_text="The table shown by default before a search is typed. Only one table should have "
                   "this checked — checking it here automatically unchecks it on every other table.",
    )

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_base:
            TreasureTable.objects.exclude(pk=self.pk).update(is_base=False)

    def __str__(self):
        return self.title
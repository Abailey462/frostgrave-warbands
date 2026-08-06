# Frostgrave Warband Ledger

A Django web app for managing Frostgrave wizards and warbands: editing stats,
tracking gold/experience, managing spells and items, and hiring/dismissing
soldiers. Ships as a Docker Compose stack (Django + Postgres) with data that
persists across container restarts via a named Postgres volume.

## Quick start

```bash
cp .env.example .env
# edit .env if you want a real SECRET_KEY / admin password
docker compose up --build
```

The app will be available at http://localhost:8000/. On first boot the
entrypoint script runs migrations, seeds reference data (schools, spells,
items, soldier types, home base options) plus a demo wizard/warband and the
mortal enemy encounter, and (if `DJANGO_SUPERUSER_USERNAME`/`PASSWORD` are
set in `.env`) creates a Django admin superuser.

- App: http://localhost:8000/
- Admin: http://localhost:8000/admin/
- API: http://localhost:8000/api/ (DRF browsable API, session-authenticated)

Data lives in the `postgres_data` Docker volume, so `docker compose down` and
`docker compose up` again will preserve everything. Use
`docker compose down -v` if you want to wipe the database.

The demo wizard is owned by a placeholder user (`demo_wizard_owner`) with no
usable password by default — create a real user via `/admin/` or
`python manage.py createsuperuser` (run inside the `web` container) and
reassign wizards to it, or just create a fresh wizard from the "New Wizard"
page after logging in.

## Schema overview

The original YAML export used loose, ad-hoc structures (dicts keyed by
soldier slot names, spell "cost" values mixed into a flat dict, etc). This
app normalizes that into a relational schema:

- **School** / **Spell** — each spell belongs to one school and has an
  admin-only `base_casting_cost` (its difficulty before any modifier) plus
  an `xp_cost` to learn it. **SchoolAffinity** captures the school-to-school
  alignment matrix (2 = aligned, 4 = neutral, 6 = opposed), seeded in both
  directions so every school has a full row against every other.
- **Wizard.school** — chosen once, when the wizard is created. It
  determines the casting-cost modifier applied to spells outside that
  school: 0 for the wizard's own school, otherwise the affinity value
  between the wizard's school and the spell's school.
- **WizardSpell** — a learned spell's `base_casting_cost` and
  `casting_modifier` are read-only, computed from the Spell and the
  wizard's school. `final_casting_cost` starts as base + modifier but is
  freely editable afterward (e.g. when the wizard levels up). Learned
  spells are grouped by school in the editor, each row showing
  Base + Modifier = Computed alongside the editable Final cost.
- **Item** — equipment/treasury items; an item can optionally `grants_spell`
  (e.g. a grimoire that teaches a specific spell).
- **SoldierType** — a hireable template (thug, archer, thief, infantryman)
  with base stats and starting items.
- **HomeBaseType** / **HomeBaseUpgrade** — home base options and upgrades.
- **Wizard** — a player's wizard: stats, level, experience, gold, home base
  (set later in the editor, not at creation), and (through join tables)
  known spells (`WizardSpell`, each with an editable per-wizard
  `casting_cost`) and items (`WizardItem`, each with a `location` of
  `wizard`, `apprentice`, or `vault` — so the UI can show exactly whose pack
  an item is in). Grimoires (spells not yet learned) are tracked as
  `WizardItem` rows, not `WizardSpell` — a grimoire is an `Item` with
  `grants_spell` pointing at the spell it teaches.
- **HomeBaseType** / **HomeBaseUpgrade** — a wizard picks one home base type
  and can purchase any number of upgrades (each with a gold `cost`),
  deducted from the wizard's treasury on purchase, from a dedicated Home
  Base section on the wizard's page.
- **Apprentice** — every wizard has exactly one (`Wizard.apprentice`,
  one-to-one). On creation its stats default to the wizard's own stats with
  -2 health and -2 will, then can be edited independently from the wizard's
  detail page.
- **Warband** — belongs to exactly one of a `Wizard` or a `MortalEnemy`
  (enforced by a DB constraint) and contains **Soldier** rows, each linked to
  a `SoldierType` (which carries a `hire_cost`) with optional per-soldier
  stat overrides and its own item list. Hiring a soldier deducts its cost
  from the wizard's gold and records it on `Soldier.price_paid`; **selling**
  a soldier refunds that amount, **retiring** does not — so warbands are
  editable rows in the database instead of a fixed dict of
  `solder1..solderN` keys, with real gold accounting behind hiring/removal.
- **MortalEnemy** — each wizard has their own mortal enemy
  (`Wizard.mortal_enemy`, one-to-one, not shared globally), with its own
  stat block, item list, spell slots (ranged attack / utility /
  out-of-game, primary & secondary), and its own `Warband`. Mortal enemies
  do not have an apprentice or a treasury, so their soldiers are hired for
  free and only support a simple dismiss. Edited from a "Mortal Enemy" tab
  on the wizard's detail page, alongside a "My Warband" tab for the
  wizard's own soldiers.
- **Purchase** — every gold-spending action (hiring a soldier, buying a
  home base upgrade) logs a `Purchase` row. The wizard's page has a
  Purchase History list with an **Undo** button per entry, which reverses
  the action (deletes the soldier / removes the upgrade) and refunds the
  gold in full. Selling or retiring a soldier directly also cleans up its
  Purchase row automatically, so Undo only ever shows purchases that are
  still genuinely reversible.

## Accounts

New users can register directly from the app at `/signup/` (also linked
from the login page and the top nav) — no admin access required. Signing
up logs you in immediately and drops you at your (empty) wizard list.

## Wizard creation flow

Creating a wizard is two steps:

1. **Basics** — name, school, stats, and whether to hire an apprentice.
   Wizards start with 400gc; hiring an apprentice costs 100gc up front
   (leaving 300gc), and can be skipped to keep the full 400gc.
2. **Starting spells** — choose 8 spells: 3 from your wizard's primary
   school, 3 from schools aligned to it (affinity 2, no two spells from the
   same school), and 2 from neutral schools (affinity 4, same
   no-duplicates rule). Casting cost for each is computed automatically
   from the spell's base cost plus your school's modifier against it.

## Games

Each wizard's page has a Games tab strip at the very top. Add a new game
with "+ Add Game", switch between existing games by clicking their tab, and
edit any game's treasures earned, gold earned, items earned, monsters
killed, successful/unsuccessful spells, bonus XP, and total XP — all
editable — or delete the game entirely. Treasures earned across all of a
wizard's games are summed into `Wizard.total_treasures`, shown in the
Treasury & Experience panel.

## Monsters

`MonsterType` (e.g. Giant Rat, Construct) is admin-only — there's no
public create/edit form, matching how monster stat blocks are usually
fixed reference data rather than something a player edits mid-campaign.
They're browsable and searchable from a "Monsters" tab next to "My
Warband" and "Mortal Enemy" on every wizard's page, showing each
monster's stats, description, and any items it carries (with their
descriptions).

## Spell casting cost mechanics

A learned spell's final casting cost is never edited directly. Instead:
`final = Spell.base_casting_cost (admin-set) + school-alignment modifier
(computed) + home base upgrade effect (computed) − points_invested
(player-editable)`. The editor shows the full breakdown as a chip trail
with only the Points field editable — handy for representing improvements
from leveling up without losing track of the underlying math. A read-only
"All Spells" tab (next to Monsters) lets you search every spell's *base*
cost with no modifiers applied, for reference.

## Home base upgrade effects

Beyond their flavor description, a `HomeBaseUpgrade` can carry two kinds
of numeric effects, both admin-only (set when the upgrade is created or
edited in `/admin`):

- **`troop_cost_modifier`** — applied to hiring *every* soldier type while
  the wizard owns the upgrade (negative = cheaper). `carrier_pidgeon` is
  seeded with -10, matching its original "10gc less" description.
- **`spell_cost_modifier`** + **`discounted_spells`** — applied only to a
  fixed set of spells the admin selects when creating the upgrade (never
  chosen by the player). `runed_tome` is seeded discounting 3 specific
  necromancer spells by -2 casting cost each.

Both effects are reflected live: hiring a soldier shows and charges the
discounted price, and a learned spell's cost breakdown shows the upgrade's
contribution alongside the school modifier and invested points.

## Apprentices and wizard deletion

An apprentice can be hired later (100gc) from the Apprentice section if
the wizard didn't start with one, and retired at any time (no refund) —
not just decided once at creation. A wizard can also be deleted entirely
from a "Danger Zone" section on their page (or a Delete button on the
wizard list), which cascades to their apprentice, mortal enemy, warband,
spells, items, purchases, and games. Both actions require confirmation.

### Data issues fixed during ingestion

- `school_alignments.yaml` had a YAML syntax error under `witch` —
  `illusionist:40` (no space) failed to parse. Normalized to `4`, consistent
  with the rest of that matrix. Separately, the file only lists 8 of the 10
  schools as top-level keys (`soothsayer` and `summoner` never appear as a
  source, only as a target of other schools' entries). Since the matrix is
  symmetric everywhere it does overlap, affinities are seeded in both
  directions so a wizard can pick soothsayer or summoner as their own
  school and still get correct modifiers against every other school.
- `items.yaml` defines `light_armour`, but `soldier_stats.yaml` referenced
  `"light armour"` (space instead of underscore) in the archer's item list —
  normalized to `light_armour` throughout.
- `soldier_stats.yaml`'s `infantryman` entry had all stats set to `null`.
  Reasonable placeholder stats are seeded (editable in `/admin/`) so the
  soldier type isn't broken.
- The warband dicts used typo'd keys (`solder1`, `solder2`, ...). Soldiers
  are now individual DB rows rather than dict keys, so this class of typo
  can't happen going forward.
- `grimoire` in `items.yaml` had a generic nested `spell` field; it's now a
  real FK (`Item.grants_spell`). Since a grimoire only ever teaches one
  specific spell, one grimoire `Item` is seeded per spell it can grant
  (`grimoire_bone_dart`, `grimoire_time_store`, `grimoire_time_walk` —
  matching the wizard's vault contents), rather than one generic item.

## Local development (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DB_HOST=localhost DB_NAME=frostgrave DB_USER=frostgrave DB_PASSWORD=frostgrave
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

## Project layout

```
frostgrave_project/   Django settings, root URLs, WSGI
warbands/              Models, admin, forms, views, templates, DRF API
  management/commands/seed_data.py   Seeds reference + demo data from the source YAML
docker-compose.yml      web (Django/Gunicorn) + db (Postgres) with a named volume
Dockerfile, entrypoint.sh
```

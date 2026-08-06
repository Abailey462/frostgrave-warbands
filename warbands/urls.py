from django.urls import path

from . import views

urlpatterns = [
    path("", views.warband_list, name="warband-list"),
    path("signup/", views.signup, name="signup"),
    path("wizards/new/", views.wizard_create, name="wizard-create"),
    path("wizards/<int:wizard_id>/choose-spells/", views.wizard_choose_starting_spells, name="wizard-choose-spells"),
    path("wizards/<int:wizard_id>/", views.wizard_detail, name="wizard-detail"),
    path("wizards/<int:wizard_id>/update-stats/", views.wizard_update_stats, name="wizard-update-stats"),
    path("wizards/<int:wizard_id>/delete/", views.wizard_delete, name="wizard-delete"),
    path("wizards/<int:wizard_id>/adjust-gold-xp/", views.wizard_adjust_gold_xp, name="wizard-adjust-gold-xp"),

    # Home base
    path("wizards/<int:wizard_id>/home-base/set/", views.wizard_set_home_base, name="wizard-set-home-base"),
    path("wizards/<int:wizard_id>/home-base/buy-upgrade/", views.wizard_buy_home_base_upgrade, name="wizard-buy-home-base-upgrade"),

    # Items
    path("wizards/<int:wizard_id>/add-item/", views.wizard_add_item, name="wizard-add-item"),
    path("wizards/<int:wizard_id>/remove-item/<int:wizard_item_id>/", views.wizard_remove_item, name="wizard-remove-item"),

    # Spells
    path("wizards/<int:wizard_id>/add-spell/", views.wizard_add_spell, name="wizard-add-spell"),
    path("wizards/<int:wizard_id>/remove-spell/<int:wizard_spell_id>/", views.wizard_remove_spell, name="wizard-remove-spell"),
    path("wizards/<int:wizard_id>/spell/<int:wizard_spell_id>/points/", views.wizard_spell_update_points, name="wizard-spell-update-points"),

    # Wizard's own warband
    path("wizards/<int:wizard_id>/add-soldier/", views.warband_add_soldier, name="warband-add-soldier"),
    path("wizards/<int:wizard_id>/sell-soldier/<int:soldier_id>/", views.warband_sell_soldier, name="warband-sell-soldier"),
    path("wizards/<int:wizard_id>/retire-soldier/<int:soldier_id>/", views.warband_retire_soldier, name="warband-retire-soldier"),
    path("wizards/<int:wizard_id>/soldier/<int:soldier_id>/health/", views.soldier_update_health, name="soldier-update-health"),
    path("wizards/<int:wizard_id>/soldier/<int:soldier_id>/description/", views.soldier_update_description, name="soldier-update-description"),

    # Purchases (undo)
    path("wizards/<int:wizard_id>/purchase/<int:purchase_id>/undo/", views.purchase_undo, name="purchase-undo"),

    # Games
    path("wizards/<int:wizard_id>/games/new/", views.game_create, name="game-create"),
    path("wizards/<int:wizard_id>/games/<int:game_id>/update/", views.game_update, name="game-update"),
    path("wizards/<int:wizard_id>/games/<int:game_id>/delete/", views.game_delete, name="game-delete"),

    # Apprentice
    path("wizards/<int:wizard_id>/apprentice/update-stats/", views.apprentice_update_stats, name="apprentice-update-stats"),
    path("wizards/<int:wizard_id>/apprentice/hire/", views.apprentice_hire, name="apprentice-hire"),
    path("wizards/<int:wizard_id>/apprentice/retire/", views.apprentice_retire, name="apprentice-retire"),

    # Mortal enemy
    path("wizards/<int:wizard_id>/mortal-enemy/update-stats/", views.mortal_enemy_update_stats, name="mortal-enemy-update-stats"),
    path("wizards/<int:wizard_id>/mortal-enemy/add-item/", views.mortal_enemy_add_item, name="mortal-enemy-add-item"),
    path("wizards/<int:wizard_id>/mortal-enemy/remove-item/<int:item_id>/", views.mortal_enemy_remove_item, name="mortal-enemy-remove-item"),
    path("wizards/<int:wizard_id>/mortal-enemy/add-soldier/", views.mortal_enemy_add_soldier, name="mortal-enemy-add-soldier"),
    path("wizards/<int:wizard_id>/mortal-enemy/remove-soldier/<int:soldier_id>/", views.mortal_enemy_remove_soldier, name="mortal-enemy-remove-soldier"),
    path("wizards/<int:wizard_id>/mortal-enemy/soldier/<int:soldier_id>/health/", views.mortal_enemy_soldier_update_health, name="mortal-enemy-soldier-update-health"),
    path("wizards/<int:wizard_id>/mortal-enemy/soldier/<int:soldier_id>/description/", views.mortal_enemy_soldier_update_description, name="mortal-enemy-soldier-update-description"),
]

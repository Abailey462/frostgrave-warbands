from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.register("wizards", api_views.WizardViewSet, basename="api-wizard")
router.register("soldiers", api_views.SoldierViewSet, basename="api-soldier")
router.register("items", api_views.ItemViewSet, basename="api-item")
router.register("spells", api_views.SpellViewSet, basename="api-spell")
router.register("soldier-types", api_views.SoldierTypeViewSet, basename="api-soldier-type")

urlpatterns = router.urls

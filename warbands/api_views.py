from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Item, Soldier, SoldierType, Spell, Warband, Wizard
from .serializers import (
    ItemSerializer,
    SoldierSerializer,
    SoldierTypeSerializer,
    SpellSerializer,
    WizardSerializer,
)


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        wizard = obj if isinstance(obj, Wizard) else getattr(obj, "wizard", None)
        return wizard is not None and wizard.owner_id == request.user.id


class WizardViewSet(viewsets.ModelViewSet):
    serializer_class = WizardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Wizard.objects.filter(owner=self.request.user).select_related(
            "apprentice", "mortal_enemy", "school"
        ).prefetch_related(
            "wizard_items__item", "wizard_spells__spell", "warband__soldiers__soldier_type",
            "mortal_enemy__items", "mortal_enemy__warband__soldiers__soldier_type",
            "purchases", "games",
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def adjust_gold(self, request, pk=None):
        wizard = self.get_object()
        delta = int(request.data.get("delta", 0))
        wizard.gold = max(0, wizard.gold + delta)
        wizard.save(update_fields=["gold"])
        return Response(WizardSerializer(wizard).data)

    @action(detail=True, methods=["post"])
    def adjust_experience(self, request, pk=None):
        wizard = self.get_object()
        delta = int(request.data.get("delta", 0))
        wizard.experience = max(0, wizard.experience + delta)
        wizard.save(update_fields=["experience"])
        return Response(WizardSerializer(wizard).data)


class SoldierViewSet(viewsets.ModelViewSet):
    serializer_class = SoldierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Soldier.objects.filter(warband__wizard__owner=self.request.user)

    def perform_create(self, serializer):
        warband_id = self.request.data.get("warband")
        warband = Warband.objects.get(id=warband_id, wizard__owner=self.request.user)
        serializer.save(warband=warband)


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]


class SpellViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Spell.objects.select_related("school").all()
    serializer_class = SpellSerializer
    permission_classes = [permissions.IsAuthenticated]


class SoldierTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SoldierType.objects.prefetch_related("base_items").all()
    serializer_class = SoldierTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

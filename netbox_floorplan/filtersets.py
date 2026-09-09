from django.db.models import Q

from netbox.filtersets import NetBoxModelFilterSet
from .models import Floorplan, FloorplanImage


class FloorplanFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Floorplan
        fields = ['id', 'site', 'location']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(site__name__icontains=value) |
            Q(location__name__icontains=value) |
            Q(assigned_image__name__icontains=value)
        )


class FloorplanImageFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = FloorplanImage
        fields = ['id', 'name', 'external_url']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(external_url__icontains=value) |
            Q(comments__icontains=value)
        )

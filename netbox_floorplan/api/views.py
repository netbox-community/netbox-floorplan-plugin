from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets, models
from .serializers import FloorplanSerializer, FloorplanImageSerializer


class FloorplanViewSet(NetBoxModelViewSet):
    queryset = models.Floorplan.objects.all()
    serializer_class = FloorplanSerializer
    filterset_class = filtersets.FloorplanFilterSet


class FloorplanImageViewSet(NetBoxModelViewSet):
    queryset = models.FloorplanImage.objects.prefetch_related('tags')
    serializer_class = FloorplanImageSerializer

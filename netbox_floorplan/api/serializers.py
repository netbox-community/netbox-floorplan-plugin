from rest_framework import serializers
from netbox.api.serializers import NetBoxModelSerializer
from ..models import Floorplan, FloorplanImage


class FloorplanImageSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_floorplan-api:floorplanimage-detail')
    file_url = serializers.SerializerMethodField(read_only=True)

    def get_file_url(self, obj):
        """
        The storage backend's own URL for the uploaded file.

        `file` uses DRF's default representation, which is an absolute URL built from the
        request. That bakes in whatever hostname NetBox saw, which breaks when NetBox is
        behind a reverse proxy serving a different hostname.

        This field returns the storage's URL instead:

        * With local storage it is MEDIA_URL-relative (e.g. `/media/...`), so the browser
          resolves it against whatever origin it is actually using.
        * With remote storage (S3, a CDN) the storage URL is already absolute and is
          returned unchanged, so those deployments keep working.

        The floorplan canvas uses this field rather than `file`. `file` is left alone so
        existing API consumers are unaffected.
        """
        if not obj.file:
            return None
        return obj.file.url

    class Meta:
        model = FloorplanImage
        fields = ['id', 'url', 'display', 'name', 'file', 'file_url', 'external_url', 'filename', 'comments', 'tags', 'custom_fields', 'created', 'last_updated']
        brief_fields = ['id', 'url', 'display', 'name', 'file', 'file_url', 'filename', 'external_url']


class FloorplanSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_floorplan-api:floorplan-detail')
    assigned_image = FloorplanImageSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = Floorplan
        fields = ['id', 'url', 'display', 'site', 'location', 'assigned_image',
                  'width', 'height', 'tags', 'custom_fields', 'created',
                  'last_updated', 'canvas', 'measurement_unit']
        # Without this, ?brief=1 returns every field, including the whole canvas.
        brief_fields = ['id', 'url', 'display']

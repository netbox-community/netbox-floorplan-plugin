from netbox.forms import NetBoxModelForm
from .models import Floorplan, FloorplanImage
from dcim.models import Rack, Device
from utilities.forms.rendering import FieldSet
from utilities.forms.fields import CommentField


class FloorplanImageForm(NetBoxModelForm):

    comments = CommentField()

    fieldsets = (
        FieldSet(('name', 'file', 'external_url', 'comments'), name='General'),
        FieldSet(('comments', 'tags'), name='')
    )

    class Meta:
        model = FloorplanImage
        fields = [
            'name',
            'file',
            'external_url'
        ]


class FloorplanForm(NetBoxModelForm):
    class Meta:
        model = Floorplan
        fields = ['site', 'location', 'assigned_image', 'width', 'height']


class FloorplanRackFilterForm(NetBoxModelForm):
    class Meta:
        model = Rack
        fields = ['name']


class FloorplanDeviceFilterForm(NetBoxModelForm):
    class Meta:
        model = Device
        fields = ['name']

import django_tables2 as tables

from netbox.tables import NetBoxTable
from .models import Floorplan, FloorplanImage

from dcim.models import Rack


class FloorplanImageTable(NetBoxTable):
    name = tables.Column(
        linkify=True,
    )

    class Meta(NetBoxTable.Meta):
        model = FloorplanImage
        fields = (
            'pk',
            'id',
            'name',
            'file'
        )


class FloorplanTable(NetBoxTable):

    class Meta(NetBoxTable.Meta):
        model = Floorplan
        fields = ('pk', 'site', 'location',
                  'assigned_image', 'width', 'height')
        default_columns = ('pk', 'site', 'location',
                           'assigned_image', 'width', 'height')


class FloorplanRackTable(NetBoxTable):

    name = tables.LinkColumn()

    actions = tables.TemplateColumn(template_code="""
    <a type="button" class="btn btn-sm btn-outline-info" onclick="add_floorplan_object(300, 500, '{{ record.outer_width }}', '{{ record.outer_depth}}', '{{ record.outer_unit }}', '#ea8fe', 30, '{{ record.id }}', '{{ record.name }}', 'rack', '{{ record.status }}')">Add Rack
    </a>
    """)

    class Meta(NetBoxTable.Meta):
        model = Rack
        fields = ('pk', 'name', 'u_height')
        default_columns = ('pk', 'name', 'u_height')
        row_attrs = {
            'id': lambda record: 'object_rack_{}'.format(record.pk),
        }


class FloorplanDeviceTable(NetBoxTable):

    name = tables.LinkColumn()

    actions = tables.TemplateColumn(template_code="""
    <a type="button" class="btn btn-sm btn-outline-info" onclick="add_floorplan_object(30, 50, 60, 60, '{{ record.outer_unit }}', '#ea8fe', 30, '{{ record.id }}', '{{ record.name }}', 'device', '{{ record.status }}', '{{ record.device_type.front_image }}')">Add Device
    </a>
    """)

    class Meta(NetBoxTable.Meta):
        model = Rack
        fields = ('pk', 'name', 'device_type')
        default_columns = ('pk', 'name', 'device_type')
        row_attrs = {
            'id': lambda record: 'object_device_{}'.format(record.pk),
        }

import django_tables2 as tables

from netbox.tables import NetBoxTable
from .models import Floorplan, FloorplanImage
from functools import cached_property

from dcim.models import Rack, Device


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
    embedded = True

    role = tables.TemplateColumn(
        # Show the role name if it exists, otherwise show "None" on the edit_floorplan view
        template_code="""
        {% if record.role %}
            {{ record.role.name }}
        {% else %}
            <span class="text-muted">None</span>
        {% endif %}
        """,
        verbose_name="Role"
    )

    # The outer dimensions are read through the rack_outer_js filter rather than directly
    # off the Rack, because Rack.outer_width / outer_depth / outer_unit are deprecated in
    # NetBox 4.7 and are to be inferred from the rack's RackType in v5.0.
    actions = tables.TemplateColumn(template_code="""
    {% load template_utils %}
    <div class="btn-group" role="group">
        {% if record.role and record.role.color %}
        <a type="button" class="btn btn-sm btn-outline-secondary" onclick="add_floorplan_object_simple(300, 500, {{ record|rack_outer_js:'width' }}, {{ record|rack_outer_js:'depth' }}, {{ record|rack_outer_js:'unit' }}, '#000000', 30, {{ record.id|js_str }}, {{ record.name|js_str }}, 'rack', {{ record.status|js_str }}, null)">Simple<br>Rack</a>
        <a type="button" class="btn btn-sm btn-outline-info ms-1" onclick="add_floorplan_object_advanced(300, 500, {{ record|rack_outer_js:'width' }}, {{ record|rack_outer_js:'depth' }}, {{ record|rack_outer_js:'unit' }}, '#{{ record.role.color }}', 30, {{ record.id|js_str }}, {{ record.name|js_str }}, 'rack', {{ record.status|js_str }}, {% if record.tenant %}{{ record.tenant|js_str }}{% else %}null{% endif %}, {{ record.role.name|js_str }}, null, '#000000')">Advanced<br>Rack</a>
        {% else %}
        <a type="button" class="btn btn-sm btn-outline-secondary" onclick="add_floorplan_object_simple(300, 500, {{ record|rack_outer_js:'width' }}, {{ record|rack_outer_js:'depth' }}, {{ record|rack_outer_js:'unit' }}, '#000000', 30, {{ record.id|js_str }}, {{ record.name|js_str }}, 'rack', {{ record.status|js_str }}, null)">Simple<br>Rack</a>
        <a type="button" class="btn btn-sm btn-outline-info ms-1" onclick="add_floorplan_object_advanced(300, 500, {{ record|rack_outer_js:'width' }}, {{ record|rack_outer_js:'depth' }}, {{ record|rack_outer_js:'unit' }}, '#000000', 30, {{ record.id|js_str }}, {{ record.name|js_str }}, 'rack', {{ record.status|js_str }}, {% if record.tenant %}{{ record.tenant|js_str }}{% else %}null{% endif %}, 'None', null, '#000000')">Advanced<br>Rack</a>
        {% endif %}
    </div>
    """, orderable=False)

    @cached_property
    def htmx_url(self):
        # no need to check for embedded as this table is always embedded
        return "/plugins/floorplan/floorplans/racks/"

    class Meta(NetBoxTable.Meta):
        model = Rack
        # Show the Rack name, role, and U-height in the table
        fields = ('pk', 'name', 'role', 'u_height')
        default_columns = ('pk', 'name', 'role', 'u_height')
        row_attrs = {
            'id': lambda record: 'object_rack_{}'.format(record.pk),
        }


class FloorplanDeviceTable(NetBoxTable):
    name = tables.LinkColumn()
    embedded = True

    actions = tables.TemplateColumn(template_code="""
    {% load template_utils %}
    <div class="btn-group" role="group">
        <a type="button" class="btn btn-sm btn-outline-secondary" onclick="add_floorplan_object_simple(30, 50, 60, 60, null, '#000000', 30, {{ record.id|js_str }}, {{ record.name|js_str }}, 'device', {{ record.status|js_str }}, {% if record.device_type.front_image %}{{ record.device_type.front_image.url|js_str }}{% else %}null{% endif %})">Simple<br>Device</a>
        <a type="button" class="btn btn-sm btn-outline-info ms-1" onclick="add_floorplan_object_advanced(30, 50, 60, 60, null, '#000000', 30, {{ record.id|js_str }}, {{ record.name|js_str }}, 'device', {{ record.status|js_str }}, {% if record.tenant %}{{ record.tenant|js_str }}{% else %}null{% endif %}, null, {% if record.device_type.front_image %}{{ record.device_type.front_image.url|js_str }}{% else %}null{% endif %}, '#6ea8fe')">Advanced<br>Device</a>
    </div>
    """, orderable=False)

    @cached_property
    def htmx_url(self):
        # no need to check for embedded as this table is always embedded
        return "/plugins/floorplan/floorplans/devices/"

    class Meta(NetBoxTable.Meta):
        model = Device
        fields = ('pk', 'name', 'device_type')
        default_columns = ('pk', 'name', 'device_type')
        row_attrs = {
            'id': lambda record: 'object_device_{}'.format(record.pk),
        }

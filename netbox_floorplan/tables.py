import django_tables2 as tables

from netbox.tables import NetBoxTable
from .models import Floorplan, FloorplanImage

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

    actions = tables.TemplateColumn(template_code="""
    <div class="btn-group" role="group">
        {% if record.role and record.role.color %}
        <a type="button" class="btn btn-sm btn-outline-secondary" onclick="add_floorplan_object_simple(300, 500, {% if record.outer_width %}{{ record.outer_width }}{% else %}null{% endif %}, {% if record.outer_depth %}{{ record.outer_depth }}{% else %}null{% endif %}, {% if record.outer_unit %}'{{ record.outer_unit }}'{% else %}null{% endif %}, '#000000', 30, '{{ record.id }}', '{{ record.name }}', 'rack', '{{ record.status }}', null)">Simple<br>Rack</a>
        <a type="button" class="btn btn-sm btn-outline-info ms-1" onclick="add_floorplan_object_advanced(300, 500, {% if record.outer_width %}{{ record.outer_width }}{% else %}null{% endif %}, {% if record.outer_depth %}{{ record.outer_depth }}{% else %}null{% endif %}, {% if record.outer_unit %}'{{ record.outer_unit }}'{% else %}null{% endif %}, '#{{ record.role.color }}', 30, '{{ record.id }}', '{{ record.name }}', 'rack', '{{ record.status }}', {% if record.tenant %}'{{ record.tenant }}'{% else %}null{% endif %}, '{{ record.role.name }}', null, '#000000')">Advanced<br>Rack</a>
        {% else %}
        <a type="button" class="btn btn-sm btn-outline-secondary" onclick="add_floorplan_object_simple(300, 500, {% if record.outer_width %}{{ record.outer_width }}{% else %}null{% endif %}, {% if record.outer_depth %}{{ record.outer_depth }}{% else %}null{% endif %}, {% if record.outer_unit %}'{{ record.outer_unit }}'{% else %}null{% endif %}, '#000000', 30, '{{ record.id }}', '{{ record.name }}', 'rack', '{{ record.status }}', null)">Simple<br>Rack</a>
        <a type="button" class="btn btn-sm btn-outline-info ms-1" onclick="add_floorplan_object_advanced(300, 500, {% if record.outer_width %}{{ record.outer_width }}{% else %}null{% endif %}, {% if record.outer_depth %}{{ record.outer_depth }}{% else %}null{% endif %}, {% if record.outer_unit %}'{{ record.outer_unit }}'{% else %}null{% endif %}, '#000000', 30, '{{ record.id }}', '{{ record.name }}', 'rack', '{{ record.status }}', {% if record.tenant %}'{{ record.tenant }}'{% else %}null{% endif %}, 'None', null, '#000000')">Advanced<br>Rack</a>
        {% endif %}
    </div>
    """, orderable=False)

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

    actions = tables.TemplateColumn(template_code="""
    <div class="btn-group" role="group">
        <a type="button" class="btn btn-sm btn-outline-secondary" onclick="add_floorplan_object_simple(30, 50, 60, 60, null, '#000000', 30, '{{ record.id }}', '{{ record.name }}', 'device', '{{ record.status }}', {% if record.device_type.front_image %}'{{ record.device_type.front_image }}'{% else %}null{% endif %})">Simple<br>Device</a>
        <a type="button" class="btn btn-sm btn-outline-info ms-1" onclick="add_floorplan_object_advanced(30, 50, 60, 60, null, '#000000', 30, '{{ record.id }}', '{{ record.name }}', 'device', '{{ record.status }}', {% if record.tenant %}'{{ record.tenant }}'{% else %}null{% endif %}, null, {% if record.device_type.front_image %}'{{ record.device_type.front_image }}'{% else %}null{% endif %}, '#6ea8fe')">Advanced<br>Device</a>
    </div>
    """, orderable=False)

    class Meta(NetBoxTable.Meta):
        model = Device
        fields = ('pk', 'name', 'device_type')
        default_columns = ('pk', 'name', 'device_type')
        row_attrs = {
            'id': lambda record: 'object_device_{}'.format(record.pk),
        }

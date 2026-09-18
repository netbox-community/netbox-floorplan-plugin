"""
Attribute panels for the plugin's object views.

These replace the hand-written attribute tables the detail templates used to carry.
"""
from django.utils.translation import gettext_lazy as _
from netbox.ui import attrs, panels


class FloorplanImagePanel(panels.ObjectAttributesPanel):
    title = _('Floorplan Image')

    name = attrs.TextAttr('name')
    # An image is either uploaded or referenced by URL, so one of these is always empty. The
    # template showed whichever applied and hid the other; both are listed here, with the
    # usual placeholder standing in for the one not in use.
    external_url = attrs.TemplatedAttr(
        'external_url',
        template_name='netbox_floorplan/inc/attrs/external_url.html',
        label=_('External URL'),
    )
    filename = attrs.TemplatedAttr(
        'filename',
        template_name='netbox_floorplan/inc/attrs/file_link.html',
        label=_('Filename'),
    )
    size = attrs.TemplatedAttr(
        'size',
        template_name='netbox_floorplan/inc/attrs/file_size.html',
        label=_('Size'),
    )

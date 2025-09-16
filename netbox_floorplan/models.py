from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel
from dcim.models import Rack, Device
from .utils import file_upload


class FloorplanImage(NetBoxModel):
    """
    A Floorplan Image is effectively a background image
    """
    name = models.CharField(
        help_text='Can be used to quickly identify a particular image',
        max_length=128,
        blank=False,
        null=False
    )

    file = models.FileField(
        upload_to=file_upload,
        blank=True
    )

    external_url = models.URLField(
        blank=True,
        max_length=255
    )

    comments = models.TextField(
        blank=True
    )

    def get_absolute_url(self):
        return reverse('plugins:netbox_floorplan:floorplanimage', args=[self.pk])

    def __str__(self):
        return f'{self.name}'

    class Meta:
        ordering = ('name',)

    @property
    def size(self):
        """
        Wrapper around `document.size` to suppress an OSError in case the file is inaccessible. Also opportunistically
        catch other exceptions that we know other storage back-ends to throw.
        """
        expected_exceptions = [OSError]

        try:
            from botocore.exceptions import ClientError
            expected_exceptions.append(ClientError)
        except ImportError:
            pass

        try:
            return self.file.size
        except NameError:
            return None

    @property
    def filename(self):
        filename = self.file.name.rsplit('/', 1)[-1]
        return filename

    def clean(self):
        super().clean()

        # Must have an uploaded document or an external URL. cannot have both
        if not self.file and self.external_url == '':
            raise ValidationError("A document must contain an uploaded file or an external URL.")
        if self.file and self.external_url:
            raise ValidationError("A document cannot contain both an uploaded file and an external URL.")

    def delete(self, *args, **kwargs):

        # Check if its a document or a URL
        if self.external_url == '':

            _name = self.file.name

            # Delete file from disk
            super().delete(*args, **kwargs)
            self.file.delete(save=False)

            # Restore the name of the document as it's re-used in the notifications later
            self.file.name = _name
        else:
            # Straight delete of external URL
            super().delete(*args, **kwargs)


class Floorplan(NetBoxModel):

    site = models.ForeignKey(
        to='dcim.Site',
        blank=True,
        null=True,
        on_delete=models.PROTECT
    )
    location = models.ForeignKey(
        to='dcim.Location',
        blank=True,
        null=True,
        on_delete=models.PROTECT
    )

    assigned_image = models.ForeignKey(
        to='FloorplanImage',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    measurement_choices = [
        ('ft', 'Feet'),
        ('m', 'Meters')
    ]
    measurement_unit = models.CharField(
        max_length=2,
        choices=measurement_choices,
        default='m'
    )

    canvas = models.JSONField(default=dict)

    class Meta:
        ordering = ('site', 'location', 'assigned_image',
                    'width', 'height', 'measurement_unit')

    def __str__(self):
        if self.site:
            return f'{self.site.name} Floorplan'
        else:
            return f'{self.location.name} Floorplan'

    def get_absolute_url(self):
        return reverse('plugins:netbox_floorplan:floorplan_edit', args=[self.pk])

    @property
    def record_type(self):
        if self.site:
            return "site"
        else:
            return "location"

    @property
    def mapped_racks(self):
        drawn_racks = []
        if self.canvas:
            if self.canvas.get("objects"):
                for obj in self.canvas["objects"]:
                    if obj.get("objects"):
                        for subobj in obj["objects"]:
                            if subobj.get("custom_meta"):
                                if subobj["custom_meta"].get("object_type") == "rack":
                                    drawn_racks.append(
                                        int(subobj["custom_meta"]["object_id"]))
        return drawn_racks

    @property
    def mapped_devices(self):
        drawn_devices = []
        if self.canvas:
            if self.canvas.get("objects"):
                for obj in self.canvas["objects"]:
                    if obj.get("objects"):
                        for subobj in obj["objects"]:
                            if subobj.get("custom_meta"):
                                if subobj["custom_meta"].get("object_type") == "device":
                                    drawn_devices.append(
                                        int(subobj["custom_meta"]["object_id"]))
        return drawn_devices

    def resync_canvas(self):
        """
        Synchronize canvas objects with current NetBox data.
        Handles both advanced mode (role/tenant/status) and original mode (status only) rack displays.
        """
        changed = False
        if self.canvas:
            if self.canvas.get("objects"):
                for index, obj in enumerate(self.canvas["objects"]):
                    if obj.get("custom_meta"):
                        if obj["custom_meta"].get("object_type") == "rack":
                            rack_id = int(obj["custom_meta"]["object_id"])
                            # if rack is not in the database, remove it from the canvas
                            rack_qs = Rack.objects.filter(pk=rack_id)
                            if not rack_qs.exists():
                                self.canvas["objects"].remove(obj)
                                changed = True
                            else:
                                rack = rack_qs.first()
                                self.canvas["objects"][index]["custom_meta"]["object_name"] = rack.name

                                # Update rack fill color based on role (only if not manually set
                                # and for advanced racks only)
                                # Check if color was manually set by looking for manual_color flag
                                color_manually_set = obj["custom_meta"].get("manual_color", False)

                                # Detect if this is an advanced rack by checking for info text type
                                is_advanced_mode_rack = False
                                if obj.get("objects"):
                                    for subobj in obj["objects"]:
                                        if (subobj.get("type") in ["i-text", "textbox"] and
                                                subobj.get("custom_meta", {}).get("text_type") == "info"):
                                            is_advanced_mode_rack = True
                                            break

                                # Only apply automatic color updates to advanced racks
                                if not color_manually_set and is_advanced_mode_rack:
                                    expected_color = None
                                    if rack.role and hasattr(rack.role, 'color'):
                                        expected_color = f"#{rack.role.color}"
                                    else:
                                        # Default color if no role or color is set
                                        expected_color = "#000000"

                                    # Check if the rack rectangle color needs updating
                                    if obj.get("objects") and len(obj["objects"]) > 0:
                                        rack_rect = obj["objects"][0]  # First object is typically the rack rectangle
                                        if rack_rect.get("fill") != expected_color:
                                            self.canvas["objects"][index]["objects"][0]["fill"] = expected_color
                                            changed = True
                                # End of rack fill color update

                                if obj.get("objects"):
                                    for subcounter, subobj in enumerate(obj["objects"]):
                                        # Check if the subobject is a rectangle and has custom_meta for rack
                                        # Update the custom_meta and text fields to match the current rack data
                                        # in Netbox
                                        if subobj.get("type") == "rect":
                                            if subobj.get("custom_meta", {}).get("object_type") == "rack":
                                                # Make sure the object_name matches the actual rack name
                                                if subobj["custom_meta"]["object_name"] != f"{rack.name}":
                                                    self.canvas["objects"][index]["objects"][
                                                        subcounter]["custom_meta"]["object_name"] = f"{rack.name}"
                                                    changed = True

                                        # Check if the subobject is a textbox or i-text object. This will have both
                                        # the rack name and the info text (status, role, tenant for advanced racks
                                        # or just status for simple racks).
                                        if subobj.get("type") == "i-text" or subobj.get("type") == "textbox":
                                            # Update the name text box with the current rack name if it exists
                                            if subobj.get("custom_meta", {}).get("text_type") == "name":
                                                if subobj["text"] != f"{rack.name}":
                                                    self.canvas["objects"][index]["objects"][
                                                        subcounter]["text"] = f"{rack.name}"
                                                    changed = True
                                            # Handle advanced racks combined info text box
                                            elif subobj.get("custom_meta", {}).get("text_type") == "info":
                                                # Handle combined info text box (advanced mode)
                                                rack_role_text = rack.role.name if rack.role else ""
                                                rack_tenant_text = f"{rack.tenant}" if rack.tenant else ""

                                                # Update stored values in custom_meta
                                                subobj["custom_meta"]["status"] = f"{rack.status}"
                                                subobj["custom_meta"]["role"] = rack_role_text
                                                subobj["custom_meta"]["tenant"] = rack_tenant_text

                                                # Rebuild the combined text based on visibility settings
                                                info_lines = []
                                                if subobj["custom_meta"].get("show_status", True):
                                                    info_lines.append(f"{rack.status}")
                                                if subobj["custom_meta"].get("show_role", True) and rack_role_text:
                                                    info_lines.append(rack_role_text)
                                                if subobj["custom_meta"].get("show_tenant", True) and rack_tenant_text:
                                                    info_lines.append(rack_tenant_text)

                                                new_text = '\n'.join(info_lines)
                                                if subobj["text"] != new_text:
                                                    self.canvas["objects"][index]["objects"][subcounter]["text"] = new_text
                                                    changed = True
                                            # Handle simple racks status text box, which only shows status
                                            elif subobj.get("custom_meta", {}).get("text_type") == "status":
                                                if subobj["text"] != f"{rack.status}":
                                                    self.canvas["objects"][index]["objects"][
                                                        subcounter]["text"] = f"{rack.status}"
                                                    changed = True

                        # Handle device objects on the canvas
                        if obj["custom_meta"].get("object_type") == "device":
                            device_id = int(obj["custom_meta"]["object_id"])
                            # if device is not in the database, remove it from the canvas
                            device_qs = Device.objects.filter(pk=device_id)
                            if not device_qs.exists():
                                self.canvas["objects"].remove(obj)
                                changed = True
                            else:
                                device = device_qs.first()
                                self.canvas["objects"][index]["custom_meta"]["object_name"] = device.name
                                if obj.get("objects"):
                                    for subcounter, subobj in enumerate(obj["objects"]):
                                        # Update device rectangle metadata
                                        if subobj.get("type") == "rect":
                                            if subobj.get("custom_meta", {}).get("object_type") == "device":
                                                # Make sure the object_name matches the actual device name
                                                if subobj["custom_meta"]["object_name"] != f"{device.name}":
                                                    self.canvas["objects"][index]["objects"][
                                                        subcounter]["custom_meta"]["object_name"] = f"{device.name}"
                                                    changed = True
                                        # Update device text elements (supports both advanced and simple devices)
                                        if subobj.get("type") == "i-text" or subobj.get("type") == "textbox":

                                            # Update device name text
                                            if subobj.get("custom_meta", {}).get("text_type") == "name":
                                                if subobj["text"] != f"{device.name}":
                                                    self.canvas["objects"][index]["objects"][
                                                        subcounter]["text"] = f"{device.name}"
                                                    changed = True
                                            # Handle advanced devices combined info text box for devices
                                            elif subobj.get("custom_meta", {}).get("text_type") == "info":
                                                # Handle combined info text box for devices (advanced mode)
                                                device_tenant_text = f"{device.tenant}" if device.tenant else ""

                                                # Update stored values in custom_meta
                                                subobj["custom_meta"]["status"] = f"{device.status}"
                                                subobj["custom_meta"]["tenant"] = device_tenant_text

                                                # Rebuild the combined text based on visibility settings
                                                info_lines = []
                                                if subobj["custom_meta"].get("show_status", True):
                                                    info_lines.append(f"{device.status}")
                                                if subobj["custom_meta"].get("show_tenant", True) and device_tenant_text:
                                                    info_lines.append(device_tenant_text)

                                                new_text = '\n'.join(info_lines)
                                                if subobj["text"] != new_text:
                                                    self.canvas["objects"][index]["objects"][subcounter]["text"] = new_text
                                                    changed = True
                                            # Handle 'simple' devices status text box
                                            elif subobj.get("custom_meta", {}).get("text_type") == "status":
                                                if subobj["text"] != f"{device.status}":
                                                    self.canvas["objects"][index]["objects"][
                                                        subcounter]["text"] = f"{device.status}"
                                                    changed = True
        if changed:
            self.save()

    def save(self, *args, **kwargs):
        if self.site and self.location:
            raise ValueError(
                "Only one of site or location can be set for a floorplan")
        # ensure that the site or location is set
        if not self.site and not self.location:
            raise ValueError(
                "Either site or location must be set for a floorplan")
        super().save(*args, **kwargs)

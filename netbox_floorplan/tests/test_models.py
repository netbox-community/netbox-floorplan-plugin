from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Device, DeviceRole, DeviceType, Location, Manufacturer, Rack, Site

from netbox_floorplan.models import Floorplan, FloorplanImage


def rack_canvas(rack_id, rack_name, status='active', advanced=False):
    """
    Build a canvas fragment of the shape the Fabric.js editor produces for a rack.

    A placed object is a group: the group itself carries custom_meta identifying the
    NetBox object, and its members are the rectangle and the text labels.
    """
    members = [
        {
            'type': 'rect',
            'fill': '#000000',
            'custom_meta': {
                'object_type': 'rack',
                'object_id': str(rack_id),
                'object_name': rack_name,
            },
        },
        {'type': 'i-text', 'text': rack_name, 'custom_meta': {'text_type': 'name'}},
    ]
    if advanced:
        members.append({
            'type': 'i-text',
            'text': status,
            'custom_meta': {
                'text_type': 'info',
                'status': status,
                'show_status': True,
                'show_role': True,
                'show_tenant': True,
            },
        })
    else:
        members.append({
            'type': 'i-text',
            'text': status,
            'custom_meta': {'text_type': 'status'},
        })

    return {
        'custom_meta': {
            'object_type': 'rack',
            'object_id': str(rack_id),
            'object_name': rack_name,
        },
        'objects': members,
    }


def device_canvas(device_id, device_name, status='active'):
    return {
        'custom_meta': {
            'object_type': 'device',
            'object_id': str(device_id),
            'object_name': device_name,
        },
        'objects': [
            {
                'type': 'rect',
                'custom_meta': {
                    'object_type': 'device',
                    'object_id': str(device_id),
                    'object_name': device_name,
                },
            },
            {'type': 'i-text', 'text': device_name, 'custom_meta': {'text_type': 'name'}},
            {'type': 'i-text', 'text': status, 'custom_meta': {'text_type': 'status'}},
        ],
    }


class FloorplanTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.location = Location.objects.create(name='Location 1', slug='location-1', site=cls.site)

    def test_str_uses_site_name(self):
        floorplan = Floorplan.objects.create(site=self.site)
        self.assertEqual(str(floorplan), 'Site 1 Floorplan')

    def test_str_uses_location_name(self):
        floorplan = Floorplan.objects.create(location=self.location)
        self.assertEqual(str(floorplan), 'Location 1 Floorplan')

    def test_record_type(self):
        self.assertEqual(Floorplan.objects.create(site=self.site).record_type, 'site')
        self.assertEqual(Floorplan.objects.create(location=self.location).record_type, 'location')

    def test_get_absolute_url(self):
        floorplan = Floorplan.objects.create(site=self.site)
        self.assertEqual(floorplan.get_absolute_url(), f'/plugins/floorplan/floorplans/{floorplan.pk}/edit/')

    def test_defaults(self):
        floorplan = Floorplan.objects.create(site=self.site)
        self.assertEqual(floorplan.measurement_unit, 'm')
        self.assertEqual(floorplan.canvas, {})


class FloorplanValidationTestCase(TestCase):
    """A floorplan is assigned to exactly one of a site or a location."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.location = Location.objects.create(name='Location 1', slug='location-1', site=cls.site)

    def test_clean_rejects_both_site_and_location(self):
        floorplan = Floorplan(site=self.site, location=self.location)
        with self.assertRaises(ValidationError):
            floorplan.clean()

    def test_clean_rejects_neither_site_nor_location(self):
        with self.assertRaises(ValidationError):
            Floorplan().clean()

    def test_clean_accepts_site_only(self):
        Floorplan(site=self.site).clean()

    def test_clean_accepts_location_only(self):
        Floorplan(location=self.location).clean()

    def test_save_rejects_both_site_and_location(self):
        # save() keeps its own guard for code paths which never call clean().
        with self.assertRaises(ValidationError):
            Floorplan(site=self.site, location=self.location).save()

    def test_save_rejects_neither_site_nor_location(self):
        with self.assertRaises(ValidationError):
            Floorplan().save()

    def test_invalid_floorplan_is_not_persisted(self):
        before = Floorplan.objects.count()
        with self.assertRaises(ValidationError):
            Floorplan().save()
        self.assertEqual(Floorplan.objects.count(), before)


class FloorplanMappedObjectsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.racks = [
            Rack.objects.create(name='rack-1', site=cls.site),
            Rack.objects.create(name='rack-2', site=cls.site),
        ]
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(
            manufacturer=manufacturer, model='Model 1', slug='model-1'
        )
        role = DeviceRole.objects.create(name='Role 1', slug='role-1')
        cls.device = Device.objects.create(
            name='device-1', site=cls.site, device_type=device_type, role=role
        )

    def test_mapped_racks_empty_canvas(self):
        floorplan = Floorplan.objects.create(site=self.site)
        self.assertEqual(floorplan.mapped_racks, [])
        self.assertEqual(floorplan.mapped_devices, [])

    def test_mapped_racks_returns_placed_rack_ids(self):
        floorplan = Floorplan.objects.create(site=self.site, canvas={'objects': [
            rack_canvas(self.racks[0].pk, 'rack-1'),
            rack_canvas(self.racks[1].pk, 'rack-2'),
        ]})
        self.assertEqual(sorted(floorplan.mapped_racks), sorted([r.pk for r in self.racks]))

    def test_mapped_devices_returns_placed_device_ids(self):
        floorplan = Floorplan.objects.create(site=self.site, canvas={'objects': [
            device_canvas(self.device.pk, 'device-1'),
        ]})
        self.assertEqual(floorplan.mapped_devices, [self.device.pk])

    def test_racks_and_devices_are_reported_separately(self):
        floorplan = Floorplan.objects.create(site=self.site, canvas={'objects': [
            rack_canvas(self.racks[0].pk, 'rack-1'),
            device_canvas(self.device.pk, 'device-1'),
        ]})
        self.assertEqual(floorplan.mapped_racks, [self.racks[0].pk])
        self.assertEqual(floorplan.mapped_devices, [self.device.pk])


class FloorplanResyncCanvasTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')

    def setUp(self):
        self.rack = Rack.objects.create(name='rack-1', site=self.site)
        self.floorplan = Floorplan.objects.create(site=self.site, canvas={'objects': [
            rack_canvas(self.rack.pk, 'rack-1'),
        ]})

    def test_renaming_a_rack_updates_the_canvas_labels(self):
        self.rack.name = 'rack-1-renamed'
        self.rack.save()

        self.floorplan.resync_canvas()
        self.floorplan.refresh_from_db()

        group = self.floorplan.canvas['objects'][0]
        self.assertEqual(group['custom_meta']['object_name'], 'rack-1-renamed')
        rect = group['objects'][0]
        self.assertEqual(rect['custom_meta']['object_name'], 'rack-1-renamed')
        name_label = group['objects'][1]
        self.assertEqual(name_label['text'], 'rack-1-renamed')

    def test_deleting_a_rack_removes_it_from_the_canvas(self):
        self.rack.delete()

        self.floorplan.resync_canvas()
        self.floorplan.refresh_from_db()

        self.assertEqual(self.floorplan.canvas['objects'], [])

    def test_unchanged_rack_leaves_the_canvas_alone(self):
        before = self.floorplan.canvas
        self.floorplan.resync_canvas()
        self.floorplan.refresh_from_db()
        self.assertEqual(self.floorplan.canvas, before)

    def test_empty_canvas_is_a_no_op(self):
        floorplan = Floorplan.objects.create(site=self.site)
        floorplan.resync_canvas()
        self.assertEqual(floorplan.canvas, {})


class FloorplanImageTestCase(TestCase):

    def test_str(self):
        image = FloorplanImage.objects.create(name='Image 1', external_url='https://example.com/a.png')
        self.assertEqual(str(image), 'Image 1')

    def test_get_absolute_url(self):
        image = FloorplanImage.objects.create(name='Image 1', external_url='https://example.com/a.png')
        self.assertEqual(
            image.get_absolute_url(),
            f'/plugins/floorplan/floorplans/floorplanimages/{image.pk}/',
        )

    def test_clean_requires_a_file_or_an_external_url(self):
        with self.assertRaises(ValidationError):
            FloorplanImage(name='Image 1').clean()

    def test_clean_rejects_both_a_file_and_an_external_url(self):
        image = FloorplanImage(name='Image 1', file='netbox-floorplan/a.png',
                               external_url='https://example.com/a.png')
        with self.assertRaises(ValidationError):
            image.clean()

    def test_clean_accepts_an_external_url_alone(self):
        FloorplanImage(name='Image 1', external_url='https://example.com/a.png').clean()

    def test_size_is_none_when_there_is_no_file(self):
        # An external_url image has no file, and FieldFile.size raises ValueError in that
        # state. The property must absorb it rather than propagate a 500 to the detail view.
        image = FloorplanImage.objects.create(name='Image 1', external_url='https://example.com/a.png')
        self.assertIsNone(image.size)

    def test_size_is_none_when_the_file_is_missing_from_storage(self):
        image = FloorplanImage.objects.create(name='Image 1', file='netbox-floorplan/absent.png')
        self.assertIsNone(image.size)

    def test_filename_is_the_basename(self):
        image = FloorplanImage.objects.create(name='Image 1', file='netbox-floorplan/diagram.png')
        self.assertEqual(image.filename, 'diagram.png')

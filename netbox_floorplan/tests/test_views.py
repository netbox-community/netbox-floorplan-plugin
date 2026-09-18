from django.urls import reverse
from utilities.testing import TestCase, ViewTestCases

from dcim.models import Location, Site

from netbox_floorplan.models import Floorplan, FloorplanImage


def plugin_base_url(model):
    return 'plugins:{}:{}_{{}}'.format(model._meta.app_label, model._meta.model_name)


class FloorplanImageTestCase(
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
):
    model = FloorplanImage

    def _get_base_url(self):
        return plugin_base_url(self.model)

    @classmethod
    def setUpTestData(cls):
        FloorplanImage.objects.bulk_create([
            FloorplanImage(name='Image 1', external_url='https://example.com/1.png'),
            FloorplanImage(name='Image 2', external_url='https://example.com/2.png'),
            FloorplanImage(name='Image 3', external_url='https://example.com/3.png'),
        ])

        cls.form_data = {
            'name': 'Image X',
            'external_url': 'https://example.com/x.png',
            'comments': 'created by the test suite',
        }


class FloorplanTestCase(ViewTestCases.DeleteObjectViewTestCase):
    """
    Only the delete case from NetBox's generic suite applies to Floorplan.

    There is no generic detail or edit view — get_absolute_url() points at the canvas
    editor, which is a plain Django View rather than an ObjectView. The generic list case
    is excluded too, because it asserts that each object's absolute URL appears in the
    rendered list, and FloorplanTable has no linkified column. The list view is covered
    by FloorplanListViewTestCase below instead.
    """
    model = Floorplan

    def _get_base_url(self):
        return plugin_base_url(self.model)

    @classmethod
    def setUpTestData(cls):
        for i in range(1, 4):
            site = Site.objects.create(name=f'Site {i}', slug=f'site-{i}')
            Floorplan.objects.create(site=site)


class FloorplanListViewTestCase(TestCase):
    user_permissions = ()

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Amsterdam DC', slug='amsterdam-dc')
        cls.floorplan = Floorplan.objects.create(site=cls.site)

    def test_list_renders_and_includes_the_assigned_site(self):
        self.add_permissions('netbox_floorplan.view_floorplan')
        response = self.client.get(reverse('plugins:netbox_floorplan:floorplan_list'))
        self.assertHttpStatus(response, 200)
        self.assertIn('Amsterdam DC', response.content.decode())

    def test_list_requires_permission(self):
        response = self.client.get(reverse('plugins:netbox_floorplan:floorplan_list'))
        self.assertEqual(response.status_code, 403)


class FloorplanAddViewTestCase(TestCase):
    """
    The add view is a bare View which creates a Floorplan from a ?site= or ?location=
    query parameter and redirects to the canvas editor.
    """
    user_permissions = ()

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.location = Location.objects.create(name='Location 1', slug='location-1', site=cls.site)

    def test_add_for_a_site_creates_a_floorplan_and_redirects(self):
        self.add_permissions('netbox_floorplan.add_floorplan')
        url = reverse('plugins:netbox_floorplan:floorplan_add')

        response = self.client.get(f'{url}?site={self.site.pk}')

        floorplan = Floorplan.objects.get(site=self.site)
        self.assertRedirects(
            response,
            reverse('plugins:netbox_floorplan:floorplan_edit', args=[floorplan.pk]),
            fetch_redirect_response=False,
        )

    def test_add_for_a_location_creates_a_floorplan(self):
        self.add_permissions('netbox_floorplan.add_floorplan')
        url = reverse('plugins:netbox_floorplan:floorplan_add')

        self.client.get(f'{url}?location={self.location.pk}')

        self.assertTrue(Floorplan.objects.filter(location=self.location).exists())

    def test_add_without_permission_is_rejected(self):
        url = reverse('plugins:netbox_floorplan:floorplan_add')
        response = self.client.get(f'{url}?site={self.site.pk}')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Floorplan.objects.filter(site=self.site).exists())


class FloorplanEditorViewTestCase(TestCase):
    """The canvas editor is a bare View which renders the Fabric.js page."""
    user_permissions = ()

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.floorplan = Floorplan.objects.create(site=cls.site)

    def test_editor_renders(self):
        response = self.client.get(
            reverse('plugins:netbox_floorplan:floorplan_edit', args=[self.floorplan.pk])
        )
        self.assertHttpStatus(response, 200)


class FloorplanTabsTestCase(TestCase):
    """The plugin registers a Floor Plan tab on both Site and Location."""
    user_permissions = ()

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.location = Location.objects.create(name='Location 1', slug='location-1', site=cls.site)
        Floorplan.objects.create(site=cls.site)

    def test_site_tab_renders_with_a_floorplan(self):
        self.add_permissions('dcim.view_site', 'netbox_floorplan.view_floorplan')
        response = self.client.get(reverse('dcim:site_floorplans', args=[self.site.pk]))
        self.assertHttpStatus(response, 200)

    def test_location_tab_renders_without_a_floorplan(self):
        self.add_permissions('dcim.view_location', 'netbox_floorplan.view_floorplan')
        response = self.client.get(reverse('dcim:location_floorplans', args=[self.location.pk]))
        self.assertHttpStatus(response, 200)


class FloorplanObjectListViewsTestCase(TestCase):
    """
    The rack and device pickers in the editor are ObjectListViews filtered to the
    floorplan, driven by a floorplan_id query parameter.
    """
    user_permissions = ()

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.floorplan = Floorplan.objects.create(site=cls.site)

    def test_rack_list_renders(self):
        self.add_permissions('dcim.view_rack')
        url = reverse('plugins:netbox_floorplan:floorplan_rack_list')
        response = self.client.get(f'{url}?floorplan_id={self.floorplan.pk}')
        self.assertHttpStatus(response, 200)

    def test_device_list_renders(self):
        self.add_permissions('dcim.view_device')
        url = reverse('plugins:netbox_floorplan:floorplan_device_list')
        response = self.client.get(f'{url}?floorplan_id={self.floorplan.pk}')
        self.assertHttpStatus(response, 200)


class MediaUrlExposureTestCase(TestCase):
    """
    The canvas needs NetBox's MEDIA_URL, so the templates publish it from Django settings
    rather than the JavaScript assuming /media/.
    """
    user_permissions = ()

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.floorplan = Floorplan.objects.create(site=cls.site)

    def test_editor_publishes_media_url(self):
        from django.conf import settings
        response = self.client.get(
            reverse('plugins:netbox_floorplan:floorplan_edit', args=[self.floorplan.pk])
        )
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        self.assertIn('window.NETBOX_MEDIA_URL', content)
        self.assertIn(f'window.NETBOX_MEDIA_URL = "{settings.MEDIA_URL}"', content)

    def test_media_url_is_published_before_the_module_script(self):
        # The module reads the global at import time, so ordering matters.
        response = self.client.get(
            reverse('plugins:netbox_floorplan:floorplan_edit', args=[self.floorplan.pk])
        )
        content = response.content.decode()
        self.assertLess(
            content.index('window.NETBOX_MEDIA_URL'),
            content.index('floorplan/edit.js'),
        )

    def test_site_tab_publishes_media_url(self):
        from django.conf import settings
        self.add_permissions('dcim.view_site', 'netbox_floorplan.view_floorplan')
        response = self.client.get(reverse('dcim:site_floorplans', args=[self.site.pk]))
        self.assertHttpStatus(response, 200)
        self.assertIn(f'window.NETBOX_MEDIA_URL = "{settings.MEDIA_URL}"', response.content.decode())


class DevicePickerImageUrlTestCase(TestCase):
    """
    The device picker passes the storage backend's URL for a device type's front image, so
    the JavaScript does not have to prepend a hardcoded media prefix.
    """
    user_permissions = ()

    @classmethod
    def setUpTestData(cls):
        from dcim.models import DeviceRole, DeviceType, Manufacturer
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.floorplan = Floorplan.objects.create(site=cls.site)
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        cls.device_type = DeviceType.objects.create(
            manufacturer=manufacturer, model='Model 1', slug='model-1',
            front_image='devicetype-images/front.png',
        )
        role = DeviceRole.objects.create(name='Role 1', slug='role-1')
        from dcim.models import Device
        cls.device = Device.objects.create(
            name='device-1', site=cls.site, device_type=cls.device_type, role=role
        )

    def test_picker_emits_the_storage_url(self):
        from django.conf import settings
        self.add_permissions('dcim.view_device')
        url = reverse('plugins:netbox_floorplan:floorplan_device_list')
        response = self.client.get(f'{url}?floorplan_id={self.floorplan.pk}')
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        # The picker emits the storage URL, not the bare stored name. Compare through js_str,
        # which is what escapes the value into the onclick handler.
        from netbox_floorplan.templatetags.template_utils import js_str
        self.assertIn(js_str(f"{settings.MEDIA_URL}devicetype-images/front.png"), content)
        self.assertNotIn(js_str("devicetype-images/front.png"), content)

    def test_picker_emits_no_absolute_host(self):
        self.add_permissions('dcim.view_device')
        url = reverse('plugins:netbox_floorplan:floorplan_device_list')
        response = self.client.get(f'{url}?floorplan_id={self.floorplan.pk}')
        content = response.content.decode()
        onclicks = [line for line in content.splitlines() if 'add_floorplan_object' in line]
        self.assertTrue(onclicks)
        for line in onclicks:
            self.assertNotIn('http://testserver', line)


class VendoredAssetsTestCase(TestCase):
    """
    The canvas pages load their vendored libraries by filename, so a rename must be reflected
    in the templates and the file must remain discoverable by staticfiles.

    The Fabric build is pinned to 5.2.1: the plugin uses its callback APIs (loadFromJSON with a
    reviver, fromURL with a callback, setBackgroundImage with a callback), all of which became
    promise-based in v6. The filename previously claimed 6.0.2 while containing 5.2.1.
    """
    user_permissions = ()

    FABRIC = 'netbox_floorplan/vendors/fabric-js-5.2.1.js'

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.floorplan = Floorplan.objects.create(site=cls.site)

    def test_vendored_fabric_is_discoverable(self):
        from django.contrib.staticfiles import finders
        self.assertIsNotNone(
            finders.find(self.FABRIC),
            f'{self.FABRIC} was not found by staticfiles',
        )

    def test_vendored_fabric_filename_matches_the_version_inside(self):
        import re
        from django.contrib.staticfiles import finders
        with open(finders.find(self.FABRIC)) as f:
            head = f.read(200)
        version = re.search(r'version:"([0-9.]+)"', head).group(1)
        self.assertIn(version, self.FABRIC)

    def test_editor_references_the_vendored_fabric(self):
        response = self.client.get(
            reverse('plugins:netbox_floorplan:floorplan_edit', args=[self.floorplan.pk])
        )
        self.assertHttpStatus(response, 200)
        self.assertIn('fabric-js-5.2.1.js', response.content.decode())

    def test_site_tab_references_the_vendored_fabric(self):
        self.add_permissions('dcim.view_site', 'netbox_floorplan.view_floorplan')
        response = self.client.get(reverse('dcim:site_floorplans', args=[self.site.pk]))
        self.assertHttpStatus(response, 200)
        self.assertIn('fabric-js-5.2.1.js', response.content.decode())

from django.urls import reverse
from utilities.testing import APITestCase, APIViewTestCases

from dcim.models import Location, Site

from netbox_floorplan.models import Floorplan, FloorplanImage


class AppTest(APITestCase):

    def test_root(self):
        url = reverse('plugins-api:netbox_floorplan-api:api-root')
        response = self.client.get(f'{url}?format=api', **self.header)
        self.assertEqual(response.status_code, 200)


class FloorplanImageTest(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    model = FloorplanImage
    view_namespace = 'plugins-api:netbox_floorplan'
    brief_fields = ['display', 'external_url', 'file', 'file_url', 'filename', 'id', 'name', 'url']

    create_data = [
        {'name': 'Image 4', 'external_url': 'https://example.com/4.png'},
        {'name': 'Image 5', 'external_url': 'https://example.com/5.png'},
        {'name': 'Image 6', 'external_url': 'https://example.com/6.png'},
    ]
    bulk_update_data = {
        'comments': 'bulk updated',
    }

    @classmethod
    def setUpTestData(cls):
        FloorplanImage.objects.bulk_create([
            FloorplanImage(name='Image 1', external_url='https://example.com/1.png'),
            FloorplanImage(name='Image 2', external_url='https://example.com/2.png'),
            FloorplanImage(name='Image 3', external_url='https://example.com/3.png'),
        ])


class FloorplanTest(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    model = Floorplan
    view_namespace = 'plugins-api:netbox_floorplan'
    brief_fields = ['display', 'id', 'url']
    bulk_update_data = {
        'measurement_unit': 'ft',
    }

    @classmethod
    def setUpTestData(cls):
        sites = [
            Site.objects.create(name=f'Site {i}', slug=f'site-{i}')
            for i in range(1, 7)
        ]
        Floorplan.objects.create(site=sites[0])
        Floorplan.objects.create(site=sites[1])
        Floorplan.objects.create(site=sites[2])

        # Each floorplan needs its own site, since a site may only have one.
        cls.create_data = [
            {'site': sites[3].pk},
            {'site': sites[4].pk},
            {'site': sites[5].pk},
        ]


class FloorplanValidationAPITest(APITestCase):
    """A floorplan is assigned to exactly one of a site or a location."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        cls.location = Location.objects.create(name='Location 1', slug='location-1', site=cls.site)

    def _post(self, data):
        self.add_permissions('netbox_floorplan.add_floorplan')
        url = reverse('plugins-api:netbox_floorplan-api:floorplan-list')
        return self.client.post(url, data, format='json', **self.header)

    def test_create_with_a_site_succeeds(self):
        response = self._post({'site': self.site.pk})
        self.assertEqual(response.status_code, 201)

    def test_create_with_a_location_succeeds(self):
        response = self._post({'location': self.location.pk})
        self.assertEqual(response.status_code, 201)

    def test_create_with_both_is_rejected(self):
        response = self._post({'site': self.site.pk, 'location': self.location.pk})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Floorplan.objects.count(), 0)

    def test_create_with_neither_is_rejected(self):
        response = self._post({})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Floorplan.objects.count(), 0)


class FloorplanImageFileUrlTest(APITestCase):
    """
    `file_url` renders the storage backend's URL rather than an absolute URL built from the
    request, so a floorplan loads correctly when NetBox is reached through a different
    hostname than the one that served the API call (a reverse proxy).
    """

    @classmethod
    def setUpTestData(cls):
        cls.uploaded = FloorplanImage.objects.create(
            name='Uploaded', file='netbox-floorplan/plan.png'
        )
        cls.linked = FloorplanImage.objects.create(
            name='Linked', external_url='https://files.example.com/plan.png'
        )

    def _get(self, instance, host='netbox.internal:8001'):
        self.add_permissions('netbox_floorplan.view_floorplanimage')
        url = reverse(
            'plugins-api:netbox_floorplan-api:floorplanimage-detail', kwargs={'pk': instance.pk}
        )
        return self.client.get(url, HTTP_HOST=host, **self.header).data

    def test_file_is_absolute_and_carries_the_request_host(self):
        # DRF's default representation, retained for API compatibility.
        data = self._get(self.uploaded)
        self.assertTrue(data['file'].startswith('http'))
        self.assertIn('netbox.internal', data['file'])

    def test_file_url_is_relative_for_local_storage(self):
        data = self._get(self.uploaded)
        self.assertTrue(data['file_url'].startswith('/'))
        self.assertNotIn('netbox.internal', data['file_url'])
        self.assertNotIn('http', data['file_url'])

    def test_file_url_does_not_change_with_the_request_host(self):
        # The point of the field: the value must not depend on how NetBox was addressed.
        first = self._get(self.uploaded, host='netbox.internal:8001')['file_url']
        second = self._get(self.uploaded, host='netbox.example.com')['file_url']
        self.assertEqual(first, second)

    def test_file_url_points_at_the_same_path_as_file(self):
        data = self._get(self.uploaded)
        self.assertTrue(data['file'].endswith(data['file_url']))

    def test_file_url_is_none_when_there_is_no_file(self):
        data = self._get(self.linked)
        self.assertIsNone(data['file_url'])
        self.assertEqual(data['external_url'], 'https://files.example.com/plan.png')

from django.test import TestCase

from dcim.models import Location, Site

from netbox_floorplan.filtersets import FloorplanFilterSet, FloorplanImageFilterSet
from netbox_floorplan.models import Floorplan, FloorplanImage


class FloorplanFilterSetTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.site_a = Site.objects.create(name='Amsterdam DC', slug='amsterdam-dc')
        cls.site_b = Site.objects.create(name='Berlin DC', slug='berlin-dc')
        cls.location = Location.objects.create(
            name='Cologne Room', slug='cologne-room', site=cls.site_a
        )

        cls.fp_site_a = Floorplan.objects.create(site=cls.site_a)
        cls.fp_site_b = Floorplan.objects.create(site=cls.site_b)
        cls.fp_location = Floorplan.objects.create(location=cls.location)

    def _qs(self):
        return Floorplan.objects.all()

    # Floorplan extends NetBoxModel, which has no description field. The search method
    # previously filtered description__icontains, so any q= raised FieldError.
    def test_search_does_not_raise(self):
        fs = FloorplanFilterSet({'q': 'anything'}, queryset=self._qs())
        self.assertEqual(fs.qs.count(), 0)

    def test_search_matches_site_name(self):
        fs = FloorplanFilterSet({'q': 'Amsterdam'}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [self.fp_site_a])

    def test_search_matches_location_name(self):
        fs = FloorplanFilterSet({'q': 'Cologne'}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [self.fp_location])

    def test_search_is_case_insensitive(self):
        fs = FloorplanFilterSet({'q': 'berlin'}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [self.fp_site_b])

    def test_search_matches_a_partial_name(self):
        fs = FloorplanFilterSet({'q': 'DC'}, queryset=self._qs())
        self.assertEqual(fs.qs.count(), 2)

    def test_empty_search_returns_everything(self):
        fs = FloorplanFilterSet({'q': ''}, queryset=self._qs())
        self.assertEqual(fs.qs.count(), 3)

    def test_filter_by_site(self):
        fs = FloorplanFilterSet({'site': self.site_a.pk}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [self.fp_site_a])

    def test_filter_by_location(self):
        fs = FloorplanFilterSet({'location': self.location.pk}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [self.fp_location])

    def test_filter_by_id(self):
        fs = FloorplanFilterSet({'id': [self.fp_site_b.pk]}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [self.fp_site_b])

    def test_search_matches_assigned_image_name(self):
        image = FloorplanImage.objects.create(name='Ground Floor Plan', external_url='https://example.com/a.png')
        fp = Floorplan.objects.create(site=Site.objects.create(name='Dublin DC', slug='dublin-dc'), assigned_image=image)
        fs = FloorplanFilterSet({'q': 'Ground Floor'}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [fp])


class FloorplanImageFilterSetTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.image_a = FloorplanImage.objects.create(
            name='Warehouse Layout', external_url='https://example.com/warehouse.png', comments='primary site'
        )
        cls.image_b = FloorplanImage.objects.create(
            name='Office Layout', external_url='https://example.com/office.png', comments='secondary site'
        )

    def _qs(self):
        return FloorplanImage.objects.all()

    def test_search_matches_name(self):
        fs = FloorplanImageFilterSet({'q': 'Warehouse'}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [self.image_a])

    def test_search_matches_external_url(self):
        fs = FloorplanImageFilterSet({'q': 'office.png'}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [self.image_b])

    def test_search_matches_comments(self):
        fs = FloorplanImageFilterSet({'q': 'primary'}, queryset=self._qs())
        self.assertEqual(list(fs.qs), [self.image_a])

    def test_empty_search_returns_everything(self):
        fs = FloorplanImageFilterSet({'q': ''}, queryset=self._qs())
        self.assertEqual(fs.qs.count(), 2)

from django.template import Context, Template
from django.test import TestCase

from dcim.models import Manufacturer, Rack, RackType, Site

from netbox_floorplan.templatetags.template_utils import (
    denormalize_measurement,
    js_str,
    rack_outer_js,
)


class DenormalizeMeasurementTestCase(TestCase):

    def test_metres(self):
        self.assertEqual(denormalize_measurement('m', 500), 5.0)

    def test_feet(self):
        self.assertEqual(denormalize_measurement('ft', 500), 16.4)

    def test_accepts_a_string_value(self):
        self.assertEqual(denormalize_measurement('m', '250'), 2.5)


class JsStrTestCase(TestCase):
    """
    The tables build onclick handlers containing JavaScript string literals. Django
    escapes a quote to &#x27;, which the browser decodes back to a quote before the
    JavaScript is parsed, so the handler must be escaped for JavaScript instead.
    """

    def test_wraps_in_single_quotes(self):
        self.assertEqual(js_str('rack1'), "'rack1'")

    def test_escapes_a_hyphen(self):
        # Django's escapejs also escapes '-', guarding against a '-->' sequence. The
        # result is verbose but decodes back to a hyphen in JavaScript.
        self.assertEqual(js_str('rack-1'), "'rack\\u002D1'")

    def test_escapes_a_single_quote(self):
        self.assertEqual(js_str("O'Brien"), "'O\\u0027Brien'")

    def test_escapes_a_double_quote(self):
        self.assertIn('\\u0022', js_str('say "hi"'))

    def test_escapes_a_newline(self):
        self.assertNotIn('\n', js_str('a\nb'))

    def test_escapes_a_closing_script_tag(self):
        self.assertNotIn('</script>', js_str('</script>'))

    def test_renders_an_integer(self):
        self.assertEqual(js_str(7), "'7'")

    def test_renders_none_as_the_string_none(self):
        # Matches Django's default rendering of None, so only escaping changed.
        self.assertEqual(js_str(None), "'None'")

    def test_output_is_marked_safe_so_django_does_not_double_escape(self):
        rendered = Template(
            "{% load template_utils %}{{ value|js_str }}"
        ).render(Context({'value': "O'Brien"}))
        self.assertEqual(rendered, "'O\\u0027Brien'")
        self.assertNotIn('&#x27;', rendered)

    def test_quotes_stay_balanced_for_a_quote_heavy_value(self):
        rendered = js_str("a'b'c'd")
        self.assertEqual(rendered.count("'"), 2)


class RackOuterJsTestCase(TestCase):
    """
    Rack.outer_width / outer_depth / outer_unit are deprecated in NetBox 4.7 and are to
    be inferred from the assigned RackType in v5.0, so the filter reads the RackType
    first and falls back to the Rack's own fields.
    """

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='Site 1', slug='site-1')
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        cls.rack_type = RackType.objects.create(
            manufacturer=manufacturer, model='Wide Rack', slug='wide-rack',
            outer_width=800, outer_depth=1200, outer_unit='mm',
        )
        cls.rack_type_no_dims = RackType.objects.create(
            manufacturer=manufacturer, model='Plain Rack', slug='plain-rack',
        )

    def test_unset_dimensions_render_as_null(self):
        rack = Rack.objects.create(name='rack-1', site=self.site)
        self.assertEqual(rack_outer_js(rack, 'width'), 'null')
        self.assertEqual(rack_outer_js(rack, 'depth'), 'null')
        self.assertEqual(rack_outer_js(rack, 'unit'), 'null')

    def test_reads_the_racks_own_dimensions(self):
        rack = Rack.objects.create(
            name='rack-1', site=self.site,
            outer_width=600, outer_depth=1000, outer_unit='mm',
        )
        self.assertEqual(rack_outer_js(rack, 'width'), '600')
        self.assertEqual(rack_outer_js(rack, 'depth'), '1000')
        self.assertEqual(rack_outer_js(rack, 'unit'), "'mm'")

    def test_reads_the_rack_types_dimensions(self):
        rack = Rack.objects.create(name='rack-1', site=self.site, rack_type=self.rack_type)
        self.assertEqual(rack_outer_js(rack, 'width'), '800')
        self.assertEqual(rack_outer_js(rack, 'depth'), '1200')
        self.assertEqual(rack_outer_js(rack, 'unit'), "'mm'")

    def test_falls_back_to_the_rack_when_the_rack_type_has_no_dimensions(self):
        rack = Rack.objects.create(name='rack-1', site=self.site, rack_type=self.rack_type_no_dims)
        # NetBox copies the RackType's (empty) values down on save, so set them after.
        rack.outer_width, rack.outer_depth, rack.outer_unit = 600, 1000, 'mm'
        self.assertEqual(rack_outer_js(rack, 'width'), '600')
        self.assertEqual(rack_outer_js(rack, 'unit'), "'mm'")

    def test_zero_is_treated_as_unset(self):
        # The template this replaced used {% if %}, which treats 0 as falsy.
        rack = Rack.objects.create(name='rack-1', site=self.site, outer_width=0, outer_depth=1000,
                                   outer_unit='mm')
        self.assertEqual(rack_outer_js(rack, 'width'), 'null')
        self.assertEqual(rack_outer_js(rack, 'depth'), '1000')

    def test_works_when_the_rack_has_no_deprecated_fields_at_all(self):
        # Forward compatibility: once NetBox v5.0 removes the fields from Rack, only the
        # RackType carries them.
        class FutureRack:
            def __init__(self, rack_type):
                self.rack_type = rack_type

        self.assertEqual(rack_outer_js(FutureRack(self.rack_type), 'width'), '800')
        self.assertEqual(rack_outer_js(FutureRack(self.rack_type), 'unit'), "'mm'")

    def test_unit_is_escaped_for_javascript(self):
        rack = Rack.objects.create(name='rack-1', site=self.site)
        rack.outer_unit = "in'ch"
        self.assertEqual(rack_outer_js(rack, 'unit'), "'in\\u0027ch'")

from importlib import reload

from django.test import TestCase, override_settings

from netbox.plugins import PluginMenu, PluginMenuItem

from netbox_floorplan import navigation


class NavigationTestCase(TestCase):
    """
    navigation.py reads PLUGINS_CONFIG['netbox_floorplan']['top_level_menu'] at import
    time, so exercising both branches means reloading the module under each setting.
    """

    def tearDown(self):
        # Restore the module to its real, non-overridden state for subsequent tests.
        reload(navigation)

    @override_settings(PLUGINS_CONFIG={'netbox_floorplan': {'top_level_menu': False}})
    def test_default_nests_under_plugins_menu(self):
        reload(navigation)
        self.assertIsNone(navigation.menu)
        self.assertEqual(len(navigation.menu_items), 1)
        self.assertIsInstance(navigation.menu_items[0], PluginMenuItem)
        self.assertEqual(navigation.menu_items[0].link_text, 'Floorplan Images')

    @override_settings(PLUGINS_CONFIG={'netbox_floorplan': {'top_level_menu': True}})
    def test_top_level_menu_registers_a_dedicated_menu(self):
        reload(navigation)
        self.assertEqual(navigation.menu_items, ())
        self.assertIsInstance(navigation.menu, PluginMenu)
        self.assertEqual(navigation.menu.label, 'Floorplan')
        self.assertEqual(len(navigation.menu.groups), 1)
        group = navigation.menu.groups[0]
        self.assertEqual(group.label, 'Floorplan')
        self.assertEqual(len(group.items), 1)
        self.assertEqual(group.items[0].link_text, 'Floorplan Images')

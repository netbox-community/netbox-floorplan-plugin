"""
Define the plugin menu buttons & the plugin navigation bar enteries.
"""

from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem, get_plugin_config

PLUGIN_NAME = 'netbox_floorplan'


#
# Define plugin menu buttons
#
menu_buttons = (
    PluginMenuItem(
        link="plugins:netbox_floorplan:floorplanimage_list",
        link_text="Floorplan Images",
        buttons=(
            PluginMenuButton(
                link='plugins:netbox_floorplan:floorplanimage_add',
                title='Add',
                icon_class='mdi mdi-plus-thick',
            ),
        ),
    ),

)


# By default the plugin nests its links under NetBox's shared "Plugins" menu, via
# menu_items. Setting PLUGINS_CONFIG['netbox_floorplan']['top_level_menu'] = True instead
# registers a dedicated top-level menu, via menu. NetBox's PluginConfig.ready() registers
# whichever of the two is non-empty, so only one is ever active.
if get_plugin_config(PLUGIN_NAME, 'top_level_menu'):
    menu = PluginMenu(
        label='Floorplan',
        groups=(
            ('Floorplan', menu_buttons),
        ),
        icon_class='mdi mdi-floor-plan',
    )
    menu_items = ()
else:
    menu = None
    menu_items = menu_buttons

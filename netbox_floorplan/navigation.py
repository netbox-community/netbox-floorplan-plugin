"""
Define the plugin menu buttons & the plugin navigation bar enteries.
"""

from netbox.plugins import PluginMenuItem, PluginMenuButton


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


menu_items = menu_buttons

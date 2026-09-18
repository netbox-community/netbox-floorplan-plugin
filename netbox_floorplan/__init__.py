from netbox.plugins import PluginConfig
from .version import __version__


class FloorplanConfig(PluginConfig):

    name = "netbox_floorplan"
    verbose_name = "Netbox Floorplan"
    description = ""
    version = __version__
    base_url = "floorplan"
    min_version = "4.7.0"
    max_version = "4.7.99"
    default_settings = {
        # Register a dedicated top-level menu instead of nesting under NetBox's shared
        # "Plugins" menu. See netbox_floorplan/navigation.py.
        'top_level_menu': False,
    }


config = FloorplanConfig

from netbox.plugins import PluginConfig
from .version import __version__


class FloorplanConfig(PluginConfig):

    name = "netbox_floorplan"
    verbose_name = "Netbox Floorplan"
    description = ""
    version = __version__
    base_url = "floorplan"
    min_version = "4.5.0"
    max_version = "4.5.99"


config = FloorplanConfig

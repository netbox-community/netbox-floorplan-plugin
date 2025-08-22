from extras.plugins import PluginConfig


class FloorplanConfig(PluginConfig):
    name = "netbox_floorplan"
    verbose_name = "Netbox Floorplan"
    description = ""
    version = "0.3.7"
    base_url = "floorplan"
    min_version = "3.4.1"


config = FloorplanConfig

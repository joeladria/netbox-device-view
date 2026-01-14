from netbox.plugins import PluginConfig
from importlib.metadata import metadata

metadata = metadata("netbox_device_view")


class NetBoxDeviceViewConfig(PluginConfig):
    name = metadata.get("Name").replace("-", "_")
    verbose_name = metadata.get("Summary")
    description = "Plugin to visualize device ports"
    version = metadata.get("Version")
    author = metadata.get("Author")
    base_url = "device_view"
    required_settings = []
    default_settings = {
        "show_on_device_tab": False,
        "show_site_ports": False,
        "site_ports_label": "Port View",
        "vlan_role_colors": {
            # Default VLAN role to color mappings (hex colors without #)
            # Users can override these in their configuration.py PLUGINS_CONFIG
            "Video": "28A745",              # green
            "Lighting": "DC3545",           # red
            "Audio": "007BFF",              # blue
            "Cameras": "FFC107",            # yellow
            "Network Management": "343A40", # dark-gray
            "Interactive": "FFC107",        # yellow
        }
    }


config = NetBoxDeviceViewConfig

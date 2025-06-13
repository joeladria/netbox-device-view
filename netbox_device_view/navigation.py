from netbox.plugins import PluginMenuButton, PluginMenuItem
from netbox.choices import ButtonColorChoices

deviceview_buttons = [
    PluginMenuButton(
        link="plugins:netbox_device_view:deviceview_add",
        title="Add",
        icon_class="mdi mdi-plus-thick",
        color=ButtonColorChoices.GREEN,
    ),
    PluginMenuButton(
        link="plugins:netbox_device_view:deviceview_import",
        title="Import",
        icon_class="mdi mdi-upload",
    ),
]

device_elevation_item = PluginMenuItem(
    link="plugins:netbox_device_view:device_elevation",
    link_text="Device Elevation",
    permissions=["dcim.view_device"],  # Or more specific if needed
)

menu_items = (
    PluginMenuItem(
        link="plugins:netbox_device_view:deviceview_list",
        link_text="Device Views",
        buttons=deviceview_buttons,
    ),
    device_elevation_item,
)

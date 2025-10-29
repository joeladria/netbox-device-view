from dcim.models import ConsolePort
from .models import DeviceView
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from extras.models import Tag

import re


def get_hostname_last_segment(hostname):
    """
    Extract the last segment of a hostname after splitting by dashes.
    
    Args:
        hostname: The hostname string to process
    
    Returns:
        The last segment of the hostname after splitting by '-'
        If no dashes are present, returns the original hostname
        
    Examples:
        "FVR2-CTL-XAG01" → "XAG01"
        "switch-01" → "01" 
        "router" → "router"
    """
    if not isinstance(hostname, str):
        return hostname
    
    parts = hostname.split('-')
    if parts:
        return parts[-1]
    return hostname


def process_interfaces(interfaces, ports_chassis, dev):
    if interfaces is not None:
        for itf in interfaces:
            if itf.type == "virtual" or itf.type == "lag":
                continue
            stylename = re.sub(r"[/\.\s\+]+", "-", itf.name.lower())

            stylename = re.sub(r"-+", "-", stylename).strip("-")

            if not stylename:
                stylename = f"iface-{itf.pk}"

            itf.stylename = stylename

            if itf.stylename and (
                itf.stylename[0].isdigit() or itf.stylename[0] == "-"
            ):
                itf.stylename = f"p{itf.stylename}"

            # Add hostname processing for connected endpoints
            if hasattr(itf, 'connected_endpoints') and itf.connected_endpoints:
                for ce in itf.connected_endpoints:
                    if hasattr(ce, 'device') and hasattr(ce.device, 'name'):
                        ce.device.name_last_segment = get_hostname_last_segment(ce.device.name)

            itf.vlan_role_color = None
            itf.debug_vlan_role_tag_name = "N/A"
            itf.debug_vlan_role_tag_color = "N/A"

            if not hasattr(itf, 'untagged_vlan') or not itf.untagged_vlan:
                itf.debug_vlan_role_name = "No untagged VLAN"
            elif not itf.untagged_vlan.role:
                itf.debug_vlan_role_name = "Untagged VLAN has no role"
            else:
                itf.debug_vlan_role_name = itf.untagged_vlan.role.name
                try:
                    role_tags = itf.untagged_vlan.role.tags.all()
                    found_tag = False
                    for tag in role_tags:
                        if tag.color:
                            itf.vlan_role_color = tag.color
                            itf.debug_vlan_role_tag_name = tag.name
                            itf.debug_vlan_role_tag_color = f"#{tag.color}"
                            found_tag = True
                            break
                    if not found_tag and role_tags:
                        itf.debug_vlan_role_tag_name = f"Found {len(role_tags)} tag(s), none with color"
                    elif not role_tags:
                        itf.debug_vlan_role_tag_name = "No tags on role"
                except Exception as e:
                    error_message = str(e)
                    if "managerfromrestrictedqueryset" in error_message.lower():
                        error_message = "Permission error fetching tags."
                    print(f"Error looking up tag for VLAN role on interface {itf.name}: {e}")
                    itf.debug_vlan_role_tag_name = f"Error: {error_message[:50]}"

            if dev not in ports_chassis:
                ports_chassis[dev] = []
            ports_chassis[dev].append(itf)
    return ports_chassis


def process_ports(ports, ports_chassis, dev):
    if ports is not None:
        for port in ports:
            if port.type == "virtual":
                continue
            port.is_port = True
            port.stylename = re.sub(r"[^.a-zA-Z\d]", "-", port.name.lower())
            if port.stylename.isdigit():
                port.stylename = f"p{port.stylename}"

            port.debug_vlan_role_name = "N/A (Not an Interface)"
            port.debug_vlan_role_tag_name = "N/A"
            port.debug_vlan_role_tag_color = "N/A"
            port.vlan_role_color = None

            # Add hostname processing for link peers
            if hasattr(port, 'link_peers') and port.link_peers:
                for lp in port.link_peers:
                    if hasattr(lp, 'device') and hasattr(lp.device, 'name'):
                        lp.device.name_last_segment = get_hostname_last_segment(lp.device.name)

            if dev not in ports_chassis:
                ports_chassis[dev] = []
            ports_chassis[dev].append(port)
    return ports_chassis


def prepare(obj, instance_prefix=None):
    ports_chassis = {}
    dv = {}
    modules = {}
    device_view_model = apps.get_model('netbox_device_view', 'DeviceView')

    try:
        if obj.virtual_chassis is None:
            device_view_instance = device_view_model.objects.get(device_type=obj.device_type)
            grid_css = device_view_instance.grid_template_area

            if instance_prefix:
                prefixed_css_lines = []
                for line in grid_css.splitlines():
                    stripped_line = line.strip()
                    if stripped_line.startswith('.') and '{' in stripped_line:
                        prefixed_css_lines.append(f".{instance_prefix} {stripped_line}")
                    elif stripped_line.startswith('#') and '{' in stripped_line:
                        prefixed_css_lines.append(f".{instance_prefix} {stripped_line}")
                    else:
                        prefixed_css_lines.append(line)
                dv[1] = "\n".join(prefixed_css_lines)
            else:
                dv[1] = grid_css
            
            modules[1] = obj.modules.all()
            ports_chassis = process_interfaces(
                obj.interfaces.all(), ports_chassis, obj.name
            )
            ports_chassis = process_ports(obj.frontports.all(), ports_chassis, "Front")
            ports_chassis = process_ports(obj.rearports.all(), ports_chassis, "Rear")
            ports_chassis = process_ports(
                ConsolePort.objects.filter(device_id=obj.id),
                ports_chassis,
                obj.name,
            )
        else:
            for member in obj.virtual_chassis.members.all():
                member_device_view_instance = device_view_model.objects.get(device_type=member.device_type)
                member_grid_css = member_device_view_instance.grid_template_area
                
                processed_member_grid_css = member_grid_css.replace(".area", ".area.d" + str(member.vc_position))

                if instance_prefix:
                    prefixed_css_lines = []
                    for line in processed_member_grid_css.splitlines():
                        stripped_line = line.strip()
                        if stripped_line.startswith('.') and '{' in stripped_line:
                            prefixed_css_lines.append(f".{instance_prefix} {stripped_line}")
                        elif stripped_line.startswith('#') and '{' in stripped_line:
                            prefixed_css_lines.append(f".{instance_prefix} {stripped_line}")
                        else:
                            prefixed_css_lines.append(line)
                    dv[member.vc_position] = "\n".join(prefixed_css_lines)
                else:
                    dv[member.vc_position] = processed_member_grid_css

                modules[member.vc_position] = member.modules.all()
                ports_chassis = process_interfaces(
                    member.interfaces.all(), ports_chassis, member.vc_position
                )
                ports_chassis = process_ports(
                    ConsolePort.objects.filter(device_id=member.id),
                    ports_chassis,
                    member.vc_position,
                )
    except ObjectDoesNotExist:
        return None, None, None

    return dv, modules, ports_chassis

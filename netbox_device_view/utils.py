from dcim.models import ConsolePort
from .models import DeviceView
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps # Added for getting DeviceView model reliably
from extras.models import Tag # Added Tag import

import re


def process_interfaces(interfaces, ports_chassis, dev):
    if interfaces is not None:
        for itf in interfaces:
            if itf.type == "virtual" or itf.type == "lag":
                continue
            # Convert to lowercase and replace common separators with hyphens
            # This replaces the original regex matching and if/else block
            stylename = re.sub(r"[/\.\s\+]+", "-", itf.name.lower())

            # Clean up multiple hyphens and leading/trailing hyphens
            stylename = re.sub(r"-+", "-", stylename).strip("-")

            # If the name becomes empty after cleaning, use a fallback
            if not stylename:
                stylename = f"iface-{itf.pk}"  # Use a unique fallback

            # Assign the generated stylename back to the object property
            itf.stylename = stylename

            # Check if the stylename exists and starts with a digit or a hyphen
            # This replaces the original 'if itf.stylename.isdigit():' line
            if itf.stylename and (
                itf.stylename[0].isdigit() or itf.stylename[0] == "-"
            ):
                itf.stylename = f"p{itf.stylename}"

            # Add VLAN role color logic & debug attributes for interfaces
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
                    # Use the related manager 'tags.all()' for the VLANRole instance
                    role_tags = itf.untagged_vlan.role.tags.all()
                    found_tag = False
                    for tag in role_tags:
                        if tag.color:
                            itf.vlan_role_color = tag.color
                            itf.debug_vlan_role_tag_name = tag.name
                            itf.debug_vlan_role_tag_color = f"#{tag.color}"
                            found_tag = True
                            break # Use the first tag with a color
                    if not found_tag and role_tags:
                        itf.debug_vlan_role_tag_name = f"Found {len(role_tags)} tag(s), none with color"
                    elif not role_tags:
                        itf.debug_vlan_role_tag_name = "No tags on role"
                except Exception as e:
                    error_message = str(e)
                    # Simplify common long error messages for display
                    if "managerfromrestrictedqueryset" in error_message.lower():
                        error_message = "Permission error fetching tags."
                    print(f"Error looking up tag for VLAN role on interface {itf.name}: {e}")
                    itf.debug_vlan_role_tag_name = f"Error: {error_message[:50]}" # Truncate long errors

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

            # Initialize debug attributes for non-interface ports to ensure they exist for the template
            port.debug_vlan_role_name = "N/A (Not an Interface)"
            port.debug_vlan_role_tag_name = "N/A"
            port.debug_vlan_role_tag_color = "N/A"
            port.vlan_role_color = None # Ensure this is also initialized for non-interfaces

            if dev not in ports_chassis:
                ports_chassis[dev] = []
            ports_chassis[dev].append(port)
    return ports_chassis


def prepare(obj, instance_prefix=None): # Added instance_prefix argument
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
                # For virtual chassis members, the existing logic for namespacing might be sufficient,
                # or it might also need to incorporate the instance_prefix if a VC master is part of a multi-device view.
                # For now, keeping the original VC logic, assuming instance_prefix is mainly for distinct devices on the new page.
                # If a VC itself is shown on the multi-device page, its internal members are already handled by 'd' + vc_position.
                # The instance_prefix would apply to the VC as a whole.

                member_device_view_instance = device_view_model.objects.get(device_type=member.device_type)
                member_grid_css = member_device_view_instance.grid_template_area
                
                # Apply VC internal prefix
                processed_member_grid_css = member_grid_css.replace(".area", ".area.d" + str(member.vc_position))

                if instance_prefix: # If the whole VC is on a multi-device page, prefix its already VC-namespaced CSS
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
                    member.interfaces.all(), ports_chassis, member.vc_position # Using vc_position as key for ports_chassis
                )
                ports_chassis = process_ports(
                    ConsolePort.objects.filter(device_id=member.id),
                    ports_chassis,
                    member.vc_position,
                )
    except ObjectDoesNotExist:
        return None, None, None

    return dv, modules, ports_chassis

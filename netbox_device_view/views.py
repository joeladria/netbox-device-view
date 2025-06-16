from netbox.views import generic
from dcim.models import Device, Site, Rack # Added Site and Rack
from . import forms, models, tables, filtersets
from utilities.views import ViewTab, register_model_view
from .utils import prepare
from django.http import HttpResponse
from django.shortcuts import render # Added render
from django.apps import apps # Added apps
from django.views import View as DjangoView # Added DjangoView import
import pprint

from netbox.views.generic import BulkImportView
from .forms import DeviceViewImportForm # Changed to relative import


class DeviceViewView(generic.ObjectView):
    queryset = models.DeviceView.objects


class DeviceViewListView(generic.ObjectListView):
    queryset = models.DeviceView.objects
    table = tables.DeviceViewTable


class DeviceViewEditView(generic.ObjectEditView):
    queryset = models.DeviceView.objects
    form = forms.DeviceViewForm


class DeviceViewBulkImportView(BulkImportView):
    queryset = models.DeviceView.objects.all()
    model_form = DeviceViewImportForm


class DeviceViewDeleteView(generic.ObjectDeleteView):
    queryset = models.DeviceView.objects


@register_model_view(Device, "deviceview", path="device-view")
class DeviceDeviceView(generic.ObjectView):
    queryset = models.DeviceView.objects

    tab = ViewTab(
        label="Device View",
        badge=lambda obj: models.DeviceView.objects.filter(
            device_type=obj.device_type
        ).count(),
        hide_if_empty=True,
    )

    def get_extra_context(self, request, instance):
        dv, modules, ports_chassis = prepare(instance)
        display_size_param = request.GET.get("display_size", "large")
        if display_size_param == "small":
            display_cell_size = 20
        elif display_size_param == "large":
            display_cell_size = 60  # Changed from 80 to 60
        else:  # medium or default
            display_cell_size = 40
        
        render_height = instance.device_type.u_height * 2 * display_cell_size + instance.device_type.u_height * 2
        
        return {
            "device_view": models.DeviceView.objects.filter(
                device_type=instance.device_type
            ).first(),
            "dv": dv,
            "modules": modules,
            "render_height": render_height,
            "ports_chassis": ports_chassis,
            "cable_colors": request.GET.get("cable_colors", "vlan_role"),
            "port_type": request.GET.get("port_type", "vlan_letter"),
            "display_size": display_size_param,
            "link_type": request.GET.get("link_type", "interface"),
            "something_else": request.GET.get("something_else", "off"),
        }

    def get_object(self, **kwargs):
        return Device.objects.get(pk=kwargs.get("pk"))


class DeviceElevationView(DjangoView): # Changed to DjangoView
    def get(self, request):
        site_slug = request.GET.get('site_slug')
        rack_id = request.GET.get('rack_id')
        
        devices_to_display = Device.objects.none()
        site = None # Initialize site
        rack = None # Initialize rack
        
        all_sites = Site.objects.all()
        racks_for_dropdown = Rack.objects.none()

        if site_slug:
            try:
                site = Site.objects.get(slug=site_slug)
                devices_to_display = Device.objects.filter(site=site).prefetch_related(
                    'device_type', 'modules', 'interfaces', 'frontports', 'rearports', 'virtual_chassis__members'
                )
                racks_for_dropdown = Rack.objects.filter(site=site)
            except Site.DoesNotExist:
                site_slug = None # Clear invalid site slug
                racks_for_dropdown = Rack.objects.all() # Show all racks if site is invalid
                pass 
        elif rack_id:
            try:
                rack = Rack.objects.get(pk=rack_id)
                devices_to_display = Device.objects.filter(rack=rack).prefetch_related(
                    'device_type', 'modules', 'interfaces', 'frontports', 'rearports', 'virtual_chassis__members'
                )
                # If a rack is selected, we might still want to show its site's racks or all racks
                # For simplicity now, if rack is chosen directly, site context for dropdown might not be primary
                if rack.site:
                    racks_for_dropdown = Rack.objects.filter(site=rack.site)
                    site = rack.site # Set current site based on selected rack
                else:
                    racks_for_dropdown = Rack.objects.all() # Or just this rack, or all racks
            except Rack.DoesNotExist:
                rack_id = None # Clear invalid rack id
                racks_for_dropdown = Rack.objects.all()
                pass
        else: # Neither site_slug nor rack_id provided
            racks_for_dropdown = Rack.objects.all()


        prepared_devices_data = []
        # Use the existing models import
        # device_view_model = apps.get_model('netbox_device_view', 'DeviceView')
        
        # Filter for devices that actually have a DeviceView definition for their type
        # This requires getting the device_type IDs for which a DeviceView exists
        device_types_with_view = models.DeviceView.objects.values_list('device_type_id', flat=True)
        
        # Further filter devices_to_display
        devices_with_view_defined = devices_to_display.filter(device_type_id__in=device_types_with_view)

        display_size_param = request.GET.get("display_size", "large")

        for device in devices_with_view_defined[:50]: # Limit to 50 devices
            instance_id = f"dev-{device.pk}"
            dv_css_map, modules_map, ports_chassis_map = prepare(device, instance_prefix=instance_id)
            
            if dv_css_map is not None:
                if display_size_param == "small":
                    display_cell_size = 20
                elif display_size_param == "large":
                    display_cell_size = 60  # Changed from 80 to 60
                else:  # medium or default
                    display_cell_size = 40
                
                device_render_height = device.device_type.u_height * 2 * display_cell_size + device.device_type.u_height * 2
                
                prepared_devices_data.append({
                    'device_obj': device,
                    'instance_id': instance_id,
                    'dv_css_map': dv_css_map,
                    'modules_map': modules_map,
                    'ports_chassis_map': ports_chassis_map,
                    'device_render_height': device_render_height
                })
        
        return render(request, 'netbox_device_view/device_elevation.html', {
            'prepared_devices': prepared_devices_data,
            'title': 'Device Elevation',
            'site': site,
            'rack': rack,
            'all_sites': all_sites,
            'racks_for_dropdown': racks_for_dropdown,
            'selected_site_slug': site_slug,
            'selected_rack_id': int(rack_id) if rack_id else None,
            # Pass query params to template for potential use in regenerating links or options
            'cable_colors': request.GET.get("cable_colors", "vlan_role"),
            'port_type': request.GET.get("port_type", "vlan_letter"),
            'display_size': display_size_param,
            'link_type': request.GET.get("link_type", "interface"),
        })

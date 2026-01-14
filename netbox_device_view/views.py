from netbox.views import generic
from dcim.models import Device, Site, Rack
from . import forms, models, tables, filtersets
from utilities.views import ViewTab, register_model_view
# utilities.permissions.PermissionRequiredMixin was incorrect, removed.
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin # Standard Django mixins
from .utils import prepare
from django.http import HttpResponse
from django.shortcuts import render
from django.apps import apps
from django.views import View as DjangoView
from django.conf import settings
import pprint

from netbox.views.generic import BulkImportView
from .forms import DeviceViewImportForm


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
        display_size_param = request.GET.get("display_size", "medium")
        if display_size_param == "small":
            display_cell_size = 20
        elif display_size_param == "large":
            display_cell_size = 60
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


class DeviceElevationView(LoginRequiredMixin, PermissionRequiredMixin, DjangoView): # DjangoView is alias for django.views.View
    permission_required = 'dcim.view_device' # Standard Django PermissionRequiredMixin accepts a string for a single perm
    # login_url = '/login/' # Optional: if NetBox login URL is different or needs to be explicit
    # raise_exception = True # Optional: to raise 403 if logged in but no perm, instead of redirect

    def _get_context(self, request):
        site_slug = request.GET.get('site_slug')
        rack_id = request.GET.get('rack_id')
        
        devices_to_display = Device.objects.none()
        site = None
        rack = None
        
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
                site_slug = None
                racks_for_dropdown = Rack.objects.all()
                pass
        elif rack_id:
            try:
                rack = Rack.objects.get(pk=rack_id)
                devices_to_display = Device.objects.filter(rack=rack).prefetch_related(
                    'device_type', 'modules', 'interfaces', 'frontports', 'rearports', 'virtual_chassis__members'
                )
                if rack.site:
                    racks_for_dropdown = Rack.objects.filter(site=rack.site)
                    site = rack.site
                else:
                    racks_for_dropdown = Rack.objects.all()
            except Rack.DoesNotExist:
                rack_id = None
                racks_for_dropdown = Rack.objects.all()
                pass
        else:
            racks_for_dropdown = Rack.objects.all()


        prepared_devices_data = []
        
        device_types_with_view = models.DeviceView.objects.values_list('device_type_id', flat=True)
        
        devices_with_view_defined = devices_to_display.filter(device_type_id__in=device_types_with_view)

        display_size_param = request.GET.get("display_size", "medium")

        for device in devices_with_view_defined[:50]:
            instance_id = f"dev-{device.pk}"
            dv_css_map, modules_map, ports_chassis_map = prepare(device, instance_prefix=instance_id)
            
            if dv_css_map is not None:
                if display_size_param == "small":
                    display_cell_size = 20
                elif display_size_param == "large":
                    display_cell_size = 60
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
        
        return {
            'prepared_devices': prepared_devices_data,
            'title': 'Device Elevation',
            'site': site,
            'rack': rack,
            'all_sites': all_sites,
            'racks_for_dropdown': racks_for_dropdown,
            'selected_site_slug': site_slug,
            'selected_rack_id': int(rack_id) if rack_id else None,
            'cable_colors': request.GET.get("cable_colors", "vlan_role"),
            'port_type': request.GET.get("port_type", "vlan_letter"),
            'display_size': display_size_param,
            'link_type': request.GET.get("link_type", "interface"),
        }

    def get(self, request):
        context = self._get_context(request)
        return render(request, 'netbox_device_view/device_elevation.html', context)


# Define the view class without decorator first
class SiteDeviceElevationView(generic.ObjectView):
    queryset = Site.objects.all()
    template_name = 'netbox_device_view/site_device_elevation.html'

    def get_extra_context(self, request, instance):
        request.GET = request.GET.copy()
        request.GET['site_slug'] = instance.slug

        # Re-implement the context gathering from DeviceElevationView
        site_slug = request.GET.get('site_slug')
        devices_to_display = Device.objects.filter(site__slug=site_slug).prefetch_related(
            'device_type', 'modules', 'interfaces', 'frontports', 'rearports', 'virtual_chassis__members'
        )

        prepared_devices_data = []
        device_types_with_view = models.DeviceView.objects.values_list('device_type_id', flat=True)
        devices_with_view_defined = devices_to_display.filter(device_type_id__in=device_types_with_view)
        display_size_param = request.GET.get("display_size", "medium")

        for device in devices_with_view_defined[:50]:
            instance_id = f"dev-{device.pk}"
            dv_css_map, modules_map, ports_chassis_map = prepare(device, instance_prefix=instance_id)
            
            if dv_css_map is not None:
                if display_size_param == "small":
                    display_cell_size = 20
                elif display_size_param == "large":
                    display_cell_size = 60
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

        return {
            'prepared_devices': prepared_devices_data,
            'title': 'Port View',
            'cable_colors': request.GET.get("cable_colors", "vlan_role"),
            'port_type': request.GET.get("port_type", "vlan_letter"),
            'display_size': display_size_param,
            'link_type': request.GET.get("link_type", "interface"),
        }

    tab = ViewTab(
        label=settings.PLUGINS_CONFIG.get('netbox_device_view', {}).get('ports_tab_label', 'Port View'),
        badge=lambda obj: obj.devices.filter(
            device_type_id__in=models.DeviceView.objects.values_list('device_type_id', flat=True)
        ).count(),
        hide_if_empty=True,
    )


# Conditionally register the view based on plugin settings
if settings.PLUGINS_CONFIG.get('netbox_device_view', {}).get('show_site_ports', True):
    SiteDeviceElevationView = register_model_view(Site, name='ports', path='ports')(SiteDeviceElevationView)

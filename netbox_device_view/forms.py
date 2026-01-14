from netbox.forms import NetBoxModelForm, NetBoxModelImportForm
from django.utils.translation import gettext_lazy as _
from django import forms
from .models import DeviceView
from dcim.models import DeviceType
from utilities.forms.fields import CSVModelChoiceField, CSVModelMultipleChoiceField
from utilities.forms.widgets import APISelectMultiple


class DeviceViewForm(NetBoxModelForm):
    device_types = forms.ModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        required=True,
        widget=APISelectMultiple(
            api_url="/api/dcim/device-types/",
        ),
        help_text="Select one or more device types that will use this view"
    )
    
    class Meta:
        model = DeviceView
        fields = ("name", "device_types", "grid_template_area", "tags")
    
    def clean_device_types(self):
        """Validate that selected device types aren't already assigned to other views"""
        device_types = self.cleaned_data['device_types']
        
        # Check if any of the selected device types are already assigned
        for dt in device_types:
            existing = DeviceView.objects.filter(device_types=dt)
            if self.instance.pk:
                # Exclude current instance when editing
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f"Device type '{dt.model}' is already assigned to another view: {existing.first()}"
                )
        
        return device_types


class DeviceViewImportForm(NetBoxModelImportForm):
    device_types = CSVModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        to_field_name="model",
        help_text=_("Device Model Names (comma-separated)"),
    )

    class Meta:
        model = DeviceView
        fields = ("name", "device_types", "grid_template_area")

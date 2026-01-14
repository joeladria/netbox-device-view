from netbox.filtersets import NetBoxModelFilterSet
import django_filters
from dcim.models import DeviceType
from .models import DeviceView


class DeviceViewFilterSet(NetBoxModelFilterSet):
    device_types = django_filters.ModelMultipleChoiceFilter(
        queryset=DeviceType.objects.all(),
        label='Device Types',
    )
    
    class Meta:
        model = DeviceView
        fields = ("id", "name", "device_types")

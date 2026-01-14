from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer
from dcim.models import DeviceType
from dcim.api.serializers import DeviceTypeSerializer
from ..models import DeviceView


class DeviceViewSerializer(NetBoxModelSerializer):
    device_types = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=DeviceType.objects.all()
    )
    device_types_detail = DeviceTypeSerializer(
        many=True,
        read_only=True,
        source='device_types'
    )
    
    class Meta:
        model = DeviceView
        fields = (
            "id",
            "display",
            "name",
            "device_types",
            "device_types_detail",
            "grid_template_area",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )

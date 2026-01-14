from django.contrib.postgres.fields import ArrayField
from django.db import models

from netbox.models import NetBoxModel


class DeviceView(NetBoxModel):
    device_types = models.ManyToManyField(
        to="dcim.DeviceType",
        related_name="device_views",
        blank=False,
    )

    grid_template_area = models.TextField(blank=False)
    
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional name for this device view"
    )

    class Meta:
        ordering = ("id",)

    def __str__(self):
        if self.name:
            return self.name
        # Safely handle M2M access during deletion to avoid RecursionError
        try:
            types = self.device_types.all()
            if types.count() == 1:
                return types.first().model
            elif types.count() > 1:
                return f"View for {types.count()} device types"
        except:
            # During deletion or if M2M is unavailable, use pk
            pass
        return f"DeviceView #{self.pk}"
    
    @property
    def device_type_list(self):
        """Return comma-separated list of device type models"""
        return ", ".join([dt.model for dt in self.device_types.all()])

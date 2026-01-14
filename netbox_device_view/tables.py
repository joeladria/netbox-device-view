import django_tables2 as tables

from netbox.tables import NetBoxTable, ChoiceFieldColumn
from .models import DeviceView


class DeviceViewTable(NetBoxTable):
    name = tables.Column(
        linkify=True
    )
    device_types = tables.TemplateColumn(
        template_code="""
        {% for dt in record.device_types.all %}
            <a href="{% url 'dcim:devicetype' pk=dt.pk %}">{{ dt.model }}</a>{% if not forloop.last %}, {% endif %}
        {% endfor %}
        """,
        verbose_name="Device Types"
    )
    
    class Meta(NetBoxTable.Meta):
        model = DeviceView
        fields = ("pk", "id", "name", "device_types", "grid_template_area")
        default_columns = ("name", "device_types", "grid_template_area")

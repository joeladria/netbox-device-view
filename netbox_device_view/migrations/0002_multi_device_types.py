# Migration to convert device_type ForeignKey to device_types ManyToManyField

from django.db import migrations, models


def migrate_device_types_forward(apps, schema_editor):
    """Migrate existing ForeignKey relationships to ManyToMany"""
    DeviceView = apps.get_model('netbox_device_view', 'DeviceView')
    
    # For each existing DeviceView, copy the device_type to device_types
    # Use .order_by() to override default model ordering which references old field
    for device_view in DeviceView.objects.all().order_by():
        # Get the old device_type_id from the temporary field
        old_device_type_id = getattr(device_view, '_old_device_type_id', None)
        if old_device_type_id:
            # Add the single device type to the M2M field
            device_view.device_types.add(old_device_type_id)


def migrate_device_types_backward(apps, schema_editor):
    """Reverse migration - not fully reversible if multiple types assigned"""
    DeviceView = apps.get_model('netbox_device_view', 'DeviceView')
    
    for device_view in DeviceView.objects.all():
        types = device_view.device_types.all()
        if types.exists():
            # Take the first device type as the single FK
            device_view._old_device_type_id = types.first().id
            device_view.save()


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_device_view', '0001_initial'),
        ('dcim', '0172_larger_power_draw_values'),
    ]

    operations = [
        # Step 1: Rename old field to temporary name
        migrations.RenameField(
            model_name='deviceview',
            old_name='device_type',
            new_name='_old_device_type_id',
        ),
        
        # Step 2: Create new M2M field
        migrations.AddField(
            model_name='deviceview',
            name='device_types',
            field=models.ManyToManyField(
                to='dcim.DeviceType',
                related_name='device_views',
            ),
        ),
        
        # Step 3: Migrate data from old FK to new M2M
        migrations.RunPython(
            migrate_device_types_forward,
            migrate_device_types_backward
        ),
        
        # Step 4: Remove old FK field
        migrations.RemoveField(
            model_name='deviceview',
            name='_old_device_type_id',
        ),
        
        # Step 5: Add name field
        migrations.AddField(
            model_name='deviceview',
            name='name',
            field=models.CharField(
                max_length=100,
                blank=True,
                default='',
                help_text='Optional name for this device view',
            ),
        ),
        
        # Step 6: Update ordering
        migrations.AlterModelOptions(
            name='deviceview',
            options={'ordering': ('id',)},
        ),
    ]

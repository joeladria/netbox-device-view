# Upgrade Notes: Multi-Device Type Support

## Overview

DeviceView now supports assigning multiple Device Types to a single view definition. This allows you to reuse the same view configuration across similar device models (e.g., C9200-24P, C9200-48P, C9200L-24P).

## Breaking Changes

### Database Schema
- `device_type` ForeignKey → `device_types` ManyToManyField
- New `name` CharField added (optional)
- Ordering changed from `device_type` to `id`

### API Changes
- **Request Format**: `device_type` (single ID) → `device_types` (array of IDs)
- **Response Format**: Returns array of device types instead of single value
- **New Field**: `device_types_detail` provides full nested DeviceType objects

### Python Code
Any custom code referencing `device_view.device_type` must be updated:
- For single device type: `device_view.device_types.first()`
- For all device types: `device_view.device_types.all()`

## Migration Process

### Step 1: Backup Your Database
```bash
# Backup your NetBox database before proceeding
pg_dump netbox > netbox_backup_$(date +%Y%m%d).sql
```

### Step 2: Update Plugin Code
```bash
cd /path/to/netbox-device-view
git pull
# OR if you have local changes
git stash
git pull
git stash pop
```

### Step 3: Run Migration
```bash
# Activate NetBox virtual environment
source /opt/netbox/venv/bin/activate

# Run migrations
cd /opt/netbox/netbox
python manage.py migrate netbox_device_view

# The migration will:
# 1. Preserve all existing device_type assignments
# 2. Convert them to many-to-many relationships
# 3. Add the optional 'name' field
```

### Step 4: Restart NetBox
```bash
sudo systemctl restart netbox netbox-rq
```

## New Features

### 1. Multi-Device Type Assignment
- Select multiple device types when creating/editing a DeviceView
- All selected device types will use the same view definition

### 2. Duplicate Prevention
- Form validation prevents assigning a device type to multiple views
- Clear error messages guide users

### 3. Optional Naming
- Add a descriptive name to DeviceViews with multiple types
- Falls back to "View for N device types" if unnamed

### 4. Enhanced Display
- Admin table shows all assigned device types with links
- Comma-separated display in listings

## Usage Examples

### Creating a View for Multiple Types

**Via Web UI:**
1. Navigate to Plugins → Device Views → Add
2. Enter optional name: "Catalyst 9200 Series"
3. Select multiple device types:
   - C9200-24P
   - C9200-48P
   - C9200L-24P
4. Add grid_template_area CSS
5. Save

**Via API:**
```bash
curl -X POST https://netbox.example.com/api/plugins/netbox-device-view/device-views/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Catalyst 9200 Series",
    "device_types": [1, 2, 3],
    "grid_template_area": "..."
  }'
```

### Querying Views with Multiple Types

**Python:**
```python
from netbox_device_view.models import DeviceView

# Get all device types for a view
view = DeviceView.objects.first()
device_types = view.device_types.all()

# Get comma-separated list
type_list = view.device_type_list

# Find view for a specific device type
device_type_id = 5
views = DeviceView.objects.filter(device_types=device_type_id)
```

**API:**
```bash
# Get all views
curl https://netbox.example.com/api/plugins/netbox-device-view/device-views/

# Filter by device type
curl "https://netbox.example.com/api/plugins/netbox-device-view/device-views/?device_types=1,2,3"
```

## Rollback Instructions

If you need to rollback (must be done BEFORE assigning multiple types to any view):

```bash
# Activate NetBox virtual environment
source /opt/netbox/venv/bin/activate

# Rollback migration
cd /opt/netbox/netbox
python manage.py migrate netbox_device_view 0001_initial

# Restart NetBox
sudo systemctl restart netbox netbox-rq
```

**Warning**: Rollback is only safe if you haven't assigned multiple device types to any view. If you have, the rollback will only preserve the first device type of each view.

## Data Migration Details

The migration automatically:
1. ✅ Preserves all existing device_type → DeviceView relationships
2. ✅ Converts them to the new many-to-many structure
3. ✅ Zero data loss for existing configurations
4. ✅ Adds empty 'name' field (can be filled later)

## Validation Rules

### Form Validation
- At least one device type must be selected
- A device type cannot be assigned to multiple DeviceViews
- Error message shows which view already has the device type

### API Validation
- `device_types` array cannot be empty
- All device type IDs must exist
- Duplicate assignments are rejected with 400 error

## Testing Checklist

After migration, verify:
- [ ] Existing DeviceViews still display correctly
- [ ] Device detail pages show "Device View" tab for configured types
- [ ] Site "Port View" tab shows devices with views
- [ ] Can create new DeviceView with single device type
- [ ] Can create new DeviceView with multiple device types
- [ ] Can edit existing view to add more device types
- [ ] Cannot assign same device type to two different views
- [ ] API returns device_types as array
- [ ] API accepts device_types as array

## Support

If you encounter issues:
1. Check NetBox logs: `journalctl -u netbox -f`
2. Check migration was successful: `python manage.py showmigrations netbox_device_view`
3. Report issues with full error messages and logs

## Performance Notes

No significant performance impact expected. The many-to-many relationship uses a standard Django junction table with proper indexes.

# Grafana Dashboard Provisioning Guide

## Table of Contents
1. [Overview](#overview)
2. [Current Provisioning Architecture](#current-provisioning-architecture)
3. [Dashboard Provisioning Lifecycle](#dashboard-provisioning-lifecycle)
4. [How It Works: New Organization](#how-it-works-new-organization)
5. [Dashboard Template Management](#dashboard-template-management)
6. [Updating Dashboards](#updating-dashboards)
7. [Proposed Improvements](#proposed-improvements)
8. [Implementation Guide](#implementation-guide)
9. [Troubleshooting](#troubleshooting)

---

## Overview

IoTDash automates the provisioning of Grafana dashboards for each organization. When a new organization is created, the system:
1. Creates a dedicated Grafana organization
2. Provisions an InfluxDB datasource
3. Deploys a default "IoT Metrics" dashboard from a template
4. Records the dashboard UID in the database for future reference

This ensures consistent dashboard setup across all organizations while maintaining data isolation.

---

## Current Provisioning Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     IoTDash Backend                        │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │   Admin Orgs Router                                  │ │
│  │   /api/admin/organisations                          │ │
│  │                                                      │ │
│  │   POST /  → Creates org + provisions Grafana        │ │
│  └────────────────┬─────────────────────────────────────┘ │
│                   │                                        │
│  ┌────────────────▼─────────────────────────────────────┐ │
│  │   GrafanaClient Service                              │ │
│  │                                                      │ │
│  │   - create_org()                                    │ │
│  │   - add_datasource_to_org()                        │ │
│  │   - create_dashboard_in_org()                      │ │
│  └────────────────┬─────────────────────────────────────┘ │
└───────────────────┼──────────────────────────────────────┘
                    │
                    │ HTTP API
                    │
┌───────────────────▼──────────────────────────────────────┐
│                    Grafana                               │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Org 1     │  │   Org 2     │  │   Org 3     │     │
│  │             │  │             │  │             │     │
│  │ Dashboard A │  │ Dashboard A │  │ Dashboard A │     │
│  │ InfluxDB DS │  │ InfluxDB DS │  │ InfluxDB DS │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└──────────────────────────────────────────────────────────┘
```

### File Structure

```
iotdash/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   └── admin_orgs.py          # Org creation logic
│   │   └── services/
│   │       └── grafana_client.py      # Grafana API client
├── grafana/
│   ├── grafana.ini                     # Grafana config
│   └── provisioning/
│       ├── datasources/
│       │   └── influxdb.yaml           # Default datasource (unused)
│       └── dashboards/
│           ├── dashboards.yaml         # Provisioning config (unused)
│           └── iot-metrics.json        # Dashboard template ✅
```

**Note**: The files in `grafana/provisioning/datasources/` and `grafana/provisioning/dashboards/dashboards.yaml` are NOT used for per-org provisioning. They would only provision to the default Grafana org. Instead, we use the Grafana API to provision each org dynamically.

---

## Dashboard Provisioning Lifecycle

### Phase 1: Organization Creation

**Trigger**: Admin creates new organization via IoTDash admin panel

**Backend Flow** (`admin_orgs.py:create_org()`):

```python
1. Validate organization name (no duplicates)
2. Create Organisation record in PostgreSQL
3. Call GrafanaClient.create_org(org_name)
   └─> POST /api/orgs
       Returns: grafana_org_id
4. Store grafana_org_id in Organisation.grafana_org_id
5. Call GrafanaClient.add_datasource_to_org(grafana_org_id)
   └─> POST /api/datasources (with X-Grafana-Org-Id header)
       Creates InfluxDB datasource in the org
6. Load dashboard template from iot-metrics.json
7. Call GrafanaClient.create_dashboard_in_org(grafana_org_id, dashboard_json)
   └─> POST /api/dashboards/db (with X-Grafana-Org-Id header)
       Returns: dashboard_uid
8. Create GrafanaDashboard record in PostgreSQL
9. Commit transaction
```

### Phase 2: User Access

**SSO Authentication**:
- User logs into IoTDash
- JWT token includes organisation_id
- When accessing Grafana, auth proxy sets X-Grafana-Org-Id header
- User sees only their org's dashboards

### Phase 3: Dashboard Evolution

**Currently**:
- Dashboards are created once and never updated by the system
- Users can manually edit dashboards in Grafana
- Changes persist in Grafana's database
- No version control or rollback capability

**Issue**:
- If template is updated, existing orgs don't get updates
- No migration path for dashboard schema changes

---

## How It Works: New Organization

### Step-by-Step Example

**Scenario**: Admin creates "Acme Corp" organization

```bash
# Admin submits form in IoTDash
POST /api/admin/organisations
{
  "name": "Acme Corp"
}
```

**Backend Processing**:

```python
# 1. Create DB record
org = Organisation(name="Acme Corp")
db.add(org)
db.flush()  # Get org.id

# 2. Create Grafana org
grafana_org_id = grafana.create_org("Acme Corp")
# → Grafana creates org with ID 5

# 3. Add datasource
grafana.add_datasource_to_org(grafana_org_id=5)
# → POST /api/datasources with header X-Grafana-Org-Id: 5
# → Creates InfluxDB datasource pointing to influxdb:8086

# 4. Load template
with open("/app/grafana/provisioning/dashboards/iot-metrics.json") as f:
    dashboard_json = json.load(f)

# 5. Reset IDs (Grafana assigns new ones)
dashboard_json["id"] = None
dashboard_json["uid"] = None  # Optional, Grafana generates if missing

# 6. Create dashboard
dashboard_uid = grafana.create_dashboard_in_org(
    org_id=5,
    dashboard_json=dashboard_json
)
# → POST /api/dashboards/db with header X-Grafana-Org-Id: 5
# → Returns: { "uid": "abc123xyz" }

# 7. Record dashboard metadata
dashboard_record = GrafanaDashboard(
    organisation_id=org.id,
    title="IoT Metrics",
    grafana_uid="abc123xyz",
    grafana_org_id=5,
    panel_ids=[1, 2, 3, 4],  # From dashboard_json
    embed_base_url="http://grafana:3000"
)
db.add(dashboard_record)

# 8. Commit
db.commit()
```

**Result**:
- Acme Corp users can now access their isolated Grafana org
- Default dashboard shows temperature, humidity, pressure panels
- Ready to receive device data

---

## Dashboard Template Management

### Current Template Location

**File**: `grafana/provisioning/dashboards/iot-metrics.json`

**Structure**:
```json
{
  "id": null,
  "uid": null,
  "title": "IoT Metrics",
  "tags": ["iot", "devices"],
  "timezone": "browser",
  "panels": [
    {
      "id": 1,
      "title": "Temperature Over Time",
      "type": "graph",
      "datasource": "InfluxDB",
      "targets": [
        {
          "measurement": "mqtt_consumer",
          "select": [[{"type": "field", "params": ["temperature"]}]],
          "groupBy": [{"type": "time", "params": ["1m"]}]
        }
      ],
      "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}
    },
    // ... more panels
  ],
  "templating": { "list": [] },
  "time": { "from": "now-6h", "to": "now" },
  "refresh": "1m"
}
```

### Editing the Template

**Method 1: Edit JSON directly**
```bash
# 1. Edit the file
vim grafana/provisioning/dashboards/iot-metrics.json

# 2. Rebuild backend container (to copy new file)
docker compose up -d --build backend

# 3. New orgs will get updated template
# Existing orgs remain unchanged ❌
```

**Method 2: Export from Grafana**
```bash
# 1. Create test org and customize dashboard in Grafana UI
# 2. Export dashboard JSON (Share → Export)
# 3. Save to iot-metrics.json
# 4. Clean up: remove "id" and org-specific fields
# 5. Rebuild containers
```

---

## Updating Dashboards

### Current Limitation

⚠️ **There is NO automated way to update dashboards for existing organizations.**

Once a dashboard is provisioned, it lives in Grafana's database. Template changes only affect new organizations.

### Manual Update Process

**Option 1: Manual Update in Grafana**
```
1. Admin logs into each org's Grafana
2. Manually edits dashboard to match new template
3. Saves changes
4. Repeat for all orgs
```
❌ **Not scalable** for > 5 organizations

**Option 2: API-Based Update (Custom Script)**
```python
# Pseudo-code
for org in organisations:
    grafana.switch_to_org(org.grafana_org_id)
    dashboard = grafana.get_dashboard(org.dashboard_uid)

    # Update specific panel
    dashboard["panels"].append(new_panel_config)

    grafana.update_dashboard(dashboard)
```
✅ **Scalable** but requires development

**Option 3: Delete and Recreate**
```python
# ⚠️ DESTRUCTIVE: Loses user customizations
grafana.delete_dashboard(org.dashboard_uid)
new_uid = grafana.create_dashboard(updated_template)
```
❌ **Loses user customizations**

---

## Proposed Improvements

### 1. Dashboard Versioning

**Problem**: No tracking of dashboard versions
**Solution**: Add version metadata to template and DB

```json
// iot-metrics.json
{
  "title": "IoT Metrics",
  "version": 2,
  "changelog": "Added CO2 metric panel",
  "panels": [...]
}
```

```python
# GrafanaDashboard model
class GrafanaDashboard(Base):
    # ... existing fields
    template_version = Column(Integer, default=1)
    last_updated = Column(DateTime)
```

**Migration Strategy**:
```python
def migrate_dashboards_to_v2():
    for org in orgs:
        dashboard = get_current_dashboard(org)
        if dashboard.template_version < 2:
            apply_v2_changes(dashboard)
            dashboard.template_version = 2
            save_dashboard(dashboard)
```

### 2. Dashboard Update API

**New Endpoint**: `POST /api/admin/dashboards/update`

```python
@router.post("/dashboards/update")
def update_dashboards(
    target_version: int,
    org_ids: list[UUID] | None = None,  # None = all orgs
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update dashboards to target version.
    Applies migrations defined in dashboard_migrations.py
    """
    orgs_to_update = (
        db.query(Organisation).filter(Organisation.id.in_(org_ids)).all()
        if org_ids
        else db.query(Organisation).all()
    )

    results = []
    for org in orgs_to_update:
        try:
            migrate_dashboard(org, target_version)
            results.append({"org_id": org.id, "status": "success"})
        except Exception as e:
            results.append({"org_id": org.id, "status": "failed", "error": str(e)})

    return results
```

### 3. Dashboard Templates Directory

**Problem**: Only one template (iot-metrics.json)
**Solution**: Support multiple template types

```
grafana/provisioning/dashboards/
├── templates/
│   ├── iot-metrics-v1.json
│   ├── iot-metrics-v2.json
│   ├── environmental-monitoring.json
│   └── power-management.json
├── migrations/
│   ├── v1_to_v2.py
│   └── v2_to_v3.py
└── dashboards.yaml
```

**Template Selection**:
```python
@router.post("/organisations")
def create_org(
    body: OrgCreate,
    template: str = "iot-metrics-v2",  # New parameter
    ...
):
    dashboard_json = load_template(template)
    ...
```

### 4. Dashboard Backup & Restore

**Automatic Backups**:
```python
def backup_dashboard(org_id: UUID, dashboard_uid: str):
    """Backup dashboard JSON before updates"""
    dashboard = grafana.get_dashboard(dashboard_uid)
    backup_path = f"/backups/{org_id}/{dashboard_uid}_{datetime.now().isoformat()}.json"
    with open(backup_path, "w") as f:
        json.dump(dashboard, f)
```

**Restore API**:
```python
@router.post("/dashboards/{org_id}/restore")
def restore_dashboard(
    org_id: UUID,
    backup_timestamp: str,
    ...
):
    backup_file = f"/backups/{org_id}/*_{backup_timestamp}.json"
    with open(backup_file) as f:
        dashboard = json.load(f)
    grafana.update_dashboard(dashboard)
```

### 5. Template Validation

**Pre-deployment Validation**:
```python
def validate_dashboard_template(template_path: str):
    """
    Validate template before deployment:
    - Valid JSON
    - Required fields present
    - Panel IDs unique
    - Datasource references valid
    """
    with open(template_path) as f:
        template = json.load(f)

    assert "title" in template
    assert "panels" in template
    assert all("id" in p for p in template["panels"])

    panel_ids = [p["id"] for p in template["panels"]]
    assert len(panel_ids) == len(set(panel_ids)), "Duplicate panel IDs"

    return True
```

**CI/CD Integration**:
```yaml
# .github/workflows/validate-dashboards.yml
name: Validate Dashboards
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Templates
        run: python tools/validate_dashboard_templates.py
```

---

## Implementation Guide

### Adding a New Panel to Template

**Scenario**: Add CO2 metric panel to default template

**Step 1: Export Current Dashboard**
```bash
# In Grafana UI:
# 1. Navigate to IoT Metrics dashboard
# 2. Click Share icon → Export → Save to file
# 3. Download dashboard.json
```

**Step 2: Add Panel via Grafana UI**
```
1. Add new panel
2. Configure:
   - Data source: InfluxDB
   - Measurement: mqtt_consumer
   - Field: co2_ppm
   - Visualization: Graph
3. Save dashboard
4. Export again
```

**Step 3: Extract New Panel**
```bash
# Compare old and new exports
diff old-dashboard.json new-dashboard.json > changes.diff

# Extract new panel JSON (look for panel with new ID)
jq '.panels[] | select(.title == "CO2 Level")' new-dashboard.json > co2-panel.json
```

**Step 4: Update Template**
```bash
# Edit iot-metrics.json
vim grafana/provisioning/dashboards/iot-metrics.json

# Add new panel to "panels" array
# Assign unique panel ID (e.g., 5)
# Adjust gridPos to position on dashboard
```

**Step 5: Test**
```bash
# Create test org to verify template
docker compose exec backend python -c "
from app.database import SessionLocal
from app.services.grafana_client import GrafanaClient
from app.models import Organisation

db = SessionLocal()
grafana = GrafanaClient()

# Create test org
org = Organisation(name='Test Org CO2')
db.add(org)
db.flush()

grafana_org_id = grafana.create_org('Test Org CO2')
org.grafana_org_id = grafana_org_id
# ... provision dashboard

db.commit()
"

# Verify in Grafana UI
# Delete test org when done
```

**Step 6: Deploy**
```bash
# Rebuild and restart
docker compose up -d --build backend

# New orgs will get CO2 panel
# Existing orgs: use migration script (see proposed improvements)
```

---

## Troubleshooting

### Dashboard Not Appearing for New Org

**Check**:
```bash
# 1. Verify org created in Grafana
docker compose exec grafana curl -u admin:admin http://localhost:3000/api/orgs | jq

# 2. Check IoTDash database
docker compose exec backend python -c "
from app.database import SessionLocal
from app.models import Organisation
db = SessionLocal()
orgs = db.query(Organisation).all()
for org in orgs:
    print(f'{org.name}: grafana_org_id={org.grafana_org_id}')
"

# 3. Check dashboard record
docker compose exec backend python -c "
from app.database import SessionLocal
from app.models import GrafanaDashboard
db = SessionLocal()
dashboards = db.query(GrafanaDashboard).all()
for dash in dashboards:
    print(f'{dash.title}: uid={dash.grafana_uid}, org={dash.grafana_org_id}')
"
```

**Common Issues**:
- Grafana API unreachable (check `GRAFANA_URL` in .env)
- Invalid credentials (check `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`)
- Template JSON malformed (validate with `jq . iot-metrics.json`)

### Template Changes Not Applied

**Reason**: Template file not copied to container

**Fix**:
```bash
# Force rebuild
docker compose down
docker compose build --no-cache backend
docker compose up -d

# Verify file in container
docker compose exec backend cat /app/grafana/provisioning/dashboards/iot-metrics.json
```

### Datasource Not Found in Dashboard

**Check Datasource Name**:
```bash
# List datasources in org
docker compose exec grafana curl -u admin:admin \
  -H "X-Grafana-Org-Id: 2" \
  http://localhost:3000/api/datasources | jq

# Update template to match datasource name/UID
```

**Common Mismatch**:
- Template references `"datasource": "InfluxDB"`
- But created datasource is named `"datasource": "InfluxDB (IoTDash)"`

**Fix**: Update `add_datasource_to_org()` to use consistent name

---

## Best Practices

### Template Design

✅ **DO**:
- Use descriptive panel titles
- Set reasonable default time ranges (last 6h)
- Include helpful descriptions in panels
- Use variables for device selection
- Set appropriate Y-axis units

❌ **DON'T**:
- Hardcode device IDs in queries
- Use absolute time ranges
- Create > 12 panels per dashboard (performance)
- Forget to test template before deployment

### Deployment

✅ **DO**:
- Version templates (iot-metrics-v1, v2, etc.)
- Test templates in isolated Grafana org first
- Document changes in CHANGELOG
- Back up production databases before major updates

❌ **DON'T**:
- Deploy untested templates to production
- Update templates without version bump
- Delete old template versions (keep for rollback)

### Maintenance

✅ **DO**:
- Regularly review dashboard performance
- Archive unused panels/dashboards
- Monitor Grafana logs for errors
- Keep Grafana updated to latest stable version

---

## Future Roadmap

### Short-Term (1-3 months)
- [ ] Implement dashboard versioning
- [ ] Add migration scripts for v1 → v2
- [ ] Create backup/restore CLI tool
- [ ] Template validation in CI/CD

### Medium-Term (3-6 months)
- [ ] Dashboard update API endpoint
- [ ] Multi-template support
- [ ] Automated testing framework for dashboards
- [ ] Dashboard analytics (usage tracking)

### Long-Term (6-12 months)
- [ ] Visual template editor (no-code)
- [ ] Dashboard marketplace (community templates)
- [ ] AI-suggested panels based on device metrics
- [ ] Cross-org dashboard comparison tools

---

## References

- **Grafana HTTP API**: https://grafana.com/docs/grafana/latest/developers/http_api/
- **Dashboard Provisioning**: https://grafana.com/docs/grafana/latest/administration/provisioning/
- **InfluxDB Query Language**: https://docs.influxdata.com/influxdb/v1.8/query_language/
- **IoTDash Backend Code**: `backend/app/routers/admin_orgs.py`, `backend/app/services/grafana_client.py`

---

**Last Updated**: April 2026
**Version**: 1.0
**Maintainer**: IoTDash Team

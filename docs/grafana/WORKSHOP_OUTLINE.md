# Grafana Management Workshop for IoTDash
## 2-3 Hour Hands-On Training

---

## Workshop Overview

**Duration**: 2-3 hours (flexible based on audience)
**Level**: Intermediate (basic Grafana knowledge helpful but not required)
**Format**: Presentation + Hands-on Labs
**Prerequisites**:
- Access to IoTDash instance
- Admin or viewer account
- Laptop with web browser

**Learning Objectives**:
By the end of this workshop, participants will be able to:
1. Navigate and customize Grafana dashboards
2. Add new panels and visualizations
3. Understand the IoTDash data lifecycle
4. Manage growing metrics and optimize queries
5. Understand dashboard provisioning process
6. Apply best practices for dashboard management

---

## Agenda

| Time | Duration | Topic | Type |
|------|----------|-------|------|
| 0:00 | 15 min | Introduction & Setup | Lecture |
| 0:15 | 30 min | Grafana Basics & Navigation | Hands-on Lab |
| 0:45 | 45 min | Creating & Customizing Panels | Hands-on Lab |
| 1:30 | 15 min | **Break** | - |
| 1:45 | 30 min | Data Lifecycle & Query Optimization | Lecture + Demo |
| 2:15 | 30 min | Dashboard Provisioning & Automation | Lecture + Demo |
| 2:45 | 15 min | Q&A & Best Practices | Discussion |
| **3:00** | **Total** | **Workshop Complete** | - |

---

## Session 1: Introduction & Setup (15 min)

### 1.1 Welcome & Introductions (5 min)

**Facilitator Introduction**:
- Name, role, experience with IoTDash/Grafana

**Participant Introductions** (if < 10 people):
- Name, role, experience with Grafana
- What they hope to learn

**Workshop Goals**:
- Become proficient in Grafana dashboard management
- Understand IoTDash's data flow
- Learn to handle scaling metrics

### 1.2 Architecture Overview (10 min)

**Slide: IoTDash Data Flow**
```
Device (MQTT) → Telegraf → InfluxDB → Grafana
                                ↓
                          IoTDash Backend (Alerts)
```

**Key Concepts**:
- **MQTT**: Message protocol devices use to send data
- **Telegraf**: Collects and forwards metrics to InfluxDB
- **InfluxDB**: Time-series database storing metric data
- **Grafana**: Visualization layer (what we're learning today)

**Organization Isolation**:
- Each IoTDash org has its own Grafana organization
- Data is isolated between orgs
- Users only see their org's dashboards

**Access URLs**:
- IoTDash: `https://your-domain.com/`
- Grafana Direct: `https://your-domain.com/grafana/`

### 1.3 Environment Check (5 min)

**Hands-On: Verify Access**

1. Log into IoTDash
2. Navigate to Dashboard → Devices
3. Click on a device to see embedded Grafana panels
4. Open Grafana directly at `/grafana/`
5. Verify you can see "IoT Metrics" dashboard

**Troubleshooting**:
- Can't login? Check credentials with admin
- Don't see dashboards? Verify org assignment
- Grafana not loading? Check browser console for errors

---

## Session 2: Grafana Basics & Navigation (30 min)

### 2.1 Dashboard Tour (10 min)

**Demo: Navigate IoT Metrics Dashboard**

**Top Bar**:
- **Time Range Picker**: Last 6h, 24h, 7d, custom
- **Refresh Interval**: Auto-refresh settings
- **Zoom**: Time range zoom on graphs

**Panels**:
- Hover over panel → panel menu
- Click panel title → quick menu
- View (fullscreen), Edit, Share, More...

**Variables** (if enabled):
- Device selector
- Metric type selector

**Demo: Explore Tab**
```
1. Click Explore icon (compass) in sidebar
2. Select InfluxDB datasource
3. Write query:
   FROM mqtt_consumer
   WHERE device_code = 'sensor01'
   SELECT field(temperature)
4. Run query → See raw data
```

**Why Explore is Useful**:
- Test queries before adding to dashboard
- Debug "No Data" issues
- Explore available metrics

### 2.2 Understanding Panels (10 min)

**Panel Types Overview**:

1. **Time Series (Graph)**
   - Line charts showing data over time
   - Best for: Trends, historical analysis
   - Example: Temperature over last 24h

2. **Gauge**
   - Current value with min/max/thresholds
   - Best for: Real-time status, at-a-glance metrics
   - Example: Current battery level

3. **Stat**
   - Single value display (latest reading)
   - Best for: Key metrics, current state
   - Example: Last reported temperature

4. **Table**
   - Tabular data view
   - Best for: Multiple devices, detailed data
   - Example: All sensor readings

**Demo: Switch Panel Types**
```
1. Edit Temperature panel
2. Switch visualization: Graph → Gauge → Stat
3. Observe how same data looks different
4. Cancel changes (don't save)
```

### 2.3 Hands-On Lab 1: Explore Your Dashboard (10 min)

**Tasks**:
1. Change time range to "Last 24 hours"
2. Enable auto-refresh (30s interval)
3. View temperature panel in fullscreen mode
4. Use Explore tab to query humidity data for your device
5. Export dashboard JSON (Share → Export)

**Expected Outcomes**:
- Comfortable navigating Grafana UI
- Understand time range and refresh controls
- Know how to access Explore tab

**Facilitator Notes**:
- Walk around to help participants
- Common issues: Finding Explore, selecting datasource
- Have solution steps on screen for reference

---

## Session 3: Creating & Customizing Panels (45 min)

### 3.1 Adding a New Panel (15 min)

**Demo: Create Battery Gauge**

**Step-by-Step**:
```
1. Click "Add panel" → "Add a new panel"

2. Configure Query:
   Data Source: InfluxDB
   FROM: mqtt_consumer
   WHERE: device_code = 'sensor01'
   SELECT: field(battery) mean()
   GROUP BY: time(1m)

3. Choose Visualization:
   Type: Gauge

4. Configure Options:
   Title: Battery Level
   Description: Current battery percentage
   Unit: Percent (0-100)
   Min: 0
   Max: 100

5. Set Thresholds:
   0-20: Red (Low)
   20-50: Yellow (Medium)
   50-100: Green (Good)

6. Apply → Save dashboard
```

**Key Concepts**:
- **Aggregation**: Why use `mean()` vs `last()`?
  - `mean()`: Average over time window
  - `last()`: Most recent value
  - Use `last()` for gauge (current state)
- **GROUP BY time**: Reduces data points, improves performance

### 3.2 Query Patterns (10 min)

**Common Query Patterns**:

**Pattern 1: Single Device, Single Metric**
```flux
FROM mqtt_consumer
WHERE device_code = 'sensor01'
SELECT field(temperature) mean()
GROUP BY time(1m)
```
Use Case: Device detail page

**Pattern 2: Multiple Devices, Same Metric**
```flux
FROM mqtt_consumer
WHERE device_code =~ /sensor0[1-3]/
SELECT field(temperature) mean()
GROUP BY time(1m), device_code
```
Use Case: Compare multiple devices

**Pattern 3: Single Device, Multiple Metrics**
```flux
SELECT field(temperature) mean() AS temp,
       field(humidity) mean() AS humidity
FROM mqtt_consumer
WHERE device_code = 'sensor01'
GROUP BY time(1m)
```
Use Case: Correlation analysis (temp vs humidity)

**Pattern 4: Calculated Fields**
```flux
SELECT (field(battery) / 100) * 4.2 AS battery_voltage
FROM mqtt_consumer
WHERE device_code = 'sensor01'
```
Use Case: Derived metrics

### 3.3 Customization Options (10 min)

**Panel Options Deep Dive**:

**Graph Styles**:
- Line width: 1-5px (thicker for emphasis)
- Fill opacity: 0% (line only) to 100% (area chart)
- Point size: 0 (no points) to 10 (large dots)
- Line interpolation: Linear, Smooth, Step

**Axes**:
- **Left Y-axis**: Primary metric
- **Right Y-axis**: Secondary metric (different scale)
- **Soft min/max**: Dynamically adjust but respect hints
- **Decimals**: 0 (integers), 2 (precision)

**Legend**:
- Position: Bottom, Right, Hidden
- Mode: List, Table
- Values: Min, Max, Last, Avg

**Thresholds**:
- Base: Default color
- Add threshold: Click "+ Add threshold"
- Colors: Green, Yellow, Orange, Red, Custom
- Mode: Absolute vs Percentage

**Demo: Customize Temperature Graph**
```
1. Edit Temperature panel
2. Set:
   - Line width: 2
   - Fill opacity: 20%
   - Point size: 3
   - Y-axis: Soft min: 0, Soft max: 40
   - Unit: Celsius (°C)
   - Decimals: 1
   - Thresholds:
     < 10: Blue (Cold)
     10-25: Green (Normal)
     > 25: Red (Hot)
3. Apply → Save
```

### 3.4 Hands-On Lab 2: Build Your Own Panel (10 min)

**Challenge**: Create a Humidity Gauge

**Requirements**:
1. Data source: InfluxDB
2. Metric: Humidity
3. Visualization: Gauge
4. Query: Use your device_code
5. Aggregation: mean() over 1-minute intervals
6. Configuration:
   - Title: "Humidity Level"
   - Unit: Percent (0-100)
   - Thresholds:
     - 0-30%: Orange (Dry)
     - 30-60%: Green (Comfortable)
     - 60-100%: Blue (Humid)
7. Save to dashboard

**Bonus Tasks** (if time permits):
- Add a description to the panel
- Change the gauge display mode (e.g., LCD)
- Add a second query for a different device

**Expected Outcome**:
- Functional humidity gauge showing real-time data
- Understanding of query → visualization workflow

**Facilitator Notes**:
- Provide query template on screen
- Common mistakes: Forgetting GROUP BY, wrong field name
- Solution screenshot available for reference

---

## **Break (15 min)**

---

## Session 4: Data Lifecycle & Query Optimization (30 min)

### 4.1 Data Flow Architecture (10 min)

**Slide: Detailed Data Flow**
```
┌──────────┐  MQTT Publish (10s interval)
│  Device  │─────────────────────────────┐
└──────────┘                             │
                                         ▼
                              ┌──────────────────┐
                              │  MQTT Broker     │
                              │  (Mosquitto)     │
                              └────────┬─────────┘
                                       │ Subscribe
                              ┌────────▼─────────┐
                              │   Telegraf       │
                              │   (Collector)    │
                              └────────┬─────────┘
                                       │ Write
                              ┌────────▼─────────┐
                              │   InfluxDB       │
                              │  (Time-Series DB)│
                              └────────┬─────────┘
                                       │ Query
                              ┌────────▼─────────┐
                              │    Grafana       │
                              │ (Visualization)  │
                              └──────────────────┘
```

**Timeline**:
1. **T=0s**: Device measures temperature = 22.5°C
2. **T=10s**: Device publishes to MQTT topic `iot/sensor01/metrics`
3. **T=10.1s**: Telegraf receives message, parses JSON
4. **T=10.2s**: Telegraf writes to InfluxDB:
   ```
   measurement: mqtt_consumer
   tags: device_code=sensor01, topic=iot/sensor01/metrics
   fields: temperature=22.5, humidity=55.2, battery=87
   timestamp: 1713826810000000000 (nanoseconds)
   ```
5. **T=60s**: Grafana queries InfluxDB (1-minute refresh)
6. **T=60.1s**: Grafana displays data point on graph

**Key Metrics**:
- **Data Frequency**: 10 seconds (configurable per device)
- **Data Points per Day**: 8,640 per device per metric
- **Retention**: 30 days (259,200 data points per device per metric)

### 4.2 Retention & Downsampling (10 min)

**Slide: Data Retention Strategy**

**Current State**:
```
All data: 10-second resolution for 30 days
Storage: ~2.5MB per device per month (4 metrics)
Query load: High for long time ranges
```

**Problem**:
- Querying 6 months of 10s data = 15.5M data points
- Slow dashboard load times
- Most users don't need 10s resolution for historical data

**Ideal State** (Future Enhancement):
```
┌─────────────────────────────────────────────────────┐
│  0-7 days:    10s resolution (Full detail)          │
│  7-30 days:   1min resolution (Downsampled)         │
│  30-90 days:  10min resolution (Summary)            │
│  90+ days:    1hr resolution (Archive)              │
└─────────────────────────────────────────────────────┘
```

**Implementation** (InfluxDB Continuous Queries):
```sql
-- Create 1-minute downsampled data
CREATE CONTINUOUS QUERY "cq_1min"
ON "iotdash"
BEGIN
  SELECT mean(temperature) AS temperature,
         mean(humidity) AS humidity
  INTO "iotdash"."autogen_1min"."mqtt_consumer_1min"
  FROM "iotdash"."autogen"."mqtt_consumer"
  GROUP BY time(1m), device_code
END

-- Dashboard query uses appropriate resolution
SELECT mean(temperature)
FROM mqtt_consumer       -- 10s data (recent)
WHERE time > now() - 7d
UNION
SELECT mean(temperature)
FROM mqtt_consumer_1min  -- 1min data (older)
WHERE time BETWEEN now() - 30d AND now() - 7d
```

**Benefits**:
- 85% reduction in data points for 30-day queries
- Faster dashboard load times
- Lower InfluxDB memory usage

### 4.3 Query Optimization (10 min)

**Slide: Query Performance Best Practices**

**1. Use Appropriate Aggregation**

❌ **Bad**: Query all raw data
```sql
SELECT temperature FROM mqtt_consumer
WHERE time > now() - 30d
-- Result: 2.6M data points (slow!)
```

✅ **Good**: Aggregate to reasonable resolution
```sql
SELECT mean(temperature) FROM mqtt_consumer
WHERE time > now() - 30d
GROUP BY time(10m)
-- Result: 4,320 data points (fast!)
```

**2. Filter Early**

❌ **Bad**: Filter after aggregation
```sql
SELECT mean(temperature) FROM mqtt_consumer
GROUP BY time(1m), device_code
HAVING device_code = 'sensor01'
```

✅ **Good**: Filter in WHERE clause
```sql
SELECT mean(temperature) FROM mqtt_consumer
WHERE device_code = 'sensor01'
GROUP BY time(1m)
```

**3. Limit Time Range**

❌ **Bad**: Unbounded time range
```sql
SELECT * FROM mqtt_consumer
-- Queries entire database!
```

✅ **Good**: Use relative time ranges
```sql
SELECT temperature FROM mqtt_consumer
WHERE time > now() - 6h
```

**4. Use Variables for Flexibility**

```sql
-- Dashboard variable: $interval (auto-calculated)
SELECT mean(temperature) FROM mqtt_consumer
WHERE time > now() - $__range
GROUP BY time($__interval), device_code
```

Grafana automatically adjusts `$__interval`:
- 6h range → GROUP BY time(1m)
- 24h range → GROUP BY time(5m)
- 7d range → GROUP BY time(1h)

**Demo: Query Performance Comparison**

**Setup**: Create two identical panels, different queries

**Panel A (Slow)**:
```sql
SELECT temperature FROM mqtt_consumer
WHERE device_code = 'sensor01'
  AND time > now() - 7d
-- No GROUP BY → 60,480 raw data points
```

**Panel B (Fast)**:
```sql
SELECT mean(temperature) FROM mqtt_consumer
WHERE device_code = 'sensor01'
  AND time > now() - 7d
GROUP BY time(10m)
-- 1,008 aggregated data points
```

**Compare**:
- Query time (see panel footer)
- Number of series/data points
- Visual difference (should be minimal)

**Conclusion**: Aggregation significantly improves performance with negligible visual impact

---

## Session 5: Dashboard Provisioning & Automation (30 min)

### 5.1 Provisioning Architecture (10 min)

**Slide: How Dashboards Are Created**

**Manual Process** (Old Way):
1. Admin creates org in Grafana UI
2. Admin creates datasource in Grafana UI
3. Admin creates dashboard in Grafana UI
4. Admin adds panels one-by-one
5. **Repeat for every new organization** 😰

**Automated Process** (IoTDash Way):
1. Admin creates org in IoTDash UI
2. **Backend automatically**:
   - Creates Grafana org
   - Provisions InfluxDB datasource
   - Deploys dashboard from template
3. **Done in < 5 seconds** ✅

**Code Walkthrough** (High-Level):

```python
# backend/app/routers/admin_orgs.py

@router.post("/organisations")
def create_org(body: OrgCreate):
    # 1. Create DB record
    org = Organisation(name=body.name)
    db.add(org)

    # 2. Provision in Grafana
    grafana_org_id = grafana.create_org(body.name)
    grafana.add_datasource_to_org(grafana_org_id)

    # 3. Deploy dashboard template
    dashboard_json = load_template("iot-metrics.json")
    dashboard_uid = grafana.create_dashboard_in_org(
        grafana_org_id, dashboard_json
    )

    # 4. Save metadata
    org.grafana_org_id = grafana_org_id
    GrafanaDashboard(
        organisation_id=org.id,
        grafana_uid=dashboard_uid,
        ...
    )
    db.commit()
```

**Benefits**:
- **Consistency**: All orgs start with same dashboard
- **Speed**: 5 seconds vs 30 minutes manual setup
- **Scalability**: Can provision hundreds of orgs
- **Version Control**: Template is code, tracked in Git

### 5.2 Template Management (10 min)

**Slide: Dashboard Template**

**Template Location**: `grafana/provisioning/dashboards/iot-metrics.json`

**Structure**:
```json
{
  "title": "IoT Metrics",
  "tags": ["iot", "devices"],
  "timezone": "browser",
  "panels": [
    {
      "id": 1,
      "title": "Temperature",
      "type": "graph",
      "targets": [...]
    },
    {
      "id": 2,
      "title": "Humidity",
      "type": "graph",
      "targets": [...]
    }
  ],
  "time": {"from": "now-6h", "to": "now"},
  "refresh": "1m"
}
```

**Updating Template**:

**Method 1: Edit JSON** (Advanced)
```bash
vim grafana/provisioning/dashboards/iot-metrics.json
# Add new panel to "panels" array
# Assign unique panel ID
docker compose up -d --build backend
```

**Method 2: Export from Grafana** (Easier)
```
1. Create test org
2. Customize dashboard in Grafana UI
3. Export: Share → Export → Save to file
4. Clean up JSON (remove IDs, org references)
5. Replace iot-metrics.json
6. Rebuild backend container
```

**Demo: Template Update Process**

**Scenario**: Add "Pressure" panel to template

```
1. Login to test org's Grafana
2. Open IoT Metrics dashboard
3. Add new panel:
   - Title: Pressure
   - Query: field(pressure) mean()
   - Visualization: Graph
   - Unit: hPa
4. Save dashboard
5. Export dashboard JSON
6. Compare with current template:
   diff current-template.json exported-dashboard.json
7. Copy new panel definition
8. Update iot-metrics.json
9. Rebuild: docker compose up -d --build backend
10. Create new test org → Verify pressure panel exists
```

**Important Notes**:
- ⚠️ **Template changes only affect NEW organizations**
- Existing orgs keep their current dashboards
- To update existing orgs, need migration script (see Provisioning Guide)

### 5.3 Challenges & Solutions (10 min)

**Challenge 1: Updating Existing Dashboards**

**Problem**:
- Template updated with new "CO2" panel
- 20 existing organizations don't have CO2 panel
- Manual update = 20 dashboards × 10 minutes = 200 minutes

**Current Solution**: Manual update (not scalable)

**Proposed Solution**: Dashboard Migration API
```python
# tools/migrate_dashboards.py

def migrate_to_v2():
    """Add CO2 panel to all org dashboards"""
    for org in Organisation.query.all():
        dashboard = grafana.get_dashboard(org.dashboard_uid)

        # Add CO2 panel
        co2_panel = load_panel_config("co2-panel.json")
        dashboard["panels"].append(co2_panel)

        # Update version
        dashboard["version"] += 1

        # Save
        grafana.update_dashboard(dashboard)
        print(f"Updated {org.name} dashboard to v2")
```

**Challenge 2: Dashboard Versioning**

**Problem**:
- No way to track which orgs have which template version
- Can't rollback if update causes issues
- Difficult to know who needs updates

**Proposed Solution**: Version Metadata
```python
# models.py
class GrafanaDashboard(Base):
    # ... existing fields
    template_version = Column(Integer, default=1)
    last_migrated = Column(DateTime)

# Query orgs needing update
outdated_orgs = (
    db.query(Organisation)
    .join(GrafanaDashboard)
    .filter(GrafanaDashboard.template_version < 2)
    .all()
)
```

**Challenge 3: User Customizations**

**Problem**:
- User adds custom panel to their dashboard
- Template update overwrites custom panel
- User customizations lost

**Solution**: Smart Merging
```python
def merge_dashboards(current_dashboard, template_update):
    """
    Merge template updates while preserving user customizations
    """
    # Identify user-added panels (panel IDs not in template)
    template_panel_ids = {p["id"] for p in template_update["panels"]}
    user_panels = [
        p for p in current_dashboard["panels"]
        if p["id"] not in template_panel_ids
    ]

    # Combine: template panels + user panels
    merged_dashboard = template_update.copy()
    merged_dashboard["panels"].extend(user_panels)

    return merged_dashboard
```

**Challenge 4: Testing Templates**

**Problem**:
- Deploy broken template → all new orgs broken
- No validation before deployment

**Solution**: CI/CD Validation
```yaml
# .github/workflows/validate-templates.yml
name: Validate Dashboard Templates
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate JSON Syntax
        run: |
          jq . grafana/provisioning/dashboards/iot-metrics.json
      - name: Check Required Fields
        run: |
          python tools/validate_dashboard.py
      - name: Test Deployment
        run: |
          docker compose up -d
          python tools/test_dashboard_provision.py
```

**Slide: Improvements Roadmap**

**Short-Term** (1-3 months):
- [ ] Dashboard versioning system
- [ ] Migration scripts for v1 → v2
- [ ] Backup/restore functionality

**Medium-Term** (3-6 months):
- [ ] Dashboard update API
- [ ] Multi-template support (e.g., environmental, power)
- [ ] CI/CD validation pipeline

**Long-Term** (6+ months):
- [ ] Visual template editor
- [ ] Dashboard marketplace (community templates)
- [ ] AI-suggested panels based on device metrics

---

## Session 6: Q&A & Best Practices (15 min)

### 6.1 Common Questions

**Q: How do I add a panel for a new metric?**

A:
1. Verify metric is being sent by device (check MQTT/Telegraf logs)
2. Enable metric in IoTDash admin panel (Devices → Manage Metrics)
3. In Grafana, add panel and select new metric field
4. Configure visualization and save

**Q: Dashboard is slow to load. How to fix?**

A:
1. Reduce time range (30d → 7d → 24h)
2. Increase aggregation interval (10s → 1m → 10m)
3. Limit number of panels (< 12 recommended)
4. Use query caching (Grafana enterprise feature)

**Q: Can I share a dashboard with another org?**

A: Not directly. Options:
1. Export dashboard JSON and import into other org (manual)
2. Update template and provision for both orgs (automated)
3. Use Grafana Folders and cross-org permissions (complex)

**Q: How to backup dashboards?**

A:
1. **Manual**: Export JSON via Grafana UI (Share → Export)
2. **Automated**: Use Grafana API + cron job
3. **Database**: Backup Grafana SQLite/Postgres database

### 6.2 Best Practices Summary

**Dashboard Design**:
- ✅ Use descriptive panel titles and descriptions
- ✅ Set appropriate Y-axis ranges and units
- ✅ Group related panels with rows
- ✅ Limit to 12 panels per dashboard
- ❌ Don't hardcode device IDs (use variables)
- ❌ Don't mix unrelated metrics on one dashboard

**Query Optimization**:
- ✅ Use aggregation (mean, max, min)
- ✅ Filter early with WHERE clauses
- ✅ Limit time ranges (relative, not absolute)
- ✅ Use appropriate GROUP BY intervals
- ❌ Don't query raw data for > 24h
- ❌ Don't use `SELECT *`

**Maintenance**:
- ✅ Version dashboards (add version in title/description)
- ✅ Document custom changes (save notes)
- ✅ Test queries in Explore before adding to production
- ✅ Regularly review performance (Query Inspector)
- ❌ Don't edit live dashboards (duplicate first)
- ❌ Don't delete old template versions

**Provisioning**:
- ✅ Test templates in isolated org before production
- ✅ Keep templates in version control (Git)
- ✅ Document template changes in CHANGELOG
- ✅ Backup production before major updates
- ❌ Don't deploy untested templates
- ❌ Don't update templates without version bump

### 6.3 Additional Resources

**Documentation**:
- IoTDash Grafana User Guide: `docs/grafana/USER_GUIDE.md`
- Provisioning Guide: `docs/grafana/PROVISIONING_GUIDE.md`
- Grafana Official Docs: https://grafana.com/docs/

**Community**:
- Grafana Community Forums: https://community.grafana.com/
- InfluxDB Community: https://community.influxdata.com/
- IoTDash GitHub Issues: [Your repo URL]

**Tools**:
- Grafana Explore Tab: Test queries interactively
- Query Inspector: Debug slow queries
- Dashboard JSON: Version control dashboards

### 6.4 Hands-On Challenge (Optional, if time)

**Build a Complete Dashboard from Scratch**

**Scenario**: Create "Device Health" dashboard

**Requirements**:
1. Create new dashboard (not from template)
2. Add 4 panels:
   - **Battery Gauge**: 0-100%, thresholds at 20%/50%
   - **Signal Strength Stat**: Last value, unit: dBm
   - **Uptime Graph**: Device uptime over 24h
   - **Alert Count Table**: Show alert history
3. Add dashboard variable for device selection
4. Set dashboard time range to last 24h
5. Enable auto-refresh (1m)
6. Save and export dashboard JSON

**Time**: 15 minutes

**Facilitator**: Provide solution JSON for comparison

---

## Post-Workshop

### Follow-Up Materials

**Email Participants**:
- Workshop slides (PDF)
- Lab solution files
- Additional resources links
- Survey link (feedback)

**Survey Questions**:
1. How would you rate the workshop overall? (1-5)
2. Which session was most valuable?
3. What topics need more coverage?
4. Confidence level before/after workshop
5. What would you like to see in a follow-up workshop?

### Next Steps for Participants

**Immediate** (This Week):
- [ ] Create one custom panel in your dashboard
- [ ] Optimize a slow-loading panel
- [ ] Export your dashboard as backup

**Short-Term** (This Month):
- [ ] Build a custom dashboard for specific use case
- [ ] Set up dashboard variables for device selection
- [ ] Explore Grafana alerting (if not using IoTDash alerts)

**Long-Term** (This Quarter):
- [ ] Propose dashboard template improvements
- [ ] Contribute to dashboard template library
- [ ] Train team members on Grafana

### Facilitator Notes

**Preparation Checklist**:
- [ ] Provision test IoTDash instance
- [ ] Create test organization with sample data
- [ ] Verify all participants have accounts
- [ ] Prepare slides and lab materials
- [ ] Test demo scenarios in advance
- [ ] Have backup slides if internet fails

**Materials Needed**:
- [ ] Laptop + projector
- [ ] Workshop slides (PDF/PPT)
- [ ] Lab handouts (printed or digital)
- [ ] Access credentials for participants
- [ ] Whiteboard/flipchart for discussions

**Contingency Plans**:
- Internet down? Use local Grafana instance
- Tool not working? Have screenshots/videos ready
- Participant questions? Park in "parking lot" for end

---

## Appendix: Additional Lab Exercises

### Lab A: Advanced Query - Correlation Analysis

**Goal**: Create a panel showing temperature vs humidity correlation

**Steps**:
1. Create new panel
2. Add two queries:
   ```
   Query A (Temperature):
   SELECT mean(temperature) FROM mqtt_consumer
   WHERE device_code = '$device'
   GROUP BY time(5m)

   Query B (Humidity):
   SELECT mean(humidity) FROM mqtt_consumer
   WHERE device_code = '$device'
   GROUP BY time(5m)
   ```
3. Visualization: Graph with dual Y-axes
4. Left Y-axis: Temperature (°C)
5. Right Y-axis: Humidity (%)

### Lab B: Creating Dashboard Variables

**Goal**: Add device selector to dashboard

**Steps**:
1. Dashboard Settings → Variables → Add variable
2. Configure:
   - Name: `device`
   - Type: Query
   - Data Source: InfluxDB
   - Query: `SHOW TAG VALUES WITH KEY = "device_code"`
3. Save variable
4. Update all panel queries to use `$device`
5. Test dropdown selector at top of dashboard

### Lab C: Setting Up Alerts (Grafana Native)

**Goal**: Create alert if temperature > 30°C

**Steps**:
1. Edit Temperature panel
2. Alert tab → Create Alert
3. Conditions:
   - WHEN: avg() OF query(A, 5m, now)
   - IS ABOVE: 30
4. Configure notifications (email, Slack, etc.)
5. Test alert (manually set threshold low to trigger)

---

**Workshop Version**: 1.0
**Last Updated**: April 2026
**Next Review**: July 2026
**Facilitator**: [Your Name]
**Contact**: [Your Email]

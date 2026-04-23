# Grafana User Guide for IoTDash

## Table of Contents
1. [Introduction](#introduction)
2. [Accessing Grafana Dashboards](#accessing-grafana-dashboards)
3. [Understanding Your Dashboard](#understanding-your-dashboard)
4. [Adding New Panels (Graphs)](#adding-new-panels-graphs)
5. [Customizing Existing Panels](#customizing-existing-panels)
6. [Data Lifecycle & Retention](#data-lifecycle--retention)
7. [Managing Growing Data & Metrics](#managing-growing-data--metrics)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Introduction

Grafana is an open-source analytics and monitoring platform integrated into IoTDash. It allows you to:
- Visualize device metrics in real-time
- Create custom dashboards with multiple graphs
- Set up alerts on metric thresholds
- Analyze historical data trends

Each organization in IoTDash has its own dedicated Grafana organization with isolated dashboards and data.

---

## Accessing Grafana Dashboards

### From IoTDash

1. **Login** to IoTDash at your deployment URL
2. **Navigate** to Dashboard → Devices tab
3. **Click** on any device card to view its detail page
4. **View** embedded Grafana panels showing live metrics (temperature, humidity, etc.)

### Direct Grafana Access

You can also access Grafana directly:

1. Navigate to `https://your-domain.com/grafana/` (note the trailing slash)
2. Login with your IoTDash credentials (SSO enabled)
3. You'll see your organization's dashboards

> **Note**: IoTDash automatically provisions a default "IoT Metrics" dashboard for each organization.

---

## Understanding Your Dashboard

### Dashboard Structure

Your default IoT Metrics dashboard consists of:

**Time Range Selector** (top right)
- Last 6 hours (default)
- Last 24 hours
- Last 7 days
- Custom range

**Refresh Interval** (top right)
- Auto-refresh every 1m, 5m, 30m, etc.
- Manual refresh button

**Panels (Graphs)**
- Temperature Over Time
- Humidity Over Time
- Pressure Over Time
- Battery Level Over Time
- Custom metrics (if configured)

### Panel Types

1. **Time Series** - Line graphs showing metrics over time
2. **Gauge** - Current value with min/max ranges
3. **Stat** - Single value display (latest reading)
4. **Table** - Tabular data view

---

## Adding New Panels (Graphs)

### Step 1: Enter Edit Mode

1. Open your dashboard in Grafana
2. Click **Add panel** button (top right)
3. Select **Add a new panel**

### Step 2: Configure Data Source

1. **Data Source**: InfluxDB (pre-configured for your org)
2. **FROM**: Select your measurement
   - `mqtt_consumer` (default for device metrics)
3. **WHERE**: Filter by device
   ```
   device_code = 'your-device-uid'
   ```

### Step 3: Select Metric

In the **SELECT** section:
1. Choose the field (metric) to visualize:
   - `temperature`
   - `humidity`
   - `pressure`
   - `battery`
   - Any custom metrics enabled for your devices

2. Add aggregation (optional):
   - `mean()` - Average value
   - `max()` - Maximum value
   - `min()` - Minimum value
   - `last()` - Most recent value

### Step 4: Customize Visualization

**Panel Options**:
- **Title**: Give your panel a descriptive name
- **Description**: Add context for other users

**Graph Styles**:
- **Line width**: 1-10px
- **Fill opacity**: 0-100%
- **Point size**: Show data points

**Axes**:
- **Unit**: Choose appropriate unit (°C, %, hPa, etc.)
- **Y-axis min/max**: Set scale limits
- **Legend**: Show/hide, position

**Thresholds**:
- Add color-coded thresholds (e.g., red if temp > 30°C)

### Step 5: Save Panel

1. Click **Apply** (top right)
2. Click **Save dashboard** (disk icon)
3. Add a note describing your changes
4. Click **Save**

### Example: Adding a New Temperature Gauge

```
Query:
FROM: mqtt_consumer
WHERE: device_code = 'sensor01'
SELECT: field(temperature) mean()
GROUP BY: time(1m)

Visualization: Gauge
Unit: Celsius (°C)
Min: 0
Max: 50
Thresholds:
  - 0-20: Blue (Cold)
  - 20-25: Green (Normal)
  - 25-30: Yellow (Warm)
  - 30+: Red (Hot)
```

---

## Customizing Existing Panels

### Edit a Panel

1. **Hover** over the panel you want to edit
2. Click the **panel title dropdown**
3. Select **Edit**
4. Make your changes
5. Click **Apply** then **Save dashboard**

### Common Customizations

**Change Time Range** (for specific panel):
- Edit panel → Query options → Time range
- Override dashboard time range

**Add Multiple Queries**:
- Click **+ Query** to add another data series
- Useful for comparing multiple devices or metrics

**Change Visualization Type**:
- Edit panel → Visualization dropdown
- Switch between Graph, Gauge, Stat, Table, etc.

**Add Transformations**:
- Edit panel → Transform tab
- Merge series, calculate differences, rename fields

---

## Data Lifecycle & Retention

### How Data Flows

1. **Device** → Sends data via MQTT to Telegraf
2. **Telegraf** → Writes to InfluxDB (time-series database)
3. **InfluxDB** → Stores metrics with timestamps
4. **Grafana** → Queries InfluxDB and visualizes data

### Data Retention Policy

**Default Retention**: 30 days
- Data older than 30 days is automatically deleted
- Configurable in InfluxDB settings

**High-Frequency Data**: 10-second intervals
- Devices send data every 10 seconds by default
- Results in ~8,640 data points per device per day

### Downsampling (Future Enhancement)

For long-term storage without overwhelming the database:
- Keep 10s resolution for last 7 days
- Downsample to 1min resolution for 8-30 days
- Downsample to 1hr resolution for 30-90 days
- (Not currently implemented)

---

## Managing Growing Data & Metrics

### When You Start Receiving More Metrics

As your deployment grows, you may add:
- More devices
- New metric types (e.g., CO2, light level, motion)
- Higher frequency data

### Dashboard Organization Strategies

**1. Multi-Device Dashboards**

Use template variables to switch between devices:
1. Dashboard settings → Variables
2. Add variable:
   ```
   Name: device
   Type: Query
   Query: SHOW TAG VALUES WITH KEY = "device_code"
   ```
3. Use `$device` in panel queries

**2. Metric-Specific Dashboards**

Create separate dashboards for:
- Environmental metrics (temp, humidity)
- Power metrics (battery, voltage)
- System metrics (uptime, signal strength)

**3. Row Grouping**

Organize panels into collapsible rows:
1. Add → Row
2. Drag panels into the row
3. Click row title to collapse/expand

### Query Optimization Tips

**Use Aggregation**:
```
SELECT mean("temperature") FROM "mqtt_consumer"
WHERE time > now() - 6h
GROUP BY time(1m)
```
Instead of raw 10s data, aggregate to 1-minute averages.

**Limit Time Range**:
- Avoid querying months of data
- Use relative time ranges (last 6h, last 24h)

**Filter Early**:
```
WHERE device_code = 'sensor01' AND time > now() - 6h
```
Filter by device before aggregating.

### Performance Monitoring

**Signs of Performance Issues**:
- Panels loading slowly (> 3 seconds)
- Timeout errors
- Missing data points

**Solutions**:
1. Reduce time range
2. Increase aggregation interval (10s → 1m)
3. Limit number of series per panel (< 10)
4. Use continuous queries in InfluxDB

---

## Best Practices

### Dashboard Design

✅ **DO**:
- Use descriptive panel titles
- Add units to all metrics
- Set appropriate Y-axis ranges
- Group related metrics together
- Add panel descriptions for complex queries

❌ **DON'T**:
- Overload dashboards with > 20 panels
- Use default auto-scaling without limits
- Mix unrelated metrics on one dashboard
- Forget to save after changes

### Query Best Practices

✅ **DO**:
- Use appropriate aggregation (mean, max, min)
- Filter by device_code early in query
- Use time-based grouping (`GROUP BY time(1m)`)
- Test queries before adding to production

❌ **DON'T**:
- Query raw data for > 24 hours
- Use `SELECT *` (select specific fields)
- Forget WHERE clauses (filters)

### Collaboration

- **Save versions**: Add notes when saving dashboards
- **Star important dashboards**: Makes them easy to find
- **Export/Import**: Share dashboard JSON with team
- **Avoid editing live dashboards**: Duplicate first, then edit

---

## Troubleshooting

### Panel Shows "No Data"

**Check**:
1. Time range - is data recent enough?
2. Device filter - is device_code correct?
3. Metric name - is field name spelled correctly?
4. InfluxDB - is data being written? (Check Explore tab)

**Debug Query**:
1. Edit panel → Query Inspector
2. View raw query sent to InfluxDB
3. Copy query and test in Explore tab

### Panel Shows Incorrect Data

**Verify**:
1. **Aggregation**: Using mean() vs last() vs max()
2. **Group By**: Time interval (1m, 5m, etc.)
3. **Filters**: WHERE clauses applied correctly

### Dashboard Won't Save

**Possible Causes**:
1. **Permissions**: You may not have edit rights
2. **Timeout**: Large dashboard, try simplifying
3. **Conflicts**: Someone else edited simultaneously

**Solution**:
- Export dashboard JSON as backup
- Contact admin if permission issue persists

### Slow Dashboard Performance

**Optimize**:
1. Reduce number of panels (< 12 recommended)
2. Shorten time range (6h instead of 30d)
3. Increase aggregation interval (10s → 1m → 5m)
4. Remove duplicate queries

### Missing Metrics After Device Update

**When new metrics are added**:
1. Verify device is sending new metric (check MQTT logs)
2. Confirm metric is enabled in IoTDash admin panel
3. Wait up to 1 minute for Telegraf to pick up changes
4. Refresh Grafana data source (Settings → Data Sources → InfluxDB → Save & Test)

---

## Advanced Topics

### Using Variables

Create dynamic dashboards that adapt to user selection:

**Example: Device Selector**
```
Name: device
Type: Query
Query: SHOW TAG VALUES WITH KEY = "device_code"
Refresh: On time range change
```

Use in panel:
```
WHERE device_code = '$device'
```

### Templating

Create dashboard templates for:
- New device types
- Regional deployments
- Customer-specific views

### Annotations

Mark events on graphs:
- Device maintenance windows
- Alert events
- Configuration changes

**Add Annotation**:
1. Dashboard settings → Annotations
2. Add annotation query
3. Choose event source (InfluxDB, API)

### Alerting (Advanced)

While IoTDash handles alerting, you can also use Grafana's alerting:
1. Edit panel → Alert tab
2. Create alert rule
3. Set conditions (threshold, time window)
4. Configure notification channels

---

## Getting Help

**Resources**:
- IoTDash Admin Panel - Manage devices and metrics
- Grafana Documentation - https://grafana.com/docs/
- InfluxDB Query Language - https://docs.influxdata.com/influxdb/

**Support**:
- Contact your system administrator
- Check IoTDash logs for errors
- Grafana Explore tab - Test queries interactively

---

**Last Updated**: April 2026
**Version**: 1.0
**For IoTDash**: v0.1.0+

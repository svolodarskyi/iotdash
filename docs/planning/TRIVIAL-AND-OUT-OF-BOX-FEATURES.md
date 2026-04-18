# IoTDash — Trivial & Out-of-the-Box Features

> **Purpose:** Features that are dead simple to implement but look impressive to clients. Low effort, high perceived value. Each is tagged **TRIVIAL** (hours to build) or **OUT-OF-BOX** (creative/unexpected but still easy).

---

## 1. Device Health & Connectivity

### 1.1 Device Online/Offline Status — TRIVIAL

**What:** Green dot = online, red dot = offline. Last seen timestamp.

**Why clients love it:** First thing they look at. "Is my thing working?"

**How it works:**
```
Step 1: Device publishes every N seconds (you already have this)
Step 2: Backend tracks last_seen_at per device
Step 3: If now - last_seen_at > 2 × publish_interval → offline
Step 4: Show green/red dot on device list
```

**Implementation:** One DB column (`last_seen_at`), one comparison. Update on every MQTT message via Telegraf → webhook or a simple consumer.

**Bonus — MQTT Last Will and Testament:**
```
Device connects with LWT:
  topic: {device_id}/from/status
  payload: {"status": "offline"}
  retain: true

EMQX auto-publishes this when device disconnects unexpectedly.
Your backend picks it up → instant offline detection. Zero polling.
```

**Effort:** 2-4 hours.

---

### 1.2 Uptime Percentage — TRIVIAL

**What:** "Device was online 99.2% of the last 30 days."

**Why clients love it:** SLA tracking. They can report to their management.

**How it works:**
```
Step 1: Log state changes (online/offline) with timestamps
Step 2: Sum online time / total time × 100
Step 3: Display as a single number on device detail page
```

**Implementation:** One SQL query over a `device_status_log` table. Or calculate from InfluxDB message gaps.

**Effort:** 2-3 hours.

---

### 1.3 Connection Quality Indicator — TRIVIAL

**What:** Show message delivery rate. "48 of 50 expected messages received in the last hour (96%)."

**Why clients love it:** They can tell if their network/SIM card/WiFi is flaky before a full outage.

**How it works:**
```
Step 1: Device is expected to send every 30 seconds → 120 messages/hour
Step 2: Count actual messages received in last hour
Step 3: Delivery rate = actual / expected × 100%
Step 4: Show as percentage + color (green >95%, yellow >80%, red <80%)
```

**Implementation:** One InfluxDB/TimescaleDB count query.

**Effort:** 1-2 hours.

---

## 2. Dashboards & Visualization

### 2.1 Daily/Weekly Email Digest — OUT-OF-BOX

**What:** Client receives a daily or weekly email: "Your 5 devices summary — all healthy, sensor03 had 2 alerts this week, average temperature was 22.3C."

**Why clients love it:** They don't need to log in to know everything's fine. Peace of mind in their inbox.

**How it works:**
```
Step 1: Cron job runs at 8am (or weekly on Monday)
Step 2: Query per org:
        - Device count, online/offline counts
        - Alert count (fired, resolved)
        - Key metric averages (temperature, humidity, etc.)
Step 3: Render HTML email template
Step 4: Send via SendGrid/SMTP
```

**Implementation:** One Python script, one HTML template, one cron schedule.

**Effort:** 4-6 hours.

---

### 2.2 "Last Reading" Card — TRIVIAL

**What:** Big number showing the most recent value for each metric. "Temperature: 22.5C (2 seconds ago)."

**Why clients love it:** Immediate answer to "what's happening RIGHT NOW?" without reading a graph.

**How it works:**
```
Step 1: Query last data point per device per metric
Step 2: Display as a large number with unit + relative timestamp
Step 3: Color-code: green (normal), yellow (warning), red (critical)
```

**Implementation:** One Grafana Stat panel (already supported) or one API endpoint returning `SELECT last(value) FROM measurements WHERE device_id = $1`.

**Effort:** 30 minutes per device type in Grafana. 2 hours if building custom in React.

---

### 2.3 Mini Sparkline on Device List — OUT-OF-BOX

**What:** Tiny inline chart (last 24 hours) next to each device in the list view. No click needed — see the trend at a glance.

**Why clients love it:** One page shows all devices with their trends. Instant overview without clicking into each.

**How it works:**
```
Step 1: API returns last 24 values (hourly averages) per device
Step 2: Render as tiny SVG line (50x20px) inline in the table row
```

**Implementation:** React: a small `<svg>` with a `<polyline>`. Data: one InfluxDB query with `aggregateWindow(every: 1h, fn: mean)`.

**Effort:** 3-4 hours.

---

### 2.4 Device Map View — OUT-OF-BOX

**What:** Show devices on a map. Pins colored by status (green/yellow/red).

**Why clients love it:** Especially for clients with devices across multiple locations (warehouses, buildings, fields).

**How it works:**
```
Step 1: Add lat/lng fields to device registration
Step 2: Use Leaflet.js (free, open-source maps) or Grafana Geomap panel
Step 3: Plot pins, color by latest status
Step 4: Click pin → see device detail
```

**Implementation:** `react-leaflet` + OpenStreetMap tiles (free). No API key needed.

**Effort:** 4-6 hours.

---

### 2.5 Dark Mode — TRIVIAL

**What:** Toggle dark/light theme.

**Why clients love it:** Control rooms and NOCs (Network Operations Centers) are always dark. Bright white dashboards hurt eyes.

**How it works:**
```
Step 1: Tailwind CSS: add `dark:` variants to components
Step 2: Zustand store: { theme: 'light' | 'dark' }
Step 3: Toggle button in header
Step 4: Apply `class="dark"` on <html> element
```

**Implementation:** Tailwind has built-in dark mode support. One store value, one class toggle.

**Effort:** 2-3 hours (if you use Tailwind dark: prefixes from the start).

---

## 3. Alerts & Notifications

### 3.1 "All Quiet" Confirmation — OUT-OF-BOX

**What:** When everything is normal, explicitly show "All systems operational" with a green banner. Not just absence of alerts — a positive confirmation.

**Why clients love it:** Silence is ambiguous. "No alerts" could mean "everything's fine" or "alerting is broken." Explicit confirmation removes doubt.

**How it works:**
```
Step 1: Query: any active alerts for this org? Any devices offline?
Step 2: If all clear → show green banner: "✓ All 5 devices operational. No active alerts."
Step 3: If issues → show yellow/red banner with count
```

**Implementation:** One query, one conditional banner.

**Effort:** 1 hour.

---

### 3.2 Alert History Timeline — TRIVIAL

**What:** Chronological list of all past alerts: when they fired, when they resolved, how long they lasted.

**Why clients love it:** Compliance, auditing, pattern recognition. "We've had 12 temperature alerts this month, all between 2-4 PM."

**How it works:**
```
Step 1: Log every alert state change (firing, resolved) with timestamp
Step 2: Display as timeline/table: alert name, fired at, resolved at, duration
Step 3: Filter by device, date range, status
```

**Implementation:** One DB table (`alert_history`), one list page.

**Effort:** 3-4 hours.

---

### 3.3 Maintenance Window / Snooze — TRIVIAL

**What:** "Mute alerts for device X for the next 2 hours" (during planned maintenance).

**Why clients love it:** They do maintenance. They don't want 50 false alerts while a machine is deliberately powered off.

**How it works:**
```
Step 1: User clicks "Snooze" on a device, picks duration (1h, 2h, 4h, custom)
Step 2: Backend sets snooze_until on the device record
Step 3: Alert evaluation checks: if now < snooze_until → suppress
Step 4: Auto-resume after snooze expires
```

**Implementation:** One datetime column, one check in alert logic.

**Effort:** 2-3 hours.

---

### 3.4 Alert Escalation (Simple) — TRIVIAL

**What:** "If alert is not acknowledged within 30 minutes, send to a second email."

**Why clients love it:** The night shift operator might miss it. Their supervisor should know.

**How it works:**
```
Step 1: Alert fires → send to primary contact
Step 2: Start 30-minute timer
Step 3: If not acknowledged (no one clicked "Acknowledge" in web app) → send to secondary contact
Step 4: Optional: third level after 60 minutes
```

**Implementation:** A scheduled job that checks unacknowledged alerts older than N minutes.

**Effort:** 3-4 hours.

---

### 3.5 Alert Acknowledge Button — TRIVIAL

**What:** Button in the web app: "I see this alert, I'm handling it." Stops escalation, logs who acknowledged.

**Why clients love it:** Accountability. Management can see "alert was acknowledged by John at 14:32."

**How it works:**
```
Step 1: Alert fires → status = "firing"
Step 2: User clicks "Acknowledge" → status = "acknowledged", acknowledged_by = user_id
Step 3: Alert resolves → status = "resolved"
Step 4: Timeline shows: fired → acknowledged by John (12 min) → resolved (45 min)
```

**Implementation:** One status field, one button, one API endpoint.

**Effort:** 2 hours.

---

## 4. Data & Reporting

### 4.1 CSV Export — TRIVIAL

**What:** "Download last 30 days of data for this device as CSV."

**Why clients love it:** They want to put it in Excel. Always. Every client. No exceptions.

**How it works:**
```
Step 1: User clicks "Export" on device page
Step 2: Backend queries time-series data for date range
Step 3: Stream as CSV with headers: timestamp, temperature, humidity, ...
Step 4: Browser downloads file
```

**Implementation:** One API endpoint that returns `Content-Type: text/csv`.

**Effort:** 2-3 hours.

---

### 4.2 Min/Max/Avg Summary Cards — TRIVIAL

**What:** Show min, max, average for each metric over a selectable period (today, this week, this month).

**Why clients love it:** Quick glance: "This week the temperature ranged from 18.2C to 26.8C, averaging 22.1C."

**How it works:**
```
Step 1: Query: SELECT MIN(value), MAX(value), AVG(value)
        FROM measurements WHERE device_id = $1 AND time > $2
Step 2: Display as 3 cards: Min | Avg | Max
Step 3: Period selector: Today / 7 days / 30 days / custom
```

**Implementation:** One aggregation query, three number cards.

**Effort:** 1-2 hours.

---

### 4.3 Comparison View — OUT-OF-BOX

**What:** Overlay two devices (or two time periods) on the same chart. "Compare freezer A vs freezer B." Or "Compare this week vs last week."

**Why clients love it:** Spot differences between devices. See if a fix improved things.

**How it works:**
```
Device comparison:
  Step 1: User selects two devices
  Step 2: Query both time-series
  Step 3: Render on same chart with different colors + legend

Time comparison:
  Step 1: User selects device + two date ranges
  Step 2: Query both, align timestamps (offset second range)
  Step 3: Render overlaid
```

**Implementation:** Grafana can do this natively with variables. In custom React: two datasets on one chart (Recharts/Chart.js).

**Effort:** 4-6 hours.

---

### 4.4 Scheduled PDF Reports — OUT-OF-BOX

**What:** Auto-generate a PDF report weekly/monthly and email it. Includes charts, summaries, alert history.

**Why clients love it:** They forward it to their boss. Management loves PDF reports.

**How it works:**
```
Step 1: Cron job (weekly/monthly)
Step 2: Grafana Reporting (Enterprise) OR custom:
        - Query data: summaries, alert counts, min/max/avg
        - Generate charts as images (matplotlib or chart screenshot)
        - Build PDF (WeasyPrint, ReportLab, or Puppeteer screenshot)
Step 3: Email PDF as attachment
```

**Implementation:** Simplest: screenshot Grafana dashboards with Puppeteer + stitch into PDF. More polished: custom template with WeasyPrint.

**Effort:** 6-8 hours (basic), 2-3 days (polished).

---

## 5. Device Management

### 5.1 Device Naming / Labels — TRIVIAL

**What:** Client gives human-readable names to devices. "Warehouse B - Cold Room 3" instead of "sensor_0a4f2c".

**Why clients love it:** They don't think in device IDs. They think in locations and equipment names.

**How it works:**
```
Step 1: Add display_name field to devices table (nullable, falls back to device_code)
Step 2: Editable in web app — click device name to rename
Step 3: Show display_name everywhere in UI, keep device_code for MQTT
```

**Implementation:** One column, one input field.

**Effort:** 1 hour.

---

### 5.2 Device Groups / Tags — TRIVIAL

**What:** Tag devices: "Floor 2", "Cold Storage", "Critical". Filter dashboard by tag.

**Why clients love it:** 100 devices is unmanageable as a flat list. Groups make it usable.

**How it works:**
```
Step 1: Many-to-many: devices ↔ tags table
Step 2: Admin assigns tags to devices
Step 3: Dashboard: filter dropdown with tags
Step 4: "Show me all 'Cold Storage' devices"
```

**Implementation:** One junction table, one filter dropdown.

**Effort:** 3-4 hours.

---

### 5.3 Device Notes / Log — OUT-OF-BOX

**What:** Free-text notes attached to a device. "2026-04-10: Replaced sensor probe. Old one had corrosion."

**Why clients love it:** Maintenance log. When someone investigates an anomaly, they can see what was done before.

**How it works:**
```
Step 1: device_notes table: device_id, user_id, created_at, text
Step 2: Text area on device detail page
Step 3: Chronological list of all notes
```

**Implementation:** One table, one form, one list.

**Effort:** 2-3 hours.

---

### 5.4 QR Code for Device — OUT-OF-BOX

**What:** Generate a QR code for each device. Print and stick on physical equipment. Scan → opens device dashboard on phone.

**Why clients love it:** Technician walks up to a machine, scans QR code, instantly sees its data and history. No searching.

**How it works:**
```
Step 1: Generate QR code containing URL: https://app.yourdomain.com/devices/{id}
Step 2: Show on device detail page with "Print" button
Step 3: Tech scans with phone camera → opens dashboard
```

**Implementation:** `qrcode` Python library (backend generates PNG) or `qrcode.react` npm package (frontend generates SVG).

**Effort:** 1-2 hours.

---

## 6. User Experience

### 6.1 Notification Bell + Badge — TRIVIAL

**What:** Bell icon in header with count of unacknowledged alerts. Click → dropdown list of recent alerts.

**Why clients love it:** They see at a glance "3 things need attention" without navigating to the alerts page.

**How it works:**
```
Step 1: Query unacknowledged alerts for user's org
Step 2: Show count as badge on bell icon
Step 3: Click → dropdown with last 10 alerts
Step 4: Click alert → navigate to alert detail
Step 5: Poll every 30 seconds (or WebSocket for real-time)
```

**Implementation:** One API endpoint, one dropdown component, TanStack Query with `refetchInterval: 30000`.

**Effort:** 3-4 hours.

---

### 6.2 Dashboard Auto-Refresh Indicator — TRIVIAL

**What:** Small text: "Last updated: 5 seconds ago" with a countdown to next refresh.

**Why clients love it:** Removes uncertainty. "Is this live data or cached from 3 hours ago?"

**How it works:**
```
Step 1: Track when data was last fetched (TanStack Query gives you this)
Step 2: Display relative time: "5s ago", "1m ago"
Step 3: Show next refresh countdown if using polling
```

**Implementation:** `dataUpdatedAt` from TanStack Query + `date-fns` `formatDistanceToNow`.

**Effort:** 30 minutes.

---

### 6.3 Quick Date Range Picker — TRIVIAL

**What:** Buttons: "Last hour | 24h | 7 days | 30 days | Custom" above charts.

**Why clients love it:** They need to zoom in/out of time ranges constantly. One click instead of a date picker.

**How it works:**
```
Step 1: Preset buttons that set start/end timestamps
Step 2: Pass as query params to Grafana iframe URL:
        &from=now-24h&to=now
Step 3: All panels update simultaneously
```

**Implementation:** A row of buttons that update Grafana embed URL params.

**Effort:** 1-2 hours.

---

### 6.4 Onboarding Wizard / First-Run Guide — OUT-OF-BOX

**What:** When a new user logs in for the first time, show a 3-step guide: "Here's your dashboard → Here's how to set an alert → Here's how to export data."

**Why clients love it:** They don't read documentation. A 30-second walkthrough prevents 90% of support questions.

**How it works:**
```
Step 1: Track `has_completed_onboarding` per user (boolean)
Step 2: If false → show overlay with tooltip arrows pointing at key UI elements
Step 3: "Next → Next → Done" flow
Step 4: Set flag to true, never show again
```

**Implementation:** `react-joyride` library or custom overlay with absolute positioning.

**Effort:** 3-4 hours.

---

## 7. Smart Defaults That Feel Like Features

### 7.1 Auto-Detect Normal Range — OUT-OF-BOX

**What:** After a device sends data for 24 hours, automatically suggest alert thresholds based on observed range.

**Why clients love it:** "The system learned my device's normal range and suggested alerts for me." Feels like AI. It's just min/max + margin.

**How it works:**
```
Step 1: After 24h of data, calculate: min, max, mean, stddev
Step 2: Suggest thresholds:
        - Warning high: mean + 2σ
        - Critical high: mean + 3σ
        - Warning low: mean - 2σ
        - Critical low: mean - 3σ
Step 3: Show: "Based on 24h of data, we suggest alerting above 28.5C. Set this alert?"
Step 4: User clicks "Accept" → alert created automatically
```

**Implementation:** One query after 24h, one suggestion UI, one-click alert creation.

**Effort:** 3-4 hours. **Feels like ML. It's arithmetic.**

---

### 7.2 "Similar Devices" Baseline — OUT-OF-BOX

**What:** "Your freezer is running at -16C. The 12 other freezers in our system average -18C." Contextual comparison.

**Why clients love it:** Benchmarking against peers. "Am I normal?"

**How it works:**
```
Step 1: Tag devices by type (freezer, motor, HVAC, etc.)
Step 2: Calculate fleet-wide average for same device type
Step 3: Show: "Your device: -16C | Fleet average: -18C"
Step 4: Flag if significantly different from fleet
```

**Implementation:** One aggregation query grouped by device_type. Crosses org boundaries (anonymized — only show averages).

**Effort:** 2-3 hours. **Privacy note:** only show aggregate stats, never individual client data.

---

### 7.3 Automatic Unit Detection — TRIVIAL

**What:** Device sends `{"temperature": 22.5}`. System shows "22.5 C" with the right unit and icon.

**Why clients love it:** Professional polish. Not just raw numbers.

**How it works:**
```
Step 1: Config map:
        temperature → °C, icon: thermometer
        humidity → %, icon: droplet
        pressure → bar, icon: gauge
        current → A, icon: bolt
        vibration → mm/s, icon: activity
Step 2: Match metric name → display unit + icon
Step 3: Show in all cards, charts, alerts
```

**Implementation:** One lookup object. Applied everywhere metrics are displayed.

**Effort:** 1 hour.

---

### 7.4 Smart Alert Messages — TRIVIAL

**What:** Instead of "Alert: temperature > 30", send: "Warehouse B Cold Room 3 temperature is 32.5C (threshold: 30C). This is 2.5C above your limit. The temperature has been rising for the last 45 minutes."

**Why clients love it:** Context. They know what to worry about without opening the dashboard.

**How it works:**
```
Step 1: On alert fire, query:
        - Current value
        - Threshold value
        - Delta (current - threshold)
        - Trend direction (rising/falling/stable from last 1h)
        - Device display name + location
Step 2: Template the message with all context
Step 3: Send enriched email instead of raw alert
```

**Implementation:** String template with 4-5 queried values.

**Effort:** 2-3 hours.

---

## 8. Features That Cost Almost Nothing but Sell Well

### 8.1 Webhook on Alert — TRIVIAL

**What:** When an alert fires, POST a JSON payload to a URL the client configures. They can integrate with Slack, Teams, their own systems.

**Why clients love it:** Integration capability. "We can connect it to anything."

**How it works:**
```
Step 1: Org settings: webhook_url (optional)
Step 2: On alert fire → POST to webhook_url:
        {"alert": "temperature_high", "device": "sensor01",
         "value": 32.5, "threshold": 30, "timestamp": "..."}
Step 3: Client's system receives and handles it
```

**Implementation:** One `httpx.post()` call in the alert handler. Add timeout and retry.

**Effort:** 1-2 hours.

---

### 8.2 Public Status Page — OUT-OF-BOX

**What:** A public URL showing the client's device status. No login needed. Like GitHub's status page.

**Why clients love it:** They can share it with their customers. "Here's proof our cold chain is maintained."

**How it works:**
```
Step 1: Org setting: enable_public_status = true
Step 2: Generate unique URL: status.yourdomain.com/{org_slug}
Step 3: Public page shows:
        - Device list with green/red status
        - Uptime percentage (last 30 days)
        - Last incident timeline
Step 4: No login, no auth (public read-only)
```

**Implementation:** One unauthenticated route, one simplified view of device status.

**Effort:** 4-6 hours.

---

### 8.3 Data Retention Settings — TRIVIAL

**What:** Client chooses: "Keep my data for 30 days / 90 days / 1 year / forever."

**Why clients love it:** Compliance, storage awareness, control.

**How it works:**
```
Step 1: Org setting: retention_days (default 90)
Step 2: InfluxDB retention policy or TimescaleDB retention policy per org
Step 3: Cron job deletes data older than retention_days
Step 4: Display in settings: "Your data is retained for 90 days. Currently using 2.3 GB."
```

**Implementation:** One setting + one scheduled cleanup query.

**Effort:** 2-3 hours.

---

### 8.4 Activity Audit Log — TRIVIAL

**What:** "Who did what when." Every action logged: login, alert created, device renamed, settings changed.

**Why clients love it:** Compliance, accountability, debugging. "Who changed the threshold from 30 to 50?"

**How it works:**
```
Step 1: audit_log table: user_id, action, resource_type, resource_id, details, timestamp
Step 2: Log on every mutating API call
Step 3: Display as searchable/filterable table in admin section
```

**Implementation:** One decorator/middleware that logs after each POST/PUT/DELETE.

**Effort:** 3-4 hours.

---

## 9. Effort vs Impact Matrix

```
HIGH IMPACT
    │
    │  ★ Daily digest        ★ Smart alert messages
    │  ★ Auto-detect range   ★ QR codes
    │  ★ Device map          ★ CSV export
    │  ★ Public status page  ★ Comparison view
    │
    │  ★ Alert acknowledge   ★ Webhook
    │  ★ Sparklines          ★ Device groups
    │  ★ Notification bell   ★ PDF reports
    │
    │  ★ Online/offline dot  ★ Uptime %
    │  ★ Last reading card   ★ All-quiet banner
    │  ★ Dark mode           ★ Snooze alerts
    │  ★ Auto-refresh timer  ★ Unit detection
    │  ★ Date range picker   ★ Device naming
    │
LOW IMPACT ──────────────────────────────────── HIGH EFFORT
           1h        3h        6h        1d
```

---

## 10. Recommended Build Order

Build these in this order — each adds visible value with minimal effort:

| # | Feature | Effort | When | Tag |
|---|---------|:---:|------|:---:|
| 1 | Device online/offline dot | 2h | Sprint 0 | TRIVIAL |
| 2 | Last reading card | 1h | Sprint 0 | TRIVIAL |
| 3 | Device naming | 1h | Sprint 0 | TRIVIAL |
| 4 | Unit detection | 1h | Sprint 1 | TRIVIAL |
| 5 | All-quiet banner | 1h | Sprint 2 | OUT-OF-BOX |
| 6 | Date range picker | 1.5h | Sprint 1 | TRIVIAL |
| 7 | Auto-refresh indicator | 30m | Sprint 1 | TRIVIAL |
| 8 | Alert acknowledge button | 2h | Sprint 2 | TRIVIAL |
| 9 | Snooze / maintenance window | 2.5h | Sprint 2 | TRIVIAL |
| 10 | Smart alert messages | 2.5h | Sprint 2 | TRIVIAL |
| 11 | CSV export | 2.5h | Sprint 3 | TRIVIAL |
| 12 | Min/max/avg cards | 1.5h | Sprint 1 | TRIVIAL |
| 13 | Device groups / tags | 3.5h | Sprint 3 | TRIVIAL |
| 14 | Notification bell | 3.5h | Sprint 3 | TRIVIAL |
| 15 | Auto-detect normal range | 3.5h | Sprint 3 | OUT-OF-BOX |
| 16 | Dark mode | 2.5h | Sprint 3 | TRIVIAL |
| 17 | QR code for device | 1.5h | Sprint 3 | OUT-OF-BOX |
| 18 | Webhook on alert | 1.5h | Sprint 3 | TRIVIAL |
| 19 | Uptime percentage | 2.5h | Sprint 3 | TRIVIAL |
| 20 | Alert history timeline | 3.5h | Sprint 3 | TRIVIAL |
| 21 | Device notes | 2.5h | Sprint 3 | OUT-OF-BOX |
| 22 | Sparklines on device list | 3.5h | Sprint 3 | OUT-OF-BOX |
| 23 | Audit log | 3.5h | Sprint 3 | TRIVIAL |
| 24 | Onboarding wizard | 3.5h | Sprint 4 | OUT-OF-BOX |
| 25 | Daily/weekly digest | 5h | Sprint 4 | OUT-OF-BOX |
| 26 | Comparison view | 5h | Sprint 4 | OUT-OF-BOX |
| 27 | Device map | 5h | Sprint 4 | OUT-OF-BOX |
| 28 | Connection quality | 1.5h | Sprint 4 | TRIVIAL |
| 29 | Escalation | 3.5h | Sprint 4 | TRIVIAL |
| 30 | Data retention settings | 2.5h | Sprint 5 | TRIVIAL |
| 31 | Public status page | 5h | Sprint 5 | OUT-OF-BOX |
| 32 | Similar devices baseline | 2.5h | Sprint 5 | OUT-OF-BOX |
| 33 | PDF reports | 8h+ | Sprint 5 | OUT-OF-BOX |

**Total: ~33 features, ~90 hours.** Sprinkle 2-3 per sprint alongside core work. Each one makes the product feel more polished and complete.

---

*Companion to [`TECH-LEAD-PLAYBOOK.md`](./TECH-LEAD-PLAYBOOK.md) — see sprint plan for when to weave these in.*

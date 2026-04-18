# IoTDash — Edge AI Strategy

> **Purpose:** What changes when you run analytics on the device/gateway (edge) instead of the cloud. What's possible, what's practical, and how the mechanics differ.

---

## 1. You're Not Confusing Anything

The analytics from `CLASSICAL-VS-ML-ANALYTICS.md` and `PREDICTIVE-MAINTENANCE.md` can run in **three places**:

```
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│   DEVICE     │        │   GATEWAY    │        │    CLOUD     │
│   (edge)     │───────►│   (edge)     │───────►│   (server)   │
│              │        │              │        │              │
│ Microcontroller       │ Raspberry Pi │        │ Azure / AWS  │
│ ESP32, STM32 │        │ Jetson Nano  │        │ Your backend │
│ 256KB-4MB RAM│        │ 1-8GB RAM    │        │ 16-64GB RAM  │
└──────────────┘        └──────────────┘        └──────────────┘

What can run here:        What can run here:       What can run here:
- Threshold checks        - Everything device can   - Everything
- Simple averages         - SPC / Z-score           - ML training
- Rate-of-change          - Trend fitting           - Complex ML inference
- Data filtering          - Isolation Forest        - Cross-device analysis
- Duty cycle counting     - Small neural nets       - Historical queries
                          - TinyML models           - Dashboards
                          - Local alerting          - Multi-tenant logic
```

**The key difference:** Edge analytics run **before** data is sent to the cloud. This changes cost, latency, bandwidth, and reliability.

---

## 2. Why Run Analytics at the Edge?

| Reason | Explanation | Example |
|--------|-------------|---------|
| **Bandwidth savings** | Don't send every reading to the cloud. Send only anomalies/summaries. | 100 devices × 1 msg/sec = 8.6M messages/day. Edge filtering → send only 10K/day. |
| **Latency** | Edge reacts in milliseconds. Cloud round-trip takes 100-500ms. | Emergency shutoff: motor overheating → cut power NOW, not in 500ms. |
| **Offline resilience** | Edge works without internet. Cloud doesn't. | Factory in rural area with spotty connectivity. |
| **Cost** | Less data transmitted = less cloud ingestion cost. | InfluxDB/TimescaleDB storage, MQTT broker load, egress fees. |
| **Privacy** | Sensitive data stays on-premise. | Medical devices, military, some manufacturing. |

---

## 3. What Changes: Edge vs Cloud for Each Technique

### 3.1 Classical Techniques on the Edge

| Technique | On Device? | On Gateway? | What Changes |
|-----------|:---:|:---:|---------|
| Static threshold | Yes | Yes | **Runs identically.** Just an `if` statement. Device can self-alert. |
| Rate-of-change | Yes | Yes | Needs to buffer last N readings. Minimal memory. Works fine. |
| Moving average | Yes | Yes | Ring buffer of N values. ESP32 handles this easily. |
| Dead-band / hysteresis | Yes | Yes | Two thresholds + state bit. Trivial. |
| SPC (control charts) | Partial | Yes | Device needs μ and σ pre-loaded. Can check but can't recalculate from full history. Gateway can recalculate locally. |
| Z-score anomaly | Partial | Yes | Same as SPC — needs pre-computed μ,σ. |
| Duty cycle tracking | Yes | Yes | Simple counter. |
| Trend extrapolation | No | Yes | Needs enough history + `polyfit`. Too heavy for most microcontrollers. Gateway handles it. |
| Seasonality decomposition | No | Yes | Needs weeks of data + computation. Gateway or cloud only. |

**Key pattern:** Simple comparisons run on the device. Anything needing history or computation moves to the gateway.

---

### 3.2 ML Techniques on the Edge

| Technique | On Device (TinyML)? | On Gateway? | What Changes |
|-----------|:---:|:---:|---------|
| Isolation Forest (inference) | No | Yes | ~10KB model. Gateway runs it easily. |
| Random Forest (inference) | Partial | Yes | Small models (≤100 trees) can run on ESP32 with TinyML. |
| Autoencoder (inference) | Partial | Yes | TensorFlow Lite Micro on ESP32. Model <100KB. Possible but tight. |
| LSTM (inference) | No | Yes | Too heavy for microcontrollers. Jetson Nano or Raspberry Pi 4 handles it. |
| Gradient Boosting (inference) | No | Yes | XGBoost inference needs more memory than ESP32 has. Gateway. |
| **Any model TRAINING** | No | Rare | Train in cloud, deploy model to edge. Gateway can do incremental updates. |

**Key pattern:**
- **Training always in the cloud** (or on a powerful workstation)
- **Inference can run on the edge** — deploy the trained model to device/gateway
- The lighter the model, the closer to the device it can run

---

## 4. Edge Architecture Patterns

### Pattern A — Filter at Edge, Analyze in Cloud (Recommended for IoTDash MVP)

```
Device                          Cloud
┌────────────────┐              ┌─────────────────┐
│ Sensor reads   │              │                  │
│ every 1 second │              │ InfluxDB/        │
│                │              │ TimescaleDB      │
│ Edge logic:    │   MQTT       │                  │
│ - Threshold    │─────────────►│ Grafana          │
│   check        │  Only send:  │                  │
│ - Rate check   │  - 1/min avg │ Alert engine     │
│ - Average 60   │  - Anomalies │                  │
│   readings     │  - Alerts    │ Dashboard        │
│ - Send summary │              │                  │
└────────────────┘              └─────────────────┘

Data reduction: 60:1
Device sends 1 message/minute (average) instead of 60 messages/minute
+ immediate anomaly messages when thresholds crossed
```

**How it works mechanically:**
```
Step 1: Device reads sensor every 1 second
Step 2: Store in ring buffer (last 60 readings)
Step 3: Every 60 seconds:
        - Calculate: min, max, mean, std of buffer
        - Publish summary: {device_id}/from/message
          {"temp_avg": 22.5, "temp_min": 21.8, "temp_max": 23.1,
           "temp_std": 0.4, "samples": 60}
Step 4: On EVERY reading, check thresholds:
        - If temp > 80 → immediately publish: {device_id}/from/alert
          {"type": "threshold", "metric": "temperature", "value": 85.2}
Step 5: Cloud receives summaries + alerts only
        - 98% bandwidth reduction for steady-state
        - Zero latency on critical alerts (device catches them)
```

**Implementation on ESP32/Arduino:**
```
// Pseudocode — runs on device firmware
float buffer[60];
int idx = 0;

void loop() {
    float temp = readSensor();
    buffer[idx++ % 60] = temp;

    // Immediate alert check
    if (temp > THRESHOLD_HIGH) {
        mqtt.publish("device01/from/alert",
            "{\"type\":\"threshold\",\"value\":" + String(temp) + "}");
    }

    // Summary every 60 readings
    if (idx % 60 == 0) {
        float avg = mean(buffer, 60);
        float sd = stddev(buffer, 60);
        mqtt.publish("device01/from/message",
            "{\"temp_avg\":" + String(avg) +
            ",\"temp_std\":" + String(sd) + "}");
    }

    delay(1000);
}
```

---

### Pattern B — Gateway Intelligence (Recommended at 100+ devices per site)

```
Devices (many)          Gateway (1 per site)           Cloud
┌────────────┐          ┌─────────────────────┐        ┌──────────┐
│ Sensor #1  │──────┐   │                     │        │          │
│ (raw data) │      │   │ Aggregation:        │  MQTT  │ Time-    │
├────────────┤      ├──►│ - Collect from all  │───────►│ series   │
│ Sensor #2  │──────┤   │   devices on site   │        │ DB       │
│ (raw data) │      │   │ - SPC per device    │        │          │
├────────────┤      │   │ - Anomaly detection │        │ Web App  │
│ Sensor #3  │──────┘   │ - Local dashboard   │        │          │
│ (raw data) │          │ - Offline buffering │        │ Alerts   │
└────────────┘          └─────────────────────┘        └──────────┘

Devices → Gateway: local network (WiFi, BLE, Zigbee, wired)
Gateway → Cloud: internet (MQTT over TLS)
```

**Gateway runs (Raspberry Pi 4 / Jetson Nano / industrial PC):**
- Local MQTT broker (Mosquitto) — devices connect locally
- Python analytics service:
  - Aggregates data from all local devices
  - Runs SPC, Z-score, trend analysis per device
  - Runs Isolation Forest or small ML models
  - Buffers data if internet is down (SQLite or local InfluxDB)
- Forwards summaries + alerts to cloud MQTT (your EMQX)
- Optional: local Grafana dashboard for on-site operators

**Offline resilience:** Gateway stores data locally. When internet returns, it flushes the buffer to the cloud. No data loss.

---

### Pattern C — Full Edge ML (10K+ devices, advanced)

```
Device                  Gateway                     Cloud
┌──────────────┐        ┌───────────────────┐       ┌───────────────┐
│ TinyML model │        │ ML inference      │       │ ML training   │
│ on ESP32     │        │ on Jetson Nano    │       │ Model registry│
│              │        │                   │       │               │
│ - Vibration  │ raw ──►│ - RUL prediction  │ ────► │ - Retrain     │
│   anomaly    │ data   │ - Failure classif │ pred  │   monthly     │
│   detection  │        │ - Multi-device    │ only  │ - Push new    │
│              │        │   correlation     │       │   models to   │
│ Alerts ──────│────────│──────────────────►│       │   gateways    │
└──────────────┘        └───────────────────┘       └───────────────┘

Cloud sends: updated models (monthly)
Gateway sends: predictions + alerts (not raw data)
Device sends: immediate critical alerts
```

**Model deployment pipeline:**
```
Step 1: Train model in cloud (Python, full dataset)
Step 2: Export model:
        - For gateway: ONNX / TensorFlow SavedModel / pickle
        - For device: TensorFlow Lite Micro / ONNX Micro
Step 3: Push to gateway: MQTT command or HTTP pull
        Gateway downloads new model file, hot-swaps
Step 4: Push to device: OTA firmware update
        New model baked into firmware binary
Step 5: Gateway runs inference on new data
        Device runs lightweight anomaly detection
```

---

## 5. TinyML: Running ML on Microcontrollers

**TinyML** = ML models that run on devices with <1MB RAM (ESP32, STM32, Arduino).

### What's Possible

| Model Type | Model Size | Inference Time | RAM Needed | Example Use |
|-----------|:---:|:---:|:---:|---------|
| Simple threshold + stats | <1KB | <1ms | 1-4KB | Threshold, rate-of-change, average |
| Decision tree (1 tree) | 1-10KB | <1ms | 2-8KB | Simple anomaly classification |
| Random Forest (10 trees) | 10-50KB | 1-5ms | 16-64KB | Vibration anomaly detection |
| Small neural net (MLP) | 10-100KB | 1-10ms | 16-128KB | Sensor fusion, pattern recognition |
| CNN (1D, small) | 50-200KB | 5-50ms | 64-256KB | Vibration frequency analysis |
| Autoencoder (tiny) | 20-100KB | 5-20ms | 32-128KB | Anomaly detection (3-5 features) |

### What's NOT Possible on Microcontrollers

- LSTM / RNN (too much memory for state)
- Large Random Forest (>100 trees)
- Transformers / attention models
- Any model training (inference only)
- Processing images (need Jetson Nano minimum)

### Frameworks

| Framework | Target | Language |
|-----------|--------|---------|
| TensorFlow Lite Micro | ESP32, STM32, Arduino | C++ |
| Edge Impulse | ESP32, Arduino, Nordic | C++ (auto-generated from web UI) |
| ONNX Micro Runtime | Various microcontrollers | C |
| emlearn | ESP32, Arduino | C (auto-generated from Python sklearn) |
| micromlgen | Arduino | C++ (from Python sklearn) |

**Edge Impulse** is the easiest path: train model in browser, deploy to ESP32 with generated C++ library. No ML expertise needed for simple models.

---

## 6. What Changes in Your IoTDash Architecture

### Today (Cloud-Only)

```
Device → EMQX → Telegraf → InfluxDB → Grafana → Alert
```

All intelligence is in the cloud. Devices are dumb sensors.

### With Edge (Pattern A — Device Filtering)

```
Device (smart):
  - Read sensor
  - Buffer 60 readings
  - Check thresholds locally
  - Send summary + alerts to cloud

Cloud (same as today):
  - Receives 60x less data
  - Grafana displays summaries
  - Alerts are faster (device-side) + deeper (cloud-side)
```

**What changes in your stack:**
- **Device firmware** needs to be smarter (buffer, average, threshold check)
- **MQTT topic scheme** adds `{device_id}/from/alert` for edge-detected alerts
- **Telegraf config** needs to handle both summaries and raw alert messages
- **InfluxDB** stores less data (summaries, not every reading)
- **Web app** needs to display device-generated alerts alongside Grafana alerts
- **Backend** needs an endpoint to configure device thresholds (pushed via MQTT `{device_id}/to/config`)

### With Edge (Pattern B — Gateway)

**Additional changes:**
- **Gateway software** (Python service) needs to be built and maintained
- **Deployment** now includes gateway provisioning (not just cloud containers)
- **Device management** includes gateway management (firmware updates, monitoring)
- **Offline handling** — web app shows "last seen" and "buffered data pending"

---

## 7. Edge vs Cloud: Decision Matrix for IoTDash

| Factor | Do It at Edge | Do It in Cloud |
|--------|:---:|:---:|
| Reading sensor values | Always | Never |
| Threshold alerts | Yes — faster, works offline | Also yes — as backup/confirmation |
| Rate-of-change | Yes — low compute | Also yes — for historical analysis |
| Moving average / summary | Yes — reduces bandwidth | Receives pre-averaged data |
| SPC control charts | Gateway — yes | Also yes — for dashboard display |
| Trend extrapolation | Gateway — if enough local history | Preferred — has full history |
| ML anomaly detection | Gateway — with pre-trained model | Also yes — can use bigger models |
| RUL prediction | Gateway — with pre-trained model | Preferred — has cross-device data |
| Model training | Never (not enough compute/data) | Always |
| Cross-device correlation | Never (doesn't see other devices) | Always (has all device data) |
| Dashboard / visualization | Local gateway only (for on-site) | Always (web app) |
| Multi-tenant logic | Never | Always |

---

## 8. Recommended Progression for IoTDash

| Stage | Edge Strategy | What Runs Where |
|-------|--------------|-----------------|
| **MVP** (now) | None — devices are dumb sensors | All analytics in cloud (Grafana/InfluxDB) |
| **v2** (after MVP) | Pattern A — device-side filtering | Device: threshold + summary. Cloud: everything else. |
| **v3** (100+ devices/site) | Pattern B — gateway | Gateway: aggregation + SPC + buffering. Cloud: ML + dashboards. |
| **v4** (advanced customers) | Pattern C — edge ML | Gateway: ML inference + RUL. Cloud: training + model registry. |

**Don't build edge before cloud works.** Your cloud analytics are the foundation. Edge is an optimization you layer on when bandwidth costs or latency requirements demand it.

---

## 9. What This Means for Your Product Offering

| Tier | What Client Gets | Edge Needed? |
|------|-----------------|:---:|
| **Basic** | Cloud dashboards + threshold alerts | No |
| **Standard** | + SPC + trend analysis + condition-based maintenance | No |
| **Professional** | + Gateway with offline resilience + local dashboards | Yes (gateway) |
| **Enterprise** | + Predictive maintenance (ML) + anomaly detection | Yes (gateway + ML) |

Edge capability becomes a **premium tier differentiator**. Basic clients just need a sensor publishing to your cloud. Enterprise clients get a gateway with local intelligence.

---

*Companions:*
- *[`CLASSICAL-VS-ML-ANALYTICS.md`](./CLASSICAL-VS-ML-ANALYTICS.md) — what's classical vs what needs ML*
- *[`PREDICTIVE-MAINTENANCE.md`](./PREDICTIVE-MAINTENANCE.md) — deep dive on predictive maintenance levels*

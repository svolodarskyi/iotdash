# MQTT Topic Structure

## Topic Format

All MQTT messages use the following topic structure:

```
iot/{device_id}/mo/{message_type}
```

### Components:

| Position | Component | Description | Example |
|----------|-----------|-------------|---------|
| 1 | `iot` | Fixed prefix for all IoT messages | `iot` |
| 2 | `{device_id}` | Unique device identifier | `DEVICE001` |
| 3 | `mo` | Message Originated (fixed) | `mo` |
| 4 | `{message_type}` | Type of message | `message`, `cfg` |

---

## Message Types

### 1. Device Data (Sensor Readings)

**Topic:** `iot/{device_id}/mo/message`

**Direction:** Device → Server

**Purpose:** Send sensor data/metrics to the server

**Example:**
```
Topic: iot/DEVICE001/mo/message
Payload: {"temperature": 25.5, "humidity": 60}
```

**Telegraf subscribes to:** `iot/+/mo/message`

---

### 2. Device Configuration

**Topic:** `iot/{device_id}/mo/cfg`

**Direction:** Server → Device

**Purpose:** Send configuration updates to device (enable/disable metrics)

**Example:**
```
Topic: iot/DEVICE001/mo/cfg
Payload: {"metrics": {"temperature": 1, "humidity": 1, "pressure": 0}}
```

**Device subscribes to:** `iot/DEVICE001/mo/cfg`

---

## Device Code Examples

### Python

```python
import paho.mqtt.client as mqtt
import json

BROKER = "YOUR_AZURE_IP"
PORT = 1883
DEVICE_ID = "DEVICE001"

# Topics
TOPIC_PUBLISH = f"iot/{DEVICE_ID}/mo/message"
TOPIC_SUBSCRIBE = f"iot/{DEVICE_ID}/mo/cfg"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=DEVICE_ID)

# Subscribe to config updates
client.subscribe(TOPIC_SUBSCRIBE)

# Publish sensor data
data = {"temperature": 25.5, "humidity": 60}
client.publish(TOPIC_PUBLISH, json.dumps(data))
```

### Arduino/ESP32

```cpp
const char* device_id = "DEVICE001";
const char* topic_publish = "iot/DEVICE001/mo/message";
const char* topic_subscribe = "iot/DEVICE001/mo/cfg";

void setup() {
  client.setServer(mqtt_broker, 1883);
  client.connect(device_id);

  // Subscribe to config
  client.subscribe(topic_subscribe);
}

void loop() {
  // Publish sensor data
  String payload = "{\"temperature\":25.5,\"humidity\":60}";
  client.publish(topic_publish, payload.c_str());
  delay(10000);
}
```

### MicroPython

```python
from umqtt.simple import MQTTClient
import ujson

DEVICE_ID = "DEVICE001"
topic_publish = f"iot/{DEVICE_ID}/mo/message"
topic_subscribe = f"iot/{DEVICE_ID}/mo/cfg"

client = MQTTClient(DEVICE_ID, "YOUR_AZURE_IP", 1883)
client.connect()

# Subscribe to config
client.subscribe(topic_subscribe)

# Publish data
data = {"temperature": 25.5, "humidity": 60}
client.publish(topic_publish, ujson.dumps(data))
```

---

## Testing with Mosquitto

### Simulate Device Sending Data

```bash
mosquitto_pub -h YOUR_AZURE_IP -p 1883 \
  -t "iot/DEVICE001/mo/message" \
  -m '{"temperature":25.5,"humidity":60}'
```

### Simulate Server Sending Config

```bash
mosquitto_pub -h YOUR_AZURE_IP -p 1883 \
  -t "iot/DEVICE001/mo/cfg" \
  -m '{"metrics":{"temperature":1,"humidity":1}}'
```

### Subscribe to All Device Messages

```bash
# See all data from all devices
mosquitto_sub -h YOUR_AZURE_IP -p 1883 -t "iot/+/mo/message"

# See all messages for specific device
mosquitto_sub -h YOUR_AZURE_IP -p 1883 -t "iot/DEVICE001/mo/#"

# See all IoT messages
mosquitto_sub -h YOUR_AZURE_IP -p 1883 -t "iot/#"
```

---

## Telegraf Configuration

Telegraf subscribes to device data messages and extracts device_id from position 2:

```toml
[[inputs.mqtt_consumer]]
  servers = ["tcp://emqx:1883"]
  topics  = ["iot/+/mo/message"]

  [[inputs.mqtt_consumer.topic_parsing]]
    topic = "iot/+/mo/message"
    tags  = "_/device_id/_/_"
```

**Parsing explanation:**
- `_` = ignore position 1 (`iot`)
- `device_id` = capture position 2 as `device_id` tag
- `_` = ignore position 3 (`mo`)
- `_` = ignore position 4 (`message`)

---

## Backend Configuration

Backend publishes config to devices:

```python
# In backend/app/services/mqtt_publisher.py
topic = f"iot/{device_code}/mo/cfg"
payload = {"metrics": metrics_state}
client.publish(topic, json.dumps(payload))
```

---

## Important Notes

✅ **Device ID must match** in firmware and IoTDash database
✅ **All topics use `mo`** (no `mt` for message terminated)
✅ **JSON format required** for all payloads
✅ **QoS 0 or 1** recommended
✅ **Topic is case-sensitive**

---

## Wildcards in MQTT

| Wildcard | Meaning | Example | Matches |
|----------|---------|---------|---------|
| `+` | Single level | `iot/+/mo/message` | `iot/DEVICE001/mo/message` |
| `#` | Multiple levels | `iot/DEVICE001/#` | `iot/DEVICE001/mo/message`, `iot/DEVICE001/mo/cfg` |

---

## Summary

**Device sends data:**
```
Topic: iot/DEVICE001/mo/message
Payload: {"temperature": 25.5}
```

**Server sends config:**
```
Topic: iot/DEVICE001/mo/cfg
Payload: {"metrics": {"temperature": 1}}
```

**Telegraf listens to:**
```
iot/+/mo/message
```

**Device listens to:**
```
iot/DEVICE001/mo/cfg
```

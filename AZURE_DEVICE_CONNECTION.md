# Connecting IoT Devices to MQTT in Azure

This guide explains how IoT devices connect to your IoTDash MQTT broker (EMQX) when deployed in Azure.

## Architecture Overview

```
┌──────────────┐                    ┌─────────────────────────────────┐
│              │                    │      Azure Cloud                │
│  IoT Device  │──────MQTT──────────▶  Public IP / Domain             │
│  (ESP32,     │   Port 1883/8883   │         │                       │
│   Raspberry  │                    │         ▼                       │
│   Pi, etc.)  │                    │  ┌─────────────┐                │
│              │                    │  │    EMQX     │                │
└──────────────┘                    │  │ MQTT Broker │                │
                                    │  └──────┬──────┘                │
                                    │         │                       │
                                    │         ▼                       │
                                    │  ┌─────────────┐                │
                                    │  │  Telegraf   │                │
                                    │  │  (Decoder)  │                │
                                    │  └──────┬──────┘                │
                                    │         │                       │
                                    │         ▼                       │
                                    │  ┌─────────────┐                │
                                    │  │  InfluxDB   │                │
                                    │  └─────────────┘                │
                                    └─────────────────────────────────┘
```

---

## Prerequisites

Before connecting devices, you need:

1. ✅ IoTDash deployed in Azure (web app, EMQX, InfluxDB, etc.)
2. ✅ EMQX MQTT broker exposed to the internet
3. ✅ Public IP address or domain name for your Azure deployment
4. ✅ Firewall rules allowing MQTT traffic (port 1883 or 8883)

---

## Step 1: Expose EMQX MQTT Broker

### Option A: Azure Container Instances / VM

If deploying on Azure VM or Container Instances, expose port 1883:

```yaml
# In docker-compose.yml or Azure Container definition
emqx:
  image: emqx/emqx:5.8
  ports:
    - "1883:1883"    # MQTT (expose this)
    - "8883:8883"    # MQTT over TLS (recommended for production)
    - "18083:18083"  # EMQX Dashboard (keep internal)
```

### Option B: Azure App Service with External MQTT

Azure App Service doesn't support TCP port exposure well. Consider:
- Deploy EMQX separately on Azure Container Instances or VM
- Use Azure IoT Hub instead (requires code changes)
- Use a managed MQTT service

### Option C: Azure Kubernetes Service (AKS)

```yaml
# Kubernetes Service with LoadBalancer
apiVersion: v1
kind: Service
metadata:
  name: emqx-mqtt
spec:
  type: LoadBalancer
  ports:
    - port: 1883
      targetPort: 1883
      protocol: TCP
      name: mqtt
    - port: 8883
      targetPort: 8883
      protocol: TCP
      name: mqtts
  selector:
    app: emqx
```

---

## Step 2: Configure Azure Networking

### Firewall / Network Security Group Rules

Add inbound rule to allow MQTT traffic:

```
Protocol: TCP
Port: 1883 (MQTT) and/or 8883 (MQTT over TLS)
Source: Any (0.0.0.0/0) or specific IP ranges
Destination: Your EMQX container/VM
Action: Allow
```

**Azure Portal Steps:**
1. Go to your VM/Container Instance
2. Navigate to **Networking** → **Inbound port rules**
3. Click **Add inbound port rule**
4. Configure:
   - Source: `Any` or `IP Addresses`
   - Source port ranges: `*`
   - Destination: `Any`
   - Destination port ranges: `1883,8883`
   - Protocol: `TCP`
   - Action: `Allow`
   - Priority: `1000`
   - Name: `AllowMQTT`

---

## Step 3: Get Your MQTT Connection Details

### Find Your Public Endpoint

**For Azure VM:**
```bash
# Get public IP
az vm list-ip-addresses --name YOUR_VM_NAME --resource-group YOUR_RG
```

**For Azure Container Instance:**
```bash
# Get public IP
az container show --name YOUR_CONTAINER --resource-group YOUR_RG --query ipAddress.ip
```

**For AKS:**
```bash
# Get LoadBalancer external IP
kubectl get service emqx-mqtt -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### Your Device Connection Settings

Once you have the public IP or domain, devices will connect with:

```python
# Example connection details
MQTT_BROKER = "20.123.45.67"  # Your Azure public IP or domain
MQTT_PORT = 1883              # Or 8883 for TLS
MQTT_TOPIC = "DEVICE_CODE/from/message"
```

---

## Step 4: Device Code Examples

### Python (Raspberry Pi, Linux)

```python
import paho.mqtt.client as mqtt
import json
import time

# Azure MQTT connection settings
MQTT_BROKER = "YOUR_AZURE_IP_OR_DOMAIN"  # e.g., "20.123.45.67"
MQTT_PORT = 1883
DEVICE_CODE = "DEVICE001"  # Your device unique code
MQTT_TOPIC = f"{DEVICE_CODE}/from/message"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to Azure MQTT broker!")
    else:
        print(f"Connection failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully")

# Create MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=DEVICE_CODE)
client.on_connect = on_connect
client.on_publish = on_publish

# Connect to Azure MQTT broker
print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# Send data to Azure
while True:
    # Read sensor data
    data = {
        "temperature": 25.5,
        "humidity": 60.2,
        "timestamp": int(time.time())
    }

    # Publish to Azure
    payload = json.dumps(data)
    result = client.publish(MQTT_TOPIC, payload, qos=0)
    print(f"Sent: {payload}")

    time.sleep(10)  # Send every 10 seconds
```

### MicroPython (ESP32, ESP8266)

```python
from umqtt.simple import MQTTClient
import ujson
import time
from machine import Pin

# Azure MQTT connection settings
MQTT_BROKER = "YOUR_AZURE_IP_OR_DOMAIN"  # e.g., "20.123.45.67"
MQTT_PORT = 1883
DEVICE_CODE = "DEVICE001"
MQTT_TOPIC = f"{DEVICE_CODE}/from/message"

# Connect to WiFi first (not shown)
# ...

# Connect to Azure MQTT broker
client = MQTTClient(DEVICE_CODE, MQTT_BROKER, port=MQTT_PORT)
client.connect()
print("Connected to Azure MQTT!")

# Send data loop
while True:
    # Read sensor data
    data = {
        "temperature": 25.5,
        "humidity": 60.2
    }

    # Publish to Azure
    payload = ujson.dumps(data)
    client.publish(MQTT_TOPIC, payload)
    print(f"Sent: {payload}")

    time.sleep(10)
```

### Arduino (ESP32)

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Azure MQTT settings
const char* mqtt_broker = "YOUR_AZURE_IP_OR_DOMAIN";  // e.g., "20.123.45.67"
const int mqtt_port = 1883;
const char* device_code = "DEVICE001";
const char* mqtt_topic = "DEVICE001/from/message";

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("Connecting to Azure MQTT...");
    if (client.connect(device_code)) {
      Serial.println("connected!");
    } else {
      Serial.print("failed, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_broker, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect_mqtt();
  }
  client.loop();

  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["temperature"] = 25.5;
  doc["humidity"] = 60.2;

  char payload[256];
  serializeJson(doc, payload);

  // Publish to Azure
  client.publish(mqtt_topic, payload);
  Serial.print("Sent: ");
  Serial.println(payload);

  delay(10000);  // Send every 10 seconds
}
```

---

## Step 5: Configure Devices in IoTDash

Before devices can send data, they must be registered in IoTDash:

1. **Log into IoTDash** (your Azure web app)
2. **Navigate to Devices** → **Add Device**
3. **Create device with code**: `DEVICE001` (must match device code in firmware)
4. **Assign device type** with metrics (temperature, humidity, etc.)
5. **Enable metrics** you want to collect
6. **Save device**

The device code in your firmware **must match** the device code in IoTDash!

---

## Step 6: Message Format

Devices must send messages in JSON format to topic: `{DEVICE_CODE}/from/message`

### Required Format:

```json
{
  "temperature": 25.5,
  "humidity": 60.2,
  "pressure": 1013.25
}
```

- **Topic**: `DEVICE001/from/message` (replace DEVICE001 with your device code)
- **QoS**: 0 or 1
- **Format**: JSON object with metric names as keys

### Example Messages:

```json
// Simple reading
{"temperature": 22.3}

// Multiple metrics
{"temperature": 22.3, "humidity": 55.2, "pressure": 1015}

// With timestamp (optional)
{"temperature": 22.3, "timestamp": 1714089600}
```

---

## Step 7: Verify Connection

### Check EMQX Dashboard

1. Access EMQX dashboard: `http://YOUR_AZURE_IP:18083`
2. Login: `admin` / `public` (change in production!)
3. Go to **Connections** → Check if your device is listed
4. Go to **Topics** → Verify messages are being published

### Check Telegraf Logs

```bash
# SSH into your Azure VM/container
docker-compose logs -f telegraf

# You should see:
# I! [inputs.mqtt_consumer] Connected [tcp://emqx:1883]
```

### Check InfluxDB Data

```bash
# Query InfluxDB to see device data
docker-compose exec influxdb influx query '
  from(bucket: "iot")
    |> range(start: -10m)
    |> filter(fn: (r) => r.device_id == "DEVICE001")
'
```

### Check Grafana Dashboard

1. Open Grafana: `http://YOUR_AZURE_DOMAIN:3000`
2. Go to your device dashboard
3. You should see real-time metrics from your device

---

## Security Recommendations

### For Production Deployments:

1. **Use TLS/SSL** (port 8883 instead of 1883)
   ```python
   # Python example with TLS
   client.tls_set(ca_certs="/path/to/ca.crt")
   client.connect(MQTT_BROKER, 8883, 60)
   ```

2. **Enable EMQX Authentication**
   - Configure username/password in EMQX
   - Update device code:
     ```python
     client.username_pw_set("device_user", "device_password")
     ```

3. **Use Azure VPN/Private Link** for sensitive deployments

4. **Restrict IP ranges** in Network Security Groups

5. **Use Device Certificates** (mutual TLS)

---

## Troubleshooting

### Device Can't Connect

1. **Check firewall rules**: Port 1883/8883 allowed?
2. **Verify public IP**: Can you ping/telnet the IP?
3. **Check EMQX is running**: `docker-compose ps emqx`
4. **Test with MQTT client**:
   ```bash
   # Install mosquitto-clients
   mosquitto_pub -h YOUR_AZURE_IP -p 1883 -t "test/topic" -m "hello"
   ```

### Messages Not Appearing in InfluxDB

1. **Check topic format**: Must be `{DEVICE_CODE}/from/message`
2. **Verify device exists in IoTDash** with matching code
3. **Check Telegraf logs**: `docker-compose logs telegraf`
4. **Verify JSON format**: Must be valid JSON

### Connection Drops

1. **Increase keep-alive**: Set to 60+ seconds
2. **Implement reconnect logic** (shown in examples above)
3. **Check network stability**
4. **Monitor EMQX logs**: `docker-compose logs emqx`

---

## Testing Without Real Device

Use MQTT client tools to simulate device messages:

### Using Mosquitto Client (Linux/Mac)

```bash
# Install
brew install mosquitto  # Mac
sudo apt install mosquitto-clients  # Linux

# Publish test message to Azure
mosquitto_pub -h YOUR_AZURE_IP -p 1883 \
  -t "TEST_DEVICE/from/message" \
  -m '{"temperature":25.5,"humidity":60}'
```

### Using MQTT Explorer (GUI)

1. Download: http://mqtt-explorer.com/
2. Connect to: `YOUR_AZURE_IP:1883`
3. Publish to topic: `DEVICE001/from/message`
4. Send JSON: `{"temperature":25.5}`

---

## Summary

**To connect a device to Azure-deployed IoTDash:**

1. ✅ Deploy IoTDash with EMQX exposed on port 1883
2. ✅ Configure Azure firewall to allow port 1883
3. ✅ Get your Azure public IP or domain
4. ✅ Register device in IoTDash web interface
5. ✅ Flash device firmware with:
   - MQTT broker = Azure IP
   - Device code = Registered device code
   - Topic = `{DEVICE_CODE}/from/message`
6. ✅ Power on device and verify data in Grafana

---

**Need Help?**
- EMQX Docs: https://www.emqx.io/docs/
- Paho MQTT: https://www.eclipse.org/paho/
- Azure Networking: https://docs.microsoft.com/azure/virtual-network/

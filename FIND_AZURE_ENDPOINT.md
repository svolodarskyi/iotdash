# Find Your Azure MQTT Broker Endpoint

## Method 1: Azure Portal (Easiest)

1. Go to https://portal.azure.com
2. Navigate to your resource (VM, Container Instance, or AKS)
3. Click on **Overview**
4. Look for **Public IP address** or **FQDN**

Example:
- Public IP: `20.123.45.67`
- FQDN: `iotdash.eastus.cloudapp.azure.com`

---

## Method 2: Azure CLI

### For Virtual Machine:
```bash
# List all VMs
az vm list --output table

# Get public IP for specific VM
az vm list-ip-addresses \
  --name YOUR_VM_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --output table

# Example output:
# PublicIPAddresses    PrivateIPAddresses
# 20.123.45.67        10.0.0.4
```

### For Container Instance:
```bash
# List all container instances
az container list --output table

# Get specific container IP
az container show \
  --name YOUR_CONTAINER_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --query ipAddress.ip \
  --output tsv

# Example output: 20.123.45.67
```

### For AKS (Kubernetes):
```bash
# Get LoadBalancer external IP
kubectl get service emqx-mqtt -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Or see all services
kubectl get services
```

### For App Service:
```bash
# Get app service URL
az webapp show \
  --name YOUR_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --query defaultHostName \
  --output tsv

# Example output: iotdash.azurewebsites.net
```

---

## Test if MQTT Broker is Online

### Test 1: Ping the IP
```bash
ping YOUR_AZURE_IP

# Example:
ping 20.123.45.67
```

### Test 2: Telnet to MQTT Port
```bash
telnet YOUR_AZURE_IP 1883

# If successful, you'll see:
# Trying 20.123.45.67...
# Connected to 20.123.45.67.
# Escape character is '^]'.

# Press Ctrl+] then type 'quit' to exit
```

### Test 3: Netcat (nc)
```bash
nc -zv YOUR_AZURE_IP 1883

# If successful:
# Connection to 20.123.45.67 port 1883 [tcp/*] succeeded!
```

### Test 4: Mosquitto Client Test
```bash
# Install mosquitto-clients first
# macOS:
brew install mosquitto

# Ubuntu/Debian:
sudo apt install mosquitto-clients

# Test connection
mosquitto_pub -h YOUR_AZURE_IP -p 1883 -t "test/topic" -m "hello"

# If successful, no error is shown
# If fails, you'll see: Error: Connection refused or timeout
```

### Test 5: Subscribe to Test Topic
```bash
# In one terminal, subscribe
mosquitto_sub -h YOUR_AZURE_IP -p 1883 -t "test/#" -v

# In another terminal, publish
mosquitto_pub -h YOUR_AZURE_IP -p 1883 -t "test/hello" -m "world"

# If working, you'll see in subscriber:
# test/hello world
```

---

## Device Configuration Details

Once you find your Azure IP, use these settings for your device:

### Connection Settings:
```
MQTT Broker: YOUR_AZURE_IP (e.g., 20.123.45.67)
MQTT Port: 1883 (or 8883 for TLS)
Device ID: DEVICE001 (your unique device code)
```

### Topics:
```
Publish (send data):
  Topic: iot/DEVICE001/mt/cbor
  Payload: MessagePack (base64 encoded or raw binary)

Subscribe (receive config):
  Topic: iot/DEVICE001/mo/cfg
  Payload: MessagePack (base64 encoded)
```

### Example Device Code:
```python
import paho.mqtt.client as mqtt
import msgpack
import base64

# Your Azure settings
BROKER = "20.123.45.67"  # ← PUT YOUR AZURE IP HERE
PORT = 1883
DEVICE_ID = "DEVICE001"

# Topics
TOPIC_PUBLISH = f"iot/{DEVICE_ID}/mt/cbor"
TOPIC_SUBSCRIBE = f"iot/{DEVICE_ID}/mo/cfg"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=DEVICE_ID)
client.connect(BROKER, PORT, 60)

# Subscribe to config
client.subscribe(TOPIC_SUBSCRIBE)

# Send data
data = {"temperature": 25.5, "humidity": 60}
packed = msgpack.packb(data)
encoded = base64.b64encode(packed)
client.publish(TOPIC_PUBLISH, encoded)
```

---

## Troubleshooting

### "Connection refused"
✅ Check Azure firewall/NSG allows port 1883
✅ Verify EMQX container is running: `docker ps | grep emqx`
✅ Check EMQX logs: `docker logs emqx`

### "Connection timeout"
✅ Verify public IP is correct
✅ Check if VM/container is running
✅ Ensure Network Security Group allows inbound on 1883

### "Cannot resolve hostname"
✅ Use IP address instead of hostname
✅ Check DNS settings if using FQDN

---

## Quick Test Script

Save this as `test_mqtt.sh`:

```bash
#!/bin/bash

AZURE_IP="YOUR_AZURE_IP"  # ← CHANGE THIS

echo "Testing MQTT broker at $AZURE_IP..."

# Test 1: Ping
echo -n "1. Ping test: "
if ping -c 1 -W 2 $AZURE_IP > /dev/null 2>&1; then
    echo "✓ IP is reachable"
else
    echo "✗ IP not reachable"
    exit 1
fi

# Test 2: Port check
echo -n "2. Port 1883 test: "
if nc -zv -w 2 $AZURE_IP 1883 2>&1 | grep -q succeeded; then
    echo "✓ Port 1883 is open"
else
    echo "✗ Port 1883 is closed or filtered"
    exit 1
fi

# Test 3: MQTT publish
echo -n "3. MQTT publish test: "
if mosquitto_pub -h $AZURE_IP -p 1883 -t "test/connection" -m "hello" -q 0 2>&1 | grep -q -v Error; then
    echo "✓ MQTT broker is working"
else
    echo "✗ MQTT broker not responding"
    exit 1
fi

echo ""
echo "✓ All tests passed! MQTT broker is online and ready."
echo ""
echo "Device Configuration:"
echo "  MQTT Broker: $AZURE_IP"
echo "  MQTT Port: 1883"
echo "  Publish Topic: iot/DEVICE001/mt/cbor"
echo "  Subscribe Topic: iot/DEVICE001/mo/cfg"
```

Run it:
```bash
chmod +x test_mqtt.sh
./test_mqtt.sh
```

---

## Summary Checklist

- [ ] Find Azure public IP/FQDN
- [ ] Test with `ping`
- [ ] Test with `telnet` or `nc`
- [ ] Test with `mosquitto_pub`
- [ ] Configure device with:
  - Broker: YOUR_AZURE_IP
  - Port: 1883
  - Topics: `iot/{DEVICE_ID}/mt/cbor` (publish), `iot/{DEVICE_ID}/mo/cfg` (subscribe)
  - Format: MessagePack (base64 encoded)
- [ ] Register device in IoTDash web UI
- [ ] Test end-to-end data flow

---

**Need more help?** See:
- MQTT_TOPIC_STRUCTURE.md
- AZURE_DEVICE_CONNECTION.md
- encoding_decoding_extension.md

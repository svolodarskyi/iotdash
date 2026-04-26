# Quick Start: Connect Device to Azure MQTT

## TL;DR - 3 Steps to Connect

### 1. Get Your Azure MQTT Endpoint

After deploying to Azure, get your public IP:

```bash
# For Azure VM
az vm list-ip-addresses --name YOUR_VM_NAME --resource-group YOUR_RG

# For Azure Container Instance
az container show --name YOUR_CONTAINER --resource-group YOUR_RG --query ipAddress.ip

# Or check Azure Portal → Your Resource → Overview → Public IP
```

**Example:** `20.123.45.67`

---

### 2. Update Your Device Code

Change the MQTT broker from `localhost` to your Azure IP:

**Before (Local Development):**
```python
BROKER = "localhost"
PORT = 1883
```

**After (Azure Production):**
```python
BROKER = "20.123.45.67"  # Your Azure public IP
PORT = 1883
```

---

### 3. Run Your Device

Using your existing `fake_device.py`:

```bash
# Connect to Azure instead of localhost
python3 fake_device.py --broker 20.123.45.67 --device-id DEVICE001

# Or set as environment variable
export MQTT_BROKER=20.123.45.67
python3 fake_device.py --broker $MQTT_BROKER
```

---

## Adapting fake_device.py for Azure

### Option A: Command-line Arguments (Easiest)

Your `fake_device.py` already supports `--broker` argument:

```bash
# Local testing
python3 fake_device.py --broker localhost --device-id sensor01

# Azure deployment
python3 fake_device.py --broker YOUR_AZURE_IP --device-id sensor01
```

### Option B: Environment Variables

Create a `.env` file for device configuration:

```bash
# device.env
MQTT_BROKER=20.123.45.67
MQTT_PORT=1883
DEVICE_ID=sensor01
```

Then modify `fake_device.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv('device.env')

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
DEVICE_ID = os.getenv("DEVICE_ID", "sensor01")
```

Run:
```bash
python3 fake_device.py
```

---

## Testing the Connection

### 1. From Your Device/Computer

```bash
# Test if Azure MQTT is reachable
telnet YOUR_AZURE_IP 1883

# Or use mosquitto client
mosquitto_pub -h YOUR_AZURE_IP -p 1883 -t "test/topic" -m "hello azure"
```

### 2. Run Your Fake Device

```bash
python3 fake_device.py --broker YOUR_AZURE_IP --device-id sensor01
```

Expected output:
```
Connected to MQTT broker!
Publishing to sensor01/from/message: {"temperature": 22.45, "humidity": 58.32}
Publishing to sensor01/from/message: {"temperature": 22.89, "humidity": 59.12}
...
```

### 3. Verify in IoTDash

1. Open your Azure web app: `https://YOUR_AZURE_APP.azurewebsites.net`
2. Go to **Devices** → Find `sensor01`
3. Check that metrics are updating in real-time
4. View in **Grafana** dashboard

---

## Real Hardware Examples

### ESP32 (Arduino)

```cpp
// Change this line:
const char* mqtt_broker = "20.123.45.67";  // Your Azure IP

// Rest of code stays the same
```

### Raspberry Pi (Python)

```python
# Change this line:
MQTT_BROKER = "20.123.45.67"  # Your Azure IP

# Rest of code stays the same
```

---

## Common Issues

### "Connection refused"
- ✅ Check Azure firewall allows port 1883
- ✅ Verify EMQX container is running: `docker ps`
- ✅ Test with: `telnet YOUR_AZURE_IP 1883`

### "Connection timeout"
- ✅ Check Network Security Group rules in Azure
- ✅ Verify public IP is correct
- ✅ Check if VM/container is running

### "Device shows offline in dashboard"
- ✅ Verify device code matches in IoTDash
- ✅ Check topic format: `{DEVICE_CODE}/from/message`
- ✅ Verify JSON payload format

---

## Production Checklist

Before deploying real devices:

- [ ] Use MQTT over TLS (port 8883)
- [ ] Enable EMQX authentication (username/password)
- [ ] Restrict Azure NSG to specific IP ranges
- [ ] Use strong passwords for EMQX dashboard
- [ ] Set up monitoring/alerts
- [ ] Test reconnection logic
- [ ] Document device credentials securely

---

## Need More Details?

See the full guide: **AZURE_DEVICE_CONNECTION.md**

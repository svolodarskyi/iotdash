# MQTT Encoding/Decoding Extension

This document explains the encoding/decoding infrastructure for MQTT messages in IoTDash.

## Overview

The system has two processing points:
1. **Encoding** (Backend → MQTT): Before sending config to devices via MQTT
2. **Decoding** (MQTT → InfluxDB): After receiving data from devices via Telegraf

Currently both are **pass-through** (no transformation). Follow the steps below to add your actual encoding/decoding logic.

---

## Architecture

```
┌─────────────┐                    ┌──────────┐                    ┌──────────────┐
│   Backend   │ ──[encode]──────→  │   MQTT   │ ──[decode]──────→  │   InfluxDB   │
│  (Python)   │                    │  (EMQX)  │   (Telegraf +     │              │
│             │                    │          │    Python script) │              │
└─────────────┘                    └──────────┘                    └──────────────┘
```

---

## 1. Encoding (Backend → MQTT)

**File:** `backend/app/services/mqtt_publisher.py`

**Function:** `encode_payload(payload: dict) -> dict`

### How to Add Your Encoding Logic:

1. Open `backend/app/services/mqtt_publisher.py`
2. Find the `encode_payload()` function (around line 14)
3. Replace the pass-through logic with your encoding:

```python
def encode_payload(payload: dict) -> dict:
    """Encode the payload before sending to MQTT."""

    # Example 1: Base64 encode all values
    import base64
    encoded = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            # Recursively encode nested dicts
            encoded[key] = encode_payload(value)
        else:
            value_str = str(value)
            encoded[key] = base64.b64encode(value_str.encode()).decode()
    return encoded

    # Example 2: Hex encode numeric values
    # encoded = {}
    # for key, value in payload.items():
    #     if isinstance(value, int):
    #         encoded[key] = hex(value)
    #     else:
    #         encoded[key] = value
    # return encoded
```

### Testing:
```bash
# After modifying, restart the backend
docker-compose restart backend
```

---

## 2. Decoding (MQTT → InfluxDB)

**File:** `telegraf_decoder.py`

**Functions:**
- `decode_payload(payload: str) -> str` - Decode individual values
- `process_line(line: str) -> str` - Process influx line protocol

### How to Add Your Decoding Logic:

#### Step 1: Add decode logic to `decode_payload()`

```python
def decode_payload(payload: str) -> str:
    """Decode the payload from the device."""

    # Example 1: Base64 decode
    import base64
    try:
        decoded_bytes = base64.b64decode(payload)
        return decoded_bytes.decode('utf-8')
    except Exception:
        return payload  # Return original if decode fails

    # Example 2: Hex decode
    # try:
    #     return bytes.fromhex(payload).decode('utf-8')
    # except Exception:
    #     return payload
```

#### Step 2: Uncomment the parsing logic in `process_line()`

Find the TODO section (around line 85) and uncomment the steps:

```python
# STEP 1: Parse the fields string into a dictionary
field_dict = {}
for field_pair in fields.split(','):
    if '=' in field_pair:
        key, value = field_pair.split('=', 1)
        field_dict[key] = value

# STEP 2: Decode each field value
for key, encoded_value in field_dict.items():
    decoded_value = decode_payload(encoded_value)
    field_dict[key] = decoded_value

# STEP 3: Reconstruct the fields string
decoded_fields = ','.join(f"{k}={v}" for k, v in field_dict.items())

# STEP 4: Reconstruct the complete line
decoded_line = f"{measurement_and_tags} {decoded_fields}"
if timestamp:
    decoded_line += f" {timestamp}"

# Return the decoded line instead of pass-through
return decoded_line
```

### Testing:
```bash
# After modifying, restart telegraf
docker-compose restart telegraf

# View telegraf logs to see if decoding works
docker-compose logs -f telegraf
```

---

## 3. Example: Simple Base64 Encoding/Decoding

### Backend Encoding:
```python
# In backend/app/services/mqtt_publisher.py
import base64

def encode_payload(payload: dict) -> dict:
    encoded = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            encoded[key] = {
                k: base64.b64encode(str(v).encode()).decode()
                for k, v in value.items()
            }
        else:
            encoded[key] = base64.b64encode(str(value).encode()).decode()
    return encoded
```

### Telegraf Decoding:
```python
# In telegraf_decoder.py
import base64

def decode_payload(payload: str) -> str:
    try:
        return base64.b64decode(payload).decode('utf-8')
    except Exception:
        return payload  # Pass through if not base64
```

---

## 4. Verification

### Test the Flow:
1. Start the stack: `docker-compose up -d`
2. Send a device config update from the backend
3. Check MQTT messages: `docker-compose logs emqx | grep "DEVICE_ID"`
4. Check InfluxDB data: Access Grafana at http://localhost:3000
5. Verify data is correctly decoded in InfluxDB

### Debug Logs:
```bash
# Backend encoding logs
docker-compose logs -f backend | grep "Published config"

# Telegraf decoding logs (errors appear in stderr)
docker-compose logs -f telegraf

# View raw MQTT messages
docker exec -it emqx emqx_ctl subscribe "DEVICE_ID/from/message"
```

---

## 5. Files Modified

| File | Purpose | What to Modify |
|------|---------|----------------|
| `backend/app/services/mqtt_publisher.py` | Backend encoding | `encode_payload()` function |
| `telegraf_decoder.py` | Telegraf decoding | `decode_payload()` and `process_line()` |
| `telegraf.conf` | Telegraf config | Already configured (no changes needed) |
| `docker-compose.yml` | Container setup | Already configured (no changes needed) |

---

## Notes

- **Keep encoding/decoding symmetric**: What you encode in the backend should be decodable by Telegraf
- **Handle errors gracefully**: If decoding fails, pass through the original value
- **Test with real devices**: Ensure devices can handle encoded configs
- **Performance**: Simple encodings (base64, hex) have minimal overhead
- **Security**: Encoding is NOT encryption - don't rely on it for security

---

## Future Enhancements

- Add encryption (AES, RSA) for sensitive data
- Implement compression for large payloads
- Add validation before/after encoding/decoding
- Create unit tests for encoding/decoding functions

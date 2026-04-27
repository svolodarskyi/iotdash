#!/usr/bin/env python3
"""
Telegraf execd processor for decoding MQTT messages.

This script reads influx line protocol from stdin, decodes MessagePack data,
and writes the transformed data back to stdout in influx format.
"""

import sys
import msgpack
import base64


def decode_payload(payload: str) -> str:
    """
    Decode MessagePack payload from the device.

    Assumes payload is MessagePack data (possibly base64 encoded).
    Decodes it using msgpack.unpackb and returns the unpacked value.

    Args:
        payload: The MessagePack payload (raw bytes, base64, or hex encoded)

    Returns:
        Decoded payload as string
    """
    try:
        # Try to decode as base64 first (common encoding for binary data in text protocols)
        try:
            msgpack_bytes = base64.b64decode(payload)
        except Exception:
            # If not base64, try hex encoding
            try:
                msgpack_bytes = bytes.fromhex(payload)
            except ValueError:
                # If neither base64 nor hex, treat as raw bytes
                if isinstance(payload, str):
                    msgpack_bytes = payload.encode('latin1')
                else:
                    msgpack_bytes = payload

        # Unpack MessagePack data
        decoded = msgpack.unpackb(msgpack_bytes, raw=False)

        # Convert decoded data to string
        return str(decoded)

    except Exception as e:
        # If MessagePack decoding fails, pass through original value
        print(f"MessagePack decode error for payload '{payload[:50]}...': {e}", file=sys.stderr)
        return payload


def process_line(line: str) -> str:
    """
    Process a single line of influx line protocol.

    Influx line protocol format:
    measurement,tag1=value1,tag2=value2 field1=value1,field2=value2 timestamp

    Example input line:
    mqtt_consumer,device_id=DEVICE123,topic=DEVICE123/from/message temperature=25.5,humidity=60.2 1234567890

    Args:
        line: A line in influx line protocol format

    Returns:
        Processed line in influx line protocol format
    """
    if not line.strip():
        return line

    try:
        # Parse the line (basic parsing - measurement, tags, fields, timestamp)
        parts = line.strip().split(' ')

        if len(parts) < 2:
            # Invalid format, pass through
            return line

        measurement_and_tags = parts[0]  # e.g., "mqtt_consumer,device_id=DEVICE123"
        fields = parts[1] if len(parts) > 1 else ""  # e.g., "temperature=25.5,humidity=60.2"
        timestamp = parts[2] if len(parts) > 2 else ""  # e.g., "1234567890"

        # ═══════════════════════════════════════════════════════════════════════
        # TODO: ADD YOUR DECODING LOGIC HERE
        # ═══════════════════════════════════════════════════════════════════════
        #
        # STEP 1: Parse the fields string into a dictionary
        # Example: "temperature=25.5,humidity=60.2" -> {"temperature": "25.5", "humidity": "60.2"}
        #
        # field_dict = {}
        # for field_pair in fields.split(','):
        #     if '=' in field_pair:
        #         key, value = field_pair.split('=', 1)
        #         field_dict[key] = value
        #
        # STEP 2: Decode each field value using your decoding function
        #
        # for key, encoded_value in field_dict.items():
        #     decoded_value = decode_payload(encoded_value)  # Call your decode function
        #     field_dict[key] = decoded_value
        #
        # STEP 3: Reconstruct the fields string with decoded values
        #
        # decoded_fields = ','.join(f"{k}={v}" for k, v in field_dict.items())
        #
        # STEP 4: Reconstruct the complete line
        #
        # decoded_line = f"{measurement_and_tags} {decoded_fields}"
        # if timestamp:
        #     decoded_line += f" {timestamp}"
        #
        # ═══════════════════════════════════════════════════════════════════════

        # For now, just pass through without modification
        decoded_line = line

        return decoded_line

    except Exception as e:
        # On error, log to stderr and pass through original
        print(f"Error processing line: {e}", file=sys.stderr)
        return line


def main():
    """Main loop: read from stdin, process, write to stdout."""
    try:
        for line in sys.stdin:
            processed = process_line(line)
            sys.stdout.write(processed)
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""MQTT publisher — sends device configuration to EMQX."""

import json
import logging

import paho.mqtt.client as mqtt

from app.config import settings

logger = logging.getLogger(__name__)


def encode_payload(payload: dict) -> dict:
    """
    Encode the payload before sending to MQTT.

    Currently just passes through the payload unchanged.

    Args:
        payload: The payload dictionary to encode

    Returns:
        Encoded payload dictionary

    ═══════════════════════════════════════════════════════════════════════
    TODO: ADD YOUR ENCODING LOGIC HERE
    ═══════════════════════════════════════════════════════════════════════
    Examples of what you might add:

    # Base64 encode specific fields:
    # import base64
    # for key, value in payload.items():
    #     if isinstance(value, (int, float)):
    #         value_str = str(value)
    #         encoded = base64.b64encode(value_str.encode()).decode()
    #         payload[key] = encoded

    # Hex encode numeric values:
    # for key, value in payload.items():
    #     if isinstance(value, int):
    #         payload[key] = hex(value)

    # Custom binary protocol encoding:
    # import struct
    # for key, value in payload.items():
    #     if isinstance(value, float):
    #         packed = struct.pack('<f', value)
    #         payload[key] = packed.hex()

    ═══════════════════════════════════════════════════════════════════════
    """
    # Placeholder: just return the input unchanged
    return payload


class MqttPublisher:
    def __init__(self, broker_host: str, broker_port: int) -> None:
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._client: mqtt.Client | None = None

    def _connect(self) -> mqtt.Client:
        if self._client is None:
            self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="iotdash-backend")
            try:
                self._client.connect(self._broker_host, self._broker_port, keepalive=60)
                self._client.loop_start()
                logger.info("Connected to MQTT broker %s:%s", self._broker_host, self._broker_port)
            except Exception:
                logger.exception("Failed to connect to MQTT broker")
                self._client = None
                raise
        return self._client

    def sync_device_metrics(
        self, device_code: str, metrics_state: dict[str, int]
    ) -> bool:
        """Send full metrics state to device.

        Args:
            device_code: The device UID.
            metrics_state: Dict of metric_name -> 1 (enabled) or 0 (disabled).
                           Includes ALL metrics the device type supports.
        """
        topic = f"iot/{device_code}/mo/cfg"

        # ═══════════════════════════════════════════════════════════════════════
        # Encode the payload before sending to MQTT
        # ═══════════════════════════════════════════════════════════════════════
        payload_dict = {"metrics": metrics_state}
        encoded_payload_dict = encode_payload(payload_dict)  # Apply encoding
        payload = json.dumps(encoded_payload_dict)

        try:
            client = self._connect()
            result = client.publish(topic, payload, qos=0)
            logger.info("Published config to %s: %s (rc=%s)", topic, payload, result.rc)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception:
            logger.exception("Failed to publish config to %s", topic)
            return False

    def disconnect(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None


_publisher: MqttPublisher | None = None


def get_mqtt_publisher() -> MqttPublisher:
    global _publisher
    if _publisher is None:
        _publisher = MqttPublisher(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT)
    return _publisher

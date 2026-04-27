"""MQTT publisher — sends device configuration to EMQX."""

import json
import logging
import base64

import msgpack
import paho.mqtt.client as mqtt

from app.config import settings

logger = logging.getLogger(__name__)


def encode_payload(payload: dict) -> bytes:
    """
    Encode the payload to MessagePack before sending to MQTT.

    Converts the payload dictionary to MessagePack binary format,
    then base64 encodes it for transport over MQTT.

    Args:
        payload: The payload dictionary to encode

    Returns:
        Base64-encoded MessagePack bytes (as string for MQTT transport)

    Example:
        >>> payload = {"metrics": {"temperature": 1, "humidity": 0}}
        >>> encoded = encode_payload(payload)
        >>> # Returns base64-encoded MessagePack binary
    """
    try:
        # Pack to MessagePack binary format
        msgpack_bytes = msgpack.packb(payload, use_bin_type=True)

        # Base64 encode for safe MQTT transport
        # Note: Some MQTT clients can send raw binary, but base64 is safer
        encoded = base64.b64encode(msgpack_bytes).decode('ascii')

        logger.debug(f"Encoded payload to MessagePack (base64): {encoded[:100]}...")
        return encoded

    except Exception as e:
        logger.exception(f"Failed to encode payload to MessagePack: {e}")
        # Fallback to JSON encoding
        return json.dumps(payload)


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
        # Encode the payload to MessagePack before sending to MQTT
        # ═══════════════════════════════════════════════════════════════════════
        payload_dict = {"metrics": metrics_state}
        payload = encode_payload(payload_dict)  # Returns base64-encoded MessagePack

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

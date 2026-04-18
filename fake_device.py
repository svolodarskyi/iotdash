#!/usr/bin/env python3
"""Fake IoT sensor — publishes metrics to EMQX, listens for config updates."""

import argparse
import json
import math
import random
import time

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
DEVICE_ID = "sensor01"


def generate_temperature(t: float) -> float:
    base = 22.0
    drift = 3.0 * math.sin(t / 60.0)
    noise = random.gauss(0, 0.3)
    return round(base + drift + noise, 2)


def generate_humidity(t: float) -> float:
    base = 55.0
    drift = 10.0 * math.sin(t / 90.0)
    noise = random.gauss(0, 1.5)
    return round(base + drift + noise, 2)


def generate_engine_rpm(t: float) -> float:
    base = 2500.0
    drift = 500.0 * math.sin(t / 45.0)
    noise = random.gauss(0, 25)
    return round(base + drift + noise, 2)


GENERATORS = {
    "temperature": generate_temperature,
    "humidity": generate_humidity,
    "engine_rpm": generate_engine_rpm,
}


def main():
    parser = argparse.ArgumentParser(description="Fake IoT device simulator")
    parser.add_argument("--device-id", default=DEVICE_ID, help="Device ID (default: sensor01)")
    parser.add_argument("--broker", default=BROKER, help="MQTT broker host")
    parser.add_argument("--port", type=int, default=PORT, help="MQTT broker port")
    parser.add_argument("--all-metrics", action="store_true", help="Start with all metrics enabled")
    args = parser.parse_args()

    device_id = args.device_id
    pub_topic = f"{device_id}/from/message"
    config_topic = f"{device_id}/to/config"

    # Start with temperature by default, or all metrics if --all-metrics
    enabled_metrics: set[str] = set(GENERATORS.keys()) if args.all_metrics else {"temperature"}

    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"Connected to {args.broker}:{args.port}")
        client.subscribe(config_topic)
        print(f"Subscribed to {config_topic}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if "metrics" in payload:
                metrics_state = payload["metrics"]
                enabled_metrics.clear()
                for name, flag in metrics_state.items():
                    if flag == 1 and name in GENERATORS:
                        enabled_metrics.add(name)
                enabled = [n for n, f in metrics_state.items() if f == 1]
                disabled = [n for n, f in metrics_state.items() if f == 0]
                print(f"  CONFIG received: enabled={enabled} disabled={disabled}  (active: {sorted(enabled_metrics)})")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  CONFIG error: {e}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=device_id)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.broker, args.port, keepalive=60)
    client.loop_start()

    print(f"Publishing to {pub_topic} every 1s  (Ctrl+C to stop)")
    print(f"  Initial metrics: {sorted(enabled_metrics)}")
    start = time.time()

    try:
        while True:
            t = time.time() - start
            payload = {}
            for metric in sorted(enabled_metrics):
                if metric in GENERATORS:
                    payload[metric] = GENERATORS[metric](t)
            data = json.dumps(payload)
            client.publish(pub_topic, data, qos=0)
            print(f"  {pub_topic}  →  {data}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

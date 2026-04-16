#!/usr/bin/env python3
"""Fake IoT temperature sensor — publishes to EMQX every second."""

import json
import math
import random
import time

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
DEVICE_ID = "sensor01"
TOPIC = f"{DEVICE_ID}/from/message"

def generate_temperature(t: float) -> float:
    """Simulate realistic temperature: base ~22C with slow sine drift + noise."""
    base = 22.0
    drift = 3.0 * math.sin(t / 60.0)  # slow oscillation over ~6 min
    noise = random.gauss(0, 0.3)
    return round(base + drift + noise, 2)

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=DEVICE_ID)
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    print(f"Publishing temperature to {TOPIC} every 1s  (Ctrl+C to stop)")
    start = time.time()

    try:
        while True:
            t = time.time() - start
            temp = generate_temperature(t)
            payload = json.dumps({"temperature": temp})
            client.publish(TOPIC, payload, qos=0)
            print(f"  {TOPIC}  →  {payload}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()

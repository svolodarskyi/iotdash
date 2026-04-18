#!/usr/bin/env python3
"""
Async IoT device simulator for soak testing.

Simulates N devices publishing sensor metrics over MQTT at a configurable
interval. Designed for 1000 devices @ 5s (~200 msg/s sustained).

Usage:
    python soak_simulator.py --devices 1000 --interval 5 --broker localhost
    python soak_simulator.py --devices 10 --interval 5 --broker localhost  # local test
"""

import argparse
import asyncio
import json
import logging
import math
import os
import random
import signal
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

try:
    import aiomqtt
except ImportError:
    print("ERROR: aiomqtt is required. Install with: pip install aiomqtt")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("soak-simulator")


# ── Metric generators (match fake_device.py schema) ────────────────────────

def generate_temperature(t: float) -> float:
    """Temperature in Celsius — 22 base, slow drift, small noise."""
    drift = 3 * math.sin(t / 300)
    noise = random.gauss(0, 0.3)
    return round(22 + drift + noise, 2)


def generate_humidity(t: float) -> float:
    """Humidity percentage — 55 base, drift, noise."""
    drift = 10 * math.sin(t / 600)
    noise = random.gauss(0, 1.5)
    return round(max(0, min(100, 55 + drift + noise)), 2)


def generate_engine_rpm(t: float) -> float:
    """Engine RPM — 2500 base, drift, noise."""
    drift = 500 * math.sin(t / 200)
    noise = random.gauss(0, 25)
    return round(max(0, 2500 + drift + noise), 1)


def generate_battery(t: float) -> float:
    """Battery voltage — slow drain from 12.6V with noise."""
    drain = 0.001 * (t / 60)  # very slow drain
    noise = random.gauss(0, 0.05)
    return round(max(10.0, 12.6 - drain + noise), 2)


GENERATORS = {
    "temperature": generate_temperature,
    "humidity": generate_humidity,
    "engine_rpm": generate_engine_rpm,
    "battery": generate_battery,
}


# ── Stats tracking ─────────────────────────────────────────────────────────

@dataclass
class Stats:
    messages_sent: int = 0
    errors: int = 0
    reconnects: int = 0
    connected_devices: int = 0
    start_time: float = field(default_factory=time.time)

    def msg_rate(self) -> float:
        elapsed = time.time() - self.start_time
        return self.messages_sent / elapsed if elapsed > 0 else 0


stats = Stats()
shutdown_event = asyncio.Event()


# ── Single device coroutine ────────────────────────────────────────────────

async def run_device(
    device_id: str,
    broker: str,
    port: int,
    interval: float,
    start_delay: float,
):
    """Run a single simulated device with reconnect logic."""
    await asyncio.sleep(start_delay)

    if shutdown_event.is_set():
        return

    topic = f"{device_id}/from/message"
    backoff = 1
    max_backoff = 60
    t_offset = random.uniform(0, 1000)  # unique phase per device

    while not shutdown_event.is_set():
        try:
            async with aiomqtt.Client(
                broker,
                port=port,
                identifier=device_id,
                keepalive=30,
            ) as client:
                stats.connected_devices += 1
                backoff = 1  # reset on successful connect
                log.debug("Device %s connected", device_id)

                while not shutdown_event.is_set():
                    t = time.time() + t_offset

                    # Build payload matching existing schema
                    payload = {
                        name: gen(t)
                        for name, gen in GENERATORS.items()
                    }

                    # 5% chance of a status message
                    if random.random() < 0.05:
                        payload["status"] = random.choice([
                            "nominal", "warning", "maintenance_due",
                        ])

                    # 1% chance of an error condition
                    if random.random() < 0.01:
                        payload["error"] = random.choice([
                            "sensor_timeout", "calibration_drift",
                            "low_signal", "overtemp",
                        ])

                    await client.publish(
                        topic,
                        json.dumps(payload),
                        qos=0,
                    )
                    stats.messages_sent += 1

                    # Wait for next publish cycle (or early exit on shutdown)
                    try:
                        await asyncio.wait_for(
                            shutdown_event.wait(),
                            timeout=interval,
                        )
                        # If we get here, shutdown was requested
                        break
                    except asyncio.TimeoutError:
                        pass  # Normal — interval elapsed, publish again

        except aiomqtt.MqttError as e:
            stats.connected_devices = max(0, stats.connected_devices - 1)
            stats.reconnects += 1
            if not shutdown_event.is_set():
                log.warning(
                    "Device %s disconnected (%s), retrying in %ds",
                    device_id, e, backoff,
                )
                try:
                    await asyncio.wait_for(
                        shutdown_event.wait(), timeout=backoff,
                    )
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, max_backoff)
        except Exception as e:
            stats.errors += 1
            stats.connected_devices = max(0, stats.connected_devices - 1)
            log.error("Device %s unexpected error: %s", device_id, e)
            try:
                await asyncio.wait_for(
                    shutdown_event.wait(), timeout=backoff,
                )
            except asyncio.TimeoutError:
                pass
            backoff = min(backoff * 2, max_backoff)


# ── Stats printer ──────────────────────────────────────────────────────────

async def print_stats(interval: int = 60):
    """Print live stats every `interval` seconds."""
    while not shutdown_event.is_set():
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
        if shutdown_event.is_set():
            break
        elapsed = time.time() - stats.start_time
        log.info(
            "STATS | connected=%d | sent=%d | rate=%.1f msg/s | "
            "errors=%d | reconnects=%d | uptime=%.0fs",
            stats.connected_devices,
            stats.messages_sent,
            stats.msg_rate(),
            stats.errors,
            stats.reconnects,
            elapsed,
        )


# ── Main ───────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(
        description="IoTDash soak test device simulator",
    )
    parser.add_argument(
        "--devices", type=int, default=1000,
        help="Number of devices to simulate (default: 1000)",
    )
    parser.add_argument(
        "--interval", type=float, default=5.0,
        help="Publish interval in seconds (default: 5)",
    )
    parser.add_argument(
        "--broker", type=str, default="localhost",
        help="MQTT broker hostname (default: localhost)",
    )
    parser.add_argument(
        "--port", type=int, default=1883,
        help="MQTT broker port (default: 1883)",
    )
    parser.add_argument(
        "--ramp-rate", type=float, default=5.0,
        help="Devices to connect per second during ramp-up (default: 5)",
    )
    parser.add_argument(
        "--prefix", type=str, default="soak",
        help="Device ID prefix (default: soak)",
    )
    args = parser.parse_args()

    ramp_delay = 1.0 / args.ramp_rate  # seconds between each device start
    total_ramp = args.devices * ramp_delay

    log.info(
        "Starting soak simulator: %d devices @ %.1fs interval, "
        "broker=%s:%d, ramp=%.0fs (%.0f devices/sec)",
        args.devices, args.interval, args.broker, args.port,
        total_ramp, args.ramp_rate,
    )

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_event.set)

    # Launch all device tasks with staggered start
    tasks = []
    for i in range(args.devices):
        device_id = f"{args.prefix}-device-{i:04d}"
        delay = i * ramp_delay
        task = asyncio.create_task(
            run_device(device_id, args.broker, args.port, args.interval, delay),
            name=device_id,
        )
        tasks.append(task)

    # Stats printer
    tasks.append(asyncio.create_task(print_stats(60), name="stats-printer"))

    log.info("All %d device tasks queued. Ramping up over %.0fs...", args.devices, total_ramp)

    # Wait for shutdown
    await shutdown_event.wait()

    log.info("Shutdown requested. Waiting for devices to disconnect...")

    # Give devices a moment to finish their current cycle
    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

    # Final stats
    elapsed = time.time() - stats.start_time
    log.info(
        "FINAL STATS | total_sent=%d | avg_rate=%.1f msg/s | "
        "errors=%d | reconnects=%d | uptime=%.0fs",
        stats.messages_sent,
        stats.msg_rate(),
        stats.errors,
        stats.reconnects,
        elapsed,
    )


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
import os, time, json, random
import paho.mqtt.client as mqtt
import requests
from prometheus_client import start_http_server, Gauge, Histogram

# --- Configuration ---
MQTT_URL = os.getenv("MQTT_URL", "mqtt://localhost:1883")
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")
WORKER_ID = os.getenv("WORKER_ID", "zenith-worker")
LISTEN_PORT = int(os.getenv("LISTEN_PORT", "9100"))
SOURCE_TYPE = os.getenv("SOURCE_TYPE", "sensor")  # sensor, api, file

# Prometheus metrics
telemetry_value = Gauge("telemetry_value", "Telemetry values emitted")
telemetry_status = Gauge("telemetry_status", "Worker status indicator")
latency_histogram = Histogram("telemetry_latency_seconds", "Latency distribution of telemetry emission")

# --- MQTT Setup ---
def parse_mqtt_url(url):
    parts = url.replace("mqtt://","").split(":")
    return parts[0], int(parts[1]) if len(parts) > 1 else 1883

host, port = parse_mqtt_url(MQTT_URL)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=WORKER_ID)
if MQTT_USER and MQTT_PASS:
    client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(host, port, 60)

# --- Ingestion Sources ---
def ingest_sensor_json(path="sensor.json"):
    try:
        with open(path) as f:
            data = json.load(f)
        return {"value": data.get("value", 0), "status": data.get("status","ok")}
    except Exception:
        return {"value": random.uniform(0,100), "status":"fallback"}

def ingest_api(url="https://api.example.com/telemetry"):
    try:
        r = requests.get(url, timeout=2)
        data = r.json()
        return {"value": data.get("value", 0), "status": data.get("status","ok")}
    except Exception:
        return {"value": random.uniform(0,100), "status":"fallback"}

def ingest_file_stream(path="telemetry.log"):
    try:
        with open(path) as f:
            line = f.readlines()[-1]
            parts = line.strip().split(",")
            return {"value": float(parts[0]), "status": parts[1]}
    except Exception:
        return {"value": random.uniform(0,100), "status":"fallback"}

def select_source():
    if SOURCE_TYPE == "api":
        return ingest_api()
    elif SOURCE_TYPE == "file":
        return ingest_file_stream()
    else:
        return ingest_sensor_json()

# --- Telemetry Loop ---
def main():
    start_http_server(LISTEN_PORT)
    print(f"[+] {WORKER_ID} started. Publishing telemetry to MQTT and Prometheus on port {LISTEN_PORT}.")

    while True:
        start = time.time()
        data = select_source()
        payload = {
            "worker": WORKER_ID,
            "timestamp": time.time(),
            "value": data["value"],
            "status": data["status"]
        }
        msg = json.dumps(payload)

        # Partitioned topics
        client.publish(f"telemetry/{WORKER_ID}/value", str(data["value"]))
        client.publish(f"telemetry/{WORKER_ID}/status", data["status"])
        client.publish(f"telemetry/{WORKER_ID}/json", msg)

        # Prometheus metrics
        telemetry_value.set(data["value"])
        telemetry_status.set(1 if data["status"]=="ok" else 0)
        latency_histogram.observe(time.time() - start)

        print(f"[+] Published: {msg}")
        time.sleep(5)

if __name__ == "__main__":
    main()

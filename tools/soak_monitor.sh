#!/usr/bin/env bash
# Soak test metrics collector — runs every 5 min via cron
# Appends a row to /opt/iotdash/soak-metrics.csv with system and container stats
#
# Crontab entry:
#   */5 * * * * /opt/iotdash/tools/soak_monitor.sh >> /opt/iotdash/soak-monitor.log 2>&1

set -euo pipefail

CSV_FILE="${SOAK_METRICS_FILE:-/opt/iotdash/soak-metrics.csv}"

# Write CSV header if file doesn't exist
if [[ ! -f "$CSV_FILE" ]]; then
  echo "timestamp,cpu_pct,ram_used_mb,ram_total_mb,disk_used_gb,disk_total_gb,emqx_mem_mb,influxdb_mem_mb,telegraf_mem_mb,backend_mem_mb,postgres_mem_mb,grafana_mem_mb,emqx_connections,emqx_msg_rate,influxdb_disk_mb,docker_restarts_emqx,docker_restarts_influxdb,docker_restarts_telegraf,docker_restarts_backend,docker_restarts_postgres,docker_restarts_grafana" > "$CSV_FILE"
fi

# ── System metrics ──────────────────────────────────────────────────────────

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# CPU usage (1-second sample)
CPU_PCT=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' 2>/dev/null || echo "0")

# RAM
RAM_USED_MB=$(free -m | awk '/^Mem:/ {print $3}')
RAM_TOTAL_MB=$(free -m | awk '/^Mem:/ {print $2}')

# Disk (root partition)
DISK_USED_GB=$(df -BG / | awk 'NR==2 {gsub("G",""); print $3}')
DISK_TOTAL_GB=$(df -BG / | awk 'NR==2 {gsub("G",""); print $2}')

# ── Per-container memory (MB) ──────────────────────────────────────────────

get_container_mem_mb() {
  local name=$1
  local mem_bytes
  mem_bytes=$(docker stats --no-stream --format "{{.MemUsage}}" "$name" 2>/dev/null | awk '{print $1}' || echo "0")
  # Convert to MB — handles MiB, GiB, KiB suffixes
  if echo "$mem_bytes" | grep -qi "gib\|gb"; then
    echo "$mem_bytes" | sed 's/[^0-9.]//g' | awk '{printf "%.0f", $1 * 1024}'
  elif echo "$mem_bytes" | grep -qi "mib\|mb"; then
    echo "$mem_bytes" | sed 's/[^0-9.]//g' | awk '{printf "%.0f", $1}'
  elif echo "$mem_bytes" | grep -qi "kib\|kb"; then
    echo "$mem_bytes" | sed 's/[^0-9.]//g' | awk '{printf "%.0f", $1 / 1024}'
  else
    echo "0"
  fi
}

EMQX_MEM=$(get_container_mem_mb emqx)
INFLUXDB_MEM=$(get_container_mem_mb influxdb)
TELEGRAF_MEM=$(get_container_mem_mb telegraf)
BACKEND_MEM=$(get_container_mem_mb backend)
POSTGRES_MEM=$(get_container_mem_mb postgres)
GRAFANA_MEM=$(get_container_mem_mb grafana)

# ── EMQX stats (via REST API) ──────────────────────────────────────────────

EMQX_CONNECTIONS=0
EMQX_MSG_RATE=0

EMQX_STATS=$(curl -sf -u admin:public "http://localhost:18083/api/v5/stats" 2>/dev/null || echo "{}")

if [[ "$EMQX_STATS" != "{}" ]]; then
  EMQX_CONNECTIONS=$(echo "$EMQX_STATS" | jq -r '.[0].connections // 0' 2>/dev/null || echo "0")
  EMQX_MSG_RATE=$(echo "$EMQX_STATS" | jq -r '.[0]."messages.received.rate" // 0' 2>/dev/null || echo "0")
fi

# ── InfluxDB disk usage ────────────────────────────────────────────────────

INFLUXDB_DISK_MB=$(docker exec influxdb du -sm /var/lib/influxdb2 2>/dev/null | awk '{print $1}' || echo "0")

# ── Docker restart counts ──────────────────────────────────────────────────

get_restart_count() {
  docker inspect --format='{{.RestartCount}}' "$1" 2>/dev/null || echo "0"
}

RESTARTS_EMQX=$(get_restart_count emqx)
RESTARTS_INFLUXDB=$(get_restart_count influxdb)
RESTARTS_TELEGRAF=$(get_restart_count telegraf)
RESTARTS_BACKEND=$(get_restart_count backend)
RESTARTS_POSTGRES=$(get_restart_count postgres)
RESTARTS_GRAFANA=$(get_restart_count grafana)

# ── Write CSV row ──────────────────────────────────────────────────────────

echo "${TIMESTAMP},${CPU_PCT},${RAM_USED_MB},${RAM_TOTAL_MB},${DISK_USED_GB},${DISK_TOTAL_GB},${EMQX_MEM},${INFLUXDB_MEM},${TELEGRAF_MEM},${BACKEND_MEM},${POSTGRES_MEM},${GRAFANA_MEM},${EMQX_CONNECTIONS},${EMQX_MSG_RATE},${INFLUXDB_DISK_MB},${RESTARTS_EMQX},${RESTARTS_INFLUXDB},${RESTARTS_TELEGRAF},${RESTARTS_BACKEND},${RESTARTS_POSTGRES},${RESTARTS_GRAFANA}" >> "$CSV_FILE"

echo "[$(date)] Metrics collected successfully"

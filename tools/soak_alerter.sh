#!/usr/bin/env bash
# Soak test alerter — runs every 15 min via cron
# Checks for failure conditions and sends webhook alerts
#
# Crontab entry:
#   */15 * * * * ALERT_WEBHOOK_URL="https://..." /opt/iotdash/tools/soak_alerter.sh >> /opt/iotdash/soak-alerter.log 2>&1
#
# Supports: Slack webhooks, ntfy.sh, or any endpoint accepting POST with text body.

set -euo pipefail

WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"
HOSTNAME=$(hostname)
ALERT_PREFIX="[iotdash-soak@${HOSTNAME}]"

# Minimum expected EMQX connections (alert if below this)
MIN_CONNECTIONS="${SOAK_MIN_CONNECTIONS:-500}"

alerts=()

# ── Check: container restarts (crash loops) ────────────────────────────────

check_restarts() {
  local name=$1
  local count
  count=$(docker inspect --format='{{.RestartCount}}' "$name" 2>/dev/null || echo "0")
  if [[ "$count" -gt 0 ]]; then
    alerts+=("Container '$name' has restarted $count time(s)")
  fi
}

for svc in emqx influxdb telegraf backend postgres grafana; do
  check_restarts "$svc"
done

# ── Check: container running status ────────────────────────────────────────

check_running() {
  local name=$1
  local status
  status=$(docker inspect --format='{{.State.Status}}' "$name" 2>/dev/null || echo "missing")
  if [[ "$status" != "running" ]]; then
    alerts+=("Container '$name' is NOT running (status: $status)")
  fi
}

for svc in emqx influxdb telegraf backend postgres grafana; do
  check_running "$svc"
done

# ── Check: disk usage > 80% ───────────────────────────────────────────────

DISK_PCT=$(df / | awk 'NR==2 {gsub("%",""); print $5}')
if [[ "$DISK_PCT" -gt 80 ]]; then
  alerts+=("Disk usage is at ${DISK_PCT}% (threshold: 80%)")
fi

# ── Check: RAM usage > 90% ────────────────────────────────────────────────

RAM_TOTAL=$(free -m | awk '/^Mem:/ {print $2}')
RAM_USED=$(free -m | awk '/^Mem:/ {print $3}')
RAM_PCT=$((RAM_USED * 100 / RAM_TOTAL))
if [[ "$RAM_PCT" -gt 90 ]]; then
  alerts+=("RAM usage is at ${RAM_PCT}% (${RAM_USED}/${RAM_TOTAL} MB)")
fi

# ── Check: EMQX connections dropped ───────────────────────────────────────

EMQX_STATS=$(curl -sf -u admin:public "http://localhost:18083/api/v5/stats" 2>/dev/null || echo "[]")
EMQX_CONNS=$(echo "$EMQX_STATS" | jq -r '.[0].connections // 0' 2>/dev/null || echo "0")

if [[ "$EMQX_CONNS" -lt "$MIN_CONNECTIONS" ]]; then
  alerts+=("EMQX connections dropped to $EMQX_CONNS (expected >= $MIN_CONNECTIONS)")
fi

# ── Check: InfluxDB health ─────────────────────────────────────────────────

INFLUX_HEALTH=$(curl -sf "http://localhost:8086/health" 2>/dev/null || echo '{"status":"fail"}')
INFLUX_STATUS=$(echo "$INFLUX_HEALTH" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")

if [[ "$INFLUX_STATUS" != "pass" ]]; then
  alerts+=("InfluxDB health check: $INFLUX_STATUS")
fi

# ── Send alerts ────────────────────────────────────────────────────────────

if [[ ${#alerts[@]} -eq 0 ]]; then
  echo "[$(date)] All checks passed"
  exit 0
fi

# Build alert message
MESSAGE="${ALERT_PREFIX} $(date -u +"%Y-%m-%dT%H:%M:%SZ")"$'\n'
for alert in "${alerts[@]}"; do
  MESSAGE+="  - ${alert}"$'\n'
  echo "[$(date)] ALERT: ${alert}"
done

if [[ -n "$WEBHOOK_URL" ]]; then
  # Detect webhook type and format accordingly
  if echo "$WEBHOOK_URL" | grep -q "hooks.slack.com"; then
    # Slack webhook
    PAYLOAD=$(jq -n --arg text "$MESSAGE" '{"text": $text}')
    curl -sf -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$WEBHOOK_URL" || true
  else
    # Generic webhook (ntfy.sh, etc.)
    curl -sf -X POST -d "$MESSAGE" "$WEBHOOK_URL" || true
  fi
  echo "[$(date)] Alert sent to webhook"
else
  echo "[$(date)] No ALERT_WEBHOOK_URL configured — alerts logged only"
fi

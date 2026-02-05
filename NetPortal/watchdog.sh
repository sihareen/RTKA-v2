#!/usr/bin/env bash
set -u

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/portal.log"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"

mkdir -p "$LOG_DIR"

echo "$(date '+%F %T') [watchdog] starting wifi_manager watchdog" >> "$LOG_FILE"

while true; do
  echo "$(date '+%F %T') [watchdog] launching wifi_manager.py" >> "$LOG_FILE"
  "$PYTHON_BIN" "$BASE_DIR/wifi_manager.py" >> "$LOG_FILE" 2>&1
  rc=$?
  echo "$(date '+%F %T') [watchdog] wifi_manager exited rc=$rc, restarting in 3s" >> "$LOG_FILE"
  sleep 3
done

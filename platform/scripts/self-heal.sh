#!/bin/bash
# Ligerwave Self-Healing Script — runs every 5 minutes via cron
# Zero cost, keeps the site up without human intervention

set -e

HOME_DIR="/home/ubuntu/ligerwave-platform"
PLATFORM_DIR="$HOME_DIR/platform"
LOG_FILE="$HOME_DIR/heal.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if API container is running
if ! docker ps --format '{{.Names}}' | grep -q 'ligerwave-api'; then
  log "WARNING: ligerwave-api container is not running. Attempting restart..."
  
  # Check if container exists but is stopped
  if docker ps -a --format '{{.Names}}' | grep -q 'ligerwave-api'; then
    log "Container exists but stopped. Removing and recreating..."
    docker rm -f ligerwave-api 2>/dev/null || true
  fi
  
  # Try to restart
  cd "$PLATFORM_DIR" && docker compose up -d 2>&1 >> "$LOG_FILE"
  
  sleep 5
  
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    log "HEALED: API is back online"
  else
    log "FAILED: API still down after restart attempt"
    # Try rebuilding
    log "Attempting rebuild..."
    cd "$PLATFORM_DIR" && docker compose build api 2>&1 >> "$LOG_FILE"
    cd "$PLATFORM_DIR" && docker compose up -d 2>&1 >> "$LOG_FILE"
    sleep 5
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
      log "HEALED via rebuild: API is back online"
    else
      log "CRITICAL: API still down after rebuild. Manual intervention required."
    fi
  fi
fi

# Check if Nginx container is running
if ! docker ps --format '{{.Names}}' | grep -q 'ligerwave-nginx'; then
  log "WARNING: ligerwave-nginx container is not running. Restarting..."
  cd "$PLATFORM_DIR" && docker compose up -d 2>&1 >> "$LOG_FILE"
  log "Nginx restart attempted"
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
  log "WARNING: Disk usage at ${DISK_USAGE}%. Cleaning up..."
  docker system prune -f 2>&1 >> "$LOG_FILE"
  docker builder prune -f 2>&1 >> "$LOG_FILE"
  log "Cleanup complete. Usage now: $(df / | tail -1 | awk '{print $5}')"
fi

# Keep last 7 days of logs
find "$HOME_DIR" -name "heal.log" -size +1M -exec sh -c 'tail -c 100000 "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;

log "Health check complete"

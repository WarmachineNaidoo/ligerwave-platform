#!/bin/bash
# Ligerwave Rollback Script
# Usage: ./rollback.sh          → revert to previous commit
# Usage: ./rollback.sh <commit> → revert to specific commit

set -e
HOME_DIR="/home/ubuntu/ligerwave-platform"
PLATFORM_DIR="$HOME_DIR/platform"

if [ $# -eq 0 ]; then
  echo "Reverting to previous commit..."
  cd "$HOME_DIR"
  COMMIT=$(git rev-parse HEAD~1)
  echo "Target: $COMMIT ($(git log --oneline -1 HEAD~1))"
  read -p "Continue? (y/N): " confirm
  if [ "$confirm" != "y" ]; then echo "Cancelled"; exit 1; fi
  git reset --hard HEAD~1
elif [ $# -eq 1 ]; then
  echo "Reverting to: $1"
  cd "$HOME_DIR"
  if ! git cat-file -t "$1" > /dev/null 2>&1; then
    echo "Invalid commit: $1"
    exit 1
  fi
  git reset --hard "$1"
else
  echo "Usage: $0 [commit-hash]"
  exit 1
fi

echo "Code reverted. Rebuilding..."
cd "$PLATFORM_DIR"
docker compose build api 2>&1 | tail -3
docker compose up -d 2>&1

sleep 3
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo "✅ Rollback successful. API is healthy."
else
  echo "❌ Rollback failed. Manual intervention required."
  exit 1
fi

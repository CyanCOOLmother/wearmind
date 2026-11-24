#!/usr/bin/env bash
set -euo pipefail
edge_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$edge_root"
export WEARMIND_DATA="${WEARMIND_DATA:-$edge_root/data}"
export WEARMIND_PORT="${WEARMIND_PORT:-8780}"
export TZ="${TZ:-Asia/Shanghai}"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -m app.main

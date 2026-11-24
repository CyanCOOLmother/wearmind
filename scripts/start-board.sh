#!/usr/bin/env bash
# 开发板专用入口：与旧版 8780 / 8781 分开，默认使用 8790。
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
export WEARMIND_PORT="${WEARMIND_PORT:-8790}"
exec bash "$script_dir/start-edge.sh"

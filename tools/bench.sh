#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEED=42
DURATION=30
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --seed)
      SEED="${2:-42}"
      shift 2
      ;;
    --duration)
      DURATION="${2:-30}"
      shift 2
      ;;
    --out)
      OUT="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$OUT" ]]; then
  echo "Usage: $0 --seed <int> --duration <sec> --out <bench.json>" >&2
  exit 2
fi

if [[ "$OUT" != /* && ! "$OUT" =~ ^[A-Za-z]: ]]; then
  OUT="$(pwd)/$OUT"
fi

GODOT_BIN="${GODOT_BIN:-$(command -v godot || command -v godot4 || true)}"
if [[ -z "$GODOT_BIN" ]]; then
  echo "Error: godot binary not found on PATH (set GODOT_BIN)" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
exec "$GODOT_BIN" --path "$ROOT_DIR/godot" --resolution 1280x720 --windowed res://scenes/Bench.tscn -- --seed "$SEED" --duration "$DURATION" --out "$OUT"

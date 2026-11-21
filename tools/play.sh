#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
launch_dir="$PWD"
for arg in "$@"; do
    if [[ "$arg" == --export-leaderboard || "$arg" == --export-leaderboard=* ]]; then
        PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m chonoi.live "$@"
    fi
done

cd "$root"
engine="${GODOT_BIN:-$(command -v godot || command -v godot4 || true)}"
if [[ -z "$engine" ]]; then
    echo "Cần Godot Standard trên PATH hoặc biến GODOT_BIN." >&2
    exit 1
fi
"$engine" --headless --editor --path "$root/godot" --import

server_log="$(mktemp "${TMPDIR:-/tmp}/chonoi-live.XXXXXXXX")"
server_pid=""
cleanup() {
    if [[ -n "$server_pid" ]]; then
        kill "$server_pid" 2>/dev/null || true
        wait "$server_pid" 2>/dev/null || true
    fi
    rm -f "$server_log"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cd "$launch_dir"
PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}" python3 -u -m chonoi.live --presentation "$@" --port 0 --host 127.0.0.1 >"$server_log" 2>&1 &
server_pid="$!"
for ((attempt = 0; attempt < 100; attempt++)); do
    server_url="$(sed -n 's|.*\(http://127\.0\.0\.1:[0-9][0-9]*\)/.*|\1|p' "$server_log")"
    if [[ -n "$server_url" ]]; then
        CHONOI_SERVER_URL="$server_url" "$engine" --path "$root/godot"
        exit
    fi
    if ! kill -0 "$server_pid" 2>/dev/null; then
        break
    fi
    sleep 0.05
done
cat "$server_log" >&2
exit 1

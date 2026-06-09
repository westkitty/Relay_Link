#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT_DIR/android"
LOG_DIR="$HOME/Library/Logs"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENT_DIR/com.westkitty.relaylink.plist"
TOKEN="${RELAY_LINK_TOKEN:-relay-link-local}"
MAC_WIDTH="${RELAY_LINK_MAC_WIDTH:-1440}"
MAC_HEIGHT="${RELAY_LINK_MAC_HEIGHT:-900}"
MAC_IP="${RELAY_LINK_MAC_IP:-}"
SKIP_ANDROID="${RELAY_LINK_SKIP_ANDROID:-0}"

daemon_is_listening() {
  lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -Fq "$MAC_IP:8765"
}

if [[ -z "$MAC_IP" ]]; then
  MAC_IP="$(ipconfig getifaddr en0 2>/dev/null || true)"
fi
if [[ -z "$MAC_IP" ]]; then
  MAC_IP="$(ipconfig getifaddr en1 2>/dev/null || true)"
fi
if [[ -z "$MAC_IP" ]]; then
  echo "Could not detect Mac LAN IP. Set RELAY_LINK_MAC_IP and rerun." >&2
  exit 1
fi

cd "$ROOT_DIR"
if [[ ! -x ".venv/bin/python" ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -e ".[dev]" >/tmp/relay-link-one-shot-pip.log

mkdir -p "$LOG_DIR"
mkdir -p "$LAUNCH_AGENT_DIR"
if ! daemon_is_listening; then
  cat >"$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.westkitty.relaylink</string>
  <key>ProgramArguments</key>
  <array>
    <string>$ROOT_DIR/.venv/bin/python</string>
    <string>-m</string>
    <string>relay_link.daemon</string>
    <string>--host</string>
    <string>$MAC_IP</string>
    <string>--port</string>
    <string>8765</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>RELAY_LINK_TOKEN</key>
    <string>$TOKEN</string>
  </dict>
  <key>WorkingDirectory</key>
  <string>$ROOT_DIR</string>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/relay-link.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/relay-link.log</string>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
PLIST
  launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
  launchctl kickstart -k "gui/$(id -u)/com.westkitty.relaylink"
  sleep 2
fi
if ! daemon_is_listening; then
  echo "Mac daemon did not bind port 8765. See $LOG_DIR/relay-link.log." >&2
  exit 1
fi

if [[ "$SKIP_ANDROID" == "1" ]]; then
  echo "Relay Link Mac daemon launched."
  echo "Mac WebSocket: ws://$MAC_IP:8765"
  exit 0
fi

if ! adb get-state >/dev/null 2>&1; then
  echo "No Android device detected by adb. Connect USB, enable USB debugging, and rerun." >&2
  exit 1
fi

cd "$ANDROID_DIR"
if [[ ! -x "./gradlew" ]]; then
  gradle wrapper --gradle-version 9.5.1
fi

./gradlew installDebug
adb shell am start \
  -n com.westkitty.relaylink/.MainActivity \
  --es host "$MAC_IP" \
  --es token "$TOKEN" \
  --ei mac_width "$MAC_WIDTH" \
  --ei mac_height "$MAC_HEIGHT" \
  --ez autostart true
sleep 2
if ! daemon_is_listening; then
  echo "Mac daemon stopped after Android launch. See $LOG_DIR/relay-link.log." >&2
  exit 1
fi

echo "Relay Link Android installed and launched."
echo "Mac WebSocket: ws://$MAC_IP:8765"
echo "Token: $TOKEN"

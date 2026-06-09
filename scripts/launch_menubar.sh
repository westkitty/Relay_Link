#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$HOME/Library/Logs"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENT_DIR/com.westkitty.relaylink.menubar.plist"

cd "$ROOT_DIR"
if [[ ! -x ".venv/bin/python" ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -e ".[macos,dev]" >/tmp/relay-link-menubar-pip.log

mkdir -p "$LOG_DIR"
mkdir -p "$LAUNCH_AGENT_DIR"
cat >"$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.westkitty.relaylink.menubar</string>
  <key>ProgramArguments</key>
  <array>
    <string>$ROOT_DIR/.venv/bin/python</string>
    <string>-m</string>
    <string>relay_link.menubar</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>RELAY_LINK_ROOT</key>
    <string>$ROOT_DIR</string>
  </dict>
  <key>WorkingDirectory</key>
  <string>$ROOT_DIR</string>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/relay-link-menubar.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/relay-link-menubar.log</string>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/com.westkitty.relaylink.menubar"

echo "Relay Link menu bar controller launched."
echo "Logs: $LOG_DIR/relay-link-menubar.log"

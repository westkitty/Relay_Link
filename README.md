# Relay Link

Relay Link is a local macOS host daemon for Android tablet handoff over a standard WebSocket relay on port `8765`.

It supports:

- Bidirectional clipboard messages for text and PNG image data URLs.
- Pointer coordinate packets routed into macOS through Quartz Event Services.
- A bounded buffered sync queue for inspecting inbound clipboard writes before release.
- A small macOS menu bar controller for starting the daemon and opening logs.
- A native Android starter app with one-command install and launch.

## Status

This repository contains the macOS host side. The Android client should connect to:

```text
ws://<mac-lan-ip>:8765
```

Use a shared token with `RELAY_LINK_TOKEN` when running on an untrusted network. Binding to `0.0.0.0` is convenient on a local area network (LAN), but it exposes the daemon to every reachable device on that network. Tiny detail. Rather important.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[macos,dev]"
```

For text-only development on non-macOS hosts:

```bash
pip install -e ".[dev]"
```

## Run The Daemon

```bash
relay-link-daemon
```

If a local editable install leaves the console script stale, use the module entrypoint:

```bash
python -m relay_link.daemon
```

Defaults:

- Host: `0.0.0.0`
- Port: `8765`
- Clipboard poll interval: `0.35` seconds
- Queue mode: auto-release enabled

Manual queue inspection mode:

```bash
relay-link-daemon --manual-release
```

Token mode:

```bash
RELAY_LINK_TOKEN="change-this" relay-link-daemon
```

The Android client should send a hello packet after connecting:

```json
{"type":"hello","role":"tablet","token":"change-this"}
```

## Message Protocol

Outbound macOS text clipboard:

```json
{"type":"clipboard","format":"text","sender":"mac","content":"copied text"}
```

Outbound macOS image clipboard:

```json
{"type":"clipboard","format":"image","sender":"mac","content":"data:image/png;base64,..."}
```

Inbound Android clipboard:

```json
{"type":"clipboard","format":"text","sender":"tablet","content":"tablet text"}
```

Pointer routing:

```json
{"type":"pointer","x":1200,"y":500,"action":"move","button":"left"}
```

Supported pointer actions are `move`, `down`, and `up`.

Queue inspection:

```json
{"type":"queue:list"}
{"type":"queue:release","id":"<update-id>"}
{"type":"queue:discard","id":"<update-id>"}
```

## Menu Bar Controller

Start the menu bar utility:

```bash
relay-link-menubar
```

The menu shows whether port `8765` is reachable, can start the daemon, and can open `~/Library/Logs/relay-link.log`.

## macOS Permissions

Text clipboard sync uses `pbpaste` and `pbcopy`.

Image clipboard sync requires `pyobjc-framework-Cocoa`.

Pointer routing requires `pyobjc-framework-Quartz` and macOS Accessibility permission for the Python process or app wrapper that launches the daemon:

```text
System Settings -> Privacy & Security -> Accessibility
```

## Android Client Notes

The repository includes a native Android app under `android/`.

Fast path, with an Android device connected over Universal Serial Bus (USB) and USB debugging enabled:

```bash
scripts/android_one_shot.sh
```

The script:

1. Detects the Mac LAN IP.
2. Creates the Python virtual environment if needed.
3. Starts the Mac daemon on port `8765`.
4. Builds and installs the Android debug app.
5. Launches the app with host, token, display width, display height, and autostart extras.

Useful overrides:

```bash
RELAY_LINK_TOKEN="change-this" \
RELAY_LINK_MAC_IP="192.168.1.20" \
RELAY_LINK_MAC_WIDTH="1728" \
RELAY_LINK_MAC_HEIGHT="1117" \
scripts/android_one_shot.sh
```

Manual Android behavior:

1. Enter the Mac IP address.
2. Enter the shared token.
3. Enter the Mac display width and height.
4. Tap `Save and Start Relay`.
5. Keep the app visible for the most reliable clipboard watching on modern Android.
6. Use the pointer pad to send macOS pointer packets.

Android clipboard limits:

- Text clipboard sync is implemented.
- Inbound image data URLs are preserved as clipboard text.
- Native Android image clipboard insertion needs a `ContentProvider` and file grants; that is intentionally not hidden behind fake magic.
- Android may restrict background clipboard reads. The foreground service keeps the socket alive, but clipboard watching is most reliable while Relay Link is visible.

## Development

```bash
pytest tests/ -x -q
ruff check .
ruff format --check .
cd android && ./gradlew testDebugUnitTest assembleDebug
```

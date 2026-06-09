# Relay Link

Relay Link is a local macOS host daemon for Android tablet handoff over a standard WebSocket relay on port `8765`.

It supports:

- Bidirectional clipboard messages for text and PNG image data URLs.
- Pointer coordinate packets routed into macOS through Quartz Event Services.
- A bounded buffered sync queue for inspecting inbound clipboard writes before release.
- A small macOS menu bar controller for starting the daemon and opening logs.

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

The Android tablet client should:

1. Connect to `ws://<mac-lan-ip>:8765`.
2. Send `hello` with role `tablet`.
3. Listen for `clipboard` messages and write them into the Android clipboard.
4. Watch the Android clipboard and send `clipboard` messages back to the host.
5. Convert boundary gestures into `pointer` packets with macOS display coordinates.
6. Use `queue:list`, `queue:release`, and `queue:discard` when manual release mode is active.

## Development

```bash
pytest tests/ -x -q
ruff check .
ruff format --check .
```


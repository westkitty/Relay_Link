# Integration Guide

## Codex Implementation Prompt

Generate or update a macOS local controller daemon for Relay Link with these requirements:

1. Run a WebSocket server on port `8765`, binding to `0.0.0.0`.
2. Watch the macOS clipboard for text and PNG image payloads.
3. Broadcast clipboard changes as JSON to connected clients.
4. Accept inbound clipboard JSON from Android tablets and update the local macOS clipboard.
5. Prevent clipboard recursion when the daemon writes to the clipboard itself.
6. Accept pointer coordinate packets and route them through native macOS event APIs.
7. Maintain connected node metadata: role, remote address, token verification status, and byte counters.
8. Provide a bounded buffered sync queue so inbound clipboard updates can be inspected, released, or discarded.
9. Provide a small menu bar utility that starts the daemon and opens logs.

## Native Android Tablet Instructions

Implement a foreground service with a persistent notification and a WebSocket client.

Minimum behavior:

- Connect to `ws://<mac-lan-ip>:8765`.
- Send `{"type":"hello","role":"tablet","token":"<shared-token>"}`.
- On Android clipboard change, send `clipboard` JSON to the host.
- On inbound `clipboard` JSON, write text or decoded image data into Android clipboard/storage.
- On pointer boundary activation, send `pointer` JSON packets with absolute display coordinates.
- If manual-release mode is used, present queue items to the user before sending `queue:release`.

Keep clipboard overwrites visible to the user. Silent clipboard replacement is a wonderful way to create confusion and then pretend it is synchronization.


import json

import pytest

from relay_link.clipboard import Clipboard
from relay_link.daemon import RelayConfig, RelayDaemon
from relay_link.messages import ClipboardPayload, PointerPayload
from relay_link.pointer import PointerController


class FakeClipboard(Clipboard):
    def __init__(self) -> None:
        self.payload: ClipboardPayload | None = None
        self.writes: list[ClipboardPayload] = []

    def read(self) -> ClipboardPayload | None:
        return self.payload

    def write(self, payload: ClipboardPayload) -> None:
        self.writes.append(payload)
        self.payload = payload


class FakePointer(PointerController):
    def __init__(self) -> None:
        self.events: list[PointerPayload] = []

    def apply(self, payload: PointerPayload) -> None:
        self.events.append(payload)


class Sender:
    def __init__(self) -> None:
        self.messages: list[dict[str, object]] = []

    async def __call__(self, raw: str) -> None:
        self.messages.append(json.loads(raw))


@pytest.mark.asyncio
async def test_inbound_clipboard_auto_release_updates_local_clipboard() -> None:
    clipboard = FakeClipboard()
    daemon = RelayDaemon(RelayConfig(auto_release=True), clipboard=clipboard, pointer=FakePointer())
    sender = Sender()

    await daemon._route_message(
        "node-1",
        json.dumps(
            {"type": "clipboard", "format": "text", "sender": "tablet", "content": "copied"}
        ),
        sender,
    )

    assert clipboard.writes == [ClipboardPayload(format="text", sender="tablet", content="copied")]
    assert daemon.buffer.list_pending() == []


@pytest.mark.asyncio
async def test_manual_release_keeps_clipboard_update_buffered() -> None:
    clipboard = FakeClipboard()
    daemon = RelayDaemon(
        RelayConfig(auto_release=False), clipboard=clipboard, pointer=FakePointer()
    )
    sender = Sender()

    await daemon._route_message(
        "node-1",
        json.dumps({"type": "clipboard", "format": "text", "sender": "tablet", "content": "hold"}),
        sender,
    )

    pending = daemon.buffer.list_pending()
    assert len(pending) == 1
    assert clipboard.writes == []

    await daemon._route_message(
        "node-1", json.dumps({"type": "queue:release", "id": pending[0].update_id}), sender
    )

    assert clipboard.writes == [ClipboardPayload(format="text", sender="tablet", content="hold")]


@pytest.mark.asyncio
async def test_pointer_payload_routes_to_pointer_controller() -> None:
    pointer = FakePointer()
    daemon = RelayDaemon(RelayConfig(), clipboard=FakeClipboard(), pointer=pointer)
    sender = Sender()

    await daemon._route_message(
        "node-1",
        json.dumps({"type": "pointer", "x": 22, "y": 44, "action": "move"}),
        sender,
    )

    assert pointer.events == [PointerPayload(x=22.0, y=44.0, action="move")]

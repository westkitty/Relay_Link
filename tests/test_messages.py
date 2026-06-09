import pytest

from relay_link.messages import ClipboardPayload, PointerPayload


def test_clipboard_payload_round_trip() -> None:
    payload = ClipboardPayload(format="text", sender="mac", content="hello")

    parsed = ClipboardPayload.from_json(payload.to_json())

    assert parsed == payload


def test_clipboard_payload_rejects_bad_format() -> None:
    with pytest.raises(ValueError, match="format"):
        ClipboardPayload.from_json(
            {"type": "clipboard", "format": "pdf", "sender": "tablet", "content": "x"}
        )


def test_pointer_payload_accepts_coordinate_alias() -> None:
    payload = PointerPayload.from_json({"type": "coordinate", "x": 12, "y": 34, "action": "down"})

    assert payload.x == 12.0
    assert payload.y == 34.0
    assert payload.action == "down"

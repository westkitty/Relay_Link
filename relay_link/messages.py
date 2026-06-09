from dataclasses import dataclass
from typing import Any, Literal, Self

ClipboardFormat = Literal["text", "image"]
NodeRole = Literal["host", "tablet"]


@dataclass(slots=True)
class ClipboardPayload:
    format: ClipboardFormat
    sender: str
    content: str

    def to_json(self) -> dict[str, str]:
        return {
            "type": "clipboard",
            "format": self.format,
            "sender": self.sender,
            "content": self.content,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        if data.get("type") != "clipboard":
            raise ValueError("message is not a clipboard payload")
        payload_format = data.get("format")
        if payload_format not in {"text", "image"}:
            raise ValueError("clipboard format must be text or image")
        content = data.get("content")
        if not isinstance(content, str):
            raise ValueError("clipboard content must be a string")
        sender = data.get("sender", "unknown")
        if not isinstance(sender, str):
            raise ValueError("clipboard sender must be a string")
        return cls(format=payload_format, sender=sender, content=content)


@dataclass(slots=True)
class PointerPayload:
    x: float
    y: float
    action: str = "move"
    button: str = "left"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        if data.get("type") not in {"pointer", "coordinate"}:
            raise ValueError("message is not a pointer payload")
        x = data.get("x")
        y = data.get("y")
        if not isinstance(x, int | float) or not isinstance(y, int | float):
            raise ValueError("pointer x and y must be numeric")
        action = data.get("action", "move")
        button = data.get("button", "left")
        if not isinstance(action, str) or not isinstance(button, str):
            raise ValueError("pointer action and button must be strings")
        return cls(x=float(x), y=float(y), action=action, button=button)

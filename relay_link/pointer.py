import logging
from typing import Protocol

from relay_link.messages import PointerPayload

logger = logging.getLogger(__name__)


class PointerController(Protocol):
    def apply(self, payload: PointerPayload) -> None: ...


class QuartzPointerController:
    def apply(self, payload: PointerPayload) -> None:
        try:
            from Quartz import (
                CGEventCreateMouseEvent,
                CGEventPost,
                kCGEventLeftMouseDown,
                kCGEventLeftMouseUp,
                kCGEventMouseMoved,
                kCGHIDEventTap,
                kCGMouseButtonLeft,
            )
        except ImportError as exc:
            raise RuntimeError("pointer routing requires pyobjc-framework-Quartz") from exc

        event_type = kCGEventMouseMoved
        if payload.action == "down":
            event_type = kCGEventLeftMouseDown
        elif payload.action == "up":
            event_type = kCGEventLeftMouseUp
        event = CGEventCreateMouseEvent(
            None, event_type, (payload.x, payload.y), kCGMouseButtonLeft
        )
        CGEventPost(kCGHIDEventTap, event)


class LoggingPointerController:
    def apply(self, payload: PointerPayload) -> None:
        logger.info(
            "pointer %s x=%.1f y=%.1f button=%s",
            payload.action,
            payload.x,
            payload.y,
            payload.button,
        )


def default_pointer_controller() -> PointerController:
    return QuartzPointerController()

import asyncio
import time
import uuid
from dataclasses import dataclass, field

from relay_link.messages import ClipboardPayload


@dataclass(slots=True)
class BufferedClipboardUpdate:
    update_id: str
    payload: ClipboardPayload
    created_at: float = field(default_factory=time.time)

    @property
    def size_kb(self) -> float:
        return len(self.payload.content.encode("utf-8")) / 1024


class BufferedSyncQueue:
    def __init__(self, max_size: int = 100) -> None:
        self._queue: asyncio.Queue[BufferedClipboardUpdate] = asyncio.Queue(maxsize=max_size)
        self._pending: dict[str, BufferedClipboardUpdate] = {}

    async def submit(self, payload: ClipboardPayload) -> BufferedClipboardUpdate:
        update = BufferedClipboardUpdate(update_id=str(uuid.uuid4()), payload=payload)
        await self._queue.put(update)
        self._pending[update.update_id] = update
        return update

    def list_pending(self) -> list[BufferedClipboardUpdate]:
        return list(self._pending.values())

    def release(self, update_id: str) -> BufferedClipboardUpdate | None:
        return self._pending.pop(update_id, None)

    def discard(self, update_id: str) -> BufferedClipboardUpdate | None:
        return self._pending.pop(update_id, None)

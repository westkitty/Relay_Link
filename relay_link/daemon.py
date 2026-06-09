import argparse
import asyncio
import hashlib
import json
import logging
import os
import signal
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import websockets

from relay_link.buffer import BufferedSyncQueue
from relay_link.clients import ClientNode, ClientRegistry
from relay_link.clipboard import Clipboard, default_clipboard
from relay_link.messages import ClipboardPayload, PointerPayload
from relay_link.pointer import PointerController, default_pointer_controller

logger = logging.getLogger("relay_link")


@dataclass(slots=True)
class RelayConfig:
    host: str = "0.0.0.0"
    port: int = 8765
    token: str | None = None
    clipboard_poll_seconds: float = 0.35
    queue_size: int = 100
    auto_release: bool = True


class RelayDaemon:
    def __init__(
        self,
        config: RelayConfig,
        clipboard: Clipboard | None = None,
        pointer: PointerController | None = None,
    ) -> None:
        self.config = config
        self.clipboard = clipboard or default_clipboard()
        self.pointer = pointer or default_pointer_controller()
        self.clients = ClientRegistry()
        self.buffer = BufferedSyncQueue(max_size=config.queue_size)
        self._sockets: dict[str, Any] = {}
        self._last_clipboard_hash: str | None = None
        self._self_update_hashes: set[str] = set()
        self._stop = asyncio.Event()

    async def serve(self) -> None:
        async with websockets.serve(self._handle_client, self.config.host, self.config.port):
            logger.info("relay listening on ws://%s:%s", self.config.host, self.config.port)
            watcher = asyncio.create_task(self._watch_clipboard())
            try:
                await self._stop.wait()
            finally:
                watcher.cancel()
                await asyncio.gather(watcher, return_exceptions=True)

    def stop(self) -> None:
        self._stop.set()

    async def _handle_client(self, websocket: Any) -> None:
        node_id = str(uuid.uuid4())
        remote = str(websocket.remote_address)
        token_verified = self.config.token is None
        node = ClientNode(
            node_id=node_id,
            role="tablet",
            remote=remote,
            token_verified=token_verified,
        )
        self.clients.add(node)
        self._sockets[node_id] = websocket
        logger.info(
            "client connected role=%s remote=%s token=%s", node.role, remote, token_verified
        )
        try:
            async for raw in websocket:
                self.clients.touch(node_id, bytes_in=len(str(raw).encode("utf-8")))
                await self._route_message(node_id, str(raw), websocket.send)
        finally:
            self.clients.remove(node_id)
            self._sockets.pop(node_id, None)
            logger.info("client disconnected remote=%s", remote)

    async def _route_message(
        self,
        node_id: str,
        raw: str,
        send: Callable[[str], Awaitable[None]],
    ) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await send(json.dumps({"type": "error", "message": "invalid json"}))
            return

        if data.get("type") == "hello":
            await self._handle_hello(node_id, data, send)
            return
        if self.config.token and not self._node_verified(node_id):
            await send(json.dumps({"type": "error", "message": "token required"}))
            return
        if data.get("type") == "clipboard":
            await self._handle_inbound_clipboard(ClipboardPayload.from_json(data))
            return
        if data.get("type") in {"pointer", "coordinate"}:
            self.pointer.apply(PointerPayload.from_json(data))
            return
        if data.get("type") == "queue:list":
            await send(json.dumps({"type": "queue", "items": self._queue_items()}))
            return
        if data.get("type") == "queue:release":
            await self._release_update(str(data.get("id", "")))
            return
        if data.get("type") == "queue:discard":
            self.buffer.discard(str(data.get("id", "")))
            return
        await send(json.dumps({"type": "error", "message": "unknown message type"}))

    async def _handle_hello(
        self,
        node_id: str,
        data: dict[str, Any],
        send: Callable[[str], Awaitable[None]],
    ) -> None:
        provided_token = data.get("token")
        verified = self.config.token is None or provided_token == self.config.token
        role = data.get("role", "tablet")
        if role not in {"host", "tablet"}:
            role = "tablet"
        nodes = {node.node_id: node for node in self.clients.snapshot()}
        if node_id in nodes:
            nodes[node_id].role = role
            nodes[node_id].token_verified = verified
        await send(json.dumps({"type": "hello", "ok": verified, "node_id": node_id}))
        logger.info("hello role=%s token=%s", role, verified)

    async def _handle_inbound_clipboard(self, payload: ClipboardPayload) -> None:
        update = await self.buffer.submit(payload)
        logger.info("buffered clipboard sender=%s size=%.1fKB", payload.sender, update.size_kb)
        if self.config.auto_release:
            await self._release_update(update.update_id)

    async def _release_update(self, update_id: str) -> None:
        update = self.buffer.release(update_id)
        if update is None:
            return
        self.clipboard.write(update.payload)
        self._self_update_hashes.add(self._hash_payload(update.payload))
        logger.info("released clipboard update id=%s size=%.1fKB", update.update_id, update.size_kb)

    async def _watch_clipboard(self) -> None:
        while not self._stop.is_set():
            try:
                payload = self.clipboard.read()
                if payload is not None:
                    payload_hash = self._hash_payload(payload)
                    if payload_hash in self._self_update_hashes:
                        self._self_update_hashes.discard(payload_hash)
                        self._last_clipboard_hash = payload_hash
                    elif payload_hash != self._last_clipboard_hash:
                        self._last_clipboard_hash = payload_hash
                        await self._broadcast(payload.to_json())
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("clipboard watcher failed")
            await asyncio.sleep(self.config.clipboard_poll_seconds)

    async def _broadcast(self, payload: dict[str, str]) -> None:
        raw = json.dumps(payload)
        if not self._sockets:
            return
        results = await asyncio.gather(
            *(socket.send(raw) for socket in self._sockets.values()),
            return_exceptions=True,
        )
        size_kb = len(raw.encode("utf-8")) / 1024
        logger.info("broadcast clipboard clients=%s size=%.1fKB", len(self._sockets), size_kb)
        for node_id in self._sockets:
            self.clients.touch(node_id, bytes_out=len(raw.encode("utf-8")))
        for result in results:
            if isinstance(result, Exception):
                logger.warning("broadcast failed: %s", result)

    def _queue_items(self) -> list[dict[str, str | float]]:
        return [
            {
                "id": update.update_id,
                "format": update.payload.format,
                "sender": update.payload.sender,
                "size_kb": update.size_kb,
                "created_at": update.created_at,
            }
            for update in self.buffer.list_pending()
        ]

    def _node_verified(self, node_id: str) -> bool:
        return any(
            node.node_id == node_id and node.token_verified for node in self.clients.snapshot()
        )

    def _hash_payload(self, payload: ClipboardPayload) -> str:
        return hashlib.sha256(f"{payload.format}\0{payload.content}".encode()).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Relay Link macOS host daemon")
    parser.add_argument("--host", default=os.getenv("RELAY_LINK_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("RELAY_LINK_PORT", "8765")))
    parser.add_argument("--token", default=os.getenv("RELAY_LINK_TOKEN"))
    parser.add_argument("--manual-release", action="store_true")
    parser.add_argument("--log-level", default=os.getenv("RELAY_LINK_LOG_LEVEL", "INFO"))
    return parser


async def amain() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s"
    )
    daemon = RelayDaemon(
        RelayConfig(
            host=args.host,
            port=args.port,
            token=args.token,
            auto_release=not args.manual_release,
        )
    )
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, daemon.stop)
    await daemon.serve()


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()

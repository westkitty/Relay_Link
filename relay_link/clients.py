import time
from dataclasses import dataclass, field

from relay_link.messages import NodeRole


@dataclass(slots=True)
class ClientNode:
    node_id: str
    role: NodeRole
    remote: str
    token_verified: bool
    connected_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    bytes_in: int = 0
    bytes_out: int = 0

    def touch(self, bytes_in: int = 0, bytes_out: int = 0) -> None:
        self.last_seen = time.time()
        self.bytes_in += bytes_in
        self.bytes_out += bytes_out


class ClientRegistry:
    def __init__(self) -> None:
        self._nodes: dict[str, ClientNode] = {}

    def add(self, node: ClientNode) -> None:
        self._nodes[node.node_id] = node

    def remove(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)

    def touch(self, node_id: str, bytes_in: int = 0, bytes_out: int = 0) -> None:
        if node_id in self._nodes:
            self._nodes[node_id].touch(bytes_in=bytes_in, bytes_out=bytes_out)

    def snapshot(self) -> list[ClientNode]:
        return list(self._nodes.values())

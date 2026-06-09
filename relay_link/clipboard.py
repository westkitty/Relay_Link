import base64
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Protocol

from relay_link.messages import ClipboardPayload

logger = logging.getLogger(__name__)


class Clipboard(Protocol):
    def read(self) -> ClipboardPayload | None: ...

    def write(self, payload: ClipboardPayload) -> None: ...


class MacClipboard:
    def read(self) -> ClipboardPayload | None:
        image = self._read_image()
        if image is not None:
            return image
        text = subprocess.run(
            ["pbpaste"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout
        if text == "":
            return None
        return ClipboardPayload(format="text", sender="mac", content=text)

    def write(self, payload: ClipboardPayload) -> None:
        if payload.format == "text":
            subprocess.run(["pbcopy"], input=payload.content, text=True, check=True, timeout=2)
            return
        self._write_image(payload.content)

    def _read_image(self) -> ClipboardPayload | None:
        try:
            from AppKit import NSImage, NSPasteboard, NSPasteboardTypePNG
        except ImportError:
            return None

        pasteboard = NSPasteboard.generalPasteboard()
        data = pasteboard.dataForType_(NSPasteboardTypePNG)
        if data is None:
            image = NSImage.alloc().initWithPasteboard_(pasteboard)
            if image is None:
                return None
            data = image.TIFFRepresentation()
        if data is None:
            return None
        raw = bytes(data)
        encoded = base64.b64encode(raw).decode("ascii")
        return ClipboardPayload(
            format="image", sender="mac", content=f"data:image/png;base64,{encoded}"
        )

    def _write_image(self, data_url: str) -> None:
        try:
            from AppKit import NSPasteboard, NSPasteboardTypePNG
            from Foundation import NSData
        except ImportError as exc:
            raise RuntimeError("image clipboard support requires pyobjc-framework-Cocoa") from exc

        prefix = "data:image/png;base64,"
        if not data_url.startswith(prefix):
            raise ValueError("image clipboard payload must be a PNG data URL")
        raw = base64.b64decode(data_url[len(prefix) :])
        ns_data = NSData.dataWithBytes_length_(raw, len(raw))
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        pasteboard.setData_forType_(ns_data, NSPasteboardTypePNG)


class FileClipboard:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> ClipboardPayload | None:
        if not self.path.exists():
            return None
        content = self.path.read_text()
        if content == "":
            return None
        return ClipboardPayload(format="text", sender="mac", content=content)

    def write(self, payload: ClipboardPayload) -> None:
        if payload.format != "text":
            logger.info("file clipboard ignores non-text payloads")
            return
        self.path.write_text(payload.content)


def default_clipboard() -> Clipboard:
    if Path("/usr/bin/pbpaste").exists() or Path("/bin/pbpaste").exists():
        return MacClipboard()
    temp_path = Path(tempfile.gettempdir()) / "relay-link-clipboard.txt"
    return FileClipboard(temp_path)

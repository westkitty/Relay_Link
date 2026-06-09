import json
import socket
import subprocess
import sys
from pathlib import Path


def _daemon_command() -> list[str]:
    return [sys.executable, "-m", "relay_link.daemon"]


def _is_port_open(host: str = "127.0.0.1", port: int = 8765) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def _open_logs() -> None:
    log_path = Path.home() / "Library" / "Logs" / "relay-link.log"
    subprocess.run(["open", str(log_path.parent)], check=False)


def _launch_daemon() -> None:
    log_path = Path.home() / "Library" / "Logs" / "relay-link.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as log_file:
        subprocess.Popen(
            [*_daemon_command(), "--log-level", "INFO"],
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )


def _print_status() -> None:
    status = {"running": _is_port_open(), "port": 8765}
    print(json.dumps(status))


def _run_rumps() -> None:
    try:
        import rumps
    except ImportError as exc:
        raise RuntimeError("menu bar mode requires rumps; install relay-link[macos]") from exc

    class RelayLinkMenu(rumps.App):
        def __init__(self) -> None:
            super().__init__("Relay Link")
            self.menu = [
                rumps.MenuItem("Start Daemon", callback=self.start_daemon),
                rumps.MenuItem("Open Logs", callback=self.open_logs),
                rumps.MenuItem("Refresh Status", callback=self.refresh_status),
            ]
            self.refresh_status(None)

        def start_daemon(self, _: object) -> None:
            if not _is_port_open():
                _launch_daemon()
            self.refresh_status(None)

        def open_logs(self, _: object) -> None:
            _open_logs()

        def refresh_status(self, _: object) -> None:
            self.title = "Relay Link: On" if _is_port_open() else "Relay Link: Off"

    RelayLinkMenu().run()


def main() -> None:
    if "--status" in sys.argv:
        _print_status()
        return
    _run_rumps()


if __name__ == "__main__":
    main()

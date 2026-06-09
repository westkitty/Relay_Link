import json
import os
import subprocess
import sys
from pathlib import Path


def _one_shot_command() -> list[str]:
    return [sys.executable, "-m", "relay_link.one_shot"]


def _is_port_open() -> bool:
    result = subprocess.run(
        ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
        check=False,
        capture_output=True,
        text=True,
    )
    return ":8765" in result.stdout


def _open_logs() -> None:
    log_path = Path.home() / "Library" / "Logs" / "relay-link.log"
    subprocess.run(["open", str(log_path.parent)], check=False)


def _run_detached(command: list[str]) -> None:
    log_path = Path.home() / "Library" / "Logs" / "relay-link-menubar.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("RELAY_LINK_ROOT", str(Path.cwd()))
    with log_path.open("a") as log_file:
        subprocess.Popen(
            command,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
            env=env,
        )


def _launch_daemon() -> None:
    _run_detached([*_one_shot_command(), "--mac-only"])


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
                rumps.MenuItem("Launch Mac + Android", callback=self.launch_all),
                rumps.MenuItem("Launch Android App", callback=self.launch_android),
                rumps.MenuItem("Start Mac Daemon", callback=self.start_daemon),
                rumps.MenuItem("Open Logs", callback=self.open_logs),
                rumps.MenuItem("Refresh Status", callback=self.refresh_status),
            ]
            self.refresh_status(None)

        def launch_all(self, _: object) -> None:
            _run_detached(_one_shot_command())
            self.title = "Relay Link: Launching"

        def launch_android(self, _: object) -> None:
            _run_detached([*_one_shot_command(), "--android-only"])
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

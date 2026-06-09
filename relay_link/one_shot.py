import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_repo_root() -> Path:
    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parents[1],
        Path(os.getenv("RELAY_LINK_ROOT", "")) if os.getenv("RELAY_LINK_ROOT") else None,
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        script = candidate / "scripts" / "android_one_shot.sh"
        if script.exists():
            return candidate
    raise RuntimeError("Relay Link repo root not found; set RELAY_LINK_ROOT")


def run_script(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    env = os.environ.copy()
    if args.token:
        env["RELAY_LINK_TOKEN"] = args.token
    if args.mac_ip:
        env["RELAY_LINK_MAC_IP"] = args.mac_ip
    if args.mac_width:
        env["RELAY_LINK_MAC_WIDTH"] = str(args.mac_width)
    if args.mac_height:
        env["RELAY_LINK_MAC_HEIGHT"] = str(args.mac_height)
    if args.mac_only:
        env["RELAY_LINK_SKIP_ANDROID"] = "1"
    script = repo_root / "scripts" / "android_one_shot.sh"
    return subprocess.run([str(script)], cwd=repo_root, env=env, check=False).returncode


def launch_android_app() -> int:
    adb = shutil.which("adb")
    if adb is None:
        print("adb not found on PATH", file=sys.stderr)
        return 1
    return subprocess.run(
        [
            adb,
            "shell",
            "am",
            "start",
            "-n",
            "com.westkitty.relaylink/.MainActivity",
        ],
        check=False,
    ).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Relay Link one-shot Android launcher")
    parser.add_argument("--mac-ip")
    parser.add_argument("--token")
    parser.add_argument("--mac-width", type=int)
    parser.add_argument("--mac-height", type=int)
    parser.add_argument("--mac-only", action="store_true")
    parser.add_argument("--android-only", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.android_only:
        raise SystemExit(launch_android_app())
    raise SystemExit(run_script(args))


if __name__ == "__main__":
    main()

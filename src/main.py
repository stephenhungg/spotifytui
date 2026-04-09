#!/usr/bin/env python3
"""
Entry point for spotifytui.

Handles logging setup, optional VibeChain API startup, and app launch.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

from logging_config import setup_logging
from config import VIBECHAIN_API_URL, VIBECHAIN_API_PATH

_api_process = None


def _check_vibechain() -> bool:
    """Check if the VibeChain API is reachable."""
    try:
        resp = requests.get(f"{VIBECHAIN_API_URL}/health", timeout=2)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False


def _start_vibechain() -> bool:
    """Start the VibeChain API server if available."""
    global _api_process

    api_path = Path(VIBECHAIN_API_PATH)
    if not api_path.exists():
        print(f"  VibeChain path not found: {api_path}")
        print("  AI features disabled (set VIBECHAIN_API_PATH to override)")
        return False

    try:
        print("  Starting VibeChain API...")
        _api_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(api_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

        for i in range(15):
            if _check_vibechain():
                print("  VibeChain API ready")
                return True
            time.sleep(1)

        print("  VibeChain failed to start (timed out)")
        if _api_process:
            _api_process.terminate()
            _api_process = None
        return False

    except FileNotFoundError:
        print("  npm not found -- AI features disabled")
        return False
    except Exception as e:
        print(f"  VibeChain error: {e}")
        return False


def _cleanup() -> None:
    """Terminate the VibeChain process on exit."""
    global _api_process
    if _api_process:
        try:
            os.killpg(os.getpgid(_api_process.pid), signal.SIGTERM)
            _api_process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(os.getpgid(_api_process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        except Exception:
            pass
        finally:
            _api_process = None


def _signal_handler(signum, frame) -> None:
    _cleanup()
    sys.exit(0)


def main() -> None:
    """Main entry point."""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    log_file = setup_logging()

    print("spotifytui")
    print(f"  logs: {log_file}")

    if not _check_vibechain():
        _start_vibechain()
    else:
        print("  VibeChain API already running")

    try:
        from app import SpotifyTUI

        app = SpotifyTUI()
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"  Fatal error: {e}")
    finally:
        _cleanup()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run the complete historical runtime and game audit on a disposable database."""
from __future__ import annotations

import os
import socket
import tempfile


def main():
    with tempfile.TemporaryDirectory(prefix="soulbound-full-audit-") as directory:
        os.environ["SOULBOUND_DB"] = os.path.join(directory, "audit.db")
        os.environ["SOULBOUND_FULL_AUDIT"] = "1"
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            os.environ["SOULBOUND_PORT"] = str(probe.getsockname()[1])
        import server
        try:
            ns = vars(server)
            full = ns["FULL_GAME_PREDEPLOY_AUDIT_V0336"]
            print(f"FULL PREDEPLOY: {full['error_count']} errors, {full.get('warning_count', 0)} warnings")
            for error in full.get("errors", ()):
                print(f"ERROR: {error}")
            if full["error_count"]:
                raise SystemExit(1)
        finally:
            server._BOOT_SOCKET.close()


if __name__ == "__main__":
    main()

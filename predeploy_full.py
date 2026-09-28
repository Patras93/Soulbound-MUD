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
            from admin.cross_system_audit_v1001 import audit as audit_cross_system_v1001
            cross = audit_cross_system_v1001(server)
            print(
                f"CROSS SYSTEM: {len(cross['errors'])} errors, "
                f"{len(cross['warnings'])} warnings; "
                f"{cross['quests']} quests, {cross['mobs']} mobs, "
                f"{cross['items']} items, {cross['rooms']} rooms, {cross['npcs']} NPCs"
            )
            for error in cross.get("errors", ()):
                print(f"CROSS ERROR: {error}")
            for warning in cross.get("warnings", ())[:100]:
                print(f"CROSS WARNING: {warning}")
            if cross["errors"]:
                raise SystemExit(1)

            from validation.ocean_contract_v1001 import audit_ocean_contract_v1001
            contract = audit_ocean_contract_v1001()
            print(f"OCEAN CONTRACT: {contract['error_count']} errors, {contract['routes']} routes")
            if contract["error_count"]:
                raise SystemExit(1)

            from admin.fast_predeploy_audit_v0571 import FAST_PREDEPLOY_AUDIT_V0571 as fast
            print(
                "FINAL AUDIT SUMMARY: "
                f"{fast['duplicate_literal_key_count']} duplicate dict keys; "
                f"{fast['swallowed_exception_count']} swallowed exceptions; "
                f"{fast.get('intentional_swallowed_exception_count', 0)} intentional passes; "
                f"{fast['todo_fixme_count']} TODO/FIXME; "
                f"{len(cross['warnings'])} cross-system warnings"
            )
            print(
                "FULL AUDIT PASS: "
                f"{fast['duplicate_literal_key_count']} duplicate dict keys; "
                f"{fast['swallowed_exception_count']} swallowed exceptions; "
                f"{fast.get('intentional_swallowed_exception_count', 0)} intentional passes; "
                f"{fast['todo_fixme_count']} TODO/FIXME; "
                f"{len(cross['warnings'])} cross-system warnings"
            )
        finally:
            server._BOOT_SOCKET.close()


if __name__ == "__main__":
    main()

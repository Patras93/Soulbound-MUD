#!/usr/bin/env python3
"""Run the complete production-runtime gameplay audit on a disposable database.

SOULBOUND_FULL_AUDIT enables expensive semantic verification, while historical
developer/style audit modules remain a separate opt-in lane.
"""
from __future__ import annotations

import os
import socket
import tempfile


def main():
    with tempfile.TemporaryDirectory(prefix="soulbound-full-audit-") as directory:
        os.environ["SOULBOUND_DB"] = os.path.join(directory, "audit.db")
        os.environ["SOULBOUND_FULL_AUDIT"] = "1"
        os.environ.pop("SOULBOUND_HISTORICAL_AUDITS", None)
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
            # v1.13.30 — audit audytów. Runtime modules may expose diagnostics
            # without raising during production startup. Full predeploy collects every
            # audit report from the assembled compatibility namespace and rejects the
            # image here instead.
            audit_failures = []
            audit_reports = 0
            for name, value in sorted(ns.items()):
                if "AUDIT" not in str(name).upper() or not isinstance(value, dict):
                    continue
                if "error_count" not in value:
                    continue
                audit_reports += 1
                try:
                    error_count = int(value.get("error_count", 0) or 0)
                except (TypeError, ValueError, OverflowError):
                    audit_failures.append(
                        f"{name}: invalid error_count={value.get('error_count')!r}"
                    )
                    continue
                if error_count:
                    errors = tuple(value.get("errors", ()) or ())
                    if errors:
                        audit_failures.extend(
                            f"{name}: {error}" for error in errors[:100]
                        )
                    else:
                        audit_failures.append(
                            f"{name}: error_count={error_count} without error details"
                        )
            print(
                f"RUNTIME AUDIT REGISTRY: {audit_reports} reports, "
                f"{len(audit_failures)} failures"
            )
            for error in audit_failures[:300]:
                print(f"RUNTIME AUDIT ERROR: {error}")
            if audit_failures:
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

            from admin.mob_display_name_audit_v11129 import audit_mob_display_names_v11129
            mob_names = audit_mob_display_names_v11129(server)
            print(
                f"MOB DISPLAY NAMES: {mob_names['error_count']} errors; "
                f"{mob_names['checked']} runtime mob templates checked"
            )
            for error in mob_names.get("errors", ())[:100]:
                print(f"MOB NAME ERROR: {error}")
            if mob_names["error_count"]:
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
            from collections import Counter
            swallowed_hotspots = Counter(
                site.split(":", 1)[0] for site in fast.get("swallowed_exception_sites", ())
            )
            todo_hotspots = Counter(
                site.split(":", 1)[0] for site in fast.get("todo_sites", ())
            )
            swallowed_text = ",".join(
                f"{path}={count}" for path, count in swallowed_hotspots.most_common(6)
            ) or "none"
            todo_text = ",".join(
                f"{path}={count}" for path, count in todo_hotspots.most_common(6)
            ) or "none"
            print(
                "FULL AUDIT PASS: "
                f"{fast['duplicate_literal_key_count']} duplicate dict keys; "
                f"{fast['swallowed_exception_count']} swallowed exceptions; "
                f"{fast.get('intentional_swallowed_exception_count', 0)} intentional passes; "
                f"{fast['todo_fixme_count']} TODO/FIXME; "
                f"{len(cross['warnings'])} cross-system warnings; "
                f"swallowed hotspots [{swallowed_text}]; "
                f"TODO hotspots [{todo_text}]"
            )
        finally:
            server._BOOT_SOCKET.close()


if __name__ == "__main__":
    main()

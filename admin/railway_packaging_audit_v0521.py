# -*- coding: utf-8 -*-
"""Soulbound v0.52.1 - Railway container packaging audit.

Guards the exact regression that caused Railway to build an /app image without
config/, data/, events/ and validation/ even though those packages were present
in DEPLOY_ONLY.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_RUNTIME_PACKAGES = (
    "core", "systems", "world", "network", "storage", "player", "server", "admin",
    "config", "data", "events", "validation",
)


def railway_packaging_audit_v0521():
    errors = []
    missing_runtime_dirs = [name for name in REQUIRED_RUNTIME_PACKAGES if not (ROOT / name).is_dir()]
    for name in missing_runtime_dirs:
        errors.append(f"missing runtime package directory: {name}/")

    docker_path = ROOT / "Dockerfile"
    missing_docker_copies = []
    if docker_path.is_file():
        docker = docker_path.read_text(encoding="utf-8", errors="replace")
        if "COPY server.py /app/server.py" not in docker:
            errors.append("Dockerfile does not copy server.py to /app/server.py")
        for name in REQUIRED_RUNTIME_PACKAGES:
            expected = f"COPY {name} /app/{name}"
            if expected not in docker:
                missing_docker_copies.append(name)
                errors.append(f"Dockerfile missing: {expected}")

        missing_docker_copy_sources = []
        for raw_line in docker.splitlines():
            line = raw_line.strip()
            if not line.upper().startswith("COPY "):
                continue
            parts = line.split()
            if len(parts) < 3 or any(part.startswith("--") for part in parts[1:-1]):
                continue
            for source in parts[1:-1]:
                if any(ch in source for ch in "*?["):
                    continue
                if not (ROOT / source).exists():
                    missing_docker_copy_sources.append(source)
                    errors.append(f"Dockerfile COPY source missing from release root: {source}")
    else:
        missing_docker_copy_sources = []
        errors.append("Dockerfile missing from runtime/release root")

    return {
        "version": "0.52.1",
        "required_package_count": len(REQUIRED_RUNTIME_PACKAGES),
        "missing_runtime_dirs": missing_runtime_dirs,
        "missing_docker_copies": missing_docker_copies,
        "missing_docker_copy_sources": missing_docker_copy_sources,
        "error_count": len(errors),
        "errors": errors,
    }


RAILWAY_PACKAGING_AUDIT_V0521 = railway_packaging_audit_v0521()
if RAILWAY_PACKAGING_AUDIT_V0521["error_count"]:
    raise RuntimeError(
        "Railway Packaging Audit v0.52.1 failed: "
        + "; ".join(RAILWAY_PACKAGING_AUDIT_V0521["errors"][:100])
    )

__all__ = ["railway_packaging_audit_v0521", "RAILWAY_PACKAGING_AUDIT_V0521"]

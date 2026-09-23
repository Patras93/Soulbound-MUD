# -*- coding: utf-8 -*-
"""Structured runtime diagnostics for Soulbound v0.44.0."""
from __future__ import annotations

import hashlib
import json
import time
import traceback
from pathlib import Path

from core.maintenance_catalog import maintenance_hint, subsystem_for_path


def _relative_runtime_path(filename: str, root: Path | None) -> str:
    path = Path(filename)
    if root is not None:
        try:
            return path.resolve().relative_to(Path(root).resolve()).as_posix()
        except Exception:
            pass
    return path.as_posix()


def build_runtime_error_report(exc: BaseException, *, root=None, command=None, handler=None) -> dict:
    root_path = Path(root) if root is not None else None
    frames = traceback.extract_tb(exc.__traceback__)
    chosen = frames[-1] if frames else None
    if root_path is not None:
        for frame in reversed(frames):
            rel = _relative_runtime_path(frame.filename, root_path)
            if not rel.startswith("../") and rel not in ("core/runtime_diagnostics.py", "core/runtime_loader.py", "core/native_runtime.py"):
                chosen = frame
                break

    if chosen is not None:
        rel_file = _relative_runtime_path(chosen.filename, root_path)
        line = int(chosen.lineno or 0)
        function = str(chosen.name or "")
    else:
        rel_file, line, function = "unknown", 0, ""

    stamp = time.time_ns()
    seed = f"{type(exc).__name__}|{rel_file}|{line}|{handler or ''}|{stamp}".encode("utf-8", "replace")
    error_id = "SB-" + hashlib.blake2s(seed, digest_size=4).hexdigest().upper()
    area = subsystem_for_path(rel_file)
    return {
        "error_id": error_id,
        "exception": type(exc).__name__,
        "message": str(exc),
        "command": str(command or ""),
        "handler": str(handler or function or ""),
        "file": rel_file,
        "line": line,
        "function": function,
        "subsystem": area,
        "maintenance_hint": maintenance_hint(rel_file),
        "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    }


def log_runtime_error(report: dict) -> None:
    header = {k: report.get(k) for k in (
        "error_id", "exception", "message", "command", "handler", "file", "line", "subsystem"
    )}
    print("[SOULBOUND ERROR] " + json.dumps(header, ensure_ascii=False, sort_keys=True), flush=True)
    tb = str(report.get("traceback") or "").rstrip()
    if tb:
        print(tb, flush=True)

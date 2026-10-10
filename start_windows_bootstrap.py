# -*- coding: utf-8 -*-
"""Minimal standard-library guard: log even if host_windows.py cannot be imported."""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import runpy
import sys
import traceback

ROOT = Path(__file__).resolve().parent
LOG_DIR = Path(os.environ.get("SOULBOUND_LOG_DIR") or ROOT / "logs").resolve()


def run_host(source: Path | None = None) -> int:
    host = Path(source) if source is not None else ROOT / "host_windows.py"
    try:
        runpy.run_path(str(host), run_name="__main__")
    except SystemExit:
        # The launcher has already logged the child process outcome.
        raise
    except BaseException as exc:
        details = traceback.format_exc()
        message = f"BLAD PRZED STARTEM SERWERA: {type(exc).__name__}: {exc}"
        if sys.stderr is not None:
            print(message, file=sys.stderr, flush=True)
            print(details, file=sys.stderr, flush=True)
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            with (LOG_DIR / "bledy.log").open("a", encoding="utf-8") as log:
                log.write(f"{datetime.now().isoformat(timespec='seconds')} | {message}\n{details}\n")
        except OSError as storage_error:
            if sys.stderr is not None:
                print(f"Nie mozna zapisac bledy.log: {storage_error}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run_host())

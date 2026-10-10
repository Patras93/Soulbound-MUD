# -*- coding: utf-8 -*-
"""Windows console launcher: UTF-8 console + rotating full/error logs.

Standalone, standard-library only; does not alter Soulbound combat or database.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
import traceback

ROOT = Path(__file__).resolve().parent
LOG_DIR = Path(os.environ.get("SOULBOUND_LOG_DIR") or (ROOT / "logs")).resolve()
MAX_LOG_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

# Soulbound intentionally emits certain handled exceptions on stdout.
ERROR_LINE = re.compile(
    r"\[SOULBOUND ERROR\]|\b(?:CRITICAL|FATAL|ERROR)\b|"
    r"(?:^|[\s\[])\w+_ERROR\b|^Traceback \(most recent call last\):|"
    r"\b(?:Exception|OverflowError|MemoryError|RuntimeError|ValueError):",
    re.IGNORECASE,
)


def _setup_logger(name: str, filename: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()
    sink = RotatingFileHandler(
        LOG_DIR / filename,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    sink.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(sink)
    return logger


def _forward(stream, kind: str, all_log: logging.Logger, error_log: logging.Logger, console_lock: threading.Lock) -> None:
    to_console = sys.stderr if kind == "STDERR" else sys.stdout
    trace_tail = 0
    try:
        for raw in iter(stream.readline, ""):
            line = raw.rstrip("\r\n")
            with console_lock:
                try:
                    to_console.write(raw)
                    to_console.flush()
                except (OSError, UnicodeError) as exc:
                    # Terminal may be closed; keep writing to logs regardless.
                    all_log.error("CONSOLE_WRITE_FAILURE | %s: %s", type(exc).__name__, exc)
                    error_log.error("CONSOLE_WRITE_FAILURE | %s: %s", type(exc).__name__, exc)
            # Record stdout and stderr in one timeline. A separate file captures
            # stderr and explicitly marked stdout errors from Soulbound modules.
            all_log.info("%s | %s", kind, line)
            flagged = bool(ERROR_LINE.search(line))
            if kind == "STDERR" or flagged or trace_tail > 0:
                error_log.error("%s | %s", kind, line)
            # Soulbound's [SOULBOUND ERROR] output is followed by a traceback on
            # stdout. Keep a bounded number of subsequent traceback lines.
            if "[SOULBOUND ERROR]" in line or "Traceback (most recent call last):" in line:
                trace_tail = 100
            elif trace_tail:
                trace_tail -= 1
                if not line.strip() or re.match(r"^[A-Za-z_][\w.]*(?:Error|Exception|Exit|Interrupt):", line):
                    trace_tail = 0
                elif line and not line.startswith((" ", "\t")) and not flagged:
                    trace_tail = 0
    finally:
        stream.close()


def run_server(entry: Path | None = None) -> int:
    """Return child's exit status; do not restart a failing server automatically."""
    source = Path(entry) if entry is not None else ROOT / "server.py"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    all_log = _setup_logger("soulbound.host.all", "serwer.log")
    error_log = _setup_logger("soulbound.host.errors", "bledy.log")
    if not source.is_file():
        message = f"BRAK PLIKU SERWERA: {source}"
        all_log.error("START | %s", message)
        error_log.error("START | %s", message)
        print(message, file=sys.stderr, flush=True)
        return 2
    env = os.environ.copy()
    env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"})
    env["SOULBOUND_CONTROL_TOKEN"] = secrets.token_hex(32)
    env["SOULBOUND_CONTROL_FILE"] = str(LOG_DIR / "soulbound_control.json")
    print(f"Soulbound — logi serwera: {LOG_DIR / 'serwer.log'}", flush=True)
    print(f"Soulbound — logi bledow: {LOG_DIR / 'bledy.log'}", flush=True)
    print("Ctrl+C zatrzymuje serwer. Logi sa zapisywane w UTF-8.", flush=True)
    all_log.info("START | Uruchomiono proces Soulbound.")
    try:
        process = subprocess.Popen(
            [sys.executable, "-u", str(source)],
            cwd=ROOT,
            env=env,
            stdin=None,  # Pass through terminal input when needed.
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except (OSError, ValueError) as exc:
        all_log.exception("Nie mozna uruchomic serwera: %s", exc)
        error_log.exception("Nie mozna uruchomic serwera: %s", exc)
        print(f"Blad uruchomienia serwera: {exc}", file=sys.stderr, flush=True)
        return 1
    guard = threading.Lock()
    threads = [
        threading.Thread(target=_forward, args=(pipe, kind, all_log, error_log, guard), daemon=True)
        for pipe, kind in ((process.stdout, "STDOUT"), (process.stderr, "STDERR"))
    ]
    for t in threads:
        t.start()
    try:
        code = process.wait()
    except KeyboardInterrupt:
        # CTRL+C may be received by the server as well; terminate if needed.
        if process.poll() is None:
            process.terminate()
        try:
            code = process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            code = process.wait()
    for t in threads:
        t.join(timeout=5)
    all_log.info("STOP | Kod zakonczenia serwera: %s", code)
    if code:
        error_log.error("STOP | Kod zakonczenia serwera: %s", code)
        print(f"Serwer zakonczyl prace z kodem: {code}", file=sys.stderr, flush=True)
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(run_server())
    except KeyboardInterrupt:
        print("Soulbound: przerwano uruchamianie.", file=sys.stderr, flush=True)
        raise SystemExit(130)
    except BaseException as exc:
        # Awaria samego launchera (np. brak dostepu do plikow logow).
        # Nie ukrywaj tracebacka przed NVDA, nawet jesli zapis jest niemozliwy.
        message = f"BLAD LAUNCHERA: {type(exc).__name__}: {exc}"
        print(message, file=sys.stderr, flush=True)
        traceback.print_exc()
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            error_log = _setup_logger("soulbound.host.errors", "bledy.log")
            error_log.error("%s\n%s", message, traceback.format_exc())
        except (OSError, ValueError):
            print("Nie mozna zapisac bledy.log: sprawdz uprawnienia i dysk.", file=sys.stderr, flush=True)
        raise SystemExit(1)

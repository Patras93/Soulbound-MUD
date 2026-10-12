# -*- coding: utf-8 -*-
"""Spójne migawki SQLite bez zatrzymywania Soulbound; tylko biblioteka standardowa.

Każdy backup jest tworzony do pliku tymczasowego metodą Connection.backup().
Publikacja następuje dopiero po zamknięciu połączeń i integrity_check=ok.
Nie dotykamy WAL/SHM pracującego serwera ani istniejących backupów przy błędzie.
"""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parent
KINDS = {"start": 2, "hourly": 48, "stop": 14, "manual": 14}


def db_path() -> Path:
    raw = os.environ.get("SOULBOUND_DB", "").strip()
    if not raw:
        mount = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
        raw = str(Path(mount) / "soulbound.db") if mount else "soulbound.db"
    value = Path(raw)
    return (value if value.is_absolute() else ROOT / value).resolve()


def backups_path() -> Path:
    raw = os.environ.get("SOULBOUND_BACKUP_DIR", "").strip()
    return Path(raw).resolve() if raw else ROOT.parent / (ROOT.name + "_BACKUPS")


def create_backup(kind: str = "manual") -> Path:
    if kind not in KINDS:
        raise ValueError("Nieznany tryb backupu")
    source = db_path()
    if not source.is_file() or source.stat().st_size < 1024:
        raise FileNotFoundError(f"Brak prawdziwej bazy danych: {source}")
    directory = backups_path()
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out = directory / f"soulbound-{kind}-{stamp}.db"
    fd, pending_name = tempfile.mkstemp(prefix=".soulbound-", suffix=".db.tmp", dir=directory)
    os.close(fd)
    pending = Path(pending_name)
    committed = False
    try:
        src = sqlite3.connect(str(source), timeout=20.0)
        try:
            src.execute("PRAGMA query_only=ON")
            dst = sqlite3.connect(str(pending), timeout=20.0)
            try:
                src.backup(dst, pages=128, sleep=0.15)
                # Zamieniamy tryb WAL na samodzielny plik (bez sidecarów).
                mode = dst.execute("PRAGMA journal_mode=DELETE").fetchone()[0]
                if str(mode).lower() != "delete":
                    raise RuntimeError("Nie udalo sie zamknac WAL w kopii SQLite")
                result = dst.execute("PRAGMA integrity_check").fetchone()[0]
                if result != "ok":
                    raise RuntimeError(f"Kontrola bazy zakonczona bledem: {result}")
            finally:
                dst.close()
        finally:
            src.close()
        # Finalna nazwa pojawia się dopiero gdy kopia jest w pełni gotowa.
        os.replace(pending, out)
        committed = True
        seed = ROOT / "soulbound_world_seed.txt"
        if seed.is_file():
            try:
                shutil.copy2(seed, out.with_suffix('.seed.txt'))
            except OSError as exc:
                print(f"UWAGA: nie skopiowano world_seed: {exc}", flush=True)
        # Usuwamy tylko najstarsze własne kopie, po skutecznym ukończeniu nowej.
        owned = sorted(directory.glob(f"soulbound-{kind}-*.db"))
        for old in owned[:-KINDS[kind]]:
            try:
                old.unlink()
                old.with_suffix('.seed.txt').unlink(missing_ok=True)
            except OSError as exc:
                print(f"UWAGA: nie usunieto starej kopii {old.name}: {exc}", flush=True)
        print(f"BACKUP OK ({kind}): {out}", flush=True)
        return out
    finally:
        if not committed:
            pending.unlink(missing_ok=True)
            # SQLite mogło utworzyć tymczasowe sidecary przy zamykaniu WAL.
            for suffix in ('-wal', '-shm', '-journal'):
                Path(str(pending) + suffix).unlink(missing_ok=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) >= 2 else "manual"
    try:
        create_backup(mode)
    except Exception as exc:
        print(f"BACKUP BLAD: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)

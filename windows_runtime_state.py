# -*- coding: utf-8 -*-
"""Windows launcher state paths and atomic publication; no process termination."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile


def fallback_dir(root: Path) -> Path:
    """Separate secondary state per installation, in the user's TEMP folder."""
    digest = hashlib.sha256(str(root.resolve()).casefold().encode('utf-8')).hexdigest()[:20]
    return Path(os.getenv('TEMP') or os.getenv('TMP') or tempfile.gettempdir()) / ('Soulbound-MUD-control-' + digest)


def read_state(path: Path) -> dict:
    try:
        result = json.loads(path.read_text(encoding='utf-8'))
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def write_state(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + str(os.getpid()) + '.new')
    try:
        temp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def remove_matching(path: Path, key: str, value: object, *, root: Path) -> None:
    data = read_state(path)
    if data.get(key) == value and data.get('root') == str(root):
        path.unlink(missing_ok=True)

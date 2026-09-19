# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Soulbound v0.30.43 Modular Core — flat GitHub deploy loader.

All runtime parts live beside server.py so the whole deploy can be uploaded
through GitHub's web "Upload files" dialog in one selection.
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_RUNTIME_PARTS = sorted(_ROOT.glob("part_*.py"))
_EXPECTED = [f"part_{i:02d}.py" for i in range(1, 7)]
_FOUND = [p.name for p in _RUNTIME_PARTS]
if _FOUND != _EXPECTED:
    raise RuntimeError(
        "Soulbound runtime incomplete. Expected: "
        + ", ".join(_EXPECTED)
        + "; found: "
        + (", ".join(_FOUND) if _FOUND else "none")
    )

for _part in _RUNTIME_PARTS:
    _source = _part.read_text(encoding="utf-8")
    exec(compile(_source, str(_part), "exec"), globals(), globals())

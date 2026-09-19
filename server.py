# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Soulbound v0.30.43 Modular Core loader.

Runtime is split into ordered source parts.  Each part executes in this module's
global namespace, preserving the exact v0.30.42 runtime semantics while making
future changes smaller and easier to deploy/test.
"""
from pathlib import Path

_RUNTIME_DIR = Path(__file__).with_name("runtime_parts")
_RUNTIME_PARTS = sorted(_RUNTIME_DIR.glob("part_*.py"))
if not _RUNTIME_PARTS:
    raise RuntimeError("Soulbound runtime_parts are missing")

for _part in _RUNTIME_PARTS:
    _source = _part.read_text(encoding="utf-8")
    exec(compile(_source, str(_part), "exec"), globals(), globals())

del _source, _part

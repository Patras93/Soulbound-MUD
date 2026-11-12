# -*- coding: utf-8 -*-
"""Single authoritative release number for current and future Soulbound.

A release changes VERSION once. No gameplay file requires editing to match it.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r'[0-9]+(?:\.[0-9]+){2}\Z')

def load_version(root=ROOT):
    version=(Path(root)/'VERSION').read_text(encoding='utf-8-sig').strip()
    if not PATTERN.fullmatch(version):
        raise ValueError('Bledny numer wersji w VERSION')
    return version

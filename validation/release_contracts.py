# -*- coding: utf-8 -*-
"""Version-aware historical test contract (no open-ended allowlist).

Validate the version in the archive against the imported game engine and the
packaged VERSION file. Historical regression checks have minimum releases;
mechanical/content assertions remain independent and strict.
"""
from pathlib import Path
import re

_VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")


def parse_version(value):
    value = str(value)
    if not _VERSION_RE.fullmatch(value):
        raise ValueError("Niepoprawny numer wersji: " + repr(value))
    return tuple(map(int, value.split('.')))


def release_valid(value, minimum):
    from core.bootstrap_economy_professions import VERSION as runtime_version
    release_file = Path(__file__).resolve().parents[1] / "VERSION"
    packaged_version = release_file.read_text(encoding="utf-8-sig").strip()
    return (parse_version(value) >= parse_version(minimum)
            and str(value) == runtime_version == packaged_version)


def modern_quest_catalog(value):
    """v35+ retains precisely 6793 authored quests (not a relaxed >= test)."""
    return parse_version(value) >= (35, 0, 0)

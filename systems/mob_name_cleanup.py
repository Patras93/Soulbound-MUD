# -*- coding: utf-8 -*-
"""Runtime mob display-name cleanup.

v1.14.3 rules:
- no floor/level digits in mob display names;
- no duplicated adjacent words;
- no stacked procedural rank noise;
- ordinary runtime mob names are kept to at most three readable words;
- NEMESIS marker remains deliberate and may use its em-dash presentation.
"""
from __future__ import annotations

import re

_LEVEL_RE = re.compile(r"(?:[,;:]?\s*[-–—]?\s*)?(?:poziom|level|pi[eę]tro|floor)\s*[:#-]?\s*\d+", re.I)
_DIGIT_SUFFIX_RE = re.compile(r"(?:[,;:]?\s*[-–—]?\s*)?\b\d+\b")
_WS_RE = re.compile(r"\s+")

# Prefixes that commonly stack through procedural rare/elite generators.
_RANK_WORDS = {
    "wędrujący", "wedrujacy", "rzadki", "elitarna", "elitarny", "elitarne",
    "mityczna", "mityczny", "mityczne", "astralna", "astralny", "astralne",
    "przeklęta", "przeklęty", "przeklęte", "opancerzona", "opancerzony",
    "opancerzone", "wściekła", "wściekły", "wściekłe", "regenerująca",
    "regenerujący", "regenerujące", "przetaktowana", "przetaktowany",
    "przetaktowane",
}


def _dedupe_adjacent(words):
    out = []
    for word in words:
        if out and out[-1].casefold() == word.casefold():
            continue
        out.append(word)
    return out


def clean_mob_display_name_v1142(name: str) -> str:
    raw = _WS_RE.sub(" ", str(name or "").strip())
    if not raw:
        return raw
    if "NEMESIS" in raw.upper():
        # Keep the deliberate Nemesis rank marker but still remove numeric floor text.
        return _WS_RE.sub(" ", _LEVEL_RE.sub("", raw)).strip(" ,;:-–—")

    # Procedural suffixes after an em dash are flavor, not identity; keeping them
    # is the main source of unreadably long names.
    raw = raw.split(" — ", 1)[0].strip()
    raw = _LEVEL_RE.sub("", raw)
    raw = _DIGIT_SUFFIX_RE.sub("", raw)
    raw = _WS_RE.sub(" ", raw).strip(" ,;:-–—")

    words = _dedupe_adjacent(raw.split())
    if not words:
        return "Przeciwnik"

    # Collapse stacked procedural ranks. Keep only the most specific last rank
    # directly before the creature identity.
    rank_positions = [i for i, w in enumerate(words[:-1]) if w.casefold() in _RANK_WORDS]
    if len(rank_positions) > 1:
        keep = rank_positions[-1]
        words = [w for i, w in enumerate(words) if i == keep or i not in rank_positions]
        words = _dedupe_adjacent(words)

    if len(words) > 3:
        # Preserve a rank when present, then the two most identity-bearing tail words.
        rank = next((w for w in words if w.casefold() in _RANK_WORDS), None)
        tail = words[-2:]
        words = ([rank] if rank and rank.casefold() not in {x.casefold() for x in tail} else []) + tail
        words = words[-3:]

    return " ".join(words).strip() or "Przeciwnik"




_ELITE_QUALIFIERS = (
    ("__elite_armored", "Opancerzony"),
    ("__elite_vampiric", "Wampiryczny"),
    ("__elite_regenerating", "Regenerujący"),
    ("__elite_ice", "Lodowy"),
    ("__elite_fire", "Ognisty"),
    ("__elite_astral", "Astralny"),
    ("__elite_furious", "Wściekły"),
    ("__elite_storm", "Burzowy"),
    ("__elite_toxic", "Toksyczny"),
    ("__elite_cursed", "Przeklęty"),
    ("__rare", "Rzadki"),
)

def _mob_qualifier_v1143(mob_id: str) -> str:
    key = str(mob_id or "").casefold()
    for token, label in _ELITE_QUALIFIERS:
        if token in key:
            return label
    if "miniboss" in key:
        return "Czempion"
    if "worldboss" in key:
        return "Światowy"
    if "legendary" in key:
        return "Legendarny"
    if "titan" in key:
        return "Tytaniczny"
    if "ruin_guardian" in key:
        return "Runiczny"
    return "Odmieniec"

def _mob_code_word_v1143(seed: str) -> str:
    # Deterministic, pronounceable, digit-free fallback used only when a short
    # semantic qualifier is still not enough to make a display name unique.
    consonants = ("m", "n", "r", "s", "t", "v", "z", "k", "l", "f", "d", "b")
    vowels = ("a", "e", "i", "o", "u", "y")
    value = sum((i + 1) * ord(ch) for i, ch in enumerate(str(seed))) or 1
    parts = []
    for shift in (0, 7, 13):
        c = consonants[(value >> shift) % len(consonants)]
        v = vowels[(value >> (shift + 3)) % len(vowels)]
        parts.append(c + v)
    return ("".join(parts) + "r").capitalize()

def _unique_runtime_mob_names_v1143(mob_templates: dict) -> int:
    used = set()
    renamed = 0
    # Deterministic order makes names stable across restarts.
    for mob_id in sorted(mob_templates, key=lambda x: str(x)):
        template = mob_templates.get(mob_id)
        if not isinstance(template, dict):
            continue
        name = str(template.get("name") or "").strip()
        if not name:
            continue
        key = name.casefold()
        if key not in used:
            used.add(key)
            continue

        words = name.split()
        qualifier = _mob_qualifier_v1143(str(mob_id))
        # Keep two identity-bearing words and one semantic variant marker.
        identity = words[-2:] if len(words) >= 2 else words[-1:]
        candidate_words = _dedupe_adjacent([qualifier] + identity)
        candidate = " ".join(candidate_words[-3:]).strip()
        if candidate.casefold() in used:
            code = _mob_code_word_v1143(str(mob_id))
            head = identity[-1:] if identity else ["Przeciwnik"]
            candidate = " ".join(_dedupe_adjacent([qualifier] + head + [code])[-3:]).strip()
        salt = 0
        while candidate.casefold() in used:
            salt += 1
            code = _mob_code_word_v1143(f"{mob_id}:{salt}")
            head = identity[-1:] if identity else ["Przeciwnik"]
            candidate = " ".join(_dedupe_adjacent([qualifier] + head + [code])[-3:]).strip()
        template["name"] = candidate
        used.add(candidate.casefold())
        renamed += 1
    return renamed


def normalize_runtime_mob_names_v1142(mob_templates: dict) -> dict:
    changed = 0
    digits_removed = 0
    long_removed = 0
    duplicate_removed = 0
    for template in mob_templates.values():
        if not isinstance(template, dict):
            continue
        before = str(template.get("name") or "").strip()
        if not before:
            continue
        before_words = before.split()
        after = clean_mob_display_name_v1142(before)
        if any(ch.isdigit() for ch in before) and not any(ch.isdigit() for ch in after):
            digits_removed += 1
        if len(before_words) > 3 and len(after.split()) <= 3:
            long_removed += 1
        if any(a.casefold() == b.casefold() for a, b in zip(before_words, before_words[1:])):
            duplicate_removed += 1
        if after != before:
            template["name"] = after
            changed += 1
    uniqueness_renamed = _unique_runtime_mob_names_v1143(mob_templates)
    return {
        "version": "1.14.3",
        "changed": changed,
        "digits_removed": digits_removed,
        "long_names_compacted": long_removed,
        "duplicate_names_cleaned": duplicate_removed,
        "uniqueness_renamed": uniqueness_renamed,
    }


def audit_runtime_mob_names_v1142(mob_templates: dict) -> dict:
    errors = []
    checked = 0
    for mob_id, template in mob_templates.items():
        if not isinstance(template, dict):
            continue
        checked += 1
        name = str(template.get("name") or "").strip()
        if not name:
            errors.append(f"{mob_id}: empty name")
            continue
        if "NEMESIS" not in name.upper():
            if any(ch.isdigit() for ch in name):
                errors.append(f"{mob_id}: digit in display name: {name}")
            if len(name.split()) > 3:
                errors.append(f"{mob_id}: overlong display name: {name}")
            words = name.split()
            if any(a.casefold() == b.casefold() for a, b in zip(words, words[1:])):
                errors.append(f"{mob_id}: repeated word: {name}")
    names = {}
    for mob_id, template in mob_templates.items():
        if not isinstance(template, dict):
            continue
        name = str(template.get("name") or "").strip()
        if name:
            names.setdefault(name.casefold(), []).append(str(mob_id))
    for name, ids in names.items():
        if len(ids) > 1:
            errors.append(f"duplicate display name {name}: {tuple(ids)}")
    return {"version": "1.14.3", "checked": checked, "error_count": len(errors), "errors": errors}

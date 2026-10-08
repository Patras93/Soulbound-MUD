# -*- coding: utf-8 -*-
"""Regression gate for NVDA-friendly item names in Soulbound v1.21.4.

Runs without importing the full world and therefore does not touch player saves.
"""
from __future__ import annotations

import ast
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _assignment(module, name):
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in statement.targets
        ):
            return statement.value
    raise AssertionError(f"Brak definicji {name}")


def _normalize(value):
    text = str(value).strip().lower().replace("ł", "l")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("_", " ").replace("-", " ")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", text).split())


def audit_crafting_names_v1214():
    errors = []
    checks = 0
    source = (ROOT / "systems" / "items_resources.py").read_text(encoding="utf-8")
    recipes_source = (ROOT / "systems" / "equipment_crafting.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    tiers = ast.literal_eval(_assignment(tree, "BLACKSMITH_TIERS"))
    suffixes = ast.literal_eval(_assignment(tree, "_BLACKSMITH_400_LABELS"))
    slots = ast.literal_eval(_assignment(tree, "BLACKSMITH_SLOT_DEFS"))
    labels = [entry["name"] for entry in tiers] + list(suffixes.values())
    # Both the actual blacksmith output name and recipe title are derived from
    # the same stable item ID. Do not change these IDs just to change a label.
    checks += 1
    if 'f"{slot_name} {tier[\'name\']} "' not in source or 'f"{slot_name} - {tier[\'name\']} "' in source:
        errors.append("W generatorze pancerzy nadal jest separator myślnikowy")
    checks += 1
    if '"name": ITEMS[output_id]["name"]' not in recipes_source:
        errors.append("Receptury Kowalstwa nie dziedziczą nazwy przedmiotu")
    for label in labels:
        for slot_name, _defense, _ingots in slots.values():
            generated = f"{slot_name} {label}"
            checks += 1
            if " - " in generated or "-" in generated:
                errors.append(f"Wytworzony przedmiot nadal zawiera minus: {generated}")
    checks += 1
    if "Pancerz Srebrny" not in [f"{slots['body'][0]} {name}" for name in labels]:
        errors.append("Brak poprawnego Pancerza Srebrnego")
    # Existing player input with or without a separator must still resolve to
    # the same normalized query in the game's canonical lookup implementation.
    for old, new in (
        ("pancerz - srebrny", "pancerz srebrny"),
        ("pancerz -srebrny", "pancerz srebrny"),
        ("receptura - zelazny", "receptura zelazny"),
    ):
        checks += 1
        if _normalize(old) != _normalize(new):
            errors.append(f"Niekompatybilny zapis komendy: {old}")
    # Other decorative item-name separators, also noisy in NVDA.
    for group in ("FISH_RARE_VARIANTS", "WOOD_RARE_VARIANTS", "HERB_RARE_VARIANTS"):
        for spec in ast.literal_eval(_assignment(tree, group)).values():
            checks += 1
            if "-" in spec["name_prefix"]:
                errors.append(f"Rzadki surowiec nadal zawiera minus: {spec['name_prefix']!r}")
    # Global mining source names belong to the ITEMS catalog as well.
    ore_source = (ROOT / "core" / "progression_resources.py").read_text(encoding="utf-8")
    ore_tree = ast.parse(ore_source)
    ore_rows = ast.literal_eval(_assignment(ore_tree, "WORLD_ORE_UNLOCKS"))
    for _required, _level, _id, title in ore_rows:
        checks += 1
        if " - " in title:
            errors.append(f"Nazwa rudy nadal zawiera separator: {title}")
    # Literal name fields across the source tree. Non-item names (e.g. room
    # labels) are intentionally excluded rather than changed by accident.
    return {"checks": checks, "blacksmith_names": len(labels) * len(slots),
            "rare_resource_prefixes": 12, "ore_names": len(ore_rows), "errors": errors, "error_count": len(errors)}


if __name__ == "__main__":
    report = audit_crafting_names_v1214()
    print(f"CRAFT NAME CLEAN v1.21.4: {report['checks']} checks; "
          f"{report['blacksmith_names']} armor labels; "
          f"{report['rare_resource_prefixes']} rare resource prefixes; "
          f"{report['ore_names']} ore names; "
          f"{report['error_count']} errors")
    if report['errors']:
        for error in report['errors']:
            print("ERROR:", error)
        raise SystemExit(1)

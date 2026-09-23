# -*- coding: utf-8 -*-
"""Architecture validators for v0.42 data/config/event boundaries."""
from __future__ import annotations

import ast
from pathlib import Path

CATALOG_OWNERS = {
    "ROOMS": "data/rooms.py",
    "ITEMS": "data/items.py",
    "NPCS": "data/npcs.py",
    "QUESTS": "data/quests.py",
    "MOB_TEMPLATES": "data/mobs.py",
    "SHOPS": "data/shops.py",
    "CRAFT_RECIPES": "data/crafting_recipes.py",
    "ALCHEMY_RECIPES": "data/alchemy_recipes.py",
}

LEGACY_LOGIC_FILES = {
    "ROOMS": "core/classes_skills.py",
    "ITEMS": "core/mines_threat.py",
    "NPCS": "systems/content_registry.py",
    "QUESTS": "systems/content_registry.py",
    "MOB_TEMPLATES": "systems/content_registry.py",
    "SHOPS": "systems/equipment_crafting.py",
    "CRAFT_RECIPES": "systems/equipment_crafting.py",
    "ALCHEMY_RECIPES": "systems/equipment_crafting.py",
}


def _assigned_names(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            result.add(node.target.id)
    return result


def validate_modular_boundaries(root):
    root = Path(root)
    errors = []
    for symbol, owner in CATALOG_OWNERS.items():
        owner_path = root / owner
        if not owner_path.is_file():
            errors.append(f"missing data owner {owner}")
            continue
        if symbol not in _assigned_names(owner_path):
            errors.append(f"{symbol} is not owned by {owner}")
        legacy = root / LEGACY_LOGIC_FILES[symbol]
        if legacy.is_file() and symbol in _assigned_names(legacy):
            errors.append(f"{symbol} still assigned in logic file {LEGACY_LOGIC_FILES[symbol]}")

    balance_path = root / "config/balance.py"
    if not balance_path.is_file():
        errors.append("missing config/balance.py")
    else:
        balance_names = _assigned_names(balance_path)
        for expected in ("CHARACTER_MAX_LEVEL", "SKILL_MAX_LEVEL", "PROFESSION_COOLDOWN", "V019_CLASS_REQ"):
            if expected not in balance_names:
                errors.append(f"balance setting missing: {expected}")

    for rel in (
        "events/bus.py", "events/contracts.py", "events/bootstrap.py",
        "events/listeners/chronicle.py", "events/listeners/kill_progression.py",
        "events/listeners/gathering_progression.py",
    ):
        if not (root / rel).is_file():
            errors.append(f"missing event module: {rel}")

    return {"error_count": len(errors), "errors": errors, "catalog_owner_count": len(CATALOG_OWNERS)}

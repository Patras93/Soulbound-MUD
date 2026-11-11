"""Equipment Balance 4.0: read-only production catalogs with disposable dynamic variants.

Run in the disposable, fully assembled world during ``predeploy_full.py``.
This is not a player DPS simulation and never changes a live account/database.
"""
from __future__ import annotations

import copy
import math

STAGES = (100, 200, 400, 600)
QUALITY = ("normal", "good", "excellent", "masterwork", "legendary")


def audit_equipment_balance_runtime_v1174(items, shop_catalog):
    from core.classes_skills import CLASSES
    from systems.legendary_reborn import LEGENDARY_FORGE, CHASE_RELICS
    from systems.crafting_quality import (
        register_crafting_quality_variant_v03054,
        ensure_crafting_quality_variant_v0332,
    )
    from systems.infinite_equipment import (
        infinite_source_profile,
        register_infinite_equipment_variant,
        ensure_infinite_equipment_variant,
    )

    errors, checks = [], 0
    records = {"shop": 0, "legendary": 0, "crafted": 0, "deep": 0, "restored": 0}
    created = set()
    baseline_keys = set(items)
    try:
        # Final runtime catalog: all playable classes must have meaningful,
        # explicitly separate style choices at late stages.
        for class_name, *_ in CLASSES:
            for stage in STAGES:
                hand_ids = [
                    iid for iid in shop_catalog.get(class_name, {}).get(stage, ())
                    if iid in items and items[iid].get("slot") == "hands"
                ]
                checks += 3
                records["shop"] += len(hand_ids)
                if len(hand_ids) < 3:
                    errors.append(f"{class_name}/{stage}: missing shop style hands")
                    continue
                if len({(
                    int(items[i]["defense"]), int(items[i].get("attack", 0) or 0),
                    int(items[i].get("magic_attack", 0) or 0),
                    tuple(sorted((items[i].get("stats") or {}).items())),
                ) for i in hand_ids}) < 3:
                    errors.append(f"{class_name}/{stage}: duplicate styles")
                if any(int(items[i].get("required_mastery", 0) or 0) != stage for i in hand_ids):
                    errors.append(f"{class_name}/{stage}: incorrect equipment gate")
                if any(items[i].get("required_class") != class_name for i in hand_ids):
                    errors.append(f"{class_name}/{stage}: class-specific gear became generic")

        # The Generator must preserve handcrafted legendary item identities,
        # including special effects and elemental wards (not only raw defense).
        authored = {**CHASE_RELICS, **{iid: row[0] for iid, row in LEGENDARY_FORGE.items()}}
        for iid, template in authored.items():
            actual = items.get(iid)
            records["legendary"] += 1
            checks += 5
            if not actual:
                errors.append(f"missing legendary item: {iid}")
                continue
            for attr in ("stats", "properties", "element_wards"):
                if actual.get(attr, {}) != template.get(attr, {}):
                    errors.append(f"{iid}: Generator changed authored {attr}")
            if int(actual.get("sockets", 0) or 0) != int(template.get("sockets", 0) or 0):
                errors.append(f"{iid}: legendary sockets overwritten")
            if actual.get("price") is not None:
                errors.append(f"{iid}: legend was made an ordinary store item")

        # Real catalog samples from four crafting sources and from class EQ
        # with sub-1% effect. The latter directly detects lost fractional perks.
        samples = list(LEGENDARY_FORGE)
        for iid, item in items.items():
            if len(samples) >= len(LEGENDARY_FORGE) + 8:
                break
            if not item.get("slot"):
                continue
            if any(isinstance(v, float) and 0 < v < 1
                   for v in (item.get("properties") or {}).values()):
                samples.append(iid)
        if len(samples) <= len(LEGENDARY_FORGE):
            errors.append("missing fractional-property equipment source to test")

        for base_id in samples:
            base = copy.deepcopy(items[base_id])
            base_props = base.get("properties") or {}
            prev_def = -1
            for quality in QUALITY:
                vid = register_crafting_quality_variant_v03054(base_id, quality)
                created.add(vid)
                item = items[vid]
                records["crafted"] += 1
                checks += 5 + len(base_props)
                if int(item.get("defense", 0) or 0) < int(base.get("defense", 0) or 0):
                    errors.append(f"{vid}: crafting weaker than its base defense")
                if int(item.get("defense", 0) or 0) < prev_def:
                    errors.append(f"{vid}: quality decreased defense")
                prev_def = int(item.get("defense", 0) or 0)
                if item.get("element_wards", {}) != base.get("element_wards", {}):
                    errors.append(f"{vid}: authored wards changed")
                if item.get("price") != base.get("price"):
                    errors.append(f"{vid}: unintended price/gold-generation change")
                for key, value in base_props.items():
                    actual = (item.get("properties") or {}).get(key)
                    if not isinstance(actual, (int, float)) or not math.isfinite(float(actual)):
                        errors.append(f"{vid}: invalid property {key}")
                    elif float(value) > 0 and float(actual) + 1e-8 < float(value):
                        errors.append(f"{vid}: quality weakened {key}: {value}->{actual}")
                if quality in ("masterwork", "legendary") and not item.get("legendary_perk_v1150"):
                    errors.append(f"{vid}: missing special craft perk")
                # Restore from the exact persistent identifier. Tests use the
                # disposable predeploy world and leave no account mutations.
                snapshot = copy.deepcopy(item)
                items.pop(vid, None)
                recreated = ensure_crafting_quality_variant_v0332(vid)
                records["restored"] += 1
                checks += 1
                if recreated != snapshot:
                    errors.append(f"{vid}: changed properties after restart")

        # Endlessly scaling dungeon items must not add impossible 601+ gates,
        # lose authored power, or be reconstructed differently on reconnect.
        for class_name, *_ in CLASSES:
            candidates = shop_catalog.get(class_name, {}).get(600, ())
            if not candidates:
                continue
            base_id = next((iid for iid in candidates if iid in items and items[iid].get("slot") == "hands"), None)
            if not base_id:
                errors.append(f"{class_name}: no floor-600 baseline")
                continue
            previous = -1
            for rank in (1, 20, 100):
                vid = register_infinite_equipment_variant(base_id, "crypt", "b", rank)
                created.add(vid)
                item = items[vid]
                records["deep"] += 1
                checks += 6
                current = int(item.get("attack", 0) or 0) + int(item.get("magic_attack", 0) or 0)
                if current < previous:
                    errors.append(f"{vid}: deeper equipment lost power")
                previous = current
                if int(item.get("required_mastery", -1)) != 600:
                    errors.append(f"{vid}: invalid 601+ equipment gate")
                if item.get("price") != items[base_id].get("price"):
                    errors.append(f"{vid}: changed existing base price")
                if item.get("required_class") != items[base_id].get("required_class"):
                    errors.append(f"{vid}: lost class requirement")
                if int(item.get("sockets", -1)) > 6:
                    errors.append(f"{vid}: socket cap exceeded")
                snapshot = copy.deepcopy(item)
                items.pop(vid, None)
                rebuilt = ensure_infinite_equipment_variant(vid)
                records["restored"] += 1
                checks += 1
                if snapshot != rebuilt:
                    errors.append(f"{vid}: deep variant changed after restart")
        checks += 1
        if infinite_source_profile({"uoss_superboss": True, "crypt_floor": 1000}) is not None:
            errors.append("UOSS superboss loot incorrectly converted into deepq")
    finally:
        # Dynamic test IDs never become part of the shipping catalog.
        for vid in created:
            if vid not in baseline_keys:
                items.pop(vid, None)

    return {"version": "1.17.4", "checks": checks,
            "sources": records, "errors": errors, "error_count": len(errors)}

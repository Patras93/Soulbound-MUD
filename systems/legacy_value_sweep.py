# -*- coding: utf-8 -*-
"""Soulbound v1.13.25 - Global Legacy Value Sweep helpers.

This layer fixes old authored values without replacing modern authored systems:
- explicit legacy sell prices cannot undercut the current progression floor for
  ordinary loot and armor unless the item explicitly opts into an exact manual value;
- old mob families whose authored drops are effectively only a potion gain a
  characteristic material roll instead of another universal jackpot.
"""
from __future__ import annotations

from core.bootstrap_economy_professions import legacy_currency_to_coins
from core.progression_resources import v0190_resource_stage, v1138_resource_sale_base_coins
from systems.items_resources import economy_stage_anchor_v11314

V11325_LEGACY_VALUE_SWEEP_VERSION = "1.13.25"

V11325_ARMOR_RESALE_FRACTION = {
    "common": 0.025,
    "crafted": 0.035,
    "uncommon": 0.035,
    "rare": 0.050,
    "epic": 0.070,
    "legendary": 0.100,
    "mythic": 0.140,
    "unique": 0.160,
    "eternal": 0.180,
}

V11325_LOOT_RARITY_MULT = {
    "common": 0.50,
    "uncommon": 0.75,
    "rare": 1.25,
    "epic": 2.25,
    "legendary": 4.00,
    "mythic": 7.00,
    "unique": 10.00,
    "eternal": 12.00,
}

V11325_POTION_IDS = frozenset({
    "healing_potion",
    "mana_potion",
    "greater_healing_potion",
    "greater_mana_potion",
})


def _manual_sale_value_v11325(item) -> bool:
    item = item or {}
    return bool(
        item.get("manual_sale_value_exact")
        or item.get("sale_value_mode") == "manual"
    )


def legacy_explicit_sale_floor_v11325(item_id, item) -> int:
    """Return the minimum internal-silver sale value for old loot/EQ.

    Resources already have their own profession floor. Tools, quest items,
    currencies and explicitly manual prices are never changed here.
    """
    item = item or {}
    if _manual_sale_value_v11325(item):
        return 0

    item_type = str(item.get("type") or "").strip().lower()
    if item_type not in {"loot", "armor"}:
        return 0

    stage = max(1, min(600, int(v0190_resource_stage(item_id, item) or 1)))
    rarity = str(item.get("rarity") or "common").strip().lower()

    if item_type == "loot":
        return max(
            1,
            int(round(
                v1138_resource_sale_base_coins(stage)
                * V11325_LOOT_RARITY_MULT.get(rarity, 0.50)
            )),
        )

    fraction = V11325_ARMOR_RESALE_FRACTION.get(rarity, 0.035)
    return max(
        1,
        int(round(economy_stage_anchor_v11314(stage) * fraction)),
    )


def legacy_explicit_sale_value_v11325(item_id, item):
    """Floor an explicit sell_* value without changing its catalog fields."""
    item = item or {}
    authored = legacy_currency_to_coins(
        item.get("sell_silver", 0),
        item.get("sell_gold", 0),
        item.get("sell_mithril", 0),
    )
    floor = legacy_explicit_sale_floor_v11325(item_id, item)
    return max(0, int(authored), int(floor))


def _weak_authored_drop_v11325(template) -> bool:
    """True only for old ordinary mobs whose authored pool has little identity."""
    template = template or {}
    if template.get("training_dummy"):
        return False
    if any(template.get(flag) for flag in (
        "world_boss", "boss", "mini_boss", "boss_mechanic",
        "crypt_boss", "astral_boss", "mythic_crypt_boss",
        "mythic_astral_boss", "magitek_boss", "machine_boss",
        "giant_fortress_boss", "dungeon_boss", "instance_boss",
    )):
        return False
    if template.get("corpse_equipment_pool"):
        return False

    drops = template.get("drops") or {}
    if not isinstance(drops, dict) or not drops:
        return True
    meaningful = [
        item_id
        for item_id in drops
        if str(item_id) not in V11325_POTION_IDS
    ]
    return not meaningful


def legacy_identity_drop_spec_v11325(template, roll):
    """Return (item_id, chance) for weak legacy mob families only."""
    if not _weak_authored_drop_v11325(template):
        return None

    template = template or {}
    name = str(template.get("name") or "").casefold()
    target = str(template.get("quest_target") or "").casefold()

    if "szczur" in name or "rat" in name:
        item_id, chance = "legacy_rat_tail", 0.35
    elif "goblin" in name or target == "goblin":
        item_id, chance = "legacy_goblin_salvage", 0.28
    elif "bandyt" in name or target == "bandit":
        item_id, chance = "legacy_bandit_purse", 0.24
    elif any(token in name for token in (
        "ruin", "ruin", "starej straży", "starej strazy", "wartownik",
        "runiczny strażnik", "runiczny straznik",
    )):
        item_id, chance = "legacy_ancient_fragment", 0.26
    else:
        return None

    if float(roll) >= chance:
        return None
    return item_id, chance


def legacy_value_sweep_audit_v11325():
    errors = []

    low_loot = {
        "type": "loot", "sell_silver": 1, "generator_level": 100,
    }
    floored = legacy_explicit_sale_value_v11325("audit_loot", low_loot)
    if floored <= 1:
        errors.append("explicit loot value still bypasses progression floor")

    manual = {
        "type": "loot", "sell_silver": 1, "generator_level": 100,
        "manual_sale_value_exact": True,
    }
    if legacy_explicit_sale_value_v11325("audit_manual", manual) != 1:
        errors.append("manual sale value lost exactness")

    if legacy_identity_drop_spec_v11325(
        {"name": "Goblin", "drops": {"healing_potion": 0.1}},
        0.0,
    ) is None:
        errors.append("weak goblin family has no identity material")

    if legacy_identity_drop_spec_v11325(
        {"name": "Boss Goblinów", "world_boss": True, "drops": {}},
        0.0,
    ) is not None:
        errors.append("boss polluted by legacy identity-drop sweep")

    if legacy_identity_drop_spec_v11325(
        {"name": "Żywy Manekin", "training_dummy": True, "drops": {}},
        0.0,
    ) is not None:
        errors.append("training dummy receives legacy identity drop")

    return {
        "version": V11325_LEGACY_VALUE_SWEEP_VERSION,
        "error_count": len(errors),
        "errors": errors,
    }


LEGACY_VALUE_SWEEP_AUDIT_V11325 = legacy_value_sweep_audit_v11325()
if LEGACY_VALUE_SWEEP_AUDIT_V11325["error_count"]:
    raise RuntimeError(
        "Global Legacy Value Sweep Audit v1.13.25 failed: "
        + "; ".join(LEGACY_VALUE_SWEEP_AUDIT_V11325["errors"][:50])
    )

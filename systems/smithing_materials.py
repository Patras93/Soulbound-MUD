# -*- coding: utf-8 -*-
"""Soulbound v0.38.10 — canonical smithing materials for EQ upgrades.

Mithril is a currency denomination in current Soulbound, not a smithing ore/ingot.
EQ upgrades therefore use the same ingot progression as normal Kowalstwo recipes.
"""
from core.progression_600 import PROFESSION_MAX_LEVEL
from data.crafting_recipes import CRAFT_RECIPES
from data.items import ITEMS
from network.protocol_gameplay_utils import (
    V03042_EQ_UPGRADE_MAX, normalize_lookup_text, v03042_upgrade_required_smithing,
)
from systems.items_resources import BLACKSMITH_TIERS
from world.equipment_help import HELP_TOPICS


V03810_SMITHING_MATERIALS_VERSION = "0.38.10"


def v03810_upgrade_material_item_id(item, target_upgrade=1):
    """Return the canonical Kowalstwo ingot for an EQ upgrade.

    The material follows the actual required Kowalstwo level for the requested
    upgrade, so upgrading can naturally move into the next smithing tier.
    """
    required = max(1, min(
        PROFESSION_MAX_LEVEL,
        int(v03042_upgrade_required_smithing(item, target_upgrade)),
    ))
    tiers = sorted(
        BLACKSMITH_TIERS,
        key=lambda row: int(row.get("profession_level", 1) or 1),
    )
    chosen = tiers[0]
    for tier in tiers:
        if int(tier.get("profession_level", 1) or 1) <= required:
            chosen = tier
        else:
            break
    ingot_id = str(chosen.get("ingot") or "iron_ingot")
    if ingot_id not in ITEMS:
        return "iron_ingot"
    return ingot_id


def smithing_materials_audit_v03810():
    errors = []

    # No active smithing recipe may consume mithril as a material. Mithril is currency.
    bad_recipes = []
    for recipe_id, recipe in CRAFT_RECIPES.items():
        if str(recipe.get("category") or "") != "smithing":
            continue
        for ingredient_id in (recipe.get("ingredients") or {}):
            if "mithril" in normalize_lookup_text(ingredient_id):
                bad_recipes.append((recipe_id, ingredient_id))
    if bad_recipes:
        errors.append(f"smithing recipes still consume mithril: {bad_recipes[:10]}")

    # Every upgrade stage 1..600 / +1..+10 must resolve to a real non-mithril ingot.
    bad_upgrade = []
    for level in range(1, 601):
        sample = {
            "required_character_level": level,
            "required_mastery": level,
            "type": "armor",
            "slot": "charm",
            "rarity": "common",
        }
        for target in range(1, V03042_EQ_UPGRADE_MAX + 1):
            iid = v03810_upgrade_material_item_id(sample, target)
            if iid not in ITEMS or "mithril" in normalize_lookup_text(iid) or "mithril" in normalize_lookup_text(ITEMS.get(iid, {}).get("name", "")):
                bad_upgrade.append((level, target, iid))
                if len(bad_upgrade) >= 20:
                    break
        if len(bad_upgrade) >= 20:
            break
    if bad_upgrade:
        errors.append(f"upgrade material ladder invalid: {bad_upgrade}")

    # Regression example reported by the player: level 80 +0 -> +1 must be Gold, never Mithril.
    level80 = {"required_character_level": 80, "required_mastery": 80, "type": "armor", "slot": "charm"}
    resolved80 = v03810_upgrade_material_item_id(level80, 1)
    if resolved80 != "gold_ingot":
        errors.append(f"level 80 +1 material={resolved80}, expected gold_ingot")

    return {
        "version": V03810_SMITHING_MATERIALS_VERSION,
        "smithing_recipe_count": sum(1 for r in CRAFT_RECIPES.values() if str(r.get("category") or "") == "smithing"),
        "level80_upgrade_material": resolved80,
        "error_count": len(errors),
        "errors": errors,
    }


SMITHING_MATERIALS_AUDIT_V03810 = smithing_materials_audit_v03810()
if SMITHING_MATERIALS_AUDIT_V03810["error_count"]:
    raise RuntimeError(
        "Smithing Materials Audit v0.38.10 failed: "
        + "; ".join(SMITHING_MATERIALS_AUDIT_V03810["errors"][:100])
    )

HELP_TOPICS.setdefault("kowalstwo", []).append(
    "v0.38.10: ulepszanie EQ +1..+10 korzysta z normalnych sztabek Kowalstwa. "
    "Mithril pozostaje walutą i nie jest składnikiem receptur ani materiałem kosztu ulepszania EQ."
)
HELP_TOPICS.setdefault("ulepszanie eq", []).append(
    "Materiał ulepszenia jest dobierany z drabinki Kowalstwa według wymaganego poziomu: "
    "żelazo, srebro, złoto, kobalt, runiczny metal, smocza stal, astral, Pustka, eternium i materiały 220-600."
)

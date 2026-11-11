"""Regression of actual NPC resource prices, not merely catalogue metadata."""


def audit_profession_market_v1148():
    from core.mines_threat import ITEMS
    from systems.items_resources import (
        FISH_RESOURCE_IDS, ORE_RESOURCE_IDS, WOOD_RESOURCE_IDS, HERB_RESOURCE_IDS,
        FISH_STORAGE_IDS, WOOD_STORAGE_IDS, HERB_STORAGE_IDS,
        profession_resource_market_value_v1148 as market,
    )
    from systems.equipment_crafting import MINING_STORAGE_IDS
    from player.session_mixins.sales import SessionSalesMixin

    errors = []
    checks = 0
    groups = {
        "fish": FISH_RESOURCE_IDS,
        "ore": MINING_STORAGE_IDS,
        "wood": WOOD_RESOURCE_IDS,
        "herb": HERB_RESOURCE_IDS,
    }
    sales = SessionSalesMixin()
    for category, ids in groups.items():
        seen = {}
        for item_id in sorted(ids):
            item = ITEMS.get(item_id)
            if not item or item.get("rare_resource_variant"):
                continue
            calculated = market(item_id, item, category=category)
            checks += 1
            if calculated <= 0:
                errors.append(f"{category}/{item_id}: nonpositive price")
            if calculated in seen:
                errors.append(f"{category}/{item_id}: price collision with {seen[calculated]}")
            seen[calculated] = item_id
            sold = sales.generic_item_sale_value(item_id, item)
            if int(sold["silver"]) != calculated or int(sold["gold"]) or int(sold["mithril"]):
                errors.append(f"{category}/{item_id}: single sale != catalog market")
                
    for item_id in sorted(FISH_STORAGE_IDS | WOOD_STORAGE_IDS | HERB_STORAGE_IDS):
        item = ITEMS.get(item_id)
        if not item or not item.get("rare_resource_variant"):
            continue
        base_id = str(item.get("base_resource_id") or "")
        base = ITEMS.get(base_id)
        if not base:
            errors.append(f"rare/{item_id}: no base")
            continue
        price = market(item_id, item)
        base_price = market(base_id, base)
        factor = max(1.0, float(item.get("rare_value_multiplier", 1) or 1))
        checks += 1
        if price != round(base_price * factor):
            errors.append(f"rare/{item_id}: multiplier applied incorrectly")
        if factor > 1 and price <= base_price:
            errors.append(f"rare/{item_id}: not more valuable")
        sold = sales.generic_item_sale_value(item_id, item)
        if int(sold["silver"]) != price:
            errors.append(f"rare/{item_id}: NPC sale mismatch")

    # Two endgame fish originally authored at precisely 25 gold each.
    trout = market("soulfin_trout", ITEMS["soulfin_trout"], "fish")
    carp = market("crystal_carp", ITEMS["crystal_carp"], "fish")
    checks += 1
    if trout == carp:
        errors.append("fish: Soulfin Trout and Crystal Carp remain flat-priced")

    return {"checks": checks, "errors": errors, "error_count": len(errors),
            "groups": {name: len(ids) for name, ids in groups.items()}}

# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _upgrade_named_unique_from_source_v11327(item_id, mob_id):
    item = ITEMS.get(item_id)
    template = MOB_TEMPLATES.get(mob_id)
    if not item or not template:
        return None

    stage = _boss_source_stage_v11327(template)
    budget = equipment_progression_budget_v1138(stage)
    affix = str(item.get("affix") or "")
    current_amount = max(0, int(item.get("affix_amount", 0) or 0))
    if affix == "hp":
        target_amount = max(current_amount, int(round(budget * 0.45)) * 10)
    elif affix == "mana":
        target_amount = max(current_amount, int(round(budget * 0.45)) * 8)
    else:
        target_amount = max(current_amount, int(round(budget * 0.45)))
    item["affix_amount"] = target_amount

    current_defense = max(0, int(item.get("defense", 0) or 0))
    item["defense"] = max(
        current_defense,
        current_defense + max(1, int(round(equipment_defense_step_v1138(stage) * 0.75))),
    )

    properties = dict(item.get("properties") or {})
    for key, value in _named_unique_property_v11327(affix, stage).items():
        properties[key] = max(float(properties.get(key, 0.0) or 0.0), float(value))
    item["properties"] = properties

    sockets = 1
    if stage >= 50:
        sockets = 2
    if stage >= 100:
        sockets = 3
    item["sockets"] = max(int(item.get("sockets", 0) or 0), sockets)

    item["source_progression_stage"] = stage
    item["source_progression_floor_v11327"] = True
    item["equipment_identity_source"] = "world_boss"
    item["equipment_identity_role"] = "named_unique"
    item["equipment_identity_label"] = (
        f"World Boss — nazwany unikat skalowany do źródła (etap {stage})"
    )
    return stage


def loot_source_progression_audit_v11327():
    errors = []
    rows = {}
    for item_id, mob_id in LEGACY_NAMED_UNIQUE_SOURCES_V11327.items():
        item = ITEMS.get(item_id) or {}
        template = MOB_TEMPLATES.get(mob_id) or {}
        stage = _boss_source_stage_v11327(template)
        budget = equipment_progression_budget_v1138(stage)
        affix = str(item.get("affix") or "")
        amount = int(item.get("affix_amount", 0) or 0)
        expected = int(round(budget * 0.45))
        if affix == "hp":
            expected *= 10
        elif affix == "mana":
            expected *= 8
        if amount < max(1, expected):
            errors.append(f"{item_id}: affix {amount} < source floor {expected}")
        if int(item.get("source_progression_stage", 0) or 0) != stage:
            errors.append(f"{item_id}: missing source stage {stage}")
        if not item.get("properties"):
            errors.append(f"{item_id}: missing source-scaled property")
        if int(item.get("sockets", 0) or 0) < 1:
            errors.append(f"{item_id}: missing boss-unique socket")
        rows[item_id] = {
            "stage": stage,
            "affix_amount": amount,
            "defense": int(item.get("defense", 0) or 0),
            "sockets": int(item.get("sockets", 0) or 0),
            "properties": dict(item.get("properties") or {}),
        }

    # Crypt rarity must remain a real progression ladder.
    _rarity_order = ("common", "rare", "epic", "legendary", "mythic")
    _prop_floor = {
        "common": 0.5, "rare": 1.0, "epic": 1.5,
        "legendary": 2.5, "mythic": 4.0,
    }
    if any(
        _prop_floor[_rarity_order[i]] >= _prop_floor[_rarity_order[i + 1]]
        for i in range(len(_rarity_order) - 1)
    ):
        errors.append("crypt rarity property ladder is not strictly increasing")

    return {
        "version": "1.13.27",
        "legacy_named_uniques": rows,
        "error_count": len(errors),
        "errors": errors,
    }


def build_crypt_loot_variants():
    slot_pattern = "|".join(re.escape(slot) for slot in CLASS_EQUIPMENT_SLOT_DEFS)
    base_ids = [
        item_id
        for item_id, item in list(ITEMS.items())
        if re.fullmatch(rf"crypt_t\d+_(?:{slot_pattern})", item_id)
    ]

    for base_item_id in base_ids:
        base_item = ITEMS[base_item_id]
        m = re.fullmatch(
            rf"crypt_t(\d+)_({slot_pattern})",
            base_item_id,
        )
        if not m:
            continue

        tier = int(m.group(1))
        slot = m.group(2)

        # Stary item bazowy pozostaje kompatybilny i jest zwykłym
        # elementem setu bez affixu.
        base_item["rarity"] = "common"
        base_item["rarity_name"] = "Zwykły"
        base_item["crypt_set_tier"] = tier
        base_item["crypt_base_item"] = base_item_id
        base_item["source_progression_stage"] = max(1, min(800, tier * 10))
        base_item["affix"] = None
        base_item["affix_amount"] = 0
        base_item["equipment_identity_source"] = "crypt"
        base_item["equipment_identity_role"] = "random_affix"
        base_item["equipment_identity_label"] = (
            "Krypta — polowanie na rarity i losowy affix"
        )

        for rarity_key, rarity in CRYPT_RARITIES.items():
            for affix_key, affix_name in CRYPT_AFFIXES.items():
                amount = crypt_affix_amount(
                    tier, rarity_key, affix_key
                )
                variant_id = crypt_variant_id(
                    base_item_id, rarity_key, affix_key
                )
                mastery = max(1, min(800, tier * 10))
                budget = equipment_progression_budget_v1138(mastery)
                rarity_power = {
                    "common": 0.03,
                    "rare": 0.045,
                    "epic": 0.06,
                    "legendary": 0.08,
                    "mythic": 0.11,
                }.get(rarity_key, 0.03)
                rarity_defense = {
                    "common": 0.00,
                    "rare": 0.08,
                    "epic": 0.12,
                    "legendary": 0.18,
                    "mythic": 0.25,
                }.get(rarity_key, 0.00)
                defense = (
                    int(base_item.get("defense", 0))
                    + int(rarity["defense_bonus"])
                    + int(round(
                        equipment_defense_step_v1138(mastery)
                        * rarity_defense
                    ))
                )
                flat_power = max(
                    0,
                    int(round(
                        budget
                        * rarity_power
                        * float(MATERIAL_SLOT_POWER_SCALE.get(slot, 0.50))
                    )),
                )
                attack = (
                    flat_power if affix_key in {"strength", "dexterity"} else 0
                )
                magic_attack = (
                    flat_power if affix_key in {"intelligence", "willpower"} else 0
                )
                sockets = {
                    "common": 0,
                    "rare": 1,
                    "epic": 2,
                    "legendary": 3,
                    "mythic": 4,
                }.get(rarity_key, 0)
                if mastery >= 300 and rarity_key in {"legendary", "mythic"}:
                    sockets = min(5, sockets + 1)
                prop_key = {
                    "strength": "physical_damage_pct",
                    "dexterity": "physical_damage_pct",
                    "constitution": "physical_defense_pct",
                    "intelligence": "magic_damage_pct",
                    "willpower": "magic_defense_pct",
                    "hp": "max_hp_pct",
                    "mana": "max_mana_pct",
                }.get(affix_key)
                prop_value = {
                    "common": 0.5,
                    "rare": 1.0,
                    "epic": 1.5,
                    "legendary": 2.5,
                    "mythic": 4.0,
                }.get(rarity_key, 0.5)
                variant_name = (
                    f"{base_item['name']} "
                    f"[{rarity['name']}, {affix_name} +{amount}]"
                )
                _catalog_mut.catalog_assign({
                    "name": variant_name,
                    "type": "armor",
                    "slot": slot,
                    "defense": defense,
                    "attack": attack,
                    "magic_attack": magic_attack,
                    "sockets": sockets,
                    "properties": {prop_key: prop_value} if prop_key else {},
                    "price": None,
                    # v0.61.2: opis wariantu Krypty jest generowany przy wyświetleniu.
                    "rarity": rarity_key,
                    "rarity_name": rarity["name"],
                    "crypt_set_tier": tier,
                    "crypt_base_item": base_item_id,
                    "source_progression_stage": mastery,
                    "affix": affix_key,
                    "affix_amount": amount,
                    "equipment_identity_source": "crypt",
                    "equipment_identity_role": "random_affix",
                    "equipment_identity_label": (
                        "Krypta — rarity, losowy affix i rosnące sockety"
                    ),
                }, 'ITEMS', ITEMS, (variant_id,))


def crypt_rarity_progression_audit_v11329():
    errors = []
    scores = {
        "common": 0.0,
        "rare": 1.0,
        "epic": 2.0,
        "legendary": 3.0,
        "mythic": 4.0,
    }

    def expected_score(is_boss, mastery):
        weights = crypt_rarity_weights_v11329(is_boss, mastery)
        total = sum(weights.values())
        return sum(
            scores[key] * weight for key, weight in weights.items()
        ) / max(1e-9, total)

    stages = (1, 100, 200, 300, 400, 500, 600)
    for is_boss in (False, True):
        values = [expected_score(is_boss, stage) for stage in stages]
        if any(values[i] >= values[i + 1] for i in range(len(values) - 1)):
            errors.append(
                ("boss" if is_boss else "regular")
                + " Crypt rarity does not improve with depth"
            )

    for stage in stages:
        if expected_score(True, stage) <= expected_score(False, stage):
            errors.append(
                f"Crypt boss rarity is not stronger at stage {stage}"
            )
            break

    deep_regular = crypt_rarity_weights_v11329(False, 600)
    deep_boss = crypt_rarity_weights_v11329(True, 600)
    if deep_regular["mythic"] < 7.0:
        errors.append("deep regular Crypt mythic weight below 7")
    if deep_boss["mythic"] < 22.0:
        errors.append("deep boss Crypt mythic weight below 22")

    return {
        "version": "1.13.29",
        "error_count": len(errors),
        "errors": errors,
    }


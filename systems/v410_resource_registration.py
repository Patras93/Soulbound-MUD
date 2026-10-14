# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _blacksmith_masterwork_profile_v1138(level, slot):
    level = max(1, min(800, int(level or 1)))
    base_budget = equipment_progression_budget_v1138(level)
    stat_budget = max(2, int(round(base_budget * 0.65)))
    first, second = BLACKSMITH_MASTERWORK_STAT_PROFILE[slot]
    first_amount = max(1, int(round(stat_budget * 0.55)))
    second_amount = max(1, stat_budget - first_amount)
    stats = {first: first_amount, second: second_amount}

    prop = BLACKSMITH_MASTERWORK_PROPERTY[slot]
    prop_value = round(
        0.50 + 2.50 * ((level - 1) / 599.0) ** 0.80,
        2,
    )
    properties = {prop: prop_value}

    attack = 0
    magic_attack = 0
    if slot == "hands":
        attack = max(1, int(round(base_budget * 0.10)))
    elif slot == "feet":
        attack = max(0, int(round(base_budget * 0.04)))
    elif slot == "charm":
        magic_attack = max(1, int(round(base_budget * 0.10)))
    elif slot == "head":
        magic_attack = max(0, int(round(base_budget * 0.04)))

    if level >= 500:
        sockets = 5
    elif level >= 360:
        sockets = 4
    elif level >= 200:
        sockets = 3
    elif level >= 100:
        sockets = 2
    else:
        sockets = 1

    return {
        "stats": stats,
        "properties": properties,
        "attack": attack,
        "magic_attack": magic_attack,
        "sockets": sockets,
    }


def _register_blacksmith_items():
    extra_ingots = (
        ("cobalt_ingot", "Kobaltowa sztabka"),
        ("runestone_ingot", "Runiczna sztabka"),
        ("dragonsteel_ingot", "Sztabka Smoczej Stali"),
        ("astral_ingot", "Astralna sztabka"),
        ("void_ingot", "Sztabka Pustki"),
        ("eternium_ingot", "Sztabka Eternium"),
    )
    for item_id, name in extra_ingots:
        _catalog_mut.catalog_assign({
            "name": name,
            "type": "craft_material",
            "price": None,
            "desc": (
                "Przetopiony metal używany w zaawansowanym "
                "Kowalstwie."
            ),
        }, 'ITEMS', ITEMS, (item_id,))

    for tier_number, tier in enumerate(BLACKSMITH_TIERS, 1):
        for slot, (
            slot_name, defense_delta, _ingot_cost
        ) in BLACKSMITH_SLOT_DEFS.items():
            item_id = (
                f"smith_{tier['key']}_{slot}"
            )
            level = int(tier["profession_level"])
            defense = max(
                1,
                int(tier["base_defense"])
                + int(defense_delta)
                + int(round(equipment_defense_step_v1138(level) * 1.10)),
            )
            masterwork = _blacksmith_masterwork_profile_v1138(level, slot)
            _catalog_mut.catalog_assign({
                "name": (
                    f"{slot_name} {tier['name']} "
                    f"[Kowalstwo Tier {tier_number}]"
                ),
                "type": "armor",
                "slot": slot,
                "defense": defense,
                "attack": int(masterwork["attack"]),
                "magic_attack": int(masterwork["magic_attack"]),
                "stats": dict(masterwork["stats"]),
                "properties": dict(masterwork["properties"]),
                "sockets": int(masterwork["sockets"]),
                "crafted_masterwork": True,
                "equipment_identity_source": "blacksmith",
                "source_progression_stage": level,
                "equipment_identity_role": "masterwork_customization",
                "equipment_identity_label": (
                    "Kowalstwo — masterwork, właściwość materiałowa i sockety"
                ),
                "price": None,
                "desc": (
                    f"Wyposażenie wykute przez Kowala. "
                    f"Kowalstwo level {tier['profession_level']}+. "
                    "Młot Rzemieślniczy wpływa na dostęp do lepszych materiałów "
                    "i bonus produktu. Tier Młota musi spełniać próg receptury; "
                    "pojedynczy level Młota wewnątrz Tieru nie skraca czasu. "
                    f"Obrona +{defense}. Masterwork: statystyki, właściwość materiałowa "
                    f"i {int(masterwork['sockets'])} gniazd(a) do dalszego dopracowania."
                ),
                "blacksmith_tier": tier_number,
                "blacksmith_material": tier["key"],
            }, 'ITEMS', ITEMS, (item_id,))


def _register_corpse_material_items():
    global CORPSE_MATERIAL_ITEM_IDS
    CORPSE_MATERIAL_ITEM_IDS = {}
    all_names = set()
    for tier_index, tier in enumerate(CORPSE_MATERIAL_TIERS, 1):
        ids = []
        for slot in CORPSE_MATERIAL_SLOT_DEFS:
            seen_stats = set()
            for variant_index in range(1, CORPSE_RANDOM_VARIANTS_PER_SLOT + 1):
                item_id = f"corpse_{tier['key']}_{slot}_v{variant_index:02d}"
                profile = None
                for salt in range(512):
                    (
                        defense, stats, properties,
                        attack, magic_attack, sockets, quality,
                    ) = _material_random_profile(
                        tier, slot, variant_index, salt=salt
                    )
                    stat_sig = tuple(sorted((str(k), int(v)) for k, v in stats.items()))
                    if stat_sig not in seen_stats:
                        profile = (
                            defense, stats, properties, attack,
                            magic_attack, sockets, quality, stat_sig,
                        )
                        break
                if profile is None:
                    raise RuntimeError(
                        f"v0.30.37: nie udało się utworzyć unikalnych statów {tier['key']} {slot} wariant {variant_index}"
                    )
                (
                    defense, stats, properties, attack,
                    magic_attack, sockets, quality, stat_sig,
                ) = profile
                seen_stats.add(stat_sig)
                required_mastery = corpse_material_variant_mastery(tier["key"], variant_index)
                name = _material_variant_title(tier, slot, stats, variant_index, required_mastery)
                if str(name).casefold() in all_names:
                    raise RuntimeError(f"v0.30.37: powtórzona nazwa materiałowego EQ: {name}")
                all_names.add(str(name).casefold())
                stat_text = ", ".join(
                    f"{MATERIAL_STAT_NAMES.get(stat, stat)} +{amount}" for stat, amount in stats.items()
                )
                prop_text = ", ".join(
                    f"{MATERIAL_PROPERTY_NAMES.get(prop, prop)} +{amount}%" for prop, amount in properties.items()
                )
                crit_note = (
                    " Zręczność z tej części zwiększa także szansę na trafienie krytyczne."
                    if stats.get("dexterity", 0) > 0 else ""
                )
                _catalog_mut.catalog_assign({
                    "name": name,
                    "type": "armor",
                    "slot": slot,
                    "defense": defense,
                    "attack": int(attack),
                    "magic_attack": int(magic_attack),
                    "sockets": int(sockets),
                    "drop_quality": round(float(quality), 3),
                    "price": None,
                    "rarity": tier["rarity"],
                    "rarity_name": tier["rarity_name"],
                    "stats": stats,
                    "properties": properties,
                    "corpse_material": tier["key"],
                    "corpse_material_tier": tier_index,
                    "corpse_random_variant": variant_index,
                    "required_mastery": required_mastery,
                    "source_progression_stage": required_mastery,
                    "equipment_identity_source": "corpse_drop",
                    "equipment_identity_role": "random_material_variant",
                    "equipment_identity_label": (
                        "Drop z moba — losowy materiał, wariant i profil "
                        + str(tier["identity"])
                    ),
                    "mastery_requirement_scope": "active_class",
                    # v0.61.2: opis materiałowego EQ jest składany na żądanie.
                }, 'ITEMS', ITEMS, (item_id,))
                ids.append(item_id)
        CORPSE_MATERIAL_ITEM_IDS[tier["key"]] = tuple(ids)


def _register_rare_resource_variants():
    groups = (
        (
            "fish",
            tuple(FISH_RESOURCE_IDS),
            FISH_RARE_VARIANTS,
        ),
        (
            "wood",
            tuple(WOOD_RESOURCE_IDS),
            WOOD_RARE_VARIANTS,
        ),
        (
            "herb",
            tuple(HERB_RESOURCE_IDS),
            HERB_RARE_VARIANTS,
        ),
    )

    for category, base_ids, variants in groups:
        for base_item_id in base_ids:
            base_item = ITEMS.get(base_item_id)
            if not base_item:
                continue

            for key, definition in variants.items():
                variant_id = rare_resource_variant_id(
                    category, key, base_item_id
                )
                value_mult = int(definition["value_mult"])
                item = {
                    "name": (
                        definition["name_prefix"]
                        + base_item["name"]
                    ),
                    "type": "resource",
                    "price": None,
                    "desc": (
                        f"{definition['desc']} "
                        f"Bazowy zasób: {base_item['name']}. "
                        f"Wartość sprzedaży x{value_mult}."
                    ),
                    "resource_category": category,
                    "base_resource_id": base_item_id,
                    "rare_resource_variant": key,
                    "rare_resource_label": definition["label"],
                    "rare_value_multiplier": value_mult,
                }
                item.update(
                    _scaled_resource_sale_fields(
                        base_item, value_mult
                    )
                )
                _catalog_mut.catalog_assign(item, 'ITEMS', ITEMS, (variant_id,))


# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def class_equipment_split_stat_budget(class_name, legacy_amount, slot=None, style_index=1):
    # v1.13.6: każdy klasowy element ma trzy realne statystyki bazowe.
    # Łączny budżet pozostaje kontrolowany; minimalnie 3, aby żadna oś nie
    # mogła spaść do zera nawet na Tierze 1.
    budget = max(3, int(legacy_amount or 0))
    profile = class_equipment_profile(class_name)
    ratio = float(profile.get("primary_ratio", 0.50))
    ratio += float(CLASS_EQUIPMENT_SLOT_PRIMARY_BIAS.get(str(slot or ""), 0.0))
    ratio = max(0.20, min(0.80, ratio))

    primary_stat, secondary_stat, tertiary_stat = class_equipment_base_stat_triplet(class_name)

    # Najpierw gwarantujemy po 1 dla wszystkich trzech osi. Pozostały budżet
    # wzmacnia profil klasy: primary_ratio rozdziela dodatkowe punkty między
    # dwie główne osie, a Kondycja zawsze pozostaje pełnoprawną trzecią osią.
    remaining = budget - 3
    constitution_extra = int(round(remaining * 0.25))
    main_pool = remaining - constitution_extra
    primary_extra = int(round(main_pool * ratio))
    primary_extra = max(0, min(main_pool, primary_extra))
    secondary_extra = main_pool - primary_extra

    primary_amount = 1 + primary_extra
    secondary_amount = 1 + secondary_extra
    tertiary_amount = 1 + constitution_extra

    # Style 2 przenosi część CON w ofensywne osie; style 3 robi odwrotnie.
    # Łączny budżet pozostaje identyczny, więc wybór jest buildem, nie prostym
    # "numer 3 ma więcej wszystkiego".
    style = class_equipment_style_profile(class_name, style_index)
    shift_ratio = float(style.get("stat_shift", 0.0) or 0.0)
    shift_points = max(0, int(round(budget * abs(shift_ratio))))
    if shift_ratio > 0.0 and shift_points > 0:
        moved = min(max(0, tertiary_amount - 1), shift_points)
        primary_gain = int(round(moved * 0.70))
        secondary_gain = moved - primary_gain
        tertiary_amount -= moved
        primary_amount += primary_gain
        secondary_amount += secondary_gain
    elif shift_ratio < 0.0 and shift_points > 0:
        movable_primary = max(0, primary_amount - 1)
        movable_secondary = max(0, secondary_amount - 1)
        wanted_primary = int(round(shift_points * 0.60))
        moved_primary = min(movable_primary, wanted_primary)
        moved_secondary = min(
            movable_secondary,
            max(0, shift_points - moved_primary),
        )
        # Jeżeli jedna oś nie miała wystarczającej liczby punktów, dobierz resztę
        # z drugiej, nadal nigdy nie schodząc poniżej 1.
        remaining_shift = shift_points - moved_primary - moved_secondary
        if remaining_shift > 0:
            extra_primary = min(
                max(0, movable_primary - moved_primary),
                remaining_shift,
            )
            moved_primary += extra_primary
            remaining_shift -= extra_primary
        if remaining_shift > 0:
            extra_secondary = min(
                max(0, movable_secondary - moved_secondary),
                remaining_shift,
            )
            moved_secondary += extra_secondary
        moved = moved_primary + moved_secondary
        primary_amount -= moved_primary
        secondary_amount -= moved_secondary
        tertiary_amount += moved

    return (
        primary_stat, primary_amount,
        secondary_stat, secondary_amount,
        tertiary_stat, tertiary_amount,
    )


def _register_class_equipment_shops():
    for class_name, definition in CLASS_EQUIPMENT_SETS.items():
        CLASS_SHOP_CLASSES_BY_ROOM.setdefault(definition["room"], []).append(class_name)
        per_tier = CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.setdefault(class_name, {})
        styles = CLASS_EQUIPMENT_STYLES.get(class_name, (definition["set_name"],))

        for tier_index, required_mastery in enumerate(CLASS_EQUIPMENT_MASTERY_LEVELS):
            tier_items = []
            # v1.13.8: każdy nowy set ma być odczuwalny także defensywnie.
            # Early game rośnie spokojnie, od 50+ kolejne progi dają już
            # wyraźniejszą ochronę. Dzięki capowi redukcji zwykłe moby nie
            # stają się całkowicie bezbronne, a bossowie pozostają groźni.
            defense_step = equipment_defense_step_v1138(required_mastery)
            # v0.36.0: każdy próg 1/10/20/30/.../600 ma inny realny
            # budżet podstawowych statów. Wcześniej affix rósł co drugi próg,
            # więc np. część niskiego EQ 1/10/20 mogła mieć identyczne
            # Siła/Kondycja albo Inteligencja/Siła Woli. Teraz łączny budżet
            # rośnie dokładnie o 1 na każdym kolejnym Tierze, zachowując
            # klasowy ratio i bias konkretnego slotu.
            # Ceny rosną wyraźnie wraz z Biegłością, ale pozostają w istniejącej ekonomii srebra.
            price_multiplier = 1 + tier_index + (tier_index * tier_index) // 4

            for style_index, style_name in enumerate(styles, 1):
                for slot, (slot_name, defense_delta, base_price) in CLASS_EQUIPMENT_SLOT_DEFS.items():
                    # Pierwsza linia zachowuje stare ID 1:1.
                    style_suffix = "" if style_index == 1 else f"_s{style_index}"
                    if required_mastery == 1:
                        item_id = f"class_{definition['prefix']}{style_suffix}_{slot}"
                    else:
                        item_id = f"class_{definition['prefix']}{style_suffix}_m{required_mastery}_{slot}"

                    if slot in ("necklace", "relic"):
                        base_affix = 3
                    elif slot in (
                        "ring", "charm", "earring", "shoulders", "belt", "cloak",
                        "bracers", "bracelet", "accessory",
                    ):
                        base_affix = 2
                    else:
                        base_affix = 1

                    # Minimalny Tier zawsze ma trzy statystyki (budżet >= 3),
                    # a każdy następny próg dodaje kolejny pełny punkt budżetu.
                    legacy_affix_amount = class_equipment_stat_budget(required_mastery, slot)
                    (
                        primary_stat, primary_amount,
                        secondary_stat, secondary_amount,
                        tertiary_stat, tertiary_amount,
                    ) = class_equipment_split_stat_budget(
                        class_name, legacy_affix_amount, slot, style_index
                    )
                    expected_stats = (
                        {"intelligence", "willpower", "constitution"}
                        if class_type_for_name(class_name) == "magic"
                        else {"strength", "dexterity", "constitution"}
                    )
                    actual_stats = {primary_stat, secondary_stat, tertiary_stat}
                    if actual_stats != expected_stats:
                        raise RuntimeError(
                            f"Class EQ stat triplet mismatch: {class_name} {slot}: "
                            f"{sorted(actual_stats)} != {sorted(expected_stats)}"
                        )
                    style_profile = class_equipment_style_profile(class_name, style_index)
                    raw_defense = (
                        int(definition["base_defense"])
                        + int(defense_delta)
                        + defense_step
                    )
                    defense = max(
                        1,
                        int(round(
                            raw_defense
                            * float(style_profile["defense_multiplier"])
                        )),
                    )
                    flat_power = class_equipment_flat_power_channels(
                        class_name, required_mastery, slot, style_index
                    )
                    item_properties = _merge_equipment_properties_v11326(
                        class_equipment_profile_properties(
                            class_name, required_mastery, slot
                        ),
                        class_equipment_style_properties_v11326(
                            class_name, required_mastery, slot, style_index
                        ),
                    )
                    # v1.13.14: historyczna cena jest minimum, ale realny
                    # koszt śledzi wspólną krzywą zarobków 1-600.
                    legacy_price = max(
                        1, int(base_price) * int(price_multiplier)
                    )
                    price = max(
                        legacy_price,
                        class_equipment_shop_price_v11314(
                            required_mastery, base_price
                        ),
                    )
                    tier_label = _class_equipment_tier_label(required_mastery)

                    _catalog_mut.catalog_assign({
                        "name": (
                            f"{slot_name} {style_name}"
                            if required_mastery == 1
                            else f"{slot_name} {style_name} {_class_equipment_tier_label(required_mastery)}"
                        ),
                        "type": "armor",
                        "slot": slot,
                        "defense": defense,
                        "attack": int(flat_power["attack"]),
                        "magic_attack": int(flat_power["magic_attack"]),
                        "properties": dict(item_properties),
                        "equipment_identity_source": "class_shop",
                        "source_progression_stage": required_mastery,
                        "equipment_identity_role": class_equipment_style_role(
                            class_name, style_index
                        ),
                        "equipment_identity_label": (
                            "Sklep klasowy — przewidywalny set i profil "
                            + class_equipment_style_role(class_name, style_index)
                        ),
                        "price": price,
                        "currency": "silver",
                        "rarity": "crafted",
                        "rarity_name": _class_equipment_rarity_name(required_mastery),
                        "affix": primary_stat,
                        "affix_amount": primary_amount,
                        "stats": {
                            secondary_stat: secondary_amount,
                            tertiary_stat: tertiary_amount,
                            **(mec_hybrid_extra_stats(legacy_affix_amount) if class_name == "Mec" else {}),
                        },
                        "class_base_stat_pair": (primary_stat, secondary_stat),
                        "class_base_stat_triplet": (
                            primary_stat, secondary_stat, tertiary_stat,
                        ),
                        "required_class": class_name,
                        "required_mastery": required_mastery,
                        "class_shop_item": True,
                        "class_set_name": style_name,
                        "class_set_piece": slot,
                        "class_equipment_tier": tier_index + 1,
                        "class_equipment_style": style_index,
                        # v0.61.2: opis zwykłego klasowego EQ jest składany na żądanie
                        # z istniejących pól. Nie przechowujemy 38k długich kopii tekstu w RAM.
                    }, 'ITEMS', ITEMS, (item_id,))
                    CLASS_EQUIPMENT_ITEM_IDS.add(item_id)
                    tier_items.append(item_id)

            per_tier[required_mastery] = tuple(tier_items)

        # Statyczna lista zachowuje pełną ofertę Tier 1 dla zgodności starych miejsc kodu.
        # Interfejs sklepu dynamicznie pokazuje najlepszy odblokowany Tier.
        CLASS_SHOP_ITEMS_BY_ROOM[definition["room"]].extend(per_tier[1])


def _register_legendary_class_loot():
    for class_name, definition in CLASS_EQUIPMENT_SETS.items():
        affix, base_defense = _legendary_class_loot_stat_profile(class_name)
        set_name = f"Legendy {definition['set_name']}"
        class_slug = definition["prefix"]
        class_sets = LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER.setdefault(class_name, {})
        relics = LEGENDARY_CLASS_RELIC_BY_CLASS_TIER.setdefault(class_name, {})

        for mastery in LEGENDARY_CLASS_LOOT_TIERS:
            tier_index = max(1, mastery // 10)
            defense_step = (tier_index + 1) // 2
            affix_step = tier_index // 2
            tier_items = []
            for slot, (slot_name, defense_delta, _base_price) in CLASS_EQUIPMENT_SLOT_DEFS.items():
                item_id = f"legendset_{class_slug}_m{mastery}_{slot}"
                defense = max(1, base_defense + int(defense_delta) + defense_step + 1)
                base_affix = 3 if slot in ("necklace", "relic") else 2 if slot in ("ring", "charm", "earring", "shoulders", "belt", "cloak", "bracers") else 1
                legacy_affix_amount = base_affix + affix_step + 1
                (
                    primary_stat, primary_amount,
                    secondary_stat, secondary_amount,
                    tertiary_stat, tertiary_amount,
                ) = class_equipment_split_stat_budget(
                    class_name, legacy_affix_amount, slot
                )
                expected_stats = (
                    {"intelligence", "willpower", "constitution"}
                    if class_type_for_name(class_name) == "magic"
                    else {"strength", "dexterity", "constitution"}
                )
                if {primary_stat, secondary_stat, tertiary_stat} != expected_stats:
                    raise RuntimeError(
                        f"Legendary class EQ stat triplet mismatch: {class_name} {slot}"
                    )
                legendary_properties_v11326 = (
                    legendary_class_set_properties_v11326(
                        class_name, mastery, slot
                    )
                )
                legendary_flat_power_v11338 = (
                    legendary_class_equipment_flat_power_channels_v11338(
                        class_name, mastery, slot
                    )
                )
                _catalog_mut.catalog_assign({
                    "name": f"{slot_name} {set_name} +{mastery}",
                    "type": "armor",
                    "slot": slot,
                    "defense": defense,
                    "attack": int(legendary_flat_power_v11338["attack"]),
                    "magic_attack": int(legendary_flat_power_v11338["magic_attack"]),
                    "price": None,
                    "rarity": "legendary",
                    "rarity_name": "Legendarny Setowy",
                    "affix": primary_stat,
                    "affix_amount": primary_amount,
                    "stats": {
                        secondary_stat: secondary_amount,
                        tertiary_stat: tertiary_amount,
                        **(mec_hybrid_extra_stats(legacy_affix_amount) if class_name == "Mec" else {}),
                    },
                    "properties": dict(legendary_properties_v11326),
                    "equipment_identity_source": "boss_set",
                    "source_progression_stage": mastery,
                    "equipment_identity_role": "boss_upgrade",
                    "equipment_identity_label": (
                        "Bossowy set klasowy — mocniejsze właściwości "
                        "niż sklepowy odpowiednik"
                    ),
                    "class_base_stat_pair": (primary_stat, secondary_stat),
                    "class_base_stat_triplet": (
                        primary_stat, secondary_stat, tertiary_stat,
                    ),
                    "required_class": class_name,
                    "required_mastery": mastery,
                    # Celowo korzysta z istniejących progów 2/4/6/8 klasy.
                    "class_shop_item": True,
                    "class_set_name": set_name,
                    "class_set_piece": slot,
                    "legendary_set_loot": True,
                    "legendary_loot_tier": mastery,
                    "desc": (
                        f"Legendarna część zestawu dla klasy {class_name}. "
                        f"Wymaga aktywnej klasy {class_name} i Biegłości {mastery}. "
                        f"Zdobywana z bossów kamieni milowych co 50 pięter. Obrona +{defense}. "
                        f"Podstawowe statystyki EQ: "
                        f"{class_equipment_base_stats_text(class_name, legacy_affix_amount, slot)}."
                    ),
                }, 'ITEMS', ITEMS, (item_id,))
                CLASS_EQUIPMENT_ITEM_IDS.add(item_id)
                tier_items.append(item_id)
            class_sets[mastery] = tuple(tier_items)

            relic_id = f"legendrelic_{class_slug}_m{mastery}"
            relic_defense = max(1, base_defense + 4 + defense_step + 2)
            legacy_relic_affix = 4 + affix_step + 2
            (
                relic_primary_stat, relic_primary_amount,
                relic_secondary_stat, relic_secondary_amount,
                relic_tertiary_stat, relic_tertiary_amount,
            ) = class_equipment_split_stat_budget(
                class_name, legacy_relic_affix, "necklace"
            )
            expected_stats = (
                {"intelligence", "willpower", "constitution"}
                if class_type_for_name(class_name) == "magic"
                else {"strength", "dexterity", "constitution"}
            )
            if {
                relic_primary_stat, relic_secondary_stat, relic_tertiary_stat
            } != expected_stats:
                raise RuntimeError(
                    f"Legendary class relic stat triplet mismatch: {class_name}"
                )
            relic_flat_power_v11338 = (
                legendary_class_equipment_flat_power_channels_v11338(
                    class_name, mastery, "relic", relic=True
                )
            )
            prop_value = max(1, min(5, mastery // 100 + 1))
            properties = {
                "all_damage_pct": prop_value,
                "physical_defense_pct": prop_value,
                "magic_defense_pct": prop_value,
            }
            if class_type_for_name(class_name) == "magic":
                properties["max_mana_pct"] = prop_value
            else:
                properties["max_hp_pct"] = prop_value
            _catalog_mut.catalog_assign({
                "name": f"Relikwiarz Legendy {definition['set_name']} +{mastery}",
                "type": "armor",
                "slot": "necklace",
                "defense": relic_defense,
                "attack": int(relic_flat_power_v11338["attack"]),
                "magic_attack": int(relic_flat_power_v11338["magic_attack"]),
                "price": None,
                "rarity": "legendary",
                "rarity_name": "Legendarny Klasowy",
                "affix": relic_primary_stat,
                "affix_amount": relic_primary_amount,
                "stats": {
                    relic_secondary_stat: relic_secondary_amount,
                    relic_tertiary_stat: relic_tertiary_amount,
                    **(mec_hybrid_extra_stats(legacy_relic_affix) if class_name == "Mec" else {}),
                },
                "class_base_stat_pair": (relic_primary_stat, relic_secondary_stat),
                "class_base_stat_triplet": (
                    relic_primary_stat, relic_secondary_stat, relic_tertiary_stat,
                ),
                "required_class": class_name,
                "required_mastery": mastery,
                "properties": properties,
                "equipment_identity_source": "boss_relic",
                "source_progression_stage": mastery,
                "equipment_identity_role": "unique_power",
                "equipment_identity_label": (
                    "Relikt bossa — unikalna alternatywa dla części setowej"
                ),
                "legendary_class_relic": True,
                "legendary_loot_tier": mastery,
                "desc": (
                    f"Legendarny relikt klasy {class_name} z bossa kamienia milowego co 100 pięter. "
                    f"Wymaga Biegłości {mastery}. Nie należy do zestawu, więc jest świadomą alternatywą "
                    "dla naszyjnika setowego. "
                    f"Podstawowe statystyki EQ: "
                    f"{class_equipment_base_stats_text(class_name, legacy_relic_affix)}."
                ),
            }, 'ITEMS', ITEMS, (relic_id,))
            relics[mastery] = relic_id


def equipment_identity_audit_v11326():
    errors = []

    def _flat_power_channel_ok_v11338(item):
        class_name = str(item.get("required_class") or "")
        attack = int(item.get("attack", 0) or 0)
        magic_attack = int(item.get("magic_attack", 0) or 0)
        if class_name == "Mec":
            return attack > 0 and magic_attack > 0
        if class_type_for_name(class_name) == "magic":
            return magic_attack > 0 and attack == 0
        return attack > 0 and magic_attack == 0

    class_shop_items = [
        item
        for item in ITEMS.values()
        if item.get("class_shop_item") and not item.get("legendary_set_loot")
    ]
    if not class_shop_items:
        errors.append("missing class shop items")
    else:
        for item in class_shop_items[:200]:
            if item.get("equipment_identity_source") != "class_shop":
                errors.append("class shop identity source missing")
                break
            if not item.get("properties"):
                errors.append("class shop item has no identity properties")
                break
            if not _flat_power_channel_ok_v11338(item):
                errors.append(
                    "v1.13.38 class shop Attack/Magic Attack channel missing: "
                    + str(item.get("name") or "?")
                )
                break

    # v1.13.38 UOSS benchmark: Quartz Charm (lvl 110) daje +60 Attack i
    # +60 Magic Attack. Ofensywny klasowy accessory na tym samym progu nie może
    # przegrywać w właściwym kanale, również dla hybrydowego Meca.
    for _class_name in CLASS_EQUIPMENT_SETS:
        _bench = class_equipment_flat_power_channels(
            _class_name, 110, "accessory", 3
            if class_equipment_style_role(_class_name, 3) == "ofensywny"
            else 2
            if class_equipment_style_role(_class_name, 2) == "ofensywny"
            else 1,
        )
        if _class_name == "Mec":
            if int(_bench.get("attack", 0) or 0) < 60 or int(
                _bench.get("magic_attack", 0) or 0
            ) < 60:
                errors.append("v1.13.38 Mec accessory loses to Quartz Charm flat power")
                break
        elif class_type_for_name(_class_name) == "magic":
            if int(_bench.get("magic_attack", 0) or 0) < 60:
                errors.append(
                    "v1.13.38 magic class accessory loses to Quartz Charm Magic Attack"
                )
                break
        elif int(_bench.get("attack", 0) or 0) < 60:
            errors.append(
                "v1.13.38 physical class accessory loses to Quartz Charm Attack"
            )
            break

    roles = {}
    for item in class_shop_items:
        key = (
            item.get("required_class"),
            item.get("required_mastery"),
            item.get("slot"),
        )
        role = item.get("equipment_identity_role")
        if role:
            roles.setdefault(key, {})[role] = dict(item.get("properties") or {})
    if not any(
        len(group) >= 3 and len({tuple(sorted(v.items())) for v in group.values()}) >= 3
        for group in roles.values()
    ):
        errors.append("shop styles are not materially distinct")

    # v1.13.27: a boss-set source must not lose to the strongest shop
    # style at the same class/mastery/slot on total percentage properties.
    _shop_prop_by_key = {}
    _shop_flat_power_by_key_v11338 = {}
    for item in class_shop_items:
        key = (
            item.get("required_class"),
            int(item.get("required_mastery", 1) or 1),
            item.get("slot"),
        )
        prop_sum = sum(float(v or 0.0) for v in (item.get("properties") or {}).values())
        _shop_prop_by_key[key] = max(_shop_prop_by_key.get(key, 0.0), prop_sum)
        flat_sum_v11338 = int(item.get("attack", 0) or 0) + int(
            item.get("magic_attack", 0) or 0
        )
        _shop_flat_power_by_key_v11338[key] = max(
            _shop_flat_power_by_key_v11338.get(key, 0), flat_sum_v11338
        )

    legendary_sets = [
        item for item in ITEMS.values() if item.get("legendary_set_loot")
    ]
    if not legendary_sets:
        errors.append("missing legendary boss sets")
    else:
        if not all(item.get("equipment_identity_source") == "boss_set" for item in legendary_sets[:100]):
            errors.append("boss set identity source missing")
        if not all(item.get("properties") for item in legendary_sets[:100]):
            errors.append("boss set identity properties missing")
        if not all(_flat_power_channel_ok_v11338(item) for item in legendary_sets):
            errors.append("v1.13.38 boss set Attack/Magic Attack channel missing")
        for item in legendary_sets:
            key = (
                item.get("required_class"),
                int(item.get("required_mastery", 1) or 1),
                item.get("slot"),
            )
            shop_sum = float(_shop_prop_by_key.get(key, 0.0))
            boss_sum = sum(
                float(v or 0.0)
                for v in (item.get("properties") or {}).values()
            )
            if shop_sum > 0.0 and boss_sum <= shop_sum:
                errors.append(
                    f"boss set source regression: {item.get('name')} "
                    f"properties {boss_sum:.2f} <= shop {shop_sum:.2f}"
                )
                break
            shop_flat_v11338 = int(
                _shop_flat_power_by_key_v11338.get(key, 0) or 0
            )
            boss_flat_v11338 = int(item.get("attack", 0) or 0) + int(
                item.get("magic_attack", 0) or 0
            )
            if shop_flat_v11338 > 0 and boss_flat_v11338 <= shop_flat_v11338:
                errors.append(
                    f"v1.13.38 boss set flat power regression: {item.get('name')} "
                    f"{boss_flat_v11338} <= shop {shop_flat_v11338}"
                )
                break
            if int(item.get("source_progression_stage", 0) or 0) != int(
                item.get("required_mastery", 1) or 1
            ):
                errors.append("boss set source stage mismatch")
                break

    legendary_relics_v11338 = [
        item for item in ITEMS.values() if item.get("legendary_class_relic")
    ]
    if not legendary_relics_v11338:
        errors.append("v1.13.38 missing legendary class relics")
    elif not all(
        _flat_power_channel_ok_v11338(item) for item in legendary_relics_v11338
    ):
        errors.append("v1.13.38 legendary relic Attack/Magic Attack channel missing")

    blacksmith = [
        item for item in ITEMS.values() if item.get("crafted_masterwork")
    ]
    if blacksmith and not all(
        item.get("equipment_identity_source") == "blacksmith"
        and int(item.get("sockets", 0) or 0) >= 1
        and bool(item.get("properties"))
        for item in blacksmith[:100]
    ):
        errors.append("blacksmith masterwork identity incomplete")

    return {
        "version": "1.13.38",
        "class_shop_count": len(class_shop_items),
        "legendary_set_count": len(legendary_sets),
        "blacksmith_count": len(blacksmith),
        "error_count": len(errors),
        "errors": errors,
    }


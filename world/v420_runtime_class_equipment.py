# -*- coding: utf-8 -*-
"""Native historical helper extraction; unchanged function bodies."""
def finalize_class_equipment_v03015():
    errors = []
    touched = 0

    expected_mastery = {}
    expected_class = {}
    for class_name, tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        for mastery, item_ids in tiers.items():
            for item_id in item_ids:
                expected_mastery[item_id] = int(mastery)
                expected_class[item_id] = class_name
    for class_name, tiers in LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER.items():
        for mastery, item_ids in tiers.items():
            for item_id in item_ids:
                expected_mastery[item_id] = int(mastery)
                expected_class[item_id] = class_name
    for class_name, tiers in LEGENDARY_CLASS_RELIC_BY_CLASS_TIER.items():
        for mastery, item_id in tiers.items():
            expected_mastery[item_id] = int(mastery)
            expected_class[item_id] = class_name

    labels = {
        "strength": "Siła", "dexterity": "Zręczność", "constitution": "Kondycja",
        "intelligence": "Inteligencja", "willpower": "Siła Woli",
    }
    for item_id, mastery in expected_mastery.items():
        item = ITEMS.get(item_id)
        if not item:
            errors.append(f"brak class EQ {item_id}")
            continue
        class_name = expected_class[item_id]
        # Dla zwykłego klasowego EQ finalna warstwa wymusza progresję statów
        # na KAŻDYM progu 1/10/20/.../600. Generator Core może wcześniej
        # przeliczyć affix_amount, ale nie może spłaszczyć dwóch sąsiednich
        # Tierów do identycznego budżetu. Legendarne sety/relicty zachowują
        # swój osobny wygenerowany budżet.
        if item.get("class_shop_item") and not item.get("legendary_set_loot") and not item.get("legendary_class_relic"):
            generated_budget = class_equipment_stat_budget(mastery, item.get("slot"))
        else:
            generated_budget = max(3, int(item.get("affix_amount", 1) or 1))
        (
            primary_stat, primary_amount,
            secondary_stat, secondary_amount,
            tertiary_stat, tertiary_amount,
        ) = class_equipment_split_stat_budget(
            class_name,
            generated_budget,
            item.get("slot"),
            int(item.get("class_equipment_style", 1) or 1),
        )
        item["affix"] = primary_stat
        item["affix_amount"] = primary_amount
        item["stats"] = {
            secondary_stat: secondary_amount,
            tertiary_stat: tertiary_amount,
            # v1.17.2: the earlier Mec generator deliberately adds INT/WILL
            # to its physical STR/DEX/CON baseline.  The final post-Generator
            # pass must not erase those hybrid channels when rebuilding stats.
            **(mec_hybrid_extra_stats(generated_budget) if class_name == "Mec" else {}),
        }
        # v0.61.2: pola pochodne, których gameplay nie odczytuje, nie są materializowane
        # dla dziesiątek tysięcy zwykłych części klasowego EQ.
        if not item.get("class_shop_item"):
            item["class_base_stat_pair"] = (primary_stat, secondary_stat)
            item["class_base_stat_triplet"] = (
                primary_stat, secondary_stat, tertiary_stat,
            )
            item["class_equipment_profile"] = class_equipment_profile(class_name).get("identity")
        item["required_class"] = class_name
        item["required_mastery"] = mastery
        item["properties"] = class_equipment_profile_properties(
            class_name, mastery, item.get("slot")
        )

        stat_text = (
            f"{labels[primary_stat]} +{primary_amount}, "
            f"{labels[secondary_stat]} +{secondary_amount}, "
            f"{labels[tertiary_stat]} +{tertiary_amount}"
        )
        if class_name == "Mec":
            stat_text += (
                f", Inteligencja +{item['stats']['intelligence']}"
                f", Siła Woli +{item['stats']['willpower']}"
            )
        profile_text = str(item.get("class_equipment_profile") or class_equipment_profile(class_name).get("identity") or "")
        defense = int(item.get("defense", 0) or 0)
        set_name = item.get("class_set_name") or "Klasowy"
        if item.get("legendary_class_relic"):
            item["desc"] = (
                f"Legendarny relikt klasy {class_name} z bossa kamienia milowego. "
                f"Wymaga aktywnej klasy {class_name} i Biegłości {mastery}. "
                f"Obrona +{defense}. Podstawowe statystyki EQ: {stat_text}. Profil klasy: {profile_text}. "
                f"Właściwości: {item.get('properties', {})}."
            )
        elif item.get("legendary_set_loot"):
            item["desc"] = (
                f"Legendarna część zestawu {set_name} dla klasy {class_name}. "
                f"Wymaga aktywnej klasy {class_name} i Biegłości {mastery}. "
                f"Obrona +{defense}. Podstawowe statystyki EQ: {stat_text}. Profil klasy: {profile_text}. "
                f"Właściwości: {item.get('properties', {})}."
            )
        else:
            # v0.61.2: zwykłe klasowe EQ dostaje identyczny opis dopiero przy wyświetleniu.
            item.pop("desc", None)
        touched += 1

    # Remove stale seller entries left after moving profession NPCs to private rooms.
    stale_sellers = []
    for room_id in list(SHOP_SELLERS):
        if room_id not in SHOPS:
            stale_sellers.append(room_id)
            SHOP_SELLERS.pop(room_id, None)

    return {
        "version": "0.30.16",
        "touched": touched,
        "stale_shop_sellers_removed": tuple(sorted(stale_sellers)),
        "error_count": len(errors),
        "errors": errors,
    }


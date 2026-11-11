# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _material_random_profile(tier, slot, variant_index, salt=0):
    """Deterministyczny profil materiałowego EQ.

    v0.30.37: każdy slot ma własne preferencje statów/właściwości, a rejestracja
    odrzuca powtórzone profile statów w obrębie tego samego materiału i slotu.
    `salt` służy wyłącznie do deterministycznego znalezienia innego profilu.
    """
    tier_index = 1 + next(
        i for i, row in enumerate(CORPSE_MATERIAL_TIERS)
        if row["key"] == tier["key"]
    )
    rng = random.Random(
        f"soulbound-v0.30.37:{tier['key']}:{slot}:{int(variant_index)}:{int(salt)}"
    )

    property_budgets = (1, 1, 2, 3, 4, 5, 7, 8, 10, 12)
    required_mastery = corpse_material_variant_mastery(tier["key"], variant_index)
    band_levels = CORPSE_MATERIAL_MASTERY_BANDS[tier["key"]]
    substep = band_levels.index(required_mastery)

    # Drop nie jest już ubogim kuzynem sklepu. Ten sam etap korzysta z tej samej
    # ogólnej skali mocy, ale roll ma 80-110% budżetu i losowy rozkład statów.
    # Dzięki temu dobry egzemplarz może być lepszy dla konkretnego buildu,
    # podczas gdy sklep pozostaje pewnym, klasowo dopasowanym wyborem.
    quality = 0.80 + rng.random() * 0.30
    progression_budget = equipment_progression_budget_v1138(required_mastery)
    stat_budget = max(2, int(round(progression_budget * quality)))
    property_budget = (
        property_budgets[tier_index - 1]
        + max(0, int(round((quality - 0.80) * 8.0)))
    )

    if tier_index <= 4:
        stat_count = 2
    elif tier_index <= 6:
        stat_count = rng.choice((2, 3))
    elif tier_index <= 8:
        stat_count = 3
    elif tier_index == 9:
        stat_count = rng.choice((3, 4))
    else:
        stat_count = 4
    stat_count = min(stat_count, len(MATERIAL_RANDOM_STAT_POOL), stat_budget)

    # Preferencje slotu są rotowane przez seed, więc slot ma własny charakter,
    # ale 24 warianty nadal nie są kopiami tego samego rozkładu.
    stat_pref = list(MATERIAL_SLOT_STAT_PREFERENCES.get(slot, MATERIAL_RANDOM_STAT_POOL))
    tier_pref = [tier.get("primary"), tier.get("secondary")]
    weighted_stats = []
    for stat in tier_pref + stat_pref + list(MATERIAL_RANDOM_STAT_POOL):
        if stat in MATERIAL_RANDOM_STAT_POOL and stat not in weighted_stats:
            weighted_stats.append(stat)
    # Losuj z preferowanej listy przez permutację, nie przez identyczną stałą parę.
    rotated = weighted_stats[rng.randrange(len(weighted_stats)):] + weighted_stats[:rng.randrange(len(weighted_stats))]
    # Drugi shuffle daje warianty przy zachowaniu slot-specific seed.
    rng.shuffle(rotated)
    chosen_stats = rotated[:stat_count]
    stat_values = _material_budget_split(rng, stat_budget, stat_count)
    stats = dict(zip(chosen_stats, stat_values))

    if tier_index <= 2:
        property_count = 1
    elif tier_index <= 5:
        property_count = 2
    elif tier_index <= 8:
        property_count = 3
    else:
        property_count = 4
    property_count = min(property_count, len(MATERIAL_RANDOM_PROPERTY_POOL), property_budget)
    prop_pref = list(MATERIAL_SLOT_PROPERTY_PREFERENCES.get(slot, MATERIAL_RANDOM_PROPERTY_POOL))
    rng.shuffle(prop_pref)
    chosen_properties = prop_pref[:property_count]
    property_values = _material_budget_split(rng, property_budget, property_count)
    properties = dict(zip(chosen_properties, property_values))

    _slot_label, defense_delta = CORPSE_MATERIAL_SLOT_DEFS[slot]
    defense = max(
        1,
        int(tier["base_defense"])
        + int(defense_delta)
        + int(round(
            equipment_defense_step_v1138(required_mastery)
            * (0.88 + (quality - 0.80) * 0.55)
        )),
    )

    # Losowy profil ofensywny może mieć Attack, Magic Attack albo oba.
    slot_scale = float(MATERIAL_SLOT_POWER_SCALE.get(slot, 0.50))
    flat_pool = max(
        0,
        int(round(progression_budget * 0.11 * slot_scale * quality)),
    )
    physical_score = (
        int(stats.get("strength", 0))
        + int(stats.get("dexterity", 0))
        + int(round(float(properties.get("physical_damage_pct", 0)) * 2.0))
    )
    magic_score = (
        int(stats.get("intelligence", 0))
        + int(stats.get("willpower", 0))
        + int(round(float(properties.get("magic_damage_pct", 0)) * 2.0))
    )
    score_total = physical_score + magic_score
    attack = 0
    magic_attack = 0
    if flat_pool > 0 and score_total > 0:
        attack = int(round(flat_pool * physical_score / float(score_total)))
        magic_attack = max(0, flat_pool - attack)
        if physical_score > 0 and attack <= 0:
            attack = 1
        if magic_score > 0 and magic_attack <= 0:
            magic_attack = 1

    if required_mastery >= 500:
        sockets = 4
    elif required_mastery >= 360:
        sockets = 3
    elif required_mastery >= 240:
        sockets = 2
    elif required_mastery >= 120:
        sockets = 1
    else:
        sockets = 0
    if quality >= 1.04:
        sockets = min(5, sockets + 1)

    return (
        defense, stats, properties, attack, magic_attack, sockets, quality
    )


def loot_source_equipment_audit_v11327():
    errors = []

    crafted = [
        item for item in ITEMS.values() if item.get("crafted_masterwork")
    ]
    if not crafted:
        errors.append("missing blacksmith masterwork items")
    else:
        for item in crafted[:200]:
            if int(item.get("source_progression_stage", 0) or 0) <= 0:
                errors.append("blacksmith item missing source progression stage")
                break
            if int(item.get("sockets", 0) or 0) < 1:
                errors.append("blacksmith item lost socket identity")
                break

    corpse = [
        item for item in ITEMS.values()
        if item.get("corpse_material") and not item.get("infinite_depth_variant")
    ]
    if not corpse:
        errors.append("missing corpse material equipment")
    else:
        for item in corpse[:500]:
            mastery = int(item.get("required_mastery", 0) or 0)
            stage = int(item.get("source_progression_stage", 0) or 0)
            if stage != mastery or stage <= 0:
                errors.append("corpse drop source stage mismatch")
                break
            if item.get("equipment_identity_source") != "corpse_drop":
                errors.append("corpse drop identity source missing")
                break

    return {
        "version": "1.13.27",
        "blacksmith_count": len(crafted),
        "corpse_drop_count": len(corpse),
        "error_count": len(errors),
        "errors": errors,
    }


def roll_fish_measurement(item_id):
    """Losowy rozmiar okazu do rekordów v0.9.5; bez wpływu na balans."""
    item = ITEMS.get(item_id, {})
    base_id = base_fish_species_id(item_id)
    name = normalize_lookup_text(ITEMS.get(base_id, item).get("name", base_id))
    rarity = fish_species_rarity(base_id)
    tiny_words = ("szprot", "sardyn", "sardine", "anchovy", "sardela", "stynk", "uklej", "gudgeon", "kiełb", "kielb")
    eel_words = ("węgorz", "wegorz", "eel")
    shark_words = ("rekin", "shark")
    monster_words = ("lewiatan", "leviathan", "serpent", "smok", "drake")
    large_words = ("tuńczyk", "tunczyk", "tuna", "marlin", "miecznik", "swordfish", "samogłów", "samoglow", "sunfish", "jesiotr", "sturgeon", "catfish", "halibut")
    if any(word in name for word in monster_words):
        length_mm = random.randint(1800, 8000)
        weight_g = random.randint(80000, 1500000)
    elif any(word in name for word in shark_words):
        length_mm = random.randint(700, 5200)
        weight_g = random.randint(8000, 750000)
    elif any(word in name for word in eel_words):
        length_mm = random.randint(250, 2200)
        weight_g = random.randint(150, 30000)
    elif any(word in name for word in tiny_words):
        length_mm = random.randint(60, 360)
        weight_g = random.randint(20, 1200)
    elif any(word in name for word in large_words):
        length_mm = random.randint(350, 2600)
        weight_g = random.randint(1500, 220000)
    else:
        ranges = {
            "common": ((90, 650), (60, 7000)),
            "uncommon": ((120, 900), (100, 14000)),
            "rare": ((160, 1300), (200, 30000)),
            "epic": ((220, 1900), (500, 70000)),
            "legendary": ((400, 3200), (1500, 220000)),
        }
        (lmin, lmax), (wmin, wmax) = ranges[rarity]
        length_mm = random.randint(lmin, lmax)
        weight_g = random.randint(wmin, wmax)
    variant = str(item.get("rare_resource_variant") or "")
    if variant == "giant":
        length_mm = int(round(length_mm * 1.30))
        weight_g = int(round(weight_g * 1.80))
    elif variant == "ancient":
        length_mm = int(round(length_mm * 1.10))
        weight_g = int(round(weight_g * 1.20))
    return max(1, length_mm), max(1, weight_g)


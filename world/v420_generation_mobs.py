# -*- coding: utf-8 -*-
"""Native historical helper extraction; unchanged function bodies."""
def _v0130_apply_resources(room_id, spec):
    for resource in spec.get("resources", ()):
        if resource == "herb_meadow":
            HERBALISM_ROOMS.add(room_id)
            MEADOW_HERBALISM_ROOMS.add(room_id)
            V012_MEADOW_HERB_GROUP[room_id] = "meadow"
        elif resource == "herb_forest":
            HERBALISM_ROOMS.add(room_id)
            V012_MEADOW_HERB_GROUP[room_id] = "forest"
        elif resource == "herb_water":
            HERBALISM_ROOMS.add(room_id)
            V012_MEADOW_HERB_GROUP[room_id] = "water"
        elif resource == "wood":
            WOODCUTTING_ROOMS.add(room_id)
        elif resource == "mine":
            # v0.25.1: geologiczny motyw może wystąpić wizualnie, ale
            # wydobycie jest dostępne wyłącznie w Kopalni Głębinowej.
            pass
        elif resource == "fish_river":
            RIVER_FISHING_ROOMS.add(room_id)
            FRESHWATER_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralna rzeka"
        elif resource == "fish_lake":
            LAKE_FISHING_ROOMS.add(room_id)
            FRESHWATER_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralne jezioro"
        elif resource == "fish_sea":
            SEA_FISHING_ROOMS.add(room_id)
            MARINE_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralne morze"
        elif resource == "fish_ocean":
            OCEAN_FISHING_ROOMS.add(room_id)
            MARINE_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralny ocean"


def _v0140_clone_variant(base_id, *, rare=False, miniboss=False):
    base = MOB_TEMPLATES.get(base_id)
    if not base:
        return None
    suffix = "rare" if rare else "miniboss"
    variant_id = f"v0140_{suffix}_{base_id}"
    if variant_id in MOB_TEMPLATES:
        return variant_id
    data = dict(base)
    data["drops"] = dict(base.get("drops", {}))
    if rare:
        data["name"] = f"Wędrujący Rzadki {base['name']}"
        data["rare_mob"] = True
        data["rare_base_template"] = base_id
        hp_mult, dmg_mult, reward_mult = 1.75, 1.30, 2.20
    else:
        data["name"] = f"Strażnik Mini-Lochu: {base['name']}"
        data["mini_boss"] = True
        data["stationary_mob"] = True
        data["v0140_mini_boss"] = True
        hp_mult, dmg_mult, reward_mult = 2.80, 1.55, 3.20
    data["max_hp"] = max(1, int(round(int(base.get("max_hp", 1)) * hp_mult)))
    data["damage"] = max(1, int(round(int(base.get("damage", 1)) * dmg_mult)))
    data["stat_reward"] = max(1, int(round(int(base.get("stat_reward", 1)) * min(1.8, reward_mult))))
    data["soul_reward"] = max(1, int(round(int(base.get("soul_reward", 1)) * reward_mult)))
    data["class_xp_reward"] = max(50, int(round(int(base.get("class_xp_reward", max(50, int(base.get("stat_reward", 1))*10))) * reward_mult)))
    data["silver"] = max(1, int(round(int(base.get("silver", 1)) * reward_mult)))
    data["gold"] = 0
    data["mithril"] = 0
    data["auto_aggro"] = False
    data["drops"].setdefault(V014_TREASURE_MAP_ITEM, 0.28 if rare else 0.45)
    data["drops"].setdefault("soul_shard", 0.45 if rare else 0.70)
    _catalog_mut.catalog_assign(data, 'MOB_TEMPLATES', MOB_TEMPLATES, (variant_id,))
    return variant_id


def v0150_dynamic_world_offer(account_id, now=None):
    slot = v0150_dynamic_quest_slot(now)
    kinds = tuple(V013_FRONTIER_SPECS)
    qtypes = ("explore", "event", "secret", "mini", "fish", "herb", "mine", "wood")
    qtype = qtypes[_v0140_hash_int("v015-dq-type", account_id, slot) % len(qtypes)]
    kind = kinds[_v0140_hash_int("v015-dq-kind", account_id, slot) % len(kinds)]
    target = kind if qtype in {"explore"} else "any"
    needs = {"explore":12, "event":2, "secret":2, "mini":1, "fish":12, "herb":12, "mine":12, "wood":12}
    labels = {
        "explore":f"Zbadaj nowe sektory: {V013_FRONTIER_SPECS[kind]['zone']}",
        "event":"Odwiedź aktywne wydarzenia świata", "secret":"Odkryj sekrety rubieży",
        "mini":"Dotrzyj do finału proceduralnego mini-lochu", "fish":"Złów ryby",
        "herb":"Zbierz zioła", "mine":"Wydobądź surowce", "wood":"Pozyskaj drewno",
    }
    needed = needs[qtype]
    stage=max(1,min(CHARACTER_MAX_LEVEL,int(V013_FRONTIER_SPECS[kind].get("base_mastery",1) or 1)))
    complexity=1.5 if qtype in {"event","secret","mini"} else 1.0
    reward_soul=max(1,int(round(v0190_log_curve(stage,V019_SOUL_KILL_NORMAL)*max(2.0,math.sqrt(needed))*complexity)))
    # v1.13.8: dynamic world quests bypass the static QUESTS finalizer, so
    # they need the same modern economy floor explicitly.
    from systems.economy_income_balance import v1138_activity_income
    reward_coins=max(
        1,
        int(round(v0190_log_curve(stage,V019_QUEST_COIN)*complexity)),
        v1138_activity_income(stage, "dynamic_world", complexity),
    )
    reward_gold=max(1,reward_coins//SILVER_PER_GOLD)
    return {
        "quest_key":f"v015:{slot}:{qtype}:{kind}", "quest_type":qtype, "target":target,
        "label":labels[qtype], "needed":needed, "progress":0,
        "stage":stage, "reward_soul_xp":reward_soul,
        "reward_gold":reward_gold, "accepted_slot":slot, "completed":False,
    }


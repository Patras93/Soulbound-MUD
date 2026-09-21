# -*- coding: utf-8 -*-
"""Soulbound v0.31.6 Economy Audit 2.0.

Final post-generation normalization for the denomination:
100 silver = 1 gold, 1,000,000 gold = 1 mithril.
The pass intentionally preserves reasonable authored values and only clamps
legacy outliers created for older denomination scales.
"""

ECONOMY_AUDIT_VERSION = "0.31.6"


def _v03060_stage(record):
    candidates = (
        record.get("generator_level"), record.get("required_soul_level"),
        record.get("required_profession_level"), record.get("min_profession_level"),
        record.get("required_mastery"), record.get("level"),
    )
    for value in candidates:
        try:
            if value is not None and int(value) > 0:
                return max(1, min(PROGRESSION_MAX_LEVEL, int(value)))
        except Exception:
            pass
    return 1


def _v03060_quest_cap(quest):
    stage = _v03060_stage(quest)
    base = int(generator_core_v027.currency_for_stage(stage, "normal"))
    kind = str(quest.get("kind") or "").lower()
    needed = max(1, int(quest.get("needed", 1) or 1))
    if kind == "world_boss": mult = 24.0
    elif kind == "legendary_rare": mult = 16.0
    elif kind == "mini_dungeon": mult = 16.0
    elif kind == "world_event": mult = 14.0
    elif kind == "discover_secret": mult = 10.0
    elif kind == "explore_frontier": mult = 9.0
    elif kind in ("craft_set", "collect_resource_set"): mult = 12.0
    elif kind == "kill": mult = 8.0 + min(10.0, needed / 3.0)
    elif kind in ("collect", "collect_resource", "collect_category"):
        mult = 6.0 + min(8.0, needed / 5.0)
    elif kind == "deliver_npc": mult = 4.0
    elif kind == "talk_class_teacher": mult = 3.0
    else: mult = 7.0
    if int(quest.get("required_soul_level", 0) or 0) > 0:
        mult = max(mult, 20.0)
    if quest.get("repeatable"):
        mult *= 0.85
    else:
        mult *= 1.10
    # Keep early authored quest rewards intact unless truly excessive.
    return max(10_000, int(round(base * mult)))


def _v03060_sell_cap(item):
    stage = _v03060_stage(item)
    base = int(generator_core_v027.currency_for_stage(stage, "normal"))
    typ = str(item.get("type") or "").lower()
    if typ in ("gem", "gem_raw"): mult = 8.0
    elif typ == "geode": mult = 6.0
    elif typ in ("resource", "craft_material", "fish"): mult = 4.0
    elif typ in ("armor", "weapon"): mult = 6.0
    else: mult = 4.0
    return max(500, int(round(base * mult)))


def _v03060_currency_value(record, prefix="sell"):
    return legacy_currency_to_coins(
        record.get(prefix + "_silver", 0),
        record.get(prefix + "_gold", 0),
        record.get(prefix + "_mithril", 0),
    )


def apply_economy_audit_v03060():
    result = {
        "version": ECONOMY_AUDIT_VERSION,
        "quest_rewards_clamped": 0,
        "sell_values_clamped": 0,
        "quest_before_max": 0,
        "quest_after_max": 0,
        "sell_before_max": 0,
        "sell_after_max": 0,
    }

    # Quest rewards: preserve reasonable authored rewards, clamp old-scale outliers.
    for quest in QUESTS.values():
        current = legacy_currency_to_coins(
            quest.get("reward_silver", 0), quest.get("reward_gold", 0), quest.get("reward_mithril", 0)
        )
        result["quest_before_max"] = max(result["quest_before_max"], current)
        cap = _v03060_quest_cap(quest)
        if current > cap:
            quest["reward_silver"] = cap
            quest["reward_gold"] = 0
            quest["reward_mithril"] = 0
            result["quest_rewards_clamped"] += 1
        result["quest_after_max"] = max(
            result["quest_after_max"],
            legacy_currency_to_coins(quest.get("reward_silver", 0), quest.get("reward_gold", 0), quest.get("reward_mithril", 0)),
        )

    # Explicit sell values: stop single gathered resources from exceeding endgame gear economics.
    for item in ITEMS.values():
        current = _v03060_currency_value(item, "sell")
        if current <= 0:
            continue
        result["sell_before_max"] = max(result["sell_before_max"], current)
        cap = _v03060_sell_cap(item)
        if current > cap:
            item["sell_silver"] = cap
            item["sell_gold"] = 0
            item["sell_mithril"] = 0
            result["sell_values_clamped"] += 1
        result["sell_after_max"] = max(result["sell_after_max"], _v03060_currency_value(item, "sell"))

    return result


ECONOMY_AUDIT_V03060 = apply_economy_audit_v03060()

# Shared-guild sinks were authored for the pre-rebase denomination. Keep them meaningful,
# but make a top hall upgrade require a handful of endgame bosses rather than dozens.
def v0927_guild_hall_upgrade_cost(current_level):
    level=max(1,min(V0927_GUILD_HALL_MAX_LEVEL,int(current_level or 1)))
    if level>=V0927_GUILD_HALL_MAX_LEVEL:
        return 0
    stage=generator_core_v027.stage_from_index(level+1,V0927_GUILD_HALL_MAX_LEVEL)
    return generator_core_v027.system_cost(stage,"guild-hall",50.0)


def v0927_guild_building_upgrade_cost(current_level):
    level=max(0,min(V0927_GUILD_HALL_MAX_LEVEL,int(current_level or 0)))
    if level>=V0927_GUILD_HALL_MAX_LEVEL:
        return 0
    stage=generator_core_v027.stage_from_index(level+1,V0927_GUILD_HALL_MAX_LEVEL)
    return generator_core_v027.system_cost(stage,"guild-building",15.0)


def economy_audit_summary_v03060():
    return dict(ECONOMY_AUDIT_V03060)


HELP_TOPICS["economy_audit2"] = [
    "Economy Audit 2.0 obowiązuje po kursie 100 srebra = 1 złoto i 1 000 000 złota = 1 mithril.",
    "Nagrody questów mają końcowy limit zależny od poziomu, rodzaju celu, liczby wymaganych akcji i powtarzalności; zachowano rozsądne niższe nagrody ręczne.",
    "Jawne ceny sprzedaży surowców i klejnotów są ograniczone względem poziomu, aby pojedynczy drop nie był wielokrotnie cenniejszy od endgame EQ.",
    "Siedziba Gildii i budynki używają skali dostosowanej do nowego nominału. Housing pozostaje lekkim osobistym sinkiem, a odkryty transport jest darmowy z powodów dostępności.",
]
HELP_TOPIC_ALIASES.update({"audyt ekonomii":"economy_audit2", "economy audit":"economy_audit2", "ekonomia 2":"economy_audit2"})

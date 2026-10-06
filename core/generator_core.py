"""Soulbound Generator Core v0.64.0 — stage math + procedural/fallback balance.

Authored content is authoritative. Generator Core derives shared stage mathematics and may
fill missing numeric fields, but it must not rebalance authored character resources/passives,
Soul bonuses, class set bonuses, Soul Weapon bases, quest rewards or recipe XP.
Fully procedural/runtime-created content may still opt into generator-owned numeric balance.
"""
from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import math
import re
import os

from core.player_math import (
    uncapped_stat_xp_scale as authored_uncapped_stat_xp_scale,
    uncapped_stat_xp_gain as authored_uncapped_stat_xp_gain,
    character_attribute_power as authored_character_attribute_power,
    character_offensive_build_multiplier as authored_character_offensive_build_multiplier,
    speed_from_dexterity as authored_speed_from_dexterity,
    basic_attack_hits_from_speed as authored_basic_attack_hits_from_speed,
    basic_attack_hits_from_dexterity as authored_basic_attack_hits_from_dexterity,
    mec_vmax_duration_seconds as authored_mec_vmax_duration_seconds,
    dodge_from_dexterity as authored_dodge_from_dexterity,
    critical_chance_from_dexterity as authored_critical_chance_from_dexterity,
    critical_multiplier as authored_critical_multiplier,
    physical_defense_base as authored_physical_defense_base,
    magic_defense_base as authored_magic_defense_base,
    skill_level_power as authored_skill_level_power,
    skill_cooldown_factor as authored_skill_cooldown_factor,
)
from core.profession_timing import (
    profession_action_seconds as authored_profession_action_seconds,
)
from core.economy_curve import (
    economy_stage_anchor,
    economy_lane_amount,
)
from core.character_resources import (
    character_hp_base as authored_character_hp_base,
    character_mana_base as authored_character_mana_base,
    class_passive_profile as authored_class_passive_profile,
    race_passive_profile as authored_race_passive_profile,
    passive_text_pl as authored_passive_text_pl,
    class_passive_text_pl as authored_class_passive_text_pl,
    race_passive_text_pl as authored_race_passive_text_pl,
)

GENERATOR_VERSION = "0.64.0"
MAX_LEVEL = 600
SAFE_INT = 9_000_000_000_000_000_000

AXIS_TARGET_ACTIONS = {
    "character": 18,
    "class": 16,
    "soul": 25,
    "skill": 18,
    "profession": 50,
    "tool": 65,
    "stat": 60,
}
AXIS_CURVES = {
    "character": (140.0, 54.0, 1.82),
    "class": (180.0, 70.0, 1.84),
    "soul": (110.0, 48.0, 1.80),
    "skill": (90.0, 31.0, 1.73),
    "profession": (130.0, 43.0, 1.78),
    "tool": (115.0, 37.0, 1.78),
    "stat": (100.0, 29.0, 1.70),
}

RANK_HP = {"normal": 1.0, "elite": 1.55, "rare": 2.15, "mini": 4.2, "boss": 8.5, "world_boss": 14.0}
RANK_DAMAGE = {"normal": 1.0, "elite": 1.12, "rare": 1.24, "mini": 1.42, "boss": 1.68, "world_boss": 1.95}
RANK_REWARD = {"normal": 1.0, "elite": 1.8, "rare": 3.0, "mini": 5.0, "boss": 8.0, "world_boss": 13.0}

SLOT_DEFENSE_WEIGHT = {
    "head": 0.75, "body": 1.35, "hands": 0.55, "legs": 1.0, "feet": 0.55,
    "ring": 0.35, "ring1": 0.35, "ring2": 0.35, "charm": 0.45, "charm1": 0.45, "charm2": 0.45,
    "necklace": 0.45, "shoulders": 0.90, "belt": 0.70, "cloak": 0.50,
    "bracers": 0.60, "relic": 0.55,
}


def clamp(value, low, high):
    return max(low, min(high, value))


def stable_unit(text: str) -> float:
    raw = hashlib.sha256(str(text).encode("utf-8")).digest()
    return int.from_bytes(raw[:8], "big") / float((1 << 64) - 1)


def stable_jitter(text: str, span: float = 0.08) -> float:
    return 1.0 + (stable_unit(text) * 2.0 - 1.0) * span


def stage_from_index(index: int, maximum: int) -> int:
    """Map an ordinal system level to the shared 1-600 Generator Core stage."""
    index = max(1, int(index))
    maximum = max(1, int(maximum))
    if maximum <= 1:
        return 1
    index = min(index, maximum)
    return 1 + int(round((index - 1) * (MAX_LEVEL - 1) / (maximum - 1)))


def axis_requirement(axis: str, level: int) -> int:
    # v0.27.1: statystyki są jedyną osią bez twardego limitu. Pozostałe
    # osie nadal należą do przestrzeni 1-400. Ta sama krzywa statów jest
    # bezpiecznie ekstrapolowana ponad 400 aż do SAFE_INT.
    raw_level = max(1, int(level))
    level = raw_level if axis == "stat" else clamp(raw_level, 1, MAX_LEVEL)
    base, growth, power = AXIS_CURVES[axis]
    value = base + growth * (level ** power)
    return min(SAFE_INT, max(1, int(round(value))))


def uncapped_stat_xp_scale(stat_level: int) -> float:
    """Compatibility wrapper; player stat progression lives outside Generator Core."""
    return authored_uncapped_stat_xp_scale(stat_level)


def uncapped_stat_xp_gain(base_amount: int, stat_level: int) -> int:
    """Compatibility wrapper; player stat progression lives outside Generator Core."""
    return authored_uncapped_stat_xp_gain(base_amount, stat_level)


def axis_gain(axis: str, level: int, intensity: float = 1.0) -> int:
    target = AXIS_TARGET_ACTIONS[axis]
    value = axis_requirement(axis, level) / float(target) * max(0.05, float(intensity))
    return min(SAFE_INT, max(1, int(round(value))))


def character_hp_base(character_level: int, constitution: int) -> int:
    """Compatibility wrapper; authored character resources live outside Generator Core."""
    return authored_character_hp_base(character_level, constitution)


def character_mana_base(
    character_level: int,
    intelligence: int,
    willpower: int | None = None,
) -> int:
    """Compatibility wrapper; authored character resources live outside Generator Core."""
    return authored_character_mana_base(character_level, intelligence, willpower)


def character_attribute_power(character_level: int, stat_value: int) -> int:
    """Compatibility wrapper; player combat math lives outside Generator Core."""
    return authored_character_attribute_power(character_level, stat_value)


def character_offensive_build_multiplier(stat_value: int | float) -> float:
    return authored_character_offensive_build_multiplier(stat_value)


def speed_from_dexterity(dexterity: int) -> int:
    return authored_speed_from_dexterity(dexterity)


def basic_attack_hits_from_speed(speed: int, haste: bool = False) -> int:
    return authored_basic_attack_hits_from_speed(speed, haste)


def basic_attack_hits_from_dexterity(dexterity: int, haste: bool = False) -> int:
    return authored_basic_attack_hits_from_dexterity(dexterity, haste)


def mec_vmax_duration_seconds(skill_level: int, willpower: int) -> int:
    return authored_mec_vmax_duration_seconds(skill_level, willpower)


# v1.13.16: player-math invariants are audited in core/player_math.py.
# Generator Core keeps compatibility wrappers only; duplicate audits here would
# incorrectly depend on Generator MAX_LEVEL before progression_600 patches it.


def dodge_from_dexterity(dexterity: int) -> float:
    return authored_dodge_from_dexterity(dexterity)


def critical_chance_from_dexterity(dexterity: int) -> float:
    return authored_critical_chance_from_dexterity(dexterity)


def critical_multiplier(character_level: int) -> float:
    return authored_critical_multiplier(character_level)


def physical_defense_base(character_level: int, constitution: int) -> int:
    return authored_physical_defense_base(character_level, constitution)


def magic_defense_base(character_level: int, willpower: int) -> int:
    return authored_magic_defense_base(character_level, willpower)


def skill_level_power(level: int) -> float:
    return authored_skill_level_power(level)


def skill_cooldown_factor(level: int) -> float:
    return authored_skill_cooldown_factor(level)


def profession_action_seconds(tool_type: str, level: int) -> int:
    """Compatibility wrapper; profession tempo is authored outside Generator Core."""
    return authored_profession_action_seconds(tool_type, level)


def gather_quantity(tool_type: str, tool_level: int, profession_level: int, roll: float) -> int:
    tool_level = clamp(int(tool_level), 1, MAX_LEVEL)
    profession_level = clamp(int(profession_level), 1, MAX_LEVEL)
    progress = ((tool_level + profession_level - 2) / (2 * (MAX_LEVEL - 1)))
    identity = 0.85 + 0.30 * stable_unit(f"{tool_type}:yield")
    p2 = clamp((0.035 + 0.19 * progress) * identity, 0.02, 0.28)
    p3 = clamp((0.010 + 0.055 * progress ** 1.35) * identity, 0.005, 0.09)
    p4 = clamp((0.002 + 0.015 * progress ** 2.0) * identity, 0.001, 0.025)
    if roll < p4: return 4
    if roll < p4 + p3: return 3
    if roll < p4 + p3 + p2: return 2
    return 1


def crafting_xp_roll(base_value: int, roll: float) -> int:
    base = max(1, int(base_value))
    variance = 0.08 + 0.08 * stable_unit(f"craft-xp:{base}")
    factor = 1.0 + (clamp(float(roll), 0.0, 1.0) * 2.0 - 1.0) * variance
    return max(1, int(round(base * factor)))


def boss_chest_currency(stage: int, chest_kind: str = "boss") -> int:
    stage = clamp(int(stage), 1, MAX_LEVEL)
    identity = 1.0 + 0.25 * stable_unit(f"chest:{chest_kind}")
    return max(1, int(round(currency_for_stage(stage, "boss") * 2.25 * identity)))


def resource_pool(resource_ids, items: dict, level: int, context: str = "resource") -> tuple:
    level = clamp(int(level), 1, MAX_LEVEL)
    candidates = []
    for iid in resource_ids:
        item = items.get(iid, {})
        generated = int(item.get("generator_level", 1) or 1)
        if generated <= level:
            candidates.append((iid, generated))
    if not candidates:
        fallback = sorted(
            ((iid, int(items.get(iid, {}).get("generator_level", 1) or 1)) for iid in resource_ids if iid in items),
            key=lambda row: (row[1], row[0]),
        )
        return tuple(iid for iid, _ in fallback[:1])
    # Keep the pool cumulative, while deterministic ecology affinity makes different
    # locations feel distinct without per-location numeric loot tables.
    candidates.sort(key=lambda row: (row[1], row[0]))
    return tuple(iid for iid, _ in candidates)


def resource_weights(resource_ids, items: dict, level: int, context: str = "resource") -> list[float]:
    level = clamp(int(level), 1, MAX_LEVEL)
    weights = []
    for iid in resource_ids:
        generated = int(items.get(iid, {}).get("generator_level", 1) or 1)
        age = max(0, level - generated)
        freshness = 0.30 + 8.0 / ((1.0 + age / 34.0) ** 1.28)
        affinity = 0.72 + 0.56 * stable_unit(f"{context}:{iid}:affinity")
        weights.append(max(0.01, freshness * affinity))
    return weights


def jackpot_chance(level: int, context: str = "jackpot") -> float:
    level = clamp(int(level), 1, MAX_LEVEL)
    progress = (level - 1) / (MAX_LEVEL - 1)
    identity = 0.75 + 0.50 * stable_unit(context)
    return clamp((0.000002 + 0.000018 * progress ** 2.1) * identity, 0.000001, 0.00003)


def mob_hp(level: int, rank: str = "normal") -> int:
    level = clamp(int(level), 1, MAX_LEVEL)
    base = 52.0 + 9.5 * level + 0.74 * level * level
    return max(1, int(round(base * RANK_HP.get(rank, 1.0))))


def mob_damage(level: int, rank: str = "normal") -> int:
    level = clamp(int(level), 1, MAX_LEVEL)
    base = 3.0 + 0.30 * level + 0.0105 * level * level
    return max(1, int(round(base * RANK_DAMAGE.get(rank, 1.0))))


def currency_for_stage(level: int, rank: str = "normal") -> int:
    level = clamp(int(level), 1, MAX_LEVEL)
    return min(
        SAFE_INT,
        economy_lane_amount(level, "mob_currency", RANK_REWARD.get(rank, 1.0)),
    )


def item_price_for_stage(level: int, rarity_mult: float = 1.0) -> int:
    level = clamp(int(level), 1, MAX_LEVEL)
    return min(
        SAFE_INT,
        economy_lane_amount(level, "item_price", max(0.25, rarity_mult)),
    )


def quest_currency_for_stage(
    level: int,
    workload: float = 1.0,
    repeatable: bool = False,
    identity: str = "quest",
) -> int:
    level = clamp(int(level), 1, MAX_LEVEL)
    workload = clamp(float(workload), 1.0, 8.0)
    work_mult = 1.0 + 0.22 * (workload - 1.0)
    repeat_mult = 0.72 if repeatable else 1.0
    identity_mult = stable_jitter(f"quest-currency:{identity}", 0.045)
    coins = int(round(
        economy_stage_anchor(level) * work_mult * repeat_mult * identity_mult
    ))
    coins = max(1_001, coins)
    if coins < 1_000_000_000 and coins % 1000 == 0:
        coins += 137
    return min(SAFE_INT, coins)


def tool_price_for_item(item: dict, identity: str = "tool") -> int:
    gates = []
    for key in (
        "required_tool_level", "min_tool_level", "min_profession_level",
        "required_profession_level", "required_mastery",
    ):
        try:
            value = int(item.get(key, 0) or 0)
        except Exception:
            value = 0
        if value > 0:
            gates.append(value)
    stage = clamp(max(gates) if gates else 1, 1, MAX_LEVEL)
    base = economy_stage_anchor(stage)
    identity_mult = 0.92 + 0.16 * stable_unit(f"tool-price:{identity}")
    return min(
        SAFE_INT,
        max(1_001, int(round(base * 1.20 * identity_mult))),
    )


def system_cost(stage: int, identity: str = "system", intensity: float = 1.0) -> int:
    """Generated cost for non-item systems (guilds, services, upgrades)."""
    stage = clamp(int(stage), 1, MAX_LEVEL)
    identity_mult = 0.88 + 0.24 * stable_unit(f"system-cost:{identity}")
    return min(SAFE_INT, max(1, int(round(item_price_for_stage(stage) * max(0.10, float(intensity)) * identity_mult))))


def system_reward(stage: int, identity: str = "system", intensity: float = 1.0) -> int:
    """Generated currency reward for system-level objectives."""
    stage = clamp(int(stage), 1, MAX_LEVEL)
    identity_mult = 0.90 + 0.20 * stable_unit(f"system-reward:{identity}")
    return min(SAFE_INT, max(1, int(round(currency_for_stage(stage) * max(0.10, float(intensity)) * identity_mult))))


def generated_count(stage: int, identity: str = "objective", low: int = 1, high: int = 100) -> int:
    """Bounded deterministic objective count derived from stage and identity."""
    stage = clamp(int(stage), 1, MAX_LEVEL)
    low, high = max(1, int(low)), max(1, int(high))
    if high < low:
        low, high = high, low
    progress = ((stage - 1) / (MAX_LEVEL - 1)) ** 0.82
    identity_shift = (stable_unit(f"count:{identity}") - 0.5) * 0.16
    value = low + (high - low) * clamp(progress + identity_shift, 0.0, 1.0)
    return clamp(int(round(value)), low, high)


def generated_cooldown_seconds(stage: int, identity: str = "system", minimum: int = 3600, maximum: int = 21600) -> int:
    """Generated cooldown; higher-stage systems may take longer but remain bounded."""
    stage = clamp(int(stage), 1, MAX_LEVEL)
    minimum, maximum = max(3600, int(minimum)), max(3600, int(maximum))
    if maximum < minimum:
        minimum, maximum = maximum, minimum
    progress = (stage - 1) / (MAX_LEVEL - 1)
    identity_shift = stable_unit(f"cooldown:{identity}")
    seconds = minimum + (maximum - minimum) * clamp(0.65 * progress + 0.35 * identity_shift, 0.0, 1.0)
    # Hour granularity keeps user-facing timers predictable and NVDA-friendly.
    return max(3600, int(round(seconds / 3600.0)) * 3600)


def guild_bonus_percent(level: int, max_level: int = 100) -> int:
    level = clamp(int(level), 1, max(1, int(max_level)))
    progress = (level - 1) / max(1, int(max_level) - 1)
    return clamp(int(round(1 + 10 * progress ** 0.82)), 1, 11)


def resource_sale_for_stage(level: int, rarity_mult: float = 1.0) -> int:
    level = clamp(int(level), 1, MAX_LEVEL)
    return min(
        SAFE_INT,
        economy_lane_amount(level, "resource_sale", max(0.5, rarity_mult)),
    )


def mob_rank(template: dict) -> str:
    if template.get("world_boss") or template.get("v016_world_boss") or template.get("v020_mythic_world_boss"):
        return "world_boss"
    if template.get("crypt_boss") or template.get("astral_boss") or template.get("giant_fortress_boss") or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss") or template.get("boss_mechanic") or template.get("v018_great_ruin_guardian"):
        return "boss"
    if template.get("mini_boss") or template.get("v0140_mini_boss"):
        return "mini"
    if template.get("rare_mob") or template.get("rare_variant") or template.get("rare_troll") or template.get("v016_legendary_rare"):
        return "rare"
    if template.get("elite_affix"):
        return "elite"
    return "normal"


def semantic_floor_level(template: dict) -> int | None:
    direct = (
        ("crypt_floor", 1.0, 0),
        ("astral_floor", 1.0, 0),
        ("giant_fortress_floor", 4.0, 0),
        ("profession_dungeon_floor", 4.0, 0),
        ("mythic_crypt_floor", 0.72, 115),
        ("mythic_astral_floor", 0.66, 135),
        ("v020_gauntlet_round", 18.0, 210),
        ("guild_hall_level", 38.0, 20),
        ("procedural_region_stage", 1.0, 0),
    )
    for key, scale, offset in direct:
        if template.get(key) is not None:
            try:
                return clamp(int(round(offset + int(template[key]) * scale)), 1, MAX_LEVEL)
            except (TypeError, ValueError, OverflowError):  # AUDIT_INTENTIONAL_PASS: malformed legacy numeric hint is ignored
                pass
    return None


def _graph_room_levels(rooms: dict) -> dict[str, int]:
    """Derive numeric balance stages without changing authored room semantics."""
    if not rooms:
        return {}
    start = "square" if "square" in rooms else next(iter(rooms))
    dist = {start: 0}
    q = deque([start])
    while q:
        rid = q.popleft()
        for target in (rooms.get(rid, {}).get("exits") or {}).values():
            if target in rooms and target not in dist:
                dist[target] = dist[rid] + 1
                q.append(target)
    room_levels = {}
    for rid, room in rooms.items():
        lvl = semantic_floor_level(room)
        if lvl is None:
            text = f"{rid} {room.get('zone','')} {room.get('name','')}".lower()
            floor_match = re.search(r"(?:floor|level|poziom|pietro|piętro)[_ -]*(\d{1,4})", text)
            if floor_match and any(k in text for k in ("crypt", "krypt", "astral", "tower", "wież", "fortress", "twierdz", "dungeon", "loch")):
                lvl = clamp(int(floor_match.group(1)), 1, MAX_LEVEL)
            else:
                d = dist.get(rid)
                if d is None:
                    lvl = 160 + int(stable_unit(rid) * 220)
                else:
                    lvl = 1 + int(round(1.9 * d + 0.10 * d * d))
                if room.get("v020_mega_gate") or room.get("v020_gauntlet"):
                    lvl = max(lvl, 220)
        try:
            recommended = int(room.get("recommended_mastery", 0) or 0)
        except (TypeError, ValueError, OverflowError):
            recommended = 0
        if recommended > 0:
            lvl = max(lvl, recommended)
        room_levels[rid] = clamp(int(lvl), 1, MAX_LEVEL)
        # generator_level is balance metadata only. Never overwrite recommended_mastery,
        # exits, names, zones or any authored access/recommendation field.
        _write_record_numeric("ROOMS", room, "generator_level", room_levels[rid])
    return room_levels



def _mob_levels(ns: dict, room_levels: dict[str, int]) -> dict[str, int]:
    mobs = ns.get("MOB_TEMPLATES", {})
    spawns = ns.get("MOB_SPAWNS", [])
    by_mob = defaultdict(list)
    for rid, mid in spawns:
        if rid in room_levels:
            by_mob[str(mid)].append(room_levels[rid])

    cache = {}
    visiting = set()
    def level_for(mid: str) -> int:
        if mid in cache:
            return cache[mid]
        if mid in visiting:
            return 1 + int(stable_unit(mid) * (MAX_LEVEL - 1))
        visiting.add(mid)
        t = mobs.get(mid, {})
        lvl = semantic_floor_level(t)
        if lvl is None:
            for base_key in ("elite_base_template", "rare_base_template", "base_template", "template_id"):
                base = t.get(base_key)
                if base and base != mid and base in mobs:
                    lvl = level_for(str(base)); break
        if lvl is None and by_mob.get(mid):
            # A reusable template is balanced for the EARLIEST place where it can occur.
            # Later rooms may add harder ranks/other templates, but a quest drop cannot
            # require a mob whose stats were tuned for a later duplicate spawn.
            lvl = min(by_mob[mid])
        if lvl is None:
            lvl = 1 + int(stable_unit(mid) * (MAX_LEVEL - 1))
        cache[mid] = clamp(int(lvl), 1, MAX_LEVEL)
        visiting.discard(mid)
        return cache[mid]

    for mid in mobs:
        level_for(mid)
    return cache


def runtime_mob_balance(template_id: str, template: dict, level: int, rank: str | None = None) -> dict:
    """Balance whitelisted numeric fields of a runtime mob; semantic identity stays authored."""
    level = clamp(int(level), 1, MAX_LEVEL)
    rank = str(rank or mob_rank(template))
    _write_record_numeric("MOB_TEMPLATES", template, "generator_level", level)
    _write_record_numeric("MOB_TEMPLATES", template, "v019_stage", level)
    hp = mob_hp(level, rank)
    _write_record_numeric("MOB_TEMPLATES", template, "max_hp", hp)
    _write_record_numeric("MOB_TEMPLATES", template, "base_max_hp", hp)
    _write_record_numeric("MOB_TEMPLATES", template, "damage", mob_damage(level, rank))
    reward_mult = RANK_REWARD.get(rank, 1.0)
    _write_record_numeric("MOB_TEMPLATES", template, "character_xp_reward", axis_gain("character", level, reward_mult))
    _write_record_numeric("MOB_TEMPLATES", template, "class_xp_reward", axis_gain("class", level, reward_mult))
    _write_record_numeric("MOB_TEMPLATES", template, "soul_reward", axis_gain("soul", level, reward_mult))
    _write_record_numeric("MOB_TEMPLATES", template, "stat_reward", axis_gain("stat", level, reward_mult))
    _write_record_numeric("MOB_TEMPLATES", template, "silver", currency_for_stage(level, rank))
    _write_record_numeric("MOB_TEMPLATES", template, "gold", 0)
    _write_record_numeric("MOB_TEMPLATES", template, "mithril", 0)
    drops = template.get("drops")
    if isinstance(drops, dict) and drops:
        base_chance = {"normal": .055, "elite": .09, "rare": .14, "mini": .22, "boss": .34, "world_boss": .48}.get(rank, .055)
        count = max(1, len(drops))
        for item_id in list(drops):
            chance = base_chance * stable_jitter(f"{template_id}:{item_id}", .22) / (count ** .20)
            _write_nested_numeric("MOB_TEMPLATES", template, "drops", item_id, round(clamp(chance, .005, .85), 5))
    return template




def _generate_mobs(ns: dict, levels: dict[str, int]) -> None:
    """Attach Generator metadata and fill only missing mob numbers.

    Authored combat/reward/economy values are design decisions. Generator Core
    may provide a fallback for incomplete templates, but must not erase tuned
    HP, damage, rewards, currency or authored drop chances.
    """
    mobs = ns.get("MOB_TEMPLATES", {})
    for mid, t in mobs.items():
        lvl = levels[mid]
        rank = mob_rank(t)
        _write_record_numeric("MOB_TEMPLATES", t, "generator_level", lvl)
        _write_record_numeric("MOB_TEMPLATES", t, "v019_stage", lvl)
        hp = mob_hp(lvl, rank)
        _write_record_numeric_fallback("MOB_TEMPLATES", t, "max_hp", hp, minimum=1)
        _write_record_numeric_fallback("MOB_TEMPLATES", t, "base_max_hp", int(t.get("max_hp", hp) or hp), minimum=1)
        _write_record_numeric_fallback("MOB_TEMPLATES", t, "damage", mob_damage(lvl, rank), minimum=1)
        reward_mult = RANK_REWARD.get(rank, 1.0)
        _write_record_numeric_fallback("MOB_TEMPLATES", t, "character_xp_reward", axis_gain("character", lvl, reward_mult), minimum=0)
        _write_record_numeric_fallback("MOB_TEMPLATES", t, "class_xp_reward", axis_gain("class", lvl, reward_mult), minimum=0)
        _write_record_numeric_fallback("MOB_TEMPLATES", t, "soul_reward", axis_gain("soul", lvl, reward_mult), minimum=0)
        _write_record_numeric_fallback("MOB_TEMPLATES", t, "stat_reward", axis_gain("stat", lvl, reward_mult), minimum=0)

        # Preserve authored denominations. Generate silver only when a template
        # has no currency fields at all.
        has_authored_currency = any(key in t for key in ("silver", "gold", "mithril"))
        if not has_authored_currency:
            _write_record_numeric("MOB_TEMPLATES", t, "silver", currency_for_stage(lvl, rank))
            _write_record_numeric("MOB_TEMPLATES", t, "gold", 0)
            _write_record_numeric("MOB_TEMPLATES", t, "mithril", 0)

        drops = t.get("drops")
        if isinstance(drops, dict) and drops:
            base_chance = {"normal": .055, "elite": .09, "rare": .14, "mini": .22, "boss": .34, "world_boss": .48}.get(rank, .055)
            count = max(1, len(drops))
            for item_id in list(drops):
                chance = base_chance * stable_jitter(f"{mid}:{item_id}", .22) / (count ** .20)
                _write_nested_numeric_fallback("MOB_TEMPLATES", t, "drops", item_id, round(clamp(chance, .005, .85), 5))




def _initial_item_level(item_id: str, item: dict) -> int | None:
    # v0.71.6: ordinary class-shop EQ receives its stage from the ordinal
    # class_equipment_tier pass below. Avoid building/searching a description
    # string for 30k+ generated pieces.
    if item.get("class_shop_item") and item.get("class_equipment_tier") is not None:
        return None
    # Only structural world semantics are accepted here. Legacy prices, defense,
    # required mastery and old profession levels are deliberately ignored.
    for key in ("procedural_region_stage", "boss_chest_floor", "boss_relic_floor", "astral_relic_floor"):
        value = item.get(key)
        if value:
            try:
                return clamp(int(value), 1, MAX_LEVEL)
            except (TypeError, ValueError, OverflowError):  # AUDIT_INTENTIONAL_PASS: malformed legacy numeric hint is ignored
                pass
    text = f"{item_id} {item.get('desc','')}".lower()
    floor_match = re.search(r"(?:floor|pietro|piętro)[ _:+-]*(\d{1,4})", text)
    if floor_match:
        return clamp(int(floor_match.group(1)), 1, MAX_LEVEL)
    return None


def _ordinal_hints(items: dict) -> dict[str, int]:
    """Turn content tiers into generated 1-400 stages without trusting their values.

    v0.71.6 builds every ordinal domain in two catalog passes instead of two
    full ITEMS scans per field. With 30k+ class-shop pieces this removes a large
    amount of repeated dictionary work while producing identical stages.
    """
    fields = (
        "class_equipment_tier", "crypt_set_tier", "corpse_material_tier",
        "legendary_loot_tier", "blacksmith_tier", "gem_level",
        "astral_set_tier", "v020_artifact_tier", "jewelcraft_level",
    )
    values_by_field = {field: set() for field in fields}
    for item in items.values():
        for field in fields:
            value = item.get(field)
            if value is not None:
                values_by_field[field].add(value)

    positions_by_field = {}
    for field, values in values_by_field.items():
        unique = sorted(values, key=lambda x: (float(x) if str(x).replace('.', '', 1).isdigit() else str(x)))
        if not unique:
            continue
        positions_by_field[field] = {
            value: (1 if len(unique) == 1 else 1 + int(round(index * (MAX_LEVEL - 1) / (len(unique) - 1))))
            for index, value in enumerate(unique)
        }

    hints = {}
    for iid, item in items.items():
        generated = None
        for field, positions in positions_by_field.items():
            value = item.get(field)
            if value in positions:
                stage = positions[value]
                generated = stage if generated is None else min(generated, stage)
        if generated is not None:
            hints[iid] = generated
    return hints


def _normalized_order_levels(pairs) -> dict:
    cleaned = [(str(iid), float(order)) for iid, order in pairs if iid is not None and order is not None]
    if not cleaned:
        return {}
    unique = sorted({order for _iid, order in cleaned})
    if len(unique) == 1:
        rank_to_level = {unique[0]: 1}
    else:
        rank_to_level = {order: 1 + int(round(idx * (MAX_LEVEL - 1) / (len(unique) - 1))) for idx, order in enumerate(unique)}
    return {iid: rank_to_level[order] for iid, order in cleaned}


def _resource_order_hints(ns: dict, items: dict) -> dict[str, int]:
    hints = {}
    fish_ids = set(ns.get("FISH_RESOURCE_IDS", set()) or set())
    fish_unlock = ns.get("fish_unlock_level")
    if callable(fish_unlock):
        pairs = []
        for iid in fish_ids:
            try:
                pairs.append((iid, fish_unlock(iid)))
            except Exception as exc:
                print(f"GENERATOR_FISH_UNLOCK_ERROR: {iid}: {type(exc).__name__}: {exc}", flush=True)
        hints.update(_normalized_order_levels(pairs))

    ore_levels = ns.get("ORE_ATLAS_LEVELS", {}) or {}
    hints.update(_normalized_order_levels((iid, ore_levels.get(iid, 1)) for iid in (ns.get("ORE_RESOURCE_IDS", set()) or set())))

    for ids_name, table_name in (("WOOD_RESOURCE_IDS", "WOOD_ATLAS_ROOM_MIN_LEVELS"), ("HERB_RESOURCE_IDS", "HERB_ATLAS_ROOM_MIN_LEVELS")):
        ids = set(ns.get(ids_name, set()) or set())
        table = ns.get(table_name, {}) or {}
        mins = {}
        for _room, mapping in table.items():
            if not isinstance(mapping, dict):
                continue
            for iid, old_order in mapping.items():
                if iid in ids:
                    try:
                        old_order = float(old_order)
                        mins[iid] = min(mins.get(iid, old_order), old_order)
                    except (TypeError, ValueError, OverflowError):  # AUDIT_INTENTIONAL_PASS: malformed legacy numeric hint is ignored
                        pass
        # Resources without an old placement still join deterministically after ordered ones.
        ordered = _normalized_order_levels(mins.items())
        hints.update(ordered)
        missing = sorted(ids - set(ordered))
        for iid in missing:
            hints[iid] = 1 + int(stable_unit(f"resource-order:{ids_name}:{iid}") * (MAX_LEVEL - 1))

    # Rare resource variants inherit their base species/material stage later.
    return hints


def _item_levels(ns: dict, mob_levels: dict[str, int]) -> dict[str, int]:
    items = ns.get("ITEMS", {})
    mobs = ns.get("MOB_TEMPLATES", {})
    levels = {iid: _initial_item_level(iid, item) for iid, item in items.items()}
    resource_hints = _resource_order_hints(ns, items)
    for iid, hint in resource_hints.items():
        levels[iid] = hint
    ordinal = _ordinal_hints(items)
    for iid, hint in ordinal.items():
        if levels.get(iid) is None:
            levels[iid] = hint
    # Drops inherit the earliest content level that can produce them.
    drop_sources = defaultdict(list)
    for mid, t in mobs.items():
        for iid in (t.get("drops") or {}):
            if iid in items:
                drop_sources[iid].append(mob_levels.get(mid, 1))
        for key in ("corpse_equipment_pool", "corpse_material_pool"):
            for iid in (t.get(key) or []):
                if iid in items:
                    drop_sources[iid].append(mob_levels.get(mid, 1))
    for iid, values in drop_sources.items():
        # Gathering resources keep their generated profession order. Mob drops of the
        # same material are re-priced to that stage instead of collapsing the whole
        # profession curve to the earliest creature that happens to carry it.
        if iid in resource_hints:
            continue
        inherited = min(values)
        levels[iid] = inherited if levels.get(iid) is None else min(levels[iid], inherited)

    # Resource variants inherit base-resource level. Resolve repeatedly.
    for _ in range(4):
        changed = False
        for iid, item in items.items():
            base = item.get("base_resource_id") or item.get("crypt_base_item") or item.get("v020_artifact_base")
            if base in levels and levels.get(base) is not None and levels.get(iid) is None:
                levels[iid] = levels[base]; changed = True
        if not changed: break

    # Unlinked content is placed deterministically; it cannot inherit balance from hand-written prices/stats.
    for iid in items:
        if levels.get(iid) is None:
            levels[iid] = 1 + int(stable_unit(iid) * (MAX_LEVEL - 1))
    return {k: clamp(int(v), 1, MAX_LEVEL) for k, v in levels.items()}


def _rarity_multiplier(item: dict) -> float:
    rarity = str(item.get("rarity", "")).lower()
    return {
        "common": 1.0, "uncommon": 1.25, "rare": 1.6, "epic": 2.1,
        "legendary": 3.0, "mythic": 4.0, "crafted": 1.35,
    }.get(rarity, max(1.0, float(item.get("rare_value_multiplier", 1.0) or 1.0)))


def _generate_items(ns: dict, levels: dict[str, int]) -> None:
    """Attach stage and fill only genuinely missing item numeric fields."""
    items = ns.get("ITEMS", {})
    resource_ids = set()
    for key in (
        "FISH_RESOURCE_IDS", "ORE_RESOURCE_IDS",
        "WOOD_RESOURCE_IDS", "HERB_RESOURCE_IDS",
    ):
        resource_ids.update(ns.get(key, set()) or set())

    for iid, item in items.items():
        lvl = levels[iid]
        _write_record_numeric("ITEMS", item, "generator_level", lvl)
        rarity_mult = _rarity_multiplier(item)
        typ = str(item.get("type", "")).lower()
        is_resource = bool(
            iid in resource_ids
            or item.get("resource_category")
            or item.get("base_resource_id")
        )

        if is_resource:
            # Currency denominations are one authored group. If any denomination
            # exists, Generator must not add a second parallel sale currency.
            has_authored_sale = any(
                key in item
                for key in ("sell_silver", "sell_gold", "sell_mithril")
            )
            sale = resource_sale_for_stage(lvl, rarity_mult)
            if not has_authored_sale:
                _write_record_numeric("ITEMS", item, "sell_silver", sale)
                _write_record_numeric("ITEMS", item, "sell_gold", 0)
                _write_record_numeric("ITEMS", item, "sell_mithril", 0)
            _write_record_numeric_fallback(
                "ITEMS", item, "price", max(sale * 3, 1), preserve_none=True
            )
        elif typ == "tool" or item.get("tool_type"):
            _write_record_numeric_fallback(
                "ITEMS",
                item,
                "price",
                tool_price_for_item(item, str(item.get("tool_type") or iid)),
                preserve_none=True,
            )
        else:
            _write_record_numeric_fallback(
                "ITEMS",
                item,
                "price",
                item_price_for_stage(lvl, rarity_mult),
                preserve_none=True,
            )

        plain_class_shop = bool(
            item.get("class_shop_item")
            and not item.get("legendary_set_loot")
            and not item.get("legendary_class_relic")
        )
        if typ == "armor" or item.get("slot"):
            slot = str(item.get("slot", "body"))
            weight = SLOT_DEFENSE_WEIGHT.get(slot, 0.75)
            _write_record_numeric_fallback(
                "ITEMS",
                item,
                "defense",
                max(
                    1,
                    int(round(
                        (1.0 + 0.050 * lvl + 0.00045 * (lvl ** 2))
                        * weight
                        * rarity_mult
                    )),
                ),
            )
            if item.get("affix") and not plain_class_shop:
                _write_record_numeric_fallback(
                    "ITEMS",
                    item,
                    "affix_amount",
                    max(
                        1,
                        int(round(
                            (1.0 + 0.035 * lvl + 0.00022 * (lvl ** 2))
                            * math.sqrt(rarity_mult)
                        )),
                    ),
                )

        if isinstance(item.get("stats"), dict) and not plain_class_shop:
            for stat in list(item["stats"]):
                value = max(
                    1,
                    int(round(
                        (1.0 + 0.032 * lvl + 0.00020 * (lvl ** 2))
                        * math.sqrt(rarity_mult)
                        * stable_jitter(f"{iid}:stat:{stat}", 0.12)
                    )),
                )
                _write_nested_numeric_fallback(
                    "ITEMS", item, "stats", stat, value
                )

        if isinstance(item.get("properties"), dict) and not plain_class_shop:
            for prop in list(item["properties"]):
                value = round(
                    clamp(
                        (1.0 + 0.025 * lvl + 0.00012 * (lvl ** 2))
                        * math.sqrt(rarity_mult)
                        * stable_jitter(f"{iid}:prop:{prop}", 0.10),
                        0.5,
                        36.0,
                    ),
                    3,
                )
                _write_nested_numeric_fallback(
                    "ITEMS", item, "properties", prop, value
                )

        if isinstance(item.get("rune_stats"), dict):
            for stat in list(item["rune_stats"]):
                _write_nested_numeric_fallback(
                    "ITEMS",
                    item,
                    "rune_stats",
                    stat,
                    max(1, int(round(
                        1.0 + 0.025 * lvl + 0.00016 * (lvl ** 2)
                    ))),
                )

        if isinstance(item.get("rune_properties"), dict):
            for prop in list(item["rune_properties"]):
                _write_nested_numeric_fallback(
                    "ITEMS",
                    item,
                    "rune_properties",
                    prop,
                    round(clamp(
                        0.8 + 0.018 * lvl + 0.00009 * (lvl ** 2),
                        0.8,
                        18.0,
                    ), 3),
                )

        if "heal" in item:
            _write_record_numeric_fallback(
                "ITEMS", item, "heal", max(5, int(round(18 + lvl * 2.2)))
            )
        if "mana" in item:
            _write_record_numeric_fallback(
                "ITEMS", item, "mana", max(5, int(round(15 + lvl * 2.0)))
            )
        if "soul_xp" in item:
            _write_record_numeric_fallback(
                "ITEMS", item, "soul_xp", axis_gain("soul", lvl, 2.0)
            )


def _recipe_stage(recipe: dict, item_levels: dict[str, int]) -> int:
    """Semantic hint only; final recipe levels are regenerated across 1-400."""
    values = []
    for iid in (recipe.get("ingredients") or {}):
        if iid in item_levels:
            values.append(item_levels[iid])
    if values:
        return clamp(max(values), 1, MAX_LEVEL)
    output = recipe.get("output")
    if output in item_levels:
        return clamp(item_levels[output], 1, MAX_LEVEL)
    rid = str(recipe.get("id") or recipe.get("name") or "recipe")
    return 1 + int(stable_unit(rid) * (MAX_LEVEL - 1))


def _recipe_topological_order(table: dict, item_levels: dict[str, int]) -> list[str]:
    """Order recipes by dependencies and generated ingredient stages, never old numeric requirements."""
    output_to_recipe = {}
    for rid, recipe in table.items():
        output = recipe.get("output")
        if output:
            output_to_recipe[str(output)] = rid

    outgoing = defaultdict(set)
    indegree = {rid: 0 for rid in table}
    for rid, recipe in table.items():
        for iid in (recipe.get("ingredients") or {}):
            producer = output_to_recipe.get(str(iid))
            if producer and producer != rid and rid not in outgoing[producer]:
                outgoing[producer].add(rid)
                indegree[rid] += 1

    # Content insertion order describes semantic progression without carrying any
    # hand-authored balance number. Dependencies still take precedence, so a
    # component recipe is always generated before recipes that consume it.
    insertion_index = {rid: i for i, rid in enumerate(table)}

    def key(rid: str):
        return (insertion_index.get(rid, 10**9), stable_unit(f"recipe-order:{rid}"), rid)

    ready = sorted((rid for rid, deg in indegree.items() if deg == 0), key=key)
    ordered = []
    while ready:
        rid = ready.pop(0)
        ordered.append(rid)
        for nxt in sorted(outgoing.get(rid, ()), key=key):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
                ready.sort(key=key)

    # Cycles should not block generation. Deterministic ordering breaks them without trusting legacy levels.
    if len(ordered) != len(table):
        remaining = [rid for rid in table if rid not in set(ordered)]
        ordered.extend(sorted(remaining, key=key))
    return ordered


def _generate_recipes(ns: dict, item_levels: dict[str, int]) -> int:
    """Balance recipe XP only; authored requirements, ingredients, outputs and quantities are immutable."""
    total = 0
    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):
        table = ns.get(table_name, {}) or {}
        for rid, recipe in table.items():
            total += 1
            lvl = _recipe_stage(recipe, item_levels)
            for gate in (recipe.get("min_profession_level"), recipe.get("min_tool_level")):
                try:
                    if gate is not None:
                        lvl = max(lvl, int(gate))
                except (TypeError, ValueError, OverflowError):  # AUDIT_INTENTIONAL_PASS: malformed legacy numeric hint is ignored
                    pass
            lvl = clamp(int(lvl), 1, MAX_LEVEL)
            xp = axis_gain("profession", lvl, 1.35)
            _write_record_numeric(table_name, recipe, "generator_level", lvl)
            _write_record_numeric_fallback(table_name, recipe, "xp", xp)
            _write_record_numeric_fallback(table_name, recipe, "profession_xp", xp)
            _write_record_numeric_fallback(
                table_name, recipe, "tool_xp", axis_gain("tool", lvl, 1.20)
            )
    return total




def _giver_stage(ns: dict, quest: dict, giver_stages: dict | None = None) -> int:
    giver = str(quest.get("giver") or "")
    if giver_stages is not None:
        return clamp(int(giver_stages.get(giver, 1) or 1), 1, MAX_LEVEL)
    rooms = ns.get("ROOMS", {}) or {}
    stages = []
    for npc in (ns.get("NPCS", {}) or {}).values():
        if str(npc.get("name") or "") != giver:
            continue
        room = rooms.get(str(npc.get("room") or ""), {})
        if isinstance(room, dict):
            try:
                stages.append(int(room.get("generator_level", 1) or 1))
            except (TypeError, ValueError):  # AUDIT_INTENTIONAL_PASS: malformed room level falls back to other giver rooms
                pass
    return clamp(min(stages) if stages else 1, 1, MAX_LEVEL)


def _quest_alias_levels(ns: dict, alias: str, mob_levels: dict[str, int], alias_levels_index: dict | None = None) -> list[int]:
    alias = str(alias or "")
    if not alias:
        return []
    if alias_levels_index is not None:
        return alias_levels_index.get(alias, ())
    values = []
    for mid, mob in (ns.get("MOB_TEMPLATES", {}) or {}).items():
        tags = set(map(str, mob.get("quest_targets") or ()))
        direct = mob.get("quest_target")
        if direct is not None:
            tags.add(str(direct))
        if alias in tags:
            values.append(int(mob_levels.get(mid, mob.get("generator_level", 1) or 1)))
    return values


def _collect_category_stage(ns: dict, category: str, item_levels: dict[str, int], category_stages: dict | None = None) -> int | None:
    category = str(category or "").lower()
    if category_stages is not None and category in category_stages:
        return category_stages[category]
    set_name = {
        "fish": "FISH_RESOURCE_IDS", "fish_river": "FISH_RESOURCE_IDS",
        "ore": "ORE_RESOURCE_IDS", "wood": "WOOD_RESOURCE_IDS", "herb": "HERB_RESOURCE_IDS",
    }.get(category)
    if not set_name:
        return None
    values = [int(item_levels[iid]) for iid in (ns.get(set_name, set()) or set()) if iid in item_levels]
    return min(values) if values else None


def _quest_stage(ns: dict, qid: str, quest: dict, mob_levels: dict[str, int], item_levels: dict[str, int], giver_stages=None, alias_levels_index=None, category_stages=None) -> int:
    # A starter flag is semantic identity: starter quests must be available to a
    # fresh character regardless of the item they happen to reward.
    if quest.get("starter_quest"):
        return 1

    kind = str(quest.get("kind") or "")
    target = quest.get("target")
    # Profession onboarding must follow the first obtainable resource of that
    # profession, never the generated physical location of its NPC. Rebuilding
    # the city/world topology therefore cannot move a starter profession quest
    # to mid/endgame. This is a semantic rule, not a per-quest exception.
    if (quest.get("reward_profession") and not quest.get("requires_quest")
            and kind in ("collect_category", "collect_distinct_category")):
        category_stage = _collect_category_stage(ns, target, item_levels, category_stages)
        if category_stage is not None:
            return clamp(category_stage, 1, MAX_LEVEL)

    values = [_giver_stage(ns, quest, giver_stages)]
    if target in mob_levels:
        values.append(mob_levels[target])
    else:
        alias_levels = _quest_alias_levels(ns, target, mob_levels, alias_levels_index)
        if alias_levels:
            # A category/alias quest becomes available when its first valid source
            # is reachable; later variants stay valid automatically.
            values.append(min(alias_levels))
    if target in item_levels:
        values.append(item_levels[target])
    if kind in ("collect_category", "collect_distinct_category"):
        category_stage = _collect_category_stage(ns, target, item_levels, category_stages)
        if category_stage is not None:
            values.append(category_stage)
    for target_id in (quest.get("targets") or ()):
        if target_id in mob_levels: values.append(mob_levels[target_id])
        if target_id in item_levels: values.append(item_levels[target_id])
    for iid in (quest.get("resource_targets") or {}):
        if iid in item_levels: values.append(item_levels[iid])

    # Delivery difficulty follows the destination, not the free quest item.
    target_npc = quest.get("target_npc")
    if target_npc and target_npc in (ns.get("NPCS", {}) or {}):
        room_id = ns["NPCS"][target_npc].get("room")
        room = (ns.get("ROOMS", {}) or {}).get(room_id, {})
        if isinstance(room, dict):
            values.append(int(room.get("generator_level", 1) or 1))

    # Soul trial tier is structural identity; its old required-level number is ignored.
    if quest.get("soul_trial_tier"):
        try:
            tier = clamp(int(quest["soul_trial_tier"]), 1, 40)
            values.append(1 if tier == 1 else (tier - 1) * 10)
        except (TypeError, ValueError, OverflowError):  # AUDIT_INTENTIONAL_PASS: malformed legacy numeric hint is ignored
            pass
    return clamp(max(values or [1]), 1, MAX_LEVEL)


def _generate_quests(ns: dict, mob_levels: dict[str, int], item_levels: dict[str, int]) -> None:
    """Generate whitelisted numeric quest rewards while preserving explicitly authored currency rewards."""
    quests = ns.get("QUESTS", {})

    # v0.71.6: build quest lookup indexes once. Historically every quest scanned
    # all NPCs for its giver and, for alias targets, all mob templates again.
    # With thousands of quests this dominated Generator Core startup time.
    rooms = ns.get("ROOMS", {}) or {}
    giver_stages = {}
    for npc in (ns.get("NPCS", {}) or {}).values():
        giver = str(npc.get("name") or "")
        if not giver:
            continue
        room = rooms.get(str(npc.get("room") or ""), {})
        if not isinstance(room, dict):
            continue
        try:
            stage = clamp(int(room.get("generator_level", 1) or 1), 1, MAX_LEVEL)
        except Exception:
            stage = 1
        previous = giver_stages.get(giver)
        giver_stages[giver] = stage if previous is None else min(previous, stage)

    alias_levels_index = defaultdict(list)
    for mid, mob in (ns.get("MOB_TEMPLATES", {}) or {}).items():
        stage = int(mob_levels.get(mid, mob.get("generator_level", 1) or 1))
        tags = set(map(str, mob.get("quest_targets") or ()))
        direct = mob.get("quest_target")
        if direct is not None:
            tags.add(str(direct))
        for alias in tags:
            alias_levels_index[alias].append(stage)
    alias_levels_index = {key: tuple(values) for key, values in alias_levels_index.items()}

    category_stages = {}
    for category, set_name in {
        "fish":"FISH_RESOURCE_IDS", "fish_river":"FISH_RESOURCE_IDS",
        "ore":"ORE_RESOURCE_IDS", "wood":"WOOD_RESOURCE_IDS", "herb":"HERB_RESOURCE_IDS",
    }.items():
        values = [int(item_levels[iid]) for iid in (ns.get(set_name, set()) or set()) if iid in item_levels]
        if values:
            category_stages[category] = min(values)

    levels = {
        qid: _quest_stage(
            ns, qid, q, mob_levels, item_levels,
            giver_stages=giver_stages,
            alias_levels_index=alias_levels_index,
            category_stages=category_stages,
        )
        for qid, q in quests.items()
    }
    # v0.71.6: each quest has at most one requires_quest predecessor. Resolve
    # prerequisite chains in O(N) instead of repeatedly rescanning all quests.
    # Cycles (if authored accidentally) are handled safely: every quest in the
    # cycle receives the maximum initial stage found in that cycle.
    requires = {qid: q.get("requires_quest") for qid, q in quests.items()}
    resolved = {}
    for origin in levels:
        if origin in resolved:
            continue
        path = []
        positions = {}
        current = origin
        while current in levels and current not in resolved and current not in positions:
            positions[current] = len(path)
            path.append(current)
            current = requires.get(current)

        if current in resolved:
            inherited = resolved[current]
        elif current in positions:
            cycle_at = positions[current]
            cycle_nodes = path[cycle_at:]
            inherited = max(levels[node] for node in cycle_nodes)
            for node in cycle_nodes:
                resolved[node] = inherited
            path = path[:cycle_at]
        else:
            inherited = 0

        for node in reversed(path):
            inherited = max(levels[node], inherited)
            resolved[node] = inherited
    levels = resolved
    for qid, q in quests.items():
        lvl = clamp(int(levels.get(qid, 1)), 1, MAX_LEVEL)
        needed = max(1, int(q.get("needed", 1) or 1))
        workload = clamp(math.sqrt(needed), 1.0, 8.0)
        repeat_mult = .72 if q.get("repeatable") else 1.0
        _write_record_numeric("QUESTS", q, "generator_level", lvl)
        _write_record_numeric_fallback("QUESTS", q, "character_xp_reward", axis_gain("character", lvl, workload * repeat_mult))
        _write_record_numeric_fallback("QUESTS", q, "reward_soul_xp", axis_gain("soul", lvl, workload * repeat_mult))
        _write_record_numeric_fallback("QUESTS", q, "reward_stat_progress", axis_gain("stat", lvl, workload * repeat_mult))
        if "reward_profession_xp" in q or q.get("reward_profession") or q.get("specialist_tool_type"):
            _write_record_numeric_fallback("QUESTS", q, "reward_profession_xp", axis_gain("profession", lvl, max(1.0, workload * .75) * repeat_mult))
        if "reward_tool_xp" in q or q.get("reward_tool_type") or q.get("specialist_tool_type"):
            _write_record_numeric_fallback("QUESTS", q, "reward_tool_xp", axis_gain("tool", lvl, max(1.0, workload * .70) * repeat_mult))

        # v1.13.15: authored quest rewards win. Manual currency markers still
        # force an exact protected amount; otherwise Generator fills currency
        # only when the quest has no authored denomination at all.
        manual_coins = q.get("manual_currency_reward_coins")
        has_authored_currency = any(
            key in q for key in ("reward_silver", "reward_gold", "reward_mithril")
        )
        if manual_coins is not None:
            coins = clamp(int(manual_coins), 0, SAFE_INT)
            _write_record_numeric("QUESTS", q, "reward_silver", min(SAFE_INT, coins))
            _write_record_numeric("QUESTS", q, "reward_gold", 0)
            _write_record_numeric("QUESTS", q, "reward_mithril", 0)
        elif not has_authored_currency:
            coins = quest_currency_for_stage(
                lvl, workload, bool(q.get("repeatable")), str(qid)
            )
            _write_record_numeric("QUESTS", q, "reward_silver", min(SAFE_INT, coins))
            _write_record_numeric("QUESTS", q, "reward_gold", 0)
            _write_record_numeric("QUESTS", q, "reward_mithril", 0)


def _skill_kind_fields(skill: dict, unlock: int, sid: str) -> None:
    kind = str(skill.get("kind") or "damage")
    scale = 1.0 + unlock / 400.0
    _write_record_numeric_fallback("CLASS_SKILLS", skill, "cooldown", clamp(int(round((3.0 + 5.0 * stable_unit(sid + ':cd')) * (1.0 + unlock / 900.0))), 2, 12))
    magical = str(skill.get("scale", "")).lower() in ("intelligence", "willpower", "magic") or kind in ("heal", "group_heal", "drain")
    _write_record_numeric_fallback("CLASS_SKILLS", skill, "mana", 0 if not magical else max(1, int(round(4 + unlock * .055 + 8 * stable_unit(sid + ':mana')))))
    if kind in ("damage", "aoe", "aoe_damage", "drain", "execute"):
        _write_record_numeric_fallback("CLASS_SKILLS", skill, "mult", round((1.05 + .55 * scale) * stable_jitter(sid + ':mult', .09), 4))
    if kind == "boost":
        _write_record_numeric_fallback("CLASS_SKILLS", skill, "boost", round(clamp(1.12 + unlock / 1300.0 + stable_unit(sid) * .10, 1.12, 1.55), 4))
        _write_record_numeric_fallback("CLASS_SKILLS", skill, "duration", clamp(int(round(6 + unlock / 45.0)), 6, 16))
    if kind == "guard":
        _write_record_numeric_fallback("CLASS_SKILLS", skill, "guard", max(2, int(round(3 + unlock / 16.0))))
    if kind in ("heal", "group_heal"):
        base = .16 + unlock / 1800.0
        if kind == "group_heal":
            base *= .78
        _write_record_numeric_fallback("CLASS_SKILLS", skill, "heal_pct", round(clamp(base, .12, .42), 4))
    if kind == "drain":
        _write_record_numeric_fallback("CLASS_SKILLS", skill, "drain_pct", round(clamp(.18 + unlock / 2400.0, .18, .36), 4))
    if kind == "execute":
        _write_record_numeric_fallback("CLASS_SKILLS", skill, "execute_mult", round(1.35 + 0.45 * (unlock / MAX_LEVEL) * stable_jitter(sid + ':execute', .08), 4))
    if "self_damage" in skill:
        _write_record_numeric_fallback("CLASS_SKILLS", skill, "self_damage", max(1, int(round(2 + unlock / 80.0))))
    if "self_damage_pct" in skill:
        _write_record_numeric_fallback("CLASS_SKILLS", skill, "self_damage_pct", round(clamp(.025 + unlock / 8000.0, .025, .075), 4))



def _generate_skills(ns: dict) -> int:
    """Attach stage and fill only skill numbers that authored content omitted."""
    class_skills = ns.get("CLASS_SKILLS", {}) or {}
    count = 0
    for class_name, skills in class_skills.items():
        for idx, skill in enumerate(skills):
            count += 1
            try:
                unlock = int(skill.get("unlock", 1) or 1)
            except Exception:
                unlock = 1
            balance_level = clamp(unlock, 1, MAX_LEVEL)
            _write_record_numeric(
                "CLASS_SKILLS", skill, "generator_level", balance_level
            )
            _skill_kind_fields(
                skill,
                balance_level,
                str(skill.get("id") or f"{class_name}:{idx}"),
            )
    return count


def class_passive_profile(class_name: str) -> dict:
    """Compatibility wrapper to the authored class profile."""
    return authored_class_passive_profile(class_name)


def race_passive_profile(race_name: str) -> dict:
    """Compatibility wrapper to the authored race profile."""
    return authored_race_passive_profile(race_name)


def passive_text_pl(kind: str, value: float) -> str:
    return authored_passive_text_pl(kind, value)


def class_passive_text_pl(class_name: str) -> str:
    return authored_class_passive_text_pl(class_name)


def race_passive_text_pl(race_name: str) -> str:
    return authored_race_passive_text_pl(race_name)


def _generate_soul(ns: dict) -> None:
    """Deprecated no-op: Soul bonus numbers are authored content."""
    return None


def _generate_class_set_bonuses(ns: dict) -> None:
    """Deprecated no-op: CLASS_SET_BONUSES are authored per class."""
    return None


def _generate_class_race_numeric(ns: dict) -> None:
    """Deprecated no-op: class Soul Weapon bases are authored in CLASSES."""
    return None


def _rewrite_atlases(ns: dict, item_levels: dict[str, int]) -> None:
    """Numeric-only v0.30.18: atlas/unlock thresholds are authored semantics and are never rewritten."""
    return None




def _rewrite_area_targets(ns: dict, room_levels: dict[str, int], mob_levels: dict[str, int]) -> None:
    """Update only numeric target-power telemetry; never rewrite area/gate requirements."""
    targets = ns.get("EXP_AREA_TARGET_POWER")
    zone_map = ns.get("EXP_ZONE_AREA_ID", {}) or {}
    rooms = ns.get("ROOMS", {}) or {}
    if not isinstance(targets, dict):
        return
    by_area = defaultdict(list)
    for rid, room in rooms.items():
        area = zone_map.get(room.get("zone"))
        if area and rid in room_levels:
            by_area[area].append(room_levels[rid])
    mob_area_values = defaultdict(list)
    for rid, mid in (ns.get("MOB_SPAWNS", []) or []):
        room = rooms.get(rid, {})
        area = zone_map.get(room.get("zone"))
        if area and str(mid) in mob_levels:
            mob_area_values[area].append(mob_levels[str(mid)])
    for area in list(targets):
        values = mob_area_values.get(area) or by_area.get(area)
        if values:
            value = min(values)
        elif area == "trening":
            value = 1
        else:
            value = 1 + int(stable_unit(f"area:{area}") * (MAX_LEVEL - 1))
        _write_top_map_numeric(ns, "EXP_AREA_TARGET_POWER", area, value)




def runtime_room_level(room_id: str, room: dict, rooms: dict | None = None) -> int:
    """Assign numeric balance stage to runtime rooms without creating gameplay gates."""
    room_id = str(room_id or "room")
    room = room or {}
    lvl = semantic_floor_level(room)
    if lvl is None:
        text = f"{room_id} {room.get('zone','')} {room.get('name','')}".lower()
        m = re.search(r"(?:floor|level|poziom|pietro|piętro)[_ -]*(\d{1,5})", text)
        if m and any(k in text for k in ("crypt", "krypt", "astral", "tower", "wież", "fortress", "twierdz", "dungeon", "loch", "mine", "kopal")):
            lvl = int(m.group(1))
    if lvl is None and rooms:
        frontier = re.fullmatch(r"v0130_frontier_([a-z]+)_(\d{2})_(\d{2})", room_id)
        if frontier:
            kind, sx, sy = frontier.groups()
            gateway = rooms.get(f"v0130_gateway_{kind}", {})
            base = int(gateway.get("generator_level", 1) or 1)
            distance = int(sx) + int(sy)
            span = max(24, min(140, int(round((MAX_LEVEL - base) * 0.45))))
            lvl = base + int(round((distance / 22.0) * span))
    if lvl is None and rooms:
        linked = []
        for target in (room.get("exits") or {}).values():
            other = rooms.get(target, {})
            if other.get("generator_level") is not None:
                linked.append(int(other["generator_level"]))
        if linked:
            lvl = max(1, min(linked))
    if lvl is None:
        lvl = 1 + int(stable_unit(f"runtime-room:{room_id}") * (MAX_LEVEL - 1))
    try:
        recommended = int(room.get("recommended_mastery", 0) or 0)
    except (TypeError, ValueError, OverflowError):
        recommended = 0
    if recommended > 0:
        lvl = max(lvl, recommended)
    lvl = clamp(int(lvl), 1, MAX_LEVEL)
    _write_record_numeric("ROOMS", room, "generator_level", lvl)
    return lvl




NUMERIC_SKILL_FIELDS = {
    "generator_level", "cooldown", "mana", "mult", "boost", "duration", "guard",
    "heal_pct", "drain_pct", "execute_mult", "self_damage", "self_damage_pct",
}
NUMERIC_ITEM_FIELDS = {
    "generator_level", "price", "sell_silver", "sell_gold", "sell_mithril", "defense",
    "affix_amount", "heal", "mana", "soul_xp",
}
NUMERIC_MOB_FIELDS = {
    "generator_level", "v019_stage", "max_hp", "base_max_hp", "damage",
    "character_xp_reward", "class_xp_reward", "soul_reward", "stat_reward",
    "silver", "gold", "mithril",
}
NUMERIC_QUEST_FIELDS = {
    "generator_level", "character_xp_reward", "reward_soul_xp", "reward_stat_progress",
    "reward_profession_xp", "reward_tool_xp", "reward_silver", "reward_gold", "reward_mithril",
}
NUMERIC_RECIPE_FIELDS = {"generator_level", "xp", "profession_xp", "tool_xp"}


# v0.30.19: explicit, auditable write whitelist.
# Design chooses WHAT exists; Generator Core may only decide HOW MUCH.
GENERATOR_WRITE_WHITELIST = {
    "ROOMS": frozenset({"generator_level"}),
    "MOB_TEMPLATES": frozenset(NUMERIC_MOB_FIELDS),
    "ITEMS": frozenset(NUMERIC_ITEM_FIELDS),
    "QUESTS": frozenset(NUMERIC_QUEST_FIELDS),
    "CLASS_SKILLS": frozenset(NUMERIC_SKILL_FIELDS),
    "CRAFT_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),
    "COOK_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),
    "ALCHEMY_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),
    "JEWELCRAFT_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),
}
GENERATOR_NESTED_VALUE_WHITELIST = {
    "MOB_TEMPLATES": frozenset({"drops"}),
    "ITEMS": frozenset({"stats", "properties", "rune_stats", "rune_properties"}),
}
GENERATOR_TOP_LEVEL_VALUE_WHITELIST = frozenset({
    "EXP_AREA_TARGET_POWER",
})


_GENERATOR_WHITELIST_WRITE_COUNT = 0

def _write_record_numeric(domain: str, record: dict, field: str, value) -> None:
    global _GENERATOR_WHITELIST_WRITE_COUNT
    allowed = GENERATOR_WRITE_WHITELIST.get(domain, ())
    if field not in allowed:
        raise RuntimeError(f"Generator whitelist denied write: {domain}.{field}")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise RuntimeError(f"Generator whitelist denied non-numeric value: {domain}.{field}")
    record[field] = value
    _GENERATOR_WHITELIST_WRITE_COUNT += 1

def _write_record_numeric_fallback(
    domain: str,
    record: dict,
    field: str,
    value,
    minimum=None,
    preserve_none: bool = False,
):
    """Fill a numeric field only when design/runtime did not already author it."""
    if field in record:
        current = record.get(field)
        if current is None and preserve_none:
            return current
        if (
            isinstance(current, (int, float))
            and not isinstance(current, bool)
            and math.isfinite(float(current))
            and (minimum is None or float(current) >= float(minimum))
        ):
            return current
    _write_record_numeric(domain, record, field, value)
    return value


def _write_nested_numeric_fallback(domain: str, record: dict, field: str, leaf, value):
    """Keep authored nested numeric values such as item stats and drop chances."""
    mapping = record.get(field)
    if isinstance(mapping, dict) and leaf in mapping:
        current = mapping.get(leaf)
        if isinstance(current, (int, float)) and not isinstance(current, bool) and math.isfinite(float(current)):
            return current
    _write_nested_numeric(domain, record, field, leaf, value)
    return value


def _write_nested_numeric(domain: str, record: dict, field: str, leaf, value) -> None:
    global _GENERATOR_WHITELIST_WRITE_COUNT
    if field not in GENERATOR_NESTED_VALUE_WHITELIST.get(domain, ()):
        raise RuntimeError(f"Generator whitelist denied nested write: {domain}.{field}")
    mapping = record.get(field)
    if not isinstance(mapping, dict) or leaf not in mapping:
        raise RuntimeError(f"Generator whitelist denied new nested key: {domain}.{field}.{leaf}")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise RuntimeError(f"Generator whitelist denied non-numeric nested value: {domain}.{field}.{leaf}")
    mapping[leaf] = value
    _GENERATOR_WHITELIST_WRITE_COUNT += 1


def _write_top_sequence(ns: dict, key: str, values) -> None:
    global _GENERATOR_WHITELIST_WRITE_COUNT
    if key not in GENERATOR_TOP_LEVEL_VALUE_WHITELIST or key not in ns:
        raise RuntimeError(f"Generator whitelist denied top-level write: {key}")
    old = ns[key]
    new = tuple(values) if isinstance(old, tuple) else list(values) if isinstance(old, list) else values
    if isinstance(old, (tuple, list)) and len(new) != len(old):
        raise RuntimeError(f"Generator whitelist denied shape change: {key}")
    if isinstance(new, (tuple, list)) and any(
        not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(float(v))
        for v in new
    ):
        raise RuntimeError(f"Generator whitelist denied non-numeric sequence: {key}")
    ns[key] = new
    _GENERATOR_WHITELIST_WRITE_COUNT += len(new) if isinstance(new, (tuple, list)) else 1


def _write_top_map_numeric(ns: dict, key: str, leaf, value) -> None:
    global _GENERATOR_WHITELIST_WRITE_COUNT
    if key not in GENERATOR_TOP_LEVEL_VALUE_WHITELIST:
        raise RuntimeError(f"Generator whitelist denied top-map write: {key}")
    mapping = ns.get(key)
    if not isinstance(mapping, dict) or leaf not in mapping:
        raise RuntimeError(f"Generator whitelist denied new top-map key: {key}.{leaf}")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise RuntimeError(f"Generator whitelist denied non-numeric top-map value: {key}.{leaf}")
    mapping[leaf] = value
    _GENERATOR_WHITELIST_WRITE_COUNT += 1


def _write_class_set_numeric(entry: dict, field: str, value, leaf=None) -> None:
    raise RuntimeError(
        "Generator Core cannot mutate authored CLASS_SET_BONUSES"
    )

def _write_classes_weapon_bases(ns: dict, new_rows) -> None:
    raise RuntimeError(
        "Generator Core cannot mutate authored CLASSES Soul Weapon bases"
    )

def _freeze_semantic(value):
    if isinstance(value, dict):
        return tuple(sorted((str(k), _freeze_semantic(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_semantic(v) for v in value)
    if isinstance(value, set):
        return tuple(sorted((_freeze_semantic(v) for v in value), key=repr))
    return value


def _protected_record(record: dict, numeric_fields: set[str], numeric_map_fields=()) -> tuple:
    result = []
    for key, value in record.items():
        if key in numeric_fields:
            continue
        if key in numeric_map_fields and isinstance(value, dict):
            result.append((str(key), tuple(sorted(map(str, value.keys())))))
        elif key == "drops" and isinstance(value, dict):
            # Drop identity is semantic; probabilities are numeric balance.
            result.append(("drops", tuple(sorted(map(str, value.keys())))))
        else:
            result.append((str(key), _freeze_semantic(value)))
    return tuple(sorted(result))



def _class_row_whitelist_projection(row):
    """Only CLASSES[row][3] (Soul-weapon numeric base) may change."""
    seq = list(row) if isinstance(row, (list, tuple)) else [row]
    if len(seq) >= 4:
        seq[3] = "<GENERATOR_NUMERIC>"
    return _freeze_semantic(seq)


def _class_set_whitelist_projection(table):
    """Protect class-set identity; allow only existing numeric values."""
    out = {}
    for cname, entry in (table or {}).items():
        if not isinstance(entry, dict):
            out[str(cname)] = _freeze_semantic(entry)
            continue
        row = {}
        for key, value in entry.items():
            if key == "stats" and isinstance(value, dict):
                row[key] = tuple(sorted((str(stat), "<GENERATOR_NUMERIC>") for stat in value))
            elif key in ("damage", "defense", "vitality"):
                row[key] = "<GENERATOR_NUMERIC>"
            else:
                row[key] = _freeze_semantic(value)
        out[str(cname)] = tuple(sorted(row.items()))
    return _freeze_semantic(out)


def _value_container_whitelist_projection(value):
    """Keep container shape/keys, hide only numeric values."""
    if isinstance(value, dict):
        return tuple(sorted((str(k), "<GENERATOR_NUMERIC>") for k in value))
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, len(value), tuple("<GENERATOR_NUMERIC>" for _ in value))
    return "<GENERATOR_NUMERIC>"


def generator_whitelist_fingerprint(ns: dict) -> str:
    """Cheap shape fingerprint; safe setters enforce every Generator write."""
    protected = [("TOP_LEVEL_KEYS", tuple(sorted(str(k) for k in ns.keys())))]
    # Top-level write domains may change values only, never shape/keys.
    protected.append(("CLASSES_SHAPE", tuple(len(row) for row in (ns.get("CLASSES", ()) or ()))))
    protected.append(("CLASS_SET_KEYS", tuple(
        (str(cname),
         tuple(sorted(str(k) for k in entry.keys())) if isinstance(entry, dict) else ("<NON_DICT>",),
         tuple(sorted(str(k) for k in (entry.get("stats") or {}).keys())) if isinstance(entry, dict) and isinstance(entry.get("stats"), dict) else ())
        for cname, entry in (ns.get("CLASS_SET_BONUSES", {}) or {}).items()
    )))
    protected.append(("EXP_AREA_KEYS", tuple(sorted(str(k) for k in (ns.get("EXP_AREA_TARGET_POWER", {}) or {}).keys()))))
    for key in sorted(GENERATOR_TOP_LEVEL_VALUE_WHITELIST - {"CLASSES", "CLASS_SET_BONUSES", "EXP_AREA_TARGET_POWER"}):
        value = ns.get(key)
        if isinstance(value, dict):
            shape = ("dict", tuple(sorted(str(k) for k in value.keys())))
        elif isinstance(value, (list, tuple)):
            shape = (type(value).__name__, len(value))
        else:
            shape = (type(value).__name__,)
        protected.append((key, shape))
    return hashlib.sha256(repr(tuple(protected)).encode("utf-8")).hexdigest()





def _is_generator_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _validate_record_whitelist_numbers(ns: dict, errors: list[str]) -> int:
    checked = 0
    for table_name, allowed in GENERATOR_WRITE_WHITELIST.items():
        table = ns.get(table_name, {}) or {}
        if not isinstance(table, dict):
            errors.append(f"whitelist table {table_name} is not dict")
            continue
        nested = GENERATOR_NESTED_VALUE_WHITELIST.get(table_name, ())
        for rid, record in table.items():
            if not isinstance(record, dict):
                continue
            for field in allowed:
                if field in record:
                    checked += 1
                    if not _is_generator_number(record[field]):
                        errors.append(f"non-numeric whitelisted value {table_name}.{rid}.{field}")
            for field in nested:
                mapping = record.get(field)
                if mapping is None:
                    continue
                if not isinstance(mapping, dict):
                    errors.append(f"whitelist nested field {table_name}.{rid}.{field} is not dict")
                    continue
                for leaf, value in mapping.items():
                    checked += 1
                    if not _is_generator_number(value):
                        errors.append(f"non-numeric whitelisted value {table_name}.{rid}.{field}.{leaf}")
    return checked


def generator_whitelist_validate(ns: dict, before_fingerprint: str) -> dict:
    after = generator_whitelist_fingerprint(ns)
    errors = []
    if before_fingerprint != after:
        errors.append("Generator Core changed a protected whitelist shape/key")
    return {
        "version": GENERATOR_VERSION,
        "enforced": True,
        "passed": not errors,
        "fingerprint_before": before_fingerprint,
        "fingerprint_after": after,
        "numeric_values_checked": int(_GENERATOR_WHITELIST_WRITE_COUNT),
        "error_count": len(errors),
        "errors": errors,
        "record_whitelist": {k: tuple(sorted(v)) for k, v in GENERATOR_WRITE_WHITELIST.items()},
        "nested_value_whitelist": {k: tuple(sorted(v)) for k, v in GENERATOR_NESTED_VALUE_WHITELIST.items()},
        "top_level_value_whitelist": tuple(sorted(GENERATOR_TOP_LEVEL_VALUE_WHITELIST)),
    }



def semantic_fingerprint(ns: dict) -> str:
    """Hash all authored semantics that Generator Core is forbidden to change."""
    protected = []
    protected.append(("CLASSES", _freeze_semantic(ns.get("CLASSES", ()))))
    protected.append(("RACES", _freeze_semantic(ns.get("RACES", ()))))
    protected.append(("CLASS_DESCRIPTIONS", _freeze_semantic(ns.get("CLASS_DESCRIPTIONS", {}))))
    protected.append(("CLASS_STARTING_STAT_BONUSES", _freeze_semantic(ns.get("CLASS_STARTING_STAT_BONUSES", {}))))
    constants = (
        "SOUL_MAX_LEVEL", "SOUL_MAX_TIER", "SOUL_TIER_THRESHOLDS", "TIER2_LEVEL", "TIER3_LEVEL", "TIER4_LEVEL", "TIER5_LEVEL",
        "SOUL_SKILL_UNLOCK_LEVELS", "SOUL_MILESTONE_TIERS", "SOUL_MILESTONE_NAMES",
        "SOUL_TIER_POWER_BONUSES", "SOUL_TIER_CLASS_BONUS_PERCENT",
        "SOUL_TIER_DODGE_BONUS", "SOUL_TIER_GUARDIAN_REDUCTION",
        "SOUL_MILESTONE_SPECIALIZATION_BONUS", "SOUL_MILESTONE_DODGE_BONUS",
        "SOUL_MILESTONE_GUARDIAN_REDUCTION",
        "PROFESSION_RANK_THRESHOLDS", "PROFESSION_MAX_RANK", "BLACKSMITHING_RANK_THRESHOLDS", "BLACKSMITHING_MAX_RANK",
        "TOOL_TIER_THRESHOLDS", "TOOL_MAX_TIER", "ASTRAL_MIN_SOUL_LEVEL", "MYTHIC_CRYPT_MIN_SOUL_LEVEL", "MYTHIC_ASTRAL_MIN_SOUL_LEVEL",
    )
    protected.append(("CONSTANTS", tuple((k, _freeze_semantic(ns.get(k))) for k in constants)))
    protected.append(("SKILLS", tuple(
        (str(cname), tuple(_protected_record(s, NUMERIC_SKILL_FIELDS) for s in rows))
        for cname, rows in (ns.get("CLASS_SKILLS", {}) or {}).items()
    )))
    protected.append(("ITEMS", tuple(
        (str(iid), _protected_record(item, NUMERIC_ITEM_FIELDS, ("stats", "properties", "rune_stats", "rune_properties")))
        for iid, item in (ns.get("ITEMS", {}) or {}).items()
    )))
    protected.append(("MOBS", tuple(
        (str(mid), _protected_record(mob, NUMERIC_MOB_FIELDS))
        for mid, mob in (ns.get("MOB_TEMPLATES", {}) or {}).items()
    )))
    protected.append(("QUESTS", tuple(
        (str(qid), _protected_record(q, NUMERIC_QUEST_FIELDS))
        for qid, q in (ns.get("QUESTS", {}) or {}).items()
    )))
    recipes = []
    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):
        recipes.append((table_name, tuple(
            (str(rid), _protected_record(recipe, NUMERIC_RECIPE_FIELDS))
            for rid, recipe in (ns.get(table_name, {}) or {}).items()
        )))
    protected.append(("RECIPES", tuple(recipes)))
    protected.append(("NPCS", _freeze_semantic(ns.get("NPCS", {}))))
    protected.append(("MOB_SPAWNS", _freeze_semantic(ns.get("MOB_SPAWNS", ()))))
    protected.append(("ROOMS", tuple(
        (str(rid), _protected_record(room, {"generator_level"}))
        for rid, room in (ns.get("ROOMS", {}) or {}).items()
    )))
    protected.append(("ATLASES", _freeze_semantic({
        "ORE_ATLAS_LEVELS": ns.get("ORE_ATLAS_LEVELS", {}),
        "ORE_MINE_FLOOR_MINIMUMS": ns.get("ORE_MINE_FLOOR_MINIMUMS", {}),
        "WOOD_ATLAS_ROOM_MIN_LEVELS": ns.get("WOOD_ATLAS_ROOM_MIN_LEVELS", {}),
        "HERB_ATLAS_ROOM_MIN_LEVELS": ns.get("HERB_ATLAS_ROOM_MIN_LEVELS", {}),
    })))
    protected.append(("EXP_AREAS", _freeze_semantic(ns.get("EXP_AREAS", ()))))
    protected.append((
        "CLASS_SET_BONUSES",
        _freeze_semantic(ns.get("CLASS_SET_BONUSES", {})),
    ))
    return hashlib.sha256(repr(tuple(protected)).encode("utf-8")).hexdigest()

def authored_reward_snapshot(ns: dict) -> dict:
    """Capture only quest/recipe numeric values authored before Generator runs."""
    quest_fields = tuple(sorted(NUMERIC_QUEST_FIELDS - {"generator_level"}))
    recipe_fields = tuple(sorted(NUMERIC_RECIPE_FIELDS - {"generator_level"}))
    quests = {}
    for qid, quest in (ns.get("QUESTS", {}) or {}).items():
        quests[str(qid)] = {
            field: _freeze_semantic(quest[field])
            for field in quest_fields
            if field in quest
        }
    recipes = {}
    for table_name in (
        "CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"
    ):
        recipes[table_name] = {}
        for rid, recipe in (ns.get(table_name, {}) or {}).items():
            recipes[table_name][str(rid)] = {
                field: _freeze_semantic(recipe[field])
                for field in recipe_fields
                if field in recipe
            }
    # generator_level is Generator-owned telemetry, not authored skill balance.
    # Protect every actual combat number that existed before Generator runs.
    skill_fields = tuple(sorted(NUMERIC_SKILL_FIELDS - {"generator_level"}))
    skills = {}
    for class_name, rows in (ns.get("CLASS_SKILLS", {}) or {}).items():
        skills[str(class_name)] = {}
        for index, skill in enumerate(rows):
            sid = str(skill.get("id") or f"index:{index}")
            skills[str(class_name)][sid] = {
                field: _freeze_semantic(skill[field])
                for field in skill_fields
                if field in skill
            }
    return {"quests": quests, "recipes": recipes, "skills": skills}


def authored_reward_differences(ns: dict, before: dict) -> list[str]:
    """Explain any authored numeric mutation with an exact domain/id/field diff."""
    differences = []
    if not isinstance(before, dict):
        return ["snapshot: invalid before-state"]

    quests_now = ns.get("QUESTS", {}) or {}
    for qid, fields in (before.get("quests") or {}).items():
        current = quests_now.get(qid)
        if not isinstance(current, dict):
            differences.append(f"quest/{qid}: row missing")
            continue
        for field, expected in fields.items():
            actual = _freeze_semantic(current.get(field)) if field in current else "<missing>"
            if actual != expected:
                differences.append(f"quest/{qid}/{field}: {expected!r} -> {actual!r}")

    for table_name, rows in (before.get("recipes") or {}).items():
        table_now = ns.get(table_name, {}) or {}
        for rid, fields in rows.items():
            current = table_now.get(rid)
            if not isinstance(current, dict):
                differences.append(f"{table_name}/{rid}: row missing")
                continue
            for field, expected in fields.items():
                actual = _freeze_semantic(current.get(field)) if field in current else "<missing>"
                if actual != expected:
                    differences.append(
                        f"{table_name}/{rid}/{field}: {expected!r} -> {actual!r}"
                    )

    skills_now = ns.get("CLASS_SKILLS", {}) or {}
    for class_name, rows in (before.get("skills") or {}).items():
        current_rows = {
            str(skill.get("id") or f"index:{index}"): skill
            for index, skill in enumerate(skills_now.get(class_name, ()) or ())
        }
        for sid, fields in rows.items():
            current = current_rows.get(sid)
            if not isinstance(current, dict):
                differences.append(f"skill/{class_name}/{sid}: row missing")
                continue
            for field, expected in fields.items():
                actual = _freeze_semantic(current.get(field)) if field in current else "<missing>"
                if actual != expected:
                    differences.append(
                        f"skill/{class_name}/{sid}/{field}: {expected!r} -> {actual!r}"
                    )
    return differences


def authored_rewards_preserved(ns: dict, before: dict) -> bool:
    """Every pre-existing authored quest/recipe/skill numeric value is immutable."""
    return not authored_reward_differences(ns, before)


def _authored_rewards_preserved_legacy_removed(ns: dict, before: dict) -> bool:
    """Legacy implementation retained only as source history; never called."""
    if not isinstance(before, dict):
        return False
    quests_now = ns.get("QUESTS", {}) or {}
    for qid, fields in (before.get("quests") or {}).items():
        current = quests_now.get(qid)
        if not isinstance(current, dict):
            return False
        for field, expected in fields.items():
            if field not in current or _freeze_semantic(current[field]) != expected:
                return False
    for table_name, rows in (before.get("recipes") or {}).items():
        table_now = ns.get(table_name, {}) or {}
        for rid, fields in rows.items():
            current = table_now.get(rid)
            if not isinstance(current, dict):
                return False
            for field, expected in fields.items():
                if field not in current or _freeze_semantic(current[field]) != expected:
                    return False

    skills_now = ns.get("CLASS_SKILLS", {}) or {}
    for class_name, rows in (before.get("skills") or {}).items():
        current_rows = {
            str(skill.get("id") or f"index:{index}"): skill
            for index, skill in enumerate(skills_now.get(class_name, ()) or ())
        }
        for sid, fields in rows.items():
            current = current_rows.get(sid)
            if not isinstance(current, dict):
                return False
            for field, expected in fields.items():
                if field not in current or _freeze_semantic(current[field]) != expected:
                    return False
    return True

def validate(ns: dict) -> dict:
    errors = []
    mobs = ns.get("MOB_TEMPLATES", {})
    items = ns.get("ITEMS", {})
    quests = ns.get("QUESTS", {})
    skills = ns.get("CLASS_SKILLS", {})
    recipes = sum((len(ns.get(name, {}) or {}) for name in ("CRAFT_RECIPES","COOK_RECIPES","ALCHEMY_RECIPES","JEWELCRAFT_RECIPES")), 0)
    for mid, t in mobs.items():
        lvl = int(t.get("generator_level", 0) or 0)
        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"mob level {mid}")
        rank = mob_rank(t)
        if int(t.get("max_hp",0) or 0) <= 0: errors.append(f"mob hp {mid}")
        if int(t.get("damage",0) or 0) <= 0: errors.append(f"mob damage {mid}")
        if int(t.get("character_xp_reward",0) or 0) < 0: errors.append(f"mob charxp {mid}")
        if int(t.get("class_xp_reward",0) or 0) < 0: errors.append(f"mob classxp {mid}")
        if int(t.get("soul_reward",0) or 0) < 0: errors.append(f"mob soulxp {mid}")
        if int(t.get("stat_reward",0) or 0) < 0: errors.append(f"mob statxp {mid}")
        if any(int(t.get(key,0) or 0) < 0 for key in ("silver", "gold", "mithril")):
            errors.append(f"mob currency {mid}")
    for iid, item in items.items():
        lvl = int(item.get("generator_level",0) or 0)
        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"item level {iid}")
        # price=None is an authored "not sold" contract and must survive the
        # restrained generator. Missing prices still receive a generated value.
        if item.get("price") is not None and int(item.get("price",0) or 0) <= 0:
            errors.append(f"item price {iid}")
    for qid, q in quests.items():
        lvl = int(q.get("generator_level",0) or 0)
        if not 1 <= lvl <= MAX_LEVEL:
            errors.append(f"quest level {qid}")
        for field in (
            "character_xp_reward", "reward_soul_xp", "reward_stat_progress",
            "reward_profession_xp", "reward_tool_xp",
        ):
            if field in q and int(q.get(field, 0) or 0) < 0:
                errors.append(f"quest negative {field} {qid}")
        silver = int(q.get("reward_silver",0) or 0)
        gold = int(q.get("reward_gold",0) or 0)
        mithril = int(q.get("reward_mithril",0) or 0)
        if min(silver, gold, mithril) < 0:
            errors.append(f"quest negative currency {qid}")
        manual = q.get("manual_currency_reward_coins")
        if manual is not None:
            expected = clamp(int(manual), 0, SAFE_INT)
            if silver != expected or gold != 0 or mithril != 0:
                errors.append(
                    f"quest manual currency changed {qid}: "
                    f"{silver}/{gold}/{mithril}!={expected}/0/0"
                )
    skill_count = 0
    skill_grid = (1, *range(10, MAX_LEVEL + 1, 10))
    skill_grid_set = set(skill_grid)
    for cname, rows in skills.items():
        unlocks = []
        per_unlock = defaultdict(int)
        for s in rows:
            skill_count += 1
            try: unlock = int(s.get("unlock",0) or 0)
            except Exception: unlock = 0
            unlocks.append(unlock)
            if not 1 <= unlock <= MAX_LEVEL: errors.append(f"skill level {s.get('id')}")
            if cname not in ("Inżynier","Mec") and unlock not in skill_grid_set: errors.append(f"skill off-grid {s.get('id')}:{unlock}")
            per_unlock[unlock] += 1
        if unlocks and (min(unlocks) != 1 or max(unlocks) != MAX_LEVEL): errors.append(f"skill span {cname}")
        if cname not in ("Inżynier","Mec"):
            for level in skill_grid:
                rows_at_level = [
                    skill for skill in rows
                    if int(skill.get("unlock", 0) or 0) == int(level)
                ]
                actual = len(rows_at_level)
                if actual < 3:
                    errors.append(
                        f"skill grid {cname}:{level}={actual} expected minimum 3"
                    )
                    continue
                if actual > 3:
                    source_authored = sum(
                        1 for skill in rows_at_level
                        if any(str(key).startswith("source_") for key in skill)
                    )
                    extras = actual - 3
                    if source_authored < extras:
                        errors.append(
                            f"skill grid {cname}:{level}={actual}; "
                            f"{extras} extra but only {source_authored} source-authored"
                        )
    for table_name in ("CRAFT_RECIPES","COOK_RECIPES","ALCHEMY_RECIPES","JEWELCRAFT_RECIPES"):
        for rid, recipe in (ns.get(table_name, {}) or {}).items():
            lvl = int(recipe.get("generator_level", 0) or 0)
            if not 1 <= lvl <= MAX_LEVEL: errors.append(f"recipe level {rid}")
            if int(recipe.get("profession_xp",0) or 0) < 0:
                errors.append(f"recipe negative profession xp {rid}")
            if int(recipe.get("tool_xp",0) or 0) < 0:
                errors.append(f"recipe negative tool xp {rid}")
    for fn_name, fn in (("mob_hp", mob_hp),("mob_damage",mob_damage)):
        vals = [fn(l) for l in range(1, MAX_LEVEL+1)]
        if any(b < a for a,b in zip(vals, vals[1:])): errors.append(f"nonmonotonic {fn_name}")
    for axis in AXIS_CURVES:
        vals = [axis_requirement(axis,l) for l in range(1, MAX_LEVEL+1)]
        if any(b < a for a,b in zip(vals,vals[1:])): errors.append(f"nonmonotonic {axis}")
    return {
        "errors": errors,
        "error_count": len(errors),
        "mobs": len(mobs), "items": len(items), "quests": len(quests),
        "skills": skill_count, "recipes": recipes, "rooms": len(ns.get("ROOMS",{})),
    }



def apply_generator_core(ns: dict) -> dict:
    global _GENERATOR_WHITELIST_WRITE_COUNT
    _GENERATOR_WHITELIST_WRITE_COUNT = 0
    full_audit = os.environ.get("SOULBOUND_FULL_AUDIT", "").strip().lower() in ("1", "true", "yes", "on")
    if full_audit:
        semantic_before = semantic_fingerprint(ns)
        whitelist_before = generator_whitelist_fingerprint(ns)
        authored_rewards_before = authored_reward_snapshot(ns)
    else:
        semantic_before = None
        whitelist_before = None
        authored_rewards_before = None

    # Soul, class/race identity and class set bonuses are authored and never
    # mutated here. Generator starts at shared stage derivation.
    room_levels = _graph_room_levels(ns.get("ROOMS", {}) or {})
    mob_levels = _mob_levels(ns, room_levels)
    _generate_mobs(ns, mob_levels)
    item_levels = _item_levels(ns, mob_levels)
    _generate_items(ns, item_levels)
    recipe_count = _generate_recipes(ns, item_levels)
    _generate_quests(ns, mob_levels, item_levels)
    skill_count = _generate_skills(ns)
    _rewrite_atlases(ns, item_levels)
    _rewrite_area_targets(ns, room_levels, mob_levels)

    if full_audit:
        semantic_after = semantic_fingerprint(ns)
        whitelist_audit = generator_whitelist_validate(ns, whitelist_before)
        audit = validate(ns)
        semantic_ok = semantic_before == semantic_after
        authored_reward_differences_v11330 = authored_reward_differences(
            ns, authored_rewards_before
        )
        authored_rewards_ok = not authored_reward_differences_v11330
        audit["semantic_fingerprint_before"] = semantic_before
        audit["semantic_fingerprint_after"] = semantic_after
        audit["semantic_preserved"] = semantic_ok
        audit["authored_rewards_preserved"] = authored_rewards_ok
        audit["authored_reward_differences"] = tuple(
            authored_reward_differences_v11330[:100]
        )
        audit["whitelist_enforced"] = True
        audit["whitelist_passed"] = bool(whitelist_audit.get("passed"))
        audit["whitelist_audit"] = whitelist_audit
        if not semantic_ok:
            audit["errors"].append("Generator Core changed protected authored semantics")
        if not authored_rewards_ok:
            audit["errors"].append(
                "Generator Core changed pre-existing authored quest/recipe/skill numeric values: "
                + "; ".join(authored_reward_differences_v11330[:20])
            )
        if not whitelist_audit.get("passed"):
            audit["errors"].extend(whitelist_audit.get("errors", []))
        audit["error_count"] = len(audit["errors"])
    else:
        audit = {
            "errors": [], "error_count": 0, "runtime_fast_path": True,
            "semantic_preserved": None, "authored_rewards_preserved": None,
            "whitelist_enforced": False,
            "whitelist_passed": None, "whitelist_audit": None,
            "mobs": len(ns.get("MOB_TEMPLATES", {}) or {}),
            "items": len(ns.get("ITEMS", {}) or {}),
            "quests": len(ns.get("QUESTS", {}) or {}),
            "skills": sum(len(rows) for rows in (ns.get("CLASS_SKILLS", {}) or {}).values()),
            "recipes": sum(len(ns.get(name, {}) or {}) for name in ("CRAFT_RECIPES","COOK_RECIPES","ALCHEMY_RECIPES","JEWELCRAFT_RECIPES")),
            "rooms": len(ns.get("ROOMS", {}) or {}),
        }

    audit["recipe_count_generated"] = recipe_count
    audit["skill_count_generated"] = skill_count
    audit["numeric_only"] = True
    ns["GENERATOR_CORE_AUDIT"] = audit
    ns["GENERATOR_CORE_VERSION"] = GENERATOR_VERSION
    ns["GENERATOR_ROOM_LEVELS"] = room_levels
    ns["GENERATOR_MOB_LEVELS"] = mob_levels
    ns["GENERATOR_ITEM_LEVELS"] = item_levels
    return audit

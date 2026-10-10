"""Stable authored game balancing curves and progression mathematics.

Only calculations and *explicitly requested* runtime room/mob scaling live here.
Never rewrite static item, quest, class, skill or recipe catalogs.
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

BALANCE_MATH_VERSION = "1.28.6"
MAX_LEVEL = 800
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
    """Map an ordinal system level to the shared 1-800 balance stage."""
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
    """Compatibility wrapper; player stat progression lives outside balance formulas."""
    return authored_uncapped_stat_xp_scale(stat_level)


def uncapped_stat_xp_gain(base_amount: int, stat_level: int) -> int:
    """Compatibility wrapper; player stat progression lives outside balance formulas."""
    return authored_uncapped_stat_xp_gain(base_amount, stat_level)


def axis_gain(axis: str, level: int, intensity: float = 1.0) -> int:
    target = AXIS_TARGET_ACTIONS[axis]
    value = axis_requirement(axis, level) / float(target) * max(0.05, float(intensity))
    return min(SAFE_INT, max(1, int(round(value))))


def character_hp_base(character_level: int, constitution: int) -> int:
    """Compatibility wrapper; authored character resources live outside balance formulas."""
    return authored_character_hp_base(character_level, constitution)


def character_mana_base(
    character_level: int,
    intelligence: int,
    willpower: int | None = None,
) -> int:
    """Compatibility wrapper; authored character resources live outside balance formulas."""
    return authored_character_mana_base(character_level, intelligence, willpower)


def character_attribute_power(character_level: int, stat_value: int) -> int:
    """Compatibility wrapper; player combat math lives outside balance formulas."""
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
# balance formulas keeps compatibility wrappers only; duplicate audits here would
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
    """Compatibility wrapper; profession tempo is authored outside balance formulas."""
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



def _assign_runtime_number(table: str, record: dict, key: str, value):
    """Assign balance numbers only to fresh, explicitly procedural entities."""
    if table not in ("ROOMS", "MOB_TEMPLATES"):
        raise ValueError("Runtime balance is forbidden to mutate authored catalogs")
    record[key] = value

def _assign_runtime_drop(record: dict, key: str, chance: float):
    if key not in (record.get("drops") or {}):
        raise ValueError("Runtime drop may not add an authored drop identifier")
    record["drops"][key] = chance

def runtime_mob_balance(template_id: str, template: dict, level: int, rank: str | None = None) -> dict:
    """Balance whitelisted numeric fields of a runtime mob; semantic identity stays authored."""
    level = clamp(int(level), 1, MAX_LEVEL)
    rank = str(rank or mob_rank(template))
    _assign_runtime_number("MOB_TEMPLATES", template, "generator_level", level)
    _assign_runtime_number("MOB_TEMPLATES", template, "v019_stage", level)
    hp = mob_hp(level, rank)
    _assign_runtime_number("MOB_TEMPLATES", template, "max_hp", hp)
    _assign_runtime_number("MOB_TEMPLATES", template, "base_max_hp", hp)
    _assign_runtime_number("MOB_TEMPLATES", template, "damage", mob_damage(level, rank))
    reward_mult = RANK_REWARD.get(rank, 1.0)
    _assign_runtime_number("MOB_TEMPLATES", template, "character_xp_reward", axis_gain("character", level, reward_mult))
    _assign_runtime_number("MOB_TEMPLATES", template, "class_xp_reward", axis_gain("class", level, reward_mult))
    _assign_runtime_number("MOB_TEMPLATES", template, "soul_reward", axis_gain("soul", level, reward_mult))
    _assign_runtime_number("MOB_TEMPLATES", template, "stat_reward", axis_gain("stat", level, reward_mult))
    _assign_runtime_number("MOB_TEMPLATES", template, "silver", currency_for_stage(level, rank))
    _assign_runtime_number("MOB_TEMPLATES", template, "gold", 0)
    _assign_runtime_number("MOB_TEMPLATES", template, "mithril", 0)
    drops = template.get("drops")
    if isinstance(drops, dict) and drops:
        base_chance = {"normal": .055, "elite": .09, "rare": .14, "mini": .22, "boss": .34, "world_boss": .48}.get(rank, .055)
        count = max(1, len(drops))
        for item_id in list(drops):
            chance = base_chance * stable_jitter(f"{template_id}:{item_id}", .22) / (count ** .20)
            _assign_runtime_drop(template, item_id, round(clamp(chance, .005, .85), 5))
    return template

def runtime_room_level(room_id: str, room: dict, rooms: dict | None = None) -> int:
    """Assign numeric balance stage to runtime rooms without creating gameplay gates."""
    room_id = str(room_id or "room")
    room = room or {}
    # The original temple basement is the onboarding zone, not a random
    # progression dungeon. Never inherit levels from nearby high-stage rooms.
    if room_id.startswith("temple_basement") and room.get("zone") == "Piwnica Świątyni":
        _assign_runtime_number("ROOMS", room, "generator_level", 1)
        return 1
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
    _assign_runtime_number("ROOMS", room, "generator_level", lvl)
    return lvl


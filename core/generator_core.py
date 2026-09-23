"""Soulbound v0.30.24 Generator Core — Numeric Whitelist + Hybrid Quest Rewards.

Numeric-only balance layer. Authored identity, names, IDs, unlock thresholds, requirements,
quest/recipe structure, class equipment identity and world semantics are immutable here.
Generator Core may only derive numeric balance values such as HP, damage, XP, prices,
automatic reward amounts, cooldowns, mana costs and numeric effect strength. Quests explicitly
marked with manual_currency_reward_coins keep that authored currency reward unchanged. Base player attributes
from race/class profiles are intentionally NOT generated.
"""
from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import math
import re
import os

GENERATOR_VERSION = "0.52.0"
MAX_LEVEL = 400
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
    """Map an ordinal system level to the shared 1-400 Generator Core stage."""
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
    """Scale a stage-balanced stat XP reward to an uncapped stat level.

    Level 1-400 keeps the original reward exactly. Above 400, the reward
    grows in the same proportion as the generated requirement. This keeps
    a stage-400 source at roughly the same actions-per-stat-point while
    low-stage sources remain proportionally inefficient forever.
    """
    level = max(1, int(stat_level))
    if level <= MAX_LEVEL:
        return 1.0
    anchor = float(axis_requirement("stat", MAX_LEVEL))
    current = float(axis_requirement("stat", level))
    return max(1.0, current / max(1.0, anchor))


def uncapped_stat_xp_gain(base_amount: int, stat_level: int) -> int:
    base_amount = max(0, int(base_amount))
    if base_amount <= 0:
        return 0
    return min(SAFE_INT, max(1, int(round(base_amount * uncapped_stat_xp_scale(stat_level)))))


def axis_gain(axis: str, level: int, intensity: float = 1.0) -> int:
    target = AXIS_TARGET_ACTIONS[axis]
    value = axis_requirement(axis, level) / float(target) * max(0.05, float(intensity))
    return min(SAFE_INT, max(1, int(round(value))))


def character_hp_base(character_level: int, constitution: int) -> int:
    character_level = clamp(int(character_level), 1, MAX_LEVEL)
    constitution = max(1, int(constitution))
    return max(1, int(round(48 + constitution * 5.2 + character_level * 3.1)))


def character_mana_base(character_level: int, intelligence: int, willpower: int | None = None) -> int:
    character_level = clamp(int(character_level), 1, MAX_LEVEL)
    intelligence = max(1, int(intelligence))
    willpower = intelligence if willpower is None else max(1, int(willpower))
    return max(0, int(round(22 + intelligence * 2.4 + willpower * 2.4 + character_level * 2.0)))


def character_attribute_power(character_level: int, stat_value: int) -> int:
    character_level = clamp(int(character_level), 1, MAX_LEVEL)
    stat_value = max(1, int(stat_value))
    return max(1, int(round(stat_value + 0.30 * character_level)))


def speed_from_dexterity(dexterity: int) -> int:
    dexterity = max(1, int(dexterity))
    return max(1, int(round(8 + dexterity * 1.65)))


def dodge_from_dexterity(dexterity: int) -> float:
    dexterity = max(1, int(dexterity))
    value = 0.25 * (1.0 - math.exp(-max(0.0, dexterity - 10.0) / 78.0))
    return round(clamp(value, 0.0, 0.25), 6)


def critical_chance_from_dexterity(dexterity: int) -> float:
    dexterity = max(1, int(dexterity))
    value = 0.035 + 0.285 * (1.0 - math.exp(-max(0.0, dexterity - 8.0) / 105.0))
    return round(clamp(value, 0.035, 0.35), 6)


def critical_multiplier(character_level: int) -> float:
    level = clamp(int(character_level), 1, MAX_LEVEL)
    return round(1.45 + 0.20 * ((level - 1) / (MAX_LEVEL - 1)) ** 0.75, 6)


def magic_defense_base(character_level: int, willpower: int) -> int:
    character_level = clamp(int(character_level), 1, MAX_LEVEL)
    willpower = max(1, int(willpower))
    return max(0, int(round(willpower * 0.55 + character_level * 0.10)))


def skill_level_power(level: int) -> float:
    level = clamp(int(level), 1, MAX_LEVEL)
    # v0.33.2 Full Progression Rebalance: every Skill Level must be felt.
    # 1=1.00x, 50~=1.54x, 100~=1.96x, 200~=2.70x, 300~=3.37x, 400=4.00x.
    return round(1.0 + 3.0 * ((level - 1) / (MAX_LEVEL - 1)) ** 0.82, 6)


def skill_cooldown_factor(level: int) -> float:
    level = clamp(int(level), 1, MAX_LEVEL)
    # Utility, evade and control skills improve through shorter cooldowns as well.
    reduction = 0.50 * ((level - 1) / (MAX_LEVEL - 1)) ** 0.90
    return round(1.0 - reduction, 6)


def profession_action_seconds(tool_type: str, level: int) -> int:
    level = clamp(int(level), 1, MAX_LEVEL)
    # Tool identity changes feel deterministically, not through hand-authored per-tool timers.
    u = stable_unit(f"{tool_type}:action-time")
    base = 14.0 + 14.0 * u
    minimum = 3.0 + 5.0 * stable_unit(f"{tool_type}:minimum-time")
    progress = ((level - 1) / (MAX_LEVEL - 1)) ** 0.78
    return max(1, int(round(base - (base - minimum) * progress)))


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
    base = 7.0 * ((1.0 + level / 9.0) ** 2.18)
    return min(SAFE_INT, max(1, int(round(base * RANK_REWARD.get(rank, 1.0)))))


def item_price_for_stage(level: int, rarity_mult: float = 1.0) -> int:
    level = clamp(int(level), 1, MAX_LEVEL)
    base = 18.0 * ((1.0 + level / 8.0) ** 2.05)
    return min(SAFE_INT, max(1, int(round(base * max(0.25, rarity_mult)))))


QUEST_CURRENCY_ANCHORS = (
    (1, 1_200), (10, 1_500), (25, 2_500), (50, 5_000),
    (100, 10_000), (150, 20_000), (200, 40_000), (250, 100_000),
    (300, 1_000_000), (350, 50_000_000), (400, 1_000_000_000),
)

def _economy_anchor_value(level: int, anchors=QUEST_CURRENCY_ANCHORS) -> int:
    level = clamp(int(level), 1, MAX_LEVEL)
    if level <= anchors[0][0]: return int(anchors[0][1])
    if level >= anchors[-1][0]: return int(anchors[-1][1])
    for (l0,v0),(l1,v1) in zip(anchors, anchors[1:]):
        if l0 <= level <= l1:
            t=(level-l0)/float(l1-l0)
            # Log interpolation keeps the late-game mithril transition smooth.
            value=math.exp(math.log(max(1.0,float(v0))) + (math.log(max(1.0,float(v1)))-math.log(max(1.0,float(v0))))*t)
            return min(SAFE_INT,max(1,int(round(value))))
    return int(anchors[-1][1])

def quest_currency_for_stage(level: int, workload: float = 1.0, repeatable: bool = False, identity: str = "quest") -> int:
    level=clamp(int(level),1,MAX_LEVEL)
    workload=clamp(float(workload),1.0,8.0)
    # Workload matters, but cannot multiply rewards eight-fold.
    work_mult=1.0 + 0.22*(workload-1.0)
    repeat_mult=0.72 if repeatable else 1.0
    identity_mult=stable_jitter(f"quest-currency:{identity}",0.045)
    coins=int(round(_economy_anchor_value(level)*work_mult*repeat_mult*identity_mult))
    # Every ordinary quest pays at least one gold plus a silver remainder.
    coins=max(1_001, coins)
    if coins < 1_000_000_000 and coins % 1000 == 0:
        coins += 137
    return min(SAFE_INT, coins)

def tool_price_for_item(item: dict, identity: str = "tool") -> int:
    # Basic profession tools are starter equipment. Their price must not depend on
    # arbitrary item ordering / generator_level. Future gated tools may opt into
    # authored numeric gates; Generator reads those gates but never creates them.
    gates=[]
    for key in ("required_tool_level","min_tool_level","min_profession_level","required_profession_level","required_mastery"):
        try:
            value=int(item.get(key,0) or 0)
        except Exception:
            value=0
        if value>0: gates.append(value)
    stage=clamp(max(gates) if gates else 1,1,MAX_LEVEL)
    base=_economy_anchor_value(stage)
    identity_mult=0.92 + 0.16*stable_unit(f"tool-price:{identity}")
    return min(SAFE_INT,max(1_001,int(round(base*1.20*identity_mult))))


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
    base = 3.0 * ((1.0 + level / 10.0) ** 1.95)
    return min(SAFE_INT, max(1, int(round(base * max(0.5, rarity_mult)))))


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
            except Exception:
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
    mobs = ns.get("MOB_TEMPLATES", {})
    for mid, t in mobs.items():
        lvl = levels[mid]
        rank = mob_rank(t)  # derived from authored flags; never stored back as identity.
        _write_record_numeric("MOB_TEMPLATES", t, "generator_level", lvl)
        _write_record_numeric("MOB_TEMPLATES", t, "v019_stage", lvl)
        hp = mob_hp(lvl, rank)
        _write_record_numeric("MOB_TEMPLATES", t, "max_hp", hp)
        _write_record_numeric("MOB_TEMPLATES", t, "base_max_hp", hp)
        _write_record_numeric("MOB_TEMPLATES", t, "damage", mob_damage(lvl, rank))
        reward_mult = RANK_REWARD.get(rank, 1.0)
        _write_record_numeric("MOB_TEMPLATES", t, "character_xp_reward", axis_gain("character", lvl, reward_mult))
        _write_record_numeric("MOB_TEMPLATES", t, "class_xp_reward", axis_gain("class", lvl, reward_mult))
        _write_record_numeric("MOB_TEMPLATES", t, "soul_reward", axis_gain("soul", lvl, reward_mult))
        _write_record_numeric("MOB_TEMPLATES", t, "stat_reward", axis_gain("stat", lvl, reward_mult))
        _write_record_numeric("MOB_TEMPLATES", t, "silver", currency_for_stage(lvl, rank))
        _write_record_numeric("MOB_TEMPLATES", t, "gold", 0)
        _write_record_numeric("MOB_TEMPLATES", t, "mithril", 0)
        drops = t.get("drops")
        if isinstance(drops, dict) and drops:
            base_chance = {"normal": .055, "elite": .09, "rare": .14, "mini": .22, "boss": .34, "world_boss": .48}.get(rank, .055)
            count = max(1, len(drops))
            for item_id in list(drops):
                chance = base_chance * stable_jitter(f"{mid}:{item_id}", .22) / (count ** .20)
                _write_nested_numeric("MOB_TEMPLATES", t, "drops", item_id, round(clamp(chance, .005, .85), 5))




def _initial_item_level(item_id: str, item: dict) -> int | None:
    # Only structural world semantics are accepted here. Legacy prices, defense,
    # required mastery and old profession levels are deliberately ignored.
    for key in ("procedural_region_stage", "boss_chest_floor", "boss_relic_floor", "astral_relic_floor"):
        value = item.get(key)
        if value:
            try:
                return clamp(int(value), 1, MAX_LEVEL)
            except Exception:
                pass
    text = f"{item_id} {item.get('desc','')}".lower()
    floor_match = re.search(r"(?:floor|pietro|piętro)[ _:+-]*(\d{1,4})", text)
    if floor_match:
        return clamp(int(floor_match.group(1)), 1, MAX_LEVEL)
    return None


def _ordinal_hints(items: dict) -> dict[str, int]:
    """Turn content tiers into generated 1-400 stages without trusting their values.

    Tier numbers are treated only as ordering labels. Their old numeric magnitude is
    never used as a level or power value.
    """
    fields = (
        "class_equipment_tier", "crypt_set_tier", "corpse_material_tier",
        "legendary_loot_tier", "blacksmith_tier", "gem_level",
        "astral_set_tier", "v020_artifact_tier", "jewelcraft_level",
    )
    hints = {}
    for field in fields:
        vals = []
        for item in items.values():
            value = item.get(field)
            if value is not None:
                vals.append(value)
        unique = sorted(set(vals), key=lambda x: (float(x) if str(x).replace('.', '', 1).isdigit() else str(x)))
        if not unique:
            continue
        positions = {v: (1 if len(unique) == 1 else 1 + int(round(i * (MAX_LEVEL - 1) / (len(unique) - 1)))) for i, v in enumerate(unique)}
        for iid, item in items.items():
            if item.get(field) in positions:
                generated = positions[item[field]]
                hints[iid] = min(hints.get(iid, MAX_LEVEL), generated)
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
            try: pairs.append((iid, fish_unlock(iid)))
            except Exception: pass
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
                    except Exception:
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
    """Generate only whitelisted numeric item balance; authored gates/types/stat identity stay intact."""
    items = ns.get("ITEMS", {})
    resource_ids = set()
    for key in ("FISH_RESOURCE_IDS", "ORE_RESOURCE_IDS", "WOOD_RESOURCE_IDS", "HERB_RESOURCE_IDS"):
        resource_ids.update(ns.get(key, set()) or set())
    for iid, item in items.items():
        lvl = levels[iid]
        _write_record_numeric("ITEMS", item, "generator_level", lvl)
        rarity_mult = _rarity_multiplier(item)
        typ = str(item.get("type", "")).lower()
        if iid in resource_ids or item.get("resource_category") or item.get("base_resource_id"):
            sale = resource_sale_for_stage(lvl, rarity_mult)
            _write_record_numeric("ITEMS", item, "sell_silver", sale)
            _write_record_numeric("ITEMS", item, "sell_gold", 0)
            _write_record_numeric("ITEMS", item, "sell_mithril", 0)
            _write_record_numeric("ITEMS", item, "price", max(sale * 3, 1))
        elif typ == "tool" or item.get("tool_type"):
            _write_record_numeric("ITEMS", item, "price", tool_price_for_item(item, str(item.get("tool_type") or iid)))
        else:
            _write_record_numeric("ITEMS", item, "price", item_price_for_stage(lvl, rarity_mult))
        if typ == "armor" or item.get("slot"):
            slot = str(item.get("slot", "body"))
            weight = SLOT_DEFENSE_WEIGHT.get(slot, .75)
            _write_record_numeric("ITEMS", item, "defense", max(1, int(round((1.0 + 0.050 * lvl + 0.00045 * (lvl ** 2)) * weight * rarity_mult))))
            if item.get("affix"):
                _write_record_numeric("ITEMS", item, "affix_amount", max(1, int(round((1.0 + 0.035 * lvl + 0.00022 * (lvl ** 2)) * math.sqrt(rarity_mult)))))
        if isinstance(item.get("stats"), dict):
            for stat in list(item["stats"]):
                value = max(1, int(round((1.0 + 0.032 * lvl + 0.00020 * (lvl ** 2)) * math.sqrt(rarity_mult) * stable_jitter(f"{iid}:stat:{stat}", .12))))
                _write_nested_numeric("ITEMS", item, "stats", stat, value)
        if isinstance(item.get("properties"), dict):
            for prop in list(item["properties"]):
                value = round(clamp((1.0 + 0.025 * lvl + 0.00012 * (lvl ** 2)) * math.sqrt(rarity_mult) * stable_jitter(f"{iid}:prop:{prop}", .10), .5, 36.0), 3)
                _write_nested_numeric("ITEMS", item, "properties", prop, value)
        if isinstance(item.get("rune_stats"), dict):
            for stat in list(item["rune_stats"]):
                _write_nested_numeric("ITEMS", item, "rune_stats", stat, max(1, int(round(1.0 + 0.025 * lvl + 0.00016 * (lvl ** 2)))))
        if isinstance(item.get("rune_properties"), dict):
            for prop in list(item["rune_properties"]):
                _write_nested_numeric("ITEMS", item, "rune_properties", prop, round(clamp(.8 + 0.018 * lvl + 0.00009 * (lvl ** 2), .8, 18.0), 3))
        if "heal" in item:
            _write_record_numeric("ITEMS", item, "heal", max(5, int(round(18 + lvl * 2.2))))
        if "mana" in item:
            _write_record_numeric("ITEMS", item, "mana", max(5, int(round(15 + lvl * 2.0))))
        if "soul_xp" in item:
            _write_record_numeric("ITEMS", item, "soul_xp", axis_gain("soul", lvl, 2.0))




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
                except Exception:
                    pass
            lvl = clamp(int(lvl), 1, MAX_LEVEL)
            xp = axis_gain("profession", lvl, 1.35)
            _write_record_numeric(table_name, recipe, "generator_level", lvl)
            _write_record_numeric(table_name, recipe, "xp", xp)
            _write_record_numeric(table_name, recipe, "profession_xp", xp)
            _write_record_numeric(table_name, recipe, "tool_xp", axis_gain("tool", lvl, 1.20))
    return total




def _giver_stage(ns: dict, quest: dict) -> int:
    giver = str(quest.get("giver") or "")
    rooms = ns.get("ROOMS", {}) or {}
    stages = []
    for npc in (ns.get("NPCS", {}) or {}).values():
        if str(npc.get("name") or "") != giver:
            continue
        room = rooms.get(str(npc.get("room") or ""), {})
        if isinstance(room, dict):
            try: stages.append(int(room.get("generator_level", 1) or 1))
            except Exception: pass
    return clamp(min(stages) if stages else 1, 1, MAX_LEVEL)


def _quest_alias_levels(ns: dict, alias: str, mob_levels: dict[str, int]) -> list[int]:
    alias = str(alias or "")
    if not alias:
        return []
    values = []
    for mid, mob in (ns.get("MOB_TEMPLATES", {}) or {}).items():
        tags = set(map(str, mob.get("quest_targets") or ()))
        direct = mob.get("quest_target")
        if direct is not None:
            tags.add(str(direct))
        if alias in tags:
            values.append(int(mob_levels.get(mid, mob.get("generator_level", 1) or 1)))
    return values


def _collect_category_stage(ns: dict, category: str, item_levels: dict[str, int]) -> int | None:
    category = str(category or "").lower()
    set_name = {
        "fish": "FISH_RESOURCE_IDS", "fish_river": "FISH_RESOURCE_IDS",
        "ore": "ORE_RESOURCE_IDS", "wood": "WOOD_RESOURCE_IDS", "herb": "HERB_RESOURCE_IDS",
    }.get(category)
    if not set_name:
        return None
    values = [int(item_levels[iid]) for iid in (ns.get(set_name, set()) or set()) if iid in item_levels]
    return min(values) if values else None


def _quest_stage(ns: dict, qid: str, quest: dict, mob_levels: dict[str, int], item_levels: dict[str, int]) -> int:
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
        category_stage = _collect_category_stage(ns, target, item_levels)
        if category_stage is not None:
            return clamp(category_stage, 1, MAX_LEVEL)

    values = [_giver_stage(ns, quest)]
    if target in mob_levels:
        values.append(mob_levels[target])
    else:
        alias_levels = _quest_alias_levels(ns, target, mob_levels)
        if alias_levels:
            # A category/alias quest becomes available when its first valid source
            # is reachable; later variants stay valid automatically.
            values.append(min(alias_levels))
    if target in item_levels:
        values.append(item_levels[target])
    if kind in ("collect_category", "collect_distinct_category"):
        category_stage = _collect_category_stage(ns, target, item_levels)
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
        except Exception:
            pass
    return clamp(max(values or [1]), 1, MAX_LEVEL)


def _generate_quests(ns: dict, mob_levels: dict[str, int], item_levels: dict[str, int]) -> None:
    """Generate whitelisted numeric quest rewards while preserving explicitly authored currency rewards."""
    quests = ns.get("QUESTS", {})
    levels = {qid: _quest_stage(ns, qid, q, mob_levels, item_levels) for qid, q in quests.items()}
    for _ in range(max(1, len(quests))):
        changed = False
        for qid, q in quests.items():
            prev = q.get("requires_quest")
            if prev in levels and levels[qid] < levels[prev]:
                levels[qid] = levels[prev]; changed = True
        if not changed:
            break
    for qid, q in quests.items():
        lvl = clamp(int(levels.get(qid, 1)), 1, MAX_LEVEL)
        needed = max(1, int(q.get("needed", 1) or 1))
        workload = clamp(math.sqrt(needed), 1.0, 8.0)
        repeat_mult = .72 if q.get("repeatable") else 1.0
        _write_record_numeric("QUESTS", q, "generator_level", lvl)
        _write_record_numeric("QUESTS", q, "character_xp_reward", axis_gain("character", lvl, workload * repeat_mult))
        _write_record_numeric("QUESTS", q, "reward_soul_xp", axis_gain("soul", lvl, workload * repeat_mult))
        _write_record_numeric("QUESTS", q, "reward_stat_progress", axis_gain("stat", lvl, workload * repeat_mult))
        if "reward_profession_xp" in q or q.get("reward_profession") or q.get("specialist_tool_type"):
            _write_record_numeric("QUESTS", q, "reward_profession_xp", axis_gain("profession", lvl, max(1.0, workload * .75) * repeat_mult))
        if "reward_tool_xp" in q or q.get("reward_tool_type") or q.get("specialist_tool_type"):
            _write_record_numeric("QUESTS", q, "reward_tool_xp", axis_gain("tool", lvl, max(1.0, workload * .70) * repeat_mult))

        # v0.30.24: hybrydowy system waluty questów.
        # Ważne, ręcznie zaprojektowane questy mogą mieć chronioną kwotę.
        # Wszystkie pozostałe dalej używają automatycznego Generator Core.
        manual_coins = q.get("manual_currency_reward_coins")
        if manual_coins is not None:
            coins = clamp(int(manual_coins), 0, SAFE_INT)
        else:
            coins = quest_currency_for_stage(lvl, workload, bool(q.get("repeatable")), str(qid))
        _write_record_numeric("QUESTS", q, "reward_silver", min(SAFE_INT, coins))
        _write_record_numeric("QUESTS", q, "reward_gold", 0)
        _write_record_numeric("QUESTS", q, "reward_mithril", 0)


def _skill_kind_fields(skill: dict, unlock: int, sid: str) -> None:
    kind = str(skill.get("kind") or "damage")
    scale = 1.0 + unlock / 400.0
    _write_record_numeric("CLASS_SKILLS", skill, "cooldown", clamp(int(round((3.0 + 5.0 * stable_unit(sid + ':cd')) * (1.0 + unlock / 900.0))), 2, 12))
    magical = str(skill.get("scale", "")).lower() in ("intelligence", "willpower", "magic") or kind in ("heal", "group_heal", "drain")
    _write_record_numeric("CLASS_SKILLS", skill, "mana", 0 if not magical else max(1, int(round(4 + unlock * .055 + 8 * stable_unit(sid + ':mana')))))
    if kind in ("damage", "aoe", "aoe_damage", "drain", "execute"):
        _write_record_numeric("CLASS_SKILLS", skill, "mult", round((1.05 + .55 * scale) * stable_jitter(sid + ':mult', .09), 4))
    if kind == "boost":
        _write_record_numeric("CLASS_SKILLS", skill, "boost", round(clamp(1.12 + unlock / 1300.0 + stable_unit(sid) * .10, 1.12, 1.55), 4))
        _write_record_numeric("CLASS_SKILLS", skill, "duration", clamp(int(round(6 + unlock / 45.0)), 6, 16))
    if kind == "guard":
        _write_record_numeric("CLASS_SKILLS", skill, "guard", max(2, int(round(3 + unlock / 16.0))))
    if kind in ("heal", "group_heal"):
        base = .16 + unlock / 1800.0
        if kind == "group_heal":
            base *= .78
        _write_record_numeric("CLASS_SKILLS", skill, "heal_pct", round(clamp(base, .12, .42), 4))
    if kind == "drain":
        _write_record_numeric("CLASS_SKILLS", skill, "drain_pct", round(clamp(.18 + unlock / 2400.0, .18, .36), 4))
    if kind == "execute":
        _write_record_numeric("CLASS_SKILLS", skill, "execute_mult", round(1.35 + 0.45 * (unlock / MAX_LEVEL) * stable_jitter(sid + ':execute', .08), 4))
    if "self_damage" in skill:
        _write_record_numeric("CLASS_SKILLS", skill, "self_damage", max(1, int(round(2 + unlock / 80.0))))
    if "self_damage_pct" in skill:
        _write_record_numeric("CLASS_SKILLS", skill, "self_damage_pct", round(clamp(.025 + unlock / 8000.0, .025, .075), 4))



def _generate_skills(ns: dict) -> int:
    """Balance skill numbers while preserving authored ID/name/unlock/kind/scale exactly."""
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
            _write_record_numeric("CLASS_SKILLS", skill, "generator_level", balance_level)
            _skill_kind_fields(skill, balance_level, str(skill.get("id") or f"{class_name}:{idx}"))
    return count





CLASS_PASSIVE_KIND = {
    "Wojownik": "physical_damage", "Berserker": "physical_damage", "Łotrzyk": "dodge",
    "Łowca": "physical_damage", "Mnich": "healing", "Strażnik": "damage_reduction",
    "Mag": "magic_damage", "Nekromanta": "drain_healing", "Kapłan": "healing",
    "Czarownik": "magic_damage", "Druid": "healing", "Psionik": "magic_defense",
    "Mec": "damage_reduction", "Inżynier": "physical_damage",
}
RACE_PASSIVE_KIND = {
    "Człowiek": "stat_xp", "Ogr": "physical_damage", "Elf": "dodge",
    "Krasnolud": "damage_reduction", "Ork": "max_hp", "Niziołek": "profession_bonus",
    "Mroczny Elf": "magic_damage", "Gnom": "max_mana", "Smoczy": "all_damage",
    "Troll": "physical_reduction", "Diablę": "soul_xp", "Aasimar": "magic_defense",
    "Driada": "healing", "Cyborg": "damage_reduction",
}

def _percent_for_identity(identity: str, kind: str, low: float, high: float) -> float:
    return low + (high-low) * stable_unit(f"{identity}:{kind}:passive")

def class_passive_profile(class_name: str) -> dict:
    kind=CLASS_PASSIVE_KIND.get(class_name, "none")
    if kind == "dodge":
        value=round(_percent_for_identity(class_name,kind,.035,.055),4)
    elif kind == "damage_reduction":
        value=round(_percent_for_identity(class_name,kind,.08,.12),4)
    elif kind in ("physical_damage","magic_damage","healing","magic_defense"):
        value=round(_percent_for_identity(class_name,kind,.08,.13),4)
    elif kind == "drain_healing":
        value=round(_percent_for_identity(class_name,kind,.11,.17),4)
    else:
        value=0.0
    return {"kind":kind,"value":value}

def race_passive_profile(race_name: str) -> dict:
    kind=RACE_PASSIVE_KIND.get(race_name,"none")
    ranges={
        "stat_xp":(.08,.12),"physical_damage":(.09,.13),"dodge":(.035,.055),
        "damage_reduction":(.08,.12),"max_hp":(.08,.13),"profession_bonus":(.02,.04),
        "magic_damage":(.08,.13),"max_mana":(.10,.16),"all_damage":(.06,.10),
        "physical_reduction":(.09,.14),"soul_xp":(.08,.13),"magic_defense":(.09,.14),
        "healing":(.11,.17),
    }
    low,high=ranges.get(kind,(0.0,0.0))
    return {"kind":kind,"value":round(_percent_for_identity(race_name,kind,low,high),4) if high else 0.0}


def passive_text_pl(kind: str, value: float) -> str:
    pct=int(round(value*100))
    return {
        "physical_damage": f"+{pct} procent obrażeń fizycznych",
        "magic_damage": f"+{pct} procent obrażeń magicznych",
        "all_damage": f"+{pct} procent wszystkich obrażeń",
        "healing": f"+{pct} procent mocy leczenia",
        "drain_healing": f"+{pct} procent leczenia z wysysania życia",
        "magic_defense": f"+{pct} procent obrony magicznej",
        "damage_reduction": f"{pct} procent redukcji wszystkich obrażeń",
        "physical_reduction": f"{pct} procent redukcji obrażeń fizycznych",
        "dodge": f"+{pct} punktów procentowych uniku",
        "stat_xp": f"+{pct} procent EXP statystyk",
        "max_hp": f"+{pct} procent maksymalnego HP",
        "profession_bonus": f"+{pct} punktów procentowych szansy na bonus profesji",
        "max_mana": f"+{pct} procent maksymalnej Many",
        "soul_xp": f"+{pct} procent Soul XP",
    }.get(kind,"brak")

def class_passive_text_pl(class_name: str) -> str:
    p=class_passive_profile(class_name); return passive_text_pl(p["kind"],p["value"])

def race_passive_text_pl(race_name: str) -> str:
    p=race_passive_profile(race_name); return passive_text_pl(p["kind"],p["value"])

def _generate_soul(ns: dict) -> None:
    """Balance existing Soul bonus values only; never rewrite tiers, thresholds, names or trial gates."""
    try:
        max_tier = max(1, int(ns.get("SOUL_MAX_TIER", 40) or 40))
    except Exception:
        max_tier = 40
    if "SOUL_TIER_POWER_BONUSES" in ns:
        _write_top_sequence(ns, "SOUL_TIER_POWER_BONUSES", (int(round((tier - 1) * 2.2)) for tier in range(1, max_tier + 1)))
    if "SOUL_TIER_CLASS_BONUS_PERCENT" in ns:
        _write_top_sequence(ns, "SOUL_TIER_CLASS_BONUS_PERCENT", (int(round(4 + (tier - 1) * .65)) for tier in range(1, max_tier + 1)))
    if "SOUL_TIER_DODGE_BONUS" in ns:
        _write_top_sequence(ns, "SOUL_TIER_DODGE_BONUS", (round(min(.05, .005 + (tier - 1) * .0012), 4) for tier in range(1, max_tier + 1)))
    if "SOUL_TIER_GUARDIAN_REDUCTION" in ns:
        _write_top_sequence(ns, "SOUL_TIER_GUARDIAN_REDUCTION", (int(round(2 + (tier - 1) * .45)) for tier in range(1, max_tier + 1)))
    milestones = tuple(ns.get("SOUL_MILESTONE_TIERS", ()) or ())
    spec = ns.get("SOUL_MILESTONE_SPECIALIZATION_BONUS")
    if isinstance(spec, dict):
        for tier in list(spec):
            if tier in milestones:
                _write_top_map_numeric(ns, "SOUL_MILESTONE_SPECIALIZATION_BONUS", tier, int(round(int(tier) * .45)))
    dodge = ns.get("SOUL_MILESTONE_DODGE_BONUS")
    if isinstance(dodge, dict):
        for tier in list(dodge):
            if tier in milestones:
                _write_top_map_numeric(ns, "SOUL_MILESTONE_DODGE_BONUS", tier, round(min(.05, int(tier) * .0012), 4))
    guard = ns.get("SOUL_MILESTONE_GUARDIAN_REDUCTION")
    if isinstance(guard, dict):
        for tier in list(guard):
            if tier in milestones:
                _write_top_map_numeric(ns, "SOUL_MILESTONE_GUARDIAN_REDUCTION", tier, int(round(int(tier) * .30)))




def _generate_class_set_bonuses(ns: dict) -> None:
    """Rebalance values inside the authored set-bonus structure; never change owned stats/effects."""
    table = ns.get("CLASS_SET_BONUSES")
    if not isinstance(table, dict):
        return
    for cname, entry in table.items():
        if not isinstance(entry, dict):
            continue
        stats = entry.get("stats")
        if isinstance(stats, dict):
            for stat in list(stats):
                _write_class_set_numeric(entry, "stats", 3 + int(stable_unit(f"{cname}:set:stat:{stat}") * 4), leaf=stat)
        if "damage" in entry:
            _write_class_set_numeric(entry, "damage", round(1.06 + .10 * stable_unit(f"{cname}:set:damage"), 4))
        if "defense" in entry:
            _write_class_set_numeric(entry, "defense", round(1.08 + .18 * stable_unit(f"{cname}:set:defense"), 4))
        if "vitality" in entry:
            _write_class_set_numeric(entry, "vitality", round(1.10 + .22 * stable_unit(f"{cname}:set:vitality"), 4))




def _generate_class_race_numeric(ns: dict) -> None:
    """Only the numeric Soul-weapon base may be balanced; class/race identity stays authored."""
    classes = list(ns.get("CLASSES", []))
    new_classes = []
    for row in classes:
        if len(row) >= 4:
            name, ctype, weapon, _old_base, *rest = row
            base = 7 + (1 if stable_unit(str(name) + ':weapon') > .72 else 0)
            new_classes.append((name, ctype, weapon, base, *rest))
        else:
            new_classes.append(row)
    _write_classes_weapon_bases(ns, new_classes)

    # RACES, CLASS_STARTING_STAT_BONUSES and all description text are authored and untouched.



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
    "SOUL_TIER_POWER_BONUSES",
    "SOUL_TIER_CLASS_BONUS_PERCENT",
    "SOUL_TIER_DODGE_BONUS",
    "SOUL_TIER_GUARDIAN_REDUCTION",
    "SOUL_MILESTONE_SPECIALIZATION_BONUS",
    "SOUL_MILESTONE_DODGE_BONUS",
    "SOUL_MILESTONE_GUARDIAN_REDUCTION",
    "CLASS_SET_BONUSES",
    "CLASSES",
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
    global _GENERATOR_WHITELIST_WRITE_COUNT
    if field == "stats":
        stats = entry.get("stats")
        if not isinstance(stats, dict) or leaf not in stats:
            raise RuntimeError(f"Generator whitelist denied class-set stat key: {leaf}")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise RuntimeError(f"Generator whitelist denied class-set stat value: {leaf}")
        stats[leaf] = value
    elif field in ("damage", "defense", "vitality") and field in entry:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise RuntimeError(f"Generator whitelist denied class-set value: {field}")
        entry[field] = value
    else:
        raise RuntimeError(f"Generator whitelist denied class-set write: {field}")
    _GENERATOR_WHITELIST_WRITE_COUNT += 1


def _write_classes_weapon_bases(ns: dict, new_rows) -> None:
    global _GENERATOR_WHITELIST_WRITE_COUNT
    old_rows = list(ns.get("CLASSES", ()) or ())
    new_rows = list(new_rows)
    if len(old_rows) != len(new_rows):
        raise RuntimeError("Generator whitelist denied CLASSES shape change")
    for old, new in zip(old_rows, new_rows):
        if len(old) != len(new):
            raise RuntimeError("Generator whitelist denied CLASSES row shape change")
        for idx, (a, b) in enumerate(zip(old, new)):
            if idx == 3:
                if not isinstance(b, (int, float)) or isinstance(b, bool):
                    raise RuntimeError("Generator whitelist denied non-numeric Soul weapon base")
            elif a != b:
                raise RuntimeError(f"Generator whitelist denied CLASSES semantic write at index {idx}")
    ns["CLASSES"] = new_rows
    _GENERATOR_WHITELIST_WRITE_COUNT += len(new_rows)


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
    protected.append(("CLASSES", tuple(tuple(row[:3]) for row in ns.get("CLASSES", ()))))
    protected.append(("RACES", _freeze_semantic(ns.get("RACES", ()))))
    protected.append(("CLASS_DESCRIPTIONS", _freeze_semantic(ns.get("CLASS_DESCRIPTIONS", {}))))
    protected.append(("CLASS_STARTING_STAT_BONUSES", _freeze_semantic(ns.get("CLASS_STARTING_STAT_BONUSES", {}))))
    constants = (
        "SOUL_MAX_LEVEL", "SOUL_MAX_TIER", "SOUL_TIER_THRESHOLDS", "TIER2_LEVEL", "TIER3_LEVEL", "TIER4_LEVEL", "TIER5_LEVEL",
        "SOUL_SKILL_UNLOCK_LEVELS", "SOUL_MILESTONE_TIERS", "SOUL_MILESTONE_NAMES",
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
    set_structure = {}
    for cname, entry in (ns.get("CLASS_SET_BONUSES", {}) or {}).items():
        if isinstance(entry, dict):
            set_structure[str(cname)] = {
                "keys": tuple(sorted(map(str, entry.keys()))),
                "stat_keys": tuple(sorted(map(str, (entry.get("stats") or {}).keys()))) if isinstance(entry.get("stats"), dict) else (),
            }
    protected.append(("CLASS_SET_STRUCTURE", _freeze_semantic(set_structure)))
    return hashlib.sha256(repr(tuple(protected)).encode("utf-8")).hexdigest()

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
        if int(t.get("max_hp",0) or 0) != mob_hp(lvl, rank): errors.append(f"mob hp {mid}")
        if int(t.get("damage",0) or 0) != mob_damage(lvl, rank): errors.append(f"mob damage {mid}")
        if int(t.get("character_xp_reward",0) or 0) != axis_gain("character", lvl, RANK_REWARD.get(rank,1.0)): errors.append(f"mob charxp {mid}")
        if int(t.get("class_xp_reward",0) or 0) != axis_gain("class", lvl, RANK_REWARD.get(rank,1.0)): errors.append(f"mob classxp {mid}")
        if int(t.get("soul_reward",0) or 0) != axis_gain("soul", lvl, RANK_REWARD.get(rank,1.0)): errors.append(f"mob soulxp {mid}")
        if int(t.get("silver",0) or 0) != currency_for_stage(lvl, rank): errors.append(f"mob currency {mid}")
    for iid, item in items.items():
        lvl = int(item.get("generator_level",0) or 0)
        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"item level {iid}")
        if int(item.get("price",0) or 0) <= 0: errors.append(f"item price {iid}")
    for qid, q in quests.items():
        lvl = int(q.get("generator_level",0) or 0)
        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"quest level {qid}")
        if int(q.get("character_xp_reward",0) or 0) <= 0: errors.append(f"quest charxp {qid}")
        reward = int(q.get("reward_silver",0) or 0)
        manual = q.get("manual_currency_reward_coins")
        if manual is not None:
            if reward != clamp(int(manual), 0, SAFE_INT):
                errors.append(f"quest manual currency changed {qid}: {reward}!={manual}")
        elif reward < 1001:
            errors.append(f"quest currency {qid}")
        if int(q.get("reward_gold",0) or 0) != 0 or int(q.get("reward_mithril",0) or 0) != 0:
            errors.append(f"quest split currency {qid}")
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
                if per_unlock.get(level, 0) != 3:
                    errors.append(f"skill grid {cname}:{level}={per_unlock.get(level,0)} expected=3")
    for table_name in ("CRAFT_RECIPES","COOK_RECIPES","ALCHEMY_RECIPES","JEWELCRAFT_RECIPES"):
        for rid, recipe in (ns.get(table_name, {}) or {}).items():
            lvl = int(recipe.get("generator_level", 0) or 0)
            if not 1 <= lvl <= MAX_LEVEL: errors.append(f"recipe level {rid}")
            if int(recipe.get("profession_xp",0) or 0) <= 0: errors.append(f"recipe profession xp {rid}")
            if int(recipe.get("tool_xp",0) or 0) <= 0: errors.append(f"recipe tool xp {rid}")
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
    else:
        semantic_before = None
        whitelist_before = None

    _generate_soul(ns)
    _generate_class_race_numeric(ns)
    _generate_class_set_bonuses(ns)
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
        audit["semantic_fingerprint_before"] = semantic_before
        audit["semantic_fingerprint_after"] = semantic_after
        audit["semantic_preserved"] = semantic_ok
        audit["whitelist_enforced"] = True
        audit["whitelist_passed"] = bool(whitelist_audit.get("passed"))
        audit["whitelist_audit"] = whitelist_audit
        if not semantic_ok:
            audit["errors"].append("Generator Core changed protected authored semantics")
        if not whitelist_audit.get("passed"):
            audit["errors"].extend(whitelist_audit.get("errors", []))
        audit["error_count"] = len(audit["errors"])
    else:
        audit = {
            "errors": [], "error_count": 0, "runtime_fast_path": True,
            "semantic_preserved": None, "whitelist_enforced": False,
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

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soulbound v0.30.29 Deploy Startup Hotfix Edition
Wieloosobowy tekstowy MUD TCP/Telnet dla MUSHclienta/Mudleta.

Najważniejsze zasady projektu:
- postać ma generowany Level 1-400 i XP postaci,
- każda z sześciu statystyk ma własny automatyczny EXP i własny próg,
- liczbowy balans gry jest wyliczany przez Generator Core; nazwy, progi, wymagania i semantyka są ręcznie projektowane,
- Broń Duszy ma osobny Soul Level 1-400,
- Soul Tier 1-40 odblokowuje się osobno,
- wszystkie trwałe dane gracza są zapisywane w SQLite.
"""

import asyncio
import json
import hashlib
import hmac
import math
import os
import random
import re
import secrets
import sqlite3
import sys
import time
import unicodedata
from collections import deque
from dataclasses import dataclass
from typing import Optional
import types

def _load_embedded_runtime_module(name, source):
    module = types.ModuleType(name)
    module.__file__ = f"<embedded:{name}>"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module

_EMBEDDED_GENERATOR_CORE_SOURCE = '"""Soulbound v0.30.24 Generator Core — Numeric Whitelist + Hybrid Quest Rewards.\n\nNumeric-only balance layer. Authored identity, names, IDs, unlock thresholds, requirements,\nquest/recipe structure, class equipment identity and world semantics are immutable here.\nGenerator Core may only derive numeric balance values such as HP, damage, XP, prices,\nautomatic reward amounts, cooldowns, mana costs and numeric effect strength. Quests explicitly\nmarked with manual_currency_reward_coins keep that authored currency reward unchanged. Base player attributes\nfrom race/class profiles are intentionally NOT generated.\n"""\nfrom __future__ import annotations\n\nfrom collections import defaultdict, deque\nimport hashlib\nimport math\nimport re\nimport os\n\nGENERATOR_VERSION = "0.35.6"\nMAX_LEVEL = 400\nSAFE_INT = 9_000_000_000_000_000_000\n\nAXIS_TARGET_ACTIONS = {\n    "character": 18,\n    "class": 16,\n    "soul": 25,\n    "skill": 18,\n    "profession": 50,\n    "tool": 65,\n    "stat": 60,\n}\nAXIS_CURVES = {\n    "character": (140.0, 54.0, 1.82),\n    "class": (180.0, 70.0, 1.84),\n    "soul": (110.0, 48.0, 1.80),\n    "skill": (90.0, 31.0, 1.73),\n    "profession": (130.0, 43.0, 1.78),\n    "tool": (115.0, 37.0, 1.78),\n    "stat": (100.0, 29.0, 1.70),\n}\n\nRANK_HP = {"normal": 1.0, "elite": 1.55, "rare": 2.15, "mini": 4.2, "boss": 8.5, "world_boss": 14.0}\nRANK_DAMAGE = {"normal": 1.0, "elite": 1.12, "rare": 1.24, "mini": 1.42, "boss": 1.68, "world_boss": 1.95}\nRANK_REWARD = {"normal": 1.0, "elite": 1.8, "rare": 3.0, "mini": 5.0, "boss": 8.0, "world_boss": 13.0}\n\nSLOT_DEFENSE_WEIGHT = {\n    "head": 0.75, "body": 1.35, "hands": 0.55, "legs": 1.0, "feet": 0.55,\n    "ring": 0.35, "ring1": 0.35, "ring2": 0.35, "charm": 0.45, "charm1": 0.45, "charm2": 0.45,\n    "necklace": 0.45, "shoulders": 0.90, "belt": 0.70, "cloak": 0.50,\n    "bracers": 0.60, "relic": 0.55,\n}\n\n\ndef clamp(value, low, high):\n    return max(low, min(high, value))\n\n\ndef stable_unit(text: str) -> float:\n    raw = hashlib.sha256(str(text).encode("utf-8")).digest()\n    return int.from_bytes(raw[:8], "big") / float((1 << 64) - 1)\n\n\ndef stable_jitter(text: str, span: float = 0.08) -> float:\n    return 1.0 + (stable_unit(text) * 2.0 - 1.0) * span\n\n\ndef stage_from_index(index: int, maximum: int) -> int:\n    """Map an ordinal system level to the shared 1-400 Generator Core stage."""\n    index = max(1, int(index))\n    maximum = max(1, int(maximum))\n    if maximum <= 1:\n        return 1\n    index = min(index, maximum)\n    return 1 + int(round((index - 1) * (MAX_LEVEL - 1) / (maximum - 1)))\n\n\ndef axis_requirement(axis: str, level: int) -> int:\n    # v0.27.1: statystyki są jedyną osią bez twardego limitu. Pozostałe\n    # osie nadal należą do przestrzeni 1-400. Ta sama krzywa statów jest\n    # bezpiecznie ekstrapolowana ponad 400 aż do SAFE_INT.\n    raw_level = max(1, int(level))\n    level = raw_level if axis == "stat" else clamp(raw_level, 1, MAX_LEVEL)\n    base, growth, power = AXIS_CURVES[axis]\n    value = base + growth * (level ** power)\n    return min(SAFE_INT, max(1, int(round(value))))\n\n\ndef uncapped_stat_xp_scale(stat_level: int) -> float:\n    """Scale a stage-balanced stat XP reward to an uncapped stat level.\n\n    Level 1-400 keeps the original reward exactly. Above 400, the reward\n    grows in the same proportion as the generated requirement. This keeps\n    a stage-400 source at roughly the same actions-per-stat-point while\n    low-stage sources remain proportionally inefficient forever.\n    """\n    level = max(1, int(stat_level))\n    if level <= MAX_LEVEL:\n        return 1.0\n    anchor = float(axis_requirement("stat", MAX_LEVEL))\n    current = float(axis_requirement("stat", level))\n    return max(1.0, current / max(1.0, anchor))\n\n\ndef uncapped_stat_xp_gain(base_amount: int, stat_level: int) -> int:\n    base_amount = max(0, int(base_amount))\n    if base_amount <= 0:\n        return 0\n    return min(SAFE_INT, max(1, int(round(base_amount * uncapped_stat_xp_scale(stat_level)))))\n\n\ndef axis_gain(axis: str, level: int, intensity: float = 1.0) -> int:\n    target = AXIS_TARGET_ACTIONS[axis]\n    value = axis_requirement(axis, level) / float(target) * max(0.05, float(intensity))\n    return min(SAFE_INT, max(1, int(round(value))))\n\n\ndef character_hp_base(character_level: int, constitution: int) -> int:\n    character_level = clamp(int(character_level), 1, MAX_LEVEL)\n    constitution = max(1, int(constitution))\n    return max(1, int(round(48 + constitution * 5.2 + character_level * 3.1)))\n\n\ndef character_mana_base(character_level: int, intelligence: int, willpower: int | None = None) -> int:\n    character_level = clamp(int(character_level), 1, MAX_LEVEL)\n    intelligence = max(1, int(intelligence))\n    willpower = intelligence if willpower is None else max(1, int(willpower))\n    return max(0, int(round(22 + intelligence * 2.4 + willpower * 2.4 + character_level * 2.0)))\n\n\ndef character_attribute_power(character_level: int, stat_value: int) -> int:\n    character_level = clamp(int(character_level), 1, MAX_LEVEL)\n    stat_value = max(1, int(stat_value))\n    return max(1, int(round(stat_value + 0.30 * character_level)))\n\n\ndef speed_from_dexterity(dexterity: int) -> int:\n    dexterity = max(1, int(dexterity))\n    return max(1, int(round(8 + dexterity * 1.65)))\n\n\ndef dodge_from_dexterity(dexterity: int) -> float:\n    dexterity = max(1, int(dexterity))\n    value = 0.25 * (1.0 - math.exp(-max(0.0, dexterity - 10.0) / 78.0))\n    return round(clamp(value, 0.0, 0.25), 6)\n\n\ndef critical_chance_from_dexterity(dexterity: int) -> float:\n    dexterity = max(1, int(dexterity))\n    value = 0.035 + 0.285 * (1.0 - math.exp(-max(0.0, dexterity - 8.0) / 105.0))\n    return round(clamp(value, 0.035, 0.35), 6)\n\n\ndef critical_multiplier(character_level: int) -> float:\n    level = clamp(int(character_level), 1, MAX_LEVEL)\n    return round(1.45 + 0.20 * ((level - 1) / (MAX_LEVEL - 1)) ** 0.75, 6)\n\n\ndef magic_defense_base(character_level: int, willpower: int) -> int:\n    character_level = clamp(int(character_level), 1, MAX_LEVEL)\n    willpower = max(1, int(willpower))\n    return max(0, int(round(willpower * 0.55 + character_level * 0.10)))\n\n\ndef skill_level_power(level: int) -> float:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    # v0.33.2 Full Progression Rebalance: every Skill Level must be felt.\n    # 1=1.00x, 50~=1.54x, 100~=1.96x, 200~=2.70x, 300~=3.37x, 400=4.00x.\n    return round(1.0 + 3.0 * ((level - 1) / (MAX_LEVEL - 1)) ** 0.82, 6)\n\n\ndef skill_cooldown_factor(level: int) -> float:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    # Utility, evade and control skills improve through shorter cooldowns as well.\n    reduction = 0.50 * ((level - 1) / (MAX_LEVEL - 1)) ** 0.90\n    return round(1.0 - reduction, 6)\n\n\ndef profession_action_seconds(tool_type: str, level: int) -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    # Tool identity changes feel deterministically, not through hand-authored per-tool timers.\n    u = stable_unit(f"{tool_type}:action-time")\n    base = 14.0 + 14.0 * u\n    minimum = 3.0 + 5.0 * stable_unit(f"{tool_type}:minimum-time")\n    progress = ((level - 1) / (MAX_LEVEL - 1)) ** 0.78\n    return max(1, int(round(base - (base - minimum) * progress)))\n\n\ndef gather_quantity(tool_type: str, tool_level: int, profession_level: int, roll: float) -> int:\n    tool_level = clamp(int(tool_level), 1, MAX_LEVEL)\n    profession_level = clamp(int(profession_level), 1, MAX_LEVEL)\n    progress = ((tool_level + profession_level - 2) / (2 * (MAX_LEVEL - 1)))\n    identity = 0.85 + 0.30 * stable_unit(f"{tool_type}:yield")\n    p2 = clamp((0.035 + 0.19 * progress) * identity, 0.02, 0.28)\n    p3 = clamp((0.010 + 0.055 * progress ** 1.35) * identity, 0.005, 0.09)\n    p4 = clamp((0.002 + 0.015 * progress ** 2.0) * identity, 0.001, 0.025)\n    if roll < p4: return 4\n    if roll < p4 + p3: return 3\n    if roll < p4 + p3 + p2: return 2\n    return 1\n\n\ndef crafting_xp_roll(base_value: int, roll: float) -> int:\n    base = max(1, int(base_value))\n    variance = 0.08 + 0.08 * stable_unit(f"craft-xp:{base}")\n    factor = 1.0 + (clamp(float(roll), 0.0, 1.0) * 2.0 - 1.0) * variance\n    return max(1, int(round(base * factor)))\n\n\ndef boss_chest_currency(stage: int, chest_kind: str = "boss") -> int:\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    identity = 1.0 + 0.25 * stable_unit(f"chest:{chest_kind}")\n    return max(1, int(round(currency_for_stage(stage, "boss") * 2.25 * identity)))\n\n\ndef resource_pool(resource_ids, items: dict, level: int, context: str = "resource") -> tuple:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    candidates = []\n    for iid in resource_ids:\n        item = items.get(iid, {})\n        generated = int(item.get("generator_level", 1) or 1)\n        if generated <= level:\n            candidates.append((iid, generated))\n    if not candidates:\n        fallback = sorted(\n            ((iid, int(items.get(iid, {}).get("generator_level", 1) or 1)) for iid in resource_ids if iid in items),\n            key=lambda row: (row[1], row[0]),\n        )\n        return tuple(iid for iid, _ in fallback[:1])\n    # Keep the pool cumulative, while deterministic ecology affinity makes different\n    # locations feel distinct without per-location numeric loot tables.\n    candidates.sort(key=lambda row: (row[1], row[0]))\n    return tuple(iid for iid, _ in candidates)\n\n\ndef resource_weights(resource_ids, items: dict, level: int, context: str = "resource") -> list[float]:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    weights = []\n    for iid in resource_ids:\n        generated = int(items.get(iid, {}).get("generator_level", 1) or 1)\n        age = max(0, level - generated)\n        freshness = 0.30 + 8.0 / ((1.0 + age / 34.0) ** 1.28)\n        affinity = 0.72 + 0.56 * stable_unit(f"{context}:{iid}:affinity")\n        weights.append(max(0.01, freshness * affinity))\n    return weights\n\n\ndef jackpot_chance(level: int, context: str = "jackpot") -> float:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    progress = (level - 1) / (MAX_LEVEL - 1)\n    identity = 0.75 + 0.50 * stable_unit(context)\n    return clamp((0.000002 + 0.000018 * progress ** 2.1) * identity, 0.000001, 0.00003)\n\n\ndef mob_hp(level: int, rank: str = "normal") -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 52.0 + 9.5 * level + 0.74 * level * level\n    return max(1, int(round(base * RANK_HP.get(rank, 1.0))))\n\n\ndef mob_damage(level: int, rank: str = "normal") -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 3.0 + 0.30 * level + 0.0105 * level * level\n    return max(1, int(round(base * RANK_DAMAGE.get(rank, 1.0))))\n\n\ndef currency_for_stage(level: int, rank: str = "normal") -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 7.0 * ((1.0 + level / 9.0) ** 2.18)\n    return min(SAFE_INT, max(1, int(round(base * RANK_REWARD.get(rank, 1.0)))))\n\n\ndef item_price_for_stage(level: int, rarity_mult: float = 1.0) -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 18.0 * ((1.0 + level / 8.0) ** 2.05)\n    return min(SAFE_INT, max(1, int(round(base * max(0.25, rarity_mult)))))\n\n\nQUEST_CURRENCY_ANCHORS = (\n    (1, 1_200), (10, 1_500), (25, 2_500), (50, 5_000),\n    (100, 10_000), (150, 20_000), (200, 40_000), (250, 100_000),\n    (300, 1_000_000), (350, 50_000_000), (400, 1_000_000_000),\n)\n\ndef _economy_anchor_value(level: int, anchors=QUEST_CURRENCY_ANCHORS) -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    if level <= anchors[0][0]: return int(anchors[0][1])\n    if level >= anchors[-1][0]: return int(anchors[-1][1])\n    for (l0,v0),(l1,v1) in zip(anchors, anchors[1:]):\n        if l0 <= level <= l1:\n            t=(level-l0)/float(l1-l0)\n            # Log interpolation keeps the late-game mithril transition smooth.\n            value=math.exp(math.log(max(1.0,float(v0))) + (math.log(max(1.0,float(v1)))-math.log(max(1.0,float(v0))))*t)\n            return min(SAFE_INT,max(1,int(round(value))))\n    return int(anchors[-1][1])\n\ndef quest_currency_for_stage(level: int, workload: float = 1.0, repeatable: bool = False, identity: str = "quest") -> int:\n    level=clamp(int(level),1,MAX_LEVEL)\n    workload=clamp(float(workload),1.0,8.0)\n    # Workload matters, but cannot multiply rewards eight-fold.\n    work_mult=1.0 + 0.22*(workload-1.0)\n    repeat_mult=0.72 if repeatable else 1.0\n    identity_mult=stable_jitter(f"quest-currency:{identity}",0.045)\n    coins=int(round(_economy_anchor_value(level)*work_mult*repeat_mult*identity_mult))\n    # Every ordinary quest pays at least one gold plus a silver remainder.\n    coins=max(1_001, coins)\n    if coins < 1_000_000_000 and coins % 1000 == 0:\n        coins += 137\n    return min(SAFE_INT, coins)\n\ndef tool_price_for_item(item: dict, identity: str = "tool") -> int:\n    # Basic profession tools are starter equipment. Their price must not depend on\n    # arbitrary item ordering / generator_level. Future gated tools may opt into\n    # authored numeric gates; Generator reads those gates but never creates them.\n    gates=[]\n    for key in ("required_tool_level","min_tool_level","min_profession_level","required_profession_level","required_mastery"):\n        try:\n            value=int(item.get(key,0) or 0)\n        except Exception:\n            value=0\n        if value>0: gates.append(value)\n    stage=clamp(max(gates) if gates else 1,1,MAX_LEVEL)\n    base=_economy_anchor_value(stage)\n    identity_mult=0.92 + 0.16*stable_unit(f"tool-price:{identity}")\n    return min(SAFE_INT,max(1_001,int(round(base*1.20*identity_mult))))\n\n\ndef system_cost(stage: int, identity: str = "system", intensity: float = 1.0) -> int:\n    """Generated cost for non-item systems (guilds, services, upgrades)."""\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    identity_mult = 0.88 + 0.24 * stable_unit(f"system-cost:{identity}")\n    return min(SAFE_INT, max(1, int(round(item_price_for_stage(stage) * max(0.10, float(intensity)) * identity_mult))))\n\n\ndef system_reward(stage: int, identity: str = "system", intensity: float = 1.0) -> int:\n    """Generated currency reward for system-level objectives."""\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    identity_mult = 0.90 + 0.20 * stable_unit(f"system-reward:{identity}")\n    return min(SAFE_INT, max(1, int(round(currency_for_stage(stage) * max(0.10, float(intensity)) * identity_mult))))\n\n\ndef generated_count(stage: int, identity: str = "objective", low: int = 1, high: int = 100) -> int:\n    """Bounded deterministic objective count derived from stage and identity."""\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    low, high = max(1, int(low)), max(1, int(high))\n    if high < low:\n        low, high = high, low\n    progress = ((stage - 1) / (MAX_LEVEL - 1)) ** 0.82\n    identity_shift = (stable_unit(f"count:{identity}") - 0.5) * 0.16\n    value = low + (high - low) * clamp(progress + identity_shift, 0.0, 1.0)\n    return clamp(int(round(value)), low, high)\n\n\ndef generated_cooldown_seconds(stage: int, identity: str = "system", minimum: int = 3600, maximum: int = 21600) -> int:\n    """Generated cooldown; higher-stage systems may take longer but remain bounded."""\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    minimum, maximum = max(3600, int(minimum)), max(3600, int(maximum))\n    if maximum < minimum:\n        minimum, maximum = maximum, minimum\n    progress = (stage - 1) / (MAX_LEVEL - 1)\n    identity_shift = stable_unit(f"cooldown:{identity}")\n    seconds = minimum + (maximum - minimum) * clamp(0.65 * progress + 0.35 * identity_shift, 0.0, 1.0)\n    # Hour granularity keeps user-facing timers predictable and NVDA-friendly.\n    return max(3600, int(round(seconds / 3600.0)) * 3600)\n\n\ndef guild_bonus_percent(level: int, max_level: int = 100) -> int:\n    level = clamp(int(level), 1, max(1, int(max_level)))\n    progress = (level - 1) / max(1, int(max_level) - 1)\n    return clamp(int(round(1 + 10 * progress ** 0.82)), 1, 11)\n\n\ndef resource_sale_for_stage(level: int, rarity_mult: float = 1.0) -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 3.0 * ((1.0 + level / 10.0) ** 1.95)\n    return min(SAFE_INT, max(1, int(round(base * max(0.5, rarity_mult)))))\n\n\ndef mob_rank(template: dict) -> str:\n    if template.get("world_boss") or template.get("v016_world_boss") or template.get("v020_mythic_world_boss"):\n        return "world_boss"\n    if template.get("crypt_boss") or template.get("astral_boss") or template.get("giant_fortress_boss") or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss") or template.get("boss_mechanic") or template.get("v018_great_ruin_guardian"):\n        return "boss"\n    if template.get("mini_boss") or template.get("v0140_mini_boss"):\n        return "mini"\n    if template.get("rare_mob") or template.get("rare_variant") or template.get("rare_troll") or template.get("v016_legendary_rare"):\n        return "rare"\n    if template.get("elite_affix"):\n        return "elite"\n    return "normal"\n\n\ndef semantic_floor_level(template: dict) -> int | None:\n    direct = (\n        ("crypt_floor", 1.0, 0),\n        ("astral_floor", 1.0, 0),\n        ("giant_fortress_floor", 4.0, 0),\n        ("profession_dungeon_floor", 4.0, 0),\n        ("mythic_crypt_floor", 0.72, 115),\n        ("mythic_astral_floor", 0.66, 135),\n        ("v020_gauntlet_round", 18.0, 210),\n        ("guild_hall_level", 38.0, 20),\n        ("procedural_region_stage", 1.0, 0),\n    )\n    for key, scale, offset in direct:\n        if template.get(key) is not None:\n            try:\n                return clamp(int(round(offset + int(template[key]) * scale)), 1, MAX_LEVEL)\n            except Exception:\n                pass\n    return None\n\n\ndef _graph_room_levels(rooms: dict) -> dict[str, int]:\n    """Derive numeric balance stages without changing authored room semantics."""\n    if not rooms:\n        return {}\n    start = "square" if "square" in rooms else next(iter(rooms))\n    dist = {start: 0}\n    q = deque([start])\n    while q:\n        rid = q.popleft()\n        for target in (rooms.get(rid, {}).get("exits") or {}).values():\n            if target in rooms and target not in dist:\n                dist[target] = dist[rid] + 1\n                q.append(target)\n    room_levels = {}\n    for rid, room in rooms.items():\n        lvl = semantic_floor_level(room)\n        if lvl is None:\n            text = f"{rid} {room.get(\'zone\',\'\')} {room.get(\'name\',\'\')}".lower()\n            floor_match = re.search(r"(?:floor|level|poziom|pietro|piętro)[_ -]*(\\d{1,4})", text)\n            if floor_match and any(k in text for k in ("crypt", "krypt", "astral", "tower", "wież", "fortress", "twierdz", "dungeon", "loch")):\n                lvl = clamp(int(floor_match.group(1)), 1, MAX_LEVEL)\n            else:\n                d = dist.get(rid)\n                if d is None:\n                    lvl = 160 + int(stable_unit(rid) * 220)\n                else:\n                    lvl = 1 + int(round(1.9 * d + 0.10 * d * d))\n                if room.get("v020_mega_gate") or room.get("v020_gauntlet"):\n                    lvl = max(lvl, 220)\n        room_levels[rid] = clamp(int(lvl), 1, MAX_LEVEL)\n        # generator_level is balance metadata only. Never overwrite recommended_mastery,\n        # exits, names, zones or any authored access/recommendation field.\n        _write_record_numeric("ROOMS", room, "generator_level", room_levels[rid])\n    return room_levels\n\n\n\ndef _mob_levels(ns: dict, room_levels: dict[str, int]) -> dict[str, int]:\n    mobs = ns.get("MOB_TEMPLATES", {})\n    spawns = ns.get("MOB_SPAWNS", [])\n    by_mob = defaultdict(list)\n    for rid, mid in spawns:\n        if rid in room_levels:\n            by_mob[str(mid)].append(room_levels[rid])\n\n    cache = {}\n    visiting = set()\n    def level_for(mid: str) -> int:\n        if mid in cache:\n            return cache[mid]\n        if mid in visiting:\n            return 1 + int(stable_unit(mid) * (MAX_LEVEL - 1))\n        visiting.add(mid)\n        t = mobs.get(mid, {})\n        lvl = semantic_floor_level(t)\n        if lvl is None:\n            for base_key in ("elite_base_template", "rare_base_template", "base_template", "template_id"):\n                base = t.get(base_key)\n                if base and base != mid and base in mobs:\n                    lvl = level_for(str(base)); break\n        if lvl is None and by_mob.get(mid):\n            # A reusable template is balanced for the EARLIEST place where it can occur.\n            # Later rooms may add harder ranks/other templates, but a quest drop cannot\n            # require a mob whose stats were tuned for a later duplicate spawn.\n            lvl = min(by_mob[mid])\n        if lvl is None:\n            lvl = 1 + int(stable_unit(mid) * (MAX_LEVEL - 1))\n        cache[mid] = clamp(int(lvl), 1, MAX_LEVEL)\n        visiting.discard(mid)\n        return cache[mid]\n\n    for mid in mobs:\n        level_for(mid)\n    return cache\n\n\ndef runtime_mob_balance(template_id: str, template: dict, level: int, rank: str | None = None) -> dict:\n    """Balance whitelisted numeric fields of a runtime mob; semantic identity stays authored."""\n    level = clamp(int(level), 1, MAX_LEVEL)\n    rank = str(rank or mob_rank(template))\n    _write_record_numeric("MOB_TEMPLATES", template, "generator_level", level)\n    _write_record_numeric("MOB_TEMPLATES", template, "v019_stage", level)\n    hp = mob_hp(level, rank)\n    _write_record_numeric("MOB_TEMPLATES", template, "max_hp", hp)\n    _write_record_numeric("MOB_TEMPLATES", template, "base_max_hp", hp)\n    _write_record_numeric("MOB_TEMPLATES", template, "damage", mob_damage(level, rank))\n    reward_mult = RANK_REWARD.get(rank, 1.0)\n    _write_record_numeric("MOB_TEMPLATES", template, "character_xp_reward", axis_gain("character", level, reward_mult))\n    _write_record_numeric("MOB_TEMPLATES", template, "class_xp_reward", axis_gain("class", level, reward_mult))\n    _write_record_numeric("MOB_TEMPLATES", template, "soul_reward", axis_gain("soul", level, reward_mult))\n    _write_record_numeric("MOB_TEMPLATES", template, "stat_reward", axis_gain("stat", level, reward_mult))\n    _write_record_numeric("MOB_TEMPLATES", template, "silver", currency_for_stage(level, rank))\n    _write_record_numeric("MOB_TEMPLATES", template, "gold", 0)\n    _write_record_numeric("MOB_TEMPLATES", template, "mithril", 0)\n    drops = template.get("drops")\n    if isinstance(drops, dict) and drops:\n        base_chance = {"normal": .055, "elite": .09, "rare": .14, "mini": .22, "boss": .34, "world_boss": .48}.get(rank, .055)\n        count = max(1, len(drops))\n        for item_id in list(drops):\n            chance = base_chance * stable_jitter(f"{template_id}:{item_id}", .22) / (count ** .20)\n            _write_nested_numeric("MOB_TEMPLATES", template, "drops", item_id, round(clamp(chance, .005, .85), 5))\n    return template\n\n\n\n\ndef _generate_mobs(ns: dict, levels: dict[str, int]) -> None:\n    mobs = ns.get("MOB_TEMPLATES", {})\n    for mid, t in mobs.items():\n        lvl = levels[mid]\n        rank = mob_rank(t)  # derived from authored flags; never stored back as identity.\n        _write_record_numeric("MOB_TEMPLATES", t, "generator_level", lvl)\n        _write_record_numeric("MOB_TEMPLATES", t, "v019_stage", lvl)\n        hp = mob_hp(lvl, rank)\n        _write_record_numeric("MOB_TEMPLATES", t, "max_hp", hp)\n        _write_record_numeric("MOB_TEMPLATES", t, "base_max_hp", hp)\n        _write_record_numeric("MOB_TEMPLATES", t, "damage", mob_damage(lvl, rank))\n        reward_mult = RANK_REWARD.get(rank, 1.0)\n        _write_record_numeric("MOB_TEMPLATES", t, "character_xp_reward", axis_gain("character", lvl, reward_mult))\n        _write_record_numeric("MOB_TEMPLATES", t, "class_xp_reward", axis_gain("class", lvl, reward_mult))\n        _write_record_numeric("MOB_TEMPLATES", t, "soul_reward", axis_gain("soul", lvl, reward_mult))\n        _write_record_numeric("MOB_TEMPLATES", t, "stat_reward", axis_gain("stat", lvl, reward_mult))\n        _write_record_numeric("MOB_TEMPLATES", t, "silver", currency_for_stage(lvl, rank))\n        _write_record_numeric("MOB_TEMPLATES", t, "gold", 0)\n        _write_record_numeric("MOB_TEMPLATES", t, "mithril", 0)\n        drops = t.get("drops")\n        if isinstance(drops, dict) and drops:\n            base_chance = {"normal": .055, "elite": .09, "rare": .14, "mini": .22, "boss": .34, "world_boss": .48}.get(rank, .055)\n            count = max(1, len(drops))\n            for item_id in list(drops):\n                chance = base_chance * stable_jitter(f"{mid}:{item_id}", .22) / (count ** .20)\n                _write_nested_numeric("MOB_TEMPLATES", t, "drops", item_id, round(clamp(chance, .005, .85), 5))\n\n\n\n\ndef _initial_item_level(item_id: str, item: dict) -> int | None:\n    # Only structural world semantics are accepted here. Legacy prices, defense,\n    # required mastery and old profession levels are deliberately ignored.\n    for key in ("procedural_region_stage", "boss_chest_floor", "boss_relic_floor", "astral_relic_floor"):\n        value = item.get(key)\n        if value:\n            try:\n                return clamp(int(value), 1, MAX_LEVEL)\n            except Exception:\n                pass\n    text = f"{item_id} {item.get(\'desc\',\'\')}".lower()\n    floor_match = re.search(r"(?:floor|pietro|piętro)[ _:+-]*(\\d{1,4})", text)\n    if floor_match:\n        return clamp(int(floor_match.group(1)), 1, MAX_LEVEL)\n    return None\n\n\ndef _ordinal_hints(items: dict) -> dict[str, int]:\n    """Turn content tiers into generated 1-400 stages without trusting their values.\n\n    Tier numbers are treated only as ordering labels. Their old numeric magnitude is\n    never used as a level or power value.\n    """\n    fields = (\n        "class_equipment_tier", "crypt_set_tier", "corpse_material_tier",\n        "legendary_loot_tier", "blacksmith_tier", "gem_level",\n        "astral_set_tier", "v020_artifact_tier", "jewelcraft_level",\n    )\n    hints = {}\n    for field in fields:\n        vals = []\n        for item in items.values():\n            value = item.get(field)\n            if value is not None:\n                vals.append(value)\n        unique = sorted(set(vals), key=lambda x: (float(x) if str(x).replace(\'.\', \'\', 1).isdigit() else str(x)))\n        if not unique:\n            continue\n        positions = {v: (1 if len(unique) == 1 else 1 + int(round(i * (MAX_LEVEL - 1) / (len(unique) - 1)))) for i, v in enumerate(unique)}\n        for iid, item in items.items():\n            if item.get(field) in positions:\n                generated = positions[item[field]]\n                hints[iid] = min(hints.get(iid, MAX_LEVEL), generated)\n    return hints\n\n\ndef _normalized_order_levels(pairs) -> dict:\n    cleaned = [(str(iid), float(order)) for iid, order in pairs if iid is not None and order is not None]\n    if not cleaned:\n        return {}\n    unique = sorted({order for _iid, order in cleaned})\n    if len(unique) == 1:\n        rank_to_level = {unique[0]: 1}\n    else:\n        rank_to_level = {order: 1 + int(round(idx * (MAX_LEVEL - 1) / (len(unique) - 1))) for idx, order in enumerate(unique)}\n    return {iid: rank_to_level[order] for iid, order in cleaned}\n\n\ndef _resource_order_hints(ns: dict, items: dict) -> dict[str, int]:\n    hints = {}\n    fish_ids = set(ns.get("FISH_RESOURCE_IDS", set()) or set())\n    fish_unlock = ns.get("fish_unlock_level")\n    if callable(fish_unlock):\n        pairs = []\n        for iid in fish_ids:\n            try: pairs.append((iid, fish_unlock(iid)))\n            except Exception: pass\n        hints.update(_normalized_order_levels(pairs))\n\n    ore_levels = ns.get("ORE_ATLAS_LEVELS", {}) or {}\n    hints.update(_normalized_order_levels((iid, ore_levels.get(iid, 1)) for iid in (ns.get("ORE_RESOURCE_IDS", set()) or set())))\n\n    for ids_name, table_name in (("WOOD_RESOURCE_IDS", "WOOD_ATLAS_ROOM_MIN_LEVELS"), ("HERB_RESOURCE_IDS", "HERB_ATLAS_ROOM_MIN_LEVELS")):\n        ids = set(ns.get(ids_name, set()) or set())\n        table = ns.get(table_name, {}) or {}\n        mins = {}\n        for _room, mapping in table.items():\n            if not isinstance(mapping, dict):\n                continue\n            for iid, old_order in mapping.items():\n                if iid in ids:\n                    try:\n                        old_order = float(old_order)\n                        mins[iid] = min(mins.get(iid, old_order), old_order)\n                    except Exception:\n                        pass\n        # Resources without an old placement still join deterministically after ordered ones.\n        ordered = _normalized_order_levels(mins.items())\n        hints.update(ordered)\n        missing = sorted(ids - set(ordered))\n        for iid in missing:\n            hints[iid] = 1 + int(stable_unit(f"resource-order:{ids_name}:{iid}") * (MAX_LEVEL - 1))\n\n    # Rare resource variants inherit their base species/material stage later.\n    return hints\n\n\ndef _item_levels(ns: dict, mob_levels: dict[str, int]) -> dict[str, int]:\n    items = ns.get("ITEMS", {})\n    mobs = ns.get("MOB_TEMPLATES", {})\n    levels = {iid: _initial_item_level(iid, item) for iid, item in items.items()}\n    resource_hints = _resource_order_hints(ns, items)\n    for iid, hint in resource_hints.items():\n        levels[iid] = hint\n    ordinal = _ordinal_hints(items)\n    for iid, hint in ordinal.items():\n        if levels.get(iid) is None:\n            levels[iid] = hint\n    # Drops inherit the earliest content level that can produce them.\n    drop_sources = defaultdict(list)\n    for mid, t in mobs.items():\n        for iid in (t.get("drops") or {}):\n            if iid in items:\n                drop_sources[iid].append(mob_levels.get(mid, 1))\n        for key in ("corpse_equipment_pool", "corpse_material_pool"):\n            for iid in (t.get(key) or []):\n                if iid in items:\n                    drop_sources[iid].append(mob_levels.get(mid, 1))\n    for iid, values in drop_sources.items():\n        # Gathering resources keep their generated profession order. Mob drops of the\n        # same material are re-priced to that stage instead of collapsing the whole\n        # profession curve to the earliest creature that happens to carry it.\n        if iid in resource_hints:\n            continue\n        inherited = min(values)\n        levels[iid] = inherited if levels.get(iid) is None else min(levels[iid], inherited)\n\n    # Resource variants inherit base-resource level. Resolve repeatedly.\n    for _ in range(4):\n        changed = False\n        for iid, item in items.items():\n            base = item.get("base_resource_id") or item.get("crypt_base_item") or item.get("v020_artifact_base")\n            if base in levels and levels.get(base) is not None and levels.get(iid) is None:\n                levels[iid] = levels[base]; changed = True\n        if not changed: break\n\n    # Unlinked content is placed deterministically; it cannot inherit balance from hand-written prices/stats.\n    for iid in items:\n        if levels.get(iid) is None:\n            levels[iid] = 1 + int(stable_unit(iid) * (MAX_LEVEL - 1))\n    return {k: clamp(int(v), 1, MAX_LEVEL) for k, v in levels.items()}\n\n\ndef _rarity_multiplier(item: dict) -> float:\n    rarity = str(item.get("rarity", "")).lower()\n    return {\n        "common": 1.0, "uncommon": 1.25, "rare": 1.6, "epic": 2.1,\n        "legendary": 3.0, "mythic": 4.0, "crafted": 1.35,\n    }.get(rarity, max(1.0, float(item.get("rare_value_multiplier", 1.0) or 1.0)))\n\n\ndef _generate_items(ns: dict, levels: dict[str, int]) -> None:\n    """Generate only whitelisted numeric item balance; authored gates/types/stat identity stay intact."""\n    items = ns.get("ITEMS", {})\n    resource_ids = set()\n    for key in ("FISH_RESOURCE_IDS", "ORE_RESOURCE_IDS", "WOOD_RESOURCE_IDS", "HERB_RESOURCE_IDS"):\n        resource_ids.update(ns.get(key, set()) or set())\n    for iid, item in items.items():\n        lvl = levels[iid]\n        _write_record_numeric("ITEMS", item, "generator_level", lvl)\n        rarity_mult = _rarity_multiplier(item)\n        typ = str(item.get("type", "")).lower()\n        if iid in resource_ids or item.get("resource_category") or item.get("base_resource_id"):\n            sale = resource_sale_for_stage(lvl, rarity_mult)\n            _write_record_numeric("ITEMS", item, "sell_silver", sale)\n            _write_record_numeric("ITEMS", item, "sell_gold", 0)\n            _write_record_numeric("ITEMS", item, "sell_mithril", 0)\n            _write_record_numeric("ITEMS", item, "price", max(sale * 3, 1))\n        elif typ == "tool" or item.get("tool_type"):\n            _write_record_numeric("ITEMS", item, "price", tool_price_for_item(item, str(item.get("tool_type") or iid)))\n        else:\n            _write_record_numeric("ITEMS", item, "price", item_price_for_stage(lvl, rarity_mult))\n        if typ == "armor" or item.get("slot"):\n            slot = str(item.get("slot", "body"))\n            weight = SLOT_DEFENSE_WEIGHT.get(slot, .75)\n            _write_record_numeric("ITEMS", item, "defense", max(1, int(round((1.0 + 0.050 * lvl + 0.00045 * (lvl ** 2)) * weight * rarity_mult))))\n            if item.get("affix"):\n                _write_record_numeric("ITEMS", item, "affix_amount", max(1, int(round((1.0 + 0.035 * lvl + 0.00022 * (lvl ** 2)) * math.sqrt(rarity_mult)))))\n        if isinstance(item.get("stats"), dict):\n            for stat in list(item["stats"]):\n                value = max(1, int(round((1.0 + 0.032 * lvl + 0.00020 * (lvl ** 2)) * math.sqrt(rarity_mult) * stable_jitter(f"{iid}:stat:{stat}", .12))))\n                _write_nested_numeric("ITEMS", item, "stats", stat, value)\n        if isinstance(item.get("properties"), dict):\n            for prop in list(item["properties"]):\n                value = round(clamp((1.0 + 0.025 * lvl + 0.00012 * (lvl ** 2)) * math.sqrt(rarity_mult) * stable_jitter(f"{iid}:prop:{prop}", .10), .5, 36.0), 3)\n                _write_nested_numeric("ITEMS", item, "properties", prop, value)\n        if isinstance(item.get("rune_stats"), dict):\n            for stat in list(item["rune_stats"]):\n                _write_nested_numeric("ITEMS", item, "rune_stats", stat, max(1, int(round(1.0 + 0.025 * lvl + 0.00016 * (lvl ** 2)))))\n        if isinstance(item.get("rune_properties"), dict):\n            for prop in list(item["rune_properties"]):\n                _write_nested_numeric("ITEMS", item, "rune_properties", prop, round(clamp(.8 + 0.018 * lvl + 0.00009 * (lvl ** 2), .8, 18.0), 3))\n        if "heal" in item:\n            _write_record_numeric("ITEMS", item, "heal", max(5, int(round(18 + lvl * 2.2))))\n        if "mana" in item:\n            _write_record_numeric("ITEMS", item, "mana", max(5, int(round(15 + lvl * 2.0))))\n        if "soul_xp" in item:\n            _write_record_numeric("ITEMS", item, "soul_xp", axis_gain("soul", lvl, 2.0))\n\n\n\n\ndef _recipe_stage(recipe: dict, item_levels: dict[str, int]) -> int:\n    """Semantic hint only; final recipe levels are regenerated across 1-400."""\n    values = []\n    for iid in (recipe.get("ingredients") or {}):\n        if iid in item_levels:\n            values.append(item_levels[iid])\n    if values:\n        return clamp(max(values), 1, MAX_LEVEL)\n    output = recipe.get("output")\n    if output in item_levels:\n        return clamp(item_levels[output], 1, MAX_LEVEL)\n    rid = str(recipe.get("id") or recipe.get("name") or "recipe")\n    return 1 + int(stable_unit(rid) * (MAX_LEVEL - 1))\n\n\ndef _recipe_topological_order(table: dict, item_levels: dict[str, int]) -> list[str]:\n    """Order recipes by dependencies and generated ingredient stages, never old numeric requirements."""\n    output_to_recipe = {}\n    for rid, recipe in table.items():\n        output = recipe.get("output")\n        if output:\n            output_to_recipe[str(output)] = rid\n\n    outgoing = defaultdict(set)\n    indegree = {rid: 0 for rid in table}\n    for rid, recipe in table.items():\n        for iid in (recipe.get("ingredients") or {}):\n            producer = output_to_recipe.get(str(iid))\n            if producer and producer != rid and rid not in outgoing[producer]:\n                outgoing[producer].add(rid)\n                indegree[rid] += 1\n\n    # Content insertion order describes semantic progression without carrying any\n    # hand-authored balance number. Dependencies still take precedence, so a\n    # component recipe is always generated before recipes that consume it.\n    insertion_index = {rid: i for i, rid in enumerate(table)}\n\n    def key(rid: str):\n        return (insertion_index.get(rid, 10**9), stable_unit(f"recipe-order:{rid}"), rid)\n\n    ready = sorted((rid for rid, deg in indegree.items() if deg == 0), key=key)\n    ordered = []\n    while ready:\n        rid = ready.pop(0)\n        ordered.append(rid)\n        for nxt in sorted(outgoing.get(rid, ()), key=key):\n            indegree[nxt] -= 1\n            if indegree[nxt] == 0:\n                ready.append(nxt)\n                ready.sort(key=key)\n\n    # Cycles should not block generation. Deterministic ordering breaks them without trusting legacy levels.\n    if len(ordered) != len(table):\n        remaining = [rid for rid in table if rid not in set(ordered)]\n        ordered.extend(sorted(remaining, key=key))\n    return ordered\n\n\ndef _generate_recipes(ns: dict, item_levels: dict[str, int]) -> int:\n    """Balance recipe XP only; authored requirements, ingredients, outputs and quantities are immutable."""\n    total = 0\n    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):\n        table = ns.get(table_name, {}) or {}\n        for rid, recipe in table.items():\n            total += 1\n            lvl = _recipe_stage(recipe, item_levels)\n            for gate in (recipe.get("min_profession_level"), recipe.get("min_tool_level")):\n                try:\n                    if gate is not None:\n                        lvl = max(lvl, int(gate))\n                except Exception:\n                    pass\n            lvl = clamp(int(lvl), 1, MAX_LEVEL)\n            xp = axis_gain("profession", lvl, 1.35)\n            _write_record_numeric(table_name, recipe, "generator_level", lvl)\n            _write_record_numeric(table_name, recipe, "xp", xp)\n            _write_record_numeric(table_name, recipe, "profession_xp", xp)\n            _write_record_numeric(table_name, recipe, "tool_xp", axis_gain("tool", lvl, 1.20))\n    return total\n\n\n\n\ndef _giver_stage(ns: dict, quest: dict) -> int:\n    giver = str(quest.get("giver") or "")\n    rooms = ns.get("ROOMS", {}) or {}\n    stages = []\n    for npc in (ns.get("NPCS", {}) or {}).values():\n        if str(npc.get("name") or "") != giver:\n            continue\n        room = rooms.get(str(npc.get("room") or ""), {})\n        if isinstance(room, dict):\n            try: stages.append(int(room.get("generator_level", 1) or 1))\n            except Exception: pass\n    return clamp(min(stages) if stages else 1, 1, MAX_LEVEL)\n\n\ndef _quest_alias_levels(ns: dict, alias: str, mob_levels: dict[str, int]) -> list[int]:\n    alias = str(alias or "")\n    if not alias:\n        return []\n    values = []\n    for mid, mob in (ns.get("MOB_TEMPLATES", {}) or {}).items():\n        tags = set(map(str, mob.get("quest_targets") or ()))\n        direct = mob.get("quest_target")\n        if direct is not None:\n            tags.add(str(direct))\n        if alias in tags:\n            values.append(int(mob_levels.get(mid, mob.get("generator_level", 1) or 1)))\n    return values\n\n\ndef _collect_category_stage(ns: dict, category: str, item_levels: dict[str, int]) -> int | None:\n    category = str(category or "").lower()\n    set_name = {\n        "fish": "FISH_RESOURCE_IDS", "fish_river": "FISH_RESOURCE_IDS",\n        "ore": "ORE_RESOURCE_IDS", "wood": "WOOD_RESOURCE_IDS", "herb": "HERB_RESOURCE_IDS",\n    }.get(category)\n    if not set_name:\n        return None\n    values = [int(item_levels[iid]) for iid in (ns.get(set_name, set()) or set()) if iid in item_levels]\n    return min(values) if values else None\n\n\ndef _quest_stage(ns: dict, qid: str, quest: dict, mob_levels: dict[str, int], item_levels: dict[str, int]) -> int:\n    # A starter flag is semantic identity: starter quests must be available to a\n    # fresh character regardless of the item they happen to reward.\n    if quest.get("starter_quest"):\n        return 1\n\n    kind = str(quest.get("kind") or "")\n    target = quest.get("target")\n    # Profession onboarding must follow the first obtainable resource of that\n    # profession, never the generated physical location of its NPC. Rebuilding\n    # the city/world topology therefore cannot move a starter profession quest\n    # to mid/endgame. This is a semantic rule, not a per-quest exception.\n    if (quest.get("reward_profession") and not quest.get("requires_quest")\n            and kind in ("collect_category", "collect_distinct_category")):\n        category_stage = _collect_category_stage(ns, target, item_levels)\n        if category_stage is not None:\n            return clamp(category_stage, 1, MAX_LEVEL)\n\n    values = [_giver_stage(ns, quest)]\n    if target in mob_levels:\n        values.append(mob_levels[target])\n    else:\n        alias_levels = _quest_alias_levels(ns, target, mob_levels)\n        if alias_levels:\n            # A category/alias quest becomes available when its first valid source\n            # is reachable; later variants stay valid automatically.\n            values.append(min(alias_levels))\n    if target in item_levels:\n        values.append(item_levels[target])\n    if kind in ("collect_category", "collect_distinct_category"):\n        category_stage = _collect_category_stage(ns, target, item_levels)\n        if category_stage is not None:\n            values.append(category_stage)\n    for target_id in (quest.get("targets") or ()):\n        if target_id in mob_levels: values.append(mob_levels[target_id])\n        if target_id in item_levels: values.append(item_levels[target_id])\n    for iid in (quest.get("resource_targets") or {}):\n        if iid in item_levels: values.append(item_levels[iid])\n\n    # Delivery difficulty follows the destination, not the free quest item.\n    target_npc = quest.get("target_npc")\n    if target_npc and target_npc in (ns.get("NPCS", {}) or {}):\n        room_id = ns["NPCS"][target_npc].get("room")\n        room = (ns.get("ROOMS", {}) or {}).get(room_id, {})\n        if isinstance(room, dict):\n            values.append(int(room.get("generator_level", 1) or 1))\n\n    # Soul trial tier is structural identity; its old required-level number is ignored.\n    if quest.get("soul_trial_tier"):\n        try:\n            tier = clamp(int(quest["soul_trial_tier"]), 1, 40)\n            values.append(1 if tier == 1 else (tier - 1) * 10)\n        except Exception:\n            pass\n    return clamp(max(values or [1]), 1, MAX_LEVEL)\n\n\ndef _generate_quests(ns: dict, mob_levels: dict[str, int], item_levels: dict[str, int]) -> None:\n    """Generate whitelisted numeric quest rewards while preserving explicitly authored currency rewards."""\n    quests = ns.get("QUESTS", {})\n    levels = {qid: _quest_stage(ns, qid, q, mob_levels, item_levels) for qid, q in quests.items()}\n    for _ in range(max(1, len(quests))):\n        changed = False\n        for qid, q in quests.items():\n            prev = q.get("requires_quest")\n            if prev in levels and levels[qid] < levels[prev]:\n                levels[qid] = levels[prev]; changed = True\n        if not changed:\n            break\n    for qid, q in quests.items():\n        lvl = clamp(int(levels.get(qid, 1)), 1, MAX_LEVEL)\n        needed = max(1, int(q.get("needed", 1) or 1))\n        workload = clamp(math.sqrt(needed), 1.0, 8.0)\n        repeat_mult = .72 if q.get("repeatable") else 1.0\n        _write_record_numeric("QUESTS", q, "generator_level", lvl)\n        _write_record_numeric("QUESTS", q, "character_xp_reward", axis_gain("character", lvl, workload * repeat_mult))\n        _write_record_numeric("QUESTS", q, "reward_soul_xp", axis_gain("soul", lvl, workload * repeat_mult))\n        _write_record_numeric("QUESTS", q, "reward_stat_progress", axis_gain("stat", lvl, workload * repeat_mult))\n        if "reward_profession_xp" in q or q.get("reward_profession") or q.get("specialist_tool_type"):\n            _write_record_numeric("QUESTS", q, "reward_profession_xp", axis_gain("profession", lvl, max(1.0, workload * .75) * repeat_mult))\n        if "reward_tool_xp" in q or q.get("reward_tool_type") or q.get("specialist_tool_type"):\n            _write_record_numeric("QUESTS", q, "reward_tool_xp", axis_gain("tool", lvl, max(1.0, workload * .70) * repeat_mult))\n\n        # v0.30.24: hybrydowy system waluty questów.\n        # Ważne, ręcznie zaprojektowane questy mogą mieć chronioną kwotę.\n        # Wszystkie pozostałe dalej używają automatycznego Generator Core.\n        manual_coins = q.get("manual_currency_reward_coins")\n        if manual_coins is not None:\n            coins = clamp(int(manual_coins), 0, SAFE_INT)\n        else:\n            coins = quest_currency_for_stage(lvl, workload, bool(q.get("repeatable")), str(qid))\n        _write_record_numeric("QUESTS", q, "reward_silver", min(SAFE_INT, coins))\n        _write_record_numeric("QUESTS", q, "reward_gold", 0)\n        _write_record_numeric("QUESTS", q, "reward_mithril", 0)\n\n\ndef _skill_kind_fields(skill: dict, unlock: int, sid: str) -> None:\n    kind = str(skill.get("kind") or "damage")\n    scale = 1.0 + unlock / 400.0\n    _write_record_numeric("CLASS_SKILLS", skill, "cooldown", clamp(int(round((3.0 + 5.0 * stable_unit(sid + \':cd\')) * (1.0 + unlock / 900.0))), 2, 12))\n    magical = str(skill.get("scale", "")).lower() in ("intelligence", "willpower", "magic") or kind in ("heal", "group_heal", "drain")\n    _write_record_numeric("CLASS_SKILLS", skill, "mana", 0 if not magical else max(1, int(round(4 + unlock * .055 + 8 * stable_unit(sid + \':mana\')))))\n    if kind in ("damage", "aoe", "aoe_damage", "drain", "execute"):\n        _write_record_numeric("CLASS_SKILLS", skill, "mult", round((1.05 + .55 * scale) * stable_jitter(sid + \':mult\', .09), 4))\n    if kind == "boost":\n        _write_record_numeric("CLASS_SKILLS", skill, "boost", round(clamp(1.12 + unlock / 1300.0 + stable_unit(sid) * .10, 1.12, 1.55), 4))\n        _write_record_numeric("CLASS_SKILLS", skill, "duration", clamp(int(round(6 + unlock / 45.0)), 6, 16))\n    if kind == "guard":\n        _write_record_numeric("CLASS_SKILLS", skill, "guard", max(2, int(round(3 + unlock / 16.0))))\n    if kind in ("heal", "group_heal"):\n        base = .16 + unlock / 1800.0\n        if kind == "group_heal":\n            base *= .78\n        _write_record_numeric("CLASS_SKILLS", skill, "heal_pct", round(clamp(base, .12, .42), 4))\n    if kind == "drain":\n        _write_record_numeric("CLASS_SKILLS", skill, "drain_pct", round(clamp(.18 + unlock / 2400.0, .18, .36), 4))\n    if kind == "execute":\n        _write_record_numeric("CLASS_SKILLS", skill, "execute_mult", round(1.35 + 0.45 * (unlock / MAX_LEVEL) * stable_jitter(sid + \':execute\', .08), 4))\n    if "self_damage" in skill:\n        _write_record_numeric("CLASS_SKILLS", skill, "self_damage", max(1, int(round(2 + unlock / 80.0))))\n    if "self_damage_pct" in skill:\n        _write_record_numeric("CLASS_SKILLS", skill, "self_damage_pct", round(clamp(.025 + unlock / 8000.0, .025, .075), 4))\n\n\n\ndef _generate_skills(ns: dict) -> int:\n    """Balance skill numbers while preserving authored ID/name/unlock/kind/scale exactly."""\n    class_skills = ns.get("CLASS_SKILLS", {}) or {}\n    count = 0\n    for class_name, skills in class_skills.items():\n        for idx, skill in enumerate(skills):\n            count += 1\n            try:\n                unlock = int(skill.get("unlock", 1) or 1)\n            except Exception:\n                unlock = 1\n            balance_level = clamp(unlock, 1, MAX_LEVEL)\n            _write_record_numeric("CLASS_SKILLS", skill, "generator_level", balance_level)\n            _skill_kind_fields(skill, balance_level, str(skill.get("id") or f"{class_name}:{idx}"))\n    return count\n\n\n\n\n\nCLASS_PASSIVE_KIND = {\n    "Wojownik": "physical_damage", "Berserker": "physical_damage", "Łotrzyk": "dodge",\n    "Łowca": "physical_damage", "Mnich": "healing", "Strażnik": "damage_reduction",\n    "Mag": "magic_damage", "Nekromanta": "drain_healing", "Kapłan": "healing",\n    "Czarownik": "magic_damage", "Druid": "healing", "Psionik": "magic_defense",\n    "Mec": "damage_reduction", "Inżynier": "physical_damage",\n}\nRACE_PASSIVE_KIND = {\n    "Człowiek": "stat_xp", "Ogr": "physical_damage", "Elf": "dodge",\n    "Krasnolud": "damage_reduction", "Ork": "max_hp", "Niziołek": "profession_bonus",\n    "Mroczny Elf": "magic_damage", "Gnom": "max_mana", "Smoczy": "all_damage",\n    "Troll": "physical_reduction", "Diablę": "soul_xp", "Aasimar": "magic_defense",\n    "Driada": "healing", "Cyborg": "damage_reduction",\n}\n\ndef _percent_for_identity(identity: str, kind: str, low: float, high: float) -> float:\n    return low + (high-low) * stable_unit(f"{identity}:{kind}:passive")\n\ndef class_passive_profile(class_name: str) -> dict:\n    kind=CLASS_PASSIVE_KIND.get(class_name, "none")\n    if kind == "dodge":\n        value=round(_percent_for_identity(class_name,kind,.035,.055),4)\n    elif kind == "damage_reduction":\n        value=round(_percent_for_identity(class_name,kind,.08,.12),4)\n    elif kind in ("physical_damage","magic_damage","healing","magic_defense"):\n        value=round(_percent_for_identity(class_name,kind,.08,.13),4)\n    elif kind == "drain_healing":\n        value=round(_percent_for_identity(class_name,kind,.11,.17),4)\n    else:\n        value=0.0\n    return {"kind":kind,"value":value}\n\ndef race_passive_profile(race_name: str) -> dict:\n    kind=RACE_PASSIVE_KIND.get(race_name,"none")\n    ranges={\n        "stat_xp":(.08,.12),"physical_damage":(.09,.13),"dodge":(.035,.055),\n        "damage_reduction":(.08,.12),"max_hp":(.08,.13),"profession_bonus":(.02,.04),\n        "magic_damage":(.08,.13),"max_mana":(.10,.16),"all_damage":(.06,.10),\n        "physical_reduction":(.09,.14),"soul_xp":(.08,.13),"magic_defense":(.09,.14),\n        "healing":(.11,.17),\n    }\n    low,high=ranges.get(kind,(0.0,0.0))\n    return {"kind":kind,"value":round(_percent_for_identity(race_name,kind,low,high),4) if high else 0.0}\n\n\ndef passive_text_pl(kind: str, value: float) -> str:\n    pct=int(round(value*100))\n    return {\n        "physical_damage": f"+{pct} procent obrażeń fizycznych",\n        "magic_damage": f"+{pct} procent obrażeń magicznych",\n        "all_damage": f"+{pct} procent wszystkich obrażeń",\n        "healing": f"+{pct} procent mocy leczenia",\n        "drain_healing": f"+{pct} procent leczenia z wysysania życia",\n        "magic_defense": f"+{pct} procent obrony magicznej",\n        "damage_reduction": f"{pct} procent redukcji wszystkich obrażeń",\n        "physical_reduction": f"{pct} procent redukcji obrażeń fizycznych",\n        "dodge": f"+{pct} punktów procentowych uniku",\n        "stat_xp": f"+{pct} procent EXP statystyk",\n        "max_hp": f"+{pct} procent maksymalnego HP",\n        "profession_bonus": f"+{pct} punktów procentowych szansy na bonus profesji",\n        "max_mana": f"+{pct} procent maksymalnej Many",\n        "soul_xp": f"+{pct} procent Soul XP",\n    }.get(kind,"brak")\n\ndef class_passive_text_pl(class_name: str) -> str:\n    p=class_passive_profile(class_name); return passive_text_pl(p["kind"],p["value"])\n\ndef race_passive_text_pl(race_name: str) -> str:\n    p=race_passive_profile(race_name); return passive_text_pl(p["kind"],p["value"])\n\ndef _generate_soul(ns: dict) -> None:\n    """Balance existing Soul bonus values only; never rewrite tiers, thresholds, names or trial gates."""\n    try:\n        max_tier = max(1, int(ns.get("SOUL_MAX_TIER", 40) or 40))\n    except Exception:\n        max_tier = 40\n    if "SOUL_TIER_POWER_BONUSES" in ns:\n        _write_top_sequence(ns, "SOUL_TIER_POWER_BONUSES", (int(round((tier - 1) * 2.2)) for tier in range(1, max_tier + 1)))\n    if "SOUL_TIER_CLASS_BONUS_PERCENT" in ns:\n        _write_top_sequence(ns, "SOUL_TIER_CLASS_BONUS_PERCENT", (int(round(4 + (tier - 1) * .65)) for tier in range(1, max_tier + 1)))\n    if "SOUL_TIER_DODGE_BONUS" in ns:\n        _write_top_sequence(ns, "SOUL_TIER_DODGE_BONUS", (round(min(.05, .005 + (tier - 1) * .0012), 4) for tier in range(1, max_tier + 1)))\n    if "SOUL_TIER_GUARDIAN_REDUCTION" in ns:\n        _write_top_sequence(ns, "SOUL_TIER_GUARDIAN_REDUCTION", (int(round(2 + (tier - 1) * .45)) for tier in range(1, max_tier + 1)))\n    milestones = tuple(ns.get("SOUL_MILESTONE_TIERS", ()) or ())\n    spec = ns.get("SOUL_MILESTONE_SPECIALIZATION_BONUS")\n    if isinstance(spec, dict):\n        for tier in list(spec):\n            if tier in milestones:\n                _write_top_map_numeric(ns, "SOUL_MILESTONE_SPECIALIZATION_BONUS", tier, int(round(int(tier) * .45)))\n    dodge = ns.get("SOUL_MILESTONE_DODGE_BONUS")\n    if isinstance(dodge, dict):\n        for tier in list(dodge):\n            if tier in milestones:\n                _write_top_map_numeric(ns, "SOUL_MILESTONE_DODGE_BONUS", tier, round(min(.05, int(tier) * .0012), 4))\n    guard = ns.get("SOUL_MILESTONE_GUARDIAN_REDUCTION")\n    if isinstance(guard, dict):\n        for tier in list(guard):\n            if tier in milestones:\n                _write_top_map_numeric(ns, "SOUL_MILESTONE_GUARDIAN_REDUCTION", tier, int(round(int(tier) * .30)))\n\n\n\n\ndef _generate_class_set_bonuses(ns: dict) -> None:\n    """Rebalance values inside the authored set-bonus structure; never change owned stats/effects."""\n    table = ns.get("CLASS_SET_BONUSES")\n    if not isinstance(table, dict):\n        return\n    for cname, entry in table.items():\n        if not isinstance(entry, dict):\n            continue\n        stats = entry.get("stats")\n        if isinstance(stats, dict):\n            for stat in list(stats):\n                _write_class_set_numeric(entry, "stats", 3 + int(stable_unit(f"{cname}:set:stat:{stat}") * 4), leaf=stat)\n        if "damage" in entry:\n            _write_class_set_numeric(entry, "damage", round(1.06 + .10 * stable_unit(f"{cname}:set:damage"), 4))\n        if "defense" in entry:\n            _write_class_set_numeric(entry, "defense", round(1.08 + .18 * stable_unit(f"{cname}:set:defense"), 4))\n        if "vitality" in entry:\n            _write_class_set_numeric(entry, "vitality", round(1.10 + .22 * stable_unit(f"{cname}:set:vitality"), 4))\n\n\n\n\ndef _generate_class_race_numeric(ns: dict) -> None:\n    """Only the numeric Soul-weapon base may be balanced; class/race identity stays authored."""\n    classes = list(ns.get("CLASSES", []))\n    new_classes = []\n    for row in classes:\n        if len(row) >= 4:\n            name, ctype, weapon, _old_base, *rest = row\n            base = 7 + (1 if stable_unit(str(name) + \':weapon\') > .72 else 0)\n            new_classes.append((name, ctype, weapon, base, *rest))\n        else:\n            new_classes.append(row)\n    _write_classes_weapon_bases(ns, new_classes)\n\n    # RACES, CLASS_STARTING_STAT_BONUSES and all description text are authored and untouched.\n\n\n\ndef _rewrite_atlases(ns: dict, item_levels: dict[str, int]) -> None:\n    """Numeric-only v0.30.18: atlas/unlock thresholds are authored semantics and are never rewritten."""\n    return None\n\n\n\n\ndef _rewrite_area_targets(ns: dict, room_levels: dict[str, int], mob_levels: dict[str, int]) -> None:\n    """Update only numeric target-power telemetry; never rewrite area/gate requirements."""\n    targets = ns.get("EXP_AREA_TARGET_POWER")\n    zone_map = ns.get("EXP_ZONE_AREA_ID", {}) or {}\n    rooms = ns.get("ROOMS", {}) or {}\n    if not isinstance(targets, dict):\n        return\n    by_area = defaultdict(list)\n    for rid, room in rooms.items():\n        area = zone_map.get(room.get("zone"))\n        if area and rid in room_levels:\n            by_area[area].append(room_levels[rid])\n    mob_area_values = defaultdict(list)\n    for rid, mid in (ns.get("MOB_SPAWNS", []) or []):\n        room = rooms.get(rid, {})\n        area = zone_map.get(room.get("zone"))\n        if area and str(mid) in mob_levels:\n            mob_area_values[area].append(mob_levels[str(mid)])\n    for area in list(targets):\n        values = mob_area_values.get(area) or by_area.get(area)\n        if values:\n            value = min(values)\n        elif area == "trening":\n            value = 1\n        else:\n            value = 1 + int(stable_unit(f"area:{area}") * (MAX_LEVEL - 1))\n        _write_top_map_numeric(ns, "EXP_AREA_TARGET_POWER", area, value)\n\n\n\n\ndef runtime_room_level(room_id: str, room: dict, rooms: dict | None = None) -> int:\n    """Assign numeric balance stage to runtime rooms without creating gameplay gates."""\n    room_id = str(room_id or "room")\n    room = room or {}\n    lvl = semantic_floor_level(room)\n    if lvl is None:\n        text = f"{room_id} {room.get(\'zone\',\'\')} {room.get(\'name\',\'\')}".lower()\n        m = re.search(r"(?:floor|level|poziom|pietro|piętro)[_ -]*(\\d{1,5})", text)\n        if m and any(k in text for k in ("crypt", "krypt", "astral", "tower", "wież", "fortress", "twierdz", "dungeon", "loch", "mine", "kopal")):\n            lvl = int(m.group(1))\n    if lvl is None and rooms:\n        frontier = re.fullmatch(r"v0130_frontier_([a-z]+)_(\\d{2})_(\\d{2})", room_id)\n        if frontier:\n            kind, sx, sy = frontier.groups()\n            gateway = rooms.get(f"v0130_gateway_{kind}", {})\n            base = int(gateway.get("generator_level", 1) or 1)\n            distance = int(sx) + int(sy)\n            span = max(24, min(140, int(round((MAX_LEVEL - base) * 0.45))))\n            lvl = base + int(round((distance / 22.0) * span))\n    if lvl is None and rooms:\n        linked = []\n        for target in (room.get("exits") or {}).values():\n            other = rooms.get(target, {})\n            if other.get("generator_level") is not None:\n                linked.append(int(other["generator_level"]))\n        if linked:\n            lvl = max(1, min(linked))\n    if lvl is None:\n        lvl = 1 + int(stable_unit(f"runtime-room:{room_id}") * (MAX_LEVEL - 1))\n    lvl = clamp(int(lvl), 1, MAX_LEVEL)\n    _write_record_numeric("ROOMS", room, "generator_level", lvl)\n    return lvl\n\n\n\n\nNUMERIC_SKILL_FIELDS = {\n    "generator_level", "cooldown", "mana", "mult", "boost", "duration", "guard",\n    "heal_pct", "drain_pct", "execute_mult", "self_damage", "self_damage_pct",\n}\nNUMERIC_ITEM_FIELDS = {\n    "generator_level", "price", "sell_silver", "sell_gold", "sell_mithril", "defense",\n    "affix_amount", "heal", "mana", "soul_xp",\n}\nNUMERIC_MOB_FIELDS = {\n    "generator_level", "v019_stage", "max_hp", "base_max_hp", "damage",\n    "character_xp_reward", "class_xp_reward", "soul_reward", "stat_reward",\n    "silver", "gold", "mithril",\n}\nNUMERIC_QUEST_FIELDS = {\n    "generator_level", "character_xp_reward", "reward_soul_xp", "reward_stat_progress",\n    "reward_profession_xp", "reward_tool_xp", "reward_silver", "reward_gold", "reward_mithril",\n}\nNUMERIC_RECIPE_FIELDS = {"generator_level", "xp", "profession_xp", "tool_xp"}\n\n\n# v0.30.19: explicit, auditable write whitelist.\n# Design chooses WHAT exists; Generator Core may only decide HOW MUCH.\nGENERATOR_WRITE_WHITELIST = {\n    "ROOMS": frozenset({"generator_level"}),\n    "MOB_TEMPLATES": frozenset(NUMERIC_MOB_FIELDS),\n    "ITEMS": frozenset(NUMERIC_ITEM_FIELDS),\n    "QUESTS": frozenset(NUMERIC_QUEST_FIELDS),\n    "CLASS_SKILLS": frozenset(NUMERIC_SKILL_FIELDS),\n    "CRAFT_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),\n    "COOK_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),\n    "ALCHEMY_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),\n    "JEWELCRAFT_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),\n}\nGENERATOR_NESTED_VALUE_WHITELIST = {\n    "MOB_TEMPLATES": frozenset({"drops"}),\n    "ITEMS": frozenset({"stats", "properties", "rune_stats", "rune_properties"}),\n}\nGENERATOR_TOP_LEVEL_VALUE_WHITELIST = frozenset({\n    "SOUL_TIER_POWER_BONUSES",\n    "SOUL_TIER_CLASS_BONUS_PERCENT",\n    "SOUL_TIER_DODGE_BONUS",\n    "SOUL_TIER_GUARDIAN_REDUCTION",\n    "SOUL_MILESTONE_SPECIALIZATION_BONUS",\n    "SOUL_MILESTONE_DODGE_BONUS",\n    "SOUL_MILESTONE_GUARDIAN_REDUCTION",\n    "CLASS_SET_BONUSES",\n    "CLASSES",\n    "EXP_AREA_TARGET_POWER",\n})\n\n\n_GENERATOR_WHITELIST_WRITE_COUNT = 0\n\ndef _write_record_numeric(domain: str, record: dict, field: str, value) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    allowed = GENERATOR_WRITE_WHITELIST.get(domain, ())\n    if field not in allowed:\n        raise RuntimeError(f"Generator whitelist denied write: {domain}.{field}")\n    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):\n        raise RuntimeError(f"Generator whitelist denied non-numeric value: {domain}.{field}")\n    record[field] = value\n    _GENERATOR_WHITELIST_WRITE_COUNT += 1\n\n\ndef _write_nested_numeric(domain: str, record: dict, field: str, leaf, value) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    if field not in GENERATOR_NESTED_VALUE_WHITELIST.get(domain, ()):\n        raise RuntimeError(f"Generator whitelist denied nested write: {domain}.{field}")\n    mapping = record.get(field)\n    if not isinstance(mapping, dict) or leaf not in mapping:\n        raise RuntimeError(f"Generator whitelist denied new nested key: {domain}.{field}.{leaf}")\n    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):\n        raise RuntimeError(f"Generator whitelist denied non-numeric nested value: {domain}.{field}.{leaf}")\n    mapping[leaf] = value\n    _GENERATOR_WHITELIST_WRITE_COUNT += 1\n\n\ndef _write_top_sequence(ns: dict, key: str, values) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    if key not in GENERATOR_TOP_LEVEL_VALUE_WHITELIST or key not in ns:\n        raise RuntimeError(f"Generator whitelist denied top-level write: {key}")\n    old = ns[key]\n    new = tuple(values) if isinstance(old, tuple) else list(values) if isinstance(old, list) else values\n    if isinstance(old, (tuple, list)) and len(new) != len(old):\n        raise RuntimeError(f"Generator whitelist denied shape change: {key}")\n    if isinstance(new, (tuple, list)) and any(\n        not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(float(v))\n        for v in new\n    ):\n        raise RuntimeError(f"Generator whitelist denied non-numeric sequence: {key}")\n    ns[key] = new\n    _GENERATOR_WHITELIST_WRITE_COUNT += len(new) if isinstance(new, (tuple, list)) else 1\n\n\ndef _write_top_map_numeric(ns: dict, key: str, leaf, value) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    if key not in GENERATOR_TOP_LEVEL_VALUE_WHITELIST:\n        raise RuntimeError(f"Generator whitelist denied top-map write: {key}")\n    mapping = ns.get(key)\n    if not isinstance(mapping, dict) or leaf not in mapping:\n        raise RuntimeError(f"Generator whitelist denied new top-map key: {key}.{leaf}")\n    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):\n        raise RuntimeError(f"Generator whitelist denied non-numeric top-map value: {key}.{leaf}")\n    mapping[leaf] = value\n    _GENERATOR_WHITELIST_WRITE_COUNT += 1\n\n\ndef _write_class_set_numeric(entry: dict, field: str, value, leaf=None) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    if field == "stats":\n        stats = entry.get("stats")\n        if not isinstance(stats, dict) or leaf not in stats:\n            raise RuntimeError(f"Generator whitelist denied class-set stat key: {leaf}")\n        if not isinstance(value, (int, float)) or isinstance(value, bool):\n            raise RuntimeError(f"Generator whitelist denied class-set stat value: {leaf}")\n        stats[leaf] = value\n    elif field in ("damage", "defense", "vitality") and field in entry:\n        if not isinstance(value, (int, float)) or isinstance(value, bool):\n            raise RuntimeError(f"Generator whitelist denied class-set value: {field}")\n        entry[field] = value\n    else:\n        raise RuntimeError(f"Generator whitelist denied class-set write: {field}")\n    _GENERATOR_WHITELIST_WRITE_COUNT += 1\n\n\ndef _write_classes_weapon_bases(ns: dict, new_rows) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    old_rows = list(ns.get("CLASSES", ()) or ())\n    new_rows = list(new_rows)\n    if len(old_rows) != len(new_rows):\n        raise RuntimeError("Generator whitelist denied CLASSES shape change")\n    for old, new in zip(old_rows, new_rows):\n        if len(old) != len(new):\n            raise RuntimeError("Generator whitelist denied CLASSES row shape change")\n        for idx, (a, b) in enumerate(zip(old, new)):\n            if idx == 3:\n                if not isinstance(b, (int, float)) or isinstance(b, bool):\n                    raise RuntimeError("Generator whitelist denied non-numeric Soul weapon base")\n            elif a != b:\n                raise RuntimeError(f"Generator whitelist denied CLASSES semantic write at index {idx}")\n    ns["CLASSES"] = new_rows\n    _GENERATOR_WHITELIST_WRITE_COUNT += len(new_rows)\n\n\ndef _freeze_semantic(value):\n    if isinstance(value, dict):\n        return tuple(sorted((str(k), _freeze_semantic(v)) for k, v in value.items()))\n    if isinstance(value, (list, tuple)):\n        return tuple(_freeze_semantic(v) for v in value)\n    if isinstance(value, set):\n        return tuple(sorted((_freeze_semantic(v) for v in value), key=repr))\n    return value\n\n\ndef _protected_record(record: dict, numeric_fields: set[str], numeric_map_fields=()) -> tuple:\n    result = []\n    for key, value in record.items():\n        if key in numeric_fields:\n            continue\n        if key in numeric_map_fields and isinstance(value, dict):\n            result.append((str(key), tuple(sorted(map(str, value.keys())))))\n        elif key == "drops" and isinstance(value, dict):\n            # Drop identity is semantic; probabilities are numeric balance.\n            result.append(("drops", tuple(sorted(map(str, value.keys())))))\n        else:\n            result.append((str(key), _freeze_semantic(value)))\n    return tuple(sorted(result))\n\n\n\ndef _class_row_whitelist_projection(row):\n    """Only CLASSES[row][3] (Soul-weapon numeric base) may change."""\n    seq = list(row) if isinstance(row, (list, tuple)) else [row]\n    if len(seq) >= 4:\n        seq[3] = "<GENERATOR_NUMERIC>"\n    return _freeze_semantic(seq)\n\n\ndef _class_set_whitelist_projection(table):\n    """Protect class-set identity; allow only existing numeric values."""\n    out = {}\n    for cname, entry in (table or {}).items():\n        if not isinstance(entry, dict):\n            out[str(cname)] = _freeze_semantic(entry)\n            continue\n        row = {}\n        for key, value in entry.items():\n            if key == "stats" and isinstance(value, dict):\n                row[key] = tuple(sorted((str(stat), "<GENERATOR_NUMERIC>") for stat in value))\n            elif key in ("damage", "defense", "vitality"):\n                row[key] = "<GENERATOR_NUMERIC>"\n            else:\n                row[key] = _freeze_semantic(value)\n        out[str(cname)] = tuple(sorted(row.items()))\n    return _freeze_semantic(out)\n\n\ndef _value_container_whitelist_projection(value):\n    """Keep container shape/keys, hide only numeric values."""\n    if isinstance(value, dict):\n        return tuple(sorted((str(k), "<GENERATOR_NUMERIC>") for k in value))\n    if isinstance(value, (list, tuple)):\n        return (type(value).__name__, len(value), tuple("<GENERATOR_NUMERIC>" for _ in value))\n    return "<GENERATOR_NUMERIC>"\n\n\ndef generator_whitelist_fingerprint(ns: dict) -> str:\n    """Cheap shape fingerprint; safe setters enforce every Generator write."""\n    protected = [("TOP_LEVEL_KEYS", tuple(sorted(str(k) for k in ns.keys())))]\n    # Top-level write domains may change values only, never shape/keys.\n    protected.append(("CLASSES_SHAPE", tuple(len(row) for row in (ns.get("CLASSES", ()) or ()))))\n    protected.append(("CLASS_SET_KEYS", tuple(\n        (str(cname),\n         tuple(sorted(str(k) for k in entry.keys())) if isinstance(entry, dict) else ("<NON_DICT>",),\n         tuple(sorted(str(k) for k in (entry.get("stats") or {}).keys())) if isinstance(entry, dict) and isinstance(entry.get("stats"), dict) else ())\n        for cname, entry in (ns.get("CLASS_SET_BONUSES", {}) or {}).items()\n    )))\n    protected.append(("EXP_AREA_KEYS", tuple(sorted(str(k) for k in (ns.get("EXP_AREA_TARGET_POWER", {}) or {}).keys()))))\n    for key in sorted(GENERATOR_TOP_LEVEL_VALUE_WHITELIST - {"CLASSES", "CLASS_SET_BONUSES", "EXP_AREA_TARGET_POWER"}):\n        value = ns.get(key)\n        if isinstance(value, dict):\n            shape = ("dict", tuple(sorted(str(k) for k in value.keys())))\n        elif isinstance(value, (list, tuple)):\n            shape = (type(value).__name__, len(value))\n        else:\n            shape = (type(value).__name__,)\n        protected.append((key, shape))\n    return hashlib.sha256(repr(tuple(protected)).encode("utf-8")).hexdigest()\n\n\n\n\n\ndef _is_generator_number(value) -> bool:\n    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))\n\n\ndef _validate_record_whitelist_numbers(ns: dict, errors: list[str]) -> int:\n    checked = 0\n    for table_name, allowed in GENERATOR_WRITE_WHITELIST.items():\n        table = ns.get(table_name, {}) or {}\n        if not isinstance(table, dict):\n            errors.append(f"whitelist table {table_name} is not dict")\n            continue\n        nested = GENERATOR_NESTED_VALUE_WHITELIST.get(table_name, ())\n        for rid, record in table.items():\n            if not isinstance(record, dict):\n                continue\n            for field in allowed:\n                if field in record:\n                    checked += 1\n                    if not _is_generator_number(record[field]):\n                        errors.append(f"non-numeric whitelisted value {table_name}.{rid}.{field}")\n            for field in nested:\n                mapping = record.get(field)\n                if mapping is None:\n                    continue\n                if not isinstance(mapping, dict):\n                    errors.append(f"whitelist nested field {table_name}.{rid}.{field} is not dict")\n                    continue\n                for leaf, value in mapping.items():\n                    checked += 1\n                    if not _is_generator_number(value):\n                        errors.append(f"non-numeric whitelisted value {table_name}.{rid}.{field}.{leaf}")\n    return checked\n\n\ndef generator_whitelist_validate(ns: dict, before_fingerprint: str) -> dict:\n    after = generator_whitelist_fingerprint(ns)\n    errors = []\n    if before_fingerprint != after:\n        errors.append("Generator Core changed a protected whitelist shape/key")\n    return {\n        "version": GENERATOR_VERSION,\n        "enforced": True,\n        "passed": not errors,\n        "fingerprint_before": before_fingerprint,\n        "fingerprint_after": after,\n        "numeric_values_checked": int(_GENERATOR_WHITELIST_WRITE_COUNT),\n        "error_count": len(errors),\n        "errors": errors,\n        "record_whitelist": {k: tuple(sorted(v)) for k, v in GENERATOR_WRITE_WHITELIST.items()},\n        "nested_value_whitelist": {k: tuple(sorted(v)) for k, v in GENERATOR_NESTED_VALUE_WHITELIST.items()},\n        "top_level_value_whitelist": tuple(sorted(GENERATOR_TOP_LEVEL_VALUE_WHITELIST)),\n    }\n\n\n\ndef semantic_fingerprint(ns: dict) -> str:\n    """Hash all authored semantics that Generator Core is forbidden to change."""\n    protected = []\n    protected.append(("CLASSES", tuple(tuple(row[:3]) for row in ns.get("CLASSES", ()))))\n    protected.append(("RACES", _freeze_semantic(ns.get("RACES", ()))))\n    protected.append(("CLASS_DESCRIPTIONS", _freeze_semantic(ns.get("CLASS_DESCRIPTIONS", {}))))\n    protected.append(("CLASS_STARTING_STAT_BONUSES", _freeze_semantic(ns.get("CLASS_STARTING_STAT_BONUSES", {}))))\n    constants = (\n        "SOUL_MAX_LEVEL", "SOUL_MAX_TIER", "SOUL_TIER_THRESHOLDS", "TIER2_LEVEL", "TIER3_LEVEL", "TIER4_LEVEL", "TIER5_LEVEL",\n        "SOUL_SKILL_UNLOCK_LEVELS", "SOUL_MILESTONE_TIERS", "SOUL_MILESTONE_NAMES",\n        "PROFESSION_RANK_THRESHOLDS", "PROFESSION_MAX_RANK", "BLACKSMITHING_RANK_THRESHOLDS", "BLACKSMITHING_MAX_RANK",\n        "TOOL_TIER_THRESHOLDS", "TOOL_MAX_TIER", "ASTRAL_MIN_SOUL_LEVEL", "MYTHIC_CRYPT_MIN_SOUL_LEVEL", "MYTHIC_ASTRAL_MIN_SOUL_LEVEL",\n    )\n    protected.append(("CONSTANTS", tuple((k, _freeze_semantic(ns.get(k))) for k in constants)))\n    protected.append(("SKILLS", tuple(\n        (str(cname), tuple(_protected_record(s, NUMERIC_SKILL_FIELDS) for s in rows))\n        for cname, rows in (ns.get("CLASS_SKILLS", {}) or {}).items()\n    )))\n    protected.append(("ITEMS", tuple(\n        (str(iid), _protected_record(item, NUMERIC_ITEM_FIELDS, ("stats", "properties", "rune_stats", "rune_properties")))\n        for iid, item in (ns.get("ITEMS", {}) or {}).items()\n    )))\n    protected.append(("MOBS", tuple(\n        (str(mid), _protected_record(mob, NUMERIC_MOB_FIELDS))\n        for mid, mob in (ns.get("MOB_TEMPLATES", {}) or {}).items()\n    )))\n    protected.append(("QUESTS", tuple(\n        (str(qid), _protected_record(q, NUMERIC_QUEST_FIELDS))\n        for qid, q in (ns.get("QUESTS", {}) or {}).items()\n    )))\n    recipes = []\n    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):\n        recipes.append((table_name, tuple(\n            (str(rid), _protected_record(recipe, NUMERIC_RECIPE_FIELDS))\n            for rid, recipe in (ns.get(table_name, {}) or {}).items()\n        )))\n    protected.append(("RECIPES", tuple(recipes)))\n    protected.append(("NPCS", _freeze_semantic(ns.get("NPCS", {}))))\n    protected.append(("MOB_SPAWNS", _freeze_semantic(ns.get("MOB_SPAWNS", ()))))\n    protected.append(("ROOMS", tuple(\n        (str(rid), _protected_record(room, {"generator_level"}))\n        for rid, room in (ns.get("ROOMS", {}) or {}).items()\n    )))\n    protected.append(("ATLASES", _freeze_semantic({\n        "ORE_ATLAS_LEVELS": ns.get("ORE_ATLAS_LEVELS", {}),\n        "ORE_MINE_FLOOR_MINIMUMS": ns.get("ORE_MINE_FLOOR_MINIMUMS", {}),\n        "WOOD_ATLAS_ROOM_MIN_LEVELS": ns.get("WOOD_ATLAS_ROOM_MIN_LEVELS", {}),\n        "HERB_ATLAS_ROOM_MIN_LEVELS": ns.get("HERB_ATLAS_ROOM_MIN_LEVELS", {}),\n    })))\n    protected.append(("EXP_AREAS", _freeze_semantic(ns.get("EXP_AREAS", ()))))\n    set_structure = {}\n    for cname, entry in (ns.get("CLASS_SET_BONUSES", {}) or {}).items():\n        if isinstance(entry, dict):\n            set_structure[str(cname)] = {\n                "keys": tuple(sorted(map(str, entry.keys()))),\n                "stat_keys": tuple(sorted(map(str, (entry.get("stats") or {}).keys()))) if isinstance(entry.get("stats"), dict) else (),\n            }\n    protected.append(("CLASS_SET_STRUCTURE", _freeze_semantic(set_structure)))\n    return hashlib.sha256(repr(tuple(protected)).encode("utf-8")).hexdigest()\n\ndef validate(ns: dict) -> dict:\n    errors = []\n    mobs = ns.get("MOB_TEMPLATES", {})\n    items = ns.get("ITEMS", {})\n    quests = ns.get("QUESTS", {})\n    skills = ns.get("CLASS_SKILLS", {})\n    recipes = sum((len(ns.get(name, {}) or {}) for name in ("CRAFT_RECIPES","COOK_RECIPES","ALCHEMY_RECIPES","JEWELCRAFT_RECIPES")), 0)\n    for mid, t in mobs.items():\n        lvl = int(t.get("generator_level", 0) or 0)\n        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"mob level {mid}")\n        rank = mob_rank(t)\n        if int(t.get("max_hp",0) or 0) != mob_hp(lvl, rank): errors.append(f"mob hp {mid}")\n        if int(t.get("damage",0) or 0) != mob_damage(lvl, rank): errors.append(f"mob damage {mid}")\n        if int(t.get("character_xp_reward",0) or 0) != axis_gain("character", lvl, RANK_REWARD.get(rank,1.0)): errors.append(f"mob charxp {mid}")\n        if int(t.get("class_xp_reward",0) or 0) != axis_gain("class", lvl, RANK_REWARD.get(rank,1.0)): errors.append(f"mob classxp {mid}")\n        if int(t.get("soul_reward",0) or 0) != axis_gain("soul", lvl, RANK_REWARD.get(rank,1.0)): errors.append(f"mob soulxp {mid}")\n        if int(t.get("silver",0) or 0) != currency_for_stage(lvl, rank): errors.append(f"mob currency {mid}")\n    for iid, item in items.items():\n        lvl = int(item.get("generator_level",0) or 0)\n        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"item level {iid}")\n        if int(item.get("price",0) or 0) <= 0: errors.append(f"item price {iid}")\n    for qid, q in quests.items():\n        lvl = int(q.get("generator_level",0) or 0)\n        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"quest level {qid}")\n        if int(q.get("character_xp_reward",0) or 0) <= 0: errors.append(f"quest charxp {qid}")\n        reward = int(q.get("reward_silver",0) or 0)\n        manual = q.get("manual_currency_reward_coins")\n        if manual is not None:\n            if reward != clamp(int(manual), 0, SAFE_INT):\n                errors.append(f"quest manual currency changed {qid}: {reward}!={manual}")\n        elif reward < 1001:\n            errors.append(f"quest currency {qid}")\n        if int(q.get("reward_gold",0) or 0) != 0 or int(q.get("reward_mithril",0) or 0) != 0:\n            errors.append(f"quest split currency {qid}")\n    skill_count = 0\n    skill_grid = (1, *range(10, MAX_LEVEL + 1, 10))\n    skill_grid_set = set(skill_grid)\n    for cname, rows in skills.items():\n        unlocks = []\n        per_unlock = defaultdict(int)\n        for s in rows:\n            skill_count += 1\n            try: unlock = int(s.get("unlock",0) or 0)\n            except Exception: unlock = 0\n            unlocks.append(unlock)\n            if not 1 <= unlock <= MAX_LEVEL: errors.append(f"skill level {s.get(\'id\')}")\n            if cname not in ("Inżynier","Mec") and unlock not in skill_grid_set: errors.append(f"skill off-grid {s.get(\'id\')}:{unlock}")\n            per_unlock[unlock] += 1\n        if unlocks and (min(unlocks) != 1 or max(unlocks) != MAX_LEVEL): errors.append(f"skill span {cname}")\n        if cname not in ("Inżynier","Mec"):\n            for level in skill_grid:\n                if per_unlock.get(level, 0) != 3:\n                    errors.append(f"skill grid {cname}:{level}={per_unlock.get(level,0)} expected=3")\n    for table_name in ("CRAFT_RECIPES","COOK_RECIPES","ALCHEMY_RECIPES","JEWELCRAFT_RECIPES"):\n        for rid, recipe in (ns.get(table_name, {}) or {}).items():\n            lvl = int(recipe.get("generator_level", 0) or 0)\n            if not 1 <= lvl <= MAX_LEVEL: errors.append(f"recipe level {rid}")\n            if int(recipe.get("profession_xp",0) or 0) <= 0: errors.append(f"recipe profession xp {rid}")\n            if int(recipe.get("tool_xp",0) or 0) <= 0: errors.append(f"recipe tool xp {rid}")\n    for fn_name, fn in (("mob_hp", mob_hp),("mob_damage",mob_damage)):\n        vals = [fn(l) for l in range(1, MAX_LEVEL+1)]\n        if any(b < a for a,b in zip(vals, vals[1:])): errors.append(f"nonmonotonic {fn_name}")\n    for axis in AXIS_CURVES:\n        vals = [axis_requirement(axis,l) for l in range(1, MAX_LEVEL+1)]\n        if any(b < a for a,b in zip(vals,vals[1:])): errors.append(f"nonmonotonic {axis}")\n    return {\n        "errors": errors,\n        "error_count": len(errors),\n        "mobs": len(mobs), "items": len(items), "quests": len(quests),\n        "skills": skill_count, "recipes": recipes, "rooms": len(ns.get("ROOMS",{})),\n    }\n\n\n\ndef apply_generator_core(ns: dict) -> dict:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    _GENERATOR_WHITELIST_WRITE_COUNT = 0\n    full_audit = os.environ.get("SOULBOUND_FULL_AUDIT", "").strip().lower() in ("1", "true", "yes", "on")\n    if full_audit:\n        semantic_before = semantic_fingerprint(ns)\n        whitelist_before = generator_whitelist_fingerprint(ns)\n    else:\n        semantic_before = None\n        whitelist_before = None\n\n    _generate_soul(ns)\n    _generate_class_race_numeric(ns)\n    _generate_class_set_bonuses(ns)\n    room_levels = _graph_room_levels(ns.get("ROOMS", {}) or {})\n    mob_levels = _mob_levels(ns, room_levels)\n    _generate_mobs(ns, mob_levels)\n    item_levels = _item_levels(ns, mob_levels)\n    _generate_items(ns, item_levels)\n    recipe_count = _generate_recipes(ns, item_levels)\n    _generate_quests(ns, mob_levels, item_levels)\n    skill_count = _generate_skills(ns)\n    _rewrite_atlases(ns, item_levels)\n    _rewrite_area_targets(ns, room_levels, mob_levels)\n\n    if full_audit:\n        semantic_after = semantic_fingerprint(ns)\n        whitelist_audit = generator_whitelist_validate(ns, whitelist_before)\n        audit = validate(ns)\n        semantic_ok = semantic_before == semantic_after\n        audit["semantic_fingerprint_before"] = semantic_before\n        audit["semantic_fingerprint_after"] = semantic_after\n        audit["semantic_preserved"] = semantic_ok\n        audit["whitelist_enforced"] = True\n        audit["whitelist_passed"] = bool(whitelist_audit.get("passed"))\n        audit["whitelist_audit"] = whitelist_audit\n        if not semantic_ok:\n            audit["errors"].append("Generator Core changed protected authored semantics")\n        if not whitelist_audit.get("passed"):\n            audit["errors"].extend(whitelist_audit.get("errors", []))\n        audit["error_count"] = len(audit["errors"])\n    else:\n        audit = {\n            "errors": [], "error_count": 0, "runtime_fast_path": True,\n            "semantic_preserved": None, "whitelist_enforced": False,\n            "whitelist_passed": None, "whitelist_audit": None,\n            "mobs": len(ns.get("MOB_TEMPLATES", {}) or {}),\n            "items": len(ns.get("ITEMS", {}) or {}),\n            "quests": len(ns.get("QUESTS", {}) or {}),\n            "skills": sum(len(rows) for rows in (ns.get("CLASS_SKILLS", {}) or {}).values()),\n            "recipes": sum(len(ns.get(name, {}) or {}) for name in ("CRAFT_RECIPES","COOK_RECIPES","ALCHEMY_RECIPES","JEWELCRAFT_RECIPES")),\n            "rooms": len(ns.get("ROOMS", {}) or {}),\n        }\n\n    audit["recipe_count_generated"] = recipe_count\n    audit["skill_count_generated"] = skill_count\n    audit["numeric_only"] = True\n    ns["GENERATOR_CORE_AUDIT"] = audit\n    ns["GENERATOR_CORE_VERSION"] = GENERATOR_VERSION\n    ns["GENERATOR_ROOM_LEVELS"] = room_levels\n    ns["GENERATOR_MOB_LEVELS"] = mob_levels\n    ns["GENERATOR_ITEM_LEVELS"] = item_levels\n    return audit\n'
generator_core_v027 = _load_embedded_runtime_module('generator_core', _EMBEDDED_GENERATOR_CORE_SOURCE)

_EMBEDDED_WORLD_TOPOLOGY_GENERATOR_SOURCE = '"""Soulbound v0.30.0 Semantic Universal World Topology Generator.\n\nAll non-runtime/static zone topology is generated deterministically from a seed.\nContent records keep semantic identity (room id/name/role), while adjacency is not\ntrusted from hand-authored horizontal exits. Existing procedural systems keep their\nown generated topology. Cross-zone gateways and vertical semantic links are kept as\nanchors so saves, quests and runtime portals remain compatible.\n"""\nfrom __future__ import annotations\n\nfrom collections import defaultdict, deque\nimport hashlib\n\nGENERATOR_VERSION = "0.30.0"\nWORLD_TOPOLOGY_SEED = "soulbound:v0.30.0:semantic-world-topology"\nCARDINAL = ("north", "east", "south", "west")\nDIAGONAL = ("northeast", "southeast", "southwest", "northwest")\nHORIZONTAL = CARDINAL + DIAGONAL\nGENERATED_DIRS = HORIZONTAL\nOPPOSITE = {"north":"south", "south":"north", "east":"west", "west":"east", "northeast":"southwest", "southwest":"northeast", "northwest":"southeast", "southeast":"northwest", "up":"down", "down":"up"}\n\n# v0.30.0: generator ma tworzyć logiczny świat, nie losową sieć.\n# Tożsamość lokacji pozostaje treścią świata, ale generator przypisuje jej\n# rolę semantyczną i preferuje zgodne sąsiedztwa. Pion jest zarezerwowany\n# wyłącznie dla zachowanych semantycznych schodów/piwnic/wież/portali.\ndef _room_role(rid: str, room: dict) -> str:\n    text=(str(rid)+" "+str(room.get("name") or "")).lower()\n    if any(k in text for k in ("gate", "brama", "street", "ulica", "lane", "alley", "zauł", "road", "trakt", "path", "szlak", "square", "plac")):\n        return "transit"\n    if any(k in text for k in ("temple", "świąty", "swiaty", "shrine", "kaplic", "cathedral", "katedr")):\n        return "sacred"\n    if any(k in text for k in ("guard", "straż", "straz", "barrack", "koszar", "armory", "zbroj", "watch", "patrol", "training", "arena")):\n        return "guard"\n    if any(k in text for k in ("harbor", "port", "dock", "stoczn", "ship", "pier", "nabrze", "warehouse", "magazyn", "ropewalk", "powroź")):\n        return "harbor"\n    if any(k in text for k in ("market", "targ", "inn", "karcz", "bakery", "piek", "pharmacy", "apte", "healer", "uzdrow", "kitchen", "kuchn")):\n        return "commerce"\n    if any(k in text for k in ("forge", "kuź", "kuz", "workshop", "warsztat", "jeweler", "jubiler", "tailor", "krawiec", "carpenter", "ciesiel", "leather", "kalet", "mason", "kamien", "potter", "garncar")):\n        return "craft"\n    if any(k in text for k in ("library", "bibliot", "archive", "archiw", "school", "szko", "courier", "kurier", "cartograph", "kartograf", "office", "biuro")):\n        return "civic"\n    if any(k in text for k in ("guild", "gild")):\n        return "guild"\n    if any(k in text for k in ("house", "dom", "residential", "miesz", "well", "studn")):\n        return "residential"\n    if any(k in text for k in ("cave", "jask", "crypt", "krypt", "sewer", "kanał", "kanal", "basement", "piwn", "dungeon", "loch", "mine", "kopal")):\n        return "underground"\n    if any(k in text for k in ("mountain", "gór", "gor", "summit", "szczyt", "ice", "lodow")):\n        return "highland"\n    if any(k in text for k in ("forest", "las", "grove", "gaj", "meadow", "łąk", "lak", "river", "rzek", "lake", "jezior", "swamp", "bag", "desert", "pust")):\n        return "wilderness"\n    return "general"\n\n_ROLE_COMPAT = {\n    "transit": {"transit":10,"civic":9,"commerce":9,"guard":9,"residential":9,"craft":8,"harbor":8,"sacred":8,"guild":8,"general":8,"wilderness":6,"underground":3,"highland":3},\n    "sacred": {"sacred":10,"transit":9,"civic":8,"residential":6,"guard":6,"guild":5,"commerce":4,"craft":3,"harbor":3,"general":6,"underground":6,"wilderness":5,"highland":3},\n    "guard": {"guard":10,"transit":9,"civic":8,"guild":7,"residential":6,"commerce":6,"craft":6,"harbor":7,"general":7,"sacred":6,"wilderness":6,"underground":6,"highland":6},\n    "harbor": {"harbor":10,"transit":9,"craft":9,"commerce":8,"guard":7,"civic":6,"residential":5,"general":7,"wilderness":6,"sacred":3,"guild":5,"underground":4,"highland":2},\n    "commerce": {"commerce":10,"transit":9,"craft":9,"residential":8,"civic":7,"harbor":8,"guard":6,"guild":6,"general":7,"sacred":4,"wilderness":4,"underground":3,"highland":2},\n    "craft": {"craft":10,"transit":8,"commerce":9,"harbor":9,"residential":6,"guard":6,"civic":6,"guild":6,"general":7,"sacred":3,"wilderness":5,"underground":5,"highland":5},\n    "civic": {"civic":10,"transit":9,"sacred":8,"guard":8,"commerce":7,"guild":8,"residential":7,"craft":6,"harbor":6,"general":7,"wilderness":4,"underground":4,"highland":3},\n    "guild": {"guild":10,"transit":9,"civic":8,"guard":8,"commerce":7,"craft":7,"residential":5,"harbor":5,"sacred":5,"general":7,"wilderness":5,"underground":5,"highland":5},\n    "residential": {"residential":10,"transit":9,"commerce":8,"civic":7,"craft":6,"guard":6,"sacred":6,"guild":5,"harbor":5,"general":7,"wilderness":4,"underground":3,"highland":2},\n    "underground": {"underground":10,"transit":5,"guard":6,"sacred":6,"craft":5,"general":6,"wilderness":6,"highland":7},\n    "highland": {"highland":10,"wilderness":8,"transit":5,"guard":6,"craft":5,"underground":7,"general":6},\n    "wilderness": {"wilderness":10,"highland":8,"underground":7,"transit":6,"guard":6,"craft":5,"general":7},\n    "general": {"general":8,"transit":8,"civic":7,"commerce":7,"guard":7,"craft":7,"harbor":7,"sacred":6,"guild":7,"residential":7,"wilderness":7,"underground":6,"highland":6},\n}\n\ndef _role_compat(a_role: str, b_role: str) -> int:\n    return int(_ROLE_COMPAT.get(a_role, {}).get(b_role, _ROLE_COMPAT.get(b_role, {}).get(a_role, 5)))\n\n\ndef _unit(text: str) -> float:\n    raw = hashlib.sha256(str(text).encode("utf-8")).digest()\n    return int.from_bytes(raw[:8], "big") / float((1 << 64) - 1)\n\n\ndef _is_native_procedural(room: dict) -> bool:\n    # v0.28 regions already own their complete topology. Other runtime/infinite\n    # dungeons are materialized outside the static ROOMS registry.\n    return bool(room.get("procedural_region_v028") or room.get("procedural_dynamic"))\n\n\ndef _normalize_cross_zone_edges(rooms):\n    """Make every static cross-zone edge geometrically reciprocal.\n\n    The semantic zone relationship is preserved, but direction slots are chosen\n    deterministically. This removes legacy cases such as south one way / west back.\n    """\n    pairs={}\n    for a,room in rooms.items():\n        za=str(room.get("zone") or "Bez strefy")\n        for d,b in list((room.get("exits") or {}).items()):\n            if b not in rooms: continue\n            zb=str(rooms[b].get("zone") or "Bez strefy")\n            if za==zb: continue\n            key=tuple(sorted((a,b)))\n            pairs.setdefault(key,[]).append((a,d,b))\n    for (x,y),records in sorted(pairs.items()):\n        # Remove only direct x<->y links; unrelated exits keep their slots.\n        old_xy=[]; old_yx=[]\n        for d,t in list(rooms[x].setdefault("exits",{}).items()):\n            if t==y: old_xy.append(d); del rooms[x]["exits"][d]\n        for d,t in list(rooms[y].setdefault("exits",{}).items()):\n            if t==x: old_yx.append(d); del rooms[y]["exits"][d]\n        # Preserve true vertical semantics whenever possible.\n        preferred=[]\n        for d in old_xy:\n            preferred.append(d)\n        for d in old_yx:\n            if d in OPPOSITE: preferred.append(OPPOSITE[d])\n        ordered=[]\n        for d in preferred + list(HORIZONTAL) + ["up","down"]:\n            if d in OPPOSITE and d not in ordered: ordered.append(d)\n        chosen=None\n        for d in ordered:\n            rev=OPPOSITE[d]\n            if _free(rooms[x],d) and _free(rooms[y],rev):\n                chosen=(d,rev); break\n        if not chosen:\n            raise RuntimeError(f"No reciprocal direction slots for cross-zone edge {x}<->{y}")\n        rooms[x]["exits"][chosen[0]]=y\n        rooms[y]["exits"][chosen[1]]=x\n\n\ndef _zone_groups(rooms):\n    groups = defaultdict(list)\n    for rid, room in rooms.items():\n        if _is_native_procedural(room):\n            continue\n        groups[str(room.get("zone") or "Bez strefy")].append(rid)\n    return groups\n\n\ndef _free(room, direction):\n    return direction not in room.setdefault("exits", {})\n\n\ndef _connect(rooms, a, da, b, db):\n    if not _free(rooms[a], da) or not _free(rooms[b], db):\n        return False\n    rooms[a]["exits"][da] = b\n    rooms[b]["exits"][db] = a\n    return True\n\n\ndef _internal_neighbors(rooms, rid, zone):\n    out=[]\n    for target in rooms[rid].get("exits", {}).values():\n        if target in rooms and str(rooms[target].get("zone") or "Bez strefy") == zone:\n            out.append(target)\n    return out\n\n\ndef _components(rooms, ids, zone):\n    # Only reciprocal preserved links form a pre-connected component. One-way\n    # historical links do not count, because the generated world must be fully\n    # navigable in both directions.\n    ids=set(ids); seen=set(); comps=[]\n    for start in sorted(ids):\n        if start in seen: continue\n        q=[start]; seen.add(start); comp=[]\n        while q:\n            cur=q.pop(); comp.append(cur)\n            for d,nxt in rooms[cur].get("exits",{}).items():\n                if nxt not in ids or nxt not in rooms: continue\n                if str(rooms[nxt].get("zone") or "Bez strefy") != zone: continue\n                rev=OPPOSITE.get(d)\n                if not rev or rooms[nxt].get("exits",{}).get(rev)!=cur: continue\n                if nxt not in seen:\n                    seen.add(nxt); q.append(nxt)\n        comps.append(sorted(comp))\n    return comps\n\n\ndef _component_slots(rooms, comp):\n    slots=[]\n    for rid in comp:\n        for d in GENERATED_DIRS:\n            if _free(rooms[rid], d): slots.append((rid,d))\n    return slots\n\n\ndef _candidate_links(rooms, left, right, seed):\n    candidates=[]\n    right_set=set(right)\n    for a, da in _component_slots(rooms,left):\n        db=OPPOSITE[da]\n        for b in right_set:\n            if _free(rooms[b],db):\n                role_score=_role_compat(_room_role(a,rooms[a]), _room_role(b,rooms[b]))\n                score=role_score*10.0 + _unit(f"{seed}:link:{a}:{da}:{b}")\n                candidates.append((score,a,da,b,db))\n    candidates.sort(reverse=True)\n    return candidates\n\n\ndef _choose_root(zone, ids, rooms):\n    preferred={\n        "Miasto Dusz":"square", "Gildia Dusz":"guild_hall", "Wioska Górska":"mountain_village",\n        "Podziemia":"temple_basement", "Kanały Pod Miastem":"sewer_entrance",\n    }.get(zone)\n    if preferred in ids: return preferred\n    # Prefer a room with external anchors, then deterministic hash.\n    ranked=[]\n    for rid in ids:\n        ext=sum(1 for t in rooms[rid].get("exits",{}).values() if t in rooms and rooms[t].get("zone")!=zone)\n        ranked.append((-ext, _unit(f"{WORLD_TOPOLOGY_SEED}:root:{zone}:{rid}"), rid))\n    ranked.sort()\n    return ranked[0][2]\n\n\ndef _generate_zone(rooms, zone, ids):\n    ids=list(ids)\n    if len(ids) <= 1:\n        for rid in ids:\n            rooms[rid]["topology_generated_v0281"] = True\n            rooms[rid]["topology_generated_v030"] = True\n            rooms[rid]["world_role"] = _room_role(rid, rooms[rid])\n        return {"rooms":len(ids),"links":0,"loops":0,"root":ids[0] if ids else None}\n\n    seed=f"{WORLD_TOPOLOGY_SEED}:{zone}"\n    # Keep cross-zone gateways and all vertical semantic links. Horizontal links\n    # inside this zone are deliberately discarded and rebuilt from the seed.\n    for rid in ids:\n        old=dict(rooms[rid].get("exits",{})); new={}\n        for d,target in old.items():\n            if d in ("up","down"):\n                new[d]=target\n            elif target not in rooms:\n                new[d]=target\n            elif str(rooms[target].get("zone") or "Bez strefy") != zone:\n                new[d]=target\n        rooms[rid]["exits"]=new\n\n    # Normalize preserved internal vertical links. A vertical pair must be exact\n    # up<->down. Conflicting legacy one-way links are dropped and the affected\n    # rooms are reconnected horizontally by the generated topology.\n    for rid in sorted(ids):\n        for d,target in list(rooms[rid].get("exits",{}).items()):\n            if d not in ("up","down") or target not in rooms: continue\n            if str(rooms[target].get("zone") or "Bez strefy") != zone: continue\n            rev=OPPOSITE[d]\n            rooms[target].setdefault("exits",{})\n            back=rooms[target]["exits"].get(rev)\n            if back==rid:\n                continue\n            if back is None:\n                rooms[target]["exits"][rev]=rid\n            else:\n                # Another semantic vertical pair owns this shaft/stair slot.\n                del rooms[rid]["exits"][d]\n\n    root=_choose_root(zone,ids,rooms)\n    comps=_components(rooms,ids,zone)\n    # Put root component first, remaining components in deterministic order.\n    comps.sort(key=lambda c:(0 if root in c else 1, _unit(f"{seed}:component:{\'|\'.join(c)}")))\n    connected=list(comps[0])\n    links=0\n    for comp in comps[1:]:\n        # Find a generated cardinal link from any already-connected node into this component.\n        left=connected\n        cand=_candidate_links(rooms,left,comp,seed)\n        if not cand:\n            raise RuntimeError(f"Topology generator has no free cardinal slots in zone {zone!r} for component {comp[:3]}")\n        _,a,da,b,db=cand[0]\n        if not _connect(rooms,a,da,b,db):\n            raise RuntimeError(f"Topology generator failed to connect {a} and {b}")\n        links+=1; connected.extend(comp)\n\n    # Add deterministic loops, aiming at roughly one extra link per 6 rooms.\n    loop_target=max(1,len(ids)//6) if len(ids)>=5 else 0\n    loops=0\n    pair_candidates=[]\n    ordered=sorted(ids)\n    for i,a in enumerate(ordered):\n        for b in ordered[i+1:]:\n            if b in rooms[a].get("exits",{}).values(): continue\n            for da in GENERATED_DIRS:\n                db=OPPOSITE[da]\n                if _free(rooms[a],da) and _free(rooms[b],db):\n                    compat=_role_compat(_room_role(a,rooms[a]), _room_role(b,rooms[b]))\n                    pair_candidates.append((compat*10.0+_unit(f"{seed}:loop:{a}:{da}:{b}"),a,da,b,db))\n    pair_candidates.sort(reverse=True)\n    for _,a,da,b,db in pair_candidates:\n        if loops>=loop_target: break\n        if _connect(rooms,a,da,b,db): loops+=1\n\n    # Annotate generated layout metadata.\n    # BFS depth is useful for accessible map/debug output and future content generation.\n    depth={root:0}; q=deque([root])\n    while q:\n        cur=q.popleft()\n        for nxt in _internal_neighbors(rooms,cur,zone):\n            if nxt not in depth:\n                depth[nxt]=depth[cur]+1; q.append(nxt)\n    if len(depth)!=len(ids):\n        missing=sorted(set(ids)-set(depth))[:10]\n        raise RuntimeError(f"Generated zone {zone!r} disconnected: {missing}")\n    for rid in ids:\n        rooms[rid]["topology_generated_v0281"]=True\n        rooms[rid]["topology_generated_v030"]=True\n        rooms[rid]["world_role"]=_room_role(rid,rooms[rid])\n        rooms[rid]["topology_zone_depth"]=depth[rid]\n        rooms[rid]["topology_seed"]=seed\n    return {"rooms":len(ids),"links":links,"loops":loops,"root":root,"max_depth":max(depth.values(),default=0)}\n\n\ndef apply_world_topology(rooms: dict) -> dict:\n    if not isinstance(rooms,dict): raise TypeError("rooms must be a dict")\n    _normalize_cross_zone_edges(rooms)\n    groups=_zone_groups(rooms)\n    zones={}; errors=[]\n    for zone,ids in sorted(groups.items()):\n        try: zones[zone]=_generate_zone(rooms,zone,ids)\n        except Exception as exc: errors.append(f"{zone}: {exc}")\n    # Validate all references and reciprocal generated internal cardinal edges.\n    for rid,room in rooms.items():\n        zone=str(room.get("zone") or "Bez strefy")\n        for d,target in room.get("exits",{}).items():\n            if target not in rooms:\n                # Runtime/infinite/profession dungeon entrances intentionally point\n                # at rooms materialized on demand. Keep the semantic portal.\n                continue\n            if room.get("topology_generated_v0281") and rooms[target].get("topology_generated_v0281") and rooms[target].get("zone")==zone and d in HORIZONTAL:\n                rev=OPPOSITE[d]\n                if rooms[target].get("exits",{}).get(rev)!=rid:\n                    errors.append(f"non-reciprocal {rid}.{d}->{target}")\n    # Global reachability from default spawn; preserves the original cross-zone graph.\n    if "square" in rooms:\n        seen={"square"}; q=deque(["square"])\n        while q:\n            cur=q.popleft()\n            for target in rooms[cur].get("exits",{}).values():\n                if target in rooms and target not in seen:\n                    seen.add(target); q.append(target)\n        missing=set(rooms)-seen\n    else:\n        seen=set(); missing=set(rooms)\n    city=[rid for rid,r in rooms.items() if r.get("zone")=="Miasto Dusz"]\n    city_links=sum(1 for rid in city for t in rooms[rid].get("exits",{}).values() if t in city)//2\n    return {\n        "version":GENERATOR_VERSION,"seed":WORLD_TOPOLOGY_SEED,"zone_count":len(zones),\n        "generated_room_count":sum(v.get("rooms",0) for v in zones.values()),\n        "city_room_count":len(city),"city_internal_links":city_links,\n        "static_reachable_from_square":len(seen),"static_unreachable_without_runtime":len(missing),\n        "zones":zones,"error_count":len(errors),"errors":errors,\n    }\n'
world_topology_generator_v0281 = _load_embedded_runtime_module('world_topology_generator', _EMBEDDED_WORLD_TOPOLOGY_GENERATOR_SOURCE)

_EMBEDDED_DYNAMIC_WORLD_V029_SOURCE = '"""Soulbound v0.29.0 - Dynamic World Events + Boss/Nemesis Generator.\n\nThis module contains deterministic content-generation rules only. Numeric combat\nbalance is delegated to Generator Core through runtime_mob_balance().\n"""\nfrom __future__ import annotations\n\nimport copy\nimport hashlib\nimport random\nimport time\n\nEVENT_ROTATION_SECONDS = 60 * 60\nEVENT_COUNT = 5\nEVENT_KINDS = (\n    ("incursion", "Najazd", "elite", 3),\n    ("rare_pack", "Polowanie na rzadkie bestie", "rare", 2),\n    ("mini_hunt", "Łowy na czempiona", "mini", 1),\n    ("boss_manifestation", "Manifestacja Bossa", "world_boss", 1),\n    ("roaming_elites", "Wędrująca elita", "elite", 2),\n)\n\nBOSS_MECHANICS = (\n    ("blood_drain", "Drenaż życia co kilka kontrataków."),\n    ("ash_curse", "Magiczne przekleństwo częściowo omija obronę."),\n    ("catacomb_echo", "Co kilka kontrataków wyzwala bardzo silne echo."),\n    ("spectral_shift", "Naprzemiennie zmienia typ obrażeń fizyczne/magiczne."),\n    ("necro_regen", "Okresowo odzyskuje część maksymalnego HP."),\n    ("black_flame", "Okresowo używa silnego magicznego płomienia."),\n    ("stellar_storm", "Okresowo wyzwala silną magiczną burzę."),\n    ("giant_crush", "Okresowo wykonuje ciężkie fizyczne miażdżenie."),\n)\n\nELITE_AFFIXES = (\n    ("armored", "Opancerzony: okresowo redukuje otrzymywane obrażenia."),\n    ("vampiric", "Wampiryczny: część zadanych obrażeń leczy przeciwnika."),\n    ("regenerating", "Regenerujący: okresowo odzyskuje HP."),\n    ("ice", "Lodowy: kontrataki zyskują magiczny charakter i większą moc."),\n    ("fire", "Ognisty: kontrataki zyskują magiczny charakter i większą moc."),\n)\n\nEPITHETS = (\n    "Nieugięty", "Pożeracz Dusz", "Zwiastun Końca", "Krwawy", "Astralny",\n    "Bezsenna Groza", "Łamacz Kości", "Władca Popiołu", "Wieczny Łowca",\n    "Pogromca Wędrowców", "Czarny Strażnik", "Ten, Który Powraca",\n)\n\n\ndef _hash_int(seed: str, *parts) -> int:\n    text = ":".join(str(x) for x in (seed,) + parts)\n    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)\n\n\ndef event_slot(now=None) -> int:\n    now = time.time() if now is None else float(now)\n    return int(now // EVENT_ROTATION_SECONDS)\n\n\ndef _eligible_rooms(rooms: dict, mob_spawns, mob_templates: dict):\n    by_room = {}\n    for room_id, template_id in mob_spawns:\n        room = rooms.get(str(room_id))\n        template = mob_templates.get(str(template_id))\n        if not isinstance(room, dict) or not isinstance(template, dict):\n            continue\n        # Safe hubs / utility-only rooms are excluded implicitly by requiring a real hostile spawn.\n        if template.get("auto_aggro") is True:\n            # Still valid; world policy will force generated variants to passive.\n            pass\n        stage = max(1, min(600, int(room.get("generator_level", room.get("recommended_mastery", 1)) or 1)))\n        by_room.setdefault(str(room_id), {"stage": stage, "templates": []})["templates"].append(str(template_id))\n    return [(rid, meta) for rid, meta in by_room.items() if meta["templates"]]\n\n\ndef active_events(rooms: dict, mob_spawns, mob_templates: dict, world_seed: str, now=None):\n    now = time.time() if now is None else float(now)\n    slot = event_slot(now)\n    eligible = _eligible_rooms(rooms, mob_spawns, mob_templates)\n    if not eligible:\n        return tuple()\n    result = []\n    used = set()\n    for index in range(EVENT_COUNT):\n        kind, title, rank, count = EVENT_KINDS[index % len(EVENT_KINDS)]\n        rng = random.Random(_hash_int(world_seed, "v029-event", slot, index, kind))\n        choices = [row for row in eligible if row[0] not in used] or eligible\n        room_id, meta = choices[rng.randrange(len(choices))]\n        used.add(room_id)\n        bases = tuple(meta["templates"])\n        result.append({\n            "type": kind,\n            "title": title,\n            "rank": rank,\n            "count": count,\n            "room_id": room_id,\n            "stage": int(meta["stage"]),\n            "base_templates": bases,\n            "slot": slot,\n            "token": f"{slot}:{kind}:{room_id}",\n            "expires_at": (slot + 1) * EVENT_ROTATION_SECONDS,\n        })\n    return tuple(result)\n\n\ndef _rank_stage(stage: int, rank: str) -> int:\n    offsets = {"normal": 0, "elite": 4, "rare": 8, "mini": 14, "boss": 20, "world_boss": 26}\n    return max(1, min(600, int(stage) + offsets.get(str(rank), 0)))\n\n\ndef generated_name(base_name: str, seed: str, role: str = "event") -> str:\n    epithet = EPITHETS[_hash_int(seed, role, base_name) % len(EPITHETS)]\n    if role == "nemesis":\n        return f"{base_name}, {epithet} — NEMESIS"\n    if role == "boss":\n        return f"{base_name}, {epithet}"\n    return f"{epithet} {base_name}"\n\n\ndef build_event_template(event: dict, index: int, mob_templates: dict, generator_core, world_seed: str):\n    bases = tuple(event.get("base_templates") or ())\n    if not bases:\n        return None, None\n    pick = _hash_int(world_seed, event["token"], index, "base") % len(bases)\n    base_id = bases[pick]\n    base = mob_templates.get(base_id)\n    if not isinstance(base, dict):\n        return None, None\n    rank = str(event.get("rank") or "normal")\n    stage = _rank_stage(int(event.get("stage", 1) or 1), rank)\n    template_id = f"v029_event_{event[\'slot\']}_{event[\'type\']}_{index}_{hashlib.sha1(base_id.encode()).hexdigest()[:8]}"\n    if template_id in mob_templates:\n        return template_id, mob_templates[template_id]\n    data = copy.deepcopy(base)\n    data["base_template"] = base_id\n    data["v029_dynamic_event"] = True\n    data["v029_event_token"] = event["token"]\n    data["generator_level"] = stage\n    data["auto_aggro"] = False\n    data["stationary_mob"] = rank in ("mini", "boss", "world_boss")\n    if rank == "elite":\n        data["name"] = generated_name(str(base.get("name", base_id)), event["token"] + str(index), "elite")\n        affix, text = ELITE_AFFIXES[_hash_int(world_seed, event["token"], index, "affix") % len(ELITE_AFFIXES)]\n        data["elite_affix"] = affix\n        data["elite_affix_text"] = text\n    elif rank == "rare":\n        data["name"] = generated_name(str(base.get("name", base_id)), event["token"] + str(index), "rare")\n        data["rare_mob"] = True\n    else:\n        data["name"] = generated_name(str(base.get("name", base_id)), event["token"] + str(index), "boss")\n        if rank == "mini":\n            data["mini_boss"] = True\n            affix, text = ELITE_AFFIXES[_hash_int(world_seed, event["token"], index, "mini-affix") % len(ELITE_AFFIXES)]\n            data["elite_affix"] = affix\n            data["elite_affix_text"] = "Czempion: " + text\n        else:\n            mechanic, text = BOSS_MECHANICS[_hash_int(world_seed, event["token"], index, "mechanic") % len(BOSS_MECHANICS)]\n            data["boss_mechanic"] = mechanic\n            data["boss_mechanic_text"] = "Proceduralny boss v0.29. " + text + " Fazy 75/50/25%."\n            if rank == "world_boss":\n                data["world_boss"] = True\n                data["v029_world_boss"] = True\n    generator_core.runtime_mob_balance(template_id, data, stage, rank=rank)\n    mob_templates[template_id] = data\n    return template_id, data\n\n\ndef nemesis_name(base_name: str, account_id: int, player_name: str, rank: int) -> str:\n    seed = f"nemesis:{account_id}:{player_name}:{rank}:{base_name}"\n    return generated_name(base_name, seed, "nemesis")\n\n\ndef build_nemesis_template(record, mob_templates: dict, generator_core):\n    base_id = str(record["base_template_id"])\n    base = mob_templates.get(base_id)\n    if not isinstance(base, dict):\n        return None, None\n    rank_no = max(1, int(record["rank"]))\n    if rank_no >= 7:\n        rank = "world_boss"\n    elif rank_no >= 4:\n        rank = "boss"\n    elif rank_no >= 2:\n        rank = "mini"\n    else:\n        rank = "rare"\n    stage = max(1, min(600, int(record["level"])))\n    template_id = f"v029_nemesis_{int(record[\'account_id\'])}_{rank_no}_{hashlib.sha1(base_id.encode()).hexdigest()[:8]}"\n    if template_id in mob_templates:\n        return template_id, mob_templates[template_id]\n    data = copy.deepcopy(base)\n    data["base_template"] = base_id\n    data["name"] = str(record["nemesis_name"])\n    data["v029_nemesis"] = True\n    data["v029_nemesis_owner_account_id"] = int(record["account_id"])\n    data["v029_nemesis_rank"] = rank_no\n    data["generator_level"] = stage\n    data["auto_aggro"] = False\n    data["stationary_mob"] = True\n    if rank in ("boss", "world_boss"):\n        mechanic, text = BOSS_MECHANICS[_hash_int(str(record["account_id"]), base_id, rank_no, "nemesis-mechanic") % len(BOSS_MECHANICS)]\n        data["boss_mechanic"] = mechanic\n        data["boss_mechanic_text"] = f"Nemesis rangi {rank_no}. {text} Fazy 75/50/25%."\n        data["world_boss"] = rank == "world_boss"\n    elif rank == "mini":\n        data["mini_boss"] = True\n        affix, text = ELITE_AFFIXES[_hash_int(str(record["account_id"]), base_id, rank_no, "nemesis-affix") % len(ELITE_AFFIXES)]\n        data["elite_affix"] = affix\n        data["elite_affix_text"] = f"Nemesis rangi {rank_no}: {text}"\n    else:\n        data["rare_mob"] = True\n    generator_core.runtime_mob_balance(template_id, data, stage, rank=rank)\n    mob_templates[template_id] = data\n    return template_id, data\n'
dynamic_world_v029 = _load_embedded_runtime_module('dynamic_world_v029', _EMBEDDED_DYNAMIC_WORLD_V029_SOURCE)

_EMBEDDED_WORLD_LOGIC_VALIDATOR_SOURCE = '"""Soulbound v0.30.0 Semantic World Logic Validator.\n\nThe topology may be procedural, but geography must remain understandable.\nThis validator checks semantic gateway rules, vertical movement semantics,\nworld reachability, reciprocal navigation and deterministic topology output.\n"""\nfrom __future__ import annotations\n\nfrom collections import defaultdict, deque\nimport hashlib\nimport json\n\nVERSION = "0.30.0"\nHORIZONTAL = ("north","east","south","west","northeast","southeast","southwest","northwest")\nOPPOSITE = {\n    "north":"south","south":"north","east":"west","west":"east",\n    "northeast":"southwest","southwest":"northeast",\n    "northwest":"southeast","southeast":"northwest",\n    "up":"down","down":"up",\n}\n\n\ndef _norm(text):\n    return str(text or "").casefold()\n\n\ndef zone_family(zone: str) -> str:\n    z=_norm(zone)\n    if any(k in z for k in ("miasto dusz","gildia dusz","pracownia kartografa")):\n        return "urban"\n    if any(k in z for k in ("przedmieścia","przedmiescia","wioska","osada","posterunek","obóz straży","oboz strazy","przystań","przystan")):\n        return "settlement"\n    if any(k in z for k in ("kanały","kanaly","podziemia","krypt","jaskini","jaskinie","nekropolia","katakumb","kopal")):\n        return "underground"\n    if any(k in z for k in ("góry","gory","lodowe","twierdza gigant")):\n        return "highland"\n    if any(k in z for k in ("popielne","rozbite niebo","pustki","korona świata","korona swiata","rubież końca","rubiez konca")):\n        return "endgame"\n    if any(k in z for k in ("próba","proba","arena","archiwum otchłani","archiwum otchlani","katedra tysiąca","katedra tysiaca","kuźnia pierwszych","kuznia pierwszych","labirynt wiecznych","pałac bezimiennej","palac bezimiennej")):\n        return "instance"\n    if "proceduralny region:" in z:\n        return "expedition"\n    if any(k in z for k in ("ocean","wybrzeże","wybrzeze","jezior","dolina rzek")):\n        return "waterland"\n    return "wilderness"\n\n\ndef _gateway_semantic(rid: str, room: dict, direction: str, target_id: str, target: dict) -> bool:\n    """True when a cross-zone edge has a believable semantic transition."""\n    if direction in ("up","down"):\n        return True\n    src=_norm(rid)+" "+_norm(room.get("name"))\n    dst=_norm(target_id)+" "+_norm(target.get("name"))\n    gateway_words=(\n        "gate","brama","harbor","port","pier","molo","road","trakt","path","szlak",\n        "pass","przełęcz","przelecz","bridge","most","entrance","wejście","wejscie",\n        "mouth","wylot","frontier","rubież","rubiez","gateway","portal","archive","archiw",\n        "hall","hala","lobby","warsztat kartograf","cartographer","watchpost","posterunek",\n        "camp","obóz","oboz","v0130_gateway","v028_region_gate",\n    )\n    return any(k in src or k in dst for k in gateway_words)\n\n\ndef _reachable(rooms, start):\n    if start not in rooms:\n        return set()\n    seen={start}; q=deque([start])\n    while q:\n        cur=q.popleft()\n        for target in rooms[cur].get("exits",{}).values():\n            if target in rooms and target not in seen:\n                seen.add(target); q.append(target)\n    return seen\n\n\ndef topology_fingerprint(rooms):\n    payload=[]\n    for rid in sorted(rooms):\n        exits=rooms[rid].get("exits",{}) or {}\n        payload.append((rid,tuple(sorted((str(k),str(v)) for k,v in exits.items()))))\n    raw=json.dumps(payload,ensure_ascii=False,separators=(",",":"))\n    return hashlib.sha256(raw.encode("utf-8")).hexdigest()\n\n\ndef validate_world_logic(rooms: dict) -> dict:\n    errors=[]; warnings=[]; cross=[]; vertical=[]\n    if not isinstance(rooms,dict):\n        return {"version":VERSION,"error_count":1,"errors":["ROOMS is not dict"]}\n\n    # References and reciprocal navigation for every static edge.\n    for rid,room in rooms.items():\n        exits=room.get("exits",{}) or {}\n        for direction,target_id in exits.items():\n            if target_id not in rooms:\n                # Runtime/lazy destination; validated by its own materializer.\n                continue\n            target=rooms[target_id]\n            if direction in OPPOSITE:\n                reverse=OPPOSITE[direction]\n                if target.get("exits",{}).get(reverse)!=rid:\n                    # Some explicit gauntlet finales remain one-way by design; require a\n                    # global return path instead of pretending the exact edge is reciprocal.\n                    if not (room.get("procedural_dynamic") or target.get("procedural_dynamic")):\n                        warnings.append(f"one-way {rid}.{direction}->{target_id}")\n            z1=str(room.get("zone") or "Bez strefy")\n            z2=str(target.get("zone") or "Bez strefy")\n            if direction in ("up","down"):\n                vertical.append((rid,direction,target_id))\n            if z1!=z2:\n                cross.append((rid,direction,target_id,z1,z2))\n                f1,f2=zone_family(z1),zone_family(z2)\n                semantic_gateway=_gateway_semantic(rid,room,direction,target_id,target)\n                # Granice naturalnych biomów (np. łąka -> rzeka -> dzicz) mogą\n                # przechodzić bez sztucznej bramy. Twarda semantyczna brama jest\n                # wymagana, gdy opuszczamy/wchodzimy do huba miejskiego.\n                if (f1=="urban") != (f2=="urban") and not semantic_gateway:\n                    errors.append(f"urban boundary without semantic gateway: {rid}.{direction}->{target_id} ({z1}->{z2})")\n                # Miasto nie może być bezpośrednim sąsiadem gór/endgame. Nawet\n                # prawdziwa brama miejska ma prowadzić najpierw do traktu/przedmieść.\n                if f1=="urban" and f2 in {"highland","endgame"} and direction not in ("up","down"):\n                    errors.append(f"urban direct jump to {f2}: {rid}.{direction}->{target_id}")\n                if f2=="urban" and f1 in {"highland","endgame"} and direction not in ("up","down"):\n                    errors.append(f"{f1} direct jump to urban: {rid}.{direction}->{target_id}")\n\n    # v0.30 generator nie używa up/down jako GENERATED_DIRS. Każde pionowe\n    # przejście obecne tutaj pochodzi więc z semantycznej tożsamości świata\n    # (schody, piwnica, wieża, krypta, jaskinia, portal) albo z generatora\n    # dedykowanej instancji, a nie z losowego łączenia topologii.\n\n    reachable=_reachable(rooms,"square")\n    if len(reachable)!=len(rooms):\n        missing=sorted(set(rooms)-reachable)\n        errors.append(f"unreachable from square: {len(missing)} rooms; sample {missing[:10]}")\n\n    # Every static room must have some route back to the hub. Reverse-graph BFS.\n    rev=defaultdict(list)\n    for rid,room in rooms.items():\n        for target in room.get("exits",{}).values():\n            if target in rooms: rev[target].append(rid)\n    can_return=set()\n    if "square" in rooms:\n        can_return={"square"}; q=deque(["square"])\n        while q:\n            cur=q.popleft()\n            for source in rev.get(cur,[]):\n                if source not in can_return:\n                    can_return.add(source); q.append(source)\n    if len(can_return)!=len(rooms):\n        missing=sorted(set(rooms)-can_return)\n        errors.append(f"cannot return to square: {len(missing)} rooms; sample {missing[:10]}")\n\n    city=[rid for rid,r in rooms.items() if r.get("zone")=="Miasto Dusz"]\n    city_bad=[]\n    for rid in city:\n        for d,t in rooms[rid].get("exits",{}).items():\n            if t not in rooms: continue\n            z2=rooms[t].get("zone")\n            if z2=="Miasto Dusz": continue\n            if not _gateway_semantic(rid,rooms[rid],d,t,rooms[t]):\n                city_bad.append(f"{rid}.{d}->{t}")\n    if city_bad:\n        errors.append("city exits without gateway semantics: "+", ".join(city_bad[:10]))\n\n    families=defaultdict(int)\n    for r in rooms.values(): families[zone_family(r.get("zone"))]+=1\n    return {\n        "version":VERSION,\n        "room_count":len(rooms),\n        "reachable_from_square":len(reachable),\n        "returnable_to_square":len(can_return),\n        "cross_zone_edges":len(cross),\n        "vertical_edges":len(vertical),\n        "city_rooms":len(city),\n        "zone_family_room_counts":dict(families),\n        "topology_fingerprint":topology_fingerprint(rooms),\n        "warning_count":len(warnings),\n        "warnings":warnings,\n        "error_count":len(errors),\n        "errors":errors,\n    }\n'
world_logic_validator_v030 = _load_embedded_runtime_module('world_logic_validator', _EMBEDDED_WORLD_LOGIC_VALIDATOR_SOURCE)

VERSION = "0.38.10"
GLOBAL_SKILL_BUFF_DURATION_SECONDS = 30
HISTORY_BUFFER_LIMIT = 100
HISTORY_BUFFER_DEFAULT_SHOW = 20

# v0.30.10: cykliczny Happy Hour EXP. Każda pełna godzina zegarowa
# zaczyna 15-minutowe okno x2 EXP. Jedna funkcja jest źródłem prawdy dla
# statusu, komunikatów oraz wszystkich kanałów progresji.
DOUBLE_XP_EVENT_INTERVAL_SECONDS = 60 * 60
DOUBLE_XP_EVENT_DURATION_SECONDS = 15 * 60
DOUBLE_XP_EVENT_MULTIPLIER = 2

def double_xp_event_state(now=None):
    now = time.time() if now is None else float(now)
    elapsed = now % DOUBLE_XP_EVENT_INTERVAL_SECONDS
    active = elapsed < DOUBLE_XP_EVENT_DURATION_SECONDS
    if active:
        remaining = max(0, int(math.ceil(DOUBLE_XP_EVENT_DURATION_SECONDS - elapsed)))
        next_start = max(0, int(math.ceil(DOUBLE_XP_EVENT_INTERVAL_SECONDS - elapsed)))
    else:
        remaining = 0
        next_start = max(0, int(math.ceil(DOUBLE_XP_EVENT_INTERVAL_SECONDS - elapsed)))
    return {
        "active": active,
        "multiplier": DOUBLE_XP_EVENT_MULTIPLIER if active else 1,
        "remaining_seconds": remaining,
        "next_start_seconds": next_start,
        "duration_seconds": DOUBLE_XP_EVENT_DURATION_SECONDS,
    }

# v0.8.72: właścicielskie komendy administracyjne. Nazwy kont podaje się
# po stronie serwera, np. SOULBOUND_ADMIN_ACCOUNTS=Patryk. Nigdy nie są
# przyznawane na podstawie nazwy postaci.
ADMIN_ACCOUNT_NAMES = {
    name.strip().casefold()
    for name in os.environ.get("SOULBOUND_ADMIN_ACCOUNTS", "").split(",")
    if name.strip()
}
MAX_CHARACTERS_PER_ACCOUNT = 14

HOST = os.getenv("SOULBOUND_HOST", "0.0.0.0")
_RAILWAY_TCP_PORT = os.getenv("RAILWAY_TCP_APPLICATION_PORT", "").strip()
_SOULBOUND_PORT = os.getenv("SOULBOUND_PORT", "").strip()
_GENERIC_PORT = os.getenv("PORT", "").strip()

def _valid_port(raw, fallback=None):
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return fallback
    return value if 1 <= value <= 65535 else fallback

# Railway raw-TCP proxy has the strongest signal when configured. Otherwise
# Railway's injected PORT must win over any legacy Soulbound override.
if _RAILWAY_TCP_PORT:
    PORT = _valid_port(_RAILWAY_TCP_PORT, 4000)
    PORT_SOURCE = "RAILWAY_TCP_APPLICATION_PORT"
elif _GENERIC_PORT:
    PORT = _valid_port(_GENERIC_PORT, 4000)
    PORT_SOURCE = "PORT"
elif _SOULBOUND_PORT:
    PORT = _valid_port(_SOULBOUND_PORT, 4000)
    PORT_SOURCE = "SOULBOUND_PORT"
else:
    PORT = 4000
    PORT_SOURCE = "default"

_VOLUME_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
_DEFAULT_DB = os.path.join(_VOLUME_PATH, "soulbound.db") if _VOLUME_PATH else "soulbound.db"
DB_PATH = os.getenv("SOULBOUND_DB", _DEFAULT_DB)

# ============================================================
# v0.25.2 - ORE ATLAS THRESHOLD HOTFIX
# Atlas podstawowych rud pokazuje dokładnie te same minimalne progi Kilofa i piętra,
# których używa realna logika Kopalni Głębinowej: Żelazo 10/10, Srebro 25/25, Złoto 50/50.

# v0.25.1 - UNIFIED DEEP MINE
# Wszystkie normalne rudy/minerały, geody i klejnoty pochodzą z jednej
# Kopalni Głębinowej. Dawne źródła terenowe i Kopalnia Kryształów nie są
# już aktywnymi miejscami Górnictwa.
#
# v0.25.0 - GLOBAL GENERATOR 2.0
# Jeden trwały seed serwera dla nowych warstw proceduralnych. Nie zmieniamy
# historycznych seedów v0.11-v0.21, dzięki czemu istniejące mapy i save'y
# zachowują dawny układ. Seed v0.25 steruje nowymi profilami świata,
# hotspotami profesji, geologią Kopalni oraz opisami proceduralnych pięter.
# ============================================================
def _v0250_world_seed_path():
    override = os.getenv("SOULBOUND_WORLD_SEED_FILE", "").strip()
    if override:
        return override
    base_dir = os.path.dirname(os.path.abspath(DB_PATH)) or "."
    return os.path.join(base_dir, "soulbound_world_seed.txt")


def _v0250_load_or_create_world_seed():
    explicit = os.getenv("SOULBOUND_WORLD_SEED", "").strip()
    if explicit:
        return explicit
    path = _v0250_world_seed_path()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = handle.read().strip()
            if value:
                return value
    except OSError:
        pass
    value = secrets.token_hex(24)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(value + "\n")
        os.replace(tmp, path)
    except OSError:
        # Read-only deployment: seed remains stable for the lifetime of process.
        pass
    return value


V0250_WORLD_SEED = _v0250_load_or_create_world_seed()
V0250_WORLD_SEED_ID = hashlib.sha256(V0250_WORLD_SEED.encode("utf-8")).hexdigest()[:12]
V0250_HOTSPOT_SECONDS = 60 * 60


def v0250_seed_int(*parts):
    payload = ":".join(str(part) for part in (V0250_WORLD_SEED,) + parts)
    return int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16], 16)


def v0250_rng(*parts):
    return random.Random(v0250_seed_int(*parts))


V0250_WORLD_AMBIENCE = (
    "spokojne echo terenu", "ślady niedawnej wędrówki", "zmienny wiatr",
    "stare ślady na ziemi", "nietypowa cisza", "odległe odgłosy świata",
    "świeże tropy", "lekka mgła", "wyraźny zapach roślin", "suchy pył w powietrzu",
)
V0250_WORLD_FEATURES = (
    "stary kamienny znak", "wąskie boczne przejście", "naturalna nisza",
    "porzucone ognisko", "ślady dawnego obozu", "niewielkie rumowisko",
    "wyróżniająca się formacja terenu", "stara ścieżka", "ukryty zakątek",
    "miejsce osłonięte od wiatru",
)
V0250_CITY_AMBIENCE = (
    "ruch mieszkańców", "dźwięk pracy rzemieślników", "przechodzący patrol",
    "gwar rozmów", "odgłos wozów", "spokojny ruch kupców",
)
V0250_GATHER_HOTSPOT_LABELS = {
    "fishing": ("Ławica", "Żerowisko", "Dobry prąd"),
    "mining": ("Bogata żyła", "Świeże odsłonięcie", "Gęsta mineralizacja"),
    "woodcutting": ("Gęsty drzewostan", "Dobre drewno", "Stary zagajnik"),
    "herbalism": ("Rozkwit ziół", "Żyzna gleba", "Skupisko roślin"),
}


def v0250_room_generator_profile(room_id):
    room = globals().get("ROOMS", {}).get(str(room_id), {})
    zone = str(room.get("zone", "Nieznana strefa"))
    rng = v0250_rng("room-profile", room_id, zone)
    city = "miasto" in zone.casefold() or "świątynia" in zone.casefold()
    ambience_pool = V0250_CITY_AMBIENCE if city else V0250_WORLD_AMBIENCE
    return {
        "seed_id": V0250_WORLD_SEED_ID,
        "ambience": rng.choice(ambience_pool),
        "feature": rng.choice(V0250_WORLD_FEATURES),
        "variant": 1 + rng.randrange(9999),
        "city": city,
    }


def v0250_gather_hotspot(room_id, tool_type=None, now=None):
    tool = str(tool_type or "").strip().casefold()
    labels = V0250_GATHER_HOTSPOT_LABELS.get(tool)
    if not labels:
        return {"label":"", "quantity_bonus":0, "xp_mult":1.0, "slot":0}
    room = globals().get("ROOMS", {}).get(str(room_id), {})
    zone = str(room.get("zone", ""))
    slot = int((time.time() if now is None else float(now)) // V0250_HOTSPOT_SECONDS)
    roll = v0250_seed_int("hotspot", slot, zone, tool)
    # Około 1/4 stref profesyjnych ma aktywny bonus w danej godzinie.
    if roll % 4 != 0:
        return {"label":"", "quantity_bonus":0, "xp_mult":1.0, "slot":slot}
    label = labels[(roll // 4) % len(labels)]
    return {
        "label": f"Global Generator: {label}",
        "quantity_bonus": 0,
        "xp_mult": 1.05,
        "slot": slot,
    }


def v0250_mine_floor_profile(floor):
    floor = max(1, int(floor))
    rng = v0250_rng("deep-mine-profile", floor)
    strata = (
        "granitowa warstwa", "ciemny bazalt", "łupek z metalicznymi żyłami",
        "kwarcowa skała", "żelazisty kamień", "kryształowa warstwa",
        "stary wulkaniczny przekop", "zbita skała głębinowa",
    )
    shapes = (
        "szeroka komora", "wąski chodnik", "pęknięta galeria", "naturalna grota",
        "stary szyb", "rozgałęziony przekop", "komora podparta filarami",
    )
    signs = (
        "ślady dawnych górników", "świeże pęknięcia skały", "drobne kryształy w ścianach",
        "stare stemple górnicze", "wilgoć spływającą po skale", "pył mineralny w powietrzu",
    )
    return {
        "strata": rng.choice(strata),
        "shape": rng.choice(shapes),
        "sign": rng.choice(signs),
        "profile_id": v0250_seed_int("mine-profile-id", floor) % 100000,
    }


def v0250_instance_floor_profile(kind, floor):
    rng = v0250_rng("instance-profile", kind, int(floor))
    motifs = (
        "echo dawnych walk", "ślady starego rytuału", "niestabilne sklepienie",
        "gęsta mgła przy ziemi", "stare runy na ścianach", "rozbite posągi",
        "zimny przeciąg", "ciemne boczne nisze", "pozostałości dawnego obozu",
    )
    layouts = (
        "liczne pętle", "dwie główne odnogi", "wąskie łączniki", "szerokie galerie",
        "krótkie ślepe odnogi", "kilka alternatywnych przejść",
    )
    return {"motif": rng.choice(motifs), "layout": rng.choice(layouts)}

MAX_CLIENTS = int(os.getenv("SOULBOUND_MAX_CLIENTS", "100"))
PBKDF2_ROUNDS = 210_000

STAT_GROWTH_THRESHOLD = 100

def stat_quality_label(value):
    """Czytelna słowna ocena statystyki bez fałszywego capu po 200."""
    value = max(0, int(value))
    if value <= 5: return "bardzo słabo"
    if value <= 9: return "słabo"
    if value <= 13: return "poniżej przeciętnej"
    if value <= 19: return "przeciętnie"
    if value <= 29: return "dobrze"
    if value <= 44: return "bardzo dobrze"
    if value <= 64: return "świetnie"
    if value <= 89: return "wybitnie"
    if value <= 119: return "mistrzowsko"
    if value <= 159: return "nadludzko"
    if value <= 199: return "legendarnie"
    if value <= 399: return "mitycznie"
    if value <= 999: return "transcendentalnie"
    if value <= 4999: return "bosko"
    if value <= 9999: return "kosmicznie"
    if value <= 19999: return "absolutnie"
    return "poza skalą"

SOUL_MAX_LEVEL = 400
SOUL_TIER_THRESHOLDS = (
    1, 10, 20, 25, 35, 45, 60, 70, 80, 90,
    100, 110, 120, 130, 140, 150, 160, 170, 180, 200,
) + tuple(range(210, 401, 10))
SOUL_MAX_TIER = 40

# Pierwsze pięć progów zachowane jako aliasy kompatybilności.
TIER2_LEVEL = SOUL_TIER_THRESHOLDS[1]
TIER3_LEVEL = SOUL_TIER_THRESHOLDS[2]
TIER4_LEVEL = SOUL_TIER_THRESHOLDS[3]
TIER5_LEVEL = SOUL_TIER_THRESHOLDS[4]

# v0.8.53: każdy awans Soul Tier od 2 do 20 wymaga jednorazowej
# Próby Broni Duszy u Kapłana Elora. Cztery stare quest_id pozostają
# bez zmian, aby istniejące save'y zachowały ukończone Próby.
SOUL_TRIAL_QUEST_IDS = {
    2: "soul_tier_02_trial",
    3: "soul_tier_03_trial",
    4: "soul_tier_2_trial",
    5: "soul_tier_05_trial",
    6: "soul_tier_06_trial",
    7: "soul_tier_3_trial",
    8: "soul_tier_08_trial",
    9: "soul_tier_09_trial",
    10: "soul_tier_10_trial",
    11: "soul_tier_11_trial",
    12: "soul_tier_12_trial",
    13: "soul_tier_4_trial",
    14: "soul_tier_14_trial",
    15: "soul_tier_15_trial",
    16: "soul_tier_16_trial",
    17: "soul_tier_17_trial",
    18: "soul_tier_18_trial",
    19: "soul_tier_5_trial",
    20: "soul_tier_20_trial",
}
SOUL_TIER_POWER_BONUSES = (
    0, 4, 8, 12, 18, 24, 30, 34, 38, 42,
    46, 50, 55, 60, 65, 70, 75, 80, 85, 100,
) + tuple(102 + i * 2 for i in range(20))
SOUL_TIER_CLASS_BONUS_PERCENT = (
    5, 7, 8, 10, 12, 13, 15, 16, 17, 18,
    19, 19, 20, 21, 22, 23, 24, 24, 25, 30,
) + tuple(30 + (i + 1) // 2 for i in range(20))
# v0.9.0: specjalizacja Łotrzyka nie może marnować progresji na hard capie
# 35% uniku. Sam Soul Weapon daje teraz maks. +5 pp uniku; pozostała część
# jego budżetu specjalizacji przechodzi w umiarkowane obrażenia fizyczne.
SOUL_TIER_DODGE_BONUS = (
    0.01, 0.01, 0.015, 0.015, 0.02, 0.02, 0.025, 0.025, 0.03, 0.03,
    0.03, 0.035, 0.035, 0.04, 0.04, 0.04, 0.045, 0.045, 0.05, 0.05,
) + (0.05,) * 20
SOUL_TIER_GUARDIAN_REDUCTION = (
    3, 4, 5, 6, 7, 8, 9, 9, 10, 10,
    11, 11, 12, 12, 13, 13, 14, 14, 15, 18,
) + tuple(18 + (i + 1) // 2 for i in range(20))

# v0.34.1: Weapon Traits per class. Każda klasa ma własny profil cech
# Broni Duszy na Soul Tierach 1-40. Cechy są pasywne i dotyczą wyłącznie
# zwykłego ataku Broni Duszy; nie są skillami ani spellami.
_SOUL_TRAIT_BASE_NAMES = (
    "Przebudzenie", "Instynkt", "Rezonans", "Krwiobieg", "Wyrok",
    "Zapłon", "Przenikliwość", "Harmonia", "Puls", "Łowy",
    "Furia", "Wizja", "Echo", "Szkarłat", "Egzekucja",
    "Transcendencja", "Gwiezdny Znak", "Podwójny Rezonans", "Tętno", "Zagłada",
    "Żar", "Pustka", "Wieczność", "Strumień", "Pieczęć",
    "Astralny Płomień", "Otchłań", "Nieskończoność", "Krew Gwiazd", "Ostateczność",
    "Przeznaczenie", "Absolut", "Kosmos", "Nieśmiertelność", "Sąd",
    "Apoteoza", "Wieczyste Oko", "Echo Absolutu", "Serce", "Korona Duszy",
)

# effect, base value. Poszczególne klasy mają inne cykle, więc ich Broń Duszy
# rozwija się inaczej nawet przy tym samym Tierze.
_SOUL_TRAIT_CLASS_PROFILES = {
    "Wojownik":   {"theme":"Przysięgi", "cycle":(("damage_percent",1.20),("crit_damage_percent",3.0),("lifesteal_percent",0.35),("crit_chance",0.004),("execute_damage_percent",1.2))},
    "Berserker":  {"theme":"Krwi", "cycle":(("damage_percent",1.45),("lifesteal_percent",0.55),("crit_damage_percent",3.5),("execute_damage_percent",1.8),("damage_percent",0.85))},
    "Łotrzyk":    {"theme":"Cienia", "cycle":(("crit_chance",0.006),("crit_damage_percent",3.4),("execute_damage_percent",1.8),("damage_percent",0.85),("lifesteal_percent",0.30))},
    "Łowca":      {"theme":"Tropu", "cycle":(("crit_chance",0.005),("damage_percent",1.05),("execute_damage_percent",1.6),("crit_damage_percent",3.0),("boss_damage_percent",1.2))},
    "Mnich":      {"theme":"Ducha", "cycle":(("damage_percent",0.95),("lifesteal_percent",0.45),("crit_chance",0.004),("mana_restore_percent",0.40),("crit_damage_percent",2.6))},
    "Strażnik":   {"theme":"Bastionu", "cycle":(("lifesteal_percent",0.55),("boss_damage_percent",1.0),("damage_percent",0.85),("crit_damage_percent",2.3),("execute_damage_percent",1.0))},
    "Mag":        {"theme":"Arkanów", "cycle":(("mana_restore_percent",0.65),("damage_percent",1.0),("crit_damage_percent",3.1),("crit_chance",0.004),("boss_damage_percent",1.1))},
    "Nekromanta": {"theme":"Żniwa", "cycle":(("lifesteal_percent",0.70),("execute_damage_percent",1.7),("damage_percent",0.95),("mana_restore_percent",0.40),("crit_damage_percent",2.6))},
    "Kapłan":     {"theme":"Światła", "cycle":(("lifesteal_percent",0.55),("mana_restore_percent",0.55),("damage_percent",0.85),("boss_damage_percent",1.0),("crit_chance",0.0035))},
    "Czarownik":  {"theme":"Otchłani", "cycle":(("damage_percent",1.15),("crit_damage_percent",3.2),("mana_restore_percent",0.50),("execute_damage_percent",1.5),("crit_chance",0.004))},
    "Druid":      {"theme":"Dziczy", "cycle":(("lifesteal_percent",0.55),("damage_percent",0.90),("mana_restore_percent",0.50),("boss_damage_percent",1.0),("execute_damage_percent",1.2))},
    "Psionik":    {"theme":"Umysłu", "cycle":(("crit_chance",0.0045),("mana_restore_percent",0.60),("crit_damage_percent",3.0),("damage_percent",0.95),("execute_damage_percent",1.3))},
    "Mec":        {"theme":"Rdzenia", "cycle":(("boss_damage_percent",1.35),("damage_percent",1.10),("crit_damage_percent",2.7),("lifesteal_percent",0.35),("execute_damage_percent",1.2))},
    "Inżynier":   {"theme":"Omni-Narzędzia", "cycle":(("crit_chance",0.0045),("boss_damage_percent",1.25),("damage_percent",1.0),("mana_restore_percent",0.45),("crit_damage_percent",2.8))},
}

_SOUL_TRAIT_EFFECT_DESCRIPTIONS = {
    "damage_percent": lambda v: f"+{v:g} procent obrażeń zwykłego ataku Broni Duszy",
    "crit_chance": lambda v: f"+{v*100:g} punktu procentowego szansy na krytyk zwykłego ataku Broni Duszy",
    "crit_damage_percent": lambda v: f"+{v:g} procent obrażeń krytycznych zwykłego ataku Broni Duszy",
    "lifesteal_percent": lambda v: f"leczy za {v:g} procent obrażeń zadanych zwykłym atakiem Broni Duszy",
    "execute_damage_percent": lambda v: f"+{v:g} procent obrażeń zwykłego ataku przeciw celom z 35 procent HP lub mniej",
    "mana_restore_percent": lambda v: f"odzyskuje Manę równą {v:g} procent obrażeń zwykłego ataku Broni Duszy",
    "boss_damage_percent": lambda v: f"+{v:g} procent obrażeń zwykłego ataku przeciw bossom",
}

SOUL_TIER_TRAITS_BY_CLASS = {}
for _class_name, _profile in _SOUL_TRAIT_CLASS_PROFILES.items():
    _rows = {}
    _cycle = _profile["cycle"]
    for _tier, _base_name in enumerate(_SOUL_TRAIT_BASE_NAMES, start=1):
        _effect, _value = _cycle[(_tier - 1) % len(_cycle)]
        _name = f"{_base_name} {_profile['theme']}"
        _rows[_tier] = {
            "name": _name,
            "effect": _effect,
            "value": float(_value),
            "description": _SOUL_TRAIT_EFFECT_DESCRIPTIONS[_effect](float(_value)),
        }
    SOUL_TIER_TRAITS_BY_CLASS[_class_name] = _rows

def soul_weapon_trait_for_tier(tier, class_name=None):
    tier = max(1, min(SOUL_MAX_TIER, int(tier)))
    class_name = class_name or "Wojownik"
    rows = SOUL_TIER_TRAITS_BY_CLASS.get(class_name) or SOUL_TIER_TRAITS_BY_CLASS["Wojownik"]
    return rows.get(tier)

def soul_weapon_trait_totals(tier, class_name=None):
    tier = max(1, min(SOUL_MAX_TIER, int(tier)))
    class_name = class_name or "Wojownik"
    rows = SOUL_TIER_TRAITS_BY_CLASS.get(class_name) or SOUL_TIER_TRAITS_BY_CLASS["Wojownik"]
    totals = {
        "damage_percent": 0.0, "crit_chance": 0.0, "crit_damage_percent": 0.0,
        "lifesteal_percent": 0.0, "execute_damage_percent": 0.0,
        "mana_restore_percent": 0.0, "boss_damage_percent": 0.0,
    }
    for _t in range(1, tier + 1):
        row = rows[_t]
        totals[row["effect"]] += float(row["value"])
    return totals

SOUL_MILESTONE_TIERS = (5, 10, 15, 20)
SOUL_MILESTONE_NAMES = {
    5: "Przebudzenie Broni Duszy",
    10: "Wzmocnienie Broni Duszy",
    15: "Transcendencja Broni Duszy",
    20: "Apoteoza Broni Duszy",
}
SOUL_MILESTONE_SPECIALIZATION_BONUS = {5: 2, 10: 4, 15: 7, 20: 10}
SOUL_MILESTONE_DODGE_BONUS = {5: 0.0, 10: 0.0, 15: 0.0, 20: 0.0}
SOUL_MILESTONE_GUARDIAN_REDUCTION = {5: 2, 10: 4, 15: 6, 20: 8}
# Tiery 21-40 mają dalszą moc bazową, ale nie dodają nowych globalnych
# milestone buffów; dzięki temu zakres 201-400 nie podwaja buildów klasowych.
SOUL_TRIAL_QUEST_IDS.update({
    tier: f"soul_tier_{tier:02d}_trial" for tier in range(21, 41)
})

# v0.26.1: Próby Broni Duszy mają czytelne pasma trudności.
# Początek nie wymaga już bossów Krypty o dziesiątkach tysięcy HP.
def soul_trial_difficulty_band(tier):
    tier = int(tier)
    if tier <= 4:
        return "Początkująca"
    if tier <= 7:
        return "Poszukiwacza"
    if tier <= 12:
        return "Weterana"
    if tier <= 20:
        return "Mistrzowska"
    if tier <= 30:
        return "Endgame"
    return "Ekstremalna"
REGULAR_MOB_RESPAWN_SECONDS = 120
BOSS_RESPAWN_SECONDS = 300
TRAINING_DUMMY_RESPAWN_SECONDS = 60
GLOBAL_MOB_RESPAWN_MULTIPLIER = 2.0
CORPSE_LIFETIME_SECONDS = 600
GLOBAL_MOB_HP_MULTIPLIER = 2.0
QUEST_REPEAT_COOLDOWN_SECONDS = 60 * 60
BLACKSMITH_QUEST_COOLDOWN_SECONDS = 60 * 60

# Ekonomia v0.8.60: jedno wspólne saldo z trzema nominałami.
# Wewnętrznie saldo jest przechowywane jako łączna liczba srebra.
# 100 srebra = 1 złoto.
# 1 000 000 złota = 1 mithril.
# Zatem 1 mithril = 100 000 000 srebra.
SILVER_PER_GOLD = 100
GOLD_PER_MITHRIL = 1_000_000
SILVER_PER_MITHRIL = SILVER_PER_GOLD * GOLD_PER_MITHRIL
COINS_PER_OLD_GOLD = SILVER_PER_GOLD
COINS_PER_OLD_MITHRIL = SILVER_PER_MITHRIL
# v0.19: ekonomia startuje mało i czytelnie. Globalny generator rośnie dopiero
# wraz z postępem; nowa postać nadal zaczyna dokładnie z 2 zł i 30 srebra.
STARTING_SILVER = 30
STARTING_GOLD = 2
STARTING_MITHRIL = 0
CURRENCY_SQLITE_SAFE_TOTAL = 8_000_000_000_000_000_000

def legacy_currency_to_coins(silver=0, gold=0, mithril=0):
    """Zwraca jedno wspólne saldo w najmniejszym nominale: srebrze."""
    return (
        max(0, int(silver))
        + max(0, int(gold)) * SILVER_PER_GOLD
        + max(0, int(mithril)) * SILVER_PER_MITHRIL
    )

def normalize_currency_values(silver, gold, mithril):
    """Normalizuje trzy nominały do jednego salda przechowywanego w silver."""
    total = legacy_currency_to_coins(silver, gold, mithril)
    # SQLite INTEGER jest 64-bitowy. Pozwalamy na gospodarkę w bilionach i
    # wyżej, ale chronimy zapis przed przepełnieniem przy ekstremalnym endgame.
    total = min(CURRENCY_SQLITE_SAFE_TOTAL, max(0, int(total)))
    return total, 0, 0

def currency_denominations(total_silver):
    """Rozkłada wspólne saldo na mithril, złoto i srebro tylko do prezentacji."""
    total_silver = max(0, int(total_silver))
    mithril, remainder = divmod(total_silver, SILVER_PER_MITHRIL)
    gold, silver = divmod(remainder, SILVER_PER_GOLD)
    return mithril, gold, silver

def currency_unit_multiplier(raw):
    """Mnożnik nominału dla komend. Wszystkie trafiają do jednego salda."""
    value = normalize_lookup_text(raw) if 'normalize_lookup_text' in globals() else str(raw or '').strip().lower()
    if value in ('silver','srebro','srebra','srebrnych','s'):
        return 1
    if value in ('gold','zloto','złoto','zlota','złota','g','zl','zł'):
        return SILVER_PER_GOLD
    if value in ('mithril','mithrilu','m'):
        return SILVER_PER_MITHRIL
    if value in ('moneta','monety','monet','coin','coins'):
        return 1
    return None

def currency_reading_text(silver=0, gold=0, mithril=0, *, full_names=False, include_zero=False):
    """Czytelny dla NVDA zapis jednego salda w nominałach mithril/złoto/srebro."""
    total = legacy_currency_to_coins(silver, gold, mithril)
    mithril_count, gold_count, silver_count = currency_denominations(total)
    parts = []
    if mithril_count or include_zero:
        parts.append(f"{mithril_count} mithril")
    if gold_count or include_zero:
        parts.append(f"{gold_count} złota")
    if silver_count or include_zero or not parts:
        parts.append(f"{silver_count} srebra")
    return ", ".join(parts)


PROFESSION_MAX_LEVEL = 400
BLACKSMITHING_MAX_LEVEL = 400
JEWELCRAFTING_MAX_LEVEL = 400

# v0.8.66: wszystkie umiejętności profesyjne rozwijają się 1-200.
# Poziom PROFESJI odpowiada za tempo pracy i wymagania receptur/zleceń.
# Poziom NARZĘDZIA nie skraca czasu: odblokowuje lepsze surowce oraz
# zwiększa jakość/rare roll i szansę dodatkowego urobku/produktu.
PROFESSION_XP_GAIN_MULTIPLIER = 2
PROFESSION_XP_REQUIREMENT_MULTIPLIER = 1

CHARISMA_DISCOUNT_STEP = 4
CHARISMA_MAX_DISCOUNT = 25
PARTY_BASE_CAPACITY = 8
PARTY_CHARISMA_STEP = 25
PARTY_AUTO_HEAL_THRESHOLD = 0.85

PROFESSION_RANK_THRESHOLDS = (
    1, 15, 30, 45, 60, 75, 90,
    100, 120, 140, 160, 180, 200,
) + tuple(range(220, 401, 20))
PROFESSION_MAX_RANK = len(PROFESSION_RANK_THRESHOLDS)
BLACKSMITHING_MAX_RANK = PROFESSION_MAX_RANK
BLACKSMITHING_RANK_THRESHOLDS = PROFESSION_RANK_THRESHOLDS

PROFESSION_RANK_NAMES = {
    "Wędkarstwo": (
        "Uczeń Wędkarstwa", "Adept Wędkarstwa", "Czeladnik Wędkarstwa",
        "Specjalista Wędkarstwa", "Ekspert Wędkarstwa", "Mistrz Wędkarstwa",
        "Arcymistrz Wędkarstwa", "Legenda Wędkarstwa", "Runiczny Wędkarz",
        "Wędkarz Smoczych Głębin", "Astralny Wędkarz", "Wędkarz Pustki",
        "Wieczny Mistrz Wędkarstwa",
    ),
    "Górnictwo": (
        "Uczeń Górnictwa", "Adept Górnictwa", "Czeladnik Górnictwa",
        "Specjalista Górnictwa", "Ekspert Górnictwa", "Mistrz Górnictwa",
        "Arcymistrz Górnictwa", "Legenda Górnictwa", "Górnik Runiczny",
        "Górnik Smoczej Stali", "Górnik Astralny", "Górnik Pustki",
        "Wieczny Mistrz Górnictwa",
    ),
    "Drwalstwo": (
        "Uczeń Drwalstwa", "Adept Drwalstwa", "Czeladnik Drwalstwa",
        "Specjalista Drwalstwa", "Ekspert Drwalstwa", "Mistrz Drwalstwa",
        "Arcymistrz Drwalstwa", "Legenda Drwalstwa", "Runiczny Drwal",
        "Drwal Smoczego Drewna", "Astralny Drwal", "Drwal Pustki",
        "Wieczny Mistrz Drwalstwa",
    ),
    "Zielarstwo": (
        "Uczeń Zielarstwa", "Adept Zielarstwa", "Czeladnik Zielarstwa",
        "Specjalista Zielarstwa", "Ekspert Zielarstwa", "Mistrz Zielarstwa",
        "Arcymistrz Zielarstwa", "Legenda Zielarstwa", "Runiczny Zielarz",
        "Zielarz Smoczego Szałwii", "Astralny Zielarz", "Zielarz Pustki",
        "Wieczny Mistrz Zielarstwa",
    ),
    "Gotowanie": (
        "Uczeń Gotowania", "Adept Gotowania", "Czeladnik Gotowania",
        "Specjalista Gotowania", "Ekspert Gotowania", "Mistrz Gotowania",
        "Arcymistrz Gotowania", "Legenda Gotowania", "Runiczny Kuchmistrz",
        "Kuchmistrz Smoczego Ognia", "Astralny Kuchmistrz", "Kuchmistrz Pustki",
        "Wieczny Mistrz Gotowania",
    ),
    "Alchemia": (
        "Uczeń Alchemii", "Adept Alchemii", "Czeladnik Alchemii",
        "Specjalista Alchemii", "Ekspert Alchemii", "Mistrz Alchemii",
        "Arcymistrz Alchemii", "Legenda Alchemii", "Alchemik Runiczny",
        "Alchemik Smoczej Stali", "Alchemik Astralny", "Alchemik Pustki",
        "Wieczny Mistrz Alchemii",
    ),
    "Kowalstwo": (
        "Uczeń Kowalstwa", "Adept Kowalstwa", "Czeladnik Kowalstwa",
        "Specjalista Kowalstwa", "Ekspert Kowalstwa", "Mistrz Kowalstwa",
        "Arcymistrz Kowalstwa", "Legenda Kowalstwa", "Kowal Runiczny",
        "Kowal Smoczej Stali", "Kowal Astralny", "Kowal Pustki",
        "Wieczny Mistrz Kowalstwa",
    ),
    "Jubilerstwo": (
        "Uczeń Jubilerstwa", "Adept Jubilerstwa", "Czeladnik Jubilerstwa",
        "Specjalista Jubilerstwa", "Ekspert Jubilerstwa", "Mistrz Jubilerstwa",
        "Arcymistrz Jubilerstwa", "Legenda Jubilerstwa", "Jubiler Runiczny",
        "Jubiler Smoczej Stali", "Jubiler Astralny", "Jubiler Pustki",
        "Wieczny Mistrz Jubilerstwa",
    ),
}

# v0.9.12: prestiżowe rangi 201-400. Nie dają dodatkowej mocy same z siebie;
# pokazują dalszą progresję profesji i są czytane przez NVDA/NPC.
_PROFESSION_400_RANK_SUFFIXES = (
    "Paragon", "Transcendentny Mistrz", "Mistrz Horyzontu",
    "Mistrz Otchłani", "Mistrz Gwiezdnego Szlaku",
    "Mistrz Pierwotnej Sztuki", "Mistrz Nieskończoności",
    "Mistrz Korony Świata", "Mistrz Ponadczasowy", "Arcylegenda",
)
for _profession_name, _names in list(PROFESSION_RANK_NAMES.items()):
    PROFESSION_RANK_NAMES[_profession_name] = tuple(_names) + tuple(
        f"{suffix} {_profession_name}" for suffix in _PROFESSION_400_RANK_SUFFIXES
    )

TOOL_PROFESSION_MAP = {
    "fishing": "Wędkarstwo",
    "mining": "Górnictwo",
    "woodcutting": "Drwalstwo",
    "crafting": "Kowalstwo",
    "cooking": "Gotowanie",
    "herbalism": "Zielarstwo",
    "alchemy": "Alchemia",
    "jewelcrafting": "Jubilerstwo",
}

def profession_for_tool_type(tool_type):
    return TOOL_PROFESSION_MAP.get(str(tool_type or ""))

def normalize_profession_name(profession):
    value = str(profession).strip().lower()
    if value in ("fishing", "wedkarstwo", "wędkarstwo"):
        return "Wędkarstwo"
    if value in ("mining", "gornictwo", "górnictwo"):
        return "Górnictwo"
    if value in ("woodcutting", "drwalstwo", "drwal"):
        return "Drwalstwo"
    if value in ("herbalism", "zielarstwo", "zielarz"):
        return "Zielarstwo"
    if value in ("cooking", "gotowanie", "kucharz"):
        return "Gotowanie"
    if value in ("alchemy", "alchemia"):
        return "Alchemia"
    if value in (
        "blacksmithing", "smithing", "kowalstwo",
        "kowal", "rzemioslo", "rzemiosło",
    ):
        return "Kowalstwo"
    if value in (
        "jewelcrafting", "jewelry", "jubilerstwo",
        "jubiler", "bizuteria", "biżuteria",
    ):
        return "Jubilerstwo"
    return str(profession)

def profession_max_level(profession):
    return PROFESSION_MAX_LEVEL

def profession_rank_thresholds(profession):
    return PROFESSION_RANK_THRESHOLDS

def profession_max_rank(profession):
    return PROFESSION_MAX_RANK

def profession_rank(level, profession=None):
    thresholds = profession_rank_thresholds(profession)
    level = max(1, int(level or 1))
    rank = 1
    for index, threshold in enumerate(thresholds, start=1):
        if level >= int(threshold):
            rank = index
        else:
            break
    return min(rank, profession_max_rank(profession))

def profession_rank_name(profession, level):
    profession = normalize_profession_name(profession)
    names = PROFESSION_RANK_NAMES.get(profession)
    if not names:
        return f"Ranga {profession_rank(level, profession)}"
    rank = profession_rank(level, profession)
    return names[min(rank - 1, len(names) - 1)]

# v0.9.7: NPC profesyjni reagują na realną rangę danej profesji.
# Warstwa jest wyłącznie dialogowa/prestiżowa: nie zmienia cen, XP ani statystyk.
def profession_npc_reaction_stage(rank):
    rank = max(1, min(PROFESSION_MAX_RANK, int(rank or 1)))
    if rank == 1:
        return "uczen"
    if rank <= 3:
        return "adept"
    if rank <= 5:
        return "specjalista"
    if rank <= 7:
        return "mistrz"
    if rank <= 12:
        return "legenda"
    return "wieczny"


PROFESSION_NPC_RANK_REACTIONS = {
    "fisher_tomas": {
        "uczen": "Dopiero zaczynasz, więc ucz się czytać wodę i nie śpiesz się z wielkimi połowami.",
        "adept": "Masz już pewną rękę. Teraz zacznij rozpoznawać łowiska po tym, co naprawdę w nich żyje.",
        "specjalista": "Widać doświadczenie. Takiego wędkarza można już wysłać na trudniejsze wody.",
        "mistrz": "Nie muszę ci tłumaczyć podstaw. Twoje połowy mówią same za siebie.",
        "legenda": "Ha! Taką rangę widuje się rzadziej niż legendarne ryby. Dobrze cię widzieć przy moim targu.",
        "wieczny": "Wieczny Mistrz przy moim straganie. Dziś to raczej ja powinienem słuchać twoich opowieści z wody.",
    },
    "miner_toren": {
        "uczen": "Na początku najważniejsze jest pewne uderzenie i powrót z kopalni w jednym kawałku.",
        "adept": "Już odróżniasz zwykły kamień od żyły wartej pracy.",
        "specjalista": "Masz oko do skały. Głębsze poziomy nie powinny cię już zaskakiwać.",
        "mistrz": "Twojego kilofa nie trzeba przedstawiać. W kopalni zostawiasz po sobie porządną robotę.",
        "legenda": "Górnicy mówią o takich jak ty przy ognisku. Rzadko widuję kogoś z taką rangą.",
        "wieczny": "Wieczny Mistrz Górnictwa. Przy tobie nawet stara kopalnia ma jeszcze coś do odkrycia.",
    },
    "lumberjack_bran": {
        "uczen": "Najpierw naucz się prowadzić Piłę równo. Las nie wybacza pośpiechu.",
        "adept": "Już słyszysz różnicę między młodym drewnem a porządnym pniem.",
        "specjalista": "Masz dobre tempo i oko do gatunków drewna.",
        "mistrz": "Twojej pracy nie trzeba poprawiać. Tak tnie ktoś, kto zna las.",
        "legenda": "O twoich ścinkach słyszałem, zanim dotarłeś do obozu. To już poziom legendy.",
        "wieczny": "Wieczny Mistrz Drwalstwa. Niewielu zna drewno tak dobrze jak ty.",
    },
    "herbalist_liora": {
        "uczen": "Zbieraj ostrożnie. Uczeń najwięcej traci wtedy, gdy pomyli podobne zioła.",
        "adept": "Coraz lepiej rozpoznajesz rośliny. Zaczynasz patrzeć na nie jak zielarz, nie jak przechodzień.",
        "specjalista": "Masz już wprawę w zbiorze i potrafisz znaleźć wartościowe okazy.",
        "mistrz": "Twoja wiedza o ziołach jest solidna. Mogę mówić z tobą jak z fachowcem.",
        "legenda": "Nieczęsto trafia do mnie Zielarz tej klasy. Twoja reputacja wyprzedza kroki.",
        "wieczny": "Wieczny Mistrz Zielarstwa. Przy takim doświadczeniu ogród sam staje się podręcznikiem.",
    },
    "specialist_cooking": {
        "uczen": "Na razie pilnuj temperatury i kolejności składników. Dobra kuchnia zaczyna się od podstaw.",
        "adept": "Masz już wyczucie smaku. Teraz ucz się powtarzalności.",
        "specjalista": "Twoje potrawy mają charakter. To już nie jest przypadkowe gotowanie.",
        "mistrz": "W kuchni możesz pracować obok mnie bez instrukcji na każdym kroku.",
        "legenda": "Legenda Gotowania w Błękitnym Płomieniu? Dzisiaj goście będą mieli o czym mówić.",
        "wieczny": "Wieczny Mistrz Gotowania. Nawet ja chętnie spróbuję tego, co przygotujesz.",
    },
    "specialist_alchemy": {
        "uczen": "Odmierzaj wszystko dwa razy. W Alchemii pomyłka pachnie znacznie gorzej niż w kuchni.",
        "adept": "Twoje mikstury są już stabilniejsze. To dobry znak.",
        "specjalista": "Potrafisz kontrolować reakcję zamiast tylko na nią patrzeć.",
        "mistrz": "Możemy rozmawiać o trudnych recepturach bez wracania do podstaw.",
        "legenda": "Legenda Alchemii nie pojawia się tu codziennie. Twoje eliksiry mają już własną reputację.",
        "wieczny": "Wieczny Mistrz Alchemii. Niewiele zostało rzeczy, których mógłbym cię nauczyć.",
    },
    "specialist_crafting": {
        "uczen": "Najpierw naucz się szanować materiał. Młot nie naprawi złego przygotowania.",
        "adept": "Twoje wykonanie jest coraz równiejsze. To podstawa dobrego Kowalstwa.",
        "specjalista": "Masz już rękę do trudniejszych zamówień.",
        "mistrz": "Przy twojej randze możemy mówić o rzemiośle bez tłumaczenia podstaw.",
        "legenda": "Legenda Kowalstwa w mojej Kuźni. Takie nazwisko przyciąga zamówienia samo.",
        "wieczny": "Wieczny Mistrz Kowalstwa. Twój młot ma większy autorytet niż niejeden mistrz.",
    },
    "jeweler_mirella": {
        "uczen": "Przy kamieniach liczy się cierpliwość. Jeden zły ruch potrafi zmarnować dobry materiał.",
        "adept": "Twoje dłonie są już pewniejsze. Możesz myśleć o trudniejszych oprawach.",
        "specjalista": "Masz oko do jakości i coraz lepiej dobierasz kamień do metalu.",
        "mistrz": "Twoje wyroby można już stawiać obok pracy doświadczonych jubilerów.",
        "legenda": "Legenda Jubilerstwa w mojej pracowni. Rzadkie kamienie trafiają w dobre ręce.",
        "wieczny": "Wieczny Mistrz Jubilerstwa. Przy takim kunszcie to klejnot ma zaszczyt trafić do twojej oprawy.",
    },
}

# Mistrzowie zbierackich profesji używają tego samego tonu co ich lokalni fachowcy.
PROFESSION_NPC_RANK_REACTION_ALIASES = {
    "specialist_fishing": "fisher_tomas",
    "specialist_mining": "miner_toren",
    "specialist_woodcutting": "lumberjack_bran",
    "specialist_herbalism": "herbalist_liora",
}

TOOL_MAX_LEVEL = 400
TOOL_MAX_TIER = 40
# Progi 1-200 pozostają dokładnie takie jak wcześniej. 201-400 dopisuje
# kolejne Tiery co 10 leveli bez przesuwania starych odblokowań.
TOOL_TIER_THRESHOLDS = (
    1, 10, 20, 30, 40, 50, 60, 70, 80, 90,
    100, 110, 120, 130, 140, 150, 160, 170, 180, 200,
) + tuple(range(210, 401, 10))
TOOL_TIER_BONUS_CHANCES = (
    0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18,
    0.20, 0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.37, 0.40,
) + tuple(round(0.40 + step * 0.01, 2) for step in range(1, 21))

def tool_max_level(tool_type):
    return TOOL_MAX_LEVEL

TOOL_TIER_NAMES = {
    "fishing": (
        "Wędka Ucznia",
        "Wędka Strumienia",
        "Wędka Jeziora",
        "Wędka Rzeki",
        "Wędka Wybrzeża",
        "Wędka Głębin",
        "Wędka Srebrnej Łuski",
        "Wędka Złotej Łuski",
        "Wędka Sztormu",
        "Wędka Mistrza",
        "Wędka Runiczna",
        "Wędka Smoczej Toni",
        "Wędka Kryształowa",
        "Wędka Astralnego Prądu",
        "Wędka Otchłani",
        "Wędka Pustki",
        "Wędka Gwiezdnego Morza",
        "Wędka Wiecznych Głębin",
        "Wędka Mitycznego Lewiatana",
        "Wędka Wiecznego Oceanu",
    ),
    "mining": (
        "Kilof Ucznia",
        "Kilof Miedzi",
        "Kilof Żelaza",
        "Kilof Srebra",
        "Kilof Złota",
        "Kilof Hartowanej Skały",
        "Kilof Głębinowy",
        "Kilof Kryształowy",
        "Kilof Kobaltu",
        "Kilof Mistrza",
        "Kilof Runiczny",
        "Kilof Smoczej Stali",
        "Kilof Obsydianowy",
        "Kilof Astralny",
        "Kilof Gwiezdnego Rdzenia",
        "Kilof Pustki",
        "Kilof Otchłani",
        "Kilof Eternium",
        "Kilof Mitycznego Złoża",
        "Kilof Wiecznej Góry",
    ),
    "woodcutting": (
        "Piła Ucznia",
        "Piła Brzozowa",
        "Piła Sosnowa",
        "Piła Dębowa",
        "Piła Bukowa",
        "Piła Jesionowa",
        "Piła Cedrowa",
        "Piła Cisowa",
        "Piła Żelaznego Drewna",
        "Piła Mistrza",
        "Piła Runicznego Drewna",
        "Piła Smoczego Drewna",
        "Piła Kryształowego Pnia",
        "Piła Astralnego Drewna",
        "Piła Gwiezdnego Serca",
        "Piła Pustki",
        "Piła Pradawnego Drzewa",
        "Piła Eternium",
        "Piła Drzewa Świata",
        "Piła Wiecznego Lasu",
    ),
    "crafting": (
        "Młot Rzemieślniczy Ucznia",
        "Młot Miedzi",
        "Młot Żelaza",
        "Młot Srebra",
        "Młot Złota",
        "Młot Hartowanej Stali",
        "Młot Precyzji",
        "Młot Kryształowy",
        "Młot Kobaltu",
        "Młot Mistrza",
        "Młot Runiczny",
        "Młot Smoczej Stali",
        "Młot Obsydianowy",
        "Młot Astralny",
        "Młot Gwiezdnej Kuźni",
        "Młot Pustki",
        "Młot Otchłani",
        "Młot Eternium",
        "Młot Mitycznej Kuźni",
        "Młot Wiecznego Kowala",
    ),
    "cooking": (
        "Nóż Kucharski Ucznia",
        "Nóż Spiżarni",
        "Nóż Targowy",
        "Nóż Karczemny",
        "Nóż Srebrnego Ostrza",
        "Nóż Złotego Ostrza",
        "Nóż Precyzji",
        "Nóż Szefa Kuchni",
        "Nóż Kryształowy",
        "Nóż Mistrza",
        "Nóż Runiczny",
        "Nóż Smoczego Ognia",
        "Nóż Uczty Bohaterów",
        "Nóż Astralny",
        "Nóż Gwiezdnej Uczty",
        "Nóż Pustki",
        "Nóż Otchłani",
        "Nóż Eternium",
        "Nóż Mitycznej Uczty",
        "Nóż Wiecznego Kucharza",
    ),
    "herbalism": (
        "Sierp Zielarski Ucznia",
        "Sierp Łąki",
        "Sierp Ziół Polnych",
        "Sierp Leśny",
        "Sierp Księżycowych Ziół",
        "Sierp Głębokiego Gaju",
        "Sierp Rzadkich Ziół",
        "Sierp Mistrzowskiego Zbioru",
        "Sierp Kryształowy",
        "Sierp Mistrza",
        "Sierp Runiczny",
        "Sierp Smoczych Ziół",
        "Sierp Słonecznego Kwiatu",
        "Sierp Astralny",
        "Sierp Gwiezdnego Mchu",
        "Sierp Pustki",
        "Sierp Otchłani",
        "Sierp Eternium",
        "Sierp Mitycznego Ogrodu",
        "Sierp Wiecznego Zielarza",
    ),
    "alchemy": (
        "Moździerz Ucznia",
        "Moździerz Kamienny",
        "Moździerz Żelazny",
        "Moździerz Srebrny",
        "Moździerz Złoty",
        "Moździerz Precyzji",
        "Moździerz Zielonego Szkła",
        "Moździerz Kryształowy",
        "Moździerz Kobaltu",
        "Moździerz Mistrza",
        "Moździerz Runiczny",
        "Moździerz Smoczej Esencji",
        "Moździerz Słonecznej Esencji",
        "Moździerz Astralny",
        "Moździerz Gwiezdnej Esencji",
        "Moździerz Pustki",
        "Moździerz Otchłani",
        "Moździerz Eternium",
        "Moździerz Mitycznej Esencji",
        "Moździerz Wiecznego Alchemika",
    ),
    "jewelcrafting": (
        "Szczypce Jubilerskie Ucznia",
        "Szczypce Miedzianego Drutu",
        "Szczypce Srebrnego Drutu",
        "Szczypce Złotego Splotu",
        "Szczypce Precyzyjnego Szlifu",
        "Szczypce Kryształowej Oprawy",
        "Szczypce Szmaragdowej Oprawy",
        "Szczypce Diamentowej Oprawy",
        "Szczypce Kobaltowej Oprawy",
        "Szczypce Mistrza Jubilerstwa",
        "Szczypce Runicznej Oprawy",
        "Szczypce Smoczej Stali",
        "Szczypce Słonecznego Klejnotu",
        "Szczypce Astralnego Splotu",
        "Szczypce Gwiezdnej Oprawy",
        "Szczypce Pustki",
        "Szczypce Otchłani",
        "Szczypce Eternium",
        "Szczypce Mitycznego Klejnotu",
        "Szczypce Wiecznego Klejnotu",
    ),
}

# v0.30.33: Tiery 21-40 mają pełne, unikalne nazwy zamiast powtarzania
# nazwy Tieru 20 z dopiskiem +210/+220 itd. Progi i mechanika pozostają bez zmian.
V03033_TOOL_TIER_NAMES_21_40 = {
    "fishing": (
        "Wędka Przebudzonej Rafy",
        "Wędka Transcendentnego Strumienia",
        "Wędka Horyzontu",
        "Wędka Niebiańskiego Prądu",
        "Wędka Pierwotnego Morza",
        "Wędka Echa Lewiatana",
        "Wędka Korony Fal",
        "Wędka Serca Oceanu",
        "Wędka Nieskończonego Sztormu",
        "Wędka Pradawnej Toni",
        "Wędka Zorzy Głębin",
        "Wędka Smoczego Prądu",
        "Wędka Tajemnicy Rafy",
        "Wędka Gwiezdnej Otchłani",
        "Wędka Wiecznego Horyzontu",
        "Wędka Korony Lewiatana",
        "Wędka Przeznaczenia Mórz",
        "Wędka Ponadczasowej Fali",
        "Wędka Końca Głębin",
        "Wędka Absolutnych Głębin",
    ),
    "mining": (
        "Kilof Przebudzonego Kamienia",
        "Kilof Transcendentnej Rudy",
        "Kilof Horyzontu Skał",
        "Kilof Niebiańskiego Kryształu",
        "Kilof Pierwotnej Góry",
        "Kilof Echa Głębin",
        "Kilof Korony Minerałów",
        "Kilof Serca Ziemi",
        "Kilof Nieskończonego Złoża",
        "Kilof Pradawnego Granitu",
        "Kilof Zorzy Kryształów",
        "Kilof Smoczej Skały",
        "Kilof Tajemnicy Podziemi",
        "Kilof Gwiezdnej Żyły",
        "Kilof Wiecznego Masywu",
        "Kilof Korony Gór",
        "Kilof Przeznaczenia Rudy",
        "Kilof Ponadczasowej Skały",
        "Kilof Końca Złoża",
        "Kilof Absolutnej Góry",
    ),
    "woodcutting": (
        "Piła Przebudzonego Gaju",
        "Piła Transcendentnego Pnia",
        "Piła Horyzontu Koron",
        "Piła Niebiańskiej Kory",
        "Piła Pierwotnego Lasu",
        "Piła Echa Drzew",
        "Piła Korony Konarów",
        "Piła Serca Puszczy",
        "Piła Nieskończonego Boru",
        "Piła Pradawnego Dębu",
        "Piła Zorzy Liści",
        "Piła Smoczego Pnia",
        "Piła Tajemnicy Kniei",
        "Piła Gwiezdnej Kory",
        "Piła Wiecznej Puszczy",
        "Piła Korony Drzewa Świata",
        "Piła Przeznaczenia Lasu",
        "Piła Ponadczasowego Drewna",
        "Piła Końca Boru",
        "Piła Absolutnego Drzewa",
    ),
    "crafting": (
        "Młot Przebudzonej Kuźni",
        "Młot Transcendentnego Kowala",
        "Młot Horyzontu Metalu",
        "Młot Niebiańskiej Stali",
        "Młot Pierwotnego Ognia",
        "Młot Echa Kowadła",
        "Młot Korony Kuźni",
        "Młot Serca Metalu",
        "Młot Nieskończonego Żaru",
        "Młot Pradawnego Kowadła",
        "Młot Zorzy Stali",
        "Młot Smoczego Żaru",
        "Młot Tajemnicy Metalu",
        "Młot Gwiezdnego Kowadła",
        "Młot Wiecznej Kuźni",
        "Młot Korony Kowali",
        "Młot Przeznaczenia Stali",
        "Młot Ponadczasowego Metalu",
        "Młot Końca Kuźni",
        "Młot Absolutnego Kowala",
    ),
    "cooking": (
        "Nóż Przebudzonej Kuchni",
        "Nóż Transcendentnego Smaku",
        "Nóż Horyzontu Uczty",
        "Nóż Niebiańskiej Potrawy",
        "Nóż Pierwotnego Paleniska",
        "Nóż Echa Przypraw",
        "Nóż Korony Szefów",
        "Nóż Serca Uczty",
        "Nóż Nieskończonego Smaku",
        "Nóż Pradawnej Receptury",
        "Nóż Zorzy Aromatów",
        "Nóż Smoczego Paleniska",
        "Nóż Tajemnicy Kuchni",
        "Nóż Gwiezdnej Receptury",
        "Nóż Wiecznej Uczty",
        "Nóż Korony Kucharzy",
        "Nóż Przeznaczenia Smaku",
        "Nóż Ponadczasowej Potrawy",
        "Nóż Końca Uczty",
        "Nóż Absolutnego Kucharza",
    ),
    "herbalism": (
        "Sierp Przebudzonej Łąki",
        "Sierp Transcendentnych Ziół",
        "Sierp Horyzontu Kwiatów",
        "Sierp Niebiańskiego Ogrodu",
        "Sierp Pierwotnego Gaju",
        "Sierp Echa Natury",
        "Sierp Korony Zielarzy",
        "Sierp Serca Ogrodu",
        "Sierp Nieskończonej Łąki",
        "Sierp Pradawnego Zielnika",
        "Sierp Zorzy Kwiatów",
        "Sierp Smoczych Korzeni",
        "Sierp Tajemnicy Natury",
        "Sierp Gwiezdnego Zielnika",
        "Sierp Wiecznego Ogrodu",
        "Sierp Korony Kwiatów",
        "Sierp Przeznaczenia Ziół",
        "Sierp Ponadczasowego Gaju",
        "Sierp Końca Łąki",
        "Sierp Absolutnego Zielarza",
    ),
    "alchemy": (
        "Moździerz Przebudzonej Esencji",
        "Moździerz Transcendentnego Eliksiru",
        "Moździerz Horyzontu Mikstur",
        "Moździerz Niebiańskiej Esencji",
        "Moździerz Pierwotnej Substancji",
        "Moździerz Echa Alchemii",
        "Moździerz Korony Alchemików",
        "Moździerz Serca Eliksiru",
        "Moździerz Nieskończonej Mikstury",
        "Moździerz Pradawnej Formuły",
        "Moździerz Zorzy Esencji",
        "Moździerz Smoczego Eliksiru",
        "Moździerz Tajemnicy Alchemii",
        "Moździerz Gwiezdnej Formuły",
        "Moździerz Wiecznej Esencji",
        "Moździerz Korony Mikstur",
        "Moździerz Przeznaczenia Eliksiru",
        "Moździerz Ponadczasowej Substancji",
        "Moździerz Końca Formuły",
        "Moździerz Absolutnego Alchemika",
    ),
    "jewelcrafting": (
        "Szczypce Przebudzonego Klejnotu",
        "Szczypce Transcendentnej Oprawy",
        "Szczypce Horyzontu Kryształów",
        "Szczypce Niebiańskiego Szlifu",
        "Szczypce Pierwotnego Kamienia",
        "Szczypce Echa Klejnotów",
        "Szczypce Korony Jubilerów",
        "Szczypce Serca Kryształu",
        "Szczypce Nieskończonej Oprawy",
        "Szczypce Pradawnego Szlifu",
        "Szczypce Zorzy Klejnotów",
        "Szczypce Smoczego Kryształu",
        "Szczypce Tajemnicy Oprawy",
        "Szczypce Gwiezdnego Kamienia",
        "Szczypce Wiecznej Korony",
        "Szczypce Korony Kryształów",
        "Szczypce Przeznaczenia Szlifu",
        "Szczypce Ponadczasowej Oprawy",
        "Szczypce Końca Klejnotu",
        "Szczypce Absolutnego Jubilera",
    ),
}
for _tool_type, _names in list(TOOL_TIER_NAMES.items()):
    _base_names = tuple(_names)
    TOOL_TIER_NAMES[_tool_type] = _base_names + V03033_TOOL_TIER_NAMES_21_40[_tool_type]

def tool_tier(level):
    level = max(1, min(TOOL_MAX_LEVEL, int(level)))
    tier = 1
    for number, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
        if level >= minimum:
            tier = number
        else:
            break
    return tier

def tool_tier_access_level(level):
    """Najwyższy próg zasobów/receptur odblokowany przez aktualny Tier narzędzia.

    Dostęp do nowej zawartości zmienia się wyłącznie przy awansie Tieru,
    a nie przy każdym pojedynczym levelu narzędzia.
    """
    tier = tool_tier(level)
    return int(TOOL_TIER_THRESHOLDS[tier - 1])


def required_tool_tier_for_level(required_level):
    return tool_tier(max(1, int(required_level or 1)))

def tool_tier_name(tool_type, level):
    tier = tool_tier(level)
    names = TOOL_TIER_NAMES.get(tool_type, TOOL_TIER_NAMES["mining"])
    return names[tier - 1]

def tool_tier_bonus_chance(level):
    return TOOL_TIER_BONUS_CHANCES[tool_tier(level) - 1]

# ============================================================
# v0.19.0 - GLOBAL PROGRESSION & REWARD GENERATOR
# Duże nagrody pozostają duże. Tempo gry kontrolują rosnące wymagania.
# Wszystkie krzywe używają wspólnej interpolacji logarytmicznej z mocnymi
# kamieniami milowymi co około 10-50 poziomów. Początek pozostaje szybki,
# endgame może operować milionami, miliardami i bilionami.
# ============================================================
V019_SAFE_INT = 8_000_000_000_000_000_000

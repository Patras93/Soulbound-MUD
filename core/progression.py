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

_EMBEDDED_GENERATOR_CORE_SOURCE = '"""Soulbound v0.30.24 Generator Core — Numeric Whitelist + Hybrid Quest Rewards.\n\nNumeric-only balance layer. Authored identity, names, IDs, unlock thresholds, requirements,\nquest/recipe structure, class equipment identity and world semantics are immutable here.\nGenerator Core may only derive numeric balance values such as HP, damage, XP, prices,\nautomatic reward amounts, cooldowns, mana costs and numeric effect strength. Quests explicitly\nmarked with manual_currency_reward_coins keep that authored currency reward unchanged. Base player attributes\nfrom race/class profiles are intentionally NOT generated.\n"""\nfrom __future__ import annotations\n\nfrom collections import defaultdict, deque\nimport hashlib\nimport math\nimport re\n\nGENERATOR_VERSION = "0.30.24"\nMAX_LEVEL = 400\nSAFE_INT = 9_000_000_000_000_000_000\n\nAXIS_TARGET_ACTIONS = {\n    "character": 18,\n    "class": 16,\n    "soul": 25,\n    "skill": 18,\n    "profession": 22,\n    "tool": 24,\n    "stat": 28,\n}\nAXIS_CURVES = {\n    "character": (140.0, 54.0, 1.82),\n    "class": (180.0, 70.0, 1.84),\n    "soul": (110.0, 48.0, 1.80),\n    "skill": (90.0, 31.0, 1.73),\n    "profession": (130.0, 43.0, 1.78),\n    "tool": (115.0, 37.0, 1.78),\n    "stat": (100.0, 29.0, 1.70),\n}\n\nRANK_HP = {"normal": 1.0, "elite": 1.55, "rare": 2.15, "mini": 4.2, "boss": 8.5, "world_boss": 14.0}\nRANK_DAMAGE = {"normal": 1.0, "elite": 1.12, "rare": 1.24, "mini": 1.42, "boss": 1.68, "world_boss": 1.95}\nRANK_REWARD = {"normal": 1.0, "elite": 1.8, "rare": 3.0, "mini": 5.0, "boss": 8.0, "world_boss": 13.0}\n\nSLOT_DEFENSE_WEIGHT = {\n    "head": 0.75, "body": 1.35, "hands": 0.55, "legs": 1.0, "feet": 0.55,\n    "ring": 0.35, "ring1": 0.35, "ring2": 0.35, "charm": 0.45, "charm1": 0.45, "charm2": 0.45,\n    "necklace": 0.45, "shoulders": 0.90, "belt": 0.70, "cloak": 0.50,\n    "bracers": 0.60, "relic": 0.55,\n}\n\n\ndef clamp(value, low, high):\n    return max(low, min(high, value))\n\n\ndef stable_unit(text: str) -> float:\n    raw = hashlib.sha256(str(text).encode("utf-8")).digest()\n    return int.from_bytes(raw[:8], "big") / float((1 << 64) - 1)\n\n\ndef stable_jitter(text: str, span: float = 0.08) -> float:\n    return 1.0 + (stable_unit(text) * 2.0 - 1.0) * span\n\n\ndef stage_from_index(index: int, maximum: int) -> int:\n    """Map an ordinal system level to the shared 1-400 Generator Core stage."""\n    index = max(1, int(index))\n    maximum = max(1, int(maximum))\n    if maximum <= 1:\n        return 1\n    index = min(index, maximum)\n    return 1 + int(round((index - 1) * (MAX_LEVEL - 1) / (maximum - 1)))\n\n\ndef axis_requirement(axis: str, level: int) -> int:\n    # v0.27.1: statystyki są jedyną osią bez twardego limitu. Pozostałe\n    # osie nadal należą do przestrzeni 1-400. Ta sama krzywa statów jest\n    # bezpiecznie ekstrapolowana ponad 400 aż do SAFE_INT.\n    raw_level = max(1, int(level))\n    level = raw_level if axis == "stat" else clamp(raw_level, 1, MAX_LEVEL)\n    base, growth, power = AXIS_CURVES[axis]\n    value = base + growth * (level ** power)\n    return min(SAFE_INT, max(1, int(round(value))))\n\n\ndef uncapped_stat_xp_scale(stat_level: int) -> float:\n    """Scale a stage-balanced stat XP reward to an uncapped stat level.\n\n    Level 1-400 keeps the original reward exactly. Above 400, the reward\n    grows in the same proportion as the generated requirement. This keeps\n    a stage-400 source at roughly the same actions-per-stat-point while\n    low-stage sources remain proportionally inefficient forever.\n    """\n    level = max(1, int(stat_level))\n    if level <= MAX_LEVEL:\n        return 1.0\n    anchor = float(axis_requirement("stat", MAX_LEVEL))\n    current = float(axis_requirement("stat", level))\n    return max(1.0, current / max(1.0, anchor))\n\n\ndef uncapped_stat_xp_gain(base_amount: int, stat_level: int) -> int:\n    base_amount = max(0, int(base_amount))\n    if base_amount <= 0:\n        return 0\n    return min(SAFE_INT, max(1, int(round(base_amount * uncapped_stat_xp_scale(stat_level)))))\n\n\ndef axis_gain(axis: str, level: int, intensity: float = 1.0) -> int:\n    target = AXIS_TARGET_ACTIONS[axis]\n    value = axis_requirement(axis, level) / float(target) * max(0.05, float(intensity))\n    return min(SAFE_INT, max(1, int(round(value))))\n\n\ndef character_hp_base(character_level: int, constitution: int) -> int:\n    character_level = clamp(int(character_level), 1, MAX_LEVEL)\n    constitution = max(1, int(constitution))\n    return max(1, int(round(48 + constitution * 5.2 + character_level * 3.1)))\n\n\ndef character_mana_base(character_level: int, intelligence: int, willpower: int | None = None) -> int:\n    character_level = clamp(int(character_level), 1, MAX_LEVEL)\n    intelligence = max(1, int(intelligence))\n    willpower = intelligence if willpower is None else max(1, int(willpower))\n    return max(0, int(round(22 + intelligence * 2.4 + willpower * 2.4 + character_level * 2.0)))\n\n\ndef character_attribute_power(character_level: int, stat_value: int) -> int:\n    character_level = clamp(int(character_level), 1, MAX_LEVEL)\n    stat_value = max(1, int(stat_value))\n    return max(1, int(round(stat_value + 0.30 * character_level)))\n\n\ndef speed_from_dexterity(dexterity: int) -> int:\n    dexterity = max(1, int(dexterity))\n    return max(1, int(round(8 + dexterity * 1.65)))\n\n\ndef dodge_from_dexterity(dexterity: int) -> float:\n    dexterity = max(1, int(dexterity))\n    value = 0.25 * (1.0 - math.exp(-max(0.0, dexterity - 10.0) / 78.0))\n    return round(clamp(value, 0.0, 0.25), 6)\n\n\ndef critical_chance_from_dexterity(dexterity: int) -> float:\n    dexterity = max(1, int(dexterity))\n    value = 0.035 + 0.285 * (1.0 - math.exp(-max(0.0, dexterity - 8.0) / 105.0))\n    return round(clamp(value, 0.035, 0.35), 6)\n\n\ndef critical_multiplier(character_level: int) -> float:\n    level = clamp(int(character_level), 1, MAX_LEVEL)\n    return round(1.45 + 0.20 * ((level - 1) / (MAX_LEVEL - 1)) ** 0.75, 6)\n\n\ndef magic_defense_base(character_level: int, willpower: int) -> int:\n    character_level = clamp(int(character_level), 1, MAX_LEVEL)\n    willpower = max(1, int(willpower))\n    return max(0, int(round(willpower * 0.55 + character_level * 0.10)))\n\n\ndef skill_level_power(level: int) -> float:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    # Smooth generated curve: meaningful 1-400 growth without a hidden 1-200 legacy branch.\n    return round(1.0 + 1.15 * ((level - 1) / (MAX_LEVEL - 1)) ** 0.82, 6)\n\n\ndef skill_cooldown_factor(level: int) -> float:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    reduction = 0.38 * ((level - 1) / (MAX_LEVEL - 1)) ** 0.90\n    return round(1.0 - reduction, 6)\n\n\ndef profession_action_seconds(tool_type: str, level: int) -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    # Tool identity changes feel deterministically, not through hand-authored per-tool timers.\n    u = stable_unit(f"{tool_type}:action-time")\n    base = 14.0 + 14.0 * u\n    minimum = 3.0 + 5.0 * stable_unit(f"{tool_type}:minimum-time")\n    progress = ((level - 1) / (MAX_LEVEL - 1)) ** 0.78\n    return max(1, int(round(base - (base - minimum) * progress)))\n\n\ndef gather_quantity(tool_type: str, tool_level: int, profession_level: int, roll: float) -> int:\n    tool_level = clamp(int(tool_level), 1, MAX_LEVEL)\n    profession_level = clamp(int(profession_level), 1, MAX_LEVEL)\n    progress = ((tool_level + profession_level - 2) / (2 * (MAX_LEVEL - 1)))\n    identity = 0.85 + 0.30 * stable_unit(f"{tool_type}:yield")\n    p2 = clamp((0.035 + 0.19 * progress) * identity, 0.02, 0.28)\n    p3 = clamp((0.010 + 0.055 * progress ** 1.35) * identity, 0.005, 0.09)\n    p4 = clamp((0.002 + 0.015 * progress ** 2.0) * identity, 0.001, 0.025)\n    if roll < p4: return 4\n    if roll < p4 + p3: return 3\n    if roll < p4 + p3 + p2: return 2\n    return 1\n\n\ndef crafting_xp_roll(base_value: int, roll: float) -> int:\n    base = max(1, int(base_value))\n    variance = 0.08 + 0.08 * stable_unit(f"craft-xp:{base}")\n    factor = 1.0 + (clamp(float(roll), 0.0, 1.0) * 2.0 - 1.0) * variance\n    return max(1, int(round(base * factor)))\n\n\ndef boss_chest_currency(stage: int, chest_kind: str = "boss") -> int:\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    identity = 1.0 + 0.25 * stable_unit(f"chest:{chest_kind}")\n    return max(1, int(round(currency_for_stage(stage, "boss") * 2.25 * identity)))\n\n\ndef resource_pool(resource_ids, items: dict, level: int, context: str = "resource") -> tuple:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    candidates = []\n    for iid in resource_ids:\n        item = items.get(iid, {})\n        generated = int(item.get("generator_level", 1) or 1)\n        if generated <= level:\n            candidates.append((iid, generated))\n    if not candidates:\n        fallback = sorted(\n            ((iid, int(items.get(iid, {}).get("generator_level", 1) or 1)) for iid in resource_ids if iid in items),\n            key=lambda row: (row[1], row[0]),\n        )\n        return tuple(iid for iid, _ in fallback[:1])\n    # Keep the pool cumulative, while deterministic ecology affinity makes different\n    # locations feel distinct without per-location numeric loot tables.\n    candidates.sort(key=lambda row: (row[1], row[0]))\n    return tuple(iid for iid, _ in candidates)\n\n\ndef resource_weights(resource_ids, items: dict, level: int, context: str = "resource") -> list[float]:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    weights = []\n    for iid in resource_ids:\n        generated = int(items.get(iid, {}).get("generator_level", 1) or 1)\n        age = max(0, level - generated)\n        freshness = 0.30 + 8.0 / ((1.0 + age / 34.0) ** 1.28)\n        affinity = 0.72 + 0.56 * stable_unit(f"{context}:{iid}:affinity")\n        weights.append(max(0.01, freshness * affinity))\n    return weights\n\n\ndef jackpot_chance(level: int, context: str = "jackpot") -> float:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    progress = (level - 1) / (MAX_LEVEL - 1)\n    identity = 0.75 + 0.50 * stable_unit(context)\n    return clamp((0.000002 + 0.000018 * progress ** 2.1) * identity, 0.000001, 0.00003)\n\n\ndef mob_hp(level: int, rank: str = "normal") -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 52.0 + 9.5 * level + 0.74 * level * level\n    return max(1, int(round(base * RANK_HP.get(rank, 1.0))))\n\n\ndef mob_damage(level: int, rank: str = "normal") -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 3.0 + 0.30 * level + 0.0105 * level * level\n    return max(1, int(round(base * RANK_DAMAGE.get(rank, 1.0))))\n\n\ndef currency_for_stage(level: int, rank: str = "normal") -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 7.0 * ((1.0 + level / 9.0) ** 2.18)\n    return min(SAFE_INT, max(1, int(round(base * RANK_REWARD.get(rank, 1.0)))))\n\n\ndef item_price_for_stage(level: int, rarity_mult: float = 1.0) -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 18.0 * ((1.0 + level / 8.0) ** 2.05)\n    return min(SAFE_INT, max(1, int(round(base * max(0.25, rarity_mult)))))\n\n\nQUEST_CURRENCY_ANCHORS = (\n    (1, 1_200), (10, 1_500), (25, 2_500), (50, 5_000),\n    (100, 10_000), (150, 20_000), (200, 40_000), (250, 100_000),\n    (300, 1_000_000), (350, 50_000_000), (400, 1_000_000_000),\n)\n\ndef _economy_anchor_value(level: int, anchors=QUEST_CURRENCY_ANCHORS) -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    if level <= anchors[0][0]: return int(anchors[0][1])\n    if level >= anchors[-1][0]: return int(anchors[-1][1])\n    for (l0,v0),(l1,v1) in zip(anchors, anchors[1:]):\n        if l0 <= level <= l1:\n            t=(level-l0)/float(l1-l0)\n            # Log interpolation keeps the late-game mithril transition smooth.\n            value=math.exp(math.log(max(1.0,float(v0))) + (math.log(max(1.0,float(v1)))-math.log(max(1.0,float(v0))))*t)\n            return min(SAFE_INT,max(1,int(round(value))))\n    return int(anchors[-1][1])\n\ndef quest_currency_for_stage(level: int, workload: float = 1.0, repeatable: bool = False, identity: str = "quest") -> int:\n    level=clamp(int(level),1,MAX_LEVEL)\n    workload=clamp(float(workload),1.0,8.0)\n    # Workload matters, but cannot multiply rewards eight-fold.\n    work_mult=1.0 + 0.22*(workload-1.0)\n    repeat_mult=0.72 if repeatable else 1.0\n    identity_mult=stable_jitter(f"quest-currency:{identity}",0.045)\n    coins=int(round(_economy_anchor_value(level)*work_mult*repeat_mult*identity_mult))\n    # Every ordinary quest pays at least one gold plus a silver remainder.\n    coins=max(1_001, coins)\n    if coins < 1_000_000_000 and coins % 1000 == 0:\n        coins += 137\n    return min(SAFE_INT, coins)\n\ndef tool_price_for_item(item: dict, identity: str = "tool") -> int:\n    # Basic profession tools are starter equipment. Their price must not depend on\n    # arbitrary item ordering / generator_level. Future gated tools may opt into\n    # authored numeric gates; Generator reads those gates but never creates them.\n    gates=[]\n    for key in ("required_tool_level","min_tool_level","min_profession_level","required_profession_level","required_mastery"):\n        try:\n            value=int(item.get(key,0) or 0)\n        except Exception:\n            value=0\n        if value>0: gates.append(value)\n    stage=clamp(max(gates) if gates else 1,1,MAX_LEVEL)\n    base=_economy_anchor_value(stage)\n    identity_mult=0.92 + 0.16*stable_unit(f"tool-price:{identity}")\n    return min(SAFE_INT,max(1_001,int(round(base*1.20*identity_mult))))\n\n\ndef system_cost(stage: int, identity: str = "system", intensity: float = 1.0) -> int:\n    """Generated cost for non-item systems (guilds, services, upgrades)."""\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    identity_mult = 0.88 + 0.24 * stable_unit(f"system-cost:{identity}")\n    return min(SAFE_INT, max(1, int(round(item_price_for_stage(stage) * max(0.10, float(intensity)) * identity_mult))))\n\n\ndef system_reward(stage: int, identity: str = "system", intensity: float = 1.0) -> int:\n    """Generated currency reward for system-level objectives."""\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    identity_mult = 0.90 + 0.20 * stable_unit(f"system-reward:{identity}")\n    return min(SAFE_INT, max(1, int(round(currency_for_stage(stage) * max(0.10, float(intensity)) * identity_mult))))\n\n\ndef generated_count(stage: int, identity: str = "objective", low: int = 1, high: int = 100) -> int:\n    """Bounded deterministic objective count derived from stage and identity."""\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    low, high = max(1, int(low)), max(1, int(high))\n    if high < low:\n        low, high = high, low\n    progress = ((stage - 1) / (MAX_LEVEL - 1)) ** 0.82\n    identity_shift = (stable_unit(f"count:{identity}") - 0.5) * 0.16\n    value = low + (high - low) * clamp(progress + identity_shift, 0.0, 1.0)\n    return clamp(int(round(value)), low, high)\n\n\ndef generated_cooldown_seconds(stage: int, identity: str = "system", minimum: int = 3600, maximum: int = 21600) -> int:\n    """Generated cooldown; higher-stage systems may take longer but remain bounded."""\n    stage = clamp(int(stage), 1, MAX_LEVEL)\n    minimum, maximum = max(3600, int(minimum)), max(3600, int(maximum))\n    if maximum < minimum:\n        minimum, maximum = maximum, minimum\n    progress = (stage - 1) / (MAX_LEVEL - 1)\n    identity_shift = stable_unit(f"cooldown:{identity}")\n    seconds = minimum + (maximum - minimum) * clamp(0.65 * progress + 0.35 * identity_shift, 0.0, 1.0)\n    # Hour granularity keeps user-facing timers predictable and NVDA-friendly.\n    return max(3600, int(round(seconds / 3600.0)) * 3600)\n\n\ndef guild_bonus_percent(level: int, max_level: int = 100) -> int:\n    level = clamp(int(level), 1, max(1, int(max_level)))\n    progress = (level - 1) / max(1, int(max_level) - 1)\n    return clamp(int(round(1 + 10 * progress ** 0.82)), 1, 11)\n\n\ndef resource_sale_for_stage(level: int, rarity_mult: float = 1.0) -> int:\n    level = clamp(int(level), 1, MAX_LEVEL)\n    base = 3.0 * ((1.0 + level / 10.0) ** 1.95)\n    return min(SAFE_INT, max(1, int(round(base * max(0.5, rarity_mult)))))\n\n\ndef mob_rank(template: dict) -> str:\n    if template.get("world_boss") or template.get("v016_world_boss") or template.get("v020_mythic_world_boss"):\n        return "world_boss"\n    if template.get("crypt_boss") or template.get("astral_boss") or template.get("giant_fortress_boss") or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss") or template.get("boss_mechanic") or template.get("v018_great_ruin_guardian"):\n        return "boss"\n    if template.get("mini_boss") or template.get("v0140_mini_boss"):\n        return "mini"\n    if template.get("rare_mob") or template.get("rare_variant") or template.get("rare_troll") or template.get("v016_legendary_rare"):\n        return "rare"\n    if template.get("elite_affix"):\n        return "elite"\n    return "normal"\n\n\ndef semantic_floor_level(template: dict) -> int | None:\n    direct = (\n        ("crypt_floor", 1.0, 0),\n        ("astral_floor", 1.0, 0),\n        ("giant_fortress_floor", 4.0, 0),\n        ("profession_dungeon_floor", 4.0, 0),\n        ("mythic_crypt_floor", 0.72, 115),\n        ("mythic_astral_floor", 0.66, 135),\n        ("v020_gauntlet_round", 18.0, 210),\n        ("guild_hall_level", 38.0, 20),\n        ("procedural_region_stage", 1.0, 0),\n    )\n    for key, scale, offset in direct:\n        if template.get(key) is not None:\n            try:\n                return clamp(int(round(offset + int(template[key]) * scale)), 1, MAX_LEVEL)\n            except Exception:\n                pass\n    return None\n\n\ndef _graph_room_levels(rooms: dict) -> dict[str, int]:\n    """Derive numeric balance stages without changing authored room semantics."""\n    if not rooms:\n        return {}\n    start = "square" if "square" in rooms else next(iter(rooms))\n    dist = {start: 0}\n    q = deque([start])\n    while q:\n        rid = q.popleft()\n        for target in (rooms.get(rid, {}).get("exits") or {}).values():\n            if target in rooms and target not in dist:\n                dist[target] = dist[rid] + 1\n                q.append(target)\n    room_levels = {}\n    for rid, room in rooms.items():\n        lvl = semantic_floor_level(room)\n        if lvl is None:\n            text = f"{rid} {room.get(\'zone\',\'\')} {room.get(\'name\',\'\')}".lower()\n            floor_match = re.search(r"(?:floor|level|poziom|pietro|piętro)[_ -]*(\\d{1,4})", text)\n            if floor_match and any(k in text for k in ("crypt", "krypt", "astral", "tower", "wież", "fortress", "twierdz", "dungeon", "loch")):\n                lvl = clamp(int(floor_match.group(1)), 1, MAX_LEVEL)\n            else:\n                d = dist.get(rid)\n                if d is None:\n                    lvl = 160 + int(stable_unit(rid) * 220)\n                else:\n                    lvl = 1 + int(round(1.9 * d + 0.10 * d * d))\n                if room.get("v020_mega_gate") or room.get("v020_gauntlet"):\n                    lvl = max(lvl, 220)\n        room_levels[rid] = clamp(int(lvl), 1, MAX_LEVEL)\n        # generator_level is balance metadata only. Never overwrite recommended_mastery,\n        # exits, names, zones or any authored access/recommendation field.\n        _write_record_numeric("ROOMS", room, "generator_level", room_levels[rid])\n    return room_levels\n\n\n\ndef _mob_levels(ns: dict, room_levels: dict[str, int]) -> dict[str, int]:\n    mobs = ns.get("MOB_TEMPLATES", {})\n    spawns = ns.get("MOB_SPAWNS", [])\n    by_mob = defaultdict(list)\n    for rid, mid in spawns:\n        if rid in room_levels:\n            by_mob[str(mid)].append(room_levels[rid])\n\n    cache = {}\n    visiting = set()\n    def level_for(mid: str) -> int:\n        if mid in cache:\n            return cache[mid]\n        if mid in visiting:\n            return 1 + int(stable_unit(mid) * (MAX_LEVEL - 1))\n        visiting.add(mid)\n        t = mobs.get(mid, {})\n        lvl = semantic_floor_level(t)\n        if lvl is None:\n            for base_key in ("elite_base_template", "rare_base_template", "base_template", "template_id"):\n                base = t.get(base_key)\n                if base and base != mid and base in mobs:\n                    lvl = level_for(str(base)); break\n        if lvl is None and by_mob.get(mid):\n            # A reusable template is balanced for the EARLIEST place where it can occur.\n            # Later rooms may add harder ranks/other templates, but a quest drop cannot\n            # require a mob whose stats were tuned for a later duplicate spawn.\n            lvl = min(by_mob[mid])\n        if lvl is None:\n            lvl = 1 + int(stable_unit(mid) * (MAX_LEVEL - 1))\n        cache[mid] = clamp(int(lvl), 1, MAX_LEVEL)\n        visiting.discard(mid)\n        return cache[mid]\n\n    for mid in mobs:\n        level_for(mid)\n    return cache\n\n\ndef runtime_mob_balance(template_id: str, template: dict, level: int, rank: str | None = None) -> dict:\n    """Balance whitelisted numeric fields of a runtime mob; semantic identity stays authored."""\n    level = clamp(int(level), 1, MAX_LEVEL)\n    rank = str(rank or mob_rank(template))\n    _write_record_numeric("MOB_TEMPLATES", template, "generator_level", level)\n    _write_record_numeric("MOB_TEMPLATES", template, "v019_stage", level)\n    hp = mob_hp(level, rank)\n    _write_record_numeric("MOB_TEMPLATES", template, "max_hp", hp)\n    _write_record_numeric("MOB_TEMPLATES", template, "base_max_hp", hp)\n    _write_record_numeric("MOB_TEMPLATES", template, "damage", mob_damage(level, rank))\n    reward_mult = RANK_REWARD.get(rank, 1.0)\n    _write_record_numeric("MOB_TEMPLATES", template, "character_xp_reward", axis_gain("character", level, reward_mult))\n    _write_record_numeric("MOB_TEMPLATES", template, "class_xp_reward", axis_gain("class", level, reward_mult))\n    _write_record_numeric("MOB_TEMPLATES", template, "soul_reward", axis_gain("soul", level, reward_mult))\n    _write_record_numeric("MOB_TEMPLATES", template, "stat_reward", axis_gain("stat", level, reward_mult))\n    _write_record_numeric("MOB_TEMPLATES", template, "silver", currency_for_stage(level, rank))\n    _write_record_numeric("MOB_TEMPLATES", template, "gold", 0)\n    _write_record_numeric("MOB_TEMPLATES", template, "mithril", 0)\n    drops = template.get("drops")\n    if isinstance(drops, dict) and drops:\n        base_chance = {"normal": .055, "elite": .09, "rare": .14, "mini": .22, "boss": .34, "world_boss": .48}.get(rank, .055)\n        count = max(1, len(drops))\n        for item_id in list(drops):\n            chance = base_chance * stable_jitter(f"{template_id}:{item_id}", .22) / (count ** .20)\n            _write_nested_numeric("MOB_TEMPLATES", template, "drops", item_id, round(clamp(chance, .005, .85), 5))\n    return template\n\n\n\n\ndef _generate_mobs(ns: dict, levels: dict[str, int]) -> None:\n    mobs = ns.get("MOB_TEMPLATES", {})\n    for mid, t in mobs.items():\n        lvl = levels[mid]\n        rank = mob_rank(t)  # derived from authored flags; never stored back as identity.\n        _write_record_numeric("MOB_TEMPLATES", t, "generator_level", lvl)\n        _write_record_numeric("MOB_TEMPLATES", t, "v019_stage", lvl)\n        hp = mob_hp(lvl, rank)\n        _write_record_numeric("MOB_TEMPLATES", t, "max_hp", hp)\n        _write_record_numeric("MOB_TEMPLATES", t, "base_max_hp", hp)\n        _write_record_numeric("MOB_TEMPLATES", t, "damage", mob_damage(lvl, rank))\n        reward_mult = RANK_REWARD.get(rank, 1.0)\n        _write_record_numeric("MOB_TEMPLATES", t, "character_xp_reward", axis_gain("character", lvl, reward_mult))\n        _write_record_numeric("MOB_TEMPLATES", t, "class_xp_reward", axis_gain("class", lvl, reward_mult))\n        _write_record_numeric("MOB_TEMPLATES", t, "soul_reward", axis_gain("soul", lvl, reward_mult))\n        _write_record_numeric("MOB_TEMPLATES", t, "stat_reward", axis_gain("stat", lvl, reward_mult))\n        _write_record_numeric("MOB_TEMPLATES", t, "silver", currency_for_stage(lvl, rank))\n        _write_record_numeric("MOB_TEMPLATES", t, "gold", 0)\n        _write_record_numeric("MOB_TEMPLATES", t, "mithril", 0)\n        drops = t.get("drops")\n        if isinstance(drops, dict) and drops:\n            base_chance = {"normal": .055, "elite": .09, "rare": .14, "mini": .22, "boss": .34, "world_boss": .48}.get(rank, .055)\n            count = max(1, len(drops))\n            for item_id in list(drops):\n                chance = base_chance * stable_jitter(f"{mid}:{item_id}", .22) / (count ** .20)\n                _write_nested_numeric("MOB_TEMPLATES", t, "drops", item_id, round(clamp(chance, .005, .85), 5))\n\n\n\n\ndef _initial_item_level(item_id: str, item: dict) -> int | None:\n    # Only structural world semantics are accepted here. Legacy prices, defense,\n    # required mastery and old profession levels are deliberately ignored.\n    for key in ("procedural_region_stage", "boss_chest_floor", "boss_relic_floor", "astral_relic_floor"):\n        value = item.get(key)\n        if value:\n            try:\n                return clamp(int(value), 1, MAX_LEVEL)\n            except Exception:\n                pass\n    text = f"{item_id} {item.get(\'desc\',\'\')}".lower()\n    floor_match = re.search(r"(?:floor|pietro|piętro)[ _:+-]*(\\d{1,4})", text)\n    if floor_match:\n        return clamp(int(floor_match.group(1)), 1, MAX_LEVEL)\n    return None\n\n\ndef _ordinal_hints(items: dict) -> dict[str, int]:\n    """Turn content tiers into generated 1-400 stages without trusting their values.\n\n    Tier numbers are treated only as ordering labels. Their old numeric magnitude is\n    never used as a level or power value.\n    """\n    fields = (\n        "class_equipment_tier", "crypt_set_tier", "corpse_material_tier",\n        "legendary_loot_tier", "blacksmith_tier", "gem_level",\n        "astral_set_tier", "v020_artifact_tier", "jewelcraft_level",\n    )\n    hints = {}\n    for field in fields:\n        vals = []\n        for item in items.values():\n            value = item.get(field)\n            if value is not None:\n                vals.append(value)\n        unique = sorted(set(vals), key=lambda x: (float(x) if str(x).replace(\'.\', \'\', 1).isdigit() else str(x)))\n        if not unique:\n            continue\n        positions = {v: (1 if len(unique) == 1 else 1 + int(round(i * (MAX_LEVEL - 1) / (len(unique) - 1)))) for i, v in enumerate(unique)}\n        for iid, item in items.items():\n            if item.get(field) in positions:\n                generated = positions[item[field]]\n                hints[iid] = min(hints.get(iid, MAX_LEVEL), generated)\n    return hints\n\n\ndef _normalized_order_levels(pairs) -> dict:\n    cleaned = [(str(iid), float(order)) for iid, order in pairs if iid is not None and order is not None]\n    if not cleaned:\n        return {}\n    unique = sorted({order for _iid, order in cleaned})\n    if len(unique) == 1:\n        rank_to_level = {unique[0]: 1}\n    else:\n        rank_to_level = {order: 1 + int(round(idx * (MAX_LEVEL - 1) / (len(unique) - 1))) for idx, order in enumerate(unique)}\n    return {iid: rank_to_level[order] for iid, order in cleaned}\n\n\ndef _resource_order_hints(ns: dict, items: dict) -> dict[str, int]:\n    hints = {}\n    fish_ids = set(ns.get("FISH_RESOURCE_IDS", set()) or set())\n    fish_unlock = ns.get("fish_unlock_level")\n    if callable(fish_unlock):\n        pairs = []\n        for iid in fish_ids:\n            try: pairs.append((iid, fish_unlock(iid)))\n            except Exception: pass\n        hints.update(_normalized_order_levels(pairs))\n\n    ore_levels = ns.get("ORE_ATLAS_LEVELS", {}) or {}\n    hints.update(_normalized_order_levels((iid, ore_levels.get(iid, 1)) for iid in (ns.get("ORE_RESOURCE_IDS", set()) or set())))\n\n    for ids_name, table_name in (("WOOD_RESOURCE_IDS", "WOOD_ATLAS_ROOM_MIN_LEVELS"), ("HERB_RESOURCE_IDS", "HERB_ATLAS_ROOM_MIN_LEVELS")):\n        ids = set(ns.get(ids_name, set()) or set())\n        table = ns.get(table_name, {}) or {}\n        mins = {}\n        for _room, mapping in table.items():\n            if not isinstance(mapping, dict):\n                continue\n            for iid, old_order in mapping.items():\n                if iid in ids:\n                    try:\n                        old_order = float(old_order)\n                        mins[iid] = min(mins.get(iid, old_order), old_order)\n                    except Exception:\n                        pass\n        # Resources without an old placement still join deterministically after ordered ones.\n        ordered = _normalized_order_levels(mins.items())\n        hints.update(ordered)\n        missing = sorted(ids - set(ordered))\n        for iid in missing:\n            hints[iid] = 1 + int(stable_unit(f"resource-order:{ids_name}:{iid}") * (MAX_LEVEL - 1))\n\n    # Rare resource variants inherit their base species/material stage later.\n    return hints\n\n\ndef _item_levels(ns: dict, mob_levels: dict[str, int]) -> dict[str, int]:\n    items = ns.get("ITEMS", {})\n    mobs = ns.get("MOB_TEMPLATES", {})\n    levels = {iid: _initial_item_level(iid, item) for iid, item in items.items()}\n    resource_hints = _resource_order_hints(ns, items)\n    for iid, hint in resource_hints.items():\n        levels[iid] = hint\n    ordinal = _ordinal_hints(items)\n    for iid, hint in ordinal.items():\n        if levels.get(iid) is None:\n            levels[iid] = hint\n    # Drops inherit the earliest content level that can produce them.\n    drop_sources = defaultdict(list)\n    for mid, t in mobs.items():\n        for iid in (t.get("drops") or {}):\n            if iid in items:\n                drop_sources[iid].append(mob_levels.get(mid, 1))\n        for key in ("corpse_equipment_pool", "corpse_material_pool"):\n            for iid in (t.get(key) or []):\n                if iid in items:\n                    drop_sources[iid].append(mob_levels.get(mid, 1))\n    for iid, values in drop_sources.items():\n        # Gathering resources keep their generated profession order. Mob drops of the\n        # same material are re-priced to that stage instead of collapsing the whole\n        # profession curve to the earliest creature that happens to carry it.\n        if iid in resource_hints:\n            continue\n        inherited = min(values)\n        levels[iid] = inherited if levels.get(iid) is None else min(levels[iid], inherited)\n\n    # Resource variants inherit base-resource level. Resolve repeatedly.\n    for _ in range(4):\n        changed = False\n        for iid, item in items.items():\n            base = item.get("base_resource_id") or item.get("crypt_base_item") or item.get("v020_artifact_base")\n            if base in levels and levels.get(base) is not None and levels.get(iid) is None:\n                levels[iid] = levels[base]; changed = True\n        if not changed: break\n\n    # Unlinked content is placed deterministically; it cannot inherit balance from hand-written prices/stats.\n    for iid in items:\n        if levels.get(iid) is None:\n            levels[iid] = 1 + int(stable_unit(iid) * (MAX_LEVEL - 1))\n    return {k: clamp(int(v), 1, MAX_LEVEL) for k, v in levels.items()}\n\n\ndef _rarity_multiplier(item: dict) -> float:\n    rarity = str(item.get("rarity", "")).lower()\n    return {\n        "common": 1.0, "uncommon": 1.25, "rare": 1.6, "epic": 2.1,\n        "legendary": 3.0, "mythic": 4.0, "crafted": 1.35,\n    }.get(rarity, max(1.0, float(item.get("rare_value_multiplier", 1.0) or 1.0)))\n\n\ndef _generate_items(ns: dict, levels: dict[str, int]) -> None:\n    """Generate only whitelisted numeric item balance; authored gates/types/stat identity stay intact."""\n    items = ns.get("ITEMS", {})\n    resource_ids = set()\n    for key in ("FISH_RESOURCE_IDS", "ORE_RESOURCE_IDS", "WOOD_RESOURCE_IDS", "HERB_RESOURCE_IDS"):\n        resource_ids.update(ns.get(key, set()) or set())\n    for iid, item in items.items():\n        lvl = levels[iid]\n        _write_record_numeric("ITEMS", item, "generator_level", lvl)\n        rarity_mult = _rarity_multiplier(item)\n        typ = str(item.get("type", "")).lower()\n        if iid in resource_ids or item.get("resource_category") or item.get("base_resource_id"):\n            sale = resource_sale_for_stage(lvl, rarity_mult)\n            _write_record_numeric("ITEMS", item, "sell_silver", sale)\n            _write_record_numeric("ITEMS", item, "sell_gold", 0)\n            _write_record_numeric("ITEMS", item, "sell_mithril", 0)\n            _write_record_numeric("ITEMS", item, "price", max(sale * 3, 1))\n        elif typ == "tool" or item.get("tool_type"):\n            _write_record_numeric("ITEMS", item, "price", tool_price_for_item(item, str(item.get("tool_type") or iid)))\n        else:\n            _write_record_numeric("ITEMS", item, "price", item_price_for_stage(lvl, rarity_mult))\n        if typ == "armor" or item.get("slot"):\n            slot = str(item.get("slot", "body"))\n            weight = SLOT_DEFENSE_WEIGHT.get(slot, .75)\n            _write_record_numeric("ITEMS", item, "defense", max(1, int(round((1.0 + lvl / 18.0) * weight * rarity_mult))))\n            if item.get("affix"):\n                _write_record_numeric("ITEMS", item, "affix_amount", max(1, int(round(1 + lvl / 55.0 * math.sqrt(rarity_mult)))))\n        if isinstance(item.get("stats"), dict):\n            for stat in list(item["stats"]):\n                value = max(1, int(round((1 + lvl / 62.0) * math.sqrt(rarity_mult) * stable_jitter(f"{iid}:stat:{stat}", .12))))\n                _write_nested_numeric("ITEMS", item, "stats", stat, value)\n        if isinstance(item.get("properties"), dict):\n            for prop in list(item["properties"]):\n                value = round(clamp((1.0 + lvl / 48.0) * math.sqrt(rarity_mult) * stable_jitter(f"{iid}:prop:{prop}", .10), .5, 18.0), 3)\n                _write_nested_numeric("ITEMS", item, "properties", prop, value)\n        if isinstance(item.get("rune_stats"), dict):\n            for stat in list(item["rune_stats"]):\n                _write_nested_numeric("ITEMS", item, "rune_stats", stat, max(1, int(round(1 + lvl / 70.0))))\n        if isinstance(item.get("rune_properties"), dict):\n            for prop in list(item["rune_properties"]):\n                _write_nested_numeric("ITEMS", item, "rune_properties", prop, round(clamp(.8 + lvl / 85.0, .8, 7.0), 3))\n        if "heal" in item:\n            _write_record_numeric("ITEMS", item, "heal", max(5, int(round(18 + lvl * 2.2))))\n        if "mana" in item:\n            _write_record_numeric("ITEMS", item, "mana", max(5, int(round(15 + lvl * 2.0))))\n        if "soul_xp" in item:\n            _write_record_numeric("ITEMS", item, "soul_xp", axis_gain("soul", lvl, 2.0))\n\n\n\n\ndef _recipe_stage(recipe: dict, item_levels: dict[str, int]) -> int:\n    """Semantic hint only; final recipe levels are regenerated across 1-400."""\n    values = []\n    for iid in (recipe.get("ingredients") or {}):\n        if iid in item_levels:\n            values.append(item_levels[iid])\n    if values:\n        return clamp(max(values), 1, MAX_LEVEL)\n    output = recipe.get("output")\n    if output in item_levels:\n        return clamp(item_levels[output], 1, MAX_LEVEL)\n    rid = str(recipe.get("id") or recipe.get("name") or "recipe")\n    return 1 + int(stable_unit(rid) * (MAX_LEVEL - 1))\n\n\ndef _recipe_topological_order(table: dict, item_levels: dict[str, int]) -> list[str]:\n    """Order recipes by dependencies and generated ingredient stages, never old numeric requirements."""\n    output_to_recipe = {}\n    for rid, recipe in table.items():\n        output = recipe.get("output")\n        if output:\n            output_to_recipe[str(output)] = rid\n\n    outgoing = defaultdict(set)\n    indegree = {rid: 0 for rid in table}\n    for rid, recipe in table.items():\n        for iid in (recipe.get("ingredients") or {}):\n            producer = output_to_recipe.get(str(iid))\n            if producer and producer != rid and rid not in outgoing[producer]:\n                outgoing[producer].add(rid)\n                indegree[rid] += 1\n\n    # Content insertion order describes semantic progression without carrying any\n    # hand-authored balance number. Dependencies still take precedence, so a\n    # component recipe is always generated before recipes that consume it.\n    insertion_index = {rid: i for i, rid in enumerate(table)}\n\n    def key(rid: str):\n        return (insertion_index.get(rid, 10**9), stable_unit(f"recipe-order:{rid}"), rid)\n\n    ready = sorted((rid for rid, deg in indegree.items() if deg == 0), key=key)\n    ordered = []\n    while ready:\n        rid = ready.pop(0)\n        ordered.append(rid)\n        for nxt in sorted(outgoing.get(rid, ()), key=key):\n            indegree[nxt] -= 1\n            if indegree[nxt] == 0:\n                ready.append(nxt)\n                ready.sort(key=key)\n\n    # Cycles should not block generation. Deterministic ordering breaks them without trusting legacy levels.\n    if len(ordered) != len(table):\n        remaining = [rid for rid in table if rid not in set(ordered)]\n        ordered.extend(sorted(remaining, key=key))\n    return ordered\n\n\ndef _generate_recipes(ns: dict, item_levels: dict[str, int]) -> int:\n    """Balance recipe XP only; authored requirements, ingredients, outputs and quantities are immutable."""\n    total = 0\n    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):\n        table = ns.get(table_name, {}) or {}\n        for rid, recipe in table.items():\n            total += 1\n            lvl = _recipe_stage(recipe, item_levels)\n            for gate in (recipe.get("min_profession_level"), recipe.get("min_tool_level")):\n                try:\n                    if gate is not None:\n                        lvl = max(lvl, int(gate))\n                except Exception:\n                    pass\n            lvl = clamp(int(lvl), 1, MAX_LEVEL)\n            xp = axis_gain("profession", lvl, 1.35)\n            _write_record_numeric(table_name, recipe, "generator_level", lvl)\n            _write_record_numeric(table_name, recipe, "xp", xp)\n            _write_record_numeric(table_name, recipe, "profession_xp", xp)\n            _write_record_numeric(table_name, recipe, "tool_xp", axis_gain("tool", lvl, 1.20))\n    return total\n\n\n\n\ndef _giver_stage(ns: dict, quest: dict) -> int:\n    giver = str(quest.get("giver") or "")\n    rooms = ns.get("ROOMS", {}) or {}\n    stages = []\n    for npc in (ns.get("NPCS", {}) or {}).values():\n        if str(npc.get("name") or "") != giver:\n            continue\n        room = rooms.get(str(npc.get("room") or ""), {})\n        if isinstance(room, dict):\n            try: stages.append(int(room.get("generator_level", 1) or 1))\n            except Exception: pass\n    return clamp(min(stages) if stages else 1, 1, MAX_LEVEL)\n\n\ndef _quest_alias_levels(ns: dict, alias: str, mob_levels: dict[str, int]) -> list[int]:\n    alias = str(alias or "")\n    if not alias:\n        return []\n    values = []\n    for mid, mob in (ns.get("MOB_TEMPLATES", {}) or {}).items():\n        tags = set(map(str, mob.get("quest_targets") or ()))\n        direct = mob.get("quest_target")\n        if direct is not None:\n            tags.add(str(direct))\n        if alias in tags:\n            values.append(int(mob_levels.get(mid, mob.get("generator_level", 1) or 1)))\n    return values\n\n\ndef _collect_category_stage(ns: dict, category: str, item_levels: dict[str, int]) -> int | None:\n    category = str(category or "").lower()\n    set_name = {\n        "fish": "FISH_RESOURCE_IDS", "fish_river": "FISH_RESOURCE_IDS",\n        "ore": "ORE_RESOURCE_IDS", "wood": "WOOD_RESOURCE_IDS", "herb": "HERB_RESOURCE_IDS",\n    }.get(category)\n    if not set_name:\n        return None\n    values = [int(item_levels[iid]) for iid in (ns.get(set_name, set()) or set()) if iid in item_levels]\n    return min(values) if values else None\n\n\ndef _quest_stage(ns: dict, qid: str, quest: dict, mob_levels: dict[str, int], item_levels: dict[str, int]) -> int:\n    # A starter flag is semantic identity: starter quests must be available to a\n    # fresh character regardless of the item they happen to reward.\n    if quest.get("starter_quest"):\n        return 1\n\n    kind = str(quest.get("kind") or "")\n    target = quest.get("target")\n    # Profession onboarding must follow the first obtainable resource of that\n    # profession, never the generated physical location of its NPC. Rebuilding\n    # the city/world topology therefore cannot move a starter profession quest\n    # to mid/endgame. This is a semantic rule, not a per-quest exception.\n    if (quest.get("reward_profession") and not quest.get("requires_quest")\n            and kind in ("collect_category", "collect_distinct_category")):\n        category_stage = _collect_category_stage(ns, target, item_levels)\n        if category_stage is not None:\n            return clamp(category_stage, 1, MAX_LEVEL)\n\n    values = [_giver_stage(ns, quest)]\n    if target in mob_levels:\n        values.append(mob_levels[target])\n    else:\n        alias_levels = _quest_alias_levels(ns, target, mob_levels)\n        if alias_levels:\n            # A category/alias quest becomes available when its first valid source\n            # is reachable; later variants stay valid automatically.\n            values.append(min(alias_levels))\n    if target in item_levels:\n        values.append(item_levels[target])\n    if kind in ("collect_category", "collect_distinct_category"):\n        category_stage = _collect_category_stage(ns, target, item_levels)\n        if category_stage is not None:\n            values.append(category_stage)\n    for target_id in (quest.get("targets") or ()):\n        if target_id in mob_levels: values.append(mob_levels[target_id])\n        if target_id in item_levels: values.append(item_levels[target_id])\n    for iid in (quest.get("resource_targets") or {}):\n        if iid in item_levels: values.append(item_levels[iid])\n\n    # Delivery difficulty follows the destination, not the free quest item.\n    target_npc = quest.get("target_npc")\n    if target_npc and target_npc in (ns.get("NPCS", {}) or {}):\n        room_id = ns["NPCS"][target_npc].get("room")\n        room = (ns.get("ROOMS", {}) or {}).get(room_id, {})\n        if isinstance(room, dict):\n            values.append(int(room.get("generator_level", 1) or 1))\n\n    # Soul trial tier is structural identity; its old required-level number is ignored.\n    if quest.get("soul_trial_tier"):\n        try:\n            tier = clamp(int(quest["soul_trial_tier"]), 1, 40)\n            values.append(1 if tier == 1 else (tier - 1) * 10)\n        except Exception:\n            pass\n    return clamp(max(values or [1]), 1, MAX_LEVEL)\n\n\ndef _generate_quests(ns: dict, mob_levels: dict[str, int], item_levels: dict[str, int]) -> None:\n    """Generate whitelisted numeric quest rewards while preserving explicitly authored currency rewards."""\n    quests = ns.get("QUESTS", {})\n    levels = {qid: _quest_stage(ns, qid, q, mob_levels, item_levels) for qid, q in quests.items()}\n    for _ in range(max(1, len(quests))):\n        changed = False\n        for qid, q in quests.items():\n            prev = q.get("requires_quest")\n            if prev in levels and levels[qid] < levels[prev]:\n                levels[qid] = levels[prev]; changed = True\n        if not changed:\n            break\n    for qid, q in quests.items():\n        lvl = clamp(int(levels.get(qid, 1)), 1, MAX_LEVEL)\n        needed = max(1, int(q.get("needed", 1) or 1))\n        workload = clamp(math.sqrt(needed), 1.0, 8.0)\n        repeat_mult = .72 if q.get("repeatable") else 1.0\n        _write_record_numeric("QUESTS", q, "generator_level", lvl)\n        _write_record_numeric("QUESTS", q, "character_xp_reward", axis_gain("character", lvl, workload * repeat_mult))\n        _write_record_numeric("QUESTS", q, "reward_soul_xp", axis_gain("soul", lvl, workload * repeat_mult))\n        _write_record_numeric("QUESTS", q, "reward_stat_progress", axis_gain("stat", lvl, workload * repeat_mult))\n        if "reward_profession_xp" in q or q.get("reward_profession") or q.get("specialist_tool_type"):\n            _write_record_numeric("QUESTS", q, "reward_profession_xp", axis_gain("profession", lvl, max(1.0, workload * .75) * repeat_mult))\n        if "reward_tool_xp" in q or q.get("reward_tool_type") or q.get("specialist_tool_type"):\n            _write_record_numeric("QUESTS", q, "reward_tool_xp", axis_gain("tool", lvl, max(1.0, workload * .70) * repeat_mult))\n\n        # v0.30.24: hybrydowy system waluty questów.\n        # Ważne, ręcznie zaprojektowane questy mogą mieć chronioną kwotę.\n        # Wszystkie pozostałe dalej używają automatycznego Generator Core.\n        manual_coins = q.get("manual_currency_reward_coins")\n        if manual_coins is not None:\n            coins = clamp(int(manual_coins), 0, SAFE_INT)\n        else:\n            coins = quest_currency_for_stage(lvl, workload, bool(q.get("repeatable")), str(qid))\n        _write_record_numeric("QUESTS", q, "reward_silver", min(SAFE_INT, coins))\n        _write_record_numeric("QUESTS", q, "reward_gold", 0)\n        _write_record_numeric("QUESTS", q, "reward_mithril", 0)\n\n\ndef _skill_kind_fields(skill: dict, unlock: int, sid: str) -> None:\n    kind = str(skill.get("kind") or "damage")\n    scale = 1.0 + unlock / 400.0\n    _write_record_numeric("CLASS_SKILLS", skill, "cooldown", clamp(int(round((3.0 + 5.0 * stable_unit(sid + \':cd\')) * (1.0 + unlock / 900.0))), 2, 12))\n    magical = str(skill.get("scale", "")).lower() in ("intelligence", "willpower", "magic") or kind in ("heal", "group_heal", "drain")\n    _write_record_numeric("CLASS_SKILLS", skill, "mana", 0 if not magical else max(1, int(round(4 + unlock * .055 + 8 * stable_unit(sid + \':mana\')))))\n    if kind in ("damage", "aoe", "aoe_damage", "drain", "execute"):\n        _write_record_numeric("CLASS_SKILLS", skill, "mult", round((1.05 + .55 * scale) * stable_jitter(sid + \':mult\', .09), 4))\n    if kind == "boost":\n        _write_record_numeric("CLASS_SKILLS", skill, "boost", round(clamp(1.12 + unlock / 1300.0 + stable_unit(sid) * .10, 1.12, 1.55), 4))\n        _write_record_numeric("CLASS_SKILLS", skill, "duration", clamp(int(round(6 + unlock / 45.0)), 6, 16))\n    if kind == "guard":\n        _write_record_numeric("CLASS_SKILLS", skill, "guard", max(2, int(round(3 + unlock / 16.0))))\n    if kind in ("heal", "group_heal"):\n        base = .16 + unlock / 1800.0\n        if kind == "group_heal":\n            base *= .78\n        _write_record_numeric("CLASS_SKILLS", skill, "heal_pct", round(clamp(base, .12, .42), 4))\n    if kind == "drain":\n        _write_record_numeric("CLASS_SKILLS", skill, "drain_pct", round(clamp(.18 + unlock / 2400.0, .18, .36), 4))\n    if kind == "execute":\n        _write_record_numeric("CLASS_SKILLS", skill, "execute_mult", round(1.35 + 0.45 * (unlock / MAX_LEVEL) * stable_jitter(sid + \':execute\', .08), 4))\n    if "self_damage" in skill:\n        _write_record_numeric("CLASS_SKILLS", skill, "self_damage", max(1, int(round(2 + unlock / 80.0))))\n    if "self_damage_pct" in skill:\n        _write_record_numeric("CLASS_SKILLS", skill, "self_damage_pct", round(clamp(.025 + unlock / 8000.0, .025, .075), 4))\n\n\n\ndef _generate_skills(ns: dict) -> int:\n    """Balance skill numbers while preserving authored ID/name/unlock/kind/scale exactly."""\n    class_skills = ns.get("CLASS_SKILLS", {}) or {}\n    count = 0\n    for class_name, skills in class_skills.items():\n        for idx, skill in enumerate(skills):\n            count += 1\n            try:\n                unlock = int(skill.get("unlock", 1) or 1)\n            except Exception:\n                unlock = 1\n            balance_level = clamp(unlock, 1, MAX_LEVEL)\n            _write_record_numeric("CLASS_SKILLS", skill, "generator_level", balance_level)\n            _skill_kind_fields(skill, balance_level, str(skill.get("id") or f"{class_name}:{idx}"))\n    return count\n\n\n\n\n\nCLASS_PASSIVE_KIND = {\n    "Wojownik": "physical_damage", "Berserker": "physical_damage", "Łotrzyk": "dodge",\n    "Łowca": "physical_damage", "Mnich": "healing", "Strażnik": "damage_reduction",\n    "Mag": "magic_damage", "Nekromanta": "drain_healing", "Kapłan": "healing",\n    "Czarownik": "magic_damage", "Druid": "healing", "Psionik": "magic_defense",\n}\nRACE_PASSIVE_KIND = {\n    "Człowiek": "stat_xp", "Ogr": "physical_damage", "Elf": "dodge",\n    "Krasnolud": "damage_reduction", "Ork": "max_hp", "Niziołek": "profession_bonus",\n    "Mroczny Elf": "magic_damage", "Gnom": "max_mana", "Smoczy": "all_damage",\n    "Troll": "physical_reduction", "Diablę": "soul_xp", "Aasimar": "magic_defense",\n    "Driada": "healing",\n}\n\ndef _percent_for_identity(identity: str, kind: str, low: float, high: float) -> float:\n    return low + (high-low) * stable_unit(f"{identity}:{kind}:passive")\n\ndef class_passive_profile(class_name: str) -> dict:\n    kind=CLASS_PASSIVE_KIND.get(class_name, "none")\n    if kind == "dodge":\n        value=round(_percent_for_identity(class_name,kind,.035,.055),4)\n    elif kind == "damage_reduction":\n        value=round(_percent_for_identity(class_name,kind,.08,.12),4)\n    elif kind in ("physical_damage","magic_damage","healing","magic_defense"):\n        value=round(_percent_for_identity(class_name,kind,.08,.13),4)\n    elif kind == "drain_healing":\n        value=round(_percent_for_identity(class_name,kind,.11,.17),4)\n    else:\n        value=0.0\n    return {"kind":kind,"value":value}\n\ndef race_passive_profile(race_name: str) -> dict:\n    kind=RACE_PASSIVE_KIND.get(race_name,"none")\n    ranges={\n        "stat_xp":(.08,.12),"physical_damage":(.09,.13),"dodge":(.035,.055),\n        "damage_reduction":(.08,.12),"max_hp":(.08,.13),"profession_bonus":(.02,.04),\n        "magic_damage":(.08,.13),"max_mana":(.10,.16),"all_damage":(.06,.10),\n        "physical_reduction":(.09,.14),"soul_xp":(.08,.13),"magic_defense":(.09,.14),\n        "healing":(.11,.17),\n    }\n    low,high=ranges.get(kind,(0.0,0.0))\n    return {"kind":kind,"value":round(_percent_for_identity(race_name,kind,low,high),4) if high else 0.0}\n\n\ndef passive_text_pl(kind: str, value: float) -> str:\n    pct=int(round(value*100))\n    return {\n        "physical_damage": f"+{pct} procent obrażeń fizycznych",\n        "magic_damage": f"+{pct} procent obrażeń magicznych",\n        "all_damage": f"+{pct} procent wszystkich obrażeń",\n        "healing": f"+{pct} procent mocy leczenia",\n        "drain_healing": f"+{pct} procent leczenia z wysysania życia",\n        "magic_defense": f"+{pct} procent obrony magicznej",\n        "damage_reduction": f"{pct} procent redukcji wszystkich obrażeń",\n        "physical_reduction": f"{pct} procent redukcji obrażeń fizycznych",\n        "dodge": f"+{pct} punktów procentowych uniku",\n        "stat_xp": f"+{pct} procent EXP statystyk",\n        "max_hp": f"+{pct} procent maksymalnego HP",\n        "profession_bonus": f"+{pct} punktów procentowych szansy na bonus profesji",\n        "max_mana": f"+{pct} procent maksymalnej Many",\n        "soul_xp": f"+{pct} procent Soul XP",\n    }.get(kind,"brak")\n\ndef class_passive_text_pl(class_name: str) -> str:\n    p=class_passive_profile(class_name); return passive_text_pl(p["kind"],p["value"])\n\ndef race_passive_text_pl(race_name: str) -> str:\n    p=race_passive_profile(race_name); return passive_text_pl(p["kind"],p["value"])\n\ndef _generate_soul(ns: dict) -> None:\n    """Balance existing Soul bonus values only; never rewrite tiers, thresholds, names or trial gates."""\n    try:\n        max_tier = max(1, int(ns.get("SOUL_MAX_TIER", 40) or 40))\n    except Exception:\n        max_tier = 40\n    if "SOUL_TIER_POWER_BONUSES" in ns:\n        _write_top_sequence(ns, "SOUL_TIER_POWER_BONUSES", (int(round((tier - 1) * 2.2)) for tier in range(1, max_tier + 1)))\n    if "SOUL_TIER_CLASS_BONUS_PERCENT" in ns:\n        _write_top_sequence(ns, "SOUL_TIER_CLASS_BONUS_PERCENT", (int(round(4 + (tier - 1) * .65)) for tier in range(1, max_tier + 1)))\n    if "SOUL_TIER_DODGE_BONUS" in ns:\n        _write_top_sequence(ns, "SOUL_TIER_DODGE_BONUS", (round(min(.05, .005 + (tier - 1) * .0012), 4) for tier in range(1, max_tier + 1)))\n    if "SOUL_TIER_GUARDIAN_REDUCTION" in ns:\n        _write_top_sequence(ns, "SOUL_TIER_GUARDIAN_REDUCTION", (int(round(2 + (tier - 1) * .45)) for tier in range(1, max_tier + 1)))\n    milestones = tuple(ns.get("SOUL_MILESTONE_TIERS", ()) or ())\n    spec = ns.get("SOUL_MILESTONE_SPECIALIZATION_BONUS")\n    if isinstance(spec, dict):\n        for tier in list(spec):\n            if tier in milestones:\n                _write_top_map_numeric(ns, "SOUL_MILESTONE_SPECIALIZATION_BONUS", tier, int(round(int(tier) * .45)))\n    dodge = ns.get("SOUL_MILESTONE_DODGE_BONUS")\n    if isinstance(dodge, dict):\n        for tier in list(dodge):\n            if tier in milestones:\n                _write_top_map_numeric(ns, "SOUL_MILESTONE_DODGE_BONUS", tier, round(min(.05, int(tier) * .0012), 4))\n    guard = ns.get("SOUL_MILESTONE_GUARDIAN_REDUCTION")\n    if isinstance(guard, dict):\n        for tier in list(guard):\n            if tier in milestones:\n                _write_top_map_numeric(ns, "SOUL_MILESTONE_GUARDIAN_REDUCTION", tier, int(round(int(tier) * .30)))\n\n\n\n\ndef _generate_class_set_bonuses(ns: dict) -> None:\n    """Rebalance values inside the authored set-bonus structure; never change owned stats/effects."""\n    table = ns.get("CLASS_SET_BONUSES")\n    if not isinstance(table, dict):\n        return\n    for cname, entry in table.items():\n        if not isinstance(entry, dict):\n            continue\n        stats = entry.get("stats")\n        if isinstance(stats, dict):\n            for stat in list(stats):\n                _write_class_set_numeric(entry, "stats", 3 + int(stable_unit(f"{cname}:set:stat:{stat}") * 4), leaf=stat)\n        if "damage" in entry:\n            _write_class_set_numeric(entry, "damage", round(1.06 + .10 * stable_unit(f"{cname}:set:damage"), 4))\n        if "defense" in entry:\n            _write_class_set_numeric(entry, "defense", round(1.08 + .18 * stable_unit(f"{cname}:set:defense"), 4))\n        if "vitality" in entry:\n            _write_class_set_numeric(entry, "vitality", round(1.10 + .22 * stable_unit(f"{cname}:set:vitality"), 4))\n\n\n\n\ndef _generate_class_race_numeric(ns: dict) -> None:\n    """Only the numeric Soul-weapon base may be balanced; class/race identity stays authored."""\n    classes = list(ns.get("CLASSES", []))\n    new_classes = []\n    for row in classes:\n        if len(row) >= 4:\n            name, ctype, weapon, _old_base, *rest = row\n            base = 7 + (1 if stable_unit(str(name) + \':weapon\') > .72 else 0)\n            new_classes.append((name, ctype, weapon, base, *rest))\n        else:\n            new_classes.append(row)\n    _write_classes_weapon_bases(ns, new_classes)\n\n    # RACES, CLASS_STARTING_STAT_BONUSES and all description text are authored and untouched.\n\n\n\ndef _rewrite_atlases(ns: dict, item_levels: dict[str, int]) -> None:\n    """Numeric-only v0.30.18: atlas/unlock thresholds are authored semantics and are never rewritten."""\n    return None\n\n\n\n\ndef _rewrite_area_targets(ns: dict, room_levels: dict[str, int], mob_levels: dict[str, int]) -> None:\n    """Update only numeric target-power telemetry; never rewrite area/gate requirements."""\n    targets = ns.get("EXP_AREA_TARGET_POWER")\n    zone_map = ns.get("EXP_ZONE_AREA_ID", {}) or {}\n    rooms = ns.get("ROOMS", {}) or {}\n    if not isinstance(targets, dict):\n        return\n    by_area = defaultdict(list)\n    for rid, room in rooms.items():\n        area = zone_map.get(room.get("zone"))\n        if area and rid in room_levels:\n            by_area[area].append(room_levels[rid])\n    mob_area_values = defaultdict(list)\n    for rid, mid in (ns.get("MOB_SPAWNS", []) or []):\n        room = rooms.get(rid, {})\n        area = zone_map.get(room.get("zone"))\n        if area and str(mid) in mob_levels:\n            mob_area_values[area].append(mob_levels[str(mid)])\n    for area in list(targets):\n        values = mob_area_values.get(area) or by_area.get(area)\n        if values:\n            value = min(values)\n        elif area == "trening":\n            value = 1\n        else:\n            value = 1 + int(stable_unit(f"area:{area}") * (MAX_LEVEL - 1))\n        _write_top_map_numeric(ns, "EXP_AREA_TARGET_POWER", area, value)\n\n\n\n\ndef runtime_room_level(room_id: str, room: dict, rooms: dict | None = None) -> int:\n    """Assign numeric balance stage to runtime rooms without creating gameplay gates."""\n    room_id = str(room_id or "room")\n    room = room or {}\n    lvl = semantic_floor_level(room)\n    if lvl is None:\n        text = f"{room_id} {room.get(\'zone\',\'\')} {room.get(\'name\',\'\')}".lower()\n        m = re.search(r"(?:floor|level|poziom|pietro|piętro)[_ -]*(\\d{1,5})", text)\n        if m and any(k in text for k in ("crypt", "krypt", "astral", "tower", "wież", "fortress", "twierdz", "dungeon", "loch", "mine", "kopal")):\n            lvl = int(m.group(1))\n    if lvl is None and rooms:\n        frontier = re.fullmatch(r"v0130_frontier_([a-z]+)_(\\d{2})_(\\d{2})", room_id)\n        if frontier:\n            kind, sx, sy = frontier.groups()\n            gateway = rooms.get(f"v0130_gateway_{kind}", {})\n            base = int(gateway.get("generator_level", 1) or 1)\n            distance = int(sx) + int(sy)\n            span = max(24, min(140, int(round((MAX_LEVEL - base) * 0.45))))\n            lvl = base + int(round((distance / 22.0) * span))\n    if lvl is None and rooms:\n        linked = []\n        for target in (room.get("exits") or {}).values():\n            other = rooms.get(target, {})\n            if other.get("generator_level") is not None:\n                linked.append(int(other["generator_level"]))\n        if linked:\n            lvl = max(1, min(linked))\n    if lvl is None:\n        lvl = 1 + int(stable_unit(f"runtime-room:{room_id}") * (MAX_LEVEL - 1))\n    lvl = clamp(int(lvl), 1, MAX_LEVEL)\n    _write_record_numeric("ROOMS", room, "generator_level", lvl)\n    return lvl\n\n\n\n\nNUMERIC_SKILL_FIELDS = {\n    "generator_level", "cooldown", "mana", "mult", "boost", "duration", "guard",\n    "heal_pct", "drain_pct", "execute_mult", "self_damage", "self_damage_pct",\n}\nNUMERIC_ITEM_FIELDS = {\n    "generator_level", "price", "sell_silver", "sell_gold", "sell_mithril", "defense",\n    "affix_amount", "heal", "mana", "soul_xp",\n}\nNUMERIC_MOB_FIELDS = {\n    "generator_level", "v019_stage", "max_hp", "base_max_hp", "damage",\n    "character_xp_reward", "class_xp_reward", "soul_reward", "stat_reward",\n    "silver", "gold", "mithril",\n}\nNUMERIC_QUEST_FIELDS = {\n    "generator_level", "character_xp_reward", "reward_soul_xp", "reward_stat_progress",\n    "reward_profession_xp", "reward_tool_xp", "reward_silver", "reward_gold", "reward_mithril",\n}\nNUMERIC_RECIPE_FIELDS = {"generator_level", "xp", "profession_xp", "tool_xp"}\n\n\n# v0.30.19: explicit, auditable write whitelist.\n# Design chooses WHAT exists; Generator Core may only decide HOW MUCH.\nGENERATOR_WRITE_WHITELIST = {\n    "ROOMS": frozenset({"generator_level"}),\n    "MOB_TEMPLATES": frozenset(NUMERIC_MOB_FIELDS),\n    "ITEMS": frozenset(NUMERIC_ITEM_FIELDS),\n    "QUESTS": frozenset(NUMERIC_QUEST_FIELDS),\n    "CLASS_SKILLS": frozenset(NUMERIC_SKILL_FIELDS),\n    "CRAFT_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),\n    "COOK_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),\n    "ALCHEMY_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),\n    "JEWELCRAFT_RECIPES": frozenset(NUMERIC_RECIPE_FIELDS),\n}\nGENERATOR_NESTED_VALUE_WHITELIST = {\n    "MOB_TEMPLATES": frozenset({"drops"}),\n    "ITEMS": frozenset({"stats", "properties", "rune_stats", "rune_properties"}),\n}\nGENERATOR_TOP_LEVEL_VALUE_WHITELIST = frozenset({\n    "SOUL_TIER_POWER_BONUSES",\n    "SOUL_TIER_CLASS_BONUS_PERCENT",\n    "SOUL_TIER_DODGE_BONUS",\n    "SOUL_TIER_GUARDIAN_REDUCTION",\n    "SOUL_MILESTONE_SPECIALIZATION_BONUS",\n    "SOUL_MILESTONE_DODGE_BONUS",\n    "SOUL_MILESTONE_GUARDIAN_REDUCTION",\n    "CLASS_SET_BONUSES",\n    "CLASSES",\n    "EXP_AREA_TARGET_POWER",\n})\n\n\n_GENERATOR_WHITELIST_WRITE_COUNT = 0\n\ndef _write_record_numeric(domain: str, record: dict, field: str, value) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    allowed = GENERATOR_WRITE_WHITELIST.get(domain, ())\n    if field not in allowed:\n        raise RuntimeError(f"Generator whitelist denied write: {domain}.{field}")\n    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):\n        raise RuntimeError(f"Generator whitelist denied non-numeric value: {domain}.{field}")\n    record[field] = value\n    _GENERATOR_WHITELIST_WRITE_COUNT += 1\n\n\ndef _write_nested_numeric(domain: str, record: dict, field: str, leaf, value) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    if field not in GENERATOR_NESTED_VALUE_WHITELIST.get(domain, ()):\n        raise RuntimeError(f"Generator whitelist denied nested write: {domain}.{field}")\n    mapping = record.get(field)\n    if not isinstance(mapping, dict) or leaf not in mapping:\n        raise RuntimeError(f"Generator whitelist denied new nested key: {domain}.{field}.{leaf}")\n    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):\n        raise RuntimeError(f"Generator whitelist denied non-numeric nested value: {domain}.{field}.{leaf}")\n    mapping[leaf] = value\n    _GENERATOR_WHITELIST_WRITE_COUNT += 1\n\n\ndef _write_top_sequence(ns: dict, key: str, values) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    if key not in GENERATOR_TOP_LEVEL_VALUE_WHITELIST or key not in ns:\n        raise RuntimeError(f"Generator whitelist denied top-level write: {key}")\n    old = ns[key]\n    new = tuple(values) if isinstance(old, tuple) else list(values) if isinstance(old, list) else values\n    if isinstance(old, (tuple, list)) and len(new) != len(old):\n        raise RuntimeError(f"Generator whitelist denied shape change: {key}")\n    if isinstance(new, (tuple, list)) and any(\n        not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(float(v))\n        for v in new\n    ):\n        raise RuntimeError(f"Generator whitelist denied non-numeric sequence: {key}")\n    ns[key] = new\n    _GENERATOR_WHITELIST_WRITE_COUNT += len(new) if isinstance(new, (tuple, list)) else 1\n\n\ndef _write_top_map_numeric(ns: dict, key: str, leaf, value) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    if key not in GENERATOR_TOP_LEVEL_VALUE_WHITELIST:\n        raise RuntimeError(f"Generator whitelist denied top-map write: {key}")\n    mapping = ns.get(key)\n    if not isinstance(mapping, dict) or leaf not in mapping:\n        raise RuntimeError(f"Generator whitelist denied new top-map key: {key}.{leaf}")\n    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):\n        raise RuntimeError(f"Generator whitelist denied non-numeric top-map value: {key}.{leaf}")\n    mapping[leaf] = value\n    _GENERATOR_WHITELIST_WRITE_COUNT += 1\n\n\ndef _write_class_set_numeric(entry: dict, field: str, value, leaf=None) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    if field == "stats":\n        stats = entry.get("stats")\n        if not isinstance(stats, dict) or leaf not in stats:\n            raise RuntimeError(f"Generator whitelist denied class-set stat key: {leaf}")\n        if not isinstance(value, (int, float)) or isinstance(value, bool):\n            raise RuntimeError(f"Generator whitelist denied class-set stat value: {leaf}")\n        stats[leaf] = value\n    elif field in ("damage", "defense", "vitality") and field in entry:\n        if not isinstance(value, (int, float)) or isinstance(value, bool):\n            raise RuntimeError(f"Generator whitelist denied class-set value: {field}")\n        entry[field] = value\n    else:\n        raise RuntimeError(f"Generator whitelist denied class-set write: {field}")\n    _GENERATOR_WHITELIST_WRITE_COUNT += 1\n\n\ndef _write_classes_weapon_bases(ns: dict, new_rows) -> None:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    old_rows = list(ns.get("CLASSES", ()) or ())\n    new_rows = list(new_rows)\n    if len(old_rows) != len(new_rows):\n        raise RuntimeError("Generator whitelist denied CLASSES shape change")\n    for old, new in zip(old_rows, new_rows):\n        if len(old) != len(new):\n            raise RuntimeError("Generator whitelist denied CLASSES row shape change")\n        for idx, (a, b) in enumerate(zip(old, new)):\n            if idx == 3:\n                if not isinstance(b, (int, float)) or isinstance(b, bool):\n                    raise RuntimeError("Generator whitelist denied non-numeric Soul weapon base")\n            elif a != b:\n                raise RuntimeError(f"Generator whitelist denied CLASSES semantic write at index {idx}")\n    ns["CLASSES"] = new_rows\n    _GENERATOR_WHITELIST_WRITE_COUNT += len(new_rows)\n\n\ndef _freeze_semantic(value):\n    if isinstance(value, dict):\n        return tuple(sorted((str(k), _freeze_semantic(v)) for k, v in value.items()))\n    if isinstance(value, (list, tuple)):\n        return tuple(_freeze_semantic(v) for v in value)\n    if isinstance(value, set):\n        return tuple(sorted((_freeze_semantic(v) for v in value), key=repr))\n    return value\n\n\ndef _protected_record(record: dict, numeric_fields: set[str], numeric_map_fields=()) -> tuple:\n    result = []\n    for key, value in record.items():\n        if key in numeric_fields:\n            continue\n        if key in numeric_map_fields and isinstance(value, dict):\n            result.append((str(key), tuple(sorted(map(str, value.keys())))))\n        elif key == "drops" and isinstance(value, dict):\n            # Drop identity is semantic; probabilities are numeric balance.\n            result.append(("drops", tuple(sorted(map(str, value.keys())))))\n        else:\n            result.append((str(key), _freeze_semantic(value)))\n    return tuple(sorted(result))\n\n\n\ndef _class_row_whitelist_projection(row):\n    """Only CLASSES[row][3] (Soul-weapon numeric base) may change."""\n    seq = list(row) if isinstance(row, (list, tuple)) else [row]\n    if len(seq) >= 4:\n        seq[3] = "<GENERATOR_NUMERIC>"\n    return _freeze_semantic(seq)\n\n\ndef _class_set_whitelist_projection(table):\n    """Protect class-set identity; allow only existing numeric values."""\n    out = {}\n    for cname, entry in (table or {}).items():\n        if not isinstance(entry, dict):\n            out[str(cname)] = _freeze_semantic(entry)\n            continue\n        row = {}\n        for key, value in entry.items():\n            if key == "stats" and isinstance(value, dict):\n                row[key] = tuple(sorted((str(stat), "<GENERATOR_NUMERIC>") for stat in value))\n            elif key in ("damage", "defense", "vitality"):\n                row[key] = "<GENERATOR_NUMERIC>"\n            else:\n                row[key] = _freeze_semantic(value)\n        out[str(cname)] = tuple(sorted(row.items()))\n    return _freeze_semantic(out)\n\n\ndef _value_container_whitelist_projection(value):\n    """Keep container shape/keys, hide only numeric values."""\n    if isinstance(value, dict):\n        return tuple(sorted((str(k), "<GENERATOR_NUMERIC>") for k in value))\n    if isinstance(value, (list, tuple)):\n        return (type(value).__name__, len(value), tuple("<GENERATOR_NUMERIC>" for _ in value))\n    return "<GENERATOR_NUMERIC>"\n\n\ndef generator_whitelist_fingerprint(ns: dict) -> str:\n    """Cheap shape fingerprint; safe setters enforce every Generator write."""\n    protected = [("TOP_LEVEL_KEYS", tuple(sorted(str(k) for k in ns.keys())))]\n    # Top-level write domains may change values only, never shape/keys.\n    protected.append(("CLASSES_SHAPE", tuple(len(row) for row in (ns.get("CLASSES", ()) or ()))))\n    protected.append(("CLASS_SET_KEYS", tuple(\n        (str(cname),\n         tuple(sorted(str(k) for k in entry.keys())) if isinstance(entry, dict) else ("<NON_DICT>",),\n         tuple(sorted(str(k) for k in (entry.get("stats") or {}).keys())) if isinstance(entry, dict) and isinstance(entry.get("stats"), dict) else ())\n        for cname, entry in (ns.get("CLASS_SET_BONUSES", {}) or {}).items()\n    )))\n    protected.append(("EXP_AREA_KEYS", tuple(sorted(str(k) for k in (ns.get("EXP_AREA_TARGET_POWER", {}) or {}).keys()))))\n    for key in sorted(GENERATOR_TOP_LEVEL_VALUE_WHITELIST - {"CLASSES", "CLASS_SET_BONUSES", "EXP_AREA_TARGET_POWER"}):\n        value = ns.get(key)\n        if isinstance(value, dict):\n            shape = ("dict", tuple(sorted(str(k) for k in value.keys())))\n        elif isinstance(value, (list, tuple)):\n            shape = (type(value).__name__, len(value))\n        else:\n            shape = (type(value).__name__,)\n        protected.append((key, shape))\n    return hashlib.sha256(repr(tuple(protected)).encode("utf-8")).hexdigest()\n\n\n\n\n\ndef _is_generator_number(value) -> bool:\n    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))\n\n\ndef _validate_record_whitelist_numbers(ns: dict, errors: list[str]) -> int:\n    checked = 0\n    for table_name, allowed in GENERATOR_WRITE_WHITELIST.items():\n        table = ns.get(table_name, {}) or {}\n        if not isinstance(table, dict):\n            errors.append(f"whitelist table {table_name} is not dict")\n            continue\n        nested = GENERATOR_NESTED_VALUE_WHITELIST.get(table_name, ())\n        for rid, record in table.items():\n            if not isinstance(record, dict):\n                continue\n            for field in allowed:\n                if field in record:\n                    checked += 1\n                    if not _is_generator_number(record[field]):\n                        errors.append(f"non-numeric whitelisted value {table_name}.{rid}.{field}")\n            for field in nested:\n                mapping = record.get(field)\n                if mapping is None:\n                    continue\n                if not isinstance(mapping, dict):\n                    errors.append(f"whitelist nested field {table_name}.{rid}.{field} is not dict")\n                    continue\n                for leaf, value in mapping.items():\n                    checked += 1\n                    if not _is_generator_number(value):\n                        errors.append(f"non-numeric whitelisted value {table_name}.{rid}.{field}.{leaf}")\n    return checked\n\n\ndef generator_whitelist_validate(ns: dict, before_fingerprint: str) -> dict:\n    after = generator_whitelist_fingerprint(ns)\n    errors = []\n    if before_fingerprint != after:\n        errors.append("Generator Core changed a protected whitelist shape/key")\n    return {\n        "version": GENERATOR_VERSION,\n        "enforced": True,\n        "passed": not errors,\n        "fingerprint_before": before_fingerprint,\n        "fingerprint_after": after,\n        "numeric_values_checked": int(_GENERATOR_WHITELIST_WRITE_COUNT),\n        "error_count": len(errors),\n        "errors": errors,\n        "record_whitelist": {k: tuple(sorted(v)) for k, v in GENERATOR_WRITE_WHITELIST.items()},\n        "nested_value_whitelist": {k: tuple(sorted(v)) for k, v in GENERATOR_NESTED_VALUE_WHITELIST.items()},\n        "top_level_value_whitelist": tuple(sorted(GENERATOR_TOP_LEVEL_VALUE_WHITELIST)),\n    }\n\n\n\ndef semantic_fingerprint(ns: dict) -> str:\n    """Hash all authored semantics that Generator Core is forbidden to change."""\n    protected = []\n    protected.append(("CLASSES", tuple(tuple(row[:3]) for row in ns.get("CLASSES", ()))))\n    protected.append(("RACES", _freeze_semantic(ns.get("RACES", ()))))\n    protected.append(("CLASS_DESCRIPTIONS", _freeze_semantic(ns.get("CLASS_DESCRIPTIONS", {}))))\n    protected.append(("CLASS_STARTING_STAT_BONUSES", _freeze_semantic(ns.get("CLASS_STARTING_STAT_BONUSES", {}))))\n    constants = (\n        "SOUL_MAX_LEVEL", "SOUL_MAX_TIER", "SOUL_TIER_THRESHOLDS", "TIER2_LEVEL", "TIER3_LEVEL", "TIER4_LEVEL", "TIER5_LEVEL",\n        "SOUL_SKILL_UNLOCK_LEVELS", "SOUL_MILESTONE_TIERS", "SOUL_MILESTONE_NAMES",\n        "PROFESSION_RANK_THRESHOLDS", "PROFESSION_MAX_RANK", "BLACKSMITHING_RANK_THRESHOLDS", "BLACKSMITHING_MAX_RANK",\n        "TOOL_TIER_THRESHOLDS", "TOOL_MAX_TIER", "ASTRAL_MIN_SOUL_LEVEL", "MYTHIC_CRYPT_MIN_SOUL_LEVEL", "MYTHIC_ASTRAL_MIN_SOUL_LEVEL",\n    )\n    protected.append(("CONSTANTS", tuple((k, _freeze_semantic(ns.get(k))) for k in constants)))\n    protected.append(("SKILLS", tuple(\n        (str(cname), tuple(_protected_record(s, NUMERIC_SKILL_FIELDS) for s in rows))\n        for cname, rows in (ns.get("CLASS_SKILLS", {}) or {}).items()\n    )))\n    protected.append(("ITEMS", tuple(\n        (str(iid), _protected_record(item, NUMERIC_ITEM_FIELDS, ("stats", "properties", "rune_stats", "rune_properties")))\n        for iid, item in (ns.get("ITEMS", {}) or {}).items()\n    )))\n    protected.append(("MOBS", tuple(\n        (str(mid), _protected_record(mob, NUMERIC_MOB_FIELDS))\n        for mid, mob in (ns.get("MOB_TEMPLATES", {}) or {}).items()\n    )))\n    protected.append(("QUESTS", tuple(\n        (str(qid), _protected_record(q, NUMERIC_QUEST_FIELDS))\n        for qid, q in (ns.get("QUESTS", {}) or {}).items()\n    )))\n    recipes = []\n    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):\n        recipes.append((table_name, tuple(\n            (str(rid), _protected_record(recipe, NUMERIC_RECIPE_FIELDS))\n            for rid, recipe in (ns.get(table_name, {}) or {}).items()\n        )))\n    protected.append(("RECIPES", tuple(recipes)))\n    protected.append(("NPCS", _freeze_semantic(ns.get("NPCS", {}))))\n    protected.append(("MOB_SPAWNS", _freeze_semantic(ns.get("MOB_SPAWNS", ()))))\n    protected.append(("ROOMS", tuple(\n        (str(rid), _protected_record(room, {"generator_level"}))\n        for rid, room in (ns.get("ROOMS", {}) or {}).items()\n    )))\n    protected.append(("ATLASES", _freeze_semantic({\n        "ORE_ATLAS_LEVELS": ns.get("ORE_ATLAS_LEVELS", {}),\n        "ORE_MINE_FLOOR_MINIMUMS": ns.get("ORE_MINE_FLOOR_MINIMUMS", {}),\n        "WOOD_ATLAS_ROOM_MIN_LEVELS": ns.get("WOOD_ATLAS_ROOM_MIN_LEVELS", {}),\n        "HERB_ATLAS_ROOM_MIN_LEVELS": ns.get("HERB_ATLAS_ROOM_MIN_LEVELS", {}),\n    })))\n    protected.append(("EXP_AREAS", _freeze_semantic(ns.get("EXP_AREAS", ()))))\n    set_structure = {}\n    for cname, entry in (ns.get("CLASS_SET_BONUSES", {}) or {}).items():\n        if isinstance(entry, dict):\n            set_structure[str(cname)] = {\n                "keys": tuple(sorted(map(str, entry.keys()))),\n                "stat_keys": tuple(sorted(map(str, (entry.get("stats") or {}).keys()))) if isinstance(entry.get("stats"), dict) else (),\n            }\n    protected.append(("CLASS_SET_STRUCTURE", _freeze_semantic(set_structure)))\n    return hashlib.sha256(repr(tuple(protected)).encode("utf-8")).hexdigest()\n\ndef validate(ns: dict) -> dict:\n    errors = []\n    mobs = ns.get("MOB_TEMPLATES", {})\n    items = ns.get("ITEMS", {})\n    quests = ns.get("QUESTS", {})\n    skills = ns.get("CLASS_SKILLS", {})\n    recipes = sum((len(ns.get(name, {}) or {}) for name in ("CRAFT_RECIPES","COOK_RECIPES","ALCHEMY_RECIPES","JEWELCRAFT_RECIPES")), 0)\n    for mid, t in mobs.items():\n        lvl = int(t.get("generator_level", 0) or 0)\n        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"mob level {mid}")\n        rank = mob_rank(t)\n        if int(t.get("max_hp",0) or 0) != mob_hp(lvl, rank): errors.append(f"mob hp {mid}")\n        if int(t.get("damage",0) or 0) != mob_damage(lvl, rank): errors.append(f"mob damage {mid}")\n        if int(t.get("character_xp_reward",0) or 0) != axis_gain("character", lvl, RANK_REWARD.get(rank,1.0)): errors.append(f"mob charxp {mid}")\n        if int(t.get("class_xp_reward",0) or 0) != axis_gain("class", lvl, RANK_REWARD.get(rank,1.0)): errors.append(f"mob classxp {mid}")\n        if int(t.get("soul_reward",0) or 0) != axis_gain("soul", lvl, RANK_REWARD.get(rank,1.0)): errors.append(f"mob soulxp {mid}")\n        if int(t.get("silver",0) or 0) != currency_for_stage(lvl, rank): errors.append(f"mob currency {mid}")\n    for iid, item in items.items():\n        lvl = int(item.get("generator_level",0) or 0)\n        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"item level {iid}")\n        if int(item.get("price",0) or 0) <= 0: errors.append(f"item price {iid}")\n    for qid, q in quests.items():\n        lvl = int(q.get("generator_level",0) or 0)\n        if not 1 <= lvl <= MAX_LEVEL: errors.append(f"quest level {qid}")\n        if int(q.get("character_xp_reward",0) or 0) <= 0: errors.append(f"quest charxp {qid}")\n        reward = int(q.get("reward_silver",0) or 0)\n        manual = q.get("manual_currency_reward_coins")\n        if manual is not None:\n            if reward != clamp(int(manual), 0, SAFE_INT):\n                errors.append(f"quest manual currency changed {qid}: {reward}!={manual}")\n        elif reward < 1001:\n            errors.append(f"quest currency {qid}")\n        if int(q.get("reward_gold",0) or 0) != 0 or int(q.get("reward_mithril",0) or 0) != 0:\n            errors.append(f"quest split currency {qid}")\n    skill_count = 0\n    skill_grid = (1, *range(10, MAX_LEVEL + 1, 10))\n    skill_grid_set = set(skill_grid)\n    for cname, rows in skills.items():\n        unlocks = []\n        per_unlock = defaultdict(int)\n        for s in rows:\n            skill_count += 1\n            try: unlock = int(s.get("unlock",0) or 0)\n            except Exception: unlock = 0\n            unlocks.append(unlock)\n            if not 1 <= unlock <= MAX_LEVEL: errors.append(f"skill level {s.get(\'id\')}")\n            if unlock not in skill_grid_set: errors.append(f"skill off-grid {s.get(\'id\')}:{unlock}")\n            per_unlock[unlock] += 1\n        if unlocks and (min(unlocks) != 1 or max(unlocks) != MAX_LEVEL): errors.append(f"skill span {cname}")\n        for level in skill_grid:\n            if per_unlock.get(level, 0) != 3:\n                errors.append(f"skill grid {cname}:{level}={per_unlock.get(level,0)} expected=3")\n    for table_name in ("CRAFT_RECIPES","COOK_RECIPES","ALCHEMY_RECIPES","JEWELCRAFT_RECIPES"):\n        for rid, recipe in (ns.get(table_name, {}) or {}).items():\n            lvl = int(recipe.get("generator_level", 0) or 0)\n            if not 1 <= lvl <= MAX_LEVEL: errors.append(f"recipe level {rid}")\n            if int(recipe.get("profession_xp",0) or 0) <= 0: errors.append(f"recipe profession xp {rid}")\n            if int(recipe.get("tool_xp",0) or 0) <= 0: errors.append(f"recipe tool xp {rid}")\n    for fn_name, fn in (("mob_hp", mob_hp),("mob_damage",mob_damage)):\n        vals = [fn(l) for l in range(1, MAX_LEVEL+1)]\n        if any(b < a for a,b in zip(vals, vals[1:])): errors.append(f"nonmonotonic {fn_name}")\n    for axis in AXIS_CURVES:\n        vals = [axis_requirement(axis,l) for l in range(1, MAX_LEVEL+1)]\n        if any(b < a for a,b in zip(vals,vals[1:])): errors.append(f"nonmonotonic {axis}")\n    return {\n        "errors": errors,\n        "error_count": len(errors),\n        "mobs": len(mobs), "items": len(items), "quests": len(quests),\n        "skills": skill_count, "recipes": recipes, "rooms": len(ns.get("ROOMS",{})),\n    }\n\n\n\ndef apply_generator_core(ns: dict) -> dict:\n    global _GENERATOR_WHITELIST_WRITE_COUNT\n    _GENERATOR_WHITELIST_WRITE_COUNT = 0\n    semantic_before = semantic_fingerprint(ns)\n    whitelist_before = generator_whitelist_fingerprint(ns)\n    _generate_soul(ns)\n    _generate_class_race_numeric(ns)\n    _generate_class_set_bonuses(ns)\n    room_levels = _graph_room_levels(ns.get("ROOMS", {}) or {})\n    mob_levels = _mob_levels(ns, room_levels)\n    _generate_mobs(ns, mob_levels)\n    item_levels = _item_levels(ns, mob_levels)\n    _generate_items(ns, item_levels)\n    recipe_count = _generate_recipes(ns, item_levels)\n    _generate_quests(ns, mob_levels, item_levels)\n    skill_count = _generate_skills(ns)\n    # Numeric-only/no-op for authored thresholds.\n    _rewrite_atlases(ns, item_levels)\n    _rewrite_area_targets(ns, room_levels, mob_levels)\n\n    semantic_after = semantic_fingerprint(ns)\n    whitelist_audit = generator_whitelist_validate(ns, whitelist_before)\n    audit = validate(ns)\n    semantic_ok = semantic_before == semantic_after\n    audit["semantic_fingerprint_before"] = semantic_before\n    audit["semantic_fingerprint_after"] = semantic_after\n    audit["semantic_preserved"] = semantic_ok\n    audit["whitelist_enforced"] = True\n    audit["whitelist_passed"] = bool(whitelist_audit.get("passed"))\n    audit["whitelist_audit"] = whitelist_audit\n    if not semantic_ok:\n        audit["errors"].append("Generator Core changed protected authored semantics")\n    if not whitelist_audit.get("passed"):\n        audit["errors"].extend(whitelist_audit.get("errors", []))\n    audit["error_count"] = len(audit["errors"])\n    audit["recipe_count_generated"] = recipe_count\n    audit["skill_count_generated"] = skill_count\n    audit["numeric_only"] = True\n    ns["GENERATOR_CORE_AUDIT"] = audit\n    ns["GENERATOR_CORE_VERSION"] = GENERATOR_VERSION\n    ns["GENERATOR_ROOM_LEVELS"] = room_levels\n    ns["GENERATOR_MOB_LEVELS"] = mob_levels\n    ns["GENERATOR_ITEM_LEVELS"] = item_levels\n    return audit\n\n\n'
generator_core_v027 = _load_embedded_runtime_module('generator_core', _EMBEDDED_GENERATOR_CORE_SOURCE)

_EMBEDDED_WORLD_TOPOLOGY_GENERATOR_SOURCE = '"""Soulbound v0.30.0 Semantic Universal World Topology Generator.\n\nAll non-runtime/static zone topology is generated deterministically from a seed.\nContent records keep semantic identity (room id/name/role), while adjacency is not\ntrusted from hand-authored horizontal exits. Existing procedural systems keep their\nown generated topology. Cross-zone gateways and vertical semantic links are kept as\nanchors so saves, quests and runtime portals remain compatible.\n"""\nfrom __future__ import annotations\n\nfrom collections import defaultdict, deque\nimport hashlib\n\nGENERATOR_VERSION = "0.30.0"\nWORLD_TOPOLOGY_SEED = "soulbound:v0.30.0:semantic-world-topology"\nCARDINAL = ("north", "east", "south", "west")\nDIAGONAL = ("northeast", "southeast", "southwest", "northwest")\nHORIZONTAL = CARDINAL + DIAGONAL\nGENERATED_DIRS = HORIZONTAL\nOPPOSITE = {"north":"south", "south":"north", "east":"west", "west":"east", "northeast":"southwest", "southwest":"northeast", "northwest":"southeast", "southeast":"northwest", "up":"down", "down":"up"}\n\n# v0.30.0: generator ma tworzyć logiczny świat, nie losową sieć.\n# Tożsamość lokacji pozostaje treścią świata, ale generator przypisuje jej\n# rolę semantyczną i preferuje zgodne sąsiedztwa. Pion jest zarezerwowany\n# wyłącznie dla zachowanych semantycznych schodów/piwnic/wież/portali.\ndef _room_role(rid: str, room: dict) -> str:\n    text=(str(rid)+" "+str(room.get("name") or "")).lower()\n    if any(k in text for k in ("gate", "brama", "street", "ulica", "lane", "alley", "zauł", "road", "trakt", "path", "szlak", "square", "plac")):\n        return "transit"\n    if any(k in text for k in ("temple", "świąty", "swiaty", "shrine", "kaplic", "cathedral", "katedr")):\n        return "sacred"\n    if any(k in text for k in ("guard", "straż", "straz", "barrack", "koszar", "armory", "zbroj", "watch", "patrol", "training", "arena")):\n        return "guard"\n    if any(k in text for k in ("harbor", "port", "dock", "stoczn", "ship", "pier", "nabrze", "warehouse", "magazyn", "ropewalk", "powroź")):\n        return "harbor"\n    if any(k in text for k in ("market", "targ", "inn", "karcz", "bakery", "piek", "pharmacy", "apte", "healer", "uzdrow", "kitchen", "kuchn")):\n        return "commerce"\n    if any(k in text for k in ("forge", "kuź", "kuz", "workshop", "warsztat", "jeweler", "jubiler", "tailor", "krawiec", "carpenter", "ciesiel", "leather", "kalet", "mason", "kamien", "potter", "garncar")):\n        return "craft"\n    if any(k in text for k in ("library", "bibliot", "archive", "archiw", "school", "szko", "courier", "kurier", "cartograph", "kartograf", "office", "biuro")):\n        return "civic"\n    if any(k in text for k in ("guild", "gild")):\n        return "guild"\n    if any(k in text for k in ("house", "dom", "residential", "miesz", "well", "studn")):\n        return "residential"\n    if any(k in text for k in ("cave", "jask", "crypt", "krypt", "sewer", "kanał", "kanal", "basement", "piwn", "dungeon", "loch", "mine", "kopal")):\n        return "underground"\n    if any(k in text for k in ("mountain", "gór", "gor", "summit", "szczyt", "ice", "lodow")):\n        return "highland"\n    if any(k in text for k in ("forest", "las", "grove", "gaj", "meadow", "łąk", "lak", "river", "rzek", "lake", "jezior", "swamp", "bag", "desert", "pust")):\n        return "wilderness"\n    return "general"\n\n_ROLE_COMPAT = {\n    "transit": {"transit":10,"civic":9,"commerce":9,"guard":9,"residential":9,"craft":8,"harbor":8,"sacred":8,"guild":8,"general":8,"wilderness":6,"underground":3,"highland":3},\n    "sacred": {"sacred":10,"transit":9,"civic":8,"residential":6,"guard":6,"guild":5,"commerce":4,"craft":3,"harbor":3,"general":6,"underground":6,"wilderness":5,"highland":3},\n    "guard": {"guard":10,"transit":9,"civic":8,"guild":7,"residential":6,"commerce":6,"craft":6,"harbor":7,"general":7,"sacred":6,"wilderness":6,"underground":6,"highland":6},\n    "harbor": {"harbor":10,"transit":9,"craft":9,"commerce":8,"guard":7,"civic":6,"residential":5,"general":7,"wilderness":6,"sacred":3,"guild":5,"underground":4,"highland":2},\n    "commerce": {"commerce":10,"transit":9,"craft":9,"residential":8,"civic":7,"harbor":8,"guard":6,"guild":6,"general":7,"sacred":4,"wilderness":4,"underground":3,"highland":2},\n    "craft": {"craft":10,"transit":8,"commerce":9,"harbor":9,"residential":6,"guard":6,"civic":6,"guild":6,"general":7,"sacred":3,"wilderness":5,"underground":5,"highland":5},\n    "civic": {"civic":10,"transit":9,"sacred":8,"guard":8,"commerce":7,"guild":8,"residential":7,"craft":6,"harbor":6,"general":7,"wilderness":4,"underground":4,"highland":3},\n    "guild": {"guild":10,"transit":9,"civic":8,"guard":8,"commerce":7,"craft":7,"residential":5,"harbor":5,"sacred":5,"general":7,"wilderness":5,"underground":5,"highland":5},\n    "residential": {"residential":10,"transit":9,"commerce":8,"civic":7,"craft":6,"guard":6,"sacred":6,"guild":5,"harbor":5,"general":7,"wilderness":4,"underground":3,"highland":2},\n    "underground": {"underground":10,"transit":5,"guard":6,"sacred":6,"craft":5,"general":6,"wilderness":6,"highland":7},\n    "highland": {"highland":10,"wilderness":8,"transit":5,"guard":6,"craft":5,"underground":7,"general":6},\n    "wilderness": {"wilderness":10,"highland":8,"underground":7,"transit":6,"guard":6,"craft":5,"general":7},\n    "general": {"general":8,"transit":8,"civic":7,"commerce":7,"guard":7,"craft":7,"harbor":7,"sacred":6,"guild":7,"residential":7,"wilderness":7,"underground":6,"highland":6},\n}\n\ndef _role_compat(a_role: str, b_role: str) -> int:\n    return int(_ROLE_COMPAT.get(a_role, {}).get(b_role, _ROLE_COMPAT.get(b_role, {}).get(a_role, 5)))\n\n\ndef _unit(text: str) -> float:\n    raw = hashlib.sha256(str(text).encode("utf-8")).digest()\n    return int.from_bytes(raw[:8], "big") / float((1 << 64) - 1)\n\n\ndef _is_native_procedural(room: dict) -> bool:\n    # v0.28 regions already own their complete topology. Other runtime/infinite\n    # dungeons are materialized outside the static ROOMS registry.\n    return bool(room.get("procedural_region_v028") or room.get("procedural_dynamic"))\n\n\ndef _normalize_cross_zone_edges(rooms):\n    """Make every static cross-zone edge geometrically reciprocal.\n\n    The semantic zone relationship is preserved, but direction slots are chosen\n    deterministically. This removes legacy cases such as south one way / west back.\n    """\n    pairs={}\n    for a,room in rooms.items():\n        za=str(room.get("zone") or "Bez strefy")\n        for d,b in list((room.get("exits") or {}).items()):\n            if b not in rooms: continue\n            zb=str(rooms[b].get("zone") or "Bez strefy")\n            if za==zb: continue\n            key=tuple(sorted((a,b)))\n            pairs.setdefault(key,[]).append((a,d,b))\n    for (x,y),records in sorted(pairs.items()):\n        # Remove only direct x<->y links; unrelated exits keep their slots.\n        old_xy=[]; old_yx=[]\n        for d,t in list(rooms[x].setdefault("exits",{}).items()):\n            if t==y: old_xy.append(d); del rooms[x]["exits"][d]\n        for d,t in list(rooms[y].setdefault("exits",{}).items()):\n            if t==x: old_yx.append(d); del rooms[y]["exits"][d]\n        # Preserve true vertical semantics whenever possible.\n        preferred=[]\n        for d in old_xy:\n            preferred.append(d)\n        for d in old_yx:\n            if d in OPPOSITE: preferred.append(OPPOSITE[d])\n        ordered=[]\n        for d in preferred + list(HORIZONTAL) + ["up","down"]:\n            if d in OPPOSITE and d not in ordered: ordered.append(d)\n        chosen=None\n        for d in ordered:\n            rev=OPPOSITE[d]\n            if _free(rooms[x],d) and _free(rooms[y],rev):\n                chosen=(d,rev); break\n        if not chosen:\n            raise RuntimeError(f"No reciprocal direction slots for cross-zone edge {x}<->{y}")\n        rooms[x]["exits"][chosen[0]]=y\n        rooms[y]["exits"][chosen[1]]=x\n\n\ndef _zone_groups(rooms):\n    groups = defaultdict(list)\n    for rid, room in rooms.items():\n        if _is_native_procedural(room):\n            continue\n        groups[str(room.get("zone") or "Bez strefy")].append(rid)\n    return groups\n\n\ndef _free(room, direction):\n    return direction not in room.setdefault("exits", {})\n\n\ndef _connect(rooms, a, da, b, db):\n    if not _free(rooms[a], da) or not _free(rooms[b], db):\n        return False\n    rooms[a]["exits"][da] = b\n    rooms[b]["exits"][db] = a\n    return True\n\n\ndef _internal_neighbors(rooms, rid, zone):\n    out=[]\n    for target in rooms[rid].get("exits", {}).values():\n        if target in rooms and str(rooms[target].get("zone") or "Bez strefy") == zone:\n            out.append(target)\n    return out\n\n\ndef _components(rooms, ids, zone):\n    # Only reciprocal preserved links form a pre-connected component. One-way\n    # historical links do not count, because the generated world must be fully\n    # navigable in both directions.\n    ids=set(ids); seen=set(); comps=[]\n    for start in sorted(ids):\n        if start in seen: continue\n        q=[start]; seen.add(start); comp=[]\n        while q:\n            cur=q.pop(); comp.append(cur)\n            for d,nxt in rooms[cur].get("exits",{}).items():\n                if nxt not in ids or nxt not in rooms: continue\n                if str(rooms[nxt].get("zone") or "Bez strefy") != zone: continue\n                rev=OPPOSITE.get(d)\n                if not rev or rooms[nxt].get("exits",{}).get(rev)!=cur: continue\n                if nxt not in seen:\n                    seen.add(nxt); q.append(nxt)\n        comps.append(sorted(comp))\n    return comps\n\n\ndef _component_slots(rooms, comp):\n    slots=[]\n    for rid in comp:\n        for d in GENERATED_DIRS:\n            if _free(rooms[rid], d): slots.append((rid,d))\n    return slots\n\n\ndef _candidate_links(rooms, left, right, seed):\n    candidates=[]\n    right_set=set(right)\n    for a, da in _component_slots(rooms,left):\n        db=OPPOSITE[da]\n        for b in right_set:\n            if _free(rooms[b],db):\n                role_score=_role_compat(_room_role(a,rooms[a]), _room_role(b,rooms[b]))\n                score=role_score*10.0 + _unit(f"{seed}:link:{a}:{da}:{b}")\n                candidates.append((score,a,da,b,db))\n    candidates.sort(reverse=True)\n    return candidates\n\n\ndef _choose_root(zone, ids, rooms):\n    preferred={\n        "Miasto Dusz":"square", "Gildia Dusz":"guild_hall", "Wioska Górska":"mountain_village",\n        "Podziemia":"temple_basement", "Kanały Pod Miastem":"sewer_entrance",\n    }.get(zone)\n    if preferred in ids: return preferred\n    # Prefer a room with external anchors, then deterministic hash.\n    ranked=[]\n    for rid in ids:\n        ext=sum(1 for t in rooms[rid].get("exits",{}).values() if t in rooms and rooms[t].get("zone")!=zone)\n        ranked.append((-ext, _unit(f"{WORLD_TOPOLOGY_SEED}:root:{zone}:{rid}"), rid))\n    ranked.sort()\n    return ranked[0][2]\n\n\ndef _generate_zone(rooms, zone, ids):\n    ids=list(ids)\n    if len(ids) <= 1:\n        for rid in ids:\n            rooms[rid]["topology_generated_v0281"] = True\n            rooms[rid]["topology_generated_v030"] = True\n            rooms[rid]["world_role"] = _room_role(rid, rooms[rid])\n        return {"rooms":len(ids),"links":0,"loops":0,"root":ids[0] if ids else None}\n\n    seed=f"{WORLD_TOPOLOGY_SEED}:{zone}"\n    # Keep cross-zone gateways and all vertical semantic links. Horizontal links\n    # inside this zone are deliberately discarded and rebuilt from the seed.\n    for rid in ids:\n        old=dict(rooms[rid].get("exits",{})); new={}\n        for d,target in old.items():\n            if d in ("up","down"):\n                new[d]=target\n            elif target not in rooms:\n                new[d]=target\n            elif str(rooms[target].get("zone") or "Bez strefy") != zone:\n                new[d]=target\n        rooms[rid]["exits"]=new\n\n    # Normalize preserved internal vertical links. A vertical pair must be exact\n    # up<->down. Conflicting legacy one-way links are dropped and the affected\n    # rooms are reconnected horizontally by the generated topology.\n    for rid in sorted(ids):\n        for d,target in list(rooms[rid].get("exits",{}).items()):\n            if d not in ("up","down") or target not in rooms: continue\n            if str(rooms[target].get("zone") or "Bez strefy") != zone: continue\n            rev=OPPOSITE[d]\n            rooms[target].setdefault("exits",{})\n            back=rooms[target]["exits"].get(rev)\n            if back==rid:\n                continue\n            if back is None:\n                rooms[target]["exits"][rev]=rid\n            else:\n                # Another semantic vertical pair owns this shaft/stair slot.\n                del rooms[rid]["exits"][d]\n\n    root=_choose_root(zone,ids,rooms)\n    comps=_components(rooms,ids,zone)\n    # Put root component first, remaining components in deterministic order.\n    comps.sort(key=lambda c:(0 if root in c else 1, _unit(f"{seed}:component:{\'|\'.join(c)}")))\n    connected=list(comps[0])\n    links=0\n    for comp in comps[1:]:\n        # Find a generated cardinal link from any already-connected node into this component.\n        left=connected\n        cand=_candidate_links(rooms,left,comp,seed)\n        if not cand:\n            raise RuntimeError(f"Topology generator has no free cardinal slots in zone {zone!r} for component {comp[:3]}")\n        _,a,da,b,db=cand[0]\n        if not _connect(rooms,a,da,b,db):\n            raise RuntimeError(f"Topology generator failed to connect {a} and {b}")\n        links+=1; connected.extend(comp)\n\n    # Add deterministic loops, aiming at roughly one extra link per 6 rooms.\n    loop_target=max(1,len(ids)//6) if len(ids)>=5 else 0\n    loops=0\n    pair_candidates=[]\n    ordered=sorted(ids)\n    for i,a in enumerate(ordered):\n        for b in ordered[i+1:]:\n            if b in rooms[a].get("exits",{}).values(): continue\n            for da in GENERATED_DIRS:\n                db=OPPOSITE[da]\n                if _free(rooms[a],da) and _free(rooms[b],db):\n                    compat=_role_compat(_room_role(a,rooms[a]), _room_role(b,rooms[b]))\n                    pair_candidates.append((compat*10.0+_unit(f"{seed}:loop:{a}:{da}:{b}"),a,da,b,db))\n    pair_candidates.sort(reverse=True)\n    for _,a,da,b,db in pair_candidates:\n        if loops>=loop_target: break\n        if _connect(rooms,a,da,b,db): loops+=1\n\n    # Annotate generated layout metadata.\n    # BFS depth is useful for accessible map/debug output and future content generation.\n    depth={root:0}; q=deque([root])\n    while q:\n        cur=q.popleft()\n        for nxt in _internal_neighbors(rooms,cur,zone):\n            if nxt not in depth:\n                depth[nxt]=depth[cur]+1; q.append(nxt)\n    if len(depth)!=len(ids):\n        missing=sorted(set(ids)-set(depth))[:10]\n        raise RuntimeError(f"Generated zone {zone!r} disconnected: {missing}")\n    for rid in ids:\n        rooms[rid]["topology_generated_v0281"]=True\n        rooms[rid]["topology_generated_v030"]=True\n        rooms[rid]["world_role"]=_room_role(rid,rooms[rid])\n        rooms[rid]["topology_zone_depth"]=depth[rid]\n        rooms[rid]["topology_seed"]=seed\n    return {"rooms":len(ids),"links":links,"loops":loops,"root":root,"max_depth":max(depth.values(),default=0)}\n\n\ndef apply_world_topology(rooms: dict) -> dict:\n    if not isinstance(rooms,dict): raise TypeError("rooms must be a dict")\n    _normalize_cross_zone_edges(rooms)\n    groups=_zone_groups(rooms)\n    zones={}; errors=[]\n    for zone,ids in sorted(groups.items()):\n        try: zones[zone]=_generate_zone(rooms,zone,ids)\n        except Exception as exc: errors.append(f"{zone}: {exc}")\n    # Validate all references and reciprocal generated internal cardinal edges.\n    for rid,room in rooms.items():\n        zone=str(room.get("zone") or "Bez strefy")\n        for d,target in room.get("exits",{}).items():\n            if target not in rooms:\n                # Runtime/infinite/profession dungeon entrances intentionally point\n                # at rooms materialized on demand. Keep the semantic portal.\n                continue\n            if room.get("topology_generated_v0281") and rooms[target].get("topology_generated_v0281") and rooms[target].get("zone")==zone and d in HORIZONTAL:\n                rev=OPPOSITE[d]\n                if rooms[target].get("exits",{}).get(rev)!=rid:\n                    errors.append(f"non-reciprocal {rid}.{d}->{target}")\n    # Global reachability from default spawn; preserves the original cross-zone graph.\n    if "square" in rooms:\n        seen={"square"}; q=deque(["square"])\n        while q:\n            cur=q.popleft()\n            for target in rooms[cur].get("exits",{}).values():\n                if target in rooms and target not in seen:\n                    seen.add(target); q.append(target)\n        missing=set(rooms)-seen\n    else:\n        seen=set(); missing=set(rooms)\n    city=[rid for rid,r in rooms.items() if r.get("zone")=="Miasto Dusz"]\n    city_links=sum(1 for rid in city for t in rooms[rid].get("exits",{}).values() if t in city)//2\n    return {\n        "version":GENERATOR_VERSION,"seed":WORLD_TOPOLOGY_SEED,"zone_count":len(zones),\n        "generated_room_count":sum(v.get("rooms",0) for v in zones.values()),\n        "city_room_count":len(city),"city_internal_links":city_links,\n        "static_reachable_from_square":len(seen),"static_unreachable_without_runtime":len(missing),\n        "zones":zones,"error_count":len(errors),"errors":errors,\n    }\n'
world_topology_generator_v0281 = _load_embedded_runtime_module('world_topology_generator', _EMBEDDED_WORLD_TOPOLOGY_GENERATOR_SOURCE)

_EMBEDDED_DYNAMIC_WORLD_V029_SOURCE = '"""Soulbound v0.29.0 - Dynamic World Events + Boss/Nemesis Generator.\n\nThis module contains deterministic content-generation rules only. Numeric combat\nbalance is delegated to Generator Core through runtime_mob_balance().\n"""\nfrom __future__ import annotations\n\nimport copy\nimport hashlib\nimport random\nimport time\n\nEVENT_ROTATION_SECONDS = 60 * 60\nEVENT_COUNT = 5\nEVENT_KINDS = (\n    ("incursion", "Najazd", "elite", 3),\n    ("rare_pack", "Polowanie na rzadkie bestie", "rare", 2),\n    ("mini_hunt", "Łowy na czempiona", "mini", 1),\n    ("boss_manifestation", "Manifestacja Bossa", "world_boss", 1),\n    ("roaming_elites", "Wędrująca elita", "elite", 2),\n)\n\nBOSS_MECHANICS = (\n    ("blood_drain", "Drenaż życia co kilka kontrataków."),\n    ("ash_curse", "Magiczne przekleństwo częściowo omija obronę."),\n    ("catacomb_echo", "Co kilka kontrataków wyzwala bardzo silne echo."),\n    ("spectral_shift", "Naprzemiennie zmienia typ obrażeń fizyczne/magiczne."),\n    ("necro_regen", "Okresowo odzyskuje część maksymalnego HP."),\n    ("black_flame", "Okresowo używa silnego magicznego płomienia."),\n    ("stellar_storm", "Okresowo wyzwala silną magiczną burzę."),\n    ("giant_crush", "Okresowo wykonuje ciężkie fizyczne miażdżenie."),\n)\n\nELITE_AFFIXES = (\n    ("armored", "Opancerzony: okresowo redukuje otrzymywane obrażenia."),\n    ("vampiric", "Wampiryczny: część zadanych obrażeń leczy przeciwnika."),\n    ("regenerating", "Regenerujący: okresowo odzyskuje HP."),\n    ("ice", "Lodowy: kontrataki zyskują magiczny charakter i większą moc."),\n    ("fire", "Ognisty: kontrataki zyskują magiczny charakter i większą moc."),\n)\n\nEPITHETS = (\n    "Nieugięty", "Pożeracz Dusz", "Zwiastun Końca", "Krwawy", "Astralny",\n    "Bezsenna Groza", "Łamacz Kości", "Władca Popiołu", "Wieczny Łowca",\n    "Pogromca Wędrowców", "Czarny Strażnik", "Ten, Który Powraca",\n)\n\n\ndef _hash_int(seed: str, *parts) -> int:\n    text = ":".join(str(x) for x in (seed,) + parts)\n    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)\n\n\ndef event_slot(now=None) -> int:\n    now = time.time() if now is None else float(now)\n    return int(now // EVENT_ROTATION_SECONDS)\n\n\ndef _eligible_rooms(rooms: dict, mob_spawns, mob_templates: dict):\n    by_room = {}\n    for room_id, template_id in mob_spawns:\n        room = rooms.get(str(room_id))\n        template = mob_templates.get(str(template_id))\n        if not isinstance(room, dict) or not isinstance(template, dict):\n            continue\n        # Safe hubs / utility-only rooms are excluded implicitly by requiring a real hostile spawn.\n        if template.get("auto_aggro") is True:\n            # Still valid; world policy will force generated variants to passive.\n            pass\n        stage = max(1, min(400, int(room.get("generator_level", room.get("recommended_mastery", 1)) or 1)))\n        by_room.setdefault(str(room_id), {"stage": stage, "templates": []})["templates"].append(str(template_id))\n    return [(rid, meta) for rid, meta in by_room.items() if meta["templates"]]\n\n\ndef active_events(rooms: dict, mob_spawns, mob_templates: dict, world_seed: str, now=None):\n    now = time.time() if now is None else float(now)\n    slot = event_slot(now)\n    eligible = _eligible_rooms(rooms, mob_spawns, mob_templates)\n    if not eligible:\n        return tuple()\n    result = []\n    used = set()\n    for index in range(EVENT_COUNT):\n        kind, title, rank, count = EVENT_KINDS[index % len(EVENT_KINDS)]\n        rng = random.Random(_hash_int(world_seed, "v029-event", slot, index, kind))\n        choices = [row for row in eligible if row[0] not in used] or eligible\n        room_id, meta = choices[rng.randrange(len(choices))]\n        used.add(room_id)\n        bases = tuple(meta["templates"])\n        result.append({\n            "type": kind,\n            "title": title,\n            "rank": rank,\n            "count": count,\n            "room_id": room_id,\n            "stage": int(meta["stage"]),\n            "base_templates": bases,\n            "slot": slot,\n            "token": f"{slot}:{kind}:{room_id}",\n            "expires_at": (slot + 1) * EVENT_ROTATION_SECONDS,\n        })\n    return tuple(result)\n\n\ndef _rank_stage(stage: int, rank: str) -> int:\n    offsets = {"normal": 0, "elite": 4, "rare": 8, "mini": 14, "boss": 20, "world_boss": 26}\n    return max(1, min(400, int(stage) + offsets.get(str(rank), 0)))\n\n\ndef generated_name(base_name: str, seed: str, role: str = "event") -> str:\n    epithet = EPITHETS[_hash_int(seed, role, base_name) % len(EPITHETS)]\n    if role == "nemesis":\n        return f"{base_name}, {epithet} — NEMESIS"\n    if role == "boss":\n        return f"{base_name}, {epithet}"\n    return f"{epithet} {base_name}"\n\n\ndef build_event_template(event: dict, index: int, mob_templates: dict, generator_core, world_seed: str):\n    bases = tuple(event.get("base_templates") or ())\n    if not bases:\n        return None, None\n    pick = _hash_int(world_seed, event["token"], index, "base") % len(bases)\n    base_id = bases[pick]\n    base = mob_templates.get(base_id)\n    if not isinstance(base, dict):\n        return None, None\n    rank = str(event.get("rank") or "normal")\n    stage = _rank_stage(int(event.get("stage", 1) or 1), rank)\n    template_id = f"v029_event_{event[\'slot\']}_{event[\'type\']}_{index}_{hashlib.sha1(base_id.encode()).hexdigest()[:8]}"\n    if template_id in mob_templates:\n        return template_id, mob_templates[template_id]\n    data = copy.deepcopy(base)\n    data["base_template"] = base_id\n    data["v029_dynamic_event"] = True\n    data["v029_event_token"] = event["token"]\n    data["generator_level"] = stage\n    data["auto_aggro"] = False\n    data["stationary_mob"] = rank in ("mini", "boss", "world_boss")\n    if rank == "elite":\n        data["name"] = generated_name(str(base.get("name", base_id)), event["token"] + str(index), "elite")\n        affix, text = ELITE_AFFIXES[_hash_int(world_seed, event["token"], index, "affix") % len(ELITE_AFFIXES)]\n        data["elite_affix"] = affix\n        data["elite_affix_text"] = text\n    elif rank == "rare":\n        data["name"] = generated_name(str(base.get("name", base_id)), event["token"] + str(index), "rare")\n        data["rare_mob"] = True\n    else:\n        data["name"] = generated_name(str(base.get("name", base_id)), event["token"] + str(index), "boss")\n        if rank == "mini":\n            data["mini_boss"] = True\n            affix, text = ELITE_AFFIXES[_hash_int(world_seed, event["token"], index, "mini-affix") % len(ELITE_AFFIXES)]\n            data["elite_affix"] = affix\n            data["elite_affix_text"] = "Czempion: " + text\n        else:\n            mechanic, text = BOSS_MECHANICS[_hash_int(world_seed, event["token"], index, "mechanic") % len(BOSS_MECHANICS)]\n            data["boss_mechanic"] = mechanic\n            data["boss_mechanic_text"] = "Proceduralny boss v0.29. " + text + " Fazy 75/50/25%."\n            if rank == "world_boss":\n                data["world_boss"] = True\n                data["v029_world_boss"] = True\n    generator_core.runtime_mob_balance(template_id, data, stage, rank=rank)\n    mob_templates[template_id] = data\n    return template_id, data\n\n\ndef nemesis_name(base_name: str, account_id: int, player_name: str, rank: int) -> str:\n    seed = f"nemesis:{account_id}:{player_name}:{rank}:{base_name}"\n    return generated_name(base_name, seed, "nemesis")\n\n\ndef build_nemesis_template(record, mob_templates: dict, generator_core):\n    base_id = str(record["base_template_id"])\n    base = mob_templates.get(base_id)\n    if not isinstance(base, dict):\n        return None, None\n    rank_no = max(1, int(record["rank"]))\n    if rank_no >= 7:\n        rank = "world_boss"\n    elif rank_no >= 4:\n        rank = "boss"\n    elif rank_no >= 2:\n        rank = "mini"\n    else:\n        rank = "rare"\n    stage = max(1, min(400, int(record["level"])))\n    template_id = f"v029_nemesis_{int(record[\'account_id\'])}_{rank_no}_{hashlib.sha1(base_id.encode()).hexdigest()[:8]}"\n    if template_id in mob_templates:\n        return template_id, mob_templates[template_id]\n    data = copy.deepcopy(base)\n    data["base_template"] = base_id\n    data["name"] = str(record["nemesis_name"])\n    data["v029_nemesis"] = True\n    data["v029_nemesis_owner_account_id"] = int(record["account_id"])\n    data["v029_nemesis_rank"] = rank_no\n    data["generator_level"] = stage\n    data["auto_aggro"] = False\n    data["stationary_mob"] = True\n    if rank in ("boss", "world_boss"):\n        mechanic, text = BOSS_MECHANICS[_hash_int(str(record["account_id"]), base_id, rank_no, "nemesis-mechanic") % len(BOSS_MECHANICS)]\n        data["boss_mechanic"] = mechanic\n        data["boss_mechanic_text"] = f"Nemesis rangi {rank_no}. {text} Fazy 75/50/25%."\n        data["world_boss"] = rank == "world_boss"\n    elif rank == "mini":\n        data["mini_boss"] = True\n        affix, text = ELITE_AFFIXES[_hash_int(str(record["account_id"]), base_id, rank_no, "nemesis-affix") % len(ELITE_AFFIXES)]\n        data["elite_affix"] = affix\n        data["elite_affix_text"] = f"Nemesis rangi {rank_no}: {text}"\n    else:\n        data["rare_mob"] = True\n    generator_core.runtime_mob_balance(template_id, data, stage, rank=rank)\n    mob_templates[template_id] = data\n    return template_id, data\n'
dynamic_world_v029 = _load_embedded_runtime_module('dynamic_world_v029', _EMBEDDED_DYNAMIC_WORLD_V029_SOURCE)

_EMBEDDED_WORLD_LOGIC_VALIDATOR_SOURCE = '"""Soulbound v0.30.0 Semantic World Logic Validator.\n\nThe topology may be procedural, but geography must remain understandable.\nThis validator checks semantic gateway rules, vertical movement semantics,\nworld reachability, reciprocal navigation and deterministic topology output.\n"""\nfrom __future__ import annotations\n\nfrom collections import defaultdict, deque\nimport hashlib\nimport json\n\nVERSION = "0.30.0"\nHORIZONTAL = ("north","east","south","west","northeast","southeast","southwest","northwest")\nOPPOSITE = {\n    "north":"south","south":"north","east":"west","west":"east",\n    "northeast":"southwest","southwest":"northeast",\n    "northwest":"southeast","southeast":"northwest",\n    "up":"down","down":"up",\n}\n\n\ndef _norm(text):\n    return str(text or "").casefold()\n\n\ndef zone_family(zone: str) -> str:\n    z=_norm(zone)\n    if any(k in z for k in ("miasto dusz","gildia dusz","pracownia kartografa")):\n        return "urban"\n    if any(k in z for k in ("przedmieścia","przedmiescia","wioska","osada","posterunek","obóz straży","oboz strazy","przystań","przystan")):\n        return "settlement"\n    if any(k in z for k in ("kanały","kanaly","podziemia","krypt","jaskini","jaskinie","nekropolia","katakumb","kopal")):\n        return "underground"\n    if any(k in z for k in ("góry","gory","lodowe","twierdza gigant")):\n        return "highland"\n    if any(k in z for k in ("popielne","rozbite niebo","pustki","korona świata","korona swiata","rubież końca","rubiez konca")):\n        return "endgame"\n    if any(k in z for k in ("próba","proba","arena","archiwum otchłani","archiwum otchlani","katedra tysiąca","katedra tysiaca","kuźnia pierwszych","kuznia pierwszych","labirynt wiecznych","pałac bezimiennej","palac bezimiennej")):\n        return "instance"\n    if "proceduralny region:" in z:\n        return "expedition"\n    if any(k in z for k in ("ocean","wybrzeże","wybrzeze","jezior","dolina rzek")):\n        return "waterland"\n    return "wilderness"\n\n\ndef _gateway_semantic(rid: str, room: dict, direction: str, target_id: str, target: dict) -> bool:\n    """True when a cross-zone edge has a believable semantic transition."""\n    if direction in ("up","down"):\n        return True\n    src=_norm(rid)+" "+_norm(room.get("name"))\n    dst=_norm(target_id)+" "+_norm(target.get("name"))\n    gateway_words=(\n        "gate","brama","harbor","port","pier","molo","road","trakt","path","szlak",\n        "pass","przełęcz","przelecz","bridge","most","entrance","wejście","wejscie",\n        "mouth","wylot","frontier","rubież","rubiez","gateway","portal","archive","archiw",\n        "hall","hala","lobby","warsztat kartograf","cartographer","watchpost","posterunek",\n        "camp","obóz","oboz","v0130_gateway","v028_region_gate",\n    )\n    return any(k in src or k in dst for k in gateway_words)\n\n\ndef _reachable(rooms, start):\n    if start not in rooms:\n        return set()\n    seen={start}; q=deque([start])\n    while q:\n        cur=q.popleft()\n        for target in rooms[cur].get("exits",{}).values():\n            if target in rooms and target not in seen:\n                seen.add(target); q.append(target)\n    return seen\n\n\ndef topology_fingerprint(rooms):\n    payload=[]\n    for rid in sorted(rooms):\n        exits=rooms[rid].get("exits",{}) or {}\n        payload.append((rid,tuple(sorted((str(k),str(v)) for k,v in exits.items()))))\n    raw=json.dumps(payload,ensure_ascii=False,separators=(",",":"))\n    return hashlib.sha256(raw.encode("utf-8")).hexdigest()\n\n\ndef validate_world_logic(rooms: dict) -> dict:\n    errors=[]; warnings=[]; cross=[]; vertical=[]\n    if not isinstance(rooms,dict):\n        return {"version":VERSION,"error_count":1,"errors":["ROOMS is not dict"]}\n\n    # References and reciprocal navigation for every static edge.\n    for rid,room in rooms.items():\n        exits=room.get("exits",{}) or {}\n        for direction,target_id in exits.items():\n            if target_id not in rooms:\n                # Runtime/lazy destination; validated by its own materializer.\n                continue\n            target=rooms[target_id]\n            if direction in OPPOSITE:\n                reverse=OPPOSITE[direction]\n                if target.get("exits",{}).get(reverse)!=rid:\n                    # Some explicit gauntlet finales remain one-way by design; require a\n                    # global return path instead of pretending the exact edge is reciprocal.\n                    if not (room.get("procedural_dynamic") or target.get("procedural_dynamic")):\n                        warnings.append(f"one-way {rid}.{direction}->{target_id}")\n            z1=str(room.get("zone") or "Bez strefy")\n            z2=str(target.get("zone") or "Bez strefy")\n            if direction in ("up","down"):\n                vertical.append((rid,direction,target_id))\n            if z1!=z2:\n                cross.append((rid,direction,target_id,z1,z2))\n                f1,f2=zone_family(z1),zone_family(z2)\n                semantic_gateway=_gateway_semantic(rid,room,direction,target_id,target)\n                # Granice naturalnych biomów (np. łąka -> rzeka -> dzicz) mogą\n                # przechodzić bez sztucznej bramy. Twarda semantyczna brama jest\n                # wymagana, gdy opuszczamy/wchodzimy do huba miejskiego.\n                if (f1=="urban") != (f2=="urban") and not semantic_gateway:\n                    errors.append(f"urban boundary without semantic gateway: {rid}.{direction}->{target_id} ({z1}->{z2})")\n                # Miasto nie może być bezpośrednim sąsiadem gór/endgame. Nawet\n                # prawdziwa brama miejska ma prowadzić najpierw do traktu/przedmieść.\n                if f1=="urban" and f2 in {"highland","endgame"} and direction not in ("up","down"):\n                    errors.append(f"urban direct jump to {f2}: {rid}.{direction}->{target_id}")\n                if f2=="urban" and f1 in {"highland","endgame"} and direction not in ("up","down"):\n                    errors.append(f"{f1} direct jump to urban: {rid}.{direction}->{target_id}")\n\n    # v0.30 generator nie używa up/down jako GENERATED_DIRS. Każde pionowe\n    # przejście obecne tutaj pochodzi więc z semantycznej tożsamości świata\n    # (schody, piwnica, wieża, krypta, jaskinia, portal) albo z generatora\n    # dedykowanej instancji, a nie z losowego łączenia topologii.\n\n    reachable=_reachable(rooms,"square")\n    if len(reachable)!=len(rooms):\n        missing=sorted(set(rooms)-reachable)\n        errors.append(f"unreachable from square: {len(missing)} rooms; sample {missing[:10]}")\n\n    # Every static room must have some route back to the hub. Reverse-graph BFS.\n    rev=defaultdict(list)\n    for rid,room in rooms.items():\n        for target in room.get("exits",{}).values():\n            if target in rooms: rev[target].append(rid)\n    can_return=set()\n    if "square" in rooms:\n        can_return={"square"}; q=deque(["square"])\n        while q:\n            cur=q.popleft()\n            for source in rev.get(cur,[]):\n                if source not in can_return:\n                    can_return.add(source); q.append(source)\n    if len(can_return)!=len(rooms):\n        missing=sorted(set(rooms)-can_return)\n        errors.append(f"cannot return to square: {len(missing)} rooms; sample {missing[:10]}")\n\n    city=[rid for rid,r in rooms.items() if r.get("zone")=="Miasto Dusz"]\n    city_bad=[]\n    for rid in city:\n        for d,t in rooms[rid].get("exits",{}).items():\n            if t not in rooms: continue\n            z2=rooms[t].get("zone")\n            if z2=="Miasto Dusz": continue\n            if not _gateway_semantic(rid,rooms[rid],d,t,rooms[t]):\n                city_bad.append(f"{rid}.{d}->{t}")\n    if city_bad:\n        errors.append("city exits without gateway semantics: "+", ".join(city_bad[:10]))\n\n    families=defaultdict(int)\n    for r in rooms.values(): families[zone_family(r.get("zone"))]+=1\n    return {\n        "version":VERSION,\n        "room_count":len(rooms),\n        "reachable_from_square":len(reachable),\n        "returnable_to_square":len(can_return),\n        "cross_zone_edges":len(cross),\n        "vertical_edges":len(vertical),\n        "city_rooms":len(city),\n        "zone_family_room_counts":dict(families),\n        "topology_fingerprint":topology_fingerprint(rooms),\n        "warning_count":len(warnings),\n        "warnings":warnings,\n        "error_count":len(errors),\n        "errors":errors,\n    }\n'
world_logic_validator_v030 = _load_embedded_runtime_module('world_logic_validator', _EMBEDDED_WORLD_LOGIC_VALIDATOR_SOURCE)

VERSION = "0.30.45"
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
MAX_CHARACTERS_PER_ACCOUNT = 12

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
# 1000 srebra = 1 złoto.
# 1 000 000 złota = 1 mithril.
# Zatem 1 mithril = 1 000 000 000 srebra.
SILVER_PER_GOLD = 1000
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
PROFESSION_XP_GAIN_MULTIPLIER = 4
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

def v0190_log_curve(value, anchors):
    """v0.27 compatibility adapter for historical curve call sites.

    The old anchor Y values are deliberately ignored. X coordinates are used only
    as ordinal/range metadata so legacy systems can remain wired while Generator
    Core owns every active numeric result.
    """
    # Resolve a stable semantic identity without trusting the historical values.
    identity = "legacy-curve"
    for _name, _obj in globals().items():
        if _obj is anchors and isinstance(_name, str) and (_name.startswith("V019_") or _name.startswith("V020_") or _name.startswith("V021_") or _name.startswith("V022_")):
            identity = _name
            break
    try:
        xs = [max(1, int(round(float(x)))) for x, _y in anchors]
        maximum = max(xs) if xs else 400
    except Exception:
        maximum = 400
    raw = max(1, int(round(float(value))))
    # Real 1-400 axes keep their stage. Short ordinal systems (e.g. ranks 1-10)
    # are stretched through the same 1-400 Generator Core space.
    stage = generator_core_v027.clamp(raw, 1, 400) if maximum >= 300 else generator_core_v027.stage_from_index(raw, max(1, maximum))

    exact = {
        "V019_CLASS_REQ": lambda: generator_core_v027.axis_requirement("class", stage),
        "V019_SOUL_REQ": lambda: generator_core_v027.axis_requirement("soul", stage),
        "V019_SKILL_REQ": lambda: generator_core_v027.axis_requirement("skill", stage),
        "V019_PROF_REQ": lambda: generator_core_v027.axis_requirement("profession", stage),
        "V019_TOOL_REQ": lambda: generator_core_v027.axis_requirement("tool", stage),
        "V019_STAT_REQ": lambda: generator_core_v027.axis_requirement("stat", stage),
        "V019_SKILL_GAIN": lambda: generator_core_v027.axis_gain("skill", stage),
        "V019_PROF_GAIN": lambda: generator_core_v027.axis_gain("profession", stage),
        "V019_TOOL_GAIN": lambda: generator_core_v027.axis_gain("tool", stage),
        "V019_CLASS_KILL_NORMAL": lambda: generator_core_v027.axis_gain("class", stage, 1.0),
        "V019_CLASS_KILL_BOSS": lambda: generator_core_v027.axis_gain("class", stage, generator_core_v027.RANK_REWARD["boss"]),
        "V019_SOUL_KILL_NORMAL": lambda: generator_core_v027.axis_gain("soul", stage, 1.0),
        "V019_SOUL_KILL_BOSS": lambda: generator_core_v027.axis_gain("soul", stage, generator_core_v027.RANK_REWARD["boss"]),
        "V019_STAT_KILL_NORMAL": lambda: generator_core_v027.axis_gain("stat", stage, 1.0),
        "V019_STAT_KILL_BOSS": lambda: generator_core_v027.axis_gain("stat", stage, generator_core_v027.RANK_REWARD["boss"]),
        "V019_COIN_KILL_NORMAL": lambda: generator_core_v027.currency_for_stage(stage, "normal"),
        "V019_COIN_KILL_BOSS": lambda: generator_core_v027.currency_for_stage(stage, "boss"),
        "V019_HP_NORMAL": lambda: generator_core_v027.mob_hp(stage, "normal"),
        "V019_DAMAGE_NORMAL": lambda: generator_core_v027.mob_damage(stage, "normal"),
        "V019_QUEST_COIN": lambda: generator_core_v027.system_reward(stage, "quest"),
        "V019_ECONOMY_SINK": lambda: generator_core_v027.system_cost(stage, "economy"),
        "V019_RESOURCE_SALE": lambda: generator_core_v027.resource_sale_for_stage(stage),
    }
    if identity in exact:
        return min(V019_SAFE_INT, max(1, int(exact[identity]())))
    upper = identity.upper()
    if "HP" in upper:
        result = generator_core_v027.mob_hp(stage, "boss" if "BOSS" in upper else "normal")
    elif "DAMAGE" in upper or "DMG" in upper:
        result = generator_core_v027.mob_damage(stage, "boss" if "BOSS" in upper else "normal")
    elif "REQ" in upper or "COST" in upper:
        result = generator_core_v027.system_cost(stage, identity)
    elif "SALE" in upper:
        result = generator_core_v027.resource_sale_for_stage(stage)
    else:
        result = generator_core_v027.system_reward(stage, identity)
    return min(V019_SAFE_INT, max(1, int(result)))

V019_CLASS_REQ = ((1,1000),(10,80000),(20,500000),(30,1200000),(40,2500000),(50,5000000),(75,18000000),(100,60000000),(150,600000000),(200,6000000000),(250,60000000000),(300,600000000000),(350,6000000000000),(399,60000000000000))
V019_SOUL_REQ = ((1,500),(10,12000),(20,100000),(30,250000),(40,500000),(50,1000000),(75,6000000),(100,25000000),(150,250000000),(200,2500000000),(250,25000000000),(300,250000000000),(350,2500000000000),(399,25000000000000))
V019_SKILL_REQ = ((1,100),(10,1000),(20,5000),(30,12000),(40,25000),(50,50000),(75,180000),(100,600000),(150,6000000),(200,60000000),(250,500000000),(300,4000000000),(350,25000000000),(399,150000000000))
V019_PROF_REQ = ((1,200),(10,2000),(20,10000),(30,25000),(40,60000),(50,120000),(75,600000),(100,3000000),(150,30000000),(200,300000000),(250,3000000000),(300,30000000000),(350,300000000000),(399,3000000000000))
V019_TOOL_REQ = ((1,200),(10,1000),(20,5000),(30,12000),(40,30000),(50,80000),(75,400000),(100,2000000),(150,20000000),(200,200000000),(250,2000000000),(300,20000000000),(350,200000000000),(399,2000000000000))
V019_STAT_REQ = ((1,100),(10,100),(20,1000),(30,10000),(40,25000),(50,60000),(75,400000),(100,2000000),(150,40000000),(200,800000000),(300,80000000000),(400,8000000000000))
V019_SKILL_GAIN = ((1,30),(10,75),(20,150),(50,800),(100,10000),(200,1000000),(300,50000000),(399,1000000000))
V019_PROF_GAIN = ((1,40),(10,100),(20,250),(50,1500),(100,15000),(150,120000),(200,1000000),(250,8000000),(300,60000000),(350,400000000),(399,6000000000))
V019_TOOL_GAIN = ((1,30),(10,75),(20,180),(50,900),(100,10000),(200,700000),(300,40000000),(399,4000000000))

def v0190_requirement(kind, level):
    # v0.27.0: Generator Core jest jedynym źródłem krzywych progresji.
    return generator_core_v027.axis_requirement(kind, int(level))

def v0190_scaled_gain(raw, level, kind, typical_raw):
    # Stare wartości raw/typical_raw nie sterują już balansem. Sam fakt akcji
    # uruchamia wygenerowaną nagrodę właściwej osi progresji.
    if int(raw or 0) <= 0:
        return 0
    return generator_core_v027.axis_gain(kind, int(level), 1.0)

# Centralny generator walki i ekonomii v0.19.0.
# Nagrody nigdy nie są celowo obniżane poniżej starszych wartości.
# Balans długości gry wynika przede wszystkim z rosnących wymagań.
V019_CLASS_KILL_NORMAL = ((1,100),(5,300),(10,1500),(20,10000),(30,25000),(40,60000),(50,120000),(75,500000),(100,2000000),(150,20000000),(200,200000000),(250,2000000000),(300,20000000000),(350,200000000000),(400,2000000000000))
V019_CLASS_KILL_BOSS = ((1,1500),(10,75000),(20,250000),(30,450000),(40,750000),(50,1250000),(75,4500000),(100,15000000),(150,150000000),(200,1500000000),(250,15000000000),(300,150000000000),(350,1500000000000),(400,15000000000000))
V019_SOUL_KILL_NORMAL = ((1,40),(10,300),(20,2000),(30,4500),(50,20000),(75,90000),(100,400000),(150,4000000),(200,40000000),(250,400000000),(300,4000000000),(350,40000000000),(400,400000000000))
V019_SOUL_KILL_BOSS = ((1,300),(10,6000),(20,50000),(30,90000),(50,250000),(75,1500000),(100,6000000),(150,60000000),(200,600000000),(250,6000000000),(300,60000000000),(350,600000000000),(400,6000000000000))
V019_STAT_KILL_NORMAL = ((1,2),(10,10),(20,50),(30,250),(40,700),(50,3000),(75,20000),(100,100000),(150,2000000),(200,40000000),(250,400000000),(300,4000000000),(350,40000000000),(400,400000000000))
V019_STAT_KILL_BOSS = ((1,20),(10,100),(20,250),(30,1500),(40,5000),(50,15000),(75,100000),(100,500000),(150,10000000),(200,200000000),(250,2000000000),(300,20000000000),(350,200000000000),(400,2000000000000))
V019_COIN_KILL_NORMAL = ((1,10),(10,200),(20,2000),(30,7500),(40,20000),(50,50000),(75,250000),(100,1000000),(150,25000000),(200,500000000),(250,10000000000),(300,200000000000),(350,4000000000000),(400,80000000000000))
V019_COIN_KILL_BOSS = ((1,100),(10,5000),(20,50000),(30,150000),(40,400000),(50,1000000),(75,6000000),(100,30000000),(150,600000000),(200,15000000000),(250,300000000000),(300,6000000000000),(350,120000000000000),(400,2400000000000000))
V019_HP_NORMAL = ((1,80),(10,300),(20,900),(30,1800),(50,5000),(75,12000),(100,25000),(150,100000),(200,500000),(250,2500000),(300,10000000),(350,50000000),(400,200000000))
V019_DAMAGE_NORMAL = ((1,5),(10,15),(20,35),(30,60),(50,120),(75,260),(100,500),(150,1600),(200,5000),(250,16000),(300,50000),(350,160000),(400,500000))
V019_QUEST_COIN = ((1,100),(10,2000),(20,20000),(30,60000),(50,500000),(75,3000000),(100,20000000),(150,500000000),(200,10000000000),(250,200000000000),(300,4000000000000),(350,80000000000000),(400,1600000000000000))
V019_ECONOMY_SINK = ((1,200),(10,5000),(20,20000),(30,70000),(50,500000),(75,3000000),(100,25000000),(150,500000000),(200,10000000000),(250,200000000000),(300,4000000000000),(350,80000000000000),(400,1600000000000000))
V019_RESOURCE_SALE = ((1,5),(10,50),(20,200),(30,500),(50,2500),(75,12000),(100,50000),(150,1000000),(200,20000000),(250,400000000),(300,8000000000),(350,160000000000),(400,3200000000000))

def v0190_mob_stage(template):
    template = template or {}
    # Idempotencja: ten sam template może wystąpić w wielu spawnach. Po
    # pierwszej klasyfikacji etap nie może ponownie rosnąć od HP/damage już
    # zwiększonych przez generator.
    if template.get("v019_stage") is not None:
        return max(1, min(400, int(template.get("v019_stage") or 1)))
    if template.get("crypt_floor") is not None:
        return max(1, min(400, int(template.get("crypt_floor") or 1)))
    if template.get("astral_floor") is not None:
        return max(1, min(400, int(template.get("astral_floor") or 1)))
    if template.get("giant_fortress_floor") is not None:
        return max(1, min(400, int(template.get("giant_fortress_floor") or 1)))
    if template.get("mythic_crypt_floor") is not None:
        floor=max(1,int(template.get("mythic_crypt_floor") or 1))
        return max(130,min(400,120 + floor*2//5))
    if template.get("mythic_astral_floor") is not None:
        floor=max(1,int(template.get("mythic_astral_floor") or 1))
        return max(150,min(400,140 + floor*3//10))
    if template.get("v018_endless_band") is not None:
        band=max(1,int(template.get("v018_endless_band") or 1))
        return max(200,min(400,190 + band*5))
    if template.get("required_mastery") is not None:
        return max(1,min(400,int(template.get("required_mastery") or 1)))
    try:
        if "v0866_mob_progression_power" in globals():
            return max(1,min(400,int(round(v0866_mob_progression_power(template)))))
    except Exception:
        pass
    hp=max(1,float(template.get("max_hp",1) or 1))
    dmg=max(1,float(template.get("damage",1) or 1))
    estimate=max(1.0, ((hp/80.0)**0.45)*8.0 + ((dmg/5.0)**0.55)*4.0)
    return max(1,min(400,int(round(estimate))))

def v0190_mob_rank(template):
    template=template or {}
    if template.get("world_boss") or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss") or template.get("v016_world_boss"):
        return "world_boss"
    if template.get("crypt_boss") or template.get("astral_boss") or template.get("giant_fortress_boss") or template.get("boss_mechanic") or template.get("v018_great_ruin_guardian"):
        return "boss"
    if template.get("mini_boss"):
        return "mini"
    if template.get("rare_mob") or template.get("rare_variant") or template.get("rare_troll") or template.get("v016_legendary_rare"):
        return "rare"
    if template.get("elite_affix"):
        return "elite"
    return "normal"

def v0190_generated_combat_reward(template, kind):
    template = template or {}
    stage = max(1, min(400, int(template.get("generator_level", template.get("v019_stage", 1)) or 1)))
    rank = str(template.get("generator_rank") or generator_core_v027.mob_rank(template))
    intensity = generator_core_v027.RANK_REWARD.get(rank, 1.0)
    if kind == "coins":
        return generator_core_v027.currency_for_stage(stage, rank)
    axis = {"class": "class", "soul": "soul", "stat": "stat", "character": "character"}[kind]
    return generator_core_v027.axis_gain(axis, stage, intensity)

def v0190_combat_reward(template, kind):
    # v0.27.0: brak max(stara, wygenerowana). Ręczne liczby nie wygrywają.
    return v0190_generated_combat_reward(template, kind)

def v0190_apply_combat_template(template):
    """Nadaj wygenerowane statystyki także mobom tworzonym w runtime."""
    if not isinstance(template, dict):
        return template
    stage = template.get("generator_level")
    if stage is None:
        stage = generator_core_v027.semantic_floor_level(template)
    if stage is None:
        for key in ("elite_base_template", "rare_base_template", "base_template", "template_id"):
            base = template.get(key)
            if base and base in globals().get("MOB_TEMPLATES", {}):
                stage = globals()["MOB_TEMPLATES"][base].get("generator_level")
                if stage is not None:
                    break
    if stage is None:
        stage = 1 + int(generator_core_v027.stable_unit(str(template.get("name", "mob"))) * 399)
    stage = max(1, min(400, int(stage)))
    rank = generator_core_v027.mob_rank(template)
    template["generator_level"] = stage
    template["v019_stage"] = stage
    template["max_hp"] = generator_core_v027.mob_hp(stage, rank)
    template["base_max_hp"] = template["max_hp"]
    template["damage"] = generator_core_v027.mob_damage(stage, rank)
    template["character_xp_reward"] = generator_core_v027.axis_gain("character", stage, generator_core_v027.RANK_REWARD.get(rank,1.0))
    template["class_xp_reward"] = generator_core_v027.axis_gain("class", stage, generator_core_v027.RANK_REWARD.get(rank,1.0))
    template["soul_reward"] = generator_core_v027.axis_gain("soul", stage, generator_core_v027.RANK_REWARD.get(rank,1.0))
    template["stat_reward"] = generator_core_v027.axis_gain("stat", stage, generator_core_v027.RANK_REWARD.get(rank,1.0))
    template["silver"] = generator_core_v027.currency_for_stage(stage, rank)
    template["gold"] = 0
    template["mithril"] = 0
    drops=template.get("drops")
    if isinstance(drops,dict) and drops:
        base_chance={"normal":.055,"elite":.09,"rare":.14,"mini":.22,"boss":.34,"world_boss":.48}.get(rank,.055)
        count=max(1,len(drops))
        for item_id in list(drops):
            chance=base_chance*generator_core_v027.stable_jitter(f"{template.get('name','mob')}:{item_id}",.22)/(count**.20)
            drops[item_id]=round(generator_core_v027.clamp(chance,.005,.85),5)
    return template

def v0190_quest_stage(quest):
    quest=quest or {}
    values=[1]
    for key in ("required_soul_level","min_tool_level","min_profession_level","required_mastery","level"):
        try:
            val=int(quest.get(key,0) or 0)
            if val>0: values.append(val)
        except Exception: pass
    target=quest.get("target")
    if target in globals().get("MOB_TEMPLATES",{}):
        values.append(v0190_mob_stage(MOB_TEMPLATES[target]))
    # Liczba wymaganych akcji podnosi wartość zadania, ale nie udaje levelu.
    needed=max(1,int(quest.get("needed",1) or 1))
    base=max(values)
    return max(1,min(400,int(round(base + min(30,math.sqrt(needed)*2)))))

def v0190_quest_currency_reward(quest):
    quest = quest or {}
    if quest.get("generator_level") is not None:
        return max(0, int(quest.get("reward_silver", 0) or 0))
    stage = v0190_quest_stage(quest)
    workload = max(1.0, min(8.0, math.sqrt(max(1, int(quest.get("needed",1) or 1)))))
    return int(round(generator_core_v027.currency_for_stage(stage) * max(2.0, workload) * (.72 if quest.get("repeatable") else 1.0)))

def v0190_quest_stat_reward(quest):
    quest = quest or {}
    if quest.get("generator_level") is not None:
        return max(0, int(quest.get("reward_stat_progress", 0) or 0))
    return generator_core_v027.axis_gain("stat", v0190_quest_stage(quest), 2.0)

def v0190_quest_soul_reward(quest):
    quest = quest or {}
    if quest.get("generator_level") is not None:
        return max(0, int(quest.get("reward_soul_xp", 0) or 0))
    return generator_core_v027.axis_gain("soul", v0190_quest_stage(quest), 2.0)

def v0270_quest_character_reward(quest):
    quest = quest or {}
    if quest.get("generator_level") is not None:
        return max(1, int(quest.get("character_xp_reward", 1) or 1))
    return generator_core_v027.axis_gain("character", v0190_quest_stage(quest), 2.0)

def v0190_economy_sink(stage, category="generic"):
    stage=max(1,min(400,int(stage)))
    mult={"skill":1.0,"equipment":0.60,"service":0.35,"generic":1.0}.get(category,1.0)
    return min(V019_SAFE_INT,max(1,int(round(generator_core_v027.item_price_for_stage(stage)*mult))))

def v0190_resource_stage(item_id, item=None):
    """Poziom ekonomiczny surowca 1-400 z Generator Core."""
    item = item or globals().get("ITEMS", {}).get(item_id, {}) or {}
    if item.get("generator_level") is not None:
        return max(1, min(400, int(item.get("generator_level") or 1)))
    base_id = str(item.get("base_resource_id") or item_id)
    base_item = globals().get("ITEMS", {}).get(base_id, item) or item
    # Ryby mają pełne tabele unlocków, gdy funkcja jest już zdefiniowana.
    try:
        if "fish_unlock_level" in globals() and (base_id in globals().get("FISH_RESOURCE_IDS", set()) or base_id.startswith("fish_400_")):
            return max(1, min(400, int(fish_unlock_level(base_id))))
    except Exception:
        pass
    for key in ("min_tool_level", "min_profession_level", "required_mastery", "level"):
        try:
            val = int(base_item.get(key, 0) or 0)
            if val > 0:
                return max(1, min(400, val))
        except Exception:
            pass
    text = f"{base_id} {base_item.get('desc','')}"
    matches = re.findall(r"(?:level|poziom|lvl)[ _:+-]*(\d{1,4})", text, flags=re.I)
    if not matches:
        matches = re.findall(r"(?:^|_)([1-4]\d{2})(?:_|$)", base_id)
    if matches:
        return max(1, min(400, max(int(x) for x in matches)))
    return 1

def v0190_resource_sale_coins(item_id, item=None):
    item = item or globals().get("ITEMS", {}).get(item_id, {}) or {}
    stage = v0190_resource_stage(item_id, item)
    mult = max(1.0, float(item.get("rare_value_multiplier", 1.0) or 1.0))
    return generator_core_v027.resource_sale_for_stage(stage, mult)

CHARACTER_MAX_LEVEL = 400
STAT_MAX_LEVEL = None  # v0.27.1: statystyki są bez twardego limitu
def character_xp_to_next(level):
    level=max(1,min(CHARACTER_MAX_LEVEL,int(level)))
    if level >= CHARACTER_MAX_LEVEL:
        return 0
    return generator_core_v027.axis_requirement("character", level)

CLASS_MASTERY_MAX_LEVEL = 400
CLASS_MASTERY_XP_BASE = 1000
CLASS_MASTERY_XP_STEP = 250
MULTICLASS_MAX_ACTIVE = 3

def class_mastery_xp_to_next(level):
    level = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(level)))
    if level >= CLASS_MASTERY_MAX_LEVEL:
        return 0
    return v0190_requirement("class", level)

def class_type_for_name(class_name):
    for cname, ctype, weapon, base in CLASSES:
        if cname == class_name:
            return ctype
    return "physical"

SKILL_MAX_LEVEL = 400
SKILL_XP_BASE = 50
# v0.8.64: stara wartość 25 dawała około 50 tysięcy użyć na jeden
# skill 1-200. Mniejszy krok + większe XP za użycie utrzymują długą,
# ale osiągalną progresję.
SKILL_XP_STEP = 8

def skill_xp_to_next(level):
    level = max(1, min(SKILL_MAX_LEVEL, int(level)))
    if level >= SKILL_MAX_LEVEL:
        return 0
    return v0190_requirement("skill", level)

def skill_power_multiplier(level):
    return generator_core_v027.skill_level_power(level)

def skill_cooldown_multiplier(level):
    return generator_core_v027.skill_cooldown_factor(level)

BANK_ROOM = "market"

PROFESSION_COOLDOWN = 2.0

# v0.8.66 - realny czas czynności wynika z poziomu UMIEJĘTNOŚCI/PROFESJI.
# Narzędzie nie skraca czasu; jego level odblokowuje lepszy surowiec/jakość/bonus.
TOOL_ACTION_BASE_SECONDS = {
    # v0.9.6: Wędkarstwo zaczyna od 16 s i schodzi płynnie do 3 s przy 200.
    "fishing": 16,
    "mining": 30,
    "woodcutting": 24,
    "crafting": 20,
    "cooking": 12,
    "herbalism": 10,
    "alchemy": 18,
    "jewelcrafting": 20,
}

TOOL_ACTION_MIN_SECONDS = {
    "fishing": 3,
    "mining": 10,
    "woodcutting": 8,
    "crafting": 7,
    "cooking": 4,
    "herbalism": 3,
    "alchemy": 6,
    "jewelcrafting": 7,
}

REST_TICK_SECONDS = 5.0
REST_REGEN_PERCENT = 10

# v0.9.6: wartości referencyjne z v0.9.5 służą tylko do rebalansu
# XP/cen/zleceń po zmianie czasu 15->5 na 16->3.
V095_FISHING_BASE_SECONDS = 15
V095_FISHING_MIN_SECONDS = 5

PROFESSION_SPEED_CAP_LEVEL = 200

# v0.10.2: Tool XP dla narzędzi zbierackich jest wyrównany względem
# rzeczywistego czasu jednej akcji. Wcześniej Kilof i Piła dostawały prawie
# tyle samo XP co znacznie szybszy Sierp, więc wbijanie ich leveli trwało
# wielokrotnie dłużej. Mnożniki nie zmieniają Profession XP ani dropu.
GATHER_TOOL_LEVELING_MULTIPLIERS = {
    "fishing": 1.50,
    "mining": 3.00,
    "woodcutting": 2.40,
    "herbalism": 1.00,
}

def balanced_gather_tool_xp(tool_type, raw_xp):
    multiplier = GATHER_TOOL_LEVELING_MULTIPLIERS.get(str(tool_type), 1.0)
    return max(1, int(round(max(1, int(raw_xp)) * multiplier)))

def _profession_speed_progress(level):
    # Stary balans timerów 1-200 pozostaje 1:1. Po 200 profesja rozwija się
    # dalej, ale nie skraca akcji poniżej ustalonego minimum.
    effective = max(1, min(PROFESSION_SPEED_CAP_LEVEL, int(level)))
    return (effective - 1) / max(1, PROFESSION_SPEED_CAP_LEVEL - 1)

def _linear_profession_seconds(level, base_seconds, minimum_seconds):
    progress = _profession_speed_progress(level)
    seconds = round(base_seconds - (base_seconds - minimum_seconds) * progress)
    return max(int(minimum_seconds), int(seconds))

def v095_fishing_action_seconds(level):
    return _linear_profession_seconds(level, V095_FISHING_BASE_SECONDS, V095_FISHING_MIN_SECONDS)

def v096_fishing_action_seconds(level):
    return _linear_profession_seconds(
        level, TOOL_ACTION_BASE_SECONDS["fishing"], TOOL_ACTION_MIN_SECONDS["fishing"]
    )

def v096_fishing_reward_scale(level):
    """Skaluje nagrody per połów, aby XP/h nie eksplodował przy 3 s endgame.

    Używa ciągłej krzywej zamiast zaokrąglonych sekund, żeby współczynnik
    malał płynnie i nigdy nie skakał w górę przez zaokrąglenie timera.
    """
    level = max(1, min(PROFESSION_MAX_LEVEL, int(level)))
    progress = _profession_speed_progress(level)
    old_seconds = V095_FISHING_BASE_SECONDS - (V095_FISHING_BASE_SECONDS - V095_FISHING_MIN_SECONDS) * progress
    new_seconds = TOOL_ACTION_BASE_SECONDS["fishing"] - (TOOL_ACTION_BASE_SECONDS["fishing"] - TOOL_ACTION_MIN_SECONDS["fishing"]) * progress
    return max(0.55, min(1.10, new_seconds / old_seconds))

def v096_fishing_workload_scale(level):
    """Ile sztuk potrzeba dla podobnego czasu kontraktu jak w v0.9.5."""
    return max(1.0, min(1.75, 1.0 / v096_fishing_reward_scale(level)))

RIVER_FISHING_ROOMS = {"riverbank", "stone_bridge"}
LAKE_FISHING_ROOMS = {"lake_shore"}
SEA_FISHING_ROOMS = {"sea_pier"}
OCEAN_FISHING_ROOMS = {"ocean_platform"}
FRESHWATER_FISHING_ROOMS = RIVER_FISHING_ROOMS | LAKE_FISHING_ROOMS
MARINE_FISHING_ROOMS = SEA_FISHING_ROOMS | OCEAN_FISHING_ROOMS
FISHING_ROOMS = FRESHWATER_FISHING_ROOMS | MARINE_FISHING_ROOMS

# v0.9.5: opis ekologiczny łowiska jest oddzielony od technicznej puli
# river/lake/sea/ocean. Dzięki temu np. Czarny Kanał może mówić graczowi
# "Łowisko: Kanał", a nadal korzystać z rzecznej progresji ryb.
FISHING_WATER_TYPE_OVERRIDES = {
    "riverbank": "Rzeka",
    "stone_bridge": "Rzeka",
    "lake_shore": "Jezioro",
    "sea_pier": "Morze",
    "ocean_platform": "Ocean",
    "sewer_black_channel": "Kanał",
    "forest_stream": "Strumień",
    "blackwater_pool": "Bagienne rozlewisko",
    "troll_underground_river": "Podziemna rzeka",
    "ice_cave_frozen_lake": "Zamarznięte jezioro",
}

FISHING_HABITAT_LABELS = {
    "river": "rzeka",
    "lake": "jezioro",
    "sea": "morze",
    "ocean": "ocean",
}

# Preferowane pule ekologiczne dla wybranych istniejących wód świata.
# Filtr działa wyłącznie na gatunkach już odblokowanych przez Wędkę;
# gdy na bardzo niskim levelu przecięcie byłoby puste, zachowujemy pulę bazową.
FISHING_ECOLOGY_PREFERRED_IDS = {
    "forest_stream": {
        "small_fish", "dace", "river_perch", "chub", "stone_loach",
        "brown_trout", "grayling", "silver_trout", "golden_trout",
        "salmon", "river_taimen", "spirit_grayling",
    },
    "blackwater_pool": {
        "lake_roach", "crucian_carp", "bream", "tench", "lake_perch",
        "pike", "zander", "freshwater_eel", "golden_tench",
        "deepwater_pike", "moon_carp", "astral_pike",
    },
    "troll_underground_river": {
        "small_fish", "dace", "stone_loach", "burbot", "river_catfish",
        "moon_eel", "ancient_sturgeon", "runic_sturgeon", "chrono_eel",
    },
    "ice_cave_frozen_lake": {
        "lake_roach", "lake_smelt", "vendace", "whitefish", "lake_char",
        "lake_trout", "crystal_whitefish", "starfin_char", "mirror_sturgeon",
    },
}
MINE_MIN_FLOOR = 1
# v0.9.13: 200 oznacza wyłącznie ręcznie przygotowaną część kopalni.
# Kolejne poziomy są generowane na żądanie bez górnego limitu.
MINE_PREGENERATED_MAX_FLOOR = 200
MINE_MAX_FLOOR = MINE_PREGENERATED_MAX_FLOOR  # legacy compatibility only
MINE_WALL_SCALING_START_FLOOR = 10

def mine_wall_hit_range(floor):
    """Zwraca losowy przedział wytrzymałości ściany dla danego piętra."""
    floor = max(MINE_MIN_FLOOR, int(floor))
    effective_floor = min(400, floor)
    if effective_floor < MINE_WALL_SCALING_START_FLOOR:
        return 3, 8
    low = max(6, int(math.floor(effective_floor * 0.70)))
    high = max(low + 1, int(math.ceil(effective_floor * 1.30)))
    return low, high

def roll_mine_wall_hits_required(floor, current_hits=0):
    """Losuje próg raz na ścianę; istniejący postęp nigdy nie jest tracony."""
    low, high = mine_wall_hit_range(floor)
    minimum = max(low, int(current_hits) + 1)
    if minimum > high:
        return int(current_hits) + 1
    return random.randint(minimum, high)

def mine_floor_id(floor):
    return f"mine_floor_{int(floor)}"

def mine_floor_number(room_id):
    match = re.fullmatch(r"mine_floor_(\d+)(?:_r\d+)?", str(room_id or ""))
    if not match:
        return None
    floor = int(match.group(1))
    return floor if floor >= MINE_MIN_FLOOR else None

MINING_DEPTH_ROOMS = {
    mine_floor_id(floor)
    for floor in range(MINE_MIN_FLOOR, MINE_PREGENERATED_MAX_FLOOR + 1)
}
MINING_ROOMS = {
    "cave_entrance", "cave_tunnel", "crystal_chamber"
} | MINING_DEPTH_ROOMS


UNIFIED_DEEP_MINE_STATIC_ROOMS = {
    "cave_entrance", "cave_tunnel", "crystal_chamber"
}

def is_mining_room(room_id):
    """v0.25.1: mining is available only in the single Deep Mine complex."""
    room_id = str(room_id or "")
    return room_id in UNIFIED_DEEP_MINE_STATIC_ROOMS or mine_floor_number(room_id) is not None

AUTO_FISHING_ROUTE = (
    "riverbank", "lake_shore", "sea_pier", "ocean_platform",
)
AUTO_WOODCUTTING_ROUTE = (
    "lumberjack_camp", "whisper_grove", "meadow",
    "old_road", "deep_grove",
)
AUTO_HERBALISM_ROUTE = (
    "meadow", "mint_meadow", "flower_meadow", "lakeside_meadow",
    "riverbank", "lake_shore", "whisper_grove",
    "herbalist_hut", "old_road", "deep_grove",
)

WOODCUTTING_ROOMS = {"lumberjack_camp", "meadow", "whisper_grove", "deep_grove", "old_road"}
MEADOW_HERBALISM_ROOMS = {
    "meadow", "mint_meadow", "flower_meadow", "lakeside_meadow"
}
HERBALISM_ROOMS = {
    "herbalist_hut", "meadow", "mint_meadow", "flower_meadow",
    "lakeside_meadow", "whisper_grove", "deep_grove",
    "riverbank", "lake_shore", "old_road"
}

ENDGAME_FISH_UNLOCKS = {
    "river": (
        (100, "soulfin_trout"),
        (140, "runic_sturgeon"),
        (180, "chrono_eel"),
        (200, "eternal_salmon"),
    ),
    "lake": (
        (100, "crystal_carp"),
        (140, "moon_pike"),
        (180, "starfin_char"),
        (200, "mirror_leviathan"),
    ),
    "sea": (
        (100, "storm_cod"),
        (140, "abyss_halibut"),
        (180, "void_turbot"),
        (200, "crown_monkfish"),
    ),
    "ocean": (
        (100, "celestial_tuna"),
        (120, "dragon_mahi"),
        (120, "reef_shark"),
        (140, "abyss_tuna"),
        (140, "mako_shark"),
        (160, "storm_marlin"),
        (160, "hammerhead_shark"),
        (180, "moon_leviathan"),
        (180, "tiger_shark"),
        (190, "ghost_marlin"),
        (200, "great_white_shark"),
        (200, "eternal_coelacanth"),
    ),
}

BASE_FISH_MIN_TOOL_LEVELS = {
    # Zwykły Tuńczyk jest dużym oceanicznym połowem
    # i nie powinien pojawiać się na niskich levelach Wędki.
    "tuna": 80,
}

MORE_FISH_UNLOCKS = {
    "river": (
        (1, "river_bleak"),
        (5, "stone_loach"),
        (15, "river_bream"),
        (30, "brown_trout"),
        (50, "river_taimen"),
        (75, "emerald_barbel"),
        (110, "spirit_grayling"),
        (150, "bloodfin_salmon"),
        (175, "star_river_eel"),
        (200, "eternal_river_dragon"),
    ),
    "lake": (
        (1, "lake_gudgeon"),
        (8, "lake_smelt"),
        (20, "blue_bream"),
        (35, "golden_tench"),
        (55, "deepwater_pike"),
        (80, "crystal_whitefish"),
        (110, "moon_carp"),
        (150, "astral_pike"),
        (175, "mirror_sturgeon"),
        (200, "eternal_lake_serpent"),
    ),
    "sea": (
        (1, "sand_eel"),
        (10, "garfish"),
        (20, "sea_bream"),
        (35, "bluefish"),
        (55, "conger_eel"),
        (80, "red_snapper"),
        (110, "storm_herring"),
        (150, "abyss_conger"),
        (175, "void_sole"),
        (200, "eternal_sea_drake"),
    ),
    "ocean": (
        (1, "flying_fish"),
        (15, "bonito"),
        (30, "yellowfin_tuna"),
        (50, "king_mackerel"),
        (70, "marlin_black"),
        (90, "opah"),
        (120, "celestial_swordfish"),
        (150, "astral_sunfish"),
        (180, "void_marlin"),
        (200, "world_leviathan"),
    ),
}

ENDGAME_ORE_UNLOCKS = (
    (100, "cobalt_ore"),
    (120, "runestone_ore"),
    (140, "dragonsteel_ore"),
    (160, "astral_ore"),
    (180, "void_ore"),
    (200, "eternium_ore"),
)

ENDGAME_WOOD_UNLOCKS = (
    (100, "runewood_log"),
    (120, "dragonwood_log"),
    (140, "astralwood_log"),
    (160, "voidwood_log"),
    (180, "starheart_log"),
    (200, "eternal_worldwood_log"),
)

ENDGAME_HERB_UNLOCKS = (
    (100, "sunfire_bloom"),
    (120, "dragon_sage"),
    (140, "astral_orchid"),
    (160, "void_lotus"),
    (180, "phoenix_crown"),
    (200, "eternal_blossom"),
)

# v0.9.12: dalsza progresja narzędzi 201-400 ma własne zasoby.
PROGRESSION_400_LEVELS = tuple(range(220, 401, 20))
ENDGAME_ORE_UNLOCKS += tuple((level, f"ore_400_{level}") for level in PROGRESSION_400_LEVELS)
ENDGAME_WOOD_UNLOCKS += tuple((level, f"wood_400_{level}") for level in PROGRESSION_400_LEVELS)
ENDGAME_HERB_UNLOCKS += tuple((level, f"herb_400_{level}") for level in PROGRESSION_400_LEVELS)
for _habitat in tuple(ENDGAME_FISH_UNLOCKS):
    ENDGAME_FISH_UNLOCKS[_habitat] = tuple(ENDGAME_FISH_UNLOCKS[_habitat]) + tuple(
        (level, f"fish_400_{_habitat}_{level}") for level in PROGRESSION_400_LEVELS
    )

def unlocked_resource_pool(
    base_items,
    unlocks,
    tool_level,
):
    result = []
    tool_level = int(tool_level)

    for item_id in base_items:
        minimum = int(
            BASE_FISH_MIN_TOOL_LEVELS.get(item_id, 1)
        )
        if tool_level >= minimum and item_id not in result:
            result.append(item_id)

    for required_level, item_id in unlocks:
        if (
            tool_level >= int(required_level)
            and item_id not in result
        ):
            result.append(item_id)

    return tuple(result)


def add_more_fish_to_pool(pool, habitat, tool_level):
    result = list(pool)
    for required_level, item_id in MORE_FISH_UNLOCKS.get(habitat, ()):
        if int(tool_level) >= int(required_level) and item_id not in result:
            result.append(item_id)
    for required_level, item_id, _name in WORLD_FISH_UNLOCKS.get(habitat, ()):
        if int(tool_level) >= int(required_level) and item_id not in result:
            result.append(item_id)
    return tuple(result)

WORLD_FISH_UNLOCKS = {
    "river": (
        (1, 'world_arapaima', 'Arapaima'),
        (5, 'world_red_bellied_piranha', 'Pirania czerwonobrzucha'),
        (10, 'world_black_piranha', 'Pirania czarna'),
        (15, 'world_pacu', 'Pacu'),
        (20, 'world_tambaqui', 'Tambaqui'),
        (25, 'world_golden_dorado', 'Dorado złociste'),
        (30, 'world_peacock_bass', 'Bass pawiooki'),
        (35, 'world_nile_perch', 'Okoń nilowy'),
        (40, 'world_goliath_tigerfish', 'Tygrysica goliat'),
        (45, 'world_mahseer', 'Mahseer'),
        (50, 'world_rohu', 'Rohu'),
        (55, 'world_catla', 'Katla'),
        (60, 'world_giant_snakehead', 'Wężogłów olbrzymi'),
        (65, 'world_giant_gourami', 'Gurami olbrzymi'),
        (70, 'world_clown_knifefish', 'Nożowiec chitala'),
        (75, 'world_electric_eel', 'Węgorz elektryczny'),
        (80, 'world_alligator_gar', 'Niszczuka krokodyla'),
        (85, 'world_american_paddlefish', 'Wiosłonos amerykański'),
        (90, 'world_bowfin', 'Amia'),
        (95, 'world_muskellunge', 'Muskellunge'),
        (100, 'world_brook_trout', 'Pstrąg źródlany'),
        (105, 'world_rainbow_trout', 'Pstrąg tęczowy'),
        (110, 'world_chinook_salmon', 'Łosoś królewski'),
        (115, 'world_sockeye_salmon', 'Łosoś nerka'),
        (120, 'world_coho_salmon', 'Łosoś kiżucz'),
        (125, 'world_chum_salmon', 'Łosoś keta'),
        (130, 'world_pink_salmon', 'Łosoś różowy'),
        (135, 'world_cutthroat_trout', 'Pstrąg łososiowy'),
        (140, 'world_freshwater_drum', 'Kulbak słodkowodny'),
        (145, 'world_blue_catfish', 'Sum błękitny'),
        (150, 'world_channel_catfish', 'Sum kanałowy'),
        (155, 'world_flathead_catfish', 'Sum płaskogłowy'),
        (160, 'world_grass_carp', 'Amur biały'),
        (165, 'world_bighead_carp', 'Tołpyga pstra'),
        (170, 'world_silver_carp', 'Tołpyga biała'),
        (175, 'world_black_carp', 'Amur czarny'),
        (180, 'world_wels_catfish', 'Sum europejski'),
        (185, 'world_freshwater_stingray', 'Płaszczka słodkowodna'),
        (195, 'world_giant_barb', 'Brzana olbrzymia'),
        (200, 'world_mekong_giant_catfish', 'Sum mekongski'),
    ),
    "lake": (
        (1, 'world_largemouth_bass', 'Bass wielkogębowy'),
        (5, 'world_smallmouth_bass', 'Bass małogębowy'),
        (10, 'world_black_crappie', 'Pomoxis czarny'),
        (15, 'world_white_crappie', 'Pomoxis biały'),
        (20, 'world_bluegill', 'Bass słoneczny'),
        (25, 'world_pumpkinseed', 'Bass dyniowy'),
        (30, 'world_yellow_perch', 'Okoń żółty'),
        (35, 'world_walleye', 'Sandacz amerykański'),
        (40, 'world_sauger', 'Sandacz kanadyjski'),
        (45, 'world_kokanee_salmon', 'Kokanee'),
        (50, 'world_cisco', 'Sielawa amerykańska'),
        (55, 'world_lake_sturgeon', 'Jesiotr jeziorowy'),
        (60, 'world_brown_bullhead', 'Sumik brunatny'),
        (65, 'world_black_bullhead', 'Sumik czarny'),
        (70, 'world_yellow_bullhead', 'Sumik żółty'),
        (75, 'world_nile_tilapia', 'Tilapia nilowa'),
        (80, 'world_mozambique_tilapia', 'Tilapia mozambicka'),
        (85, 'world_blue_tilapia', 'Tilapia niebieska'),
        (90, 'world_oscar_cichlid', 'Pielęgnica pawiooka'),
        (95, 'world_discus', 'Paletka'),
        (100, 'world_freshwater_angelfish', 'Skalar'),
        (105, 'world_silver_arowana', 'Arowana srebrna'),
        (110, 'world_asian_arowana', 'Arowana azjatycka'),
        (115, 'world_giant_barbel_siam', 'Brzana syjamska'),
        (120, 'world_giant_freshwater_whipray', 'Płaszczka rzeczna olbrzymia'),
        (125, 'world_pangas_catfish', 'Panga'),
        (130, 'world_redtail_catfish', 'Sum czerwonoogonowy'),
        (135, 'world_ripsaw_catfish', 'Sum kolczasty'),
        (140, 'world_payara', 'Payara'),
        (145, 'world_wolf_fish', 'Trahira'),
        (150, 'world_arctic_grayling', 'Lipień arktyczny'),
        (155, 'world_lake_chub', 'Jelec jeziorowy'),
        (160, 'world_round_whitefish', 'Sieja okrągła'),
        (165, 'world_inconnu', 'Nelma'),
        (170, 'world_huchen', 'Głowacica'),
        (175, 'world_ide_world', 'Jaź syberyjski'),
        (180, 'world_golden_mahseer', 'Mahseer złoty'),
        (185, 'world_marble_trout', 'Pstrąg marmurkowy'),
        (195, 'world_taimen', 'Tajmień syberyjski'),
        (200, 'world_chinese_perch', 'Okoń chiński'),
    ),
    "sea": (
        (1, 'world_atlantic_tarpon', 'Tarpon atlantycki'),
        (5, 'world_bonefish', 'Albula'),
        (10, 'world_permit_fish', 'Permit'),
        (15, 'world_common_snook', 'Snook'),
        (20, 'world_red_drum', 'Kulbin czerwony'),
        (25, 'world_black_drum', 'Kulbin czarny'),
        (30, 'world_striped_bass', 'Moron prążkowany'),
        (35, 'world_atlantic_croaker', 'Kulbin atlantycki'),
        (40, 'world_sheepshead', 'Sargus owczy'),
        (45, 'world_pompano', 'Pompan'),
        (50, 'world_greater_amberjack', 'Seriola olbrzymia'),
        (55, 'world_yellowtail_snapper', 'Lucjan żółtoogonowy'),
        (60, 'world_mangrove_snapper', 'Lucjan namorzynowy'),
        (65, 'world_lane_snapper', 'Lucjan pręgowany'),
        (70, 'world_red_grouper', 'Strzępiel czerwony'),
        (75, 'world_goliath_grouper', 'Strzępiel goliat'),
        (80, 'world_nassau_grouper', 'Strzępiel nassauski'),
        (85, 'world_european_conger', 'Konger europejski'),
        (90, 'world_mediterranean_moray', 'Murena śródziemnomorska'),
        (95, 'world_giant_moray', 'Murena olbrzymia'),
        (100, 'world_red_lionfish', 'Skrzydlica ognista'),
        (105, 'world_stonefish', 'Szkaradnica'),
        (110, 'world_scorpionfish', 'Skorpena'),
        (115, 'world_queen_triggerfish', 'Rogatnica królewska'),
        (120, 'world_clown_triggerfish', 'Rogatnica klaun'),
        (125, 'world_bumphead_parrotfish', 'Papugoryba garbogłowa'),
        (130, 'world_napoleon_wrasse', 'Wargacz garbogłowy'),
        (135, 'world_corkwing_wrasse', 'Wargacz korkowy'),
        (140, 'world_atlantic_bonito', 'Bonito atlantyckie'),
        (145, 'world_spanish_mackerel', 'Makrela hiszpańska'),
        (150, 'world_atlantic_mackerel', 'Makrela atlantycka'),
        (155, 'world_horse_mackerel', 'Ostrobok'),
        (160, 'world_capelin', 'Gromadnik'),
        (165, 'world_atlantic_saury', 'Sajra atlantycka'),
        (170, 'world_john_dory', 'Piotrosz'),
        (175, 'world_tub_gurnard', 'Kurek czerwony'),
        (180, 'world_wolffish', 'Zębacz pasiasty'),
        (185, 'world_lumpsucker', 'Tasza'),
        (195, 'world_atlantic_anglerfish', 'Żabnica atlantycka'),
        (200, 'world_atlantic_halibut_world', 'Halibut atlantycki'),
    ),
    "ocean": (
        (1, 'world_blue_marlin', 'Marlin błękitny'),
        (5, 'world_white_marlin', 'Marlin biały'),
        (10, 'world_striped_marlin', 'Marlin pasiasty'),
        (15, 'world_longbill_spearfish', 'Włócznik długodzioby'),
        (20, 'world_shortbill_spearfish', 'Włócznik krótkodzioby'),
        (25, 'world_atlantic_bluefin_tuna_world', 'Tuńczyk błękitnopłetwy atlantycki'),
        (30, 'world_southern_bluefin_tuna', 'Tuńczyk błękitnopłetwy południowy'),
        (35, 'world_skipjack_tuna', 'Bonito pasiaste'),
        (40, 'world_blackfin_tuna', 'Tuńczyk czarnopłetwy'),
        (45, 'world_longtail_tuna', 'Tuńczyk długogonowy'),
        (50, 'world_escolar', 'Eskolar'),
        (55, 'world_oilfish', 'Kostropak'),
        (60, 'world_oarfish', 'Wstęgor królewski'),
        (65, 'world_lancetfish', 'Lancetnik długonosy'),
        (70, 'world_pomfret', 'Pomfret'),
        (75, 'world_remora', 'Podnawka'),
        (80, 'world_pilot_fish', 'Pilot'),
        (85, 'world_blue_shark', 'Żarłacz błękitny'),
        (90, 'world_oceanic_whitetip_shark', 'Żarłacz białopłetwy oceaniczny'),
        (95, 'world_common_thresher', 'Kosogon pospolity'),
        (100, 'world_bigeye_thresher', 'Kosogon wielkooki'),
        (105, 'world_porbeagle', 'Żarłacz śledziowy'),
        (110, 'world_greenland_shark', 'Rekin polarny'),
        (115, 'world_salmon_shark', 'Rekin łososiowy'),
        (120, 'world_goblin_shark', 'Rekin chochlik'),
        (125, 'world_megamouth_shark', 'Rekin wielkogębowy'),
        (130, 'world_cookiecutter_shark', 'Rekin foremkowy'),
        (135, 'world_bluntnose_sixgill', 'Sześcioszpar szary'),
        (140, 'world_frilled_shark', 'Chlamida'),
        (145, 'world_whale_shark', 'Rekin wielorybi'),
        (150, 'world_manta_ray', 'Manta oceaniczna'),
        (155, 'world_spotted_eagle_ray', 'Orleń cętkowany'),
        (160, 'world_devil_ray', 'Diabeł morski'),
        (165, 'world_sunfish_sharptail', 'Samogłów ostroogonowy'),
        (170, 'world_slender_sunfish', 'Samogłów smukły'),
        (175, 'world_antarctic_toothfish', 'Antarktyczny kłykacz'),
        (180, 'world_patagonian_toothfish', 'Kłykacz patagoński'),
        (185, 'world_orange_roughy', 'Gardłosz atlantycki'),
        (195, 'world_grenadier', 'Buławik'),
        (200, 'world_coelacanth_world', 'Latimeria'),
    ),
}

WORLD_HERB_UNLOCKS = {
    "meadow": (
        (1, 'world_rosemary', 'Rozmaryn'),
        (10, 'world_thyme', 'Tymianek'),
        (20, 'world_basil', 'Bazylia'),
        (30, 'world_oregano', 'Oregano'),
        (40, 'world_parsley', 'Pietruszka'),
        (50, 'world_dill', 'Koper'),
        (60, 'world_coriander', 'Kolendra'),
        (70, 'world_fennel', 'Koper włoski'),
        (80, 'world_tarragon', 'Estragon'),
        (90, 'world_marjoram', 'Majeranek'),
        (100, 'world_savory', 'Cząber'),
        (110, 'world_chives', 'Szczypiorek'),
        (120, 'world_garlic', 'Czosnek'),
        (130, 'world_ginger', 'Imbir'),
        (140, 'world_turmeric', 'Kurkuma'),
        (150, 'world_galangal', 'Galangal'),
        (160, 'world_cardamom', 'Kardamon'),
        (170, 'world_clove', 'Goździk'),
        (190, 'world_vanilla', 'Wanilia'),
        (200, 'world_saffron', 'Szafran'),
    ),
    "water": (
        (1, 'world_lemongrass', 'Trawa cytrynowa'),
        (10, 'world_aloe_vera', 'Aloes'),
        (20, 'world_calendula', 'Nagietek'),
        (30, 'world_echinacea', 'Jeżówka'),
        (40, 'world_st_johns_wort', 'Dziurawiec'),
        (50, 'world_ribwort_plantain', 'Babka lancetowata'),
        (60, 'world_dandelion', 'Mniszek lekarski'),
        (70, 'world_burdock', 'Łopian'),
        (80, 'world_horsetail', 'Skrzyp polny'),
        (90, 'world_elderflower', 'Kwiat bzu czarnego'),
        (100, 'world_hawthorn', 'Głóg'),
        (110, 'world_rosehip', 'Dzika róża'),
        (120, 'world_hibiscus', 'Hibiskus'),
        (130, 'world_jasmine', 'Jaśmin'),
        (140, 'world_arnica', 'Arnika'),
        (150, 'world_comfrey', 'Żywokost'),
        (160, 'world_mugwort', 'Bylica pospolita'),
        (170, 'world_wormwood', 'Piołun'),
        (190, 'world_skullcap', 'Tarczyca bajkalska'),
        (200, 'world_passionflower', 'Męczennica'),
    ),
    "forest": (
        (1, 'world_hops', 'Chmiel'),
        (10, 'world_licorice_root', 'Lukrecja'),
        (20, 'world_marshmallow_root', 'Prawoślaz'),
        (30, 'world_fenugreek', 'Kozieradka'),
        (40, 'world_cumin', 'Kmin rzymski'),
        (50, 'world_anise', 'Anyż'),
        (60, 'world_star_anise', 'Anyż gwiazdkowy'),
        (70, 'world_black_cumin', 'Czarnuszka'),
        (80, 'world_sesame', 'Sezam'),
        (90, 'world_flax', 'Len'),
        (100, 'world_chia', 'Chia'),
        (110, 'world_amaranth', 'Amarantus'),
        (120, 'world_quinoa', 'Komosa ryżowa'),
        (130, 'world_maca', 'Maca'),
        (140, 'world_guarana', 'Guarana'),
        (150, 'world_yerba_mate', 'Yerba mate'),
        (160, 'world_tea_leaf', 'Liść herbaty'),
        (170, 'world_coffee_berry', 'Owoc kawowca'),
        (190, 'world_cocoa_pod', 'Owoc kakaowca'),
        (200, 'world_kola_nut', 'Orzech kola'),
    ),
    "deep": (
        (1, 'world_holy_basil', 'Tulsi'),
        (10, 'world_ashwagandha', 'Ashwagandha'),
        (20, 'world_moringa', 'Moringa'),
        (30, 'world_neem', 'Neem'),
        (40, 'world_gotu_kola', 'Gotu kola'),
        (50, 'world_bacopa', 'Bakopa'),
        (60, 'world_shatavari', 'Shatavari'),
        (70, 'world_rhodiola', 'Różeniec górski'),
        (80, 'world_eleuthero', 'Eleuterokok'),
        (90, 'world_astragalus', 'Traganek'),
        (100, 'world_milk_thistle', 'Ostropest plamisty'),
        (110, 'world_artichoke_leaf', 'Liść karczocha'),
        (120, 'world_gentian', 'Goryczka'),
        (130, 'world_angelica', 'Arcydzięgiel'),
        (140, 'world_juniper_berry', 'Jagoda jałowca'),
        (150, 'world_bay_leaf', 'Liść laurowy'),
        (160, 'world_olive_leaf', 'Liść oliwny'),
        (170, 'world_eucalyptus_leaf', 'Liść eukaliptusa'),
        (190, 'world_myrrh', 'Mirra'),
        (200, 'world_frankincense', 'Olibanum'),
    ),
}

WORLD_WOOD_UNLOCKS = {
    "beginner": (
        (1, 'world_norway_spruce', 'Pień świerku pospolitego'),
        (7, 'world_silver_fir', 'Pień jodły pospolitej'),
        (13, 'world_european_larch', 'Pień modrzewia europejskiego'),
        (19, 'world_douglas_fir', 'Pień daglezji'),
        (25, 'world_western_hemlock', 'Pień choiny zachodniej'),
        (31, 'world_mediterranean_cypress', 'Pień cyprysa'),
        (37, 'world_juniper_wood', 'Pień jałowca'),
        (43, 'world_black_locust', 'Pień robinii akacjowej'),
        (49, 'world_acacia_wood', 'Pień akacji'),
        (55, 'world_american_sycamore', 'Pień platana amerykańskiego'),
        (61, 'world_elm_wood', 'Pień wiązu'),
        (67, 'world_hornbeam_wood', 'Pień grabu'),
        (73, 'world_basswood', 'Pień lipy amerykańskiej'),
        (79, 'world_aspen_wood', 'Pień osiki'),
        (85, 'world_cottonwood', 'Pień topoli bawełnianej'),
    ),
    "forest": (
        (20, 'world_cherry_wood', 'Pień wiśni'),
        (26, 'world_apple_wood', 'Pień jabłoni'),
        (32, 'world_pear_wood', 'Pień gruszy'),
        (38, 'world_plum_wood', 'Pień śliwy'),
        (44, 'world_olive_wood', 'Pień oliwki'),
        (50, 'world_eucalyptus_wood', 'Pień eukaliptusa'),
        (56, 'world_rubberwood', 'Pień kauczukowca'),
        (62, 'world_cork_oak', 'Pień dębu korkowego'),
        (68, 'world_white_oak', 'Pień dębu białego'),
        (74, 'world_red_oak', 'Pień dębu czerwonego'),
        (80, 'world_sugar_maple', 'Pień klonu cukrowego'),
        (86, 'world_red_maple', 'Pień klonu czerwonego'),
        (92, 'world_hickory', 'Pień hikory'),
        (98, 'world_pecan_wood', 'Pień pekana'),
        (104, 'world_rosewood', 'Pień palisandru'),
    ),
    "deep": (
        (60, 'world_padauk', 'Pień padouku'),
        (67, 'world_wenge', 'Pień wenge'),
        (74, 'world_iroko', 'Pień iroko'),
        (81, 'world_sapele', 'Pień sapeli'),
        (88, 'world_merbau', 'Pień merbau'),
        (95, 'world_bubinga', 'Pień bubingi'),
        (102, 'world_zebrawood', 'Pień zebrano'),
        (109, 'world_jatoba', 'Pień jatoby'),
        (116, 'world_purpleheart', 'Pień amarantowca'),
        (123, 'world_greenheart', 'Pień greenheart'),
        (130, 'world_lignum_vitae', 'Pień gwajakowca'),
        (137, 'world_sandalwood', 'Pień sandałowca'),
        (144, 'world_agarwood', 'Drewno agarowe'),
        (151, 'world_koa', 'Pień koa'),
        (158, 'world_paulownia', 'Pień paulowni'),
        (165, 'world_balsa', 'Pień balsy'),
        (172, 'world_baobab', 'Pień baobabu'),
        (179, 'world_kauri', 'Pień kauri'),
        (186, 'world_jarrah', 'Pień jarrah'),
        (193, 'world_tasmanian_blackwood', 'Pień akacji czarnej tasmańskiej'),
    ),
}

WORLD_ORE_UNLOCKS = (
    (5, 5, 'world_cassiterite', 'Ruda cyny - kasyteryt'),
    (10, 10, 'world_galena', 'Ruda ołowiu - galena'),
    (15, 15, 'world_sphalerite', 'Ruda cynku - sfaleryt'),
    (20, 20, 'world_pentlandite', 'Ruda niklu - pentlandyt'),
    (25, 25, 'world_chromite', 'Ruda chromu - chromit'),
    (30, 30, 'world_pyrolusite', 'Ruda manganu - piroluzyt'),
    (35, 35, 'world_bauxite', 'Boksyt'),
    (40, 40, 'world_ilmenite', 'Ruda tytanu - ilmenit'),
    (45, 45, 'world_rutile', 'Ruda tytanu - rutyl'),
    (50, 50, 'world_wolframite', 'Ruda wolframu - wolframit'),
    (55, 55, 'world_scheelite', 'Ruda wolframu - scheelit'),
    (60, 60, 'world_molybdenite', 'Ruda molibdenu - molibdenit'),
    (65, 65, 'world_cinnabar', 'Ruda rtęci - cynober'),
    (70, 70, 'world_stibnite', 'Ruda antymonu - antymonit'),
    (75, 75, 'world_arsenopyrite', 'Arsenopiryt'),
    (80, 80, 'world_cobaltite', 'Kobaltyn'),
    (85, 85, 'world_spodumene', 'Ruda litu - spodumen'),
    (90, 90, 'world_lepidolite', 'Ruda litu - lepidolit'),
    (95, 95, 'world_coltan', 'Kolumbit-tantalit'),
    (100, 100, 'world_pyrochlore', 'Ruda niobu - pirochlor'),
    (105, 105, 'world_monazite', 'Monacyt'),
    (110, 110, 'world_bastnasite', 'Bastnazyt'),
    (115, 115, 'world_uraninite', 'Uraninit'),
    (120, 120, 'world_thorite', 'Toryt'),
    (125, 125, 'world_platinum_ore', 'Ruda platyny'),
    (130, 130, 'world_palladium_ore', 'Ruda palladu'),
    (135, 135, 'world_rhodium_ore', 'Ruda rodu'),
    (140, 140, 'world_iridium_ore', 'Ruda irydu'),
    (145, 145, 'world_osmium_ore', 'Ruda osmu'),
    (150, 150, 'world_vanadinite', 'Ruda wanadu - wanadynit'),
    (155, 155, 'world_magnesite', 'Magnezyt'),
    (160, 160, 'world_celestite', 'Celestyn'),
    (165, 165, 'world_barite', 'Baryt'),
    (170, 170, 'world_apatite', 'Apatyt fosforanowy'),
    (175, 175, 'world_native_sulfur', 'Siarka rodzima'),
    (180, 180, 'world_halite', 'Halit'),
    (185, 185, 'world_sylvite', 'Sylwin'),
    (190, 190, 'world_kimberlite', 'Kimberlit diamentonośny'),
    (195, 195, 'world_graphite', 'Grafit'),
    (200, 200, 'world_magnetite_world', 'Magnetyt'),
)


def _world_resource_sell_fields(level):
    level = max(1, min(200, int(level)))
    if level < 100:
        return {"sell_silver": max(5, 5 + level * 2)}
    return {"sell_gold": max(1, (level - 80) // 8)}

def _register_world_resource_items():
    for habitat, rows in WORLD_FISH_UNLOCKS.items():
        for level, item_id, name in rows:
            item = {
                "name": name,
                "type": "resource",
                "price": None,
                "desc": (
                    f"Ryba świata. Łowisko: {habitat}. "
                    f"Wędka level {level}+."
                ),
            }
            item.update(_world_resource_sell_fields(level))
            ITEMS[item_id] = item

    for group, rows in WORLD_HERB_UNLOCKS.items():
        for level, item_id, name in rows:
            item = {
                "name": name,
                "type": "resource",
                "price": None,
                "desc": (
                    f"Roślina świata. Grupa występowania: {group}. "
                    f"Sierp level {level}+."
                ),
            }
            item.update(_world_resource_sell_fields(level))
            ITEMS[item_id] = item

    for group, rows in WORLD_WOOD_UNLOCKS.items():
        for level, item_id, name in rows:
            item = {
                "name": name,
                "type": "resource",
                "price": None,
                "desc": (
                    f"Drewno świata. Grupa występowania: {group}. "
                    f"Piła level {level}+."
                ),
            }
            item.update(_world_resource_sell_fields(level))
            ITEMS[item_id] = item

    for level, floor, item_id, name in WORLD_ORE_UNLOCKS:
        item = {
            "name": name,
            "type": "resource",
            "price": None,
            "desc": (
                f"Ruda lub minerał świata. Kilof level {level}+, "
                f"Kopalnia Głębinowa poziom {floor}+."
            ),
        }
        item.update(_world_resource_sell_fields(level))
        ITEMS[item_id] = item

def unlocked_world_ids(rows, tool_level):
    return tuple(
        item_id
        for required, item_id, _name in rows
        if int(tool_level) >= int(required)
    )

def unlocked_world_ore_ids(tool_level, floor):
    return tuple(
        item_id
        for required_level, required_floor, item_id, _name
        in WORLD_ORE_UNLOCKS
        if int(tool_level) >= int(required_level)
        and int(floor) >= int(required_floor)
    )

FISH_RESOURCE_IDS = {
    # Rzeka
    "small_fish", "river_carp", "river_perch", "dace", "chub", "common_nase",
    "barbel", "ide", "asp", "grayling", "burbot", "pike", "zander",
    "silver_trout", "golden_trout", "salmon", "river_catfish",
    "ancient_sturgeon", "moon_eel",
    # Jezioro
    "lake_roach", "rudd", "crucian_carp", "bream", "tench", "lake_perch",
    "vendace", "whitefish", "lake_char", "lake_trout", "pike", "zander",
    "giant_pike", "freshwater_eel",
    # Morze
    "sprat", "sardine", "anchovy", "herring", "mackerel", "whiting",
    "cod", "hake", "sea_bass", "red_mullet", "haddock", "pollock",
    "flounder", "sole", "halibut", "turbot", "monkfish",
    # Ocean
    "tuna", "albacore", "bigeye_tuna", "mahi_mahi", "wahoo",
    "barracuda", "cobia", "amberjack", "sailfish", "swordfish",
    "bluefin_tuna", "ocean_sunfish", "reef_shark", "mako_shark",
    "tiger_shark", "hammerhead_shark", "great_white_shark", "ghost_marlin",
    # Endgame 100-200
    "soulfin_trout", "runic_sturgeon", "chrono_eel", "eternal_salmon",
    "crystal_carp", "moon_pike", "starfin_char", "mirror_leviathan",
    "storm_cod", "abyss_halibut", "void_turbot", "crown_monkfish",
    "celestial_tuna", "dragon_mahi", "abyss_tuna", "storm_marlin",
    "moon_leviathan", "eternal_coelacanth",
    # v0.6.98
    "river_bleak", "stone_loach", "river_bream", "brown_trout",
    "river_taimen", "emerald_barbel", "spirit_grayling",
    "bloodfin_salmon", "star_river_eel", "eternal_river_dragon",
    "lake_gudgeon", "lake_smelt", "blue_bream", "golden_tench",
    "deepwater_pike", "crystal_whitefish", "moon_carp",
    "astral_pike", "mirror_sturgeon", "eternal_lake_serpent",
    "sand_eel", "garfish", "sea_bream", "bluefish", "conger_eel",
    "red_snapper", "storm_herring", "abyss_conger", "void_sole",
    "eternal_sea_drake",
    "flying_fish", "bonito", "yellowfin_tuna", "king_mackerel",
    "marlin_black", "opah", "celestial_swordfish", "astral_sunfish",
    "void_marlin", "world_leviathan",
}
ORE_RESOURCE_IDS = {
    "stone_chunk", "copper_ore", "iron_ore",
    "silver_ore", "gold_ore",
    "cobalt_ore", "runestone_ore", "dragonsteel_ore",
    "astral_ore", "void_ore", "eternium_ore",
}
WOOD_RESOURCE_IDS = {
    "fallen_branch", "birch_log", "alder_log", "pine_log", "poplar_log",
    "willow_log", "linden_log", "oak_log", "beech_log", "maple_log",
    "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log", "ebony_log",
    "silverwood_log", "spiritwood_log", "ancient_heartwood", "worldtree_wood",
    "runewood_log", "dragonwood_log", "astralwood_log",
    "voidwood_log", "starheart_log", "eternal_worldwood_log",
}

HERB_RESOURCE_IDS = {
    "nettle", "chamomile", "mint", "sage", "lavender", "yarrow",
    "lemon_balm", "valerian", "ginseng", "nightshade", "mandrake",
    "moonflower", "soulroot", "phoenix_leaf", "star_moss", "astral_lotus",
    "sunfire_bloom", "dragon_sage", "astral_orchid",
    "void_lotus", "phoenix_crown", "eternal_blossom",
}
HERB_MEADOW_ATLAS = {"nettle", "chamomile", "mint", "yarrow", "lemon_balm", "lavender"}
HERB_FOREST_ATLAS = {"sage", "valerian", "ginseng", "nightshade", "mandrake", "moonflower", "soulroot"}
HERB_WATER_ATLAS = {"mint", "lemon_balm", "star_moss", "moonflower"}
HERB_DEEP_ATLAS = {
    "mandrake", "moonflower", "soulroot", "phoenix_leaf",
    "star_moss", "astral_lotus",
    "sunfire_bloom", "dragon_sage", "astral_orchid",
    "void_lotus", "phoenix_crown", "eternal_blossom",
}

RIVER_FISH_ATLAS = {
    "small_fish", "dace", "river_perch", "chub", "common_nase",
    "river_carp", "barbel", "ide", "asp", "grayling", "burbot",
    "silver_trout", "golden_trout", "pike", "zander", "salmon",
    "river_catfish", "ancient_sturgeon", "moon_eel",
    "soulfin_trout", "runic_sturgeon", "chrono_eel", "eternal_salmon",
    "river_bleak", "stone_loach", "river_bream", "brown_trout",
    "river_taimen", "emerald_barbel", "spirit_grayling",
    "bloodfin_salmon", "star_river_eel", "eternal_river_dragon",
}
LAKE_FISH_ATLAS = {
    "lake_roach", "rudd", "crucian_carp", "bream", "tench",
    "lake_perch", "vendace", "whitefish", "lake_char", "lake_trout",
    "pike", "zander", "giant_pike", "freshwater_eel",
    "crystal_carp", "moon_pike", "starfin_char", "mirror_leviathan",
    "lake_gudgeon", "lake_smelt", "blue_bream", "golden_tench",
    "deepwater_pike", "crystal_whitefish", "moon_carp",
    "astral_pike", "mirror_sturgeon", "eternal_lake_serpent",
}
SEA_FISH_ATLAS = {
    "sprat", "sardine", "anchovy", "herring", "mackerel", "whiting",
    "cod", "hake", "sea_bass", "red_mullet", "haddock", "pollock",
    "flounder", "sole", "halibut", "turbot", "monkfish",
    "storm_cod", "abyss_halibut", "void_turbot", "crown_monkfish",
    "sand_eel", "garfish", "sea_bream", "bluefish", "conger_eel",
    "red_snapper", "storm_herring", "abyss_conger",
    "void_sole", "eternal_sea_drake",
}
OCEAN_FISH_ATLAS = {
    "mackerel", "mahi_mahi", "albacore", "wahoo", "barracuda", "tuna",
    "sailfish", "bigeye_tuna", "cobia", "amberjack", "swordfish",
    "bluefin_tuna", "ocean_sunfish", "reef_shark", "mako_shark",
    "tiger_shark", "hammerhead_shark", "great_white_shark", "ghost_marlin",
    "celestial_tuna", "dragon_mahi", "abyss_tuna",
    "storm_marlin", "moon_leviathan", "eternal_coelacanth",
    "flying_fish", "bonito", "yellowfin_tuna", "king_mackerel",
    "marlin_black", "opah", "celestial_swordfish",
    "astral_sunfish", "void_marlin", "world_leviathan",
}

WOOD_BEGINNER_ATLAS = {
    "fallen_branch", "birch_log", "alder_log", "pine_log", "poplar_log",
    "willow_log", "linden_log", "oak_log", "beech_log", "maple_log",
}
WOOD_FOREST_ATLAS = {
    "linden_log", "oak_log", "beech_log", "maple_log", "ash_log",
    "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log",
}
WOOD_DEEP_ATLAS = {
    "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log",
    "ebony_log", "silverwood_log", "spiritwood_log",
    "ancient_heartwood", "worldtree_wood",
    "runewood_log", "dragonwood_log", "astralwood_log",
    "voidwood_log", "starheart_log", "eternal_worldwood_log",
}

# v0.9.12: zasoby 220-400 są pełnoprawnymi zasobami atlasów/kolekcji.
_POST400_ORE_IDS = {item_id for _level, item_id in ENDGAME_ORE_UNLOCKS if _level > 200}
_POST400_WOOD_IDS = {item_id for _level, item_id in ENDGAME_WOOD_UNLOCKS if _level > 200}
_POST400_HERB_IDS = {item_id for _level, item_id in ENDGAME_HERB_UNLOCKS if _level > 200}
_POST400_FISH_BY_HABITAT = {
    habitat: {item_id for _level, item_id in rows if _level > 200}
    for habitat, rows in ENDGAME_FISH_UNLOCKS.items()
}
ORE_RESOURCE_IDS.update(_POST400_ORE_IDS)
WOOD_RESOURCE_IDS.update(_POST400_WOOD_IDS)
HERB_RESOURCE_IDS.update(_POST400_HERB_IDS)
FISH_RESOURCE_IDS.update(*(ids for ids in _POST400_FISH_BY_HABITAT.values()))
RIVER_FISH_ATLAS.update(_POST400_FISH_BY_HABITAT.get("river", set()))
LAKE_FISH_ATLAS.update(_POST400_FISH_BY_HABITAT.get("lake", set()))
SEA_FISH_ATLAS.update(_POST400_FISH_BY_HABITAT.get("sea", set()))
OCEAN_FISH_ATLAS.update(_POST400_FISH_BY_HABITAT.get("ocean", set()))
WOOD_DEEP_ATLAS.update(_POST400_WOOD_IDS)
HERB_DEEP_ATLAS.update(_POST400_HERB_IDS)

WORLD_FISH_IDS = {
    item_id
    for rows in WORLD_FISH_UNLOCKS.values()
    for _level, item_id, _name in rows
}
WORLD_HERB_IDS = {
    item_id
    for rows in WORLD_HERB_UNLOCKS.values()
    for _level, item_id, _name in rows
}
WORLD_WOOD_IDS = {
    item_id
    for rows in WORLD_WOOD_UNLOCKS.values()
    for _level, item_id, _name in rows
}
WORLD_ORE_IDS = {
    item_id
    for _level, _floor, item_id, _name in WORLD_ORE_UNLOCKS
}

FISH_RESOURCE_IDS.update(WORLD_FISH_IDS)
HERB_RESOURCE_IDS.update(WORLD_HERB_IDS)
WOOD_RESOURCE_IDS.update(WORLD_WOOD_IDS)
ORE_RESOURCE_IDS.update(WORLD_ORE_IDS)

RIVER_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["river"]
)
LAKE_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["lake"]
)
SEA_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["sea"]
)
OCEAN_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["ocean"]
)

HERB_MEADOW_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["meadow"]
)
HERB_WATER_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["water"]
)
HERB_FOREST_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["forest"]
)
HERB_DEEP_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["deep"]
)

WOOD_BEGINNER_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_WOOD_UNLOCKS["beginner"]
)
WOOD_FOREST_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_WOOD_UNLOCKS["forest"]
)
WOOD_DEEP_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_WOOD_UNLOCKS["deep"]
)

# Pełne atlasy zasobów.
# Te zbiory są bezpośrednio oparte na aktywnych RESOURCE_IDS,
# dzięki czemu każda istniejąca ryba, ruda, sztuka drewna i zioło
# zawsze trafia do pełnego widoku atlasu.
FISH_ATLAS_ALL = set(FISH_RESOURCE_IDS)
ORE_ATLAS_ALL = set(ORE_RESOURCE_IDS)
WOOD_ATLAS_ALL = set(WOOD_RESOURCE_IDS)
HERB_ATLAS_ALL = set(HERB_RESOURCE_IDS)

def validate_complete_resource_atlases():
    checks = (
        ("ryby", FISH_RESOURCE_IDS, FISH_ATLAS_ALL),
        ("rudy", ORE_RESOURCE_IDS, ORE_ATLAS_ALL),
        ("drewno", WOOD_RESOURCE_IDS, WOOD_ATLAS_ALL),
        ("zioła", HERB_RESOURCE_IDS, HERB_ATLAS_ALL),
    )
    for label, source_ids, atlas_ids in checks:
        missing = set(source_ids) - set(atlas_ids)
        if missing:
            raise RuntimeError(
                f"Atlas {label} nie zawiera: "
                + ", ".join(sorted(missing))
            )

validate_complete_resource_atlases()

ORE_ATLAS_LEVELS = {
    "stone_chunk": 1,
    "copper_ore": 1,
    "iron_ore": 10,
    "silver_ore": 25,
    "gold_ore": 50,
    "cobalt_ore": 100,
    "runestone_ore": 120,
    "dragonsteel_ore": 140,
    "astral_ore": 160,
    "void_ore": 180,
    "eternium_ore": 200,
}

ORE_MINE_FLOOR_MINIMUMS = {
    "stone_chunk": 1,
    "copper_ore": 1,
    "iron_ore": 10,
    "silver_ore": 25,
    "gold_ore": 50,
    "cobalt_ore": 100,
    "runestone_ore": 120,
    "dragonsteel_ore": 140,
    "astral_ore": 160,
    "void_ore": 180,
    "eternium_ore": 200,
}

for _level, _floor, _item_id, _name in WORLD_ORE_UNLOCKS:
    ORE_ATLAS_LEVELS[_item_id] = _level
    ORE_MINE_FLOOR_MINIMUMS[_item_id] = _floor

# v0.24.4: rudy progresji 220-400 wymagają równocześnie odpowiedniego
# Kilofa i głębokości Kopalni Głębinowej. Atlas ma pokazywać te same progi.
for _level, _item_id in ENDGAME_ORE_UNLOCKS:
    if int(_level) > 200:
        ORE_ATLAS_LEVELS[_item_id] = int(_level)
        ORE_MINE_FLOOR_MINIMUMS[_item_id] = int(_level)

# v0.8.22 - dokładne minimalne levele narzędzi według lokacji.
# Dane odpowiadają aktywnym pulom Drwalstwa i Zielarstwa v0.8.22.
WOOD_ATLAS_ROOM_MIN_LEVELS = {'deep_grove': {'ancient_heartwood': 80,
                'ash_log': 1,
                'astralwood_log': 140,
                'cedar_log': 1,
                'chestnut_log': 1,
                'dragonwood_log': 120,
                'ebony_log': 40,
                'eternal_worldwood_log': 200,
                'ironwood_log': 40,
                'mahogany_log': 40,
                'redwood_log': 60,
                'runewood_log': 100,
                'silverwood_log': 60,
                'spiritwood_log': 80,
                'starheart_log': 180,
                'teak_log': 40,
                'voidwood_log': 160,
                'walnut_log': 1,
                'world_agarwood': 144,
                'world_balsa': 165,
                'world_baobab': 172,
                'world_bubinga': 95,
                'world_greenheart': 123,
                'world_iroko': 74,
                'world_jarrah': 186,
                'world_jatoba': 109,
                'world_kauri': 179,
                'world_koa': 151,
                'world_lignum_vitae': 130,
                'world_merbau': 88,
                'world_padauk': 60,
                'world_paulownia': 158,
                'world_purpleheart': 116,
                'world_sandalwood': 137,
                'world_sapele': 81,
                'world_tasmanian_blackwood': 193,
                'world_wenge': 67,
                'world_zebrawood': 102,
                'worldtree_wood': 80,
                'yew_log': 40},
 'lumberjack_camp': {'alder_log': 1,
                     'beech_log': 35,
                     'birch_log': 1,
                     'fallen_branch': 1,
                     'linden_log': 15,
                     'maple_log': 35,
                     'oak_log': 35,
                     'pine_log': 1,
                     'poplar_log': 15,
                     'willow_log': 15,
                     'world_acacia_wood': 49,
                     'world_american_sycamore': 55,
                     'world_aspen_wood': 79,
                     'world_basswood': 73,
                     'world_black_locust': 43,
                     'world_cottonwood': 85,
                     'world_douglas_fir': 19,
                     'world_elm_wood': 61,
                     'world_european_larch': 13,
                     'world_hornbeam_wood': 67,
                     'world_juniper_wood': 37,
                     'world_mediterranean_cypress': 31,
                     'world_norway_spruce': 1,
                     'world_silver_fir': 7,
                     'world_western_hemlock': 25},
 'meadow': {'alder_log': 1,
            'beech_log': 35,
            'birch_log': 1,
            'fallen_branch': 1,
            'linden_log': 15,
            'maple_log': 35,
            'oak_log': 35,
            'pine_log': 1,
            'poplar_log': 15,
            'willow_log': 15,
            'world_acacia_wood': 49,
            'world_american_sycamore': 55,
            'world_aspen_wood': 79,
            'world_basswood': 73,
            'world_black_locust': 43,
            'world_cottonwood': 85,
            'world_douglas_fir': 19,
            'world_elm_wood': 61,
            'world_european_larch': 13,
            'world_hornbeam_wood': 67,
            'world_juniper_wood': 37,
            'world_mediterranean_cypress': 31,
            'world_norway_spruce': 1,
            'world_silver_fir': 7,
            'world_western_hemlock': 25},
 'old_road': {'ash_log': 25,
              'beech_log': 1,
              'cedar_log': 50,
              'chestnut_log': 25,
              'ironwood_log': 75,
              'linden_log': 1,
              'mahogany_log': 50,
              'maple_log': 1,
              'oak_log': 1,
              'redwood_log': 75,
              'teak_log': 75,
              'walnut_log': 25,
              'world_apple_wood': 26,
              'world_cherry_wood': 20,
              'world_cork_oak': 62,
              'world_eucalyptus_wood': 50,
              'world_hickory': 92,
              'world_olive_wood': 44,
              'world_pear_wood': 32,
              'world_pecan_wood': 98,
              'world_plum_wood': 38,
              'world_red_maple': 86,
              'world_red_oak': 74,
              'world_rosewood': 104,
              'world_rubberwood': 56,
              'world_sugar_maple': 80,
              'world_white_oak': 68,
              'yew_log': 50},
 'whisper_grove': {'ash_log': 25,
                   'beech_log': 1,
                   'cedar_log': 50,
                   'chestnut_log': 25,
                   'ironwood_log': 75,
                   'linden_log': 1,
                   'mahogany_log': 50,
                   'maple_log': 1,
                   'oak_log': 1,
                   'redwood_log': 75,
                   'teak_log': 75,
                   'walnut_log': 25,
                   'world_apple_wood': 26,
                   'world_cherry_wood': 20,
                   'world_cork_oak': 62,
                   'world_eucalyptus_wood': 50,
                   'world_hickory': 92,
                   'world_olive_wood': 44,
                   'world_pear_wood': 32,
                   'world_pecan_wood': 98,
                   'world_plum_wood': 38,
                   'world_red_maple': 86,
                   'world_red_oak': 74,
                   'world_rosewood': 104,
                   'world_rubberwood': 56,
                   'world_sugar_maple': 80,
                   'world_white_oak': 68,
                   'yew_log': 50}}

HERB_ATLAS_ROOM_MIN_LEVELS = {'chamomile_meadow': {'chamomile': 1},
 'deep_grove': {'astral_lotus': 90,
                'astral_orchid': 140,
                'dragon_sage': 120,
                'eternal_blossom': 200,
                'ginseng': 1,
                'mandrake': 1,
                'moonflower': 40,
                'nightshade': 1,
                'phoenix_crown': 180,
                'phoenix_leaf': 70,
                'soulroot': 40,
                'star_moss': 40,
                'sunfire_bloom': 100,
                'void_lotus': 160,
                'world_angelica': 130,
                'world_artichoke_leaf': 110,
                'world_ashwagandha': 10,
                'world_astragalus': 90,
                'world_bacopa': 50,
                'world_bay_leaf': 150,
                'world_eleuthero': 80,
                'world_eucalyptus_leaf': 170,
                'world_frankincense': 200,
                'world_gentian': 120,
                'world_gotu_kola': 40,
                'world_holy_basil': 1,
                'world_juniper_berry': 140,
                'world_milk_thistle': 100,
                'world_moringa': 20,
                'world_myrrh': 190,
                'world_neem': 30,
                'world_olive_leaf': 160,
                'world_rhodiola': 70,
                'world_shatavari': 60},
 'flower_meadow': {'chamomile': 1,
                   'lavender': 1,
                   'lemon_balm': 15,
                   'nettle': 1,
                   'sage': 35,
                   'valerian': 35,
                   'world_basil': 20,
                   'world_cardamom': 160,
                   'world_chives': 110,
                   'world_clove': 170,
                   'world_coriander': 60,
                   'world_dill': 50,
                   'world_fennel': 70,
                   'world_galangal': 150,
                   'world_garlic': 120,
                   'world_ginger': 130,
                   'world_marjoram': 90,
                   'world_oregano': 30,
                   'world_parsley': 40,
                   'world_rosemary': 1,
                   'world_saffron': 200,
                   'world_savory': 100,
                   'world_tarragon': 80,
                   'world_thyme': 10,
                   'world_turmeric': 140,
                   'world_vanilla': 190,
                   'yarrow': 15},
 'ginseng_meadow': {'ginseng': 1},
 'herbalist_hut': {'chamomile': 1,
                   'lavender': 15,
                   'lemon_balm': 15,
                   'mint': 1,
                   'nettle': 1,
                   'sage': 35,
                   'valerian': 35,
                   'world_basil': 20,
                   'world_cardamom': 160,
                   'world_chives': 110,
                   'world_clove': 170,
                   'world_coriander': 60,
                   'world_dill': 50,
                   'world_fennel': 70,
                   'world_galangal': 150,
                   'world_garlic': 120,
                   'world_ginger': 130,
                   'world_marjoram': 90,
                   'world_oregano': 30,
                   'world_parsley': 40,
                   'world_rosemary': 1,
                   'world_saffron': 200,
                   'world_savory': 100,
                   'world_tarragon': 80,
                   'world_thyme': 10,
                   'world_turmeric': 140,
                   'world_vanilla': 190,
                   'yarrow': 15},
 'lake_shore': {'chamomile': 1,
                'ginseng': 55,
                'lemon_balm': 1,
                'mint': 1,
                'moonflower': 55,
                'sage': 25,
                'star_moss': 25,
                'valerian': 55,
                'world_aloe_vera': 10,
                'world_arnica': 140,
                'world_burdock': 70,
                'world_calendula': 20,
                'world_comfrey': 150,
                'world_dandelion': 60,
                'world_echinacea': 30,
                'world_elderflower': 90,
                'world_hawthorn': 100,
                'world_hibiscus': 120,
                'world_horsetail': 80,
                'world_jasmine': 130,
                'world_lemongrass': 1,
                'world_mugwort': 160,
                'world_passionflower': 200,
                'world_ribwort_plantain': 50,
                'world_rosehip': 110,
                'world_skullcap': 190,
                'world_st_johns_wort': 40,
                'world_wormwood': 170,
                'yarrow': 25},
 'lakeside_meadow': {'chamomile': 1,
                     'lavender': 15,
                     'lemon_balm': 1,
                     'mint': 1,
                     'sage': 35,
                     'star_moss': 35,
                     'world_aloe_vera': 10,
                     'world_arnica': 140,
                     'world_burdock': 70,
                     'world_calendula': 20,
                     'world_comfrey': 150,
                     'world_dandelion': 60,
                     'world_echinacea': 30,
                     'world_elderflower': 90,
                     'world_hawthorn': 100,
                     'world_hibiscus': 120,
                     'world_horsetail': 80,
                     'world_jasmine': 130,
                     'world_lemongrass': 1,
                     'world_mugwort': 160,
                     'world_passionflower': 200,
                     'world_ribwort_plantain': 50,
                     'world_rosehip': 110,
                     'world_skullcap': 190,
                     'world_st_johns_wort': 40,
                     'world_wormwood': 170,
                     'yarrow': 15},
 'lavender_meadow': {'lavender': 1},
 'lemon_balm_meadow': {'lemon_balm': 1},
 'meadow': {'chamomile': 1,
            'lavender': 15,
            'lemon_balm': 15,
            'mint': 1,
            'nettle': 1,
            'sage': 35,
            'valerian': 35,
            'world_basil': 20,
            'world_cardamom': 160,
            'world_chives': 110,
            'world_clove': 170,
            'world_coriander': 60,
            'world_dill': 50,
            'world_fennel': 70,
            'world_galangal': 150,
            'world_garlic': 120,
            'world_ginger': 130,
            'world_marjoram': 90,
            'world_oregano': 30,
            'world_parsley': 40,
            'world_rosemary': 1,
            'world_saffron': 200,
            'world_savory': 100,
            'world_tarragon': 80,
            'world_thyme': 10,
            'world_turmeric': 140,
            'world_vanilla': 190,
            'yarrow': 15},
 'mint_meadow': {'mint': 1},
 'moonflower_meadow': {'moonflower': 1},
 'nettle_meadow': {'nettle': 1},
 'old_road': {'ginseng': 25,
              'lavender': 1,
              'mandrake': 50,
              'moonflower': 50,
              'nightshade': 25,
              'phoenix_leaf': 75,
              'sage': 1,
              'soulroot': 50,
              'star_moss': 75,
              'valerian': 1,
              'world_amaranth': 110,
              'world_anise': 50,
              'world_black_cumin': 70,
              'world_chia': 100,
              'world_cocoa_pod': 190,
              'world_coffee_berry': 170,
              'world_cumin': 40,
              'world_fenugreek': 30,
              'world_flax': 90,
              'world_guarana': 140,
              'world_hops': 1,
              'world_kola_nut': 200,
              'world_licorice_root': 10,
              'world_maca': 130,
              'world_marshmallow_root': 20,
              'world_quinoa': 120,
              'world_sesame': 80,
              'world_star_anise': 60,
              'world_tea_leaf': 160,
              'world_yerba_mate': 150},
 'riverbank': {'chamomile': 1,
               'ginseng': 55,
               'lemon_balm': 1,
               'mint': 1,
               'moonflower': 55,
               'sage': 25,
               'star_moss': 25,
               'valerian': 55,
               'world_aloe_vera': 10,
               'world_arnica': 140,
               'world_burdock': 70,
               'world_calendula': 20,
               'world_comfrey': 150,
               'world_dandelion': 60,
               'world_echinacea': 30,
               'world_elderflower': 90,
               'world_hawthorn': 100,
               'world_hibiscus': 120,
               'world_horsetail': 80,
               'world_jasmine': 130,
               'world_lemongrass': 1,
               'world_mugwort': 160,
               'world_passionflower': 200,
               'world_ribwort_plantain': 50,
               'world_rosehip': 110,
               'world_skullcap': 190,
               'world_st_johns_wort': 40,
               'world_wormwood': 170,
               'yarrow': 25},
 'sage_meadow': {'sage': 1},
 'valerian_meadow': {'valerian': 1},
 'whisper_grove': {'ginseng': 25,
                   'lavender': 1,
                   'mandrake': 50,
                   'moonflower': 50,
                   'nightshade': 25,
                   'phoenix_leaf': 75,
                   'sage': 1,
                   'soulroot': 50,
                   'star_moss': 75,
                   'valerian': 1,
                   'world_amaranth': 110,
                   'world_anise': 50,
                   'world_black_cumin': 70,
                   'world_chia': 100,
                   'world_cocoa_pod': 190,
                   'world_coffee_berry': 170,
                   'world_cumin': 40,
                   'world_fenugreek': 30,
                   'world_flax': 90,
                   'world_guarana': 140,
                   'world_hops': 1,
                   'world_kola_nut': 200,
                   'world_licorice_root': 10,
                   'world_maca': 130,
                   'world_marshmallow_root': 20,
                   'world_quinoa': 120,
                   'world_sesame': 80,
                   'world_star_anise': 60,
                   'world_tea_leaf': 160,
                   'world_yerba_mate': 150},
 'yarrow_meadow': {'yarrow': 1}}


# Profil bazowy v0.8.76 jest zachowany wyłącznie do bezpiecznej migracji
# istniejących postaci. Nie jest używany przy tworzeniu nowych postaci.
V0876_RACE_BASE_STATS = {
    "Człowiek": {"strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 10, "willpower": 10},
    "Ogr": {"strength": 14, "dexterity": 8, "constitution": 14, "intelligence": 6, "willpower": 8},
    "Elf": {"strength": 8, "dexterity": 14, "constitution": 9, "intelligence": 13, "willpower": 11},
    "Krasnolud": {"strength": 12, "dexterity": 9, "constitution": 14, "intelligence": 9, "willpower": 12},
    "Ork": {"strength": 13, "dexterity": 10, "constitution": 13, "intelligence": 7, "willpower": 9},
    "Niziołek": {"strength": 7, "dexterity": 14, "constitution": 10, "intelligence": 10, "willpower": 11},
    "Mroczny Elf": {"strength": 9, "dexterity": 13, "constitution": 9, "intelligence": 14, "willpower": 10},
    "Gnom": {"strength": 7, "dexterity": 12, "constitution": 9, "intelligence": 14, "willpower": 13},
    "Smoczy": {"strength": 13, "dexterity": 9, "constitution": 13, "intelligence": 10, "willpower": 10},
    "Troll": {"strength": 15, "dexterity": 7, "constitution": 15, "intelligence": 5, "willpower": 8},
    "Diablę": {"strength": 9, "dexterity": 11, "constitution": 9, "intelligence": 13, "willpower": 13},
    "Aasimar": {"strength": 10, "dexterity": 10, "constitution": 11, "intelligence": 12, "willpower": 14},
    "Driada": {"strength": 7, "dexterity": 10, "constitution": 11, "intelligence": 15, "willpower": 15},
}

# v0.9.0: każda rasa ma dokładnie ten sam budżet 50 bazowych punktów
# w pięciu głównych statystykach. Różni się WYŁĄCZNIE rozkładem oraz
# pasywem rasowym. Usuwa to dawną ukrytą przewagę 50-58 punktów.
RACES = [
    ("Człowiek",
     "Wszechstronny. Wszystkie pięć głównych statystyk startuje na równym poziomie. "
     "Pasyw rasowy: +10 procent do zdobywanego Postępu Rozwoju statystyk.",
     10, 10, 10, 10, 10),
    ("Ogr",
     "Bardzo silny i wytrzymały. Wysoka Siła i Kondycja wspierają walkę wręcz. "
     "Pasyw rasowy: +12 procent obrażeń fizycznych.",
     14, 8, 14, 6, 8),
    ("Elf",
     "Bardzo zręczny, z wyraźnym talentem magicznym. "
     "Pasyw rasowy: +5 punktów procentowych do szansy uniku.",
     8, 14, 8, 12, 8),
    ("Krasnolud",
     "Bardzo odporny. Wysoka Kondycja i Siła Woli wspierają przetrwanie. "
     "Pasyw rasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń.",
     11, 7, 14, 6, 12),
    ("Ork",
     "Urodzony wojownik. Wysoka Siła i Kondycja dają mocne ciosy i dużo HP. "
     "Pasyw rasowy: +10 procent maksymalnego HP.",
     13, 9, 13, 7, 8),
    ("Niziołek",
     "Zręczny i szczęśliwy poszukiwacz. "
     "Pasyw rasowy: +3 punkty procentowe do szansy na bonusowy połów, dodatkową rudę lub dodatkowe drewno.",
     7, 14, 9, 10, 10),
    ("Mroczny Elf",
     "Zręczny i utalentowany magicznie. Dobrze łączy szybkość z ofensywną magią. "
     "Pasyw rasowy: +10 procent obrażeń magicznych.",
     8, 13, 8, 13, 8),
    ("Gnom",
     "Bardzo inteligentny, z dobrym zapasem Siły Woli. "
     "Pasyw rasowy: +15 procent maksymalnej Many.",
     7, 10, 8, 14, 11),
    ("Smoczy",
     "Silny, wytrzymały i wszechstronny w walce. "
     "Pasyw rasowy: +8 procent wszystkich zadawanych obrażeń, fizycznych i magicznych.",
     12, 9, 12, 9, 8),
    ("Troll",
     "Największa surowa Siła i Kondycja. Jest wolny i słaby magicznie, ale bardzo trudny do powalenia. "
     "Pasyw rasowy: 12 procent redukcji otrzymywanych obrażeń fizycznych.",
     15, 7, 15, 5, 8),
    ("Diablę",
     "Dobre predyspozycje magiczne i silna więź z energią dusz. "
     "Pasyw rasowy: +10 procent zdobywanego Soul XP Broni Duszy.",
     8, 10, 8, 13, 11),
    ("Aasimar",
     "Silna Siła Woli i dobre predyspozycje obronne. "
     "Pasyw rasowy: +12 procent obrony magicznej.",
     9, 9, 10, 10, 12),
    ("Driada",
     "Rasa natury nastawiona na życie, magię i odnowę. "
     "Pasyw rasowy: +15 procent mocy wszystkich klasowych umiejętności leczących. "
     "Szczególnie dobrze pasuje do Kapłana i Druida.",
     7, 9, 10, 12, 12),
]

# v0.8.46: rekomendacje klas są wskazówką dla nowych graczy, nie ograniczeniem.
# Każda rasa nadal może wybrać każdą z 12 klas.
RACE_CLASS_RECOMMENDATIONS = {
    "Człowiek": {
        "classes": ["Wojownik", "Łotrzyk", "Mag", "Kapłan", "Druid", "Psionik"],
        "reason": "jest wszechstronny i rozwija statystyki szybciej, więc dobrze sprawdza się praktycznie w każdej roli",
    },
    "Ogr": {
        "classes": ["Wojownik", "Berserker", "Strażnik", "Mnich"],
        "reason": "bardzo wysoka Siła i Kondycja oraz bonus do obrażeń fizycznych najlepiej wspierają klasy walczące fizycznie",
    },
    "Elf": {
        "classes": ["Łotrzyk", "Łowca", "Mag", "Druid", "Psionik"],
        "reason": "wysoka Zręczność i Inteligencja łączą szybkie klasy fizyczne z klasami magicznymi",
    },
    "Krasnolud": {
        "classes": ["Strażnik", "Wojownik", "Kapłan", "Psionik"],
        "reason": "wysoka Kondycja i Siła Woli wzmacniają przetrwanie, gardy i odporność magiczną",
    },
    "Ork": {
        "classes": ["Wojownik", "Berserker", "Strażnik", "Mnich"],
        "reason": "wysoka Siła, Kondycja i dodatkowe maksymalne HP sprzyjają bezpośredniej walce",
    },
    "Niziołek": {
        "classes": ["Łotrzyk", "Łowca", "Mnich"],
        "reason": "bardzo wysoka Zręczność dobrze współpracuje z unikami, szybkością i precyzyjnymi atakami",
    },
    "Mroczny Elf": {
        "classes": ["Mag", "Czarownik", "Nekromanta", "Łotrzyk", "Psionik"],
        "reason": "wysoka Inteligencja i Zręczność oraz bonus do obrażeń magicznych wspierają ofensywną magię i szybkie buildy",
    },
    "Gnom": {
        "classes": ["Mag", "Psionik", "Nekromanta", "Kapłan", "Czarownik"],
        "reason": "najwyższa startowa Inteligencja wśród ras i większa maksymalna Mana mocno wspierają klasy magiczne",
    },
    "Smoczy": {
        "classes": ["Wojownik", "Berserker", "Strażnik", "Czarownik", "Mag"],
        "reason": "bonus do wszystkich obrażeń pozwala skutecznie grać zarówno fizycznie, jak i magicznie",
    },
    "Troll": {
        "classes": ["Berserker", "Strażnik", "Wojownik", "Mnich"],
        "reason": "najwyższa Siła i Kondycja oraz redukcja obrażeń fizycznych czynią go bardzo mocnym wojownikiem wręcz",
    },
    "Diablę": {
        "classes": ["Czarownik", "Nekromanta", "Mag", "Psionik"],
        "reason": "dobra Inteligencja i Siła Woli sprzyjają magii, a bonus Soul XP wspiera szybki rozwój Broni Duszy",
    },
    "Aasimar": {
        "classes": ["Kapłan", "Psionik", "Druid", "Strażnik"],
        "reason": "wysoka Siła Woli i rasowa obrona magiczna wspierają leczenie, obronę magiczną i klasy defensywne",
    },
    "Driada": {
        "classes": ["Druid", "Kapłan", "Psionik", "Mag"],
        "reason": "profil Inteligencji i Siły Woli oraz rasowy bonus do leczenia szczególnie wspierają klasy magiczne i lecznicze",
    },
}

def race_class_recommendation_text(race_name):
    data = RACE_CLASS_RECOMMENDATIONS.get(race_name)
    if not data:
        return ""
    return f"Polecane klasy: {', '.join(data['classes'])}. Dlaczego: {data['reason']}."

# v0.9.0: bazowa Moc Broni Duszy ma wąski zakres 7-8 zamiast 6-9.
# Różnice klas nadal wynikają ze skilli, pasywów i specjalizacji Soul Tier,
# ale żaden archetyp nie zaczyna z ukrytą karą/bonusem 50% w weapon_base.
CLASSES = [
    ("Wojownik", "physical", "Miecz Przysięgi", 7),
    ("Berserker", "physical", "Topór Krwi", 8),
    ("Łotrzyk", "physical", "Sztylety Cienia", 7),
    ("Łowca", "physical", "Łuk Echa", 7),
    ("Mnich", "physical", "Rękawice Ducha", 7),
    ("Strażnik", "physical", "Młot Bastionu", 7),
    ("Mag", "magic", "Kostur Arkanów", 7),
    ("Nekromanta", "magic", "Kosa Dusz", 8),
    ("Kapłan", "magic", "Młot Światła", 7),
    ("Czarownik", "magic", "Ostrze Otchłani", 8),
    ("Druid", "magic", "Kostur Korzeni", 7),
    ("Psionik", "magic", "Kryształ Umysłu", 7),
]

# v0.30.17: Broń Duszy jest aktywną bronią autoataku, nie tylko ukrytym bonusem.
SOUL_WEAPON_ATTACK_TECHNIQUES = {
    "Wojownik": "Cięcie Przysięgi",
    "Berserker": "Rąbnięcie Krwi",
    "Łotrzyk": "Podwójne Ukłucie Cienia",
    "Łowca": "Strzał Echa",
    "Mnich": "Cios Ducha",
    "Strażnik": "Uderzenie Bastionu",
    "Mag": "Impuls Arkanów",
    "Nekromanta": "Żniwo Dusz",
    "Kapłan": "Uderzenie Światła",
    "Czarownik": "Cięcie Otchłani",
    "Druid": "Cios Korzeni",
    "Psionik": "Impuls Umysłu",
}

# v0.8.51: klasa nadaje własny profil startowych statystyk.
# Maksymalne HP i Mana nie są wpisane na sztywno dla klasy: wynikają potem
# bezpośrednio z Kondycji i Inteligencji oraz bonusów rasy/ekwipunku.
# Profil klasowy v0.8.76 pozostaje dostępny tylko dla migracji starych save'ów.
V0876_CLASS_STARTING_STAT_BONUSES = {
    "Wojownik":   {"strength": 3, "dexterity": 1, "constitution": 3, "intelligence": 0, "willpower": 1, "charisma": 0},
    "Berserker":  {"strength": 4, "dexterity": 1, "constitution": 3, "intelligence": 0, "willpower": 0, "charisma": 0},
    "Łotrzyk":    {"strength": 1, "dexterity": 4, "constitution": 1, "intelligence": 1, "willpower": 0, "charisma": 1},
    "Łowca":      {"strength": 2, "dexterity": 4, "constitution": 2, "intelligence": 0, "willpower": 0, "charisma": 0},
    "Mnich":      {"strength": 1, "dexterity": 3, "constitution": 2, "intelligence": 1, "willpower": 2, "charisma": 0},
    "Strażnik":   {"strength": 2, "dexterity": 0, "constitution": 4, "intelligence": 0, "willpower": 2, "charisma": 0},
    "Mag":        {"strength": 0, "dexterity": 2, "constitution": 1, "intelligence": 4, "willpower": 2, "charisma": 0},
    "Nekromanta": {"strength": 0, "dexterity": 1, "constitution": 2, "intelligence": 3, "willpower": 3, "charisma": 0},
    "Kapłan":     {"strength": 0, "dexterity": 0, "constitution": 3, "intelligence": 2, "willpower": 4, "charisma": 0},
    "Czarownik":  {"strength": 1, "dexterity": 2, "constitution": 1, "intelligence": 4, "willpower": 1, "charisma": 0},
    "Druid":      {"strength": 0, "dexterity": 1, "constitution": 3, "intelligence": 3, "willpower": 3, "charisma": 0},
    "Psionik":    {"strength": 0, "dexterity": 2, "constitution": 1, "intelligence": 3, "willpower": 4, "charisma": 0},
}

# v0.9.0: każda klasa dokłada dokładnie 9 punktów startowych.
# Dzięki temu o sile startu nie decyduje ukryty budżet 8-10, tylko profil
# klasy, pasyw, skille i Broń Duszy.
CLASS_STARTING_STAT_BONUSES = {
    "Wojownik":   {"strength": 4, "dexterity": 1, "constitution": 3, "intelligence": 0, "willpower": 1, "charisma": 0},
    "Berserker":  {"strength": 4, "dexterity": 2, "constitution": 3, "intelligence": 0, "willpower": 0, "charisma": 0},
    "Łotrzyk":    {"strength": 1, "dexterity": 4, "constitution": 1, "intelligence": 1, "willpower": 1, "charisma": 1},
    "Łowca":      {"strength": 2, "dexterity": 4, "constitution": 2, "intelligence": 0, "willpower": 1, "charisma": 0},
    "Mnich":      {"strength": 1, "dexterity": 4, "constitution": 2, "intelligence": 1, "willpower": 1, "charisma": 0},
    "Strażnik":   {"strength": 2, "dexterity": 0, "constitution": 4, "intelligence": 0, "willpower": 3, "charisma": 0},
    "Mag":        {"strength": 0, "dexterity": 2, "constitution": 1, "intelligence": 4, "willpower": 2, "charisma": 0},
    "Nekromanta": {"strength": 0, "dexterity": 1, "constitution": 2, "intelligence": 4, "willpower": 2, "charisma": 0},
    "Kapłan":     {"strength": 0, "dexterity": 0, "constitution": 3, "intelligence": 2, "willpower": 4, "charisma": 0},
    "Czarownik":  {"strength": 1, "dexterity": 2, "constitution": 1, "intelligence": 4, "willpower": 1, "charisma": 0},
    "Druid":      {"strength": 0, "dexterity": 1, "constitution": 2, "intelligence": 4, "willpower": 2, "charisma": 0},
    "Psionik":    {"strength": 0, "dexterity": 1, "constitution": 1, "intelligence": 3, "willpower": 4, "charisma": 0},
}

def class_starting_stat_bonus(class_name, stat_name):
    return int(CLASS_STARTING_STAT_BONUSES.get(class_name, {}).get(stat_name, 0))

def class_starting_stats_for(race, cls):
    rname, _desc, strength, dexterity, constitution, intelligence, willpower = race
    cname = cls[0]
    b = CLASS_STARTING_STAT_BONUSES.get(cname, {})
    return {
        "strength": int(strength) + int(b.get("strength", 0)),
        "dexterity": int(dexterity) + int(b.get("dexterity", 0)),
        "constitution": int(constitution) + int(b.get("constitution", 0)),
        "intelligence": int(intelligence) + int(b.get("intelligence", 0)),
        "willpower": int(willpower) + int(b.get("willpower", 0)),
        "charisma": 10 + int(b.get("charisma", 0)),
    }

def starting_hp_mana_for(race, cls):
    stats = class_starting_stats_for(race, cls)
    hp = 40 + stats["constitution"] * 5
    mana = int(round(20 + stats["intelligence"] * 2.5 + stats["willpower"] * 2.5))
    race_name = race[0]
    if race_name == "Ork":
        hp = int(round(hp * 1.10))
    if race_name == "Gnom":
        mana = int(round(mana * 1.15))
    return max(1, hp), max(0, mana)


CLASS_DESCRIPTIONS = {
    "Wojownik": (
        "Klasa fizyczna. Stabilny wojownik do walki wręcz. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobra dla graczy chcących mocnych ciosów, szybkości i dużej ilości HP."
        "Pasyw klasowy: +10 procent obrażeń fizycznych."
    ),
    "Berserker": (
        "Klasa fizyczna nastawiona na bardzo wysokie obrażenia. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Broń Duszy ma wysoki bazowy potencjał ofensywny."
        "Pasyw klasowy: +12 procent obrażeń fizycznych."
    ),
    "Łotrzyk": (
        "Klasa fizyczna nastawiona na szybkość i zwinność. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze korzysta z wysokiej Zręczności i uników."
        "Pasyw klasowy: +5 punktów procentowych do szansy uniku."
    ),
    "Łowca": (
        "Klasa fizyczna walcząca z dystansu. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Najlepiej współpracuje z rasami o wysokiej Zręczności."
        "Pasyw klasowy: +8 procent obrażeń fizycznych."
    ),
    "Mnich": (
        "Klasa fizyczna oparta na szybkości i kontroli ciała. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze skaluje się ze Zręcznością oraz Kondycją."
        "Pasyw klasowy: +8 procent mocy klasowych umiejętności leczących."
    ),
    "Strażnik": (
        "Klasa fizyczna nastawiona na przetrwanie. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze wykorzystuje wysoką Kondycję i cięższy pancerz."
        "Pasyw klasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń."
    ),
    "Mag": (
        "Klasa magiczna. Inteligencja zwiększa moc czarów i ataków Bronią Duszy, a Inteligencja razem z Siłą Woli zwiększają Manę, "
        "Zręczność daje szybkość, unik i krytyki, Kondycja zwiększa HP, a Siła Woli obronę magiczną. "
        "Każda z sześciu statystyk ma własny automatyczny EXP."
        "Pasyw klasowy: +10 procent obrażeń magicznych."
    ),
    "Nekromanta": (
        "Klasa magiczna oparta na mrocznej energii i silnych czarach. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze korzysta z wysokiej Inteligencji."
        "Pasyw klasowy: +15 procent leczenia z umiejętności wysysających życie."
    ),
    "Kapłan": (
        "Klasa magiczna o defensywnym charakterze. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Wysoka Siła Woli wzmacnia obronę magiczną."
        "Pasyw klasowy: +10 procent mocy klasowych umiejętności leczących."
    ),
    "Czarownik": (
        "Ofensywna klasa magiczna z mocną Bronią Duszy. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze skaluje się z Inteligencją i dużą pulą Many."
        "Pasyw klasowy: +12 procent obrażeń magicznych."
    ),
    "Druid": (
        "Wszechstronna klasa magiczna związana z naturą. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Łączy dobrą moc czarów z obroną magiczną."
        "Pasyw klasowy: +10 procent mocy klasowych umiejętności leczących."
    ),
    "Psionik": (
        "Klasa magiczna oparta na mocy umysłu. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Najlepiej wykorzystuje wysoką Inteligencję i Siłę Woli."
        "Pasyw klasowy: +10 procent obrony magicznej."
    ),
}


CLASS_SKILLS = {'Wojownik': [{'id': 'warrior_power_slash',
               'name': 'Potężne Cięcie',
               'aliases': ['potezne ciecie', 'potężne cięcie', 'power slash'],
               'unlock': 1,
               'kind': 'damage',
               'cooldown': 4,
               'mana': 0,
               'desc': 'Mocny fizyczny cios skalowany Siłą.',
               'scale': 'strength',
               'mult': 1.35},
              {'id': 'warrior_war_cry',
               'name': 'Okrzyk Wojenny',
               'aliases': ['okrzyk wojenny', 'war cry'],
               'unlock': 20,
               'kind': 'boost',
               'cooldown': 12,
               'mana': 0,
               'desc': 'Przez 12 sekund wzmacnia wszystkie skille i spelle o 35 procent.',
               'boost': 1.35,
               'duration': 12},
              {'id': 'warrior_unbreakable',
               'name': 'Niezłomność',
               'aliases': ['niezlomnosc', 'niezłomność', 'unbreakable'],
               'unlock': 60,
               'kind': 'guard',
               'cooldown': 15,
               'mana': 0,
               'desc': 'Zmniejsza obrażenia następnego trafienia o dodatkowe 18.',
               'guard': 18}],
 'Berserker': [{'id': 'berserker_blood_swing',
                'name': 'Krwawy Zamach',
                'aliases': ['krwawy zamach', 'blood swing'],
                'unlock': 1,
                'kind': 'damage',
                'cooldown': 5,
                'mana': 0,
                'desc': 'Bardzo mocny cios Siłą, ale kosztuje 4 HP.',
                'scale': 'strength',
                'mult': 1.5,
                'self_damage': 4},
               {'id': 'berserker_blood_fury',
                'name': 'Szał Krwi',
                'aliases': ['szal krwi', 'szał krwi', 'blood fury'],
                'unlock': 20,
                'kind': 'boost',
                'cooldown': 13,
                'mana': 0,
                'desc': 'Czasowo wzmacnia wszystkie skille i spelle o 55 procent.',
                'boost': 1.55},
               {'id': 'berserker_execution',
                'name': 'Egzekucja',
                'aliases': ['egzekucja', 'execution'],
                'unlock': 60,
                'kind': 'execute',
                'cooldown': 10,
                'mana': 0,
                'desc': 'Silny cios, wyjątkowo mocny poniżej 35 procent HP celu.',
                'scale': 'strength',
                'mult': 1.45,
                'execute_mult': 1.9}],
 'Łotrzyk': [{'id': 'rogue_shadow_strike',
              'name': 'Cios z Cienia',
              'aliases': ['cios z cienia', 'shadow strike'],
              'unlock': 1,
              'kind': 'damage',
              'cooldown': 4,
              'mana': 0,
              'desc': 'Szybki atak skalowany Zręcznością.',
              'scale': 'dexterity',
              'mult': 1.38},
             {'id': 'rogue_double_blade',
              'name': 'Podwójne Ostrze',
              'aliases': ['podwojne ostrze', 'podwójne ostrze', 'double blade'],
              'unlock': 20,
              'kind': 'damage',
              'cooldown': 8,
              'mana': 0,
              'desc': 'Seria dwóch cięć jako jeden silny atak.',
              'scale': 'dexterity',
              'mult': 1.68},
             {'id': 'rogue_vanish',
              'name': 'Zniknięcie',
              'aliases': ['znikniecie', 'zniknięcie', 'vanish'],
              'unlock': 60,
              'kind': 'evade',
              'cooldown': 12,
              'mana': 0,
              'desc': 'Gwarantuje unik następnego ataku przeciwnika.'}],
 'Łowca': [{'id': 'hunter_precise_shot',
            'name': 'Celny Strzał',
            'aliases': ['celny strzal', 'celny strzał', 'precise shot'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 4,
            'mana': 0,
            'desc': 'Precyzyjny atak dystansowy skalowany Zręcznością.',
            'scale': 'dexterity',
            'mult': 1.42},
           {'id': 'hunter_echo_volley',
            'name': 'Salwa Echa',
            'aliases': ['salwa echa', 'echo volley'],
            'unlock': 20,
            'kind': 'damage',
            'cooldown': 8,
            'mana': 0,
            'desc': 'Potężna salwa z Łuku Echa.',
            'scale': 'dexterity',
            'mult': 1.72},
           {'id': 'hunter_instinct',
            'name': 'Instynkt Łowcy',
            'aliases': ['instynkt lowcy', 'instynkt łowcy', 'hunter instinct'],
            'unlock': 60,
            'kind': 'evade',
            'cooldown': 10,
            'mana': 0,
            'desc': 'Gwarantuje unik następnego ataku przeciwnika.'}],
 'Mnich': [{'id': 'monk_spirit_punch',
            'name': 'Uderzenie Ducha',
            'aliases': ['uderzenie ducha', 'spirit punch'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 3,
            'mana': 0,
            'desc': 'Szybkie uderzenie skalowane Zręcznością.',
            'scale': 'dexterity',
            'mult': 1.32},
           {'id': 'monk_combo',
            'name': 'Seria Ciosów',
            'aliases': ['seria ciosow', 'seria ciosów', 'combo'],
            'unlock': 20,
            'kind': 'damage',
            'cooldown': 7,
            'mana': 0,
            'desc': 'Szybka kombinacja kilku uderzeń.',
            'scale': 'dexterity',
            'mult': 1.65},
           {'id': 'monk_meditation',
            'name': 'Medytacja',
            'aliases': ['medytacja', 'meditation'],
            'unlock': 60,
            'kind': 'heal',
            'cooldown': 16,
            'mana': 0,
            'desc': 'Przywraca 28 procent maksymalnego HP.',
            'heal_pct': 0.28}],
 'Strażnik': [{'id': 'guardian_crushing_blow',
               'name': 'Miażdżący Cios',
               'aliases': ['miazdzacy cios', 'miażdżący cios', 'crushing blow'],
               'unlock': 1,
               'kind': 'damage',
               'cooldown': 4,
               'mana': 0,
               'desc': 'Ciężki fizyczny cios Młotem Bastionu.',
               'scale': 'strength',
               'mult': 1.28},
              {'id': 'guardian_bastion',
               'name': 'Bastion',
               'aliases': ['bastion'],
               'unlock': 20,
               'kind': 'guard',
               'cooldown': 11,
               'mana': 0,
               'desc': 'Zmniejsza obrażenia następnego trafienia o dodatkowe 22.',
               'guard': 22},
              {'id': 'guardian_soul_wall',
               'name': 'Mur Duszy',
               'aliases': ['mur duszy', 'soul wall'],
               'unlock': 60,
               'kind': 'guard',
               'cooldown': 18,
               'mana': 0,
               'desc': 'Potężna osłona redukująca następne trafienie o 35.',
               'guard': 35}],
 'Mag': [{'id': 'mage_arcane_bolt',
          'name': 'Pocisk Arkanów',
          'aliases': ['pocisk arkanow', 'pocisk arkanów', 'arcane bolt'],
          'unlock': 1,
          'kind': 'damage',
          'cooldown': 3,
          'mana': 6,
          'desc': 'Podstawowy czar ofensywny skalowany Inteligencją.',
          'scale': 'intelligence',
          'mult': 1.42},
         {'id': 'mage_chain_energy',
          'name': 'Łańcuch Energii',
          'aliases': ['lancuch energii', 'łańcuch energii', 'chain energy'],
          'unlock': 20,
          'kind': 'damage',
          'cooldown': 7,
          'mana': 12,
          'desc': 'Silny impuls energii magicznej.',
          'scale': 'intelligence',
          'mult': 1.78},
         {'id': 'mage_arcane_barrier',
          'name': 'Bariera Arkanów',
          'aliases': ['bariera arkanow', 'bariera arkanów', 'arcane barrier'],
          'unlock': 60,
          'kind': 'guard',
          'cooldown': 13,
          'mana': 10,
          'desc': 'Magiczna bariera redukująca następne trafienie o 24.',
          'guard': 24}],
 'Nekromanta': [{'id': 'necro_death_touch',
                 'name': 'Dotyk Śmierci',
                 'aliases': ['dotyk smierci', 'dotyk śmierci', 'death touch'],
                 'unlock': 1,
                 'kind': 'damage',
                 'cooldown': 4,
                 'mana': 6,
                 'desc': 'Mroczny atak magiczny skalowany Inteligencją.',
                 'scale': 'intelligence',
                 'mult': 1.38},
                {'id': 'necro_soul_drain',
                 'name': 'Wysysanie Duszy',
                 'aliases': ['wysysanie duszy', 'soul drain'],
                 'unlock': 20,
                 'kind': 'drain',
                 'cooldown': 8,
                 'mana': 10,
                 'desc': 'Zadaje obrażenia i leczy za 45 procent zadanych obrażeń.',
                 'scale': 'intelligence',
                 'mult': 1.45,
                 'drain_pct': 0.45},
                {'id': 'necro_soul_reaping',
                 'name': 'Żniwo Dusz',
                 'aliases': ['zniwo dusz', 'żniwo dusz', 'soul reaping'],
                 'unlock': 60,
                 'kind': 'execute',
                 'cooldown': 11,
                 'mana': 16,
                 'desc': 'Potężny czar silniejszy poniżej 35 procent HP celu.',
                 'scale': 'intelligence',
                 'mult': 1.65,
                 'execute_mult': 1.75}],
 'Kapłan': [{'id': 'priest_small_heal',
             'name': 'Małe Leczenie',
             'aliases': ['male leczenie', 'małe leczenie', 'small heal'],
             'unlock': 1,
             'kind': 'heal',
             'cooldown': 6,
             'mana': 3,
             'desc': 'Podstawowe leczenie dla początkujących Kapłanów. Przywraca 12 procent maksymalnego HP i rośnie wraz ze Skill Level.',
             'heal_pct': 0.12},
            {'id': 'priest_holy_hammer',
             'name': 'Święty Młot',
             'aliases': ['swiety mlot', 'święty młot', 'holy hammer'],
             'unlock': 1,
             'kind': 'damage',
             'cooldown': 4,
             'mana': 5,
             'desc': 'Święty atak magiczny skalowany Inteligencją.',
             'scale': 'intelligence',
             'mult': 1.28},
            {'id': 'priest_great_heal',
             'name': 'Wielkie Leczenie',
             'aliases': ['wielkie leczenie', 'great heal'],
             'unlock': 20,
             'kind': 'heal',
             'cooldown': 14,
             'mana': 10,
             'desc': 'Przywraca 38 procent maksymalnego HP.',
             'heal_pct': 0.38},
            {'id': 'priest_divine_shield',
             'name': 'Boska Tarcza',
             'aliases': ['boska tarcza', 'divine shield'],
             'unlock': 60,
             'kind': 'guard',
             'cooldown': 17,
             'mana': 12,
             'desc': 'Silna tarcza redukująca następne trafienie o 32.',
             'guard': 32}],
 'Czarownik': [{'id': 'warlock_void_blade',
                'name': 'Ostrze Otchłani',
                'aliases': ['ostrze otchlani', 'ostrze otchłani', 'void blade'],
                'unlock': 1,
                'kind': 'damage',
                'cooldown': 4,
                'mana': 7,
                'desc': 'Ofensywny czar Ostrza Otchłani.',
                'scale': 'intelligence',
                'mult': 1.48},
               {'id': 'warlock_void_flame',
                'name': 'Płomień Otchłani',
                'aliases': ['plomien otchlani', 'płomień otchłani', 'void flame'],
                'unlock': 20,
                'kind': 'damage',
                'cooldown': 8,
                'mana': 13,
                'desc': 'Bardzo mocny magiczny atak.',
                'scale': 'intelligence',
                'mult': 1.85},
               {'id': 'warlock_blood_pact',
                'name': 'Pakt Krwi',
                'aliases': ['pakt krwi', 'blood pact'],
                'unlock': 60,
                'kind': 'damage',
                'cooldown': 12,
                'mana': 8,
                'desc': 'Ekstremalnie silny czar kosztujący dodatkowo 10 procent maksymalnego HP.',
                'scale': 'intelligence',
                'mult': 2.15,
                'self_damage_pct': 0.1}],
 'Druid': [{'id': 'druid_thorns',
            'name': 'Ciernie',
            'aliases': ['ciernie', 'thorns'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 4,
            'mana': 5,
            'desc': 'Magiczny atak natury skalowany Inteligencją.',
            'scale': 'intelligence',
            'mult': 1.32},
           {'id': 'druid_nature_heal',
            'name': 'Uzdrowienie Natury',
            'aliases': ['uzdrowienie natury', 'nature heal'],
            'unlock': 20,
            'kind': 'heal',
            'cooldown': 13,
            'mana': 9,
            'desc': 'Przywraca 32 procent maksymalnego HP.',
            'heal_pct': 0.32},
           {'id': 'druid_storm_wrath',
            'name': 'Gniew Burzy',
            'aliases': ['gniew burzy', 'storm wrath'],
            'unlock': 60,
            'kind': 'damage',
            'cooldown': 10,
            'mana': 15,
            'desc': 'Potężny czar burzy.',
            'scale': 'intelligence',
            'mult': 1.92}],
 'Psionik': [{'id': 'psion_mind_pulse',
              'name': 'Impuls Umysłu',
              'aliases': ['impuls umyslu', 'impuls umysłu', 'mind pulse'],
              'unlock': 1,
              'kind': 'damage',
              'cooldown': 3,
              'mana': 5,
              'desc': 'Szybki psioniczny atak skalowany Inteligencją.',
              'scale': 'intelligence',
              'mult': 1.38},
             {'id': 'psion_psionic_wave',
              'name': 'Fala Psioniczna',
              'aliases': ['fala psioniczna', 'psionic wave'],
              'unlock': 20,
              'kind': 'damage',
              'cooldown': 7,
              'mana': 11,
              'desc': 'Silna fala energii umysłu.',
              'scale': 'intelligence',
              'mult': 1.75},
             {'id': 'psion_mind_barrier',
              'name': 'Bariera Umysłu',
              'aliases': ['bariera umyslu', 'bariera umysłu', 'mind barrier'],
              'unlock': 60,
              'kind': 'guard',
              'cooldown': 14,
              'mana': 10,
              'desc': 'Psioniczna bariera redukująca następne obrażenia o 28.',
              'guard': 28}]}


ENDGAME_CLASS_SKILLS = {
    "Wojownik": [
        {
            "id": "warrior_soul_rend",
            "name": "Rozcięcie Duszy Bohatera",
            "aliases": ["rozciecie duszy bohatera", "rozcięcie duszy bohatera", "hero soul slash"],
            "natural_tags": ["ciecie", "slash", "dusza"],
            "unlock": 100, "kind": "damage", "cooldown": 8, "mana": 0,
            "desc": "Silne cięcie końcowego etapu Wojownika.",
            "scale": "strength", "mult": 2.10,
        },
        {
            "id": "warrior_iron_wall",
            "name": "Żelazny Mur",
            "aliases": ["zelazny mur", "żelazny mur", "iron wall"],
            "natural_tags": ["tarcza", "oslona", "guard", "obrona"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 0,
            "desc": "Potężna osłona Wojownika redukująca następne trafienie.",
            "guard": 58,
        },
        {
            "id": "warrior_hero_charge",
            "name": "Szarża Bohatera",
            "aliases": ["szarza bohatera", "szarża bohatera", "hero charge"],
            "natural_tags": ["szarza", "charge", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 0,
            "desc": "Mocna szarża skalowana Siłą.",
            "scale": "strength", "mult": 2.55,
        },
        {
            "id": "warrior_final_slash",
            "name": "Ostateczne Cięcie",
            "aliases": ["ostateczne ciecie", "ostateczne cięcie", "final slash"],
            "natural_tags": ["ciecie", "slash", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 16, "mana": 0,
            "desc": "Najsilniejsze cięcie Wojownika, szczególnie groźne na osłabionym celu.",
            "scale": "strength", "mult": 2.55, "execute_mult": 1.90,
        },
    ],
    "Berserker": [
        {
            "id": "berserker_butcher_swing",
            "name": "Rzeźniczy Zamach",
            "aliases": ["rzezniczy zamach", "rzeźniczy zamach", "butcher swing"],
            "natural_tags": ["zamach", "ciecie", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 8, "mana": 0,
            "desc": "Brutalny zamach Berserkera skalowany Siłą.",
            "scale": "strength", "mult": 2.20,
        },
        {
            "id": "berserker_titan_rage",
            "name": "Szał Tytana",
            "aliases": ["szal tytana", "szał tytana", "titan rage"],
            "natural_tags": ["szal", "rage", "buff", "wzmocnienie"],
            "unlock": 140, "kind": "boost", "cooldown": 15, "mana": 0,
            "desc": "Czasowo wzmacnia wszystkie skille i spelle.",
            "boost": 1.65,
        },
        {
            "id": "berserker_blood_whirl",
            "name": "Krwawy Wir",
            "aliases": ["krwawy wir", "blood whirl"],
            "natural_tags": ["krew", "wir", "drain", "wysysanie"],
            "unlock": 180, "kind": "drain", "cooldown": 12, "mana": 0,
            "desc": "Krwawy atak, który przywraca część zadanych obrażeń jako HP.",
            "scale": "strength", "mult": 2.45, "drain_pct": 0.35,
        },
        {
            "id": "berserker_blood_apocalypse",
            "name": "Apokalipsa Krwi",
            "aliases": ["apokalipsa krwi", "blood apocalypse"],
            "natural_tags": ["krew", "apokalipsa", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 0,
            "desc": "Ostateczny atak Berserkera, jeszcze silniejszy na osłabionym przeciwniku.",
            "scale": "strength", "mult": 2.65, "execute_mult": 1.95,
        },
    ],
    "Łotrzyk": [
        {
            "id": "rogue_spectral_cut",
            "name": "Cięcie Widma",
            "aliases": ["ciecie widma", "cięcie widma", "spectral cut"],
            "natural_tags": ["ciecie", "slash", "widmo"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 0,
            "desc": "Błyskawiczne cięcie skalowane Zręcznością.",
            "scale": "dexterity", "mult": 2.05,
        },
        {
            "id": "rogue_shadow_step",
            "name": "Krok Cienia",
            "aliases": ["krok cienia", "shadow step"],
            "natural_tags": ["unik", "evade", "cien"],
            "unlock": 140, "kind": "evade", "cooldown": 11, "mana": 0,
            "desc": "Gwarantuje unik następnego ataku przeciwnika.",
        },
        {
            "id": "rogue_blade_dance",
            "name": "Taniec Ostrzy",
            "aliases": ["taniec ostrzy", "blade dance"],
            "natural_tags": ["ostrza", "taniec", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 0,
            "desc": "Seria szybkich cięć skalowana Zręcznością.",
            "scale": "dexterity", "mult": 2.55,
        },
        {
            "id": "rogue_shadow_execution",
            "name": "Egzekucja Cienia",
            "aliases": ["egzekucja cienia", "shadow execution"],
            "natural_tags": ["egzekucja", "execute", "dobij", "cien"],
            "unlock": 200, "kind": "execute", "cooldown": 15, "mana": 0,
            "desc": "Kończący cios Łotrzyka na osłabionego przeciwnika.",
            "scale": "dexterity", "mult": 2.50, "execute_mult": 2.00,
        },
    ],
    "Łowca": [
        {
            "id": "hunter_soul_arrow",
            "name": "Strzała Duszy",
            "aliases": ["strzala duszy", "strzała duszy", "soul arrow"],
            "natural_tags": ["strzala", "arrow", "strzal"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 0,
            "desc": "Silny strzał skalowany Zręcznością.",
            "scale": "dexterity", "mult": 2.10,
        },
        {
            "id": "hunter_predator_camouflage",
            "name": "Kamuflaż Drapieżcy",
            "aliases": ["kamuflaz drapieznika", "kamuflaż drapieżcy", "predator camouflage"],
            "natural_tags": ["unik", "evade", "kamuflaz"],
            "unlock": 140, "kind": "evade", "cooldown": 12, "mana": 0,
            "desc": "Pozwala uniknąć następnego ataku przeciwnika.",
        },
        {
            "id": "hunter_echo_rain",
            "name": "Deszcz Echa",
            "aliases": ["deszcz echa", "echo rain"],
            "natural_tags": ["deszcz", "strzaly", "arrow", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 0,
            "desc": "Potężna salwa skalowana Zręcznością.",
            "scale": "dexterity", "mult": 2.60,
        },
        {
            "id": "hunter_final_shot",
            "name": "Strzał Końca",
            "aliases": ["strzal konca", "strzał końca", "final shot"],
            "natural_tags": ["strzal", "shot", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 16, "mana": 0,
            "desc": "Ostateczny strzał Łowcy, wyjątkowo mocny na osłabionym celu.",
            "scale": "dexterity", "mult": 2.55, "execute_mult": 1.90,
        },
    ],
    "Mnich": [
        {
            "id": "monk_soul_fist",
            "name": "Pięść Duszy",
            "aliases": ["piesc duszy", "pięść duszy", "soul fist"],
            "natural_tags": ["piesc", "fist", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 0,
            "desc": "Skoncentrowane uderzenie skalowane Siłą.",
            "scale": "strength", "mult": 2.05,
        },
        {
            "id": "monk_master_meditation",
            "name": "Medytacja Mistrza",
            "aliases": ["medytacja mistrza", "master meditation"],
            "natural_tags": ["heal", "leczenie", "medytacja", "odnowa"],
            "unlock": 140, "kind": "heal", "cooldown": 12, "mana": 0,
            "desc": "Zaawansowana medytacja przywracająca dużą część HP.",
            "heal_pct": 0.38,
        },
        {
            "id": "monk_dragon_combo",
            "name": "Smocza Seria",
            "aliases": ["smocza seria", "dragon combo"],
            "natural_tags": ["seria", "combo", "smok", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 0,
            "desc": "Szybka seria ciosów o wysokiej sile.",
            "scale": "strength", "mult": 2.50,
        },
        {
            "id": "monk_enlightened_strike",
            "name": "Cios Oświecenia",
            "aliases": ["cios oswiecenia", "cios oświecenia", "enlightened strike"],
            "natural_tags": ["cios", "oswiecenie", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 15, "mana": 0,
            "desc": "Ostateczny cios Mnicha, silniejszy na osłabionym przeciwniku.",
            "scale": "strength", "mult": 2.45, "execute_mult": 1.90,
        },
    ],
    "Strażnik": [
        {
            "id": "guardian_fortress_strike",
            "name": "Uderzenie Fortecy",
            "aliases": ["uderzenie fortecy", "fortress strike"],
            "natural_tags": ["uderzenie", "mlot", "hammer", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 0,
            "desc": "Ciężkie uderzenie skalowane Siłą.",
            "scale": "strength", "mult": 2.00,
        },
        {
            "id": "guardian_eternal_bastion",
            "name": "Wieczny Bastion",
            "aliases": ["wieczny bastion", "eternal bastion"],
            "natural_tags": ["tarcza", "bastion", "guard", "obrona"],
            "unlock": 140, "kind": "guard", "cooldown": 14, "mana": 0,
            "desc": "Najpotężniejsza osłona Strażnika.",
            "guard": 72,
        },
        {
            "id": "guardian_bastion_wrath",
            "name": "Gniew Bastionu",
            "aliases": ["gniew bastionu", "bastion wrath"],
            "natural_tags": ["gniew", "mlot", "hammer", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 0,
            "desc": "Potężny atak Strażnika.",
            "scale": "strength", "mult": 2.45,
        },
        {
            "id": "guardian_final_hammer",
            "name": "Młot Końca",
            "aliases": ["mlot konca", "młot końca", "final hammer"],
            "natural_tags": ["mlot", "hammer", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 0,
            "desc": "Ostateczne uderzenie Strażnika.",
            "scale": "strength", "mult": 2.60, "execute_mult": 1.85,
        },
    ],
    "Mag": [
        {
            "id": "mage_arcane_lance",
            "name": "Lanca Arkanów",
            "aliases": ["lanca arkanow", "lanca arkanów", "arcane lance"],
            "natural_tags": ["pocisk", "bolt", "lanca", "arkany"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 18,
            "desc": "Skoncentrowany czar ofensywny skalowany Inteligencją.",
            "scale": "intelligence", "mult": 2.20,
        },
        {
            "id": "mage_arcane_aegis",
            "name": "Aegis Arkanów",
            "aliases": ["aegis arkanow", "aegis arkanów", "arcane aegis"],
            "natural_tags": ["tarcza", "oslona", "guard", "arkany"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 16,
            "desc": "Silna magiczna osłona.",
            "guard": 62,
        },
        {
            "id": "mage_mana_tempest",
            "name": "Burza Many",
            "aliases": ["burza many", "mana tempest"],
            "natural_tags": ["burza", "storm", "mana", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 26,
            "desc": "Potężny wybuch Many skalowany Inteligencją.",
            "scale": "intelligence", "mult": 2.75,
        },
        {
            "id": "mage_arcane_cataclysm",
            "name": "Kataklizm Arkanów",
            "aliases": ["kataklizm arkanow", "kataklizm arkanów", "arcane cataclysm"],
            "natural_tags": ["kataklizm", "arkany", "czar", "atak"],
            "unlock": 200, "kind": "damage", "cooldown": 16, "mana": 35,
            "desc": "Najsilniejszy czar Maga.",
            "scale": "intelligence", "mult": 3.25,
        },
    ],
    "Nekromanta": [
        {
            "id": "necromancer_bone_curse",
            "name": "Klątwa Kości",
            "aliases": ["klatwa kosci", "klątwa kości", "bone curse"],
            "natural_tags": ["klatwa", "kosci", "czar", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 17,
            "desc": "Nekromantyczna klątwa skalowana Inteligencją.",
            "scale": "intelligence", "mult": 2.15,
        },
        {
            "id": "necromancer_greater_drain",
            "name": "Wielkie Wysysanie",
            "aliases": ["wielkie wysysanie", "greater drain"],
            "natural_tags": ["drain", "wysysanie", "leech"],
            "unlock": 140, "kind": "drain", "cooldown": 10, "mana": 20,
            "desc": "Silny drenaż życia.",
            "scale": "intelligence", "mult": 2.25, "drain_pct": 0.50,
        },
        {
            "id": "necromancer_dead_reaping",
            "name": "Żniwo Umarłych",
            "aliases": ["zniwo umarlych", "żniwo umarłych", "reaping of the dead"],
            "natural_tags": ["zniwo", "drain", "wysysanie"],
            "unlock": 180, "kind": "drain", "cooldown": 12, "mana": 28,
            "desc": "Potężne żniwo dusz przywracające część HP.",
            "scale": "intelligence", "mult": 2.70, "drain_pct": 0.55,
        },
        {
            "id": "necromancer_death_sentence",
            "name": "Wyrok Śmierci",
            "aliases": ["wyrok smierci", "wyrok śmierci", "death sentence"],
            "natural_tags": ["smierc", "wyrok", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 34,
            "desc": "Ostateczny nekromantyczny wyrok na osłabionym celu.",
            "scale": "intelligence", "mult": 2.80, "execute_mult": 2.00,
        },
    ],
    "Kapłan": [
        {
            "id": "priest_light_beam",
            "name": "Promień Światła",
            "aliases": ["promien swiatla", "promień światła", "light beam"],
            "natural_tags": ["swiatlo", "promien", "czar", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 17,
            "desc": "Silny święty atak skalowany Inteligencją.",
            "scale": "intelligence", "mult": 2.10,
        },
        {
            "id": "priest_greater_restoration",
            "name": "Wielkie Uzdrowienie",
            "aliases": ["wielkie uzdrowienie", "greater restoration"],
            "natural_tags": ["heal", "leczenie", "uzdrowienie", "odnowa"],
            "unlock": 140, "kind": "heal", "cooldown": 10, "mana": 20,
            "desc": "Potężne leczenie Kapłana.",
            "heal_pct": 0.48,
        },
        {
            "id": "priest_aegis_of_light",
            "name": "Aegis Światła",
            "aliases": ["aegis swiatla", "aegis światła", "aegis of light"],
            "natural_tags": ["tarcza", "oslona", "guard", "swiatlo"],
            "unlock": 180, "kind": "guard", "cooldown": 13, "mana": 24,
            "desc": "Święta osłona redukująca następne trafienie.",
            "guard": 68,
        },
        {
            "id": "priest_miracle_rebirth",
            "name": "Cud Odrodzenia",
            "aliases": ["cud odrodzenia", "miracle of rebirth"],
            "natural_tags": ["heal", "leczenie", "cud", "odrodzenie"],
            "unlock": 200, "kind": "heal", "cooldown": 17, "mana": 32,
            "desc": "Najsilniejsze leczenie Kapłana.",
            "heal_pct": 0.68,
        },
    ],
    "Czarownik": [
        {
            "id": "warlock_void_fire",
            "name": "Ogień Pustki",
            "aliases": ["ogien pustki", "ogień pustki", "void fire"],
            "natural_tags": ["ogien", "plomien", "fire", "pustka"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 18,
            "desc": "Silny ognisty czar Otchłani.",
            "scale": "intelligence", "mult": 2.25,
        },
        {
            "id": "warlock_void_shield",
            "name": "Tarcza Otchłani",
            "aliases": ["tarcza otchlani", "tarcza otchłani", "void shield"],
            "natural_tags": ["tarcza", "oslona", "guard", "pustka"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 18,
            "desc": "Mroczna osłona Czarownika.",
            "guard": 58,
        },
        {
            "id": "warlock_abyss_inferno",
            "name": "Inferno Otchłani",
            "aliases": ["inferno otchlani", "inferno otchłani", "abyss inferno"],
            "natural_tags": ["ogien", "plomien", "fire", "inferno"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 29,
            "desc": "Potężne inferno skalowane Inteligencją.",
            "scale": "intelligence", "mult": 2.85,
        },
        {
            "id": "warlock_hell_judgment",
            "name": "Piekielny Wyrok",
            "aliases": ["piekielny wyrok", "hell judgment"],
            "natural_tags": ["ogien", "wyrok", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 35,
            "desc": "Ostateczny czar Czarownika, szczególnie silny na osłabionym celu.",
            "scale": "intelligence", "mult": 2.80, "execute_mult": 1.95,
        },
    ],
    "Druid": [
        {
            "id": "druid_ancient_roots",
            "name": "Pradawne Korzenie",
            "aliases": ["pradawne korzenie", "ancient roots"],
            "natural_tags": ["korzenie", "natura", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 17,
            "desc": "Pradawna magia natury skalowana Inteligencją.",
            "scale": "intelligence", "mult": 2.10,
        },
        {
            "id": "druid_grove_restoration",
            "name": "Odnowa Gaju",
            "aliases": ["odnowa gaju", "grove restoration"],
            "natural_tags": ["heal", "leczenie", "odnowa", "natura"],
            "unlock": 140, "kind": "heal", "cooldown": 11, "mana": 18,
            "desc": "Silna regeneracja Druida.",
            "heal_pct": 0.42,
        },
        {
            "id": "druid_elemental_storm",
            "name": "Burza Żywiołów",
            "aliases": ["burza zywiolow", "burza żywiołów", "elemental storm"],
            "natural_tags": ["burza", "storm", "zywioly", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 28,
            "desc": "Potężna burza żywiołów.",
            "scale": "intelligence", "mult": 2.70,
        },
        {
            "id": "druid_worldtree_wrath",
            "name": "Gniew Drzewa Świata",
            "aliases": ["gniew drzewa swiata", "gniew drzewa świata", "worldtree wrath"],
            "natural_tags": ["gniew", "drzewo", "natura", "atak"],
            "unlock": 200, "kind": "damage", "cooldown": 16, "mana": 34,
            "desc": "Najsilniejszy ofensywny czar Druida.",
            "scale": "intelligence", "mult": 3.10,
        },
    ],
    "Psionik": [
        {
            "id": "psion_mind_blade",
            "name": "Ostrze Umysłu",
            "aliases": ["ostrze umyslu", "ostrze umysłu", "mind blade"],
            "natural_tags": ["ostrze", "umysl", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 17,
            "desc": "Psioniczne ostrze skalowane Inteligencją.",
            "scale": "intelligence", "mult": 2.20,
        },
        {
            "id": "psion_mind_fortress",
            "name": "Forteca Umysłu",
            "aliases": ["forteca umyslu", "forteca umysłu", "mind fortress"],
            "natural_tags": ["tarcza", "oslona", "guard", "umysl"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 18,
            "desc": "Potężna psioniczna osłona.",
            "guard": 64,
        },
        {
            "id": "psion_psyche_rend",
            "name": "Rozdarcie Jaźni",
            "aliases": ["rozdarcie jazni", "rozdarcie jaźni", "psyche rend"],
            "natural_tags": ["rozdarcie", "umysl", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 28,
            "desc": "Potężny atak psioniczny.",
            "scale": "intelligence", "mult": 2.75,
        },
        {
            "id": "psion_end_of_thought",
            "name": "Koniec Myśli",
            "aliases": ["koniec mysli", "koniec myśli", "end of thought"],
            "natural_tags": ["mysl", "umysl", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 35,
            "desc": "Ostateczny psioniczny cios na osłabionego przeciwnika.",
            "scale": "intelligence", "mult": 2.75, "execute_mult": 1.95,
        },
    ],
}

for _class_name, _skills in ENDGAME_CLASS_SKILLS.items():
    CLASS_SKILLS.setdefault(_class_name, []).extend(_skills)


AREA_MAGIC_AND_GROUP_HEALING_SKILLS = {
    "Mag": [
        {"id":"mage_arcane_explosion","name":"Eksplozja Arkanów","aliases":["eksplozja arkanow","eksplozja arkanów","arcane explosion"],"natural_tags":["aoe","obszar","arkany"],"unlock":40,"kind":"aoe_damage","cooldown":10,"mana":18,"desc":"Obszarowy czar Maga trafiający wszystkich dostępnych przeciwników w lokacji.","scale":"intelligence","mult":1.35},
        {"id":"mage_meteor_storm","name":"Burza Meteorów","aliases":["burza meteorow","burza meteorów","meteor storm"],"natural_tags":["aoe","obszar","meteor"],"unlock":160,"kind":"aoe_damage","cooldown":18,"mana":36,"desc":"Potężny obszarowy czar Maga na wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.20},
    ],
    "Nekromanta": [
        {"id":"necro_soul_plague","name":"Plaga Dusz","aliases":["plaga dusz","soul plague"],"natural_tags":["aoe","obszar","plaga"],"unlock":40,"kind":"aoe_damage","cooldown":11,"mana":18,"desc":"Plaga nekromantyczna uderzająca wszystkich przeciwników w lokacji.","scale":"intelligence","mult":1.30},
        {"id":"necro_grave_tempest","name":"Nawałnica Grobów","aliases":["nawalnica grobow","nawałnica grobów","grave tempest"],"natural_tags":["aoe","obszar","grob"],"unlock":160,"kind":"aoe_damage","cooldown":19,"mana":35,"desc":"Potężna fala śmierci obejmująca wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.10},
    ],
    "Czarownik": [
        {"id":"warlock_void_nova","name":"Nova Otchłani","aliases":["nova otchlani","nova otchłani","void nova"],"natural_tags":["aoe","obszar","nova","pustka"],"unlock":40,"kind":"aoe_damage","cooldown":11,"mana":20,"desc":"Eksplozja Otchłani zadająca obrażenia wszystkim przeciwnikom w lokacji.","scale":"intelligence","mult":1.42},
        {"id":"warlock_void_rain","name":"Deszcz Pustki","aliases":["deszcz pustki","void rain"],"natural_tags":["aoe","obszar","pustka"],"unlock":160,"kind":"aoe_damage","cooldown":18,"mana":38,"desc":"Endgameowy czar obszarowy Czarownika na wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.30},
    ],
    "Druid": [
        {"id":"druid_hurricane","name":"Huragan","aliases":["huragan","hurricane"],"natural_tags":["aoe","obszar","burza"],"unlock":40,"kind":"aoe_damage","cooldown":11,"mana":17,"desc":"Obszarowy huragan natury uderzający wszystkich przeciwników w lokacji.","scale":"intelligence","mult":1.28},
        {"id":"druid_starfall","name":"Deszcz Gwiazd","aliases":["deszcz gwiazd","starfall"],"natural_tags":["aoe","obszar","gwiazdy"],"unlock":160,"kind":"aoe_damage","cooldown":18,"mana":34,"desc":"Silny obszarowy czar Druida trafiający wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.00},
    ],
    "Psionik": [
        {"id":"psion_mind_storm","name":"Burza Umysłów","aliases":["burza umyslow","burza umysłów","mind storm"],"natural_tags":["aoe","obszar","umysl"],"unlock":40,"kind":"aoe_damage","cooldown":10,"mana":18,"desc":"Psioniczna fala obszarowa uderzająca wszystkie dostępne cele w lokacji.","scale":"intelligence","mult":1.34},
        {"id":"psion_psychic_collapse","name":"Psychiczne Załamanie","aliases":["psychiczne zalamanie","psychiczne załamanie","psychic collapse"],"natural_tags":["aoe","obszar","psychic"],"unlock":160,"kind":"aoe_damage","cooldown":18,"mana":35,"desc":"Potężne obszarowe uderzenie psioniczne na wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.12},
    ],
    "Kapłan": [
        {"id":"priest_prayer_of_renewal","name":"Modlitwa Odnowy","aliases":["modlitwa odnowy","prayer of renewal","group heal"],"natural_tags":["heal","leczenie","grupa","druzyna"],"unlock":40,"kind":"group_heal","cooldown":13,"mana":16,"desc":"Obszarowe leczenie Kapłana dla całej drużyny w tej samej lokacji.","heal_pct":0.24},
        {"id":"priest_mass_restoration","name":"Masowe Uzdrowienie","aliases":["masowe uzdrowienie","mass restoration","mass heal"],"natural_tags":["heal","leczenie","grupa","druzyna"],"unlock":160,"kind":"group_heal","cooldown":20,"mana":34,"desc":"Potężne obszarowe leczenie całej drużyny Kapłana w tej samej lokacji.","heal_pct":0.46},
    ],
}
for _class_name, _skills in AREA_MAGIC_AND_GROUP_HEALING_SKILLS.items():
    CLASS_SKILLS.setdefault(_class_name, []).extend(_skills)


# v0.8.25 utworzyło pełną siatkę skilli w dawnych progach Soul 1-200.
# v0.8.41 przeniosło odblokowanie na Biegłość klasy.
# v0.8.42 rozszerza Biegłość każdej klasy do 200 i zachowuje progi 1-200
# bez dzielenia ich przez dwa. Postać nadal NIE ma levelu postaci.
SOUL_SKILL_UNLOCK_LEVELS = tuple([1] + list(range(10, SOUL_MAX_LEVEL + 1, 10)))

_SOUL_GRID_CLASS_PROFILES = {
    "Wojownik":   {"prefix":"warrior_grid",   "scale":"strength",     "magic":False},
    "Berserker":  {"prefix":"berserker_grid", "scale":"strength",     "magic":False},
    "Łotrzyk":    {"prefix":"rogue_grid",     "scale":"dexterity",    "magic":False},
    "Łowca":      {"prefix":"hunter_grid",    "scale":"dexterity",    "magic":False},
    "Mnich":      {"prefix":"monk_grid",      "scale":"dexterity",    "magic":False},
    "Strażnik":   {"prefix":"guardian_grid",  "scale":"strength",     "magic":False},
    "Mag":        {"prefix":"mage_grid",      "scale":"intelligence", "magic":True},
    "Nekromanta": {"prefix":"necro_grid",     "scale":"intelligence", "magic":True},
    "Kapłan":     {"prefix":"priest_grid",    "scale":"intelligence", "magic":True},
    "Czarownik":  {"prefix":"warlock_grid",   "scale":"intelligence", "magic":True},
    "Druid":      {"prefix":"druid_grid",     "scale":"intelligence", "magic":True},
    "Psionik":    {"prefix":"psion_grid",     "scale":"intelligence", "magic":True},
}

# Tylko brakujące progi. Istniejące umiejętności z wcześniejszych wersji
# zostają zachowane i dalej mają te same ID, Skill Level oraz Skill XP.
SOUL_LEVEL_SKILL_EXPANSION = {
    "Wojownik": [
        (10,"Cięcie Straży","damage"),(30,"Żelazny Impet","boost"),
        (40,"Wir Ostrza","damage"),(50,"Przełamanie Gardy","damage"),
        (70,"Marsz Wojenny","guard"),(80,"Cięcie Weterana","damage"),
        (90,"Szturm Duszy","execute"),(110,"Ostrze Bohatera","damage"),
        (120,"Stalowa Postawa","guard"),(130,"Rozszczepienie Pancerza","damage"),
        (150,"Gniew Czempiona","boost"),(160,"Wir Bohatera","damage"),
        (170,"Natarcie Legendy","damage"),(190,"Wyrok Wojownika","execute"),
    ],
    "Berserker": [
        (10,"Krwawy Cios","damage"),(30,"Wściekły Ryk","boost"),
        (40,"Rzeźniczy Wir","damage"),(50,"Rozłupanie","damage"),
        (70,"Skóra Furii","guard"),(80,"Łamacz Kości","damage"),
        (90,"Krwawa Egzekucja","execute"),(110,"Szał Rzezi","damage"),
        (120,"Niepowstrzymany","boost"),(130,"Rozdarcie Ciała","damage"),
        (150,"Furia Przodków","boost"),(160,"Wir Rzezi","damage"),
        (170,"Gniew Kolosa","drain"),(190,"Ostatnia Rzeź","execute"),
    ],
    "Łotrzyk": [
        (10,"Szybkie Ostrze","damage"),(30,"Cienisty Impet","boost"),
        (40,"Wir Sztyletów","damage"),(50,"Pchnięcie w Lukę","damage"),
        (70,"Unik Widma","evade"),(80,"Potrójne Cięcie","damage"),
        (90,"Cichy Wyrok","execute"),(110,"Ostrze Nocy","damage"),
        (120,"Zasłona Cienia","evade"),(130,"Rozprucie","damage"),
        (150,"Zabójczy Rytm","boost"),(160,"Taniec Sztyletów","damage"),
        (170,"Skok Zabójcy","damage"),(190,"Ostatni Cień","execute"),
    ],
    "Łowca": [
        (10,"Szybki Strzał","damage"),(30,"Sokoli Wzrok","boost"),
        (40,"Deszcz Strzał","damage"),(50,"Strzał Przebijający","damage"),
        (70,"Unik Tropiciela","evade"),(80,"Potrójna Salwa","damage"),
        (90,"Strzał Łowcy","execute"),(110,"Strzała Widma","damage"),
        (120,"Zasadzka","evade"),(130,"Strzał w Słaby Punkt","damage"),
        (150,"Sokole Skupienie Mistrza","boost"),(160,"Nawałnica Strzał","damage"),
        (170,"Polowanie Legendy","damage"),(190,"Ostatnia Strzała","execute"),
    ],
    "Mnich": [
        (10,"Szybka Pięść","damage"),(30,"Oddech Wojownika","heal"),
        (40,"Wirujący Kop","damage"),(50,"Uderzenie Meridianu","damage"),
        (70,"Krok Wiatru","evade"),(80,"Seria Tygrysa","damage"),
        (90,"Cios Smoka","execute"),(110,"Pięść Harmonii","damage"),
        (120,"Wewnętrzny Spokój","heal"),(130,"Fala Ki","damage"),
        (150,"Skupienie Mistrza Ki","boost"),(160,"Taniec Smoka","damage"),
        (170,"Pięść Legendy","damage"),(190,"Wyrok Oświeconego","execute"),
    ],
    "Strażnik": [
        (10,"Uderzenie Tarczy","damage"),(30,"Postawa Bastionu","guard"),
        (40,"Krąg Młota","damage"),(50,"Przełamanie","damage"),
        (70,"Kamienna Skóra","guard"),(80,"Cios Strażnika","damage"),
        (90,"Wyrok Twierdzy","execute"),(110,"Młot Duszy","damage"),
        (120,"Mur Fortecy","guard"),(130,"Roztrzaskanie","damage"),
        (150,"Przysięga Obrońcy","boost"),(160,"Burza Młota","damage"),
        (170,"Natarcie Bastionu","damage"),(190,"Ostatnia Obrona","guard"),
    ],
    "Mag": [
        (10,"Iskra Arkanów","damage"),(30,"Skupienie Many","boost"),
        (50,"Lanca Many","damage"),(70,"Odbicie Arkanów","guard"),
        (80,"Kula Mocy","damage"),(90,"Rozdarcie Eteru","execute"),
        (110,"Pocisk Astralny","damage"),(120,"Bariera Mistrza","guard"),
        (130,"Fala Arkanów","damage"),(150,"Przeciążenie Many","boost"),
        (170,"Promień Próżni","damage"),(190,"Wyrok Arkanów","execute"),
    ],
    "Nekromanta": [
        (10,"Kolec Kości","damage"),(30,"Mroczny Szept","boost"),
        (50,"Widmowy Pocisk","damage"),(70,"Zasłona Grobu","guard"),
        (80,"Uścisk Kości","damage"),(90,"Kradzież Życia","drain"),
        (110,"Włócznia Śmierci","damage"),(120,"Pancerz Kości","guard"),
        (130,"Mroczne Żniwo","damage"),(150,"Przymierze Grobu","boost"),
        (170,"Rozdarcie Duszy Grobu","damage"),(190,"Ostatni Oddech","execute"),
    ],
    "Kapłan": [
        (10,"Błysk Światła","damage"),(30,"Modlitwa Skupienia","boost"),
        (50,"Uzdrowienie Wiary","heal"),(70,"Tarcza Wiary","guard"),
        (80,"Promień Łaski","damage"),(90,"Wielka Modlitwa","heal"),
        (110,"Ostrze Światła","damage"),(120,"Sanktuarium","guard"),
        (130,"Łaska Arcykapłana","heal"),(150,"Hymn Mocy","boost"),
        (170,"Sąd Światła","damage"),(190,"Ostateczne Błogosławieństwo","heal"),
    ],
    "Czarownik": [
        (10,"Iskra Pustki","damage"),(30,"Szept Otchłani","boost"),
        (50,"Cierń Pustki","damage"),(70,"Zasłona Otchłani","guard"),
        (80,"Krwawy Płomień","damage"),(90,"Wysysanie Pustki","drain"),
        (110,"Lanca Otchłani","damage"),(120,"Pakt Cienia","boost"),
        (130,"Rozdarcie Pustki","damage"),(150,"Mroczne Przeładowanie","boost"),
        (170,"Gniew Piekieł","damage"),(190,"Ostateczny Pakt","execute"),
    ],
    "Druid": [
        (10,"Pnącze Cierni","damage"),(30,"Pieśń Gaju","heal"),
        (50,"Pazur Natury","damage"),(70,"Kora Życia","guard"),
        (80,"Piorun Natury","damage"),(90,"Oddech Lasu","heal"),
        (110,"Korzeń Duszy","damage"),(120,"Ochrona Pradawnych","guard"),
        (130,"Gniew Dziczy","damage"),(150,"Pieśń Burzy","boost"),
        (170,"Wściekłość Natury","damage"),(190,"Wyrok Pradawnego Dębu","execute"),
    ],
    "Psionik": [
        (10,"Kolec Umysłu","damage"),(30,"Skupienie Psioniczne","boost"),
        (50,"Wstrząs Jaźni","damage"),(70,"Tarcza Myśli","guard"),
        (80,"Impuls Dominacji","damage"),(90,"Wysysanie Woli","drain"),
        (110,"Ostrze Jaźni","damage"),(120,"Forteca Jaźni","guard"),
        (130,"Kruszenie Umysłu","damage"),(150,"Trans Psioniczny","boost"),
        (170,"Burza Jaźni","damage"),(190,"Zerwanie Świadomości","execute"),
    ],
}


def _make_soul_grid_skill(class_name, soul_level, name, kind):
    profile = _SOUL_GRID_CLASS_PROFILES[class_name]
    magic = bool(profile["magic"])
    skill = {
        "id": f"{profile['prefix']}_{int(soul_level)}",
        "name": name,
        "aliases": [name.lower()],
        "natural_tags": [word.lower() for word in name.split()],
        "unlock": int(soul_level),
        "kind": kind,
        "cooldown": 4,
        "mana": 0,
        "desc": (
            f"Umiejętność klasy {class_name} odblokowywana przez "
            f"Soul Level {int(soul_level)} Broni Duszy."
        ),
    }

    # Mana rośnie wraz z siłą czaru, ale fizyczne klasy pozostają bez many.
    if magic:
        skill["mana"] = max(4, 5 + int(soul_level) // 7)

    if kind == "damage":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.18 + int(soul_level) * 0.0082, 2)
        skill["cooldown"] = min(12, 4 + int(soul_level) // 35)
    elif kind == "execute":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.22 + int(soul_level) * 0.0078, 2)
        skill["execute_mult"] = round(min(2.0, 1.45 + int(soul_level) / 400.0), 2)
        skill["cooldown"] = min(17, 9 + int(soul_level) // 30)
    elif kind == "drain":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.16 + int(soul_level) * 0.0074, 2)
        skill["drain_pct"] = round(min(0.48, 0.24 + int(soul_level) / 800.0), 2)
        skill["cooldown"] = min(15, 8 + int(soul_level) // 35)
    elif kind == "boost":
        skill["boost"] = round(min(1.70, 1.20 + int(soul_level) / 400.0), 2)
        skill["cooldown"] = min(16, 10 + int(soul_level) // 45)
        skill["duration"] = skill["cooldown"]
        skill["desc"] = (
            f"Czasowo wzmacnia wszystkie skille i spelle. Wymaga Biegłości klasy {int(soul_level)}."
        )
    elif kind == "guard":
        skill["guard"] = 10 + int(soul_level) // 3
        skill["cooldown"] = min(18, 10 + int(soul_level) // 35)
    elif kind == "evade":
        skill["cooldown"] = min(16, 9 + int(soul_level) // 40)
    elif kind == "heal":
        skill["heal_pct"] = round(min(0.52, 0.14 + int(soul_level) / 520.0), 3)
        skill["cooldown"] = min(18, 9 + int(soul_level) // 35)
    else:
        raise ValueError(f"Nieobsługiwany typ skilla progresji Soul: {kind}")

    return skill


for _class_name, _specs in SOUL_LEVEL_SKILL_EXPANSION.items():
    _existing_levels = {
        int(skill.get("unlock", 1))
        for skill in CLASS_SKILLS.get(_class_name, [])
    }
    for _soul_level, _name, _kind in _specs:
        if int(_soul_level) in _existing_levels:
            continue
        CLASS_SKILLS.setdefault(_class_name, []).append(
            _make_soul_grid_skill(_class_name, _soul_level, _name, _kind)
        )
        _existing_levels.add(int(_soul_level))


# v0.9.12: nowe umiejętności Biegłości 220-400. Stare progi 1-200
# pozostają bez zmian; nowe skille mają malejący przyrost mocy.
_POST200_SKILL_STAGES = (
    (220, "Przebudzenie"), (240, "Transcendencja"), (260, "Horyzont"),
    (280, "Otchłań"), (300, "Gwiezdny Rdzeń"), (320, "Pierwotność"),
    (340, "Nieskończoność"), (360, "Korona Świata"),
    (380, "Ponadczasowość"), (400, "Absolut"),
)
_POST200_CLASS_NOUN = {
    "Wojownik":"Wojownika", "Berserker":"Berserkera", "Łotrzyk":"Łotrzyka",
    "Łowca":"Łowcy", "Mnich":"Mnicha", "Strażnik":"Strażnika",
    "Mag":"Maga", "Nekromanta":"Nekromanty", "Kapłan":"Kapłana",
    "Czarownik":"Czarownika", "Druid":"Druida", "Psionik":"Psionika",
}
_POST200_ROLE_KINDS = {
    "Wojownik":("damage","guard","damage","boost","execute"),
    "Berserker":("damage","boost","drain","damage","execute"),
    "Łotrzyk":("damage","evade","damage","boost","execute"),
    "Łowca":("damage","evade","damage","boost","execute"),
    "Mnich":("damage","heal","damage","boost","execute"),
    "Strażnik":("damage","guard","guard","boost","damage"),
    "Mag":("damage","guard","damage","boost","execute"),
    "Nekromanta":("damage","guard","drain","boost","execute"),
    "Kapłan":("damage","heal","guard","boost","heal"),
    "Czarownik":("damage","guard","drain","boost","execute"),
    "Druid":("damage","heal","guard","boost","execute"),
    "Psionik":("damage","guard","drain","boost","execute"),
}

def _make_post200_mastery_skill(class_name, level, stage, kind):
    profile = _SOUL_GRID_CLASS_PROFILES[class_name]
    magic = bool(profile["magic"])
    noun = _POST200_CLASS_NOUN[class_name]
    name = f"{stage} {noun}"
    skill = {
        "id": f"{profile['prefix']}_mastery_{level}", "name": name,
        "aliases": [name.lower()], "natural_tags": [stage.lower(), "biegłość"],
        "unlock": level, "kind": kind, "cooldown": 10,
        "mana": (18 + level // 18) if magic else 0,
        "desc": f"Umiejętność Biegłości {level} klasy {class_name}.",
    }
    progress = (level - 200) / 200.0
    if kind in ("damage", "execute", "drain"):
        skill["scale"] = profile["scale"]
        skill["mult"] = round(2.65 + progress * 0.55, 2)
        skill["cooldown"] = 10 if kind == "damage" else 15
    if kind == "execute":
        skill["execute_mult"] = round(1.75 + progress * 0.15, 2)
    elif kind == "drain":
        skill["drain_pct"] = round(0.28 + progress * 0.08, 2)
    elif kind == "guard":
        skill["guard"] = 70 + (level - 200) // 8
        skill["cooldown"] = 15
    elif kind == "evade":
        skill["cooldown"] = 13
    elif kind == "boost":
        skill["boost"] = round(1.50 + progress * 0.15, 2)
        skill["duration"] = 14
        skill["cooldown"] = 16
    elif kind == "heal":
        skill["heal_pct"] = round(min(0.60, 0.42 + progress * 0.12), 3)
        skill["cooldown"] = 15
    return skill

for _class_name in _SOUL_GRID_CLASS_PROFILES:
    _existing = {int(x.get("unlock", 1)) for x in CLASS_SKILLS.get(_class_name, [])}
    _pattern = _POST200_ROLE_KINDS[_class_name]
    for _index, (_level, _stage) in enumerate(_POST200_SKILL_STAGES):
        if _level in _existing:
            continue
        _kind = _pattern[_index % len(_pattern)]
        CLASS_SKILLS.setdefault(_class_name, []).append(
            _make_post200_mastery_skill(_class_name, _level, _stage, _kind)
        )

# v0.9.22: każdy próg Biegłości ma kilka realnych umiejętności do nauki.
# Docelowo dokładnie 3 skille/spelle na próg 1, 10, 20...200 oraz 220...400.
# Dodatkowe umiejętności są alternatywami tego samego progu i korzystają ze
# wspólnego cooldownu mastery_choice_group, żeby zwiększyć wybór bez potrajania DPS.
_V0922_MASTERY_LEVELS = tuple(sorted(set(SOUL_SKILL_UNLOCK_LEVELS) | {
    level for level, _stage in _POST200_SKILL_STAGES
}))
_V0922_CLASS_ALT_PROFILES = {
    "Wojownik":   (("Kontratak Wojownika", "damage"), ("Mur Wojownika", "guard"), ("Rozkaz Wojownika", "boost")),
    "Berserker":  (("Rozdarcie Berserkera", "drain"), ("Furia Berserkera", "damage"), ("Ryk Berserkera", "boost")),
    "Łotrzyk":    (("Riposta Łotrzyka", "damage"), ("Krok Łotrzyka", "evade"), ("Impuls Cienia", "boost")),
    "Łowca":      (("Strzał Tropiciela", "damage"), ("Odskok Łowcy", "evade"), ("Skupienie Tropiciela", "boost")),
    "Mnich":      (("Fala Ki", "damage"), ("Oddech Harmonii", "heal"), ("Krok Harmonii", "evade")),
    "Strażnik":   (("Cios Bastionu", "damage"), ("Tarcza Strażnika", "guard"), ("Przysięga Bastionu", "boost")),
    "Mag":        (("Lanca Arkanów", "damage"), ("Krąg Arkanów", "aoe_damage"), ("Bariera Eteru", "guard")),
    "Nekromanta": (("Żniwo Nekromanty", "drain"), ("Fala Grobów", "aoe_damage"), ("Pancerz Grobu", "guard")),
    "Kapłan":     (("Promień Kapłana", "damage"), ("Łaska Kapłana", "heal"), ("Modlitwa Drużyny", "group_heal")),
    "Czarownik":  (("Pocisk Otchłani", "damage"), ("Krąg Pustki", "aoe_damage"), ("Pakt Otchłani", "drain")),
    "Druid":      (("Cierń Druida", "damage"), ("Odnowa Natury", "heal"), ("Krąg Dziczy", "aoe_damage")),
    "Psionik":    (("Impuls Psionika", "damage"), ("Fala Umysłu", "aoe_damage"), ("Forteca Myśli", "guard")),
}

# v0.24.4: stary generator tworzył dziesiątki nazw typu
# "Kontratak Wojownika 10", "Kontratak Wojownika 20" itd. ID i mechanika
# pozostają bez zmian, ale nazwy alternatywnych skilli Wojownika są teraz
# faktycznie różne i czytelne dla NVDA.
_V0244_WARRIOR_LEVEL_TITLES = {
    level: title for level, title in zip(
        _V0922_MASTERY_LEVELS,
        (
            "Pierwszej Warty", "Żelaznego Świtu", "Stalowej Straży",
            "Miecza Północy", "Tarczy Miasta", "Krwawego Frontu",
            "Srebrnej Gwardii", "Nieugiętej Linii", "Płonącego Bastionu",
            "Weterana", "Kamiennej Bramy", "Wojennego Sztandaru",
            "Hartowanego Ostrza", "Czerwonej Warty", "Złamanego Muru",
            "Niezłomnego Legionu", "Ostatniej Straży", "Ducha Bohatera",
            "Korony Wojny", "Mistrza Oręża", "Legendy Pola Bitwy",
            "Przekroczonej Granicy", "Przebudzonej Stali", "Wyższej Warty",
            "Transcendentnej Gwardii", "Dalekiego Horyzontu",
            "Horyzontu Bitew", "Głębokiej Otchłani", "Otchłannego Ostrza",
            "Gwiezdnej Kuźni", "Gwiezdnego Bastionu", "Pierwotnego Szańca",
            "Pierwotnego Legionu", "Wiecznej Warty", "Nieskończonej Straży",
            "Korony Zwycięstwa", "Korony Świata", "Czasu Bohaterów",
            "Ponadczasowej Wojny", "Ostatniej Granicy", "Absolutnej Stali",
        ),
    )
}
_V0244_WARRIOR_ACTION_PREFIXES = {
    "damage": (
        "Riposta", "Odwet", "Przechwyt", "Cięcie Odpowiedzi",
        "Pchnięcie Zwrotne", "Uderzenie po Bloku", "Natarcie Zwrotne",
        "Zamach Odpowiedzi", "Przecięcie Gardy",
    ),
    "guard": (
        "Żelazna Zasłona", "Bastion", "Tarcza", "Garda",
        "Forteca", "Warta", "Szańcowanie", "Mur",
    ),
    "boost": (
        "Rozkaz", "Zew", "Komenda", "Sygnał Natarcia",
        "Marsz", "Przysięga", "Mobilizacja", "Sztandar",
    ),
}

def _v0244_warrior_alt_name(level, kind):
    title = _V0244_WARRIOR_LEVEL_TITLES.get(int(level), f"Biegłości {int(level)}")
    prefixes = _V0244_WARRIOR_ACTION_PREFIXES.get(kind)
    if not prefixes:
        return None
    idx = _V0922_MASTERY_LEVELS.index(int(level))
    return f"{prefixes[idx % len(prefixes)]} {title}"


def _v0922_alt_skill(class_name, level, variant_index, base_name, kind):
    profile = _SOUL_GRID_CLASS_PROFILES[class_name]
    magic = bool(profile["magic"])
    level = int(level)
    # Nazwa ma być jednoznaczna dla NVDA i komendy learn, ale nie może
    # udawać nowego skilla przez samo dopisanie numeru poziomu.
    name = None
    if class_name == "Wojownik":
        name = _v0244_warrior_alt_name(level, kind)
    if not name:
        name = f"{base_name} {level}"
    skill = {
        "id": f"v0922_{profile['prefix']}_{level}_{variant_index}",
        "name": name,
        "aliases": [name.lower()],
        "natural_tags": [w.lower() for w in base_name.split()],
        "unlock": level,
        "kind": kind,
        "cooldown": 10,
        "mana": (max(4, 5 + level // 12) if magic else 0),
        "desc": (
            f"Alternatywna umiejętność progu Biegłości {level} klasy {class_name}. "
            "Umiejętności z tego samego progu współdzielą cooldown wyboru."
        ),
        "mastery_choice_group": f"{class_name}:{level}",
    }
    progress = min(1.0, max(0.0, (level - 1) / 399.0))
    if kind in ("damage", "aoe_damage", "execute", "drain"):
        skill["scale"] = profile["scale"]
        # Alternatywy są trochę słabsze od najmocniejszego głównego skilla progu;
        # ich wartością jest inny typ działania, nie power creep.
        skill["mult"] = round(1.16 + progress * 1.75, 2)
        skill["cooldown"] = 8 if kind == "damage" else 12
    if kind == "aoe_damage":
        skill["mult"] = round(1.02 + progress * 1.40, 2)
        skill["cooldown"] = 14
    elif kind == "execute":
        skill["execute_mult"] = round(1.45 + progress * 0.35, 2)
        skill["cooldown"] = 15
    elif kind == "drain":
        skill["drain_pct"] = round(0.24 + progress * 0.14, 2)
        skill["cooldown"] = 13
    elif kind == "guard":
        skill["guard"] = 10 + int(round(progress * 110))
        skill["cooldown"] = 13
    elif kind == "evade":
        skill["cooldown"] = 13
    elif kind == "boost":
        skill["boost"] = round(1.18 + progress * 0.42, 2)
        skill["duration"] = 12
        skill["cooldown"] = 15
    elif kind == "heal":
        skill["heal_pct"] = round(0.14 + progress * 0.36, 3)
        skill["cooldown"] = 13
    elif kind == "group_heal":
        skill["heal_pct"] = round(0.10 + progress * 0.28, 3)
        skill["cooldown"] = 16
    return skill


for _class_name in _SOUL_GRID_CLASS_PROFILES:
    _skills = CLASS_SKILLS.setdefault(_class_name, [])
    for _level in _V0922_MASTERY_LEVELS:
        _at_level = [s for s in _skills if int(s.get("unlock", 1)) == int(_level)]
        # Każdy już istniejący skill także należy do wspólnej grupy tego progu.
        for _skill in _at_level:
            _skill["mastery_choice_group"] = f"{_class_name}:{int(_level)}"
        _profile_alts = _V0922_CLASS_ALT_PROFILES[_class_name]
        _alt_index = 0
        while len(_at_level) < 3:
            _base_name, _kind = _profile_alts[_alt_index % len(_profile_alts)]
            _candidate = _v0922_alt_skill(
                _class_name, int(_level), len(_at_level) + 1, _base_name, _kind
            )
            if all(s.get("id") != _candidate["id"] for s in _skills):
                _skills.append(_candidate)
                _at_level.append(_candidate)
            _alt_index += 1
        for _skill in _at_level:
            _skill["mastery_choice_group"] = f"{_class_name}:{int(_level)}"

# ============================================================
# v0.30.14 - FULL CLASS SKILL/SPELL NAME AUDIT
# ============================================================
# v0.9.22 intentionally created three real choices per mastery threshold, but
# eleven classes still displayed large numbered families such as
# "Furia Berserkera 10" or "Fala Umysłu 80".  IDs/mechanics stay untouched;
# only the user-facing names are replaced.  Old names remain aliases so saved
# macros and learned-skill workflows keep working.
_V03014_SKILL_TITLES = (
    "Pierwszy Świt", "Żelazny Próg", "Stalowy Szlak", "Północny Zew",
    "Kamienna Brama", "Srebrny Front", "Czerwony Horyzont", "Nieugięta Linia",
    "Płonący Bastion", "Szlak Weterana", "Brama Duszy", "Wojenny Sztandar",
    "Hartowany Rdzeń", "Krwawy Księżyc", "Złamany Mur", "Niezłomny Legion",
    "Ostatnia Warta", "Duch Bohatera", "Korona Burzy", "Mistrzowski Krąg",
    "Legenda Pola", "Przekroczona Granica", "Przebudzony Rdzeń", "Wyższa Warta",
    "Transcendentny Krąg", "Daleki Horyzont", "Horyzont Mocy", "Głęboka Otchłań",
    "Otchłanny Znak", "Gwiezdna Kuźnia", "Gwiezdny Bastion", "Pierwotne Serce",
    "Pierwotny Tron", "Wieczny Zew", "Nieskończona Droga", "Korona Zwycięstwa",
    "Korona Świata", "Czas Bohaterów", "Ponadczasowy Znak", "Ostatnia Granica",
    "Absolutny Szczyt",
)

_V03014_SKILL_FAMILIES = {
    "Berserker": {
        "damage": ("Szkarłatna Furia", "Rzeźniczy Zamach", "Gniew Rozłamu"),
        "drain": ("Krwiożercze Rozdarcie", "Żniwo Krwi", "Rozdarcie Żył"),
        "boost": ("Ryk Rzezi", "Zew Furii", "Szał Bez Kajdan"),
        "execute": ("Wyrok Topora", "Ostatnie Rozdarcie", "Kres Krwi"),
    },
    "Łotrzyk": {
        "damage": ("Riposta Czarnego Ostrza", "Cięcie Nocnego Widma", "Sztych Bez Śladu"),
        "evade": ("Krok Widma", "Unik Cichego Cienia", "Przejście Bez Śladu"),
        "boost": ("Impuls Nocnego Cienia", "Skupienie Zabójcy", "Zew Czarnej Maski"),
        "execute": ("Cichy Wyrok", "Ostatni Sztych", "Wyrok Bez Świadków"),
    },
    "Łowca": {
        "damage": ("Strzał Sokolego Tropu", "Strzała Dalekiego Łuku", "Pocisk Leśnego Widma"),
        "evade": ("Odskok Tropiciela", "Krok Leśnego Cienia", "Unik Sokoła"),
        "boost": ("Skupienie Szarego Tropiciela", "Sokoli Zew", "Instynkt Dalekiego Łuku"),
        "execute": ("Strzał Ostatniego Tropu", "Wyrok Sokoła", "Ostatnia Strzała"),
    },
    "Mnich": {
        "damage": ("Fala Smoczego Ki", "Pięść Cichego Ducha", "Uderzenie Lotosu"),
        "heal": ("Oddech Białego Lotosu", "Harmonia Życia", "Medytacja Odnowy"),
        "evade": ("Krok Cichej Harmonii", "Taniec Wiatru", "Przejście Lotosu"),
        "boost": ("Skupienie Ki", "Pieśń Harmonii", "Przebudzenie Ducha"),
        "execute": ("Dotyk Końca", "Pięść Ostatniego Oddechu", "Wyrok Meridianu"),
    },
    "Strażnik": {
        "damage": ("Cios Kamiennego Bastionu", "Uderzenie Żelaznej Warty", "Taranująca Tarcza"),
        "guard": ("Tarcza Żelaznej Przysięgi", "Mur Niezłomnej Straży", "Bastion Kamiennego Serca"),
        "boost": ("Przysięga Niezłomnej Straży", "Rozkaz Bastionu", "Zew Ostatniej Warty"),
        "execute": ("Wyrok Bastionu", "Ostatni Cios Warty", "Kres Oblężenia"),
    },
    "Mag": {
        "damage": ("Lanca Gwiezdnych Arkanów", "Pocisk Kryształowego Eteru", "Ostrze Runicznego Ognia"),
        "aoe_damage": ("Krąg Eterycznej Burzy", "Nova Gwiezdnych Run", "Wir Arkanicznego Nieba"),
        "guard": ("Bariera Kryształowego Eteru", "Pieczęć Astralnej Tarczy", "Mur Runicznego Światła"),
        "boost": ("Skupienie Arkanów", "Przebudzenie Eteru", "Zew Gwiezdnej Many"),
        "execute": ("Wyrok Arkanów", "Ostatnia Lanca", "Kres Gwiezdnej Iskry"),
    },
    "Nekromanta": {
        "damage": ("Kościany Pocisk", "Włócznia Czarnego Grobu", "Cios Umarłego Tronu"),
        "aoe_damage": ("Fala Umarłych", "Krąg Cmentarnej Burzy", "Marsz Kościanego Legionu"),
        "drain": ("Żniwo Czarnego Grobu", "Wysysanie Zgasłej Duszy", "Pocałunek Kostuchy"),
        "guard": ("Pancerz Kościanego Tronu", "Zasłona Czarnego Grobu", "Mur Umarłych"),
        "boost": ("Szept Nekropolii", "Przysięga Kostuchy", "Zew Umarłego Legionu"),
        "execute": ("Wyrok Kostuchy", "Ostatnie Żniwo", "Kres Duszy"),
    },
    "Kapłan": {
        "damage": ("Promień Świętego Sądu", "Młot Złotego Światła", "Iskra Boskiej Pieczęci"),
        "heal": ("Łaska Złotego Światła", "Dotyk Miłosierdzia", "Uzdrowienie Świętej Pieczęci"),
        "group_heal": ("Modlitwa Wspólnoty", "Pieśń Zbiorowej Łaski", "Krąg Wspólnego Światła"),
        "guard": ("Tarcza Wiary", "Boska Zasłona", "Pieczęć Sanktuarium"),
        "boost": ("Modlitwa Skupienia", "Zew Świętej Łaski", "Błogosławieństwo Światła"),
        "execute": ("Wyrok Światła", "Ostatni Sąd", "Pieczęć Końca"),
    },
    "Czarownik": {
        "damage": ("Pocisk Głębokiej Otchłani", "Ostrze Bezgwiezdnej Pustki", "Płomień Czarnego Paktu"),
        "aoe_damage": ("Krąg Bezgwiezdnej Pustki", "Nova Otchłannego Mroku", "Wir Czarnego Horyzontu"),
        "drain": ("Pakt Krwawej Otchłani", "Wysysanie Pustki", "Danina Czarnego Paktu"),
        "guard": ("Zasłona Otchłani", "Bariera Pustki", "Pieczęć Czarnego Kręgu"),
        "boost": ("Szept Otchłani", "Przebudzenie Paktu", "Zew Bezgwiezdnej Pustki"),
        "execute": ("Wyrok Otchłani", "Kres Paktu", "Ostatni Pocisk Pustki"),
    },
    "Druid": {
        "damage": ("Cierń Pradawnego Gaju", "Pazur Zielonego Serca", "Korzeń Dzikiej Burzy"),
        "aoe_damage": ("Krąg Pierwotnej Dziczy", "Burza Starego Lasu", "Taniec Rozszalałych Korzeni"),
        "heal": ("Odnowa Zielonego Serca", "Szept Leczącego Gaju", "Pieśń Żywej Kory"),
        "guard": ("Kora Pradawnych", "Mur Żywego Dębu", "Osłona Zielonego Serca"),
        "boost": ("Zew Dzikiej Natury", "Przebudzenie Gaju", "Pieśń Pierwotnego Lasu"),
        "execute": ("Wyrok Pradawnego Dębu", "Ostatni Cierń", "Kres Dzikiego Korzenia"),
    },
    "Psionik": {
        "damage": ("Impuls Kryształowej Jaźni", "Kolec Astralnej Myśli", "Ostrze Cichego Umysłu"),
        "aoe_damage": ("Fala Astralnego Umysłu", "Burza Wspólnej Jaźni", "Krąg Psionicznego Echa"),
        "drain": ("Wysysanie Woli", "Pęknięcie Jaźni", "Wysysanie Astralnej Myśli"),
        "guard": ("Forteca Niezłomnej Myśli", "Bariera Kryształowej Jaźni", "Mur Psionicznej Woli"),
        "boost": ("Skupienie Psioniczne", "Przebudzenie Jaźni", "Zew Astralnej Woli"),
        "execute": ("Wyrok Umysłu", "Ostatni Impuls", "Kres Jaźni"),
    },
}


def _v03014_unique_generated_skill_names():
    renamed = 0
    old_aliases_added = 0
    level_to_title = {
        int(level): _V03014_SKILL_TITLES[idx]
        for idx, level in enumerate(_V0922_MASTERY_LEVELS)
    }
    for class_name, skills in CLASS_SKILLS.items():
        if class_name == "Wojownik":
            # v0.24.4 already gave the Warrior authored, non-numbered names.
            continue
        families = _V03014_SKILL_FAMILIES.get(class_name, {})
        for skill in skills:
            sid = str(skill.get("id", ""))
            if not sid.startswith("v0922_"):
                continue
            match = re.search(r"_(\d+)_(\d+)$", sid)
            if not match:
                continue
            original_level = int(match.group(1))
            variant_index = int(match.group(2))
            title = level_to_title.get(original_level, f"Próg {original_level}")
            kind = str(skill.get("kind", "damage"))
            family_options = families.get(kind) or families.get("damage") or (class_name,)
            family = family_options[(variant_index + original_level) % len(family_options)]
            old_name = str(skill.get("name", "")).strip()
            new_name = f"{family}: {title}"
            aliases = [str(a).strip() for a in (skill.get("aliases") or []) if str(a).strip()]
            if old_name and old_name.casefold() not in {a.casefold() for a in aliases}:
                aliases.append(old_name)
                old_aliases_added += 1
            if new_name.casefold() not in {a.casefold() for a in aliases}:
                aliases.append(new_name)
            skill["legacy_display_name_v03013"] = old_name
            skill["name"] = new_name
            skill["aliases"] = aliases
            skill["natural_tags"] = list(dict.fromkeys(
                list(skill.get("natural_tags") or []) +
                [w.lower().strip(":,—") for w in (family + " " + title).split() if w.strip(":,—")]
            ))
            renamed += 1
    return renamed, old_aliases_added


V03014_SKILLS_RENAMED, V03014_OLD_NAME_ALIASES = _v03014_unique_generated_skill_names()


def _v03014_skill_name_audit():
    errors = []
    warnings = []
    seen_names = {}
    seen_ids = {}
    valid_kinds = {
        "damage", "aoe_damage", "execute", "drain", "boost", "guard", "evade",
        "heal", "group_heal",
    }
    per_class = {}
    numeric_names = []
    for class_name, skills in CLASS_SKILLS.items():
        per_class[class_name] = len(skills)
        for skill in skills:
            sid = str(skill.get("id", "")).strip()
            name = str(skill.get("name", "")).strip()
            kind = str(skill.get("kind", "")).strip()
            if not sid or not name:
                errors.append(f"{class_name}: skill bez id/nazwy")
                continue
            id_key = sid.casefold()
            if id_key in seen_ids:
                errors.append(f"Powtórzone ID {sid}: {seen_ids[id_key]} / {class_name}")
            else:
                seen_ids[id_key] = class_name
            name_key = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").casefold()
            name_key = re.sub(r"[^a-z0-9]+", " ", name_key).strip()
            if name_key in seen_names:
                errors.append(f"Powtórzona nazwa {name}: {seen_names[name_key]} / {class_name}")
            else:
                seen_names[name_key] = class_name
            if re.search(r"\s\d+$", name):
                numeric_names.append((class_name, name))
            if kind not in valid_kinds:
                warnings.append(f"{class_name}/{name}: nieznany kind={kind}")
            unlock = int(skill.get("unlock", 1) or 1)
            if not (1 <= unlock <= CLASS_MASTERY_MAX_LEVEL):
                errors.append(f"{class_name}/{name}: unlock poza zakresem: {unlock}")
    if numeric_names:
        errors.append(f"Pozostały numerowane nazwy: {len(numeric_names)}")
    return {
        "version": "0.30.14",
        "classes": len(CLASS_SKILLS),
        "skills": sum(per_class.values()),
        "renamed": V03014_SKILLS_RENAMED,
        "legacy_aliases_added": V03014_OLD_NAME_ALIASES,
        "legacy_aliases_preserved": sum(
            1 for _skills in CLASS_SKILLS.values() for _skill in _skills
            if _skill.get("legacy_display_name_v03013") and
            str(_skill.get("legacy_display_name_v03013")).casefold() in
            {str(_a).casefold() for _a in (_skill.get("aliases") or [])}
        ),
        "per_class": per_class,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


# The generator later redistributes unlock numbers, but it does not change names.
# A second final audit is executed near the bottom of the file after Generator Core.
V03014_SKILL_NAME_AUDIT_PREGEN = _v03014_skill_name_audit()
if V03014_SKILL_NAME_AUDIT_PREGEN.get("error_count"):
    raise RuntimeError(
        "Skill/Spell Name Audit v0.30.14 failed before Generator Core: " +
        "; ".join(V03014_SKILL_NAME_AUDIT_PREGEN.get("errors", [])[:20])
    )

# v0.8.42: progi dostępu do skilli są progami Biegłości klasy 1-200.
# Zachowujemy numer dawnego progu Soul jako identyczny próg Biegłości,
# np. dawny 100 -> Biegłość 100, dawny 200 -> Biegłość 200.
def _legacy_skill_unlock_to_mastery(value):
    value = max(1, int(value or 1))
    return min(CLASS_MASTERY_MAX_LEVEL, value)


for _class_name, _skills in CLASS_SKILLS.items():
    for _skill in _skills:
        _legacy_unlock = max(1, int(_skill.get("unlock", 1)))
        _skill["legacy_soul_unlock"] = _legacy_unlock
        _skill["unlock"] = _legacy_skill_unlock_to_mastery(_legacy_unlock)
        _desc = str(_skill.get("desc", ""))
        if "Soul Level" in _desc and "Broni Duszy" in _desc:
            _skill["desc"] = (
                f"Umiejętność klasy {_class_name} odblokowywana przez "
                f"Biegłość klasy {_skill['unlock']}."
            )

# Czytelna kolejność dla skills, nauczycieli i Kodeksu Klasowego.
for _class_name in CLASS_SKILLS:
    CLASS_SKILLS[_class_name].sort(
        key=lambda skill: (int(skill.get("unlock", 1)), skill.get("name", ""))
    )


NATURAL_SKILL_INTENTS = {
    "heal": {"kinds": {"heal"}},
    "healing": {"kinds": {"heal"}},
    "lecz": {"kinds": {"heal"}},
    "leczenie": {"kinds": {"heal"}},
    "uzdrow": {"kinds": {"heal"}},
    "uzdrowienie": {"kinds": {"heal"}},
    "tarcza": {"kinds": {"guard"}},
    "oslona": {"kinds": {"guard"}},
    "guard": {"kinds": {"guard"}},
    "obrona": {"kinds": {"guard"}},
    "unik": {"kinds": {"evade"}},
    "evade": {"kinds": {"evade"}},
    "buff": {"kinds": {"boost"}},
    "boost": {"kinds": {"boost"}},
    "wzmocnij": {"kinds": {"boost"}},
    "wzmocnienie": {"kinds": {"boost"}},
    "drain": {"kinds": {"drain"}},
    "wysysanie": {"kinds": {"drain"}},
    "wysysaj": {"kinds": {"drain"}},
    "egzekucja": {"kinds": {"execute"}},
    "execute": {"kinds": {"execute"}},
    "dobij": {"kinds": {"execute"}},
    "ciecie": {"tags": {"ciecie", "slash"}},
    "slash": {"tags": {"ciecie", "slash"}},
    "pocisk": {"tags": {"pocisk", "bolt", "lanca"}},
    "bolt": {"tags": {"pocisk", "bolt", "lanca"}},
    "ogien": {"tags": {"ogien", "plomien", "fire", "inferno"}},
    "plomien": {"tags": {"ogien", "plomien", "fire", "inferno"}},
    "fire": {"tags": {"ogien", "plomien", "fire", "inferno"}},
    "burza": {"tags": {"burza", "storm"}},
    "storm": {"tags": {"burza", "storm"}},
    "mlot": {"tags": {"mlot", "hammer"}},
    "hammer": {"tags": {"mlot", "hammer"}},
    "strzal": {"tags": {"strzal", "strzala", "shot", "arrow"}},
    "strzala": {"tags": {"strzal", "strzala", "shot", "arrow"}},
    "arrow": {"tags": {"strzal", "strzala", "shot", "arrow"}},
}


# 28 trwałych lokacji. Opisy są krótkie i przyjazne czytnikom ekranu.
ROOMS = {
    "square": {
        "zone": "Miasto Dusz", "name": "Plac Dusz",
        "desc": "Centralny plac osady. Nad kamienną fontanną płonie błękitny ogień.",
        "exits": {"north": "north_street", "south": "south_street", "east": "market", "west": "temple"},
    },
    "temple": {
        "zone": "Miasto Dusz", "name": "Świątynia Odrodzenia",
        "desc": "Spokojna świątynia. Polegli bohaterowie odzyskują tutaj świadomość.",
        "exits": {"east": "square", "north": "library", "down": "temple_basement"},
    },
    "temple_basement": {
        "zone": "Podziemia", "name": "Piwnica Świątyni",
        "desc": "Wilgotna piwnica pod Świątynią Odrodzenia. Między skrzyniami słychać piski szczurów.",
        "exits": {"up": "temple"},
    },
    "library": {
        "zone": "Miasto Dusz", "name": "Biblioteka Kronik",
        "desc": "Kamienne regały przechowują kroniki o duszach, rasach i dawnych wojnach.",
        "exits": {"south": "temple", "east": "guild_hall"},
    },
    "guild_hall": {
        "zone": "Gildia Dusz", "name": "Sala Główna Gildii",
        "desc": "Centralny hol Gildii Dusz. Korytarze prowadzą do wyspecjalizowanych sal nauczycieli.",
        "exits": {
            "west": "library",
            "south": "north_street",
            "north": "guild_martial_hall",
            "east": "guild_arcane_chamber",
            "up": "guild_shadow_gallery",
            "down": "guild_sanctuary",
        },
    },
    "guild_martial_hall": {
        "zone": "Gildia Dusz", "name": "Sala Oręża Gildii",
        "desc": "Ciężkie manekiny i stojaki treningowe służą Wojownikom i Berserkerom.",
        "exits": {"south": "guild_hall", "east": "guild_body_hall"},
    },
    "guild_body_hall": {
        "zone": "Gildia Dusz", "name": "Sala Dyscypliny Gildii",
        "desc": "Spokojna sala ćwiczeń ciała i obrony przeznaczona dla Mnichów i Strażników.",
        "exits": {"west": "guild_martial_hall"},
    },
    "guild_arcane_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Arkanów Gildii",
        "desc": "Runy świecą na ścianach. Tutaj Magowie i Psionicy ćwiczą kontrolę energii.",
        "exits": {"west": "guild_hall", "east": "guild_dark_chamber"},
    },
    "guild_dark_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Mrocznych Sztuk",
        "desc": "Zabezpieczona sala do nauki Nekromantów i Czarowników.",
        "exits": {"west": "guild_arcane_chamber"},
    },
    "guild_shadow_gallery": {
        "zone": "Gildia Dusz", "name": "Galeria Cieni Gildii",
        "desc": "Wąskie przejścia i cele treningowe służą Łotrzykom i Łowcom.",
        "exits": {"down": "guild_hall"},
    },
    "guild_sanctuary": {
        "zone": "Gildia Dusz", "name": "Sanktuarium Gildii",
        "desc": "Cicha sala natury i światła, w której szkolą się Kapłani i Druidzi.",
        "exits": {"up": "guild_hall"},
    },
    "north_street": {
        "zone": "Miasto Dusz", "name": "Ulica Północna",
        "desc": "Szeroka ulica prowadząca ku dziedzińcowi i północnej bramie.",
        "exits": {"south": "square", "north": "training", "east": "guard_hall", "west": "guild_hall"},
    },
    "guard_hall": {
        "zone": "Miasto Dusz", "name": "Strażnica Główna",
        "desc": (
            "Główna sala miejskiej straży. Na ścianach wiszą mapy szlaków, "
            "tablice patroli i meldunki z obu bram. Stąd można przejść do koszar, "
            "zbrojowni, komnaty dowódcy, wieży obserwacyjnej i cel strażnicy."
        ),
        "exits": {
            "west": "north_street", "east": "guard_barracks",
            "south": "guard_armory", "north": "guard_command",
            "up": "guard_watchtower", "down": "guard_cells",
        },
    },
    "guard_barracks": {
        "zone": "Miasto Dusz", "name": "Koszary Straży",
        "desc": (
            "Rzędy prycz, stojaki na płaszcze i tablice zmian wypełniają koszary. "
            "Strażnicy odpoczywają tutaj między patrolami północnej i południowej bramy."
        ),
        "exits": {"west": "guard_hall", "east": "guard_mess"},
    },
    "guard_mess": {
        "zone": "Miasto Dusz", "name": "Jadalnia Straży",
        "desc": (
            "Długi stół, kocioł i beczki z wodą zajmują niewielką jadalnię. "
            "Na ścianie wisi plan godzinnych zmian patroli miejskich."
        ),
        "exits": {"west": "guard_barracks"},
    },
    "guard_armory": {
        "zone": "Miasto Dusz", "name": "Zbrojownia Straży",
        "desc": (
            "Zamknięte stojaki przechowują włócznie, tarcze, kusze i zapasowe pancerze. "
            "Kwatermistrz prowadzi tu ewidencję wyposażenia miejskiej straży."
        ),
        "exits": {"north": "guard_hall"},
    },
    "guard_command": {
        "zone": "Miasto Dusz", "name": "Komnata Dowódcy Straży",
        "desc": (
            "Duży stół mapowy pokazuje Miasto Dusz, Stary Trakt, Gaj Szeptów i pogranicze. "
            "Tutaj planowane są patrole i akcje przeciw goblinom oraz bandytom."
        ),
        "exits": {"south": "guard_hall", "east": "guard_archive"},
    },
    "guard_archive": {
        "zone": "Miasto Dusz", "name": "Archiwum Straży",
        "desc": (
            "Regały są pełne raportów z patroli, listów gończych i starych map. "
            "Archiwistka straży porządkuje meldunki z obu bram."
        ),
        "exits": {"west": "guard_command"},
    },
    "guard_watchtower": {
        "zone": "Miasto Dusz", "name": "Wieża Obserwacyjna Straży",
        "desc": (
            "Z kamiennej wieży widać północną bramę, Stary Trakt i dachy miasta. "
            "Wartownicy przekazują stąd sygnały do posterunków przy bramach."
        ),
        "exits": {"down": "guard_hall"},
    },
    "guard_cells": {
        "zone": "Miasto Dusz", "name": "Cele Strażnicy",
        "desc": (
            "Kilka żelaznych cel służy do przetrzymywania schwytanych bandytów i szabrowników. "
            "Korytarz prowadzi do małego pokoju przesłuchań."
        ),
        "exits": {"up": "guard_hall", "east": "guard_interrogation"},
    },
    "guard_interrogation": {
        "zone": "Miasto Dusz", "name": "Pokój Przesłuchań",
        "desc": (
            "Surowy stół, dwa krzesła i półka z raportami tworzą niewielki pokój przesłuchań. "
            "Straż zbiera tu informacje o napadach, goblinach i ruchach bandytów."
        ),
        "exits": {"west": "guard_cells"},
    },
    "training": {
        "zone": "Miasto Dusz", "name": "Plac Treningowy",
        "desc": "Plac do ćwiczeń. Drewniane manekiny stoją obok północnej bramy.",
        "exits": {"south": "north_street", "north": "north_gate"},
    },
    "north_gate": {
        "zone": "Miasto Dusz", "name": "Północna Brama",
        "desc": (
            "Ciężka brama otwiera się na Stary Trakt. Dwóch miejskich strażników "
            "pełni tu stałą wartę i kontroluje podróżnych wracających z pogranicza."
        ),
        "exits": {"south": "training", "north": "old_road"},
    },
    "market": {
        "zone": "Miasto Dusz", "name": "Rynek",
        "desc": (
            "Kupcy sprzedają prowiant i podstawowe wyposażenie. Mikstury kupisz w Aptece Pod Srebrnym Liściem. "
            "Przy kamiennym kantorze działa Bank Dusz Bankiera Aldrena. "
            "Handlarz Skupu Radan kupuje łupy, trofea i niezałożone EQ, "
            "ale nie skupuje ryb, rud, drewna, ziół ani innych materiałów rzemieślniczych."
        ),
        "exits": {"west": "square", "east": "forge", "south": "inn", "north": "fish_market"},
    },
    "fish_market": {
        "zone": "Miasto Dusz", "name": "Targ Rybny",
        "desc": "Stragany pachną świeżą rybą i mokrymi sieciami. Tutaj sprzedaje się sprzęt wędkarski.",
        "exits": {"south": "market", "east": "harbor"},
    },
    "harbor": {
        "zone": "Miasto Dusz", "name": "Port Dusz",
        "desc": "Drewniane pomosty, kutry i skrzynie rybackie wypełniają miejski port.",
        "exits": {"west": "fish_market", "east": "sea_pier"},
    },
    "sea_pier": {
        "zone": "Wybrzeże", "name": "Morskie Molo",
        "desc": "Długie molo wychodzi nad morze. To łowisko typowych ryb morskich.",
        "exits": {"west": "harbor", "east": "ocean_platform"},
    },
    "ocean_platform": {
        "zone": "Wybrzeże", "name": "Oceaniczna Platforma",
        "desc": "Daleka platforma nad otwartym oceanem. Trafiają się tu wielkie ryby oceaniczne i rekiny.",
        "exits": {"west": "sea_pier"},
    },
    "forge": {
        "zone": "Miasto Dusz", "name": "Kuźnia Dusz",
        "desc": "Młoty uderzają o metal, a Broń Duszy odpowiada cichym rezonansem.",
        "exits": {"west": "market"},
    },
    "inn": {
        "zone": "Miasto Dusz", "name": "Karczma Pod Błękitnym Płomieniem",
        "desc": "Ciepła karczma pełna rozmów podróżników.",
        "exits": {"north": "market", "west": "south_street"},
    },
    "south_street": {
        "zone": "Miasto Dusz", "name": "Ulica Południowa",
        "desc": "Cichsza część miasta prowadząca do południowej bramy.",
        "exits": {"north": "square", "east": "inn", "south": "south_gate"},
    },
    "south_gate": {
        "zone": "Miasto Dusz", "name": "Południowa Brama",
        "desc": (
            "Brama otwiera się na łąki i Gaj Szeptów. Miejska straż utrzymuje tu "
            "stały posterunek i ostrzega podróżnych o wilkach oraz zagrożeniach w dziczy."
        ),
        "exits": {"north": "south_street", "south": "meadow"},
    },
    "meadow": {
        "zone": "Łąki", "name": "Srebrna Łąka",
        "desc": (
            "Centralna część rozległych łąk. W trawie rosną Pokrzywa, "
            "Rumianek, Mięta, Krwawnik, Melisa i Lawenda. "
            "Na zachodzie leży Łąka Kwiatów, na wschodzie Łąka Mięty, "
            "a na południu Łąka Nadjeziorna."
        ),
        "exits": {
            "north": "south_gate",
            "west": "flower_meadow",
            "east": "mint_meadow",
            "south": "lakeside_meadow",
        },
    },
    "mint_meadow": {
        "zone": "Łąki", "name": "Łąka Mięty",
        "desc": (
            "Wilgotniejsza łąka pachnąca Miętą i Melisą. "
            "To dobre miejsce do Zielarstwa, szczególnie dla początkujących."
        ),
        "exits": {"west": "meadow", "east": "riverbank"},
    },
    "flower_meadow": {
        "zone": "Łąki", "name": "Łąka Kwiatów",
        "desc": (
            "Kolorowa łąka pełna Rumianku, Lawendy i Krwawnika. "
            "Dalej na zachodzie zaczyna się Gaj Szeptów."
        ),
        "exits": {"east": "meadow", "west": "whisper_grove"},
    },
    "lakeside_meadow": {
        "zone": "Łąki", "name": "Łąka Nadjeziorna",
        "desc": (
            "Łąka schodząca ku Srebrnemu Jezioru. "
            "Rosną tu Mięta, Melisa, Rumianek i inne zioła lubiące wilgoć."
        ),
        "exits": {"north": "meadow", "south": "lake_shore"},
    },
    "lake_shore": {
        "zone": "Dzicz", "name": "Brzeg Srebrnego Jeziora",
        "desc": "Spokojne jezioro jest osobnym łowiskiem dla ryb jeziorowych.",
        "exits": {"north": "lakeside_meadow"},
    },
    "whisper_grove": {
        "zone": "Dzicz", "name": "Gaj Szeptów",
        "desc": "Stare drzewa szepczą pod wpływem magicznego wiatru.",
        "exits": {"east": "flower_meadow", "south": "deep_grove", "west": "lumberjack_camp", "north": "herbalist_hut"},
    },
    "herbalist_hut": {
        "zone": "Dzicz", "name": "Chata Zielarki",
        "desc": "Półki są pełne suszonych ziół, fiolek i alchemicznych naczyń.",
        "exits": {"south": "whisper_grove"},
    },
    "lumberjack_camp": {
        "zone": "Dzicz", "name": "Obóz Drwala",
        "desc": "Przy stosach drewna stoi warsztat Drwala Brana. Tutaj kupuje się Piłę.",
        "exits": {"east": "whisper_grove"},
    },
    "deep_grove": {
        "zone": "Dzicz", "name": "Głębia Gaju",
        "desc": "Światło prawie nie dociera między gęste konary.",
        "exits": {"north": "whisper_grove", "east": "hill"},
    },
    "hill": {
        "zone": "Dzicz", "name": "Wzgórze Kamiennych Znaków",
        "desc": "Na szczycie stoją stare kamienie pokryte nieczytelnymi runami.",
        "exits": {"west": "deep_grove", "north": "shrine"},
    },
    "shrine": {
        "zone": "Dzicz", "name": "Zapomniana Kapliczka",
        "desc": "Mała kapliczka poświęcona dawnym strażnikom dusz.",
        "exits": {"south": "hill"},
    },
    "riverbank": {
        "zone": "Dzicz", "name": "Brzeg Rzeki",
        "desc": "Szybka rzeka oddziela łąki od ruin starego pogranicza.",
        "exits": {"west": "mint_meadow", "east": "stone_bridge"},
    },
    "stone_bridge": {
        "zone": "Dzicz", "name": "Kamienny Most",
        "desc": "Popękany most prowadzi na wschodni brzeg.",
        "exits": {"west": "riverbank", "east": "ruined_watchtower"},
    },
    "ruined_watchtower": {
        "zone": "Ruiny Strażnicy", "name": "Ruiny Strażnicy",
        "desc": (
            "Zawalona wieża obserwacyjna góruje nad starym pograniczem. "
            "Gobliny plądrują wejście, lecz spod gruzów prowadzą schody do zachowanych części dawnego garnizonu."
        ),
        "exits": {
            "west": "stone_bridge", "south": "goblin_camp", "east": "graveyard",
            "down": "ruin_gatehouse",
        },
    },
    "ruin_gatehouse": {
        "zone": "Ruiny Strażnicy", "name": "Zawalona Brama Strażnicy",
        "desc": (
            "Kamienny korytarz pod wieżą wciąż nosi ślady dawnej obrony. "
            "Połamane kraty i tarcze tworzą wąskie przejście do wnętrza ruin."
        ),
        "exits": {"up": "ruined_watchtower", "east": "ruin_courtyard"},
    },
    "ruin_courtyard": {
        "zone": "Ruiny Strażnicy", "name": "Wewnętrzny Dziedziniec",
        "desc": (
            "Popękane płyty dziedzińca otaczają resztki studni. "
            "Wokół zachowały się wejścia do koszar, murów i piwnic dawnej straży."
        ),
        "exits": {
            "west": "ruin_gatehouse", "north": "ruin_barracks",
            "east": "ruin_wall_walk", "south": "ruin_cellar",
        },
    },
    "ruin_barracks": {
        "zone": "Ruiny Strażnicy", "name": "Opuszczone Koszary",
        "desc": (
            "Spróchniałe prycze stoją między zardzewiałymi stojakami na broń. "
            "Niektórzy dawni strażnicy najwyraźniej nigdy nie opuścili posterunku."
        ),
        "exits": {"south": "ruin_courtyard", "east": "ruin_armory"},
    },
    "ruin_armory": {
        "zone": "Ruiny Strażnicy", "name": "Zbrojownia Starej Straży",
        "desc": (
            "Ciężkie szafy i skrzynie z resztkami uzbrojenia wypełniają kamienną salę. "
            "Na ścianach wiszą pęknięte herby dawnego garnizonu."
        ),
        "exits": {"west": "ruin_barracks", "east": "ruin_command_chamber"},
    },
    "ruin_wall_walk": {
        "zone": "Ruiny Strażnicy", "name": "Chodnik na Murze",
        "desc": (
            "Wąski chodnik biegnie po ocalałym fragmencie muru. "
            "Dawne stanowiska kuszników nadal spoglądają na drogę i dolinę."
        ),
        "exits": {"west": "ruin_courtyard", "north": "ruin_archive"},
    },
    "ruin_archive": {
        "zone": "Ruiny Strażnicy", "name": "Archiwum Runiczne",
        "desc": (
            "Kamienne tablice i metalowe pieczęcie pokrywają resztki archiwum. "
            "W powietrzu utrzymuje się słaba, lecz wciąż aktywna magia ochronna."
        ),
        "exits": {"south": "ruin_wall_walk", "down": "ruin_undercroft"},
    },
    "ruin_cellar": {
        "zone": "Ruiny Strażnicy", "name": "Piwnice Strażnicy",
        "desc": (
            "Wilgotne piwnice pełne są rozbitych beczek, kości i śladów szabrowników. "
            "Niżej prowadzi stary tunel służbowy."
        ),
        "exits": {"north": "ruin_courtyard", "down": "ruin_undercroft"},
    },
    "ruin_undercroft": {
        "zone": "Ruiny Strażnicy", "name": "Podziemia Garnizonu",
        "desc": (
            "Niskie sklepienia podtrzymują filary pokryte znakami wartowników. "
            "Stąd prowadzi droga do zapieczętowanej sali wewnętrznej."
        ),
        "exits": {
            "up": "ruin_cellar", "west": "ruin_archive", "east": "ruin_sealed_hall",
        },
    },
    "ruin_sealed_hall": {
        "zone": "Ruiny Strażnicy", "name": "Sala Pieczęci",
        "desc": (
            "Pęknięte pieczęcie na posadzce wciąż pulsują bladym światłem. "
            "Za nimi znajduje się dawna komnata dowódcy strażnicy."
        ),
        "exits": {"west": "ruin_undercroft", "north": "ruin_command_chamber"},
    },
    "ruin_command_chamber": {
        "zone": "Ruiny Strażnicy", "name": "Komnata Dowódcy Strażnicy",
        "desc": (
            "Ocalały stół dowódcy stoi pod poszarpanym sztandarem. "
            "Najpotężniejszy z dawnych obrońców strzeże tej komnaty nawet po upadku garnizonu."
        ),
        "exits": {"south": "ruin_sealed_hall", "west": "ruin_armory"},
    },
    "goblin_camp": {
        "zone": "Dzicz", "name": "Obóz Goblinów",
        "desc": (
            "Prymitywne namioty stoją wokół dymiącego ogniska. "
            "Na wschodzie w skale zieje wejście do rozległych Jaskiń Goblinów."
        ),
        "exits": {"north": "ruined_watchtower", "south": "cave_entrance", "east": "goblin_cave_mouth"},
    },
    "goblin_cave_mouth": {
        "zone": "Jaskinie Goblinów", "name": "Wejście do Jaskiń Goblinów",
        "desc": "Niski skalny otwór jest obwieszony kośćmi, sznurkami i prymitywnymi dzwonkami alarmowymi.",
        "exits": {"west": "goblin_camp", "east": "goblin_fungus_gallery"},
    },
    "goblin_fungus_gallery": {
        "zone": "Jaskinie Goblinów", "name": "Galeria Grzybów",
        "desc": "Wilgotny korytarz porastają świecące grzyby. W bocznych niszach widać ślady goblińskich wartowników.",
        "exits": {"west": "goblin_cave_mouth", "east": "goblin_scrap_tunnels", "south": "goblin_shaman_hollow"},
    },
    "goblin_scrap_tunnels": {
        "zone": "Jaskinie Goblinów", "name": "Tunele Złomu",
        "desc": "Gobliny zatarasowały ściany resztkami pancerzy, kół i połamanych narzędzi.",
        "exits": {"west": "goblin_fungus_gallery", "east": "goblin_guard_post", "south": "goblin_bomb_workshop"},
    },
    "goblin_shaman_hollow": {
        "zone": "Jaskinie Goblinów", "name": "Kotlina Szamanów",
        "desc": "Dym z gorzkich ziół miesza się tu z zielonkawą poświatą prostych goblińskich rytuałów.",
        "exits": {"north": "goblin_fungus_gallery", "east": "goblin_war_den"},
    },
    "goblin_bomb_workshop": {
        "zone": "Jaskinie Goblinów", "name": "Warsztat Bombiarzy",
        "desc": "Na chwiejnych stołach leżą gliniane kule, proch i wiązki lontów. Powietrze pachnie siarką.",
        "exits": {"north": "goblin_scrap_tunnels", "east": "goblin_war_den"},
    },
    "goblin_guard_post": {
        "zone": "Jaskinie Goblinów", "name": "Podziemny Posterunek",
        "desc": "Drewniane barykady i ostre pale tworzą pierwszy prawdziwy punkt obrony głębszej części jaskiń.",
        "exits": {"west": "goblin_scrap_tunnels", "east": "goblin_war_den"},
    },
    "goblin_war_den": {
        "zone": "Jaskinie Goblinów", "name": "Nora Wojenna",
        "desc": "Kamienne stoły pokrywają mapy szlaków, skradzione chorągwie i stosy broni gotowej do użycia.",
        "exits": {"west": "goblin_guard_post", "north": "goblin_shaman_hollow", "south": "goblin_bomb_workshop", "east": "goblin_treasure_burrow"},
    },
    "goblin_treasure_burrow": {
        "zone": "Jaskinie Goblinów", "name": "Nora Łupów",
        "desc": "Skrzynie, worki i chaotyczne stosy skradzionych przedmiotów wypełniają prawie całe pomieszczenie.",
        "exits": {"west": "goblin_war_den", "east": "goblin_throne_cave"},
    },
    "goblin_throne_cave": {
        "zone": "Jaskinie Goblinów", "name": "Grota Króla Goblinów",
        "desc": "Najgłębsza komora została zamieniona w prymitywną salę tronową. Tu rządzi Król Goblinów.",
        "exits": {"west": "goblin_treasure_burrow"},
    },
    "cave_entrance": {
        "zone": "Podziemia", "name": "Wejście do Kopalni Głębinowej",
        "desc": "Główne wejście do jedynej kopalni świata. Niżej zaczynają się kolejne poziomy Kopalni Głębinowej.",
        "exits": {"north": "goblin_camp", "down": "cave_tunnel"},
    },
    "cave_tunnel": {
        "zone": "Podziemia", "name": "Tunel Wejściowy Kopalni Głębinowej",
        "desc": "Tunel prowadzi z wejścia do komnaty zejściowej Kopalni Głębinowej.",
        "exits": {"up": "cave_entrance", "east": "crystal_chamber"},
    },
    "crystal_chamber": {
        "zone": "Podziemia", "name": "Komnata Zejściowa Kopalni Głębinowej",
        "desc": "Ostatnia komnata wejściowa. Stąd schodzi się na poziom 1 jedynej Kopalni Głębinowej.",
        "exits": {"west": "cave_tunnel"},
    },
    "graveyard": {
        "zone": "Dzicz", "name": "Stary Cmentarz",
        "desc": "Pęknięte nagrobki otaczają zejście do zapomnianej krypty.",
        "exits": {"west": "ruined_watchtower", "down": "crypt_entrance"},
    },
    "crypt_entrance": {
        "zone": "Podziemia", "name": "Przedsionek Krypty",
        "desc": "Kamienne schody prowadzą w ciemność.",
        "exits": {"up": "graveyard", "south": "crypt_hall"},
    },
    "crypt_hall": {
        "zone": "Podziemia", "name": "Sala Krypty",
        "desc": "W ścianach znajdują się stare nisze grobowe.",
        "exits": {"north": "crypt_entrance", "down": "crypt_depths"},
    },
    "crypt_depths": {
        "zone": "Podziemia", "name": "Głębia Krypty",
        "desc": "Najstarsza część podziemi. Powietrze drży od niespokojnej energii.",
        "exits": {"up": "crypt_hall"},
    },
    "old_road": {
        "zone": "Dzicz", "name": "Stary Trakt",
        "desc": "Kamienny trakt prowadzi między zarośniętymi słupami granicznymi. Na wschodzie widać wartownię straży.",
        "exits": {"south": "north_gate", "north": "crossroads", "east": "north_watchpost"},
    },
    "north_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Północna",
        "desc": "Drewniana wartownia pilnuje północnego szlaku. Strażnicy obserwują ruch na Starym Trakcie.",
        "exits": {"west": "old_road", "east": "frontier_watchpost"},
    },
    "frontier_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Pogranicza",
        "desc": "Kamienno-drewniany posterunek stoi na granicy bezpiecznych ziem. Dalej zaczyna się teren bandytów.",
        "exits": {"west": "north_watchpost", "east": "bandit_camp"},
    },
    "bandit_camp": {
        "zone": "Obozowiska Bandytów", "name": "Skraj Obozowiska Bandytów",
        "desc": (
            "Pierwsze brudne namioty i wygasające ogniska stoją tuż za granicą straży. "
            "Dalej obozowisko rozdziela się na kilka pilnowanych części."
        ),
        "exits": {"west": "frontier_watchpost", "east": "bandit_outer_ring", "north": "bandit_supply_tents", "south": "bandit_training_yard"},
    },
    "bandit_outer_ring": {
        "zone": "Obozowiska Bandytów", "name": "Zewnętrzny Pierścień Obozu",
        "desc": "Niskie barykady, ogniska i prowizoryczne strażnice tworzą zewnętrzny pas obrony bandytów.",
        "exits": {"west": "bandit_camp", "east": "bandit_barricade"},
    },
    "bandit_supply_tents": {
        "zone": "Obozowiska Bandytów", "name": "Namioty Zaopatrzenia",
        "desc": "Pod płachtami leżą worki z jedzeniem, beczki i towary zabrane kupieckim karawanom.",
        "exits": {"south": "bandit_camp", "east": "bandit_loot_depot"},
    },
    "bandit_training_yard": {
        "zone": "Obozowiska Bandytów", "name": "Plac Ćwiczeń Bandytów",
        "desc": "Zużyte manekiny, tarcze i prowizoryczna arena służą bandytom do brutalnych ćwiczeń.",
        "exits": {"north": "bandit_camp", "east": "bandit_arena"},
    },
    "bandit_barricade": {
        "zone": "Obozowiska Bandytów", "name": "Wewnętrzna Barykada",
        "desc": "Wysoka palisada oddziela zwykłych rabusiów od lepiej uzbrojonej części obozu.",
        "exits": {"west": "bandit_outer_ring", "east": "bandit_inner_camp"},
    },
    "bandit_loot_depot": {
        "zone": "Obozowiska Bandytów", "name": "Magazyn Łupów",
        "desc": "Skrzynie z monetami, bronią i skradzionymi zapasami stoją pod silną strażą.",
        "exits": {"west": "bandit_supply_tents", "south": "bandit_inner_camp"},
    },
    "bandit_arena": {
        "zone": "Obozowiska Bandytów", "name": "Krąg Walk",
        "desc": "Ubita ziemia jest otoczona palami. Najsilniejsi bandyci ćwiczą tu walkę bez zasad.",
        "exits": {"west": "bandit_training_yard", "north": "bandit_inner_camp"},
    },
    "bandit_inner_camp": {
        "zone": "Obozowiska Bandytów", "name": "Wewnętrzne Obozowisko",
        "desc": "Tu stoją najlepsze namioty, stoły dowódców i straże pilnujące drogi do kwatery Herszta.",
        "exits": {"west": "bandit_barricade", "north": "bandit_loot_depot", "south": "bandit_arena", "east": "bandit_command_tent"},
    },
    "bandit_command_tent": {
        "zone": "Obozowiska Bandytów", "name": "Namiot Herszta",
        "desc": "Duży namiot pełen map, rozkazów i trofeów. To tutaj przebywa Herszt Bandytów.",
        "exits": {"west": "bandit_inner_camp"},
    },
    "crossroads": {
        "zone": "Dzicz", "name": "Rozdroże",
        "desc": "Stary drogowskaz wskazuje zachód ku lasom i wschód ku ruinom.",
        "exits": {"south": "old_road", "west": "deep_grove", "east": "ruined_watchtower"},
    },
}

def build_mine_depth_rooms():
    ROOMS["crystal_chamber"]["exits"]["down"] = mine_floor_id(1)

    for floor in range(MINE_MIN_FLOOR, MINE_MAX_FLOOR + 1):
        exits = {
            "up": (
                "crystal_chamber"
                if floor == MINE_MIN_FLOOR
                else mine_floor_id(floor - 1)
            )
        }
        if floor < MINE_MAX_FLOOR:
            exits["down"] = mine_floor_id(floor + 1)

        if floor < 10:
            band = "kamień i miedź"
        elif floor < 25:
            band = "miedź i żelazo"
        elif floor < 50:
            band = "żelazo i srebro"
        elif floor < 100:
            band = "srebro i złoto"
        elif floor < 120:
            band = "złoto i kobalt"
        elif floor < 140:
            band = "kobalt i Kamień Runiczny"
        elif floor < 160:
            band = "Kamień Runiczny i Smocza Stal"
        elif floor < 180:
            band = "Smocza Stal i Ruda Astralna"
        elif floor < 200:
            band = "Ruda Astralna i Ruda Pustki"
        else:
            band = "Ruda Pustki i Eternium"

        wall_text = " Niżej znajduje się ściana do przebicia Kilofem."
        ROOMS[mine_floor_id(floor)] = {
            "zone": "Kopalnia Głębinowa",
            "name": f"Kopalnia - poziom {floor}",
            "desc": (
                f"Poziom {floor}. Pierwsze 200 poziomów to ręcznie przygotowana część Kopalni. "
                f"Najczęstsze złoża: {band}." + wall_text
            ),
            "exits": exits,
        }

build_mine_depth_rooms()

ROOMS["jeweler_workshop"] = {
    "zone": "Miasto Dusz",
    "name": "Pracownia Jubilerska",
    "desc": (
        "Jasna pracownia pełna drobnych narzędzi, metalowych opraw "
        "i stołów do wykonywania pierścieni oraz naszyjników. "
        "Pracuje tutaj Jubilerka Mirella."
    ),
    "exits": {"down": "market"},
}
ROOMS["market"]["exits"]["up"] = "jeweler_workshop"

DIRECTION_ALIASES = {
    "n": "north", "north": "north", "północ": "north", "polnoc": "north",
    "s": "south", "south": "south", "południe": "south", "poludnie": "south",
    "e": "east", "east": "east", "wschód": "east", "wschod": "east",
    "w": "west", "west": "west", "zachód": "west", "zachod": "west",
    "ne": "northeast", "northeast": "northeast", "pnw": "northeast", "północnywschód": "northeast", "polnocnywschod": "northeast",
    "se": "southeast", "southeast": "southeast", "pdw": "southeast", "południowywschód": "southeast", "poludniowywschod": "southeast",
    "sw": "southwest", "southwest": "southwest", "pdz": "southwest", "południowyzachód": "southwest", "poludniowyzachod": "southwest",
    "nw": "northwest", "northwest": "northwest", "pnz": "northwest", "północnyzachód": "northwest", "polnocnyzachod": "northwest",
    "u": "up", "up": "up", "góra": "up", "gora": "up",
    "d": "down", "down": "down", "dół": "down", "dol": "down",
}

# v0.8.56: ruch między lokacjami jest krótkim marszem zamiast natychmiastowego
# przestawienia room_id. Opóźnienie jest celowo niewielkie, żeby NVDA zdążył
# przeczytać kierunek, ale nawigacja po dużym świecie nadal była wygodna.
DIRECTION_WALK_LABELS = {
    "north": "na północ",
    "south": "na południe",
    "east": "na wschód",
    "west": "na zachód",
    "northeast": "na północny wschód",
    "southeast": "na południowy wschód",
    "southwest": "na południowy zachód",
    "northwest": "na północny zachód",
    "up": "w górę",
    "down": "w dół",
}
WALK_STEP_DELAY = float(os.getenv("SOULBOUND_WALK_STEP_DELAY", "0.70"))
GUIDE_STEP_DELAY = float(os.getenv("SOULBOUND_GUIDE_STEP_DELAY", "0.35"))

GUIDE_DESTINATION_ALIASES = {
    # MIASTO, NPC I POZOSTALE CELE
    'ira': 'alpine_herbalist_hut',
    'zielarka alpejska': 'alpine_herbalist_hut',
    'bandyci': 'bandit_camp',
    'bandits': 'bandit_camp',
    'bandit camp': 'bandit_camp',
    'bandit camps': 'bandit_camp',
    'herszt': 'bandit_camp',
    'oboz bandytow': 'bandit_camp',
    'obozowisko bandytow': 'bandit_camp',
    'mistrz karawan': 'caravan_camp',
    'oboz karawan': 'caravan_camp',
    'samir': 'caravan_camp',
    'krysztalowy tunel': 'cave_tunnel',
    'tunel': 'cave_tunnel',
    'laka rumianku': 'chamomile_meadow',
    'rozdroze': 'crossroads',
    'komnata krysztalowa': 'crystal_chamber',
    'krysztal': 'crystal_chamber',
    'krysztalowa komnata': 'crystal_chamber',
    'glebia gaju': 'deep_grove',
    'stara kopalnia krasnoludow': 'dwarf_mine_entrance',
    'kwiatowa laka': 'flower_meadow',
    'laka kwiatow': 'flower_meadow',
    'anna': 'frontier_watchpost',
    'strazniczka anna': 'frontier_watchpost',
    'wartownia pogranicza': 'frontier_watchpost',
    'laka zen szenia': 'ginseng_meadow',
    'laka zenszenia': 'ginseng_meadow',
    'szlak kozic': 'goat_trail',
    'gobliny': 'goblin_camp',
    'goblins': 'goblin_camp',
    'goblin camp': 'goblin_camp',
    'jaskinia goblinow': 'goblin_cave_mouth',
    'jaskinie goblinow': 'goblin_cave_mouth',
    'goblin cave': 'goblin_cave_mouth',
    'goblin caves': 'goblin_cave_mouth',
    'oboz goblinow': 'goblin_camp',
    'cmentarz': 'graveyard',
    'stary cmentarz': 'graveyard',
    'arven': 'guard_hall',
    'kapitan arven': 'guard_hall',
    'straznica': 'guard_hall',
    'harbor': 'harbor',
    'port': 'harbor',
    'port dusz': 'harbor',
    'lak zielarskich': 'herb_meadow_hub',
    'laki zielarskie': 'herb_meadow_hub',
    'chata zielarki': 'herbalist_hut',
    'liora': 'herbalist_hut',
    'zielarka liora': 'herbalist_hut',
    'kamienne znaki': 'hill',
    'wzgorze': 'hill',
    'elda': 'hunter_clearing',
    'lowczyni elda': 'hunter_clearing',
    'polana lowcow': 'hunter_clearing',
    'chata lowcy': 'hunter_lodge',
    'lowca potworow': 'hunter_lodge',
    'ragna': 'hunter_lodge',
    'elia': 'inn',
    'gospoda': 'inn',
    'karczma': 'inn',
    'karczmarka elia': 'inn',
    'kucharz': 'inn',
    'specjalista gotowania': 'inn',
    'brzeg jeziora': 'lake_shore',
    'jezioro': 'lake_shore',
    'laka nadjeziorna': 'lakeside_meadow',
    'nadjeziorna laka': 'lakeside_meadow',
    'laka lawendy': 'lavender_meadow',
    'laka melisy': 'lemon_balm_meadow',
    'archiwista sol': 'library',
    'archiwum': 'library',
    'biblioteka': 'library',
    'sol': 'library',
    'aldren': 'market',
    'bank': 'market',
    'bank dusz': 'market',
    'bankier': 'market',
    'bankier aldren': 'market',
    'market': 'market',
    'rynek': 'market',
    'targ': 'market',
    'laka': 'meadow',
    'laki': 'meadow',
    'srebrna laka': 'meadow',
    'laka miety': 'mint_meadow',
    'mietowa laka': 'mint_meadow',
    'laka ksiezycowego kwiatu': 'moonflower_meadow',
    'laka pokrzywy': 'nettle_meadow',
    'brama polnocna': 'north_gate',
    'polnocna brama': 'north_gate',
    'dowodca roderik': 'north_watchpost',
    'roderik': 'north_watchpost',
    'wartownia polnocna': 'north_watchpost',
    'ocean': 'ocean_platform',
    'platforma': 'ocean_platform',
    'platforma oceaniczna': 'ocean_platform',
    'stary trakt': 'old_road',
    'trakt': 'old_road',
    'brzeg rzeki': 'riverbank',
    'rzeka': 'riverbank',
    'ruiny': 'ruined_watchtower',
    'ruiny straznicy': 'ruined_watchtower',
    'ruiny strażnicy': 'ruined_watchtower',
    'stara straznica': 'ruined_watchtower',
    'stara strażnica': 'ruined_watchtower',
    'laka szalwii': 'sage_meadow',
    'amina': 'sandstone_ruins',
    'badaczka amina': 'sandstone_ruins',
    'molo': 'sea_pier',
    'morskie molo': 'sea_pier',
    'kapliczka': 'shrine',
    'zapomniana kapliczka': 'shrine',
    'brama poludniowa': 'south_gate',
    'poludniowa brama': 'south_gate',
    'centrum': 'square',
    'plac': 'square',
    'plac dusz': 'square',
    'kamienny most': 'stone_bridge',
    'most': 'stone_bridge',
    'harek': 'summit_camp',
    'oboz szczytowy': 'summit_camp',
    'zwiadowca harek': 'summit_camp',
    'elor': 'temple',
    'kaplan elor': 'temple',
    'swiatynia': 'temple',
    'swiatynia odrodzenia': 'temple',
    'piwnica': 'temple_basement',
    'piwnica swiatyni': 'temple_basement',
    'dziedziniec': 'training',
    'plac treningowy': 'training',
    'manekin': 'training',
    'manekiny': 'training',
    'trening': 'training',
    'oltar trolli': 'troll_altar',
    'gleboki oboz wojenny': 'troll_deep_war_camp',
    'badaczka trolli': 'troll_fungus_cavern',
    'grota grzybow': 'troll_fungus_cavern',
    'yorna': 'troll_fungus_cavern',
    'laka waleriany': 'valerian_meadow',
    'gaj': 'whisper_grove',
    'gaj szeptow': 'whisper_grove',
    'mira': 'whisper_grove',
    'zielarka mira': 'whisper_grove',
    'laka krwawnika': 'yarrow_meadow',

    # GILDIA DUSZ I NAUCZYCIELE
    'arkany': 'guild_arcane_chamber',
    'magowie': 'guild_arcane_chamber',
    'psionicy': 'guild_arcane_chamber',
    'sklep maga': 'guild_arcane_chamber',
    'sklep psionika': 'guild_arcane_chamber',
    'berserker hall': 'guild_berserker_chamber',
    'brynja': 'guild_berserker_chamber',
    'sala berserkera': 'guild_berserker_chamber',
    'mnisi': 'guild_body_hall',
    'sala dyscypliny': 'guild_body_hall',
    'sklep mnicha': 'guild_body_hall',
    'sklep straznika': 'guild_body_hall',
    'sklep strażnika': 'guild_body_hall',
    'straznicy': 'guild_body_hall',
    'czarownicy': 'guild_dark_chamber',
    'mroczne sztuki': 'guild_dark_chamber',
    'nekromanci': 'guild_dark_chamber',
    'sklep czarownika': 'guild_dark_chamber',
    'sklep nekromanty': 'guild_dark_chamber',
    'druid grove': 'guild_druid_chamber',
    'gaj druida': 'guild_druid_chamber',
    'thalen': 'guild_druid_chamber',
    'bastion straznika': 'guild_guardian_chamber',
    'borin': 'guild_guardian_chamber',
    'guardian hall': 'guild_guardian_chamber',
    'gildia': 'guild_hall',
    'sala gildii': 'guild_hall',
    'eira': 'guild_hunter_chamber',
    'hunter hall': 'guild_hunter_chamber',
    'sala lowcy': 'guild_hunter_chamber',
    'komnata maga': 'guild_mage_chamber',
    'mage chamber': 'guild_mage_chamber',
    'vaelis': 'guild_mage_chamber',
    'berserkerzy': 'guild_martial_hall',
    'sala oreza': 'guild_martial_hall',
    'sklep berserkera': 'guild_martial_hall',
    'sklep wojownika': 'guild_martial_hall',
    'wojownicy': 'guild_martial_hall',
    'monk hall': 'guild_monk_chamber',
    'sala mnicha': 'guild_monk_chamber',
    'shen': 'guild_monk_chamber',
    'komnata nekromanty': 'guild_necromancer_chamber',
    'morwen': 'guild_necromancer_chamber',
    'necromancer chamber': 'guild_necromancer_chamber',
    'aureon': 'guild_priest_chamber',
    'kaplica kaplana': 'guild_priest_chamber',
    'priest chapel': 'guild_priest_chamber',
    'ilyra': 'guild_psion_chamber',
    'komnata psionika': 'guild_psion_chamber',
    'psion chamber': 'guild_psion_chamber',
    'kael': 'guild_rogue_chamber',
    'rogue hall': 'guild_rogue_chamber',
    'sala lotrzyka': 'guild_rogue_chamber',
    'druidzi': 'guild_sanctuary',
    'kaplani': 'guild_sanctuary',
    'sanktuarium': 'guild_sanctuary',
    'sklep druida': 'guild_sanctuary',
    'sklep kaplana': 'guild_sanctuary',
    'sklep kapłana': 'guild_sanctuary',
    'galeria cieni': 'guild_shadow_gallery',
    'lotrzycy': 'guild_shadow_gallery',
    'lowcy': 'guild_shadow_gallery',
    'sklep lotrzyka': 'guild_shadow_gallery',
    'sklep lowcy': 'guild_shadow_gallery',
    'sklep łotrzyka': 'guild_shadow_gallery',
    'sklep łowcy': 'guild_shadow_gallery',
    'komnata czarownika': 'guild_warlock_chamber',
    'nyra': 'guild_warlock_chamber',
    'warlock chamber': 'guild_warlock_chamber',
    'garran': 'guild_warrior_chamber',
    'sala wojownika': 'guild_warrior_chamber',
    'warrior hall': 'guild_warrior_chamber',

    # PROFESJE I NARZEDZIA
    'laboratorium alchemiczne': 'alchemy_lab',
    'mistrz alchemii': 'alchemy_lab',
    'mozdzierz sklep': 'alchemy_lab',
    'orin': 'alchemy_lab',
    'sklep mozdzierza': 'alchemy_lab',
    'kucharz marcel': 'blue_flame_kitchen',
    'kuchnia blekitnego plomienia': 'blue_flame_kitchen',
    'marcel': 'blue_flame_kitchen',
    'noz kucharski sklep': 'blue_flame_kitchen',
    'sklep noza': 'blue_flame_kitchen',
    'gornik toren': 'cave_entrance',
    'jaskinia': 'cave_entrance',
    'sklep kilof': 'cave_entrance',
    'sklep kilofa': 'cave_entrance',
    'toren': 'cave_entrance',
    'wejscie do jaskini': 'cave_entrance',
    'haldor': 'crafting_workshop',
    'mistrz rzemiosla': 'crafting_workshop',
    'mlot rzemieslniczy sklep': 'crafting_workshop',
    'sklep mlota': 'crafting_workshop',
    'warsztat rzemieslniczy': 'crafting_workshop',
    'rybak borys': 'fish_market',
    'borys': 'fish_market',
    # Stare aliasy Tomasa pozostają tylko dla zgodności zapisanych skrótów/makr.
    'rybak tomas': 'fish_market',
    'ryby': 'fish_market',
    'targ rybny': 'fish_market',
    'tomas': 'fish_market',
    'mistrz wedkarstwa': 'fishing_school',
    'neris': 'fishing_school',
    'sklep wedek': 'fishing_school',
    'sklep wedki': 'fishing_school',
    'szkola wedkarstwa': 'fishing_school',
    'wedka sklep': 'fishing_school',
    'lesniczowka': 'forester_lodge',
    'mistrz drwalstwa': 'forester_lodge',
    'oren': 'forester_lodge',
    'pila sklep': 'forester_lodge',
    'sklep pily': 'forester_lodge',
    'doran': 'forge',
    'kowal': 'forge',
    'kowal doran': 'forge',
    'kuznia': 'forge',
    'mistrzyni zielarstwa': 'herbalism_garden',
    'ogrod zielarski': 'herbalism_garden',
    'sena': 'herbalism_garden',
    'sierp sklep': 'herbalism_garden',
    'sklep sierpa': 'herbalism_garden',
    'jubiler': 'jeweler_workshop',
    'jubilerka': 'jeweler_workshop',
    'jubilerka mirella': 'jeweler_workshop',
    'jubilerstwo': 'jeweler_workshop',
    'mirella': 'jeweler_workshop',
    'pracownia jubilerska': 'jeweler_workshop',
    'sklep szczypiec': 'jeweler_workshop',
    'szczypce sklep': 'jeweler_workshop',
    'bran': 'lumberjack_camp',
    'drwal': 'lumberjack_camp',
    'drwal bran': 'lumberjack_camp',
    'gildia gornikow': 'miners_guild',
    'kordan': 'miners_guild',
    'mistrz gornictwa': 'miners_guild',

    # REGIONY I TERENY
    'legowisko rogatego krola': 'beast_den',
    'rogaty krol': 'beast_den',
    'serce bagna': 'bog_heart',
    'pustynia': 'desert_gate',
    'wielka pustynia': 'desert_gate',
    'sanktuarium wiecznego slonca': 'desert_solar_sanctum',
    'grobowiec slonca': 'desert_sun_tomb',
    'brok': 'mountain_forge',
    'gorska kuznia': 'mountain_forge',
    'kowal gorski': 'mountain_forge',
    'eryk': 'mountain_guard_house',
    'straznik eryk': 'mountain_guard_house',
    'nizsze stoki': 'mountain_lower_slopes',
    'dagna': 'mountain_market',
    'gorski targ mineralow': 'mountain_market',
    'gorska przelecz': 'mountain_pass',
    'gory': 'mountain_pass',
    'sciezka wiecznej burzy': 'mountain_tempest_path',
    'sanktuarium wiecznej burzy': 'mountain_tempest_sanctum',
    'wioska gorska': 'mountain_village',
    'wioska w gorach': 'mountain_village',
    'szczyt burzy': 'storm_summit',
    'swiatynia slonca': 'sun_temple',
    'bagna': 'swamp_boardwalk',
    'czarne bagno': 'swamp_boardwalk',
    'lowca bagien': 'swamp_hunter_post',
    'posterunek bagien': 'swamp_hunter_post',
    'varg': 'swamp_hunter_post',
    'pradawne rozlewisko': 'swamp_primordial_pool',
    'gnijace glebie bagna': 'swamp_rotten_depths',
    'bagienna zielarka': 'swamp_witch_hut',
    'nela': 'swamp_witch_hut',
    'pradawny szlak bestii': 'wild_ancient_path',
    'polnocna dzicz': 'wild_frontier',
    'skraj polnocnej dziczy': 'wild_frontier',
    'pradawna kotlina dziczy': 'wild_primal_hollow',

    # LOCHY I ENDGAME
    'astral': 'astral_gate',
    'astralna brama': 'astral_gate',
    'brama astralna': 'astral_gate',
    'wieza': 'astral_gate',
    'wieza astralna': 'astral_gate',
    'wieża': 'astral_gate',
    'wieża astralna': 'astral_gate',
    'glebia krypty': 'crypt_depths',
    'przedsionek krypty': 'crypt_entrance',
    'wejscie do krypty': 'crypt_entrance',
    'sala krypty': 'crypt_hall',
    'brama twierdzy gigantow': 'giant_fortress_gate',
    'twierdza gigantow': 'giant_fortress_gate',
    'kopalnia glebinowa': 'mine_floor_1',
    'mityczna wieza astralna': 'mythic_astral_gate',
    'mythic astral tower': 'mythic_astral_gate',
    'mityczna krypta': 'mythic_crypt_gate',
    'mythic crypt': 'mythic_crypt_gate',
    'ogrod alchemika': 'prof_alchemy_garden_1',
    'pradawny las': 'prof_ancient_forest_1',
    'kopalnia krysztalow': 'mine_floor_1',
    'krysztalowa kopalnia': 'mine_floor_1',
    'zatopiona grota': 'prof_sunken_grotto_1',
    'otchlan trolli': 'troll_abyss',
    'tron pierwszego wodza': 'troll_abyss_throne',
    'jaskinia trolli': 'troll_cave_entrance',
    'trolle': 'troll_cave_entrance',
    'krol trolli': 'troll_king_den',

    # v0.8.14 Exploration First Guide
    'krypta': 'crypt_entrance',
    'crypt': 'crypt_entrance',
    'kopalnia': 'mine_floor_1',
    'mine': 'mine_floor_1',
    'twierdza': 'giant_fortress_gate',
    'fortress': 'giant_fortress_gate',
    'giant fortress': 'giant_fortress_gate',
    'dzicz': 'old_road',
    'wilds': 'old_road',
    'podziemia': 'cave_entrance',
    'underground': 'cave_entrance',
    'crystal cave': 'cave_entrance',
    'crystal mine': 'mine_floor_1',
    'krysztalowe groty': 'prof_crystal_mine_1',
    'kryształowe groty': 'prof_crystal_mine_1',
    'crystal grottos': 'prof_crystal_mine_1',
    'sunken grotto': 'prof_sunken_grotto_1',
    'ancient forest': 'prof_ancient_forest_1',
    'alchemy garden': 'prof_alchemy_garden_1',

}

TOOL_BUY_ALIASES = {
    "wedka": "fishing_rod",
    "wedke": "fishing_rod",
    "rod": "fishing_rod",
    "kilof": "pickaxe",
    "pickaxe": "pickaxe",
    "pila": "saw",
    "pile": "saw",
    "saw": "saw",
    "mlot": "crafting_hammer",
    "mlot rzemieslniczy": "crafting_hammer",
    "hammer": "crafting_hammer",
    "noz": "chef_knife",
    "noz kucharski": "chef_knife",
    "knife": "chef_knife",
    "sierp": "herbalist_sickle",
    "sierp zielarski": "herbalist_sickle",
    "sickle": "herbalist_sickle",
    "mozdzierz": "alchemy_mortar",
    "mozdzierz alchemiczny": "alchemy_mortar",
    "mortar": "alchemy_mortar",
    "szczypce": "jeweler_pliers",
    "szczypce jubilerskie": "jeweler_pliers",
    "pliers": "jeweler_pliers",
    "jeweler pliers": "jeweler_pliers",
}

CHARACTER_BOUND_TOOL_IDS = {
    "fishing_rod",
    "pickaxe",
    "saw",
    "crafting_hammer",
    "chef_knife",
    "herbalist_sickle",
    "alchemy_mortar",
    "jeweler_pliers",
}

def is_character_bound_item(item_id):
    return item_id in CHARACTER_BOUND_TOOL_IDS

TOOL_SHOP_ROOMS = {
    "fishing_rod": "fish_market",
    "pickaxe": "cave_entrance",
    "saw": "lumberjack_camp",
    "crafting_hammer": "forge",
    "chef_knife": "inn",
    "herbalist_sickle": "herbalist_hut",
    "alchemy_mortar": "herbalist_hut",
    "jeweler_pliers": "jeweler_workshop",
}

EQUIPMENT_SLOT_ALIASES = {
    "helm": "head",
    "helmet": "head",
    "helmik": "head",
    "hełm": "head",
    "glowa": "head",
    "głowa": "head",

    "zbroja": "body",
    "pancerz": "body",
    "napierśnik": "body",
    "napiersnik": "body",
    "korpus": "body",
    "armor": "body",
    "body": "body",

    "rekawice": "hands",
    "rękawice": "hands",
    "dlonie": "hands",
    "dłonie": "hands",
    "gloves": "hands",
    "hands": "hands",

    "nogi": "legs",
    "nogawice": "legs",
    "spodnie": "legs",
    "legs": "legs",

    "buty": "feet",
    "stopy": "feet",
    "boots": "feet",
    "feet": "feet",

    "talizman": "charm",
    "amulet": "charm",
    "charm": "charm",
    "talizman 1": "charm1", "talizman1": "charm1",
    "amulet 1": "charm1", "charm 1": "charm1", "charm1": "charm1",
    "talizman 2": "charm2", "talizman2": "charm2",
    "amulet 2": "charm2", "charm 2": "charm2", "charm2": "charm2",

    "pierścień": "ring",
    "pierscien": "ring",
    "pierścien": "ring",
    "ring": "ring",
    "pierścień 1": "ring1", "pierscien 1": "ring1",
    "ring 1": "ring1", "ring1": "ring1", "first ring": "ring1",
    "pierścień 2": "ring2", "pierscien 2": "ring2",
    "ring 2": "ring2", "ring2": "ring2", "second ring": "ring2",

    "naszyjnik": "necklace",
    "naszyjnika": "necklace",
    "necklace": "necklace",

    "kolczyk": "earring",
    "kolczyki": "earring",
    "earring": "earring",
    "earrings": "earring",
    "kolczyk 1": "earring1", "kolczyk1": "earring1",
    "earring 1": "earring1", "earring1": "earring1",
    "kolczyk 2": "earring2", "kolczyk2": "earring2",
    "earring 2": "earring2", "earring2": "earring2",

    "naramienniki": "shoulders",
    "naramiennik": "shoulders",
    "shoulders": "shoulders",
    "shoulder": "shoulders",

    "pas": "belt",
    "belt": "belt",

    "peleryna": "cloak",
    "plaszcz": "cloak",
    "płaszcz": "cloak",
    "cloak": "cloak",

    "karwasze": "bracers",
    "karwasz": "bracers",
    "bracers": "bracers",

    "relikt": "relic",
    "relic": "relic",

}

EQUIPMENT_SLOT_NAMES = {
    "head": "głowa",
    "body": "korpus",
    "hands": "dłonie",
    "legs": "nogi",
    "feet": "stopy",
    "charm": "talizman",
    "charm1": "talizman 1",
    "charm2": "talizman 2",
    "ring": "pierścień",
    "ring1": "pierścień 1",
    "ring2": "pierścień 2",
    "necklace": "naszyjnik",
    "earring": "kolczyki",
    "earring1": "kolczyk 1",
    "earring2": "kolczyk 2",
    "shoulders": "naramienniki",
    "belt": "pas",
    "cloak": "peleryna",
    "bracers": "karwasze",
    "relic": "relikt",
}

EXP_AREAS = (
    {
        "id": "trening",
        "name": "Plac Treningowy",
        "aliases": (
            "trening", "plac treningowy", "manekin", "manekiny",
        ),
        "soul_min": 1,
        "soul_max": 10,
        "difficulty": "bardzo łatwa",
        "guide": "manekiny",
        "enemies": "Żywy Manekin",
        "description": (
            "Najbezpieczniejsze miejsce do sprawdzania obrażeń, "
            "umiejętności i podstaw walki. Dobre na sam początek."
        ),
        "note": (
            "Manekin jest przeznaczony głównie do treningu, "
            "więc szybko warto przenieść się do Podziemi lub Dziczy."
        ),
    },
    {
        "id": "podziemia",
        "name": "Podziemia i Kryształowa Jaskinia",
        "aliases": (
            "podziemia", "krysztalowa jaskinia", "jaskinia",
            "piwnica swiatyni", "krysztalowa komnata",
        ),
        "soul_min": 1,
        "soul_max": 25,
        "difficulty": "łatwa",
        "guide": "jaskinia",
        "enemies": (
            "Szczur Świątynny, Szkielet Strażnik, Upiór Krypty, "
            "Kryształowy Strażnik i Kryształowy Władca"
        ),
        "description": (
            "Wczesne podziemia z rosnącą trudnością. "
            "Dobre miejsce na pierwsze regularne walki i oswojenie się "
            "z silniejszymi przeciwnikami."
        ),
        "note": (
            "Kryształowy Władca jest bossem i jest znacznie mocniejszy "
            "od zwykłych mobów tego regionu."
        ),
    },
    {
        "id": "bandit_camps",
        "name": "Obozowiska Bandytów",
        "aliases": (
            "bandyci", "oboz bandytow", "obozowiska bandytow", "bandit camp", "bandit camps",
        ),
        "soul_min": 10,
        "soul_max": 40,
        "difficulty": "łatwa do średniej",
        "guide": "bandyci",
        "enemies": (
            "Bandyta, Bandycki Zwiadowca, Kusznik, Rzezimieszek, Maruder, "
            "Najeźdźca, Alchemik, Egzekutor, Weteran, Kapitan Bandytów i Herszt Bandytów"
        ),
        "description": (
            "Rozbudowany kompleks kilku części obozu. Im głębiej, tym lepiej uzbrojeni przeciwnicy. "
            "Wewnętrzne obozowisko prowadzi do namiotu Herszta."
        ),
        "note": (
            "Prowadzenie zatrzymuje przed wejściem do obozowiska. Wnętrze trzeba eksplorować samodzielnie."
        ),
    },
    {
        "id": "goblin_caves",
        "name": "Jaskinie Goblinów",
        "aliases": (
            "gobliny", "jaskinia goblinow", "jaskinie goblinow", "goblin cave", "goblin caves",
        ),
        "soul_min": 10,
        "soul_max": 45,
        "difficulty": "łatwa do średniej",
        "guide": "jaskinie goblinow",
        "enemies": (
            "Goblin, Gobliński Zwiadowca, Włócznik, Łucznik, Osiłek, Szaman, Bombiarz, "
            "Strażnik Jaskiń, Wojownik Króla, Gobliński Wódz Wojenny i Król Goblinów"
        ),
        "description": (
            "Rozległy podziemny kompleks od galerii grzybów po grotę Króla Goblinów. "
            "W głębi pojawia się więcej magii, cięższa straż i elity."
        ),
        "note": (
            "Prowadzenie zatrzymuje przed wejściem do Jaskiń Goblinów. Wnętrze i drogę do króla trzeba odkryć samemu."
        ),
    },
    {
        "id": "ruiny_straznicy",
        "name": "Ruiny Strażnicy",
        "aliases": (
            "ruiny straznicy", "ruiny strażnicy", "stara straznica", "stara strażnica", "ruined watchtower",
        ),
        "soul_min": 15,
        "soul_max": 55,
        "difficulty": "łatwa do średniej",
        "guide": "ruiny straznicy",
        "enemies": (
            "Ożywieni Wartownicy, Włócznicy, Kusznicy i Tarczownicy Starej Straży, "
            "Runiczni Strażnicy, Widma Strażnicy, Kamienni Obserwatorzy, Goblińscy Łupieżcy, "
            "Kapitan Starej Straży i Strażnik Ruin"
        ),
        "description": (
            "Rozbudowane ruiny dawnego garnizonu: brama, dziedziniec, koszary, zbrojownia, mur, "
            "archiwum runiczne, piwnice, podziemia, sala pieczęci i komnata dowódcy."
        ),
        "note": (
            "Wejście do wnętrza prowadzi w dół z głównej lokacji Ruiny Strażnicy. "
            "Strażnik Ruin znajduje się teraz w najgłębszej komnacie dowódcy."
        ),
    },
    {
        "id": "dzicz",
        "name": "Dzicz",
        "aliases": (
            "dzicz", "ruiny", "gobliny", "bandyci", "wilki",
            "stary cmentarz", "oboz bandytow",
        ),
        "soul_min": 10,
        "soul_max": 45,
        "difficulty": "łatwa do średniej",
        "guide": "ruiny",
        "enemies": (
            "Bandyci wielu rang, Gobliny wielu rang, Goblińscy Szamani i Bombiarze, "
            "oraz Wilki Cienia"
        ),
        "description": (
            "Rozległy teren świata z kilkoma grupami przeciwników. "
            "Dobry do zwykłego expienia, questów i zdobywania sprzętu."
        ),
        "note": (
            "Obozowiska Bandytów i Jaskinie Goblinów są teraz osobnymi, rozbudowanymi expowiskami. "
            "Herszt Bandytów i Król Goblinów znajdują się głęboko w swoich obszarach."
        ),
    },
    {
        "id": "trolle",
        "name": "Góry i Jaskinia Trolli",
        "aliases": (
            "trolle", "jaskinia trolli", "gory", "góry",
            "gorski szlak", "krol trolli",
        ),
        "soul_min": 25,
        "soul_max": 70,
        "difficulty": "średnia",
        "guide": "jaskinia trolli",
        "enemies": (
            "Górskie Trolle, Trolle Osiłki, Trolle Szamani "
            "oraz rzadkie i elitarne warianty trolli"
        ),
        "description": (
            "Mocniejsze expowisko powiązane z Wioską Górską. "
            "Przeciwnicy mają więcej HP, a rzadkie trolle i elite affixy "
            "mogą wyraźnie zwiększyć trudność."
        ),
        "note": (
            "Na końcu jaskini czeka Król Trolli Grum. "
            "Trolle mogą też zostawiać Skradzione Skrzynie Rudy."
        ),
    },
    {
        "id": "giganci",
        "name": "Twierdza Gigantów 1+",
        "aliases": (
            "giganci", "twierdza gigantow", "twierdza gigantów",
            "twierdza", "cyklopy", "ogry",
        ),
        "soul_min": 45,
        "soul_max": 130,
        "difficulty": "średnia do bardzo trudnej",
        "guide": "twierdza gigantow",
        "enemies": (
            "Ogrzy Miotacze Głazów, Cyklopi Strażnicy i Górskie Giganty"
        ),
        "description": (
            "Nieskończony górski dungeon; każdy poziom od 1 jest tworzony dynamicznie dopiero przy wejściu. "
            "Z każdym poziomem rośnie HP, obrażenie i nagroda Soul XP. "
            "Nadaje się do dłuższego expienia bez zmiany regionu."
        ),
        "note": (
            "Boss stoi co 10 poziomów i musi zostać pokonany, aby wejść wyżej."
        ),
    },
    {
        "id": "krypta",
        "name": "Krypta Nieskończona",
        "aliases": (
            "krypta", "krypta nieskonczona", "krypta nieskończona", "crypt", "infinite crypt",
        ),
        "soul_min": 30,
        "soul_max": 200,
        "difficulty": "skalowana bez końca od średniej do ekstremalnej",
        "guide": "wejscie do krypty",
        "enemies": (
            "Szkielety Krypty, Upiory Krypty, Strażnicy Sarkofagu, "
            "Cienie Katakumb i Zjawiska Pustki"
        ),
        "description": (
            "Główne nieskończone expowisko. "
            "Trudność i XP rosną z piętrem, z dodatkowym progiem co 10 pięter, "
            "więc możesz dobierać głębokość do aktualnej siły postaci."
        ),
        "note": (
            "Boss stoi co 10 pięter. Boss blokuje zejście niżej. "
            "Pokonani bossowie odblokowują checkpointy portalu."
        ),
    },
    {
        "id": "astral",
        "name": "Wieża Astralna 100+",
        "aliases": (
            "astral", "wieza astralna", "wieża astralna",
            "astralna wieza", "astralna wieża",
        ),
        "soul_min": 100,
        "soul_max": 200,
        "difficulty": "trudna i endgame",
        "guide": "wieza astralna",
        "enemies": (
            "Astralni Strażnicy, Widma Konstelacji, Rycerze Gwiezdnego Pyłu, "
            "Tkacze Nebuli, Heroldzi Komety i Strażnicy Firmamentu"
        ),
        "description": (
            "Drugie główne expowisko endgame. "
            "Wieża zaczyna się na poziomie 100 i wymaga Soul Level 100. "
            "Daje wysokie Soul XP oraz Astralny ekwipunek."
        ),
        "note": (
            "Boss stoi co 10 poziomów od 100 bez górnego limitu i blokuje drogę w górę."
        ),
    },
    {
        "id": "mythic_crypt",
        "name": "Mityczna Krypta Nieskończona",
        "aliases": (
            "mityczna krypta", "mythic crypt", "mythic krypta",
        ),
        "soul_min": 1,
        "soul_max": 200,
        "difficulty": "bardzo trudna od wejścia, skalowana bez końca",
        "guide": "mityczna krypta",
        "enemies": (
            "Mityczni Kościani Rycerze, Mityczne Upiory, "
            "Mityczni Żniwiarze Grobowca i Strażnicy Otchłani"
        ),
        "description": (
            "Mityczna wersja Krypty jest dostępna bez blokady Soul Level. "
            "Od pierwszego piętra jest bardzo trudna, a trudność i XP rosną bez końca."
        ),
        "note": (
            "Wejście nie ma wymogu Soul Level ani ukończenia zwykłej Krypty. "
            "Mityczny boss występuje co 10 pięter bez końca i blokuje zejście niżej."
        ),
    },
    {
        "id": "mythic_astral",
        "name": "Mityczna Wieża Astralna 1+",
        "aliases": (
            "mityczna wieza astralna", "mityczna wieża astralna",
            "mythic astral", "mythic astral tower",
        ),
        "soul_min": 100,
        "soul_max": 200,
        "difficulty": "najtrudniejszy endgame",
        "guide": "mityczna wieza astralna",
        "enemies": (
            "Mityczni Astralni Strażnicy, Mityczni Rycerze Konstelacji, "
            "Mityczne Widma Nebuli i Heroldzi Gwiezdnej Burzy"
        ),
        "description": (
            "Mityczna Wieża Astralna jest dostępna od Soul Level 100. "
            "To ekstremalnie trudne expowisko z bardzo wysokimi nagrodami Soul XP."
        ),
        "note": (
            "Wejście wymaga Soul Level 100. "
            "Nie wymaga ukończenia zwykłej Wieży Astralnej do poziomu 200. "
            "Mityczny boss występuje co 10 poziomów."
        ),
    },
)

# v0.8.54 - dynamiczne kategorie terenów i skalowanie EXP.
# Kategoria bazowa opisuje naturalne przeznaczenie obszaru. Ocena "dla ciebie"
# jest liczona na bieżąco z faktycznego rozwoju postaci, bo Soulbound nie ma
# ogólnego levelu postaci.
EXP_AREA_BASE_CATEGORY = {
    "trening": "Początkujący",
    "podziemia": "Początkujący",
    "bandit_camps": "Początkujący",
    "goblin_caves": "Początkujący",
    "ruiny_straznicy": "Początkujący",
    "dzicz": "Początkujący",
    "kanaly": "Początkujący",
    "cmentarz": "Początkujący",
    "whisper_forest": "Początkujący",
    "trolle": "Umiarkowany",
    "legowisko_bestii": "Umiarkowany",
    "ruiny_kultystow": "Umiarkowany",
    "bagna": "Umiarkowany",
    "giganci": "Trudny",
    "lodowe_jaskinie": "Trudny",
    "pustynia": "Trudny",
    "nekropolia": "Trudny",
    "krypta": "Trudny skalowany",
    "astral": "Śmiertelny",
    "mythic_crypt": "Śmiertelny",
    "mythic_astral": "Ekstremalny Endgame",
}

# Orientacyjna siła wejściowa obszaru w skali 1-400. Dla wielopiętrowych
# lochów faktyczny próg jest dodatkowo liczony z aktualnego piętra.
EXP_AREA_TARGET_POWER = {
    "trening": 1,
    "podziemia": 5,
    "bandit_camps": 10,
    "goblin_caves": 10,
    "ruiny_straznicy": 18,
    "dzicz": 14,
    "kanaly": 12,
    "cmentarz": 15,
    "whisper_forest": 12,
    "trolle": 30,
    "legowisko_bestii": 35,
    "ruiny_kultystow": 45,
    "bagna": 45,
    "giganci": 50,
    "lodowe_jaskinie": 65,
    "pustynia": 75,
    "nekropolia": 80,
    "krypta": 30,
    "astral": 110,
    "mythic_crypt": 130,
    "mythic_astral": 150,
}

EXP_ZONE_AREA_ID = {
    "Podziemia": "podziemia",
    "Obozowiska Bandytów": "bandit_camps",
    "Jaskinie Goblinów": "goblin_caves",
    "Ruiny Strażnicy": "ruiny_straznicy",
    "Dzicz": "dzicz",
    "Góry": "trolle",
    "Jaskinia Trolli": "trolle",
    "Twierdza Gigantów": "giganci",
    "Krypta Nieskończona": "krypta",
    "Wieża Astralna": "astral",
    "Mityczna Krypta": "mythic_crypt",
    "Mityczna Wieża Astralna": "mythic_astral",
    "Bagna": "bagna",
    "Pustynia": "pustynia",
    "Stary Cmentarz": "cmentarz",
    "Ruiny Kultystów": "ruiny_kultystow",
    "Legowisko Bestii": "legowisko_bestii",
    "Nekropolia": "nekropolia",
    "Kanały Pod Miastem": "kanaly",
    "Lodowe Jaskinie": "lodowe_jaskinie",
    "Las Szeptów": "whisper_forest",
}

# v0.23.0: EXP z walki nie jest stałą nagrodą z tabeli moba. Bazowa wartość
# nadal opisuje rangę przeciwnika, ale końcowa wypłata EXP statów, Soul XP i
# Class XP zależy płynnie od siły moba względem AKTUALNEJ siły postaci.
# Dzięki temu słabsza postać dostaje premię za ryzyko, a po przerośnięciu
# danego expowiska ta sama farma daje stopniowo mniej EXP. Waluta i loot nie
# są przez ten mnożnik zmieniane.
DYNAMIC_KILL_XP_MIN_MULTIPLIER = 0.35
DYNAMIC_KILL_XP_MAX_MULTIPLIER = 2.25

# v0.8.66 - teren i EXP są oceniane z faktycznej siły spawnów, a nie tylko
# z ręcznej etykiety biomu. Kalibracja bazuje na krzywej Krypty 1-200:
# zwykły mob około floor 100 ma ~1940 HP i ~39 dmg, floor 200 ~3740/72.
_ROOM_THREAT_CACHE = {}
_ZONE_THREAT_CACHE = {}

def v0866_is_boss_template(template):
    return bool(
        template.get("world_boss")
        or template.get("mini_boss")
        or template.get("crypt_boss")
        or template.get("astral_boss")
        or template.get("mythic_crypt_boss")
        or template.get("mythic_astral_boss")
        or template.get("giant_fortress_boss")
        or template.get("boss_mechanic")
    )

def v0866_is_random_variant_template(template):
    return bool(
        template.get("rare_mob")
        or template.get("elite_affix")
        or template.get("rare_troll")
    )

def v0866_template_explicit_floor_power(template):
    level = template.get("generator_level")
    if level is not None:
        return max(1, min(400, int(level)))
    semantic = generator_core_v027.semantic_floor_level(template)
    return max(1, min(400, int(semantic))) if semantic is not None else None

def v0866_mob_progression_power(template):
    """Compatibility route: active threat is Generator Core stage 1-400."""
    level = template.get("generator_level")
    if level is not None:
        return max(1, min(400, int(level)))
    explicit = v0866_template_explicit_floor_power(template)
    if explicit is not None:
        return explicit
    # Dynamic records are normalized immediately before use.
    v0190_apply_combat_template(template)
    return max(1, min(400, int(template.get("generator_level", 1) or 1)))

def v0866_percentile(values, fraction):
    values = sorted(int(v) for v in values)
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    index = max(0, min(len(values) - 1, int(round((len(values) - 1) * fraction))))
    return values[index]

def v0866_room_threat_profile(room_id, fallback=1):
    cache_key = str(room_id or "")
    cached = _ROOM_THREAT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    normal = []
    bosses = []
    variants = []
    for spawn_room, template_id in MOB_SPAWNS:
        if spawn_room != room_id:
            continue
        template = MOB_TEMPLATES.get(template_id)
        if not template or template.get("training_dummy"):
            continue
        power = v0866_mob_progression_power(template)
        if v0866_is_random_variant_template(template):
            variants.append(power)
        elif v0866_is_boss_template(template):
            bosses.append(power)
        else:
            normal.append(power)
    # 60 percentyl zwykłych spawnów lepiej opisuje realny grind niż maksimum.
    # Endgame odnogi z dwoma silnymi mobami nadal dostają pełny wysoki target.
    target = v0866_percentile(normal, 0.60)
    if target is None:
        target = v0866_percentile(variants, 0.50)
    if target is None:
        target = v0866_percentile(bosses, 0.35)
    if target is None:
        target = max(1, min(400, int(fallback or 1)))
    profile = {
        "target": int(target),
        "normal_min": min(normal) if normal else None,
        "normal_max": max(normal) if normal else None,
        "boss_min": min(bosses) if bosses else None,
        "boss_max": max(bosses) if bosses else None,
        "variant_min": min(variants) if variants else None,
        "variant_max": max(variants) if variants else None,
        "normal_count": len(normal),
        "boss_count": len(bosses),
        "variant_count": len(variants),
    }
    _ROOM_THREAT_CACHE[cache_key] = profile
    return profile

def v0866_threat_label(target, power):
    delta = int(target) - int(power)
    if delta <= -40:
        return "Trywialny"
    if delta <= -15:
        return "Łatwy"
    if delta <= 10:
        return "Odpowiedni"
    if delta <= 30:
        return "Trudny"
    if delta <= 60:
        return "Śmiertelny"
    return "Ekstremalny"


def v0866_zone_threat_profile(zone):
    cache_key = str(zone or "")
    cached = _ZONE_THREAT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    room_targets = []
    boss_targets = []
    for room_id, room in ROOMS.items():
        if room.get("zone") != zone:
            continue
        profile = v0866_room_threat_profile(room_id, fallback=1)
        if profile["normal_count"] or profile["variant_count"]:
            room_targets.append(profile["target"])
        if profile["boss_max"] is not None:
            boss_targets.append(profile["boss_max"])
    result = {
        "min": min(room_targets) if room_targets else None,
        "median": v0866_percentile(room_targets, 0.50),
        "p80": v0866_percentile(room_targets, 0.80),
        "max": max(room_targets) if room_targets else None,
        "boss_min": min(boss_targets) if boss_targets else None,
        "boss_max": max(boss_targets) if boss_targets else None,
        "rooms": len(room_targets),
    }
    _ZONE_THREAT_CACHE[cache_key] = result
    return result

COMMAND_ALIASES = {
    "pomoc": "help", "pomoce": "help",
    "kodowanie": "encoding", "encoding": "encoding",
    "charset": "encoding", "znaki": "encoding",
    "opis": "describe", "opisz": "describe", "describe": "describe", "description": "describe",
    "changes": "changes", "zmiany": "changes", "changelog": "changes",
    "historia": "lifetime", "history": "lifetime", "lifetime": "lifetime",
    "statystykizycia": "lifetime", "lifestats": "lifetime",
    "bufor": "historybuffer", "bufory": "historybuffer", "histbuf": "historybuffer",
    "historybuffer": "historybuffer", "logbuf": "historybuffer",
    "spójrz": "look", "spojrz": "look", "sp": "look", "l": "look",
    "wyjścia": "exits", "wyjscia": "exits", "ex": "exits",
    "wydarzenia": "worldevents", "wydarzenie": "worldevents", "eventy": "worldevents", "events": "worldevents",
    "worldevents": "worldevents", "worldevent": "worldevents",
    "eventxp": "eventxp", "xpevent": "eventxp", "eventexp": "eventxp", "happyhour": "eventxp",
    "wimpy": "wimpy",
    "dynamiceventy": "dynamicevents", "dynamicevents": "dynamicevents", "dynamiczneeventy": "dynamicevents",
    "nemesis": "nemesis", "nemezis": "nemesis",
    "mapa": "map",
    "sekret": "instancesecret", "secret": "instancesecret",
    "tajemnica": "instancesecret",
    "gdzie": "where",
    "trasa": "route", "route": "route", "droga": "route", "sciezka": "route", "ścieżka": "route",
    "kto": "who",
    "expowiska": "expareas", "expowisko": "expareas",
    "terenyexp": "expareas", "terenydoexpienia": "expareas",
    "expienie": "expareas",
    "teren": "terraininfo", "terrain": "terraininfo", "region": "terraininfo",
    "tereninfo": "terraininfo",
    "sety": "classsets", "setklasowy": "classsets", "setyklasowe": "classsets",
    "say": "say", "powiedz": "say", "mow": "say", "mów": "say",
    "tell": "tell", "msg": "tell", "pm": "tell", "wiadomosc": "tell", "wiadomość": "tell",
    "reply": "reply", "odpisz": "reply", "r": "reply",
    "znajomi": "friends", "znajomy": "friends", "friends": "friends", "friend": "friends",
    "atlas": "atlas", "atlasy": "atlas",
    "codex": "codex", "kodeks": "codex",
    "kodeksklasowy": "classcodex", "kodeks_klasowy": "classcodex",
    "codexklasowy": "classcodex", "klasowycodex": "classcodex",
    "classcodex": "classcodex", "class_codex": "classcodex",
    "skillcodex": "classcodex", "skill_codex": "classcodex",
    "bestiariusz": "bestiary", "bestiary": "bestiary",
    "encyklopedia": "codex", "encyclopedia": "codex",
    "charyzma": "charisma", "haryzma": "charisma", "charisma": "charisma",
    "drużyna": "party", "druzyna": "party", "party": "party",
    "zaproś": "partyinvite", "zapros": "partyinvite", "invite": "partyinvite",
    "dołącz": "partyaccept", "dolacz": "partyaccept",
    "odrzuć": "partydecline", "odrzuc": "partydecline", "decline": "partydecline",
    "opuść": "partyleave", "opusc": "partyleave", "leave": "partyleave",
    "wyrzuć": "partykick", "wyrzuc": "partykick", "kick": "partykick",
    "rozwiąż": "partydisband", "rozwiaz": "partydisband", "disband": "partydisband",
    "lider": "partyleader", "leader": "partyleader",
    "zasłoń": "partyprotect", "zaslon": "partyprotect", "osłoń": "partyprotect", "oslon": "partyprotect", "protect": "partyprotect",
    "wspieraj": "assist", "assist": "assist", "pomagaj": "assist",
    "pc": "partychat", "dczat": "partychat", "partychat": "partychat",
    "multiclass": "multiclass", "multiklasa": "multiclass",
    "multiklas": "multiclass", "klasy": "multiclass",
    "odpoczywaj": "rest", "odpocznij": "rest", "odpoczynek": "rest",
    "rest": "rest", "regen": "rest", "regeneruj": "rest",
    "staty": "stats", "status": "stats",
    "hp": "hp", "health": "hp", "zdrowie": "hp", "zycie": "hp", "życie": "hp",
    "score": "score", "wynik": "score", "postac": "score", "postać": "score",
    "level": "level", "lvl": "level", "poziom": "level",
    "xp": "xp", "exp": "xp",
    "mana": "mana", "manaregen": "mana",
    "odmiana": "declension", "przypadki": "declension", "namecases": "declension", "declension": "declension",
    "skills": "skills", "umiejętności": "skills", "umiejetnosci": "skills", "zdolności": "skills", "zdolnosci": "skills",
    "spells": "spells", "spels": "spells", "spellsy": "spells", "czary": "spells", "zaklecia": "spells", "zaklęcia": "spells",
    "skillnames": "skillnames", "nazwyskilli": "skillnames", "nazwyumiejetnosci": "skillnames", "nazwyumiejętności": "skillnames",
    "skill": "skill", "umiejętność": "skill", "umiejetnosc": "skill", "zdolność": "skill", "zdolnosc": "skill",
    "cast": "skill", "rzuc": "skill", "rzuć": "skill",
    "kolejka": "skillqueue", "queue": "skillqueue", "skillqueue": "skillqueue",
    "kolejkaskilli": "skillqueue", "kolejkaumiejetnosci": "skillqueue", "kolejkaumiejętności": "skillqueue",
    "learn": "learn", "naucz": "learn", "ucz": "learn", "uczsię": "learn", "uczsie": "learn",
    "dusza": "soul", "soul": "soul",
    "portfel": "money", "wallet": "money", "saldo": "money", "pieniadze": "money", "pieniądze": "money",
    "ekwipunek": "inventory", "inv": "inventory", "i": "inventory",
    "załóż": "equip", "zaloz": "equip",
    # v0.30.16 szybkie zakładanie EQ z numerowanej listy slotu.
    "zh": "equiphead", "zz": "equipbody", "zr": "equiphands",
    "zn": "equiplegs", "zb": "equipfeet",
    "zt": "equipcharmauto", "zt1": "equipcharm", "zt2": "equipcharm2",
    "zp": "equipringauto", "zp1": "equipring1", "zp2": "equipring2", "zna": "equipnecklace",
    "zkol": "equipearringauto", "zkol1": "equipearring1", "zkol2": "equipearring2",
    "znar": "equipshoulders", "zpas": "equipbelt", "zpel": "equipcloak",
    "zkar": "equipbracers", "zrel": "equiprelic",
    # v0.30.40 czytelne skróty całego EQ; stare ultra-krótkie aliasy pozostają.
    "zhel": "equiphead", "zhelm": "equiphead", "zhełm": "equiphead",
    "zpan": "equipbody", "zpanc": "equipbody", "zpancerz": "equipbody",
    "zrek": "equiphands", "zrekawice": "equiphands", "zrękawice": "equiphands",
    "znog": "equiplegs", "zbut": "equipfeet",
    "ztal": "equipcharmauto", "zpier": "equipringauto",
    "znasz": "equipnecklace", "znas": "equipnecklace",
    "autoeq": "autoequip", "eqauto": "autoequip", "zauto": "autoequip",
    "zdejmij": "unequip", "zdejm": "unequip", "ściągnij": "unequip", "sciagnij": "unequip", "unequip": "unequip",
    "wyposażenie": "equipment", "wyposazenie": "equipment", "eq": "equipment",
    "przekaż": "giveeq", "przekaz": "giveeq", "daj": "giveeq", "give": "giveeq", "giveeq": "giveeq",
    "użyj": "use", "uzyj": "use", "use": "use",
    "sklep": "shop", "list": "shop", "lista": "shop",
    "kup": "buy",
    "mów": "say", "mow": "say", "powiedz": "say",
    "rozmawiaj": "talk",
    "oddaj": "turnin", "zdaj": "turnin",
    "turnin": "turnin", "turn-in": "turnin",
    "dostarcz": "deliver", "deliver": "deliver",
    "teachers": "teachers", "training": "teachers", "trainers": "teachers", "nauczyciele": "teachers", "trenerzy": "teachers",
    "zadania": "quests", "questy": "quests", "quest": "quests",
    "accept": "questaccept", "akceptuj": "questaccept", "przyjmij": "questaccept",
    "atakuj": "attack", "walcz": "attack", "zabij": "attack", "kill": "attack", "k": "attack",
    "combat": "combatlog", "combatlog": "combatlog", "logwalki": "combatlog", "logwalka": "combatlog",
    "consider": "consider", "con": "consider",
    "ocen": "consider", "oceń": "consider",
    "ocenmob": "consider", "oceńmob": "consider",
    "ciało": "corpse", "cialo": "corpse", "zwłoki": "corpse", "zwloki": "corpse",
    "body": "corpse", "corpse": "corpse",
    "przeszukaj": "lootcorpse", "loot": "lootcorpse", "ograb": "lootcorpse",
    "get": "getcorpseitem", "weź": "getcorpseitem", "wez": "getcorpseitem",
    "krypta": "cryptinfo", "crypt": "cryptinfo",
    "wieza": "astralinfo", "wieża": "astralinfo",
    "astral": "astralinfo", "astralna": "astralinfo",
    "wiezainfo": "astralinfo", "astralinfo": "astralinfo",
    "astralportal": "astralportal",
    "portalastralny": "astralportal",
    "portalwiezy": "astralportal", "portalwieży": "astralportal",
    "checkpointwiezy": "astralportal", "checkpointwieży": "astralportal",
    "portal": "portal", "portale": "portal",
    "portalkrypty": "portal", "portalekrypty": "portal",
    "cryptportal": "portal",
    "checkpoint": "portal", "check": "portal",
    "checkpointkrypty": "portal", "punktkrypty": "portal",
    "punktykrypty": "portal", "cryptcheckpoint": "portal",
    "uciekaj": "flee",
    "odblokuj": "unlock", "odklucz": "unlock", "unlock": "unlock",
    "zapisz": "save", "save": "save",
    "admin": "admin", "administrator": "admin",
    "wipe": "wipe", "wyczysc": "wipe", "wyczyść": "wipe", "wymaz": "wipe",
    "włóż": "put", "wloz": "put", "put": "put",
    "wyjmij": "take", "wyciągnij": "take", "wyciagnij": "take", "take": "take",
    "siatka": "net", "net": "net",
    "woda": "waterinfo", "water": "waterinfo",
    "lowisko": "waterinfo", "łowisko": "waterinfo",
    "dziennikryb": "fishjournal", "dziennik_ryb": "fishjournal",
    "fishjournal": "fishjournal", "fishlog": "fishjournal",
    "sakwa": "bag", "worek": "bag", "bag": "bag",
    "wędkuj": "fish", "wedkuj": "fish", "łów": "fish", "low": "fish",
    # Jedna nawigacja: polskie i angielskie nazwy trafiają do guide.
    "prowadź": "guide", "prowadz": "guide", "guide": "guide",
    "walk": "guide", "walkto": "guide", "go": "guide",
    "idź": "guide", "idz": "guide", "nawiguj": "guide", "navigate": "guide",
    "lokalizacja": "location", "lokacja": "location", "location": "location",
    "kop": "mine", "wydobywaj": "mine",
    "kopalnia": "mineinfo", "mineinfo": "mineinfo",
    "glebokosc": "mineinfo", "głębokość": "mineinfo",
    "tnij": "woodcut", "drwal": "woodcut", "woodcut": "woodcut", "saw": "woodcut",
    "drewno": "woodpile", "stos": "woodpile", "woodpile": "woodpile",
    "zbieraj": "herb", "zbierz": "herb", "zielarstwo": "herb", "herbalism": "herb",
    "zioła": "herbbag", "ziola": "herbbag", "herbs": "herbbag", "herbbag": "herbbag",
    "szkatułka": "craftbox", "szkatulka": "craftbox", "craftbox": "craftbox",
    "materialy": "craftbox", "materiały": "craftbox",
    "rozloz": "salvage", "rozłóż": "salvage", "salvage": "salvage", "recycleeq": "salvage",
    "przekuj": "reforge", "reforge": "reforge",
    "ulepsz": "equpgrade", "ulepszaj": "equpgrade", "upgrade": "equpgrade",
    "upgradeeq": "equpgrade", "ulepszeq": "equpgrade", "ulepsz_eq": "equpgrade",
    "runy": "runes", "runes": "runes", "runa": "socketrune", "socketrune": "socketrune",
    # v0.9.26: system graczy nazywa się Gildia. Stare klan/clan są tylko zgodnościowymi aliasami.
    "gildia": "playerguild", "guild": "playerguild", "guilda": "playerguild",
    "klan": "playerguild", "clan": "playerguild",
    "osiagnieciaklasowe": "masteryachievements", "osiągnięciaklasowe": "masteryachievements",
    "osiagnieciaprofesji": "masteryachievements", "osiągnięciaprofesji": "masteryachievements",
    "masteryachievements": "masteryachievements",
    "alchemia": "alchemy", "alchemy": "alchemy", "warz": "alchemy", "warzenie": "alchemy",
    "jubilerstwo": "jewelcraftinginfo", "jewelcrafting": "jewelcraftinginfo",
    "jub": "jewelcraft", "jubcraft": "jewelcraft",
    "kamienie": "gems", "klejnoty": "gems", "gems": "gems",
    "geody": "geodes", "geodes": "geodes", "geoda": "geodes", "geode": "geodes",
    "opengeode": "geodeopen", "otworzgeode": "geodeopen", "otwórzgeodę": "geodeopen",
    "szlifuj": "cutgem", "oszlifuj": "cutgem", "cutgem": "cutgem",
    "osadz": "socketgem", "osadź": "socketgem", "socket": "socketgem",
    "gniazda": "gemsockets", "sockety": "gemsockets", "sockets": "gemsockets",
    "bizuteria": "jewelcraftinginfo", "biżuteria": "jewelcraftinginfo",
    "sprzedaj": "sell", "sell": "sell",
    "receptury": "recipes", "przepisy": "recipes", "recipes": "recipes",
    "rzemiosło": "recipes", "rzemioslo": "recipes",
    "przetop": "smelt", "przetapiaj": "smelt", "smelt": "smelt",
    "kowalstwo": "blacksmithinginfo",
    "blacksmithing": "blacksmithinginfo",
    "smithing": "blacksmithinginfo",
    "kuj": "craft", "wykuj": "craft",
    "stwórz": "craft", "stworz": "craft", "wytwórz": "craft", "wytworz": "craft", "craft": "craft",
    "gotuj": "cook", "ugotuj": "cook", "cook": "cook",
    "gotowanie": "cookinginfo", "kuchnia": "cookinginfo",
    "cooking": "cookinginfo",
    "profesje": "professions",
    "rangi": "ranks", "ranks": "ranks", "rangiprofesji": "ranks", "professionranks": "ranks",
    "narzędzia": "tools", "narzedzia": "tools",
    "wędka": "toolinfo_fishing", "wedka": "toolinfo_fishing", "rod": "toolinfo_fishing",
    "kilof": "toolinfo_mining", "pickaxe": "toolinfo_mining",
    "piła": "toolinfo_woodcutting", "pila": "toolinfo_woodcutting",
    "młot": "toolinfo_crafting", "mlot": "toolinfo_crafting", "hammer": "toolinfo_crafting",
    "nóż": "toolinfo_cooking", "noz": "toolinfo_cooking", "knife": "toolinfo_cooking",
    "sierp": "toolinfo_herbalism", "sickle": "toolinfo_herbalism",
    "moździerz": "toolinfo_alchemy", "mozdzierz": "toolinfo_alchemy", "mortar": "toolinfo_alchemy",
    "szczypce": "toolinfo_jewelcrafting",
    "szczypcejubilerskie": "toolinfo_jewelcrafting",
    "pliers": "toolinfo_jewelcrafting",
    "tiers": "tiers", "tiery": "tiers", "tiernazwy": "tiers", "nazwytierow": "tiers", "nazwytierów": "tiers",
    # Bezpieczna nawigacja dla gracza niewidomego.
    "cofnij": "dungeonexit", "wstecz": "dungeonexit", "back": "dungeonexit", "return": "dungeonexit",
    "wyjście": "dungeonexit", "wyjscie": "dungeonexit",
    "wyjdź": "dungeonexit", "wyjdz": "dungeonexit",
    "exit": "dungeonexit", "dungeonexit": "dungeonexit",
    "escape": "dungeonexit",

    # Jednoznaczne wylogowanie po zmianie znaczenia słowa wyjście.
    "wyloguj": "quit", "koniec": "quit", "logout": "quit",
    "quitgame": "quit", "quit": "quit",

    # Popularne angielskie odpowiedniki brakujące wcześniej.
    "areas": "expareas", "grindingareas": "expareas",
    "levelingareas": "expareas", "levelareas": "expareas",
    "terraininfo": "terraininfo", "regioninfo": "terraininfo",
    "areainfo": "terraininfo",
    "sets": "classsets", "set": "classsets",
    "classset": "classsets", "classsets": "classsets",
    "profession": "professions", "professions": "professions",
    "tool": "tools", "tools": "tools",
    "questlog": "quests", "quests": "quests",
    "trainers": "teachers", "teachers": "teachers",
    "woodcutting": "woodcut", "chop": "woodcut",
    "gather": "herb", "gatherherbs": "herb",
    "jewelry": "jewelcraftinginfo", "jewellery": "jewelcraftinginfo",
    "gildiaklasowa": "classguild", "gildia_klasowa": "classguild", "classguild": "classguild",
    "reputacja": "classguild", "reputation": "classguild",
    "zadanieklasowe": "guildquest",
    "classquest": "guildquest",
    "egzamin": "guildexam",
    "exam": "guildexam",
    "bounty": "bounty",
    "zlecenie": "bounty",
    "zlecenia": "bounty",
    "contracts": "bounty",
    "kontrakty": "bounty",
    "contract": "bounty",
    "tablicazlecen": "bounty",
    "tablica_zlecen": "bounty",
    "guildbounty": "guildbounty",
    "zleceniagildii": "guildbounty",
    "zleceniegildii": "guildbounty",
    "skrzynia": "chest",
    "skarb": "chest",
    "chest": "chest",
    "treasure": "chest",
    "otworz": "chest",
    "otwórz": "chest",
    "open": "chest",
    "otworzskrzynie": "chest",
    "otwórzskrzynię": "chest",

}

ITEMS = {
    "healing_potion": {
        "name": "Mikstura leczenia", "type": "consumable", "price": 24, "currency": "silver",
        "desc": "Przywraca 35 punktów życia podczas walki.", "heal": 35,
    },
    "soul_elixir": {
        "name": "Eliksir Duszy", "type": "consumable", "price": None,
        "desc": "Daje 80 Soul XP.", "soul_xp": 80,
    },
    "leather_vest": {
        "name": "Skórzana kamizelka", "type": "armor", "slot": "body", "defense": 2,
        "price": 48, "currency": "silver", "desc": "Lekki pancerz. Obrona +2.",
    },
    "iron_helmet": {
        "name": "Żelazny hełm", "type": "armor", "slot": "head", "defense": 2,
        "price": 90, "currency": "silver",
        "desc": "Hełm kowalskiego zestawu. Slot głowa. Obrona fizyczna +2.",
    },
    "iron_guard": {
        "name": "Żelazny napierśnik", "type": "armor", "slot": "body", "defense": 4,
        "price": 180, "currency": "silver",
        "desc": "Główna część kowalskiego zestawu. Slot korpus. Obrona fizyczna +4.",
    },
    "iron_gauntlets": {
        "name": "Żelazne rękawice", "type": "armor", "slot": "hands", "defense": 1,
        "price": 70, "currency": "silver",
        "desc": "Rękawice kowalskiego zestawu. Slot dłonie. Obrona fizyczna +1.",
    },
    "iron_leggings": {
        "name": "Żelazne nogawice", "type": "armor", "slot": "legs", "defense": 3,
        "price": 130, "currency": "silver",
        "desc": "Osłona nóg kowalskiego zestawu. Slot nogi. Obrona fizyczna +3.",
    },
    "iron_boots": {
        "name": "Żelazne buty", "type": "armor", "slot": "feet", "defense": 1,
        "price": 70, "currency": "silver",
        "desc": "Buty kowalskiego zestawu. Slot stopy. Obrona fizyczna +1.",
    },
    "forge_charm": {
        "name": "Talizman Kowala", "type": "armor", "slot": "charm", "defense": 1,
        "price": 110, "currency": "silver",
        "desc": "Hartowany talizman ochronny. Slot talizman. Obrona fizyczna +1.",
    },
    "lucky_charm": {
        "name": "Talizman Wędrowca", "type": "armor", "slot": "charm", "defense": 1,
        "price": 72, "currency": "silver", "desc": "Drobny talizman. Obrona +1.",
    },
    "fishing_rod": {
        "name": "Wędka", "type": "tool", "tool_type": "fishing",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Wędkarstwa. Ma własny level 1-400 i 40 Tierów.",
    },
    "pickaxe": {
        "name": "Kilof", "type": "tool", "tool_type": "mining",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Górnictwa. Ma własny level 1-400 i 40 Tierów.",
    },
    "saw": {
        "name": "Piła", "type": "tool", "tool_type": "woodcutting",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Drwalstwa. Ma własny level 1-400 i 40 Tierów.",
    },
    "crafting_hammer": {
        "name": "Młot Rzemieślniczy", "type": "tool", "tool_type": "crafting",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Rzemiosła. Ma własny level 1-400, XP i 40 Tierów.",
    },
    "chef_knife": {
        "name": "Nóż Kucharski", "type": "tool", "tool_type": "cooking",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Gotowania. Ma własny level 1-400, XP i 40 Tierów.",
    },
    "herbalist_sickle": {
        "name": "Sierp Zielarski", "type": "tool", "tool_type": "herbalism",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Zielarstwa. Ma własny level 1-400, XP i 40 Tierów.",
    },
    "alchemy_mortar": {
        "name": "Moździerz Alchemiczny", "type": "tool", "tool_type": "alchemy",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Alchemii. Ma własny level 1-400, XP i 40 Tierów.",
    },
    "nettle": {"name": "Pokrzywa", "type": "resource", "price": None, "sell_silver": 5, "desc": "Pospolite zioło lecznicze."},
    "chamomile": {"name": "Rumianek", "type": "resource", "price": None, "sell_silver": 7, "desc": "Łagodne zioło lecznicze."},
    "mint": {"name": "Mięta", "type": "resource", "price": None, "sell_silver": 8, "desc": "Aromatyczne zioło."},
    "sage": {"name": "Szałwia", "type": "resource", "price": None, "sell_silver": 12, "desc": "Silne zioło alchemiczne."},
    "lavender": {"name": "Lawenda", "type": "resource", "price": None, "sell_silver": 14, "desc": "Pachnące zioło."},
    "yarrow": {"name": "Krwawnik", "type": "resource", "price": None, "sell_silver": 16, "desc": "Zioło lecznicze."},
    "lemon_balm": {"name": "Melisa", "type": "resource", "price": None, "sell_silver": 18, "desc": "Zioło przydatne w miksturach Many."},
    "valerian": {"name": "Kozłek", "type": "resource", "price": None, "sell_silver": 25, "desc": "Leśne zioło."},
    "ginseng": {"name": "Żeń-szeń", "type": "resource", "price": None, "sell_silver": 40, "desc": "Cenny korzeń alchemiczny."},
    "nightshade": {"name": "Wilcza jagoda", "type": "resource", "price": None, "sell_silver": 55, "desc": "Rzadkie zioło alchemiczne."},
    "mandrake": {"name": "Mandragora", "type": "resource", "price": None, "sell_gold": 1, "desc": "Rzadki magiczny korzeń."},
    "moonflower": {"name": "Kwiat księżycowy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Magiczny kwiat."},
    "soulroot": {"name": "Korzeń duszy", "type": "resource", "price": None, "sell_gold": 3, "desc": "Korzeń nasycony energią dusz."},
    "phoenix_leaf": {"name": "Liść feniksa", "type": "resource", "price": None, "sell_gold": 5, "desc": "Bardzo rzadki liść."},
    "star_moss": {"name": "Gwiezdny mech", "type": "resource", "price": None, "sell_gold": 8, "desc": "Rzadki magiczny mech."},
    "astral_lotus": {"name": "Astralny lotos", "type": "resource", "price": None, "sell_gold": 15, "desc": "Mityczne zioło."},
    "mana_potion": {"name": "Mikstura Many", "type": "consumable", "price": None, "mana": 35, "desc": "Przywraca do 35 Many."},
    "greater_healing_potion": {"name": "Wielka Mikstura Leczenia", "type": "consumable", "price": None, "heal": 70, "desc": "Przywraca do 70 HP."},
    "greater_mana_potion": {"name": "Wielka Mikstura Many", "type": "consumable", "price": None, "mana": 70, "desc": "Przywraca do 70 Many."},
    "vitality_elixir": {"name": "Eliksir Witalności", "type": "consumable", "price": None, "heal": 55, "mana": 30, "desc": "Przywraca do 55 HP i 30 Many."},
    "fallen_branch": {"name": "Suche gałęzie", "type": "resource", "price": None, "sell_silver": 6, "desc": "Najprostszy materiał drwala."},
    "birch_log": {"name": "Pień brzozy", "type": "resource", "price": None, "sell_silver": 10, "desc": "Lekkie drewno brzozowe."},
    "pine_log": {"name": "Pień sosny", "type": "resource", "price": None, "sell_silver": 15, "desc": "Pospolite drewno sosnowe."},
    "willow_log": {"name": "Pień wierzby", "type": "resource", "price": None, "sell_silver": 22, "desc": "Miękkie drewno wierzby."},
    "oak_log": {"name": "Pień dębu", "type": "resource", "price": None, "sell_silver": 40, "desc": "Twarde drewno dębowe."},
    "beech_log": {"name": "Pień buku", "type": "resource", "price": None, "sell_silver": 55, "desc": "Mocne drewno bukowe."},
    "maple_log": {"name": "Pień klonu", "type": "resource", "price": None, "sell_silver": 70, "desc": "Cenne drewno klonowe."},
    "ash_log": {"name": "Pień jesionu", "type": "resource", "price": None, "sell_silver": 90, "desc": "Sprężyste drewno jesionowe."},
    "cedar_log": {"name": "Pień cedru", "type": "resource", "price": None, "sell_silver": 130, "desc": "Aromatyczne drewno cedrowe."},
    "yew_log": {"name": "Pień cisu", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadkie drewno cisu."},
    "ironwood_log": {"name": "Pień żelaznego drzewa", "type": "resource", "price": None, "sell_gold": 5, "desc": "Niezwykle twarde drewno."},
    "ebony_log": {"name": "Pień hebanu", "type": "resource", "price": None, "sell_gold": 8, "desc": "Ciężkie i bardzo cenne drewno."},
    "silverwood_log": {"name": "Pień srebrnego drzewa", "type": "resource", "price": None, "sell_gold": 10, "desc": "Magiczne srebrzyste drewno."},
    "spiritwood_log": {"name": "Pień drzewa duchów", "type": "resource", "price": None, "sell_gold": 15, "desc": "Drewno nasycone energią dusz."},
    "ancient_heartwood": {"name": "Pradawna twardziel", "type": "resource", "price": None, "sell_gold": 30, "desc": "Rdzeń bardzo starego drzewa."},
    "worldtree_wood": {"name": "Drewno Drzewa Świata", "type": "resource", "price": None, "sell_gold": 75, "desc": "Mityczny materiał dla najlepszych drwali."},
    "iron_ingot": {
        "name": "Żelazna sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione żelazo używane w recepturach rzemieślniczych.",
    },
    "silver_ingot": {
        "name": "Srebrna sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione srebro używane w lepszych recepturach.",
    },
    "gold_ingot": {
        "name": "Złota sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione złoto używane w zaawansowanych recepturach.",
    },
    "oak_plank": {
        "name": "Deska dębowa", "type": "craft_material", "price": None,
        "desc": "Obrobiona deska z drewna dębowego.",
    },
    "ash_plank": {
        "name": "Deska jesionowa", "type": "craft_material", "price": None,
        "desc": "Sprężysta deska jesionowa.",
    },
    "yew_plank": {
        "name": "Deska cisowa", "type": "craft_material", "price": None,
        "desc": "Rzadka deska z drewna cisu.",
    },
    "ironwood_plank": {
        "name": "Deska żelaznego drzewa", "type": "craft_material", "price": None,
        "desc": "Bardzo twarda deska z żelaznego drzewa.",
    },
    "spiritwood_plank": {
        "name": "Deska drzewa duchów", "type": "craft_material", "price": None,
        "desc": "Magiczna deska nasycona energią dusz.",
    },
    "oak_iron_charm": {
        "name": "Talizman Dębu i Żelaza", "type": "armor", "slot": "charm",
        "defense": 2, "price": None,
        "desc": "Wytwarzany talizman. Slot talizman. Obrona fizyczna +2.",
    },
    "yew_silver_charm": {
        "name": "Talizman Cisu i Srebra", "type": "armor", "slot": "charm",
        "defense": 3, "price": None,
        "desc": "Rzadki wytwarzany talizman. Slot talizman. Obrona fizyczna +3.",
    },
    "spiritwood_gold_charm": {
        "name": "Talizman Drzewa Dusz", "type": "armor", "slot": "charm",
        "defense": 5, "price": None,
        "desc": "Zaawansowany talizman z magicznego drewna i złota. Obrona fizyczna +5.",
    },
    "grilled_river_fish": {
        "name": "Pieczona ryba rzeczna", "type": "consumable", "price": None,
        "heal": 30,
        "desc": "Prosta potrawa. Przywraca do 30 HP.",
    },
    "river_fish_stew": {
        "name": "Gulasz rzeczny", "type": "consumable", "price": None,
        "heal": 45,
        "desc": "Syta potrawa z ryb rzecznych. Przywraca do 45 HP.",
    },
    "lake_fish_stew": {
        "name": "Potrawka jeziorowa", "type": "consumable", "price": None,
        "heal": 50, "mana": 10,
        "desc": "Potrawa z ryb jeziorowych. Przywraca do 50 HP i 10 Many.",
    },
    "sea_chowder": {
        "name": "Zupa morska", "type": "consumable", "price": None,
        "heal": 60, "mana": 15,
        "desc": "Gęsta zupa morska. Przywraca do 60 HP i 15 Many.",
    },
    "ocean_steak": {
        "name": "Stek oceaniczny", "type": "consumable", "price": None,
        "heal": 75, "mana": 25,
        "desc": "Potężna potrawa z ryb oceanu. Przywraca do 75 HP i 25 Many.",
    },
    "master_fisher_feast": {
        "name": "Uczta Mistrza Rybaka", "type": "consumable", "price": None,
        "heal": 100, "mana": 40,
        "desc": "Wielka uczta z czterech środowisk. Przywraca do 100 HP i 40 Many.",
    },

    "herb_crusted_perch": {
        "name": "Okoń w Ziołowej Skorupce",
        "type": "consumable",
        "price": None,
        "heal": 42,
        "mana": 5,
        "desc": "Lekka potrawa rybna z Miętą. Przywraca do 42 HP i 5 Many.",
    },
    "silver_trout_soup": {
        "name": "Zupa ze Srebrnego Pstrąga",
        "type": "consumable",
        "price": None,
        "heal": 52,
        "mana": 12,
        "desc": "Gorąca zupa z pstrąga i Szałwii. Przywraca do 52 HP i 12 Many.",
    },
    "lake_fisher_pie": {
        "name": "Zapiekanka Jeziornego Rybaka",
        "type": "consumable",
        "price": None,
        "heal": 62,
        "mana": 18,
        "desc": "Treściwa zapiekanka z ryb jeziorowych. Przywraca do 62 HP i 18 Many.",
    },
    "spiced_mackerel": {
        "name": "Makrela Korzenna",
        "type": "consumable",
        "price": None,
        "heal": 72,
        "mana": 22,
        "desc": "Makrela doprawiona Szałwią. Przywraca do 72 HP i 22 Many.",
    },
    "salmon_herb_plate": {
        "name": "Łosoś z Ziołami",
        "type": "consumable",
        "price": None,
        "heal": 88,
        "mana": 30,
        "desc": "Łosoś z Lawendą. Przywraca do 88 HP i 30 Many.",
    },
    "moon_eel_broth": {
        "name": "Rosół z Księżycowego Węgorza",
        "type": "consumable",
        "price": None,
        "heal": 112,
        "mana": 48,
        "desc": "Rzadka potrawa z Księżycowego Węgorza i Kwiatu księżycowego. Przywraca do 112 HP i 48 Many.",
    },

    # Nowe ryby v0.6.98 - rzeka
    "river_bleak": {"name": "Ukleja Rzeczna", "type": "resource", "price": None, "sell_silver": 4, "desc": "Mała rzeczna ryba. Wędka level 1+."},
    "stone_loach": {"name": "Śliz Kamienny", "type": "resource", "price": None, "sell_silver": 6, "desc": "Niewielka ryba denna rzeki. Wędka level 5+."},
    "river_bream": {"name": "Krąp Rzeczny", "type": "resource", "price": None, "sell_silver": 10, "desc": "Pospolita ryba rzeczna. Wędka level 15+."},
    "brown_trout": {"name": "Pstrąg Potokowy", "type": "resource", "price": None, "sell_silver": 18, "desc": "Szybka ryba czystych rzek. Wędka level 30+."},
    "river_taimen": {"name": "Tajmień Rzeczny", "type": "resource", "price": None, "sell_silver": 34, "desc": "Duży drapieżnik rzeczny. Wędka level 50+."},
    "emerald_barbel": {"name": "Szmaragdowa Brzana", "type": "resource", "price": None, "sell_silver": 60, "desc": "Rzadka brzana o zielonym połysku. Wędka level 75+."},
    "spirit_grayling": {"name": "Lipień Duchów", "type": "resource", "price": None, "sell_gold": 2, "desc": "Magiczny lipień. Wędka level 110+."},
    "bloodfin_salmon": {"name": "Krwawopłetwy Łosoś", "type": "resource", "price": None, "sell_gold": 5, "desc": "Rzadki łosoś endgame. Wędka level 150+."},
    "star_river_eel": {"name": "Gwiezdny Węgorz Rzeczny", "type": "resource", "price": None, "sell_gold": 12, "desc": "Węgorz nasycony energią gwiazd. Wędka level 175+."},
    "eternal_river_dragon": {"name": "Wieczny Smok Rzeczny", "type": "resource", "price": None, "sell_gold": 35, "desc": "Legendarny drapieżnik rzeki. Wędka level 200."},

    # Nowe ryby v0.6.98 - jezioro
    "lake_gudgeon": {"name": "Kiełb Jeziorowy", "type": "resource", "price": None, "sell_silver": 5, "desc": "Mała ryba przybrzeżna jeziora. Wędka level 1+."},
    "lake_smelt": {"name": "Stynka Jeziorowa", "type": "resource", "price": None, "sell_silver": 7, "desc": "Drobna srebrzysta ryba jeziorowa. Wędka level 8+."},
    "blue_bream": {"name": "Niebieski Leszcz", "type": "resource", "price": None, "sell_silver": 12, "desc": "Rzadziej spotykany leszcz. Wędka level 20+."},
    "golden_tench": {"name": "Złoty Lin", "type": "resource", "price": None, "sell_silver": 22, "desc": "Cenny lin jeziorowy. Wędka level 35+."},
    "deepwater_pike": {"name": "Szczupak Głębinowy", "type": "resource", "price": None, "sell_silver": 40, "desc": "Duży szczupak z głębokich partii jeziora. Wędka level 55+."},
    "crystal_whitefish": {"name": "Kryształowa Sieja", "type": "resource", "price": None, "sell_silver": 70, "desc": "Jasna magiczna sieja. Wędka level 80+."},
    "moon_carp": {"name": "Karp Księżycowy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Karp aktywny przy blasku księżyca. Wędka level 110+."},
    "astral_pike": {"name": "Astralny Szczupak", "type": "resource", "price": None, "sell_gold": 6, "desc": "Endgame drapieżnik jeziorowy. Wędka level 150+."},
    "mirror_sturgeon": {"name": "Lustrzany Jesiotr", "type": "resource", "price": None, "sell_gold": 14, "desc": "Rzadki jesiotr z lustrzanymi łuskami. Wędka level 175+."},
    "eternal_lake_serpent": {"name": "Wieczny Wąż Jeziora", "type": "resource", "price": None, "sell_gold": 38, "desc": "Legendarny mieszkaniec najgłębszej toni. Wędka level 200."},

    # Nowe ryby v0.6.98 - morze
    "sand_eel": {"name": "Dobijak Piaskowy", "type": "resource", "price": None, "sell_silver": 5, "desc": "Mała ryba przybrzeżna morza. Wędka level 1+."},
    "garfish": {"name": "Belona", "type": "resource", "price": None, "sell_silver": 8, "desc": "Długa ryba morska. Wędka level 10+."},
    "sea_bream": {"name": "Prażma Morska", "type": "resource", "price": None, "sell_silver": 14, "desc": "Smaczna ryba morska. Wędka level 20+."},
    "bluefish": {"name": "Lufar", "type": "resource", "price": None, "sell_silver": 25, "desc": "Waleczny morski drapieżnik. Wędka level 35+."},
    "conger_eel": {"name": "Konger", "type": "resource", "price": None, "sell_silver": 45, "desc": "Duży węgorz morski. Wędka level 55+."},
    "red_snapper": {"name": "Lucjan Czerwony", "type": "resource", "price": None, "sell_silver": 80, "desc": "Cenna ryba morska. Wędka level 80+."},
    "storm_herring": {"name": "Śledź Burzy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Ryba pojawiająca się przy wzburzonym morzu. Wędka level 110+."},
    "abyss_conger": {"name": "Konger Otchłani", "type": "resource", "price": None, "sell_gold": 7, "desc": "Mroczny endgame węgorz morski. Wędka level 150+."},
    "void_sole": {"name": "Sola Pustki", "type": "resource", "price": None, "sell_gold": 15, "desc": "Rzadka płastuga nasycona Pustką. Wędka level 175+."},
    "eternal_sea_drake": {"name": "Wieczny Smok Morza", "type": "resource", "price": None, "sell_gold": 40, "desc": "Legendarny morski drapieżnik. Wędka level 200."},

    # Nowe ryby v0.6.98 - ocean
    "flying_fish": {"name": "Ryba Latająca", "type": "resource", "price": None, "sell_silver": 8, "desc": "Szybka ryba otwartego oceanu. Wędka level 1+."},
    "bonito": {"name": "Bonito", "type": "resource", "price": None, "sell_silver": 12, "desc": "Mały krewniak tuńczyka. Wędka level 15+."},
    "yellowfin_tuna": {"name": "Tuńczyk Żółtopłetwy", "type": "resource", "price": None, "sell_silver": 24, "desc": "Popularny oceaniczny tuńczyk. Wędka level 30+."},
    "king_mackerel": {"name": "Makrela Królewska", "type": "resource", "price": None, "sell_silver": 42, "desc": "Duża makrela otwartego oceanu. Wędka level 50+."},
    "marlin_black": {"name": "Marlin Czarny", "type": "resource", "price": None, "sell_silver": 78, "desc": "Potężny oceaniczny drapieżnik. Wędka level 70+."},
    "opah": {"name": "Strojnik Oceaniczny", "type": "resource", "price": None, "sell_gold": 1, "desc": "Rzadka głębinowa ryba oceanu. Wędka level 90+."},
    "celestial_swordfish": {"name": "Niebiański Miecznik", "type": "resource", "price": None, "sell_gold": 4, "desc": "Magiczny miecznik endgame. Wędka level 120+."},
    "astral_sunfish": {"name": "Astralny Samogłów", "type": "resource", "price": None, "sell_gold": 9, "desc": "Ogromny samogłów nasycony Astralem. Wędka level 150+."},
    "void_marlin": {"name": "Marlin Pustki", "type": "resource", "price": None, "sell_gold": 18, "desc": "Skrajnie rzadka ryba oceaniczna. Wędka level 180+."},
    "world_leviathan": {"name": "Lewiatan Świata", "type": "resource", "price": None, "sell_gold": 50, "desc": "Legendarny szczyt oceanicznego połowu. Wędka level 200."},

    "small_fish": {
        "name": "Mała ryba", "type": "resource", "price": None,
        "desc": "Pospolity połów z płytkiej wody.", "sell_silver": 8,
    },
    "river_carp": {
        "name": "Karp rzeczny", "type": "resource", "price": None,
        "desc": "Solidna ryba rzeczna.", "sell_silver": 20,
    },
    "silver_trout": {
        "name": "Srebrny pstrąg", "type": "resource", "price": None,
        "desc": "Rzadsza ryba o srebrzystych łuskach.", "sell_silver": 55,
    },
    "golden_trout": {
        "name": "Złoty pstrąg", "type": "resource", "price": None,
        "desc": "Cenny połów dostępny przy lepszej wędce.", "sell_gold": 1,
    },
    "ancient_sturgeon": {
        "name": "Pradawny jesiotr", "type": "resource", "price": None,
        "desc": "Bardzo duża i cenna ryba.", "sell_gold": 3,
    },
    "moon_eel": {
        "name": "Księżycowy węgorz", "type": "resource", "price": None,
        "desc": "Niezwykle rzadki połów z wysokiego poziomu Wędkarstwa.", "sell_gold": 8,
    },
    "herring": {
        "name": "Śledź", "type": "resource", "price": None,
        "desc": "Morska ryba dostępna dopiero od levelu 30 Wędki.", "sell_gold": 1,
    },
    "mackerel": {
        "name": "Makrela", "type": "resource", "price": None,
        "desc": "Szybka ryba morska.", "sell_gold": 2,
    },
    "salmon": {
        "name": "Łosoś", "type": "resource", "price": None,
        "desc": "Cenny połów z rozwiniętego Wędkarstwa.", "sell_gold": 5,
    },
    "tuna": {
        "name": "Tuńczyk", "type": "resource", "price": None,
        "desc": "Duży i cenny połów oceaniczny. Wędka level 80+.",
        "sell_gold": 15,
    },
    "swordfish": {
        "name": "Miecznik", "type": "resource", "price": None,
        "desc": "Rzadki i silny morski okaz.", "sell_gold": 30,
    },
    "bluefin_tuna": {
        "name": "Tuńczyk błękitnopłetwy", "type": "resource", "price": None,
        "desc": "Bardzo rzadki tuńczyk dostępny na wysokim levelu Wędki.", "sell_gold": 75,
    },
    "reef_shark": {
        "name": "Rekin rafowy", "type": "resource", "price": None,
        "desc": "Rzadki rekin możliwy do złowienia dopiero bardzo dobrą Wędką.", "sell_gold": 125,
    },
    "hammerhead_shark": {
        "name": "Rekin młot", "type": "resource", "price": None,
        "desc": "Bardzo rzadki rekin dla mistrzów Wędkarstwa.", "sell_gold": 250,
    },
    "great_white_shark": {
        "name": "Żarłacz biały", "type": "resource", "price": None,
        "desc": "Ekstremalnie rzadki okaz dla najwyższych leveli Wędki.", "sell_gold": 500,
    },
    "ghost_marlin": {
        "name": "Widmowy marlin", "type": "resource", "price": None,
        "desc": "Legendarny połów dostępny jedynie mistrzom Wędkarstwa.", "sell_mithril": 1,
    },
    "sardine": {
        "name": "Sardynka", "type": "resource", "price": None,
        "desc": "Niewielka morska ryba ławicowa.", "sell_silver": 35,
    },
    "anchovy": {
        "name": "Sardela", "type": "resource", "price": None,
        "desc": "Mała ryba morska spotykana w dużych ławicach.", "sell_silver": 45,
    },
    "cod": {
        "name": "Dorsz", "type": "resource", "price": None,
        "desc": "Cenna ryba morska o jasnym mięsie.", "sell_gold": 3,
    },
    "sea_bass": {
        "name": "Labraks", "type": "resource", "price": None,
        "desc": "Drapieżna ryba morska ceniona przez kupców.", "sell_gold": 4,
    },
    "haddock": {
        "name": "Plamiak", "type": "resource", "price": None,
        "desc": "Krewniak dorsza, trudniejszy do złowienia.", "sell_gold": 6,
    },
    "pollock": {
        "name": "Mintaj", "type": "resource", "price": None,
        "desc": "Silna ryba morska z chłodnych wód.", "sell_gold": 8,
    },
    "flounder": {
        "name": "Flądra", "type": "resource", "price": None,
        "desc": "Płaska ryba denna wymagająca lepszej Wędki.", "sell_gold": 10,
    },
    "halibut": {
        "name": "Halibut", "type": "resource", "price": None,
        "desc": "Duża i droga ryba denna.", "sell_gold": 20,
    },
    "river_perch": {"name": "Okoń rzeczny", "type": "resource", "price": None, "sell_silver": 14, "desc": "Pospolity drapieżnik rzeczny."},
    "barbel": {"name": "Brzana", "type": "resource", "price": None, "sell_silver": 25, "desc": "Silna ryba nurtu rzecznego."},
    "pike": {"name": "Szczupak", "type": "resource", "price": None, "sell_silver": 60, "desc": "Duży słodkowodny drapieżnik."},
    "zander": {"name": "Sandacz", "type": "resource", "price": None, "sell_silver": 85, "desc": "Cenny drapieżnik słodkowodny."},
    "river_catfish": {"name": "Sum rzeczny", "type": "resource", "price": None, "sell_gold": 3, "desc": "Wielki mieszkaniec głębokiej rzeki."},
    "lake_roach": {"name": "Płoć jeziorowa", "type": "resource", "price": None, "sell_silver": 10, "desc": "Pospolita ryba jeziorowa."},
    "bream": {"name": "Leszcz", "type": "resource", "price": None, "sell_silver": 20, "desc": "Popularna ryba jezior."},
    "tench": {"name": "Lin", "type": "resource", "price": None, "sell_silver": 35, "desc": "Ryba spokojnych, zarośniętych jezior."},
    "lake_perch": {"name": "Okoń jeziorowy", "type": "resource", "price": None, "sell_silver": 45, "desc": "Drapieżnik jeziorowy."},
    "lake_trout": {"name": "Troć jeziorowa", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadka duża ryba chłodnych jezior."},
    "giant_pike": {"name": "Olbrzymi szczupak", "type": "resource", "price": None, "sell_gold": 6, "desc": "Bardzo stary szczupak."},
    "freshwater_eel": {"name": "Węgorz jeziorowy", "type": "resource", "price": None, "sell_gold": 8, "desc": "Rzadki węgorz z głębin jeziora."},
    "turbot": {"name": "Turbot", "type": "resource", "price": None, "sell_gold": 6, "desc": "Cenna ryba denna morza."},
    "mahi_mahi": {"name": "Mahi-mahi", "type": "resource", "price": None, "sell_gold": 10, "desc": "Szybka ryba oceaniczna."},
    "wahoo": {"name": "Wahoo", "type": "resource", "price": None, "sell_gold": 15, "desc": "Bardzo szybki drapieżnik oceanu."},
    "sailfish": {"name": "Żaglica", "type": "resource", "price": None, "sell_gold": 25, "desc": "Ekstremalnie szybka ryba oceaniczna."},
    "ocean_sunfish": {"name": "Samogłów oceaniczny", "type": "resource", "price": None, "sell_gold": 40, "desc": "Ogromna ryba otwartego oceanu."},
    # Dodatkowe ryby rzeczne
    "dace": {"name": "Jelec", "type": "resource", "price": None, "sell_silver": 12, "desc": "Mała szybka ryba rzeczna."},
    "chub": {"name": "Kleń", "type": "resource", "price": None, "sell_silver": 18, "desc": "Pospolita, silna ryba rzeczna."},
    "common_nase": {"name": "Świnka", "type": "resource", "price": None, "sell_silver": 22, "desc": "Ryba czystych, płynących wód."},
    "ide": {"name": "Jaź", "type": "resource", "price": None, "sell_silver": 32, "desc": "Cenna ryba większych rzek."},
    "asp": {"name": "Boleń", "type": "resource", "price": None, "sell_silver": 70, "desc": "Szybki drapieżnik rzeczny."},
    "grayling": {"name": "Lipień", "type": "resource", "price": None, "sell_silver": 90, "desc": "Cenna ryba chłodnych rzek."},
    "burbot": {"name": "Miętus", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadki denny drapieżnik rzeczny."},

    # Dodatkowe ryby jeziorowe
    "rudd": {"name": "Wzdręga", "type": "resource", "price": None, "sell_silver": 14, "desc": "Kolorowa ryba spokojnych jezior."},
    "crucian_carp": {"name": "Karaś", "type": "resource", "price": None, "sell_silver": 18, "desc": "Wytrzymała ryba jeziorowa."},
    "vendace": {"name": "Sielawa", "type": "resource", "price": None, "sell_silver": 55, "desc": "Ryba chłodnych, czystych jezior."},
    "whitefish": {"name": "Sieja", "type": "resource", "price": None, "sell_gold": 1, "desc": "Cenna ryba głębokich jezior."},
    "lake_char": {"name": "Palia jeziorowa", "type": "resource", "price": None, "sell_gold": 3, "desc": "Rzadki drapieżnik zimnych jezior."},

    # Dodatkowe ryby morskie
    "sprat": {"name": "Szprot", "type": "resource", "price": None, "sell_silver": 8, "desc": "Mała ryba morska żyjąca w ławicach."},
    "whiting": {"name": "Witlinek", "type": "resource", "price": None, "sell_silver": 32, "desc": "Pospolita ryba morska."},
    "hake": {"name": "Morszczuk", "type": "resource", "price": None, "sell_silver": 85, "desc": "Drapieżna ryba morska."},
    "red_mullet": {"name": "Barwena", "type": "resource", "price": None, "sell_gold": 2, "desc": "Cenna morska ryba przydenna."},
    "sole": {"name": "Sola", "type": "resource", "price": None, "sell_gold": 4, "desc": "Cenna płaska ryba morska."},
    "monkfish": {"name": "Żabnica", "type": "resource", "price": None, "sell_gold": 9, "desc": "Duży morski drapieżnik głębinowy."},

    # Dodatkowe ryby oceaniczne
    "albacore": {"name": "Albakora", "type": "resource", "price": None, "sell_gold": 12, "desc": "Oceaniczny gatunek tuńczyka."},
    "bigeye_tuna": {"name": "Tuńczyk wielkooki", "type": "resource", "price": None, "sell_gold": 20, "desc": "Cenny tuńczyk głębokiego oceanu."},
    "barracuda": {"name": "Barakuda", "type": "resource", "price": None, "sell_gold": 18, "desc": "Szybki oceaniczny drapieżnik."},
    "cobia": {"name": "Kobia", "type": "resource", "price": None, "sell_gold": 22, "desc": "Duża ryba otwartego morza i oceanu."},
    "amberjack": {"name": "Seriola", "type": "resource", "price": None, "sell_gold": 28, "desc": "Silna oceaniczna ryba sportowa."},
    "mako_shark": {"name": "Rekin mako", "type": "resource", "price": None, "sell_gold": 180, "desc": "Bardzo szybki i rzadki rekin oceaniczny."},
    "tiger_shark": {"name": "Rekin tygrysi", "type": "resource", "price": None, "sell_gold": 300, "desc": "Wielki, bardzo rzadki drapieżnik oceaniczny."},

    # Dodatkowe gatunki drewna
    "alder_log": {"name": "Pień olchy", "type": "resource", "price": None, "sell_silver": 12, "desc": "Drewno lubiące wilgotne tereny."},
    "poplar_log": {"name": "Pień topoli", "type": "resource", "price": None, "sell_silver": 18, "desc": "Lekkie i łatwe w obróbce drewno."},
    "linden_log": {"name": "Pień lipy", "type": "resource", "price": None, "sell_silver": 28, "desc": "Miękkie drewno cenione przez rzemieślników."},
    "chestnut_log": {"name": "Pień kasztana", "type": "resource", "price": None, "sell_silver": 110, "desc": "Twarde, trwałe drewno."},
    "walnut_log": {"name": "Pień orzecha", "type": "resource", "price": None, "sell_gold": 2, "desc": "Cenne ciemne drewno orzechowe."},
    "mahogany_log": {"name": "Pień mahoniu", "type": "resource", "price": None, "sell_gold": 6, "desc": "Szlachetne, ciemnoczerwone drewno."},
    "teak_log": {"name": "Pień teku", "type": "resource", "price": None, "sell_gold": 9, "desc": "Bardzo trwałe i odporne drewno."},
    "redwood_log": {"name": "Pień sekwoi", "type": "resource", "price": None, "sell_gold": 18, "desc": "Ogromne i rzadkie drewno ze starych drzew."},

    "stone_chunk": {
        "name": "Odłamek skały", "type": "resource", "price": None,
        "desc": "Pospolity urobek.", "sell_silver": 3,
    },
    "copper_ore": {
        "name": "Ruda miedzi", "type": "resource", "price": None,
        "desc": "Podstawowa ruda górnicza.", "sell_silver": 12,
    },
    "iron_ore": {
        "name": "Ruda żelaza", "type": "resource", "price": None,
        "desc": "Użyteczna ruda metalu.", "sell_silver": 35,
    },
    "silver_ore": {
        "name": "Ruda srebra", "type": "resource", "price": None,
        "desc": "Cenniejsza ruda wydobywana lepszym kilofem.", "sell_gold": 1,
    },
    "gold_ore": {
        "name": "Ruda złota", "type": "resource", "price": None,
        "desc": "Rzadka i cenna ruda.", "sell_gold": 4,
    },
    "mithril_ore": {
        "name": "Ruda mithrilu (stary przedmiot)", "type": "resource", "price": None,
        "desc": "Przedmiot zgodności ze starszych wersji. Nie można go już wydobyć.",
        "sell_gold": 120,
    },
    "soul_shard": {
        "name": "Odłamek Duszy", "type": "quest", "price": None,
        "desc": "Niestabilny odłamek znaleziony przy istotach z krypty.",
    },
    "wolf_fang": {
        "name": "Kieł Wilka Cienia", "type": "loot", "price": None,
        "desc": "Ciemny kieł pulsujący słabą energią.",
    },
}


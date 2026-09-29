"""Read-only cross-system data and reward audit for the assembled runtime.

Run with ``python -m admin.cross_system_audit_v1001``. This is intentionally
separate from the runtime manifest: it measures final catalogs after loading.
"""
from __future__ import annotations

import inspect
import json
import os
import socket
import tempfile
from collections import Counter, defaultdict
from config.balance import (
    CHARACTER_XP_REQUIREMENT_MULTIPLIER,
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    STAT_XP_REQUIREMENT_MULTIPLIER,
    TOOL_XP_REQUIREMENT_MULTIPLIERS,
)


def audit(runtime):
    quests = runtime.QUESTS
    mobs = runtime.MOB_TEMPLATES
    items = runtime.ITEMS
    rooms = runtime.ROOMS
    npcs = runtime.NPCS
    profession_names = set(runtime.PROFESSION_RANK_NAMES)
    tool_profession_map = dict(runtime.TOOL_PROFESSION_MAP)
    quest_aliases = set(mobs)
    for mob in mobs.values():
        for field in ("quest_target", "canonical_template_id"):
            if isinstance(mob.get(field), str):
                quest_aliases.add(mob[field])
        quest_aliases.update(mob.get("quest_targets") or ())
    errors = []
    warnings = []

    # Quest acceptance must never be gated by any numeric level axis.
    # Level metadata remains valid for staging/rewards, but not availability.
    from player.session_mixins.quest_offers import SessionQuestOffersMixin
    from player.session_mixins.quest_npc import SessionQuestNpcMixin
    level_gate_fields = (
        "required_level",
        "required_soul_level",
        "required_soul_tier",
        "min_profession_level",
        "min_tool_level",
    )
    for label, method in (
        ("quest_lock_reasons", SessionQuestOffersMixin.quest_lock_reasons),
        ("specialist_quest_available", SessionQuestNpcMixin.specialist_quest_available),
    ):
        source = inspect.getsource(method)
        used = [field for field in level_gate_fields if field in source]
        if used:
            errors.append(
                f"{label}: quest availability contains forbidden level gate fields: "
                + ", ".join(used)
            )

    # Driada is a female-only playable race. This must be enforced below the UI
    # so alternate creation paths cannot bypass the rule.
    from storage.db_accounts import DatabaseAccountsMixin
    character_create_source = inspect.getsource(DatabaseAccountsMixin.create_character)
    if 'rname == "Driada"' not in character_create_source or 'gender != "kobieta"' not in character_create_source:
        errors.append("character creation no longer enforces female-only Dryad race")
    kinds = Counter()
    by_stage = defaultdict(lambda: {"quests": 0, "quest_silver": [], "quest_character_xp": [], "mobs": 0, "mob_silver": [], "mob_class_xp": []})
    stage_bands = ((1, 50), (51, 100), (101, 200), (201, 300), (301, 400), (401, 500), (501, 600))

    def band(level):
        for low, high in stage_bands:
            if low <= level <= high:
                return f"{low}-{high}"
        return "outside_1_600"

    for qid, q in quests.items():
        kind = q.get("kind", "")
        kinds[kind] += 1
        target = q.get("target")
        needed = q.get("needed")
        if needed is not None and (not isinstance(needed, int) or needed <= 0):
            errors.append(f"quest {qid}: invalid needed={needed!r}")
        dynamic_kill_target = isinstance(target, str) and (
            target == "*"
            or target.startswith("crypt_boss_") and target.removeprefix("crypt_boss_").isdigit()
            or target in ("magitek_infinite", "magitek_elite")
        )
        if kind == "kill" and target and target not in quest_aliases and not dynamic_kill_target:
            warnings.append(f"quest {qid}: kill target absent from mob catalog: {target}")
        if kind in ("collect", "collect_resource") and isinstance(target, str) and target not in items:
            warnings.append(f"quest {qid}: item target absent from item catalog: {target}")
        if kind in ("talk_npc", "deliver_npc") and isinstance(target, str) and target not in npcs:
            warnings.append(f"quest {qid}: NPC target absent from NPC catalog: {target}")
        if q.get("target_npc") and q["target_npc"] not in npcs:
            errors.append(f"quest {qid}: unknown target_npc {q['target_npc']}")
        for field in ("reward_silver", "reward_gold", "reward_mithril", "character_xp_reward", "reward_soul_xp", "reward_profession_xp", "reward_tool_xp"):
            value = q.get(field, 0)
            if not isinstance(value, (int, float)):
                errors.append(f"quest {qid}: non-numeric {field}={value!r}")
            elif value < 0:
                errors.append(f"quest {qid}: negative {field}={value}")

        reward_profession = q.get("reward_profession")
        reward_tool_type = q.get("reward_tool_type")
        raw_profession_xp = q.get("reward_profession_xp", 0)
        raw_tool_xp = q.get("reward_tool_xp", 0)
        reward_profession_xp = int(raw_profession_xp or 0) if isinstance(raw_profession_xp, (int, float)) else 0
        reward_tool_xp = int(raw_tool_xp or 0) if isinstance(raw_tool_xp, (int, float)) else 0
        if reward_profession and reward_profession not in profession_names:
            errors.append(f"quest {qid}: unknown reward profession {reward_profession}")
        if reward_tool_type and reward_tool_type not in tool_profession_map:
            errors.append(f"quest {qid}: unknown reward tool type {reward_tool_type}")
        if reward_profession_xp and not reward_profession:
            mapped = tool_profession_map.get(reward_tool_type)
            if not mapped:
                errors.append(f"quest {qid}: profession XP reward has no profession/tool mapping")
        if reward_profession and reward_tool_type:
            mapped = tool_profession_map.get(reward_tool_type)
            if mapped and mapped != reward_profession:
                errors.append(
                    f"quest {qid}: reward tool {reward_tool_type} maps to {mapped}, "
                    f"but reward_profession is {reward_profession}"
                )
        if reward_tool_xp and not reward_tool_type:
            errors.append(f"quest {qid}: tool XP reward missing reward_tool_type")
        prerequisite = q.get("requires_quest")
        if prerequisite and prerequisite not in quests:
            errors.append(f"quest {qid}: missing prerequisite {prerequisite}")
        for item_id in (q.get("reward_items") or {}):
            if item_id not in items:
                errors.append(f"quest {qid}: unknown reward item {item_id}")
        level = max(int(q.get("generator_level", 1) or 1), int(q.get("min_profession_level", 1) or 1), int(q.get("required_level", 1) or 1))
        row = by_stage[band(level)]
        row["quests"] += 1
        row["quest_silver"].append(int(q.get("reward_silver", 0) or 0) + 100 * int(q.get("reward_gold", 0) or 0) + 100_000_000 * int(q.get("reward_mithril", 0) or 0))
        row["quest_character_xp"].append(int(q.get("character_xp_reward", 0) or 0))

    for mid, mob in mobs.items():
        for field in ("max_hp", "damage", "silver", "gold", "mithril", "character_xp_reward", "class_xp_reward", "soul_reward"):
            value = mob.get(field, 0)
            if isinstance(value, (int, float)) and value < 0:
                errors.append(f"mob {mid}: negative {field}={value}")
        for item_id in (mob.get("drops") or {}):
            if item_id not in items:
                warnings.append(f"mob {mid}: unknown drop {item_id}")
        level = int(mob.get("generator_level", 1) or 1)
        row = by_stage[band(level)]
        row["mobs"] += 1
        row["mob_silver"].append(int(mob.get("silver", 0) or 0) + 100 * int(mob.get("gold", 0) or 0) + 100_000_000 * int(mob.get("mithril", 0) or 0))
        row["mob_class_xp"].append(int(mob.get("class_xp_reward", 0) or 0))

    for qid in quests:
        visited = set()
        current = qid
        while current in quests and current not in visited:
            visited.add(current)
            current = quests[current].get("requires_quest")
        if current in visited:
            errors.append(f"quest {qid}: prerequisite cycle through {current}")

    summary = {}
    for name, row in by_stage.items():
        summary[name] = {key: (round(sum(value) / len(value), 1) if value else 0) if isinstance(value, list) else value for key, value in row.items()}
    ocean_fish = {key: item for key, item in items.items() if item.get("deep_ocean")}
    generator = runtime.generator_core_v027
    progression = {}
    for stage in (1, 50, 100, 200, 300, 400, 500, 600):
        sample = {}
        for axis in ("character", "class", "soul", "profession", "tool", "stat"):
            multiplier = {
                "character": CHARACTER_XP_REQUIREMENT_MULTIPLIER,
                "profession": PROFESSION_XP_REQUIREMENT_MULTIPLIERS.get("Wędkarstwo", 1),
                "tool": TOOL_XP_REQUIREMENT_MULTIPLIERS.get("fishing", 1),
                "stat": STAT_XP_REQUIREMENT_MULTIPLIER,
            }.get(axis, 1)
            required = generator.axis_requirement(axis, stage) * multiplier
            gained = generator.axis_gain(axis, stage)
            sample[axis] = round(required / gained, 2)
        progression[stage] = sample
    return {
        "quests": len(quests), "mobs": len(mobs), "items": len(items), "rooms": len(rooms), "npcs": len(npcs),
        "professions": len(profession_names), "tool_types": len(tool_profession_map),
        "quest_kinds": dict(kinds), "bands": summary,
        "equal_stage_actions_per_level": progression,
        "ocean_economy": {
            "ship_purchase_silver": 25_000,
            "one_module_levels_2_to_5_silver": sum(12_500 * level * level for level in range(2, 6)),
            "contract_rewards_silver": [offer[4] for offer in runtime.SessionOceanV1000Mixin.ocean_trade_offers_v1000(None)],
            "deep_fish_sell_silver": {key: item.get("sell_silver") for key, item in ocean_fish.items()},
        },
        "errors": errors, "warnings": warnings,
    }


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="soulbound-cross-audit-") as directory:
        os.environ["SOULBOUND_DB"] = os.path.join(directory, "audit.db")
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            os.environ["SOULBOUND_PORT"] = str(probe.getsockname()[1])
        import server
        try:
            print(json.dumps(audit(server), ensure_ascii=False, indent=2))
        finally:
            server._BOOT_SOCKET.close()

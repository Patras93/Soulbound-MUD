# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

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
        maximum = max(xs) if xs else CHARACTER_MAX_LEVEL
    except Exception:
        maximum = 400
    raw = max(1, int(round(float(value))))
    # Real 1-600 axes keep their stage. Short ordinal systems (e.g. ranks 1-10)
    # are stretched through the same 1-600 Generator Core space.
    stage = balance_math.clamp(raw, 1, CHARACTER_MAX_LEVEL) if maximum >= 300 else balance_math.stage_from_index(raw, max(1, maximum))

    exact = {
        "V019_CLASS_REQ": lambda: balance_math.axis_requirement("class", stage),
        "V019_SOUL_REQ": lambda: balance_math.axis_requirement("soul", stage),
        "V019_SKILL_REQ": lambda: balance_math.axis_requirement("skill", stage),
        "V019_PROF_REQ": lambda: balance_math.axis_requirement("profession", stage),
        "V019_TOOL_REQ": lambda: balance_math.axis_requirement("tool", stage),
        "V019_STAT_REQ": lambda: balance_math.axis_requirement("stat", stage),
        "V019_SKILL_GAIN": lambda: balance_math.axis_gain("skill", stage),
        "V019_PROF_GAIN": lambda: balance_math.axis_gain("profession", stage),
        "V019_TOOL_GAIN": lambda: balance_math.axis_gain("tool", stage),
        "V019_CLASS_KILL_NORMAL": lambda: balance_math.axis_gain("class", stage, 1.0),
        "V019_CLASS_KILL_BOSS": lambda: balance_math.axis_gain("class", stage, balance_math.RANK_REWARD["boss"]),
        "V019_SOUL_KILL_NORMAL": lambda: balance_math.axis_gain("soul", stage, 1.0),
        "V019_SOUL_KILL_BOSS": lambda: balance_math.axis_gain("soul", stage, balance_math.RANK_REWARD["boss"]),
        "V019_STAT_KILL_NORMAL": lambda: balance_math.axis_gain("stat", stage, 1.0),
        "V019_STAT_KILL_BOSS": lambda: balance_math.axis_gain("stat", stage, balance_math.RANK_REWARD["boss"]),
        "V019_COIN_KILL_NORMAL": lambda: balance_math.currency_for_stage(stage, "normal"),
        "V019_COIN_KILL_BOSS": lambda: balance_math.currency_for_stage(stage, "boss"),
        "V019_HP_NORMAL": lambda: balance_math.mob_hp(stage, "normal"),
        "V019_DAMAGE_NORMAL": lambda: balance_math.mob_damage(stage, "normal"),
        "V019_QUEST_COIN": lambda: balance_math.system_reward(stage, "quest"),
        "V019_ECONOMY_SINK": lambda: balance_math.system_cost(stage, "economy"),
        "V019_RESOURCE_SALE": lambda: balance_math.resource_sale_for_stage(stage),
    }
    if identity in exact:
        return min(V019_SAFE_INT, max(1, int(exact[identity]())))
    upper = identity.upper()
    if "HP" in upper:
        result = balance_math.mob_hp(stage, "boss" if "BOSS" in upper else "normal")
    elif "DAMAGE" in upper or "DMG" in upper:
        result = balance_math.mob_damage(stage, "boss" if "BOSS" in upper else "normal")
    elif "REQ" in upper or "COST" in upper:
        result = balance_math.system_cost(stage, identity)
    elif "SALE" in upper:
        result = balance_math.resource_sale_for_stage(stage)
    else:
        result = balance_math.system_reward(stage, identity)
    return min(V019_SAFE_INT, max(1, int(result)))


def v0190_apply_combat_template(template):
    """Restore an authored runtime baseline and fill only missing combat numbers.

    Later dungeon/world wrappers may safely call this repeatedly: the first call
    snapshots the authored/generated baseline, and every later call restores it
    before applying its own multipliers. This keeps runtime refresh idempotent
    without letting Generator Core erase hand-tuned combat/economy values.
    """
    if not isinstance(template, dict):
        return template
    stage = template.get("generator_level")
    if stage is None:
        stage = balance_math.semantic_floor_level(template)
    if stage is None:
        for key in ("elite_base_template", "rare_base_template", "base_template", "template_id"):
            base = template.get(key)
            if base and base in globals().get("MOB_TEMPLATES", {}):
                stage = globals()["MOB_TEMPLATES"][base].get("generator_level")
                if stage is not None:
                    break
    if stage is None:
        # v2.00.6: names are NOT difficulty levels.  The legacy name hash made
        # the starter Goblin a stage-112 monster.  Derive an implicit stage from
        # authored combat stats; explicit dungeon, zone and boss stages above
        # always take precedence.  This never reads player level or followers.
        stage = v0190_mob_stage(template)
    stage = max(1, min(CHARACTER_MAX_LEVEL, int(stage)))
    rank = balance_math.mob_rank(template)
    template["generator_level"] = stage
    template["v019_stage"] = stage

    generated = {
        "max_hp": balance_math.mob_hp(stage, rank),
        "damage": balance_math.mob_damage(stage, rank),
        "character_xp_reward": balance_math.axis_gain("character", stage, balance_math.RANK_REWARD.get(rank,1.0)),
        "class_xp_reward": balance_math.axis_gain("class", stage, balance_math.RANK_REWARD.get(rank,1.0)),
        "soul_reward": balance_math.axis_gain("soul", stage, balance_math.RANK_REWARD.get(rank,1.0)),
        "stat_reward": balance_math.axis_gain("stat", stage, balance_math.RANK_REWARD.get(rank,1.0)),
    }

    # Procedural no-limit floors have separate depth curves. Their temporary
    # authoring formulas are not a second combat baseline, otherwise floor
    # scaling would be multiplied twice and explode at 1000/10000+. Static and
    # normal-world authored content keeps its hand-tuned baseline.
    depth_hints = []
    for floor_key in (
        "crypt_floor", "mythic_crypt_floor", "astral_floor",
        "mythic_astral_floor", "giant_fortress_floor",
        "profession_dungeon_floor",
    ):
        raw_floor = template.get(floor_key)
        if raw_floor is None:
            continue
        try:
            parsed_floor = int(raw_floor or 0)
        except (TypeError, ValueError, OverflowError):
            parsed_floor = 0
        if parsed_floor > 0:
            depth_hints.append(parsed_floor)
    procedural_no_limit = bool(depth_hints and max(depth_hints) > 200)

    for key, fallback in generated.items():
        baseline_key = f"_v1138_authored_{key}"
        if baseline_key not in template:
            current = template.get(key)
            valid = isinstance(current, (int, float)) and not isinstance(current, bool)
            if key in ("max_hp", "damage"):
                valid = valid and float(current) > 0
            elif valid:
                valid = float(current) >= 0
            if procedural_no_limit:
                valid = False
            template[baseline_key] = int(current) if valid else int(fallback)
        template[key] = int(template[baseline_key])

    template["base_max_hp"] = int(template["max_hp"])

    # Preserve authored denominations. If no currency existed at all, snapshot
    # Generator silver once as a fallback. Runtime refresh never changes it.
    currency_keys = ("silver", "gold", "mithril")
    if "_v1138_authored_currency" not in template:
        had_currency = any(key in template for key in currency_keys)
        template["_v1138_authored_currency"] = tuple(
            int(template.get(key, 0) or 0) for key in currency_keys
        ) if had_currency else (int(balance_math.currency_for_stage(stage, rank)), 0, 0)
    template["silver"], template["gold"], template["mithril"] = template["_v1138_authored_currency"]

    # v0.36.2 terrain clones remain a deliberate generated layer, but start
    # from the restored authored baseline on every refresh.
    if template.get("terrain_runtime_clone_v0362"):
        hp_mult = float(template.get("terrain_hp_multiplier_v0362", 1.0) or 1.0)
        dmg_mult = float(template.get("terrain_damage_multiplier_v0362", 1.0) or 1.0)
        template["max_hp"] = max(1, int(round(template["max_hp"] * hp_mult)))
        template["base_max_hp"] = template["max_hp"]
        template["damage"] = max(1, int(round(template["damage"] * dmg_mult)))

    # Drop chances are authored content. Runtime refresh must never reroll or
    # normalize them behind the designer's back.
    return template


def v0190_quest_stat_reward(quest):
    quest = quest or {}
    stage = v0190_quest_stage(quest)
    generated_base = balance_math.axis_gain("stat", stage, 2.0)

    # v1.13.42: ręczna/stara nagroda może być większa, ale nie może już
    # obniżyć questa wysokiego Tieru do płaskiej wartości z dawnych danych.
    manual_reward = quest.get("manual_stat_progress")
    if manual_reward is not None:
        base = max(generated_base, max(0, int(manual_reward or 0)))
    elif quest.get("generator_level") is not None:
        base = max(
            generated_base,
            max(0, int(quest.get("reward_stat_progress", 0) or 0)),
        )
    else:
        base = generated_base

    # v1.13.8: ordinary quests move stats a little faster, while memorable
    # objectives pay a clearly stronger stat-progress burst.
    kind = str(quest.get("kind") or "").strip().lower()
    mult = {
        "talk_npc": 1.05,
        "talk_class_teacher": 1.10,
        "deliver_npc": 1.10,
        "collect": 1.12,
        "collect_resource": 1.12,
        "collect_category": 1.15,
        "collect_distinct_category": 1.18,
        "collect_resource_set": 1.22,
        "craft_set": 1.25,
        "kill": 1.25,
        "explore_frontier": 1.20,
        "discover_secret": 1.50,
        "mini_dungeon": 1.85,
        "legendary_rare": 2.25,
        "world_event": 2.10,
        "world_boss": 3.00,
    }.get(kind, 1.12)
    if int(quest.get("required_soul_level", 0) or 0) > 0:
        mult = max(mult, 2.25)
    return max(0, int(round(base * mult)))


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
            _catalog_mut.catalog_assign(item, 'ITEMS', ITEMS, (item_id,))

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
            _catalog_mut.catalog_assign(item, 'ITEMS', ITEMS, (item_id,))

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
            _catalog_mut.catalog_assign(item, 'ITEMS', ITEMS, (item_id,))

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
        _catalog_mut.catalog_assign(item, 'ITEMS', ITEMS, (item_id,))


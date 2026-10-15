from validation.v4200_virtual_source import read_actual_refactored_source_v4200 as _sb420_view
# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def full_release_integrity_audit_v03022():
    errors=[]
    warnings=[]
    stats={}

    # Every previously active release gate must still be clean.
    audit_names=(
        "CATALOG_VALIDATION_AUDIT", "GENERATOR_WHITELIST_AUDIT_V03019",
        "WORLD_TOPOLOGY_AUDIT", "WORLD_LOGIC_AUDIT",
        "FULL_WORLD_TOPOLOGY_AUDIT_V03013", "FULL_GAME_AUDIT_V03014",
        "FULL_COMBAT_SCALING_AUDIT_V03015", "AGGRO_CLEANUP_AUDIT_V03015",
        "CLASS_EQ_AUDIT_V03015", "EQUIPMENT_NAME_AUDIT_V03016",
        "CLASS_EQ_IDENTITY_AUDIT_V03016", "PROGRESSION_COMBAT_AUDIT_V03017",
        "GENERATOR_NUMERIC_ONLY_AUDIT_V03018", "EQUIPMENT_EXPANSION_AUDIT_V03020",
        "FULL_HELP_AUDIT_V03021", "EQ_SHOP_AUDIT_V03021",
        "CURRENCY_ECONOMY_AUDIT_V03021",
    )
    for name in audit_names:
        audit=globals().get(name)
        if not isinstance(audit,dict):
            errors.append(f"missing audit {name}")
            continue
        if int(audit.get("error_count",0) or 0):
            errors.append(f"{name}: {audit.get('errors',[])[:3]}")
        if int(audit.get("warning_count",0) or 0):
            warnings.append(f"{name}: {audit.get('warnings',[])[:3]}")

    opposite={
        "north":"south", "south":"north", "east":"west", "west":"east",
        "northeast":"southwest", "southwest":"northeast",
        "northwest":"southeast", "southeast":"northwest",
        "up":"down", "down":"up",
    }
    static_edges=0
    lazy_edges=[]
    for rid,room in ROOMS.items():
        if not str(room.get("name","")).strip(): errors.append(f"room without name: {rid}")
        if not str(room.get("zone","")).strip(): errors.append(f"room without zone: {rid}")
        if not str(room.get("desc","")).strip(): errors.append(f"room without desc: {rid}")
        exits=room.get("exits",{})
        if not isinstance(exits,dict):
            errors.append(f"room exits not dict: {rid}")
            continue
        for direction,target in exits.items():
            if direction not in opposite: errors.append(f"invalid direction: {rid}.{direction}")
            if target==rid: errors.append(f"self exit: {rid}.{direction}")
            if target in ROOMS:
                static_edges += 1
                if ROOMS[target].get("exits",{}).get(opposite.get(direction)) != rid:
                    errors.append(f"nonreciprocal: {rid}.{direction}->{target}")
            else:
                lazy_edges.append((rid,direction,target))
                kind,floor=instance_room_identity(target)
                known=kind is not None or str(target).startswith((
                    "v0130_frontier_", "v018_endless_", "v020_mega_", "magitek_floor_",
                    "v021_gauntlet_", "v0140_mini_", "v0140_secret_",
                    "v018_archipelago_", "v018_ruin_",
                    "uoss_deep_dungeon_floor_",
                ))
                if not known:
                    errors.append(f"unknown lazy exit: {rid}.{direction}->{target}")

    # Reachability and return-path invariants are mandatory release gates.
    logic=WORLD_LOGIC_AUDIT
    if int(logic.get("reachable_from_square",0)) != len(ROOMS):
        errors.append(f"reachable {logic.get('reachable_from_square')} != rooms {len(ROOMS)}")
    if int(logic.get("returnable_to_square",0)) != len(ROOMS):
        errors.append(f"returnable {logic.get('returnable_to_square')} != rooms {len(ROOMS)}")

    # Profession terrain references: every authored gathering location must still exist.
    room_collections={
        "RIVER_FISHING_ROOMS":RIVER_FISHING_ROOMS, "LAKE_FISHING_ROOMS":LAKE_FISHING_ROOMS,
        "SEA_FISHING_ROOMS":SEA_FISHING_ROOMS, "OCEAN_FISHING_ROOMS":OCEAN_FISHING_ROOMS,
        "FRESHWATER_FISHING_ROOMS":FRESHWATER_FISHING_ROOMS, "MARINE_FISHING_ROOMS":MARINE_FISHING_ROOMS,
        "FISHING_ROOMS":FISHING_ROOMS, "MINING_ROOMS":MINING_ROOMS,
        "UNIFIED_DEEP_MINE_STATIC_ROOMS":UNIFIED_DEEP_MINE_STATIC_ROOMS,
        "AUTO_FISHING_ROUTE":AUTO_FISHING_ROUTE, "AUTO_WOODCUTTING_ROUTE":AUTO_WOODCUTTING_ROUTE,
        "AUTO_HERBALISM_ROUTE":AUTO_HERBALISM_ROUTE, "WOODCUTTING_ROOMS":WOODCUTTING_ROOMS,
        "MEADOW_HERBALISM_ROOMS":MEADOW_HERBALISM_ROOMS, "HERBALISM_ROOMS":HERBALISM_ROOMS,
    }
    for name,values in room_collections.items():
        missing=[room for room in values if room not in ROOMS]
        if missing: errors.append(f"{name} missing rooms: {missing[:10]}")

    for tool_id,room_id in TOOL_SHOP_ROOMS.items():
        if tool_id not in ITEMS: errors.append(f"tool shop item missing: {tool_id}")
        if room_id not in ROOMS: errors.append(f"tool shop room missing: {tool_id}->{room_id}")
    for room_id,item_ids in SHOPS.items():
        if room_id not in ROOMS: errors.append(f"shop room missing: {room_id}")
        for item_id in item_ids:
            if item_id not in ITEMS: errors.append(f"shop item missing: {room_id}->{item_id}")
    for room_id in PROFESSION_GUIDE_PRIMARY_ROOMS.values():
        if room_id not in ROOMS: errors.append(f"profession guide room missing: {room_id}")

    resource_collections={
        "FISH_RESOURCE_IDS":FISH_RESOURCE_IDS, "ORE_RESOURCE_IDS":ORE_RESOURCE_IDS,
        "WOOD_RESOURCE_IDS":WOOD_RESOURCE_IDS, "HERB_RESOURCE_IDS":HERB_RESOURCE_IDS,
        "WORLD_FISH_IDS":WORLD_FISH_IDS, "WORLD_ORE_IDS":WORLD_ORE_IDS,
        "WORLD_WOOD_IDS":WORLD_WOOD_IDS, "WORLD_HERB_IDS":WORLD_HERB_IDS,
    }
    for name,values in resource_collections.items():
        missing=[item_id for item_id in values if item_id not in ITEMS]
        if missing: errors.append(f"{name} missing items: {missing[:10]}")

    # Static content references outside the terrain graph.
    for room_id,template_id in MOB_SPAWNS:
        if room_id not in ROOMS: errors.append(f"spawn room missing: {room_id}:{template_id}")
        if template_id not in MOB_TEMPLATES: errors.append(f"spawn mob missing: {room_id}:{template_id}")
    for npc_id,npc in NPCS.items():
        if npc.get("room") not in ROOMS: errors.append(f"NPC room missing: {npc_id}->{npc.get('room')}")
    for class_name,tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        for mastery,item_ids in tiers.items():
            for item_id in item_ids:
                if item_id not in ITEMS: errors.append(f"class EQ missing: {class_name}/{mastery}/{item_id}")

    stats.update({
        "rooms":len(ROOMS), "static_directed_edges":static_edges, "lazy_runtime_exits":len(lazy_edges),
        "zones":len({str(r.get('zone') or '') for r in ROOMS.values()}),
        "mobs":len(MOB_TEMPLATES), "spawns":len(MOB_SPAWNS), "items":len(ITEMS),
        "quests":len(QUESTS), "npcs":len(NPCS), "skills":sum(len(v) for v in CLASS_SKILLS.values()),
        "help_topics":len(HELP_TOPICS), "help_aliases":len(HELP_TOPIC_ALIASES),
        "fishing_rooms":len(FISHING_ROOMS), "mining_rooms":len(MINING_ROOMS),
        "woodcutting_rooms":len(WOODCUTTING_ROOMS), "herbalism_rooms":len(HERBALISM_ROOMS),
        "active_audits_checked":len(audit_names),
    })
    return {
        "version":"0.30.22", "error_count":len(errors), "warning_count":len(warnings),
        "errors":errors, "warnings":warnings, **stats,
    }


def quest_reward_hybrid_audit_v03024():
    errors = []
    manual_ids = set(V03024_MANUAL_QUEST_REWARDS_COINS)
    automatic_ids = set(QUESTS) - manual_ids

    if V03024_MANUAL_QUEST_REWARD_MARKING.get("missing"):
        errors.append("manual quest IDs missing: " + ", ".join(V03024_MANUAL_QUEST_REWARD_MARKING["missing"][:10]))

    for quest_id, quest in QUESTS.items():
        reward = int(quest.get("reward_silver", 0) or 0)
        if reward < 0:
            errors.append(f"negative quest reward: {quest_id}")
        if int(quest.get("reward_gold", 0) or 0) != 0 or int(quest.get("reward_mithril", 0) or 0) != 0:
            errors.append(f"quest has split wallet reward: {quest_id}")
        if quest_id in manual_ids:
            expected = int(V03024_MANUAL_QUEST_REWARDS_COINS[quest_id])
            if quest.get("currency_reward_mode") != "manual":
                errors.append(f"manual reward mode missing: {quest_id}")
            if int(quest.get("manual_currency_reward_coins", -1)) != expected:
                errors.append(f"manual reward marker changed: {quest_id}")
            if reward != expected:
                errors.append(f"manual reward overwritten: {quest_id}={reward}, expected={expected}")
        else:
            if quest.get("manual_currency_reward_coins") is not None:
                errors.append(f"unexpected manual marker: {quest_id}")
            # v1.13.21: since Generator Core v0.62.0/v1.13.15, authored
            # quest currency wins even without a manual marker. The old 1001
            # minimum belonged to Generator-owned fallback rewards and must not
            # reject valid authored payouts. Global quest economy only requires
            # the shared minimum of 1 Gold = SILVER_PER_GOLD.
            if reward < SILVER_PER_GOLD:
                errors.append(f"quest reward below unified economy floor: {quest_id}={reward}")

    # Critical hand-authored anchors.
    anchors = {
        "soul_shards": 7_500,
        "fisher_30_fish": 2_500,
        "herbalist_30_herbs": 2_500,
        "lumberjack_30_wood": 2_500,
        "miner_30_ore": 2_500,
        "mountain_troll_hunt": 15_000,
        "troll_king_hunt": 75_000,
        "desert_patrol": 150_000,
    }
    for quest_id, expected in anchors.items():
        if int(QUESTS.get(quest_id, {}).get("reward_silver", -1)) != expected:
            errors.append(f"anchor reward mismatch: {quest_id}")

    # Presentation must be a lossless view of the one shared integer balance.
    sample_values = (
        0, 1, 999, 1000, 2500, 7_500, 150_000,
        SILVER_PER_MITHRIL, SILVER_PER_MITHRIL + 2 * SILVER_PER_GOLD + 345,
        max(int(q.get("reward_silver", 0) or 0) for q in QUESTS.values()),
    )
    for coins in sample_values:
        mithril, gold, silver = currency_denominations(coins)
        rebuilt = legacy_currency_to_coins(silver, gold, mithril)
        if rebuilt != coins:
            errors.append(f"currency roundtrip {coins}->{mithril}/{gold}/{silver}->{rebuilt}")

    rewards = [int(q.get("reward_silver", 0) or 0) for q in QUESTS.values()]
    return {
        "version": "0.30.24",
        "quests": len(QUESTS),
        "manual_quests": len(manual_ids),
        "automatic_quests": len(automatic_ids),
        "min_reward": min(rewards) if rewards else 0,
        "max_reward": max(rewards) if rewards else 0,
        "single_balance_storage": all(
            int(q.get("reward_gold", 0) or 0) == 0 and int(q.get("reward_mithril", 0) or 0) == 0
            for q in QUESTS.values()
        ),
        "error_count": len(errors),
        "errors": errors,
    }


def profession_tool_xp_audit_v03025():
    errors = []
    recipe_tables = (
        ("Kowalstwo", "crafting", CRAFT_RECIPES),
        ("Alchemia", "alchemy", ALCHEMY_RECIPES),
        ("Gotowanie", "cooking", COOK_RECIPES),
        ("Jubilerstwo", "jewelcrafting", JEWELCRAFT_RECIPES),
    )
    recipe_count = 0
    ingot_count = 0
    for profession, tool_type, recipes in recipe_tables:
        for recipe_id, recipe in recipes.items():
            recipe_count += 1
            profession_xp = int(recipe.get("profession_xp", 0) or 0)
            tool_xp = int(recipe.get("tool_xp", 0) or 0)
            if profession_xp <= 0:
                errors.append(f"{profession}/{recipe_id}: brak profession_xp")
            if tool_xp <= 0:
                errors.append(f"{profession}/{recipe_id}: brak tool_xp")
            output_id = str(recipe.get("output") or "")
            if tool_type == "crafting" and (output_id.endswith("_ingot") or output_id.startswith("ingot_")):
                ingot_count += 1
                if profession_xp <= 0 or tool_xp <= 0:
                    errors.append(f"przetop {recipe_id}: nie rozwija jednocześnie Kowalstwa i Młota")

    profession_quest_count = 0
    for quest_id, quest in QUESTS.items():
        profession_xp = int(quest.get("reward_profession_xp", 0) or 0)
        tool_xp = int(quest.get("reward_tool_xp", 0) or 0)
        profession = quest.get("reward_profession")
        tool_type = quest.get("reward_tool_type")
        if not (profession_xp or tool_xp or profession or tool_type):
            continue
        profession_quest_count += 1
        expected = profession_for_tool_type(tool_type)
        if profession_xp <= 0:
            errors.append(f"quest {quest_id}: brak reward_profession_xp")
        if tool_xp <= 0:
            errors.append(f"quest {quest_id}: brak reward_tool_xp")
        if not tool_type:
            errors.append(f"quest {quest_id}: brak reward_tool_type")
        if not profession:
            errors.append(f"quest {quest_id}: brak reward_profession")
        if expected and profession and profession != expected:
            errors.append(
                f"quest {quest_id}: {profession} nie pasuje do narzędzia {tool_type} ({expected})"
            )

    # Główne akcje zbierackie są celowo jawne: każda wywołuje
    # grant_profession_progress(profesja, xp, narzędzie, xp).
    gathering_pairs = {
        "fish": ("Wędkarstwo", "fishing"),
        "mine": ("Górnictwo", "mining"),
        "woodcut": ("Drwalstwo", "woodcutting"),
        "gather_herb": ("Zielarstwo", "herbalism"),
    }
    return {
        "version": "0.30.25",
        "recipes_checked": recipe_count,
        "ingot_recipes_checked": ingot_count,
        "profession_quests_checked": profession_quest_count,
        "quest_profession_repairs": len(V03025_PROFESSION_REWARD_REPAIRS),
        "gathering_actions_checked": len(gathering_pairs),
        "gathering_pairs": gathering_pairs,
        "error_count": len(errors),
        "errors": errors,
    }


def gameplay_flow_audit_v03026():
    errors = []
    if COMMAND_ALIASES.get("ex") != "exits":
        errors.append("ex nie mapuje się na exits")

    # Dostęp zasobów musi zmieniać się wyłącznie na progach Tieru.
    for _tool_type in ("fishing", "mining", "woodcutting", "herbalism"):
        previous_access = None
        previous_tier = None
        for _level in range(1, 401):
            _tier = tool_tier(_level)
            _access = tool_tier_access_level(_level)
            if _access != TOOL_TIER_THRESHOLDS[_tier - 1]:
                errors.append(f"{_tool_type}: zły access level {_level}->{_access}")
                break
            if previous_tier == _tier and previous_access != _access:
                errors.append(f"{_tool_type}: pula zmienia się wewnątrz Tieru {_tier}")
                break
            previous_access, previous_tier = _access, _tier

    recipe_count = 0
    for _recipes in (CRAFT_RECIPES, COOK_RECIPES, ALCHEMY_RECIPES, JEWELCRAFT_RECIPES):
        for _rid, _recipe in _recipes.items():
            recipe_count += 1
            _required = max(1, int(_recipe.get("min_profession_level", _recipe.get("min_tool_level", 1)) or 1))
            _required_tier = required_tool_tier_for_level(_required)
            if not 1 <= _required_tier <= TOOL_MAX_TIER:
                errors.append(f"recipe {_rid}: invalid tool tier {_required_tier}")
            if int(_recipe.get("profession_xp", 0) or 0) <= 0:
                errors.append(f"recipe {_rid}: brak profession_xp")
            if int(_recipe.get("tool_xp", 0) or 0) <= 0:
                errors.append(f"recipe {_rid}: brak tool_xp")

    for _rid in V03026_WOOD_RECIPES:
        _recipe = CRAFT_RECIPES[_rid]
        if _recipe.get("profession") != "Drwalstwo" or _recipe.get("tool_type") != "woodcutting":
            errors.append(f"wood recipe {_rid}: zła para profesja/narzędzie")

    smith_missing = [
        _rid for _rid, _recipe in CRAFT_RECIPES.items()
        if _rid not in V03026_WOOD_RECIPES
        and "crafting_workshop" not in tuple(_recipe.get("stations", ()))
    ]
    if smith_missing:
        errors.append(f"station crafting_workshop: brak w {smith_missing[:5]}")
    wood_missing = [
        _rid for _rid in V03026_WOOD_RECIPES
        if "forester_lodge" not in tuple(CRAFT_RECIPES[_rid].get("stations", ()))
    ]
    if wood_missing:
        errors.append(f"station forester_lodge: brak w {wood_missing[:5]}")
    required_stations = (
        (COOK_RECIPES, "blue_flame_kitchen"),
        (ALCHEMY_RECIPES, "alchemy_lab"),
        (JEWELCRAFT_RECIPES, "jeweler_workshop"),
    )
    for _recipes, _station in required_stations:
        missing = [_rid for _rid, _recipe in _recipes.items() if _station not in tuple(_recipe.get("stations", ()))]
        if missing:
            errors.append(f"station {_station}: brak w {missing[:5]}")


    return {
        "version": "0.30.26",
        "generator_version": str(BALANCE_MATH_VERSION),
        "recipes_checked": recipe_count,
        "wood_recipes_fixed": len(V03026_WOOD_RECIPES),
        "tool_tiers": TOOL_MAX_TIER,
        "gathering_professions": 4,
        "error_count": len(errors),
        "errors": errors,
    }


def full_game_audit_v03055():
    errors = []
    warnings = []

    # 1. World graph: every explicit exit must point to a real room.
    bad_exits = []
    dynamic_exits = []
    dynamic_prefixes = (
        "prof_", "mine_floor_", "crypt_floor_", "astral_floor_",
        "mythic_crypt_floor_", "mythic_astral_floor_", "giant_fortress_",
        "v0130_frontier_", "v018_endless_", "v020_mega_", "magitek_floor_",
        "uoss_deep_dungeon_floor_",
    )
    exit_count = 0
    for room_id, room in ROOMS.items():
        exits = room.get("exits", {}) or {}
        if isinstance(exits, dict):
            for direction, target in exits.items():
                exit_count += 1
                if target not in ROOMS:
                    if str(target).startswith(dynamic_prefixes):
                        dynamic_exits.append(f"{room_id}:{direction}->{target}")
                    else:
                        bad_exits.append(f"{room_id}:{direction}->{target}")
    if bad_exits:
        errors.append("invalid static room exits: " + ", ".join(bad_exits[:20]))
    if dynamic_exits:
        warnings.append(f"dynamic exit targets={len(dynamic_exits)} (validated by runtime generators)")

    # 2. Core catalogs.
    if len(CLASSES) != 22:
        errors.append(f"classes={len(CLASSES)}, expected 22")
    class_names = [row[0] for row in CLASSES]
    missing_skill_classes = [name for name in class_names if not CLASS_SKILLS.get(name)]
    if missing_skill_classes:
        errors.append("classes without skills: " + ", ".join(missing_skill_classes))
    if not ITEMS:
        errors.append("ITEMS is empty")
    if not MOB_TEMPLATES:
        errors.append("MOB_TEMPLATES is empty")
    if not QUESTS:
        errors.append("QUESTS is empty")

    # 3. Recipe integrity across all major recipe registries.
    recipe_sets = {
        "craft": CRAFT_RECIPES,
        "cook": COOK_RECIPES,
        "alchemy": ALCHEMY_RECIPES,
        "jewel": JEWELCRAFT_RECIPES,
        "extended": V03053_CRAFT_RECIPES,
    }
    recipe_count = 0
    for label, table in recipe_sets.items():
        for recipe_id, recipe in table.items():
            recipe_count += 1
            for item_id, qty in (recipe.get("ingredients", {}) or {}).items():
                if item_id not in ITEMS:
                    errors.append(f"{label}/{recipe_id}: missing ingredient {item_id}")
                if int(qty or 0) <= 0:
                    errors.append(f"{label}/{recipe_id}: invalid quantity {item_id}={qty}")
            output = recipe.get("output")
            if output and output not in ITEMS:
                errors.append(f"{label}/{recipe_id}: missing output {output}")

    # 4. Profession/tool mappings.
    expected_professions = {
        "fishing":"Wędkarstwo", "mining":"Górnictwo", "woodcutting":"Drwalstwo",
        "crafting":"Kowalstwo", "cooking":"Gotowanie", "herbalism":"Zielarstwo",
        "alchemy":"Alchemia", "jewelcrafting":"Jubilerstwo", "tailoring":"Krawiectwo",
        "leatherworking":"Garbarstwo", "carpentry":"Stolarstwo", "enchanting":"Zaklinanie",
    }
    for tool_type, profession in expected_professions.items():
        if TOOL_PROFESSION_MAP.get(tool_type) != profession:
            errors.append(f"tool/profession map {tool_type}->{TOOL_PROFESSION_MAP.get(tool_type)!r}, expected {profession}")
        if profession not in PROFESSION_RANK_NAMES:
            errors.append(f"missing rank names for {profession}")

    # 5. English command coverage for every newer Polish-only canonical command.
    english_aliases = {
        "tailoring":"krawiectwo", "sew":"szyj",
        "leatherworking":"garbarstwo", "tan":"garbuj",
        "carpentry":"stolarstwo", "woodcraft":"stolarka",
        "enchanting":"zaklinanie", "enchantitem":"zaklinaj",
        "craftingmastery":"craftmastery", "leaderboard":"leaderboards",
        "rankings":"leaderboards", "deathsummary":"deathrecap",
        "combatsummary":"combatrecap",
    }
    for alias, target in english_aliases.items():
        if COMMAND_ALIASES.get(alias) != target:
            errors.append(f"English command alias missing/wrong: {alias}->{COMMAND_ALIASES.get(alias)!r}, expected {target}")

    # 6. HELP integrity and current-system coverage.
    virtual_help = {"tematy", "komendy", "wszystko", "kategorie"}
    for alias, target in HELP_TOPIC_ALIASES.items():
        if target not in HELP_TOPICS and target not in virtual_help:
            errors.append(f"HELP alias without target: {alias}->{target}")
    required_help = {
        "krawiectwo", "garbarstwo", "stolarstwo", "zaklinanie",
        "jakosccraftu", "krytycznycraft", "craftmastery",
        "collection2", "completion2", "leaderboards2", "mentor2",
        "housing2", "transport2", "recaps", "loothistory2",
        "accessibility_presets", "social2",
    }
    for topic in sorted(required_help):
        rows = HELP_TOPICS.get(topic)
        if not rows:
            errors.append(f"missing current HELP topic: {topic}")

    # 7. Important data collisions worth reviewing, but not fatal.
    names = {}
    for item_id, item in ITEMS.items():
        name = normalize_lookup_text(item.get("name", ""))
        if name:
            names.setdefault(name, []).append(item_id)
    duplicate_names = {name: ids for name, ids in names.items() if len(ids) > 1}
    if duplicate_names:
        warnings.append(f"duplicate visible item names={len(duplicate_names)} (may be intentional variants)")

    return {
        "version": "0.30.55",
        "rooms": len(ROOMS),
        "exits": exit_count,
        "items": len(ITEMS),
        "mobs": len(MOB_TEMPLATES),
        "quests": len(QUESTS),
        "classes": len(CLASSES),
        "skills": sum(len(CLASS_SKILLS.get(name, ())) for name in class_names),
        "professions": len(PROFESSION_RANK_NAMES),
        "recipes": recipe_count,
        "help_topics": len(HELP_TOPICS),
        "help_aliases": len(HELP_TOPIC_ALIASES),
        "command_aliases": len(COMMAND_ALIASES),
        "warnings": warnings,
        "error_count": len(errors),
        "errors": errors,
    }


def full_game_predeploy_audit_v0336():
    errors=[]; warnings=[]; metrics={}
    def err(kind,*parts): errors.append((kind,*parts))

    # 1) Core registries and basic identity.
    registries={
        'rooms':ROOMS,'items':ITEMS,'mobs':MOB_TEMPLATES,'quests':QUESTS,
        'npcs':NPCS,'shops':SHOPS,'classes':CLASSES,'skills':CLASS_SKILLS,
        'help_topics':HELP_TOPICS,'help_aliases':HELP_TOPIC_ALIASES,
        'command_aliases':COMMAND_ALIASES,
    }
    for name,table in registries.items():
        metrics[name]=len(table)
        if not table: err('empty_registry',name)

    # 2) UTF-8/mojibake guard for runtime-visible text.
    bad_text_tokens=('\ufffd','Ã','Â','â€','â€™','ï¿½')
    def bad_text(value):
        s=str(value or '')
        return any(tok in s for tok in bad_text_tokens)
    for iid,it in ITEMS.items():
        for field in ('name','desc','rarity_name'):
            if bad_text(it.get(field,'')): err('mojibake_item',iid,field,it.get(field))
    for mid,mob in MOB_TEMPLATES.items():
        for field in ('name','desc'):
            if bad_text(mob.get(field,'')): err('mojibake_mob',mid,field,mob.get(field))
    for qid,q in QUESTS.items():
        for field in ('name','desc','description'):
            if bad_text(q.get(field,'')): err('mojibake_quest',qid,field,q.get(field))
    for rid,room in ROOMS.items():
        for field in ('name','desc'):
            if bad_text(room.get(field,'')): err('mojibake_room',rid,field,room.get(field))
    for topic,lines in HELP_TOPICS.items():
        if bad_text(topic): err('mojibake_help_topic',topic)
        if isinstance(lines,(list,tuple)):
            for line in lines:
                if bad_text(line): err('mojibake_help',topic,line)

    # 2b) Player-facing names that identify content must be globally unique
    # inside their own registry. This is especially important for NVDA navigation.
    for registry_name,table in (
        ('items',ITEMS),('mobs',MOB_TEMPLATES),('quests',QUESTS),('npcs',NPCS),('rooms',ROOMS)
    ):
        names={}
        for object_id,obj in table.items():
            name=str(obj.get('name') or '').strip()
            if not name:
                continue
            key=name.casefold()
            names.setdefault(key,[]).append(object_id)
        for key,object_ids in names.items():
            if len(object_ids)>1:
                err('duplicate_display_name',registry_name,key,tuple(object_ids))

    # 3) Rooms and exits.
    dynamic_prefixes=(
        'prof_','mine_floor_','crypt_floor_','astral_floor_','mythic_crypt_floor_',
        'mythic_astral_floor_','giant_fortress_','v0130_frontier_','v018_endless_',
        'v020_mega_','magitek_floor_','uoss_deep_dungeon_floor_',
        'eth_void_floor_','eth_holy_floor_','eth_shadow_floor_'
    )
    # Echo Labyrinth generates floors on demand, so static rooms legitimately
    # point at valid future room IDs. Only accept those IDs if the runtime
    # generator really is installed; a generic v1500_ prefix would hide bugs.
    from systems.echo_dungeon_v1500 import echo_identity
    from world.world_state import World
    echo_generator_ready = bool(getattr(World.ensure_infinite_dungeon_floor,
                                        '_v1500_echo', False))
    for rid,room in ROOMS.items():
        if not str(room.get('name') or '').strip(): err('room_missing_name',rid)
        for direction,target in (room.get('exits') or {}).items():
            if target in ROOMS or str(target).startswith(dynamic_prefixes):
                continue
            if echo_generator_ready and echo_identity(target) is not None:
                continue
            err('broken_exit',rid,direction,target)

    # 4) NPCs and shops.
    for nid,npc in NPCS.items():
        if not str(npc.get('name') or '').strip(): err('npc_missing_name',nid)
        room=npc.get('room')
        if room and room not in ROOMS: err('npc_missing_room',nid,room)
        for key in ('quest','specialist_quest'):
            qid=npc.get(key)
            if qid and qid not in QUESTS: err('npc_missing_quest',nid,key,qid)
        for qid in tuple(npc.get('quest_chain') or ()) + tuple(npc.get('specialist_quests') or ()):
            if qid not in QUESTS: err('npc_missing_quest',nid,'chain',qid)
    for shop_id,offers in SHOPS.items():
        for iid in offers or ():
            if iid not in ITEMS: err('shop_missing_item',shop_id,iid)
    for room_id,offers in CLASS_SHOP_ITEMS_BY_ROOM.items():
        if room_id not in ROOMS: err('class_shop_missing_room',room_id)
        for iid in offers or ():
            if iid not in ITEMS: err('class_shop_missing_item',room_id,iid)

    # 5) Item identity and player-facing names.
    technical_name_prefixes=('craftq_','item_','eq_','loot_')
    for iid,it in ITEMS.items():
        name=str(it.get('name') or '').strip()
        if not name: err('item_missing_name',iid)
        if name==str(iid) or name.lower().startswith(technical_name_prefixes):
            err('technical_item_name',iid,name)
        if 'price' in it:
            try:
                if int(it.get('price') or 0) < 0: err('negative_price',iid,it.get('price'))
            except Exception: err('invalid_price',iid,it.get('price'))

    # 6) Numeric item descriptions must equal post-generator runtime values.
    numeric_claims=0
    stat_patterns={
        'strength':r'Siła','dexterity':r'Zręczność','constitution':r'Kondycja',
        'intelligence':r'Inteligencja','willpower':r'Siła Woli','charisma':r'Charyzma'
    }
    for iid,it in ITEMS.items():
        desc=str(it.get('desc') or '')
        m=re.search(r'(?i)Obrona\s*\+\s*(-?\d+(?:[.,]\d+)?)',desc)
        if m:
            numeric_claims+=1
            stated=float(m.group(1).replace(',','.')); actual=float(it.get('defense',0) or 0)
            if abs(stated-actual)>1e-6: err('stale_item_defense_desc',iid,stated,actual)
        stats=dict(it.get('stats') or {}); affix=str(it.get('affix') or ''); affix_amount=it.get('affix_amount')
        for key,label in stat_patterns.items():
            for m in re.finditer(rf'(?i){label}\s*\+\s*(-?\d+(?:[.,]\d+)?)',desc):
                actual=stats.get(key)
                if actual is None and affix==key: actual=affix_amount
                if actual is None: continue
                numeric_claims+=1
                stated=float(m.group(1).replace(',','.'))
                if abs(stated-float(actual))>1e-6: err('stale_item_stat_desc',iid,key,stated,actual)
    metrics['numeric_item_claims_checked']=numeric_claims

    # 7) Mob drops.
    for mid,mob in MOB_TEMPLATES.items():
        if not str(mob.get('name') or '').strip(): err('mob_missing_name',mid)
        drops=mob.get('drops') or mob.get('loot') or {}
        if isinstance(drops,dict): iterable=drops.keys()
        else: iterable=drops
        for entry in iterable:
            iid=(entry.get('item') or entry.get('id')) if isinstance(entry,dict) else entry
            if iid and iid not in ITEMS: err('mob_missing_drop_item',mid,iid)

    # 7b) v0.71.1 final Crypt Soul Shard guarantee.  This is intentionally
    # checked after the full runtime has been assembled, because older fixes
    # could be overwritten by later Generator Core / Crypt balance passes.
    crypt_shard_checked = 0
    for mid, mob in MOB_TEMPLATES.items():
        try:
            crypt_floor = int(mob.get('crypt_floor', 0) or 0)
        except Exception:
            crypt_floor = 0
        try:
            mythic_floor = int(mob.get('mythic_crypt_floor', 0) or 0)
        except Exception:
            mythic_floor = 0
        is_crypt = bool(
            crypt_floor > 0 or mythic_floor > 0
            or mob.get('crypt_boss') or mob.get('mythic_crypt_boss')
            or str(mid) in ('skeleton', 'crypt_wraith')
        )
        if not is_crypt:
            continue
        crypt_shard_checked += 1
        drops = mob.get('drops') or {}
        try:
            chance = float(drops.get('soul_shard', 0) or 0)
        except Exception:
            chance = 0.0
        if chance < 1.0:
            err('crypt_soul_shard_not_guaranteed', mid, chance)
    metrics['crypt_soul_shard_templates_checked'] = crypt_shard_checked

    # 8) Recipes across every recipe registry.
    recipe_tables={
        'craft':CRAFT_RECIPES,'cook':COOK_RECIPES,'alchemy':ALCHEMY_RECIPES,
        'jewelcraft':JEWELCRAFT_RECIPES,'profession':V03053_CRAFT_RECIPES,
    }
    if 'TECH_CRAFT_RECIPES' in globals(): recipe_tables['tech']=TECH_CRAFT_RECIPES
    for table_name,table in recipe_tables.items():
        for rid,recipe in table.items():
            for iid,qty in (recipe.get('ingredients') or {}).items():
                if iid not in ITEMS: err('recipe_missing_ingredient',table_name,rid,iid)
                try:
                    if int(qty)<=0: err('recipe_bad_quantity',table_name,rid,iid,qty)
                except Exception: err('recipe_bad_quantity',table_name,rid,iid,qty)
            output=recipe.get('output')
            if output and output not in ITEMS: err('recipe_missing_output',table_name,rid,output)
    metrics['recipes_total']=sum(len(x) for x in recipe_tables.values())

    # 9) Quests: definitions, items, rewards and supported kinds.
    supported_kinds={
        'collect','collect_category','collect_distinct_category','collect_resource',
        'collect_resource_set','kill','deliver_npc','talk_npc','talk_class_teacher','craft_set','profession_action',
        'explore_frontier','discover_secret','mini_dungeon','world_event',
        'legendary_rare','world_boss','party_contract'
    }
    quest_kinds=set()
    for qid,q in QUESTS.items():
        if not str(q.get('name') or '').strip(): err('quest_missing_name',qid)
        kind=q.get('kind'); quest_kinds.add(kind)
        if kind not in supported_kinds: err('unsupported_quest_kind',qid,kind)
        try:
            if int(q.get('needed',1) or 0) < 0: err('quest_bad_needed',qid,q.get('needed'))
        except Exception: err('quest_bad_needed',qid,q.get('needed'))
        for field in ('item','item_id','required_item'):
            iid=q.get(field)
            if iid and isinstance(iid,str) and iid not in ITEMS: err('quest_missing_item',qid,field,iid)
        for field in ('accept_items','reward_items','required_items'):
            values=q.get(field) or {}
            if isinstance(values,dict):
                for iid,qty in values.items():
                    if iid not in ITEMS: err('quest_missing_item',qid,field,iid)
                    try:
                        if int(qty)<=0: err('quest_bad_item_qty',qid,field,iid,qty)
                    except Exception: err('quest_bad_item_qty',qid,field,iid,qty)
        if kind=='craft_set':
            req=q.get('craft_requirements') or q.get('requirements') or {}
            for iid,qty in req.items():
                if iid not in ITEMS: err('craft_set_missing_item',qid,iid)
                try:
                    if int(qty)<=0: err('craft_set_bad_qty',qid,iid,qty)
                except Exception: err('craft_set_bad_qty',qid,iid,qty)
        if kind=='party_contract':
            try:
                if int(q.get('minimum_party_size',0) or 0) < 2:
                    err('party_contract_bad_minimum_party_size',qid,q.get('minimum_party_size'))
            except Exception:
                err('party_contract_bad_minimum_party_size',qid,q.get('minimum_party_size'))
            if not q.get('repeatable'):
                err('party_contract_not_repeatable',qid)
            if str(q.get('target') or '') not in {'elite','boss','elemental','named_rare'}:
                err('party_contract_bad_target',qid,q.get('target'))
    metrics['quest_kinds']=tuple(sorted(str(x) for x in quest_kinds))

    # 9b) Collections, museum, sets, boss codex and achievements.
    if 'COLLECTION_V2_SET_GROUPS' in globals():
        for group_id,item_ids in COLLECTION_V2_SET_GROUPS.items():
            for iid in item_ids:
                if iid not in ITEMS: err('collection_set_missing_item',group_id,iid)
    if 'V0260_SET_PIECE_GROUPS' in globals():
        for group_id,slots in V0260_SET_PIECE_GROUPS.items():
            for slot,item_ids in slots.items():
                for iid in item_ids:
                    if iid not in ITEMS: err('museum_set_missing_item',group_id,slot,iid)
    if 'LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER' in globals():
        for cname,tiers in LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER.items():
            if cname not in CLASS_SKILLS: err('legendary_set_missing_class',cname)
            for tier,item_ids in tiers.items():
                for iid in item_ids:
                    if iid not in ITEMS: err('legendary_set_missing_item',cname,tier,iid)
    for table_name in ('V017_BIOME_SET_ITEMS','V021_MYTHIC_SET_ITEMS'):
        table=globals().get(table_name,{})
        for group_id,item_ids in table.items():
            for iid in item_ids:
                if iid not in ITEMS: err('set_missing_item',table_name,group_id,iid)
    if 'NAMED_LOOT_CATALOG' in globals():
        for iid in NAMED_LOOT_CATALOG:
            if iid not in ITEMS: err('named_loot_missing_item',iid)
    if 'WORLD_BOSS_UNIQUES' in globals():
        for iid in WORLD_BOSS_UNIQUES:
            if iid not in ITEMS: err('world_unique_missing_item',iid)
    if 'BOSS_COLLECTION_CATALOG' in globals():
        for mid in BOSS_COLLECTION_CATALOG:
            if mid not in MOB_TEMPLATES: err('boss_catalog_missing_mob',mid)
    if 'REGION_COLLECTION_ENTRIES' in globals():
        for region,entry in REGION_COLLECTION_ENTRIES.items():
            for mid in entry.get('bosses',()):
                if mid not in MOB_TEMPLATES: err('region_collection_missing_boss',region,mid)
    if 'CLASS_EQUIPMENT_SETS' in globals():
        for cname,spec in CLASS_EQUIPMENT_SETS.items():
            if cname not in CLASS_SKILLS: err('class_set_unknown_class',cname)
            room=spec.get('room')
            if room and room not in ROOMS: err('class_set_missing_room',cname,room)
    if 'ACHIEVEMENT_TITLE_REWARDS' in globals() and 'ACHIEVEMENT_TRACKS' in globals():
        for (track,tier),title in ACHIEVEMENT_TITLE_REWARDS.items():
            if track not in ACHIEVEMENT_TRACKS:
                err('achievement_title_missing_track',track,tier,title); continue
            valid_tiers={x[1] for x in ACHIEVEMENT_TRACKS[track].get('tiers',())}
            if tier not in valid_tiers: err('achievement_title_missing_tier',track,tier,title)

    # 9c) Professions, tools and progression tables.
    _expected_professions_v1112 = {
        'Wędkarstwo', 'Górnictwo', 'Drwalstwo', 'Zielarstwo',
        'Gotowanie', 'Alchemia', 'Kowalstwo', 'Jubilerstwo',
        'Krawiectwo', 'Garbarstwo', 'Stolarstwo', 'Zaklinanie',
        'Archeologia', 'Kartografia',
    }
    if set(PROFESSION_RANK_NAMES) != _expected_professions_v1112:
        err('profession_catalog_mismatch', tuple(sorted(PROFESSION_RANK_NAMES)), tuple(sorted(_expected_professions_v1112)))
    if len(TOOL_TIER_THRESHOLDS)!=TOOL_MAX_TIER or TOOL_MAX_TIER!=80: err('tool_tier_count',len(TOOL_TIER_THRESHOLDS))

    # 9d) Deep quest target/dependency validation for every quest.
    valid_kill_targets=set(MOB_TEMPLATES)
    for _mid,_mob in MOB_TEMPLATES.items():
        for _field in ('quest_target','quest_targets'):
            _value=_mob.get(_field)
            if isinstance(_value,str): valid_kill_targets.add(_value)
            elif isinstance(_value,(list,tuple,set)): valid_kill_targets.update(map(str,_value))
    valid_collect_categories={'fish','fish_river','fish_lake','fish_sea','fish_ocean','ore','wood','herb'}
    npc_display_names={str(_npc.get('name') or '').casefold() for _npc in NPCS.values()}
    for qid,q in QUESTS.items():
        kind=q.get('kind'); target=q.get('target')
        if kind in ('collect','collect_resource') and target not in ITEMS:
            err('quest_bad_target_item',qid,target)
        if kind in ('collect_category','collect_distinct_category') and target not in valid_collect_categories:
            err('quest_bad_category',qid,target)
        if kind=='kill' and target not in valid_kill_targets:
            # "*" is the intentional wildcard used by hourly class quests:
            # storage.db_quests.increment_quest accepts either the killed target
            # or "*" so these quests advance on any valid mob kill.
            dynamic_ok = target == "*"
            # v0.38.4: these aliases are authored for lazy-generated Infinite Magitek
            # templates, so they may have no static template before the first floor
            # is materialized. Their dedicated audit verifies runtime tagging.
            if target in ('magitek_infinite', 'magitek_elite') and callable(globals().get('create_infinite_magitek_floor_definition')):
                dynamic_ok=True
            if isinstance(target,str) and target.startswith('crypt_boss_'):
                try:
                    floor=int(target.rsplit('_',1)[1])
                    dynamic_ok=210<=floor<=SOUL_MAX_LEVEL and floor%10==0
                except Exception:
                    dynamic_ok=False
            if not dynamic_ok: err('quest_bad_kill_target',qid,target)
        if kind=='deliver_npc' and q.get('target_npc') not in NPCS:
            err('quest_bad_target_npc',qid,q.get('target_npc'))
        if q.get('quest_item') and q.get('quest_item') not in ITEMS:
            err('quest_bad_quest_item',qid,q.get('quest_item'))
        if q.get('requires_quest') and q.get('requires_quest') not in QUESTS:
            err('quest_bad_prerequisite',qid,q.get('requires_quest'))
        if q.get('required_profession') and q.get('required_profession') not in PROFESSION_RANK_NAMES:
            err('quest_bad_required_profession',qid,q.get('required_profession'))
        if q.get('reward_profession') and q.get('reward_profession') not in PROFESSION_RANK_NAMES:
            err('quest_bad_reward_profession',qid,q.get('reward_profession'))
        if q.get('reward_faction_v016') and q.get('reward_faction_v016') not in V016_FACTIONS:
            err('quest_bad_faction',qid,q.get('reward_faction_v016'))
        if q.get('repeatable') and int(q.get('repeat_cooldown',0) or 0)<=0:
            err('quest_bad_repeat_cooldown',qid,q.get('repeat_cooldown'))
        if kind=='collect_resource_set':
            req=dict(q.get('resource_targets') or {})
            if sum(int(v) for v in req.values()) != int(q.get('needed',0) or 0):
                err('quest_resource_set_needed_mismatch',qid,q.get('needed'),req)
            for iid,qty in req.items():
                if iid not in ITEMS: err('quest_resource_set_missing_item',qid,iid)
                if int(qty)<=0: err('quest_resource_set_bad_qty',qid,iid,qty)
        if kind=='craft_set':
            targets=tuple(q.get('targets') or ())
            if len(targets) != int(q.get('needed',0) or 0):
                err('quest_craft_set_needed_mismatch',qid,q.get('needed'),len(targets))
            for iid in targets:
                if iid not in ITEMS: err('quest_craft_set_missing_item',qid,iid)
        giver=str(q.get('giver') or '').strip()
        if giver and giver.casefold() not in npc_display_names and giver!='Tablica Godzinnych Zleceń':
            err('quest_unknown_giver',qid,giver)

    # Prerequisite graph must be acyclic.
    _visited=set(); _stack=set()
    def _visit_quest_dep_v0336(qid):
        if qid in _stack:
            err('quest_prerequisite_cycle',qid); return
        if qid in _visited: return
        _visited.add(qid); _stack.add(qid)
        dep=QUESTS[qid].get('requires_quest')
        if dep in QUESTS: _visit_quest_dep_v0336(dep)
        _stack.remove(qid)
    for _qid in QUESTS: _visit_quest_dep_v0336(_qid)

    # 9e) v0.34.1 Blacksmithing NPC resale must not multiply raw ore value.
    _smith_rows_checked=0
    try:
        _smith_dummy=object.__new__(Session)
        for _tier in BLACKSMITH_TIERS:
            _ore=ITEMS.get(str(_tier.get('ore')), {})
            _ore_value=legacy_currency_to_coins(
                _ore.get('sell_silver',0), _ore.get('sell_gold',0), _ore.get('sell_mithril',0)
            )
            if _ore_value<=0:
                err('blacksmith_ore_without_sale_value',_tier.get('key'),_tier.get('ore')); continue
            for _slot,_slot_row in BLACKSMITH_SLOT_DEFS.items():
                _iid=f"smith_{_tier['key']}_{_slot}"
                _item=ITEMS.get(_iid)
                if not _item:
                    err('blacksmith_missing_crafted_item',_iid); continue
                _cost=max(1,int(_slot_row[2] or 1))
                _material_value=_ore_value*_cost
                _sale=Session.generic_item_sale_value(_smith_dummy,_iid,_item)
                _sale_value=legacy_currency_to_coins(_sale.get('silver',0),_sale.get('gold',0),_sale.get('mithril',0))
                _max_normal=int(_material_value*0.90)
                if _sale_value>_max_normal:
                    err('blacksmith_normal_resale_too_high',_iid,_sale_value,_max_normal,_material_value)
                _smith_rows_checked+=1
    except Exception as _exc:
        err('blacksmith_economy_audit_exception',repr(_exc))
    metrics['blacksmith_resale_rows_checked']=_smith_rows_checked

    # 9f) v0.34.4 Currency economy + Mithril mining gate.
    # One wallet uses silver as the canonical unit; gold/mithril are display denominations.
    if int(SILVER_PER_GOLD) != 100:
        err('currency_ratio_silver_gold',SILVER_PER_GOLD,100)
    if int(GOLD_PER_MITHRIL) != 1000000:
        err('currency_ratio_gold_mithril',GOLD_PER_MITHRIL,1000000)
    if int(SILVER_PER_MITHRIL) != 100000000:
        err('currency_ratio_silver_mithril',SILVER_PER_MITHRIL,100000000)

    _mob_split=0; _quest_split=0
    _max_mob_currency=0; _max_quest_currency=0; _repeatable_count=0; _max_repeatable=0
    for _mid,_mob in MOB_TEMPLATES.items():
        _silver=int(_mob.get('silver',0) or 0)
        _max_mob_currency=max(_max_mob_currency,_silver)
        if int(_mob.get('gold',0) or 0) or int(_mob.get('mithril',0) or 0):
            _mob_split+=1; err('mob_split_currency_not_normalized',_mid,_mob.get('gold'),_mob.get('mithril'))
    for _qid,_q in QUESTS.items():
        _coins=int(_q.get('reward_silver',0) or 0)
        _max_quest_currency=max(_max_quest_currency,_coins)
        if bool(_q.get('repeatable')) or int(_q.get('cooldown_seconds',0) or 0)>0:
            _repeatable_count+=1; _max_repeatable=max(_max_repeatable,_coins)
        if int(_q.get('reward_gold',0) or 0) or int(_q.get('reward_mithril',0) or 0):
            _quest_split+=1; err('quest_split_currency_not_normalized',_qid,_q.get('reward_gold'),_q.get('reward_mithril'))
    metrics['currency_mob_split_count']=_mob_split
    metrics['currency_quest_split_count']=_quest_split
    metrics['currency_max_mob_reward']=_max_mob_currency
    metrics['currency_max_quest_reward']=_max_quest_currency
    metrics['currency_repeatable_quests']=_repeatable_count
    metrics['currency_max_repeatable_quest_reward']=_max_repeatable

    # Real shop offers only, with the maximum Charisma cashback applied: no buy -> sell profit loop.
    _shop_ids=set()
    for _offers in SHOPS.values():
        _shop_ids.update(_offers or ())
    for _offers in CLASS_SHOP_ITEMS_BY_ROOM.values():
        _shop_ids.update(_offers or ())
    _shop_arbitrage=[]
    try:
        _economy_dummy=object.__new__(Session)
        _max_discount=max(0,min(100,int(CHARISMA_MAX_DISCOUNT or 0)))
        for _iid in sorted(_shop_ids):
            _item=ITEMS.get(_iid)
            if not _item:
                continue
            _buy=int(Session.shop_item_base_value_silver(_economy_dummy,_item) or 0)
            if _buy<=0:
                continue
            _effective_buy=max(0,_buy-((_buy*_max_discount)//100))
            _sale=Session.generic_item_sale_value(_economy_dummy,_iid,_item)
            _sell=legacy_currency_to_coins(
                _sale.get('silver',0),_sale.get('gold',0),_sale.get('mithril',0)
            )
            if _sell>_effective_buy:
                _shop_arbitrage.append((_iid,_effective_buy,_sell))
                err('shop_buy_sell_arbitrage',_iid,_effective_buy,_sell,_max_discount)
    except Exception as _exc:
        err('currency_shop_audit_exception',repr(_exc))
    metrics['currency_shop_items_checked']=len(_shop_ids)
    metrics['currency_shop_arbitrage_count']=len(_shop_arbitrage)
    metrics['currency_max_charisma_discount']=int(CHARISMA_MAX_DISCOUNT or 0)

    _max_explicit_sell=0
    for _iid,_item in ITEMS.items():
        _value=legacy_currency_to_coins(
            _item.get('sell_silver',0),_item.get('sell_gold',0),_item.get('sell_mithril',0)
        )
        _max_explicit_sell=max(_max_explicit_sell,int(_value or 0))
    metrics['currency_max_explicit_item_sell']=_max_explicit_sell

    # v0.34.4: Mithril is a currency bonus from mining, never an ore resource.
    if 'mithril_ore' in ORE_RESOURCE_IDS:
        err('mithril_ore_must_not_be_active_resource')
    if 'mithril_ore' in ORE_ATLAS_ALL:
        err('mithril_ore_must_not_be_in_atlas')
    if 'mithril_ore' in ORE_ATLAS_LEVELS or 'mithril_ore' in ORE_MINE_FLOOR_MINIMUMS:
        err('mithril_ore_must_not_have_unlock_threshold')
    _mithril_chance_79=mining_mithril_currency_chance(79,79,79)
    _mithril_chance_80=mining_mithril_currency_chance(80,80,80)
    _mithril_chance_400=mining_mithril_currency_chance(400,400,400)
    _mithril_chance_600=mining_mithril_currency_chance(600,600,600)
    if _mithril_chance_79 != 0:
        err('mithril_currency_unlock_too_early',_mithril_chance_79)
    if not (0.0049 <= _mithril_chance_80 <= 0.0051):
        err('mithril_currency_level80_chance',_mithril_chance_80)
    _mithril_chance_800=mining_mithril_currency_chance(800,800,800)
    if not (0.0199 <= _mithril_chance_800 <= 0.0201):
        err('mithril_currency_level800_chance',_mithril_chance_800)
    metrics['mithril_currency_chance_level80']=_mithril_chance_80
    metrics['mithril_currency_chance_level400']=_mithril_chance_400
    metrics['mithril_currency_chance_level600']=_mithril_chance_600

    # Audit authored ore weighting: newly unlocked core ores must be meaningfully
    # visible, while older ores remain possible.
    _ore_drop_checks=(
        (50,'gold_ore'),(100,'cobalt_ore'),(120,'runestone_ore'),
        (140,'dragonsteel_ore'),(160,'astral_ore'),(180,'void_ore'),
        (200,'eternium_ore'),(220,'ore_400_220'),(400,'ore_400_400'),
    )
    _ore_drop_metrics={}
    for _level,_ore_id in _ore_drop_checks:
        _pool=[]
        for _iid in ORE_RESOURCE_IDS:
            if _iid not in ITEMS:
                continue
            if int(ORE_ATLAS_LEVELS.get(_iid,1) or 1) <= _level and int(ORE_MINE_FLOOR_MINIMUMS.get(_iid,1) or 1) <= _level:
                _pool.append(_iid)
        _weights=mining_ore_weights(_pool,_level,f'audit:mine_floor_{_level}')
        _total=sum(_weights) or 1.0
        _prob=0.0
        if _ore_id in _pool:
            _prob=float(_weights[_pool.index(_ore_id)])/_total
        _ore_drop_metrics[_ore_id]=round(_prob,6)
        if _prob < 0.08:
            err('current_tier_ore_too_rare',_level,_ore_id,_prob)
    metrics['mining_current_ore_probabilities']=_ore_drop_metrics
    try:
        metrics['currency_guild_upgrade_1_400']=sum(int(v0926_guild_upgrade_cost(_lvl) or 0) for _lvl in range(1,V0926_GUILD_MAX_LEVEL))
    except Exception as _exc:
        warnings.append(('guild_currency_sink_metric_unavailable',repr(_exc)))

    # 10) Skills/spells: no duplicate display names, no numeric disambiguators.
    seen_skill_names={}; skill_count=0
    for cname,rows in CLASS_SKILLS.items():
        for skill in rows:
            skill_count+=1
            name=str(skill.get('name') or '').strip()
            if not name: err('skill_missing_name',cname,skill.get('id'))
            key=normalize_lookup_text(name)
            seen_skill_names.setdefault(key,[]).append((cname,skill.get('id'),name))
            if re.search(r'\d',name): err('skill_numeric_name',cname,skill.get('id'),name)
            try:
                unlock=int(skill.get('unlock',0) or 0)
                if not 1<=unlock<=CLASS_MASTERY_MAX_LEVEL: err('skill_bad_unlock',cname,skill.get('id'),unlock)
            except Exception: err('skill_bad_unlock',cname,skill.get('id'),skill.get('unlock'))
    for key,rows in seen_skill_names.items():
        if len(rows)>1: err('duplicate_skill_name',key,rows)
    metrics['skills_total']=skill_count

    # v0.35.3: Hunter/combat regression gate. Offensive Hunter skills must keep
    # their authored Dexterity scaling, and Soul Weapon trait_totals must never
    # leak into use_class_skill (traits belong only to the basic weapon attack).
    _hunter_rows=list(CLASS_SKILLS.get('Łowca') or [])
    _hunter_supported={'damage','drain','execute','aoe_damage','heal','group_heal','guard','evade','boost','passive'}
    _hunter_aliases={}
    _hunter_alias_collisions=[]
    for _skill in _hunter_rows:
        _sid=str(_skill.get('id') or '')
        _kind=str(_skill.get('kind') or '')
        if _kind not in _hunter_supported:
            err('hunter_unsupported_kind',_sid,_kind)
        if _kind in {'damage','drain','execute','aoe_damage'}:
            if _skill.get('scale') != 'dexterity':
                err('hunter_bad_scale',_sid,_skill.get('scale'))
            for _field in ('scale','mult'):
                if _field not in _skill:
                    err('hunter_missing_field',_sid,_field)
        if _kind == 'execute' and 'execute_mult' not in _skill:
            err('hunter_missing_field',_sid,'execute_mult')
        if _kind == 'boost' and 'boost' not in _skill:
            err('hunter_missing_field',_sid,'boost')
        for _form in [str(_skill.get('name') or '')] + list(_skill.get('aliases') or []):
            _norm=normalize_lookup_text(_form)
            if not _norm:
                continue
            _prev=_hunter_aliases.get(_norm)
            if _prev and _prev != _sid:
                _hunter_alias_collisions.append((_form,_prev,_sid))
            else:
                _hunter_aliases[_norm]=_sid
    for _row in _hunter_alias_collisions:
        err('hunter_alias_collision',*_row)
    metrics['hunter_skills_checked']=len(_hunter_rows)
    metrics['hunter_alias_collisions']=len(_hunter_alias_collisions)
    try:
        _use_body=_sb420_view(_ROOT/'player/session_mixins/combat_skills.py')
        if 'trait_totals' in _use_body:
            err('soul_weapon_trait_leak_into_skills')
    except Exception as _exc:
        err('combat_skill_source_audit_failed',repr(_exc))

    # 10b) v0.35.3 Soul Weapon Mastery + Main Menu Exit gate.
    try:
        if int(SOUL_WEAPON_MASTERY_MAX_LEVEL) != 800:
            err('soul_weapon_mastery_bad_cap',SOUL_WEAPON_MASTERY_MAX_LEVEL)
        _m1=soul_weapon_mastery_bonuses(1)
        _m200=soul_weapon_mastery_bonuses(200)
        _m400=soul_weapon_mastery_bonuses(400)
        _m600=soul_weapon_mastery_bonuses(600)
        _m800=soul_weapon_mastery_bonuses(800)
        if any(float(_m1.get(k,0) or 0) != 0.0 for k in ('damage_percent','crit_chance','crit_damage_percent','boss_damage_percent','echo_chance')):
            err('soul_weapon_mastery_level1_not_neutral',_m1)
        if not (0.0099 <= float(_m200.get('echo_chance',0) or 0) <= 0.0101):
            err('soul_weapon_mastery_echo_200',_m200.get('echo_chance'))
        if abs(float(_m800.get('damage_percent',0))-8.0)>0.0001:
            err('soul_weapon_mastery_damage_800',_m600.get('damage_percent'))
        if abs(float(_m800.get('crit_chance',0))-0.02)>0.000001:
            err('soul_weapon_mastery_crit_800',_m600.get('crit_chance'))
        if abs(float(_m800.get('crit_damage_percent',0))-12.0)>0.0001:
            err('soul_weapon_mastery_crit_damage_800',_m600.get('crit_damage_percent'))
        if abs(float(_m800.get('boss_damage_percent',0))-5.0)>0.0001:
            err('soul_weapon_mastery_boss_800',_m600.get('boss_damage_percent'))
        if abs(float(_m800.get('echo_chance',0))-0.05)>0.000001:
            err('soul_weapon_mastery_echo_800',_m600.get('echo_chance'))
        _basic_body=_sb420_view(_ROOT/'player/session_mixins/combat_realtime.py')
        if 'grant_soul_weapon_mastery_hit_xp' not in _basic_body:
            err('soul_weapon_mastery_missing_basic_attack_xp')
        _use_body=_sb420_view(_ROOT/'player/session_mixins/combat_skills.py')
        if 'grant_soul_weapon_mastery_hit_xp' in _use_body or 'soul_weapon_mastery_bonuses' in _use_body:
            err('soul_weapon_mastery_leaked_into_skills')
        _auth_source=_sb420_view(_ROOT/'player/session_mixins/io_auth_character.py')
        if 'await self.close_from_main_menu()' not in _auth_source or 'self.writer.close()' not in _auth_source:
            err('main_menu_exit_not_explicit_close')
        _db_source='\n'.join(((_ROOT/'storage/db_schema.py').read_text(encoding='utf-8'), (_ROOT/'storage/schema_migrate_character.py').read_text(encoding='utf-8')))
        for _column in ('soul_weapon_mastery_level','soul_weapon_mastery_xp'):
            if _column not in _db_source:
                err('soul_weapon_mastery_db_column_missing',_column)
        metrics['soul_weapon_mastery_cap']=int(SOUL_WEAPON_MASTERY_MAX_LEVEL)
        metrics['soul_weapon_mastery_bonus_400']=dict(_m400)
    except Exception as _exc:
        err('soul_weapon_mastery_audit_exception',repr(_exc))

    # 10c) v0.35.3 profession automation / identifier regression gate.
    # The v0.35.0 Polish Pass accidentally changed some Python identifiers
    # from ``level`` to ``poziom`` while leaving references to the other name.
    # That produced NameError inside gathering XP and silently killed auto tasks.
    try:
        import ast as _ast
        _identifier_mismatches=[]
        _functions_checked=0
        for _path in sorted(_ROOT.rglob('*.py')):
            # Ignore generated bytecode/cache trees if a local developer has them.
            if '__pycache__' in _path.parts:
                continue
            try:
                _tree=_ast.parse(_path.read_text(encoding='utf-8'), filename=str(_path))
            except Exception as _exc:
                err('python_source_parse_failed',str(_path.relative_to(_ROOT)),repr(_exc))
                continue
            for _node in _ast.walk(_tree):
                if not isinstance(_node,(_ast.FunctionDef,_ast.AsyncFunctionDef)):
                    continue
                _functions_checked += 1
                _params={_a.arg for _a in list(_node.args.args)+list(_node.args.kwonlyargs)}
                _stores=set(_params)
                _loads=set()
                for _child in _ast.walk(_node):
                    if isinstance(_child,_ast.Name):
                        if isinstance(_child.ctx,(_ast.Store,_ast.Param)):
                            _stores.add(_child.id)
                        elif isinstance(_child.ctx,_ast.Load):
                            _loads.add(_child.id)
                if 'level' in _stores and 'poziom' in _loads and 'poziom' not in _stores:
                    _identifier_mismatches.append((str(_path.relative_to(_ROOT)),_node.name,'local_level_load_poziom'))
                if 'poziom' in _stores and 'level' in _loads and 'level' not in _stores:
                    _identifier_mismatches.append((str(_path.relative_to(_ROOT)),_node.name,'local_poziom_load_level'))
        for _row in _identifier_mismatches:
            err('level_poziom_identifier_mismatch',*_row)
        metrics['python_functions_identifier_checked']=_functions_checked
        metrics['level_poziom_identifier_mismatches']=len(_identifier_mismatches)

        _prof_source=_sb420_view(_ROOT/'player/session_mixins/gathering.py')
        _auto_specs=(
            ('auto_fishing_loop','set_auto_fishing','AUTO_FISHING_ERROR'),
            ('auto_mining_loop','set_auto_mining','AUTO_MINING_ERROR'),
            ('auto_woodcutting_loop','set_auto_woodcutting','AUTO_WOODCUTTING_ERROR'),
            ('auto_herbalism_loop','set_auto_herbalism','AUTO_HERBALISM_ERROR'),
        )
        for _fn,_next_fn,_tag in _auto_specs:
            _start=_prof_source.find(f'    async def {_fn}(')
            _end=_prof_source.find(f'    async def {_next_fn}(',_start+1)
            if _start < 0 or _end < 0:
                err('auto_profession_loop_missing',_fn)
                continue
            _body=_prof_source[_start:_end]
            if 'except Exception as exc:' not in _body or _tag not in _body:
                err('auto_profession_loop_silent_failure_guard_missing',_fn)
        metrics['auto_profession_loops_guarded']=len(_auto_specs)
    except Exception as _exc:
        err('profession_automation_regression_audit_exception',repr(_exc))

    # 11) HELP aliases and nonempty topics.
    virtual={'tematy','komendy','wszystko','kategorie'}
    for alias,target in HELP_TOPIC_ALIASES.items():
        if target not in HELP_TOPICS and target not in virtual: err('help_alias_missing_target',alias,target)
    for topic,lines in HELP_TOPICS.items():
        if not lines: err('empty_help_topic',topic)

    # 11b) v0.35.3 polish regression gate: keep internal release labels and
    # stale caps out of normal player-facing runtime text.
    try:
        _polish_files=(
            'player/session_mixins/quest_progress.py',
            'player/session_mixins/quest_offers.py',
            'player/session_mixins/quest_turnin.py',
            'player/session_mixins/quest_npc.py',
            'player/session_mixins/quest_commands.py',
            'player/session_mixins/progression_accessibility.py',
            'player/session_mixins/milestone.py',
            'player/session_mixins/crafting.py',
            'player/session_mixins/inventory_equipment.py',
            'player/session_mixins/shops_teachers.py',
            'player/session_mixins/crafting_expansion.py',
            'player/session_mixins/tech_crafting.py',
            'player/session_mixins/museum_bounty.py',
            'player/session_mixins/world_events_endgame.py',
            'player/session_mixins/exploration_progress.py',
            'player/session_mixins/collection_loot_records.py',
            'player/session_mixins/social_expansion.py',
            'player/session_mixins/courier_delivery.py',
            'player/session_mixins/admin_tools.py',
            'player/session_mixins/gathering_actions.py',
            'player/session_mixins/sales.py',
            'player/session_mixins/forge_guilds.py',
            'systems/content_registry.py',
        )
        _polish_source='\n'.join((_ROOT/_rel).read_text(encoding='utf-8') for _rel in _polish_files)
        _forbidden_ui=(
            'QUEST LIST:', 'QUEST INFO:', 'AKTYWNE QUESTY:', 'UKOŃCZONE QUESTY:',
            'COLLECTION CODEX 2.0', 'LOOT HISTORY 2.0', 'DEATH RECAP:',
            'COMBAT RECAP:', 'PARTY QUEST PROGRESS 2.0', 'SALVAGE 3.0:',
            'REFINING 2.0', 'MACHINE SALVAGE 2.0', 'FISHING RECORDS 2.0',
            'DYNAMICZNE EVENTY v0.29', 'MITYCZNA PROGRESJA v0.21',
            'COLLECTION CODEX — ŚWIAT v0.15',
            'poziomy Gildii 1-100', 'maksymalnie +11% do Biegłości',
        )
        for _token in _forbidden_ui:
            if _token in _polish_source:
                err('stale_player_ui_token',_token)
        metrics['polish_ui_tokens_checked']=len(_forbidden_ui)
    except Exception as _exc:
        err('polish_source_audit_failed',repr(_exc))

    # 12) Static code-integrity gate for assembled runtime.
    # Check method references across every Session mixin, plus the main runtime
    # collaborators used through self.server/db/world/character. This catches
    # rare-path typos that normal startup cannot execute (e.g. a single Mec proc
    # or an admin-only command).
    try:
        import ast as _ast_code
        _session_called=set()
        _db_called=set()
        _world_called=set()
        _server_called=set()
        _character_called=set()
        _session_files=list((_ROOT/'player/session_mixins').glob('*.py'))+[(_ROOT/'player/session.py')]
        for _path in _session_files:
            _tree=_ast_code.parse(_path.read_text(encoding='utf-8'), filename=str(_path))
            for _node in _ast_code.walk(_tree):
                if not isinstance(_node,_ast_code.Call) or not isinstance(_node.func,_ast_code.Attribute):
                    continue
                _attr=_node.func.attr
                _value=_node.func.value
                if isinstance(_value,_ast_code.Name) and _value.id=='self':
                    _session_called.add(_attr)
                    continue
                # self.character.foo(...)
                if (isinstance(_value,_ast_code.Attribute) and _value.attr=='character'
                        and isinstance(_value.value,_ast_code.Name) and _value.value.id=='self'):
                    _character_called.add(_attr); continue
                # self.server.foo(...)
                if (isinstance(_value,_ast_code.Attribute) and _value.attr=='server'
                        and isinstance(_value.value,_ast_code.Name) and _value.value.id=='self'):
                    _server_called.add(_attr); continue
                # self.server.db.foo(...) / self.server.world.foo(...)
                if isinstance(_value,_ast_code.Attribute) and _value.attr in ('db','world'):
                    _base=_value.value
                    if (isinstance(_base,_ast_code.Attribute) and _base.attr=='server'
                            and isinstance(_base.value,_ast_code.Name) and _base.value.id=='self'):
                        (_db_called if _value.attr=='db' else _world_called).add(_attr)
        for _name in sorted(_session_called):
            if not hasattr(Session,_name): err('missing_session_method_reference',_name)
        for _name in sorted(_db_called):
            if not hasattr(Database,_name): err('missing_database_method_reference',_name)
        for _name in sorted(_world_called):
            if not hasattr(World,_name): err('missing_world_method_reference',_name)
        for _name in sorted(_server_called):
            if not hasattr(MudServer,_name): err('missing_server_method_reference',_name)
        for _name in sorted(_character_called):
            if not hasattr(Character,_name): err('missing_character_method_reference',_name)
        metrics['session_methods_called_checked']=len(_session_called)
        metrics['database_methods_called_checked']=len(_db_called)
        metrics['world_methods_called_checked']=len(_world_called)
        metrics['server_methods_called_checked']=len(_server_called)
        metrics['character_methods_called_checked']=len(_character_called)

        # MRO regression gate: newer extensions must remain the active methods,
        # while they can explicitly delegate to their older compatibility layer.
        _expected_owners={
            'salvage_equipment_v0925':SessionCraftingExpansionV03114Mixin,
            'tell':SessionSocialExpansionMixin,
            'who':SessionSocialExpansionMixin,
            'channel_broadcast_v03050':SessionSocialExpansionMixin,
            'show_channels_v03050':SessionSocialExpansionMixin,
        }
        for _name,_owner in _expected_owners.items():
            _resolved=getattr(Session,_name,None)
            _expected=getattr(_owner,_name,None)
            if _resolved is not _expected:
                err('session_mro_shadowing_regression',_name,getattr(_resolved,'__qualname__',None),getattr(_expected,'__qualname__',None))
        metrics['mro_resolution_checks']=len(_expected_owners)

        # Long-lived background loops must survive an unexpected iteration error.
        _server_source=(_ROOT/'server/mud_server.py').read_text(encoding='utf-8')
        for _fn,_tag in (('double_xp_event_loop','DOUBLE XP LOOP ERROR'),('mob_wander_loop','MOB WANDER LOOP ERROR')):
            _start=_server_source.find(f'    async def {_fn}(')
            _next=_server_source.find('    async def ',_start+1)
            _body=_server_source[_start:(_next if _next>_start else len(_server_source))]
            if 'except Exception as exc:' not in _body or _tag not in _body:
                err('background_loop_guard_missing',_fn)
        _core_source=(_ROOT/'player/session_mixins/rest_mana.py').read_text(encoding='utf-8')
        _start=_core_source.find('    async def rest_loop(')
        _next=_core_source.find('    async def ',_start+1)
        _body=_core_source[_start:(_next if _next>_start else len(_core_source))]
        if 'except Exception as exc:' not in _body or 'REST_LOOP_ERROR' not in _body:
            err('background_loop_guard_missing','rest_loop')
        metrics['background_loop_guards_checked']=3
    except Exception as _exc:
        err('code_integrity_gate_exception',repr(_exc))

    return {
        'version':'0.35.6','error_count':len(errors),'warning_count':len(warnings),
        'errors':errors,'warnings':warnings,'metrics':metrics,
        'description_sync':dict(ITEM_DESCRIPTION_SYNC_V0336),
    }


# -*- coding: utf-8 -*-
"""v4.00.6: isolated historical audit rule bodies.

No runtime imports, no catalog mutation during module import. Dependencies
are received from admin/audits.py at the ORIGINAL call site and time.
"""


def generator_numeric_only_audit_v03018(*, CATALOG_VALIDATION_AUDIT, SOUL_MILESTONE_TIERS, CLASS_MASTERY_MAX_LEVEL, CLASS_SKILLS, ITEMS):
    audit = CATALOG_VALIDATION_AUDIT or {}
    errors = []
    if not audit.get("numeric_only"):
        errors.append("Generator Core numeric_only flag missing")
    if not audit.get("runtime_fast_path") and not audit.get("semantic_preserved"):
        errors.append("Generator Core changed protected authored semantics")
    # Explicit regression guards for semantics previously overwritten by Generator Core.
    if tuple(SOUL_MILESTONE_TIERS) != (5, 10, 15, 20):
        errors.append(f"Soul Milestones changed: {SOUL_MILESTONE_TIERS}")
    skill_grid = {1, *range(10, CLASS_MASTERY_MAX_LEVEL + 1, 10)}
    for cname, rows in CLASS_SKILLS.items():
        if cname in ("Inżynier","Mec"):
            if any(not 1 <= int(s.get("unlock", 0) or 0) <= CLASS_MASTERY_MAX_LEVEL for s in rows):
                errors.append(f"skill unlock range changed: {cname}")
            continue
        if any(int(s.get("unlock", 0) or 0) not in skill_grid for s in rows):
            errors.append(f"skill unlock grid changed: {cname}")
    # Generator is forbidden to invent equipment mastery requirements.
    missing_currency = sum(1 for item in ITEMS.values() if item.get("currency") is None)
    return {
        "version": "0.30.18",
        "error_count": len(errors),
        "errors": errors,
        "semantic_preserved": bool(audit.get("semantic_preserved")),
        "semantic_fingerprint": audit.get("semantic_fingerprint_after"),
        "numeric_only": bool(audit.get("numeric_only")),
        "authored_soul_milestones": tuple(SOUL_MILESTONE_TIERS),
        "items_without_explicit_currency": missing_currency,
    }


def generator_whitelist_audit_v03019(*, CATALOG_VALIDATION_AUDIT, BALANCE_MATH_VERSION):
    audit = CATALOG_VALIDATION_AUDIT or {}
    whitelist = audit.get("whitelist_audit") or {}
    errors = []
    if not audit.get("numeric_only"):
        errors.append("numeric_only flag missing")
    runtime_fast = bool(audit.get("runtime_fast_path"))
    if not runtime_fast:
        if not audit.get("semantic_preserved"):
            errors.append("semantic fingerprint changed")
        if not audit.get("whitelist_enforced"):
            errors.append("whitelist_enforced flag missing")
        if not audit.get("whitelist_passed"):
            errors.extend(whitelist.get("errors") or ["numeric whitelist failed"])
    required_tables = {
        "ROOMS", "MOB_TEMPLATES", "ITEMS", "QUESTS", "CLASS_SKILLS",
        "CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES",
    }
    actual_tables = set((whitelist.get("record_whitelist") or {}).keys())
    if not runtime_fast:
        missing = sorted(required_tables - actual_tables)
        if missing:
            errors.append("whitelist missing tables: " + ", ".join(missing))
    return {
        "version": "0.30.19",
        "generator_version": str(BALANCE_MATH_VERSION),
        "whitelist_enforced": bool(audit.get("whitelist_enforced")),
        "whitelist_passed": bool(audit.get("whitelist_passed")),
        "semantic_preserved": bool(audit.get("semantic_preserved")),
        "numeric_values_checked": int(whitelist.get("numeric_values_checked", 0) or 0),
        "record_tables": tuple(sorted(actual_tables)),
        "nested_value_tables": tuple(sorted((whitelist.get("nested_value_whitelist") or {}).keys())),
        "top_level_domains": tuple(whitelist.get("top_level_value_whitelist") or ()),
        "error_count": len(errors),
        "errors": errors,
    }


def equipment_expansion_audit_v03020(*, CLASS_EQUIPMENT_SLOT_DEFS, EQUIPMENT_SLOT_NAMES, COMMAND_ALIASES, CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER, ITEMS):
    errors = []
    required_slots = {"shoulders", "belt", "cloak", "bracers", "bracelet", "accessory", "relic"}
    if not required_slots.issubset(CLASS_EQUIPMENT_SLOT_DEFS):
        errors.append("missing new class EQ slots: " + ", ".join(sorted(required_slots - set(CLASS_EQUIPMENT_SLOT_DEFS))))
    if not required_slots.issubset(EQUIPMENT_SLOT_NAMES):
        errors.append("missing new slot display names")
    expected_commands = {
        "zp":"equipringauto", "zt":"equipcharmauto", "znar":"equipshoulders",
        "zpas":"equipbelt", "zpel":"equipcloak", "zkar":"equipbracers",
        "zbra":"equipbracelet", "zakc":"equipaccessoryauto", "zrel":"equiprelic",
    }
    for alias, command in expected_commands.items():
        if COMMAND_ALIASES.get(alias) != command:
            errors.append(f"shortcut {alias} -> {COMMAND_ALIASES.get(alias)!r}, expected {command!r}")
    # Every class/tier should expose the complete logical equipment grid per style.
    logical_slots = set(CLASS_EQUIPMENT_SLOT_DEFS)
    for class_name, tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        for mastery in (1, 100, 200, 400, 600):
            ids = tiers.get(mastery, ())
            present = {ITEMS[i].get("slot") for i in ids if i in ITEMS}
            if not logical_slots.issubset(present):
                errors.append(f"{class_name} mastery {mastery}: missing slots {sorted(logical_slots-present)}")
                break
    return {
        "version":"0.30.20",
        "logical_slot_count":len(logical_slots),
        "new_slots":tuple(sorted(required_slots)),
        "error_count":len(errors),
        "errors":errors,
    }


def currency_economy_audit_v03021(*, SILVER_PER_GOLD, SILVER_PER_MITHRIL, currency_reading_text, QUESTS, v0190_quest_currency_reward, ITEMS):
    errors=[]
    formatter_tests={
        SILVER_PER_GOLD-1:f"{SILVER_PER_GOLD-1} srebra",
        SILVER_PER_GOLD:"1 złota",
        2*SILVER_PER_GOLD+50:"2 złota, 50 srebra",
        SILVER_PER_MITHRIL:"1 mithril",
        SILVER_PER_MITHRIL+2*SILVER_PER_GOLD+45:"1 mithril, 2 złota, 45 srebra",
    }
    for total,expected in formatter_tests.items():
        got=currency_reading_text(total,0,0)
        if got!=expected: errors.append(f"format {total}: {got!r} != {expected!r}")
    quest_values=[]
    for qid,q in QUESTS.items():
        value=v0190_quest_currency_reward(q)
        quest_values.append(value)
        if value<SILVER_PER_GOLD: errors.append(f"quest <1 gold: {qid}={value}")
    tool_rows=[]
    for iid,item in ITEMS.items():
        if str(item.get("type","")).lower()=="tool" or item.get("tool_type"):
            price=int(item.get("price",0) or 0)
            tool_rows.append((iid,price))
            # Basic ungated tools must stay in a compact starter band.
            has_gate=any(int(item.get(k,0) or 0)>0 for k in ("required_tool_level","min_tool_level","min_profession_level","required_profession_level","required_mastery"))
            if not has_gate and not (1001 <= price <= 3500):
                errors.append(f"starter tool price {iid}={price}")
    return {
        "version":"0.30.21",
        "quests":len(quest_values),
        "quest_min":min(quest_values) if quest_values else 0,
        "quest_max":max(quest_values) if quest_values else 0,
        "tools":tuple(tool_rows),
        "error_count":len(errors),
        "errors":errors,
    }


def buff_duration_audit_v03030(*, CLASS_SKILLS, GLOBAL_SKILL_BUFF_DURATION_SECONDS):
    errors = []
    checked = 0
    for class_name, skills in CLASS_SKILLS.items():
        for skill in skills:
            if str(skill.get("kind") or "").lower() != "boost":
                continue
            checked += 1
            if int(skill.get("duration", 0) or 0) != GLOBAL_SKILL_BUFF_DURATION_SECONDS:
                errors.append(
                    f"{class_name}/{skill.get('name')}: duration={skill.get('duration')}"
                )
            desc = str(skill.get("desc") or "")
            if "30 sekund" not in desc:
                errors.append(f"{class_name}/{skill.get('name')}: opis bez 30 sekund")
    return {
        "version": "0.30.30",
        "checked": checked,
        "duration_seconds": GLOBAL_SKILL_BUFF_DURATION_SECONDS,
        "error_count": len(errors),
        "errors": errors,
    }


def party_combat_feed_audit_v03031(*, MudServer):
    errors = []
    if not hasattr(MudServer, "party_combat_broadcast"):
        errors.append("brak MudServer.party_combat_broadcast")
    return {
        "version": "0.30.31",
        "error_count": len(errors),
        "errors": errors,
    }


def party_roles_audit_v03032(*, MudServer, Session, PARTY_AUTO_HEAL_THRESHOLD):
    errors = []
    for name in ("party_combat_target", "auto_priest_party_heal"):
        if not hasattr(MudServer, name):
            errors.append(f"brak MudServer.{name}")
    for name in ("auto_priest_heal_option", "perform_auto_priest_heal"):
        if not hasattr(Session, name):
            errors.append(f"brak Session.{name}")
    if PARTY_AUTO_HEAL_THRESHOLD != 0.85:
        errors.append(f"threshold={PARTY_AUTO_HEAL_THRESHOLD}")
    return {"version": "0.30.32", "error_count": len(errors), "errors": errors}


def tool_tier_name_audit_v03033(*, TOOL_TIER_NAMES, TOOL_MAX_TIER, QUESTS, QUEST_REPEAT_COOLDOWN_SECONDS):
    errors = []
    checked = 0
    for tool_type, names in TOOL_TIER_NAMES.items():
        checked += len(names)
        if len(names) != TOOL_MAX_TIER:
            errors.append(f"{tool_type}: {len(names)} nazw, oczekiwano {TOOL_MAX_TIER}")
        normalized = [str(name).strip().casefold() for name in names]
        if len(set(normalized)) != len(normalized):
            seen = set()
            duplicates = []
            for name in normalized:
                if name in seen and name not in duplicates:
                    duplicates.append(name)
                seen.add(name)
            errors.append(f"{tool_type}: duplikaty {duplicates[:5]}")
    quest = QUESTS.get("city_tailor_guard_delivery", {})
    if not quest.get("repeatable"):
        errors.append("city_tailor_guard_delivery nie jest repeatable")
    if int(quest.get("repeat_cooldown", 0) or 0) != int(QUEST_REPEAT_COOLDOWN_SECONDS):
        errors.append("city_tailor_guard_delivery ma zły cooldown")
    return {
        "version": "0.30.33",
        "tool_names_checked": checked,
        "expected_tool_names": len(TOOL_TIER_NAMES) * TOOL_MAX_TIER,
        "tailor_quest_repeatable": bool(quest.get("repeatable")),
        "error_count": len(errors),
        "errors": errors,
    }


def haldor_steel_plate_corpse_audit_v03034(*, QUESTS, MOB_TEMPLATES, ITEMS, CRAFT_MATERIAL_STORAGE_IDS):
    errors = []
    q = QUESTS.get("haldor_steel_recycling", {})
    if q.get("target") != "salvaged_steel_plate" or int(q.get("needed", 0) or 0) != 4:
        errors.append("haldor_steel_recycling target/needed")
    sources = {
        "cemetery_steel_skeleton": 0.72,
        "cemetery_restless_dead": 0.28,
        "cemetery_bone_collector": 0.42,
    }
    for mid, expected in sources.items():
        t = MOB_TEMPLATES.get(mid, {})
        if "salvaged_steel_plate" in (t.get("drops") or {}):
            errors.append(f"{mid}: plate still in direct drops")
        actual = float((t.get("corpse_material_chances") or {}).get("salvaged_steel_plate", -1))
        if abs(actual - expected) > 1e-9:
            errors.append(f"{mid}: corpse chance={actual} expected={expected}")
    if ITEMS.get("salvaged_steel_plate", {}).get("type") != "craft_material":
        errors.append("plate is not craft_material")
    if "salvaged_steel_plate" not in CRAFT_MATERIAL_STORAGE_IDS:
        errors.append("plate missing from craftbox routing")
    return {"version":"0.30.34","sources":len(sources),"error_count":len(errors),"errors":errors}


def broken_blades_spoken_progress_audit_v03038(*, Session, QUESTS):
    errors = []
    import inspect as _inspect_v03038
    src = _inspect_v03038.getsource(Session.grant_hourly_quest_kill_drop_v0929)
    required = (
        "increment_item_collect_quest",
        "Postęp questa:",
        "quest_progress=False",
    )
    for token in required:
        if token not in src:
            errors.append(f"missing runtime token: {token}")
    quest = QUESTS.get("haldor_broken_blades_v0929", {})
    if quest.get("target") != "damaged_weapon_v0929" or int(quest.get("needed", 0) or 0) != 6:
        errors.append("broken blades target/needed changed")
    return {
        "version": "0.30.38",
        "error_count": len(errors),
        "errors": errors,
    }


def eq_shortcuts_auto_audit_v03040(*, COMMAND_ALIASES, Session, CLASS_EQUIPMENT_SLOT_DEFS):
    errors = []
    expected_aliases = {
        "zhel":"equiphead", "zpan":"equipbody", "ztar":"equipshield", "zrek":"equiphands",
        "znog":"equiplegs", "zbut":"equipfeet", "ztal":"equipcharmauto",
        "zpier":"equipringauto", "znasz":"equipnecklace", "zkol":"equipearringauto",
        "znar":"equipshoulders", "zpas":"equipbelt", "zpel":"equipcloak",
        "zkar":"equipbracers", "zbra":"equipbracelet", "zakc":"equipaccessoryauto",
        "zrel":"equiprelic",
        "autoeq":"autoequip", "eqauto":"autoequip", "zauto":"autoequip",
    }
    for alias, expected in expected_aliases.items():
        if COMMAND_ALIASES.get(alias) != expected:
            errors.append(f"{alias}: {COMMAND_ALIASES.get(alias)!r}, expected {expected!r}")
    import inspect as _inspect_v03040
    src = _inspect_v03040.getsource(Session.auto_equip_best_v03040)
    for token in (
        "required_class", "equipment_mastery_requirement_met",
        "ring1", "ring2", "charm1", "charm2", "earring1", "earring2",
        "accessory1", "accessory2", "return_socketed_gems", "AUTO EQ",
    ):
        if token not in src:
            errors.append(f"auto eq missing token: {token}")
    if len(CLASS_EQUIPMENT_SLOT_DEFS) != 17:
        errors.append(f"logical EQ slot count {len(CLASS_EQUIPMENT_SLOT_DEFS)}, expected 17")
    return {
        "version":"0.30.40",
        "shortcut_count":len(expected_aliases),
        "logical_slot_count":len(CLASS_EQUIPMENT_SLOT_DEFS),
        "error_count":len(errors),
        "errors":errors,
    }


def universal_salvage_audit_v03041(*, ITEMS, V0925_SALVAGE_MATERIALS, v03041_salvage_material_key, SessionForgeGuildsMixin, Session, normalize_lookup_text):
    errors = []
    armor_ids = [item_id for item_id, item in ITEMS.items() if item.get("type") == "armor"]
    by_material = {key: 0 for key in V0925_SALVAGE_MATERIALS}
    for item_id in armor_ids:
        item = ITEMS[item_id]
        material = v03041_salvage_material_key(item)
        if material not in V0925_SALVAGE_MATERIALS:
            errors.append(f"{item_id}: invalid salvage material {material!r}")
            continue
        by_material[material] += 1
        level = max(1, min(400, int(item.get("required_character_level", item.get("required_mastery", 1)) or 1)))
        # Bez jawnego materiału późne EQ nie może wpadać z powrotem do Żelaza.
        explicit = str(item.get("corpse_material") or item.get("blacksmith_material") or "").strip()
        if not explicit and level >= 360 and material != "eternium" and not any(
            token in normalize_lookup_text(item.get("name", ""))
            for token in ("eternium", "pustk", "astral", "smocz", "runicz", "kobalt", "adamant", "mithril", "stal", "zelaz")
        ):
            errors.append(f"{item_id}: level {level} maps to {material}, expected eternium")
    import inspect as _inspect_v03041
    # v0.35.3: the active method is the newer Salvage 3.0 wrapper, which
    # delegates classic armor salvage to SessionForgeGuildsMixin. Audit both
    # layers instead of forcing the old implementation to remain first in MRO.
    base_src = _inspect_v03041.getsource(SessionForgeGuildsMixin.salvage_equipment_v0925)
    active_src = _inspect_v03041.getsource(Session.salvage_equipment_v0925)
    for token in (
        "free_equipment_quantity", "v03041_salvage_material_key",
        "equipment_runes_v0925", "clear_equipment_crafting_v0925",
        "ROZKŁADANIE EQ", "Wybierz numer",
    ):
        if token not in base_src:
            errors.append(f"salvage base implementation missing token: {token}")
    if "is_character_bound_item" in base_src:
        errors.append("salvage still rejects bound armor")
    if "SessionForgeGuildsMixin.salvage_equipment_v0925" not in active_src:
        errors.append("Salvage 3.0 wrapper no longer delegates classic armor salvage")
    if "SALVAGE3_V03114" not in active_src:
        errors.append("Salvage 3.0 wrapper missing extended salvage registry")
    return {
        "version": "0.30.41",
        "armor_checked": len(armor_ids),
        "material_counts": by_material,
        "error_count": len(errors),
        "errors": errors,
    }


def equipment_upgrade_audit_v03042(*, ITEMS, V03042_EQ_UPGRADE_MAX, v03042_upgrade_required_smithing, v03042_upgrade_material_cost, CHARACTER_MAX_LEVEL, v03041_salvage_material_key, V0925_SALVAGE_MATERIALS, COMMAND_ALIASES, Session):
    errors = []
    armor_ids = [iid for iid, item in ITEMS.items() if item.get("type") == "armor"]
    for item_id in armor_ids:
        item = ITEMS[item_id]
        previous_req = 0
        previous_cost = 0
        for target in range(1, V03042_EQ_UPGRADE_MAX + 1):
            req = v03042_upgrade_required_smithing(item, target)
            cost = v03042_upgrade_material_cost(item, target)
            if not 1 <= req <= CHARACTER_MAX_LEVEL:
                errors.append(f"{item_id}: bad smithing requirement +{target}={req}")
                break
            if req < previous_req:
                errors.append(f"{item_id}: smithing requirement decreases at +{target}")
                break
            if cost <= 0 or cost < previous_cost:
                errors.append(f"{item_id}: bad/nonmonotonic material cost +{target}={cost}")
                break
            previous_req, previous_cost = req, cost
        material = v03041_salvage_material_key(item)
        if material not in V0925_SALVAGE_MATERIALS:
            errors.append(f"{item_id}: invalid upgrade material {material}")
    expected_aliases = {
        "ulepsz": "equpgrade", "ulepszaj": "equpgrade", "upgrade": "equpgrade",
        "upgradeeq": "equpgrade", "ulepszeq": "equpgrade",
    }
    for alias, command in expected_aliases.items():
        if COMMAND_ALIASES.get(alias) != command:
            errors.append(f"shortcut {alias} -> {COMMAND_ALIASES.get(alias)!r}, expected {command!r}")
    import inspect as _inspect_v03042
    src = _inspect_v03042.getsource(Session.upgrade_equipment_v03042)
    for token in (
        "Kowalstwo", "crafting_hammer", "required_tool_tier_for_level",
        "v03042_upgrade_material_cost", "set_equipment_upgrade_level_v03042",
        "grant_profession_progress", "Nie ma ryzyka zniszczenia",
    ):
        if token not in src:
            errors.append(f"upgrade implementation missing token: {token}")
    return {
        "version": "0.30.42",
        "armor_checked": len(armor_ids),
        "max_upgrade": V03042_EQ_UPGRADE_MAX,
        "error_count": len(errors),
        "errors": errors,
    }


def soul_tier7_cemetery_spawn_audit_v0365(*, SOUL_TRIAL_QUEST_IDS, QUESTS, MOB_SPAWNS, ROOMS):
    errors=[]
    quest_id = SOUL_TRIAL_QUEST_IDS.get(7)
    quest = QUESTS.get(quest_id, {}) if quest_id else {}
    target = str(quest.get("target") or "")
    needed = int(quest.get("needed", 0) or 0)
    if target != "cemetery_restless_dead":
        errors.append(f"Tier 7 target={target!r}, expected cemetery_restless_dead")
    if needed != 4:
        errors.append(f"Tier 7 needed={needed}, expected 4")
    target_rooms = [
        room_id for room_id, mob_id in MOB_SPAWNS
        if mob_id == "cemetery_restless_dead"
        and ROOMS.get(room_id, {}).get("zone") == "Stary Cmentarz"
    ]
    distinct_rooms = sorted(set(target_rooms))
    expected_rooms = {
        "graveyard", "cemetery_ossuary_path", "cemetery_moon_garden",
        "cemetery_fallen_chapel", "cemetery_bone_field", "cemetery_bell_tower",
    }
    missing = sorted(expected_rooms - set(distinct_rooms))
    if missing:
        errors.append("missing Tier 7 cemetery spawn rooms: " + ", ".join(missing))
    if len(distinct_rooms) < 6:
        errors.append(f"Tier 7 has only {len(distinct_rooms)} distinct cemetery target rooms, expected >=6")
    return {
        "version":"0.36.5", "quest_id":quest_id, "target":target, "needed":needed,
        "distinct_spawn_rooms":len(distinct_rooms), "spawn_rooms":distinct_rooms,
        "error_count":len(errors), "errors":errors,
    }

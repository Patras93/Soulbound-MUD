# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def apply_equipment_name_pass_v03016():
    renamed_class = 0
    renamed_artifacts = 0
    for item_id, item in ITEMS.items():
        if item.get("type") != "armor":
            continue
        old_name = str(item.get("name") or item_id)
        new_name = None

        if item.get("required_class"):
            new_name = _v03016_class_eq_name(item_id, item)
        else:
            match = re.fullmatch(r"v017_artifact_.+_t(\d+)", str(item_id))
            if match:
                artifact_tier = int(match.group(1))
                epithet = V03016_ARTIFACT_EPITHETS.get(artifact_tier)
                if epithet:
                    base = re.sub(r"\s*\+\d+\s*$", "", old_name).strip()
                    new_name = f"{base} {epithet}"

        if new_name and new_name != old_name:
            item["name"] = new_name
            _v03016_add_legacy_item_alias(item, old_name)
            if item.get("required_class"):
                renamed_class += 1
            else:
                renamed_artifacts += 1

            # Katalogi kolekcji przechowują tekst nazwy osobno od ITEMS.
            for catalog_name in (
                "UNIQUE_ITEM_COLLECTION_CATALOG",
                "EQUIPMENT_COLLECTION_CATALOG",
            ):
                catalog = globals().get(catalog_name)
                if isinstance(catalog, dict) and item_id in catalog:
                    catalog[item_id] = new_name

    return {
        "class_equipment_renamed": renamed_class,
        "artifact_variants_renamed": renamed_artifacts,
    }


def equipment_name_audit_v03016():
    errors = []
    warnings = []
    armor_rows = [
        (item_id, item)
        for item_id, item in ITEMS.items()
        if item.get("type") == "armor"
    ]
    class_rows = [(iid, item) for iid, item in armor_rows if item.get("required_class")]

    # 1. Nazwy wszystkich pancerzy muszą być globalnie unikalne.
    seen = {}
    for item_id, item in armor_rows:
        key = normalize_lookup_text(item.get("name", ""))
        if not key:
            errors.append(f"empty equipment name {item_id}")
            continue
        if key in seen:
            errors.append(
                f"duplicate equipment name {item.get('name')}: {seen[key]} / {item_id}"
            )
        else:
            seen[key] = item_id

    # 2. Klasowe EQ nie może wrócić do schematu +liczba ani kończyć samą cyfrą.
    for item_id, item in class_rows:
        name = str(item.get("name") or "")
        if re.search(r"\+\d+\s*$", name) or re.search(r"\s\d+\s*$", name):
            errors.append(f"numeric class equipment name {item_id}: {name}")
        mastery = max(1, int(item.get("required_mastery", 1) or 1))
        expected = V03016_EQ_MASTERY_EPITHETS.get(mastery)
        if expected and expected not in name:
            errors.append(f"missing mastery epithet {item_id}: {name}")

    # 3. Każda klasa / styl / slot ma inne nazwy na każdym progu Biegłości.
    groups = {}
    for item_id, item in class_rows:
        if item.get("legendary_class_relic"):
            group = (item.get("required_class"), "relic", "necklace")
        elif item.get("legendary_set_loot"):
            group = (item.get("required_class"), "legendary_set", item.get("slot"))
        else:
            group = (
                item.get("required_class"),
                item.get("class_equipment_style", 1),
                item.get("slot"),
            )
        groups.setdefault(group, []).append((item_id, normalize_lookup_text(item.get("name", ""))))
    for group, rows in groups.items():
        names = [name for _iid, name in rows]
        if len(names) != len(set(names)):
            errors.append(f"repeated progression names {group}")

    plus_numeric_armor = [
        iid for iid, item in armor_rows
        if re.search(r"\+\d+\s*$", str(item.get("name") or ""))
    ]
    if plus_numeric_armor:
        errors.append(f"equipment +number suffix remains: {plus_numeric_armor[:10]}")

    return {
        "version": "0.30.16",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "armor_items": len(armor_rows),
        "class_armor_items": len(class_rows),
        "unique_armor_names": len(seen),
        "numeric_suffix_armor_names": len(plus_numeric_armor),
        **V03016_EQUIPMENT_NAME_PASS,
    }


def full_game_audit_v03014():
    errors = []
    warnings = []
    summary = {}

    def require(condition, message):
        if not condition:
            errors.append(str(message))

    # Wbudowane audyty muszą być czyste.
    for audit_name in (
        "CATALOG_VALIDATION_AUDIT", "WORLD_TOPOLOGY_AUDIT", "WORLD_LOGIC_AUDIT",
        "FULL_WORLD_TOPOLOGY_AUDIT_V03013", "EQUIPMENT_NAME_AUDIT_V03016", "CLASS_EQ_IDENTITY_AUDIT_V03016",
    ):
        audit = globals().get(audit_name, {}) or {}
        require(int(audit.get("error_count", 0) or 0) == 0,
                f"{audit_name}: {audit.get('errors', [])[:5]}")

    # Klasy i rasy.
    class_types = {row[0]: row[1] for row in CLASSES}
    require(len(class_types) == 14, f"classes={len(class_types)}")
    require(all(kind in ("physical", "magic") for kind in class_types.values()),
            "invalid class archetype")
    race_names = [row[0] for row in RACES]
    require(len(race_names) == 14 and len(set(race_names)) == 14,
            "races are not 14 unique entries")
    for row in RACES:
        require(sum(int(v) for v in row[2:7]) == 50,
                f"race base stat budget {row[0]}")

    # Skille/spelle wszystkich klas.
    all_skills = []
    skill_ids = {}
    skill_names = {}
    for class_name in class_types:
        rows = CLASS_SKILLS.get(class_name, [])
        # v0.9.22 guarantees at least three choices on every authored mastery
        # threshold. Later source-faithful abilities may legally add extra
        # skills (for example Priest Regen), so total length must not be exact.
        expected_min = len(_V0922_MASTERY_LEVELS) * 3
        require(len(rows) >= expected_min, f"{class_name}: skills={len(rows)} minimum={expected_min}")
        # The generic Soul grid uses 1/10/20/... mastery thresholds.
        # Mec and Engineer deliberately replace part of that generated grid
        # with source-authored UOSSMUD unlocks (8, 12, 14, 16, 18, 21, 23,
        # 32, 44, 46, etc.), so threshold-by-threshold counts do not apply.
        # Their total catalogue still has to meet the generated minimum, while
        # IDs/names/unlocks are validated below and Mec has its own strict
        # MEC_CONTRACT_AUDIT_V11149.
        if class_name not in {"Mec", "Inżynier"}:
            for mastery_level in _V0922_MASTERY_LEVELS:
                at_level = [
                    skill for skill in rows
                    if int(skill.get("unlock", 1) or 1) == int(mastery_level)
                ]
                require(
                    len(at_level) >= 3,
                    f"{class_name}: mastery {mastery_level} has {len(at_level)} skills; minimum=3",
                )
        for skill in rows:
            all_skills.append((class_name, skill))
            sid = str(skill.get("id", ""))
            sname = normalize_lookup_text(skill.get("name", ""))
            if sid in skill_ids:
                errors.append(f"duplicate skill id {sid}")
            skill_ids[sid] = class_name
            if sname in skill_names:
                errors.append(f"duplicate skill name {skill.get('name')}")
            skill_names[sname] = sid
            require(1 <= int(skill.get("unlock", 0) or 0) <= CLASS_MASTERY_MAX_LEVEL,
                    f"skill unlock {sid}")
            require(int(skill.get("cooldown", 0) or 0) >= 0,
                    f"negative cooldown {sid}")
            require(int(skill.get("mana", 0) or 0) >= 0,
                    f"negative mana {sid}")
            require(not re.search(r"\s\d+$", str(skill.get("name", ""))),
                    f"numeric skill name {sid}")
    require(len(_FINAL_SKILL_HELP_SEARCH_ROWS) == len(all_skills),
            "skill HELP index incomplete")

    # Klasowe EQ: dwie bazowe statystyki dla każdego klasowego pancerza.
    class_armor = 0
    for item_id, item in ITEMS.items():
        class_name = item.get("required_class")
        if not class_name or item.get("type") != "armor":
            continue
        class_armor += 1
        present = set()
        if int(item.get("affix_amount", 0) or 0) > 0:
            present.add(item.get("affix"))
        present.update(
            stat for stat, amount in (item.get("stats") or {}).items()
            if int(amount or 0) > 0
        )
        # Ręcznie projektowane zestawy technologiczne mają własne profile
        # (np. Tech Mec: STR+CON+WILL) i nie podlegają generatorowej parze
        # bazowych statów zwykłego klasowego EQ.
        if str(item.get("regional_set", "")).startswith("tech_"):
            continue
        expected = set(class_equipment_base_stat_pair(class_name))
        require(expected.issubset(present),
                f"class armor stats {item_id}: expected {sorted(expected)}, got {sorted(present)}")

    # NPC i ich prywatne pokoje/questy.
    room_npcs = {}
    for npc_id, npc in NPCS.items():
        room_id = npc.get("room")
        require(room_id in ROOMS, f"NPC room missing {npc_id}:{room_id}")
        room_npcs.setdefault(room_id, []).append(npc_id)
        if npc.get("quest"):
            require(npc.get("quest") in QUESTS,
                    f"NPC quest missing {npc_id}:{npc.get('quest')}")
    for room_id, npc_ids in room_npcs.items():
        require(len(npc_ids) <= 1,
                f"multiple static NPCs in {room_id}: {npc_ids}")

    # Questy: relacje i brak globalnej blokady Character Level.
    virtual_kill_targets = set()
    for mob in MOB_TEMPLATES.values():
        if mob.get("quest_target"):
            virtual_kill_targets.add(str(mob.get("quest_target")))
        virtual_kill_targets.update(str(v) for v in (mob.get("quest_targets") or ()))
    for quest_id, quest in QUESTS.items():
        prerequisite = quest.get("requires_quest")
        if prerequisite:
            require(prerequisite in QUESTS,
                    f"quest prerequisite missing {quest_id}:{prerequisite}")
        for key in ("reward_items", "accept_items"):
            for item_id in (quest.get(key) or {}):
                require(item_id in ITEMS,
                        f"quest {quest_id} {key} missing {item_id}")
        kind = quest.get("kind")
        target = quest.get("target")
        if kind in ("collect", "collect_resource") and target not in (None, "any"):
            require(target in ITEMS, f"quest item target missing {quest_id}:{target}")
        if kind == "kill" and target not in (None, "any", "*"):
            target_text = str(target)
            dynamic_crypt = bool(re.fullmatch(r"crypt_boss_\d+", target_text))
            require(target in MOB_TEMPLATES or target_text in virtual_kill_targets or dynamic_crypt,
                    f"quest mob target missing {quest_id}:{target}")
        if kind == "collect_resource_set":
            for item_id in (quest.get("resource_targets") or {}):
                require(item_id in ITEMS,
                        f"quest resource target missing {quest_id}:{item_id}")
        if kind == "craft_set":
            for item_id in (quest.get("targets") or ()):
                require(item_id in ITEMS,
                        f"quest craft target missing {quest_id}:{item_id}")
        if kind == "deliver_npc":
            require(quest.get("target_npc") in NPCS,
                    f"quest target NPC missing {quest_id}:{quest.get('target_npc')}")
            require(quest.get("quest_item") in ITEMS,
                    f"quest delivery item missing {quest_id}:{quest.get('quest_item')}")
        for forbidden in ("required_character_level", "min_character_level", "character_level_required"):
            require(forbidden not in quest,
                    f"Character Level quest gate {quest_id}:{forbidden}")

    # Łańcuchy questów nie mogą mieć pętli.
    for start in QUESTS:
        seen = set()
        current = start
        while current in QUESTS and QUESTS[current].get("requires_quest"):
            if current in seen:
                errors.append(f"quest dependency cycle {start}")
                break
            seen.add(current)
            current = QUESTS[current].get("requires_quest")

    # Receptury: referencje, progi i tekst widoczny dla gracza.
    recipe_count = 0
    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):
        table = globals().get(table_name, {}) or {}
        recipe_count += len(table)
        for recipe_id, recipe in table.items():
            for item_id in (recipe.get("ingredients") or {}):
                require(item_id in ITEMS,
                        f"{table_name} ingredient missing {recipe_id}:{item_id}")
            output_id = recipe.get("output")
            if output_id:
                require(output_id in ITEMS,
                        f"{table_name} output missing {recipe_id}:{output_id}")
            level = int(recipe.get("generator_level", 0) or 0)
            require(1 <= level <= PROFESSION_MAX_LEVEL, f"{table_name} level {recipe_id}:{level}")
            desc = str(recipe.get("desc", "") or "")
            match = re.search(r"(?i)level\s*(\d+)", desc)
            if match:
                require(int(match.group(1)) == int(recipe.get("min_profession_level", 0) or 0),
                        f"recipe text level mismatch {table_name}:{recipe_id}")
            quantities = re.findall(r"(?i)(\d+)\s+sztuk", desc)
            if quantities and len(recipe.get("ingredients") or {}) == 1:
                actual = sum(int(v or 0) for v in (recipe.get("ingredients") or {}).values())
                require(int(quantities[0]) == actual,
                        f"recipe text quantity mismatch {table_name}:{recipe_id}")

    # Statyczne spawny.
    for room_id, mob_id in MOB_SPAWNS:
        require(room_id in ROOMS, f"spawn room missing {room_id}:{mob_id}")
        require(mob_id in MOB_TEMPLATES, f"spawn mob missing {room_id}:{mob_id}")

    # HELP: aliasy do tematów lub czterech wirtualnych widoków menu.
    virtual_help = {"tematy", "komendy", "wszystko", "kategorie"}
    for alias, target in HELP_TOPIC_ALIASES.items():
        require(target in HELP_TOPICS or target in virtual_help,
                f"HELP alias target missing {alias}:{target}")

    # Wszystkie główne krzywe progresji 1-600 muszą być monotoniczne.
    for axis in balance_math.AXIS_CURVES:
        values = [balance_math.axis_requirement(axis, level) for level in range(1, PROGRESSION_MAX_LEVEL + 1)]
        require(all(b >= a for a, b in zip(values, values[1:])),
                f"nonmonotonic progression axis {axis}")

    summary.update({
        "classes": len(class_types), "races": len(race_names),
        "skills": len(all_skills), "class_armor": class_armor,
        "npcs": len(NPCS), "quests": len(QUESTS), "recipes": recipe_count,
        "spawns": len(MOB_SPAWNS), "mobs": len(MOB_TEMPLATES),
        "items": len(ITEMS), "rooms": len(ROOMS),
        "help_topics": len(HELP_TOPICS), "command_aliases": len(COMMAND_ALIASES),
        "recipe_text_levels_fixed": V03014_RECIPE_TEXT_AUDIT.get("level_descriptions_fixed", 0),
        "recipe_text_quantities_fixed": V03014_RECIPE_TEXT_AUDIT.get("ingredient_descriptions_fixed", 0),
        "equipment_unique_names": EQUIPMENT_NAME_AUDIT_V03016.get("unique_armor_names", 0),
        "class_equipment_renamed": V03016_EQUIPMENT_NAME_PASS.get("class_equipment_renamed", 0),
        "equipment_numeric_suffix_names": EQUIPMENT_NAME_AUDIT_V03016.get("numeric_suffix_armor_names", 0),
    })
    return {
        "version": "0.30.14", "error_count": len(errors),
        "warning_count": len(warnings), "errors": errors,
        "warnings": warnings, **summary,
    }


def full_combat_scaling_audit_v03015():
    errors = []
    physical_classes = {name for name, kind, *_ in CLASSES if kind == "physical"}
    magical_classes = {name for name, kind, *_ in CLASSES if kind == "magic"}
    offensive = {"damage", "aoe_damage", "execute", "drain"}
    checked = 0
    dexterity_classes = {"Łotrzyk", "Łowca"}
    flexible_classes = {"Mnich", "Mec", "Inżynier"}
    for class_name, skills in CLASS_SKILLS.items():
        if class_name in dexterity_classes:
            expected = "dexterity"
        elif class_name in magical_classes:
            expected = "intelligence"
        elif class_name in physical_classes and class_name not in flexible_classes:
            expected = "strength"
        else:
            expected = None
        for skill in skills:
            if skill.get("kind") not in offensive:
                continue
            checked += 1
            actual = skill.get("scale")
            if class_name in flexible_classes:
                allowed = {"strength", "dexterity", "intelligence"}
                if class_name == "Mec":
                    # Authored Mec abilities use several source-backed scales:
                    # Willpower for support/control, Attack for many weapon
                    # techniques, HP difference for Crush and current target HP
                    # percentage for Compress.
                    allowed.update({
                        "willpower",
                        "attack",
                        "hp_difference",
                        "target_current_hp_percent",
                    })
                if actual not in allowed:
                    errors.append(f"{class_name}/{skill.get('id')}: invalid branch scale={actual}")
            elif expected is not None and actual != expected:
                errors.append(f"{class_name}/{skill.get('id')}: scale={actual} expected={expected}")
    base = balance_math.character_mana_base(100, 50, 50)
    int_plus = balance_math.character_mana_base(100, 60, 50)
    wil_plus = balance_math.character_mana_base(100, 50, 60)
    if int_plus <= base or wil_plus <= base:
        errors.append("INT/WIL does not increase mana")
    if int_plus - base != wil_plus - base:
        errors.append("INT/WIL mana contribution is not equal")
    return {
        "version": "0.30.19",
        "generator_version": str(BALANCE_MATH_VERSION),
        "offensive_skills_checked": checked,
        "skill_scales_normalized": V03015_SKILL_SCALES_NORMALIZED,
        "mana_base": base,
        "mana_plus_10_int": int_plus,
        "mana_plus_10_will": wil_plus,
        "error_count": len(errors),
        "errors": errors,
    }


def aggro_cleanup_audit_v03015():
    errors = []
    room_id = next(iter(ROOMS))
    template_id = next(iter(MOB_TEMPLATES))
    max_hp = int(MOB_TEMPLATES[template_id].get("max_hp", 100) or 100)

    server = object.__new__(MudServer)
    server.sessions = set()
    server.parties = {}
    server.party_invites = {}
    server.party_protectors = {}
    server.world = type("AuditWorld", (), {"mobs": {}})()

    character = type("AuditCharacter", (), {"name": "AuditTester", "room_id": room_id})()
    session = type("AuditSession", (), {})()
    session.closed = False
    session.character = character
    session.current_hp = 100
    session.combat_mob_key = None
    session.account_id = 999999991

    ghost = MobState(
        key="audit_ghost_aggro", room_id=room_id, template_id=template_id,
        hp=max_hp, engaged_by="NieistniejacyGracz", engaged_at=12.0,
        combat_turn=3, player_hits=4,
    )
    server.world.mobs[ghost.key] = ghost
    if not server.engagement_allowed(session, ghost):
        errors.append("ghost aggro still blocks a free mob")
    if ghost.engaged_by is not None or ghost.engaged_at != 0.0:
        errors.append("ghost aggro was not cleared")

    server.sessions.add(session)
    session.combat_mob_key = "audit_owned_1"
    for key in ("audit_owned_1", "audit_owned_2"):
        server.world.mobs[key] = MobState(
            key=key, room_id=room_id, template_id=template_id, hp=max_hp,
            engaged_by=character.name, engaged_at=1.0,
        )
    released = server.release_all_engagements_for_session(session)
    if released != 2:
        errors.append(f"release_all count={released} expected=2")
    if any(server.world.mobs[key].engaged_by for key in ("audit_owned_1", "audit_owned_2")):
        errors.append("release_all left owned mob aggro behind")

    return {
        "version": "0.30.16",
        "ghost_aggro_cleared": ghost.engaged_by is None,
        "multi_mob_release_count": released,
        "error_count": len(errors),
        "errors": errors,
    }


def progression_combat_audit_v03017():
    errors = []
    grid = (1, *range(10, CLASS_MASTERY_MAX_LEVEL + 1, 10))
    grid_set = set(grid)
    class_names = [row[0] for row in CLASSES]

    for class_name in class_names:
        rows = CLASS_SKILLS.get(class_name, [])
        counts = {level: 0 for level in grid}
        for skill in rows:
            unlock = int(skill.get("unlock", 0) or 0)
            if class_name not in ("Inżynier","Mec") and unlock not in grid_set:
                errors.append(f"{class_name}/{skill.get('id')}: próg {unlock} poza siatką")
            elif unlock in grid_set:
                counts[unlock] += 1
            elif not (1 <= unlock <= CLASS_MASTERY_MAX_LEVEL):
                errors.append(f"{class_name}/{skill.get('id')}: nieprawidłowy próg {unlock}")
        expected_min = len(grid) * 3
        if len(rows) < expected_min:
            errors.append(f"{class_name}: {len(rows)} skilli, minimum {expected_min}")
        if class_name not in ("Inżynier","Mec"):
            for level in grid:
                if counts[level] < 3:
                    errors.append(f"{class_name}: próg {level} ma {counts[level]} skilli, minimum 3")

    expected_slots = {1: 10, 10: 11, 100: 20, 200: 30, 400: 50, 600: 70}
    for level, expected in expected_slots.items():
        got = min(10 + CHARACTER_MAX_LEVEL // 10, 10 + level // 10)
        if got != expected:
            errors.append(f"sloty Level {level}: {got}, oczekiwano {expected}")

    techniques = [SOUL_WEAPON_ATTACK_TECHNIQUES.get(name) for name in class_names]
    if any(not value for value in techniques):
        errors.append("brak techniki autoataku Broni Duszy dla klasy")
    if len(set(techniques)) != len(class_names):
        errors.append("techniki autoataku Broni Duszy nie są unikalne")
    weapons = [row[2] for row in CLASSES]
    if len(set(weapons)) != len(class_names):
        errors.append("nazwy Broni Duszy nie są unikalne")

    return {
        "version": "0.30.17",
        "classes": len(class_names),
        "skills": sum(len(CLASS_SKILLS.get(name, [])) for name in class_names),
        "thresholds_per_class": len(grid),
        "skills_per_threshold": 3,
        "queue_slot_checkpoints": expected_slots,
        "soul_weapon_techniques": len(set(techniques)),
        "error_count": len(errors),
        "errors": errors,
    }


def help_truth_audit_v11197():
    errors = []

    def topic_text(name):
        value = HELP_TOPICS.get(name, [])
        if isinstance(value, str):
            return value
        return " ".join(str(line) for line in value)

    canonical_600 = (
        "podstawy", "score", "level", "xp", "umiejetnosci", "skille",
        "dusza", "profesje", "generator",
    )
    current_800 = {"podstawy", "score", "level", "xp", "dusza"}
    for name in canonical_600:
        text = topic_text(name)
        if not text:
            errors.append(f"HELP {name}: empty")
        if "1-400" in text or "1–400" in text:
            errors.append(f"HELP {name}: stale 1-400 limit")
        if name in current_800:
            if "800" not in text:
                errors.append(f"HELP {name}: missing current 800 progression")
            if "1-600" in text or "Na Levelu 600" in text:
                errors.append(f"HELP {name}: obsolete 600 cap")
        elif "1-600" not in text and "600" not in text:
            errors.append(f"HELP {name}: missing expected legacy topic coverage")

    professions = topic_text("profesje")
    if "14 profesji" not in professions:
        errors.append("HELP profesje: must state 14 professions")
    for needle in (
        "sensowny zarobek",
        "Rekiny",
        "Geody",
        "premię odkrywcy",
    ):
        if needle not in professions:
            errors.append(f"HELP profesje: missing reward identity {needle}")

    queue = topic_text("kolejka")
    if "bez limitu" not in queue and "nie mają limitu" not in queue:
        errors.append("HELP kolejka: missing unlimited rotation semantics")
    if "automatycznie" not in queue or "nauczyciela" not in queue:
        errors.append("HELP kolejka: missing automatic learned-skill enrollment")
    if any(stale in queue.casefold() for stale in (
        "aktywnych slotów; co 10", "aż do 80 na levelu", "maksymalnie 120 na levelu",
        "co 10 leveli dochodzi", "20 aktywnych slotów",
    )):
        errors.append("HELP kolejka: obsolete level-based slot limits")

    skills = topic_text("umiejetnosci")
    if "nie mają cooldownu" not in skills or "V-MAX" not in skills:
        errors.append("HELP umiejetnosci: global no-cooldown policy / mechanic exception missing")

    equipment = topic_text("ekwipunek")
    if "tarc" not in equipment.casefold() or "bransolet" not in equipment.casefold():
        errors.append("HELP ekwipunek: shield/bracelet missing")

    statuses = topic_text("statusy")
    if "przeciwn" not in statuses.casefold() or "Silence" not in statuses:
        errors.append("HELP statusy: enemy debuff contract missing")

    aliases = ("superbosses", "statusy", "progresja600")
    for alias in aliases:
        target = HELP_TOPIC_ALIASES.get(alias, alias)
        if target not in HELP_TOPICS:
            errors.append(f"HELP alias missing target: {alias}->{target}")

    return {
        "version": "1.11.97",
        "canonical_topics_checked": len(canonical_600),
        "error_count": len(errors),
        "errors": errors,
    }


def help_surface_audit_v11197():
    errors = []

    def text_of(name):
        value = HELP_TOPICS.get(name, [])
        if isinstance(value, str):
            return value
        return " ".join(str(line) for line in value)

    expected = {
        "klasy": ("14", "1-600"),
        "rasy": ("14", "Cyborg"),
        "cyborg": ("Black Rabite", "NIE jest"),
        "inzynier": ("1-600", "Omni-Narzędzie"),
        "skille100_200": ("1-600", "80"),
        "materialy_eq": ("17", "akcesorium"),
        "kolczyki": ("17", "zkol1", "zkol2"),
        "sety_klasowe": ("17", "2/4/6/8"),
        "sklepy": ("17", "bransolet"),
        "ekwipunek": (
            "17", "zakc",
            "Siłę + Zręczność + Kondycję",
            "Inteligencję + Siłę Woli + Kondycję",
            "mieszać style",
            "Attack",
            "Magic Attack",
            "Masterwork",
            "dobry roll",
            "Relikty bossów Krypty",
        ),
        "moogle_board": ("Black Rabite", "150"),
        "silence": ("One Enemy", "Cleanseable", "Extendable"),
        "hp_mobow": ("600", "con"),
        "soul_xp_bloki": ("1-600", "dusza info"),
        "hp_bossow_lochow": ("600", "consider"),
        "expowiska": ("1-600", "teren info"),
        "questy_gotowania_1_200": ("1-600", "historyczna"),
        "questy_mikstur_orina": ("1-600", "Alchemia"),
        "atlas_kompletny": ("600", "atlas"),
        "walka": ("help skill", "V-MAX"),
        "odpoczynek": ("2 procent", "10 procent", "5 sekund"),
        "leczenie": ("Inteligencja", "Siła Woli", "Magic Attack"),
        "statystyki": ("bez twardego limitu", "x4", "60 akcji"),
    }
    for topic, needles in expected.items():
        text = text_of(topic)
        if not text:
            errors.append(f"HELP {topic}: empty")
            continue
        for needle in needles:
            if needle.casefold() not in text.casefold():
                errors.append(f"HELP {topic}: missing {needle}")

    forbidden_current = {
        "klasy": ("Level postaci 1-400", "Biegłość 1-400"),
        "cyborg": ("dostaje Moogle Board na starcie",),
        "inzynier": ("klasa fizyczna 1-400",),
        "skille100_200": ("10 slotów", "50 na Levelu 400"),
        "materialy_eq": ("15 logicznych",),
        "sety_klasowe": ("14 logicznych",),
        "ekwipunek": ("13 logicznych", "14 logicznych", "15 logicznych"),
    }
    for topic, bad_values in forbidden_current.items():
        text = text_of(topic)
        for bad in bad_values:
            if bad.casefold() in text.casefold():
                errors.append(f"HELP {topic}: stale phrase {bad}")

    return {
        "version": "1.11.97",
        "topics_checked": len(expected),
        "error_count": len(errors),
        "errors": errors,
    }


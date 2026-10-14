# -*- coding: utf-8 -*-
"""Native historical helper extraction; unchanged function bodies."""
def configure_equipment_mastery_requirements_v0918():
    blacksmith_mastery = {
        str(tier["key"]): max(1, min(CLASS_MASTERY_MAX_LEVEL, int(tier["profession_level"])))
        for tier in BLACKSMITH_TIERS
    }

    # Regionalne zestawy i unikatowe dropy bossów istniały przed globalnym
    # systemem wymagań EQ. W v0.9.18 dostają realne progi Biegłości, aby
    # przekazanie przedmiotu nowej postaci nie omijało progresji.
    regional_mastery = {
        "cultist": 40,
        "necropolis": 70,
        "ice_caves": 60,
    }
    named_mastery = {
        "bandit_chief_signet": 10,
        "goblin_king_crown": 20,
        "shadow_alpha_fang": 20,
        "ruin_warden_plate": 30,
        "crystal_lord_core": 40,
        "cemetery_keeper_lantern": 15,
        "void_archon_ring": 40,
        "primal_alpha_necklace": 35,
        "dead_king_seal": 70,
        "cistern_king_chain": 10,
        "eternal_ice_heart": 60,
        "troll_king_tusk": 40,
    }

    recipe_mastery = {}
    for recipe_table in (CRAFT_RECIPES, JEWELCRAFT_RECIPES):
        for recipe in recipe_table.values():
            output = recipe.get("output")
            if not output or ITEMS.get(output, {}).get("type") != "armor":
                continue
            req = max(
                1,
                int(recipe.get("min_profession_level", 0) or 0),
                int(recipe.get("min_tool_level", 0) or 0),
            )
            recipe_mastery[output] = max(recipe_mastery.get(output, 1), req)

    configured = 0
    for item_id, item in ITEMS.items():
        if item.get("type") != "armor":
            continue
        required_class = item.get("required_class")
        if required_class:
            item["required_mastery"] = max(1, int(item.get("required_mastery", 1) or 1))
            configured += 1
            continue

        requirement = max(1, int(item.get("required_mastery", 1) or 1))

        material = item.get("corpse_material")
        if material in CORPSE_MATERIAL_REQUIRED_MASTERY:
            requirement = max(requirement, CORPSE_MATERIAL_REQUIRED_MASTERY[material])

        crypt_tier = int(item.get("crypt_set_tier", 0) or 0)
        if crypt_tier > 0:
            requirement = max(requirement, min(CHARACTER_MAX_LEVEL, crypt_tier * 10))

        astral_tier = int(item.get("astral_set_tier", 0) or 0)
        if astral_tier > 0:
            requirement = max(requirement, min(CHARACTER_MAX_LEVEL, 90 + astral_tier * 10))

        astral_floor = int(item.get("astral_relic_floor", 0) or 0)
        if astral_floor > 0:
            requirement = max(requirement, min(CHARACTER_MAX_LEVEL, astral_floor))

        crypt_boss_floor = int(item.get("boss_relic_floor", 0) or 0)
        if crypt_boss_floor > 0:
            requirement = max(requirement, min(CHARACTER_MAX_LEVEL, crypt_boss_floor))

        regional_set = str(item.get("regional_set") or "")
        if regional_set in regional_mastery:
            requirement = max(requirement, regional_mastery[regional_set])

        if item_id in named_mastery:
            requirement = max(requirement, named_mastery[item_id])

        blacksmith_material = str(item.get("blacksmith_material") or "")
        if blacksmith_material in blacksmith_mastery:
            requirement = max(requirement, blacksmith_mastery[blacksmith_material])

        jewel_level = int(item.get("jewelcraft_level", 0) or 0)
        if jewel_level > 0:
            requirement = max(requirement, min(CHARACTER_MAX_LEVEL, jewel_level))

        if item_id in recipe_mastery:
            requirement = max(requirement, min(CHARACTER_MAX_LEVEL, recipe_mastery[item_id]))

        item["required_mastery"] = max(1, min(CLASS_MASTERY_MAX_LEVEL, requirement))
        item["mastery_requirement_scope"] = "active_class"
        marker = f"Wymaga Biegłości aktywnej klasy {item['required_mastery']}."
        desc = str(item.get("desc") or "").strip()
        if "Wymaga Biegłości aktywnej klasy" not in desc:
            item["desc"] = (desc + " " + marker).strip()
        configured += 1
    return configured


def densify_static_dungeon_spawns():
    # Najpierw usuń stare identyczne duplikaty tego samego archetypu
    # tylko w lochach objętych tym systemem. Zastępujemy je różnymi mobami.
    compact = []
    seen_pairs = set()
    for room_id, template_id in MOB_SPAWNS:
        zone = ROOMS.get(room_id, {}).get("zone")
        pair = (room_id, template_id)
        if zone in DENSE_DUNGEON_ZONES and pair in seen_pairs:
            continue
        compact.append(pair)
        seen_pairs.add(pair)
    MOB_SPAWNS[:] = compact

    room_spawns = {}
    for room_id, template_id in MOB_SPAWNS:
        room_spawns.setdefault(room_id, []).append(template_id)

    additions = []
    for room_id, room in ROOMS.items():
        zone = room.get("zone")
        if zone not in DENSE_DUNGEON_ZONES:
            continue
        # Nigdy nie dotykamy żadnej kopalni.
        if "Kopalnia" in str(zone) or "Kopalnia" in str(room.get("name", "")):
            continue
        existing = room_spawns.get(room_id, [])
        regular = [
            tid for tid in existing
            if tid in MOB_TEMPLATES and not _is_boss_for_density(MOB_TEMPLATES[tid])
        ]
        if not regular:
            continue
        pool = DENSE_ZONE_NAME_POOLS.get(zone, ())
        def _archetype_name(template_id):
            name = str(MOB_TEMPLATES.get(template_id, {}).get("name", template_id))
            name = re.sub(r",\s*(?:poziom|piętro)\s+\d+.*$", "", name, flags=re.I)
            return name.casefold().strip()
        distinct_archetypes = {_archetype_name(tid) for tid in regular}
        needed = max(0, 3 - len(distinct_archetypes))
        available_pool = [
            name for name in pool
            if str(name).casefold().strip() not in distinct_archetypes
        ]
        for n in range(needed):
            base_id = regular[n % len(regular)]
            base = MOB_TEMPLATES[base_id]
            variant_id = f"{base_id}_v915_{n + 2}"
            if variant_id in MOB_TEMPLATES:
                additions.append((room_id, variant_id))
                continue
            variant = dict(base)
            if isinstance(base.get("drops"), dict):
                variant["drops"] = dict(base["drops"])
            if isinstance(base.get("corpse_equipment_pool"), list):
                variant["corpse_equipment_pool"] = list(base["corpse_equipment_pool"])
            floor_match = re.search(r"(\d+)$", room_id)
            floor_text = floor_match.group(1) if floor_match else None
            suffix = f", poziom {floor_text}" if floor_text else ""
            if "Krypta" in zone:
                suffix = f", piętro {floor_text}" if floor_text else ""
            base_name = re.sub(
                r",\s*(?:poziom|piętro)\s+\d+.*$",
                "",
                str(base.get("name", "Przeciwnik")),
                flags=re.I,
            ).strip()
            if available_pool:
                # v1.13.30: wariant ma jeden czytelny archetyp. Nie łączymy
                # dwóch konkurencyjnych nazw separatorem „—”; NVDA i combat
                # feed mają czytać jeden gatunek, zgodnie z kontraktem v1.11.29.
                chosen = available_pool[n % len(available_pool)]
                variant["name"] = f"{chosen}{suffix}"
                distinct_archetypes.add(str(chosen).casefold().strip())
            else:
                # Awaryjny wariant zachowuje bazowy gatunek, ale dostaje
                # pojedynczą nazwę roli zamiast starego formatu „A — B”.
                variant["name"] = f"Patrolowy {base_name} {n + 2}{suffix}".strip()
            # Lekko różny profil walki, bez zwiększania ekonomii za pojedyncze zabicie.
            if n % 2 == 0:
                variant["damage_type"] = "magic" if base.get("damage_type") == "physical" else "physical"
            variant["dense_dungeon_variant"] = True
            # Techniczny wariant zagęszczający zawsze wskazuje jeden
            # kanoniczny gatunek. Bestiariusz/kontrakty używają base template,
            # a nazwa ekranowa pozostaje pojedyncza (bez „A — B”).
            variant["dense_dungeon_base_template"] = base_id
            variant["template_id"] = variant_id
            _catalog_mut.catalog_assign(variant, 'MOB_TEMPLATES', MOB_TEMPLATES, (variant_id,))
            additions.append((room_id, variant_id))
    MOB_SPAWNS.extend(additions)
    return len(additions)


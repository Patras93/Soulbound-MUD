# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _dynamic_regular_mob_pack(room_id, base_id, template, names, floor, floor_word="poziom"):
    spawns = [(room_id, base_id)]
    names = tuple(names or ())
    base_index = (max(1, int(floor)) - 1) % len(names) if names else 0
    if template.get("mythic_crypt_floor") is not None:
        name_kind = "mythic_crypt"
    elif template.get("crypt_floor") is not None:
        name_kind = "crypt"
    elif template.get("mythic_astral_floor") is not None:
        name_kind = "mythic_astral"
    elif template.get("astral_floor") is not None:
        name_kind = "astral"
    elif template.get("giant_fortress_floor") is not None:
        name_kind = "giant"
    else:
        name_kind = str(template.get("profession_dungeon") or "")
    for offset in (1, 2):
        variant_id = f"{base_id}_v{offset + 1}"
        variant = dict(template)
        if isinstance(template.get("drops"), dict):
            variant["drops"] = dict(template["drops"])
        if isinstance(template.get("corpse_equipment_pool"), list):
            variant["corpse_equipment_pool"] = list(template["corpse_equipment_pool"])
        if names:
            variant["name"] = dungeon_mob_display_name_v11336(
                name_kind,
                names[(base_index + offset) % len(names)],
                floor,
                variant=offset,
            )
        else:
            variant["name"] = dungeon_mob_display_name_v11336(
                name_kind or "dungeon",
                template.get("name", "Przeciwnik"),
                floor,
                variant=offset,
            )
        if offset == 1:
            variant["max_hp"] = max(1, int(round(int(template.get("max_hp", 1)) * 1.06)))
            variant["damage_type"] = "magic" if template.get("damage_type") == "physical" else "physical"
        else:
            variant["damage"] = max(1, int(round(int(template.get("damage", 1)) * 1.08)))
        variant["template_id"] = variant_id
        variant["dense_dungeon_variant"] = True
        _catalog_mut.catalog_assign(variant, 'MOB_TEMPLATES', MOB_TEMPLATES, (variant_id,))
        _configure_dynamic_corpse_material(variant)
        spawns.append((room_id, variant_id))
    return spawns


def create_infinite_crypt_floor_definition(floor, mythic=False):
    floor = max(1, int(floor))
    mult = crypt_depth_multiplier(floor)
    econ = _infinite_crypt_economy_floor(floor)
    # EQ rośnie do progresji 600, potem ma twardy cap mimo nieskończonej Krypty.
    tier = min(SOUL_MAX_TIER, max(1, (floor - 1) // 10 + 1))
    if mythic:
        tier = min(SOUL_MAX_TIER, max(20, 20 + (floor - 1) // 10))
    gear = [f"crypt_t{tier}_{slot}" for slot in CLASS_EQUIPMENT_SLOT_DEFS]
    if mythic:
        room_id = mythic_crypt_floor_id(floor)
        exits = {
            "up": "mythic_crypt_gate" if floor == 1 else mythic_crypt_floor_id(floor - 1),
            "down": mythic_crypt_floor_id(floor + 1),
        }
        note = " Przy pierwszym przejściu mityczny boss blokuje zejście do chwili pokonania." if is_mythic_crypt_boss_floor(floor) else ""
        _catalog_mut.catalog_assign({
            "zone": "Mityczna Krypta",
            "name": crypt_floor_display_name(floor, mythic=True),
            "desc": f"Ta mityczna głębokość ma próg trudności {crypt_depth_step(floor)}.{note}",
            "exits": exits,
            "procedural_infinite": True,
        }, 'ROOMS', ROOMS, (room_id,))
        regular_id = f"mythic_crypt_mob_{floor}"
        base_hp = max(1, int(round((4000 + floor * 100) * mult)))
        template = {
            "name": dungeon_mob_display_name_v11336(
                "mythic_crypt",
                "Mityczny Strażnik Głębi",
                floor,
            ),
            "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
            "base_max_hp": base_hp,
            "damage": max(1, int(round((120 + floor) * mult))),
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 800 + econ * 8,
            "gold": 5 + econ // 20,
            "mithril": 0,
            "stat_reward": max(1, int(round((800 + floor * 5) * mult))),
            "class_xp_reward": max(1, int(round((20000 + floor * 300) * mult))),
            "soul_reward": max(1, int(round((4000 + floor * 25) * mult))),
            "drops": {"soul_shard": 1.0},
            "quest_target": None,
            "mythic_crypt_floor": floor,
            "corpse_equipment_pool": list(gear),
            "corpse_equipment_guaranteed": 1,
        }
        _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
        _configure_dynamic_corpse_material(template)
        spawns = _dynamic_regular_mob_pack(
            room_id, regular_id, template, MYTHIC_CRYPT_REGULAR_NAMES, floor, "piętro"
        )
        if is_mythic_crypt_boss_floor(floor):
            boss_id = f"mythic_crypt_boss_{floor}"
            bname, mechanic, mechanic_text = _infinite_mythic_boss_profile(floor)
            boss = {
                "name": bname,
                "max_hp": max(1, int(round((300000 + floor * 5000) * mult))),
                "base_max_hp": max(1, int(round((300000 + floor * 5000) * mult / GLOBAL_MOB_HP_MULTIPLIER))),
                "damage": max(1, int(round((240 + floor * 2) * mult))),
                "damage_type": "magic" if floor % 20 else "physical",
                "silver": 8000 + econ * 40,
                "gold": 60 + econ // 5,
                "mithril": 1,
                "stat_reward": max(1, int(round((3000 + floor * 12) * mult))),
                "class_xp_reward": max(1, int(round((60000 + floor * 700) * mult))),
                "soul_reward": max(1, int(round((9000 + floor * 50) * mult))),
                "drops": {"soul_shard": 1.0, "soul_elixir": 0.70},
                "quest_target": None,
                "mythic_crypt_floor": floor,
                "mythic_crypt_boss": True,
                "boss_mechanic": mechanic,
                "boss_mechanic_text": mechanic_text,
                "corpse_equipment_pool": list(gear),
                "corpse_equipment_guaranteed": 3,
            }
            boss["template_id"] = boss_id
            apply_milestone_boss_identity(boss, "mythic_crypt", floor)
            _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
            _configure_dynamic_corpse_material(boss)
            _ensure_dynamic_boss_key("mythic_crypt", floor)
            spawns.append((room_id, boss_id))
        return room_id, spawns

    room_id = crypt_floor_id(floor)
    exits = {
        "up": "crypt_hall" if floor == 1 else crypt_floor_id(floor - 1),
        "down": crypt_floor_id(floor + 1),
    }
    note = " Przy pierwszym przejściu boss tego progu blokuje zejście do chwili pokonania." if is_crypt_boss_floor(floor) else ""
    _catalog_mut.catalog_assign({
        "zone": "Krypta Nieskończona",
        "name": crypt_floor_display_name(floor),
        "desc": f"Ta głębokość ma próg trudności {crypt_depth_step(floor)}.{note}",
        "exits": exits,
        "procedural_infinite": True,
    }, 'ROOMS', ROOMS, (room_id,))
    regular_id = f"crypt_floor_mob_{floor}"
    base_hp = max(1, int(round((70 + floor * 9) * mult)))
    template = {
        "name": dungeon_mob_display_name_v11336(
            "crypt",
            CRYPT_REGULAR_NAMES[(floor - 1) % len(CRYPT_REGULAR_NAMES)],
            floor,
        ),
        "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
        "base_max_hp": base_hp,
        "damage": max(1, int(round((6 + floor // 3) * mult))),
        "damage_type": "magic" if (floor % 3 == 0 or floor % 4 == 0) else "physical",
        "silver": 8 + econ,
        "gold": 0,
        "mithril": 0,
        "stat_reward": max(1, int(round((20 + floor * 2) * mult))),
        "class_xp_reward": max(1, int(round((450 + floor * 60) * mult))),
        "soul_reward": max(1, int(round((100 + floor * 10) * mult))),
        "drops": {"soul_shard": 1.0},
        "quest_target": None,
        "crypt_floor": floor,
        "corpse_equipment_pool": gear,
        "corpse_equipment_guaranteed": 1,
    }
    _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
    _configure_dynamic_corpse_material(template)
    spawns = _dynamic_regular_mob_pack(
        room_id, regular_id, template, CRYPT_REGULAR_NAMES, floor, "piętro"
    )

    # v1.00.2: Krypta ma mieć wyraźnie więcej Strażników Szkieletów.
    # Dodajemy dwa osobne szkielety na każde zwykłe piętro, niezależnie od
    # rotacji nazw podstawowej trójki. Nie zmienia to statystyk ani balansu
    # pojedynczego moba; zwiększa wyłącznie dostępność tego typu przeciwnika.
    _skeleton_guard_names = (
        "Szkielet Strażnik Kościanej Warty",
        "Szkielet Strażnik Grobowej Warty",
    )
    for skeleton_no in (1, 2):
        skeleton_id = f"{regular_id}_skeleton_guard_{skeleton_no}"
        skeleton = dict(template)
        if isinstance(template.get("drops"), dict):
            skeleton["drops"] = dict(template["drops"])
        if isinstance(template.get("corpse_equipment_pool"), list):
            skeleton["corpse_equipment_pool"] = list(template["corpse_equipment_pool"])
        skeleton["name"] = dungeon_mob_display_name_v11336(
            "crypt",
            _skeleton_guard_names[skeleton_no - 1],
            floor,
            variant=6 + skeleton_no,
        )
        skeleton["template_id"] = skeleton_id
        skeleton["crypt_skeleton_guard_v1002"] = True
        _catalog_mut.catalog_assign(
            skeleton, 'MOB_TEMPLATES', MOB_TEMPLATES, (skeleton_id,)
        )
        _configure_dynamic_corpse_material(skeleton)
        spawns.append((room_id, skeleton_id))

    if floor == 1 or floor % 5 == 0:
        elite_id = f"crypt_elite_guardian_{floor}"
        elite = dict(template)
        elite.update({
            "name": f"Elitarny Strażnik Krypty, piętro {floor}",
            "rank": "elite", "fame_target": True,
            "crypt_floor": floor,
            "max_hp": max(1, int(template["max_hp"] * 3)),
            "damage": max(1, int(template["damage"] * 2)),
            "class_xp_reward": max(1, int(template["class_xp_reward"] * 3)),
            "soul_reward": max(1, int(template["soul_reward"] * 3)),
            "stat_reward": max(1, int(template["stat_reward"] * 3)),
        })
        _catalog_mut.catalog_assign(elite, 'MOB_TEMPLATES', MOB_TEMPLATES, (elite_id,))
        _configure_dynamic_corpse_material(elite)
        spawns.append((room_id, elite_id))

    if is_crypt_boss_floor(floor):
        boss_id = f"crypt_boss_{floor}"
        bname, mechanic, mechanic_text = _infinite_crypt_boss_profile(floor)
        # v1.28.2: lazy generation also creates floors 1-200 after their
        # static rooms are compacted. Those floors MUST retain the authored
        # boss identity and the legacy Soul Trial kill-tag; otherwise floor
        # 120 becomes a generic lord and Tier 13 cannot be completed.
        authored_crypt_boss = floor <= CRYPT_PREGENERATED_MAX_FLOOR and floor in CRYPT_BOSS_NAMES
        if authored_crypt_boss:
            bname = CRYPT_BOSS_NAMES[floor]
            mechanic = CRYPT_BOSS_MECHANICS[floor]
            mechanic_text = CRYPT_BOSS_MECHANIC_TEXT[floor]
        boss = {
            "name": bname,
            "max_hp": max(1, int(round(floor * 1000 * mult))),
            "base_max_hp": max(1, int(round(floor * 1000 * mult / GLOBAL_MOB_HP_MULTIPLIER))),
            "damage": max(1, int(round((16 + floor // 2) * mult))),
            "damage_type": "magic" if floor % 20 == 0 else "physical",
            "silver": 300 + econ * 12,
            "gold": 0,
            "mithril": 0,
            "stat_reward": max(1, int(round((350 + floor * 6) * mult))),
            "class_xp_reward": max(1, int(round((3000 + floor * 160) * mult))),
            "soul_reward": max(1, int(round((600 + floor * 20) * mult))),
            "drops": {"soul_shard": 1.0, "soul_elixir": min(0.50, 0.15 + econ * 0.003)},
            "quest_target": (
                CRYPT_TRIAL_TARGETS.get(floor) if authored_crypt_boss
                else f"crypt_boss_{floor}"
            ),
            "crypt_floor": floor,
            "crypt_boss": True,
            "boss_mechanic": mechanic,
            "boss_mechanic_text": mechanic_text,
            "corpse_equipment_pool": list(gear),
            "corpse_equipment_guaranteed": 3,
        }
        boss["template_id"] = boss_id
        # Milestone titles are procedural identities. Do not replace
        # handcrafted boss names such as Wladca Bezdennych Katakumb at 150
        # or Wladca Dwustu Pieter at 200; the trials name those bosses.
        if not authored_crypt_boss:
            apply_milestone_boss_identity(boss, "crypt", floor)
        _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
        _configure_dynamic_corpse_material(boss)
        _ensure_dynamic_boss_key("crypt", floor)
        spawns.append((room_id, boss_id))
    return room_id, spawns


def create_infinite_astral_floor_definition(floor, mythic=False):
    floor = max(1, int(floor))
    if mythic:
        room_id = mythic_astral_floor_id(floor)
        mult = infinite_continuation_multiplier(floor, MYTHIC_MAX_FLOOR)
        econ = _capped_dungeon_economy_floor(floor)
        theme = infinite_combat_floor_theme("mythic_astral", floor)
        exits = {
            "down": "mythic_astral_gate" if floor == 1 else mythic_astral_floor_id(floor - 1),
            "up": mythic_astral_floor_id(floor + 1),
        }
        note = " Przy pierwszym przejściu mityczny boss blokuje drogę w górę do chwili pokonania." if is_mythic_astral_boss_floor(floor) else ""
        _catalog_mut.catalog_assign({
            "zone": "Mityczna Wieża Astralna",
            "name": f"Mityczna Wieża Astralna, poziom {floor}",
            "desc": (
                f"Mityczny poziom {floor}. Wieża ciągnie się dalej bez końca. "
                f"Próg głębi {max(0, (floor - 1) // 10)}. "
                f"Motyw piętra: {theme['label']} — {theme['desc']}.{note}"
            ),
            "exits": exits,
            "procedural_infinite": True,
        }, 'ROOMS', ROOMS, (room_id,))
        regular_id = f"mythic_astral_mob_{floor}"
        base_hp = max(1, int(round((5000 + floor * 120) * mult)))
        template = {
            "name": dungeon_mob_display_name_v11336(
                "mythic_astral",
                "Mityczny Strażnik Nieskończonego Astralu",
                floor,
            ),
            "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
            "base_max_hp": base_hp,
            "damage": max(1, int(round((145 + floor) * mult))),
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 1000 + econ * 10,
            "gold": 7 + econ // 18,
            "mithril": 0,
            "stat_reward": max(1, int(round((950 + floor * 6) * mult))),
            "class_xp_reward": max(1, int(round((25000 + floor * 350) * mult))),
            "soul_reward": max(1, int(round((5000 + floor * 30) * mult))),
            "drops": {"soul_shard": 0.65},
            "quest_target": None,
            "mythic_astral_floor": floor,
            "corpse_equipment_pool": [
                f"astral_t11_{slot}"
                for slot in CLASS_EQUIPMENT_SLOT_DEFS
            ],
            "corpse_equipment_guaranteed": 1,
        }
        template["template_id"] = regular_id
        _apply_infinite_combat_theme(template, theme)
        _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
        _configure_dynamic_corpse_material(template)
        spawns = _dynamic_regular_mob_pack(
            room_id, regular_id, template, MYTHIC_ASTRAL_REGULAR_NAMES, floor, "poziom"
        )
        if floor % 5 == 0 and not is_mythic_astral_boss_floor(floor):
            challenge_id = f"mythic_astral_challenge_{floor}"
            challenge = _infinite_challenge_template(template, "mythic_astral", floor)
            challenge["elite_base_template"] = regular_id
            _catalog_mut.catalog_assign(challenge, 'MOB_TEMPLATES', MOB_TEMPLATES, (challenge_id,))
            _configure_dynamic_corpse_material(challenge)
            spawns.append((room_id, challenge_id))
        if is_mythic_astral_boss_floor(floor):
            boss_id = f"mythic_astral_boss_{floor}"
            bname, mechanic, mechanic_text = _dynamic_mythic_astral_boss_profile(floor)
            boss_hp = max(1, int(round((400000 + floor * 6000) * mult)))
            boss = {
                "name": bname,
                "max_hp": boss_hp,
                "base_max_hp": max(1, int(round(boss_hp / GLOBAL_MOB_HP_MULTIPLIER))),
                "damage": max(1, int(round((280 + floor * 2) * mult))),
                "damage_type": "magic",
                "silver": 10000 + econ * 45,
                "gold": 80 + econ // 4,
                "mithril": 1,
                "stat_reward": max(1, int(round((3500 + floor * 14) * mult))),
                "class_xp_reward": max(1, int(round((75000 + floor * 800) * mult))),
                "soul_reward": max(1, int(round((11000 + floor * 55) * mult))),
                "drops": {"soul_shard": 1.0, "soul_elixir": 0.80},
                "quest_target": None,
                "mythic_astral_floor": floor,
                "mythic_astral_boss": True,
                "boss_mechanic": mechanic,
                "boss_mechanic_text": mechanic_text,
                "corpse_equipment_pool": [
                    f"astral_t11_{slot}"
                    for slot in CLASS_EQUIPMENT_SLOT_DEFS
                ],
                "corpse_equipment_guaranteed": 3,
            }
            boss["template_id"] = boss_id
            apply_milestone_boss_identity(boss, "mythic_astral", floor)
            _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
            _configure_dynamic_corpse_material(boss)
            _ensure_dynamic_boss_key("mythic_astral", floor)
            spawns.append((room_id, boss_id))
        return room_id, spawns

    floor = max(ASTRAL_MIN_FLOOR, floor)
    room_id = astral_floor_id(floor)
    mult = infinite_continuation_multiplier(floor, ASTRAL_MAX_FLOOR)
    econ = _capped_dungeon_economy_floor(floor)
    theme = infinite_combat_floor_theme("astral", floor)
    exits = {
        "down": "astral_gate" if floor == ASTRAL_MIN_FLOOR else astral_floor_id(floor - 1),
        "up": astral_floor_id(floor + 1),
    }
    note = " Przy pierwszym przejściu boss tego poziomu blokuje drogę w górę do chwili pokonania." if is_astral_boss_floor(floor) else ""
    _catalog_mut.catalog_assign({
        "zone": "Wieża Astralna",
        "name": f"Wieża Astralna, poziom {floor}",
        "desc": (
            f"Poziom {floor}. Wieża nie ma szczytu; gwiezdne kondygnacje "
            f"ciągną się dalej bez końca. Motyw piętra: {theme['label']} — "
            f"{theme['desc']}.{note}"
        ),
        "exits": exits,
        "procedural_infinite": True,
    }, 'ROOMS', ROOMS, (room_id,))
    relative = floor - ASTRAL_MIN_FLOOR
    regular_id = f"astral_floor_mob_{floor}"
    base_hp = max(1, int(round((1050 + relative * 12) * mult)))
    template = {
        "name": dungeon_mob_display_name_v11336(
            "astral",
            ASTRAL_REGULAR_NAMES[relative % len(ASTRAL_REGULAR_NAMES)],
            floor,
        ),
        "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
        "base_max_hp": base_hp,
        "damage": max(1, int(round((42 + relative // 3) * mult))),
        "damage_type": "magic" if floor % 2 else "physical",
        "silver": 120 + max(0, econ - ASTRAL_MIN_FLOOR) * 2,
        "gold": 1 + max(0, econ - ASTRAL_MIN_FLOOR) // 35,
        "mithril": 0,
        "stat_reward": max(1, int(round((230 + relative * 3) * mult))),
        "class_xp_reward": max(1, int(round((7000 + relative * 100) * mult))),
        "soul_reward": max(1, int(round((1250 + relative * 14) * mult))),
        "drops": {"soul_shard": min(0.45, 0.20 + max(0, econ - ASTRAL_MIN_FLOOR) * 0.002)},
        "quest_target": None,
        "astral_floor": floor,
        "corpse_equipment_pool": [
            f"astral_t11_{slot}"
            for slot in CLASS_EQUIPMENT_SLOT_DEFS
        ],
        "corpse_equipment_guaranteed": 1,
    }
    template["template_id"] = regular_id
    _apply_infinite_combat_theme(template, theme)
    _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
    _configure_dynamic_corpse_material(template)
    spawns = _dynamic_regular_mob_pack(
        room_id, regular_id, template, ASTRAL_REGULAR_NAMES, floor, "poziom"
    )
    if floor % 5 == 0 and not is_astral_boss_floor(floor):
        challenge_id = f"astral_challenge_{floor}"
        challenge = _infinite_challenge_template(template, "astral", floor)
        challenge["elite_base_template"] = regular_id
        _catalog_mut.catalog_assign(challenge, 'MOB_TEMPLATES', MOB_TEMPLATES, (challenge_id,))
        _configure_dynamic_corpse_material(challenge)
        spawns.append((room_id, challenge_id))
    if is_astral_boss_floor(floor):
        boss_id = f"astral_boss_{floor}"
        bname, mechanic, mechanic_text = _dynamic_astral_boss_profile(floor)
        boss_hp = max(1, int(round(floor * 1000 * mult)))
        boss = {
            "name": bname,
            "max_hp": boss_hp,
            "base_max_hp": max(1, int(round(boss_hp / GLOBAL_MOB_HP_MULTIPLIER))),
            "damage": max(1, int(round((72 + relative // 2) * mult))),
            "damage_type": "magic" if floor % 20 == 0 else "physical",
            "silver": 900 + max(0, econ - ASTRAL_MIN_FLOOR) * 14,
            "gold": 5 + max(0, econ - ASTRAL_MIN_FLOOR) // 20,
            "mithril": 0,
            "stat_reward": max(1, int(round((900 + relative * 8) * mult))),
            "class_xp_reward": max(1, int(round((15000 + relative * 220) * mult))),
            "soul_reward": max(1, int(round((2400 + relative * 28) * mult))),
            "drops": {"soul_shard": 1.0, "soul_elixir": 0.70},
            "quest_target": None,
            "astral_floor": floor,
            "astral_boss": True,
            "boss_mechanic": mechanic,
            "boss_mechanic_text": mechanic_text,
            "corpse_equipment_pool": [
                f"astral_t11_{slot}"
                for slot in CLASS_EQUIPMENT_SLOT_DEFS
            ],
            "corpse_equipment_guaranteed": 3,
        }
        boss["template_id"] = boss_id
        apply_milestone_boss_identity(boss, "astral", floor)
        _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
        _configure_dynamic_corpse_material(boss)
        _ensure_dynamic_boss_key("astral", floor)
        spawns.append((room_id, boss_id))
    return room_id, spawns


def create_infinite_giant_fortress_floor_definition(floor):
    floor = max(1, int(floor))
    room_id = giant_fortress_floor_id(floor)
    mult = infinite_continuation_multiplier(floor, GIANT_FORTRESS_MAX_FLOOR)
    econ = _capped_dungeon_economy_floor(floor)
    theme = infinite_combat_floor_theme("giant", floor)
    exits = {
        "down": "giant_fortress_gate" if floor == 1 else giant_fortress_floor_id(floor - 1),
        "up": giant_fortress_floor_id(floor + 1),
    }
    note = " Przy pierwszym przejściu boss tego poziomu blokuje drogę w górę do chwili pokonania." if is_giant_fortress_boss_floor(floor) else ""
    _catalog_mut.catalog_assign({
        "zone": "Twierdza Gigantów",
        "name": f"Twierdza Gigantów - poziom {floor}",
        "desc": (
            f"Poziom {floor}. Twierdza ciągnie się bez końca w górę. "
            f"Próg głębi {max(0, (floor - 1) // 10)}. "
            f"Motyw piętra: {theme['label']} — {theme['desc']}.{note}"
        ),
        "exits": exits,
        "procedural_infinite": True,
    }, 'ROOMS', ROOMS, (room_id,))
    names = ("Ogr Miotacz Głazów", "Cyklop Strażnik", "Górski Gigant")
    mob_id = f"giant_fortress_mob_{floor}"
    base_hp = max(1, int(round((450 + floor * 55) * mult)))
    template = {
        "name": dungeon_mob_display_name_v11336(
            "giant",
            names[(floor - 1) % len(names)],
            floor,
        ),
        "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
        "base_max_hp": base_hp,
        "damage": max(1, int(round((18 + floor * 2) * mult))),
        "damage_type": "magic" if floor % 5 == 0 else "physical",
        "silver": 80 + econ * 12,
        "gold": max(0, econ // 10),
        "mithril": 0,
        "stat_reward": max(1, int(round((70 + floor * 5) * mult))),
        "class_xp_reward": max(1, int(round((1200 + floor * 140) * mult))),
        "soul_reward": max(1, int(round((300 + floor * 45) * mult))),
        "drops": {
            "iron_ore": 0.08,
            "silver_ore": 0.08,
            "gold_ore": 0.06,
        },
        "quest_target": None,
        "elite_eligible": True,
        "giant_fortress_floor": floor,
        "corpse_equipment_pool": ["iron_guard", "iron_gauntlets", "iron_leggings", "iron_boots"],
        "corpse_equipment_guaranteed": 1,
    }
    template["template_id"] = mob_id
    _apply_infinite_combat_theme(template, theme)
    _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (mob_id,))
    _configure_dynamic_corpse_material(template)
    spawns = _dynamic_regular_mob_pack(
        room_id, mob_id, template, names, floor, "poziom"
    )
    if floor % 5 == 0 and not is_giant_fortress_boss_floor(floor):
        challenge_id = f"giant_fortress_challenge_{floor}"
        challenge = _infinite_challenge_template(template, "giant", floor)
        challenge["elite_base_template"] = mob_id
        _catalog_mut.catalog_assign(challenge, 'MOB_TEMPLATES', MOB_TEMPLATES, (challenge_id,))
        _configure_dynamic_corpse_material(challenge)
        spawns.append((room_id, challenge_id))
    if is_giant_fortress_boss_floor(floor):
        boss_id = f"giant_fortress_boss_{floor}"
        bname, mechanic, mechanic_text = _dynamic_giant_boss_profile(floor)
        boss_base_hp = max(1, int(round((5000 + floor * 300) * mult)))
        boss = {
            "name": bname,
            "max_hp": max(1, int(round(boss_base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
            "base_max_hp": boss_base_hp,
            "damage": max(1, int(round((45 + floor * 3) * mult))),
            "damage_type": "physical",
            "silver": 1000 + econ * 40,
            "gold": 3 + econ // 10,
            "mithril": 0,
            "stat_reward": max(1, int(round((350 + floor * 8) * mult))),
            "class_xp_reward": max(1, int(round((6000 + floor * 400) * mult))),
            "soul_reward": max(1, int(round((1400 + floor * 100) * mult))),
            "drops": {"soul_elixir": 0.20, "soul_shard": 0.60},
            "quest_target": None,
            "world_boss": True,
            "giant_fortress_boss": True,
            "giant_fortress_floor": floor,
            "boss_mechanic": mechanic,
            "boss_mechanic_text": mechanic_text,
            "corpse_equipment_pool": [
                "iron_helmet", "iron_guard", "iron_gauntlets",
                "iron_leggings", "iron_boots", "forge_charm",
            ],
            "corpse_equipment_guaranteed": 2,
        }
        boss["template_id"] = boss_id
        apply_milestone_boss_identity(boss, "giant", floor)
        _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
        _configure_dynamic_corpse_material(boss)
        _ensure_dynamic_boss_key("giant", floor)
        spawns.append((room_id, boss_id))
    return room_id, spawns


def create_infinite_profession_dungeon_floor_definition(dungeon, floor):
    floor = max(1, int(floor))
    room_id = profession_dungeon_room_id(dungeon, floor)
    required = profession_dungeon_required_tool_level(floor)
    feature = infinite_gathering_floor_feature(dungeon, floor, PROF_DUNGEON_MAX_FLOOR)
    previous = profession_dungeon_room_id(dungeon, floor - 1) if floor > 1 else None
    next_room = profession_dungeon_room_id(dungeon, floor + 1)
    if dungeon == "crystal_mine":
        exits = ({"west": "crystal_chamber", "down": next_room} if floor == 1
                 else {"up": previous, "down": next_room})
        zone = "Kryształowe Groty"
        name = f"Kryształowe Groty, komora {floor}"
        desc = (
            f"Kryształowa komora eksploracyjna {floor}. "
            "Wydobycie jest wyłączone; wszystkie rudy są w Kopalni Głębinowej."
        )
    elif dungeon == "sunken_grotto":
        exits = {"up": "sea_pier" if floor == 1 else previous, "down": next_room}
        zone = "Loch Profesyjny - Zatopiona Grota"
        name = f"Zatopiona Grota, głębokość {floor}"
        desc = (
            f"Nieskończona głębokość {floor}. Wymagane Wędkarstwo level {required}. "
            "Najrzadsze ryby nadal respektują cap Wędkarstwa 600."
            + (f" Specjalny sektor: {feature['label']} — {feature['desc']}." if feature['label'] else "")
        )
        OCEAN_FISHING_ROOMS.add(room_id)
        FISHING_ROOMS.add(room_id)
        MARINE_FISHING_ROOMS.add(room_id)
    elif dungeon == "ancient_forest":
        exits = ({"up": "deep_grove", "south": next_room} if floor == 1
                 else {"north": previous, "south": next_room})
        zone = "Loch Profesyjny - Pradawny Las"
        name = f"Pradawny Las, ostęp {floor}"
        desc = (
            f"Nieskończony ostęp {floor}. Wymagane Drwalstwo level {required}. "
            "Jakość drewna zatrzymuje progresję mocy na levelu 600."
            + (f" Specjalny sektor: {feature['label']} — {feature['desc']}." if feature['label'] else "")
        )
        WOODCUTTING_ROOMS.add(room_id)
    elif dungeon == "alchemy_garden":
        exits = ({"south": "herbalist_hut", "east": next_room} if floor == 1
                 else {"west": previous, "east": next_room})
        zone = "Loch Profesyjny - Ogród Alchemika"
        name = f"Ogród Alchemika, sektor {floor}"
        desc = (
            f"Nieskończony sektor {floor}. Wymagane Zielarstwo level {required}. "
            "Rzadkość ziół respektuje cap progresji 600."
            + (f" Specjalny sektor: {feature['label']} — {feature['desc']}." if feature['label'] else "")
        )
        HERBALISM_ROOMS.add(room_id)
    else:
        return None, []
    _catalog_mut.catalog_assign({
        "zone": zone,
        "name": name,
        "desc": desc,
        "exits": exits,
        "procedural_infinite": True,
        "infinite_gather_feature": feature,
    }, 'ROOMS', ROOMS, (room_id,))
    spawns = profession_dungeon_combat_pack(dungeon, floor)
    return room_id, spawns


def v0874_min_hp_damage_ratio(template):
    """Minimalna trwałość względem obrażeń dla przeciwników, którzy byli papierowi.

    Generowane bossy Krypty/Astralu/Mityczne i Twierdzy Gigantów mają własne
    duże pule HP i nie są dodatkowo pompowane. Zwykłe, rare/elite, mini i
    starsze world bossy dostają tylko dolną granicę, więc mocne template'y
    pozostają bez zmian.
    """
    power = v0866_mob_progression_power(template)
    if template.get("world_boss"):
        if power <= 80:
            return 45
        if power <= 120:
            return 55
        if power <= 160:
            return 70
        return 85
    if template.get("mini_boss"):
        if power <= 20:
            return 30
        if power <= 50:
            return 34
        if power <= 100:
            return 38
        if power <= 150:
            return 42
        return 46
    elite = bool(
        template.get("rare_mob") or template.get("rare_variant")
        or template.get("rare_troll") or template.get("elite_affix")
    )
    if power <= 20:
        base = 20
    elif power <= 50:
        base = 24
    elif power <= 100:
        base = 28
    elif power <= 150:
        base = 32
    else:
        base = 36
    return base + (4 if elite else 0)


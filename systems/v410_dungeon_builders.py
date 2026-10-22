# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def build_astral_tower():
    _catalog_mut.catalog_assign("astral_gate", 'ROOMS', ROOMS, ("shrine", "exits", "east"))
    _catalog_mut.catalog_assign({
        "zone": "Wieża Astralna",
        "name": "Astralna Brama",
        "desc": (
            "Nad urwiskiem unosi się błękitno-fioletowa brama z gwiezdnego szkła. "
            "Za nią zaczyna się Wieża Astralna bez minimalnego Soul Level; barierą jest wyłącznie realna trudność starcia."
        ),
        "exits": {
            "west": "shrine",
            "up": astral_floor_id(ASTRAL_MIN_FLOOR),
        },
    }, 'ROOMS', ROOMS, ("astral_gate",))

    for tier_index, start_floor in enumerate(
        range(ASTRAL_MIN_FLOOR, ASTRAL_MAX_FLOOR + 1, 10),
        1,
    ):
        stat_cycle = (
            "strength", "dexterity", "constitution",
            "intelligence", "willpower"
        )
        defs = (
            ("head", "Astralny Hełm", 6 + tier_index // 2),
            ("body", "Astralny Pancerz", 9 + tier_index),
            ("shield", "Astralna Tarcza", 7 + tier_index // 2),
            ("hands", "Astralne Rękawice", 5 + tier_index // 2),
            ("legs", "Astralne Nogawice", 7 + tier_index // 2),
            ("feet", "Astralne Buty", 5 + tier_index // 2),
            ("charm", "Astralny Talizman", 4 + tier_index // 2),
            ("ring", "Astralny Pierścień", 4 + tier_index // 2),
            ("necklace", "Astralny Naszyjnik", 5 + tier_index // 2),
            ("earring", "Astralny Kolczyk", 4 + tier_index // 2),
            ("shoulders", "Astralne Naramienniki", 7 + tier_index // 2),
            ("belt", "Astralny Pas", 6 + tier_index // 2),
            ("cloak", "Astralna Peleryna", 5 + tier_index // 2),
            ("bracers", "Astralne Karwasze", 5 + tier_index // 2),
            ("bracelet", "Astralna Bransoletka", 4 + tier_index // 2),
            ("accessory", "Astralne Akcesorium", 4 + tier_index // 2),
            ("relic", "Astralny Relikt", 6 + tier_index // 2),
        )
        affix = stat_cycle[(tier_index - 1) % len(stat_cycle)]
        affix_amount = 5 + tier_index // 2
        for slot, label, defense in defs:
            item_id = f"astral_t{tier_index}_{slot}"
            _catalog_mut.catalog_assign({
                "name": f"{label} Kręgu {tier_index}",
                "type": "armor",
                "slot": slot,
                "defense": defense,
                "price": None,
                "desc": (
                    f"Ekwipunek Wieży Astralnej. Krąg {tier_index}. "
                    f"Obrona +{defense}. "
                    f"Bonus: {CRYPT_AFFIXES[affix]} +{affix_amount}."
                ),
                "rarity": "epic",
                "rarity_name": "Astralny",
                "affix": affix,
                "affix_amount": affix_amount,
                "astral_set_tier": tier_index,
            }, 'ITEMS', ITEMS, (item_id,))

    for floor in range(ASTRAL_MIN_FLOOR, ASTRAL_MAX_FLOOR + 1):
        room_id = astral_floor_id(floor)
        exits = {}
        if floor == ASTRAL_MIN_FLOOR:
            exits["down"] = "astral_gate"
        else:
            exits["down"] = astral_floor_id(floor - 1)
        if floor < ASTRAL_MAX_FLOOR:
            exits["up"] = astral_floor_id(floor + 1)

        if floor in ASTRAL_BOSS_FLOORS:
            note = (
                " Strażnik tego poziomu blokuje drogę w górę; Wieża ciągnie się "
                "dalej po jego pokonaniu. Po zaliczeniu checkpointu Astralny Portal "
                "na tym poziomie pozwala wrócić do Astralnej Bramy."
            )
        else:
            note = ""

        _catalog_mut.catalog_assign({
            "zone": "Wieża Astralna",
            "name": f"Wieża Astralna, poziom {floor}",
            "desc": (
                f"Poziom {floor}. Przez przezroczyste ściany widać gwiazdy, "
                f"mgławice i odległe pasma światła.{note}"
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (room_id,))

        tier_index = min(
            11,
            (floor - ASTRAL_MIN_FLOOR) // 10 + 1,
        )
        gear = [
            f"astral_t{tier_index}_{slot}"
            for slot in CLASS_EQUIPMENT_SLOT_DEFS
        ]

        regular_id = f"astral_floor_mob_{floor}"
        regular_name = ASTRAL_REGULAR_NAMES[
            (floor - ASTRAL_MIN_FLOOR) % len(ASTRAL_REGULAR_NAMES)
        ]
        relative = floor - ASTRAL_MIN_FLOOR
        _catalog_mut.catalog_assign({
            "name": dungeon_mob_display_name_v11336(
                "astral", regular_name, floor
            ),
            "max_hp": 1050 + relative * 12,
            "damage": 42 + relative // 3,
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 120 + relative * 2,
            "gold": 1 + relative // 35,
            "mithril": 0,
            "stat_reward": 230 + relative * 3,
            "class_xp_reward": 7000 + relative * 100,
            "soul_reward": 1250 + relative * 14,
            "drops": {
                "soul_shard": min(0.45, 0.20 + relative * 0.002),
            },
            "quest_target": None,
            "astral_floor": floor,
            "corpse_equipment_pool": gear,
            "corpse_equipment_guaranteed": 1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
        MOB_SPAWNS.append((room_id, regular_id))

        if floor in ASTRAL_BOSS_FLOORS:
            boss_id = f"astral_boss_{floor}"
            pool = list(gear)
            relic_id = ASTRAL_BOSS_RELICS[floor][0]
            _catalog_mut.catalog_assign({
                "name": ASTRAL_BOSS_NAMES[floor],
                "max_hp": 3300 + relative * 32,
                "damage": 72 + relative // 2,
                "damage_type": "magic" if floor % 20 == 0 else "physical",
                "silver": 900 + relative * 14,
                "gold": 5 + relative // 20,
                "mithril": 0,
                "stat_reward": 900 + relative * 8,
                "class_xp_reward": 15000 + relative * 220,
                "soul_reward": 2400 + relative * 28,
                "drops": {
                    "soul_shard": 1.0,
                    "soul_elixir": min(0.70, 0.30 + relative * 0.003),
                    relic_id: 1.0 if floor == ASTRAL_MAX_FLOOR else 0.45,
                },
                "quest_target": None,
                "astral_floor": floor,
                "astral_boss": True,
                "boss_mechanic": ASTRAL_BOSS_MECHANICS[floor],
                "boss_mechanic_text": ASTRAL_BOSS_MECHANIC_TEXT[floor],
                "corpse_equipment_pool": pool,
                "corpse_equipment_guaranteed": 3,
            }, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
            MOB_SPAWNS.append((room_id, boss_id))


def build_crypt_200_floors():
    _catalog_mut.catalog_assign(crypt_floor_id(1), 'ROOMS', ROOMS, ("crypt_hall", "exits", "down"))
    _catalog_mut.catalog_assign("crypt_depths", 'ROOMS', ROOMS, ("crypt_hall", "exits", "east"))
    _catalog_mut.catalog_assign({"west": "crypt_hall"}, 'ROOMS', ROOMS, ("crypt_depths", "exits"))

    crypt_slot_specs = {
        "head": ("Hełm Krypty", 1),
        "body": ("Napierśnik Krypty", 3),
        "shield": ("Tarcza Krypty", 2),
        "hands": ("Rękawice Krypty", 0),
        "legs": ("Nogawice Krypty", 2),
        "feet": ("Buty Krypty", 0),
        "charm": ("Talizman Krypty", 0),
        "ring": ("Pierścień Krypty", 0),
        "necklace": ("Naszyjnik Krypty", 1),
        "earring": ("Kolczyk Krypty", 0),
        "shoulders": ("Naramienniki Krypty", 2),
        "belt": ("Pas Krypty", 1),
        "cloak": ("Peleryna Krypty", 0),
        "bracers": ("Karwasze Krypty", 0),
        "bracelet": ("Bransoletka Krypty", -1),
        "accessory": ("Akcesorium Krypty", -1),
        "relic": ("Relikt Krypty", 1),
    }
    for tier in range(1, 41):
        for slot, (label, defense_delta) in crypt_slot_specs.items():
            defense = max(1, 1 + tier // 2 + defense_delta)
            if slot == "body":
                defense = max(defense, 2 + tier)
            item_id=f"crypt_t{tier}_{slot}"
            _catalog_mut.catalog_assign({
                "name":f"{label} Tier {tier}","type":"armor","slot":slot,
                "defense":defense,"price":None,
                "desc":f"Ekwipunek z Krypty. Tier {tier}. Obrona +{defense}.",
            }, 'ITEMS', ITEMS, (item_id,))


    for floor in range(1, CRYPT_MAX_FLOOR+1):
        room_id=crypt_floor_id(floor); exits={}
        exits["up"]="crypt_hall" if floor==1 else crypt_floor_id(floor-1)
        exits["down"]=crypt_floor_id(floor+1)
        if is_crypt_boss_floor(floor):
            note=(
                " Przy pierwszym przejściu boss tego progu blokuje zejście do chwili "
                "pokonania. Po zaliczeniu checkpointu Portal Krypty na tym piętrze "
                "pozwala wrócić do Sali Krypty."
            )
        else:
            note=""
        _catalog_mut.catalog_assign({
            "zone":"Krypta Nieskończona","name":crypt_floor_display_name(floor),
            "desc":(
                f"Ta głębokość ma próg trudności {crypt_depth_step(floor)}. "
                f"Kamienne korytarze stają się coraz bardziej niebezpieczne.{note}"
            ),
            "exits":exits,
        }, 'ROOMS', ROOMS, (room_id,))
        tier=min(40,(floor-1)//10+1)
        gear=[f"crypt_t{tier}_{x}" for x in CLASS_EQUIPMENT_SLOT_DEFS]
        tid=f"crypt_floor_mob_{floor}"
        name=CRYPT_REGULAR_NAMES[(floor-1)%len(CRYPT_REGULAR_NAMES)]
        depth_mult=crypt_depth_multiplier(floor)
        _catalog_mut.catalog_assign({
            "name":dungeon_mob_display_name_v11336(
                "crypt", name, floor
            ),
            "max_hp":max(1,int(round((70+floor*9)*depth_mult))),
            "damage":max(1,int(round((6+floor//3)*depth_mult))),
            "damage_type":"magic" if (floor%3==0 or floor%4==0) else "physical",
            "silver":8+floor,"gold":0,"mithril":0,
            "stat_reward":max(1,int(round((20+floor*2)*depth_mult))),
            "class_xp_reward":max(1,int(round((450+floor*60)*depth_mult))),
            "soul_reward":max(1,int(round((100+floor*10)*depth_mult))),
            "drops":{"soul_shard":1.0},"quest_target":None,
            "crypt_floor":floor,"corpse_equipment_pool":gear,"corpse_equipment_guaranteed":1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (tid,))
        MOB_SPAWNS.append((room_id,tid))
        if floor == 1 or floor % 5 == 0:
            # Dedicated natural elite, never a regular mob or runtime variant.
            elite_id = f"crypt_elite_guardian_{floor}"
            elite_template = dict(MOB_TEMPLATES[tid])
            elite_template.update({
                "name": f"Elitarny Strażnik Krypty, piętro {floor}",
                "rank": "elite", "fame_target": True,
                "crypt_floor": floor,
                "max_hp": max(1, int(elite_template["max_hp"] * 3)),
                "damage": max(1, int(elite_template["damage"] * 2)),
                "class_xp_reward": max(1, int(elite_template["class_xp_reward"] * 3)),
                "soul_reward": max(1, int(elite_template["soul_reward"] * 3)),
                "stat_reward": max(1, int(elite_template["stat_reward"] * 3)),
            })
            _catalog_mut.catalog_assign(elite_template, 'MOB_TEMPLATES', MOB_TEMPLATES, (elite_id,))
            MOB_SPAWNS.append((room_id, elite_id))
        if is_crypt_boss_floor(floor):
            bid=f"crypt_boss_{floor}"; pool=list(gear)
            _catalog_mut.catalog_assign({
                "name":CRYPT_BOSS_NAMES[floor],"max_hp":350+floor*25,
                "damage":max(1,int(round((16+floor//2)*depth_mult))),
                "damage_type":"magic" if floor%20==0 else "physical",
                "silver":300+floor*12,"gold":0,"mithril":0,
                "stat_reward":max(1,int(round((350+floor*6)*depth_mult))),
                "class_xp_reward":max(1,int(round((3000+floor*160)*depth_mult))),
                "soul_reward":max(1,int(round((600+floor*20)*depth_mult))),
                "drops":{
                    "soul_shard":1.0,
                    "soul_elixir":min(0.50,0.15+floor*0.003),
                    BOSS_RELICS[floor][0]: (
                        1.0 if floor == CRYPT_MAX_FLOOR else 0.45
                    ),
                },
                "quest_target":CRYPT_TRIAL_TARGETS.get(floor),
                "crypt_floor":floor,
                "crypt_boss":True,
                "boss_mechanic":CRYPT_BOSS_MECHANICS[floor],
                "boss_mechanic_text":CRYPT_BOSS_MECHANIC_TEXT[floor],
                "corpse_equipment_pool":pool,"corpse_equipment_guaranteed":3,
            }, 'MOB_TEMPLATES', MOB_TEMPLATES, (bid,))
            MOB_SPAWNS.append((room_id,bid))


def build_mythic_endgame():
    # Mythic Crypt opens from the old Crypt depths after floor 200 completion.
    _catalog_mut.catalog_assign("mythic_crypt_gate", 'ROOMS', ROOMS, ("crypt_depths", "exits", "east"))
    _catalog_mut.catalog_assign({
        "zone": "Mityczna Krypta",
        "name": "Brama Mitycznej Krypty",
        "desc": (
            "Czarna brama rezonuje mityczną energią Krypty. "
            "Wejście nie ma wymogu Soul Level, ale już pierwsze piętro jest bardzo trudne."
        ),
        "exits": {
            "west": "crypt_depths",
            "down": mythic_crypt_floor_id(1),
        },
    }, 'ROOMS', ROOMS, ("mythic_crypt_gate",))

    # Mythic Astral opens from the ordinary Astral Gate.
    _catalog_mut.catalog_assign("mythic_astral_gate", 'ROOMS', ROOMS, ("astral_gate", "exits", "east"))
    _catalog_mut.catalog_assign({
        "zone": "Mityczna Wieża Astralna",
        "name": "Brama Mitycznej Wieży Astralnej",
        "desc": (
            "Pęknięcie gwiezdnej przestrzeni prowadzi do trudniejszej "
            "wersji Wieży. Wejście nie ma minimalnego Soul Level; barierą jest realna trudność starcia."
        ),
        "exits": {
            "west": "astral_gate",
            "up": mythic_astral_floor_id(1),
        },
    }, 'ROOMS', ROOMS, ("mythic_astral_gate",))

    crypt_names = (
        "Mityczny Kościany Rycerz",
        "Mityczny Upiór",
        "Mityczny Żniwiarz Grobowca",
        "Mityczny Strażnik Otchłani",
    )
    astral_names = (
        "Mityczny Astralny Strażnik",
        "Mityczny Rycerz Konstelacji",
        "Mityczne Widmo Nebuli",
        "Mityczny Herold Gwiezdnej Burzy",
    )

    for floor in range(MYTHIC_MIN_FLOOR, MYTHIC_MAX_FLOOR + 1):
        # Mythic Crypt
        c_room = mythic_crypt_floor_id(floor)
        c_exits = {
            "up": (
                "mythic_crypt_gate"
                if floor == 1
                else mythic_crypt_floor_id(floor - 1)
            )
        }
        c_exits["down"] = mythic_crypt_floor_id(floor + 1)
        c_note = (
            " Przy pierwszym przejściu mityczny boss blokuje zejście do chwili "
            "pokonania. Po zaliczeniu checkpointu Mityczny Portal Krypty na "
            "tym piętrze pozwala wrócić do Bramy Mitycznej Krypty."
            if is_mythic_crypt_boss_floor(floor)
            else ""
        )
        _catalog_mut.catalog_assign({
            "zone": "Mityczna Krypta",
            "name": crypt_floor_display_name(floor, mythic=True),
            "desc": (
                f"Ta mityczna głębokość ma próg trudności {crypt_depth_step(floor)}. "
                f"Ściany są przesycone ciemną energią.{c_note}"
            ),
            "exits": c_exits,
        }, 'ROOMS', ROOMS, (c_room,))

        c_regular = f"mythic_crypt_mob_{floor}"
        c_depth_mult = crypt_depth_multiplier(floor)
        _catalog_mut.catalog_assign({
            "name": dungeon_mob_display_name_v11336(
                "mythic_crypt",
                crypt_names[(floor - 1) % len(crypt_names)],
                floor,
            ),
            "max_hp": max(1, int(round((4000 + floor * 100) * c_depth_mult))),
            "damage": max(1, int(round((120 + floor) * c_depth_mult))),
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 800 + floor * 8,
            "gold": 5 + floor // 20,
            "mithril": 0,
            "stat_reward": max(1, int(round((800 + floor * 5) * c_depth_mult))),
            "class_xp_reward": max(1, int(round((20000 + floor * 300) * c_depth_mult))),
            "soul_reward": max(1, int(round((4000 + floor * 25) * c_depth_mult))),
            "drops": {"soul_shard": 1.0},
            "quest_target": None,
            "mythic_crypt_floor": floor,
            "corpse_equipment_pool": [
                f"crypt_t{min(40, 20 + (floor - 1) // 10)}_{slot}"
                for slot in CLASS_EQUIPMENT_SLOT_DEFS
            ],
            "corpse_equipment_guaranteed": 1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (c_regular,))
        MOB_SPAWNS.append((c_room, c_regular))

        if is_mythic_crypt_boss_floor(floor):
            c_boss = f"mythic_crypt_boss_{floor}"
            _catalog_mut.catalog_assign({
                "name": dungeon_mob_display_name_v11336(
                    "mythic_crypt",
                    "Mityczny Władca Krypty",
                    floor,
                    variant=3,
                ),
                "max_hp": 100000,
                "damage": max(1, int(round((240 + floor * 2) * c_depth_mult))),
                "damage_type": "magic" if floor % 20 else "physical",
                "silver": 8000 + floor * 40,
                "gold": 60 + floor // 5,
                "mithril": 1 if floor >= 100 else 0,
                "stat_reward": max(1, int(round((3000 + floor * 12) * c_depth_mult))),
                "class_xp_reward": max(1, int(round((60000 + floor * 700) * c_depth_mult))),
                "soul_reward": max(1, int(round((9000 + floor * 50) * c_depth_mult))),
                "drops": {
                    "soul_shard": 1.0,
                    "soul_elixir": 0.70,
                },
                "quest_target": None,
                "mythic_crypt_floor": floor,
                "mythic_crypt_boss": True,
                "boss_mechanic": "two_hundred_lord",
                "boss_mechanic_text": (
                    "Mityczna Bariera, druga faza i silny "
                    "magiczny kontratak co trzecią odpowiedź."
                ),
                "corpse_equipment_pool": [
                    f"crypt_t{min(40, 20 + (floor - 1) // 10)}_{slot}"
                    for slot in CLASS_EQUIPMENT_SLOT_DEFS
                ],
                "corpse_equipment_guaranteed": 3,
            }, 'MOB_TEMPLATES', MOB_TEMPLATES, (c_boss,))
            MOB_SPAWNS.append((c_room, c_boss))

        # Mythic Astral Tower
        a_room = mythic_astral_floor_id(floor)
        a_exits = {
            "down": (
                "mythic_astral_gate"
                if floor == 1
                else mythic_astral_floor_id(floor - 1)
            )
        }
        if floor < MYTHIC_MAX_FLOOR:
            a_exits["up"] = mythic_astral_floor_id(floor + 1)
        a_note = (
            " Przy pierwszym przejściu mityczny boss blokuje drogę w górę; po "
            "pokonaniu próg zostaje odblokowany na stałe. Po zaliczeniu checkpointu "
            "Mityczny Astralny Portal na tym poziomie pozwala wrócić do "
            "Mitycznej Astralnej Bramy."
            if floor in MYTHIC_BOSS_FLOORS
            else ""
        )
        _catalog_mut.catalog_assign({
            "zone": "Mityczna Wieża Astralna",
            "name": f"Mityczna Wieża Astralna, poziom {floor}",
            "desc": (
                f"Mityczny poziom {floor}. Pierwsze 200 poziomów to ręcznie przygotowana część Wieży. "
                f"Gwiazdy wydają się nienaturalnie blisko.{a_note}"
            ),
            "exits": a_exits,
        }, 'ROOMS', ROOMS, (a_room,))

        a_regular = f"mythic_astral_mob_{floor}"
        _catalog_mut.catalog_assign({
            "name": dungeon_mob_display_name_v11336(
                "mythic_astral",
                astral_names[(floor - 1) % len(astral_names)],
                floor,
            ),
            "max_hp": 5000 + floor * 120,
            "damage": 145 + floor,
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 1000 + floor * 10,
            "gold": 7 + floor // 18,
            "mithril": 0,
            "stat_reward": 950 + floor * 6,
            "class_xp_reward": 25000 + floor * 350,
            "soul_reward": 5000 + floor * 30,
            "drops": {"soul_shard": 0.65},
            "quest_target": None,
            "mythic_astral_floor": floor,
            "corpse_equipment_pool": [
                f"astral_t11_{slot}"
                for slot in CLASS_EQUIPMENT_SLOT_DEFS
            ],
            "corpse_equipment_guaranteed": 1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (a_regular,))
        MOB_SPAWNS.append((a_room, a_regular))

        if floor in MYTHIC_BOSS_FLOORS:
            a_boss = f"mythic_astral_boss_{floor}"
            _catalog_mut.catalog_assign({
                "name": dungeon_mob_display_name_v11336(
                    "mythic_astral",
                    "Mityczny Suweren Astralny",
                    floor,
                    variant=4,
                ),
                "max_hp": 120000,
                "damage": 280 + floor * 2,
                "damage_type": "magic",
                "silver": 10000 + floor * 45,
                "gold": 80 + floor // 4,
                "mithril": 1 if floor >= 80 else 0,
                "stat_reward": 3500 + floor * 14,
                "class_xp_reward": 75000 + floor * 800,
                "soul_reward": 11000 + floor * 55,
                "drops": {
                    "soul_shard": 1.0,
                    "soul_elixir": 0.80,
                },
                "quest_target": None,
                "mythic_astral_floor": floor,
                "mythic_astral_boss": True,
                "boss_mechanic": "astral_sovereign",
                "boss_mechanic_text": (
                    "Mityczna Bariera Suwerena, druga faza i "
                    "Astralne Załamanie."
                ),
                "corpse_equipment_pool": [
                    f"astral_t11_{slot}"
                    for slot in CLASS_EQUIPMENT_SLOT_DEFS
                ],
                "corpse_equipment_guaranteed": 3,
            }, 'MOB_TEMPLATES', MOB_TEMPLATES, (a_boss,))
            MOB_SPAWNS.append((a_room, a_boss))


def build_profession_dungeons():
    # v0.25.1: istnieje tylko jedna aktywna kopalnia — Kopalnia Głębinowa.
    # Dawna Kopalnia Kryształów pozostaje połączona wyłącznie jako zwykły
    # obszar eksploracyjny "Kryształowe Groty" bez możliwości wydobycia.
    _catalog_mut.catalog_assign(profession_dungeon_room_id("crystal_mine", 1), 'ROOMS', ROOMS, ("crystal_chamber", "exits", "east"))
    # 2. Zatopiona Grota - fishing
    _catalog_mut.catalog_assign(profession_dungeon_room_id("sunken_grotto", 1), 'ROOMS', ROOMS, ("sea_pier", "exits", "down"))
    # 3. Pradawny Las - woodcutting
    _catalog_mut.catalog_assign(profession_dungeon_room_id("ancient_forest", 1), 'ROOMS', ROOMS, ("deep_grove", "exits", "south"))
    # 4. Ogród Alchemika - herbalism
    _catalog_mut.catalog_assign(profession_dungeon_room_id("alchemy_garden", 1), 'ROOMS', ROOMS, ("herbalist_hut", "exits", "east"))

    for floor in range(1, PROF_DUNGEON_MAX_FLOOR + 1):
        required = profession_dungeon_required_tool_level(floor)

        # Crystal Mine, down = deeper.
        rid = profession_dungeon_room_id("crystal_mine", floor)
        exits = {
            "up": (
                "crystal_chamber"
                if floor == 1
                else profession_dungeon_room_id(
                    "crystal_mine", floor - 1
                )
            )
        }
        if floor < PROF_DUNGEON_MAX_FLOOR:
            exits["down"] = profession_dungeon_room_id(
                "crystal_mine", floor + 1
            )
        _catalog_mut.catalog_assign({
            "zone": "Kryształowe Groty",
            "name": f"Kryształowe Groty, komora {floor}",
            "desc": (
                f"Kryształowa komora eksploracyjna {floor}. "
                "Nie prowadzi się tu wydobycia. Wszystkie rudy i Górnictwo są w Kopalni Głębinowej."
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (rid,))
        # Brak MINING_ROOMS: to nie jest już aktywna kopalnia.

        # Sunken Grotto, down = deeper.
        rid = profession_dungeon_room_id("sunken_grotto", floor)
        exits = {
            "up": (
                "sea_pier"
                if floor == 1
                else profession_dungeon_room_id(
                    "sunken_grotto", floor - 1
                )
            )
        }
        if floor < PROF_DUNGEON_MAX_FLOOR:
            exits["down"] = profession_dungeon_room_id(
                "sunken_grotto", floor + 1
            )
        _catalog_mut.catalog_assign({
            "zone": "Loch Profesyjny - Zatopiona Grota",
            "name": f"Zatopiona Grota, głębokość {floor}",
            "desc": (
                f"Podwodne łowisko {floor}. Pierwsze 20 poziomów to ręcznie przygotowana część, a dalsza głębokość nie ma limitu. "
                f"Wymagane Wędkarstwo level {required}. "
                "Lepsza Wędka odblokowuje lepsze ryby i bonusy jakości. "
                "Niższe komory prowadzą do coraz rzadszych ryb."
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (rid,))
        if floor <= 10:
            SEA_FISHING_ROOMS.add(rid)
        else:
            OCEAN_FISHING_ROOMS.add(rid)
        FISHING_ROOMS.add(rid)
        MARINE_FISHING_ROOMS.add(rid)

        # Ancient Forest, south = deeper.
        rid = profession_dungeon_room_id("ancient_forest", floor)
        exits = {
            "north": (
                "deep_grove"
                if floor == 1
                else profession_dungeon_room_id(
                    "ancient_forest", floor - 1
                )
            )
        }
        if floor < PROF_DUNGEON_MAX_FLOOR:
            exits["south"] = profession_dungeon_room_id(
                "ancient_forest", floor + 1
            )
        _catalog_mut.catalog_assign({
            "zone": "Loch Profesyjny - Pradawny Las",
            "name": f"Pradawny Las, ostęp {floor}",
            "desc": (
                f"Pradawny ostęp {floor}. Pierwsze 20 ostępów to ręcznie przygotowana część, a dalsza głębokość nie ma limitu. "
                f"Wymagane Drwalstwo level {required}. "
                "Lepsza Piła odblokowuje lepsze drewno i bonusy jakości. "
                "Głębsze ostępy dają dostęp do rzadszego drewna."
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (rid,))
        WOODCUTTING_ROOMS.add(rid)

        # Alchemy Garden, east = deeper.
        rid = profession_dungeon_room_id("alchemy_garden", floor)
        exits = {
            "west": (
                "herbalist_hut"
                if floor == 1
                else profession_dungeon_room_id(
                    "alchemy_garden", floor - 1
                )
            )
        }
        if floor < PROF_DUNGEON_MAX_FLOOR:
            exits["east"] = profession_dungeon_room_id(
                "alchemy_garden", floor + 1
            )
        _catalog_mut.catalog_assign({
            "zone": "Loch Profesyjny - Ogród Alchemika",
            "name": f"Ogród Alchemika, sektor {floor}",
            "desc": (
                f"Alchemiczny sektor {floor}. Pierwsze 20 sektorów to ręcznie przygotowana część, a dalsza głębokość nie ma limitu. "
                f"Wymagane Zielarstwo level {required}. "
                "Lepszy Sierp odblokowuje lepsze zioła i bonusy jakości. "
                "Głębsze sektory zawierają coraz rzadsze rośliny."
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (rid,))
        HERBALISM_ROOMS.add(rid)


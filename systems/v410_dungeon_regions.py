# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def build_mountain_region_and_herb_meadows():
    # -----------------------------
    # Wioska Górska i góry
    # -----------------------------
    _catalog_mut.catalog_assign("mountain_pass", 'ROOMS', ROOMS, ("hill", "exits", "east"))

    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Górska Przełęcz",
        "desc": (
            "Wąska kamienna przełęcz pnie się między wysokimi skałami. "
            "Na wschodzie widać dym z kominów Wioski Górskiej."
        ),
        "exits": {
            "west": "hill",
            "east": "mountain_village",
        },
    }, 'ROOMS', ROOMS, ("mountain_pass",))

    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Plac Wioski Górskiej",
        "desc": (
            "Kamienne domy stoją wokół niewielkiego placu. "
            "Mieszkańcy mówią o trollach wychodzących z jaskini "
            "na południowym stoku."
        ),
        "exits": {
            "west": "mountain_pass",
            "north": "mountain_guard_house",
            "east": "mountain_inn",
            "south": "mountain_troll_trail",
        },
    }, 'ROOMS', ROOMS, ("mountain_village",))

    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Dom Straży Górskiej",
        "desc": (
            "Prosty kamienny budynek służy strażnikom wioski. "
            "Na stole leżą mapy szlaków prowadzących do Jaskini Trolli."
        ),
        "exits": {"south": "mountain_village"},
    }, 'ROOMS', ROOMS, ("mountain_guard_house",))

    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Górska Gospoda",
        "desc": (
            "Ciepła gospoda daje schronienie przed górskim wiatrem. "
            "Podróżnicy opowiadają o potężnym Królu Trolli."
        ),
        "exits": {"west": "mountain_village"},
    }, 'ROOMS', ROOMS, ("mountain_inn",))

    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Szlak Trolli",
        "desc": (
            "Ścieżka prowadzi między głazami pełnymi wielkich śladów. "
            "Na południu czernieje wejście do Jaskini Trolli."
        ),
        "exits": {
            "north": "mountain_village",
            "south": "troll_cave_entrance",
        },
    }, 'ROOMS', ROOMS, ("mountain_troll_trail",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Wejście do Jaskini Trolli",
        "desc": (
            "Szerokie wejście prowadzi w głąb góry. "
            "W powietrzu czuć wilgoć i dym z prymitywnych palenisk."
        ),
        "exits": {
            "north": "mountain_troll_trail",
            "down": "troll_cave_1",
        },
    }, 'ROOMS', ROOMS, ("troll_cave_entrance",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Jaskinia Trolli - Kamienna Sala",
        "desc": (
            "Wielka komora jest zasłana połamanymi kośćmi i głazami. "
            "Trolle urządziły tu pierwszy posterunek."
        ),
        "exits": {
            "up": "troll_cave_entrance",
            "east": "troll_cave_2",
        },
    }, 'ROOMS', ROOMS, ("troll_cave_1",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Jaskinia Trolli - Wilgotny Tunel",
        "desc": (
            "Woda ścieka po ścianach, a ciężkie kroki odbijają się echem."
        ),
        "exits": {
            "west": "troll_cave_1",
            "east": "troll_cave_3",
        },
    }, 'ROOMS', ROOMS, ("troll_cave_2",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Jaskinia Trolli - Sala Głazów",
        "desc": (
            "Ogromne głazy służą trollom za stoły i broń. "
            "Na wschodzie znajduje się legowisko ich przywódcy."
        ),
        "exits": {
            "west": "troll_cave_2",
            "east": "troll_king_den",
        },
    }, 'ROOMS', ROOMS, ("troll_cave_3",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Legowisko Króla Trolli",
        "desc": (
            "Największa komora jaskini. Pośrodku stoi kamienny tron "
            "otoczony stosami kości i zdobytego żelaza."
        ),
        "exits": {"west": "troll_cave_3"},
    }, 'ROOMS', ROOMS, ("troll_king_den",))

    # -----------------------------
    # NPC + quest na trolle
    # -----------------------------
    _catalog_mut.catalog_assign({
        "name": "Plaga Trolli",
        "giver": "Strażnik Górski Eryk",
        "kind": "kill",
        "target": "mountain_troll",
        "needed": 12,
        "description": (
            "Pokonaj 12 trolli w Jaskini Trolli i wróć do "
            "Strażnika Górskiego Eryka w Wiosce Górskiej."
        ),
        "reward_stat_progress": 280,
        "reward_silver": 750,
        "reward_gold": 2,
        "reward_mithril": 0,
        "reward_items": {
            "healing_potion": 3,
            "soul_shard": 1,
        },
        "repeatable": False,
    }, 'QUESTS', QUESTS, ("mountain_troll_hunt",))

    _catalog_mut.catalog_assign({
        "name": "Strażnik Górski Eryk",
        "room": "mountain_guard_house",
        "dialogue": (
            "Trolle z południowej jaskini coraz częściej schodzą "
            "pod samą wioskę. Potrzebujemy kogoś, kto przerzedzi ich szeregi."
        ),
        "quest": "mountain_troll_hunt",
    }, 'NPCS', NPCS, ("mountain_guard_eryk",))

    # -----------------------------
    # Trolle i boss
    # Wartości bazowe są potem mnożone przez globalne x2 HP.
    # -----------------------------
    _catalog_mut.catalog_assign({
        "name": "Kieł Króla Trolli",
        "type": "armor",
        "slot": "charm",
        "defense": 7,
        "price": None,
        "desc": (
            "Unikalne trofeum Króla Trolli. Obrona +7. "
            "Bonus: Kondycja +6."
        ),
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "constitution",
        "affix_amount": 6,
    }, 'ITEMS', ITEMS, ("troll_king_tusk",))

    _catalog_mut.catalog_assign({
        "name": "Górski Troll",
        "max_hp": 300,
        "damage": 24,
        "damage_type": "physical",
        "silver": 90,
        "gold": 1,
        "mithril": 0,
        "stat_reward": 85,
        "class_xp_reward": 1400,
        "soul_reward": 360,
        "drops": {
            "healing_potion": 0.08,
            "iron_ore": 0.12,
        },
        "quest_target": "mountain_troll",
        "corpse_equipment_pool": [
            "iron_guard", "iron_gauntlets", "iron_boots"
        ],
        "corpse_equipment_guaranteed": 1,
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("mountain_troll",))

    _catalog_mut.catalog_assign({
        "name": "Troll Osiłek",
        "max_hp": 420,
        "damage": 31,
        "damage_type": "physical",
        "silver": 130,
        "gold": 1,
        "mithril": 0,
        "stat_reward": 115,
        "class_xp_reward": 1900,
        "soul_reward": 470,
        "drops": {
            "healing_potion": 0.12,
            "silver_ore": 0.10,
        },
        "quest_target": "mountain_troll",
        "corpse_equipment_pool": [
            "iron_guard", "iron_leggings",
            "iron_gauntlets", "iron_boots"
        ],
        "corpse_equipment_guaranteed": 1,
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("troll_brute",))

    _catalog_mut.catalog_assign({
        "name": "Troll Szaman",
        "max_hp": 360,
        "damage": 29,
        "damage_type": "magic",
        "silver": 120,
        "gold": 2,
        "mithril": 0,
        "stat_reward": 110,
        "class_xp_reward": 2000,
        "soul_reward": 500,
        "drops": {
            "mana_potion": 0.15,
            "soul_shard": 0.15,
        },
        "quest_target": "mountain_troll",
        "corpse_equipment_pool": [
            "forge_charm", "lucky_charm"
        ],
        "corpse_equipment_guaranteed": 1,
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("troll_shaman",))

    _catalog_mut.catalog_assign({
        "name": "Król Trolli Grum",
        "max_hp": 900,
        "damage": 48,
        "damage_type": "physical",
        "silver": 1200,
        "gold": 6,
        "mithril": 0,
        "stat_reward": 420,
        "class_xp_reward": 6500,
        "soul_reward": 1500,
        "drops": {
            "soul_elixir": 0.25,
            "troll_king_tusk": 0.45,
        },
        "quest_target": "mountain_troll",
        "boss_mechanic": "troll_king",
        "boss_mechanic_text": (
            "Król Trolli używa ciężkich fizycznych uderzeń. "
            "Poniżej połowy HP staje się wyraźnie groźniejszy."
        ),
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_helmet", "iron_guard", "iron_gauntlets",
            "iron_leggings", "iron_boots", "forge_charm"
        ],
        "corpse_equipment_guaranteed": 2,
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("troll_king",))

    MOB_SPAWNS.extend([
        ("mountain_troll_trail", "mountain_troll"),
        ("troll_cave_1", "mountain_troll"),
        ("troll_cave_1", "mountain_troll"),
        ("troll_cave_2", "mountain_troll"),
        ("troll_cave_2", "troll_brute"),
        ("troll_cave_3", "mountain_troll"),
        ("troll_cave_3", "troll_brute"),
        ("troll_cave_3", "troll_shaman"),
        ("troll_king_den", "troll_king"),
    ])

    # -----------------------------
    # Osobne łąki pod konkretne zioła
    # -----------------------------
    _catalog_mut.catalog_assign("herb_meadow_hub", 'ROOMS', ROOMS, ("flower_meadow", "exits", "north"))

    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Rozdroże Łąk Zielarskich",
        "desc": (
            "Kilka wyraźnie oddzielonych łąk ciągnie się w różnych "
            "kierunkach. Każda jest znana z jednego dominującego zioła."
        ),
        "exits": {
            "south": "flower_meadow",
            "north": "chamomile_meadow",
            "east": "lavender_meadow",
            "west": "yarrow_meadow",
        },
    }, 'ROOMS', ROOMS, ("herb_meadow_hub",))

    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Rumianku",
        "desc": "Białe kwiaty rumianku pokrywają niemal całą łąkę.",
        "exits": {
            "south": "herb_meadow_hub",
            "north": "nettle_meadow",
        },
    }, 'ROOMS', ROOMS, ("chamomile_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Pokrzywy",
        "desc": "Gęste kępy pokrzywy rosną między niskimi kamieniami.",
        "exits": {
            "south": "chamomile_meadow",
            "north": "lemon_balm_meadow",
        },
    }, 'ROOMS', ROOMS, ("nettle_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Melisy",
        "desc": "Powietrze wypełnia łagodny cytrynowy zapach melisy.",
        "exits": {"south": "nettle_meadow"},
    }, 'ROOMS', ROOMS, ("lemon_balm_meadow",))

    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Lawendy",
        "desc": "Fioletowe pasy lawendy ciągną się po łagodnym zboczu.",
        "exits": {
            "west": "herb_meadow_hub",
            "east": "sage_meadow",
        },
    }, 'ROOMS', ROOMS, ("lavender_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Szałwii",
        "desc": "Srebrzystozielone liście szałwii rosną w suchszej części łąk.",
        "exits": {
            "west": "lavender_meadow",
            "east": "valerian_meadow",
        },
    }, 'ROOMS', ROOMS, ("sage_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Waleriany",
        "desc": "Wysokie łodygi waleriany rosną w spokojnej kotlinie.",
        "exits": {"west": "sage_meadow"},
    }, 'ROOMS', ROOMS, ("valerian_meadow",))

    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Krwawnika",
        "desc": "Drobne białe kwiaty krwawnika tworzą szerokie skupiska.",
        "exits": {
            "east": "herb_meadow_hub",
            "west": "ginseng_meadow",
        },
    }, 'ROOMS', ROOMS, ("yarrow_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Żeń-szenia",
        "desc": "W zacienionych zagłębieniach rośnie dziki żeń-szeń.",
        "exits": {
            "east": "yarrow_meadow",
            "west": "moonflower_meadow",
        },
    }, 'ROOMS', ROOMS, ("ginseng_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Księżycowego Kwiatu",
        "desc": (
            "Blade kwiaty rosną na chłodnej łące, a ich płatki "
            "lekko połyskują nawet w cieniu."
        ),
        "exits": {"east": "ginseng_meadow"},
    }, 'ROOMS', ROOMS, ("moonflower_meadow",))

    # Istniejąca Łąka Mięty jest także pełną łąką tematyczną.
    _catalog_mut.catalog_assign("Łąki Zielarskie", 'ROOMS', ROOMS, ("mint_meadow", "zone"))
    _catalog_mut.catalog_assign("Mięta dominuje na tej łące. Zbieranie tutaj daje Miętę "
        "jako podstawowy plon.", 'ROOMS', ROOMS, ("mint_meadow", "desc"))

    for room_id in HERB_SPECIFIC_MEADOWS:
        HERBALISM_ROOMS.add(room_id)
        MEADOW_HERBALISM_ROOMS.add(room_id)


def _register_elite_variants(base_ids):
    for base_id in tuple(base_ids):
        base_template = MOB_TEMPLATES.get(base_id)
        if not base_template:
            continue
        for affix_id, definition in ELITE_AFFIXES.items():
            elite_id = f"{base_id}__elite_{affix_id}"
            elite = dict(base_template)
            elite["name"] = (
                f"{definition['label']} "
                f"{base_template['name']}"
            )
            elite["elite_affix"] = affix_id
            elite["elite_affix_text"] = definition["text"]
            elite["elite_base_template"] = base_id
            elite["max_hp"] = max(
                1,
                int(round(
                    int(base_template["max_hp"])
                    * (1.20 if affix_id == "armored" else 1.10)
                )),
            )
            elite["damage"] = max(
                1,
                int(round(
                    int(base_template["damage"])
                    * (
                        1.15
                        if affix_id in {
                            "fire", "astral"
                        }
                        else 1.05
                    )
                )),
            )
            elite["silver"] = int(
                round(
                    int(base_template.get("silver", 0))
                    * 1.50
                )
            )
            elite["gold"] = int(
                base_template.get("gold", 0)
            ) + 1
            elite["soul_reward"] = int(
                round(
                    int(
                        base_template.get(
                            "soul_reward", 0
                        )
                    )
                    * 1.40
                )
            )
            elite["class_xp_reward"] = int(
                round(
                    int(base_template.get("class_xp_reward", max(50, int(base_template.get("stat_reward", 1)) * 10)))
                    * 1.40
                )
            )
            elite["stat_reward"] = int(round(int(base_template.get("stat_reward", 0)) * 1.25))
            elite["drops"] = dict(base_template.get("drops", {}))
            elite["drops"].setdefault("soul_shard", 0.18)
            _catalog_mut.catalog_assign(elite, 'MOB_TEMPLATES', MOB_TEMPLATES, (elite_id,))


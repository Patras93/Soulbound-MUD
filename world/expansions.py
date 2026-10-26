from data import catalog_mutations as _catalog_mut
# v0.45.0: explicit imports; no compatibility-runtime injection.
from core.bootstrap_economy_professions import QUEST_REPEAT_COOLDOWN_SECONDS
from core.classes_skills import ORE_ATLAS_LEVELS, ORE_MINE_FLOOR_MINIMUMS
from core.mines_threat import CHARACTER_BOUND_TOOL_IDS, EXP_AREAS, GUIDE_DESTINATION_ALIASES, TOOL_SHOP_ROOMS
from core.progression_resources import (
    FISH_ATLAS_ALL,
    FISH_RESOURCE_IDS,
    HERB_ATLAS_ALL,
    HERB_RESOURCE_IDS,
    ORE_ATLAS_ALL,
    ORE_RESOURCE_IDS,
    RIVER_FISHING_ROOMS,
    WOOD_ATLAS_ALL,
    WOOD_RESOURCE_IDS,
)
from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES, MOB_DESCRIPTIONS
from systems.dungeons_regions import (
    FISHING_ROOMS,
    GIANT_FORTRESS_BOSS_FLOORS,
    GIANT_FORTRESS_BOSS_MECHANICS,
    GIANT_FORTRESS_BOSS_NAMES,
    GIANT_FORTRESS_MAX_FLOOR,
    HERBALISM_ROOMS,
    ITEMS,
    MOB_SPAWNS,
    MOB_TEMPLATES,
    NPCS,
    QUESTS,
    RARE_TROLL_VARIANTS,
    ROOMS,
    WOODCUTTING_ROOMS,
    _register_elite_variants,
    _register_rare_variants,
    giant_fortress_floor_id,
)
from systems.equipment_crafting import (
    FISH_STORAGE_IDS,
    MINING_STORAGE_IDS,
    ORE_STORAGE_IDS,
    SHOPS,
    SHOP_SELLERS,
)
from systems.items_resources import HERB_STORAGE_IDS, WOOD_STORAGE_IDS

def build_mountain_crafting_expansion():
    """Compatibility entrypoint for the isolated authored expansion."""
    from world.expansion_mountain import build_mountain_crafting_expansion as _build
    return _build()

    

def build_world_expansion_i():
    """Compatibility entrypoint: preserve EXP_AREAS' historical facade binding."""
    global EXP_AREAS
    from world.expansion_frontiers import build_world_expansion_i as _build
    from world import expansion_frontiers as _impl
    _impl.EXP_AREAS = EXP_AREAS
    _build()
    EXP_AREAS = _impl.EXP_AREAS



def build_world_expansion_ii():
    """Compatibility entrypoint: preserve EXP_AREAS' historical facade binding."""
    global EXP_AREAS
    from world.expansion_frontiers import build_world_expansion_ii as _build
    from world import expansion_frontiers as _impl
    _impl.EXP_AREAS = EXP_AREAS
    _build()
    EXP_AREAS = _impl.EXP_AREAS

def build_high_end_mob_pack():
    """Compatibility entrypoint for the isolated authored expansion."""
    from world.expansion_high_end import build_high_end_mob_pack as _build
    return _build()


def configure_profession_tool_sellers():
    """Compatibility entrypoint for the isolated authored expansion."""
    from world.expansion_services import configure_profession_tool_sellers as _build
    return _build()

def configure_v0800_help_info():
    """Compatibility entrypoint for the isolated authored expansion."""
    from world.expansion_services import configure_v0800_help_info as _build
    return _build()

def configure_v081_help_info():
    """Compatibility entrypoint for the isolated authored expansion."""
    from world.expansion_services import configure_v081_help_info as _build
    return _build()

def build_paid_training_guild_expansion():
    """Compatibility entrypoint for the isolated authored expansion."""
    from world.expansion_services import build_paid_training_guild_expansion as _build
    return _build()


# ============================================================
# v0.8.19 - Forest, Wolves & Quest Balance Expansion
# ============================================================
def build_forest_wolves_and_quest_balance():
    """Compatibility entrypoint: preserve EXP_AREAS' historical facade binding."""
    global EXP_AREAS
    from world.expansion_frontiers import build_forest_wolves_and_quest_balance as _build
    from world import expansion_frontiers as _impl
    _impl.EXP_AREAS = EXP_AREAS
    _build()
    EXP_AREAS = _impl.EXP_AREAS


REGIONAL_SET_BONUSES = {
    "cultist": {"name":"Set Kultystów Pustki", "hp":1.08, "damage":1.18, "defense":1.12},
    "necropolis": {"name":"Set Umarłego Króla", "hp":1.12, "damage":1.14, "defense":1.18},
    "ice_caves": {"name":"Set Wiecznego Lodu", "hp":1.10, "damage":1.16, "defense":1.16},
}

TREASURE_CHEST_RARITIES = {
    "common": ("Zwykła", 62),
    "rare": ("Rzadka", 25),
    "epic": ("Epicka", 10),
    "legendary": ("Legendarna", 3),
}
TREASURE_CHESTS = {}


def normalize_authored_mob_names_v11128():
    """Keep authored mob display names singular and screen-reader friendly."""
    canonical = {
        "goblin_scout": "Goblin Zwiadowca",
        "deep_troll_shaman": "Troll Jaskiniowy",
    }
    for mob_id, template in MOB_TEMPLATES.items():
        if not isinstance(template, dict):
            continue
        if mob_id in canonical:
            template["name"] = canonical[mob_id]
        name = str(template.get("name") or "").strip()
        # Procedural Nemesis intentionally uses an em dash as a rank marker.
        # Authored mobs must expose one name, never two competing names.
        if " — " in name and "NEMESIS" not in name and not template.get("v029_dynamic_event"):
            parts = [part.strip() for part in name.split(" — ") if part.strip()]
            if len(parts) == 2:
                template["name"] = parts[0]


normalize_authored_mob_names_v11128()


def build_elite_rare_named_loot_expansion():
    # --------------------------------------------------------
    # Regional sets: 3 x 6 pieces, thresholds 2/4/6.
    # --------------------------------------------------------
    slots = (
        ("head","Hełm"),("body","Pancerz"),("hands","Rękawice"),
        ("legs","Nogawice"),("feet","Buty"),("charm","Talizman"),
    )
    set_specs = {
        "cultist": ("Kultysty Pustki", 8, "intelligence", 4),
        "necropolis": ("Umarłego Króla", 10, "willpower", 5),
        "ice_caves": ("Wiecznego Lodu", 11, "constitution", 5),
    }
    regional_items = {}
    for set_id, (label, defense_base, affix, amount) in set_specs.items():
        ids=[]
        for idx,(slot,slot_name) in enumerate(slots):
            item_id=f"regional_{set_id}_{slot}"
            defense=max(1, defense_base + idx//2)
            _catalog_mut.catalog_assign({
                "name":f"{slot_name} {label}", "type":"armor", "slot":slot,
                "defense":defense, "price":None, "rarity":"epic", "rarity_name":"Epicki",
                "affix":affix, "affix_amount":amount,
                "regional_set":set_id,
                "desc":(
                    f"Część regionalnego zestawu {REGIONAL_SET_BONUSES[set_id]['name']}. "
                    f"Obrona +{defense}. Bonus statystyki +{amount}. "
                    "Progi: 2 części HP/Mana, 4 części obrażenia, 6 części obrona."
                ),
            }, 'ITEMS', ITEMS, (item_id,))
            ids.append(item_id)
        regional_items[set_id]=ids

    # --------------------------------------------------------
    # Named boss loot.
    # --------------------------------------------------------
    named = {
        "cemetery_keeper_lantern": {"name":"Latarnia Strażnika Cmentarza","type":"armor","slot":"charm","defense":7,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"willpower","affix_amount":5,"desc":"Unikalna latarnia Strażnika Cmentarza. Obrona +7, Siła Woli +5."},
        "void_archon_ring": {"name":"Pierścień Arcykultysty Otchłani","type":"armor","slot":"ring","defense":6,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"intelligence","affix_amount":6,"sockets":2,"desc":"Unikalny pierścień Arcykultysty. Obrona +6, Inteligencja +6, 2 gniazda."},
        "primal_alpha_necklace": {"name":"Naszyjnik Pradawnego Alfa","type":"armor","slot":"necklace","defense":7,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"strength","affix_amount":6,"sockets":2,"desc":"Kły Pradawnego Alfa oprawione w naszyjnik. Obrona +7, Siła +6, 2 gniazda."},
        "dead_king_seal": {"name":"Pieczęć Umarłego Króla","type":"armor","slot":"ring","defense":9,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"willpower","affix_amount":7,"sockets":3,"desc":"Pierścień Umarłego Króla Nekropolii. Obrona +9, Siła Woli +7, 3 gniazda."},
        "cistern_king_chain": {"name":"Łańcuch Króla Cysterny","type":"armor","slot":"necklace","defense":6,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"constitution","affix_amount":5,"sockets":2,"desc":"Ciężki łańcuch Króla Podmiejskich Kanałów. Obrona +6, Kondycja +5, 2 gniazda."},
        "eternal_ice_heart": {"name":"Serce Wiecznego Lodu","type":"armor","slot":"charm","defense":11,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"intelligence","affix_amount":8,"desc":"Zamarznięte serce Pradawnego Lodowego Smoka. Obrona +11, Inteligencja +8."},
    }
    _catalog_mut.catalog_update_path('ITEMS', ITEMS, (), named)
    for _named_item_id in named:
        _catalog_mut.catalog_assign(True, 'ITEMS', ITEMS, (_named_item_id, "named_loot"))
    boss_named = {
        "cemetery_keeper": ("cemetery_keeper_lantern",0.45),
        "cult_archon": ("void_archon_ring",0.45),
        "beast_ancient_alpha": ("primal_alpha_necklace",0.45),
        "necro_dead_king": ("dead_king_seal",0.45),
        "sewer_king": ("cistern_king_chain",0.45),
        "ice_dragon": ("eternal_ice_heart",0.45),
    }
    for boss_id,(item_id,chance) in boss_named.items():
        if boss_id in MOB_TEMPLATES:
            _catalog_mut.catalog_setdefault_path('MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,), "drops",{})[item_id]=chance

    # Main regional bosses also yield regional set pieces through corpse loot.
    for boss_id,set_id in (("cult_archon","cultist"),("necro_dead_king","necropolis"),("ice_dragon","ice_caves")):
        t=MOB_TEMPLATES.get(boss_id)
        if t:
            t["corpse_equipment_pool"]=list(regional_items[set_id])
            t["corpse_equipment_guaranteed"]=2

    # --------------------------------------------------------
    # Mini bosses: two in each of 8 exploration areas.
    # --------------------------------------------------------
    mini_specs = [
        ("cemetery_crypt_reaper","Żniwiarz Starej Krypty","cemetery_fallen_chapel",700,46,"magic",2200,1500,None),
        ("cemetery_mourning_knight","Rycerz Martwego Dzwonu","cemetery_bell_tower",900,55,"physical",2800,1900,None),
        ("cult_void_executioner","Egzekutor Pustki","cult_ruins_ritual_hall",1200,70,"physical",3800,2600,"cultist"),
        ("cult_black_oracle","Czarna Wyrocznia","cult_ruins_library",1050,76,"magic",4000,2800,"cultist"),
        ("beast_cave_matriarch","Matriarcha Jaskiniowych Bestii","beast_lair_bone_nest",1400,78,"physical",4300,3000,None),
        ("beast_ironhorn_champion","Żelaznorogi Czempion","beast_lair_hunting_ground",1650,84,"physical",4700,3300,None),
        ("necro_ossuary_champion","Czempion Ossuarium","necropolis_catacombs",2100,92,"physical",6000,4400,"necropolis"),
        ("necro_death_bishop","Biskup Śmierci","necropolis_royal_tombs",1950,98,"magic",6400,4700,"necropolis"),
        ("sewer_plague_broodmother","Matka Zarazy","sewer_rat_nest",850,48,"physical",2500,1700,None),
        ("sewer_smuggler_boss","Mistrz Przemytników","sewer_smuggler_den",1100,58,"physical",3100,2200,None),
        ("ice_crystal_behemoth","Kryształowy Behemot","ice_cave_crystal_chamber",2400,104,"physical",7200,5200,"ice_caves"),
        ("ice_frost_lich","Licz Wiecznego Szronu","ice_cave_ancient_hall",2200,110,"magic",7600,5600,"ice_caves"),
        ("bandit_quartermaster","Kwatermistrz Bandytów","bandit_loot_depot",520,34,"physical",1900,900,None),
        ("bandit_duelist","Bandycki Mistrz Pojedynku","bandit_arena",640,39,"physical",2300,1100,None),
        ("goblin_mushroom_beast","Goblińska Bestia Grzybowa","goblin_fungus_gallery",500,31,"physical",1700,800,None),
        ("goblin_bombmaster","Mistrz Goblińskich Bombiarzy","goblin_bomb_workshop",620,42,"magic",2400,1200,None),
    ]
    for mob_id,name,room,hp,damage,dtype,classxp,soul,set_id in mini_specs:
        t={
            "name":name,"max_hp":hp,"damage":damage,"damage_type":dtype,
            "silver":max(90,hp//5),"gold":max(1,hp//900),"mithril":0,
            "stat_reward":max(100,hp//8),"class_xp_reward":classxp,"soul_reward":soul,
            "drops":{"soul_shard":0.55,"soul_elixir":0.12},
            # v3.31.1: regional bandit minibosses belong to the authored bandit
            # kill family, just like the regular camp mobs. Other minibosses
            # retain their old identity and must not falsely credit bandits.
            "quest_target": "bandit" if mob_id in {"bandit_quartermaster", "bandit_duelist"} else None,
            "mini_boss":True,"respawn_seconds":180,
            "boss_mechanic_text":"Mini-boss. Jest wyraźnie mocniejszy od zwykłych przeciwników w tym expowisku.",
            "corpse_equipment_pool":[],"corpse_equipment_guaranteed":0,
        }
        if set_id:
            t["corpse_equipment_pool"]=list(regional_items[set_id])
            t["corpse_equipment_guaranteed"]=1
        _catalog_mut.catalog_assign(t, 'MOB_TEMPLATES', MOB_TEMPLATES, (mob_id,))
        MOB_SPAWNS.append((room,mob_id))

    # --------------------------------------------------------
    # Elite + Rare eligibility. Bosses/minibosses excluded.
    # --------------------------------------------------------
    eligible=[]
    # v102.00.9: elite eligibility tests a snapshot of spawn template IDs.
    # Reuse it across templates; the eligibility loop itself adds no spawns.
    spawned_template_ids_v102009 = {tid for _room, tid in MOB_SPAWNS}
    for mob_id,t in list(MOB_TEMPLATES.items()):
        if (
            t.get("training_dummy") or t.get("world_boss") or t.get("mini_boss")
            or t.get("crypt_boss") or t.get("astral_boss")
            or t.get("mythic_crypt_boss") or t.get("mythic_astral_boss")
            or t.get("giant_fortress_boss") or "__elite_" in mob_id or mob_id.endswith("__rare")
        ):
            continue
        # Actual spawned ordinary combat opponents only. Some spawned
        # world/content templates are non-combat objects and intentionally
        # have no classic damage field; elite/rare variants require both.
        if (
            "max_hp" in t
            and "damage" in t
            and mob_id in spawned_template_ids_v102009
        ):
            t["elite_eligible"]=True
            t["rare_eligible"]=True
            eligible.append(mob_id)
    _register_elite_variants(eligible)
    _register_rare_variants(eligible)

    # --------------------------------------------------------
    # Renewable treasure chests. One to two per area.
    # --------------------------------------------------------
    chest_rows = {
        "bandit_loot_depot": ("Skrzynia Łupów Bandytów",900,["healing_potion","soul_shard"],[]),
        "goblin_treasure_burrow": ("Goblińska Skrzynia Skarbów",900,["healing_potion","mana_potion","soul_shard"],[]),
        "ruin_armory": ("Skrzynia Starej Zbrojowni",1200,["healing_potion","mana_potion","soul_shard"],[]),
        "cemetery_bone_field": ("Zapieczętowana Skrzynia Cmentarna",1200,["soul_shard","soul_elixir"],[]),
        "cult_ruins_library": ("Skrzynia Zakazanej Wiedzy",1200,["soul_shard","soul_elixir"],regional_items["cultist"]),
        "cult_ruins_ritual_hall": ("Rytualna Skrzynia Kultystów",1500,["soul_elixir"],regional_items["cultist"]),
        "beast_lair_bone_nest": ("Skrzynia Łowców Bestii",1200,["wolf_fang","soul_shard"],[]),
        "necropolis_catacombs": ("Sarkofag Skarbów Nekropolii",1500,["soul_shard","soul_elixir"],regional_items["necropolis"]),
        "necropolis_royal_tombs": ("Królewska Skrzynia Nekropolii",1800,["soul_elixir"],regional_items["necropolis"]),
        "sewer_flooded_vault": ("Zalana Skrzynia Przemytników",900,["healing_potion","mana_potion","soul_shard"],[]),
        "ice_cave_crystal_chamber": ("Kryształowa Skrzynia Lodu",1500,["soul_shard","soul_elixir"],regional_items["ice_caves"]),
        "ice_cave_ancient_hall": ("Pradawna Skrzynia Lodowa",1800,["soul_elixir"],regional_items["ice_caves"]),
    }
    TREASURE_CHESTS.clear()
    for room,(name,respawn,base_pool,set_pool) in chest_rows.items():
        TREASURE_CHESTS[room]={
            "name":name,"respawn":respawn,"base_pool":tuple(base_pool),"set_pool":tuple(set_pool),
        }

# v0.31.2: sale treningowe nowych klas technologicznych, obecne przed auditami.
_catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (), "guild_mec_chamber", {
    "name": "Hangar Meca", "zone": "Gildia Dusz",
    "desc": "Wzmocniony hangar z rdzeniami energetycznymi i stanowiskami ciężkiego pancerza.",
    "exits": {"south": "guild_martial_hall"},
})
_catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (), "guild_engineer_chamber", {
    "name": "Warsztat Inżyniera", "zone": "Gildia Dusz",
    "desc": "Warsztat pełen narzędzi, działek testowych, skanerów i mechanicznych konstrukcji.",
    "exits": {"east": "guild_shadow_gallery"},
})
_catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (), "guild_martial_hall", {}).setdefault("exits", {})["east"] = "guild_mec_chamber"
_catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (), "guild_shadow_gallery", {}).setdefault("exits", {})["west"] = "guild_engineer_chamber"
if "teacher_mec" in NPCS:
    _catalog_mut.catalog_assign("guild_mec_chamber", 'NPCS', NPCS, ("teacher_mec", "room"))
if "teacher_engineer" in NPCS:
    _catalog_mut.catalog_assign("guild_engineer_chamber", 'NPCS', NPCS, ("teacher_engineer", "room"))

"""Soulbound v4.00.1: authored world expansion implementation.

Public entry points remain available from world.expansions.
"""

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


def build_high_end_mob_pack():
    """
    High-End Mob Pack.
    Nie dodaje levelu ani XP postaci.
    Ogromne nagrody dotyczą wyłącznie Soul XP i Class Mastery XP.
    Najtrudniejsze moby są w osobnych odnogach, aby nie blokować
    zwykłego przechodzenia regionów.
    """

    # ========================================================
    # 5 ODDZIELNYCH ODNÓG WYZWANIA
    # ========================================================
    _catalog_mut.catalog_assign("wild_ancient_path", 'ROOMS', ROOMS, ("beast_den", "exits", "down"))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Pradawny Szlak Bestii",
        "desc": (
            "To odgałęzienie Północnej Dziczy jest przeznaczone dla "
            "bardzo mocnych postaci. Zwykłe bestie tutaj nie przetrwały."
        ),
        "exits": {
            "up": "beast_den",
            "north": "wild_primal_hollow",
        },
    }, 'ROOMS', ROOMS, ("wild_ancient_path",))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Pradawna Kotlina Dziczy",
        "desc": (
            "W kotlinie żyje coś znacznie potężniejszego od Rogatego Króla. "
            "To teren wyzwania, nie zwykła ścieżka fabularna."
        ),
        "exits": {"south": "wild_ancient_path"},
    }, 'ROOMS', ROOMS, ("wild_primal_hollow",))

    _catalog_mut.catalog_assign("mountain_tempest_path", 'ROOMS', ROOMS, ("storm_summit", "exits", "up"))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Ścieżka Wiecznej Burzy",
        "desc": (
            "Błyskawice uderzają bez przerwy. Przeciwnicy tutaj mają "
            "ogromne HP i mocne kontrataki."
        ),
        "exits": {
            "down": "storm_summit",
            "north": "mountain_tempest_sanctum",
        },
    }, 'ROOMS', ROOMS, ("mountain_tempest_path",))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Sanktuarium Wiecznej Burzy",
        "desc": (
            "Kamienny krąg na samym szczycie. To miejsce jednego z "
            "najpotężniejszych przeciwników otwartego świata."
        ),
        "exits": {"south": "mountain_tempest_path"},
    }, 'ROOMS', ROOMS, ("mountain_tempest_sanctum",))

    _catalog_mut.catalog_assign("troll_abyss", 'ROOMS', ROOMS, ("troll_altar", "exits", "down"))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Otchłań Trolli",
        "desc": (
            "Niżej żyją stare, wojenne kasty trolli. Ich wytrzymałość "
            "jest wielokrotnie większa od zwykłych trolli."
        ),
        "exits": {
            "up": "troll_altar",
            "south": "troll_abyss_throne",
        },
    }, 'ROOMS', ROOMS, ("troll_abyss",))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Tron Pierwszego Wodza",
        "desc": (
            "Pradawny kamienny tron stoi w ogromnej pieczarze. "
            "To końcowe wyzwanie głębin Jaskini Trolli."
        ),
        "exits": {"north": "troll_abyss"},
    }, 'ROOMS', ROOMS, ("troll_abyss_throne",))

    _catalog_mut.catalog_assign("swamp_rotten_depths", 'ROOMS', ROOMS, ("bog_heart", "exits", "down"))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Gnijące Głębie Bagna",
        "desc": (
            "Pod powierzchnią mokradeł pulsują stare korzenie. "
            "Moby tej odnogi są przeznaczone dla endgame."
        ),
        "exits": {
            "up": "bog_heart",
            "south": "swamp_primordial_pool",
        },
    }, 'ROOMS', ROOMS, ("swamp_rotten_depths",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Pradawne Rozlewisko",
        "desc": (
            "Czarna woda nie porusza się nawet przy silnym wietrze. "
            "To legowisko pierwotnej hydry."
        ),
        "exits": {"north": "swamp_rotten_depths"},
    }, 'ROOMS', ROOMS, ("swamp_primordial_pool",))

    _catalog_mut.catalog_assign("desert_sun_tomb", 'ROOMS', ROOMS, ("sun_temple", "exits", "down"))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Grobowiec Słońca",
        "desc": (
            "Ukryta część świątyni zaczyna prawdziwy endgame Pustyni. "
            "Tutejsi strażnicy mają setki tysięcy punktów życia."
        ),
        "exits": {
            "up": "sun_temple",
            "north": "desert_solar_sanctum",
        },
    }, 'ROOMS', ROOMS, ("desert_sun_tomb",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Sanktuarium Wiecznego Słońca",
        "desc": (
            "Oślepiające sanktuarium skrywa najpotężniejsze otwarte "
            "wyzwanie tego pakietu."
        ),
        "exits": {"south": "desert_sun_tomb"},
    }, 'ROOMS', ROOMS, ("desert_solar_sanctum",))

    # ========================================================
    # ENDGAME ELITY + BOSSOWIE
    # max_hp jest wartością bazową; globalne x2 jest nakładane później.
    # ========================================================
    mobs = {
        # Dzicz — wejście do wysokiego endgame.
        "end_wild_ancient_mauler": {
            "name": "Pradawny Rozpruwacz Dziczy",
            "max_hp": 60000,
            "damage": 210,
            "damage_type": "physical",
            "silver": 10000, "gold": 20, "mithril": 0,
            "stat_reward": 4500,
            "class_xp_reward": 150000,
            "soul_reward": 100000,
            "drops": {"soul_shard": 0.65, "soul_elixir": 0.12},
            "quest_target": None,
        },
        "end_wild_spirit_behemoth": {
            "name": "Duchowy Behemot Dziczy",
            "max_hp": 100000,
            "damage": 270,
            "damage_type": "magic",
            "silver": 14000, "gold": 30, "mithril": 0,
            "stat_reward": 6000,
            "class_xp_reward": 300000,
            "soul_reward": 250000,
            "drops": {"soul_shard": 0.80, "cut_gem_diamond": 0.05},
            "quest_target": None,
        },
        "end_wild_primal_avatar": {
            "name": "Pierwotny Avatar Dziczy",
            "max_hp": 250000,
            "damage": 430,
            "damage_type": "physical",
            "silver": 35000, "gold": 75, "mithril": 1,
            "stat_reward": 12000,
            "class_xp_reward": 1500000,
            "soul_reward": 1000000,
            "drops": {"soul_elixir": 0.60, "cut_gem_soul_topaz": 0.12},
            "quest_target": None,
            "world_boss": True,
        },

        # Góry.
        "end_mountain_ice_colossus": {
            "name": "Lodowy Kolos Szczytu",
            "max_hp": 125000,
            "damage": 360,
            "damage_type": "physical",
            "silver": 18000, "gold": 40, "mithril": 0,
            "stat_reward": 7500,
            "class_xp_reward": 450000,
            "soul_reward": 350000,
            "drops": {"cobalt_ore": 0.25, "cut_gem_sapphire": 0.06},
            "quest_target": None,
        },
        "end_mountain_storm_elemental": {
            "name": "Żywiołak Wiecznej Burzy",
            "max_hp": 190000,
            "damage": 480,
            "damage_type": "magic",
            "silver": 24000, "gold": 55, "mithril": 0,
            "stat_reward": 9000,
            "class_xp_reward": 750000,
            "soul_reward": 600000,
            "drops": {"astral_ore": 0.14, "cut_gem_astral_crystal": 0.05},
            "quest_target": None,
        },
        "end_mountain_tempest_titan": {
            "name": "Tytan Wiecznej Burzy",
            "max_hp": 600000,
            "damage": 760,
            "damage_type": "magic",
            "silver": 65000, "gold": 150, "mithril": 1,
            "stat_reward": 18000,
            "class_xp_reward": 3000000,
            "soul_reward": 2000000,
            "drops": {"soul_elixir": 0.75, "cut_gem_astral_crystal": 0.14},
            "quest_target": None,
            "world_boss": True,
        },

        # Jaskinia Trolli.
        "end_troll_juggernaut": {
            "name": "Troll Juggernaut Głębin",
            "max_hp": 160000,
            "damage": 430,
            "damage_type": "physical",
            "silver": 22000, "gold": 50, "mithril": 0,
            "stat_reward": 8500,
            "class_xp_reward": 600000,
            "soul_reward": 450000,
            "drops": {"soul_shard": 0.85, "dragonsteel_ore": 0.12},
            "quest_target": None,
        },
        "end_troll_ancestral_shaman": {
            "name": "Pradawny Szaman Trolli",
            "max_hp": 230000,
            "damage": 540,
            "damage_type": "magic",
            "silver": 28000, "gold": 65, "mithril": 0,
            "stat_reward": 10500,
            "class_xp_reward": 1000000,
            "soul_reward": 800000,
            "drops": {"soul_elixir": 0.30, "cut_gem_dragon_garnet": 0.08},
            "quest_target": None,
        },
        "end_troll_first_warlord": {
            "name": "Pierwszy Wódz Trolli Grommar",
            "max_hp": 750000,
            "damage": 860,
            "damage_type": "physical",
            "silver": 85000, "gold": 190, "mithril": 2,
            "stat_reward": 22000,
            "class_xp_reward": 4000000,
            "soul_reward": 3000000,
            "drops": {"soul_elixir": 0.80, "cut_gem_dragon_garnet": 0.16},
            "quest_target": None,
            "world_boss": True,
        },

        # Bagna.
        "end_swamp_plague_colossus": {
            "name": "Kolos Zarazy",
            "max_hp": 210000,
            "damage": 500,
            "damage_type": "physical",
            "silver": 26000, "gold": 60, "mithril": 0,
            "stat_reward": 10000,
            "class_xp_reward": 800000,
            "soul_reward": 650000,
            "drops": {"void_lotus": 0.18, "cut_gem_amethyst": 0.07},
            "quest_target": None,
        },
        "end_swamp_rotten_oracle": {
            "name": "Wyrocznia Gnijących Głębin",
            "max_hp": 300000,
            "damage": 620,
            "damage_type": "magic",
            "silver": 34000, "gold": 80, "mithril": 0,
            "stat_reward": 12500,
            "class_xp_reward": 1200000,
            "soul_reward": 950000,
            "drops": {"void_lotus": 0.25, "cut_gem_void_onyx": 0.08},
            "quest_target": None,
        },
        "end_swamp_primordial_hydra": {
            "name": "Pierwotna Hydra Bagna",
            "max_hp": 1000000,
            "damage": 980,
            "damage_type": "physical",
            "silver": 110000, "gold": 250, "mithril": 2,
            "stat_reward": 27000,
            "class_xp_reward": 7000000,
            "soul_reward": 5000000,
            "drops": {"soul_elixir": 0.90, "cut_gem_void_onyx": 0.20},
            "quest_target": None,
            "world_boss": True,
        },

        # Pustynia — najwyższy poziom pakietu.
        "end_desert_glass_colossus": {
            "name": "Szklany Kolos Pustyni",
            "max_hp": 350000,
            "damage": 650,
            "damage_type": "physical",
            "silver": 40000, "gold": 95, "mithril": 0,
            "stat_reward": 13500,
            "class_xp_reward": 1400000,
            "soul_reward": 1000000,
            "drops": {"void_ore": 0.20, "cut_gem_void_onyx": 0.07},
            "quest_target": None,
        },
        "end_desert_solar_revenant": {
            "name": "Słoneczny Revenant",
            "max_hp": 475000,
            "damage": 780,
            "damage_type": "magic",
            "silver": 52000, "gold": 120, "mithril": 1,
            "stat_reward": 16000,
            "class_xp_reward": 2200000,
            "soul_reward": 1800000,
            "drops": {"eternium_ore": 0.06, "cut_gem_eternium_prism": 0.06},
            "quest_target": None,
        },
        "end_desert_eternal_sun": {
            "name": "Awatar Wiecznego Słońca",
            "max_hp": 1500000,
            "damage": 1200,
            "damage_type": "magic",
            "silver": 160000, "gold": 400, "mithril": 3,
            "stat_reward": 35000,
            "class_xp_reward": 10000000,
            "soul_reward": 8000000,
            "drops": {"soul_elixir": 1.0, "cut_gem_eternium_prism": 0.25},
            "quest_target": None,
            "world_boss": True,
        },
    }

    corpse_pool = [
        "iron_helmet", "iron_guard", "iron_gauntlets",
        "iron_leggings", "iron_boots", "forge_charm",
    ]
    for mob_id, template in mobs.items():
        template.setdefault("corpse_equipment_pool", corpse_pool)
        template.setdefault(
            "corpse_equipment_guaranteed",
            3 if template.get("world_boss") else 2,
        )
        template["high_end_mob"] = True
        _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (mob_id,))

    MOB_SPAWNS.extend([
        ("wild_ancient_path", "end_wild_ancient_mauler"),
        ("wild_ancient_path", "end_wild_spirit_behemoth"),
        ("wild_primal_hollow", "end_wild_primal_avatar"),

        ("mountain_tempest_path", "end_mountain_ice_colossus"),
        ("mountain_tempest_path", "end_mountain_storm_elemental"),
        ("mountain_tempest_sanctum", "end_mountain_tempest_titan"),

        ("troll_abyss", "end_troll_juggernaut"),
        ("troll_abyss", "end_troll_ancestral_shaman"),
        ("troll_abyss_throne", "end_troll_first_warlord"),

        ("swamp_rotten_depths", "end_swamp_plague_colossus"),
        ("swamp_rotten_depths", "end_swamp_rotten_oracle"),
        ("swamp_primordial_pool", "end_swamp_primordial_hydra"),

        ("desert_sun_tomb", "end_desert_glass_colossus"),
        ("desert_sun_tomb", "end_desert_solar_revenant"),
        ("desert_solar_sanctum", "end_desert_eternal_sun"),
    ])

    
    HELP_TOPICS["high_end_moby"] = [
        "High-End Mob Pack dodaje 15 bardzo trudnych elit i bossów.",
        "Nie istnieje XP postaci. Ogromne nagrody to Soul XP i Class Mastery XP.",
        "Elity dają od 100 tysięcy do 1,8 miliona Soul XP.",
        "Bossowie dają od 1 miliona do 8 milionów Soul XP.",
        "Class Mastery XP sięga od 150 tysięcy do 10 milionów.",
        "Przeciwnicy mają bardzo wysokie HP i obrażenia, więc nagrody nie są darmową farmą.",
        "Najtrudniejsze moby są w osobnych odnogach Dziczy, Gór, Jaskini Trolli, Bagien i Pustyni.",
        "Zwykłe ścieżki regionów pozostają przechodnie bez walki z tymi mobami.",
        "Użyj consider <mob>, żeby ocenić zagrożenie przed atakiem.",
        "Wysokie wyzwania mają sens po rozwinięciu statystyk, Soul, Class Mastery, EQ i socketów.",
        "Awatar Wiecznego Słońca jest najmocniejszym bossem tego pakietu: po globalnym skalowaniu ma 3 miliony HP.",
    ]


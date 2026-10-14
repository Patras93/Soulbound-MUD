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

def build_forest_wolves_and_quest_balance():
    """Rozbudowuje Las Szeptów i poprawia trzy istniejące questy."""
    global EXP_AREAS

    # --------------------------------------------------------
    # Las Szeptów: osobne, większe expowisko po Głębi Gaju.
    # --------------------------------------------------------
    _catalog_mut.catalog_assign("forest_edge", 'ROOMS', ROOMS, ("deep_grove", "exits", "west"))
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, (), {
        "forest_edge": {
            "zone": "Las Szeptów", "name": "Skraj Lasu Szeptów",
            "desc": (
                "Drzewa rosną tu znacznie gęściej niż w Gaju Szeptów. "
                "Między korzeniami widać liczne ślady wilczych łap."
            ),
            "exits": {"east": "deep_grove", "west": "forest_birch_path", "north": "forest_wolf_trail"},
        },
        "forest_birch_path": {
            "zone": "Las Szeptów", "name": "Brzozowy Trakt",
            "desc": "Wąski trakt przecina jasny zagajnik. Wycie odbija się między białymi pniami.",
            "exits": {"east": "forest_edge", "west": "forest_stream", "north": "forest_old_oaks"},
        },
        "forest_wolf_trail": {
            "zone": "Las Szeptów", "name": "Wilczy Trakt",
            "desc": "Ziemię pokrywają świeże tropy całej watahy. Szlak prowadzi ku ciemniejszej części lasu.",
            "exits": {"south": "forest_edge", "north": "forest_moon_glade", "west": "forest_old_oaks"},
        },
        "forest_old_oaks": {
            "zone": "Las Szeptów", "name": "Krąg Starych Dębów",
            "desc": "Pradawne dęby tworzą naturalny krąg. Między korzeniami leżą kości zwierzyny.",
            "exits": {"south": "forest_birch_path", "east": "forest_wolf_trail", "north": "forest_fallen_tree"},
        },
        "forest_stream": {
            "zone": "Las Szeptów", "name": "Cichy Strumień",
            "desc": "Zimna woda płynie pod korzeniami. Na błotnistym brzegu odciśnięte są wilcze łapy.",
            "exits": {"east": "forest_birch_path", "north": "forest_moss_hollow"},
        },
        "forest_moss_hollow": {
            "zone": "Las Szeptów", "name": "Omszała Kotlina",
            "desc": "Miękki mech tłumi kroki. Niskie warczenie dochodzi z kilku kierunków jednocześnie.",
            "exits": {"south": "forest_stream", "east": "forest_fallen_tree", "north": "forest_wolf_den"},
        },
        "forest_fallen_tree": {
            "zone": "Las Szeptów", "name": "Powalony Olbrzym",
            "desc": "Ogromny przewrócony pień dzieli las na dwie ścieżki. Pod korzeniami kryją się drapieżniki.",
            "exits": {"south": "forest_old_oaks", "west": "forest_moss_hollow", "east": "forest_moon_glade"},
        },
        "forest_moon_glade": {
            "zone": "Las Szeptów", "name": "Księżycowa Polana",
            "desc": "Nawet w dzień polanę spowija srebrzysta poświata. Watahy zbierają się tutaj przed polowaniem.",
            "exits": {"south": "forest_wolf_trail", "west": "forest_fallen_tree", "north": "forest_alpha_hollow"},
        },
        "forest_wolf_den": {
            "zone": "Las Szeptów", "name": "Wilcza Nora",
            "desc": "Między głazami znajduje się rozległa nora pełna sierści, kości i świeżych tropów.",
            "exits": {"south": "forest_moss_hollow", "east": "forest_alpha_hollow"},
        },
        "forest_alpha_hollow": {
            "zone": "Las Szeptów", "name": "Kotlina Wilczej Watahy",
            "desc": "Najgłębsza część lasu. Dziesiątki śladów zbiegają się przy kamiennym wyniesieniu przywódcy watahy.",
            "exits": {"south": "forest_moon_glade", "west": "forest_wolf_den"},
        },
    })

    # --------------------------------------------------------
    # Nowe odmiany wilków. Wszystkie zaliczają quest Cienie w gaju.
    # --------------------------------------------------------
    _catalog_mut.catalog_assign({
        "name": "Tropiciel Cienia", "max_hp": 95, "damage": 11, "damage_type": "physical",
        "silver": 34, "gold": 0, "mithril": 0,
        "stat_reward": 36, "soul_reward": 175,
        "drops": {"wolf_fang": 0.55, "healing_potion": 0.05},
        "quest_target": "shadow_wolf",
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("shadow_wolf_stalker",))
    _catalog_mut.catalog_assign({
        "name": "Wyjący Wilk Cienia", "max_hp": 125, "damage": 14, "damage_type": "physical",
        "silver": 46, "gold": 0, "mithril": 0,
        "stat_reward": 44, "soul_reward": 220,
        "drops": {"wolf_fang": 0.65, "mana_potion": 0.04},
        "quest_target": "shadow_wolf",
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("shadow_wolf_howler",))
    _catalog_mut.catalog_assign({
        "name": "Przywódca Watahy Cienia", "max_hp": 320, "damage": 22, "damage_type": "physical",
        "silver": 150, "gold": 1, "mithril": 0,
        "stat_reward": 120, "class_xp_reward": 1000, "soul_reward": 700,
        "drops": {"wolf_fang": 1.0, "soul_shard": 0.35, "soul_elixir": 0.08},
        "quest_target": "shadow_wolf",
        "mini_boss": True, "respawn_seconds": 180,
        "boss_mechanic_text": (
            "Mini-boss wilczej watahy. Jest znacznie mocniejszy od zwykłych Wilków Cienia."
        ),
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("shadow_wolf_pack_leader",))
    MOB_DESCRIPTIONS.update({
        "shadow_wolf_stalker": "Szybszy Wilk Cienia, który poluje na skraju watahy.",
        "shadow_wolf_howler": "Silniejszy Wilk Cienia. Jego wycie przyciąga uwagę całej watahy.",
        "shadow_wolf_pack_leader": "Największy wilk Lasu Szeptów i przywódca miejscowej watahy.",
    })

    # W lesie ma być wyraźnie więcej wilków niż w starym Gaju Szeptów.
    forest_spawns = (
        ("forest_edge", "shadow_wolf"), ("forest_edge", "shadow_wolf"),
        ("forest_birch_path", "shadow_wolf"), ("forest_birch_path", "shadow_wolf_stalker"),
        ("forest_wolf_trail", "shadow_wolf"), ("forest_wolf_trail", "shadow_wolf"),
        ("forest_wolf_trail", "shadow_wolf_stalker"),
        ("forest_old_oaks", "shadow_wolf_stalker"), ("forest_old_oaks", "shadow_wolf_howler"),
        ("forest_stream", "shadow_wolf"), ("forest_stream", "shadow_wolf"),
        ("forest_moss_hollow", "shadow_wolf"), ("forest_moss_hollow", "shadow_wolf_stalker"),
        ("forest_fallen_tree", "shadow_wolf_stalker"), ("forest_fallen_tree", "shadow_wolf_howler"),
        ("forest_moon_glade", "shadow_wolf"), ("forest_moon_glade", "shadow_wolf_stalker"),
        ("forest_moon_glade", "shadow_wolf_howler"),
        ("forest_wolf_den", "shadow_wolf"), ("forest_wolf_den", "shadow_wolf"),
        ("forest_wolf_den", "shadow_wolf_stalker"), ("forest_wolf_den", "shadow_wolf_howler"),
        ("forest_alpha_hollow", "shadow_wolf"), ("forest_alpha_hollow", "shadow_wolf_stalker"),
        ("forest_alpha_hollow", "shadow_wolf_pack_leader"),
    )
    MOB_SPAWNS.extend(forest_spawns)

    GUIDE_DESTINATION_ALIASES.update({
        "las": "forest_edge",
        "las szeptow": "forest_edge",
        "las szeptów": "forest_edge",
        "forest": "forest_edge",
        "whisper forest": "forest_edge",
        "wilczy trakt": "forest_edge",
        "wilcza nora": "forest_edge",
        "wataha wilkow": "forest_edge",
        "wataha wilków": "forest_edge",
    })

    EXP_AREAS = EXP_AREAS + ({
        "id": "whisper_forest",
        "name": "Las Szeptów",
        "aliases": (
            "las", "las szeptow", "las szeptów", "wilki", "wilcza nora",
            "forest", "whisper forest",
        ),
        "soul_min": 10,
        "soul_max": 45,
        "difficulty": "łatwa do średniej",
        "guide": "las szeptow",
        "enemies": (
            "Wilki Cienia, Tropiciele Cienia, Wyjące Wilki Cienia, "
            "elitarne i rare warianty oraz Przywódca Watahy Cienia"
        ),
        "description": (
            "Duży leśny obszar za Głębią Gaju. Dziesięć nowych miejsc tworzy "
            "sieć ścieżek, polan i wilczych nor z gęstymi watahami."
        ),
        "note": (
            "Prowadzenie zatrzymuje na Skraju Lasu Szeptów. Wnętrze trzeba odkryć samodzielnie."
        ),
    },)

    # --------------------------------------------------------
    # Quest goblinów: 20 zabitych i powtarzalny co godzinę.
    # --------------------------------------------------------
    if "goblin_problem" in QUESTS:
        _catalog_mut.catalog_assign(20, 'QUESTS', QUESTS, ("goblin_problem", "needed"))
        _catalog_mut.catalog_assign(True, 'QUESTS', QUESTS, ("goblin_problem", "repeatable"))
        _catalog_mut.catalog_assign(QUEST_REPEAT_COOLDOWN_SECONDS, 'QUESTS', QUESTS, ("goblin_problem", "repeat_cooldown"))
        _catalog_mut.catalog_assign("Pokonaj 20 goblinów w ruinach, obozie i Jaskiniach Goblinów. "
            "Po ukończeniu zadanie można ponownie przyjąć po 60 minutach.", 'QUESTS', QUESTS, ("goblin_problem", "description"))
        if "captain_arven" in NPCS:
            _catalog_mut.catalog_assign("Gobliny zajęły starą strażnicę i wciąż wracają. "
                "Zabij 20 goblinów. To zlecenie mogę wystawić ponownie co godzinę.", 'NPCS', NPCS, ("captain_arven", "dialogue"))

    # --------------------------------------------------------
    # Cienie w Gaju: powtarzalne co godzinę.
    # --------------------------------------------------------
    if "shadow_wolves" in QUESTS:
        _catalog_mut.catalog_assign(True, 'QUESTS', QUESTS, ("shadow_wolves", "repeatable"))
        _catalog_mut.catalog_assign(QUEST_REPEAT_COOLDOWN_SECONDS, 'QUESTS', QUESTS, ("shadow_wolves", "repeat_cooldown"))
        _catalog_mut.catalog_assign("Pokonaj 2 Wilki Cienia w Gaju Szeptów lub Lesie Szeptów. "
            "Po ukończeniu zadanie można ponownie przyjąć po 60 minutach.", 'QUESTS', QUESTS, ("shadow_wolves", "description"))
        if "mira" in NPCS:
            _catalog_mut.catalog_assign("Wilki Cienia zakłócają równowagę gaju. Ich obecność jest coraz silniejsza. "
                "Zlecenie Cienie w Gaju mogę ponownie wystawić co godzinę.", 'NPCS', NPCS, ("mira", "dialogue"))

    # --------------------------------------------------------
    # Główny quest trolli: powtarzalny co godzinę.
    # --------------------------------------------------------
    if "mountain_troll_hunt" in QUESTS:
        _catalog_mut.catalog_assign(True, 'QUESTS', QUESTS, ("mountain_troll_hunt", "repeatable"))
        _catalog_mut.catalog_assign(QUEST_REPEAT_COOLDOWN_SECONDS, 'QUESTS', QUESTS, ("mountain_troll_hunt", "repeat_cooldown"))
        _catalog_mut.catalog_assign("Pokonaj 12 trolli w Jaskini Trolli i wróć do Strażnika Górskiego Eryka "
            "w Wiosce Górskiej. Po ukończeniu zadanie można ponownie przyjąć po 60 minutach.", 'QUESTS', QUESTS, ("mountain_troll_hunt", "description"))
        if "mountain_guard_eryk" in NPCS:
            _catalog_mut.catalog_assign("Trolle z południowej jaskini coraz częściej schodzą pod samą wioskę. "
                "Potrzebujemy kogoś, kto przerzedzi ich szeregi. "
                "Zlecenie Plaga Trolli mogę wystawić ponownie co godzinę.", 'NPCS', NPCS, ("mountain_guard_eryk", "dialogue"))

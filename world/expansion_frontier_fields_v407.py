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

def build_world_expansion_ii():
    """Six explorable areas plus location-bound profession field quests."""
    global EXP_AREAS

    # ========================================================
    # UNIQUE FIELD RESOURCES — ONLY FROM SPECIFIC NEW ROOMS
    # ========================================================
    field_items = {
        "field_grave_moss": {
            "name": "Mech Nagrobny", "type": "resource", "price": None,
            "resource_category": "herb", "sell_silver": 22,
            "desc": "Zioło rosnące wyłącznie na starych nagrobkach Cmentarza.",
        },
        "field_void_thorn": {
            "name": "Cierń Pustki", "type": "resource", "price": None,
            "resource_category": "herb", "sell_silver": 38,
            "desc": "Skażona roślina występująca tylko w Ruinach Kultystów.",
        },
        "field_ironbark_root": {
            "name": "Korzeń Żelaznokory", "type": "resource", "price": None,
            "resource_category": "wood", "sell_silver": 34,
            "desc": "Twardy korzeń pozyskiwany tylko w Legowisku Bestii.",
        },
        "field_tomb_silver": {
            "name": "Srebro Grobowe", "type": "resource", "price": None,
            "resource_category": "ore", "sell_silver": 45,
            "desc": "Ciemne srebro z głębszych warstw Kopalni Głębinowej, dostępne od poziomu 80.",
        },
        "field_blind_sewer_eel": {
            "name": "Ślepy Węgorz Kanałowy", "type": "resource", "price": None,
            "resource_category": "fish", "sell_silver": 28,
            "desc": "Rzadka ryba żyjąca tylko w podziemnym kanale pod Miastem Dusz.",
        },
        "field_frost_crystal_ore": {
            "name": "Ruda Lodowego Kryształu", "type": "resource", "price": None,
            "resource_category": "ore", "sell_silver": 60,
            "desc": "Lodowy minerał z Kopalni Głębinowej, dostępny od poziomu 100.",
        },
    }
    _catalog_mut.catalog_update_path('ITEMS', ITEMS, (), field_items)
    HERB_STORAGE_IDS.update({"field_grave_moss", "field_void_thorn"})
    WOOD_STORAGE_IDS.add("field_ironbark_root")
    ORE_STORAGE_IDS.update({"field_tomb_silver", "field_frost_crystal_ore"})
    MINING_STORAGE_IDS.update({"field_tomb_silver", "field_frost_crystal_ore"})
    FISH_STORAGE_IDS.add("field_blind_sewer_eel")
    # v0.8.72: terenowe zasoby są pełnoprawną częścią atlasów/codexu,
    # nie tylko specjalistycznych sakw.
    HERB_RESOURCE_IDS.update({"field_grave_moss", "field_void_thorn"})
    WOOD_RESOURCE_IDS.add("field_ironbark_root")
    ORE_RESOURCE_IDS.update({"field_tomb_silver", "field_frost_crystal_ore"})
    FISH_RESOURCE_IDS.add("field_blind_sewer_eel")
    HERB_ATLAS_ALL.update({"field_grave_moss", "field_void_thorn"})
    WOOD_ATLAS_ALL.add("field_ironbark_root")
    ORE_ATLAS_ALL.update({"field_tomb_silver", "field_frost_crystal_ore"})
    FISH_ATLAS_ALL.add("field_blind_sewer_eel")
    # Minimalne wymagania narzędzia zgodne ze specjalistycznymi questami.
    ORE_ATLAS_LEVELS.update({"field_tomb_silver": 80, "field_frost_crystal_ore": 100})
    ORE_MINE_FLOOR_MINIMUMS.update({"field_tomb_silver": 80, "field_frost_crystal_ore": 100})

    # ========================================================
    # 1. STARY CMENTARZ — expansion of the existing Graveyard
    # ========================================================
    _catalog_mut.catalog_assign("Stary Cmentarz", 'ROOMS', ROOMS, ("graveyard", "zone"))
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, ("graveyard", "exits"), {"north": "cemetery_ossuary_path", "east": "necropolis_gate"})
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, (), {
        "cemetery_ossuary_path": {"zone":"Stary Cmentarz","name":"Aleja Ossuariów","desc":"Popękane kapliczki i kamienne ossuaria stoją po obu stronach wąskiej alei.","exits":{"south":"graveyard","north":"cemetery_fallen_chapel","west":"cemetery_moon_garden"}},
        "cemetery_moon_garden": {"zone":"Stary Cmentarz","name":"Ogród Księżycowego Mchu","desc":"Wilgotne nagrobki porasta Mech Nagrobny. To terenowe miejsce Zielarstwa.","exits":{"east":"cemetery_ossuary_path","north":"cemetery_bone_field"}},
        "cemetery_fallen_chapel": {"zone":"Stary Cmentarz","name":"Zawalona Kaplica","desc":"Dach kaplicy runął, odsłaniając stare krypty i zbezczeszczony ołtarz.","exits":{"south":"cemetery_ossuary_path","north":"cemetery_bell_tower"}},
        "cemetery_bone_field": {"zone":"Stary Cmentarz","name":"Pole Kości","desc":"Płytkie groby zostały rozkopane, a kości tworzą białe pasma wśród ziemi.","exits":{"south":"cemetery_moon_garden","east":"cemetery_bell_tower"}},
        "cemetery_bell_tower": {"zone":"Stary Cmentarz","name":"Wieża Martwego Dzwonu","desc":"Pęknięty dzwon porusza się bez wiatru. Dalej znajduje się grobowiec grabarza.","exits":{"south":"cemetery_fallen_chapel","west":"cemetery_bone_field","north":"cemetery_keeper_tomb"}},
        "cemetery_keeper_tomb": {"zone":"Stary Cmentarz","name":"Grobowiec Strażnika Cmentarza","desc":"Kamienny sarkofag stoi pośrodku komory. Spoczynek Strażnika dawno został przerwany.","exits":{"south":"cemetery_bell_tower"}},
    })
    HERBALISM_ROOMS.add("cemetery_moon_garden")

    # ========================================================
    # 2. RUINY KULTYSTÓW
    # ========================================================
    _catalog_mut.catalog_assign("cult_ruins_gate", 'ROOMS', ROOMS, ("ruined_watchtower", "exits", "north"))
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, (), {
        "cult_ruins_gate": {"zone":"Ruiny Kultystów","name":"Brama Ruin Kultystów","desc":"Czarne symbole pokrywają resztki kamiennej bramy. Dalej prowadzi zarośnięty dziedziniec.","exits":{"south":"ruined_watchtower","north":"cult_ruins_courtyard"}},
        "cult_ruins_courtyard": {"zone":"Ruiny Kultystów","name":"Zbezczeszczony Dziedziniec","desc":"Rozbite posągi otaczają krąg wypalonej ziemi.","exits":{"south":"cult_ruins_gate","north":"cult_ruins_cloister","east":"cult_ruins_overgrown_garden"}},
        "cult_ruins_overgrown_garden": {"zone":"Ruiny Kultystów","name":"Ogród Cierni Pustki","desc":"Czarne pnącza rodzą Cierń Pustki. To terenowe miejsce Zielarstwa.","exits":{"west":"cult_ruins_courtyard","north":"cult_ruins_library"}},
        "cult_ruins_cloister": {"zone":"Ruiny Kultystów","name":"Krużganek Szeptów","desc":"Każdy krok odbija się szeptem, którego nie wypowiada żaden żywy człowiek.","exits":{"south":"cult_ruins_courtyard","north":"cult_ruins_ritual_hall"}},
        "cult_ruins_library": {"zone":"Ruiny Kultystów","name":"Spalona Biblioteka Kultu","desc":"Zwęglone księgi i metalowe tablice leżą między zawalonymi regałami.","exits":{"south":"cult_ruins_overgrown_garden","west":"cult_ruins_ritual_hall"}},
        "cult_ruins_ritual_hall": {"zone":"Ruiny Kultystów","name":"Sala Rytuałów","desc":"Runy tworzą koncentryczne kręgi wokół kamiennego ołtarza.","exits":{"south":"cult_ruins_cloister","east":"cult_ruins_library","north":"cult_ruins_sanctum"}},
        "cult_ruins_sanctum": {"zone":"Ruiny Kultystów","name":"Sanktuarium Pustki","desc":"Najgłębsza część ruin. Tutaj Arcykultysta podtrzymuje pęknięcie Pustki.","exits":{"south":"cult_ruins_ritual_hall"}},
    })
    HERBALISM_ROOMS.add("cult_ruins_overgrown_garden")

    # ========================================================
    # 3. LEGOWISKO BESTII — deeper branch from Beast Den
    # ========================================================
    _catalog_mut.catalog_assign("beast_lair_mouth", 'ROOMS', ROOMS, ("beast_den", "exits", "west"))
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, (), {
        "beast_lair_mouth": {"zone":"Legowisko Bestii","name":"Szczelina Legowiska Bestii","desc":"Pazury wyżłobiły głębokie ślady w skale. Z wnętrza dochodzi ciężki oddech.","exits":{"east":"beast_den","west":"beast_lair_tracks"}},
        "beast_lair_tracks": {"zone":"Legowisko Bestii","name":"Korytarz Tropów","desc":"Błoto jest pełne nakładających się śladów łap i kopyt.","exits":{"east":"beast_lair_mouth","west":"beast_lair_root_cavern","north":"beast_lair_bone_nest"}},
        "beast_lair_root_cavern": {"zone":"Legowisko Bestii","name":"Grota Żelaznokory","desc":"Pradawne korzenie przebijają strop. Można tu pozyskać Korzeń Żelaznokory.","exits":{"east":"beast_lair_tracks","north":"beast_lair_hunting_ground"}},
        "beast_lair_bone_nest": {"zone":"Legowisko Bestii","name":"Kościane Gniazdo","desc":"Wielkie gniazdo zbudowano z gałęzi, futer i kości.","exits":{"south":"beast_lair_tracks","west":"beast_lair_hunting_ground"}},
        "beast_lair_hunting_ground": {"zone":"Legowisko Bestii","name":"Podziemne Łowisko","desc":"Szeroka jaskinia jest naturalną areną polowań drapieżników.","exits":{"south":"beast_lair_root_cavern","east":"beast_lair_bone_nest","north":"beast_lair_alpha_den"}},
        "beast_lair_alpha_den": {"zone":"Legowisko Bestii","name":"Nora Pradawnego Alfa","desc":"Najgłębsza nora jest pełna świeżych śladów i połamanych rogów. Tu mieszka Pradawny Alfa.","exits":{"south":"beast_lair_hunting_ground"}},
    })
    WOODCUTTING_ROOMS.add("beast_lair_root_cavern")

    # ========================================================
    # 4. NEKROPOLIA
    # ========================================================
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, (), {
        "necropolis_gate": {"zone":"Nekropolia","name":"Brama Nekropolii","desc":"Olbrzymie kamienne wrota prowadzą do miasta grobowców.","exits":{"west":"graveyard","east":"necropolis_procession"}},
        "necropolis_procession": {"zone":"Nekropolia","name":"Aleja Procesyjna","desc":"Posągi bez twarzy stoją wzdłuż drogi prowadzącej między mauzoleami.","exits":{"west":"necropolis_gate","east":"necropolis_quarry","north":"necropolis_catacombs"}},
        "necropolis_quarry": {"zone":"Nekropolia","name":"Grobowy Kamieniołom","desc":"Dawny kamieniołom Nekropolii. Wydobycie przeniesiono do Kopalni Głębinowej; miejsce pozostało częścią regionu i questów.","exits":{"west":"necropolis_procession","north":"necropolis_silent_square"}},
        "necropolis_catacombs": {"zone":"Nekropolia","name":"Katakumby Bezimiennych","desc":"Niskie tunele są wypełnione setkami zapieczętowanych nisz.","exits":{"south":"necropolis_procession","east":"necropolis_silent_square"}},
        "necropolis_silent_square": {"zone":"Nekropolia","name":"Plac Ciszy","desc":"Centralny plac Nekropolii otaczają cztery monumentalne grobowce.","exits":{"south":"necropolis_quarry","west":"necropolis_catacombs","north":"necropolis_royal_tombs"}},
        "necropolis_royal_tombs": {"zone":"Nekropolia","name":"Królewskie Grobowce","desc":"Złote inskrypcje mówią o dynastii, której imię zostało wymazane.","exits":{"south":"necropolis_silent_square","north":"necropolis_throne"}},
        "necropolis_throne": {"zone":"Nekropolia","name":"Tron Umarłego Króla","desc":"Kamienny tron stoi przed otwartym sarkofagiem. Umarły Król powrócił do swej sali.","exits":{"south":"necropolis_royal_tombs"}},
    })

    # ========================================================
    # 5. KANAŁY POD MIASTEM
    # ========================================================
    _catalog_mut.catalog_assign("sewer_entrance", 'ROOMS', ROOMS, ("south_street", "exits", "down"))
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, (), {
        "sewer_entrance": {"zone":"Kanały Pod Miastem","name":"Krata Kanałów","desc":"Kamienne schody schodzą pod ulicę do wilgotnych kanałów.","exits":{"up":"south_street","down":"sewer_runoff"}},
        "sewer_runoff": {"zone":"Kanały Pod Miastem","name":"Kanał Odpływowy","desc":"Brudna woda płynie płytkim korytem między kamiennymi ścianami.","exits":{"up":"sewer_entrance","east":"sewer_rat_nest","south":"sewer_black_channel"}},
        "sewer_rat_nest": {"zone":"Kanały Pod Miastem","name":"Gniazdo Szczurów","desc":"Resztki skrzyń i tkanin tworzą ogromne gniazdo pod fundamentami.","exits":{"west":"sewer_runoff","south":"sewer_smuggler_den"}},
        "sewer_black_channel": {"zone":"Kanały Pod Miastem","name":"Czarny Kanał","desc":"Głęboki kanał jest jedynym siedliskiem Ślepego Węgorza Kanałowego.","exits":{"north":"sewer_runoff","east":"sewer_smuggler_den"}},
        "sewer_smuggler_den": {"zone":"Kanały Pod Miastem","name":"Kryjówka Przemytników","desc":"Puste beczki i fałszywe skrzynie zdradzają dawną trasę przemytników.","exits":{"north":"sewer_rat_nest","west":"sewer_black_channel","south":"sewer_flooded_vault"}},
        "sewer_flooded_vault": {"zone":"Kanały Pod Miastem","name":"Zalana Komora","desc":"Woda sięga kolan, a na dnie widać stare monety i kości.","exits":{"north":"sewer_smuggler_den","east":"sewer_cistern"}},
        "sewer_cistern": {"zone":"Kanały Pod Miastem","name":"Stara Cysterna","desc":"Wielka podziemna cysterna jest legowiskiem czegoś znacznie większego niż szczur.","exits":{"west":"sewer_flooded_vault"}},
    })
    RIVER_FISHING_ROOMS.add("sewer_black_channel")
    FISHING_ROOMS.add("sewer_black_channel")

    # ========================================================
    # 6. LODOWE JASKINIE
    # ========================================================
    _catalog_mut.catalog_assign("ice_cave_mouth", 'ROOMS', ROOMS, ("ice_pass", "exits", "east"))
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, (), {
        "ice_cave_mouth": {"zone":"Lodowe Jaskinie","name":"Wejście do Lodowych Jaskiń","desc":"Szczelina w lodzie prowadzi do błękitnych tuneli pod górą.","exits":{"west":"ice_pass","east":"ice_cave_blue_tunnel"}},
        "ice_cave_blue_tunnel": {"zone":"Lodowe Jaskinie","name":"Błękitny Tunel","desc":"Światło odbija się w tysiącach drobnych kryształów lodu.","exits":{"west":"ice_cave_mouth","east":"ice_cave_frozen_lake","north":"ice_cave_crystal_chamber"}},
        "ice_cave_crystal_chamber": {"zone":"Lodowe Jaskinie","name":"Komnata Lodowego Kryształu","desc":"Komnata lodowych kryształów. Wydobycie przeniesiono do Kopalni Głębinowej; komnata pozostała miejscem eksploracji i walki.","exits":{"south":"ice_cave_blue_tunnel","east":"ice_cave_glacier裂"}},
        "ice_cave_frozen_lake": {"zone":"Lodowe Jaskinie","name":"Zamarznięte Jezioro","desc":"Gruby lód przykrywa czarną wodę. Coś porusza się pod powierzchnią.","exits":{"west":"ice_cave_blue_tunnel","north":"ice_cave_glacier裂"}},
        "ice_cave_glacier裂": {"zone":"Lodowe Jaskinie","name":"Szczelina Lodowca","desc":"Wąska rozpadlina prowadzi do najstarszej części jaskiń.","exits":{"west":"ice_cave_crystal_chamber","south":"ice_cave_frozen_lake","north":"ice_cave_ancient_hall"}},
        "ice_cave_ancient_hall": {"zone":"Lodowe Jaskinie","name":"Pradawna Sala Lodu","desc":"Naturalne kolumny lodu przypominają salę tronową.","exits":{"south":"ice_cave_glacier裂","north":"ice_cave_dragon_nest"}},
        "ice_cave_dragon_nest": {"zone":"Lodowe Jaskinie","name":"Gniazdo Lodowego Smoka","desc":"Ogromne ślady pazurów otaczają gniazdo wykute w wiecznym lodzie.","exits":{"south":"ice_cave_ancient_hall"}},
    })

    # ========================================================
    # MOBS — 6 AREAS, REGULARS + ELITES + BOSSES
    # ========================================================
    _catalog_mut.catalog_update_path('MOB_TEMPLATES', MOB_TEMPLATES, (), {
        # Cemetery
        "cemetery_restless_dead":{"name":"Niespokojny Zmarły","max_hp":260,"damage":22,"damage_type":"physical","silver":55,"gold":0,"mithril":0,"stat_reward":70,"class_xp_reward":850,"soul_reward":520,"drops":{"soul_shard":0.25},"quest_target":None},
        "cemetery_grave_hound":{"name":"Grobowy Ogar","max_hp":320,"damage":26,"damage_type":"physical","silver":65,"gold":0,"mithril":0,"stat_reward":82,"class_xp_reward":1000,"soul_reward":610,"drops":{"wolf_fang":0.45},"quest_target":None},
        "cemetery_bone_collector":{"name":"Zbieracz Kości","max_hp":410,"damage":31,"damage_type":"magic","silver":80,"gold":1,"mithril":0,"stat_reward":95,"class_xp_reward":1250,"soul_reward":750,"drops":{"soul_shard":0.45},"quest_target":None},
        "cemetery_bell_wraith":{"name":"Upiór Martwego Dzwonu","max_hp":540,"damage":38,"damage_type":"magic","silver":95,"gold":1,"mithril":0,"stat_reward":115,"class_xp_reward":1550,"soul_reward":930,"drops":{"soul_shard":0.60},"quest_target":None},
        "cemetery_keeper":{"name":"Nieumarły Strażnik Cmentarza","max_hp":1300,"damage":55,"damage_type":"physical","silver":250,"gold":3,"mithril":0,"stat_reward":180,"class_xp_reward":3300,"soul_reward":1900,"drops":{"soul_elixir":0.18},"quest_target":None,"boss_mechanic":"cemetery_keeper","world_boss":True},
        # Cult ruins
        "cult_acolyte":{"name":"Akolita Pustki","max_hp":520,"damage":41,"damage_type":"magic","silver":100,"gold":1,"mithril":0,"stat_reward":120,"class_xp_reward":1750,"soul_reward":1050,"drops":{"soul_shard":0.45},"quest_target":None},
        "cult_blade":{"name":"Ostrze Kultu","max_hp":610,"damage":47,"damage_type":"physical","silver":115,"gold":1,"mithril":0,"stat_reward":135,"class_xp_reward":2050,"soul_reward":1220,"drops":{"soul_shard":0.40},"quest_target":None},
        "cult_void_seer":{"name":"Wieszcz Pustki","max_hp":700,"damage":53,"damage_type":"magic","silver":130,"gold":2,"mithril":0,"stat_reward":150,"class_xp_reward":2350,"soul_reward":1450,"drops":{"soul_elixir":0.10},"quest_target":None},
        "cult_ritual_guard":{"name":"Strażnik Rytuału","max_hp":850,"damage":61,"damage_type":"physical","silver":150,"gold":2,"mithril":0,"stat_reward":165,"class_xp_reward":2750,"soul_reward":1700,"drops":{"soul_shard":0.70},"quest_target":None},
        "cult_archon":{"name":"Arcykultysta Otchłani","max_hp":2400,"damage":82,"damage_type":"magic","silver":350,"gold":6,"mithril":0,"stat_reward":260,"class_xp_reward":6000,"soul_reward":4200,"drops":{"soul_elixir":0.30},"quest_target":None,"boss_mechanic":"void_archon","world_boss":True},
        # Beast lair
        "beast_cave_stalker":{"name":"Jaskiniowy Tropiciel","max_hp":430,"damage":36,"damage_type":"physical","silver":75,"gold":1,"mithril":0,"stat_reward":105,"class_xp_reward":1450,"soul_reward":880,"drops":{"wolf_fang":0.55},"quest_target":None},
        "beast_ironhide_boar":{"name":"Dzik Żelaznoskóry","max_hp":650,"damage":45,"damage_type":"physical","silver":90,"gold":1,"mithril":0,"stat_reward":125,"class_xp_reward":1800,"soul_reward":1100,"drops":{},"quest_target":None},
        "beast_root_bear":{"name":"Niedźwiedź Korzeni","max_hp":780,"damage":52,"damage_type":"physical","silver":105,"gold":1,"mithril":0,"stat_reward":140,"class_xp_reward":2200,"soul_reward":1350,"drops":{},"quest_target":None},
        "beast_bone_mane":{"name":"Kościanogrzywy Drapieżnik","max_hp":920,"damage":60,"damage_type":"physical","silver":125,"gold":2,"mithril":0,"stat_reward":160,"class_xp_reward":2600,"soul_reward":1600,"drops":{"soul_shard":0.35},"quest_target":None},
        "beast_ancient_alpha":{"name":"Pradawny Alfa Bestii","max_hp":2800,"damage":88,"damage_type":"physical","silver":320,"gold":5,"mithril":0,"stat_reward":275,"class_xp_reward":6500,"soul_reward":4500,"drops":{"soul_elixir":0.22},"quest_target":None,"boss_mechanic":"ancient_alpha","world_boss":True},
        # Necropolis
        "necro_tomb_guard":{"name":"Strażnik Grobowca","max_hp":820,"damage":58,"damage_type":"physical","silver":130,"gold":2,"mithril":0,"stat_reward":165,"class_xp_reward":2800,"soul_reward":1750,"drops":{"soul_shard":0.55},"quest_target":None},
        "necro_mourning_spirit":{"name":"Duch Żałobnika","max_hp":760,"damage":62,"damage_type":"magic","silver":140,"gold":2,"mithril":0,"stat_reward":175,"class_xp_reward":3000,"soul_reward":1900,"drops":{"soul_shard":0.65},"quest_target":None},
        "necro_bone_knight":{"name":"Kościany Rycerz","max_hp":1050,"damage":72,"damage_type":"physical","silver":165,"gold":3,"mithril":0,"stat_reward":195,"class_xp_reward":3500,"soul_reward":2250,"drops":{},"quest_target":None},
        "necro_royal_lich":{"name":"Królewski Licz","max_hp":1250,"damage":78,"damage_type":"magic","silver":185,"gold":3,"mithril":0,"stat_reward":210,"class_xp_reward":3900,"soul_reward":2550,"drops":{"soul_elixir":0.12},"quest_target":None},
        "necro_dead_king":{"name":"Umarły Król Nekropolii","max_hp":4200,"damage":105,"damage_type":"magic","silver":450,"gold":9,"mithril":1,"stat_reward":340,"class_xp_reward":9000,"soul_reward":7000,"drops":{"soul_elixir":0.38},"quest_target":None,"boss_mechanic":"dead_king","world_boss":True},
        # Sewers
        "sewer_plague_rat":{"name":"Szczur Zarazy","max_hp":210,"damage":19,"damage_type":"physical","silver":40,"gold":0,"mithril":0,"stat_reward":60,"class_xp_reward":700,"soul_reward":410,"drops":{},"quest_target":None},
        "sewer_slime":{"name":"Szlam Kanałowy","max_hp":290,"damage":23,"damage_type":"magic","silver":48,"gold":0,"mithril":0,"stat_reward":72,"class_xp_reward":850,"soul_reward":500,"drops":{},"quest_target":None},
        "sewer_smuggler":{"name":"Przemytnik Kanałów","max_hp":360,"damage":28,"damage_type":"physical","silver":70,"gold":1,"mithril":0,"stat_reward":85,"class_xp_reward":1050,"soul_reward":640,"drops":{},"quest_target":None},
        "sewer_mutant":{"name":"Mutant z Cysterny","max_hp":500,"damage":35,"damage_type":"physical","silver":85,"gold":1,"mithril":0,"stat_reward":100,"class_xp_reward":1350,"soul_reward":820,"drops":{"soul_shard":0.25},"quest_target":None},
        "sewer_king":{"name":"Król Podmiejskich Kanałów","max_hp":1500,"damage":58,"damage_type":"physical","silver":260,"gold":3,"mithril":0,"stat_reward":190,"class_xp_reward":3600,"soul_reward":2200,"drops":{"soul_elixir":0.15},"quest_target":None,"boss_mechanic":"sewer_king","world_boss":True},
        # Ice caves
        "ice_fang_wolf":{"name":"Wilk Lodowego Kła","max_hp":700,"damage":52,"damage_type":"physical","silver":110,"gold":1,"mithril":0,"stat_reward":145,"class_xp_reward":2350,"soul_reward":1450,"drops":{"wolf_fang":0.70},"quest_target":None},
        "ice_crystal_golem":{"name":"Golem Lodowego Kryształu","max_hp":980,"damage":60,"damage_type":"magic","silver":135,"gold":2,"mithril":0,"stat_reward":170,"class_xp_reward":2900,"soul_reward":1850,"drops":{"soul_shard":0.50},"quest_target":None},
        "ice_wraith":{"name":"Upiór Szronu","max_hp":860,"damage":65,"damage_type":"magic","silver":145,"gold":2,"mithril":0,"stat_reward":180,"class_xp_reward":3150,"soul_reward":2050,"drops":{"soul_shard":0.65},"quest_target":None},
        "ice_glacier_guard":{"name":"Strażnik Lodowca","max_hp":1200,"damage":74,"damage_type":"physical","silver":170,"gold":3,"mithril":0,"stat_reward":205,"class_xp_reward":3700,"soul_reward":2450,"drops":{},"quest_target":None},
        "ice_dragon":{"name":"Pradawny Lodowy Smok","flying":True,"max_hp":5000,"damage":118,"damage_type":"magic","silver":520,"gold":10,"mithril":1,"stat_reward":380,"class_xp_reward":10500,"soul_reward":8200,"drops":{"soul_elixir":0.42},"quest_target":None,"boss_mechanic":"ice_dragon","world_boss":True},
    })

    MOB_SPAWNS.extend([
        # v0.36.5: Soul Tier 7 asks for 4 Niespokojnych Zmarłych. Keep six
        # simultaneous targets distributed across the whole Stary Cmentarz so the
        # trial never depends on waiting for a single respawn.
        ("graveyard","cemetery_restless_dead"),("cemetery_ossuary_path","cemetery_restless_dead"),
        ("cemetery_moon_garden","cemetery_restless_dead"),("cemetery_fallen_chapel","cemetery_restless_dead"),
        ("cemetery_bone_field","cemetery_restless_dead"),("cemetery_bell_tower","cemetery_restless_dead"),
        ("cemetery_moon_garden","cemetery_grave_hound"),("cemetery_fallen_chapel","cemetery_bone_collector"),("cemetery_bone_field","cemetery_grave_hound"),("cemetery_bell_tower","cemetery_bell_wraith"),("cemetery_keeper_tomb","cemetery_keeper"),
        ("cult_ruins_gate","cult_acolyte"),("cult_ruins_courtyard","cult_blade"),("cult_ruins_overgrown_garden","cult_acolyte"),("cult_ruins_cloister","cult_void_seer"),("cult_ruins_library","cult_void_seer"),("cult_ruins_ritual_hall","cult_ritual_guard"),("cult_ruins_sanctum","cult_archon"),
        ("beast_lair_mouth","beast_cave_stalker"),("beast_lair_tracks","beast_cave_stalker"),("beast_lair_root_cavern","beast_ironhide_boar"),("beast_lair_bone_nest","beast_bone_mane"),("beast_lair_hunting_ground","beast_root_bear"),("beast_lair_alpha_den","beast_ancient_alpha"),
        ("necropolis_gate","necro_tomb_guard"),("necropolis_procession","necro_tomb_guard"),("necropolis_quarry","necro_bone_knight"),("necropolis_catacombs","necro_mourning_spirit"),("necropolis_silent_square","necro_bone_knight"),("necropolis_royal_tombs","necro_royal_lich"),("necropolis_throne","necro_dead_king"),
        ("sewer_runoff","sewer_plague_rat"),("sewer_rat_nest","sewer_plague_rat"),("sewer_black_channel","sewer_slime"),("sewer_smuggler_den","sewer_smuggler"),("sewer_flooded_vault","sewer_mutant"),("sewer_cistern","sewer_king"),
        ("ice_cave_mouth","ice_fang_wolf"),("ice_cave_blue_tunnel","ice_fang_wolf"),("ice_cave_crystal_chamber","ice_crystal_golem"),("ice_cave_frozen_lake","ice_wraith"),("ice_cave_glacier裂","ice_glacier_guard"),("ice_cave_ancient_hall","ice_wraith"),("ice_cave_dragon_nest","ice_dragon"),
    ])

    # ========================================================
    # FIELD PROFESSION QUESTS
    # ========================================================
    _catalog_mut.catalog_update_path('QUESTS', QUESTS, (), {
        "field_grave_moss": {"name":"Terenowe Zielarstwo: Mech Nagrobny","giver":"Mistrzyni Zielarstwa Sena","kind":"collect_resource","target":"field_grave_moss","needed":8,"description":"Zbierz 8 sztuk Mchu Nagrobnego wyłącznie w Ogrodzie Księżycowego Mchu na Starym Cmentarzu. Postęp zaczyna od 0/8 i rośnie przy każdym nowym zbiorze po przyjęciu questa.","progress_label":"Mech Nagrobny","specialist_tool_type":"herbalism","min_tool_level":20,"reward_profession":"Zielarstwo","reward_profession_xp":1400,"reward_tool_type":"herbalism","reward_tool_xp":1100,"reward_silver":260,"reward_gold":1,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_void_thorn": {"name":"Terenowe Zielarstwo: Cierń Pustki","giver":"Mistrzyni Zielarstwa Sena","kind":"collect_resource","target":"field_void_thorn","needed":8,"description":"Zbierz 8 Cierni Pustki wyłącznie w Ogrodzie Cierni Pustki w Ruinach Kultystów.","specialist_tool_type":"herbalism","min_tool_level":60,"reward_profession":"Zielarstwo","reward_profession_xp":2400,"reward_tool_type":"herbalism","reward_tool_xp":1900,"reward_silver":420,"reward_gold":2,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_ironbark_root": {"name":"Terenowe Drwalstwo: Korzeń Żelaznokory","giver":"Mistrz Drwalstwa Oren","kind":"collect_resource","target":"field_ironbark_root","needed":8,"description":"Pozyskaj 8 Korzeni Żelaznokory wyłącznie w Grocie Żelaznokory w Legowisku Bestii.","specialist_tool_type":"woodcutting","min_tool_level":40,"reward_profession":"Drwalstwo","reward_profession_xp":1900,"reward_tool_type":"woodcutting","reward_tool_xp":1500,"reward_silver":330,"reward_gold":1,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_tomb_silver": {"name":"Głębinowe Górnictwo: Srebro Grobowe","giver":"Mistrz Górnictwa Kordan","kind":"collect_resource","target":"field_tomb_silver","needed":10,"description":"Wydobądź 10 Srebra Grobowego w Kopalni Głębinowej od poziomu 80.","specialist_tool_type":"mining","min_tool_level":80,"reward_profession":"Górnictwo","reward_profession_xp":3200,"reward_tool_type":"mining","reward_tool_xp":2600,"reward_silver":600,"reward_gold":3,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_blind_sewer_eel": {"name":"Terenowe Wędkarstwo: Ślepy Węgorz","giver":"Mistrz Wędkarstwa Neris","kind":"collect_resource","target":"field_blind_sewer_eel","needed":6,"description":"Złów 6 Ślepych Węgorzy Kanałowych wyłącznie w Czarnym Kanale pod Miastem Dusz.","specialist_tool_type":"fishing","min_tool_level":30,"reward_profession":"Wędkarstwo","reward_profession_xp":1600,"reward_tool_type":"fishing","reward_tool_xp":1300,"reward_silver":300,"reward_gold":1,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_frost_crystal_ore": {"name":"Głębinowe Górnictwo: Lodowy Kryształ","giver":"Mistrz Górnictwa Kordan","kind":"collect_resource","target":"field_frost_crystal_ore","needed":10,"description":"Wydobądź 10 Rudy Lodowego Kryształu w Kopalni Głębinowej od poziomu 100.","specialist_tool_type":"mining","min_tool_level":100,"reward_profession":"Górnictwo","reward_profession_xp":4200,"reward_tool_type":"mining","reward_tool_xp":3500,"reward_silver":800,"reward_gold":4,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
    })

    # Specialists list these field quests when spoken to.
    _catalog_mut.catalog_assign(tuple(NPCS["specialist_herbalism"].get("specialist_quests", ())) + ("field_grave_moss","field_void_thorn"), 'NPCS', NPCS, ("specialist_herbalism", "specialist_quests"))
    _catalog_mut.catalog_assign(tuple(NPCS["specialist_woodcutting"].get("specialist_quests", ())) + ("field_ironbark_root",), 'NPCS', NPCS, ("specialist_woodcutting", "specialist_quests"))
    _catalog_mut.catalog_assign(tuple(NPCS["specialist_mining"].get("specialist_quests", ())) + ("field_tomb_silver","field_frost_crystal_ore"), 'NPCS', NPCS, ("specialist_mining", "specialist_quests"))
    _catalog_mut.catalog_assign(tuple(NPCS["specialist_fishing"].get("specialist_quests", ())) + ("field_blind_sewer_eel",), 'NPCS', NPCS, ("specialist_fishing", "specialist_quests"))

    # ========================================================
    # GUIDE — only entrances; interior remains exploration-only
    # ========================================================
    GUIDE_DESTINATION_ALIASES.update({
        "cmentarz":"graveyard","stary cmentarz":"graveyard","cemetery":"graveyard",
        "ruiny kultystow":"cult_ruins_gate","ruiny kultu":"cult_ruins_gate","cultist ruins":"cult_ruins_gate",
        "legowisko bestii":"beast_lair_mouth","beast lair":"beast_lair_mouth",
        "nekropolia":"necropolis_gate","necropolis":"necropolis_gate",
        "kanaly":"sewer_entrance","kanaly pod miastem":"sewer_entrance","sewers":"sewer_entrance","city sewers":"sewer_entrance",
        "lodowe jaskinie":"ice_cave_mouth","lodowa jaskinia":"ice_cave_mouth","ice caves":"ice_cave_mouth","ice cave":"ice_cave_mouth",
    })

    # ========================================================
    # EXP AREAS
    # ========================================================
    EXP_AREAS = EXP_AREAS + (
        {"id":"cmentarz","name":"Stary Cmentarz","aliases":("cmentarz","stary cmentarz","cemetery"),"soul_min":15,"soul_max":45,"difficulty":"łatwa do średniej","guide":"cmentarz","enemies":"Niespokojni Zmarli, Grobowe Ogary, Zbieracze Kości, Upiory Dzwonu i Nieumarły Strażnik Cmentarza","description":"Rozbudowany cmentarz z alejami, kaplicą, polem kości, miejscem Zielarstwa i bossem na końcu.","note":"Mech Nagrobny można zebrać tylko w Ogrodzie Księżycowego Mchu."},
        {"id":"ruiny_kultystow","name":"Ruiny Kultystów","aliases":("ruiny kultystow","ruiny kultu","cultist ruins"),"soul_min":40,"soul_max":80,"difficulty":"średnia do trudnej","guide":"ruiny kultystow","enemies":"Akolici Pustki, Ostrza Kultu, Wieszcze Pustki, Strażnicy Rytuału i Arcykultysta Otchłani","description":"Zniszczony kompleks kultu z ogrodem skażonych roślin, biblioteką i sanktuarium.","note":"Cierń Pustki występuje tylko w Ogrodzie Cierni Pustki."},
        {"id":"legowisko_bestii","name":"Legowisko Bestii","aliases":("legowisko bestii","beast lair"),"soul_min":35,"soul_max":75,"difficulty":"średnia","guide":"legowisko bestii","enemies":"Jaskiniowe Tropiciele, Dziki Żelaznoskóre, Niedźwiedzie Korzeni, Kościanogrzywe Drapieżniki i Pradawny Alfa","description":"Podziemne legowisko drapieżników z bocznymi norami, terenem Drwalstwa i bossem alfa.","note":"Korzeń Żelaznokory pozyskuje się tylko w Grocie Żelaznokory."},
        {"id":"nekropolia","name":"Nekropolia","aliases":("nekropolia","necropolis"),"soul_min":70,"soul_max":125,"difficulty":"trudna","guide":"nekropolia","enemies":"Strażnicy Grobowców, Duchy Żałobników, Kościani Rycerze, Królewscy Licze i Umarły Król","description":"Miasto grobowców za Starym Cmentarzem, z katakumbami, kamieniołomem i królewską częścią.","note":"Srebro Grobowe wydobywa się w Kopalni Głębinowej od poziomu 80; kamieniołom jest miejscem eksploracji."},
        {"id":"kanaly","name":"Kanały Pod Miastem","aliases":("kanaly","kanaly pod miastem","sewers","city sewers"),"soul_min":10,"soul_max":45,"difficulty":"łatwa do średniej","guide":"kanaly","enemies":"Szczury Zarazy, Szlamy Kanałowe, Przemytnicy, Mutanci i Król Podmiejskich Kanałów","description":"Podziemna sieć pod Miastem Dusz z kanałem, kryjówką przemytników i starą cysterną.","note":"Ślepy Węgorz Kanałowy żyje tylko w Czarnym Kanale."},
        {"id":"lodowe_jaskinie","name":"Lodowe Jaskinie","aliases":("lodowe jaskinie","lodowa jaskinia","ice caves","ice cave"),"soul_min":60,"soul_max":115,"difficulty":"trudna","guide":"lodowe jaskinie","enemies":"Wilki Lodowego Kła, Golemy Lodowego Kryształu, Upiory Szronu, Strażnicy Lodowca i Pradawny Lodowy Smok","description":"Rozległe jaskinie odchodzące od Lodowej Przełęczy, z kryształową komnatą i gniazdem smoka.","note":"Rudę Lodowego Kryształu wydobywa się w Kopalni Głębinowej od poziomu 100; komnata jest miejscem eksploracji i walki."},
    )

    HELP_TOPICS["world_expansion_ii"] = [
        "World Expansion II dodaje 6 rozbudowanych expowisk: Stary Cmentarz, Ruiny Kultystów, Legowisko Bestii, Nekropolię, Kanały Pod Miastem i Lodowe Jaskinie.",
        "Każdy obszar ma własne pokoje, zwykłe moby, mocniejsze moby i bossa na końcu.",
        "prowadz / guide / walk prowadzi tylko przed wejście; wnętrze trzeba eksplorować samodzielnie.",
        "Dodano terenowe questy profesyjne z unikalnymi surowcami możliwymi do zdobycia tylko w konkretnym miejscu.",
        "Sena: Mech Nagrobny ze Starego Cmentarza i Cierń Pustki z Ruin Kultystów.",
        "Oren: Korzeń Żelaznokory z Legowiska Bestii.",
        "Kordan: wszystkie rudy, w tym Srebro Grobowe i Rudę Lodowego Kryształu, wydobywa się w Kopalni Głębinowej.",
        "Neris: Ślepy Węgorz Kanałowy z Kanałów Pod Miastem.",
    ]
    HELP_TOPICS["questy_profesji_teren"] = HELP_TOPICS["world_expansion_ii"]

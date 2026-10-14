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


def configure_profession_tool_sellers():
    # v0.8.8: wszystkie narzędzia profesji są przypisane do postaci.
    for _bound_tool_id in CHARACTER_BOUND_TOOL_IDS:
        if _bound_tool_id in ITEMS:
            _catalog_mut.catalog_assign(True, 'ITEMS', ITEMS, (_bound_tool_id, "character_bound"))

    """
    Każde narzędzie jest sprzedawane tylko przez NPC dokładnie
    związany z daną profesją. Narzędzia są usuwane ze wszystkich
    innych sklepów przed przypisaniem docelowych sprzedawców.
    """

    # Osobna kuchnia dla Kucharza Marcela, żeby Karczmarz
    # nie sprzedawał narzędzia profesji Gotowanie.
    _catalog_mut.catalog_assign("blue_flame_kitchen", 'ROOMS', ROOMS, ("inn", "exits", "east"))
    _catalog_mut.catalog_assign({
        "zone": "Miasto Dusz",
        "name": "Kuchnia Błękitnego Płomienia",
        "desc": (
            "Gorąca kuchnia pełna garnków, pieców i stołów roboczych. "
            "Kucharz Marcel prowadzi tutaj Gotowanie i jako jedyny "
            "sprzedaje Nóż Kucharski."
        ),
        "exits": {"west": "inn"},
    }, 'ROOMS', ROOMS, ("blue_flame_kitchen",))
    _catalog_mut.catalog_assign("blue_flame_kitchen", 'NPCS', NPCS, ("specialist_cooking", "room"))

    profession_tools = {
        "fishing_rod": ("fish_market", "fisher_tomas"),
        "pickaxe": ("cave_entrance", "miner_toren"),
        "saw": ("forester_lodge", "specialist_woodcutting"),
        "crafting_hammer": (
            "crafting_workshop",
            "specialist_crafting",
        ),
        "chef_knife": (
            "blue_flame_kitchen",
            "specialist_cooking",
        ),
        "herbalist_sickle": (
            "herbalism_garden",
            "specialist_herbalism",
        ),
        "alchemy_mortar": (
            "alchemy_lab",
            "specialist_alchemy",
        ),
        "jeweler_pliers": (
            "jeweler_workshop",
            "jeweler_mirella",
        ),
    }

    tool_ids = set(profession_tools)

    # Usuń wszystkie narzędzia z dotychczasowych sklepów.
    for room_id in list(SHOPS):
        _catalog_mut.catalog_assign([
            item_id
            for item_id in SHOPS[room_id]
            if item_id not in tool_ids
        ], 'SHOPS', SHOPS, (room_id,))
        if not SHOPS[room_id]:
            _catalog_mut.catalog_pop_path('SHOPS', SHOPS, (), room_id, None)

    # Dodaj każde narzędzie dokładnie raz.
    for item_id, (room_id, seller_id) in profession_tools.items():
        _catalog_mut.catalog_setdefault_path('SHOPS', SHOPS, (), room_id, [])
        if item_id not in SHOPS[room_id]:
            SHOPS[room_id].append(item_id)
        SHOP_SELLERS[room_id] = seller_id
        TOOL_SHOP_ROOMS[item_id] = room_id

        npc = NPCS.get(seller_id)
        if npc is not None:
            npc["shopkeeper"] = True

    # Stare sklepy zachowują sprzedawcę tylko dla swoich innych towarów.
    SHOP_SELLERS["inn"] = "innkeeper"
    SHOP_SELLERS["forge"] = "doran"

    # Przejrzyste opisy NPC.
    _catalog_mut.catalog_assign(True, 'NPCS', NPCS, ("fisher_tomas", "shopkeeper"))
    _catalog_mut.catalog_assign("Jeśli chcesz zacząć Wędkarstwo, kupisz u mnie podstawową Wędkę. "
        "Przynieś mi także trzydzieści dowolnych ryb, a wynagrodzę twoją pracę. "
        "Wpisz list albo shop, aby zobaczyć ofertę.", 'NPCS', NPCS, ("fisher_tomas", "dialogue"))
    _catalog_mut.catalog_assign("Jestem Mistrzem Wędkarstwa Neris. Uczę rozwoju Wędki, Tierów "
        "i łowisk wysokiego levelu. Podstawową Wędkę kupisz u Rybaka Borysa na Targu Rybnym.", 'NPCS', NPCS, ("specialist_fishing", "dialogue"))
    _catalog_mut.catalog_assign("Dobra ruda nie wydobędzie się sama. "
        "Tylko u mnie kupisz Kilof do Górnictwa. "
        "Wpisz list albo shop, aby zobaczyć ofertę.", 'NPCS', NPCS, ("miner_toren", "dialogue"))
    _catalog_mut.catalog_assign("Jestem Mistrzem Drwalstwa. Tylko u mnie kupisz Piłę. "
        "Uczę pracy z drewnem od levelu 1 do 600.", 'NPCS', NPCS, ("specialist_woodcutting", "dialogue"))
    _catalog_mut.catalog_assign("Prowadzę Rzemiosło i Kowalstwo. "
        "Tylko u mnie kupisz Młot Rzemieślniczy.", 'NPCS', NPCS, ("specialist_crafting", "dialogue"))
    _catalog_mut.catalog_assign("Jestem Kucharzem Błękitnego Płomienia. "
        "Tylko u mnie kupisz Nóż Kucharski i uczysz się Gotowania.", 'NPCS', NPCS, ("specialist_cooking", "dialogue"))
    _catalog_mut.catalog_assign("Jestem Mistrzynią Zielarstwa. "
        "Tylko u mnie kupisz Sierp Zielarski.", 'NPCS', NPCS, ("specialist_herbalism", "dialogue"))
    _catalog_mut.catalog_assign("Jestem Mistrzem Alchemii. "
        "Tylko u mnie kupisz Moździerz Alchemiczny.", 'NPCS', NPCS, ("specialist_alchemy", "dialogue"))
    _catalog_mut.catalog_assign("Prowadzę Jubilerstwo od levelu 1 do 600. "
        "Tylko u mnie kupisz Szczypce Jubilerskie.", 'NPCS', NPCS, ("jeweler_mirella", "dialogue"))

    
    HELP_TOPICS["sprzedawcy_narzedzi"] = [
        "Każde narzędzie kupisz tylko u NPC dokładnie związanego z jego profesją.",
        "Wędka: Rybak Borys na Targu Rybnym.",
        "Kilof: Górnik Toren przy Wejściu do Kryształowej Jaskini.",
        "Piła: Mistrz Drwalstwa Oren w Leśniczówce.",
        "Młot Rzemieślniczy: Mistrz Rzemiosła Haldor w Warsztacie Rzemieślniczym.",
        "Nóż Kucharski: Kucharz Marcel w Kuchni Błękitnego Płomienia.",
        "Sierp Zielarski: Mistrzyni Zielarstwa Sena w Ogrodzie Zielarskim.",
        "Moździerz Alchemiczny: Mistrz Alchemii Orin w Laboratorium Alchemicznym.",
        "Szczypce Jubilerskie: Jubilerka Mirella w Pracowni Jubilerskiej.",
        "Żaden z tych przedmiotów nie jest sprzedawany w zwykłym sklepie innej profesji.",
    ]


def configure_v0800_help_info():
    HELP_TOPICS["informacje"] = [
        "W v0.8.0 najważniejsze komendy informacyjne mają dwa poziomy szczegółowości.",
        "Bez dopisku info dostajesz szybki stan, wygodny pod NVDA.",
        "Z dopiskiem info dostajesz pełny opis mechaniki, progów i dalszego celu.",
        "dusza - szybki stan Broni Duszy.",
        "dusza info - pełne Soul XP, Tiery, Próby Broni Duszy, progi i następny cel.",
        "staty - szybkie statystyki bojowe.",
        "staty info - statystyki bazowe, bonusy EQ, pasywy, sety i sposób rozwoju.",
        "profesje - szybkie levele i rangi profesji.",
        "profesje info - XP, akcje, następne rangi oraz narzędzia i sprzedawcy.",
        "narzedzia - szybki stan narzędzi.",
        "narzedzia info - XP, Tier, bonus, czas akcji i właściwy sprzedawca.",
        "eq - szybka lista założonego wyposażenia.",
        "eq info - pełne bonusy, obrona, sety, sockety i efektywne statystyki.",
        "kodeksklasowy <klasa> - skille, wymagana Biegłość, nauczyciel, cena i status odblokowania.",
        "help informacje - ten przewodnik.",
    ]
    HELP_TOPIC_ALIASES.update({
        "info": "informacje",
        "informacja": "informacje",
        "informacje": "informacje",
        "komendy info": "informacje",
    })


def configure_v081_help_info():
    HELP_TOPICS["sety_klasowe"] = [
        "Każda z 14 klas ma pełny zestaw 8 części: głowa, korpus, dłonie, nogi, stopy, talizman, pierścień i naszyjnik.",
        "Klasowe EQ ma Tiery Biegłości 1, 10, 20, 30 i dalej co 10 aż do 600; każdy próg daje mocniejszy pełny zestaw.",
        "Każda część klasowego EQ ma dwie podstawowe statystyki archetypu: klasy fizyczne dostają Siłę i Kondycję, a klasy magiczne Inteligencję i Siłę Woli.",
        "W klasach magicznych Inteligencja jest statystyką odpowiadającą mocy/mądrości magicznej; gra nie tworzy osobnej siódmej statystyki Mądrość.",
        "Sklep klasowy pokazuje najlepszy Tier odblokowany przez Biegłość danej klasy; wyższy Tier wymaga tej Biegłości także przy zakładaniu.",
        "Próg 2 części daje klasowy bonus do statystyk.",
        "Próg 4 części zwiększa wszystkie obrażenia.",
        "Próg 6 części zwiększa obronę fizyczną i magiczną.",
        "Próg 8 części zwiększa maksymalne HP, a klasom magicznym także Manę.",
        "Wartości są różne dla każdej klasy, np. Berserker i Czarownik mają bardziej ofensywne sety, a Strażnik bardziej defensywny.",
        "Bonus liczy się tylko dla aktywnej klasy.",
        "Komenda sety pokazuje aktywne sety.",
        "Komenda sety info pokazuje wszystkie 14 zestawów i progi 2/4/6/8.",
        "Komenda sety <klasa> pokazuje konkretny zestaw.",
        "eq info i staty info pokazują aktywne bonusy setów klasowych.",
    ]
    HELP_TOPICS["teren_info"] = [
        "teren info <nazwa> pokazuje zbiorcze informacje o regionie.",
        "Przykład: teren info bagna, teren info góry, teren info pustynia.",
        "Informacje obejmują liczbę lokacji, orientacyjny zakres Soul, trudność, NPC, questy, bossów, przeciwników, profesje i dojście.",
        "Dane są zbierane z faktycznego świata gry, NPC, spawnów i expowisk.",
        "expowiska <nazwa> nadal służy do szczegółów expienia.",
        "mapa nadal pokazuje strukturę lokacji.",
        "prowadz <teren> prowadzi do wybranego regionu.",
    ]
    HELP_TOPIC_ALIASES.update({
        "sety": "sety_klasowe",
        "sety klasowe": "sety_klasowe",
        "set klasowy": "sety_klasowe",
        "class sets": "sety_klasowe",
        "teren": "teren_info",
        "teren info": "teren_info",
        "region": "teren_info",
        "region info": "teren_info",
    })
    HELP_TOPICS["informacje"].extend([
        "sety / sety info - aktywne i pełne bonusy zestawów klasowych 2/4/6/8.",
        "teren info <nazwa> - region, Soul, NPC, questy, bossowie, profesje i dojście.",
    ])

    # Uaktualnienie starszych opisów po rozwoju profesji i narzędzi.
    if "profesje" in HELP_TOPICS:
        HELP_TOPICS["profesje"].append(
            "Aktualne profesje 1-600: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo i Jubilerstwo. Każda ma własny poziom; odpowiadające narzędzie rozwija się osobno."
        )
    if "ekwipunek" in HELP_TOPICS:
        HELP_TOPICS["ekwipunek"].append(
            "Wyposażenie klasowe ma teraz aktywne progi zestawu 2/4/6/8. Użyj sety info."
        )


def build_paid_training_guild_expansion():
    """v0.8.9: płatna nauka i 12 osobnych sal klasowych."""

    class_rooms = {
        "teacher_warrior": (
            "guild_warrior_chamber", "Sala Wojownika",
            "guild_martial_hall",
            "Sala tarcz, mieczy i ciężkich manekinów. Mistrz Garran szkoli tu wyłącznie Wojowników.",
        ),
        "teacher_berserker": (
            "guild_berserker_chamber", "Sala Berserkera",
            "guild_martial_hall",
            "Wzmocnione ściany i ciężkie cele pozwalają ćwiczyć furię bez narażania całej Gildii.",
        ),
        "teacher_monk": (
            "guild_monk_chamber", "Sala Mnicha",
            "guild_body_hall",
            "Cicha sala oddechu, równowagi i walki wręcz. Mistrz Shen prowadzi tu trening Mnichów.",
        ),
        "teacher_guardian": (
            "guild_guardian_chamber", "Bastion Strażnika",
            "guild_body_hall",
            "Ciężkie tarcze i stanowiska obronne tworzą salę przeznaczoną wyłącznie dla tanków Strażników.",
        ),
        "teacher_rogue": (
            "guild_rogue_chamber", "Sala Łotrzyka",
            "guild_shadow_gallery",
            "Wąskie przejścia, zamki i cele precyzyjne służą treningowi Łotrzyków.",
        ),
        "teacher_hunter": (
            "guild_hunter_chamber", "Sala Łowcy",
            "guild_shadow_gallery",
            "Długi tor strzelecki i ruchome cele pozwalają Łowcom trenować bez przeszkadzania Łotrzykom.",
        ),
        "teacher_mage": (
            "guild_mage_chamber", "Komnata Maga",
            "guild_arcane_chamber",
            "Runy izolują energię Arkanów. Arcymag Vaelis szkoli tu tylko Magów.",
        ),
        "teacher_psion": (
            "guild_psion_chamber", "Komnata Psionika",
            "guild_arcane_chamber",
            "Wyciszona komnata skupienia chroni innych przed niekontrolowaną energią umysłu.",
        ),
        "teacher_necromancer": (
            "guild_necromancer_chamber", "Komnata Nekromanty",
            "guild_dark_chamber",
            "Pieczęcie ochronne otaczają salę pracy z energią śmierci. Morwen szkoli tu Nekromantów.",
        ),
        "teacher_warlock": (
            "guild_warlock_chamber", "Komnata Czarownika",
            "guild_dark_chamber",
            "Osobna sala Otchłani pozwala Czarownikom trenować bez zakłócania nauki Nekromantów.",
        ),
        "teacher_priest": (
            "guild_priest_chamber", "Kaplica Kapłana",
            "guild_sanctuary",
            "Jasna kaplica leczenia i ochrony. Mistrz Aureon prowadzi tu naukę Kapłanów.",
        ),
        "teacher_druid": (
            "guild_druid_chamber", "Gaj Druida",
            "guild_sanctuary",
            "Żywe rośliny i kamienny krąg tworzą osobny gaj treningowy dla Druidów.",
        ),
    }

    # Każda dotychczasowa sala pary staje się hubem z dwoma wyjściami.
    room_links = {
        "guild_martial_hall": (
            ("north", "guild_warrior_chamber"),
            ("west", "guild_berserker_chamber"),
        ),
        "guild_body_hall": (
            ("north", "guild_monk_chamber"),
            ("east", "guild_guardian_chamber"),
        ),
        "guild_shadow_gallery": (
            ("north", "guild_rogue_chamber"),
            ("east", "guild_hunter_chamber"),
        ),
        "guild_arcane_chamber": (
            ("north", "guild_mage_chamber"),
            ("south", "guild_psion_chamber"),
        ),
        "guild_dark_chamber": (
            ("north", "guild_necromancer_chamber"),
            ("east", "guild_warlock_chamber"),
        ),
        "guild_sanctuary": (
            ("south", "guild_priest_chamber"),
            ("west", "guild_druid_chamber"),
        ),
    }
    for hub, links in room_links.items():
        for direction, target in links:
            _catalog_mut.catalog_assign(target, 'ROOMS', ROOMS, (hub, "exits", direction))

    # Return direction is deliberately simple for screen-reader navigation.
    return_direction = {
        "guild_martial_hall": "south",
        "guild_body_hall": "west",
        "guild_shadow_gallery": "down",
        "guild_arcane_chamber": "west",
        "guild_dark_chamber": "west",
        "guild_sanctuary": "up",
    }

    for teacher_id, (room_id, room_name, hub, desc) in class_rooms.items():
        _catalog_mut.catalog_assign({
            "zone": "Gildia Dusz",
            "name": room_name,
            "desc": desc,
            "exits": {return_direction[hub]: hub},
        }, 'ROOMS', ROOMS, (room_id,))
        _catalog_mut.catalog_assign(room_id, 'NPCS', NPCS, (teacher_id, "room"))
        _catalog_mut.catalog_aug_path('NPCS', NPCS, (teacher_id, "dialogue"), 'Add', " Nauka umiejętności jest płatna. Cena rośnie wraz z wymaganą Biegłością klasy skilla.")

    
    HELP_TOPICS["nauka"] = [
        "Nauka umiejętności klasowych u nauczycieli Gildii Dusz jest płatna.",
        "Cena zależy od Biegłości klasy wymaganej przez konkretną umiejętność.",
        "Skille kosztują wspólną walutę; późniejsze skille kosztują coraz więcej.",
        "Nauczyciel zawsze podaje cenę przed nauką.",
        "Komendy: learn <numer>, learn <skill>, naucz <numer>, naucz <umiejętność>.",
        "Pieniądze są pobierane dopiero po sprawdzeniu aktywnej klasy, wymaganej Biegłości i tego, czy skill nie jest już znany.",
        "Każda z 14 klas ma teraz własną salę i własnego nauczyciela.",
        "Wpisz teachers albo nauczyciele, aby usłyszeć dokładne lokacje.",
    ]


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


def build_world_expansion_i():
    global EXP_AREAS

    # ========================================================
    # LOGICZNY PODZIAŁ ISTNIEJĄCYCH SPECJALISTÓW
    # Sprzedawcy podstawowych narzędzi zostają w swoich punktach,
    # a mistrzowie profesji dostają osobne miejsca nauki.
    # ========================================================
    _catalog_mut.catalog_assign("fishing_school", 'ROOMS', ROOMS, ("fish_market", "exits", "west"))
    _catalog_mut.catalog_assign({
        "zone": "Miasto Dusz",
        "name": "Szkoła Wędkarstwa",
        "desc": (
            "Cicha sala nad Targiem Rybnym. Na ścianach wiszą mapy "
            "łowisk i stare wędki mistrzów. Tutaj uczy Neris."
        ),
        "exits": {"east": "fish_market"},
    }, 'ROOMS', ROOMS, ("fishing_school",))

    _catalog_mut.catalog_assign("miners_guild", 'ROOMS', ROOMS, ("cave_entrance", "exits", "east"))
    _catalog_mut.catalog_assign({
        "zone": "Podziemia",
        "name": "Gildia Górników",
        "desc": (
            "Kamienna izba przy wejściu do kopalni. Kordan prowadzi "
            "tu szkolenie z Górnictwa, z dala od sklepu Torena."
        ),
        "exits": {"west": "cave_entrance"},
    }, 'ROOMS', ROOMS, ("miners_guild",))

    _catalog_mut.catalog_assign("forester_lodge", 'ROOMS', ROOMS, ("lumberjack_camp", "exits", "north"))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Leśniczówka",
        "desc": (
            "Drewniana leśniczówka stoi na skraju Gaju Szeptów. "
            "Mistrz Drwalstwa Oren uczy tutaj pracy z rzadkim drewnem."
        ),
        "exits": {"south": "lumberjack_camp"},
    }, 'ROOMS', ROOMS, ("forester_lodge",))

    _catalog_mut.catalog_assign("herbalism_garden", 'ROOMS', ROOMS, ("herbalist_hut", "exits", "west"))
    _catalog_mut.catalog_assign("alchemy_lab", 'ROOMS', ROOMS, ("herbalist_hut", "exits", "east"))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Ogród Zielarski",
        "desc": (
            "Uporządkowane grządki otaczają mały drewniany pawilon. "
            "Mistrzyni Sena prowadzi tu naukę Zielarstwa."
        ),
        "exits": {"east": "herbalist_hut"},
    }, 'ROOMS', ROOMS, ("herbalism_garden",))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Laboratorium Alchemiczne",
        "desc": (
            "Kamienne stoły, retorty i moździerze wypełniają osobne "
            "laboratorium. Orin prowadzi tutaj Alchemię i swoje zlecenia."
        ),
        "exits": {"west": "herbalist_hut"},
    }, 'ROOMS', ROOMS, ("alchemy_lab",))

    _catalog_mut.catalog_assign("crafting_workshop", 'ROOMS', ROOMS, ("forge", "exits", "north"))
    _catalog_mut.catalog_assign({
        "zone": "Miasto Dusz",
        "name": "Warsztat Rzemieślniczy",
        "desc": (
            "Za Kuźnią Dusz działa osobny warsztat precyzyjnego "
            "rzemiosła. Haldor prowadzi tu zlecenia Kowalstwa i Rzemiosła."
        ),
        "exits": {"south": "forge"},
    }, 'ROOMS', ROOMS, ("crafting_workshop",))

    _catalog_mut.catalog_assign("fishing_school", 'NPCS', NPCS, ("specialist_fishing", "room"))
    _catalog_mut.catalog_assign("miners_guild", 'NPCS', NPCS, ("specialist_mining", "room"))
    _catalog_mut.catalog_assign("forester_lodge", 'NPCS', NPCS, ("specialist_woodcutting", "room"))
    _catalog_mut.catalog_assign("herbalism_garden", 'NPCS', NPCS, ("specialist_herbalism", "room"))
    _catalog_mut.catalog_assign("alchemy_lab", 'NPCS', NPCS, ("specialist_alchemy", "room"))
    _catalog_mut.catalog_assign("crafting_workshop", 'NPCS', NPCS, ("specialist_crafting", "room"))

    # ========================================================
    # DZICZ — NOWY PÓŁNOCNY REGION
    # ========================================================
    _catalog_mut.catalog_assign("wild_frontier", 'ROOMS', ROOMS, ("crossroads", "exits", "north"))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Skraj Północnej Dziczy",
        "desc": (
            "Stary trakt znika pod trawą. Dalej rozchodzą się ścieżki "
            "do zarośli, opuszczonych gospodarstw i obozu łowców."
        ),
        "exits": {
            "south": "crossroads",
            "north": "hunter_clearing",
            "west": "thorn_scrub",
            "east": "abandoned_farm",
        },
    }, 'ROOMS', ROOMS, ("wild_frontier",))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Polana Łowców",
        "desc": (
            "Bezpieczna polana służy jako mały terenowy hub. "
            "Łowcy naprawiają tu sprzęt i obserwują ruch bestii."
        ),
        "exits": {
            "south": "wild_frontier",
            "north": "burnt_fields",
        },
    }, 'ROOMS', ROOMS, ("hunter_clearing",))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Cierniste Zarośla",
        "desc": (
            "Gęste kolczaste krzewy tworzą naturalny labirynt. "
            "Między nimi słychać warczenie dzikich bestii."
        ),
        "exits": {
            "east": "wild_frontier",
            "north": "beast_den",
        },
    }, 'ROOMS', ROOMS, ("thorn_scrub",))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Opuszczona Farma",
        "desc": (
            "Zawalone zabudowania przypominają o dawnych osadnikach. "
            "Ślady zwierząt prowadzą na północ."
        ),
        "exits": {
            "west": "wild_frontier",
            "north": "broken_shrine",
        },
    }, 'ROOMS', ROOMS, ("abandoned_farm",))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Spalone Pola",
        "desc": (
            "Czarna ziemia i zwęglone pnie ciągną się ku kamiennemu "
            "wąwozowi. W popiele żerują agresywne stworzenia."
        ),
        "exits": {
            "south": "hunter_clearing",
            "north": "stone_ravine",
        },
    }, 'ROOMS', ROOMS, ("burnt_fields",))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Kamienny Wąwóz",
        "desc": (
            "Wąwóz przecina północną Dzicz. Boczne przejście prowadzi "
            "do legowiska największej bestii regionu."
        ),
        "exits": {
            "south": "burnt_fields",
            "west": "beast_den",
        },
    }, 'ROOMS', ROOMS, ("stone_ravine",))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Pęknięta Kapliczka",
        "desc": (
            "Dawna kapliczka została rozbita przez korzenie i pazury. "
            "Na zachodzie leży wejście do legowiska bestii."
        ),
        "exits": {
            "south": "abandoned_farm",
            "west": "beast_den",
        },
    }, 'ROOMS', ROOMS, ("broken_shrine",))
    _catalog_mut.catalog_assign({
        "zone": "Dzicz",
        "name": "Legowisko Rogatego Króla",
        "desc": (
            "W skalnej niecce leżą kości i połamane rogi. "
            "To terytorium największego drapieżnika północnej Dziczy."
        ),
        "exits": {
            "south": "thorn_scrub",
            "east": "stone_ravine",
            "north": "broken_shrine",
        },
    }, 'ROOMS', ROOMS, ("beast_den",))

    # ========================================================
    # GÓRY — NIŻSZE STOKI, LÓD, SZCZYT I STARA KOPALNIA
    # ========================================================
    _catalog_mut.catalog_assign("mountain_lower_slopes", 'ROOMS', ROOMS, ("mountain_pass", "exits", "north"))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Niższe Stoki",
        "desc": (
            "Kamienista ścieżka odchodzi od głównej przełęczy. "
            "Wyżej słychać wiatr uderzający o skalne półki."
        ),
        "exits": {
            "south": "mountain_pass",
            "north": "wind_shelf",
            "west": "goat_trail",
        },
    }, 'ROOMS', ROOMS, ("mountain_lower_slopes",))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Szlak Kozic",
        "desc": (
            "Wąska ścieżka prowadzi nad urwiskiem do dawnej "
            "krasnoludzkiej kopalni."
        ),
        "exits": {
            "east": "mountain_lower_slopes",
            "west": "dwarf_mine_entrance",
        },
    }, 'ROOMS', ROOMS, ("goat_trail",))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Wejście do Starej Kopalni Krasnoludów",
        "desc": (
            "Zardzewiała brama stoi otwarta. To opuszczone wyrobisko "
            "jest częścią terenu Gór, a nie Kopalni Głębinowej."
        ),
        "exits": {
            "east": "goat_trail",
            "north": "abandoned_dwarf_hall",
        },
    }, 'ROOMS', ROOMS, ("dwarf_mine_entrance",))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Opuszczona Hala Krasnoludów",
        "desc": (
            "Kamienne filary podtrzymują strop dawnej hali wydobywczej. "
            "Dziś mieszkają tu górskie bestie."
        ),
        "exits": {"south": "dwarf_mine_entrance"},
    }, 'ROOMS', ROOMS, ("abandoned_dwarf_hall",))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Wietrzna Półka",
        "desc": (
            "Silny wiatr niemal zrzuca z wąskiej skalnej półki. "
            "Stąd droga rozdziela się ku lodowej przełęczy i obozowi."
        ),
        "exits": {
            "south": "mountain_lower_slopes",
            "north": "ice_pass",
            "east": "summit_camp",
        },
    }, 'ROOMS', ROOMS, ("wind_shelf",))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Lodowa Przełęcz",
        "desc": (
            "Śnieg skrzypi pod stopami, a oblodzone skały prowadzą "
            "na Szczyt Burzy."
        ),
        "exits": {
            "south": "wind_shelf",
            "north": "storm_summit",
        },
    }, 'ROOMS', ROOMS, ("ice_pass",))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Obóz Szczytowy",
        "desc": (
            "Mały obóz badaczy i zwiadowców osłania kamienny mur. "
            "To bezpieczny hub wysokich Gór."
        ),
        "exits": {
            "west": "wind_shelf",
            "east": "lava_fissure",
            "north": "storm_summit",
        },
    }, 'ROOMS', ROOMS, ("summit_camp",))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Szczelina Lawowa",
        "desc": (
            "Gorące powietrze wydobywa się z głębokiej szczeliny. "
            "Kamienie mają tu czerwony połysk."
        ),
        "exits": {"west": "summit_camp"},
    }, 'ROOMS', ROOMS, ("lava_fissure",))
    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Szczyt Burzy",
        "desc": (
            "Najwyższy punkt szlaku tonie w chmurach i błyskawicach. "
            "Ogromny drapieżnik krąży nad szczytem."
        ),
        "exits": {
            "south": "ice_pass",
            "west": "summit_camp",
        },
    }, 'ROOMS', ROOMS, ("storm_summit",))

    # ========================================================
    # JASKINIA TROLLI — BOCZNE GŁĘBOKIE KOMORY
    # ========================================================
    _catalog_mut.catalog_assign("troll_fungus_cavern", 'ROOMS', ROOMS, ("troll_cave_2", "exits", "north"))
    _catalog_mut.catalog_assign("troll_war_camp", 'ROOMS', ROOMS, ("troll_cave_3", "exits", "south"))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Grota Grzybów",
        "desc": (
            "Olbrzymie blade grzyby rosną na wilgotnej skale. "
            "Ślady trolli prowadzą ku podziemnej rzece."
        ),
        "exits": {
            "south": "troll_cave_2",
            "east": "troll_underground_river",
        },
    }, 'ROOMS', ROOMS, ("troll_fungus_cavern",))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Podziemna Rzeka Trolli",
        "desc": (
            "Ciemna rzeka przecina jaskinię. Prymitywne kładki "
            "prowadzą do sal szamanów i do dołu kości."
        ),
        "exits": {
            "west": "troll_fungus_cavern",
            "north": "troll_shaman_gallery",
            "south": "troll_bone_pit",
        },
    }, 'ROOMS', ROOMS, ("troll_underground_river",))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Galeria Szamanów",
        "desc": (
            "Ściany pokrywają malunki i kościane amulety. "
            "Szamani trolli odprawiają tu rytuały."
        ),
        "exits": {
            "south": "troll_underground_river",
            "east": "troll_nursery",
        },
    }, 'ROOMS', ROOMS, ("troll_shaman_gallery",))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Gniazdo Trolli",
        "desc": (
            "Ciepła komora jest pełna skór, kości i zapasów. "
            "Dalej znajdują się zagrody jeńców."
        ),
        "exits": {
            "west": "troll_shaman_gallery",
            "south": "troll_slave_pens",
        },
    }, 'ROOMS', ROOMS, ("troll_nursery",))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Zagrody Jeńców",
        "desc": (
            "Puste drewniane klatki stoją pod ścianami. "
            "Na wschodzie widać skarbiec plemienia."
        ),
        "exits": {
            "north": "troll_nursery",
            "east": "troll_treasure_vault",
        },
    }, 'ROOMS', ROOMS, ("troll_slave_pens",))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Skarbiec Trolli",
        "desc": (
            "Skrzynie, metal i łupy z karawan leżą w wielkim nieładzie. "
            "Na południu słychać wojenne bębny."
        ),
        "exits": {
            "west": "troll_slave_pens",
            "south": "troll_deep_war_camp",
        },
    }, 'ROOMS', ROOMS, ("troll_treasure_vault",))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Dół Kości",
        "desc": (
            "Głęboka komora jest wypełniona kośćmi zwierząt i wojowników. "
            "Wschodni tunel prowadzi do wojennego obozu."
        ),
        "exits": {
            "north": "troll_underground_river",
            "east": "troll_deep_war_camp",
        },
    }, 'ROOMS', ROOMS, ("troll_bone_pit",))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Głęboki Obóz Wojenny",
        "desc": (
            "Uzbrojone trolle ćwiczą tu przed wyprawami na powierzchnię. "
            "Południowy korytarz prowadzi do pradawnego ołtarza."
        ),
        "exits": {
            "north": "troll_treasure_vault",
            "west": "troll_bone_pit",
            "south": "troll_altar",
        },
    }, 'ROOMS', ROOMS, ("troll_deep_war_camp",))
    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Pradawny Ołtarz Trolli",
        "desc": (
            "Kamienny ołtarz nosi ślady setek rytuałów. "
            "Najpotężniejszy wojownik głębin strzeże tego miejsca."
        ),
        "exits": {"north": "troll_deep_war_camp"},
    }, 'ROOMS', ROOMS, ("troll_altar",))

    # ========================================================
    # BAGNA — NOWY TEREN
    # ========================================================
    _catalog_mut.catalog_assign("swamp_boardwalk", 'ROOMS', ROOMS, ("deep_grove", "exits", "south"))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Groble Czarnego Bagna",
        "desc": (
            "Drewniane pomosty prowadzą nad ciemną wodą. "
            "Na wschodzie znajduje się posterunek łowców bagien."
        ),
        "exits": {
            "north": "deep_grove",
            "south": "reed_mire",
            "east": "swamp_hunter_post",
        },
    }, 'ROOMS', ROOMS, ("swamp_boardwalk",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Posterunek Łowców Bagien",
        "desc": (
            "Sucha platforma służy jako bezpieczny hub wypraw na Bagna."
        ),
        "exits": {"west": "swamp_boardwalk"},
    }, 'ROOMS', ROOMS, ("swamp_hunter_post",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Trzcinowe Mokradła",
        "desc": (
            "Wysokie trzciny zasłaniają ścieżki. Woda sięga do kolan."
        ),
        "exits": {
            "north": "swamp_boardwalk",
            "east": "blackwater_pool",
            "west": "fungal_bog",
            "south": "poison_fen",
        },
    }, 'ROOMS', ROOMS, ("reed_mire",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Czarne Rozlewisko",
        "desc": (
            "Nieruchoma czarna woda odbija tylko fragmenty nieba. "
            "Na wschodzie stoi chata bagiennej zielarki."
        ),
        "exits": {
            "west": "reed_mire",
            "east": "swamp_witch_hut",
            "south": "drowned_ruins",
        },
    }, 'ROOMS', ROOMS, ("blackwater_pool",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Chata Bagiennej Zielarki",
        "desc": (
            "Chata stoi na grubych palach. Suszą się tu zioła "
            "i składniki znajdowane tylko na mokradłach."
        ),
        "exits": {"west": "blackwater_pool"},
    }, 'ROOMS', ROOMS, ("swamp_witch_hut",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Grzybowe Torfowisko",
        "desc": (
            "Mokry torf porastają wielkie grzyby i blade mchy."
        ),
        "exits": {
            "east": "reed_mire",
            "south": "serpent_nest",
        },
    }, 'ROOMS', ROOMS, ("fungal_bog",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Gniazdo Bagiennych Węży",
        "desc": (
            "W korzeniach starych drzew wiją się ślady wielkich gadów."
        ),
        "exits": {"north": "fungal_bog"},
    }, 'ROOMS', ROOMS, ("serpent_nest",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Trujące Mokradło",
        "desc": (
            "Zielonkawa mgła unosi się nad wodą. Kamienna ścieżka "
            "prowadzi do zatopionej kapliczki."
        ),
        "exits": {
            "north": "reed_mire",
            "east": "sunken_swamp_shrine",
        },
    }, 'ROOMS', ROOMS, ("poison_fen",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Zatopiona Kapliczka Bagien",
        "desc": (
            "Połowa starej świątyni zniknęła pod wodą. "
            "Na wschodzie leżą zatopione ruiny."
        ),
        "exits": {
            "west": "poison_fen",
            "east": "drowned_ruins",
        },
    }, 'ROOMS', ROOMS, ("sunken_swamp_shrine",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Zatopione Ruiny",
        "desc": (
            "Kamienne mury wystają z czarnej wody. "
            "Na południu pulsuje serce mokradeł."
        ),
        "exits": {
            "north": "blackwater_pool",
            "west": "sunken_swamp_shrine",
            "south": "bog_heart",
        },
    }, 'ROOMS', ROOMS, ("drowned_ruins",))
    _catalog_mut.catalog_assign({
        "zone": "Bagna",
        "name": "Serce Czarnego Bagna",
        "desc": (
            "Głęboka sadzawka otoczona martwymi drzewami jest legowiskiem "
            "Hydry Czarnego Bagna."
        ),
        "exits": {"north": "drowned_ruins"},
    }, 'ROOMS', ROOMS, ("bog_heart",))

    # Bagna są logicznym wysokopoziomowym terenem Zielarstwa.
    HERBALISM_ROOMS.update({
        "swamp_boardwalk", "reed_mire", "blackwater_pool",
        "swamp_witch_hut", "fungal_bog", "serpent_nest",
        "poison_fen", "sunken_swamp_shrine", "drowned_ruins",
    })

    # ========================================================
    # PUSTYNIA — NOWY TEREN
    # ========================================================
    _catalog_mut.catalog_assign("dry_canyon", 'ROOMS', ROOMS, ("ruined_watchtower", "exits", "north"))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Suchy Kanion",
        "desc": (
            "Kamienny kanion prowadzi z zielonych ziem ku pustyni."
        ),
        "exits": {
            "south": "ruined_watchtower",
            "north": "desert_gate",
        },
    }, 'ROOMS', ROOMS, ("dry_canyon",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Brama Pustyni",
        "desc": (
            "Dwa kamienne filary oznaczają początek Wielkiej Pustyni. "
            "Na wschodzie stoi obóz karawan."
        ),
        "exits": {
            "south": "dry_canyon",
            "north": "desert_dunes",
            "east": "caravan_camp",
        },
    }, 'ROOMS', ROOMS, ("desert_gate",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Obóz Karawan",
        "desc": (
            "Namioty, studnia i zwierzęta juczne tworzą bezpieczny "
            "hub podróżników."
        ),
        "exits": {
            "west": "desert_gate",
            "east": "desert_oasis",
        },
    }, 'ROOMS', ROOMS, ("caravan_camp",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Oaza Siedmiu Palm",
        "desc": (
            "Źródło i palmy dają chwilę odpoczynku. "
            "Na północy zaczynają się piaskowcowe ruiny."
        ),
        "exits": {
            "west": "caravan_camp",
            "north": "sandstone_ruins",
        },
    }, 'ROOMS', ROOMS, ("desert_oasis",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Morze Wydm",
        "desc": (
            "Wydmy ciągną się aż po horyzont. "
            "Na zachodzie leży Kotlina Skorpionów."
        ),
        "exits": {
            "south": "desert_gate",
            "north": "glass_flats",
            "west": "scorpion_basin",
        },
    }, 'ROOMS', ROOMS, ("desert_dunes",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Kotlina Skorpionów",
        "desc": (
            "Kamienista niecka jest pełna nor wielkich pustynnych skorpionów."
        ),
        "exits": {"east": "desert_dunes"},
    }, 'ROOMS', ROOMS, ("scorpion_basin",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Szklane Równiny",
        "desc": (
            "Piasek stopił się kiedyś w czarne szkło. "
            "Wschodni szlak prowadzi do Świątyni Słońca."
        ),
        "exits": {
            "south": "desert_dunes",
            "east": "sun_temple",
        },
    }, 'ROOMS', ROOMS, ("glass_flats",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Piaskowcowe Ruiny",
        "desc": (
            "Ruiny dawnego miasta otaczają zejście do zasypanej świątyni."
        ),
        "exits": {
            "south": "desert_oasis",
            "north": "buried_temple",
        },
    }, 'ROOMS', ROOMS, ("sandstone_ruins",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Zasypana Świątynia",
        "desc": (
            "Piasek wdziera się przez pęknięty strop. "
            "Na północy znajduje się główne sanktuarium."
        ),
        "exits": {
            "south": "sandstone_ruins",
            "north": "sun_temple",
        },
    }, 'ROOMS', ROOMS, ("buried_temple",))
    _catalog_mut.catalog_assign({
        "zone": "Pustynia",
        "name": "Świątynia Płonącego Słońca",
        "desc": (
            "Złote symbole świecą na ścianach. "
            "Pradawny Strażnik Słońca nie opuszcza sanktuarium."
        ),
        "exits": {
            "south": "buried_temple",
            "west": "glass_flats",
        },
    }, 'ROOMS', ROOMS, ("sun_temple",))

    # ========================================================
    # NOWE NPC — KAŻDY W LOGICZNYM HUBIE
    # ========================================================
    _catalog_mut.catalog_assign({
        "name": "Łowczyni Elda",
        "room": "hunter_clearing",
        "dialogue": (
            "Północna Dzicz robi się coraz bardziej niebezpieczna. "
            "Potrzebuję kogoś do ograniczenia liczby bestii."
        ),
        "quest": "wild_frontier_hunt",
    }, 'NPCS', NPCS, ("wild_ranger_elda",))
    _catalog_mut.catalog_assign({
        "name": "Kartograf Ivo",
        "room": "hunter_clearing",
        "dialogue": (
            "Rysuję nowe ścieżki Dziczy. Polana jest naszym punktem "
            "orientacyjnym, a Legowisko Rogatego Króla końcem szlaku."
        ),
        "quest": None,
    }, 'NPCS', NPCS, ("wild_cartographer_ivo",))
    _catalog_mut.catalog_assign({
        "name": "Zwiadowca Harek",
        "room": "summit_camp",
        "dialogue": (
            "Wysokie stoki pełne są drapieżników. "
            "Oczyść szlak między obozem a Szczytem Burzy."
        ),
        "quest": "high_mountain_patrol",
    }, 'NPCS', NPCS, ("mountain_scout_harek",))
    _catalog_mut.catalog_assign({
        "name": "Badaczka Trolli Yorna",
        "room": "troll_fungus_cavern",
        "dialogue": (
            "Głębsze komory są częścią całej osady trolli, "
            "nie tylko drogą do Króla. Zbadaj i oczyść ich wojenny szlak."
        ),
        "quest": "deep_troll_clearance",
    }, 'NPCS', NPCS, ("troll_scholar_yorna",))
    _catalog_mut.catalog_assign({
        "name": "Łowca Bagien Varg",
        "room": "swamp_hunter_post",
        "dialogue": (
            "Mokradła są pełne gadów i stworzeń z czarnej wody. "
            "Trzymaj się pomostów, dopóki nie poznasz terenu."
        ),
        "quest": "swamp_purge",
    }, 'NPCS', NPCS, ("swamp_hunter_varg",))
    _catalog_mut.catalog_assign({
        "name": "Bagienna Zielarka Nela",
        "room": "swamp_witch_hut",
        "dialogue": (
            "Na bagnach rosną najmocniejsze zioła Dziczy. "
            "Możesz tu korzystać z Zielarstwa, ale uważaj na bestie."
        ),
        "quest": None,
    }, 'NPCS', NPCS, ("swamp_herbalist_nela",))
    _catalog_mut.catalog_assign({
        "name": "Mistrz Karawan Samir",
        "room": "caravan_camp",
        "dialogue": (
            "Karawany tracą ludzi na wydmach. Oczyść szlak między "
            "Bramą Pustyni, oazą i ruinami."
        ),
        "quest": "desert_patrol",
    }, 'NPCS', NPCS, ("caravan_master_samir",))
    _catalog_mut.catalog_assign({
        "name": "Badaczka Amina",
        "room": "sandstone_ruins",
        "dialogue": (
            "Te ruiny są starsze niż Miasto Dusz. "
            "Świątynia Słońca na północy wciąż jest aktywna."
        ),
        "quest": None,
    }, 'NPCS', NPCS, ("desert_scholar_amina",))

    # ========================================================
    # QUESTY TERENOWE
    # ========================================================
    _catalog_mut.catalog_assign({
        "name": "Bestie Północnej Dziczy",
        "giver": "Łowczyni Elda",
        "kind": "kill",
        "target": "world_exp_wild_beast",
        "needed": 12,
        "description": (
            "Pokonaj 12 bestii Północnej Dziczy i wróć do Eldy."
        ),
        "reward_stat_progress": 320,
        "reward_silver": 850,
        "reward_gold": 2,
        "reward_mithril": 0,
        "reward_items": {"healing_potion": 3},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }, 'QUESTS', QUESTS, ("wild_frontier_hunt",))
    _catalog_mut.catalog_assign({
        "name": "Patrol Wysokich Gór",
        "giver": "Zwiadowca Harek",
        "kind": "kill",
        "target": "world_exp_mountain_threat",
        "needed": 10,
        "description": (
            "Pokonaj 10 stworzeń na wysokich stokach i wróć do Harka."
        ),
        "reward_stat_progress": 430,
        "reward_silver": 1100,
        "reward_gold": 3,
        "reward_mithril": 0,
        "reward_items": {"greater_healing_potion": 2},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }, 'QUESTS', QUESTS, ("high_mountain_patrol",))
    _catalog_mut.catalog_assign({
        "name": "Wojenny Szlak Trolli",
        "giver": "Badaczka Trolli Yorna",
        "kind": "kill",
        "target": "world_exp_troll_depths",
        "needed": 12,
        "description": (
            "Pokonaj 12 trolli z głębokich komór i wróć do Yorny."
        ),
        "reward_stat_progress": 500,
        "reward_silver": 1350,
        "reward_gold": 4,
        "reward_mithril": 0,
        "reward_items": {"soul_shard": 2},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }, 'QUESTS', QUESTS, ("deep_troll_clearance",))
    _catalog_mut.catalog_assign({
        "name": "Oczyszczanie Czarnego Bagna",
        "giver": "Łowca Bagien Varg",
        "kind": "kill",
        "target": "world_exp_swamp_threat",
        "needed": 12,
        "description": (
            "Pokonaj 12 stworzeń Czarnego Bagna i wróć do Varga."
        ),
        "reward_stat_progress": 560,
        "reward_silver": 1600,
        "reward_gold": 5,
        "reward_mithril": 0,
        "reward_items": {"greater_healing_potion": 2},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }, 'QUESTS', QUESTS, ("swamp_purge",))
    _catalog_mut.catalog_assign({
        "name": "Bezpieczny Szlak Karawan",
        "giver": "Mistrz Karawan Samir",
        "kind": "kill",
        "target": "world_exp_desert_threat",
        "needed": 12,
        "description": (
            "Pokonaj 12 zagrożeń Wielkiej Pustyni i wróć do Samira."
        ),
        "reward_stat_progress": 680,
        "reward_silver": 1900,
        "reward_gold": 6,
        "reward_mithril": 0,
        "reward_items": {"soul_elixir": 1},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }, 'QUESTS', QUESTS, ("desert_patrol",))

    # ========================================================
    # MOBY I BOSSOWIE NOWYCH TERENÓW
    # max_hp jest bazowe; globalne x2 zostanie nałożone później.
    # ========================================================
    expansion_mobs = {
        "wild_thorn_wolf": {
            "name": "Wilk Cierniowy",
            "max_hp": 150, "damage": 14, "damage_type": "physical",
            "silver": 45, "gold": 0, "mithril": 0,
            "stat_reward": 55, "class_xp_reward": 850, "soul_reward": 180,
            "drops": {"healing_potion": 0.06},
            "quest_target": "world_exp_wild_beast",
        },
        "wild_ash_boar": {
            "name": "Popielny Dzik",
            "max_hp": 190, "damage": 17, "damage_type": "physical",
            "silver": 55, "gold": 0, "mithril": 0,
            "stat_reward": 65, "class_xp_reward": 980, "soul_reward": 215,
            "drops": {"iron_ore": 0.08},
            "quest_target": "world_exp_wild_beast",
        },
        "wild_horned_king": {
            "name": "Rogaty Król Dziczy",
            "max_hp": 1500, "damage": 32, "damage_type": "physical",
            "silver": 600, "gold": 2, "mithril": 0,
            "stat_reward": 260, "class_xp_reward": 4800, "soul_reward": 1100,
            "drops": {"soul_shard": 0.55},
            "quest_target": "world_exp_wild_beast",
            "world_boss": True,
        },
        "mountain_harpy": {
            "name": "Harpia Szczytowa", "flying": True,
            "max_hp": 300, "damage": 25, "damage_type": "physical",
            "silver": 90, "gold": 1, "mithril": 0,
            "stat_reward": 90, "class_xp_reward": 1550, "soul_reward": 390,
            "drops": {"silver_ore": 0.08},
            "quest_target": "world_exp_mountain_threat",
        },
        "mountain_ice_wolf": {
            "name": "Lodowy Wilk",
            "max_hp": 360, "damage": 29, "damage_type": "magic",
            "silver": 105, "gold": 1, "mithril": 0,
            "stat_reward": 100, "class_xp_reward": 1750, "soul_reward": 430,
            "drops": {"gold_ore": 0.05},
            "quest_target": "world_exp_mountain_threat",
        },
        "mountain_stone_ram": {
            "name": "Kamienny Tryk",
            "max_hp": 430, "damage": 31, "damage_type": "physical",
            "silver": 115, "gold": 1, "mithril": 0,
            "stat_reward": 110, "class_xp_reward": 1950, "soul_reward": 470,
            "drops": {"cobalt_ore": 0.04},
            "quest_target": "world_exp_mountain_threat",
        },
        "mountain_storm_eagle": {
            "name": "Orzeł Burzy", "flying": True,
            "max_hp": 3200, "damage": 55, "damage_type": "magic",
            "silver": 1200, "gold": 5, "mithril": 0,
            "stat_reward": 480, "class_xp_reward": 9000, "soul_reward": 2400,
            "drops": {"soul_elixir": 0.25, "astral_ore": 0.08},
            "quest_target": "world_exp_mountain_threat",
            "world_boss": True,
        },
        "deep_troll_warrior": {
            "name": "Troll Wojenny",
            "max_hp": 480, "damage": 34, "damage_type": "physical",
            "silver": 125, "gold": 1, "mithril": 0,
            "stat_reward": 120, "class_xp_reward": 2200, "soul_reward": 520,
            "drops": {"iron_ore": 0.10},
            "quest_target": "mountain_troll",
            "quest_targets": ("world_exp_troll_depths",),
        },
        "deep_troll_shaman": {
            "name": "Szaman Głębin Trolli",
            "mob_aliases": ("Troll Szaman Głębin",),
            "max_hp": 420, "damage": 37, "damage_type": "magic",
            "silver": 140, "gold": 1, "mithril": 0,
            "stat_reward": 130, "class_xp_reward": 2450, "soul_reward": 570,
            "drops": {"soul_shard": 0.14},
            "quest_target": "mountain_troll",
            "quest_targets": ("world_exp_troll_depths",),
        },
        "deep_troll_warlord": {
            "name": "Wódz Głębin Urrak",
            "max_hp": 4200, "damage": 62, "damage_type": "physical",
            "silver": 1500, "gold": 6, "mithril": 0,
            "stat_reward": 540, "class_xp_reward": 10500, "soul_reward": 2800,
            "drops": {"soul_shard": 0.80, "soul_elixir": 0.20},
            "quest_target": "mountain_troll",
            "quest_targets": ("world_exp_troll_depths",),
            "world_boss": True,
        },
        "swamp_crawler": {
            "name": "Pełzacz Bagienny",
            "max_hp": 380, "damage": 30, "damage_type": "physical",
            "silver": 110, "gold": 1, "mithril": 0,
            "stat_reward": 115, "class_xp_reward": 2100, "soul_reward": 500,
            "drops": {"nightshade": 0.10},
            "quest_target": "world_exp_swamp_threat",
        },
        "swamp_serpent": {
            "name": "Wąż Czarnej Wody",
            "max_hp": 460, "damage": 35, "damage_type": "physical",
            "silver": 130, "gold": 1, "mithril": 0,
            "stat_reward": 130, "class_xp_reward": 2400, "soul_reward": 580,
            "drops": {"mandrake": 0.10},
            "quest_target": "world_exp_swamp_threat",
        },
        "swamp_mire_witch": {
            "name": "Wiedźma Mokradła",
            "max_hp": 520, "damage": 40, "damage_type": "magic",
            "silver": 155, "gold": 1, "mithril": 0,
            "stat_reward": 145, "class_xp_reward": 2750, "soul_reward": 650,
            "drops": {"moonflower": 0.10},
            "quest_target": "world_exp_swamp_threat",
        },
        "swamp_hydra": {
            "name": "Hydra Czarnego Bagna",
            "max_hp": 5200, "damage": 70, "damage_type": "physical",
            "silver": 1800, "gold": 7, "mithril": 0,
            "stat_reward": 620, "class_xp_reward": 12500, "soul_reward": 3400,
            "drops": {"soul_elixir": 0.30, "astral_lotus": 0.15},
            "quest_target": "world_exp_swamp_threat",
            "world_boss": True,
        },
        "desert_raider": {
            "name": "Pustynny Łupieżca",
            "max_hp": 520, "damage": 40, "damage_type": "physical",
            "silver": 170, "gold": 1, "mithril": 0,
            "stat_reward": 150, "class_xp_reward": 2900, "soul_reward": 700,
            "drops": {"gold_ore": 0.08},
            "quest_target": "world_exp_desert_threat",
        },
        "dune_scorpion": {
            "name": "Olbrzymi Skorpion Wydm",
            "max_hp": 610, "damage": 44, "damage_type": "physical",
            "silver": 185, "gold": 1, "mithril": 0,
            "stat_reward": 165, "class_xp_reward": 3200, "soul_reward": 780,
            "drops": {"void_ore": 0.03},
            "quest_target": "world_exp_desert_threat",
        },
        "sand_wraith": {
            "name": "Piaskowy Upiór",
            "max_hp": 560, "damage": 47, "damage_type": "magic",
            "silver": 200, "gold": 2, "mithril": 0,
            "stat_reward": 175, "class_xp_reward": 3450, "soul_reward": 830,
            "drops": {"soul_shard": 0.18},
            "quest_target": "world_exp_desert_threat",
        },
        "sun_guardian": {
            "name": "Pradawny Strażnik Słońca",
            "max_hp": 6800, "damage": 82, "damage_type": "magic",
            "silver": 2400, "gold": 9, "mithril": 0,
            "stat_reward": 760, "class_xp_reward": 15000, "soul_reward": 4200,
            "drops": {"soul_elixir": 0.35, "eternium_ore": 0.05},
            "quest_target": "world_exp_desert_threat",
            "world_boss": True,
        },
    }

    for mob_id, template in expansion_mobs.items():
        template.setdefault("corpse_equipment_pool", [
            "iron_guard", "iron_gauntlets", "forge_charm"
        ])
        template.setdefault("corpse_equipment_guaranteed", 1)
        _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (mob_id,))

    MOB_SPAWNS.extend([
        # Dzicz
        ("wild_frontier", "wild_thorn_wolf"),
        ("thorn_scrub", "wild_thorn_wolf"),
        ("thorn_scrub", "wild_ash_boar"),
        ("abandoned_farm", "wild_ash_boar"),
        ("burnt_fields", "wild_ash_boar"),
        ("stone_ravine", "wild_thorn_wolf"),
        ("broken_shrine", "wild_ash_boar"),
        ("beast_den", "wild_horned_king"),

        # Góry
        ("mountain_lower_slopes", "mountain_stone_ram"),
        ("goat_trail", "mountain_stone_ram"),
        ("abandoned_dwarf_hall", "mountain_ice_wolf"),
        ("wind_shelf", "mountain_harpy"),
        ("ice_pass", "mountain_ice_wolf"),
        ("lava_fissure", "mountain_stone_ram"),
        ("storm_summit", "mountain_storm_eagle"),

        # Jaskinia Trolli
        ("troll_fungus_cavern", "deep_troll_warrior"),
        ("troll_underground_river", "deep_troll_warrior"),
        ("troll_shaman_gallery", "deep_troll_shaman"),
        ("troll_nursery", "deep_troll_warrior"),
        ("troll_slave_pens", "deep_troll_warrior"),
        ("troll_treasure_vault", "deep_troll_shaman"),
        ("troll_bone_pit", "deep_troll_warrior"),
        ("troll_deep_war_camp", "deep_troll_warrior"),
        ("troll_deep_war_camp", "deep_troll_shaman"),
        ("troll_altar", "deep_troll_warlord"),

        # Bagna
        ("reed_mire", "swamp_crawler"),
        ("blackwater_pool", "swamp_serpent"),
        ("fungal_bog", "swamp_crawler"),
        ("serpent_nest", "swamp_serpent"),
        ("poison_fen", "swamp_mire_witch"),
        ("sunken_swamp_shrine", "swamp_mire_witch"),
        ("drowned_ruins", "swamp_crawler"),
        ("bog_heart", "swamp_hydra"),

        # Pustynia
        ("desert_gate", "desert_raider"),
        ("desert_dunes", "dune_scorpion"),
        ("scorpion_basin", "dune_scorpion"),
        ("glass_flats", "sand_wraith"),
        ("sandstone_ruins", "desert_raider"),
        ("buried_temple", "sand_wraith"),
        ("sun_temple", "sun_guardian"),
    ])

    # ========================================================
    # GUIDE / NPC ALIASES
    # ========================================================
    
    # ========================================================
    # EXPOWISKA
    # ========================================================
    for area in EXP_AREAS:
        if area["id"] == "dzicz":
            area["soul_max"] = 65
            area["description"] = (
                "Dzicz obejmuje teraz także Północną Dzicz, "
                "Cierniste Zarośla, Spalone Pola, Kamienny Wąwóz "
                "i Legowisko Rogatego Króla."
            )
        elif area["id"] == "trolle":
            area["soul_max"] = 120
            area["description"] = (
                "Góry obejmują Niższe Stoki, starą kopalnię krasnoludów, "
                "Lodową Przełęcz i Szczyt Burzy. Jaskinia Trolli ma teraz "
                "rozbudowane głębokie komory i wojenny obóz."
            )

    EXP_AREAS = EXP_AREAS + (
        {
            "id": "bagna",
            "name": "Czarne Bagna",
            "aliases": (
                "bagna", "czarne bagno", "mokradla", "mokradła",
                "hydra",
            ),
            "soul_min": 40,
            "soul_max": 100,
            "difficulty": "średnia do trudnej",
            "guide": "bagna",
            "enemies": (
                "Pełzacze Bagienne, Węże Czarnej Wody, "
                "Wiedźmy Mokradła i Hydra Czarnego Bagna"
            ),
            "description": (
                "Rozległy teren mokradeł z hubem łowców, "
                "Zielarstwem i bossem świata na końcu."
            ),
            "note": (
                "Bagna są dobrym terenem dla Zielarstwa, ale głębsze "
                "lokacje są znacznie groźniejsze od wejścia."
            ),
        },
        {
            "id": "pustynia",
            "name": "Wielka Pustynia",
            "aliases": (
                "pustynia", "wydmy", "karawany", "swiatynia slonca",
                "świątynia słońca",
            ),
            "soul_min": 70,
            "soul_max": 140,
            "difficulty": "trudna",
            "guide": "pustynia",
            "enemies": (
                "Pustynni Łupieżcy, Olbrzymie Skorpiony Wydm, "
                "Piaskowe Upiory i Pradawny Strażnik Słońca"
            ),
            "description": (
                "Duży region z obozem karawan, oazą, ruinami, "
                "Zasypaną Świątynią i bossem świata."
            ),
            "note": (
                "Obóz Karawan jest głównym bezpiecznym hubem Pustyni."
            ),
        },
    )

    # ========================================================
    # HELP
    # ========================================================
    HELP_TOPICS["world_expansion_i"] = [
        "World Expansion I rozbudowuje Dzicz, Góry i Jaskinię Trolli oraz dodaje Bagna i Pustynię.",
        "Dodano ponad 40 nowych lokacji i kilka nowych terenowych hubów.",
        "Północna Dzicz zaczyna się na północ od Rozdroża.",
        "Wysokie Góry odchodzą na północ od Górskiej Przełęczy.",
        "Głębokie komory Jaskini Trolli odchodzą od istniejących tuneli.",
        "Czarne Bagna zaczynają się na południe od Głębi Gaju.",
        "Wielka Pustynia zaczyna się na północ od Ruin Strażnicy.",
        "Nowe tereny mają własne moby, bossów świata, NPC i questy.",
        "Specjaliści profesji zostali rozdzieleni do osobnych logicznych pomieszczeń.",
        "Neris: Szkoła Wędkarstwa.",
        "Kordan: Gildia Górników.",
        "Oren: Leśniczówka.",
        "Sena: Ogród Zielarski.",
        "Orin: Laboratorium Alchemiczne.",
        "Haldor: Warsztat Rzemieślniczy.",
        "Sprzedawcy podstawowych narzędzi pozostają w swoich dotychczasowych miejscach.",
        "Kilof nadal sprzedaje wyłącznie Górnik Toren.",
        "Komendy prowadz i expowiska obejmują nowe regiony.",
    ]


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


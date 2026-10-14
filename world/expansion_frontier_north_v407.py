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

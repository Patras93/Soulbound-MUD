from data import catalog_mutations as _catalog_mut
from core.command_catalog import CommandAliasMap
from config.command_aliases import COMMAND_ALIAS_DEFINITIONS
from config.postal import GUIDE_CITY_HUBS_V0522

def build_mine_depth_rooms():
    _catalog_mut.catalog_assign(mine_floor_id(1), 'ROOMS', ROOMS, ("crystal_chamber", "exits", "down"))

    for floor in range(MINE_MIN_FLOOR, MINE_MAX_FLOOR + 1):
        exits = {
            "up": (
                "crystal_chamber"
                if floor == MINE_MIN_FLOOR
                else mine_floor_id(floor - 1)
            )
        }
        if floor < MINE_MAX_FLOOR:
            exits["down"] = mine_floor_id(floor + 1)

        if floor < 10:
            band = "kamień i miedź"
        elif floor < 25:
            band = "miedź i żelazo"
        elif floor < 50:
            band = "żelazo i srebro"
        elif floor < 100:
            band = "srebro i złoto"
        elif floor < 120:
            band = "złoto i kobalt"
        elif floor < 140:
            band = "kobalt i Kamień Runiczny"
        elif floor < 160:
            band = "Kamień Runiczny i Smocza Stal"
        elif floor < 180:
            band = "Smocza Stal i Ruda Astralna"
        elif floor < 200:
            band = "Ruda Astralna i Ruda Pustki"
        else:
            band = "Ruda Pustki i Eternium"

        wall_text = " Niżej znajduje się ściana do przebicia Kilofem."
        _catalog_mut.catalog_assign({
            "zone": "Kopalnia Głębinowa",
            "name": f"Kopalnia - poziom {floor}",
            "desc": (
                f"Poziom {floor}. Pierwsze 200 poziomów to ręcznie przygotowana część Kopalni. "
                f"Najczęstsze złoża: {band}." + wall_text
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (mine_floor_id(floor),))

build_mine_depth_rooms()

_catalog_mut.catalog_assign({
    "zone": "Miasto Dusz",
    "name": "Pracownia Jubilerska",
    "desc": (
        "Jasna pracownia pełna drobnych narzędzi, metalowych opraw "
        "i stołów do wykonywania pierścieni oraz naszyjników. "
        "Pracuje tutaj Jubilerka Mirella."
    ),
    "exits": {"down": "market"},
}, 'ROOMS', ROOMS, ("jeweler_workshop",))
_catalog_mut.catalog_assign("jeweler_workshop", 'ROOMS', ROOMS, ("market", "exits", "up"))

DIRECTION_ALIASES = {
    "n": "north", "north": "north", "północ": "north", "polnoc": "north",
    "s": "south", "south": "south", "południe": "south", "poludnie": "south",
    "e": "east", "east": "east", "wschód": "east", "wschod": "east",
    "w": "west", "west": "west", "zachód": "west", "zachod": "west",
    "ne": "northeast", "northeast": "northeast", "pnw": "northeast", "północnywschód": "northeast", "polnocnywschod": "northeast",
    "se": "southeast", "southeast": "southeast", "pdw": "southeast", "południowywschód": "southeast", "poludniowywschod": "southeast",
    "sw": "southwest", "southwest": "southwest", "pdz": "southwest", "południowyzachód": "southwest", "poludniowyzachod": "southwest",
    "nw": "northwest", "northwest": "northwest", "pnz": "northwest", "północnyzachód": "northwest", "polnocnyzachod": "northwest",
    "u": "up", "up": "up", "góra": "up", "gora": "up",
    "d": "down", "down": "down", "dół": "down", "dol": "down",
}

# v0.8.56: ruch między lokacjami jest krótkim marszem zamiast natychmiastowego
# przestawienia room_id. Opóźnienie jest celowo niewielkie, żeby NVDA zdążył
# przeczytać kierunek, ale nawigacja po dużym świecie nadal była wygodna.
DIRECTION_WALK_LABELS = {
    "north": "na północ",
    "south": "na południe",
    "east": "na wschód",
    "west": "na zachód",
    "northeast": "na północny wschód",
    "southeast": "na południowy wschód",
    "southwest": "na południowy zachód",
    "northwest": "na północny zachód",
    "up": "w górę",
    "down": "w dół",
}
WALK_STEP_DELAY = float(os.getenv("SOULBOUND_WALK_STEP_DELAY", "0.70"))
GUIDE_STEP_DELAY = float(os.getenv("SOULBOUND_GUIDE_STEP_DELAY", "0.35"))

GUIDE_DESTINATION_ALIASES = {
    # MIASTO, NPC I POZOSTALE CELE
    'ira': 'alpine_herbalist_hut',
    'zielarka alpejska': 'alpine_herbalist_hut',
    'bandyci': 'bandit_camp',
    'bandits': 'bandit_camp',
    'bandit camp': 'bandit_camp',
    'bandit camps': 'bandit_camp',
    'herszt': 'bandit_camp',
    'oboz bandytow': 'bandit_camp',
    'obozowisko bandytow': 'bandit_camp',
    'mistrz karawan': 'caravan_camp',
    'oboz karawan': 'caravan_camp',
    'samir': 'caravan_camp',
    'krysztalowy tunel': 'cave_tunnel',
    'tunel': 'cave_tunnel',
    'laka rumianku': 'chamomile_meadow',
    'rozdroze': 'crossroads',
    'komnata krysztalowa': 'crystal_chamber',
    'krysztal': 'crystal_chamber',
    'krysztalowa komnata': 'crystal_chamber',
    'glebia gaju': 'deep_grove',
    'stara kopalnia krasnoludow': 'dwarf_mine_entrance',
    'kwiatowa laka': 'flower_meadow',
    'laka kwiatow': 'flower_meadow',
    'anna': 'frontier_watchpost',
    'strazniczka anna': 'frontier_watchpost',
    'wartownia pogranicza': 'frontier_watchpost',
    'laka zen szenia': 'ginseng_meadow',
    'laka zenszenia': 'ginseng_meadow',
    'szlak kozic': 'goat_trail',
    'gobliny': 'goblin_camp',
    'goblins': 'goblin_camp',
    'goblin camp': 'goblin_camp',
    'jaskinia goblinow': 'goblin_cave_mouth',
    'jaskinie goblinow': 'goblin_cave_mouth',
    'goblin cave': 'goblin_cave_mouth',
    'goblin caves': 'goblin_cave_mouth',
    'oboz goblinow': 'goblin_camp',
    'cmentarz': 'graveyard',
    'stary cmentarz': 'graveyard',
    'arven': 'guard_hall',
    'kapitan arven': 'guard_hall',
    'straznica': 'guard_hall',
    'harbor': 'harbor',
    'port': 'harbor',
    'port dusz': 'harbor',
    'lak zielarskich': 'herb_meadow_hub',
    'laki zielarskie': 'herb_meadow_hub',
    'chata zielarki': 'herbalist_hut',
    'liora': 'herbalist_hut',
    'zielarka liora': 'herbalist_hut',
    'kamienne znaki': 'hill',
    'wzgorze': 'hill',
    'elda': 'hunter_clearing',
    'lowczyni elda': 'hunter_clearing',
    'polana lowcow': 'hunter_clearing',
    'chata lowcy': 'hunter_lodge',
    'lowca potworow': 'hunter_lodge',
    'ragna': 'hunter_lodge',
    'elia': 'inn',
    'gospoda': 'inn',
    'karczma': 'inn',
    'karczmarka elia': 'inn',
    'kucharz': 'inn',
    'specjalista gotowania': 'inn',
    'brzeg jeziora': 'lake_shore',
    'jezioro': 'lake_shore',
    'laka nadjeziorna': 'lakeside_meadow',
    'nadjeziorna laka': 'lakeside_meadow',
    'laka lawendy': 'lavender_meadow',
    'laka melisy': 'lemon_balm_meadow',
    'archiwista sol': 'library',
    'archiwum': 'library',
    'biblioteka': 'library',
    'sol': 'library',
    'aldren': 'market',
    'bank': 'market',
    'bank dusz': 'market',
    'bankier': 'market',
    'bankier aldren': 'market',
    'market': 'market',
    'rynek': 'market',
    'targ': 'market',
    'laka': 'meadow',
    'laki': 'meadow',
    'srebrna laka': 'meadow',
    'laka miety': 'mint_meadow',
    'mietowa laka': 'mint_meadow',
    'laka ksiezycowego kwiatu': 'moonflower_meadow',
    'laka pokrzywy': 'nettle_meadow',
    'brama polnocna': 'north_gate',
    'polnocna brama': 'north_gate',
    'dowodca roderik': 'north_watchpost',
    'roderik': 'north_watchpost',
    'wartownia polnocna': 'north_watchpost',
    'ocean': 'ocean_platform',
    'platforma': 'ocean_platform',
    'platforma oceaniczna': 'ocean_platform',
    'stary trakt': 'old_road',
    'trakt': 'old_road',
    'brzeg rzeki': 'riverbank',
    'rzeka': 'riverbank',
    'ruiny': 'ruined_watchtower',
    'ruiny straznicy': 'ruined_watchtower',
    'ruiny strażnicy': 'ruined_watchtower',
    'stara straznica': 'ruined_watchtower',
    'stara strażnica': 'ruined_watchtower',
    'laka szalwii': 'sage_meadow',
    'amina': 'sandstone_ruins',
    'badaczka amina': 'sandstone_ruins',
    'molo': 'sea_pier',
    'morskie molo': 'sea_pier',
    'kapliczka': 'shrine',
    'zapomniana kapliczka': 'shrine',
    'brama poludniowa': 'south_gate',
    'poludniowa brama': 'south_gate',
    'centrum': 'square',
    'plac': 'square',
    'plac dusz': 'square',
    'kamienny most': 'stone_bridge',
    'most': 'stone_bridge',
    'harek': 'summit_camp',
    'oboz szczytowy': 'summit_camp',
    'zwiadowca harek': 'summit_camp',
    'elor': 'temple',
    'kaplan elor': 'temple',
    'swiatynia': 'temple',
    'swiatynia odrodzenia': 'temple',
    'piwnica': 'temple_basement',
    'piwnica swiatyni': 'temple_basement',
    'dziedziniec': 'training',
    'plac treningowy': 'training',
    'manekin': 'training',
    'manekiny': 'training',
    'trening': 'training',
    'oltar trolli': 'troll_altar',
    'gleboki oboz wojenny': 'troll_deep_war_camp',
    'badaczka trolli': 'troll_fungus_cavern',
    'grota grzybow': 'troll_fungus_cavern',
    'yorna': 'troll_fungus_cavern',
    'laka waleriany': 'valerian_meadow',
    'gaj': 'whisper_grove',
    'gaj szeptow': 'whisper_grove',
    'mira': 'whisper_grove',
    'zielarka mira': 'whisper_grove',
    'laka krwawnika': 'yarrow_meadow',

    # GILDIA DUSZ I NAUCZYCIELE
    'arkany': 'guild_arcane_chamber',
    'magowie': 'guild_arcane_chamber',
    'psionicy': 'guild_arcane_chamber',
    'sklep maga': 'guild_arcane_chamber',
    'sklep psionika': 'guild_arcane_chamber',
    'berserker hall': 'guild_berserker_chamber',
    'brynja': 'guild_berserker_chamber',
    'sala berserkera': 'guild_berserker_chamber',
    'mnisi': 'guild_body_hall',
    'sala dyscypliny': 'guild_body_hall',
    'sklep mnicha': 'guild_body_hall',
    'sklep straznika': 'guild_body_hall',
    'sklep strażnika': 'guild_body_hall',
    'straznicy': 'guild_body_hall',
    'czarownicy': 'guild_dark_chamber',
    'mroczne sztuki': 'guild_dark_chamber',
    'nekromanci': 'guild_dark_chamber',
    'sklep czarownika': 'guild_dark_chamber',
    'sklep nekromanty': 'guild_dark_chamber',
    'druid grove': 'guild_druid_chamber',
    'gaj druida': 'guild_druid_chamber',
    'thalen': 'guild_druid_chamber',
    'bastion straznika': 'guild_guardian_chamber',
    'borin': 'guild_guardian_chamber',
    'guardian hall': 'guild_guardian_chamber',
    'gildia': 'guild_hall',
    'sala gildii': 'guild_hall',
    'eira': 'guild_hunter_chamber',
    'hunter hall': 'guild_hunter_chamber',
    'sala lowcy': 'guild_hunter_chamber',
    'komnata maga': 'guild_mage_chamber',
    'mage chamber': 'guild_mage_chamber',
    'vaelis': 'guild_mage_chamber',
    'berserkerzy': 'guild_martial_hall',
    'sala oreza': 'guild_martial_hall',
    'sklep berserkera': 'guild_martial_hall',
    'sklep wojownika': 'guild_martial_hall',
    'wojownicy': 'guild_martial_hall',
    'monk hall': 'guild_monk_chamber',
    'sala mnicha': 'guild_monk_chamber',
    'shen': 'guild_monk_chamber',
    'komnata nekromanty': 'guild_necromancer_chamber',
    'morwen': 'guild_necromancer_chamber',
    'necromancer chamber': 'guild_necromancer_chamber',
    'aureon': 'guild_priest_chamber',
    'kaplica kaplana': 'guild_priest_chamber',
    'priest chapel': 'guild_priest_chamber',
    'ilyra': 'guild_psion_chamber',
    'komnata psionika': 'guild_psion_chamber',
    'psion chamber': 'guild_psion_chamber',
    'kael': 'guild_rogue_chamber',
    'rogue hall': 'guild_rogue_chamber',
    'sala lotrzyka': 'guild_rogue_chamber',
    'druidzi': 'guild_sanctuary',
    'kaplani': 'guild_sanctuary',
    'sanktuarium': 'guild_sanctuary',
    'sklep druida': 'guild_sanctuary',
    'sklep kaplana': 'guild_sanctuary',
    'sklep kapłana': 'guild_sanctuary',
    'galeria cieni': 'guild_shadow_gallery',
    'lotrzycy': 'guild_shadow_gallery',
    'lowcy': 'guild_shadow_gallery',
    'sklep lotrzyka': 'guild_shadow_gallery',
    'sklep lowcy': 'guild_shadow_gallery',
    'sklep łotrzyka': 'guild_shadow_gallery',
    'sklep łowcy': 'guild_shadow_gallery',
    'komnata czarownika': 'guild_warlock_chamber',
    'nyra': 'guild_warlock_chamber',
    'warlock chamber': 'guild_warlock_chamber',
    'garran': 'guild_warrior_chamber',
    'sala wojownika': 'guild_warrior_chamber',
    'warrior hall': 'guild_warrior_chamber',

    # PROFESJE I NARZEDZIA
    'laboratorium alchemiczne': 'alchemy_lab',
    'mistrz alchemii': 'alchemy_lab',
    'mozdzierz sklep': 'alchemy_lab',
    'orin': 'alchemy_lab',
    'sklep mozdzierza': 'alchemy_lab',
    'kucharz marcel': 'blue_flame_kitchen',
    'kuchnia blekitnego plomienia': 'blue_flame_kitchen',
    'marcel': 'blue_flame_kitchen',
    'noz kucharski sklep': 'blue_flame_kitchen',
    'sklep noza': 'blue_flame_kitchen',
    'gornik toren': 'cave_entrance',
    'jaskinia': 'cave_entrance',
    'sklep kilof': 'cave_entrance',
    'sklep kilofa': 'cave_entrance',
    'toren': 'cave_entrance',
    'wejscie do jaskini': 'cave_entrance',
    'haldor': 'crafting_workshop',
    'mistrz rzemiosla': 'crafting_workshop',
    'mlot rzemieslniczy sklep': 'crafting_workshop',
    'sklep mlota': 'crafting_workshop',
    'warsztat rzemieslniczy': 'crafting_workshop',
    'rybak borys': 'fish_market',
    'borys': 'fish_market',
    # Stare aliasy Tomasa pozostają tylko dla zgodności zapisanych skrótów/makr.
    'rybak tomas': 'fish_market',
    'ryby': 'fish_market',
    'targ rybny': 'fish_market',
    'tomas': 'fish_market',
    'mistrz wedkarstwa': 'fishing_school',
    'neris': 'fishing_school',
    'sklep wedek': 'fishing_school',
    'sklep wedki': 'fishing_school',
    'szkola wedkarstwa': 'fishing_school',
    'wedka sklep': 'fishing_school',
    'lesniczowka': 'forester_lodge',
    'mistrz drwalstwa': 'forester_lodge',
    'oren': 'forester_lodge',
    'pila sklep': 'forester_lodge',
    'sklep pily': 'forester_lodge',
    'doran': 'forge',
    'kowal': 'forge',
    'kowal doran': 'forge',
    'kuznia': 'forge',
    'mistrzyni zielarstwa': 'herbalism_garden',
    'ogrod zielarski': 'herbalism_garden',
    'sena': 'herbalism_garden',
    'sierp sklep': 'herbalism_garden',
    'sklep sierpa': 'herbalism_garden',
    'jubiler': 'jeweler_workshop',
    'jubilerka': 'jeweler_workshop',
    'jubilerka mirella': 'jeweler_workshop',
    'jubilerstwo': 'jeweler_workshop',
    'mirella': 'jeweler_workshop',
    'pracownia jubilerska': 'jeweler_workshop',
    'sklep szczypiec': 'jeweler_workshop',
    'szczypce sklep': 'jeweler_workshop',
    'bran': 'lumberjack_camp',
    'drwal': 'lumberjack_camp',
    'drwal bran': 'lumberjack_camp',
    'gildia gornikow': 'miners_guild',
    'kordan': 'miners_guild',
    'mistrz gornictwa': 'miners_guild',

    # REGIONY I TERENY
    'legowisko rogatego krola': 'beast_den',
    'rogaty krol': 'beast_den',
    'serce bagna': 'bog_heart',
    'pustynia': 'desert_gate',
    'wielka pustynia': 'desert_gate',
    'sanktuarium wiecznego slonca': 'desert_solar_sanctum',
    'grobowiec slonca': 'desert_sun_tomb',
    'brok': 'mountain_forge',
    'gorska kuznia': 'mountain_forge',
    'kowal gorski': 'mountain_forge',
    'eryk': 'mountain_guard_house',
    'straznik eryk': 'mountain_guard_house',
    'nizsze stoki': 'mountain_lower_slopes',
    'dagna': 'mountain_market',
    'gorski targ mineralow': 'mountain_market',
    'gorska przelecz': 'mountain_pass',
    'gory': 'mountain_pass',
    'sciezka wiecznej burzy': 'mountain_tempest_path',
    'sanktuarium wiecznej burzy': 'mountain_tempest_sanctum',
    'wioska gorska': 'mountain_village',
    'wioska w gorach': 'mountain_village',
    'szczyt burzy': 'storm_summit',
    'swiatynia slonca': 'sun_temple',
    'bagna': 'swamp_boardwalk',
    'czarne bagno': 'swamp_boardwalk',
    'lowca bagien': 'swamp_hunter_post',
    'posterunek bagien': 'swamp_hunter_post',
    'varg': 'swamp_hunter_post',
    'pradawne rozlewisko': 'swamp_primordial_pool',
    'gnijace glebie bagna': 'swamp_rotten_depths',
    'bagienna zielarka': 'swamp_witch_hut',
    'nela': 'swamp_witch_hut',
    'pradawny szlak bestii': 'wild_ancient_path',
    'polnocna dzicz': 'wild_frontier',
    'skraj polnocnej dziczy': 'wild_frontier',
    'pradawna kotlina dziczy': 'wild_primal_hollow',

    # LOCHY I ENDGAME
    'astral': 'astral_gate',
    'astralna brama': 'astral_gate',
    'brama astralna': 'astral_gate',
    'wieza': 'astral_gate',
    'wieza astralna': 'astral_gate',
    'wieża': 'astral_gate',
    'wieża astralna': 'astral_gate',
    'glebia krypty': 'crypt_depths',
    'przedsionek krypty': 'crypt_entrance',
    'wejscie do krypty': 'crypt_entrance',
    'sala krypty': 'crypt_hall',
    'brama twierdzy gigantow': 'giant_fortress_gate',
    'twierdza gigantow': 'giant_fortress_gate',
    'kopalnia glebinowa': 'mine_floor_1',
    'mityczna wieza astralna': 'mythic_astral_gate',
    'mythic astral tower': 'mythic_astral_gate',
    'mityczna krypta': 'mythic_crypt_gate',
    'mythic crypt': 'mythic_crypt_gate',
    'ogrod alchemika': 'prof_alchemy_garden_1',
    'pradawny las': 'prof_ancient_forest_1',
    'kopalnia krysztalow': 'mine_floor_1',
    'krysztalowa kopalnia': 'mine_floor_1',
    'zatopiona grota': 'prof_sunken_grotto_1',
    'otchlan trolli': 'troll_abyss',
    'tron pierwszego wodza': 'troll_abyss_throne',
    'jaskinia trolli': 'troll_cave_entrance',
    'trolle': 'troll_cave_entrance',
    'krol trolli': 'troll_king_den',

    # v0.8.14 Exploration First Guide
    'krypta': 'crypt_entrance',
    'crypt': 'crypt_entrance',
    'kopalnia': 'mine_floor_1',
    'mine': 'mine_floor_1',
    'twierdza': 'giant_fortress_gate',
    'fortress': 'giant_fortress_gate',
    'giant fortress': 'giant_fortress_gate',
    'dzicz': 'old_road',
    'wilds': 'old_road',
    'podziemia': 'cave_entrance',
    'underground': 'cave_entrance',
    'crystal cave': 'cave_entrance',
    'crystal mine': 'mine_floor_1',
    'krysztalowe groty': 'prof_crystal_mine_1',
    'kryształowe groty': 'prof_crystal_mine_1',
    'crystal grottos': 'prof_crystal_mine_1',
    'sunken grotto': 'prof_sunken_grotto_1',
    'ancient forest': 'prof_ancient_forest_1',
    'alchemy garden': 'prof_alchemy_garden_1',

}

# v0.52.2: settlement names are first-class guide destinations.  Queries are
# normalized before lookup, so aliases stored here intentionally use the same
# ASCII form as the navigation normalizer.
for _city_name_v0522, _city_room_v0522 in GUIDE_CITY_HUBS_V0522.items():
    _city_key_v0522 = (
        _city_name_v0522.lower()
        .replace("ą", "a").replace("ć", "c").replace("ę", "e")
        .replace("ł", "l").replace("ń", "n").replace("ó", "o")
        .replace("ś", "s").replace("ź", "z").replace("ż", "z")
    )
    GUIDE_DESTINATION_ALIASES[_city_key_v0522] = _city_room_v0522

# Miasto Dusz ma osobne, istniejące Biuro Kurierów; pozostałe miasta
# obsługują pocztę na swoich centralnych placach.
GUIDE_DESTINATION_ALIASES.update({
    "poczta": "courier_office",
    "biuro kurierow": "courier_office",
    "biuro kuriera": "courier_office",
    "kurier": "courier_office",
})

TOOL_BUY_ALIASES = {
    "wedka": "fishing_rod",
    "wedke": "fishing_rod",
    "rod": "fishing_rod",
    "kilof": "pickaxe",
    "pickaxe": "pickaxe",
    "pila": "saw",
    "pile": "saw",
    "saw": "saw",
    "mlot": "crafting_hammer",
    "mlot rzemieslniczy": "crafting_hammer",
    "hammer": "crafting_hammer",
    "noz": "chef_knife",
    "noz kucharski": "chef_knife",
    "knife": "chef_knife",
    "sierp": "herbalist_sickle",
    "sierp zielarski": "herbalist_sickle",
    "sickle": "herbalist_sickle",
    "mozdzierz": "alchemy_mortar",
    "mozdzierz alchemiczny": "alchemy_mortar",
    "mortar": "alchemy_mortar",
    "szczypce": "jeweler_pliers",
    "szczypce jubilerskie": "jeweler_pliers",
    "pliers": "jeweler_pliers",
    "jeweler pliers": "jeweler_pliers",
}

CHARACTER_BOUND_TOOL_IDS = {
    "fishing_rod",
    "pickaxe",
    "saw",
    "crafting_hammer",
    "chef_knife",
    "herbalist_sickle",
    "alchemy_mortar",
    "jeweler_pliers",
}

def is_character_bound_item(item_id):
    return item_id in CHARACTER_BOUND_TOOL_IDS

TOOL_SHOP_ROOMS = {
    "fishing_rod": "fish_market",
    "pickaxe": "cave_entrance",
    "saw": "lumberjack_camp",
    "crafting_hammer": "forge",
    "chef_knife": "inn",
    "herbalist_sickle": "herbalist_hut",
    "alchemy_mortar": "herbalist_hut",
    "jeweler_pliers": "jeweler_workshop",
}

EQUIPMENT_SLOT_ALIASES = {
    "helm": "head",
    "helmet": "head",
    "helmik": "head",
    "hełm": "head",
    "glowa": "head",
    "głowa": "head",

    "zbroja": "body",
    "pancerz": "body",
    "napierśnik": "body",
    "napiersnik": "body",
    "korpus": "body",
    "armor": "body",
    "body": "body",

    "rekawice": "hands",
    "rękawice": "hands",
    "dlonie": "hands",
    "dłonie": "hands",
    "gloves": "hands",
    "hands": "hands",

    "nogi": "legs",
    "nogawice": "legs",
    "spodnie": "legs",
    "legs": "legs",

    "buty": "feet",
    "stopy": "feet",
    "boots": "feet",
    "feet": "feet",

    "talizman": "charm",
    "amulet": "charm",
    "charm": "charm",
    "talizman 1": "charm1", "talizman1": "charm1",
    "amulet 1": "charm1", "charm 1": "charm1", "charm1": "charm1",
    "talizman 2": "charm2", "talizman2": "charm2",
    "amulet 2": "charm2", "charm 2": "charm2", "charm2": "charm2",

    "pierścień": "ring",
    "pierscien": "ring",
    "pierścien": "ring",
    "ring": "ring",
    "pierścień 1": "ring1", "pierscien 1": "ring1",
    "ring 1": "ring1", "ring1": "ring1", "first ring": "ring1",
    "pierścień 2": "ring2", "pierscien 2": "ring2",
    "ring 2": "ring2", "ring2": "ring2", "second ring": "ring2",

    "naszyjnik": "necklace",
    "naszyjnika": "necklace",
    "necklace": "necklace",

    "kolczyk": "earring",
    "kolczyki": "earring",
    "earring": "earring",
    "earrings": "earring",
    "kolczyk 1": "earring1", "kolczyk1": "earring1",
    "earring 1": "earring1", "earring1": "earring1",
    "kolczyk 2": "earring2", "kolczyk2": "earring2",
    "earring 2": "earring2", "earring2": "earring2",

    "naramienniki": "shoulders",
    "naramiennik": "shoulders",
    "shoulders": "shoulders",
    "shoulder": "shoulders",

    "pas": "belt",
    "belt": "belt",

    "peleryna": "cloak",
    "plaszcz": "cloak",
    "płaszcz": "cloak",
    "cloak": "cloak",

    "karwasze": "bracers",
    "karwasz": "bracers",
    "bracers": "bracers",

    "relikt": "relic",
    "relic": "relic",

    "board": "board",
    "moogle board": "board",
    "modul": "board",
    "moduł": "board",

}

EQUIPMENT_SLOT_NAMES = {
    "head": "głowa",
    "body": "korpus",
    "hands": "dłonie",
    "legs": "nogi",
    "feet": "stopy",
    "charm": "talizman",
    "charm1": "talizman 1",
    "charm2": "talizman 2",
    "ring": "pierścień",
    "ring1": "pierścień 1",
    "ring2": "pierścień 2",
    "necklace": "naszyjnik",
    "earring": "kolczyki",
    "earring1": "kolczyk 1",
    "earring2": "kolczyk 2",
    "shoulders": "naramienniki",
    "belt": "pas",
    "cloak": "peleryna",
    "bracers": "karwasze",
    "relic": "relikt",
    "board": "Board",
}

EXP_AREAS = (
    {
        "id": "trening",
        "name": "Plac Treningowy",
        "aliases": (
            "trening", "plac treningowy", "manekin", "manekiny",
        ),
        "soul_min": 1,
        "soul_max": 10,
        "difficulty": "bardzo łatwa",
        "guide": "manekiny",
        "enemies": "Żywy Manekin",
        "description": (
            "Najbezpieczniejsze miejsce do sprawdzania obrażeń, "
            "umiejętności i podstaw walki. Dobre na sam początek."
        ),
        "note": (
            "Manekin jest przeznaczony głównie do treningu, "
            "więc szybko warto przenieść się do Podziemi lub Dziczy."
        ),
    },
    {
        "id": "podziemia",
        "name": "Podziemia i Kryształowa Jaskinia",
        "aliases": (
            "podziemia", "krysztalowa jaskinia", "jaskinia",
            "piwnica swiatyni", "krysztalowa komnata",
        ),
        "soul_min": 1,
        "soul_max": 25,
        "difficulty": "łatwa",
        "guide": "jaskinia",
        "enemies": (
            "Szczur Świątynny, Szkielet Strażnik, Upiór Krypty, "
            "Kryształowy Strażnik i Kryształowy Władca"
        ),
        "description": (
            "Wczesne podziemia z rosnącą trudnością. "
            "Dobre miejsce na pierwsze regularne walki i oswojenie się "
            "z silniejszymi przeciwnikami."
        ),
        "note": (
            "Kryształowy Władca jest bossem i jest znacznie mocniejszy "
            "od zwykłych mobów tego regionu."
        ),
    },
    {
        "id": "bandit_camps",
        "name": "Obozowiska Bandytów",
        "aliases": (
            "bandyci", "oboz bandytow", "obozowiska bandytow", "bandit camp", "bandit camps",
        ),
        "soul_min": 10,
        "soul_max": 40,
        "difficulty": "łatwa do średniej",
        "guide": "bandyci",
        "enemies": (
            "Bandyta, Bandycki Zwiadowca, Kusznik, Rzezimieszek, Maruder, "
            "Najeźdźca, Alchemik, Egzekutor, Weteran, Kapitan Bandytów i Herszt Bandytów"
        ),
        "description": (
            "Rozbudowany kompleks kilku części obozu. Im głębiej, tym lepiej uzbrojeni przeciwnicy. "
            "Wewnętrzne obozowisko prowadzi do namiotu Herszta."
        ),
        "note": (
            "Prowadzenie zatrzymuje przed wejściem do obozowiska. Wnętrze trzeba eksplorować samodzielnie."
        ),
    },
    {
        "id": "goblin_caves",
        "name": "Jaskinie Goblinów",
        "aliases": (
            "gobliny", "jaskinia goblinow", "jaskinie goblinow", "goblin cave", "goblin caves",
        ),
        "soul_min": 10,
        "soul_max": 45,
        "difficulty": "łatwa do średniej",
        "guide": "jaskinie goblinow",
        "enemies": (
            "Goblin, Gobliński Zwiadowca, Włócznik, Łucznik, Osiłek, Szaman, Bombiarz, "
            "Strażnik Jaskiń, Wojownik Króla, Gobliński Wódz Wojenny i Król Goblinów"
        ),
        "description": (
            "Rozległy podziemny kompleks od galerii grzybów po grotę Króla Goblinów. "
            "W głębi pojawia się więcej magii, cięższa straż i elity."
        ),
        "note": (
            "Prowadzenie zatrzymuje przed wejściem do Jaskiń Goblinów. Wnętrze i drogę do króla trzeba odkryć samemu."
        ),
    },
    {
        "id": "ruiny_straznicy",
        "name": "Ruiny Strażnicy",
        "aliases": (
            "ruiny straznicy", "ruiny strażnicy", "stara straznica", "stara strażnica", "ruined watchtower",
        ),
        "soul_min": 15,
        "soul_max": 55,
        "difficulty": "łatwa do średniej",
        "guide": "ruiny straznicy",
        "enemies": (
            "Ożywieni Wartownicy, Włócznicy, Kusznicy i Tarczownicy Starej Straży, "
            "Runiczni Strażnicy, Widma Strażnicy, Kamienni Obserwatorzy, Goblińscy Łupieżcy, "
            "Kapitan Starej Straży i Strażnik Ruin"
        ),
        "description": (
            "Rozbudowane ruiny dawnego garnizonu: brama, dziedziniec, koszary, zbrojownia, mur, "
            "archiwum runiczne, piwnice, podziemia, sala pieczęci i komnata dowódcy."
        ),
        "note": (
            "Wejście do wnętrza prowadzi w dół z głównej lokacji Ruiny Strażnicy. "
            "Strażnik Ruin znajduje się teraz w najgłębszej komnacie dowódcy."
        ),
    },
    {
        "id": "dzicz",
        "name": "Dzicz",
        "aliases": (
            "dzicz", "ruiny", "gobliny", "bandyci", "wilki",
            "stary cmentarz", "oboz bandytow",
        ),
        "soul_min": 10,
        "soul_max": 45,
        "difficulty": "łatwa do średniej",
        "guide": "ruiny",
        "enemies": (
            "Bandyci wielu rang, Gobliny wielu rang, Goblińscy Szamani i Bombiarze, "
            "oraz Wilki Cienia"
        ),
        "description": (
            "Rozległy teren świata z kilkoma grupami przeciwników. "
            "Dobry do zwykłego expienia, questów i zdobywania sprzętu."
        ),
        "note": (
            "Obozowiska Bandytów i Jaskinie Goblinów są teraz osobnymi, rozbudowanymi expowiskami. "
            "Herszt Bandytów i Król Goblinów znajdują się głęboko w swoich obszarach."
        ),
    },
    {
        "id": "trolle",
        "name": "Góry i Jaskinia Trolli",
        "aliases": (
            "trolle", "jaskinia trolli", "gory", "góry",
            "gorski szlak", "krol trolli",
        ),
        "soul_min": 25,
        "soul_max": 70,
        "difficulty": "średnia",
        "guide": "jaskinia trolli",
        "enemies": (
            "Górskie Trolle, Trolle Osiłki, Trolle Szamani "
            "oraz rzadkie i elitarne warianty trolli"
        ),
        "description": (
            "Mocniejsze expowisko powiązane z Wioską Górską. "
            "Przeciwnicy mają więcej HP, a rzadkie trolle i elite affixy "
            "mogą wyraźnie zwiększyć trudność."
        ),
        "note": (
            "Na końcu jaskini czeka Król Trolli Grum. "
            "Trolle mogą też zostawiać Skradzione Skrzynie Rudy."
        ),
    },
    {
        "id": "giganci",
        "name": "Twierdza Gigantów 1+",
        "aliases": (
            "giganci", "twierdza gigantow", "twierdza gigantów",
            "twierdza", "cyklopy", "ogry",
        ),
        "soul_min": 45,
        "soul_max": 130,
        "difficulty": "średnia do bardzo trudnej",
        "guide": "twierdza gigantow",
        "enemies": (
            "Ogrzy Miotacze Głazów, Cyklopi Strażnicy i Górskie Giganty"
        ),
        "description": (
            "Nieskończony górski dungeon; każdy poziom od 1 jest tworzony dynamicznie dopiero przy wejściu. "
            "Z każdym poziomem rośnie HP, obrażenie i nagroda Soul XP. "
            "Nadaje się do dłuższego expienia bez zmiany regionu."
        ),
        "note": (
            "Boss stoi co 10 poziomów i musi zostać pokonany, aby wejść wyżej."
        ),
    },
    {
        "id": "krypta",
        "name": "Krypta Nieskończona",
        "aliases": (
            "krypta", "krypta nieskonczona", "krypta nieskończona", "crypt", "infinite crypt",
        ),
        "soul_min": 30,
        "soul_max": 200,
        "difficulty": "skalowana bez końca od średniej do ekstremalnej",
        "guide": "wejscie do krypty",
        "enemies": (
            "Szkielety Krypty, Upiory Krypty, Strażnicy Sarkofagu, "
            "Cienie Katakumb i Zjawiska Pustki"
        ),
        "description": (
            "Główne nieskończone expowisko. "
            "Trudność i XP rosną z piętrem, z dodatkowym progiem co 10 pięter, "
            "więc możesz dobierać głębokość do aktualnej siły postaci."
        ),
        "note": (
            "Boss stoi co 10 pięter. Boss blokuje zejście niżej. "
            "Pokonani bossowie odblokowują checkpointy portalu."
        ),
    },
    {
        "id": "astral",
        "name": "Wieża Astralna 100+",
        "aliases": (
            "astral", "wieza astralna", "wieża astralna",
            "astralna wieza", "astralna wieża",
        ),
        "soul_min": 100,
        "soul_max": 200,
        "difficulty": "trudna i endgame",
        "guide": "wieza astralna",
        "enemies": (
            "Astralni Strażnicy, Widma Konstelacji, Rycerze Gwiezdnego Pyłu, "
            "Tkacze Nebuli, Heroldzi Komety i Strażnicy Firmamentu"
        ),
        "description": (
            "Drugie główne expowisko endgame. "
            "Wieża zaczyna się na poziomie 100 i wymaga Soul Level 100. "
            "Daje wysokie Soul XP oraz Astralny ekwipunek."
        ),
        "note": (
            "Boss stoi co 10 poziomów od 100 bez górnego limitu i blokuje drogę w górę."
        ),
    },
    {
        "id": "mythic_crypt",
        "name": "Mityczna Krypta Nieskończona",
        "aliases": (
            "mityczna krypta", "mythic crypt", "mythic krypta",
        ),
        "soul_min": 1,
        "soul_max": 200,
        "difficulty": "bardzo trudna od wejścia, skalowana bez końca",
        "guide": "mityczna krypta",
        "enemies": (
            "Mityczni Kościani Rycerze, Mityczne Upiory, "
            "Mityczni Żniwiarze Grobowca i Strażnicy Otchłani"
        ),
        "description": (
            "Mityczna wersja Krypty jest dostępna bez blokady Soul Level. "
            "Od pierwszego piętra jest bardzo trudna, a trudność i XP rosną bez końca."
        ),
        "note": (
            "Wejście nie ma wymogu Soul Level ani ukończenia zwykłej Krypty. "
            "Mityczny boss występuje co 10 pięter bez końca i blokuje zejście niżej."
        ),
    },
    {
        "id": "mythic_astral",
        "name": "Mityczna Wieża Astralna 1+",
        "aliases": (
            "mityczna wieza astralna", "mityczna wieża astralna",
            "mythic astral", "mythic astral tower",
        ),
        "soul_min": 100,
        "soul_max": 200,
        "difficulty": "najtrudniejszy endgame",
        "guide": "mityczna wieza astralna",
        "enemies": (
            "Mityczni Astralni Strażnicy, Mityczni Rycerze Konstelacji, "
            "Mityczne Widma Nebuli i Heroldzi Gwiezdnej Burzy"
        ),
        "description": (
            "Mityczna Wieża Astralna jest dostępna od Soul Level 100. "
            "To ekstremalnie trudne expowisko z bardzo wysokimi nagrodami Soul XP."
        ),
        "note": (
            "Wejście wymaga Soul Level 100. "
            "Nie wymaga ukończenia zwykłej Wieży Astralnej do poziomu 200. "
            "Mityczny boss występuje co 10 poziomów."
        ),
    },
)

# v0.8.54 - dynamiczne kategorie terenów i skalowanie EXP.
# Kategoria bazowa opisuje naturalne przeznaczenie obszaru. Ocena "dla ciebie"
# jest liczona na bieżąco z faktycznego rozwoju postaci, bo Soulbound nie ma
# ogólnego levelu postaci.
EXP_AREA_BASE_CATEGORY = {
    "trening": "Początkujący",
    "podziemia": "Początkujący",
    "bandit_camps": "Początkujący",
    "goblin_caves": "Początkujący",
    "ruiny_straznicy": "Początkujący",
    "dzicz": "Początkujący",
    "kanaly": "Początkujący",
    "cmentarz": "Początkujący",
    "whisper_forest": "Początkujący",
    "trolle": "Umiarkowany",
    "legowisko_bestii": "Umiarkowany",
    "ruiny_kultystow": "Umiarkowany",
    "bagna": "Umiarkowany",
    "giganci": "Trudny",
    "lodowe_jaskinie": "Trudny",
    "pustynia": "Trudny",
    "nekropolia": "Trudny",
    "krypta": "Trudny skalowany",
    "astral": "Śmiertelny",
    "mythic_crypt": "Śmiertelny",
    "mythic_astral": "Ekstremalny Endgame",
}

# Orientacyjna siła wejściowa obszaru w skali 1-600. Dla wielopiętrowych
# lochów faktyczny próg jest dodatkowo liczony z aktualnego piętra.
EXP_AREA_TARGET_POWER = {
    "trening": 1,
    "podziemia": 5,
    "bandit_camps": 10,
    "goblin_caves": 10,
    "ruiny_straznicy": 18,
    "dzicz": 14,
    "kanaly": 12,
    "cmentarz": 15,
    "whisper_forest": 12,
    "trolle": 30,
    "legowisko_bestii": 35,
    "ruiny_kultystow": 45,
    "bagna": 45,
    "giganci": 50,
    "lodowe_jaskinie": 65,
    "pustynia": 75,
    "nekropolia": 80,
    "krypta": 30,
    "astral": 110,
    "mythic_crypt": 130,
    "mythic_astral": 150,
}

EXP_ZONE_AREA_ID = {
    "Podziemia": "podziemia",
    "Obozowiska Bandytów": "bandit_camps",
    "Jaskinie Goblinów": "goblin_caves",
    "Ruiny Strażnicy": "ruiny_straznicy",
    "Dzicz": "dzicz",
    "Góry": "trolle",
    "Jaskinia Trolli": "trolle",
    "Twierdza Gigantów": "giganci",
    "Krypta Nieskończona": "krypta",
    "Wieża Astralna": "astral",
    "Mityczna Krypta": "mythic_crypt",
    "Mityczna Wieża Astralna": "mythic_astral",
    "Bagna": "bagna",
    "Pustynia": "pustynia",
    "Stary Cmentarz": "cmentarz",
    "Ruiny Kultystów": "ruiny_kultystow",
    "Legowisko Bestii": "legowisko_bestii",
    "Nekropolia": "nekropolia",
    "Kanały Pod Miastem": "kanaly",
    "Lodowe Jaskinie": "lodowe_jaskinie",
    "Las Szeptów": "whisper_forest",
}

# v0.23.0: EXP z walki nie jest stałą nagrodą z tabeli moba. Bazowa wartość
# nadal opisuje rangę przeciwnika, ale końcowa wypłata EXP statów, Soul XP i
# Class XP zależy płynnie od siły moba względem AKTUALNEJ siły postaci.
# Dzięki temu słabsza postać dostaje premię za ryzyko, a po przerośnięciu
# danego expowiska ta sama farma daje stopniowo mniej EXP. Waluta i loot nie
# są przez ten mnożnik zmieniane.
DYNAMIC_KILL_XP_MIN_MULTIPLIER = 0.35
DYNAMIC_KILL_XP_MAX_MULTIPLIER = 2.25

# v0.8.66 - teren i EXP są oceniane z faktycznej siły spawnów, a nie tylko
# z ręcznej etykiety biomu. Kalibracja bazuje na krzywej Krypty 1-200:
# zwykły mob około floor 100 ma ~1940 HP i ~39 dmg, floor 200 ~3740/72.
_ROOM_THREAT_CACHE = {}
_ZONE_THREAT_CACHE = {}

def v0866_is_boss_template(template):
    return bool(
        template.get("world_boss")
        or template.get("mini_boss")
        or template.get("crypt_boss")
        or template.get("astral_boss")
        or template.get("mythic_crypt_boss")
        or template.get("mythic_astral_boss")
        or template.get("giant_fortress_boss")
        or template.get("boss_mechanic")
    )

def v0866_is_random_variant_template(template):
    return bool(
        template.get("rare_mob")
        or template.get("elite_affix")
        or template.get("rare_troll")
    )

def v0866_template_explicit_floor_power(template):
    level = template.get("generator_level")
    if level is not None:
        return max(1, min(CHARACTER_MAX_LEVEL, int(level)))
    semantic = generator_core_v027.semantic_floor_level(template)
    return max(1, min(CHARACTER_MAX_LEVEL, int(semantic))) if semantic is not None else None

def v0866_mob_progression_power(template):
    """Compatibility route: active threat is Generator Core stage 1-600."""
    level = template.get("generator_level")
    if level is not None:
        return max(1, min(CHARACTER_MAX_LEVEL, int(level)))
    explicit = v0866_template_explicit_floor_power(template)
    if explicit is not None:
        return explicit
    # Dynamic records are normalized immediately before use.
    v0190_apply_combat_template(template)
    return max(1, min(CHARACTER_MAX_LEVEL, int(template.get("generator_level", 1) or 1)))

def v0866_percentile(values, fraction):
    values = sorted(int(v) for v in values)
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    index = max(0, min(len(values) - 1, int(round((len(values) - 1) * fraction))))
    return values[index]

def v0866_room_threat_profile(room_id, fallback=1):
    cache_key = str(room_id or "")
    cached = _ROOM_THREAT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    normal = []
    bosses = []
    variants = []
    for spawn_room, template_id in MOB_SPAWNS:
        if spawn_room != room_id:
            continue
        template = MOB_TEMPLATES.get(template_id)
        if not template or template.get("training_dummy"):
            continue
        power = v0866_mob_progression_power(template)
        if v0866_is_random_variant_template(template):
            variants.append(power)
        elif v0866_is_boss_template(template):
            bosses.append(power)
        else:
            normal.append(power)
    # 60 percentyl zwykłych spawnów lepiej opisuje realny grind niż maksimum.
    # Endgame odnogi z dwoma silnymi mobami nadal dostają pełny wysoki target.
    target = v0866_percentile(normal, 0.60)
    if target is None:
        target = v0866_percentile(variants, 0.50)
    if target is None:
        target = v0866_percentile(bosses, 0.35)
    if target is None:
        target = max(1, min(CHARACTER_MAX_LEVEL, int(fallback or 1)))
    profile = {
        "target": int(target),
        "normal_min": min(normal) if normal else None,
        "normal_max": max(normal) if normal else None,
        "boss_min": min(bosses) if bosses else None,
        "boss_max": max(bosses) if bosses else None,
        "variant_min": min(variants) if variants else None,
        "variant_max": max(variants) if variants else None,
        "normal_count": len(normal),
        "boss_count": len(bosses),
        "variant_count": len(variants),
    }
    _ROOM_THREAT_CACHE[cache_key] = profile
    return profile

def v0866_threat_label(target, power):
    delta = int(target) - int(power)
    if delta <= -40:
        return "Trywialny"
    if delta <= -15:
        return "Łatwy"
    if delta <= 10:
        return "Odpowiedni"
    if delta <= 30:
        return "Trudny"
    if delta <= 60:
        return "Śmiertelny"
    return "Ekstremalny"


def v0866_zone_threat_profile(zone):
    cache_key = str(zone or "")
    cached = _ZONE_THREAT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    room_targets = []
    boss_targets = []
    for room_id, room in ROOMS.items():
        if room.get("zone") != zone:
            continue
        profile = v0866_room_threat_profile(room_id, fallback=1)
        if profile["normal_count"] or profile["variant_count"]:
            room_targets.append(profile["target"])
        if profile["boss_max"] is not None:
            boss_targets.append(profile["boss_max"])
    result = {
        "min": min(room_targets) if room_targets else None,
        "median": v0866_percentile(room_targets, 0.50),
        "p80": v0866_percentile(room_targets, 0.80),
        "max": max(room_targets) if room_targets else None,
        "boss_min": min(boss_targets) if boss_targets else None,
        "boss_max": max(boss_targets) if boss_targets else None,
        "rooms": len(room_targets),
    }
    _ZONE_THREAT_CACHE[cache_key] = result
    return result

COMMAND_ALIASES = CommandAliasMap(COMMAND_ALIAS_DEFINITIONS)

from data.items import ITEMS


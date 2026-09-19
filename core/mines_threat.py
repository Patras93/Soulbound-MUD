
def build_mine_depth_rooms():
    ROOMS["crystal_chamber"]["exits"]["down"] = mine_floor_id(1)

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
        ROOMS[mine_floor_id(floor)] = {
            "zone": "Kopalnia Głębinowa",
            "name": f"Kopalnia - poziom {floor}",
            "desc": (
                f"Poziom {floor}. Pierwsze 200 poziomów to ręcznie przygotowana część Kopalni. "
                f"Najczęstsze złoża: {band}." + wall_text
            ),
            "exits": exits,
        }

build_mine_depth_rooms()

ROOMS["jeweler_workshop"] = {
    "zone": "Miasto Dusz",
    "name": "Pracownia Jubilerska",
    "desc": (
        "Jasna pracownia pełna drobnych narzędzi, metalowych opraw "
        "i stołów do wykonywania pierścieni oraz naszyjników. "
        "Pracuje tutaj Jubilerka Mirella."
    ),
    "exits": {"down": "market"},
}
ROOMS["market"]["exits"]["up"] = "jeweler_workshop"

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

# Orientacyjna siła wejściowa obszaru w skali 1-400. Dla wielopiętrowych
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
        return max(1, min(400, int(level)))
    semantic = generator_core_v027.semantic_floor_level(template)
    return max(1, min(400, int(semantic))) if semantic is not None else None

def v0866_mob_progression_power(template):
    """Compatibility route: active threat is Generator Core stage 1-400."""
    level = template.get("generator_level")
    if level is not None:
        return max(1, min(400, int(level)))
    explicit = v0866_template_explicit_floor_power(template)
    if explicit is not None:
        return explicit
    # Dynamic records are normalized immediately before use.
    v0190_apply_combat_template(template)
    return max(1, min(400, int(template.get("generator_level", 1) or 1)))

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
        target = max(1, min(400, int(fallback or 1)))
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

COMMAND_ALIASES = {
    "pomoc": "help", "pomoce": "help",
    "kodowanie": "encoding", "encoding": "encoding",
    "charset": "encoding", "znaki": "encoding",
    "opis": "describe", "opisz": "describe", "describe": "describe", "description": "describe",
    "changes": "changes", "zmiany": "changes", "changelog": "changes",
    "historia": "lifetime", "history": "lifetime", "lifetime": "lifetime",
    "statystykizycia": "lifetime", "lifestats": "lifetime",
    "bufor": "historybuffer", "bufory": "historybuffer", "histbuf": "historybuffer",
    "historybuffer": "historybuffer", "logbuf": "historybuffer",
    "spójrz": "look", "spojrz": "look", "sp": "look", "l": "look",
    "wyjścia": "exits", "wyjscia": "exits", "ex": "exits",
    "wydarzenia": "worldevents", "wydarzenie": "worldevents", "eventy": "worldevents", "events": "worldevents",
    "worldevents": "worldevents", "worldevent": "worldevents",
    "eventxp": "eventxp", "xpevent": "eventxp", "eventexp": "eventxp", "happyhour": "eventxp",
    "wimpy": "wimpy",
    "dynamiceventy": "dynamicevents", "dynamicevents": "dynamicevents", "dynamiczneeventy": "dynamicevents",
    "nemesis": "nemesis", "nemezis": "nemesis",
    "mapa": "map",
    "sekret": "instancesecret", "secret": "instancesecret",
    "tajemnica": "instancesecret",
    "gdzie": "where",
    "trasa": "route", "route": "route", "droga": "route", "sciezka": "route", "ścieżka": "route",
    "kto": "who",
    "expowiska": "expareas", "expowisko": "expareas",
    "terenyexp": "expareas", "terenydoexpienia": "expareas",
    "expienie": "expareas",
    "teren": "terraininfo", "terrain": "terraininfo", "region": "terraininfo",
    "tereninfo": "terraininfo",
    "sety": "classsets", "setklasowy": "classsets", "setyklasowe": "classsets",
    "say": "say", "powiedz": "say", "mow": "say", "mów": "say",
    "gossip": "gossip", "plotki": "gossip", "plotka": "gossip",
    "newbie": "newbie", "nowi": "newbie", "nowicjusze": "newbie",
    "trade": "trade", "handel": "trade", "targ": "trade",
    "kanaly": "channels", "kanały": "channels", "channels": "channels",
    "mentor": "mentor", "mentoring": "mentor",
    "tell": "tell", "msg": "tell", "pm": "tell", "wiadomosc": "tell", "wiadomość": "tell",
    "reply": "reply", "odpisz": "reply", "r": "reply",
    "znajomi": "friends", "znajomy": "friends", "friends": "friends", "friend": "friends",
    "atlas": "atlas", "atlasy": "atlas",
    "codex": "codex", "kodeks": "codex",
    "kodeksklasowy": "classcodex", "kodeks_klasowy": "classcodex",
    "codexklasowy": "classcodex", "klasowycodex": "classcodex",
    "classcodex": "classcodex", "class_codex": "classcodex",
    "skillcodex": "classcodex", "skill_codex": "classcodex",
    "bestiariusz": "bestiary", "bestiary": "bestiary",
    "encyklopedia": "codex", "encyclopedia": "codex",
    "charyzma": "charisma", "haryzma": "charisma", "charisma": "charisma",
    "drużyna": "party", "druzyna": "party", "party": "party",
    "zaproś": "partyinvite", "zapros": "partyinvite", "invite": "partyinvite",
    "dołącz": "partyaccept", "dolacz": "partyaccept",
    "odrzuć": "partydecline", "odrzuc": "partydecline", "decline": "partydecline",
    "opuść": "partyleave", "opusc": "partyleave", "leave": "partyleave",
    "wyrzuć": "partykick", "wyrzuc": "partykick", "kick": "partykick",
    "rozwiąż": "partydisband", "rozwiaz": "partydisband", "disband": "partydisband",
    "lider": "partyleader", "leader": "partyleader",
    "zasłoń": "partyprotect", "zaslon": "partyprotect", "osłoń": "partyprotect", "oslon": "partyprotect", "protect": "partyprotect",
    "wspieraj": "assist", "assist": "assist", "pomagaj": "assist",
    "pc": "partychat", "dczat": "partychat", "partychat": "partychat",
    "multiclass": "multiclass", "multiklasa": "multiclass",
    "multiklas": "multiclass", "klasy": "multiclass",
    "odpoczywaj": "rest", "odpocznij": "rest", "odpoczynek": "rest",
    "rest": "rest", "regen": "rest", "regeneruj": "rest",
    "staty": "stats", "status": "stats",
    "hp": "hp", "health": "hp", "zdrowie": "hp", "zycie": "hp", "życie": "hp",
    "score": "score", "wynik": "score", "postac": "score", "postać": "score",
    "level": "level", "lvl": "level", "poziom": "level",
    "xp": "xp", "exp": "xp",
    "mana": "mana", "manaregen": "mana",
    "odmiana": "declension", "przypadki": "declension", "namecases": "declension", "declension": "declension",
    "skills": "skills", "umiejętności": "skills", "umiejetnosci": "skills", "zdolności": "skills", "zdolnosci": "skills",
    "spells": "spells", "spels": "spells", "spellsy": "spells", "czary": "spells", "zaklecia": "spells", "zaklęcia": "spells",
    "skillnames": "skillnames", "nazwyskilli": "skillnames", "nazwyumiejetnosci": "skillnames", "nazwyumiejętności": "skillnames",
    "skill": "skill", "umiejętność": "skill", "umiejetnosc": "skill", "zdolność": "skill", "zdolnosc": "skill",
    "cast": "skill", "rzuc": "skill", "rzuć": "skill",
    "kolejka": "skillqueue", "queue": "skillqueue", "skillqueue": "skillqueue",
    "kolejkaskilli": "skillqueue", "kolejkaumiejetnosci": "skillqueue", "kolejkaumiejętności": "skillqueue",
    "learn": "learn", "naucz": "learn", "ucz": "learn", "uczsię": "learn", "uczsie": "learn",
    "dusza": "soul", "soul": "soul",
    "portfel": "money", "wallet": "money", "saldo": "money", "pieniadze": "money", "pieniądze": "money",
    "ekwipunek": "inventory", "inv": "inventory", "i": "inventory",
    "załóż": "equip", "zaloz": "equip",
    # v0.30.16 szybkie zakładanie EQ z numerowanej listy slotu.
    "zh": "equiphead", "zz": "equipbody", "zr": "equiphands",
    "zn": "equiplegs", "zb": "equipfeet",
    "zt": "equipcharmauto", "zt1": "equipcharm", "zt2": "equipcharm2",
    "zp": "equipringauto", "zp1": "equipring1", "zp2": "equipring2", "zna": "equipnecklace",
    "zkol": "equipearringauto", "zkol1": "equipearring1", "zkol2": "equipearring2",
    "znar": "equipshoulders", "zpas": "equipbelt", "zpel": "equipcloak",
    "zkar": "equipbracers", "zrel": "equiprelic",
    # v0.30.40 czytelne skróty całego EQ; stare ultra-krótkie aliasy pozostają.
    "zhel": "equiphead", "zhelm": "equiphead", "zhełm": "equiphead",
    "zpan": "equipbody", "zpanc": "equipbody", "zpancerz": "equipbody",
    "zrek": "equiphands", "zrekawice": "equiphands", "zrękawice": "equiphands",
    "znog": "equiplegs", "zbut": "equipfeet",
    "ztal": "equipcharmauto", "zpier": "equipringauto",
    "znasz": "equipnecklace", "znas": "equipnecklace",
    "autoeq": "autoequip", "eqauto": "autoequip", "zauto": "autoequip",
    "zdejmij": "unequip", "zdejm": "unequip", "ściągnij": "unequip", "sciagnij": "unequip", "unequip": "unequip",
    "wyposażenie": "equipment", "wyposazenie": "equipment", "eq": "equipment",
    "przekaż": "giveeq", "przekaz": "giveeq", "daj": "giveeq", "give": "giveeq", "giveeq": "giveeq",
    "użyj": "use", "uzyj": "use", "use": "use",
    "sklep": "shop", "list": "shop", "lista": "shop",
    "kup": "buy",
    "mów": "say", "mow": "say", "powiedz": "say",
    "rozmawiaj": "talk",
    "oddaj": "turnin", "zdaj": "turnin",
    "turnin": "turnin", "turn-in": "turnin",
    "dostarcz": "deliver", "deliver": "deliver",
    "teachers": "teachers", "training": "teachers", "trainers": "teachers", "nauczyciele": "teachers", "trenerzy": "teachers",
    "zadania": "quests", "questy": "quests", "quest": "quests",
    "accept": "questaccept", "akceptuj": "questaccept", "przyjmij": "questaccept",
    "atakuj": "attack", "walcz": "attack", "zabij": "attack", "kill": "attack", "k": "attack",
    "combat": "combatlog", "combatlog": "combatlog", "logwalki": "combatlog", "logwalka": "combatlog",
    "consider": "consider", "con": "consider",
    "ocen": "consider", "oceń": "consider",
    "ocenmob": "consider", "oceńmob": "consider",
    "ciało": "corpse", "cialo": "corpse", "zwłoki": "corpse", "zwloki": "corpse",
    "body": "corpse", "corpse": "corpse",
    "przeszukaj": "lootcorpse", "loot": "lootcorpse", "ograb": "lootcorpse",
    "get": "getcorpseitem", "weź": "getcorpseitem", "wez": "getcorpseitem",
    "krypta": "cryptinfo", "crypt": "cryptinfo",
    "wieza": "astralinfo", "wieża": "astralinfo",
    "astral": "astralinfo", "astralna": "astralinfo",
    "wiezainfo": "astralinfo", "astralinfo": "astralinfo",
    "astralportal": "astralportal",
    "portalastralny": "astralportal",
    "portalwiezy": "astralportal", "portalwieży": "astralportal",
    "checkpointwiezy": "astralportal", "checkpointwieży": "astralportal",
    "portal": "portal", "portale": "portal",
    "portalkrypty": "portal", "portalekrypty": "portal",
    "cryptportal": "portal",
    "checkpoint": "portal", "check": "portal",
    "checkpointkrypty": "portal", "punktkrypty": "portal",
    "punktykrypty": "portal", "cryptcheckpoint": "portal",
    "uciekaj": "flee",
    "odblokuj": "unlock", "odklucz": "unlock", "unlock": "unlock",
    "zapisz": "save", "save": "save",
    "admin": "admin", "administrator": "admin",
    "wipe": "wipe", "wyczysc": "wipe", "wyczyść": "wipe", "wymaz": "wipe",
    "włóż": "put", "wloz": "put", "put": "put",
    "wyjmij": "take", "wyciągnij": "take", "wyciagnij": "take", "take": "take",
    "siatka": "net", "net": "net",
    "woda": "waterinfo", "water": "waterinfo",
    "lowisko": "waterinfo", "łowisko": "waterinfo",
    "dziennikryb": "fishjournal", "dziennik_ryb": "fishjournal",
    "fishjournal": "fishjournal", "fishlog": "fishjournal",
    "sakwa": "bag", "worek": "bag", "bag": "bag",
    "wędkuj": "fish", "wedkuj": "fish", "łów": "fish", "low": "fish",
    # Jedna nawigacja: polskie i angielskie nazwy trafiają do guide.
    "prowadź": "guide", "prowadz": "guide", "guide": "guide",
    "walk": "guide", "walkto": "guide", "go": "guide",
    "idź": "guide", "idz": "guide", "nawiguj": "guide", "navigate": "guide",
    "lokalizacja": "location", "lokacja": "location", "location": "location",
    "kop": "mine", "wydobywaj": "mine",
    "kopalnia": "mineinfo", "mineinfo": "mineinfo",
    "glebokosc": "mineinfo", "głębokość": "mineinfo",
    "tnij": "woodcut", "drwal": "woodcut", "woodcut": "woodcut", "saw": "woodcut",
    "drewno": "woodpile", "stos": "woodpile", "woodpile": "woodpile",
    "zbieraj": "herb", "zbierz": "herb", "zielarstwo": "herb", "herbalism": "herb",
    "zioła": "herbbag", "ziola": "herbbag", "herbs": "herbbag", "herbbag": "herbbag",
    "szkatułka": "craftbox", "szkatulka": "craftbox", "craftbox": "craftbox",
    "materialy": "craftbox", "materiały": "craftbox",
    "rozloz": "salvage", "rozłóż": "salvage", "salvage": "salvage", "recycleeq": "salvage",
    "przekuj": "reforge", "reforge": "reforge",
    "ulepsz": "equpgrade", "ulepszaj": "equpgrade", "upgrade": "equpgrade",
    "upgradeeq": "equpgrade", "ulepszeq": "equpgrade", "ulepsz_eq": "equpgrade",
    "runy": "runes", "runes": "runes", "runa": "socketrune", "socketrune": "socketrune",
    # v0.9.26: system graczy nazywa się Gildia. Stare klan/clan są tylko zgodnościowymi aliasami.
    "gildia": "playerguild", "guild": "playerguild", "guilda": "playerguild",
    "klan": "playerguild", "clan": "playerguild",
    "osiagnieciaklasowe": "masteryachievements", "osiągnięciaklasowe": "masteryachievements",
    "osiagnieciaprofesji": "masteryachievements", "osiągnięciaprofesji": "masteryachievements",
    "masteryachievements": "masteryachievements",
    "alchemia": "alchemy", "alchemy": "alchemy", "warz": "alchemy", "warzenie": "alchemy",
    "jubilerstwo": "jewelcraftinginfo", "jewelcrafting": "jewelcraftinginfo",
    "jub": "jewelcraft", "jubcraft": "jewelcraft",
    "kamienie": "gems", "klejnoty": "gems", "gems": "gems",
    "geody": "geodes", "geodes": "geodes", "geoda": "geodes", "geode": "geodes",
    "opengeode": "geodeopen", "otworzgeode": "geodeopen", "otwórzgeodę": "geodeopen",
    "szlifuj": "cutgem", "oszlifuj": "cutgem", "cutgem": "cutgem",
    "osadz": "socketgem", "osadź": "socketgem", "socket": "socketgem",
    "gniazda": "gemsockets", "sockety": "gemsockets", "sockets": "gemsockets",
    "bizuteria": "jewelcraftinginfo", "biżuteria": "jewelcraftinginfo",
    "sprzedaj": "sell", "sell": "sell",
    "receptury": "recipes", "przepisy": "recipes", "recipes": "recipes",
    "rzemiosło": "recipes", "rzemioslo": "recipes",
    "przetop": "smelt", "przetapiaj": "smelt", "smelt": "smelt",
    "konwersje": "materialconversion", "materialconversion": "materialconversion", "conversions": "materialconversion",
    "refine": "refine", "rafinuj": "refine", "rafinacja": "refine",
    "socketcraft": "socketcraft", "dodajgniazdo": "socketcraft", "dodaj_gniazdo": "socketcraft",
    "vmaxupgrade": "vmaxupgrade", "vmaxulepsz": "vmaxupgrade",
    "techsety": "techsets", "techsets": "techsets",

    "techupgrade": "techupgrade", "techulepsz": "techupgrade", "techupgradeeq": "techupgrade",
    "partyquest": "partyquest", "questparty": "partyquest", "druzynaquest": "partyquest", "drużynaquest": "partyquest",
    "dungeonbonus": "dungeonbonus", "bonusloch": "dungeonbonus", "bonuslochu": "dungeonbonus",
    "kowalstwo": "blacksmithinginfo",
    "blacksmithing": "blacksmithinginfo",
    "smithing": "blacksmithinginfo",
    "kuj": "craft", "wykuj": "craft",
    "stwórz": "craft", "stworz": "craft", "wytwórz": "craft", "wytworz": "craft", "craft": "craft",
    "gotuj": "cook", "ugotuj": "cook", "cook": "cook",
    "gotowanie": "cookinginfo", "kuchnia": "cookinginfo",
    "cooking": "cookinginfo",
    "profesje": "professions",
    "rangi": "ranks", "ranks": "ranks", "rangiprofesji": "ranks", "professionranks": "ranks",
    "narzędzia": "tools", "narzedzia": "tools",
    "wędka": "toolinfo_fishing", "wedka": "toolinfo_fishing", "rod": "toolinfo_fishing",
    "kilof": "toolinfo_mining", "pickaxe": "toolinfo_mining",
    "piła": "toolinfo_woodcutting", "pila": "toolinfo_woodcutting",
    "młot": "toolinfo_crafting", "mlot": "toolinfo_crafting", "hammer": "toolinfo_crafting",
    "nóż": "toolinfo_cooking", "noz": "toolinfo_cooking", "knife": "toolinfo_cooking",
    "sierp": "toolinfo_herbalism", "sickle": "toolinfo_herbalism",
    "moździerz": "toolinfo_alchemy", "mozdzierz": "toolinfo_alchemy", "mortar": "toolinfo_alchemy",
    "szczypce": "toolinfo_jewelcrafting",
    "szczypcejubilerskie": "toolinfo_jewelcrafting",
    "pliers": "toolinfo_jewelcrafting",
    "tiers": "tiers", "tiery": "tiers", "tiernazwy": "tiers", "nazwytierow": "tiers", "nazwytierów": "tiers",
    # Bezpieczna nawigacja dla gracza niewidomego.
    "cofnij": "dungeonexit", "wstecz": "dungeonexit", "back": "dungeonexit", "return": "dungeonexit",
    "wyjście": "dungeonexit", "wyjscie": "dungeonexit",
    "wyjdź": "dungeonexit", "wyjdz": "dungeonexit",
    "exit": "dungeonexit", "dungeonexit": "dungeonexit",
    "escape": "dungeonexit",

    # Jednoznaczne wylogowanie po zmianie znaczenia słowa wyjście.
    "wyloguj": "quit", "koniec": "quit", "logout": "quit",
    "quitgame": "quit", "quit": "quit",

    # Popularne angielskie odpowiedniki brakujące wcześniej.
    "areas": "expareas", "grindingareas": "expareas",
    "levelingareas": "expareas", "levelareas": "expareas",
    "terraininfo": "terraininfo", "regioninfo": "terraininfo",
    "areainfo": "terraininfo",
    "sets": "classsets", "set": "classsets",
    "classset": "classsets", "classsets": "classsets",
    "profession": "professions", "professions": "professions",
    "tool": "tools", "tools": "tools",
    "questlog": "quests", "quests": "quests",
    "trainers": "teachers", "teachers": "teachers",
    "woodcutting": "woodcut", "chop": "woodcut",
    "gather": "herb", "gatherherbs": "herb",
    "jewelry": "jewelcraftinginfo", "jewellery": "jewelcraftinginfo",
    "gildiaklasowa": "classguild", "gildia_klasowa": "classguild", "classguild": "classguild",
    "reputacja": "classguild", "reputation": "classguild",
    "zadanieklasowe": "guildquest",
    "classquest": "guildquest",
    "egzamin": "guildexam",
    "exam": "guildexam",
    "bounty": "bounty",
    "zlecenie": "bounty",
    "zlecenia": "bounty",
    "contracts": "bounty",
    "kontrakty": "bounty",
    "contract": "bounty",
    "tablicazlecen": "bounty",
    "tablica_zlecen": "bounty",
    "guildbounty": "guildbounty",
    "zleceniagildii": "guildbounty",
    "zleceniegildii": "guildbounty",
    "skrzynia": "chest",
    "skarb": "chest",
    "chest": "chest",
    "treasure": "chest",
    "otworz": "chest",
    "otwórz": "chest",
    "open": "chest",
    "otworzskrzynie": "chest",
    "otwórzskrzynię": "chest",

    # v0.30.55 - pełne angielskie aliasy dla nowszych rzemiosł.
    "tailoring": "krawiectwo", "tailor": "krawiectwo",
    "sew": "szyj", "sewing": "szyj",
    "leatherworking": "garbarstwo", "leatherwork": "garbarstwo",
    "tan": "garbuj", "tanning": "garbuj",
    "carpentry": "stolarstwo", "woodworking": "stolarstwo",
    "woodcraft": "stolarka", "carpenter": "stolarstwo",
    "enchanting": "zaklinanie", "enchantinginfo": "zaklinanie",
    "enchantitem": "zaklinaj", "enchant": "zaklinaj",
    "craftmastery": "craftmastery", "craftingmastery": "craftmastery",
    "leaderboard": "leaderboards", "rankings": "leaderboards",
    "collections": "collection2", "completionpercent": "completion",
    "deathsummary": "deathrecap", "combatsummary": "combatrecap",
    "loothistory": "loothistory",

}

ITEMS = {
    "healing_potion": {
        "name": "Mikstura leczenia", "type": "consumable", "price": 24, "currency": "silver",
        "desc": "Przywraca 35 punktów życia podczas walki.", "heal": 35,
    },
    "soul_elixir": {
        "name": "Eliksir Duszy", "type": "consumable", "price": None,
        "desc": "Daje 80 Soul XP.", "soul_xp": 80,
    },
    "leather_vest": {
        "name": "Skórzana kamizelka", "type": "armor", "slot": "body", "defense": 2,
        "price": 48, "currency": "silver", "desc": "Lekki pancerz. Obrona +2.",
    },
    "iron_helmet": {
        "name": "Żelazny hełm", "type": "armor", "slot": "head", "defense": 2,
        "price": 90, "currency": "silver",
        "desc": "Hełm kowalskiego zestawu. Slot głowa. Obrona fizyczna +2.",
    },
    "iron_guard": {
        "name": "Żelazny napierśnik", "type": "armor", "slot": "body", "defense": 4,
        "price": 180, "currency": "silver",
        "desc": "Główna część kowalskiego zestawu. Slot korpus. Obrona fizyczna +4.",
    },
    "iron_gauntlets": {
        "name": "Żelazne rękawice", "type": "armor", "slot": "hands", "defense": 1,
        "price": 70, "currency": "silver",
        "desc": "Rękawice kowalskiego zestawu. Slot dłonie. Obrona fizyczna +1.",
    },
    "iron_leggings": {
        "name": "Żelazne nogawice", "type": "armor", "slot": "legs", "defense": 3,
        "price": 130, "currency": "silver",
        "desc": "Osłona nóg kowalskiego zestawu. Slot nogi. Obrona fizyczna +3.",
    },
    "iron_boots": {
        "name": "Żelazne buty", "type": "armor", "slot": "feet", "defense": 1,
        "price": 70, "currency": "silver",
        "desc": "Buty kowalskiego zestawu. Slot stopy. Obrona fizyczna +1.",
    },
    "forge_charm": {
        "name": "Talizman Kowala", "type": "armor", "slot": "charm", "defense": 1,
        "price": 110, "currency": "silver",
        "desc": "Hartowany talizman ochronny. Slot talizman. Obrona fizyczna +1.",
    },
    "lucky_charm": {
        "name": "Talizman Wędrowca", "type": "armor", "slot": "charm", "defense": 1,
        "price": 72, "currency": "silver", "desc": "Drobny talizman. Obrona +1.",
    },
    "fishing_rod": {
        "name": "Wędka", "type": "tool", "tool_type": "fishing",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Wędkarstwa. Ma własny level 1-400 i 40 Tierów.",
    },
    "pickaxe": {
        "name": "Kilof", "type": "tool", "tool_type": "mining",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Górnictwa. Ma własny level 1-400 i 40 Tierów.",
    },
    "saw": {
        "name": "Piła", "type": "tool", "tool_type": "woodcutting",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Drwalstwa. Ma własny level 1-400 i 40 Tierów.",
    },
    "crafting_hammer": {
        "name": "Młot Rzemieślniczy", "type": "tool", "tool_type": "crafting",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Rzemiosła. Ma własny level 1-400, XP i 40 Tierów.",
    },
    "chef_knife": {
        "name": "Nóż Kucharski", "type": "tool", "tool_type": "cooking",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Gotowania. Ma własny level 1-400, XP i 40 Tierów.",
    },
    "herbalist_sickle": {
        "name": "Sierp Zielarski", "type": "tool", "tool_type": "herbalism",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Zielarstwa. Ma własny level 1-400, XP i 40 Tierów.",
    },
    "alchemy_mortar": {
        "name": "Moździerz Alchemiczny", "type": "tool", "tool_type": "alchemy",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Alchemii. Ma własny level 1-400, XP i 40 Tierów.",
    },
    "nettle": {"name": "Pokrzywa", "type": "resource", "price": None, "sell_silver": 5, "desc": "Pospolite zioło lecznicze."},
    "chamomile": {"name": "Rumianek", "type": "resource", "price": None, "sell_silver": 7, "desc": "Łagodne zioło lecznicze."},
    "mint": {"name": "Mięta", "type": "resource", "price": None, "sell_silver": 8, "desc": "Aromatyczne zioło."},
    "sage": {"name": "Szałwia", "type": "resource", "price": None, "sell_silver": 12, "desc": "Silne zioło alchemiczne."},
    "lavender": {"name": "Lawenda", "type": "resource", "price": None, "sell_silver": 14, "desc": "Pachnące zioło."},
    "yarrow": {"name": "Krwawnik", "type": "resource", "price": None, "sell_silver": 16, "desc": "Zioło lecznicze."},
    "lemon_balm": {"name": "Melisa", "type": "resource", "price": None, "sell_silver": 18, "desc": "Zioło przydatne w miksturach Many."},
    "valerian": {"name": "Kozłek", "type": "resource", "price": None, "sell_silver": 25, "desc": "Leśne zioło."},
    "ginseng": {"name": "Żeń-szeń", "type": "resource", "price": None, "sell_silver": 40, "desc": "Cenny korzeń alchemiczny."},
    "nightshade": {"name": "Wilcza jagoda", "type": "resource", "price": None, "sell_silver": 55, "desc": "Rzadkie zioło alchemiczne."},
    "mandrake": {"name": "Mandragora", "type": "resource", "price": None, "sell_gold": 1, "desc": "Rzadki magiczny korzeń."},
    "moonflower": {"name": "Kwiat księżycowy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Magiczny kwiat."},
    "soulroot": {"name": "Korzeń duszy", "type": "resource", "price": None, "sell_gold": 3, "desc": "Korzeń nasycony energią dusz."},
    "phoenix_leaf": {"name": "Liść feniksa", "type": "resource", "price": None, "sell_gold": 5, "desc": "Bardzo rzadki liść."},
    "star_moss": {"name": "Gwiezdny mech", "type": "resource", "price": None, "sell_gold": 8, "desc": "Rzadki magiczny mech."},
    "astral_lotus": {"name": "Astralny lotos", "type": "resource", "price": None, "sell_gold": 15, "desc": "Mityczne zioło."},
    "mana_potion": {"name": "Mikstura Many", "type": "consumable", "price": None, "mana": 35, "desc": "Przywraca do 35 Many."},
    "greater_healing_potion": {"name": "Wielka Mikstura Leczenia", "type": "consumable", "price": None, "heal": 70, "desc": "Przywraca do 70 HP."},
    "greater_mana_potion": {"name": "Wielka Mikstura Many", "type": "consumable", "price": None, "mana": 70, "desc": "Przywraca do 70 Many."},
    "vitality_elixir": {"name": "Eliksir Witalności", "type": "consumable", "price": None, "heal": 55, "mana": 30, "desc": "Przywraca do 55 HP i 30 Many."},
    "fallen_branch": {"name": "Suche gałęzie", "type": "resource", "price": None, "sell_silver": 6, "desc": "Najprostszy materiał drwala."},
    "birch_log": {"name": "Pień brzozy", "type": "resource", "price": None, "sell_silver": 10, "desc": "Lekkie drewno brzozowe."},
    "pine_log": {"name": "Pień sosny", "type": "resource", "price": None, "sell_silver": 15, "desc": "Pospolite drewno sosnowe."},
    "willow_log": {"name": "Pień wierzby", "type": "resource", "price": None, "sell_silver": 22, "desc": "Miękkie drewno wierzby."},
    "oak_log": {"name": "Pień dębu", "type": "resource", "price": None, "sell_silver": 40, "desc": "Twarde drewno dębowe."},
    "beech_log": {"name": "Pień buku", "type": "resource", "price": None, "sell_silver": 55, "desc": "Mocne drewno bukowe."},
    "maple_log": {"name": "Pień klonu", "type": "resource", "price": None, "sell_silver": 70, "desc": "Cenne drewno klonowe."},
    "ash_log": {"name": "Pień jesionu", "type": "resource", "price": None, "sell_silver": 90, "desc": "Sprężyste drewno jesionowe."},
    "cedar_log": {"name": "Pień cedru", "type": "resource", "price": None, "sell_silver": 130, "desc": "Aromatyczne drewno cedrowe."},
    "yew_log": {"name": "Pień cisu", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadkie drewno cisu."},
    "ironwood_log": {"name": "Pień żelaznego drzewa", "type": "resource", "price": None, "sell_gold": 5, "desc": "Niezwykle twarde drewno."},
    "ebony_log": {"name": "Pień hebanu", "type": "resource", "price": None, "sell_gold": 8, "desc": "Ciężkie i bardzo cenne drewno."},
    "silverwood_log": {"name": "Pień srebrnego drzewa", "type": "resource", "price": None, "sell_gold": 10, "desc": "Magiczne srebrzyste drewno."},
    "spiritwood_log": {"name": "Pień drzewa duchów", "type": "resource", "price": None, "sell_gold": 15, "desc": "Drewno nasycone energią dusz."},
    "ancient_heartwood": {"name": "Pradawna twardziel", "type": "resource", "price": None, "sell_gold": 30, "desc": "Rdzeń bardzo starego drzewa."},
    "worldtree_wood": {"name": "Drewno Drzewa Świata", "type": "resource", "price": None, "sell_gold": 75, "desc": "Mityczny materiał dla najlepszych drwali."},
    "iron_ingot": {
        "name": "Żelazna sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione żelazo używane w recepturach rzemieślniczych.",
    },
    "silver_ingot": {
        "name": "Srebrna sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione srebro używane w lepszych recepturach.",
    },
    "gold_ingot": {
        "name": "Złota sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione złoto używane w zaawansowanych recepturach.",
    },
    "oak_plank": {
        "name": "Deska dębowa", "type": "craft_material", "price": None,
        "desc": "Obrobiona deska z drewna dębowego.",
    },
    "ash_plank": {
        "name": "Deska jesionowa", "type": "craft_material", "price": None,
        "desc": "Sprężysta deska jesionowa.",
    },
    "yew_plank": {
        "name": "Deska cisowa", "type": "craft_material", "price": None,
        "desc": "Rzadka deska z drewna cisu.",
    },
    "ironwood_plank": {
        "name": "Deska żelaznego drzewa", "type": "craft_material", "price": None,
        "desc": "Bardzo twarda deska z żelaznego drzewa.",
    },
    "spiritwood_plank": {
        "name": "Deska drzewa duchów", "type": "craft_material", "price": None,
        "desc": "Magiczna deska nasycona energią dusz.",
    },
    "oak_iron_charm": {
        "name": "Talizman Dębu i Żelaza", "type": "armor", "slot": "charm",
        "defense": 2, "price": None,
        "desc": "Wytwarzany talizman. Slot talizman. Obrona fizyczna +2.",
    },
    "yew_silver_charm": {
        "name": "Talizman Cisu i Srebra", "type": "armor", "slot": "charm",
        "defense": 3, "price": None,
        "desc": "Rzadki wytwarzany talizman. Slot talizman. Obrona fizyczna +3.",
    },
    "spiritwood_gold_charm": {
        "name": "Talizman Drzewa Dusz", "type": "armor", "slot": "charm",
        "defense": 5, "price": None,
        "desc": "Zaawansowany talizman z magicznego drewna i złota. Obrona fizyczna +5.",
    },
    "grilled_river_fish": {
        "name": "Pieczona ryba rzeczna", "type": "consumable", "price": None,
        "heal": 30,
        "desc": "Prosta potrawa. Przywraca do 30 HP.",
    },
    "river_fish_stew": {
        "name": "Gulasz rzeczny", "type": "consumable", "price": None,
        "heal": 45,
        "desc": "Syta potrawa z ryb rzecznych. Przywraca do 45 HP.",
    },
    "lake_fish_stew": {
        "name": "Potrawka jeziorowa", "type": "consumable", "price": None,
        "heal": 50, "mana": 10,
        "desc": "Potrawa z ryb jeziorowych. Przywraca do 50 HP i 10 Many.",
    },
    "sea_chowder": {
        "name": "Zupa morska", "type": "consumable", "price": None,
        "heal": 60, "mana": 15,
        "desc": "Gęsta zupa morska. Przywraca do 60 HP i 15 Many.",
    },
    "ocean_steak": {
        "name": "Stek oceaniczny", "type": "consumable", "price": None,
        "heal": 75, "mana": 25,
        "desc": "Potężna potrawa z ryb oceanu. Przywraca do 75 HP i 25 Many.",
    },
    "master_fisher_feast": {
        "name": "Uczta Mistrza Rybaka", "type": "consumable", "price": None,
        "heal": 100, "mana": 40,
        "desc": "Wielka uczta z czterech środowisk. Przywraca do 100 HP i 40 Many.",
    },

    "herb_crusted_perch": {
        "name": "Okoń w Ziołowej Skorupce",
        "type": "consumable",
        "price": None,
        "heal": 42,
        "mana": 5,
        "desc": "Lekka potrawa rybna z Miętą. Przywraca do 42 HP i 5 Many.",
    },
    "silver_trout_soup": {
        "name": "Zupa ze Srebrnego Pstrąga",
        "type": "consumable",
        "price": None,
        "heal": 52,
        "mana": 12,
        "desc": "Gorąca zupa z pstrąga i Szałwii. Przywraca do 52 HP i 12 Many.",
    },
    "lake_fisher_pie": {
        "name": "Zapiekanka Jeziornego Rybaka",
        "type": "consumable",
        "price": None,
        "heal": 62,
        "mana": 18,
        "desc": "Treściwa zapiekanka z ryb jeziorowych. Przywraca do 62 HP i 18 Many.",
    },
    "spiced_mackerel": {
        "name": "Makrela Korzenna",
        "type": "consumable",
        "price": None,
        "heal": 72,
        "mana": 22,
        "desc": "Makrela doprawiona Szałwią. Przywraca do 72 HP i 22 Many.",
    },
    "salmon_herb_plate": {
        "name": "Łosoś z Ziołami",
        "type": "consumable",
        "price": None,
        "heal": 88,
        "mana": 30,
        "desc": "Łosoś z Lawendą. Przywraca do 88 HP i 30 Many.",
    },
    "moon_eel_broth": {
        "name": "Rosół z Księżycowego Węgorza",
        "type": "consumable",
        "price": None,
        "heal": 112,
        "mana": 48,
        "desc": "Rzadka potrawa z Księżycowego Węgorza i Kwiatu księżycowego. Przywraca do 112 HP i 48 Many.",
    },

    # Nowe ryby v0.6.98 - rzeka
    "river_bleak": {"name": "Ukleja Rzeczna", "type": "resource", "price": None, "sell_silver": 4, "desc": "Mała rzeczna ryba. Wędka level 1+."},
    "stone_loach": {"name": "Śliz Kamienny", "type": "resource", "price": None, "sell_silver": 6, "desc": "Niewielka ryba denna rzeki. Wędka level 5+."},
    "river_bream": {"name": "Krąp Rzeczny", "type": "resource", "price": None, "sell_silver": 10, "desc": "Pospolita ryba rzeczna. Wędka level 15+."},
    "brown_trout": {"name": "Pstrąg Potokowy", "type": "resource", "price": None, "sell_silver": 18, "desc": "Szybka ryba czystych rzek. Wędka level 30+."},
    "river_taimen": {"name": "Tajmień Rzeczny", "type": "resource", "price": None, "sell_silver": 34, "desc": "Duży drapieżnik rzeczny. Wędka level 50+."},
    "emerald_barbel": {"name": "Szmaragdowa Brzana", "type": "resource", "price": None, "sell_silver": 60, "desc": "Rzadka brzana o zielonym połysku. Wędka level 75+."},
    "spirit_grayling": {"name": "Lipień Duchów", "type": "resource", "price": None, "sell_gold": 2, "desc": "Magiczny lipień. Wędka level 110+."},
    "bloodfin_salmon": {"name": "Krwawopłetwy Łosoś", "type": "resource", "price": None, "sell_gold": 5, "desc": "Rzadki łosoś endgame. Wędka level 150+."},
    "star_river_eel": {"name": "Gwiezdny Węgorz Rzeczny", "type": "resource", "price": None, "sell_gold": 12, "desc": "Węgorz nasycony energią gwiazd. Wędka level 175+."},
    "eternal_river_dragon": {"name": "Wieczny Smok Rzeczny", "type": "resource", "price": None, "sell_gold": 35, "desc": "Legendarny drapieżnik rzeki. Wędka level 200."},

    # Nowe ryby v0.6.98 - jezioro
    "lake_gudgeon": {"name": "Kiełb Jeziorowy", "type": "resource", "price": None, "sell_silver": 5, "desc": "Mała ryba przybrzeżna jeziora. Wędka level 1+."},
    "lake_smelt": {"name": "Stynka Jeziorowa", "type": "resource", "price": None, "sell_silver": 7, "desc": "Drobna srebrzysta ryba jeziorowa. Wędka level 8+."},
    "blue_bream": {"name": "Niebieski Leszcz", "type": "resource", "price": None, "sell_silver": 12, "desc": "Rzadziej spotykany leszcz. Wędka level 20+."},
    "golden_tench": {"name": "Złoty Lin", "type": "resource", "price": None, "sell_silver": 22, "desc": "Cenny lin jeziorowy. Wędka level 35+."},
    "deepwater_pike": {"name": "Szczupak Głębinowy", "type": "resource", "price": None, "sell_silver": 40, "desc": "Duży szczupak z głębokich partii jeziora. Wędka level 55+."},
    "crystal_whitefish": {"name": "Kryształowa Sieja", "type": "resource", "price": None, "sell_silver": 70, "desc": "Jasna magiczna sieja. Wędka level 80+."},
    "moon_carp": {"name": "Karp Księżycowy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Karp aktywny przy blasku księżyca. Wędka level 110+."},
    "astral_pike": {"name": "Astralny Szczupak", "type": "resource", "price": None, "sell_gold": 6, "desc": "Endgame drapieżnik jeziorowy. Wędka level 150+."},
    "mirror_sturgeon": {"name": "Lustrzany Jesiotr", "type": "resource", "price": None, "sell_gold": 14, "desc": "Rzadki jesiotr z lustrzanymi łuskami. Wędka level 175+."},
    "eternal_lake_serpent": {"name": "Wieczny Wąż Jeziora", "type": "resource", "price": None, "sell_gold": 38, "desc": "Legendarny mieszkaniec najgłębszej toni. Wędka level 200."},

    # Nowe ryby v0.6.98 - morze
    "sand_eel": {"name": "Dobijak Piaskowy", "type": "resource", "price": None, "sell_silver": 5, "desc": "Mała ryba przybrzeżna morza. Wędka level 1+."},
    "garfish": {"name": "Belona", "type": "resource", "price": None, "sell_silver": 8, "desc": "Długa ryba morska. Wędka level 10+."},
    "sea_bream": {"name": "Prażma Morska", "type": "resource", "price": None, "sell_silver": 14, "desc": "Smaczna ryba morska. Wędka level 20+."},
    "bluefish": {"name": "Lufar", "type": "resource", "price": None, "sell_silver": 25, "desc": "Waleczny morski drapieżnik. Wędka level 35+."},
    "conger_eel": {"name": "Konger", "type": "resource", "price": None, "sell_silver": 45, "desc": "Duży węgorz morski. Wędka level 55+."},
    "red_snapper": {"name": "Lucjan Czerwony", "type": "resource", "price": None, "sell_silver": 80, "desc": "Cenna ryba morska. Wędka level 80+."},
    "storm_herring": {"name": "Śledź Burzy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Ryba pojawiająca się przy wzburzonym morzu. Wędka level 110+."},
    "abyss_conger": {"name": "Konger Otchłani", "type": "resource", "price": None, "sell_gold": 7, "desc": "Mroczny endgame węgorz morski. Wędka level 150+."},
    "void_sole": {"name": "Sola Pustki", "type": "resource", "price": None, "sell_gold": 15, "desc": "Rzadka płastuga nasycona Pustką. Wędka level 175+."},
    "eternal_sea_drake": {"name": "Wieczny Smok Morza", "type": "resource", "price": None, "sell_gold": 40, "desc": "Legendarny morski drapieżnik. Wędka level 200."},

    # Nowe ryby v0.6.98 - ocean
    "flying_fish": {"name": "Ryba Latająca", "type": "resource", "price": None, "sell_silver": 8, "desc": "Szybka ryba otwartego oceanu. Wędka level 1+."},
    "bonito": {"name": "Bonito", "type": "resource", "price": None, "sell_silver": 12, "desc": "Mały krewniak tuńczyka. Wędka level 15+."},
    "yellowfin_tuna": {"name": "Tuńczyk Żółtopłetwy", "type": "resource", "price": None, "sell_silver": 24, "desc": "Popularny oceaniczny tuńczyk. Wędka level 30+."},
    "king_mackerel": {"name": "Makrela Królewska", "type": "resource", "price": None, "sell_silver": 42, "desc": "Duża makrela otwartego oceanu. Wędka level 50+."},
    "marlin_black": {"name": "Marlin Czarny", "type": "resource", "price": None, "sell_silver": 78, "desc": "Potężny oceaniczny drapieżnik. Wędka level 70+."},
    "opah": {"name": "Strojnik Oceaniczny", "type": "resource", "price": None, "sell_gold": 1, "desc": "Rzadka głębinowa ryba oceanu. Wędka level 90+."},
    "celestial_swordfish": {"name": "Niebiański Miecznik", "type": "resource", "price": None, "sell_gold": 4, "desc": "Magiczny miecznik endgame. Wędka level 120+."},
    "astral_sunfish": {"name": "Astralny Samogłów", "type": "resource", "price": None, "sell_gold": 9, "desc": "Ogromny samogłów nasycony Astralem. Wędka level 150+."},
    "void_marlin": {"name": "Marlin Pustki", "type": "resource", "price": None, "sell_gold": 18, "desc": "Skrajnie rzadka ryba oceaniczna. Wędka level 180+."},
    "world_leviathan": {"name": "Lewiatan Świata", "type": "resource", "price": None, "sell_gold": 50, "desc": "Legendarny szczyt oceanicznego połowu. Wędka level 200."},

    "small_fish": {
        "name": "Mała ryba", "type": "resource", "price": None,
        "desc": "Pospolity połów z płytkiej wody.", "sell_silver": 8,
    },
    "river_carp": {
        "name": "Karp rzeczny", "type": "resource", "price": None,
        "desc": "Solidna ryba rzeczna.", "sell_silver": 20,
    },
    "silver_trout": {
        "name": "Srebrny pstrąg", "type": "resource", "price": None,
        "desc": "Rzadsza ryba o srebrzystych łuskach.", "sell_silver": 55,
    },
    "golden_trout": {
        "name": "Złoty pstrąg", "type": "resource", "price": None,
        "desc": "Cenny połów dostępny przy lepszej wędce.", "sell_gold": 1,
    },
    "ancient_sturgeon": {
        "name": "Pradawny jesiotr", "type": "resource", "price": None,
        "desc": "Bardzo duża i cenna ryba.", "sell_gold": 3,
    },
    "moon_eel": {
        "name": "Księżycowy węgorz", "type": "resource", "price": None,
        "desc": "Niezwykle rzadki połów z wysokiego poziomu Wędkarstwa.", "sell_gold": 8,
    },
    "herring": {
        "name": "Śledź", "type": "resource", "price": None,
        "desc": "Morska ryba dostępna dopiero od levelu 30 Wędki.", "sell_gold": 1,
    },
    "mackerel": {
        "name": "Makrela", "type": "resource", "price": None,
        "desc": "Szybka ryba morska.", "sell_gold": 2,
    },
    "salmon": {
        "name": "Łosoś", "type": "resource", "price": None,
        "desc": "Cenny połów z rozwiniętego Wędkarstwa.", "sell_gold": 5,
    },
    "tuna": {
        "name": "Tuńczyk", "type": "resource", "price": None,
        "desc": "Duży i cenny połów oceaniczny. Wędka level 80+.",
        "sell_gold": 15,
    },
    "swordfish": {
        "name": "Miecznik", "type": "resource", "price": None,
        "desc": "Rzadki i silny morski okaz.", "sell_gold": 30,
    },
    "bluefin_tuna": {
        "name": "Tuńczyk błękitnopłetwy", "type": "resource", "price": None,
        "desc": "Bardzo rzadki tuńczyk dostępny na wysokim levelu Wędki.", "sell_gold": 75,
    },
    "reef_shark": {
        "name": "Rekin rafowy", "type": "resource", "price": None,
        "desc": "Rzadki rekin możliwy do złowienia dopiero bardzo dobrą Wędką.", "sell_gold": 125,
    },
    "hammerhead_shark": {
        "name": "Rekin młot", "type": "resource", "price": None,
        "desc": "Bardzo rzadki rekin dla mistrzów Wędkarstwa.", "sell_gold": 250,
    },
    "great_white_shark": {
        "name": "Żarłacz biały", "type": "resource", "price": None,
        "desc": "Ekstremalnie rzadki okaz dla najwyższych leveli Wędki.", "sell_gold": 500,
    },
    "ghost_marlin": {
        "name": "Widmowy marlin", "type": "resource", "price": None,
        "desc": "Legendarny połów dostępny jedynie mistrzom Wędkarstwa.", "sell_mithril": 1,
    },
    "sardine": {
        "name": "Sardynka", "type": "resource", "price": None,
        "desc": "Niewielka morska ryba ławicowa.", "sell_silver": 35,
    },
    "anchovy": {
        "name": "Sardela", "type": "resource", "price": None,
        "desc": "Mała ryba morska spotykana w dużych ławicach.", "sell_silver": 45,
    },
    "cod": {
        "name": "Dorsz", "type": "resource", "price": None,
        "desc": "Cenna ryba morska o jasnym mięsie.", "sell_gold": 3,
    },
    "sea_bass": {
        "name": "Labraks", "type": "resource", "price": None,
        "desc": "Drapieżna ryba morska ceniona przez kupców.", "sell_gold": 4,
    },
    "haddock": {
        "name": "Plamiak", "type": "resource", "price": None,
        "desc": "Krewniak dorsza, trudniejszy do złowienia.", "sell_gold": 6,
    },
    "pollock": {
        "name": "Mintaj", "type": "resource", "price": None,
        "desc": "Silna ryba morska z chłodnych wód.", "sell_gold": 8,
    },
    "flounder": {
        "name": "Flądra", "type": "resource", "price": None,
        "desc": "Płaska ryba denna wymagająca lepszej Wędki.", "sell_gold": 10,
    },
    "halibut": {
        "name": "Halibut", "type": "resource", "price": None,
        "desc": "Duża i droga ryba denna.", "sell_gold": 20,
    },
    "river_perch": {"name": "Okoń rzeczny", "type": "resource", "price": None, "sell_silver": 14, "desc": "Pospolity drapieżnik rzeczny."},
    "barbel": {"name": "Brzana", "type": "resource", "price": None, "sell_silver": 25, "desc": "Silna ryba nurtu rzecznego."},
    "pike": {"name": "Szczupak", "type": "resource", "price": None, "sell_silver": 60, "desc": "Duży słodkowodny drapieżnik."},
    "zander": {"name": "Sandacz", "type": "resource", "price": None, "sell_silver": 85, "desc": "Cenny drapieżnik słodkowodny."},
    "river_catfish": {"name": "Sum rzeczny", "type": "resource", "price": None, "sell_gold": 3, "desc": "Wielki mieszkaniec głębokiej rzeki."},
    "lake_roach": {"name": "Płoć jeziorowa", "type": "resource", "price": None, "sell_silver": 10, "desc": "Pospolita ryba jeziorowa."},
    "bream": {"name": "Leszcz", "type": "resource", "price": None, "sell_silver": 20, "desc": "Popularna ryba jezior."},
    "tench": {"name": "Lin", "type": "resource", "price": None, "sell_silver": 35, "desc": "Ryba spokojnych, zarośniętych jezior."},
    "lake_perch": {"name": "Okoń jeziorowy", "type": "resource", "price": None, "sell_silver": 45, "desc": "Drapieżnik jeziorowy."},
    "lake_trout": {"name": "Troć jeziorowa", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadka duża ryba chłodnych jezior."},
    "giant_pike": {"name": "Olbrzymi szczupak", "type": "resource", "price": None, "sell_gold": 6, "desc": "Bardzo stary szczupak."},
    "freshwater_eel": {"name": "Węgorz jeziorowy", "type": "resource", "price": None, "sell_gold": 8, "desc": "Rzadki węgorz z głębin jeziora."},
    "turbot": {"name": "Turbot", "type": "resource", "price": None, "sell_gold": 6, "desc": "Cenna ryba denna morza."},
    "mahi_mahi": {"name": "Mahi-mahi", "type": "resource", "price": None, "sell_gold": 10, "desc": "Szybka ryba oceaniczna."},
    "wahoo": {"name": "Wahoo", "type": "resource", "price": None, "sell_gold": 15, "desc": "Bardzo szybki drapieżnik oceanu."},
    "sailfish": {"name": "Żaglica", "type": "resource", "price": None, "sell_gold": 25, "desc": "Ekstremalnie szybka ryba oceaniczna."},
    "ocean_sunfish": {"name": "Samogłów oceaniczny", "type": "resource", "price": None, "sell_gold": 40, "desc": "Ogromna ryba otwartego oceanu."},
    # Dodatkowe ryby rzeczne
    "dace": {"name": "Jelec", "type": "resource", "price": None, "sell_silver": 12, "desc": "Mała szybka ryba rzeczna."},
    "chub": {"name": "Kleń", "type": "resource", "price": None, "sell_silver": 18, "desc": "Pospolita, silna ryba rzeczna."},
    "common_nase": {"name": "Świnka", "type": "resource", "price": None, "sell_silver": 22, "desc": "Ryba czystych, płynących wód."},
    "ide": {"name": "Jaź", "type": "resource", "price": None, "sell_silver": 32, "desc": "Cenna ryba większych rzek."},
    "asp": {"name": "Boleń", "type": "resource", "price": None, "sell_silver": 70, "desc": "Szybki drapieżnik rzeczny."},
    "grayling": {"name": "Lipień", "type": "resource", "price": None, "sell_silver": 90, "desc": "Cenna ryba chłodnych rzek."},
    "burbot": {"name": "Miętus", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadki denny drapieżnik rzeczny."},

    # Dodatkowe ryby jeziorowe
    "rudd": {"name": "Wzdręga", "type": "resource", "price": None, "sell_silver": 14, "desc": "Kolorowa ryba spokojnych jezior."},
    "crucian_carp": {"name": "Karaś", "type": "resource", "price": None, "sell_silver": 18, "desc": "Wytrzymała ryba jeziorowa."},
    "vendace": {"name": "Sielawa", "type": "resource", "price": None, "sell_silver": 55, "desc": "Ryba chłodnych, czystych jezior."},
    "whitefish": {"name": "Sieja", "type": "resource", "price": None, "sell_gold": 1, "desc": "Cenna ryba głębokich jezior."},
    "lake_char": {"name": "Palia jeziorowa", "type": "resource", "price": None, "sell_gold": 3, "desc": "Rzadki drapieżnik zimnych jezior."},

    # Dodatkowe ryby morskie
    "sprat": {"name": "Szprot", "type": "resource", "price": None, "sell_silver": 8, "desc": "Mała ryba morska żyjąca w ławicach."},
    "whiting": {"name": "Witlinek", "type": "resource", "price": None, "sell_silver": 32, "desc": "Pospolita ryba morska."},
    "hake": {"name": "Morszczuk", "type": "resource", "price": None, "sell_silver": 85, "desc": "Drapieżna ryba morska."},
    "red_mullet": {"name": "Barwena", "type": "resource", "price": None, "sell_gold": 2, "desc": "Cenna morska ryba przydenna."},
    "sole": {"name": "Sola", "type": "resource", "price": None, "sell_gold": 4, "desc": "Cenna płaska ryba morska."},
    "monkfish": {"name": "Żabnica", "type": "resource", "price": None, "sell_gold": 9, "desc": "Duży morski drapieżnik głębinowy."},

    # Dodatkowe ryby oceaniczne
    "albacore": {"name": "Albakora", "type": "resource", "price": None, "sell_gold": 12, "desc": "Oceaniczny gatunek tuńczyka."},
    "bigeye_tuna": {"name": "Tuńczyk wielkooki", "type": "resource", "price": None, "sell_gold": 20, "desc": "Cenny tuńczyk głębokiego oceanu."},
    "barracuda": {"name": "Barakuda", "type": "resource", "price": None, "sell_gold": 18, "desc": "Szybki oceaniczny drapieżnik."},
    "cobia": {"name": "Kobia", "type": "resource", "price": None, "sell_gold": 22, "desc": "Duża ryba otwartego morza i oceanu."},
    "amberjack": {"name": "Seriola", "type": "resource", "price": None, "sell_gold": 28, "desc": "Silna oceaniczna ryba sportowa."},
    "mako_shark": {"name": "Rekin mako", "type": "resource", "price": None, "sell_gold": 180, "desc": "Bardzo szybki i rzadki rekin oceaniczny."},
    "tiger_shark": {"name": "Rekin tygrysi", "type": "resource", "price": None, "sell_gold": 300, "desc": "Wielki, bardzo rzadki drapieżnik oceaniczny."},

    # Dodatkowe gatunki drewna
    "alder_log": {"name": "Pień olchy", "type": "resource", "price": None, "sell_silver": 12, "desc": "Drewno lubiące wilgotne tereny."},
    "poplar_log": {"name": "Pień topoli", "type": "resource", "price": None, "sell_silver": 18, "desc": "Lekkie i łatwe w obróbce drewno."},
    "linden_log": {"name": "Pień lipy", "type": "resource", "price": None, "sell_silver": 28, "desc": "Miękkie drewno cenione przez rzemieślników."},
    "chestnut_log": {"name": "Pień kasztana", "type": "resource", "price": None, "sell_silver": 110, "desc": "Twarde, trwałe drewno."},
    "walnut_log": {"name": "Pień orzecha", "type": "resource", "price": None, "sell_gold": 2, "desc": "Cenne ciemne drewno orzechowe."},
    "mahogany_log": {"name": "Pień mahoniu", "type": "resource", "price": None, "sell_gold": 6, "desc": "Szlachetne, ciemnoczerwone drewno."},
    "teak_log": {"name": "Pień teku", "type": "resource", "price": None, "sell_gold": 9, "desc": "Bardzo trwałe i odporne drewno."},
    "redwood_log": {"name": "Pień sekwoi", "type": "resource", "price": None, "sell_gold": 18, "desc": "Ogromne i rzadkie drewno ze starych drzew."},

    "stone_chunk": {
        "name": "Odłamek skały", "type": "resource", "price": None,
        "desc": "Pospolity urobek.", "sell_silver": 3,
    },
    "copper_ore": {
        "name": "Ruda miedzi", "type": "resource", "price": None,
        "desc": "Podstawowa ruda górnicza.", "sell_silver": 12,
    },
    "iron_ore": {
        "name": "Ruda żelaza", "type": "resource", "price": None,
        "desc": "Użyteczna ruda metalu.", "sell_silver": 35,
    },
    "silver_ore": {
        "name": "Ruda srebra", "type": "resource", "price": None,
        "desc": "Cenniejsza ruda wydobywana lepszym kilofem.", "sell_gold": 1,
    },
    "gold_ore": {
        "name": "Ruda złota", "type": "resource", "price": None,
        "desc": "Rzadka i cenna ruda.", "sell_gold": 4,
    },
    "mithril_ore": {
        "name": "Stary mithrilowy urobek", "type": "legacy", "price": None,
        "desc": "Przedmiot legacy z v0.34.3. Nie wypada już w kopalni; mithril jest walutą.",
        "sell_silver": 500,
    },
    "soul_shard": {
        "name": "Odłamek Duszy", "type": "quest", "price": None,
        "desc": "Niestabilny odłamek znaleziony przy istotach z krypty.",
    },
    "wolf_fang": {
        "name": "Kieł Wilka Cienia", "type": "loot", "price": None,
        "desc": "Ciemny kieł pulsujący słabą energią.",
    },
}


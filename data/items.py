# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
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
        "desc": "Podstawowe narzędzie do Wędkarstwa. Ma własny level 1-600 i 60 Tierów.",
    },
    "pickaxe": {
        "name": "Kilof", "type": "tool", "tool_type": "mining",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Górnictwa. Ma własny level 1-600 i 60 Tierów.",
    },
    "saw": {
        "name": "Piła", "type": "tool", "tool_type": "woodcutting",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Drwalstwa. Ma własny level 1-600 i 60 Tierów.",
    },
    "crafting_hammer": {
        "name": "Młot Rzemieślniczy", "type": "tool", "tool_type": "crafting",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Rzemiosła. Ma własny level 1-600, XP i 60 Tierów.",
    },
    "chef_knife": {
        "name": "Nóż Kucharski", "type": "tool", "tool_type": "cooking",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Gotowania. Ma własny level 1-600, XP i 60 Tierów.",
    },
    "herbalist_sickle": {
        "name": "Sierp Zielarski", "type": "tool", "tool_type": "herbalism",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Zielarstwa. Ma własny level 1-600, XP i 60 Tierów.",
    },
    "alchemy_mortar": {
        "name": "Moździerz Alchemiczny", "type": "tool", "tool_type": "alchemy",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Alchemii. Ma własny level 1-600, XP i 60 Tierów.",
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
        "desc": "Niestabilny odłamek znaleziony przy istotach z krypty. Służy także jako składnik craftingu duszy, run i socketów.",
    },
    "wolf_fang": {
        "name": "Kieł Wilka Cienia", "type": "loot", "price": None,
        "desc": "Ciemny kieł pulsujący słabą energią.",
    },
}

__all__ = ['ITEMS']

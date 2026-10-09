from data import catalog_mutations as _catalog_mut

def normalize_recipe_requirements_v0866():
    """v0.8.66: receptury blokuje profesja, nigdy level narzędzia."""
    alchemy_defaults = {
        "mana_potion": 1,
        "healing_potion": 5,
        "greater_healing_potion": 40,
        "greater_mana_potion": 60,
        "vitality_elixir": 80,
        "soul_elixir": 90,
    }
    for recipes in (CRAFT_RECIPES, COOK_RECIPES, ALCHEMY_RECIPES, JEWELCRAFT_RECIPES):
        for recipe_id, recipe in recipes.items():
            fallback = recipe.get("min_tool_level")
            if recipes is ALCHEMY_RECIPES:
                fallback = alchemy_defaults.get(recipe_id, fallback)
            if not recipe.get("min_profession_level"):
                recipe["min_profession_level"] = max(1, int(fallback or 1))
            # Od v0.8.66 receptura nie ma już wymogu levelu narzędzia.
            # Narzędzie musi istnieć, ale jego level służy zasobom/jakości.
            recipe.pop("min_tool_level", None)


normalize_recipe_requirements_v0866()

# v0.9.15: osobna Szkatułka Rzemieślnicza przechowuje wszystkie
# półprodukty rzemieślnicze (sztabki, deski itd.) oraz gotowe materiały
# jubilerskie po obróbce, np. oszlifowane klejnoty. Surowe kamienie
# z Górnictwa nadal trafiają do Sakwy Górnika aż do ich oszlifowania.
# Ryby, rudy, drewno i zioła zachowują własne magazyny profesji.
CRAFT_MATERIAL_STORAGE_IDS = frozenset(
    item_id for item_id, item in ITEMS.items()
    if item.get("type") == "craft_material" or item_id in CUT_GEM_IDS
)

from data.npcs import NPCS


_catalog_mut.catalog_assign({
    "name": "Jubilerka Mirella",
    "room": "jeweler_workshop",
    "rank_profession": "Jubilerstwo",
    "dialogue": (
        "W mojej pracowni kupisz Szczypce Jubilerskie. "
        "Uczę Jubilerstwa od levelu 1 do 400 i prowadzę "
        "dziewięć etapów zleceń na pierścienie oraz naszyjniki."
    ),
    "shopkeeper": True,
    "specialist_tool_type": "jewelcrafting",
    "specialist_topic": "jubilerstwo",
    "specialist_recipes": "receptury jubilerstwo",
    "quest": "mirella_jewel_iron",
    "specialist_quests": (
        "mirella_jewel_iron",
        "mirella_jewel_silver",
        "mirella_jewel_gold",
        "mirella_jewel_cobalt",
        "mirella_jewel_runic",
        "mirella_jewel_dragonsteel",
        "mirella_jewel_astral",
        "mirella_jewel_void",
        "mirella_jewel_eternium",
    ),
}, 'NPCS', NPCS, ("jeweler_mirella",))

_catalog_mut.catalog_update_path('NPCS', NPCS, (), {
    "guild_quartermaster_martial": {
        "name": "Kwatermistrz Varek",
        "room": "guild_martial_hall",
        "dialogue": (
            "Prowadzę skład wyposażenia Wojowników i Berserkerów. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_shadow": {
        "name": "Kwatermistrzyni Lysa",
        "room": "guild_shadow_gallery",
        "dialogue": (
            "Prowadzę skład wyposażenia Łotrzyków i Łowców. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_body": {
        "name": "Kwatermistrz Omir",
        "room": "guild_body_hall",
        "dialogue": (
            "Prowadzę skład wyposażenia Mnichów i Strażników. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_arcane": {
        "name": "Kwatermistrzyni Selene",
        "room": "guild_arcane_chamber",
        "dialogue": (
            "Prowadzę skład wyposażenia Magów i Psioników oraz sprzedaję "
            "Fokus Runiczny potrzebny do Zaklinania. Wpisz list albo shop."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_dark": {
        "name": "Kwatermistrz Veyran",
        "room": "guild_dark_chamber",
        "dialogue": (
            "Prowadzę skład wyposażenia Nekromantów i Czarowników. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_sanctuary": {
        "name": "Kwatermistrz Elandor",
        "room": "guild_sanctuary",
        "dialogue": (
            "Prowadzę skład wyposażenia Kapłanów i Druidów. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
})


NPC_DESCRIPTIONS = {
    "fisher_tomas": (
        "Doświadczony rybak z Targu Rybnego. Uczy podstaw Wędkarstwa i nagradza "
        "graczy, którzy udowodnią cierpliwość przy połowie."
    ),
    "lumberjack_bran": (
        "Doświadczony drwal prowadzący Obóz Drwala. "
        "Jako jedyny sprzedaje Piłę potrzebną do Drwalstwa."
    ),
    "miner_toren": (
        "Doświadczony górnik stojący przy wejściu do Kryształowej Jaskini. "
        "Zleca próbę Górnictwa polegającą na dostarczeniu 30 dowolnych rud."
    ),
    "herbalist_liora": (
        "Zielarka i alchemiczka mieszkająca w Chacie Zielarki. "
        "Sprzedaje Sierp Zielarski i Moździerz Alchemiczny oraz zleca próbę Zielarstwa na 30 ziół."
    ),
    "specialist_fishing": (
        "Specjalista Wędkarstwa na Targu Rybnym. Wyjaśnia rozwój Wędki, "
        "Tier narzędzia i dostęp do ryb wysokiego levelu."
    ),
    "market_trader_radan": (
        "Handlarz działający na Rynku. Skupuje łupy, trofea i niezałożone EQ. "
        "Nie skupuje zasobów profesyjnych i materiałów rzemieślniczych, takich jak "
        "ryby, rudy, minerały, drewno i zioła."
    ),
    "specialist_mining": (
        "Specjalista Górnictwa przy wejściu do Kryształowej Jaskini. "
        "Wyjaśnia rozwój Kilofa, Tier narzędzia i progi rud endgame."
    ),
    "specialist_woodcutting": (
        "Specjalista Drwalstwa w Obozie Drwala. Wyjaśnia rozwój Piły "
        "i dostęp do coraz rzadszych gatunków drewna."
    ),
    "specialist_crafting": (
        "Specjalista Rzemiosła w Kuźni Dusz. Pomaga śledzić rozwój "
        "Młota Rzemieślniczego i przypomina komendę receptury craft."
    ),
    "specialist_cooking": (
        "Kucharz w Karczmie Pod Błękitnym Płomieniem. Pomaga rozwijać "
        "Nóż Kucharski i korzystać z receptur Gotowania."
    ),
    "specialist_herbalism": (
        "Specjalistka Zielarstwa w Chacie Zielarki. Wyjaśnia rozwój "
        "Sierpa Zielarskiego i progi rzadkich ziół."
    ),
    "specialist_alchemy": (
        "Specjalista Alchemii w Chacie Zielarki. Pomaga rozwijać "
        "Moździerz Alchemiczny i przypomina receptury Alchemii."
    ),
    "banker_aldren": (
        "Bankier na Rynku. Obsługuje trwałe konto bankowe na srebro, "
        "złoto, mithril i zwykłe przedmioty z inventory."
    ),
    "priest_elor": (
        "Kapłan Świątyni Odrodzenia. Prowadzi wszystkie Próby Broni Duszy dla Tierów 2-40. "
        "Pierwsze próby są początkujące, później przechodzą przez bossów regionalnych, Kryptę i endgame 201-400."
    ),
    "captain_arven": (
        "Dowódca miejskiej straży. Zleca zadania związane z bezpieczeństwem dróg, "
        "strażnic i okolic Miasta Dusz."
    ),
    "watch_commander_roderik": (
        "Dowódca Wartowni Północnej. Organizuje powtarzalne patrole przeciw bandytom "
        "z Obozowiska Bandytów."
    ),
    "frontier_guard_anna": (
        "Strażniczka z Wartowni Pogranicza. Ostrzega podróżnych przed bandytami "
        "i wskazuje drogę do ich obozowiska."
    ),
    "mira": (
        "Zielarka mieszkająca w Gaju Szeptów. Zna dzicz i reaguje na zagrożenia "
        "naruszające równowagę natury."
    ),
    "doran": (
        "Kowal z Kuźni Dusz. Sprzedaje pełny żelazny zestaw ochronny na głowę, korpus, "
        "dłonie, nogi, stopy i slot talizmanu, a także Kilof. Interesuje się Odłamkami Duszy."
    ),
    "innkeeper": (
        "Karczmarka prowadząca Błękitny Płomień. Sprzedaje podstawowe zapasy i "
        "udziela prostych informacji podróżnym."
    ),
    "archivist": (
        "Archiwista Biblioteki Kronik. Wyjaśnia zasady świata, w którym rozwój "
        "postaci odbywa się przez statystyki, a nie przez level bohatera."
    ),
    "teacher_warrior": "Nauczyciel klasy Wojownik w Sali Gildii.",
    "teacher_berserker": "Nauczycielka klasy Berserker w Sali Gildii.",
    "teacher_rogue": "Nauczyciel klasy Łotrzyk w Sali Gildii.",
    "teacher_hunter": "Nauczycielka klasy Łowca w Sali Gildii.",
    "teacher_monk": "Nauczyciel klasy Mnich w Sali Gildii.",
    "teacher_guardian": "Nauczyciel klasy Strażnik w Sali Gildii.",
    "teacher_mage": "Nauczyciel klasy Mag w Sali Gildii.",
    "teacher_necromancer": "Nauczycielka klasy Nekromanta w Sali Gildii.",
    "teacher_priest": "Nauczyciel klasy Kapłan w Sali Gildii.",
    "teacher_warlock": "Nauczycielka klasy Czarownik w Sali Gildii.",
    "teacher_druid": "Nauczyciel klasy Druid w Sali Gildii.",
    "teacher_psion": "Nauczycielka klasy Psionik w Sali Gildii.",
}

MOB_DESCRIPTIONS = {
    "temple_rat": "Mały, szybki szkodnik z piwnicy świątyni. Dobry pierwszy przeciwnik.",
    "training_dummy": "Magicznie ożywiony manekin przeznaczony do bezpiecznego treningu walki.",
    "goblin": "Lekko uzbrojony goblin nękający drogi i ruiny poza miastem.",
    "goblin_brute": "Silniejszy goblin nastawiony na ciężkie, fizyczne uderzenia.",
    "goblin_scout": "Szybki gobliński zwiadowca pilnujący wejścia do podziemnych tuneli.",
    "goblin_spearman": "Goblin walczący długą włócznią i trzymający przeciwnika na dystans.",
    "goblin_archer": "Łucznik ukrywający się za barykadami Jaskiń Goblinów.",
    "goblin_shaman": "Gobliński szaman używający prymitywnej, ale groźnej magii.",
    "goblin_bomber": "Goblin noszący gliniane bomby i łatwopalne mieszanki.",
    "goblin_cave_guard": "Ciężej opancerzony strażnik głębokich korytarzy.",
    "goblin_warrior": "Doświadczony wojownik należący do osobistej straży króla.",
    "goblin_warchief": "Wódz wojenny dowodzący obroną wewnętrznych Jaskiń Goblinów.",
    "shadow_wolf": "Drapieżnik skażony energią cienia. Szybszy i groźniejszy od zwykłej bestii.",
    "bandit": "Rozbójnik czatujący na podróżnych na Starym Trakcie.",
    "bandit_scout": "Lekki zwiadowca obserwujący drogi prowadzące do obozowiska.",
    "bandit_crossbowman": "Bandyta używający kuszy i walczący zza barykad.",
    "bandit_cutthroat": "Szybki rzezimieszek uzbrojony w krótkie ostrza.",
    "bandit_raider": "Doświadczony rabusiów karawan, twardszy od zwykłych bandytów.",
    "bandit_alchemist": "Obozowy alchemik używający toksycznych i magicznych mieszanek.",
    "bandit_enforcer": "Ciężko uzbrojony egzekutor pilnujący wewnętrznego obozu.",
    "bandit_veteran": "Weteran wielu napadów, należący do najgroźniejszych ludzi Herszta.",
    "bandit_captain": "Kapitan obozu dowodzący strażą przed namiotem Herszta.",
    "skeleton": "Nieumarły strażnik krypty. Wytrzymały przeciwnik walczący fizycznie.",
    "crypt_wraith": "Magiczny nieumarły z głębi krypty. Jego ataki sprawdzają obronę magiczną.",
    "crystal_guardian": "Potężny magiczny strażnik Kryształowej Komnaty. Zadaje obrażenia magiczne.",
    "ruin_watchman": "Ożywiony wartownik dawnej strażnicy. Walczy mieczem i nadal pilnuje wyznaczonego posterunku.",
    "ruin_spearman": "Nieumarły włócznik Starej Straży, groźniejszy i bardziej wytrzymały od zwykłego wartownika.",
    "ruin_crossbowman": "Dawny kusznik garnizonu. Jego fizyczne ataki są silniejsze od ataków zwykłych wartowników.",
    "ruin_shieldbearer": "Ciężko opancerzony tarczownik dawnego garnizonu, przeznaczony do obrony wąskich przejść.",
    "ruin_runekeeper": "Runiczny strażnik podtrzymywany starą magią ochronną Strażnicy.",
    "ruin_wraith": "Widmo poległego wartownika. Atakuje magią i nawiedza podziemne części garnizonu.",
    "ruin_gargoyle": "Kamienny obserwator ożywiony przez dawne pieczęcie obronne.",
    "ruin_goblin_looter": "Gobliński szabrownik przeszukujący opuszczone koszary i piwnice w poszukiwaniu metalu oraz kosztowności.",
    "ruin_captain": "Kapitan Starej Straży. Mini-boss dowodzący pozostałymi obrońcami wewnętrznych ruin.",
}

STAT_DESCRIPTIONS = {
    "siła": "Siła zwiększa obrażenia fizyczne postaci.",
    "sila": "Siła zwiększa obrażenia fizyczne postaci.",
    "strength": "Siła zwiększa obrażenia fizyczne postaci.",
    "zręczność": (
        "Zręczność zwiększa Szybkość. Wyższa Szybkość zwiększa szansę uniknięcia "
        "kontrataku. Aktualny limit uniku wynosi 35 procent."
    ),
    "zrecznosc": (
        "Zręczność zwiększa Szybkość. Wyższa Szybkość zwiększa szansę uniknięcia "
        "kontrataku. Aktualny limit uniku wynosi 35 procent."
    ),
    "dexterity": (
        "Zręczność zwiększa Szybkość, unik i szansę na trafienie krytyczne. Przy 10 Zręczności krytyk ma 5 procent; do 40 Zręczności każdy punkt daje +0,5 punktu procentowego, od 41 do 80 +0,25, a powyżej 80 +0,10, do limitu 35 procent."
    ),
    "kondycja": "Kondycja zwiększa maksymalne HP. Każdy punkt Kondycji daje 5 maksymalnego HP.",
    "constitution": "Kondycja zwiększa maksymalne HP. Każdy punkt Kondycji daje 5 maksymalnego HP.",
    "inteligencja": "Inteligencja zwiększa maksymalną Manę każdej klasy; w klasach magicznych zwiększa też główną Moc czarów.",
    "intelligence": "Inteligencja zwiększa maksymalną Manę każdej klasy; w klasach magicznych zwiększa też główną Moc czarów.",
    "siła woli": "Siła Woli zwiększa obronę magiczną.",
    "sila woli": "Siła Woli zwiększa obronę magiczną.",
    "willpower": "Siła Woli zwiększa obronę magiczną.",
    "charyzma": (
        "Charyzma zwiększa rabat sklepowy i limit drużyny lidera. "
        "Ma własny niezależny EXP i własny próg jak pozostałe statystyki; "
        "sprzedaż przyznaje EXP Charyzmy zależny od wartości transakcji."
    ),
    "haryzma": (
        "Charyzma zwiększa rabat sklepowy i limit drużyny lidera. "
        "Ma własny niezależny EXP i własny próg jak pozostałe statystyki; "
        "sprzedaż przyznaje EXP Charyzmy zależny od wartości transakcji."
    ),
    "charisma": (
        "Charyzma zwiększa rabat sklepowy i limit drużyny lidera. "
        "Ma własny niezależny EXP i własny próg jak pozostałe statystyki; "
        "sprzedaż przyznaje EXP Charyzmy zależny od wartości transakcji."
    ),
}

SYSTEM_DESCRIPTIONS = {
    "wędkarstwo": (
        "Wędkarstwo ma własny poziom profesji. Do połowu potrzebna jest Wędka, która ma "
        "osobny level 1-400 i osobny XP. Podstawową Wędkę kupisz u Rybaka Borysa na Targu Rybnym. "
        "Użyj fish albo low. Auto-łowienie: low on i low off. "
        "Czas połowu zależy od Wędkarstwa: 16 sekund na poziomie 1 i minimum 3 sekundy na poziomie 200."
    ),
    "wedkarstwo": (
        "Wędkarstwo ma własny poziom profesji. Do połowu potrzebna jest Wędka, która ma "
        "osobny level 1-400 i osobny XP. Podstawową Wędkę kupisz u Rybaka Borysa na Targu Rybnym. "
        "Użyj fish albo low. Auto-łowienie: low on i low off. "
        "Czas połowu zależy od Wędkarstwa: 16 sekund na poziomie 1 i minimum 3 sekundy na poziomie 200."
    ),
    "fishing": "Wędkarstwo ma własny poziom profesji 1-400, a Wędka własny niezależny level 1-400. Podstawową Wędkę sprzedaje Rybak Borys. Czas połowu spada z 16 do minimum 3 sekund wraz z poziomem Wędkarstwa.",
    "górnictwo": (
        "Górnictwo ma własny poziom 1-400. Kilof ma osobny level 1-400. "
        "Użyj mine albo kop. Auto-kopanie: kop on i kop off. "
        "Mithril jest walutą i może wypaść jako dodatkowy bonus od Kilofa 80, Górnictwa 80 i poziomu kopalni 80. "
        "Od Kilofa 20 mogą wypadać geody; open geode / otwórz geodę otwiera je na klejnoty."
    ),
    "gornictwo": (
        "Górnictwo ma własny poziom 1-400. Kilof ma osobny level 1-400. "
        "Mithril jest walutą i może wypaść jako dodatkowy bonus od Kilofa 80, Górnictwa 80 i poziomu kopalni 80."
    ),
    "mining": "Górnictwo ma własny poziom 1-400 i do 200 skraca czas wydobycia; Kilof ma niezależny level 1-400 i odblokowuje lepsze rudy/żyły.",
    "jubilerstwo": (
        "Jubilerstwo ma własny level 1-400. "
        "Szczypce Jubilerskie mają niezależny level 1-400 i 40 Tierów. "
        "Biżuterię wykonujesz w Pracowni Jubilerskiej u Mirelli."
    ),
    "jewelcrafting": (
        "Jubilerstwo 1-400. Narzędzie: Szczypce Jubilerskie 1-400. "
        "Receptury tworzą pierścienie i naszyjniki."
    ),
    "broń duszy": (
        "Broń Duszy jest na stałe związana z klasą. Ma osobny Soul Level 1-400, Soul XP i 40 Tierów. "
        "Od v0.9.0 bazowa Moc startowa klas mieści się w zakresie 7-8, a dalsza przewaga wynika z Soul Levelu, Tieru i specjalizacji klasy. "
        "Łotrzyk otrzymuje z Broni Duszy mieszany bonus: umiarkowany unik oraz obrażenia fizyczne, żeby progres nie był marnowany na limicie 35 procent uniku. "
        "Każdy awans Soul Tieru 2-40 wymaga jednorazowej Próby Broni Duszy u Kapłana Elora. "
        "Trudność rośnie pasmami: T2-4 Początkująca, T5-7 Poszukiwacza, T8-12 Weterana, T13-20 Mistrzowska, T21-40 endgame."
    ),
    "bron duszy": "Broń Duszy ma Soul Level 1-400, 40 Tierów i zbalansowaną bazową Moc startową 7-8.",
    "soul weapon": "Broń Duszy ma Soul Level 1-400, 40 Tierów i zbalansowaną bazową Moc startową 7-8.",
    "próby duszy": (
        "Próby Broni Duszy odblokowują Tiery 2-40 u Kapłana Elora. "
        "Pasma trudności: T2-4 Początkująca, T5-7 Poszukiwacza, T8-12 Weterana, "
        "T13-20 Mistrzowska, T21-30 Endgame, T31-40 Ekstremalna. "
        "Pierwsze siedem Tierów nie wymagają bossów Krypty; od T8 pojawiają się bossowie regionalni, "
        "a ciężkie Próby Krypty zaczynają się od T13. Użyj dusza info, aby sprawdzić stan każdej Próby."
    ),
    "proby duszy": "Próby Broni Duszy mają pasma trudności od początkujących T2-4 do ekstremalnych T31-40. Użyj dusza info.",
    "soul trials": "Próby Broni Duszy mają pasma trudności od początkujących T2-4 do ekstremalnych T31-40. Użyj dusza info.",
    "srebro": "Srebro jest najmniejszym nominałem wspólnej waluty. 100 srebra = 1 złoto.",
    "silver": "Srebro jest najmniejszym nominałem wspólnej waluty. 100 srebra = 1 złoto.",
    "złoto": "Złoto jest wyższym nominałem tego samego salda. 1 złoto = 100 srebra.",
    "zloto": "Złoto jest wyższym nominałem tego samego salda. 1 złoto = 100 srebra.",
    "gold": "Złoto jest wyższym nominałem tego samego salda. 1 złoto = 100 srebra.",
    "mithril": (
        "Mithril jest najwyższym nominałem tego samego wspólnego salda. "
        "1 mithril = 1 000 000 złota = 100000000 srebra. "
        "Może być nagrodą lub bardzo rzadkim bezpośrednim wydobyciem wysokopoziomowym Kilofem."
    ),
    "siatka": "Siatka na ryby jest osobnym trwałym magazynem profesji. Komenda siatka/net pokazuje też łączną liczbę ryb, liczbę gatunków i szacowany zarobek ze sprzedaży całej zawartości. Sprzedaż ryb właściwym rybakom daje dodatkowy EXP Wędkarstwa.",
    "net": "Siatka na ryby przechowuje wszystkie złowione ryby i pokazuje łączną liczbę ryb oraz wartość sprzedaży całej siatki.",
    "sakwa": "Sakwa Górnika przechowuje cały urobek Górnictwa: rudy, minerały, klejnoty wszystkich jakości oraz geody. Całą zawartość skupuje wyłącznie Dagna na Górskim Targu Minerałów. Sprzedaż Dagnie daje dodatkowy EXP Górnictwa; geody możesz zamiast tego otwierać.",
    "bag": "Sakwa Górnika przechowuje rudy, minerały, surowe klejnoty i geody. Dagna jest jedynym skupującym zawartość sakwy; geody otwierasz przez open geode / otwórz geodę.",
    "śmierć": (
        "Po śmierci postać odradza się w Świątyni Odrodzenia i traci 10 procent "
        "wartości wspólnego salda."
    ),
    "smierc": "Po śmierci postać odradza się w Świątyni Odrodzenia i traci 10 procent wartości wspólnego salda.",
    "death": "Po śmierci postać odradza się w Świątyni Odrodzenia i traci część waluty.",
}


LATEST_CHANGES_TITLE = "Soulbound v1.40.0 - STABILNOSC WALKI I NAGROD"
LATEST_CHANGES = [
    "v1.40.0: ochrona przed podwojnym rozliczeniem tego samego zabojstwa przy rownoleglym AoE, ataku i najemnikach; testy 24 pomocnikow, wygaszania i ponownego odrodzenia bossa.",
    "Nowa bramka validation/v1400_combat_stability.py w predeploy; bez zmian nagrod EXP, obrazen, profesji i danych graczy.",
    "v1.39.0: test 4 wirtualnych graczy, zapisow SQLite, profesji, ekwipunku i skalowania walki. Wyniki: validation/v1390_world_stress.py. Balans i zapisy bez zmian.",
    "Poprawiono nieaktualne opisy narzędzi 1-600 / 60 Tierów na faktyczny zakres 1-800 / 80 Tierów oraz pomoc questów walki bez Generator Core.",
    "v1.37.1: admin blad naprawiony/otworz ID, admin log aktywne/naprawione/podglad oraz czyszczenie wyłącznie oznaczonych błędów z potwierdzeniem.",
    "Rejestr błędów SB w SQLite: migracja bez utraty historii, audyt działań admina, bez usuwania logów Railway i aktywnych zgłoszeń.",
    "v1.37.0: 492 trwałe legendarne osiągnięcia. Retroaktywny postęp klas, profesji, postaci, Duszy, Broni Duszy, walki, odkryć, kontraktów i handlu.",
    "Nagrody w postaci unikalnych tytułów, bez zwiększania EXP lub psucia ekonomii. Kronika postaci i osobne rekordy serwera. Stronicowanie pod NVDA.",
    "Komendy: medale, medale rozwoj, klasy, profesje, wyczyny, brakujace, kronika postaci, rekordy, osiagniecia legendarne.",
    "v1.36.0: Gospodarka 4.0. Karawany PvE ladowe i morskie, wielkie zamowienia rzemieslnicze, produkcja gildii i szescio-godzinne ceny kontraktow.",
    "Transakcje SQLite: pobieranie materialow z ekwipunku i magazynow, wyplaty jednokrotne, bez podwojnego odbioru, bez resetow poziomow lub czasu lowienia.",
    "Komendy: gospodarka pomoc, ceny, karawany, wyslij, transport, obron, odbierz, zamowienia, wykonaj, produkcja, rozbuduj, zbierz, rekordy.",
    "v1.35.0: Ocean 4.0 - PvE flot, eskorty 2 okretow, starcia z korsarzami, blokada morska i 3 morskimi potworami.",
    "Bitwy trwale zapisywane w SQLite; abordaz przeciw okretom, naprawy w porcie, nagrody tylko raz za zwyciestwo, 2-godzinny odpoczynek flot.",
    "Komendy: ocean4 pomoc, ocean4 flota, ocean4 eskorta, ocean4 cele, ocean4 atak, ocean4 rozkaz, ocean4 napraw, ocean4 rekordy.",
    "v1.34.0: jedna gildia kontra frakcje NPC (PvE). Garnizony, wyprawy odwetowe, kontrataki, rozwój terytoriów i raporty. Bez zmian zapisów postaci.",
    'v1.33.2: ewolucje zależne od rodzaju skilla: obrażenia, leczenie, obszarówki, guard, regen i automatyczne boosty. Nie zmieniamy zapisów ani limitów.',
    'Rada Starożytnych: wspólna arena Smoka Korony Burz i Olbrzyma Pierwszych Kuźni, pomoc sojusznika w walce, uzdrawianie i koordynowane ciosy.',
    'Dojście: Sanktuarium Smoka, wschód, północ. Komenda dziedzictwo skille pokazuje specjalizację każdego poznanego skilla.', 
    'v1.33.0: trzy automatyczne ewolucje poznanych skilli klasowych zależne od Skill Level i Soul Level, bez resetów postaci.',
    'Broń Duszy: dodatkowy rezonans zwykłego ataku za biegłość 150/350/600, bez zmieniania XP lub szybkości ataku.',
    'Czterej Starożytni: indywidualne rotacje żywiołów, Echo Pradawnych, Rozdarcie Starożytnych; realni pomocnicy bez limitu.',
    'Komendy: dziedzictwo, dziedzictwo skille, dziedzictwo starozytni. Czytelne komunikaty pod NVDA.',

    "v1.32.1: Wieloetapowe oblężenia twierdz: brama, dziedziniec, cytadela; taktyczne rozkazy i straty; stara komenda szybkiego oblężenia zachowana.",
    "Licytacje czasowe z zabezpieczeniem ofert: 1/6/12/24/48 godzin. Przebite oferty zwracane do aukcja odbierz. Rozliczanie przenosi przedmiot i pieniądze atomowo.",
    "Stocznia: flota wielu statków, własne poziomy modułów na każdym statku, nadawanie nazw i zmiana aktywnego statku w porcie. Zapis Ocean 2.0 zachowany.",
    "v1.32.0: Armie gildii, oblężenia i mury zdobywanych twierdz, giełda aukcyjna z depozytem, statki bryg/fregata/galeon z własną stocznią.",
    "Komendy: imperium, armia, oblezenie, aukcja, stocznia. Kupno i sprzedaż także offline; odbiór zapłaty przez aukcja odbierz.",
    "Bez resetów kont, bez Generator Core, bez ruszania dotychczasowych poziomów, EXP i tras Ocean 2.0.",
    "v1.31.0: Cztery imperia z twierdzami, trzy wymiary, trzy nowe wyspy, dzielnica graczy, cztery sanktuaria Starożytnych i pięć prób Dziedzictwa Dusz.",
    "Nowe ręcznie opisane lokacje, NPC, sklepy, zadania z trwałym postępem, bossowie, materiały i Relikt Dziedzictwa Dusz. Bez resetu postaci.",
    "Handel, domy i twierdze gildii nadal korzystają z istniejących komend i zapisów; nie ma Generator Core.",
    "v1.30.1: Kraina Orków Gor-Khaz: 24 własne lokacje, NPC klanów, handel, tawerna, zadania, orcze patrole, arena, król i legendarne materiały.",
    "Naprawa przywoływania: boss przyzywa pierwszego strażnika już po rozpoczęciu walki, potem co trzy akcje bez limitu liczby żywych pomocników.",
    "Strażnicy po respawnie bossa są resetowani; specjalne skrypty superbossów UOSS działają niezależnie.",
    "v1.30.0: Podziemne Królestwo, Podniebny Archipelag i Zaginiony Kontynent: 72 ręcznie opisane lokacje, sklepy, tawerny, NPC i bossowie.",
    "Wojny: aktywny najazd co 3 godziny, walka i obrona miast zwiększają reputację frakcji i stolic.",
    "Trzy nowe superbossy i strażnicy cytadel: mechaniki faz, pomocnicy i wyjątkowe materiały.",
    "Profesje: wyższe wymagania XP (Wędkarstwo x4; pozostałe 2-2,5), bez zmiany czasu łowienia, narzędzi i zróżnicowanych nagród.",
    "Trzy nowe korony z legendarnych materiałów; żywy rynek ma ceny kontraktów zmieniające się co 6 godzin.",
    "Ekspedycje: obozy i strażnicy dokładani na żądanie co 100 pięter bez końca w kryptach, wieżach i Deep Dungeon.",
    "v1.28.12: 4 podziemne miasta z 7 połączonymi salami, działającą tawerną najemników, kupcem, kuźnią, archiwistą, powtarzalnym zadaniem i prawdziwym bossem.",
    "W archiwach: Kronika Podziemi — 6 powiązanych zadań przez krypty, wyspy, Ocean i kopalnię, finał z legendarnym medalionem.",
    "Legendarne i Mityczne zwykłe potwory mają własne techniki oraz bardzo rzadkie trofea w ciele.",
    "Mistrzowskie Rzemiosło 2.0: dodatkowa szansa awansu jakości zależna od materiałów, profesji, narzędzia i mastery.",
    "Wydarzenia: cztery rotujące co 3 godziny najazdy, atak smoka, oblężenie i starożytny boss. Prawdziwe walki na bramach miast.",
    "Globalne ogłoszenia rotacji świata, startu i końca regionalnych kryzysów. Solo lub w party.",
    "v1.28.11: Solo portal, astralportal i winda Deep Dungeon nie wymagają lidera nieobecnej drużyny.",
    "Naprawiono TypeError kop on kierunek oraz UnboundLocalError ręcznego drążenia chodników.",
    "Legendarny skarbiec i sekret dziedzictwo: wyjątkowa receptura oraz nowy craft Relikt Odkrywcy.",
    "Cztery profesje zbierackie mogą odkryć bardzo rzadkie, cenne materiały i trofea.",
    "Bossowie w nowych falach przyzywają różnych strażników: magów, tarczowników, berserkerów i uzdrowicieli, bez limitu liczby żywych pomocników.",
    "v1.28.10: SCORE pokazuje bieżący Soul XP, wymagany Soul XP i dokładny brak do następnego Soul Levelu.",
    "Przy blokadzie Soul Tier pokazuje status odblokowania, a przy Soul Level 800: maksimum.",
    "Bez zmian w wymaganiach i nagrodach EXP, walce, skrzyniach, zadaniach klasowych oraz zapisach postaci.",
    "v1.28.9: Bossowie krypt oraz pozostali zwykli bossowie przyzywają kolejnych strażników bez limitu żywych pomocników.",
    "Pierwsze przywołanie w turze 4, dalej co 7 tur. Strażnicy nadal walczą i znikają po śmierci bossa.",
    "Zadanieklasowe i zlecenia klasowe u nauczycieli odnawiają się co 2 godziny zamiast co godzinę.",
    "v1.28.8: Skrzynia stoi w komnacie żywego bossa, klucz wypada dopiero z jego ciała po zabiciu.",
    "Po otwarciu skrzynia znika; wraca, gdy boss naprawdę się odrodzi. Naprawiono też starsze piętra bez znacznika pokoju.",
    "v1.28.7: SCORE nie pokazuje już fałszywej progresji 1-600 ani nieistniejącego Generator Core; potwierdza limity 800.",
    "Zaktualizowano dusza info i pomoc podstawy / score / level / xp / dusza. EXP, skalowanie i skrzynie z v1.28.6 bez zmian.",
    "v1.28.6: Naprawiono skrzynie checkpointów w Kryptach, Mitycznych Kryptach i pozostałych piętrowych lochach: tylko komnata bossa, bez cofania do lądowania.",
    "Po zabiciu bossa skrzynia zostaje ponownie odblokowana. Działa skrzynia / chest / odklucz; po otwarciu znika dla nagrodzonych graczy.",
    "v1.28.6: Koniec wielopoziomowych awansów za zwykłego moba na głębokim piętrze.",
    "EXP z lochów zależy od poziomu otrzymującej go postaci, klasy lub Duszy, a nie od poziomu pokonanego potwora.",
    "Grind pozostaje długoterminowy: zwykli przeciwnicy dają mały stały postęp, bossowie znacznie więcej.",
    "Drużyna, najemnicy, elity i event x2 nadal działają. Zachowano wymagania EXP 1-800.",
    "Otwarty świat, zadania i źródłowe nagrody UOSS nie zostały zmienione. Generator Core pozostaje usunięty.",
]

HELP_TOPIC_ALIASES = {
    "temat": "tematy", "topics": "tematy",
    "kategorie": "kategorie", "categories": "kategorie", "category": "kategorie",
    "all": "wszystko",
    "commands": "komendy", "command": "komendy",
    "basics": "podstawy",
    "movement": "nawigacja",
    "stats": "statystyki", "stat": "statystyki",
    "odmiana": "odmiana_imienia", "przypadki": "odmiana_imienia", "namecases": "odmiana_imienia", "declension": "odmiana_imienia",
    "combat": "walka", "fight": "walka", "combatlog": "walka", "logwalki": "walka",
    "walk": "nawigacja", "guide": "nawigacja", "prowadzenie": "nawigacja", "autowalk": "nawigacja", "navigation": "nawigacja",
    "endgameprof": "endgame_profesje", "profesje200": "endgame_profesje", "receptury200": "endgame_profesje",
    "login": "logowanie", "logowanie": "logowanie", "spawn": "logowanie", "start": "logowanie",
    "critical": "krytyki", "crit": "krytyki",
    "statgrowth": "rozwoj_statystyk", "rozwojstatystyk": "rozwoj_statystyk", "rozwoj": "rozwoj_statystyk",
    "uzyjskill": "uzywanie_umiejetnosci", "uzywanieumiejetnosci": "uzywanie_umiejetnosci", "useskill": "uzywanie_umiejetnosci",
    "criticalhits": "krytyki", "krytyk": "krytyki",
    "krytyki": "krytyki",
    "respawn": "respawn", "odrodzenie": "respawn",
    "odradzanie": "respawn",
    "bosses": "bossowie", "boss": "bossowie", "bossowie": "bossowie", "herszt": "bossowie",
    "mobhp": "hp_mobow", "hpmobow": "hp_mobow", "hpprzeciwnikow": "hp_mobow",
    "bosshp": "hp_bossow_lochow", "hpbossow": "hp_bossow_lochow",
    "soul": "dusza", "soulweapon": "dusza",
    "soulxp": "soul_xp_bloki",
    "duszaexp": "soul_xp_bloki", "expsoul": "soul_xp_bloki",
    "money": "pieniadze", "economy": "pieniadze",
    "kurs": "kurs_walut", "waluty": "kurs_walut", "currency": "kurs_walut",
    "wartoscsatki": "wartosc_siatki", "wartoscsiatki": "wartosc_siatki", "netvalue": "wartosc_siatki",
    "equipment": "ekwipunek", "items": "ekwipunek",
    "rarity": "loot_krypty", "rzadkosc": "loot_krypty", "rzadkość": "loot_krypty", "set": "loot_krypty", "lootkrypty": "loot_krypty", "sety krypty": "loot_krypty",

    "professions": "profesje",
    "fishing": "wedkarstwo", "fish": "wedkarstwo",
    "laki": "laki", "laka": "laki", "meadows": "laki", "meadow": "laki",

    "codex": "codex_swiata", "kodeks": "codex_swiata",
    "kodeksklasowy": "kodeks_klasowy", "kodeks klasowy": "kodeks_klasowy",
    "classcodex": "kodeks_klasowy", "class codex": "kodeks_klasowy",
    "skillcodex": "kodeks_klasowy", "skill codex": "kodeks_klasowy",
    "rarezasoby": "rare_resources", "rzadkiezasoby": "rare_resources",
    "atlaszasobow": "atlas_kompletny", "atlaszasobów": "atlas_kompletny",
    "zasobyswiata": "zasoby_swiata", "worldresources": "zasoby_swiata",
    "roslinyswiata": "zasoby_swiata", "rybyswiata": "zasoby_swiata",
    "autooff": "auto_off", "off": "auto_off",
    "autochodzenie": "auto_chodzenie", "automove": "auto_chodzenie",
    "kopalnia": "kopalnia_200", "mine200": "kopalnia_200",
    "water": "woda", "woda": "woda", "lowisko": "woda", "łowisko": "woda",
    "dziennikryb": "dziennik_ryb", "fishjournal": "dziennik_ryb", "fishlog": "dziennik_ryb",
    "wiecejryb": "wiecej_ryb", "moreryb": "wiecej_ryb", "morefish": "wiecej_ryb",
    "turnin": "oddawanie_zadan", "oddaj": "oddawanie_zadan",
    "mining": "gornictwo", "mine": "gornictwo",
    "woodcutting": "drwalstwo", "drwal": "drwalstwo",
    "crafting": "rzemioslo", "craft": "rzemioslo", "rzemiosło": "rzemioslo",
    "cooking": "gotowanie_rozbudowane", "cook": "gotowanie_rozbudowane",
    "gotowanie": "gotowanie_rozbudowane", "kuchnia": "gotowanie_rozbudowane",
    "herbalism": "zielarstwo", "zielarstwo": "zielarstwo",
    "alchemy": "alchemia", "alchemia": "alchemia",
    "recipes": "receptury", "recipe": "receptury", "przepisy": "receptury",
    "containers": "pojemniki",
    "shops": "sklepy", "shop": "sklepy",
    "multiplayer": "gracze", "players": "gracze",
    "death": "smierc",
    "races": "rasy", "race": "rasy",
    "classes": "klasy", "class": "klasy",
    "descriptions": "opisy", "describe": "opisy",
    "skills": "umiejetnosci", "abilities": "umiejetnosci",
    "skillnames": "nazwy_skilli", "nazwyskilli": "nazwy_skilli",
    "teachers": "nauczyciele", "trainers": "nauczyciele",
    "multiclass": "multiclass", "multiklasa": "multiclass",
    "multiklas": "multiclass", "klasy": "multiclass",
    "changes": "zmiany", "changelog": "zmiany",
    "quest": "questy", "quests": "questy", "questy": "questy", "zadania": "questy",
    "corpse": "zwloki", "body": "zwloki", "cialo": "zwloki", "ciało": "zwloki",
    "loot": "zwloki", "zwloki": "zwloki", "zwłoki": "zwloki",
    "crypt": "krypta", "krypta": "krypta",
    "portal": "portale", "portals": "portale", "portale": "portale",
    "portalkrypty": "portale", "cryptportal": "portale",
    "checkpoint": "portale", "checkpoints": "portale",
    "punktkrypty": "portale", "punktykrypty": "portale",
    "atlas": "atlas", "atlasy": "atlas",
    "party": "druzyny", "parties": "druzyny", "druzyna": "druzyny", "drużyna": "druzyny",
    "zaslon": "druzyny", "zasłoń": "druzyny", "oslon": "druzyny", "osłoń": "druzyny",
    "zaproś": "druzyny", "zapros": "druzyny", "opusc": "druzyny", "opuść": "druzyny",
    "charisma": "charyzma", "charyzma": "charyzma", "haryzma": "charyzma",
    "historia": "historia", "history": "historia", "lifetime": "historia", "lifestats": "historia",
}

HELP_TOPICS = {
    "gospodarka": [
        "Gospodarka 4.0: gospodarka ceny lub karawany; wyslij <kod> potwierdz, transport, obron, odbierz.",
        "Gospodarka zamowienia; wykonaj <kod> potwierdz — wielkie zamowienia surowcow, co dwie godziny.",
        "Gospodarka produkcja; rozbuduj <kopalnia/tartak/farma/warsztat> potwierdz; zbierz — gildia produkuje co 6 godzin. Koszty ze skarbca gildii; zbior do banku.",
        "Transport morski wymaga aktywnego statku, odpowiedniej ladowni i portu. Brak walk PvP. Towary pobierane od razu; zapis trwa w SQLite.",
    ],
    "ocean4": ["Ocean 4.0: bitwy flot przeciw NPC, nie przeciw graczom. Aby zacząć: ocean4 cele i ocean4 atak korsarze, blokada, kraken, lewiatan lub smok.", "ocean4 flota; ocean4 eskorta dodaj <nr>; ocean4 eskorta usun <nr> - ustaw w porcie do dwoch okretow eskortowych.", "ocean4 status; ocean4 rozkaz salwa/manewr/oslona/abordaz. Abordaz tylko na oslabione okręty, nie na potwory.", "ocean4 odwrot potwierdz - wycofanie bez lupow; ocean4 napraw <nr> potwierdz - remont bojowego kadluba w porcie. Po bitwie odpoczynek 2 godziny. Rejsy Ocean 2.0 bez zmian."],
    "imperium": ["Żyjące Imperia v1.34.0: garnizon, obsadz, wycofaj, rozbuduj, pobierz, wojny, raport. Kontrataki co 12 godzin, dochody co 6 godzin; twierdze nie przepadają przez bycie offline.","imperium — kontrolowane przez gildie twierdze i ich obrona.", "imperium mury <kod> potwierdz — lider rozbudowuje zdobyte mury ze skarbca."],
    "armia": ["armia — siła i skład armii twojej gildii.", "armia rekrutuj <wojownik/lucznik/mag> <ilość> potwierdz — finansowanie ze skarbca; bez całkowitego limitu oddziałów."],
    "oblezenie": ["oblezenie <kod> rozpocznij potwierdz — lider gildii rozpoczyna trzyetapową bitwę u bramy lub posterunku twierdzy.", "oblezenie <kod> status; oblezenie <kod> rozkaz natarcie/ostrzal/magia/oslona; oblezenie <kod> odwrot potwierdz.", "Brama sprzyja natarciu, dziedziniec ostrzałowi, cytadela magii. Do 24 rozkazów, utrata jednostek, odpoczynek 4 godziny.", "Stara komenda oblezenie <kod> potwierdz rozpoczyna teraz bitwę trzyetapową. Przejścia świata pozostają otwarte."],
    "aukcja": ["aukcja — 30 najnowszych ofert kup teraz i licytacji. aukcja moje — twoje oferty.", "aukcja wystaw <przedmiot> <ilość> <cena> — cena stała; aukcja licytacja <przedmiot> <ilość> <cena startowa> <1/6/12/24/48 godzin> — licytacja czasowa.", "aukcja licytuj <nr> <kwota> — blokuje pieniądze w depozycie. aukcja rozlicz [nr] — zakończenie po upływie czasu.", "aukcja kup <nr>; aukcja anuluj <nr>; aukcja odbierz — wypłata, również zwrot przebitej oferty. Anulowanie licytacji możliwe tylko przed pierwszą ofertą.", "Chronione, przypisane i założone EQ nie może zostać sprzedane."],
    "stocznia": ["stocznia lub stocznia flota — lista posiadanych statków, typów i osobnych modułów.", "stocznia buduj bryg/fregata/galeon potwierdz — kolejny statek we flocie (w porcie), z wykorzystaniem surowców.", "stocznia wybierz <nr> — zmiana aktywnego statku w porcie. stocznia nazwij <nr> <nazwa> — zmiana nazwy.", "Moduły kadłuba, żagli, ładowni i nawigacji pozostają przy każdym statku; dawne rejsy Ocean 2.0 nie są resetowane."],
    "historia": [
        "historia / history / lifetime - trwała Historia postaci zapisywana osobno dla każdego slotu postaci.",
        "Walka: zwycięstwa, wszystkie zabite moby, bossowie, rare moby i śmierci.",
        "Zadania: łączna liczba ukończonych questów i odebranych kontraktów z Tablicy Zleceń.",
        "Profesje: wszystkie akcje profesji, liczba craftingów oraz liczba wytworzonych przedmiotów.",
        "Zbiory: od v0.9.4 dokładne ilości złowionych ryb, wydobytych rud/minerałów, drewna, ziół i znalezionych klejnotów.",
        "Świat: liczba odkrytych lokacji, wpisów Bestiariusza i rzadkich ryb.",
        "Migracja starych postaci odtwarza tylko dane rzeczywiście zapisane wcześniej: Bestiariusz, boss/rare, śmierci, questy, kontrakty, akcje profesji i eksplorację. Nie zgaduje dawnych ilości sprzedanych lub zużytych surowców.",
        "Usunięcie pojedynczej postaci usuwa również jej Historię; login i wspólny portfel konta pozostają bez zmian.",
    ],
    "walka": [
        "Walka działa w czasie rzeczywistym. atakuj <mob> i k <mob> rozpoczynają starcie z wybranym zabijalnym mobem.",
        "PvP jest wyłączone. Gracze nie mogą atakować, ranić ani zabijać innych graczy; ofensywne skille i AoE wybierają wyłącznie moby.",
        "combat — pokazuje aktualny filtr logu walki.",
        "combat concise — minimalny log pod NVDA: kluczowe wydarzenia, mechaniki bossa, ostrzeżenia HP, zwycięstwo, śmierć i najważniejsze nagrody.",
        "combat normal — domyślny tryb: czyta zwykłe trafienia i używane skille, ale ogranicza techniczne szczegóły redukcji oraz Skill XP podczas walki.",
        "combat full — pełny log walki z detalami obrażeń, redukcji, Skill XP i mechanik.",
        "Ustawienie combat jest trwałe i zapisuje się osobno dla każdej postaci.",
        "flee / uciekaj — przerywa aktywną walkę realtime.",
    ],
    "questy": [
        "HELP QUEST — pełna pomoc systemu zadań. Każdy quest ma generowany wymagany Level postaci 1-400; jeśli go nie spełniasz, zadania nie można przyjąć.",
        "quest / quest aktywne — numerowana lista wszystkich aktualnie aktywnych questów.",
        "quest ukończone / questy ukończone — osobna historia ukończonych questów, liczba ukończeń oraz pozostały cooldown zadań powtarzalnych.",
        "quest — aktywny dziennik. Po wykonaniu wszystkich celów wpis zmienia stan na ZAKTUALIZOWANO — GOTOWE DO ODDANIA.",
        "quest list <NPC> — numerowana oferta questów konkretnego NPC w twojej bieżącej lokacji, np. quest list Orin albo quest list Arven.",
        "talk <NPC> — NPC reaguje na stan swoich zadań: mówi, gdy ma nowe zadanie, komentuje powrót z aktywnym zadaniem i informuje, gdy cel jest gotowy do oddania. Następnie pokazuje ofertę, ale nie przyjmuje zadania automatycznie.",
        "quest accept <numer> / accept quest <numer> / quest przyjmij <numer> — przyjmuje wskazany numer z ostatnio pokazanej listy questów NPC tylko po spełnieniu wygenerowanego Levelu postaci i pozostałych wymagań. NPC najpierw komentuje zlecenie, potem NVDA czyta przyjęcie i start 0/x.",
        "Każdy quest po przyjęciu zaczyna od 0/x. Liczą się wyłącznie wymagane akcje wykonane po przyjęciu: nowe zabicia, połowy, zbiory, wydobycie, ścinanie, craft, rozmowy i inne zdarzenia celu. Stary zapas ani wcześniejsze zabicia nie naliczają postępu.",
        "Po każdym zdarzeniu zwiększającym licznik NVDA od razu czyta bieżący postęp. Ponowne quest / quest aktywne zawsze pobiera aktualny stan z bazy, bez starego cache.",
        "quest info <numer> — działa po quest, quest ukończone i quest list <NPC>; pokazuje NPC, opis, cel, aktualny postęp, wymagania, nagrody, powtarzalność i cooldown.",
        "quest oddaj <numer> / oddaj quest <numer> — oddaje wskazany aktywny quest, jeżeli cele są wykonane i jesteś u właściwego NPC; NPC komentuje wykonanie i osobiście przekazuje nagrodę.",
        "dostarcz <nazwa> / deliver <nazwa> — jawnie przekazuje aktywny przedmiot dostawy właściwemu NPC, np. dostarcz mapa. Rozmowa z odbiorcą nadal również może automatycznie zakończyć dostawę.",
        "quest porzuć <numer> / quest abandon <numer> — porzuca aktywny quest z ostatniej listy. Bieżący postęp przepada, ale wcześniejsze ukończenia pozostają w historii; quest można później przyjąć ponownie.",
        "Kilka questów jednego NPC może być aktywnych równocześnie. Zlecenia profesyjne są niezależne, np. Mikstury Many i Mikstury Leczenia u Orina.",
        "Questy powtarzalne zachowują osobny czas odnowienia. Problem goblinów, Plaga Trolli i Cienie w Gaju odnawiają się co 60 minut.",
        "Kartograf Eren ma pięć niezależnych zleceń: mapa patroli, plan portowych magazynów, mapa drogi do kopalni, odkrycie 5 nowych sektorów i odkrycie 1 nowego sekretu. Każde odnawia się co 60 minut.",
        "Karczmarka Elia w Błękitnym Płomieniu ma trzy niezależne zlecenia godzinne: świeże ryby, zioła do naparów oraz bezpieczny szlak przeciw bandytom.",
        "Próba Rybaka u Borysa wymaga 30 dowolnych ryb złowionych po przyjęciu zadania.",
        "Pierwsze zlecenie Kucharza Marcela wymaga ugotowania 1 Pieczonej ryby rzecznej po przyjęciu zadania. Przepis zużywa 2 RÓŻNE gatunki małych ryb rzecznych (Ukleja Rzeczna, Jelec lub Śliz Kamienny); przedmiot Mała ryba nie jest wymagany.",
        "Jeśli numer nie pasuje, najpierw ponownie wpisz quest, quest ukończone albo quest list <NPC>, aby ustawić właściwą listę kontekstową.",
    ],
    "elity": [
        "Elity pojawiają się losowo zamiast zwykłych mobów. Prefixy obejmują Opancerzony, Wściekły, Astralny, Przeklęty, Regenerujący i inne.",
        "Elity mają wyższe nagrody Soul XP i Class XP oraz lepszy loot.",
        "Rzadkie moby pojawiają się znacznie rzadziej i mają jeszcze większe HP, obrażenia i nagrody.",
        "Mini-bossy mają własny respawn i są mocniejsze od zwykłych mobów danego expowiska.",
        "Regionalne sety: Kultystów Pustki, Umarłego Króla i Wiecznego Lodu. Progi 2/4/6.",
        "Skrzynie: wpisz otwórz skrzynię, skrzynia albo chest. Każda postać otwiera je osobno; odnawiają się po czasie i losują rzadkość.",
    ],
    "skrzynie": [
        "Skrzynie skarbów znajdują się w wybranych expowiskach i odnawiają się po czasie.",
        "Komendy: otwórz skrzynię, skrzynia, chest, treasure. Skrzynie mają osobny cooldown dla każdej postaci.",
        "Rzadkości: Zwykła, Rzadka, Epicka, Legendarna.",
        "Wyższa rzadkość daje więcej waluty i większą szansę na regionalne części setów.",
    ],
    "kodeks_klasowy": [
        "Codex klasowy pokazuje wszystkie skille klas wraz z wymaganiami i stanem postaci.",
        "kodeksklasowy <klasa> / classcodex <class> - pełny Codex jednej klasy.",
        "kodeksklasowy moje / classcodex mine - Codex wszystkich aktywnych klas.",
        "kodeksklasowy wszystkie / classcodex all - wszystkie 14 klas.",
        "Możesz też użyć: codex klasy <klasa> albo codex class <class>.",
        "Każdy skill pokazuje wymaganą Biegłość klasy, nauczyciela, jego salę, koszt nauki po aktualnym rabacie Gildii oraz status odblokowania.",
        "Status rozróżnia: nauczona, dostępna do nauki, zablokowana przez Biegłość albo zablokowana przez nieaktywną klasę.",
    ],
    "znajomi": [
        "znajomi — lista znajomych, ich status online/offline oraz oczekujące zaproszenia.",
        "znajomi dodaj <gracz> — wysyła prośbę o dodanie do znajomych; znajomi akceptuj <gracz> / odrzuc <gracz>.",
        "znajomi usun <gracz> — usuwa obustronną znajomość.",
        "znajomi party <gracz> — szybkie zaproszenie znajomego do drużyny.",
        "znajomi gildia <gracz> — szybkie zaproszenie znajomego do Gildii; nadal obowiązują prawa rangi i pozostałe zasady Gildii.",
        "tell <gracz> <tekst> — prywatna wiadomość do gracza online. reply <tekst> / odpisz <tekst> odpowiada ostatniemu nadawcy prywatnej wiadomości.",
    ],
    "gildia": [
        "gildia — status Gildii graczy: poziom, bonus, skarbiec, członkowie i osiągnięcia.",
        "v0.34.5: nowa postać na koncie automatycznie dołącza jako Członek do tej samej Gildii, jeśli pozostałe postacie konta mają jedną wspólną Gildię.",
        "gildia utworz <nazwa> / guild create <name> — założenie kosztuje 500 złota; gildia dolacz; gildia zapros <gracz>; gildia członkowie.",
        "gildia wplac <kwota> [monet|zlota|mithril] — każdy członek może zasilać wspólny skarbiec.",
        "gildia wyplac <kwota> [monet|zlota|mithril] — wypłata na własny portfel wymaga prawa przypisanego do rangi.",
        "gildia rozbuduj; gildia rozbuduj potwierdz — tylko lider wydaje skarbiec na poziomy Gildii 1-400.",
        "gildia siedziba — prywatna Siedziba Gildii 1-10; wysokie poziomy kosztują bardzo dużo, nawet mithril jako najwyższy nominał waluty.",
        "gildia budynek rozbuduj <kowal/skarbiec/biblioteka/trening> — tańsze budynki 1-10, nie mogą przewyższyć poziomu Siedziby.",
        "gildia kontrakty; gildia kontrakt oddaj <ilość> — wspólne polowania, bossowie i dostawy materiałów z nagrodą do skarbca.",
        "gildia boss; gildia boss przyzwij; gildia boss ranking; gildia trofea — specjalni bossowie Gildii, ranking i trofea.",
        "gildia rangi; gildia ranga utworz/ustaw/priorytet/nadaj — własne rangi i uprawnienia.",
        "Bonus Gildii rośnie wraz z poziomem 1-400: +11% na 100, +15% na 200, +19% na 300 i maksymalnie +23% na 400 do Biegłości, Soul XP, EXP statystyk i profesji.",
        "gildia bank [wplac|wyplac] — wspólny bank przedmiotów; wypłata przedmiotów też zależy od rangi.",
        "gildia chat <tekst>; gildia log; gildia osiągnięcia.",
    ],
    "gildiaklasowa": [
        "gildiaklasowa / reputacja — pokazuje reputację aktywnych klas, rangę i zniżkę na naukę.",
        "gildiaklasowa <klasa> — szczegóły reputacji i zadania danej klasy.",
        "zadanieklasowe / classquest — klasowe zadanie gildyjne.",
        "egzamin / exam — stan egzaminów Soul 50, 100, 150 i 200.",
        "Egzaminy wymagają Soul, rosnącej reputacji Gildii oraz opłaty; Soul 50 wymaga też ukończenia zadania klasowego.",
        "egzamin <50|100|150|200> — podejście do egzaminu.",
        "guildbounty / zleceniagildii — dawna tablica celów Gildii i nagrody reputacji.",
        "Nowa losowana Tablica Zleceń działa przez bounty / zlecenia / contracts i ma osobny trwały postęp 0/x.",
        "Reputacja obniża ceny nauki u nauczycieli maksymalnie o 25 procent.",
    ],
    "przypisane": [
        "Broń Duszy i progresja Duszy są na stałe przypisane do postaci i nie są przedmiotem inventory.",
        "Wszystkie 8 narzędzi profesji jest przypisanych do postaci po zakupie.",
        "Narzędzia nie można oddać, wyrzucić, sprzedać ani schować w Banku Dusz.",
        "Każde narzędzie można kupić tylko jeden raz na postać.",
        "Level, XP i Tier narzędzia pozostają zapisane przy tej postaci.",
        "Stare kopie z banku są automatycznie przywracane do postaci, a duplikaty redukowane do jednej sztuki.",
        "English: profession tools and Soul progression are character-bound; each tool can be purchased once per character.",
    ],
    "aoe": [
        "Czary obszarowe trafiają wszystkich dostępnych przeciwników w tej samej lokacji.",
        "Mag: Eksplozja Arkanów Soul 40, Burza Meteorów Soul 160.",
        "Nekromanta: Plaga Dusz Soul 40, Nawałnica Grobów Soul 160.",
        "Czarownik: Nova Otchłani Soul 40, Deszcz Pustki Soul 160.",
        "Druid: Huragan Soul 40, Deszcz Gwiazd Soul 160.",
        "Psionik: Burza Umysłów Soul 40, Psychiczne Załamanie Soul 160.",
        "Kapłan: Modlitwa Odnowy Soul 40 i Masowe Uzdrowienie Soul 160 leczą całą drużynę w tej samej lokacji.",
        "Działają też angielskie nazwy, np. arcane explosion, meteor storm, soul plague, void nova, hurricane, mind storm, group heal, mass heal.",
        "Akcja obszarowa nie wywołuje osobnego kontrataku; przeciwnik atakuje według własnego timera.",
    ],
    "bestiariusz": [
        "bestiariusz / bestiary - podsumowanie odblokowanych gatunków i wszystkich zabójstw.",
        "bestiariusz lista / bestiary list - wszystkie odkryte wpisy wraz z liczbą zabójstw.",
        "bestiariusz <mob> / bestiary <mob> - liczba zabójstw, rekord czasu, HP, obrażenia, lokacje, realne dropy i zdefiniowane odporności.",
        "Pierwsze zabicie odblokowuje wpis. Proceduralne warianty elite/rare są przypisane do bazowego gatunku.",
        "bestiariusz rekordy / bestiary records - najlepsze zapisane czasy zabicia.",
    ],    "dwa_pierscienie": [
        "Postać może nosić dwa pierścienie jednocześnie: ring1 i ring2.",
        "Komendy: załóż pierścień 1, załóż pierścień 2, equip ring1, equip ring2.",
        "Sockety są osobne dla obu pierścieni: osadz rubin pierścień 1 albo socket ruby ring2.",
        "Do dwóch identycznych pierścieni trzeba posiadać dwie sztuki.",
        "Drugi taki sam pierścień nie liczy się drugi raz do progu setu klasowego 2/4/6/8.",
    ],
    "soul_milestones": [
        "Kamienie milowe Broni Duszy są na Tierach 5, 10, 15 i 20.",
        "Każdy wzmacnia specjalizację klasy głównej; Łotrzyk dostaje dodatkowy unik, a Strażnik dodatkową redukcję obrażeń.",
        "Komendy: dusza info albo soul info.",
    ],
    "nawigacja": [
        "Dla lochów i expowisk prowadzenie kończy się przed wejściem; nigdy nie prowadzi na piętro ani w głąb obszaru.",
        "prowadz <cel> i walk <cel> to dokładnie ten sam system nawigacji.",
        "Dla zwykłej lokalizacji prowadzenie zatrzymuje się jeden krok przed celem; ostatni kierunek wykonujesz sam.",
        "Wyjątek: gdy celem jest NPC, prowadzenie dochodzi dokładnie do pokoju NPC.",
        "Działają też guide <cel>, idz <cel>, go <cel> oraz navigate <cel>.",
        "Lista jest uporządkowana kategoriami: prowadz lista lub walk list.",
        "Kategorie: miasto, miasta, gildia, profesje, tereny, lochy, npc i wszystko. `walk miasta` pokazuje wszystkie 9 miejscowości.",
        "Przykład: prowadz lista gildia, walk list dungeons, prowadz lista profesje.",
        "Jeżeli nazwa pasuje do kilku miejsc, dostajesz jedną numerowaną listę i wpisujesz tylko cyfrę.",
        "v0.38.12: prowadz kopalnia kończy się w Komnacie Kryształowej przy progu Kopalni Głębinowej; wpisz kopalnia, aby wejść bez podawania kierunku.",
        "cofnij, wyjście, back, exit, wstecz, return i escape prowadzą bezpośrednio do bezpiecznego wyjścia z rozpoznanego lochu.",
        "Nawigacja automatyczna zatrzymuje się na blokadach progresji, żywym bossie, zamkniętej ścianie kopalni albo rozpoczęciu walki.",
        "Zmiana postaci: quit. Komenda zapisuje obecną postać i wraca do MENU POSTACI bez rozłączania.",
    ],
    "dungeon_exit": [
        "Dostępność lochów: cofnij, wyjście, back, exit, wstecz, return i escape prowadzą bezpośrednio do bezpiecznego wyjścia z lochu.",
        "Te komendy nie cofają o jedną lokację.",
        "Działają w rozpoznanych lochach, profession dungeonach, Jaskini Trolli i zamkniętych odnogach endgame.",
        "Podczas walki najpierw użyj flee albo pokonaj przeciwnika.",
    ],
    "kamienie": [
        "Kamienie szlachetne są dodatkowym łupem z Górnictwa i nie zastępują rudy.",
        "Dodano 11 kamieni od Rubinu do Pryzmatu Eternium.",
        "Surowy kamień trzeba oszlifować u Mirelli w Pracowni Jubilerskiej.",
        "Komenda: szlifuj <kamień>.",
        "Szlifowanie rozwija Jubilerstwo i Szczypce Jubilerskie.",
        "Oszlifowany klejnot można osadzić w założonym pierścieniu albo naszyjniku.",
        "Komenda: osadz <klejnot> pierścień.",
        "Komenda: osadz <klejnot> naszyjnik.",
        "Komenda gniazda pokazuje zajęte gniazda i osadzone klejnoty.",
        "Craftowana biżuteria ma 1, 2 lub 3 gniazda zależnie od tieru.",
        "Klasowy pierścień ma 1 gniazdo, a klasowy naszyjnik 2.",
        "Po zmianie pierścienia lub naszyjnika osadzone klejnoty automatycznie wracają do ekwipunku.",
        "Gniazda i klejnoty są zapisywane w SQLite.",
    ],
    "jubilerstwo": [
        "Jubilerstwo jest profesją 1-400 z 23 rangami.",
        "Narzędzie: Szczypce Jubilerskie, level 1-400 i 40 Tierów.",
        "Szczypce nie mają trwałości i nie zużywają się.",
        "Kupisz je wyłącznie u Jubilerki Mirelli w Pracowni Jubilerskiej nad Rynkiem.",
        "Użyj prowadz jubilerka albo prowadz pracownia jubilerska.",
        "Komenda jubilerstwo pokazuje stan profesji.",
        "Komenda szczypce pokazuje stan narzędzia.",
        "Komenda receptury jubilerstwo pokazuje wszystkie receptury.",
        "Komenda jub <receptura> wykonuje biżuterię.",
        "Dodano 18 receptur: 9 pierścieni i 9 naszyjników od Żelaza do Eternium.",
        "Jubilerka Mirella prowadzi 9-etapowy łańcuch zleceń profesyjnych.",
    ],
    "prowadz_wybor": [
        "Gdy prowadz pasuje do kilku lokacji, MUD pokazuje numerowaną listę zamiast zgadywać.",
        "Działa to teraz dla wszystkich terenów, nie tylko dla kopalni.",
        "Po liście wpisujesz tylko sam numer, na przykład 1 albo 2.",
        "Nie ma drugiego pytania ani drugiego wyboru.",
        "Przykłady: prowadz kopalnia, prowadz dzicz, prowadz góry, prowadz podziemia, prowadz gildia, prowadz jaskinia trolli, prowadz krypta, prowadz wieża i prowadz twierdza.",
        "Duże wielopoziomowe lochy są zwijane do czytelnej pozycji zamiast wypisywania dziesiątek lub setek pięter.",
        "Konkretne piętra nie są celem prowadzenia. Wnętrza lochów i expowisk eksplorujesz samodzielnie.",
        "Wpisz anuluj, jeśli chcesz zamknąć oczekujący wybór bez wybierania.",
    ],
    "respawn_mobow": [
        "Czas odradzania mobów został globalnie zwiększony 2 razy.",
        "Zwykłe moby: bazowo 120 sekund, teraz 240 sekund.",
        "Bossowie: bazowo 300 sekund, teraz 600 sekund.",
        "Manekin treningowy: bazowo 60 sekund, teraz 120 sekund.",
        "Jeżeli konkretny mob ma własny respawn_seconds, jego indywidualny czas również jest mnożony razy 2.",
        "HP, obrażenia, Soul XP, nagrody, loot i mechaniki walki nie zostały zmienione.",
    ],
    "bizuteria_klasowa": [
        "Każda z 14 klas ma własny Pierścień i Naszyjnik.",
        "Pierścień zajmuje osobny slot pierścień.",
        "Naszyjnik zajmuje osobny slot naszyjnik.",
        "Biżuteria jest dostępna w tym samym sklepie klasowym co pozostałe części zestawu.",
        "Pierścień daje klasowy bonus +2 do głównej cechy zestawu.",
        "Naszyjnik daje klasowy bonus +3 do głównej cechy zestawu.",
        "Kupno i założenie wymaga aktywnej odpowiedniej klasy.",
        "Multiclass działa także dla pierścieni i naszyjników.",
        "Szybkie komendy: załóż pierścień oraz załóż naszyjnik.",
    ],
    "sklepy_klasowe": [
        "Dodano klasowe sklepy wyposażenia dla wszystkich 14 klas.",
        "Każda klasa ma 3 różne linie wyposażenia; każda linia obejmuje hełm, pancerz, rękawice, nogawice, buty, talizman, pierścień i naszyjnik.",
        "Wojownik i Berserker kupują wyposażenie w Sali Oręża Gildii.",
        "Łotrzyk i Łowca kupują wyposażenie w Galerii Cieni Gildii.",
        "Mnich i Strażnik kupują wyposażenie w Sali Dyscypliny Gildii.",
        "Mag i Psionik kupują wyposażenie w Komnacie Arkanów Gildii.",
        "Nekromanta i Czarownik kupują wyposażenie w Komnacie Mrocznych Sztuk.",
        "Kapłan i Druid kupują wyposażenie w Sanktuarium Gildii.",
        "Wpisz shop albo list w odpowiedniej sali. Możesz też filtrować: shop <klasa>, np. shop wojownik.",
        "Klasowe EQ może też losowo wypaść z mobów; moc dropu jest dopasowana do siły przeciwnika, a klasa/linia/slot są losowe.",
        "Przedmiot klasowy można kupić i założyć tylko wtedy, gdy wymagana klasa jest aktywna.",
        "Multiclass działa: aktywna klasa dodatkowa również pozwala korzystać z jej wyposażenia.",
        "Możesz użyć prowadz sklep <klasa>, na przykład prowadz sklep maga.",
    ],
    "kilof_u_gornika": [
        "Kilof nie jest już sprzedawany przez Kowala Dorana ani w Górskiej Kuźni.",
        "Podstawowy Kilof sprzedaje wyłącznie Górnik Toren przy Wejściu do Kryształowej Jaskini.",
        "Użyj prowadz jaskinia albo prowadz sklep kilofa.",
        "Na miejscu wpisz shop albo list, a potem kup kilof.",
    ],
    "waluta_auto": [
        "Wspólne saldo działa automatycznie bez komendy wymiany.",
        "Jedno wspólne saldo z nominałami: srebro, złoto i mithril.",
        "Nominały: 100 srebra = 1 złoto; 1 000 000 złota = 1 mithril.",
        "Portfel i Bank Dusz normalizują nominały automatycznie.",
        "Stara ręczna wymiana została usunięta z MUD-a.",
        "Stare salda są zachowywane wartościowo i nie są kasowane.",
    ],
    "przetop": [
        "przetop <metal, ruda albo płyty> przetapia surowiec na właściwą sztabkę.",
        "4 Stalowe Płyty z Pancerza ze Szkatułki można przetopić w 1 Sztabkę Stali: przetop płyty / smelt plates.",
        "Przetop max <metal> zużywa TYLKO wybrany surowiec. Aby przetopić Salvage, użyj jawnie: przetop max odłamki żelaza. Przetop wszystko nadal obejmuje wszystkie dostępne źródła.",
        "Pojedyncze przetop <metal> może awaryjnie wykorzystać Salvage, jeśli brakuje zwykłej rudy. Dwa zgodne fragmenty Salvage dają 1 sztabkę.",
        "v0.31.15: każda udana receptura nalicza aktywne questy craftingowe; Salvage/Salvage 3.0/Tech Salvage dają Kowalstwo XP bez sztucznego nabijania Młota.",
        "Komenda korzysta z istniejących receptur Kowalstwa i nie omija wymagań.",
        "Musisz mieć Młot Rzemieślniczy, odpowiedni level Kowalstwa, wymagany Tier Młota, składniki i stać przy właściwej kuźni.",
        "Przykłady: przetop żelazo, przetop odłamki żelaza, przetop srebro, przetop płyty, przetop złoto, przetop mithril, przetop kobalt.",
        "Mithril wydobywa się od Kilofa 80 i poziomu 80 Kopalni Głębinowej. Obsługiwane są także: runa, smocza stal, astral, pustka i Eternium.",
        "Przetapianie rudy w sztabki daje XP Kowalstwa i Młota tak samo jak pozostałe receptury wytwarzania sztabek.",
    ],
    "assist": [
        "Drużyna ma automatyczne asystowanie: gdy członek rozpoczyna walkę, wolni członkowie tej samej drużyny i lokacji automatycznie dołączają do jego celu.",
        "wspieraj <gracz> i assist <gracz> pozostają jako ręczne komendy awaryjne.",
        "Obaj gracze muszą należeć do tej samej drużyny.",
        "Obaj gracze muszą stać w tej samej lokacji.",
        "Wskazany członek drużyny musi aktualnie walczyć z żywym przeciwnikiem.",
        "Automatyczne dołączenie uruchamia zwykłą walkę realtime bez dodatkowego darmowego ciosu.",
        "Jeśli walczysz już z innym mobem, assist nie przełączy celu; najpierw zakończ walkę albo użyj flee.",
        "Działa także jako: druzyna wspieraj <gracz> oraz druzyna assist <gracz>.",
    ],
    "mityczne_od_100": [
        "Mityczna Krypta nie ma wymogu Soul Level i jest dostępna od razu, ale od pierwszego piętra jest bardzo trudna.",
        "Mityczna Krypta ma nieskończone piętra i bossa co 10 pięter bez końca.",
        "Mityczna Wieża Astralna zachowuje własny wymóg Soul Level 100, ale nie ma górnego limitu pięter.",
        "Dostępność Krypty nie oznacza rekomendacji: con, expowiska i komunikat zagrożenia pokazują, gdy przeciwnik jest za silny.",
        "W Kryptach co 10 pięter rosną trudność, Class XP i Soul XP; waluta i moc EQ nie rosną bez końca.",
    ],
    "expowiska": [
        "Komenda expowiska pokazuje listę terenów przeznaczonych do expienia.",
        "Każdy teren ma kategorię bazową: Początkujący, Umiarkowany, Trudny, Śmiertelny albo Endgame.",
        "Ocena dla ciebie zmienia się automatycznie wraz z Biegłością aktywnych klas, Soul Levelem, statystykami i wyposażeniem.",
        "Gobliny, Bandyci, Las Szeptów, Kanały i podobne wczesne strefy należą do kategorii Początkujący.",
        "expowiska polecane pokazuje obszary, które są teraz Odpowiednie albo Trudne dla twojej postaci.",
        "EXP za zabicie jest dynamiczne 1-400: silniejszy od ciebie mob daje premię, a ten sam przeciwnik daje stopniowo mniej EXP, gdy twoja postać go przerasta.",
        "Dynamiczny mnożnik obejmuje EXP statów, Soul XP i Class XP; nie zmienia waluty ani lootu. Minimalna wypłata to 35% bazowego EXP, maksymalna premia x2.25.",
        "con <mob> pokazuje aktualny mnożnik EXP oraz porównanie siły postaci i przeciwnika.",
        "expowiska krypta pokazuje szczegółowy opis Krypty.",
        "expowiska trolle pokazuje szczegółowy opis Jaskini Trolli.",
        "expowiska giganci pokazuje szczegółowy opis Twierdzy Gigantów.",
        "expowiska astral pokazuje szczegółowy opis Wieży Astralnej.",
        "Szczegóły zawierają przeciwników, trudność, opis, uwagi i komendę prowadzenia.",
        "Soulbound nadal nie ma levelu postaci ani Character XP.",
    ],
    "auto_kopalnia_down": [
        "kop on może teraz automatycznie zejść w dół po przebiciu ściany Kopalni Głębinowej.",
        "Automat schodzi tylko przez kierunek down.",
        "Automat schodzi tylko wtedy, gdy następny poziom jest już odblokowany w mine_progress.",
        "Automat sprawdza, czy wyjście down prowadzi dokładnie na następny poziom Kopalni.",
        "Nie przejdzie przez nieprzebitą ścianę.",
        "Nie chodzi po świecie i nie wybiera innych kierunków.",
        "Jeśli włączysz kop on na poziomie z wcześniej przebitą ścianą, zejdzie na odblokowany następny poziom.",
        "Po zejściu kontynuuje kopanie na nowym poziomie.",
    ],
    "sciany_kopalni": [
        "Każda ściana Kopalni Głębinowej ma losową liczbę wymaganych uderzeń Kilofa.",
        "Poziomy 1-9 losują od 3 do 8 uderzeń.",
        "Od poziomu 10 próg losuje się w przybliżeniu od 70 do 130 procent numeru piętra.",
        "Wylosowany próg jest zapisywany w SQLite i nie zmienia się po restarcie ani ponownym logowaniu.",
        "Po przebiciu ściany następna ściana dostaje nowy niezależny losowy próg.",
        "Istniejący zapis wall_hits nie jest resetowany po aktualizacji.",
        "Komenda kopalnia pokazuje bieżący postęp i aktualnie wylosowany próg.",
        "kop on może po przebiciu bezpiecznie zejść na kolejny odblokowany poziom.",
    ],
    "who": [
        "who pokazuje wszystkich aktualnie zalogowanych graczy.",
        "Dla każdego gracza podaje nazwę, aktywną klasę lub klasy, Soul Level, aktualną lokację i strefę.",
        "Alias po polsku: kto.",
        "Przykładowa linia: Asia. Klasa: Mag. Soul Level 42. Lokalizacja: Rynek. Strefa: Miasto.",
    ],
    "look_skrot": [
        "Skrót l działa dokładnie tak samo jak look.",
        "l bez argumentu opisuje aktualną lokację.",
        "l Asia działa jak look Asia.",
        "l Górski Troll działa jak look Górski Troll.",
        "l Mikstura Leczenia działa jak look Mikstura Leczenia.",
        "l hełm działa jak look hełm.",
        "Skrót obsługuje graczy, NPC, przeciwników i przedmioty.",
    ],
    "look_cel": [
        "look bez argumentu opisuje aktualną lokację jak wcześniej.",
        "look gracz pokazuje gracza w tej samej lokacji.",
        "Przykład: look Asia.",
        "look NPC pokazuje opis NPC stojącego w tej samej lokacji.",
        "look przeciwnik pokazuje aktualne HP, bazowe obrażenia, typ obrażeń i specjalne mechaniki.",
        "look przedmiot pokazuje opis przedmiotu z ekwipunku, założonego sprzętu albo lokalnego sklepu.",
        "Przykład: look Mikstura Leczenia albo look hełm.",
        "Przy częściowej nazwie cel musi być jednoznaczny.",
        "look nie pokazuje graczy, NPC ani mobów z innych lokacji.",
    ],
    "apostrof_say": [
        "Apostrof na początku linii działa jak komenda say.",
        "Przykład: 'Cześć wszystkim",
        "To samo co: say Cześć wszystkim",
        "Nie trzeba wpisywać słowa say.",
        "Sam apostrof bez tekstu pokazuje użycie say.",
        "Wiadomość nadal trafia tylko do graczy w tej samej lokacji.",
    ],
    "say": [
        "say tekst lub apostrof przed tekstem wysyła wiadomość do wszystkich graczy w tej samej lokacji.",
        "Ty otrzymujesz: Mówisz: tekst.",
        "Inni gracze w pokoju otrzymują: nazwa gracza mówi: tekst.",
        "Wiadomość nie jest słyszana w innych lokacjach.",
        "Puste wiadomości i same spacje są odrzucane.",
        "Maksymalna długość jednej wiadomości to 500 znaków.",
        "Aliasy: powiedz, mow, mów.",
        "say nie przerywa odpoczynku.",
    ],
    "kodowanie": [
        "Soulbound domyślnie używa UTF-8 dla całej komunikacji tekstowej.",
        "Serwer wysyła klientowi Telnet negocjację CHARSET z preferowanym UTF-8.",
        "Komenda kodowanie pokazuje bieżący tryb.",
        "kodowanie utf8 przełącza wejście i wyjście sesji na UTF-8.",
        "kodowanie cp1250 przełącza wejście i wyjście sesji na Windows-1250 dla starszych klientów.",
        "Obsługiwane polskie znaki: ą ć ę ł ń ó ś ź ż oraz wielkie odpowiedniki.",
        "Wejście nie używa już errors ignore, więc polskie bajty nie są po cichu usuwane.",
        "Zmiana dotyczy tylko aktualnej sesji i nie zmienia bazy danych.",
    ],
    "mountain_expansion": [
        "Wioska Górska została rozbudowana o Górską Kuźnię, Chatę Łowcy Potworów, Górski Targ Minerałów i Chatę Zielarki Alpejskiej.",
        "Eryk ma dodatkowy Patrol Górskiego Szlaku.",
        "Łowca Potworów Ragna zleca polowanie na Trolli Szamanów i Króla Trolli.",
        "Dagna zleca odzyskanie Skradzionych Skrzyń Rudy oraz serię zadań na konkretne rudy.",
        "Twierdza Gigantów generuje wielopokojowe poziomy dynamicznie od pierwszego piętra i może tworzyć dalszą kontynuację na żądanie.",
        "Bossowie Twierdzy stoją na poziomach 10, 20, 30, 40 i 50.",
        "Boss progu blokuje tylko przejście na następne piętro i tylko do pierwszego trwałego zaliczenia przez daną postać.",
        "W Twierdzy występują Ogrzy Miotacze Głazów, Cyklopi Strażnicy i Górskie Giganty.",
        "Prowadzenie: prowadz twierdza gigantow.",
    ],
    "questy_kowalstwa_1_200": [
        "Kowal Górski Brok ma 13-etapowy łańcuch Kowalstwa od levelu 1 do 200.",
        "Questy wymagają jednocześnie odpowiedniego levelu Kowalstwa.",
        "Po każdym wykutym przedmiocie gra czyta postęp np. 1 z 3.",
        "Każda akcja Kowalstwa/Rzemiosła, Gotowania, Alchemii i Jubilerstwa ma losowy przyrost XP; receptury ze stałym XP losują wokół wartości bazowej bez zwiększania średniej.",
        "Finał level 200 wymaga wykucia pełnego sześcioczęściowego Zestawu Eternium.",
        "Każdy etap odnawia się po 60 minutach.",
    ],
    "questy_gotowania_1_200": [
        "Marcel ma 13 etapów z konkretnymi potrawami od levelu 1 do 200.",
        "Wykonanie potraw jest liczone tak samo jak mikstury Orina.",
        "Po każdym gotowaniu słyszysz dokładny postęp.",
        "Każdy etap odnawia się po 60 minutach.",
    ],
    "questy_konkretne_zasoby": [
        "Zielarka Alpejska Ira zleca 10 Lawendy, 8 Żeń-szenia i 5 Księżycowych Kwiatów z osobnych łąk.",
        "Handlarka Dagna ma zadania na konkretne rudy od Miedzi do Eternium.",
        "Mistrz Wędkarstwa Neris ma zadania na konkretne gatunki i rzadkie warianty ryb.",
        "Wśród zleceń Neris są trzy Złote Okazy Pstrąga i jeden Pradawny Tuńczyk.",
        "Stare zapasy nie nabijają licznika zdobywania. Zasób musi zostać pozyskany po przyjęciu questa.",
        "Do oddania nadal trzeba posiadać wymaganą liczbę sztuk.",
        "Każdy quest profesyjny odnawia się co 60 minut.",
    ],
    "rare_trolls_elites": [
        "Górski Troll może przy spawnie zostać zastąpiony rzadkim wariantem.",
        "Rzadkie trolle: Albinos Troll, Kryształowy Troll, Pradawny Troll i Troll Runiczny.",
        "Zwykłe trolle, rzadkie trolle i mieszkańcy Twierdzy mogą pojawić się jako elity.",
        "Affixy elit: Opancerzony, Wampiryczny, Regenerujący, Lodowy, Ognisty, Astralny, Burzowy, Toksyczny, Berserker i Przeklęty.",
        "Opancerzony redukuje otrzymywane obrażenia.",
        "Wampiryczny wysysa życie.",
        "Regenerujący odnawia HP.",
        "Lodowy i Ognisty wzmacniają magię.",
        "Astralny zmienia typ obrażeń i częściowo omija obronę.",
        "consider pokazuje affix oraz informację o rzadkim trollu.",
    ],
    "questy_mikstur_orina": [
        "Orin ma 11-etapowy łańcuch zleceń Alchemii od levelu Alchemii 1 do 200.",
        "Etap I level 1: 3 Mikstury Many.",
        "Etap II level 5: 4 Mikstury Leczenia.",
        "Etap III level 40: 3 Wielkie Mikstury Leczenia.",
        "Etap IV level 60: 3 Wielkie Mikstury Many.",
        "Etap V level 80: 2 Eliksiry Witalności.",
        "Etap VI level 100: 2 Najwyższe Mikstury Leczenia.",
        "Etap VII level 120: 2 Najwyższe Mikstury Many.",
        "Etap VIII level 140: 2 Wielkie Eliksiry Witalności.",
        "Etap IX level 160: 2 Toniki Duszy.",
        "Etap X level 180: 1 Astralny Eliksir Odnowy.",
        "Etap XI level 200: 1 Eliksir Wiecznej Duszy.",
        "Każdy etap śledzi faktycznie uwarzone sztuki i czyta postęp po każdym warzeniu.",
        "Każde zlecenie jest powtarzalne po 60 minutach.",
        "Kolejny etap wymaga ukończenia poprzedniego oraz odpowiedniego levelu Alchemii.",
    ],
    "postep_mikstur": [
        "Questy Alchemii Orina śledzą teraz faktycznie uwarzone mikstury od momentu przyjęcia zadania.",
        "Po każdym warzeniu otrzymujesz komunikat np. Wykonałeś: Mikstura Many. Postęp 1 z 3.",
        "Kolejne warzenie pokazuje 2 z 3, a trzecie 3 z 3.",
        "Bonusowa mikstura z Tieru Moździerza także liczy się jako wykonana, ponieważ rzeczywiście została wytworzona.",
        "Mikstury posiadane przed przyjęciem questa nie zwiększają licznika wykonania.",
        "Po wykonaniu wymaganej liczby nadal musisz posiadać odpowiednią liczbę mikstur, aby oddać je Orinowi.",
        "Jeśli zużyjesz lub sprzedasz miksturę, dziennik pokaże, że wykonanie jest zakończone, ale brakuje sztuk do oddania.",
        "Po ponownym przyjęciu questa po godzinnym cooldownie licznik wykonania wraca do 0.",
        "Dotyczy wszystkich jedenastu zleceń Alchemii Orina.",
    ],
    "wioska_gorska": [
        "Dodano Wioskę Górską w nowym regionie Gór.",
        "Ze Wzgórza Kamiennych Znaków idź na wschód przez Górską Przełęcz.",
        "Na placu Wioski Górskiej są drogi do Domu Straży, Górskiej Gospody i Szlaku Trolli.",
        "Strażnik Górski Eryk w Domu Straży daje zadanie Plaga Trolli.",
        "Zadanie wymaga zabicia 12 trolli w Jaskini Trolli.",
        "Jaskinia Trolli ma wejście, trzy komory i Legowisko Króla Trolli.",
        "W jaskini występują Górskie Trolle, Trolle Osiłki i Trolle Szamani.",
        "Boss: Król Trolli Grum. Jest nieagresywny i walka zaczyna się dopiero po jawnej komendzie ataku.",
        "Prowadzenie: prowadz wioska gorska, prowadz jaskinia trolli, prowadz eryk.",
    ],
    "laki_zielarskie": [
        "Dodano osobne Łąki Zielarskie dla konkretnych ziół.",
        "Łąka Mięty daje Miętę.",
        "Łąka Rumianku daje Rumianek.",
        "Łąka Pokrzywy daje Pokrzywę.",
        "Łąka Melisy daje Melisę.",
        "Łąka Lawendy daje Lawendę.",
        "Łąka Krwawnika daje Krwawnik.",
        "Łąka Szałwii daje Szałwię.",
        "Łąka Waleriany daje Walerianę.",
        "Łąka Żeń-szenia daje Żeń-szeń.",
        "Łąka Księżycowego Kwiatu daje Księżycowy Kwiat.",
        "Wejście do kompleksu Łąk Zielarskich prowadzi na północ z Łąki Kwiatów.",
        "zbieraj i zbieraj on działają na każdej z tych łąk.",
        "Auto-Zielarstwo nie chodzi między łąkami; zbiera tylko tam, gdzie stoisz.",
        "Rzadkie warianty roślin nadal mogą pojawić się przy zbieraniu.",
    ],
    "questy_rzemieslnicze_godzina": [
        "Wszystkie powtarzalne questy profesyjne i rzemieślnicze odnawiają się dokładnie co 60 minut od ukończenia.",
        "Próba Rybaka, Próba Górnika, Próba Drwala i Próba Zielarki: 60 minut.",
        "Cztery zlecenia Haldora: każde 60 minut, w tym przetop 4 Stalowych Płyt z Cmentarza.",
        "Trzy zlecenia Marcela: każde 60 minut.",
        "Trzy zlecenia Orina: każde 60 minut.",
        "Łącznie 13 questów profesyjno-rzemieślniczych.",
        "Zwykłe questy fabularne nie zostały zmienione.",
    ],
    "kowalstwo": [
        "Kowalstwo jest pełną profesją level 1-400.",
        "Kowalstwo ma level 1-400 i rozwija receptury/zlecenia. Młot Rzemieślniczy ma osobny level 1-400 i odpowiada za Tier/bonus produktu.",
        "Przetapianie metali i kucie w Kuźni Dusz daje XP Kowalstwa oraz XP Młota Rzemieślniczego.",
        "Receptury przechodzą od Żelaza, Srebra i Złota do Kobaltu, Run, Smoczej Stali, Astralu, Pustki i Eternium.",
        "Każdy metal ma sztabkę oraz sześć elementów wyposażenia: hełm, pancerz, rękawice, nogawice, buty i talizman.",
        "Wyższe receptury wymagają jednocześnie odpowiedniego levelu Kowalstwa.",
        "Komendy: kowalstwo, kuj <receptura>, craft <receptura>, receptury kowalstwo.",
        "Haldor w Kuźni daje trzy poziomy zleceń Rzemiosła/Kowalstwa oraz godzinne zlecenie recyklingu Stalowych Płyt.",
        "Zlecenia Haldora są powtarzalne i każde odnawia się dokładnie co 60 minut.",
        "Questy Haldora dają XP Kowalstwa, XP Młota oraz walutę.",
        "Sprzedaż wykutego EQ jest ograniczona względem wartości zużytej rudy: zwykły craft nie służy do mnożenia waluty, a wyższą cenę mogą uzyskać dopiero rzadkie jakości craftu.",
        "v0.30.42: ulepsz <EQ> / ulepsz lista u Haldora wzmacnia każde armor EQ od +1 do +10, zużywając fragment materiału z rozkładania. Ulepszanie daje XP Kowalstwa i Młota.",
        "Kowalstwo nie ma trwałości, zużycia ani napraw narzędzi.",
    ],
    "rare_resources": [
        "Dodano rzadkie warianty zasobów profesyjnych.",
        "Ryby mogą wypaść jako Albinos, Złoty okaz, Olbrzymi okaz albo Pradawny okaz.",
        "Rzadkie ryby mają większą wartość sprzedaży i są przechowywane jako osobne okazy w Siatce.",
        "Górnictwo losuje jakość żyły przy każdym udanym wydobyciu.",
        "Zwykła żyła daje x1, Bogata x2, Kryształowa x3, a Legendarna x5 tej samej rudy.",
        "Mithril pozostaje osobną walutą: 0,5-2 procent szansy zależnie od progresu, nie zastępuje rudy i nie jest mnożony przez żyłę.",
        "Drewno może być Bujne, Pradawne, Kryształowe albo Legendarne.",
        "Rośliny mogą być Bujne, Lśniące, Pradawne albo Legendarne.",
        "Rzadkie drewno i rośliny są osobnymi cenniejszymi okazami w magazynach profesji.",
        "Szanse wariantów zależą od poziomu narzędzia, profesji i trudności surowca; warianty legendarne nie wypadają na początku gry.",
        "Obfity zbiór, hotspot i bonus Tieru nie powielają wyjątkowych wariantów ani legendarnych żył.",
        "Questy zbierania kategorii liczą również rzadkie warianty.",
        "Hurtowa sprzedaż magazynów profesji (wszystko siatka/sakwa/stos/torba) obejmuje również rzadkie warianty; zwykłe sell all inventory sprzedaje tylko niezałożone EQ.",
    ],
    "codex_swiata": [
        "Codex Świata łączy wiedzę o zasobach, mobach, bossach i reliktach.",
        "codex pokazuje podsumowanie wszystkich działów.",
        "codex ryby pokazuje wszystkie bazowe gatunki i zasady rzadkich wariantów.",
        "codex rośliny pokazuje rośliny i warianty.",
        "codex drewno pokazuje drewno i warianty drzew.",
        "codex rudy pokazuje wszystkie rudy i cztery rodzaje żył.",
        "codex moby pokazuje zwykłych przeciwników.",
        "codex bossowie pokazuje bossów świata, Krypty, Wieży oraz Mythic.",
        "codex relikty pokazuje relikty i unikalne trofea.",
        "codex warianty opisuje wszystkie rzadkie warianty profesyjne.",
        "codex <nazwa> wyszukuje konkretny zasób, mob, bossa lub relikt.",
        "Długie listy są dzielone na części przyjazne NVDA.",
    ],
    "astralne_sety": [
        "Astralne zestawy mają teraz pełne bonusy 2/4/6 części.",
        "Każdy Krąg Astralny ma teraz 6 elementów: głowa, korpus, dłonie, nogi, stopy i talizman.",
        "2 części jednego Kręgu: +12 procent maksymalnego HP i Many.",
        "4 części jednego Kręgu: dodatkowo +15 procent wszystkich zadawanych obrażeń.",
        "6 części jednego Kręgu: dodatkowo +20 procent obrony fizycznej i magicznej.",
        "Bonusy Astralne mogą współistnieć z aktywnymi bonusami Zestawu Krypty.",
        "stats i equipment czytają aktywny Zestaw Astralny.",
    ],
    "mythic_endgame": [
        "Mityczna Krypta jest dostępna bez wymogu Soul Level; barierą jest jej bardzo wysoka trudność.",
        "Nie wymaga ukończenia zwykłej Krypty ani osiągnięcia konkretnego piętra.",
        "Wejście do Mitycznej Krypty znajduje się w Głębi Krypty.",
        "Mityczna Krypta ma nieskończone piętra i bossa co 10 pięter bez końca.",
        "Mityczna Wieża Astralna odblokowuje się od Soul Level 100.",
        "Nie wymaga ukończenia zwykłej Wieży Astralnej do poziomu 200.",
        "Wejście do Mitycznej Wieży znajduje się przy Astralnej Bramie.",
        "Mityczna Wieża Astralna ma nieskończone piętra i bossa co 10 pięter.",
        "Mityczni bossowie mają znacznie więcej HP, wyższe obrażenia i lepsze nagrody.",
        "Boss Mitycznej Krypty blokuje zejście, a boss Mitycznej Wieży blokuje wejście wyżej.",
        "Mityczna Krypta używa końcowego ekwipunku Krypty, a Mityczna Wieża końcowego Astralnego Kręgu.",
    ],
    "lochy_profesyjne": [
        "Cztery lochy profesyjne są nieskończone; od v0.80.0 każdy poziom ma po 20 pomieszczeń i jest tworzony dynamicznie dopiero przy wejściu.",
        "Górnictwo rozwijasz wyłącznie w Kopalni Głębinowej; nie ma drugiej aktywnej kopalni.",
        "Zatopiona Grota zaczyna się przy Morskim Molo i rozwija Wędkarstwo.",
        "Pradawny Las zaczyna się w Głębi Gaju i rozwija Drwalstwo.",
        "Ogród Alchemika zaczyna się w Chacie Zielarki i rozwija Zielarstwo.",
        "Dostęp do etapów zleceń i receptur wynika z levelu właściwej profesji; level narzędzia odpowiada za dostęp do lepszych surowców oraz bonus jakości/urobku.",
        "Poziom 20 zachowuje dawny wymóg profesji 200; od 21 wymagania rosną do profesji 400, a po 40 kolejne piętra pozostają dostępne przy profesji 400.",
        "Im głębiej w lochu profesyjnym, tym wyższy poziom zasobów może wypaść.",
        "Auto-profesja uruchomiona wewnątrz lochu pozostaje w aktualnej komorze i dalej zbiera zasoby.",
        "Prowadzenie: prowadz kopalnia, prowadz zatopiona grota, prowadz pradawny las, prowadz ogrod alchemika.",
    ],
    "zasoby_swiata": [
        "World Resources Pack dodaje szeroki przekrój realnych zasobów z całego świata.",
        "Dodano 160 nowych realnych ryb: po 40 do rzeki, jeziora, morza i oceanu.",
        "Dodano 80 nowych roślin, ziół i przypraw.",
        "Dodano 50 nowych rodzajów drewna.",
        "Dodano 40 nowych realnych rud i minerałów.",
        "Nowe ryby są faktycznie łowione przez low i low on.",
        "Nowe rośliny są faktycznie zbierane przez zbieraj i zbieraj on.",
        "Nowe drewna są faktycznie pozyskiwane przez tnij i tnij on.",
        "Nowe rudy są faktycznie wydobywane w Kopalni Głębinowej przez kop i kop on.",
        "Zasoby odblokowują się wraz z levelem narzędzia, a rudy także z głębokością.",
        "atlas ryby, atlas zioła, atlas rośliny, atlas drewno i atlas rudy automatycznie obejmują nowy pakiet.",
        "To duży grywalny przekrój zasobów świata, a nie literalna lista każdej naukowo opisanej species na Ziemi.",
    ],
    "atlas_kompletny": [
        "Atlas zasobów jest teraz kompletny.",
        "atlas ryby pokazuje wszystkie istniejące ryby w grze, a następnie podział na rzekę, jezioro, morze i ocean.",
        "atlas drewno pokazuje wszystkie istniejące rodzaje drewna oraz podział według terenów.",
        "atlas rudy pokazuje wszystkie istniejące rudy, wymagany level Kilofa i minimalną głębokość Kopalni Głębinowej.",
        "atlas zioła i atlas rośliny pokazują wszystkie istniejące zioła i rośliny oraz grupy występowania.",
        "Długie listy są dzielone na krótsze części, żeby NVDA czytał je wygodniej.",
        "Można nadal wpisać atlas <nazwa surowca>, aby usłyszeć informacje o jednym konkretnym zasobie.",
        "Pełne atlasy są bezpośrednio oparte na aktywnych listach RESOURCE_IDS, więc nowy zasób nie powinien wypaść z pełnego spisu.",
    ],
    "kopalnia_200": [
        "Kopalnia Głębinowa generuje piętra dynamicznie od pierwszego poziomu i może rozwijać się dalej na żądanie.",
        "Kryształowa Komnata prowadzi przez down na poziom 1.",
        "Każde udane kopanie na najgłębszym odblokowanym poziomie daje 1 uderzenie w ścianę w dół.",
        "Każda ściana ma własny losowy próg uderzeń zapisany trwale w SQLite.",
        "Im głębiej, tym lepsza pula rud.",
        "Level Kilofa nadal ogranicza jakość wydobycia.",
        "1-9: Kamień i Miedź.",
        "10-24: Miedź i Żelazo.",
        "25-49: Żelazo i Srebro.",
        "50-99: Srebro i Złoto.",
        "100-119: Złoto i Kobalt.",
        "120-139: Kobalt i Kamień Runiczny.",
        "140-159: Kamień Runiczny i Smocza Stal.",
        "160-179: Smocza Stal i Ruda Astralna.",
        "180-199: Ruda Astralna i Ruda Pustki.",
        "200+: Ruda Pustki i Eternium; nowe zasoby 201-400 respektują cap narzędzia/profesji 400, a dalsza głębokość nie zwiększa mocy ekonomii ponad 400.",
        "kopalnia pokazuje aktualne położenie/piętro, najgłębszy odblokowany poziom, postęp ściany, auto-kopanie, Górnictwo, Kilof i dostępne progi rud.",
        "kop on może wystartować w ręcznej części Kryształowej Jaskini, sam dojść do poziomu 1 i po przebiciu ściany schodzić na kolejny odblokowany poziom.",
    ],
    "auto_chodzenie": [
        "Auto-profesje nie chodzą samodzielnie.",
        "low on łowi tylko w aktualnym łowisku i nie przemieszcza postaci.",
        "zbieraj on zbiera tylko w aktualnym miejscu i nie przemieszcza postaci.",
        "tnij on ścina tylko w aktualnym miejscu i nie przemieszcza postaci.",
        "kop on jest wyjątkiem: w ręcznej części Kryształowej Jaskini może sam dojść do poziomu 1, a potem automatycznie schodzi na kolejne odblokowane poziomy po przebiciu ściany.",
        "Manualny ruch gracza nadal wyłącza aktywne auto.",
        "off nadal dokańcza bieżącą akcję i dopiero potem zatrzymuje automat.",
    ],
    "laki": [
        "Strefa Łąk składa się teraz z czterech lokacji.",
        "Srebrna Łąka jest centralnym punktem strefy.",
        "Łąka Mięty leży na wschód od Srebrnej Łąki i prowadzi dalej do Brzegu Rzeki.",
        "Łąka Kwiatów leży na zachód od Srebrnej Łąki i prowadzi dalej do Gaju Szeptów.",
        "Łąka Nadjeziorna leży na południe od Srebrnej Łąki i prowadzi dalej do Srebrnego Jeziora.",
        "Na wszystkich łąkach działa zbieraj i zbieraj on.",
        "Łąka Mięty częściej daje Miętę i Melisę.",
        "Łąka Kwiatów częściej daje Rumianek, Lawendę i Krwawnik.",
        "Łąka Nadjeziorna ma zioła wilgotnych terenów, a na wyższych poziomach Sierpa może pojawić się Gwiezdny mech.",
        "Użyj prowadz srebrna laka, prowadz laka miety, prowadz laka kwiatow albo prowadz laka nadjeziorna.",
    ],
    "auto_off": [
        "low off, fish off, kop off, mine off, tnij off, woodcut off i zbieraj off zatrzymują automat po dokończeniu bieżącej akcji.",
        "Jeśli akcja już trwa, nie jest anulowana.",
        "Po zakończeniu dostajesz normalnie surowiec, XP profesji i XP używanego narzędzia.",
        "Następna automatyczna akcja już się nie rozpoczyna.",
        "Wymuszone zatrzymanie, na przykład wyjście z gry, podróż albo przełączenie na inną auto-aktywność, nadal może przerwać akcję natychmiast.",
    ],
    "kurs_walut": [
        "Nominały wspólnego salda przeliczają się automatycznie.",
        "Jedno wspólne saldo z nominałami: srebro, złoto i mithril.",
        "Nominały: 100 srebra = 1 złoto; 1 000 000 złota = 1 mithril.",
        "Saldo jest automatycznie przedstawiane w najwyższych możliwych nominałach.",
        "Automatyczne przeliczanie działa w portfelu oraz Banku Dusz.",
        "Stara ręczna komenda wymiany została usunięta.",
        "Istniejący majątek nie jest zerowany; zachowuje pełną wartość.",
    ],
    "wiecej_ryb": [
        "Dodano 40 nowych gatunków ryb: po 10 do rzeki, jeziora, morza i oceanu.",
        "Nowe ryby mają progi Wędki od levelu 1 aż do 200.",
        "Rzeka otrzymała między innymi Ukleję Rzeczną, Pstrąga Potokowego, Tajmienia Rzecznego, Lipienia Duchów i Wiecznego Smoka Rzecznego.",
        "Jezioro otrzymało między innymi Kiełbia Jeziorowego, Złotego Lina, Kryształową Sieję, Astralnego Szczupaka i Wiecznego Węża Jeziora.",
        "Morze otrzymało między innymi Belonę, Prażmę Morską, Kongera, Śledzia Burzy i Wiecznego Smoka Morza.",
        "Ocean otrzymał między innymi Rybę Latającą, Tuńczyka Żółtopłetwego, Marlina Czarnego, Marlina Pustki i Lewiatana Świata.",
        "Komenda woda automatycznie pokazuje nowe ryby po osiągnięciu wymaganego levelu Wędki.",
        "fish losuje z dokładnie tej samej listy, którą pokazuje woda.",
        "Nowe ryby są widoczne w atlasie odpowiedniego łowiska.",
        "Nowe ryby można normalnie przechowywać w Siatce i sprzedawać.",
    ],
    "oddawanie_zadan": [
        "Po wykonaniu celu zadania dziennik pokazuje GOTOWE DO ODDANIA.",
        "Wróć do NPC, który dał zadanie.",
        "oddaj zadanie i oddaj questa automatycznie oddają jedyne gotowe zadanie u NPC w tej lokacji.",
        "oddaj <nazwa zadania> pozwala wybrać konkretne zadanie.",
        "Przy ukończonym zadaniu NPC komentuje wykonanie, a potem NVDA czyta, co dokładnie wręcza jako nagrodę.",
        "Questy profesyjne i rzemieślnicze zawsze mają także nagrodę w walucie; istniejące wypłaty zachowują balans gry.",
        "zdaj zadanie oraz turnin są aliasami.",
        "Jeśli kilka zadań jest gotowych u NPC w tej samej lokacji, gra nie zgaduje i prosi o pełną nazwę.",
        "Jeśli zadanie nie jest ukończone, oddaj podaje aktualny postęp.",
        "talk to <NPC> działa tak samo jak talk <NPC>.",
        "Rozmowa z NPC rozpoznaje, czy wracasz z zadaniem w toku albo gotowym do oddania, ale przyjęcie i oddanie pozostają jawnymi komendami gracza.",
        "Oddawanie collect nadal zabiera wymagane przedmioty dopiero przy rozliczeniu zadania.",
        "Oddawanie collect_category nadal korzysta z właściwego magazynu profesji i inventory.",
    ],
    "woda": [
        "Komenda woda / łowisko zaczyna od jasnej informacji o typie bieżącego łowiska, np. Rzeka, Jezioro, Morze, Ocean, Kanał albo Zatopiona Grota.",
        "Dla specjalnych miejsc nazwa łowiska jest oddzielona od technicznego ekosystemu ryb; Czarny Kanał mówi Kanał, a nadal korzysta z rzecznej progresji gatunków.",
        "Pokazuje aktualny level Wędki i dokładną liczbę gatunków, które rzeczywiście mogą zostać wylosowane w tym miejscu.",
        "Pokazuje ile z obecnej puli już odkryto w Dzienniku ryb oraz ile pozostaje nieodkrytych.",
        "Nazwy czytane przez woda dotyczą tylko gatunków już odkrytych przez tę postać; nieodkryte pozostają jako licznik.",
        "Czarny Kanał od Wędki 30 ma własną rzeczywistą pulę Ślepego Węgorza Kanałowego, a Zatopiona Grota ogranicza pulę zgodnie z głębokością.",
        "Jeśli kolejny próg zwykłego ekosystemu jest zablokowany, woda podaje wymagany level Wędki.",
        "Ryby nie mają twardego limitu sztuk, nie ma przełowienia i łowiska nie wyczerpują się od łowienia.",
    ],
    "dziennik_ryb": [
        "dziennikryb / fishjournal - trwały Dziennik ryb zapisany osobno dla każdej postaci.",
        "Pokazuje liczbę odkrytych gatunków, zarejestrowanych połowów i odkrytych gatunków legendarnych.",
        "dziennikryb lista czyta wszystkie odkryte gatunki, ich kolekcjonerską rzadkość, liczbę połowów oraz rekord długości i masy.",
        "dziennikryb <nazwa ryby> pokazuje szczegóły konkretnego odkrytego gatunku i typy wód, w których występuje.",
        "Pierwszy połów nowego gatunku jest natychmiast czytany przez NVDA jako NOWY GATUNEK W DZIENNIKU RYB.",
        "Pobicie rekordu długości lub masy jest natychmiast czytane przez NVDA.",
        "Rzadkości gatunków: pospolita, niepospolita, rzadka, epicka i legendarna. Rzadkość jest kolekcjonerska i nie daje bonusów bojowych.",
        "Starszy save może odtworzyć gatunki nadal obecne w Siatce. Dokładne rekordy długości/masy i pełne nowe wpisy są liczone od v0.9.5.",
    ],
    "gotowanie_rozbudowane": [
        "Gotowanie korzysta z Noża Kucharskiego level 1-400.",
        "Nie jest osobnym levelem postaci i nie dodaje Character XP.",
        "Gotowanie jest osobną profesją 1-400; jej poziom skraca czas i odblokowuje receptury. Nóż rozwija się osobno 1-400 i daje bonus produktu.",
        "Potrawy przygotowuje się w Karczmie Pod Błękitnym Płomieniem albo na Targu Rybnym.",
        "gotowanie pokazuje stan systemu i aktualny Nóż Kucharski.",
        "gotuj lista pokazuje wszystkie receptury Gotowania.",
        "gotuj <potrawa> przygotowuje wybraną potrawę.",
        "receptury cook nadal działa.",
        "Receptury mają progi Gotowania: 1,10,20,30,40,50,60,70,80,90,95,99,100,120,140,160,180 i 200.",
        "Dodano Okoń w Ziołowej Skorupce, Zupę ze Srebrnego Pstrąga, Zapiekankę Jeziornego Rybaka, Makrelę Korzenną, Łososia z Ziołami i Rosół z Księżycowego Węgorza.",
        "Każda akcja Gotowania wykorzystuje czas wynikający z poziomu profesji Gotowanie; Nóż Kucharski nie skraca czasu.",
        "Gotowanie level 1 daje 12 sekund bazowego czasu, a Gotowanie level 200 daje 4 sekundy; level Noża nie skraca czasu.",
        "Tier Noża daje szansę na dodatkową porcję.",
        "Gotowanie zużywa składniki z właściwych magazynów profesji oraz inventory.",
        "Potrawy przywracają HP, a część również Manę.",
        "Questy Kucharza Marcela pozostają i nadal wykorzystują Gotowanie.",
    ],
    "hp_bossow_lochow": [
        "Bossowie Krypty i Wieży Astralnej mają teraz HP według numeru piętra.",
        "Wzór: numer piętra razy 1000 HP.",
        "Krypta piętro 10: 10000 HP.",
        "Krypta piętro 20: 20000 HP.",
        "Krypta piętro 100: 100000 HP.",
        "Krypta piętro 200: 200000 HP.",
        "Wieża Astralna poziom 100: 100000 HP.",
        "Wieża Astralna poziom 150: 150000 HP.",
        "Wieża Astralna poziom 200: 200000 HP.",
        "Zwykłe moby nadal mają globalne 2 razy HP z v0.6.94.",
        "Bossowie świata poza Kryptą i Wieżą zachowują swoje 2 razy HP.",
        "Damage i nagrody bossów nie zostały zwiększone.",
        "consider automatycznie korzysta z nowych wartości HP.",
    ],
    "hp_mobow": [
        "Wszystkie moby i bossowie mają teraz globalnie 2 razy więcej maksymalnego HP.",
        "Zmiana obejmuje zwykłych przeciwników, bossów świata, manekina treningowego, Kryptę 1-200 i Wieżę Astralną 100-200.",
        "Obrażenia mobów nie zostały zwiększone.",
        "Samo podwojenie HP nie daje automatycznie większej waluty ani lootu; późniejsze wersje balansu liczą EXP z realnej siły konkretnego przeciwnika.",
        "Mechaniki bossów nadal korzystają z ich aktualnego podwojonego maksymalnego HP.",
        "Respawn pozostaje bez zmian i przywraca pełne nowe maksymalne HP.",
        "consider automatycznie pokazuje i ocenia nowe wartości HP.",
        "Moby i bossowie nadal nie są agresywni.",
        "Walka działa w czasie rzeczywistym: gracz i przeciwnik mają niezależne timery akcji.",
    ],
    "soul_xp_bloki": [
        "Wymagane Soul XP zachowuje starą krzywą 1-200, a w zakresie 201-400 rośnie kontrolowanie bez wykładniczej eksplozji.",
        "Soul Level 1-10 używa mnożnika x1. Każdy kolejny pełny blok 10 leveli podnosi mnożnik o 25 procent.",
        "Bazowy wzór wynosi 180 + 60 razy Soul Level minus 1, a następnie jest mnożony przez 1,25 do potęgi liczby ukończonych bloków 10 leveli.",
        "Przykład: z Soul Level 10 na 11 potrzeba 720 XP.",
        "Przykład: z Soul Level 11 na 12 potrzeba 975 XP.",
        "Przykład: z Soul Level 21 na 22 potrzeba około 2156 XP.",
        "Przykład: z Soul Level 51 na 52 potrzeba około 9705 XP.",
        "Od v0.8.64 pojedynczy kill ma też limit Soul XP zależny od rangi przeciwnika, więc carry nie przeskakuje dziesiątek Soul Leveli naraz.",
        "Już zdobyty Soul XP pozostaje zapisany i nie jest resetowany.",
        "Soul Level ma zakres 1-400.",
    ],
    "consider": [
        "consider <mob>, con <mob> albo ocen <mob> ocenia przeciwnika bez rozpoczynania walki.",
        "Jeśli w lokacji jest dokładnie jeden mob, samo consider oceni właśnie jego; przy wielu mobach podaj nazwę lub numer wystąpienia.",
        "Od v1.13.31 consider używa tej samej prognozy Adaptive Combat co realne starcie: uwzględnia aktualną postać, Speed/multi-hit oraz wszystkich żywych członków drużyny stojących w tej samej lokacji.",
        "Pokazuje prognozowane skalowane HP moba, bazowe max HP, mnożnik HP, rangę Adaptive Combat i liczbę członków lokalnej drużyny.",
        "Pokazuje szacowane obrażenia odpowiedzi już po adaptacyjnym skalowaniu względem twojego HP, obrony, redukcji i uniku.",
        "Twój zwykły atak jest liczony jako hit oraz pełna akcja z aktualną liczbą trafień; w drużynie consider pokazuje też łączną zwykłą akcję lokalnej drużyny.",
        "Ocena może być: bardzo słaby, słaby, korzystny, porównywalny, niebezpieczny, bardzo niebezpieczny albo śmiertelnie groźny.",
        "Bossowie są oceniani ostrożniej, ponieważ specjalne mechaniki zwiększają ryzyko; jeśli boss ma opis mechaniki, consider go przeczyta.",
        "Consider pokazuje również prognozowany mnożnik rekompensaty EXP/waluty Adaptive Combat; drop chance i unikalne dropy nie są przez niego mnożone.",
        "Consider nie angażuje moba, nie wykonuje ataku, nie zużywa Many i nie mutuje skali przeciwnika. To bezpieczna prognoza przed walką.",
    ],
    "wolniejsze_staty": [
        "Każda z sześciu statystyk ma własny licznik EXP i własny próg.",
        "Próg startuje od 100 EXP i rośnie osobno wraz z wartością danej statystyki.",
        "Po osiągnięciu progu rośnie tylko wskazana statystyka; pozostałe zachowują własny postęp.",
        "Statystyki nadal nie mają ręcznego rozdawania punktów ani levelu postaci.",
        "Stary wspólny Postęp Rozwoju jest jednorazowo migrowany do sześciu osobnych liczników bez utraty zapisanego postępu.",
    ],
    "wieza_astralna": [
        "Wieża Astralna jest drugim lochowym endgame obok Krypty.",
        "Wejście znajduje się przy Zapomnianej Kapliczce. Wpisz prowadz wieza astralna.",
        "Do wejścia na pierwszy poziom potrzebny jest Soul Level 100.",
        "Wieża zaczyna właściwe piętra od 100 i nie ma górnego limitu; 100-200 pozostaje ręcznie zaprojektowaną częścią.",
        "Boss stoi co 10 poziomów: 100, 110, 120 i dalej bez końca.",
        "Boss blokuje drogę w górę, dopóki żyje.",
        "Pokonanie bossa odblokowuje niezależny Astralny Portal/checkpoint.",
        "Astralny Portal działa wyłącznie przy Astralnej Bramie.",
        "Komenda astralportal pokazuje checkpointy.",
        "Komenda astralportal 150 przenosi na poziom 150, jeśli checkpoint jest odblokowany.",
        "Zwykłe moby zostawiają 1 element Astralnego ekwipunku, bossowie 3.",
        "Ręcznie zaprojektowani bossowie 100-200 zachowują unikalne relikty; dalsi bossowie proceduralni pojawiają się co 10 poziomów bez końca.",
        "Wieża ma własne moby, bossów, mechaniki i klimat gwiezdny, niezależny od Krypty.",
        "Moby i bossowie nie atakują automatycznie.",
        "Walka działa w czasie rzeczywistym: zwykłe ataki i auto kolejka wykonują się automatycznie.",
    ],
    "soul_tier45_krypta200": [
        "Broń Duszy ma 40 Tierów rozłożonych na Soul Level 1-400.",
        "Progi: 1, 10, 20, 25, 35, 45, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 200.",
        "Każdy Tier 2-20 ma własną jednorazową Próbę Broni Duszy u Kapłana Elora.",
        "Po osiągnięciu progu użyj quest list Kapłan Elor, wykonaj właściwą Próbę, a następnie wpisz unlock.",
        "Tier 4: Soul 25 i 5 Szkieletowych Strażników.",
        "Tier 7: Soul 60 i 3 Widma Krypty.",
        "Tier 13: Soul 120 i boss Próby na piętrze 120 Krypty.",
        "Tier 19: Soul 180 i boss Próby na piętrze 180 Krypty.",
        "Tier 20 wymaga Soul 200 i kończy mistrzowską część 1-200; Próby Tierów 21-40 kontynuują progresję Broni Duszy do Soul 400.",
        "Stare postacie są automatycznie migrowane: dawny Tier 2->4, 3->7, 4->13, 5->19.",
        "Nie ma resetu Soul Levelu, Soul XP ani ukończonych prób.",
    ],
    "lancuchy_specjalistow": [
        "Haldor, Marcel i Orin mają teraz po 3 osobne etapy zleceń.",
        "Etap 1 jest dostępny od levelu właściwej profesji 1.",
        "Etap 2 wymaga ukończenia etapu 1 i levelu właściwej profesji 100.",
        "Etap 3 wymaga ukończenia etapu 2 i levelu właściwej profesji 200.",
        "Haldor: Żelazne sztabki, Runiczny Talizman Straży, Talizman Wiecznej Duszy.",
        "Marcel: Pieczone ryby rzeczne, Runiczny Półmisek Rybny, Wieczna Uczta Oceanu.",
        "Orin: Mikstury Many, Najwyższe Mikstury Leczenia, Eliksir Wiecznej Duszy.",
        "Rozmowa ze specjalistą podaje stan każdego etapu: aktywne, ukończone, dostępne albo zablokowane.",
        "Po odblokowaniu wyższego etapu specjalista automatycznie proponuje najwyższy dostępny etap.",
        "Każdy etap pozostaje powtarzalny z 30-minutowym cooldownem.",
    ],
    "bank": [
        "Bank Dusz znajduje się na Rynku u Bankiera Aldrena.",
        "prowadz bank prowadzi bezpośrednio na Rynek.",
        "bank pokazuje saldo bankowe oraz przedmioty w skrytce.",
        "bank wplac 100 wpłaca 100 srebra do wspólnego salda.",
        "bank wplac 5 zlota wpłaca 500 srebra wartości; bank wplac 1 mithril wpłaca 100000000 srebra wartości.",
        "bank wyplac <ile> <nominał> wypłaca wskazaną wartość z tego samego salda.",
        "bank wplac wszystko wpłaca całe wspólne saldo z portfela.",
        "bank wyplac wszystko wypłaca całe wspólne saldo z banku.",
        "bank wloz <przedmiot> [ile] przenosi zwykły przedmiot z inventory do trwałej skrytki.",
        "bank wyjmij <przedmiot> [ile] przenosi przedmiot ze skrytki do inventory.",
        "Założonego elementu wyposażenia nie można schować w banku.",
        "Bank jest trwały w SQLite i nie znika po wylogowaniu ani restarcie serwera.",
        "Bank nie pobiera opłat.",
    ],
    "questy_specjalistow": [
        "Mistrz Rzemiosła Haldor ma 3-etapowy łańcuch powtarzalnych zleceń rzemieślniczych.",
        "Haldor prosi o 3 Żelazne sztabki i nagradza XP Młota Rzemieślniczego oraz srebrem.",
        "Kucharz Marcel ma 3-etapowy łańcuch powtarzalnych zleceń Gotowania.",
        "Marcel prosi o 3 Pieczone ryby rzeczne i nagradza XP Noża Kucharskiego oraz srebrem.",
        "Mistrz Alchemii Orin ma 3-etapowy łańcuch powtarzalnych zleceń Alchemii.",
        "Orin prosi o 3 Mikstury Many i nagradza XP profesji Alchemia, XP Moździerza oraz srebrem.",
        "Każde z tych zleceń ma 30 minut odnowienia po ukończeniu.",
        "Rozmowa ze specjalistą nadal najpierw podaje informacje o jego narzędziu i recepturach.",
    ],
    "sprzedaj_wszystko": [
        "sprzedaj wszystko siatka sprzedaje wszystkie ryby z Siatki wyłącznie rybakom na Targu Rybnym.",
        "sprzedaj wszystko sakwa sprzedaje Dagnie cały urobek Górnictwa: rudy, minerały i surowe klejnoty.",
        "sprzedaj wszystko stos sprzedaje całe drewno wyłącznie Drwalowi Branowi w Obozie Drwala.",
        "sprzedaj wszystko torba sprzedaje wszystkie zioła wyłącznie Zielarce Liorze w Chacie Zielarki.",
        "Działają też: sprzedaj wszystko ryby, rudy, drewno i ziola.",
        "sprzedaj wszystko / sell all sprzedaje WYŁĄCZNIE niezałożone EQ z inventory u zwykłego kupca.",
        "Sell all nigdy nie sprzedaje mikstur, consumables, lootu, materiałów, narzędzi, quest itemów ani aktualnie założonego EQ.",
        "sprzedaj wszystko przedmioty działa tak samo bezpiecznie: tylko niezałożone EQ.",
        "Każda kategoria profesyjna nadal wymaga właściwego punktu skupu.",
        "Sprzedaż surowców profesji daje dodatkowy EXP właściwej specjalizacji: ryby -> Wędkarstwo, urobek Dagny -> Górnictwo, drewno -> Drwalstwo, zioła -> Zielarstwo.",
        "EXP sprzedażowy wynosi 1 bazowy EXP za sztukę i korzysta z globalnego mnożnika EXP profesji; nie daje EXP narzędzia.",
        "Po sprzedaży gra podaje liczbę sztuk, rodzajów i zarobek.",
    ],
    "naturalne_naucz": [
        "U nauczyciela aktywnej klasy możesz uczyć się skilli naturalną nazwą kategorii.",
        "naucz leczenie wybiera najwyżej odblokowane leczenie tej klasy, którego jeszcze nie znasz.",
        "naucz tarcza wybiera najwyżej odblokowaną osłonę.",
        "naucz unik wybiera najwyżej odblokowany unik.",
        "naucz drain albo naucz wysysanie wybiera skill wysysający życie.",
        "naucz dobij wybiera najwyżej odblokowaną umiejętność execute.",
        "Ofensywne przykłady: naucz ciecie, naucz pocisk, naucz ogien, naucz burza, naucz mlot, naucz strzal.",
        "System bierze pod uwagę tylko skille klasy nauczyciela, przy którym aktualnie stoisz.",
        "Najpierw preferuje skill, którego jeszcze nie znasz, a potem najwyższy dostępny próg Soul.",
        "Pełne nazwy i numery skilli nadal działają.",
    ],
    "czas_narzedzi": [
        "Każda czynność narzędzia ma teraz realny czas wykonania.",
        "Przy profesji level 1: Wędkarstwo 16 sekund, Górnictwo 30, Drwalstwo 24, Kowalstwo 20, Gotowanie 12, Zielarstwo 10, Alchemia 18, Jubilerstwo 20 sekund.",
        "Czas skraca się stopniowo wraz z levelem właściwej profesji; level narzędzia nie skraca czasu.",
        "Przy profesji level 200: Wędkarstwo 3 sekundy, Górnictwo 10, Drwalstwo 8, Kowalstwo 7, Gotowanie 4, Zielarstwo 3, Alchemia 6, Jubilerstwo 7 sekund.",
        "Po wpisaniu wedka, kilof, pila, mlot, noz, sierp, mozdzierz albo szczypce gra podaje aktualny czas akcji wynikający z levelu profesji.",
        "Auto-łowienie, auto-kopanie, auto-Drwalstwo i auto-Zielarstwo używają tego samego realnego czasu.",
        "Crafting, Gotowanie i Alchemia także czekają rzeczywistą liczbę sekund przed ukończeniem receptury.",
    ],
    "nazwy_narzedzi": [
        "Po wpisaniu nazwy narzędzia gra od razu podaje jego aktualną pełną nazwę Tieru.",
        "Przykład: wedka może powiedzieć Aktualna nazwa narzędzia: Wędka Ucznia.",
        "Po awansie Tieru nazwa zmienia się automatycznie, np. na Wędka Rzeczna albo Wędka Srebrnego Haczyka.",
        "Działa dla: wedka, kilof, pila, mlot, noz, sierp, mozdzierz i szczypce.",
        "Potem gra nadal podaje level, XP, użycia, Tier, bonus i następny Tier.",
        "Komenda narzedzia pokazuje aktualne nazwy wszystkich posiadanych narzędzi.",
    ],
    "odpoczynek_wszystko": [
        "Odpoczynek zawsze regeneruje wszystko, co można regenerować poza walką.",
        "Co 5 sekund odnawia 10 procent maksymalnego HP oraz 10 procent maksymalnej Many.",
        "Postać bez Many regeneruje tylko HP.",
        "odpoczywaj, rest i regen uruchamiają ten sam pełny odpoczynek.",
        "regen mana oraz mana regen również uruchamiają pełny odpoczynek HP i Many.",
        "Nie ma osobnego trybu regenerującego wyłącznie Manę.",
        "Ruch albo aktywna akcja przerywa odpoczynek.",
    ],
    "specjalisci_profesji": [
        "Soulbound ma ośmiu głównych specjalistów profesji odpowiadających wszystkim ośmiu profesjom i narzędziom.",
        "Mistrz Wędkarstwa Neris: Targ Rybny.",
        "Mistrz Górnictwa Kordan: Wejście do Kryształowej Jaskini.",
        "Mistrz Drwalstwa Oren: Obóz Drwala.",
        "Mistrz Rzemiosła Haldor: Kuźnia Dusz.",
        "Kucharz Marcel: Karczma Pod Błękitnym Płomieniem.",
        "Mistrzyni Zielarstwa Sena: Chata Zielarki.",
        "Mistrz Alchemii Orin: Chata Zielarki.",
        "Jubilerka Mirella: Pracownia Jubilerska.",
        "Rozmowa ze specjalistą pokazuje level profesji oraz odpowiadającego narzędzia, XP, Tier, bonus i tempo pracy.",
        "Kucharz, Rzemieślnik i Alchemik przypominają również odpowiednią komendę receptur.",
        "Specjaliści są przyjaznymi NPC i nie można ich atakować.",
    ],
    "regen_mana": [
        "Od v0.6.84 regen mana nie jest osobnym trybem.",
        "regen mana i mana regen uruchamiają pełny odpoczynek.",
        "Odpoczynek odnawia jednocześnie HP i Manę co 5 sekund.",
        "mana nadal pokazuje aktualną i maksymalną Manę.",
        "mana stop zatrzymuje aktywny odpoczynek.",
    ],
    "sprzedaz_hurtowa": [
        "sprzedaj ryby siatka sprzedaje wszystkie ryby wyłącznie rybakom na Targu Rybnym.",
        "sprzedaj rudy sakwa sprzedaje Dagnie cały urobek Górnictwa z Sakwy, w tym rudy, minerały i surowe klejnoty.",
        "sprzedaj drewno stos sprzedaje całe drewno wyłącznie Drwalowi Branowi w Obozie Drwala.",
        "sprzedaj ziola torba sprzedaje wszystkie zioła wyłącznie Zielarce Liorze w Chacie Zielarki.",
        "Skup jest profesyjny: ryby tylko Targ Rybny; rudy, minerały i surowe klejnoty tylko Dagna; drewno tylko Drwal Bran; zioła tylko Zielarka Liora.",
        "Hurtowa sprzedaż podaje liczbę sztuk, liczbę rodzajów i łączny zarobek.",
        "Sprzedaż daje EXP Charyzmy zależny od wartości transakcji; hurtowa sprzedaż nie pompuje Charyzmy liniowo liczbą tanich sztuk.",
        "sprzedaj przedmioty sprzedaje z inventory tylko rzeczy z jawną ceną sprzedaży i dozwolone w aktualnej lokacji.",
        "Duplikat możesz wskazać numerem, np. sprzedaj 2.talizman korzeni; założone egzemplarze nie są sprzedawane.",
        "sprzedaj przedmioty nie sprzedaje narzędzi, mikstur, założonego wyposażenia ani rzeczy bez ceny.",
    ],
    "mana_stats_eq": [
        "stats zawsze pokazuje Mana: aktualna z maksymalnej.",
        "Klasa bez Many zobaczy Mana: 0 z 0.",
        "Klasa magiczna albo multiclass magiczny zobaczy aktualną i maksymalną Manę.",
        "eq działa jak equipment.",
    ],
    "wartosc_magazynow": [
        "Wszystkie cztery magazyny profesji pokazują teraz podsumowanie ilości i wartości.",
        "siatka/net: łączna liczba ryb, liczba gatunków i wartość sprzedaży.",
        "sakwa/bag: cały urobek Górnictwa — rudy, minerały i surowe klejnoty; pokazuje liczbę sztuk, rodzajów i wartość sprzedaży u Dagny.",
        "drewno/stos/woodpile: łączna liczba sztuk drewna, liczba rodzajów i wartość sprzedaży.",
        "ziola/herbs: łączna liczba ziół, liczba rodzajów i wartość sprzedaży.",
        "Srebro, złoto i mithril są nominałami jednego wspólnego salda.",
        "Podsumowania obejmują tylko zawartość danego magazynu, nie zwykły inventory.",
        "Sprawdzenie magazynu niczego nie sprzedaje ani nie usuwa.",
    ],
    "wartosc_siatki": [
        "Komenda siatka albo net pokazuje każdą rybę i jej ilość.",
        "Na końcu podaje łączną liczbę wszystkich ryb w siatce.",
        "Podaje też liczbę różnych gatunków ryb.",
        "Szacowany zarobek jest liczony z aktualnych cen sprzedaży każdej ryby pomnożonych przez jej ilość.",
        "Portfel podaje jedno saldo rozbite na mithril, złoto i srebro.",
        "Wartość obejmuje tylko ryby aktualnie znajdujące się w Siatce, nie ryby w zwykłym inventory.",
        "Podsumowanie nie sprzedaje ryb. To tylko informacja przed sprzedażą.",
    ],
    "tempo_profesji": [
        "Aktualnie wszystkie osiem profesji ma zakres 1-400; tempo pracy zależy od profesji, a jakość/odblokowania zasobów od osobnego narzędzia.",
        "Każda profesja korzysta z osiągalnej krzywej 1-400; stare progi 1-200 pozostają zachowane, a 201-400 jest dalszą progresją.",
        "Level profesji skraca czas pracy i spełnia wymagania receptur/zleceń; level narzędzia odblokowuje lepsze surowce oraz zwiększa jakość/bonus urobku.",
        "Wszystkie osiem profesji rozwija się od 1 do 400 według aktualnej progresji.",
        "Narzędzia mają osobną progresję XP 1-400; wpisz help narzedzia200 albo help progresja400 po szczegóły.",
        "Nie ma trwałości ani zużywania narzędzi.",
    ],
    "zakladanie_lootu": [
        "Gracz sam decyduje, jaki konkretny element EQ zakłada. Wyjątek to pierścienie i talizmany: po wybraniu przedmiotu gra może automatycznie wybrać wolny albo słabszy z dwóch równoległych slotów.",
        "Gdy masz kilka przedmiotów dla jednego slotu, załóż <slot> pokazuje dostępne opcje i niczego nie zmienia. Aby założyć wybrany przedmiot, wpisz jego pełną nazwę.",
        "Całe EQ ma wymaganie Biegłości, nie Soul Levelu. Poziom startowy to 1, a kolejne progi są co 10 aż do 400. Materiałowe EQ ma kilka wariantów Biegłości w ramach tego samego materiału. Dla nieklasowego EQ liczy się najwyższa Biegłość aktywnej klasy.",
        "Jeśli zwykły slot jest zajęty, samo załóż hełm / zbroja / rękawice / nogi / buty niczego nie podmienia. Dokładna nazwa nowego przedmiotu jest świadomą decyzją o zastąpieniu starego.",
        "Pierścienie i talizmany zakładają się automatycznie: najpierw do wolnego slotu, a gdy oba są zajęte — zastępują słabszy. Ręczne sloty 1/2 nadal działają.",
        "Skróty: zp pokazuje pierścienie i zp <numer> zakłada wybrany; zt robi to samo dla talizmanów. zp1/zp2 i zt1/zt2 wymuszają konkretny slot.",
        "Nowe sloty EQ: naramienniki, pas, peleryna, karwasze, kolczyki i relikt.",
        "Zdejmowanie jest ręczne: zdejmij hełm, zbroja, naramienniki, pas, peleryna, karwasze, relikt, pierścień 1, talizman 2 itd.",
        "Założone EQ nadal jest niesprzedawalne; po zdjęciu staje się zwykłym wolnym egzemplarzem i może zostać sprzedane, jeśli jego kategoria na to pozwala.",
        "Zmiana ekwipunku podczas aktywnej walki nadal jest zablokowana.",
    ],
    "skill200": [
        "Wszystkie umiejętności mają Skill Level od 1 do 400 i rozwijają się wyłącznie przez używanie konkretnego skilla/spella.",
        "v0.8.64 zmniejsza przyrost wymaganego Skill XP z +25 do +8 na level i podnosi typową nagrodę za użycie do 25-35 XP.",
        "Moc rośnie malejąco: około x1,495 przy Skill Level 100 i około x1,745 przy 200, zamiast starego x2,49.",
        "Cooldown skraca się przez całe 1-400: około 12,4 procent przy 100, około 24,9 procent przy 200 i maksymalnie około 35 procent przy 400.",
        "Na Skill Level 400 XP zostaje wyzerowane i skill osiąga maksymalny poziom.",
    ],
    "wolniejszy_xp_narzedzi": [
        "Narzędzia mają level 1-400 i 40 Tierów, bez trwałości i bez psucia.",
        "v0.8.64 używa krzywej: 60 + 8 razy level minus 1 XP do następnego poziomu narzędzia.",
        "Level 1->2 wymaga 60 XP; level 100->101 852 XP; level 199->200 1644 XP.",
        "XP przyznawane przez konkretne akcje pozostaje zależne od aktywności i bonusów narzędzia.",
        "Nieużywane narzędzia nie zdobywają XP ani użyć.",
    ],
    "skille100_200": [
        "Każda z 14 klas dostała 4 nowe umiejętności endgame.",
        "Historyczne progi endgame są teraz Biegłością klasy 100, 140, 180 i 200.",
        "Łącznie dodano 48 nowych skilli.",
        "Nowe skille trzeba nauczyć się u właściwego nauczyciela klasy, tak jak wcześniejsze.",
        "Skill Level każdego skilla rozwija się osobno od 1 do 400; zakres 201-400 ma malejący przyrost mocy.",
        "Cooldown, Mana, Skill XP i krytyki pozostają zgodne z istniejącym systemem; walka działa teraz w czasie rzeczywistym.",
        "Wpisz skills, skillnames albo porozmawiaj z nauczycielem klasy.",
    ],
    "naturalne_uzyj": [
        "Komenda użyj obsługuje naturalne intencje skilli.",
        "Przykłady: użyj heal, użyj tarcza, użyj unik, użyj drain, użyj dobij goblin.",
        "Ofensywne skróty: użyj ciecie goblin, użyj pocisk goblin, użyj ogien goblin, użyj burza goblin, użyj strzal goblin.",
        "Gra wybiera najwyżej odblokowany i nauczony skill pasujący do intencji.",
        "Jeśli dwa skille mają taki sam najlepszy wynik w multiclassie, gra nie wybierze losowo. Użyj pełnej nazwy.",
        "Pełne komendy skill, cast, użyj umiejętność oraz użyj czar nadal działają.",
    ],
    "prowadz_most": [
        "Komenda prowadz most prowadzi bezpośrednio do lokacji Kamienny Most.",
        "Działa też walk most, idz most, go most oraz prowadz kamienny most.",
        "Prowadzenie wykorzystuje ten sam bezpieczny system wyznaczania trasy co pozostałe cele.",
    ],
    "uzyj_skilla": [
        "Komenda użyj może uruchamiać nauczone umiejętności i czary.",
        "Przykład Wojownika: użyj ciecie goblin uruchamia Potężne Cięcie, jeśli skrót jest jednoznaczny i skill jest nauczony.",
        "Przykład Maga: użyj pocisk goblin może uruchomić Pocisk Arkanów.",
        "Przykład Czarownika: użyj plomien goblin może uruchomić Płomień Otchłani.",
        "Działa też użyj czar <nazwa> [cel], use spell <name> [target], skill <nazwa> [cel] i cast <nazwa> [cel].",
        "Jeżeli krótka nazwa pasuje do kilku aktywnych skilli, użyj pełnej nazwy.",
        "Cooldown, Mana, Skill Level i Skill XP pozostają bez zmian.",
    ],
    "kup_narzedzia": [
        "Narzędzia można kupować krótkimi nazwami bez polskich znaków.",
        "Przykłady: kup wedka, kup kilof, kup pila, kup mlot, kup noz, kup sierp, kup mozdzierz.",
        "Narzędzie nadal trzeba kupić u właściwego sprzedawcy. Gra poda właściwą lokację, jeśli jesteś w złym miejscu.",
        "Kupienie narzędzia nie daje mu XP ani levelu.",
    ],
    "xp_narzedzi": [
        "XP dostaje wyłącznie narzędzie faktycznie użyte w danej akcji.",
        "v1.13.42: Tool XP nie jest już płaski. Im wyższy poziom materiału, receptury, EQ do salvage albo innej pracy, tym większy realny XP narzędzia.",
        "Młot Rzemieślniczy ma dodatkowy mnożnik jakości x1.35; salvage, hartowanie, ulepszanie i kucie rozwijają Młot zależnie od poziomu wykonywanej pracy.",
        "Łowienie rozwija Wędkarstwo oraz Wędkę.",
        "Kopanie rozwija Górnictwo oraz Kilof.",
        "Drwalstwo i obróbka desek rozwijają Drwalstwo oraz Piłę.",
        "Kucie i przetapianie rozwijają Kowalstwo oraz Młot Rzemieślniczy.",
        "Gotowanie rozwija Gotowanie oraz Nóż Kucharski.",
        "Zielarstwo rozwija Zielarstwo oraz Sierp Zielarski.",
        "Alchemia rozwija Alchemię oraz Moździerz Alchemiczny.",
        "Jubilerstwo rozwija Jubilerstwo oraz Szczypce Jubilerskie.",
        "Pozostałe narzędzia nie dostają XP, użyć ani leveli od tej akcji.",
    ],
    "endgame_profesje": [
        "Narzędzia 1-400 odblokowują coraz lepsze surowce i zwiększają rare/quality oraz bonus urobku; profesje 1-400 skracają czas i blokują receptury/zlecenia.",
        "Wędka odblokowuje nowe ryby endgame; część zależy od typu łowiska: rzeka, jezioro, morze albo ocean.",
        "Kilof odblokowuje: Ruda Kobaltu 100, Kamień Runiczny 120, Smocza Stal 140, Ruda Astralna 160, Ruda Pustki 180 i Eternium 200.",
        "Piła w Głębi Gaju odblokowuje nowe drewna na levelach 100, 120, 140, 160, 180 i 200.",
        "Sierp w Głębi Gaju odblokowuje nowe zioła na levelach 100, 120, 140, 160, 180 i 200.",
        "Kowalstwo, Gotowanie, Alchemia i Jubilerstwo mają receptury progresji wymagające odpowiedniego levelu profesji oraz Tieru właściwego narzędzia.",
        "Receptury są twardo zablokowane jednocześnie levelem profesji i wymaganym Tierem narzędzia; sam składnik albo tylko jedna z tych osi nie wystarcza.",
        "Wpisz receptury, receptury craft, receptury cook albo receptury alchemia, aby usłyszeć wymagany level.",
    ],
    "logowanie": [
        "Po każdym zalogowaniu postać rozpoczyna sesję w Świątyni Odrodzenia.",
        "Nie ma znaczenia, gdzie postać wylogowała się poprzednio.",
        "Zapisana lokacja z poprzedniej sesji nie jest miejscem startowym następnego logowania.",
        "Po wejściu do świata HP i Mana są ustawiane jak dotychczas przy logowaniu.",
        "Portale Krypty, questy, ekwipunek i cała trwała progresja pozostają zapisane.",
    ],
    "soul_level_hp": [
        "Każdy awans Soul Level Broni Duszy natychmiast odnawia postać do 100 procent HP.",
        "Działa niezależnie od źródła Soul XP, między innymi z przeciwników oraz Eliksiru Duszy.",
        "Jeżeli Soul XP nie wbije nowego Soul Levelu, HP nie jest odnawiane.",
        "Odnowienie dotyczy tylko HP. Mana nie jest automatycznie odnawiana.",
        "Soul Level ma zakres 1-400.",
    ],
    "rozwoj_statystyk": [
        "Statystyki rosną automatycznie przez sześć niezależnych liczników EXP; nie ma ręcznego rozdawania punktów ani levelu postaci.",
        "Każda statystyka zaczyna od progu 100 EXP. Po przekroczeniu wartości bazowej 25 jej własny próg rośnie o 10 za każdy kolejny punkt tej statystyki.",
        "Pełny próg zwiększa tylko tę konkretną statystykę o 1; pozostałe zachowują własny EXP i własne progi.",
        "Pojedynczy mob ma limit EXP każdej statystyki zależny od rangi, więc boss nie przeskakuje całej progresji jednym zabiciem.",
        "Bonus rasy Człowiek do Postępu Rozwoju nadal działa.",
    ],
    "uzywanie_umiejetnosci": [
        "Umiejętności można używać dotychczasową komendą skill <nazwa lub numer> [cel].",
        "Działa też umiejętność <nazwa> [cel], zdolność <nazwa> [cel] oraz cast <nazwa> [cel].",
        "Dodano składnię użyj umiejętność <nazwa> [cel].",
        "Angielska wersja to use skill <name> [target].",
        "Jeżeli po use/użyj podasz bezpośrednio rozpoznawalną nazwę skilla, gra także spróbuje go użyć.",
        "Ofensywne umiejętności nadal rozpoczynają walkę tylko na wyraźną akcję gracza.",
        "Cooldown, Mana, Skill Level i zdobywanie Skill XP działają dokładnie tak jak przy komendzie skill.",
    ],
    "soul200": [
        "Broń Duszy ma Soul Level 1-400.",
        "Soul XP używa od v0.8.64 płynnej krzywej +25 procent mnożnika co pełny blok 10 leveli; wpisz help soulxp.",
        "Tier 4 wymaga próby od Soul Level 25.",
        "Tier 7 wymaga próby od Soul Level 60.",
        "Tier 13 odblokowuje się od Soul Level 120 po Próbie Elora na bossie piętra 120 Krypty.",
        "Tier 19 odblokowuje się od Soul Level 180 po Próbie Elora na bossie piętra 180 Krypty.",
        "Po Soul Level 100 Broń Duszy rozwija się dalej aż do 400.",
        "Soul Level nadal zwiększa bazową moc Broni Duszy.",
        "Nie ma levelu postaci.",
    ],
    "narzedzia200": [
        "Wszystkie 8 narzędzi ma level 1-400 i 40 Tierów.",
        "Wędka, Kilof, Piła, Młot Rzemieślniczy, Nóż Kucharski, Sierp Zielarski, Moździerz Alchemiczny i Szczypce Jubilerskie rozwijają się do 400.",
        "Tier 1 obejmuje level 1-9; kolejne Tiery zaczynają się na 10, 20, 30 i dalej co 10 aż do 180; Tier 20 jest na levelu 200.",
        "Przykłady bonusu: Tier 1 = 0 procent, Tier 10 od levelu 90 = 18 procent, Tier 11 od 100 = 20 procent, Tier 19 od 180 = 37 procent, Tier 20 na 200 = 40 procent.",
        "Każdy Tier ma osobną nazwę dla każdego rodzaju narzędzia.",
        "tools, tiers oraz bezpośrednie komendy narzędzi pokazują aktualny Tier i następny próg.",
    ],
    "krytyki": [
        "Trafienia krytyczne zależą od efektywnej Zręczności, czyli także od bonusów ekwipunku. Od v0.8.63 wysokie wartości mają malejący przyrost, a limit pozostaje 35 procent.",
        "Przy Zręczności 10 bazowa szansa na krytyk wynosi 5 procent.",
        "Każdy punkt Zręczności ponad 10 dodaje 0,5 punktu procentowego szansy.",
        "Zręczność poniżej 10 obniża szansę o 0,5 punktu procentowego za punkt.",
        "Minimalna szansa wynosi 1 procent, maksymalna 35 procent.",
        "Trafienie krytyczne zadaje 150 procent normalnych obrażeń.",
        "Krytyki działają dla zwykłego ataku i ofensywnych umiejętności klasowych.",
        "Mechaniki obronne bossów nadal mogą zredukować albo anulować krytyk.",
        "stats pokazuje aktualną szansę na krytyk i mnożnik.",
    ],
    "respawn": [
        "Zwykłe moby odradzają się po 120 sekundach od śmierci.",
        "Bossowie Krypty i Herszt Bandytów odradzają się po 300 sekundach.",
        "Żywy Manekin treningowy odradza się po 60 sekundach.",
        "Boss progu blokuje przejście tylko do pierwszego pokonania przez daną postać. Po respawnie jest opcjonalny.",
    ],
    "bossowie": [
        "Bossowie działają w walce czasu rzeczywistego i wykonują ataki według własnego timera.",
        "Bossowie i zwykłe moby nie są agresywne; nie zaczynają walki sami.",
        "Kościany Egzekutor: co trzeci kontratak używa Kościanego Miażdżenia.",
        "Krwawy Kurator: co trzeci kontratak używa Krwawego Drenażu i leczy się częścią zadanych obrażeń.",
        "Rycerz Grobowca: co trzecie trafienie gracza redukuje Tarczą Grobowca o połowę.",
        "Wiedźma Popiołu: co trzeci kontratak używa Klątwy Popiołu, która omija połowę obrony magicznej.",
        "Pan Katakumb: co czwarty kontratak używa Echa Katakumb.",
        "Widmowy Tytan: naprzemiennie zmienia kontratak fizyczny i magiczny.",
        "Nekromantyczny Kolos: co czwarty kontratak regeneruje 7 procent maksymalnego HP.",
        "Arcyupiór Otchłani: ma 25 procent szansy na eteryczny unik przeciw trafieniu gracza.",
        "Król Kości: poniżej 50 procent HP zadaje 50 procent więcej obrażeń.",
        "Władca Stu Pięter: poniżej połowy HP wchodzi w drugą fazę; co trzeci kontratak używa Załamania Duszy, a co czwarte trafienie gracza osłabia Pieczęcią Stu Pięter.",
        "Strażnik Pękniętej Duszy, piętro 110: co trzeci kontratak używa Rozdarcia Duszy.",
        "Królowa Otchłannej Krypty, piętro 120: co czwarty kontratak używa Drenażu Otchłani i jest celem Próby Tier 4.",
        "Tytan Żelaznych Kości, piętro 130: co trzecie trafienie gracza jest silnie redukowane.",
        "Prorok Czarnego Płomienia, piętro 140: co trzeci kontratak omija połowę obrony magicznej.",
        "Władca Bezdennych Katakumb, piętro 150: co czwarty kontratak używa Bezdennego Echa.",
        "Astralny Żniwiarz, piętro 160: zmienia fizyczną i magiczną fazę.",
        "Kolos Pustki, piętro 170: regeneruje 8 procent HP co czwarty własny atak.",
        "Cesarz Upiorów, piętro 180: ma Widmowy Unik i jest celem Próby Tier 5.",
        "Strażnik Końca, piętro 190: poniżej połowy HP zadaje 60 procent więcej obrażeń.",
        "Władca Dwustu Pięter, piętro 200: druga faza, Bariera Końca i Załamanie Wieczności; głębiej Krypta trwa dalej proceduralnie.",
        "Ręcznie przygotowani bossowie Krypty 10-200 mają własne relikty. Bossowie powyżej 200 są proceduralni i zamiast nowej nieskończenie silnej linii EQ korzystają z najwyższego istniejącego Tieru 20.",
        "Herszt Bandytów przebywa w Namiocie Herszta, głęboko w Obozowiskach Bandytów. Co trzeci kontratak wykonuje Brutalną Kombinację.",
        "Herszt Bandytów może upuścić unikalny Sygnet Herszta Bandytów.",
        "Król Goblinów przebywa w Grocie Króla Goblinów, na końcu Jaskiń Goblinów, i co trzeci kontratak wykonuje Królewską Szarżę.",
        "Alfa Wilków Cienia pojawia się w Głębi Gaju i poniżej połowy HP wpada w Szał Cienia.",
        "Strażnik Ruin pojawia się przy Zrujnowanej Wieży i co czwarty kontratak używa Runicznego Wybuchu.",
        "Kryształowy Władca pojawia się w Kryształowej Komnacie; używa Kryształowego Promienia i Kryształowej Bariery.",
        "Każdy z nowych bossów świata ma własny unikalny przedmiot z 45 procent szansy.",
    ],
    "loot_krypty": [
        "Ekwipunek z Krypty ma 5 rzadkości: Zwykły, Rzadki, Epicki, Legendarny i Mityczny.",
        "Wyższa rzadkość daje większą obronę i mocniejszy losowy affix.",
        "Losowe affixy to: Siła, Zręczność, Kondycja, Inteligencja, Siła Woli, HP albo Mana.",
        "Zwykłe moby częściej dają Zwykły lub Rzadki loot.",
        "Bossowie mają dużo lepszą szansę na Epicki, Legendarny i Mityczny loot.",
        "Każdy element Krypty należy do Zestawu Krypty swojego Tieru 1-40; moc EQ zatrzymuje się na progresji 400.",
        "Dominujący set to Tier, którego masz założonych najwięcej części; przy remisie wygrywa wyższy Tier.",
        "2 części jednego setu: +10 procent maksymalnego HP i Many.",
        "4 części jednego setu: dodatkowo +10 procent wszystkich zadawanych obrażeń.",
        "6 części jednego setu: dodatkowo +15 procent obrony fizycznej i magicznej.",
        "Komenda equipment pokazuje rarity, affix oraz aktywny bonus setu.",
        "Komenda stats pokazuje statystyki bazowe, statystyki z wyposażeniem oraz bonusy setu.",
        "Stare przedmioty Krypty pozostają działające i liczą się do odpowiedniego setu jako Zwykłe bez affixu.",
    ],
    "portale": [
        "Portal Krypty odblokowuje się po pokonaniu bossa co 10 pięter.",
        "Portale prowadzą co 10 pięter od 10 bez górnego limitu.",
        "Odblokowanie portalu zapisuje się trwale w SQLite.",
        "portal pokazuje wszystkie odblokowane cele.",
        "portal 30 przenosi z Sali Krypty lub Przedsionka Krypty bezpośrednio na piętro 30.",
        "Portal służy do szybkiego powrotu; pierwszy boss progu nadal wymaga pokonania, ale jego kolejne respawny są opcjonalne.",
        "Jeśli boss tego progu nigdy nie został jeszcze pokonany przez postać, żywy boss blokuje dalszą drogę.",
        "Po pierwszym zabiciu bossa przejście pozostaje odblokowane na stałe dla postaci, także po jego respawnie.",
        "Portalu nie można używać podczas walki.",
        "Stare komendy checkpoint nadal działają jako alias portalu dla zgodności.",
    ],
    "krypta": [
        "Loot Krypty ma rarity, losowe affixy statystyk i bonusy setowe 2/4/6 części.",
        "Wpisz help loot_krypty, help rarity albo help sety po szczegóły.",
        "Krypta nie ma końcowego piętra; od v0.11.0 każde piętro od 1 wzwyż powstaje dynamicznie dopiero przy wejściu.",
        "Każde główne piętro jest dużą mapą: od v0.80.0 ma 30 pomieszczeń, pętle, boczne komnaty i dużo więcej przeciwników.",
        "Moby nie są agresywne i nie rozpoczynają walki same.",
        "Bossowie są co 10 pięter od 10 bez końca.",
        "Boss co 10 pięter blokuje zejście tylko przy pierwszym przejściu danej postaci.",
        "Po pierwszym pokonaniu bossa próg jest zapisany jako zaliczony na stałe dla postaci.",
        "Po respawnie boss może być farmiony, ale nie blokuje już dalszej drogi ani checkpointu.",
        "Pokonanie bossa odblokowuje trwały Portal Krypty do jego piętra.",
        "portal pokazuje odblokowane cele; portal 50 przenosi na piętro 50.",
        "Portal nie zalicza niepokonanego progu; po pierwszym zwycięstwie żywy respawn bossa jest już opcjonalny.",
        "Zwykły mob Krypty daje 100 + piętro*10 Soul XP.",
        "Boss Krypty daje 600 + piętro*20 Soul XP.",
        "Zwykły mob zostawia 1 element ekwipunku na ciele, boss 3.",
        "prowadz krypta prowadzi tylko przed wejście do Krypty. Piętra eksplorujesz samodzielnie; schody na kolejne piętro trzeba odnaleźć w głębi mapy.",
        "Co 10 pięter rośnie próg trudności i nagród XP; Tier EQ rośnie tylko do Tieru 40 / progresji 400.",
    ],
    "multiclass": [
        "Multiclass jest całkowicie opcjonalny.",
        "Każda postać ma jedną klasę główną i może włączyć maksymalnie dwie dodatkowe klasy, czyli 3 aktywne łącznie.",
        "multiclass pokazuje aktywne klasy i ich Biegłość.",
        "multiclass add <klasa> włącza klasę dodatkową.",
        "multiclass remove <klasa> wyłącza klasę dodatkową. Klasy głównej nie można wyłączyć.",
        "Klasa główna zachowuje swoją Broń Duszy. Jej bonus klasowy także zawsze wzmacnia klasę główną; dodatkowe klasy nie dostają osobnej Broni Duszy.",
        "Dodatkowe klasy aktywują swoje pasywy i dają dostęp do własnych nauczycieli oraz skilli.",
        "Class XP z zabitego moba jest jedną pulą dzieloną równo między wszystkie aktywne klasy.",
        "Każda klasa ma własną Biegłość 1-400 i własny Class XP. To nie jest level postaci.",
        "Wyłączenie klasy nie kasuje jej Biegłości ani wcześniej nauczonych skilli, ale skilli nie można używać, gdy klasa jest nieaktywna.",
        "Jeśli włączysz klasę magiczną jako dodatkową, postać otrzymuje pulę Many i może używać jej magicznych skilli.",
    ],
    "opisy": [
        "Komenda opis bez argumentu opisuje aktualną lokację.",
        "opis <przedmiot> pokazuje działanie, typ i ceny.",
        "opis <NPC> pokazuje rolę, lokację i powiązane zadanie.",
        "NPC-e pomocni, handlowi, zadaniowi i nauczyciele są pokojowi oraz chronieni przed walką.",
        "opis <przeciwnik> pokazuje HP, obrażenia, typ ataku i nagrody.",
        "opis <lokacja> pokazuje strefę, opis, wyjścia i specjalne funkcje.",
        "opis <zadanie>, opis <rasa>, opis <klasa>, opis <statystyka> i opis <waluta> także działają.",
    ],
    "zmiany": [
        "changes, zmiany albo changelog pokazuje pełną historię wszystkich wersji.",
        "Najnowsza wersja jest na górze, starsze wersje są niżej.",
        "Historia jest czytana z CHANGELOG_PL.txt linia po linii dla NVDA.",
    ],
}

from data.quests import QUESTS


# v0.30.51: Godzinne Zlecenia — pełna stała oferta.
# Wszystkie zlecenia są zawsze dostępne do przyjęcia. Każde odnawia się
# niezależnie po 60 minutach od ukończenia/oddania, zaczyna od 0/x i liczy
# wyłącznie zdarzenia wykonane po przyjęciu.
HOURLY_QUEST_ROTATION_SIZE = 0
HOURLY_QUEST_IDS = (
    "hourly_goblins",
    "hourly_bandits",
    "hourly_shadow_wolves",
    "hourly_shadow_fangs",
    "hourly_skeletons",
    "hourly_temple_rats",
    "hourly_fishing",
    "hourly_mining",
    "hourly_woodcutting",
    "hourly_herbalism",
    "hourly_fish_variety",
    "hourly_ore_variety",
    "hourly_herb_variety",
    "hourly_class_wojownik",
    "hourly_class_berserker",
    "hourly_class_lotrzyk",
    "hourly_class_lowca",
    "hourly_class_mnich",
    "hourly_class_straznik",
    "hourly_class_mag",
    "hourly_class_nekromanta",
    "hourly_class_kaplan",
    "hourly_class_czarownik",
    "hourly_class_druid",
    "hourly_class_psionik",
    "hourly_class_mec",
    "hourly_class_inzynier",
)

_catalog_mut.catalog_update_path('QUESTS', QUESTS, (), {
    # v1.28.9: dwugodzinne zlecenia klasowe. Liczą dowolnego przeciwnika
    # pokonanego po przyjęciu i nagradzają reputacją właściwej klasy.
    "hourly_class_wojownik": {"name":"Dwugodzinne klasowe: Próba Wojownika","giver":"Mistrz Garran","required_npc_id":"teacher_warrior","kind":"kill","target":"*","needed":12,"description":"Pokonaj 12 dowolnych przeciwników jako Wojownik.","required_class":"Wojownik","reward_guild_class":"Wojownik","reward_guild_reputation":40,"reward_silver":1400,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_berserker": {"name":"Dwugodzinne klasowe: Próba Berserkera","giver":"Mistrzyni Brynja","required_npc_id":"teacher_berserker","kind":"kill","target":"*","needed":14,"description":"Pokonaj 14 dowolnych przeciwników jako Berserker.","required_class":"Berserker","reward_guild_class":"Berserker","reward_guild_reputation":45,"reward_silver":1500,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_lotrzyk": {"name":"Dwugodzinne klasowe: Próba Łotrzyka","giver":"Mistrz Kael","required_npc_id":"teacher_rogue","kind":"kill","target":"*","needed":12,"description":"Pokonaj 12 dowolnych przeciwników jako Łotrzyk.","required_class":"Łotrzyk","reward_guild_class":"Łotrzyk","reward_guild_reputation":40,"reward_silver":1400,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_lowca": {"name":"Dwugodzinne klasowe: Próba Łowcy","giver":"Mistrzyni Eira","required_npc_id":"teacher_hunter","kind":"kill","target":"*","needed":14,"description":"Pokonaj 14 dowolnych przeciwników jako Łowca.","required_class":"Łowca","reward_guild_class":"Łowca","reward_guild_reputation":45,"reward_silver":1500,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_mnich": {"name":"Dwugodzinne klasowe: Próba Mnicha","giver":"Mistrz Shen","required_npc_id":"teacher_monk","kind":"kill","target":"*","needed":12,"description":"Pokonaj 12 dowolnych przeciwników jako Mnich.","required_class":"Mnich","reward_guild_class":"Mnich","reward_guild_reputation":45,"reward_silver":1500,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_straznik": {"name":"Dwugodzinne klasowe: Próba Strażnika","giver":"Mistrz Borin","required_npc_id":"teacher_guardian","kind":"kill","target":"*","needed":10,"description":"Pokonaj 10 dowolnych przeciwników jako Strażnik.","required_class":"Strażnik","reward_guild_class":"Strażnik","reward_guild_reputation":50,"reward_silver":1600,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_mag": {"name":"Dwugodzinne klasowe: Próba Maga","giver":"Arcymag Vaelis","required_npc_id":"teacher_mage","kind":"kill","target":"*","needed":14,"description":"Pokonaj 14 dowolnych przeciwników jako Mag.","required_class":"Mag","reward_guild_class":"Mag","reward_guild_reputation":45,"reward_silver":1500,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_nekromanta": {"name":"Dwugodzinne klasowe: Próba Nekromanty","giver":"Mistrzyni Morwen","required_npc_id":"teacher_necromancer","kind":"kill","target":"*","needed":14,"description":"Pokonaj 14 dowolnych przeciwników jako Nekromanta.","required_class":"Nekromanta","reward_guild_class":"Nekromanta","reward_guild_reputation":45,"reward_silver":1500,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_kaplan": {"name":"Dwugodzinne klasowe: Próba Kapłana","giver":"Mistrz Aureon","required_npc_id":"teacher_priest","kind":"kill","target":"*","needed":10,"description":"Pokonaj 10 dowolnych przeciwników jako Kapłan.","required_class":"Kapłan","reward_guild_class":"Kapłan","reward_guild_reputation":50,"reward_silver":1600,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_czarownik": {"name":"Dwugodzinne klasowe: Próba Czarownika","giver":"Mistrzyni Nyra","required_npc_id":"teacher_warlock","kind":"kill","target":"*","needed":14,"description":"Pokonaj 14 dowolnych przeciwników jako Czarownik.","required_class":"Czarownik","reward_guild_class":"Czarownik","reward_guild_reputation":50,"reward_silver":1600,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_druid": {"name":"Dwugodzinne klasowe: Próba Druida","giver":"Mistrz Thalen","required_npc_id":"teacher_druid","kind":"kill","target":"*","needed":12,"description":"Pokonaj 12 dowolnych przeciwników jako Druid.","required_class":"Druid","reward_guild_class":"Druid","reward_guild_reputation":45,"reward_silver":1500,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_psionik": {"name":"Dwugodzinne klasowe: Próba Psionika","giver":"Mistrzyni Ilyra","required_npc_id":"teacher_psion","kind":"kill","target":"*","needed":14,"description":"Pokonaj 14 dowolnych przeciwników jako Psionik.","required_class":"Psionik","reward_guild_class":"Psionik","reward_guild_reputation":50,"reward_silver":1600,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_mec": {"name":"Dwugodzinne klasowe: Próba Meca","giver":"Mechanik Vektor","required_npc_id":"teacher_mec","kind":"kill","target":"*","needed":12,"description":"Pokonaj 12 dowolnych przeciwników jako Mec.","required_class":"Mec","reward_guild_class":"Mec","reward_guild_reputation":50,"reward_silver":1600,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_class_inzynier": {"name":"Dwugodzinne klasowe: Próba Inżyniera","giver":"Inżynierka Ada","required_npc_id":"teacher_engineer","kind":"kill","target":"*","needed":14,"description":"Pokonaj 14 dowolnych przeciwników jako Inżynier.","required_class":"Inżynier","reward_guild_class":"Inżynier","reward_guild_reputation":45,"reward_silver":1500,"reward_gold":0,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":2*60*60,"hourly_rotation":False,"remote_turnin":False},
    "hourly_goblins": {
        "name": "Godzinne zlecenie: Gobliny na szlaku", "giver": "Tablica Godzinnych Zleceń",
        "kind": "kill", "target": "goblin", "needed": 20,
        "description": "Pokonaj 20 goblinów. Liczą się wyłącznie zabójstwa po przyjęciu zadania.",
        "reward_silver": 900, "reward_gold": 0, "reward_mithril": 0, "reward_items": {"healing_potion": 1},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_bandits": {
        "name": "Godzinne zlecenie: Patrol przeciw bandytom", "giver": "Tablica Godzinnych Zleceń",
        "kind": "kill", "target": "bandit", "needed": 15,
        "description": "Pokonaj 15 bandytów po przyjęciu tego godzinnego zlecenia.",
        "reward_silver": 1000, "reward_gold": 0, "reward_mithril": 0, "reward_items": {"healing_potion": 1},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_shadow_wolves": {
        "name": "Godzinne zlecenie: Cienie w gaju", "giver": "Tablica Godzinnych Zleceń",
        "kind": "kill", "target": "shadow_wolf", "needed": 12,
        "description": "Pokonaj 12 Wilków Cienia po przyjęciu zlecenia.",
        "reward_silver": 1100, "reward_gold": 0, "reward_mithril": 0, "reward_items": {"healing_potion": 2},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_shadow_fangs": {
        "name": "Godzinne zlecenie: Kły Wilków Cienia", "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect", "target": "wolf_fang", "needed": 5,
        "description": "Zdobądź 5 Kłów Wilka Cienia po przyjęciu zlecenia. Stare zapasy nie nabijają postępu; przy oddaniu kły są zabierane.",
        "progress_label": "Kłów Wilka Cienia",
        "reward_silver": 950, "reward_gold": 0, "reward_mithril": 0, "reward_items": {"healing_potion": 1},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_skeletons": {
        "name": "Godzinne zlecenie: Kości krypty", "giver": "Tablica Godzinnych Zleceń",
        "kind": "kill", "target": "skeleton", "needed": 18,
        "description": "Pokonaj 18 szkieletów po przyjęciu zlecenia.",
        "reward_silver": 1200, "reward_gold": 0, "reward_mithril": 0, "reward_items": {"healing_potion": 2},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_temple_rats": {
        "name": "Godzinne zlecenie: Szczurza plaga", "giver": "Tablica Godzinnych Zleceń",
        "kind": "kill", "target": "temple_rat", "needed": 25,
        "description": "Pokonaj 25 szczurów świątynnych po przyjęciu zlecenia.",
        "reward_silver": 700, "reward_gold": 0, "reward_mithril": 0, "reward_items": {"healing_potion": 1},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_fishing": {
        "name": "Godzinne zlecenie: Połów", "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect_category", "target": "fish", "needed": 20,
        "description": "Złów 20 dowolnych ryb po przyjęciu zlecenia.",
        "reward_profession": "Wędkarstwo", "reward_profession_xp": 900, "reward_tool_type": "fishing", "reward_tool_xp": 750,
        "reward_silver": 800, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_mining": {
        "name": "Godzinne zlecenie: Górnicza zmiana", "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect_category", "target": "ore", "needed": 20,
        "description": "Wydobądź 20 dowolnych rud po przyjęciu zlecenia.",
        "reward_profession": "Górnictwo", "reward_profession_xp": 900, "reward_tool_type": "mining", "reward_tool_xp": 750,
        "reward_silver": 850, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_woodcutting": {
        "name": "Godzinne zlecenie: Drewno na zapasy", "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect_category", "target": "wood", "needed": 20,
        "description": "Zbierz 20 jednostek dowolnego drewna po przyjęciu zlecenia.",
        "reward_profession": "Drwalstwo", "reward_profession_xp": 900, "reward_tool_type": "woodcutting", "reward_tool_xp": 750,
        "reward_silver": 800, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_herbalism": {
        "name": "Godzinne zlecenie: Zielarski zbiór", "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect_category", "target": "herb", "needed": 20,
        "description": "Zbierz 20 dowolnych ziół po przyjęciu zlecenia.",
        "reward_profession": "Zielarstwo", "reward_profession_xp": 900, "reward_tool_type": "herbalism", "reward_tool_xp": 750,
        "reward_silver": 800, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_fish_variety": {
        "name": "Godzinne zlecenie: Różnorodny połów", "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect_category", "target": "fish", "needed": 30,
        "description": "Złów 30 ryb po przyjęciu zlecenia. Starsze gatunki nadal się liczą.",
        "reward_profession": "Wędkarstwo", "reward_profession_xp": 1200, "reward_tool_type": "fishing", "reward_tool_xp": 950,
        "reward_silver": 1000, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_ore_variety": {
        "name": "Godzinne zlecenie: Zapasy rudy", "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect_category", "target": "ore", "needed": 30,
        "description": "Wydobądź 30 rud po przyjęciu zlecenia. Liczą się wszystkie odpowiednie tiery.",
        "reward_profession": "Górnictwo", "reward_profession_xp": 1200, "reward_tool_type": "mining", "reward_tool_xp": 950,
        "reward_silver": 1050, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_herb_variety": {
        "name": "Godzinne zlecenie: Zapas ziół", "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect_category", "target": "herb", "needed": 30,
        "description": "Zbierz 30 ziół po przyjęciu zlecenia. Liczą się wcześniejsze i późniejsze tiery.",
        "reward_profession": "Zielarstwo", "reward_profession_xp": 1200, "reward_tool_type": "herbalism", "reward_tool_xp": 950,
        "reward_silver": 1000, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
        "repeatable": True, "repeat_cooldown": 60 * 60, "hourly_rotation": False, "remote_turnin": True,
    },
})

# v0.8.43: jednorazowe questy startowe Archiwisty Sola.
# Nie mają cooldownu i po ukończeniu nigdy się nie odnawiają.
_catalog_mut.catalog_update_path('QUESTS', QUESTS, (), {
    "sol_starter_blacksmith_delivery": {
        "name": "Pierwsze kroki: Paczka dla Kowala",
        "giver": "Archiwista Sol",
        "kind": "deliver_npc",
        "target_npc": "doran",
        "quest_item": "sol_smith_package",
        "accept_items": {"sol_smith_package": 1},
        "needed": 1,
        "description": (
            "Archiwista Sol prosi, abyś zaniósł zapieczętowaną paczkę "
            "Kowalowi Doranowi w Kuźni. Porozmawiaj z Doranem, aby ją przekazać."
        ),
        "reward_stat_progress": 30,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 1},
        "repeatable": False,
        "starter_quest": True,
    },
    "sol_starter_inn_delivery": {
        "name": "Pierwsze kroki: Wiadomość do Karczmy",
        "giver": "Archiwista Sol",
        "kind": "deliver_npc",
        "target_npc": "innkeeper",
        "quest_item": "sol_inn_letter",
        "accept_items": {"sol_inn_letter": 1},
        "needed": 1,
        "description": (
            "Zanieś list Archiwisty Sola Karczmarce Elii w Karczmie Błękitny Płomień. "
            "Porozmawiaj z Elią, aby oddać wiadomość."
        ),
        "reward_stat_progress": 35,
        "reward_silver": 60, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"mana_potion": 1},
        "repeatable": False,
        "starter_quest": True,
    },
    "sol_starter_guard_delivery": {
        "name": "Pierwsze kroki: Meldunek dla Straży",
        "giver": "Archiwista Sol",
        "kind": "deliver_npc",
        "target_npc": "watch_commander_roderik",
        "quest_item": "sol_guard_report",
        "accept_items": {"sol_guard_report": 1},
        "needed": 1,
        "description": (
            "Dostarcz meldunek Archiwisty Sola Dowódcy Roderikowi w Wartowni Północnej. "
            "Porozmawiaj z Roderikiem, aby przekazać dokument."
        ),
        "reward_stat_progress": 45,
        "reward_silver": 90, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 1},
        "repeatable": False,
        "starter_quest": True,
    },
    "sol_starter_herbalist_delivery": {
        "name": "Pierwsze kroki: Notatki dla Zielarki",
        "giver": "Archiwista Sol",
        "kind": "deliver_npc",
        "target_npc": "mira",
        "quest_item": "sol_herbal_notes",
        "accept_items": {"sol_herbal_notes": 1},
        "needed": 1,
        "description": (
            "Zanieś notatki Archiwisty Sola Zielarce Mirze w Gaju Szeptów. "
            "Porozmawiaj z Mirą, aby przekazać notatki."
        ),
        "reward_stat_progress": 55,
        "reward_silver": 110, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 2},
        "repeatable": False,
        "starter_quest": True,
    },
    "sol_starter_class_teacher": {
        "name": "Pierwsze kroki: Poznaj swojego nauczyciela",
        "giver": "Archiwista Sol",
        "kind": "talk_class_teacher",
        "needed": 1,
        "description": (
            "Odszukaj nauczyciela swojej podstawowej klasy i porozmawiaj z nim. "
            "Zadanie zaliczy się przy rozmowie z właściwym nauczycielem."
        ),
        "reward_stat_progress": 70,
        "reward_silver": 150, "reward_gold": 1, "reward_mithril": 0,
        "reward_items": {"healing_potion": 1, "mana_potion": 1},
        "repeatable": False,
        "starter_quest": True,
    },
})


# v0.8.53 — brakujące jednorazowe Próby Broni Duszy.
# Cztery historyczne Próby (Tiery 4, 7, 13 i 19) są zdefiniowane
# wyżej i zachowują stare quest_id dla pełnej zgodności save'ów.
_catalog_mut.catalog_update_path('QUESTS', QUESTS, (), {
    "soul_tier_02_trial": {
        "name": "Próba Broni Duszy: Tier 2",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_10", "needed": 1,
        "description": (
            "Pokonaj Kościanego Egzekutora na piętrze 10 Krypty, a następnie "
            "wróć do Kapłana Elora w Świątyni Odrodzenia."
        ),
        "required_soul_level": 10, "required_soul_tier": 1,
        "unlocks_soul_tier": 2,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_03_trial": {
        "name": "Próba Broni Duszy: Tier 3",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_20", "needed": 1,
        "description": (
            "Pokonaj Krwawego Kuratora na piętrze 20 Krypty, a następnie "
            "wróć do Kapłana Elora."
        ),
        "required_soul_level": 20, "required_soul_tier": 2,
        "unlocks_soul_tier": 3,
        "reward_silver": 75, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_05_trial": {
        "name": "Próba Broni Duszy: Tier 5",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_floor_mob_35", "needed": 4,
        "description": (
            "Pokonaj 4 Strażników Sarkofagu na piętrze 35 Krypty i wróć do Kapłana Elora."
        ),
        "required_soul_level": 35, "required_soul_tier": 4,
        "unlocks_soul_tier": 5,
        "reward_silver": 150, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_06_trial": {
        "name": "Próba Broni Duszy: Tier 6",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_floor_mob_45", "needed": 4,
        "description": (
            "Pokonaj 4 Zjawiska Pustki na piętrze 45 Krypty i wróć do Kapłana Elora."
        ),
        "required_soul_level": 45, "required_soul_tier": 5,
        "unlocks_soul_tier": 6,
        "reward_silver": 200, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_08_trial": {
        "name": "Próba Broni Duszy: Tier 8",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "cemetery_bell_wraith", "needed": 5,
        "description": "Pokonaj 5 Upiorów Dzwonu na Starym Cmentarzu i wróć do Kapłana Elora.",
        "required_soul_level": 70, "required_soul_tier": 7,
        "unlocks_soul_tier": 8,
        "reward_silver": 300, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_09_trial": {
        "name": "Próba Broni Duszy: Tier 9",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_80", "needed": 1,
        "description": "Pokonaj Arcyupiora Otchłani na piętrze 80 Krypty i wróć do Kapłana Elora.",
        "required_soul_level": 80, "required_soul_tier": 8,
        "unlocks_soul_tier": 9,
        "reward_silver": 350, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_10_trial": {
        "name": "Próba Broni Duszy: Tier 10",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_90", "needed": 1,
        "description": "Pokonaj Króla Kości na piętrze 90 Krypty i wróć do Kapłana Elora.",
        "required_soul_level": 90, "required_soul_tier": 9,
        "unlocks_soul_tier": 10,
        "reward_silver": 400, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_11_trial": {
        "name": "Próba Broni Duszy: Tier 11",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_100", "needed": 1,
        "description": "Pokonaj Władcę Stu Pięter na piętrze 100 Krypty i wróć do Kapłana Elora.",
        "required_soul_level": 100, "required_soul_tier": 10,
        "unlocks_soul_tier": 11,
        "reward_silver": 500, "reward_gold": 1, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_12_trial": {
        "name": "Próba Broni Duszy: Tier 12",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_110", "needed": 1,
        "description": "Pokonaj Strażnika Pękniętej Duszy na piętrze 110 Krypty i wróć do Kapłana Elora.",
        "required_soul_level": 110, "required_soul_tier": 11,
        "unlocks_soul_tier": 12,
        "reward_silver": 550, "reward_gold": 1, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_14_trial": {
        "name": "Próba Broni Duszy: Tier 14",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_130", "needed": 1,
        "description": "Pokonaj Tytana Żelaznych Kości na piętrze 130 Krypty i wróć do Kapłana Elora.",
        "required_soul_level": 130, "required_soul_tier": 13,
        "unlocks_soul_tier": 14,
        "reward_silver": 700, "reward_gold": 2, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_15_trial": {
        "name": "Próba Broni Duszy: Tier 15",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_140", "needed": 1,
        "description": "Pokonaj Proroka Czarnego Płomienia na piętrze 140 Krypty i wróć do Kapłana Elora.",
        "required_soul_level": 140, "required_soul_tier": 14,
        "unlocks_soul_tier": 15,
        "reward_silver": 800, "reward_gold": 2, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_16_trial": {
        "name": "Próba Broni Duszy: Tier 16",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_150", "needed": 1,
        "description": "Pokonaj Władcę Bezdennych Katakumb na piętrze 150 Krypty i wróć do Kapłana Elora.",
        "required_soul_level": 150, "required_soul_tier": 15,
        "unlocks_soul_tier": 16,
        "reward_silver": 900, "reward_gold": 3, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_17_trial": {
        "name": "Próba Broni Duszy: Tier 17",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_160", "needed": 1,
        "description": "Pokonaj Astralnego Żniwiarza na piętrze 160 Krypty i wróć do Kapłana Elora.",
        "required_soul_level": 160, "required_soul_tier": 16,
        "unlocks_soul_tier": 17,
        "reward_silver": 1000, "reward_gold": 3, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_18_trial": {
        "name": "Próba Broni Duszy: Tier 18",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_170", "needed": 1,
        "description": "Pokonaj Kolosa Pustki na piętrze 170 Krypty i wróć do Kapłana Elora.",
        "required_soul_level": 170, "required_soul_tier": 17,
        "unlocks_soul_tier": 18,
        "reward_silver": 1100, "reward_gold": 4, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_20_trial": {
        "name": "Próba Broni Duszy: Tier 20",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_boss_200", "needed": 1,
        "description": (
            "Pokonaj Władcę Dwustu Pięter na kamieniu milowym piętra 200 Krypty i wróć do Kapłana Elora. "
            "To ostatnia Próba Broni Duszy."
        ),
        "required_soul_level": 200, "required_soul_tier": 19,
        "unlocks_soul_tier": 20,
        "reward_silver": 2000, "reward_gold": 10, "reward_mithril": 1,
        "reward_items": {},
    },
})

from data.mobs import MOB_TEMPLATES

# v0.9.10: fauna otwartego świata. Miasta, Gildia Dusz i Wioska Górska
# pozostają bez wrogich spawnów; Plac Treningowy zachowuje tylko manekina.
_catalog_mut.catalog_update_path('MOB_TEMPLATES', MOB_TEMPLATES, (), {
    "meadow_field_wolf": {
        "name": "Wilk Łąkowy", "max_hp": 48, "damage": 5, "damage_type": "physical",
        "silver": 16, "gold": 0, "mithril": 0, "stat_reward": 20, "soul_reward": 105,
        "drops": {"wolf_fang": 0.20}, "quest_target": None,
    },
    "meadow_wild_boar": {
        "name": "Dziki Knur Łąkowy", "max_hp": 62, "damage": 6, "damage_type": "physical",
        "silver": 22, "gold": 0, "mithril": 0, "stat_reward": 24, "soul_reward": 120,
        "drops": {}, "quest_target": None,
    },
    "meadow_giant_wasp": {
        "name": "Wielka Osa Łąkowa", "max_hp": 40, "damage": 5, "damage_type": "physical",
        "silver": 14, "gold": 0, "mithril": 0, "stat_reward": 18, "soul_reward": 95,
        "drops": {}, "quest_target": None,
    },
    "coast_rock_crab": {
        "name": "Krab Skalny", "max_hp": 88, "damage": 9, "damage_type": "physical",
        "silver": 34, "gold": 0, "mithril": 0, "stat_reward": 34, "soul_reward": 165,
        "drops": {}, "quest_target": None,
    },
    "coast_sea_raider": {
        "name": "Morski Rozbójnik", "max_hp": 105, "damage": 11, "damage_type": "physical",
        "silver": 52, "gold": 0, "mithril": 0, "stat_reward": 42, "soul_reward": 205,
        "drops": {"healing_potion": 0.08}, "quest_target": "bandit",
    },
})

# room_id, template_id
MOB_SPAWNS = [
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("temple_basement_storage", "temple_rat"),
    ("temple_basement_storage", "temple_rat"),
    ("temple_basement_storage", "temple_rat"),
    ("temple_basement_storage", "temple_rat"),
    ("temple_basement_storage", "temple_rat"),
    ("temple_basement_pantry", "temple_rat"),
    ("temple_basement_pantry", "temple_rat"),
    ("temple_basement_pantry", "temple_rat"),
    ("temple_basement_pantry", "temple_rat"),
    ("temple_basement_pantry", "temple_rat"),
    ("temple_basement_wine", "temple_rat"),
    ("temple_basement_wine", "temple_rat"),
    ("temple_basement_wine", "temple_rat"),
    ("temple_basement_wine", "temple_rat"),
    ("temple_basement_wine", "temple_rat"),
    ("temple_basement_drain", "temple_rat"),
    ("temple_basement_drain", "temple_rat"),
    ("temple_basement_drain", "temple_rat"),
    ("temple_basement_drain", "temple_rat"),
    ("temple_basement_drain", "temple_rat"),
    ("temple_basement_moldy", "temple_rat"),
    ("temple_basement_moldy", "temple_rat"),
    ("temple_basement_moldy", "temple_rat"),
    ("temple_basement_moldy", "temple_rat"),
    ("temple_basement_moldy", "temple_rat"),
    ("temple_basement_cistern", "temple_rat"),
    ("temple_basement_cistern", "temple_rat"),
    ("temple_basement_cistern", "temple_rat"),
    ("temple_basement_cistern", "temple_rat"),
    ("temple_basement_cistern", "temple_rat"),
    ("temple_basement_flooded", "temple_rat"),
    ("temple_basement_flooded", "temple_rat"),
    ("temple_basement_flooded", "temple_rat"),
    ("temple_basement_flooded", "temple_rat"),
    ("temple_basement_flooded", "temple_rat"),
    ("temple_basement_root", "temple_rat"),
    ("temple_basement_root", "temple_rat"),
    ("temple_basement_root", "temple_rat"),
    ("temple_basement_root", "temple_rat"),
    ("temple_basement_root", "temple_rat"),
    ("temple_basement_hidden", "temple_rat"),
    ("temple_basement_hidden", "temple_rat"),
    ("temple_basement_hidden", "temple_rat"),
    ("temple_basement_hidden", "temple_rat"),
    ("temple_basement_hidden", "temple_rat"),
    ("temple_basement_nest_a", "temple_rat"),
    ("temple_basement_nest_a", "temple_rat"),
    ("temple_basement_nest_a", "temple_rat"),
    ("temple_basement_nest_a", "temple_rat"),
    ("temple_basement_nest_a", "temple_rat"),
    ("temple_basement_collapsed", "temple_rat"),
    ("temple_basement_collapsed", "temple_rat"),
    ("temple_basement_collapsed", "temple_rat"),
    ("temple_basement_collapsed", "temple_rat"),
    ("temple_basement_collapsed", "temple_rat"),
    ("temple_basement_boiler", "temple_rat"),
    ("temple_basement_boiler", "temple_rat"),
    ("temple_basement_boiler", "temple_rat"),
    ("temple_basement_boiler", "temple_rat"),
    ("temple_basement_boiler", "temple_rat"),
    ("temple_basement_sewer_grate", "temple_rat"),
    ("temple_basement_sewer_grate", "temple_rat"),
    ("temple_basement_sewer_grate", "temple_rat"),
    ("temple_basement_sewer_grate", "temple_rat"),
    ("temple_basement_sewer_grate", "temple_rat"),
    ("temple_basement_bone_pit", "temple_rat"),
    ("temple_basement_bone_pit", "temple_rat"),
    ("temple_basement_bone_pit", "temple_rat"),
    ("temple_basement_bone_pit", "temple_rat"),
    ("temple_basement_bone_pit", "temple_rat"),
    ("temple_basement_lower_vault", "temple_rat"),
    ("temple_basement_lower_vault", "temple_rat"),
    ("temple_basement_lower_vault", "temple_rat"),
    ("temple_basement_lower_vault", "temple_rat"),
    ("temple_basement_lower_vault", "temple_rat"),
    ("temple_basement_chapel", "temple_rat"),
    ("temple_basement_chapel", "temple_rat"),
    ("temple_basement_chapel", "temple_rat"),
    ("temple_basement_chapel", "temple_rat"),
    ("temple_basement_chapel", "temple_rat"),
    ("temple_basement_nest_b", "temple_rat"),
    ("temple_basement_nest_b", "temple_rat"),
    ("temple_basement_nest_b", "temple_rat"),
    ("temple_basement_nest_b", "temple_rat"),
    ("temple_basement_nest_b", "temple_rat"),
    ("temple_basement_nest_c", "temple_rat"),
    ("temple_basement_nest_c", "temple_rat"),
    ("temple_basement_nest_c", "temple_rat"),
    ("temple_basement_nest_c", "temple_rat"),
    ("temple_basement_nest_c", "temple_rat"),
    ("temple_basement_deep_nest", "temple_rat"),
    ("temple_basement_deep_nest", "temple_rat"),
    ("temple_basement_deep_nest", "temple_rat"),
    ("temple_basement_deep_nest", "temple_rat"),
    ("temple_basement_deep_nest", "temple_rat"),
    ("training", "training_dummy"),
    ("old_road", "bandit"),
    ("bandit_camp", "bandit"),
    ("bandit_camp", "bandit_scout"),
    ("bandit_outer_ring", "bandit_scout"),
    ("bandit_outer_ring", "bandit_crossbowman"),
    ("bandit_outer_ring", "bandit"),
    ("bandit_supply_tents", "bandit"),
    ("bandit_supply_tents", "bandit_cutthroat"),
    ("bandit_supply_tents", "bandit_marauder"),
    ("bandit_training_yard", "bandit_marauder"),
    ("bandit_training_yard", "bandit_raider"),
    ("bandit_training_yard", "bandit_cutthroat"),
    ("bandit_barricade", "bandit_crossbowman"),
    ("bandit_barricade", "bandit_enforcer"),
    ("bandit_loot_depot", "bandit_raider"),
    ("bandit_loot_depot", "bandit_alchemist"),
    ("bandit_arena", "bandit_enforcer"),
    ("bandit_arena", "bandit_veteran"),
    ("bandit_arena", "bandit_captain"),
    ("bandit_inner_camp", "bandit_veteran"),
    ("bandit_inner_camp", "bandit_enforcer"),
    ("bandit_inner_camp", "bandit_alchemist"),
    ("bandit_command_tent", "bandit_veteran"),
    ("bandit_command_tent", "bandit_chief"),
    ("goblin_camp", "goblin"),
    ("goblin_camp", "goblin_scout"),
    ("goblin_cave_mouth", "goblin_scout"),
    ("goblin_cave_mouth", "goblin_spearman"),
    ("goblin_fungus_gallery", "goblin"),
    ("goblin_fungus_gallery", "goblin_archer"),
    ("goblin_fungus_gallery", "goblin_spearman"),
    ("goblin_scrap_tunnels", "goblin_archer"),
    ("goblin_scrap_tunnels", "goblin_cave_guard"),
    ("goblin_shaman_hollow", "goblin_shaman"),
    ("goblin_shaman_hollow", "goblin_shaman"),
    ("goblin_bomb_workshop", "goblin_bomber"),
    ("goblin_bomb_workshop", "goblin_bomber"),
    ("goblin_guard_post", "goblin_cave_guard"),
    ("goblin_guard_post", "goblin_warrior"),
    ("goblin_war_den", "goblin_warrior"),
    ("goblin_war_den", "goblin_cave_guard"),
    ("goblin_war_den", "goblin_warchief"),
    ("goblin_treasure_burrow", "goblin_warrior"),
    ("goblin_treasure_burrow", "goblin_shaman"),
    ("goblin_throne_cave", "goblin_warrior"),
    ("goblin_throne_cave", "goblin_king"),
    ("deep_grove", "shadow_alpha"),
    ("ruin_command_chamber", "ruin_warden"),
    ("crystal_chamber", "crystal_lord"),
    ("deep_grove", "shadow_wolf"),
    ("whisper_grove", "shadow_wolf"),
    ("ruined_watchtower", "goblin"),
    ("ruined_watchtower", "ruin_goblin_looter"),
    ("ruin_gatehouse", "ruin_watchman"),
    ("ruin_gatehouse", "ruin_spearman"),
    ("ruin_courtyard", "ruin_watchman"),
    ("ruin_courtyard", "ruin_goblin_looter"),
    ("ruin_courtyard", "ruin_shieldbearer"),
    ("ruin_barracks", "ruin_watchman"),
    ("ruin_barracks", "ruin_spearman"),
    ("ruin_barracks", "ruin_shieldbearer"),
    ("ruin_armory", "ruin_shieldbearer"),
    ("ruin_armory", "ruin_runekeeper"),
    ("ruin_wall_walk", "ruin_crossbowman"),
    ("ruin_wall_walk", "ruin_crossbowman"),
    ("ruin_wall_walk", "ruin_gargoyle"),
    ("ruin_archive", "ruin_runekeeper"),
    ("ruin_archive", "ruin_wraith"),
    ("ruin_cellar", "ruin_goblin_looter"),
    ("ruin_cellar", "ruin_watchman"),
    ("ruin_undercroft", "ruin_wraith"),
    ("ruin_undercroft", "ruin_gargoyle"),
    ("ruin_sealed_hall", "ruin_shieldbearer"),
    ("ruin_sealed_hall", "ruin_runekeeper"),
    ("ruin_sealed_hall", "ruin_captain"),
    ("ruin_command_chamber", "ruin_wraith"),
    ("ruin_command_chamber", "ruin_gargoyle"),
    ("goblin_camp", "goblin_brute"),
    ("goblin_fungus_gallery", "goblin_brute"),
    ("crypt_hall", "skeleton"),
    ("crypt_depths", "crypt_wraith"),
    ("crystal_chamber", "crystal_guardian"),
]

# v0.9.10: dodatkowe spawny na otwartym świecie. Celowo pomijamy Miasto Dusz,
# Gildię Dusz, Wioskę Górską oraz bezpieczne chaty/posterunki/obozy NPC.
WORLD_SURFACE_EXTRA_SPAWNS = [
    # Łąki
    ("meadow", "meadow_field_wolf"),
    ("flower_meadow", "meadow_giant_wasp"),
    ("lakeside_meadow", "meadow_wild_boar"),
    # Łąki Zielarskie
    ("mint_meadow", "meadow_giant_wasp"),
    ("herb_meadow_hub", "meadow_field_wolf"),
    ("chamomile_meadow", "meadow_giant_wasp"),
    ("nettle_meadow", "meadow_wild_boar"),
    ("lemon_balm_meadow", "meadow_giant_wasp"),
    ("lavender_meadow", "meadow_field_wolf"),
    ("sage_meadow", "meadow_wild_boar"),
    ("valerian_meadow", "meadow_field_wolf"),
    ("yarrow_meadow", "meadow_giant_wasp"),
    ("ginseng_meadow", "meadow_wild_boar"),
    ("moonflower_meadow", "meadow_field_wolf"),
    # Góry
    ("mountain_pass", "mountain_stone_ram"),
    ("dwarf_mine_entrance", "mountain_ice_wolf"),
    ("summit_camp", "mountain_harpy"),
    # Dzicz - naturalne szlaki, bez chat i posterunków NPC
    ("lake_shore", "shadow_wolf"),
    ("hill", "goblin_scout"),
    ("shrine", "shadow_wolf"),
    ("riverbank", "bandit"),
    ("stone_bridge", "bandit_scout"),
    ("crossroads", "bandit"),
    ("hunter_clearing", "shadow_wolf"),
    # Bagna i pustynia
    ("swamp_boardwalk", "swamp_crawler"),
    ("dry_canyon", "desert_raider"),
    # Wybrzeże
    ("sea_pier", "coast_rock_crab"),
    ("ocean_platform", "coast_sea_raider"),
]
MOB_SPAWNS.extend(WORLD_SURFACE_EXTRA_SPAWNS)

# v1.11.36 — unique UOSSMUD Super Boss arenas are authored by the world layer,
# while their canonical spawns are installed here after MOB_SPAWNS exists.
# Player-facing help. Category/group page labels are explicitly documented as
# not being boss names so the mistake cannot silently return later.
HELP_TOPICS["superbossy"] = [
    "Superbossy UOSSMUD są unikalnymi wyzwaniami świata, a nie rotacją bossów Mitycznej Krypty/Wierzy.",
    "Dostępne są wyzwania solo, solo/party i party. Minimalny próg nie oznacza zalecanego poziomu.",
    "Black Rabite: każdy uczestnik dostaje własny losowy drop z 10 przedmiotów + Moogle Steel; przy maks. 3 graczach można za 1 mithril zatrudnić Primm albo Popoi.",
    "Deep Dungeon UOSS: loch nie ma limitu pięter. Apanda blokuje zejście co 25 pięter; progres jest osobisty, a deepelevator wraca do wcześniej odwiedzonych pięter.",
    "Serpentarius: każdy uczestnik musi osobiście dotrzeć co najmniej do Deep Dungeon piętro 100. To odblokowuje Floor 0; po zabiciu Serpentariusa ponowne wejście do Floor 0/starcia jest zablokowane przez 24 godziny. Sam Deep Dungeon pozostaje dostępny i można schodzić dalej bez limitu.",
    "Portale Krypty i Astralne w drużynie uruchamia lider. Razem przenoszeni są tylko członkowie stojący obok, którzy mają wybrany checkpoint odblokowany u siebie.",
    "Każdy uczestnik Serpentariusa dostaje Serpentarius Emblem; przy maks. 3 graczach pomaga Byblos.",
    "Odin: Level 100+, drużyna 3-5; 8 unikalnych dropów + Odin's Mantle dla każdego uczestnika; przy 4-5 graczach trudność rośnie.",
    "Yiazmat: 7 unikalnych dropów + Godslayer's Badge dla każdego uczestnika; przy maks. 3 graczach pomaga Montblanc.",
    "24-godzinny lockout dotyczy Black Rabite, Serpentariusa, Odina i Yiazmata. Restart ani deploy Railway nie resetuje czasu.",
]
HELP_TOPIC_ALIASES.update({
    "superboss": "superbossy", "superbosses": "superbossy", "uossbosses": "superbossy",
    "uoss boss": "superbossy", "uoss bosses": "superbossy",
    "deep dungeon": "superbossy", "deepdungeon": "superbossy",
})
HELP_TOPICS.setdefault("wersja", []).append(
    "v1.11.34: Superbossy UOSSMUD są unikalnymi wyzwaniami świata; dodano pełny katalog trybów oraz reguły Black Rabite, Serpentariusa i Yiazmata."
)


from world.uoss_superboss_world import install_uoss_superboss_spawns_v11136
install_uoss_superboss_spawns_v11136(MOB_SPAWNS)


# v0.9.12: 200 oznacza wyłącznie zakres ręcznie przygotowanej zawartości.
# Sama Krypta nie ma maksymalnego piętra; kolejne pokoje powstają na żądanie.
CRYPT_PREGENERATED_MAX_FLOOR = 200
CRYPT_MAX_FLOOR = CRYPT_PREGENERATED_MAX_FLOOR  # legacy compatibility only
CRYPT_BOSS_FLOORS = tuple(range(10, CRYPT_PREGENERATED_MAX_FLOOR + 1, 10))
INFINITE_CRYPT_STEP_RATE = 0.025


# v0.31.9 HELP refresh
HELP_TOPICS["mec"] = [
 "Mec: pełny zestaw Melee, Ranged, Feedback, Magic, Support, Counter, Inherent i Passive. Progi umiejętności zależą od Biegłości Meca.",
 "V-MAX wymaga Biegłości 130. Will wydłuża czas działania. Aktywuje Protect, Shell, Haste, Regen, Preach, Praise i Permanence oraz zmienia wybrane umiejętności.",
 "Cosmic Rave: Biegłość 110; normalnie trafia wszystkich, w V-MAX wykonuje 5 losowych trafień. Shoot-All i Starlight Shower także zyskują efekty V-MAX.",
 "Self-Repair, Combat Mastery, Maxwell Program, Shooting Mastery oraz cztery Protocols działają pasywnie po nauczeniu.",
]
HELP_TOPICS["engineer upgrade"] = [
 "Engineer Upgrade 2.0: Upgrade <narzędzie> zapisuje ulepszenie. Scanner nie podlega Upgrade.",
 "Bazowo masz 1 slot Upgrade; Silver Gear daje drugi, Gold Battery trzeci.",
 "Upgrade bez argumentu pokazuje aktywne sloty oraz dokładny efekt każdego ulepszonego narzędzia.",
 "Przykłady: Launcher 4->6 pocisków, Debilitator 1->3 podatności, Drill wzmacnia przebicie/dispel, Chainsaw Demi->Quarter, Napalm nakłada olej.",
]
HELP_TOPIC_ALIASES.update({"mec skills":"mec","mec umiejętności":"mec","engineer upgrade":"engineer upgrade","upgrade 2":"engineer upgrade"})


# v0.31.12 Tech Crafting / Runes & Sockets 2.0
HELP_TOPICS["techcraft"] = [
    "Machine Salvage 2.0: komponenty Machine trafiają do Szkatułki -> Technologia.",
    "techsalvage <komponent> rozkłada cięższe części na Servo, Circuit, Power Cell i Plating.",
    "techcraft pokazuje receptury technologiczne; techcraft <nazwa> wykonuje Boardy Cyborga, komponenty Meca, zestawy Upgrade Inżyniera i technologiczne EQ.",
    "Upgrade Inżyniera wymaga teraz 1 Zestawu Upgrade Inżyniera na trwałe ulepszenie narzędzia.",
]
HELP_TOPICS["sockety2"] = [
    "Runy i sockety 2.0 rozwijają istniejące systemy bez kasowania starych run i klejnotów.",
    "Oszlifowane klejnoty mogą trafiać także do wysokopoziomowego lub technologicznego EQ z gniazdami, nie tylko do biżuterii.",
    "gemsockets pokazuje jednocześnie zajęcie gniazd klejnotów i run na założonym EQ.",
    "Stare runy endgame pozostają; dodano Runę Impulsu, Runę Bariery Magitek i Runę Rdzenia.",
]
HELP_TOPICS["vmax2"] = [
    "vmaxstatus / vmaxinfo pokazuje stan V-MAX, pozostały czas, Overheat i efekty zależne od V-MAX.",
    "Will wydłuża V-MAX. Po wygaśnięciu występuje Overheat i czasowa kara do statystyk.",
    "Zmiany: Cosmic Rave = 5 losowych trafień; Shoot-All = większy damage/crit; Starlight Shower = pełne AoE; Kamikaze Crush = większy limit HP; Heal Beam = party heal.",
]
HELP_TOPIC_ALIASES.update({"tech crafting":"techcraft","technologia":"techcraft","sockets2":"sockety2","sockety":"sockety2","vmaxstatus":"vmax2","v-max":"vmax2"})

# v0.32.0 HELP refresh — Party Progress, Recap, Tech Set Upgrade, Salvage 4.0
HELP_TOPICS["partyquest2"] = [
    "Party Quest Progress 2.0: kill questy oraz boss kill credit są przyznawane każdemu członkowi drużyny stojącemu w tej samej lokacji podczas zabicia.",
    "Gathering i crafting nie są współdzielone: postęp dostaje wyłącznie postać, która samodzielnie zebrała zasób lub wykonała recepturę.",
    "partyquest pokazuje bieżącą zasadę i liczbę członków drużyny stojących obok.",
]
HELP_TOPICS["dungeonparty"] = [
    "Dungeon Party Bonus działa wyłącznie w lokacjach lochowych.",
    "Pełna drużyna daje +3 procent EXP. Co najmniej 3 różne klasy daje +2 procent, a 5 lub więcej różnych klas kolejne +2 procent.",
    "Łączny bonus jest ograniczony do +7 procent, aby nie zaburzać głównego balansu progresji.",
    "dungeonbonus pokazuje aktualny bonus w bieżącej lokacji.",
]
HELP_TOPICS["recap2"] = [
    "Death/Combat Recap 2.0 rozszerza deathrecap i combatrecap.",
    "Recap pokazuje finalny cios, przyczynę śmierci lub zwycięstwa, ostatnie 10 zdarzeń walki, sumę leczenia i obrażenia zatrzymane przez aktywny guard.",
]
HELP_TOPICS["techupgrade"] = [
    "Tech Set Upgrade: części 8-elementowych setów Meca, Inżyniera i Cyborga można ulepszać z Mk-I do Mk-II i Mk-III.",
    "Użycie: techupgrade <pełna nazwa części EQ>. Mk-II wymaga Kowalstwo 240; Mk-III wymaga Kowalstwo 340 oraz rzadszych materiałów.",
    "Poziom Mk jest trwały. Mk-II/Mk-III zwiększa obronę części i wzmacnia działanie założonego Tech Setu.",
]
HELP_TOPICS["salvage4"] = [
    "Salvage 4.0 działa podczas rozkładania ostatniej posiadanej kopii danego EQ.",
    "Osadzone runy są zwracane do Szkatułki. Osadzone klejnoty mają szansę odzysku zależną od Kowalstwa: około 25 procent na początku do maksymalnie 85 procent.",
    "Nieodzyskany klejnot zostaje zniszczony podczas rozkładania.",
]
HELP_TOPIC_ALIASES.update({
    "party quest 2":"partyquest2", "party quest":"partyquest2", "questy drużynowe":"partyquest2",
    "dungeon party bonus":"dungeonparty", "bonus lochu":"dungeonparty",
    "recap 2":"recap2", "death recap 2":"recap2", "combat recap 2":"recap2",
    "tech set upgrade":"techupgrade", "tech upgrade":"techupgrade",
    "salvage 4":"salvage4", "salvage 4.0":"salvage4",
})


# v0.52.2 - City Courier Network
HELP_TOPICS["poczta"] = [
    "Poczta obsługuje dostawy paczek między 21 miastami i osadami Soulbound.",
    "W punkcie pocztowym wpisz poczta lista lub paczki. Lista ofert zmienia się automatycznie co 15 minut.",
    "Przyjmij kurs komendą paczka <numer> albo poczta wez <numer>. Jednocześnie możesz nieść jedną paczkę.",
    "poczta status pokazuje aktywną przesyłkę, cel i pełną nagrodę. Przyjęta paczka nie znika po odświeżeniu listy ani reconnect.",
    "Od v0.54.0 paczki nie mają losowych komplikacji, uszkodzeń, przechwyceń ani losowego obniżania wypłaty.",
    "poczta gildia pokazuje reputację 1-400, rangę, bonus wypłaty i odblokowane klasy przesyłek.",
    "poczta statystyki pokazuje liczbę dostaw, zarobek, najdłuższą trasę i odwiedzone miasta.",
    "poczta osiągnięcia pokazuje progi 10/100/1000/10 000 dostaw, wszystkie miasta i typy oraz osiągnięcia za 100 dostaw do każdego miasta i 100 dostaw każdego typu paczki.",
    "Prestiżowa paczka odblokowuje się od reputacji 360 (Strażnik Szlaków), zawsze pojawia się na liście po odblokowaniu i daje bardzo wysoką wypłatę bez losowego ryzyka.",
    "Po dotarciu do punktu pocztowego miasta docelowego wpisz poczta dostarcz. Nagrodą jest waluta; dostawy nie dają Soul XP.",
    "walk miasta / prowadz lista miasta pokazuje wszystkie miasta. Możesz też wpisać bezpośrednio np. walk Srebrna Korona.",
]
HELP_TOPIC_ALIASES.update({
    "postal": "poczta", "paczka": "poczta", "paczki": "poczta",
    "kurier": "poczta", "kurierzy": "poczta", "dostawy": "poczta",
})

HELP_TOPICS["questy_walka_0522"] = [
    "Od v0.52.2 każdy quest typu kill daje dodatkowo EXP Biegłości aktywnych klas.",
    "EXP Biegłości korzysta z aktualnych zasad balansu i istniejących bonusów x2 EXP, Gildii oraz Mentora. Generator Core został usunięty.",
    "Questy profesyjne i rzemieślnicze nie dają już Soul XP. Profesja i narzędzie zachowują własne EXP.",
]
HELP_TOPIC_ALIASES.update({
    "questy walki": "questy_walka_0522", "combat quests": "questy_walka_0522",
    "exp bieglosci quest": "questy_walka_0522", "exp biegłości quest": "questy_walka_0522",
})


# v0.59.0 - precise progression gaps command.
HELP_TOPICS["braki"] = [
    "braki / gaps / missing - pokazuje wyłącznie to, czego brakuje do najbliższych ważnych celów progresji.",
    "Level postaci: brakujący EXP do następnego Character Levelu.",
    "Soul Tier: brakujący Soul Level lub dokładny stan właściwej Próby Broni Duszy, a po jej ukończeniu przypomnienie o unlock.",
    "Profesje: dla każdej z 14 profesji brakujący XP do następnego poziomu albo informacja o maksimum.",
    "Gildia gracza: brakująca waluta w skarbcu do następnego poziomu Gildii.",
    "Kolekcje: liczba brakujących wpisów do 100% i trzy kategorie najbliższe ukończenia.",
    "Aktywne cele: do pięciu aktywnych questów oraz aktywna Tablica Zleceń, Legendarny Kontrakt i dostawa kurierska.",
]
HELP_TOPIC_ALIASES.update({"gaps": "braki", "missing": "braki"})


# v0.60.0 - rotating crafting orders and inventory EQ comparison.
HELP_TOPICS["zamowienia_rzemieslnicze"] = [
    "zamowienia / zamówienia / orders - pokaż do 3 rotujących ofert lokalnego specjalisty; system obejmuje wszystkie 14 profesji i odświeża się co 60 minut.",
    "zamowienia wez <numer> - przyjmij ofertę. Jednocześnie możesz mieć jedno aktywne zamówienie, ale każdą dostępną ofertę możesz ukończyć raz w danym cyklu; ukończenie jednej nie blokuje pozostałych.",
    "Wędkarstwo, Górnictwo, Drwalstwo i Zielarstwo liczą wyłącznie świeżo zebrane surowce po przyjęciu; przy oddaniu wymagana ilość jest pobierana z właściwego magazynu profesji lub ekwipunku.",
    "Zaklinanie liczy wyłącznie udane akcje zaklinania wykonane po przyjęciu; przy oddaniu nie pobiera się drugiego produktu.",
    "Kowalstwo, Gotowanie, Alchemia, Jubilerstwo, Krawiectwo, Garbarstwo i Stolarstwo nadal korzystają z prawdziwych receptur i fizycznych produktów.",
    "zamowienia status - pokaż cel, postęp, zleceniodawcę i nagrodę; zamowienia oddaj - oddaj gotowe zamówienie u właściwego NPC; zamowienia porzuc - anuluj.",
    "zamowienia historia / zamowienia statystyki - trwała historia ukończeń per profesja, zarobek, XP profesji/narzędzia i rekord nagrody; stare ukończenia sprzed v0.61.4 zachowują tylko pewny licznik.",
    "Nagrody to waluta oraz dodatkowy XP profesji i narzędzia. Zamówienia profesji nie dają Soul XP.",
]
HELP_TOPIC_ALIASES.update({
    "zamowienia": "zamowienia_rzemieslnicze", "zamówienia": "zamowienia_rzemieslnicze",
    "orders": "zamowienia_rzemieslnicze", "craft orders": "zamowienia_rzemieslnicze",
})

HELP_TOPICS["porownaj_eq"] = [
    "porownaj <przedmiot> / porównaj <przedmiot> / compare <przedmiot> - porównuje posiadany element EQ z aktualnie założonym wyposażeniem tego samego slotu.",
    "Pokazuje różnicę obrony, statystyk, właściwości procentowych i liczby gniazd. Uwzględnia upgrade, reforge, runy oraz klejnoty obecnie osadzone w założonym EQ.",
    "Dla pierścieni, talizmanów i kolczyków pokazuje osobne porównanie względem każdego zajętego slotu.",
    "Komenda działa poza sklepem i porównuje wyłącznie EQ, które faktycznie posiadasz.",
]
HELP_TOPIC_ALIASES.update({
    "porownaj": "porownaj_eq", "porównaj": "porownaj_eq", "compare": "porownaj_eq", "compare eq": "porownaj_eq",
})


# v0.61.4 - Crafting Logistics: bulk craft, recipe route and mail attachments.
HELP_TOPICS["crafting_logistics"] = [
    "craft <ilość> <receptura> - wykonuje podaną liczbę craftów, ale nie więcej niż pozwalają aktualne materiały; każdy craft zachowuje własny XP, jakość, krytyk, questy i bonusy.",
    "craft wszystko <receptura> / craft max <receptura> - oblicza maksymalną liczbę wykonań z bezpośrednich, pooled i distinct składników i wykonuje je istniejącym silnikiem craftingu.",
    "receptura droga <przedmiot> - pokazuje wielopoziomowy łańcuch produkcji od produktu przez półprodukty aż do źródeł surowców.",
    "Fragment Mithrilu z Salvage nie jest walutowym mithrilem: Kowalstwo 80 może z niego bezpośrednio wykuwać mithrilowe EQ (hełm 6, pancerz 10, rękawice 4, nogawice 8, buty 4, talizman 4). Normalne EQ ze sztabek nadal działa; dodatkowo 2 Fragmenty -> 1 Esencja Przekucia, 3 Fragmenty -> 2 Pyły Runiczne.",
]
HELP_TOPIC_ALIASES.update({
    "craft hurtowy":"crafting_logistics", "bulk craft":"crafting_logistics",
    "receptura droga":"crafting_logistics", "recipe route":"crafting_logistics",
})
HELP_TOPICS["mail"] = [
    "mail list - skrzynka; mail send <gracz> <tekst> - zwykła wiadomość; mail read <id> - odczyt.",
    "mail wyslij <gracz> przedmiot <nazwa> - wysyła jedną wolną, przekazywalną sztukę jako bezpieczny załącznik escrow.",
    "mail wyslij <gracz> waluta <kwota> <nominał> - wysyła walutę do escrow, np. mail wyslij Arven waluta 5 złota.",
    "mail odbierz <id> - odbiera załącznik dokładnie raz. Wiadomości z nieodebranym załącznikiem nie można usunąć.",
]
HELP_TOPIC_ALIASES.update({"poczta graczy":"mail", "player mail":"mail", "mail attachments":"mail"})

# v0.70.0 - Courier & Profession Expansion
HELP_TOPICS["questy_profesji_0700"] = [
    "Każda z 14 profesji ma 4 kontrakty mistrzowskie na poziomach 50, 150, 300 i 500.",
    "Kontrakty liczą rzeczywiste akcje profesji wykonane dopiero po przyjęciu zadania; nagrody XP z questów nie nabijają ich ponownie.",
    "Questy są odnawialne niezależnie i odbiera się je u mistrza danej profesji.",
]
HELP_TOPIC_ALIASES.update({
    "questy profesji":"questy_profesji_0700", "kontrakty profesji":"questy_profesji_0700",
    "profession quests":"questy_profesji_0700",
})


# v0.90.1 - unified reputation help.
HELP_TOPICS["reputacja"] = [
    "Reputacja w Soulbound jest trwałą progresją zaufania. Główne systemy to: Frakcje Świata, Reputacja Miast, Gildia Kurierów oraz Gildie Klasowe.",
    "frakcje / factions - pokazuje reputację pięciu Frakcji Świata. Szczegóły pomocy: help reputacja frakcji.",
    "reputacjamiast [miasto] / cityrep - pokazuje reputację 21 miast i bonus kurierski. Szczegóły: help reputacja miast.",
    "poczta gildia / poczta reputacja - pokazuje reputację Gildii Kurierów. Szczegóły: help reputacja kurierow.",
    "gildiaklasowa / reputacja - pokazuje reputację aktywnych gildii klasowych. Szczegóły: help reputacja gildii klasowej.",
    "postep / braki pomagają śledzić reputacje razem z pozostałą progresją postaci.",
]

HELP_TOPICS["reputacja_frakcji"] = [
    "Frakcje Świata: Liga Kartografów, Bractwo Wód, Kamienny Związek, Krąg Zielonego Szlaku i Straż Rubieży.",
    "Komenda: frakcje / factions. Możesz też podać nazwę frakcji, aby zobaczyć jej stan.",
    "Rangi: 0 Nieznajomy, 25 Sympatyk, 75 Zaufany, 150 Sojusznik, 300 Mistrz Frakcji.",
    "Liga Kartografów: reputację zdobywasz przez eksplorację proceduralnych rubieży, wielkie ruiny, wydarzenia świata i wybrane questy.",
    "Bractwo Wód: reputację zdobywasz podczas łowienia ryb oraz przez zadania powiązane z wodami.",
    "Kamienny Związek: reputację zdobywasz podczas Górnictwa oraz przez zadania powiązane z kopalniami i minerałami.",
    "Krąg Zielonego Szlaku: reputację zdobywasz podczas Drwalstwa i Zielarstwa oraz przez zadania związane z dzikimi terenami.",
    "Straż Rubieży: reputację dają m.in. Legendary Rare, World Bossowie, Mityczni World Bossowie, legendarne wydarzenia i wybrane questy endgame.",
    "Nagrody progowe frakcji obejmują tytuły, Mapę Skarbu, unikalną odznakę oraz nagrody końcowego progu.",
]

HELP_TOPICS["reputacja_miast"] = [
    "Każde z 21 miast i osad ma osobną trwałą reputację od 1 do 600.",
    "Komendy: reputacjamiast / miastarep / cityrep; reputacjamiast <miasto> pokazuje szczegóły jednego miasta.",
    "Rangi: 1 Przybysz, 40 Znajomy Miasta, 100 Zaufany Mieszkaniec, 180 Przyjaciel Miasta, 260 Opiekun Miasta, 340 Bohater Miasta, 400 Legenda Miasta, 450 Protektor Miasta, 500 Strażnik Dziedzictwa, 550 Symbol Miasta, 600 Wieczna Legenda Miasta.",
    "Reputację miasta zdobywasz przez lokalne questy oraz dostarczanie paczek do tego miasta.",
    "Wyższa ranga zwiększa wypłatę za paczki kierowane do danego miasta: od 0% do maksymalnie +20% przy 600 reputacji.",
    "Wszystkie lokalne questy miejskie, w tym Miasta 2.0, odnawiają się co 60 minut i pozwalają rozwijać reputację aż do 600.",
]

HELP_TOPICS["reputacja_kurierow"] = [
    "Gildia Kurierów ma trwałą reputację od 1 do 600. Zdobywasz ją głównie przez ukończone dostawy paczek.",
    "Komendy: poczta gildia, poczta reputacja, gildia kurierow, gildia kurierow statystyki.",
    "Rangi: 1 Posłaniec, 40 Kurier, 80 Kurier Gildyjny, 140 Starszy Kurier, 220 Kurier Królewski, 300 Naczelny Kurier, 360 Strażnik Szlaków, 400 Mistrz Szlaków, 450 Arcymistrz Szlaków, 500 Herold Szlaków, 550 Marszałek Szlaków, 600 Legenda Szlaków.",
    "Wyższa reputacja odblokowuje lepsze klasy paczek i zwiększa bazowy bonus wypłaty aż do +85% przy reputacji 600.",
    "Prestiżowa paczka odblokowuje się od reputacji 360 i daje bardzo wysoką wypłatę bez losowego ryzyka utraty przesyłki.",
    "Na przyrost reputacji wpływa m.in. długość trasy i klasa przesyłki; każda ukończona dostawa aktualizuje trwałe statystyki Kuriera.",
]

HELP_TOPICS["reputacja_gildii_klasowej"] = [
    "Każda aktywna klasa ma własną reputację Gildii Klasowej od 0 do 1000.",
    "Komendy: gildiaklasowa / reputacja; gildiaklasowa <klasa> pokazuje szczegóły konkretnej klasy.",
    "Rangi: 0 Nowicjusz, 100 Znany, 250 Zaufany, 450 Weteran, 700 Elita Gildii, 1000 Legenda Gildii.",
    "Rangi dają zniżkę na naukę skilli: 0%, 5%, 10%, 15%, 20% i maksymalnie 25%.",
    "Reputację zdobywasz przede wszystkim przez zadania klasowe, egzaminy i gildyjne zlecenia przeznaczone dla danej klasy.",
    "Egzaminy Soul 50/100/150/200 wymagają odpowiednio 100/250/450/700 reputacji Gildii; pierwszy wymaga także ukończenia zadania klasowego.",
]

HELP_TOPIC_ALIASES.update({
    "rep": "reputacja", "reputation": "reputacja", "reputacje": "reputacja",
    "reputacja frakcji": "reputacja_frakcji", "frakcje reputacja": "reputacja_frakcji", "faction reputation": "reputacja_frakcji",
    "reputacja miast": "reputacja_miast", "reputacjamiast": "reputacja_miast", "city reputation": "reputacja_miast", "cityrep": "reputacja_miast",
    "reputacja kurierow": "reputacja_kurierow", "reputacja kurierów": "reputacja_kurierow", "kurier reputacja": "reputacja_kurierow", "courier reputation": "reputacja_kurierow",
    "reputacja gildii klasowej": "reputacja_gildii_klasowej", "gildia reputacja": "reputacja_gildii_klasowej", "class guild reputation": "reputacja_gildii_klasowej",
})

HELP_TOPICS["ochronaeq"] = [
    "Ochrona EQ: chron <pełna nazwa>, odchron <pełna nazwa>, chron lista.",
    "Chronione przedmioty są pomijane przez sprzedaj wszystko i salvage wszystko; zwykła sprzedaż i salvage również odmawiają.",
    "Blokada obejmuje wszystkie egzemplarze tego samego item_id i zostaje po restarcie/deployu.",
]


# v1.28.12: human-readable information, never procedurally generated help.
HELP_TOPICS['podziemne miasta'] = [
    'Podziemne miasta znajdują się przy piętrach Krypty 50, 100 i 200 oraz Mitycznej Krypty 100.',
    'Szukaj zwykłego bocznego kierunku z głównej sali piętra. Miasta mają bramę, plac, targ, karczmę, kuźnię, archiwum i arenę.',
    'Sklep działa na targu. Karczma przyjmuje najemników. Mistrz w kuźni uczy skilli właściwej klasy. Na arenie czeka boss.',
    'Każda archiwistka daje powtarzalne zadanie miasta. W Bazaltowym Azylu rozpoczyna się także sześć etapów Kroniki Podziemi.',
]
HELP_TOPICS['kronika podziemi'] = [
    'Kronika Podziemi: 6 zależnych zadań od Archiwistki w Bazaltowym Azylu przy Krypcie piętro 50.',
    'Kolejne cele prowadzą przez arenę Bazaltowego Azylu, Archipelag, Ocean 2.0, Górnictwo, setne piętro Krypty i Mityczne Sanktuarium.',
    'Użyj quest list przy Archiwistce oraz quest info, aby sprawdzić cel. Na końcu czeka unikatowy Medalion Strażnika Kroniki.',
]
HELP_TOPICS['legendy świata'] = [
    'Rzadkie Legendarne i Mityczne potwory świata mogą wystąpić również na głębokich piętrach lochów.',
    'Mają własne afiksy i ataki, a ich ciała mogą zawierać Pieczęć Pradawnych Legend albo Serce Mitycznej Bestii.',
]
HELP_TOPICS['mistrzowskie rzemiosło'] = [
    'Wyjątkowe ARCYDZIEŁO może dodatkowo podnieść jakość wykonanego EQ.',
    'Szansa zależy od rodzaju materiału, poziomu profesji, narzędzia i mistrzostwa. Nie zmienia istniejących receptur ani limitów statystyk.',
]
HELP_TOPICS['najazdy świata'] = [
    'Co 3 godziny rotuje jeden z czterech podziemnych najazdów: nieumarli, smok, oblężenie i pradawny boss.',
    'Przy bramie ogłoszonego miasta pojawia się prawdziwy boss wydarzenia; walczyć można solo lub w drużynie.',
    'Komunikaty świata ogłaszają nowy kryzys. Wydarzenia nie zmieniają zwykłego EXP ani resetu istniejących bossów.',
]
for _alias, _topic in {
    'miasta podziemne':'podziemne miasta',
    'kronika':'kronika podziemi',
    'legendarne potwory':'legendy świata',
    'arcydzieła':'mistrzowskie rzemiosło',
    'wydarzenia podziemi':'najazdy świata',
}.items():
    HELP_TOPIC_ALIASES.setdefault(_alias, _topic)


HELP_TOPICS['ery'] = [
    'SZEŚĆ ER: ery imperia, ery wymiary, ery odkrywcy, ery gracze, ery starozytni, ery dusze.',
    'Rozpocznij wyprawy bez teleportów: w grze działa normalny ruch po kierunkach.',
    'Przy NPC wpisz quest list oraz quest przyjmij. Siedziby gildii: gildia siedziba, domy: house.',
    'W nowych lokacjach dostępne są sklep, kontrakty, bossowie, artefakty i dalsze zadania.',
]


# v1.37.0: accessible command help without replacing the legacy achievements menu.
HELP_TOPICS['medale'] = [
    'Legendarne osiągnięcia: 492 trwałe cele. 14 klas, 14 profesji, rozwój postaci, Dusza, Broń Duszy i rekordy wyczynów.',
    'medale: liczba odblokowanych celów i ostatnie wpisy.',
    'medale rozwoj, medale klasy, medale profesje, medale wyczyny: kategorie.',
    'medale brakujace: następny cel każdego rodzaju z rzeczywistym postępem.',
    'medale profesje 2: druga strona. Maksymalnie 15 wpisów naraz dla NVDA.',
    'kronika postaci lub kronikapostaci: historia odblokowanych wyczynów.',
    'medale rekordy: najwyższe poziomy z prawdziwych zapisów graczy.',
    'Tytuły są przyznawane jednokrotnie. Możesz je włączać przez tytul.',
]

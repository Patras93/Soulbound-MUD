# -*- coding: utf-8 -*-
"""Pure data catalog for Soulbound v4.00.5.

No global runtime import, no shared mutable templates: each builder returns
fresh dictionaries; the legacy systems.content_registry runtime remains the
only owner of the mutable catalogs after initialization.
"""

def make_npc_descriptions_v405():
    """Build the original v4.00.4 NPC_DESCRIPTIONS data as a fresh dictionary."""
    return {
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

def make_mob_descriptions_v405():
    """Build the original v4.00.4 MOB_DESCRIPTIONS data as a fresh dictionary."""
    return {
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

def make_stat_descriptions_v405():
    """Build the original v4.00.4 STAT_DESCRIPTIONS data as a fresh dictionary."""
    return {
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

def make_system_descriptions_v405():
    """Build the original v4.00.4 SYSTEM_DESCRIPTIONS data as a fresh dictionary."""
    return {
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

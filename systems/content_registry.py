from data import catalog_mutations as _catalog_mut
from data.items import ITEMS
from data.crafting_recipes import CRAFT_RECIPES
from data.alchemy_recipes import ALCHEMY_RECIPES
from systems.equipment_crafting import COOK_RECIPES, JEWELCRAFT_RECIPES, CUT_GEM_IDS

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


from data.world_description_catalog_v405 import make_npc_descriptions_v405
NPC_DESCRIPTIONS = make_npc_descriptions_v405()

from data.world_description_catalog_v405 import make_mob_descriptions_v405
MOB_DESCRIPTIONS = make_mob_descriptions_v405()

from data.world_description_catalog_v405 import make_stat_descriptions_v405
STAT_DESCRIPTIONS = make_stat_descriptions_v405()

from data.world_description_catalog_v405 import make_system_descriptions_v405
SYSTEM_DESCRIPTIONS = make_system_descriptions_v405()


LATEST_CHANGES_TITLE = "Soulbound v11.00.17 - PROSTE KOMENDY PROFESJI"
LATEST_CHANGES = [
    "v11.00.12: osiem imiennych nauczycieli klas v9 oferuje po trzy własne questy klasowe; rozmowa pokazuje zadanie i nadal umożliwia learn. Help mag i pozostale klasy wyświetlają opis bez proszenia o wpisanie nazwy skilla. Skradzione Skrzynie Rudy częściej wypadają z trolli, wymagane 10 sztuk i nagrody bez zmian.",
    "v11.00.11: help <nazwa skilla> otwiera pełny opis, tak samo jak help skill <nazwa>; działają nowe nazwy 22 klas, stare aliasy, ID i polskie znaki. Bez wykonywania skilla ani zmiany balansu.",
    "v11.00.10: 4659 nazw skilli odróżnia klasy i mechanikę. Zachowano 5461 ID, wszystkie parametry, wyuczone skille i stare aliasy dla makr.",
    "v11.00.9: 18 typów questów pokazuje rzeczywiste liczniki; Droga Legendy raportuje każde zaliczenie; przedmioty i zbiórki nie giną w trybie zwięzłej walki; questy postęp.",
    "v11.00.8: wszystkie deski obrabia Piła w Obozie Drwala; XP Drwalstwa i Piły, nie Kowalstwa; obrabiaj i receptury drwalstwo; wyroby Stolarstwa zachowane.",
    "v11.00.7: HELP otwiera wyłącznie pomoc, bez komunikatu o użyciu skilla; krótkie nazwy wszystkich dawnych komend z cyframi; stare aliasy zachowane.",
    "v11.00.6: Krótkie komendy profesja, kupiectwo, karawana, lowy, wyprawa, rozbudowa; stare komendy zgodne.",
    "v11.00.5: Questy i zlecenia profesji nie wyplacaja Soul XP; oferta NPC wyswietla faktyczne nagrody.",
    "v11.00.4: Osiem nowych narzędzi w sklepach mistrzów; trwały zakup raz na postać także dla starszych narzędzi.",
    "v11.00.4: Tablica Zleceń w Sali Głównej Gildii Dusz; zdalny odczyt postępu bez zmian w SQLite.",
    "v11.00.3: HELP <temat> poprawiony globalnie. Nowe profesje i karawany, inteligentne wyszukiwanie, lista stronicowana pod NVDA.",
    "v11.00.2: Hotfix Przysiegi Switu, prawidlowy poziom rzeczywistego moba dla Drogi Legendy (22 klasy). Nowy numer wydania umozliwia legalne wdrozenie po v11.00.1.",
    "v11.00.1: 22 najemników odpowiadających 22 klasom, zachowano stare kontrakty i pełną moc obrażeń; osiem nowych klas ma zadania gildyjne. Droga Legendy zalicza walki każdej aktywnej klasy, bez zmian EXP i SQLite.",
    'v11.00.0: Era Wiecznej Chwały — dwanaście nowych krain, dwanaście podziemi fabularnych i trzy dodatkowe nieskończone lochy.',
    'v11.00.0: EP automatycznie za ważne odkrycia poza miastami; 1 EP i 1 unikatowe Fame nagradzają 100% aktualnego Multi Cap EXP.',
    'v11.00.0: Nowi superbossowie, dwanaście rozdziałów Wojny Pradawnych, mistrzowskie techniki 22 klas, próby i łupy.',
    'v11.00.0: Rozbudowa najemników, przywołań, 22 profesji, gildii, oceanu i Kartografii; zachowano dawny świat, EXP Bank oraz zapisy SQLite.',
    'v11.00.0: Przed wdrożeniem wymaga Windows PREDEPLOY 60/60 PLUS na kopii rzeczywistej bazy.',
    'v10.00.0: Zapomniane Horyzonty: sześć powiązanych regionów, 72 pokoje, 18 punktów mapowania, 6 przewodników, 12 ręcznie opisanych questów.',
    'v10.00.0: EXP Goal = 50 procent aktualnego Multi Cap; bez zmian nagród i progów. Fame i EP mają zwięzły status pod NVDA.',
    'v10.00.0: Kartografia regionu pokazuje charakterystyczne miejsca zmapowane komendą mapuj; samo speedwalk nie zalicza dokumentacji.',
    'v10.00.0: Wszystkie 22 klasy/rasy, 22 profesje, Bronie Duszy, SQLite, EXP Bank, EP/Fame i długoterminowy grind zachowane.',

    'v8.00.0: 1680 nowych zadań Drogi Legendy (14 klas × 120 etapów); 14 oddzielnych mentorów.',
    'v8.00.0: wymagające realne walki, elity, bossowie, eksploracja i zdobywanie surowców.',
    'v8.00.0: NVDA — tylko aktualny etap u mentora, krótkie komunikaty postępu; trwały SQLite bez resetów.', 
    "v7.10.1: oddzielne EQ fizyczne i magiczne; tylko Mec pozostaje hybrydą z pięcioma statystykami i Attack/Magic Attack. MultiClass EQ nie dopisuje już obcych statystyk. Zachowano przedmioty i ulepszenia.",
    "v7.10.1: jedna klasa główna na postać, pozostałe Biegłości i skille zachowane w SQLite jako archiwum; tylko główna klasa daje pasywy, skille i cap. MultiClass add/remove wyłączone.",
    "v7.10.0: chronologia questów Kroniki, pełny podgląd kosztów, zwięzłe dokładne nagrody EXP i mocniejsze testy transakcji SQLite i NVDA; brak nerfów i zmian istniejących questów.",
    "v7.00.0: osiem powiązanych systemów gospodarczych, 64 nowe questy Kroniki, 3925 zadań łącznie; zachowano wszystkie profesje i zapisy.",
    "v7.00.0: 22 kontrakty mistrzowskie, 8 rozbudów, cztery wyprawy morskie, cztery karawany, prawdziwe legendarne łowy i NVDA zwięźle/pełne.",
    "v6.00.1: 960 nowych questow (8 profesji x 120 etapow) od 1 do 800, 8 osobnych NPC; konkretne czynnosci, progi i prawdziwy postep SQLite.",
    "v6.00.0: 8 nowych profesji i 8 narzędzi, 26 czynności, 7 progów trudności, własne łańcuchy prac, zamówienia, trwałe jednorazowe zakupy, gotowanie i rzemiosło; baza v5.00.1.",
    "v5.00.1: nowe konto otrzymuje prywatny kod odzyskania hasla; obecny gracz wpisuje konto kod i zapisuje go poza gra.",
    "v5.00.1: menu 4 odzyskuje haslo kodem, nie poczta; wygasle, zuzyte i poprzednie kody sa blokowane.",
    "v5.00.0: 12 indywidualnych faz Pradawnych i zmieniane ataki zywiolowe; 32 kontynuacje historii i osiem prob lochowych.",
    "v5.00.0: 28 nowych prawdziwych skilli 14 klas; 28 nowych receptur i zlecen dostawy; piec istniejących flot z taktykami.",
    "v5.00.0: niezalezne od progow nagrody XP, EP i Fame; SQLite bez destrukcyjnej migracji.",
    "v4.21.1: EP przyznaja stale 120-220 XP za punkt wedlug lokacji, nie od wymagan poziomu; Fame ma osobna krzywa nagrod i nie uzywa capu jako wyplaty.",
    "v4.21.1: Nie zmieniono liczby EP za pokoje, EXP z walk, questow, profesji, progow EXP 1-800, postaci ani SQLite.",
    "v4.00.4: Dwa legendarne wydarzenia nigdy nie blokuja sie przez wspolna lokacje.",
    "v4.00.4: Pradawny Rozrost i pozostale wydarzenia gwarantuja poprawne akcje profesji.",
    "v4.00.3: Wszystkie 14 narzedzi wymagaja wiecej XP do kolejnego poziomu: wedka x5, kilof x4, pozostale x3.",
    "v4.00.3: EXP za czynnosci bez zmian; zachowano zdobyte poziomy, zapisany postep i stare progi 14 profesji.",
    "v4.00.2: naprawiono izolacje katalogu klas i mistrzowskich skilli przy powtornym uruchomieniu modulu; brak duplikatow.",
    "v4.00.2: specjalny test sprawdza dwoch powtornych wykonaniach 14 klas, 3445 skilli i poziomy 260/420/600.",
    "v4.00.1: przeniesiono deklaracje skilli 14 klas do core/class_skill_catalog.py bez zmian w danych lub kolejnosci patchy.",
    "v4.00.1: rozdzielono funkcje rozbudowy swiata na 4 osobne moduly; world.expansions utrzymuje dotychczasowe punkty wejscia i EXP_AREAS.",
    "v4.00.1: bez nowych funkcji gry, narzedzi, receptur, balansu, SQLite czy zmiany wszystkich 2701 zadan; wymagania EXP nadal x10.",
    "v4.00.0: Kroniki Korony Dusz — 32 historie starego świata, 5 nowych tras morskich, 12 superbossów, 14 ścieżek profesji i 70 prawdziwych receptur bez nowych narzędzi.",
    "v4.00.0: Każdy nowy NPC ma własny pokój. Najemnicy stosują nowe bezkarne reakcje fazowe. Bez zmian progów EXP x10, poziomów postaci, starych questów i SQLite.",
    "v3.31.4: WSZYSTKIE osie permanentnego rozwoju od poziomu 1 wymagaja 2x wiecej EXP niz v3.31.3, lacznie 10x wobec v3.30.0: postac, biegosc 14 klas, Dusza, Bron Duszy, skille, statystyki, 14 profesji i narzedzi oraz Wzniesienie.",
    "v3.31.4: NIE ZMNIEJSZONO nagrod EXP, zdobytych poziomow, postepu, bonusow eventow, dropu, Multi Cap ani zapisow SQLite. Zachowano 200 questow v3.31.3, osobne NPC, naprawe eventow i bandytow.",
    "v3.31.3: 200 nowych, godzinnych zlecen opartych na prawdziwych czynnosciach profesji: osiem etapow dla kazdej z 14 profesji (112), dodatkowe 22 etapy dla Stolarstwa, Krawiectwa, Garbarstwa i Zaklinania (88).",
    "v3.31.3: zachowano stare questy i ich nagrody, x5 progi EXP, zdobyte poziomy, Multi Cap, SQLite i zasade jeden NPC na pokoj. Nowe zadania sa widoczne u dotychczasowych mistrzow; brak nowych blokad poziomu.",
    "v3.31.2: aktywne wydarzenia złoż rudy, ławic, ziół i boru oraz legendarne żyły/prądy/rozkwity/rozrosty pozwalają wykonać rzeczywistą akcję profesji na oznaczonym sektorze, bez otwierania wydobycia w całym świecie.",
    "v3.31.2: rotujące stanowisko wykopaliskowe pozwala użyć wykop i daje +25% XP Archeologii/Pędzla. Komenda wydarzenia pokazuje aktywne grupy eventów i właściwe komendy; kryzys pomoc/ratuj odblokowane.",
    "v3.31.1: Kwatermistrz Bandytow i Bandycki Mistrz Pojedynku zaliczaja teraz zabicia do aktywnych questow bandytow u Roderika, Elii i na Tablicy Godzinnych Zlecen.",
    "v3.31.1: nowy test 13 odmian bandytow, izolacji kont SQLite i komunikatu Postep questa w trybie combat concise (essential). Zwykli bandyci byli przypisani poprawnie, wiec brak komunikatu u nich wymaga sprawdzenia aktywnosci zadania.",
    "v3.31.0: wszystkie progresje zdobywajace EXP potrzebuja x5 wiecej EXP do kolejnego poziomu: postac, 14 klas, Dusza, skille, Bron Duszy, statystyki, 14 profesji, 14 narzedzi i Wzniesienie. Takze poziomy 1-49.",
    "v3.31.0: NIE ZMIENIONO wyplacanego EXP, EXP Bank, Multi Cap, nagrod, dropu, zdobytych poziomow, zapisanego postepu ani limitow. Zachowane historyczne krzywe i roznice trudnosci profesji. Wymagania liczone na biezaco.",
    "v3.30.0: naprawiono 56 nieoddawalnych zadan profesji w Erze Legend (v3.10 i v3.20): kazde zadanie ma prawidlowy typ narzedzia dla swojej profesji.",
    "v3.30.0: rozbudowano bramki predeploy o audyt 2134 nagrod questowych, celow fabularnych, tras NPC i rzeczywistych zdarzen postepu w izolowanej SQLite. Bez resetowania postaci i zmian krzywych EXP.",
    "v3.20.0: JEDNO WIELKIE WYDANIE — fabula starego i nowego swiata, mistrzostwo 14 klas, 14 profesji, eksploracja 3.0, ekspedycje 2.0, superbossowie 8.0 i odnawialne Kroniki. Pomoc: help legendy.",
    "v3.20.0: nowe kampanie, sale i bossowie dodane bez kasowania starych NPC, questow, klasy, danych SQLite i bez ograniczania Multi Cap. 42 prawdziwe umiejetnosci klasowe mozna opanowac u dawnych nauczycieli.",
    "v3.10.5: naprawiono niespojnosc wersji w komendzie changes i bramce PREDEPLOY. VERSION, CHANGELOG_PL i LATEST_CHANGES_TITLE teraz wskazuja v3.10.5. Bez zmian rozgrywki, SQLite, kont i postaci.",
    "v3.10.4: koncowy pelny audyt NPC poprawnie otrzymuje migawke oryginalnych identyfikatorow i przechodzi testy bez zmniejszenia rygoru kontroli.",
    "v3.10.3: finalny predeploy porownuje tozsamosc wszystkich pierwotnych NPC zamiast wymagac niezmiennej liczby po testach. Nadal wykrywa znikniecia, wspoldzielone pokoje, brak wyjsc i popsute sklepy. Bez zmian danych gry i SQLite.",
    "v3.10.2: stare fronty Bazaltu i Szronu uznaja dowodce w przyleglym, odrebnym gabinecie zamiast wymagac starego pokoju. Dodatkowe kontrole przejsc, wylacznosci NPC i negatywne testy zabezpieczen; brak zmian w balansie i SQLite.",
    "v3.10.1: zlikwidowano wspoldzielenie pokojow przez NPC w calym swiecie, zachowano sklepy, nauczycieli i drogi. `przyjmij 1` i `przyjmij 2` wybieraja oferte jedynego NPC w pomieszczeniu bez wczesniejszej listy.",
    "v3.10.0: FUNDAMENT FABULY — 8 nowych krain (Korony, Khar-Dum, Dzicz, Morze Dusz, Chaos, Cytadela, Owady, Elfowie), Sala Drogowskazow i 8 bram. 141 nowych polaczonych lokacji, 53 NPC, 48 przeciwnikow/bossow, 8 unikatowych przedmiotow questowych i 168 zadan. Realne wieloetapowe historie: przynies, zabij, porozmawiaj, wyprawy i odnawialne kroniki.",
    "v3.10.0: 8 nowych bossow swiata, 8 pieciopokojowych ekspedycji z bossami, 32 rozdzialy fabuly starego swiata, 28 etapow klas i 28 zamowien fabularnych profesji. EXP/SQLite/Multiclass 14 i wszystkie starsze zadania zachowane; wejscie z Placu Dusz na polnocny zachod. Pomoc: help legendy.",
    "v3.10.0: to PIERWSZY GRYWALNY ETAP wielkiego dodatku. Nie dodano jeszcze zapowiedzianych nowych skilli bojowych 14 klas ani zaawansowanych mechanik profesji/bossow — zadania fabularne mistrzow juz sa. Wymagane Windows PREDEPLOY 60/60 PLUS przed wdrozeniem.",
    "v3.00.7: ep pokazuje jednym wierszem trwale zdobyte Exploration Points. ep region i ep all przedstawiaja eksploracje regionu i calego swiata. Odczyt tylko do odczytu, bez zmian nagrod, postaci i SQLite.",
    "v3.00.7: Borys na Targu Rybnym ma 48 nowych, niezaleznych zlecen: 4 akweny (rzeka, jezioro, morze, ocean), 32 konkretne gatunki od podstawowych po legendarne, 8 mieszanych zestawow i 4 wyzwania odkrycia roznych gatunkow. Kazde rozlicza wylacznie polowy po przyjeciu; nagrody Wędkarstwa i Wędki oraz monety rosną wraz z trudnoscia, kazde odnawia sie osobno po godzinie. Zachowane wszystkie starsze questy, postacie, EXP, SQLite i NPC Neris.",
    "v3.00.6: help kolejka opisuje auto-ucznie, kolejki bez limitu i 25 pozycji na strone; historyczny audyt HELP nie podmienia juz opisu na przestarzaly limit. Bez zmian mechaniki v3.00.5 i danych SQLite.",
    "v3.00.5: kazdy aktywny skill i czar po nauczeniu u nauczyciela automatycznie trafia do odpowiedniej kolejki fizycznej, magicznej lub Feedback. W czasie walki wybierane sa gotowe umiejetnosci bez recznego kolejka dodaj. Starsze poznane skille sa dodawane jednorazowo z zachowaniem pozniejszych recznych usuniec. Limit 40-120 slotow usuniety; NVDA lista jest stronicowana po 25. Tempo walki, mana, aktywne klasy, cooldowny i autoatak Broni Duszy bez zmian.",
    "v3.00.4: kazdy punkt eksploracji nagradza jak Fame: oddzielne pelne nagrody EXP postaci, Duszy, kazdej aktywnej klasy i kazdej statystyki; bez EXP profesji i narzedzi. Wszystkie wyplaty podlegaja Multi Cap / EXP Bank i nie sa dzielone.",
    "v3.00.4: komenda learn bez argumentu przy nauczycielu aktywnej klasy wypisuje numerowana liste skilli, ceny i wymagania; learn <numer> ma identyczne indeksy jak talk nauczyciela. Poza nauczycielem nauka jest zablokowana, a lokalny look podaje skladnie. Bez zmian SQLite i EXP.",
    "v3.00.3: poprawiono start SQLite bez automatycznego usuwania osieroconych kontraktow/taktyk; globalny wipe czysci je dopiero na jawne polecenie administratora. v3.00.2: zaktualizowano help progresja800, multiclass, wzniesienie i worldtier; rzeczywisty prog Wzniesienia Bieglosc 800; Soul Tier 80; kolejka 40-120 slotow; hybrydowe EQ w pomocy, zgodnosc z NVDA. Naprawa czyszczenia kontraktow i taktyk najemnikow przy wipe postaci oraz usuwaniu pojedynczej postaci. Schemat SQLite, EXP i balans bez zmian.",
    "v3.00.1: fizyczne EQ daje dodatkowo INT, Sile Woli i Magic Attack; magiczne EQ daje dodatkowo STR, Zrecznosc i Attack. Bonusy liczone osobno przy zakladaniu, widoczne w eq info/porownaj i liczone w auto-EQ. Dotychczasowe staty, ceny, SQLite, sety i EXP bez zmian.",
    "v3.00.0: przebalansowanie zagrozenia dla postaci ponizej zalecanego poziomu w calej grze, takze na terenach 1-99. Zwiekszony HP i presja obrazen przeciwnikow o wyzszym etapie, z plynna zaleznoscia od roznicy poziomow; CONSIDER podaje ostrzezenie. Bez sztywnych blokad, bez kar do obrazen najemnikow i przywolan, bez obnizania EXP/dropu i bez zmian SQLite. Nowych systemow nie dodano.",
    "v2.32.19: pelny Multi Cap takze za zwykle wydobywanie, zbieranie, crafting oraz sprzedaz surowcow. Wysokie poziomy profesji i narzedzi wymagaja wiecej EXP od poziomu 50; przyznawane nagrody EXP nie sa zmniejszane, jakosc materialu nadal podnosi nagrody. EXP Bank zachowuje kazda nadwyzke i wyplaca maksymalnie 1 bank XP za 1 swiezo przyznany XP, nie pozwalajac na wyplate milionow za 1 XP. Wszystkie postacie i zapis SQLite bez resetu.",
    "v2.32.18: wszystkie 14 aktywnych klas otrzymuje osobno cala nagrode Class XP do pelnego Multi Cap, bez dzielenia przez liczbe klas. Sila i kazda inna statystyka, Dusza, skill, profesja i narzedzie maja oddzielny limit tej samej wielkosci; nagrody nadal zalezne od przeciwnika i czynnosci. Fame nie mnozy juz surowej nagrody przez liczbe klas; brak sztucznego przyspieszania eventow. EXP Bank per klasa zachowany.",
    "v2.32.17: narastający Multi Cap co 10 poziomów KAŻDEJ zdobytej dziedziny: 1-10 +500, 11-20 +1000, 21-30 +5000, 31-40 +7500, dalej +2500 do stawki co 10 poziomów bez końca. Każda klasa, Soul, stat, skill, profesja, narzędzie i wzniesienie liczone osobno; to limit nagród, nie zmiana wymaganych XP ani wysokości dropu. Komenda level pokazuje rzeczywiste Soul XP, próg i brak do kolejnego Soul Level. Ostatnia linia to Your experience cap is N EXP.",
    "v2.32.16: komenda level pokazuje wszystkie rzeczywiste poziomy postaci, Duszy, Soul Tier, Broni Duszy, odblokowanych 14 klas (takze nieaktywnych), statystyk, poznanych skilli, profesji, narzedzi i wzniesien. Ostatnia linia dokladnie: Your experience cap is N EXP. Ten sam Multi Cap co expcap, bez ograniczania listy lub zmiany danych i nagrod.",
    "v2.32.15: Multi Cap EXP = 500 razy suma trwałych poziomów postaci, Duszy, Soul Tier, Broni Duszy, wszystkich poznanych klas i skilli, statystyk, profesji, narzędzi oraz wzniesień. Jedna wspólna wartość capu każdej osobnej nagrody, XP Bank i boss doublecap zachowane. Multiclass do 14 klas, każda ma własną Biegłość i niezależny postęp; walka nie rozwija profesji.",
    "v2.32.14: regresja uruchamiania w tle rozpoznaje poprawne przekazywanie kodu procesu przez !errorlevel! z EnableDelayedExpansion; wczesniejsze sprawdzenie wymagalo starej formy %errorlevel%. Bez zmian STOP/Watchdog, rozgrywki i SQLite.",
    "v2.32.13: STOP i nadzorca Windows dzialaja razem, a brak tokenu blokuje niebezpieczna podmiane plikow. Dodatkowe sterowanie w TEMP i testy PREDEPLOY bez zmian rozgrywki.",
    "v2.32.6: pelny predeploy 9 etapow z osobnej paczki ZIP bez zatrzymania serwera. Bramka PASS i SHA256 przed wdrozeniem, bez zmian danych i mechaniki gry.",
    "v2.32.5: wszystkie wysokie tereny, w tym Krypty, Wieze, Magitek, Deep Dungeon, Ocean, Archipelag, wymiary i wydarzenia. Poziom przeciwnika oraz terenu podnosi HP i zadawane obrazenia, kiedy grupa ma duzo nizszy poziom. Bez blokad poziomu, bez kar dla najemnikow; CONSIDER zgodny z walka; Railway/SQLite bez zmian.",
    "v2.32.4: Dockerfile kopiuje testuj_soulbound_windows.py przed FAST/FULL na Railway, dzieki czemu testy validation/v2102_predeploy_contract.py i v2302_coverage_contract.py moga poprawnie importowac kontroler; po buildzie usuwa modul testowy z obrazu runtime. Nowy test sprawdza COPY, kolejnosc i cleanup. Bez zmian mechaniki gry i SQLite.",
    "v2.32.3: zamknieto oba fizyczne polaczenia SQLite po tescie automatycznego wielopunktowego EP. Windows WinError 32 przy usuwaniu real.sqlite przestaje blokowac FAST/FULL; nowa regresja sprawdza faktyczne zamkniecie uchwytow i usuwalnosc pliku. Bez zmian punktacji EP, balansu i danych postaci.",
    "v2.32.2: automatyczne 2-8+ EP za nowa lokacje zalezne od poziomu, sekretu i bossa, osobny pelny EXP Cap za kazdy EP, zapis EP w SQLite, poprawny bilans eksploracji. Prowadzenie bez look() tez odkrywa pokój tylko raz na konto. Naprawiono test Matki Popiolu z uwzglednieniem skalowanych szablonow bossa. Bez resetowania SQLite i balansu.",
    "v2.32.1: Matka Popiolu odradza sie w Legowisku Matki Popiolu zamiast na Popielnej Grani. Przed wydaniem tester sprawdza prawdziwy spawn World(), obecność, brak wedrowania i odrodzenie. Nie zmieniono SQLite, nagrod ani innych bossow.",
    "v2.32.0: realne TCP: rozmowa z Kaplanem Elorem, oferta, przyjecie zadania przez leadera, dzielenie z piecioma innymi klientami, odmowa nagrody przed ukonczeniem, zejscie do piwnicy, zabicie szczura i trwały postep SQLite po restarcie. Planer tras i dziewiec obowiazkowych bramek. Nadal NOT TESTED pozostale calosciowe scenariusze NPC i 1526 odbiorow nagrod.",
    "v2.31.0: tester uruchamia realne metody postepu questow w SQLite dla dostepnych rodzajow, sprawdza izolacje kont, limity, restart, porzucenie oraz brak progresu po ukonczeniu. Pozostale typy i kompletna fabula/NPC pozostaja jawnie NOT TESTED. Osiem bramek Windows; bez zmian mechaniki gry.",
    "v2.30.2: szerszy predeploy Windows, 7 bramek, kontrola wszystkich handlerow i typow questow, izolacja postepu kont oraz rzeczywiste dodatkowe scenariusze TCP. Raport nadal jasno odroznia brak testu pelnej gry od PASS.",
    "v2.30.1: naprawa blokady tymczasowej bazy po testach 6 graczy TCP na Windows, nowe testy jawnego zamykania SQLite, bez zmian balansu i zapisow postaci.",
    "v2.30.0: globalne role AI na zwyklych potworach, 42 receptury mistrzowskie w 14 profesjach, 2 nowe legendarne szlaki oceanu i 6 obowiazkowych etapow predeploy Windows. Bez resetu SQLite, Fame, EP i EXP Banku.",
    "v2.20.0: Ocean 5.0 cztery nowe regiony, 16 lokacji, 16 przeciwnikow i bossow, 4 questy i 4 cele flot; Inteligentni Przeciwnicy 5.0 — role potworow w nowych regionach; Mistrzowie Profesji 6.0 — 14 profesji, 42 sciezki i zamowienia zalezne od rzeczywistych czynnosci. Predeploy v4.0: dodatkowe testy scenariuszy SQLite/AI/mapy, stare audyty i 6 graczy TCP zachowane.",
    "v2.10.3: Fame i kazdy EP daja pelny aktualny EXP Cap przez EXP Bank. Questy zawsze rozliczaja srebro, zloto i mithril; zwykle zadania bez waluty dostaja minimum 1 zloto. Pelny predeploy wykrywa regresje nagrod i testuje wszystkie questy.",
    "v2.10.2: TESTUJ_Soulbound uruchamia FAST, FULL (wszystkie aliasy, komendy, questy i SQLite) oraz 6 klientow TCP na localhost, z druzyna, wieloma komendami i restartem; testowa baza. Braki scenariuszy raportowane jako NOT TESTED.",
    "v2.10.1: naprawiony znacznik dynamicznego generatora Labiryntu Echa w audycie wyjsc; brak zmian checkpointow i starszych zapisow.",
    "v2.10.0: osiem Tytanow co 50 pieter, sekretne komnaty co 25 pieter, fazy 70/40/15, tytani obrona, artefakty, osobisty bonus 24h i trwale zapisy SQLite. Komendy tytani i lochy7; stare portale i EXP Bank bez zmian.",
    "v2.00.11: EXP Bank w SQLite zapisuje nadwyzki ponad cap z osobnym saldem dla kazdej osi. expbank pokazuje saldo; wolne miejsce w nastepnej nagrodzie wyplaca bank bez przekraczania capu.",
    "v2.00.10: portal N i astralportal N przenosza z odblokowanego checkpointu bezposrednio na inny odblokowany checkpoint zwyklych i mitycznych Krypt/Wiez; Katakumby portal 1/2/3 zapisane jako odwiedzone; zachowane limity, Fame, exp i SQLite.",
    "v2.00.9: experience cap / your experience cap do 800, doublecap trudnych bossow, Fame na kolejnych pietrach oraz pietro gora / pietro dol przez prawdziwe schody; bez resetu SQLite.",
    "v2.00.8: żywiołaki Maga zadają minimum obrażeń wynikające z rzeczywistego magicznego uderzenia właściciela, zachowując starsze wysokie obrażenia, rangi i bariery.",
    "v2.00.7: naprawiony NameError ROOMS w consider / con podczas opisu regionu; dodano testy komendy na terenach poczatkujacych i dawnych lokacjach, bez zmiany balansu.",
    "v2.00.6: regionalny balans swiata; Gobliny, Bandyci i dalsze jaskinie maja recznie ustawione etapy zamiast przypadkowego poziomu z nazwy.",
    "v2.00.3: szybsze przejscia swiata, jednoczesne dostarczanie komunikatow wielu klientom, przywolania, SQLite, NVDA i test obciazenia TCP.",
    "v2.00.2: szybkie rozliczanie serii przywolan; pojedynczy odczyt premii miasta, jedna kalkulacja mocy Maga, pojedyncze wyszukiwanie moba; opcjonalne pomiary wydajnosci i usuniecie podwojonego komunikatu frakcji.",
    "v2.00.1: katalog wartosci liczbowych wczytywany strumieniowo z pliku skompresowanego, z pelna zgodnoscia wartosci i mniejszym zuzyciem pamieci przy starcie.",
    "v2.00.0: 4 wymiary i 3 archipelagi Oceanu 5.0, siedem trwałych frakcji z kontraktami oraz Arena Legend 3.0 z 3 falami i bossem. SQLite i dawne statki zachowane.",
    "v1.90.1: optymalizacja AoE przy 10+ mobach: AI sprawdza aktualny pokój zamiast całego świata i pomija niepotrzebne wyszukiwania podczas cooldownu. Bez zmian w sile mobów, EXP, Fame i przywołaniach.",
    "v1.80.8: Kobra Piasków zatruwa; żywiołaki Ognia podpalają, Lodu i Kryształu zamrażają, Błyskawic porażają. DOT i pojedyncza utrata akcji działają w prawdziwej pętli walki, bez permanentnego blokowania bossów.",
    "v1.80.7: fame pokazuje liczbę zdobytych punktów, where fame / gdzie fame mówi none/some/most/all w obecnym terenie; istniejące zapisy i komendy Fame zachowane.",
    "v1.80.6: Fame zaliczane natychmiast za cele, premia EXP po chwili; Miniony Maga/Druida/Nekromanty maja poziom wlasciciela, bez osobnego EXP i z regeneracja poza walka.",
    "v1.80.5: test CITY SERVICES zamyka polaczenie SQLite przed usunieciem pliku tymczasowego (Windows WinError 32).",
    "v1.80.4: naprawiono zgodnosc audytu XP z Windows i zwalnianie plikow SQLite po testach; tester zapisuje pelny log.",
    "v1.80.2: rozszerzono Fame do 6 celow w regionach z bossami, bez zmiany starych zaliczen i nagrod; fame cele i fame braki.",
    "v1.80.0: taktyka szturm/bastion/harmonia, 12 bossow Chaosu, reakcje zywiolow i mistrzostwo uzyj dla 14 klas. Wszystkie stare przywolania i leczenie nadal dzialaja.",
    "v1.70.10: Druidzie Life Oak od poziomu 150, Ancient Oak od poziomu 400; postep zwierzat i konstruktow, skalowanie HP, Nekromanta z nowymi straznikami i metalowymi konstruktami.",
    "v1.70.9: 10 biomow, 41 nowych przywolan zwierzecych, rzadkie od poziomu 100, legendarne od 300; wiewiorka tylko w lesie i na lace.",
    "v1.70.8: call list, call squirrel, call <zwierze>, order <zwierze> <rozkaz>; szyszki za mane od wiewiorki, bez Pieczeci Chowancow.",
    "v1.70.7: druid zbierz prawidlowo odczytuje poziom postaci i przyznaje szyszki bez AttributeError SB-5AD59274.",
    "v1.70.6: START uruchamia Pythona bez pozostawiania CMD; STOP czeka na zapis SQLite i zamkniecie launchera. Aktualizator chroni folder przed podmiana podczas pracy.",
    "v1.70.5: Windows host_windows.py prawidlowo odroznia SystemExit(0) przy STOP od awarii; bledy.log bez falszywych alarmow.",
    "v1.70.4: Historycznie fame pokazywało stan bieżącego terenu; od v1.80.7 tę rolę przejęło where fame / gdzie fame. Fame log i regiony zachowane.",
    "v1.70.3: Fame terenu, fame log i odroczony EXP dla poziomu, Duszy, Biegłości oraz statystyk (bez profesji). Po zalogowaniu przywołania trzeba wezwać na nowo.",
    "v1.70.2: Druid przywołuje drzewa za szyszki i manę; zbiór w lasach i wymiana starych nasion, Fame none/some/most/all z prawdziwych zabójstw bossów.",
    "v1.70.1: Dziewięć kolorów Kamieni Duszy, mana przywołań, wyrywania dusz i ulepszeń, scalanie, Rycerze Szkieletów i Licze.",
    "v1.70.0: Podniebne Królestwa, 9 bossów, Chowańce, Miasta Graczy, Rzemiosło 6.0, Wojny Legend, Klasy 4.0; nekromanta z zębami i Kamieniami Duszy, druid z Life Oak i Ancient Oak.",
    "v1.60.6: Windows: AKTUALIZUJ_Soulbound.bat, kopia bazy i kodu, bezpieczne STOP i aktualizacja z ZIP.",
    "v1.60.5: Naprawiono build Railway: do testow predeploy kopiowane sa pliki START/STOP Windows i po testach usuwane z obrazu Linux.",
    "v1.60.4: START_Soulbound.bat uruchamia serwer w tle bez otwartego okna CMD; STOP_Soulbound.bat zatrzymuje go bezpiecznie.",
    "v1.60.3: START_Soulbound.bat i STOP_Soulbound.bat; bezpieczne zamykanie z zapisem sesji przez lokalny uwierzytelniony kanal.",
    "Kopalnia: kop kierunki, kop 1..10 i kop <kierunek> wlaczaja stale auto-kopanie; kop off zatrzymuje.",
    "v1.60.2: aktualizacja wszystkich atlasów świata i 14 profesji, polskie znaki w help, limit 800 i nowe działy pomocy.",
    "v1.60.1: poprawiono walidacje lazy room Labiryntu Echa w pelnym audycie Railway; nie zmieniono gry ani zapisow.",
    "WIELKA ERA LEGEND: 4 podziemne krolestwa, osiem nowych bossow i podziemne sklepy.",
    "DROGA DO ORKOW: walk orki / orkowie / gor khaz prowadzi normalnym szlakiem z Rozdroza Czterech Wiatrow, bez Krypt 100.",
    "Wojny PvE: cztery fronty z powtarzalnymi misjami, rotujace co 4 godziny inwazje i 10 polowan na legendy.",
    "Ocean 5.0: osiem podwodnych lokacji, dwaj bossowie, trzy morskie bitwy flot i legendarne perly.",
    "Gildie i Twierdze 5.0: Sala Wojenna od poziomu 3 i Archiwum Reliktow od poziomu 6 istniejacej siedziby.",
    "Najemnicy 6.0: straznik moze automatycznie dodac oslone przeciw bossowi bez tracenia ataku.",
    "Komenda era60: orki, podziemia, wojny, twierdza, najemnicy, ocean, inwazje, lowcy.",
    "v1.50.0: cztery krainy, 160 lokacji, 20 bossow, 5 superbossow i 40-etapowa saga.",
    "Profesje 5.0: 42 nowe zlecenia dla 14 profesji i 24 nowe projekty wyposazenia.",
    "Labirynt Echa: nieskonczone pietra po piec komor, elita co 5, boss co 10; lokacje tworzone na zadanie.",
    "Komendy: kontynent, kontynent saga, kontynent profesje, kontynent bossowie, lochy50.",
    "v1.40.8: mocniejsze ale plynne wymagania EXP od poziomu 50; profesje i narzedzia x2 na 100, x4 na 200, x8 na 400, x25 na 799.",
    "Bieglosci, Dusza, skille i postac: x2 na 100, x4 na 200, x22 na 799. Statystyki osobno, lagodniej: x1.5 na 100, x2 na 200, x8 na 799.",
    "Wszystkie 6 statystyk ma wyzszy prog EXP od wartosci 50, nadal bez limitu. Wyplaty EXP i nagrody, drop, czasy akcji, poziomy i zapisany postep bez zmian.",
    "v1.40.6: duzo lepsze nagrody za zamowienia wszystkich 14 profesji oraz wielkie zamowienia krolestw; zwiekszono monety i XP kontraktowe.",
    "Wyplaty uwzgledniaja poziom, ilosc, trudnosc zlecenia i rynkowa wartosc surowcow; zachowano godzinne oferty i blokady ponownego odbioru.",
    "Aktywne zamowienia zachowuja obiecana kwote zapisana przy przyjeciu, nowe oferty maja wyzsze wyplaty. Bez zmian XP za zwykla prace, dropu i zapisow.",
    "v1.40.5: po flee lub wylogowaniu ranny mob poza walka odzyskuje co 15 sekund do 10 procent bazowego HP; nigdy podczas walki z innym graczem.",
    "v1.40.5: wyczysc naprawione POTWIERDZAM to bezpieczny skrot do czyszczenia oznaczonych bledow SB; nie wymazuje postaci.",
    "v1.40.5: zamowienie porzuc / zamówienie porzuć anuluje zamowienie profesji, bez zabierania materialow lub nagrod.",
    "Adaptacyjne HP bossow po zakonczeniu walki zachowuje procent ran zamiast natychmiastowego leczenia. Bez zmian EXP, dropu, walki aktywnej i zapisow.",
    "v1.40.4: poprawiono predeploy wewnatrz obrazu Docker: .dockerignore nie jest kopiowany do /app, wiec audyt sprawdza bezpieczny krok usuniecia generatora.",
    "Nowy test osobno sprawdza zrodla oraz obraz bez .dockerignore i odrzuca przywrocony generator lub brak zabezpieczenia. Bez zmian EXP, nagrod i postaci.",
    "v1.40.3: naprawa budowania Railway: Docker ignoruje i usuwa pozostaly core/generator_core.py przed kontrolami. Bez przywracania generatora.",
    "Wymagania EXP profesji i narzedzi od 50 mocniejsze jak w v1.40.8; wszystkie nagrody i zapisy bez zmian.",
    "v1.40.2: wszystkie 14 narzedzi ma plynnie wyzsze wymagania EXP od poziomu 100, identyczna krzywa jak profesje (150 x1.12, 200 x1.30, 400 x2.60, 600 x6, 799 x12).",
    "Kilof zachowuje swoj mnoznik x2. Nagrody EXP, wypracowane poziomy i XP, drop, oraz czas akcji bez zmian. Wedka nadal minimum 3 sekundy.",
    "v1.40.1: od poziomu profesji 100 zaczyna plynnie rosnac wymagany EXP: x1.12 przy 150, x1.30 przy 200, x2.60 przy 400, x6 przy 600, x12 przy 799.",
    "Nagrody EXP, juz zdobyte poziomy i XP, drop, ceny oraz czas narzedzi bez zmian; wedka nadal min. 3 s.",
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

from data.help_base_catalog_v405 import make_help_topic_aliases_v405
HELP_TOPIC_ALIASES = make_help_topic_aliases_v405()

from data.help_base_catalog_v405 import make_help_topics_v405
HELP_TOPICS = make_help_topics_v405()

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
    "zamowienia status - pokaż cel, postęp, zleceniodawcę i nagrodę; zamowienia oddaj - oddaj gotowe zamówienie u właściwego NPC; zamowienia porzuc albo zamówienie porzuć - anuluj bez utraty materiałów.",
    "zamowienia historia / zamowienia statystyki - trwała historia ukończeń per profesja, zarobek, XP profesji/narzędzia i rekord nagrody; stare ukończenia sprzed v0.61.4 zachowują tylko pewny licznik.",
    "Od v1.40.6 nagrody za nowe zamówienia rosną z poziomem, wielkością zamówienia i kosztem surowców; większe są zarówno waluta, jak i XP profesji oraz narzędzia. Już przyjęte zamówienia zachowują obiecaną nagrodę. Zamówienia nie dają Soul XP.",
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

# Soulbound v1.70.2: accessible command descriptions.
HELP_TOPICS['fame'] = [
    'fame — liczba zdobytych punktów Fame na całym świecie i stan celów z aktualnego katalogu.',
    'where fame / gdzie fame — status Fame bieżącego terenu: You have no/some/most/all fame in this area.',
    'none 0%, some 1–49%, most 50–99%, all 100%. Loch sumuje wszystkie piętra.',
    'fame log — zapis zabitych celów terenu; fame log wszystko — cały świat.',
    'fame cele / fame braki — cele obecnego terenu i to, co jeszcze pozostało.',
    'fame regiony — wszystkie tereny; fame none/some/most/all — filtr według stanu ukończenia.',
    'Fame jest zaliczana od razu do SQLite po pierwszym zabiciu; jedynie premia EXP może nadejść później.',
]

HELP_TOPICS['druid'] = [
    'call list — zwierzęta zależne od bieżącego terenu; call <nazwa> — przywołanie za manę bez Pieczęci Chowańców.',
    'call squirrel — tylko las i łąka, wiewiórka rzuca 2–4 szyszki i odchodzi, 20 MP, 90 s odnowienia.',
    'chowaniec przywolaj lifeoak — 2 szyszki + 80 MP; ancientoak — 5 szyszek + 180 MP.',
    'order <zwierzę|all> atakuj|bron|wspieraj|czekaj — wydawanie rozkazów.',
    'druid szyszki — zasoby; druid wymien — wymiana dawnych nasion; druid zbierz odsyła do call squirrel.',
    'Zwierzęta i dęby mają HP, mogą zginąć i wymagają ponownego wezwania po zalogowaniu.'
]
HELP_TOPICS['call'] = list(HELP_TOPICS['druid'])
HELP_TOPICS['order'] = list(HELP_TOPICS['druid'])

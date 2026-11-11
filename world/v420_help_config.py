# -*- coding: utf-8 -*-
"""Native historical helper extraction; unchanged function bodies."""
def configure_v0856_help_categories():
    """Przywraca ogólne tematy reklamowane przez główny help."""
    HELP_TOPIC_ALIASES.update({
        "professions": "profesje", "profession": "profesje",
        "inventory": "ekwipunek", "equipment": "ekwipunek", "eq": "ekwipunek",
        "mining": "gornictwo", "mine": "gornictwo",
        "woodcutting": "drwalstwo", "wood": "drwalstwo",
        "herbalism": "zielarstwo", "herbs": "zielarstwo",
        "alchemy": "alchemia", "crafting": "rzemioslo", "craft": "rzemioslo",
        "recipes": "receptury", "recipe": "receptury",
        "charisma": "charyzma", "haryzma": "charyzma",
        "party": "druzyny", "druzyna": "druzyny", "drużyna": "druzyny",
        "corpse": "zwloki", "zwloki": "zwloki", "zwłoki": "zwloki",
        "containers": "pojemniki", "container": "pojemniki",
        "shops": "sklepy", "shop": "sklepy", "sklep": "sklepy",
        "sprzedaj": "sklepy", "sell": "sklepy", "kup": "sklepy", "buy": "sklepy",
        "dostarcz": "questy", "deliver": "questy",
        "players": "gracze", "player": "gracze",
        "death": "smierc", "smierc": "smierc", "śmierć": "smierc",
        "races": "rasy", "race": "rasy",
        "abilities": "umiejetnosci", "skills": "umiejetnosci", "umiejętności": "umiejetnosci",
        "skillnames": "nazwy_skilli", "nazwyskilli": "nazwy_skilli",
        "teachers": "nauczyciele", "trainers": "nauczyciele",
        "atlas": "atlas",
    })
    HELP_TOPICS["profesje"] = [
        "Soulbound ma 8 profesji 1-600: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo i Jubilerstwo.",
        "Każda profesja ma własny level 1-600. Odpowiadające narzędzie ma osobną progresję 1-600 i służy do odblokowania lepszych surowców oraz bonusów jakości/urobku.",
        "profesje pokazuje szybki stan; profesje info pokazuje XP, rangi i dalszy rozwój.",
        "Narzędzia profesji rozwijają się do 600 i nie mają trwałości.",
        "Zasada v0.8.66: level profesji skraca czas pracy i blokuje receptury/zlecenia/poziomy lochów; level narzędzia odblokowuje lepsze zasoby i zwiększa bonus jakości/urobku.",
        "v0.9.9: przy rozmowie NPC profesyjny informuje o nowym zadaniu, komentuje powrót i stan n/x, a przy przyjęciu mówi osobną kwestię przed startem 0/x.",
        "v0.9.8: przy oddaniu questa NPC komentuje wykonanie i czytelnie wręcza nagrodę; questy profesyjne/rzemieślnicze zawsze mają także nagrodę w walucie.",
        "v0.9.7: NPC profesyjni rozpoznają twoją aktualną rangę. Rozmowa z Borysem, Torenem, Branem, Liorą, Marcelem, Orinem, Haldorem, Mirellą i mistrzami zbieractwa zmienia ton wraz z rangą; jest to wyłącznie prestiż/dialog.",
    ]
    HELP_TOPICS["ekwipunek"] = [
        "inventory / i pokazuje przedmioty w ekwipunku. eq / equipment pokazuje założone wyposażenie.",
        "Od v0.9.11 nowa postać NIE dostaje startowego EQ klasowego. Klasowe wyposażenie zdobywa się w sklepach i jako losowy drop z mobów.",
        "Każda z 14 klas ma 3 różne linie EQ na każdym progu Biegłości; alternatywne linie mają równy budżet mocy, więc wybór jest różnorodnością, nie power creepem.",
        "eq info pokazuje pełne bonusy, sety i sockety.",
        "Materiałowe EQ z ciał występuje jako żelazo, stal, mithril, adamantyt, kobalt, runiczne, smocza stal, astral, Pustka i eternium; konkretne statystyki i właściwości są losowane niezależnie od klasy.",
        "Zręczność z EQ realnie zwiększa szansę na krytyk; inne właściwości mogą wzmacniać obrażenia, obronę, unik, HP albo Manę.",
        "Klasowe EQ ma progi Biegłości 1, 10, 20 i dalej co 10 aż do 600.",
        "Postać może nosić dwa pierścienie i dwa talizmany.",
        "Sprzedawalne nieprzypisane duplikaty można wskazać numerem, np. sprzedaj 2.talizman korzeni.",
    ]
    HELP_TOPICS["atlas"] = [
        "atlas pokazuje gdzie i od jakiego levelu narzędzia odblokowują się ryby, drewno, zioła, rudy i inne surowce.",
        "Przykłady: atlas ryby, atlas drewno, atlas rudy, atlas <nazwa surowca>.",
        "Wpis konkretnego zasobu podaje region/lokację, wymagane narzędzie i minimalny level narzędzia. Szybkość pracy zależy od levelu właściwej profesji.",
    ]
    HELP_TOPICS["gornictwo"] = [
        "Górnictwo ma progresję 1-600; jego level skraca czas kopania do ustalonego minimum. Kilof rozwija się osobno 1-600 i odblokowuje lepsze rudy/żyły oraz bonus urobku.",
        "kop wykonuje pojedyncze wydobycie; kop on i kop off sterują auto-kopaniem.",
        "Od v1.25.1 możesz drążyć we wszystkich kierunkach: kop north, south, east, west, northeast, northwest, southeast, southwest, up, down.",
        "Polskie odpowiedniki: kop północ, południe, prawo, lewo, góra, dół. kop on north automatycznie drąży w tym kierunku; kop off zatrzymuje.",
        "Boczne chodniki są trwałe i przypisane do postaci; ich uderzenia i położenie zostają po restarcie na trwałym volume SQLite.",
        "Kopalnia Głębinowa nie ma końca; ściany mają losową liczbę uderzeń zapisywaną dla postaci. Zasobowa moc głębokości zatrzymuje się na progresji 400.",
        "kop on może wystartować już w ręcznej części Kryształowej Jaskini: automat sam dochodzi w dół do poziomu 1, a potem schodzi po każdym przebiciu ściany.",
        "Rudy progresji 220-600 wymagają jednocześnie odpowiedniego levelu Kilofa i co najmniej odpowiadającego mu poziomu Kopalni Głębinowej.",
        "Po odblokowaniu ruda pozostaje dostępna na wszystkich głębszych piętrach. Starsze rudy stają się rzadsze, ale nie znikają z puli.",
        "atlas rudy pokazuje wymagany level Kilofa i minimalną głębokość dla każdej rudy.",
        "kopalnia / mineinfo pokazuje bieżące piętro, najgłębszy odblokowany poziom, ścianę, auto-kopanie, Górnictwo, Kilof oraz najważniejsze dostępne rudy.",
    ]
    HELP_TOPICS["drwalstwo"] = [
        "Drwalstwo ma progresję 1-600; jego level skraca czas cięcia do ustalonego minimum. Piła rozwija się osobno 1-600 i odblokowuje lepsze drewno oraz bonus urobku.",
        "tnij wykonuje pojedynczą akcję; tnij on i tnij off sterują automatem.",
        "atlas drewno pokazuje wymagany level Piły i miejsca występowania drewna.",
    ]
    HELP_TOPICS["zielarstwo"] = [
        "Zielarstwo ma progresję 1-600; jego level skraca czas zbioru do ustalonego minimum. Sierp rozwija się osobno 1-600 i odblokowuje lepsze zioła oraz bonus urobku.",
        "zbieraj wykonuje pojedynczy zbiór; zbieraj on i zbieraj off sterują automatem.",
        "atlas zioła pokazuje wymagany level Sierpa i miejsca występowania ziół.",
    ]
    HELP_TOPICS["alchemia"] = [
        "Alchemia rozwija się 1-600; jej level skraca czas warzenia do ustalonego minimum i blokuje receptury/zlecenia. Moździerz rozwija się osobno 1-600 i zwiększa Tier/bonus produktu.",
        "alchemia / warz <receptura> tworzy mikstury, jeśli masz wymagany poziom i składniki.",
        "Questy Alchemii u Orina są niezależne; np. Mikstury Many i Mikstury Leczenia mogą być aktywne równocześnie.",
    ]
    HELP_TOPICS["rzemioslo"] = [
        "Crafting metalowy korzysta z Młota Rzemieślniczego 1-600, a jego wymagania i tempo wynikają z profesji Kowalstwo 1-600.",
        "craft / stworz / wytworz <receptura> tworzy przedmiot.",
        "Nie ma trwałości ani zużywania narzędzi.",
    ]
    HELP_TOPICS["receptury"] = [
        "receptury pokazuje dostępne przepisy.",
        "receptury craft, receptury cook, receptury alchemia i receptury jubilerstwo filtrują listę.",
        "Wymagania receptur pokazują level odpowiedniej profesji oraz wymagany Tier właściwego narzędzia. Oba warunki muszą być spełnione.",
    ]
    HELP_TOPICS["charyzma"] = [
        "Charyzma jest szóstą normalną statystyką postaci.",
        "Ma własny niezależny EXP i próg; sprzedaż przyznaje dodatkowy EXP Charyzmy zależny od wartości transakcji.",
        "Wpływa na rabat sklepowy i limit drużyny lidera.",
        "Komendy: charyzma, haryzma, charisma oraz staty info.",
    ]
    HELP_TOPICS["druzyny"] = [
        "załóż drużynę / zaloz druzyne tworzy drużynę. Samo druzyna / party pokazuje jej skład i status osłony.",
        "zaproś <gracz> / zapros <gracz> zaprasza gracza; działa też forma zaproś <gracz> do drużyny oraz druzyna zapros <gracz>.",
        "dołącz / dolacz przyjmuje zaproszenie, odrzuć / odrzuc je odrzuca, a opuść / opusc opuszcza drużynę.",
        "wyrzuć <gracz> / wyrzuc <gracz> usuwa członka. rozwiąż / rozwiaz rozwiązuje drużynę. Te dwie operacje wymagają lidera.",
        "lider <gracz> przekazuje wskazanemu członkowi dowodzenie drużyną.",
        "pc <tekst> to czat drużynowy. wspieraj / assist pomaga członkowi drużyny w jego aktualnej walce.",
        "zasłoń / zaslon albo zasłoń drużynę / zaslon druzyne włącza drużynową osłonę Strażnika. Aktywna klasa Strażnik przejmuje aggro wspólnego przeciwnika od całej drużyny w tej samej lokacji.",
        "zasłoń off / zaslon off wyłącza osłonę. Tank może chronić jeden wspólny cel walki naraz; nie przejmuje zdalnie obrażeń z innych lokacji ani innego równoległego moba.",
        "Guardy, pancerz, redukcja klasowa i Broń Duszy Strażnika działają normalnie na trafienia przejęte przez tankowanie.",
        "Limit drużyny rośnie z Charyzmą lidera.",
    ]
    HELP_TOPICS["zwloki"] = [
        "ciało / zwloki / corpse pokazuje numerowaną listę ciał mobów w aktualnej lokacji.",
        "Przy wielu ciałach użyj selektora 2.cialo / 2.corpse, 3.cialo / 3.corpse itd.",
        "l in corpse / l in 2.corpse / l w 2.cialo pokazuje zawartość bez zabierania.",
        "przeszukaj 2.cialo / loot 2.corpse zabiera całą zawartość konkretnego ciała. W drużynie każdy członek stojący razem przy ciele dostaje własną kopię znalezionych przedmiotów.",
        "get miecz from 2.corpse / wez miecz z 2.cialo zabiera jeden przedmiot; get all from 2.corpse zabiera wszystko. Pojedyncze zabranie także współdzieli ten przedmiot z obecną lokalnie drużyną.",
        "Każde ciało przeciwnika może mieć materiałowe EQ dobrane poziomem do siły moba: od żelaza i stali przez mithril i adamantyt aż po eternium. Konkretne statystyki i właściwości części są losowe.",
        "Elity, rzadkie moby i bossowie mogą zostawić dwie części materiałowego EQ, a ich dotychczasowy unikalny loot pozostaje osobno.",
    ]
    HELP_TOPICS["pojemniki"] = [
        "Siatka przechowuje ryby, Sakwa rudy, Stos drewna drewno, a Torba Zielarska zioła.",
        "put / wloz przenosi surowce profesyjne do ich pojemników; take / wyjmij wyciąga zasób.",
        "Szkatułka Rzemieślnicza działa automatycznie: sztabki, deski, materiały craftu i oszlifowane klejnoty jubilerskie wpadają do niej przy zdobyciu i nie wymagają ręcznego przenoszenia.",
        "Receptury automatycznie pobierają materiały ze Szkatułki; sell i sell all nigdy jej nie opróżniają.",
        "Bank Dusz jest osobnym trwałym magazynem konta.",
    ]
    HELP_TOPICS["level"] = [
        "level albo lvl pokazuje Level postaci 1-600, aktualny EXP oraz dokładnie ile EXP brakuje do następnego Levelu.",
        "Level postaci jest osobny od Soul Levelu Broni Duszy; dusza pokazuje progres Broni Duszy.",
    ]
    HELP_TOPICS["xp"] = [
        "xp pokazuje aktualny EXP postaci oraz dokładnie ile brakuje do następnego Levelu postaci.",
        "Na Levelu 600 komenda informuje o osiągniętym maksimum.",
    ]
    HELP_TOPICS["nawigacja_profesje"] = [
        "walk profesje albo prowadz profesje pokazuje wszystkie profesje i miejsca, do których warto iść: mistrzów, sklepy narzędzi, warsztaty i wejścia.",
        "walk profesje <profesja> prowadzi do głównego huba danej profesji, np. walk profesje alchemia.",
        "walk eq pokazuje sklepy z klasowym EQ; walk eq <klasa> prowadzi do właściwego kwatermistrza.",
    ]
    HELP_TOPIC_ALIASES.update({
        "level":"level", "lvl":"level", "xp":"xp",
        "walk profesje":"nawigacja_profesje", "prowadz profesje":"nawigacja_profesje",
        "walk eq":"nawigacja_profesje", "prowadz eq":"nawigacja_profesje",
    })
    HELP_TOPICS["sklepy"] = [
        "shop / sklep / list / lista pokazuje numerowaną ofertę aktualnego sprzedawcy.",
        "shop info <numer> / sklep info <numer> pokazuje pełny opis, statystyki, wymagania, cenę po rabacie i porównanie z założonym EQ przed zakupem.",
        "kup <nazwa> albo kup <numer> kupuje przedmiot; np. kup 9 lub kup 9 3.",
        "sprzedaj <nazwa> sprzedaje dokładnie jedną wolną sztukę przedmiotu z inventory.",
        "EQ możesz wskazać typem zamiast pełnej nazwy: sprzedaj helm, zbroja, rękawice, nogi, buty, pierścień, talizman albo naszyjnik.",
        "Jeśli do typu lub fragmentu pasuje kilka twoich przedmiotów, gra pokazuje numerowaną listę. Potem wpisz sprzedaj <numer>; nic nie jest wybierane losowo.",
        "Założone EQ i Character-Bound są zawsze chronione. Sprzedaż pojedyncza nigdy nie zdejmie ani nie sprzeda założonej sztuki.",
        "sprzedaj inventory sprzedaje hurtowo dozwolone wolne przedmioty. Zasoby profesji sprzedaje się u właściwych fachowców i można używać ich istniejących komend skupu.",
        "Charyzma wpływa na rabat zakupowy i rozwija się również przez sprzedaż.",
    ]
    HELP_TOPICS["gracze"] = [
        "who pokazuje graczy online.",
        "say <tekst> mówi do osób w tej samej lokacji; tell <gracz> <tekst> wysyła wiadomość prywatną.",
        "pc <tekst> wysyła wiadomość do drużyny.",
    ]
    HELP_TOPICS["smierc"] = [
        "Po śmierci postać odradza się w Świątyni Odrodzenia.",
        "Traci 10 procent każdego nominału wspólnego portfela zgodnie z obecną mechaniką śmierci.",
        "Postęp postaci, EQ, questy, Biegłość, Soul i profesje pozostają zapisane.",
    ]
    HELP_TOPICS["rasy"] = [
        "Gra ma 14 ras. Od v0.9.0 każda rasa ma dokładnie 50 bazowych punktów rozdzielonych między Siłę, Zręczność, Kondycję, Inteligencję i Siłę Woli; nie ma rasy z ukrytym większym budżetem startowym.",
        "Rasy różnią się rozkładem tych 50 punktów oraz własnym pasywem, więc nadal mają wyraźne specjalizacje.",
        "Każda z 14 klas dokłada dokładnie 9 własnych punktów startowych; startowa Charyzma bazowa wynosi 10 przed bonusem klasy.",
        "Kreator podaje polecane klasy dla każdej rasy, ale żadna kombinacja rasa-klasa nie jest blokowana.",
        "opis <rasa> pokazuje opis rasy oraz polecane klasy.",
    ]
    HELP_TOPICS["umiejetnosci"] = [
        "Każda z 14 klas ma Biegłość 1-600; istniejące progi odblokowania skilli 1-200 pozostają bez zmian.",
        "Progi umiejętności: 1, 10, 20, 30 i dalej co 10 aż do 600. Każdy próg ma 3 skille/spelle do nauczenia; alternatywy progu współdzielą cooldown wyboru.",
        "skills pokazuje umiejętności aktywnej klasy; kodeksklasowy <klasa> pokazuje pełną progresję.",
        "help <nazwa skilla> albo skill info <nazwa> pokazuje pełną pomoc konkretnej umiejętności.",
        "Soul Level nie odblokowuje skilli klasowych.",
    ]
    HELP_TOPICS["nazwy_skilli"] = [
        "skillnames / nazwyskilli pokazuje nazwy wszystkich skilli/spelli.",
        "help <nazwa skilla> działa dla wszystkich obecnych skilli/spelli, także klas nieaktywnych.",
    ]
    HELP_TOPICS["nauczyciele"] = [
        "teachers / nauczyciele pokazuje nauczycieli klasowych.",
        "Samo learn / naucz / ucz przy nauczycielu aktywnej klasy pokazuje tylko odblokowane i jeszcze nienauczone umiejętności oraz ich ceny.",
        "learn <numer> i learn <nazwa> ucza wybranej umiejetnosci; poza sala nauczyciela nauka nie jest mozliwa.",
        "Numery learn sa identyczne jak numery skilli w talk <nauczyciel> i nie zmieniaja sie po nauce. Pelny katalog: kodeksklasowy.",
        "Koszt nauki może być obniżany przez reputację Gildii klasowej.",
    ]
    HELP_TOPICS["learn"] = list(HELP_TOPICS["nauczyciele"])


def configure_v0856_help_refresh():
    """Aktualizuje podstawowe pomoce do rzeczywistego stanu v0.8.56."""
    HELP_TOPIC_ALIASES.update({
        "staty": "statystyki", "status": "statystyki", "stats": "statystyki", "stat": "statystyki",
        "hp": "hp", "health": "hp", "zdrowie": "hp", "zycie": "hp", "życie": "hp",
        "score": "score", "wynik": "score", "postac": "score", "postać": "score",
        "dusza": "dusza", "soul": "dusza", "soul info": "dusza",
        "quest": "questy", "quests": "questy", "zadania": "questy",
    })

    HELP_TOPICS["podstawy"] = [
        "Soulbound nie ma levelu postaci. Rozwój odbywa się przez statystyki, Biegłość klas, Soul Level Broni Duszy, EQ i profesje.",
        "Najważniejsze komendy startowe: look, exits, hp, score, staty, dusza, eq, quest, portfel i help.",
        "k <mob> rozpoczyna walkę realtime z dowolnym zabijalnym mobem; con <mob> ocenia go bez walki.",
        "quit zapisuje bieżącą postać i wraca do menu wyboru postaci na tym samym koncie.",
        "help staty, help hp, help score, help dusza i help quest opisują najważniejsze systemy.",
    ]
    HELP_TOPICS["statystyki"] = [
        "staty pokazuje każdą statystykę w osobnym komunikacie NVDA, a potem HP, Manę, obronę i ofensywę.",
        "staty info pokazuje osobno bazę, wartość efektywną oraz bonus EQ/klejnotów dla każdej statystyki.",
        "Sześć statystyk: Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma.",
        "Każda z sześciu statystyk ma własny licznik EXP i własny próg. Od v0.19 próg wylicza Global Progression Generator: początek jest szybki, a wymagania rosną mocniej wraz z wartością statystyki. Zdobycie pełnego progu zwiększa tylko tę konkretną statystykę o 1.",
        "Kondycja zwiększa HP każdej klasy. Inteligencja zwiększa Manę każdej klasy.",
        "Zręczność wpływa na szybkość, unik i krytyki. Siła zwiększa fizyczne obrażenia i częściowo skaluje magiczne skille/spelle.",
        "Nie ma ręcznego rozdawania punktów i nie ma levelu postaci.",
    ]
    HELP_TOPICS["hp"] = [
        "hp / zdrowie pokazuje bieżące HP, maksymalne HP, bieżącą Manę i maksymalną Manę.",
        "Wartości są czytane osobno, żeby NVDA nie łączył całego stanu w jeden długi komunikat.",
        "Maksymalne HP wynika głównie z Kondycji, rasy, klasy, EQ i bonusów. Maksymalna Mana wynika głównie z Inteligencji oraz bonusów.",
    ]
    HELP_TOPICS["score"] = [
        "score / wynik to zwarte podsumowanie aktualnej postaci.",
        "Pokazuje rasę, główną i aktywne klasy, Biegłość każdej klasy, Soul Level/Tier i Soul Weapon Mastery, HP, Manę i sześć statystyk.",
        "Pokazuje też wspólny portfel konta, aktualną lokację/strefę oraz dynamiczną ocenę terenu.",
        "score i expowiska pokazują orientacyjną ocenę terenu w historycznej skali 1-600; con i dynamiczny EXP walki używają osobnej bieżącej skali siły 1-600. Żadna z tych ocen nie jest levelem postaci.",
    ]
    HELP_TOPICS["dusza"] = [
        "dusza pokazuje krótki stan Broni Duszy: Soul Level, Tier, Soul XP, moc i następny cel.",
        "dusza info pokazuje pełne progi Tierów 1-40 oraz stan Prób Broni Duszy potrzebnych do dalszej progresji.",
        "Kolejne Tiery do 80 wymagają odpowiedniego Soul Levelu i właściwego odblokowania; progi 1-200 zachowują wcześniejsze Próby, a 201-800 kontynuują progresję endgame.",
        "Soul Level ma zakres 1-600 i rozwija Broń Duszy; nie jest levelem postaci. Soul Weapon Mastery ma osobny zakres 1-600 i rozwija wyłącznie zwykły atak broni.",
        "Skille/spelle klasowe zachowują stare progi odblokowania do 200, a Biegłość właściwej klasy rozwija się 1-600, nie Soul Level.",
        "Po osiągnięciu progu wpisz quest list Kapłan Elor, przyjmij właściwą Próbę, wykonaj cel, oddaj quest i użyj unlock.",
    ]

    HELP_TOPICS["aoe"] = [
        "Czary i skille obszarowe trafiają wszystkie dostępne cele zgodnie z opisem konkretnej umiejętności.",
        "Historyczne progi Soul zostały zastąpione Biegłością klasy: np. umiejętność z progu 40 wymaga Biegłości 40 danej klasy.",
        "Skille odblokowuje Biegłość właściwej klasy w całym zakresie 1-600: klasyczne progi pozostają do 200, a dalsze odblokowania są w zakresie 220-600.",
        "Pełne szczegóły konkretnego AoE: help <nazwa skilla> albo skill info <nazwa>.",
        "Akcja obszarowa działa w walce realtime i nie tworzy osobnej tury przeciwnika.",
    ]
    HELP_TOPICS["naturalne_naucz"] = [
        "U nauczyciela aktywnej klasy możesz uczyć się skilli naturalną nazwą kategorii.",
        "naucz leczenie, naucz tarcza, naucz unik, naucz drain i naucz dobij wybierają pasujący dostępny skill.",
        "Ofensywne przykłady: naucz ciecie, naucz pocisk, naucz ogien, naucz burza, naucz mlot, naucz strzal.",
        "System bierze pod uwagę tylko skille klasy nauczyciela, przy którym aktualnie stoisz.",
        "Najpierw preferuje skill, którego jeszcze nie znasz, a potem najwyższy dostępny próg Biegłości klasy.",
        "Pełne nazwy i numery skilli nadal działają.",
    ]
    HELP_TOPICS["rozwoj_statystyk"] = list(HELP_TOPICS["statystyki"])
    HELP_TOPICS["soul200"] = [
        "Broń Duszy ma Soul Level 1-600 i 60 Tierów.",
        "Każdy Tier 2-20 ma własną jednorazową Próbę u Kapłana Elora.",
        "Po osiągnięciu wymaganego Soul Levelu wykonaj Próbę, oddaj ją i wpisz unlock.",
        "Soul Level zwiększa moc Broni Duszy i nie odblokowuje skilli klasowych.",
        "Skille klasowe odblokowuje Biegłość klasy 1-600; stare progi 1-200 pozostają w tych samych miejscach, a dalsza linia działa do 600.",
        "Nie ma levelu postaci.",
    ]
    HELP_TOPICS["soul_tier45_krypta200"] = [
        "Broń Duszy ma 20 Tierów na Soul Levelach: 1, 10, 20, 25, 35, 45, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180 i 200.",
        "Każdy Tier 2-20 wymaga własnej jednorazowej Próby Broni Duszy u Kapłana Elora.",
        "Po progu użyj quest list Kapłan Elor, wykonaj Próbę, oddaj zadanie i wpisz unlock.",
        "dusza info pokazuje stan wszystkich 39 Prób (Tier 2-40), ich pasmo trudności oraz następny cel.",
        "Nie ma resetu Soul Levelu, Soul XP ani historycznie ukończonych prób.",
    ]

    if "informacje" in HELP_TOPICS:
        HELP_TOPICS["informacje"] = [
            "Najważniejsze komendy informacyjne są rozdzielone na krótkie i pełne wersje pod NVDA.",
            "hp - bieżące i maksymalne HP oraz Mana, osobno.",
            "score - ogólne podsumowanie postaci i progresji.",
            "staty - każda statystyka osobno; staty info - baza, wartość efektywna, EQ i mechanika.",
            "dusza - szybki stan Broni Duszy; dusza info - Tiery 1-40, wymagania i następny cel.",
            "profesje / profesje info - stan i pełne informacje profesji.",
            "narzedzia / narzedzia info - stan i pełne informacje narzędzi.",
            "eq / eq info - założone EQ oraz pełne bonusy, sockety i sety.",
            "kodeksklasowy <klasa> - skille odblokowywane Biegłością klasy, nauczyciel, cena i status.",
            "help informacje - ten przewodnik.",
        ]


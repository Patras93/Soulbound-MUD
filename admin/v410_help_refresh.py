# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def refresh_generator_help_v0271():
    HELP_TOPICS["podstawy"] = [
        "Soulbound v0.27.1 używa dawny Generator Core jako jedynego źródła aktywnego balansu.",
        "Level postaci, Biegłość, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia mają zakres 1-400. Sześć statystyk bazowych nie ma twardego limitu.",
        "Najważniejsze komendy startowe: look, exits, hp, score, staty, dusza, eq, quest, atlas i help.",
        "k <mob> rozpoczyna walkę realtime; con <mob> pokazuje wygenerowaną ocenę przeciwnika bez walki.",
        "Nowa zawartość dziedziczy liczby z dawny Generator Core zamiast wymagać ręcznego balansowania.",
    ]
    HELP_TOPICS["score"] = [
        "score pokazuje Level postaci i EXP, aktywne klasy i Biegłość, Soul Level/Tier i Soul Weapon Mastery, HP, Manę, statystyki, portfel i lokację.",
        "Ocena siły postaci i terenu działa w tej samej skali dawny Generator Core 1-400.",
        "Wartości terenu wynikają z wygenerowanych lokacji i realnych spawnów, a nie ze starej ręcznej tabeli.",
    ]
    HELP_TOPICS["statystyki"] = [
        "Sześć automatycznych statystyk to Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma.",
        "Statystyki nie mają twardego limitu. Każda ma własny EXP i wygenerowany próg rosnący także powyżej 400; nie rozdzielasz punktów ręcznie.",
        "v1.13.42: każde źródło stat EXP nadal dostaje globalnie x4 przed bonusem rasy i Gildii, ale wymagany EXP do kolejnego punktu ma teraz mnożnik x4 dla długoterminowej progresji.",
        "Dla równorzędnego zwykłego źródła generator celuje teraz efektywnie w około 60 akcji na kolejny punkt każdej statystyki; rare, minibossy, bossy, questy i x2 EXP nadal przyspieszają postęp.",
        "Powyżej 400 dawny Generator Core skaluje wymagany EXP i nagrodę statystyczną z zachowaniem jakości źródła: endgame pozostaje opłacalny, a słabe moby nie stają się dobrym farmem.",
        "Level postaci, wyposażenie, rasa, klasa i statystyki wspólnie wpływają na parametry bojowe.",
        "staty info pokazuje bazę, wartość efektywną, bieżący EXP do następnego punktu i bonusy wyposażenia.",
    ]
    HELP_TOPICS["dusza"] = [
        f"Broń Duszy ma Soul Level 1-{SOUL_MAX_LEVEL} i {SOUL_MAX_TIER} Tierów.",
        "Progi Tierów, moc, bonusy i wymagania Prób są generowane z jednej krzywej dawny Generator Core.",
        "Soul Level jest osobną osią od Levelu postaci, Biegłości klasy i Skill Levelu. Soul Weapon Mastery 1-400 rozwija wyłącznie zwykły atak Broni Duszy i zdobywa XP tylko za jego trafienia.",
        "dusza info pokazuje aktualne progi i stan Prób; po spełnieniu warunków użyj unlock.",
    ]
    HELP_TOPICS["aoe"] = [
        "Skille i spelle obszarowe trafiają dostępne cele zgodnie z wygenerowanym rodzajem umiejętności.",
        "Odblokowanie 1-400, cooldown i bazowa moc pochodzą z dawny Generator Core. Koszt Many dotyczy wyłącznie umiejętności klas magicznych; klasy fizyczne nie zużywają Many.",
        "Własny Skill Level 1-400 dalej skaluje końcową moc umiejętności po jej odblokowaniu.",
        "Pełne aktualne wartości: help <nazwa skilla> albo skill info <nazwa>.",
    ]
    HELP_TOPICS["umiejetnosci"] = [
        "Każda z 14 klas ma wygenerowaną linię skilli/spelli rozłożoną po Biegłości 1-400.",
        "Skill Level każdej poznanej umiejętności ma zakres 1-400 i korzysta z jednej wygenerowanej krzywej mocy/cooldownu.",
        "Damage, heal, guard, drain, boost i cooldown są wyliczane przez dawny Generator Core z rodzaju i etapu umiejętności. Mana jest zasobem klas magicznych; skille klas fizycznych mają koszt Many równy 0.",
    ]
    HELP_TOPICS["profesje"] = [
        "Osiem profesji oraz osiem odpowiadających narzędzi rozwijają się 1-400.",
        "EXP, progi, czasy akcji, zasoby, ich odblokowania, ceny i receptury pochodzą z dawny Generator Core.",
        "Nowy zasób albo receptura po dodaniu do rejestru otrzymuje etap z powiązań i wygenerowane wymagania; nie wymaga ręcznej liczby levelu.",
        "Narzędzia nie mają trwałości i nie psują się.",
    ]
    HELP_TOPICS["tempo_profesji"] = [
        "Czas każdej aktywności profesyjnej jest generowany z typu narzędzia i poziomu profesji 1-400.",
        "Nie istnieje osobna ręcznie ustawiona dawna krzywa; jeden wzór obsługuje całą progresję.",
        "Komendy informacji o narzędziu pokazują aktualny czas wyliczony przez dawny Generator Core.",
    ]
    HELP_TOPICS["narzedzia200"] = [
        "Narzędzia mają zakres 1-400, a ich Tiery są rozłożone automatycznie przez dawny Generator Core.",
        "Tool XP, progi Tierów i bonusy nie wymagają osobnej tabeli dla każdego levelu.",
        "Narzędzia nie mają durability.",
    ]
    HELP_TOPICS["wiecej_ryb"] = [
        "Gatunki ryb są rozłożone przez dawny Generator Core po progresji Wędki 1-400.",
        "atlas ryby pokazuje bieżący wygenerowany próg każdego gatunku; łowisko wykorzystuje tę samą wartość.",
        "Dodanie nowego gatunku nie wymaga ręcznego ustawiania ceny ani progu.",
    ]
    HELP_TOPICS["hp_mobow"] = [
        "HP i obrażenia każdego moba i bossa są generowane z etapu 1-400, rangi i miejsca w świecie.",
        "Ta sama zasada obejmuje świat, Kryptę, Wieżę Astralną, lochy mityczne, profesyjne i nieskończone piętra.",
        "Ręczne stare HP/damage nie jest źródłem aktywnego balansu.",
    ]
    HELP_TOPICS["soul_xp_bloki"] = [
        "Soul XP 1-400 korzysta z jednej krzywej dawny Generator Core.",
        "Nagroda i wymagany próg są wyliczane z aktualnego etapu; nie ma osobnego historycznego bloku dawnych poziomów.",
    ]
    HELP_TOPICS["progresja400"] = [
        "Level postaci, Biegłość, Soul, Skill Level, profesje i narzędzia korzystają z progresji 1-400; sześć statystyk bazowych rozwija się bez twardego limitu, ale ich bazowy profil rasa+klasa nie jest generowany.",
        "Moby, questy, przedmioty, receptury i zasoby dziedziczą etap z grafu świata i relacji między treścią.",
        "Balance Validator sprawdza komplet rejestrów po zbudowaniu gry.",
    ]
    HELP_TOPICS["questy_kowalstwa_1_200"] = [
        "Zlecenia Kowalstwa korzystają z wygenerowanego etapu wymaganych materiałów i produktów.",
        "Wymagany poziom, Profession XP, Tool XP, Character XP i pieniądze są liczone przez dawny Generator Core.",
    ]
    HELP_TOPICS["questy_gotowania_1_200"] = [
        "Zlecenia Gotowania korzystają z wygenerowanego etapu potraw i składników 1-400.",
        "Wymagania i nagrody są pobierane z dawny Generator Core, nie z dawnej ręcznej drabinki.",
    ]
    HELP_TOPICS["questy_mikstur_orina"] = [
        "Zlecenia Alchemii korzystają z wygenerowanego etapu mikstur i składników 1-400.",
        "Wymagania i nagrody są pobierane z dawny Generator Core.",
    ]
    for topic in ("balans 0865", "balans 0866", "balans 0874"):
        if topic in HELP_TOPICS:
            HELP_TOPICS[topic] = [
                "To historyczny opis dawnego wydania i nie opisuje aktywnego balansu v0.27.1.",
                "Aktualny balans pochodzi z dawny Generator Core; główne osie mają zakres 1-400, a statystyki są nielimitowane. Wpisz help generator.",
            ]
    HELP_TOPICS["atlas_kompletny"] = [
        "Atlasy ryb, rud, drewna i ziół pokazują ręcznie zaprojektowane progi; dawny Generator Core ich nie nadpisuje.",
        "Zmiana balansu liczbowego generatora nie zmienia wymagań ani kolejności odblokowania zasobów.",
        "Użyj atlas ryby, atlas rudy, atlas drewno albo atlas ziola; szczegóły zasobu pokazują jego aktualny wygenerowany próg.",
    ]
    archaeology = HELP_TOPICS.get("archeologia", [])
    if isinstance(archaeology, str):
        archaeology = [archaeology]
    archaeology.append(
        "v1.13.8: znaleziska mają etapową wartość sprzedaży; nowy wpis kolekcji daje x2 Profession XP i zwiększony Tool XP."
    )
    HELP_TOPICS["archeologia"] = archaeology

    cartography = HELP_TOPICS.get("kartografia", [])
    if isinstance(cartography, str):
        cartography = [cartography]
    cartography.append(
        "v1.13.8: pierwszy pomiar nowej lokacji daje jednorazową premię odkrywcy zależną od etapu terenu; ponowne pomiary rozwijają profesję bez ponownego bonusu."
    )
    HELP_TOPICS["kartografia"] = cartography

    HELP_TOPICS["generator"] = [
        "Od v1.28.4 Generator Core został całkowicie usunięty.",
        f"Aktualny katalog danych jest tylko walidowany: {CATALOG_VALIDATION_AUDIT['mobs']} mobów, {CATALOG_VALIDATION_AUDIT['items']} przedmiotów, {CATALOG_VALIDATION_AUDIT['quests']} zadań, {CATALOG_VALIDATION_AUDIT['skills']} skilli.",
        "Wzory balansu są w osobnych modułach; nie nadpisują katalogów skilli, EQ ani questów.",
        "Statystyki bez limitu, poziomy postaci i rozwoju do 800.",
    ]

    HELP_TOPICS["hp_bossow_lochow"] = [
        "Bossowie lochów nie korzystają już z ręcznego wzoru HP na piętro.",
        "Krzywe balansu wyznaczają etap z piętra/rodzaju lochu, a następnie liczy HP, damage, EXP i walutę z rangi bossa oraz wspólnej krzywej 1-400.",
        "Nieskończone piętra powyżej zakresu progresji są bezpiecznie domykane do etapu 400 zamiast tworzyć niekontrolowany power creep.",
        "consider pokazuje aktualne wartości wygenerowane przez ten sam system.",
    ]
    HELP_TOPICS["quest"] = [
        "quest pokazuje aktywny dziennik; quest list <NPC> pokazuje ofertę, quest accept <numer> przyjmuje zadanie, quest info pokazuje szczegóły, a oddaj quest kończy gotowe zadanie.",
        "dawny Generator Core nie tworzy ani nie zmienia wymagań questów. Globalnej blokady Character Level na questy nie ma; obowiązują tylko ręcznie zaprojektowane wymagania danego zadania.",
        "Każdy nowo przyjęty cel zaczyna od 0/x i liczy wyłącznie zdarzenia wykonane po przyjęciu.",
        "Po wykonaniu celu dziennik pokazuje: ZAKTUALIZOWANO — GOTOWE DO ODDANIA.",
        "EXP, Soul XP, Stat XP, Profession/Tool XP i pieniądze z questów są liczone przez dawny Generator Core z etapu i nakładu pracy.",
    ]
    HELP_TOPICS["receptury"] = [
        "receptury pokazuje wygenerowane przepisy; receptury craft, cook, alchemia i jubilerstwo filtrują listę.",
        "Progi profesji/narzędzia, składniki, ilości i produkty receptur są ręcznie zaprojektowane i dawny Generator Core ich nie zmienia.",
        "Generator wylicza tylko liczbowy balans receptury, np. Profession XP, Tool XP i wewnętrzny generator_level używany do balansu.",
    ]
    HELP_TOPICS["sklepy"] = [
        "shop / sklep / list / lista pokazuje numerowaną ofertę: numer, nazwa i aktualna wygenerowana cena.",
        "shop info <numer> / sklep info <numer> pokazuje pełny opis, statystyki, wymagania, cenę po rabacie oraz porównanie z aktualnie założonym EQ przed zakupem.",
        "kup <numer> lub kup <numer> <ilość> kupuje pozycję z listy; nadal można kupować także po nazwie.",
        "Ceny przedmiotów pochodzą z dawny Generator Core i są liczone w jednej bazowej walucie; nowe przedmioty nie wymagają ręcznego wpisywania ceny.",
        "Założone EQ i Character-Bound pozostają chronione przy sprzedaży.",
    ]
    HELP_TOPICS["atlas"] = [
        "atlas pokazuje ręcznie zaprojektowane progi ryb, rud, drewna, ziół i innych zasobów.",
        "dawny Generator Core może balansować wartości ekonomiczne i wydajność zasobów, ale nie zmienia progów atlasu ani miejsc odblokowania.",
    ]


def refresh_help_v03010():
    HELP_TOPIC_ALIASES.update({
        "wimpy": "wimpy",
        "auto ucieczka": "wimpy",
        "event exp": "event_exp",
        "eventxp": "event_exp",
        "xpevent": "event_exp",
        "x2 exp": "event_exp",
        "podwojny exp": "event_exp",
        "podwójny exp": "event_exp",
    })
    quest_help = [
        "quest pokazuje aktywny dziennik; quest list <NPC> pokazuje ofertę, quest accept <numer> przyjmuje zadanie, quest info pokazuje szczegóły, a oddaj quest kończy gotowe zadanie.",
        "Questy NIE mają globalnej blokady Levelu postaci. Możesz przyjąć zadanie niezależnie od Character Levelu, o ile spełniasz jego rzeczywiste wymagania fabularne, Soul lub profesyjne.",
        "Każdy nowo przyjęty cel zaczyna od 0/x i liczy wyłącznie zdarzenia wykonane po przyjęciu.",
        "Po wykonaniu celu dziennik oznacza zadanie jako GOTOWE DO ODDANIA; zadania zbierackie pokazują też realny stan wymaganych przedmiotów.",
        "Nagrody EXP, Soul, statystyk, profesji i narzędzi korzystają z dawny Generator Core; podczas eventu x2 EXP są podwajane.",
    ]
    HELP_TOPICS["quest"] = list(quest_help)
    HELP_TOPICS["questy"] = list(quest_help)
    HELP_TOPICS["wimpy"] = [
        "wimpy pokazuje aktualne ustawienie automatycznej ucieczki.",
        "wimpy set 50 ustawia ucieczkę przy 50 procent HP lub mniej. Dozwolone wartości: 1-99.",
        "wimpy off albo wimpy 0 wyłącza automatyczną ucieczkę.",
        "WIMPY sprawdza próg po otrzymaniu nieśmiertelnego trafienia; jeśli trafienie zabije postać, śmierć ma pierwszeństwo.",
    ]
    HELP_TOPICS["event_exp"] = [
        "Event x2 EXP uruchamia się na początku każdej pełnej godziny i trwa 15 minut.",
        "Podwaja Character XP, Class XP, Soul XP, Skill XP, EXP sześciu statystyk oraz EXP profesji i narzędzi.",
        "eventxp, xpevent albo wydarzenia pokazuje bieżący status i czas do zmiany.",
        "Start i koniec eventu są ogłaszane wszystkim zalogowanym graczom.",
    ]
    HELP_TOPICS["nawigacja"] = [
        "prowadz <cel> / walk <cel> automatycznie idzie dokładnie do rozpoznanej lokalizacji lub NPC; prowadz stop przerywa marsz, prowadz status pokazuje stan.",
        "exits / ex czyta każdy dostępny kierunek razem z nazwą lokacji, do której prowadzi; exits info dodaje strefę i zagrożenie.",
        "walk krypta dół działa wewnątrz zwykłej Krypty i prowadzi przez bieżące piętro przed zejście na kolejne. Samo zejście wykonujesz ręcznie.",
        "Sam znak / i Enter przerywa aktywności i teleportuje do Świątyni Odrodzenia. Jeśli jesteś w drużynie, teleport obejmuje tylko członków stojących razem z tobą w tej samej lokacji.",
        "prowadz lista / walk list pokazuje kategorie celów; trasa <cel> planuje drogę bez wykonywania ruchu.",
    ]
    HELP_TOPICS["przetop"] = [
        "przetop <metal> rozpoczyna pojedyncze przetapianie w Kuźni.",
        "przetop max <metal> wykonuje kolejne przetopy aż do wyczerpania dostępnego materiału; przetop wszystko wykonuje hurtowy plan dla wszystkich dostępnych metali.",
        "przetop status pokazuje, czy przetapianie jest aktywne.",
        "przetop stop zatrzymuje aktywne przetapianie. Jeżeli trwa jeszcze czas oczekiwania, zatrzymanie następuje przed pobraniem materiałów; jeśli wynik jest już zapisywany, bieżący przetop kończy się bezpiecznie i kolejny nie startuje.",
        "Podczas aktywnego przetapiania inne akcje są blokowane, aby postać nie opuściła Kuźni w połowie operacji.",
    ]

    regen_help = [
        "Poza walką postać naturalnie regeneruje HP i Manę podczas stania: 2 procent wartości maksymalnej co 5 sekund.",
        "Komenda rest / odpoczywaj uruchamia szybszą regenerację: 10 procent maksymalnego HP i Many co 5 sekund, czyli pięć razy szybciej niż zwykłe stanie.",
        "Naturalny regen stojąc jest cichy dla NVDA i zatrzymuje się podczas walki, ruchu, prowadzenia oraz automatycznego zbierania.",
        "Nullify Healing i inne blokady leczenia zatrzymują odzyskiwanie HP, ale nie blokują naturalnej regeneracji Many.",
        "rest status pokazuje bieżące HP, Manę i tempo regeneracji.",
    ]
    HELP_TOPICS["odpoczynek"] = list(regen_help)
    HELP_TOPICS["rest"] = list(regen_help)
    HELP_TOPICS["regen"] = list(regen_help)

    HELP_TOPICS["walka"] = [
        "k <mob> / atakuj <mob> rozpoczyna walkę realtime. uciekaj / flee ręcznie wycofuje z walki.",
        "wimpy set <1-99> ustawia automatyczną ucieczkę przy wybranym procencie HP; wimpy off wyłącza.",
        "combatlog concise, normal albo full ustawia szczegółowość komunikatów walki dla NVDA.",
        "Skille, kolejki, buffy, guardy, uniki, krytyki, drużyna i dawny Generator Core działają na bieżących danych postaci.",
    ]
    HELP_TOPICS["podstawy"] = [
        "Soulbound v0.30.11 używa dawny Generator Core jako źródła aktywnego balansu; bazowe statystyki rasy i klasy pozostają stałe i nie są losowane przez generator.",
        "Level postaci, Biegłość, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia mają progresję 1-400; sześć statystyk bazowych rozwija się automatycznie.",
        "Najważniejsze komendy: help, look/l/sp, exits, hp, level/lvl, xp, score, staty, dusza, eq, quest, walk/prowadz oraz / do Świątyni.",
        "k <mob> rozpoczyna walkę; con <mob> ocenia przeciwnika; wimpy set 50 może automatycznie wycofać postać przy niskim HP.",
        "eventxp pokazuje godzinny event x2 EXP. Samo help zawsze otwiera menu kategorii.",
    ]
    HELP_TOPICS["krypta"] = [
        "Zwykła Krypta ma rozgałęzione piętra i bossów blokujących zejście na wybranych poziomach.",
        "walk krypta dół prowadzi z dowolnego pokoju bieżącego piętra przed zejście na następne piętro. Samo zejście wykonujesz ręcznie.",
        "portal pokazuje odblokowane checkpointy Krypty; mapa w instancji pokazuje odkrycie bieżącego sektora.",
        "Krypta korzysta z dawny Generator Core i może tworzyć dalsze piętra dynamicznie.",
    ]

    # Usuń z dostępnych tematów pomocy najbardziej szkodliwe historyczne zdania,
    # które twierdziły, że Character Level nie istnieje lub że prowadzenie zawsze
    # kończy się przed celem/piętrem. Historyczne audyty w plikach wydania zostają.
    stale_fragments = (
        "nie ma levelu postaci",
        "nadal nie ma levelu postaci",
        "prowadzenie kończy się przed wejściem",
        "prowadzenie zatrzymuje się jeden krok przed celem",
        "prowadz krypta prowadzi tylko przed wejście do krypty",
        "każdy quest ma generowany wymagany level postaci",
    )
    for topic, lines in list(HELP_TOPICS.items()):
        cleaned = []
        for line in lines:
            low = normalize_lookup_text(str(line))
            if any(fragment in low for fragment in stale_fragments):
                continue
            cleaned.append(line)
        HELP_TOPICS[topic] = cleaned


def refresh_help_v03011():
    global LATEST_CHANGES_TITLE, LATEST_CHANGES
    LATEST_CHANGES_TITLE = "Soulbound v0.30.11 - Party Follow, History Buffers & Player Trading"
    LATEST_CHANGES = [
        "Członkowie drużyny stojący z liderem automatycznie podążają za jego zwykłym ruchem i prowadzeniem; indywidualne blokady nadal obowiązują.",
        "Dodano sesyjne bufory historii XP, lootu, questów, systemu, czatu lokalnego, drużyny, PM i walki.",
        "Komenda daj/przekaż obsługuje zwykłe przedmioty inventory, ilości oraz walutę między graczami w tej samej lokacji.",
        "Character-Bound narzędzia, przedmioty questowe i założone EQ nie mogą być przekazywane.",
        "Pełny indeks HELP został zaktualizowany o follow, bufory, przekazywanie przedmiotów i waluty oraz aktualne aliasy.",
    ]

    HELP_TOPIC_ALIASES.update({
        "bufor":"bufory", "bufory":"bufory", "history buffer":"bufory",
        "historia xp":"bufory", "historia loot":"bufory", "historia quest":"bufory",
        "przekaz":"przekazywanie", "przekaż":"przekazywanie",
        "daj":"przekazywanie", "give":"przekazywanie", "trading":"przekazywanie",
        "handel graczy":"przekazywanie", "przekazywanie":"przekazywanie",
        "follow":"druzyny", "podazanie":"druzyny", "podążanie":"druzyny",
    })

    HELP_TOPICS["bufory"] = [
        "Bufory historii są sesyjne i przechowują po 100 ostatnich wpisów na kategorię, bez potrzeby przewijania terminala/NVDA.",
        "bufor xp, loot, quest, system, chat, party, tell albo walka pokazuje domyślnie 20 ostatnich wpisów; np. bufor xp 50 pokazuje 50.",
        "bufor all pokazuje wspólną chronologiczną historię wszystkich kategorii.",
        "historia xp, historia loot i historia quest są skrótami do tych samych buforów; samo historia nadal pokazuje trwałe statystyki życia postaci.",
        "bufor wyczysc <kategoria> albo bufor wyczysc all czyści wyłącznie pamięć bieżącej sesji i nie usuwa trwałych danych postaci.",
    ]
    HELP_TOPICS["przekazywanie"] = [
        "daj <gracz> <pełna nazwa przedmiotu> / przekaż <gracz> <przedmiot> przekazuje jedną sztukę z inventory.",
        "daj <gracz> <ilość> <przedmiot> przekazuje kilka identycznych sztuk, np. daj Arven 3 Mikstura Leczenia.",
        "daj <gracz> <ilość> złota przekazuje walutę; działają też srebro i mithril, np. daj Arven 250 złota.",
        "Odbiorca musi być online i stać w tej samej lokacji. Transfer przedmiotu i waluty jest wykonywany atomowo, aby nie tworzyć duplikatów.",
        "Narzędzia Character-Bound i przedmioty questowe nie mogą być przekazywane. Założone EQ trzeba najpierw zdjąć; wolna druga sztuka może być przekazana.",
        "Wspólny portfel wszystkich postaci na jednym koncie nie pozwala przesyłać waluty między własnymi slotami jako osobnego transferu.",
    ]
    HELP_TOPICS["gracze"] = [
        "who pokazuje graczy online.",
        "say <tekst> mówi do osób w tej samej lokacji; tell <gracz> <tekst> wysyła wiadomość prywatną; reply <tekst> odpowiada ostatniemu nadawcy.",
        "pc <tekst> wysyła wiadomość do drużyny.",
        "daj/przekaż pozwala oddawać zwykłe przedmioty i walutę graczowi stojącemu w tej samej lokacji; help przekazywanie pokazuje składnię.",
        "bufor chat, bufor party i bufor tell pozwalają odczytać ostatnią komunikację z bieżącej sesji.",
    ]
    HELP_TOPICS["druzyny"] = [
        "załóż drużynę / zaloz druzyne tworzy drużynę; druzyna / party pokazuje skład i status.",
        "zaproś <gracz>, dołącz, odrzuć, opuść, wyrzuć <gracz>, rozwiąż oraz lider <gracz> zarządzają drużyną.",
        "Gdy porusza się lider, członkowie stojący z nim w tej samej lokacji automatycznie próbują wykonać ten sam krok. Działa to również podczas prowadzenia walk/prowadz.",
        "Follower nie jest teleportowany przez blokady: walka, niedostępne przejście lub indywidualne wymaganie może zatrzymać konkretnego członka bez zatrzymywania lidera.",
        "pc <tekst> to czat drużynowy; bufor party pokazuje jego ostatnie wpisy.",
        "Jeśli Odłamek Duszy wypadnie z przeciwnika podczas wspólnej walki, każdy członek drużyny obecny w tej samej lokacji otrzymuje własny Odłamek. Odłamki po queście zużywa też crafting: Eliksiry Duszy, wysokie talizmany, runy i Rdzeń Gniazda.",
        "wspieraj / assist pomaga członkowi w walce; zasłoń / zaslon pozwala aktywnemu Strażnikowi przejmować aggro wspólnego przeciwnika w tej samej lokacji.",
        "Limit drużyny rośnie z Charyzmą lidera.",
    ]
    HELP_TOPICS["pieniadze"] = [
        "portfel / wallet / saldo pokazuje jedno wspólne saldo konta jako mithril, złoto i srebro.",
        "100 srebra = 1 złoto; 1 000 000 złota = 1 mithril. Wewnętrznie gra zapisuje jedno saldo w srebrze.",
        "daj <gracz> <ilość> złota przekazuje walutę innemu graczowi online w tej samej lokacji; można też podać srebro lub mithril.",
        "Przekazanie waluty aktualizuje oba wspólne portfele atomowo i nie może zejść poniżej zera ani przekroczyć bezpiecznego limitu SQLite.",
    ]
    HELP_TOPICS["xp"] = [
        "xp pokazuje aktualny Character XP i dokładnie ile brakuje do następnego Levelu postaci; na 400 informuje o maksimum.",
        "Event x2 EXP obejmuje Character, Class, Soul, Skill, stat, profession i tool XP; eventxp pokazuje jego status.",
        "historia xp albo bufor xp pokazuje ostatnie komunikaty progresji z bieżącej sesji.",
    ]
    # Finalne dopiski do istniejących tematów bez duplikowania całych historycznych bloków.
    for topic, line in (
        ("ekwipunek", "daj/przekaż obsługuje teraz także zwykłe przedmioty inventory; Character-Bound, questowe i założone EQ są chronione."),
        ("questy", "historia quest albo bufor quest pokazuje ostatnie komunikaty questowe z bieżącej sesji."),
        ("walka", "bufor walka pokazuje ostatnie komunikaty walki; bufor xp zachowuje komunikaty progresji."),
        ("podstawy", "v0.30.11: drużyna podąża za liderem, bufory historii są dostępne przez bufor/historia <kategoria>, a daj/przekaż obsługuje przedmioty i walutę."),
    ):
        HELP_TOPICS.setdefault(topic, [])
        if line not in HELP_TOPICS[topic]:
            HELP_TOPICS[topic].append(line)

    # Końcowy audyt spójności: usuń puste/duplikowane linie, zachowując kolejność.
    for topic, lines in list(HELP_TOPICS.items()):
        clean = []
        seen = set()
        for line in lines:
            text = str(line).strip()
            if not text:
                continue
            key = normalize_lookup_text(text)
            if key in seen:
                continue
            seen.add(key)
            clean.append(text)
        HELP_TOPICS[topic] = clean


def refresh_help_truth_v11197():
    HELP_TOPICS["podstawy"] = [
        "Główna progresja postaci działa w zakresie 1-800. Statystyki bazowe nie mają twardego limitu.",
        "Level postaci, Biegłość klas, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia rozwijają się do 800.",
        "Soulbound ma 14 klas i 14 profesji. Szczegóły: help klasy, help profesje, help umiejetnosci, help ekwipunek.",
        "Najważniejsze komendy startowe: help, look/l, exits, hp, score, staty, dusza, eq, quest, atlas, prowadz/walk.",
        "k <mob> / atakuj <mob> rozpoczyna walkę realtime; con <mob> ocenia przeciwnika bez rozpoczynania walki.",
        "Dokładne wartości skilli, EQ, przeciwników i progresji są czytane z bieżących danych runtime, a nie ze starej tabeli HELP.",
    ]

    HELP_TOPICS["statystyki"] = [
        "Sześć automatycznych statystyk to Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma.",
        "Bazowe statystyki są bez twardego limitu. EQ, runy, sety i relikty zwiększają wartości efektywne używane przez walkę.",
        "v1.13.42: każde źródło stat EXP nadal dostaje globalnie x4 przed bonusem rasy i Gildii, ale wymagany EXP do kolejnego punktu ma teraz mnożnik x4 dla długoterminowej progresji.",
        "Dla równorzędnego zwykłego źródła generator celuje efektywnie w około 60 akcji na kolejny punkt każdej statystyki; rare, minibossy, bossy, questy i x2 EXP nadal przyspieszają postęp.",
        "Ofensywne skille używają właściwych statystyk klasy. Każde leczenie w Soulbound skaluje się z Inteligencją i Siłą Woli; Magic Attack zwiększa obrażenia magiczne, ale nie leczenie.",
        "Zręczność buduje końcową Szybkość. Liczba trafień zwykłego autoataku Broni Duszy wynika z końcowej Szybkości, a aktywny Haste osobno zwiększa długość serii trafień.",
        "staty info pokazuje bazę, wartości efektywne, postęp oraz bonusy wyposażenia.",
    ]

    HELP_TOPICS["score"] = [
        "score pokazuje Level postaci, EXP, aktywne klasy i Biegłość, Duszę, HP/Manę, statystyki, portfel, EQ i bieżący teren.",
        "Poziom postaci, Biegłość klas, Soul Level i Mastery, skille, profesje oraz narzędzia mają limit 800; statystyki bazowe są bez limitu. Generator Core został usunięty.",
        "con <mob> jest właściwą komendą do bieżącej oceny konkretnego przeciwnika.",
    ]

    HELP_TOPICS["level"] = [
        "level / lvl pokazuje Level postaci 1-800, aktualny EXP i dokładnie ile brakuje do następnego Levelu.",
        "Na Levelu 800 komenda informuje o osiągniętym maksimum.",
        "Biegłość klasy, Soul Level, Skill Level, profesje i narzędzia są osobnymi osiami progresji.",
    ]

    HELP_TOPICS["xp"] = [
        "xp pokazuje aktualny Character XP oraz ile brakuje do następnego Levelu postaci.",
        "Character Level ma zakres 1-800. Na 800 osiąga maksimum.",
        "Event x2 EXP obejmuje Character, Class, Soul, Skill, stat, profession i tool XP; eventxp pokazuje status eventu.",
    ]

    skill_help = [
        "Każda z 14 klas ma własne skille/spelle odblokowywane przez Biegłość klasy 1-600.",
        "Każdy nauczony skill ma osobny Skill Level 1-600. Wspólna krzywa mocy rośnie przez cały zakres i na Skill Level 600 osiąga końcowy punkt 4.00x.",
        "Zwykłe skille klasowe nie mają cooldownu ponownego użycia. Wyjątek stanowią zdolności, których timer jest częścią specjalnej mechaniki, np. V-MAX.",
        "Pasywne umiejętności po nauczeniu działają automatycznie i nie zajmują slotów auto-kolejki.",
        "help skill <nazwa>, help <nazwa skilla> i skill info <nazwa> czytają bieżące dane skilla: klasę, próg Biegłości, Manę, target, skalowanie, właściwości źródłowe, Skill Level i mechaniczny cooldown, jeśli istnieje.",
        "skills pokazuje skille aktywnych klas; skills all, skillnames oraz kodeksklasowy <klasa> pozwalają przejrzeć pełny katalog.",
    ]
    HELP_TOPICS["umiejetnosci"] = list(skill_help)
    HELP_TOPICS["skille"] = list(skill_help)

    HELP_TOPICS["aoe"] = [
        "aoe on włącza ofensywne efekty wielocelowe; aoe off ogranicza je do jednego przeciwnika.",
        "Dotyczy to wszystkich zwykłych skilli aoe_damage oraz źródłowych wyjątków wielocelowych, m.in. Starlight Shower i Jammer z aktywnym Support Effect.",
        "Przy aoe on umiejętność zachowuje własne zasady targetowania: diminishing, non-diminishing, losowe trafienia albo tylko już zaangażowane cele. help skill <nazwa> pokazuje opis konkretnej zdolności.",
        "AoE nie przepisuje właściciela nagród cudzego moba; party credit działa według aktualnej logiki drużyny.",
        "Zwykłe AoE nie ma globalnego cooldownu; specjalny timer występuje tylko tam, gdzie jest częścią mechaniki skilla.",
    ]

    HELP_TOPICS["kolejka"] = [
        "Auto-kolejka dzieli aktywne umiejętności na fizyczne, magiczne i Feedback. Pasywki działają automatycznie, bez kolejki.",
        "Nowo nauczony u nauczyciela aktywny czar lub skill automatycznie trafia do właściwej rotacji; kolejka dodaj jest opcjonalne.",
        "Wcześniej poznane aktywne skille są uzupełniane jednorazowo; ręczne usunięcie nie zostaje cofnięte przy kolejnym logowaniu.",
        "Kolejki fizyczna, magiczna i Feedback są bez limitu aktywnych i zapisanych miejsc. Level postaci nie narzuca liczby slotów.",
        "W rundzie walki kolejka używa gotowego skilla zgodnie z maną, celem, specjalnymi timerami i aktywnymi klasami. Nie zastępuje zwykłego autoataku Broni Duszy.",
        "kolejka lista [fizyczna|magiczna|feedback] [strona] pokazuje 25 wpisów na stronę, czytelnie dla NVDA.",
        "kolejka on/off, kolejka usuń <numer>, kolejka wyczyść i kolejka góra/dół pozwalają sterować rotacją. Ręczne kolejka off jest zachowywane.",
    ]

    HELP_TOPICS["dusza"] = [
        "Broń Duszy ma Soul Level 1-800 oraz osobną Soul Weapon Mastery 1-800.",
        "Soul Weapon Mastery rozwija zwykły autoatak Broni Duszy; skille klasowe rozwijają własny Skill Level 1-800.",
        "Zwykły atak Broni Duszy działa w każdej rundzie walki niezależnie od auto-kolejki. Skill z kolejki może wykonać się w tej samej rundzie i nie zabiera ataku Broni Duszy.",
        "System Soul Tierów obejmuje progresję do 800; dusza info pokazuje bieżący Tier, wymagania, Próby i następny cel.",
        "Relikty Broni Duszy są wybierane przez relic / relikt; EQ i aktywny relikt wpływają na realne parametry walki.",
    ]

    HELP_TOPICS["profesje"] = [
        "Soulbound ma 14 profesji 1-600.",
        "Zbieractwo: Wędkarstwo, Górnictwo, Drwalstwo i Zielarstwo.",
        "Rzemiosła: Gotowanie, Alchemia, Kowalstwo, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo i Zaklinanie.",
        "Eksploracja: Archeologia i Kartografia.",
        "Każda profesja ma własny poziom 1-600; jej narzędzie rozwija się osobno 1-600. Wszystkie 14 narzędzi kupuje się tylko raz na postać.",
        "zamowienia / zamówienia obsługuje zamówienia wszystkich 14 profesji; zlecenia odnawiają się niezależnie zgodnie z ich godzinnym cooldownem.",
        "Archeologia: wykop. Kartografia: mapuj. Szczegóły: help archeologia i help kartografia.",
        "v1.13.8: zwykłe zbieractwo daje sensowny zarobek względem etapu, a rzadkie warianty są jackpotami: rośnie wartość sprzedaży oraz Profession/Tool XP.",
        "Wędkarstwo dodatkowo wycenia trofealność gatunku. Rekiny, legendarne ryby i lewiatany są warte wyraźnie więcej nawet bez rzadkiego wariantu; Albinos/Złoty/Olbrzymi/Pradawny mnożą wartość dalej.",
        "Górnictwo nagradza bogate, kryształowe i legendarne żyły większą ilością oraz XP; Geody mają realne złoto i szansę na Doskonałe/Perfekcyjne klejnoty.",
        "Pierwsze odkrycia Archeologii mają premię XP i wysoką wartość kolekcjonerską; pierwszy pomiar lokacji w Kartografii daje dodatkową premię odkrywcy.",
    ]

    HELP_TOPICS["tempo_profesji"] = [
        "Czas aktywności profesyjnych zależy od bieżącej profesji, narzędzia i konkretnej czynności.",
        "Profesje i narzędzia rozwijają się 1-600; szczegółowy stan pokazują profesje info i narzedzia info.",
    ]
    HELP_TOPICS["narzedzia200"] = [
        "Narzędzia wszystkich 14 profesji mają progresję 1-600 i nie mają trwałości.",
        "narzedzia / tools pokazuje stan; narzedzia info pokazuje XP, Tiery, bonusy i sprzedawców.",
        "Każde przypisane narzędzie profesji można kupić tylko raz na postać.",
    ]
    HELP_TOPICS["wiecej_ryb"] = [
        "Wędkarstwo i Wędka mają progresję 1-600. Kolejne gatunki odblokowują się wraz z narzędziem i właściwym łowiskiem.",
        "atlas ryby oraz woda / łowisko pokazują bieżące źródła i wymagania.",
        "Gatunki trofealne mają własną premię wartości: im rzadszy gatunek, tym większa cena; rekiny i lewiatany dostają dodatkową premię.",
        "Rzadkie warianty są jackpotami: Albinos x3, Olbrzymi x5, Złoty x8, Pradawny x15 wartości bazowej. Jackpot zwiększa też Wędkarstwo/Tool XP, ale łagodniej niż cenę.",
    ]

    HELP_TOPICS["generator"] = [
        "dawny Generator Core i warstwa progresji 600 są źródłem bieżących wartości balansu tam, gdzie system korzysta z generowanych danych.",
        "Główne osie progresji kończą się na 600; bazowe statystyki postaci nie mają twardego limitu.",
        "Dokładne liczby sprawdzaj przez komendy runtime: con, score, staty info, skill info, eq info, atlas i receptury.",
        "HELP nie powinien kopiować historycznych limitów 400 ani zwykłych cooldownów skilli.",
    ]
    HELP_TOPICS["progresja600"] = [
        "Aktualna główna progresja Soulbound to 1-800: Character Level, Biegłość klas, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia.",
        "Statystyki bazowe są rozwijane bez twardego limitu.",
        "Historyczne nazwy wewnętrzne zawierające 400 mogą pozostać dla kompatybilności save'ów i ID, ale nie oznaczają aktualnego limitu gracza.",
    ]
    HELP_TOPICS["progresja400"] = [
        "To historyczna nazwa starszej warstwy progresji. Aktualna gra używa progresji 1-800.",
        "Wpisz help progresja600, aby usłyszeć bieżące zasady.",
    ]

    for topic, profession in (
        ("krawiectwo", "Krawiectwo"),
        ("garbarstwo", "Garbarstwo"),
        ("stolarstwo", "Stolarstwo"),
        ("zaklinanie", "Zaklinanie"),
    ):
        old = HELP_TOPICS.get(topic, [])
        if isinstance(old, str):
            old = [old]
        cleaned = [
            str(line).replace("1-400", "1-600").replace("1–400", "1–600")
            for line in old
            if str(line).strip()
        ]
        if not cleaned:
            cleaned = [f"{profession} ma progresję 1-600."]
        if profession == "Zaklinanie":
            cleaned.append(
                "Fokus Runiczny kupisz w Komnacie Arkanów u Kwatermistrzyni "
                "Selene. Wpisz shop albo kup Fokus Runiczny. Narzędzie jest "
                "przypisane do postaci i kupuje się je tylko raz."
            )
        HELP_TOPICS[topic] = cleaned

    old_jewel = HELP_TOPICS.get("jubilerstwo2", [])
    if isinstance(old_jewel, str):
        old_jewel = [old_jewel]
    HELP_TOPICS["jubilerstwo2"] = [
        str(line).replace("do levelu 400", "do levelu 600").replace("1-400", "1-600")
        for line in old_jewel
    ] or ["Jubilerstwo ma progresję 1-600; receptury sprawdzisz przez receptury jubilerstwo."]

    equipment = HELP_TOPICS.get("ekwipunek", [])
    if isinstance(equipment, str):
        equipment = [equipment]
    equipment = list(equipment)
    equipment.extend([
        "Aktualne sloty obejmują także tarczę i bransoletę. Skróty: ztar / ztarcza dla tarczy oraz zbra dla bransolety.",
        "AUTO EQ ocenia sprzęt pod aktywne klasy: właściwe STR/DEX/INT, Kondycję/Siłę Woli, Attack/Magic Attack/Weapon Power, obrony, właściwości procentowe, wardy, status-proof, rarity i sockety.",
        "eq info pokazuje realne bonusy, sety, sockety oraz oddziela potwierdzone dane źródłowe od Bonusów Soulbound tam, gdzie taki podział istnieje.",
    ])
    HELP_TOPICS["ekwipunek"] = equipment
    HELP_TOPICS["eq"] = list(equipment)
    party_help = list(HELP_TOPICS.get("druzyny", []))
    party_help.extend([
        "Nagrody za wspólne zabicie nie mają kary drużynowej: każdy obecny członek drużyny dostaje własne pełne Character XP, Class XP, Soul XP i EXP statystyk.",
        "Waluta z pokonanego przeciwnika również nie jest dzielona przez liczbę graczy: każdy obecny członek dostaje pełną bazową pulę monet, a jego własne mnożniki nagród są stosowane osobno.",
        "Udane dropy drużynowe i osobiste nagrody bossów zachowują własne zasady; samo dołączenie do party nie obniża wartości EXP ani monet.",
        "W lochach drużyna może dodatkowo uzyskać Dungeon Party Bonus do EXP, więc wspólna gra nie jest karana za liczbę członków.",
    ])
    HELP_TOPICS["druzyny"] = party_help
    HELP_TOPICS["party"] = list(party_help)

    HELP_TOPICS["leczenie"] = [
        "Każdy heal w Soulbound używa wspólnego rdzenia leczenia: Inteligencja + Siła Woli.",
        "INT i WILL mają równy udział w bazowej mocy leczenia, więc EQ podnoszące którykolwiek z tych statów zwiększa healing.",
        "Magic Attack zwiększa obrażenia magiczne, ale nie zwiększa leczenia.",
        "Skill Level, rasa, klasa i specjalne efekty konkretnej umiejętności nadal modyfikują końcową wartość leczenia.",
        "Dotyczy to zwykłych healów, Cure Beam, Heal Beam oraz okresowego Regen.",
    ]

    HELP_TOPICS["statusy"] = [
        "Efekty ofensywne takie jak Silence, Slow, Paralyze i obniżenie obrony są nakładane na przeciwników, nie na rzucającego.",
        "Heale i buffy używają celu zapisanego przy konkretnej umiejętności: siebie, sojusznika, drużynę albo inny dozwolony cel.",
        "Źródłowy Silence oznacza One Enemy, skaluje celność/czas z poziomem umiejętności i blokuje rzucanie magii; jest Cleanseable i Extendable.",
        "help skill <nazwa> pokazuje zapisany target, wpływ statystyk, właściwości i efekt Skill Level tam, gdzie dane źródłowe są znane.",
    ]

    HELP_TOPICS["forma"] = [
        "Bronie zdobywane lub kupowane jako wzmocnienia Broni Duszy działają jako jej formy, a nie jako drugi osobny slot broni.",
        "Kupiona forma zostaje na stałe w kolekcji. Tylko jedna forma może być aktywna naraz i tylko ona przekazuje swoje statystyki, Attack/Magic Attack/Weapon Power oraz zapisane efekty do Broni Duszy.",
        "forma lista pokazuje wszystkie dostępne formy, ich typ źródłowy i najważniejsze bonusy; aktywna forma jest oznaczona.",
        "forma wybierz <numer lub nazwa> ustawia konkretną formę na stałe. forma auto wraca do automatycznego wyboru najwyższej dostępnej formy według wymaganego poziomu.",
        "Przełączenie formy nie resetuje Soul Level, Soul Tier ani Soul Weapon Mastery. Starsze komendy relikt/relic pozostają zgodnymi aliasami.",
    ]
    HELP_TOPICS["formy"] = list(HELP_TOPICS["forma"])

    HELP_TOPICS["mec"] = [
        "Mec korzysta z jednej Broni Duszy; role melee, ranged, magic, feedback i support są gałęziami tej klasy, nie osobnymi broniami do noszenia.",
        "Strength Protocol, Ranged Protocol, Feedback Protocol i Magic Protocol są pasywne. Po nauczeniu działają automatycznie i wzmacniają odpowiadające im gałęzie wraz ze Skill Level.",
        "Cure Beam i Heal Beam skalują leczenie z Inteligencją i Siłą Woli oraz Skill Levelem. Magic Attack nie zwiększa leczenia. Support Effect zmienia ich zachowanie zgodnie z opisem skilla.",
        "V-MAX jest specjalnym overdrive'em zależnym od Siły Woli: daje Protect, Shell, Haste, Regen, Preach, Praise i Permanence oraz zmienia wybrane skille. Haste osobno zwiększa serię trafień zwykłego autoataku, którego baza zależy od końcowej Szybkości. Timer V-MAX jest mechaniką specjalną, więc pozostaje wyjątkiem od globalnego braku cooldownów.",
        "Cosmic Rave normalnie trafia wszystkie cele z diminishing; podczas V-MAX wykonuje losowe trafienia. Shoot-All trafia wszystkie cele bez diminishing i w V-MAX zyskuje damage oraz crit.",
    ]

    HELP_TOPICS["superbossy"] = [
        "superbosses pokazuje unikalne wyzwania Super Bossów, wymagania i zaliczenia.",
        "superbosses <nazwa> pokazuje informacje o konkretnym bossie; superboss <nazwa> obsługuje wejście do jego encounteru.",
        "Black Rabite pozwala wybrać Primm albo Popoi komendą pomocnik primm / pomocnik popoi; wybór działa na jego arenie i dla drużyny maksymalnie 3 graczy.",
        "Nagrody, sklepy bossów, relikty i specjalne właściwości EQ są częścią aktualnego runtime Soulbound; eq info i shop info pokazują bieżące dane.",
    ]

    HELP_TOPIC_ALIASES.update({
        "forma broni duszy": "forma",
        "formy broni duszy": "forma",
        "formy": "forma",
        "progresja600": "progresja600",
        "progression600": "progresja600",
        "statusy": "statusy",
        "status": "statusy",
        "debuffy": "statusy",
        "superbossy": "superbossy",
        "superboss": "superbossy",
        "superbosses": "superbossy",
    })


def refresh_public_help_surface_v11197():
    HELP_TOPICS["klasy"] = [
        "Soulbound ma 14 grywalnych klas. Każda ma osobną Biegłość 1-600, własną Broń Duszy, skille/spelle i profil statystyk.",
        "Biegłość właściwej klasy odblokowuje jej umiejętności; Skill Level rozwija każdą nauczoną umiejętność osobno.",
        "Multiclass pozwala utrzymywać do 3 aktywnych klas bez kasowania progresji klas wyłączonych.",
        "kodeksklasowy <klasa> pokazuje pełny katalog umiejętności, wymagania, nauczyciela i status nauki.",
    ]

    HELP_TOPICS["zadania klasowe"] = [
        "Każda z 14 klas ma 5 różnych zadań klasowych w każdym cyklu godzinnym: walka, bossowie, eksploracja, zbieractwo i crafting.",
        "v1.13.42: wymagania, nazwy i nagrody rosną wraz z Biegłością klasy przez etapy Początek, Adept, Mistrz, Legenda, Transcendencja, Apogeum i Absolut.",
        "Każda klasa ma własne priorytety dwóch aktywności, więc Wojownik/Berserker mocniej idą w walkę i bossów, Druid/Łowca w teren i zasoby, a Mec/Inżynier w bossy/crafting.",
        "Etap Biegłości jest zamrażany na całą bieżącą godzinę. Awans klasy w połowie zadania nie podnosi nagle wymagania; nowy etap wchodzi dopiero przy następnym odnowieniu.",
        "Wpisz zadanieklasowe, aby zobaczyć pięć ofert aktywnej klasy. Przyjmij przez zadanieklasowe <numer>; jednocześnie aktywne jest jedno zadanie.",
        "Po wykonaniu celu wpisz zadanieklasowe, aby odebrać nagrodę. Potem możesz wybrać kolejne zadanie z tej samej piątki.",
        "zadanieklasowe porzuc wstrzymuje aktywne zadanie bez kasowania jego postępu do końca bieżącej godziny.",
        "O pełnej godzinie cykl zadań klasowych odnawia się i postępy bieżącego cyklu startują od nowa. Ukończenie dowolnego zadania zachowuje historyczne wymaganie do egzaminu Soul 50.",
        "Postęp liczy wyłącznie właściwą aktywność aktywnego zadania: kill, boss, nowe lokacje, zebrane zasoby albo udane crafty.",
    ]
    HELP_TOPICS["zadanieklasowe"] = list(HELP_TOPICS["zadania klasowe"])
    HELP_TOPICS["class quests"] = list(HELP_TOPICS["zadania klasowe"])
    HELP_TOPIC_ALIASES.update({
        "zadania klasowe": "zadania klasowe",
        "zadanie klasowe": "zadania klasowe",
        "zadanieklasowe": "zadania klasowe",
        "class quest": "zadania klasowe",
        "class quests": "zadania klasowe",
    })
    HELP_TOPICS["hartowanie"] = [
        "Hartowanie EQ jest osobnym systemem ulepszania odporności żywiołowych u Haldora w Kuźni.",
        "Komenda: hartuj <żywioł> <pełna nazwa EQ>. Przykład: hartuj fire Venetian Shield.",
        "Stan konkretnego przedmiotu: hartuj status <pełna nazwa EQ>.",
        "Dostępne żywioły: Fire, Ice, Electric, Dark, Poison, Holy, Water i Arcane.",
        "Każdy żywioł na jednym EQ ma 5 rang; każda ranga daje +2 procent odporności, maksymalnie 10 procent z danego przedmiotu.",
        "Hartowanie wielu założonych przedmiotów sumuje się do 40 procent. Istniejące specjalne Wardy z authored/boss EQ są dodawane ponad to, a końcowa ochrona ma limit 80 procent.",
        "Koszt rośnie z rangą i poziomem EQ: Esencja Runiczna oraz odpowiedni stop. Hartowanie daje XP Kowalstwa i Młota; im wyższe EQ i ranga, tym większy realny XP.",
        "Hartowanie jest trwałe i przenosi się razem z EQ przy przekazaniu przedmiotu.",
    ]
    HELP_TOPICS["hartuj"] = list(HELP_TOPICS["hartowanie"])
    HELP_TOPIC_ALIASES.update({
        "hartuj": "hartowanie",
        "harden": "hartowanie",
        "hardening": "hartowanie",
        "hartowanie eq": "hartowanie",
    })


    HELP_TOPICS["rasy"] = [
        "Soulbound ma 14 grywalnych ras. Każda może wybrać każdą z 14 klas; rekomendacje rasowo-klasowe są wskazówką, nie blokadą.",
        "Rasy różnią się rozkładem pięciu głównych statystyk oraz pasywem rasowym.",
        "Cyborg jest rasą technologiczną szczególnie pasującą do Meca i Inżyniera, ale nie otrzymuje Moogle Board na starcie.",
        "Pełne statystyki i pasyw konkretnej rasy są czytane przy tworzeniu postaci oraz w jej opisie.",
    ]

    HELP_TOPICS["cyborg"] = [
        "Cyborg: technologiczna rasa z wysoką Kondycją i dobrą Zręcznością. Pasyw rasowy zmniejsza wszystkie otrzymywane obrażenia.",
        "Polecane klasy to m.in. Mec, Inżynier, Strażnik i Łowca, ale Cyborg może wybrać dowolną z 14 klas.",
        "Moogle Board NIE jest przedmiotem startowym. Jest unikalną osobistą nagrodą Black Rabite i może wypaść tylko Cyborgowi.",
        "Moogle Board od Levelu postaci 150 daje +20 do Siły, Zręczności, Kondycji, Inteligencji i Siły Woli; od 151 każdy kolejny Level zwiększa ten bonus o +2.",
    ]

    engineer_help = [
        "Inżynier jest technologiczną klasą fizyczną z Biegłością 1-600. Broń Duszy: Omni-Narzędzie.",
        "Autorski zestaw obejmuje m.in. Auto Crossbow, Mako Gun, Bio Blaster, Scanner, Flash, Debilitator, Drill, Napalm, Launcher, Noise Blaster, Chainsaw, Mega Bomb i Air Anchor.",
        "Upgrade <narzędzie> zapisuje trwałe ulepszenie Inżyniera; Hypercharge, Lindblum Assembly i Improved Kinematics działają zgodnie z aktualną mechaniką klasy.",
        "help skill <nazwa> pokazuje bieżący target, skalowanie, wymagania i właściwości konkretnej umiejętności.",
    ]
    HELP_TOPICS["inzynier"] = list(engineer_help)
    HELP_TOPICS["inżynier"] = list(engineer_help)

    HELP_TOPICS["skille100_200"] = [
        "To historyczna nazwa tematu. Aktualnie Biegłość klas i Skill Level rozwijają się 1-600.",
        "Standardowe klasy mają dalsze odblokowania aż do 600; Mec i Inżynier zachowują autorskie progi swoich źródłowych zestawów.",
        "Auto-kolejka zaczyna od 20 aktywnych slotów na Character Level 1 i rośnie do 80 na Levelu 600.",
        "Zwykłe skille klasowe nie mają cooldownu ponownego użycia; specjalny timer zostaje tylko tam, gdzie jest częścią mechaniki.",
    ]

    HELP_TOPICS["hp_mobow"] = [
        "HP, obrażenia i nagrody przeciwników są liczone z ich aktualnego profilu runtime, rangi, regionu i warstwy progresji.",
        "Główna progresja świata dochodzi do 600; nieskończone instancje i Super Bossowie mają własne dalsze zasady skalowania.",
        "con <mob> pokazuje bieżącą ocenę konkretnego przeciwnika i jest właściwym źródłem aktualnych liczb.",
    ]
    HELP_TOPICS["soul_xp_bloki"] = [
        "Soul Level rozwija się 1-600. Soul XP i progi kolejnych Tierów korzystają z aktualnej warstwy progresji 600.",
        "dusza info pokazuje bieżący Soul XP, Tier, blokadę Próby i dokładny następny cel.",
    ]
    HELP_TOPICS["hp_bossow_lochow"] = [
        "Bossowie lochów korzystają z aktualnych danych konkretnej instancji i jej bieżącego skalowania, a nie ze starego limitu etapu 400.",
        "Główna progresja kończy się na 600; nieskończone lochy zachowują własne zasady dalszego wzrostu.",
        "consider / con pokazuje aktualną ocenę bossa przed rozpoczęciem walki.",
    ]
    HELP_TOPICS["expowiska"] = [
        "Dobór zwykłych terenów i expowisk opiera się na Character Levelu oraz realnym zagrożeniu regionu w aktualnej progresji 1-600.",
        "Biegłość klasy rozwija klasę i odblokowuje jej umiejętności; nie zastępuje Character Levelu przy ocenie terenu.",
        "teren info <nazwa>, con <mob> i progress region pokazują bieżące informacje zamiast historycznej tabeli 1-400.",
    ]
    HELP_TOPICS["questy_kowalstwa_1_200"] = [
        "To historyczna nazwa tematu. Kowalstwo jest pełną profesją 1-600.",
        "Aktualne zlecenia czytają wymagane materiały, produkty, postęp i nagrody z bieżących danych runtime.",
    ]
    HELP_TOPICS["questy_gotowania_1_200"] = [
        "To historyczna nazwa tematu. Gotowanie jest pełną profesją 1-600.",
        "Aktualne zlecenia korzystają z bieżących potraw, składników i wymagań; stare ograniczenie 1-400 nie obowiązuje.",
    ]
    HELP_TOPICS["questy_mikstur_orina"] = [
        "Alchemia jest pełną profesją 1-600. Zlecenia Orina korzystają z bieżących mikstur, składników i wymagań.",
        "Każde przyjęte zlecenie liczy postęp od 0/x zgodnie z aktualną logiką questa.",
    ]
    HELP_TOPICS["atlas"] = [
        "atlas bez argumentu pokazuje działy Atlasu. atlas odkrycia otwiera Globalny Atlas Odkryć.",
        "Globalny Atlas śledzi miasta, wyspy, lochy, platformy oceaniczne, ruiny, areny Super Bossów i sekretne lokacje na podstawie realnej historii odkrywania postaci.",
        "Każdy dział ma osobne osiągnięcie za 100 procent. Ukończenie wszystkich działów odblokowuje osiągnięcie Globalny Atlas: cały odkryty świat oraz tytuł Kartograf Całego Świata.",
        "Szczegóły: atlas odkrycia miasta / wyspy / lochy / platformy / ruiny / superbossy / sekrety. Nieodkryte sekrety, proceduralne mini-lochy i Wielkie Ruiny są ukrywane jako ???.",
        "Atlas działa retroaktywnie dla starszych save'ów: wcześniej odwiedzone miejsca są zaliczane z istniejącej historii odkrytych lokacji.",
        "Atlas zasobów pozostaje dostępny przez atlas ryby, atlas rudy, atlas drewno, atlas ziola, atlas geody albo atlas <zasób>.",
    ]
    HELP_TOPICS["atlas_kompletny"] = [
        "Globalny Atlas Odkryć: atlas odkrycia. Śledzi wszystkie skończone kategorie długoterminowej eksploracji i daje osobne osiągnięcia za ich ukończenie.",
        "Atlas zasobów pokazuje aktualne progi i miejsca występowania ryb, rud, drewna, ziół, geod i innych zasobów.",
        "Użyj atlas odkrycia albo atlas ryby, atlas rudy, atlas drewno, atlas ziola, atlas geody i atlas <zasób>; wynik jest czytany z bieżących danych.",
        "Profesje i narzędzia rozwijają się do 600, więc stary opis kończący atlas na 400 nie jest aktualny.",
    ]
    HELP_TOPIC_ALIASES.update({
        "atlas odkryc": "atlas",
        "atlas odkryć": "atlas",
        "atlas odkrycia": "atlas",
        "globalny atlas": "atlas",
    })
    for _legacy_balance_topic in ("balans 0865", "balans 0866", "balans 0874"):
        if _legacy_balance_topic in HELP_TOPICS:
            HELP_TOPICS[_legacy_balance_topic] = [
                "To historyczny temat dawnego wydania. Nie opisuje aktywnego balansu.",
                "Aktualna główna progresja dochodzi do 600, a bazowe statystyki postaci nie mają twardego limitu.",
                "Bieżące liczby sprawdzaj przez con, score, staty info, skill info, eq info i atlas.",
            ]

    HELP_TOPICS["walka"] = [
        "k <mob> / atakuj <mob> rozpoczyna walkę realtime; uciekaj / flee wycofuje z walki, a wimpy może robić to automatycznie przy ustawionym progu HP.",
        "Zwykły autoatak korzysta z Broni Duszy i aktualnego buildu postaci. Auto-kolejka nie zastępuje tego ataku: w tej samej rundzie może wykonać się skill oraz zwykły atak Bronią Duszy.",
        "Ofensywne skille nie są globalnie dzielone na zasadę fizyczne=tylko Siła i magiczne=tylko Inteligencja; help skill <nazwa> pokazuje właściwe skalowanie konkretnej zdolności.",
        "Zwykłe skille klasowe są bez cooldownu ponownego użycia; specjalne timery pozostają tylko tam, gdzie są elementem mechaniki, np. V-MAX.",
        "combatlog concise/normal/full oraz bufor walka sterują szczegółowością i pozwalają wrócić do ostatnich komunikatów.",
    ]

    HELP_TOPICS["materialy_eq"] = [
        "Materiałowe EQ obejmuje pełną aktualną siatkę 17 logicznych typów: głowę, korpus, tarczę, dłonie, nogi, stopy, talizman, pierścień, naszyjnik, kolczyk, naramienniki, pas, pelerynę, karwasze, bransoletę, akcesorium i relikt.",
        "Pierścienie, talizmany, kolczyki i akcesoria mają po dwa fizyczne sloty 1/2.",
        "Materiały i warianty EQ rozciągają się przez aktualną progresję 1-600; dokładne wymaganie konkretnego przedmiotu pokazuje eq info.",
        "Losowe statystyki, rarity, sockety, runy i inne właściwości są oceniane z realnych danych przedmiotu.",
    ]

    HELP_TOPICS["kolczyki"] = [
        "Kolczyk jest jednym z 17 logicznych typów aktualnego EQ; postać ma dwa fizyczne sloty kolczyków.",
        "zkol pokazuje/wybiera kolczyki automatycznie, a zkol1 i zkol2 pozwalają wskazać konkretny slot.",
        "Materiałowe, klasowe i inne bieżące źródła EQ mogą zawierać kolczyki zgodnie z ich aktualnymi tabelami dropu/sklepu.",
        "eq info oraz porownaj pokazują realne statystyki i porównanie konkretnego kolczyka.",
    ]

    HELP_TOPICS["zakladanie_lootu"] = [
        "Gracz sam wybiera konkretny element EQ; załóż <nazwa> oraz skróty slotów zakładają posiadany przedmiot spełniający jego bieżące wymagania.",
        "Pierścienie, talizmany, kolczyki i akcesoria mają po dwa miejsca. zp, zt, zkol i zakc wybierają wolny lub słabszy slot automatycznie.",
        "Tarcza używa ztar / ztarcza, a bransoleta zbra. Ręczne sloty 1/2 pozostają dostępne dla podwójnych kategorii.",
        "Zmiana EQ podczas aktywnej walki jest blokowana. Założonego EQ nie można sprzedać ani przekazać.",
    ]

    HELP_TOPICS["sety_klasowe"] = [
        "Każda z 14 klas ma klasowe EQ w pełnej aktualnej siatce 17 logicznych typów wyposażenia.",
        "Bonusy setów pozostają na progach 2/4/6/8 części; nowe sloty, w tym Bransoletka i Akcesorium, nie tworzą łatwiejszych progów setowych.",
        "sety / sety info / sety <klasa> pokazuje bieżące składniki i aktywne bonusy.",
        "Bieżące wymagania konkretnej części sprawdzaj przez shop info albo eq info.",
    ]

    HELP_TOPICS["sklepy"] = [
        "shop / sklep / list / lista pokazuje numerowaną ofertę aktualnego sprzedawcy; shop info <numer> pokazuje pełny opis i porównanie.",
        "Każda z 14 klas ma własną linię klasowego EQ w pełnej siatce 17 logicznych typów, w tym tarczę, bransoletę i akcesorium.",
        "Zakup i założenie respektują aktualne wymagania konkretnego przedmiotu oraz wymaganą aktywną klasę/rasę, jeśli przedmiot je posiada.",
        "sell all / sprzedaj wszystko sprzedaje tylko dozwolone niezałożone EQ; chronione przedmioty są pomijane.",
    ]

    HELP_TOPICS["moogle_board"] = [
        "Moogle Board jest unikalną osobistą nagrodą Black Rabite przeznaczoną wyłącznie dla Cyborga. Nie jest startowym Boardem rasy.",
        "Od Character Level 150 daje +20 do Siły, Zręczności, Kondycji, Inteligencji i Siły Woli.",
        "Od Levelu 151 każdy kolejny Character Level zwiększa każdy z tych pięciu bonusów o +2.",
        "eq info Moogle Board pokazuje bieżący bonus wyliczony dla aktualnego Levelu postaci.",
    ]

    HELP_TOPICS["silence"] = [
        "Silence jest szkodliwym statusem kierowanym wyłącznie w przeciwnika; nie powinien być nakładany na rzucającego ani sojusznika.",
        "Kontrakt źródłowy Temple Knight: One Enemy, koszt MP 32, Stat Influence: Will, Properties: Cleanseable i Extendable.",
        "Skill Level zwiększa celność i czas działania. Efekt blokuje przeciwnikowi możliwość rzucania magii.",
        "Temple Knight nie jest piętnastą grywalną klasą Soulbound; ten wpis dokumentuje źródłowy kontrakt statusu używany przez istniejące mechaniki.",
    ]
    HELP_TOPIC_ALIASES.update({
        "moogle board": "moogle_board",
        "moogleboard": "moogle_board",
        "board moogle": "moogle_board",
        "silence": "silence",
        "cisza": "silence",
    })

    equipment = HELP_TOPICS.get("ekwipunek", [])
    if isinstance(equipment, str):
        equipment = [equipment]
    equipment = [
        line for line in equipment
        if "Aktualne sloty obejmują także tarczę i bransoletę." not in str(line)
    ]
    equipment.append(
        "Aktualna siatka ma 17 logicznych typów EQ, w tym tarczę, bransoletę i akcesorium; podwójne są pierścienie, talizmany, kolczyki i akcesoria."
    )
    equipment.append(
        "Skróty nowych slotów: ztar / ztarcza — tarcza, zbra — bransoleta, zakc — akcesoria auto."
    )
    equipment.append(
        "v1.13.6: każdy element klasowego EQ klas fizycznych daje Siłę + Zręczność + Kondycję, a każdy element klasowego EQ klas magicznych daje Inteligencję + Siłę Woli + Kondycję. Dotyczy także legendarnych setów i reliktów klasowych."
    )
    equipment.append(
        "v1.13.8: trzy linie klasowego EQ na tym samym progu są realnymi wariantami pojedynczych części: zbalansowanym, ofensywnym i pancernym. Możesz dowolnie mieszać style w różnych slotach."
    )
    equipment.append(
        "Mieszane style tej samej aktywnej klasy nadal liczą się wspólnie do progów setu 2/4/6/8. Klasowe EQ daje też płaski Attack albo Magic Attack na slotach ofensywnych; Mec jako hybryda dostaje oba kanały."
    )
    equipment.append(
        "Źródła EQ mają różne role: sklep klasowy daje pewny, klasowo dopasowany set; Kowalstwo tworzy Masterwork z mocną obroną, wyspecjalizowanymi statami i rosnącą liczbą gniazd; dropy materiałowe są losowe i dobry roll może przebić sklep w konkretnym buildzie."
    )
    equipment.append(
        "Krypta ma własną ścieżkę łupu: rzadkość zwiększa affix, obronę, Attack lub Magic Attack, właściwość procentową i liczbę gniazd. Relikty bossów Krypty skalują się z piętrem i mają pozostać warte polowania."
    )
    HELP_TOPICS["ekwipunek"] = equipment
    HELP_TOPICS["eq"] = list(equipment)


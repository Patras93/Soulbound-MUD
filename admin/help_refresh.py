


# ============================================================
# v0.27.1 - FINAL HELP/ATLAS TRUTH LAYER
# Pomoce nie przechowują kopii liczb balansu. Opisują Generator Core, a komendy
# szczegółowe (skill info, atlas, con, score) czytają aktualne wygenerowane dane.
# ============================================================
def refresh_generator_help_v0271():
    HELP_TOPICS["podstawy"] = [
        "Soulbound v0.27.1 używa Generator Core jako jedynego źródła aktywnego balansu.",
        "Level postaci, Biegłość, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia mają zakres 1-400. Sześć statystyk bazowych nie ma twardego limitu.",
        "Najważniejsze komendy startowe: look, exits, hp, score, staty, dusza, eq, quest, atlas i help.",
        "k <mob> rozpoczyna walkę realtime; con <mob> pokazuje wygenerowaną ocenę przeciwnika bez walki.",
        "Nowa zawartość dziedziczy liczby z Generator Core zamiast wymagać ręcznego balansowania.",
    ]
    HELP_TOPICS["score"] = [
        "score pokazuje Level postaci i EXP, aktywne klasy i Biegłość, Soul Level/Tier i Soul Weapon Mastery, HP, Manę, statystyki, portfel i lokację.",
        "Ocena siły postaci i terenu działa w tej samej skali Generator Core 1-400.",
        "Wartości terenu wynikają z wygenerowanych lokacji i realnych spawnów, a nie ze starej ręcznej tabeli.",
    ]
    HELP_TOPICS["statystyki"] = [
        "Sześć automatycznych statystyk to Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma.",
        "Statystyki nie mają twardego limitu. Każda ma własny EXP i wygenerowany próg rosnący także powyżej 400; nie rozdzielasz punktów ręcznie.",
        "Powyżej 400 Generator Core skaluje wymagany EXP i nagrodę statystyczną z zachowaniem jakości źródła: endgame pozostaje opłacalny, a słabe moby nie stają się dobrym farmem.",
        "Level postaci, wyposażenie, rasa, klasa i statystyki wspólnie wpływają na parametry bojowe.",
        "staty info pokazuje bazę, wartość efektywną, bieżący EXP do następnego punktu i bonusy wyposażenia.",
    ]
    HELP_TOPICS["dusza"] = [
        f"Broń Duszy ma Soul Level 1-{SOUL_MAX_LEVEL} i {SOUL_MAX_TIER} Tierów.",
        "Progi Tierów, moc, bonusy i wymagania Prób są generowane z jednej krzywej Generator Core.",
        "Soul Level jest osobną osią od Levelu postaci, Biegłości klasy i Skill Levelu. Soul Weapon Mastery 1-400 rozwija wyłącznie zwykły atak Broni Duszy i zdobywa XP tylko za jego trafienia.",
        "dusza info pokazuje aktualne progi i stan Prób; po spełnieniu warunków użyj unlock.",
    ]
    HELP_TOPICS["aoe"] = [
        "Skille i spelle obszarowe trafiają dostępne cele zgodnie z wygenerowanym rodzajem umiejętności.",
        "Odblokowanie 1-400, koszt Many, cooldown i bazowa moc pochodzą z Generator Core.",
        "Własny Skill Level 1-400 dalej skaluje końcową moc umiejętności po jej odblokowaniu.",
        "Pełne aktualne wartości: help <nazwa skilla> albo skill info <nazwa>.",
    ]
    HELP_TOPICS["umiejetnosci"] = [
        "Każda z 14 klas ma wygenerowaną linię skilli/spelli rozłożoną po Biegłości 1-400.",
        "Skill Level każdej poznanej umiejętności ma zakres 1-400 i korzysta z jednej wygenerowanej krzywej mocy/cooldownu.",
        "Damage, heal, guard, drain, boost, Mana i cooldown nie są balansowane ręcznie per skill; wylicza je Generator Core z rodzaju i etapu umiejętności.",
    ]
    HELP_TOPICS["profesje"] = [
        "Osiem profesji oraz osiem odpowiadających narzędzi rozwijają się 1-400.",
        "EXP, progi, czasy akcji, zasoby, ich odblokowania, ceny i receptury pochodzą z Generator Core.",
        "Nowy zasób albo receptura po dodaniu do rejestru otrzymuje etap z powiązań i wygenerowane wymagania; nie wymaga ręcznej liczby levelu.",
        "Narzędzia nie mają trwałości i nie psują się.",
    ]
    HELP_TOPICS["tempo_profesji"] = [
        "Czas każdej aktywności profesyjnej jest generowany z typu narzędzia i poziomu profesji 1-400.",
        "Nie istnieje osobna ręcznie ustawiona dawna krzywa; jeden wzór obsługuje całą progresję.",
        "Komendy informacji o narzędziu pokazują aktualny czas wyliczony przez Generator Core.",
    ]
    HELP_TOPICS["narzedzia200"] = [
        "Narzędzia mają zakres 1-400, a ich Tiery są rozłożone automatycznie przez Generator Core.",
        "Tool XP, progi Tierów i bonusy nie wymagają osobnej tabeli dla każdego levelu.",
        "Narzędzia nie mają durability.",
    ]
    HELP_TOPICS["wiecej_ryb"] = [
        "Gatunki ryb są rozłożone przez Generator Core po progresji Wędki 1-400.",
        "atlas ryby pokazuje bieżący wygenerowany próg każdego gatunku; łowisko wykorzystuje tę samą wartość.",
        "Dodanie nowego gatunku nie wymaga ręcznego ustawiania ceny ani progu.",
    ]
    HELP_TOPICS["hp_mobow"] = [
        "HP i obrażenia każdego moba i bossa są generowane z etapu 1-400, rangi i miejsca w świecie.",
        "Ta sama zasada obejmuje świat, Kryptę, Wieżę Astralną, lochy mityczne, profesyjne i nieskończone piętra.",
        "Ręczne stare HP/damage nie jest źródłem aktywnego balansu.",
    ]
    HELP_TOPICS["soul_xp_bloki"] = [
        "Soul XP 1-400 korzysta z jednej krzywej Generator Core.",
        "Nagroda i wymagany próg są wyliczane z aktualnego etapu; nie ma osobnego historycznego bloku dawnych poziomów.",
    ]
    HELP_TOPICS["progresja400"] = [
        "Level postaci, Biegłość, Soul, Skill Level, profesje i narzędzia korzystają z progresji 1-400; sześć statystyk bazowych rozwija się bez twardego limitu, ale ich bazowy profil rasa+klasa nie jest generowany.",
        "Moby, questy, przedmioty, receptury i zasoby dziedziczą etap z grafu świata i relacji między treścią.",
        "Balance Validator sprawdza komplet rejestrów po zbudowaniu gry.",
    ]
    HELP_TOPICS["questy_kowalstwa_1_200"] = [
        "Zlecenia Kowalstwa korzystają z wygenerowanego etapu wymaganych materiałów i produktów.",
        "Wymagany poziom, Profession XP, Tool XP, Character XP i pieniądze są liczone przez Generator Core.",
    ]
    HELP_TOPICS["questy_gotowania_1_200"] = [
        "Zlecenia Gotowania korzystają z wygenerowanego etapu potraw i składników 1-400.",
        "Wymagania i nagrody są pobierane z Generator Core, nie z dawnej ręcznej drabinki.",
    ]
    HELP_TOPICS["questy_mikstur_orina"] = [
        "Zlecenia Alchemii korzystają z wygenerowanego etapu mikstur i składników 1-400.",
        "Wymagania i nagrody są pobierane z Generator Core.",
    ]
    for topic in ("balans 0865", "balans 0866", "balans 0874"):
        if topic in HELP_TOPICS:
            HELP_TOPICS[topic] = [
                "To historyczny opis dawnego wydania i nie opisuje aktywnego balansu v0.27.1.",
                "Aktualny balans pochodzi z Generator Core; główne osie mają zakres 1-400, a statystyki są nielimitowane. Wpisz help generator.",
            ]
    HELP_TOPICS["atlas_kompletny"] = [
        "Atlasy ryb, rud, drewna i ziół pokazują ręcznie zaprojektowane progi; Generator Core ich nie nadpisuje.",
        "Zmiana balansu liczbowego generatora nie zmienia wymagań ani kolejności odblokowania zasobów.",
        "Użyj atlas ryby, atlas rudy, atlas drewno albo atlas ziola; szczegóły zasobu pokazują jego aktualny wygenerowany próg.",
    ]
    HELP_TOPICS["generator"] = [
        f"Generator Core {GENERATOR_CORE_VERSION} działa w trybie NUMERIC-ONLY: zarządza tylko liczbami balansu.",
        f"Po starcie waliduje {GENERATOR_CORE_AUDIT['mobs']} mobów, {GENERATOR_CORE_AUDIT['items']} przedmiotów, {GENERATOR_CORE_AUDIT['quests']} questów, {GENERATOR_CORE_AUDIT['skills']} skilli/spelli, {GENERATOR_CORE_AUDIT['recipes']} receptur i {GENERATOR_CORE_AUDIT['rooms']} lokacji.",
        "Może wyliczać HP, damage, EXP, ceny, nagrody, drop-rate, cooldown, koszt many, siłę efektów, czasy i inne wartości liczbowe.",
        "Nie może zmieniać nazw, ID, progów odblokowania, wymagań EQ, struktury questów/receptur, kluczy statystyk, klasowej tożsamości EQ, atlasów, gate'ów terenu ani opisów.",
        "Bazowe statystyki rasy/klasy są ręcznie projektowane. Skill unlock 1/10/20...400, Soul Milestones, progi profesji/narzędzi i wymagania zawartości są chronione przed Generatorem.",
        f"Semantic Guard: {'PASS' if GENERATOR_CORE_AUDIT.get('semantic_preserved') else 'FAIL'}. Generator nie może wystartować po zmianie chronionej semantyki.",
    ]
    HELP_TOPICS["hp_bossow_lochow"] = [
        "Bossowie lochów nie korzystają już z ręcznego wzoru HP na piętro.",
        "Generator Core wyznacza etap z piętra/rodzaju lochu, a następnie liczy HP, damage, EXP i walutę z rangi bossa oraz wspólnej krzywej 1-400.",
        "Nieskończone piętra powyżej zakresu progresji są bezpiecznie domykane do etapu 400 zamiast tworzyć niekontrolowany power creep.",
        "consider pokazuje aktualne wartości wygenerowane przez ten sam system.",
    ]
    HELP_TOPICS["quest"] = [
        "quest pokazuje aktywny dziennik; quest list <NPC> pokazuje ofertę, quest accept <numer> przyjmuje zadanie, quest info pokazuje szczegóły, a oddaj quest kończy gotowe zadanie.",
        "Generator Core nie tworzy ani nie zmienia wymagań questów. Globalnej blokady Character Level na questy nie ma; obowiązują tylko ręcznie zaprojektowane wymagania danego zadania.",
        "Każdy nowo przyjęty cel zaczyna od 0/x i liczy wyłącznie zdarzenia wykonane po przyjęciu.",
        "Po wykonaniu celu dziennik pokazuje: ZAKTUALIZOWANO — GOTOWE DO ODDANIA.",
        "EXP, Soul XP, Stat XP, Profession/Tool XP i pieniądze z questów są liczone przez Generator Core z etapu i nakładu pracy.",
    ]
    HELP_TOPICS["receptury"] = [
        "receptury pokazuje wygenerowane przepisy; receptury craft, cook, alchemia i jubilerstwo filtrują listę.",
        "Progi profesji/narzędzia, składniki, ilości i produkty receptur są ręcznie zaprojektowane i Generator Core ich nie zmienia.",
        "Generator wylicza tylko liczbowy balans receptury, np. Profession XP, Tool XP i wewnętrzny generator_level używany do balansu.",
    ]
    HELP_TOPICS["sklepy"] = [
        "shop / sklep / list / lista pokazuje numerowaną ofertę: numer, nazwa i aktualna wygenerowana cena.",
        "shop info <numer> / sklep info <numer> pokazuje pełny opis, statystyki, wymagania, cenę po rabacie oraz porównanie z aktualnie założonym EQ przed zakupem.",
        "kup <numer> lub kup <numer> <ilość> kupuje pozycję z listy; nadal można kupować także po nazwie.",
        "Ceny przedmiotów pochodzą z Generator Core i są liczone w jednej bazowej walucie; nowe przedmioty nie wymagają ręcznego wpisywania ceny.",
        "Założone EQ i Character-Bound pozostają chronione przy sprzedaży.",
    ]
    HELP_TOPICS["atlas"] = [
        "atlas pokazuje ręcznie zaprojektowane progi ryb, rud, drewna, ziół i innych zasobów.",
        "Generator Core może balansować wartości ekonomiczne i wydajność zasobów, ale nie zmienia progów atlasu ani miejsc odblokowania.",
    ]

refresh_generator_help_v0271()

# ============================================================
# v0.30.10 - FINAL HELP AUDIT
# Najnowsza warstwa nadpisuje historyczne teksty, które kłóciły się z realnym
# gameplayem. `help` pozostaje kategoriowym indeksem i prowadzi do tych tematów.
# ============================================================
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
        "Nagrody EXP, Soul, statystyk, profesji i narzędzi korzystają z Generator Core; podczas eventu x2 EXP są podwajane.",
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
    HELP_TOPICS["walka"] = [
        "k <mob> / atakuj <mob> rozpoczyna walkę realtime. uciekaj / flee ręcznie wycofuje z walki.",
        "wimpy set <1-99> ustawia automatyczną ucieczkę przy wybranym procencie HP; wimpy off wyłącza.",
        "combatlog concise, normal albo full ustawia szczegółowość komunikatów walki dla NVDA.",
        "Skille, kolejki, buffy, guardy, uniki, krytyki, drużyna i Generator Core działają na bieżących danych postaci.",
    ]
    HELP_TOPICS["podstawy"] = [
        "Soulbound v0.30.11 używa Generator Core jako źródła aktywnego balansu; bazowe statystyki rasy i klasy pozostają stałe i nie są losowane przez generator.",
        "Level postaci, Biegłość, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia mają progresję 1-400; sześć statystyk bazowych rozwija się automatycznie.",
        "Najważniejsze komendy: help, look/l/sp, exits, hp, level/lvl, xp, score, staty, dusza, eq, quest, walk/prowadz oraz / do Świątyni.",
        "k <mob> rozpoczyna walkę; con <mob> ocenia przeciwnika; wimpy set 50 może automatycznie wycofać postać przy niskim HP.",
        "eventxp pokazuje godzinny event x2 EXP. Samo help zawsze otwiera menu kategorii.",
    ]
    HELP_TOPICS["krypta"] = [
        "Zwykła Krypta ma rozgałęzione piętra i bossów blokujących zejście na wybranych poziomach.",
        "walk krypta dół prowadzi z dowolnego pokoju bieżącego piętra przed zejście na następne piętro. Samo zejście wykonujesz ręcznie.",
        "portal pokazuje odblokowane checkpointy Krypty; mapa w instancji pokazuje odkrycie bieżącego sektora.",
        "Krypta korzysta z Generator Core i może tworzyć dalsze piętra dynamicznie.",
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

refresh_help_v03010()

# ============================================================
# v0.30.11 - PARTY FOLLOW + HISTORY BUFFERS + PLAYER TRADING HELP AUDIT
# ============================================================
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
        "Jeśli Odłamek Duszy wypadnie z przeciwnika podczas wspólnej walki, każdy członek drużyny obecny w tej samej lokacji otrzymuje własny Odłamek.",
        "wspieraj / assist pomaga członkowi w walce; zasłoń / zaslon pozwala aktywnemu Strażnikowi przejmować aggro wspólnego przeciwnika w tej samej lokacji.",
        "Limit drużyny rośnie z Charyzmą lidera.",
    ]
    HELP_TOPICS["pieniadze"] = [
        "portfel / wallet / saldo pokazuje jedno wspólne saldo konta jako mithril, złoto i srebro.",
        "100 srebra = 1 złoto; 1000 złota = 1 mithril. Wewnętrznie gra zapisuje jedno saldo w srebrze.",
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

refresh_help_v03011()

# v0.30.12 - aktualizacja HELP po zmianie świata i progresji terenów.
HELP_TOPICS.setdefault("podstawy", []).append(
    "v0.30.12: rekomendacje i zakresy terenów korzystają z Levelu postaci, a nie z Biegłości klasy."
)
HELP_TOPICS.setdefault("poruszanie", []).append(
    "Stali NPC nie dzielą już jednego pokoju: gdy dawniej kilku NPC stało razem, otrzymali osobne pomieszczenia; prowadz <NPC> prowadzi bezpośrednio do jego pokoju."
)
HELP_TOPICS.setdefault("expowiska", []).append(
    "Dobór expowisk i zwykłych regionów świata opiera się na Levelu postaci 1-400. Biegłość klasy nadal rozwija klasę i odblokowuje skille/EQ, ale nie określa terenu."
)
HELP_TOPICS.setdefault("poruszanie", []).append(
    "v0.30.13: generator topologii zachowuje ręcznie zaprojektowany semantic backbone ważnych lokacji; proceduralne rozszerzenia są dołączane bez zrywania fabularnych przejść."
)
HELP_TOPICS.setdefault("generator", []).append(
    "Full World Topology Audit v0.30.13 sprawdza cały statyczny świat: osiągalność, powrót, spójność stref, wzajemność przejść, semantic backbone i kolejność prób."
)

# v0.30.14 - FULL RECIPE TEXT CONSISTENCY PASS
# Generator Core przelicza progi i ilości składników. Starsze opisy były
# ręcznie wpisane i mogły po generacji podawać inny level/ilość niż realna
# receptura. Od tej wersji liczby widoczne dla gracza są synchronizowane z
# aktywną definicją runtime.
def refresh_recipe_descriptions_v03014():
    changed_levels = 0
    changed_quantities = 0
    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):
        table = globals().get(table_name, {}) or {}
        for recipe in table.values():
            desc = str(recipe.get("desc", "") or "")
            if not desc:
                continue
            level = max(1, int(recipe.get("min_profession_level", recipe.get("generator_level", 1)) or 1))
            # Każde wystąpienie "level N" w opisie receptury jest progiem
            # tej receptury; inne poziomy są przechowywane w osobnych polach.
            new_desc, count = re.subn(r"(?i)\blevel\s+\d+\b", f"level {level}", desc)
            if count and new_desc != desc:
                changed_levels += 1
                desc = new_desc

            ingredients = recipe.get("ingredients") or {}
            if len(ingredients) == 1:
                actual_qty = max(1, int(next(iter(ingredients.values())) or 1))
                # Synchronizuj pierwszy tekstowy licznik "X sztuk(i)" odnoszący
                # się do pojedynczego składnika. Nie dotykamy liczby produktu.
                m = re.search(r"(?i)\b\d+\s+sztuk(?:a|i|ę)?\b", desc)
                if m:
                    old = m.group(0)
                    suffix = old[old.find(' '):]
                    replacement = f"{actual_qty}{suffix}"
                    if replacement != old:
                        desc = desc[:m.start()] + replacement + desc[m.end():]
                        changed_quantities += 1
            recipe["desc"] = desc
    return {"level_descriptions_fixed": changed_levels, "ingredient_descriptions_fixed": changed_quantities}

V03014_RECIPE_TEXT_AUDIT = refresh_recipe_descriptions_v03014()

# ============================================================
# v0.30.16 - FULL EQUIPMENT NAME AUDIT / UNIQUE PROGRESSION NAMES
# ============================================================
# W v0.30.16 klasowe EQ było formalnie unikalne, ale kolejne progi różniły
# się niemal wyłącznie sufiksem +10, +20, ... +400. Dla czytnika ekranu
# brzmiało to jak ten sam przedmiot z inną cyfrą. Od v0.30.16 Biegłość
# pozostaje wymaganiem/opisem, natomiast sama nazwa dostaje unikalny epitet.
# ID, statystyki, ceny, sety, dropy i wymagania pozostają bez zmian.
V03016_EQ_MASTERY_EPITHETS = {
    1: "Początku",
    10: "Próby",
    20: "Hartu",
    30: "Szlaku",
    40: "Przebudzenia",
    50: "Żaru",
    60: "Przełomu",
    70: "Triumfu",
    80: "Chwały",
    90: "Weterana",
    100: "Mistrzostwa",
    110: "Niezłomności",
    120: "Dominacji",
    130: "Dziedzictwa",
    140: "Szczytu",
    150: "Potęgi",
    160: "Przeznaczenia",
    170: "Arcymistrza",
    180: "Wiecznego Marszu",
    190: "Nieugiętości",
    200: "Wieczności",
    210: "Pradawnego Echa",
    220: "Korony",
    230: "Gwiezdnego Progu",
    240: "Transcendencji",
    250: "Bezkresu",
    260: "Nieśmiertelności",
    270: "Nieskończonego Szlaku",
    280: "Astralnego Wzniesienia",
    290: "Wielkiego Przełomu",
    300: "Pradawnej Potęgi",
    310: "Odwiecznej Chwały",
    320: "Pierwotnego Dziedzictwa",
    330: "Nieugaszonego Żaru",
    340: "Bezgwiezdnego Horyzontu",
    350: "Mitycznej Korony",
    360: "Absolutnego Mistrzostwa",
    370: "Władzy nad Losem",
    380: "Końca Świata",
    390: "Ostatniej Granicy",
    400: "Transcendentnego Dziedzictwa",
    410: "Przekroczenia",
    420: "Gwiezdnego Tronu",
    430: "Wiecznego Echa",
    440: "Serca Otchłani",
    450: "Korony Gwiazd",
    460: "Sądu Horyzontu",
    470: "Nieskończonego Pulsu",
    480: "Kosmicznej Pieczęci",
    490: "Pradawnego Rezonansu",
    500: "Świtu Absolutu",
    510: "Drogi Przeznaczenia",
    520: "Oka Wszechświata",
    530: "Wiecznej Iskry",
    540: "Transcendentnego Znaku",
    550: "Głosu Nieskończoności",
    560: "Ostatecznego Horyzontu",
    570: "Duszy Kosmosu",
    580: "Korony Wieczności",
    590: "Apogeum",
    600: "Absolutu Duszy",
}

V03016_ARTIFACT_EPITHETS = {
    2: "Przebudzenia",
    3: "Rezonansu",
    4: "Harmonii",
    5: "Rozkwitu",
    6: "Ascendencji",
    7: "Pradawnej Mocy",
    8: "Wieczności",
    9: "Nieskończoności",
    10: "Transcendencji",
}


def _v03016_add_legacy_item_alias(item, old_name):
    old_name = str(old_name or "").strip()
    if not old_name:
        return
    aliases = list(item.get("aliases") or ())
    if old_name != item.get("name") and old_name not in aliases:
        aliases.append(old_name)
    if aliases:
        item["aliases"] = aliases
    item.setdefault("legacy_display_name_v03015", old_name)


def _v03016_slot_label(item):
    slot = str(item.get("slot") or "")
    spec = CLASS_EQUIPMENT_SLOT_DEFS.get(slot)
    if spec:
        return str(spec[0])
    return {
        "ring": "Pierścień", "charm": "Talizman", "necklace": "Naszyjnik",
        "head": "Hełm", "body": "Pancerz", "hands": "Rękawice",
        "legs": "Nogawice", "feet": "Buty",
    }.get(slot, "Wyposażenie")


def _v03016_class_eq_name(item_id, item):
    class_name = str(item.get("required_class") or "").strip()
    mastery = max(1, int(item.get("required_mastery", 1) or 1))
    epithet = V03016_EQ_MASTERY_EPITHETS.get(mastery, f"Biegłości {mastery}")

    if item.get("legendary_class_relic"):
        base_set = str(CLASS_EQUIPMENT_SETS.get(class_name, {}).get("set_name") or class_name)
        return f"Relikwiarz {base_set} {epithet}"

    slot_label = _v03016_slot_label(item)
    set_name = str(item.get("class_set_name") or CLASS_EQUIPMENT_SETS.get(class_name, {}).get("set_name") or class_name)
    return f"{slot_label} {set_name} {epithet}"


def apply_equipment_name_pass_v03016():
    renamed_class = 0
    renamed_artifacts = 0
    for item_id, item in ITEMS.items():
        if item.get("type") != "armor":
            continue
        old_name = str(item.get("name") or item_id)
        new_name = None

        if item.get("required_class"):
            new_name = _v03016_class_eq_name(item_id, item)
        else:
            match = re.fullmatch(r"v017_artifact_.+_t(\d+)", str(item_id))
            if match:
                artifact_tier = int(match.group(1))
                epithet = V03016_ARTIFACT_EPITHETS.get(artifact_tier)
                if epithet:
                    base = re.sub(r"\s*\+\d+\s*$", "", old_name).strip()
                    new_name = f"{base} {epithet}"

        if new_name and new_name != old_name:
            item["name"] = new_name
            _v03016_add_legacy_item_alias(item, old_name)
            if item.get("required_class"):
                renamed_class += 1
            else:
                renamed_artifacts += 1

            # Katalogi kolekcji przechowują tekst nazwy osobno od ITEMS.
            for catalog_name in (
                "UNIQUE_ITEM_COLLECTION_CATALOG",
                "EQUIPMENT_COLLECTION_CATALOG",
            ):
                catalog = globals().get(catalog_name)
                if isinstance(catalog, dict) and item_id in catalog:
                    catalog[item_id] = new_name

    return {
        "class_equipment_renamed": renamed_class,
        "artifact_variants_renamed": renamed_artifacts,
    }


V03016_EQUIPMENT_NAME_PASS = apply_equipment_name_pass_v03016()


def equipment_name_audit_v03016():
    errors = []
    warnings = []
    armor_rows = [
        (item_id, item)
        for item_id, item in ITEMS.items()
        if item.get("type") == "armor"
    ]
    class_rows = [(iid, item) for iid, item in armor_rows if item.get("required_class")]

    # 1. Nazwy wszystkich pancerzy muszą być globalnie unikalne.
    seen = {}
    for item_id, item in armor_rows:
        key = normalize_lookup_text(item.get("name", ""))
        if not key:
            errors.append(f"empty equipment name {item_id}")
            continue
        if key in seen:
            errors.append(
                f"duplicate equipment name {item.get('name')}: {seen[key]} / {item_id}"
            )
        else:
            seen[key] = item_id

    # 2. Klasowe EQ nie może wrócić do schematu +liczba ani kończyć samą cyfrą.
    for item_id, item in class_rows:
        name = str(item.get("name") or "")
        if re.search(r"\+\d+\s*$", name) or re.search(r"\s\d+\s*$", name):
            errors.append(f"numeric class equipment name {item_id}: {name}")
        mastery = max(1, int(item.get("required_mastery", 1) or 1))
        expected = V03016_EQ_MASTERY_EPITHETS.get(mastery)
        if expected and expected not in name:
            errors.append(f"missing mastery epithet {item_id}: {name}")

    # 3. Każda klasa / styl / slot ma inne nazwy na każdym progu Biegłości.
    groups = {}
    for item_id, item in class_rows:
        if item.get("legendary_class_relic"):
            group = (item.get("required_class"), "relic", "necklace")
        elif item.get("legendary_set_loot"):
            group = (item.get("required_class"), "legendary_set", item.get("slot"))
        else:
            group = (
                item.get("required_class"),
                item.get("class_equipment_style", 1),
                item.get("slot"),
            )
        groups.setdefault(group, []).append((item_id, normalize_lookup_text(item.get("name", ""))))
    for group, rows in groups.items():
        names = [name for _iid, name in rows]
        if len(names) != len(set(names)):
            errors.append(f"repeated progression names {group}")

    plus_numeric_armor = [
        iid for iid, item in armor_rows
        if re.search(r"\+\d+\s*$", str(item.get("name") or ""))
    ]
    if plus_numeric_armor:
        errors.append(f"equipment +number suffix remains: {plus_numeric_armor[:10]}")

    return {
        "version": "0.30.16",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "armor_items": len(armor_rows),
        "class_armor_items": len(class_rows),
        "unique_armor_names": len(seen),
        "numeric_suffix_armor_names": len(plus_numeric_armor),
        **V03016_EQUIPMENT_NAME_PASS,
    }


EQUIPMENT_NAME_AUDIT_V03016 = equipment_name_audit_v03016()
if EQUIPMENT_NAME_AUDIT_V03016.get("error_count"):
    raise RuntimeError(
        "Equipment Name Audit v0.30.16 failed: " +
        "; ".join(EQUIPMENT_NAME_AUDIT_V03016.get("errors", [])[:20])
    )

HELP_TOPICS.setdefault("eq", []).append(
    "v0.30.16: klasowe EQ wszystkich 14 klas ma unikalne nazwy progresji. Nazwa nie jest już tym samym przedmiotem z +10/+20/+30; Biegłość pozostaje w wymaganiu i opisie."
)
HELP_TOPICS.setdefault("eq", []).append(
    "Stare numerowane nazwy EQ pozostają aliasami wyszukiwania, więc wcześniejsze komendy nadal mogą rozpoznać stary przedmiot."
)

HELP_TOPICS.setdefault("eq", []).append(
    "v0.30.16: klasy nie mają już identycznych wartości bazowych. Berserker kieruje budżet w Siłę, Strażnik w Kondycję, Mag w Inteligencję, Kapłan w Siłę Woli, a każda z 14 klas ma własne proporcje i właściwości EQ."
)
HELP_TOPICS.setdefault("eq", []).append(
    "Różnią się też sloty: rękawice i pierścienie są bardziej ofensywne, pancerz i nogawice bardziej przeżywalnościowe. Łączny budżet danego Tieru pozostaje kontrolowany."
)
HELP_TOPICS.setdefault("eq", []).append(
    "Skróty zakładania: zh, zz, zr, zn, zb, zp, zt, zp1/zp2, zt1/zt2, zna, znar, zpas, zpel, zkar, zrel. zp/zt automatycznie wybierają właściwy podwójny slot."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.16 - Unique Class Equipment Identity"
LATEST_CHANGES = [
    "Pełny audyt nazw EQ: 23 238 pancerzy ma unikalne nazwy; 0 nazw progresji kończy się +liczba.",
    "14 klas ma własne proporcje dwóch bazowych statystyk EQ oraz własne właściwości procentowe; klasy nie są już statystycznymi kopiami.",
    "Fizyczne klasy nadal używają Siły + Kondycji, magiczne Inteligencji + Siły Woli, ale rozkład zależy od klasy i slotu.",
    "Skróty NVDA do zakładania EQ: zh, zz, zr, zn, zb, zp, zt, zp1/zp2, zt1/zt2, zna, znar, zpas, zpel, zkar, zrel; skrót bez argumentu pokazuje numerowaną listę.",
    "Stare numerowane nazwy EQ pozostają aliasami wyszukiwania; brak wipe i brak zmiany ID przedmiotów.",
]

# v0.30.14 - FULL GAME CROSS-SYSTEM AUDIT
# Ten audyt celowo działa po Generator Core i po wszystkich późnych patchach.
# Sprawdza nie tylko pojedyncze rekordy, ale też relacje pomiędzy systemami.
def full_game_audit_v03014():
    errors = []
    warnings = []
    summary = {}

    def require(condition, message):
        if not condition:
            errors.append(str(message))

    # Wbudowane audyty muszą być czyste.
    for audit_name in (
        "GENERATOR_CORE_AUDIT", "WORLD_TOPOLOGY_AUDIT", "WORLD_LOGIC_AUDIT",
        "FULL_WORLD_TOPOLOGY_AUDIT_V03013", "EQUIPMENT_NAME_AUDIT_V03016", "CLASS_EQ_IDENTITY_AUDIT_V03016",
    ):
        audit = globals().get(audit_name, {}) or {}
        require(int(audit.get("error_count", 0) or 0) == 0,
                f"{audit_name}: {audit.get('errors', [])[:5]}")

    # Klasy i rasy.
    class_types = {row[0]: row[1] for row in CLASSES}
    require(len(class_types) == 14, f"classes={len(class_types)}")
    require(all(kind in ("physical", "magic") for kind in class_types.values()),
            "invalid class archetype")
    race_names = [row[0] for row in RACES]
    require(len(race_names) == 14 and len(set(race_names)) == 14,
            "races are not 14 unique entries")
    for row in RACES:
        require(sum(int(v) for v in row[2:7]) == 50,
                f"race base stat budget {row[0]}")

    # Skille/spelle wszystkich klas.
    all_skills = []
    skill_ids = {}
    skill_names = {}
    for class_name in class_types:
        rows = CLASS_SKILLS.get(class_name, [])
        require(len(rows) == len(_V0922_MASTERY_LEVELS) * 3, f"{class_name}: skills={len(rows)}")
        for skill in rows:
            all_skills.append((class_name, skill))
            sid = str(skill.get("id", ""))
            sname = normalize_lookup_text(skill.get("name", ""))
            if sid in skill_ids:
                errors.append(f"duplicate skill id {sid}")
            skill_ids[sid] = class_name
            if sname in skill_names:
                errors.append(f"duplicate skill name {skill.get('name')}")
            skill_names[sname] = sid
            require(1 <= int(skill.get("unlock", 0) or 0) <= CLASS_MASTERY_MAX_LEVEL,
                    f"skill unlock {sid}")
            require(int(skill.get("cooldown", 0) or 0) >= 0,
                    f"negative cooldown {sid}")
            require(int(skill.get("mana", 0) or 0) >= 0,
                    f"negative mana {sid}")
            require(not re.search(r"\s\d+$", str(skill.get("name", ""))),
                    f"numeric skill name {sid}")
    require(len(_FINAL_SKILL_HELP_SEARCH_ROWS) == len(all_skills),
            "skill HELP index incomplete")

    # Klasowe EQ: dwie bazowe statystyki dla każdego klasowego pancerza.
    class_armor = 0
    physical = {c for c, kind in class_types.items() if kind == "physical"}
    for item_id, item in ITEMS.items():
        class_name = item.get("required_class")
        if not class_name or item.get("type") != "armor":
            continue
        class_armor += 1
        present = set()
        if int(item.get("affix_amount", 0) or 0) > 0:
            present.add(item.get("affix"))
        present.update(
            stat for stat, amount in (item.get("stats") or {}).items()
            if int(amount or 0) > 0
        )
        expected = {"strength", "constitution"} if class_name in physical else {"intelligence", "willpower"}
        require(expected.issubset(present),
                f"class armor stats {item_id}: {sorted(present)}")

    # NPC i ich prywatne pokoje/questy.
    room_npcs = {}
    for npc_id, npc in NPCS.items():
        room_id = npc.get("room")
        require(room_id in ROOMS, f"NPC room missing {npc_id}:{room_id}")
        room_npcs.setdefault(room_id, []).append(npc_id)
        if npc.get("quest"):
            require(npc.get("quest") in QUESTS,
                    f"NPC quest missing {npc_id}:{npc.get('quest')}")
    for room_id, npc_ids in room_npcs.items():
        require(len(npc_ids) <= 1,
                f"multiple static NPCs in {room_id}: {npc_ids}")

    # Questy: relacje i brak globalnej blokady Character Level.
    virtual_kill_targets = set()
    for mob in MOB_TEMPLATES.values():
        if mob.get("quest_target"):
            virtual_kill_targets.add(str(mob.get("quest_target")))
        virtual_kill_targets.update(str(v) for v in (mob.get("quest_targets") or ()))
    for quest_id, quest in QUESTS.items():
        prerequisite = quest.get("requires_quest")
        if prerequisite:
            require(prerequisite in QUESTS,
                    f"quest prerequisite missing {quest_id}:{prerequisite}")
        for key in ("reward_items", "accept_items"):
            for item_id in (quest.get(key) or {}):
                require(item_id in ITEMS,
                        f"quest {quest_id} {key} missing {item_id}")
        kind = quest.get("kind")
        target = quest.get("target")
        if kind in ("collect", "collect_resource") and target not in (None, "any"):
            require(target in ITEMS, f"quest item target missing {quest_id}:{target}")
        if kind == "kill" and target not in (None, "any"):
            target_text = str(target)
            dynamic_crypt = bool(re.fullmatch(r"crypt_boss_\d+", target_text))
            require(target in MOB_TEMPLATES or target_text in virtual_kill_targets or dynamic_crypt,
                    f"quest mob target missing {quest_id}:{target}")
        if kind == "collect_resource_set":
            for item_id in (quest.get("resource_targets") or {}):
                require(item_id in ITEMS,
                        f"quest resource target missing {quest_id}:{item_id}")
        if kind == "craft_set":
            for item_id in (quest.get("targets") or ()):
                require(item_id in ITEMS,
                        f"quest craft target missing {quest_id}:{item_id}")
        if kind == "deliver_npc":
            require(quest.get("target_npc") in NPCS,
                    f"quest target NPC missing {quest_id}:{quest.get('target_npc')}")
            require(quest.get("quest_item") in ITEMS,
                    f"quest delivery item missing {quest_id}:{quest.get('quest_item')}")
        for forbidden in ("required_character_level", "min_character_level", "character_level_required"):
            require(forbidden not in quest,
                    f"Character Level quest gate {quest_id}:{forbidden}")

    # Łańcuchy questów nie mogą mieć pętli.
    for start in QUESTS:
        seen = set()
        current = start
        while current in QUESTS and QUESTS[current].get("requires_quest"):
            if current in seen:
                errors.append(f"quest dependency cycle {start}")
                break
            seen.add(current)
            current = QUESTS[current].get("requires_quest")

    # Receptury: referencje, progi i tekst widoczny dla gracza.
    recipe_count = 0
    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):
        table = globals().get(table_name, {}) or {}
        recipe_count += len(table)
        for recipe_id, recipe in table.items():
            for item_id in (recipe.get("ingredients") or {}):
                require(item_id in ITEMS,
                        f"{table_name} ingredient missing {recipe_id}:{item_id}")
            output_id = recipe.get("output")
            if output_id:
                require(output_id in ITEMS,
                        f"{table_name} output missing {recipe_id}:{output_id}")
            level = int(recipe.get("generator_level", 0) or 0)
            require(1 <= level <= PROFESSION_MAX_LEVEL, f"{table_name} level {recipe_id}:{level}")
            desc = str(recipe.get("desc", "") or "")
            match = re.search(r"(?i)level\s*(\d+)", desc)
            if match:
                require(int(match.group(1)) == int(recipe.get("min_profession_level", 0) or 0),
                        f"recipe text level mismatch {table_name}:{recipe_id}")
            quantities = re.findall(r"(?i)(\d+)\s+sztuk", desc)
            if quantities and len(recipe.get("ingredients") or {}) == 1:
                actual = sum(int(v or 0) for v in (recipe.get("ingredients") or {}).values())
                require(int(quantities[0]) == actual,
                        f"recipe text quantity mismatch {table_name}:{recipe_id}")

    # Statyczne spawny.
    for room_id, mob_id in MOB_SPAWNS:
        require(room_id in ROOMS, f"spawn room missing {room_id}:{mob_id}")
        require(mob_id in MOB_TEMPLATES, f"spawn mob missing {room_id}:{mob_id}")

    # HELP: aliasy do tematów lub czterech wirtualnych widoków menu.
    virtual_help = {"tematy", "komendy", "wszystko", "kategorie"}
    for alias, target in HELP_TOPIC_ALIASES.items():
        require(target in HELP_TOPICS or target in virtual_help,
                f"HELP alias target missing {alias}:{target}")

    # Wszystkie główne krzywe progresji 1-600 muszą być monotoniczne.
    for axis in generator_core_v027.AXIS_CURVES:
        values = [generator_core_v027.axis_requirement(axis, level) for level in range(1, PROGRESSION_MAX_LEVEL + 1)]
        require(all(b >= a for a, b in zip(values, values[1:])),
                f"nonmonotonic progression axis {axis}")

    summary.update({
        "classes": len(class_types), "races": len(race_names),
        "skills": len(all_skills), "class_armor": class_armor,
        "npcs": len(NPCS), "quests": len(QUESTS), "recipes": recipe_count,
        "spawns": len(MOB_SPAWNS), "mobs": len(MOB_TEMPLATES),
        "items": len(ITEMS), "rooms": len(ROOMS),
        "help_topics": len(HELP_TOPICS), "command_aliases": len(COMMAND_ALIASES),
        "recipe_text_levels_fixed": V03014_RECIPE_TEXT_AUDIT.get("level_descriptions_fixed", 0),
        "recipe_text_quantities_fixed": V03014_RECIPE_TEXT_AUDIT.get("ingredient_descriptions_fixed", 0),
        "equipment_unique_names": EQUIPMENT_NAME_AUDIT_V03016.get("unique_armor_names", 0),
        "class_equipment_renamed": V03016_EQUIPMENT_NAME_PASS.get("class_equipment_renamed", 0),
        "equipment_numeric_suffix_names": EQUIPMENT_NAME_AUDIT_V03016.get("numeric_suffix_armor_names", 0),
    })
    return {
        "version": "0.30.14", "error_count": len(errors),
        "warning_count": len(warnings), "errors": errors,
        "warnings": warnings, **summary,
    }

FULL_GAME_AUDIT_V03014 = full_game_audit_v03014()
if FULL_GAME_AUDIT_V03014.get("error_count"):
    raise RuntimeError(
        "Full Game Audit v0.30.14 failed: " +
        "; ".join(FULL_GAME_AUDIT_V03014.get("errors", [])[:20])
    )

# v0.30.14: końcowy audyt po przejściu Generator Core.
V03014_SKILL_NAME_AUDIT = _v03014_skill_name_audit()
if V03014_SKILL_NAME_AUDIT.get("error_count"):
    raise RuntimeError(
        "Final Skill/Spell Name Audit v0.30.14 failed: " +
        "; ".join(V03014_SKILL_NAME_AUDIT.get("errors", [])[:20])
    )
HELP_TOPICS.setdefault("skille", []).append(
    "v0.30.14: pełny audyt nazw 14 klas usunął numerowane serie skilli/spelli; każda umiejętność ma unikalną nazwę, a dawne nazwy pozostają aliasami kompatybilności."
)
HELP_TOPICS.setdefault("biegłość", []).append(
    "Nazwy alternatywnych umiejętności progów Biegłości są unikalne; stare formy typu 'Furia Berserkera 80' nadal działają jako aliasy."
)

# v0.30.16 - STAT-BASED DAMAGE / MANA + ROOM-WIDE AOE AUDIT
def full_combat_scaling_audit_v03015():
    errors = []
    physical_classes = {name for name, kind, *_ in CLASSES if kind == "physical"}
    magical_classes = {name for name, kind, *_ in CLASSES if kind == "magic"}
    offensive = {"damage", "aoe_damage", "execute", "drain"}
    checked = 0
    dexterity_classes = {"Łotrzyk", "Łowca"}
    flexible_classes = {"Mnich", "Mec", "Inżynier"}
    for class_name, skills in CLASS_SKILLS.items():
        if class_name in dexterity_classes:
            expected = "dexterity"
        elif class_name in magical_classes:
            expected = "intelligence"
        elif class_name in physical_classes and class_name not in flexible_classes:
            expected = "strength"
        else:
            expected = None
        for skill in skills:
            if skill.get("kind") not in offensive:
                continue
            checked += 1
            actual = skill.get("scale")
            if class_name in flexible_classes:
                if actual not in {"strength", "dexterity", "intelligence"}:
                    errors.append(f"{class_name}/{skill.get('id')}: invalid branch scale={actual}")
            elif expected is not None and actual != expected:
                errors.append(f"{class_name}/{skill.get('id')}: scale={actual} expected={expected}")
    base = generator_core_v027.character_mana_base(100, 50, 50)
    int_plus = generator_core_v027.character_mana_base(100, 60, 50)
    wil_plus = generator_core_v027.character_mana_base(100, 50, 60)
    if int_plus <= base or wil_plus <= base:
        errors.append("INT/WIL does not increase mana")
    if int_plus - base != wil_plus - base:
        errors.append("INT/WIL mana contribution is not equal")
    if GENERATOR_CORE_VERSION != "0.36.5":
        errors.append(f"GENERATOR_CORE_VERSION={GENERATOR_CORE_VERSION}")
    return {
        "version": "0.30.19",
        "offensive_skills_checked": checked,
        "skill_scales_normalized": V03015_SKILL_SCALES_NORMALIZED,
        "mana_base": base,
        "mana_plus_10_int": int_plus,
        "mana_plus_10_will": wil_plus,
        "error_count": len(errors),
        "errors": errors,
    }

FULL_COMBAT_SCALING_AUDIT_V03015 = full_combat_scaling_audit_v03015()
if FULL_COMBAT_SCALING_AUDIT_V03015.get("error_count"):
    raise RuntimeError(
        "Combat/Stat Audit v0.30.16 failed: " +
        "; ".join(FULL_COMBAT_SCALING_AUDIT_V03015.get("errors", [])[:20])
    )

def aggro_cleanup_audit_v03015():
    errors = []
    room_id = next(iter(ROOMS))
    template_id = next(iter(MOB_TEMPLATES))
    max_hp = int(MOB_TEMPLATES[template_id].get("max_hp", 100) or 100)

    server = object.__new__(MudServer)
    server.sessions = set()
    server.parties = {}
    server.party_invites = {}
    server.party_protectors = {}
    server.world = type("AuditWorld", (), {"mobs": {}})()

    character = type("AuditCharacter", (), {"name": "AuditTester", "room_id": room_id})()
    session = type("AuditSession", (), {})()
    session.closed = False
    session.character = character
    session.current_hp = 100
    session.combat_mob_key = None
    session.account_id = 999999991

    ghost = MobState(
        key="audit_ghost_aggro", room_id=room_id, template_id=template_id,
        hp=max_hp, engaged_by="NieistniejacyGracz", engaged_at=12.0,
        combat_turn=3, player_hits=4,
    )
    server.world.mobs[ghost.key] = ghost
    if not server.engagement_allowed(session, ghost):
        errors.append("ghost aggro still blocks a free mob")
    if ghost.engaged_by is not None or ghost.engaged_at != 0.0:
        errors.append("ghost aggro was not cleared")

    server.sessions.add(session)
    session.combat_mob_key = "audit_owned_1"
    for key in ("audit_owned_1", "audit_owned_2"):
        server.world.mobs[key] = MobState(
            key=key, room_id=room_id, template_id=template_id, hp=max_hp,
            engaged_by=character.name, engaged_at=1.0,
        )
    released = server.release_all_engagements_for_session(session)
    if released != 2:
        errors.append(f"release_all count={released} expected=2")
    if any(server.world.mobs[key].engaged_by for key in ("audit_owned_1", "audit_owned_2")):
        errors.append("release_all left owned mob aggro behind")

    return {
        "version": "0.30.16",
        "ghost_aggro_cleared": ghost.engaged_by is None,
        "multi_mob_release_count": released,
        "error_count": len(errors),
        "errors": errors,
    }

AGGRO_CLEANUP_AUDIT_V03015 = aggro_cleanup_audit_v03015()
if AGGRO_CLEANUP_AUDIT_V03015.get("error_count"):
    raise RuntimeError(
        "Aggro Cleanup Audit v0.30.16 failed: " +
        "; ".join(AGGRO_CLEANUP_AUDIT_V03015.get("errors", [])[:20])
    )

# v0.30.16 - STAT-BASED DAMAGE / MANA + ROOM-WIDE AOE
HELP_TOPICS.setdefault("statystyki", []).extend([
    "v0.30.16: Siła bezpośrednio zwiększa moc wszystkich fizycznych skilli ofensywnych.",
    "v0.30.16: Inteligencja bezpośrednio zwiększa moc wszystkich magicznych skilli i spelli ofensywnych.",
    "Maksymalna Mana rośnie równomiernie z Inteligencją i Siłą Woli; oba staty mają taki sam udział w bazowej puli Many.",
    "Kondycja zwiększa maksymalne HP; Zręczność odpowiada m.in. za krytyk, unik i szybkość.",
])
HELP_TOPICS.setdefault("aoe", []).extend([
    "v0.30.16: ofensywne AoE trafia wszystkie żywe moby w całym pokoju, również te walczące już z innym graczem.",
    "AoE nie przejmuje aggro cudzego moba. Jeśli obszarówka dobije takiego przeciwnika, nagrody pozostają przy dotychczasowym właścicielu aggro i jego drużynie.",
    "Bez aktywnej drużyny zwykła blokada celu mówi 'walczy już z innym graczem'; tekst 'spoza twojej drużyny' jest używany dopiero, gdy naprawdę jesteś w drużynie.",
    "Osierocone aggro jest czyszczone automatycznie: mob nie pozostaje zajęty przez gracza, którego nie ma już w pokoju albo który nie walczy już z tym mobem.",
])


# ============================================================
# v0.30.17 - SKILL GRID / CHARACTER-LEVEL QUEUE / SOUL WEAPON COMBAT AUDIT
# ============================================================
def progression_combat_audit_v03017():
    errors = []
    grid = (1, *range(10, CLASS_MASTERY_MAX_LEVEL + 1, 10))
    grid_set = set(grid)
    class_names = [row[0] for row in CLASSES]

    for class_name in class_names:
        rows = CLASS_SKILLS.get(class_name, [])
        counts = {level: 0 for level in grid}
        for skill in rows:
            unlock = int(skill.get("unlock", 0) or 0)
            if class_name not in ("Inżynier","Mec") and unlock not in grid_set:
                errors.append(f"{class_name}/{skill.get('id')}: próg {unlock} poza siatką")
            elif unlock in grid_set:
                counts[unlock] += 1
            elif not (1 <= unlock <= CLASS_MASTERY_MAX_LEVEL):
                errors.append(f"{class_name}/{skill.get('id')}: nieprawidłowy próg {unlock}")
        if len(rows) != len(grid) * 3:
            errors.append(f"{class_name}: {len(rows)} skilli, oczekiwano {len(grid)*3}")
        if class_name not in ("Inżynier","Mec"):
            for level in grid:
                if counts[level] != 3:
                    errors.append(f"{class_name}: próg {level} ma {counts[level]} skilli, oczekiwano 3")

    expected_slots = {1: 10, 10: 11, 100: 20, 200: 30, 400: 50, 600: 70}
    for level, expected in expected_slots.items():
        got = min(10 + CHARACTER_MAX_LEVEL // 10, 10 + level // 10)
        if got != expected:
            errors.append(f"sloty Level {level}: {got}, oczekiwano {expected}")

    techniques = [SOUL_WEAPON_ATTACK_TECHNIQUES.get(name) for name in class_names]
    if any(not value for value in techniques):
        errors.append("brak techniki autoataku Broni Duszy dla klasy")
    if len(set(techniques)) != len(class_names):
        errors.append("techniki autoataku Broni Duszy nie są unikalne")
    weapons = [row[2] for row in CLASSES]
    if len(set(weapons)) != len(class_names):
        errors.append("nazwy Broni Duszy nie są unikalne")

    return {
        "version": "0.30.17",
        "classes": len(class_names),
        "skills": sum(len(CLASS_SKILLS.get(name, [])) for name in class_names),
        "thresholds_per_class": len(grid),
        "skills_per_threshold": 3,
        "queue_slot_checkpoints": expected_slots,
        "soul_weapon_techniques": len(set(techniques)),
        "error_count": len(errors),
        "errors": errors,
    }


PROGRESSION_COMBAT_AUDIT_V03017 = progression_combat_audit_v03017()
if PROGRESSION_COMBAT_AUDIT_V03017.get("error_count"):
    raise RuntimeError(
        "Progression/Combat Audit v0.30.17 failed: " +
        "; ".join(PROGRESSION_COMBAT_AUDIT_V03017.get("errors", [])[:30])
    )

HELP_TOPICS.setdefault("skille", []).extend([
    "Większość klas zachowuje siatkę 1, 10, 20...400 po 3 skille. Inżynier i Mec mają autorskie progi wynikające z ich projektów klasowych.",
    "Generator Core nie rozciąga już 123 skilli po przypadkowych poziomach 1-400; zachowuje zaprojektowane progi Biegłości.",
])
HELP_TOPICS.setdefault("walka", []).extend([
    "v0.30.17: zwykły autoatak jest jawnym atakiem twoją Bronią Duszy; komunikat podaje nazwę broni i klasową technikę.",
    "Ofensywne skille i spelle także korzystają z Mocy Broni Duszy. Fizyczne skaluje Siła, magiczne Inteligencja.",
])
HELP_TOPICS.setdefault("kolejka", []).append(
    "v0.30.18: sloty auto kolejki rosną z Levelem postaci: 10 na Levelu 1, +1 co 10 Leveli, maksymalnie 50 na Levelu 400. Biegłość odblokowuje skille, nie sloty."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.17 - Soul Weapon Combat + Skill Grid + Character-Level Queue"
LATEST_CHANGES = [
    "Broń Duszy jest jawną aktywną bronią autoataku; każda z 14 klas ma własną technikę ataku, a Soul Power pozostaje rdzeniem obrażeń.",
    "Broń Duszy wykonuje wyłącznie zwykły atak bronią. Skille i spelle są uruchamiane jako osobne zdolności i nie są opisywane jako ataki wykonywane przez broń. Ich dotychczasowe skalowanie obrażeń pozostaje bez zmian.",
    "Naprawiono Generator Core: 123 skille na klasę nie są już rozciągane po losowych progach. Każda klasa ma dokładnie 3 skille na 1, 10, 20...400.",
    "Sloty auto kolejki zależą od Character Level: 10 na Levelu 1, 11 na 10, 20 na 100, 30 na 200, 50 na 400.",
    "Brak wipe; ID skilli, nauczone umiejętności i zapisane kolejki pozostają kompatybilne.",
]


# v0.30.53 help additions
try:
    HELP_TOPICS.update({
      "krawiectwo":"Krawiectwo 1-400. Krawcowa Lysa, Pracownia Krawiecka. Komendy: krawiectwo, szyj <receptura>, szyj lista. Tworzy tkaniny, szaty i płaszcze.",
      "garbarstwo":"Garbarstwo 1-400. Kaletnik Soren. Komendy: garbarstwo, garbuj <receptura>, garbuj lista. Skóry bestii -> garbowana skóra -> pasy, karwasze i naramienniki.",
      "stolarstwo":"Stolarstwo 1-400. Cieśla Edric. Komendy: stolarstwo, stolarka <receptura>, stolarka lista. Obrabia drewno i tworzy totemy oraz komponenty housingu.",
      "zaklinanie":"Zaklinanie 1-400. Komnata Arkanów. Komendy: zaklinanie, zaklinaj <slot> <typ>, enchants. Jedno trwałe zaklęcie na slot; nowe zastępuje stare.",
      "jubilerstwo2":"Jubilerstwo 2.0 dodaje nowe kolczyki, pierścienie i naszyjniki w progresji do levelu 400. Użyj receptury jubilerstwo i jub <nazwa>.",
    })
except Exception:
    pass


# v0.30.54 Crafting 2.0 help
try:
    HELP_TOPICS.update({
      "jakosccraftu":"Jakość craftu v0.30.54: gotowe EQ może wyjść jako Zwykłe, Dobre, Doskonałe, Mistrzowskie lub Legendarne. Wyższa jakość realnie zwiększa bazową moc/statystyki przedmiotu.",
      "krytycznycraft":"Krytyczny craft v0.30.54: mała szansa na dodatkowy affix statystyki. Szansa rośnie z levelem profesji oraz Crafting Mastery i ma bezpieczny limit.",
      "craftmastery":"Crafting Mastery v0.30.54 jest osobne od levelu profesji i narzędzia. Rośnie od liczby udanych craftów w konkretnej kategorii. Komenda: craftmastery [filtr]. Maksymalnie 100.",
    })
except Exception:
    pass


# v0.31.7 Engineer Toolkit + profession tool audit.
HELP_TOPICS.setdefault("inzynier", []).extend([
    "v0.31.7: Inżynier ma autorski zestaw narzędzi: Auto Crossbow, Mako Gun, Bio Blaster, Scanner, Flash, Debilitator, Drill, Napalm, Launcher, Upgrade, Noise Blaster, Chainsaw, Mega Bomb i Air Anchor.",
    "Soulbound nie używa AP. Wartości źródłowej mocy są tylko wewnętrzną mocą bazową umiejętności.",
    "Upgrade <nazwa narzędzia> zapisuje trwałe ulepszenie. Bazowo dostępny jest 1 slot; Silver Gear daje drugi, Gold Battery trzeci. Upgrade reset czyści sloty.",
    "Hypercharge pasywnie wzmacnia single-target, Lindblum Assembly obszarowe narzędzia, a Improved Kinematics wydłuża efekty statusowe.",
])
HELP_TOPICS.setdefault("narzedzia", []).append(
    "v0.31.7: wszystkie 12 profesji ma dokładnie jedno kupowalne, przypisane do postaci narzędzie. Ponowny zakup tej samej postaci jest blokowany."
)

# v0.31.8: Mec support semantics + tool migration clarification.
try:
    _mec_help = HELP_TOPICS.get("mec", "")
    if isinstance(_mec_help, str) and "Support Effect" not in _mec_help:
        HELP_TOPICS["mec"] = _mec_help + (
            "\nSupport Effect to dodatkowy tryb/efekt konkretnej umiejętności Meca. "
            "Nie jest osobną bronią. Rdzeń Meca pozostaje jego jedyną Bronią Duszy."
        )
except Exception:
    pass

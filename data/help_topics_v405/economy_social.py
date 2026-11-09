"""Historyczna pomoc Soulbound v4.00.5: economy social."""

def make_topics():
    return {'gospodarka': ['Gospodarka 4.0: gospodarka ceny lub karawany; wyslij <kod> potwierdz, transport, obron, '
                'odbierz.',
                'Gospodarka zamowienia; wykonaj <kod> potwierdz — wielkie zamowienia surowcow, co dwie '
                'godziny.',
                'Gospodarka produkcja; rozbuduj <kopalnia/tartak/farma/warsztat> potwierdz; zbierz — gildia '
                'produkuje co 6 godzin. Koszty ze skarbca gildii; zbior do banku.',
                'Transport morski wymaga aktywnego statku, odpowiedniej ladowni i portu. Brak walk PvP. '
                'Towary pobierane od razu; zapis trwa w SQLite.'],
 'ocean4': ['Ocean 4.0: bitwy flot przeciw NPC, nie przeciw graczom. Aby zacząć: ocean4 cele i ocean4 atak '
            'korsarze, blokada, kraken, lewiatan lub smok.',
            'ocean4 flota; ocean4 eskorta dodaj <nr>; ocean4 eskorta usun <nr> - ustaw w porcie do dwoch '
            'okretow eskortowych.',
            'ocean4 status; ocean4 rozkaz salwa/manewr/oslona/abordaz. Abordaz tylko na oslabione okręty, '
            'nie na potwory.',
            'ocean4 odwrot potwierdz - wycofanie bez lupow; ocean4 napraw <nr> potwierdz - remont bojowego '
            'kadluba w porcie. Po bitwie odpoczynek 2 godziny. Rejsy Ocean 2.0 bez zmian.'],
 'imperium': ['Żyjące Imperia v1.34.0: garnizon, obsadz, wycofaj, rozbuduj, pobierz, wojny, raport. '
              'Kontrataki co 12 godzin, dochody co 6 godzin; twierdze nie przepadają przez bycie offline.',
              'imperium — kontrolowane przez gildie twierdze i ich obrona.',
              'imperium mury <kod> potwierdz — lider rozbudowuje zdobyte mury ze skarbca.'],
 'armia': ['armia — siła i skład armii twojej gildii.',
           'armia rekrutuj <wojownik/lucznik/mag> <ilość> potwierdz — finansowanie ze skarbca; bez '
           'całkowitego limitu oddziałów.'],
 'oblezenie': ['oblezenie <kod> rozpocznij potwierdz — lider gildii rozpoczyna trzyetapową bitwę u bramy lub '
               'posterunku twierdzy.',
               'oblezenie <kod> status; oblezenie <kod> rozkaz natarcie/ostrzal/magia/oslona; oblezenie '
               '<kod> odwrot potwierdz.',
               'Brama sprzyja natarciu, dziedziniec ostrzałowi, cytadela magii. Do 24 rozkazów, utrata '
               'jednostek, odpoczynek 4 godziny.',
               'Stara komenda oblezenie <kod> potwierdz rozpoczyna teraz bitwę trzyetapową. Przejścia świata '
               'pozostają otwarte.'],
 'aukcja': ['aukcja — 30 najnowszych ofert kup teraz i licytacji. aukcja moje — twoje oferty.',
            'aukcja wystaw <przedmiot> <ilość> <cena> — cena stała; aukcja licytacja <przedmiot> <ilość> '
            '<cena startowa> <1/6/12/24/48 godzin> — licytacja czasowa.',
            'aukcja licytuj <nr> <kwota> — blokuje pieniądze w depozycie. aukcja rozlicz [nr] — zakończenie '
            'po upływie czasu.',
            'aukcja kup <nr>; aukcja anuluj <nr>; aukcja odbierz — wypłata, również zwrot przebitej oferty. '
            'Anulowanie licytacji możliwe tylko przed pierwszą ofertą.',
            'Chronione, przypisane i założone EQ nie może zostać sprzedane.'],
 'stocznia': ['stocznia lub stocznia flota — lista posiadanych statków, typów i osobnych modułów.',
              'stocznia buduj bryg/fregata/galeon potwierdz — kolejny statek we flocie (w porcie), z '
              'wykorzystaniem surowców.',
              'stocznia wybierz <nr> — zmiana aktywnego statku w porcie. stocznia nazwij <nr> <nazwa> — '
              'zmiana nazwy.',
              'Moduły kadłuba, żagli, ładowni i nawigacji pozostają przy każdym statku; dawne rejsy Ocean '
              '2.0 nie są resetowane.'],
 'historia': ['historia / history / lifetime - trwała Historia postaci zapisywana osobno dla każdego slotu '
              'postaci.',
              'Walka: zwycięstwa, wszystkie zabite moby, bossowie, rare moby i śmierci.',
              'Zadania: łączna liczba ukończonych questów i odebranych kontraktów z Tablicy Zleceń.',
              'Profesje: wszystkie akcje profesji, liczba craftingów oraz liczba wytworzonych przedmiotów.',
              'Zbiory: od v0.9.4 dokładne ilości złowionych ryb, wydobytych rud/minerałów, drewna, ziół i '
              'znalezionych klejnotów.',
              'Świat: liczba odkrytych lokacji, wpisów Bestiariusza i rzadkich ryb.',
              'Migracja starych postaci odtwarza tylko dane rzeczywiście zapisane wcześniej: Bestiariusz, '
              'boss/rare, śmierci, questy, kontrakty, akcje profesji i eksplorację. Nie zgaduje dawnych '
              'ilości sprzedanych lub zużytych surowców.',
              'Usunięcie pojedynczej postaci usuwa również jej Historię; login i wspólny portfel konta '
              'pozostają bez zmian.'],
 'walka': ['Walka działa w czasie rzeczywistym. atakuj <mob> i k <mob> rozpoczynają starcie z wybranym '
           'zabijalnym mobem.',
           'PvP jest wyłączone. Gracze nie mogą atakować, ranić ani zabijać innych graczy; ofensywne skille '
           'i AoE wybierają wyłącznie moby.',
           'combat — pokazuje aktualny filtr logu walki.',
           'combat concise — minimalny log pod NVDA: kluczowe wydarzenia, mechaniki bossa, ostrzeżenia HP, '
           'zwycięstwo, śmierć i najważniejsze nagrody.',
           'combat normal — domyślny tryb: czyta zwykłe trafienia i używane skille, ale ogranicza techniczne '
           'szczegóły redukcji oraz Skill XP podczas walki.',
           'combat full — pełny log walki z detalami obrażeń, redukcji, Skill XP i mechanik.',
           'Ustawienie combat jest trwałe i zapisuje się osobno dla każdej postaci.',
           'flee / uciekaj — przerywa aktywną walkę realtime.'],
 'questy': ['HELP QUEST — pełna pomoc systemu zadań. Poziom postaci nie blokuje przyjęcia zadań; obowiązują '
            'tylko wymagania fabularne, klasowe i obecności właściwego NPC.',
            'quest / quest aktywne — numerowana lista wszystkich aktualnie aktywnych questów.',
            'quest ukończone / questy ukończone — osobna historia ukończonych questów, liczba ukończeń oraz '
            'pozostały cooldown zadań powtarzalnych.',
            'quest — aktywny dziennik. Po wykonaniu wszystkich celów wpis zmienia stan na ZAKTUALIZOWANO — '
            'GOTOWE DO ODDANIA.',
            'quest list — lista zadań NPC w bieżącym pokoju. Quest list <NPC> nadal działa, ale nie jest '
            'wymagane przed przyjęciem zadania.',
            'talk <NPC> — NPC reaguje na stan swoich zadań: mówi, gdy ma nowe zadanie, komentuje powrót z '
            'aktywnym zadaniem i informuje, gdy cel jest gotowy do oddania. Następnie pokazuje ofertę, ale '
            'nie przyjmuje zadania automatycznie.',
            'przyjmij 1, przyjmij 2 itd. — wystarczy podać numer zadania lokalnego NPC, bez rozmowy, quest '
            'list i bez słowa quest. Dłuższe składnie quest accept <numer> i quest przyjmij <numer> nadal '
            'działają. NPC komentuje przyjęcie i pokazuje postęp 0/x.',
            'Każdy quest po przyjęciu zaczyna od 0/x. Liczą się wyłącznie wymagane akcje wykonane po '
            'przyjęciu: nowe zabicia, połowy, zbiory, wydobycie, ścinanie, craft, rozmowy i inne zdarzenia '
            'celu. Stary zapas ani wcześniejsze zabicia nie naliczają postępu.',
            'Po każdym zdarzeniu zwiększającym licznik NVDA od razu czyta bieżący postęp. Ponowne quest / '
            'quest aktywne zawsze pobiera aktualny stan z bazy, bez starego cache.',
            'quest info <numer> — działa po quest, quest ukończone i quest list <NPC>; pokazuje NPC, opis, '
            'cel, aktualny postęp, wymagania, nagrody, powtarzalność i cooldown.',
            'quest oddaj <numer> / oddaj quest <numer> — oddaje wskazany aktywny quest, jeżeli cele są '
            'wykonane i jesteś u właściwego NPC; NPC komentuje wykonanie i osobiście przekazuje nagrodę.',
            'dostarcz <nazwa> / deliver <nazwa> — jawnie przekazuje aktywny przedmiot dostawy właściwemu '
            'NPC, np. dostarcz mapa. Rozmowa z odbiorcą nadal również może automatycznie zakończyć dostawę.',
            'quest porzuć <numer> / quest abandon <numer> — porzuca aktywny quest z ostatniej listy. Bieżący '
            'postęp przepada, ale wcześniejsze ukończenia pozostają w historii; quest można później przyjąć '
            'ponownie.',
            'Kilka questów jednego NPC może być aktywnych równocześnie. Zlecenia profesyjne są niezależne, '
            'np. Mikstury Many i Mikstury Leczenia u Orina.',
            'Questy powtarzalne zachowują osobny czas odnowienia. Problem goblinów, Plaga Trolli i Cienie w '
            'Gaju odnawiają się co 60 minut.',
            'Kartograf Eren ma pięć niezależnych zleceń: mapa patroli, plan portowych magazynów, mapa drogi '
            'do kopalni, odkrycie 5 nowych sektorów i odkrycie 1 nowego sekretu. Każde odnawia się co 60 '
            'minut.',
            'Karczmarka Elia w Błękitnym Płomieniu ma trzy niezależne zlecenia godzinne: świeże ryby, zioła '
            'do naparów oraz bezpieczny szlak przeciw bandytom.',
            'Próba Rybaka u Borysa wymaga 30 dowolnych ryb złowionych po przyjęciu zadania.',
            'Pierwsze zlecenie Kucharza Marcela wymaga ugotowania 1 Pieczonej ryby rzecznej po przyjęciu '
            'zadania. Przepis zużywa 2 RÓŻNE gatunki małych ryb rzecznych (Ukleja Rzeczna, Jelec lub Śliz '
            'Kamienny); przedmiot Mała ryba nie jest wymagany.',
            'Jeśli numer nie pasuje, najpierw ponownie wpisz quest, quest ukończone albo quest list <NPC>, '
            'aby ustawić właściwą listę kontekstową.'],
 'elity': ['Elity pojawiają się losowo zamiast zwykłych mobów. Prefixy obejmują Opancerzony, Wściekły, '
           'Astralny, Przeklęty, Regenerujący i inne.',
           'Elity mają wyższe nagrody Soul XP i Class XP oraz lepszy loot.',
           'Rzadkie moby pojawiają się znacznie rzadziej i mają jeszcze większe HP, obrażenia i nagrody.',
           'Mini-bossy mają własny respawn i są mocniejsze od zwykłych mobów danego expowiska.',
           'Regionalne sety: Kultystów Pustki, Umarłego Króla i Wiecznego Lodu. Progi 2/4/6.',
           'Skrzynie: wpisz otwórz skrzynię, skrzynia albo chest. Każda postać otwiera je osobno; odnawiają '
           'się po czasie i losują rzadkość.'],
 'skrzynie': ['Skrzynie skarbów znajdują się w wybranych expowiskach i odnawiają się po czasie.',
              'Komendy: otwórz skrzynię, skrzynia, chest, treasure. Skrzynie mają osobny cooldown dla każdej '
              'postaci.',
              'Rzadkości: Zwykła, Rzadka, Epicka, Legendarna.',
              'Wyższa rzadkość daje więcej waluty i większą szansę na regionalne części setów.'],
 'kodeks_klasowy': ['Codex klasowy pokazuje wszystkie skille klas wraz z wymaganiami i stanem postaci.',
                    'kodeksklasowy <klasa> / classcodex <class> - pełny Codex jednej klasy.',
                    'kodeksklasowy moje / classcodex mine - Codex wszystkich aktywnych klas.',
                    'kodeksklasowy wszystkie / classcodex all - wszystkie 14 klas.',
                    'Możesz też użyć: codex klasy <klasa> albo codex class <class>.',
                    'Każdy skill pokazuje wymaganą Biegłość klasy, nauczyciela, jego salę, koszt nauki po '
                    'aktualnym rabacie Gildii oraz status odblokowania.',
                    'Status rozróżnia: nauczona, dostępna do nauki, zablokowana przez Biegłość albo '
                    'zablokowana przez nieaktywną klasę.'],
 'znajomi': ['znajomi — lista znajomych, ich status online/offline oraz oczekujące zaproszenia.',
             'znajomi dodaj <gracz> — wysyła prośbę o dodanie do znajomych; znajomi akceptuj <gracz> / '
             'odrzuc <gracz>.',
             'znajomi usun <gracz> — usuwa obustronną znajomość.',
             'znajomi party <gracz> — szybkie zaproszenie znajomego do drużyny.',
             'znajomi gildia <gracz> — szybkie zaproszenie znajomego do Gildii; nadal obowiązują prawa rangi '
             'i pozostałe zasady Gildii.',
             'tell <gracz> <tekst> — prywatna wiadomość do gracza online. reply <tekst> / odpisz <tekst> '
             'odpowiada ostatniemu nadawcy prywatnej wiadomości.'],
 'gildia': ['gildia — status Gildii graczy: poziom, bonus, skarbiec, członkowie i osiągnięcia.',
            'v0.34.5: nowa postać na koncie automatycznie dołącza jako Członek do tej samej Gildii, jeśli '
            'pozostałe postacie konta mają jedną wspólną Gildię.',
            'gildia utworz <nazwa> / guild create <name> — założenie kosztuje 500 złota; gildia dolacz; '
            'gildia zapros <gracz>; gildia członkowie.',
            'gildia wplac <kwota> [monet|zlota|mithril] — każdy członek może zasilać wspólny skarbiec.',
            'gildia wyplac <kwota> [monet|zlota|mithril] — wypłata na własny portfel wymaga prawa '
            'przypisanego do rangi.',
            'gildia rozbuduj; gildia rozbuduj potwierdz — tylko lider wydaje skarbiec na poziomy Gildii '
            '1-400.',
            'gildia siedziba — prywatna Siedziba Gildii 1-10; wysokie poziomy kosztują bardzo dużo, nawet '
            'mithril jako najwyższy nominał waluty.',
            'gildia budynek rozbuduj <kowal/skarbiec/biblioteka/trening> — tańsze budynki 1-10, nie mogą '
            'przewyższyć poziomu Siedziby.',
            'gildia kontrakty; gildia kontrakt oddaj <ilość> — wspólne polowania, bossowie i dostawy '
            'materiałów z nagrodą do skarbca.',
            'gildia boss; gildia boss przyzwij; gildia boss ranking; gildia trofea — specjalni bossowie '
            'Gildii, ranking i trofea.',
            'gildia rangi; gildia ranga utworz/ustaw/priorytet/nadaj — własne rangi i uprawnienia.',
            'Bonus Gildii rośnie wraz z poziomem 1-400: +11% na 100, +15% na 200, +19% na 300 i maksymalnie '
            '+23% na 400 do Biegłości, Soul XP, EXP statystyk i profesji.',
            'gildia bank [wplac|wyplac] — wspólny bank przedmiotów; wypłata przedmiotów też zależy od rangi.',
            'gildia chat <tekst>; gildia log; gildia osiągnięcia.'],
 'gildiaklasowa': ['gildiaklasowa / reputacja — pokazuje reputację aktywnych klas, rangę i zniżkę na naukę.',
                   'gildiaklasowa <klasa> — szczegóły reputacji i zadania danej klasy.',
                   'zadanieklasowe / classquest — klasowe zadanie gildyjne.',
                   'egzamin / exam — stan egzaminów Soul 50, 100, 150 i 200.',
                   'Egzaminy wymagają Soul, rosnącej reputacji Gildii oraz opłaty; Soul 50 wymaga też '
                   'ukończenia zadania klasowego.',
                   'egzamin <50|100|150|200> — podejście do egzaminu.',
                   'guildbounty / zleceniagildii — dawna tablica celów Gildii i nagrody reputacji.',
                   'Nowa losowana Tablica Zleceń działa przez bounty / zlecenia / contracts i ma osobny '
                   'trwały postęp 0/x.',
                   'Reputacja obniża ceny nauki u nauczycieli maksymalnie o 25 procent.'],
 'przypisane': ['Broń Duszy i progresja Duszy są na stałe przypisane do postaci i nie są przedmiotem '
                'inventory.',
                'Wszystkie 8 narzędzi profesji jest przypisanych do postaci po zakupie.',
                'Narzędzia nie można oddać, wyrzucić, sprzedać ani schować w Banku Dusz.',
                'Każde narzędzie można kupić tylko jeden raz na postać.',
                'Level, XP i Tier narzędzia pozostają zapisane przy tej postaci.',
                'Stare kopie z banku są automatycznie przywracane do postaci, a duplikaty redukowane do '
                'jednej sztuki.',
                'English: profession tools and Soul progression are character-bound; each tool can be '
                'purchased once per character.'],
 'aoe': ['Czary obszarowe trafiają wszystkich dostępnych przeciwników w tej samej lokacji.',
         'Mag: Eksplozja Arkanów Soul 40, Burza Meteorów Soul 160.',
         'Nekromanta: Plaga Dusz Soul 40, Nawałnica Grobów Soul 160.',
         'Czarownik: Nova Otchłani Soul 40, Deszcz Pustki Soul 160.',
         'Druid: Huragan Soul 40, Deszcz Gwiazd Soul 160.',
         'Psionik: Burza Umysłów Soul 40, Psychiczne Załamanie Soul 160.',
         'Kapłan: Modlitwa Odnowy Soul 40 i Masowe Uzdrowienie Soul 160 leczą całą drużynę w tej samej '
         'lokacji.',
         'Działają też angielskie nazwy, np. arcane explosion, meteor storm, soul plague, void nova, '
         'hurricane, mind storm, group heal, mass heal.',
         'Akcja obszarowa nie wywołuje osobnego kontrataku; przeciwnik atakuje według własnego timera.'],
 'bestiariusz': ['bestiariusz / bestiary - podsumowanie odblokowanych gatunków i wszystkich zabójstw.',
                 'bestiariusz lista / bestiary list - wszystkie odkryte wpisy wraz z liczbą zabójstw.',
                 'bestiariusz <mob> / bestiary <mob> - liczba zabójstw, rekord czasu, HP, obrażenia, '
                 'lokacje, realne dropy i zdefiniowane odporności.',
                 'Pierwsze zabicie odblokowuje wpis. Proceduralne warianty elite/rare są przypisane do '
                 'bazowego gatunku.',
                 'bestiariusz rekordy / bestiary records - najlepsze zapisane czasy zabicia.'],
 'dwa_pierscienie': ['Postać może nosić dwa pierścienie jednocześnie: ring1 i ring2.',
                     'Komendy: załóż pierścień 1, załóż pierścień 2, equip ring1, equip ring2.',
                     'Sockety są osobne dla obu pierścieni: osadz rubin pierścień 1 albo socket ruby ring2.',
                     'Do dwóch identycznych pierścieni trzeba posiadać dwie sztuki.',
                     'Drugi taki sam pierścień nie liczy się drugi raz do progu setu klasowego 2/4/6/8.']}

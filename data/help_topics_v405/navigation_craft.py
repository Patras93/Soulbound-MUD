"""Historyczna pomoc Soulbound v4.00.5: navigation craft."""

def make_topics():
    return {'soul_milestones': ['Kamienie milowe Broni Duszy są na Tierach 5, 10, 15 i 20.',
                     'Każdy wzmacnia specjalizację klasy głównej; Łotrzyk dostaje dodatkowy unik, a Strażnik '
                     'dodatkową redukcję obrażeń.',
                     'Komendy: dusza info albo soul info.'],
 'nawigacja': ['Dla lochów i expowisk prowadzenie kończy się przed wejściem; nigdy nie prowadzi na piętro '
               'ani w głąb obszaru.',
               'prowadz <cel> i walk <cel> to dokładnie ten sam system nawigacji.',
               'Dla zwykłej lokalizacji prowadzenie zatrzymuje się jeden krok przed celem; ostatni kierunek '
               'wykonujesz sam.',
               'Wyjątek: gdy celem jest NPC, prowadzenie dochodzi dokładnie do pokoju NPC.',
               'Działają też guide <cel>, idz <cel>, go <cel> oraz navigate <cel>.',
               'Lista jest uporządkowana kategoriami: prowadz lista lub walk list.',
               'Kategorie: miasto, miasta, gildia, profesje, tereny, lochy, npc i wszystko. `walk miasta` '
               'pokazuje wszystkie 9 miejscowości.',
               'Przykład: prowadz lista gildia, walk list dungeons, prowadz lista profesje.',
               'Jeżeli nazwa pasuje do kilku miejsc, dostajesz jedną numerowaną listę i wpisujesz tylko '
               'cyfrę.',
               'v0.38.12: prowadz kopalnia kończy się w Komnacie Kryształowej przy progu Kopalni Głębinowej; '
               'wpisz kopalnia, aby wejść bez podawania kierunku.',
               'cofnij, wyjście, back, exit, wstecz, return i escape prowadzą bezpośrednio do bezpiecznego '
               'wyjścia z rozpoznanego lochu.',
               'Nawigacja automatyczna zatrzymuje się na blokadach progresji, żywym bossie, zamkniętej '
               'ścianie kopalni albo rozpoczęciu walki.',
               'Zmiana postaci: quit. Komenda zapisuje obecną postać i wraca do MENU POSTACI bez '
               'rozłączania.'],
 'dungeon_exit': ['Dostępność lochów: cofnij, wyjście, back, exit, wstecz, return i escape prowadzą '
                  'bezpośrednio do bezpiecznego wyjścia z lochu.',
                  'Te komendy nie cofają o jedną lokację.',
                  'Działają w rozpoznanych lochach, profession dungeonach, Jaskini Trolli i zamkniętych '
                  'odnogach endgame.',
                  'Podczas walki najpierw użyj flee albo pokonaj przeciwnika.'],
 'kamienie': ['Kamienie szlachetne są dodatkowym łupem z Górnictwa i nie zastępują rudy.',
              'Dodano 11 kamieni od Rubinu do Pryzmatu Eternium.',
              'Surowy kamień trzeba oszlifować u Mirelli w Pracowni Jubilerskiej.',
              'Komenda: szlifuj <kamień>.',
              'Szlifowanie rozwija Jubilerstwo i Szczypce Jubilerskie.',
              'Oszlifowany klejnot można osadzić w założonym pierścieniu albo naszyjniku.',
              'Komenda: osadz <klejnot> pierścień.',
              'Komenda: osadz <klejnot> naszyjnik.',
              'Komenda gniazda pokazuje zajęte gniazda i osadzone klejnoty.',
              'Craftowana biżuteria ma 1, 2 lub 3 gniazda zależnie od tieru.',
              'Klasowy pierścień ma 1 gniazdo, a klasowy naszyjnik 2.',
              'Po zmianie pierścienia lub naszyjnika osadzone klejnoty automatycznie wracają do ekwipunku.',
              'Gniazda i klejnoty są zapisywane w SQLite.'],
 'jubilerstwo': ['Jubilerstwo jest profesją 1-400 z 23 rangami.',
                 'Narzędzie: Szczypce Jubilerskie, level 1-400 i 40 Tierów.',
                 'Szczypce nie mają trwałości i nie zużywają się.',
                 'Kupisz je wyłącznie u Jubilerki Mirelli w Pracowni Jubilerskiej nad Rynkiem.',
                 'Użyj prowadz jubilerka albo prowadz pracownia jubilerska.',
                 'Komenda jubilerstwo pokazuje stan profesji.',
                 'Komenda szczypce pokazuje stan narzędzia.',
                 'Komenda receptury jubilerstwo pokazuje wszystkie receptury.',
                 'Komenda jub <receptura> wykonuje biżuterię.',
                 'Dodano 18 receptur: 9 pierścieni i 9 naszyjników od Żelaza do Eternium.',
                 'Jubilerka Mirella prowadzi 9-etapowy łańcuch zleceń profesyjnych.'],
 'prowadz_wybor': ['Gdy prowadz pasuje do kilku lokacji, MUD pokazuje numerowaną listę zamiast zgadywać.',
                   'Działa to teraz dla wszystkich terenów, nie tylko dla kopalni.',
                   'Po liście wpisujesz tylko sam numer, na przykład 1 albo 2.',
                   'Nie ma drugiego pytania ani drugiego wyboru.',
                   'Przykłady: prowadz kopalnia, prowadz dzicz, prowadz góry, prowadz podziemia, prowadz '
                   'gildia, prowadz jaskinia trolli, prowadz krypta, prowadz wieża i prowadz twierdza.',
                   'Duże wielopoziomowe lochy są zwijane do czytelnej pozycji zamiast wypisywania dziesiątek '
                   'lub setek pięter.',
                   'Konkretne piętra nie są celem prowadzenia. Wnętrza lochów i expowisk eksplorujesz '
                   'samodzielnie.',
                   'Wpisz anuluj, jeśli chcesz zamknąć oczekujący wybór bez wybierania.'],
 'respawn_mobow': ['Czas odradzania mobów został globalnie zwiększony 2 razy.',
                   'Zwykłe moby: bazowo 120 sekund, teraz 240 sekund.',
                   'Bossowie: bazowo 300 sekund, teraz 600 sekund.',
                   'Manekin treningowy: bazowo 60 sekund, teraz 120 sekund.',
                   'Jeżeli konkretny mob ma własny respawn_seconds, jego indywidualny czas również jest '
                   'mnożony razy 2.',
                   'HP, obrażenia, Soul XP, nagrody, loot i mechaniki walki nie zostały zmienione.'],
 'bizuteria_klasowa': ['Każda z 14 klas ma własny Pierścień i Naszyjnik.',
                       'Pierścień zajmuje osobny slot pierścień.',
                       'Naszyjnik zajmuje osobny slot naszyjnik.',
                       'Biżuteria jest dostępna w tym samym sklepie klasowym co pozostałe części zestawu.',
                       'Pierścień daje klasowy bonus +2 do głównej cechy zestawu.',
                       'Naszyjnik daje klasowy bonus +3 do głównej cechy zestawu.',
                       'Kupno i założenie wymaga aktywnej odpowiedniej klasy.',
                       'Multiclass działa także dla pierścieni i naszyjników.',
                       'Szybkie komendy: załóż pierścień oraz załóż naszyjnik.'],
 'sklepy_klasowe': ['Dodano klasowe sklepy wyposażenia dla wszystkich 14 klas.',
                    'Każda klasa ma 3 różne linie wyposażenia; każda linia obejmuje hełm, pancerz, rękawice, '
                    'nogawice, buty, talizman, pierścień i naszyjnik.',
                    'Wojownik i Berserker kupują wyposażenie w Sali Oręża Gildii.',
                    'Łotrzyk i Łowca kupują wyposażenie w Galerii Cieni Gildii.',
                    'Mnich i Strażnik kupują wyposażenie w Sali Dyscypliny Gildii.',
                    'Mag i Psionik kupują wyposażenie w Komnacie Arkanów Gildii.',
                    'Nekromanta i Czarownik kupują wyposażenie w Komnacie Mrocznych Sztuk.',
                    'Kapłan i Druid kupują wyposażenie w Sanktuarium Gildii.',
                    'Wpisz shop albo list w odpowiedniej sali. Możesz też filtrować: shop <klasa>, np. shop '
                    'wojownik.',
                    'Klasowe EQ może też losowo wypaść z mobów; moc dropu jest dopasowana do siły '
                    'przeciwnika, a klasa/linia/slot są losowe.',
                    'Przedmiot klasowy można kupić i założyć tylko wtedy, gdy wymagana klasa jest aktywna.',
                    'Multiclass działa: aktywna klasa dodatkowa również pozwala korzystać z jej wyposażenia.',
                    'Możesz użyć prowadz sklep <klasa>, na przykład prowadz sklep maga.'],
 'kilof_u_gornika': ['Kilof nie jest już sprzedawany przez Kowala Dorana ani w Górskiej Kuźni.',
                     'Podstawowy Kilof sprzedaje wyłącznie Górnik Toren przy Wejściu do Kryształowej '
                     'Jaskini.',
                     'Użyj prowadz jaskinia albo prowadz sklep kilofa.',
                     'Na miejscu wpisz shop albo list, a potem kup kilof.'],
 'waluta_auto': ['Wspólne saldo działa automatycznie bez komendy wymiany.',
                 'Jedno wspólne saldo z nominałami: srebro, złoto i mithril.',
                 'Nominały: 100 srebra = 1 złoto; 1 000 000 złota = 1 mithril.',
                 'Portfel i Bank Dusz normalizują nominały automatycznie.',
                 'Stara ręczna wymiana została usunięta z MUD-a.',
                 'Stare salda są zachowywane wartościowo i nie są kasowane.'],
 'przetop': ['przetop <metal, ruda albo płyty> przetapia surowiec na właściwą sztabkę.',
             '4 Stalowe Płyty z Pancerza ze Szkatułki można przetopić w 1 Sztabkę Stali: przetop płyty / '
             'smelt plates.',
             'Przetop max <metal> zużywa TYLKO wybrany surowiec. Aby przetopić Salvage, użyj jawnie: przetop '
             'max odłamki żelaza. Przetop wszystko nadal obejmuje wszystkie dostępne źródła.',
             'Pojedyncze przetop <metal> może awaryjnie wykorzystać Salvage, jeśli brakuje zwykłej rudy. Dwa '
             'zgodne fragmenty Salvage dają 1 sztabkę.',
             'v0.31.15: każda udana receptura nalicza aktywne questy craftingowe; Salvage/Salvage 3.0/Tech '
             'Salvage dają Kowalstwo XP bez sztucznego nabijania Młota.',
             'Komenda korzysta z istniejących receptur Kowalstwa i nie omija wymagań.',
             'Musisz mieć Młot Rzemieślniczy, odpowiedni level Kowalstwa, wymagany Tier Młota, składniki i '
             'stać przy właściwej kuźni.',
             'Przykłady: przetop żelazo, przetop odłamki żelaza, przetop srebro, przetop płyty, przetop '
             'złoto, przetop mithril, przetop kobalt.',
             'Mithril wydobywa się od Kilofa 80 i poziomu 80 Kopalni Głębinowej. Obsługiwane są także: runa, '
             'smocza stal, astral, pustka i Eternium.',
             'Przetapianie rudy w sztabki daje XP Kowalstwa i Młota tak samo jak pozostałe receptury '
             'wytwarzania sztabek.'],
 'assist': ['Drużyna ma automatyczne asystowanie: gdy członek rozpoczyna walkę, wolni członkowie tej samej '
            'drużyny i lokacji automatycznie dołączają do jego celu.',
            'wspieraj <gracz> i assist <gracz> pozostają jako ręczne komendy awaryjne.',
            'Obaj gracze muszą należeć do tej samej drużyny.',
            'Obaj gracze muszą stać w tej samej lokacji.',
            'Wskazany członek drużyny musi aktualnie walczyć z żywym przeciwnikiem.',
            'Automatyczne dołączenie uruchamia zwykłą walkę realtime bez dodatkowego darmowego ciosu.',
            'Jeśli walczysz już z innym mobem, assist nie przełączy celu; najpierw zakończ walkę albo użyj '
            'flee.',
            'Działa także jako: druzyna wspieraj <gracz> oraz druzyna assist <gracz>.'],
 'mityczne_od_100': ['Mityczna Krypta nie ma wymogu Soul Level i jest dostępna od razu, ale od pierwszego '
                     'piętra jest bardzo trudna.',
                     'Mityczna Krypta ma nieskończone piętra i bossa co 10 pięter bez końca.',
                     'Mityczna Wieża Astralna zachowuje własny wymóg Soul Level 100, ale nie ma górnego '
                     'limitu pięter.',
                     'Dostępność Krypty nie oznacza rekomendacji: con, expowiska i komunikat zagrożenia '
                     'pokazują, gdy przeciwnik jest za silny.',
                     'W Kryptach co 10 pięter rosną trudność, Class XP i Soul XP; waluta i moc EQ nie rosną '
                     'bez końca.'],
 'expowiska': ['Komenda expowiska pokazuje listę terenów przeznaczonych do expienia.',
               'Każdy teren ma kategorię bazową: Początkujący, Umiarkowany, Trudny, Śmiertelny albo Endgame.',
               'Ocena dla ciebie zmienia się automatycznie wraz z Biegłością aktywnych klas, Soul Levelem, '
               'statystykami i wyposażeniem.',
               'Gobliny, Bandyci, Las Szeptów, Kanały i podobne wczesne strefy należą do kategorii '
               'Początkujący.',
               'expowiska polecane pokazuje obszary, które są teraz Odpowiednie albo Trudne dla twojej '
               'postaci.',
               'EXP za zabicie jest dynamiczne 1-400: silniejszy od ciebie mob daje premię, a ten sam '
               'przeciwnik daje stopniowo mniej EXP, gdy twoja postać go przerasta.',
               'Dynamiczny mnożnik obejmuje EXP statów, Soul XP i Class XP; nie zmienia waluty ani lootu. '
               'Minimalna wypłata to 35% bazowego EXP, maksymalna premia x2.25.',
               'con <mob> pokazuje aktualny mnożnik EXP oraz porównanie siły postaci i przeciwnika.',
               'expowiska krypta pokazuje szczegółowy opis Krypty.',
               'expowiska trolle pokazuje szczegółowy opis Jaskini Trolli.',
               'expowiska giganci pokazuje szczegółowy opis Twierdzy Gigantów.',
               'expowiska astral pokazuje szczegółowy opis Wieży Astralnej.',
               'Szczegóły zawierają przeciwników, trudność, opis, uwagi i komendę prowadzenia.',
               'Soulbound nadal nie ma levelu postaci ani Character XP.'],
 'auto_kopalnia_down': ['kop on może teraz automatycznie zejść w dół po przebiciu ściany Kopalni Głębinowej.',
                        'Automat schodzi tylko przez kierunek down.',
                        'Automat schodzi tylko wtedy, gdy następny poziom jest już odblokowany w '
                        'mine_progress.',
                        'Automat sprawdza, czy wyjście down prowadzi dokładnie na następny poziom Kopalni.',
                        'Nie przejdzie przez nieprzebitą ścianę.',
                        'Nie chodzi po świecie i nie wybiera innych kierunków.',
                        'Jeśli włączysz kop on na poziomie z wcześniej przebitą ścianą, zejdzie na '
                        'odblokowany następny poziom.',
                        'Po zejściu kontynuuje kopanie na nowym poziomie.'],
 'sciany_kopalni': ['Każda ściana Kopalni Głębinowej ma losową liczbę wymaganych uderzeń Kilofa.',
                    'Poziomy 1-9 losują od 3 do 8 uderzeń.',
                    'Od poziomu 10 próg losuje się w przybliżeniu od 70 do 130 procent numeru piętra.',
                    'Wylosowany próg jest zapisywany w SQLite i nie zmienia się po restarcie ani ponownym '
                    'logowaniu.',
                    'Po przebiciu ściany następna ściana dostaje nowy niezależny losowy próg.',
                    'Istniejący zapis wall_hits nie jest resetowany po aktualizacji.',
                    'Komenda kopalnia pokazuje bieżący postęp i aktualnie wylosowany próg.',
                    'kop on może po przebiciu bezpiecznie zejść na kolejny odblokowany poziom.'],
 'who': ['who pokazuje wszystkich aktualnie zalogowanych graczy.',
         'Dla każdego gracza podaje nazwę, aktywną klasę lub klasy, Soul Level, aktualną lokację i strefę.',
         'Alias po polsku: kto.',
         'Przykładowa linia: Asia. Klasa: Mag. Soul Level 42. Lokalizacja: Rynek. Strefa: Miasto.'],
 'look_skrot': ['Skrót l działa dokładnie tak samo jak look.',
                'l bez argumentu opisuje aktualną lokację.',
                'l Asia działa jak look Asia.',
                'l Górski Troll działa jak look Górski Troll.',
                'l Mikstura Leczenia działa jak look Mikstura Leczenia.',
                'l hełm działa jak look hełm.',
                'Skrót obsługuje graczy, NPC, przeciwników i przedmioty.'],
 'look_cel': ['look bez argumentu opisuje aktualną lokację jak wcześniej.',
              'look gracz pokazuje gracza w tej samej lokacji.',
              'Przykład: look Asia.',
              'look NPC pokazuje opis NPC stojącego w tej samej lokacji.',
              'look przeciwnik pokazuje aktualne HP, bazowe obrażenia, typ obrażeń i specjalne mechaniki.',
              'look przedmiot pokazuje opis przedmiotu z ekwipunku, założonego sprzętu albo lokalnego '
              'sklepu.',
              'Przykład: look Mikstura Leczenia albo look hełm.',
              'Przy częściowej nazwie cel musi być jednoznaczny.',
              'look nie pokazuje graczy, NPC ani mobów z innych lokacji.']}

"""Historyczna pomoc Soulbound v4.00.5: world exploration."""

def make_topics():
    return {'atlas_kompletny': ['Atlas zasobów jest teraz kompletny.',
                     'atlas ryby pokazuje wszystkie istniejące ryby w grze, a następnie podział na rzekę, '
                     'jezioro, morze i ocean.',
                     'atlas drewno pokazuje wszystkie istniejące rodzaje drewna oraz podział według terenów.',
                     'atlas rudy pokazuje wszystkie istniejące rudy, wymagany level Kilofa i minimalną '
                     'głębokość Kopalni Głębinowej.',
                     'atlas zioła i atlas rośliny pokazują wszystkie istniejące zioła i rośliny oraz grupy '
                     'występowania.',
                     'Długie listy są dzielone na krótsze części, żeby NVDA czytał je wygodniej.',
                     'Można nadal wpisać atlas <nazwa surowca>, aby usłyszeć informacje o jednym konkretnym '
                     'zasobie.',
                     'Pełne atlasy są bezpośrednio oparte na aktywnych listach RESOURCE_IDS, więc nowy zasób '
                     'nie powinien wypaść z pełnego spisu.'],
 'kopalnia_200': ['Kopalnia Głębinowa generuje piętra dynamicznie od pierwszego poziomu i może rozwijać się '
                  'dalej na żądanie.',
                  'Kryształowa Komnata prowadzi przez down na poziom 1.',
                  'Każde udane kopanie na najgłębszym odblokowanym poziomie daje 1 uderzenie w ścianę w dół.',
                  'Każda ściana ma własny losowy próg uderzeń zapisany trwale w SQLite.',
                  'Im głębiej, tym lepsza pula rud.',
                  'Level Kilofa nadal ogranicza jakość wydobycia.',
                  '1-9: Kamień i Miedź.',
                  '10-24: Miedź i Żelazo.',
                  '25-49: Żelazo i Srebro.',
                  '50-99: Srebro i Złoto.',
                  '100-119: Złoto i Kobalt.',
                  '120-139: Kobalt i Kamień Runiczny.',
                  '140-159: Kamień Runiczny i Smocza Stal.',
                  '160-179: Smocza Stal i Ruda Astralna.',
                  '180-199: Ruda Astralna i Ruda Pustki.',
                  '200+: Ruda Pustki i Eternium; nowe zasoby 201-400 respektują cap narzędzia/profesji 400, '
                  'a dalsza głębokość nie zwiększa mocy ekonomii ponad 400.',
                  'kopalnia pokazuje aktualne położenie/piętro, najgłębszy odblokowany poziom, postęp '
                  'ściany, auto-kopanie, Górnictwo, Kilof i dostępne progi rud.',
                  'kop on może wystartować w ręcznej części Kryształowej Jaskini, sam dojść do poziomu 1 i '
                  'po przebiciu ściany schodzić na kolejny odblokowany poziom.'],
 'auto_chodzenie': ['Auto-profesje nie chodzą samodzielnie.',
                    'low on łowi tylko w aktualnym łowisku i nie przemieszcza postaci.',
                    'zbieraj on zbiera tylko w aktualnym miejscu i nie przemieszcza postaci.',
                    'tnij on ścina tylko w aktualnym miejscu i nie przemieszcza postaci.',
                    'kop on jest wyjątkiem: w ręcznej części Kryształowej Jaskini może sam dojść do poziomu '
                    '1, a potem automatycznie schodzi na kolejne odblokowane poziomy po przebiciu ściany.',
                    'Manualny ruch gracza nadal wyłącza aktywne auto.',
                    'off nadal dokańcza bieżącą akcję i dopiero potem zatrzymuje automat.'],
 'laki': ['Strefa Łąk składa się teraz z czterech lokacji.',
          'Srebrna Łąka jest centralnym punktem strefy.',
          'Łąka Mięty leży na wschód od Srebrnej Łąki i prowadzi dalej do Brzegu Rzeki.',
          'Łąka Kwiatów leży na zachód od Srebrnej Łąki i prowadzi dalej do Gaju Szeptów.',
          'Łąka Nadjeziorna leży na południe od Srebrnej Łąki i prowadzi dalej do Srebrnego Jeziora.',
          'Na wszystkich łąkach działa zbieraj i zbieraj on.',
          'Łąka Mięty częściej daje Miętę i Melisę.',
          'Łąka Kwiatów częściej daje Rumianek, Lawendę i Krwawnik.',
          'Łąka Nadjeziorna ma zioła wilgotnych terenów, a na wyższych poziomach Sierpa może pojawić się '
          'Gwiezdny mech.',
          'Użyj prowadz srebrna laka, prowadz laka miety, prowadz laka kwiatow albo prowadz laka '
          'nadjeziorna.'],
 'auto_off': ['low off, fish off, kop off, mine off, tnij off, woodcut off i zbieraj off zatrzymują automat '
              'po dokończeniu bieżącej akcji.',
              'Jeśli akcja już trwa, nie jest anulowana.',
              'Po zakończeniu dostajesz normalnie surowiec, XP profesji i XP używanego narzędzia.',
              'Następna automatyczna akcja już się nie rozpoczyna.',
              'Wymuszone zatrzymanie, na przykład wyjście z gry, podróż albo przełączenie na inną '
              'auto-aktywność, nadal może przerwać akcję natychmiast.'],
 'kurs_walut': ['Nominały wspólnego salda przeliczają się automatycznie.',
                'Jedno wspólne saldo z nominałami: srebro, złoto i mithril.',
                'Nominały: 100 srebra = 1 złoto; 1 000 000 złota = 1 mithril.',
                'Saldo jest automatycznie przedstawiane w najwyższych możliwych nominałach.',
                'Automatyczne przeliczanie działa w portfelu oraz Banku Dusz.',
                'Stara ręczna komenda wymiany została usunięta.',
                'Istniejący majątek nie jest zerowany; zachowuje pełną wartość.'],
 'wiecej_ryb': ['Dodano 40 nowych gatunków ryb: po 10 do rzeki, jeziora, morza i oceanu.',
                'Nowe ryby mają progi Wędki od levelu 1 aż do 200.',
                'Rzeka otrzymała między innymi Ukleję Rzeczną, Pstrąga Potokowego, Tajmienia Rzecznego, '
                'Lipienia Duchów i Wiecznego Smoka Rzecznego.',
                'Jezioro otrzymało między innymi Kiełbia Jeziorowego, Złotego Lina, Kryształową Sieję, '
                'Astralnego Szczupaka i Wiecznego Węża Jeziora.',
                'Morze otrzymało między innymi Belonę, Prażmę Morską, Kongera, Śledzia Burzy i Wiecznego '
                'Smoka Morza.',
                'Ocean otrzymał między innymi Rybę Latającą, Tuńczyka Żółtopłetwego, Marlina Czarnego, '
                'Marlina Pustki i Lewiatana Świata.',
                'Komenda woda automatycznie pokazuje nowe ryby po osiągnięciu wymaganego levelu Wędki.',
                'fish losuje z dokładnie tej samej listy, którą pokazuje woda.',
                'Nowe ryby są widoczne w atlasie odpowiedniego łowiska.',
                'Nowe ryby można normalnie przechowywać w Siatce i sprzedawać.'],
 'oddawanie_zadan': ['Po wykonaniu celu zadania dziennik pokazuje GOTOWE DO ODDANIA.',
                     'Wróć do NPC, który dał zadanie.',
                     'oddaj zadanie i oddaj questa automatycznie oddają jedyne gotowe zadanie u NPC w tej '
                     'lokacji.',
                     'oddaj <nazwa zadania> pozwala wybrać konkretne zadanie.',
                     'Przy ukończonym zadaniu NPC komentuje wykonanie, a potem NVDA czyta, co dokładnie '
                     'wręcza jako nagrodę.',
                     'Questy profesyjne i rzemieślnicze zawsze mają także nagrodę w walucie; istniejące '
                     'wypłaty zachowują balans gry.',
                     'zdaj zadanie oraz turnin są aliasami.',
                     'Jeśli kilka zadań jest gotowych u NPC w tej samej lokacji, gra nie zgaduje i prosi o '
                     'pełną nazwę.',
                     'Jeśli zadanie nie jest ukończone, oddaj podaje aktualny postęp.',
                     'talk to <NPC> działa tak samo jak talk <NPC>.',
                     'Rozmowa z NPC rozpoznaje, czy wracasz z zadaniem w toku albo gotowym do oddania, ale '
                     'przyjęcie i oddanie pozostają jawnymi komendami gracza.',
                     'Oddawanie collect nadal zabiera wymagane przedmioty dopiero przy rozliczeniu zadania.',
                     'Oddawanie collect_category nadal korzysta z właściwego magazynu profesji i inventory.'],
 'woda': ['Komenda woda / łowisko zaczyna od jasnej informacji o typie bieżącego łowiska, np. Rzeka, '
          'Jezioro, Morze, Ocean, Kanał albo Zatopiona Grota.',
          'Dla specjalnych miejsc nazwa łowiska jest oddzielona od technicznego ekosystemu ryb; Czarny Kanał '
          'mówi Kanał, a nadal korzysta z rzecznej progresji gatunków.',
          'Pokazuje aktualny level Wędki i dokładną liczbę gatunków, które rzeczywiście mogą zostać '
          'wylosowane w tym miejscu.',
          'Pokazuje ile z obecnej puli już odkryto w Dzienniku ryb oraz ile pozostaje nieodkrytych.',
          'Nazwy czytane przez woda dotyczą tylko gatunków już odkrytych przez tę postać; nieodkryte '
          'pozostają jako licznik.',
          'Czarny Kanał od Wędki 30 ma własną rzeczywistą pulę Ślepego Węgorza Kanałowego, a Zatopiona Grota '
          'ogranicza pulę zgodnie z głębokością.',
          'Jeśli kolejny próg zwykłego ekosystemu jest zablokowany, woda podaje wymagany level Wędki.',
          'Ryby nie mają twardego limitu sztuk, nie ma przełowienia i łowiska nie wyczerpują się od '
          'łowienia.'],
 'dziennik_ryb': ['dziennikryb / fishjournal - trwały Dziennik ryb zapisany osobno dla każdej postaci.',
                  'Pokazuje liczbę odkrytych gatunków, zarejestrowanych połowów i odkrytych gatunków '
                  'legendarnych.',
                  'dziennikryb lista czyta wszystkie odkryte gatunki, ich kolekcjonerską rzadkość, liczbę '
                  'połowów oraz rekord długości i masy.',
                  'dziennikryb <nazwa ryby> pokazuje szczegóły konkretnego odkrytego gatunku i typy wód, w '
                  'których występuje.',
                  'Pierwszy połów nowego gatunku jest natychmiast czytany przez NVDA jako NOWY GATUNEK W '
                  'DZIENNIKU RYB.',
                  'Pobicie rekordu długości lub masy jest natychmiast czytane przez NVDA.',
                  'Rzadkości gatunków: pospolita, niepospolita, rzadka, epicka i legendarna. Rzadkość jest '
                  'kolekcjonerska i nie daje bonusów bojowych.',
                  'Starszy save może odtworzyć gatunki nadal obecne w Siatce. Dokładne rekordy długości/masy '
                  'i pełne nowe wpisy są liczone od v0.9.5.'],
 'gotowanie_rozbudowane': ['Gotowanie korzysta z Noża Kucharskiego level 1-400.',
                           'Nie jest osobnym levelem postaci i nie dodaje Character XP.',
                           'Gotowanie jest osobną profesją 1-400; jej poziom skraca czas i odblokowuje '
                           'receptury. Nóż rozwija się osobno 1-400 i daje bonus produktu.',
                           'Potrawy przygotowuje się w Karczmie Pod Błękitnym Płomieniem albo na Targu '
                           'Rybnym.',
                           'gotowanie pokazuje stan systemu i aktualny Nóż Kucharski.',
                           'gotuj lista pokazuje wszystkie receptury Gotowania.',
                           'gotuj <potrawa> przygotowuje wybraną potrawę.',
                           'receptury cook nadal działa.',
                           'Receptury mają progi Gotowania: '
                           '1,10,20,30,40,50,60,70,80,90,95,99,100,120,140,160,180 i 200.',
                           'Dodano Okoń w Ziołowej Skorupce, Zupę ze Srebrnego Pstrąga, Zapiekankę '
                           'Jeziornego Rybaka, Makrelę Korzenną, Łososia z Ziołami i Rosół z Księżycowego '
                           'Węgorza.',
                           'Każda akcja Gotowania wykorzystuje czas wynikający z poziomu profesji Gotowanie; '
                           'Nóż Kucharski nie skraca czasu.',
                           'Gotowanie level 1 daje 12 sekund bazowego czasu, a Gotowanie level 200 daje 4 '
                           'sekundy; level Noża nie skraca czasu.',
                           'Tier Noża daje szansę na dodatkową porcję.',
                           'Gotowanie zużywa składniki z właściwych magazynów profesji oraz inventory.',
                           'Potrawy przywracają HP, a część również Manę.',
                           'Questy Kucharza Marcela pozostają i nadal wykorzystują Gotowanie.'],
 'hp_bossow_lochow': ['Bossowie Krypty i Wieży Astralnej mają teraz HP według numeru piętra.',
                      'Wzór: numer piętra razy 1000 HP.',
                      'Krypta piętro 10: 10000 HP.',
                      'Krypta piętro 20: 20000 HP.',
                      'Krypta piętro 100: 100000 HP.',
                      'Krypta piętro 200: 200000 HP.',
                      'Wieża Astralna poziom 100: 100000 HP.',
                      'Wieża Astralna poziom 150: 150000 HP.',
                      'Wieża Astralna poziom 200: 200000 HP.',
                      'Zwykłe moby nadal mają globalne 2 razy HP z v0.6.94.',
                      'Bossowie świata poza Kryptą i Wieżą zachowują swoje 2 razy HP.',
                      'Damage i nagrody bossów nie zostały zwiększone.',
                      'consider automatycznie korzysta z nowych wartości HP.'],
 'hp_mobow': ['Wszystkie moby i bossowie mają teraz globalnie 2 razy więcej maksymalnego HP.',
              'Zmiana obejmuje zwykłych przeciwników, bossów świata, manekina treningowego, Kryptę 1-200 i '
              'Wieżę Astralną 100-200.',
              'Obrażenia mobów nie zostały zwiększone.',
              'Samo podwojenie HP nie daje automatycznie większej waluty ani lootu; późniejsze wersje '
              'balansu liczą EXP z realnej siły konkretnego przeciwnika.',
              'Mechaniki bossów nadal korzystają z ich aktualnego podwojonego maksymalnego HP.',
              'Respawn pozostaje bez zmian i przywraca pełne nowe maksymalne HP.',
              'consider automatycznie pokazuje i ocenia nowe wartości HP.',
              'Moby i bossowie nadal nie są agresywni.',
              'Walka działa w czasie rzeczywistym: gracz i przeciwnik mają niezależne timery akcji.'],
 'soul_xp_bloki': ['Wymagane Soul XP zachowuje starą krzywą 1-200, a w zakresie 201-400 rośnie kontrolowanie '
                   'bez wykładniczej eksplozji.',
                   'Soul Level 1-10 używa mnożnika x1. Każdy kolejny pełny blok 10 leveli podnosi mnożnik o '
                   '25 procent.',
                   'Bazowy wzór wynosi 180 + 60 razy Soul Level minus 1, a następnie jest mnożony przez 1,25 '
                   'do potęgi liczby ukończonych bloków 10 leveli.',
                   'Przykład: z Soul Level 10 na 11 potrzeba 720 XP.',
                   'Przykład: z Soul Level 11 na 12 potrzeba 975 XP.',
                   'Przykład: z Soul Level 21 na 22 potrzeba około 2156 XP.',
                   'Przykład: z Soul Level 51 na 52 potrzeba około 9705 XP.',
                   'Od v0.8.64 pojedynczy kill ma też limit Soul XP zależny od rangi przeciwnika, więc carry '
                   'nie przeskakuje dziesiątek Soul Leveli naraz.',
                   'Już zdobyty Soul XP pozostaje zapisany i nie jest resetowany.',
                   'Soul Level ma zakres 1-400.'],
 'consider': ['consider <mob>, con <mob> albo ocen <mob> ocenia przeciwnika bez rozpoczynania walki.',
              'Jeśli w lokacji jest dokładnie jeden mob, samo consider oceni właśnie jego; przy wielu mobach '
              'podaj nazwę lub numer wystąpienia.',
              'Od v1.13.31 consider używa tej samej prognozy Adaptive Combat co realne starcie: uwzględnia '
              'aktualną postać, Speed/multi-hit oraz wszystkich żywych członków drużyny stojących w tej '
              'samej lokacji.',
              'Pokazuje prognozowane skalowane HP moba, bazowe max HP, mnożnik HP, rangę Adaptive Combat i '
              'liczbę członków lokalnej drużyny.',
              'Pokazuje szacowane obrażenia odpowiedzi już po adaptacyjnym skalowaniu względem twojego HP, '
              'obrony, redukcji i uniku.',
              'Twój zwykły atak jest liczony jako hit oraz pełna akcja z aktualną liczbą trafień; w drużynie '
              'consider pokazuje też łączną zwykłą akcję lokalnej drużyny.',
              'Ocena może być: bardzo słaby, słaby, korzystny, porównywalny, niebezpieczny, bardzo '
              'niebezpieczny albo śmiertelnie groźny.',
              'Bossowie są oceniani ostrożniej, ponieważ specjalne mechaniki zwiększają ryzyko; jeśli boss '
              'ma opis mechaniki, consider go przeczyta.',
              'Consider pokazuje również prognozowany mnożnik rekompensaty EXP/waluty Adaptive Combat; drop '
              'chance i unikalne dropy nie są przez niego mnożone.',
              'Consider nie angażuje moba, nie wykonuje ataku, nie zużywa Many i nie mutuje skali '
              'przeciwnika. To bezpieczna prognoza przed walką.'],
 'wolniejsze_staty': ['Każda z sześciu statystyk ma własny licznik EXP i własny próg.',
                      'Każda statystyka ma osobny, rosnący próg; od wartości 50 dalszy wzrost jest wyraźnie '
                      'wolniejszy, bez limitu statystyk.',
                      'Po osiągnięciu progu rośnie tylko wskazana statystyka; pozostałe zachowują własny '
                      'postęp.',
                      'Statystyki nadal nie mają ręcznego rozdawania punktów ani levelu postaci.',
                      'Stary wspólny Postęp Rozwoju jest jednorazowo migrowany do sześciu osobnych liczników '
                      'bez utraty zapisanego postępu.'],
 'wieza_astralna': ['Wieża Astralna jest drugim lochowym endgame obok Krypty.',
                    'Wejście znajduje się przy Zapomnianej Kapliczce. Wpisz prowadz wieza astralna.',
                    'Do wejścia na pierwszy poziom potrzebny jest Soul Level 100.',
                    'Wieża zaczyna właściwe piętra od 100 i nie ma górnego limitu; 100-200 pozostaje ręcznie '
                    'zaprojektowaną częścią.',
                    'Boss stoi co 10 poziomów: 100, 110, 120 i dalej bez końca.',
                    'Boss blokuje drogę w górę, dopóki żyje.',
                    'Pokonanie bossa odblokowuje niezależny Astralny Portal/checkpoint.',
                    'Astralny Portal działa wyłącznie przy Astralnej Bramie.',
                    'Komenda astralportal pokazuje checkpointy.',
                    'Komenda astralportal 150 przenosi na poziom 150, jeśli checkpoint jest odblokowany.',
                    'Zwykłe moby zostawiają 1 element Astralnego ekwipunku, bossowie 3.',
                    'Ręcznie zaprojektowani bossowie 100-200 zachowują unikalne relikty; dalsi bossowie '
                    'proceduralni pojawiają się co 10 poziomów bez końca.',
                    'Wieża ma własne moby, bossów, mechaniki i klimat gwiezdny, niezależny od Krypty.',
                    'Moby i bossowie nie atakują automatycznie.',
                    'Walka działa w czasie rzeczywistym: zwykłe ataki i auto kolejka wykonują się '
                    'automatycznie.'],
 'soul_tier45_krypta200': ['Broń Duszy ma 40 Tierów rozłożonych na Soul Level 1-400.',
                           'Progi: 1, 10, 20, 25, 35, 45, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, '
                           '170, 180, 200.',
                           'Każdy Tier 2-20 ma własną jednorazową Próbę Broni Duszy u Kapłana Elora.',
                           'Po osiągnięciu progu użyj quest list Kapłan Elor, wykonaj właściwą Próbę, a '
                           'następnie wpisz unlock.',
                           'Tier 4: Soul 25 i 5 Szkieletowych Strażników.',
                           'Tier 7: Soul 60 i 3 Widma Krypty.',
                           'Tier 13: Soul 120 i boss Próby na piętrze 120 Krypty.',
                           'Tier 19: Soul 180 i boss Próby na piętrze 180 Krypty.',
                           'Tier 20 wymaga Soul 200 i kończy mistrzowską część 1-200; Próby Tierów 21-40 '
                           'kontynuują progresję Broni Duszy do Soul 400.',
                           'Stare postacie są automatycznie migrowane: dawny Tier 2->4, 3->7, 4->13, 5->19.',
                           'Nie ma resetu Soul Levelu, Soul XP ani ukończonych prób.'],
 'lancuchy_specjalistow': ['Haldor, Marcel i Orin mają teraz po 3 osobne etapy zleceń.',
                           'Etap 1 jest dostępny od levelu właściwej profesji 1.',
                           'Etap 2 wymaga ukończenia etapu 1 i levelu właściwej profesji 100.',
                           'Etap 3 wymaga ukończenia etapu 2 i levelu właściwej profesji 200.',
                           'Haldor: Żelazne sztabki, Runiczny Talizman Straży, Talizman Wiecznej Duszy.',
                           'Marcel: Pieczone ryby rzeczne, Runiczny Półmisek Rybny, Wieczna Uczta Oceanu.',
                           'Orin: Mikstury Many, Najwyższe Mikstury Leczenia, Eliksir Wiecznej Duszy.',
                           'Rozmowa ze specjalistą podaje stan każdego etapu: aktywne, ukończone, dostępne '
                           'albo zablokowane.',
                           'Po odblokowaniu wyższego etapu specjalista automatycznie proponuje najwyższy '
                           'dostępny etap.',
                           'Każdy etap pozostaje powtarzalny z 30-minutowym cooldownem.'],
 'bank': ['Bank Dusz znajduje się na Rynku u Bankiera Aldrena.',
          'prowadz bank prowadzi bezpośrednio na Rynek.',
          'bank pokazuje saldo bankowe oraz przedmioty w skrytce.',
          'bank wplac 100 wpłaca 100 srebra do wspólnego salda.',
          'bank wplac 5 zlota wpłaca 500 srebra wartości; bank wplac 1 mithril wpłaca 100000000 srebra '
          'wartości.',
          'bank wyplac <ile> <nominał> wypłaca wskazaną wartość z tego samego salda.',
          'bank wplac wszystko wpłaca całe wspólne saldo z portfela.',
          'bank wyplac wszystko wypłaca całe wspólne saldo z banku.',
          'bank wloz <przedmiot> [ile] przenosi zwykły przedmiot z inventory do trwałej skrytki.',
          'bank wyjmij <przedmiot> [ile] przenosi przedmiot ze skrytki do inventory.',
          'Założonego elementu wyposażenia nie można schować w banku.',
          'Bank jest trwały w SQLite i nie znika po wylogowaniu ani restarcie serwera.',
          'Bank nie pobiera opłat.']}

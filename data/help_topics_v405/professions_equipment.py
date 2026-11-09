"""Historyczna pomoc Soulbound v4.00.5: professions equipment."""

def make_topics():
    return {'questy_specjalistow': ['Mistrz Rzemiosła Haldor ma 3-etapowy łańcuch powtarzalnych zleceń rzemieślniczych.',
                         'Haldor prosi o 3 Żelazne sztabki i nagradza XP Młota Rzemieślniczego oraz srebrem.',
                         'Kucharz Marcel ma 3-etapowy łańcuch powtarzalnych zleceń Gotowania.',
                         'Marcel prosi o 3 Pieczone ryby rzeczne i nagradza XP Noża Kucharskiego oraz '
                         'srebrem.',
                         'Mistrz Alchemii Orin ma 3-etapowy łańcuch powtarzalnych zleceń Alchemii.',
                         'Orin prosi o 3 Mikstury Many i nagradza XP profesji Alchemia, XP Moździerza oraz '
                         'srebrem.',
                         'Każde z tych zleceń ma 30 minut odnowienia po ukończeniu.',
                         'Rozmowa ze specjalistą nadal najpierw podaje informacje o jego narzędziu i '
                         'recepturach.'],
 'sprzedaj_wszystko': ['sprzedaj wszystko siatka sprzedaje wszystkie ryby z Siatki wyłącznie rybakom na '
                       'Targu Rybnym.',
                       'sprzedaj wszystko sakwa sprzedaje Dagnie cały urobek Górnictwa: rudy, minerały i '
                       'surowe klejnoty.',
                       'sprzedaj wszystko stos sprzedaje całe drewno wyłącznie Drwalowi Branowi w Obozie '
                       'Drwala.',
                       'sprzedaj wszystko torba sprzedaje wszystkie zioła wyłącznie Zielarce Liorze w Chacie '
                       'Zielarki.',
                       'Działają też: sprzedaj wszystko ryby, rudy, drewno i ziola.',
                       'sprzedaj wszystko / sell all sprzedaje WYŁĄCZNIE niezałożone EQ z inventory u '
                       'zwykłego kupca.',
                       'Sell all nigdy nie sprzedaje mikstur, consumables, lootu, materiałów, narzędzi, '
                       'quest itemów ani aktualnie założonego EQ.',
                       'sprzedaj wszystko przedmioty działa tak samo bezpiecznie: tylko niezałożone EQ.',
                       'Każda kategoria profesyjna nadal wymaga właściwego punktu skupu.',
                       'Sprzedaż surowców profesji daje dodatkowy EXP właściwej specjalizacji: ryby -> '
                       'Wędkarstwo, urobek Dagny -> Górnictwo, drewno -> Drwalstwo, zioła -> Zielarstwo.',
                       'EXP sprzedażowy wynosi 1 bazowy EXP za sztukę i korzysta z globalnego mnożnika EXP '
                       'profesji; nie daje EXP narzędzia.',
                       'Po sprzedaży gra podaje liczbę sztuk, rodzajów i zarobek.'],
 'naturalne_naucz': ['U nauczyciela aktywnej klasy możesz uczyć się skilli naturalną nazwą kategorii.',
                     'naucz leczenie wybiera najwyżej odblokowane leczenie tej klasy, którego jeszcze nie '
                     'znasz.',
                     'naucz tarcza wybiera najwyżej odblokowaną osłonę.',
                     'naucz unik wybiera najwyżej odblokowany unik.',
                     'naucz drain albo naucz wysysanie wybiera skill wysysający życie.',
                     'naucz dobij wybiera najwyżej odblokowaną umiejętność execute.',
                     'Ofensywne przykłady: naucz ciecie, naucz pocisk, naucz ogien, naucz burza, naucz mlot, '
                     'naucz strzal.',
                     'System bierze pod uwagę tylko skille klasy nauczyciela, przy którym aktualnie stoisz.',
                     'Najpierw preferuje skill, którego jeszcze nie znasz, a potem najwyższy dostępny próg '
                     'Soul.',
                     'Pełne nazwy i numery skilli nadal działają.'],
 'czas_narzedzi': ['Każda czynność narzędzia ma teraz realny czas wykonania.',
                   'Przy profesji level 1: Wędkarstwo 16 sekund, Górnictwo 30, Drwalstwo 24, Kowalstwo 20, '
                   'Gotowanie 12, Zielarstwo 10, Alchemia 18, Jubilerstwo 20 sekund.',
                   'Czas skraca się stopniowo wraz z levelem właściwej profesji; level narzędzia nie skraca '
                   'czasu.',
                   'Przy profesji level 200: Wędkarstwo 3 sekundy, Górnictwo 10, Drwalstwo 8, Kowalstwo 7, '
                   'Gotowanie 4, Zielarstwo 3, Alchemia 6, Jubilerstwo 7 sekund.',
                   'Po wpisaniu wedka, kilof, pila, mlot, noz, sierp, mozdzierz albo szczypce gra podaje '
                   'aktualny czas akcji wynikający z levelu profesji.',
                   'Auto-łowienie, auto-kopanie, auto-Drwalstwo i auto-Zielarstwo używają tego samego '
                   'realnego czasu.',
                   'Crafting, Gotowanie i Alchemia także czekają rzeczywistą liczbę sekund przed ukończeniem '
                   'receptury.'],
 'nazwy_narzedzi': ['Po wpisaniu nazwy narzędzia gra od razu podaje jego aktualną pełną nazwę Tieru.',
                    'Przykład: wedka może powiedzieć Aktualna nazwa narzędzia: Wędka Ucznia.',
                    'Po awansie Tieru nazwa zmienia się automatycznie, np. na Wędka Rzeczna albo Wędka '
                    'Srebrnego Haczyka.',
                    'Działa dla: wedka, kilof, pila, mlot, noz, sierp, mozdzierz i szczypce.',
                    'Potem gra nadal podaje level, XP, użycia, Tier, bonus i następny Tier.',
                    'Komenda narzedzia pokazuje aktualne nazwy wszystkich posiadanych narzędzi.'],
 'odpoczynek_wszystko': ['Odpoczynek zawsze regeneruje wszystko, co można regenerować poza walką.',
                         'Co 5 sekund odnawia 10 procent maksymalnego HP oraz 10 procent maksymalnej Many.',
                         'Postać bez Many regeneruje tylko HP.',
                         'odpoczywaj, rest i regen uruchamiają ten sam pełny odpoczynek.',
                         'regen mana oraz mana regen również uruchamiają pełny odpoczynek HP i Many.',
                         'Nie ma osobnego trybu regenerującego wyłącznie Manę.',
                         'Ruch albo aktywna akcja przerywa odpoczynek.'],
 'specjalisci_profesji': ['Soulbound ma ośmiu głównych specjalistów profesji odpowiadających wszystkim ośmiu '
                          'profesjom i narzędziom.',
                          'Mistrz Wędkarstwa Neris: Targ Rybny.',
                          'Mistrz Górnictwa Kordan: Wejście do Kryształowej Jaskini.',
                          'Mistrz Drwalstwa Oren: Obóz Drwala.',
                          'Mistrz Rzemiosła Haldor: Kuźnia Dusz.',
                          'Kucharz Marcel: Karczma Pod Błękitnym Płomieniem.',
                          'Mistrzyni Zielarstwa Sena: Chata Zielarki.',
                          'Mistrz Alchemii Orin: Chata Zielarki.',
                          'Jubilerka Mirella: Pracownia Jubilerska.',
                          'Rozmowa ze specjalistą pokazuje level profesji oraz odpowiadającego narzędzia, '
                          'XP, Tier, bonus i tempo pracy.',
                          'Kucharz, Rzemieślnik i Alchemik przypominają również odpowiednią komendę '
                          'receptur.',
                          'Specjaliści są przyjaznymi NPC i nie można ich atakować.'],
 'regen_mana': ['Od v0.6.84 regen mana nie jest osobnym trybem.',
                'regen mana i mana regen uruchamiają pełny odpoczynek.',
                'Odpoczynek odnawia jednocześnie HP i Manę co 5 sekund.',
                'mana nadal pokazuje aktualną i maksymalną Manę.',
                'mana stop zatrzymuje aktywny odpoczynek.'],
 'sprzedaz_hurtowa': ['sprzedaj ryby siatka sprzedaje wszystkie ryby wyłącznie rybakom na Targu Rybnym.',
                      'sprzedaj rudy sakwa sprzedaje Dagnie cały urobek Górnictwa z Sakwy, w tym rudy, '
                      'minerały i surowe klejnoty.',
                      'sprzedaj drewno stos sprzedaje całe drewno wyłącznie Drwalowi Branowi w Obozie '
                      'Drwala.',
                      'sprzedaj ziola torba sprzedaje wszystkie zioła wyłącznie Zielarce Liorze w Chacie '
                      'Zielarki.',
                      'Skup jest profesyjny: ryby tylko Targ Rybny; rudy, minerały i surowe klejnoty tylko '
                      'Dagna; drewno tylko Drwal Bran; zioła tylko Zielarka Liora.',
                      'Hurtowa sprzedaż podaje liczbę sztuk, liczbę rodzajów i łączny zarobek.',
                      'Sprzedaż daje EXP Charyzmy zależny od wartości transakcji; hurtowa sprzedaż nie '
                      'pompuje Charyzmy liniowo liczbą tanich sztuk.',
                      'sprzedaj przedmioty sprzedaje z inventory tylko rzeczy z jawną ceną sprzedaży i '
                      'dozwolone w aktualnej lokacji.',
                      'Duplikat możesz wskazać numerem, np. sprzedaj 2.talizman korzeni; założone '
                      'egzemplarze nie są sprzedawane.',
                      'sprzedaj przedmioty nie sprzedaje narzędzi, mikstur, założonego wyposażenia ani '
                      'rzeczy bez ceny.'],
 'mana_stats_eq': ['stats zawsze pokazuje Mana: aktualna z maksymalnej.',
                   'Klasa bez Many zobaczy Mana: 0 z 0.',
                   'Klasa magiczna albo multiclass magiczny zobaczy aktualną i maksymalną Manę.',
                   'eq działa jak equipment.'],
 'wartosc_magazynow': ['Wszystkie cztery magazyny profesji pokazują teraz podsumowanie ilości i wartości.',
                       'siatka/net: łączna liczba ryb, liczba gatunków i wartość sprzedaży.',
                       'sakwa/bag: cały urobek Górnictwa — rudy, minerały i surowe klejnoty; pokazuje liczbę '
                       'sztuk, rodzajów i wartość sprzedaży u Dagny.',
                       'drewno/stos/woodpile: łączna liczba sztuk drewna, liczba rodzajów i wartość '
                       'sprzedaży.',
                       'ziola/herbs: łączna liczba ziół, liczba rodzajów i wartość sprzedaży.',
                       'Srebro, złoto i mithril są nominałami jednego wspólnego salda.',
                       'Podsumowania obejmują tylko zawartość danego magazynu, nie zwykły inventory.',
                       'Sprawdzenie magazynu niczego nie sprzedaje ani nie usuwa.'],
 'wartosc_siatki': ['Komenda siatka albo net pokazuje każdą rybę i jej ilość.',
                    'Na końcu podaje łączną liczbę wszystkich ryb w siatce.',
                    'Podaje też liczbę różnych gatunków ryb.',
                    'Szacowany zarobek jest liczony z aktualnych cen sprzedaży każdej ryby pomnożonych przez '
                    'jej ilość.',
                    'Portfel podaje jedno saldo rozbite na mithril, złoto i srebro.',
                    'Wartość obejmuje tylko ryby aktualnie znajdujące się w Siatce, nie ryby w zwykłym '
                    'inventory.',
                    'Podsumowanie nie sprzedaje ryb. To tylko informacja przed sprzedażą.'],
 'tempo_profesji': ['Aktualnie wszystkie osiem profesji ma zakres 1-400; tempo pracy zależy od profesji, a '
                    'jakość/odblokowania zasobów od osobnego narzędzia.',
                    'Każda profesja korzysta z osiągalnej krzywej 1-400; stare progi 1-200 pozostają '
                    'zachowane, a 201-400 jest dalszą progresją.',
                    'Level profesji skraca czas pracy i spełnia wymagania receptur/zleceń; level narzędzia '
                    'odblokowuje lepsze surowce oraz zwiększa jakość/bonus urobku.',
                    'Wszystkie osiem profesji rozwija się od 1 do 400 według aktualnej progresji.',
                    'Narzędzia mają osobną progresję XP 1-400; wpisz help narzedzia200 albo help '
                    'progresja400 po szczegóły.',
                    'Nie ma trwałości ani zużywania narzędzi.'],
 'zakladanie_lootu': ['Gracz sam decyduje, jaki konkretny element EQ zakłada. Wyjątek to pierścienie i '
                      'talizmany: po wybraniu przedmiotu gra może automatycznie wybrać wolny albo słabszy z '
                      'dwóch równoległych slotów.',
                      'Gdy masz kilka przedmiotów dla jednego slotu, załóż <slot> pokazuje dostępne opcje i '
                      'niczego nie zmienia. Aby założyć wybrany przedmiot, wpisz jego pełną nazwę.',
                      'Całe EQ ma wymaganie Biegłości, nie Soul Levelu. Poziom startowy to 1, a kolejne '
                      'progi są co 10 aż do 400. Materiałowe EQ ma kilka wariantów Biegłości w ramach tego '
                      'samego materiału. Dla nieklasowego EQ liczy się najwyższa Biegłość aktywnej klasy.',
                      'Jeśli zwykły slot jest zajęty, samo załóż hełm / zbroja / rękawice / nogi / buty '
                      'niczego nie podmienia. Dokładna nazwa nowego przedmiotu jest świadomą decyzją o '
                      'zastąpieniu starego.',
                      'Pierścienie i talizmany zakładają się automatycznie: najpierw do wolnego slotu, a gdy '
                      'oba są zajęte — zastępują słabszy. Ręczne sloty 1/2 nadal działają.',
                      'Skróty: zp pokazuje pierścienie i zp <numer> zakłada wybrany; zt robi to samo dla '
                      'talizmanów. zp1/zp2 i zt1/zt2 wymuszają konkretny slot.',
                      'Nowe sloty EQ: naramienniki, pas, peleryna, karwasze, kolczyki i relikt.',
                      'Zdejmowanie jest ręczne: zdejmij hełm, zbroja, naramienniki, pas, peleryna, karwasze, '
                      'relikt, pierścień 1, talizman 2 itd.',
                      'Założone EQ nadal jest niesprzedawalne; po zdjęciu staje się zwykłym wolnym '
                      'egzemplarzem i może zostać sprzedane, jeśli jego kategoria na to pozwala.',
                      'Zmiana ekwipunku podczas aktywnej walki nadal jest zablokowana.'],
 'skill200': ['Wszystkie umiejętności mają Skill Level od 1 do 400 i rozwijają się wyłącznie przez używanie '
              'konkretnego skilla/spella.',
              'v0.8.64 zmniejsza przyrost wymaganego Skill XP z +25 do +8 na level i podnosi typową nagrodę '
              'za użycie do 25-35 XP.',
              'Moc rośnie malejąco: około x1,495 przy Skill Level 100 i około x1,745 przy 200, zamiast '
              'starego x2,49.',
              'Cooldown skraca się przez całe 1-400: około 12,4 procent przy 100, około 24,9 procent przy '
              '200 i maksymalnie około 35 procent przy 400.',
              'Na Skill Level 400 XP zostaje wyzerowane i skill osiąga maksymalny poziom.'],
 'wolniejszy_xp_narzedzi': ['Narzędzia mają level 1-400 i 40 Tierów, bez trwałości i bez psucia.',
                            'v0.8.64 używa krzywej: 60 + 8 razy level minus 1 XP do następnego poziomu '
                            'narzędzia.',
                            'Level 1->2 wymaga 60 XP; level 100->101 852 XP; level 199->200 1644 XP.',
                            'XP przyznawane przez konkretne akcje pozostaje zależne od aktywności i bonusów '
                            'narzędzia.',
                            'Nieużywane narzędzia nie zdobywają XP ani użyć.'],
 'skille100_200': ['Każda z 14 klas dostała 4 nowe umiejętności endgame.',
                   'Historyczne progi endgame są teraz Biegłością klasy 100, 140, 180 i 200.',
                   'Łącznie dodano 48 nowych skilli.',
                   'Nowe skille trzeba nauczyć się u właściwego nauczyciela klasy, tak jak wcześniejsze.',
                   'Skill Level każdego skilla rozwija się osobno od 1 do 400; zakres 201-400 ma malejący '
                   'przyrost mocy.',
                   'Cooldown, Mana, Skill XP i krytyki pozostają zgodne z istniejącym systemem; walka działa '
                   'teraz w czasie rzeczywistym.',
                   'Wpisz skills, skillnames albo porozmawiaj z nauczycielem klasy.'],
 'naturalne_uzyj': ['Komenda użyj obsługuje naturalne intencje skilli.',
                    'Przykłady: użyj heal, użyj tarcza, użyj unik, użyj drain, użyj dobij goblin.',
                    'Ofensywne skróty: użyj ciecie goblin, użyj pocisk goblin, użyj ogien goblin, użyj burza '
                    'goblin, użyj strzal goblin.',
                    'Gra wybiera najwyżej odblokowany i nauczony skill pasujący do intencji.',
                    'Jeśli dwa skille mają taki sam najlepszy wynik w multiclassie, gra nie wybierze losowo. '
                    'Użyj pełnej nazwy.',
                    'Pełne komendy skill, cast, użyj umiejętność oraz użyj czar nadal działają.'],
 'prowadz_most': ['Komenda prowadz most prowadzi bezpośrednio do lokacji Kamienny Most.',
                  'Działa też walk most, idz most, go most oraz prowadz kamienny most.',
                  'Prowadzenie wykorzystuje ten sam bezpieczny system wyznaczania trasy co pozostałe cele.'],
 'uzyj_skilla': ['Komenda użyj może uruchamiać nauczone umiejętności i czary.',
                 'Przykład Wojownika: użyj ciecie goblin uruchamia Potężne Cięcie, jeśli skrót jest '
                 'jednoznaczny i skill jest nauczony.',
                 'Przykład Maga: użyj pocisk goblin może uruchomić Pocisk Arkanów.',
                 'Przykład Czarownika: użyj plomien goblin może uruchomić Płomień Otchłani.',
                 'Działa też użyj czar <nazwa> [cel], use spell <name> [target], skill <nazwa> [cel] i cast '
                 '<nazwa> [cel].',
                 'Jeżeli krótka nazwa pasuje do kilku aktywnych skilli, użyj pełnej nazwy.',
                 'Cooldown, Mana, Skill Level i Skill XP pozostają bez zmian.']}

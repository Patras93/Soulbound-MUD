SOULBOUND v0.6.30 THREE CURRENCIES
==========================

Duży build rozbudowujący działający serwer online do pierwszej właściwej wersji świata MUD.

NAJWAŻNIEJSZE ZASADY
--------------------
- Postać NIE ma levelu.
- Postać NIE ma XP postaci.
- Nie rozdaje się ręcznie punktów statystyk.
- Statystyki rosną automatycznie podczas gry.
- Klasy fizyczne rozwijają Siłę, Zręczność i Kondycję.
- Inteligencja i Siła Woli klas fizycznych nie rosną.
- Klasy magiczne rozwijają Inteligencję i Siłę Woli.
- Broń Duszy ma osobny Soul Level 1-100.
- Broń Duszy ma Soul Tier 1-3.

WORLD CORE
----------
- 31 lokacji połączonych kierunkami.
- Miasto Dusz.
- Dzicz.
- Podziemia.
- NPC.
- Zadania.
- Potwory widoczne dla wszystkich graczy.
- Turowa walka komendą attack.
- Ucieczka komendą flee.
- Śmierć i odrodzenie w świątyni.
- Utrata 10% posiadanego złota przy śmierci.
- Złoto.
- Sklepy.
- Przedmioty.
- Mikstury.
- Podstawowe pancerze i talizmany.
- Inventory i equipment.
- Drop z przeciwników.
- Automatyczne zapisy postaci.
- Zapis questów i wyposażenia do SQLite.
- Migracja starej bazy v0.5.1 bez kasowania kont i postaci.

PIERWSZE QUESTY
---------------
1. Problem goblinów — Kapitan Arven.
2. Cienie w gaju — Zielarka Mira.
3. Odłamki dla kowala — Kowal Doran.

WAŻNE
-----
Po aktualizacji NIE usuwaj Railway Volume.
Stary /data/soulbound.db zostanie automatycznie rozszerzony o nowe dane.


EKONOMIA v0.6.2
---------------
Soulbound ma teraz trzy trwałe waluty:
- srebro,
- złoto,
- mithril.

Domyślny kurs:
- 100 srebra = 1 złoto,
- 1000 złota = 1 mithril.

Komendy:
money
exchange
exchange gold
exchange mithril

Sklepy mogą wyceniać przedmioty w różnych walutach.
Questy i potwory mogą nagradzać srebrem, złotem i mithrilem.
Mithril jest najrzadszą walutą.


QUEST STARTOWY v0.6.3
---------------------
W Świątyni Odrodzenia stoi Kapłan Elor.
Komenda:
talk elor

Zadanie:
Szczury pod świątynią

Cel:
- zejść z Temple komendą down,
- zabić 10 Szczurów Świątynnych w piwnicy,
- wrócić do Kapłana Elora,
- ponownie użyć talk elor.

Nagroda:
- 120 EXP rozwoju,
- 2 złota,
- 1 Mikstura leczenia.

EXP ROZWOJU
-----------
Postać nadal NIE ma levelu.
EXP rozwoju zasila automatyczny wzrost statystyk.
Nie ma ręcznego rozdawania punktów.

SOUL LEVEL
----------
Tempo Soul Level zostało wyraźnie spowolnione:
- próg Soul XP na poziomy jest około 3 razy większy,
- Soul XP z potworów został obniżony.


PROFESJE v0.6.4
---------------
Dodano dwie pierwsze profesje:
- Wędkarstwo,
- Górnictwo.

Obie profesje mają automatyczny poziom 1-100 oraz własne XP.

WĘDKARSTWO
----------
Wymaga Wędki.
Wędkę kupisz na Rynku.

Komenda:
fish

Łowiska:
- Srebrna Łąka,
- Brzeg Rzeki,
- Kamienny Most.

Wędka ma własny level 1-100 i własne XP.
Im wyższy level Wędki, tym lepsze ryby można wyłowić.

Przykładowe połowy:
- Mała ryba,
- Karp rzeczny,
- Srebrny pstrąg,
- Złoty pstrąg,
- Pradawny jesiotr,
- Księżycowy węgorz.

GÓRNICTWO
---------
Wymaga Kilofa.
Kilof kupisz w Kuźni Dusz.

Komenda:
mine

Złoża:
- Wejście do Kryształowej Jaskini,
- Kryształowy Tunel,
- Kryształowa Komnata.

Kilof ma własny level 1-100 i własne XP.
Im wyższy level Kilofa, tym lepsze rudy można wydobywać.

Rudy:
- Odłamek skały,
- Ruda miedzi,
- Ruda żelaza,
- Ruda srebra,
- Ruda złota,
- Ruda mithrilu.

MITHRIL
-------
Ruda mithrilu jest niezwykle rzadka.
Nie może wypaść przy niskim levelu Kilofa.

Minimalny level Kilofa dla Rudy mithrilu:
60.

Szansa:
- level 60-79: 0,25%,
- level 80-94: 0,5%,
- level 95-100: 1%.

To jest Ruda mithrilu jako surowiec, a nie waluta mithril.

KOMENDY
-------
professions
tools
fish
mine
sell <przedmiot>

Ryby sprzedaje się na Rynku lub w Karczmie.
Rudy sprzedaje się w Kuźni Dusz.


POJEMNIKI PROFESJI v0.6.5
-------------------------
Dodano dwa trwałe, osobne magazyny:
- Siatka na ryby,
- Sakwa górnicza.

Nie są przedmiotami w zwykłym inventory.

Nowo złowione ryby trafiają automatycznie do Siatki.
Nowo wydobyte rudy trafiają automatycznie do Sakwy.

Komendy polskie i angielskie:
siatka
net

sakwa
bag

wloz ryba siatka
włóż ryba siatka
put fish net

wloz ruda sakwa
włóż ruda sakwa
put ore bag

wyjmij ryba siatka
take fish net

wyjmij ruda sakwa
take ore bag

Można też podawać konkretną nazwę surowca.

Sprzedaż ryb i rud automatycznie sprawdza najpierw odpowiedni pojemnik,
a dopiero potem zwykły ekwipunek.

JĘZYK KOMEND
------------
Serwer respektuje zarówno komendy polskie, jak i angielskie.
Polskie aliasy działają również w wielu przypadkach bez polskich znaków,
np.:
wedkuj
kop
profesje
narzedzia
wloz ryba siatka
sprzedaj ruda


TARG RYBNY I PRÓBA RYBAKA v0.6.6
--------------------------------
Nowa lokacja:
Targ Rybny.

Z głównego Rynku idź:
north

Wędka została przeniesiona na Targ Rybny.
Nie kupuje się jej już na zwykłym Rynku.

RYBAK TOMAS
-----------
Na Targu Rybnym:
talk tomas

Quest:
Próba Rybaka

Cel:
przynieś 30 dowolnych ryb.

Quest liczy ryby z:
- Siatki na ryby,
- zwykłego inventory.

Przy oddaniu najpierw pobiera ryby z Siatki, a potem z inventory.

Nagroda:
- 1000 XP Wędkarstwa,
- 1000 XP Wędki,
- 200 złota.

Wędkarstwo i Wędka mają osobne levele.
Górnictwo i Kilof mają osobne levele.
Wędka i Kilof nigdy nie współdzielą XP ani levelu.


RZADKIE RYBY v0.6.7
-------------------
Rozszerzono tabelę połowów dla wysokiego levelu Wędki.

Nowe ryby:
- Śledź,
- Makrela,
- Łosoś,
- Tuńczyk,
- Miecznik,
- Tuńczyk błękitnopłetwy,
- Rekin rafowy,
- Rekin młot,
- Żarłacz biały,
- Widmowy marlin.

Przybliżone progi:
- od levelu 10 Wędki: Śledź,
- od levelu 25: Makrela i Łosoś,
- od levelu 40: Tuńczyk i Miecznik,
- od levelu 60: Tuńczyk błękitnopłetwy i Rekin rafowy,
- od levelu 75: Rekin młot i bardzo rzadka szansa na Żarłacza białego,
- od levelu 90: najlepsza tabela połowów i ekstremalnie rzadki Widmowy marlin.

Najrzadsze ryby mają wysoką wartość sprzedaży.


CENY I PROGI RZADKICH RYB v0.6.8
--------------------------------
Śledź jest dostępny dopiero od levelu 30 Wędki.

Ceny:
- Śledź: 1 złoto,
- Makrela: 2 złota,
- Łosoś: 5 złota,
- Tuńczyk: 15 złota,
- Miecznik: 30 złota,
- Tuńczyk błękitnopłetwy: 75 złota,
- Rekin rafowy: 125 złota,
- Rekin młot: 250 złota,
- Żarłacz biały: 500 złota,
- Widmowy marlin: 1 mithril.

1000 złota = 1 mithril.


CZYSTY MITHRIL Z KOPALNI v0.6.9
-------------------------------
Ruda mithrilu nie jest już aktywnym dropem.

Na wysokim levelu Kilofa można wydobyć bezpośrednio:
1 mithril

Mithril trafia od razu do portfela walutowego, nie do Sakwy.

Minimalny level Kilofa:
80

Szanse:
- Kilof 80-89: 0,10%
- Kilof 90-99: 0,25%
- Kilof 100: 0,50%

Powód niskich szans:
1 mithril = 1000 złota.

Stara Ruda mithrilu pozostaje tylko jako przedmiot zgodności dla istniejących baz,
ale nie można jej już normalnie wydobyć.


MORSKIE WĘDKARSTWO v0.6.10
--------------------------
Dodano Port Dusz i Morskie Molo.

Droga:
Targ Rybny -> east -> Port Dusz -> east -> Morskie Molo.

Na Morskim Molo komenda fish korzysta z osobnej tabeli ryb morskich.

Nowe ryby:
- Sardynka,
- Sardela,
- Dorsz,
- Labraks,
- Plamiak,
- Mintaj,
- Flądra,
- Halibut.

Zachowano też wysokopoziomowe ryby morskie:
- Śledź,
- Makrela,
- Tuńczyk,
- Miecznik,
- Tuńczyk błękitnopłetwy,
- Rekin rafowy,
- Rekin młot,
- Żarłacz biały,
- Widmowy marlin.

Śledź nadal wymaga minimum levelu 30 Wędki.

Łowiska rzeczne i morskie mają teraz osobne tabele połowów.
Dorsz i inne ryby morskie nie wypadają na łące ani przy rzecznej tabeli.


AUTO-ŁOWIENIE v0.6.11
---------------------
Komendy:
low on
łów on
fish on

Wyłączenie:
low off
łów off
fish off

Auto-łowienie wykonuje kolejne połowy automatycznie i respektuje cooldown profesji.
Nowe ryby nadal trafiają do Siatki na ryby.

Auto-łowienie zatrzymuje się automatycznie, gdy:
- ruszysz do innej lokacji,
- rozpoczniesz walkę,
- opuścisz łowisko,
- stracisz Wędkę,
- rozłączysz się.

PROWADZENIE / WALK TO
---------------------
Polski:
prowadz Targ Rybny
prowadź Morskie Molo

Angielski:
walk to Fish Market
walk to Sea Pier

Serwer znajduje najkrótszą drogę po istniejących wyjściach i przeprowadza postać
przez kolejne lokacje.

Komenda:
lokalizacja
location

Pokazuje aktualną lokację, strefę i wyjścia.


KOMENDY WALKI v0.6.12
---------------------
Do rozpoczęcia/wykonania tury walki działają teraz równolegle:
attack <przeciwnik>
atakuj <przeciwnik>
zabij <przeciwnik>
kill <przeciwnik>


LISTA SPRZEDAWCY v0.6.13
------------------------
Aby przejrzeć ofertę sprzedawcy w aktualnej lokacji użyj:

list
lista
shop
sklep

Wszystkie cztery komendy pokazują dostępne przedmioty, ceny i opisy.


MIKSTURY I HP v0.6.14
---------------------
Po użyciu Mikstury leczenia serwer mówi teraz:
- ile HP zostało odzyskane,
- aktualne HP,
- maksymalne HP.

Przykład:
Masz teraz 72 z 95 HP.


STATYSTYKI I WALKA v0.6.15
--------------------------
Statystyki mają teraz jednoznaczne role:

Kondycja:
- zwiększa maksymalne HP.

Siła:
- zwiększa obrażenia fizyczne.

Zręczność:
- zwiększa Szybkość,
- Szybkość zwiększa szansę uniknięcia kontrataku,
- unik ma limit 35%.

Inteligencja:
- zwiększa maksymalną Manę,
- zwiększa Moc czarów.

Siła Woli:
- zwiększa Obrony magiczną,
- nie zwiększa już obrażeń magicznych.

Pancerz:
- odpowiada za obronę fizyczną.

Przeciwnicy mogą zadawać obrażenia fizyczne lub magiczne.
Upiór Krypty i Kryształowy Strażnik korzystają z obrażeń magicznych.


KREATOR POSTACI v0.6.16
-----------------------
Przy wyborze rasy serwer podaje teraz:
- opis rasy,
- mocne i słabe strony,
- wartości wszystkich pięciu statystyk,
- informację, co statystyki robią w walce.

Przy wyborze klasy serwer podaje:
- typ klasy: fizyczna lub magiczna,
- styl gry i główne zalety,
- które statystyki rosną automatycznie,
- nazwę Broni Duszy.

Dzięki temu wszystkie informacje są czytane tekstowo przez NVDA podczas tworzenia postaci.


ROZWÓJ STATYSTYK v0.6.17
------------------------
Od tej wersji KAŻDA klasa rozwija automatycznie wszystkie pięć statystyk:

- Siła,
- Zręczność,
- Kondycja,
- Inteligencja,
- Siła Woli.

Dotyczy to klas fizycznych i magicznych.

Przy każdym pełnym progu rozwoju:
Siła +1
Zręczność +1
Kondycja +1
Inteligencja +1
Siła Woli +1

Postać nadal NIE ma levelu.
Rozwój odbywa się wyłącznie przez statystyki.


AUTO-KOPANIE v0.6.18
--------------------
Włączenie:
kop on
mine on

Wyłączenie:
kop off
mine off

Auto-kopanie:
- wymaga Kilofa,
- działa tylko w lokacjach górniczych,
- respektuje cooldown profesji,
- rozwija Górnictwo i Kilof normalnie,
- może wydobyć czysty mithril na odpowiednio wysokim levelu Kilofa,
- zatrzymuje się przy ruchu,
- zatrzymuje się przy walce,
- zatrzymuje się po opuszczeniu kopalni,
- zatrzymuje się przy rozłączeniu.

Auto-kopanie i auto-łowienie nie działają jednocześnie.
Włączenie jednego systemu automatycznie wyłącza drugi.


PEŁNY SYSTEM POMOCY I OPISÓW v0.6.19
------------------------------------
Główna pomoc:
help
pomoc

Lista działów:
help tematy

Pełna lista komend:
help komendy

Pełny przewodnik:
help wszystko

Przykładowe działy:
help podstawy
help nawigacja
help statystyki
help walka
help dusza
help pieniadze
help ekwipunek
help zadania
help profesje
help wedkarstwo
help gornictwo
help pojemniki
help sklepy
help gracze
help smierc
help rasy
help klasy
help opisy

SYSTEM OPISÓW
-------------
Komenda:
opis <nazwa>
describe <name>

Bez argumentu:
opis
opisuje aktualną lokację.

Przykłady:
opis Dorsz
opis Mikstura leczenia
opis Rybak Tomas
opis Upiór Krypty
opis Morskie Molo
opis Próba Rybaka
opis Elf
opis Mag
opis Kondycja
opis Siła Woli
opis mithril
opis Wędkarstwo
opis Broń Duszy

System opisuje wszystkie przedmioty, NPC, przeciwników, lokacje, zadania,
rasy, klasy, statystyki, profesje, waluty, Broń Duszy i magazyny profesji.


NAJNOWSZE ZMIANY v0.6.20
------------------------
Komendy:
changes
zmiany
changelog

Każda z nich pokazuje tylko:
- numer najnowszej wersji,
- najnowszy zestaw zmian.

Nie pokazuje całej starej historii, dzięki czemu wynik jest krótki i wygodny dla NVDA.

Pomoc:
help changes
help zmiany


PEŁNY EKWIPUNEK U KOWALA v0.6.21
--------------------------------
W Kuźni Dusz Kowal Doran sprzedaje teraz pełny żelazny zestaw ochronny.

Elementy:
1. Żelazny hełm — głowa — Obrona +2 — 1 złoto.
2. Żelazny napierśnik — korpus — Obrona +4 — 2 złota.
3. Żelazne rękawice — dłonie — Obrona +1 — 1 złoto.
4. Żelazne nogawice — nogi — Obrona +3 — 2 złota.
5. Żelazne buty — stopy — Obrona +1 — 1 złoto.
6. Talizman Kowala — talizman — Obrona +1 — 2 złota.

Pełny zestaw:
- 6 osobnych slotów,
- 12 punktów łącznej obrony fizycznej,
- 9 złota za cały komplet.

Kilof nadal jest sprzedawany osobno przez Kowala.

Komendy:
list
lista
shop
sklep

Po zakupie:
equip <nazwa przedmiotu>

Podgląd założonego zestawu:
equipment

Zwykłej broni kowal nie sprzedaje, ponieważ podstawową bronią postaci
pozostaje przypisana do klasy Broń Duszy.


UMIEJĘTNOŚCI KLASOWE v0.6.22
-----------------------------
Każda z 12 klas ma 3 unikalne aktywne umiejętności.
Odblokowanie: Soul Level 1, 25 i 60. Postać nadal NIE ma levelu.

Komendy:
skills
umiejetnosci
umiejętności
skill <nazwa lub numer> [cel]
umiejetnosc <nazwa lub numer> [cel]

Przykłady:
skill 1 goblin
skill Potężne Cięcie goblin
umiejetnosc 1 goblin

Klasy:
Wojownik — Potężne Cięcie, Okrzyk Wojenny, Niezłomność.
Berserker — Krwawy Zamach, Szał Krwi, Egzekucja.
Łotrzyk — Cios z Cienia, Podwójne Ostrze, Zniknięcie.
Łowca — Celny Strzał, Salwa Echa, Instynkt Łowcy.
Mnich — Uderzenie Ducha, Seria Ciosów, Medytacja.
Strażnik — Miażdżący Cios, Bastion, Mur Duszy.
Mag — Pocisk Arkanów, Łańcuch Energii, Bariera Arkanów.
Nekromanta — Dotyk Śmierci, Wysysanie Duszy, Żniwo Dusz.
Kapłan — Święty Młot, Wielkie Leczenie, Boska Tarcza.
Czarownik — Ostrze Otchłani, Płomień Otchłani, Pakt Krwi.
Druid — Ciernie, Uzdrowienie Natury, Gniew Burzy.
Psionik — Impuls Umysłu, Fala Psioniczna, Bariera Umysłu.


NAUCZYCIELE W SALI GILDII v0.6.23
---------------------------------
W Sali Gildii jest 12 nauczycieli, po jednym dla każdej klasy.

teachers / nauczyciele / trenerzy — lista nauczycieli.
talk <nauczyciel> — lekcja klasy i jej umiejętności.

WALKA TUROWA
------------
Jedna akcja gracza = jedna tura.
Jeśli przeciwnik żyje, wykonuje potem dokładnie jedną swoją turę.

Turę zużywają:
- attack / zabij / kill,
- ofensywny skill,
- leczenie klasowe,
- osłona,
- gwarantowany unik,
- wzmocnienie,
- mikstura leczenia.

Zmiana ekwipunku podczas aktywnej walki jest zablokowana.


GILDIA I NAUKA UMIEJĘTNOŚCI v0.6.24
-----------------------------------
Nauczyciele nie stoją już wszyscy w Sali Głównej.

Gildia Dusz ma teraz 6 sal:
- Sala Oręża Gildii — Wojownik i Berserker,
- Galeria Cieni Gildii — Łotrzyk i Łowca,
- Sala Dyscypliny Gildii — Mnich i Strażnik,
- Komnata Arkanów Gildii — Mag i Psionik,
- Komnata Mrocznych Sztuk — Nekromanta i Czarownik,
- Sanktuarium Gildii — Kapłan i Druid.

teachers / nauczyciele pokazuje nauczycieli oraz ich dokładne lokacje.
Można użyć prowadz <lokacja>, aby automatycznie dojść do odpowiedniej sali.

NAUKA SKILLI
------------
Skille NIE są już automatycznie dostępne po osiągnięciu Soul Level.

Soul Level jest tylko wymaganiem:
- skill 1: można nauczyć się od Soul Level 1,
- skill 2: można nauczyć się od Soul Level 25,
- skill 3: można nauczyć się od Soul Level 60.

Aby nauczyć się umiejętności:
1. Idź do nauczyciela swojej klasy.
2. Wpisz talk <nauczyciel>.
3. Wpisz learn 1, learn 2, learn 3 albo naucz <nazwa>.

Przykłady:
learn 1
naucz Potężne Cięcie
ucz 2

Nauczone umiejętności są trwale zapisywane w SQLite.
Po ponownym wejściu do gry postać nadal je zna.

skills / umiejetnosci pokazuje trzy stany:
- nauczona,
- gotowa do nauki u nauczyciela,
- zablokowana przez wymagany Soul Level.

Walka pozostaje turowa.


NAZWY SKILLI v0.6.25
--------------------
Nowe komendy:
skillnames
nazwyskilli
nazwyumiejetnosci

Pokazują wszystkie 36 skilli, po 3 dla każdej klasy.

Wojownik:
1. Potężne Cięcie
2. Okrzyk Wojenny
3. Niezłomność

Berserker:
1. Krwawy Zamach
2. Szał Krwi
3. Egzekucja

Łotrzyk:
1. Cios z Cienia
2. Podwójne Ostrze
3. Zniknięcie

Łowca:
1. Celny Strzał
2. Salwa Echa
3. Instynkt Łowcy

Mnich:
1. Uderzenie Ducha
2. Seria Ciosów
3. Medytacja

Strażnik:
1. Miażdżący Cios
2. Bastion
3. Mur Duszy

Mag:
1. Pocisk Arkanów
2. Łańcuch Energii
3. Bariera Arkanów

Nekromanta:
1. Dotyk Śmierci
2. Wysysanie Duszy
3. Żniwo Dusz

Kapłan:
1. Święty Młot
2. Wielkie Leczenie
3. Boska Tarcza

Czarownik:
1. Ostrze Otchłani
2. Płomień Otchłani
3. Pakt Krwi

Druid:
1. Ciernie
2. Uzdrowienie Natury
3. Gniew Burzy

Psionik:
1. Impuls Umysłu
2. Fala Psioniczna
3. Bariera Umysłu


MAŁE LECZENIE KAPŁANA v0.6.26
-----------------------------
Kapłan otrzymał dodatkową umiejętność dla początkujących:

Małe Leczenie
- do nauki od Soul Level 1,
- Mana: 3,
- bazowy cooldown: 6 sekund,
- bazowe leczenie: 12 procent maksymalnego HP,
- rośnie razem ze Skill Level.

Kapłan ma teraz 4 skille:
1. Małe Leczenie
2. Święty Młot
3. Wielkie Leczenie
4. Boska Tarcza

SYSTEM LEVELOVANIA SKILLI
-------------------------
Każda nauczona umiejętność ma własny:
- Skill Level 1-100,
- Skill XP,
- licznik użyć.

Nie jest to level postaci.
Każdy skill rozwija się osobno tylko przez używanie właśnie tego skilla.

Wymagany XP do kolejnego Skill Level:
50 + (aktualny level - 1) * 25.

Udane użycie skilla daje 8-12 Skill XP.

Wyższy Skill Level:
- zwiększa obrażenia skilli ofensywnych,
- zwiększa leczenie,
- zwiększa siłę osłon,
- zwiększa siłę buffów,
- skraca cooldown wszystkich skilli do maksymalnie około 30 procent na Skill Level 100.

skills / umiejetnosci pokazuje:
- czy skill jest nauczony,
- Skill Level,
- Skill XP,
- liczbę użyć,
- bazowy i aktualny cooldown.


8 TIERÓW WĘDKI I KILOFA v0.6.27
-------------------------------
Tier 1: level 1-14
Tier 2: level 15-29
Tier 3: level 30-44
Tier 4: level 45-59
Tier 5: level 60-74
Tier 6: level 75-89
Tier 7: level 90-99
Tier 8: level 100

Wędka:
1. Prosta — 0%
2. Wzmocniona — 2%
3. Precyzyjna — 4%
4. Profesjonalna — 6%
5. Głębinowa — 8%
6. Mistrzowska — 10%
7. Legendarna — 12%
8. Mityczna — 15%

Bonus Wędki daje szansę na drugi egzemplarz złowionej ryby.

Kilof:
1. Prosty — 0%
2. Wzmocniony — 2%
3. Stalowy — 4%
4. Hartowany — 6%
5. Kryształowy — 8%
6. Mistrzowski — 10%
7. Legendarny — 12%
8. Mityczny — 15%

Bonus Kilofa daje szansę na dodatkową zwykłą rudę.
Czysty mithril NIE jest podwajany.

tools / narzedzia pokazuje level, XP, Tier, nazwę, bonus i próg następnego Tieru.


PEŁNE NAZWY TIERÓW v0.6.28
--------------------------
Komendy:
tiers
tiery
tiernazwy
nazwytierow
nazwytierów

WĘDKA:
Tier 1 — Wędka Ucznia
Tier 2 — Wędka Rzeczna
Tier 3 — Wędka Srebrnego Haczyka
Tier 4 — Wędka Morskiego Wiatru
Tier 5 — Wędka Głębin
Tier 6 — Wędka Mistrza Połowu
Tier 7 — Wędka Legendarnego Wędkarza
Tier 8 — Wędka Mitycznych Głębin

KILOF:
Tier 1 — Kilof Ucznia
Tier 2 — Kilof Górnika
Tier 3 — Kilof Stalowego Ostrza
Tier 4 — Kilof Hartowanego Rdzenia
Tier 5 — Kilof Kryształowej Żyły
Tier 6 — Kilof Mistrza Kopalni
Tier 7 — Kilof Legendarnych Złóż
Tier 8 — Kilof Mitycznego Rdzenia


RANGI PROFESJI v0.6.29
----------------------
Wędkarstwo i Górnictwo mają po 8 rang.

Progi:
1. level 1-14
2. level 15-29
3. level 30-44
4. level 45-59
5. level 60-74
6. level 75-89
7. level 90-99
8. level 100

WĘDKARSTWO:
1. Uczeń Wędkarstwa
2. Adept Wędkarstwa
3. Czeladnik Wędkarstwa
4. Specjalista Wędkarstwa
5. Ekspert Wędkarstwa
6. Mistrz Wędkarstwa
7. Arcymistrz Wędkarstwa
8. Legenda Wędkarstwa

GÓRNICTWO:
1. Uczeń Górnictwa
2. Adept Górnictwa
3. Czeladnik Górnictwa
4. Specjalista Górnictwa
5. Ekspert Górnictwa
6. Mistrz Górnictwa
7. Arcymistrz Górnictwa
8. Legenda Górnictwa

Komendy:
professions
profesje
rangi
ranks
rangiprofesji
professionranks

MAGAZYNY PROFESJI
-----------------
Każda złowiona ryba trafia automatycznie do Siatki na ryby.
Każda zwykła wydobyta ruda trafia automatycznie do Sakwy górniczej.
Nie trafiają automatycznie do zwykłego inventory.

Bonus Tieru Wędki także trafia do Siatki.
Bonus Tieru Kilofa także trafia do Sakwy.
Czysty mithril jest wyjątkiem i nadal trafia bezpośrednio do portfela.

Sprzedaż ryb najpierw pobiera je z Siatki.
Sprzedaż rud najpierw pobiera je z Sakwy.


ODMIANA IMIENIA POSTACI v0.6.30
-------------------------------
Po utworzeniu konta i wyborze nazwy postaci, rasy oraz klasy
pojawia się nowy etap: ODMIANA IMIENIA POSTACI.

Mianownik jest automatycznie równy wybranej nazwie postaci.
Następnie gracz podaje:
- Dopełniacz — kogo? czego?
- Celownik — komu? czemu?
- Biernik — kogo? co?
- Narzędnik — z kim? z czym?
- Miejscownik — o kim? o czym?
- Wołacz — o!

Łącznie zapisywanych jest siedem przypadków:
Mianownik, Dopełniacz, Celownik, Biernik, Narzędnik, Miejscownik, Wołacz.

Komendy:
odmiana
przypadki
namecases

pokazują wszystkie zapisane formy.

Odmiana jest trwale zapisana w SQLite.
Stare postacie są zachowane: jeśli nie mają jeszcze form,
migracja wpisuje ich dotychczasowe imię we wszystkie przypadki.

Powitanie po wejściu do świata używa Wołacza.

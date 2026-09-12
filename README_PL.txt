SOULBOUND v0.6.81 THREE CURRENCIES
==========================

Duży build rozbudowujący działający serwer online do pierwszej właściwej wersji świata MUD.

NAJWAŻNIEJSZE ZASADY
--------------------
- Postać NIE ma levelu.
- Nie rozdaje się ręcznie punktów statystyk.
- Statystyki rosną automatycznie podczas gry.
- Wszystkie klasy rozwijają wszystkie pięć statystyk automatycznie.
- Broń Duszy ma osobny Soul Level 1-200.
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


DRIADA — RASA POD LECZENIE v0.6.31
---------------------------------
Dodano 13. rasę: Driada.

Statystyki początkowe:
Siła: 7
Zręczność: 10
Kondycja: 11
Inteligencja: 15
Siła Woli: 15

Bonus rasowy:
+15 procent mocy wszystkich klasowych umiejętności typu heal.

Bonus działa obecnie między innymi na:
- Małe Leczenie Kapłana,
- Wielkie Leczenie Kapłana,
- Medytację Mnicha,
- Uzdrowienie Natury Druida.

Bonus działa również na przyszłe umiejętności oznaczone jako heal.
Skaluje się razem ze Skill Level danego skilla.

Driada jest szczególnie dobrym wyborem dla:
- Kapłana,
- Druida.

Komendy:
opis Driada
stats

stats pokazuje aktywny bonus rasowy do leczenia.


KRASNOLUD — RASOWA REDUKCJA OBRAŻEŃ v0.6.32
-------------------------------------------
Krasnolud ma teraz stały rasowy pasyw:

10 procent redukcji wszystkich otrzymywanych obrażeń.

Działa na:
- obrażenia fizyczne,
- obrażenia magiczne.

Kolejność obliczeń:
1. zwykła obrona fizyczna albo magiczna,
2. aktywna osłona umiejętności, jeśli działa,
3. rasowa redukcja Krasnoluda 10 procent,
4. pozostałe obrażenia odejmują HP.

Redukcja nie może zmniejszyć normalnego trafienia poniżej 1 obrażenia.

Komendy:
opis Krasnolud
stats

pokazują informację o pasywie.


PASYWY KLASOWE v0.6.33
----------------------
Wojownik — +10% obrażeń fizycznych.
Berserker — +12% obrażeń fizycznych.
Łotrzyk — +5 punktów procentowych uniku.
Łowca — +8% obrażeń fizycznych.
Mnich — +8% mocy leczenia klasowego.
Strażnik — 10% redukcji wszystkich otrzymywanych obrażeń.
Mag — +10% obrażeń magicznych.
Nekromanta — +15% leczenia z wysysania życia.
Kapłan — +10% mocy leczenia klasowego.
Czarownik — +12% obrażeń magicznych.
Druid — +10% mocy leczenia klasowego.
Psionik — +10% obrony magicznej.

Pasywy są stałe i nie trzeba ich uczyć.
Driada-Kapłan i Driada-Druid łączą bonus rasowy z klasowym leczeniem.
Krasnolud-Strażnik łączy rasową i klasową redukcję obrażeń.
Postać nadal nie ma levelu.


PASYWY WSZYSTKICH RAS v0.6.34
-----------------------------
Każda z 13 ras ma własny stały bonus.

Człowiek
+10% zdobywanego Postępu Rozwoju statystyk.

Ogr
+12% obrażeń fizycznych.

Elf
+5 punktów procentowych do szansy uniku.

Krasnolud
10% redukcji wszystkich otrzymywanych obrażeń.

Ork
+10% maksymalnego HP.

Niziołek
+3 punkty procentowe do szansy na bonusowy połów lub dodatkową zwykłą rudę.
Bonus łączy się z bonusem Tieru Wędki lub Kilofa.

Mroczny Elf
+10% obrażeń magicznych.

Gnom
+15% maksymalnej Many dla klas magicznych.

Smoczy
+8% wszystkich zadawanych obrażeń, fizycznych i magicznych.

Troll
12% redukcji otrzymywanych obrażeń fizycznych.

Diablę
+10% zdobywanego Soul XP Broni Duszy.

Aasimar
+12% obrony magicznej.

Driada
+15% mocy klasowych umiejętności leczących.

Pasywy rasowe i klasowe mogą się łączyć.
Przykłady:
- Ogr Wojownik łączy rasowy i klasowy bonus obrażeń fizycznych.
- Elf Łotrzyk łączy rasowy i klasowy bonus uniku.
- Krasnolud Strażnik łączy dwie redukcje obrażeń.
- Driada Kapłan łączy dwa bonusy leczenia.
- Aasimar Psionik łączy dwa bonusy obrony magicznej.

Komendy:
stats
opis <rasa>

pokazują pasyw rasy.


DRWALSTWO v0.6.35
-----------------
Dodano trzecią profesję: Drwalstwo.

Profesja:
- level 1-100,
- własny XP,
- 8 rang: Uczeń, Adept, Czeladnik, Specjalista, Ekspert, Mistrz, Arcymistrz, Legenda.

Narzędzie: Piła
- własny level 1-100,
- własny XP,
- 8 Tierów,
- bonus do szansy na dodatkowe drewno.

Komendy:
tnij
drwal
woodcut
tnij on
tnij off
woodcut on
woodcut off
drewno
stos
woodpile

Obszary:
Łąka, Gaj Szeptów, Głębia Gaju, Stary Trakt.

Drewno:
Suche gałęzie, Pień sosny, Pień dębu, Pień jesionu, Pień cisu,
Pień żelaznego drzewa, Pień drzewa duchów, Pradawna twardziel.

Każde drewno trafia automatycznie na Stos drewna.
Piłę kupuje się w Kuźni Dusz za 2 złota.
Drewno można sprzedawać na Rynku albo w Kuźni Dusz.


DRWAL BRAN I PIŁA v0.6.36
-------------------------
Piła nie jest już sprzedawana w Kuźni Dusz.
Piłę sprzedaje wyłącznie Drwal Bran w Obozie Drwala.

Trasa:
Gaj Szeptów -> zachód -> Obóz Drwala.

W obozie:
list
kup Piła

DREWNO
------
Drwalstwo ma 16 gatunków drewna:
Suche gałęzie, brzoza, sosna, wierzba, dąb, buk, klon, jesion,
cedr, cis, żelazne drzewo, heban, srebrne drzewo, drzewo duchów,
Pradawna twardziel i Drewno Drzewa Świata.

Obóz Drwala i Łąka dają głównie drewna początkujące.
Gaj Szeptów i Stary Trakt dają średnie i rzadkie drewna.
Głębia Gaju daje najrzadsze drewna magiczne i mityczne.

WĘDKARSTWO: 4 ŚRODOWISKA
------------------------
Rzeka:
Brzeg Rzeki i Kamienny Most.
Ryby m.in. karp, okoń rzeczny, brzana, szczupak, sandacz, pstrągi, łosoś, sum, jesiotr.

Jezioro:
Brzeg Srebrnego Jeziora.
Ryby m.in. płoć, leszcz, lin, okoń jeziorowy, szczupak, sandacz, troć jeziorowa, olbrzymi szczupak i węgorz.

Morze:
Morskie Molo.
Ryby m.in. sardynka, sardela, śledź, makrela, dorsz, okoń morski, plamiak, mintaj, flądra, halibut i turbot.

Ocean:
Oceaniczna Platforma.
Ryby m.in. tuńczyk, mahi-mahi, wahoo, żaglica, miecznik, tuńczyk błękitnopłetwy, samogłów oraz rekiny.

Każdy typ wody ma własną pulę połowu.
Ryby nadal trafiają automatycznie do Siatki na ryby.
Drewno nadal trafia automatycznie na Stos drewna.


WIĘCEJ RYB I DREWNA v0.6.37
---------------------------
Dodano 26 nowych gatunków ryb.

RZEKA:
Jelec, Kleń, Świnka, Jaź, Boleń, Lipień, Miętus
oraz wcześniejsze gatunki rzeczne.

JEZIORO:
Wzdręga, Karaś, Sielawa, Sieja, Palia jeziorowa
oraz wcześniejsze gatunki jeziorowe.

MORZE:
Szprot, Witlinek, Morszczuk, Barwena, Sola, Żabnica
oraz wcześniejsze gatunki morskie.

OCEAN:
Albakora, Tuńczyk wielkooki, Barakuda, Kobia, Seriola,
Rekin mako, Rekin tygrysi
oraz wcześniejsze gatunki oceaniczne.

DRWALSTWO:
Liczba gatunków drewna wzrosła z 16 do 24.

Nowe drewna:
Pień olchy,
Pień topoli,
Pień lipy,
Pień kasztana,
Pień orzecha,
Pień mahoniu,
Pień teku,
Pień sekwoi.

Nowe gatunki są przypisane do odpowiednich obszarów i leveli Piły.
Ryby nadal trafiają do Siatki, a drewno na Stos drewna.


RZEMIOSŁO v0.6.38
-----------------
Rzemiosło automatycznie pobiera rudy z Sakwy i drewno ze Stosu.

Komendy:
receptury
receptury craft
craft <nazwa>
stworz <nazwa>
wytworz <nazwa>

Kuźnia:
2 Rudy żelaza -> Żelazna sztabka.
2 Rudy srebra -> Srebrna sztabka.
2 Rudy złota -> Złota sztabka.

Obóz Drwala:
2 Pnie dębu -> Deska dębowa.
2 Pnie jesionu -> Deska jesionowa.
2 Pnie cisu -> Deska cisowa.
2 Pnie żelaznego drzewa -> Deska żelaznego drzewa.
2 Pnie drzewa duchów -> Deska drzewa duchów.

Talizmany:
Talizman Dębu i Żelaza: obrona +2.
Talizman Cisu i Srebra: obrona +3.
Talizman Drzewa Dusz: obrona +5.

GOTOWANIE v0.6.38
-----------------
Gotować można w Karczmie oraz na Targu Rybnym.
Ryby są pobierane bezpośrednio z Siatki.

Komendy:
receptury cook
cook <potrawa>
gotuj <potrawa>

Potrawy:
Pieczona ryba rzeczna: do 30 HP.
Gulasz rzeczny: do 45 HP.
Potrawka jeziorowa: do 50 HP i 10 Many.
Zupa morska: do 60 HP i 15 Many.
Stek oceaniczny: do 75 HP i 25 Many.
Uczta Mistrza Rybaka: do 100 HP i 40 Many.

Potraw używa się przez use/uzyj.
W walce użycie jedzenia zużywa jedną turę.


ATLASY v0.6.39
--------------
atlas
atlas ryby
atlas rzeka
atlas jezioro
atlas morze
atlas ocean
atlas drewno
atlas rudy
atlas <nazwa surowca>

Atlas pokazuje występowanie ryb, drewna i rud.

DRUŻYNY v0.6.39
---------------
druzyna
druzyna zapros <gracz>
druzyna dolacz
druzyna odrzuc
druzyna opusc
druzyna wyrzuc <gracz>
druzyna rozwiaz
druzyna limit
pc <tekst>

Startowy limit: 8 osób łącznie z liderem.
Co 25 Charyzmy lidera: +1 miejsce.

Członkowie w tym samym pomieszczeniu mogą wspólnie walczyć
z tym samym przeciwnikiem.

Po zwycięstwie obecni członkowie otrzymują pełny EXP rozwoju,
pełny Soul XP oraz postęp zadań zabijania.
Waluta jest dzielona.
Każdy wylosowany drop trafia do jednego losowego członka.

CHARYZMA HANDLOWA v0.6.39
-------------------------
Charyzma jest osobnym rozwojem handlowym.
Nie jest szóstą statystyką bojową i nie daje levelu postaci.

Każda udana sprzedaż surowca: Charyzma +1.
Co 4 Charyzmy: +1% rabatu.
Maksymalny rabat: 25%.

W sklepie płacisz bazową walutą, a wartość rabatu jest zwracana
w srebrze. Dzięki temu rabat działa także na przedmioty kosztujące złoto.

Charyzma wpływa też na wielkość drużyny:
start 8 osób, potem +1 miejsce co 25 Charyzmy lidera.

Komendy:
charyzma
charisma
stats


NARZĘDZIA RZEMIOSŁA I GOTOWANIA v0.6.40
---------------------------------------
Wędkarstwo: Wędka 1-100, 8 Tierów.
Górnictwo: Kilof 1-100, 8 Tierów.
Drwalstwo: Piła 1-100, 8 Tierów.

Rzemiosło:
Młot Rzemieślniczy 1-100, własny XP, użycia i 8 Tierów.
Kupuje się u Kowala Dorana w Kuźni Dusz za 2 złota.
Bez Młota craft / stworz / wytworz nie działa.
Udana receptura daje 8-12 XP Młota.
Wyższy Tier może dać dodatkowy produkt bez dodatkowych składników.

Gotowanie:
Nóż Kucharski 1-100, własny XP, użycia i 8 Tierów.
Kupuje się w Karczmie Pod Błękitnym Płomieniem za 1 złoto.
Bez Noża cook / gotuj nie działa.
Udana receptura daje 8-12 XP Noża.
Wyższy Tier może dać dodatkową potrawę bez dodatkowych składników.

Progi Tierów:
1, 15, 30, 45, 60, 75, 90, 100.

Bonus Tierów:
0%, 2%, 4%, 6%, 8%, 10%, 12%, 15%.

Komendy:
tools
narzedzia
tiers
tiery
nazwytierow
help rzemioslo
help gotowanie
help receptury


ZIELARSTWO v0.6.41
------------------
Profesja 1-100, 8 rang.
Narzędzie: Sierp Zielarski 1-100, 8 Tierów.
Kupisz go w Chacie Zielarki.

Komendy:
zbieraj
zbieraj on
zbieraj off
zielarstwo
ziola
herbs
atlas ziola

Auto-Zielarstwo działa jak auto-łowienie i wykonuje kolejne zbiory co około 2 sekundy.
Zioła automatycznie trafiają do Torby Zielarskiej.

ALCHEMIA v0.6.41
----------------
Profesja 1-100, 8 rang.
Narzędzie: Moździerz Alchemiczny 1-100, 8 Tierów.
Kupisz go w Chacie Zielarki.

Komendy:
receptury alchemia
alchemia <mikstura>
warz <mikstura>

Receptury:
Mikstura leczenia
Mikstura Many
Wielka Mikstura Leczenia
Wielka Mikstura Many
Eliksir Witalności
Eliksir Duszy

Udana receptura rozwija Alchemię i Moździerz.


BEZPOŚREDNIE INFORMACJE O NARZĘDZIACH v0.6.42
---------------------------------------------
Możesz teraz wpisać bezpośrednio nazwę narzędzia:

wedka
kilof
pila
mlot
noz
sierp
mozdzierz

Obsługiwane są również polskie znaki:
wędka
piła
młot
nóż
moździerz

Każda z tych komend pokazuje:
- obecny level 1-100,
- liczbę użyć,
- obecne XP,
- wymagane XP do następnego levelu,
- dokładnie ile XP brakuje do następnego levelu,
- obecny Tier 1-8,
- nazwę obecnego Tieru,
- bonus obecnego Tieru,
- nazwę następnego Tieru,
- level wymagany do następnego Tieru,
- ile leveli brakuje do następnego Tieru,
- łączne XP potrzebne do następnego Tieru,
- pełną listę wszystkich 8 Tierów tego narzędzia.

Komenda:
tools
narzedzia

nadal pokazuje skrót wszystkich narzędzi.

Komenda:
tiers
tiery
nazwytierow

nadal pokazuje wszystkie Tiery wszystkich narzędzi.


OCHRONA POMOCNYCH NPC v0.6.43
-----------------------------
Wszystkie postacie znajdujące się w systemie NPCS są pokojowe i chronione.

Nie można ich atakować ani zabijać przez:
attack
atakuj
zabij
kill

Nie można ich również obrać jako celu ofensywnej umiejętności klasowej.

Ochrona NIE ogranicza się do miasta.

Chronieni są między innymi:
- Kowal Doran,
- Drwal Bran,
- Zielarka Liora,
- Zielarka Mira,
- Rybak Tomas,
- Kapłan Elor,
- Kapitan Arven,
- Karczmarka Elia,
- Archiwista Sol,
- wszyscy nauczyciele klas.

Zasada:
sprzedawca, nauczyciel, questgiver lub inny pomocny NPC = brak możliwości walki.

Moby i potwory przeznaczone do walki nadal można normalnie atakować.


QUESTY PROFESYJNE v0.6.44
-------------------------
Dodano komplet prób dla czterech profesji zbierackich.

PRÓBA RYBAKA
NPC: Rybak Tomas.
Cel: przynieś 30 dowolnych ryb.
Surowce pobierane są z Siatki na ryby i zwykłego ekwipunku.
Nagroda: 1000 XP Wędkarstwa, 1000 XP Wędki, 50 srebra.

PRÓBA GÓRNIKA
NPC: Górnik Toren.
Lokacja: Wejście do Kryształowej Jaskini.
Cel: przynieś 30 dowolnych rud.
Surowce pobierane są z Sakwy górniczej i zwykłego ekwipunku.
Nagroda: 1000 XP Górnictwa, 1000 XP Kilofa, 50 srebra.

PRÓBA DRWALA
NPC: Drwal Bran.
Cel: przynieś 30 sztuk dowolnego drewna.
Surowce pobierane są ze Stosu drewna i zwykłego ekwipunku.
Nagroda: 1000 XP Drwalstwa, 1000 XP Piły, 50 srebra.

PRÓBA ZIELARKI
NPC: Zielarka Liora.
Cel: przynieś 30 dowolnych ziół.
Surowce pobierane są z Torby Zielarskiej i zwykłego ekwipunku.
Nagroda: 1000 XP Zielarstwa, 1000 XP Sierpa Zielarskiego, 50 srebra.

Aby rozpocząć lub oddać zadanie:
talk <NPC>
rozmawiaj <NPC>

Postęp:
quests
zadania


NOWE KURSY WALUT v0.6.45
------------------------
1000 srebra = 1 złoto.

1000000 złota = 1 mithril.

Czyli:
1 złoto = 1000 srebra.
1 mithril = 1000000000 srebra.

Komendy:
exchange
exchange gold
exchange mithril

exchange gold:
wymienia 1000 srebra na 1 złoto.

exchange mithril:
wymienia 1000000 złota na 1 mithril.

Rabat Charyzmy korzysta z tych samych nowych przeliczników.
Przykład:
przedmiot za 1 złoto ma wartość bazową 1000 srebra przy obliczaniu rabatu.

Ważne:
aktualizacja nie przelicza automatycznie istniejących portfeli graczy.
Liczba posiadanych srebrnych, złotych i mithrilowych monet pozostaje taka sama.
Rzadkość czystego mithrilu z Górnictwa nie została zmieniona.


REBALANS CEN SKLEPOWYCH v0.6.46
-------------------------------
Po kursie 1000 srebra = 1 złoto podstawowe przedmioty sklepowe
zostały przeliczone na srebro.

NARZĘDZIA
Wędka: 10 srebra.
Kilof: 10 srebra.
Piła: 10 srebra.
Młot Rzemieślniczy: 10 srebra.
Nóż Kucharski: 10 srebra.
Sierp Zielarski: 10 srebra.
Moździerz Alchemiczny: 10 srebra.

MIKSTURY
Mikstura leczenia: 24 srebra.

PODSTAWOWY EKWIPUNEK
Skórzana kamizelka: 48 srebra.
Talizman Wędrowca: 72 srebra.

ŻELAZNY EKWIPUNEK
Żelazne rękawice: 70 srebra.
Żelazne buty: 70 srebra.
Żelazny hełm: 90 srebra.
Talizman Kowala: 110 srebra.
Żelazne nogawice: 130 srebra.
Żelazny napierśnik: 180 srebra.

Rabat Charyzmy nadal obniża efektywny koszt tych cen.
Craftowane przedmioty, surowce, dropy i już posiadany ekwipunek
nie są zmieniane przez ten rebalans.


QUESTY - REBALANS NAGRÓD v0.6.47
--------------------------------
Próby Rybaka, Górnika, Drwala i Zielarki: po 50 srebra.
Szczury pod świątynią: 75 srebra.
Problem goblinów: 100 srebra.
Cienie w gaju: 120 srebra.
Odłamki dla kowala: 300 srebra.
Nagrody pieniężne tych zadań nie używają już złota ani mithrilu.

CIAŁA I EKWIPUNEK MOBÓW v0.6.47
-------------------------------
Po śmierci większości mobów zostaje ciało przez około 10 minut.
Komendy: ciało, zwloki, corpse, przeszukaj ciało, loot.
Ekwipunek zabrany z ciała trafia do zwykłego inventory.
Dotychczasowe losowe dropy działają niezależnie.

KRYPTA 1-100 v0.6.47
--------------------
Krypta ma 100 prawdziwych pięter.
Bossowie: 10 Kościany Egzekutor; 20 Krwawy Kurator; 30 Rycerz Grobowca;
40 Wiedźma Popiołu; 50 Pan Katakumb; 60 Widmowy Tytan;
70 Nekromantyczny Kolos; 80 Arcyupiór Otchłani; 90 Król Kości;
100 Władca Stu Pięter.
Na piętrach 10-90 boss blokuje zejście down, dopóki żyje.
Prowadzenie automatyczne nie omija bossów.
Co 10 pięter zmienia się Tier ekwipunku z ciał: Tier 1 na 1-10, ... Tier 10 na 91-100.
Zwykły mob Krypty zostawia 1 element, boss 2 elementy.
Komendy: krypta, crypt, prowadz krypta 25.
Mapa pokazuje Kryptę skrótowo dla NVDA.


SKALOWANIE KRYPTY v0.6.48
-------------------------
Im niższe piętro, tym trudniejsi przeciwnicy i lepsze nagrody.

ZWYKŁE MOBY
HP = 70 + piętro * 9.
Obrażenia = 6 + piętro / 3.
EXP rozwoju = 20 + piętro * 2.
Soul XP = 2 + piętro / 4.
Srebro = 8 + numer piętra.

Przykłady:
Piętro 1: 79 HP, 6 obrażeń bazowych, 22 EXP rozwoju, 2 Soul XP, 9 srebra.
Piętro 50: 520 HP, 22 obrażenia bazowe, 120 EXP rozwoju, 14 Soul XP, 58 srebra.
Piętro 100: 970 HP, 39 obrażeń bazowych, 220 EXP rozwoju, 27 Soul XP, 108 srebra.

BOSSOWIE
HP = 350 + piętro * 25.
Obrażenia = 16 + piętro / 2.
EXP rozwoju = 180 + piętro * 4.
Soul XP = 35 + numer piętra.
Srebro = 150 + piętro * 8.

Boss piętra 10: 600 HP, 21 obrażeń, 220 EXP rozwoju, 45 Soul XP, 230 srebra.
Boss piętra 50: 1600 HP, 41 obrażeń, 380 EXP rozwoju, 85 Soul XP, 550 srebra.
Boss piętra 100: 2850 HP, 66 obrażeń, 580 EXP rozwoju, 135 Soul XP, 950 srebra.

Nie ma levelu postaci.
EXP rozwoju automatycznie zwiększa pięć statystyk.
Soul XP rozwija Broń Duszy.


MULTICLASS v0.6.49
------------------
Multiclass jest opcjonalny.

Każda postać:
- zawsze ma jedną klasę główną,
- może dodać maksymalnie 2 klasy dodatkowe,
- może mieć maksymalnie 3 aktywne klasy.

Przykład:
Strażnik + Mag + Druid.

Komendy:
multiclass
klasy
multiclass add Mag
multiclass add Druid
multiclass remove Mag

Klasy głównej nie można wyłączyć.
Broń Duszy zawsze pozostaje Bronią Duszy klasy głównej.

Aktywne dodatkowe klasy:
- włączają swoje pasywy,
- udostępniają swoich nauczycieli,
- pozwalają uczyć się i używać ich skilli,
- klasa magiczna daje pulę Many także fizycznej klasie głównej.

BIEGŁOŚĆ KLAS
Każda klasa ma własną Biegłość 1-100.
Nie jest to level postaci.

Class XP do następnej Biegłości:
1000 + (Biegłość - 1) * 250.

Mob daje jedną pulę Class XP.
Pula jest dzielona równo pomiędzy wszystkie aktywne klasy.

Przykład:
mob daje 1050 Class XP.
1 aktywna klasa: 1050 XP dla niej.
2 aktywne klasy: po 525 XP.
3 aktywne klasy: po 350 XP.

Wyłączenie klasy zachowuje jej Biegłość, XP i nauczone skille.

KRYPTA - CLASS XP I SOUL XP v0.6.49
-----------------------------------
Zwykły mob Krypty:
Class XP = 450 + piętro * 60.

Piętro 10:
1050 Class XP.

Piętro 50:
3450 Class XP.

Piętro 100:
6450 Class XP.

Boss:
Class XP = 1800 + piętro * 100.

Boss piętra 10:
2800 Class XP.

Boss piętra 50:
6800 Class XP.

Boss piętra 100:
11800 Class XP.

Soul XP rozwija się wolniej:
zwykły mob = 1 + piętro / 10.
Boss = 10 + piętro / 5.

EXP rozwoju statystyk pozostaje osobnym systemem i nadal automatycznie
zwiększa pięć statystyk. Nie istnieje level postaci.

CENY NARZĘDZI v0.6.49
----------------------
Wszystkie podstawowe narzędzia kosztują po 10 srebra:
Wędka,
Kilof,
Piła,
Młot Rzemieślniczy,
Nóż Kucharski,
Sierp Zielarski,
Moździerz Alchemiczny.


STARTOWA EKONOMIA v0.6.50
-------------------------
Nowa postać zaczyna z:
30 srebra,
2 złota,
0 mithrilu,
2 Miksturami leczenia.

Aktualizacja nie zmienia portfeli istniejących postaci.


PEŁNA HISTORIA ZMIAN v0.6.51
----------------------------
Komendy:
changes
zmiany
changelog

Pokazują cały CHANGELOG_PL.txt, a nie tylko ostatnią wersję.
Najnowsza wersja jest na górze, wszystkie starsze niżej.
Każda linia jest wysyłana osobno dla NVDA.

Jeśli plik CHANGELOG_PL.txt jest niedostępny, gra pokazuje awaryjnie
zmiany bieżącej wersji.


BONUS KLASOWY BRONI DUSZY v0.6.52
---------------------------------
Broń Duszy klasy głównej daje teraz dodatkowy bonus klasowy.

Standardowa skala:
Tier 1: 5 procent.
Tier 2: 10 procent.
Tier 3: 15 procent.

Wojownik:
obrażenia fizyczne +5 / +10 / +15 procent.

Berserker:
obrażenia fizyczne +5 / +10 / +15 procent.

Łowca:
obrażenia fizyczne +5 / +10 / +15 procent.

Mag:
obrażenia magiczne +5 / +10 / +15 procent.

Czarownik:
obrażenia magiczne +5 / +10 / +15 procent.

Mnich:
moc leczenia +5 / +10 / +15 procent.

Kapłan:
moc leczenia +5 / +10 / +15 procent.

Druid:
moc leczenia +5 / +10 / +15 procent.

Nekromanta:
leczenie z wysysania życia +5 / +10 / +15 procent.

Psionik:
obrona magiczna +5 / +10 / +15 procent.

Łotrzyk:
unik +2 / +4 / +6 punktów procentowych.
Globalny limit uniku nadal wynosi 45 procent.

Strażnik:
redukcja wszystkich otrzymywanych obrażeń +3 / +6 / +9 procent.

Multiclass:
Broń Duszy i jej bonus należą zawsze do klasy głównej.
Dodatkowe klasy zachowują swoje pasywy, skille i Biegłość,
ale nie otrzymują osobnej Broni Duszy.

WIĘKSZE NAGRODY BOSSÓW KRYPTY v0.6.52
-------------------------------------
Bossowie zostali wyraźnie odróżnieni od zwykłych mobów.

Class XP bossa:
3000 + piętro * 160.

Boss piętra 10:
4600 Class XP.

Boss piętra 50:
11000 Class XP.

Boss piętra 100:
19000 Class XP.

EXP rozwoju bossa:
350 + piętro * 6.
Piętro 10: 410.
Piętro 50: 650.
Piętro 100: 950.

Soul XP bossa:
20 + piętro / 4.
Piętro 10: 22.
Piętro 50: 32.
Piętro 100: 45.

Srebro bossa:
300 + piętro * 12.
Piętro 10: 420 srebra.
Piętro 50: 900 srebra.
Piętro 100: 1500 srebra.

Loot bossa:
- 3 elementy ekwipunku z aktualnego Tieru na ciele,
- Odłamek Duszy zawsze,
- większa szansa na Eliksir Duszy.


PRÓBY BRONI DUSZY v0.6.53
-------------------------
Tier 2:
1. Osiągnij Soul Level 25.
2. Idź do Kapłana Elora w Świątyni Odrodzenia.
3. Przyjmij zadanie Próba Broni Duszy: Tier 2.
4. Pokonaj 5 Szkieletów Strażników.
5. Wróć do Kapłana Elora.
6. Po ukończeniu próby wpisz unlock.
7. Broń Duszy przechodzi na Tier 2.

Tier 3:
1. Miej Tier 2.
2. Osiągnij Soul Level 60.
3. Idź do Kapłana Elora w Świątyni Odrodzenia.
4. Przyjmij zadanie Próba Broni Duszy: Tier 3.
5. Pokonaj 3 Upiory Krypty.
6. Wróć do Kapłana Elora.
7. Po ukończeniu próby wpisz unlock.
8. Broń Duszy przechodzi na Tier 3.

Stare postacie:
jeśli postać już posiada Tier 2 lub Tier 3, aktualizacja nie obniża Tiera
i nie wymusza ponownego wykonywania starego odblokowania.

POWTARZALNE QUESTY PROFESYJNE v0.6.53
-------------------------------------
Co 30 minut można ponownie wykonać:
Próbę Rybaka,
Próbę Górnika,
Próbę Drwala,
Próbę Zielarki.

30 minut liczy się od ukończenia zadania.
Cooldown jest zapisany w SQLite.
Reconnect, restart serwera i redeploy nie zerują czasu oczekiwania.

Po rozmowie z właściwym NPC:
- jeśli cooldown jeszcze trwa, gra podaje dokładny pozostały czas,
- jeśli minęło 30 minut, quest można ponownie przyjąć,
- dziennik quests / zadania również pokazuje stan odnowienia.


POSTĘP AKTYWNYCH QUESTÓW v0.6.54
--------------------------------
Każdy aktywny quest mówi dokładnie ile wykonano i ile potrzeba.

Przykłady:
Próba Broni Duszy Tier 2:
Quest aktywny: Próba Broni Duszy: Tier 2. Postęp 3 z 5.

Próba Górnika:
Quest aktywny: Próba Górnika. Postęp 17 z 30.

Po osiągnięciu celu:
Quest aktywny: Próba Górnika. Postęp 30 z 30. Cel wykonany, wróć do NPC.

Postęp jest odczytywany:
- zaraz po przyjęciu questa,
- po każdym zabiciu celu questa,
- po złowieniu ryby,
- po wydobyciu zwykłej rudy,
- po pozyskaniu drewna,
- po zebraniu zioła,
- przy rozmowie z NPC,
- w dzienniku quests / zadania.

Bonusowy surowiec z Tieru narzędzia jest uwzględniany w stanie.
Czysty mithril trafiający bezpośrednio do portfela nie liczy się jako
zwykła ruda w Próbie Górnika.


WARTOWNIE I OBOZOWISKO BANDYTÓW v0.6.55
---------------------------------------
Nowe lokacje:
Wartownia Północna.
Wartownia Pogranicza.
Obozowisko Bandytów.

Trasa:
Stary Trakt
-> east
Wartownia Północna
-> east
Wartownia Pogranicza
-> east
Obozowisko Bandytów.

Powrót prowadzi kierunkiem west.

NPC:
Dowódca Roderik - Wartownia Północna.
Strażniczka Anna - Wartownia Pogranicza.

PATROL PRZECIW BANDYTOM
-----------------------
Giver:
Dowódca Roderik.

Cel:
pokonaj 10 bandytów w Obozowisku Bandytów.

Do celu liczą się:
Bandyta,
Bandycki Maruder.

Nagroda:
250 srebra,
150 EXP rozwoju statystyk,
2 Mikstury leczenia.

Quest jest powtarzalny co 60 minut.
Cooldown zaczyna się po ukończeniu i jest zapisany w SQLite.

Live progress:
po każdym zabiciu gra mówi np.
Quest aktywny: Patrol przeciw bandytom. Postęp 4 z 10.

Po 10 z 10:
Cel wykonany, wróć do NPC.

W obozowisku spawnuje się:
4 Bandytów,
2 Bandyckich Maruderów.

Komendy prowadzenia:
prowadz Wartownia Północna
prowadz Wartownia Pogranicza
prowadz Obozowisko Bandytów


WIĘCEJ SOUL XP Z MOBÓW v0.6.56
------------------------------
Rozwój Broni Duszy jest teraz szybszy.

Podstawowe moby:
Szczur Świątynny: 2 Soul XP.
Żywy Manekin: 6 Soul XP.
Goblin: 10 Soul XP.
Gobliński Osiłek: 13 Soul XP.
Wilk Cienia: 12 Soul XP.
Bandyta: 12 Soul XP.
Bandycki Maruder: 15 Soul XP.
Szkielet Strażnik: 16 Soul XP.
Upiór Krypty: 22 Soul XP.
Kryształowy Strażnik: 26 Soul XP.

Krypta, zwykły mob:
Soul XP = 3 + piętro / 6.

Przykłady:
Piętro 10: 4 Soul XP.
Piętro 50: 11 Soul XP.
Piętro 100: 19 Soul XP.

Boss Krypty:
Soul XP = 35 + piętro / 3.

Przykłady:
Boss piętra 10: 38 Soul XP.
Boss piętra 50: 51 Soul XP.
Boss piętra 100: 68 Soul XP.

Bossowie są najlepszym źródłem Soul XP.
Class XP nadal jest znacznie większe liczbowo, więc Soul XP pozostaje
osobnym i wolniejszym systemem rozwoju Broni Duszy.


WYSOKIE SOUL XP v0.6.57
-----------------------
Rozwój Broni Duszy został mocno przyspieszony.

Podstawowe moby:
Szczur Świątynny: 80 Soul XP.
Żywy Manekin: 100.
Goblin: 140.
Gobliński Osiłek: 180.
Wilk Cienia: 160.
Bandyta: 170.
Bandycki Maruder: 220.
Szkielet Strażnik: 240.
Upiór Krypty: 280.
Kryształowy Strażnik: 320.

Krypta, zwykły mob:
Soul XP = 100 + piętro * 10.

Przykłady:
Piętro 10: 200 Soul XP.
Piętro 50: 600 Soul XP.
Piętro 100: 1100 Soul XP.

Boss Krypty:
Soul XP = 600 + piętro * 20.

Przykłady:
Boss piętra 10: 800 Soul XP.
Boss piętra 50: 1600 Soul XP.
Boss piętra 100: 2600 Soul XP.

Dzięki temu nawet przy rosnących wymaganiach Soul Level rozwija się dużo szybciej.


ODPOCZYNEK I REGENERACJA v0.6.58
--------------------------------
Komendy:
odpoczywaj
odpocznij
odpoczynek
rest
regen

Odpoczynek działa tylko poza walką.

Co 5 sekund:
- odzyskujesz 10 procent maksymalnego HP,
- jeśli masz Manę, odzyskujesz 10 procent maksymalnej Many.

NVDA przykładowo usłyszy:
Regeneracja: HP 145 z 200. Mana 90 z 150.

Dodatkowe:
odpoczywaj status
odpoczywaj stop

Ruch, walka i inne aktywne czynności przerywają odpoczynek.
Komendy informacyjne, np. stats, look, quests, soul i inventory,
nie przerywają regeneracji.

UŻYWANIE PRZEDMIOTÓW v0.6.58
----------------------------
Komendy:
użyj <przedmiot>
uzyj <przedmiot>
use <przedmiot>

Szybkie skróty:
użyj mikstura
= Mikstura leczenia.

użyj eliksir
= Eliksir Duszy.

użyj mana
= Mikstura Many.

Pełne nazwy również działają:
użyj Wielka Mikstura Leczenia
użyj Wielka Mikstura Many
użyj Eliksir Witalności
use soul elixir

Mikstury HP/Many i jedzenie odnawiają zasoby.
Eliksir Duszy daje Soul XP.
W walce użycie przedmiotu zużywa turę i przeciwnik odpowiada.


PROWADZENIE DO WSZYSTKICH LOKACJI v0.6.59
-----------------------------------------
Komendy:
prowadz <lokacja>
prowadź <lokacja>
guide <lokacja>
walk to <lokacja>

Każda lokacja z ROOMS jest automatycznie celem prowadzenia.

Aktualna liczba celów:
148 lokacji,
w tym wszystkie 100 pięter Krypty.

Lista:
prowadz lista
guide list

Przykłady:
prowadz Plac Dusz
prowadz targ rybny
prowadz Targ Rybny
prowadz fish market
prowadz wartownia polnocna
prowadz Obozowisko Bandytow
prowadz Gildia Dusz
prowadz krypta 1
prowadz krypta 37
prowadz pietro 50
guide crypt floor 100

Resolver:
- ignoruje wielkość liter,
- obsługuje polskie znaki i warianty bez polskich znaków,
- rozumie room_id zapisany ze spacjami zamiast podkreśleń,
- obsługuje nazwy wyświetlane w mapie,
- jeśli nazwa jest niejednoznaczna, podaje listę pasujących lokacji.

Mapa:
map pokazuje dynamicznie wszystkie strefy zwykłego świata.
Krypta pozostaje skrócona do pięter 1-100, żeby nie spamować NVDA.

Nowe lokacje dodane w przyszłości do ROOMS automatycznie będą działały
z prowadz bez dopisywania ich do osobnej tabeli aliasów.


CHECKPOINTY KRYPTY I NAPRAWA BOSS GATE v0.6.60
-----------------------------------------------
Bossowie pozostają na piętrach:
10, 20, 30, 40, 50, 60, 70, 80, 90 i 100.

NOWA ZASADA BLOKADY:
Boss blokuje zejście tylko dopóki twoja postać nie zaliczy tego bossa.

Po pokonaniu:
- zaliczenie zapisuje się w SQLite,
- odblokowuje się checkpoint tego piętra,
- boss tego piętra już nigdy nie blokuje twojego zejścia,
- nie ma znaczenia, że później boss odrodzi się dla innych graczy.

W drużynie:
wszyscy obecni członkowie drużyny, którzy dostają nagrody za bossa,
dostają także zaliczenie bossa i checkpoint.

CHECKPOINTY
-----------
checkpoint
pokazuje najwyższy i wszystkie odblokowane checkpointy.

checkpoint 10
checkpoint 20
...
checkpoint 100

Checkpointu można użyć:
- w Sali Krypty,
- w Przedsionku Krypty,
- na dowolnym piętrze Krypty.

Nie można używać checkpointu podczas walki.

Stare postacie:
jeśli stara postać stoi np. na piętrze 73, gra bezpiecznie uzna,
że wcześniej przeszła bossy do 70 i zapisze checkpoint 70.
Jeżeli stoi dokładnie na piętrze bossa, np. 50, nie dostaje automatycznie
zaliczenia bossa 50 — tylko poprzednich bossów do 40.

MOBY
----
Moby NIE są agresywne.
Nie atakują gracza same po wejściu do lokacji.
Walka zaczyna się dopiero po:
attack / atakuj / zabij / kill
albo po świadomym użyciu ofensywnego skilla.

LOOT KRYPTY
------------
Zwykły mob: 1 element ekwipunku na ciele.
Boss: 3 elementy ekwipunku na ciele.


BOSS ZAWSZE BLOKUJE, GDY ŻYJE v0.6.61
-------------------------------------
Poprawiona zasada Krypty:

1. Wchodzisz na piętro bossa.
2. Jeśli boss żyje, zejście down jest zablokowane.
3. Zabijasz bossa.
4. Zejście otwiera się.
5. Boss po 35 sekundach odradza się.
6. Po respawnie ponownie blokuje zejście.

Dotyczy to także postaci, która wcześniej pokonała tego bossa.

CHECKPOINT
----------
Checkpoint nadal zapisuje się trwale.
Pozwala wrócić np. na piętro 50 bez przechodzenia ponownie pięter 1-49.

Ale:
jeżeli boss piętra 50 po respawnie żyje,
checkpoint 50 przeniesie cię na piętro 50,
lecz zejście na 51 będzie zablokowane do ponownego pokonania bossa.

MOBY
----
Moby nadal NIE są agresywne.
Nie rozpoczynają walki same.


PORTALE KRYPTY v0.6.62
----------------------
Po pokonaniu bossów na piętrach:
10, 20, 30, 40, 50, 60, 70, 80, 90 i 100
odblokowuje się trwały Portal Krypty do danego piętra.

Komendy:
portal
portal 10
portal 20
portal 30
...
portal 100

Portal można uruchomić tylko w:
- Sali Krypty,
- Przedsionku Krypty.

Przykład:
pokonujesz bossa piętra 50.
Gra mówi:
Odblokowano Portal Krypty do piętra 50.

Wracasz później do Sali Krypty i wpisujesz:
portal 50

Portal przenosi bezpośrednio na piętro 50.

WAŻNE:
Portal nie wyłącza żywego bossa.
Jeżeli boss piętra 50 żyje, nadal blokuje zejście na 51.
Po zabiciu przejście jest otwarte do respawnu.
Po respawnie boss ponownie blokuje.

Moby nadal NIE są agresywne.

ZGODNOŚĆ:
stare komendy checkpoint nadal działają jako alias portalu.
Dane pozostają w istniejącej kolumnie crypt_checkpoint,
żeby stare zapisy nie wymagały konwersji.


LOOT KRYPTY: RARITY, AFFIXY I SETY v0.6.63
------------------------------------------
Nowe dropy wyposażenia z Krypty losują rzadkość:

1. Zwykły.
2. Rzadki.
3. Epicki.
4. Legendarny.
5. Mityczny.

Wyższa rzadkość daje:
- większą obronę,
- mocniejszy losowy bonus statystyki.

Możliwe losowe bonusy:
- Siła,
- Zręczność,
- Kondycja,
- Inteligencja,
- Siła Woli,
- HP,
- Mana.

Bossowie mają znacznie większą szansę na najlepsze rarity
niż zwykłe moby Krypty.

PRZYKŁADOWA NAZWA:
Napierśnik Krypty Tier 5 [Epicki, Siła +4]

Bonus Siły realnie zwiększa obrażenia fizyczne.
Zręczność zwiększa szybkość i unik.
Kondycja zwiększa maksymalne HP.
Inteligencja zwiększa moc magiczną i Manę.
Siła Woli zwiększa obronę magiczną.
HP i Mana dają bezpośrednie dodatkowe zasoby.

SETY KRYPTY
-----------
Każdy Tier 1-10 ma własny Zestaw Krypty.

Sloty:
głowa,
korpus,
dłonie,
nogi,
stopy,
talizman.

Bonusy:
2 części: +10 procent maksymalnego HP i Many.
4 części: dodatkowo +10 procent wszystkich obrażeń.
6 części: dodatkowo +15 procent obrony fizycznej i magicznej.

Set liczony jest według Tieru.
Jeśli masz części różnych Tierów, aktywny jest Tier z największą liczbą
założonych części; przy remisie wybierany jest wyższy Tier.

KOMENDY:
equipment
pokazuje rarity, affix i bonus setu.

stats
pokazuje bazowe statystyki oraz wartości po bonusach sprzętu.

help loot_krypty
pokazuje zasady w grze.

ZGODNOŚĆ
--------
Stare przedmioty Krypty nadal działają.
Są traktowane jako Zwykłe, bez affixu, ale liczą się do setu Tieru.
Nie wymaga to nowej tabeli SQLite ani resetu postaci.


UNIKALNE MECHANIKI BOSSÓW v0.6.64
---------------------------------
Walka pozostaje turowa:
akcja gracza -> dokładnie jedna odpowiedź przeciwnika.

Bossowie i zwykłe moby nadal NIE są agresywne.

KRYPTA
------
10 Kościany Egzekutor:
co trzeci kontratak Kościane Miażdżenie, +60% mocy.

20 Krwawy Kurator:
co trzeci kontratak Krwawy Drenaż, +25% mocy,
leczy się o 50% rzeczywiście zadanych obrażeń.

30 Rycerz Grobowca:
co trzecie trafienie gracza jest redukowane o połowę Tarczą Grobowca.

40 Wiedźma Popiołu:
co trzeci kontratak Klątwa Popiołu,
+25% mocy i tylko połowa obrony magicznej gracza.

50 Pan Katakumb:
co czwarty kontratak Echo Katakumb, +70% mocy.

60 Widmowy Tytan:
zmienia typ kontrataku magiczny/fizyczny co turę.

70 Nekromantyczny Kolos:
co czwarty kontratak odzyskuje 7% maksymalnego HP.

80 Arcyupiór Otchłani:
25% szansy na całkowity Eteryczny Unik trafienia gracza.

90 Król Kości:
poniżej połowy HP +50% obrażeń.

100 Władca Stu Pięter:
druga faza poniżej połowy HP,
co trzeci kontratak Załamanie Duszy,
co czwarte trafienie gracza Pieczęć Stu Pięter.

Każdy boss ma własny unikalny relikt.
Bossowie 10-90: 45% szansy.
Boss 100: 100% szansy.

HERSZT BANDYTÓW
---------------
Nowy boss w Obozowisku Bandytów:
Herszt Bandytów.

320 HP.
24 bazowe obrażenia fizyczne.
420 srebra.
180 Postępu Rozwoju.
2200 Class XP.
650 Soul XP.

Co trzeci kontratak:
Brutalna Kombinacja, +40% obrażeń.

Herszt liczy się jako bandyta do Patrolu przeciw bandytom.
Może upuścić Sygnet Herszta Bandytów:
Obrona +3, Zręczność +3, 45% szansy.


KRYTYCZNE TRAFIENIA v0.6.65
---------------------------
Krytyki zależą od efektywnej Zręczności.

Zręczność 10 = 5%.
Każdy punkt ponad 10 = +0,5 punktu procentowego.
Każdy punkt poniżej 10 = -0,5 punktu procentowego.

Minimum: 1%.
Maksimum: 35%.
Krytyk zadaje 150% normalnych obrażeń.

Krytyki działają dla:
- zwykłych ataków,
- ofensywnych skilli klasowych.

Bonus Zręczności z ekwipunku również zwiększa szansę.

Przykłady:
Dex 10 = 5%.
Dex 20 = 10%.
Dex 30 = 15%.
Dex 50 = 25%.
Dex 70+ = 35%.

stats pokazuje aktualny krytyk.

WOLNIEJSZY RESPAWN v0.6.65
--------------------------
Poprzednio globalny respawn wynosił 35 sekund.

Teraz:
- zwykłe moby: 120 sekund,
- bossowie Krypty: 300 sekund,
- Herszt Bandytów: 300 sekund,
- Żywy Manekin: 60 sekund.

Po respawnie boss Krypty ponownie blokuje zejście.
Moby nadal nie są agresywne.



WIĘCEJ BOSSÓW ŚWIATA v0.6.66
----------------------------
1. Król Goblinów.
Lokacja: Obóz Goblinów.
360 HP.
720 Soul XP.
2600 Class XP.
2600 XP postaci.
Mechanika: co trzeci kontratak Królewska Szarża.
Unikalny drop: Korona Króla Goblinów, Zręczność +3.

2. Alfa Wilków Cienia.
Lokacja: Głębia Gaju.
390 HP.
780 Soul XP.
2900 Class XP.
2900 XP postaci.
Mechanika: poniżej połowy HP Szał Cienia, +40% obrażeń.
Unikalny drop: Kieł Alfy Cienia, Siła +4.

3. Strażnik Ruin.
Lokacja: Zrujnowana Wieża.
430 HP.
860 Soul XP.
3300 Class XP.
3300 XP postaci.
Mechanika: co czwarty kontratak Runiczny Wybuch.
Unikalny drop: Płyta Strażnika Ruin, Siła Woli +4.

4. Kryształowy Władca.
Lokacja: Kryształowa Komnata.
500 HP.
1000 Soul XP.
4000 Class XP.
4000 XP postaci.
Mechaniki: Kryształowy Promień co trzeci kontratak oraz
Kryształowa Bariera co czwarte trafienie gracza.
Unikalny drop: Rdzeń Kryształowego Władcy, Inteligencja +5.

Każdy z tych bossów:
- jest nieagresywny,
- odradza się po 300 sekundach,
- ma 45% szansy na własny unikalny przedmiot.


KOREKTA PROGRESJI v0.6.67
-------------------------
Soulbound NIE ma levelu postaci.

Zmiana v0.6.66 z Level 1-200 postaci została wycofana.
Jeśli baza SQLite była już uruchomiona na v0.6.66,
kolumny character_level i character_xp mogą fizycznie pozostać w tabeli.
Są jednak ignorowane przez grę i nie tworzą żadnej progresji postaci.

STATYSTYKI
----------
Siła, Zręczność, Kondycja, Inteligencja i Siła Woli
pozostają dokładnie na dotychczasowym systemie.

Każdy pełny próg Postępu Rozwoju:
Siła +1.
Zręczność +1.
Kondycja +1.
Inteligencja +1.
Siła Woli +1.

Nie ma ręcznego rozdawania punktów.

SOUL LEVEL 1-200
----------------
Broń Duszy rozwija się teraz od Soul Level 1 do 200.

Wzór Soul XP pozostaje:
180 + (Soul Level - 1) * 60.

Tier 2:
Soul Level 25 + Próba Broni Duszy u Kapłana Elora.

Tier 3:
Soul Level 60 + Próba Broni Duszy u Kapłana Elora.

Po Soul Level 100 rozwój nie zatrzymuje się.
Broń Duszy może rosnąć dalej do Soul Level 200.

Soul Level nadal zwiększa bazową moc Broni Duszy.

RZEMIOSŁO 1-200
----------------
Młot Rzemieślniczy i system Rzemiosła mają teraz level 1-200.

Inne narzędzia pozostają na levelu 1-100:
Wędka,
Kilof,
Piła,
Nóż Kucharski,
Sierp Zielarski,
Moździerz Alchemiczny.

Młot Rzemieślniczy:
level 1-200.

Tier 8 zaczyna się na levelu 100 i obejmuje cały zakres 100-200.
Po levelu 100 Młot nadal zdobywa XP za craftowanie.
Szansa bonusowego produktu Tieru 8 działa aż do levelu 200.

Komendy:
mlot
tools
craft
receptury

BOSSOWIE v0.6.66
----------------
Król Goblinów, Alfa Wilków Cienia, Strażnik Ruin i
Kryształowy Władca pozostają w grze wraz z mechanikami,
unikalnymi dropami i respawnem 300 sekund.


WSZYSTKIE NARZĘDZIA 1-200 v0.6.68
---------------------------------
Wszystkie 7 narzędzi rozwija się od levelu 1 do 200:

Wędka.
Kilof.
Piła.
Młot Rzemieślniczy.
Nóż Kucharski.
Sierp Zielarski.
Moździerz Alchemiczny.

Tier 8 zaczyna się na levelu 100 i trwa do levelu 200.
Po levelu 100 każde narzędzie nadal zdobywa XP.
Bonus Tieru 8 pozostaje aktywny aż do 200.

UŻYWANIE UMIEJĘTNOŚCI v0.6.68
-----------------------------
Dotychczas nadal działa:
skill <nazwa lub numer> [cel]
umiejętność <nazwa lub numer> [cel]
zdolność <nazwa lub numer> [cel]

Nowe warianty:
cast <nazwa lub numer> [cel]
użyj umiejętność <nazwa> [cel]
use skill <name> [target]

Komenda use/użyj próbuje najpierw rozpoznać przedmiot.
Jeżeli nie jest to przedmiot, ale rozpoznaje skill,
uruchamia istniejący system umiejętności.

Przykład:
użyj umiejętność <nazwa skilla> goblin
use skill <skill name> goblin

Nie zmienia to zasad walki:
moby nadal nie atakują same.
Ofensywny skill rozpoczyna walkę dopiero po akcji gracza.
Cooldown, Mana, Skill Level oraz Skill XP pozostają aktywne.

Soul Level nadal 1-200.
Soulbound nadal nie ma levelu postaci.


13 TIERÓW NARZĘDZI v0.6.69
--------------------------
Wszystkie 7 narzędzi nadal ma level 1-200,
ale progres 100-200 został podzielony na dodatkowe Tiery.

PROGI:
Tier 1: level 1-14, bonus 0%.
Tier 2: level 15-29, bonus 2%.
Tier 3: level 30-44, bonus 4%.
Tier 4: level 45-59, bonus 6%.
Tier 5: level 60-74, bonus 8%.
Tier 6: level 75-89, bonus 10%.
Tier 7: level 90-99, bonus 12%.
Tier 8: level 100-119, bonus 15%.
Tier 9: level 120-139, bonus 18%.
Tier 10: level 140-159, bonus 21%.
Tier 11: level 160-179, bonus 24%.
Tier 12: level 180-199, bonus 27%.
Tier 13: level 200, bonus 30%.

Bonus oznacza odpowiednio:
Wędka: szansa na dodatkowy połów.
Kilof: szansa na dodatkowy urobek.
Piła: szansa na dodatkowe drewno.
Młot Rzemieślniczy: szansa na dodatkowy produkt.
Nóż Kucharski: szansa na dodatkową potrawę.
Sierp Zielarski: szansa na dodatkowe zioło.
Moździerz Alchemiczny: szansa na dodatkową miksturę.

Każde narzędzie ma własne nazwy Tierów 9-13.

Przykładowo Młot Rzemieślniczy:
Tier 9: Młot Arcyrzemieślnika.
Tier 10: Młot Smoczej Kuźni.
Tier 11: Młot Astralnego Twórcy.
Tier 12: Młot Pradawnej Kuźni.
Tier 13: Młot Wiecznego Kowadła.

Komendy:
tools
tiers
wedka
kilof
pila
mlot
noz
sierp
mozdzierz

Soul Level pozostaje 1-200.
Levelu postaci nadal nie ma.


SZYBSZY WZROST STATYSTYK v0.6.70
--------------------------------
Statystyki rosną teraz dwa razy szybciej.

Stary próg:
100 Postępu Rozwoju.

Nowy próg:
50 Postępu Rozwoju.

Każde pełne 50 Postępu Rozwoju daje jednocześnie:
Siła +1.
Zręczność +1.
Kondycja +1.
Inteligencja +1.
Siła Woli +1.

Nie zmieniono sposobu działania statystyk.
Nadal nie ma ręcznego rozdawania punktów.
Nadal wszystkie pięć statystyk rośnie razem.

Bonus rasy Człowiek do zdobywanego Postępu Rozwoju nadal działa.

Soulbound nadal nie ma levelu postaci.
Soul Level pozostaje 1-200.
Narzędzia pozostają 1-200 z 13 Tierami.


PEŁNE HP PO SOUL LEVEL v0.6.71
------------------------------
Każdy awans Soul Level Broni Duszy odnawia teraz postać
do 100 procent maksymalnego HP.

Przykład:
masz 42 z 300 HP.
Zdobywasz Soul XP i wbijasz kolejny Soul Level.
Po awansie masz 300 z 300 HP.

Działa dla Soul XP z:
- pokonanych przeciwników,
- Eliksiru Duszy,
- każdego miejsca korzystającego z głównego systemu przyznawania Soul XP.

Jeżeli otrzymujesz Soul XP, ale nie awansujesz na nowy Soul Level,
HP pozostaje bez zmian.

Mana nie jest odnawiana.

Soul Level nadal ma zakres 1-200.


START PO ZALOGOWANIU v0.6.72
----------------------------
Po każdym zalogowaniu postać rozpoczyna sesję w:

Świątynia Odrodzenia.

Nie ma znaczenia, gdzie postać zakończyła poprzednią sesję.

Przykład:
wylogowujesz się na 73 piętrze Krypty.
Przy następnym logowaniu pojawiasz się w Świątyni Odrodzenia.

Portale Krypty i ich odblokowanie pozostają zapisane.
Questy, ekwipunek, waluty, Soul Level, klasy, profesje,
narzędzia i pozostała progresja nie są resetowane.

Nowe postacie również rozpoczynają wejście do świata w Świątyni Odrodzenia.


WALK I KRÓTKIE CELE v0.6.73
---------------------------
Nie trzeba już wpisywać:
walk to <lokacja>

Można od razu:
walk targ
walk kuznia
walk swiatynia
walk port
walk karczma
walk jaskinia
walk cmentarz
walk bandyci
walk gobliny
walk ruiny
walk jezioro
walk rzeka

Działają również:
prowadz targ
idz targ
go targ

Starsze:
walk to targ
guide targ

także pozostają działające.

PRZYKŁADOWE SKRÓTY NPC
----------------------
walk elor -> Świątynia Odrodzenia.
walk doran -> Kuźnia Dusz.
walk tomas -> Targ Rybny.
walk bran -> Obóz Drwala.
walk liora -> Chata Zielarki.
walk toren -> Wejście do Kryształowej Jaskini.
walk arven -> Strażnica.
walk roderik -> Wartownia Północna.
walk anna -> Wartownia Pogranicza.

KRYPTA
------
walk krypta 1
walk krypta 50
walk krypta 100

nadal działa dla wszystkich pięter.

Prowadzenie nie omija żywego bossa Krypty.


ENDGAME PROFESJI 100-200 v0.6.74
--------------------------------
Nowe progi zawartości:
100, 120, 140, 160, 180 i 200.

NOWE RUDY
---------
100: Ruda Kobaltu.
120: Ruda Kamienia Runicznego.
140: Ruda Smoczej Stali.
160: Ruda Astralna.
180: Ruda Pustki.
200: Ruda Eternium.

Czysty mithril nadal ma osobną, bardzo małą szansę:
level 100-200: 0,50%.

NOWE DREWNO
-----------
Dostępne w Głębi Gaju:
100: Pień Runicznego Drzewa.
120: Pień Smoczego Drzewa.
140: Pień Astralnego Drzewa.
160: Pień Drzewa Pustki.
180: Pień Gwiezdnego Serca.
200: Pień Wiecznego Drzewa Świata.

NOWE ZIOŁA
----------
Dostępne w Głębi Gaju:
100: Kwiat Słonecznego Ognia.
120: Smocza Szałwia.
140: Astralna Orchidea.
160: Lotos Pustki.
180: Korona Feniksa.
200: Wieczny Kwiat.

NOWE RYBY
---------
Każdy typ łowiska dostał nowe połowy high-level.
Ocean ma dodatkowo osobny nowy połów na każdym progu:
100 Niebiański Tuńczyk.
120 Smocze Mahi-mahi.
140 Tuńczyk Otchłani.
160 Marlin Burzy.
180 Księżycowy Lewiatan.
200 Wieczna Latimeria.

Rzeka, jezioro i morze także mają własne nowe gatunki od 100 do 200.

RECEPTURY RZEMIOSŁA
-------------------
100 Runiczny Talizman Straży.
120 Talizman Smoczej Kuźni.
140 Astralny Talizman Kuźni.
160 Talizman Straży Pustki.
180 Talizman Serca Świata.
200 Talizman Wiecznej Duszy.

RECEPTURY GOTOWANIA
-------------------
100 Runiczny Półmisek Rybny.
120 Smocza Potrawka Oceaniczna.
140 Stek Rybny Otchłani.
160 Uczta Marlina Burzy.
180 Uczta Lewiatana.
200 Wieczna Uczta Oceanu.

RECEPTURY ALCHEMII
------------------
100 Najwyższa Mikstura Leczenia.
120 Najwyższa Mikstura Many.
140 Wielki Eliksir Witalności.
160 Tonik Duszy.
180 Astralny Eliksir Odnowy.
200 Eliksir Wiecznej Duszy.

Każda receptura jest naprawdę zablokowana wymaganym levelem
Młota Rzemieślniczego, Noża Kucharskiego albo Moździerza Alchemicznego.
Lista receptur podaje wymagany level.


UŻYJ SKILLA / CZARU v0.6.75
----------------------------
Komenda użyj rozpoznaje teraz naturalne skróty skilli.

Przykłady:
użyj ciecie goblin
uzyj ciecie goblin
użyj pocisk goblin
użyj plomien goblin
użyj czar pocisk goblin
use spell arcane bolt goblin

Jeżeli skrót jest jednoznaczny wśród aktywnych klas,
gra uruchamia właściwą nauczoną umiejętność.

Pełne nazwy nadal działają:
skill Potężne Cięcie goblin
cast Pocisk Arkanów goblin
umiejętność Płomień Otchłani goblin

KUP NARZĘDZIE
-------------
Nazwy przy kupowaniu są teraz odporne na brak polskich znaków.

Przykłady:
kup wedka
kup kilof
kup pila
kup mlot
kup noz
kup sierp
kup mozdzierz

Narzędzia nadal są sprzedawane u właściwych sprzedawców.
Jeśli próbujesz kupić narzędzie w złym miejscu,
gra poda lokację właściwego sklepu.

IZOLOWANY XP NARZĘDZI
---------------------
Tylko używane narzędzie zdobywa XP i użycia.

Łowienie -> tylko Wędka.
Kopanie -> tylko Kilof.
Drwalstwo -> tylko Piła.
Rzemiosło -> tylko Młot Rzemieślniczy.
Gotowanie -> tylko Nóż Kucharski.
Zielarstwo -> tylko Sierp Zielarski.
Alchemia -> tylko Moździerz Alchemiczny.

Pozostałe sześć narzędzi nie zmienia:
levelu,
XP,
liczby użyć.

Samo kupienie narzędzia również nie daje XP.


PROWADZ MOST v0.6.76
--------------------
Nowe jawne skróty:

prowadz most
prowadz kamienny most
walk most
idz most
go most

Wszystkie prowadzą do lokacji:
Kamienny Most.


NOWE SKILLE KLASOWE 100-200 v0.6.77
-----------------------------------
Każda z 12 klas otrzymała 4 nowe skille:
Soul Level 100.
Soul Level 140.
Soul Level 180.
Soul Level 200.

Łącznie: 48 nowych umiejętności.

WOJOWNIK
100 Rozdarcie Duszy.
140 Żelazny Mur.
180 Szarża Bohatera.
200 Ostateczne Cięcie.

BERSERKER
100 Rzeźniczy Zamach.
140 Szał Tytana.
180 Krwawy Wir.
200 Apokalipsa Krwi.

ŁOTRZYK
100 Cięcie Widma.
140 Krok Cienia.
180 Taniec Ostrzy.
200 Egzekucja Cienia.

ŁOWCA
100 Strzała Duszy.
140 Kamuflaż Drapieżcy.
180 Deszcz Echa.
200 Strzał Końca.

MNICH
100 Pięść Duszy.
140 Medytacja Mistrza.
180 Smocza Seria.
200 Cios Oświecenia.

STRAŻNIK
100 Uderzenie Fortecy.
140 Wieczny Bastion.
180 Gniew Bastionu.
200 Młot Końca.

MAG
100 Lanca Arkanów.
140 Aegis Arkanów.
180 Burza Many.
200 Kataklizm Arkanów.

NEKROMANTA
100 Klątwa Kości.
140 Wielkie Wysysanie.
180 Żniwo Umarłych.
200 Wyrok Śmierci.

KAPŁAN
100 Promień Światła.
140 Wielkie Uzdrowienie.
180 Aegis Światła.
200 Cud Odrodzenia.

CZAROWNIK
100 Ogień Pustki.
140 Tarcza Otchłani.
180 Inferno Otchłani.
200 Piekielny Wyrok.

DRUID
100 Pradawne Korzenie.
140 Odnowa Gaju.
180 Burza Żywiołów.
200 Gniew Drzewa Świata.

PSIONIK
100 Ostrze Umysłu.
140 Forteca Umysłu.
180 Rozdarcie Jaźni.
200 Koniec Myśli.

Nowe skille uczysz się u dotychczasowych nauczycieli klasowych.
Każdy ma osobny Skill Level 1-100.

NATURALNE UŻYJ
--------------
Przykłady:
użyj heal
użyj tarcza
użyj unik
użyj drain goblin
użyj dobij goblin
użyj ciecie goblin
użyj pocisk goblin
użyj ogien goblin
użyj burza goblin
użyj mlot goblin
użyj strzal goblin

System wybiera najwyżej odblokowaną i nauczoną umiejętność
pasującą do naturalnego skrótu.

Przy remisie w multiclassie nie wybiera losowo.
Wtedy użyj pełnej nazwy skilla.


SKILL LEVEL 1-200 v0.6.78
-------------------------
Wszystkie umiejętności mogą rozwijać własny Skill Level aż do 200.

Dawny limit:
Skill Level 100.

Nowy limit:
Skill Level 200.

Skill XP nadal zdobywa się przez używanie nauczonego skilla.
Formuła wymaganego XP pozostaje:
50 + (Skill Level - 1) * 25.

Przykłady:
Skill Level 100 -> 101 wymaga 2525 XP.
Skill Level 140 -> 141 wymaga 3525 XP.
Skill Level 180 -> 181 wymaga 4525 XP.
Skill Level 199 -> 200 wymaga 5000 XP.

Moc skilla nadal rośnie wraz ze Skill Level aż do 200.
Redukcja cooldownu ma dotychczasowy maksymalny limit 30%.

WOLNIEJSZY ROZWÓJ NARZĘDZI
---------------------------
Narzędzia nadal mają:
level 1-200,
13 Tierów.

Od v0.6.78 wymagany XP narzędzia jest 2 razy większy.

Stara formuła:
60 + (level - 1) * 30.

Nowa formuła:
2 * (60 + (level - 1) * 30).

Przykłady:
level 1 -> 2: było 60 XP, jest 120 XP.
level 100 -> 101: było 3030 XP, jest 6060 XP.
level 199 -> 200: było 6000 XP, jest 12000 XP.

Ilość XP otrzymywanego z używania narzędzia, receptur i nagród
nie została zmniejszona.

Nieużywane narzędzia nadal nie zdobywają XP.


WOLNIEJSZE PROFESJE + WIĘKSZY XP v0.6.79
-----------------------------------------
Dotyczy pięciu profesji:
Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Alchemia.

Otrzymywany XP profesji:
2 razy większy.

Wymagany XP na level:
4 razy większy.

Efekt:
profesje levelują około 2 razy wolniej.

Level 1 -> 2:
było 80 XP,
jest 320 XP.

Level 50 -> 51:
było 1795 XP,
jest 7180 XP.

Level 99 -> 100:
było 3510 XP,
jest 14040 XP.

Typowa akcja:
było około 10-15 XP,
jest około 20-30 XP.

Quest dający wcześniej 1000 XP profesji:
teraz daje 2000 XP profesji.

Narzędzia nie są zmienione w tym buildzie.
Pozostają 1-200, 13 Tierów i wolniejszy XP z v0.6.78.

ZAKŁADANIE LOOTU Z MOBÓW
-------------------------
Po:
przeszukaj ciało

ekwipunek trafia do zwykłego inventory.

Możesz potem wpisać:
załóż hełm
załóż zbroja
załóż rękawice
załóż nogi
załóż buty
załóż talizman

Działają również:
zaloz helm
zaloz zbroja
zaloz rekawice
zaloz nogi
zaloz buty
zaloz talizman

Jeżeli masz kilka przedmiotów w jednym slocie,
skrót wybiera najlepszy według:
1. obrony,
2. rzadkości,
3. wartości affixu.

Możesz też podać pełną nazwę konkretnego dropu,
jeżeli chcesz założyć dokładnie ten przedmiot.

System działa również dla:
zwykłego lootu mobów,
world bossów,
Krypty,
rarity Krypty,
affixów Krypty,
setów Krypty.

W czasie walki zmiana ekwipunku nadal jest zablokowana.


SIATKA: ILOŚĆ RYB I WARTOŚĆ v0.6.80
------------------------------------
Wpisz:
siatka

albo:
net

Gra nadal czyta wszystkie gatunki i ich ilości.

Na końcu podaje:
łączną liczbę wszystkich ryb,
liczbę różnych gatunków,
szacowany zarobek ze sprzedaży całej Siatki.

Przykład:
Mała ryba x10.
Złoty pstrąg x3.
Widmowy marlin x1.
Łącznie ryb: 14. Gatunków: 3.
Szacowany zarobek ze sprzedaży całej siatki:
80 srebra, 3 złota, 1 mithrilu.

Waluty są liczone osobno.
Gra nie przelicza automatycznie srebra na złoto ani złota na mithril.

Podsumowanie obejmuje tylko ryby w Siatce.
Ryby w zwykłym inventory nie są doliczane.

Samo sprawdzenie siatki niczego nie sprzedaje.


WARTOŚĆ WSZYSTKICH MAGAZYNÓW PROFESJI v0.6.81
----------------------------------------------
SIATKA
siatka
net

Pokazuje:
łączną liczbę ryb,
liczbę gatunków,
wartość sprzedaży całej siatki.

SAKWA GÓRNICZA
sakwa
bag

Pokazuje:
łączną liczbę rud,
liczbę rodzajów rud,
wartość sprzedaży całej sakwy.

STOS DREWNA
drewno
stos
woodpile

Pokazuje:
łączną liczbę sztuk drewna,
liczbę rodzajów drewna,
wartość sprzedaży całego stosu.

TORBA ZIELARSKA
ziola
herbs

Pokazuje:
łączną liczbę ziół,
liczbę rodzajów ziół,
wartość sprzedaży całej torby.

W każdej sekcji srebro, złoto i mithril są liczone osobno.
Inventory nie jest doliczane.
Sprawdzenie magazynu niczego nie sprzedaje.

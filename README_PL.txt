SOULBOUND v0.6.6 THREE CURRENCIES
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

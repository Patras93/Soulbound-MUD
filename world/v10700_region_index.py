# -*- coding: utf-8 -*-
"""v107 – rozdzial I (5 z planowanych 30 nowych krain).

Te krainy sa dostepne wyłącznie przy SOULBOUND_V107_STAGING=1.
Kolejne rozdzialy nie sa jeszcze tworzone ani deklarowane jako gotowe.
"""
from __future__ import annotations

# slug, nazwa, opis, boss 1, boss 2, 10 nazw potworow, 4 materialy
CHAPTER_ONE = (
    (
        'rozdarcie', 'Równina Rozdarcia',
        'Ziemię przecinają świecące szczeliny. W każdej słychać inny oddech Chaosu.',
        'Strażnik Pierwszej Szczeliny', 'Monarcha Otwartego Rozdarcia',
        ('Zwiadowca Pęknięcia', 'Łowca Szczelin', 'Szeptacz Rozdarcia',
         'Zbrojny Bez Cienia', 'Przywołany Odłamek', 'Kroczący Rozłam',
         'Nocny Kartograf', 'Żołnierz Chaosu', 'Tkacz Pęknięć', 'Władca Pyłu'),
        ('Pył Szczeliny', 'Odłamek Rozdarcia', 'Rdzeń Pęknięcia', 'Pieczęć Chaosu'),
    ),
    (
        'odlamki', 'Las Odłamków',
        'Szkliste drzewa gromadzą porwane wspomnienia, a pod korzeniami migoczą runy.',
        'Pasterz Szklanych Korzeni', 'Serce Rozbitego Boru',
        ('Zwiadowca Igliwia', 'Szklany Dzięcioł', 'Złamana Driada',
         'Leśny Szkielet', 'Włóczęga Korzeni', 'Zabłąkany Drzewiec',
         'Runiczny Jeleń', 'Szeptacz Liści', 'Mściciel Boru', 'Strażnik Pnia'),
        ('Szkliste Igliwie', 'Fragment Kory', 'Runa Korzeni', 'Zielony Kryształ'),
    ),
    (
        'glosy', 'Zatoka Pustych Głosów',
        'Fale niosą głosy osób, których już nie ma. Mgła skrywa opuszczone kutry.',
        'Latarnik Zamilkłej Zatoki', 'Kapitan Tysiąca Głosów',
        ('Pusty Marynarz', 'Wodny Szept', 'Mgielny Harpunnik',
         'Strażnik Molo', 'Upiór Kutra', 'Rozbitek Bez Imienia',
         'Zaklęty Krab', 'Wodny Cień', 'Sternik Mgły', 'Żeglarz Pustki'),
        ('Sól Wspomnień', 'Wodorost Echa', 'Muszla Ciszy', 'Latarniany Kamień'),
    ),
    (
        'popiol', 'Bastion Popiołu',
        'Stare mury są gorące nawet nocą. W piwnicach biją serca z żaru.',
        'Hetman Popielnych Murów', 'Cesarz Nieskończonego Żaru',
        ('Popielny Piechur', 'Żarowy Strzelec', 'Ognisty Uciekinier',
         'Golem Spieków', 'Błędny Kowal', 'Płonący Posłaniec',
         'Wartownik Popiołu', 'Krwawa Iskra', 'Mistrz Pieców', 'Rycerz Zwęglonej Stali'),
        ('Pył Spalonej Kuźni', 'Stopiony Gwóźdź', 'Serce Żaru', 'Piecowa Pieczęć'),
    ),
    (
        'zelazne_gwiazdy', 'Kraina Żelaznych Gwiazd',
        'Po niebie płyną metalowe konstelacje. Spadające iskry budzą stare machiny.',
        'Sędzia Meteorowych Run', 'Żelazny Arcygwiazdozbiór',
        ('Meteorowy Włócznik', 'Konstruktor Gwiazd', 'Żelazny Zwiadowca',
         'Astralny Mechanizm', 'Kowal Komety', 'Strażnik Konstelacji',
         'Robotnik Zorzy', 'Przebudzona Zbroja', 'Utracony Kompas', 'Herold Żelaza'),
        ('Pył Meteorytu', 'Ruda Gwiazd', 'Gwiezdne Ogniwo', 'Znak Konstelacji'),
    ),
)
assert len(CHAPTER_ONE) == 5
assert len({row[0] for row in CHAPTER_ONE}) == len({row[1] for row in CHAPTER_ONE}) == 5
assert all(len(row[5]) == 10 and len(row[6]) == 4 for row in CHAPTER_ONE)

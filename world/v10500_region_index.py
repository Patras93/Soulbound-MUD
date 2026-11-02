# -*- coding: utf-8 -*-
"""v105: 20 authored endgame regions, 10001–30000 inclusive."""
NAMES = (
    ('przesmyk','Przesmyk Wygasłych Słońc','Strażnik Popiołu','Wygasłe Słońce'),
    ('archipelag','Archipelag Wędrujących Gór','Nawigator Szczytów','Tytan Wędrujących Gór'),
    ('pioruny','Kotlina Cichych Piorunów','Huk Bez Głosu','Władca Burz'),
    ('ogrody','Żelazne Ogrody','Stalowy Ogrodnik','Król Żelaznych Korzeni'),
    ('korona','Bastion Rozbitej Korony','Zbrojny Regent','Ostatni Król Bastionu'),
    ('mgly','Mgławica Miedzianych Mgieł','Miedziany Wieszcz','Pani Nieskończonej Mgły'),
    ('zwierciadla','Pustkowie Tysiąca Zwierciadeł','Odbity Łowca','Pan Tysiąca Odbić'),
    ('nekropolia','Nekropolia Zegarów','Mechaniczny Upiór','Wieczny Zegarmistrz'),
    ('plomienie','Cytadela Bursztynowych Płomieni','Żarowy Rycerz','Bursztynowy Feniks'),
    ('obserwatorium','Obserwatorium Zapomnianych','Strażnik Obserwatorium','Archont Zapomnianych'),
    ('las','Las Odwróconego Nieba','Odwrócony Druid','Korzeń Nieba'),
    ('golemy','Kraina Milczących Golemów','Golem Ciszy','Pierwszy Kamień'),
    ('burze','Twierdza Siedmiu Burz','Herold Siedmiu Burz','Pan Siedmiu Żywiołów'),
    ('bramy','Dolina Zapieczętowanych Bram','Strażnik Pieczęci','Władca Zamkniętych Wrót'),
    ('piesni','Miasto Spopielonych Pieśni','Cień Pieśniarza','Król Popielnych Głosów'),
    ('kometa','Pałac Widmowej Komety','Kometarny Strażnik','Widmo Władczyni Komety'),
    ('fale','Morze Skamieniałych Fal','Kamienny Żeglarz','Pradawny Lewiatan'),
    ('przysiegi','Labirynt Zaginionych Przysiąg','Złamany Przysięgły','Sędzia Przysiąg'),
    ('tytani','Szlak Nocnych Tytanów','Nocny Wojownik','Najstarszy Tytan'),
    ('przelom','Korona Wiecznego Przełomu','Posłaniec Przełomu','Monarcha Wieczności'),
)
REGIONS=tuple((slug,name,10001+1000*i,11000+1000*i,boss1,boss2) for i,(slug,name,boss1,boss2) in enumerate(NAMES))
assert len(REGIONS)==20 and REGIONS[-1][3]==30000

# -*- coding: utf-8 -*-
"""Class-authored names for procedural mastery alternatives, v11.00.10.

This file never changes a skill ID, effect, level, cost, or ownership.  The
pre-v11.00.10 name remains an exact command alias for old macros and players.
"""
from collections import defaultdict
import re
import unicodedata

# Proper genitive forms: the same common 'Żelazny Próg' MUST NOT be attached
# indiscriminately to a druid spell, monk technique and a Mec weapon system.
_MOTIFS = {
    'Wojownik': '''Ostatniej Warty|Przełamanej Linii|Stalowego Sztandaru|Królewskiej Szarży|Weteranów Północy|Bratniego Oręża|Oblężonej Bramy|Straży Koronnej|Rycerskiego Ślubowania|Bitwy o Przełęcz|Zwycięskiego Legionu|Ostrza Przodków|Tysiąca Mieczy|Nieugiętego Frontu|Pola Honorowego|Wojennego Werbla|Wyłomu w Murze|Żołnierskiej Przysięgi''',
    'Berserker': '''Krwawego Amoku|Rozbitej Czaszki|Szału Przodków|Szkarłatnej Rzezi|Wilczego Głodu|Gniewu Topora|Rozdartych Łańcuchów|Pękającej Kości|Ostatniego Ryku|Dzikości Północy|Rzeźniczego Tańca|Płonącej Furii|Bestii Bez Kajdan|Krwawych Żył|Frenezji Polowania|Potępieńczej Rany|Wściekłego Kolosa|Gniewnego Uderzenia''',
    'Łotrzyk': '''Cichej Zasadzki|Zatrutego Sztyletu|Zdradzonej Przysięgi|Mroku Zaułka|Cienia za Plecami|Skrytego Ostrza|Znikającego Śladu|Nocnej Zasłony|Ostatniego Świadka|Kieszonkowego Ostrza|Tańca Sztyletów|Zerwanej Pieczęci|Sekretu Gildii|Szeptu Zabójcy|Mroku Dachów|Fałszywego Kroku|Ulicznej Mgły|Ukrytej Klingi''',
    'Łowca': '''Sokolego Lotu|Cichego Tropu|Sarniej Ścieżki|Myśliwskiego Świtu|Wilczej Nory|Dzikiego Zwierza|Leśnej Zasadzki|Przeszywającej Strzały|Śladu w Błocie|Wiatru nad Knieją|Jeleniego Rogu|Napiętej Cięciwy|Zielonej Polany|Szeptu Boru|Dalekiego Łuku|Zwietrzonego Tropu|Nocnego Łowiska|Strzały bez Echa''',
    'Mnich': '''Oddechu Lotosu|Otwartej Dłoni|Wewnętrznej Równowagi|Ciszy Świątyni|Punktu Meridianu|Smoczego Ki|Siedmiu Oddechów|Przepływu Chi|Pustej Pięści|Rozkwitu Lotosu|Szczytu Medytacji|Oka Spokoju|Przebudzonego Ciała|Kroku Żurawia|Drogi Smoka|Duchowej Harmonii|Cichego Mistrza|Kręgu Wschodzącego Słońca''',
    'Strażnik': '''Kamiennego Bastionu|Obrony Bramy|Muru Przysięgi|Młota Obrońcy|Ostatniej Tarczy|Niezłomnego Garnizonu|Kamiennej Twierdzy|Żelaznego Szańca|Straży Wschodniej|Warownego Progu|Nocnej Warty|Oblężonej Fortecy|Gwardii Miasta|Ciosu Baszty|Twardej Zbroi|Prawa Straży|Ostatniego Muru|Przysięgi Garnizonu''',
    'Mag': '''Runicznej Iskry|Gwiezdnych Arkanów|Płomiennej Formuły|Eterycznej Matrycy|Kryształowej Many|Zakazanego Zwoju|Niebieskiej Runy|Ognia w Rękach|Szkoły Żywiołów|Astralnego Kręgu|Splotu Zaklęcia|Sfery Błyskawic|Pulsu Eteru|Wielkiego Grimuaru|Lustrzanej Many|Pęknięcia Przestrzeni|Tajemnej Pieczęci|Woli Arcymaga''',
    'Nekromanta': '''Kościanego Legionu|Zimnego Grobu|Niespokojnych Dusz|Krwi na Ołtarzu|Pustego Sarkofagu|Cmentarnego Szeptu|Prochu Umarłych|Kostnego Żniwa|Pogrzebowego Dzwonu|Martwej Królowej|Głodu Życia|Klątwy Grobowca|Szkieletowego Marszu|Zagasłej Świecy|Czarnych Katakumb|Śmiertelnej Wstęgi|Trumny Bez Imienia|Rytuału Kości''',
    'Kapłan': '''Łaski Uzdrowienia|Świętego Ołtarza|Płomienia Wiary|Miłosierdzia Świątyni|Złotego Sanktuarium|Modlitwy Ocalenia|Światła Przymierza|Cudu Wspólnoty|Błogosławionego Kielicha|Ukojenia Cierpienia|Świtu Odkupienia|Dłoni Opiekuna|Ostatniej Modlitwy|Ochrony Niewinnych|Świątynnego Dzwonu|Promienia Nadziei|Duchowego Uzdrowienia|Przebaczenia Dusz''',
    'Czarownik': '''Czarnego Paktu|Kropli Otchłani|Bezimiennej Klątwy|Płomienia Pustki|Szeptu Demona|Krwi Kontraktu|Piekielnego Pergaminu|Złamanego Zaklęcia|Znaku Potępienia|Zamkniętej Bramy|Przerażającej Ofiary|Dłoni Ciemności|Siedmiu Przekleństw|Cienia Paktodawcy|Ostatniego Długu|Rytuału Bezdna|Zabronionego Słowa|Pustego Tronu''',
    'Druid': '''Starego Dębu|Zielonego Gaju|Żywej Kory|Szeptu Korzeni|Leśnego Kręgu|Pradawnej Kniei|Mchu Uzdrowienia|Wiosennego Deszczu|Wilczego Ducha|Węzła Korzeni|Oddechu Puszczy|Dzikiej Gałęzi|Świętego Ziarna|Ciernia o Zmierzchu|Rosy Świtu|Odrodzonej Natury|Leśnego Źródła|Drzewa Życia''',
    'Psionik': '''Otwartego Umysłu|Kryształowej Jaźni|Trzeciego Oka|Cichej Myśli|Pękniętej Pamięci|Astralnego Splotu|Złudzenia Czaszki|Szeptu Woli|Mentalnej Fali|Wspomnienia Snów|Psionicznego Impulsu|Woli Bez Granic|Labiryntu Myśli|Nieprzeniknionej Jaźni|Myślowej Igły|Przebudzonej Świadomości|Snu Obcego Umysłu|Krawędzi Rozumu''',
    'Mec': '''Reaktora Duszy|Plazmowego Działa|Celownika Bojowego|Magitekowego Rdzenia|Układu Odporności|Satelitarnego Łącza|Impulsu Jonowego|Wielkiego Egzoszkieletu|Pancerza Sprzężenia|Nanomodułu Naprawy|Mechanizmu Przeciążenia|Siatki Namierzania|Serwomotoru Wojny|Lufy Orbitalnej|Tytanowego Napędu|Rdzenia Ocalenia|Programu Bojowego|Laserowego Przebicia''',
    'Inżynier': '''Prototypu Turbiny|Stacji Naprawczej|Sprężynowej Pułapki|Nitowanej Maszyny|Nanoskalpela|Ładunku Odłamkowego|Automatycznej Wieżyczki|Żyroskopu Celowania|Precyzyjnej Śruby|Wiertła Mechanika|Laboratoryjnej Iskry|Przekaźnika Warsztatu|Miedzianego Przewodu|Wzmocnionego Narzędzia|Sygnału Alarmowego|Modułu Kalibracji|Eksperymentalnej Bomby|Pancerza Polowego''',
    'Paladyn': '''Świętej Przysięgi|Miecza Sprawiedliwości|Łaski Świtu|Obrońcy Niewinnych|Złotego Sanktuarium|Świetlistego Ślubowania|Pielgrzymiego Ołtarza|Prawa Miłosierdzia|Promienia Odkupienia|Dłoni Przymierza|Ostatniego Światła|Ochrony Słabszych|Odważnego Serca|Złamanego Mroku|Tarczy Prawdy|Modlitwy Rycerza|Ognia Poświęcenia|Świętej Straży''',
    'Samuraj': '''Ostrza Honoru|Wschodniego Wiatru|Cichego Dojo|Siedmiu Cięć|Księżycowej Katany|Drogi Wojownika|Płonącej Wiśni|Niewidzialnego Zamachu|Pierwszego Doboru|Stalowej Dyscypliny|Ostatniego Ukłonu|Kroku Kensei|Szybkiego Dobycza|Wschodu Słońca|Cienia Mistrza|Próby Bushido|Spadającego Liścia|Szermierczej Ciszy''',
    'Korsarz': '''Czarnej Bandery|Sztormowego Pokładu|Abordażu o Świcie|Żagli Korsarza|Głębinowej Rafy|Kapitańskiego Rozkazu|Morskiej Zasadzki|Huku Armat|Portowego Pościgu|Burty Galeonu|Płonącej Beczki|Szlaku Piratów|Zatopionego Statku|Słonej Bryzy|Muszkietowego Dymu|Krwawego Haka|Ostatniej Kotwicy|Tajemnej Mapy''',
    'Gladiator': '''Piasku Areny|Ostatniego Pojedynku|Werdyktu Trybun|Miecza Czempiona|Krwawego Koloseum|Rzymskiego Gladiusa|Łańcuchów Areny|Ryku Publiczności|Niezłomnego Zawodnika|Pancerza Gladiatora|Śmiertelnej Walki|Sławy Koloseum|Mosiężnej Bramy|Woli Zwycięzcy|Złamanej Włóczni|Ostatniego Gongu|Wyroku Cesarza|Pojedynku o Wolność''',
    'Chronomanta': '''Zatrzymanej Sekundy|Rozbitego Zegara|Koła Przyszłości|Wstecznej Minuty|Przestawionej Klepsydry|Pętli Wydarzeń|Czasowego Echa|Skoku przez Epoki|Pękniętej Chronologii|Ukradzionej Godziny|Straconej Chwili|Paradoksu Świtu|Chronalnej Pieczęci|Cofniętego Losu|Obrotu Wskazówek|Wiecznego Teraz|Spowolnionego Czasu|Zamrożonego Jutra''',
    'Iluzjonista': '''Lustrzanego Labiryntu|Pękniętego Zwierciadła|Oszukanego Spojrzenia|Złudnego Snu|Maski Bez Twarzy|Niewidzialnego Kroku|Odbicia Księżyca|Szeptu Mirażu|Fałszywej Postaci|Znikającego Cienia|Tysiąca Odbić|Kłamstwa Obrazu|Wielkiego Przebrania|Sztucznego Horyzontu|Zamiany Miejsc|Mglistej Kurtyny|Ukrytej Sceny|Lustrzanego Błysku''',
    'Bard': '''Pierwszego Akordu|Pieśni Przyjaźni|Lutni Wędrowca|Siedmiu Tonów|Melodii Odwagi|Rezonansu Strun|Chóru Towarzyszy|Złotej Harmonii|Dźwięku Zwycięstwa|Ballady Ocalenia|Ostatniej Zwrotki|Skrzypcowego Żaru|Rytmu Karawany|Mistrzowskiej Kody|Cichej Kołysanki|Śpiewu Podróżnych|Rozstrojonego Finału|Wieczornego Koncertu''',
    'Szaman': '''Totemu Przodków|Ducha Burzy|Wilczego Opiekuna|Zwierzęcego Transu|Rytualnego Bębna|Wężowego Znaku|Ogniska Plemienia|Niebieskiego Pioruna|Świętego Dymu|Kościanej Grzechotki|Pieśni Przodków|Deszczowego Tańca|Rozmowy z Duchami|Serca Plemienia|Nocnego Obrzędu|Orlego Ducha|Gniewu Ziemi|Przebudzenia Totemów''',
}

# Class-specific combat vocabulary.  Each type refers to its ACTUAL mechanical
# kind.  No more 'Tarcza' as the name of a healing ability or an AoE salvo.
# For each class: offense, defence, empowerment, healing, area (5 alternatives).
_ACTIONS = {
    'Wojownik': ('Cięcie|Szarża|Riposta|Pchnięcie|Przełamanie', 'Garda|Parada|Osłona|Blok|Warta', 'Rozkaz|Mobilizacja|Sztandar|Zew|Hartowanie', 'Odpoczynek|Oddech|Ocalenie|Regeneracja|Opatrunek', 'Wir Ostrzy|Nawałnica Stali|Szereg Ciosów|Fala Oręża|Szturm Legionu'),
    'Berserker': ('Zamach|Rozdarcie|Rąbnięcie|Rozłupanie|Cios', 'Skóra|Opór|Niezłomność|Wytrwanie|Zaciętość', 'Furia|Szał|Wściekłość|Ryk|Amok', 'Odnowa Krwi|Głód Życia|Zasklepienie|Powrót Sił|Ukojenie', 'Rzeź|Huragan Toporów|Krąg Gniewu|Szturm|Nawałnica'),
    'Łotrzyk': ('Sztych|Pchnięcie|Podcięcie|Riposta|Ukłucie', 'Unik|Zniknięcie|Zasłona|Odskok|Zmylenie', 'Skupienie|Oszustwo|Zasadzka|Impuls|Przewaga', 'Opatrunek|Odpoczynek|Przetrwanie|Wytrwanie|Ratunek', 'Wir Sztyletów|Deszcz Ostrzy|Krąg Cieni|Nocna Seria|Szał Kling'),
    'Łowca': ('Strzał|Pocisk|Przebicie|Trafienie|Strzała', 'Odskok|Unik|Czujność|Instynkt|Zmylenie', 'Wypatrywanie|Skupienie|Napięcie Łuku|Tropienie|Instynkt', 'Opatrunek|Balsam|Odnowa|Leśny Odpoczynek|Ukojenie', 'Grad Strzał|Nawałnica Bełtów|Salwa Łuku|Burza Strzał|Deszcz Pocisków'),
    'Mnich': ('Uderzenie|Pięść|Kopnięcie|Dotyk|Przebicie Ki', 'Unik|Krok|Postawa|Równowaga|Odbicie', 'Medytacja|Koncentracja|Harmonia|Dyscyplina|Skupienie', 'Ukojenie|Odnowa|Leczenie|Regeneracja|Zjednoczenie', 'Krąg Ki|Wir Pięści|Taniec Kopnięć|Fala Ducha|Kaskada Uderzeń'),
    'Strażnik': ('Cios Młota|Pogrom|Taran|Uderzenie|Rozbicie', 'Mur|Zasłona|Tarcza|Wzmocnienie Zbroi|Osłona', 'Przysięga|Hartowanie|Rozkaz Warty|Mobilizacja|Niezłomność', 'Odpoczynek|Wytchnienie|Odnowa|Opatrunek|Ratunek', 'Fala Młotów|Krąg Ciosów|Napór Gwardii|Burza Uderzeń|Szturm Warowni'),
    'Mag': ('Pocisk|Lanca|Iskra|Impuls|Promień', 'Bariera|Pieczęć|Zasłona|Krąg Obrony|Osłona', 'Zaklęcie Mocy|Skupienie|Inkantacja|Przywołanie Many|Nasycenie', 'Regeneracja|Odnowienie|Uleczenie|Esencja Życia|Ocalenie', 'Burza Zaklęć|Nova Arkanów|Deszcz Płomieni|Wir Run|Fala Eteru'),
    'Nekromanta': ('Kościany Pocisk|Dotyk|Przebicie|Ukłucie|Znak', 'Pancerz Kości|Zasłona|Mur|Osłona|Sarkofag', 'Rytuał|Przywołanie|Szept|Zew|Koronacja Umarłych', 'Wysysanie Życia|Odzyskanie Sił|Odnowa|Wyssanie Życia|Uzdrawiający Mrok', 'Żniwo Dusz|Marsz Umarłych|Chmura Zgnilizny|Fala Grobów|Burza Kości'),
    'Kapłan': ('Promień|Święty Dotyk|Osąd|Płomień|Uderzenie Światła', 'Aureola|Bariera|Ochrona|Zasłona|Sanktuarium', 'Błogosławieństwo|Modlitwa|Natchnienie|Oświecenie|Uświęcenie', 'Łaska|Uzdrowienie|Dotyk Życia|Ocalenie|Odnowa', 'Krąg Światła|Sąd Niebios|Fala Wiary|Rozbłysk|Deszcz Łaski'),
    'Czarownik': ('Klątwa|Pocisk|Zaklęcie|Ukłucie|Dotyk', 'Bariera|Znak|Zasłona|Krąg Ochronny|Pieczęć', 'Pakt|Przyzwanie|Przysięga|Ofiara|Inkantacja', 'Pakt Życia|Uzdrowienie|Odkupienie|Ocalenie|Zasilenie', 'Eksplozja Otchłani|Krąg Klątw|Wir Pustki|Pożoga Bezdna|Fala Mroku'),
    'Druid': ('Cierń|Pazur|Uderzenie Korzenia|Kolec|Pnącze', 'Kora|Osłona Liści|Mur Korzeni|Zasłona Mchu|Pień', 'Przebudzenie|Zew Lasu|Pieśń Natury|Przymierze|Wzrost', 'Odnowa|Lecząca Rosa|Zielona Łaska|Regeneracja|Wiosenne Ukojenie', 'Burza Korzeni|Krąg Liści|Deszcz Cierni|Nawałnica Pnączy|Fala Gaju'),
    'Psionik': ('Impuls|Igła Myśli|Psychiczny Cios|Przeniknięcie|Pęknięcie', 'Bariera Woli|Forteca Myśli|Osłona Jaźni|Pancerz Mentalny|Zasłona', 'Koncentracja|Skupienie Jaźni|Przebudzenie|Wzmocnienie Umysłu|Splot', 'Ocalenie Jaźni|Odnowa Woli|Regeneracja|Wyciszenie|Harmonia', 'Burza Psioniczna|Kaskada Myśli|Krąg Woli|Wstrząs Mentalny|Fala Jaźni'),
    'Mec': ('Strzał Lasera|Uderzenie Modułu|Cięcie Mocy|Pocisk|Impuls', 'Pancerz|Osłona Tytanu|Protokół Ochrony|Bariera|Przechwyt', 'Przeciążenie|Kalibracja|Protokół Bojowy|Ładowanie|Aktywacja', 'Wiązka Lecząca|Samonaprawa|Wzmocnienie Osłon|Odbudowa|Przywrócenie', 'Salwa Laserów|Orbitalny Nalot|Impuls Plazmy|Deszcz Pocisków|Eksplozja Reaktora'),
    'Inżynier': ('Strzał Wieżyczki|Uderzenie Wiertła|Cios Maszyny|Impuls|Pocisk', 'Osłona Polowa|Naprawa Pancerza|Bariera|Wzmocnienie Kadłuba|Blok', 'Kalibracja|Modyfikacja|Dostrojenie|Przeładowanie|Aktywacja', 'Naprawa|Regeneracja|Łatanie|Przywrócenie|Wzmocnienie', 'Detonacja|Ładunek Odłamkowy|Salwa Wieżyczek|Seria Min|Eksplozja'),
    'Paladyn': ('Cios Sprawiedliwości|Uderzenie Miecza|Osąd|Promień|Rozcięcie', 'Tarcza|Osłona Wiary|Aureola|Bastion|Obrona', 'Przysięga|Błogosławieństwo|Ślubowanie|Hartowanie Wiary|Zew', 'Uzdrowienie|Łaska|Dotyk Miłosierdzia|Ocalenie|Odnowa', 'Rozbłysk|Krąg Świętości|Fala Świtu|Sąd Światła|Nawałnica Mieczy'),
    'Samuraj': ('Cięcie Katany|Szybki Zamach|Pchnięcie|Kontra|Uderzenie', 'Unik|Odskok|Parada|Postawa|Zejście', 'Skupienie|Dyscyplina|Przysięga|Koncentracja|Natchnienie', 'Ukojenie|Wyciszenie|Odnowa|Odpoczynek|Wytchnienie', 'Wir Katany|Deszcz Cięć|Taniec Kling|Nawałnica Ostrzy|Burza Pchnięć'),
    'Korsarz': ('Cięcie Szabli|Strzał Muszkietu|Pchnięcie Hakiem|Zamach|Uderzenie', 'Unik Pokładowy|Odskok|Osłona|Parada|Zasłona', 'Rozkaz Kapitana|Sygnał|Mobilizacja|Zew Załogi|Przewaga', 'Balsam Marynarza|Opatrunek|Powrót Sił|Odpoczynek|Leczenie', 'Salwa Dział|Ogień Pokładowy|Grad Kul|Wir Szabel|Burza Strzałów'),
    'Gladiator': ('Cięcie Gladiusa|Uderzenie|Pogrom|Przebicie|Kontra', 'Garda|Blok|Osłona Tarczy|Postawa|Odbicie', 'Ryk Czempiona|Mobilizacja|Zew Trybun|Niezłomność|Wola', 'Opatrunek|Przetrwanie|Odpoczynek|Odnowa|Ratunek', 'Wir Gladiusów|Nawałnica Ciosów|Taniec Areny|Krąg Mieczy|Szturm'),
    'Chronomanta': ('Impuls Chronalny|Pęknięcie|Strzała Czasu|Cios Paradoksu|Rozcięcie Chwili', 'Osłona Czasu|Bariera Chwili|Zasłona|Zastój|Ochrona', 'Przyspieszenie|Cofnięcie|Skupienie|Przewinięcie|Nasycenie', 'Odnowienie|Cofnięcie Ran|Uleczenie|Powrót Sił|Odwrócenie', 'Pętla Czasowa|Fala Paradoksu|Burza Zegarów|Krąg Eonów|Zatrzymanie Epok'),
    'Iluzjonista': ('Pęknięcie Iluzji|Uderzenie Mirażu|Cios Odbicia|Zmylenie|Promień Zwierciadła', 'Unik|Zniknięcie|Osłona Pozoru|Odbicie|Zasłona', 'Hipnoza|Skupienie|Zasłonięcie|Przemiana|Złudzenie', 'Ukojenie|Odpoczynek|Regeneracja|Ocalenie|Złudna Odnowa', 'Burza Luster|Krąg Zwierciadeł|Nawałnica Odbić|Pęknięcie Wielu Luster|Fala Miraży'),
    'Bard': ('Akord|Dźwięk|Cios Rytmu|Ton|Dysonans', 'Zasłona Dźwięku|Osłona Harmonii|Kontrapunkt|Ochrona|Wytłumienie', 'Pieśń|Refren|Hymn|Melodia|Ballada', 'Ukojenie|Kołysanka|Leczący Akord|Odnowa|Harmonia', 'Symfonia|Kaskada Dźwięków|Chór|Burza Nut|Fala Muzyki'),
    'Szaman': ('Błysk|Uderzenie Ducha|Znak Plemienia|Piorun|Pazur Ducha', 'Osłona Totemu|Bariera Duchów|Zasłona Dymu|Opieka Przodków|Ochrona', 'Zew Przodków|Przebudzenie|Pieśń Obrzędu|Trans|Rytuał', 'Uzdrowienie|Błogosławieństwo Ducha|Odnowa|Leczenie|Łaska Totemu', 'Burza Piorunów|Krąg Duchów|Gniew Totemów|Fala Przodków|Deszcz Błyskawic'),
}

_SPECIAL_ACTIONS = {
    ('Kapłan','group_heal'): 'Modlitwa Drużyny|Wspólna Łaska|Uzdrowienie Wspólnoty|Zbiorowe Ocalenie|Błogosławieństwo Drużyny',
    ('Berserker','drain'): 'Żniwo Krwi|Wydarcie Życia|Rozszarpanie Żył|Wchłonięcie Sił|Rana Wysysająca',
    ('Nekromanta','drain'): 'Wysysanie Życia|Żniwo Umarłych|Dotyk Kostuchy|Kradzież Duszy|Zabranie Tchnienia',
    ('Czarownik','drain'): 'Danina Krwi|Wyssanie Mocy|Pobór Duszy|Rytuał Wydarcia|Żer Otchłani',
    ('Samuraj','execute'): 'Ostatnie Cięcie|Egzekucja Katany|Wyrok Mistrza|Kończące Pchnięcie|Rozcięcie Losu',
    ('Gladiator','execute'): 'Dobijający Gladius|Wyrok Areny|Zwycięski Finisz|Egzekucja Czempiona|Śmiertelne Pchnięcie',
}

_EXTRA_ACTIONS = {
    ('Szaman','aoe_damage'): 'Krąg Żywiołów|Sztorm Przodków',
    ('Paladyn','guard'): 'Osłona Sanktuarium|Mur Wiary',
    ('Bard','boost'): 'Pobudka|Zagrzewająca Ballada',
}

_KIND_GROUP = {
    'damage': 0, 'drain': 0, 'execute': 0,
    'guard': 1, 'evade': 1,
    'boost': 2, 'passive': 2, 'utility': 2,
    'heal': 3, 'group_heal': 3, 'regen': 3,
    'aoe_damage': 4,
}

# The earliest signature rows were hand-authored but a few displayed the
# *wrong mechanical action*: e.g. a healing Paladin spell called a shield.
# Keep the same ID, effect and original full name as a command alias.
_SIGNATURE_REFINEMENTS = {
    'v900_paladyn_10': 'Dotyk Świętego Ukojenia',
    'v900_samuraj_20': 'Ominięcie Tysiąca Ostrzy',
    'v900_korsarz_20': 'Duch Sztormowej Załogi',
    'v900_gladiator_20': 'Zew Trybun Areny',
    'v900_chronomanta_10': 'Cięcie Wskazówek',
    'v900_iluzjonista_10': 'Rozbite Zwierciadło',
    'v900_bard_10': 'Pieśń Ukojenia',
    'v900_szaman_10': 'Totem Ukojenia',
}

def _canonical(value):
    return re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower()).strip()

def _generated(s):
    sid = str(s.get('id',''))
    if sid.startswith('v0922_'):
        return True
    if sid.startswith('v0310_'):
        return ':' in str(s.get('name',''))
    if sid.startswith('v900_'):
        return ':' in str(s.get('name',''))
    return False


def install(class_skills):
    """Rename generated rows only; all authored spells and IDs stay untouched."""
    assert set(class_skills) == set(_MOTIFS) == set(_ACTIONS), '22 authored class profiles required'
    old_names = {_canonical(s['name']) for rows in class_skills.values() for s in rows}
    new_names = set()
    new_count = 0
    by_class = {}
    for cl, rows in class_skills.items():
        motives = _MOTIFS[cl].split('|')
        action_sets = [part.split('|') for part in _ACTIONS[cl]]
        assert len(motives) == 18 and len(action_sets) == 5 and all(len(x)==5 for x in action_sets), cl
        kind_counters = defaultdict(int)
        renamed = 0
        for row in rows:
            if not _generated(row):
                if row.get('id') in _SIGNATURE_REFINEMENTS:
                    old_signature = str(row['name'])
                    candidate_signature = _SIGNATURE_REFINEMENTS[row['id']]
                    current_aliases = list(row.get('aliases') or ())
                    for alias in (old_signature,candidate_signature):
                        if _canonical(alias) not in {_canonical(v) for v in current_aliases}:
                            current_aliases.append(alias)
                    row['aliases'] = current_aliases
                    row['name'] = candidate_signature
                    row['pre_v1110_skill_name'] = old_signature
                    if old_signature in str(row.get('desc') or ''):
                        row['desc'] = str(row['desc']).replace(old_signature,candidate_signature)
                    renamed += 1
                    new_count += 1
                new_names.add(_canonical(row['name']))
                continue
            kind = row['kind']
            family = _KIND_GROUP.get(kind, 0)
            n = kind_counters[kind]
            kind_counters[kind] += 1
            old = str(row['name'])
            # 18 fully authored class themes x 5 type-appropriate skill actions.
            # 90 different name combinations for every mechanical type.
            # Resolve rare collisions with another authored combination, never numbers.
            action_pool = (_SPECIAL_ACTIONS[(cl,kind)].split('|') if (cl,kind) in _SPECIAL_ACTIONS else list(action_sets[family]))
            action_pool.extend(_EXTRA_ACTIONS.get((cl,kind), '').split('|') if (cl,kind) in _EXTRA_ACTIONS else [])
            pool_size = len(motives) * len(action_pool)
            for candidate_idx in range(pool_size):
                offset = (n + candidate_idx) % pool_size
                action = action_pool[(offset*7 + offset//18) % len(action_pool)]
                motif = motives[offset%18]
                candidate = f'{action} {motif}'
                key = _canonical(candidate)
                # Reject clumsy phrases such as 'Pieśń Pieśni', 'Łaska Łaski',
                # 'Błysk Totemu Totemu' or 'Tarcza Świtu Łaski Świtu'.
                action_roots = {w[:5] for w in _canonical(action).split() if len(w) >= 5}
                motif_roots = {w[:5] for w in _canonical(motif).split() if len(w) >= 5}
                if action_roots & motif_roots:
                    continue
                if key not in new_names and key not in old_names:
                    break
            else:
                raise AssertionError(f'{cl}/{kind}: authored name pool exhausted')
            aliases = [str(v) for v in (row.get('aliases') or ())]
            # Keep pre-existing aliases *including* legacy levels and old name.
            keys = {_canonical(v) for v in aliases}
            if _canonical(old) not in keys:
                aliases.append(old)
            if _canonical(candidate) not in keys:
                aliases.append(candidate)
            row['name'] = candidate
            row['aliases'] = aliases
            description = str(row.get('desc') or '')
            if old in description:
                row['desc'] = description.replace(old, candidate)
            new_words = [_canonical(word) for word in candidate.split()]
            previous_tags = list(row.get('natural_tags') or [])
            row['natural_tags'] = list(dict.fromkeys(previous_tags + [w for w in new_words if w]))
            row['pre_v1110_skill_name'] = old
            new_names.add(key)
            renamed += 1
            new_count += 1
        by_class[cl] = renamed
    assert len(new_names) == sum(map(len, class_skills.values())), 'global skill names must stay unique'
    return {'classes':len(class_skills),'renamed':new_count,'by_class':by_class}

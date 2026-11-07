# -*- coding: utf-8 -*-
"""25 kolejnych krain v107: unikalne biomy, potwory, bossowie i surowce.

Każdy rekord: identyfikator, nazwa, opis, dwaj bossowie, dziesięć nazw
potworów, cztery regionalne surowce. Pięć rozdziałów po pięć krain.
Rejestr nie wprowadza sam żadnych zmian do świata ani danych graczy.
"""
from __future__ import annotations


def _entry(slug, name, lore, boss_a, boss_b, monsters, materials):
    enemies = tuple(x.strip() for x in monsters.split('|'))
    loot = tuple(x.strip() for x in materials.split('|'))
    assert len(enemies) == 10 and len(set(enemies)) == 10, (slug, enemies)
    assert len(loot) == 4 and len(set(loot)) == 4, slug
    return slug, name, lore, boss_a, boss_b, enemies, loot

CHAPTER_TWO = (
    _entry('mechaniczne_korzenie','Dolina Mechanicznych Korzeni',
        'Żywe stalowe korzenie oplatają pogrzebane maszyny, które śnią o dawnych kowalach.',
        'Pierwszy Korzeń Stali','Arbiter Mechanicznego Lasu',
        'Żelazny Pąk|Korzeniowy Świdrowiec|Sadzonka z Trybami|Dolinański Zgrzytacz|Wędrowna Kosiarka|Mechaniczny Jeż|Miedziany Badyl|Opancerzony Korzeń|Rdzawy Pająk|Strażnik Obwodów',
        'Sprężyna Korzenia|Żywa Miedź|Rdzawy Sok|Zębatka Sadzonki'),
    _entry('kuznia_serc','Kuźnia Serc',
        'Pod ziemią kuźnicy budzą młoty, a każda iskra ma własny puls.',
        'Płatnerz Żywego Metalu','Wielki Kowal Serc',
        'Gorący Nitownik|Pieśniarz Kowadła|Przepalony Golem|Krwiostopowy Cień|Mistrz Łańcucha|Hartownik Płomienia|Hutniczy Duch|Kroczący Piec|Tytanowy Wyrzutnik|Łowca Iskier',
        'Żużel Serca|Niebieski Węgiel|Pręt Żywej Stali|Młotkowy Kryształ'),
    _entry('szklane_burze','Pustynia Szklanych Burz',
        'Pustynny wiatr niesie ostrza szkła, które przechowują echo dawnych bitew.',
        'Sędzia Lustrzanego Pyłu','Szklisty Huragan',
        'Wydmowy Tnący Wiatr|Szklany Skorpion|Odbity Wędrowiec|Kwarcowy Żmij|Pustynny Strzelec|Kryształowy Żuk|Płonący Miraż|Złodziej Zwierciadeł|Piaskowy Golem|Nocny Rozłupnik',
        'Szkło Burzowe|Piasek Odbić|Ząb Kwarcu|Kryształ Wydmy'),
    _entry('nekropolia_automatow','Nekropolia Automatów',
        'Niedokończone automaty powstają z kamiennych grobów i szukają swoich twórców.',
        'Strażnik Zapomnianego Prototypu','Matka Martwych Maszyn',
        'Trupi Automat|Zegarmistrz Cmentarza|Ciszy Żniwiarz|Rozbity Konstruktor|Mechaniczny Nekromanta|Grobowy Składacz|Sarkofagowy Nadzorca|Smolny Robotnik|Pielgrzym Żelaza|Zardzewiały Egzekutor',
        'Stara Cewka|Rdzeń Żałoby|Cmentarny Olej|Płyta Zmartwychwstania'),
    _entry('cytadela_rdzenia','Cytadela Rdzenia',
        'W sercu twierdzy bije reaktor napędzany wspomnieniami poległych strażników.',
        'Komendant Reaktora','Władca Ostatniego Rdzenia',
        'Żołnierz Modułu|Laserowy Obrońca|Czujnikowy Łowca|Pancerny Stabilizator|Operator Sygnału|Pilot Cewki|Sieciowy Kat|Kryptotechnik|Strażnik Baterii|Reaktorowy Najeźdźca',
        'Czysty Rdzeń|Płytka Sygnału|Iskra Reaktora|Bateria Cytadeli'),
)

CHAPTER_THREE = (
    _entry('archipelag_zorzy','Archipelag Zorzy',
        'Nad wyspami płyną wstęgi zorzy, które zsyłają blask i zakłócają pamięć.',
        'Syrena Zielonej Zorzy','Gwiezdny Admirał Wysp',
        'Świetlisty Korsarz|Zorzański Mewnik|Muszlowy Mag|Strażnik Rafałów|Rybak Północy|Błyskawiczny Krab|Szmaragdowy Nawigator|Morski Zaklinacz|Duch Bojowej Galery|Latarnik Zorzy',
        'Muszla Zorzy|Błękitny Koral|Sól Świateł|Pióro Morskiej Gwiazdy'),
    _entry('morze_wspomnien','Morze Wspomnień',
        'Każda fala zwraca zapomnianą chwilę, a wraki wypowiadają imiona żeglarzy.',
        'Poławiacz Zapomnianych Dni','Władczyni Głębokiej Pamięci',
        'Tonący Skryba|Widmowy Sternik|Fala Dzieciństwa|Pamiętliwa Ośmiornica|Głęboki Śpiewak|Perłowy Strażnik|Nurek Bez Cienia|Utracony Latarnik|Tropiciel Wraków|Syrena Żalu',
        'Perła Historii|Wodorost Pamięci|Woskowa Latarnia|Kropla Zapomnienia'),
    _entry('gory_eteru','Góry Eteru',
        'Szlaki górskie unoszą się w powietrzu, a kryształowe echa burzą magię.',
        'Sędzia Eterycznych Szczytów','Archont Białej Przepaści',
        'Eteryczny Koziorożec|Chmurowy Drwal|Sęp Kryształowych Skał|Niebieski Wspinacz|Powietrzny Warg|Błędny Geomanta|Orzeł Magii|Górski Eterowiec|Zakuty Żywiołak|Strażnik Przełęczy',
        'Kwarc Eteru|Pióro Chmury|Śnieg Zawieszenia|Kamień Szczytu'),
    _entry('ogrody_bez_czasu','Ogrody Bez Czasu',
        'Kwiaty kwitną wczoraj i jutro jednocześnie, chronione przez strażników sezonów.',
        'Ogrodniczka Utraconego Lata','Władca Zatrzymanej Wiosny',
        'Zegarowy Motyl|Wiosenna Driada|Jesienny Szerszeń|Zimowy Ogrodnik|Wędrowny Pąk|Pszczoła Stu Pór|Kwitnący Obrońca|Pokrzywowy Czasownik|Zmienny Trzmiel|Kronikarz Nasienia',
        'Nasiono Czasu|Płatek Wieczności|Żywica Sezonów|Liść Wczoraj'),
    _entry('glebia_lustrzana','Głębia Lustrzana',
        'W podwodnych zwierciadłach odbicia walczą z własnymi pierwowzorami.',
        'Strażniczka Odwróconej Fali','Monarcha Tysiąca Odbić',
        'Lustrzany Rozbitek|Odbity Płaszczka|Szklany Nur|Koralowy Sobowtór|Zmienny Krakenik|Lśniący Łowca|Podwodne Zwierciadło|Poławiacz Cieni|Świetlista Meduza|Zwierciadlany Strażnik',
        'Odłamek Zwierciadła|Koral Odbicia|Sól Lustra|Woda Drugiego Ja'),
)

CHAPTER_FOUR = (
    _entry('pekniete_zegary','Twierdza Pękniętych Zegarów',
        'Mechanizmy czasu wyrzucają w świat sekundy, których nikt jeszcze nie przeżył.',
        'Rotmistrz Wstrzymanej Minuty','Władca Ostatniej Sekundy',
        'Zegarowy Kusznik|Pęknięty Wahadłowy|Strażnik Dzwonu|Żołnierz Wskazówki|Przesunięty Rycerz|Mechanik Godzin|Cień Jutra|Sprężynowy Żniwiarz|Kapitan Chronometrów|Strażnik Kalendarza',
        'Pęknięta Sprężyna|Srebro Sekundy|Pył Wahadła|Zegarowy Ząb'),
    _entry('mosty_konstelacji','Mosty Konstelacji',
        'Kamienne mosty spinają gwiazdozbiory i rozciągają się nad próżnią.',
        'Gwiezdna Strażniczka Mostów','Mistrz Rozpiętych Niebios',
        'Astralny Łucznik|Mostowy Strażnik|Posłaniec Oriona|Tkacz Gwiazdozbiorów|Wędrowiec Północy|Niebiański Sygnalista|Złota Kometa|Kapłan Plejad|Żelazny Meteoroid|Skoczek Próżni',
        'Pióro Konstelacji|Iskra Plejad|Kamień Gwiazdy|Nić Niebios'),
    _entry('krater_siedmiu','Krater Siedmiu Księżyców',
        'Siedem księżycowych odłamków świeci w kraterze, każdy własnym kolorem.',
        'Strażnik Siódmego Księżyca','Lunarny Tyran Krateru',
        'Srebrny Kraterowiec|Księżycowa Harpia|Błękitny Żuk Skał|Czerwony Meteor|Lunarny Nekromanta|Szary Odkrywca|Złoty Pielgrzym|Fioletowy Lunatyk|Księżycowy Bazyliszek|Strażnik Fazy',
        'Srebro Krateru|Pył Siedmiu Barw|Skorupa Księżyca|Gwiezdna Lawa'),
    _entry('rozproszona_dusza','Królestwo Rozproszonej Duszy',
        'Dusze dawnych królów wędrują po pustych dziedzińcach rozproszone na tysiąc wspomnień.',
        'Kanclerz Zaginionych Imion','Król Rozszczepionych Dusz',
        'Pusty Dworzanin|Rozsypany Strażnik|Widmo Koronacji|Błędny Podkomorzy|Skryba Duszy|Rycerz Bez Odbicia|Złamany Herold|Łowca Wspomnień|Płacząca Dama|Strażnik Pieczęci',
        'Proch Duszy|Koronny Kryształ|Pieczęć Imienia|Srebrny Wspominek'),
    _entry('twierdza_echa','Twierdza Echa',
        'Nieznany dowódca powtarza rozkazy głosami swoich poległych żołnierzy.',
        'Marszałek Krzyczących Murów','Książę Ostatniego Echa',
        'Szeptający Halabardnik|Rozdwojony Kusznik|Echo Komendanta|Dźwiękowy Szermierz|Wartownik Milczenia|Burzowy Trębacz|Kamienny Akustyk|Niedoszły Bohater|Strażnik Zewu|Widmowy Tarczownik',
        'Kamień Echa|Struna Twierdzy|Głos Srebrny|Odłamek Akustyczny'),
)

CHAPTER_FIVE = (
    _entry('dolina_szeptow','Dolina Szeptów Pustki',
        'Niewypowiedziane słowa tworzą w dolinie własne istoty i własne sekrety.',
        'Pasterka Nienazwanych Szeptów','Pradawne Milczenie Doliny',
        'Szept Bez Imienia|Cichy Odkrywca|Pustkowy Skrzat|Bezgłośny Łowca|Duch Oddechu|Szeptacz Głębi|Strażnik Głuchoty|Szary Milczek|Pusty Skryba|Eteryczny Podsłuchiwacz',
        'Zapisany Szept|Kropla Ciszy|Puste Pióro|Oddech Doliny'),
    _entry('niebianskie_kopalnie','Niebiańskie Kopalnie',
        'Górnicy drążą rudę gwiazd w tunelach zawieszonych wysoko nad ziemią.',
        'Nadzorca Gwiezdnego Szybu','Tytan Niebiańskiej Rudy',
        'Astralny Górnik|Świetlista Koparka|Rudny Żywiołak|Cienisty Wiertnik|Górniczy Upiór|Magnetyczny Szczur|Kryształowy Drążnik|Szybowy Strażnik|Piaskowy Przesiewacz|Gwiezdny Ładowacz',
        'Niebiańska Ruda|Skała Komety|Kryształ Szybu|Pył Kopalni'),
    _entry('zamarzniete_burze','Tron Zamarzniętych Burz',
        'Mróz zatrzymał błyskawice w lodzie, a tron włada czasem między grzmotami.',
        'Hetmanka Błękitnego Mrozu','Władca Uwięzionych Grzmotów',
        'Lodowy Błysk|Gromowy Wilk|Śnieżny Mag|Zamarznięty Wyładowacz|Mroźna Harpia|Burzowy Niedźwiedź|Strażnik Szronu|Błękitny Drakonik|Oszroniony Halabardnik|Grzmotnik Lodowy',
        'Lód Burzy|Iskra Szronu|Fulguryt Błękitu|Zimny Grzmot'),
    _entry('rubiez_pradawnych','Rubież Pradawnych',
        'Na rubieży czuwają istoty starsze niż pamięć każdej znanej krainy.',
        'Pierwszy Strażnik Rubieży','Pradawna Matka Kamieni',
        'Wiekowy Wędrowiec|Pierwotny Rogacz|Kamienna Wyrocznia|Pradawny Ptak|Plemienny Strażnik|Runiczny Tur|Mówiący Menhir|Pierwszy Wilk|Ziemny Przodek|Kronikarz Przedświtu',
        'Odłamek Pradawny|Kość Rubieży|Korzeń Początku|Kamień Przedświtu'),
    _entry('labirynt_woli','Labirynt Woli',
        'Drogi zmieniają kierunek pod naporem myśli, ale każda decyzja ma konsekwencje.',
        'Strażniczka Zmiennej Drogi','Minotaur Nieugiętej Woli',
        'Próbnik Myśli|Woliciel Cienia|Labiryntowy Łowca|Wędrowiec Rozdroża|Strażnik Wyboru|Kłamliwy Przewodnik|Widmo Pragnienia|Kamienny Minotaur|Zagubiony Kartograf|Kusiciel Korytarzy',
        'Nić Wyboru|Fragment Mapy|Kamień Pragnienia|Znak Woli'),
)

CHAPTER_SIX = (
    _entry('pieczec_poczatku','Pieczęć Początku',
        'Na prastarej pieczęci zapisano pierwsze prawo, którego Chaos próbuje się pozbyć.',
        'Kapłanka Pierwszej Litery','Sędzia Pradawnej Pieczęci',
        'Strażnik Inicjału|Skryba Przedświata|Runiczny Początek|Golem Słowa|Pielgrzym Prawości|Cień Alfabetu|Złoty Interpretator|Szept Księgi|Egzekutor Znaku|Pierwotny Czytelnik',
        'Litera Początku|Wosk Pieczęci|Atrament Kreacji|Złota Runa'),
    _entry('bezkresna_kuznia','Bezkresna Kuźnia',
        'Kowadła kuźni płoną bez przerwy, wykuwając z pamięci materię przyszłości.',
        'Niezmordowany Mistrz Kuźni','Cesarz Niewygasłego Ognia',
        'Płonący Hutnik|Żywe Kowadło|Krawędziowy Tytan|Mistrz Stopów|Ognisty Mechanik|Przekuty Rycerz|Zbrojny Topielnik|Strażnik Żaru|Bezsenna Iskra|Huczny Młotnik',
        'Metal Wieczności|Żar Nieskończony|Kowadlany Pył|Stop Stworzenia'),
    _entry('miasto_snow','Miasto Ostatnich Snów',
        'Śniący mieszkańcy zapomnieli o przebudzeniu, a ich sny budują całe dzielnice.',
        'Tkaczka Najgłębszego Snu','Król Bezsennej Nocy',
        'Strażnik Kołysanki|Senny Poeta|Widmo Marzenia|Nocny Bibliotekarz|Łowca Koszmarów|Śniący Zegarmistrz|Pusty Marzyciel|Zjawisko Uliczne|Szeptacz Poduszki|Lunatyczny Żołnierz',
        'Nić Snu|Pył Koszmaru|Kryształ Marzenia|Atrament Nocy'),
    _entry('prog_chaosu','Próg Chaosu',
        'Za progiem przestrzeń rozpada się na warstwy, a drogę wskazują tylko dawne przysięgi.',
        'Strażnik Ostatniego Kroku','Herold Otwartego Chaosu',
        'Wartownik Granicy|Rozdartymistrz|Ruinny Geomanta|Ostatni Pielgrzym|Cień Bramny|Zaginiony Posłaniec|Żniwiarz Przejść|Zakuty Wędrowiec|Łamacz Przestrzeni|Tropiciel Otchłani',
        'Klucz Przejścia|Pył Rozdarcia|Zawias Przestrzeni|Przysięga Bramy'),
    _entry('serce_wiecznosci','Serce Wieczności',
        'W źródle chaosu pulsuje moc wszystkich epok; każda fala zmienia kształt świata.',
        'Obrończyni Serca Wieków','Awatar Wiecznego Chaosu',
        'Strażnik Pulsu|Eteryczny Władca|Rdzeń Bezkresu|Pradawna Iskra|Mistrz Rozdarć|Nienazwany Mag|Wędrowiec Eonów|Żołnierz Wieczności|Kronikarz Końca|Żywy Paradygmat',
        'Kropla Wieczności|Rdzeń Eonu|Pył Chaosu|Świetlista Przysięga'),
)

CHAPTERS = (CHAPTER_TWO, CHAPTER_THREE, CHAPTER_FOUR, CHAPTER_FIVE, CHAPTER_SIX)
ALL_NEXT = tuple(row for chapter in CHAPTERS for row in chapter)
assert len(CHAPTERS) == 5 and all(len(c) == 5 for c in CHAPTERS)
assert len(ALL_NEXT) == 25
assert len({row[0] for row in ALL_NEXT}) == len({row[1] for row in ALL_NEXT}) == 25
assert len({mob for row in ALL_NEXT for mob in row[5]}) == 250

"""Historyczna pomoc Soulbound v4.00.5: progression."""

def make_topics():
    return {'kup_narzedzia': ['Narzędzia można kupować krótkimi nazwami bez polskich znaków.',
                   'Przykłady: kup wedka, kup kilof, kup pila, kup mlot, kup noz, kup sierp, kup mozdzierz.',
                   'Narzędzie nadal trzeba kupić u właściwego sprzedawcy. Gra poda właściwą lokację, jeśli '
                   'jesteś w złym miejscu.',
                   'Kupienie narzędzia nie daje mu XP ani levelu.'],
 'xp_narzedzi': ['XP dostaje wyłącznie narzędzie faktycznie użyte w danej akcji.',
                 'v1.13.42: Tool XP nie jest już płaski. Im wyższy poziom materiału, receptury, EQ do '
                 'salvage albo innej pracy, tym większy realny XP narzędzia.',
                 'Młot Rzemieślniczy ma dodatkowy mnożnik jakości x1.35; salvage, hartowanie, ulepszanie i '
                 'kucie rozwijają Młot zależnie od poziomu wykonywanej pracy.',
                 'Łowienie rozwija Wędkarstwo oraz Wędkę.',
                 'Kopanie rozwija Górnictwo oraz Kilof.',
                 'Drwalstwo i obróbka desek rozwijają Drwalstwo oraz Piłę.',
                 'Kucie i przetapianie rozwijają Kowalstwo oraz Młot Rzemieślniczy.',
                 'Gotowanie rozwija Gotowanie oraz Nóż Kucharski.',
                 'Zielarstwo rozwija Zielarstwo oraz Sierp Zielarski.',
                 'Alchemia rozwija Alchemię oraz Moździerz Alchemiczny.',
                 'Jubilerstwo rozwija Jubilerstwo oraz Szczypce Jubilerskie.',
                 'Pozostałe narzędzia nie dostają XP, użyć ani leveli od tej akcji.'],
 'endgame_profesje': ['Narzędzia 1-400 odblokowują coraz lepsze surowce i zwiększają rare/quality oraz bonus '
                      'urobku; profesje 1-400 skracają czas i blokują receptury/zlecenia.',
                      'Wędka odblokowuje nowe ryby endgame; część zależy od typu łowiska: rzeka, jezioro, '
                      'morze albo ocean.',
                      'Kilof odblokowuje: Ruda Kobaltu 100, Kamień Runiczny 120, Smocza Stal 140, Ruda '
                      'Astralna 160, Ruda Pustki 180 i Eternium 200.',
                      'Piła w Głębi Gaju odblokowuje nowe drewna na levelach 100, 120, 140, 160, 180 i 200.',
                      'Sierp w Głębi Gaju odblokowuje nowe zioła na levelach 100, 120, 140, 160, 180 i 200.',
                      'Kowalstwo, Gotowanie, Alchemia i Jubilerstwo mają receptury progresji wymagające '
                      'odpowiedniego levelu profesji oraz Tieru właściwego narzędzia.',
                      'Receptury są twardo zablokowane jednocześnie levelem profesji i wymaganym Tierem '
                      'narzędzia; sam składnik albo tylko jedna z tych osi nie wystarcza.',
                      'Wpisz receptury, receptury craft, receptury cook albo receptury alchemia, aby '
                      'usłyszeć wymagany level.'],
 'logowanie': ['Po każdym zalogowaniu postać rozpoczyna sesję w Świątyni Odrodzenia.',
               'Nie ma znaczenia, gdzie postać wylogowała się poprzednio.',
               'Zapisana lokacja z poprzedniej sesji nie jest miejscem startowym następnego logowania.',
               'Po wejściu do świata HP i Mana są ustawiane jak dotychczas przy logowaniu.',
               'Portale Krypty, questy, ekwipunek i cała trwała progresja pozostają zapisane.'],
 'soul_level_hp': ['Każdy awans Soul Level Broni Duszy natychmiast odnawia postać do 100 procent HP.',
                   'Działa niezależnie od źródła Soul XP, między innymi z przeciwników oraz Eliksiru Duszy.',
                   'Jeżeli Soul XP nie wbije nowego Soul Levelu, HP nie jest odnawiane.',
                   'Odnowienie dotyczy tylko HP. Mana nie jest automatycznie odnawiana.',
                   'Soul Level ma zakres 1-400.'],
 'rozwoj_statystyk': ['Statystyki rosną automatycznie przez sześć niezależnych liczników EXP; nie ma '
                      'ręcznego rozdawania punktów ani levelu postaci.',
                      'Każda z sześciu statystyk ma osobną krzywą EXP, bez limitu wartości; od 50 wymaga '
                      'dodatkowo stopniowo więcej EXP. Nagrody za walki pozostają takie same.',
                      'Pełny próg zwiększa tylko tę konkretną statystykę o 1; pozostałe zachowują własny EXP '
                      'i własne progi.',
                      'Pojedynczy mob ma limit EXP każdej statystyki zależny od rangi, więc boss nie '
                      'przeskakuje całej progresji jednym zabiciem.',
                      'Bonus rasy Człowiek do Postępu Rozwoju nadal działa.'],
 'uzywanie_umiejetnosci': ['Umiejętności można używać dotychczasową komendą skill <nazwa lub numer> [cel].',
                           'Działa też umiejętność <nazwa> [cel], zdolność <nazwa> [cel] oraz cast <nazwa> '
                           '[cel].',
                           'Dodano składnię użyj umiejętność <nazwa> [cel].',
                           'Angielska wersja to use skill <name> [target].',
                           'Jeżeli po use/użyj podasz bezpośrednio rozpoznawalną nazwę skilla, gra także '
                           'spróbuje go użyć.',
                           'Ofensywne umiejętności nadal rozpoczynają walkę tylko na wyraźną akcję gracza.',
                           'Cooldown, Mana, Skill Level i zdobywanie Skill XP działają dokładnie tak jak '
                           'przy komendzie skill.'],
 'soul200': ['Broń Duszy ma Soul Level 1-400.',
             'Soul XP używa od v0.8.64 płynnej krzywej +25 procent mnożnika co pełny blok 10 leveli; wpisz '
             'help soulxp.',
             'Tier 4 wymaga próby od Soul Level 25.',
             'Tier 7 wymaga próby od Soul Level 60.',
             'Tier 13 odblokowuje się od Soul Level 120 po Próbie Elora na bossie piętra 120 Krypty.',
             'Tier 19 odblokowuje się od Soul Level 180 po Próbie Elora na bossie piętra 180 Krypty.',
             'Po Soul Level 100 Broń Duszy rozwija się dalej aż do 400.',
             'Soul Level nadal zwiększa bazową moc Broni Duszy.',
             'Nie ma levelu postaci.'],
 'narzedzia200': ['Wszystkie 8 narzędzi ma level 1-400 i 40 Tierów.',
                  'Wędka, Kilof, Piła, Młot Rzemieślniczy, Nóż Kucharski, Sierp Zielarski, Moździerz '
                  'Alchemiczny i Szczypce Jubilerskie rozwijają się do 400.',
                  'Tier 1 obejmuje level 1-9; kolejne Tiery zaczynają się na 10, 20, 30 i dalej co 10 aż do '
                  '180; Tier 20 jest na levelu 200.',
                  'Przykłady bonusu: Tier 1 = 0 procent, Tier 10 od levelu 90 = 18 procent, Tier 11 od 100 = '
                  '20 procent, Tier 19 od 180 = 37 procent, Tier 20 na 200 = 40 procent.',
                  'Każdy Tier ma osobną nazwę dla każdego rodzaju narzędzia.',
                  'tools, tiers oraz bezpośrednie komendy narzędzi pokazują aktualny Tier i następny próg.'],
 'krytyki': ['Trafienia krytyczne zależą od efektywnej Zręczności, czyli także od bonusów ekwipunku. Od '
             'v0.8.63 wysokie wartości mają malejący przyrost, a limit pozostaje 35 procent.',
             'Przy Zręczności 10 bazowa szansa na krytyk wynosi 5 procent.',
             'Każdy punkt Zręczności ponad 10 dodaje 0,5 punktu procentowego szansy.',
             'Zręczność poniżej 10 obniża szansę o 0,5 punktu procentowego za punkt.',
             'Minimalna szansa wynosi 1 procent, maksymalna 35 procent.',
             'Trafienie krytyczne zadaje 150 procent normalnych obrażeń.',
             'Krytyki działają dla zwykłego ataku i ofensywnych umiejętności klasowych.',
             'Mechaniki obronne bossów nadal mogą zredukować albo anulować krytyk.',
             'stats pokazuje aktualną szansę na krytyk i mnożnik.'],
 'respawn': ['Zwykłe moby odradzają się po 120 sekundach od śmierci.',
             'Bossowie Krypty i Herszt Bandytów odradzają się po 300 sekundach.',
             'Żywy Manekin treningowy odradza się po 60 sekundach.',
             'Boss progu blokuje przejście tylko do pierwszego pokonania przez daną postać. Po respawnie '
             'jest opcjonalny.'],
 'bossowie': ['Bossowie działają w walce czasu rzeczywistego i wykonują ataki według własnego timera.',
              'Bossowie i zwykłe moby nie są agresywne; nie zaczynają walki sami.',
              'Kościany Egzekutor: co trzeci kontratak używa Kościanego Miażdżenia.',
              'Krwawy Kurator: co trzeci kontratak używa Krwawego Drenażu i leczy się częścią zadanych '
              'obrażeń.',
              'Rycerz Grobowca: co trzecie trafienie gracza redukuje Tarczą Grobowca o połowę.',
              'Wiedźma Popiołu: co trzeci kontratak używa Klątwy Popiołu, która omija połowę obrony '
              'magicznej.',
              'Pan Katakumb: co czwarty kontratak używa Echa Katakumb.',
              'Widmowy Tytan: naprzemiennie zmienia kontratak fizyczny i magiczny.',
              'Nekromantyczny Kolos: co czwarty kontratak regeneruje 7 procent maksymalnego HP.',
              'Arcyupiór Otchłani: ma 25 procent szansy na eteryczny unik przeciw trafieniu gracza.',
              'Król Kości: poniżej 50 procent HP zadaje 50 procent więcej obrażeń.',
              'Władca Stu Pięter: poniżej połowy HP wchodzi w drugą fazę; co trzeci kontratak używa '
              'Załamania Duszy, a co czwarte trafienie gracza osłabia Pieczęcią Stu Pięter.',
              'Strażnik Pękniętej Duszy, piętro 110: co trzeci kontratak używa Rozdarcia Duszy.',
              'Królowa Otchłannej Krypty, piętro 120: co czwarty kontratak używa Drenażu Otchłani i jest '
              'celem Próby Tier 4.',
              'Tytan Żelaznych Kości, piętro 130: co trzecie trafienie gracza jest silnie redukowane.',
              'Prorok Czarnego Płomienia, piętro 140: co trzeci kontratak omija połowę obrony magicznej.',
              'Władca Bezdennych Katakumb, piętro 150: co czwarty kontratak używa Bezdennego Echa.',
              'Astralny Żniwiarz, piętro 160: zmienia fizyczną i magiczną fazę.',
              'Kolos Pustki, piętro 170: regeneruje 8 procent HP co czwarty własny atak.',
              'Cesarz Upiorów, piętro 180: ma Widmowy Unik i jest celem Próby Tier 5.',
              'Strażnik Końca, piętro 190: poniżej połowy HP zadaje 60 procent więcej obrażeń.',
              'Władca Dwustu Pięter, piętro 200: druga faza, Bariera Końca i Załamanie Wieczności; głębiej '
              'Krypta trwa dalej proceduralnie.',
              'Ręcznie przygotowani bossowie Krypty 10-200 mają własne relikty. Bossowie powyżej 200 są '
              'proceduralni i zamiast nowej nieskończenie silnej linii EQ korzystają z najwyższego '
              'istniejącego Tieru 20.',
              'Herszt Bandytów przebywa w Namiocie Herszta, głęboko w Obozowiskach Bandytów. Co trzeci '
              'kontratak wykonuje Brutalną Kombinację.',
              'Herszt Bandytów może upuścić unikalny Sygnet Herszta Bandytów.',
              'Król Goblinów przebywa w Grocie Króla Goblinów, na końcu Jaskiń Goblinów, i co trzeci '
              'kontratak wykonuje Królewską Szarżę.',
              'Alfa Wilków Cienia pojawia się w Głębi Gaju i poniżej połowy HP wpada w Szał Cienia.',
              'Strażnik Ruin pojawia się przy Zrujnowanej Wieży i co czwarty kontratak używa Runicznego '
              'Wybuchu.',
              'Kryształowy Władca pojawia się w Kryształowej Komnacie; używa Kryształowego Promienia i '
              'Kryształowej Bariery.',
              'Każdy z nowych bossów świata ma własny unikalny przedmiot z 45 procent szansy.'],
 'loot_krypty': ['Ekwipunek z Krypty ma 5 rzadkości: Zwykły, Rzadki, Epicki, Legendarny i Mityczny.',
                 'Wyższa rzadkość daje większą obronę i mocniejszy losowy affix.',
                 'Losowe affixy to: Siła, Zręczność, Kondycja, Inteligencja, Siła Woli, HP albo Mana.',
                 'Zwykłe moby częściej dają Zwykły lub Rzadki loot.',
                 'Bossowie mają dużo lepszą szansę na Epicki, Legendarny i Mityczny loot.',
                 'Każdy element Krypty należy do Zestawu Krypty swojego Tieru 1-40; moc EQ zatrzymuje się na '
                 'progresji 400.',
                 'Dominujący set to Tier, którego masz założonych najwięcej części; przy remisie wygrywa '
                 'wyższy Tier.',
                 '2 części jednego setu: +10 procent maksymalnego HP i Many.',
                 '4 części jednego setu: dodatkowo +10 procent wszystkich zadawanych obrażeń.',
                 '6 części jednego setu: dodatkowo +15 procent obrony fizycznej i magicznej.',
                 'Komenda equipment pokazuje rarity, affix oraz aktywny bonus setu.',
                 'Komenda stats pokazuje statystyki bazowe, statystyki z wyposażeniem oraz bonusy setu.',
                 'Stare przedmioty Krypty pozostają działające i liczą się do odpowiedniego setu jako Zwykłe '
                 'bez affixu.'],
 'portale': ['Portal Krypty odblokowuje się po pokonaniu bossa co 10 pięter.',
             'Portale prowadzą co 10 pięter od 10 bez górnego limitu.',
             'Odblokowanie portalu zapisuje się trwale w SQLite.',
             'portal pokazuje wszystkie odblokowane cele.',
             'portal 30 przenosi z Sali Krypty lub Przedsionka Krypty bezpośrednio na piętro 30.',
             'Portal służy do szybkiego powrotu; pierwszy boss progu nadal wymaga pokonania, ale jego '
             'kolejne respawny są opcjonalne.',
             'Jeśli boss tego progu nigdy nie został jeszcze pokonany przez postać, żywy boss blokuje dalszą '
             'drogę.',
             'Po pierwszym zabiciu bossa przejście pozostaje odblokowane na stałe dla postaci, także po jego '
             'respawnie.',
             'Portalu nie można używać podczas walki.',
             'Stare komendy checkpoint nadal działają jako alias portalu dla zgodności.'],
 'krypta': ['Loot Krypty ma rarity, losowe affixy statystyk i bonusy setowe 2/4/6 części.',
            'Wpisz help loot_krypty, help rarity albo help sety po szczegóły.',
            'Krypta nie ma końcowego piętra; od v0.11.0 każde piętro od 1 wzwyż powstaje dynamicznie dopiero '
            'przy wejściu.',
            'Każde główne piętro jest dużą mapą: od v0.80.0 ma 30 pomieszczeń, pętle, boczne komnaty i dużo '
            'więcej przeciwników.',
            'Moby nie są agresywne i nie rozpoczynają walki same.',
            'Bossowie są co 10 pięter od 10 bez końca.',
            'Boss co 10 pięter blokuje zejście tylko przy pierwszym przejściu danej postaci.',
            'Po pierwszym pokonaniu bossa próg jest zapisany jako zaliczony na stałe dla postaci.',
            'Po respawnie boss może być farmiony, ale nie blokuje już dalszej drogi ani checkpointu.',
            'Pokonanie bossa odblokowuje trwały Portal Krypty do jego piętra.',
            'portal pokazuje odblokowane cele; portal 50 przenosi na piętro 50.',
            'Portal nie zalicza niepokonanego progu; po pierwszym zwycięstwie żywy respawn bossa jest już '
            'opcjonalny.',
            'Zwykły mob Krypty daje 100 + piętro*10 Soul XP.',
            'Boss Krypty daje 600 + piętro*20 Soul XP.',
            'Zwykły mob zostawia 1 element ekwipunku na ciele, boss 3.',
            'prowadz krypta prowadzi tylko przed wejście do Krypty. Piętra eksplorujesz samodzielnie; schody '
            'na kolejne piętro trzeba odnaleźć w głębi mapy.',
            'Co 10 pięter rośnie próg trudności i nagród XP; Tier EQ rośnie tylko do Tieru 40 / progresji '
            '400.'],
 'multiclass': ['Od v7.10.1 jedna postać ma jedną klasę główną, wybieraną przy tworzeniu postaci.',
                'multiclass oraz klasy pokazują klasę i jej Biegłość. Dodawanie, usuwanie i przełączanie '
                'klas jest wyłączone.',
                'Stare odblokowane klasy, ich Biegłość i skille pozostają w SQLite jako archiwum, ale nie '
                'zapewniają mocy ani EXP.',
                'Multi Cap EXP zalicza tylko Biegłość i skille klasy głównej; pozostałe poziomy profesji i '
                'narzędzi zachowują swoje zasady.',
                'Nie jest usuwana Broń Duszy ani wcześniejsze konta, postacie, osiągnięcia i przedmioty.'],
 'opisy': ['Komenda opis bez argumentu opisuje aktualną lokację.',
           'opis <przedmiot> pokazuje działanie, typ i ceny.',
           'opis <NPC> pokazuje rolę, lokację i powiązane zadanie.',
           'NPC-e pomocni, handlowi, zadaniowi i nauczyciele są pokojowi oraz chronieni przed walką.',
           'opis <przeciwnik> pokazuje HP, obrażenia, typ ataku i nagrody.',
           'opis <lokacja> pokazuje strefę, opis, wyjścia i specjalne funkcje.',
           'opis <zadanie>, opis <rasa>, opis <klasa>, opis <statystyka> i opis <waluta> także działają.'],
 'zmiany': ['changes, zmiany albo changelog pokazuje pełną historię wszystkich wersji.',
            'Najnowsza wersja jest na górze, starsze wersje są niżej.',
            'Historia jest czytana z CHANGELOG_PL.txt linia po linii dla NVDA.']}

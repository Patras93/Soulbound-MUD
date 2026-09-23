# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
ROOMS = {
    "square": {
        "zone": "Miasto Dusz", "name": "Plac Dusz",
        "desc": "Centralny plac osady. Nad kamienną fontanną płonie błękitny ogień.",
        "exits": {"north": "north_street", "south": "south_street", "east": "market", "west": "temple"},
    },
    "temple": {
        "zone": "Miasto Dusz", "name": "Świątynia Odrodzenia",
        "desc": "Spokojna świątynia. Polegli bohaterowie odzyskują tutaj świadomość.",
        "exits": {"east": "square", "north": "library", "down": "temple_basement"},
    },
    "temple_basement": {
        "zone": "Podziemia", "name": "Piwnica Świątyni",
        "desc": "Wilgotna piwnica pod Świątynią Odrodzenia. Między skrzyniami słychać piski szczurów.",
        "exits": {"up": "temple"},
    },
    "library": {
        "zone": "Miasto Dusz", "name": "Biblioteka Kronik",
        "desc": "Kamienne regały przechowują kroniki o duszach, rasach i dawnych wojnach.",
        "exits": {"south": "temple", "east": "guild_hall"},
    },
    "guild_hall": {
        "zone": "Gildia Dusz", "name": "Sala Główna Gildii",
        "desc": "Centralny hol Gildii Dusz. Korytarze prowadzą do wyspecjalizowanych sal nauczycieli.",
        "exits": {
            "west": "library",
            "south": "north_street",
            "north": "guild_martial_hall",
            "east": "guild_arcane_chamber",
            "up": "guild_shadow_gallery",
            "down": "guild_sanctuary",
        },
    },
    "guild_martial_hall": {
        "zone": "Gildia Dusz", "name": "Sala Oręża Gildii",
        "desc": "Ciężkie manekiny i stojaki treningowe służą Wojownikom i Berserkerom.",
        "exits": {"south": "guild_hall", "east": "guild_body_hall"},
    },
    "guild_body_hall": {
        "zone": "Gildia Dusz", "name": "Sala Dyscypliny Gildii",
        "desc": "Spokojna sala ćwiczeń ciała i obrony przeznaczona dla Mnichów i Strażników.",
        "exits": {"west": "guild_martial_hall"},
    },
    "guild_arcane_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Arkanów Gildii",
        "desc": "Runy świecą na ścianach. Tutaj Magowie i Psionicy ćwiczą kontrolę energii.",
        "exits": {"west": "guild_hall", "east": "guild_dark_chamber"},
    },
    "guild_dark_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Mrocznych Sztuk",
        "desc": "Zabezpieczona sala do nauki Nekromantów i Czarowników.",
        "exits": {"west": "guild_arcane_chamber"},
    },
    "guild_shadow_gallery": {
        "zone": "Gildia Dusz", "name": "Galeria Cieni Gildii",
        "desc": "Wąskie przejścia i cele treningowe służą Łotrzykom i Łowcom.",
        "exits": {"down": "guild_hall"},
    },
    "guild_sanctuary": {
        "zone": "Gildia Dusz", "name": "Sanktuarium Gildii",
        "desc": "Cicha sala natury i światła, w której szkolą się Kapłani i Druidzi.",
        "exits": {"up": "guild_hall"},
    },
    "north_street": {
        "zone": "Miasto Dusz", "name": "Ulica Północna",
        "desc": "Szeroka ulica prowadząca ku dziedzińcowi i północnej bramie.",
        "exits": {"south": "square", "north": "training", "east": "guard_hall", "west": "guild_hall"},
    },
    "guard_hall": {
        "zone": "Miasto Dusz", "name": "Strażnica Główna",
        "desc": (
            "Główna sala miejskiej straży. Na ścianach wiszą mapy szlaków, "
            "tablice patroli i meldunki z obu bram. Stąd można przejść do koszar, "
            "zbrojowni, komnaty dowódcy, wieży obserwacyjnej i cel strażnicy."
        ),
        "exits": {
            "west": "north_street", "east": "guard_barracks",
            "south": "guard_armory", "north": "guard_command",
            "up": "guard_watchtower", "down": "guard_cells",
        },
    },
    "guard_barracks": {
        "zone": "Miasto Dusz", "name": "Koszary Straży",
        "desc": (
            "Rzędy prycz, stojaki na płaszcze i tablice zmian wypełniają koszary. "
            "Strażnicy odpoczywają tutaj między patrolami północnej i południowej bramy."
        ),
        "exits": {"west": "guard_hall", "east": "guard_mess"},
    },
    "guard_mess": {
        "zone": "Miasto Dusz", "name": "Jadalnia Straży",
        "desc": (
            "Długi stół, kocioł i beczki z wodą zajmują niewielką jadalnię. "
            "Na ścianie wisi plan godzinnych zmian patroli miejskich."
        ),
        "exits": {"west": "guard_barracks"},
    },
    "guard_armory": {
        "zone": "Miasto Dusz", "name": "Zbrojownia Straży",
        "desc": (
            "Zamknięte stojaki przechowują włócznie, tarcze, kusze i zapasowe pancerze. "
            "Kwatermistrz prowadzi tu ewidencję wyposażenia miejskiej straży."
        ),
        "exits": {"north": "guard_hall"},
    },
    "guard_command": {
        "zone": "Miasto Dusz", "name": "Komnata Dowódcy Straży",
        "desc": (
            "Duży stół mapowy pokazuje Miasto Dusz, Stary Trakt, Gaj Szeptów i pogranicze. "
            "Tutaj planowane są patrole i akcje przeciw goblinom oraz bandytom."
        ),
        "exits": {"south": "guard_hall", "east": "guard_archive"},
    },
    "guard_archive": {
        "zone": "Miasto Dusz", "name": "Archiwum Straży",
        "desc": (
            "Regały są pełne raportów z patroli, listów gończych i starych map. "
            "Archiwistka straży porządkuje meldunki z obu bram."
        ),
        "exits": {"west": "guard_command"},
    },
    "guard_watchtower": {
        "zone": "Miasto Dusz", "name": "Wieża Obserwacyjna Straży",
        "desc": (
            "Z kamiennej wieży widać północną bramę, Stary Trakt i dachy miasta. "
            "Wartownicy przekazują stąd sygnały do posterunków przy bramach."
        ),
        "exits": {"down": "guard_hall"},
    },
    "guard_cells": {
        "zone": "Miasto Dusz", "name": "Cele Strażnicy",
        "desc": (
            "Kilka żelaznych cel służy do przetrzymywania schwytanych bandytów i szabrowników. "
            "Korytarz prowadzi do małego pokoju przesłuchań."
        ),
        "exits": {"up": "guard_hall", "east": "guard_interrogation"},
    },
    "guard_interrogation": {
        "zone": "Miasto Dusz", "name": "Pokój Przesłuchań",
        "desc": (
            "Surowy stół, dwa krzesła i półka z raportami tworzą niewielki pokój przesłuchań. "
            "Straż zbiera tu informacje o napadach, goblinach i ruchach bandytów."
        ),
        "exits": {"west": "guard_cells"},
    },
    "training": {
        "zone": "Miasto Dusz", "name": "Plac Treningowy",
        "desc": "Plac do ćwiczeń. Drewniane manekiny stoją obok północnej bramy.",
        "exits": {"south": "north_street", "north": "north_gate"},
    },
    "north_gate": {
        "zone": "Miasto Dusz", "name": "Północna Brama",
        "desc": (
            "Ciężka brama otwiera się na Stary Trakt. Dwóch miejskich strażników "
            "pełni tu stałą wartę i kontroluje podróżnych wracających z pogranicza."
        ),
        "exits": {"south": "training", "north": "old_road"},
    },
    "market": {
        "zone": "Miasto Dusz", "name": "Rynek",
        "desc": (
            "Kupcy sprzedają prowiant i podstawowe wyposażenie. Mikstury kupisz w Aptece Pod Srebrnym Liściem. "
            "Przy kamiennym kantorze działa Bank Dusz Bankiera Aldrena. "
            "Handlarz Skupu Radan kupuje łupy, trofea i niezałożone EQ, "
            "ale nie skupuje ryb, rud, drewna, ziół ani innych materiałów rzemieślniczych."
        ),
        "exits": {"west": "square", "east": "forge", "south": "inn", "north": "fish_market"},
    },
    "fish_market": {
        "zone": "Miasto Dusz", "name": "Targ Rybny",
        "desc": "Stragany pachną świeżą rybą i mokrymi sieciami. Tutaj sprzedaje się sprzęt wędkarski.",
        "exits": {"south": "market", "east": "harbor"},
    },
    "harbor": {
        "zone": "Miasto Dusz", "name": "Port Dusz",
        "desc": "Drewniane pomosty, kutry i skrzynie rybackie wypełniają miejski port.",
        "exits": {"west": "fish_market", "east": "sea_pier"},
    },
    "sea_pier": {
        "zone": "Wybrzeże", "name": "Morskie Molo",
        "desc": "Długie molo wychodzi nad morze. To łowisko typowych ryb morskich.",
        "exits": {"west": "harbor", "east": "ocean_platform"},
    },
    "ocean_platform": {
        "zone": "Wybrzeże", "name": "Oceaniczna Platforma",
        "desc": "Daleka platforma nad otwartym oceanem. Trafiają się tu wielkie ryby oceaniczne i rekiny.",
        "exits": {"west": "sea_pier"},
    },
    "forge": {
        "zone": "Miasto Dusz", "name": "Kuźnia Dusz",
        "desc": "Młoty uderzają o metal, a Broń Duszy odpowiada cichym rezonansem.",
        "exits": {"west": "market"},
    },
    "inn": {
        "zone": "Miasto Dusz", "name": "Karczma Pod Błękitnym Płomieniem",
        "desc": "Ciepła karczma pełna rozmów podróżników.",
        "exits": {"north": "market", "west": "south_street"},
    },
    "south_street": {
        "zone": "Miasto Dusz", "name": "Ulica Południowa",
        "desc": "Cichsza część miasta prowadząca do południowej bramy.",
        "exits": {"north": "square", "east": "inn", "south": "south_gate"},
    },
    "south_gate": {
        "zone": "Miasto Dusz", "name": "Południowa Brama",
        "desc": (
            "Brama otwiera się na łąki i Gaj Szeptów. Miejska straż utrzymuje tu "
            "stały posterunek i ostrzega podróżnych o wilkach oraz zagrożeniach w dziczy."
        ),
        "exits": {"north": "south_street", "south": "meadow"},
    },
    "meadow": {
        "zone": "Łąki", "name": "Srebrna Łąka",
        "desc": (
            "Centralna część rozległych łąk. W trawie rosną Pokrzywa, "
            "Rumianek, Mięta, Krwawnik, Melisa i Lawenda. "
            "Na zachodzie leży Łąka Kwiatów, na wschodzie Łąka Mięty, "
            "a na południu Łąka Nadjeziorna."
        ),
        "exits": {
            "north": "south_gate",
            "west": "flower_meadow",
            "east": "mint_meadow",
            "south": "lakeside_meadow",
        },
    },
    "mint_meadow": {
        "zone": "Łąki", "name": "Łąka Mięty",
        "desc": (
            "Wilgotniejsza łąka pachnąca Miętą i Melisą. "
            "To dobre miejsce do Zielarstwa, szczególnie dla początkujących."
        ),
        "exits": {"west": "meadow", "east": "riverbank"},
    },
    "flower_meadow": {
        "zone": "Łąki", "name": "Łąka Kwiatów",
        "desc": (
            "Kolorowa łąka pełna Rumianku, Lawendy i Krwawnika. "
            "Dalej na zachodzie zaczyna się Gaj Szeptów."
        ),
        "exits": {"east": "meadow", "west": "whisper_grove"},
    },
    "lakeside_meadow": {
        "zone": "Łąki", "name": "Łąka Nadjeziorna",
        "desc": (
            "Łąka schodząca ku Srebrnemu Jezioru. "
            "Rosną tu Mięta, Melisa, Rumianek i inne zioła lubiące wilgoć."
        ),
        "exits": {"north": "meadow", "south": "lake_shore"},
    },
    "lake_shore": {
        "zone": "Dzicz", "name": "Brzeg Srebrnego Jeziora",
        "desc": "Spokojne jezioro jest osobnym łowiskiem dla ryb jeziorowych.",
        "exits": {"north": "lakeside_meadow"},
    },
    "whisper_grove": {
        "zone": "Dzicz", "name": "Gaj Szeptów",
        "desc": "Stare drzewa szepczą pod wpływem magicznego wiatru.",
        "exits": {"east": "flower_meadow", "south": "deep_grove", "west": "lumberjack_camp", "north": "herbalist_hut"},
    },
    "herbalist_hut": {
        "zone": "Dzicz", "name": "Chata Zielarki",
        "desc": "Półki są pełne suszonych ziół, fiolek i alchemicznych naczyń.",
        "exits": {"south": "whisper_grove"},
    },
    "lumberjack_camp": {
        "zone": "Dzicz", "name": "Obóz Drwala",
        "desc": "Przy stosach drewna stoi warsztat Drwala Brana. Tutaj kupuje się Piłę.",
        "exits": {"east": "whisper_grove"},
    },
    "deep_grove": {
        "zone": "Dzicz", "name": "Głębia Gaju",
        "desc": "Światło prawie nie dociera między gęste konary.",
        "exits": {"north": "whisper_grove", "east": "hill"},
    },
    "hill": {
        "zone": "Dzicz", "name": "Wzgórze Kamiennych Znaków",
        "desc": "Na szczycie stoją stare kamienie pokryte nieczytelnymi runami.",
        "exits": {"west": "deep_grove", "north": "shrine"},
    },
    "shrine": {
        "zone": "Dzicz", "name": "Zapomniana Kapliczka",
        "desc": "Mała kapliczka poświęcona dawnym strażnikom dusz.",
        "exits": {"south": "hill"},
    },
    "riverbank": {
        "zone": "Dzicz", "name": "Brzeg Rzeki",
        "desc": "Szybka rzeka oddziela łąki od ruin starego pogranicza.",
        "exits": {"west": "mint_meadow", "east": "stone_bridge"},
    },
    "stone_bridge": {
        "zone": "Dzicz", "name": "Kamienny Most",
        "desc": "Popękany most prowadzi na wschodni brzeg.",
        "exits": {"west": "riverbank", "east": "ruined_watchtower"},
    },
    "ruined_watchtower": {
        "zone": "Ruiny Strażnicy", "name": "Ruiny Strażnicy",
        "desc": (
            "Zawalona wieża obserwacyjna góruje nad starym pograniczem. "
            "Gobliny plądrują wejście, lecz spod gruzów prowadzą schody do zachowanych części dawnego garnizonu."
        ),
        "exits": {
            "west": "stone_bridge", "south": "goblin_camp", "east": "graveyard",
            "down": "ruin_gatehouse",
        },
    },
    "ruin_gatehouse": {
        "zone": "Ruiny Strażnicy", "name": "Zawalona Brama Strażnicy",
        "desc": (
            "Kamienny korytarz pod wieżą wciąż nosi ślady dawnej obrony. "
            "Połamane kraty i tarcze tworzą wąskie przejście do wnętrza ruin."
        ),
        "exits": {"up": "ruined_watchtower", "east": "ruin_courtyard"},
    },
    "ruin_courtyard": {
        "zone": "Ruiny Strażnicy", "name": "Wewnętrzny Dziedziniec",
        "desc": (
            "Popękane płyty dziedzińca otaczają resztki studni. "
            "Wokół zachowały się wejścia do koszar, murów i piwnic dawnej straży."
        ),
        "exits": {
            "west": "ruin_gatehouse", "north": "ruin_barracks",
            "east": "ruin_wall_walk", "south": "ruin_cellar",
        },
    },
    "ruin_barracks": {
        "zone": "Ruiny Strażnicy", "name": "Opuszczone Koszary",
        "desc": (
            "Spróchniałe prycze stoją między zardzewiałymi stojakami na broń. "
            "Niektórzy dawni strażnicy najwyraźniej nigdy nie opuścili posterunku."
        ),
        "exits": {"south": "ruin_courtyard", "east": "ruin_armory"},
    },
    "ruin_armory": {
        "zone": "Ruiny Strażnicy", "name": "Zbrojownia Starej Straży",
        "desc": (
            "Ciężkie szafy i skrzynie z resztkami uzbrojenia wypełniają kamienną salę. "
            "Na ścianach wiszą pęknięte herby dawnego garnizonu."
        ),
        "exits": {"west": "ruin_barracks", "east": "ruin_command_chamber"},
    },
    "ruin_wall_walk": {
        "zone": "Ruiny Strażnicy", "name": "Chodnik na Murze",
        "desc": (
            "Wąski chodnik biegnie po ocalałym fragmencie muru. "
            "Dawne stanowiska kuszników nadal spoglądają na drogę i dolinę."
        ),
        "exits": {"west": "ruin_courtyard", "north": "ruin_archive"},
    },
    "ruin_archive": {
        "zone": "Ruiny Strażnicy", "name": "Archiwum Runiczne",
        "desc": (
            "Kamienne tablice i metalowe pieczęcie pokrywają resztki archiwum. "
            "W powietrzu utrzymuje się słaba, lecz wciąż aktywna magia ochronna."
        ),
        "exits": {"south": "ruin_wall_walk", "down": "ruin_undercroft"},
    },
    "ruin_cellar": {
        "zone": "Ruiny Strażnicy", "name": "Piwnice Strażnicy",
        "desc": (
            "Wilgotne piwnice pełne są rozbitych beczek, kości i śladów szabrowników. "
            "Niżej prowadzi stary tunel służbowy."
        ),
        "exits": {"north": "ruin_courtyard", "down": "ruin_undercroft"},
    },
    "ruin_undercroft": {
        "zone": "Ruiny Strażnicy", "name": "Podziemia Garnizonu",
        "desc": (
            "Niskie sklepienia podtrzymują filary pokryte znakami wartowników. "
            "Stąd prowadzi droga do zapieczętowanej sali wewnętrznej."
        ),
        "exits": {
            "up": "ruin_cellar", "west": "ruin_archive", "east": "ruin_sealed_hall",
        },
    },
    "ruin_sealed_hall": {
        "zone": "Ruiny Strażnicy", "name": "Sala Pieczęci",
        "desc": (
            "Pęknięte pieczęcie na posadzce wciąż pulsują bladym światłem. "
            "Za nimi znajduje się dawna komnata dowódcy strażnicy."
        ),
        "exits": {"west": "ruin_undercroft", "north": "ruin_command_chamber"},
    },
    "ruin_command_chamber": {
        "zone": "Ruiny Strażnicy", "name": "Komnata Dowódcy Strażnicy",
        "desc": (
            "Ocalały stół dowódcy stoi pod poszarpanym sztandarem. "
            "Najpotężniejszy z dawnych obrońców strzeże tej komnaty nawet po upadku garnizonu."
        ),
        "exits": {"south": "ruin_sealed_hall", "west": "ruin_armory"},
    },
    "goblin_camp": {
        "zone": "Dzicz", "name": "Obóz Goblinów",
        "desc": (
            "Prymitywne namioty stoją wokół dymiącego ogniska. "
            "Na wschodzie w skale zieje wejście do rozległych Jaskiń Goblinów."
        ),
        "exits": {"north": "ruined_watchtower", "south": "cave_entrance", "east": "goblin_cave_mouth"},
    },
    "goblin_cave_mouth": {
        "zone": "Jaskinie Goblinów", "name": "Wejście do Jaskiń Goblinów",
        "desc": "Niski skalny otwór jest obwieszony kośćmi, sznurkami i prymitywnymi dzwonkami alarmowymi.",
        "exits": {"west": "goblin_camp", "east": "goblin_fungus_gallery"},
    },
    "goblin_fungus_gallery": {
        "zone": "Jaskinie Goblinów", "name": "Galeria Grzybów",
        "desc": "Wilgotny korytarz porastają świecące grzyby. W bocznych niszach widać ślady goblińskich wartowników.",
        "exits": {"west": "goblin_cave_mouth", "east": "goblin_scrap_tunnels", "south": "goblin_shaman_hollow"},
    },
    "goblin_scrap_tunnels": {
        "zone": "Jaskinie Goblinów", "name": "Tunele Złomu",
        "desc": "Gobliny zatarasowały ściany resztkami pancerzy, kół i połamanych narzędzi.",
        "exits": {"west": "goblin_fungus_gallery", "east": "goblin_guard_post", "south": "goblin_bomb_workshop"},
    },
    "goblin_shaman_hollow": {
        "zone": "Jaskinie Goblinów", "name": "Kotlina Szamanów",
        "desc": "Dym z gorzkich ziół miesza się tu z zielonkawą poświatą prostych goblińskich rytuałów.",
        "exits": {"north": "goblin_fungus_gallery", "east": "goblin_war_den"},
    },
    "goblin_bomb_workshop": {
        "zone": "Jaskinie Goblinów", "name": "Warsztat Bombiarzy",
        "desc": "Na chwiejnych stołach leżą gliniane kule, proch i wiązki lontów. Powietrze pachnie siarką.",
        "exits": {"north": "goblin_scrap_tunnels", "east": "goblin_war_den"},
    },
    "goblin_guard_post": {
        "zone": "Jaskinie Goblinów", "name": "Podziemny Posterunek",
        "desc": "Drewniane barykady i ostre pale tworzą pierwszy prawdziwy punkt obrony głębszej części jaskiń.",
        "exits": {"west": "goblin_scrap_tunnels", "east": "goblin_war_den"},
    },
    "goblin_war_den": {
        "zone": "Jaskinie Goblinów", "name": "Nora Wojenna",
        "desc": "Kamienne stoły pokrywają mapy szlaków, skradzione chorągwie i stosy broni gotowej do użycia.",
        "exits": {"west": "goblin_guard_post", "north": "goblin_shaman_hollow", "south": "goblin_bomb_workshop", "east": "goblin_treasure_burrow"},
    },
    "goblin_treasure_burrow": {
        "zone": "Jaskinie Goblinów", "name": "Nora Łupów",
        "desc": "Skrzynie, worki i chaotyczne stosy skradzionych przedmiotów wypełniają prawie całe pomieszczenie.",
        "exits": {"west": "goblin_war_den", "east": "goblin_throne_cave"},
    },
    "goblin_throne_cave": {
        "zone": "Jaskinie Goblinów", "name": "Grota Króla Goblinów",
        "desc": "Najgłębsza komora została zamieniona w prymitywną salę tronową. Tu rządzi Król Goblinów.",
        "exits": {"west": "goblin_treasure_burrow"},
    },
    "cave_entrance": {
        "zone": "Podziemia", "name": "Wejście do Kopalni Głębinowej",
        "desc": "Główne wejście do jedynej kopalni świata. Niżej zaczynają się kolejne poziomy Kopalni Głębinowej.",
        "exits": {"north": "goblin_camp", "down": "cave_tunnel"},
    },
    "cave_tunnel": {
        "zone": "Podziemia", "name": "Tunel Wejściowy Kopalni Głębinowej",
        "desc": "Tunel prowadzi z wejścia do komnaty zejściowej Kopalni Głębinowej.",
        "exits": {"up": "cave_entrance", "east": "crystal_chamber"},
    },
    "crystal_chamber": {
        "zone": "Podziemia", "name": "Komnata Zejściowa Kopalni Głębinowej",
        "desc": "Ostatnia komnata wejściowa. Stąd schodzi się na poziom 1 jedynej Kopalni Głębinowej.",
        "exits": {"west": "cave_tunnel"},
    },
    "graveyard": {
        "zone": "Dzicz", "name": "Stary Cmentarz",
        "desc": "Pęknięte nagrobki otaczają zejście do zapomnianej krypty.",
        "exits": {"west": "ruined_watchtower", "down": "crypt_entrance"},
    },
    "crypt_entrance": {
        "zone": "Podziemia", "name": "Przedsionek Krypty",
        "desc": "Kamienne schody prowadzą w ciemność.",
        "exits": {"up": "graveyard", "south": "crypt_hall"},
    },
    "crypt_hall": {
        "zone": "Podziemia", "name": "Sala Krypty",
        "desc": "W ścianach znajdują się stare nisze grobowe.",
        "exits": {"north": "crypt_entrance", "down": "crypt_depths"},
    },
    "crypt_depths": {
        "zone": "Podziemia", "name": "Głębia Krypty",
        "desc": "Najstarsza część podziemi. Powietrze drży od niespokojnej energii.",
        "exits": {"up": "crypt_hall"},
    },
    "old_road": {
        "zone": "Dzicz", "name": "Stary Trakt",
        "desc": "Kamienny trakt prowadzi między zarośniętymi słupami granicznymi. Na wschodzie widać wartownię straży.",
        "exits": {"south": "north_gate", "north": "crossroads", "east": "north_watchpost"},
    },
    "north_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Północna",
        "desc": "Drewniana wartownia pilnuje północnego szlaku. Strażnicy obserwują ruch na Starym Trakcie.",
        "exits": {"west": "old_road", "east": "frontier_watchpost"},
    },
    "frontier_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Pogranicza",
        "desc": "Kamienno-drewniany posterunek stoi na granicy bezpiecznych ziem. Dalej zaczyna się teren bandytów.",
        "exits": {"west": "north_watchpost", "east": "bandit_camp"},
    },
    "bandit_camp": {
        "zone": "Obozowiska Bandytów", "name": "Skraj Obozowiska Bandytów",
        "desc": (
            "Pierwsze brudne namioty i wygasające ogniska stoją tuż za granicą straży. "
            "Dalej obozowisko rozdziela się na kilka pilnowanych części."
        ),
        "exits": {"west": "frontier_watchpost", "east": "bandit_outer_ring", "north": "bandit_supply_tents", "south": "bandit_training_yard"},
    },
    "bandit_outer_ring": {
        "zone": "Obozowiska Bandytów", "name": "Zewnętrzny Pierścień Obozu",
        "desc": "Niskie barykady, ogniska i prowizoryczne strażnice tworzą zewnętrzny pas obrony bandytów.",
        "exits": {"west": "bandit_camp", "east": "bandit_barricade"},
    },
    "bandit_supply_tents": {
        "zone": "Obozowiska Bandytów", "name": "Namioty Zaopatrzenia",
        "desc": "Pod płachtami leżą worki z jedzeniem, beczki i towary zabrane kupieckim karawanom.",
        "exits": {"south": "bandit_camp", "east": "bandit_loot_depot"},
    },
    "bandit_training_yard": {
        "zone": "Obozowiska Bandytów", "name": "Plac Ćwiczeń Bandytów",
        "desc": "Zużyte manekiny, tarcze i prowizoryczna arena służą bandytom do brutalnych ćwiczeń.",
        "exits": {"north": "bandit_camp", "east": "bandit_arena"},
    },
    "bandit_barricade": {
        "zone": "Obozowiska Bandytów", "name": "Wewnętrzna Barykada",
        "desc": "Wysoka palisada oddziela zwykłych rabusiów od lepiej uzbrojonej części obozu.",
        "exits": {"west": "bandit_outer_ring", "east": "bandit_inner_camp"},
    },
    "bandit_loot_depot": {
        "zone": "Obozowiska Bandytów", "name": "Magazyn Łupów",
        "desc": "Skrzynie z monetami, bronią i skradzionymi zapasami stoją pod silną strażą.",
        "exits": {"west": "bandit_supply_tents", "south": "bandit_inner_camp"},
    },
    "bandit_arena": {
        "zone": "Obozowiska Bandytów", "name": "Krąg Walk",
        "desc": "Ubita ziemia jest otoczona palami. Najsilniejsi bandyci ćwiczą tu walkę bez zasad.",
        "exits": {"west": "bandit_training_yard", "north": "bandit_inner_camp"},
    },
    "bandit_inner_camp": {
        "zone": "Obozowiska Bandytów", "name": "Wewnętrzne Obozowisko",
        "desc": "Tu stoją najlepsze namioty, stoły dowódców i straże pilnujące drogi do kwatery Herszta.",
        "exits": {"west": "bandit_barricade", "north": "bandit_loot_depot", "south": "bandit_arena", "east": "bandit_command_tent"},
    },
    "bandit_command_tent": {
        "zone": "Obozowiska Bandytów", "name": "Namiot Herszta",
        "desc": "Duży namiot pełen map, rozkazów i trofeów. To tutaj przebywa Herszt Bandytów.",
        "exits": {"west": "bandit_inner_camp"},
    },
    "crossroads": {
        "zone": "Dzicz", "name": "Rozdroże",
        "desc": "Stary drogowskaz wskazuje zachód ku lasom i wschód ku ruinom.",
        "exits": {"south": "old_road", "west": "deep_grove", "east": "ruined_watchtower"},
    },
}

__all__ = ['ROOMS']

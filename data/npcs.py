# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
NPCS = {
    "fisher_tomas": {
        "name": "Rybak Borys", "room": "fish_market",
        "rank_profession": "Wędkarstwo",
        "dialogue": "Jeśli naprawdę chcesz zostać wędkarzem, przynieś mi trzydzieści ryb.",
        "quest": "fisher_30_fish",
    },
    "lumberjack_bran": {
        "name": "Drwal Bran", "room": "lumberjack_camp",
        "rank_profession": "Drwalstwo",
        "dialogue": "Piłę kupisz tylko tutaj. Jeśli chcesz sprawdzić się jako drwal, przynieś mi trzydzieści sztuk dowolnego drewna.",
        "quest": "lumberjack_30_wood",
    },
    "herbalist_liora": {
        "name": "Zielarka Liora", "room": "herbalist_hut",
        "rank_profession": "Zielarstwo",
        "dialogue": "Kupisz u mnie Sierp Zielarski i Moździerz Alchemiczny. Przynieś mi trzydzieści dowolnych ziół, a wynagrodzę twoją pracę.",
        "quest": "herbalist_30_herbs",
    },
    "miner_toren": {
        "name": "Górnik Toren", "room": "cave_entrance",
        "rank_profession": "Górnictwo",
        "dialogue": (
            "Dobra ruda nie wydobędzie się sama. "
            "Tylko u mnie kupisz podstawowy Kilof. "
            "Wpisz list albo shop, aby zobaczyć ofertę. "
            "Przynieś mi trzydzieści sztuk dowolnej rudy z kopalni."
        ),
        "quest": "miner_30_ore",
        "shopkeeper": True,
    },
    "specialist_fishing": {
        "name": "Mistrz Wędkarstwa Neris", "room": "fish_market",
        "rank_profession": "Wędkarstwo",
        "dialogue": (
            "Specjalizuję się w Wędkarstwie i rozwoju Wędki. "
            "Pokażę ci aktualny level narzędzia, Tier i drogę do następnego progu."
        ),
        "specialist_tool_type": "fishing",
        "specialist_topic": "wedkarstwo",
    },
    "specialist_mining": {
        "name": "Mistrz Górnictwa Kordan", "room": "cave_entrance",
        "rank_profession": "Górnictwo",
        "dialogue": (
            "Specjalizuję się w Górnictwie i rozwoju Kilofa. "
            "Im wyższy level Kilofa, tym lepsze rudy możesz wydobywać."
        ),
        "specialist_tool_type": "mining",
        "specialist_topic": "gornictwo",
    },
    "specialist_woodcutting": {
        "name": "Mistrz Drwalstwa Oren", "room": "lumberjack_camp",
        "rank_profession": "Drwalstwo",
        "dialogue": (
            "Specjalizuję się w Drwalstwie i rozwoju Piły. "
            "Wyższe levele otwierają dostęp do coraz rzadszych gatunków drewna."
        ),
        "specialist_tool_type": "woodcutting",
        "specialist_topic": "drwalstwo",
    },
    "specialist_crafting": {
        "name": "Mistrz Rzemiosła Haldor", "room": "forge",
        "rank_profession": "Kowalstwo",
        "dialogue": (
            "Specjalizuję się w Kowalstwie, Rzemiośle i Młocie Rzemieślniczym. "
            "W Kuźni możesz przetapiać rudy, kuć pancerze i wykonywać "
            "powtarzalne zlecenia odnawiane co godzinę."
        ),
        "specialist_tool_type": "crafting",
        "specialist_topic": "kowalstwo",
        "specialist_recipes": "receptury kowalstwo",
        "quest": "haldor_crafting_order",
        "specialist_quests": (
            "haldor_crafting_order",
            "haldor_crafting_order_advanced",
            "haldor_crafting_order_master",
        ),
    },
    "specialist_cooking": {
        "name": "Kucharz Marcel", "room": "inn",
        "rank_profession": "Gotowanie",
        "dialogue": (
            "Jestem Kucharzem Błękitnego Płomienia. "
            "Pomogę ci rozwijać Nóż Kucharski i korzystać z receptur Gotowania."
        ),
        "specialist_tool_type": "cooking",
        "specialist_topic": "gotowanie",
        "specialist_recipes": "receptury cook",
        "quest": "marcel_cooking_order",
        "specialist_quests": (
            "marcel_cooking_order",
            "marcel_cooking_order_advanced",
            "marcel_cooking_order_master",
        ),
    },
    "specialist_herbalism": {
        "name": "Mistrzyni Zielarstwa Sena", "room": "herbalist_hut",
        "rank_profession": "Zielarstwo",
        "dialogue": (
            "Specjalizuję się w Zielarstwie i rozwoju Sierpa Zielarskiego. "
            "Wysoki level Sierpa pozwala zbierać najrzadsze zioła."
        ),
        "specialist_tool_type": "herbalism",
        "specialist_topic": "zielarstwo",
    },
    "specialist_alchemy": {
        "name": "Mistrz Alchemii Orin", "room": "herbalist_hut",
        "rank_profession": "Alchemia",
        "dialogue": (
            "Specjalizuję się w Alchemii i Moździerzu Alchemicznym. "
            "Mam jedenaście poziomów zleceń na mikstury i eliksiry, "
            "od podstawowej Many aż do Eliksiru Wiecznej Duszy."
        ),
        "specialist_tool_type": "alchemy",
        "specialist_topic": "alchemia",
        "specialist_recipes": "receptury alchemia",
        "quest": "orin_alchemy_order",
        "specialist_quests": (
            "orin_alchemy_order",
            "orin_alchemy_order_healing",
            "orin_alchemy_order_greater_healing",
            "orin_alchemy_order_greater_mana",
            "orin_alchemy_order_vitality",
            "orin_alchemy_order_advanced",
            "orin_alchemy_order_supreme_mana",
            "orin_alchemy_order_grand_vitality",
            "orin_alchemy_order_soul_tonic",
            "orin_alchemy_order_astral_restoration",
            "orin_alchemy_order_master",
        ),
    },
    "banker_aldren": {
        "name": "Bankier Aldren", "room": "market",
        "dialogue": (
            "Prowadzę Bank Dusz. Możesz zdeponować walutę i "
            "przedmioty, a wszystko pozostanie bezpieczne po wylogowaniu."
        ),
        "quest": None,
        "banker": True,
    },
    "market_trader_radan": {
        "name": "Handlarz Skupu Radan", "room": "market",
        "dialogue": (
            "Skupuję zwykłe łupy z potworów, trofea oraz niezałożone wyposażenie. "
            "Sell nazwa sprzedaje wskazany przedmiot, ale sell all sprzedaje wyłącznie niezałożone EQ. "
            "Nie kupuję ryb, rud, minerałów, drewna, ziół ani innych materiałów rzemieślniczych. "
            "Nie kupuję też narzędzi, przedmiotów questowych ani EQ, które masz aktualnie założone."
        ),
        "quest": None,
        "shopkeeper": True,
        "buyback_trader": True,
    },
    "priest_elor": {
        "name": "Kapłan Elor", "room": "temple",
        "dialogue": (
            "Świątynia prowadzi Próby Broni Duszy dla każdego odblokowania Soul Tieru 2-40. "
            "Próby są rozdzielone na pasma: Początkująca T2-4, Poszukiwacza T5-7, "
            "Weterana T8-12, Mistrzowska T13-20 oraz endgame T21-40. "
            "Po osiągnięciu wymaganego Soul Levelu sprawdź quest list Kapłan Elor, "
            "przyjmij właściwą Próbę i wykonaj jej cel. Po ukończeniu użyj unlock."
        ),
        "quest": "temple_rats",
    },
    "captain_arven": {
        "name": "Kapitan Arven", "room": "guard_hall",
        "dialogue": "Gobliny zajęły starą strażnicę. Potrzebujemy kogoś, kto oczyści szlak.",
        "quest": "goblin_problem",
    },
    "north_gate_guard_oskar": {
        "name": "Strażnik Oskar", "room": "north_gate",
        "dialogue": (
            "Północna brama jest pod stałą ochroną. Za murami zaczyna się Stary Trakt, "
            "więc przed wyjściem sprawdź ekwipunek i aktywne questy."
        ),
        "quest": None,
    },
    "north_gate_guard_marta": {
        "name": "Strażniczka Marta", "room": "north_gate",
        "dialogue": (
            "Wracających ze Starego Traktu sprawdzamy po każdym alarmie. "
            "Jeżeli szukasz zleceń straży, Kapitan Arven czeka w Strażnicy Głównej."
        ),
        "quest": None,
    },
    "south_gate_guard_lena": {
        "name": "Strażniczka Lena", "room": "south_gate",
        "dialogue": (
            "Na południu zaczynają się łąki i Gaj Szeptów. Wilki potrafią podejść blisko traktu, "
            "więc nie ignoruj ostrzeżeń z dziczy."
        ),
        "quest": None,
    },
    "south_gate_guard_branek": {
        "name": "Strażnik Branek", "room": "south_gate",
        "dialogue": (
            "Pilnujemy tej bramy całą dobę. Jeśli wracasz ranny, Świątynia Odrodzenia jest w centrum miasta."
        ),
        "quest": None,
    },
    "guard_quartermaster_harek": {
        "name": "Kwatermistrz Harek", "room": "guard_armory",
        "dialogue": (
            "Każda tarcza i włócznia ma swój numer. Zbrojownia zaopatruje obie bramy i patrole miejskie."
        ),
        "quest": None,
    },
    "guard_archivist_nela": {
        "name": "Archiwistka Nela", "room": "guard_archive",
        "dialogue": (
            "Przechowuję raporty o goblinach, bandytach i ruinach pogranicza. "
            "Kapitan Arven korzysta z nich przy planowaniu patroli."
        ),
        "quest": None,
    },
    "guard_jailer_torvik": {
        "name": "Dozorca Torvik", "room": "guard_cells",
        "dialogue": (
            "Cele są dla tych, których patrole sprowadzą żywych. Najczęściej trafiają tu bandyci i szabrownicy."
        ),
        "quest": None,
    },
    "watch_commander_roderik": {
        "name": "Dowódca Roderik", "room": "north_watchpost",
        "dialogue": (
            "Bandyci znów zbierają się w obozowisku za Wartownią Pogranicza. "
            "Potrzebujemy regularnych patroli, które ograniczą ich napady."
        ),
        "quest": "bandit_patrol",
    },
    "frontier_guard_anna": {
        "name": "Strażniczka Anna", "room": "frontier_watchpost",
        "dialogue": (
            "Za tą wartownią zaczyna się Obozowisko Bandytów. "
            "Jeśli masz zlecenie od Dowódcy Roderika, trzymaj się na baczności."
        ),
        "quest": None,
    },
    "mira": {
        "name": "Zielarka Mira", "room": "whisper_grove",
        "dialogue": "Wilki Cienia zakłócają równowagę gaju. Ich obecność jest coraz silniejsza.",
        "quest": "shadow_wolves",
    },
    "doran": {
        "name": "Kowal Doran", "room": "forge",
        "dialogue": "Mam pełny żelazny zestaw ochronny. Wpisz list, aby przejrzeć ofertę. Odłamki Duszy z krypty też mnie interesują.",
        "quest": "soul_shards",
    },
    "innkeeper": {
        "name": "Karczmarka Elia", "room": "inn",
        "dialogue": (
            "Witaj w Błękitnym Płomieniu. Tutaj odpoczniesz i skorzystasz z kuchni; "
            "mikstury kupisz w Aptece Pod Srebrnym Liściem. Mam też trzy niezależne "
            "zlecenia odnawiane co godzinę."
        ),
        "quest": "elia_hourly_fish",
        "specialist_quests": ("elia_hourly_fish", "elia_hourly_herbs", "elia_hourly_bandits"),
    },
    "archivist": {
        "name": "Archiwista Sol", "room": "library",
        "dialogue": "Level postaci jest jedną z osi progresji; równie ważne są statystyki, Biegłość, Dusza i umiejętności.",
        "quest": None,
    },
    "teacher_warrior": {
        "name": "Mistrz Garran", "room": "guild_martial_hall",
        "dialogue": "Uczę Wojowników kontroli Miecza Przysięgi i walki frontowej.",
        "teacher_class": "Wojownik",
    },
    "teacher_berserker": {
        "name": "Mistrzyni Brynja", "room": "guild_martial_hall",
        "dialogue": "Uczę Berserkerów kierować furią, zanim furia zacznie kierować nimi.",
        "teacher_class": "Berserker",
    },
    "teacher_rogue": {
        "name": "Mistrz Kael", "room": "guild_shadow_gallery",
        "dialogue": "Uczę Łotrzyków szybkości, precyzji i ataku z cienia.",
        "teacher_class": "Łotrzyk",
    },
    "teacher_hunter": {
        "name": "Mistrzyni Eira", "room": "guild_shadow_gallery",
        "dialogue": "Uczę Łowców wykorzystywać dystans, tempo i Łuk Echa.",
        "teacher_class": "Łowca",
    },
    "teacher_monk": {
        "name": "Mistrz Shen", "room": "guild_body_hall",
        "dialogue": "Uczę Mnichów panowania nad ciałem, oddechem i Rękawicami Ducha.",
        "teacher_class": "Mnich",
    },
    "teacher_guardian": {
        "name": "Mistrz Borin", "room": "guild_body_hall",
        "dialogue": "Uczę Strażników, jak przetrwać uderzenie, które złamałoby innych.",
        "teacher_class": "Strażnik",
    },
    "teacher_mage": {
        "name": "Arcymag Vaelis", "room": "guild_arcane_chamber",
        "dialogue": "Uczę Magów kontroli Many i energii Arkanów.",
        "teacher_class": "Mag",
    },
    "teacher_necromancer": {
        "name": "Mistrzyni Morwen", "room": "guild_dark_chamber",
        "dialogue": "Uczę Nekromantów bezpiecznego obchodzenia się z energią śmierci.",
        "teacher_class": "Nekromanta",
    },
    "teacher_priest": {
        "name": "Mistrz Aureon", "room": "guild_sanctuary",
        "dialogue": "Uczę Kapłanów łączyć świętą moc, leczenie i obronę.",
        "teacher_class": "Kapłan",
    },
    "teacher_warlock": {
        "name": "Mistrzyni Nyra", "room": "guild_dark_chamber",
        "dialogue": "Uczę Czarowników wykorzystywać Otchłań bez oddawania jej całej kontroli.",
        "teacher_class": "Czarownik",
    },
    "teacher_druid": {
        "name": "Mistrz Thalen", "room": "guild_sanctuary",
        "dialogue": "Uczę Druidów czerpać moc z natury, leczenia i burzy.",
        "teacher_class": "Druid",
    },
    "teacher_psion": {
        "name": "Mistrzyni Ilyra", "room": "guild_arcane_chamber",
        "dialogue": "Uczę Psioników dyscypliny umysłu i kontroli energii psionicznej.",
        "teacher_class": "Psionik",
    },
    "teacher_mec": {
        "name": "Mechanik Vektor", "room": "guild_mec_chamber",
        "dialogue": "Uczę Meców kontroli Rdzenia, pancerza i uzbrojenia pokładowego.",
        "teacher_class": "Mec",
    },
    "teacher_engineer": {
        "name": "Inżynierka Ada", "room": "guild_engineer_chamber",
        "dialogue": "Uczę Inżynierów obsługi Omni-Narzędzia, działek i urządzeń taktycznych.",
        "teacher_class": "Inżynier",
    },
}

__all__ = ['NPCS']

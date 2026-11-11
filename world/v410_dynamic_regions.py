# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def build_v0930_large_exploration_regions():
    """Rozbudowuje małe expowiska do dużych, zapętlonych regionów.

    Bez nowego eventu eksploracyjnego: zmiana dotyczy wyłącznie świata.
    Nowe sektory tworzą siatki z pętlami i bocznymi drogami zamiast prostych
    krzyży. Istniejące wejścia, bossowie i połączenia między regionami zostają.
    """
    reverse = {"north":"south","south":"north","east":"west","west":"east","up":"down","down":"up"}
    targets = {
        "Obozowiska Bandytów": 24,
        "Jaskinie Goblinów": 24,
        "Ruiny Strażnicy": 24,
        "Stary Cmentarz": 24,
        "Ruiny Kultystów": 24,
        "Legowisko Bestii": 24,
        "Nekropolia": 24,
        "Kanały Pod Miastem": 24,
        "Lodowe Jaskinie": 24,
        "Las Szeptów": 24,
        "Pustynia": 28,
        "Bagna": 28,
        "Góry": 28,
        "Popielne Pustkowia": 30,
        "Rozbite Niebo": 30,
        "Wybrzeże Pustki": 30,
        "Korona Świata": 30,
    }
    anchors = {
        "Obozowiska Bandytów":"bandit_outer_ring",
        "Jaskinie Goblinów":"goblin_scrap_tunnels",
        "Ruiny Strażnicy":"ruin_courtyard",
        "Stary Cmentarz":"cemetery_ossuary_path",
        "Ruiny Kultystów":"cult_ruins_courtyard",
        "Legowisko Bestii":"beast_lair_tracks",
        "Nekropolia":"necropolis_procession",
        "Kanały Pod Miastem":"sewer_runoff",
        "Lodowe Jaskinie":"ice_cave_blue_tunnel",
        "Las Szeptów":"forest_old_oaks",
        "Pustynia":"desert_dunes",
        "Bagna":"reed_mire",
        "Góry":"mountain_lower_slopes",
        "Popielne Pustkowia":"ashen_waste",
        "Rozbite Niebo":"storm_bridge",
        "Wybrzeże Pustki":"void_shore",
        "Korona Świata":"eternal_causeway",
    }
    words = {
        "Obozowiska Bandytów": (("Ścieżka","Namioty","Barykada","Plac","Zaułek"),("Czerwonych Chust","Zrabowanych Wozów","Nocnej Straży","Starych Palisad","Przemytników","Wilczych Zębów"),"Palisady, wozy i boczne przejścia rozbijają obóz na wiele połączonych sektorów."),
        "Jaskinie Goblinów": (("Tunel","Grota","Szyb","Nora","Galeria"),("Zielonego Dymu","Kościanych Totemów","Złomiarzy","Krzywych Kilofów","Grzybowych Lamp","Piszczałek"),"Kręte tunele przecinają się i wracają do wcześniejszych grot, tworząc rozległą sieć."),
        "Ruiny Strażnicy": (("Korytarz","Dziedziniec","Wieża","Komnata","Galeria"),("Pękniętych Tarcz","Starej Warty","Runicznych Murów","Zawalonych Łuków","Zapomnianego Garnizonu","Kamiennych Schodów"),"Pozostałości murów, krużganków i podziemi łączą się wieloma drogami."),
        "Stary Cmentarz": (("Aleja","Kwatera","Mauzoleum","Krypta","Ogród"),("Zapomnianych Imion","Krzywych Krzyży","Czarnych Róż","Otwartych Grobów","Płaczących Figur","Zgaszonych Lamp"),"Nagrobki, mauzolea i boczne alejki tworzą rozległy cmentarz z licznymi pętlami."),
        "Ruiny Kultystów": (("Krużganek","Komnata","Dziedziniec","Galeria","Przejście"),("Czarnej Pieczęci","Zgaszonych Świec","Pękniętych Run","Szeptów Otchłani","Spalonego Pergaminu","Pustych Masek"),"Ruiny świątyni ciągną się przez dziedzińce, biblioteki i boczne przejścia rytualne."),
        "Legowisko Bestii": (("Grota","Korytarz","Gniazdo","Szczelina","Łowisko"),("Starych Kości","Poszarpanych Skór","Żelaznych Korzeni","Ciepłego Oddechu","Śladów Pazurów","Głębokiego Ryku"),"Naturalne jaskinie rozchodzą się na kilka poziomów i łączą z powrotem bocznymi szczelinami."),
        "Nekropolia": (("Aleja","Katakumby","Mauzoleum","Plac","Grobowiec"),("Kamiennych Królów","Bezimiennych","Czarnych Chorągwi","Milczących Straży","Kościanych Bram","Wiecznego Czuwania"),"Monumentalna nekropolia ma wiele ulic grobowych, placów i zejść do katakumb."),
        "Kanały Pod Miastem": (("Kanał","Tunel","Komora","Przepust","Cysterna"),("Czarnej Wody","Starych Krat","Zgniłych Desek","Przemytników","Zielonego Szlamu","Głębokiego Odpływu"),"Kanały tworzą prawdziwy labirynt przepustów, cystern i bocznych odpływów."),
        "Lodowe Jaskinie": (("Tunel","Grota","Szczelina","Komora","Galeria"),("Błękitnego Lodu","Szronowych Kolumn","Zamarzniętych Ech","Kryształowego Pyłu","Pękniętego Lodowca","Wiecznej Zimy"),"Lodowe korytarze rozgałęziają się między szczelinami i zamarzniętymi komorami."),
        "Las Szeptów": (("Ścieżka","Polana","Zagajnik","Parów","Krąg"),("Starych Dębów","Cichego Mchu","Wilczych Tropów","Srebrnych Brzóz","Księżycowych Paproci","Powalonych Pni"),"Leśne trakty przecinają się, zawracają i prowadzą przez liczne polany oraz parowy."),
        "Pustynia": (("Wydmy","Kanion","Równina","Ruiny","Szlak"),("Siedmiu Wiatrów","Białych Kości","Czerwonego Piasku","Zaginionych Karawan","Szklanego Pyłu","Palącego Słońca"),"Wydmy i kaniony tworzą szeroki teren z wieloma szlakami między ruinami i oazami."),
        "Bagna": (("Mokradło","Groble","Rozlewisko","Torfowisko","Zarośla"),("Czarnej Wody","Gnijących Korzeni","Trujących Oparów","Zatopionych Drzew","Bagiennych Świateł","Wężowych Gniazd"),"Groble, wyspy i rozlewiska układają się w duży, zapętlony teren bagienny."),
        "Góry": (("Grań","Przełęcz","Półka","Wąwóz","Szlak"),("Białych Szczytów","Wiecznego Wiatru","Kamiennych Kozic","Starych Kopalń","Burzowych Chmur","Zamarzniętych Turni"),"Górskie trakty rozchodzą się po graniach, półkach i bocznych przełęczach."),
        "Popielne Pustkowia": (("Szlak","Pole","Wąwóz","Ruiny","Krawędź"),("Czarnego Popiołu","Dogasłych Palenisk","Zwęglonych Kości","Czerwonego Żaru","Martwych Pieców","Popielnej Burzy"),"Pustkowia rozciągają się daleko między polami popiołu, ruinami i pęknięciami ziemi."),
        "Rozbite Niebo": (("Most","Półka","Taras","Grań","Platforma"),("Piorunów","Rozdartych Chmur","Nawałnicy","Gromowych Wież","Podniebnych Ruin","Białego Wiatru"),"Podniebne mosty i półki tworzą wielodrogowy region wysoko nad chmurami."),
        "Wybrzeże Pustki": (("Brzeg","Molo","Ruiny","Zatoka","Taras"),("Czarnego Przypływu","Bezgwiezdnej Wody","Zatopionych Dzwonów","Pustych Latarni","Martwych Żagli","Otchłani"),"Czarny brzeg ciągnie się przez zatoki, mola i zatopione ruiny połączone wieloma ścieżkami."),
        "Korona Świata": (("Grobla","Galeria","Taras","Schody","Dziedziniec"),("Absolutu","Wiecznego Światła","Ponadczasowych Bram","Milczących Gwiazd","Białego Kamienia","Ostatniej Korony"),"Monumentalny szczyt tworzy rozległy kompleks tarasów, galerii i wielkich schodów."),
    }
    detail = (
        "Boczna droga wraca do dalszej części regionu, więc nie jest to ślepy krzyż.",
        "Kilka przejść pozwala obejść główny trakt i odkrywać teren różnymi trasami.",
        "Ścieżki łączą ten sektor z sąsiednimi częściami regionu w dużą pętlę.",
        "To jeden z wielu równoległych traktów; mapa ma liczne alternatywne połączenia.",
    )

    # Zbierz zwykłe moby obecnych regionów zanim dołożymy nowe spawny.
    room_zone = {rid: room.get("zone") for rid, room in ROOMS.items()}
    zone_pools = {}
    for rid, mid in list(MOB_SPAWNS):
        zone = room_zone.get(rid)
        if zone not in targets:
            continue
        tmpl = MOB_TEMPLATES.get(mid, {})
        if tmpl.get("world_boss") or tmpl.get("boss") or tmpl.get("boss_mechanic"):
            continue
        zone_pools.setdefault(zone, [])
        if mid not in zone_pools[zone]:
            zone_pools[zone].append(mid)

    # Cmentarz dostaje gęstszy zestaw nieumarłych, aby 0/25 nie wymagało stania na respawnie.
    cemetery_pool = [
        mid for mid in (
            "cemetery_restless_dead", "cemetery_bone_collector",
            "cemetery_bell_wraith", "cemetery_steel_skeleton",
            "cemetery_grave_hound", "cemetery_crypt_reaper",
            "cemetery_mourning_knight",
        ) if mid in MOB_TEMPLATES
    ]
    if cemetery_pool:
        zone_pools["Stary Cmentarz"] = cemetery_pool

    for zone, target in targets.items():
        existing = [rid for rid, room in ROOMS.items() if room.get("zone") == zone]
        need = max(0, int(target) - len(existing))
        if need <= 0:
            continue
        anchor = anchors[zone]
        prefixes, suffixes, zone_desc = words[zone]
        safe = _collection_slug(zone)
        new_ids = [f"v0930_{safe}_{i+1:02d}" for i in range(need)]
        # v0.33.6: nazwa każdego pokoju ma być globalnie jednoznaczna dla NVDA.
        # Wybieramy pełne kombinacje prefix x suffix i omijamy nazwy istniejące
        # już wcześniej w świecie; żadnych dopisków 2/3/4.
        used_room_names = {
            str(existing_room.get("name", "")).casefold().strip()
            for existing_room in ROOMS.values()
            if str(existing_room.get("name", "")).strip()
        }
        name_combinations = [
            (pfx, sfx)
            for sfx in suffixes
            for pfx in prefixes
        ]
        combo_cursor = 0
        for i, rid in enumerate(new_ids):
            chosen_pair = None
            while combo_cursor < len(name_combinations):
                candidate = name_combinations[combo_cursor]
                combo_cursor += 1
                candidate_name = f"{candidate[0]} {candidate[1]}"
                if candidate_name.casefold().strip() not in used_room_names:
                    chosen_pair = candidate
                    used_room_names.add(candidate_name.casefold().strip())
                    break
            if chosen_pair is None:
                # Teoretyczny bezpiecznik: pula ma 30 kombinacji, a każdy region
                # potrzebuje mniej nowych sektorów niż ten limit.
                chosen_pair = (prefixes[i % len(prefixes)], suffixes[(i // len(prefixes)) % len(suffixes)])
            prefix, suffix = chosen_pair
            room_data = {
                "zone": zone,
                "name": f"{prefix} {suffix}",
                "desc": f"{zone_desc} {detail[i % len(detail)]}",
                "exits": {},
            }
            endgame_recommended = dict(V0923_ENDGAME_REGIONS).get(zone)
            if endgame_recommended is not None:
                room_data["recommended_mastery"] = int(endgame_recommended)
            _catalog_mut.catalog_assign(room_data, 'ROOMS', ROOMS, (rid,))

        # Dołącz nową część bez nadpisywania istniejących wyjść.
        anchor_exits = _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (anchor,), "exits", {})
        attach = next((d for d in ("south","east","west","north","down","up") if d not in anchor_exits), None)
        if attach is None:
            attach = "down"
        anchor_exits[attach] = new_ids[0]
        _catalog_mut.catalog_assign(anchor, 'ROOMS', ROOMS, (new_ids[0], "exits", reverse[attach]))

        # Łącznik + nieregularna siatka 5 kolumn. Pełne poziome rzędy i kilka
        # pionowych łączników dają pętle i alternatywne trasy, ale nie prosty krzyż.
        if len(new_ids) > 1:
            back_from_connector = reverse[attach]
            forward = "south" if back_from_connector != "south" else "east"
            _catalog_mut.catalog_assign(new_ids[1], 'ROOMS', ROOMS, (new_ids[0], "exits", forward))
            _catalog_mut.catalog_assign(new_ids[0], 'ROOMS', ROOMS, (new_ids[1], "exits", reverse[forward]))

            grid = new_ids[1:]
            width = 5
            for idx, rid in enumerate(grid):
                row, col = divmod(idx, width)
                # poziome przejścia
                if col + 1 < width and idx + 1 < len(grid):
                    other = grid[idx + 1]
                    _catalog_mut.catalog_assign(other, 'ROOMS', ROOMS, (rid, "exits", "east"))
                    _catalog_mut.catalog_assign(rid, 'ROOMS', ROOMS, (other, "exits", "west"))
                # pionowe przejścia: kolumny skrajne zawsze, środkowe naprzemiennie
                down_idx = idx + width
                if down_idx < len(grid) and (col in (0, width-1) or (row + col) % 2 == 0):
                    other = grid[down_idx]
                    _catalog_mut.catalog_assign(other, 'ROOMS', ROOMS, (rid, "exits", "south"))
                    _catalog_mut.catalog_assign(rid, 'ROOMS', ROOMS, (other, "exits", "north"))

        # Zaludnij nowe sektory istniejącymi zwykłymi mobami regionu.
        pool = zone_pools.get(zone, [])
        if pool:
            for i, rid in enumerate(new_ids):
                MOB_SPAWNS.append((rid, pool[i % len(pool)]))
                if i % 4 == 0 and len(pool) > 1:
                    MOB_SPAWNS.append((rid, pool[(i + 1) % len(pool)]))

    # Achievement ma oznaczać faktyczne odkrycie całego aktualnego świata.
    tiers = list(ACHIEVEMENT_TRACKS.get("exploration_rooms", {}).get("tiers", ()))
    if tiers:
        fixed = [(req, rank) for req, rank in tiers if rank != "Platinum"]
        fixed.append((len(ROOMS), "Platinum"))
        ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = tuple(fixed)


def build_v0102_city_and_outskirts():
    """Rozbudowuje Miasto Dusz i tworzy żywe przedmieścia.

    Miasto pozostaje strefą bezpieczną bez wrogich spawnów. Przedmieścia
    są niskopoziomowym obszarem przejściowym między bramami i Łąkami.
    """
    city_rooms = {
        "artisan_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Rzemieślników",
            "desc":"Kamienna ulica pachnie drewnem, skórą i rozgrzanym metalem. Z obu stron stoją małe warsztaty miejskich fachowców.",
            "exits":{},
        },
        "tailor_workshop": {
            "zone":"Miasto Dusz", "name":"Pracownia Krawiecka",
            "desc":"Stoły są przykryte tkaninami, nićmi i wykrojami płaszczy dla mieszkańców oraz straży.",
            "exits":{},
        },
        "carpenter_workshop": {
            "zone":"Miasto Dusz", "name":"Warsztat Ciesielski",
            "desc":"Belki, deski i gotowe framugi wypełniają pracownię. Cieśla naprawia wozy i miejskie budynki.",
            "exits":{},
        },
        "leatherworker_workshop": {
            "zone":"Miasto Dusz", "name":"Warsztat Kaletnika",
            "desc":"Na półkach leżą pasy, torby i uprzęże. W powietrzu czuć garbowaną skórę i wosk.",
            "exits":{},
        },
        "mason_yard": {
            "zone":"Miasto Dusz", "name":"Dziedziniec Kamieniarzy",
            "desc":"Kamienne bloki, dłuta i fragmenty nowych murów tworzą głośny plac pracy budowniczych.",
            "exits":{},
        },
        "potter_workshop": {
            "zone":"Miasto Dusz", "name":"Warsztat Garncarski",
            "desc":"Koło garncarskie obraca się obok pieca. Na półkach schną misy, dzbany i naczynia dla karczmy.",
            "exits":{},
        },
        "lantern_alley": {
            "zone":"Miasto Dusz", "name":"Zaułek Latarni",
            "desc":"Wąski zaułek oświetlają rzędy błękitnych lamp. Mieszkańcy skracają tędy drogę do południowej dzielnicy.",
            "exits":{},
        },
        "city_bakery": {
            "zone":"Miasto Dusz", "name":"Piekarnia Pod Złotym Bochenkiem",
            "desc":"Ciepły zapach chleba wypełnia niewielką piekarnię zaopatrującą karczmę i strażników przy bramach.",
            "exits":{},
        },
        "healer_house": {
            "zone":"Miasto Dusz", "name":"Dom Uzdrowicielki",
            "desc":"Cicha izba z łóżkami, bandażami i suszonymi ziołami służy rannym podróżnym oraz mieszkańcom.",
            "exits":{},
        },
        "residential_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Domów",
            "desc":"Szereg niewielkich kamiennych domów otacza spokojną ulicę z ławkami i studzienkami deszczowymi.",
            "exits":{},
        },
        "well_square": {
            "zone":"Miasto Dusz", "name":"Plac Starej Studni",
            "desc":"Mały plac skupia mieszkańców południowej dzielnicy. Pośrodku stoi głęboka, nadal używana studnia.",
            "exits":{},
        },
        "courier_office": {
            "zone":"Miasto Dusz", "name":"Poczta i Biuro Kurierów",
            "desc":"Posłańcy sortują listy, paczki i meldunki przeznaczone dla portu, straży oraz odległych posterunków.",
            "exits":{},
        },
        "dockside_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Portowa",
            "desc":"Szeroka droga biegnie wzdłuż magazynów i nabrzeża. Słychać liny, dzwonki statków i nawoływania tragarzy.",
            "exits":{},
        },
        "harbor_warehouse": {
            "zone":"Miasto Dusz", "name":"Magazyn Portowy",
            "desc":"Skrzynie, beczki i zaplombowane pakunki czekają na odbiór przez kupców oraz rybaków.",
            "exits":{},
        },
        "ropewalk": {
            "zone":"Miasto Dusz", "name":"Powroźnia",
            "desc":"Długi warsztat służy do skręcania lin dla statków, wozów i miejskich dźwigów.",
            "exits":{},
        },
        "shipwright_yard": {
            "zone":"Miasto Dusz", "name":"Stocznia Miejska",
            "desc":"Na drewnianych podporach stoi naprawiany kuter. Szkutnicy wymieniają deski i uszczelniają kadłub.",
            "exits":{},
        },
        "scholar_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Uczonych",
            "desc":"Spokojna uliczka łączy Plac Treningowy z domami skrybów, nauczycieli i kartografów.",
            "exits":{},
        },
        "cartographer_house": {
            "zone":"Miasto Dusz", "name":"Pracownia Kartografa",
            "desc":"Ściany pokrywają mapy traktów, ruin, bagien i gór. Na dużym stole powstają nowe szkice szlaków.",
            "exits":{},
        },
        "city_watch_office": {
            "zone":"Miasto Dusz", "name":"Biuro Patroli Miejskich",
            "desc":"Małe biuro przy północnej dzielnicy zbiera zgłoszenia mieszkańców i rozdziela krótkie patrole poza murami.",
            "exits":{},
        },
    }
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, (), city_rooms)

    def connect(a, da, b, db):
        _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (a,), "exits", {})[da] = b
        _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (b,), "exits", {})[db] = a

    # Dzielnica rzemieślnicza przy Kuźni.
    connect("forge", "east", "artisan_lane", "west")
    connect("artisan_lane", "north", "tailor_workshop", "south")
    connect("artisan_lane", "east", "carpenter_workshop", "west")
    connect("artisan_lane", "south", "mason_yard", "north")
    connect("carpenter_workshop", "east", "leatherworker_workshop", "west")
    connect("carpenter_workshop", "south", "potter_workshop", "north")
    connect("potter_workshop", "west", "mason_yard", "east")

    # Południowa dzielnica mieszkalna.
    connect("south_street", "west", "lantern_alley", "east")
    connect("lantern_alley", "west", "residential_lane", "east")
    connect("lantern_alley", "south", "city_bakery", "north")
    connect("residential_lane", "west", "well_square", "east")
    connect("residential_lane", "south", "healer_house", "north")
    connect("well_square", "south", "courier_office", "north")
    connect("courier_office", "east", "healer_house", "west")

    # Dzielnica portowa.
    connect("harbor", "north", "dockside_lane", "south")
    connect("dockside_lane", "west", "harbor_warehouse", "east")
    connect("dockside_lane", "east", "ropewalk", "west")
    connect("ropewalk", "east", "shipwright_yard", "west")
    connect("shipwright_yard", "south", "dockside_lane", "north")

    # Uczeni i patrole.
    connect("training", "east", "scholar_lane", "west")
    connect("scholar_lane", "east", "cartographer_house", "west")
    connect("scholar_lane", "south", "city_watch_office", "north")

    outskirts = {
        "city_outskirts_gate": ("Przedbramie Południowe", "Droga tuż za murami rozdziela się na sad, pola i trakt prowadzący ku Łąkom."),
        "caravan_road": ("Droga Karawan", "Ubity trakt nosi ślady kół, końskich kopyt i pieszych podróżnych zmierzających do miasta."),
        "orchard_path": ("Droga Sadowa", "Niska kamienna ściana oddziela drogę od starych sadów należących do mieszkańców miasta."),
        "old_orchard": ("Stary Sad", "Pomiędzy jabłoniami i gruszami stoją porzucone kosze. Krzewy przyciągają drobną zwierzynę."),
        "mill_road": ("Droga do Młyna", "Boczna droga biegnie w stronę starego młyna i zakola rzeki."),
        "old_mill": ("Stary Młyn", "Koło wodne obraca się powoli przy kamiennym młynie, który nadal obsługuje okolicznych rolników."),
        "riverside_path": ("Ścieżka Nad Rzeką", "Wąska ścieżka ciągnie się wzdłuż trzcin i płytkiego brzegu rzeki."),
        "east_fields": ("Wschodnie Pola", "Niskie pola uprawne i miedze ciągną się aż do łagodnych wzgórz."),
        "shepherd_hill": ("Wzgórze Pasterzy", "Z trawiastego wzgórza widać mury miasta, Łąki i fragment Starego Traktu."),
        "roadside_shrine": ("Kapliczka Podróżnych", "Mała kamienna kapliczka stoi przy skrzyżowaniu dróg. Podróżni zostawiają tu świece i drobne monety."),
        "drainage_ditch": ("Stary Rów Obronny", "Wyschnięty fragment dawnego rowu otacza południową część murów i tworzy osłoniętą ścieżkę."),
        "abandoned_storehouse": ("Opuszczony Magazyn", "Zamknięty kiedyś magazyn ma wyłamane drzwi i ślady nieproszonych gości."),
        "charcoal_camp": ("Obóz Węglarzy", "Dymiące mielerze stoją przy skraju zagajnika. Węglarze wracają tu tylko w dzień."),
        "outer_wall_path": ("Ścieżka Pod Murami", "Patrolowa droga prowadzi wzdłuż zewnętrznej strony miejskich murów ku północnemu posterunkowi."),
    }
    for rid, (name, desc) in outskirts.items():
        _catalog_mut.catalog_assign({"zone":"Przedmieścia Miasta Dusz", "name":name, "desc":desc, "exits":{}}, 'ROOMS', ROOMS, (rid,))

    # Wstaw przedmieścia pomiędzy miasto i Łąki oraz dodaj boczną pętlę do Starego Traktu.
    _catalog_mut.catalog_assign("city_outskirts_gate", 'ROOMS', ROOMS, ("south_gate", "exits", "south"))
    _catalog_mut.catalog_assign("caravan_road", 'ROOMS', ROOMS, ("meadow", "exits", "north"))
    connect("south_gate", "south", "city_outskirts_gate", "north")
    connect("city_outskirts_gate", "south", "caravan_road", "north")
    connect("caravan_road", "south", "meadow", "north")
    connect("city_outskirts_gate", "west", "orchard_path", "east")
    connect("orchard_path", "west", "old_orchard", "east")
    connect("orchard_path", "south", "mill_road", "north")
    connect("mill_road", "west", "old_mill", "east")
    connect("mill_road", "south", "riverside_path", "north")
    connect("riverside_path", "east", "caravan_road", "west")
    connect("city_outskirts_gate", "east", "outer_wall_path", "west")
    connect("outer_wall_path", "south", "east_fields", "north")
    connect("east_fields", "south", "shepherd_hill", "north")
    connect("shepherd_hill", "west", "roadside_shrine", "east")
    connect("roadside_shrine", "north", "caravan_road", "east")
    connect("east_fields", "east", "drainage_ditch", "west")
    connect("drainage_ditch", "south", "abandoned_storehouse", "north")
    connect("abandoned_storehouse", "west", "charcoal_camp", "east")
    connect("charcoal_camp", "north", "shepherd_hill", "south")
    connect("outer_wall_path", "north", "north_watchpost", "south")


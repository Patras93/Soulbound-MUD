# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def build_v012_living_waters_and_meadows():
    # --------------------------------------------------------
    # WYBRZEŻE, MORZE I OCEAN
    # --------------------------------------------------------
    water_rooms = {
        "coastal_cove": ("Wybrzeże", "Spokojna Zatoka", "Osłonięta zatoka o łagodnym nurcie. Płytka woda sprzyja rybom przybrzeżnym."),
        "rocky_shore": ("Wybrzeże", "Skalisty Brzeg", "Poszarpane skały schodzą w słoną wodę. Między głazami tworzą się głębsze rynny łowiskowe."),
        "river_estuary": ("Wybrzeże", "Ujście Srebrnej Rzeki", "Słodka i słona woda mieszają się w szerokim ujściu. Łowisko ma charakter estuarium."),
        "salt_marsh": ("Wybrzeże", "Słone Mokradła", "Płytkie kanały pływowe przecinają kępy słonolubnych traw."),
        "tidal_flats": ("Wybrzeże", "Płycizny Pływowe", "Rozległe płycizny zmieniają się wraz z przypływem. Ryby podchodzą tu blisko brzegu."),
        "coastal_lagoon": ("Wybrzeże", "Laguna Przybrzeżna", "Ciepła laguna jest częściowo odcięta od morza pasem skał i piasku."),
        "kelp_bay": ("Wybrzeże", "Zatoka Wodorostów", "Gęste pasma wodorostów falują pod powierzchnią i kryją wiele morskich gatunków."),
        "outer_reef": ("Ocean", "Zewnętrzna Rafa", "Rafa leży już poza spokojnym pasem wybrzeża. Woda jest głęboka i przejrzysta."),
        "bluewater_channel": ("Ocean", "Błękitny Kanał", "Silny prąd oceaniczny tworzy naturalny szlak dużych ryb pelagicznych."),
        "ocean_shelf": ("Ocean", "Krawędź Szelfu", "Dno gwałtownie opada. To przejście między wodami przybrzeżnymi a otwartym oceanem."),
        "deep_ocean_buoy": ("Ocean", "Boja Głębokiego Oceanu", "Samotna boja wyznacza dalekie łowisko na bardzo głębokiej wodzie."),
        "trench_edge": ("Ocean", "Krawędź Rowu Oceanicznego", "Ciemna toń zaczyna się tuż za krawędzią podmorskiego urwiska."),
        "storm_current": ("Ocean", "Prąd Burzowy", "Niespokojny prąd niesie chłodniejszą wodę i przyciąga silne oceaniczne drapieżniki."),
    }
    for rid, (zone, name, desc) in water_rooms.items():
        _v012_add_room(rid, zone, name, desc)

    _v012_connect("sea_pier", "north", "coastal_cove", "south")
    _v012_connect("coastal_cove", "east", "rocky_shore", "west")
    _v012_connect("rocky_shore", "north", "river_estuary", "south")
    _v012_connect("river_estuary", "west", "salt_marsh", "east")
    _v012_connect("salt_marsh", "south", "coastal_cove", "north")
    _v012_connect("sea_pier", "south", "tidal_flats", "north")
    _v012_connect("tidal_flats", "east", "coastal_lagoon", "west")
    _v012_connect("coastal_lagoon", "north", "rocky_shore", "south")
    _v012_connect("tidal_flats", "south", "kelp_bay", "north")
    _v012_connect("kelp_bay", "east", "coastal_lagoon", "south")

    _v012_connect("ocean_platform", "north", "outer_reef", "south")
    _v012_connect("outer_reef", "east", "bluewater_channel", "west")
    _v012_connect("bluewater_channel", "south", "ocean_shelf", "north")
    _v012_connect("ocean_platform", "south", "ocean_shelf", "west")
    _v012_connect("bluewater_channel", "east", "deep_ocean_buoy", "west")
    _v012_connect("deep_ocean_buoy", "south", "trench_edge", "north")
    _v012_connect("trench_edge", "west", "storm_current", "east")
    _v012_connect("storm_current", "north", "ocean_shelf", "south")

    sea_ids = {
        "coastal_cove", "rocky_shore", "river_estuary", "salt_marsh",
        "tidal_flats", "coastal_lagoon", "kelp_bay",
    }
    ocean_ids = {
        "outer_reef", "bluewater_channel", "ocean_shelf",
        "deep_ocean_buoy", "trench_edge", "storm_current",
    }
    SEA_FISHING_ROOMS.update(sea_ids)
    OCEAN_FISHING_ROOMS.update(ocean_ids)
    MARINE_FISHING_ROOMS.update(sea_ids | ocean_ids)
    FISHING_ROOMS.update(sea_ids | ocean_ids)
    V012_NEW_FISHING_ROOMS.update(sea_ids | ocean_ids)

    # --------------------------------------------------------
    # RZEKA, JEZIORO, STARORZECZE I STAW ŁĄKOWY
    # --------------------------------------------------------
    fresh_rooms = {
        "willow_bend": ("Dolina Rzeki", "Wierzbowe Zakole", "Rzeka zwalnia pod starymi wierzbami i tworzy głębokie stanowiska przy brzegu."),
        "river_rapids": ("Dolina Rzeki", "Srebrne Bystrza", "Szybki nurt pieni się między kamieniami. Żyją tu gatunki lubiące natlenioną wodę."),
        "reed_bank": ("Dolina Rzeki", "Trzcinowy Brzeg", "Szeroki pas trzcin osłania spokojniejsze zatoczki rzecznego brzegu."),
        "river_ford": ("Dolina Rzeki", "Kamienny Bród", "Płytki bród przecina rzekę, a za głazami tworzą się naturalne kieszenie dla ryb."),
        "spring_creek": ("Dolina Rzeki", "Źródlany Potok", "Chłodny potok wpada do rzeki. Woda jest czysta i szybka."),
        "oxbow_pool": ("Dolina Rzeki", "Stare Starorzecze", "Odcięte zakole tworzy ciche, zarośnięte łowisko o niemal jeziorowym charakterze."),
        "reed_lake_bank": ("Srebrne Jezioro", "Trzcinowy Brzeg Jeziora", "Płytki brzeg jeziora porastają trzciny i lilie wodne."),
        "quiet_cove": ("Srebrne Jezioro", "Cicha Zatoka Jeziora", "Osłonięta zatoka ma spokojną wodę i głębszy środek."),
        "southern_lake_bank": ("Srebrne Jezioro", "Południowy Brzeg Jeziora", "Kamienisto-piaszczysty brzeg otwiera dostęp do szerokiej tafli Srebrnego Jeziora."),
        "pebble_lake_bank": ("Srebrne Jezioro", "Żwirowy Brzeg Jeziora", "Dno opada tu równomiernie, a żwir przyciąga inne gatunki niż trzcinowe zatoki."),
        "fisher_inlet": ("Srebrne Jezioro", "Zatoczka Rybaków", "Mała zatoczka z resztkami starego pomostu jest wygodnym miejscem do spokojnego łowienia."),
        "deepwater_pier": ("Srebrne Jezioro", "Pomost Głębokiej Toni", "Długi pomost sięga nad najgłębszą część jeziora dostępną z brzegu."),
        "meadow_pond": ("Łąki", "Staw pośród Łąk", "Niewielki staw otaczają miękkie trawy, mięta i owady. To spokojne łowisko jeziorno-stawowe."),
    }
    for rid, (zone, name, desc) in fresh_rooms.items():
        _v012_add_room(rid, zone, name, desc)

    _v012_connect("riverbank", "north", "willow_bend", "south")
    _v012_connect("willow_bend", "east", "river_rapids", "west")
    _v012_connect("river_rapids", "south", "stone_bridge", "north")
    _v012_connect("riverbank", "south", "reed_bank", "north")
    _v012_connect("reed_bank", "east", "river_ford", "west")
    _v012_connect("river_ford", "north", "stone_bridge", "south")
    _v012_connect("willow_bend", "west", "spring_creek", "east")
    _v012_connect("spring_creek", "south", "reed_bank", "west")
    _v012_connect("reed_bank", "south", "oxbow_pool", "north")

    _v012_connect("lake_shore", "east", "reed_lake_bank", "west")
    _v012_connect("reed_lake_bank", "south", "quiet_cove", "north")
    _v012_connect("quiet_cove", "west", "southern_lake_bank", "east")
    _v012_connect("southern_lake_bank", "north", "lake_shore", "south")
    _v012_connect("lake_shore", "west", "pebble_lake_bank", "east")
    _v012_connect("pebble_lake_bank", "south", "fisher_inlet", "north")
    _v012_connect("fisher_inlet", "east", "southern_lake_bank", "west")
    _v012_connect("quiet_cove", "east", "deepwater_pier", "west")
    _v012_connect("deepwater_pier", "north", "reed_lake_bank", "east")

    river_ids = {
        "willow_bend", "river_rapids", "reed_bank", "river_ford", "spring_creek",
    }
    lake_ids = {
        "oxbow_pool", "reed_lake_bank", "quiet_cove", "southern_lake_bank",
        "pebble_lake_bank", "fisher_inlet", "deepwater_pier", "meadow_pond",
    }
    RIVER_FISHING_ROOMS.update(river_ids)
    LAKE_FISHING_ROOMS.update(lake_ids)
    FRESHWATER_FISHING_ROOMS.update(river_ids | lake_ids)
    FISHING_ROOMS.update(river_ids | lake_ids)
    V012_NEW_FISHING_ROOMS.update(river_ids | lake_ids)

    # --------------------------------------------------------
    # ROZLEGŁE ŁĄKI - kilka typów siedlisk połączonych pętlami
    # --------------------------------------------------------
    meadow_rooms = {
        "wildflower_basin": ("Kotlina Dzikich Kwiatów", "Łagodna niecka pełna rumianku, lawendy, krwawnika i wysokich kwiatów."),
        "butterfly_field": ("Łąka Motyli", "Ciepła polana przyciąga chmary motyli i drobną zwierzynę. Rosną tu lekkie zioła łąkowe."),
        "heather_field": ("Wrzosowisko", "Purpurowe wrzosy pokrywają suchszy fragment łąk, gdzie roślinność jest rzadsza, ale bardziej aromatyczna."),
        "wind_meadow": ("Wietrzna Łąka", "Wysoka trawa ugina się pod stałym wiatrem. Między kępami rosną odporne zioła."),
        "clover_field": ("Pole Koniczyny", "Niskie, miękkie trawy i koniczyna tworzą spokojny teren dla drobnych zwierząt."),
        "tall_grass_field": ("Morze Wysokich Traw", "Trawa sięga niemal do pasa i tworzy naturalne ścieżki między pagórkami."),
        "wet_meadow": ("Mokra Łąka", "Grunt jest nasiąknięty wodą z rzeki. Mięta, melisa i rośliny wilgociolubne rosną bardzo gęsto."),
        "reed_meadow": ("Trzcinowa Łąka", "Łąka przechodzi w pas trzcin i niewielkich oczek wodnych."),
        "marshy_meadow": ("Podmokła Łąka", "Między trawami błyszczą małe rozlewiska. To przejście między łąką a mokradłem."),
        "creek_meadow": ("Łąka Nad Potokiem", "Wąski potok przecina zielony teren, tworząc wilgotne stanowiska zielarskie."),
        "herb_ridge": ("Zielarska Grań", "Nieznacznie wyniesiony teren jest suchszy i nasłoneczniony. Rosną tu szałwia i późniejsze zioła."),
        "sage_hollow": ("Niecka Szałwii", "Ciepła niecka pachnie szałwią i gorzkimi roślinami leczniczymi."),
        "valerian_lowland": ("Nizina Waleriany", "Chłodniejsza, wilgotna dolinka sprzyja walerianie i roślinom późniejszej progresji."),
        "ginseng_hill": ("Wzgórze Żeń-szenia", "Stoki wzgórza są zacienione przez pojedyncze drzewa. Wśród korzeni można znaleźć cenne zioła."),
        "moon_meadow": ("Księżycowa Łąka", "Jasne kwiaty pozostają otwarte nawet nocą. To jeden z bardziej wymagających terenów Zielarstwa."),
        "old_stone_meadow": ("Łąka Starych Kamieni", "Krąg omszałych głazów dzieli łąkę na kilka naturalnych polan i ścieżek."),
        "orchard_meadow": ("Łąka Przy Sadzie", "Trawiaste zbocze łączy dzikie łąki ze starymi sadami przedmieść."),
    }
    for rid, (name, desc) in meadow_rooms.items():
        _v012_add_room(rid, "Łąki", name, desc)
        HERBALISM_ROOMS.add(rid)
        MEADOW_HERBALISM_ROOMS.add(rid)
        V012_NEW_MEADOW_ROOMS.add(rid)

    _v012_connect("flower_meadow", "south", "wildflower_basin", "north")
    _v012_connect("wildflower_basin", "west", "butterfly_field", "east")
    _v012_connect("butterfly_field", "south", "old_stone_meadow", "north")
    _v012_connect("wildflower_basin", "east", "heather_field", "west")
    _v012_connect("heather_field", "east", "wind_meadow", "west")
    _v012_connect("wind_meadow", "south", "clover_field", "north")
    _v012_connect("clover_field", "south", "mint_meadow", "north")
    _v012_connect("heather_field", "north", "tall_grass_field", "south")
    _v012_connect("tall_grass_field", "east", "old_stone_meadow", "west")
    _v012_connect("old_stone_meadow", "south", "wind_meadow", "north")

    _v012_connect("mint_meadow", "south", "wet_meadow", "north")
    _v012_connect("wet_meadow", "east", "reed_meadow", "west")
    _v012_connect("reed_meadow", "south", "marshy_meadow", "north")
    _v012_connect("marshy_meadow", "west", "herb_ridge", "east")
    _v012_connect("lakeside_meadow", "west", "creek_meadow", "east")
    _v012_connect("creek_meadow", "south", "meadow_pond", "north")
    _v012_connect("marshy_meadow", "south", "valerian_lowland", "north")

    _v012_connect("creek_meadow", "north", "wet_meadow", "south")
    _v012_connect("herb_ridge", "south", "sage_hollow", "north")
    _v012_connect("sage_hollow", "east", "valerian_lowland", "west")
    _v012_connect("sage_hollow", "south", "ginseng_hill", "north")
    _v012_connect("ginseng_hill", "east", "moon_meadow", "west")
    _v012_connect("moon_meadow", "north", "valerian_lowland", "south")
    _v012_connect("tall_grass_field", "north", "orchard_meadow", "south")
    if "old_orchard" in ROOMS:
        _v012_connect("orchard_meadow", "north", "old_orchard", "south")

    HERBALISM_ROOMS.add("meadow_pond")
    MEADOW_HERBALISM_ROOMS.add("meadow_pond")
    V012_WATER_MEADOW_ROOMS.update({
        "wet_meadow", "reed_meadow", "marshy_meadow", "creek_meadow", "meadow_pond",
    })


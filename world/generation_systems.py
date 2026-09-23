from data import catalog_mutations as _catalog_mut


def mob_can_auto_aggro(_template=None):
    """Jedno źródło prawdy dla globalnej polityki aggro.

    Funkcja celowo zawsze zwraca False. Zostawiamy ją jawnie w kodzie,
    aby przyszłe systemy biomów/roamingu nie wprowadziły auto-ataku bokiem.
    """
    return False


V012_NEW_FISHING_ROOMS = set()
V012_NEW_MEADOW_ROOMS = set()
V012_WATER_MEADOW_ROOMS = set()
V012_MEADOW_HERB_GROUP = {}
V012_HERB_ECOLOGY_POOLS = {}


def _v012_connect(a, direction_a, b, direction_b):
    _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (a,), "exits", {})[direction_a] = b
    _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (b,), "exits", {})[direction_b] = a


def _v012_add_room(room_id, zone, name, desc):
    _catalog_mut.catalog_assign({
        "zone": zone,
        "name": name,
        "desc": desc,
        "exits": {},
    }, 'ROOMS', ROOMS, (room_id,))


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


build_v012_living_waters_and_meadows()

# Opisy typów wody używane przez komendę łowienia/atlas.
FISHING_WATER_TYPE_OVERRIDES.update({
    "coastal_cove": "Zatoka morska", "rocky_shore": "Skalisty brzeg morski",
    "river_estuary": "Estuarium", "salt_marsh": "Słone mokradła",
    "tidal_flats": "Płycizny pływowe", "coastal_lagoon": "Laguna",
    "kelp_bay": "Zatoka wodorostów", "outer_reef": "Rafa oceaniczna",
    "bluewater_channel": "Otwarty ocean", "ocean_shelf": "Krawędź szelfu",
    "deep_ocean_buoy": "Głęboki ocean", "trench_edge": "Rów oceaniczny",
    "storm_current": "Prąd oceaniczny", "willow_bend": "Zakole rzeki",
    "river_rapids": "Bystrza", "reed_bank": "Trzcinowy brzeg rzeki",
    "river_ford": "Bród rzeczny", "spring_creek": "Potok",
    "oxbow_pool": "Starorzecze", "reed_lake_bank": "Trzcinowy brzeg jeziora",
    "quiet_cove": "Zatoka jeziora", "southern_lake_bank": "Brzeg jeziora",
    "pebble_lake_bank": "Żwirowy brzeg jeziora", "fisher_inlet": "Zatoczka jeziora",
    "deepwater_pier": "Głęboka toń jeziora", "meadow_pond": "Staw łąkowy",
})

# Ekologia łowisk: preferencja zmienia charakter stanowiska, ale nigdy
# nie omija levelu Wędki. Gdy filtr byłby pusty, system wraca do normalnej puli.
FISHING_ECOLOGY_PREFERRED_IDS.update({
    "coastal_cove": {"sand_eel", "world_bonefish", "world_common_snook", "world_pompano", "world_yellowtail_snapper"},
    "rocky_shore": {"world_sheepshead", "world_red_grouper", "world_european_conger", "world_scorpionfish", "world_wolffish"},
    "river_estuary": {"world_atlantic_tarpon", "world_red_drum", "world_black_drum", "world_striped_bass", "world_atlantic_croaker"},
    "salt_marsh": {"world_bonefish", "world_common_snook", "world_red_drum", "world_mangrove_snapper", "world_lane_snapper"},
    "tidal_flats": {"sand_eel", "world_bonefish", "world_permit_fish", "world_pompano", "world_atlantic_croaker"},
    "coastal_lagoon": {"world_common_snook", "world_red_drum", "world_yellowtail_snapper", "world_mangrove_snapper", "world_queen_triggerfish"},
    "kelp_bay": {"world_atlantic_mackerel", "world_horse_mackerel", "world_john_dory", "world_wolffish", "world_atlantic_halibut_world"},
    "outer_reef": {"reef_shark", "world_manta_ray", "world_spotted_eagle_ray", "world_blue_marlin", "world_whale_shark"},
    "bluewater_channel": {"bluefin_tuna", "yellowfin_tuna", "world_skipjack_tuna", "world_blue_marlin", "world_white_marlin"},
    "ocean_shelf": {"world_escolar", "world_oilfish", "world_lancetfish", "world_blue_shark", "world_common_thresher"},
    "deep_ocean_buoy": {"world_oarfish", "world_greenland_shark", "world_goblin_shark", "world_orange_roughy", "world_coelacanth_world"},
    "trench_edge": {"world_goblin_shark", "world_megamouth_shark", "world_bluntnose_sixgill", "world_frilled_shark", "world_coelacanth_world"},
    "storm_current": {"mako_shark", "tiger_shark", "world_blue_shark", "world_oceanic_whitetip_shark", "world_common_thresher"},
    "willow_bend": {"dace", "chub", "river_carp", "barbel", "ide", "world_freshwater_drum"},
    "river_rapids": {"grayling", "salmon", "brown_trout", "river_taimen", "world_rainbow_trout", "world_chinook_salmon"},
    "reed_bank": {"river_perch", "river_carp", "burbot", "river_catfish", "world_channel_catfish", "world_wels_catfish"},
    "river_ford": {"dace", "common_nase", "barbel", "grayling", "world_mahseer", "world_golden_dorado"},
    "spring_creek": {"stone_loach", "brown_trout", "silver_trout", "golden_trout", "world_brook_trout", "world_cutthroat_trout"},
    "oxbow_pool": {"crucian_carp", "tench", "pike", "freshwater_eel", "world_largemouth_bass", "world_bluegill"},
    "reed_lake_bank": {"lake_roach", "rudd", "crucian_carp", "tench", "lake_perch", "world_bluegill"},
    "quiet_cove": {"bream", "tench", "pike", "zander", "freshwater_eel", "world_walleye"},
    "southern_lake_bank": {"lake_roach", "bream", "lake_perch", "vendace", "world_yellow_perch", "world_cisco"},
    "pebble_lake_bank": {"whitefish", "lake_char", "lake_trout", "world_round_whitefish", "world_marble_trout"},
    "fisher_inlet": {"rudd", "crucian_carp", "bream", "tench", "world_pumpkinseed", "world_black_crappie"},
    "deepwater_pier": {"pike", "zander", "lake_trout", "mirror_sturgeon", "world_lake_sturgeon", "world_taimen"},
    "meadow_pond": {"crucian_carp", "tench", "rudd", "lake_roach", "world_bluegill", "world_pumpkinseed"},
})

# Lokalne profile ziół. Mają 65% szansy wpłynąć na zbiór; pozostałe 35%
# korzysta z pełnej, levelowanej puli świata, więc progresja 1-600 nadal działa.
V012_HERB_ECOLOGY_POOLS.update({
    "wildflower_basin": ((1,"chamomile"),(1,"lavender"),(15,"yarrow"),(25,"lemon_balm"),(40,"sage")),
    "butterfly_field": ((1,"chamomile"),(1,"mint"),(10,"lavender"),(20,"yarrow"),(35,"lemon_balm")),
    "heather_field": ((15,"lavender"),(30,"sage"),(45,"valerian"),(70,"ginseng")),
    "wind_meadow": ((1,"nettle"),(1,"chamomile"),(15,"yarrow"),(30,"sage"),(50,"valerian")),
    "clover_field": ((1,"nettle"),(1,"mint"),(10,"chamomile"),(20,"lemon_balm"),(35,"yarrow")),
    "tall_grass_field": ((1,"nettle"),(15,"yarrow"),(25,"lemon_balm"),(40,"sage"),(60,"valerian")),
    "wet_meadow": ((1,"mint"),(10,"lemon_balm"),(30,"valerian"),(55,"ginseng"),(80,"moonflower")),
    "reed_meadow": ((1,"mint"),(15,"lemon_balm"),(35,"sage"),(60,"ginseng"),(90,"star_moss")),
    "marshy_meadow": ((10,"lemon_balm"),(30,"valerian"),(50,"ginseng"),(70,"nightshade"),(100,"moonflower")),
    "creek_meadow": ((1,"mint"),(10,"chamomile"),(25,"lemon_balm"),(45,"valerian"),(75,"ginseng")),
    "meadow_pond": ((1,"mint"),(20,"lemon_balm"),(40,"valerian"),(70,"ginseng"),(100,"star_moss")),
    "herb_ridge": ((20,"lavender"),(35,"sage"),(50,"valerian"),(70,"ginseng"),(90,"mandrake")),
    "sage_hollow": ((30,"sage"),(45,"valerian"),(65,"ginseng"),(85,"nightshade"),(110,"mandrake")),
    "valerian_lowland": ((40,"valerian"),(60,"ginseng"),(80,"nightshade"),(100,"moonflower"),(120,"soulroot")),
    "ginseng_hill": ((50,"ginseng"),(75,"nightshade"),(95,"mandrake"),(120,"soulroot"),(150,"phoenix_leaf")),
    "moon_meadow": ((70,"moonflower"),(100,"soulroot"),(130,"star_moss"),(160,"phoenix_leaf"),(190,"astral_lotus")),
    "old_stone_meadow": ((10,"yarrow"),(25,"lavender"),(45,"sage"),(70,"valerian"),(100,"ginseng")),
    "orchard_meadow": ((1,"chamomile"),(10,"mint"),(20,"yarrow"),(35,"lemon_balm"),(50,"sage")),
})
V012_MEADOW_HERB_GROUP.update({rid: ("water" if rid in V012_WATER_MEADOW_ROOMS else "meadow") for rid in V012_NEW_MEADOW_ROOMS})
V012_MEADOW_HERB_GROUP["meadow_pond"] = "water"

# Atlas surowców zna nowe łąki i pokazuje realne wymagania Sierpa.
for _rid, _rows in V012_HERB_ECOLOGY_POOLS.items():
    HERB_ATLAS_ROOM_MIN_LEVELS.setdefault(_rid, {})
    for _level, _herb_id in _rows:
        if _herb_id in ITEMS:
            previous = HERB_ATLAS_ROOM_MIN_LEVELS[_rid].get(_herb_id)
            HERB_ATLAS_ROOM_MIN_LEVELS[_rid][_herb_id] = int(_level if previous is None else min(previous, _level))

# Dodatkowa fauna łąkowa. To zabijalne moby, ale podlegają globalnej zasadzie
# PASSIVE WORLD i nigdy nie inicjują walki bez decyzji gracza.
_catalog_mut.catalog_update_path('MOB_TEMPLATES', MOB_TEMPLATES, (), {
    "meadow_hare": {"name":"Zając Łąkowy","max_hp":32,"damage":4,"damage_type":"physical","silver":8,"gold":0,"mithril":0,"stat_reward":12,"soul_reward":55,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_fox": {"name":"Lis Polny","max_hp":48,"damage":5,"damage_type":"physical","silver":13,"gold":0,"mithril":0,"stat_reward":18,"soul_reward":82,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_deer": {"name":"Jeleń Łąkowy","max_hp":72,"damage":6,"damage_type":"physical","silver":20,"gold":0,"mithril":0,"stat_reward":24,"soul_reward":112,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_stag": {"name":"Stary Jeleń","max_hp":105,"damage":8,"damage_type":"physical","silver":31,"gold":0,"mithril":0,"stat_reward":34,"soul_reward":165,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_grass_wisp": {"name":"Błędny Ognik Traw","max_hp":88,"damage":8,"damage_type":"magic","silver":28,"gold":0,"mithril":0,"stat_reward":31,"soul_reward":155,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_field_serpent": {"name":"Wąż Polny","max_hp":58,"damage":6,"damage_type":"physical","silver":16,"gold":0,"mithril":0,"stat_reward":21,"soul_reward":98,"drops":{},"quest_target":None,"auto_aggro":False},
})

MOB_SPAWNS.extend([
    ("wildflower_basin","meadow_hare"), ("wildflower_basin","meadow_deer"),
    ("butterfly_field","meadow_hare"), ("butterfly_field","meadow_fox"),
    ("heather_field","meadow_fox"), ("heather_field","meadow_field_serpent"),
    ("wind_meadow","meadow_deer"), ("wind_meadow","meadow_field_wolf"),
    ("clover_field","meadow_hare"), ("clover_field","meadow_deer"),
    ("tall_grass_field","meadow_field_serpent"), ("tall_grass_field","meadow_wild_boar"),
    ("wet_meadow","meadow_giant_wasp"), ("wet_meadow","meadow_hare"),
    ("reed_meadow","meadow_field_serpent"), ("reed_meadow","meadow_wild_boar"),
    ("marshy_meadow","meadow_field_serpent"), ("marshy_meadow","meadow_giant_wasp"),
    ("creek_meadow","meadow_deer"), ("creek_meadow","meadow_fox"),
    ("herb_ridge","meadow_stag"), ("herb_ridge","meadow_field_wolf"),
    ("sage_hollow","meadow_grass_wisp"), ("sage_hollow","meadow_wild_boar"),
    ("valerian_lowland","meadow_grass_wisp"), ("valerian_lowland","meadow_field_serpent"),
    ("ginseng_hill","meadow_stag"), ("ginseng_hill","meadow_field_wolf"),
    ("moon_meadow","meadow_grass_wisp"), ("moon_meadow","meadow_stag"),
    ("old_stone_meadow","meadow_deer"), ("old_stone_meadow","meadow_wild_boar"),
    ("orchard_meadow","meadow_hare"), ("orchard_meadow","meadow_fox"),
    ("meadow_pond","meadow_hare"),
])

# W istniejących definicjach również zapisujemy intencję. Mechanika walki i tak
# respektuje GLOBAL_MOB_AUTO_AGGRO_ENABLED=False, ale metadane ułatwiają audyt.
for _template in MOB_TEMPLATES.values():
    if isinstance(_template, dict):
        _template["auto_aggro"] = False

GUIDE_DESTINATION_ALIASES.update({
    "zatoka": "coastal_cove", "spokojna zatoka": "coastal_cove",
    "ujscie rzeki": "river_estuary", "estuarium": "river_estuary",
    "laguna": "coastal_lagoon", "zatoka wodorostow": "kelp_bay",
    "rafa": "outer_reef", "rafa oceaniczna": "outer_reef",
    "gleboki ocean": "deep_ocean_buoy", "row oceaniczny": "trench_edge",
    "starorzecze": "oxbow_pool", "staw": "meadow_pond", "staw lakowy": "meadow_pond",
    "wrzosowisko": "heather_field", "mokra laka": "wet_meadow",
    "trzcinowa laka": "reed_meadow", "ksiezycowa laka": "moon_meadow",
    "laka motyli": "butterfly_field", "dzikie kwiaty": "wildflower_basin",
})

HELP_TOPICS["pasywny_swiat"] = [
    "GLOBALNA ZASADA: żaden zwykły mob ani boss w Soulbound nie rozpoczyna walki automatycznie.",
    "Moby mogą chodzić między lokacjami i mogą wejść do pokoju gracza, ale samo spotkanie nigdy nie uruchamia combat loopa.",
    "Walkę rozpoczyna gracz komendą atakuj <mob> / k <mob> albo świadomą ofensywną akcją na wybranym celu.",
    "Po rozpoczęciu walki przeciwnik normalnie kontratakuje według timera realtime aż do śmierci, ucieczki lub zakończenia starcia.",
    "Zasada dotyczy całego świata: łąk, dziczy, ruin, jaskiń, krypt, wież, bossów, endgame i przyszłych biomów.",
]
HELP_TOPICS["akweny"] = [
    "v0.12.0 rozbudowuje Wędkarstwo przestrzennie: rzeki, potoki, starorzecze, jeziorne zatoki, staw, wybrzeże, estuarium, lagunę, morze, rafę, szelf i głęboki ocean.",
    "Różne stanowiska tego samego typu wody preferują inne gatunki, ale nigdy nie omijają wymaganego levelu Wędki.",
    "Nowe łowiska tworzą pętle i alternatywne trasy zamiast pojedynczego liniowego pomostu.",
    "Komenda atlas / dziennik ryb nadal pokazuje progresję gatunków, a opis łowiska podaje typ akwenu.",
]
HELP_TOPICS["rozlegle_laki"] = [
    "v0.12.0 rozbudowuje Łąki o suche, kwietne, wrzosowe, wysokotrawiaste, mokre i późniejsze zielarskie siedliska.",
    "Nowe łąki mają własne preferowane zestawy ziół, ale pełna progresja Zielarstwa 1-600 pozostaje zachowana.",
    "Na łąkach żyją i przemieszczają się moby, lecz zgodnie z zasadą PASSIVE WORLD nigdy nie atakują pierwsze.",
    "Staw pośród Łąk jest jednocześnie łowiskiem i terenem zielarskim.",
]
HELP_TOPIC_ALIASES.update({
    "pasywny swiat":"pasywny_swiat", "pasywny świat":"pasywny_swiat", "brak aggro":"pasywny_swiat", "aggro":"pasywny_swiat",
    "akweny":"akweny", "lowiska":"akweny", "łowiska":"akweny", "oceany":"akweny",
    "rozlegle laki":"rozlegle_laki", "rozległe łąki":"rozlegle_laki", "laki":"rozlegle_laki", "łąki":"rozlegle_laki",
})


# ============================================================
# v0.13.0 - HYBRID PROCEDURAL WORLD
# Stały rdzeń świata (miasta, drogi, quest huby i landmarki) pozostaje ręczny.
# Naturalne pogranicza i endgame dostają duże, deterministyczne mapy tworzone
# dopiero przy wejściu. Ten sam seed + biom + współrzędne zawsze daje ten sam pokój.
# ============================================================
V013_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0130-hybrid-world"
V013_FRONTIER_SIDE = 12
V013_FRONTIER_ROOMS_PER_BIOME = V013_FRONTIER_SIDE * V013_FRONTIER_SIDE

V013_FRONTIER_SPECS = {
    "meadow": {
        "zone": "Proceduralne Łąki", "anchor": "v0100_laki_001", "direction": "north",
        "base_mastery": 1, "step": 2,
        "titles": ("Polana Dzikich Kwiatów", "Łąka Wysokich Traw", "Wietrzne Pastwisko", "Koniczynowa Niecka", "Wrzosowa Polana"),
        "features": ("stary kamienny krąg", "małe oczko wodne", "pas dzikich kwiatów", "opuszczony szałas", "kępę pachnących ziół"),
        "mobs": ("meadow_hare", "meadow_fox", "meadow_deer", "meadow_field_serpent", "meadow_field_wolf", "meadow_wild_boar"),
        "resources": ("herb_meadow",),
    },
    "forest": {
        "zone": "Proceduralny Las", "anchor": "forest_wolf_trail", "direction": "east",
        "base_mastery": 20, "step": 3,
        "titles": ("Gęsty Bór", "Omszała Polana", "Dębowa Gęstwina", "Brzozowy Parów", "Ciemny Zagajnik"),
        "features": ("powalone pradawne drzewo", "kamień porośnięty mchem", "suchy strumień", "ukrytą leśną polanę", "ślady dawnego obozu"),
        "mobs": ("shadow_wolf", "shadow_wolf_stalker", "shadow_wolf_howler", "shadow_wolf_pack_leader"),
        "resources": ("wood", "herb_forest"),
    },
    "wild": {
        "zone": "Proceduralna Dzicz", "anchor": "stone_ravine", "direction": "east",
        "base_mastery": 30, "step": 3,
        "titles": ("Kamienista Dzicz", "Cierniste Pogranicze", "Dolina Starych Tropów", "Surowa Równina", "Parów Dziczy"),
        "features": ("zarośnięty drogowskaz", "porzucone ognisko", "głazy ze starymi runami", "zwierzęcy wodopój", "wąską ścieżkę między cierniami"),
        "mobs": ("shadow_wolf", "wild_ash_boar", "wild_thorn_wolf", "goblin_scout", "bandit_scout"),
        "resources": ("wood",),
    },
    "mountain": {
        "zone": "Proceduralne Góry", "anchor": "lava_fissure", "direction": "east",
        "base_mastery": 70, "step": 4,
        "titles": ("Skalna Grań", "Wysoka Przełęcz", "Kamienna Półka", "Wąwóz Szczytów", "Smagana Wiatrem Grań"),
        "features": ("odsłoniętą żyłę minerału", "stare osuwisko", "kamienny schron", "głęboką szczelinę", "ślady kozic na skale"),
        "mobs": ("mountain_ice_wolf", "mountain_stone_ram", "mountain_harpy", "mountain_troll"),
        "resources": ("mine",),
    },
    "swamp": {
        "zone": "Proceduralne Mokradła", "anchor": "fungal_bog", "direction": "north",
        "base_mastery": 90, "step": 4,
        "titles": ("Czarne Rozlewisko", "Trzcinowe Mokradło", "Gnijące Torfowisko", "Zatopiona Grobla", "Mglista Niecka"),
        "features": ("kępy świecących grzybów", "zatopiony kamień", "martwe drzewo", "gęsty pas trzcin", "małe błotne źródło"),
        "mobs": ("swamp_crawler", "swamp_serpent", "swamp_mire_witch"),
        "resources": ("herb_water",),
    },
    "desert": {
        "zone": "Proceduralna Pustynia", "anchor": "desert_oasis", "direction": "east",
        "base_mastery": 110, "step": 4,
        "titles": ("Morze Wydm", "Czerwony Kanion", "Szklana Równina", "Kamienista Niecka", "Szlak Gorącego Wiatru"),
        "features": ("fragment zasypanej ruiny", "ciemną skałę wystającą z piasku", "wyschniętą studnię", "ślady dawnej karawany", "pas szkliwionego piasku"),
        "mobs": ("desert_raider", "dune_scorpion", "sand_wraith"),
        "resources": ("mine",),
    },
    "coast": {
        "zone": "Proceduralne Wybrzeże", "anchor": "v0100_wybrzeze_001", "direction": "north",
        "base_mastery": 40, "step": 3,
        "titles": ("Skalisty Brzeg", "Piaszczysta Zatoka", "Klif Nad Morzem", "Płycizna Przypływu", "Wietrzne Molo"),
        "features": ("małą zatoczkę", "wyrzucone przez morze drewno", "basen pływowy", "pas muszli", "stare pale pomostu"),
        "mobs": ("coast_rock_crab", "coast_sea_raider"),
        "resources": ("fish_sea",),
    },
    "ocean": {
        "zone": "Proceduralny Ocean", "anchor": "outer_reef", "direction": "north",
        "base_mastery": 80, "step": 4,
        "titles": ("Otwarta Toń", "Głęboki Szelf", "Błękitny Prąd", "Rafa Dalekiego Morza", "Ciemna Głębia"),
        "features": ("wir chłodnej wody", "pas wodorostów", "wynurzoną skałę", "dryfującą boję", "ciemną krawędź głębi"),
        "mobs": ("coast_sea_raider", "coast_rock_crab"),
        "resources": ("fish_ocean",),
    },
    "river": {
        "zone": "Proceduralne Dorzecze", "anchor": "willow_bend", "direction": "north",
        "base_mastery": 20, "step": 2,
        "titles": ("Rzeczne Zakole", "Kamienny Bród", "Trzcinowy Brzeg", "Szybki Nurt", "Źródlana Odnoga"),
        "features": ("piaszczystą łachę", "zwalone drzewo nad wodą", "głęboki dołek nurtu", "kępę trzcin", "kamienny próg rzeczny"),
        "mobs": ("meadow_deer", "meadow_fox", "meadow_field_serpent", "bandit_scout"),
        "resources": ("fish_river", "herb_water"),
    },
    "lake": {
        "zone": "Proceduralne Pojezierze", "anchor": "deepwater_pier", "direction": "east",
        "base_mastery": 30, "step": 2,
        "titles": ("Cicha Zatoka", "Trzcinowy Brzeg", "Żwirowa Zatoczka", "Głęboka Toń", "Leśne Jezioro"),
        "features": ("stary pomost", "pas lilii wodnych", "głęboką zatokę", "małą wyspę", "zatopiony pień"),
        "mobs": ("meadow_hare", "meadow_deer", "meadow_field_wolf", "shadow_wolf"),
        "resources": ("fish_lake", "herb_water"),
    },
    "frozen": {
        "zone": "Proceduralne Lodowe Pustkowia", "anchor": "ice_cave_crystal_chamber", "direction": "north",
        "base_mastery": 140, "step": 5,
        "titles": ("Pole Niebieskiego Lodu", "Szczelina Szronu", "Kryształowa Grota", "Zamarznięta Galeria", "Lodowy Parów"),
        "features": ("żyłę lodowego kryształu", "zamarznięty wodospad", "pękniętą kolumnę lodu", "ciemną szczelinę", "warstwę pradawnego szronu"),
        "mobs": ("ice_crystal_golem", "ice_fang_wolf", "ice_wraith", "ice_glacier_guard"),
        "resources": ("mine",),
    },
    "ash": {
        "zone": "Proceduralne Popielne Rubieże", "anchor": "cinder_ravine", "direction": "east",
        "base_mastery": 220, "step": 6,
        "titles": ("Morze Popiołu", "Wąwóz Żaru", "Pole Czarnego Pyłu", "Spękana Równina", "Martwe Palenisko"),
        "features": ("dogasającą szczelinę", "stos zwęglonych kości", "czarną żyłę minerału", "ruinę pieca", "wir gorącego popiołu"),
        "mobs": ("cinder_wraith", "ash_revenant", "charred_colossus", "ash_seer"),
        "resources": ("mine",),
    },
    "sky": {
        "zone": "Proceduralne Rubieże Nieba", "anchor": "thunder_shelf", "direction": "east",
        "base_mastery": 260, "step": 6,
        "titles": ("Most Chmur", "Gromowa Półka", "Taras Nawałnicy", "Rozdarta Grań", "Podniebna Platforma"),
        "features": ("wir elektrycznych chmur", "pęknięty filar", "wiszącą skałę", "runiczny piorunochron", "szczelinę między chmurami"),
        "mobs": ("skybreaker", "storm_seraph", "thunder_harrier", "cloud_titan"),
        "resources": ("mine",),
    },
    "void": {
        "zone": "Proceduralne Wybrzeże Pustki", "anchor": "black_tide_flats", "direction": "east",
        "base_mastery": 300, "step": 7,
        "titles": ("Czarny Brzeg", "Bezgwiezdna Zatoka", "Molo Pustki", "Martwy Przypływ", "Zatopiony Taras"),
        "features": ("czarną sadzawkę", "wrak bez żagli", "milczący dzwon", "ciemną rafę", "zatopiony posąg"),
        "mobs": ("black_tide_oracle", "void_mariner", "starless_knight", "abyssal_manta"),
        "resources": ("fish_ocean",),
    },
    "crown": {
        "zone": "Proceduralne Rubieże Korony", "anchor": "absolute_gallery", "direction": "east",
        "base_mastery": 340, "step": 5,
        "titles": ("Grobla Absolutu", "Taras Milczących Gwiazd", "Galeria Wieczności", "Biała Platforma", "Ponadczasowa Grań"),
        "features": ("biały monolit", "pęknięty zegar runiczny", "kamień świecący bez cienia", "zamkniętą bramę", "krąg nieruchomego światła"),
        "mobs": ("timeless_magister", "crown_sentinel", "worldcrown_echo", "absolute_guardian"),
        "resources": ("mine",),
    },
}

V013_REVERSE_DIRECTION = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "up": "down", "down": "up",
}


def v0130_frontier_room_id(kind, x, y):
    return f"v0130_frontier_{kind}_{int(x):02d}_{int(y):02d}"


def v0130_frontier_room_identity(room_id):
    match = re.fullmatch(r"v0130_frontier_([a-z]+)_(\d{2})_(\d{2})", str(room_id or ""))
    if not match:
        return None
    kind, sx, sy = match.groups()
    if kind not in V013_FRONTIER_SPECS:
        return None
    x, y = int(sx), int(sy)
    if not (0 <= x < V013_FRONTIER_SIDE and 0 <= y < V013_FRONTIER_SIDE):
        return None
    return kind, x, y


def v0130_frontier_room_ids(kind):
    return tuple(
        v0130_frontier_room_id(kind, x, y)
        for y in range(V013_FRONTIER_SIDE)
        for x in range(V013_FRONTIER_SIDE)
    )


def v0130_gateway_id(kind):
    return f"v0130_gateway_{kind}"


def v0130_build_static_gateways():
    for kind, spec in V013_FRONTIER_SPECS.items():
        anchor = spec["anchor"]
        direction = spec["direction"]
        if anchor not in ROOMS:
            raise RuntimeError(f"Brak kotwicy proceduralnego biomu {kind}: {anchor}")
        if direction in _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (anchor,), "exits", {}):
            raise RuntimeError(f"Zajęty kierunek {direction} w kotwicy {anchor}")
        gateway = v0130_gateway_id(kind)
        reverse = V013_REVERSE_DIRECTION[direction]
        root = v0130_frontier_room_id(kind, 0, 0)
        anchor_zone = ROOMS[anchor].get("zone", "Dzicz")
        _catalog_mut.catalog_assign({
            "zone": anchor_zone,
            "name": f"Granica: {spec['zone']}",
            "desc": (
                "Stały punkt orientacyjny na granicy ręcznie zaprojektowanego świata. "
                "Dalej zaczyna się rozległy teren proceduralny. Układ sektorów jest "
                "deterministyczny i nie zmienia się po restarcie serwera."
            ),
            "exits": {reverse: anchor, direction: root},
            "procedural_gateway": kind,
        }, 'ROOMS', ROOMS, (gateway,))
        _catalog_mut.catalog_assign(gateway, 'ROOMS', ROOMS, (anchor, "exits", direction))


def _v0130_apply_resources(room_id, spec):
    for resource in spec.get("resources", ()):
        if resource == "herb_meadow":
            HERBALISM_ROOMS.add(room_id)
            MEADOW_HERBALISM_ROOMS.add(room_id)
            V012_MEADOW_HERB_GROUP[room_id] = "meadow"
        elif resource == "herb_forest":
            HERBALISM_ROOMS.add(room_id)
            V012_MEADOW_HERB_GROUP[room_id] = "forest"
        elif resource == "herb_water":
            HERBALISM_ROOMS.add(room_id)
            V012_MEADOW_HERB_GROUP[room_id] = "water"
        elif resource == "wood":
            WOODCUTTING_ROOMS.add(room_id)
        elif resource == "mine":
            # v0.25.1: geologiczny motyw może wystąpić wizualnie, ale
            # wydobycie jest dostępne wyłącznie w Kopalni Głębinowej.
            pass
        elif resource == "fish_river":
            RIVER_FISHING_ROOMS.add(room_id)
            FRESHWATER_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralna rzeka"
        elif resource == "fish_lake":
            LAKE_FISHING_ROOMS.add(room_id)
            FRESHWATER_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralne jezioro"
        elif resource == "fish_sea":
            SEA_FISHING_ROOMS.add(room_id)
            MARINE_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralne morze"
        elif resource == "fish_ocean":
            OCEAN_FISHING_ROOMS.add(room_id)
            MARINE_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralny ocean"


def v0130_create_frontier_room_definition(room_id):
    identity = v0130_frontier_room_identity(room_id)
    if identity is None:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind, x, y = identity
    spec = V013_FRONTIER_SPECS[kind]
    seed_text = f"{V013_WORLD_SEED}:{kind}:{x}:{y}"
    seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    title = rng.choice(spec["titles"])
    feature = rng.choice(spec["features"])
    distance = x + y
    mastery = min(CHARACTER_MAX_LEVEL, int(spec["base_mastery"]) + distance * int(spec["step"]))
    exits = {}
    if x > 0:
        exits["west"] = v0130_frontier_room_id(kind, x - 1, y)
    if x + 1 < V013_FRONTIER_SIDE:
        exits["east"] = v0130_frontier_room_id(kind, x + 1, y)
    if y > 0:
        exits["south"] = v0130_frontier_room_id(kind, x, y - 1)
    if y + 1 < V013_FRONTIER_SIDE:
        exits["north"] = v0130_frontier_room_id(kind, x, y + 1)
    if x == 0 and y == 0:
        direction = spec["direction"]
        exits[V013_REVERSE_DIRECTION[direction]] = v0130_gateway_id(kind)

    # v0.14.0: wejścia do mini-lochów są częścią trwałego seedu sektora.
    # Funkcja jest zdefiniowana niżej; nazwa rozwiązuje się dopiero przy
    # faktycznym generowaniu pokoju po zakończeniu importu modułu.
    if "v0140_has_mini_dungeon" in globals() and v0140_has_mini_dungeon(kind, x, y):
        exits["down"] = v0140_mini_room_id(kind, x, y, 1)
    if "v0180_has_great_ruin" in globals() and v0180_has_great_ruin(kind, x, y):
        exits["up"] = v0180_ruin_room_id(kind, x, y, 1)

    _catalog_mut.catalog_assign({
        "zone": spec["zone"],
        "name": f"{title} — sektor {x + 1}-{y + 1}",
        "desc": (
            f"Rozległy sektor biomu {spec['zone']}. Wyróżnia się tu {feature}. "
            "Teren został wygenerowany z trwałego seedu świata, więc po ponownym "
            "uruchomieniu serwera zachowuje ten sam układ i charakter."
        ),
        "exits": exits,
        "recommended_mastery": mastery,
        "procedural_surface": True,
        "generated_on_demand": True,
        "procedural_biome": kind,
        "procedural_x": x,
        "procedural_y": y,
    }, 'ROOMS', ROOMS, (room_id,))
    if "v0140_has_mini_dungeon" in globals() and v0140_has_mini_dungeon(kind, x, y):
        _catalog_mut.catalog_aug_path('ROOMS', ROOMS, (room_id, "desc"), 'Add', " W terenie ukrywa się zejście do proceduralnego mini-lochu.")
        _catalog_mut.catalog_assign(True, 'ROOMS', ROOMS, (room_id, "v0140_mini_entrance"))
    if "v0180_has_great_ruin" in globals() and v0180_has_great_ruin(kind, x, y):
        _catalog_mut.catalog_aug_path('ROOMS', ROOMS, (room_id, "desc"), 'Add', " Nad sektorem wznoszą się rozległe ruiny; wejście prowadzi w górę.")
        _catalog_mut.catalog_assign(True, 'ROOMS', ROOMS, (room_id, "v0180_great_ruin_entrance"))
    if "v0140_surface_secret_info" in globals():
        secret_info = v0140_surface_secret_info(room_id)
        if secret_info:
            _catalog_mut.catalog_assign(True, 'ROOMS', ROOMS, (room_id, "v0140_surface_secret"))
            _catalog_mut.catalog_assign(secret_info["name"], 'ROOMS', ROOMS, (room_id, "v0140_secret_name"))
    _v0130_apply_resources(room_id, spec)

    mob_pool = tuple(t for t in spec.get("mobs", ()) if t in MOB_TEMPLATES)
    spawns = []
    if mob_pool:
        spawn_count = 1 + (1 if rng.random() < 0.38 else 0)
        for _ in range(spawn_count):
            spawns.append((room_id, rng.choice(mob_pool)))
    return room_id, tuple(spawns)


def v0130_refresh_exploration_catalog():
    global TRACKED_EXPLORATION_ZONES, ALL_EXPLORATION_ROOMS
    EXPLORATION_ZONE_ROOMS.clear()
    for room_id, room in ROOMS.items():
        EXPLORATION_ZONE_ROOMS.setdefault(room["zone"], []).append(room_id)
    for kind, spec in V013_FRONTIER_SPECS.items():
        EXPLORATION_ZONE_ROOMS.setdefault(spec["zone"], []).extend(v0130_frontier_room_ids(kind))
    for zone in EXPLORATION_ZONE_ROOMS:
        EXPLORATION_ZONE_ROOMS[zone] = sorted(set(EXPLORATION_ZONE_ROOMS[zone]))
    TRACKED_EXPLORATION_ZONES = {
        zone: tuple(room_ids)
        for zone, room_ids in EXPLORATION_ZONE_ROOMS.items()
        if len(room_ids) >= EXPLORATION_ZONE_MIN_ROOMS
    }
    ALL_EXPLORATION_ROOMS = tuple(sorted({rid for ids in EXPLORATION_ZONE_ROOMS.values() for rid in ids}))

    EXPLORATION_REWARD_ITEMS.clear()
    for zone, room_ids in TRACKED_EXPLORATION_ZONES.items():
        reward_item_id = f"exploration_relic_{_collection_slug(zone)}"
        EXPLORATION_REWARD_ITEMS[zone] = reward_item_id
        _catalog_mut.catalog_setdefault_path('ITEMS', ITEMS, (), reward_item_id, {
            "name": f"Pamiątka Odkrywcy: {zone}", "type": "collectible",
            "price": None, "rarity": "unique", "rarity_name": "Unikalny",
            "exploration_reward": True,
            "desc": f"Unikalna pamiątka za odkrycie 100 procent strefy {zone}.",
        })

    tiers = list(ACHIEVEMENT_TRACKS.get("exploration_rooms", {}).get("tiers", ()))
    if tiers:
        tiers = [(req, rank) for req, rank in tiers if rank != "Platinum"]
        tiers.append((len(ALL_EXPLORATION_ROOMS), "Platinum"))
        ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = tuple(tiers)


v0130_build_static_gateways()
V013_FIXED_CORE_ROOMS = len(ROOMS)
V013_FRONTIER_POTENTIAL_ROOMS = len(V013_FRONTIER_SPECS) * V013_FRONTIER_ROOMS_PER_BIOME
V013_PROCEDURAL_SURFACE_SHARE = V013_FRONTIER_POTENTIAL_ROOMS / float(V013_FIXED_CORE_ROOMS + V013_FRONTIER_POTENTIAL_ROOMS)
v0130_refresh_exploration_catalog()

GUIDE_DESTINATION_ALIASES.update({
    "proceduralne laki": v0130_gateway_id("meadow"), "dzikie laki": v0130_gateway_id("meadow"),
    "proceduralny las": v0130_gateway_id("forest"), "dziki las": v0130_gateway_id("forest"),
    "proceduralna dzicz": v0130_gateway_id("wild"),
    "proceduralne gory": v0130_gateway_id("mountain"),
    "proceduralne bagna": v0130_gateway_id("swamp"), "proceduralne mokradla": v0130_gateway_id("swamp"),
    "proceduralna pustynia": v0130_gateway_id("desert"),
    "proceduralne wybrzeze": v0130_gateway_id("coast"),
    "proceduralny ocean": v0130_gateway_id("ocean"),
    "proceduralna rzeka": v0130_gateway_id("river"), "proceduralne dorzecze": v0130_gateway_id("river"),
    "proceduralne jeziora": v0130_gateway_id("lake"), "proceduralne pojezierze": v0130_gateway_id("lake"),
    "proceduralny lod": v0130_gateway_id("frozen"),
    "proceduralny popiol": v0130_gateway_id("ash"),
    "proceduralne niebo": v0130_gateway_id("sky"),
    "proceduralna pustka": v0130_gateway_id("void"),
    "proceduralna korona": v0130_gateway_id("crown"),
})

HELP_TOPICS["hybrydowy_swiat"] = [
    "v0.13.0 wprowadza hybrydowy świat: miasta, główne drogi, quest huby, ważni NPC i landmarki pozostają stałe.",
    f"15 naturalnych i endgame'owych biomów ma po {V013_FRONTIER_ROOMS_PER_BIOME} proceduralnych sektorów, łącznie {V013_FRONTIER_POTENTIAL_ROOMS} możliwych lokacji powierzchniowych.",
    "Sektory są tworzone dopiero przy wejściu. Nie obciążają startu serwera tysiącami gotowych pokoi.",
    "Generator jest deterministyczny: ten sam biom i współrzędne zawsze tworzą tę samą nazwę, opis, wyjścia, zasoby i bazową obsadę mobów.",
    "Proceduralne są: łąki, las, dzicz, góry, mokradła, pustynia, wybrzeże, ocean, dorzecze, pojezierze, lód oraz cztery rubieże endgame.",
    "Profesje działają w proceduralnym świecie: odpowiednie sektory wspierają Wędkarstwo, Zielarstwo, Drwalstwo lub Górnictwo bez omijania levelu narzędzia 1-600.",
    "Moby proceduralne również podlegają PASSIVE WORLD i nigdy nie zaczynają walki same.",
    "Prowadzenie doprowadza do stałej granicy biomu; dalszą proceduralną mapę odkrywa się ręcznie.",
]
HELP_TOPIC_ALIASES.update({
    "hybrydowy swiat": "hybrydowy_swiat", "hybrydowy świat": "hybrydowy_swiat",
    "proceduralny swiat": "hybrydowy_swiat", "proceduralny świat": "hybrydowy_swiat",
    "generowany swiat": "hybrydowy_swiat", "generowany świat": "hybrydowy_swiat",
})


# ============================================================
# v0.14.0 - DYNAMIC WORLD EVENTS & SECRETS
# Opcjonalne wydarzenia, rare roaming, deterministyczne mini-lochy,
# sekrety powierzchniowe, mapy skarbów i questy eksploracyjne.
# ============================================================
V014_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0140-events-secrets"
V014_EVENT_ROTATION_SECONDS = 30 * 60
V014_TREASURE_MAP_ITEM = "treasure_map_frontier"
V014_MINI_DENOMINATOR = 18
V014_SECRET_DENOMINATOR = 17

_catalog_mut.catalog_assign({
    "name": "Mapa Skarbu Rubieży",
    "type": "consumable",
    "price": None,
    "rarity": "rare",
    "rarity_name": "Rzadki",
    "treasure_map": True,
    "desc": (
        "Mapa prowadząca do jednego z deterministycznych sekretów proceduralnych rubieży. "
        "Użyj jej, aby zapisać trop; potem wpisz mapa skarbu."
    ),
}, 'ITEMS', ITEMS, (V014_TREASURE_MAP_ITEM,))

V0243_EREN_SECRET_MAP_ITEM = "quest_map_eren_secret_marks"
_catalog_mut.catalog_assign({
    "name": "Mapa Erena: Znak poza mapą",
    "type": "consumable",
    "price": None,
    "rarity": "quest",
    "rarity_name": "Questowy",
    "treasure_map": True,
    "quest_treasure_map_for": "city_cartographer_secret_marks",
    "desc": (
        "Questowa mapa Kartografa Erena. Wpisz użyj mapy, aby zapisać trop, "
        "a następnie prowadz skarb. Po porzuceniu questa mapa i jej aktywny trop znikają."
    ),
}, 'ITEMS', ITEMS, (V0243_EREN_SECRET_MAP_ITEM,))

V014_EVENT_DEFS = {
    "rare_hunt": {
        "title": "Trop rzadkiego przeciwnika",
        "kinds": tuple(V013_FRONTIER_SPECS),
        "desc": "W sektorze pojawił się wędrujący rare. Walka pozostaje całkowicie dobrowolna.",
    },
    "fish_run": {
        "title": "Wielka ławica",
        "kinds": ("coast", "ocean", "river", "lake", "void"),
        "desc": "W tym łowisku trwa ławica: +2 do bazowego połowu i +25% XP Wędkarstwa/Wędki.",
        "quantity_bonus": 2, "xp_mult": 1.25,
    },
    "herb_bloom": {
        "title": "Rozkwit rzadkich ziół",
        "kinds": ("meadow", "forest", "swamp", "river"),
        "desc": "Roślinność jest wyjątkowo obfita: +2 do bazowego zbioru i +25% XP Zielarstwa/Sierpa.",
        "quantity_bonus": 2, "xp_mult": 1.25,
    },
    "rich_vein": {
        "title": "Bogata żyła",
        "kinds": ("mountain", "desert", "frozen", "ash", "sky", "crown"),
        "desc": "Odsłonięto wyjątkowo bogate złoże: +2 do bazowego urobku i +25% XP Górnictwa/Kilofa.",
        "quantity_bonus": 2, "xp_mult": 1.25,
    },
    "forest_growth": {
        "title": "Rozrost starego boru",
        "kinds": ("forest", "wild", "meadow"),
        "desc": "Stare drzewa dają więcej drewna: +2 do bazowego pozyskania i +25% XP Drwalstwa/Piły.",
        "quantity_bonus": 2, "xp_mult": 1.25,
    },
}


def _v0140_hash_int(*parts):
    text = ":".join(str(part) for part in (V014_WORLD_SEED,) + parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def v0140_has_mini_dungeon(kind, x, y):
    if kind not in V013_FRONTIER_SPECS:
        return False
    return _v0140_hash_int("mini", kind, int(x), int(y)) % V014_MINI_DENOMINATOR == 0


def v0140_mini_size(kind, x, y):
    return 7 + (_v0140_hash_int("mini-size", kind, int(x), int(y)) % 6)


def v0140_mini_room_id(kind, x, y, index):
    return f"v0140_mini_{kind}_{int(x):02d}_{int(y):02d}_{int(index):02d}"


def v0140_mini_identity(room_id):
    match = re.fullmatch(r"v0140_mini_([a-z]+)_(\d{2})_(\d{2})_(\d{2})", str(room_id or ""))
    if not match:
        return None
    kind, sx, sy, si = match.groups()
    if kind not in V013_FRONTIER_SPECS:
        return None
    x, y, index = int(sx), int(sy), int(si)
    if not (0 <= x < V013_FRONTIER_SIDE and 0 <= y < V013_FRONTIER_SIDE):
        return None
    size = v0140_mini_size(kind, x, y)
    if not v0140_has_mini_dungeon(kind, x, y) or not (1 <= index <= size):
        return None
    return kind, x, y, index, size


def v0140_secret_room_id(kind, x, y):
    return f"v0140_secret_{kind}_{int(x):02d}_{int(y):02d}"


def v0140_secret_room_identity(room_id):
    match = re.fullmatch(r"v0140_secret_([a-z]+)_(\d{2})_(\d{2})", str(room_id or ""))
    if not match:
        return None
    kind, sx, sy = match.groups()
    if kind not in V013_FRONTIER_SPECS:
        return None
    x, y = int(sx), int(sy)
    if not (0 <= x < V013_FRONTIER_SIDE and 0 <= y < V013_FRONTIER_SIDE):
        return None
    parent = v0130_frontier_room_id(kind, x, y)
    if not v0140_surface_secret_info(parent):
        return None
    return kind, x, y


V014_SECRET_NAMES = (
    "Zapomniana Kapliczka", "Ukryta Grota", "Zarośnięty Skarbiec",
    "Kamienna Komnata", "Zatopiony Schowek", "Pradawny Krąg",
    "Szczelina Kartografów", "Ruina Bez Drogi",
)


def v0140_surface_secret_info(room_id):
    identity = v0130_frontier_room_identity(room_id)
    if identity is None:
        return None
    kind, x, y = identity
    value = _v0140_hash_int("secret", kind, x, y)
    if value % V014_SECRET_DENOMINATOR != 0:
        return None
    return {
        "kind": kind, "x": x, "y": y,
        "name": V014_SECRET_NAMES[(value // V014_SECRET_DENOMINATOR) % len(V014_SECRET_NAMES)],
        "room_id": room_id,
        "hidden_room": v0140_secret_room_id(kind, x, y),
    }


def v0140_surface_secret_room_ids(kind=None):
    kinds = (kind,) if kind else tuple(V013_FRONTIER_SPECS)
    result = []
    for current_kind in kinds:
        for y in range(V013_FRONTIER_SIDE):
            for x in range(V013_FRONTIER_SIDE):
                rid = v0130_frontier_room_id(current_kind, x, y)
                if v0140_surface_secret_info(rid):
                    result.append(rid)
    return tuple(result)


def v0140_event_slot(now=None):
    now = time.time() if now is None else float(now)
    return int(now // V014_EVENT_ROTATION_SECONDS)


def v0140_active_world_events(now=None):
    now = time.time() if now is None else float(now)
    slot = v0140_event_slot(now)
    result = []
    used_rooms = set()
    for event_type, definition in V014_EVENT_DEFS.items():
        rng = random.Random(_v0140_hash_int("event", slot, event_type))
        kinds = tuple(definition["kinds"])
        # Kilka prób, aby dwa typy eventu nie wylądowały w dokładnie tym samym sektorze.
        for _ in range(20):
            kind = rng.choice(kinds)
            x = rng.randrange(V013_FRONTIER_SIDE)
            y = rng.randrange(V013_FRONTIER_SIDE)
            room_id = v0130_frontier_room_id(kind, x, y)
            if room_id not in used_rooms:
                break
        used_rooms.add(room_id)
        result.append({
            "type": event_type,
            "title": definition["title"],
            "desc": definition["desc"],
            "kind": kind,
            "x": x,
            "y": y,
            "room_id": room_id,
            "slot": slot,
            "token": f"{slot}:{event_type}:{kind}:{x}:{y}",
            "expires_at": (slot + 1) * V014_EVENT_ROTATION_SECONDS,
            "quantity_bonus": int(definition.get("quantity_bonus", 0) or 0),
            "xp_mult": float(definition.get("xp_mult", 1.0) or 1.0),
        })
    return tuple(result)


def v0140_event_for_room(room_id, event_type=None, now=None):
    for event in v0140_active_world_events(now):
        if event["room_id"] == room_id and (event_type is None or event["type"] == event_type):
            return event
    return None


def v0140_gather_event_bonus(room_id, tool_type=None, now=None):
    event = v0140_event_for_room(room_id, now=now)
    expected = {
        "fish_run": "fishing",
        "herb_bloom": "herbalism",
        "rich_vein": "mining",
        "forest_growth": "woodcutting",
    }
    if not event or expected.get(event["type"]) != str(tool_type or ""):
        return {"label": "", "quantity_bonus": 0, "xp_mult": 1.0}
    return {
        "label": f"WYDARZENIE ŚWIATA — {event['title']}",
        "quantity_bonus": int(event.get("quantity_bonus", 0) or 0),
        "xp_mult": float(event.get("xp_mult", 1.0) or 1.0),
    }


def _v0140_clone_variant(base_id, *, rare=False, miniboss=False):
    base = MOB_TEMPLATES.get(base_id)
    if not base:
        return None
    suffix = "rare" if rare else "miniboss"
    variant_id = f"v0140_{suffix}_{base_id}"
    if variant_id in MOB_TEMPLATES:
        return variant_id
    data = dict(base)
    data["drops"] = dict(base.get("drops", {}))
    if rare:
        data["name"] = f"Wędrujący Rzadki {base['name']}"
        data["rare_mob"] = True
        data["rare_base_template"] = base_id
        hp_mult, dmg_mult, reward_mult = 1.75, 1.30, 2.20
    else:
        data["name"] = f"Strażnik Mini-Lochu: {base['name']}"
        data["mini_boss"] = True
        data["stationary_mob"] = True
        data["v0140_mini_boss"] = True
        hp_mult, dmg_mult, reward_mult = 2.80, 1.55, 3.20
    data["max_hp"] = max(1, int(round(int(base.get("max_hp", 1)) * hp_mult)))
    data["damage"] = max(1, int(round(int(base.get("damage", 1)) * dmg_mult)))
    data["stat_reward"] = max(1, int(round(int(base.get("stat_reward", 1)) * min(1.8, reward_mult))))
    data["soul_reward"] = max(1, int(round(int(base.get("soul_reward", 1)) * reward_mult)))
    data["class_xp_reward"] = max(50, int(round(int(base.get("class_xp_reward", max(50, int(base.get("stat_reward", 1))*10))) * reward_mult)))
    data["silver"] = max(1, int(round(int(base.get("silver", 1)) * reward_mult)))
    data["gold"] = 0
    data["mithril"] = 0
    data["auto_aggro"] = False
    data["drops"].setdefault(V014_TREASURE_MAP_ITEM, 0.28 if rare else 0.45)
    data["drops"].setdefault("soul_shard", 0.45 if rare else 0.70)
    _catalog_mut.catalog_assign(data, 'MOB_TEMPLATES', MOB_TEMPLATES, (variant_id,))
    return variant_id


for _kind, _spec in V013_FRONTIER_SPECS.items():
    for _base_id in tuple(_spec.get("mobs", ())):
        if _base_id in MOB_TEMPLATES:
            _v0140_clone_variant(_base_id, rare=True)
            _v0140_clone_variant(_base_id, miniboss=True)

# Katalogi Codexu powstały w starszej części modułu, więc dopisujemy nowe
# dynamiczne warianty do tych samych słowników referencyjnych.
for _mob_id, _data in MOB_TEMPLATES.items():
    if _mob_id.startswith("v0140_rare_"):
        RARE_MOB_COLLECTION_CATALOG[_mob_id] = _data["name"]
    if _mob_id.startswith("v0140_miniboss_"):
        BOSS_COLLECTION_CATALOG[_mob_id] = _data["name"]


def v0140_rare_template_for_kind(kind, salt="event"):
    pool = [base for base in V013_FRONTIER_SPECS[kind].get("mobs", ()) if base in MOB_TEMPLATES]
    if not pool:
        return None
    base = pool[_v0140_hash_int("rare-pick", kind, salt) % len(pool)]
    return _v0140_clone_variant(base, rare=True)


def v0140_miniboss_template_for_sector(kind, x, y):
    pool = [base for base in V013_FRONTIER_SPECS[kind].get("mobs", ()) if base in MOB_TEMPLATES]
    if not pool:
        return None
    base = pool[_v0140_hash_int("mini-boss-pick", kind, x, y) % len(pool)]
    return _v0140_clone_variant(base, miniboss=True)


def v0140_create_mini_room_definition(room_id):
    identity = v0140_mini_identity(room_id)
    if identity is None:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind, x, y, index, size = identity
    spec = V013_FRONTIER_SPECS[kind]
    width = 3
    cx, cy = (index - 1) % width, (index - 1) // width
    exits = {}
    candidates = {
        "west": (cx - 1, cy), "east": (cx + 1, cy),
        "south": (cx, cy - 1), "north": (cx, cy + 1),
    }
    for direction, (nx, ny) in candidates.items():
        if nx < 0 or ny < 0 or nx >= width:
            continue
        neighbor = ny * width + nx + 1
        if 1 <= neighbor <= size:
            exits[direction] = v0140_mini_room_id(kind, x, y, neighbor)
    parent = v0130_frontier_room_id(kind, x, y)
    if index == 1:
        exits["up"] = parent
    final = index == size
    seed = _v0140_hash_int("mini-room", kind, x, y, index)
    rng = random.Random(seed)
    room_titles = (
        "Zawalone Przejście", "Kamienna Galeria", "Boczna Komora", "Stary Korytarz",
        "Podziemna Sala", "Szczelina Korzeni", "Zapomniany Tunel", "Komora Runiczna",
    )
    title = "Komnata Strażnika" if final else rng.choice(room_titles)
    _catalog_mut.catalog_assign({
        "zone": f"Mini-loch: {spec['zone']}",
        "name": f"{title} — {index}/{size}",
        "desc": (
            f"Proceduralny mini-loch odkryty w sektorze {x+1}-{y+1} biomu {spec['zone']}. "
            "Układ tej podziemnej siatki jest trwały dla seedu świata."
            + (" To finałowa komnata ze strażnikiem i skrzynią." if final else "")
        ),
        "exits": exits,
        "recommended_mastery": min(CHARACTER_MAX_LEVEL, int(spec["base_mastery"]) + (x+y)*int(spec["step"]) + index*3),
        "generated_on_demand": True,
        "v0140_mini_dungeon": True,
        "v0140_mini_kind": kind,
        "v0140_mini_index": index,
        "v0140_mini_size": size,
        "v0140_mini_final": final,
    }, 'ROOMS', ROOMS, (room_id,))
    spawns = []
    mob_pool = tuple(base for base in spec.get("mobs", ()) if base in MOB_TEMPLATES)
    if final:
        boss = v0140_miniboss_template_for_sector(kind, x, y)
        if boss:
            spawns.append((room_id, boss))
        TREASURE_CHESTS.setdefault(room_id, {
            "name": f"Skrzynia Mini-Lochu: {spec['zone']}",
            "respawn": 3600,
            "base_pool": ("soul_shard", "soul_elixir", V014_TREASURE_MAP_ITEM),
            "set_pool": (),
        })
        CHEST_COLLECTION_CATALOG[room_id] = TREASURE_CHESTS[room_id]["name"]
    elif mob_pool:
        count = 1 + (1 if rng.random() < 0.45 else 0)
        for _ in range(count):
            spawns.append((room_id, rng.choice(mob_pool)))
    return room_id, tuple(spawns)


def v0140_create_secret_room_definition(room_id):
    identity = v0140_secret_room_identity(room_id)
    if identity is None:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind, x, y = identity
    parent = v0130_frontier_room_id(kind, x, y)
    secret = v0140_surface_secret_info(parent)
    spec = V013_FRONTIER_SPECS[kind]
    _catalog_mut.catalog_assign({
        "zone": f"Sekret: {spec['zone']}",
        "name": secret["name"],
        "desc": (
            f"Ukryta lokacja odnaleziona w sektorze {x+1}-{y+1}. "
            "Nie należy do zwykłej siatki dróg i pozostaje stała dla seedu świata."
        ),
        "exits": {"down": parent},
        "generated_on_demand": True,
        "v0140_secret_room": True,
        "v0140_secret_parent": parent,
        "recommended_mastery": min(CHARACTER_MAX_LEVEL, int(spec["base_mastery"]) + (x+y)*int(spec["step"])),
    }, 'ROOMS', ROOMS, (room_id,))
    TREASURE_CHESTS.setdefault(room_id, {
        "name": f"Ukryty Skarb: {secret['name']}",
        "respawn": 5400,
        "base_pool": ("soul_shard", V014_TREASURE_MAP_ITEM),
        "set_pool": ("soul_elixir",),
    })
    CHEST_COLLECTION_CATALOG[room_id] = TREASURE_CHESTS[room_id]["name"]
    return room_id, ()


# Kartografka i cztery jednorazowe questy eksploracyjne. Postęp jest zdarzeniowy,
# więc nic odkrytego przed przyjęciem nie daje darmowych punktów.
_catalog_mut.catalog_update_path('QUESTS', QUESTS, (), {
    "v014_frontier_survey": {
        "name": "Mapa Żywych Rubieży", "giver": "Kartografka Lysa",
        "kind": "explore_frontier", "target": "any", "needed": 20,
        "description": "Odkryj 20 nowych sektorów proceduralnych rubieży po przyjęciu zadania.",
        "reward_silver": 3500, "reward_gold": 2, "reward_mithril": 0,
        "reward_items": {V014_TREASURE_MAP_ITEM: 1}, "repeatable": False,
    },
    "v014_secret_signs": {
        "name": "Znaki poza drogą", "giver": "Kartografka Lysa",
        "kind": "discover_secret", "target": "any", "needed": 3,
        "description": "Odkryj 3 nowe sekrety proceduralnego świata. W podejrzanym sektorze użyj sekret.",
        "requires_quest": "v014_frontier_survey",
        "reward_silver": 6000, "reward_gold": 4, "reward_mithril": 0,
        "reward_items": {V014_TREASURE_MAP_ITEM: 2}, "repeatable": False,
    },
    "v014_mini_depths": {
        "name": "Małe głębiny", "giver": "Kartografka Lysa",
        "kind": "mini_dungeon", "target": "any", "needed": 2,
        "description": "Dotrzyj do finałowej komnaty 2 nowych proceduralnych mini-lochów.",
        "requires_quest": "v014_secret_signs",
        "reward_silver": 9000, "reward_gold": 6, "reward_mithril": 0,
        "reward_items": {"soul_elixir": 2}, "repeatable": False,
    },
    "v014_living_world": {
        "name": "Świat, który się porusza", "giver": "Kartografka Lysa",
        "kind": "world_event", "target": "any", "needed": 3,
        "description": "Odwiedź 3 nowe aktywne wydarzenia świata po przyjęciu zadania. Komenda wydarzenia pokazuje aktualne cele.",
        "requires_quest": "v014_mini_depths",
        "reward_silver": 12000, "reward_gold": 10, "reward_mithril": 0,
        "reward_items": {V014_TREASURE_MAP_ITEM: 2, "soul_elixir": 2}, "repeatable": False,
    },
})

_catalog_mut.catalog_assign({
    "name": "Kartografka Lysa", "room": "library",
    "dialogue": (
        "Stałe drogi znamy dobrze, ale rubieże żyją własnym rytmem. "
        "Zbieram mapy nowych sektorów, sekretów, mini-lochów i wydarzeń świata."
    ),
    "quest": "v014_frontier_survey",
    "quest_chain": (
        "v014_frontier_survey", "v014_secret_signs", "v014_mini_depths", "v014_living_world",
    ),
}, 'NPCS', NPCS, ("cartographer_lysa",))

HELP_TOPICS["wydarzenia_swiata"] = [
    "Komenda wydarzenia / events pokazuje pięć aktualnych eventów proceduralnego świata. Zestaw zmienia się co 30 minut.",
    "Eventy nie teleportują i nie atakują gracza. Podają biom oraz sektor, do którego można dojść normalnie.",
    "Polowanie na rare tworzy pasywnego wędrującego rare; walkę nadal rozpoczyna wyłącznie gracz.",
    "Ławica, rozkwit ziół, bogata żyła i rozrost boru dają +2 do bazowego zbioru i +25 procent XP właściwej profesji/narzędzia w sektorze eventu.",
]
HELP_TOPICS["mini_lochy"] = [
    "Część proceduralnych sektorów ma trwałe zejście do mini-lochu generowanego na żądanie.",
    "Mini-loch ma 7-12 pokojów ułożonych w małą siatkę z pętlami; finał ma pasywnego mini-bossa i odnawialną skrzynię.",
    "Mini-lochy nie zastępują dużych Krypt i Wież. Są krótkimi odkryciami podczas eksploracji powierzchni.",
]
HELP_TOPICS["sekrety_swiata"] = [
    "W części proceduralnych sektorów istnieje deterministyczny sekret. Komenda sekret odkrywa go osobno dla postaci.",
    "Po odkryciu wpisz sekret ponownie w tym samym sektorze, aby wejść do ukrytej komnaty ze skrzynią.",
    "Mapa Skarbu Rubieży może wskazać jeden nieodkryty sekret. Wpisz mapa skarbu, aby sprawdzić zapisane tropy.",
]
HELP_TOPIC_ALIASES.update({
    "wydarzenia": "wydarzenia_swiata", "eventy": "wydarzenia_swiata", "events": "wydarzenia_swiata",
    "mini lochy": "mini_lochy", "minilochy": "mini_lochy", "mini-lochy": "mini_lochy",
    "sekrety swiata": "sekrety_swiata", "sekrety świata": "sekrety_swiata", "mapy skarbow": "kartografia", "mapy skarbów": "kartografia",
})

# ============================================================
# v0.15.0 - WORLD LIFE & PROGRESSION (NO TRAPS)
# ============================================================
V015_DAY_SECONDS = 7200
V015_WEATHER_SECONDS = 1800
V015_DYNAMIC_QUEST_SECONDS = 3600
V015_BIOME_MASTERY_THRESHOLDS = (25, 50, 75, 100)
V015_TIME_PHASES = (
    ("swit", "Świt"), ("dzien", "Dzień"), ("zmierzch", "Zmierzch"), ("noc", "Noc"),
)
V015_WEATHER_POOLS = {
    "meadow": ("bezchmurnie", "lekki_deszcz", "wiatr", "mgla"),
    "forest": ("bezchmurnie", "lekki_deszcz", "mgla", "ulewa"),
    "wild": ("bezchmurnie", "wiatr", "lekki_deszcz", "mgla"),
    "mountain": ("bezchmurnie", "silny_wiatr", "snieg", "burza"),
    "swamp": ("mgla", "lekki_deszcz", "ulewa", "bezchmurnie"),
    "desert": ("bezchmurnie", "upal", "wiatr", "burza_piaskowa"),
    "coast": ("bezchmurnie", "morska_mgla", "wiatr", "ulewa"),
    "ocean": ("bezchmurnie", "morska_mgla", "wiatr", "sztorm"),
    "river": ("bezchmurnie", "lekki_deszcz", "mgla", "ulewa"),
    "lake": ("bezchmurnie", "lekki_deszcz", "mgla", "wiatr"),
    "frozen": ("bezchmurnie", "snieg", "zamiec", "mgla"),
    "ash": ("popiol", "goracy_wiatr", "bezchmurnie", "burza_popiolowa"),
    "sky": ("wiatr", "burza", "bezchmurnie", "mgla"),
    "void": ("bezchmurnie", "czarna_mgla", "wiatr", "martwy_deszcz"),
    "crown": ("bezchmurnie", "biala_mgla", "wiatr", "cichy_deszcz"),
}
V015_WEATHER_LABELS = {
    "bezchmurnie":"Bezchmurnie", "lekki_deszcz":"Lekki deszcz", "wiatr":"Wiatr",
    "mgla":"Mgła", "ulewa":"Ulewa", "silny_wiatr":"Silny wiatr", "snieg":"Śnieg",
    "burza":"Burza", "upal":"Upał", "burza_piaskowa":"Burza piaskowa", "morska_mgla":"Morska mgła",
    "sztorm":"Sztorm", "zamiec":"Zamieć", "popiol":"Opad popiołu", "goracy_wiatr":"Gorący wiatr",
    "burza_popiolowa":"Burza popiołowa", "czarna_mgla":"Czarna mgła", "martwy_deszcz":"Martwy deszcz",
    "biala_mgla":"Biała mgła", "cichy_deszcz":"Cichy deszcz",
}
V015_BIOME_TITLE_BASE = {
    kind: spec["zone"] for kind, spec in V013_FRONTIER_SPECS.items()
}


def v0150_time_state(now=None):
    now = time.time() if now is None else float(now)
    pos = (now % V015_DAY_SECONDS) / V015_DAY_SECONDS
    idx = min(3, int(pos * 4))
    key, label = V015_TIME_PHASES[idx]
    return {"key": key, "label": label, "cycle_percent": int(pos * 100)}


def v0150_weather_state(room_id, now=None):
    identity = v0130_frontier_room_identity(room_id)
    if not identity:
        return {"kind":"", "weather":"bezchmurnie", "label":"Spokojna pogoda", "slot":0}
    kind, x, y = identity
    now = time.time() if now is None else float(now)
    slot = int(now // V015_WEATHER_SECONDS)
    pool = V015_WEATHER_POOLS.get(kind, ("bezchmurnie",))
    idx = _v0140_hash_int("v015-weather", kind, slot) % len(pool)
    weather = pool[idx]
    return {"kind":kind, "weather":weather, "label":V015_WEATHER_LABELS.get(weather, weather), "slot":slot}


def v0150_environment_bonus(room_id, tool_type=None, now=None):
    identity = v0130_frontier_room_identity(room_id)
    if not identity:
        return {"label":"", "quantity_bonus":0, "xp_mult":1.0}
    weather = v0150_weather_state(room_id, now)
    phase = v0150_time_state(now)
    tool = str(tool_type or "")
    mult = 1.0
    wet = {"lekki_deszcz","ulewa","morska_mgla","mgla","sztorm","cichy_deszcz"}
    wind = {"wiatr","silny_wiatr","burza","sztorm","burza_piaskowa","zamiec","burza_popiolowa"}
    if tool == "fishing" and weather["weather"] in wet:
        mult *= 1.08
    if tool == "herbalism" and weather["weather"] in wet:
        mult *= 1.08
    if tool == "mining" and weather["weather"] in wind:
        mult *= 1.05
    if tool == "woodcutting" and weather["weather"] in {"bezchmurnie","wiatr","lekki_deszcz"}:
        mult *= 1.05
    if phase["key"] in {"swit","zmierzch"} and tool in {"fishing","herbalism"}:
        mult *= 1.04
    return {
        "label": f"Warunki: {weather['label']}, {phase['label']}",
        "quantity_bonus": 0,
        "xp_mult": round(mult, 4),
    }


def v0150_biome_mastery_title(kind, threshold):
    zone = V013_FRONTIER_SPECS[kind]["zone"]
    prefix = {25:"Wędrowiec",50:"Znawca",75:"Strażnik",100:"Mistrz"}.get(int(threshold), "Odkrywca")
    return f"{prefix}: {zone}"


def v0150_dynamic_quest_slot(now=None):
    now = time.time() if now is None else float(now)
    return int(now // V015_DYNAMIC_QUEST_SECONDS)


def v0150_dynamic_world_offer(account_id, now=None):
    slot = v0150_dynamic_quest_slot(now)
    kinds = tuple(V013_FRONTIER_SPECS)
    qtypes = ("explore", "event", "secret", "mini", "fish", "herb", "mine", "wood")
    qtype = qtypes[_v0140_hash_int("v015-dq-type", account_id, slot) % len(qtypes)]
    kind = kinds[_v0140_hash_int("v015-dq-kind", account_id, slot) % len(kinds)]
    target = kind if qtype in {"explore"} else "any"
    needs = {"explore":12, "event":2, "secret":2, "mini":1, "fish":12, "herb":12, "mine":12, "wood":12}
    labels = {
        "explore":f"Zbadaj nowe sektory: {V013_FRONTIER_SPECS[kind]['zone']}",
        "event":"Odwiedź aktywne wydarzenia świata", "secret":"Odkryj sekrety rubieży",
        "mini":"Dotrzyj do finału proceduralnego mini-lochu", "fish":"Złów ryby",
        "herb":"Zbierz zioła", "mine":"Wydobądź surowce", "wood":"Pozyskaj drewno",
    }
    needed = needs[qtype]
    stage=max(1,min(CHARACTER_MAX_LEVEL,int(V013_FRONTIER_SPECS[kind].get("base_mastery",1) or 1)))
    complexity=1.5 if qtype in {"event","secret","mini"} else 1.0
    reward_soul=max(1,int(round(v0190_log_curve(stage,V019_SOUL_KILL_NORMAL)*max(2.0,math.sqrt(needed))*complexity)))
    reward_coins=max(1,int(round(v0190_log_curve(stage,V019_QUEST_COIN)*complexity)))
    reward_gold=max(1,reward_coins//SILVER_PER_GOLD)
    return {
        "quest_key":f"v015:{slot}:{qtype}:{kind}", "quest_type":qtype, "target":target,
        "label":labels[qtype], "needed":needed, "progress":0, "reward_soul_xp":reward_soul,
        "reward_gold":reward_gold, "accepted_slot":slot, "completed":False,
    }

HELP_TOPICS["pogoda"] = [
    "pogoda / weather pokazuje aktualną pogodę, porę cyklu i ewentualny mały bonus profesyjny.",
    "Pogoda nigdy nie blokuje łowienia, zbierania, questów, ruchu ani walki. Nie ma kar za złą pogodę.",
    "Cykl świata ma Świt, Dzień, Zmierzch i Noc. Zmienia klimat oraz drobne bonusy, nie zamyka zawartości.",
]
HELP_TOPICS["biome_mastery"] = [
    "biom / mastery pokazuje postęp Biome Mastery proceduralnych rubieży.",
    "Progi 25, 50, 75 i 100 procent odkrycia odblokowują wpisy Codexu i tytuły.",
]
HELP_TOPICS["dynamiczne_questy"] = [
    "zadanie świata / worldquest pokazuje rotacyjną ofertę. worldquest accept przyjmuje ją od 0/x.",
    "Przyjęte zadanie nie znika po zmianie rotacji. worldquest aktywne pokazuje postęp, worldquest odbierz odbiera nagrodę.",
]
HELP_TOPIC_ALIASES.update({
    "pogoda":"pogoda", "weather":"pogoda", "pora dnia":"pogoda", "dzien noc":"pogoda",
    "biom":"biome_mastery", "mastery":"biome_mastery", "biome mastery":"biome_mastery",
    "zadanie swiata":"dynamiczne_questy", "zadanie świata":"dynamiczne_questy", "worldquest":"dynamiczne_questy",
})
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.


# ============================================================
# v0.16.0 - FACTIONS, TRAVELERS & WORLD BOSSES (NO TRAPS)
# ============================================================
V016_WORLD_BOSS_ROTATION_SECONDS = 2 * 60 * 60
V016_LEGENDARY_ROTATION_SECONDS = 60 * 60
V016_TRAVELER_STEP_SECONDS = 15 * 60
V016_FACTION_THRESHOLDS = (25, 75, 150, 300)

V016_FACTIONS = {
    "cartographers": {
        "name": "Liga Kartografów", "zone": "Rubieże i eksploracja",
        "desc": "Badacze dróg, sekretów, mini-lochów i nieopisanych sektorów.",
    },
    "waters": {
        "name": "Bractwo Wód", "zone": "Rzeki, jeziora, morza i ocean",
        "desc": "Rybacy, przewodnicy i badacze wielkich akwenów.",
    },
    "miners": {
        "name": "Kamienny Związek", "zone": "Góry i kopalnie",
        "desc": "Górnicy i poszukiwacze żył, minerałów i klejnotów.",
    },
    "green_path": {
        "name": "Krąg Zielonego Szlaku", "zone": "Lasy, łąki i mokradła",
        "desc": "Zielarze i drwale dbający o dzikie tereny i ich zasoby.",
    },
    "frontier_watch": {
        "name": "Straż Rubieży", "zone": "Łowy i najdalszy endgame",
        "desc": "Łowcy rare, legendary rare i world bossów. Walka zawsze pozostaje dobrowolna.",
    },
}

V016_FACTION_RANKS = (
    (0, "Nieznajomy"), (25, "Sympatyk"), (75, "Zaufany"),
    (150, "Sojusznik"), (300, "Mistrz Frakcji"),
)

for _fid, _fdata in V016_FACTIONS.items():
    _badge = f"v016_badge_{_fid}"
    _catalog_mut.catalog_setdefault_path('ITEMS', ITEMS, (), _badge, {
        "name": f"Odznaka: {_fdata['name']}", "type": "collectible", "price": None,
        "rarity": "unique", "rarity_name": "Unikalny",
        "desc": f"Pamiątkowa odznaka za wysoką reputację: {_fdata['name']}.",
    })


def v0160_faction_rank(reputation):
    reputation = max(0, int(reputation or 0))
    result = V016_FACTION_RANKS[0][1]
    for threshold, label in V016_FACTION_RANKS:
        if reputation >= threshold:
            result = label
    return result


# Pięć małych stałych punktów orientacyjnych przy proceduralnych rubieżach.
# Same rubieże nadal pozostają generowane; osady są kotwicami, nie nowymi miastami.
V016_SETTLEMENTS = {
    "cartographers": {
        "kind": "meadow", "branch": "east", "back": "west",
        "zone": "Posterunek Kartografów", "name": "Posterunek Kartografów",
        "rooms": (
            ("v016_cartographers_square", "Plac Map", "Stoły z mapami i tablicami kierunków stoją pod lekkimi zadaszeniami."),
            ("v016_cartographers_archive", "Archiwum Rubieży", "Małe archiwum przechowuje opisy odkrytych sektorów, sekretów i szlaków."),
            ("v016_cartographers_camp", "Obóz Mierniczych", "Kartografowie odpoczywają tu przed kolejnymi wyprawami."),
        ),
    },
    "waters": {
        "kind": "coast", "branch": "east", "back": "west",
        "zone": "Przystań Bractwa Wód", "name": "Przystań Bractwa Wód",
        "rooms": (
            ("v016_waters_square", "Nabrzeże Bractwa", "Pomosty i magazyny łączą rybaków rzek, jezior, mórz i oceanu."),
            ("v016_waters_hall", "Dom Sieci", "Wędkarze wymieniają informacje o ławicach, rekordach i nietypowych połowach."),
            ("v016_waters_store", "Skład Wodny", "Niewielki skład przechowuje sprzęt wyprawowy i skrzynie z połowami."),
        ),
    },
    "miners": {
        "kind": "mountain", "branch": "north", "back": "south",
        "zone": "Posterunek Kamiennego Związku", "name": "Posterunek Kamiennego Związku",
        "rooms": (
            ("v016_miners_square", "Kamienny Dziedziniec", "Punkt zbiórki górników przed wyprawami w góry i głębokie kopalnie."),
            ("v016_miners_hall", "Sala Żył", "Na kamiennych tablicach zaznaczono odkryte złoża i stare tunele."),
            ("v016_miners_workshop", "Warsztat Geologów", "Młotki, sita i próbki skał wypełniają niewielki warsztat."),
        ),
    },
    "green_path": {
        "kind": "forest", "branch": "north", "back": "south",
        "zone": "Osada Zielonego Szlaku", "name": "Osada Zielonego Szlaku",
        "rooms": (
            ("v016_green_square", "Polana Zielonego Szlaku", "Spokojna polana łączy szlaki zielarzy i drwali."),
            ("v016_green_hall", "Dom Ziół i Drewna", "Suszą się tu zioła, a próbki drewna opisano według regionów."),
            ("v016_green_garden", "Ogród Wędrowców", "Mały ogród pokazuje rośliny spotykane na wielu biomach."),
        ),
    },
    "frontier_watch": {
        "kind": "wild", "branch": "north", "back": "south",
        "zone": "Obóz Straży Rubieży", "name": "Obóz Straży Rubieży",
        "rooms": (
            ("v016_watch_square", "Plac Wielkich Łowów", "Tablice opisują tropy rare, legendary rare i world bossów."),
            ("v016_watch_hall", "Sala Tropicieli", "Łowcy porównują ślady i raporty z najdalszych rubieży."),
            ("v016_watch_rest", "Ognisko Straży", "Bezpieczne miejsce odpoczynku. Żaden przeciwnik nie atakuje tu automatycznie."),
        ),
    },
}


def v0160_build_settlements():
    for faction_id, data in V016_SETTLEMENTS.items():
        gateway = v0130_gateway_id(data["kind"])
        first, second, third = [row[0] for row in data["rooms"]]
        if gateway not in ROOMS:
            continue
        if data["branch"] not in ROOMS[gateway]["exits"]:
            _catalog_mut.catalog_assign(first, 'ROOMS', ROOMS, (gateway, "exits", data["branch"]))
        room_rows = data["rooms"]
        _catalog_mut.catalog_assign({
            "zone": data["zone"], "name": room_rows[0][1], "desc": room_rows[0][2],
            "exits": {data["back"]: gateway, "north": second, "east": third},
            "safe_hub": True, "v016_settlement": faction_id,
        }, 'ROOMS', ROOMS, (first,))
        _catalog_mut.catalog_assign({
            "zone": data["zone"], "name": room_rows[1][1], "desc": room_rows[1][2],
            "exits": {"south": first}, "safe_hub": True, "v016_settlement": faction_id,
        }, 'ROOMS', ROOMS, (second,))
        _catalog_mut.catalog_assign({
            "zone": data["zone"], "name": room_rows[2][1], "desc": room_rows[2][2],
            "exits": {"west": first}, "safe_hub": True, "v016_settlement": faction_id,
        }, 'ROOMS', ROOMS, (third,))
        GUIDE_DESTINATION_ALIASES[normalize_lookup_text(data["name"])] = first


v0160_build_settlements()
v0130_refresh_exploration_catalog()

# Stali wysłannicy frakcji w nowych małych osadach.
V016_FACTION_ENVOYS = {
    "cartographers": ("v016_envoy_cartographers", "Miernicza Alena", "v016_cartographers_archive"),
    "waters": ("v016_envoy_waters", "Rybak Orel", "v016_waters_hall"),
    "miners": ("v016_envoy_miners", "Geolog Daren", "v016_miners_hall"),
    "green_path": ("v016_envoy_green", "Zielarka Miva", "v016_green_hall"),
    "frontier_watch": ("v016_envoy_watch", "Herold Rubieży Iren", "v016_watch_hall"),
}
for _fid, (_nid, _name, _room) in V016_FACTION_ENVOYS.items():
    _catalog_mut.catalog_assign({
        "name": _name, "room": _room,
        "dialogue": f"Reprezentuję frakcję {V016_FACTIONS[_fid]['name']}. {V016_FACTIONS[_fid]['desc']} Użyj frakcje, aby sprawdzić reputację.",
        "v016_faction": _fid,
    }, 'NPCS', NPCS, (_nid,))

# Długi, sześcioczęściowy łańcuch. Każdy etap liczy tylko zdarzenia po przyjęciu,
# bo korzysta z istniejącego trwałego licznika aktywnego questa.
_catalog_mut.catalog_update_path('QUESTS', QUESTS, (), {
    "v016_frontier_oath_1": {
        "name":"Przysięga Rubieży I: Nowe Szlaki", "giver":"Herold Rubieży Iren",
        "kind":"explore_frontier", "target":"any", "needed":25,
        "description":"Odkryj 25 nowych proceduralnych sektorów po przyjęciu zadania.",
        "reward_silver":8000, "reward_gold":5, "reward_mithril":0,
        "reward_items":{V014_TREASURE_MAP_ITEM:1}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":15,
    },
    "v016_frontier_oath_2": {
        "name":"Przysięga Rubieży II: Żywy Świat", "giver":"Herold Rubieży Iren",
        "kind":"world_event", "target":"any", "needed":4, "requires_quest":"v016_frontier_oath_1",
        "description":"Odwiedź 4 nowe aktywne wydarzenia świata.",
        "reward_silver":11000, "reward_gold":7, "reward_mithril":0,
        "reward_items":{V014_TREASURE_MAP_ITEM:1}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":20,
    },
    "v016_frontier_oath_3": {
        "name":"Przysięga Rubieży III: Znaki Ukryte", "giver":"Herold Rubieży Iren",
        "kind":"discover_secret", "target":"any", "needed":4, "requires_quest":"v016_frontier_oath_2",
        "description":"Odkryj 4 nowe sekrety rubieży.",
        "reward_silver":14000, "reward_gold":9, "reward_mithril":0,
        "reward_items":{V014_TREASURE_MAP_ITEM:2}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":25,
    },
    "v016_frontier_oath_4": {
        "name":"Przysięga Rubieży IV: Małe Głębiny", "giver":"Herold Rubieży Iren",
        "kind":"mini_dungeon", "target":"any", "needed":3, "requires_quest":"v016_frontier_oath_3",
        "description":"Dotrzyj do finału 3 nowych proceduralnych mini-lochów.",
        "reward_silver":18000, "reward_gold":12, "reward_mithril":0,
        "reward_items":{"soul_elixir":2}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":30,
    },
    "v016_frontier_oath_5": {
        "name":"Przysięga Rubieży V: Legendarny Trop", "giver":"Herold Rubieży Iren",
        "kind":"legendary_rare", "target":"any", "needed":2, "requires_quest":"v016_frontier_oath_4",
        "description":"Pokonaj 2 legendary rare. Przeciwnicy są pasywni; gracz sam rozpoczyna walkę.",
        "reward_silver":24000, "reward_gold":16, "reward_mithril":0,
        "reward_items":{"soul_elixir":3}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":40,
    },
    "v016_frontier_oath_6": {
        "name":"Przysięga Rubieży VI: Wielki Łów", "giver":"Herold Rubieży Iren",
        "kind":"world_boss", "target":"any", "needed":1, "requires_quest":"v016_frontier_oath_5",
        "description":"Pokonaj jednego aktywnego world bossa. Boss nie atakuje pierwszy.",
        "reward_silver":35000, "reward_gold":25, "reward_mithril":1,
        "reward_items":{"soul_elixir":5, V014_TREASURE_MAP_ITEM:2}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":60,
    },
})
_catalog_mut.catalog_assign("v016_frontier_oath_1", 'NPCS', NPCS, ("v016_envoy_watch", "quest"))
_catalog_mut.catalog_assign(tuple(f"v016_frontier_oath_{i}" for i in range(1,7)), 'NPCS', NPCS, ("v016_envoy_watch", "quest_chain"))

# Wędrujący NPC. Ich trasa jest deterministyczna i zmienia punkt co 15 minut.
V016_TRAVELERS = {
    "v016_traveler_neria": {
        "name":"Kupczyni Neria", "faction":"waters",
        "dialogue":"Podróżuję między Rynkiem, portem i Przystanią Bractwa Wód. Zbieram wieści o połowach i eventach.",
        "route":("market","fish_market","harbor",v0130_gateway_id("coast"),"v016_waters_square"),
    },
    "v016_traveler_toren": {
        "name":"Kartograf Toren", "faction":"cartographers",
        "dialogue":"Porównuję stałe drogi z proceduralnymi rubieżami. Odkryte sektory nie zmieniają układu po restarcie.",
        "route":("library","square","north_gate",v0130_gateway_id("meadow"),"v016_cartographers_square"),
    },
    "v016_traveler_vela": {
        "name":"Wędrowna Zielarka Vela", "faction":"green_path",
        "dialogue":"Szukam roślin na łąkach, w lasach i mokradłach. Nie musisz walczyć z mobami, aby zbierać.",
        "route":("market","forest_edge",v0130_gateway_id("forest"),"v016_green_square",v0130_gateway_id("swamp")),
    },
    "v016_traveler_radan": {
        "name":"Górnik Radan", "faction":"miners",
        "dialogue":"Wędruję za nowymi żyłami. Kamienny Związek ceni regularną pracę, nie jednorazowy grind.",
        "route":("forge",v0130_gateway_id("mountain"),"v016_miners_square",v0130_gateway_id("frozen"),v0130_gateway_id("ash")),
    },
    "v016_traveler_arik": {
        "name":"Tropiciel Arik", "faction":"frontier_watch",
        "dialogue":"Śledzę legendary rare i world bossy. Każdy z nich jest pasywny, dopóki sam nie rozpoczniesz walki.",
        "route":("north_gate",v0130_gateway_id("wild"),"v016_watch_square",v0130_gateway_id("desert"),v0130_gateway_id("void")),
    },
}


def v0160_traveler_room(npc_id, now=None):
    data = V016_TRAVELERS.get(npc_id)
    if not data:
        return None
    now = time.time() if now is None else float(now)
    slot = int(now // V016_TRAVELER_STEP_SECONDS)
    route = tuple(r for r in data["route"] if r in ROOMS)
    if not route:
        return None
    offset = _v0140_hash_int("v016-traveler", npc_id) % len(route)
    return route[(slot + offset) % len(route)]


def v0160_npcs_in_room(room_id, now=None):
    result = {nid: npc for nid, npc in NPCS.items() if npc.get("room") == room_id}
    for npc_id, data in V016_TRAVELERS.items():
        if v0160_traveler_room(npc_id, now) == room_id:
            entry = dict(data)
            entry["room"] = room_id
            entry["v016_traveler"] = True
            result[npc_id] = entry
    return result


# --- Legendary rare i world bossy ---
def _v0160_clone_encounter_template(kind, encounter_type):
    spec = V013_FRONTIER_SPECS.get(kind, {})
    pool = [mid for mid in spec.get("mobs", ()) if mid in MOB_TEMPLATES]
    if not pool:
        return None
    base_id = pool[-1]
    base = MOB_TEMPLATES[base_id]
    if encounter_type == "world_boss":
        tid = f"v016_worldboss_{kind}"
        if tid in MOB_TEMPLATES:
            return tid
        mult_hp, mult_damage, mult_reward = 14.0, 2.25, 10.0
        prefix = f"Władca {spec['zone']}"
    else:
        tid = f"v016_legendary_{kind}"
        if tid in MOB_TEMPLATES:
            return tid
        mult_hp, mult_damage, mult_reward = 3.8, 1.60, 4.0
        prefix = f"Legendarny Trop {spec['zone']}"
    data = dict(base)
    data["drops"] = dict(base.get("drops", {}))
    data["name"] = f"{prefix}: {base['name']}"
    data["max_hp"] = max(1, int(round(int(base.get("max_hp", 1)) * mult_hp)))
    data["damage"] = max(1, int(round(int(base.get("damage", 1)) * mult_damage)))
    data["silver"] = max(1, int(round(int(base.get("silver", 1)) * mult_reward)))
    data["gold"] = max(1, int(base.get("gold", 0)) + (12 if encounter_type == "world_boss" else 4))
    data["mithril"] = int(base.get("mithril", 0)) + (1 if encounter_type == "world_boss" else 0)
    data["soul_reward"] = max(1, int(round(int(base.get("soul_reward", 1)) * mult_reward)))
    data["class_xp_reward"] = max(50, int(round(int(base.get("class_xp_reward", 50)) * mult_reward)))
    data["stat_reward"] = max(1, int(round(int(base.get("stat_reward", 1)) * min(2.5, mult_reward))))
    data["auto_aggro"] = False
    data["v016_biome"] = kind
    if encounter_type == "world_boss":
        data["world_boss"] = True
        data["v016_world_boss"] = True
        data["stationary_mob"] = True
        data["drops"].setdefault("soul_elixir", 0.65)
        data["drops"].setdefault(V014_TREASURE_MAP_ITEM, 0.80)
        BOSS_COLLECTION_CATALOG[tid] = data["name"]
    else:
        data["rare_mob"] = True
        data["v016_legendary_rare"] = True
        data["rare_base_template"] = base_id
        data.pop("stationary_mob", None)
        data["drops"].setdefault("soul_elixir", 0.35)
        data["drops"].setdefault(V014_TREASURE_MAP_ITEM, 0.55)
        RARE_MOB_COLLECTION_CATALOG[tid] = data["name"]
    _catalog_mut.catalog_assign(data, 'MOB_TEMPLATES', MOB_TEMPLATES, (tid,))
    return tid


for _kind in tuple(V013_FRONTIER_SPECS):
    _v0160_clone_encounter_template(_kind, "legendary_rare")
    _v0160_clone_encounter_template(_kind, "world_boss")


def _v0160_active_encounters(encounter_type, now=None):
    now = time.time() if now is None else float(now)
    if encounter_type == "world_boss":
        seconds, count = V016_WORLD_BOSS_ROTATION_SECONDS, 3
    else:
        seconds, count = V016_LEGENDARY_ROTATION_SECONDS, 5
    slot = int(now // seconds)
    rng = random.Random(_v0140_hash_int("v016-encounter", encounter_type, slot))
    kinds = list(V013_FRONTIER_SPECS)
    rng.shuffle(kinds)
    result = []
    used = set()
    for index, kind in enumerate(kinds[:count]):
        for _ in range(30):
            x = rng.randrange(V013_FRONTIER_SIDE)
            y = rng.randrange(V013_FRONTIER_SIDE)
            room_id = v0130_frontier_room_id(kind, x, y)
            if room_id not in used:
                break
        used.add(room_id)
        tid = _v0160_clone_encounter_template(kind, encounter_type)
        result.append({
            "type": encounter_type, "kind": kind, "x": x, "y": y,
            "room_id": room_id, "template_id": tid, "slot": slot,
            "token": f"{slot}:{encounter_type}:{kind}:{x}:{y}",
            "expires_at": (slot + 1) * seconds,
        })
    return tuple(result)


def v0160_active_world_bosses(now=None):
    return _v0160_active_encounters("world_boss", now)


def v0160_active_legendary_rares(now=None):
    return _v0160_active_encounters("legendary_rare", now)


def v0160_encounters_for_room(room_id, now=None):
    return tuple(
        e for e in (v0160_active_world_bosses(now) + v0160_active_legendary_rares(now))
        if e["room_id"] == room_id
    )


HELP_TOPICS["frakcje_v016"] = [
    "frakcje / factions pokazuje reputację pięciu frakcji świata.",
    "Reputacja rośnie naturalnie przez eksplorację, profesje oraz wielkie łowy. Nie jest wymagana do głównej progresji.",
    "Progi 25/75/150/300 dają tytuły lub jednorazowe drobne nagrody kolekcjonerskie.",
]
HELP_TOPICS["wielkie_lowy_v016"] = [
    "worldbossy pokazuje trzy aktywne world bossy rotujące co 2 godziny.",
    "legendy pokazuje pięć aktywnych legendary rare rotujących co godzinę.",
    "Wszystkie są objęte PASSIVE WORLD: nie rozpoczynają walki automatycznie.",
]
HELP_TOPICS["podroznicy_v016"] = [
    "podroznicy pokazuje aktualne miejsca pięciu wędrujących NPC. Zmieniają punkt trasy co 15 minut.",
    "Wędrowcy poruszają się wyłącznie po bezpiecznej, stałej sieci hubów i granic biomów.",
]
HELP_TOPIC_ALIASES.update({
    "frakcje":"frakcje_v016", "factions":"frakcje_v016", "reputacja frakcji":"frakcje_v016",
    "world bossy":"wielkie_lowy_v016", "worldbossy":"wielkie_lowy_v016", "legendary rare":"wielkie_lowy_v016",
    "podroznicy":"podroznicy_v016", "podróżnicy":"podroznicy_v016", "travelers":"podroznicy_v016",
})
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.


# ============================================================
# v0.17.0 - ARTIFACTS, BIOME SETS, BOSS MECHANICS & FACTION STORIES
# No traps. PASSIVE WORLD remains global.
# ============================================================
V017_ARTIFACTS = {
    "cartographers": {
        "item_id":"v017_artifact_compass", "name":"Kompas Pierwszej Rubieży",
        "effect":"Maksymalne HP/Mana +5%, obrona +3%.",
        "hp":1.05, "damage":1.00, "defense":1.03, "defense_flat":11,
    },
    "waters": {
        "item_id":"v017_artifact_tideheart", "name":"Serce Wiecznego Przypływu",
        "effect":"Maksymalne HP/Mana +7%.",
        "hp":1.07, "damage":1.00, "defense":1.00, "defense_flat":10,
    },
    "miners": {
        "item_id":"v017_artifact_worldstone", "name":"Odłamek Kamienia Świata",
        "effect":"Obrona +7%.",
        "hp":1.00, "damage":1.00, "defense":1.07, "defense_flat":15,
    },
    "green_path": {
        "item_id":"v017_artifact_verdant_seed", "name":"Nasienie Pradawnego Gaju",
        "effect":"Maksymalne HP/Mana +4%, obrona +4%.",
        "hp":1.04, "damage":1.00, "defense":1.04, "defense_flat":12,
    },
    "frontier_watch": {
        "item_id":"v017_artifact_hunter_mark", "name":"Znak Pierwszego Łowcy",
        "effect":"Obrażenia +7%.",
        "hp":1.00, "damage":1.07, "defense":1.00, "defense_flat":12,
    },
}

for _fid, _artifact in V017_ARTIFACTS.items():
    _iid = _artifact["item_id"]
    _catalog_mut.catalog_assign({
        "name": _artifact["name"], "type":"armor", "slot":"charm",
        "defense": int(_artifact["defense_flat"]), "price":None,
        "rarity":"legendary", "rarity_name":"Artefakt", "sockets":3,
        "v017_artifact": _fid,
        "artifact_hp_multiplier": float(_artifact["hp"]),
        "artifact_damage_multiplier": float(_artifact["damage"]),
        "artifact_defense_multiplier": float(_artifact["defense"]),
        "desc": (
            f"Unikalny artefakt frakcji {V016_FACTIONS[_fid]['name']}. "
            f"{_artifact['effect']} Można mieć założony w slocie talizmanu."
        ),
    }, 'ITEMS', ITEMS, (_iid,))
    UNIQUE_ITEM_COLLECTION_CATALOG[_iid] = _artifact["name"]
    EQUIPMENT_COLLECTION_CATALOG[_iid] = _artifact["name"]

# 15 biome-specific six-piece sets. They deliberately reuse the existing regional
# set engine, so all old EQ/set commands continue to work.
V017_BIOME_SET_NAMES = {
    "meadow":"Zestaw Kwitnących Łąk", "forest":"Zestaw Starego Boru",
    "wild":"Zestaw Nieujarzmionej Dziczy", "mountain":"Zestaw Kamiennej Grani",
    "swamp":"Zestaw Czarnego Rozlewiska", "desert":"Zestaw Szklanego Piasku",
    "coast":"Zestaw Sztormowego Wybrzeża", "ocean":"Zestaw Otwartej Toni",
    "river":"Zestaw Rzecznego Nurtu", "lake":"Zestaw Cichego Pojezierza",
    "frozen":"Zestaw Wiecznego Szronu", "ash":"Zestaw Popielnego Żaru",
    "sky":"Zestaw Rozdartego Nieba", "void":"Zestaw Bezgwiezdnej Pustki",
    "crown":"Zestaw Korony Absolutu",
}
V017_BIOME_SET_ITEMS = {}
_v017_slots = (("head","Hełm"),("body","Pancerz"),("hands","Rękawice"),("legs","Nogawice"),("feet","Buty"),("charm","Talizman"))
_v017_affixes = ("strength","dexterity","constitution","intelligence","willpower","charisma")
for _idx, (_kind, _spec) in enumerate(V013_FRONTIER_SPECS.items()):
    _sid = f"v017_{_kind}"
    _endgame = int(_spec.get("base_mastery", 1)) >= 200
    REGIONAL_SET_BONUSES[_sid] = {
        "name": V017_BIOME_SET_NAMES[_kind],
        "hp": 1.08 if _endgame else 1.06,
        "damage": 1.10 if _endgame else 1.08,
        "defense": 1.10 if _endgame else 1.08,
    }
    _ids = []
    _base_def = 7 + min(11, int(_spec.get("base_mastery", 1)) // 35)
    for _slot_index, (_slot, _slot_label) in enumerate(_v017_slots):
        _iid = f"v017_set_{_kind}_{_slot}"
        _affix = _v017_affixes[(_idx + _slot_index) % len(_v017_affixes)]
        _amount = 3 + min(7, int(_spec.get("base_mastery", 1)) // 55)
        _catalog_mut.catalog_assign({
            "name": f"{_slot_label} — {V017_BIOME_SET_NAMES[_kind]}",
            "type":"armor", "slot":_slot,
            "defense": _base_def + _slot_index // 2,
            "price":None, "rarity":"epic", "rarity_name":"Epicki",
            "affix":_affix, "affix_amount":_amount,
            "regional_set":_sid, "v017_biome_set":_kind,
            "desc": (
                f"Część biomowego zestawu {V017_BIOME_SET_NAMES[_kind]}. "
                "Progi 2/4/6 wzmacniają HP/Mana, obrażenia i obronę. "
                "Zdobywana z legendary rare i world bossów odpowiedniego biomu."
            ),
        }, 'ITEMS', ITEMS, (_iid,))
        EQUIPMENT_COLLECTION_CATALOG[_iid] = ITEMS[_iid]["name"]
        _ids.append(_iid)
    V017_BIOME_SET_ITEMS[_kind] = tuple(_ids)

# Existing combat already supports distinct mechanics + 75/50/25% boss phases.
# v0.17 assigns those mechanics to every biome world boss and legendary rare.
V017_BIOME_BOSS_MECHANICS = {
    "meadow":("blood_drain","Drenaż Życia: okresowo wysysa część zadanych obrażeń."),
    "forest":("spectral_shift","Leśna Zmiana: kontrataki przeplatają obrażenia fizyczne i magiczne."),
    "wild":("bone_crush","Miażdżenie: co trzeci kontratak jest znacznie silniejszy."),
    "mountain":("giant_crush","Miażdżenie Giganta: okresowy ciężki kontratak fizyczny."),
    "swamp":("necro_regen","Regeneracja Bagna: boss okresowo odzyskuje część HP."),
    "desert":("ash_curse","Klątwa Pyłu: okresowy magiczny kontratak częściowo ignoruje obronę."),
    "coast":("blood_drain","Drenaż Przypływu: specjalny kontratak leczy przeciwnika."),
    "ocean":("spectral_shift","Zmiana Głębi: typ obrażeń zmienia się między turami."),
    "river":("bone_rage","Furia Nurtu: poniżej połowy HP kontrataki stają się mocniejsze."),
    "lake":("necro_regen","Odnowa Głębin: przeciwnik okresowo regeneruje HP."),
    "frozen":("crystal_lord","Kryształowy Promień i bariera wzmacniają walkę fazową."),
    "ash":("black_flame","Czarny Płomień: silny magiczny kontratak częściowo ignorujący obronę."),
    "sky":("stellar_storm","Gwiezdna Burza: cykliczny silny magiczny kontratak."),
    "void":("astral_sovereign","Faza Suwerena: poniżej połowy HP rośnie siła, a specjalny atak ignoruje część obrony."),
    "crown":("two_hundred_lord","Załamanie Wieczności: wielofazowy endgame'owy profil kontrataków."),
}

for _kind, (_mechanic, _mechanic_text) in V017_BIOME_BOSS_MECHANICS.items():
    _pool = list(V017_BIOME_SET_ITEMS[_kind])
    for _prefix, _enc_type in (("v016_worldboss_","world_boss"),("v016_legendary_","legendary_rare")):
        _tid = _prefix + _kind
        _t = MOB_TEMPLATES.get(_tid)
        if not _t:
            continue
        _t["boss_mechanic"] = _mechanic
        _t["boss_mechanic_text"] = (
            _mechanic_text + " Dodatkowo walka ma fazy przy 75, 50 i 25 procent HP. "
            "PASSIVE WORLD: przeciwnik nie rozpoczyna walki sam."
        )
        _t["auto_aggro"] = False
        _t["v017_boss_phases"] = True
        _t["corpse_equipment_pool"] = _pool
        _t["corpse_equipment_guaranteed"] = max(
            int(_t.get("corpse_equipment_guaranteed", 0) or 0),
            2 if _enc_type == "world_boss" else 1,
        )

# New six-stage faction stories. The old Frontier Oath remains intact and the
# new Straż Rubieży story is appended after it.
V017_FACTION_STORIES = {
    "cartographers": {"biome":"meadow", "title":"Szlak Pierwszych Map"},
    "waters": {"biome":"ocean", "title":"Pieśń Wielkich Wód"},
    "miners": {"biome":"mountain", "title":"Głos Kamienia"},
    "green_path": {"biome":"forest", "title":"Korzenie Zielonego Szlaku"},
    "frontier_watch": {"biome":"wild", "title":"Legenda Straży Rubieży"},
}
V017_FACTION_STORY_QUESTS = {}
_v017_stage_specs = (
    ("I", "Rozpoznanie", "explore_frontier", 15, 12, 7000, 4),
    ("II", "Żywy Znak", "world_event", 2, 15, 9000, 6),
    ("III", "Ukryta Droga", "discover_secret", 2, 18, 12000, 8),
    ("IV", "Głębia Szlaku", "mini_dungeon", 2, 22, 16000, 10),
    ("V", "Legendarny Ślad", "legendary_rare", 1, 28, 22000, 14),
    ("VI", "Próba Mistrza", "world_boss", 1, 40, 32000, 20),
)
for _fid, _story in V017_FACTION_STORIES.items():
    _envoy = V016_FACTION_ENVOYS[_fid][0]
    _prev = None
    _chain = []
    for _stage_no, (_roman, _stage_name, _kind, _needed, _rep, _silver, _gold) in enumerate(_v017_stage_specs, 1):
        _qid = f"v017_{_fid}_{_stage_no}"
        _chain.append(_qid)
        _q = {
            "name":f"{_story['title']} {_roman}: {_stage_name}",
            "giver":V016_FACTION_ENVOYS[_fid][1],
            "kind":_kind, "target":_story["biome"], "needed":_needed,
            "description":(
                f"Etap historii frakcji {V016_FACTIONS[_fid]['name']}. "
                f"Cel dotyczy biomu {V013_FRONTIER_SPECS[_story['biome']]['zone']}. "
                "Postęp liczy wyłącznie zdarzenia po przyjęciu questa."
            ),
            "reward_silver":_silver, "reward_gold":_gold, "reward_mithril":0,
            "reward_items":{}, "repeatable":False,
            "reward_faction_v016":_fid, "reward_faction_amount_v016":_rep,
            "v017_faction_story":_fid,
        }
        if _prev:
            _q["requires_quest"] = _prev
        if _stage_no == 6:
            _q["reward_items"] = {V017_ARTIFACTS[_fid]["item_id"]:1, "soul_elixir":3}
            _q["reward_mithril"] = 1
        elif _stage_no in (3,5):
            _q["reward_items"] = {V014_TREASURE_MAP_ITEM:1}
        _catalog_mut.catalog_assign(_q, 'QUESTS', QUESTS, (_qid,))
        _prev = _qid
    V017_FACTION_STORY_QUESTS[_fid] = tuple(_chain)
    _old_chain = tuple(NPCS[_envoy].get("quest_chain", ()))
    _catalog_mut.catalog_assign(_old_chain + tuple(_chain), 'NPCS', NPCS, (_envoy, "quest_chain"))
    if not NPCS[_envoy].get("quest"):
        _catalog_mut.catalog_assign(_chain[0], 'NPCS', NPCS, (_envoy, "quest"))
    _catalog_mut.catalog_aug_path('NPCS', NPCS, (_envoy, "dialogue"), 'Add', f" Mam też dla ciebie historię: {_story['title']}.")

# v0.24.1: finalny pass po WSZYSTKICH definicjach questów.
# Część zadań z późniejszych wersji była dopisywana już po historycznych
# normalizatorach v0.8.66, więc porządkujemy je ponownie globalnie.
normalize_profession_requirements_v0866()
normalize_quest_progress_tracking_v0866()
ensure_profession_quest_currency_v098()

HELP_TOPICS["artefakty_v017"] = [
    "artefakty / artifacts pokazuje 5 unikalnych artefaktów frakcyjnych i ich efekty.",
    "Artefakt otrzymujesz za finał nowej historii danej frakcji. Każdy zajmuje slot talizmanu, więc wybierasz aktywny efekt.",
]
HELP_TOPICS["sety_biomowe_v017"] = [
    "setybiomowe / biomesets pokazuje 15 zestawów biomowych po 6 części.",
    "Legendary rare daje co najmniej 1 część swojego biomu, a world boss co najmniej 2. Progi 2/4/6 wzmacniają HP/Mana, obrażenia i obronę.",
]
HELP_TOPICS["historie_frakcji_v017"] = [
    "historiefrakcji / factionstories pokazuje postęp nowych sześcioczęściowych historii wszystkich 5 frakcji.",
    "Każdy etap zaczyna od 0/x i liczy tylko zdarzenia wykonane po przyjęciu.",
]
HELP_TOPIC_ALIASES.update({
    "artefakty":"artefakty_v017", "artifacts":"artefakty_v017",
    "sety biomowe":"sety_biomowe_v017", "biomesets":"sety_biomowe_v017",
    "historie frakcji":"historie_frakcji_v017", "faction stories":"historie_frakcji_v017",
})
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.


# ============================================================
# v0.18.0 - SEASONS, EXPEDITIONS & ENDGAME
# Seasons + archipelagos + transport + great ruins + legendary events
# + first endless endgame layer. NO TRAPS. PASSIVE WORLD remains global.
# ============================================================
V018_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0180-seasons-expeditions-endgame"
V018_SEASON_SECONDS = 6 * 60 * 60
V018_LEGENDARY_EVENT_SECONDS = 4 * 60 * 60
V018_GREAT_RUIN_DENOMINATOR = 48
V018_ENDLESS_POWER_CAP_BAND = 40

V018_SEASONS = (
    ("spring", "Wiosna", "Świat budzi się do życia; zioła i rzeki są szczególnie aktywne."),
    ("summer", "Lato", "Długie dni sprzyjają połowom morskim i pracy w otwartym terenie."),
    ("autumn", "Jesień", "Dojrzałe lasy i zioła dają stabilne warunki zbieractwa."),
    ("winter", "Zima", "Mróz wzmacnia górskie i lodowe wyprawy, ale niczego nie blokuje."),
)


def v0180_season_state(now=None):
    now = time.time() if now is None else float(now)
    slot = int(now // V018_SEASON_SECONDS)
    key, label, desc = V018_SEASONS[slot % len(V018_SEASONS)]
    return {
        "key": key, "label": label, "desc": desc, "slot": slot,
        "expires_at": (slot + 1) * V018_SEASON_SECONDS,
    }


def v0180_season_profession_multiplier(tool_type=None, now=None):
    tool = str(tool_type or "")
    season = v0180_season_state(now)["key"]
    table = {
        "spring": {"herbalism":1.08, "fishing":1.05},
        "summer": {"fishing":1.08, "woodcutting":1.04},
        "autumn": {"woodcutting":1.08, "herbalism":1.05},
        "winter": {"mining":1.08, "fishing":1.03},
    }
    return float(table.get(season, {}).get(tool, 1.0))


# Wrap the mature v0.15 environment system instead of replacing it.
_v0180_environment_bonus_base = v0150_environment_bonus
def v0150_environment_bonus(room_id, tool_type=None, now=None):
    base = dict(_v0180_environment_bonus_base(room_id, tool_type=tool_type, now=now))
    season = v0180_season_state(now)
    mult = v0180_season_profession_multiplier(tool_type, now)
    # Legendary world events may add a small, optional profession bonus.
    levent = v0180_legendary_event_for_room(room_id, now=now) if "v0180_legendary_event_for_room" in globals() else None
    if levent and levent.get("tool") == str(tool_type or ""):
        mult *= float(levent.get("xp_mult", 1.0) or 1.0)
        base["quantity_bonus"] = int(base.get("quantity_bonus", 0) or 0) + int(levent.get("quantity_bonus", 0) or 0)
    base["xp_mult"] = max(1.0, float(base.get("xp_mult", 1.0) or 1.0)) * max(1.0, mult)
    labels = [str(base.get("label", "") or ""), f"Sezon: {season['label']}"]
    if levent and levent.get("tool") == str(tool_type or ""):
        labels.append(f"LEGENDARNE WYDARZENIE — {levent['title']}")
    base["label"] = " + ".join(x for x in labels if x)
    return base


# ------------------------------------------------------------
# Ocean expeditions: five deterministic 4x4 archipelagos.
# ------------------------------------------------------------
V018_EXPEDITIONS = {
    "coral": {"name":"Archipelag Koralowy", "zone":"Archipelag Koralowy", "biome":"ocean", "mastery":120,
              "titles":("Koralowa Laguna","Wyspa Białych Muszli","Rafa Szmaragdowa","Ciepła Zatoka")},
    "storm": {"name":"Archipelag Burz", "zone":"Archipelag Burz", "biome":"coast", "mastery":190,
              "titles":("Wyspa Gromów","Sztormowy Klif","Zatoka Piorunów","Czarna Rafa")},
    "mist": {"name":"Mgliste Wyspy", "zone":"Mgliste Wyspy", "biome":"lake", "mastery":240,
              "titles":("Wyspa Mgieł","Cicha Laguna","Kamienny Przesmyk","Ukryta Zatoka")},
    "frost": {"name":"Archipelag Szronu", "zone":"Archipelag Szronu", "biome":"frozen", "mastery":320,
              "titles":("Lodowa Wyspa","Zamarznięty Brzeg","Błękitna Rafa","Zatoka Szronu")},
    "void": {"name":"Wyspy Czarnego Przypływu", "zone":"Wyspy Czarnego Przypływu", "biome":"void", "mastery":390,
              "titles":("Bezgwiezdna Wyspa","Czarna Laguna","Martwa Rafa","Molo Pustki")},
}
V018_EXPEDITION_SIDE = 4


def v0180_archipelago_room_id(expedition_id, x, y):
    return f"v018_arch_{expedition_id}_{int(x):02d}_{int(y):02d}"


def v0180_archipelago_identity(room_id):
    m = re.fullmatch(r"v018_arch_([a-z]+)_(\d{2})_(\d{2})", str(room_id or ""))
    if not m:
        return None
    eid, sx, sy = m.groups()
    if eid not in V018_EXPEDITIONS:
        return None
    x, y = int(sx), int(sy)
    if not (0 <= x < V018_EXPEDITION_SIDE and 0 <= y < V018_EXPEDITION_SIDE):
        return None
    return eid, x, y


def v0180_archipelago_room_ids(expedition_id):
    return tuple(v0180_archipelago_room_id(expedition_id, x, y)
                 for y in range(V018_EXPEDITION_SIDE) for x in range(V018_EXPEDITION_SIDE))


def v0180_create_archipelago_room_definition(room_id):
    ident = v0180_archipelago_identity(room_id)
    if not ident:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    eid, x, y = ident
    spec = V018_EXPEDITIONS[eid]
    seed = _v0140_hash_int("v018-arch", eid, x, y)
    rng = random.Random(seed)
    exits = {}
    if x > 0: exits["west"] = v0180_archipelago_room_id(eid, x-1, y)
    if x+1 < V018_EXPEDITION_SIDE: exits["east"] = v0180_archipelago_room_id(eid, x+1, y)
    if y > 0: exits["south"] = v0180_archipelago_room_id(eid, x, y-1)
    if y+1 < V018_EXPEDITION_SIDE: exits["north"] = v0180_archipelago_room_id(eid, x, y+1)
    if x == 0 and y == 0:
        exits["down"] = "harbor"
    title = rng.choice(spec["titles"])
    _catalog_mut.catalog_assign({
        "zone":spec["zone"], "name":f"{title} — sektor {x+1}-{y+1}",
        "desc":(
            f"Sektor ekspedycji na {spec['name']}. Wyspy są generowane z trwałego seedu; "
            "po restarcie zachowują układ. Powrót do Portu Dusz prowadzi z pierwszego sektora w dół."
        ),
        "exits":exits, "recommended_mastery":int(spec["mastery"]),
        "generated_on_demand":True, "v018_archipelago":eid,
        "v018_arch_x":x, "v018_arch_y":y,
    }, 'ROOMS', ROOMS, (room_id,))
    # Island gathering ecology: marine fishing everywhere; some later islands also support herbs/mining.
    FISHING_ROOMS.add(room_id); MARINE_FISHING_ROOMS.add(room_id); OCEAN_FISHING_ROOMS.add(room_id)
    FISHING_WATER_TYPE_OVERRIDES[room_id] = spec["name"]
    if eid in ("coral","mist") and (x+y)%2 == 0:
        HERBALISM_ROOMS.add(room_id)
    # v0.25.1: ekspedycje nie są już alternatywnymi kopalniami.
    base_kind = spec["biome"]
    pool = [t for t in V013_FRONTIER_SPECS[base_kind].get("mobs",()) if t in MOB_TEMPLATES]
    spawns = []
    if pool:
        for _ in range(1 + (1 if rng.random() < 0.45 else 0)):
            spawns.append((room_id, rng.choice(pool)))
    return room_id, tuple(spawns)


# ------------------------------------------------------------
# Great procedural ruins: rarer than mini-dungeons, 20-40 rooms.
# ------------------------------------------------------------
def v0180_has_great_ruin(kind, x, y):
    if kind not in V013_FRONTIER_SPECS:
        return False
    return _v0140_hash_int("v018-great-ruin", kind, int(x), int(y)) % V018_GREAT_RUIN_DENOMINATOR == 0


def v0180_ruin_size(kind, x, y):
    return 20 + (_v0140_hash_int("v018-ruin-size", kind, int(x), int(y)) % 21)


def v0180_ruin_room_id(kind, x, y, index):
    return f"v018_ruin_{kind}_{int(x):02d}_{int(y):02d}_{int(index):02d}"


def v0180_ruin_identity(room_id):
    m = re.fullmatch(r"v018_ruin_([a-z]+)_(\d{2})_(\d{2})_(\d{2})", str(room_id or ""))
    if not m:
        return None
    kind, sx, sy, si = m.groups()
    if kind not in V013_FRONTIER_SPECS:
        return None
    x,y,index = int(sx),int(sy),int(si)
    if not (0 <= x < V013_FRONTIER_SIDE and 0 <= y < V013_FRONTIER_SIDE):
        return None
    size = v0180_ruin_size(kind,x,y)
    if not v0180_has_great_ruin(kind,x,y) or not (1 <= index <= size):
        return None
    return kind,x,y,index,size


V018_RUIN_GUARDIANS = {}
for _kind, _spec in V013_FRONTIER_SPECS.items():
    _base = MOB_TEMPLATES.get(f"v016_legendary_{_kind}")
    if not _base:
        continue
    _tid = f"v018_ruin_guardian_{_kind}"
    _data = dict(_base)
    _data["drops"] = dict(_base.get("drops",{}))
    _data["name"] = f"Strażnik Wielkich Ruin: {_base['name']}"
    _data["max_hp"] = max(1, int(int(_base.get("max_hp",1))*1.45))
    _data["damage"] = max(1, int(int(_base.get("damage",1))*1.18))
    _data["soul_reward"] = max(1, int(int(_base.get("soul_reward",1))*1.35))
    _data["class_xp_reward"] = max(1, int(int(_base.get("class_xp_reward",1))*1.30))
    _data["world_boss"] = True; _data["mini_boss"] = True
    _data["stationary_mob"] = True; _data["auto_aggro"] = False
    _data["v018_great_ruin_guardian"] = True; _data["v018_biome"] = _kind
    _catalog_mut.catalog_assign(_data, 'MOB_TEMPLATES', MOB_TEMPLATES, (_tid,))
    V018_RUIN_GUARDIANS[_kind] = _tid


def v0180_create_ruin_room_definition(room_id):
    ident = v0180_ruin_identity(room_id)
    if not ident:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind,x,y,index,size = ident
    seed = _v0140_hash_int("v018-ruin-room",kind,x,y,index)
    rng = random.Random(seed)
    exits = {}
    if index > 1: exits["west"] = v0180_ruin_room_id(kind,x,y,index-1)
    if index < size: exits["east"] = v0180_ruin_room_id(kind,x,y,index+1)
    # deterministic cross-links create loops and alternative paths, never traps.
    if index % 4 == 1 and index + 4 <= size:
        exits["north"] = v0180_ruin_room_id(kind,x,y,index+4)
    if index >= 5 and (index-4) % 4 == 1:
        exits["south"] = v0180_ruin_room_id(kind,x,y,index-4)
    if index == 1:
        exits["down"] = v0130_frontier_room_id(kind,x,y)
    final = index == size
    zone = f"Wielkie Ruiny — {V013_FRONTIER_SPECS[kind]['zone']}"
    names = ("Galeria Run","Zawalona Nawa","Sala Kolumn","Kamienny Dziedziniec","Archiwum Ruin","Korytarz Posągów")
    _catalog_mut.catalog_assign({
        "zone":zone, "name":f"{rng.choice(names)} {index}/{size}",
        "desc":(
            "Rozległy fragment proceduralnych ruin. Układ jest deterministyczny, ma pętle i alternatywne przejścia. "
            + ("To finałowa komnata strażnika. " if final else "")
            + "Nie ma tu pułapek ani automatycznych obrażeń wejściowych."
        ),
        "exits":exits, "recommended_mastery":min(CHARACTER_MAX_LEVEL, int(V013_FRONTIER_SPECS[kind].get("base_mastery",1))+40),
        "generated_on_demand":True, "v018_great_ruin":True, "v018_ruin_final":final,
        "v018_biome":kind, "v018_ruin_parent":v0130_frontier_room_id(kind,x,y),
    }, 'ROOMS', ROOMS, (room_id,))
    spawns=[]
    pool=[t for t in V013_FRONTIER_SPECS[kind].get("mobs",()) if t in MOB_TEMPLATES]
    if final and kind in V018_RUIN_GUARDIANS:
        spawns.append((room_id,V018_RUIN_GUARDIANS[kind]))
    elif pool and rng.random() < 0.82:
        spawns.append((room_id,rng.choice(pool)))
        if rng.random() < 0.33: spawns.append((room_id,rng.choice(pool)))
    return room_id, tuple(spawns)


def v0180_all_great_ruins():
    result=[]
    for kind in V013_FRONTIER_SPECS:
        for y in range(V013_FRONTIER_SIDE):
            for x in range(V013_FRONTIER_SIDE):
                if v0180_has_great_ruin(kind,x,y):
                    result.append((kind,x,y,v0180_ruin_size(kind,x,y)))
    return tuple(result)


# ------------------------------------------------------------
# Legendary World Events: two major events every 4 hours.
# ------------------------------------------------------------
V018_LEGENDARY_EVENT_DEFS = {
    "titan_awakening":{"title":"Przebudzenie Tytana","kinds":tuple(V013_FRONTIER_SPECS),"tool":None,"desc":"W sektorze pojawił się potężny pasywny Tytan. Gracz sam decyduje o walce."},
    "great_bloom":{"title":"Wielki Rozkwit","kinds":("meadow","forest","swamp","river"),"tool":"herbalism","xp_mult":1.18,"quantity_bonus":1,"desc":"Rzadki rozkwit wzmacnia Zielarstwo w tym sektorze."},
    "ocean_convergence":{"title":"Zbieg Wielkich Prądów","kinds":("coast","ocean","river","lake","void"),"tool":"fishing","xp_mult":1.18,"quantity_bonus":1,"desc":"Wody zbiegają się w wyjątkową ławicę."},
    "deep_vein":{"title":"Przebudzenie Głębokiej Żyły","kinds":("mountain","desert","frozen","ash","sky","crown"),"tool":"mining","xp_mult":1.18,"quantity_bonus":1,"desc":"Głęboka żyła minerału odsłoniła się na krótki czas."},
    "ancient_growth":{"title":"Pradawny Rozrost","kinds":("forest","wild","meadow"),"tool":"woodcutting","xp_mult":1.18,"quantity_bonus":1,"desc":"Stare drzewa przechodzą niezwykły okres wzrostu."},
}


def v0180_legendary_event_slot(now=None):
    now=time.time() if now is None else float(now)
    return int(now//V018_LEGENDARY_EVENT_SECONDS)


def v0180_active_legendary_events(now=None):
    now=time.time() if now is None else float(now)
    slot=v0180_legendary_event_slot(now)
    keys=tuple(V018_LEGENDARY_EVENT_DEFS)
    picked=[]; used=set()
    for n in range(2):
        etype=keys[_v0140_hash_int("v018-legend-event-type",slot,n)%len(keys)]
        # ensure distinct type when possible
        if etype in used:
            etype=keys[(keys.index(etype)+1)%len(keys)]
        used.add(etype)
        d=V018_LEGENDARY_EVENT_DEFS[etype]
        kinds=tuple(d["kinds"])
        kind=kinds[_v0140_hash_int("v018-legend-event-kind",slot,n)%len(kinds)]
        x=_v0140_hash_int("v018-legend-event-x",slot,n)%V013_FRONTIER_SIDE
        y=_v0140_hash_int("v018-legend-event-y",slot,n)%V013_FRONTIER_SIDE
        room_id=v0130_frontier_room_id(kind,x,y)
        picked.append({
            "type":etype,"title":d["title"],"desc":d["desc"],"kind":kind,"x":x,"y":y,"room_id":room_id,
            "tool":d.get("tool"),"xp_mult":float(d.get("xp_mult",1.0)),"quantity_bonus":int(d.get("quantity_bonus",0)),
            "slot":slot,"token":f"{slot}:{etype}:{kind}:{x}:{y}","expires_at":(slot+1)*V018_LEGENDARY_EVENT_SECONDS,
        })
    return tuple(picked)


def v0180_legendary_event_for_room(room_id, now=None):
    return next((e for e in v0180_active_legendary_events(now) if e["room_id"]==room_id),None)


# Passive Titan templates reuse the proven v0.16/v0.17 world-boss profiles.
V018_TITAN_TEMPLATES={}
for _kind in V013_FRONTIER_SPECS:
    _base=MOB_TEMPLATES.get(f"v016_worldboss_{_kind}")
    if not _base: continue
    _tid=f"v018_titan_{_kind}"
    _data=dict(_base); _data["drops"]=dict(_base.get("drops",{}))
    _data["name"]=f"Przebudzony Tytan: {_base['name']}"
    _data["max_hp"]=max(1,int(int(_base.get("max_hp",1))*1.60))
    _data["damage"]=max(1,int(int(_base.get("damage",1))*1.22))
    _data["soul_reward"]=max(1,int(int(_base.get("soul_reward",1))*1.50))
    _data["auto_aggro"]=False; _data["stationary_mob"]=True; _data["world_boss"]=True
    _data["v018_legendary_event_boss"]=True; _data["v018_biome"]=_kind
    _catalog_mut.catalog_assign(_data, 'MOB_TEMPLATES', MOB_TEMPLATES, (_tid,)); V018_TITAN_TEMPLATES[_kind]=_tid


# ------------------------------------------------------------
# Endless Frontier: infinite mapping with bounded combat scaling.
# ------------------------------------------------------------
V018_ENDLESS_GATE="v018_endless_gate"
V018_ENDLESS_ZONE="Rubież Końca"


def v0180_endless_room_id(depth):
    return f"v018_endless_{max(1,int(depth)):08d}"


def v0180_endless_identity(room_id):
    m=re.fullmatch(r"v018_endless_(\d{8})",str(room_id or ""))
    if not m: return None
    depth=int(m.group(1))
    return depth if depth>=1 else None


def v0180_endless_band(depth):
    return min(V018_ENDLESS_POWER_CAP_BAND, 1 + (max(1,int(depth))-1)//25)


def v0180_endless_template(depth):
    band=v0180_endless_band(depth)
    tid=f"v018_endless_echo_b{band:02d}"
    if tid in MOB_TEMPLATES: return tid
    base_pool=[t for t in V013_FRONTIER_SPECS["crown"].get("mobs",()) if t in MOB_TEMPLATES]
    base_id=base_pool[(band-1)%len(base_pool)] if base_pool else "crown_sentinel"
    base=MOB_TEMPLATES[base_id]
    data=dict(base); data["drops"]=dict(base.get("drops",{}))
    mult=1.0 + min(3.0,(band-1)*0.075)
    data["name"]=f"Echo Rubieży Końca {band}: {base['name']}"
    data["max_hp"]=max(1,int(int(base.get("max_hp",1))*mult))
    data["damage"]=max(1,int(int(base.get("damage",1))*(1.0+min(1.5,(band-1)*0.04))))
    data["soul_reward"]=max(1,int(int(base.get("soul_reward",1))*(1.0+min(2.0,(band-1)*0.06))))
    data["auto_aggro"]=False; data["v018_endless"]=True; data["v018_endless_band"]=band
    _catalog_mut.catalog_assign(data, 'MOB_TEMPLATES', MOB_TEMPLATES, (tid,))
    return tid


def v0180_create_endless_room_definition(room_id):
    depth=v0180_endless_identity(room_id)
    if depth is None: return None,()
    if room_id in ROOMS: return room_id,()
    seed=_v0140_hash_int("v018-endless",depth)
    rng=random.Random(seed)
    names=("Galeria Końca","Pusty Horyzont","Kamienny Bezmiar","Taras Echa","Droga Poza Koroną","Milcząca Rubież")
    exits={"north":v0180_endless_room_id(depth+1)}
    exits["south"]=V018_ENDLESS_GATE if depth==1 else v0180_endless_room_id(depth-1)
    _catalog_mut.catalog_assign({
        "zone":V018_ENDLESS_ZONE,"name":f"{rng.choice(names)} — sektor {depth}",
        "desc":(
            "Pierwsza warstwa endless endgame. Mapa nie ma sztywnego końca i powstaje przy wejściu, "
            "ale siła przeciwników ma twardy bezpieczny cap, aby progresja 1-600 nie została unieważniona. "
            "Brak pułapek i automatycznego aggro."
        ),
        "exits":exits,"recommended_mastery":400,"generated_on_demand":True,
        "v018_endless":True,"v018_endless_depth":depth,"v018_endless_band":v0180_endless_band(depth),
    }, 'ROOMS', ROOMS, (room_id,))
    # v0.25.1: Endless nie jest miejscem Górnictwa.
    spawns=[(room_id,v0180_endless_template(depth))]
    if rng.random()<0.35: spawns.append((room_id,v0180_endless_template(depth)))
    return room_id,tuple(spawns)


# Static gate branches from the Crown procedural gateway without replacing its old exits.
if v0130_gateway_id("crown") in ROOMS:
    _gw=v0130_gateway_id("crown")
    if "north" not in _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (_gw,), "exits",{}):
        _catalog_mut.catalog_assign(V018_ENDLESS_GATE, 'ROOMS', ROOMS, (_gw, "exits", "north"))
    _catalog_mut.catalog_assign({
        "zone":V018_ENDLESS_ZONE,"name":"Brama Rubieży Końca",
        "desc":"Stała brama do pierwszej nieskończonej warstwy endgame. Dalej sektory są generowane na żądanie i nigdy nie auto-aggro.",
        "exits":{"south":_gw,"north":v0180_endless_room_id(1)},"safe_hub":True,
    }, 'ROOMS', ROOMS, (V018_ENDLESS_GATE,))
    GUIDE_DESTINATION_ALIASES["rubiez konca"]=V018_ENDLESS_GATE
    GUIDE_DESTINATION_ALIASES["rubież końca"]=V018_ENDLESS_GATE

# The new fixed Endless gate is part of the static exploration catalog.
v0130_refresh_exploration_catalog()

# Transport network: only discovered destinations are usable.
V018_TRANSPORT_HUBS = {
    "miasto":"market", "port":"harbor", "swiatynia":"temple",
    "kartografowie":"v016_cartographers_square", "wody":"v016_waters_square",
    "gornicy":"v016_miners_square", "zielony":"v016_green_square", "straz":"v016_watch_square",
    "koniec":V018_ENDLESS_GATE,
}
V018_TRANSPORT_ORIGINS = frozenset(V018_TRANSPORT_HUBS.values())


HELP_TOPICS["sezony_v018"]=[
    "sezon / season pokazuje aktualny sezon. Pełny cykl ma Wiosnę, Lato, Jesień i Zimę; każdy sezon trwa 6 godzin.",
    "Sezony dają tylko małe bonusy ekologiczne. Nigdy nie blokują questów, profesji, ryb, ziół ani dostępu do regionów.",
]
HELP_TOPICS["ekspedycje_v018"]=[
    "ekspedycje / expeditions pokazuje 5 archipelagów. ekspedycja <nazwa> wypływa z Portu Dusz lub Przystani Bractwa Wód.",
    "Każdy archipelag ma 16 proceduralnych sektorów 4x4, własną trudność i zasoby. Powrót jest zawsze dostępny z pierwszego sektora.",
]
HELP_TOPICS["ruiny_v018"]=[
    "wielkieruiny / greatruins pokazuje liczbę wielkich proceduralnych ruin. Każda ma 20-40 pokoi, pętle, alternatywne przejścia i finałowego pasywnego strażnika.",
    "Wielkie ruiny nie mają pułapek ani automatycznych obrażeń wejściowych.",
]
HELP_TOPICS["legend_event_v018"]=[
    "legendarnewydarzenia / legendaryevents pokazuje 2 duże wydarzenia świata rotujące co 4 godziny.",
    "Wydarzenia profesyjne dają mały bonus tylko właściwej profesji; Przebudzenie Tytana dodaje pasywnego world bossa.",
]
HELP_TOPICS["endless_v018"]=[
    "rubiezkonca / endless pokazuje informacje o Rubieży Końca. Mapa generuje sektory bez sztywnego końca.",
    "Skalowanie przeciwników jest ograniczone twardym capem, więc system 1-600 pozostaje ważny. PASSIVE WORLD obowiązuje wszędzie.",
]
HELP_TOPIC_ALIASES.update({
    "sezony":"sezony_v018","sezon":"sezony_v018","seasons":"sezony_v018",
    "ekspedycje":"ekspedycje_v018","expeditions":"ekspedycje_v018",
    "wielkie ruiny":"ruiny_v018","great ruins":"ruiny_v018",
    "legendarne wydarzenia":"legend_event_v018","legendary events":"legend_event_v018",
    "rubiez konca":"endless_v018","rubież końca":"endless_v018","endless":"endless_v018",
})
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.

HELP_TOPICS["generator_v019"]=[
    "v0.19.0 używa jednego Global Progression & Reward Generator dla całej gry.",
    "Początek pozostaje w setkach EXP, a później nagrody rosną do tysięcy, milionów, miliardów i bilionów.",
    "Wymagany EXP rośnie mocniej co kolejne progi; duża nagroda nie jest ukrycie obcinana procentowym capem.",
    "Krypta około piętra 20 celuje w około 10000 Class XP za zwykłego moba i około 250000 za bossa, zanim zadziałają dodatnie bonusy.",
    "Generator obejmuje staty, Biegłość, Soul Level, Skill Level, profesje, narzędzia, nagrody mobów/questów, trudność HP/damage oraz główne koszty ekonomii.",
    "Nowa postać nadal zaczyna dokładnie z 2 złota i 30 srebra; wielkie wartości ekonomii pojawiają się dopiero wraz z postępem.",
]
HELP_TOPIC_ALIASES.update({"generator":"generator_v019","balans 019":"generator_v019","progression generator":"generator_v019"})


# ============================================================
# v0.20.0 - ENDGAME CHALLENGES & MEGADUNGEONS
# Megalochy 100-300 pokoi, boss gauntlets, mythic world bosses,
# trwały rozwój artefaktów i długoterminowe cele. NO TRAPS.
# Całość korzysta z Global Progression & Reward Generator v0.19.
# ============================================================
V020_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0200-endgame-challenges-megadungeons"
V020_MYTHIC_WORLD_BOSS_SECONDS = 6 * 60 * 60
V020_MEGA_BOSS_STEP = 25

V020_MEGADUNGEONS = {
    "echo": {"name":"Katedra Tysiąca Ech", "faction":"cartographers", "biome":"crown", "size":120, "stage":220},
    "abyss": {"name":"Archiwum Otchłani", "faction":"waters", "biome":"ocean", "size":160, "stage":260},
    "forge": {"name":"Kuźnia Pierwszych Tytanów", "faction":"miners", "biome":"mountain", "size":200, "stage":300},
    "verdant": {"name":"Labirynt Wiecznych Korzeni", "faction":"green_path", "biome":"forest", "size":240, "stage":340},
    "null": {"name":"Pałac Bezimiennej Korony", "faction":"frontier_watch", "biome":"void", "size":280, "stage":380},
}

V020_MEGADUNGEON_HOST_ROOMS = {
    "echo":"v016_cartographers_archive",
    "abyss":"v016_waters_hall",
    "forge":"v016_miners_hall",
    "verdant":"v016_green_hall",
    "null":"v016_watch_hall",
}

V020_ENDGAME_MATERIALS = {
    "v020_ancient_core": ("Rdzeń Megalochu", "Skondensowany rdzeń zdobywany z bossów megalochów."),
    "v020_gauntlet_seal": ("Pieczęć Próby", "Pieczęć zdobywana za finałowe rundy boss gauntletów."),
    "v020_mythic_essence": ("Esencja Mitycznego Bossa", "Esencja pozostawiana przez mityczne world bossy."),
}
for _iid, (_name, _desc) in V020_ENDGAME_MATERIALS.items():
    _catalog_mut.catalog_assign({"name":_name, "type":"material", "price":None, "rarity":"mythic", "rarity_name":"Mityczny", "desc":_desc}, 'ITEMS', ITEMS, (_iid,))
    UNIQUE_ITEM_COLLECTION_CATALOG.setdefault(_iid, _name)


def v0200_mega_gate_id(key):
    return f"v020_mega_{key}_gate"


def v0200_mega_room_id(key, index):
    return f"v020_mega_{key}_{int(index)}"


def v0200_mega_identity(room_id):
    m = re.fullmatch(r"v020_mega_([a-z]+)_(\d+)", str(room_id or ""))
    if not m or m.group(1) not in V020_MEGADUNGEONS:
        return None
    index=int(m.group(2)); size=int(V020_MEGADUNGEONS[m.group(1)]["size"])
    if not 1 <= index <= size:
        return None
    return m.group(1), index


def v0200_mega_stage(key, index):
    spec=V020_MEGADUNGEONS[key]; size=max(2,int(spec["size"])); base=int(spec["stage"])
    # W obrębie jednego megalochu trudność powoli rośnie, ale zawsze pozostaje
    # w zakresie generatora 1-600.
    return max(1,min(CHARACTER_MAX_LEVEL,int(round(base + (CHARACTER_MAX_LEVEL-base)*((index-1)/(size-1))*0.72))))


def v0200_mega_is_boss_index(key, index):
    size=int(V020_MEGADUNGEONS[key]["size"])
    return index == size or (index % V020_MEGA_BOSS_STEP == 0)


def v0200_mega_neighbors(key, index):
    size=int(V020_MEGADUNGEONS[key]["size"]); exits={}
    if index == 1:
        exits["up"] = v0200_mega_gate_id(key)
    else:
        exits["south"] = v0200_mega_room_id(key,index-1)
    if index < size:
        exits["north"] = v0200_mega_room_id(key,index+1)
    # Deterministyczne skróty tworzą prawdziwe pętle, ale nie omijają boss gate'u
    # na końcu sekcji 25-pokojowej.
    if index % 13 == 1 and index+8 <= size and (index//25)==((index+8)//25):
        exits["east"] = v0200_mega_room_id(key,index+8)
    if index > 8 and (index-8) % 13 == 1 and ((index-8)//25)==(index//25):
        exits["west"] = v0200_mega_room_id(key,index-8)
    return exits


def v0200_mega_template(key, index, boss=False):
    stage=v0200_mega_stage(key,index); spec=V020_MEGADUNGEONS[key]; biome=spec["biome"]
    tid=f"v020_mega_{key}_{'boss' if boss else 'mob'}_{index if boss else stage}"
    if tid in MOB_TEMPLATES:
        return tid
    if boss:
        mechanic, mechanic_text = V017_BIOME_BOSS_MECHANICS.get(biome,("two_hundred_lord","Wielofazowy profil bossa."))
        pool=list((globals().get("V021_MYTHIC_SET_ITEMS",{}).get(key) or V017_BIOME_SET_ITEMS.get(biome,())))
        _catalog_mut.catalog_assign({
            "name":f"Strażnik {spec['name']} — próg {index}",
            "max_hp":1,"damage":1,"damage_type":"magic" if biome in ("void","crown","ocean") else "physical",
            "silver":0,"gold":0,"mithril":0,"stat_reward":1,"soul_reward":1,"class_xp_reward":1,
            "drops":{"v020_ancient_core":1.0,"v021_ascension_crystal":0.45,"soul_elixir":0.55},
            "auto_aggro":False,"stationary_mob":True,"boss_mechanic":mechanic,
            "boss_mechanic_text":mechanic_text+" Fazy 75/50/25%. PASSIVE WORLD.",
            "v017_boss_phases":True,"v020_megadungeon_boss":True,"v020_mega_key":key,"v020_mega_index":index,
            "v019_stage":stage,"corpse_equipment_pool":pool,"corpse_equipment_guaranteed":min(2 if index==int(spec["size"]) else 1,len(pool)),
            "respawn_seconds":6*60*60,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (tid,))
        BOSS_COLLECTION_CATALOG[tid]=MOB_TEMPLATES[tid]["name"]
    else:
        names=("Strażnik Korytarza","Wędrowiec Głębi","Opiekun Pieczęci","Echo Dawnej Straży","Bestia Megalochu")
        rng=random.Random(_v0140_hash_int(V020_WORLD_SEED,key,stage))
        _catalog_mut.catalog_assign({
            "name":f"{rng.choice(names)} — {spec['name']}","max_hp":1,"damage":1,
            "damage_type":"magic" if rng.random()<0.38 else "physical",
            "silver":0,"gold":0,"mithril":0,"stat_reward":1,"soul_reward":1,"class_xp_reward":1,
            "drops":{"soul_shard":0.10},"auto_aggro":False,"v020_megadungeon":True,"v020_mega_key":key,"v019_stage":stage,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (tid,))
    v0190_apply_combat_template(MOB_TEMPLATES[tid])
    return tid


def v0200_create_mega_room_definition(room_id):
    ident=v0200_mega_identity(room_id)
    if not ident: return None,()
    if room_id in ROOMS: return room_id,()
    key,index=ident; spec=V020_MEGADUNGEONS[key]; stage=v0200_mega_stage(key,index)
    rng=random.Random(_v0140_hash_int(V020_WORLD_SEED,key,index))
    labels=("Galeria","Komnata","Korytarz","Sanktuarium","Sala","Krużganek","Archiwum","Przejście")
    _catalog_mut.catalog_assign({
        "zone":spec["name"],"name":f"{rng.choice(labels)} — {index} z {spec['size']}",
        "desc":(
            f"Część megalochu {spec['name']}. Kompleks ma {spec['size']} pokoi i jest generowany na żądanie. "
            "Ma pętle i alternatywne drogi, ale boss progu blokuje wyłącznie przejście do następnej sekcji. "
            "Brak pułapek i auto-aggro."
        ),
        "exits":v0200_mega_neighbors(key,index),"recommended_mastery":stage,"generated_on_demand":True,
        "v020_megadungeon":key,"v020_mega_index":index,
    }, 'ROOMS', ROOMS, (room_id,))
    spawns=[]
    if v0200_mega_is_boss_index(key,index):
        spawns.append((room_id,v0200_mega_template(key,index,boss=True)))
    else:
        count=1 + (1 if rng.random()<0.52 else 0) + (1 if stage>=330 and rng.random()<0.30 else 0)
        for _ in range(count): spawns.append((room_id,v0200_mega_template(key,index,boss=False)))
    return room_id,tuple(spawns)


# Stałe bramy megalochów. Same wnętrza są lazy-generated.
for _key,_spec in V020_MEGADUNGEONS.items():
    _host=V020_MEGADUNGEON_HOST_ROOMS[_key]; _gate=v0200_mega_gate_id(_key)
    _catalog_mut.catalog_assign({"zone":_spec["name"],"name":f"Brama: {_spec['name']}",
        "desc":f"Stałe wejście do megalochu {_spec['name']} ({_spec['size']} pokoi). Wnętrze generuje się dopiero przy wejściu.",
        "exits":{"up":_host,"down":v0200_mega_room_id(_key,1)},"safe_hub":True,"v020_mega_gate":_key}, 'ROOMS', ROOMS, (_gate,))
    if _host in ROOMS and "down" not in _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (_host,), "exits",{}): _catalog_mut.catalog_assign(_gate, 'ROOMS', ROOMS, (_host, "exits", "down"))
    GUIDE_DESTINATION_ALIASES[normalize_lookup_text(_spec["name"])]=_gate


# -------------------- BOSS GAUNTLETS --------------------
V020_GAUNTLETS={
    "stalowa":{"name":"Stalowa Próba","stages":(140,160,180,200,220)},
    "mityczna":{"name":"Mityczna Próba","stages":(240,260,280,300,320)},
    "astralna":{"name":"Astralna Próba","stages":(300,325,350,375,400)},
    "wieczna":{"name":"Wieczna Próba","stages":(360,370,380,390,400)},
}
V020_GAUNTLET_LOBBY="v020_gauntlet_lobby"
_catalog_mut.catalog_assign({"zone":"Arena Prób","name":"Sala Boss Gauntletów","desc":"Bezpieczny hol czterech wieloetapowych prób bossów. Żaden boss nie atakuje pierwszy.","exits":{"west":"v016_watch_hall","north":"v020_gauntlet_stalowa_1","east":"v020_gauntlet_mityczna_1","up":"v020_gauntlet_astralna_1","down":"v020_gauntlet_wieczna_1"},"safe_hub":True}, 'ROOMS', ROOMS, (V020_GAUNTLET_LOBBY,))
if "v016_watch_hall" in ROOMS and "east" not in _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, ("v016_watch_hall",), "exits",{}): _catalog_mut.catalog_assign(V020_GAUNTLET_LOBBY, 'ROOMS', ROOMS, ("v016_watch_hall", "exits", "east"))

for _gkey,_gdata in V020_GAUNTLETS.items():
    for _round,_stage in enumerate(_gdata["stages"],1):
        _rid=f"v020_gauntlet_{_gkey}_{_round}"
        _prev=V020_GAUNTLET_LOBBY if _round==1 else f"v020_gauntlet_{_gkey}_{_round-1}"
        _next=V020_GAUNTLET_LOBBY if _round==5 else f"v020_gauntlet_{_gkey}_{_round+1}"
        _catalog_mut.catalog_assign({"zone":_gdata["name"],"name":f"{_gdata['name']} — runda {_round}/5",
            "desc":"Arena pojedynczego bossa. Wyjście naprzód otwiera się po pokonaniu aktywnego bossa. PASSIVE WORLD; brak pułapek.",
            "exits":{"south":_prev,"north":_next},"recommended_mastery":_stage,"v020_gauntlet":_gkey,"v020_gauntlet_round":_round}, 'ROOMS', ROOMS, (_rid,))
        _tid=f"v020_gauntlet_boss_{_gkey}_{_round}"
        _mechanic=list(V017_BIOME_BOSS_MECHANICS.values())[(_round+list(V020_GAUNTLETS).index(_gkey)*3)%len(V017_BIOME_BOSS_MECHANICS)][0]
        _catalog_mut.catalog_assign({"name":f"{_gdata['name']} — Boss Rundy {_round}","max_hp":1,"damage":1,"damage_type":"physical" if _round%2 else "magic",
            "silver":0,"gold":0,"mithril":0,"stat_reward":1,"soul_reward":1,"class_xp_reward":1,"drops":({"v020_gauntlet_seal":1.0} if _round==5 else {"soul_elixir":0.25}),
            "auto_aggro":False,"stationary_mob":True,"boss_mechanic":_mechanic,"v017_boss_phases":True,
            "v020_gauntlet":_gkey,"v020_gauntlet_round":_round,"v019_stage":_stage,"respawn_seconds":6*60*60}, 'MOB_TEMPLATES', MOB_TEMPLATES, (_tid,))
        v0190_apply_combat_template(MOB_TEMPLATES[_tid]); BOSS_COLLECTION_CATALOG[_tid]=MOB_TEMPLATES[_tid]["name"]
        MOB_SPAWNS.append((_rid,_tid))


# -------------------- MYTHIC WORLD BOSSES --------------------
def v0200_mythic_template(kind):
    tid=f"v020_mythic_worldboss_{kind}"
    if tid in MOB_TEMPLATES: return tid
    spec=V013_FRONTIER_SPECS[kind]; biome=kind
    stage=max(250,min(CHARACTER_MAX_LEVEL,int(spec.get("base_mastery",1))+140))
    mechanic, text=V017_BIOME_BOSS_MECHANICS.get(kind,("two_hundred_lord","Wielofazowa mechanika."))
    pool=list(V017_BIOME_SET_ITEMS.get(kind,()))
    _catalog_mut.catalog_assign({"name":f"Mityczny Władca — {spec['zone']}","max_hp":1,"damage":1,"damage_type":"magic" if kind in ("void","sky","crown","ocean") else "physical",
        "silver":0,"gold":0,"mithril":0,"stat_reward":1,"soul_reward":1,"class_xp_reward":1,
        "drops":{"v020_mythic_essence":1.0,"v020_ancient_core":0.65,"soul_elixir":0.80},"world_boss":True,"v020_mythic_world_boss":True,"v020_biome":kind,
        "auto_aggro":False,"stationary_mob":True,"boss_mechanic":mechanic,"boss_mechanic_text":text+" Mityczny world boss; fazy 75/50/25%. PASSIVE WORLD.",
        "v017_boss_phases":True,"v019_stage":stage,"corpse_equipment_pool":pool,"corpse_equipment_guaranteed":min(4,len(pool))}, 'MOB_TEMPLATES', MOB_TEMPLATES, (tid,))
    v0190_apply_combat_template(MOB_TEMPLATES[tid]); BOSS_COLLECTION_CATALOG[tid]=MOB_TEMPLATES[tid]["name"]
    return tid

for _kind in tuple(V013_FRONTIER_SPECS): v0200_mythic_template(_kind)

def v0200_active_mythic_world_bosses(now=None):
    now=time.time() if now is None else float(now); slot=int(now//V020_MYTHIC_WORLD_BOSS_SECONDS)
    rng=random.Random(_v0140_hash_int(V020_WORLD_SEED,"mythic-world",slot)); kinds=list(V013_FRONTIER_SPECS); rng.shuffle(kinds)
    out=[]
    for kind in kinds[:2]:
        x=rng.randrange(V013_FRONTIER_SIDE); y=rng.randrange(V013_FRONTIER_SIDE)
        out.append({"kind":kind,"x":x,"y":y,"room_id":v0130_frontier_room_id(kind,x,y),"template_id":v0200_mythic_template(kind),
            "token":f"{slot}:v020mythic:{kind}:{x}:{y}","expires_at":(slot+1)*V020_MYTHIC_WORLD_BOSS_SECONDS})
    return tuple(out)

def v0200_mythic_encounters_for_room(room_id,now=None):
    return tuple(e for e in v0200_active_mythic_world_bosses(now) if e["room_id"]==room_id)


# -------------------- ARTIFACT PROGRESSION --------------------
V020_ARTIFACT_MAX_TIER=10
V020_ARTIFACT_UPGRADE_COSTS={
    2:{"v020_ancient_core":3,"coins":v0190_economy_sink(250,"equipment")},
    3:{"v020_gauntlet_seal":3,"v020_ancient_core":5,"coins":v0190_economy_sink(300,"equipment")},
    4:{"v020_mythic_essence":4,"v020_gauntlet_seal":5,"coins":v0190_economy_sink(350,"equipment")},
    5:{"v020_mythic_essence":10,"v020_ancient_core":12,"v020_gauntlet_seal":8,"coins":v0190_economy_sink(400,"equipment")},
    6:{"v020_mythic_essence":20,"v020_ancient_core":18,"v020_gauntlet_seal":12,"v021_ascension_crystal":5,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*2)},
    7:{"v020_mythic_essence":35,"v020_ancient_core":28,"v020_gauntlet_seal":20,"v021_ascension_crystal":10,"v021_world_tier_crest":3,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*4)},
    8:{"v020_mythic_essence":50,"v020_ancient_core":42,"v020_gauntlet_seal":30,"v021_ascension_crystal":20,"v021_world_tier_crest":8,"v021_eternal_sigil":2,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*8)},
    9:{"v020_mythic_essence":80,"v020_ancient_core":65,"v020_gauntlet_seal":45,"v021_ascension_crystal":35,"v021_world_tier_crest":15,"v021_eternal_sigil":5,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*16)},
    10:{"v020_mythic_essence":120,"v020_ancient_core":100,"v020_gauntlet_seal":70,"v021_ascension_crystal":60,"v021_world_tier_crest":30,"v021_eternal_sigil":10,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*32)},
}
V020_ARTIFACT_VARIANTS={}
for _fid,_data in V017_ARTIFACTS.items():
    _base=_data["item_id"]; V020_ARTIFACT_VARIANTS[_fid]=[_base]
    _base_item=ITEMS[_base]
    for _tier in range(2,V020_ARTIFACT_MAX_TIER+1):
        _iid=f"{_base}_t{_tier}"; _scale=1.0+0.35*(_tier-1)
        _hp=1.0+(float(_data["hp"])-1.0)*_scale; _dmg=1.0+(float(_data["damage"])-1.0)*_scale; _def=1.0+(float(_data["defense"])-1.0)*_scale
        _catalog_mut.catalog_assign(dict(_base_item), 'ITEMS', ITEMS, (_iid,)); _catalog_mut.catalog_update_path('ITEMS', ITEMS, (_iid,), {"name":f"{_data['name']} +{_tier-1}","rarity":"mythic" if _tier>=4 else "legendary","rarity_name":"Artefakt Rozwinięty",
            "defense":int(round(int(_data["defense_flat"])*_scale)),"artifact_hp_multiplier":_hp,"artifact_damage_multiplier":_dmg,"artifact_defense_multiplier":_def,
            "v020_artifact_tier":_tier,"v020_artifact_base":_base,
            "desc":f"Rozwinięcie artefaktu {_data['name']}, poziom {_tier}/{V020_ARTIFACT_MAX_TIER}. Brak losowego faila."})
        UNIQUE_ITEM_COLLECTION_CATALOG[_iid]=ITEMS[_iid]["name"]; EQUIPMENT_COLLECTION_CATALOG[_iid]=ITEMS[_iid]["name"]
        V020_ARTIFACT_VARIANTS[_fid].append(_iid)


def v0200_artifact_owned_tier(db,account_id,faction_id):
    variants=V020_ARTIFACT_VARIANTS[faction_id]
    for tier in range(len(variants),0,-1):
        if db.item_qty(account_id,variants[tier-1])>0: return tier,variants[tier-1]
    return 0,None


# -------------------- LONG-TERM ENDGAME GOALS --------------------
V020_ENDGAME_GOALS=(
    ("mega_bosses",25,"Pokonaj 25 bossów megalochów"),
    ("gauntlet_finals",20,"Ukończ 20 finałów boss gauntletów"),
    ("mythic_world",15,"Pokonaj 15 mitycznych world bossów"),
    ("artifact_t5",5,"Zdobądź pięć artefaktów poziomu 5"),
)

v0130_refresh_exploration_catalog()

HELP_TOPICS["megalochy_v020"]=[
    "megalochy / megadungeons pokazuje pięć megalochów po 120, 160, 200, 240 i 280 pokoi.",
    "Wnętrza generują się na żądanie. Boss co 25 pokoi blokuje tylko przejście do następnej sekcji i tylko do pierwszego trwałego zaliczenia.",
    "Megalochy nie mają pułapek ani auto-aggro i używają generatora balansu v0.19.",
]
HELP_TOPICS["gauntlety_v020"]=[
    "gauntlety / gauntlets pokazuje cztery pięciorundowe próby bossów. gauntlet <nazwa> rozpoczyna próbę z Sali Boss Gauntletów.",
    "Każdy boss jest pasywny. Aktywny boss blokuje tylko wyjście do następnej rundy.",
]
HELP_TOPICS["mythicboss_v020"]=[
    "mitycznebossy / mythicbosses pokazuje dwa aktywne mityczne world bossy rotujące co 6 godzin.",
    "Są silniejsze od zwykłych world bossów, dają Esencję Mitycznego Bossa i nadal nie atakują pierwsi.",
]
HELP_TOPICS["artifactupgrade_v020"]=[
    "ulepszartefakt / artifactupgrade pokazuje lub wykonuje trwałe rozwinięcie artefaktu do poziomu 10.",
    "Poziomy 2-5 używają materiałów v0.20, a 6-10 także Kryształów Wzniesienia, Herbów World Tieru i Wiecznych Sigili. Nie ma szansy niepowodzenia ani niszczenia przedmiotu.",
]
HELP_TOPICS["endgamegoals_v020"]=["celekonca / endgamegoals pokazuje długoterminowe cele endgame i ich postęp."]
HELP_TOPIC_ALIASES.update({"megalochy":"megalochy_v020","megadungeons":"megalochy_v020","gauntlety":"gauntlety_v020","gauntlets":"gauntlety_v020",
    "mityczne bossy":"mythicboss_v020","mythic bosses":"mythicboss_v020","ulepsz artefakt":"artifactupgrade_v020","artifact upgrade":"artifactupgrade_v020",
    "cele konca":"endgamegoals_v020","endgame goals":"endgamegoals_v020"})
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.


# ============================================================
# v0.21.0 - ASCENSION, WORLD TIERS & MYTHIC PROGRESSION
# Post-400 progression without resets, optional personal World Tiers 1-10,
# artifact Tier 6-10, five 8-piece mythic sets and an endless boss gauntlet.
# PASSIVE WORLD stays global. No traps, entry damage or auto damage.
# ============================================================

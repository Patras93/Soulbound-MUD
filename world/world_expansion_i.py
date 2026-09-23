# -*- coding: utf-8 -*-
"""Soulbound v0.51.0 - World Expansion I.

Adds four permanent settlements, a looped road network, eight alternative
open-world hunting regions, local quest givers and region-specific enemies.
The module uses the v0.48 catalog mutation API so every world change remains
traceable and maintainable.
"""
from __future__ import annotations

from data.catalogs import ROOMS, NPCS, QUESTS, MOB_TEMPLATES
from data.catalog_mutations import catalog_assign, catalog_set_path
from systems.content_registry import MOB_SPAWNS
from world.generation_systems import v0130_refresh_exploration_catalog

WORLD_EXPANSION_I_VERSION = "0.51.0"

WORLD_EXPANSION_I_SETTLEMENTS = {
    "Brzozowy Trakt": "birch_square",
    "Żelazne Bramy": "iron_square",
    "Port Mglistych Wysp": "fog_square",
    "Twierdza Popiołu": "ash_square",
}

WORLD_EXPANSION_I_HUNTING_ZONES = {
    "Wilcze Wzgórza": {"stage": 35, "hub": "wolf_hills_01", "boss": "wolf_hills_den"},
    "Kamienne Jary": {"stage": 70, "hub": "stone_gullies_01", "boss": "stone_gullies_depth"},
    "Rdzawa Dolina": {"stage": 115, "hub": "rust_valley_01", "boss": "rust_valley_core"},
    "Stare Huty": {"stage": 170, "hub": "old_smelteries_01", "boss": "old_smelteries_furnace"},
    "Mglisty Archipelag": {"stage": 225, "hub": "mist_archipelago_01", "boss": "mist_archipelago_shrine"},
    "Zatopione Klify": {"stage": 290, "hub": "sunken_cliffs_01", "boss": "sunken_cliffs_abyss"},
    "Popielne Pustkowia": {"stage": 370, "hub": "ash_wastes_01", "boss": "ash_wastes_crater"},
    "Dolina Tytanów": {"stage": 480, "hub": "titan_valley_01", "boss": "titan_valley_throne"},
}

_NEW_ROOMS = []
_NEW_MOBS = []
_NEW_NPCS = []
_NEW_QUESTS = []
_NEW_SPAWNS = []

_OPPOSITE = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "up": "down", "down": "up",
}


def _room(room_id, zone, name, desc, exits=None):
    payload = {
        "zone": zone,
        "name": name,
        "desc": desc,
        "exits": dict(exits or {}),
    }
    catalog_assign(payload, "ROOMS", ROOMS, (room_id,))
    _NEW_ROOMS.append(room_id)
    return room_id


def _link(a, direction, b, *, reverse=True):
    catalog_set_path("ROOMS", ROOMS, (a, "exits", direction), b)
    if reverse:
        catalog_set_path("ROOMS", ROOMS, (b, "exits", _OPPOSITE[direction]), a)


def _chain(prefix, zone, names, desc_prefix):
    ids = []
    for idx, name in enumerate(names, 1):
        rid = f"{prefix}_{idx:02d}"
        _room(
            rid, zone, name,
            f"{desc_prefix} Odcinek {idx} szlaku zachowuje własny charakter i daje podróżnym czytelny punkt orientacyjny.",
        )
        ids.append(rid)
        if len(ids) > 1:
            _link(ids[-2], "north", ids[-1])
    return ids


def _grid_zone(prefix, zone, names, descriptions):
    """Create a compact 2x4 hunting loop. Returns ordered room ids."""
    ids = []
    for idx in range(8):
        rid = f"{prefix}_{idx + 1:02d}"
        _room(rid, zone, names[idx], descriptions[idx])
        ids.append(rid)
    # two parallel lanes, with three cross links; no dead-end corridor.
    _link(ids[0], "east", ids[1]); _link(ids[1], "east", ids[2]); _link(ids[2], "east", ids[3])
    _link(ids[4], "east", ids[5]); _link(ids[5], "east", ids[6]); _link(ids[6], "east", ids[7])
    _link(ids[0], "south", ids[4]); _link(ids[2], "south", ids[6]); _link(ids[3], "south", ids[7])
    _link(ids[5], "north", ids[1])
    return ids


def _mob(mob_id, name, stage, target, *, magic=False, boss=False, drops=None):
    stage = int(stage)
    hp = 110 + stage * (18 if boss else 9)
    damage = 10 + stage // (3 if boss else 5)
    payload = {
        "name": name,
        "max_hp": hp,
        "damage": damage,
        "damage_type": "magic" if magic else "physical",
        "silver": 40 + stage * (7 if boss else 2),
        "gold": 0,
        "mithril": 0,
        "stat_reward": max(25, stage // 2),
        "class_xp_reward": max(150, stage * (28 if boss else 9)),
        "soul_reward": max(120, stage * (10 if boss else 4)),
        "drops": dict(drops or {}),
        "quest_target": mob_id if boss else target,
        "generator_level": stage,
        "v0510_world_expansion": True,
        "v0510_region_target": target,
    }
    if boss:
        payload.update({
            "rank": "boss",
            "boss": True,
            "quest_targets": (target, mob_id),
            "corpse_equipment_guaranteed": 1,
        })
    catalog_assign(payload, "MOB_TEMPLATES", MOB_TEMPLATES, (mob_id,))
    _NEW_MOBS.append(mob_id)
    return mob_id


def _spawn(room_id, mob_id, count=1):
    for _ in range(max(1, int(count))):
        row = (room_id, mob_id)
        if row not in MOB_SPAWNS:
            MOB_SPAWNS.append(row)
            _NEW_SPAWNS.append(row)


def _npc(npc_id, name, room, dialogue, quest_ids):
    payload = {
        "name": name,
        "room": room,
        "dialogue": dialogue,
        "quest": quest_ids[0] if quest_ids else None,
        "quest_chain": tuple(quest_ids[1:]),
        "v0510_world_expansion": True,
    }
    catalog_assign(payload, "NPCS", NPCS, (npc_id,))
    _NEW_NPCS.append(npc_id)


def _quest(qid, name, giver, target, needed, description, silver, *, repeatable=True, cooldown=3600, boss=False):
    payload = {
        "name": name,
        "giver": giver,
        "kind": "kill",
        "target": target,
        "needed": int(needed),
        "description": description,
        "reward_silver": int(silver),
        "reward_gold": max(0, int(silver) // 5000),
        "reward_mithril": 0,
        "reward_items": {"soul_shard": 1} if boss else {"healing_potion": 1},
        "v0510_world_expansion": True,
    }
    if repeatable:
        payload.update({"repeatable": True, "repeat_cooldown": int(cooldown)})
    catalog_assign(payload, "QUESTS", QUESTS, (qid,))
    _NEW_QUESTS.append(qid)


# ---------------------------------------------------------------------------
# 1. ROAD NETWORK + SETTLEMENTS
# ---------------------------------------------------------------------------

# Southern loop: Crossroads -> Brzozowy Trakt and Meadow -> Brzozowy Trakt.
birch_road = _chain(
    "birch_road", "Szlak Brzozowy",
    ["Stary Słup Milowy", "Aleja Brzóz", "Most nad Strugą", "Łagodny Podjazd", "Przydrożna Kapliczka", "Brama Brzozowego Traktu"],
    "Szeroki szlak prowadzi między brzozami, polami i niskimi kamiennymi murkami.",
)
_link("crossroads", "north", birch_road[0])

willow_path = _chain(
    "willow_path", "Szlak Brzozowy",
    ["Polna Droga", "Wierzbowe Rozstaje", "Młynarski Gościniec", "Południowy Most"],
    "Polna droga łączy łąki z osadami położonymi dalej od Miasta Dusz.",
)
_link("meadow", "south", willow_path[0])

_room("birch_square", "Brzozowy Trakt", "Plac Brzozowego Traktu", "Niewielki plac otaczają drewniane domy, studnia i tablica lokalnych zleceń. To spokojna osada na skrzyżowaniu dwóch ważnych dróg.")
_room("birch_inn", "Brzozowy Trakt", "Karczma Pod Białą Korą", "Ciepła karczma służy drwalom, zwiadowcom i podróżnym przemierzającym południowe trakty.")
_room("birch_market", "Brzozowy Trakt", "Targ Brzozowy", "Mały targ oferuje żywność, skóry, drewno i towary przywożone z Miasta Dusz.")
_room("birch_shrine", "Brzozowy Trakt", "Kapliczka Wędrowców", "Kamienna kapliczka stoi w cieniu starych brzóz. Wędrowcy zostawiają tu drobne symbole szczęśliwego powrotu.")
_room("birch_rangers", "Brzozowy Trakt", "Dom Strażników Traktu", "Lokalni strażnicy prowadzą mapy Wilczych Wzgórz i Kamiennych Jarów.")
_room("birch_mill", "Brzozowy Trakt", "Młyn Nad Strugą", "Koło młyna obraca się leniwie przy płytkim kanale. Wokół stoją wozy z ziarnem i worki mąki.")
_room("birch_north_gate", "Brzozowy Trakt", "Północna Brama Brzozowego Traktu", "Za drewnianą bramą zaczyna się dłuższy trakt ku Żelaznym Bramom.")
_room("birch_east_gate", "Brzozowy Trakt", "Wschodnia Brama Brzozowego Traktu", "Droga za bramą prowadzi ku pagórkom i dzikim terenom łowieckim.")
_link(birch_road[-1], "north", "birch_square")
_link(willow_path[-1], "north", "birch_square")
_link("birch_square", "west", "birch_inn"); _link("birch_square", "east", "birch_market")
_link("birch_square", "south", "birch_shrine"); _link("birch_square", "north", "birch_north_gate")
_link("birch_market", "north", "birch_rangers"); _link("birch_inn", "south", "birch_mill")
_link("birch_market", "east", "birch_east_gate")

# North road to Iron Gates, plus a second approach from the frontier watchpost.
iron_road = _chain(
    "iron_road", "Trakt Żelazny",
    ["Północny Gościniec", "Kamienny Nasyp", "Droga Kupców", "Posterunek Karawan", "Wąwóz Podkowy", "Żelazny Most", "Przedpole Murów", "Brama Południowa Żelaznych Bram"],
    "Utwardzony trakt jest pełen śladów ciężkich wozów przewożących rudę, węgiel i stal.",
)
_link("birch_north_gate", "north", iron_road[0])

merchant_road = _chain(
    "merchant_road", "Trakt Żelazny",
    ["Pograniczny Szlak Kupiecki", "Kamieniołom przy Drodze", "Odpoczynek Woźniców", "Wschodni Most", "Rozjazd pod Murami"],
    "Boczny szlak pozwala karawanom omijać najbardziej zatłoczone odcinki głównego traktu.",
)
_link("frontier_watchpost", "north", merchant_road[0])

_room("iron_square", "Żelazne Bramy", "Plac Żelaznych Bram", "Wielkie miasto przemysłowe otacza plac pełen wozów, kowali i górników. Nad dachami górują masywne żelazne bramy.")
_room("iron_market", "Żelazne Bramy", "Rynek Rudy i Stali", "Kupcy handlują metalem, narzędziami i ciężkim wyposażeniem sprowadzanym z okolicznych dolin.")
_room("iron_inn", "Żelazne Bramy", "Karczma Pod Młotem", "Głośna karczma jest miejscem spotkań hutników, najemników i przewoźników.")
_room("iron_forge", "Żelazne Bramy", "Dzielnica Wielkich Kuźni", "Rzędy pieców i kuźni pracują bez przerwy. Nad ulicą unosi się metaliczny dym.")
_room("iron_miners", "Żelazne Bramy", "Plac Górników", "Tablice zmian i mapy terenów wydobywczych zajmują ściany kilku kamiennych budynków.")
_room("iron_smith_guild", "Żelazne Bramy", "Dom Cechu Kowali", "Mistrzowie kowalstwa oceniają tu jakość metalu i prowadzą szkolenia dla miejscowych rzemieślników.")
_room("iron_reservoir", "Żelazne Bramy", "Zbiornik Przemysłowy", "Kamienny zbiornik zasila kanały chłodzące pobliskie huty i warsztaty.")
_room("iron_east_gate", "Żelazne Bramy", "Wschodnia Brama Żelaznych Bram", "Za murami zaczyna się surowszy trakt prowadzący ku ziemiom pokrytym popiołem.")
_room("iron_south_gate", "Żelazne Bramy", "Południowa Brama Żelaznych Bram", "Główne wejście od strony Brzozowego Traktu jest stale zatłoczone przez karawany.")
_link(iron_road[-1], "north", "iron_south_gate"); _link("iron_south_gate", "north", "iron_square")
_link(merchant_road[-1], "north", "iron_square")
_link("iron_square", "west", "iron_inn"); _link("iron_square", "east", "iron_market")
_link("iron_square", "north", "iron_miners"); _link("iron_market", "east", "iron_forge")
_link("iron_forge", "north", "iron_smith_guild"); _link("iron_miners", "west", "iron_reservoir")
_link("iron_square", "south", "iron_south_gate"); _link("iron_forge", "east", "iron_east_gate")

# Eastern high road to Ash Fortress.
ash_road = _chain(
    "ash_road", "Szlak Popiołu",
    ["Droga Czerwonego Pyłu", "Spalony Drogowskaz", "Przełęcz Hutników", "Czarna Skarpa", "Posterunek Popiołu", "Most nad Szczeliną", "Droga Chorągwi", "Przedpole Twierdzy"],
    "Wiatr niesie drobny popiół, a kamienie przy drodze są coraz ciemniejsze i gorętsze.",
)
_link("iron_east_gate", "east", ash_road[0])

_room("ash_square", "Twierdza Popiołu", "Dziedziniec Twierdzy Popiołu", "Kamienna twierdza stoi na granicy najniebezpieczniejszych ziem. Żołnierze, najemnicy i badacze przygotowują się tu do wypraw na pustkowia.")
_room("ash_barracks", "Twierdza Popiołu", "Koszary Popielnej Straży", "Ciężkie drzwi prowadzą do koszar pełnych broni, tarcz i sprzętu wyprawowego.")
_room("ash_inn", "Twierdza Popiołu", "Gospoda Ostatniego Ognia", "Wędrowcy odpoczywają tu przed wejściem na Popielne Pustkowia i do Doliny Tytanów.")
_room("ash_command", "Twierdza Popiołu", "Sala Dowództwa", "Na ogromnym stole leżą mapy pustkowi, kraterów i śladów pradawnych olbrzymów.")
_room("ash_forge", "Twierdza Popiołu", "Kuźnia Oblężnicza", "Grube płyty metalu i części machin wojennych zajmują większość warsztatu.")
_room("ash_shrine", "Twierdza Popiołu", "Sanktuarium Strażników", "Cicha sala służy wojownikom wracającym z wypraw w najbardziej niebezpieczne tereny.")
_room("ash_upper_wall", "Twierdza Popiołu", "Górny Mur Twierdzy", "Z muru widać rozległe Popielne Pustkowia i odległe sylwetki Doliny Tytanów.")
_room("ash_west_gate", "Twierdza Popiołu", "Zachodnia Brama Twierdzy", "Brama prowadzi z powrotem ku Żelaznym Bramom.")
_room("ash_south_gate", "Twierdza Popiołu", "Południowa Brama Twierdzy", "Droga opada stąd ku klifom i dalekiemu wybrzeżu Mglistych Wysp.")
_link(ash_road[-1], "east", "ash_west_gate"); _link("ash_west_gate", "east", "ash_square")
_link("ash_square", "west", "ash_barracks"); _link("ash_square", "east", "ash_command")
_link("ash_square", "north", "ash_upper_wall"); _link("ash_square", "south", "ash_south_gate")
_link("ash_barracks", "south", "ash_inn"); _link("ash_command", "south", "ash_forge")
_link("ash_command", "north", "ash_shrine")

# Sea route from the old harbor to the Fog Islands, then coastal route to Ash Fortress.
sea_crossing = _chain(
    "fog_crossing", "Szlak Morski",
    ["Prom przy Oceanicznej Platformie", "Otwarte Morze", "Pas Mgły", "Podejście do Wysp"],
    "Prom i małe statki poruszają się po wyznaczonym szlaku między wybrzeżem a Mglistymi Wyspami.",
)
# Reorient generated north/south chain into an east/west voyage while keeping reciprocal exits.
for rid in sea_crossing:
    catalog_assign({}, "ROOMS", ROOMS, (rid, "exits"))
for a, b in zip(sea_crossing, sea_crossing[1:]):
    _link(a, "east", b)
_link("ocean_platform", "east", sea_crossing[0])

_room("fog_square", "Port Mglistych Wysp", "Plac Portowy Mglistych Wysp", "Kamienny port wyrasta z morza między wysokimi klifami. Mgła tłumi dźwięki statków, targu i latarni.")
_room("fog_dock", "Port Mglistych Wysp", "Główny Dok", "Masywne pale i szerokie pomosty przyjmują promy oraz kutry z głównego wybrzeża.")
_room("fog_fish_market", "Port Mglistych Wysp", "Targ Morskich Łowów", "Rybacy sprzedają tu połowy z dalekich łowisk i opowiadają o stworzeniach widzianych w mgle.")
_room("fog_inn", "Port Mglistych Wysp", "Karczma Pod Mglistą Latarnią", "Ciepłe wnętrze chroni przed zimnym wiatrem i wilgocią archipelagu.")
_room("fog_lighthouse", "Port Mglistych Wysp", "Latarnia Mglistych Wysp", "Silne światło przebija mgłę i wskazuje bezpieczny kanał między skałami.")
_room("fog_shipyard", "Port Mglistych Wysp", "Stocznia Wyspiarzy", "Na pochylniach naprawiane są kutry, promy i niewielkie statki wyprawowe.")
_room("fog_salt_market", "Port Mglistych Wysp", "Plac Solny", "Kupcy przechowują tu sól, suszone ryby, liny i towary z odległych wysp.")
_room("fog_cliff_gate", "Port Mglistych Wysp", "Brama na Klifach", "Kamienna droga wspina się stąd na wybrzeże prowadzące w kierunku Twierdzy Popiołu.")
_link(sea_crossing[-1], "east", "fog_dock"); _link("fog_dock", "east", "fog_square")
_link("fog_square", "north", "fog_fish_market"); _link("fog_square", "south", "fog_inn")
_link("fog_square", "east", "fog_shipyard"); _link("fog_fish_market", "north", "fog_lighthouse")
_link("fog_shipyard", "south", "fog_salt_market"); _link("fog_square", "west", "fog_dock")
_link("fog_shipyard", "east", "fog_cliff_gate")

coast_road = _chain(
    "coast_highroad", "Klifowy Gościniec",
    ["Schody na Klif", "Droga nad Morzem", "Kamienny Balkon", "Wietrzna Przełęcz", "Strażnica Wybrzeża", "Popielny Zjazd"],
    "Wysoki gościniec biegnie nad morzem i łączy Mglisty Port z pograniczem Twierdzy Popiołu.",
)
_link("fog_cliff_gate", "east", coast_road[0])
_link(coast_road[-1], "north", "ash_south_gate")


# ---------------------------------------------------------------------------
# 2. HUNTING REGIONS
# ---------------------------------------------------------------------------

ZONE_DATA = [
    (
        "wolf_hills", "Wilcze Wzgórza", 35, "birch_east_gate", "east",
        ["Skraj Wilczych Wzgórz", "Trawiasty Grzbiet", "Ścieżka Tropicieli", "Wysoki Kopiec", "Kamienna Niecka", "Jar Wilczych Śladów", "Stary Dąb", "Legowisko Białego Kła"],
        [
            "Łagodne wzgórza są porośnięte wysoką trawą i niskimi brzozami.", "Wiatr odsłania ślady dużych watah.",
            "W błocie widać tropy zwierząt i myśliwych.", "Ze szczytu widać Brzozowy Trakt i odległe lasy.",
            "Kamienie tworzą naturalną osłonę dla drapieżników.", "Wąski jar zbiera zapachy i odgłosy całych wzgórz.",
            "Stary dąb nosi ślady pazurów wysoko ponad ziemią.", "Głębokie legowisko należy do największego drapieżnika w regionie.",
        ],
        [("hill_wolf", "Wilk Wzgórz", False), ("hill_boar", "Dziki Odyniec", False), ("hill_stalker", "Tropiciel Watahy", False)],
        ("white_fang_alpha", "Biały Kieł, Alfa Wzgórz", False), "hill_beast",
    ),
    (
        "stone_gullies", "Kamienne Jary", 70, "birch_rangers", "east",
        ["Wejście do Kamiennych Jarów", "Łupkowy Parów", "Półka Skalna", "Rozszczepiony Głaz", "Suchy Potok", "Kamienne Labirynty", "Jaskinia Kłusowników", "Głęboki Jar"],
        [
            "Niskie urwiska tworzą wejście do sieci suchych jarów.", "Kruchy łupek osuwa się spod stóp.",
            "Wąska półka biegnie nad kamiennym dnem parowu.", "Ogromny głaz został rozłupany dawnym uderzeniem.",
            "Koryto potoku jest suche, lecz pełne śladów zwierząt.", "Ścieżki rozdzielają się między podobnymi kamiennymi ścianami.",
            "Kłusownicy urządzili kryjówkę w płytkiej jaskini.", "Najgłębsza część jaru jest odcięta od światła przez wysokie ściany.",
        ],
        [("gully_poacher", "Kłusownik z Jarów", False), ("stone_hyena", "Kamienna Hiena", False), ("gully_brute", "Rabuś z Kamiennych Jarów", False)],
        ("gully_chieftain", "Wódz Kłusowników", False), "gully_raider",
    ),
    (
        "rust_valley", "Rdzawa Dolina", 115, "iron_miners", "north",
        ["Próg Rdzawej Doliny", "Czerwony Wąwóz", "Hałda Rudy", "Stare Tory", "Żelazne Rumowisko", "Porzucony Szyb", "Pole Golemów", "Rdzawe Serce Doliny"],
        [
            "Ziemia ma czerwony kolor od pyłu żelaznego.", "Ściany wąwozu błyszczą drobnymi żyłami metalu.",
            "Stare hałdy odpadów wydobywczych tworzą sztuczne wzgórza.", "Pogięte tory znikają pod kamieniami i rdzą.",
            "Połamane konstrukcje tworzą niebezpieczny labirynt.", "Stary szyb jest zamknięty, lecz wokół wciąż krążą agresywne stworzenia.",
            "Ciężkie kamienne sylwetki poruszają się między zardzewiałymi maszynami.", "W centrum doliny pulsuje skupisko rudy o nienaturalnej energii.",
        ],
        [("rust_golem", "Rdzawy Golem", False), ("ore_hound", "Rudny Ogar", False), ("scrap_raider", "Złomowy Maruder", False)],
        ("rust_colossus", "Kolos Rdzawej Doliny", False), "rust_creature",
    ),
    (
        "old_smelteries", "Stare Huty", 170, "iron_forge", "south",
        ["Brama Starych Hut", "Zgaszona Hala", "Kanał Żużlu", "Plac Pieców", "Pęknięty Komin", "Warsztat Form", "Podziemny Kanał Ciepła", "Wielki Martwy Piec"],
        [
            "Zrujnowane huty stoją tu od czasów wcześniejszych mieszkańców regionu.", "Wielka hala jest ciemna, ale metal wciąż trzeszczy od resztkowego ciepła.",
            "Czarny żużel utworzył zastygłe fale.", "Kilka wygaszonych pieców otacza szeroki plac.",
            "Pęknięty komin grozi zawaleniem przy każdym silniejszym podmuchu.", "Stare formy i stoły są porzucone między zwałami metalu.",
            "Kanał techniczny prowadzi ciepłe powietrze z głębi kompleksu.", "Największy piec budzi konstrukty, które miały pilnować huty.",
        ],
        [("slag_construct", "Konstrukt Żużlowy", False), ("furnace_wraith", "Upiór Pieca", True), ("steel_scavenger", "Stalowy Padlinożerca", False)],
        ("dead_furnace_guardian", "Strażnik Martwego Pieca", True), "smeltery_horror",
    ),
    (
        "mist_archipelago", "Mglisty Archipelag", 225, "fog_lighthouse", "east",
        ["Pierwsza Wysepka", "Kamienny Kanał", "Wyspa Wraków", "Mokre Skały", "Zarośnięta Przystań", "Ścieżka Rozbitków", "Wyspa Syren", "Mglista Kaplica"],
        [
            "Mała wyspa znika i pojawia się w gęstej mgle.", "Wąski kanał rozdziela dwie skaliste wysepki.",
            "Resztki kilku statków leżą między skałami.", "Śliskie kamienie są niemal całkowicie przykryte wodą podczas przypływu.",
            "Dawna przystań zarosła grubymi pnączami i glonami.", "Ślady dawnych rozbitków prowadzą przez wilgotny las.",
            "Dziwne pieśni odbijają się między skalnymi ścianami.", "Ruiny niewielkiej kaplicy są najstarszą budowlą archipelagu.",
        ],
        [("mist_pirate", "Pirat Mglistych Wysp", False), ("reef_hunter", "Łowca Raf", False), ("mist_siren", "Syrena Mgły", True)],
        ("mist_reaver", "Rozpruwacz Mglistych Wysp", False), "mist_raider",
    ),
    (
        "sunken_cliffs", "Zatopione Klify", 290, "fog_cliff_gate", "south",
        ["Krawędź Zatopionych Klifów", "Schody Pływów", "Jaskinia Przypływu", "Zalana Galeria", "Most Muszli", "Kamienne Baseny", "Krypta Marynarzy", "Otchłań pod Klifem"],
        [
            "Morze podmyło klif, tworząc dziesiątki półek i grot.", "Stare schody znikają pod wodą podczas wysokiego przypływu.",
            "Woda uderza rytmicznie o ściany jaskini.", "Dawna galeria jest częściowo zalana zimną morską wodą.",
            "Naturalny most jest pokryty grubymi warstwami muszli.", "Głębokie baseny kryją ruch pod ciemną powierzchnią.",
            "Kamienne nisze zawierają szczątki dawnych marynarzy.", "Najgłębszy uskok opada ku czarnej wodzie i pradawnym ruinom.",
        ],
        [("drowned_sailor", "Utopiony Marynarz", False), ("cliff_serpent", "Wąż Klifowy", False), ("tide_caller", "Przywoływacz Pływów", True)],
        ("abyssal_mariner", "Kapitan Otchłani", True), "drowned_cliff",
    ),
    (
        "ash_wastes", "Popielne Pustkowia", 370, "ash_west_gate", "north",
        ["Skraj Popielnych Pustkowi", "Szare Wydmy", "Spalony Las", "Pole Czarnych Kości", "Popielna Burza", "Złamany Obelisk", "Pusty Krater", "Krater Żywego Popiołu"],
        [
            "Za twierdzą zaczyna się ziemia pokryta grubą warstwą gorącego pyłu.", "Wiatr układa popiół w długie szare wydmy.",
            "Zwęglone pnie tworzą martwy las bez jednego zielonego liścia.", "Czarne kości wielkich stworzeń wystają z popiołu.",
            "Gęsty pył ogranicza widoczność niemal do kilku kroków.", "Pęknięty obelisk emituje słabe, niepokojące ciepło.",
            "Stary krater jest cichy, lecz jego dno nosi świeże ślady.", "W największym kraterze popiół porusza się jak żywa istota.",
        ],
        [("ash_wraith", "Upiór Popiołu", True), ("cinder_beast", "Bestia Żaru", False), ("waste_reaver", "Rozbójnik Pustkowi", False)],
        ("living_ash", "Żywy Popiół", True), "ashborn",
    ),
    (
        "titan_valley", "Dolina Tytanów", 480, "ash_upper_wall", "north",
        ["Wejście do Doliny Tytanów", "Ślad Olbrzyma", "Kamienny Las", "Rozbita Kolumna", "Taras Gigantów", "Równina Grzmotu", "Schody Tytanów", "Tron Pradawnego Tytana"],
        [
            "Droga schodzi między ściany tak wielkie, że wyglądają jak wykonane dla olbrzymów.", "W skale odciśnięty jest ślad większy od miejskiego domu.",
            "Pionowe kamienne iglice przypominają skamieniały las.", "Fragment pradawnej kolumny leży w poprzek całej doliny.",
            "Szeroki taras wygląda jak dawne miejsce zgromadzeń gigantów.", "Każdy krok ciężkich stworzeń odbija się tu jak grzmot.",
            "Olbrzymie stopnie prowadzą ku najstarszej części doliny.", "Kamienny tron stoi pośród ruin zbudowanych dla istot wielokrotnie większych od człowieka.",
        ],
        [("titan_spawn", "Pomniejszy Tytan", False), ("thunder_giant", "Olbrzym Grzmotu", False), ("stone_titan_mage", "Runiczny Tytan", True)],
        ("ancient_titan", "Pradawny Tytan Doliny", False), "titanborn",
    ),
]

ZONE_ROOM_IDS = {}
ZONE_MOB_IDS = {}
ZONE_BOSS_IDS = {}

for prefix, zone, stage, anchor, direction, names, descriptions, mob_defs, boss_def, target in ZONE_DATA:
    rooms = _grid_zone(prefix, zone, names, descriptions)
    _link(anchor, direction, rooms[0])
    ZONE_ROOM_IDS[zone] = tuple(rooms)

    mobs = []
    for offset, (mob_id, mob_name, magic) in enumerate(mob_defs):
        mobs.append(_mob(mob_id, mob_name, stage + offset * 8, target, magic=magic, drops={"soul_shard": 0.04 + 0.02 * offset}))
    boss_id, boss_name, boss_magic = boss_def
    boss = _mob(boss_id, boss_name, stage + 35, target, magic=boss_magic, boss=True, drops={"soul_shard": 0.55, "healing_potion": 0.25})
    ZONE_MOB_IDS[zone] = tuple(mobs)
    ZONE_BOSS_IDS[zone] = boss

    # Two regular enemies in every room; mix variants by room index.
    for idx, rid in enumerate(rooms):
        _spawn(rid, mobs[idx % len(mobs)], 1)
        _spawn(rid, mobs[(idx + 1) % len(mobs)], 1)
    _spawn(rooms[-1], boss, 1)

# Canonical boss room aliases from public spec.
for zone, spec in WORLD_EXPANSION_I_HUNTING_ZONES.items():
    actual_last = ZONE_ROOM_IDS[zone][-1]
    public_boss = spec["boss"]
    if public_boss != actual_last:
        # Replace the generated final id with the stable public id while preserving exits.
        payload = dict(ROOMS[actual_last])
        catalog_assign(payload, "ROOMS", ROOMS, (public_boss,))
        _NEW_ROOMS.append(public_boss)
        # Redirect all exits pointing at the temporary final room.
        for rid in tuple(_NEW_ROOMS):
            exits = ROOMS.get(rid, {}).get("exits", {})
            for direction, dest in tuple(exits.items()):
                if dest == actual_last:
                    catalog_set_path("ROOMS", ROOMS, (rid, "exits", direction), public_boss)
        # Redirect spawns and remove the temporary room from the catalog.
        for i, (rid, mid) in enumerate(list(MOB_SPAWNS)):
            if rid == actual_last:
                MOB_SPAWNS[i] = (public_boss, mid)
        # catalog_pop would be traceable, but the mutation layer exposes pop by path.
        from data.catalog_mutations import catalog_pop_path
        catalog_pop_path("ROOMS", ROOMS, (), actual_last)
        if actual_last in _NEW_ROOMS:
            _NEW_ROOMS.remove(actual_last)
        rooms = list(ZONE_ROOM_IDS[zone])
        rooms[-1] = public_boss
        ZONE_ROOM_IDS[zone] = tuple(rooms)


# ---------------------------------------------------------------------------
# 3. LOCAL QUEST GIVERS + REPEATABLE REGION CONTRACTS
# ---------------------------------------------------------------------------

QUEST_SPECS = [
    ("birch_hunt", "Oczyszczenie Wilczych Wzgórz", "Strażniczka Irena", "hill_beast", 14, "Pokonaj 14 drapieżników na Wilczych Wzgórzach i wróć do Ireny.", 480),
    ("birch_alpha", "Biały Kieł", "Strażniczka Irena", "white_fang_alpha", 1, "Odszukaj i pokonaj Białego Kła w najgłębszej części Wilczych Wzgórz.", 900),
    ("gully_patrol", "Kamienne Jary", "Tropiciel Seweryn", "gully_raider", 16, "Rozbij grupy kłusowników i drapieżników w Kamiennych Jarach.", 850),
    ("gully_chief", "Wódz Kłusowników", "Tropiciel Seweryn", "gully_chieftain", 1, "Pokonaj Wodza Kłusowników w Głębokim Jarze.", 1400),
    ("rust_cleanup", "Rdzawe Konstrukty", "Nadzorczyni Kira", "rust_creature", 18, "Zniszcz 18 niebezpiecznych stworzeń i konstruktów w Rdzawej Dolinie.", 1800),
    ("rust_colossus_quest", "Kolos Doliny", "Nadzorczyni Kira", "rust_colossus", 1, "Pokonaj Kolosa Rdzawej Doliny.", 3000),
    ("smeltery_clear", "Cienie Starych Hut", "Mistrz Huty Wern", "smeltery_horror", 20, "Oczyść Stare Huty z 20 konstruktów, upiorów i padlinożerców.", 2800),
    ("smeltery_guardian", "Strażnik Martwego Pieca", "Mistrz Huty Wern", "dead_furnace_guardian", 1, "Pokonaj Strażnika Martwego Pieca.", 4600),
    ("mist_patrol", "Patrol Archipelagu", "Kapitan Nara", "mist_raider", 22, "Pokonaj 22 piratów i stworzenia Mglistych Wysp.", 4500),
    ("mist_reaver_quest", "Rozpruwacz Mgły", "Kapitan Nara", "mist_reaver", 1, "Pokonaj Rozpruwacza Mglistych Wysp w Mglistej Kaplicy.", 7000),
    ("cliff_dead", "Utopieni z Klifów", "Latarnik Eryk", "drowned_cliff", 24, "Pokonaj 24 przeciwników na Zatopionych Klifach.", 6500),
    ("abyssal_mariner_quest", "Kapitan Otchłani", "Latarnik Eryk", "abyssal_mariner", 1, "Zejdź do Otchłani pod Klifem i pokonaj Kapitana Otchłani.", 10000),
    ("ash_wastes_patrol", "Popielny Patrol", "Dowódczyni Varda", "ashborn", 26, "Pokonaj 26 przeciwników na Popielnych Pustkowiach.", 11000),
    ("living_ash_quest", "Żywy Popiół", "Dowódczyni Varda", "living_ash", 1, "Pokonaj Żywy Popiół w największym kraterze pustkowi.", 17000),
    ("titan_valley_patrol", "Dolina Tytanów", "Badacz Orven", "titanborn", 28, "Pokonaj 28 istot w Dolinie Tytanów i zbierz informacje dla Orvena.", 18000),
    ("ancient_titan_quest", "Pradawny Tytan", "Badacz Orven", "ancient_titan", 1, "Pokonaj Pradawnego Tytana przy kamiennym tronie.", 28000),
]

for qid, qname, giver, target, needed, description, reward in QUEST_SPECS:
    _quest(qid, qname, giver, target, needed, description, reward, repeatable=True, cooldown=3600 if needed > 1 else 4 * 3600, boss=(needed == 1))

_npc("birch_guard_irena", "Strażniczka Irena", "birch_rangers", "Wilcze Wzgórza są dobrym terenem dla wędrowców, ale watahy podchodzą coraz bliżej osady.", ("birch_hunt", "birch_alpha"))
_npc("birch_tracker_seweryn", "Tropiciel Seweryn", "birch_east_gate", "Kamienne Jary pełne są kłusowników. Znam drogę do ich najgłębszych kryjówek.", ("gully_patrol", "gully_chief"))
_npc("iron_overseer_kira", "Nadzorczyni Kira", "iron_miners", "Rdzawa Dolina przestała być zwykłym terenem wydobywczym. Konstrukty atakują karawany i górników.", ("rust_cleanup", "rust_colossus_quest"))
_npc("iron_master_wern", "Mistrz Huty Wern", "iron_smith_guild", "Stare Huty znów są aktywne, ale nie za sprawą żywych hutników.", ("smeltery_clear", "smeltery_guardian"))
_npc("fog_captain_nara", "Kapitan Nara", "fog_dock", "Mgła ukrywa piratów i rzeczy znacznie starsze od ich statków.", ("mist_patrol", "mist_reaver_quest"))
_npc("fog_keeper_eryk", "Latarnik Eryk", "fog_lighthouse", "Zatopione Klify są niebezpieczne nawet dla doświadczonych marynarzy. Woda oddaje czasem tych, których dawno zabrała.", ("cliff_dead", "abyssal_mariner_quest"))
_npc("ash_commander_varda", "Dowódczyni Varda", "ash_command", "Twierdza istnieje po to, by Popielne Pustkowia nie przesunęły swojej granicy ani o krok.", ("ash_wastes_patrol", "living_ash_quest"))
_npc("ash_scholar_orven", "Badacz Orven", "ash_upper_wall", "Dolina Tytanów nie jest legendą. Każdy ślad w tej dolinie jest większy od naszych murów.", ("titan_valley_patrol", "ancient_titan_quest"))


# Refresh exploration after all new rooms are registered.
v0130_refresh_exploration_catalog()

WORLD_EXPANSION_I_STATE = {
    "version": WORLD_EXPANSION_I_VERSION,
    "settlement_count": len(WORLD_EXPANSION_I_SETTLEMENTS),
    "hunting_zone_count": len(WORLD_EXPANSION_I_HUNTING_ZONES),
    "room_count": len(set(_NEW_ROOMS)),
    "mob_template_count": len(set(_NEW_MOBS)),
    "npc_count": len(set(_NEW_NPCS)),
    "quest_count": len(set(_NEW_QUESTS)),
    "spawn_count": len(_NEW_SPAWNS),
    "settlements": dict(WORLD_EXPANSION_I_SETTLEMENTS),
    "hunting_zones": {k: dict(v) for k, v in WORLD_EXPANSION_I_HUNTING_ZONES.items()},
    "zone_rooms": {k: tuple(v) for k, v in ZONE_ROOM_IDS.items()},
    "zone_mobs": {k: tuple(v) for k, v in ZONE_MOB_IDS.items()},
    "zone_bosses": dict(ZONE_BOSS_IDS),
    "room_ids": tuple(dict.fromkeys(_NEW_ROOMS)),
    "mob_ids": tuple(dict.fromkeys(_NEW_MOBS)),
    "npc_ids": tuple(dict.fromkeys(_NEW_NPCS)),
    "quest_ids": tuple(dict.fromkeys(_NEW_QUESTS)),
}

__all__ = [
    "WORLD_EXPANSION_I_VERSION", "WORLD_EXPANSION_I_SETTLEMENTS",
    "WORLD_EXPANSION_I_HUNTING_ZONES", "WORLD_EXPANSION_I_STATE",
]

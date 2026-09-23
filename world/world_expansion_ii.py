# -*- coding: utf-8 -*-
"""Soulbound v0.52.0 - World Expansion II.

Adds the overseas land of Ardelia: one full capital, three satellite villages,
a looped road network and ten alternative hunting regions spanning early,
mid and very high progression.  The expansion is additive: it does not replace
or rebalance existing regions, and all catalog writes go through the v0.48
controlled mutation layer.
"""
from __future__ import annotations

from data.catalogs import ROOMS, NPCS, QUESTS, MOB_TEMPLATES
from data.catalog_mutations import catalog_assign, catalog_set_path, catalog_pop_path
from systems.content_registry import MOB_SPAWNS
from world.generation_systems import v0130_refresh_exploration_catalog

WORLD_EXPANSION_II_VERSION = "0.52.0"
WORLD_EXPANSION_II_CONTINENT = "Ardelia"
WORLD_EXPANSION_II_CAPITAL = {"Srebrna Korona": "silver_crown_square"}
WORLD_EXPANSION_II_VILLAGES = {
    "Zielony Brzeg": "green_shore_square",
    "Kamienna Straż": "stone_watch_square",
    "Cicha Przystań": "quiet_haven_square",
}

WORLD_EXPANSION_II_HUNTING_ZONES = {
    "Brzegi Szeptów": {"stage": 50, "hub": "whisper_shores_01", "boss": "whisper_shores_cove"},
    "Las Srebrnych Liści": {"stage": 90, "hub": "silverleaf_forest_01", "boss": "silverleaf_forest_heart"},
    "Ruiny Strażnicy Wichru": {"stage": 140, "hub": "windwatch_ruins_01", "boss": "windwatch_ruins_tower"},
    "Szkarłatne Mokradła": {"stage": 200, "hub": "scarlet_marsh_01", "boss": "scarlet_marsh_sanctum"},
    "Góry Burzowego Grzbietu": {"stage": 260, "hub": "storm_ridge_01", "boss": "storm_ridge_peak"},
    "Kryształowe Równiny": {"stage": 320, "hub": "crystal_plains_01", "boss": "crystal_plains_nexus"},
    "Pustynia Białego Szkła": {"stage": 380, "hub": "whiteglass_desert_01", "boss": "whiteglass_desert_mirage"},
    "Kanion Smoczych Kości": {"stage": 450, "hub": "dragonbone_canyon_01", "boss": "dragonbone_canyon_maw"},
    "Wyżyna Pękniętego Nieba": {"stage": 520, "hub": "shattered_sky_01", "boss": "shattered_sky_eye"},
    "Rubieże Nocy": {"stage": 590, "hub": "night_frontier_01", "boss": "night_frontier_gate"},
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


def _w2_room(room_id, zone, name, desc, exits=None):
    payload = {"zone": zone, "name": name, "desc": desc, "exits": dict(exits or {})}
    catalog_assign(payload, "ROOMS", ROOMS, (room_id,))
    _NEW_ROOMS.append(room_id)
    return room_id


def _w2_link(a, direction, b, *, reverse=True):
    catalog_set_path("ROOMS", ROOMS, (a, "exits", direction), b)
    if reverse:
        catalog_set_path("ROOMS", ROOMS, (b, "exits", _OPPOSITE[direction]), a)


def _w2_chain(prefix, zone, names, desc_prefix, direction="north"):
    ids = []
    for idx, name in enumerate(names, 1):
        rid = f"{prefix}_{idx:02d}"
        _w2_room(
            rid, zone, name,
            f"{desc_prefix} Odcinek {idx} ma własne punkty orientacyjne, dzięki czemu podróż nie jest anonimowym korytarzem.",
        )
        ids.append(rid)
        if len(ids) > 1:
            _w2_link(ids[-2], direction, ids[-1])
    return ids


def _w2_grid_zone(prefix, zone, names, descriptions):
    """Create an eight-room hunting loop with several internal shortcuts."""
    ids = []
    for idx in range(8):
        rid = f"{prefix}_{idx + 1:02d}"
        _w2_room(rid, zone, names[idx], descriptions[idx])
        ids.append(rid)
    _w2_link(ids[0], "east", ids[1]); _w2_link(ids[1], "east", ids[2]); _w2_link(ids[2], "east", ids[3])
    _w2_link(ids[4], "east", ids[5]); _w2_link(ids[5], "east", ids[6]); _w2_link(ids[6], "east", ids[7])
    _w2_link(ids[0], "south", ids[4]); _w2_link(ids[2], "south", ids[6]); _w2_link(ids[3], "south", ids[7])
    _w2_link(ids[5], "north", ids[1])
    return ids


def _w2_mob(mob_id, name, stage, target, *, magic=False, boss=False, drops=None):
    stage = int(stage)
    hp = 120 + stage * (19 if boss else 10)
    damage = 11 + stage // (3 if boss else 5)
    payload = {
        "name": name,
        "max_hp": hp,
        "damage": damage,
        "damage_type": "magic" if magic else "physical",
        "silver": 50 + stage * (8 if boss else 2),
        "gold": 0,
        "mithril": 0,
        "stat_reward": max(25, stage // 2),
        "class_xp_reward": max(160, stage * (29 if boss else 9)),
        "soul_reward": max(125, stage * (11 if boss else 4)),
        "drops": dict(drops or {}),
        "quest_target": mob_id if boss else target,
        "generator_level": stage,
        "v0520_world_expansion": True,
        "v0520_region_target": target,
    }
    if boss:
        payload.update({
            "rank": "boss", "boss": True,
            "quest_targets": (target, mob_id),
            "corpse_equipment_guaranteed": 1,
        })
    catalog_assign(payload, "MOB_TEMPLATES", MOB_TEMPLATES, (mob_id,))
    _NEW_MOBS.append(mob_id)
    return mob_id


def _w2_spawn(room_id, mob_id, count=1):
    for _ in range(max(1, int(count))):
        row = (room_id, mob_id)
        if row not in MOB_SPAWNS:
            MOB_SPAWNS.append(row)
            _NEW_SPAWNS.append(row)


def _w2_npc(npc_id, name, room, dialogue, quest_ids):
    payload = {
        "name": name,
        "room": room,
        "dialogue": dialogue,
        "quest": quest_ids[0] if quest_ids else None,
        "quest_chain": tuple(quest_ids[1:]),
        "v0520_world_expansion": True,
    }
    catalog_assign(payload, "NPCS", NPCS, (npc_id,))
    _NEW_NPCS.append(npc_id)


def _w2_quest(qid, name, giver, target, needed, description, silver, *, cooldown=3600, boss=False):
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
        "repeatable": True,
        "repeat_cooldown": int(cooldown),
        "v0520_world_expansion": True,
    }
    catalog_assign(payload, "QUESTS", QUESTS, (qid,))
    _NEW_QUESTS.append(qid)


# ---------------------------------------------------------------------------
# 1. OVERSEAS ROUTE + CAPITAL: SREBRNA KORONA
# ---------------------------------------------------------------------------

overseas = _w2_chain(
    "ardelia_crossing", "Szlak Zamorski",
    ["Prom Ardelijski", "Morze Zachodnie", "Prąd Srebrnych Wód", "Wyspa Nawigacyjna", "Cieśnina Ardelii", "Reda Srebrnej Korony"],
    "Dalekomorski szlak łączy Mglisty Port z nowym lądem Ardelii. Wokół zmieniają się prądy, wiatr i zapach morza.",
    direction="south",
)
_w2_link("fog_dock", "south", overseas[0])

_w2_room("silver_crown_harbor", "Srebrna Korona", "Wielki Port Srebrnej Korony", "Rozległy port przyjmuje statki z obu stron morza. Kamienne nabrzeża prowadzą prosto pod mury największego miasta Ardelii.")
_w2_room("silver_crown_square", "Srebrna Korona", "Plac Srebrnej Korony", "Centralny plac nowej stolicy otaczają wysokie kamienice, fontanny i szerokie ulice prowadzące do czterech dzielnic.")
_w2_room("silver_crown_market", "Srebrna Korona", "Wielki Rynek Ardelii", "Kupcy z całego kontynentu handlują tu metalem, żywnością, mapami i egzotycznymi towarami.")
_w2_room("silver_crown_inn", "Srebrna Korona", "Gospoda Czterech Szlaków", "Ogromna gospoda mieści podróżnych przybywających z portu, wsi i dalekich ekspedycji.")
_w2_room("silver_crown_temple", "Srebrna Korona", "Świątynia Srebrnego Światła", "Jasny kamień świątyni odbija światło nawet podczas pochmurnych dni.")
_w2_room("silver_crown_guilds", "Srebrna Korona", "Dzielnica Cechów", "Domy kupieckie, rzemieślnicze i odkrywcze stoją przy jednej szerokiej alei.")
_w2_room("silver_crown_library", "Srebrna Korona", "Biblioteka Kartografów", "Mapy Ardelii, stare dzienniki wypraw i zapisy o nieznanych rubieżach wypełniają wysokie regały.")
_w2_room("silver_crown_barracks", "Srebrna Korona", "Koszary Straży Koronnej", "Strażnicy szkolą się tu przed służbą na traktach i odległych granicach kontynentu.")
_w2_room("silver_crown_west_gate", "Srebrna Korona", "Zachodnia Brama Srebrnej Korony", "Za bramą biegnie zielony trakt ku spokojniejszym ziemiom zachodu.")
_w2_room("silver_crown_north_gate", "Srebrna Korona", "Północna Brama Srebrnej Korony", "Kamienna droga wspina się ku górom i posterunkom Kamiennej Straży.")
_w2_room("silver_crown_east_gate", "Srebrna Korona", "Wschodnia Brama Srebrnej Korony", "Trakt prowadzi ku mokradłom, wybrzeżu i Cichej Przystani.")
_w2_room("silver_crown_south_gate", "Srebrna Korona", "Południowa Brama Srebrnej Korony", "Za południową bramą zaczynają się suche równiny i coraz bardziej niezwykłe ziemie.")
_w2_room("silver_crown_arcane", "Srebrna Korona", "Dziedziniec Kryształowych Badaczy", "Badacze analizują tu minerały i anomalie przywożone z Kryształowych Równin.")
_w2_room("silver_crown_watch", "Srebrna Korona", "Wieża Dalekiego Widoku", "Ze szczytu widać trzy wielkie trakty, morze oraz góry przecinające północ Ardelii.")
_w2_room("silver_crown_canals", "Srebrna Korona", "Kanały Portowe", "Kamienne kanały łączą magazyny, doki i dolne dzielnice miasta.")
_w2_room("silver_crown_south_market", "Srebrna Korona", "Targ Karawan Południa", "Karawany przygotowują się tutaj do wypraw na suche i wysokopoziomowe tereny Ardelii.")
_w2_link(overseas[-1], "south", "silver_crown_harbor")
_w2_link("silver_crown_harbor", "south", "silver_crown_square")
_w2_link("silver_crown_square", "west", "silver_crown_inn"); _w2_link("silver_crown_square", "east", "silver_crown_market")
_w2_link("silver_crown_square", "north", "silver_crown_temple"); _w2_link("silver_crown_square", "south", "silver_crown_guilds")
_w2_link("silver_crown_market", "north", "silver_crown_library"); _w2_link("silver_crown_inn", "north", "silver_crown_barracks")
_w2_link("silver_crown_inn", "west", "silver_crown_west_gate"); _w2_link("silver_crown_temple", "north", "silver_crown_north_gate")
_w2_link("silver_crown_market", "east", "silver_crown_east_gate"); _w2_link("silver_crown_guilds", "south", "silver_crown_south_gate")
_w2_link("silver_crown_library", "east", "silver_crown_arcane"); _w2_link("silver_crown_barracks", "west", "silver_crown_watch")
_w2_link("silver_crown_harbor", "east", "silver_crown_canals"); _w2_link("silver_crown_south_gate", "east", "silver_crown_south_market")


# ---------------------------------------------------------------------------
# 2. THREE SATELLITE VILLAGES + LOOPED ROAD NETWORK
# ---------------------------------------------------------------------------

west_road = _w2_chain(
    "green_road", "Zielony Trakt",
    ["Aleja Winnic", "Most Zielonej Rzeki", "Sad Podróżnych", "Łąki Ardelii", "Rozstaj Dębowy", "Przedpole Zielonego Brzegu"],
    "Łagodny trakt prowadzi przez uprawne ziemie, sady i zielone wzgórza zachodniej Ardelii.", direction="west",
)
_w2_link("silver_crown_west_gate", "west", west_road[0])
_w2_room("green_shore_square", "Zielony Brzeg", "Plac Zielonego Brzegu", "Spokojna wieś stoi nad szeroką rzeką. Rybackie łodzie, pola i leśne trakty spotykają się przy niewielkim rynku.")
_w2_room("green_shore_inn", "Zielony Brzeg", "Karczma Nad Zieloną Wodą", "Niska drewniana karczma jest pełna rybaków, myśliwych i drwali.")
_w2_room("green_shore_hunters", "Zielony Brzeg", "Dom Tropicieli", "Tropiciele zbierają informacje o Brzegach Szeptów i Lesie Srebrnych Liści.")
_w2_room("green_shore_dock", "Zielony Brzeg", "Rzeczna Przystań", "Małe łodzie przewożą ludzi i towary wzdłuż Zielonej Rzeki.")
_w2_room("green_shore_west_gate", "Zielony Brzeg", "Zachodni Skraj Zielonego Brzegu", "Ścieżka biegnie ku cichym zatokom i morskim brzegom.")
_w2_room("green_shore_north_gate", "Zielony Brzeg", "Leśna Brama Zielonego Brzegu", "Za drewnianą bramą zaczyna się gęsty Las Srebrnych Liści.")
_w2_room("green_shore_east_gate", "Zielony Brzeg", "Wschodni Gościniec", "Droga prowadzi z powrotem ku Srebrnej Koronie i północnym traktom.")
_w2_link(west_road[-1], "west", "green_shore_east_gate"); _w2_link("green_shore_east_gate", "west", "green_shore_square")
_w2_link("green_shore_square", "south", "green_shore_inn"); _w2_link("green_shore_square", "north", "green_shore_hunters")
_w2_link("green_shore_square", "west", "green_shore_west_gate"); _w2_link("green_shore_hunters", "north", "green_shore_north_gate")
_w2_link("green_shore_square", "east", "green_shore_dock")

north_road = _w2_chain(
    "stonewatch_road", "Trakt Kamiennej Straży",
    ["Północny Nasyp", "Most Strażników", "Droga Strażników", "Przełęcz Chorągwi", "Mur Wiatru", "Przedpole Kamiennej Straży"],
    "Utwardzona droga stopniowo wspina się ku chłodniejszym, górskim terenom północnej Ardelii.", direction="north",
)
_w2_link("silver_crown_north_gate", "north", north_road[0])
_w2_room("stone_watch_square", "Kamienna Straż", "Plac Kamiennej Straży", "Warowna osada kontroluje przełęcze północnej Ardelii. Kamienne domy stoją ciasno między murami i skałami.")
_w2_room("stone_watch_inn", "Kamienna Straż", "Gospoda Pod Tarczą", "Wędrowcy ogrzewają się przy wielkim palenisku przed wyprawami w góry.")
_w2_room("stone_watch_barracks", "Kamienna Straż", "Koszary Górskiej Straży", "Żołnierze i zwiadowcy obserwują Ruiny Strażnicy Wichru oraz wyższe przełęcze.")
_w2_room("stone_watch_forge", "Kamienna Straż", "Kuźnia Przełęczy", "Miejscowi kowale wzmacniają wyposażenie przeznaczone na górskie wyprawy.")
_w2_room("stone_watch_west_gate", "Kamienna Straż", "Zachodnia Furta Straży", "Wąska droga prowadzi do ruin stojących na smaganym wiatrem wzgórzu.")
_w2_room("stone_watch_north_gate", "Kamienna Straż", "Północna Brama Straży", "Za bramą wznoszą się Góry Burzowego Grzbietu.")
_w2_room("stone_watch_east_gate", "Kamienna Straż", "Wschodnia Brama Straży", "Droga schodzi ku potężnym kanionom i kościom pradawnych smoków.")
_w2_room("stone_watch_tower", "Kamienna Straż", "Wieża Sygnałowa", "Ognie sygnałowe ostrzegają Srebrną Koronę przed zagrożeniami nadchodzącymi z północnych wyżyn.")
_w2_link(north_road[-1], "north", "stone_watch_square")
_w2_link("stone_watch_square", "south", "stone_watch_inn"); _w2_link("stone_watch_square", "north", "stone_watch_barracks")
_w2_link("stone_watch_square", "west", "stone_watch_west_gate"); _w2_link("stone_watch_square", "east", "stone_watch_forge")
_w2_link("stone_watch_barracks", "north", "stone_watch_north_gate"); _w2_link("stone_watch_forge", "east", "stone_watch_east_gate")
_w2_link("stone_watch_barracks", "west", "stone_watch_tower")

east_road = _w2_chain(
    "quiet_road", "Gościniec Wschodni",
    ["Droga Pól Solnych", "Most Białych Ptaków", "Stara Karczma Drogowa", "Wierzbowy Zakręt", "Kanał Handlowy", "Przedpole Cichej Przystani"],
    "Wschodni gościniec prowadzi przez wilgotniejsze ziemie i kanały zasilające nadmorskie osady.", direction="east",
)
_w2_link("silver_crown_east_gate", "east", east_road[0])
_w2_room("quiet_haven_square", "Cicha Przystań", "Plac Cichej Przystani", "Nadmorska osada leży między trzcinowiskami i suchymi wydmami. Z jednej strony pachnie mokradłem, z drugiej rozgrzanym piaskiem.")
_w2_room("quiet_haven_inn", "Cicha Przystań", "Gospoda Cichego Dzwonu", "Dźwięk niewielkiego dzwonu portowego miesza się z rozmowami kupców i przewodników.")
_w2_room("quiet_haven_dock", "Cicha Przystań", "Mały Port Wschodni", "Niskie nabrzeże obsługuje łodzie kursujące między przybrzeżnymi zatokami Ardelii.")
_w2_room("quiet_haven_marsh_gate", "Cicha Przystań", "Brama Mokradłowa", "Drewniane pomosty znikają w czerwonych trzcinach Szkarłatnych Mokradeł.")
_w2_room("quiet_haven_desert_gate", "Cicha Przystań", "Brama Białych Wydm", "Sucha droga biegnie ku Pustyni Białego Szkła.")
_w2_room("quiet_haven_watch", "Cicha Przystań", "Wieża Dalekiego Wschodu", "Strażnicy obserwują stąd niespokojne niebo i najdalsze rubieże kontynentu.")
_w2_room("quiet_haven_west_gate", "Cicha Przystań", "Zachodni Gościniec", "Szeroka droga prowadzi z powrotem do stolicy.")
_w2_link(east_road[-1], "east", "quiet_haven_west_gate"); _w2_link("quiet_haven_west_gate", "east", "quiet_haven_square")
_w2_link("quiet_haven_square", "south", "quiet_haven_inn"); _w2_link("quiet_haven_square", "east", "quiet_haven_dock")
_w2_link("quiet_haven_square", "north", "quiet_haven_marsh_gate"); _w2_link("quiet_haven_inn", "south", "quiet_haven_desert_gate")
_w2_link("quiet_haven_dock", "north", "quiet_haven_watch")

# Outer roads form a broad triangle so travel does not require returning through the capital.
green_stone = _w2_chain(
    "green_stone_loop", "Zachodni Trakt Okrężny",
    ["Dębowe Rozstaje", "Wysoki Sad", "Most Północnej Rzeki", "Podgórska Droga"],
    "Boczny trakt łączy zachodnie ziemie bezpośrednio z Kamienną Strażą.", direction="north",
)
_w2_link("green_shore_north_gate", "west", green_stone[0]); _w2_link(green_stone[-1], "east", "stone_watch_inn")

stone_quiet = _w2_chain(
    "stone_quiet_loop", "Wschodni Trakt Okrężny",
    ["Droga pod Urwiskiem", "Kamienny Wiadukt", "Pola Wschodniej Ardelii", "Kanał Strażniczy"],
    "Trakt omija stolicę i pozwala karawanom przejechać bezpośrednio z północy na wschodnie wybrzeże.", direction="east",
)
_w2_link("stone_watch_east_gate", "south", stone_quiet[0]); _w2_link(stone_quiet[-1], "south", "quiet_haven_watch")

green_quiet = _w2_chain(
    "southern_loop", "Południowy Trakt Ardelii",
    ["Rzeczny Bród", "Łąki Południa", "Kamień Kupców", "Suchy Kanał", "Wydmowe Rozstaje"],
    "Długi południowy szlak spina zachód i wschód kontynentu bez przejazdu przez Srebrną Koronę.", direction="east",
)
_w2_link("green_shore_west_gate", "south", green_quiet[0]); _w2_link(green_quiet[-1], "east", "quiet_haven_inn")


# ---------------------------------------------------------------------------
# 3. TEN ALTERNATIVE HUNTING REGIONS
# ---------------------------------------------------------------------------

ZONE_DATA = [
    (
        "whisper_shores", "Brzegi Szeptów", 50, "green_shore_west_gate", "west",
        ["Wejście na Brzegi Szeptów", "Piaszczysta Zatoka", "Kamienie Pływów", "Trawiasty Brzeg", "Grota Szumu", "Rozbite Molo", "Zatoka Morskich Ptaków", "Ukryta Zatoczka"],
        [
            "Łagodny brzeg ciągnie się między trawą i niskimi skałami.", "Fale wyrzucają drewno i muszle na szeroki pas piasku.",
            "Woda przepływa między ciemnymi głazami odsłanianymi przez odpływ.", "Słona trawa porasta płaskie wzgórza nad morzem.",
            "Mała grota wzmacnia każdy szmer fal do dziwnego szeptu.", "Resztki starego mola są kryjówką drapieżników.",
            "Setki ptaków krążą nad skalistym fragmentem wybrzeża.", "Cicha zatoczka skrywa największego drapieżnika brzegu.",
        ],
        [("shore_jackal", "Szakal Wybrzeża", False), ("salt_crab", "Wielki Krab Solny", False), ("whisper_stalker", "Tropiciel Szeptów", False)],
        ("cove_mauler", "Rozszarpywacz Zatoki", False), "shore_predator",
    ),
    (
        "silverleaf_forest", "Las Srebrnych Liści", 90, "green_shore_north_gate", "north",
        ["Skraj Lasu Srebrnych Liści", "Ścieżka Bladych Pni", "Srebrna Polana", "Korzenie nad Strumieniem", "Leśny Kamień", "Gęstwina Lustrzanych Liści", "Krąg Srebrnych Dębów", "Serce Srebrnego Lasu"],
        [
            "Liście mają jasne spodnie strony, przez co cały las migocze przy każdym podmuchu.", "Blada kora drzew odbija słabe światło.",
            "Okrągła polana świeci srebrzyście nawet w cieniu.", "Grube korzenie tworzą naturalne mosty nad zimnym strumieniem.",
            "Omszały głaz nosi stare znaki myśliwych.", "Gęste korony odbijają światło jak tysiące małych luster.",
            "Najstarsze dęby tworzą krąg wokół dawnego miejsca kultu.", "W głębi lasu czuć obecność istoty pilnującej całego regionu.",
        ],
        [("silverleaf_wolf", "Wilk Srebrnych Liści", False), ("mirror_stag", "Lustrzany Jeleń", False), ("leaf_witch", "Wiedźma Srebrnych Liści", True)],
        ("silverwood_keeper", "Strażnik Srebrnego Lasu", True), "silverleaf_creature",
    ),
    (
        "windwatch_ruins", "Ruiny Strażnicy Wichru", 140, "stone_watch_west_gate", "west",
        ["Droga do Strażnicy Wichru", "Zawalony Barbakan", "Dziedziniec Ruin", "Schody Chorągwi", "Pęknięty Mur", "Sala Wartowników", "Górny Taras", "Wieża Wichru"],
        [
            "Kamienna droga prowadzi ku ruinom starszym niż obecna Kamienna Straż.", "Barbakan runął, pozostawiając przejście między wielkimi blokami.",
            "Dziedziniec zarósł ostrą trawą i niskimi krzakami.", "Szerokie schody prowadzą ku pozostałościom murów.",
            "Silny wiatr przechodzi przez szerokie pęknięcie w murze.", "Dawna sala wartowników jest pełna śladów nowych mieszkańców.",
            "Z tarasu widać prawie całą zachodnią Ardelie.", "Ostatnia wieża nadal stoi i przyciąga niebezpieczne istoty wiatru.",
        ],
        [("ruin_marauder", "Maruder Strażnicy", False), ("wind_harpy", "Harpia Wichru", False), ("tower_adept", "Adept Burzowej Wieży", True)],
        ("windwatch_castellan", "Kasztelan Wichru", True), "windwatch_enemy",
    ),
    (
        "scarlet_marsh", "Szkarłatne Mokradła", 200, "quiet_haven_marsh_gate", "north",
        ["Pomost Szkarłatnych Mokradeł", "Czerwone Trzciny", "Grząska Wyspa", "Zatopione Drzewa", "Mgła nad Bagnem", "Krąg Czerwonych Kwiatów", "Stara Chata", "Sanktuarium Mokradeł"],
        [
            "Drewniane pomosty prowadzą ponad ciemną wodą.", "Wysokie czerwone trzciny szeleszczą nawet bez wiatru.",
            "Twardy skrawek ziemi jest pełen śladów dużych płazów.", "Martwe drzewa wystają z wody jak czarne pale.",
            "Ciężka mgła zasłania sąsiednie wysepki.", "Jaskrawe kwiaty rosną w idealnym okręgu.",
            "Porzucona chata zielarki stoi na palach ponad bagnem.", "Kamienne sanktuarium tonie częściowo w czerwonej wodzie.",
        ],
        [("scarlet_leech", "Szkarłatna Pijawka", False), ("marsh_hydra", "Bagienna Hydra", False), ("bog_oracle", "Wyrocznia Mokradeł", True)],
        ("scarlet_matron", "Matrona Szkarłatnego Bagna", True), "scarlet_marsh_enemy",
    ),
    (
        "storm_ridge", "Góry Burzowego Grzbietu", 260, "stone_watch_north_gate", "north",
        ["Dolna Ścieżka Burzowego Grzbietu", "Kamienne Serpentyny", "Półka Chmur", "Rozdarta Turnia", "Most nad Przepaścią", "Pole Piorunów", "Próg Szczytu", "Szczyt Burzowego Grzbietu"],
        [
            "Wąska ścieżka zaczyna wspinać się między granitowymi ścianami.", "Serpentyny prowadzą coraz wyżej ponad dolinę.",
            "Chmury przesuwają się poniżej kamiennej półki.", "Turnia została rozłupana dawnym uderzeniem pioruna.",
            "Kamienny most drży od podmuchów wiatru.", "Błyskawice regularnie uderzają w metaliczne skały.",
            "Ostatnia ścieżka prowadzi niemal pionowo ku grani.", "Na szczycie burza zdaje się nigdy nie ustawać.",
        ],
        [("storm_goat", "Rogacz Burzowy", False), ("thunder_roc", "Gromowy Rok", False), ("lightning_adept", "Adept Piorunów", True)],
        ("storm_crowned_roc", "Koronowany Rok Burzy", True), "storm_ridge_enemy",
    ),
    (
        "crystal_plains", "Kryształowe Równiny", 320, "silver_crown_arcane", "east",
        ["Skraj Kryształowych Równin", "Pole Błękitnych Odłamków", "Lustrzany Trakt", "Kryształowy Jar", "Świetlista Niecka", "Pole Rezonansu", "Krąg Monolitów", "Kryształowy Węzeł"],
        [
            "Z ziemi wyrastają pierwsze małe kryształy.", "Błękitne odłamki pokrywają ziemię jak gruby szron.",
            "Gładkie kryształy odbijają sylwetki podróżnych.", "Wąski jar wypełniają pionowe iglice minerału.",
            "Światło załamuje się w setkach różnych kolorów.", "Każdy dźwięk wywołuje drganie całego pola.",
            "Ogromne monolity tworzą geometryczny krąg.", "W centrum równin energia skupia się w jednym pulsującym węźle.",
        ],
        [("crystal_hound", "Kryształowy Ogar", False), ("shard_golem", "Golem Odłamków", False), ("prism_mage", "Mag Pryzmatu", True)],
        ("crystal_nexus_guardian", "Strażnik Kryształowego Węzła", True), "crystal_plains_enemy",
    ),
    (
        "whiteglass_desert", "Pustynia Białego Szkła", 380, "quiet_haven_desert_gate", "south",
        ["Pierwsze Białe Wydmy", "Morze Szkła", "Sucha Studnia", "Oaza Bez Cienia", "Pole Szklanych Igieł", "Rozgrzany Kanion", "Pałac Mirażu", "Serce Mirażu"],
        [
            "Jasny piasek zaczyna błyszczeć jak rozbite szkło.", "Wiatr przesuwa ostre drobiny po płaskiej pustyni.",
            "Stara studnia jest sucha od wielu lat.", "Woda oazy nie rzuca żadnego odbicia.",
            "Cienkie szklane igły wyrastają całymi skupiskami.", "Rozgrzane ściany kanionu wypaczają obraz.",
            "Na horyzoncie pojawia się budowla, która znika przy każdym kroku.", "W centrum mirażu czeka istota podtrzymująca iluzję całej pustyni.",
        ],
        [("glass_scorpion", "Skorpion Białego Szkła", False), ("dune_revenant", "Upiór Białych Wydm", True), ("mirage_raider", "Łupieżca Mirażu", False)],
        ("whiteglass_djinn", "Dżinn Białego Szkła", True), "whiteglass_enemy",
    ),
    (
        "dragonbone_canyon", "Kanion Smoczych Kości", 450, "stone_watch_east_gate", "east",
        ["Wejście do Kanionu Smoczych Kości", "Żebro Olbrzyma", "Most Kręgów", "Cmentarz Skrzydeł", "Popękana Czaszka", "Wąwóz Szponów", "Stos Kręgów", "Paszcza Kanionu"],
        [
            "Białe kości wystają ze skał po obu stronach drogi.", "Ogromne żebro tworzy łuk ponad ścieżką.",
            "Naturalny most powstał z połączonych kamieniem kręgów wielkiego smoka.", "Płaskowyż pokrywają skamieniałe szczątki skrzydeł.",
            "Pęknięta czaszka jest większa od małego domu.", "Ściany wąwozu noszą długie ślady pradawnych pazurów.",
            "Kości wielu stworzeń zostały ułożone w nienaturalnie równy stos.", "Najgłębsza część kanionu przypomina otwartą paszczę potężnego smoka.",
        ],
        [("bone_drake", "Kościany Drak", False), ("canyon_wyrm", "Żmij Kanionu", False), ("dragonbone_seer", "Wieszcz Smoczych Kości", True)],
        ("bone_ancestor", "Przodek Smoczych Kości", True), "dragonbone_enemy",
    ),
    (
        "shattered_sky", "Wyżyna Pękniętego Nieba", 520, "stone_watch_tower", "north",
        ["Podejście na Wyżynę", "Kamienne Schody Nieba", "Płaskowyż Chmur", "Pęknięta Grań", "Pole Grawitacyjnych Skał", "Martwa Burza", "Krąg Rozdarcia", "Oko Pękniętego Nieba"],
        [
            "Ścieżka prowadzi wysoko ponad zwykłe szczyty.", "Nieregularne stopnie zostały wycięte w pionowej skale.",
            "Chmury przesuwają się niemal na wysokości ziemi.", "Przez grań biegnie szerokie pęknięcie pełne bladego światła.",
            "Kamienie unoszą się na chwilę nad ziemią i opadają kilka kroków dalej.", "Ciemna burza pozostaje nieruchoma nad jednym fragmentem wyżyny.",
            "Skały wokół rozdarcia są gładkie jak po stopieniu.", "W centrum wyżyny otwiera się wir przypominający oko w samym niebie.",
        ],
        [("sky_ripper", "Rozdzieracz Nieba", False), ("gravity_golem", "Golem Grawitacji", False), ("rift_caller", "Przywoływacz Rozdarcia", True)],
        ("shattered_sky_eye_boss", "Oko Pękniętego Nieba", True), "shattered_sky_enemy",
    ),
    (
        "night_frontier", "Rubieże Nocy", 590, "quiet_haven_watch", "east",
        ["Droga ku Rubieżom Nocy", "Zmierzchowe Kamienie", "Pole Bez Gwiazd", "Czarna Rzeka", "Las Nocnych Iglic", "Brama Cienia", "Przedpole Nocy", "Wrota Rubieży"],
        [
            "Światło wyraźnie słabnie mimo otwartego nieba.", "Ciemne kamienie pochłaniają światło lamp i pochodni.",
            "Nad równiną nie widać ani jednej gwiazdy.", "Czarna woda płynie bez najmniejszego odbicia.",
            "Wysokie, cienkie skały przypominają martwy las.", "Dwa monolity tworzą przejście do jeszcze ciemniejszej części rubieży.",
            "Każdy dźwięk jest tu tłumiony przez ciężką ciszę.", "Pradawne wrota stoją na granicy ziem, których nie opisuje żadna mapa Srebrnej Korony.",
        ],
        [("night_hunter", "Łowca Rubieży Nocy", False), ("void_beast", "Bestia Pustki", False), ("starless_magus", "Mag Bezgwiezdnej Nocy", True)],
        ("night_gate_keeper", "Strażnik Wrót Nocy", True), "night_frontier_enemy",
    ),
]

ZONE_ROOM_IDS = {}
ZONE_MOB_IDS = {}
ZONE_BOSS_IDS = {}

for prefix, zone, stage, anchor, direction, names, descriptions, mob_defs, boss_def, target in ZONE_DATA:
    rooms = _w2_grid_zone(prefix, zone, names, descriptions)
    _w2_link(anchor, direction, rooms[0])
    ZONE_ROOM_IDS[zone] = tuple(rooms)

    mobs = []
    for offset, (mob_id, mob_name, magic) in enumerate(mob_defs):
        mobs.append(_w2_mob(mob_id, mob_name, stage + offset * 9, target, magic=magic, drops={"soul_shard": 0.05 + 0.02 * offset}))
    boss_id, boss_name, boss_magic = boss_def
    boss = _w2_mob(boss_id, boss_name, stage + 40, target, magic=boss_magic, boss=True, drops={"soul_shard": 0.60, "healing_potion": 0.25})
    ZONE_MOB_IDS[zone] = tuple(mobs)
    ZONE_BOSS_IDS[zone] = boss

    for idx, rid in enumerate(rooms):
        _w2_spawn(rid, mobs[idx % len(mobs)], 1)
        _w2_spawn(rid, mobs[(idx + 1) % len(mobs)], 1)
    _w2_spawn(rooms[-1], boss, 1)

# Stable public ids for boss rooms, mirroring the World Expansion I convention.
for zone, spec in WORLD_EXPANSION_II_HUNTING_ZONES.items():
    actual_last = ZONE_ROOM_IDS[zone][-1]
    public_boss = spec["boss"]
    if public_boss != actual_last:
        payload = dict(ROOMS[actual_last])
        catalog_assign(payload, "ROOMS", ROOMS, (public_boss,))
        _NEW_ROOMS.append(public_boss)
        for rid in tuple(_NEW_ROOMS):
            exits = ROOMS.get(rid, {}).get("exits", {})
            for direction, dest in tuple(exits.items()):
                if dest == actual_last:
                    catalog_set_path("ROOMS", ROOMS, (rid, "exits", direction), public_boss)
        for i, (rid, mid) in enumerate(list(MOB_SPAWNS)):
            if rid == actual_last:
                MOB_SPAWNS[i] = (public_boss, mid)
        catalog_pop_path("ROOMS", ROOMS, (), actual_last)
        if actual_last in _NEW_ROOMS:
            _NEW_ROOMS.remove(actual_last)
        rooms = list(ZONE_ROOM_IDS[zone]); rooms[-1] = public_boss; ZONE_ROOM_IDS[zone] = tuple(rooms)


# ---------------------------------------------------------------------------
# 4. LOCAL QUESTS: TWO PER HUNTING REGION
# ---------------------------------------------------------------------------

QUEST_SPECS = [
    ("whisper_shores_patrol", "Szepty Wybrzeża", "Tropicielka Mila", "shore_predator", 14, "Pokonaj 14 drapieżników na Brzegach Szeptów.", 650),
    ("cove_mauler_quest", "Rozszarpywacz Zatoki", "Tropicielka Mila", "cove_mauler", 1, "Odszukaj i pokonaj Rozszarpywacza Zatoki.", 1200),
    ("silverleaf_patrol", "Straż Srebrnego Lasu", "Leśnik Boran", "silverleaf_creature", 16, "Oczyść Las Srebrnych Liści z 16 niebezpiecznych stworzeń.", 1200),
    ("silverwood_keeper_quest", "Strażnik Lasu", "Leśnik Boran", "silverwood_keeper", 1, "Pokonaj Strażnika Srebrnego Lasu.", 2200),
    ("windwatch_patrol", "Ruiny na Wietrze", "Kapitan Rena", "windwatch_enemy", 18, "Pokonaj 18 przeciwników w Ruinach Strażnicy Wichru.", 2200),
    ("windwatch_castellan_quest", "Kasztelan Wichru", "Kapitan Rena", "windwatch_castellan", 1, "Pokonaj Kasztelana Wichru w ocalałej wieży.", 3800),
    ("scarlet_marsh_patrol", "Szkarłatne Mokradła", "Zielarka Livia", "scarlet_marsh_enemy", 20, "Pokonaj 20 stworzeń na Szkarłatnych Mokradłach.", 3600),
    ("scarlet_matron_quest", "Matrona Bagna", "Zielarka Livia", "scarlet_matron", 1, "Pokonaj Matronę Szkarłatnego Bagna.", 6000),
    ("storm_ridge_patrol", "Burzowy Grzbiet", "Zwiadowca Toren", "storm_ridge_enemy", 22, "Pokonaj 22 przeciwników w Górach Burzowego Grzbietu.", 5500),
    ("storm_crowned_roc_quest", "Koronowany Rok", "Zwiadowca Toren", "storm_crowned_roc", 1, "Pokonaj Koronowanego Roka Burzy.", 9000),
    ("crystal_plains_patrol", "Rezonans Równin", "Badaczka Sera", "crystal_plains_enemy", 24, "Pokonaj 24 istoty na Kryształowych Równinach.", 8000),
    ("crystal_nexus_guardian_quest", "Strażnik Węzła", "Badaczka Sera", "crystal_nexus_guardian", 1, "Pokonaj Strażnika Kryształowego Węzła.", 13000),
    ("whiteglass_patrol", "Białe Szkło", "Przewodnik Navir", "whiteglass_enemy", 26, "Pokonaj 26 przeciwników na Pustyni Białego Szkła.", 11500),
    ("whiteglass_djinn_quest", "Dżinn Mirażu", "Przewodnik Navir", "whiteglass_djinn", 1, "Pokonaj Dżinna Białego Szkła.", 18500),
    ("dragonbone_patrol", "Kości Smoków", "Kronikarka Dalia", "dragonbone_enemy", 28, "Pokonaj 28 istot w Kanionie Smoczych Kości.", 16500),
    ("bone_ancestor_quest", "Przodek Smoczych Kości", "Kronikarka Dalia", "bone_ancestor", 1, "Pokonaj Przodka Smoczych Kości w Paszczy Kanionu.", 26000),
    ("shattered_sky_patrol", "Pęknięte Niebo", "Obserwator Kael", "shattered_sky_enemy", 30, "Pokonaj 30 przeciwników na Wyżynie Pękniętego Nieba.", 23000),
    ("shattered_sky_eye_quest", "Oko Pękniętego Nieba", "Obserwator Kael", "shattered_sky_eye_boss", 1, "Pokonaj Oko Pękniętego Nieba.", 36000),
    ("night_frontier_patrol", "Rubieże Nocy", "Strażniczka Noa", "night_frontier_enemy", 32, "Pokonaj 32 istoty na Rubieżach Nocy.", 32000),
    ("night_gate_keeper_quest", "Strażnik Wrót Nocy", "Strażniczka Noa", "night_gate_keeper", 1, "Pokonaj Strażnika Wrót Nocy.", 50000),
]

for qid, qname, giver, target, needed, description, reward in QUEST_SPECS:
    _w2_quest(qid, qname, giver, target, needed, description, reward, cooldown=3600 if needed > 1 else 4 * 3600, boss=(needed == 1))

_w2_npc("green_tracker_mila", "Tropicielka Mila", "green_shore_hunters", "Znam każdy ślad na Brzegach Szeptów. Ostatnio największe drapieżniki podchodzą zbyt blisko wsi.", ("whisper_shores_patrol", "cove_mauler_quest"))
_w2_npc("green_forester_boran", "Leśnik Boran", "green_shore_north_gate", "Srebrny Las wygląda spokojnie, ale jego najstarszy strażnik nie toleruje obcych.", ("silverleaf_patrol", "silverwood_keeper_quest"))
_w2_npc("stone_captain_rena", "Kapitan Rena", "stone_watch_barracks", "Ruiny Wichru znów zostały zajęte. Potrzebujemy kogoś, kto dotrze aż do starej wieży.", ("windwatch_patrol", "windwatch_castellan_quest"))
_w2_npc("quiet_herbalist_livia", "Zielarka Livia", "quiet_haven_marsh_gate", "Szkarłatne Mokradła są pełne użytecznych roślin, ale dziś wejście tam bez broni jest samobójstwem.", ("scarlet_marsh_patrol", "scarlet_matron_quest"))
_w2_npc("stone_scout_toren", "Zwiadowca Toren", "stone_watch_north_gate", "Na Burzowym Grzbiecie pojawił się ogromny rok. Jego cień widać z samej osady.", ("storm_ridge_patrol", "storm_crowned_roc_quest"))
_w2_npc("silver_researcher_sera", "Badaczka Sera", "silver_crown_arcane", "Rezonans Kryształowych Równin przyciąga konstrukty i magów. Potrzebuję danych z samego węzła.", ("crystal_plains_patrol", "crystal_nexus_guardian_quest"))
_w2_npc("quiet_guide_navir", "Przewodnik Navir", "quiet_haven_desert_gate", "Na Pustyni Białego Szkła drogowskazy kłamią. Nie ufaj temu, co widzisz na horyzoncie.", ("whiteglass_patrol", "whiteglass_djinn_quest"))
_w2_npc("stone_chronicler_dalia", "Kronikarka Dalia", "stone_watch_east_gate", "Smocze kości w kanionie są starsze od naszych najstarszych kronik. Coś jednak wciąż ich pilnuje.", ("dragonbone_patrol", "bone_ancestor_quest"))
_w2_npc("stone_observer_kael", "Obserwator Kael", "stone_watch_tower", "Pęknięcie nad wyżyną rośnie. Jeśli Oko jest istotą, trzeba sprawdzić, czy da się je zranić.", ("shattered_sky_patrol", "shattered_sky_eye_quest"))
_w2_npc("quiet_guard_noa", "Strażniczka Noa", "quiet_haven_watch", "Rubieże Nocy leżą poza zwykłymi szlakami. Wrota na końcu drogi nigdy nie powinny się otworzyć.", ("night_frontier_patrol", "night_gate_keeper_quest"))


v0130_refresh_exploration_catalog()

WORLD_EXPANSION_II_STATE = {
    "version": WORLD_EXPANSION_II_VERSION,
    "continent": WORLD_EXPANSION_II_CONTINENT,
    "capital_count": len(WORLD_EXPANSION_II_CAPITAL),
    "village_count": len(WORLD_EXPANSION_II_VILLAGES),
    "settlement_count": len(WORLD_EXPANSION_II_CAPITAL) + len(WORLD_EXPANSION_II_VILLAGES),
    "hunting_zone_count": len(WORLD_EXPANSION_II_HUNTING_ZONES),
    "room_count": len(set(_NEW_ROOMS)),
    "mob_template_count": len(set(_NEW_MOBS)),
    "npc_count": len(set(_NEW_NPCS)),
    "quest_count": len(set(_NEW_QUESTS)),
    "spawn_count": len(_NEW_SPAWNS),
    "capital": dict(WORLD_EXPANSION_II_CAPITAL),
    "villages": dict(WORLD_EXPANSION_II_VILLAGES),
    "settlements": {**WORLD_EXPANSION_II_CAPITAL, **WORLD_EXPANSION_II_VILLAGES},
    "hunting_zones": {k: dict(v) for k, v in WORLD_EXPANSION_II_HUNTING_ZONES.items()},
    "zone_rooms": {k: tuple(v) for k, v in ZONE_ROOM_IDS.items()},
    "zone_mobs": {k: tuple(v) for k, v in ZONE_MOB_IDS.items()},
    "zone_bosses": dict(ZONE_BOSS_IDS),
    "room_ids": tuple(dict.fromkeys(_NEW_ROOMS)),
    "mob_ids": tuple(dict.fromkeys(_NEW_MOBS)),
    "npc_ids": tuple(dict.fromkeys(_NEW_NPCS)),
    "quest_ids": tuple(dict.fromkeys(_NEW_QUESTS)),
}

__all__ = [
    "WORLD_EXPANSION_II_VERSION", "WORLD_EXPANSION_II_CONTINENT",
    "WORLD_EXPANSION_II_CAPITAL", "WORLD_EXPANSION_II_VILLAGES",
    "WORLD_EXPANSION_II_HUNTING_ZONES", "WORLD_EXPANSION_II_STATE",
]

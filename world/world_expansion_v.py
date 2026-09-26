# -*- coding: utf-8 -*-
"""Soulbound v0.90.0 - Deep World & Cities Expansion.

Three large content pillars:
- three-level catacombs below the expanded Temple Basement,
- three 40-room story dungeons on the Broken Star Archipelago,
- Cities 2.0 expansion for every courier city currently registered.

The module is additive and uses the existing world, quest, NPC and spawn catalogs.
"""
from __future__ import annotations

import re
import unicodedata

from data.catalogs import ROOMS, NPCS, ITEMS, QUESTS, MOB_TEMPLATES
from data.catalog_mutations import catalog_assign, catalog_set_path
from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES, MOB_SPAWNS
from config.postal import POSTAL_CITY_HUBS_V0522, GUIDE_CITY_HUBS_V0522
from world.generation_systems import v0130_refresh_exploration_catalog
from world.world_expansion_iv import ZONE_ROOM_IDS as V0800_ZONE_ROOM_IDS, STORY_QUEST_IDS_V0800

WORLD_EXPANSION_V_VERSION = "0.90.0"
WORLD_EXPANSION_V_NAME = "Głębie Świata i Miasta 2.0"

_V0900_OPPOSITE = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "northeast": "southwest", "southwest": "northeast",
    "northwest": "southeast", "southeast": "northwest",
    "up": "down", "down": "up",
}
_V0900_DIRS = tuple(_V0900_OPPOSITE)

V0900_NEW_ROOMS = []
V0900_NEW_MOBS = []
V0900_NEW_NPCS = []
V0900_NEW_QUESTS = []
V0900_NEW_ITEMS = []
V0900_NEW_SPAWNS = []


def _v0900_slug(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("ł", "l")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _v0900_room(room_id, zone, name, desc, **extra):
    if room_id in ROOMS:
        raise RuntimeError(f"v0.90.0 duplicate room id: {room_id}")
    payload = {"zone": zone, "name": name, "desc": desc, "exits": {}, "v0900_expansion": True}
    payload.update(extra)
    catalog_assign(payload, "ROOMS", ROOMS, (room_id,))
    V0900_NEW_ROOMS.append(room_id)
    return room_id


def _v0900_link(a, direction, b, reverse=True):
    if a not in ROOMS or b not in ROOMS:
        raise RuntimeError(f"v0.90.0 missing room while linking {a} {direction} {b}")
    if direction not in _V0900_OPPOSITE:
        raise RuntimeError(f"v0.90.0 unsupported direction: {direction}")
    old = (ROOMS[a].get("exits") or {}).get(direction)
    if old not in (None, b):
        raise RuntimeError(f"v0.90.0 would overwrite exit {a}.{direction}: {old} -> {b}")
    catalog_set_path("ROOMS", ROOMS, (a, "exits", direction), b)
    if reverse:
        back = _V0900_OPPOSITE[direction]
        old_back = (ROOMS[b].get("exits") or {}).get(back)
        if old_back not in (None, a):
            raise RuntimeError(f"v0.90.0 would overwrite exit {b}.{back}: {old_back} -> {a}")
        catalog_set_path("ROOMS", ROOMS, (b, "exits", back), a)


def _v0900_first_free_direction(room_id, preferred=()):
    used = set((ROOMS[room_id].get("exits") or {}).keys())
    for direction in tuple(preferred) + _V0900_DIRS:
        if direction not in used:
            return direction
    raise RuntimeError(f"v0.90.0 no free direction from {room_id}")


def _v0900_grid(prefix, zone, rows, cols, name_prefix, desc, **extra):
    ids = []
    for r in range(rows):
        row = []
        for c in range(cols):
            idx = r * cols + c + 1
            rid = f"v0900_{prefix}_{idx:02d}"
            row.append(_v0900_room(
                rid, zone, f"{name_prefix} {idx}",
                f"{desc} Punkt {idx} rozgałęzia trasę i nie prowadzi wyłącznie prostym korytarzem.",
                **extra,
            ))
        ids.append(row)
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                _v0900_link(ids[r][c], "east", ids[r][c + 1])
            if r + 1 < rows:
                _v0900_link(ids[r][c], "south", ids[r + 1][c])
    return [rid for row in ids for rid in row]


def _v0900_mob(mob_id, name, stage, *, magic=False, boss=False, mechanic=None, mechanic_text=None, drops=None, tags=None):
    if mob_id in MOB_TEMPLATES:
        raise RuntimeError(f"v0.90.0 duplicate mob id: {mob_id}")
    stage = int(stage)
    payload = {
        "name": name,
        "max_hp": 220 + stage * (22 if boss else 11),
        "damage": 22 + stage // (3 if boss else 5),
        "damage_type": "magic" if magic else "physical",
        "silver": 150 + stage * (10 if boss else 4),
        "gold": max(1, stage // (60 if boss else 140)),
        "mithril": 0,
        "stat_reward": max(100, stage // 2),
        "class_xp_reward": max(1400, stage * (36 if boss else 12)),
        "soul_reward": max(1000, stage * (16 if boss else 6)),
        "drops": dict(drops or {}),
        "quest_target": mob_id,
        "generator_level": stage,
        "v0900_expansion": True,
    }
    if tags:
        payload.update(tags)
    if boss:
        payload.update({"rank": "boss", "boss": True, "quest_targets": (mob_id,), "corpse_equipment_guaranteed": 1})
    if mechanic:
        payload["boss_mechanic"] = mechanic
    if mechanic_text:
        payload["boss_mechanic_text"] = mechanic_text
    catalog_assign(payload, "MOB_TEMPLATES", MOB_TEMPLATES, (mob_id,))
    V0900_NEW_MOBS.append(mob_id)
    return mob_id


def _v0900_spawn(room_id, mob_id, count=1):
    if room_id not in ROOMS or mob_id not in MOB_TEMPLATES:
        raise RuntimeError(f"v0.90.0 invalid spawn {room_id}->{mob_id}")
    for _ in range(max(1, int(count))):
        row = (room_id, mob_id)
        MOB_SPAWNS.append(row)
        V0900_NEW_SPAWNS.append(row)


def _v0900_npc(npc_id, name, room, dialogue, quest_ids=(), **extra):
    if npc_id in NPCS:
        raise RuntimeError(f"v0.90.0 duplicate NPC id: {npc_id}")
    payload = {"name": name, "room": room, "dialogue": dialogue, "v0900_expansion": True}
    payload.update(extra)
    qids = tuple(quest_ids)
    if qids:
        payload["quest"] = qids[0]
        payload["quest_chain"] = qids[1:]
    catalog_assign(payload, "NPCS", NPCS, (npc_id,))
    V0900_NEW_NPCS.append(npc_id)
    return npc_id


def _v0900_item(item_id, name, desc, item_type="quest", **extra):
    if item_id in ITEMS:
        raise RuntimeError(f"v0.90.0 duplicate item id: {item_id}")
    payload = {"name": name, "type": item_type, "price": None, "desc": desc, "v0900_expansion": True}
    payload.update(extra)
    catalog_assign(payload, "ITEMS", ITEMS, (item_id,))
    V0900_NEW_ITEMS.append(item_id)
    return item_id


def _v0900_quest(qid, name, giver, kind, needed, description, *, target=None, target_npc=None,
                 requires=None, reward_silver=0, reward_items=None, required_soul_tier=0, extra=None):
    if qid in QUESTS:
        raise RuntimeError(f"v0.90.0 duplicate quest id: {qid}")
    payload = {
        "name": name, "giver": giver, "kind": kind, "needed": int(needed), "description": description,
        "reward_silver": int(reward_silver), "reward_gold": max(0, int(reward_silver) // 10000),
        "reward_mithril": 0, "reward_items": dict(reward_items or {}), "repeatable": False,
        "v0900_expansion": True,
    }
    if target is not None:
        payload["target"] = target
    if target_npc is not None:
        payload["target_npc"] = target_npc
    if requires:
        payload["requires_quest"] = requires
    if required_soul_tier:
        payload["required_soul_tier"] = int(required_soul_tier)
    if extra:
        payload.update(extra)
    catalog_assign(payload, "QUESTS", QUESTS, (qid,))
    V0900_NEW_QUESTS.append(qid)
    return qid


# ===========================================================================
# 1. KATAKUMBY POD PIWNICĄ - 3 x 24 pomieszczenia
# ===========================================================================
if "temple_basement_deep_nest" not in ROOMS:
    raise RuntimeError("v0.90.0 requires expanded Temple Basement v0.80.3")

CATACOMB_LEVELS_V0900 = {}
_cat_names = (
    ("Górne Katakumby", "Korytarz Górnych Katakumb", "Kamienne nisze są rozbite przez ogromne szczury i poruszone kości."),
    ("Katakumby Plugastwa", "Korytarz Plugastwa", "Ściany pokrywa czarna maź, a stare ossuaria pulsują skażeniem."),
    ("Gniazdo Pod Kośćmi", "Tunel Gniazda", "Tunele są wygryzione pod fundamentami. Kości, futro i świątynne płyty tworzą jedno olbrzymie siedlisko."),
)
for floor, (zone, room_name, desc) in enumerate(_cat_names, 1):
    rooms = _v0900_grid(f"catacomb_f{floor}", zone, 4, 6, room_name, desc, v0900_catacomb=True, v0900_floor=floor)
    CATACOMB_LEVELS_V0900[floor] = tuple(rooms)
    if floor == 1:
        direction = _v0900_first_free_direction("temple_basement_deep_nest", ("down",))
        _v0900_link("temple_basement_deep_nest", direction, rooms[0])
    else:
        _v0900_link(CATACOMB_LEVELS_V0900[floor - 1][-1], "down", rooms[0])

cat_rat = _v0900_mob("v0900_catacomb_rat", "Szczur Katakumbowy", 120, drops={"soul_shard": 0.08}, tags={"v0900_catacomb": True})
cat_bone = _v0900_mob("v0900_bone_thrall", "Kościany Niewolnik", 145, drops={"soul_shard": 0.10}, tags={"v0900_catacomb": True})
cat_abom = _v0900_mob("v0900_nest_abomination", "Plugastwo Gniazda", 170, magic=True, drops={"soul_shard": 0.14}, tags={"v0900_catacomb": True})
cat_miniboss1 = _v0900_mob("v0900_bone_eater", "Kościożerca", 195, boss=True, mechanic="bone_crush", mechanic_text="Co kilka tur miażdży kości silnym ciosem.", drops={"soul_shard": 1.0}, tags={"v0900_catacomb": True, "v0900_miniboss": True})
cat_miniboss2 = _v0900_mob("v0900_plague_matron", "Matrona Zarazy", 225, magic=True, boss=True, mechanic="blood_drain", mechanic_text="Wysysa siłę z przeciwników i odnawia własną żywotność.", drops={"soul_shard": 1.0}, tags={"v0900_catacomb": True, "v0900_miniboss": True})
cat_boss = _v0900_mob("v0900_nest_king", "Król Gniazda", 270, boss=True, mechanic="bone_rage", mechanic_text="Im dłużej trwa walka, tym brutalniejsze stają się jego szarże.", drops={"soul_shard": 1.0}, tags={"v0900_catacomb": True, "v0900_final_boss": True})

for floor, rooms in CATACOMB_LEVELS_V0900.items():
    pool = (cat_rat, cat_bone) if floor == 1 else ((cat_bone, cat_abom) if floor == 2 else (cat_rat, cat_bone, cat_abom))
    for idx, rid in enumerate(rooms):
        _v0900_spawn(rid, pool[idx % len(pool)], 2)
        _v0900_spawn(rid, pool[(idx + 1) % len(pool)], 1)
    _v0900_spawn(rooms[-1], cat_miniboss1 if floor == 1 else (cat_miniboss2 if floor == 2 else cat_boss), 1)

cat_relic = _v0900_item("v0900_nest_crown", "Korona Króla Gniazda", "Trofeum z najgłębszej komory katakumb. Stare srebro jest oplecione kością i czarnym futrem.", item_type="relic", defense=12, willpower=5)
cat_q1 = _v0900_quest("v0900_cat_01", "Katakumby: zejście pod gniazdo", "Badacz Kael", "kill", 20, "Pokonaj 20 Szczurów Katakumbowych w pierwszym poziomie katakumb.", target=cat_rat, reward_silver=12000)
cat_q2 = _v0900_quest("v0900_cat_02", "Katakumby: poruszone ossuarium", "Badacz Kael", "kill", 18, "Pokonaj 18 Kościanych Niewolników.", target=cat_bone, requires=cat_q1, reward_silver=18000)
cat_q3 = _v0900_quest("v0900_cat_03", "Katakumby: Kościożerca", "Badacz Kael", "kill", 1, "Pokonaj Kościożercę na końcu Górnych Katakumb.", target=cat_miniboss1, requires=cat_q2, reward_silver=26000)
cat_q4 = _v0900_quest("v0900_cat_04", "Katakumby: plugastwa", "Badacz Kael", "kill", 20, "Oczyść drugi poziom z 20 Plugastw Gniazda.", target=cat_abom, requires=cat_q3, reward_silver=34000)
cat_q5 = _v0900_quest("v0900_cat_05", "Katakumby: Matrona Zarazy", "Badacz Kael", "kill", 1, "Pokonaj Matronę Zarazy i otwórz drogę do najgłębszego gniazda.", target=cat_miniboss2, requires=cat_q4, reward_silver=44000)
cat_q6 = _v0900_quest("v0900_cat_06", "Katakumby: Król Gniazda", "Badacz Kael", "kill", 1, "Zejdź na trzeci poziom i pokonaj Króla Gniazda.", target=cat_boss, requires=cat_q5, reward_silver=70000, reward_items={cat_relic: 1, "soul_shard": 6})
_v0900_npc("v0900_researcher_kael", "Badacz Kael", "temple_basement_deep_nest", "Pod tym gniazdem są starsze katakumby. To, co obudziło szczury, poruszyło też kości zmarłych.", (cat_q1, cat_q2, cat_q3, cat_q4, cat_q5, cat_q6), v0900_catacomb=True)


# ===========================================================================
# 2. TRZY DUŻE LOCHY FABULARNE ARCHIPELAGU - po 40 pomieszczeń
# ===========================================================================
ARCHIPELAGO_DUNGEONS_V0900 = {}
ARCHIPELAGO_STORY_QUESTS_V0900 = []

_dungeon_specs = (
    {
        "key": "glass_depths", "zone": "Głębie Szklanej Rafy", "anchor_zone": "Wyspa Szklanych Raf",
        "title": "Głębie Szklanej Rafy", "stage": 720,
        "normal": (("v0900_glass_eel", "Szklany Węgorz", False), ("v0900_crystal_devourer", "Kryształowy Pożeracz", False), ("v0900_reef_oracle", "Wyrocznia Raf", True)),
        "minis": (("v0900_mirror_hydra", "Hydra Lustrzanych Głów", "crystal_lord", "Rozszczepia uderzenia przez kryształowe osłony."), ("v0900_reef_colossus", "Kolos Rafy", "iron_bones", "Co kilka tur twardnieje jego kryształowy pancerz.")),
        "boss": ("v0900_abyssal_pearl", "Władczyni Perłowej Otchłani", "abyss_queen", "Cyklicznie wysysa energię i wzmacnia ciśnienie otchłani."),
        "reward": ("v0900_pearl_core", "Rdzeń Perłowej Otchłani"),
    },
    {
        "key": "tempest_vault", "zone": "Skarbiec Wiecznej Burzy", "anchor_zone": "Wyspa Burzowej Korony",
        "title": "Skarbiec Wiecznej Burzy", "stage": 790,
        "normal": (("v0900_arc_wraith", "Widmo Łuku", True), ("v0900_thunder_guard", "Strażnik Gromu", False), ("v0900_storm_engine", "Żywy Silnik Burzy", True)),
        "minis": (("v0900_voltage_knight", "Rycerz Napięcia", "stellar_barrier", "Co kilka tur otacza się barierą energii."), ("v0900_cloud_reaver", "Rozpruwacz Chmur", "comet_evade", "Przeskakuje między wyładowaniami i unika części ataków.")),
        "boss": ("v0900_tempest_core", "Serce Wiecznej Burzy", "stellar_storm", "Co kilka tur rozpętuje gwiezdną burzę obejmującą pole walki."),
        "reward": ("v0900_storm_core", "Rdzeń Wiecznej Burzy"),
    },
    {
        "key": "star_prison", "zone": "Więzienie Pękniętej Gwiazdy", "anchor_zone": "Wyspa Serca Gwiazdy",
        "title": "Więzienie Pękniętej Gwiazdy", "stage": 880,
        "normal": (("v0900_void_jailer", "Dozorca Pustki", True), ("v0900_chain_construct", "Konstrukt Łańcuchów", False), ("v0900_star_prisoner", "Złamany Więzień Gwiazdy", True)),
        "minis": (("v0900_orbit_warden", "Strażnik Orbity", "orbital_echo", "Powtarza część ataków przez astralne echo."), ("v0900_constellation_beast", "Bestia Konstelacji", "constellation_burst", "Co kilka tur detonuje skupisko gwiezdnej energii.")),
        "boss": ("v0900_star_gaoler", "Naczelnik Gwiezdnego Więzienia", "astral_sovereign", "Zmienia rytm walki i wzmacnia się wraz z kolejnymi fazami."),
        "reward": ("v0900_prison_seal", "Pieczęć Gwiezdnego Więzienia"),
    },
)

_prev_story = STORY_QUEST_IDS_V0800[-1]
for dindex, spec in enumerate(_dungeon_specs, 1):
    rooms = _v0900_grid(spec["key"], spec["zone"], 5, 8, spec["title"], f"Rozległy loch fabularny: {spec['title']}. Każde skrzydło ma własny rytm zagrożeń.", v0900_archipelago_dungeon=True, v0900_dungeon_key=spec["key"])
    ARCHIPELAGO_DUNGEONS_V0900[spec["key"]] = tuple(rooms)
    anchors = tuple(V0800_ZONE_ROOM_IDS.get(spec["anchor_zone"], ()))
    if not anchors:
        raise RuntimeError(f"v0.90.0 missing archipelago anchor zone: {spec['anchor_zone']}")
    direction = _v0900_first_free_direction(anchors[-1], ("down", "south", "north"))
    _v0900_link(anchors[-1], direction, rooms[0])

    normals = []
    for mid, mname, magic in spec["normal"]:
        normals.append(_v0900_mob(mid, mname, spec["stage"], magic=magic, drops={"soul_shard": 0.65}, tags={"v0900_archipelago_dungeon": spec["key"]}))
    minis = []
    for mid, mname, mechanic, mtext in spec["minis"]:
        minis.append(_v0900_mob(mid, mname, spec["stage"] + 55, boss=True, mechanic=mechanic, mechanic_text=mtext, drops={"soul_shard": 1.0}, tags={"v0900_archipelago_dungeon": spec["key"], "v0900_miniboss": True}))
    bid, bname, bmechanic, btext = spec["boss"]
    boss = _v0900_mob(bid, bname, spec["stage"] + 120, magic=True, boss=True, mechanic=bmechanic, mechanic_text=btext, drops={"soul_shard": 1.0}, tags={"v0900_archipelago_dungeon": spec["key"], "v0900_final_boss": True})

    # Every room contains enemies. Minibosses divide the 40-room dungeon into three wings.
    for idx, rid in enumerate(rooms):
        _v0900_spawn(rid, normals[idx % len(normals)], 2)
        if idx % 3 == 0:
            _v0900_spawn(rid, normals[(idx + 1) % len(normals)], 1)
    _v0900_spawn(rooms[13], minis[0], 1)
    _v0900_spawn(rooms[27], minis[1], 1)
    _v0900_spawn(rooms[-1], boss, 1)
    catalog_set_path("ROOMS", ROOMS, (rooms[13], "v0900_mechanic"), "Pierwsza brama skrzydła: pokonaj minibossa, aby bezpiecznie przejść dalej.")
    catalog_set_path("ROOMS", ROOMS, (rooms[27], "v0900_mechanic"), "Druga brama skrzydła: drugi miniboss kontroluje dalszą część lochu.")
    catalog_set_path("ROOMS", ROOMS, (rooms[-1], "v0900_mechanic"), "Komnata finałowa: główny boss lochu posiada własną mechanikę walki.")

    reward_id, reward_name = spec["reward"]
    _v0900_item(reward_id, reward_name, f"Legendarny ślad ukończenia lochu {spec['title']}.", item_type="relic", defense=10 + dindex * 3, willpower=4 + dindex * 2)
    q1 = _v0900_quest(f"v0900_arch_{dindex}_1", f"{spec['title']}: otwarcie głębin", "Kapitan Seris", "kill", 24, f"Pokonaj 24 przeciwników pierwszego typu w lochu {spec['title']}.", target=normals[0], requires=_prev_story, reward_silver=90000 + dindex * 10000, required_soul_tier=10)
    q2 = _v0900_quest(f"v0900_arch_{dindex}_2", f"{spec['title']}: pierwsze skrzydło", "Kapitan Seris", "kill", 1, "Pokonaj pierwszego minibossa i przełam blokadę skrzydła.", target=minis[0], requires=q1, reward_silver=110000 + dindex * 12000)
    q3 = _v0900_quest(f"v0900_arch_{dindex}_3", f"{spec['title']}: drugie skrzydło", "Kapitan Seris", "kill", 1, "Pokonaj drugiego minibossa w dalszej części lochu.", target=minis[1], requires=q2, reward_silver=130000 + dindex * 14000)
    q4 = _v0900_quest(f"v0900_arch_{dindex}_4", f"{spec['title']}: finał", "Kapitan Seris", "kill", 1, f"Dotrzyj do końca 40-pokojowego lochu {spec['title']} i pokonaj głównego bossa.", target=boss, requires=q3, reward_silver=180000 + dindex * 20000, reward_items={reward_id: 1, "soul_shard": 8 + dindex * 2})
    ARCHIPELAGO_STORY_QUESTS_V0900.extend((q1, q2, q3, q4))
    _prev_story = q4

# Extend Captain Seris' story after the original 12-stage campaign.
_seris_chain = tuple(NPCS.get("v0800_captain_seris", {}).get("quest_chain", ()))
catalog_set_path("NPCS", NPCS, ("v0800_captain_seris", "quest_chain"), _seris_chain + tuple(ARCHIPELAGO_STORY_QUESTS_V0900))


# ===========================================================================
# 3. MIASTA 2.0 - wszystkie miasta kurierskie
# ===========================================================================
CITIES_2_CITIES_V0900 = {}
CITIES_2_QUESTS_V0900 = {}
_city_names = tuple(POSTAL_CITY_HUBS_V0522.keys())
for city_index, city in enumerate(_city_names, 1):
    slug = _v0900_slug(city)
    hub = GUIDE_CITY_HUBS_V0522.get(city) or POSTAL_CITY_HUBS_V0522[city]
    if hub not in ROOMS:
        raise RuntimeError(f"v0.90.0 city hub missing: {city} -> {hub}")

    room_specs = (
        ("council", "Ratusz", "Siedziba zarządu miasta, lokalnych kronik i spraw mieszkańców."),
        ("residential", "Dzielnica Mieszkalna", "Domy, zaułki i małe podwórza pokazują codzienne życie mieszkańców."),
        ("craft", "Dzielnica Warsztatowa", "Kuźnie, pracownie i składy tworzą głośne serce lokalnego rzemiosła."),
        ("shrine", "Lokalna Świątynia", "Miejsce pamięci i odpoczynku związane z historią miasta."),
        ("archive", "Archiwum Miejskie", "Rejestry, mapy i stare dokumenty opisują rozwój osady."),
        ("guard", "Strażnica", "Straż miejska zbiera meldunki o problemach na ulicach i pod ziemią."),
        ("under_gate", "Wejście do Podziemi", "Schody prowadzą pod fundamenty miasta, do tuneli starszych niż obecne mury."),
        ("undercity", "Podziemia Miejskie", "Stare kanały, fundamenty i opuszczone komory kryją lokalne zagrożenie."),
    )
    city_rooms = []
    for suffix, name, desc in room_specs:
        rid = _v0900_room(f"v0900_city_{slug}_{suffix}", city, f"{name} — {city}", desc, v0900_city2=True, v0900_city=city)
        city_rooms.append(rid)

    direction = _v0900_first_free_direction(hub, ("up", "northeast", "northwest", "southeast", "southwest", "down"))
    _v0900_link(hub, direction, city_rooms[0])
    _v0900_link(city_rooms[0], "east", city_rooms[1])
    _v0900_link(city_rooms[0], "west", city_rooms[2])
    _v0900_link(city_rooms[0], "north", city_rooms[3])
    _v0900_link(city_rooms[1], "north", city_rooms[4])
    _v0900_link(city_rooms[2], "north", city_rooms[5])
    _v0900_link(city_rooms[5], "down", city_rooms[6])
    _v0900_link(city_rooms[6], "east", city_rooms[7])
    CITIES_2_CITIES_V0900[city] = tuple(city_rooms)

    stage = 70 + city_index * 9
    threat_id = _v0900_mob(f"v0900_city_{slug}_threat", f"Podziemny Szkodnik — {city}", stage, drops={"soul_shard": 0.05}, tags={"v0900_city2": True, "v0900_city": city})
    for _ in range(6):
        _v0900_spawn(city_rooms[-1], threat_id, 1)
    for _ in range(3):
        _v0900_spawn(city_rooms[-2], threat_id, 1)

    chronicler = f"v0900_city_{slug}_chronicler"
    captain = f"v0900_city_{slug}_captain"
    q1 = f"v0900_city_{slug}_1"
    q2 = f"v0900_city_{slug}_2"
    q3 = f"v0900_city_{slug}_3"
    _v0900_npc(chronicler, f"Kronikarz — {city}", city_rooms[4], f"Zbieram dzieje {city}. Nowe dzielnice mają własne problemy i własną pamięć.", (q1,), v0900_city2=True, v0900_city=city)
    _v0900_npc(captain, f"Kapitan Straży — {city}", city_rooms[5], f"Pod {city} porusza się coś, czego nie ma na nowych planach miasta.", (q2, q3), v0900_city2=True, v0900_city=city)

    old_story = tuple(getattr(__import__('world.world_expansion_iii', fromlist=['CITY_STORY_QUESTS_BY_CITY_V0710']), 'CITY_STORY_QUESTS_BY_CITY_V0710', {}).get(city, ()))
    requires = old_story[-1] if old_story else None
    _v0900_quest(q1, f"{city} 2.0: zapomniane kroniki", f"Kronikarz — {city}", "talk_npc", 1, f"Porozmawiaj z Kapitanem Straży i poznaj problem nowych podziemi miasta {city}.", target_npc=captain, requires=requires, reward_silver=5000 + city_index * 300, extra={"reward_city_v0710": city, "reward_city_amount_v0710": 20, "v0900_city2": True})
    _v0900_quest(q2, f"{city} 2.0: zagrożenie pod fundamentami", f"Kapitan Straży — {city}", "kill", 8, f"Pokonaj 8 lokalnych zagrożeń w podziemiach miasta {city}.", target=threat_id, requires=q1, reward_silver=8000 + city_index * 500, extra={"reward_city_v0710": city, "reward_city_amount_v0710": 30, "v0900_city2": True})
    _v0900_quest(q3, f"{city} 2.0: bezpieczne ulice", f"Kapitan Straży — {city}", "kill", 16, f"Oczyść dalsze podziemia: pokonaj 16 kolejnych zagrożeń i zabezpiecz {city}.", target=threat_id, requires=q2, reward_silver=12000 + city_index * 700, reward_items={"soul_shard": 1}, extra={"reward_city_v0710": city, "reward_city_amount_v0710": 50, "v0900_city2": True})
    CITIES_2_QUESTS_V0900[city] = (q1, q2, q3)


# ===========================================================================
# HELP + exploration refresh + exported state
# ===========================================================================
HELP_TOPICS.setdefault("katakumby", []).extend([
    "Katakumby pod Piwnicą zaczynają się w Głębokim Gnieździe Piwnicy Świątyni.",
    "Mają 3 poziomy po 24 pomieszczenia: Górne Katakumby, Katakumby Plugastwa i Gniazdo Pod Kośćmi.",
    "Badacz Kael prowadzi sześcioczęściową linię zadań zakończoną bossem Król Gniazda.",
])
HELP_TOPICS.setdefault("lochy archipelagu", []).extend([
    "Po ukończeniu głównej kampanii Archipelagu Kapitan Seris prowadzi dalszą 12-etapową historię przez trzy wielkie lochy.",
    "Głębie Szklanej Rafy, Skarbiec Wiecznej Burzy i Więzienie Pękniętej Gwiazdy mają po 40 pomieszczeń.",
    "Każdy loch ma dwa minibossy dzielące skrzydła oraz jednego głównego bossa z własną mechaniką.",
])
HELP_TOPICS.setdefault("miasta 2.0", []).extend([
    f"Miasta 2.0 rozszerza wszystkie {len(_city_names)} miast sieci kurierskiej.",
    "Każde miasto dostaje Ratusz, Dzielnicę Mieszkalną, Dzielnicę Warsztatową, Świątynię, Archiwum, Strażnicę i dwupoziomowe podziemia.",
    "Kronikarz i Kapitan Straży prowadzą nową trzyetapową lokalną historię, kontynuując wcześniejsze miejskie questy v0.71.0.",
])
HELP_TOPIC_ALIASES.update({
    "katakumby pod piwnica": "katakumby", "katakumby pod piwnicą": "katakumby",
    "archipelag lochy": "lochy archipelagu", "duze lochy": "lochy archipelagu", "duże lochy": "lochy archipelagu",
    "miasta2": "miasta 2.0", "cities 2.0": "miasta 2.0", "miasta 2": "miasta 2.0",
})

v0130_refresh_exploration_catalog()

WORLD_EXPANSION_V_STATE = {
    "version": WORLD_EXPANSION_V_VERSION,
    "name": WORLD_EXPANSION_V_NAME,
    "new_rooms": len(set(V0900_NEW_ROOMS)),
    "new_mobs": len(set(V0900_NEW_MOBS)),
    "new_npcs": len(set(V0900_NEW_NPCS)),
    "new_quests": len(set(V0900_NEW_QUESTS)),
    "new_items": len(set(V0900_NEW_ITEMS)),
    "new_spawns": len(V0900_NEW_SPAWNS),
    "catacomb_levels": {k: tuple(v) for k, v in CATACOMB_LEVELS_V0900.items()},
    "archipelago_dungeons": {k: tuple(v) for k, v in ARCHIPELAGO_DUNGEONS_V0900.items()},
    "archipelago_story_quests": tuple(ARCHIPELAGO_STORY_QUESTS_V0900),
    "cities_2_count": len(CITIES_2_CITIES_V0900),
    "cities_2_rooms": {k: tuple(v) for k, v in CITIES_2_CITIES_V0900.items()},
    "cities_2_quests": {k: tuple(v) for k, v in CITIES_2_QUESTS_V0900.items()},
}

__all__ = [
    "WORLD_EXPANSION_V_VERSION", "WORLD_EXPANSION_V_NAME", "WORLD_EXPANSION_V_STATE",
    "CATACOMB_LEVELS_V0900", "ARCHIPELAGO_DUNGEONS_V0900", "ARCHIPELAGO_STORY_QUESTS_V0900",
    "CITIES_2_CITIES_V0900", "CITIES_2_QUESTS_V0900",
]

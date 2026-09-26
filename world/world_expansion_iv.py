# -*- coding: utf-8 -*-
"""Soulbound v0.80.0 - Archipelag Pękniętej Gwiazdy.

Duża ekspansja fabularna: nowy archipelag połączony z Gwiezdnym Portem,
pięć wysp/stref, nowe potwory i bossowie oraz liniowa kampania fabularna.
Moduł jest addytywny i korzysta z istniejących katalogów/questów/spawnów.
"""
from __future__ import annotations

from data.catalogs import ROOMS, NPCS, ITEMS, QUESTS, MOB_TEMPLATES
from data.catalog_mutations import catalog_assign, catalog_set_path
from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES, MOB_SPAWNS
from world.generation_systems import v0130_refresh_exploration_catalog

WORLD_EXPANSION_IV_VERSION = "0.80.0"
WORLD_EXPANSION_IV_NAME = "Archipelag Pękniętej Gwiazdy"
WORLD_EXPANSION_IV_REQUIRED_SOUL_TIER = 10

_OPPOSITE = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "northeast": "southwest", "southwest": "northeast",
    "northwest": "southeast", "southeast": "northwest",
    "up": "down", "down": "up",
}

_NEW_ROOMS = []
_NEW_MOBS = []
_NEW_NPCS = []
_NEW_QUESTS = []
_NEW_ITEMS = []
_NEW_SPAWNS = []
ZONE_ROOM_IDS = {}
ZONE_MOB_IDS = {}
ZONE_BOSS_IDS = {}


def _v0800_room(room_id, zone, name, desc):
    if room_id in ROOMS:
        raise RuntimeError(f"v0.80.0 duplicate room id: {room_id}")
    payload = {"zone": zone, "name": name, "desc": desc, "exits": {}, "v0800_archipelago": True}
    catalog_assign(payload, "ROOMS", ROOMS, (room_id,))
    _NEW_ROOMS.append(room_id)
    return room_id


def _v0800_link(a, direction, b, *, reverse=True):
    if a not in ROOMS or b not in ROOMS:
        raise RuntimeError(f"v0.80.0 missing room while linking {a} {direction} {b}")
    if direction not in _OPPOSITE:
        raise RuntimeError(f"v0.80.0 unsupported direction: {direction}")
    old = (ROOMS[a].get("exits") or {}).get(direction)
    if old not in (None, b):
        raise RuntimeError(f"v0.80.0 would overwrite exit {a}.{direction}: {old} -> {b}")
    catalog_set_path("ROOMS", ROOMS, (a, "exits", direction), b)
    if reverse:
        back = _OPPOSITE[direction]
        old_back = (ROOMS[b].get("exits") or {}).get(back)
        if old_back not in (None, a):
            raise RuntimeError(f"v0.80.0 would overwrite exit {b}.{back}: {old_back} -> {a}")
        catalog_set_path("ROOMS", ROOMS, (b, "exits", back), a)


def _v0800_zone(prefix, zone, specs):
    ids = []
    for index, (name, desc) in enumerate(specs, 1):
        rid = f"v0800_{prefix}_{index:02d}"
        _v0800_room(rid, zone, name, desc)
        ids.append(rid)
        if len(ids) > 1:
            _v0800_link(ids[-2], "east", ids[-1])
    # Compact loop with alternate route; avoids a single dead-end corridor.
    if len(ids) >= 6:
        _v0800_link(ids[0], "south", ids[3])
        _v0800_link(ids[2], "south", ids[5])
    ZONE_ROOM_IDS[zone] = tuple(ids)
    return ids


def _v0800_mob(mob_id, name, stage, *, magic=False, boss=False, drops=None, quest_target=None):
    if mob_id in MOB_TEMPLATES:
        raise RuntimeError(f"v0.80.0 duplicate mob id: {mob_id}")
    stage = int(stage)
    payload = {
        "name": name,
        "max_hp": 180 + stage * (20 if boss else 10),
        "damage": 18 + stage // (3 if boss else 5),
        "damage_type": "magic" if magic else "physical",
        "silver": 100 + stage * (8 if boss else 3),
        "gold": max(1, stage // (70 if boss else 160)),
        "mithril": 0,
        "stat_reward": max(100, stage // 2),
        "class_xp_reward": max(1200, stage * (32 if boss else 11)),
        "soul_reward": max(900, stage * (14 if boss else 5)),
        "drops": dict(drops or {}),
        "quest_target": quest_target or mob_id,
        "generator_level": stage,
        "v0800_archipelago": True,
    }
    if boss:
        payload.update({
            "rank": "boss", "boss": True,
            "quest_targets": tuple(dict.fromkeys((quest_target or mob_id, mob_id))),
            "corpse_equipment_guaranteed": 1,
        })
    catalog_assign(payload, "MOB_TEMPLATES", MOB_TEMPLATES, (mob_id,))
    _NEW_MOBS.append(mob_id)
    return mob_id


def _v0800_spawn(room_id, mob_id, count=1):
    if room_id not in ROOMS or mob_id not in MOB_TEMPLATES:
        raise RuntimeError(f"v0.80.0 invalid spawn {room_id}->{mob_id}")
    for _ in range(max(1, int(count))):
        row = (room_id, mob_id)
        MOB_SPAWNS.append(row)
        _NEW_SPAWNS.append(row)


def _v0800_npc(npc_id, name, room, dialogue, quest_ids=()):
    if npc_id in NPCS:
        raise RuntimeError(f"v0.80.0 duplicate NPC id: {npc_id}")
    qids = tuple(quest_ids)
    payload = {
        "name": name,
        "room": room,
        "dialogue": dialogue,
        "v0800_archipelago": True,
    }
    if qids:
        payload["quest"] = qids[0]
        payload["quest_chain"] = qids[1:]
    catalog_assign(payload, "NPCS", NPCS, (npc_id,))
    _NEW_NPCS.append(npc_id)
    return npc_id


def _v0800_item(item_id, payload):
    if item_id in ITEMS:
        raise RuntimeError(f"v0.80.0 duplicate item id: {item_id}")
    data = dict(payload)
    data["v0800_archipelago"] = True
    catalog_assign(data, "ITEMS", ITEMS, (item_id,))
    _NEW_ITEMS.append(item_id)
    return item_id


def _v0800_quest(qid, name, giver, kind, needed, description, *, target=None, target_npc=None,
           requires=None, reward_silver=0, reward_items=None, soul_tier=0):
    if qid in QUESTS:
        raise RuntimeError(f"v0.80.0 duplicate quest id: {qid}")
    payload = {
        "name": name,
        "giver": giver,
        "kind": kind,
        "needed": int(needed),
        "description": description,
        "reward_silver": int(reward_silver),
        "reward_gold": max(0, int(reward_silver) // 10000),
        "reward_mithril": 0,
        "reward_items": dict(reward_items or {}),
        "repeatable": False,
        "v0800_archipelago": True,
        "v0800_story": True,
    }
    if target is not None:
        payload["target"] = target
    if target_npc is not None:
        payload["target_npc"] = target_npc
    if requires:
        payload["requires_quest"] = requires
    if soul_tier:
        payload["required_soul_tier"] = int(soul_tier)
    catalog_assign(payload, "QUESTS", QUESTS, (qid,))
    _NEW_QUESTS.append(qid)
    return qid


# ---------------------------------------------------------------------------
# 1. WEJŚCIE Z GWIEZDNEGO PORTU I PRZYSTAŃ ARCHIPELAGU
# ---------------------------------------------------------------------------
if "star_port_market" not in ROOMS:
    raise RuntimeError("v0.80.0 requires Gwiezdny Port (star_port_market)")

_v0800_room("v0800_star_pier", "Gwiezdny Port", "Dalekomorskie Molo", "Długie molo wychodzi poza osłonięte wody portu. Przy końcu cumuje ekspedycyjny kuter płynący ku Pękniętej Gwieździe.")
_v0800_room("v0800_open_sea_01", "Morze Pękniętej Gwiazdy", "Szlak Dalekomorski", "Za rufą maleją światła Gwiezdnego Portu. Przed dziobem morze przecinają blade smugi gwiezdnego pyłu.")
_v0800_room("v0800_open_sea_02", "Morze Pękniętej Gwiazdy", "Pas Srebrnej Mgły", "Srebrna mgła tłumi fale i dźwięki. Kompas obraca się niespokojnie, wskazując kilka północy naraz.")
_v0800_room("v0800_open_sea_03", "Morze Pękniętej Gwiazdy", "Wody Rozbitego Nieba", "Nad wodą wiszą świetliste szczeliny, jakby nocne niebo pękło i odbijało się w falach.")
_v0800_room("v0800_harbor", WORLD_EXPANSION_IV_NAME, "Przystań Siedmiu Latarni", "Siedem wysokich latarni prowadzi statki między czarnymi skałami. To bezpieczny hub Archipelagu Pękniętej Gwiazdy.")
_v0800_room("v0800_harbor_square", WORLD_EXPANSION_IV_NAME, "Plac Siedmiu Latarni", "Plac łączy nabrzeże, dom ekspedycji, warsztat i ścieżki prowadzące ku pozostałym wyspom archipelagu.")
_v0800_room("v0800_expedition_house", WORLD_EXPANSION_IV_NAME, "Dom Ekspedycji", "Mapy pięciu wysp pokrywają ściany. Na centralnym stole leży szkic gwiazdy pękniętej na pięć odłamków.")
_v0800_room("v0800_archive", WORLD_EXPANSION_IV_NAME, "Archiwum Spadającej Gwiazdy", "Kamienne tablice opisują noc, gdy nad archipelagiem rozpadła się gwiazda i zmieniła morze, pogodę oraz mieszkańców wysp.")
_v0800_room("v0800_workshop", WORLD_EXPANSION_IV_NAME, "Warsztat Latarników", "Latarnicy naprawiają soczewki, kompasowe igły i metalowe osłony chroniące światło przed sztormami.")
_v0800_link("star_port_market", "west", "v0800_star_pier")
_v0800_link("v0800_star_pier", "west", "v0800_open_sea_01")
_v0800_link("v0800_open_sea_01", "west", "v0800_open_sea_02")
_v0800_link("v0800_open_sea_02", "west", "v0800_open_sea_03")
_v0800_link("v0800_open_sea_03", "west", "v0800_harbor")
_v0800_link("v0800_harbor", "north", "v0800_harbor_square")
_v0800_link("v0800_harbor_square", "north", "v0800_expedition_house")
_v0800_link("v0800_harbor_square", "east", "v0800_archive")
_v0800_link("v0800_harbor_square", "west", "v0800_workshop")


# ---------------------------------------------------------------------------
# 2. PIĘĆ STREF FABULARNYCH
# ---------------------------------------------------------------------------
reef = _v0800_zone("reef", "Wyspa Szklanych Raf", (
    ("Plaża Szklanego Piasku", "Przezroczyste ziarna piasku dzwonią pod stopami, a w płytkiej wodzie sterczą kryształowe rafy."),
    ("Ogród Raf", "Korale tworzą naturalny labirynt. Między nimi poruszają się drapieżniki o szklistych pancerzach."),
    ("Rozpadlina Pereł", "W szczelinach skał migoczą perły pokryte gwiezdnym nalotem."),
    ("Zalana Grota", "Przypływ zalewa połowę groty. Na ścianach widać ślady dawnej strażnicy latarników."),
    ("Kryształowa Laguna", "Woda jest idealnie nieruchoma, choć nad wyspą wieje wiatr."),
    ("Świątynia Pierwszego Odłamka", "Rozbita kopuła otacza pierwszy odłamek Pękniętej Gwiazdy."),
))
_v0800_link("v0800_harbor_square", "southeast", reef[0])

storm = _v0800_zone("storm", "Wyspa Burzowej Korony", (
    ("Brzeg Gromów", "Fale rozbijają się o bazalt, a elektryczne wyładowania biegną po mokrych skałach."),
    ("Kamienne Schody Burzy", "Wykute stopnie prowadzą ku grzbietowi wyspy między masztami dawnych piorunochronów."),
    ("Pole Złamanych Masztów", "Wraki statków zostały wbite w skałę przez huraganowe wiatry."),
    ("Taras Grzmotu", "Każdy krok odpowiada głuchym pomrukiem spod ziemi."),
    ("Korona Wichru", "Najwyższy punkt wyspy tonie w stałej burzy."),
    ("Sanktuarium Drugiego Odłamka", "Drugi gwiezdny fragment lewituje pomiędzy czterema przewodzącymi kolumnami."),
))
_v0800_link("v0800_harbor_square", "northeast", storm[0])

ash = _v0800_zone("ash", "Popielna Wyspa", (
    ("Czarny Brzeg", "Plaża jest zasypana ciepłym popiołem, który nie stygnie mimo morskiej bryzy."),
    ("Las Zwęglonych Palm", "Martwe palmy skrzypią bez ognia. Między pniami przesuwają się sylwetki korsarzy."),
    ("Port Spalonej Bandery", "Dawna piracka przystań została przejęta przez kult czczący spadające gwiazdy."),
    ("Kuźnia Popiołu", "Piec zbudowany wokół gwiezdnego meteorytu wciąż pracuje bez paliwa."),
    ("Fort Ostatniego Korsarza", "Kamienny fort kontroluje szlak na wulkaniczny szczyt."),
    ("Sanktuarium Trzeciego Odłamka", "Trzeci fragment gwiazdy tkwi w czarnej skale jak rozżarzony klin."),
))
_v0800_link("v0800_harbor_square", "northwest", ash[0])

night = _v0800_zone("night", "Wyspa Bezksiężycowej Nocy", (
    ("Brzeg Bez Świtu", "Nawet w dzień nad wyspą utrzymuje się głęboki granat nocy."),
    ("Las Cichych Gwiazd", "Liście odbijają obce konstelacje, których nie widać na prawdziwym niebie."),
    ("Studnia Cienia", "Kamienny szyb oddaje szepty z wielu głosów naraz."),
    ("Aleja Czarnych Posągów", "Posągi nie mają twarzy, ale wszystkie są zwrócone ku centrum wyspy."),
    ("Próg Otchłani", "Powietrze staje się ciężkie, a światło latarni przygasa do cienkiej obręczy."),
    ("Sanktuarium Czwartego Odłamka", "Czwarty fragment niemal nie świeci; pochłania blask otoczenia."),
))
_v0800_link("v0800_harbor", "southwest", night[0])

heart = _v0800_zone("heart", "Wyspa Serca Gwiazdy", (
    ("Biała Plaża", "Piasek świeci bladym światłem, a fale cofają się przed każdym krokiem ku wnętrzu wyspy."),
    ("Droga Pięciu Znaków", "W kamieniu wyryto symbole czterech odzyskanych odłamków i pusty znak w centrum."),
    ("Taras Spadających Świateł", "Nad tarasem powoli opadają iskry, które znikają przed dotknięciem ziemi."),
    ("Galeria Astralnych Wrót", "Pięć kamiennych wrót prowadzi donikąd, lecz ich powierzchnie drżą jak woda."),
    ("Przedsionek Pękniętej Gwiazdy", "W centrum wyspy bije puls światła. To źródło zakłóceń całego archipelagu."),
    ("Serce Pękniętej Gwiazdy", "Ostatni odłamek wisi nad kraterem. Wokół niego formuje się istota z gwiezdnego pyłu i ciemności."),
))
_v0800_link("v0800_harbor", "southeast", heart[0])


# ---------------------------------------------------------------------------
# 3. PRZEDMIOTY FABULARNE I NAGRODA KOŃCOWA
# ---------------------------------------------------------------------------
for item_id, name, desc in (
    ("v0800_shard_glass", "Odłamek Szklanej Gwiazdy", "Pierwszy stabilny fragment odnaleziony na Wyspie Szklanych Raf."),
    ("v0800_shard_storm", "Odłamek Burzowej Gwiazdy", "Fragment pulsujący ładunkiem Burzowej Korony."),
    ("v0800_shard_ash", "Odłamek Popielnej Gwiazdy", "Gorący odłamek wydobyty z czarnego sanktuarium Popielnej Wyspy."),
    ("v0800_shard_night", "Odłamek Gwiazdy Nocy", "Ciemny fragment pochłaniający część padającego na niego światła."),
):
    _v0800_item(item_id, {"name": name, "type": "quest", "price": None, "desc": desc})

_v0800_item("v0800_broken_star_compass", {
    "name": "Kompas Pękniętej Gwiazdy",
    "type": "armor", "slot": "relic", "defense": 15,
    "rarity": "legendary", "rarity_name": "Legendarny",
    "affix": "willpower", "affix_amount": 8,
    "price": None,
    "desc": "Legendarny relikt ukończenia kampanii Archipelagu Pękniętej Gwiazdy. Obrona +15, Siła Woli +8.",
})


# ---------------------------------------------------------------------------
# 4. MOBY, BOSSOWIE I SPAWNY
# ---------------------------------------------------------------------------
reef_v0800_mobs = (
    _v0800_mob("v0800_glass_stalker", "Szklany Tropiciel", 460, drops={"soul_shard": 0.35}),
    _v0800_mob("v0800_reef_singer", "Śpiewaczka Raf", 475, magic=True, drops={"soul_shard": 0.40}),
)
reef_boss = _v0800_mob("v0800_tidebreaker", "Łamacz Przypływu", 500, boss=True, drops={"soul_shard": 1.0, "v0800_shard_glass": 1.0})
ZONE_MOB_IDS["Wyspa Szklanych Raf"] = reef_v0800_mobs; ZONE_BOSS_IDS["Wyspa Szklanych Raf"] = reef_boss

storm_v0800_mobs = (
    _v0800_mob("v0800_storm_harrier", "Szturmowiec Burzy", 500, magic=True, drops={"soul_shard": 0.45}),
    _v0800_mob("v0800_thunder_roc", "Rok Gromu", 520, drops={"soul_shard": 0.45}),
)
storm_boss = _v0800_mob("v0800_tempest_queen", "Królowa Nawałnicy", 550, magic=True, boss=True, drops={"soul_shard": 1.0, "v0800_shard_storm": 1.0})
ZONE_MOB_IDS["Wyspa Burzowej Korony"] = storm_v0800_mobs; ZONE_BOSS_IDS["Wyspa Burzowej Korony"] = storm_boss

ash_v0800_mobs = (
    _v0800_mob("v0800_ash_corsair", "Popielny Korsarz", 540, drops={"soul_shard": 0.40}),
    _v0800_mob("v0800_cinder_cultist", "Kultysta Żaru", 555, magic=True, drops={"soul_shard": 0.45}),
)
ash_boss = _v0800_mob("v0800_ember_admiral", "Admirał Żarzącej Bandery", 590, boss=True, drops={"soul_shard": 1.0, "v0800_shard_ash": 1.0})
ZONE_MOB_IDS["Popielna Wyspa"] = ash_v0800_mobs; ZONE_BOSS_IDS["Popielna Wyspa"] = ash_boss

night_v0800_mobs = (
    _v0800_mob("v0800_voidling", "Pomniejsze Dziecko Pustki", 575, magic=True, drops={"soul_shard": 0.50}),
    _v0800_mob("v0800_night_sentinel", "Strażnik Bezksiężycowej Nocy", 595, drops={"soul_shard": 0.55}),
)
night_boss = _v0800_mob("v0800_eclipse_warden", "Strażnik Zaćmienia", 630, magic=True, boss=True, drops={"soul_shard": 1.0, "v0800_shard_night": 1.0})
ZONE_MOB_IDS["Wyspa Bezksiężycowej Nocy"] = night_v0800_mobs; ZONE_BOSS_IDS["Wyspa Bezksiężycowej Nocy"] = night_boss

heart_v0800_mobs = (
    _v0800_mob("v0800_astral_fragment", "Żywy Fragment Astralny", 620, magic=True, drops={"soul_shard": 0.60}),
    _v0800_mob("v0800_starbound_guard", "Strażnik Gwiezdnego Więzienia", 645, drops={"soul_shard": 0.65}),
)
heart_boss = _v0800_mob("v0800_broken_star_avatar", "Awatar Pękniętej Gwiazdy", 700, magic=True, boss=True, drops={"soul_shard": 1.0, "soul_elixir": 0.55})
ZONE_MOB_IDS["Wyspa Serca Gwiazdy"] = heart_v0800_mobs; ZONE_BOSS_IDS["Wyspa Serca Gwiazdy"] = heart_boss

for rooms, normals, boss in (
    (reef, reef_v0800_mobs, reef_boss), (storm, storm_v0800_mobs, storm_boss),
    (ash, ash_v0800_mobs, ash_boss), (night, night_v0800_mobs, night_boss),
    (heart, heart_v0800_mobs, heart_boss),
):
    for idx, rid in enumerate(rooms[:-1]):
        _v0800_spawn(rid, normals[idx % len(normals)], 1)
        if idx in (1, 4):
            _v0800_spawn(rid, normals[(idx + 1) % len(normals)], 1)
    _v0800_spawn(rooms[-1], boss, 1)


# ---------------------------------------------------------------------------
# 5. NPC I PEŁNA KAMPANIA FABULARNA (12 ETAPÓW)
# ---------------------------------------------------------------------------
_v0800_npc("v0800_captain_seris", "Kapitan Seris", "v0800_expedition_house",
     "Cztery odłamki gwiazdy podtrzymują pieczęć nad piątym. Jeśli pieczęć pęknie, cały archipelag zostanie wciągnięty w astralną szczelinę.")
_v0800_npc("v0800_archivist_lyra", "Archiwistka Lyra", "v0800_archive",
     "Kroniki mówią, że gwiazda nie spadła przypadkiem. Ktoś próbował otworzyć drogę pomiędzy światami.")
_v0800_npc("v0800_keeper_oren", "Latarnik Oren", "v0800_workshop",
     "Siedem latarni stabilizuje szlaki między wyspami. Bez odłamków ich światło nie wystarczy na długo.")
_v0800_npc("v0800_scout_ves", "Zwiadowczyni Ves", reef[0],
     "Szklane rafy rosną szybciej niż dawniej. Coś w świątyni przyciąga całe stada drapieżników.")
_v0800_npc("v0800_storm_scholar", "Badacz Burz Mael", storm[1],
     "Burza nie jest pogodą. To pole ochronne zasilane drugim odłamkiem gwiazdy.")
_v0800_npc("v0800_survivor_nara", "Ocalała Nara", ash[2],
     "Korsarze przestali rabować statki. Teraz karmią kuźnię gwiezdnym pyłem i czekają na znak z Serca Gwiazdy.")

STORY_QUEST_IDS_V0800 = []
_prev = None

def _v0800_story(*args, **kwargs):
    global _prev
    kwargs.setdefault("requires", _prev)
    qid = _v0800_quest(*args, **kwargs)
    STORY_QUEST_IDS_V0800.append(qid)
    _prev = qid
    return qid

_v0800_story(
    "v0800_story_01", "Pęknięta Gwiazda: wezwanie ekspedycji", "Kapitan Seris",
    "talk_npc", 1,
    "Porozmawiaj z Archiwistką Lyrą i poznaj historię Pękniętej Gwiazdy.",
    target_npc="v0800_archivist_lyra", reward_silver=18000,
    soul_tier=WORLD_EXPANSION_IV_REQUIRED_SOUL_TIER,
)
_v0800_story(
    "v0800_story_02", "Pęknięta Gwiazda: szklane drapieżniki", "Kapitan Seris",
    "kill", 8,
    "Oczyść Wyspę Szklanych Raf z ośmiu Szklanych Tropicieli.",
    target="v0800_glass_stalker", reward_silver=24000,
)
_v0800_story(
    "v0800_story_03", "Pęknięta Gwiazda: pierwszy odłamek", "Kapitan Seris",
    "kill", 1,
    "Pokonaj Łamacza Przypływu w Świątyni Pierwszego Odłamka.",
    target="v0800_tidebreaker", reward_silver=42000,
)
_v0800_story(
    "v0800_story_04", "Pęknięta Gwiazda: głos burzy", "Kapitan Seris",
    "talk_npc", 1,
    "Odszukaj Badacza Burz Maela na Wyspie Burzowej Korony.",
    target_npc="v0800_storm_scholar", reward_silver=22000,
)
_v0800_story(
    "v0800_story_05", "Pęknięta Gwiazda: korona gromów", "Kapitan Seris",
    "kill", 10,
    "Pokonaj dziesięciu Szturmowców Burzy, zanim dotrzesz do szczytu.",
    target="v0800_storm_harrier", reward_silver=32000,
)
_v0800_story(
    "v0800_story_06", "Pęknięta Gwiazda: królowa nawałnicy", "Kapitan Seris",
    "kill", 1,
    "Pokonaj Królową Nawałnicy i odzyskaj drugi odłamek.",
    target="v0800_tempest_queen", reward_silver=52000,
)
_v0800_story(
    "v0800_story_07", "Pęknięta Gwiazda: spalona bandera", "Kapitan Seris",
    "talk_npc", 1,
    "Znajdź Ocalałą Narę w Porcie Spalonej Bandery.",
    target_npc="v0800_survivor_nara", reward_silver=26000,
)
_v0800_story(
    "v0800_story_08", "Pęknięta Gwiazda: korsarze popiołu", "Kapitan Seris",
    "kill", 12,
    "Rozbij dwanaście Popielnych Korsarzy broniących drogi do sanktuarium.",
    target="v0800_ash_corsair", reward_silver=38000,
)
_v0800_story(
    "v0800_story_09", "Pęknięta Gwiazda: admirał żaru", "Kapitan Seris",
    "kill", 1,
    "Pokonaj Admirała Żarzącej Bandery i zabierz trzeci odłamek.",
    target="v0800_ember_admiral", reward_silver=62000,
)
_v0800_story(
    "v0800_story_10", "Pęknięta Gwiazda: noc bez księżyca", "Kapitan Seris",
    "kill", 12,
    "Pokonaj dwanaście pomniejszych Dzieci Pustki na Wyspie Bezksiężycowej Nocy.",
    target="v0800_voidling", reward_silver=48000,
)
_v0800_story(
    "v0800_story_11", "Pęknięta Gwiazda: strażnik zaćmienia", "Kapitan Seris",
    "kill", 1,
    "Pokonaj Strażnika Zaćmienia i odzyskaj czwarty odłamek.",
    target="v0800_eclipse_warden", reward_silver=76000,
)
_v0800_story(
    "v0800_story_12", "Pęknięta Gwiazda: serce archipelagu", "Kapitan Seris",
    "kill", 1,
    "Wejdź na Wyspę Serca Gwiazdy i pokonaj Awatara Pękniętej Gwiazdy.",
    target="v0800_broken_star_avatar", reward_silver=120000,
    reward_items={"v0800_broken_star_compass": 1, "soul_shard": 12},
)

# Kapitan prowadzi całą główną kampanię; pozostałe NPC są celami etapów fabularnych.
catalog_set_path("NPCS", NPCS, ("v0800_captain_seris", "quest"), STORY_QUEST_IDS_V0800[0])
catalog_set_path("NPCS", NPCS, ("v0800_captain_seris", "quest_chain"), tuple(STORY_QUEST_IDS_V0800[1:]))

# Dodatkowe, powtarzalne kontrakty po eksploracji archipelagu.
SIDE_QUEST_IDS_V0800 = []
for qid, name, target, needed, silver in (
    ("v0800_contract_reef", "Kontrakt: Szklane Rafy", "v0800_reef_singer", 14, 36000),
    ("v0800_contract_storm", "Kontrakt: Burzowa Korona", "v0800_thunder_roc", 14, 42000),
    ("v0800_contract_ash", "Kontrakt: Kult Żaru", "v0800_cinder_cultist", 16, 48000),
    ("v0800_contract_night", "Kontrakt: Strażnicy Nocy", "v0800_night_sentinel", 16, 56000),
    ("v0800_contract_heart", "Kontrakt: Astralne Fragmenty", "v0800_astral_fragment", 18, 68000),
):
    payload = {
        "name": name, "giver": "Latarnik Oren", "kind": "kill", "target": target,
        "needed": needed, "description": f"Pokonaj {needed} wskazanych przeciwników na Archipelagu Pękniętej Gwiazdy.",
        "reward_silver": silver, "reward_gold": max(0, silver // 10000), "reward_mithril": 0,
        "reward_items": {"soul_shard": 2}, "repeatable": True, "repeat_cooldown": 3600,
        "v0800_archipelago": True, "v0800_contract": True,
    }
    catalog_assign(payload, "QUESTS", QUESTS, (qid,))
    _NEW_QUESTS.append(qid); SIDE_QUEST_IDS_V0800.append(qid)
catalog_set_path("NPCS", NPCS, ("v0800_keeper_oren", "quest"), SIDE_QUEST_IDS_V0800[0])
catalog_set_path("NPCS", NPCS, ("v0800_keeper_oren", "quest_chain"), tuple(SIDE_QUEST_IDS_V0800[1:]))


HELP_TOPICS.setdefault("archipelag", []).extend([
    "Archipelag Pękniętej Gwiazdy zaczyna się przy Dalekomorskim Molo w Gwiezdnym Porcie.",
    "Główną 12-etapową kampanię prowadzi Kapitan Seris w Domu Ekspedycji. Pierwszy etap wymaga Soul Tier 10.",
    "Pięć stref: Wyspa Szklanych Raf, Wyspa Burzowej Korony, Popielna Wyspa, Wyspa Bezksiężycowej Nocy i Wyspa Serca Gwiazdy.",
    "Latarnik Oren w Warsztacie Latarników oferuje pięć odnawialnych kontraktów bojowych.",
    "Za ukończenie kampanii otrzymasz legendarny relikt Kompas Pękniętej Gwiazdy.",
])
HELP_TOPIC_ALIASES.update({
    "peknięta gwiazda": "archipelag",
    "peknieta gwiazda": "archipelag",
    "pęknięta gwiazda": "archipelag",
    "wyspy": "archipelag",
})

# Refresh global exploration catalogs after all rooms are present.
v0130_refresh_exploration_catalog()

WORLD_EXPANSION_IV_STATE = {
    "version": WORLD_EXPANSION_IV_VERSION,
    "name": WORLD_EXPANSION_IV_NAME,
    "required_soul_tier": WORLD_EXPANSION_IV_REQUIRED_SOUL_TIER,
    "room_count": len(set(_NEW_ROOMS)),
    "mob_template_count": len(set(_NEW_MOBS)),
    "npc_count": len(set(_NEW_NPCS)),
    "quest_count": len(set(_NEW_QUESTS)),
    "story_quest_count": len(STORY_QUEST_IDS_V0800),
    "side_quest_count": len(SIDE_QUEST_IDS_V0800),
    "item_count": len(set(_NEW_ITEMS)),
    "spawn_count": len(_NEW_SPAWNS),
    "zone_count": len(ZONE_ROOM_IDS),
    "room_ids": tuple(dict.fromkeys(_NEW_ROOMS)),
    "mob_ids": tuple(dict.fromkeys(_NEW_MOBS)),
    "npc_ids": tuple(dict.fromkeys(_NEW_NPCS)),
    "quest_ids": tuple(dict.fromkeys(_NEW_QUESTS)),
    "item_ids": tuple(dict.fromkeys(_NEW_ITEMS)),
    "story_quest_ids": tuple(STORY_QUEST_IDS_V0800),
    "side_quest_ids": tuple(SIDE_QUEST_IDS_V0800),
    "zone_rooms": {k: tuple(v) for k, v in ZONE_ROOM_IDS.items()},
    "zone_mobs": {k: tuple(v) for k, v in ZONE_MOB_IDS.items()},
    "zone_bosses": dict(ZONE_BOSS_IDS),
}

__all__ = [
    "WORLD_EXPANSION_IV_VERSION", "WORLD_EXPANSION_IV_NAME",
    "WORLD_EXPANSION_IV_REQUIRED_SOUL_TIER", "WORLD_EXPANSION_IV_STATE",
    "STORY_QUEST_IDS_V0800", "SIDE_QUEST_IDS_V0800",
]

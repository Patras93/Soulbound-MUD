# -*- coding: utf-8 -*-
"""Soulbound v1.00.0 - Ocean 2.0.

Adds player-facing ocean content while keeping Deep Sea Fishing inside the
existing Fishing profession 1-600.
"""
from __future__ import annotations

from data.catalogs import ROOMS, NPCS, ITEMS, MOB_TEMPLATES
from data.catalog_mutations import catalog_assign, catalog_set_path
from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES, MOB_SPAWNS
from core.progression_resources import (
    FISH_RESOURCE_IDS, FISH_ATLAS_ALL, FISHING_ROOMS, OCEAN_FISHING_ROOMS,
    MARINE_FISHING_ROOMS, OCEAN_FISH_ATLAS,
)
from systems.items_resources import FISH_STORAGE_IDS
from world.generation_systems import v0130_refresh_exploration_catalog

OCEAN_2_VERSION = "1.00.0"
OCEAN_2_NAME = "Ocean 2.0"

V1000_NEW_ROOMS = []
V1000_NEW_MOBS = []
V1000_NEW_NPCS = []
V1000_NEW_ITEMS = []
V1000_NEW_SPAWNS = []

_OPP = {
    "north":"south", "south":"north", "east":"west", "west":"east",
    "northeast":"southwest", "southwest":"northeast",
    "northwest":"southeast", "southeast":"northwest", "up":"down", "down":"up",
}
_DIRS = tuple(_OPP)


def v1000_room(room_id, zone, name, desc, **extra):
    if room_id in ROOMS:
        raise RuntimeError(f"v1.00.0 duplicate room {room_id}")
    row = {"zone": zone, "name": name, "desc": desc, "exits": {}, "v1000_ocean": True}
    row.update(extra)
    catalog_assign(row, "ROOMS", ROOMS, (room_id,))
    V1000_NEW_ROOMS.append(room_id)
    return room_id


def v1000_free(room_id, preferred=()):
    used = set((ROOMS.get(room_id, {}).get("exits") or {}).keys())
    for d in tuple(preferred) + _DIRS:
        if d not in used:
            return d
    raise RuntimeError(f"v1.00.0 no free exit from {room_id}")


def v1000_link(a, direction, b, reverse=True):
    if a not in ROOMS or b not in ROOMS:
        raise RuntimeError(f"v1.00.0 missing room while linking {a}->{b}")
    if direction not in _OPP:
        raise RuntimeError(f"v1.00.0 bad direction {direction}")
    old = (ROOMS[a].get("exits") or {}).get(direction)
    if old not in (None, b):
        raise RuntimeError(f"v1.00.0 exit collision {a}.{direction}: {old}->{b}")
    catalog_set_path("ROOMS", ROOMS, (a, "exits", direction), b)
    if reverse:
        back = _OPP[direction]
        old_back = (ROOMS[b].get("exits") or {}).get(back)
        if old_back not in (None, a):
            raise RuntimeError(f"v1.00.0 exit collision {b}.{back}: {old_back}->{a}")
        catalog_set_path("ROOMS", ROOMS, (b, "exits", back), a)


def v1000_item(item_id, name, desc, **extra):
    if item_id in ITEMS:
        raise RuntimeError(f"v1.00.0 duplicate item {item_id}")
    row = {"name": name, "type": "resource", "price": None, "desc": desc, "v1000_ocean": True}
    row.update(extra)
    catalog_assign(row, "ITEMS", ITEMS, (item_id,))
    V1000_NEW_ITEMS.append(item_id)
    return item_id


def v1000_mob(mob_id, name, stage, *, boss=False, magic=False, drops=None, mechanic=None):
    if mob_id in MOB_TEMPLATES:
        raise RuntimeError(f"v1.00.0 duplicate mob {mob_id}")
    stage = int(stage)
    row = {
        "name": name,
        "max_hp": 350 + stage * (28 if boss else 12),
        "damage": 30 + stage // (3 if boss else 6),
        "damage_type": "magic" if magic else "physical",
        "silver": 300 + stage * (15 if boss else 5),
        "gold": max(1, stage // (40 if boss else 120)),
        "mithril": 0,
        "stat_reward": max(120, stage // 2),
        "class_xp_reward": max(1800, stage * (42 if boss else 14)),
        "soul_reward": max(1200, stage * (20 if boss else 8)),
        "drops": dict(drops or {}),
        "v1000_ocean": True,
    }
    if boss:
        row.update({"rank":"boss", "boss":True, "quest_targets":(mob_id,), "corpse_equipment_guaranteed":1})
    if mechanic:
        row["boss_mechanic"] = mechanic
        row["boss_mechanic_text"] = mechanic
    catalog_assign(row, "MOB_TEMPLATES", MOB_TEMPLATES, (mob_id,))
    V1000_NEW_MOBS.append(mob_id)
    return mob_id


def v1000_spawn(room_id, mob_id, count=1):
    for _ in range(max(1, int(count))):
        row = (room_id, mob_id)
        MOB_SPAWNS.append(row)
        V1000_NEW_SPAWNS.append(row)


# ---------------------------------------------------------------------------
# Deep-ocean fish remain part of Fishing 1-600.
# ---------------------------------------------------------------------------
DEEP_OCEAN_FISH = {
    "v1000_blackfin_tuna": ("Czarnopłetwy Tuńczyk", 300, 420),
    "v1000_lantern_ray": ("Płaszczka Latarniowa", 340, 500),
    "v1000_abyss_swordfish": ("Miecznik Otchłani", 380, 650),
    "v1000_star_jellyfish": ("Gwiezdna Meduza", 420, 820),
    "v1000_void_shark": ("Rekin Pustki", 460, 1050),
    "v1000_crystal_whale": ("Kryształowy Wieloryb", 500, 1400),
    "v1000_leviathan_fry": ("Młody Lewiatan", 550, 1900),
    "v1000_eternal_coelacanth": ("Latimeria Wiecznego Rowu", 600, 3000),
}
for _iid, (_name, _level, _gold) in DEEP_OCEAN_FISH.items():
    v1000_item(
        _iid, _name,
        f"Gatunek dostępny wyłącznie na głębokim oceanie. Wędkarstwo/Wędka {_level}+.",
        sell_gold=_gold, min_tool_level=_level, generator_level=_level, deep_ocean=True, fish_habitat="ocean",
    )

_DEEP_IDS = set(DEEP_OCEAN_FISH)
FISH_RESOURCE_IDS.update(_DEEP_IDS)
FISH_ATLAS_ALL.update(_DEEP_IDS)
OCEAN_FISH_ATLAS.update(_DEEP_IDS)
FISH_STORAGE_IDS.update(_DEEP_IDS)

# Treasure / ocean reward items.
v1000_item("v1000_abyss_pearl", "Perła Otchłani", "Cenna perła z podwodnych ruin i map skarbów.", sell_gold=2200)
v1000_item("v1000_sunken_relic", "Zatopiony Relikt", "Relikt wydobyty z ruin pod oceanem.", sell_gold=4500)
v1000_item("v1000_navigator_seal", "Pieczęć Nawigatora", "Prestiżowa pieczęć za dalekomorskie odkrycia.", sell_gold=8000)

# ---------------------------------------------------------------------------
# Four real sea lanes. Route rooms are physically connected to the ports and
# require a player ship in movement.py.
# ---------------------------------------------------------------------------
PORTS = {
    "platform": ("ocean_platform", "Platforma Oceaniczna"),
    "fog": ("fog_square", "Port Mglistych Wysp"),
    "star": ("star_port_market", "Gwiezdny Port"),
    "broken": ("v0800_harbor", "Przystań Siedmiu Latarni"),
    "crown": ("silver_crown_harbor", "Wielki Port Srebrnej Korony"),
}

ROUTES = {}
DEEP_OCEAN_ROOMS = set()


def v1000_sea_lane(key, title, origin_key, destination_key, sectors, navigation_required, hull_required=1):
    origin = PORTS[origin_key][0]
    dest = PORTS[destination_key][0]
    ids = []
    for i in range(1, sectors + 1):
        rid = f"v1000_sea_{key}_{i:02d}"
        ids.append(v1000_room(
            rid, "Ocean 2.0", f"{title} — sektor {i}",
            "Otwarte morze otacza statek z każdej strony. Fale, wiatr i prądy wyznaczają prawdziwy szlak między portami.",
            requires_ship=True, ocean_navigation_required=navigation_required,
            ocean_hull_required=hull_required, deep_ocean_fishing=True,
            ocean_route=key, ocean_sector=i,
        ))
        DEEP_OCEAN_ROOMS.add(rid)
    for a, b in zip(ids, ids[1:]):
        v1000_link(a, "east", b)
    d1 = v1000_free(origin, ("east", "west", "north", "south", "northeast", "northwest", "southeast", "southwest"))
    v1000_link(origin, d1, ids[0])
    d2 = v1000_free(dest, ("west", "east", "south", "north", "southwest", "southeast", "northwest", "northeast"))
    v1000_link(dest, d2, ids[-1])
    ROUTES[key] = {
        "name": title, "origin": origin, "destination": dest, "rooms": tuple(ids),
        "navigation_required": navigation_required, "hull_required": hull_required,
        "origin_direction": d1, "destination_direction": d2,
    }
    return ids


route_reef = v1000_sea_lane("reef", "Szlak Wielkiej Rafy", "platform", "fog", 10, 1, 1)
route_mist = v1000_sea_lane("mist", "Szlak Mglistego Prądu", "fog", "star", 12, 2, 1)
route_shattered = v1000_sea_lane("shattered", "Szlak Pękniętej Gwiazdy", "star", "broken", 14, 3, 2)
route_crown = v1000_sea_lane("crown", "Szlak Srebrnej Korony", "platform", "crown", 16, 4, 3)

FISHING_ROOMS.update(DEEP_OCEAN_ROOMS)
OCEAN_FISHING_ROOMS.update(DEEP_OCEAN_ROOMS)
MARINE_FISHING_ROOMS.update(DEEP_OCEAN_ROOMS)

# ---------------------------------------------------------------------------
# Three submerged ruins, 30 rooms each, reachable from ocean sectors.
# ---------------------------------------------------------------------------
UNDERWATER_DUNGEONS = {}
TREASURE_ROOMS = []


def v1000_underwater_dungeon(key, title, anchor_room, stage, hull_required, boss_name):
    zone = f"Ocean 2.0 — {title}"
    rooms = []
    rows, cols = 5, 6
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            idx = r * cols + c + 1
            rid = f"v1000_ruin_{key}_{idx:02d}"
            row.append(v1000_room(
                rid, zone, f"{title} — komnata {idx}",
                "Zatopiona kamienna komnata drży pod naporem oceanu. Runy, koral i wraki tworzą rozgałęziony podwodny kompleks.",
                ocean_hull_required=hull_required, underwater=True,
                recommended_mastery=max(1, stage // 2),
            ))
            if idx % 7 == 0:
                TREASURE_ROOMS.append(rid)
        grid.append(row)
        rooms.extend(row)
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                v1000_link(grid[r][c], "east", grid[r][c+1])
            if r + 1 < rows:
                v1000_link(grid[r][c], "south", grid[r+1][c])
    v1000_link(anchor_room, "down", rooms[0])
    # A second return exit makes navigation friendlier under NVDA.
    catalog_set_path("ROOMS", ROOMS, (rooms[0], "exits", "up"), anchor_room)

    mob_a = v1000_mob(f"v1000_{key}_guardian", f"Strażnik {title}", stage)
    mob_b = v1000_mob(f"v1000_{key}_abomination", f"Głębinowe Plugastwo {title}", stage + 20, magic=True)
    boss = v1000_mob(f"v1000_{key}_boss", boss_name, stage + 60, boss=True, magic=True,
                drops={"v1000_abyss_pearl": 1.0, "v1000_sunken_relic": 0.35},
                mechanic=f"Mechanika {boss_name}: fale ciśnienia i zalewające komnaty.")
    for i, rid in enumerate(rooms):
        v1000_spawn(rid, mob_a if i % 3 else mob_b, 2 if i % 5 else 3)
    v1000_spawn(rooms[-1], boss, 1)
    UNDERWATER_DUNGEONS[key] = {"name": title, "rooms": tuple(rooms), "boss": boss, "anchor": anchor_room}


v1000_underwater_dungeon("reef", "Ruiny Koralowego Tronu", route_reef[5], 320, 1, "Król Koralowych Głębin")
v1000_underwater_dungeon("storm", "Świątynia Zatopionej Burzy", route_shattered[7], 440, 2, "Kapłan Wiecznego Sztormu")
v1000_underwater_dungeon("abyss", "Miasto Czarnego Rowu", route_crown[10], 560, 3, "Strażnik Czarnego Rowu")

# Ocean NPCs in major ports.
catalog_assign({
    "name":"Mistrzyni Nawigacji Lyria", "room":"ocean_platform",
    "dialogue":"Pomagam kupować i ulepszać statki. Wpisz statek oraz zegluj.",
    "v1000_ocean":True,
}, "NPCS", NPCS, ("v1000_navigator_lyria",))
V1000_NEW_NPCS.append("v1000_navigator_lyria")
catalog_assign({
    "name":"Kupiec Dalekomorski Orven", "room":"star_port_market",
    "dialogue":"Prowadzę kontrakty handlu morskiego. Wpisz handel morski.",
    "v1000_ocean":True,
}, "NPCS", NPCS, ("v1000_ocean_merchant_orven",))
V1000_NEW_NPCS.append("v1000_ocean_merchant_orven")

# Help.
HELP_TOPICS["ocean"] = [
    "OCEAN 2.0: statki graczy, realne szlaki morskie, mapy skarbów, handel morski, podwodne ruiny i głębinowe Wędkarstwo.",
    "statek - stan statku; statek kup; statek ulepsz kadlub|zagle|ladownia|nawigacja.",
    "zegluj - lista tras i wymagania. Szlaki są prawdziwymi pokojami świata; po wejściu używaj ex i kierunków.",
    "skarby - aktywna mapa; skarby szukaj - wykop skarb w poprawnym sektorze.",
    "handel morski - oferty; handel morski wez <nr>; handel morski oddaj.",
    "Połów głębinowy NIE jest osobną profesją. Na głębokich sektorach używaj zwykłej komendy fish/lów; rozwija Wędkarstwo i Wędkę 1-600.",
]
HELP_TOPIC_ALIASES.update({"ocean2":"ocean", "zegluga":"ocean", "żegluga":"ocean", "statek":"ocean", "handel morski":"ocean"})
if "profesje" in HELP_TOPICS:
    HELP_TOPICS["profesje"].append(
        "Ocean 2.0 porządkuje listę: ZBIERACTWO to Wędkarstwo, Górnictwo, Drwalstwo i Zielarstwo; RZEMIOSŁA to Gotowanie, Alchemia, Kowalstwo, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo i Zaklinanie."
    )
    HELP_TOPICS["profesje"].append(
        "Użyj profesje zbieractwo albo profesje rzemiosla, aby pokazać tylko wybraną grupę. Połów głębinowy pozostaje częścią Wędkarstwa 1-600."
    )

HELP_TOPICS["profesje podzial"] = [
    "ZBIERACTWO: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo.",
    "RZEMIOSŁA: Gotowanie, Alchemia, Kowalstwo, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo, Zaklinanie.",
    "Wszystkie profesje mają progresję 1-600. Połów głębinowy pozostaje częścią Wędkarstwa.",
]
HELP_TOPIC_ALIASES.update({"zbieractwo":"profesje podzial", "rzemiosla":"profesje podzial", "rzemiosła":"profesje podzial"})

v0130_refresh_exploration_catalog()

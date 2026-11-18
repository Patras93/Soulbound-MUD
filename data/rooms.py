# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
from data.catalog_parts.rooms_01 import build_catalog as _rooms_part_01
from data.catalog_parts.rooms_02 import build_catalog as _rooms_part_02
from data.catalog_parts.rooms_03 import build_catalog as _rooms_part_03
from data.catalog_parts.rooms_04 import build_catalog as _rooms_part_04

ROOMS = {}
ROOMS.update(_rooms_part_01())
ROOMS.update(_rooms_part_02())
ROOMS.update(_rooms_part_03())
ROOMS.update(_rooms_part_04())

# v115: additional separate world catalog; legacy room definitions untouched.
from systems.v115.playable_regions import build_rooms as _v115_rooms
if set(ROOMS).intersection(_v115_rooms()):
    raise ValueError('v115: kolizja ID lokacji')
ROOMS.update(_v115_rooms())
# v115: permit only real resource sectors in existing tool/profession commands.
# Keep the historical native fishing methods/source contracts unchanged.
from systems.v115.profession_sites import register_authored_sites as _v115_register_sites
_v115_register_sites(ROOMS)
if 'up' in ROOMS['crossroads']['exits']:
    raise ValueError('v115: wyjście góra na Rozdrożu zajęte; nie nadpisuję starej drogi')
ROOMS['crossroads']['exits']['up'] = 'v115_horyzonty_wezel'

# v115: real connected dungeons, built only after every exterior anchor exists.
from systems.v115.regional_dungeons import install_rooms as _v115_install_dungeons
_v115_install_dungeons(ROOMS)

# v115: prawdziwe wejście graveyard; bez zastępowania krypt i starych przejść.
from systems.v115.graveyard_expansion import build_rooms as _v115_graveyard_rooms, room_id as _v115_graveyard_id
ROOMS.update(_v115_graveyard_rooms(ROOMS))
ROOMS['graveyard']['exits']['up'] = _v115_graveyard_id(0, 0)


# v2.00.6: region-based world balance.  Only authored starter continent
# rooms are given stages here.  All later realms, procedurally generated
# regions, dungeons, world bosses and zones with explicit metadata retain
# their own stage and their full difficulty scaling.
_V2006_STARTER_REGION_LEVELS = {
    "Miasto Dusz": (1, "bezpieczne"),
    "Gildia Dusz": (1, "bezpieczne"),
    "Łąki": (5, "poczatkujace"),
    "Dzicz": (12, "poczatkujace"),
    "Wybrzeże": (16, "poczatkujace"),
    "Jaskinie Goblinów": (21, "rozwijajace"),
    "Obozowiska Bandytów": (22, "rozwijajace"),
    "Ruiny Strażnicy": (25, "rozwijajace"),
}
_V2006_ROOM_LEVELS = {
    # Accessible exterior progression, not an invisible global boost.
    "training": 1, "goblin_camp": 16, "ruined_watchtower": 20,
    "goblin_cave_mouth": 18, "goblin_fungus_gallery": 20,
    "goblin_scrap_tunnels": 23, "goblin_shaman_hollow": 26,
    "goblin_bomb_workshop": 27, "goblin_guard_post": 28,
    "goblin_war_den": 31, "goblin_treasure_burrow": 35,
    "goblin_throne_cave": 40,
    "bandit_camp": 17, "bandit_outer_ring": 19,
    "bandit_supply_tents": 20, "bandit_training_yard": 21,
    "bandit_barricade": 24, "bandit_loot_depot": 26,
    "bandit_arena": 29, "bandit_inner_camp": 32,
    "bandit_command_tent": 40,
}
for _v2006_rid, _v2006_room in ROOMS.items():
    _v2006_profile = _V2006_STARTER_REGION_LEVELS.get(_v2006_room.get("zone"))
    if not _v2006_profile:
        continue
    # Respect already-authored stage; don't alter high-level/instanced rooms.
    if "generator_level" in _v2006_room or "recommended_mastery" in _v2006_room:
        continue
    _v2006_room["generator_level"] = _V2006_ROOM_LEVELS.get(_v2006_rid, _v2006_profile[0])
    _v2006_room["region_difficulty_v2006"] = _v2006_profile[1]
    _v2006_room["region_stage_v2006"] = _v2006_room["generator_level"]

del _v2006_rid, _v2006_room, _v2006_profile

__all__ = ['ROOMS']

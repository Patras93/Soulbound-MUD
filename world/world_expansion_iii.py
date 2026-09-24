# -*- coding: utf-8 -*-
"""Soulbound v0.70.0 - Courier & Profession Expansion: new settlements.

Adds twelve real, connected settlements to the existing world and wires each
one into the Courier/Guide network.  The module is additive: no existing exit,
room or courier destination is replaced.
"""
from __future__ import annotations

import re
import unicodedata

from data.catalogs import ROOMS, NPCS, ITEMS, QUESTS
from data.catalog_mutations import catalog_assign, catalog_set_path
from config.postal import (
    POSTAL_CITY_HUBS_V0522,
    GUIDE_CITY_HUBS_V0522,
    COURIER_CITY_ROOM_TO_NAME_V0530,
    COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550,
)

WORLD_EXPANSION_III_VERSION = "0.71.0"

_OPPOSITE = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "northeast": "southwest", "southwest": "northeast",
    "northwest": "southeast", "southeast": "northwest",
    "up": "down", "down": "up",
}

# city, prefix, anchor, outward direction, flavour
WORLD_EXPANSION_III_SETTLEMENTS = (
    ("Bursztynowa Przystań", "amber_haven", "birch_north_gate", "east", "osada kupców bursztynu i drwali przy spokojnym trakcie"),
    ("Miedziany Gród", "copper_hold", "iron_east_gate", "north", "rzemieślniczy gród hutników, kowali i górników"),
    ("Popielny Jar", "cinder_vale", "ash_south_gate", "east", "forteczna osada zaopatrująca wyprawy na popielne rubieże"),
    ("Gwiezdny Port", "star_port", "fog_dock", "north", "port dalekomorskich kartografów i nocnych żeglarzy"),
    ("Dolina Wierzb", "willow_vale", "silver_crown_west_gate", "south", "zielona osada sadowników, zielarzy i drwali"),
    ("Szafirowe Wzgórza", "sapphire_hills", "silver_crown_north_gate", "east", "górskie miasto kamieniarzy i poszukiwaczy klejnotów"),
    ("Księżycowa Zatoka", "moon_bay", "silver_crown_east_gate", "north", "nadmorska osada rybaków i alchemików"),
    ("Smoczy Trakt", "dragon_road", "silver_crown_south_gate", "south", "karawanowe miasto na drodze ku najdalszym ziemiom Ardelii"),
    ("Jeziorna Straż", "lake_watch", "green_shore_west_gate", "north", "warowna przystań nad jeziorami i mokradłami"),
    ("Runiczna Brama", "rune_gate", "stone_watch_west_gate", "north", "kamienna osada badaczy run i dawnych ruin"),
    ("Biała Przystań", "white_haven", "quiet_haven_marsh_gate", "east", "jasna przystań na granicy mokradeł i wybrzeża"),
    ("Wieczny Most", "eternal_bridge", "quiet_haven_desert_gate", "east", "miasto karawan zbudowane wokół starego kamiennego mostu"),
)

WORLD_EXPANSION_III_CITIES = {city: f"{prefix}_post" for city, prefix, *_ in WORLD_EXPANSION_III_SETTLEMENTS}
WORLD_EXPANSION_III_GUIDE_HUBS = {city: f"{prefix}_square" for city, prefix, *_ in WORLD_EXPANSION_III_SETTLEMENTS}
WORLD_EXPANSION_III_NEW_ROOMS = []
WORLD_EXPANSION_III_NEW_NPCS = []


def _v0700_room(room_id, zone, name, desc):
    if room_id in ROOMS:
        raise RuntimeError(f"v0.70.0 duplicate room id: {room_id}")
    payload = {"zone": zone, "name": name, "desc": desc, "exits": {}}
    catalog_assign(payload, "ROOMS", ROOMS, (room_id,))
    WORLD_EXPANSION_III_NEW_ROOMS.append(room_id)


def _v0700_link(a, direction, b, reverse=True):
    if a not in ROOMS or b not in ROOMS:
        raise RuntimeError(f"v0.70.0 missing room while linking {a} {direction} {b}")
    if direction not in _OPPOSITE:
        raise RuntimeError(f"v0.70.0 unsupported direction: {direction}")
    existing = (ROOMS[a].get("exits") or {}).get(direction)
    if existing not in (None, b):
        raise RuntimeError(f"v0.70.0 would overwrite exit {a}.{direction}: {existing} -> {b}")
    catalog_set_path("ROOMS", ROOMS, (a, "exits", direction), b)
    if reverse:
        back = _OPPOSITE[direction]
        existing_back = (ROOMS[b].get("exits") or {}).get(back)
        if existing_back not in (None, a):
            raise RuntimeError(f"v0.70.0 would overwrite exit {b}.{back}: {existing_back} -> {a}")
        catalog_set_path("ROOMS", ROOMS, (b, "exits", back), a)


def _v0700_npc(npc_id, name, room, dialogue, role):
    if npc_id in NPCS:
        raise RuntimeError(f"v0.70.0 duplicate NPC id: {npc_id}")
    payload = {
        "name": name,
        "room": room,
        "dialogue": dialogue,
        "v0700_world_expansion": True,
        "v0700_role": role,
    }
    catalog_assign(payload, "NPCS", NPCS, (npc_id,))
    WORLD_EXPANSION_III_NEW_NPCS.append(npc_id)


def _achievement_slug(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("ł", "l")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


for index, (city, prefix, anchor, direction, flavour) in enumerate(WORLD_EXPANSION_III_SETTLEMENTS, 1):
    if anchor not in ROOMS:
        raise RuntimeError(f"v0.70.0 settlement anchor missing: {anchor}")

    approach = f"{prefix}_approach"
    gate = f"{prefix}_gate"
    square = f"{prefix}_square"
    post = f"{prefix}_post"
    inn = f"{prefix}_inn"
    market = f"{prefix}_market"

    _v0700_room(approach, city, f"Trakt do {city}", f"Boczny trakt prowadzi do {city}; to {flavour}.")
    _v0700_room(gate, city, f"Brama — {city}", f"Brama i drogowskazy oznaczają wejście do osady {city}.")
    _v0700_room(square, city, f"Plac — {city}", f"Główny plac {city}. Mieszkańcy, kupcy i podróżni spotykają się tu przed dalszą drogą.")
    _v0700_room(post, city, f"Poczta — {city}", f"Punkt Gildii Kurierów obsługuje paczki przychodzące i wychodzące z {city}.")
    _v0700_room(inn, city, f"Karczma — {city}", f"Lokalna karczma daje podróżnym odpoczynek, informacje i godzinne zlecenia.")
    _v0700_room(market, city, f"Targ — {city}", f"Niewielki targ skupia lokalnych rzemieślników oraz towary przywożone przez kurierów.")

    _v0700_link(anchor, direction, approach)
    _v0700_link(approach, direction, gate)
    _v0700_link(gate, direction, square)
    entry_back = _OPPOSITE[direction]
    internal_dirs = [d for d in ("north", "east", "south", "west") if d != entry_back]
    _v0700_link(square, internal_dirs[0], post)
    _v0700_link(square, internal_dirs[1], inn)
    _v0700_link(square, internal_dirs[2], market)

    postmaster_names = (
        "Mira", "Darek", "Selma", "Aris", "Lena", "Toren",
        "Neris", "Radan", "Eira", "Korin", "Vela", "Odran",
    )
    innkeeper_names = (
        "Iria", "Bram", "Talia", "Nolan", "Sena", "Marek",
        "Liora", "Edric", "Anja", "Soren", "Mila", "Haren",
    )
    _v0700_npc(
        f"{prefix}_postmaster", f"Poczmistrz {postmaster_names[index-1]}", post,
        f"Prowadzę pocztę w {city}. Listę tras sprawdzisz komendą poczta lista; wszystkie dostawy są bez losowego ryzyka.",
        "postmaster",
    )
    _v0700_npc(
        f"{prefix}_innkeeper", f"Karczmarz {innkeeper_names[index-1]}", inn,
        f"Witaj w {city}. Podróżni przynoszą tu wieści z traktów, profesji i dalekich miast.",
        "innkeeper",
    )

    POSTAL_CITY_HUBS_V0522[city] = post
    GUIDE_CITY_HUBS_V0522[city] = square
    COURIER_CITY_ROOM_TO_NAME_V0530[square] = city
    COURIER_CITY_ROOM_TO_NAME_V0530[post] = city
    COURIER_CITY_ROOM_TO_NAME_V0530[inn] = city
    COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550[city] = (
        f"courier_city_v0700_{_achievement_slug(city)}_100",
        f"Kurier: 100 dostaw do {city}",
        "Gold",
    )

WORLD_EXPANSION_III_METRICS = {
    "version": WORLD_EXPANSION_III_VERSION,
    "settlement_count": len(WORLD_EXPANSION_III_SETTLEMENTS),
    "new_room_count": len(WORLD_EXPANSION_III_NEW_ROOMS),
    "new_npc_count": len(WORLD_EXPANSION_III_NEW_NPCS),
    "courier_city_total": len(POSTAL_CITY_HUBS_V0522),
}


# v0.71.0 - lokalne historie wszystkich miast i osad kurierskich.
# Każde miasto dostaje własnego zarządcę, łącznika pocztowego i starszego
# rzemieślnika oraz trzy jednorazowe etapy wprowadzające do lokalnej historii.
CITY_STORY_QUEST_IDS_V0710 = []
CITY_STORY_QUESTS_BY_CITY_V0710 = {}
CITY_STORY_NPC_IDS_V0710 = []
CITY_STORY_ITEM_IDS_V0710 = []

for city_index, city in enumerate(tuple(POSTAL_CITY_HUBS_V0522.keys()), 1):
    slug = _achievement_slug(city)
    guide_room = GUIDE_CITY_HUBS_V0522[city]
    postal_room = POSTAL_CITY_HUBS_V0522[city]
    if guide_room not in ROOMS or postal_room not in ROOMS:
        raise RuntimeError(f"v0.71.0 city story hub missing for {city}")

    steward_id = f"city_steward_{slug}_v0710"
    liaison_id = f"city_liaison_{slug}_v0710"
    artisan_id = f"city_artisan_{slug}_v0710"
    for npc_id, payload in (
        (steward_id, {
            "name": f"Zarządca Miejski — {city}",
            "room": guide_room,
            "dialogue": f"Dbam o sprawy mieszkańców {city}. Mam dla ciebie lokalną linię zadań i będę śledzić twoją reputację w tym mieście.",
            "v0710_city_story": True,
            "v0710_city": city,
        }),
        (liaison_id, {
            "name": f"Łącznik Poczty — {city}",
            "room": postal_room,
            "dialogue": f"Koordynuję lokalne przesyłki i sprawy pocztowe miasta {city}.",
            "v0710_city_story": True,
            "v0710_city": city,
        }),
        (artisan_id, {
            "name": f"Starszy Rzemieślnik — {city}",
            "room": guide_room,
            "dialogue": f"Reprezentuję warsztaty i profesje miasta {city}. Zarządca często kieruje do mnie nowych pomocników.",
            "v0710_city_story": True,
            "v0710_city": city,
        }),
    ):
        if npc_id in NPCS:
            raise RuntimeError(f"v0.71.0 duplicate city story NPC id: {npc_id}")
        catalog_assign(payload, "NPCS", NPCS, (npc_id,))
        CITY_STORY_NPC_IDS_V0710.append(npc_id)

    parcel_id = f"city_civic_packet_{slug}_v0710"
    if parcel_id in ITEMS:
        raise RuntimeError(f"v0.71.0 duplicate city story item id: {parcel_id}")
    catalog_assign({
        "name": f"Pakiet spraw miejskich — {city}",
        "type": "quest",
        "price": None,
        "desc": f"Zapieczętowany pakiet dokumentów lokalnych miasta {city}.",
        "v0710_city_story": True,
    }, "ITEMS", ITEMS, (parcel_id,))
    CITY_STORY_ITEM_IDS_V0710.append(parcel_id)

    q1 = f"v0710_city_{slug}_1"
    q2 = f"v0710_city_{slug}_2"
    q3 = f"v0710_city_{slug}_3"
    quests = (
        (q1, {
            "name": f"{city}: Poznaj lokalne sprawy",
            "giver": f"Zarządca Miejski — {city}",
            "kind": "talk_npc",
            "target_npc": liaison_id,
            "needed": 1,
            "description": f"Porozmawiaj z Łącznikiem Poczty w mieście {city}, aby poznać najważniejsze lokalne szlaki i potrzeby.",
            "reward_silver": 1500, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
            "reward_city_v0710": city, "reward_city_amount_v0710": 10,
            "repeatable": False, "v0710_city_story": True,
        }),
        (q2, {
            "name": f"{city}: Głos warsztatów",
            "giver": f"Zarządca Miejski — {city}",
            "kind": "talk_npc",
            "target_npc": artisan_id,
            "needed": 1,
            "description": f"Porozmawiaj ze Starszym Rzemieślnikiem w mieście {city} i poznaj potrzeby lokalnych profesji.",
            "requires_quest": q1,
            "reward_silver": 2000, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
            "reward_city_v0710": city, "reward_city_amount_v0710": 15,
            "repeatable": False, "v0710_city_story": True,
        }),
        (q3, {
            "name": f"{city}: Pieczęć zaufania",
            "giver": f"Zarządca Miejski — {city}",
            "kind": "deliver_npc",
            "target_npc": liaison_id,
            "quest_item": parcel_id,
            "accept_items": {parcel_id: 1},
            "needed": 1,
            "description": f"Dostarcz Pakiet spraw miejskich do Łącznika Poczty w mieście {city}. To ostatni etap lokalnego wprowadzenia.",
            "requires_quest": q2,
            "reward_silver": 3000, "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
            "reward_city_v0710": city, "reward_city_amount_v0710": 25,
            "repeatable": False, "v0710_city_story": True,
        }),
    )
    for quest_id, quest in quests:
        if quest_id in QUESTS:
            raise RuntimeError(f"v0.71.0 duplicate city quest id: {quest_id}")
        catalog_assign(quest, "QUESTS", QUESTS, (quest_id,))
        CITY_STORY_QUEST_IDS_V0710.append(quest_id)
    catalog_assign((q1, q2, q3), "NPCS", NPCS, (steward_id, "specialist_quests"))
    CITY_STORY_QUESTS_BY_CITY_V0710[city] = (q1, q2, q3)

CITY_STORY_METRICS_V0710 = {
    "version": "0.71.0",
    "city_count": len(CITY_STORY_QUESTS_BY_CITY_V0710),
    "quest_count": len(CITY_STORY_QUEST_IDS_V0710),
    "npc_count": len(CITY_STORY_NPC_IDS_V0710),
    "item_count": len(CITY_STORY_ITEM_IDS_V0710),
}

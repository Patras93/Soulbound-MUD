# -*- coding: utf-8 -*-
"""Soulbound v1.13.0 - Smoczy Świat.

Duża, stała kraina do późnego expienia:
- bezpieczny Bastion Smoczego Świata,
- sześć ośmiopokojowych stref polowań,
- dziesięciopokojowa Smocza Cytadela,
- rare smoki, minibossowie i pięciu Smoczych Władców,
- dwanaście godzinnych questów z ręcznie chronionym EXP statystyk.

Kraina nie wprowadza blokady poziomem. Etap jest rekomendacją i źródłem
skalowania nagród; gracz może wejść wcześniej na własne ryzyko.
"""
from __future__ import annotations

from data.catalogs import ROOMS, NPCS, ITEMS, QUESTS, MOB_TEMPLATES
from core.economy_curve import economy_stage_anchor
from data.catalog_mutations import catalog_assign, catalog_set_path
from systems.content_registry import MOB_SPAWNS, HELP_TOPICS, HELP_TOPIC_ALIASES
from world.generation_systems import GUIDE_DESTINATION_ALIASES, v0130_refresh_exploration_catalog
from world import dynamic_content as _dynamic_content
from world import generation_systems as _generation_systems

DRAGON_WORLD_VERSION = "1.13.0"
DRAGON_WORLD_NAME = "Smoczy Świat"

_OPPOSITE = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "northeast": "southwest", "southwest": "northeast",
    "northwest": "southeast", "southeast": "northwest",
    "up": "down", "down": "up",
}
_DIRECTIONS = tuple(_OPPOSITE)

DRAGON_WORLD_ROOMS = []
DRAGON_WORLD_MOBS = []
DRAGON_WORLD_NPCS = []
DRAGON_WORLD_QUESTS = []
DRAGON_WORLD_ITEMS = []
DRAGON_WORLD_SPAWNS = []
DRAGON_WORLD_ZONE_ROOMS = {}
DRAGON_WORLD_LORDS = []


def _dragon_room(room_id, zone, name, desc, *, stage=0, safe=False):
    if room_id in ROOMS:
        raise RuntimeError(f"v1.13.0 duplicate dragon room id: {room_id}")
    payload = {
        "zone": zone,
        "name": name,
        "desc": desc,
        "exits": {},
        "v1130_dragon_world": True,
        "dragon_stage": int(stage or 0),
    }
    if safe:
        payload["safe_room"] = True
        payload["safe_hub"] = True
        payload["dragon_safe_hub"] = True
    catalog_assign(payload, "ROOMS", ROOMS, (room_id,))
    DRAGON_WORLD_ROOMS.append(room_id)
    DRAGON_WORLD_ZONE_ROOMS.setdefault(zone, []).append(room_id)
    return room_id


def _dragon_link(a, direction, b, *, reverse=True):
    if a not in ROOMS or b not in ROOMS:
        raise RuntimeError(f"v1.13.0 missing dragon link endpoint: {a} {direction} {b}")
    if direction not in _OPPOSITE:
        raise RuntimeError(f"v1.13.0 unsupported direction: {direction}")
    old = (ROOMS[a].get("exits") or {}).get(direction)
    if old not in (None, b):
        raise RuntimeError(f"v1.13.0 exit collision {a}.{direction}: {old} -> {b}")
    catalog_set_path("ROOMS", ROOMS, (a, "exits", direction), b)
    if reverse:
        back = _OPPOSITE[direction]
        old_back = (ROOMS[b].get("exits") or {}).get(back)
        if old_back not in (None, a):
            raise RuntimeError(f"v1.13.0 reverse exit collision {b}.{back}: {old_back} -> {a}")
        catalog_set_path("ROOMS", ROOMS, (b, "exits", back), a)


def _first_free_direction(room_id, preferred=()):
    used = set((ROOMS[room_id].get("exits") or {}).keys())
    for direction in tuple(preferred) + _DIRECTIONS:
        if direction not in used:
            return direction
    raise RuntimeError(f"v1.13.0 no free direction from {room_id}")


def _grid(prefix, zone, stage, names, desc):
    if len(names) != 8:
        raise RuntimeError(f"v1.13.0 zone {zone} must define exactly 8 room names")
    ids = []
    for idx, name in enumerate(names, 1):
        ids.append(_dragon_room(
            f"dragon_{prefix}_{idx:02d}",
            zone,
            name,
            f"{desc} Punkt {idx} tworzy część szerokiej pętli łowieckiej, więc nie jest to ślepy korytarz.",
            stage=stage,
        ))
    _dragon_link(ids[0], "east", ids[1])
    _dragon_link(ids[1], "east", ids[2])
    _dragon_link(ids[2], "east", ids[3])
    _dragon_link(ids[4], "east", ids[5])
    _dragon_link(ids[5], "east", ids[6])
    _dragon_link(ids[6], "east", ids[7])
    _dragon_link(ids[0], "south", ids[4])
    _dragon_link(ids[2], "south", ids[6])
    _dragon_link(ids[3], "south", ids[7])
    _dragon_link(ids[5], "north", ids[1])
    return tuple(ids)


def _item(item_id, name, desc, *, rarity="epic"):
    if item_id in ITEMS:
        raise RuntimeError(f"v1.13.0 duplicate dragon item id: {item_id}")
    payload = {
        "name": name,
        "type": "craft_material",
        "price": None,
        "rarity": rarity,
        "rarity_name": "Mityczny" if rarity == "mythic" else "Epicki",
        "desc": desc,
        "v1130_dragon_world": True,
    }
    catalog_assign(payload, "ITEMS", ITEMS, (item_id,))
    DRAGON_WORLD_ITEMS.append(item_id)
    return item_id


def _dragon_mob(mob_id, name, stage, zone_target, *, magic=False, rank="normal",
         drops=None, mechanic=None, mechanic_text=None):
    if mob_id in MOB_TEMPLATES:
        raise RuntimeError(f"v1.13.0 duplicate dragon mob id: {mob_id}")
    stage = max(1, min(800, int(stage)))
    rank_mult = {
        "normal": 1.0,
        "rare": 1.9,
        "mini": 3.4,
        "world_boss": 8.5,
    }[rank]
    payload = {
        "name": name,
        "max_hp": max(1, int((45_000 + stage * 115) * rank_mult)),
        "damage": max(1, int((180 + stage * 1.7) * (1.0 + (rank_mult - 1.0) * 0.13))),
        "damage_type": "magic" if magic else "physical",
        "silver": max(1, int((15_000 + stage * 140) * rank_mult)),
        "gold": 0,
        "mithril": 0,
        "stat_reward": max(1, int((1_200 + stage * 3.2) * rank_mult)),
        "class_xp_reward": max(1, int(stage * 18 * rank_mult)),
        "soul_reward": max(1, int(stage * 9 * rank_mult)),
        "character_xp_reward": max(1, int(stage * 14 * rank_mult)),
        "drops": dict(drops or {}),
        "quest_target": mob_id,
        "quest_targets": (zone_target, mob_id),
        "generator_level": stage,
        "v1130_dragon_world": True,
        "dragon_zone_target": zone_target,
        "auto_aggro": False,
    }
    if rank == "rare":
        payload.update({
            "rank": "rare",
            "rare_mob": True,
            "rare_variant": True,
            "respawn_seconds": 8 * 60,
        })
    elif rank == "mini":
        payload.update({
            "rank": "mini",
            "mini_boss": True,
            "boss": True,
            "respawn_seconds": 12 * 60,
        })
    elif rank == "world_boss":
        payload.update({
            "rank": "world_boss",
            "world_boss": True,
            "boss": True,
            "respawn_seconds": 30 * 60,
            "boss_mechanic": mechanic or "astral_sovereign",
            "boss_mechanic_text": mechanic_text or "Smoczy Władca zmienia rytm walki w kolejnych fazach.",
        })
        DRAGON_WORLD_LORDS.append(mob_id)
    catalog_assign(payload, "MOB_TEMPLATES", MOB_TEMPLATES, (mob_id,))
    DRAGON_WORLD_MOBS.append(mob_id)
    return mob_id


def _dragon_spawn(room_id, mob_id, count=1):
    if room_id not in ROOMS or mob_id not in MOB_TEMPLATES:
        raise RuntimeError(f"v1.13.0 invalid dragon spawn {room_id}->{mob_id}")
    for _ in range(max(1, int(count))):
        row = (room_id, mob_id)
        MOB_SPAWNS.append(row)
        DRAGON_WORLD_SPAWNS.append(row)


def _dragon_quest_currency(stage, needed):
    """Authored dragon-quest payout on the shared 1-600 economy curve.

    Dragon quests are repeatable kill quests, so keep their authored payout
    aligned with the normal quest-income target without delegating reward
    ownership to Generator Core or a later runtime finalizer.
    """
    stage = max(1, min(800, int(stage)))
    needed = max(1, int(needed))
    workload = 1.0 + min(0.54, 0.06 * (needed - 1))
    return max(
        100,
        int(round(economy_stage_anchor(stage) * 1.25 * workload * 0.85)),
    )


def _dragon_quest(qid, name, giver, target, needed, description, stage, stat_xp,
           *, requires=None, reward_items=None):
    if qid in QUESTS:
        raise RuntimeError(f"v1.13.0 duplicate dragon quest id: {qid}")
    stage = max(1, min(800, int(stage)))
    needed = max(1, int(needed))
    payload = {
        "name": name,
        "giver": giver,
        "kind": "kill",
        "target": target,
        "needed": needed,
        "description": description,
        "level": stage,
        "manual_stat_progress": int(stat_xp),
        "reward_stat_progress": int(stat_xp),
        "reward_silver": _dragon_quest_currency(stage, needed),
        "reward_gold": 0,
        "reward_mithril": 0,
        "reward_items": dict(reward_items or {}),
        "repeatable": True,
        "repeat_cooldown": 60 * 60,
        "v1130_dragon_world": True,
    }
    if requires:
        payload["requires_quest"] = requires
    catalog_assign(payload, "QUESTS", QUESTS, (qid,))
    DRAGON_WORLD_QUESTS.append(qid)
    return qid


def _dragon_npc(npc_id, name, room, dialogue, quest_ids=()):
    if npc_id in NPCS:
        raise RuntimeError(f"v1.13.0 duplicate dragon NPC id: {npc_id}")
    qids = tuple(quest_ids)
    payload = {
        "name": name,
        "room": room,
        "dialogue": dialogue,
        "v1130_dragon_world": True,
    }
    if qids:
        payload["quest"] = qids[0]
        payload["quest_chain"] = qids[1:]
    catalog_assign(payload, "NPCS", NPCS, (npc_id,))
    DRAGON_WORLD_NPCS.append(npc_id)
    return npc_id


if "titan_valley_throne" not in ROOMS:
    raise RuntimeError("v1.13.0 requires Dolina Tytanów from World Expansion I")

gate = _dragon_room(
    "dragon_world_gate", "Bastion Smoczego Świata", "Brama Smoczego Świata",
    "Kamienny portal unosi się nad krawędzią Doliny Tytanów. Za nim czuć gorące powietrze, ozon i odległe uderzenia ogromnych skrzydeł.",
    safe=True,
)
square = _dragon_room(
    "dragon_bastion_square", "Bastion Smoczego Świata", "Plac Smoczego Bastionu",
    "Warowny plac otaczają wysokie mury odporne na ogień. To główny punkt wypraw, odpoczynku i zbierania grup.",
    safe=True,
)
hall = _dragon_room(
    "dragon_bastion_hall", "Bastion Smoczego Świata", "Sala Łowców Smoków",
    "Tablice zleceń opisują aktywne polowania od Popielnych Równin aż po Smoczą Cytadelę.",
    safe=True,
)
inn = _dragon_room(
    "dragon_bastion_inn", "Bastion Smoczego Świata", "Karczma Pod Srebrnym Skrzydłem",
    "Grube kamienne ściany tłumią ryk smoków. Wyprawy spotykają się tu przed wejściem na dalsze szlaki.",
    safe=True,
)
forge = _dragon_room(
    "dragon_bastion_forge", "Bastion Smoczego Świata", "Smocza Kuźnia",
    "Piece są zasilane żarem przywożonym z Wulkanicznej Otchłani. Na razie kuźnia skupuje wiedzę o nowych materiałach, a dalsze receptury mogą zostać dodane osobno.",
    safe=True,
)
observatory = _dragon_room(
    "dragon_bastion_observatory", "Bastion Smoczego Świata", "Obserwatorium Smoczych Szlaków",
    "Z kamiennego tarasu słychać różne odmiany smoków. Strażnicy opisują kierunki do każdej strefy bez wymagania wzroku.",
    safe=True,
)

anchor_dir = _first_free_direction("titan_valley_throne", ("up", "north", "east"))
_dragon_link("titan_valley_throne", anchor_dir, gate)
GUIDE_DESTINATION_ALIASES["smoczy swiat"] = gate
GUIDE_DESTINATION_ALIASES["smoczy świat"] = gate
GUIDE_DESTINATION_ALIASES["dragon world"] = gate
_dragon_link(gate, "north", square)
_dragon_link(square, "east", hall)
_dragon_link(square, "west", inn)
_dragon_link(square, "down", forge)
_dragon_link(square, "north", observatory)

MAT_SCALE = _item(
    "dragon_world_scale", "Łuska Smoczego Świata",
    "Twarda łuska zwykłych smoków. Bazowy materiał przyszłego smoczego rzemiosła.",
)
MAT_ASH = _item(
    "dragon_world_ashen_core", "Popielny Rdzeń",
    "Gorący rdzeń z Popielnych Równin i Smoczych Kanionów.",
)
MAT_CRYSTAL = _item(
    "dragon_world_crystal_shard", "Kryształ Smoczego Gniazda",
    "Kryształ nasycony energią smoków z Kryształowych Gniazd.",
)
MAT_INFERNO = _item(
    "dragon_world_inferno_heart", "Serce Wulkanicznego Smoka",
    "Mityczny materiał zachowujący żar Wulkanicznej Otchłani.",
    rarity="mythic",
)
MAT_STORM = _item(
    "dragon_world_storm_heart", "Serce Burzowego Smoka",
    "Mityczny rdzeń przechowujący elektryczną energię Szczytów Burzy.",
    rarity="mythic",
)
MAT_BONE = _item(
    "dragon_world_ancient_bone", "Kość Pradawnego Smoka",
    "Kość starsza niż większość zapisanej historii Soulbound.",
    rarity="mythic",
)
MAT_SIGIL = _item(
    "dragon_world_sovereign_sigil", "Pieczęć Smoczego Suwerena",
    "Najrzadszy znak władzy zdobywany w Smoczej Cytadeli.",
    rarity="mythic",
)

ZONE_SPECS = (
    (
        "ashen", "Popielne Równiny", 520,
        (
            "Spękana Brama Popiołu", "Szlak Ciepłych Skał", "Pole Czarnego Pyłu", "Wyschnięte Gniazda",
            "Rów Żarzących Kości", "Płaskowyż Młodych Smoków", "Popielna Grań", "Legowisko Matki Popiołu",
        ),
        "Szerokie równiny są pokryte popiołem, ale układ dróg pozostaje czytelny i otwarty.",
        ("dragon_ash_wyrmling", "Popielny Młody Smok", False),
        ("dragon_ember_drake", "Żarowy Drakon", True),
        ("dragon_ashen_rare", "Szkarłatny Zbieracz", False),
        ("dragon_ash_matron", "Matka Popiołu", True),
        MAT_ASH,
        None,
    ),
    (
        "canyon", "Smocze Kaniony", 540,
        (
            "Wejście do Kanionów", "Kamienny Most Skrzydeł", "Kanion Złamanych Rogów", "Przesmyk Łowców",
            "Wąwóz Echo Ryku", "Półka Kamiennych Drakonów", "Rozdarta Grań", "Arena Kanionu",
        ),
        "Wielopoziomowe ściany skalne tworzą szerokie pętle, po których krążą ciężkie drakony.",
        ("dragon_canyon_drake", "Kamienny Drakon", False),
        ("dragon_canyon_hunter", "Smoczy Łowca Kanionu", False),
        ("dragon_canyon_rare", "Żelaznorogi Smok", False),
        ("dragon_canyon_champion", "Czempion Rozdartej Grani", False),
        MAT_SCALE,
        None,
    ),
    (
        "crystal", "Kryształowe Gniazda", 560,
        (
            "Kryształowe Wejście", "Galeria Błękitnych Łusek", "Sala Lustrzanych Gniazd", "Korytarz Świetlnych Żył",
            "Taras Szafirowych Skrzydeł", "Komora Rezonansu", "Kryształowy Krąg", "Tron Kryształowych Skrzydeł",
        ),
        "Ściany rezonują od smoczej magii. Kryształy wzmacniają każdy ryk i każde uderzenie skrzydeł.",
        ("dragon_crystal_wyrm", "Kryształowy Wyrm", True),
        ("dragon_sapphire_drake", "Szafirowy Drakon", True),
        ("dragon_crystal_rare", "Lustrzany Smok", True),
        ("dragon_crystal_guardian", "Strażnik Kryształowych Gniazd", True),
        MAT_CRYSTAL,
        ("dragon_lord_crystal", "Aureliusz Kryształowych Skrzydeł", True, "crystal_lord",
         "Tworzy kryształowe osłony i wzmacnia magię w kolejnych fazach."),
    ),
    (
        "volcanic", "Wulkaniczna Otchłań", 580,
        (
            "Krawędź Otchłani", "Most nad Lawą", "Pole Bazaltowych Kolców", "Jaskinia Płynnego Ognia",
            "Schody Czerwonego Serca", "Komora Lawowych Skrzydeł", "Krater Smoczego Żaru", "Serce Wulkanu",
        ),
        "Lawa płynie pod bazaltowymi mostami, a gorąco zdradza obecność wielkich ognistych smoków.",
        ("dragon_lava_drake", "Lawowy Drakon", False),
        ("dragon_inferno_wyrm", "Wyrm Płynnego Ognia", True),
        ("dragon_volcanic_rare", "Białożarowy Smok", True),
        ("dragon_magma_colossus", "Magma Kolos", False),
        MAT_INFERNO,
        ("dragon_lord_inferno", "Ignivar, Serce Wulkanu", True, "bone_rage",
         "Wraz z kolejnymi fazami jego żar i siła fizycznych uderzeń rosną."),
    ),
    (
        "storm", "Szczyty Burzowych Smoków", 600,
        (
            "Podnóże Burzowej Korony", "Ścieżka Piorunów", "Most Chmur", "Półka Grzmotu",
            "Gniazdo Błyskawic", "Oko Smoczej Burzy", "Szczyt Rozdartego Nieba", "Korona Burzy",
        ),
        "Wysokie granie przecinają wyładowania, a smoki poruszają się między chmurami i skalnymi półkami.",
        ("dragon_storm_drake", "Burzowy Drakon", True),
        ("dragon_thunder_wyrm", "Gromowy Wyrm", True),
        ("dragon_storm_rare", "Smok Białej Błyskawicy", True),
        ("dragon_tempest_guardian", "Strażnik Oka Burzy", True),
        MAT_STORM,
        ("dragon_lord_storm", "Vaelthra, Królowa Burz", True, "stellar_storm",
         "Co kilka tur rozpętuje burzę obejmującą całe pole walki."),
    ),
    (
        "grave", "Cmentarzysko Pradawnych Smoków", 600,
        (
            "Brama Wielkich Kości", "Aleja Żeber Kolosów", "Dolina Pustych Czaszek", "Kurhan Pierwszego Lotu",
            "Pole Skamieniałych Skrzydeł", "Krypta Smoczych Imion", "Krąg Kościanego Echa", "Tron Umarłego Smoka",
        ),
        "Olbrzymie szkielety tworzą naturalne łuki i tunele. Energia dusz budzi kościane smoki i pradawne widma.",
        ("dragon_bone_wyrm", "Kościany Wyrm", False),
        ("dragon_ancestral_spirit", "Duch Pradawnego Smoka", True),
        ("dragon_grave_rare", "Bezimienny Smok Kości", True),
        ("dragon_grave_keeper", "Strażnik Smoczych Imion", True),
        MAT_BONE,
        ("dragon_lord_bone", "Morgrath Kościany", False, "blood_drain",
         "Wysysa siłę z przeciwników i odnawia część własnej żywotności."),
    ),
)

zone_mob_sets = {}
zone_lords = {}
previous_exit = observatory

for key, zone, stage, names, desc, normal_a, normal_b, rare_spec, mini_spec, material, lord_spec in ZONE_SPECS:
    rooms = _grid(key, zone, stage, names, desc)
    _dragon_link(previous_exit, "up", rooms[0])
    previous_exit = rooms[-1]

    target = f"dragon_{key}_threat"
    normal1 = _dragon_mob(
        normal_a[0], normal_a[1], stage, target, magic=normal_a[2],
        drops={MAT_SCALE: 0.22, material: 0.08},
    )
    normal2 = _dragon_mob(
        normal_b[0], normal_b[1], stage, target, magic=normal_b[2],
        drops={MAT_SCALE: 0.20, material: 0.10},
    )
    rare = _dragon_mob(
        rare_spec[0], rare_spec[1], min(800, stage + 10), target,
        magic=rare_spec[2], rank="rare",
        drops={MAT_SCALE: 0.65, material: 0.45},
    )
    mini = _dragon_mob(
        mini_spec[0], mini_spec[1], min(800, stage + 20), target,
        magic=mini_spec[2], rank="mini",
        drops={MAT_SCALE: 0.90, material: 0.70, "soul_shard": 0.55},
    )
    lord = None
    if lord_spec:
        lord = _dragon_mob(
            lord_spec[0], lord_spec[1], min(800, stage + 25), target,
            magic=lord_spec[2], rank="world_boss",
            drops={MAT_SCALE: 1.0, material: 1.0, "soul_shard": 1.0, "soul_elixir": 0.45},
            mechanic=lord_spec[3], mechanic_text=lord_spec[4],
        )
        zone_lords[key] = lord

    zone_mob_sets[key] = (normal1, normal2, rare, mini, lord)

    for idx, rid in enumerate(rooms):
        _dragon_spawn(rid, normal1 if idx % 2 == 0 else normal2, 2)
        _dragon_spawn(rid, normal2 if idx % 2 == 0 else normal1, 1)
    _dragon_spawn(rooms[5], rare, 1)
    _dragon_spawn(rooms[6], mini, 1)
    if lord:
        _dragon_spawn(rooms[7], lord, 1)

citadel_zone = "Smocza Cytadela"
citadel_names = (
    "Brama Smoczej Cytadeli", "Dziedziniec Skrzydlatych Straży", "Galeria Złotych Łusek", "Sala Smoczych Chorągwi", "Schody Suwerena",
    "Koszary Smoczej Gwardii", "Komnata Starszych Drakonów", "Korytarz Pierwszego Ognia", "Sala Koronacji", "Tron Smoczego Suwerena",
)
citadel_rooms = []
for idx, name in enumerate(citadel_names, 1):
    citadel_rooms.append(_dragon_room(
        f"dragon_citadel_{idx:02d}",
        citadel_zone,
        name,
        "Cytadela została wykuta dla najstarszych smoków. Każdy odcinek prowadzi bliżej tronu i ma własną obsadę gwardii.",
        stage=600,
    ))
for c in range(4):
    _dragon_link(citadel_rooms[c], "east", citadel_rooms[c + 1])
    _dragon_link(citadel_rooms[5 + c], "east", citadel_rooms[5 + c + 1])
_dragon_link(citadel_rooms[0], "south", citadel_rooms[5])
_dragon_link(citadel_rooms[2], "south", citadel_rooms[7])
_dragon_link(citadel_rooms[4], "south", citadel_rooms[9])
_dragon_link(citadel_rooms[6], "north", citadel_rooms[1])
_dragon_link(previous_exit, "up", citadel_rooms[0])

citadel_target = "dragon_citadel_threat"
citadel_guard = _dragon_mob(
    "dragon_citadel_guard", "Smoczy Strażnik Cytadeli", 600, citadel_target,
    drops={MAT_SCALE: 0.35, MAT_SIGIL: 0.03},
)
citadel_mage = _dragon_mob(
    "dragon_citadel_oracle", "Wyrocznia Smoczej Cytadeli", 600, citadel_target, magic=True,
    drops={MAT_SCALE: 0.30, MAT_SIGIL: 0.04},
)
citadel_rare = _dragon_mob(
    "dragon_citadel_rare", "Złoty Smok Gwardii", 600, citadel_target, rank="rare",
    drops={MAT_SCALE: 0.85, MAT_SIGIL: 0.35},
)
citadel_mini = _dragon_mob(
    "dragon_citadel_champion", "Pierwszy Czempion Cytadeli", 600, citadel_target, rank="mini",
    drops={MAT_SCALE: 1.0, MAT_SIGIL: 0.65, "soul_shard": 1.0},
)
sovereign = _dragon_mob(
    "dragon_lord_sovereign", "Azharyon, Władca Smoczego Świata", 600, citadel_target,
    magic=True, rank="world_boss",
    drops={MAT_SCALE: 1.0, MAT_SIGIL: 1.0, MAT_INFERNO: 0.65, MAT_STORM: 0.65, MAT_BONE: 0.65, "soul_elixir": 1.0},
    mechanic="astral_sovereign",
    mechanic_text="Suweren przechodzi przez kolejne fazy, łącząc magię kryształu, ognia, burzy i pradawnych dusz.",
)
zone_lords["citadel"] = sovereign

for idx, rid in enumerate(citadel_rooms):
    _dragon_spawn(rid, citadel_guard if idx % 2 == 0 else citadel_mage, 2)
    _dragon_spawn(rid, citadel_mage if idx % 2 == 0 else citadel_guard, 1)
_dragon_spawn(citadel_rooms[6], citadel_rare, 1)
_dragon_spawn(citadel_rooms[8], citadel_mini, 1)
_dragon_spawn(citadel_rooms[9], sovereign, 1)

q_ash = _dragon_quest(
    "dragon_q_ashen_hunt", "Smoczy Świat: Popielne Równiny", "Zwiadowca Smoczego Bastionu Arven",
    "dragon_ashen_threat", 16,
    "Pokonaj 16 zagrożeń na Popielnych Równinach.", 520, 30_000,
    reward_items={MAT_ASH: 2},
)
q_canyon = _dragon_quest(
    "dragon_q_canyon_hunt", "Smoczy Świat: Smocze Kaniony", "Zwiadowca Smoczego Bastionu Arven",
    "dragon_canyon_threat", 16,
    "Pokonaj 16 smoków i drakonów w Smoczych Kanionach.", 540, 35_000,
    requires=q_ash, reward_items={MAT_SCALE: 3},
)
q_crystal = _dragon_quest(
    "dragon_q_crystal_hunt", "Smoczy Świat: Kryształowe Gniazda", "Badaczka Smoków Lyra",
    "dragon_crystal_threat", 18,
    "Pokonaj 18 przeciwników w Kryształowych Gniazdach.", 560, 40_000,
    requires=q_canyon, reward_items={MAT_CRYSTAL: 3},
)
q_crystal_lord = _dragon_quest(
    "dragon_q_crystal_lord", "Smoczy Władca: Aureliusz", "Badaczka Smoków Lyra",
    zone_lords["crystal"], 1,
    "Pokonaj Aureliusza Kryształowych Skrzydeł.", 560, 50_000,
    requires=q_crystal, reward_items={MAT_CRYSTAL: 5, "soul_elixir": 1},
)
q_volcanic = _dragon_quest(
    "dragon_q_volcanic_hunt", "Smoczy Świat: Wulkaniczna Otchłań", "Badaczka Smoków Lyra",
    "dragon_volcanic_threat", 18,
    "Pokonaj 18 przeciwników w Wulkanicznej Otchłani.", 580, 45_000,
    requires=q_crystal_lord, reward_items={MAT_INFERNO: 2},
)
q_inferno_lord = _dragon_quest(
    "dragon_q_inferno_lord", "Smoczy Władca: Ignivar", "Badaczka Smoków Lyra",
    zone_lords["volcanic"], 1,
    "Pokonaj Ignivara, Serce Wulkanu.", 580, 60_000,
    requires=q_volcanic, reward_items={MAT_INFERNO: 4, "soul_elixir": 1},
)
q_storm = _dragon_quest(
    "dragon_q_storm_hunt", "Smoczy Świat: Szczyty Burzy", "Strażnik Burz Orin",
    "dragon_storm_threat", 20,
    "Pokonaj 20 smoków na Szczytach Burzowych Smoków.", 600, 50_000,
    requires=q_inferno_lord, reward_items={MAT_STORM: 2},
)
q_storm_lord = _dragon_quest(
    "dragon_q_storm_lord", "Smoczy Władca: Vaelthra", "Strażnik Burz Orin",
    zone_lords["storm"], 1,
    "Pokonaj Vaelthrę, Królową Burz.", 600, 65_000,
    requires=q_storm, reward_items={MAT_STORM: 4, "soul_elixir": 1},
)
q_grave = _dragon_quest(
    "dragon_q_grave_hunt", "Smoczy Świat: Cmentarzysko Pradawnych", "Strażnik Burz Orin",
    "dragon_grave_threat", 20,
    "Pokonaj 20 kościanych smoków i pradawnych duchów.", 600, 55_000,
    requires=q_storm_lord, reward_items={MAT_BONE: 2},
)
q_bone_lord = _dragon_quest(
    "dragon_q_bone_lord", "Smoczy Władca: Morgrath", "Strażnik Cytadeli Selene",
    zone_lords["grave"], 1,
    "Pokonaj Morgratha Kościanego.", 600, 70_000,
    requires=q_grave, reward_items={MAT_BONE: 4, "soul_elixir": 1},
)
q_citadel = _dragon_quest(
    "dragon_q_citadel_hunt", "Smoczy Świat: Szturm na Cytadelę", "Strażnik Cytadeli Selene",
    citadel_target, 24,
    "Pokonaj 24 strażników, wyrocznie i czempionów Smoczej Cytadeli.", 600, 60_000,
    requires=q_bone_lord, reward_items={MAT_SIGIL: 2},
)
q_sovereign = _dragon_quest(
    "dragon_q_sovereign", "Smoczy Władca: Azharyon", "Strażnik Cytadeli Selene",
    sovereign, 1,
    "Dotrzyj do tronu i pokonaj Azharyona, Władcę Smoczego Świata.", 600, 75_000,
    requires=q_citadel, reward_items={MAT_SIGIL: 5, "soul_elixir": 2},
)

_dragon_npc(
    "dragon_scout_arven", "Zwiadowca Smoczego Bastionu Arven", hall,
    "Popielne Równiny i Smocze Kaniony są najlepszym wejściem w tę krainę. Zlecenia odnawiają się co godzinę.",
    (q_ash, q_canyon),
)
_dragon_npc(
    "dragon_scholar_lyra", "Badaczka Smoków Lyra", observatory,
    "Kryształowe Gniazda i Wulkaniczna Otchłań pokazują, jak różne mogą być smocze linie. Badam również ich Władców.",
    (q_crystal, q_crystal_lord, q_volcanic, q_inferno_lord),
)
_dragon_npc(
    "dragon_storm_warden_orin", "Strażnik Burz Orin", square,
    "Szczyty Burzy i Cmentarzysko Pradawnych wymagają już doświadczonej drużyny, ale nagrody rosną razem z ryzykiem.",
    (q_storm, q_storm_lord, q_grave),
)
_dragon_npc(
    "dragon_citadel_selene", "Strażnik Cytadeli Selene", hall,
    "Po pokonaniu władców zewnętrznych stref pozostaje Morgrath i sama Cytadela. Suweren nie jest końcem gry, tylko najtrudniejszym celem tej krainy.",
    (q_bone_lord, q_citadel, q_sovereign),
)
_dragon_npc(
    "dragon_material_keeper", "Mistrz Smoczych Materiałów Rhael", forge,
    "Łuski, kryształy, serca i pradawne kości zachowuj. Smoczy Świat ma własną linię materiałów, którą można później rozbudować o pełne receptury bez resetowania zdobytych zasobów.",
    (),
)

for item_id in DRAGON_WORLD_ITEMS:
    _dynamic_content.MATERIAL_COLLECTION_CATALOG[item_id] = ITEMS[item_id]["name"]

for mob_id in DRAGON_WORLD_MOBS:
    _dynamic_content.BESTIARY_CATALOG[mob_id] = MOB_TEMPLATES[mob_id]["name"]
    if MOB_TEMPLATES[mob_id].get("rare_mob"):
        _dynamic_content.RARE_MOB_COLLECTION_CATALOG[mob_id] = MOB_TEMPLATES[mob_id]["name"]
    if MOB_TEMPLATES[mob_id].get("mini_boss") or MOB_TEMPLATES[mob_id].get("world_boss"):
        _dynamic_content.BOSS_COLLECTION_CATALOG[mob_id] = MOB_TEMPLATES[mob_id]["name"]

for room_id, mob_id in DRAGON_WORLD_SPAWNS:
    _dynamic_content.BESTIARY_SPAWN_ROOMS.setdefault(mob_id, set()).add(room_id)

# This module loads before player session mixins. Refresh the mutable and
# immutable exploration snapshots now, so imported player-facing views include
# Smoczy Świat from their first import instead of keeping the old tuple.
v0130_refresh_exploration_catalog()
for zone, room_ids in DRAGON_WORLD_ZONE_ROOMS.items():
    ordered = sorted(set(room_ids))
    _dynamic_content.EXPLORATION_ZONE_ROOMS[zone] = ordered
    if len(ordered) >= 3:
        _dynamic_content.TRACKED_EXPLORATION_ZONES[zone] = tuple(ordered)
    reward_item = _generation_systems.EXPLORATION_REWARD_ITEMS.get(zone)
    if reward_item:
        _dynamic_content.EXPLORATION_REWARD_ITEMS[zone] = reward_item

_dynamic_content.ALL_EXPLORATION_ROOMS = tuple(sorted(ROOMS))
_exploration_tiers = list(
    _dynamic_content.ACHIEVEMENT_TRACKS.get("exploration_rooms", {}).get("tiers", ())
)
if _exploration_tiers:
    _exploration_tiers = [
        (required, tier)
        for required, tier in _exploration_tiers
        if tier != "Platinum"
    ]
    _exploration_tiers.append(
        (len(_dynamic_content.ALL_EXPLORATION_ROOMS), "Platinum")
    )
    _dynamic_content.ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = tuple(
        _exploration_tiers
    )

_dynamic_content.MINI_BOSS_IDS = frozenset(
    mob_id
    for mob_id, template in MOB_TEMPLATES.items()
    if template.get("mini_boss")
)
_bestiary_tiers = list(
    _dynamic_content.ACHIEVEMENT_TRACKS.get("bestiary_unique", {}).get("tiers", ())
)
if _bestiary_tiers:
    _bestiary_tiers = [
        (required, tier)
        for required, tier in _bestiary_tiers
        if tier != "Platinum"
    ]
    _bestiary_tiers.append(
        (len(_dynamic_content.BESTIARY_CATALOG), "Platinum")
    )
    _dynamic_content.ACHIEVEMENT_TRACKS["bestiary_unique"]["tiers"] = tuple(
        _bestiary_tiers
    )

for zone in DRAGON_WORLD_ZONE_ROOMS:
    region = _dynamic_content.REGION_COLLECTION_ENTRIES.setdefault(
        zone, {"named": set(), "bosses": set(), "rare": set(), "chests": set()}
    )
    region.setdefault("bosses", set())
    region.setdefault("rare", set())
    region.setdefault("named", set())
    region.setdefault("chests", set())

for room_id, mob_id in DRAGON_WORLD_SPAWNS:
    zone = str(ROOMS.get(room_id, {}).get("zone") or "")
    if not zone:
        continue
    region = _dynamic_content.REGION_COLLECTION_ENTRIES.setdefault(
        zone, {"named": set(), "bosses": set(), "rare": set(), "chests": set()}
    )
    template = MOB_TEMPLATES.get(mob_id, {})
    if template.get("mini_boss") or template.get("world_boss"):
        region.setdefault("bosses", set()).add(mob_id)
    if template.get("rare_mob"):
        region.setdefault("rare", set()).add(mob_id)

HELP_TOPICS["smoczy_swiat"] = [
    "Smoczy Świat jest stałą wysokopoziomową krainą do długiego expienia, a nie pojedynczym lochem.",
    "Wejście prowadzi z Doliny Tytanów przez Bramę Smoczego Świata do bezpiecznego Bastionu.",
    "Kolejność stref: Popielne Równiny 520, Smocze Kaniony 540, Kryształowe Gniazda 560, Wulkaniczna Otchłań 580, Szczyty Burzy 600, Cmentarzysko Pradawnych 600, Smocza Cytadela 600.",
    "Kraina ma 64 stałe pomieszczenia: 6 w hubie, sześć stref po 8 pomieszczeń i 10 pomieszczeń Cytadeli.",
    "Każda strefa ma zwykłe smoki, osobnego rare i minibossa. Kryształ, Wulkan, Burza, Cmentarzysko oraz Cytadela mają łącznie pięciu Smoczych Władców.",
    "Zadania odnawiają się co 60 minut. Ich ręczna baza to 30000-75000 EXP każdej z sześciu statystyk; przy globalnym mnożniku stat EXP x4 daje to obecnie 120000-300000 do każdej statystyki przed rasą, Gildią i x2 EXP.",
    "Party nie dzieli nagród: każdy obecny członek drużyny zachowuje własne pełne EXP i walutę zgodnie z aktualnym systemem drużyny.",
    "Nie ma blokady levelem. Liczby 520-600 oznaczają rekomendowany etap i skalowanie przeciwników.",
    "Smocze materiały zachowuj; są przygotowane jako osobna baza przyszłego smoczego rzemiosła.",
]
HELP_TOPIC_ALIASES.update({
    "smoczy swiat": "smoczy_swiat",
    "smoczy świat": "smoczy_swiat",
    "dragon world": "smoczy_swiat",
    "smoki": "smoczy_swiat",
    "dragon": "smoczy_swiat",
})

def dragon_world_audit_v1130():
    errors = []
    expected_zone_sizes = {
        "Bastion Smoczego Świata": 6,
        "Popielne Równiny": 8,
        "Smocze Kaniony": 8,
        "Kryształowe Gniazda": 8,
        "Wulkaniczna Otchłań": 8,
        "Szczyty Burzowych Smoków": 8,
        "Cmentarzysko Pradawnych Smoków": 8,
        "Smocza Cytadela": 10,
    }
    if len(DRAGON_WORLD_ROOMS) != 64:
        errors.append(f"dragon world room count {len(DRAGON_WORLD_ROOMS)}, expected 64")
    for zone, expected in expected_zone_sizes.items():
        got = len(DRAGON_WORLD_ZONE_ROOMS.get(zone, ()))
        if got != expected:
            errors.append(f"{zone}: room count {got}, expected {expected}")
    if len(DRAGON_WORLD_LORDS) != 5:
        errors.append(f"dragon lord count {len(DRAGON_WORLD_LORDS)}, expected 5")
    if len(DRAGON_WORLD_QUESTS) != 12:
        errors.append(f"dragon quest count {len(DRAGON_WORLD_QUESTS)}, expected 12")
    if min(int(QUESTS[qid].get("manual_stat_progress", 0) or 0) for qid in DRAGON_WORLD_QUESTS) < 30_000:
        errors.append("dragon quest stat XP fell below 30000 per stat")
    if int(QUESTS["dragon_q_sovereign"].get("manual_stat_progress", 0) or 0) != 75_000:
        errors.append("Azharyon quest must grant 75000 stat XP per stat")
    for qid in DRAGON_WORLD_QUESTS:
        quest = QUESTS.get(qid, {})
        if not quest.get("repeatable") or int(quest.get("repeat_cooldown", 0) or 0) != 60 * 60:
            errors.append(f"{qid}: must repeat every 60 minutes")
        expected_currency = _dragon_quest_currency(
            quest.get("level", 1), quest.get("needed", 1)
        )
        if int(quest.get("reward_silver", 0) or 0) != expected_currency:
            errors.append(
                f"{qid}: currency {quest.get('reward_silver', 0)} != {expected_currency}"
            )
        if int(quest.get("reward_gold", 0) or 0) or int(quest.get("reward_mithril", 0) or 0):
            errors.append(f"{qid}: dragon currency must stay normalized to silver")
    for rid in DRAGON_WORLD_ROOMS:
        if rid not in ROOMS:
            errors.append(f"missing dragon room: {rid}")
    for mid in DRAGON_WORLD_MOBS:
        if mid not in MOB_TEMPLATES:
            errors.append(f"missing dragon mob: {mid}")
    for rid, mid in DRAGON_WORLD_SPAWNS:
        if rid not in ROOMS or mid not in MOB_TEMPLATES:
            errors.append(f"invalid dragon spawn: {rid}->{mid}")
    if gate not in (ROOMS["titan_valley_throne"].get("exits") or {}).values():
        errors.append("Dolina Tytanów is not connected to Smoczy Świat")
    return {
        "version": DRAGON_WORLD_VERSION,
        "room_count": len(DRAGON_WORLD_ROOMS),
        "mob_count": len(DRAGON_WORLD_MOBS),
        "npc_count": len(DRAGON_WORLD_NPCS),
        "quest_count": len(DRAGON_WORLD_QUESTS),
        "lord_count": len(DRAGON_WORLD_LORDS),
        "spawn_count": len(DRAGON_WORLD_SPAWNS),
        "error_count": len(errors),
        "errors": errors,
    }

DRAGON_WORLD_AUDIT_V1130 = dragon_world_audit_v1130()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
DRAGON_WORLD_STATE = {
    "version": DRAGON_WORLD_VERSION,
    "rooms": tuple(DRAGON_WORLD_ROOMS),
    "zones": {zone: tuple(ids) for zone, ids in DRAGON_WORLD_ZONE_ROOMS.items()},
    "mobs": tuple(DRAGON_WORLD_MOBS),
    "npcs": tuple(DRAGON_WORLD_NPCS),
    "quests": tuple(DRAGON_WORLD_QUESTS),
    "items": tuple(DRAGON_WORLD_ITEMS),
    "lords": tuple(DRAGON_WORLD_LORDS),
    "spawns": tuple(DRAGON_WORLD_SPAWNS),
    "entry": gate,
    "hub": square,
}

__all__ = (
    "DRAGON_WORLD_VERSION",
    "DRAGON_WORLD_NAME",
    "DRAGON_WORLD_STATE",
    "DRAGON_WORLD_AUDIT_V1130",
)

"""Soulbound v0.29.0 - Dynamic World Events + Boss/Nemesis Generator.

This module contains deterministic content-generation rules only. Numeric combat
balance is delegated to Generator Core through runtime_mob_balance().
"""
from __future__ import annotations

import copy
import hashlib
import random
import time

EVENT_ROTATION_SECONDS = 60 * 60
EVENT_COUNT = 5
EVENT_KINDS = (
    ("incursion", "Najazd", "elite", 3),
    ("rare_pack", "Polowanie na rzadkie bestie", "rare", 2),
    ("mini_hunt", "Łowy na czempiona", "mini", 1),
    ("boss_manifestation", "Manifestacja Bossa", "world_boss", 1),
    ("roaming_elites", "Wędrująca elita", "elite", 2),
)

BOSS_MECHANICS = (
    ("blood_drain", "Drenaż życia co kilka kontrataków."),
    ("ash_curse", "Magiczne przekleństwo częściowo omija obronę."),
    ("catacomb_echo", "Co kilka kontrataków wyzwala bardzo silne echo."),
    ("spectral_shift", "Naprzemiennie zmienia typ obrażeń fizyczne/magiczne."),
    ("necro_regen", "Okresowo odzyskuje część maksymalnego HP."),
    ("black_flame", "Okresowo używa silnego magicznego płomienia."),
    ("stellar_storm", "Okresowo wyzwala silną magiczną burzę."),
    ("giant_crush", "Okresowo wykonuje ciężkie fizyczne miażdżenie."),
)

ELITE_AFFIXES = (
    ("armored", "Opancerzony: okresowo redukuje otrzymywane obrażenia."),
    ("vampiric", "Wampiryczny: część zadanych obrażeń leczy przeciwnika."),
    ("regenerating", "Regenerujący: okresowo odzyskuje HP."),
    ("ice", "Lodowy: kontrataki zyskują magiczny charakter i większą moc."),
    ("fire", "Ognisty: kontrataki zyskują magiczny charakter i większą moc."),
)

EPITHETS = (
    "Nieugięty", "Pożeracz Dusz", "Zwiastun Końca", "Krwawy", "Astralny",
    "Bezsenna Groza", "Łamacz Kości", "Władca Popiołu", "Wieczny Łowca",
    "Pogromca Wędrowców", "Czarny Strażnik", "Ten, Który Powraca",
)


def _hash_int(seed: str, *parts) -> int:
    text = ":".join(str(x) for x in (seed,) + parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def event_slot(now=None) -> int:
    now = time.time() if now is None else float(now)
    return int(now // EVENT_ROTATION_SECONDS)


def _eligible_rooms(rooms: dict, mob_spawns, mob_templates: dict):
    by_room = {}
    for room_id, template_id in mob_spawns:
        room = rooms.get(str(room_id))
        template = mob_templates.get(str(template_id))
        if not isinstance(room, dict) or not isinstance(template, dict):
            continue
        # Safe hubs / utility-only rooms are excluded implicitly by requiring a real hostile spawn.
        if template.get("auto_aggro") is True:
            # Still valid; world policy will force generated variants to passive.
            pass
        stage = max(1, min(600, int(room.get("generator_level", room.get("recommended_mastery", 1)) or 1)))
        by_room.setdefault(str(room_id), {"stage": stage, "templates": []})["templates"].append(str(template_id))
    return [(rid, meta) for rid, meta in by_room.items() if meta["templates"]]


def active_events(rooms: dict, mob_spawns, mob_templates: dict, world_seed: str, now=None):
    now = time.time() if now is None else float(now)
    slot = event_slot(now)
    eligible = _eligible_rooms(rooms, mob_spawns, mob_templates)
    if not eligible:
        return tuple()
    result = []
    used = set()
    for index in range(EVENT_COUNT):
        kind, title, rank, count = EVENT_KINDS[index % len(EVENT_KINDS)]
        rng = random.Random(_hash_int(world_seed, "v029-event", slot, index, kind))
        choices = [row for row in eligible if row[0] not in used] or eligible
        room_id, meta = choices[rng.randrange(len(choices))]
        used.add(room_id)
        bases = tuple(meta["templates"])
        result.append({
            "type": kind,
            "title": title,
            "rank": rank,
            "count": count,
            "room_id": room_id,
            "stage": int(meta["stage"]),
            "base_templates": bases,
            "slot": slot,
            "token": f"{slot}:{kind}:{room_id}",
            "expires_at": (slot + 1) * EVENT_ROTATION_SECONDS,
        })
    return tuple(result)


def _rank_stage(stage: int, rank: str) -> int:
    offsets = {"normal": 0, "elite": 4, "rare": 8, "mini": 14, "boss": 20, "world_boss": 26}
    return max(1, min(600, int(stage) + offsets.get(str(rank), 0)))


def generated_name(base_name: str, seed: str, role: str = "event") -> str:
    epithet = EPITHETS[_hash_int(seed, role, base_name) % len(EPITHETS)]
    if role == "nemesis":
        return f"{base_name}, {epithet} — NEMESIS"
    if role == "boss":
        return f"{base_name}, {epithet}"
    return f"{epithet} {base_name}"


def build_event_template(event: dict, index: int, mob_templates: dict, generator_core, world_seed: str):
    bases = tuple(event.get("base_templates") or ())
    if not bases:
        return None, None
    pick = _hash_int(world_seed, event["token"], index, "base") % len(bases)
    base_id = bases[pick]
    base = mob_templates.get(base_id)
    if not isinstance(base, dict):
        return None, None
    rank = str(event.get("rank") or "normal")
    stage = _rank_stage(int(event.get("stage", 1) or 1), rank)
    template_id = f"v029_event_{event['slot']}_{event['type']}_{index}_{hashlib.sha1(base_id.encode()).hexdigest()[:8]}"
    if template_id in mob_templates:
        return template_id, mob_templates[template_id]
    data = copy.deepcopy(base)
    data["base_template"] = base_id
    data["v029_dynamic_event"] = True
    data["v029_event_token"] = event["token"]
    data["generator_level"] = stage
    data["auto_aggro"] = False
    data["stationary_mob"] = rank in ("mini", "boss", "world_boss")
    if rank == "elite":
        data["name"] = generated_name(str(base.get("name", base_id)), event["token"] + str(index), "elite")
        affix, text = ELITE_AFFIXES[_hash_int(world_seed, event["token"], index, "affix") % len(ELITE_AFFIXES)]
        data["elite_affix"] = affix
        data["elite_affix_text"] = text
    elif rank == "rare":
        data["name"] = generated_name(str(base.get("name", base_id)), event["token"] + str(index), "rare")
        data["rare_mob"] = True
    else:
        data["name"] = generated_name(str(base.get("name", base_id)), event["token"] + str(index), "boss")
        if rank == "mini":
            data["mini_boss"] = True
            affix, text = ELITE_AFFIXES[_hash_int(world_seed, event["token"], index, "mini-affix") % len(ELITE_AFFIXES)]
            data["elite_affix"] = affix
            data["elite_affix_text"] = "Czempion: " + text
        else:
            mechanic, text = BOSS_MECHANICS[_hash_int(world_seed, event["token"], index, "mechanic") % len(BOSS_MECHANICS)]
            data["boss_mechanic"] = mechanic
            data["boss_mechanic_text"] = "Proceduralny boss v0.29. " + text + " Fazy 75/50/25%."
            if rank == "world_boss":
                data["world_boss"] = True
                data["v029_world_boss"] = True
    generator_core.runtime_mob_balance(template_id, data, stage, rank=rank)
    mob_templates[template_id] = data
    return template_id, data


def nemesis_name(base_name: str, account_id: int, player_name: str, rank: int) -> str:
    seed = f"nemesis:{account_id}:{player_name}:{rank}:{base_name}"
    return generated_name(base_name, seed, "nemesis")


def build_nemesis_template(record, mob_templates: dict, generator_core):
    base_id = str(record["base_template_id"])
    base = mob_templates.get(base_id)
    if not isinstance(base, dict):
        return None, None
    rank_no = max(1, int(record["rank"]))
    if rank_no >= 7:
        rank = "world_boss"
    elif rank_no >= 4:
        rank = "boss"
    elif rank_no >= 2:
        rank = "mini"
    else:
        rank = "rare"
    stage = max(1, min(600, int(record["level"])))
    template_id = f"v029_nemesis_{int(record['account_id'])}_{rank_no}_{hashlib.sha1(base_id.encode()).hexdigest()[:8]}"
    if template_id in mob_templates:
        return template_id, mob_templates[template_id]
    data = copy.deepcopy(base)
    data["base_template"] = base_id
    data["name"] = str(record["nemesis_name"])
    data["v029_nemesis"] = True
    data["v029_nemesis_owner_account_id"] = int(record["account_id"])
    data["v029_nemesis_rank"] = rank_no
    data["generator_level"] = stage
    data["auto_aggro"] = False
    data["stationary_mob"] = True
    if rank in ("boss", "world_boss"):
        mechanic, text = BOSS_MECHANICS[_hash_int(str(record["account_id"]), base_id, rank_no, "nemesis-mechanic") % len(BOSS_MECHANICS)]
        data["boss_mechanic"] = mechanic
        data["boss_mechanic_text"] = f"Nemesis rangi {rank_no}. {text} Fazy 75/50/25%."
        data["world_boss"] = rank == "world_boss"
    elif rank == "mini":
        data["mini_boss"] = True
        affix, text = ELITE_AFFIXES[_hash_int(str(record["account_id"]), base_id, rank_no, "nemesis-affix") % len(ELITE_AFFIXES)]
        data["elite_affix"] = affix
        data["elite_affix_text"] = f"Nemesis rangi {rank_no}: {text}"
    else:
        data["rare_mob"] = True
    generator_core.runtime_mob_balance(template_id, data, stage, rank=rank)
    mob_templates[template_id] = data
    return template_id, data

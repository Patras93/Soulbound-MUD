# -*- coding: utf-8 -*-
"""v1.19.0: opt-in secret chambers on pre-existing instance secret floors.

No trap rolls and no dungeon-floor shortcuts.  The instance secret map remains
canonical; generated chamber and archive rooms are deterministic and rehydratable.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from data import catalog_mutations as _catalog_mut

SECRET_ROOM_PATTERN_V1190 = re.compile(r"^v1190_(chamber|archive|vault)_([a-z_]+)_(\d+)$")
SECRET_GUARD_NAMES_V1190 = (
    "Strażnik Zapomnianych Pieczęci",
    "Widmowy Kustosz Skarbca",
    "Milczący Strażnik Kronik",
    "Opiekun Ukrytego Sanktuarium",
)
SECRET_ARCHIVISTS_V1190 = (
    ("Archiwistka Neria", "Każde miejsce ma drugą historię. Nie wszystkie drzwi prowadzą w głąb; czasem droga powrotna jest sekretem."),
    ("Wędrowiec Aldren", "Pamiętaj o tym piętrze. Kroniki świata zapisują ślady, nie pułapki."),
    ("Kartografka Ilyra", "Zaznacz odkrycie na mapie. Po skarb wracaj dopiero po pokonaniu strażnika."),
    ("Kronikarz Miron", "Nawet najgłębszy loch ma boczną opowieść. Z sekretnej sali możesz bezpiecznie wrócić."),
)


def secret_room_id_v1190(kind, floor, role="chamber"):
    if role not in ("chamber", "archive", "vault"):
        raise ValueError("Unknown world-secret room type")
    return f"v1190_{role}_{kind}_{int(floor)}"


def secret_room_identity_v1190(room_id):
    match = SECRET_ROOM_PATTERN_V1190.fullmatch(str(room_id or ""))
    if not match:
        return None
    role, kind, floor = match.groups()
    number = int(floor)
    if number < 1:
        return None
    return role, kind, number


def world_secret_roll_v1190(room_id, date):
    """One stable, uncommon calendar-day encounter per archive."""
    stamp = date.isoformat() if hasattr(date, "isoformat") else str(date)
    digest = hashlib.sha256(f"soulbound:1190:rare:{room_id}:{stamp}".encode()).digest()
    return digest[0] % 5 == 0


def world_secret_guard_template_v1190(kind, floor, parent, spawns, mob_templates):
    """Prefer a monster actually native to the same floor, never another boss."""
    candidates = []
    for room_id, mob_id in spawns:
        if room_id != parent and not str(room_id).startswith(f"{parent}_r"):
            continue
        mob = mob_templates.get(mob_id)
        if not isinstance(mob, dict) or any(mob.get(flag) for flag in (
            "crypt_boss", "mythic_crypt_boss", "astral_boss",
            "mythic_astral_boss", "giant_fortress_boss", "uoss_unique_superboss_key"
        )):
            continue
        candidates.append(mob_id)
    if not candidates:
        # Mining floors are resource-only by design; give their *new* secret
        # chamber a dedicated passive guard without touching mining spawns.
        fallback = "goblin_cave_guard" if "goblin_cave_guard" in mob_templates else "goblin"
        if fallback not in mob_templates:
            return None
        candidates = [fallback]
    source_id = candidates[floor % len(candidates)]
    template_id = f"v1190_guard_{kind}_{floor}"
    if template_id not in mob_templates:
        base = dict(mob_templates[source_id])
        base["name"] = SECRET_GUARD_NAMES_V1190[floor % len(SECRET_GUARD_NAMES_V1190)]
        base["max_hp"] = max(1, int(base.get("max_hp", 1) or 1) * 2)
        base["base_max_hp"] = base["max_hp"]
        base["damage"] = max(1, int(int(base.get("damage", 1) or 1) * 1.25))
        base["auto_aggro"] = False
        base["stationary_mob"] = True
        base["mini_boss"] = True
        base["v1190_secret_guard"] = True
        base["quest_target"] = ""
        _catalog_mut.catalog_assign(base, 'MOB_TEMPLATES', mob_templates, (template_id,))
    return template_id


def create_world_secret_rooms_v1190(kind, floor, parent, rooms, chests, chest_catalog, npcs, spawns, mobs):
    """Idempotent catalog registration; caller verifies canonical secret floor."""
    chamber = secret_room_id_v1190(kind, floor)
    archive = secret_room_id_v1190(kind, floor, "archive")
    if parent not in rooms:
        return None, ()
    parent_room = rooms[parent]
    zone = str(parent_room.get("zone", "Nieznana kraina"))
    room_stage = max(1, int(parent_room.get("recommended_mastery", parent_room.get("generator_level", 1)) or 1))
    if chamber not in rooms:
        _catalog_mut.catalog_assign({
            "zone": f"Sekret: {zone}",
            "name": f"Komnata Zapomnianej Pieczęci — {zone}",
            "desc": "Za szczeliną odkrywasz komnatę strażnika. Skarbiec znajduje się tutaj, nie przy zejściu na kolejne piętro. Na wschodzie jest przejście do archiwum.",
            "exits": {"down": parent, "east": archive},
            "generated_on_demand": True, "v1190_secret_role": "chamber",
            "v1190_secret_parent": parent, "recommended_mastery": room_stage,
        }, 'ROOMS', rooms, (chamber,))
    if archive not in rooms:
        _catalog_mut.catalog_assign({
            "zone": f"Sekret: {zone}",
            "name": f"Archiwum Szeptów — {zone}",
            "desc": "Ciche archiwum ukrywa fragment dawnej historii. Na zachodzie wrócisz do komnaty, a w dół prowadzi alternatywne wyjście na to samo piętro, bez pomijania bossów.",
            "exits": {"west": chamber, "down": parent},
            "generated_on_demand": True, "v1190_secret_role": "archive",
            "v1190_secret_parent": parent, "recommended_mastery": room_stage,
        }, 'ROOMS', rooms, (archive,))
    if chamber not in chests:
        chests[chamber] = {
            "name": f"Skarbiec Zapomnianej Pieczęci — {zone}", "respawn": 86400,
            "base_pool": ("soul_shard", "soul_elixir"),
            "set_pool": (),
        }
    chest_catalog[chamber] = chests[chamber]["name"]
    name, dialogue = SECRET_ARCHIVISTS_V1190[floor % len(SECRET_ARCHIVISTS_V1190)]
    npc_id = f"v1190_archivist_{kind}_{floor}"
    if npc_id not in npcs:
        _catalog_mut.catalog_assign({"name": name, "room": archive, "dialogue": dialogue},
                                    'NPCS', npcs, (npc_id,))
    guard = world_secret_guard_template_v1190(kind, floor, parent, spawns, mobs)
    additional_spawns = []
    # v1.25: a fraction of existing scripted secret floors contains a further,
    # boss-guarded treasury. Secret floors use e.g. 317/337/367/387, never
    # multiples of five; choose by their ten-floor index instead.
    if floor >= 10 and (floor // 10) % 4 == 3:
        vault = secret_room_id_v1190(kind, floor, 'vault')
        if vault not in rooms:
            _catalog_mut.catalog_assign({
                "zone": f"Sekret: {zone}",
                "name": f"Zakazany Skarbiec — {zone}",
                "desc": "W zapieczętowanej komnacie odkrywasz dawny skarbiec i ślady zapomnianych receptur. Powrót prowadzi na południe. Nie ma pułapek.",
                "exits": {"south": archive},
                "generated_on_demand": True, "v1190_secret_role": "vault",
                "v1190_secret_parent": parent, "recommended_mastery": room_stage,
            }, 'ROOMS', rooms, (vault,))
        archive_room = rooms[archive]
        if 'north' not in archive_room.get('exits', {}):
            exits = dict(archive_room.get('exits') or {})
            exits['north'] = vault
            _catalog_mut.catalog_assign(exits, 'ROOMS', rooms, (archive, 'exits'))
        if vault not in chests:
            chests[vault] = {
                "name": f"Skarbiec Zapomnianych Mistrzów — {zone}",
                "respawn": 86400,
                "base_pool": ("soul_shard", "soul_elixir", "mithril_ore"),
                "set_pool": (),
            }
        chest_catalog[vault] = chests[vault]['name']
        vault_guard = world_secret_guard_template_v1190('vault_' + kind, floor, parent, spawns, mobs)
        if vault_guard:
            # Separate guardian per vault; remains a real miniboss of its room.
            vault_template = mobs[vault_guard]
            if not vault_template.get('v1250_vault_guard'):
                # Keep each generated guardian name short, pronounceable and unique
                # across floors. Dynamic mobs are generated after the startup
                # name-cleanup pass, so names must already satisfy NVDA audits.
                digest = hashlib.sha256(f"{kind}:{floor}:vault".encode()).digest()
                consonants, vowels = "bcdfghjklmnprstvz", "aeiouy"
                unique = "".join(consonants[digest[i] % len(consonants)] +
                                 vowels[digest[i + 1] % len(vowels)]
                                 for i in range(0, 10, 2)).capitalize()
                vault_template['name'] = f"Strażnik Receptur {unique}"
                vault_template['max_hp'] = max(1, int(vault_template['max_hp'] * 1.6))
                vault_template['damage'] = max(1, int(vault_template['damage'] * 1.25))
                vault_template['v1250_vault_guard'] = True
            additional_spawns.append((vault, vault_guard))
    return chamber, (((chamber, guard),) if guard else ()) + tuple(additional_spawns)


def attach_surface_secret_npc_v1190(room_id, rooms, npcs):
    """Enrich pre-existing frontier secret chambers without changing their loot."""
    room = rooms.get(str(room_id or ""))
    if not room or not room.get("v0140_secret_room"):
        return False
    index = hashlib.sha256(str(room_id).encode()).digest()[0] % len(SECRET_ARCHIVISTS_V1190)
    name, dialogue = SECRET_ARCHIVISTS_V1190[index]
    npc_id = f"v1190_surface_npc_{room_id}"
    if npc_id not in npcs:
        _catalog_mut.catalog_assign({
            "name": name, "room": room_id,
            "dialogue": dialogue + " W tej kryjówce mogą pojawiać się rzadkie wydarzenia. Wpisz sekret wydarzenie.",
        }, 'NPCS', npcs, (npc_id,))
    return True

# -*- coding: utf-8 -*-
"""Runtime helpers for unique UOSSMUD superboss encounters (v1.11.35).

This module deliberately uses the existing collection_entries persistence for
per-account clears/lockouts. No new SQLite migration is required.
"""
import random
import world.uoss_superboss_world as _uoss_superboss_world_v11136
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

SUPERBOSS_COLLECTION_V11135 = "uoss_superboss_clears_v11135"
SUPERBOSS_REWARD_COLLECTION_V11135 = "uoss_superboss_rewards_v11135"

SUPERBOSS_TOKEN_ITEMS_V11135 = {
    "black_rabite": ("uoss_moogle_steel", "Moogle Steel"),
    "serpentarius": ("uoss_serpentarius_emblem", "Serpentarius Emblem"),
    "yiazmat": ("uoss_godslayers_badge", "Godslayer's Badge"),
}

BLACK_RABITE_UNIQUE_DROPS_V11135 = tuple(f"uoss_black_rabite_unique_{i}" for i in range(1, 11))
YIAZMAT_UNIQUE_DROPS_V11135 = tuple(f"uoss_yiazmat_unique_{i}" for i in range(1, 8))


def superboss_key_from_template_v11135(template):
    if not isinstance(template, dict):
        return None
    key = str(template.get("uoss_unique_superboss_key") or "")
    return key if key in UOSS_SUPERBOSS_ENCOUNTERS_V11134 else None


def superboss_cleared_v11135(db, account_id, boss_key):
    return str(boss_key) in db.collection_entry_ids(account_id, SUPERBOSS_COLLECTION_V11135)


def mark_superboss_clear_v11135(db, account_id, boss_key):
    return db.add_collection_entry(account_id, SUPERBOSS_COLLECTION_V11135, str(boss_key))


def superboss_personal_reward_v11135(db, account_id, boss_key):
    row = SUPERBOSS_TOKEN_ITEMS_V11135.get(str(boss_key))
    if not row:
        return None
    item_id, label = row
    marker = f"{boss_key}:token"
    if not db.add_collection_entry(account_id, SUPERBOSS_REWARD_COLLECTION_V11135, marker):
        return None
    db.add_item(account_id, item_id, 1)
    return item_id, label


def superboss_shared_drop_v11135(db, recipients, boss_key):
    pool = {
        "black_rabite": BLACK_RABITE_UNIQUE_DROPS_V11135,
        "yiazmat": YIAZMAT_UNIQUE_DROPS_V11135,
    }.get(str(boss_key))
    if not pool or not recipients:
        return None
    eligible = []
    for item_id in pool:
        if any(item_id not in s.server.db.collection_entry_ids(s.account_id, "equipment") for s in recipients):
            eligible.append(item_id)
    item_id = random.choice(eligible or pool)
    # Shared boss drop: exactly one copy for the party. Give it deterministically
    # to the first local participant who does not have it; otherwise party leader/killer order.
    winner = next((s for s in recipients if item_id not in s.server.db.collection_entry_ids(s.account_id, "equipment")), recipients[0])
    db.add_item(winner.account_id, item_id, 1)
    return winner, item_id


def superboss_local_party_v11137(session):
    members = session.server.party_sessions(session.account_id, same_room=session.character.room_id)
    return list(members) if members else [session]


def superboss_attack_gate_v11137(session, template):
    key = superboss_key_from_template_v11135(template)
    if not key:
        return True, ""
    spec = UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]
    party = superboss_local_party_v11137(session)
    mode = str(spec.get("mode", "solo"))
    if mode == "solo" and len(party) > 1:
        return False, f"{spec['name']} jest wyzwaniem solo. Opuść drużynę albo walcz sam."
    if mode == "party" and len(party) < 2:
        return False, f"{spec['name']} jest wyzwaniem drużynowym. Potrzebujesz co najmniej 2 graczy."
    level_req = int(spec.get("unlock_level", 0) or 0)
    for member in party:
        if level_req and int(member.character.character_level) < level_req:
            return False, f"{member.character.name} nie spełnia wymogu Level {level_req} dla {spec['name']}."
    if spec.get("party_members_must_unlock"):
        for member in party:
            unlocked = bool(member.server.db.collection_entry_ids(member.account_id, "deep_dungeon_discovery"))
            if not unlocked:
                return False, f"{member.character.name} nie odblokował jeszcze Serpentariusa przez eksplorację Deep Dungeon."
    if superboss_cleared_v11135(session.server.db, session.account_id, key) and spec.get("once_per_cycle"):
        return False, f"{spec['name']} jest już przez ciebie zaliczony w trwałym cyklu."
    return True, ""


def superboss_helper_profile_v11137(session, template):
    key = superboss_key_from_template_v11135(template)
    if not key:
        return None
    spec = UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]
    party = superboss_local_party_v11137(session)
    if len(party) > int(spec.get("helper_max_players", 0) or 0):
        return None
    helpers = spec.get("helpers")
    helper = spec.get("helper")
    if helpers:
        # Black Rabite: exactly one helper; default is Primm until an explicit
        # chooser command is added, never both.
        name = tuple(helpers)[0]
    elif helper:
        name = str(helper)
    else:
        return None
    return {"name":name, "damage_multiplier":1.12, "damage_reduction":0.08}


def superboss_phase_v11137(template, mob):
    key = superboss_key_from_template_v11135(template)
    if not key:
        return None
    max_hp = max(1, int(template.get("max_hp", 1)))
    pct = max(0.0, min(1.0, float(mob.hp) / max_hp))
    if pct <= 0.25:
        return 3
    if pct <= 0.60:
        return 2
    return 1


def superboss_counterattack_multiplier_v11137(template, mob):
    phase = superboss_phase_v11137(template, mob)
    if phase is None:
        return 1.0, ""
    key = superboss_key_from_template_v11135(template)
    if key == "spekkio":
        return 1.0, "Spekkio dopasowuje siłę do przeciwnika."
    if phase == 3:
        return 1.55, "Faza 3: desperacki atak Super Bossa."
    if phase == 2:
        return 1.25, "Faza 2: Super Boss zwiększa napór."
    return 1.0, "Faza 1."

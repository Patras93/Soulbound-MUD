# -*- coding: utf-8 -*-
"""Runtime helpers for unique UOSSMUD superboss encounters (v1.11.35).

This module deliberately uses the existing collection_entries persistence for
per-account clears/lockouts. No new SQLite migration is required.
"""
import random
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

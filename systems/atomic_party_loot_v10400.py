# -*- coding: utf-8 -*-
"""Atomic loot settlement for an entire set of rolls from one defeated mob.

A *roll* is one item with a fixed party of eligible recipients.  Stage RNG
and conversions before calling this module; do not send network messages or
write codex/collection events while the SAVEPOINT is open.  The inventory and
craftbox portion of all rolls commits together or not at all.
"""
from __future__ import annotations

from collections import Counter

from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
from storage.db_inventory import is_craft_material_storage_item


def _validate_roll(roll):
    if not isinstance(roll, (tuple, list)) or len(roll) != 4:
        raise ValueError('Nieprawidlowa definicja losowania lupu.')
    recipients, item_id, craftbox, craftbox_item_id = roll
    if not isinstance(item_id, str) or not item_id:
        raise ValueError('Nieprawidlowy przedmiot.')
    if type(craftbox) is not bool:
        raise ValueError('Nieprawidlowa flaga craftbox.')
    if craftbox_item_id is not None and (not craftbox or
            not isinstance(craftbox_item_id, str) or not craftbox_item_id):
        raise ValueError('Nieprawidlowy przedmiot craftbox.')
    ids = []
    for recipient in recipients:
        acc = getattr(recipient, 'account_id', recipient if type(recipient) is int else None)
        if type(acc) is not int or acc <= 0:
            raise ValueError('Nieprawidlowy odbiorca lupu.')
        ids.append(acc)
    if len(ids) != len(set(ids)):
        raise ValueError('Powtorzone konto w jednym losowaniu lupu.')
    uses_storage = craftbox or is_craft_material_storage_item(item_id)
    return tuple(ids), item_id, uses_storage, craftbox_item_id or item_id


def grant_party_loot_batch_atomic_v10400(db, rolls):
    """Grant *all* item rolls of one kill in one synchronous SQLite SAVEPOINT.

    ``rolls`` is an ordered iterable of (recipients, item_id, craftbox,
    craftbox_item_id).  Different rolls may include the same item and member:
    aggregate quantities are validated *before* any write.  Returns one
    tuple of account IDs for each supplied roll, including empty rolls.

    This does not cover preceding XP, later codex/collection side effects,
    quest progression, or resuming a previously committed kill.
    """
    if db is None or not hasattr(getattr(db, 'conn', None), 'deferred_commits'):
        raise TypeError('Oczekiwano bazy Soulbound z odroczonym COMMIT.')
    prepared = tuple(_validate_roll(roll) for roll in rolls)
    if not prepared:
        return ()
    conn = db.conn
    # (inventory/craftbox, account_id, stored item_id): aggregate multiple
    # independent successful rolls of the same item before checking int64.
    totals = Counter()
    for ids, item_id, storage, stored_id in prepared:
        for account_id in ids:
            totals[(storage, account_id, stored_id if storage else item_id)] += 1
    if not totals:
        return tuple(ids for ids, _, _, _ in prepared)
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v104_atomic_kill_loot_batch')
        try:
            for (storage, account_id, item_id), increment in totals.items():
                if storage:
                    row = conn.execute(
                        'SELECT quantity FROM profession_storage WHERE account_id=? AND container=? AND item_id=?',
                        (account_id, 'craftbox', item_id)).fetchone()
                else:
                    row = conn.execute(
                        'SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',
                        (account_id, item_id)).fetchone()
                quantity = row[0] if row is not None else 0
                if type(quantity) is not int or quantity < 0:
                    raise ValueError('Nieprawidlowa liczba przedmiotow w bazie.')
                require_sqlite_int64('loot.quantity', quantity + increment)
            for ids, item_id, storage, stored_id in prepared:
                for account_id in ids:
                    if storage:
                        db.add_storage_item(account_id, 'craftbox', stored_id, 1,
                                            commit=False)
                    else:
                        db.add_item(account_id, item_id, 1, commit=False)
            conn.execute('RELEASE SAVEPOINT v104_atomic_kill_loot_batch')
        except BaseException:
            conn.execute('ROLLBACK TO SAVEPOINT v104_atomic_kill_loot_batch')
            conn.execute('RELEASE SAVEPOINT v104_atomic_kill_loot_batch')
            raise
    return tuple(ids for ids, _, _, _ in prepared)


def grant_party_loot_atomic_v10400(db, recipients, item_id, *,
                                    craftbox=False, craftbox_item_id=None):
    """Backward-compatible single-roll helper; still entirely atomic."""
    return grant_party_loot_batch_atomic_v10400(
        db, [(recipients, item_id, craftbox, craftbox_item_id)])[0]

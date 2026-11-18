# -*- coding: utf-8 -*-
"""v115 Fame ledger integration primitive, not hooked into combat yet.

Only fame can be settled by this bridge. Character/Soul/class/stat EXP must
first receive an atomic same-connection award adapter before production hookup.
"""
from __future__ import annotations
from systems.v115 import fame_queue


def queue_first_clear(conn, account_id, region, boss_id, boss_name, reward_xp, *, now=None):
    """Stage a real first-clear, without inserting into the legacy fame ledger.

    Caller must use canonical identity and real eligible recipients checked by
    systems.fame_v1702; do not use this as an eligibility shortcut.
    """
    fame_queue.ensure_schema(conn)
    # Historical awards must not be queued a second time.
    already = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fame_bosses_v1702'"
    ).fetchone()
    if already and conn.execute(
        'SELECT 1 FROM fame_bosses_v1702 WHERE account_id=? AND region=? AND boss_id=?',
        (int(account_id), str(region), str(boss_id))
    ).fetchone():
        return False
    return fame_queue.schedule_fame(conn, account_id, region, boss_id, boss_name,
                                    reward_xp=reward_xp, now=now)


def settle_legacy_fame(conn, account_id, region, boss_id, *, now=None):
    """Write first Fame into the exact legacy table, in the queue's savepoint.

    Never call until EXP was durably settled in the same authoritative store.
    The caller must commit transaction before sending SOUND_EVENT or text.
    """
    def award(db, points):
        if points != 1:
            raise ValueError('Legacy Fame ledger records one point per first-clear')
        db.execute("""CREATE TABLE IF NOT EXISTS fame_bosses_v1702 (
            account_id INTEGER NOT NULL,boss_id TEXT NOT NULL,region TEXT NOT NULL,
            first_defeated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(account_id,region,boss_id))""")
        db.execute('INSERT OR IGNORE INTO fame_bosses_v1702(account_id,boss_id,region) VALUES (?,?,?)',
                   (int(account_id),str(boss_id),str(region)))
    return fame_queue.settle_fame(conn, int(account_id), str(region), str(boss_id),
                                  award, now=now)

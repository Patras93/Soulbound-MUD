# -*- coding: utf-8 -*-
"""v106 STAGING: crash-detection journal for non-atomic craft side effects.

The item/material/mastery transaction is atomic.  Quest, XP, collection and
achievement APIs still commit independently and may mutate in-memory state.
This journal NEVER replays an uncertain grant: it blocks subsequent crafting
until a human audits the disposable copy.  It does NOT claim full atomicity.
"""
from __future__ import annotations

import re
from systems.equipment_crafting_guard_v10600 import active

STAGES = ('output', 'collections', 'quest', 'guild', 'xp', 'complete')
_TOKEN = re.compile(r'^[a-f0-9]{32}$')


def _conn(db):
    if not active(db):
        raise PermissionError('v106: dziennik nagród tylko na oznaczonej kopii testowej')
    conn = db.conn
    conn.execute('''CREATE TABLE IF NOT EXISTS v106_craft_reward_journal (
        run_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL,
        recipe_id TEXT NOT NULL,
        base_item_id TEXT NOT NULL,
        output_id TEXT NOT NULL,
        output_qty INTEGER NOT NULL CHECK(output_qty > 0),
        stage TEXT NOT NULL DEFAULT 'output',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''CREATE INDEX IF NOT EXISTS idx_v106_craft_pending
        ON v106_craft_reward_journal(account_id,stage)''')
    return conn


def pending(db, account_id):
    conn = _conn(db)
    return conn.execute('''SELECT run_id,recipe_id,stage FROM v106_craft_reward_journal
        WHERE account_id=? AND stage!='complete' ORDER BY created_at,run_id LIMIT 1''',
        (int(account_id),)).fetchone()


def assert_ready(db, account_id):
    row = pending(db, account_id)
    if row is not None:
        raise RuntimeError(
            'v106: wstrzymano nowe rzemiosło. Niedokończone rozliczenie '
            f'receptury {row[1]}, etap {row[2]}, kod {row[0][:8]}. '
            'Nie powtarzaj jej i nie dopisuj nagród automatycznie. '
            'Wymagany audyt na kopii SQLite.'
        )


def begin_in_savepoint(db, account_id, run_id, recipe_id, base_item_id, output_id, output_qty):
    """Call ONLY inside the same SAVEPOINT that mints the physical output."""
    if not isinstance(run_id,str) or _TOKEN.fullmatch(run_id) is None:
        raise ValueError('v106: błędny identyfikator wykonania receptury')
    for value in (recipe_id,base_item_id,output_id):
        if not isinstance(value,str) or not value or len(value)>128:
            raise ValueError('v106: nieprawidłowy identyfikator produktu lub receptury')
    assert_ready(db, account_id)
    _conn(db).execute('''INSERT INTO v106_craft_reward_journal
        (run_id,account_id,recipe_id,base_item_id,output_id,output_qty,stage)
        VALUES(?,?,?,?,?,?,'output')''',
        (run_id,int(account_id),recipe_id,base_item_id,output_id,int(output_qty)))


def checkpoint(db, account_id, run_id, next_stage):
    """Advance only one step; never automatically retry external side effects.

    If an external API commits, but the process dies before checkpointing,
    stage remains PREVIOUS/UNCERTAIN. Manual review is required.
    """
    if next_stage not in STAGES[1:]:
        raise ValueError('v106: nieznany etap rozliczenia')
    conn=_conn(db)
    row=conn.execute('''SELECT stage FROM v106_craft_reward_journal
        WHERE run_id=? AND account_id=?''', (run_id,int(account_id))).fetchone()
    if row is None:
        raise RuntimeError('v106: nie znaleziono wykonania receptury')
    old=row[0]
    if old not in STAGES or STAGES.index(next_stage)!=STAGES.index(old)+1:
        raise RuntimeError('v106: niedozwolone ponowienie lub pominięcie nagrody')
    changed=conn.execute('''UPDATE v106_craft_reward_journal SET stage=?,
        updated_at=CURRENT_TIMESTAMP
        WHERE run_id=? AND account_id=? AND stage=?''',
        (next_stage,run_id,int(account_id),old)).rowcount
    if changed!=1:
        raise RuntimeError('v106: zapis etapu craftingu nie powiódł się')
    conn.commit()


def audit_pending(db, account_id):
    """Read-only report for an administrator. Does not grant or repair anything."""
    return pending(db,account_id)

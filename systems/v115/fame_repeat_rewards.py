# -*- coding: utf-8 -*-
"""Zgodnościowe wypłaty EXP za ponowne Fame zabicia sprzed v116.00.47.

Od v116.00.47 normalny EXP z powtórki trafia natychmiast przy zabiciu.
Nie wolno usuwać ani ignorować wcześniejszych, już zakolejkowanych nagród.
Moduł pozostaje do ich trwałego, jednokrotnego rozliczenia po aktualizacji.
"""
from __future__ import annotations

import copy
import json
import time
import uuid

from systems.v115.fame_queue import MIN_DELAY_SECONDS, MAX_DELAY_SECONDS
from systems.v115.fame_reward_snapshot import RewardSnapshot


def ensure_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS v115_fame_repeat_exp (
        kill_token TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL,
        character_name TEXT NOT NULL,
        region TEXT NOT NULL,
        boss_id TEXT NOT NULL,
        boss_name TEXT NOT NULL,
        snapshot TEXT NOT NULL,
        due_at REAL NOT NULL,
        created_at REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING'
           CHECK(status IN ('PENDING','DONE'))
    )''')
    conn.execute('''CREATE INDEX IF NOT EXISTS v115_fame_repeat_due_idx
        ON v115_fame_repeat_exp(account_id,status,due_at)''')


def stage_repeat_exp(conn, account_id, region, boss_id, boss_name, plan, *, now=None, kill_token=None):
    """Append one real kill to an active combat transaction, never credit EXP."""
    if type(account_id) is not int or account_id <= 0:
        raise ValueError('Authenticated account required')
    if not isinstance(plan, RewardSnapshot):
        raise TypeError('Final Multi Cap reward snapshot required')
    plan.validate()
    if not plan.character_name:
        raise ValueError('A repeat EXP reward must belong to one named character')
    if not str(region).strip() or not str(boss_id).strip():
        raise ValueError('Canonical Fame mob identity required')
    now = time.time() if now is None else float(now)
    token = uuid.uuid4().hex if kill_token is None else str(kill_token)
    if not token or len(token) > 128:
        raise ValueError('Invalid kill token')
    # Each kill gets a separate row. A retry with the same token is harmless,
    # but conflicting replay payloads are fatal rather than silently replaced.
    delay = MIN_DELAY_SECONDS + int(uuid.UUID(token).int % (MAX_DELAY_SECONDS-MIN_DELAY_SECONDS+1)) if len(token)==32 else MIN_DELAY_SECONDS
    ensure_schema(conn)
    payload = plan.payload()
    old = conn.execute('''SELECT account_id,character_name,region,boss_id,snapshot
        FROM v115_fame_repeat_exp WHERE kill_token=?''', (token,)).fetchone()
    expected = (account_id, plan.character_name, str(region), str(boss_id), payload)
    if old is not None:
        if tuple(old) != expected:
            raise ValueError('Conflicting repeated kill event')
        return token, False
    conn.execute('''INSERT INTO v115_fame_repeat_exp
        (kill_token,account_id,character_name,region,boss_id,boss_name,snapshot,due_at,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)''',
        (token, account_id, plan.character_name, str(region), str(boss_id),
         str(boss_name), payload, now + delay, now))
    return token, True


def pending_online_accounts(conn, *, now=None):
    """Return only accounts with a due repeat EXP, without schema changes."""
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='v115_fame_repeat_exp'").fetchone()
    if not exists:
        return set()
    now = time.time() if now is None else float(now)
    return {int(r[0]) for r in conn.execute(
        "SELECT DISTINCT account_id FROM v115_fame_repeat_exp WHERE status='PENDING' AND due_at<=?", (now,))}


def due_repeats(conn, account_id, character_name, *, now=None, limit=20):
    """No DDL or mutation while querying already initialized tables."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='v115_fame_repeat_exp'").fetchone():
        return []
    now = time.time() if now is None else float(now)
    return conn.execute('''SELECT kill_token,boss_name FROM v115_fame_repeat_exp
        WHERE account_id=? AND character_name=? AND status='PENDING' AND due_at<=?
        ORDER BY due_at,kill_token LIMIT ?''',
        (int(account_id), str(character_name), now, max(1, min(int(limit), 100)))).fetchall()


def _restore_character(character, saved):
    character.__dict__.clear()
    character.__dict__.update(saved)


def settle_repeat_exp(db, character, account_id, token, *, now=None):
    """Award repeat EXP exactly once, on SAME SQLite connection and savepoint."""
    if (db is None or character is None or type(account_id) is not int
            or getattr(character, 'account_id', None) != account_id):
        raise ValueError('Recipient mismatch')
    conn = db.conn
    if not callable(getattr(conn, 'deferred_commits', None)):
        raise TypeError('Deferred SQLite transaction required')
    now = time.time() if now is None else float(now)
    before = copy.deepcopy(character.__dict__)
    try:
        with conn.deferred_commits():
            conn.execute('SAVEPOINT v115_repeat_payout')
            try:
                row = conn.execute('''SELECT account_id,character_name,snapshot,due_at,status
                    FROM v115_fame_repeat_exp WHERE kill_token=?''',(str(token),)).fetchone()
                if row is None or row[4]!='PENDING' or row[3]>now:
                    conn.execute('RELEASE SAVEPOINT v115_repeat_payout')
                    return None
                if row[0]!=account_id or row[1]!=getattr(character,'name',None):
                    raise ValueError('Repeat reward belongs to another character')
                data = json.loads(row[2]); plan = RewardSnapshot(
                    character_xp=data['character_xp'], soul_xp=data['soul_xp'],
                    class_xp=data['class_xp'], stat_xp=data['stat_xp'],
                    class_levels=tuple((n,l) for n,l in data['class_levels']),
                    class_max_level=data['class_max_level'],
                    overcap=data['overcap'], character_name=data.get('character_name'),
                    verified_zero=data.get('verified_zero',False)).validate()
                if plan.character_name != character.name:
                    raise ValueError('Stored snapshot belongs to another character')
                from systems.combat_kill_settlement_v10400 import settle_combat_full_progression_v10400
                paid = settle_combat_full_progression_v10400(
                    db, character, account_id, silver=0,gold=0,mithril=0,
                    character_xp=plan.character_xp, soul_xp=plan.soul_xp,
                    class_xp=plan.class_xp,stat_xp=plan.stat_xp,
                    class_levels=plan.class_levels,class_max_level=plan.class_max_level,
                    overcap=plan.overcap)
                conn.execute("UPDATE v115_fame_repeat_exp SET status='DONE' WHERE kill_token=?",(str(token),))
                conn.execute('RELEASE SAVEPOINT v115_repeat_payout')
                return paid
            except BaseException:
                conn.execute('ROLLBACK TO SAVEPOINT v115_repeat_payout')
                conn.execute('RELEASE SAVEPOINT v115_repeat_payout')
                raise
    except BaseException:
        _restore_character(character, before)
        raise

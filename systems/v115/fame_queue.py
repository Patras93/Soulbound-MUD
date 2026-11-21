# -*- coding: utf-8 -*-
"""Durable Fame bonus/Fame delivery; preserve legacy queued ordinary EXP.

This is a persistence/settlement primitive, not a replacement for character XP
APIs. A host award callback MUST write through the SAME SQLite connection and
MUST NOT commit independently. The host must commit before notifying clients.
"""
from __future__ import annotations
import hashlib
import time

MIN_DELAY_SECONDS = 60
MAX_DELAY_SECONDS = 300
FAME_GAP_SECONDS = 2


def deterministic_delay(account_id: int, region: str, boss_id: str) -> int:
    payload = f'{int(account_id)}|{region}|{boss_id}'.encode('utf-8')
    return MIN_DELAY_SECONDS + int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big') % (MAX_DELAY_SECONDS - MIN_DELAY_SECONDS + 1)


def ensure_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS v115_fame_delivery (
        account_id INTEGER NOT NULL,
        region TEXT NOT NULL,
        boss_id TEXT NOT NULL,
        boss_name TEXT NOT NULL,
        due_at REAL NOT NULL,
        fame_due_at REAL,
        status TEXT NOT NULL DEFAULT 'WAITING' CHECK(status IN ('WAITING','EXP_READY','FAME_READY','DONE')),
        created_at REAL NOT NULL,
        reward_xp INTEGER NOT NULL DEFAULT 0,
        fame_points INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(account_id, region, boss_id)
    )''')
    # Upgrade staged v115 databases (not the production v114 tables).
    columns = {row[1] for row in conn.execute('PRAGMA table_info(v115_fame_delivery)')}
    if 'reward_xp' not in columns:
        conn.execute('ALTER TABLE v115_fame_delivery ADD COLUMN reward_xp INTEGER NOT NULL DEFAULT 0')
    if 'fame_points' not in columns:
        conn.execute('ALTER TABLE v115_fame_delivery ADD COLUMN fame_points INTEGER NOT NULL DEFAULT 1')
    conn.execute('CREATE INDEX IF NOT EXISTS v115_fame_due_idx ON v115_fame_delivery(account_id,status,due_at)')


def schedule_fame(conn, account_id, region, boss_id, boss_name, *, reward_xp=0, fame_points=1, now=None):
    """Queue one first-clear bonus/Fame event; never credit either here."""
    now = time.time() if now is None else float(now)
    reward_xp, fame_points = int(reward_xp), int(fame_points)
    if reward_xp < 0 or fame_points < 1:
        raise ValueError('Invalid reward amounts')
    ensure_schema(conn)
    delay = deterministic_delay(account_id, str(region), str(boss_id))
    cur = conn.execute('''INSERT OR IGNORE INTO v115_fame_delivery
        (account_id,region,boss_id,boss_name,due_at,created_at,reward_xp,fame_points)
        VALUES(?,?,?,?,?,?,?,?)''', (int(account_id),str(region),str(boss_id),str(boss_name),now+delay,now,reward_xp,fame_points))
    return bool(cur.rowcount)


def due_events(conn, account_id, *, now=None, limit=30):
    """Read currently due phases, without side effects."""
    now = time.time() if now is None else float(now)
    ensure_schema(conn)
    return conn.execute('''SELECT region,boss_id,boss_name,status,reward_xp,fame_points
        FROM v115_fame_delivery WHERE account_id=? AND
        ((status IN ('WAITING','EXP_READY') AND due_at<=?) OR
         (status='FAME_READY' AND fame_due_at<=?))
        ORDER BY CASE WHEN status='FAME_READY' THEN 0 ELSE 1 END,
                 due_at,region,boss_id LIMIT ?''',
        (int(account_id),now,now,max(1,min(int(limit),100)))).fetchall()


def _atomic_award(conn, account_id, region, boss_id, *, phase, award, now):
    """Award and advance its phase in one SQLite savepoint.

    `award(conn, reward_amount)` must be synchronous and perform all durable
    award mutations on this connection; any exception rolls back both parts.
    Calls outside this contract (e.g. awaited session methods or external DBs)
    are NOT safe and must be integrated separately.
    """
    if not callable(award):
        raise TypeError('A same-connection award callback is required')
    ensure_schema(conn)
    now = time.time() if now is None else float(now)
    conn.execute('SAVEPOINT v115_fame_award')
    try:
        row = conn.execute('''SELECT status,due_at,fame_due_at,reward_xp,fame_points
            FROM v115_fame_delivery WHERE account_id=? AND region=? AND boss_id=?''',
            (account_id, region, boss_id)).fetchone()
        if not row:
            conn.execute('RELEASE SAVEPOINT v115_fame_award')
            return False
        status, due_at, fame_due_at, reward_xp, fame_points = row
        if phase == 'exp':
            if status not in ('WAITING','EXP_READY') or due_at > now:
                conn.execute('RELEASE SAVEPOINT v115_fame_award')
                return False
            award(conn, int(reward_xp))
            conn.execute('''UPDATE v115_fame_delivery SET status='FAME_READY',fame_due_at=?
                WHERE account_id=? AND region=? AND boss_id=?''',
                (now+FAME_GAP_SECONDS, account_id, region, boss_id))
        elif phase == 'fame':
            if status != 'FAME_READY' or fame_due_at is None or fame_due_at > now:
                conn.execute('RELEASE SAVEPOINT v115_fame_award')
                return False
            award(conn, int(fame_points))
            conn.execute('''UPDATE v115_fame_delivery SET status='DONE'
                WHERE account_id=? AND region=? AND boss_id=?''',
                (account_id, region, boss_id))
        else:
            raise ValueError('Unknown delivery phase')
        conn.execute('RELEASE SAVEPOINT v115_fame_award')
        return True
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v115_fame_award')
        conn.execute('RELEASE SAVEPOINT v115_fame_award')
        raise


def settle_exp(conn, account_id, region, boss_id, award, *, now=None):
    return _atomic_award(conn, account_id, region, boss_id, phase='exp', award=award, now=now)


def settle_fame(conn, account_id, region, boss_id, award, *, now=None):
    return _atomic_award(conn, account_id, region, boss_id, phase='fame', award=award, now=now)


def mark_exp_settled(conn, account_id, region, boss_id, *, now=None):
    """Legacy transitional API: only use after a durable EXP award."""
    now = time.time() if now is None else float(now)
    ensure_schema(conn)
    cur = conn.execute('''UPDATE v115_fame_delivery SET status='FAME_READY', fame_due_at=?
        WHERE account_id=? AND region=? AND boss_id=? AND status IN ('WAITING','EXP_READY')
        AND due_at<=?''',(now+FAME_GAP_SECONDS,account_id,region,boss_id,now))
    return bool(cur.rowcount)


def mark_fame_settled(conn, account_id, region, boss_id, *, now=None):
    """Legacy transitional API: only use after a durable Fame award."""
    now = time.time() if now is None else float(now)
    ensure_schema(conn)
    cur = conn.execute('''UPDATE v115_fame_delivery SET status='DONE'
        WHERE account_id=? AND region=? AND boss_id=? AND status='FAME_READY'
        AND fame_due_at<=?''',(account_id,region,boss_id,now))
    return bool(cur.rowcount)

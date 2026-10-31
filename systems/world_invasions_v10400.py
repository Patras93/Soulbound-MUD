# -*- coding: utf-8 -*-
"""v104: shared, rotating multi-region invasions from REAL credited kills.

Uses existing regional mob templates and existing death event. Does NOT create
another combat system or award unbacked coins. Three fronts rotate every six
hours UTC. A real boss in the last region closes the invasion after all fronts
are defended. Native mob/quest rewards remain; eligible participants earn one event seal.
"""
from __future__ import annotations
import re
import time

from world.v10400_region_index import REGIONS

SLOT_SECONDS = 6 * 3600
REQUIRED_PER_FRONT = 8
REWARD_ITEM_ID = "v10400_invasion_victory_seal"
FRONT_OFFSETS = (0, 3, 6)
_ALLOWED = re.compile(r'^v10400_([a-z]+)_(mob_3|boss_2)$')
_SLUGS = tuple(region[0] for region in REGIONS)


def rotation(now=None):
    now = int(time.time()) if now is None else int(now)
    slot = now // SLOT_SECONDS
    fronts = tuple(_SLUGS[(slot + offset) % len(_SLUGS)] for offset in FRONT_OFFSETS)
    return {'slot':slot, 'fronts':fronts, 'final_boss':f'v10400_{fronts[-1]}_boss_2',
            'expires_at':(slot + 1) * SLOT_SECONDS}


def create_schema(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS world_invasion_fronts_v10400(
        slot INTEGER NOT NULL, slug TEXT NOT NULL, kills INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(slot,slug), CHECK(kills>=0))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS world_invasion_results_v10400(
        slot INTEGER PRIMARY KEY, completed_at INTEGER NOT NULL DEFAULT 0)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS world_invasion_receipts_v10400(
        slot INTEGER NOT NULL, encounter TEXT NOT NULL,
        PRIMARY KEY(slot,encounter))""")
    # All participants are recorded only after a genuinely credited kill.
    # Tokens can also be delivered to players who disconnect before the boss.
    conn.execute("""CREATE TABLE IF NOT EXISTS world_invasion_participants_v10400(
        slot INTEGER NOT NULL, account_id INTEGER NOT NULL,
        PRIMARY KEY(slot, account_id))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS world_invasion_rewards_v10400(
        slot INTEGER NOT NULL, account_id INTEGER NOT NULL,
        item_id TEXT NOT NULL, granted_at INTEGER NOT NULL,
        PRIMARY KEY(slot, account_id))""")


def status(conn, now=None):
    event = rotation(now)
    rows = conn.execute('SELECT slug,kills FROM world_invasion_fronts_v10400 WHERE slot=?',
                        (event['slot'],)).fetchall()
    completed = conn.execute('SELECT completed_at FROM world_invasion_results_v10400 WHERE slot=?',
                             (event['slot'],)).fetchone()
    counts = dict((str(r[0]),int(r[1])) for r in rows)
    return {**event,'counts':{slug:counts.get(slug,0) for slug in event['fronts']},
            'completed':bool(completed and int(completed[0])>0)}


def record_real_defeat(conn, mob, template, *, now=None, recipients=()):
    """Called ONCE per actual MobDefeatedEvent, never per party recipient.

    Returns (kind, slug, progress) or None. A SQL UNIQUE receipt prevents
    repeated callback credit from the very same death. Respawn timestamp
    changes for the next fight, letting legitimate repeated kills count.
    """
    if mob is None or not template or bool(getattr(mob,'alive',True)):
        return None
    if (getattr(mob,'monster_ai_summoned_v1160',False) or
            getattr(mob,'uoss_summon_parent_v1144',None) or
            template.get('uoss_superboss_add') or template.get('ai_ephemeral_summon_v1160')):
        return None
    template_id = str(getattr(mob,'template_id',''))
    match = _ALLOWED.fullmatch(template_id)
    if not match:
        return None
    slug, kind = match.groups()
    if slug not in _SLUGS or not str(getattr(mob,'room_id','')).startswith(f'v10400_{slug}_'):
        return None
    current = rotation(now)
    if slug not in current['fronts']:
        return None
    if kind == 'boss_2' and template_id != current['final_boss']:
        return None
    if kind == 'mob_3' and template_id != f'v10400_{slug}_mob_3':
        return None
    respawn = float(getattr(mob,'respawn_at',0.0))
    if not (respawn > 0 and respawn != float('inf')):
        return None
    encounter = f'{str(getattr(mob,"key",""))[:256]}|{respawn:.6f}'
    if not str(getattr(mob,'key','')):
        return None
    slot = current['slot']
    # IDs are taken only from the server's actual eligible combat recipients.
    # Never trust a user-supplied username, chat text or arbitrary template.
    participant_ids = set()
    for recipient in recipients:
        try:
            account_id = int(getattr(recipient, 'account_id', 0))
        except (TypeError, ValueError, OverflowError):
            continue
        if 0 < account_id <= 9223372036854775807:
            participant_ids.add(account_id)
    # Savepoint avoids opening a second transaction inside the normal combat
    # transaction; only one server event loop owns this connection.
    conn.execute('SAVEPOINT v104_invasion_kill')
    try:
        result = conn.execute('INSERT OR IGNORE INTO world_invasion_receipts_v10400 '
                              '(slot,encounter) VALUES (?,?)',(slot,encounter))
        if result.rowcount == 0:
            conn.execute('RELEASE SAVEPOINT v104_invasion_kill')
            return None
        old = status(conn, now)
        if old['completed']:
            outcome = None
        elif kind == 'mob_3':
            current_count = old['counts'][slug]
            if current_count < REQUIRED_PER_FRONT:
                conn.execute("""INSERT INTO world_invasion_fronts_v10400(slot,slug,kills)
                    VALUES (?,?,1) ON CONFLICT(slot,slug) DO UPDATE SET kills=kills+1""",
                    (slot,slug))
                outcome = ('front',slug,current_count+1)
            else:
                outcome = None
        elif all(old['counts'][front] >= REQUIRED_PER_FRONT for front in current['fronts']):
            result = conn.execute("""INSERT INTO world_invasion_results_v10400(slot,completed_at)
                VALUES (?,?) ON CONFLICT(slot) DO UPDATE SET
                completed_at=CASE WHEN completed_at=0 THEN excluded.completed_at ELSE completed_at END""",
                (slot,int(time.time()) if now is None else int(now)))
            outcome = ('final',slug,REQUIRED_PER_FRONT)
        else:
            outcome = None
        if outcome is not None:
            # Record each eligible player once per rotation, including a boss
            # participant who did not assist on an earlier front.
            for account_id in sorted(participant_ids):
                conn.execute('INSERT OR IGNORE INTO world_invasion_participants_v10400 '
                             '(slot, account_id) SELECT ?,id FROM accounts WHERE id=?',
                             (slot, account_id))
            if outcome[0] == 'final':
                # Single savepoint covers both the durable reward receipt and
                # real item transfer. Any failure rolls back BOTH operations.
                # Offline participants still receive their personal seal.
                for (account_id,) in conn.execute(
                    'SELECT account_id FROM world_invasion_participants_v10400 '
                    'WHERE slot=? ORDER BY account_id', (slot,)).fetchall():
                    receipt = conn.execute(
                        'INSERT OR IGNORE INTO world_invasion_rewards_v10400 '
                        '(slot,account_id,item_id,granted_at) VALUES (?,?,?,?)',
                        (slot, account_id, REWARD_ITEM_ID,
                         int(time.time()) if now is None else int(now)))
                    if receipt.rowcount:
                        conn.execute('INSERT INTO inventory(account_id,item_id,quantity) '
                                     'VALUES (?,?,1) ON CONFLICT(account_id,item_id) '
                                     'DO UPDATE SET quantity=quantity+1',
                                     (account_id,REWARD_ITEM_ID))
        conn.execute('RELEASE SAVEPOINT v104_invasion_kill')
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v104_invasion_kill')
        conn.execute('RELEASE SAVEPOINT v104_invasion_kill')
        raise
    # Commit only our shared connection, just like normal combat quest writes.
    conn.commit()
    return outcome


def status_text(conn, now=None):
    state = status(conn, now)
    city = dict((row[0],row[1]) for row in REGIONS)
    bosses = dict((row[0],row[-1]) for row in REGIONS)
    readable = '; '.join(f'{city[slug]}: {state["counts"][slug]}/{REQUIRED_PER_FRONT}'
                         for slug in state['fronts'])
    outcome = 'zakończona' if state['completed'] else 'trwa'
    remaining=max(0,state['expires_at']-(int(time.time()) if now is None else int(now)))
    return (f'INWAZJA V104: {outcome}. Fronty: {readable}. '
            f'Finałowy boss: {bosses[state["fronts"][-1]]}. '
            f'Zmiana rotacji za {(remaining+59)//60} minut (UTC).')


def reward_status(conn, account_id: int, now=None) -> str:
    """Accessible read-only reminder. Only actual completed events pay seals."""
    account_id = int(account_id)
    if account_id < 1:
        return 'INWAZJA V104: brak aktywnej postaci.'
    row = conn.execute('SELECT COUNT(*) FROM world_invasion_rewards_v10400 '
                       'WHERE account_id=?', (account_id,)).fetchone()
    total = int(row[0]) if row else 0
    state = status(conn, now)
    row = conn.execute('SELECT 1 FROM world_invasion_participants_v10400 '
                       'WHERE slot=? AND account_id=?',
                       (state['slot'],account_id)).fetchone()
    participated = row is not None
    return (f'INWAZJA V104: pieczęcie zwycięstwa {total}. '
            + ('Uczestniczysz w bieżącej rotacji.' if participated else
               'Brak zaliczonego udziału w bieżącej rotacji.'))

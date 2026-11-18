# -*- coding: utf-8 -*-
"""v115: immutable, per-recipient reward snapshot for delayed Fame settlement.

The combat calculation supplies all EXP axes *after* the existing Multi Cap,
mentor, guild, dungeon and event rules. This module does not award EXP/Fame,
perform any network I/O or import audio. A snapshot must be written within the
same SQLite transaction that first stages the corresponding Fame objective.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

_MAX_XP = (1 << 63) - 1


@dataclass(frozen=True)
class RewardSnapshot:
    character_xp: int
    soul_xp: int
    class_xp: int
    stat_xp: int
    class_levels: tuple
    class_max_level: int
    overcap: bool
    character_name: str | None = None
    verified_zero: bool = False

    def validate(self):
        for key in ('character_xp', 'soul_xp', 'class_xp', 'stat_xp'):
            value = getattr(self, key)
            if type(value) is not int or not 0 <= value <= _MAX_XP:
                raise ValueError('Invalid v115 EXP axis: ' + key)
        if not any((self.character_xp, self.soul_xp, self.class_xp, self.stat_xp)) and not self.verified_zero:
            raise ValueError('Unverified zero EXP Fame reward is not permitted')
        if type(self.verified_zero) is not bool:
            raise ValueError('Invalid verified-zero flag')
        if self.character_name is not None and (not isinstance(self.character_name, str) or not self.character_name.strip()):
            raise ValueError('Invalid named Fame reward recipient')
        if type(self.overcap) is not bool:
            raise ValueError('Invalid overcap flag')
        if type(self.class_max_level) is not int or self.class_max_level < 1:
            raise ValueError('Invalid class cap')
        if not isinstance(self.class_levels, tuple):
            raise ValueError('Class levels must be a tuple')
        seen = set()
        for item in self.class_levels:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise ValueError('Invalid class entry')
            name, level = item
            if not isinstance(name, str) or not name.strip() or name in seen:
                raise ValueError('Duplicate/invalid class name')
            if type(level) is not int or level < 1:
                raise ValueError('Invalid class level')
            seen.add(name)
        if self.class_xp and not self.class_levels:
            raise ValueError('Class EXP without a class')
        return self

    def payload(self):
        self.validate()
        return json.dumps({
            'character_xp': self.character_xp, 'soul_xp': self.soul_xp,
            'class_xp': self.class_xp, 'stat_xp': self.stat_xp,
            'class_levels': self.class_levels, 'class_max_level': self.class_max_level,
            'overcap': self.overcap, 'character_name': self.character_name,
            'verified_zero': self.verified_zero,
        }, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def ensure_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS v115_fame_reward_snapshot (
        account_id INTEGER NOT NULL, region TEXT NOT NULL, boss_id TEXT NOT NULL,
        payload TEXT NOT NULL, PRIMARY KEY(account_id,region,boss_id)
    )''')


def save_snapshot(conn, account_id, region, boss_id, plan):
    """Write-once. Return True if created, False for an identical retry.

    Different retries are always rejected (not silently overwritten). Caller
    owns COMMIT/ROLLBACK, ideally together with fame_queue.schedule_fame().
    """
    if type(account_id) is not int or account_id <= 0:
        raise ValueError('Invalid account')
    if not region or not boss_id or not isinstance(plan, RewardSnapshot):
        raise ValueError('Invalid Fame objective or plan')
    payload = plan.payload()
    ensure_schema(conn)
    previous = conn.execute('''SELECT payload FROM v115_fame_reward_snapshot
        WHERE account_id=? AND region=? AND boss_id=?''', (account_id, region, boss_id)).fetchone()
    if previous:
        if previous[0] != payload:
            raise ValueError('Attempted to change a staged Fame reward')
        return False
    conn.execute('''INSERT INTO v115_fame_reward_snapshot
        (account_id,region,boss_id,payload) VALUES (?,?,?,?)''',
        (account_id, region, boss_id, payload))
    return True


def load_snapshot(conn, account_id, region, boss_id):
    ensure_schema(conn)
    row = conn.execute('''SELECT payload FROM v115_fame_reward_snapshot
        WHERE account_id=? AND region=? AND boss_id=?''', (account_id, region, boss_id)).fetchone()
    if row is None:
        return None
    obj = json.loads(row[0])
    return RewardSnapshot(
        character_xp=obj['character_xp'], soul_xp=obj['soul_xp'],
        class_xp=obj['class_xp'], stat_xp=obj['stat_xp'],
        class_levels=tuple((name, level) for name, level in obj['class_levels']),
        class_max_level=obj['class_max_level'], overcap=obj['overcap'],
        character_name=obj.get('character_name'),
        verified_zero=obj.get('verified_zero', False)).validate()


def stage_with_snapshot(conn, account_id, region, boss_id, boss_name, plan, *, now=None):
    """Atomic first-clear staging on the caller's SQLite connection.

    Does NOT decide eligibility or call the actual combat hook. Existing v114
    fame must not be invoked for the same objective by the future integration.
    """
    from systems.v115 import fame_queue
    fame_queue.ensure_schema(conn)
    ensure_schema(conn)
    conn.execute('SAVEPOINT v115_fame_stage')
    try:
        inserted = fame_queue.schedule_fame(conn, account_id, region, boss_id,
                                             boss_name, now=now)
        if inserted:
            save_snapshot(conn, account_id, region, boss_id, plan)
        else:
            existing = load_snapshot(conn, account_id, region, boss_id)
            if existing is None:
                raise ValueError('Existing Fame queue has no immutable reward snapshot')
            if existing != plan.validate():
                raise ValueError('Conflicting Fame objective replay')
        conn.execute('RELEASE SAVEPOINT v115_fame_stage')
        return inserted
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v115_fame_stage')
        conn.execute('RELEASE SAVEPOINT v115_fame_stage')
        raise

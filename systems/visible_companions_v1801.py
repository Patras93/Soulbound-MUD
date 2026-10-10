# -*- coding: utf-8 -*-
"""Read-only nearby companion visibility, grounded in the existing SQLite table."""
from __future__ import annotations
import sqlite3


def nearby_companions_v1801(server, room_id):
    """Return (owner, kind, label, hp, max_hp, level, stance).

    Companions follow their ONLINE owner; never spawn monster instances and
    never copy, update, or reset durable summon/character state.
    """
    from player.session_mixins.era_sky_v1700 import SUMMONS, summon_display
    owners = {
        int(s.account_id): s for s in tuple(server.sessions)
        if s.account_id is not None and not getattr(s, 'closed', False)
        and getattr(s, 'character', None)
        and s.character.room_id == room_id
    }
    if not owners:
        return []
    params = sorted(owners)
    sql = ('SELECT account_id,summon_type,level,soul_rank,stance,hp,max_hp '
           'FROM summons_v1700 WHERE active=1 AND hp>0 AND account_id IN ('
           + ','.join('?' for _ in params) + ')')
    try:
        rows = server.db.conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as exc:
        # A new character with no summons has no migration requirement yet.
        if 'no such table: summons_v1700' in str(exc):
            return []
        raise
    companions = []
    for row in rows:
        owner = owners.get(int(row['account_id']))
        kind = str(row['summon_type'])
        spec = SUMMONS.get(kind)
        if not owner or not spec or spec[1] not in owner.active_class_names():
            continue
        companions.append((owner, kind, summon_display(kind, row['soul_rank']),
                           int(row['hp']), int(row['max_hp']),
                           int(row['level']), str(row['stance'])))
    return sorted(companions, key=lambda c: (c[0].character.name.casefold(), c[2].casefold()))

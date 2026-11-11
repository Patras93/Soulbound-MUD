# -*- coding: utf-8 -*-
"""Czasowo aktywne wydarzenie: zaliczamy tylko prawdziwe zgony potworów.

Obsługa błędu jest poza silnikiem walki: wyjątek w wydarzeniu nie może
kasować normalnego XP i lootu, a SAVEPOINT nie zostawia częściowej nagrody.
"""
from __future__ import annotations
import time
from .clock import rotation,REQUIRED_KILLS
from .storage import create_schema
from .rewards import reward_id


def _eligible(mob,template,state):
    if mob is None or not template or getattr(mob,'alive',True):return None
    if (getattr(mob,'monster_ai_summoned_v1160',False)
        or getattr(mob,'uoss_summon_parent_v1144',None)
        or template.get('ai_ephemeral_summon_v1160') or template.get('uoss_superboss_add')):
        return None
    template_id=str(getattr(mob,'template_id',''))
    location=str(getattr(mob,'room_id',''))
    if not location.startswith(state['region_prefix']+'_'):return None
    if template_id==state['boss']:
        kind='boss'
    elif (template_id.startswith(state['region_prefix']+'_mob_')
          and template_id.rsplit('_',1)[-1] in {str(i) for i in range(1,13)}):
        kind='front'
    else:return None
    respawn=float(getattr(mob,'respawn_at',0))
    if not 0<respawn<float('inf'):return None
    key=str(getattr(mob,'key',''))
    if not key:return None
    return kind,key[:256]+'|'+format(respawn,'.6f')


def record_defeat(db,mob,template,recipients=(),now=None):
    now=int(time.time() if now is None else now)
    state=rotation(now)
    eligible=_eligible(mob,template,state)
    if eligible is None:return None
    kind,encounter=eligible
    accounts=set()
    for member in recipients:
        try:account=int(getattr(member,'account_id',0))
        except (TypeError,ValueError,OverflowError):continue
        if 0<account<2**63:accounts.add(account)
    if not accounts:return None
    conn=db.conn
    # Tables are initialized by the v110 startup migration; no DDL during kills.
    conn.execute('SAVEPOINT v110_world_event')
    try:
        receipt=conn.execute('INSERT OR IGNORE INTO v110_event_death_receipts '
            '(slot,encounter) VALUES (?,?)',(state['slot'],encounter))
        if not receipt.rowcount:
            conn.execute('RELEASE SAVEPOINT v110_world_event')
            return None
        row=conn.execute('SELECT kills,completed_at FROM v110_event_progress WHERE slot=?',
                         (state['slot'],)).fetchone()
        kills=int(row[0]) if row else 0
        if row and int(row[1])>0:
            conn.execute('RELEASE SAVEPOINT v110_world_event')
            return None
        if kind=='front':
            next_count=min(REQUIRED_KILLS,kills+1)
            conn.execute('INSERT INTO v110_event_progress(slot,slug,kills) VALUES (?,?,?) '
                         'ON CONFLICT(slot) DO UPDATE SET kills=excluded.kills',
                         (state['slot'],state['slug'],next_count))
            for account in accounts:
                conn.execute('INSERT OR IGNORE INTO v110_event_participants(slot,account_id) '
                             'SELECT ?,id FROM accounts WHERE id=?',(state['slot'],account))
            outcome=('front',state['slug'],next_count)
        elif kills>=REQUIRED_KILLS:
            conn.execute('UPDATE v110_event_progress SET completed_at=? WHERE slot=?',
                         (now,state['slot']))
            for account in accounts:
                conn.execute('INSERT OR IGNORE INTO v110_event_participants(slot,account_id) '
                             'SELECT ?,id FROM accounts WHERE id=?',(state['slot'],account))
            item=reward_id(state['slug'])
            from systems.global_events.rewards import plan_rewards
            participants=[int(r[0]) for r in conn.execute(
                'SELECT account_id FROM v110_event_participants WHERE slot=?',
                (state['slot'],)).fetchall()]
            for _,account,_ in plan_rewards(state['slot'],state['slug'],participants):
                receipt=conn.execute('INSERT OR IGNORE INTO v110_event_reward_receipts '
                    '(slot,account_id,item_id) VALUES (?,?,?)',(state['slot'],account,item))
                if receipt.rowcount:
                    db.add_item(account,item,1,commit=False)
            outcome=('final',state['slug'],kills)
        else:outcome=None
        conn.execute('RELEASE SAVEPOINT v110_world_event')
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v110_world_event')
        conn.execute('RELEASE SAVEPOINT v110_world_event')
        raise
    # Shared connection follows existing invasion engine's transactional model.
    conn.commit()
    return outcome

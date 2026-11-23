# -*- coding: utf-8 -*-
"""v116.68: read-only skill forecast and narrow Windows TCP reset reporting."""
from __future__ import annotations

import sqlite3
from types import SimpleNamespace
from unittest.mock import patch

from network.peer_reset_handler_v11668 import (is_peer_reset_cleanup,
                                               install_peer_reset_handler)
from systems.encounter_burst_v11656 import member_skill_burst_v11656


def run():
    checks = 0
    def require(value, label):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError('LIVE PERFORMANCE v11668: '+label)

    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE learned_skills (account_id INT, skill_id TEXT)')
    conn.execute('CREATE TABLE skill_progress (account_id INT, skill_id TEXT, level INT)')
    for i in range(480):
        skill_id = f'learned_{i:04d}'
        conn.execute('INSERT INTO learned_skills VALUES (7, ?)', (skill_id,))
        if i != 0:
            conn.execute('INSERT INTO skill_progress VALUES (7, ?, ?)',
                         (skill_id, 9 if i == 479 else 1))
    conn.commit()

    class Database:
        def __init__(self, connection): self.conn = connection
        def learned_skill_ids(self, aid):
            return {r[0] for r in self.conn.execute(
                'SELECT skill_id FROM learned_skills WHERE account_id=?',(aid,))}
        def skill_progress(self, aid, skill):
            raise AssertionError('read-only forecast called writable progress helper')

    class Actor:
        def __init__(self, db):
            self.server=SimpleNamespace(db=db)
            self.account_id=7
            self.character=SimpleNamespace(character_level=85,soul_level=85,class_name='Mec',
                class_physical_damage_multiplier=lambda:1.0,
                racial_physical_damage_multiplier=lambda:1.0,
                class_magic_damage_multiplier=lambda:1.0,
                racial_magic_damage_multiplier=lambda:1.0,
                racial_all_damage_multiplier=lambda:1.0)
            self.core_calls=0
            self.cache_seen=0
            self.current_hp=10000
        def class_skills(self):
            return [dict(id=f'learned_{i:04d}',kind='damage',mult=1.,scale='intelligence')
                    for i in range(480)]
        def offensive_skill_core_power_v11185(self,skill):
            self.core_calls+=1
            if getattr(self, '_read_only_equipment_cache_v1262', None) is not None:
                self.cache_seen+=1
            return 1000
        def offensive_skill_damage_type_v11190(self,skill):return 'magic'
        def total_set_damage_multiplier(self):return 1.0
        def equipment_damage_multiplier(self,k):return 1.0
        def skill_buff_multiplier(self,**k):return 1.0
        def critical_multiplier(self):return 2.0

    actor = Actor(Database(conn))
    trace=[]
    conn.set_trace_callback(trace.append)
    before=conn.total_changes
    with patch('systems.party_synergies.party_synergy_damage_multiplier_v11338',return_value=1.):
        first=member_skill_burst_v11656(actor,now=100.)
    require(first>0,'nonzero forecast from 480 learned skills')
    require(conn.total_changes==before,'forecast must not write player progress')
    require(len(trace)<=2,'at most two SQL queries for 480 known skills')
    require(not any('INSERT' in s.upper() or 'COMMIT' in s.upper() for s in trace),
            'no INSERT, no COMMIT in attack forecast')
    require(actor.core_calls==480,'each learned offensive skill is considered exactly once')
    require(actor.cache_seen==480,'per-forecast read-only EQ cache available for skills')
    require('_read_only_equipment_cache_v1262' not in vars(actor),
            'temporary EQ cache released immediately')
    trace.clear()
    with patch('systems.party_synergies.party_synergy_damage_multiplier_v11338',return_value=1.):
        again=member_skill_burst_v11656(actor,now=105.)
    require(again==first and not trace and actor.core_calls==480,
            'same forecast cached for twelve seconds with zero SQL')
    actor._read_only_equipment_cache_v1262={'external_marker':True}
    with patch('systems.party_synergies.party_synergy_damage_multiplier_v11338',return_value=1.):
        member_skill_burst_v11656(actor,now=113.)
    require(actor._read_only_equipment_cache_v1262.get('external_marker'),
            'existing per-command EQ cache never overwritten/deleted')
    del actor._read_only_equipment_cache_v1262
    # A missing progress row still starts at level 1 without silently writing.
    conn.execute('DELETE FROM skill_progress WHERE skill_id=?',('learned_0479',))
    conn.commit();trace.clear();before=conn.total_changes
    with patch('systems.party_synergies.party_synergy_damage_multiplier_v11338',return_value=1.):
        second=member_skill_burst_v11656(actor,now=130.)
    require(second>0 and conn.total_changes==before,'missing progress falls back to level one, read only')
    require(len(trace)<=2,'missing progress does not cause an N+1 lookup')
    require(second<=first,'actual learned skill level affects forecast')
    conn.close()

    # Fake the Windows asyncio transport callback without touching Windows.
    class ProactorPipe:
        __module__ = 'asyncio.proactor_events'
        def _call_connection_lost(self): pass
    handle=SimpleNamespace(_callback=ProactorPipe()._call_connection_lost)
    reset=ConnectionResetError(10054,'Peer reset')
    require(is_peer_reset_cleanup({'exception':reset,'handle':handle}),
            'expected Windows 10054 proactor cleanup')
    require(not is_peer_reset_cleanup({'exception':ConnectionResetError(121,'Timeout'),
                                       'handle':handle}), 'do not swallow WinError 121')
    require(not is_peer_reset_cleanup({'exception':reset,
                                       'handle':SimpleNamespace(_callback=lambda:None)}),
            'do not swallow arbitrary 10054 callbacks')
    require(not is_peer_reset_cleanup({'exception':RuntimeError('actual fault'),
                                       'handle':handle}), 'do not swallow server faults')

    class Loop:
        def __init__(self): self.handler=None;self.forwarded=[]
        def get_exception_handler(self):return self.handler
        def set_exception_handler(self,handler):self.handler=handler
        def default_exception_handler(self,context):self.forwarded.append(context)
    loop=Loop();install_peer_reset_handler(loop);first_handler=loop.handler
    install_peer_reset_handler(loop)
    require(loop.handler is first_handler,'handler installed only once')
    loop.handler(loop,{'exception':reset,'handle':handle})
    require(not loop.forwarded,'expected disconnected socket cleanly reported')
    context={'exception':RuntimeError('other'), 'message':'important'}
    loop.handler(loop,context)
    require(loop.forwarded==[context],'real errors still sent to native asyncio handler')
    print(f'LIVE PERFORMANCE / TCP RESET v116.68: {checks}/{checks} PASS',flush=True)
    return checks

if __name__=='__main__': run()

# -*- coding: utf-8 -*-
"""World-wide natural elite Fame, credit isolation and durability (v12.00.1)."""
import sqlite3
from types import SimpleNamespace


def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from systems.fame_v1702 import (fame_catalog, record_fame_kill,
                                   fame_report, ensure_schema, _is_fame_target)
    from collections import Counter
    rows=runtime.V1201_WORLD_FAME['encounters']
    targets=set((zone, tid) for zone, room, tid, base in rows)
    checks=0
    assert len(targets)==len(rows) and len(rows)>=180
    checks+=2
    assert runtime.V1201_WORLD_FAME['regions_with_new_fame']>=100
    checks+=1
    catalog=fame_catalog()
    spawned=Counter(runtime.MOB_SPAWNS)
    for zone, room, tid, base in rows:
        template=runtime.MOB_TEMPLATES[tid]
        assert (zone,tid) in targets
        assert spawned[(room,tid)]==1
        assert template['rank']=='elite' and template['fame_target'] is True
        assert template['max_hp']>template['v1201_base_hp']
        assert template['damage']>template['v1201_base_damage']
        assert not _is_fame_target(runtime.MOB_TEMPLATES[base])
        assert tid in catalog[zone]
        checks+=7
    # Test a true two-player battle credit and permanent single-award SQLite.
    zone,room,tid,base=rows[0]
    mob=SimpleNamespace(room_id=room,home_room_id=room,template_id=tid)
    player1=SimpleNamespace(account_id=11)
    player2=SimpleNamespace(account_id=12)
    conn=sqlite3.connect(':memory:')
    ensure_schema(conn)
    award=record_fame_kill(conn,[player1,player2],mob,runtime.MOB_TEMPLATES[tid])
    assert len(award)==2
    assert not record_fame_kill(conn,[player1,player2],mob,runtime.MOB_TEMPLATES[tid])
    assert conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0]==2
    checks+=3
    assert conn.execute('SELECT COUNT(*) FROM fame_pending_v1703').fetchone()[0]==2
    checks+=1
    assert conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702 WHERE account_id=?',(11,)).fetchone()[0]==1
    checks+=1
    assert any('Fame:' in line for line in fame_report(conn,11,''))
    checks+=1
    # Ordinary base variants should not credit a second Fame.
    plain=SimpleNamespace(room_id=room,home_room_id=room,template_id=base)
    assert not record_fame_kill(conn,[player1],plain,runtime.MOB_TEMPLATES[base])
    checks+=1
    conn.commit();conn.close()
    return checks

if __name__ == '__main__':
    print('V12.00.1 WORLD FAME:',run_regression(),'checks PASS')

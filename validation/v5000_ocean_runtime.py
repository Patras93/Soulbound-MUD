# -*- coding: utf-8 -*-
"""Five Imperial v5 fleets exercised through the actual Ocean 4 SQLite engine."""

def run_regression():
    import server  # Installs the five pre-existing Imperial fleets.
    from systems import ocean4_v1350 as navy
    from validation.regression_ocean4_v1350 import Ocean4V1350Tests
    from systems.legends_ocean_v5000 import CYCLES
    checks=0
    for target in CYCLES:
        fixture=Ocean4V1350Tests('test_no_repair_or_escort_during_combat')
        fixture.setUp()
        try:
            fleet=navy.ENEMIES[target]
            name,max_hp,attack,reward,kind,threat=fleet
            assert target in navy.MATERIALS
            navy.escort(fixture.conn,1,2)
            label,hp,ships=navy.begin(fixture.conn,1,target,now=1000)
            assert label==name and ships==2 and hp>0
            state=navy.battle_state(fixture.conn,1)
            assert state['enemy']==target and state['turn']==0
            with __import__('contextlib').suppress(ValueError):
                navy.action(fixture.conn,1,'manewr',now=1001)
            state=navy.battle_state(fixture.conn,1)
            assert state['turn']==1 and state['enemy']==target
            assert fixture.conn.execute('SELECT count(*) FROM ocean4_battles_v1350 WHERE account_id=1').fetchone()[0]==1
            fixture.conn.close();fixture.conn=fixture._connect()
            assert navy.battle_state(fixture.conn,1)['turn']==1
            assert fixture.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            checks+=7
        finally:
            fixture.tearDown()
    return checks

if __name__=='__main__':
    print(f'v5.00.0 OCEAN REAL SQLITE: {run_regression()} checks PASS')

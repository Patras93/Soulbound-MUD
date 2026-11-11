# -*- coding: utf-8 -*-
"""v11: real SQLite guild production, escrow and durability.

Tests new late-game buildings with unchanged production bank and treasury paths.
"""


def run_regression():
    from validation.regression_economy4_v1360 import Economy4V1360Tests
    from systems import economy4_v1360 as econ
    from data.catalogs import ITEMS
    new_buildings = ('obserwatorium','archiwum','stocznia','runiczna_kuznia')
    assert len(econ.BUILDINGS)==8
    checks=0
    case=Economy4V1360Tests()
    case.setUp()
    try:
        for idx,key in enumerate(new_buildings):
            name,item,qty,base,maintenance=econ.BUILDINGS[key]
            assert item in ITEMS and base>0 and qty>0 and maintenance>0
            old_treasury=int(case.c.execute('SELECT treasury FROM player_clans WHERE id=100').fetchone()[0])
            upgraded,cost=econ.upgrade_building(case.c,100,key,now=10000)
            assert upgraded==1 and cost==base
            assert int(case.c.execute('SELECT treasury FROM player_clans WHERE id=100').fetchone()[0])==old_treasury-base
            assert econ.collect_production(case.c,100,now=10000)==[]
            checks+=4
        outputs=econ.collect_production(case.c,100,now=10000+econ.SIX_HOURS)
        assert len(outputs)==4
        assert {row[0] for row in outputs} == {econ.BUILDINGS[k][0] for k in new_buildings}
        assert econ.collect_production(case.c,100,now=10000+econ.SIX_HOURS)==[]
        checks+=3
        for key in new_buildings:
            name,item,qty,base,maint=econ.BUILDINGS[key]
            row=case.c.execute('SELECT quantity FROM player_clan_bank WHERE clan_id=? AND item_id=?',(100,item)).fetchone()
            assert row and row[0]==qty
            row=case.c.execute('SELECT level FROM guild_production_v1360 WHERE clan_id=? AND building=?',(100,key)).fetchone()
            assert row and row[0]==1
            checks+=2
        old_treasury=int(case.c.execute('SELECT treasury FROM player_clans WHERE id=100').fetchone()[0])
        with __import__('contextlib').suppress(ValueError):
            econ.upgrade_building(case.c,100,'unknown_v11',now=10000)
        assert case.c.execute('SELECT treasury FROM player_clans WHERE id=100').fetchone()[0]==old_treasury
        checks+=1
        return checks
    finally:
        case.tearDown()

if __name__=='__main__':
    print('V11 GUILD BUILDINGS SQLITE:',run_regression(),'PASS')

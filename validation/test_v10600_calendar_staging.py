# -*- coding: utf-8 -*-
"""UTC rollover and no duplicate catalogue in isolated staging."""
from pathlib import Path
import datetime,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from world.v10600_krainy_30001_60000 import install as regions_install
from world.v10600_calendar_contracts import install as contracts_install
from systems.quest_calendar_v10600 import cadence_for_v106_quest,remaining_seconds
from validation.v10600_stage_catalog_audit import registries

def run():
    state=registries();regions_install(*state)
    rooms,mobs,spawns,npcs,quests,items,*_=state
    result=contracts_install(quests,npcs,mobs,items)
    assert result=={'contracts':60,'daily':30,'weekly':30}
    assert contracts_install(quests,npcs,mobs,items)['contracts']==0
    checks=2
    for key,q in quests.items():
        if not key.startswith('v10600_contract_'):continue
        assert cadence_for_v106_quest(key,q)==q['repeat_calendar_v104']
        assert q['target'] in mobs and q['reward_gold']>0 and q['repeatable']
        assert any(key in n['specialist_quests'] for n in npcs.values())
        checks+=3
    # A Sunday 23:59 UTC completion renews on Monday 00:00 UTC (weekly + daily).
    d=datetime.datetime(2026,11,1,23,59,tzinfo=datetime.timezone.utc)
    start=int(d.timestamp());renew=start+60
    assert remaining_seconds(start,'day_utc',start+2)==58;checks+=1
    assert remaining_seconds(start,'week_utc',start+2)==58;checks+=1
    assert remaining_seconds(start,'week_utc',renew)==0;checks+=1
    assert cadence_for_v106_quest('v10500_przesmyk_story_01',{'repeatable':True}) is None;checks+=1
    return checks

if __name__=='__main__':print('V106 CALENDAR STAGING:',run(),'PASS',flush=True)

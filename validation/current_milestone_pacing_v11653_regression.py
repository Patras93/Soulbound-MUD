# -*- coding: utf-8 -*-
"""v116.53: future milestone payouts are no longer automatically full Multi Cap."""
from pathlib import Path
from types import SimpleNamespace
from systems.milestone_cap_rewards_v2103 import (
    milestone_payout_from_cap_v11653, explorer_award_per_point_v1001,
    fame_cap_awards_v2103,
)
from systems.multi_cap_v23215 import multi_cap_level_value_v23217


def run():
    checks=0
    class FakeDb:
        def __init__(self, cap):self.cap=cap
        def multi_cap_v23215(self,_):return self.cap
    for cap in (1,2,10,100,11000,23491000,10**9,10**18):
        db=FakeDb(cap)
        session=SimpleNamespace(server=SimpleNamespace(db=db),account_id=1,
                                active_class_names=lambda:['Mec'])
        ep=explorer_award_per_point_v1001(cap)
        fame=fame_cap_awards_v2103(session)
        ep_value=milestone_payout_from_cap_v11653(cap,5)
        fame_value=milestone_payout_from_cap_v11653(cap,10)
        assert set(ep)==set(fame)=={'character','soul','class_total','stat'};checks+=1
        assert set(ep.values())=={ep_value};checks+=1
        assert set(fame.values())=={fame_value};checks+=1
        assert all(1<=v<=cap for v in (*ep.values(),*fame.values()));checks+=1
        assert ep_value<=fame_value<=cap;checks+=1
        assert fame_value==max(1,(cap+9)//10);checks+=1
        assert ep_value==max(1,(cap*5+99)//100);checks+=1
    player_cap=23491000
    current_exp=28631437
    requirement=81514440
    ep=explorer_award_per_point_v1001(player_cap)['character']
    fame=fame_cap_awards_v2103(SimpleNamespace(server=SimpleNamespace(db=FakeDb(player_cap)),account_id=1))['character']
    assert ep==1174550;checks+=1
    assert fame==2349100;checks+=1
    assert current_exp+3*player_cap>=requirement;checks+=1 # old exploit
    assert current_exp+3*ep<requirement;checks+=1 # now bounded
    assert current_exp+3*fame<requirement;checks+=1
    assert multi_cap_level_value_v23217(89)>multi_cap_level_value_v23217(88);checks+=1
    classless=SimpleNamespace(server=SimpleNamespace(db=FakeDb(player_cap)),account_id=1,
                              active_class_names=lambda:[])
    assert fame_cap_awards_v2103(classless)['class_total']==0;checks+=1
    root=Path(__file__).resolve().parents[1]
    exp=(root/'player/session_mixins/exploration_progress.py').read_text('utf-8')
    fam=(root/'systems/fame_v1702.py').read_text('utf-8')
    assert '5% bieżącego Multi Cap' in exp and '10% bieżącego Multi Cap' in fam;checks+=1
    assert 'caps = explorer_award_per_point_v1001(multi_cap)' in exp;checks+=1
    assert 'caps = fame_cap_awards_v2103(session)' in fam;checks+=1
    actual=(root/'systems/v115/fame_exp_progression.py').read_text('utf-8')
    assert 'fame_bonus = milestone_payout_from_cap_v11653(' in actual;checks+=1
    assert 'V11653_FAME_CAP_PERCENT' in actual;checks+=1
    online=(root/'systems/v115/fame_online_delivery.py').read_text('utf-8')
    assert '10% Multi Cap' in online;checks+=1
    return checks

if __name__=='__main__':
    print('MILESTONE SLOWDOWN v116.00.53:',run(),'PASS')

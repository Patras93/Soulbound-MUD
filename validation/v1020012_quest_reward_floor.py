# -*- coding: utf-8 -*-
"""Regression: quest offer XP equals turn-in base XP and no relevant reward <200k."""
import copy
from systems.quest_reward_floor_v1020012 import quest_xp_plan, BASE_QUEST_XP_MIN
from systems.quest_combat_salvage_v102007 import is_combat_salvage_quest
from systems.live_quest_olc_v1209 import STAT_XP_FIELDS_V3900


def run():
    checks = 0
    minimum = BASE_QUEST_XP_MIN
    assert minimum == 200000; checks += 1
    examples = {
        'fishing': {'kind':'collect','generator_level':2,'reward_tool_type':'fishing',
                    'reward_profession':'Wędkarstwo','reward_profession_xp':0,'reward_tool_xp':0},
        'fight': {'kind':'kill','generator_level':2,'olc_reward_xp':0,
                  'olc_reward_stat_xp':0,'olc_reward_class_xp':0,'olc_reward_soul_xp':0},
        'profession_none': {'kind':'profession_action','generator_level':3},
        'ordinary': {'kind':'talk_npc','generator_level':1},
        'rich': {'kind':'kill','generator_level':600,'olc_reward_xp':900000,
                 'olc_reward_stat_xp':500000,'olc_reward_class_xp':750000,
                 'olc_reward_soul_xp':850000},
        'unique_stats': {'kind':'collect','generator_level':9,
                         'olc_reward_stat_strength':765432},
        'salvage': {'kind':'collect','generator_level':5,'target':'salvaged_steel_plate'},
    }
    for qid,q in examples.items():
        old=copy.deepcopy(q)
        out=quest_xp_plan(qid,q)
        assert q == old, ('mutation',qid); checks+=1
        assert out['character'] >= minimum, qid; checks+=1
        assert len(out['stats']) == 6 and all(val >= minimum for val in out['stats'].values()), qid; checks+=1
        assert all(isinstance(value,int) and value>=0 for key,value in out.items() if key!='stats'),qid;checks+=1
    fish=quest_xp_plan('fisher_30_fish',examples['fishing'])
    assert fish['profession'] == fish['tool'] == minimum and fish['soul'] == fish['class_xp'] == 0; checks+=1
    fight=quest_xp_plan('fight',examples['fight'])
    assert fight['class_xp'] == fight['soul'] == minimum; checks+=1
    profes=quest_xp_plan('prof_none',examples['profession_none'])
    assert profes['class_xp']==profes['soul']==profes['profession']==profes['tool']==0;checks+=1
    rich=quest_xp_plan('rich',examples['rich'])
    assert (rich['character'],rich['class_xp'],rich['soul'])==(900000,750000,850000);checks+=1
    assert all(v==500000 for v in rich['stats'].values());checks+=1
    assert quest_xp_plan('unique',examples['unique_stats'])['stats']['strength']==765432;checks+=1
    assert quest_xp_plan('unique',examples['unique_stats'])['stats']['dexterity']==minimum;checks+=1
    # Exception quests require explicit opt-in; they do not become generic kill quests.
    salvage_id='haldor_steel_recycling'
    q=dict(examples['salvage'])
    assert is_combat_salvage_quest(q,salvage_id);checks+=1
    assert quest_xp_plan(salvage_id,q)['class_xp']==0;checks+=1
    q['olc_reward_class_xp']=1000;q['olc_reward_soul_xp']=1000
    assert quest_xp_plan(salvage_id,q)['class_xp']==minimum;checks+=1
    assert quest_xp_plan(salvage_id,q)['soul']==minimum;checks+=1
    # Also audit actual dynamically assembled catalog when the engine already loaded it.
    from data.quests import QUESTS
    audited=0
    for qid,q in QUESTS.items():
        q_plan=quest_xp_plan(qid,q)
        assert q_plan['character']>=minimum and min(q_plan['stats'].values())>=minimum,qid
        for channel in ('class_xp','soul','profession','tool'):
            assert q_plan[channel]==0 or q_plan[channel]>=minimum,(qid,channel)
        audited+=1
    assert audited>=40, audited;checks+=1
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    payout=(root/'player/session_mixins/quest_commands.py').read_text(encoding='utf8')
    info=(root/'player/session_mixins/quest_offers.py').read_text(encoding='utf8')
    assert 'reward_plan = quest_xp_plan(quest_id, q)' in payout;checks+=1
    assert 'reward_plan = quest_xp_plan(quest_id, quest)' in info;checks+=1
    assert "stat_reward_by_name = reward_plan['stats']" in payout;checks+=1
    assert "reward_prof_xp = reward_plan['profession']" in payout;checks+=1
    assert "quest_character_xp=reward_plan['character']" in payout;checks+=1
    return checks, audited

if __name__=='__main__':
    checks,audited=run()
    print(f'QUEST XP FLOOR v102.00.12: {checks} checks PASS, audited {audited} quests',flush=True)

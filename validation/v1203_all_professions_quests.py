# -*- coding: utf-8 -*-
"""v12.00.3: 22 profession/tool pacing and all quest catalog integrity."""
from __future__ import annotations
from collections import Counter, defaultdict

def run_regression():
    import server
    from systems.content_registry import QUESTS,ITEMS
    from systems.profession_projects_v1200 import PROJECTS,LEVELS,recipe,project_item_id
    from systems.profession_xp_v1203 import reward_xp_v1203,quest_reward_floor_v1203,material_factor
    from core.progression_resources import v0522_is_profession_quest,v0190_requirement
    from config.balance import profession_xp_requirement_v1401,tool_xp_requirement_v1402
    from systems.new_professions import PROFESSIONS as NEW
    c=0
    assert len(PROJECTS)==22 and len(NEW)==8 and LEVELS==(25,200,400,600,700,775); c+=3
    prof_quests=defaultdict(list)
    for qid,q in QUESTS.items():
        if not v0522_is_profession_quest(q):continue
        prof=str(q.get('required_profession') or q.get('reward_profession') or q.get('target') or '')
        if prof in PROJECTS: prof_quests[prof].append((qid,q))
        if int(q.get('reward_profession_xp') or 0) or int(q.get('reward_tool_xp') or 0):
            assert (q.get('reward_tool_type') or q.get('specialist_tool_type'))
        assert isinstance(q.get('reward_items') or {},dict)
        assert int(q.get('needed') or 1)>=1
        for item,qty in (q.get('reward_items') or {}).items():
            assert item in ITEMS and int(qty)>0,(qid,item)
        req=q.get('requires_quest')
        if req:assert req in QUESTS,(qid,req)
        c+=5
    assert set(prof_quests)==set(PROJECTS)
    assert sum(map(len,prof_quests.values()))==2221,(sum(map(len,prof_quests.values())),)
    c+=2
    for prof,p in PROJECTS.items():
        for level in (1,25,100,200,400,600,700,775,799):
            pr=profession_xp_requirement_v1401(v0190_requirement('profession',level),prof,level)
            tr=tool_xp_requirement_v1402(v0190_requirement('tool',level),p.tool,level)
            for required,tool in ((pr,False),(tr,True)):
                easy=reward_xp_v1203(100,required,level,1,tool=tool,content_key='oak_log')
                suitable=reward_xp_v1203(100,required,level,level,tool=tool,content_key='oak_log')
                advanced=reward_xp_v1203(100,required,level,min(800,level+50),tool=tool,content_key='oak_log')
                assert easy>=100 and suitable>=easy and advanced>=suitable,(prof,level,tool,easy,suitable,advanced)
                assert reward_xp_v1203(0,required,level,level,tool=tool)==0
                assert reward_xp_v1203(100,required,level,None,tool=tool)==100
                assert reward_xp_v1203(100,required,800,800,tool=tool)==100
                if level>=100:
                    assert suitable*200>=required,(prof,level,tool,suitable,required)
                if level>=400:
                    assert suitable>easy,(prof,level,tool,suitable,easy)
                c+=6
        for tier in LEVELS:
            ingredients=recipe(prof,tier)
            assert len(ingredients)==2 and all(i in ITEMS and qty>0 for i,qty in ingredients),(prof,tier,ingredients)
            c+=2
        assert project_item_id(prof) in ITEMS
        c+=1
    # Every resource identity has a deterministic non-RNG award. No decrease.
    assert material_factor('iron_ore') != material_factor('oak_log');c+=1
    assert material_factor('iron_ore') == material_factor('iron_ore');c+=1
    for prof,ql in prof_quests.items():
        required=profession_xp_requirement_v1401(v0190_requirement('profession',400),prof,400)
        tool_required=tool_xp_requirement_v1402(v0190_requirement('tool',400),PROJECTS[prof].tool,400)
        for qid,q in ql:
            prof_gain=int(q.get('reward_profession_xp') or 0)
            tool_gain=int(q.get('reward_tool_xp') or 0)
            # Lowest payout always preserved, no invented Soul progression.
            p=quest_reward_floor_v1203(prof_gain,required,400,q)
            t=quest_reward_floor_v1203(tool_gain,tool_required,400,q,tool=True)
            assert p>=prof_gain and t>=tool_gain,(qid,p,t)
            assert quest_reward_floor_v1203(0,required,400,q)==0
            assert quest_reward_floor_v1203(0,tool_required,400,q,tool=True)==0
            assert not q.get('requires_quest') or q['requires_quest'] in QUESTS
            c+=5
        # Real high-tier quests earn more than the old award (when tier 400).
        high=[q for _,q in ql if int(q.get('min_profession_level') or 0) in (380,400,420)]
        if high:
            assert any(quest_reward_floor_v1203(max(1,int(q.get('reward_profession_xp') or 0)),required,400,q)>max(1,int(q.get('reward_profession_xp') or 0)) for q in high)
            c+=1
    # Quest progress is never altered in this release: no new or removed IDs.
    assert len(QUESTS)==(6793 if str(server.VERSION).startswith('35.') else 6769)
    c+=1
    return c

if __name__=='__main__':
    print('v12.00.3 PROFESJE/NARZEDZIA/QUESTY:',run_regression(),'checks PASS')

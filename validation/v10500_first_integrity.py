# -*- coding: utf-8 -*-
"""Isolated v105 catalogue + mandatory-milestone smoke. No production DB writes."""
from __future__ import annotations
import asyncio
from collections import Counter
from types import SimpleNamespace


def run():
    from core.progression_600 import SOUL_MAX_TIER,SOUL_TIER_THRESHOLDS,SOUL_TRIAL_QUEST_IDS
    from world.dynamic_content import (ROOMS,MOB_TEMPLATES,MOB_SPAWNS,NPCS,QUESTS,ITEMS,
          CRAFT_RECIPES,REGIONAL_SET_BONUSES,V10500_REGIONS_BUILD,V10500_EQUIPMENT_BUILD)
    from world.v10500_region_index import REGIONS
    from world.v10500_equipment import planned_ids
    from player.session_methods_v4200 import skilllearning_part01 as src
    from pathlib import Path
    import ast
    # Compile the verbatim class method (the historical session imports rely on
    # the full server bootstrap and are intentionally not imported here).
    code=Path(__file__).resolve().parents[1]/'player/session_mixins/quest_progress.py'
    module=ast.parse(code.read_text(encoding='utf-8'))
    cls=next(n for n in module.body if isinstance(n,ast.ClassDef) and n.name=='SessionQuestProgressMixin')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='quest_ids_for_npc')
    method.decorator_list=[]
    compiled=compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(code),'exec')
    scope={'QUESTS':QUESTS,'SOUL_TRIAL_QUEST_IDS':SOUL_TRIAL_QUEST_IDS}
    exec(compiled,scope)
    quest_ids_for_npc=scope['quest_ids_for_npc']
    checks=0
    def ok(condition,msg):
        nonlocal checks
        if not condition:raise AssertionError(msg)
        checks+=1
    # v105 owns the immutable 1..3000 prefix; an approved v110 extends it
    # to 6000 without changing any historical tier, trial or quest ID.
    # Reject unexpected intermediate/truncated ranges, not the legal successor.
    from systems.v11000_activation import enabled as v110_authorized
    import os
    from pathlib import Path
    v110_runtime = (Path(__file__).resolve().parents[1]/'VERSION').read_text(encoding='utf-8-sig').strip() in ('110.00.0', '111.00.0')
    from systems.universal_activation import enabled as universal_enabled
    if universal_enabled():
        # Future releases may raise the Soul cap. Preserve every legacy tier,
        # with at least the 6000 tiers already guaranteed by modern gameplay.
        cap = SOUL_MAX_TIER
        ok(cap >= 6000, 'universal Soul cap cannot regress: '+str(cap))
    else:
        extended = os.environ.get('SOULBOUND_V106_STAGING') == '1' or (v110_runtime and v110_authorized())
        cap = 6000 if extended else 3000
        ok(SOUL_MAX_TIER == cap, 'tier cap from authenticated legacy environment: '+str(SOUL_MAX_TIER))
    ok(len(SOUL_TIER_THRESHOLDS) == cap, 'threshold count '+str(cap))
    ok(SOUL_TIER_THRESHOLDS[0] == 1, 'historical Tier 1')
    for newer_tier in range(3001, cap+1):
        ok(SOUL_TIER_THRESHOLDS[newer_tier-1] == newer_tier*10, 'successor tier '+str(newer_tier))
        ok(SOUL_TRIAL_QUEST_IDS.get(newer_tier) == f'soul_tier_{newer_tier:02d}_trial',
           'successor trial ID '+str(newer_tier))
    for tier in range(2,3001):
        ok(SOUL_TIER_THRESHOLDS[tier-1]==tier*10,f'level requirement T{tier}')
    ok(len(REGIONS)==20,'20 distinct regions')
    ok([a[:4] for a in REGIONS][0][2:]==(10001,11000),'first region')
    ok(REGIONS[-1][3]==30000,'last region')
    ok(V10500_REGIONS_BUILD['regions']==20 and V10500_REGIONS_BUILD['quests']==1000,'real registration')
    ok(V10500_EQUIPMENT_BUILD['sets']==34 and len(planned_ids())==136,'sets count')
    for i,(slug,region,low,high,*_) in enumerate(REGIONS):
        p='v10500_'+slug
        for j in range(1,15):
            rid=f'{p}_{j:02d}';ok(rid in ROOMS,'room '+rid)
            for dest in ROOMS[rid]['exits'].values():ok(dest in ROOMS, 'broken exit '+rid)
        for j in range(1,9):
            mid=f'{p}_mob_{j}';ok(mid in MOB_TEMPLATES,'mob '+mid)
            ok(any(m==mid for room,m in MOB_SPAWNS),'missing spawn '+mid)
        for j in (1,2):ok(f'{p}_boss_{j}' in MOB_TEMPLATES,'boss '+p)
        for j in (1,2,3):
            n=NPCS[f'{p}_npc_{j}'];ok(n['room'] in ROOMS, 'npc missing room')
        qids=[qid for qid in QUESTS if qid.startswith(p+'_') and any(qid.startswith(p+'_'+kind+'_') for kind in ('story','prof','hunt','explore'))]
        ok(len(qids)==50,'50 quests '+p)
        kinds=Counter(qid.rsplit('_',2)[-2] for qid in qids)
        ok(kinds=={'story':20,'prof':15,'hunt':10,'explore':5},'quest breakdown '+p)
        for qid in qids:
            q=QUESTS[qid];ok(q['giver'] in {n['name'] for n in (NPCS[f'{p}_npc_{j}'] for j in (1,2,3))},'quest giver')
            ok(q['needed']>=1 and q['reward_gold']>0,'reward/needed '+qid)
            if q['kind']=='kill':ok(q['target'] in MOB_TEMPLATES,'quest mob '+qid)
            if q.get('requires_quest'):ok(q['requires_quest'] in QUESTS,'quest chain '+qid)
    ok(len([q for q in QUESTS if q.startswith('v10500_') and any('_story_' in q or '_prof_' in q or '_hunt_' in q or '_explore_' in q for _ in (0,))])==1000,'1000 quests total')
    for iid in planned_ids():
        row=ITEMS[iid]; recipe=CRAFT_RECIPES[iid]
        ok(row['regional_set'] in REGIONAL_SET_BONUSES,'set bonus '+iid)
        ok(set(recipe['ingredients']).issubset(ITEMS),'recipe ingredients '+iid)
        ok(row['sockets']==3,'sockets '+iid)
    milestones=[t for t in range(10,3001,10)]
    ok(len(milestones)==300,'300 milestones')
    for t in milestones:
        qid=SOUL_TRIAL_QUEST_IDS[t];q=QUESTS[qid]
        ok(q['unlocks_soul_tier']==t and q['required_soul_level']==t*10,'tier metadata '+str(t))
        ok(q['required_soul_tier']==t-1,'tier predecessor '+str(t))
    new=[QUESTS[SOUL_TRIAL_QUEST_IDS[t]] for t in range(1010,3001,10)]
    ok(len(new)==200,'200 new milestones')
    ok(any(q['target'].startswith('astral_boss_') for q in new),'astral trial targets')
    ok(any(q['target'].startswith('v10500_') for q in new),'regional trial targets')
    ok(any(q['target'].startswith('crypt_boss_') for q in new),'crypt trial targets')
    # Real quest offer method, without a user DB, tests visible milestone filtering.
    class Dummy:
        character=SimpleNamespace(soul_tier=1)
        server=SimpleNamespace(db=SimpleNamespace(quest=lambda *args:None))
        account_id=3
        def normalize_description_query(self,x):return str(x).casefold()
    Dummy.quest_ids_for_npc=quest_ids_for_npc
    dummy=Dummy()
    first=dummy.quest_ids_for_npc('priest_elor',NPCS['priest_elor'])
    trials=[QUESTS[q]['unlocks_soul_tier'] for q in first if 'unlocks_soul_tier' in QUESTS[q]]
    ok(trials==list(range(10,101,10)),'first 10 Elor trials '+str(trials))
    dummy.character.soul_tier=1009
    later=dummy.quest_ids_for_npc('priest_elor',NPCS['priest_elor'])
    tiers=[QUESTS[q]['unlocks_soul_tier'] for q in later if 'unlocks_soul_tier' in QUESTS[q]]
    ok(tiers==list(range(1010,1110,10)),'Elor 1010+ '+str(tiers))
    # Direct execute of the same imported unlock body on fake session.
    src.unlock.__globals__.update(dict(SOUL_MAX_TIER=SOUL_MAX_TIER,
       SOUL_TIER_THRESHOLDS=SOUL_TIER_THRESHOLDS,
       SOUL_TRIAL_QUEST_IDS=SOUL_TRIAL_QUEST_IDS,QUESTS=QUESTS))
    class Fake:
        def __init__(self):
            self.character=SimpleNamespace(soul_tier=1,soul_level=125,room_id='temple',name='test',soul_power=lambda:1)
            self.sent=[];self.saved=[];self.broadcast=[]
            self.server=SimpleNamespace(db=SimpleNamespace(save_character=lambda c:self.saved.append(c.soul_tier)),
                                       broadcast_room=self.notify)
        async def notify(self,*args,**kw):self.broadcast.append((args,kw))
        async def send(self,msg):self.sent.append(msg)
        def soul_tier_quest_completed(self,t):return False
    fake=Fake();asyncio.run(src.unlock(fake,multi=True))
    ok(fake.character.soul_tier==9 and fake.saved==[9],'unlock max stops before T10 without quest')
    fake.soul_tier_quest_completed=lambda t: t==10
    asyncio.run(src.unlock(fake,multi=True))
    ok(fake.character.soul_tier==12 and fake.saved==[9,12],'unlock max after T10 stop at Soul125')
    ok(len(fake.broadcast)==2,'one broadcast per mass unlock')
    return checks

if __name__=='__main__':
    print(f'V105 FIRST INTEGRITY: {run()} PASS',flush=True)

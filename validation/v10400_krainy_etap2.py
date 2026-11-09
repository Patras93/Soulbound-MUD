# -*- coding: utf-8 -*-
"""Etap 2 v104: strukturalne testy świata 5001–10000, bez kont produkcyjnych."""
from __future__ import annotations
from collections import deque
import sqlite3
from copy import deepcopy
from core.classes_skills import CLASSES
from world.v10400_krainy_5001_10000 import REGIONS, PROFESSION_SPECS, install


def run():
    checks=0
    def ok(condition, message):
        nonlocal checks
        if not condition:
            raise AssertionError(message)
        checks+=1
    from validation.class_balance_v1172 import _historical_22
    historical_classes, _ = _historical_22()
    assert len(historical_classes)==22
    base='v10300_tron_12'
    rooms={base:{'exits':{'south':'v10300_tron_11'}}}
    mobs={};spawns=[];npcs={};quests={};items={'steel_ingot': {'name': 'Sztabka stali', 'type': 'craft_material'}};recipes={}
    areas=[];zones={};categories={};guides={};power={}
    result=install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,zones,categories,guides,power,class_rows=historical_classes)
    expected={'regions':10,'rooms':140,'mobs':100,'npcs':30,'quests':120+140+10*len(historical_classes),
              'story_quests':120,'profession_quests':140,'class_quests':10*len(historical_classes),
              'items':50,'recipes':20}
    for key,n in expected.items():ok(result[key]==n,f'{key}: {result[key]} != {n}')
    ok(len(historical_classes)==22,'registered 22 historical classes')
    ok(len(PROFESSION_SPECS)==14,'registered 14 professions')
    ok(len(rooms)==141 and len(mobs)==100 and len(npcs)==30 and len(quests)==480,'registry counts')
    ok(rooms[base]['exits']['east']=='v10400_sztorm_01','v103 -> v104 gate')
    ok(rooms['v10400_sztorm_01']['exits']['west']==base,'v104 -> v103 return')
    ok(REGIONS[0][2]==5001 and REGIONS[-1][3]==10000,'range 5001-10000')
    for i,row in enumerate(REGIONS):
        ok(row[2] == 5001+i*500 and row[3] == 5500+i*500,f'contiguous levels {i}')
    opposites={'north':'south','south':'north','west':'east','east':'west'}
    for rid,room in rooms.items():
        for d,to in room.get('exits',{}).items():
            if to not in rooms:
                ok(rid==base and d=='south' and to=='v10300_tron_11','only mocked external exit')
                continue
            ok(rooms[to]['exits'].get(opposites[d])==rid,f'broken return {rid}.{d}->{to}')
    found=set();q=deque((base,))
    while q:
        rid=q.popleft()
        if rid in found:continue
        found.add(rid)
        q.extend(dest for dest in rooms[rid]['exits'].values() if dest in rooms)
    ok(found==set(rooms),'connected world')
    ok(len({row['name'] for rid,row in rooms.items() if rid!=base})==140,'unique authored room names')
    ok(len({v['room'] for v in npcs.values()})==30,'all NPCs in separate rooms')
    spawn_ids={mob for rid,mob in spawns}
    for rid,mob in spawns:
        ok(rid in rooms and mob in mobs, f'invalid spawn {rid}, {mob}')
    ok(spawn_ids==set(mobs),'every mob spawned')
    offered=set()
    for nid,npc in npcs.items():
        ok(npc['room'] in rooms,f'NPC room missing {nid}')
        ok(npc['v10300_era_npc'] and npc['v10400_era_npc'],'NPC uses original NVDA offering path')
        for qid in npc['specialist_quests']:
            ok(qid in quests,f'missing quest offer {qid}')
            ok(quests[qid]['giver']==npc['name'],f'quest giver mismatch {qid}')
            ok(qid not in offered,f'duplicated offer {qid}')
            offered.add(qid)
    ok(offered==set(quests),'every quest offered exactly once')
    for qid,quest in quests.items():
        kind=quest['kind'];target=quest['target']
        if kind=='kill':
            ok(target in spawn_ids,f'kill without spawn {qid}')
        elif kind=='collect':
            ok(target in items and any(target in mob.get('drops',{}) for mob in mobs.values()),
               f'collection without loot {qid}')
        elif kind=='profession_action':
            ok(quest['reward_profession']==target and quest['reward_tool_type'],f'profession xp {qid}')
            ok('min_profession_level' not in quest,f'profession quest level gate {qid}')
        else:
            raise AssertionError(f'unsupported quest kind {qid}: {kind}')
        ok(quest['needed']>0,f'zero work quest {qid}')
        ok(quest['generator_level']>=5001,f'low level quest {qid}')
        req=quest.get('requires_quest')
        if req:ok(req in quests,f'missing previous quest {qid}')
        ok(quest.get('reward_stat_progress',1)>0,f'zero stat reward {qid}')
        ok(quest.get('reward_gold',1)>0,f'zero gold reward {qid}')
        ok(all(item in items and int(num)>0 for item,num in quest.get('reward_items',{}).items()),
           f'phantom reward item {qid}')
    for rid,recipe in recipes.items():
        ok(recipe['output'] in items,f'recipe output {rid}')
        ok(all(i in items and int(qty)>0 for i,qty in recipe['ingredients'].items()),f'recipe inputs {rid}')
        ok(recipe['min_profession_level']>=5001,'endgame recipe min')
    # NVDA offer and class visibility reuse existing helper, no new NPC subsystem.
    from systems.era_npc_offers_v10300 import visible_era_quests
    for slug,*_ in REGIONS:
        prefix=f'v10400_{slug}'
        for n in range(1,len(historical_classes)+1):
            npc=npcs[f'{prefix}_npc_2']
            class_name=historical_classes[n-1][0]
            offered_for_class=visible_era_quests(npc['specialist_quests'],quests,lambda qid:None,(class_name,))
            ok(f'{prefix}_class_{n:02d}' in offered_for_class,f'class offer missing {slug}/{class_name}')
            ok(not any(quests[qid].get('required_class') not in (None,class_name) for qid in offered_for_class),
               f'foreign class offer {slug}/{class_name}')
        for n in range(1,15):
            ok(f'{prefix}_prof_{n:02d}' in
               visible_era_quests(npcs[f'{prefix}_npc_3']['specialist_quests'],quests,lambda qid:None,()),
               f'profession offer missing {slug}/{n}')
    # All IDs prevalidated: collision must not mutate any registry or parent exit.
    clean=({base:{'exits':{'south':'v10300_tron_11'}}},{},{},[],{},{},{},{},{},{},{})
    # direct independent shallow scratch with existing quest collision
    r={base:{'exits':{'south':'v10300_tron_11'}}};m={};s=[];n={};q={'v10400_sztorm_story_01':{}};
    it={};re={};a=[];z={};cat={};g={};pw={}
    before=deepcopy((r,m,s,n,q,it,re,a,z,cat,g,pw))
    try:
        install(r,m,s,n,q,it,re,a,z,cat,g,pw,class_rows=historical_classes)
        raise AssertionError('collision permitted')
    except RuntimeError as e:
        ok('kolizja quests' in str(e),f'wrong collision error: {e}')
    ok(before== (r,m,s,n,q,it,re,a,z,cat,g,pw),'collision is atomic')
    idempotent=install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,zones,categories,guides,power,class_rows=historical_classes)
    ok(idempotent['regions']==0,'idempotent install')
    ok(len(spawns)==180,'no duplicate spawns after idempotent install')
    # Real quest sqlite state code with isolated in-memory DB, 480 distinct accounts.
    import storage.db_quests as dbmod
    from storage.db_quests import DatabaseQuestMixin
    class QuestDB(DatabaseQuestMixin):
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.row_factory=sqlite3.Row
            self.conn.executescript('''
              CREATE TABLE quests(account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
               status TEXT NOT NULL DEFAULT 'active',progress INTEGER NOT NULL DEFAULT 0,
               completed_at INTEGER NOT NULL DEFAULT 0,completion_count INTEGER NOT NULL DEFAULT 0,
               PRIMARY KEY(account_id,quest_id));
              CREATE TABLE quest_resource_progress_v0929(account_id INTEGER NOT NULL,
               quest_id TEXT NOT NULL,resource_id TEXT NOT NULL DEFAULT '',progress INTEGER NOT NULL DEFAULT 0);
            ''')
    db=QuestDB();old=dbmod.QUESTS;dbmod.QUESTS=quests
    try:
        for account,(qid,quest) in enumerate(sorted(quests.items()),1):
            db.start_quest(account,qid)
            ok(db.quest(account,qid)['status']=='active',f'quest active {qid}')
            db.set_quest_progress(account,qid,int(quest['needed']))
            ok(db.quest(account,qid)['progress']==quest['needed'],f'quest progress {qid}')
            db.complete_quest(account,qid)
            ok(db.quest(account,qid)['completion_count']==1 and db.quest(account,qid)['status']=='completed',
               f'quest completion {qid}')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
    finally:
        dbmod.QUESTS=old;db.conn.close()
    return checks, expected


if __name__=='__main__':
    n,counts=run()
    print(f'V104 ETAP 2: {n} testów PASS, {counts["rooms"]} komnat, '
          f'{counts["quests"]} questów, {counts["mobs"]} mobów, 0 DB produkcyjnych',flush=True)

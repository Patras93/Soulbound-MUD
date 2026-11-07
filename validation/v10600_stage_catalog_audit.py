# -*- coding: utf-8 -*-
"""Offline, isolated checks for UNWIRED v106 world/quest/raid/trial code.

Important: passing does NOT imply real TCP completion, actual combat balance,
per-instance EQ migration or full release readiness.
"""
from __future__ import annotations
import sys
from pathlib import Path
from collections import Counter, deque
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from world.v10600_krainy_30001_60000 import install,planned_ids,REGIONS
from world.v10600_raids_26_35 import install as raids_install,planned_ids as raid_ids,RAID_ROWS
from world.v10600_soul_trials import register as trials_register,trial_ids


def registries():
    return ({'v10500_przelom_14':{'exits':{'west':'historic_room'},'name':'Historyczna Sala'},
             'historic_room':{'exits':{'east':'v10500_przelom_14'}}},
            {},[],{}, {}, {}, {}, [],{}, {},{}, {})


def run():
    state=registries()
    rooms,mobs,spawns,npcs,quests,items,recipes,areas,zone_ids,categories,guides,power=state
    checks=0
    def check(value,what):
        nonlocal checks
        if not value:raise AssertionError(what)
        checks+=1
    outcome=install(*state)
    check((outcome['regions'],outcome['rooms'],outcome['mobs'],
           outcome['npcs'],outcome['quests'],outcome['items'],outcome['recipes'])
          ==(30,720,360,120,1800,120,30),'content counts')
    check(rooms['v10500_przelom_14']['exits']['west']=='historic_room',
          'old exit overwritten')
    check(install(*state)['regions']==0,'idempotent world import')
    check(len(areas)==0,'caller owns area expansion; no hidden world mutation')
    area_rows=outcome['areas']
    check(len(area_rows)==30,'30 EXP area descriptors')
    raid_result=raids_install(rooms,mobs,spawns,npcs,quests,items,recipes)
    check(raid_result=={'raids':10,'rooms':30,'bosses':30,'quests':30},'raid counts')
    check(raids_install(rooms,mobs,spawns,npcs,quests,items,recipes)['raids']==0,
          'raid idempotency')
    check(trials_register(quests,mobs)==300,'300 trial quests')
    check(trials_register(quests,mobs)==0,'trial idempotency')
    check(len([qid for qid in quests if qid.startswith('soul_tier_')])==300,
          'trial count')
    check(set(trial_ids())==set(range(3010,6001,10)),'trial milestones')
    spawned={}
    for room,mid in spawns:
        check(room in rooms and mid in mobs,'invalid spawn')
        spawned.setdefault(mid,set()).add(room)
    check(len(spawned)==390,'all mob types spawn')
    for rid,data in rooms.items():
        for direction,to in data.get('exits',{}).items():
            check(to in rooms,'broken exit '+rid+':'+direction)
    seen={'historic_room'};to_visit=deque(seen)
    while to_visit:
        for target in rooms[to_visit.popleft()].get('exits',{}).values():
            if target not in seen:seen.add(target);to_visit.append(target)
    check(len(seen)==len(rooms),'not all rooms reachable from historical entrance')
    check(len(rooms)==752,'overall rooms')
    kinds=Counter(q['kind'] for q in quests.values())
    for slug,name,low,high,*_ in REGIONS:
        p=f'v10600_{slug}'
        doors=rooms[f'{p}_04']['exits']
        check(doors['east']==f'{p}_15','loop opens')
        check(rooms[f'{p}_10']['exits']['west']==f'{p}_18','loop closes')
        check(rooms[f'{p}_12']['exits']['east']==f'{p}_19','hidden branch')
        check(all(f'{p}_npc_{i}' in npcs for i in range(1,5)),'all NPC')
        region_quests={qid:q for qid,q in quests.items() if qid.startswith(p+'_')}
        check(len(region_quests)==60,'60 quests '+p)
        check(len({q['kind'] for q in region_quests.values()})>=5,'objective diversity '+p)
        for i in range(1,16):
            q=quests[f'{p}_story_{i:02d}']
            if i>1:check(q.get('requires_quest')==f'{p}_story_{i-1:02d}',
                           'broken story chain')
        for j in range(1,5):
            npc=npcs[f'{p}_npc_{j}'];check(npc['room'] in seen,'NPC unreachable')
    for qid,q in quests.items():
        check(q['needed']>0,'bad objective '+qid)
        check(q['reward_gold']>0,'no reward '+qid)
        if q['kind']=='kill':check(q['target'] in spawned,'unspawned quest mob '+qid)
        if q['kind']=='talk_npc':check(q['target_npc'] in npcs,'unreachable quest NPC '+qid)
        if q['kind']=='collect':check(q['target'] in items,'missing quest item '+qid)
        if q['kind']=='profession_action':check(q['required_profession']==q['target'],
                                              'profession mismatch '+qid)
        if q.get('requires_quest'):check(q['requires_quest'] in quests,
                                         'invalid quest chain '+qid)
    for qid,q in quests.items():
        if qid.startswith('soul_tier_'):continue
        check(any(qid in npc.get('specialist_quests',()) and q['giver']==npc['name']
                  for npc in npcs.values()),'quest missing at giver '+qid)
    for t,qid in trial_ids().items():
        check(quests[qid]['unlocks_soul_tier']==t,'wrong Tier '+str(t))
        check(quests[qid]['required_soul_level']==t*10,'wrong Soul Lv '+str(t))
        check(quests[qid]['required_soul_tier']==t-1,'wrong predecessor '+str(t))
    # Negative: must reject collision before changing the historical exit.
    bad=registries()
    bad[4]['v10600_przedmurze_story_01']={'name':'PREEXISTING'}
    try:install(*bad)
    except RuntimeError:  # AUDIT_INTENTIONAL_PASS: expected duplicate key rejection; side effects checked below
        pass
    else:raise AssertionError('collision accepted')
    check('east' not in bad[0]['v10500_przelom_14']['exits'],
          'collision had side effects')
    check(kinds['talk_npc']>=100 and kinds['collect']>=100,
          'story quests only fake kind labels')
    return {'checks':checks,'rooms':len(rooms),'mobs':len(mobs),
            'npcs':len(npcs),'quests':len(quests),'trial_milestones':len(trial_ids()),
            'types':dict(kinds)}

if __name__=='__main__':
    print('V106 STAGING CATALOG: '+str(run())+' PASS',flush=True)

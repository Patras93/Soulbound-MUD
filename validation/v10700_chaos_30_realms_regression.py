# -*- coding: utf-8 -*-
"""Testy katalogowe 30 krain v107: 25 nowych, bez rajdów i fałszywych celów."""
from __future__ import annotations
import copy
import os
import sys
from collections import deque
from world.v10700_chaos_chapter_one import install as install_first, prefix
from world.v10700_chaos_chapters_2_6 import install, all_planned_ids
from world.v10700_region_index import CHAPTER_ONE
from world.v10700_region_index_chapters_2_6 import CHAPTERS, ALL_NEXT
from world.legends_v3100 import OPPOSITE
from validation.v10700_chaos_chapter_one_regression import fixture


def run():
    v=fixture()
    b1=install_first(*v)
    rooms,mobs,spawns,npcs,quests,items,recipes,zone_ids,categories,guides,power=v
    old_rooms={name:copy.deepcopy(rooms[name]) for name in rooms}
    old_quests=set(quests)
    b=install(*v)
    checks=0
    def check(ok,msg):
        nonlocal checks
        assert ok,msg
        checks+=1
    check(b['chapters']==5 and b['regions']==25 and len(b['areas'])==25,'5 chapters, 25 regions')
    check((b['rooms'],b['mobs'],b['spawns'],b['npcs'],b['quests'],b['items'],b['recipes'])
          ==(500,300,550,100,1000,125,25),'precise actual content')
    check(len(quests)==1200 and len(old_quests)==200 and len(items)==151,'first and next chapters')
    ids=all_planned_ids()
    for kind,reg in (('rooms',rooms),('mobs',mobs),('npcs',npcs),('quests',quests),
                     ('items',items),('recipes',recipes)):
        check(ids[kind]<=reg.keys(),f'all {kind} entries')
    # No chapter one data modified except the east gateway from the final boss room.
    gate=prefix(CHAPTER_ONE[-1][0])+'_12'
    for rid,original in old_rooms.items():
        if rid==gate:
            now=copy.deepcopy(rooms[rid]); now['exits'].pop('east',None)
            check(now==original,'old chapter one gateway preserved')
        else:
            check(rooms[rid]==original,'old room not overwritten '+rid)
    check(old_quests<=quests.keys(),'all earlier quest IDs retained')
    all_ids={prefix(row[0])+'_01' for row in (*CHAPTER_ONE,*ALL_NEXT)}
    path=set();q=deque(['v10600_serce_14'])
    while q:
        rid=q.popleft()
        if rid in path:continue
        path.add(rid)
        for direction,target in rooms[rid].get('exits',{}).items():
            check(target in rooms,'target room exists: '+rid+' '+direction)
            check(rooms[target].get('exits',{}).get(OPPOSITE[direction])==rid,
                  'reversible exit: '+rid+' '+direction)
            if target not in path:q.append(target)
    check(len(path)==601 and all_ids<=path,'600 rooms fully reachable from last v106')
    for n,chapter in enumerate(CHAPTERS,2):
        for k,(slug,name,lore,boss_a,boss_b,enemies,materials) in enumerate(chapter):
            p=prefix(slug);low=60001+(n-1)*5000+k*1000
            check(power[p]==low and zone_ids[name]==p,'native area indexes '+name)
            check(categories[p]=='Endgame' and guides[name.casefold()]==p+'_01', 'guide '+name)
            mobids=[f'{p}_mob_{j}' for j in range(1,11)]+[f'{p}_boss_1',f'{p}_boss_2']
            qids=[qid for qid in ids['quests'] if qid.startswith(p+'_')]
            check(len(qids)==40 and len(mobids)==12,'40 quests, 12 foes '+name)
            check(len([e for e in spawns if e[1] in mobids])==22,'22 real spawns '+name)
            check(rooms[p+'_12']['zone']==name and rooms[p+'_20']['zone']==name,'boss chambers '+name)
            for mid in mobids:
                mob=mobs[mid]
                check(any(place in path and thing==mid for place,thing in spawns), 'physical spawn '+mid)
                check(mob['max_hp']>0 and mob['damage']>0 and mob['class_xp_reward']>0,
                      'physical, XP '+mid)
                check(not mob.get('raid') and not mob.get('auto_aggro'),'non raid, no autoagro '+mid)
                check(all(drop in items for drop in mob['drops']),'real items '+mid)
            offered=set();giver_names=set()
            for j in range(1,5):
                npc=npcs[f'{p}_npc_{j}']
                check(npc['room'] in path,'reachable NPC '+str(j)+name)
                giver_names.add(npc['name']);offered.update(npc['specialist_quests'])
            check(offered==set(qids),'all 40 quests offered to actual NPC '+name)
            for qid in qids:
                quest=quests[qid];kind=quest.get('kind')
                check(quest['giver'] in giver_names and quest['needed']>=1,'native quest '+qid)
                check(quest['reward_gold']>0 and quest['olc_reward_xp']>0 and
                      quest['reward_mithril']>0,'reward '+qid)
                check(not quest.get('raid') and not quest.get('party_required'),'solo quest '+qid)
                check(all(item in items for item in quest.get('reward_items',{})),'reward items '+qid)
                if kind=='kill':
                    check(quest['target'] in mobs and any(mid==quest['target'] for _,mid in spawns),
                          'real kill target '+qid)
                elif kind=='collect':
                    item=quest['target']
                    check(item in items and any(template['drops'].get(item,0)>0
                          for template in mobs.values() if 'drops' in template),
                          'obtainable resource '+qid)
                elif kind=='talk_npc':
                    check(quest['target_npc'] in npcs and npcs[quest['target_npc']]['room'] in path,
                          'reachable dialogue '+qid)
                elif kind=='profession_action':
                    check(bool(quest.get('required_profession')) and
                          bool(quest.get('specialist_tool_type')),
                          'native profession '+qid)
                else:raise AssertionError('fake unsupported quest: '+qid)
                if 'requires_quest' in quest:
                    check(quest['requires_quest'] in quests and
                          quest['requires_quest']!=qid, 'existing quest chain '+qid)
    snapshot=copy.deepcopy(v)
    repeated=install(*v)
    check(repeated['already_installed'] and snapshot==v,'full catalog idempotent')
    check(install_first(*v)['already_installed'],'chapter one still idempotent')
    # Global preflight detects collisions in 5th chapter before ANY of 25 realms are installed.
    for kind,index,entry in (('room',0,next(iter(ids['rooms']))),
                             ('quest',4,next(iter(ids['quests']))),
                             ('mob',1,next(iter(ids['mobs'])))):
        candidate=fixture();install_first(*candidate)
        candidate[index][entry]={'collision':True}
        before=copy.deepcopy(candidate)
        try:install(*candidate)
        except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: expected collision rejection
        else:raise AssertionError('preflight should reject '+kind)
        check(candidate==before,'no mutation when collided '+kind)
    print(f'V107 30 KRAIN: {checks} PASS; 25 nowych, 500 lokacji, 300 potworów, 1000 questów')
    return checks


def real_server():
    os.environ['SOULBOUND_V107_STAGING']='1'
    os.environ['SOULBOUND_V106_STAGING']='0'
    import server
    from world.world_state import World
    print('V107 SERWER: import zakonczony, tworze instancje swiata',flush=True)
    ids=all_planned_ids()
    b=server.V10700_CHAOS_CHAPTERS_2_6_BUILD
    assert b['regions']==25 and b['quests']==1000,b
    assert server.V10700_CHAOS_CHAPTER_ONE_BUILD['regions']==5
    assert server.V10700_RAIDS_RETIRED['retired_raids']==35
    assert ids['rooms']<=server.ROOMS.keys() and ids['quests']<=server.QUESTS.keys()
    assert len([q for q in server.QUESTS if q.startswith('v10700_chaos_')])==1200
    w=World()
    spawned=[m for m in w.mobs.values() if m.template_id.split('__',1)[0] in ids['mobs']]
    assert len(spawned)==550,('actual spawns',len(spawned))
    assert len({m.template_id.split('__',1)[0] for m in spawned})==300
    assert all(m.alive and m.hp>0 and m.room_id in ids['rooms'] for m in spawned)
    from world.v10700_chaos_chapter_one import planned_ids
    one=planned_ids()['mobs']
    assert sum(m.template_id.split('__',1)[0] in one for m in w.mobs.values())==110
    from world.v10700_insects_expansion import planned_ids as i1
    from world.v10700_insects_wildlife_plus import planned_ids as i2
    insects=i1()['mobs']|i2()['mobs']
    assert sum(m.template_id.split('__',1)[0] in insects for m in w.mobs.values())==95
    assert not any('raid_' in m.template_id for m in w.mobs.values()
                   if m.template_id.startswith(('v10300_','v10400_','v10600_')))
    print('V107 SERWER: PASS, 550 nowych + 110 rozdzialu I + 95 owadow, 0 aktywnych rajdow')

if __name__=='__main__':
    real_server() if '--server' in sys.argv[1:] else run()
